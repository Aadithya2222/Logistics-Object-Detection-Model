# LOGISTICS OBJECT DETECTION & REASONING API
## Technical Presentation Script, Slide Outline & Interview Defense Guide

---

### Executive Summary & System Overview

This document serves as the complete presentation guide and technical defense reference for the **Logistics Object Detection & Reasoning API** project, prepared for the RAP Pre-Hackathon Screening.

- **GitHub Repository**: [https://github.com/Aadithya2222/Logistics-Object-Detection-Model](https://github.com/Aadithya2222/Logistics-Object-Detection-Model)
- **Live AWS API Base URL**: `http://13.233.255.22`
- **Interactive Swagger Docs**: `http://13.233.255.22/docs`
- **Primary Deliverables**:
  - `Logistics_Object_Detection_Reasoning_API_Presentation.pptx` (14 Widescreen 16:9 Slides with embedded speaker notes)
  - `Logistics_Object_Detection_Reasoning_API_Presentation.pdf` (14 Landscape Dark Slides)
  - `Presentation_Notes.md` (This document)

---

### Presentation Narrative Arc

The presentation is structured around a rigorous 12-stage ML engineering storytelling arc:

```
PROBLEM
   ↓
REAL-WORLD LOGISTICS DATA
   ↓
DATASET PREPARATION
   ↓
RT-DETR FINE-TUNING
   ↓
HELD-OUT EVALUATION
   ↓
FAILURE MODE DIAGNOSTICS
   ↓
CUSTOM 4-STAGE POST-PROCESSING
   ↓
DETERMINISTIC REASONING ENGINE
   ↓
FASTAPI MICROSERVICE
   ↓
DOCKER CONTAINERIZATION
   ↓
AWS EC2 + NGINX DEPLOYMENT
   ↓
LIVE PRODUCTION API
```

---

### Slide-by-Slide Presentation Guide & Speaker Script

#### SLIDE 1 — TITLE: LOGISTICS OBJECT DETECTION & REASONING API
- **Title**: LOGISTICS OBJECT DETECTION & REASONING API
- **Subtitle**: End-to-End Computer Vision System from RT-DETR Fine-Tuning to AWS Deployment
- **Speaker Script**:
  > *"Welcome everyone. Today I'm presenting the Logistics Object Detection & Reasoning API—an end-to-end computer vision system designed for automated warehouse object recognition and bounded natural-language reasoning. Instead of stopping at model training, we built, evaluated, post-processed, containerized, and deployed a production API live on AWS EC2."*
- **Technical Key Facts**:
  - Model: RT-DETR-L fine-tuned on 5 logistics domain classes.
  - Deployment: AWS ap-south-1 (Mumbai), EC2 t3.small, Docker Compose, Nginx (:80).

---

#### SLIDE 2 — PROBLEM & OBJECTIVE
- **Header**: PROBLEM & OBJECTIVE
- **Subtitle**: Real-World Logistics Vision & Bounded Natural Language Reasoning
- **Speaker Script**:
  > *"In modern supply chain automation, vision systems must handle dense, overlapping objects like wood pallets and cardboard boxes. Furthermore, inventory managers need to query visual scenes naturally—without relying on ungrounded LLMs that hallucinate facts. Our objective was to extract precise bounding boxes, clean raw detector noise, and provide a deterministic Q&A interface that explicitly refuses to guess when visual evidence is insufficient."*
- **Visual Flow**:
  `IMAGE → OBJECT DETECTION → STRUCTURED DETECTIONS → NATURAL LANGUAGE QUESTION → REASONING ENGINE → VERIFIED ANSWER`

---

#### SLIDE 3 — SOLUTION OVERVIEW
- **Header**: SOLUTION OVERVIEW
- **Subtitle**: Dual-Endpoint Computer Vision & Reasoning Architecture
- **Speaker Script**:
  > *"Our solution is built as a decoupled FastAPI microservice. Public HTTP traffic arrives on Nginx Port 80 and is proxied to our containerized ASGI server on Port 7860. The API exposes `/detect` for raw bounding box extraction and `/ask` for structured natural language Q&A."*
- **Technical Architecture Highlights**:
  - Decoupled endpoints (`/detect` and `/ask`).
  - Operational health checks (`/health` and `/classes`).
  - 4-stage post-processing guardrail between raw DETR output and reasoning router.

---

#### SLIDE 4 — DATASET & CLASS DESIGN
- **Header**: DATASET & CLASS DESIGN
- **Subtitle**: 2,500 Images across 5 Core Logistics Domain Classes
- **Speaker Script**:
  > *"We assembled a domain dataset of 2,500 images representing 5 key logistics assets: cardboard box, forklift, freight container, wood pallet, and truck. The dataset is split into 1,500 training images, 500 validation images, and 500 strictly held-out test images, targeting 300 train and 100 evaluation images per class filter."*
- **Dataset Metrics**:
  - Total: 2,500 images.
  - Train: 1,500 | Val: 500 | Test: 500.
  - Non-COCO custom class: `wood pallet` (Class 3).

---

#### SLIDE 5 — MODEL ARCHITECTURE: RT-DETR-L
- **Header**: MODEL ARCHITECTURE: RT-DETR-L
- **Subtitle**: Real-Time DEtection TRansformer for High-Efficiency Bounding Box Regression
- **Speaker Script**:
  > *"We selected RT-DETR-L, a Real-Time DEtection TRansformer implemented via Ultralytics. RT-DETR combines an HGNet-v2 backbone with a hybrid encoder and a transformer decoder. By using learned object queries and bipartite Hungarian matching, RT-DETR eliminates traditional anchor box heuristics and delivers superior global context awareness."*
- **Technical Highlights**:
  - HGNet-v2 backbone (B0-B5 hierarchy).
  - COCO-pretrained weight initialization (`rtdetr-l.pt`).
  - End-to-end NMS-free bipartite matching loss during training.

---

#### SLIDE 6 — EXPERIMENT CONFIGURATION
- **Header**: EXPERIMENT CONFIGURATION
- **Subtitle**: Hyperparameters, Hardware, and Checkpoint Selection
- **Speaker Script**:
  > *"Here is our complete experiment configuration. Training was conducted on a local NVIDIA RTX 3050 6GB GPU for 3,235 seconds (~54 minutes). While 50 epochs were configured, training concluded at epoch 10. The deployed checkpoint corresponds to epoch 1 (`epoch0.pt`), which achieved peak Ultralytics validation fitness of 0.40391."*
- **Configuration Dashboard**:
  - Resolution: 640x640 | Batch Size: 2 | LR0: 0.0001 (AdamW) | Weight Decay: 0.0005.
  - Augmentations: Mosaic (1.0), HSV-H (0.015), HSV-S (0.7), HSV-V (0.4), Scale (0.5), Erasing (0.4).

---

#### SLIDE 7 — EVALUATION RESULTS
- **Header**: EVALUATION RESULTS
- **Subtitle**: Rigorous Performance Benchmark on 500 Held-Out Test Images
- **Speaker Script**:
  > *"On our 500 held-out test images, the model achieved an overall mAP@0.5 of 50.40% and mAP@0.5:0.95 of 34.08%, with a Precision of 57.34% and Recall of 48.73%. Per-class breakdown highlights strong performance on wood pallets (67.08% mAP50) and trucks (65.15% mAP50), while freight containers remain the hardest class at 16.83% mAP50."*
- **Held-Out Test Benchmarks**:
  - `wood pallet`: mAP50 = 67.08%, P = 78.50%, R = 66.00%.
  - `truck`: mAP50 = 65.15%, P = 57.80%, R = 58.70%.
  - `forklift`: mAP50 = 61.51%, P = 70.00%, R = 52.80%.
  - `cardboard box`: mAP50 = 41.44%, P = 66.80%, R = 28.30%.
  - `freight container`: mAP50 = 16.83%, P = 13.60%, R = 37.90%.

---

#### SLIDE 8 — WHERE THE MODEL FAILS
- **Header**: WHERE THE MODEL FAILS
- **Subtitle**: Root-Cause Diagnostic of Real Detector Error Categories
- **Speaker Script**:
  > *"Engineering maturity means understanding where your model fails. We identified 5 specific failure modes: internal nested duplicate boxes, cross-class bounding box collisions, freight container body fragmentation (causing 16.83% mAP), cardboard box recall loss (28.30%), and low-confidence border artifacts."*
- **5 Failure Categories**:
  1. Internal sub-region duplicate boxes.
  2. Cross-class duplicate overlap (freight container vs truck).
  3. Freight container partition/split errors.
  4. Cardboard box vs wood pallet/crate confusion.
  5. Border edge artifacts (partial edge boxes).

---

#### SLIDE 9 — CUSTOM POST-PROCESSING PIPELINE
- **Header**: CUSTOM POST-PROCESSING PIPELINE
- **Subtitle**: 4-Stage Rule Engine for Error Mitigation & Output Cleanup
- **Speaker Script**:
  > *"To resolve these 5 failure modes, we engineered a deterministic 4-stage post-processing pipeline. It applies Class-Aware NMS (IoU 0.45), Containment Suppression using Intersection over Smallest (IoS 0.65) to drop nested sub-boxes, Boundary Artifact Filtering (conf < 0.30 & inside_ratio < 0.50), and Cross-Class Overlap Suppression (IoU 0.80). This pipeline is verified by 48 automated PyTest unit tests."*
- **Rule Engine Summary**:
  - Stage 1: NMS IoU = 0.45
  - Stage 2: Containment IoS = 0.65
  - Stage 3: Edge Filter (conf < 0.30 & inside_ratio < 0.50)
  - Stage 4: Cross-Class IoU = 0.80

---

#### SLIDE 10 — DETERMINISTIC REASONING ENGINE
- **Header**: DETERMINISTIC REASONING ENGINE
- **Subtitle**: Structured Natural Language Q&A with Strict Refusal Guardrails
- **Speaker Script**:
  > *"Our reasoning layer routes questions into 6 deterministic intents: COUNT, PRESENCE, LIST, MOST_COMMON, SPATIAL, and UNKNOWN. It operates without external LLM dependencies, guaranteeing sub-millisecond execution and zero hallucination. If detector confidence is below 0.25, the system explicitly refuses to guess, returning an 'insufficient information' message."*
- **Intents & Guardrails**:
  - Intents: `COUNT`, `PRESENCE`, `LIST`, `MOST_COMMON`, `SPATIAL`, `UNKNOWN`.
  - Confidence Floor: 0.25 (Refusal below 0.25).
  - High-Confidence Cutoff: 0.50.

---

#### SLIDE 11 — END-TO-END SYSTEM ARCHITECTURE
- **Header**: END-TO-END SYSTEM ARCHITECTURE
- **Subtitle**: Decoupled Production Microservice Architecture on AWS EC2
- **Speaker Script**:
  > *"Our deployment architecture follows enterprise standards. Nginx handles public ingress on Port 80, proxying traffic internally to containerized FastAPI on Port 7860. Infrastructure is managed via Terraform, keeping Port 7860 restricted to localhost."*
- **Tiered Architecture**:
  `Client → Nginx (:80) → FastAPI (:7860) → RT-DETR + Post-Processing + Reasoning Layer`

---

#### SLIDE 12 — API DEMONSTRATION & SCHEMAS
- **Header**: API DEMONSTRATION & SCHEMAS
- **Subtitle**: Production JSON Contracts for Bounding Box Extraction and Q&A
- **Speaker Script**:
  > *"Here are the actual production JSON responses returned by `/detect` and `/ask`. `/detect` delivers normalized bounding box coordinates and confidence ratings, while `/ask` returns natural language answers alongside intent metadata, confidence classification, and underlying detection counts."*

---

#### SLIDE 13 — AWS INFRASTRUCTURE & DEPLOYMENT
- **Header**: AWS INFRASTRUCTURE & DEPLOYMENT
- **Subtitle**: Cloud Hosting, Infrastructure as Code, and Operational Incident Resolution
- **Speaker Script**:
  > *"The API is live on AWS EC2 in ap-south-1 Mumbai at http://13.233.255.22. During deployment, we resolved a real disk exhaustion incident when extracting PyTorch container layers by expanding our EBS volume from 20 GiB to 40 GiB and executing live filesystem resizing using growpart and resize2fs."*
- **Deployment Details**:
  - Host: AWS ap-south-1 (Mumbai), EC2 t3.small, 40 GiB gp3 EBS, 2GB Swap.
  - Live Base URL: `http://13.233.255.22`

---

#### SLIDE 14 — RESULTS, LIMITATIONS & FUTURE WORK
- **Header**: RESULTS, LIMITATIONS & FUTURE WORK
- **Subtitle**: Project Victories, Known Constraints, and Next-Generation Roadmap
- **Speaker Script**:
  > *"In summary, we built a complete computer vision system from fine-tuning to cloud deployment. While freight container precision and CPU latency remain clear constraints, our custom guardrails, unit test suite, and automated deployment demonstrate a robust ML engineering pipeline."*
- **Roadmap Highlights**:
  - Extend training to 50 epochs with cosine LR scheduling.
  - Collect hard negative freight container samples & use focal loss.
  - Migrate deployment to GPU instance (`g4dn.xlarge`).

---

### Interview Defense Guide: 24 Technical Questions & Bulletproof Answers

1. **Q: Why RT-DETR instead of YOLOv8 or Faster R-CNN?**
   - **Answer**: RT-DETR is a Real-Time DEtection TRansformer that replaces hand-crafted NMS anchors with learned object queries and bipartite Hungarian matching. It delivers transformer global context awareness at latency comparable to YOLO, making it ideal for multi-scale logistics scenes.

2. **Q: Why are there 5 specific domain classes?**
   - **Answer**: The classes (`cardboard box`, `forklift`, `freight container`, `wood pallet`, `truck`) cover the essential assets of warehouse logistics. `wood pallet` was explicitly included to evaluate custom transfer learning on a non-COCO category.

3. **Q: How was the dataset split structured?**
   - **Answer**: 2,500 total images split into 1,500 train, 500 validation, and 500 held-out test images. Sampling targeted 300 train and 100 evaluation images per class filter.

4. **Q: Why were only 10 epochs completed out of 50 configured?**
   - **Answer**: 10 epochs provided a sufficient convergence baseline (~54 minutes training time). Ultralytics fitness peaked early at epoch 1 (`best.pt`, fitness 0.40391), demonstrating that early stopping preserved optimal validation fitness.

5. **Q: Why does `best.pt` correspond to epoch 1 (`epoch0.pt`)?**
   - **Answer**: Ultralytics calculates fitness as `0.1 * mAP50 + 0.9 * mAP50-95`. Epoch 1 achieved the highest weighted validation fitness (0.40391) across the 10 executed epochs.

6. **Q: Why is freight container mAP low (16.83%)?**
   - **Answer**: Freight containers exhibit severe aspect ratio variations, surface occlusions, and visual ambiguity with truck trailers. Raw DETR queries fragmented large container bodies into overlapping sub-boxes.

7. **Q: Why is cardboard box recall low (28.30%)?**
   - **Answer**: Cardboard boxes in warehouse environments are frequently small, densely stacked, and visually similar to wooden crates, leading the detector to miss heavily occluded boxes.

8. **Q: Why implement custom post-processing beyond standard NMS?**
   - **Answer**: Standard NMS only checks same-class IoU overlap. It cannot resolve nested sub-region boxes (where a small box is inside a large box) or severe cross-class duplicate predictions.

9. **Q: Why use IoS (Intersection over Smallest) for containment suppression?**
   - **Answer**: When box A is entirely inside box B, standard IoU is low because box B's area dominates the denominator. IoS divides intersection area by box A's area, yielding ~1.0 for contained sub-boxes and allowing clean suppression.

10. **Q: Why use Cross-Class IoU suppression at 0.80?**
    - **Answer**: In severe cases, the model predicts both a `truck` and a `freight container` for the exact same physical region. Cross-Class IoU at 0.80 removes the lower-confidence prediction.

11. **Q: Why avoid LangChain, CrewAI, or LLMs in the reasoning engine?**
    - **Answer**: The hackathon rules prohibited non-deterministic third-party APIs. Our custom pattern matcher guarantees sub-millisecond execution, zero hallucination, and 100% reproducible JSON outputs.

12. **Q: How does the confidence guardrail work?**
    - **Answer**: Detections below 0.25 confidence are dropped before reasoning. If remaining detections cannot satisfy the requested intent (or if detector confidence is below 0.50), the system explicitly returns "insufficient information".

13. **Q: What are the 6 supported reasoning intents?**
    - **Answer**: `COUNT`, `PRESENCE`, `LIST`, `MOST_COMMON`, `SPATIAL`, and `UNKNOWN`.

14. **Q: How does `UNKNOWN` intent behave?**
    - **Answer**: Questions outside the 5 visual intent categories (e.g. "What is the weather?") map to `UNKNOWN`, triggering an immediate "insufficient information" refusal response.

15. **Q: Why use FastAPI for the backend?**
    - **Answer**: FastAPI provides high-performance asynchronous request handling via Uvicorn, native Pydantic v2 schema validation, and automatic OpenAPI/Swagger documentation generation.

16. **Q: Why containerize with Docker & Docker Compose?**
    - **Answer**: Docker isolates PyTorch, CUDA runtime, OpenCV, and FastAPI dependencies into a reproducible environment, eliminating host environment mismatch on AWS EC2.

17. **Q: Why use Nginx as a reverse proxy?**
    - **Answer**: Nginx handles public HTTP traffic on Port 80, manages request buffers, provides rate limiting, and shields the internal FastAPI process on Port 7860 from direct Internet exposure.

18. **Q: What instance type was deployed on AWS?**
    - **Answer**: AWS EC2 `t3.small` (2 vCPU, 2GB RAM) in `ap-south-1` Mumbai, supplemented by a 2GB swap file to prevent OOM errors during PyTorch inference.

19. **Q: What happened during the AWS Docker disk space incident?**
    - **Answer**: Extracting heavy PyTorch container layers filled the initial 20 GiB EBS volume. We expanded the volume to 40 GiB in AWS and ran `growpart /dev/nvme0n1 1` and `resize2fs /dev/nvme0n1p1` live on Ubuntu 24.04 without downtime.

20. **Q: Why is Port 7860 not open in the AWS Security Group?**
    - **Answer**: Closing Port 7860 publicly ensures all ingress traffic passes through Nginx on Port 80, enforcing single-point ingress security.

21. **Q: How is Terraform utilized in this project?**
    - **Answer**: Terraform scripts (`terraform/main.tf`, `security-groups.tf`) provision the EC2 instance, EBS volume, and Security Group ingress rules declaratively.

22. **Q: Why is HTTPS/TLS not enabled on the live API?**
    - **Answer**: HTTPS requires a registered domain name to issue Let's Encrypt SSL certificates. The live API uses HTTP on raw IP (`http://13.233.255.22`), with Port 443 reserved in Security Groups for future domain binding.

23. **Q: What unit tests are implemented?**
    - **Answer**: 48 automated PyTest tests verify post-processing rules, IoS containment, boundary filters, intent routing, schema validation, and endpoint responses.

24. **Q: If you had 2 weeks to upgrade this system, what would you do?**
    - **Answer**: 1) Train for 40 more epochs with cosine learning rate decay; 2) Add focal loss and hard negative freight container samples; 3) Deploy on an AWS GPU instance (`g4dn.xlarge`); 4) Bind a custom domain with HTTPS TLS.

---
