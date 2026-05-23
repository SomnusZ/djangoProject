import cv2
import numpy as np


def smoothstep(edge0, edge1, x):
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-6), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def find_center_pupil_mask(gray: np.ndarray, black_threshold: int = 15):
    """
    在局部 patch 内寻找最接近中心的黑色瞳孔区域
    """
    h, w = gray.shape[:2]
    black_mask = (gray <= black_threshold).astype(np.uint8)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        black_mask, connectivity=8
    )

    cx0, cy0 = w / 2.0, h / 2.0
    best_idx = -1
    best_dist = 1e18

    for i in range(1, num_labels):
        x, y, bw, bh, area = stats[i]

        touches_border = (x == 0) or (y == 0) or (x + bw >= w) or (y + bh >= h)
        if touches_border:
            continue
        if area < 100:
            continue

        cx, cy = centroids[i]
        dist = (cx - cx0) ** 2 + (cy - cy0) ** 2
        if dist < best_dist:
            best_dist = dist
            best_idx = i

    if best_idx == -1:
        pupil_mask = np.zeros_like(gray, dtype=np.uint8)
        center = (w // 2, h // 2)
        axes = (max(1, int(w * 0.18)), max(1, int(h * 0.22)))
        cv2.ellipse(pupil_mask, center, axes, 0, 0, 360, 255, -1)
        return pupil_mask

    return (labels == best_idx).astype(np.uint8) * 255


def find_eye_roi_from_white_bg(
    template_bgr: np.ndarray,
    white_thresh: int = 245,
    pad: int = 8,
):
    """
    在白底模板中找到眼球主体区域（含虹膜+瞳孔）的外接矩形
    并返回整图级别的前景 mask（眼球圆区域）
    """
    gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

    # 非白区域 = 前景
    fg = (gray < white_thresh).astype(np.uint8) * 255

    kernel = np.ones((3, 3), np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)

    ys, xs = np.where(fg > 0)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("No eye ROI found from white background")

    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()

    h, w = gray.shape[:2]
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w - 1, x2 + pad)
    y2 = min(h - 1, y2 + pad)

    return x1, y1, x2, y2, fg


def recolor_iris_template_hsv_core(
    template_bgr: np.ndarray,
    eye_mask: np.ndarray,   # 新增：只允许眼球圆区域参与
    base_bgr: tuple[int, int, int],
    black_threshold: int = 15,
    sat_boost: float = 1.15,
    val_scale: float = 0.95,
    debug: bool = False
):
    """
    只在 eye_mask 指定区域内进行虹膜重绘
    """
    if template_bgr is None or template_bgr.size == 0:
        raise ValueError("template_bgr is empty")

    out = template_bgr.copy()
    gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)

    # 不仅要排除黑瞳孔，还要限制在眼球圆内
    iris_mask = ((gray > black_threshold) & (eye_mask > 0)).astype(np.uint8)

    kernel = np.ones((3, 3), np.uint8)
    iris_mask = cv2.morphologyEx(iris_mask, cv2.MORPH_OPEN, kernel)
    iris_mask = cv2.morphologyEx(iris_mask, cv2.MORPH_CLOSE, kernel)

    pupil_mask = find_center_pupil_mask(gray, black_threshold)
    pupil_mask_u8 = ((pupil_mask > 0) & (eye_mask > 0)).astype(np.uint8)
    iris_mask_u8 = (iris_mask > 0).astype(np.uint8)

    not_pupil = (1 - pupil_mask_u8).astype(np.uint8)
    dist_to_pupil = cv2.distanceTransform(not_pupil, cv2.DIST_L2, 3)
    dist_to_outer = cv2.distanceTransform(iris_mask_u8, cv2.DIST_L2, 3)

    radial_t = dist_to_pupil / (dist_to_pupil + dist_to_outer + 1e-6)
    radial_t[iris_mask_u8 == 0] = 0.0

    hsv = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2HSV).astype(np.float32)

    target_hsv = cv2.cvtColor(
        np.uint8([[list(base_bgr)]]), cv2.COLOR_BGR2HSV
    )[0, 0].astype(np.float32)

    target_h = target_hsv[0]
    target_s = max(float(target_hsv[1]) * sat_boost, 38.0)
    target_s = min(target_s, 255.0)

    H = hsv[:, :, 0]
    S = hsv[:, :, 1]
    V = hsv[:, :, 2]

    H_new = H.copy()
    H_new[iris_mask_u8 > 0] = target_h

    # 更强一点的饱和度径向变化
    sat_radial = 0.75 + 0.45 * smoothstep(0.08, 0.78, radial_t)
    target_s_map = target_s * sat_radial

    S_new = S.copy()
    S_new[iris_mask_u8 > 0] = (
            0.15 * S[iris_mask_u8 > 0] + 0.85 * target_s_map[iris_mask_u8 > 0]
    )
    S_new = np.clip(S_new, 0, 255)

    # 更强一点的明度内外压暗
    outer_dark = 1.0 - 0.22 * smoothstep(0.80, 1.0, radial_t)
    inner_dark = 1.0 - 0.20 * (1.0 - smoothstep(0.00, 0.22, radial_t))
    v_radial = outer_dark * inner_dark

    V_new = V.copy()
    V_new[iris_mask_u8 > 0] = (
            V[iris_mask_u8 > 0] * 1.00 * v_radial[iris_mask_u8 > 0]
    )
    V_new = np.clip(V_new, 0, 255)

    hsv_new = np.stack([H_new, S_new, V_new], axis=-1).astype(np.uint8)
    recolored = cv2.cvtColor(hsv_new, cv2.COLOR_HSV2BGR)

    out[iris_mask_u8 > 0] = recolored[iris_mask_u8 > 0]
    out[pupil_mask_u8 > 0] = 0

    if debug:
        print("[core] iris pixels  =", int((iris_mask_u8 > 0).sum()))
        print("[core] pupil pixels =", int((pupil_mask_u8 > 0).sum()))

    return out, iris_mask_u8 * 255, pupil_mask_u8 * 255


