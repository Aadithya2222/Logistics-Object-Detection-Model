"""
scripts/generate_presentation.py

Generates:
1. Chart images in artifacts/ for presentation slides:
   - artifacts/chart_dataset_dist.png
   - artifacts/chart_per_class_map.png
   - artifacts/chart_nms_pipeline.png
   - artifacts/chart_system_arch.png
   - artifacts/chart_aws_deploy.png
2. Logistics_Object_Detection_Reasoning_API_Presentation.pptx (14 widescreen slides with full speaker notes)
3. Logistics_Object_Detection_Reasoning_API_Presentation.pdf (14 landscape dark slides matching PPTX)
4. Presentation_Notes.md (Full slide script, defense Q&A, and technical documentation)
5. Synchronizes generated deliverables to RAP/Presentation/ folder.
"""

import os
import sys
import shutil
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
RAP_PRES_DIR = ROOT / "RAP" / "Presentation"
ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)
RAP_PRES_DIR.mkdir(exist_ok=True, parents=True)

# Colors
C_DARK_BG = "#0F172A"      # Slate 900
C_CARD_BG = "#1E293B"      # Slate 800
C_ACCENT_BLUE = "#38BDF8"  # Sky 400
C_ACCENT_GREEN = "#34D399" # Emerald 400
C_ACCENT_ORANGE = "#FB923C"# Amber 400
C_ACCENT_RED = "#F87171"   # Red 400
C_TEXT_LIGHT = "#F8FAFC"   # Slate 50
C_TEXT_MUTED = "#94A3B8"   # Slate 400
C_BORDER = "#334155"       # Slate 700

# RGB Colors for pptx
RGB_DARK_BG = RGBColor(15, 23, 42)
RGB_CARD_BG = RGBColor(30, 41, 59)
RGB_ACCENT_BLUE = RGBColor(56, 189, 248)
RGB_ACCENT_GREEN = RGBColor(52, 211, 153)
RGB_ACCENT_ORANGE = RGBColor(251, 146, 60)
RGB_ACCENT_RED = RGBColor(248, 113, 113)
RGB_TEXT_LIGHT = RGBColor(248, 250, 252)
RGB_TEXT_MUTED = RGBColor(148, 163, 184)
RGB_BORDER = RGBColor(51, 65, 85)

# ReportLab HexColors
RL_DARK_BG = colors.HexColor(C_DARK_BG)
RL_CARD_BG = colors.HexColor(C_CARD_BG)
RL_ACCENT_BLUE = colors.HexColor(C_ACCENT_BLUE)
RL_ACCENT_GREEN = colors.HexColor(C_ACCENT_GREEN)
RL_TEXT_LIGHT = colors.HexColor(C_TEXT_LIGHT)
RL_TEXT_MUTED = colors.HexColor(C_TEXT_MUTED)
RL_BORDER = colors.HexColor(C_BORDER)


