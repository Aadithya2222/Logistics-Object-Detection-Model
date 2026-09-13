# Engineering Memo: Logistics Object Detection & Reasoning System

**Author:** Aadithya R  
**Domain:** Warehouse Logistics & Industrial Cargo Perception  
**Architecture:** RT-DETR-L (Real-Time Detection Transformer Large)  
**Deployment:** FastAPI REST Service (Dockerized)

---

## 1. Domain & Dataset

### Operational Importance
Automated visual perception in logistics hubs must operate under challenging industrial conditions: high occlusion, variable artificial lighting, scale variance, and overlapping cargo. Efficiently locating pallets, forklifts, shipping containers, boxes, and delivery vehicles is essential for inventory auditing, automated routing, and workplace safety.

### Dataset Source & Composition
- **Source**: Sourced from Roboflow Universe benchmark dataset `large-benchmark-datasets/logistics-sz9jr` (Version 1, CC BY 4.0).
- **Custom Subset**: Filtered and constructed a balanced subset of **2,500 images** (1,500 train, 500 val, 500 test), exactly 500 images per class across 5 target classes.
- **Five Target Classes**:
  1. `cardboard box` (ID 0) — *Non-COCO industrial class*
  2. `forklift` (ID 1)
  3. `freight container` (ID 2) — *Non-COCO industrial class*
  4. `wood pallet` (ID 3) — *Non-COCO industrial class*
  5. `truck` (ID 4)

### Split Distribution
| Split | Percentage | Cardboard Box | Forklift | Freight Container | Wood Pallet | Truck | Total Images |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Train** | 60% | 300 | 300 | 300 | 300 | 300 | **1,500** |
| **Validation** | 20% | 100 | 100 | 100 | 100 | 100 | **500** |
| **Test (Held-Out)** | 20% | 100 | 100 | 100 | 100 | 100 | **500** |
| **Total** | 100% | 500 | 500 | 500 | 500 | 500 | **2,500** |

---

## 2. Model Architecture & Training

### Model Setup
- **Backbone**: RT-DETR-L (`rtdetr-l.pt`), initialized with COCO-pretrained weights.
- **Image Resolution**: $640 \times 640$ pixels.
- **Batch Size**: 2.
- **Optimizer**: AdamW (`lr0 = 1e-4`, `weight_decay = 0.0005`).
- **Epochs**: 50 configured, 10 completed during fine-tuning.
- **Augmentation Pipeline**: `mosaic: 1.0`, `hsv_h: 0.015`, `hsv_s: 0.7`, `hsv_v: 0.4`, `translate: 0.1`, `scale: 0.5`, `fliplr: 0.5`, `erasing: 0.4`.
- **Hardware**: NVIDIA GeForce RTX 3050 6GB Laptop GPU.
- **Training Time**: $3,235.52 \text{ seconds}$ (~53.93 minutes) for 10 epochs.

---

## 3. Held-Out Test Set Evaluation

The deployed model weights (`weights/best.pt`) correspond to **Epoch 1** (`epoch0.pt`), selected via maximum validation fitness (`best_fitness = 0.40391`). Evaluation was executed on the 500-image held-out test split using `python scripts/evaluate.py --weights weights/best.pt`. No hidden-set performance is claimed.

### Overall Test Set Metrics
- **mAP@0.5**: **0.5040** (50.40%)
- **mAP@0.5:0.95**: **0.3408** (34.08%)
- **Precision**: **0.5734** (57.34%)
- **Recall**: **0.4873** (48.73%)

### Per-Class Test Performance
| Class Name | Precision | Recall | mAP@0.5 | mAP@0.5:0.95 |
| :--- | :---: | :---: | :---: | :---: |
| **`wood pallet`** | 0.7850 | 0.6600 | **0.6708** | 0.4700 |
| **`truck`** | 0.5780 | 0.5870 | **0.6515** | 0.4200 |
| **`forklift`** | 0.7000 | 0.5280 | **0.6151** | 0.3610 |
| **`cardboard box`** | 0.6680 | 0.2830 | **0.4144** | 0.3170 |
| **`freight container`** | 0.1360 | 0.3790 | **0.1683** | 0.1360 |

---

## 4. Failure Analysis & Post-Processing Remediation

### Failure 1: Same-Class Internal Sub-Region Duplicates
- **Observed Behavior**: Small candidate boxes inside a large freight container survived standard NMS, generating up to 6 duplicate container detections.
- **Root Cause**: Standard NMS computes $\text{IoU} = \frac{\text{Inter}}{\text{Union}}$. For a small sub-box inside a giant container, $\text{IoU} < 0.03$, allowing sub-boxes to survive.
- **Remediation**: Added same-class Intersection-over-Smaller ($\text{IoS}$) containment suppression ($\text{threshold} = 0.65$) in `app/detector.py`.

