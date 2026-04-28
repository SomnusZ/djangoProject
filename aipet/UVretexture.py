import cv2
from pathlib import Path
import numpy as np

_AIPET_DIR = Path(__file__).resolve().parent
BASE_DIR = _AIPET_DIR / "3Dmodels" / "meshy"
BASE_DIR_MASK = _AIPET_DIR / "3Dmodels" / "Sample"
MASK_PATH = BASE_DIR_MASK / "UV_sample" / "mask_cat_eye.png"
MASK_PATH2 = BASE_DIR_MASK / "UV_sample" / "mask_cat_tongue.png"

def clean_uv_inpaint_by_task_id(task_id: str) -> str:
    """
    使用固定 EyeMask + inpaint 清理 Meshy UV 贴图
    """
    task_dir = BASE_DIR / task_id
    user_uv_path = task_dir / "texture_0_base_color.png"
    out_path = task_dir / "texture_clean.png"
    if not user_uv_path.exists():
        raise FileNotFoundError(
            f"Expected texture not found.\n"
            f"Looking for: {user_uv_path}\n"
            f"Available files: {list(task_dir.glob('*'))}"
        )

    # 读取贴图
    albedo = cv2.imread(str(user_uv_path), cv2.IMREAD_COLOR)
    if albedo is None:
        raise RuntimeError(f"Failed to read albedo: {user_uv_path}")

    # 读取 mask
    mask = cv2.imread(str(MASK_PATH), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        raise RuntimeError(f"Failed to read mask: {MASK_PATH}")

    # 尺寸兜底
    if mask.shape[:2] != albedo.shape[:2]:
        mask = cv2.resize(
            mask,
            (albedo.shape[1], albedo.shape[0]),
            interpolation=cv2.INTER_NEAREST
        )

    # 扩大 mask，防止边缘渗色
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    mask = cv2.dilate(mask, kernel, iterations=1)

    # === 核心：inpaint ===
    clean = cv2.inpaint(
        albedo,
        mask,
        inpaintRadius=7,
        flags=cv2.INPAINT_TELEA
    )

    # cv2.imwrite(str(out_path), clean)
    # #第二轮CV，对第一轮CV的结果再用mask2进行重绘，重新给舌头上粉红色
    mask_tongue = cv2.imread(str(MASK_PATH2), cv2.IMREAD_GRAYSCALE)
    if mask_tongue is None:
        raise RuntimeError(f"Failed to read mask: {MASK_PATH2}")

    if mask_tongue.shape[:2] != clean.shape[:2]:
        mask_tongue = cv2.resize(
            mask_tongue,
            (clean.shape[1], clean.shape[0]),
            interpolation=cv2.INTER_NEAREST
        )

    # 轻微膨胀 + feather
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask_tongue = cv2.dilate(mask_tongue, kernel, iterations=1)
    mask_tongue = cv2.GaussianBlur(mask_tongue, (11, 11), 0)

    # 归一化 alpha
    alpha = mask_tongue.astype(np.float32) / 255.0
    alpha = alpha[..., None]  # (H, W, 1)

    # 舌头颜色（BGR）
    tongue_color = np.array([128, 138, 220], dtype=np.float32)

    # blend
    clean = (
        clean.astype(np.float32) * (1 - alpha)
        + tongue_color * alpha
    ).astype(np.uint8)

    # # === 保存 ===
    cv2.imwrite(str(out_path), clean)
    return str(out_path)




# user_uv_path2 = out_path #用户meshy生成的贴图
# mask_path2 = "3Dmodels/meshy/UV_sample/mask1218.png"#模板mask范围
# out_path2 = "3Dmodels/meshy/2ac1e57d-d7af-472b-a261-47cb2a7e6c92/texture_clean2.png"#输出贴图给unity
# in_path = "3Dmodels/meshy/UV_sample/texture.png"
# img_bgr = cv2.imread(in_path, cv2.IMREAD_COLOR)
# h, w = img_bgr.shape[:2]
#
# # Detect red markup (BGR image): red has high R, low G/B
# b, g, r = cv2.split(img_bgr)
# red_outline = ((r > 160) & (g < 110) & (b < 110)).astype(np.uint8) * 255
#
# # Clean up and close gaps so circles become closed shapes
# k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
# closed = cv2.morphologyEx(red_outline, cv2.MORPH_CLOSE, k_close, iterations=1)
#
# # Find contours of the red markup
# contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
# mask = np.zeros((h, w), dtype=np.uint8)
#
# # Fill contours to get interior regions (eyes to be replaced)
# for cnt in contours:
#     area = cv2.contourArea(cnt)
#     if area < 200:  # ignore tiny artifacts
#         continue
#     cv2.drawContours(mask, [cnt], -1, 255, thickness=-1)
#
# # Slightly expand mask so we cover boundary bleed and the red strokes themselves
# k_dilate = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
# mask = cv2.dilate(mask, k_dilate, iterations=1)
#
# # Inpaint using surrounding fur texture
# result = cv2.inpaint(img_bgr, mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
#
# out_path = "/3Dmodels/meshy/UV_sample/uv_texture_eyes_removed.png"
# cv2.imwrite(out_path, result)
#
# # Also save mask for verification
# mask_path = "3Dmodels/meshy/UV_sample/mask.png"
# cv2.imwrite(mask_path, mask)
#
# out_path, mask_path, (h, w), len(contours)

