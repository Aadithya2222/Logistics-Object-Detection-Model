# Training Documentation

## Model

- **Architecture**: RT-DETR-L (Real-Time Detection Transformer, Large variant)
- **Implementation**: Ultralytics `RTDETR` class — NOT YOLO
- **Pretrained checkpoint**: `rtdetr-l.pt` (COCO pretrained, downloaded from Ultralytics)

## Why RT-DETR?

RT-DETR combines DETR's transformer-based detection with a hybrid encoder that achieves real-time inference speeds. Unlike YOLO models, RT-DETR uses cross-attention to reason about global context, which benefits crowded scene understanding in logistics.

## Hyperparameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | rtdetr-l.pt | Large variant, best quality for 6GB VRAM |
| Epochs | 50 | Appropriate for 1500-image dataset |
| Image size | 640 | Standard RT-DETR resolution |
| Batch size | 4 | Constrained by RTX 3050 6GB VRAM |
| Optimizer | AdamW | Built-in to Ultralytics RT-DETR |
| Learning rate | 1e-4 | Conservative fine-tuning LR |
| Weight decay | 5e-4 | Regularization |
| Seed | 42 | Reproducibility |

## Augmentation

| Augmentation | Value |
|--------------|-------|
| HSV Hue | ±0.015 |
| HSV Saturation | ±0.7 |
| HSV Value | ±0.4 |
| Horizontal flip | 0.5 |
| Vertical flip | 0.0 |
| Mosaic | 1.0 |
| Translate | 0.1 |
| Scale | 0.5 |

## Command

```bash
python scripts/train.py
```

## Output

- Best weights: `weights/best.pt`
- Training runs: `runs/train/logistics_rtdetr/`
- Summary: `artifacts/training_summary.txt`

## Training Results

> To be filled after training completes.

See: `artifacts/training_summary.txt`
