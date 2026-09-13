# Pre-Hackathon Screening Memo: Constrained Object Detection & Reasoning API

**Track:** Computer Vision + Applied ML Engineering (with a light Agentic component)  
**Author:** Aadithya R  
**Domain:** Warehouse Logistics & Cargo Object Detection  
**Model Architecture:** RT-DETR-L (Real-Time Detection Transformer Large)  
**Deployment:** FastAPI REST API (Dockerized, Uvicorn)

---

## 1. Problem Statement & Domain Justification

Warehouses and freight consolidation hubs handle tens of thousands of parcels, pallets, containers, and industrial handling equipment daily. Automated visual perception in this domain must be real-time, low-latency, and capable of operating under challenging industrial conditions: high occlusion, variable artificial lighting, scale variance, and overlapping objects.

To solve this, I selected a constrained 5-class ontology:
- `cardboard box` (Target ID 0)
- `forklift` (Target ID 1)
- `freight container` (Target ID 2)
- `wood pallet` (Target ID 3)
- `truck` (Target ID 4)

### Non-COCO Class Compliance
Standard COCO models identify generic classes like `car` and `truck`, but fail entirely on domain-specific industrial classes:
- **`wood pallet`** is **not** a COCO class.
- **`freight container`** (intermodal shipping container) is **not** a COCO class.
- **`cardboard box`** is **not** a COCO class.

By including three non-COCO industrial classes alongside `forklift` and `truck`, this system cannot be solved by off-the-shelf COCO weights, satisfying Hard Constraint 3.

---

## 2. Dataset Sourcing & Mid-Project Engineering Pivot

### Sourcing
Data was sourced from the Roboflow Universe public benchmark:
- **Project:** `large-benchmark-datasets/logistics-sz9jr` (Version 1, CC BY 4.0).
- **Original Size:** ~99,238 images across 20 logistics/warehouse classes.
- **Acquisition Strategy:** Rather than downloading the prohibitive 4.86 GB archive or using rate-limited web scrapers, I engineered a custom selective HTTP Range-request streaming engine (`scripts/prepare_dataset.py`). It reads the remote zip archive's Central Directory over HTTP, locates annotation files, and extracts strictly the required images and bounding boxes on the fly in ~14.5 minutes.

### Mid-Project Pivot (Technical Justification)
- **Initial Attempt & Failure:** In my initial sampling run, multi-class images caused severe class skew (>387 wood pallets vs. 300 boxes in train), and Roboflow's pre-augmented image duplicates produced identical SHA256 hashes across different file stems, failing my 12-check verification audit.
- **Engineering Course Correction:** I refactored `scripts/prepare_dataset.py` to:
  1. Filter strictly for pure single-class images (`len(classes_in_file) == 1`).
  2. Deduplicate images by base file stem (`stem.split('_jpg.rf.')[0]`), discarding artificial augmentations.
  3. Re-map class indices (0–4) and strip all 15 out-of-scope classes (e.g., helmets, cones, vests).
- **Outcome:** A verified dataset of exactly 2,500 unique images (1,500 train, 500 val, 500 test), exactly 300/100/100 per class, with zero duplicate SHA256 hashes and 100% valid bounding boxes.

---

## 3. Train / Val / Test Split Strategy

| Split | Percentage | Cardboard Box | Forklift | Freight Container | Wood Pallet | Truck | Total Images |
|---|---|---|---|---|---|---|---|
| **Train** | 60% | 300 | 300 | 300 | 300 | 300 | **1,500** |
| **Validation** | 20% | 100 | 100 | 100 | 100 | 100 | **500** |
| **Test (Held-Out)** | 20% | 100 | 100 | 100 | 100 | 100 | **500** |
| **Total** | 100% | 500 | 500 | 500 | 500 | 500 | **2,500** |

### Justification
- **Balanced Class Distribution:** Industrial datasets frequently suffer from box dominance. Enforcing exactly 500 images per class prevents the loss function from overfitting to ubiquitous objects at the expense of high-value equipment like forklifts.
- **Held-Out Test Set:** 500 images (20% of total) were kept strictly untouched during training and hyperparameter tuning, reserved exclusively for unbiased final evaluation.

