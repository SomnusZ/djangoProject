"""
aipet/task_workflow.py
AI 宠物生成工作流核心函数（Django 同步版）

职责：纯业务逻辑，只读写 task_obj 字段，不调用 save()。
数据库持久化统一由调用方（user_task/views.py）负责。
"""

import base64
import traceback
from pathlib import Path

from django.conf import settings

from aipet.CleanPic import clean_pic, NoPetDetectedError, ImageProcessError
from aipet.image_data_url import build_image_data_url
from aipet.Meshy3D import start_meshy_job, check_meshy_status
from aipet.Meshy_Workflow import advance_meshy_task, get_texture_result, MeshyContext
from aipet.Uv_eye_replace import overlay_transparent_png


# ── MODEL_DATA_URL 预加载 ─────────────────────────────────────
# 模块导入时立即将所有模型文件读入内存并 base64 编码，之后调用直接取字典，不再读文件。
# 前提：部署时所有模型文件必须存在，否则服务启动失败。
# 路径优先读 settings，未配置则使用默认相对路径。

# 原始单模型懒加载（保留备用）
# _MODEL_DATA_URL_CACHE = None
# def _get_model_data_url() -> str:
#     global _MODEL_DATA_URL_CACHE
#     if _MODEL_DATA_URL_CACHE:
#         return _MODEL_DATA_URL_CACHE
#     model_path = getattr(settings, 'MESHY_MODEL_PATH', '3Dmodels/Sample/model0107.fbx')
#     try:
#         with open(model_path, 'rb') as f:
#             b64 = base64.b64encode(f.read()).decode()
#         _MODEL_DATA_URL_CACHE = f"data:application/octet-stream;base64,{b64}"
#         print(f"✅ 模板模型已缓存：{model_path}")
#         return _MODEL_DATA_URL_CACHE
#     except Exception as e:
#         raise ValueError(f'模板模型加载失败：{repr(e)}')

# aipet/ 目录的绝对路径，用于拼接模型文件路径，避免相对路径因启动目录不同而失效
_AIPET_DIR = Path(__file__).resolve().parent

# 模型键 → 文件路径映射，新增模型只需在此处添加一行
_MODEL_PATH_MAP = {
    'Cat_M': getattr(settings, 'MESHY_MODEL_PATH_CAT_M', str(_AIPET_DIR / '3Dmodels' / 'Sample' / 'model0107.fbx')),
    'Cat_L': getattr(settings, 'MESHY_MODEL_PATH_CAT_L', str(_AIPET_DIR / '3Dmodels' / 'Sample' / 'Cat_L_Final.fbx')),
    'Cat_XL': getattr(settings, 'MESHY_MODEL_PATH_CAT_XL', str(_AIPET_DIR / '3Dmodels' / 'Sample' / 'Cat_XL_Final.fbx')),
}


