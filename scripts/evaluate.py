"""
scripts/evaluate.py

Evaluate the trained RT-DETR model on the held-out test set.
Produces:
  - artifacts/evaluation_results.json
  - artifacts/confusion_matrix.png
  - artifacts/PR_curve.png
  - artifacts/sample_predictions/  (annotated test images)

Usage:
    python scripts/evaluate.py
    python scripts/evaluate.py --weights weights/best.pt
"""

import argparse
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

ARTIFACTS_DIR = ROOT / "artifacts"
WEIGHTS_DIR = ROOT / "weights"
SAMPLE_PRED_DIR = ARTIFACTS_DIR / "sample_predictions"

CLASS_NAMES = {
    0: "cardboard box",
    1: "forklift",
    2: "freight container",
    3: "wood pallet",
    4: "truck",
}


def evaluate(weights_path: Path, data_yaml: Path, imgsz: int = 640):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_PRED_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("RT-DETR EVALUATION — TEST SET")
    print(f"Timestamp : {datetime.now().isoformat()}")
    print(f"Weights   : {weights_path}")
    print(f"Data YAML : {data_yaml}")
    print("=" * 65)

    try:
        from ultralytics import RTDETR
    except ImportError:
        print("ERROR: ultralytics not installed.")
        sys.exit(1)

    import torch

    if not weights_path.exists():
        print(f"ERROR: weights not found at {weights_path}")
        print("Run scripts/train.py first.")
        sys.exit(1)

    # Load model
    print(f"\n[1/4] Loading model: {weights_path}")
    model = RTDETR(str(weights_path))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[1/4] Device: {device}")

    # Run validation on test split
    print(f"\n[2/4] Running evaluation on test split ...")
    metrics = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=imgsz,
        batch=1,
        device=device,
        verbose=True,
        save_json=True,
        plots=True,
        project=str(ROOT / "runs" / "eval"),
        name="test_eval",
        exist_ok=True,
    )

    print(f"\n[3/4] Collecting metrics ...")

    results_dict = metrics.results_dict if hasattr(metrics, "results_dict") else {}

    mAP50 = float(results_dict.get("metrics/mAP50(B)", 0))
    mAP50_95 = float(results_dict.get("metrics/mAP50-95(B)", 0))
    precision = float(results_dict.get("metrics/precision(B)", 0))
    recall = float(results_dict.get("metrics/recall(B)", 0))

    # Per-class metrics if available
    per_class = {}
    try:
        box_metrics = getattr(metrics, "box", metrics)
        ap_class_index = getattr(box_metrics, "ap_class_index", [])
        ap50 = getattr(box_metrics, "ap50", [])
        ap = getattr(box_metrics, "ap", [])
        p = getattr(box_metrics, "p", [])
        r = getattr(box_metrics, "r", [])
        for i, cls_idx in enumerate(ap_class_index):
            cls_name = CLASS_NAMES.get(int(cls_idx), f"class_{cls_idx}")
            per_class[cls_name] = {
                "ap50": float(ap50[i]) if i < len(ap50) else None,
                "ap50_95": float(ap[i]) if i < len(ap) else None,
                "precision": float(p[i]) if i < len(p) else None,
                "recall": float(r[i]) if i < len(r) else None,
            }
    except Exception as e:
        print(f"[WARN] Per-class metrics: {e}")

    eval_results = {
        "evaluation_timestamp": datetime.now().isoformat(),
        "weights": str(weights_path),
        "data_yaml": str(data_yaml),
        "split": "test",
        "imgsz": imgsz,
        "overall": {
            "mAP50": mAP50,
            "mAP50_95": mAP50_95,
            "precision": precision,
            "recall": recall,
        },
        "per_class": per_class,
    }

    out_path = ARTIFACTS_DIR / "evaluation_results.json"
    out_path.write_text(json.dumps(eval_results, indent=2), encoding="utf-8")
    print(f"[3/4] Results saved: {out_path}")

    # Copy confusion matrix and PR curve from run dir
    run_dir = ROOT / "runs" / "eval" / "test_eval"
    for fname in ["confusion_matrix.png", "confusion_matrix_normalized.png",
                  "PR_curve.png", "R_curve.png", "P_curve.png", "F1_curve.png",
                  "results.png"]:
        src = run_dir / fname
        if src.exists():
            dst = ARTIFACTS_DIR / fname
            shutil.copy2(src, dst)
            print(f"  Copied: {fname} → artifacts/")

    # Save sample predictions
    print(f"\n[4/4] Saving sample predictions ...")
    test_images_dir = ROOT / "data" / "logistics_2500" / "test" / "images"
    if test_images_dir.exists():
        test_imgs = sorted(test_images_dir.glob("*.jpg"))[:10]
        if not test_imgs:
            test_imgs = sorted(test_images_dir.glob("*.png"))[:10]
        if not test_imgs:
            test_imgs = list(test_images_dir.iterdir())[:10]

        for img_path in test_imgs:
            try:
                pred_results = model.predict(
                    str(img_path),
                    device=device,
                    imgsz=imgsz,
                    verbose=False,
                )
                for r in pred_results:
                    out_img = SAMPLE_PRED_DIR / img_path.name
                    r.save(filename=str(out_img))
            except Exception as e:
                print(f"  [WARN] Could not predict {img_path.name}: {e}")

    print(f"\n{'='*65}")
    print("EVALUATION SUMMARY (Test Set)")
    print(f"  mAP@0.5       : {mAP50:.4f}")
    print(f"  mAP@0.5:0.95  : {mAP50_95:.4f}")
    print(f"  Precision      : {precision:.4f}")
    print(f"  Recall         : {recall:.4f}")
    if per_class:
        print(f"\n  Per-class mAP@0.5:")
        for cls, m in per_class.items():
            print(f"    {cls:20s}: {m.get('ap50', 'N/A'):.4f}")
    print(f"{'='*65}")
    print(f"\nResults: {out_path}")
    print("Next: python scripts/error_analysis.py")


def main():
    parser = argparse.ArgumentParser(description="Evaluate RT-DETR on test set")
    parser.add_argument("--weights", type=str,
                        default=str(ROOT / "weights" / "best.pt"))
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    weights_path = Path(args.weights)
    data_yaml = ROOT / "configs" / "data.yaml"
    evaluate(weights_path, data_yaml, args.imgsz)


if __name__ == "__main__":
    main()
