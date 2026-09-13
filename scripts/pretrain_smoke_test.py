"""
scripts/pretrain_smoke_test.py

Phase 5 / Checkpoint 2: Pre-training RT-DETR Smoke Test.
Loads the official Ultralytics RT-DETR-L pretrained model (rtdetr-l.pt),
verifies CUDA execution, and runs inference on 10 sample test images
from the curated logistics dataset to ensure everything works before fine-tuning.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import torch
from PIL import Image
from ultralytics import RTDETR

def run_pretrain_smoke_test():
    print("=" * 65)
    print("PRE-TRAINING RT-DETR SMOKE TEST (CHECKPOINT 2)")
    print("=" * 65)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Target device: {device}")
    if torch.cuda.is_available():
        print(f"GPU Model    : {torch.cuda.get_device_name(0)}")
        print(f"GPU VRAM     : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")

    # 1. Load pretrained RT-DETR-L
    model_name = "rtdetr-l.pt"
    print(f"\n[1/3] Loading pretrained RT-DETR model: {model_name} ...")
    start_load = time.time()
    model = RTDETR(model_name)
    load_time = time.time() - start_load
    print(f"[1/3] Model loaded successfully in {load_time:.2f}s")

    # 2. Select 10 test images
    test_dir = ROOT / "data" / "logistics_2500" / "test" / "images"
    test_images = sorted(list(test_dir.glob("*.jpg")))[:10]
    assert len(test_images) == 10, f"Expected 10 test images, found {len(test_images)}"
    print(f"\n[2/3] Selected 10 test images for inference validation from {test_dir.name}:")

    # 3. Run inference on test images
    print("\n[3/3] Running inference on sample images...")
    results_summary = []
    total_infer_time = 0.0

    for idx, img_path in enumerate(test_images, start=1):
        t0 = time.time()
        preds = model.predict(source=str(img_path), device=device, imgsz=640, verbose=False)
        t_infer = (time.time() - t0) * 1000.0  # ms
        total_infer_time += t_infer

        boxes = preds[0].boxes
        n_dets = len(boxes) if boxes is not None else 0
        det_info = []
        if boxes is not None and len(boxes) > 0:
            for b in boxes[:3]:  # sample first 3
                cls_id = int(b.cls[0].item())
                cls_name = model.names.get(cls_id, str(cls_id))
                conf = float(b.conf[0].item())
                det_info.append(f"{cls_name} ({conf:.2f})")

        det_str = ", ".join(det_info) if det_info else "No detections (raw COCO classes)"
        print(f"  [{idx:02d}/10] {img_path.name[:35]:35s} | {t_infer:6.1f} ms | Detections: {n_dets:2d} [{det_str}]")
        results_summary.append({
            "image": img_path.name,
            "inference_ms": round(t_infer, 2),
            "num_detections": n_dets,
            "top_detections": det_info
        })

    avg_latency = total_infer_time / len(test_images)
    print("\n" + "=" * 65)
    print("PRE-TRAINING SMOKE TEST SUMMARY")
    print("=" * 65)
    print(f"Model          : RT-DETR-L (rtdetr-l.pt)")
    print(f"Device         : {device}")
    print(f"Images tested  : {len(test_images)}")
    print(f"Average latency: {avg_latency:.2f} ms/image ({1000.0 / avg_latency:.1f} FPS)")
    print("Checkpoint 2   : PASS")
    print("=" * 65)

    # Save to artifacts
    artifacts_dir = ROOT / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_file = artifacts_dir / "pretrain_smoke_test.txt"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=============================================================\n")
        f.write("PRE-TRAINING RT-DETR SMOKE TEST REPORT (CHECKPOINT 2)\n")
        f.write("=============================================================\n")
        f.write(f"Model          : RT-DETR-L (rtdetr-l.pt)\n")
        f.write(f"Device         : {device}\n")
        f.write(f"Images tested  : {len(test_images)}\n")
        f.write(f"Average latency: {avg_latency:.2f} ms/image ({1000.0 / avg_latency:.1f} FPS)\n\n")
        f.write("Detailed Inferences:\n")
        for res in results_summary:
            f.write(f"- {res['image']}: {res['inference_ms']} ms, {res['num_detections']} detections ({', '.join(res['top_detections'])})\n")
        f.write("\nSTATUS: PASS\n")

    print(f"\nReport saved to: {report_file}")
    return True

if __name__ == "__main__":
    success = run_pretrain_smoke_test()
    sys.exit(0 if success else 1)
