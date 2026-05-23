from .extract_features import FeatureExtractor
from .Combine_workflow import recolor_eye_uv_by_eye_crop


def generate_eye_uv_texture(image_path: str):
    # 第一步：特征提取，拿到所有 crop 路径
    feature_extractor = FeatureExtractor()
    result = feature_extractor.extract(image_path)

    if result.get("status") != "success":
        return result

    # 第二步：过滤出眼睛 crop，逐个重绘眼球 UV
    eye_crops = [p for p in result.get("crop_paths", []) if "cat_eye" in p]
    recolored_results = []

    for eye_crop_path in eye_crops:
        recolor_result = recolor_eye_uv_by_eye_crop(eye_crop_path)
        recolored_results.append(recolor_result)

    result["recolored_results"] = recolored_results
    return result
