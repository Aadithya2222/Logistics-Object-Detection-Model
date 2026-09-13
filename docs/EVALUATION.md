# Final Model Evaluation Report (Held-Out Test Set)

## 1. Evaluation Methodology

The model evaluation was conducted exclusively on the held-out **Test Set** comprising **500 images** (100 images per class) that were kept strictly untouched during training and hyperparameter selection.

Evaluation script used:
```bash
python scripts/evaluate.py --weights weights/best.pt
```

- **Data Split Distribution**:
  - **Total Images**: 2,500
  - **Train**: 1,500 images (60%)
  - **Validation**: 500 images (20%)
  - **Test (Held-Out)**: 500 images (20%)
- **Test Set Composition**: 100 images per class (`cardboard box`, `forklift`, `freight container`, `wood pallet`, `truck`).

---

## 2. Checkpoint & Model Metadata

- **Architecture**: RT-DETR-L (Real-Time Detection Transformer Large)
- **Pretrained Initialization**: COCO-pretrained weights (`rtdetr-l.pt`)
- **Deployed Checkpoint**: `weights/best.pt`
- **Checkpoint Origin**: Corresponds to **Epoch 1** (0-indexed `epoch0.pt` in `runs/train/logistics_rtdetr/weights/`)
- **Selection Metric**: Best fitness = `0.40391` (computed based on mAP50-95)

---

## 3. Overall Held-Out Test Set Metrics

All metrics reported below were computed directly by running `scripts/evaluate.py` against the 500-image test split:

| Metric | Value | Percentage | Description |
| :--- | :---: | :---: | :--- |
| **mAP@0.5** | **0.5040** | **50.40%** | Mean Average Precision at IoU threshold ≥ 0.50 |
| **mAP@0.5:0.95** | **0.3408** | **34.08%** | COCO-standard mAP averaged across IoU 0.50–0.95 |
| **Precision** | **0.5734** | **57.34%** | True Positives / (True Positives + False Positives) |
| **Recall** | **0.4873** | **48.73%** | True Positives / (True Positives + False Negatives) |

---

## 4. Per-Class Test Set Metrics

| Class Name | Class ID | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`wood pallet`** | 3 | **0.7850** | **0.6600** | **0.6708** | **0.4700** |
| **`truck`** | 4 | **0.5780** | **0.5870** | **0.6515** | **0.4200** |
| **`forklift`** | 1 | **0.7000** | **0.5280** | **0.6151** | **0.3610** |
| **`cardboard box`** | 0 | **0.6680** | **0.2830** | **0.4144** | **0.3170** |
| **`freight container`** | 2 | **0.1360** | **0.3790** | **0.1683** | **0.1360** |
| **Overall (Mean)** | — | **0.5734** | **0.4873** | **0.5040** | **0.3408** |

---

## 5. Analysis & Metric Limitations

### Metric Interpretation:
1. **mAP@0.5 vs mAP@0.5:0.95**:
   - **mAP@0.5 (50.40%)** measures basic detection capability—whether the model correctly locates and classifies objects under relaxed spatial tolerance.
   - **mAP@0.5:0.95 (34.08%)** measures precise bounding box alignment. Stricter IoU thresholds penalize objects with ill-defined boundaries (such as stacked cardboard boxes or large shipping containers).
2. **Class Variance**:
   - Distinct rigid machinery (`wood pallet`, `truck`, `forklift`) achieved strong mAP@0.5 scores ($61.5\% - 67.1\%$).
   - `cardboard box` ($41.4\%$) suffered lower recall ($28.3\%$) due to dense box clustering where individual borders blur together.
   - `freight container` ($16.8\%$) suffered lower precision due to non-overlapping vertical spatial partition false positives and background metal sheet confusion.

### Limitations & Scope:
- **Test Set Scope**: These metrics reflect performance on our 500-image held-out test split. They do **not** represent hidden-set evaluation performance.
- **Dataset Scale**: Evaluated on a 2,500-image subset (1,500 train), which constrains generalized representation under extreme lighting or severe outdoor weather conditions.
