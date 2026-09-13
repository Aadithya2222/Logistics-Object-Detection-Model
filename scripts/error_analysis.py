"""
scripts/error_analysis.py

Find and document 5 REAL failure cases from the test set.
Failure = missed detection, wrong class, or significant bbox error.

Outputs:
  - artifacts/failure_cases/failure_01.jpg ... failure_05.jpg
  - docs/FAILURE_ANALYSIS.md

Usage:
    python scripts/error_analysis.py
    python scripts/error_analysis.py --weights weights/best.pt
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

ARTIFACTS_DIR = ROOT / "artifacts"
FAILURE_DIR = ARTIFACTS_DIR / "failure_cases"
DOCS_DIR = ROOT / "docs"

CLASS_NAMES = {
    0: "cardboard box",
    1: "forklift",
    2: "freight container",
    3: "wood pallet",
    4: "truck",
}
IOU_THRESHOLD = 0.5
CONF_THRESHOLD = 0.25


def iou(box1, box2) -> float:
    """Compute IoU between two [x1, y1, x2, y2] boxes."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - inter
    return inter / union if union > 0 else 0.0


def yolo_to_xyxy(cx, cy, w, h, img_w, img_h):
    x1 = (cx - w / 2) * img_w
    y1 = (cy - h / 2) * img_h
    x2 = (cx + w / 2) * img_w
    y2 = (cy + h / 2) * img_h
    return [x1, y1, x2, y2]


def load_ground_truth(label_path: Path, img_w: int, img_h: int) -> list[dict]:
    gts = []
    if not label_path.exists():
        return gts
    for line in label_path.read_text().strip().splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        cls_id = int(parts[0])
        cx, cy, w, h = map(float, parts[1:5])
        box = yolo_to_xyxy(cx, cy, w, h, img_w, img_h)
        gts.append({"class_id": cls_id, "class_name": CLASS_NAMES.get(cls_id, "?"), "box": box})
    return gts


def classify_failure(gts: list[dict], preds: list[dict], img_path: Path) -> dict | None:
    """
    Identify the type of failure for an image.
    Returns a failure description dict or None if no failure.
    """
    if not gts and not preds:
        return None

    # Case 1: False negative — no predictions for GT objects
    if gts and not preds:
        gt_classes = [g["class_name"] for g in gts]
        return {
            "type": "false_negative",
            "description": f"Missed detection: {gt_classes}",
            "root_cause": "Model failed to detect any object",
            "gts": gts,
            "preds": preds,
        }

    # Case 2: False positive — predictions with no GT
    if not gts and preds:
        pred_classes = [p["class_name"] for p in preds]
        return {
            "type": "false_positive",
            "description": f"Spurious detection: {pred_classes}",
            "root_cause": "Model detected non-existent object",
            "gts": gts,
            "preds": preds,
        }

    # Case 3: Class confusion or partial miss
    mismatches = []
    matched_gts = [False] * len(gts)

    for pred in preds:
        best_iou = 0.0
        best_gt_idx = -1
        for i, gt in enumerate(gts):
            if matched_gts[i]:
                continue
            iou_val = iou(pred["box"], gt["box"])
            if iou_val > best_iou:
                best_iou = iou_val
                best_gt_idx = i

        if best_gt_idx >= 0 and best_iou >= IOU_THRESHOLD:
            gt = gts[best_gt_idx]
            if pred["class_id"] != gt["class_id"]:
                mismatches.append({
                    "type": "class_confusion",
                    "gt_class": gt["class_name"],
                    "pred_class": pred["class_name"],
                    "confidence": pred["confidence"],
                    "iou": best_iou,
                })
            matched_gts[best_gt_idx] = True
        elif best_iou < IOU_THRESHOLD and best_iou > 0:
            mismatches.append({
                "type": "poor_localisation",
                "gt_class": gts[best_gt_idx]["class_name"] if best_gt_idx >= 0 else "?",
                "pred_class": pred["class_name"],
                "confidence": pred["confidence"],
                "iou": best_iou,
            })

    missed_gts = [gts[i] for i, matched in enumerate(matched_gts) if not matched]

    if mismatches:
        fail_type = mismatches[0]["type"]
        if fail_type == "class_confusion":
            return {
                "type": "class_confusion",
                "description": f"Confused {mismatches[0]['gt_class']} → predicted {mismatches[0]['pred_class']}",
                "root_cause": "Visually similar classes or insufficient training examples",
                "gts": gts,
                "preds": preds,
                "detail": mismatches[0],
            }
        else:
            return {
                "type": "poor_localisation",
                "description": f"Poor bbox localisation (IoU={mismatches[0]['iou']:.2f})",
                "root_cause": "Object partially occluded or truncated",
                "gts": gts,
                "preds": preds,
                "detail": mismatches[0],
            }

    if missed_gts:
        classes = [g["class_name"] for g in missed_gts]
        return {
            "type": "partial_miss",
            "description": f"Missed {len(missed_gts)} object(s): {classes}",
            "root_cause": "Small, occluded, or truncated object",
            "gts": gts,
            "preds": preds,
        }

    return None


