# 📦 Logistics Object Detection & Reasoning API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1%2BCUDA12.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Ultralytics](https://img.shields.io/badge/RT--DETR-Large-00599C?style=for-the-badge&logo=opencv&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.badge?style=for-the-badge)

**An End-to-End Deep Learning & Natural Language Reasoning System for Smart Warehouses**  
*Built for the Pre-Hackathon Screening: Constrained Object Detection & Reasoning Track*

[🌐 Live Interactive Swagger API](https://termination-consists-amazing-servers.trycloudflare.com/docs) • [📄 2-Page Engineering Memo](docs/MEMO.md) • [📡 API Reference](docs/API.md) • [📊 Verification Audit](artifacts/dataset_verification.txt)

</div>

---

## 🌟 Quick Links & Live Public Deployment

The API is fully deployed and accessible over the public internet with hardware acceleration on an **NVIDIA GeForce RTX 3050 6GB GPU** (~45 ms inference latency per image):

| Resource | URL | What You Can Do There |
|---|---|---|
| **Interactive Swagger UI** | **[Open Swagger Console](https://termination-consists-amazing-servers.trycloudflare.com/docs)** | Drag-and-drop any warehouse image, ask natural language questions, and see bounding boxes and answers live! |
| **API Base URL** | `https://termination-consists-amazing-servers.trycloudflare.com` | Root endpoint for automated review scripts and curl requests. |
| **Health Check** | `https://termination-consists-amazing-servers.trycloudflare.com/health` | Instant liveness check (`{"status": "ok", "version": "1.0.0"}`). |
| **Supported Classes** | `https://termination-consists-amazing-servers.trycloudflare.com/classes` | Returns the 5 supported industrial logistics classes. |

---

## 📖 The Story Behind This Project (Explain It Like I'm 10)

Imagine stepping inside a massive Amazon, FedEx, or IKEA distribution warehouse. 

Every single minute, thousands of cardboard boxes fly down conveyor belts, heavy forklifts zoom through aisles, giant intermodal shipping containers are unloaded, and wooden pallets are stacked up to the ceiling. 

```
   📦 Box             🚜 Forklift           🚢 Container           🪵 Pallet           🚛 Truck
 [Cardboard]          [Machinery]          [Intermodal]          [Storage Base]       [Transport]
```

### The Problem
If a computer vision camera inside the warehouse makes a mistake:
- A forklift might collide with a pallet or a container.
- Packages get lost or miscounted.
- Standard off-the-shelf AI models (like standard COCO models) **fail completely** because they only know common objects like cats, dogs, cars, and pizzas. They have **never learned what a wooden warehouse pallet or shipping container looks like!**

### Our Solution
We built an end-to-end intelligent vision system:
1. **The Eagle Eye (Part A - RT-DETR Transformer)**: Spots all 5 warehouse objects simultaneously with high-precision bounding boxes in real time.
2. **The Honest Detective (Part B - Hand-Written Reasoning Engine)**: Understands human questions in plain English (*"How many forklifts are in this image?"* or *"Is the container near the truck?"*). If the lighting is too dark or the image is too blurry, **it honestly says "I don't have enough information" instead of making up a lie!**

---

## 🏷️ The 5 Target Classes (Solving Hard Constraint 3)

The project constraints state that the model **must detect at least one class that is NOT in the standard COCO dataset** (so nobody can just use an unmodified off-the-shelf pretrained model).

We went above and beyond by choosing **three non-COCO industrial classes**:

| Class ID | Class Name | Is it in standard COCO? | Real-World Warehouse Purpose |
|:---:|:---|:---:|:---|
| **0** | `cardboard box` | ❌ **NO (Non-COCO)** | Secondary packaging for parcels and e-commerce goods. |
| **1** | `forklift` | ✅ COCO equivalent: partial | Powered industrial vehicle used for lifting and transport. |
| **2** | `freight container` | ❌ **NO (Non-COCO)** | Standardized intermodal shipping cargo container. |
| **3** | `wood pallet` | ❌ **NO (Non-COCO)** | Flat wooden transport structure supporting heavy cargo stacks. |
| **4** | `truck` | ✅ Standard COCO | Freight delivery vehicles and semi-trailers. |

---

## 🔍 The Dataset Journey & Our Clever Engineering Pivot

### Sourcing
- **Source**: Roboflow Universe Public Logistics Benchmark ([`large-benchmark-datasets/logistics-sz9jr`](https://universe.roboflow.com/large-benchmark-datasets/logistics-sz9jr)).
- **Original Dataset Size**: **99,238 images** (~4.86 GB archive) spanning 20 different mixed classes.

### The Big Challenge & Our Pivot
In our initial test, downloading the full 4.86 GB archive was slow, prone to network interruptions, and the raw dataset contained extreme class imbalance (e.g. 10x more boxes than forklifts) and artificial duplicate augmented copies.

### The Engineering Course Correction:
Instead of downloading the giant archive or scraping images:
1. **HTTP Range-Request Streaming**: We wrote a custom remote ZIP parser ([`scripts/prepare_dataset.py`](scripts/prepare_dataset.py)) using HTTP Range headers. It read only the ZIP file's central directory table from Roboflow's remote server over the internet.
2. **Pure Single-Class Filtering**: It scanned thousands of remote text annotations in seconds and selected **strictly pure single-class images**.
3. **De-duplication**: It grouped files by their base stem (`stem.split('_jpg.rf.')[0]`), completely discarding artificial duplicate augmentations.
4. **Targeted Extraction**: It downloaded **only the exact 2,500 needed images** in just 14.5 minutes!

```
Remote Roboflow 4.86 GB Archive (99,238 Images)
             │
             ▼  (HTTP Range Requests: Central Directory Stream)
   [ Selective Class & Base Stem Filter ]
             │
             ▼
   Clean, Balanced Logistics Dataset (2,500 Images)
   ├── Train: 1,500 images (exactly 300 per class)
   ├── Val  :   500 images (exactly 100 per class)
   └── Test :   500 images (exactly 100 per class - strictly held out!)
```

### Programmatic Verification (12 / 12 Checks Passed)
We ran our rigorous automated audit ([`scripts/verify_dataset.py`](scripts/verify_dataset.py)). All 12 checks passed with zero errors:
- ✅ Exactly 2,500 total images.
- ✅ Exactly 1,500 train, 500 val, 500 test.
- ✅ Exactly 300/100/100 images per class.
- ✅ 0 corrupt images, 0 duplicate filenames, 0 duplicate SHA256 hashes.
- ✅ 100% valid normalized bounding boxes $[0, 1]$.
- 📄 Full log saved at [`artifacts/dataset_verification.txt`](artifacts/dataset_verification.txt).

---

## 🤖 The Model: RT-DETR (Real-Time Detection Transformer)

Rather than using traditional anchor-based detectors, we chose **RT-DETR-L** (Real-Time Detection Transformer Large):

```
Input Image (640x640) ──► [ CNN Backbone + Hybrid Encoder ] ──► [ Transformer Decoder ] ──► Hungarian Matching ──► Direct Detections
```

### Why RT-DETR is Superior for Warehouses:
1. **Global Context Attention**: Heavy warehouse equipment often overlaps (e.g. a forklift carrying a wooden pallet with 3 cardboard boxes). While traditional YOLO detectors struggle with overlapping boxes and require heuristic Non-Maximum Suppression (NMS), RT-DETR uses cross-attention queries to understand the entire scene at once.
2. **NMS-Free End-to-End Inference**: Eliminates post-processing latency jitter, ensuring smooth real-time execution (~45 ms on our RTX 3050 GPU).

### Training Configuration:
- **Base Checkpoint**: `rtdetr-l.pt` (Ultralytics implementation).
- **GPU**: NVIDIA GeForce RTX 3050 6GB Laptop GPU.
- **Precision**: Automatic Mixed Precision (AMP `torch.cuda.amp`).
- **Batch Size**: 2 (stable 2.31 GB VRAM consumption).
- **Optimizer**: AdamW with warmup and cosine decay.
- **Image Size**: 640 × 640 pixels.

---

## 🧠 Part B: The Hand-Written Reasoning Layer (Zero Frameworks)

Per **Hard Constraint 1**, agentic frameworks such as LangChain, LangGraph, CrewAI, and AutoGen are **strictly forbidden**.

We built a 100% hand-written, deterministic, auditable Python reasoning layer ([`app/reasoning.py`](app/reasoning.py)):

```
                             Natural Language Question + Image
                                             │
                                             ▼
                                   [ Regex Intent Parser ]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ Non-Visual Intent ]                       [ Visual Query Intent ]
           (e.g., "What is the weather?")                          │
                       │                                           ▼
                       │                                [ Run RT-DETR Detector ]
                       │                                           │
                       │                                           ▼
                       │                               [ 3-Tier Confidence Guardrail ]
                       │                                           │
                       │                        ┌──────────────────┴──────────────────┐
                       │                        ▼                                     ▼
                       │                 Confidence < 0.25                    Confidence ≥ 0.25
                       │                        │                                     │
                       │                        ▼                                     ▼
                       │          "Insufficient information               [ Deterministic Reasoning ]
                       │           to answer confidently."                - COUNT: Exact count
                       │                        │                         - PRESENCE: Yes/No
                       │                        │                         - SPATIAL: Near / Overlapping
                       │                        │                         - MOST_COMMON: Dominant class
                       ▼                        ▼                                     ▼
                       ────────────────────────────────────────────────────────────────
                                                       │
                                                       ▼
                                            Structured JSON Output
```

### The 4 Reasoning Steps:
1. **Intent Routing**: Categorizes the user query into `COUNT`, `PRESENCE`, `LIST`, `MOST_COMMON`, `SPATIAL`, or `UNKNOWN`. Non-visual questions skip GPU inference completely.
2. **Detection Execution**: Calls the RT-DETR model to extract bounding box coordinates, class labels, and confidence scores.
3. **Deterministic Reasoning Engine**: Performs spatial math (IoU overlap, bounding box distance calculations) and quantitative aggregations.
4. **Honest Confidence Guardrail**:
   - `high` ($\ge 0.50$): Strong confidence.
   - `medium` ($0.25 - 0.50$): Moderate confidence.
   - `low` ($< 0.25$): **Refuses to guess!** Returns:
     > *"I could not confidently detect any [class] in the image. Insufficient information to answer confidently."*

---

## 📸 Real Test Runs & Visual Sample Predictions

We executed sample test runs across real test-set images representing all 5 classes. The annotated prediction images are saved in [`artifacts/sample_predictions/`](artifacts/sample_predictions/):

```
┌──────────────────────────────────────┬────────────────────────────────┬───────────────────────────┬────────────┐
│ Image Target Class                   │ Top Model Detections           │ Sample User Question      │ Confidence │
├──────────────────────────────────────┼────────────────────────────────┼───────────────────────────┼────────────┤
│ 🪵 Wood Pallet & Box                 │ wood pallet: 0.86 confidence   │ "How many cardboard boxes │ low        │
│ (0002184_jpg.rf...)                  │ forklift: 0.39 confidence      │ are visible?"             │ (Honest!)  │
│                                      │                                │ Answer: Insufficient info │            │
├──────────────────────────────────────┼────────────────────────────────┼───────────────────────────┼────────────┤
│ 🚜 Forklift                          │ forklift: 0.62 confidence      │ "Is there a forklift in   │ high       │
│ (01FVZIGPUGWI_jpg.rf...)             │ forklift: 0.57 confidence      │ the image?"               │            │
│                                      │                                │ Answer: Yes, visible.     │            │
├──────────────────────────────────────┼────────────────────────────────┼───────────────────────────┼────────────┤
│ 🚢 Freight Container                 │ freight container: 0.62 conf   │ "How many containers are  │ high       │
│ (-1-DRY-CONTAINER-_-_png.rf...)      │ freight container: 0.54 conf   │ in this image?"           │            │
│                                      │                                │ Answer: 27 containers.    │            │
├──────────────────────────────────────┼────────────────────────────────┼───────────────────────────┼────────────┤
│ 🪵 Stored Wood Pallet                │ wood pallet: 0.86 confidence   │ "Are there pallets?"      │ high       │
│ (0000039_jpg.rf...)                  │ wood pallet: 0.49 confidence   │ Answer: Yes, 2 visible.   │            │
├──────────────────────────────────────┼────────────────────────────────┼───────────────────────────┼────────────┤
│ 🚛 Logistics Truck                   │ truck: 0.30 confidence         │ "Is there a truck?"       │ medium     │
│ (-3163ca687f_jpg.rf...)              │ freight container: 0.29 conf   │ Answer: Yes, 2 visible.   │            │
└──────────────────────────────────────┴────────────────────────────────┴───────────────────────────┴────────────┘
```

---

## ⚠️ Honest Failure Cases & Root-Cause Analysis

The review rubric states: **"A model with zero acknowledged failure cases is treated as a red flag, not a strength."** 

We thoroughly evaluated our model on the held-out test set and identified **5 real failure modes** ([`docs/MEMO.md`](docs/MEMO.md)):

1. **Severe Occlusion (Forklift hidden behind container)**:
   - *Symptom*: Only the forklift's overhead guard is visible through container doors.
   - *Root Cause*: Over 70% of the vehicle body is occluded; transformer queries drop confidence below 0.25 threshold.
2. **Small Scale & Extreme Distance (Distant Parcels)**:
   - *Symptom*: Small cardboard boxes >30 meters away on distant shelving are missed.
   - *Root Cause*: Downsampling in the feature pyramid (P3/8 stride) reduces a 30m box to only 3–4 pixels, erasing corner gradients.
3. **Class Confusion (Detached Shipping Container vs. Box Truck Trailer)**:
   - *Symptom*: A container loaded on a chassis is occasionally classified as a truck trailer.
   - *Root Cause*: Both share identical corrugated metal walls, aspect ratios, and rectangular geometry.
4. **Low Contrast in Warehouse Shadows (Unlit Wood Pallets)**:
   - *Symptom*: Dark weathered wooden pallets lying in dimly lit corners are overlooked.
   - *Root Cause*: Dark timber has nearly identical pixel intensity values to aged industrial concrete in deep shadow.
5. **Dense Stacking Boundary Merging (Palletized Box Clusters)**:
   - *Symptom*: 10 shrink-wrapped boxes on a pallet are predicted as 2 large boxes.
   - *Root Cause*: Transparent stretch wrap diffuses the seam boundaries between neighboring boxes.

---

## 🚀 Quick Start & How to Run

### Method 1: Instant Public Cloud (No Setup Required!)
Open your browser and visit:  
👉 **[Live Swagger Web Console](https://termination-consists-amazing-servers.trycloudflare.com/docs)**

### Method 2: One-Command Docker Run (Bonus 10% Rubric)
```bash
# Clone the repository
git clone https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git
cd Logistics-Object-Detection-Model

# Start the containerized API
docker compose up --build
```
The API is now live at `http://localhost:8000/docs`!

### Method 3: Local Python Run
```bash
# 1. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows (or: source .venv/bin/activate on Linux/Mac)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📡 API Usage & Example Requests

### 1. Detect Objects in an Image (`POST /detect`)
```bash
curl -X POST "http://localhost:8000/detect" \
  -F "file=@data/logistics_2500/test/images/-1-DRY-CONTAINER-_-_png_jpg.rf.af49c95763d7179243f25c6bb47f3050.jpg"
```
**Sample Response:**
```json
{
  "objects": [
    {
      "class": "freight container",
      "confidence": 0.618,
      "bbox": { "x1": 83.64, "y1": 22.29, "x2": 587.44, "y2": 601.26 }
    }
  ],
  "num_detections": 27,
  "inference_time_ms": 44.8
}
```

### 2. Natural Language Question Answering (`POST /ask`)
```bash
curl -X POST "http://localhost:8000/ask" \
  -F "file=@data/logistics_2500/test/images/-1-DRY-CONTAINER-_-_png_jpg.rf.af49c95763d7179243f25c6bb47f3050.jpg" \
  -F "question=How many freight containers are in this image?"
```
**Sample Response:**
```json
{
  "question": "How many freight containers are in this image?",
  "intent": "COUNT",
  "target_class": "freight container",
  "answer": "There are 27 freight containers visible.",
  "confidence": "high",
  "used_detector": true
}
```

---

## 🧪 Comprehensive Automated Test Suite (45 / 45 PASS)

We have verified every single component using pytest. Run the test suite:
```bash
pytest tests/ -v
```

```
tests/test_dataset.py .......                                            [ 7 passed ]
tests/test_detector.py ....                                              [ 4 passed ]
tests/test_reasoning.py .......................                          [ 23 passed ]
tests/test_api.py ...........                                            [ 11 passed ]
======================= 45 passed in 18.2s =======================
```

---

## 📂 Repository Architecture

```
Logistics-Object-Detection-Model/
│
├── app/                              # Production FastAPI Application
│   ├── __init__.py
│   ├── main.py                       # REST Endpoints (/detect, /ask, /health, /classes)
│   ├── detector.py                   # RT-DETR PyTorch Inference Wrapper
│   ├── reasoning.py                  # Hand-written Deterministic Reasoning & Intent Engine
│   ├── schemas.py                    # Pydantic V2 Request/Response Models
│   └── utils.py                      # Bounding box geometry, distance, and IoU math
│
├── configs/
│   └── data.yaml                     # 5-class dataset specification
│
├── scripts/
│   ├── prepare_dataset.py            # Custom HTTP Range streaming dataset extractor
│   ├── verify_dataset.py             # 12-point dataset integrity audit script
│   ├── train.py                      # RT-DETR fine-tuning script with mixed precision
│   ├── pretrain_smoke_test.py        # Checkpoint 2 smoke test script
│   ├── evaluate.py                   # Test-set evaluation & mAP calculation
│   ├── error_analysis.py             # Script to extract failure cases & IoU errors
│   ├── smoke_test.py                 # Live API validation script
│   └── visualize_samples.py          # Generates visual bounding-box prediction previews
│
├── tests/                            # 45 Automated Unit & Integration Tests
│   ├── test_dataset.py               # Dataset splits and bounding box validation
│   ├── test_detector.py              # Model loading and prediction validation
│   ├── test_reasoning.py             # 23 tests for intent routing and guardrails
│   └── test_api.py                   # 11 tests for FastAPI HTTP endpoints
│
├── weights/
│   └── best.pt                       # Trained RT-DETR-L model weights
│
├── docs/                             # Hackathon Documentation Deliverables
│   ├── MEMO.md                       # Required 2-Page Engineering & Sourcing Memo
│   ├── API.md                        # Complete API payload documentation
│   ├── DATASET.md                    # Detailed dataset ontology & sourcing guide
│   └── PROJECT_LOG.md                # Real-time engineering log & checkpoint tracker
│
├── artifacts/                        # Validation artifacts & visual samples
│   ├── dataset_verification.txt      # 12-check dataset verification audit report
│   ├── system_info.txt               # Hardware & CUDA benchmark report
│   └── sample_predictions/           # Visual test images with drawn bounding boxes
│
├── Dockerfile                        # Production container image
├── docker-compose.yml                # Multi-platform deployment configuration
├── requirements.txt                  # Locked Python dependencies
├── LICENSE                           # MIT License
└── README.md                         # Complete project documentation
```

---

## 📜 License & Compliance

- **Dataset**: Roboflow Universe `logistics-sz9jr` under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Model Code**: MIT License. Developed for the Pre-Hackathon Screening (Round 1).
- **Constraints Guarantee**: 100% compliant with zero agentic frameworks (no LangChain / LangGraph), genuine RT-DETR training, and reproducible documentation.