---

## 4. Evaluation Methodology & Metrics Analysis

The model was evaluated using standard Object Detection metrics: Precision, Recall, mAP@0.5, and mAP@0.5:0.95.

### What the Metrics Tell You:
1. **mAP@0.5 reflects general object discovery:** High mAP@0.5 (>0.70) demonstrates that the transformer backbone reliably locates objects and predicts correct class labels under relaxed spatial tolerance.
2. **mAP@0.5:0.95 reflects localization fidelity:** Heavy machinery like `forklift` has distinct geometric boundaries, whereas stacks of `cardboard box` objects blur together, causing stricter IoU thresholds to penalize box predictions.

### What the Metrics DO NOT Tell You:
1. **Out-of-Distribution Robustness:** High test set metrics on Roboflow logistics images do not guarantee generalization to unseen real-world facilities with extreme glare, dirty camera lenses, or unconventional night-shift lighting.
2. **Confidence Calibration:** High raw precision does not guarantee that a detection with 0.40 confidence is 40% likely to be correct. Without calibrated post-processing or guardrails, downstream systems will over-rely on weak predictions.

---

## 5. Detailed Root-Cause Analysis of Five Genuine Failure Cases

A reliable ML system must acknowledge and diagnose its failure modes. I identified five distinct failure archetypes on the test set (`artifacts/failure_cases/`):

### Failure Case 1: Extreme Occlusion (Forklift obscured by container)
- **Symptom:** Forklift partially parked behind a freight container; only the overhead safety cage and mast visible.
- **Root Cause:** Bounding box ground truth requires the entire vehicle body. With >70% visual occlusion, the cross-attention queries in the RT-DETR decoder fail to aggregate sufficient features, dropping confidence below the 0.25 threshold (False Negative).
- **Remediation:** Synthetic cut-out augmentation and multi-view aggregation across sequential camera frames.

### Failure Case 2: Severe Scale Variance / Small Objects (Distant Cardboard Boxes)
- **Symptom:** Small parcel boxes located at the far end of the warehouse (>30 meters from the camera).
- **Root Cause:** Downsampling through the hybrid encoder reduces small objects to a few pixels across feature maps (P3/8 stride). Fine details like box edges are lost.
- **Remediation:** High-resolution inference (e.g., `imgsz=1280`) or sliding-window sliced inference (SAHI).

### Failure Case 3: Class Confusion Between Rigid Rectangular Classes (Container vs. Truck Trailer)
- **Symptom:** Model misclassifies a detached freight container loaded on a flatbed chassis as a `truck`, or a box-truck cargo bed as a `freight container`.
- **Root Cause:** Both classes share nearly identical corrugated rectangular sheet-metal geometries, color schemes, and aspect ratios. When the truck cab is cropped out or occluded, visual ambiguity is extreme.
- **Remediation:** Add multi-task relational loss penalizing chassis-container co-occurrence confusion, or separate chassis as an explicit sub-class.

### Failure Case 4: Low Contrast & Dim Industrial Lighting (Unlit Wood Pallets)
- **Symptom:** Stacks of weathered wood pallets in shadowy loading bay corners missed entirely.
- **Root Cause:** Dark weathered wood has low color contrast against concrete warehouse floors in shadow. The image gradients are faint.
- **Remediation:** Dynamic histogram equalization, contrast-limited adaptive histogram equalization (CLAHE) preprocessing, or HSV augmentation with larger V (value) variance during training.

### Failure Case 5: Dense Cluster Boundary Merging (Palletized Box Stacks)
- **Symptom:** A pallet carrying 12 tightly wrapped cardboard boxes is predicted as 2–3 large boxes instead of 12 distinct units.
- **Root Cause:** Plastic shrink-wrap smooths individual box borders. The Hungarian matching in RT-DETR selects the dominant encompassing box proposal rather than separate small boxes.
- **Remediation:** Train on seam/edge enhanced data and tune the Hungarian matcher's box cost coefficient ($\lambda_{\text{box}}$).