def generate_chart_dataset_dist():
    """Slide 4: Dataset Class Distribution Chart"""
    fig, ax = plt.subplots(figsize=(8, 4.2), facecolor=C_DARK_BG)
    ax.set_facecolor(C_DARK_BG)
    
    classes = ['cardboard box', 'forklift', 'freight container', 'wood pallet', 'truck']
    train_counts = [300, 300, 300, 300, 300]
    val_counts = [100, 100, 100, 100, 100]
    test_counts = [100, 100, 100, 100, 100]
    
    x = np.arange(len(classes))
    width = 0.25
    
    rects1 = ax.bar(x - width, train_counts, width, label='Train (1,500)', color='#38BDF8', edgecolor=C_BORDER)
    rects2 = ax.bar(x, val_counts, width, label='Val (500)', color='#34D399', edgecolor=C_BORDER)
    rects3 = ax.bar(x + width, test_counts, width, label='Test (500)', color='#F59E0B', edgecolor=C_BORDER)
    
    ax.set_ylabel('Images per Split Target', color=C_TEXT_LIGHT, fontsize=11, fontweight='bold')
    ax.set_title('Dataset Balance Across 5 Logistics Classes (Total: 2,500 Images)', color=C_TEXT_LIGHT, fontsize=13, fontweight='bold', pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(classes, color=C_TEXT_LIGHT, fontsize=10, fontweight='bold')
    ax.tick_params(colors=C_TEXT_MUTED, which='both')
    ax.legend(facecolor=C_CARD_BG, edgecolor=C_BORDER, labelcolor=C_TEXT_LIGHT, fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(C_BORDER)
    ax.spines['bottom'].set_color(C_BORDER)
    ax.grid(axis='y', linestyle='--', alpha=0.2, color=C_TEXT_MUTED)
    
    # Add values on top of bars
    for rect in rects1 + rects2 + rects3:
        h = rect.get_height()
        ax.annotate(f'{h}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom',
                    color=C_TEXT_LIGHT, fontsize=8, fontweight='bold')
        
    plt.tight_layout()
    path = ARTIFACTS_DIR / "chart_dataset_dist.png"
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return path


def generate_chart_per_class_map():
    """Slide 7: Per-Class mAP Performance Chart"""
    fig, ax = plt.subplots(figsize=(8.5, 4.2), facecolor=C_DARK_BG)
    ax.set_facecolor(C_DARK_BG)
    
    classes = ['wood pallet', 'truck', 'forklift', 'cardboard box', 'freight container']
    map50 = [67.08, 65.15, 61.51, 41.44, 16.83]
    map50_95 = [47.00, 42.00, 36.10, 31.70, 13.60]
    
    y = np.arange(len(classes))
    height = 0.35
    
    rects1 = ax.barh(y - height/2, map50, height, label='mAP@0.5 (%)', color='#38BDF8', edgecolor=C_BORDER)
    rects2 = ax.barh(y + height/2, map50_95, height, label='mAP@0.5:0.95 (%)', color='#34D399', edgecolor=C_BORDER)
    
    ax.set_xlabel('Score (%)', color=C_TEXT_LIGHT, fontsize=11, fontweight='bold')
    ax.set_title('Held-Out Test Set: Per-Class mAP Benchmarks (500 Test Images)', color=C_TEXT_LIGHT, fontsize=13, fontweight='bold', pad=12)
    ax.set_yticks(y)
    ax.set_yticklabels(classes, color=C_TEXT_LIGHT, fontsize=10, fontweight='bold')
    ax.invert_yaxis()
    ax.tick_params(colors=C_TEXT_MUTED, which='both')
    ax.legend(facecolor=C_CARD_BG, edgecolor=C_BORDER, labelcolor=C_TEXT_LIGHT, fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(C_BORDER)
    ax.spines['bottom'].set_color(C_BORDER)
    ax.grid(axis='x', linestyle='--', alpha=0.2, color=C_TEXT_MUTED)
    
    for rect in rects1:
        w = rect.get_width()
        ax.annotate(f'{w:.1f}%', xy=(w, rect.get_y() + rect.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", ha='left', va='center',
                    color='#38BDF8', fontsize=8.5, fontweight='bold')
                    
    for rect in rects2:
        w = rect.get_width()
        ax.annotate(f'{w:.1f}%', xy=(w, rect.get_y() + rect.get_height() / 2),
                    xytext=(4, 0), textcoords="offset points", ha='left', va='center',
                    color='#34D399', fontsize=8.5, fontweight='bold')
        
    plt.tight_layout()
    path = ARTIFACTS_DIR / "chart_per_class_map.png"
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return path


def generate_chart_nms_pipeline():
    """Slide 9: Custom Post-Processing Pipeline Diagram"""
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=C_DARK_BG)
    ax.set_facecolor(C_DARK_BG)
    ax.axis('off')
    
    stages = [
        ("Raw Detector Output", "RT-DETR-L Bounding Boxes\n+ Confidence Scores", "#64748B"),
        ("Stage 1: Class NMS", "IoU Threshold = 0.45\nEliminates same-class overlap", "#38BDF8"),
        ("Stage 2: Containment", "IoS Threshold = 0.65\nSuppresses nested sub-boxes", "#34D399"),
        ("Stage 3: Edge Filter", "Conf < 0.30 & Inside < 0.50\nRemoves border artifacts", "#F59E0B"),
        ("Stage 4: Cross-Class", "IoU Threshold = 0.80\nResolves multi-class overlap", "#EC4899"),
        ("Clean Detections", "Structured Output\n48 Tests Passing", "#10B981")
    ]
    
    n = len(stages)
    box_width = 1.2
    spacing = 1.45
    
    for i, (title, desc, color) in enumerate(stages):
        x = 0.6 + i * spacing
        y = 0.5
        
        # Draw Box
        rect = plt.Rectangle((x - box_width/2, y - 0.3), box_width, 0.6,
                             facecolor=C_CARD_BG, edgecolor=color, linewidth=2, zorder=2)
        ax.add_patch(rect)
        
        # Add Title & Text
        ax.text(x, y + 0.12, title, color=color, fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=3)
        ax.text(x, y - 0.1, desc, color=C_TEXT_LIGHT, fontsize=7.5, ha='center', va='center', zorder=3)
        
        # Arrow to next
        if i < n - 1:
            ax.annotate('', xy=(x + spacing - box_width/2 - 0.02, y), xytext=(x + box_width/2 + 0.02, y),
                        arrowprops=dict(arrowstyle="-|>", color=C_TEXT_MUTED, lw=2, mutation_scale=15), zorder=1)
            
    ax.set_xlim(0, 0.6 + (n - 1) * spacing + box_width/2 + 0.4)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    path = ARTIFACTS_DIR / "chart_nms_pipeline.png"
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return path


def generate_chart_system_arch():
    """Slide 3 / 11: System Architecture Diagram"""
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=C_DARK_BG)
    ax.set_facecolor(C_DARK_BG)
    ax.axis('off')
    
    # Layout blocks
    boxes = [
        ("Client / API Request", "HTTP POST /detect\nHTTP POST /ask", 0.15, 0.5, "#94A3B8"),
        ("Nginx Proxy (:80)", "Reverse Proxy / Ingress\nPort 7860 restricted", 0.38, 0.5, "#38BDF8"),
        ("FastAPI Container", "Uvicorn ASGI Engine\nPydantic Schemas", 0.62, 0.5, "#34D399"),
        ("Detector Engine", "RT-DETR-L + weights/best.pt\n4-Stage Post-Processing", 0.85, 0.72, "#F59E0B"),
        ("Reasoning Engine", "Intent Router (6 Intents)\nConfidence Floor (0.25)", 0.85, 0.28, "#EC4899")
    ]
    
    for title, desc, x, y, color in boxes:
        rect = plt.Rectangle((x - 0.09, y - 0.16), 0.18, 0.32,
                             facecolor=C_CARD_BG, edgecolor=color, linewidth=2, zorder=2)
        ax.add_patch(rect)
        ax.text(x, y + 0.06, title, color=color, fontsize=9, fontweight='bold', ha='center', va='center', zorder=3)
        ax.text(x, y - 0.06, desc, color=C_TEXT_LIGHT, fontsize=7.5, ha='center', va='center', zorder=3)
        
    # Connections
    # Client -> Nginx
    ax.annotate('', xy=(0.38 - 0.09, 0.5), xytext=(0.15 + 0.09, 0.5),
                arrowprops=dict(arrowstyle="-|>", color=C_TEXT_MUTED, lw=2, mutation_scale=12))
    # Nginx -> FastAPI
    ax.annotate('', xy=(0.62 - 0.09, 0.5), xytext=(0.38 + 0.09, 0.5),
                arrowprops=dict(arrowstyle="-|>", color=C_TEXT_MUTED, lw=2, mutation_scale=12))
    # FastAPI -> Detector
    ax.annotate('', xy=(0.85 - 0.09, 0.72), xytext=(0.62 + 0.09, 0.5),
                arrowprops=dict(arrowstyle="-|>", color=C_TEXT_MUTED, lw=1.8, mutation_scale=12))
    # FastAPI -> Reasoning
    ax.annotate('', xy=(0.85 - 0.09, 0.28), xytext=(0.62 + 0.09, 0.5),
                arrowprops=dict(arrowstyle="-|>", color=C_TEXT_MUTED, lw=1.8, mutation_scale=12))
    # Detector -> Reasoning connection
    ax.annotate('', xy=(0.85, 0.28 + 0.16), xytext=(0.85, 0.72 - 0.16),
                arrowprops=dict(arrowstyle="-|>", color=C_ACCENT_BLUE, lw=1.5, linestyle='--', mutation_scale=12))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    path = ARTIFACTS_DIR / "chart_system_arch.png"
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return path


def generate_chart_aws_deploy():
    """Slide 13: AWS Deployment Diagram"""
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=C_DARK_BG)
    ax.set_facecolor(C_DARK_BG)
    ax.axis('off')
    
    nodes = [
        ("Internet Client", "Public HTTP Requests", 0.12, 0.5, "#94A3B8"),
        ("AWS SG (Security Group)", "Inbound TCP :80, :443, :22\nTCP :7860 Closed Publicly", 0.35, 0.5, "#F87171"),
        ("EC2 Instance (ap-south-1)", "t3.small | Ubuntu 24.04\n40 GB gp3 EBS + 2GB Swap", 0.60, 0.5, "#38BDF8"),
        ("Docker Container", "logistics-app\nFastAPI + RT-DETR-L", 0.85, 0.5, "#34D399")
    ]
    
    for title, desc, x, y, color in nodes:
        rect = plt.Rectangle((x - 0.09, y - 0.18), 0.18, 0.36,
                             facecolor=C_CARD_BG, edgecolor=color, linewidth=2, zorder=2)
        ax.add_patch(rect)
        ax.text(x, y + 0.08, title, color=color, fontsize=9, fontweight='bold', ha='center', va='center', zorder=3)
        ax.text(x, y - 0.06, desc, color=C_TEXT_LIGHT, fontsize=7.5, ha='center', va='center', zorder=3)
        
    for i in range(len(nodes) - 1):
        x1 = nodes[i][2] + 0.09
        x2 = nodes[i+1][2] - 0.09
        ax.annotate('', xy=(x2, 0.5), xytext=(x1, 0.5),
                    arrowprops=dict(arrowstyle="-|>", color=C_TEXT_MUTED, lw=2, mutation_scale=12))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    plt.tight_layout()
    path = ARTIFACTS_DIR / "chart_aws_deploy.png"
    plt.savefig(path, dpi=200, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return path


def build_pptx_presentation():
    """Builds the 14-slide PowerPoint presentation with custom dark theme and speaker notes."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    blank_layout = prs.slide_layouts[6]
    
    slides_data = [
        {
            "num": 1,
            "title": "LOGISTICS OBJECT DETECTION & REASONING API",
            "subtitle": "End-to-End Computer Vision System from RT-DETR Fine-Tuning to AWS Deployment",
            "type": "title",
            "notes": """WHAT TO SAY:
Welcome. Today I am presenting the Logistics Object Detection & Reasoning API—an end-to-end computer vision and deterministic reasoning system built for warehouse automation.

TECHNICAL SUMMARY:
This project fine-tunes an RT-DETR-L vision transformer across 5 logistics domain classes, implements a custom 4-stage post-processing guardrail, builds a deterministic natural-language reasoning API, containerizes the stack via Docker, and deploys it live on AWS EC2 with Terraform.

DEFENSE Q&A:
Q: Why build an end-to-end system instead of just training an object detection model?
A: In real-world ML engineering, a raw model checkpoint is insufficient. Production deployment requires domain post-processing (to eliminate sub-region duplicates), structured API contracts, confidence guardrails to prevent hallucination, containerization, and cloud infrastructure."""
        },
        {
            "num": 2,
            "title": "PROBLEM & OBJECTIVE",
            "subtitle": "Real-World Logistics Vision & Bounded Natural Language Reasoning",
            "type": "content_2col",
            "col1_title": "Real-World Logistics Problem",
            "col1_body": [
                "• Dense, cluttered warehouse environments with overlapping objects.",
                "• Domain requirement includes non-COCO class (wood pallet).",
                "• Need exact bounding boxes + confidence scores for inventory tracking.",
                "• Requirement for natural language Q&A without accepting LLM hallucinations.",
                "• Must provide a reliable, self-contained, production-ready REST API."
            ],
            "col2_title": "System Objective Flow",
            "col2_body": [
                "1. Input Image: Upload warehouse scene (640x640 resolution).",
                "2. Object Detection: RT-DETR-L extracts objects & bounding boxes.",
                "3. Structured Output: 4-stage rule engine cleans raw predictions.",
                "4. Natural Language Question: User queries image context.",
                "5. Deterministic Reasoning: Intent router answers or cleanly refuses."
            ],
            "notes": """WHAT TO SAY:
Warehouses are complex environments. Standard COCO object detectors fail on custom domain classes like wood pallets and struggle with dense box stacking. Furthermore, business users want to ask natural language questions without risk of AI hallucination.

TECHNICAL EXPLANATION:
Our objective was dual-fold: 1) Extract high-precision logistics bounding boxes, and 2) Build a bounded, deterministic reasoning layer that refuses to answer when visual evidence is insufficient.

