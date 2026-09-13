# Evaluation Documentation

## Methodology

The model is evaluated **only** on the held-out test set (500 images, 100 per class).
The validation set was used only during training for hyperparameter selection.
Final numbers are from `scripts/evaluate.py` using `model.val(split='test')`.

## Metrics Explained

| Metric | Definition | Notes |
|--------|-----------|-------|
| mAP@0.5 | Mean Average Precision at IoU≥0.5 | Primary metric for object detection |
| mAP@0.5:0.95 | mAP averaged over IoU 0.5–0.95 (COCO standard) | Stricter; penalizes poor localization |
| Precision | TP / (TP + FP) | How many detections are correct |
| Recall | TP / (TP + FN) | How many GT objects were found |

## Results

> To be filled after `python scripts/evaluate.py` completes.

See: `artifacts/evaluation_results.json`

## Per-Class Results

> To be filled after evaluation.

## Visual Outputs

- `artifacts/confusion_matrix.png`
- `artifacts/PR_curve.png`
- `artifacts/sample_predictions/` — 10 annotated test images

## Limitations

- Metrics are on our 2,500-image subset, not the full logistics dataset.
- RTX 3050 6GB constrains batch size, which may affect training convergence.
- 50 epochs may not be sufficient for full convergence on all 5 classes.