---

## 6. Part B: Hand-Written Reasoning Layer & Confidence Guardrails

In strict compliance with Hard Constraint 1, **no agentic frameworks** (LangChain, LangGraph, CrewAI, AutoGen) were used. The reasoning layer (`app/reasoning.py`) is a deterministic, auditable, pure Python implementation.

### Architectural Flow & Decision Logic:
```
Natural Language Question + Image
              │
              ▼
   [ Regex / Intent Parser ]
              │
   ┌──────────┴──────────┐
   ▼                     ▼
[ Non-Visual Intent ]  [ Visual Query ]
(e.g., Weather, Ping)    │
   │                     ▼
   │            [ Invoke RT-DETR Detector ]
   │                     │
   │                     ▼
   │           [ Detections: BBoxes + Conf ]
   │                     │
   │                     ▼
   │           [ Three-Tier Confidence Guardrail ]
   │                     │
   │          ┌──────────┴──────────┐
   │          ▼                     ▼
   │     Conf < 0.25           Conf ≥ 0.25
   │          │                     │
   │          ▼                     ▼
   │    "Insufficient         [ Deterministic
   │     Information"          Reasoning Engine ]
   │          │                (COUNT, PRESENCE,
   │          │                 SPATIAL, MOST_COMMON)
   │          │                     │
   ▼          ▼                     ▼
   ───────────────────────────────────
              │
              ▼
    Structured JSON Response
```

### 1. Intent Routing (Calling the Detector vs. Not):
- **Bypasses Detector:** Questions that are conversational, meta-queries, or unanswerable from the image (e.g., *"What is the weather outside?", "Who created this API?"*). Routed directly to intent `UNKNOWN` without incurring GPU inference latency.
- **Triggers Detector:** Questions seeking quantitative counts (*"How many forklifts?"*), existence verification (*"Is there a truck?"*), inventory listing (*"What objects are present?"*), spatial relations (*"Is the box near the forklift?"*), or dominant asset analysis (*"What is the most common object?"*).

### 2. Honest Confidence Guardrail ("Insufficient Information"):
To prevent hallucinated or guessing responses, confidence is evaluated on a three-tier threshold:
- **`high`**: Detection confidence $\ge 0.50$
- **`medium`**: Detection confidence between $0.25$ and $0.50$
- **`low`**: Detection confidence $< 0.25$

**Specific Example where it outputs "insufficient information":**
- **Image:** A heavily obscured warehouse scene with faint background clutter.
- **Question:** *"How many wood pallets are visible?"*
- **Detector Output:** 1 weak detection for `wood pallet` with confidence `0.18` (below threshold `0.25`).
- **Response Payload:**
```json
{
  "question": "How many wood pallets are visible?",
  "intent": "COUNT",
  "target_class": "wood pallet",
  "answer": "Insufficient information to answer confidently. Weak detections: 1 wood pallet detected with low confidence (0.18).",
  "confidence": "low",
  "num_detections": 1,
  "objects": [
    {
      "class": "wood pallet",
      "confidence": 0.18,
      "bbox": {"x1": 12.0, "y1": 45.0, "x2": 88.0, "y2": 110.0}
    }
  ]
}
```
The API explicitly refuses to assert an ungrounded count, maintaining truthfulness.

---

## 7. API Architecture & Reproducibility

- **Endpoints:**
  - `POST /detect`: Accepts multipart/form-data image, outputs bounding boxes, classes, and confidences.
  - `POST /ask`: Accepts image + question, executes intent routing, detection, and confidence-guarded reasoning.
  - `GET /health`: Liveness probe.
  - `GET /classes`: Returns the 5 supported logistics classes.
- **Reproducibility:**
  - Fixed seed `42` across PyTorch, NumPy, and Python.
  - Docker containerization (`Dockerfile`, `docker-compose.yml`).
  - Unit test suite: 45/45 tests passing (`tests/test_dataset.py`, `test_detector.py`, `test_reasoning.py`, `test_api.py`).
