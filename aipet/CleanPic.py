from pathlib import Path
import numpy as np
from ultralytics import YOLO
from io import BytesIO
from PIL import Image, ImageOps
from rembg import remove
import os

_AIPET_DIR = Path(__file__).resolve().parent

#检测模型
yolo = YOLO(str(_AIPET_DIR / 'model' / 'yolov8m.pt'))
PET_CLASSES = {15: "cat", 16: "dog"}

class ImageProcessError(Exception):
    pass

class NoPetDetectedError(Exception):
    pass

# 分类模型（识别品种）
yolo_classify = YOLO(str(_AIPET_DIR / 'model' / 'yolov8m-cls.pt'))

def clean_pic(task_id: str, file_bytes: bytes):
    """
    输入：任务ID、文件二进制流
    输出：裁剪后图片保存路径
    """
    output_dir = _AIPET_DIR / "image" / "ImageAfterClean"
    output_dir.mkdir(parents=True, exist_ok=True)
    # 1️⃣ 加载与规范化图像
    try:
        img = Image.open(BytesIO(file_bytes)).convert("RGB")
        img = ImageOps.exif_transpose(img)
        img.thumbnail((1280, 1280))
    except Exception as e:
        raise ImageProcessError(f"Invalid image input: {e}")

    # 2️⃣ 检测猫 / 狗
    try:
        res = yolo.predict(
            source=np.array(img),
            conf=0.3,
            verbose=False
        )[0]
    except Exception as e:
        raise ImageProcessError(f"YOLO detect failed: {e}")

    pet_bbox = None
    pet_type = None
    for box in res.boxes:
        cls_id = int(box.cls.item())
        if cls_id in PET_CLASSES:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            pet_bbox = (x1, y1, x2, y2)
            pet_type = PET_CLASSES[cls_id]
            break

    #没有识别到脸需要让用户重新上传
    if not pet_bbox:
        raise NoPetDetectedError("No cat or dog detected in image")

    # 3️⃣ 裁剪并保存
    clean_path = output_dir / f"{task_id}.png"
    # 剪裁后，识别背景并移除

    try:
        pet_img = img.crop(pet_bbox)
        pet_img_rembg = remove(pet_img)
        pet_img_rembg.save(clean_path)
    except Exception as e:
        raise ImageProcessError(f"Failed to save cropped image: {e}")
    if not clean_path.exists():
        raise ImageProcessError(f"Image not saved: {clean_path}")

    #识别品种
    # 4️⃣ 分类识别品种
    try:
        results = yolo_classify.predict(
            source=str(clean_path),
            save=False,
            verbose=False
        )
    except Exception as e:
        raise ImageProcessError(f"YOLO classify failed: {e}")

    breed = None
    confidence = 0.0
    for r in results:
        breed = r.names[r.probs.top1]
        confidence = float(r.probs.top1conf.item())

    return {
        "path": str(clean_path),
        "breed": breed,#具体品种对应模板
        "confidence": confidence,
        "type": pet_type #区分猫狗模板
    }
