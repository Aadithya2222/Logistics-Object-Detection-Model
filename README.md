# 📦 Autonomous Logistics Object Detection & Reasoning System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5.1%2BCUDA12.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![RT-DETR](https://img.shields.io/badge/Model-RT--DETR--Large-00599C?style=for-the-badge&logo=opencv&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Computer Vision + Natural Language Reasoning API**  
*Author: Aadithya R | Track: Computer Vision + Applied ML Engineering*

[📄 AWS EC2 Deployment Guide](docs/AWS_DEPLOYMENT.md) • [📄 Written Engineering Memo](docs/MEMO.md) • [📊 Evaluation Documentation](docs/EVALUATION.md) • [📊 Verification Audit](artifacts/dataset_verification.txt)

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

## 7. Deployment Artifact vs. Temporary Live Demo

### Deployment Environments Summary

| Environment Type | Base URL / Host | Purpose & SLA |
| :--- | :--- | :--- |
| **Local Docker** | `http://localhost:7860` | Development, local debugging, and unit/integration test suite execution. |
| **AWS EC2 Production** | `http://<EC2_PUBLIC_IP>` *(or Nginx `:80`/`:443` domain)* | **24/7 Autonomous Hackathon Hosting**. Public Nginx reverse proxy forwarding to internal port `7860`. |
| **Cloudflare Quick Tunnel** | `https://prices-debug-match-twist.trycloudflare.com` | **Temporary Development Demo Endpoint**. Used only for temporary external testing while local tunnel process runs. |

### Deployment Artifact (Primary & Reproducible)
The primary deployment artifact for this project is the **Docker container** built from the root `Dockerfile`. It encapsulates the full RT-DETR-L model, PyTorch inference engine, post-processing guardrails, and FastAPI application logic for consistent, reproducible local or cloud execution.

```bash
# 1. Build Docker image
docker build -t logistics-object-detection .

# 2. Run container on port 7860
docker run -d -p 7860:7860 -e PORT=7860 --name logistics-app logistics-object-detection
```

Local Swagger UI documentation is accessible at: `http://localhost:7860/docs`

### Temporary Development Demo Endpoint
For temporary live testing and external API evaluation, a **Cloudflare Quick Tunnel** forwards external HTTP requests to the locally running Docker container:

- **Temporary Base URL**: `https://prices-debug-match-twist.trycloudflare.com`
- **Interactive Swagger UI**: `https://prices-debug-match-twist.trycloudflare.com/docs`

> [!IMPORTANT]
> **Deployment Clarification**:
> - The Cloudflare Quick Tunnel URL is a **temporary development demo endpoint** used strictly to expose the locally running API container for external evaluation.
> - It is **NOT** a persistent 24/7 production server, guaranteed uptime host, or SLA-backed production deployment.
> - The tunnel URL functions only while the local server and background tunnel session remain active, and will expire or change when the local process is terminated.
> - The complete, production-reproducible deployment artifact remains the **Docker image / repository code**, which can be deployed anywhere via `docker run` on port `7860`.

---

## 8. API Endpoints & Example Usage

The API exposes four core HTTP endpoints available locally (`http://localhost:7860`), on AWS EC2 via Nginx (`http://<EC2_PUBLIC_IP>`), or via the temporary demo URL (`https://prices-debug-match-twist.trycloudflare.com`):

- **`GET /health`**: Liveness probe returning `{"status": "ok", "version": "1.0.0", "model_loaded": true}`.
- **`GET /classes`**: Returns array of 5 supported object class names.
- **`POST /detect`**: Accepts image file, returns array of detected objects with class, confidence, and bounding box coordinates `[xmin, ymin, xmax, ymax]`.
- **`POST /ask`**: Accepts image file + `question` string, returns detected intent, filtered objects, and natural language reasoning answer.

### cURL Examples

```bash
# 1. Health Check
curl -X GET "http://localhost:7860/health"

# 2. Object Detection
curl -X POST "http://localhost:7860/detect" \
  -F "file=@sample.jpg"

# 3. Visual Reasoning Question
curl -X POST "http://localhost:7860/ask" \
  -F "file=@sample.jpg" \
  -F "question=How many freight containers are visible?"
```

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

## 10. AWS EC2 Production Deployment Overview

To maintain 24/7 API availability for hackathon evaluation without keeping a local PC running, deploy to **AWS EC2**:

- **Target Instance**: `t3.small` (2 vCPU, 2 GiB RAM, Ubuntu 24.04 LTS, `ap-south-1` region).
- **Public Reverse Proxy Architecture**: Nginx accepts traffic on `:80` (with `:443` reserved for future SSL) and proxies requests internally to FastAPI on `:7860`.
- **Process Management**: `docker-compose.yml` with `restart: unless-stopped` ensures automatic restart after crashes or EC2 host reboot.
- **Security Group Inbound Rules**:
  - SSH (TCP 22): Administrator IP only (Default is empty `[]` in Terraform for security; specify `admin_cidr_blocks = ["YOUR_PUBLIC_IP/32"]` in `terraform.tfvars`).
  - HTTP (TCP 80) / HTTPS (TCP 443): `0.0.0.0/0` (Public web traffic).
  - *Port 7860 is NOT exposed publicly in Security Group.*
- **Memory Safety**: Includes documented 2–4 GB optional EC2 swap configuration buffer.
- **Deployment Guide**: Complete step-by-step instructions, Nginx setup, swap configuration, and troubleshooting commands are documented in [`docs/AWS_DEPLOYMENT.md`](docs/AWS_DEPLOYMENT.md).

> [!CAUTION]
> **AWS Billing Note**: Free Tier eligibility depends on individual AWS console account status. Resources created outside applicable Free Tier thresholds will incur charges.


---

## 11. Infrastructure as Code (Terraform)

The repository provides production-grade **Terraform Infrastructure as Code (IaC)** templates in the [`terraform/`](file:///C:/Aadithya%20projects/logistics-object-detection/terraform) directory to automate AWS EC2 provisioning:

- **Automated Provisioning**: Provisions `t3.small` EC2 instance, 20 GiB `gp3` encrypted EBS disk, and Security Group (22, 80, 443).
- **Automated Bootstrap**: `user-data.sh` automatically updates Ubuntu 24.04 LTS, configures 2GB swap space, installs Docker/Compose/Nginx, clones the GitHub repo, builds the container, and sets up Nginx proxy.
- **Reproducible Teardown**: Run `terraform destroy` to cleanly dismantle all AWS resources when evaluation ends.
- **Usage Commands**:
  ```bash
  cd terraform
  cp terraform.tfvars.example terraform.tfvars
  terraform init
  terraform plan
  terraform apply
  ```

*See [`docs/AWS_DEPLOYMENT.md`](docs/AWS_DEPLOYMENT.md) for full Terraform workflow and outputs.*

---

## 12. System Limitations & Deployment Notes

- **Primary Artifact**: The Docker container (`Dockerfile`) provides 100% reproducible deployment on any host with Docker installed.
- **Hugging Face Space**: The repository structure is also uploaded to Hugging Face Space `Aadithya2201/logistics-object-detection` (currently paused due to CPU quota limits).
- **Model Limitations**:
  1. *Spatial Partitioning*: Large shipping containers spanning full image frames may occasionally be partitioned into two adjacent container boxes ($\text{IoU} < 0.80$).
  2. *Texture Ambiguity*: Weathered wood textures on crates or stacked boxes can occasionally be misclassified as `wood pallet`.
  3. *Small Objects*: Distant cardboard boxes occupying $<10$ pixels have lower recall.




