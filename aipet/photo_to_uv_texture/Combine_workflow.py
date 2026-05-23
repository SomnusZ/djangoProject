# from detect_pupil import detect_dark_pupil_simple,extract_iris_patch_by_pupil_boundary
# from redraw_eye import recolor_iris_template_hsv
from .detect_pupil import detect_dark_pupil_simple, extract_iris_patch_by_pupil_boundary
from .redraw_eye import recolor_iris_template_hsv
from pathlib import Path
import cv2

#整合了抓取虹膜和获得最终贴图
def recolor_eye_uv_by_eye_crop(
    eye_crop_path,
    patch_size=12,
    gap=0,
    debug=True,
):
    """
    输入上一轮提取出来的眼睛 crop 图，
    自动提取虹膜颜色，并重绘固定眼球 UV 模板。
    """

    eye_crop_path = Path(eye_crop_path)

    # 固定路径：
    # template_path = Path("../source/eye_uv_template4.png")
    # output_dir = Path("../output/features/pupil_image")
    template_path = Path(__file__).parent / "source" / "eye_uv_template4.png"
    output_dir = Path(__file__).parent / "output" / "features" / "pupil_image"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 读取眼睛 crop 图
    img = cv2.imread(str(eye_crop_path))

    if img is None:
        raise FileNotFoundError(f"图片读取失败：{eye_crop_path}")

    # 2. 检测瞳孔
    pupil = detect_dark_pupil_simple(img)

    if pupil is None:
        return {
            "ok": False,
            "reason": "pupil_not_found",
            "eye_crop_path": str(eye_crop_path),
        }

    # 3. 从瞳孔边界旁边取虹膜颜色
    iris_result = extract_iris_patch_by_pupil_boundary(
        img,
        pupil_info=pupil,
        patch_size=patch_size,
        gap=gap,
        debug=debug,
    )

    if not iris_result["ok"]:
        return {
            "ok": False,
            "reason": iris_result.get("reason", "iris_extract_failed"),
            "eye_crop_path": str(eye_crop_path),
        }

    # 4. 关键：用提取出来的 median_bgr 作为 base_bgr
    base_bgr = iris_result["median_bgr"]
    base_bgr = tuple(int(x) for x in base_bgr)

    # 5. 保存虹膜取色 debug 结果
    stem = eye_crop_path.stem

    iris_patch_path = output_dir / f"{stem}_iris_patch.png"
    iris_debug_path = output_dir / f"{stem}_iris_debug.png"
    iris_patch_mask_path = output_dir / f"{stem}_iris_patch_mask.png"

    cv2.imwrite(str(iris_patch_path), iris_result["patch_bgr"])
    cv2.imwrite(str(iris_debug_path), iris_result["debug_image"])
    cv2.imwrite(str(iris_patch_mask_path), iris_result["patch_mask"])

    # 6. 读取固定 UV 模板
    template = cv2.imread(str(template_path))

    if template is None:
        raise FileNotFoundError(f"Failed to read template image: {template_path}")

    # 7. 用虹膜颜色重绘 UV 模板
    recolored, iris_mask, pupil_mask, fg_mask = recolor_iris_template_hsv(
        template,
        base_bgr=base_bgr,
        black_threshold=15,
        sat_boost=1.20,
        val_scale=0.92,
        white_thresh=245,
        auto_roi=True,
        debug=debug,
    )

    # 8. 保存重绘结果
    recolored_path = output_dir / f"{stem}_eye_uv_recolored_hsv.png"
    iris_mask_path = output_dir / f"{stem}_eye_uv_mask_hsv.png"
    pupil_mask_path = output_dir / f"{stem}_eye_uv_pupil_mask_hsv.png"
    fg_mask_path = output_dir / f"{stem}_eye_uv_fg_mask.png"

    cv2.imwrite(str(recolored_path), recolored)
    cv2.imwrite(str(iris_mask_path), iris_mask)
    cv2.imwrite(str(pupil_mask_path), pupil_mask)
    cv2.imwrite(str(fg_mask_path), fg_mask)

    return {
        "ok": True,
        "eye_crop_path": str(eye_crop_path),
        "template_path": str(template_path),

        "base_bgr": base_bgr,
        "median_bgr": base_bgr,
        "median_hsv": iris_result["median_hsv"],
        "side": iris_result["side"],
        "score": iris_result["score"],
        "box": iris_result["box"],

        "iris_patch_path": str(iris_patch_path),
        "iris_debug_path": str(iris_debug_path),
        "iris_patch_mask_path": str(iris_patch_mask_path),

        "recolored_path": str(recolored_path),
        "iris_mask_path": str(iris_mask_path),
        "pupil_mask_path": str(pupil_mask_path),
        "fg_mask_path": str(fg_mask_path),
    }

if __name__ == "__main__":
    eye_crop_path = "../output/features/cat1_cat_eye_0.png"

    result = recolor_eye_uv_by_eye_crop(eye_crop_path)

    if result["ok"]:
        print("选中的方向:", result["side"])
        print("代表色 BGR:", result["base_bgr"])
        print("代表色 HSV:", result["median_hsv"])
        print("得分:", result["score"])
        print("box:", result["box"])
        print("最终重绘UV:", result["recolored_path"])
    else:
        print("失败原因:", result["reason"])