def recolor_iris_template_hsv(
    template_bgr: np.ndarray,
    base_bgr: tuple[int, int, int],
    black_threshold: int = 15,
    sat_boost: float = 1.15,
    val_scale: float = 0.95,
    white_thresh: int = 245,
    auto_roi: bool = True,
    debug: bool = False
):
    """
    集成版：
    - 自动识别白底模板
    - 只在眼球圆内部重绘
    - 圆外全部纯白
    """
    if template_bgr is None or template_bgr.size == 0:
        raise ValueError("template_bgr is empty")

    gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    white_ratio = float((gray >= white_thresh).sum()) / gray.size

    # 全白输出图
    out_full = np.ones_like(template_bgr, dtype=np.uint8) * 255
    iris_mask_full = np.zeros(gray.shape, dtype=np.uint8)
    pupil_mask_full = np.zeros(gray.shape, dtype=np.uint8)
    fg_mask_full = np.zeros(gray.shape, dtype=np.uint8)

    if auto_roi and white_ratio > 0.35:
        x1, y1, x2, y2, fg_mask = find_eye_roi_from_white_bg(
            template_bgr,
            white_thresh=white_thresh,
            pad=8
        )

        patch = template_bgr[y1:y2+1, x1:x2+1].copy()
        patch_fg_mask = fg_mask[y1:y2+1, x1:x2+1].copy()

        recolored_patch, iris_mask_patch, pupil_mask_patch = recolor_iris_template_hsv_core(
            patch,
            eye_mask=(patch_fg_mask > 0).astype(np.uint8),
            base_bgr=base_bgr,
            black_threshold=black_threshold,
            sat_boost=sat_boost,
            val_scale=val_scale,
            debug=debug
        )

        # 只把眼球圆区域贴回去
        roi = out_full[y1:y2 + 1, x1:x2 + 1]
        valid_mask = (patch_fg_mask > 0)

        roi[valid_mask] = recolored_patch[valid_mask]
        out_full[y1:y2 + 1, x1:x2 + 1] = roi

        iris_mask_full[y1:y2+1, x1:x2+1] = iris_mask_patch
        pupil_mask_full[y1:y2+1, x1:x2+1] = pupil_mask_patch
        fg_mask_full = fg_mask.copy()

        # 圈外上色
        out_full[fg_mask_full == 0] = base_bgr

        if debug:
            print("[roi] ROI =", (x1, y1, x2, y2))
            print("[roi] white_ratio =", white_ratio)

        return out_full, iris_mask_full, pupil_mask_full, fg_mask_full

    # 非白底模板的兜底逻辑
    fg_mask_full[:] = 255
    recolored, iris_mask, pupil_mask = recolor_iris_template_hsv_core(
        template_bgr,
        eye_mask=np.ones_like(gray, dtype=np.uint8),
        base_bgr=base_bgr,
        black_threshold=black_threshold,
        sat_boost=sat_boost,
        val_scale=val_scale,
        debug=debug
    )

    out_full = recolored.copy()
    return out_full, iris_mask, pupil_mask, fg_mask_full


if __name__ == "__main__":
    template = cv2.imread("../source/eye_uv_template4.png")
    if template is None:
        raise FileNotFoundError("Failed to read template image")

    # 采样结果
    base_bgr = (171, 187, 175)

    recolored, iris_mask, pupil_mask, fg_mask = recolor_iris_template_hsv(
        template,
        base_bgr=base_bgr,
        black_threshold=15,
        sat_boost=1.20,
        val_scale=0.92,
        white_thresh=245,
        auto_roi=True,
        debug=True
    )

    cv2.imwrite("../output/eye_uv_recolored_hsv.png", recolored)
    cv2.imwrite("../output/eye_uv_mask_hsv.png", iris_mask)
    cv2.imwrite("../output/eye_uv_pupil_mask_hsv.png", pupil_mask)
    cv2.imwrite("../output/eye_uv_fg_mask.png", fg_mask)

