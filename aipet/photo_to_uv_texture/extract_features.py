"""
Extract facial features from animal (or any) photos using OWLv2 + SAM 2.

OWLv2 (Google) detects bounding boxes for each named feature via open-vocabulary
detection. SAM 2 (Meta) converts each box into a precise pixel mask.

Install dependencies before running:
    pip install transformers
    pip install git+https://github.com/facebookresearch/sam2.git

Usage:
    # Process all images in UserImage/
    python src/extract_features.py

    # Single image
    python src/extract_features.py --image UserImage/cat1.jpg

    # Custom feature list
    python src/extract_features.py --image UserImage/cat1.jpg --features "cat eye" "cat nose"

    # Adjust detection confidence threshold (default 0.2)
    python src/extract_features.py --threshold 0.3

    # Larger / more accurate OWLv2 model
    python src/extract_features.py --model-size large
"""

import argparse
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont



sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ROOT = Path(__file__).parent.parent
ROOT = Path(__file__).parent
USERIMAGE_DIR = ROOT / "UserImage"
OUTPUT_DIR = ROOT / "output" / "features"

# Default features — prefix with the subject for best OWLv2 accuracy
DEFAULT_FEATURES = ["cat eye", "cat nose", "cat mouth", "cat ear"]

OWLV2_MODELS = {
    "base":  "google/owlv2-base-patch16-ensemble",
    "large": "google/owlv2-large-patch14-ensemble",
}

# RGBA overlay colours per feature label keyword
FEATURE_COLORS: dict[str, tuple[int, int, int, int]] = {
    "eye":   (255,  80,  80, 140),
    "nose":  ( 80, 220,  80, 140),
    "mouth": ( 80,  80, 255, 140),
    "ear":   (255, 210,  50, 140),
}
DEFAULT_COLOR: tuple[int, int, int, int] = (200, 200, 200, 140)

DEFAULT_THRESHOLD = 0.2
NMS_IOU_THRESHOLD = 0.5   # suppress heavily-overlapping boxes of the same label


# ── Model loading ─────────────────────────────────────────────────────────────

def load_owlv2(model_size: str = "base"):
    """Load OWLv2 processor and model."""
    import torch
    from transformers import Owlv2ForObjectDetection, Owlv2Processor

    model_id = OWLV2_MODELS[model_size]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading OWLv2 ({model_size}) on {device}…")
    processor = Owlv2Processor.from_pretrained(model_id)
    model = Owlv2ForObjectDetection.from_pretrained(model_id).to(device)
    model.eval()
    print("OWLv2 ready")
    return model, processor, device


def load_sam2():
    """Load SAM 2 image predictor."""
    import torch
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading SAM 2 on {device}…")
    predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2-hiera-large", device=device)
    print("SAM 2 ready")
    return predictor


# ── NMS helper ────────────────────────────────────────────────────────────────

def _iou(box_a: list[float], box_b: list[float]) -> float:
    """Intersection-over-union for two [x0, y0, x1, y1] boxes."""
    xi0 = max(box_a[0], box_b[0])
    yi0 = max(box_a[1], box_b[1])
    xi1 = min(box_a[2], box_b[2])
    yi1 = min(box_a[3], box_b[3])
    inter = max(0.0, xi1 - xi0) * max(0.0, yi1 - yi0)
    area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
    area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _nms(
    boxes: list[list[float]],
    scores: list[float],
    iou_threshold: float = NMS_IOU_THRESHOLD,
) -> list[int]:
    """Return indices of boxes to keep after non-maximum suppression."""
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    keep: list[int] = []
    while order:
        i = order.pop(0)
        keep.append(i)
        order = [j for j in order if _iou(boxes[i], boxes[j]) < iou_threshold]
    return keep


# ── Detection (OWLv2) ─────────────────────────────────────────────────────────