### Failure 2: Cross-Class Duplicate Predictions
- **Observed Behavior**: Near-identical bounding boxes assigned to two different classes (e.g. `cardboard box` and `freight container` on identical coordinates).
- **Root Cause**: Class-aware NMS isolates bounding box comparisons by class ID, allowing multi-head predictions for different classes to survive.
- **Remediation**: Added cross-class high-IoU suppression ($\text{IoU} \ge 0.80$) in `app/detector.py`.

### Failure 3: Large Freight Container Spatial Partitioning
- **Observed Behavior**: A long shipping container is detected as two separate non-overlapping container boxes (top half vs. bottom half).
- **Root Cause**: Non-overlapping vertical/horizontal partitions have $\text{IoU} \approx 0.0$ and low $\text{IoS}$, so NMS and containment suppression do not trigger.
- **Impact/Limitation**: Remains an active edge limitation; requires multi-scale query context during training.

### Failure 4: Cardboard / Wooden-Crate vs. Wood-Pallet Confusion
- **Observed Behavior**: Stacked cardboard boxes or wooden crates misclassified as `wood pallet` ($\text{conf} = 0.8561$).
- **Root Cause**: Shared visual textures (slatted wood, brown cardboard, parallel lines) lead to feature distribution overlap in the model backbone.
- **Impact/Limitation**: Intrinsic model weight limitation; requires additional training epochs and hard-negative mining.

### Failure 5: Low-Confidence Boundary Clipping Artifacts
- **Observed Behavior**: Phantom boxes centered off-screen predicted near image boundaries with low confidence ($\text{conf} \approx 0.256$).
- **Root Cause**: Out-of-bounds anchor projections where $>50\%$ of the predicted box lies outside the image canvas.
- **Remediation**: Added boundary artifact suppression in `app/detector.py` filtering boxes with $\text{conf} < 0.30$ AND $\text{Inside Ratio} < 0.50$.

---

## 5. Natural Language Reasoning & Guardrails

The reasoning layer (`app/reasoning.py`) is a pure Python, auditable implementation with no agentic framework overhead.

### Supported Intent Routing
- **`COUNT`**: *"How many freight containers are visible?"* $\rightarrow$ Counts matching target objects.
- **`PRESENCE`**: *"Is there a forklift?"* $\rightarrow$ Verifies class presence.
- **`LIST`**: *"What objects are in the image?"* $\rightarrow$ Summarizes all detected object classes.
- **`SPATIAL`**: *"Is the forklift near the pallet?"* $\rightarrow$ Calculates box centroids and relative distance.
- **`MOST_COMMON`**: *"What is the dominant object?"* $\rightarrow$ Computes class frequency counts.
- **`UNKNOWN`**: Non-visual questions (e.g. *"What is the weather?"*) bypass the detector and return a clear refusal.

### Three-Tier Confidence Guardrail
- **High**: Max confidence $\ge 0.50$.
- **Medium**: Max confidence $0.25 - 0.50$.
- **Low**: Confidence $< 0.25$. When evidence is weak, the engine returns an explicit **"insufficient information"** message rather than guessing.

#### Example "Insufficient Information" Response (`POST /ask`)
```json
{
  "answer": "I could not confidently detect any wood pallet in the image. Insufficient information to answer confidently.",
  "used_detector": true,
  "confidence": "low",
  "intent": "COUNT"
}
```

---

## 6. API Reference & Interface Examples

### Endpoints
- **`GET /health`**: Returns system and model load status.
- **`GET /classes`**: Returns supported object classes.
- **`POST /detect`**: Accepts image file, returns object bounding boxes, classes, and confidence scores.
- **`POST /ask`**: Accepts image file + question string, executes intent routing, detection, and confidence-guarded reasoning.

#### `/detect` Response Example
```json
{
  "objects": [
    {"class": "freight container", "confidence": 0.5321, "bbox": {"x1": 76.53, "y1": 23.41, "x2": 589.8, "y2": 597.75}},
    {"class": "wood pallet", "confidence": 0.3842, "bbox": {"x1": 0.0, "y1": 410.72, "x2": 593.73, "y2": 586.27}}
  ],
  "num_detections": 2,
  "image_size": [640, 640]
}
```

#### `/ask` Response Example
```json
{
  "answer": "There is 1 freight container visible.",
  "used_detector": true,
  "confidence": "high",
  "detections": [
    {"class": "freight container", "confidence": 0.5321, "bbox": {"x1": 76.53, "y1": 23.41, "x2": 589.8, "y2": 597.75}}
  ],
  "intent": "COUNT"
}
```
