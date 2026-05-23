"""
detect user cat's eye's image color before bake texture
"""
import cv2
import numpy as np

#TODO detect eye bound,crop image


#detect image's color
def extract_iris_gradient_bgr_from_patch(
    patch_bgr: np.ndarray,
    debug: bool = False
):
    """
    从已经裁好的虹膜 patch 中提取渐变用的三组颜色 BGR。
    输入:
        patch_bgr: OpenCV 读入的小图(BGR)
    输出:
        dark_bgr : 偏深颜色
        base_bgr : 主颜色
        light_bgr: 偏亮颜色
        debug_mask: 调试mask，可保存查看
    """
    if patch_bgr is None or patch_bgr.size == 0:
        raise ValueError("patch_bgr is empty")

    h, w = patch_bgr.shape[:2]

    # 1.中心区域采样
    center_mask = np.zeros((h, w), dtype=np.uint8)
    center = (w // 2, h // 2)
    axes = (max(1, int(w * 0.28)), max(1, int(h * 0.22)))
    cv2.ellipse(center_mask, center, axes, 0, 0, 360, 255, -1)

    # 2.HSV 过滤太暗 / 太亮 / 太灰的像素
    hsv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2HSV)
    s_ch = hsv[:, :, 1]
    v_ch = hsv[:, :, 2]

    valid = (
        (center_mask > 0) &
        (v_ch > 35) &
        (v_ch < 240) &
        (s_ch > 15)
    )

    pixels_bgr = patch_bgr[valid]

    # 如果过滤太狠，放宽一点
    if len(pixels_bgr) < 20:
        valid = (
            (center_mask > 0) &
            (v_ch > 25) &
            (v_ch < 245)
        )
        pixels_bgr = patch_bgr[valid]

    if len(pixels_bgr) == 0:
        raise ValueError("No valid iris pixels found")

    # 3.用分位数提取深 / 中 / 亮三组颜色（用于做渐变色）
    dark_bgr = np.percentile(pixels_bgr, 25, axis=0).astype(np.uint8)
    base_bgr = np.percentile(pixels_bgr, 50, axis=0).astype(np.uint8)
    light_bgr = np.percentile(pixels_bgr, 75, axis=0).astype(np.uint8)

    debug_mask = (valid.astype(np.uint8) * 255)

    if debug:
        print(f"valid pixels: {len(pixels_bgr)}")
        print(f"dark_bgr : {tuple(map(int, dark_bgr))}")
        print(f"base_bgr : {tuple(map(int, base_bgr))}")
        print(f"light_bgr: {tuple(map(int, light_bgr))}")

    return (
        tuple(map(int, dark_bgr)),
        tuple(map(int, base_bgr)),
        tuple(map(int, light_bgr)),
        debug_mask
    )


if __name__ == "__main__":
    img = cv2.imread("../source/eye_patch_1.png")
    if img is None:
        raise FileNotFoundError("Failed to read image: ../source/eye_patch_2.png")

    dark_bgr, base_bgr, light_bgr, debug_mask = extract_iris_gradient_bgr_from_patch(
        img,
        debug=True
    )

    cv2.imwrite("debug_mask.png", debug_mask)

#load sample eye uv, redraw with new color