def detect_features(
    image: Image.Image,
    features: list[str],
    model,
    processor,
    device: str,
    threshold: float,
) -> dict[str, list[list[float]]]:
    """Run OWLv2 open-vocabulary detection for all features in one forward pass.

    Returns a dict mapping feature label → list of [x0, y0, x1, y1] boxes
    (only features with at least one detection above threshold).
    """
    import torch

    # OWLv2 expects a list-of-lists: one list of text queries per image
    texts = [features]
    inputs = processor(text=texts, images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    results = processor.post_process_grounded_object_detection(
        outputs,
        threshold=threshold,
        target_sizes=[(image.height, image.width)],
    )

    found: dict[str, list[list[float]]] = {}
    raw_boxes   = results[0]["boxes"].tolist()
    raw_scores  = results[0]["scores"].tolist()
    raw_labels  = results[0]["labels"].tolist()

    # Group by feature label, then apply per-label NMS
    label_groups: dict[int, tuple[list, list]] = {}
    for box, score, label in zip(raw_boxes, raw_scores, raw_labels):
        if label not in label_groups:
            label_groups[label] = ([], [])
        label_groups[label][0].append(box)
        label_groups[label][1].append(score)

    for label_idx, (boxes, scores) in label_groups.items():
        keep = _nms(boxes, scores)
        feature_name = features[label_idx]
        found[feature_name] = [boxes[i] for i in keep]
        print(f"    {feature_name!r}: {len(found[feature_name])} detection(s)")

    for f in features:
        if f not in found:
            print(f"    {f!r}: not found")

    return found


# ── Segmentation (SAM 2) ──────────────────────────────────────────────────────

def segment_boxes(
    image: Image.Image,
    feature_boxes: dict[str, list[list[float]]],
    predictor,
) -> dict[str, list[np.ndarray]]:
    """Convert OWLv2 bounding boxes into SAM 2 pixel masks.

    Returns a dict mapping feature label → list of boolean (H, W) masks.
    """
    import torch

    img_array = np.array(image.convert("RGB"))
    masks_out: dict[str, list[np.ndarray]] = {}

    with torch.inference_mode():
        predictor.set_image(img_array)

        for feature, boxes in feature_boxes.items():
            feature_masks: list[np.ndarray] = []
            for box in boxes:
                box_np = np.array(box, dtype=np.float32)
                masks, _, _ = predictor.predict(
                    point_coords=None,
                    point_labels=None,
                    box=box_np,
                    multimask_output=False,
                )
                feature_masks.append(masks[0])  # shape (H, W) bool
            masks_out[feature] = feature_masks

    return masks_out


# ── Output helpers ────────────────────────────────────────────────────────────

def _mask_bounds(mask: np.ndarray, pad: int = 10) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) pixel bounds for a boolean mask."""
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin = int(np.where(rows)[0][0])
    rmax = int(np.where(rows)[0][-1])
    cmin = int(np.where(cols)[0][0])
    cmax = int(np.where(cols)[0][-1])
    h, w = mask.shape
    return (
        max(0, cmin - pad),
        max(0, rmin - pad),
        min(w, cmax + pad),
        min(h, rmax + pad),
    )


def _feature_color(feature: str) -> tuple[int, int, int, int]:
    """Pick overlay colour by matching any keyword in the feature string."""
    for keyword, color in FEATURE_COLORS.items():
        if keyword in feature.lower():
            return color
    return DEFAULT_COLOR


def save_feature_crops(
    image: Image.Image,
    feature_masks: dict[str, list[np.ndarray]],
    stem: str,
    out_dir: Path,
) -> None:
    """Save each detected feature as a transparent RGBA PNG crop."""
    img_rgba = np.array(image.convert("RGBA"))

    for feature, masks in feature_masks.items():
        # Use the last word of the feature label as the filename part (e.g. "cat eye" → "eye")
        short = feature.replace(" ", "_")
        for i, mask in enumerate(masks):
            alpha = (mask * 255).astype(np.uint8)
            cropped = img_rgba.copy()
            cropped[:, :, 3] = alpha

            left, top, right, bottom = _mask_bounds(mask)
            crop = Image.fromarray(cropped).crop((left, top, right, bottom))

            suffix = f"_{i}" if len(masks) > 1 else ""
            out_path = out_dir / f"{stem}_{short}{suffix}.png"
            crop.save(out_path)
            print(f"    Crop : {out_path.name}")


def save_overlay(
    image: Image.Image,
    feature_masks: dict[str, list[np.ndarray]],
    feature_boxes: dict[str, list[list[float]]],
    stem: str,
    out_dir: Path,
) -> None:
    """Save an annotated image with coloured mask overlays and bounding boxes."""
    base = image.convert("RGBA").copy()
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))

    for feature, masks in feature_masks.items():
        color = _feature_color(feature)
        for mask in masks:
            mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
            color_fill = Image.new("RGBA", base.size, color)
            layer.paste(color_fill, mask=mask_img)

    result = Image.alpha_composite(base, layer).convert("RGB")
    draw = ImageDraw.Draw(result)

    # Draw bounding boxes
    for feature, boxes in feature_boxes.items():
        r, g, b, _ = _feature_color(feature)
        for box in boxes:
            draw.rectangle(box, outline=(r, g, b), width=3)

    # Legend
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        font = ImageFont.load_default()

    x, y = 10, 10
    for feature in feature_masks:
        r, g, b, _ = _feature_color(feature)
        draw.rectangle([x, y, x + 18, y + 18], fill=(r, g, b))
        draw.text((x + 24, y), feature, fill=(255, 255, 255), font=font)
        y += 26

    out_path = out_dir / f"{stem}_overlay.jpg"
    result.save(out_path, quality=92)
    print(f"    Overlay: {out_path.name}")


# ── Per-image orchestration ───────────────────────────────────────────────────

def process_image(
    image_path: Path,
    features: list[str],
    owlv2_model,
    owlv2_processor,
    device: str,
    sam_predictor,
    threshold: float,
    out_dir: Path,
) -> None:
    print(f"\n{'─' * 60}")
    print(f"Image : {image_path.name}")

    image = Image.open(image_path).convert("RGB")
    print(f"Size  : {image.width}×{image.height}")

    print("  OWLv2 detection…")
    feature_boxes = detect_features(
        image, features, owlv2_model, owlv2_processor, device, threshold
    )

    if not feature_boxes:
        print("  No features detected — skipping")
        return

    print("  SAM 2 segmentation…")
    feature_masks = segment_boxes(image, feature_boxes, sam_predictor)

    print("  Saving outputs…")
    save_feature_crops(image, feature_masks, image_path.stem, out_dir)
    save_overlay(image, feature_masks, feature_boxes, image_path.stem, out_dir)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract animal facial features with OWLv2 + SAM 2"
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Path to a single image (default: all images in UserImage/)",
    )
    parser.add_argument(
        "--features",
        nargs="+",
        default=DEFAULT_FEATURES,
        metavar="FEATURE",
        help=(
            "Feature text prompts. Prefix with the subject for best results "
            f"(default: {DEFAULT_FEATURES})"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Minimum detection confidence (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--model-size",
        choices=list(OWLV2_MODELS),
        default="base",
        help="OWLv2 model size: 'base' is faster, 'large' is more accurate (default: base)",
    )
    return parser.parse_args()

class FeatureExtractor:
    def __init__(
        self,
        features: list[str] = DEFAULT_FEATURES,
        threshold: float = DEFAULT_THRESHOLD,
        model_size: str = "base",
        out_dir: Path = OUTPUT_DIR,
    ):
        self.features = features
        self.threshold = threshold
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.owlv2_model, self.owlv2_processor, self.device = load_owlv2(model_size)
        self.sam_predictor = load_sam2()

    def extract(self, image_path: str | Path) -> dict:
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"图片不存在: {image_path}")

        image = Image.open(image_path).convert("RGB")

        feature_boxes = detect_features(
            image=image,
            features=self.features,
            model=self.owlv2_model,
            processor=self.owlv2_processor,
            device=self.device,
            threshold=self.threshold,
        )

        if not feature_boxes:
            return {
                "status": "not_found",
                "image_path": str(image_path),
                "features": {},
                "message": "No features detected",
            }

        feature_masks = segment_boxes(
            image=image,
            feature_boxes=feature_boxes,
            predictor=self.sam_predictor,
        )

        save_feature_crops(
            image=image,
            feature_masks=feature_masks,
            stem=image_path.stem,
            out_dir=self.out_dir,
        )

        save_overlay(
            image=image,
            feature_masks=feature_masks,
            feature_boxes=feature_boxes,
            stem=image_path.stem,
            out_dir=self.out_dir,
        )

        crop_paths = []
        for feature, masks in feature_masks.items():
            short = feature.replace(" ", "_")
            for i, _ in enumerate(masks):
                suffix = f"_{i}" if len(masks) > 1 else ""
                crop_paths.append(str(self.out_dir / f"{image_path.stem}_{short}{suffix}.png"))

        overlay_path = str(self.out_dir / f"{image_path.stem}_overlay.jpg")

        return {
            "status": "success",
            "image_path": str(image_path),
            "overlay_path": overlay_path,
            "crop_paths": crop_paths,
            "feature_boxes": feature_boxes,
            "features": {
                feature: {
                    "count": len(masks),
                }
                for feature, masks in feature_masks.items()
            },
        }

def main() -> None:
    args = parse_args()

    if args.image:
        images = [Path(args.image)]
    else:
        images = sorted(USERIMAGE_DIR.glob("*.jpg")) + sorted(USERIMAGE_DIR.glob("*.png"))

    if not images:
        print(f"No images found in {USERIMAGE_DIR}")
        sys.exit(1)

    extractor = FeatureExtractor(
        features=args.features,
        threshold=args.threshold,
        model_size=args.model_size,
        out_dir=OUTPUT_DIR,
    )

    for image_path in images:
        try:
            result = extractor.extract(image_path)
            print(result)
        except Exception as exc:
            print(f"ERROR processing {image_path.name}: {exc}")

    print("Done. Outputs written to:", OUTPUT_DIR)
# def main() -> None:
#     args = parse_args()
#
#     OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
#
#     if args.image:
#         images = [Path(args.image)]
#     else:
#         images = sorted(USERIMAGE_DIR.glob("*.jpg")) + sorted(USERIMAGE_DIR.glob("*.png"))
#
#     if not images:
#         print(f"No images found in {USERIMAGE_DIR}")
#         sys.exit(1)
#
#     print(f"Features  : {args.features}")
#     print(f"Threshold : {args.threshold}")
#     print(f"Images    : {len(images)}")
#     print(f"Output    : {OUTPUT_DIR}")
#
#     owlv2_model, owlv2_processor, device = load_owlv2(args.model_size)
#     sam_predictor = load_sam2()
#
#     for image_path in images:
#         try:
#             process_image(
#                 image_path, args.features,
#                 owlv2_model, owlv2_processor, device,
#                 sam_predictor, args.threshold, OUTPUT_DIR,
#             )
#         except Exception as exc:
#             print(f"  ERROR processing {image_path.name}: {exc}")
#
#     print(f"\n{'─' * 60}")
#     print("Done. Outputs written to:", OUTPUT_DIR)


# if __name__ == "__main__":
#     image_path = "../UserImage/cat1.jpg"
#     feature_extractor = FeatureExtractor()
#     result = feature_extractor.extract(image_path)