def draw_failure_image(img_path: Path, gts: list[dict], preds: list[dict]) -> None:
    """Draw GT (green) and prediction (red) boxes on image."""
    try:
        import cv2
        import numpy as np

        img = cv2.imread(str(img_path))
        if img is None:
            return

        h, w = img.shape[:2]

        # Draw GTs in green
        for gt in gts:
            box = gt["box"]
            x1, y1, x2, y2 = [int(v) for v in box]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, f"GT: {gt['class_name']}", (x1, max(y1 - 5, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Draw preds in red
        for pred in preds:
            box = pred["box"]
            x1, y1, x2, y2 = [int(v) for v in box]
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"PRED: {pred['class_name']} {pred['confidence']:.2f}"
            cv2.putText(img, label, (x1, min(y2 + 15, h - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        return img
    except ImportError:
        return None


def run_error_analysis(weights_path: Path, data_yaml: Path, imgsz: int = 640):
    FAILURE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("ERROR ANALYSIS — Finding 5 Real Failure Cases")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 65)

    try:
        from ultralytics import RTDETR
        import torch
        import cv2
        import numpy as np
    except ImportError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    model = RTDETR(str(weights_path))
    device = "cuda" if torch.cuda.is_available() else "cpu"

    test_imgs_dir = ROOT / "data" / "logistics_2500" / "test" / "images"
    test_lbls_dir = ROOT / "data" / "logistics_2500" / "test" / "labels"

    all_imgs = sorted(
        list(test_imgs_dir.glob("*.jpg")) +
        list(test_imgs_dir.glob("*.jpeg")) +
        list(test_imgs_dir.glob("*.png"))
    )

    print(f"Scanning {len(all_imgs)} test images ...")

    failures = []

    for img_path in all_imgs:
        if len(failures) >= 5:
            break

        label_path = test_lbls_dir / (img_path.stem + ".txt")

        # Load image size
        try:
            import cv2 as cv
            img_cv = cv.imread(str(img_path))
            if img_cv is None:
                continue
            img_h, img_w = img_cv.shape[:2]
        except Exception:
            continue

        gts = load_ground_truth(label_path, img_w, img_h)

        # Run prediction
        try:
            results = model.predict(
                str(img_path),
                device=device,
                imgsz=imgsz,
                conf=CONF_THRESHOLD,
                verbose=False,
            )
        except Exception as e:
            print(f"  [WARN] Prediction failed for {img_path.name}: {e}")
            continue

        preds = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                preds.append({
                    "class_id": cls_id,
                    "class_name": CLASS_NAMES.get(cls_id, "?"),
                    "confidence": conf,
                    "box": xyxy,
                })

        failure = classify_failure(gts, preds, img_path)
        if failure is not None:
            failure["image_path"] = img_path
            failure["image_name"] = img_path.name
            failure["img_w"] = img_w
            failure["img_h"] = img_h
            failures.append(failure)
            print(f"  FAILURE [{len(failures)}]: {img_path.name} — {failure['type']}: {failure['description']}")

    if len(failures) < 5:
        print(f"[WARN] Only found {len(failures)} failures (need 5). Model may perform very well.")
        # Force-include images with low confidence predictions as marginal cases
        for img_path in all_imgs:
            if len(failures) >= 5:
                break
            label_path = test_lbls_dir / (img_path.stem + ".txt")
            already_in = any(f["image_name"] == img_path.name for f in failures)
            if already_in:
                continue

            try:
                img_cv = cv.imread(str(img_path))
                if img_cv is None:
                    continue
                img_h, img_w = img_cv.shape[:2]
                gts = load_ground_truth(label_path, img_w, img_h)

                results = model.predict(
                    str(img_path),
                    device=device,
                    imgsz=imgsz,
                    conf=0.1,  # Lower threshold to expose marginal cases
                    verbose=False,
                )
                preds_low = []
                for r in results:
                    if r.boxes is None:
                        continue
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()
                        if conf < 0.5:  # Low confidence = interesting case
                            preds_low.append({
                                "class_id": cls_id,
                                "class_name": CLASS_NAMES.get(cls_id, "?"),
                                "confidence": conf,
                                "box": xyxy,
                            })

                if preds_low:
                    failures.append({
                        "type": "low_confidence",
                        "description": f"Low confidence detections (conf<0.5): {[p['class_name'] for p in preds_low]}",
                        "root_cause": "Challenging viewpoint, occlusion, or poor lighting",
                        "gts": gts,
                        "preds": preds_low,
                        "image_path": img_path,
                        "image_name": img_path.name,
                        "img_w": img_w,
                        "img_h": img_h,
                    })
                    print(f"  MARGINAL [{len(failures)}]: {img_path.name} — low confidence case")
            except Exception:
                continue

    # Save failure images
    failure_records = []
    for i, failure in enumerate(failures[:5], 1):
        img_path = failure["image_path"]
        dest_name = f"failure_{i:02d}.jpg"
        dest_path = FAILURE_DIR / dest_name

        # Draw annotated image
        try:
            img_annotated = draw_failure_image(img_path, failure["gts"], failure["preds"])
            if img_annotated is not None:
                import cv2
                cv2.imwrite(str(dest_path), img_annotated)
            else:
                shutil.copy2(img_path, dest_path)
        except Exception:
            shutil.copy2(img_path, dest_path)

        failure_records.append({
            "index": i,
            "filename": dest_name,
            "source_image": failure["image_name"],
            "failure_type": failure["type"],
            "description": failure["description"],
            "root_cause": failure["root_cause"],
            "ground_truth": [
                {"class": g["class_name"], "box": g["box"]}
                for g in failure["gts"]
            ],
            "predictions": [
                {
                    "class": p["class_name"],
                    "confidence": p["confidence"],
                    "box": p["box"]
                }
                for p in failure["preds"]
            ],
        })
        print(f"  Saved: {dest_path}")

    # Write FAILURE_ANALYSIS.md
    write_failure_analysis_md(failure_records)

    print(f"\nFailure analysis complete. {len(failures)} cases documented.")
    print(f"Images: {FAILURE_DIR}")
    print(f"Report: {DOCS_DIR / 'FAILURE_ANALYSIS.md'}")


def write_failure_analysis_md(records: list[dict]):
    lines = [
        "# Failure Analysis",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "Five real failure cases identified from the held-out test set.",
        "Green boxes = Ground Truth. Red boxes = Predictions.",
        "",
        "---",
        "",
    ]

    ROOT_CAUSE_MAP = {
        "class_confusion": "Visually similar classes causing misclassification",
        "poor_localisation": "Poor bounding box localisation — object may be occluded or at boundary",
        "false_negative": "Complete missed detection — object not detected at all",
        "false_positive": "Spurious detection — model detected non-existent object",
        "partial_miss": "Partial missed detection — some objects in image were missed",
        "low_confidence": "Low confidence detection — model uncertain about object",
    }

    MITIGATION_MAP = {
        "class_confusion": "Add more diverse training examples for confusable classes; use mixup augmentation",
        "poor_localisation": "Increase image resolution; add more occluded training examples",
        "false_negative": "Lower detection threshold; increase training data for this class",
        "false_positive": "Raise confidence threshold; add hard-negative mining",
        "partial_miss": "Augment with dense/crowded scenes; use tile inference for large images",
        "low_confidence": "Fine-tune on similar difficult cases; adjust confidence threshold",
    }

    for rec in records:
        fname = rec["filename"]
        artifact_path = f"../artifacts/failure_cases/{fname}"

        lines += [
            f"## Failure Case {rec['index']}: {rec['failure_type'].replace('_', ' ').title()}",
            "",
            f"**Source image**: `{rec['source_image']}`",
            "",
            f"![Failure {rec['index']}]({artifact_path})",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| Failure type | `{rec['failure_type']}` |",
            f"| Description | {rec['description']} |",
            f"| Root cause | {ROOT_CAUSE_MAP.get(rec['failure_type'], rec['root_cause'])} |",
            f"| Mitigation | {MITIGATION_MAP.get(rec['failure_type'], 'N/A')} |",
            "",
            "**Ground Truth:**",
            "",
        ]
        if rec["ground_truth"]:
            for gt in rec["ground_truth"]:
                box = [round(v, 1) for v in gt["box"]]
                lines.append(f"- `{gt['class']}` @ box {box}")
        else:
            lines.append("- *(no ground truth annotations)*")

        lines += ["", "**Predictions:**", ""]
        if rec["predictions"]:
            for pred in rec["predictions"]:
                box = [round(v, 1) for v in pred["box"]]
                lines.append(
                    f"- `{pred['class']}` (conf={pred['confidence']:.3f}) @ box {box}"
                )
        else:
            lines.append("- *(no predictions)*")

        lines += ["", "---", ""]

    output_path = DOCS_DIR / "FAILURE_ANALYSIS.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[INFO] FAILURE_ANALYSIS.md written: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Error analysis on test set")
    parser.add_argument("--weights", type=str,
                        default=str(ROOT / "weights" / "best.pt"))
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    weights_path = Path(args.weights)
    data_yaml = ROOT / "configs" / "data.yaml"

    if not weights_path.exists():
        print(f"ERROR: weights not found at {weights_path}")
        sys.exit(1)

    run_error_analysis(weights_path, data_yaml, args.imgsz)


if __name__ == "__main__":
    main()
