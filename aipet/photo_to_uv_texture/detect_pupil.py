import os
import cv2
import numpy as np

def _clip_box(x1, y1, x2, y2, w, h):
    x1 = max(0, min(int(round(x1)), w - 1))
    y1 = max(0, min(int(round(y1)), h - 1))
    x2 = max(x1 + 1, min(int(round(x2)), w))
    y2 = max(y1 + 1, min(int(round(y2)), h))
    return x1, y1, x2, y2


def detect_dark_pupil_simple(eye_bgr):
    """
    简单版瞳孔检测：
    找中心附近最主要的黑色连通区域。
    """
    h, w = eye_bgr.shape[:2]

    hsv = cv2.cvtColor(eye_bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    yy, xx = np.mgrid[0:h, 0:w]
    cx0, cy0 = w / 2.0, h / 2.0

    # 只在中心附近找，避免把眼睑/毛发识别成瞳孔
    center_mask = (
        ((xx - cx0) ** 2) / ((0.45 * w) ** 2 + 1e-6) +
        ((yy - cy0) ** 2) / ((0.45 * h) ** 2 + 1e-6)
    ) < 1.0

    center_v = V[center_mask]

    if len(center_v) < 20:
        return None

    # 自适应黑色阈值
    dark_thr = np.percentile(center_v, 10)
    dark_thr = np.clip(dark_thr, 15, 60)

    dark_mask = ((V <= dark_thr) & center_mask).astype(np.uint8) * 255

    # 形态学清理
    k = max(3, int(min(h, w) * 0.04))
    if k % 2 == 0:
        k += 1

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel)

    num, labels, stats, centroids = cv2.connectedComponentsWithStats(dark_mask, 8)

    if num <= 1:
        return None

    best_i = None
    best_score = -1

    img_area = h * w

    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]
        ccx, ccy = centroids[i]

        if area < img_area * 0.002:
            continue

        if area > img_area * 0.35:
            continue

        # 越靠近中心越可信
        dist = np.sqrt((ccx - cx0) ** 2 + (ccy - cy0) ** 2)
        center_score = 1.0 - min(dist / (0.5 * np.sqrt(w * w + h * h) + 1e-6), 1.0)


        #猫瞳孔通常偏竖，加分
        aspect = bh / (bw + 1e-6)
        vertical_bonus = np.clip(aspect / 2.0, 0.7, 1.5)

        score = np.sqrt(area) * center_score * vertical_bonus

        if score > best_score:
            best_score = score
            best_i = i

    if best_i is None:
        return None

    x = stats[best_i, cv2.CC_STAT_LEFT]
    y = stats[best_i, cv2.CC_STAT_TOP]
    bw = stats[best_i, cv2.CC_STAT_WIDTH]
    bh = stats[best_i, cv2.CC_STAT_HEIGHT]
    ccx, ccy = centroids[best_i]

    pupil_mask = (labels == best_i).astype(np.uint8) * 255

    return {
        "mask": pupil_mask,
        "center": (float(ccx), float(ccy)),
        "bbox": (int(x), int(y), int(x + bw), int(y + bh)),
        "width": int(bw),
        "height": int(bh),
        "area": int(stats[best_i, cv2.CC_STAT_AREA])
    }


def make_valid_color_mask(patch_bgr):
    """
    在一个候选 patch 内，筛掉明显不适合作为虹膜颜色的像素：
    1. 完全黑：瞳孔 / 阴影
    2. 太亮：过曝
    3. 高亮低饱和：高光
    """
    hsv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2HSV)
    H, S, V = cv2.split(hsv)

    valid = (
        (V > 35) &
        (V < 245) &
        ~((V > 225) & (S < 80))
    )

    return valid.astype(np.uint8) * 255