def _preload_models() -> dict:
    """模块导入时调用一次，将所有模型文件编码为 data URL 并返回字典。
    任意一个文件缺失都会抛出 FileNotFoundError，服务将无法启动。
    部署前请确认 _MODEL_PATH_MAP 中所有路径均存在。
    """
    cache = {}
    for key, path in _MODEL_PATH_MAP.items():
        try:
            with open(path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode()
            cache[key] = f"data:application/octet-stream;base64,{b64}"
            print(f"✅ 模板模型已预加载：{key} → {path}")
        except FileNotFoundError:
            raise FileNotFoundError(f'模型文件不存在，服务无法启动：{key} → {path}')
        except Exception as e:
            raise RuntimeError(f'模型文件加载失败：{key} → {path}，原因：{repr(e)}')
    return cache


# 服务启动时执行预加载，结果存入模块级常量供后续直接读取
_MODEL_DATA_URL_CACHE = _preload_models()


def _get_model_data_url(model_key: str = 'Cat_M') -> str:
    # 预加载后直接从字典取，键不存在则说明模型未注册
    if model_key in _MODEL_DATA_URL_CACHE:
        return _MODEL_DATA_URL_CACHE[model_key]
    raise ValueError(f'未知模型键：{model_key}，可选值：{list(_MODEL_DATA_URL_CACHE.keys())}')


# ── 内部辅助：ORM 对象 <-> dict 互转 ─────────────────────────

def _task_obj_to_dict(task_obj) -> dict:
    """把 UserTask ORM 对象转成 Meshy_Workflow 需要的 dict 结构"""
    task_id = str(task_obj.user_task_id)
    _aipet_dir = Path(__file__).resolve().parent
    download_dir = _aipet_dir / '3Dmodels' / 'meshy' / task_id
    meshy_downloaded = (download_dir / 'texture_0_base_color.png').exists()

    return {
        'status':             task_obj.workflow_status,
        'meshy_job_id':       task_obj.meshy_job_id,
        'meshy_retry_count':  task_obj.meshy_retry_count,
        'meshy_max_retries':  2,
        'clean_path':         task_obj.image_path,
        'texture_clean_path': task_obj.texture_clean_path or None,
        'texture_cleaned':    bool(task_obj.texture_clean_path),
        'meshy_downloaded':   meshy_downloaded,
        'error':              task_obj.workflow_error or None,
    }


def _sync_dict_to_obj(task_dict: dict, task_obj) -> None:
    """把 advance_meshy_task 修改后的 dict 写回 ORM 对象（只赋值，不 save）"""
    task_obj.workflow_status    = task_dict.get('status', task_obj.workflow_status)
    task_obj.meshy_retry_count  = task_dict.get('meshy_retry_count', task_obj.meshy_retry_count)
    task_obj.texture_clean_path = task_dict.get('texture_clean_path') or ''
    task_obj.workflow_error     = task_dict.get('error') or ''
    if task_dict.get('meshy_job_id'):
        task_obj.meshy_job_id = task_dict['meshy_job_id']


# ── 预处理：在创建 UserTask 之前调用 ─────────────────────────
# 不依赖 task_obj，只需要预先生成的 task_id 和图片字节
# 失败时数据库没有任何写入，用户可直接重新上传

def preprocess_image(task_id: str, file_bytes: bytes) -> tuple:
    """
    调用 CleanPic 预处理图片。
    在 UserTask 创建之前执行，失败时不产生任何数据库记录。
    返回 (ok: bool, data: dict)
      ok=True  → data 包含 image_path / pet_breed / pet_type
      ok=False → data 包含 detail / code
    """
    print(f">>> preprocess image for task: {task_id}")
    try:
        clean_result = clean_pic(task_id, file_bytes)

    except NoPetDetectedError as e:
        return False, {'detail': str(e), 'code': 'no_pet_detected'}

    except ImageProcessError as e:
        return False, {'detail': '图片处理失败', 'code': 'image_process_error'}

    except Exception:
        return False, {'detail': '服务内部错误', 'code': 'unknown_error',
                       'trace': traceback.format_exc()}

    return True, {
        'image_path': clean_result['path'],
        'pet_breed':  clean_result.get('breed') or '',
        'pet_type':   clean_result.get('type') or '',
    }


# ── 提交 Meshy 任务 ───────────────────────────────────────────

def meshy(task_obj, cat_size: str = 'Cat_M'):
    """
    提交 Meshy retexture 任务，将结果写入 task_obj 字段。
    不调用 save()，由 view 层统一持久化。
    返回 (ok: bool, data: dict)
    """
    task_id = str(task_obj.user_task_id)

    if task_obj.workflow_status != 'cleaned':
        return False, {
            'detail': f"当前状态 '{task_obj.workflow_status}' 不允许提交，需为 'cleaned'",
            'code': 'invalid_status',
        }

    image_path = Path(task_obj.image_path)
    if not image_path.exists():
        return False, {'detail': '预处理图片文件不存在', 'code': 'image_missing'}

    try:
        model_data_url = _get_model_data_url(cat_size)
    except ValueError as e:
        return False, {'detail': str(e), 'code': 'config_error'}

    image_data_url = build_image_data_url(image_path)

    try:
        result = start_meshy_job(image_url=image_data_url, model_url=model_data_url)
    except Exception as e:
        task_obj.workflow_status = 'ERROR'
        task_obj.workflow_error  = f'[start_meshy_job] {repr(e)}'
        return False, {'detail': 'Meshy 提交失败', 'code': 'meshy_submit_error'}

    task_obj.meshy_job_id    = result['job_id']
    task_obj.workflow_status = 'meshy_pending'
    task_obj.workflow_error  = ''

    return True, {
        'task_id':         task_id,
        'workflow_status': task_obj.workflow_status,
        'meshy_job_id':    task_obj.meshy_job_id,
    }


# ── 查询 Meshy 任务状态 ───────────────────────────────────────

def meshy_status(task_obj):
    """
    查询 Meshy 状态并推进工作流，将最新状态写入 task_obj 字段。
    不调用 save()，由 view 层统一持久化。
    返回 (ok: bool, data: dict)
    """
    task_id = str(task_obj.user_task_id)

    if not task_obj.meshy_job_id:
        return False, {'detail': 'Meshy 任务尚未提交', 'code': 'no_meshy_job'}

    # 终态直接返回，不修改 task_obj（view 层 save 是幂等的）
    if task_obj.workflow_status in {'DONE', 'FAILED', 'ERROR'}:
        data = {
            'task_id':         task_id,
            'workflow_status': task_obj.workflow_status,
            'workflow_error':  task_obj.workflow_error,
        }
        if task_obj.workflow_status == 'DONE':
            data['texture_clean_path'] = task_obj.texture_clean_path
        return True, data

    # ① 查询 Meshy
    try:
        meshy_result = check_meshy_status(task_obj.meshy_job_id)
    except Exception as e:
        task_obj.workflow_status = 'ERROR'
        task_obj.workflow_error  = f'[check_meshy_status] {repr(e)}'
        return False, {'detail': '查询 Meshy 失败', 'code': 'meshy_query_error'}

    # ② 推进工作流
    task_dict = _task_obj_to_dict(task_obj)
    try:
        image_data_url = build_image_data_url(Path(task_obj.image_path))
        model_data_url = _get_model_data_url()
        ctx = MeshyContext(image_url=image_data_url, model_url=model_data_url)
        advance_meshy_task(task_id, task_dict, meshy_result, ctx)
    except Exception:
        task_obj.workflow_status = 'ERROR'
        task_obj.workflow_error  = f'[advance_meshy_task] {traceback.format_exc()}'
        return False, {'detail': '工作流推进失败', 'code': 'workflow_error'}

    # ③ 同步 dict → ORM 字段（不 save）
    _sync_dict_to_obj(task_dict, task_obj)

    if task_obj.workflow_status == 'DONE':
        texture_replace_eye = ''
        # 覆盖眼睛
        if task_obj.pet_model_id in [2, 3]:
            cat_size = 'Cat_L'
            if task_obj.pet_model_id == 2:
                cat_size = 'Cat_L'
            elif task_obj.pet_model_id == 3:
                cat_size = 'Cat_XL'
            texture_replace_eye = overlay_transparent_png(
                str(_AIPET_DIR / '3Dmodels' / 'meshy' / task_obj.user_task_id / 'texture_0_base_color.png'), task_id, cat_size)

        final = get_texture_result(task_id, task_dict)
        return True, {
            'task_id':              task_id,
            'workflow_status':      'DONE',
            'texture_download_url': final.get('texture_download_url'),
            'texture_clean_path':   task_obj.texture_clean_path,
            'texture_replace_eye_path':   texture_replace_eye,
        }

    return True, {
        'task_id':         task_id,
        'workflow_status': task_obj.workflow_status,
        'workflow_error':  task_obj.workflow_error,
    }