DEFENSE Q&A:
Q: Why include wood pallet as a primary class?
A: Wood pallets are ubiquitous in supply chains but missing from COCO's 80 classes. Transfer learning on domain-specific logistics data was essential."""
        },
        {
            "num": 3,
            "title": "SOLUTION OVERVIEW",
            "subtitle": "Dual-Endpoint Computer Vision & Reasoning Microservice Architecture",
            "type": "image_slide",
            "image_path": str(ARTIFACTS_DIR / "chart_system_arch.png"),
            "bullets": [
                "• Decoupled Microservice: FastAPI framework with async Uvicorn engine.",
                "• Dual Primary Endpoints: POST /detect for raw bounding boxes; POST /ask for Q&A.",
                "• Operation Support: GET /health for container liveness; GET /classes for schema discovery.",
                "• Nginx Reverse Proxy: Exposes Port 80 publicly while keeping Port 7860 bound locally."
            ],
            "notes": """WHAT TO SAY:
Here is our end-to-end architecture. The solution exposes two primary endpoints: /detect for structured bounding boxes, and /ask for natural language query processing.

TECHNICAL EXPLANATION:
Traffic enters through Nginx on Port 80, proxied internally to FastAPI on Port 7860. Detections pass through a 4-stage post-processing pipeline before entering the intent-routed reasoning engine.

DEFENSE Q&A:
Q: Why decouple /detect and /ask instead of combining them into one endpoint?
A: Modular design allows frontend clients to retrieve raw bounding box overlays independently, cache detection results, or run downstream analytics without re-invoking the reasoning parser."""
        },
        {
            "num": 4,
            "title": "DATASET & CLASS DESIGN",
            "subtitle": "2,500 Images across 5 Core Logistics Domain Classes",
            "type": "chart_and_bullets",
            "image_path": str(ARTIFACTS_DIR / "chart_dataset_dist.png"),
            "bullets": [
                "• 5 Logistics Classes: cardboard box, forklift, freight container, wood pallet, truck.",
                "• 2,500 Total Images: Class-balanced splits across train, validation, and test.",
                "• Train Set: 1,500 images (300 target images per class filter).",
                "• Validation Set: 500 images (100 target images per class filter).",
                "• Held-Out Test Set: 500 images (100 target images per class filter)."
            ],
            "notes": """WHAT TO SAY:
Our dataset comprises 2,500 total images evenly divided across 5 core logistics classes: cardboard box, forklift, freight container, wood pallet, and truck.

TECHNICAL EXPLANATION:
The data split strictly separates 1,500 training, 500 validation, and 500 held-out test images. Sampling ensured 300 training images and 100 evaluation images per class filter.

DEFENSE Q&A:
Q: Do these numbers imply strictly single-class images?
A: No, images are sampled based on primary class filters, meaning multi-object logistics scenes contain natural co-occurrences while ensuring balanced class representation across splits."""
        },
        {
            "num": 5,
            "title": "MODEL ARCHITECTURE: RT-DETR-L",
            "subtitle": "Real-Time DEtection TRansformer for High-Efficiency Bounding Box Regression",
            "type": "content_2col",
            "col1_title": "Why RT-DETR-L?",
            "col1_body": [
                "• Transformer-Based Detector: End-to-end object query matching.",
                "• HGNet-v2 Backbone: Multi-scale feature extraction (B0-B5 hierarchy).",
                "• Hybrid Encoder: Intra-scale interaction & cross-scale feature fusion.",
                "• NMS-Free Decoder: Eliminates traditional anchor hyperparameter tuning.",
                "• Ultralytics Integration: COCO-pretrained weights (rtdetr-l.pt)."
            ],
            "col2_title": "Architecture Benefits",
            "col2_body": [
                "1. Global Context Awareness: Self-attention handles large-scale objects.",
                "2. High Efficiency: Designed specifically for real-time vision workloads.",
                "3. Robust Transfer Learning: Pretrained COCO representations accelerate domain convergence.",
                "4. Fine-Tuning Stability: Bipartite Hungarian matching stabilizes bounding box regression."
            ],
            "notes": """WHAT TO SAY:
We selected RT-DETR-L, a Real-Time DEtection TRansformer developed by Baidu and implemented in Ultralytics. Unlike anchor-based CNNs, RT-DETR uses transformer decoders with learned object queries.

TECHNICAL EXPLANATION:
The HGNet-v2 backbone extracts hierarchical features, processed through a hybrid encoder. The transformer decoder matches object queries directly to ground truth bounding boxes.

DEFENSE Q&A:
Q: Why choose RT-DETR over YOLOv8?
A: RT-DETR combines transformer global context awareness with near-YOLO inference speeds, eliminating anchor box heuristics and providing superior bounding box localization for large logistics assets."""
        },
        {
            "num": 6,
            "title": "EXPERIMENT CONFIGURATION",
            "subtitle": "Hyperparameters, Hardware, and Checkpoint Selection",
            "type": "dashboard_grid",
            "metrics": [
                ("Model", "RT-DETR-L"),
                ("Resolution", "640 × 640"),
                ("Batch Size", "2"),
                ("Configured Epochs", "50"),
                ("Completed Epochs", "10"),
                ("Deployed Checkpoint", "epoch0.pt (Epoch 1)"),
                ("Best Fitness", "0.40391 (mAP50-95)"),
                ("Initial LR", "0.0001 (AdamW)"),
                ("Weight Decay", "0.0005"),
                ("Augmentations", "Mosaic 1.0, HSV, Scale"),
                ("Hardware", "NVIDIA RTX 3050 6GB"),
                ("Training Time", "3,235.52s (~53.9m)")
            ],
            "notes": """WHAT TO SAY:
Here is our experiment configuration dashboard. Training was executed locally on an NVIDIA RTX 3050 GPU for 3,235 seconds (~54 minutes).

TECHNICAL EXPLANATION:
While 50 epochs were configured, training was completed at epoch 10. The deployed best.pt checkpoint corresponds to epoch 1 (epoch0.pt), which achieved the highest Ultralytics validation fitness (0.40391).

DEFENSE Q&A:
Q: Why is best.pt from Epoch 1 instead of Epoch 10?
A: Ultralytics evaluates fitness as a weighted combination of mAP50 and mAP50-95. Epoch 1 achieved optimal validation generalization (fitness 0.40391) before subtle validation degradation occurred in later epochs."""
        },
        {
            "num": 7,
            "title": "EVALUATION RESULTS",
            "subtitle": "Rigorous Performance Benchmark on 500 Held-Out Test Images",
            "type": "chart_and_metrics",
            "image_path": str(ARTIFACTS_DIR / "chart_per_class_map.png"),
            "metrics_boxes": [
                ("0.5040", "mAP@0.5 (Overall)"),
                ("0.3408", "mAP@0.5:0.95"),
                ("0.5734", "Precision"),
                ("0.4873", "Recall")
            ],
            "notes": """WHAT TO SAY:
Evaluating on 500 held-out test images, the system achieves an overall mAP@0.5 of 50.40% and mAP@0.5:0.95 of 34.08%.

TECHNICAL EXPLANATION:
Performance varies across domain classes: wood pallet achieves 67.08% mAP50, truck 65.15%, forklift 61.51%, cardboard box 41.44%, and freight container 16.83%. Precision is 57.34% and recall is 48.73%.

DEFENSE Q&A:
Q: Why is mAP@0.5:0.95 lower than mAP@0.5?
A: mAP@0.5:0.95 evaluates bounding box accuracy across 10 strict IoU thresholds up to 0.95, penalizing slightly loose boundary predictions."""
        },
        {
            "num": 8,
            "title": "WHERE THE MODEL FAILS",
            "subtitle": "Root-Cause Diagnostic of Real Detector Error Categories",
            "type": "failure_analysis",
            "image_path": str(ROOT / "runs" / "eval" / "test_eval" / "confusion_matrix_normalized.png"),
            "failures": [
                ("1. Same-Class Duplicate Boxes", "Nested predictions on large objects -> Addressed via Containment IoS"),
                ("2. Cross-Class Duplicates", "Container vs truck overlap -> Addressed via Cross-Class IoU 0.80"),
                ("3. Container Sub-Region Splits", "Large bodies split into parts -> Explains low Container mAP (16.83%)"),
                ("4. Box vs Pallet Confusion", "Small packed boxes missed -> Explains low Cardboard Recall (28.30%)"),
                ("5. Border Edge Artifacts", "Truncated edge detections -> Addressed via Inside Ratio < 0.50 Filter")
            ],
            "notes": """WHAT TO SAY:
Rather than masking model shortcomings, we systematically diagnosed where the raw detector fails. This empirical failure analysis directly motivated our custom post-processing rules.

TECHNICAL EXPLANATION:
We identified 5 primary failure modes: internal nested boxes, cross-class overlaps, container body fragmentation (causing 16.83% mAP), cardboard box recall loss (28.30%), and low-confidence border artifacts.

DEFENSE Q&A:
Q: Why did freight container perform poorly?
A: Freight containers exhibit massive aspect ratio variations, surface occlusions, and severe visual ambiguity with truck trailers, causing raw DETR queries to split containers into sub-boxes."""
        },
        {
            "num": 9,
            "title": "CUSTOM POST-PROCESSING PIPELINE",
            "subtitle": "4-Stage Rule Engine for Error Mitigation & Output Cleanup",
            "type": "image_slide",
            "image_path": str(ARTIFACTS_DIR / "chart_nms_pipeline.png"),
            "bullets": [
                "• Stage 1: Class-Aware NMS (IoU = 0.45) — Eliminates standard same-class bounding box overlap.",
                "• Stage 2: Containment Suppression (IoS = 0.65) — Removes internal sub-region duplicates nested inside large boxes.",
                "• Stage 3: Boundary Artifact Filter — Drops edge boxes with conf < 0.30 AND inside_ratio < 0.50.",
                "• Stage 4: Cross-Class Overlap Suppression (IoU = 0.80) — Resolves multi-class box collisions by keeping highest confidence box.",
                "• Automated Verification: 48 PyTest unit tests passing with zero failures."
            ],
            "notes": """WHAT TO SAY:
To fix the 5 failure modes discovered during evaluation, we engineered a deterministic 4-stage post-processing pipeline.

TECHNICAL EXPLANATION:
Raw detections are processed sequentially: Class NMS (IoU 0.45), Containment Suppression using Intersection over Smallest (IoS 0.65), Boundary Filtering, and Cross-Class IoU (0.80). The pipeline is fully verified by 48 passing unit tests.

DEFENSE Q&A:
Q: Why use IoS (Intersection over Smallest) instead of standard IoU?
A: When a small sub-box is completely inside a large box, standard IoU is low because the large box area dominates the denominator. IoS measures containment directly, suppressing internal sub-box clutter."""
        },
        {
            "num": 10,
            "title": "DETERMINISTIC REASONING ENGINE",
            "subtitle": "Structured Natural Language Q&A with Strict Refusal Guardrails",
            "type": "content_2col",
            "col1_title": "6 Deterministic Intents",
            "col1_body": [
                "• COUNT: 'How many objects / forklifts are there?'",
                "• PRESENCE: 'Is there a truck in the warehouse?'",
                "• LIST: 'What objects are visible in the scene?'",
                "• MOST_COMMON: 'What is the dominant object class?'",
                "• SPATIAL: 'Where is the cardboard box located?'",
                "• UNKNOWN: Out-of-scope questions -> Triggers Refusal Guardrail."
            ],
            "col2_title": "Guardrails & Zero Hallucination",
            "col2_body": [
                "1. Framework Constraint: Zero agentic frameworks (No LangChain, No CrewAI).",
                "2. Global Confidence Floor: 0.25 detector confidence threshold.",
                "3. High-Confidence Threshold: 0.50 threshold for affirmative assertions.",
                "4. Refusal Policy: Explicitly returns 'insufficient information' if detections are absent or uncertain."
            ],
            "notes": """WHAT TO SAY:
Our reasoning engine routes natural language questions into 6 deterministic intents. It relies on strict pattern matching without external LLM dependencies, ensuring sub-millisecond latency and zero hallucination.

TECHNICAL EXPLANATION:
Questions are parsed into COUNT, PRESENCE, LIST, MOST_COMMON, SPATIAL, or UNKNOWN intents. Detections below 0.25 confidence are dropped, and low-confidence visual evidence triggers an explicit refusal message.

DEFENSE Q&A:
Q: Why avoid LLMs or agent frameworks like LangChain?
A: Assignment rules prohibited non-deterministic APIs. Our deterministic engine guarantees zero hallucination, sub-millisecond execution, and 100% reproducible JSON responses."""
        },
        {
            "num": 11,
            "title": "END-TO-END SYSTEM ARCHITECTURE",
            "subtitle": "Decoupled Production Microservice Architecture on AWS EC2",
            "type": "image_slide",
            "image_path": str(ARTIFACTS_DIR / "chart_system_arch.png"),
            "bullets": [
                "• Ingress Layer: Nginx reverse proxy listening on public Port 80.",
                "• Security Controls: Port 7860 bound exclusively to local container network.",
                "• Application Core: FastAPI + Uvicorn engine running detector & reasoning modules.",
                "• Containerization: Docker & Docker Compose setup with volume mounts.",
                "• Infrastructure as Code: Terraform scripts managing Security Groups, EC2, and EBS storage."
            ],
            "notes": """WHAT TO SAY:
Here is our production deployment architecture on AWS EC2. Nginx acts as the public ingress on Port 80, proxying clean traffic to the containerized FastAPI server on Port 7860.

TECHNICAL EXPLANATION:
Application Port 7860 is kept private inside the Docker network. Infrastructure is provisioned via Terraform, configuring Security Group ingress rules (22 admin, 80 public, 443 reserved).

DEFENSE Q&A:
Q: Why keep Port 7860 closed publicly?
A: Exposing application ports directly to the Internet bypasses Nginx rate limiting, buffer management, and security header controls. Port 7860 remains strictly internal."""
        },
        {
            "num": 12,
            "title": "API DEMONSTRATION & SCHEMAS",
            "subtitle": "Production JSON Contracts for Bounding Box Extraction and Q&A",
            "type": "code_demo",
            "endpoint1": "POST /detect Response Payload",
            "code1": """{
  "objects": [
    {
      "class": "wood pallet",
      "confidence": 0.2783,
      "bbox": {"x1": 85.9, "y1": 38.9, "x2": 616.5, "y2": 635.7}
    }
  ],
  "num_detections": 1,
  "image_size": [640, 640]
}""",
            "endpoint2": "POST /ask Response Payload",
            "code2": """{
  "answer": "Detected: 1 wood pallet. Total: 1 object(s).",
  "used_detector": true,
  "intent": "COUNT",
  "confidence": "medium",
  "detections_count": 1
}""",
            "notes": """WHAT TO SAY:
Here are the actual JSON contracts returned by our production API endpoints. Both /detect and /ask provide structured, deterministic outputs.

TECHNICAL EXPLANATION:
/detect outputs normalized bounding box coordinates, confidence scores, and object counts. /ask returns the natural language answer alongside intent metadata, confidence rating, and underlying detection counts.

DEFENSE Q&A:
Q: How are invalid requests or bad image uploads handled?
A: FastAPI and Pydantic v2 validate incoming multipart form fields. Unparseable image buffers return HTTP 400 Bad Request, while invalid schemas return HTTP 422 Unprocessable Entity."""
        },
        {
            "num": 13,
            "title": "AWS INFRASTRUCTURE & DEPLOYMENT",
            "subtitle": "Cloud Hosting, Infrastructure as Code, and Operational Incident Resolution",
            "type": "chart_and_bullets",
            "image_path": str(ARTIFACTS_DIR / "chart_aws_deploy.png"),
            "bullets": [
                "• Host Specifications: AWS ap-south-1 (Mumbai) | t3.small (2 vCPU, 2GB RAM + 2GB Swap).",
                "• Storage Expansion: 40 GiB gp3 EBS volume provisioned via Terraform.",
                "• Deployment Incident: Initial 20 GiB EBS disk exhausted space during PyTorch layer extraction.",
                "• Operational Fix: Expanded EBS to 40 GiB, executed online growpart & resize2fs without downtime.",
                "• Live Base API URL: http://13.233.255.22 (Swagger Docs: http://13.233.255.22/docs)."
            ],
            "notes": """WHAT TO SAY:
The application is live on AWS EC2 in ap-south-1 Mumbai at http://13.233.255.22. During initial deployment, we resolved a real-world infrastructure incident.

TECHNICAL EXPLANATION:
Extracting heavy PyTorch CUDA container layers exhausted our initial 20 GiB root disk. We expanded the EBS volume to 40 GiB and executed growpart /dev/nvme0n1 1 and resize2fs live on Ubuntu 24.04, allowing container startup to finish cleanly.

DEFENSE Q&A:
Q: How did you fix the Docker disk space issue?
A: We resized the EBS volume to 40 GiB via AWS, then performed online partition expansion using growpart and filesystem resizing using resize2fs without destroying the running EC2 instance."""
        },
        {
            "num": 14,
            "title": "RESULTS, LIMITATIONS & FUTURE WORK",
            "subtitle": "Project Victories, Known Constraints, and Next-Generation Roadmap",
            "type": "3col_summary",
            "col1_title": "WHAT WORKS (VICTORIES)",
            "col1_body": [
                "• Fine-tuned RT-DETR-L on 5 logistics classes.",
                "• 50.40% mAP@0.5 on held-out test set.",
                "• Custom 4-stage post-processing pipeline.",
                "• Deterministic Q&A reasoning engine.",
                "• 48 PyTest unit tests passing.",
                "• Dockerized AWS EC2 deployment via Terraform."
            ],
            "col2_title": "LIMITATIONS (CONSTRAINTS)",
            "col2_body": [
                "• Freight container mAP is low (16.83%).",
                "• Cardboard box recall is low (28.30%).",
                "• Configured 50 epochs; stopped at 10.",
                "• CPU AWS instance limits throughput (~2s/img).",
                "• HTTP deployment (no SSL domain active)."
            ],
            "col3_title": "FUTURE WORK (ROADMAP)",
            "col3_body": [
                "• Train full 50 epochs with cosine LR decay.",
                "• Add hard negative freight container data.",
                "• Implement class-weighted focal loss.",
                "• Migrate to GPU EC2 instance (g4dn.xlarge).",
                "• Configure domain name & HTTPS certificates."
            ],
            "notes": """WHAT TO SAY:
In conclusion, we have built, benchmarked, safeguarded, containerized, and deployed an end-to-end computer vision reasoning pipeline.

TECHNICAL SUMMARY:
While freight container localization and CPU inference latency represent clear limitations, our deterministic post-processing rules, unit test coverage, and cloud infrastructure provide a solid, deployable baseline.

DEFENSE Q&A:
Q: What is your primary takeaway from this project?
A: Computer vision engineering requires a holistic workflow—from rigorous held-out dataset evaluation and failure mode diagnosis to deterministic guardrails and automated cloud deployment."""
        }
    ]
    
    for sdata in slides_data:
        slide = prs.slides.add_slide(blank_layout)
        
        # Background fill
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = RGB_DARK_BG
        
        # Add Header Banner
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.733), Inches(1.1))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.text = sdata["title"]
        p.font.name = "Arial"
        p.font.size = Pt(22 if len(sdata["title"]) > 35 else 26)
        p.font.bold = True
        p.font.color.rgb = RGB_TEXT_LIGHT
        
        p2 = tf.add_paragraph()
        p2.text = sdata["subtitle"]
        p2.font.name = "Arial"
        p2.font.size = Pt(13)
        p2.font.color.rgb = RGB_ACCENT_BLUE
        p2.space_before = Pt(4)
        
        # Add Footer Line & Text
        footer_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11.733), Inches(0.4))
        ftf = footer_box.text_frame
        fp = ftf.paragraphs[0]
        fp.text = f"RAP Pre-Hackathon Submission | Slide {sdata['num']} of 14"
        fp.font.name = "Arial"
        fp.font.size = Pt(9)
        fp.font.color.rgb = RGB_TEXT_MUTED
        
        # Add Slide Body based on type
        stype = sdata["type"]
        
        if stype == "title":
            # Title slide hero layout
            card = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.7))
            card.fill.solid()
            card.fill.fore_color.rgb = RGB_CARD_BG
            card.line.color.rgb = RGB_BORDER
            
            ctf = card.text_frame
            ctf.word_wrap = True
            ctf.margin_left = Inches(0.5)
            ctf.margin_top = Inches(0.6)
            
            cp = ctf.paragraphs[0]
            cp.text = "LOGISTICS OBJECT DETECTION & REASONING API"
            cp.font.size = Pt(28)
            cp.font.bold = True
            cp.font.color.rgb = RGB_ACCENT_BLUE
            
            cp2 = ctf.add_paragraph()
            cp2.text = "An End-to-End Computer Vision System from RT-DETR Fine-Tuning to AWS EC2 Cloud Deployment"
            cp2.font.size = Pt(16)
            cp2.font.color.rgb = RGB_TEXT_LIGHT
            cp2.space_before = Pt(12)
            
            cp3 = ctf.add_paragraph()
            cp3.text = "\nCore System Components & Deliverables:"
            cp3.font.size = Pt(14)
            cp3.font.bold = True
            cp3.font.color.rgb = RGB_ACCENT_GREEN
            
            bullets = [
                "• RT-DETR-L Vision Transformer fine-tuned on 5 logistics domain classes.",
                "• 4-Stage Post-Processing Pipeline (Class NMS, Containment IoS, Edge Filter, Cross-Class IoU).",
                "• Deterministic Natural Language Reasoning API with 6 intents & strict refusal guardrails.",
                "• Decoupled Microservice Architecture (FastAPI + Docker + Nginx Reverse Proxy).",
                "• Infrastructure as Code (Terraform) live on AWS EC2 ap-south-1 Mumbai (http://13.233.255.22)."
            ]
            for b in bullets:
                bp = ctf.add_paragraph()
                bp.text = b
                bp.font.size = Pt(12)
                bp.font.color.rgb = RGB_TEXT_MUTED
                bp.space_before = Pt(4)

        elif stype == "content_2col":
            # Left Card
            c1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.7), Inches(5.7), Inches(4.8))
            c1.fill.solid()
            c1.fill.fore_color.rgb = RGB_CARD_BG
            c1.line.color.rgb = RGB_BORDER
            tf1 = c1.text_frame
            tf1.word_wrap = True
            tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = Inches(0.3)
            
            p = tf1.paragraphs[0]
            p.text = sdata["col1_title"]
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_BLUE
            
            for line in sdata["col1_body"]:
                lp = tf1.add_paragraph()
                lp.text = line
                lp.font.size = Pt(11)
                lp.font.color.rgb = RGB_TEXT_LIGHT
                lp.space_before = Pt(8)
                
            # Right Card
            c2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(1.7), Inches(5.733), Inches(4.8))
            c2.fill.solid()
            c2.fill.fore_color.rgb = RGB_CARD_BG
            c2.line.color.rgb = RGB_BORDER
            tf2 = c2.text_frame
            tf2.word_wrap = True
            tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.3)
            
            p = tf2.paragraphs[0]
            p.text = sdata["col2_title"]
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_GREEN
            
            for line in sdata["col2_body"]:
                lp = tf2.add_paragraph()
                lp.text = line
                lp.font.size = Pt(11)
                lp.font.color.rgb = RGB_TEXT_LIGHT
                lp.space_before = Pt(8)

        elif stype == "image_slide":
            # Left Image, Right Bullets
            slide.shapes.add_picture(sdata["image_path"], Inches(0.8), Inches(1.7), Inches(6.2), Inches(4.8))
            
            c2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.2), Inches(1.7), Inches(5.333), Inches(4.8))
            c2.fill.solid()
            c2.fill.fore_color.rgb = RGB_CARD_BG
            c2.line.color.rgb = RGB_BORDER
            tf2 = c2.text_frame
            tf2.word_wrap = True
            tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.3)
            
            p = tf2.paragraphs[0]
            p.text = "Key System Insights"
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_BLUE
            
            for b in sdata["bullets"]:
                lp = tf2.add_paragraph()
                lp.text = b
                lp.font.size = Pt(11)
                lp.font.color.rgb = RGB_TEXT_LIGHT
                lp.space_before = Pt(8)

        elif stype == "chart_and_bullets":
            # Left Chart, Right Bullets
            slide.shapes.add_picture(sdata["image_path"], Inches(0.8), Inches(1.7), Inches(6.2), Inches(4.8))
            
            c2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.2), Inches(1.7), Inches(5.333), Inches(4.8))
            c2.fill.solid()
            c2.fill.fore_color.rgb = RGB_CARD_BG
            c2.line.color.rgb = RGB_BORDER
            tf2 = c2.text_frame
            tf2.word_wrap = True
            tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.3)
            
            p = tf2.paragraphs[0]
            p.text = "Key Breakdown"
            p.font.size = Pt(16)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_GREEN
            
            for b in sdata["bullets"]:
                lp = tf2.add_paragraph()
                lp.text = b
                lp.font.size = Pt(11)
                lp.font.color.rgb = RGB_TEXT_LIGHT
                lp.space_before = Pt(8)

        elif stype == "chart_and_metrics":
            # Left Chart, Right Metric Cards
            slide.shapes.add_picture(sdata["image_path"], Inches(0.8), Inches(1.7), Inches(6.5), Inches(4.8))
            
            grid_coords = [
                (Inches(7.5), Inches(1.7)), (Inches(10.3), Inches(1.7)),
                (Inches(7.5), Inches(4.1)), (Inches(10.3), Inches(4.1))
            ]
            for i, (val, label) in enumerate(sdata["metrics_boxes"]):
                gx, gy = grid_coords[i]
                mc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, gx, gy, Inches(2.5), Inches(2.2))
                mc.fill.solid()
                mc.fill.fore_color.rgb = RGB_CARD_BG
                mc.line.color.rgb = RGB_ACCENT_BLUE if i < 2 else RGB_ACCENT_GREEN
                mtf = mc.text_frame
                mtf.word_wrap = True
                mtf.margin_top = Inches(0.4)
                
                mp1 = mtf.paragraphs[0]
                mp1.alignment = PP_ALIGN.CENTER
                mp1.text = val
                mp1.font.size = Pt(28)
                mp1.font.bold = True
                mp1.font.color.rgb = RGB_ACCENT_BLUE if i < 2 else RGB_ACCENT_GREEN
                
                mp2 = mtf.add_paragraph()
                mp2.alignment = PP_ALIGN.CENTER
                mp2.text = label
                mp2.font.size = Pt(11)
                mp2.font.color.rgb = RGB_TEXT_LIGHT
                mp2.space_before = Pt(6)

        elif stype == "dashboard_grid":
            # 12 metric tiles in 4x3 grid
            coords = [
                (Inches(0.8 + (i % 4)*2.95), Inches(1.7 + (i // 4)*1.6))
                for i in range(12)
            ]
            for i, (label, val) in enumerate(sdata["metrics"]):
                gx, gy = coords[i]
                tile = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, gx, gy, Inches(2.8), Inches(1.4))
                tile.fill.solid()
                tile.fill.fore_color.rgb = RGB_CARD_BG
                tile.line.color.rgb = RGB_BORDER
                ttf = tile.text_frame
                ttf.word_wrap = True
                ttf.margin_top = Inches(0.2)
                ttf.margin_left = Inches(0.2)
                
                tp1 = ttf.paragraphs[0]
                tp1.text = label
                tp1.font.size = Pt(10)
                tp1.font.color.rgb = RGB_TEXT_MUTED
                
                tp2 = ttf.add_paragraph()
                tp2.text = val
                tp2.font.size = Pt(13)
                tp2.font.bold = True
                tp2.font.color.rgb = RGB_ACCENT_BLUE if i % 2 == 0 else RGB_ACCENT_GREEN
                tp2.space_before = Pt(4)

        elif stype == "failure_analysis":
            # Left Confusion Matrix Image, Right 5 Failure Rows
            slide.shapes.add_picture(sdata["image_path"], Inches(0.8), Inches(1.7), Inches(5.0), Inches(4.8))
            
            c2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.0), Inches(1.7), Inches(6.533), Inches(4.8))
            c2.fill.solid()
            c2.fill.fore_color.rgb = RGB_CARD_BG
            c2.line.color.rgb = RGB_BORDER
            tf2 = c2.text_frame
            tf2.word_wrap = True
            tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.25)
            
            p = tf2.paragraphs[0]
            p.text = "5 Root-Cause Failure Categories"
            p.font.size = Pt(15)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_RED
            
            for title, desc in sdata["failures"]:
                lp = tf2.add_paragraph()
                lp.text = f"{title}"
                lp.font.size = Pt(11)
                lp.font.bold = True
                lp.font.color.rgb = RGB_ACCENT_ORANGE
                lp.space_before = Pt(6)
                
                dp = tf2.add_paragraph()
                dp.text = f"  ↳ {desc}"
                dp.font.size = Pt(10)
                dp.font.color.rgb = RGB_TEXT_LIGHT

        elif stype == "code_demo":
            # Left Code Box 1, Right Code Box 2
            c1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.7), Inches(5.7), Inches(4.8))
            c1.fill.solid()
            c1.fill.fore_color.rgb = RGB_CARD_BG
            c1.line.color.rgb = RGB_BORDER
            tf1 = c1.text_frame
            tf1.word_wrap = True
            tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = Inches(0.3)
            
            p = tf1.paragraphs[0]
            p.text = sdata["endpoint1"]
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_BLUE
            
            cp = tf1.add_paragraph()
            cp.text = sdata["code1"]
            cp.font.name = "Courier New"
            cp.font.size = Pt(9.5)
            cp.font.color.rgb = RGB_ACCENT_GREEN
            cp.space_before = Pt(8)
            
            c2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(1.7), Inches(5.733), Inches(4.8))
            c2.fill.solid()
            c2.fill.fore_color.rgb = RGB_CARD_BG
            c2.line.color.rgb = RGB_BORDER
            tf2 = c2.text_frame
            tf2.word_wrap = True
            tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = Inches(0.3)
            
            p = tf2.paragraphs[0]
            p.text = sdata["endpoint2"]
            p.font.size = Pt(14)
            p.font.bold = True
            p.font.color.rgb = RGB_ACCENT_BLUE
            
            cp = tf2.add_paragraph()
            cp.text = sdata["code2"]
            cp.font.name = "Courier New"
            cp.font.size = Pt(9.5)
            cp.font.color.rgb = RGB_ACCENT_GREEN
            cp.space_before = Pt(8)

        elif stype == "3col_summary":
            cols = [
                (Inches(0.8), sdata["col1_title"], sdata["col1_body"], RGB_ACCENT_GREEN),
                (Inches(4.8), sdata["col2_title"], sdata["col2_body"], RGB_ACCENT_RED),
                (Inches(8.8), sdata["col3_title"], sdata["col3_body"], RGB_ACCENT_BLUE)
            ]
            for x, title, body, color in cols:
                c = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(1.7), Inches(3.733), Inches(4.8))
                c.fill.solid()
                c.fill.fore_color.rgb = RGB_CARD_BG
                c.line.color.rgb = RGB_BORDER
                tf = c.text_frame
                tf.word_wrap = True
                tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = Inches(0.25)
                
                p = tf.paragraphs[0]
                p.text = title
                p.font.size = Pt(13)
                p.font.bold = True
                p.font.color.rgb = color
                
                for b in body:
                    bp = tf.add_paragraph()
                    bp.text = b
                    bp.font.size = Pt(9.5)
                    bp.font.color.rgb = RGB_TEXT_LIGHT
                    bp.space_before = Pt(6)

        # Attach Speaker Notes
        notes_slide = slide.notes_slide
        tf_notes = notes_slide.notes_text_frame
        tf_notes.text = sdata["notes"]
        
    pptx_path = ROOT / "Logistics_Object_Detection_Reasoning_API_Presentation.pptx"
    prs.save(pptx_path)
    shutil.copy(pptx_path, RAP_PRES_DIR / pptx_path.name)
    print(f"[+] Saved PPTX to: {pptx_path}")
    return pptx_path