#评价系统
def score_boundary_candidate_patch(patch_bgr, patch_mask):
    """
    评分目标：
    选择偏亮、干净、有一定颜色感的虹膜基色块。

    核心原则：
    1. 不选最暗最稳定的区域；
    2. 不选过白/高光区域；
    3. 偏好亮度在 140~200 附近的区域；
    4. 饱和度只适度奖励，避免暗色高饱和区域胜出；
    5. 稳定性保留，但权重降低。
    """
    if patch_bgr is None or patch_bgr.size == 0:
        return -9999.0

    m = patch_mask > 0
    valid_count = int(m.sum())

    if valid_count < 6:
        return -9999.0

    hsv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2LAB)

    H, S, V = cv2.split(hsv)

    h_vals = H[m].astype(np.float32)
    s_vals = S[m].astype(np.float32)
    v_vals = V[m].astype(np.float32)
    lab_vals = lab[m].astype(np.float32)

    valid_ratio = float(valid_count / patch_mask.size)

    mean_s = float(np.mean(s_vals))
    median_s = float(np.median(s_vals))

    mean_v = float(np.mean(v_vals))
    median_v = float(np.median(v_vals))

    lab_std = float(np.mean(np.std(lab_vals, axis=0)))

    # --------------------------------------------------
    # 1. 亮度评分：偏好 175 左右
    # --------------------------------------------------
    # 目标亮度提高到 175。
    # left 的 median_v=107 会被明显压分；
    # right/down 的 median_v=187/197 会更接近目标。
    target_v = 175.0
    brightness_score = 1.0 - min(abs(median_v - target_v) / 90.0, 1.0)

    # 合理亮度像素比例：
    # 低于 120 认为偏暗；
    # 高于 215 开始接近白/高光风险。
    good_brightness_ratio = float(np.mean((v_vals >= 120) & (v_vals <= 215)))

    # --------------------------------------------------
    # 2. 强化暗部惩罚
    # --------------------------------------------------
    dark_ratio = float(np.mean(v_vals < 70))
    very_dark_ratio = float(np.mean(v_vals < 45))

    # 中位亮度低于 135，就认为整体偏暗。
    if median_v < 135:
        low_light_penalty = (135.0 - median_v) / 55.0
        low_light_penalty = min(low_light_penalty, 1.0)
    else:
        low_light_penalty = 0.0

    # --------------------------------------------------
    # 3. 白色 / 高光 / 过曝惩罚
    # --------------------------------------------------
    highlight_ratio = float(np.mean((v_vals > 220) & (s_vals < 80)))
    white_ratio = float(np.mean((v_vals > 210) & (s_vals < 45)))
    overbright_ratio = float(np.mean(v_vals > 235))

    if median_v > 210:
        too_bright_penalty = (median_v - 210.0) / 45.0
        too_bright_penalty = min(too_bright_penalty, 1.0)
    else:
        too_bright_penalty = 0.0

    # --------------------------------------------------
    # 4. 干净偏亮有色像素比例
    # --------------------------------------------------
    # 这是新的核心指标：
    # 必须有一定颜色感；
    # 必须不是暗区；
    # 也不能太白。
    clean_bright_color_mask = (
        (s_vals > 15) &
        (v_vals >= 120) &
        (v_vals <= 215) &
        ~((v_vals > 205) & (s_vals < 45))
    )

    clean_bright_color_ratio = float(np.mean(clean_bright_color_mask))

    # 饱和度适度奖励。
    # 不再让 left 这种暗区高饱和占太大便宜。
    saturation_score = (median_s - 15.0) / 55.0
    saturation_score = float(np.clip(saturation_score, 0.0, 1.0))

    # --------------------------------------------------
    # 5. 主色集中度
    # --------------------------------------------------
    # 只在 clean_bright_color_mask 内统计主色。
    # 这样暗区不会因为 hue 很集中而被奖励。
    if np.sum(clean_bright_color_mask) >= 6:
        h_use = h_vals[clean_bright_color_mask]
        s_use = s_vals[clean_bright_color_mask]

        hue_bins = (h_use // 4).astype(np.int32)
        hist = np.bincount(hue_bins, weights=s_use, minlength=45)

        peak_bin = int(np.argmax(hist))
        main_hue = peak_bin * 4 + 2

        d = np.abs(h_use - float(main_hue))
        d = np.minimum(d, 180.0 - d)

        close_main = (d < 12).astype(np.float32)

        if np.sum(s_use) > 1e-6:
            hue_consistency = float(np.sum(close_main * s_use) / np.sum(s_use))
        else:
            hue_consistency = float(np.mean(close_main))
    else:
        hue_consistency = 0.0

    # --------------------------------------------------
    # 6. 稳定性：保留但降权
    # --------------------------------------------------
    stability_score = 1.0 - min(lab_std / 65.0, 1.0)

    # --------------------------------------------------
    # 7. 最终得分计算，计算公式根据效果调整
    # --------------------------------------------------
    score = (
        valid_ratio * 0.5
        + brightness_score * 3.0
        + good_brightness_ratio * 1.5
        + clean_bright_color_ratio * 2.5
        + saturation_score * 0.8
        + hue_consistency * 0.8
        + stability_score * 0.4
        - dark_ratio * 3.5
        - very_dark_ratio * 5.0
        - low_light_penalty * 4.0
        - highlight_ratio * 2.8
        - white_ratio * 3.0
        - overbright_ratio * 3.5
        - too_bright_penalty * 2.5
    )

    return float(score)

def debug_patch_metrics(patch_bgr, patch_mask):
    m = patch_mask > 0
    valid_count = int(m.sum())

    if valid_count < 6:
        return {
            "valid_count": valid_count,
            "reason": "too_few_valid_pixels"
        }

    hsv = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(patch_bgr, cv2.COLOR_BGR2LAB)

    H, S, V = cv2.split(hsv)

    h_vals = H[m].astype(np.float32)
    s_vals = S[m].astype(np.float32)
    v_vals = V[m].astype(np.float32)
    lab_vals = lab[m].astype(np.float32)

    valid_ratio = float(valid_count / patch_mask.size)

    mean_s = float(np.mean(s_vals))
    median_s = float(np.median(s_vals))

    mean_v = float(np.mean(v_vals))
    median_v = float(np.median(v_vals))

    lab_std = float(np.mean(np.std(lab_vals, axis=0)))

    dark_ratio = float(np.mean(v_vals < 70))
    very_dark_ratio = float(np.mean(v_vals < 45))

    highlight_ratio = float(np.mean((v_vals > 220) & (s_vals < 80)))
    white_ratio = float(np.mean((v_vals > 210) & (s_vals < 45)))
    overbright_ratio = float(np.mean(v_vals > 235))

    clean_color_ratio = float(np.mean(
        (s_vals > 25) &
        (v_vals >= 85) &
        (v_vals <= 220)
    ))

    return {
        "valid_ratio": round(valid_ratio, 4),
        "mean_s": round(mean_s, 2),
        "median_s": round(median_s, 2),
        "mean_v": round(mean_v, 2),
        "median_v": round(median_v, 2),
        "lab_std": round(lab_std, 2),
        "dark_ratio": round(dark_ratio, 4),
        "very_dark_ratio": round(very_dark_ratio, 4),
        "highlight_ratio": round(highlight_ratio, 4),
        "white_ratio": round(white_ratio, 4),
        "overbright_ratio": round(overbright_ratio, 4),
        "clean_color_ratio": round(clean_color_ratio, 4),
    }

def median_color_from_patch_mask(patch_bgr, patch_mask):
    """
    只从 patch_mask 内像素取中位色。
    """
    pixels = patch_bgr[patch_mask > 0]

    if len(pixels) < 6:
        pixels = patch_bgr.reshape(-1, 3)

    median_bgr = np.median(pixels, axis=0).astype(np.uint8)

    median_hsv = cv2.cvtColor(
        median_bgr.reshape(1, 1, 3),
        cv2.COLOR_BGR2HSV
    ).reshape(3)

    return median_bgr.tolist(), median_hsv.tolist()


def box_intersects_pupil(box, pupil_box):
    """
    判断候选框是否和瞳孔 bbox 相交。
    这里作为安全检查，正常情况下左/右/下候选框不会碰到瞳孔。
    """
    x1, y1, x2, y2 = box
    px1, py1, px2, py2 = pupil_box

    return not (
        x2 <= px1 or
        x1 >= px2 or
        y2 <= py1 or
        y1 >= py2
    )


def extract_iris_patch_by_pupil_boundary(
    eye_bgr,
    pupil_info,
    patch_size=None,
    gap=None,
    debug=False
):
    """
    根据瞳孔 bbox 生成左、右、下三个候选 patch。
    激进版本：候选框直接贴着瞳孔边界，不额外留距离。
    """
    h, w = eye_bgr.shape[:2]
    min_dim = min(h, w)

    px1, py1, px2, py2 = pupil_info["bbox"]
    cx, cy = pupil_info["center"]

    pupil_w = px2 - px1
    pupil_h = py2 - py1

    if patch_size is None:
        # 当前眼睛 crop 较小，patch 不宜过大
        patch_size = int(np.clip(min_dim * 0.15, 10, 18))

    patch_size = int(patch_size)
    half = patch_size // 2

    if gap is None:
        # 激进模式：充分相信红色瞳孔框，直接贴边取虹膜颜色
        gap = 0

    candidates = []

    # 左侧候选框：右边界贴着瞳孔左边界
    left_x2 = px1 - gap
    left_x1 = left_x2 - patch_size
    left_y1 = int(round(cy - half))
    left_y2 = left_y1 + patch_size
    candidates.append(("left", left_x1, left_y1, left_x2, left_y2))

    # 右侧候选框：左边界贴着瞳孔右边界
    right_x1 = px2 + gap
    right_x2 = right_x1 + patch_size
    right_y1 = int(round(cy - half))
    right_y2 = right_y1 + patch_size
    candidates.append(("right", right_x1, right_y1, right_x2, right_y2))

    # 下侧候选框：上边界贴着瞳孔下边界
    down_x1 = int(round(cx - half))
    down_x2 = down_x1 + patch_size
    down_y1 = py2 + gap
    down_y2 = down_y1 + patch_size
    candidates.append(("down", down_x1, down_y1, down_x2, down_y2))

    scored = []

    for name, x1, y1, x2, y2 in candidates:
        x1c, y1c, x2c, y2c = _clip_box(x1, y1, x2, y2, w, h)
        box = (x1c, y1c, x2c, y2c)

        # clip 后太小就跳过
        if (x2c - x1c) < patch_size * 0.65 or (y2c - y1c) < patch_size * 0.65:
            continue

        # 安全检查：不能和瞳孔 bbox 相交
        # gap=0 时，贴边不算相交，因为 x2 <= px1 或 x1 >= px2 是合法的
        if box_intersects_pupil(box, (px1, py1, px2, py2)):
            continue

        patch_bgr = eye_bgr[y1c:y2c, x1c:x2c].copy()
        patch_mask = make_valid_color_mask(patch_bgr)

        score = score_boundary_candidate_patch(patch_bgr, patch_mask)

        scored.append({
            "name": name,
            "box": box,
            "patch_bgr": patch_bgr,
            "patch_mask": patch_mask,
            "score": score
        })

    if not scored:
        return {
            "ok": False,
            "reason": "no_boundary_candidate"
        }

    print("\n====== iris candidate scores ======")
    for item in scored:
        metrics = debug_patch_metrics(item["patch_bgr"], item["patch_mask"])

        print("\n", item["name"])
        print("score =", round(item["score"], 4))
        print("box =", item["box"])

        for k, v in metrics.items():
            print(k, "=", v)

    print("==================================\n")

    best = max(scored, key=lambda x: x["score"])

    if best["score"] < -1000:
        return {
            "ok": False,
            "reason": "all_candidates_bad",
            "candidates": scored
        }

    median_bgr, median_hsv = median_color_from_patch_mask(
        best["patch_bgr"],
        best["patch_mask"]
    )

    result = {
        "ok": True,
        "patch_bgr": best["patch_bgr"],
        "patch_mask": best["patch_mask"],
        "median_bgr": median_bgr,
        "median_hsv": median_hsv,
        "box": best["box"],
        "side": best["name"],
        "score": best["score"],
        "candidates": scored,
        "pupil": pupil_info,
    }

    if debug:
        dbg = eye_bgr.copy()

        # 红框：瞳孔边界
        cv2.rectangle(dbg, (px1, py1), (px2, py2), (0, 0, 255), 1)

        # 灰框：三个候选框
        for item in scored:
            x1, y1, x2, y2 = item["box"]
            cv2.rectangle(dbg, (x1, y1), (x2, y2), (180, 180, 180), 1)

        # 蓝框：最终选择框
        x1, y1, x2, y2 = best["box"]
        cv2.rectangle(dbg, (x1, y1), (x2, y2), (255, 0, 0), 2)

        result["debug_image"] = dbg

    return result

# ======================================================

# img = cv2.imread("../output/features/cat1_cat_eye_1.png")
#
# if img is None:
#     raise FileNotFoundError("图片读取失败：../output/features/cat1_cat_eye_0.png")
#
# pupil = detect_dark_pupil_simple(img)
#
# if pupil is None:
#     print("失败原因: pupil_not_found")
# else:
#     result = extract_iris_patch_by_pupil_boundary(
#         img,
#         pupil_info=pupil,
#         patch_size=12, #方块大小
#         gap=0,
#         debug=True
#     )
#
#     if result["ok"]:
#         print("选中的方向:", result["side"])
#         print("代表色 BGR:", result["median_bgr"])
#         print("代表色 HSV:", result["median_hsv"])
#
#         print("得分:", result["score"])
#         print("box:", result["box"])
#
#         os.makedirs("../output/features/pupil_image", exist_ok=True)
#
#         cv2.imwrite("../output/features/pupil_image/iris_patch.png", result["patch_bgr"])
#         cv2.imwrite("../output/features/pupil_image/iris_debug.png", result["debug_image"])
#         cv2.imwrite("../output/features/pupil_image/iris_patch_mask.png", result["patch_mask"])
#     else:
#         print("失败原因:", result["reason"])