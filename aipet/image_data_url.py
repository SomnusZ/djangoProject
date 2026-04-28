import mimetypes,base64
from pathlib import Path

def build_image_data_url(image_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    mime_type = mime_type or "image/png"

    if not mime_type.startswith("image/"):
        raise ValueError("Invalid image mime type")
    raw = image_path.read_bytes()

    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("Image too large for Meshy")

    b64 = base64.b64encode(raw).decode()
    return f"data:{mime_type};base64,{b64}"

    # 检测图片格式
    # mime_type, _ = mimetypes.guess_type(image_path)
    # if not mime_type:
    #     mime_type = "image/png"
    #
    # # --- 图片转 Data URI ---
    #
    # with open(image_path, "rb") as f:
    #     image_b64 = base64.b64encode(f.read()).decode()
    #
    # image_data_url = f"data:{mime_type};base64,{image_b64}"