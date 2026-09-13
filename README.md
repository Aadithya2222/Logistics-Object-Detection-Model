# 📦 Autonomous Logistics Object Detection & Reasoning System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1%2BCUDA12.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![RT-DETR](https://img.shields.io/badge/Model-RT--DETR--Large-00599C?style=for-the-badge&logo=opencv&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Computer Vision + Natural Language Reasoning API**  
*Author: Aadithya R | Track: Computer Vision + Applied ML Engineering*

[📄 Written Engineering Memo](docs/MEMO.md) • [📊 Evaluation Documentation](docs/EVALUATION.md) • [📡 API Reference](docs/API.md) • [📊 Verification Audit](artifacts/dataset_verification.txt)

</div>

---

## 1. Project Purpose & Overview

This system provides a real-time visual perception and natural-language reasoning API for warehouse and logistics environments. It combines an **RT-DETR-L (Real-Time Detection Transformer Large)** object detection backbone with a hand-written, deterministic Python reasoning engine (`app/reasoning.py`) that answers natural language questions about cargo, inventory counts, and spatial relationships without relying on external agentic frameworks.

---

## 2. Supported Object Classes

The system detects **5 target classes**, including **3 custom non-COCO industrial categories**:

| Class ID | Class Name | Category Type | Description |
| :---: | :--- | :---: | :--- |
| **0** | `cardboard box` | **Non-COCO** | Universal parcel and e-commerce packaging |
| **1** | `forklift` | Standard | Heavy material-handling vehicle |
| **2** | `freight container` | **Non-COCO** | Intermodal shipping cargo container (TEU) |
| **3** | `wood pallet` | **Non-COCO** | Structural foundation of unit load logistics |
| **4** | `truck` | Standard | Transport delivery vehicle docking at warehouse bays |

---

## 3. Dataset & Split Composition

- **Dataset Source**: Constructed from Roboflow Universe benchmark `large-benchmark-datasets/logistics-sz9jr` (CC BY 4.0).
- **Curated Dataset**: Exactly **2,500 balanced images** (500 per class), verified via a 12-point programmatic audit script ([`scripts/verify_dataset.py`](scripts/verify_dataset.py)).

| Split | Total Images | Images Per Class | Purpose |
| :--- | :---: | :---: | :--- |
| **Train** | 1,500 | 300 | Model fine-tuning |
| **Validation** | 500 | 100 | Epoch selection during training |
| **Test (Held-Out)** | 500 | 100 | Final evaluation split |

---

## 4. Model Training & Checkpoint

- **Model Architecture**: RT-DETR-L (`rtdetr-l.pt`), initialized with COCO-pretrained weights.
- **Hardware**: NVIDIA GeForce RTX 3050 6GB Laptop GPU.
- **Configuration**: Image size $640 \times 640$, batch size 2, initial learning rate $1\times 10^{-4}$ (AdamW), 50 configured epochs (10 completed).
- **Augmentation Settings**: `mosaic: 1.0`, `hsv_h: 0.015`, `hsv_s: 0.7`, `hsv_v: 0.4`, `translate: 0.1`, `scale: 0.5`, `fliplr: 0.5`, `erasing: 0.4`.
- **Deployed Checkpoint**: [`weights/best.pt`](weights/best.pt) corresponds to **Epoch 1** (`epoch0.pt`, SHA256: `455f8478266cbd48...`, best fitness `0.40391`).

---

## 5. Held-Out Test Set Evaluation Results

Evaluated on the untouched **500-image held-out test split** (`python scripts/evaluate.py --weights weights/best.pt`):

- **mAP@0.5**: **0.5040** (50.40%)
- **mAP@0.5:0.95**: **0.3408** (34.08%)
- **Precision**: **0.5734** (57.34%)
- **Recall**: **0.4873** (48.73%)

### Per-Class Test Results (mAP@0.5)
- `wood pallet`: **0.6708** (67.08%)
- `truck`: **0.6515** (65.15%)
- `forklift`: **0.6151** (61.51%)
- `cardboard box`: **0.4144** (41.44%)
- `freight container`: **0.1683** (16.83%)

*See [`docs/EVALUATION.md`](docs/EVALUATION.md) for full breakdown.*

---

## 6. Post-Processing Pipeline & Guardrails

To ensure high-precision spatial inferences, `app/detector.py` executes a 4-stage post-processing pipeline:

1. **Standard Class-Aware NMS**: `batched_nms` with $\text{IoU} = 0.45$.
2. **Same-Class IoS Containment Suppression**: Suppresses smaller sub-region false positive boxes inside a larger box of the same class ($\text{IoS} \ge 0.65$).
3. **Cross-Class High-IoU Suppression**: Suppresses lower-confidence duplicate boxes of different classes sharing near-identical coordinates ($\text{IoU} \ge 0.80$).
4. **Boundary Artifact Suppression**: Suppresses low-confidence predictions ($\text{conf} < 0.30$) with $>50\%$ of predicted box area extending outside image boundaries.

### Deterministic Reasoning & Confidence Guardrail
Questions sent to `POST /ask` are routed by intent (`COUNT`, `PRESENCE`, `LIST`, `SPATIAL`, `MOST_COMMON`, `UNKNOWN`). If detection evidence is below the confidence floor ($0.25$), the system explicitly responds:
> *"I could not confidently detect any [class] in the image. Insufficient information to answer confidently."*

---

## 7. How to Run Locally

### Option A: Direct Python Server
```bash
# 1. Activate virtual environment
.\.venv\Scripts\activate

# 2. Start Uvicorn server
python -m uvicorn app.main:app --host 0.0.0.0 --port 7860
```
Access interactive Swagger UI at: `http://localhost:7860/docs`

### Option B: Docker Container Deployment
```bash
# 1. Build Docker image
docker build -t logistics-object-detection .

# 2. Run container on port 7860
docker run -d -p 7860:7860 -e PORT=7860 --name logistics-app logistics-object-detection
```

---

## 8. API Endpoints

- **`GET /health`**: Liveness probe returning `{"status": "ok", "version": "1.0.0", "model_loaded": true}`.
- **`GET /classes`**: Returns list of 5 supported object classes.
- **`POST /detect`**: Accepts image file, returns array of detected objects with class, confidence, and bounding box coordinates.
- **`POST /ask`**: Accepts image file + question string, returns intent, detection array, and natural language answer.

---

## 9. Automated Testing

Run the 48-test automated unit and integration suite:
```bash
pytest tests/
```

Test modules covered:
- [`tests/test_dataset.py`](tests/test_dataset.py): Dataset split and label validity checks.
- [`tests/test_detector.py`](tests/test_detector.py): RT-DETR loading, IoS containment, cross-class suppression, and boundary artifact unit tests.
- [`tests/test_reasoning.py`](tests/test_reasoning.py): Intent classification, spatial math, and confidence guardrail tests.
- [`tests/test_api.py`](tests/test_api.py): FastAPI HTTP endpoint contract tests.

---

## 10. System Limitations & Deployment Status

- **Hugging Face Space**: The repository is uploaded to Hugging Face Space `Aadithya2201/logistics-object-detection`. (Note: The Space is currently paused on Hugging Face due to CPU-basic hardware quota allocation).
- **Model Limitations**:
  1. *Spatial Partitioning*: Large shipping containers spanning full image frames may occasionally be partitioned into two adjacent container boxes ($\text{IoU} < 0.80$).
  2. *Texture Ambiguity*: Weathered wood textures on crates or stacked boxes can occasionally be misclassified as `wood pallet`.
  3. *Small Objects*: Distant cardboard boxes occupying $<10$ pixels have lower recall.
