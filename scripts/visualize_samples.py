"""
scripts/visualize_samples.py

Run inference on 5 real test set images (one per class) using the trained RT-DETR model,
draw bounding boxes and confidence scores, execute sample questions via the reasoning engine,
and save annotated preview images to artifacts/sample_predictions/.
"""

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.detector import RTDETRDetector
from app.reasoning import answer_question

CLASS_NAMES = {
    0: "cardboard box",
    1: "forklift",
    2: "freight container",
    3: "wood pallet",
    4: "truck",
}

COLORS = {
    "cardboard box": "#E67E22",       # Orange
    "forklift": "#F1C40F",            # Yellow
    "freight container": "#2980B9",   # Blue
    "wood pallet": "#27AE60",         # Green
    "truck": "#E74C3C",               # Red
}

def find_sample_images():
    data_dir = ROOT / "data" / "logistics_2500" / "test"
    labels_dir = data_dir / "labels"
    images_dir = data_dir / "images"

    class_samples = {}
    for lbl in sorted(labels_dir.glob("*.txt")):
        lines = lbl.read_text().strip().splitlines()
        if not lines:
            continue
        cls_id = int(lines[0].split()[0])
        if cls_id not in class_samples:
            img_path = images_dir / (lbl.stem + ".jpg")
            if img_path.exists():
                class_samples[cls_id] = img_path
        if len(class_samples) == 5:
            break
    return class_samples

def annotate_image(img: Image.Image, detections: list[dict]) -> Image.Image:
    draw_img = img.copy()
    draw = ImageDraw.Draw(draw_img)
    w, h = img.size

    # Choose a stroke width proportional to image size
    line_w = max(2, int(min(w, h) / 200))

    for d in detections:
        cls_name = d["class"]
        conf = d["confidence"]
        bbox = d["bbox"]
        color = COLORS.get(cls_name, "#FFFFFF")

        x1, y1 = bbox["x1"], bbox["y1"]
        x2, y2 = bbox["x2"], bbox["y2"]

        # Draw box
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_w)

        # Draw badge label
        label_text = f"{cls_name} {conf:.2f}"
        # Text background
        text_bbox = draw.textbbox((x1, max(0, y1 - 18)), label_text)
        draw.rectangle(text_bbox, fill=color)
        draw.text((x1 + 2, max(0, y1 - 18)), label_text, fill="#000000")

    return draw_img

def main():
    print("=" * 70)
    print("LOGISTICS OBJECT DETECTION & REASONING — LIVE SAMPLE RUN")
    print("=" * 70)

    weights_path = ROOT / "weights" / "best.pt"
    if not weights_path.exists():
        print(f"Error: weights not found at {weights_path}")
        sys.exit(1)

    print(f"\n[1/3] Loading RT-DETR detector from {weights_path}...")
    detector = RTDETRDetector(weights=weights_path, conf_threshold=0.20)
    print("[1/3] Detector loaded successfully.")

    out_dir = ROOT / "artifacts" / "sample_predictions"
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = find_sample_images()
    print(f"\n[2/3] Selected 5 representative test images (1 per class):")

    sample_questions = {
        "cardboard box": "How many cardboard boxes are visible?",
        "forklift": "Is there a forklift in the image?",
        "freight container": "How many freight containers are in this image?",
        "wood pallet": "Are there wood pallets present?",
        "truck": "Is there a truck visible?",
    }

    for cls_id in sorted(samples.keys()):
        cls_name = CLASS_NAMES[cls_id]
        img_path = samples[cls_id]
        print("\n" + "-" * 70)
        print(f"SAMPLE {cls_id + 1}: Target Class = '{cls_name.upper()}'")
        print(f"Image File   : {img_path.name}")

        img = Image.open(img_path).convert("RGB")
        w, h = img.size
        print(f"Image Size   : {w}x{h} px")

        # 1. Run detection
        detections = detector.detect(img)
        print(f"Detections   : Found {len(detections)} object(s)")
        for i, det in enumerate(detections, 1):
            b = det["bbox"]
            print(f"   [{i}] {det['class']:18s} | Conf: {det['confidence']:.2f} | BBox: ({b['x1']:.1f}, {b['y1']:.1f}, {b['x2']:.1f}, {b['y2']:.1f})")

        # 2. Run reasoning Q&A
        question = sample_questions[cls_name]
        reasoning_res = answer_question(question=question, detections=detections)
        print(f"\nQ&A Demonstration:")
        print(f"   Question  : \"{question}\"")
        print(f"   Intent    : {reasoning_res['intent']}")
        print(f"   Confidence: {reasoning_res['confidence']}")
        print(f"   Answer    : {reasoning_res['answer']}")

        # 3. Annotate & Save
        annotated = annotate_image(img, detections)
        safe_name = cls_name.replace(" ", "_")
        out_path = out_dir / f"sample_{cls_id + 1}_{safe_name}.jpg"
        annotated.save(out_path, quality=95)
        print(f"Saved Image  : {out_path}")

    print("\n" + "=" * 70)
    print(f"All 5 sample images annotated and saved to: {out_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()
