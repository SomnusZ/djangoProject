import cv2
import numpy as np
from pathlib import Path

from aipet_backend import settings

BASE_DIR = Path("3Dmodels/meshy")
#后续使用taskid去拼接，目前先用测试文件看效果 Base_DIR/task_id,user_uv_path = task_dir / "texture_0_base_color.png"
base_uv_path="3Dmodels/Sample/UV_sample/UVmASK/UV_L.png"
#base_uv_path="3Dmodels/Sample/UV_sample/UVmASK/UV_XL.png"
eye_overlay_path_L="3Dmodels/Sample/UV_sample/UVmASK/UV_MASK_CAT_L_01.png"
eye_overlay_path_XL="3Dmodels/Sample/UV_sample/UVmASK/UV_MASK_CAT_XL_01.png"
output_path=Path("3Dmodels/Sample/UV_sample/UVmASK/UV_with_round_eyes.png")

# aipet/ 目录的绝对路径，用于拼接模型文件路径，避免相对路径因启动目录不同而失效
_AIPET_DIR = Path(__file__).resolve().parent

eye_overlay_path_map = {
    'Cat_L': getattr(settings, 'MESHY_MODEL_PATH_CAT_L', str(_AIPET_DIR / '3Dmodels' / 'Sample' / 'UV_sample' / 'UVmASK' / 'UV_MASK_CAT_L_03.png')),
    'Cat_XL': getattr(settings, 'MESHY_MODEL_PATH_CAT_XL', str(_AIPET_DIR / '3Dmodels' / 'Sample' / 'UV_sample' / 'UVmASK' / 'UV_MASK_CAT_XL_01.png')),
}

#后续需要修改成传参taskid,和模型type：L/XL
def overlay_transparent_png(base_uv_path, task_id, model_key: str = 'Cat_M'):
    output_path = Path("aipet/3Dmodels/meshy/" + task_id + "/UV_with_round_eyes.png")
    eye_overlay_path = eye_overlay_path_map[model_key]
    base = cv2.imread(str(base_uv_path), cv2.IMREAD_COLOR)  # BGR
    overlay = cv2.imread(str(eye_overlay_path), cv2.IMREAD_UNCHANGED)  # BGRA

    if base is None:
        raise FileNotFoundError(f"无法读取原始UV图: {base_uv_path}")

    if overlay is None:
        raise FileNotFoundError(f"无法读取透明眼睛图层: {eye_overlay_path}")

    if overlay.shape[2] != 4:
        raise ValueError("eye_overlay_path 不是透明")

    if base.shape[:2] != overlay.shape[:2]:
        raise ValueError(
            f"两张图尺寸不一致: base={base.shape[:2]}, overlay={overlay.shape[:2]}"
        )

    # 拆分颜色,alpha
    overlay_bgr = overlay[:, :, :3].astype(np.float32)
    alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0

    base_float = base.astype(np.float32)

    # out = overlay * alpha + base * (1 - alpha)
    result = overlay_bgr * alpha + base_float * (1.0 - alpha)

    result = np.clip(result, 0, 255).astype(np.uint8)

    # output_path.parent.mkdir(parents=True, exist_ok=True)

    cv2.imwrite(str(output_path), result)

    return str(output_path)

# overlay_transparent_png(base_uv_path)