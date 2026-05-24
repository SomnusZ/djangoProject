"""
宠物眼球UV贴图视图文件。
包含接口：
  - generateEyeUv：上传图片，立即写库并启动后台线程异步生成
  - queryEyeUv：轮询查任务状态（处理中/成功/失败）
"""

import threading
import uuid
from pathlib import Path

from django.conf import settings
from django.db import connection
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny

from app.utils import success_response, error_response
from aipet.photo_to_uv_texture import generate_eye_uv_texture

from .models import PetEyeUv


# 上传图片保存目录（与原 photo_to_uv_texture 模块约定一致）
_USERIMAGE_DIR = Path(__file__).resolve().parent.parent.parent / 'aipet' / 'photo_to_uv_texture' / 'UserImage'


def _process_eye_uv_async(record_id: str, save_path: str) -> None:
    """
    后台线程入口：执行 AI 生成并更新 PetEyeUv 记录状态。
    与 HTTP 请求解耦，调用方不感知执行进度，前端通过 queryEyeUv 轮询。

    注意：线程结束时必须关闭 DB 连接（Django ORM 在新线程中会建立独立连接，
    不关闭会泄漏；服务重启可恢复但日常运行会逐步累积连接数）。
    """
    try:
        record = PetEyeUv.objects.get(pet_eye_uv_id=record_id)

        # 标记为处理中
        record.workflow_status = 'processing'
        record.save(update_fields=['workflow_status', 'updated_at'])

        # 调用生成模块
        try:
            result = generate_eye_uv_texture(save_path)
        except Exception as exc:
            record.workflow_status = 'generate_fail'
            record.workflow_error = f'调用 generate_eye_uv_texture 异常：{exc}'
            record.save(update_fields=['workflow_status', 'workflow_error', 'updated_at'])
            return

        # 模块自身可能返回 status != "success"
        if result.get('status') != 'success':
            record.workflow_status = 'generate_fail'
            record.workflow_error = result.get('message', '生成失败')
            record.save(update_fields=['workflow_status', 'workflow_error', 'updated_at'])
            return

        # 把 recolored_path 本地绝对路径转为可访问的 URL
        # nginx 映射：/eye_uv_images/ -> aipet/photo_to_uv_texture/output/
        recolored_results = result.get('recolored_results', []) or []
        eye_urls = []
        eye_bgrs = []
        for item in recolored_results:
            if not item.get('ok'):
                continue
            recolored_path = item.get('recolored_path', '')
            if recolored_path:
                relative = recolored_path.replace('\\', '/').split('output/')[-1]
                url = f"{settings.MESHY_SERVER_URL}/eye_uv_images/{relative}"
            else:
                url = ''
            eye_urls.append(url)

            base_bgr = item.get('base_bgr')
            if isinstance(base_bgr, (list, tuple)):
                eye_bgrs.append(','.join(str(c) for c in base_bgr))
            else:
                eye_bgrs.append('')

        record.workflow_status = 'generate_success'
        record.eye_count = len(eye_urls)
        record.eye_uv_url_0 = eye_urls[0] if len(eye_urls) > 0 else ''
        record.eye_uv_url_1 = eye_urls[1] if len(eye_urls) > 1 else ''
        record.base_bgr_0 = eye_bgrs[0] if len(eye_bgrs) > 0 else ''
        record.base_bgr_1 = eye_bgrs[1] if len(eye_bgrs) > 1 else ''
        record.workflow_error = ''
        record.save(update_fields=[
            'workflow_status', 'eye_count',
            'eye_uv_url_0', 'eye_uv_url_1',
            'base_bgr_0', 'base_bgr_1',
            'workflow_error', 'updated_at',
        ])
    finally:
        # 关闭线程中 ORM 建立的独立 DB 连接，避免连接泄漏
        connection.close()


class PetEyeUvViewSet(viewsets.GenericViewSet):
    """
    宠物眼球UV贴图接口视图集。
    包含眼球UV贴图生成（异步）、任务状态轮询。
    """

    queryset = PetEyeUv.objects.all()
    # 当前不强制登录（与 photo_to_uv 模块原有的测试性质保持一致）
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='generateEyeUv',
            parser_classes=[MultiPartParser])
    def generate_eye_uv(self, request):
        """
        眼球UV贴图生成接口（异步）。
        接收前端上传的猫咪图片，写入初始记录后立即返回 pet_eye_uv_id；
        实际 AI 推理由后台线程异步执行，前端通过 queryEyeUv 轮询结果。

        表单字段：
            image: 图片文件（必填，仅支持 image/*）
        """
        # ---------- 1. 入参校验 ----------
        image_file = request.FILES.get('image')
        if not image_file:
            return error_response('请上传 image 文件', status_code=status.HTTP_200_OK, result='imgnone')
        if not image_file.content_type.startswith('image/'):
            return error_response('只支持图片文件', status_code=status.HTTP_200_OK, result='imgonly')

        # ---------- 2. 保存图片 ----------
        _USERIMAGE_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(image_file.name).suffix or '.jpg'
        # 直接复用记录主键作为文件名，方便日后排查
        record_id = str(uuid.uuid4())
        filename = f"{record_id}{suffix}"
        save_path = _USERIMAGE_DIR / filename

        with open(save_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # ---------- 3. 写入初始记录（upload_success）----------
        PetEyeUv.objects.create(
            pet_eye_uv_id=record_id,
            original_image_path=str(save_path),
            workflow_status='upload_success',
        )

        # ---------- 4. 启动后台线程异步处理 ----------
        thread = threading.Thread(
            target=_process_eye_uv_async,
            args=(record_id, str(save_path)),
            daemon=True,
        )
        thread.start()

        # ---------- 5. 立即返回前端 ----------
        return success_response(
            {
                'pet_eye_uv_id': record_id,
                'workflow_status': 'upload_success',
            },
            message='上传成功',
        )

    @action(detail=False, methods=['get'], url_path='queryEyeUv')
    def query_eye_uv(self, request):
        """
        眼球UV贴图任务状态轮询接口。
        前端拿到 generateEyeUv 返回的 pet_eye_uv_id 后定时调用此接口，
        直至 workflow_status 为终态（generate_success / generate_fail）后停止轮询。

        查询参数：
            pet_eye_uv_id: 任务ID（必填）

        响应说明（按 workflow_status 区分）：
            upload_success / processing：仅返回 id + status
            generate_success：返回 id + status + eye_uv_url_0 + eye_uv_url_1
            generate_fail：返回 id + status + workflow_error
        """
        pet_eye_uv_id = request.query_params.get('pet_eye_uv_id')
        if not pet_eye_uv_id:
            return error_response('请提供 pet_eye_uv_id', status_code=status.HTTP_200_OK)

        record = PetEyeUv.objects.filter(pet_eye_uv_id=pet_eye_uv_id).first()
        if not record:
            return error_response('记录不存在', status_code=status.HTTP_200_OK)

        response_data = {
            'pet_eye_uv_id': record.pet_eye_uv_id,
            'workflow_status': record.workflow_status,
        }

        if record.workflow_status == 'generate_success':
            response_data['eye_uv_url_0'] = record.eye_uv_url_0
            response_data['eye_uv_url_1'] = record.eye_uv_url_1
        elif record.workflow_status == 'generate_fail':
            response_data['workflow_error'] = record.workflow_error

        return success_response(response_data, message='查询成功')