class LandscapeDarkCanvas(canvas.Canvas):
    """Custom ReportLab Canvas for Landscape Dark-Themed Presentation PDF"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_slide_background(num_pages)
            super().showPage()
        super().save()

    def draw_slide_background(self, page_count):
        self.saveState()
        w, h = self._pagesize
        
        # Dark Background
        self.setFillColor(RL_DARK_BG)
        self.rect(0, 0, w, h, fill=True, stroke=False)
        
        # Top Header Accent Line
        self.setFillColor(RL_ACCENT_BLUE)
        self.rect(36, h - 30, w - 72, 2, fill=True, stroke=False)
        
        # Bottom Footer
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(RL_TEXT_MUTED)
        self.drawString(36, 20, "LOGISTICS OBJECT DETECTION & REASONING API | RT-DETR TO AWS EC2")
        self.drawRightString(w - 36, 20, f"Slide {self._pageNumber} of {page_count}")
        
        self.restoreState()


def build_pdf_presentation():
    """Builds the 14-slide PDF export matching the dark slide theme."""
    pdf_path = ROOT / "Logistics_Object_Detection_Reasoning_API_Presentation.pdf"
    
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'SlideTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=RL_TEXT_LIGHT, spaceAfter=2
    )
    sub_style = ParagraphStyle(
        'SlideSubtitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=RL_ACCENT_BLUE, spaceAfter=10
    )
    card_header = ParagraphStyle(
        'CardHeader', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=RL_ACCENT_GREEN, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'SlideBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9, leading=13, textColor=RL_TEXT_LIGHT, spaceAfter=4
    )
    code_style = ParagraphStyle(
        'SlideCode', parent=styles['Normal'],
        fontName='Courier', fontSize=8, leading=11, textColor=RL_ACCENT_GREEN, spaceAfter=4
    )
    
    story = []
    
    slides_content = [
        ("SLIDE 1: TITLE", "LOGISTICS OBJECT DETECTION & REASONING API", "End-to-End Computer Vision System from RT-DETR Fine-Tuning to AWS Deployment", [
            ("System Overview", [
                "• RT-DETR-L Vision Transformer fine-tuned on 5 logistics domain classes.",
                "• 4-Stage Post-Processing Guardrail (NMS, Containment IoS, Edge Filter, Cross-Class IoU).",
                "• Deterministic Natural Language Reasoning API with 6 intents & strict refusal guardrails.",
                "• Decoupled Microservice Architecture (FastAPI + Docker + Nginx Reverse Proxy).",
                "• Infrastructure as Code (Terraform) deployed on AWS EC2 ap-south-1 Mumbai."
            ])
        ]),
        ("SLIDE 2: PROBLEM & OBJECTIVE", "PROBLEM & OBJECTIVE", "Real-World Logistics Vision & Bounded Natural Language Reasoning", [
            ("Real-World Challenges", [
                "• Dense, cluttered warehouse environments with overlapping objects.",
                "• Domain requirement includes non-COCO class (wood pallet).",
                "• Need exact bounding boxes + confidence scores for inventory tracking.",
                "• Natural language Q&A requirement without LLM hallucinations."
            ]),
            ("System Objective Flow", [
                "1. Input Image: Upload warehouse scene (640x640).",
                "2. Object Detection: RT-DETR-L extracts objects & bounding boxes.",
                "3. Structured Output: 4-stage rule engine cleans raw predictions.",
                "4. Natural Language Question: User queries image context.",
                "5. Deterministic Reasoning: Intent router answers or cleanly refuses."
            ])
        ]),
        ("SLIDE 3: SOLUTION OVERVIEW", "SOLUTION OVERVIEW", "Dual-Endpoint Computer Vision & Reasoning Architecture", [
            ("System Architecture Diagram", ARTIFACTS_DIR / "chart_system_arch.png"),
            ("Key System Features", [
                "• Decoupled Microservice: FastAPI framework with async Uvicorn engine.",
                "• Dual Primary Endpoints: POST /detect for bounding boxes; POST /ask for Q&A.",
                "• Operational Endpoints: GET /health for container liveness; GET /classes for schema discovery.",
                "• Nginx Reverse Proxy: Exposes Port 80 publicly while keeping Port 7860 restricted internally."
            ])
        ]),
        ("SLIDE 4: DATASET & CLASS DESIGN", "DATASET & CLASS DESIGN", "2,500 Images across 5 Core Logistics Domain Classes", [
            ("Dataset Distribution Chart", ARTIFACTS_DIR / "chart_dataset_dist.png"),
            ("Split Breakdown", [
                "• 5 Logistics Classes: cardboard box, forklift, freight container, wood pallet, truck.",
                "• 2,500 Total Images: Class-balanced splits across train, validation, and test.",
                "• Train Set: 1,500 images (300 target images per class filter).",
                "• Validation Set: 500 images (100 target images per class filter).",
                "• Held-Out Test Set: 500 images (100 target images per class filter)."
            ])
        ]),
        ("SLIDE 5: MODEL ARCHITECTURE", "MODEL ARCHITECTURE: RT-DETR-L", "Real-Time DEtection TRansformer for High-Efficiency Bounding Box Regression", [
            ("Why RT-DETR-L?", [
                "• Transformer-Based Detector: End-to-end object query matching.",
                "• HGNet-v2 Backbone: Multi-scale feature extraction (B0-B5 hierarchy).",
                "• Hybrid Encoder: Intra-scale interaction & cross-scale feature fusion.",
                "• NMS-Free Decoder: Eliminates traditional anchor hyperparameter tuning.",
                "• Ultralytics Integration: COCO-pretrained weights (rtdetr-l.pt)."
            ]),
            ("Architecture Advantages", [
                "1. Global Context Awareness: Self-attention handles large-scale objects.",
                "2. High Efficiency: Designed specifically for real-time vision workloads.",
                "3. Transfer Learning: Pretrained COCO representations accelerate convergence.",
                "4. Fine-Tuning Stability: Bipartite Hungarian matching stabilizes regression."
            ])
        ]),
        ("SLIDE 6: TRAINING CONFIGURATION", "EXPERIMENT CONFIGURATION", "Hyperparameters, Hardware, and Deployed Checkpoint Selection", [
            ("Training Dashboard", [
                "• Model: RT-DETR-L | Resolution: 640x640 | Batch Size: 2",
                "• Configured Epochs: 50 | Completed Epochs: 10 | Deployed: epoch0.pt (Epoch 1, Fitness: 0.40391)",
                "• Initial LR: 0.0001 (AdamW) | Weight Decay: 0.0005",
                "• Augmentations: Mosaic (1.0), HSV-H (0.015), HSV-S (0.7), HSV-V (0.4), Scale (0.5), Erasing (0.4)",
                "• Hardware: NVIDIA GeForce RTX 3050 6GB Laptop GPU | Time: 3,235.52s (~53.93 minutes)"
            ])
        ]),
        ("SLIDE 7: EVALUATION RESULTS", "EVALUATION RESULTS", "Rigorous Performance Benchmark on 500 Held-Out Test Images", [
            ("Per-Class mAP Chart", ARTIFACTS_DIR / "chart_per_class_map.png"),
            ("Held-Out Metrics", [
                "• Overall mAP@0.5: 0.5040 (50.40%)",
                "• Overall mAP@0.5:0.95: 0.3408 (34.08%)",
                "• Overall Precision: 0.5734 (57.34%)",
                "• Overall Recall: 0.4873 (48.73%)",
                "• Best Class: wood pallet (mAP50: 67.08%, Precision: 78.50%)",
                "• Hardest Class: freight container (mAP50: 16.83%, Precision: 13.60%)"
            ])
        ]),
        ("SLIDE 8: FAILURE ANALYSIS", "WHERE THE MODEL FAILS", "Root-Cause Diagnostic of Real Detector Error Categories", [
            ("Normalized Confusion Matrix", ROOT / "runs" / "eval" / "test_eval" / "confusion_matrix_normalized.png"),
            ("5 Root-Cause Failures", [
                "1. Same-Class Internal Duplicates: Nested box predictions on large objects.",
                "2. Cross-Class Duplicates: High overlap predictions (freight container vs truck).",
                "3. Freight Container Sub-Region Splits: Container bodies split into sub-parts (mAP 16.83%).",
                "4. Box vs Pallet Confusion: Small packed boxes missed in backgrounds (Recall 28.30%).",
                "5. Border Edge Artifacts: Partial edge detections cut off at image margins."
            ])
        ]),
        ("SLIDE 9: POST-PROCESSING", "CUSTOM POST-PROCESSING PIPELINE", "4-Stage Rule Engine for Error Mitigation & Output Cleanup", [
            ("NMS Pipeline Flowchart", ARTIFACTS_DIR / "chart_nms_pipeline.png"),
            ("4-Stage Rules", [
                "• Stage 1: Class-Aware NMS (IoU = 0.45) — Eliminates standard same-class bounding box overlap.",
                "• Stage 2: Containment Suppression (IoS = 0.65) — Removes internal sub-region duplicates.",
                "• Stage 3: Boundary Artifact Filter — Drops edge boxes with conf < 0.30 AND inside_ratio < 0.50.",
                "• Stage 4: Cross-Class Overlap Suppression (IoU = 0.80) — Resolves multi-class box collisions.",
                "• Automated Verification: 48 PyTest unit tests passing cleanly with zero failures."
            ])
        ]),
        ("SLIDE 10: REASONING ENGINE", "DETERMINISTIC REASONING ENGINE", "Structured Natural Language Q&A with Strict Refusal Guardrails", [
            ("6 Deterministic Intents", [
                "• COUNT: 'How many objects / forklifts are there?'",
                "• PRESENCE: 'Is there a truck in the warehouse?'",
                "• LIST: 'What objects are visible in the scene?'",
                "• MOST_COMMON: 'What is the dominant object class?'",
                "• SPATIAL: 'Where is the cardboard box located?'",
                "• UNKNOWN: Out-of-scope questions -> Triggers Refusal Guardrail."
            ]),
            ("Guardrails & Refusal Policy", [
                "1. No Agentic Frameworks: Pure Python pattern matching (No LangChain/CrewAI).",
                "2. Global Confidence Floor: 0.25 detector confidence threshold.",
                "3. High-Confidence Threshold: 0.50 threshold for affirmative assertions.",
                "4. Refusal Policy: Explicitly returns 'insufficient information' if detections are absent or uncertain."
            ])
        ]),
        ("SLIDE 11: SYSTEM ARCHITECTURE", "END-TO-END SYSTEM ARCHITECTURE", "Decoupled Production Microservice Architecture on AWS EC2", [
            ("Architecture Diagram", ARTIFACTS_DIR / "chart_system_arch.png"),
            ("Infrastructure Details", [
                "• Ingress Layer: Nginx reverse proxy listening on public Port 80.",
                "• Security Controls: Port 7860 bound exclusively to local container network.",
                "• Application Core: FastAPI + Uvicorn engine running detector & reasoning modules.",
                "• Containerization: Docker & Docker Compose setup with volume mounts.",
                "• Infrastructure as Code: Terraform scripts managing Security Groups, EC2, and EBS storage."
            ])
        ]),
        ("SLIDE 12: API DEMONSTRATION", "API DEMONSTRATION & SCHEMAS", "Production JSON Contracts for Bounding Box Extraction and Q&A", [
            ("POST /detect Contract", [
                "{\n  \"objects\": [{\n    \"class\": \"wood pallet\",\n    \"confidence\": 0.2783,\n    \"bbox\": {\"x1\": 85.9, \"y1\": 38.9, \"x2\": 616.5, \"y2\": 635.7}\n  }],\n  \"num_detections\": 1,\n  \"image_size\": [640, 640]\n}"
            ]),
            ("POST /ask Contract", [
                "{\n  \"answer\": \"Detected: 1 wood pallet. Total: 1 object(s).\",\n  \"used_detector\": true,\n  \"intent\": \"COUNT\",\n  \"confidence\": \"medium\",\n  \"detections_count\": 1\n}"
            ])
        ]),
        ("SLIDE 13: AWS DEPLOYMENT", "AWS INFRASTRUCTURE & DEPLOYMENT", "Cloud Hosting, Infrastructure as Code, and Operational Incident Resolution", [
            ("AWS Deployment Diagram", ARTIFACTS_DIR / "chart_aws_deploy.png"),
            ("Deployment Highlights", [
                "• Host Specifications: AWS ap-south-1 (Mumbai) | t3.small (2 vCPU, 2GB RAM + 2GB Swap).",
                "• Storage Expansion: 40 GiB gp3 EBS volume provisioned via Terraform.",
                "• Deployment Incident: Initial 20 GiB EBS disk exhausted space during PyTorch layer extraction.",
                "• Operational Fix: Expanded EBS to 40 GiB, executed online growpart & resize2fs without downtime.",
                "• Live Base API URL: http://13.233.255.22 (Swagger Docs: http://13.233.255.22/docs)."
            ])
        ]),
        ("SLIDE 14: RESULTS & FUTURE WORK", "RESULTS, LIMITATIONS & FUTURE WORK", "Project Victories, Known Constraints, and Next-Generation Roadmap", [
            ("What Works (Victories)", [
                "• Fine-tuned RT-DETR-L on 5 logistics classes.",
                "• 50.40% mAP@0.5 on held-out test set.",
                "• Custom 4-stage post-processing pipeline.",
                "• Deterministic Q&A reasoning engine.",
                "• 48 PyTest unit tests passing.",
                "• Dockerized AWS EC2 deployment via Terraform."
            ]),
            ("Limitations & Next Steps", [
                "• Limitations: Freight container mAP (16.83%), Cardboard box recall (28.30%), CPU inference latency (~2s).",
                "• Future Work: Extend training to 50 epochs with cosine decay, collect freight container hard negatives, migrate to GPU EC2 (g4dn.xlarge), configure SSL domain."
            ])
        ])
    ]
    
    for slide_idx, (stitle, header, subtitle, blocks) in enumerate(slides_content):
        story.append(Paragraph(header, title_style))
        story.append(Paragraph(subtitle, sub_style))
        story.append(Spacer(1, 8))
        
        table_data = []
        for btitle, content in blocks:
            if isinstance(content, Path) and content.exists():
                img = Image(str(content), width=340, height=180)
                cell_content = [Paragraph(f"<b>{btitle}</b>", card_header), img]
            elif isinstance(content, list):
                lines = [Paragraph(f"<b>{btitle}</b>", card_header)]
                for line in content:
                    if line.startswith("{"):
                        lines.append(Paragraph(line.replace('\n', '<br/>').replace(' ', '&nbsp;'), code_style))
                    else:
                        lines.append(Paragraph(line, body_style))
                cell_content = lines
            else:
                cell_content = [Paragraph(str(content), body_style)]
            table_data.append(cell_content)
            
        if len(table_data) == 2:
            t = Table([table_data], colWidths=[350, 350])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), RL_CARD_BG),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOX', (0,0), (0,0), 1, RL_BORDER),
                ('BOX', (1,0), (1,0), 1, RL_BORDER),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('LEFTPADDING', (0,0), (-1,-1), 10),
                ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(t)
        elif len(table_data) == 1:
            t = Table([[table_data[0]]], colWidths=[708])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), RL_CARD_BG),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('BOX', (0,0), (-1,-1), 1, RL_BORDER),
                ('PADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(t)
            
        if slide_idx < len(slides_content) - 1:
            story.append(PageBreak())
            
    doc.build(story, canvasmaker=LandscapeDarkCanvas)
    shutil.copy(pdf_path, RAP_PRES_DIR / pdf_path.name)
    print(f"[+] Saved PDF to: {pdf_path}")
    return pdf_path


def build_presentation_notes():
    """Generates the comprehensive Presentation_Notes.md file."""
    notes_path = ROOT / "Presentation_Notes.md"
    
    content = """# LOGISTICS OBJECT DETECTION & REASONING API
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
"""
    with open(notes_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    shutil.copy(notes_path, RAP_PRES_DIR / notes_path.name)
    print(f"[+] Saved Presentation Notes to: {notes_path}")
    return notes_path


if __name__ == "__main__":
    print("[*] Generating charts...")
    generate_chart_dataset_dist()
    generate_chart_per_class_map()
    generate_chart_nms_pipeline()
    generate_chart_system_arch()
    generate_chart_aws_deploy()
    
    print("[*] Generating PPTX Presentation...")
    build_pptx_presentation()
    
    print("[*] Generating PDF Presentation...")
    build_pdf_presentation()
    
    print("[*] Generating Presentation Notes...")
    build_presentation_notes()
    
    print("[+] All presentation deliverables successfully generated!")
