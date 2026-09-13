"""
scripts/train.py

RT-DETR fine-tuning on the 2,500-image logistics dataset.
Uses Ultralytics RTDETR class (faithful RT-DETR implementation, NOT YOLO).

Hardware target: NVIDIA RTX 3050 6GB Laptop GPU
  - Model  : rtdetr-l (RT-DETR Large)
  - imgsz  : 640
  - batch  : 4  (reduce to 2 if OOM)
  - epochs : 50
  - seed   : 42

Usage:
    python scripts/train.py
    python scripts/train.py --epochs 30 --batch 2  # lower VRAM
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

ARTIFACTS_DIR = ROOT / "artifacts"
WEIGHTS_DIR = ROOT / "weights"
CONFIGS_DIR = ROOT / "configs"


def get_system_info() -> dict:
    info = {}
    import platform
    info["os"] = f"{platform.system()} {platform.release()}"
    info["python"] = sys.version.split()[0]
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        info["cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            info["gpu"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / 1e9, 2
            )
    except ImportError:
        info["torch"] = "not installed"
    try:
        import ultralytics
        info["ultralytics"] = ultralytics.__version__
    except ImportError:
        info["ultralytics"] = "not installed"
    return info


def train(
    data_yaml: Path,
    model_name: str = "rtdetr-l.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 4,
    lr0: float = 1e-4,
    weight_decay: float = 5e-4,
    seed: int = 42,
    project: str = "runs/train",
    name: str = "logistics_rtdetr",
):
    try:
        from ultralytics import RTDETR
    except ImportError:
        print("ERROR: ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    import torch

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    sysinfo = get_system_info()
    start_time = time.time()
    start_dt = datetime.now().isoformat()

    print("=" * 65)
    print("RT-DETR TRAINING")
    print(f"Started: {start_dt}")
    print("=" * 65)
    print(f"  Model      : {model_name}")
    print(f"  Data       : {data_yaml}")
    print(f"  Epochs     : {epochs}")
    print(f"  imgsz      : {imgsz}")
    print(f"  Batch      : {batch}")
    print(f"  LR         : {lr0}")
    print(f"  Weight dec : {weight_decay}")
    print(f"  Seed       : {seed}")
    print(f"  GPU        : {sysinfo.get('gpu', 'CPU')}")
    print(f"  VRAM       : {sysinfo.get('vram_gb', 'N/A')} GB")
    print("=" * 65)

    # Set seed
    import random, numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    # Load RT-DETR model
    print(f"\n[1/4] Loading RT-DETR model: {model_name}")
    model = RTDETR(model_name)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[1/4] Device: {device}")

    # Train
    print(f"\n[2/4] Starting training ...")
    try:
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            lr0=lr0,
            weight_decay=weight_decay,
            seed=seed,
            device=device,
            project=str(ROOT / project),
            name=name,
            exist_ok=True,
            verbose=True,
            workers=2,
            amp=True,
            # Augmentation (sensible defaults for logistics imagery)
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4,
            flipud=0.0,
            fliplr=0.5,
            mosaic=1.0,
            translate=0.1,
            scale=0.5,
            # Reproducibility
            deterministic=True,
            # Save best and last
            save=True,
            save_period=10,
        )
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            print(f"\n[OOM] CUDA out of memory at batch={batch}.")
            if batch > 2:
                new_batch = batch // 2
                print(f"[OOM] Retrying with batch={new_batch} ...")
                torch.cuda.empty_cache()
                results = model.train(
                    data=str(data_yaml),
                    epochs=epochs,
                    imgsz=imgsz,
                    batch=new_batch,
                    lr0=lr0,
                    weight_decay=weight_decay,
                    seed=seed,
                    device=device,
                    project=str(ROOT / project),
                    name=name,
                    exist_ok=True,
                    verbose=True,
                    deterministic=True,
                    save=True,
                    save_period=10,
                )
                batch = new_batch
            else:
                raise
        else:
            raise

    end_time = time.time()
    elapsed = end_time - start_time
    elapsed_str = f"{elapsed / 3600:.2f} hours ({elapsed / 60:.1f} min)"

    print(f"\n[3/4] Training complete. Duration: {elapsed_str}")

    # Copy best.pt to weights/
    run_dir = ROOT / project / name
    best_src = run_dir / "weights" / "best.pt"
    best_dst = WEIGHTS_DIR / "best.pt"
    if best_src.exists():
        import shutil
        shutil.copy2(best_src, best_dst)
        print(f"[3/4] Copied best.pt → {best_dst}")
    else:
        print(f"[WARN] best.pt not found at {best_src}")

    # Extract metrics
    metrics_summary = {}
    try:
        metrics_summary["box_loss"] = float(results.results_dict.get("train/box_loss", 0))
        metrics_summary["cls_loss"] = float(results.results_dict.get("train/cls_loss", 0))
        metrics_summary["mAP50"] = float(results.results_dict.get("metrics/mAP50(B)", 0))
        metrics_summary["mAP50_95"] = float(results.results_dict.get("metrics/mAP50-95(B)", 0))
        metrics_summary["precision"] = float(results.results_dict.get("metrics/precision(B)", 0))
        metrics_summary["recall"] = float(results.results_dict.get("metrics/recall(B)", 0))
    except Exception as e:
        print(f"[WARN] Could not extract metrics: {e}")

    # Save training summary
    summary = {
        "model": model_name,
        "pretrained_checkpoint": model_name,
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "optimizer": "AdamW",
        "lr0": lr0,
        "weight_decay": weight_decay,
        "seed": seed,
        "augmentation": {
            "hsv_h": 0.015, "hsv_s": 0.7, "hsv_v": 0.4,
            "flipud": 0.0, "fliplr": 0.5, "mosaic": 1.0,
            "translate": 0.1, "scale": 0.5,
        },
        "training_started": start_dt,
        "training_duration": elapsed_str,
        "training_duration_seconds": elapsed,
        "hardware": {
            "gpu": sysinfo.get("gpu", "N/A"),
            "vram_gb": sysinfo.get("vram_gb", "N/A"),
            "os": sysinfo.get("os", "N/A"),
        },
        "software": {
            "python": sysinfo.get("python", "N/A"),
            "torch": sysinfo.get("torch", "N/A"),
            "cuda": sysinfo.get("cuda_version", "N/A"),
            "ultralytics": sysinfo.get("ultralytics", "N/A"),
        },
        "final_metrics_val": metrics_summary,
        "best_weights": str(best_dst),
        "run_dir": str(run_dir),
    }

    summary_txt = []
    summary_txt.append("RT-DETR TRAINING SUMMARY")
    summary_txt.append(f"Generated: {datetime.now().isoformat()}")
    summary_txt.append("")
    for k, v in summary.items():
        if isinstance(v, dict):
            summary_txt.append(f"  {k}:")
            for kk, vv in v.items():
                summary_txt.append(f"    {kk}: {vv}")
        else:
            summary_txt.append(f"  {k}: {v}")

    txt_path = ARTIFACTS_DIR / "training_summary.txt"
    txt_path.write_text("\n".join(summary_txt), encoding="utf-8")
    print(f"[4/4] Training summary saved: {txt_path}")

    json_path = ARTIFACTS_DIR / "training_config.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"\n{'='*65}")
    print("TRAINING COMPLETE")
    print(f"  Duration : {elapsed_str}")
    print(f"  Best     : {best_dst}")
    print(f"  mAP@0.5  : {metrics_summary.get('mAP50', 'N/A')}")
    print(f"  mAP@0.5:0.95: {metrics_summary.get('mAP50_95', 'N/A')}")
    print(f"{'='*65}")
    print("\nNext: python scripts/evaluate.py")


def main():
    parser = argparse.ArgumentParser(description="Train RT-DETR on logistics dataset")
    parser.add_argument("--model", type=str, default="rtdetr-l.pt",
                        help="RT-DETR model variant (rtdetr-l.pt or rtdetr-x.pt)")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--lr0", type=float, default=1e-4)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_yaml = ROOT / "configs" / "data.yaml"
    if not data_yaml.exists():
        print(f"ERROR: data.yaml not found at {data_yaml}")
        print("Run scripts/prepare_dataset.py first.")
        sys.exit(1)

    train(
        data_yaml=data_yaml,
        model_name=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr0=args.lr0,
        weight_decay=args.weight_decay,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
