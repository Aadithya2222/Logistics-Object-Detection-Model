"""
scripts/generate_rap_folder.py

Generates all required deliverables inside the RAP/ directory for submission:
1. RAP/API Usage Instructions/
2. RAP/Demo Video/
3. RAP/Deployment/
4. RAP/GitHub Repository/
5. RAP/Memo/
6. RAP/Model Weights/
7. RAP/Presentation/
8. RAP/System Design/
"""

import os
import shutil
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

ROOT = Path(__file__).parent.parent
RAP_DIR = ROOT / "RAP"

PRIMARY = colors.HexColor("#0f172a")     # Slate 900
ACCENT = colors.HexColor("#0284c7")      # Sky 600
TEXT_DARK = colors.HexColor("#1e293b")   # Slate 800
BG_LIGHT = colors.HexColor("#f8fafc")    # Slate 50
BORDER_COLOR = colors.HexColor("#cbd5e1")


class PageNumCanvas(canvas.Canvas):
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
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        
        w = self._pagesize[0]
        h = self._pagesize[1]
        
        # Header line
        self.line(36, h - 36, w - 36, h - 36)
        self.drawString(36, h - 28, "RAP SUBMISSION DELIVERABLE | RT-DETR LOGISTICS VISION & REASONING")
        
        # Footer line
        self.line(36, 36, w - 36, 36)
        self.setFont("Helvetica", 8)
        self.drawString(36, 24, "Logistics Object Detection & Deterministic Reasoning API")
        self.drawRightString(w - 36, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


# Helper styles
def get_pdf_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=16, leading=19, textColor=PRIMARY, spaceAfter=2
    )
    sub_style = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=ACCENT, spaceAfter=6
    )
    h1_style = ParagraphStyle(
        'H1', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=PRIMARY, spaceBefore=8, spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8.2, leading=11, textColor=TEXT_DARK, spaceAfter=4, alignment=TA_JUSTIFY
    )
    code_style = ParagraphStyle(
        'Code', parent=styles['Normal'],
        fontName='Courier', fontSize=7.2, leading=9.5, textColor=PRIMARY,
        backColor=BG_LIGHT, borderColor=BORDER_COLOR, borderWidth=0.5, borderPadding=4, spaceBefore=3, spaceAfter=4
    )
    table_head = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.white, alignment=TA_CENTER)
    table_cell = ParagraphStyle('TC', parent=styles['Normal'], fontName='Helvetica', fontSize=7.2, leading=9, textColor=TEXT_DARK, alignment=TA_CENTER)
    table_cell_l = ParagraphStyle('TCL', parent=table_cell, alignment=TA_LEFT)
    return title_style, sub_style, h1_style, body_style, code_style, table_head, table_cell, table_cell_l


# ── 1. API Usage Instructions PDF ─────────────────────────────────────────────
def generate_api_instructions_pdf():
    out_pdf = RAP_DIR / "API Usage Instructions" / "API_Usage_Instructions.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    story = []

    story.append(Paragraph("API Usage & Integration Guide", title_s))
    story.append(Paragraph("LOGISTICS OBJECT DETECTION & REASONING REST API", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=6))

    story.append(Paragraph("1. Base URLs & Swagger Documentation", h1_s))
    story.append(Paragraph(
        "• <b>Live Cloudflare Tunnel Base URL:</b> <code>https://prices-debug-match-twist.trycloudflare.com/</code><br/>"
        "• <b>Interactive Swagger UI Console:</b> <code>https://prices-debug-match-twist.trycloudflare.com/docs</code><br/>"
        "• <b>Local Server Fallback:</b> <code>http://127.0.0.1:8000</code>",
        body_s
    ))

    story.append(Paragraph("2. Endpoint Summary Table", h1_s))
    ep_data = [
        [Paragraph("Endpoint", th_s), Paragraph("HTTP Method", th_s), Paragraph("Content-Type", th_s), Paragraph("Description", th_s)],
        [Paragraph("<code>/detect</code>", tcl_s), Paragraph("POST", tc_s), Paragraph("multipart/form-data", tc_s), Paragraph("Returns bounding boxes, class names, and confidence scores.", tcl_s)],
        [Paragraph("<code>/ask</code>", tcl_s), Paragraph("POST", tc_s), Paragraph("multipart/form-data", tc_s), Paragraph("Natural language question answering with confidence guardrail.", tcl_s)],
        [Paragraph("<code>/health</code>", tcl_s), Paragraph("GET", tc_s), Paragraph("application/json", tc_s), Paragraph("Liveness probe returning server status.", tcl_s)],
        [Paragraph("<code>/classes</code>", tcl_s), Paragraph("GET", tc_s), Paragraph("application/json", tc_s), Paragraph("Returns the 5 supported industrial object classes.", tcl_s)],
    ]
    ep_table = Table(ep_data, colWidths=[70, 70, 110, 290])
    ep_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(ep_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("3. Detection Endpoint (POST /detect)", h1_s))
    story.append(Paragraph(
        "<b>cURL Example:</b><br/>"
        "<code>curl -X POST \"https://prices-debug-match-twist.trycloudflare.com/detect\" \\\n"
        "  -H \"Accept: application/json\" \\\n"
        "  -F \"file=@warehouse_photo.jpg\"</code>",
        code_s
    ))
    story.append(Paragraph(
        "<b>Sample Response Payload (200 OK):</b><br/>"
        "<code>{\n"
        "  \"objects\": [\n"
        "    {\n"
        "      \"class\": \"freight container\",\n"
        "      \"confidence\": 0.884,\n"
        "      \"bbox\": { \"x1\": 83.64, \"y1\": 22.29, \"x2\": 587.44, \"y2\": 601.26 }\n"
        "    }\n"
        "  ],\n"
        "  \"num_detections\": 1,\n"
        "  \"image_size\": [640, 640]\n"
        "}</code>",
        code_s
    ))

    story.append(Paragraph("4. Reasoning & Question Endpoint (POST /ask)", h1_s))
    story.append(Paragraph(
        "<b>cURL Example:</b><br/>"
        "<code>curl -X POST \"https://prices-debug-match-twist.trycloudflare.com/ask\" \\\n"
        "  -H \"Accept: application/json\" \\\n"
        "  -F \"file=@warehouse_photo.jpg\" \\\n"
        "  -F \"question=How many freight containers are in this image?\"</code>",
        code_s
    ))
    story.append(Paragraph(
        "<b>Sample Response Payload (High Confidence Answer):</b><br/>"
        "<code>{\n"
        "  \"question\": \"How many freight containers are in this image?\",\n"
        "  \"intent\": \"COUNT\",\n"
        "  \"answer\": \"There are 2 freight containers visible.\",\n"
        "  \"confidence\": \"high\",\n"
        "  \"used_detector\": true\n"
        "}</code>",
        code_s
    ))

    story.append(Paragraph("5. Python Integration Example", h1_s))
    py_code = (
        "import requests\n\n"
        "url = 'https://prices-debug-match-twist.trycloudflare.com/ask'\n"
        "files = {'file': open('warehouse.jpg', 'rb')}\n"
        "data = {'question': 'Is there a forklift near the container?'}\n"
        "response = requests.post(url, files=files, data=data)\n"
        "print(response.json())"
    )
    story.append(Paragraph(f"<code>{py_code}</code>", code_s))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated API Usage Instructions PDF.")


# ── 2. Deployment Guide PDF ───────────────────────────────────────────────────
def generate_deployment_pdf():
    out_pdf = RAP_DIR / "Deployment" / "Deployment_Guide.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    story = []

    story.append(Paragraph("Deployment & System Architecture Guide", title_s))
    story.append(Paragraph("DOCKER, UVICORN & CLOUDFLARE TUNNEL PRODUCTION SETUP", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=6))

    story.append(Paragraph("1. System Requirements & Hardware", h1_s))
    story.append(Paragraph(
        "• <b>Operating System:</b> Linux (Ubuntu 20.04+) or Windows 11<br/>"
        "• <b>GPU Acceleration:</b> NVIDIA GPU with CUDA 11.8/12.1 (Tested on RTX 3050 6GB Laptop GPU)<br/>"
        "• <b>Python Version:</b> Python 3.10+<br/>"
        "• <b>Containerization:</b> Docker 24.0+ & Docker Compose v2",
        body_s
    ))

    story.append(Paragraph("2. Method 1: Docker Compose (Recommended)", h1_s))
    story.append(Paragraph(
        "Launch the containerized API stack with a single command:<br/>"
        "<code>git clone https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git\n"
        "cd Logistics-Object-Detection-Model\n"
        "docker compose up --build</code>",
        code_s
    ))
    story.append(Paragraph("The API service compiles weights, mounts volume paths, and exposes <code>http://localhost:8000</code>.", body_s))

    story.append(Paragraph("3. Method 2: Local Virtual Environment", h1_s))
    story.append(Paragraph(
        "<code>python -m venv .venv\n"
        ".\\.venv\\Scripts\\activate\n"
        "pip install -r requirements.txt\n"
        "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload</code>",
        code_s
    ))

    story.append(Paragraph("4. Method 3: Cloudflare HTTPS Tunnel Setup", h1_s))
    story.append(Paragraph(
        "To expose the local API to the public internet securely with SSL:<br/>"
        "<code>.\\cloudflared.exe tunnel --url http://localhost:8000</code>",
        code_s
    ))
    story.append(Paragraph("Output tunnel URL: <code>https://prices-debug-match-twist.trycloudflare.com</code>.", body_s))

    story.append(Paragraph("5. Environment Variables (.env)", h1_s))
    story.append(Paragraph(
        "<code>ROBOFLOW_API_KEY=5YSIVQsasg8jgmgPq2WV\n"
        "PORT=8000\n"
        "MODEL_PATH=weights/best.pt</code>",
        code_s
    ))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated Deployment Guide PDF.")


# ── 3. Presentation Slides PDF ────────────────────────────────────────────────
def generate_presentation_pdf():
    out_pdf = RAP_DIR / "Presentation" / "Presentation_Slides.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=landscape(letter), leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    
    # Custom landscape slide titles
    slide_title = ParagraphStyle('STitle', parent=title_s, fontSize=18, leading=22)
    slide_h1 = ParagraphStyle('SH1', parent=h1_s, fontSize=12, leading=15, spaceBefore=4, spaceAfter=3)

    story = []

    # Slide 1
    story.append(Paragraph("LogiVision: Real-Time Logistics Perception & Reasoning", slide_title))
    story.append(Paragraph("PRE-HACKATHON SCREENING PRESENTATION • TRACK: COMPUTER VISION + APPLIED ML", sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=10))
    story.append(Paragraph(
        "<b>Presenter:</b> Aadithya R | <b>Model:</b> RT-DETR-Large | <b>Framework:</b> FastAPI + Docker + Cloudflare<br/>"
        "<b>Live Demo URL:</b> <code>https://prices-debug-match-twist.trycloudflare.com</code><br/>"
        "<b>Key Innovations:</b> Non-COCO 5-class ontology, HTTP Range-request dataset streaming, 100% single-class pure dataset split, and a hand-written 3-tier confidence guardrail.",
        body_s
    ))
    story.append(PageBreak())

    # Slide 2
    story.append(Paragraph("1. Domain Selection & Non-COCO Compliance", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Industrial Domain:</b> Freight Consolidation Hubs & Warehouse Logistics.<br/>"
        "• <b>5-Class Ontology:</b> <code>cardboard box</code> (0), <code>forklift</code> (1), <code>freight container</code> (2), <code>wood pallet</code> (3), <code>truck</code> (4).<br/>"
        "• <b>Hard Constraint 3 Compliance:</b> <i>Wood pallet</i>, <i>freight container</i>, and <i>cardboard box</i> are <b>non-COCO classes</b>.<br/>"
        "• <b>Why it matters:</b> Prevents off-the-shelf COCO model evaluation and forces end-to-end domain fine-tuning.",
        body_s
    ))
    story.append(PageBreak())

    # Slide 3
    story.append(Paragraph("2. Dataset Acquisition & Mid-Project Engineering Pivot", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Selective HTTP Range Streaming:</b> Built custom engine (<code>scripts/prepare_dataset.py</code>) to read remote zip Central Directory and extract images over HTTP Range requests in ~14.5 mins.<br/>"
        "• <b>Mid-Project Pivot:</b> Initial run suffered from multi-class skew (>387 pallets vs 300 boxes) and augmented duplicate SHA256 hashes.<br/>"
        "• <b>Course Correction:</b> Enforced strict single-class purity (<code>len(classes_in_file) == 1</code>), stem deduplication, and class re-mapping. Passed all 12 checks in <code>verify_dataset.py</code> with 0 hash collisions.",
        body_s
    ))
    story.append(PageBreak())

    # Slide 4
    story.append(Paragraph("3. Model Architecture & Split Strategy", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Model Architecture:</b> RT-DETR-L (Real-Time Detection Transformer with Efficient Hybrid Encoder).<br/>"
        "• <b>Dataset Split (2,500 Images):</b><br/>"
        "  - <b>Train (60%):</b> 1,500 images (300 per class)<br/>"
        "  - <b>Validation (20%):</b> 500 images (100 per class)<br/>"
        "  - <b>Test (20% Held-Out):</b> 500 images (100 per class)<br/>"
        "• <b>Hardware:</b> NVIDIA GeForce RTX 3050 6GB Laptop GPU (~45 ms inference speed).",
        body_s
    ))
    story.append(PageBreak())

    # Slide 5
    story.append(Paragraph("4. Evaluation & Root-Cause Failure Analysis", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "<b>Five Genuine Failure Cases Diagnosed:</b><br/>"
        "1. <b>Extreme Occlusion (>70% Hidden Forklift):</b> Cross-attention decoder query failure.<br/>"
        "2. <b>Small Objects (Distant Box <15px):</b> Downsampling via P3/8 stride.<br/>"
        "3. <b>Class Confusion (Container vs. Truck Body):</b> Geometry & corrugated metal ambiguity.<br/>"
        "4. <b>Low Contrast (Unlit Pallets in Shadow):</b> Near-zero contrast against concrete.<br/>"
        "5. <b>Cluster Merging (Palletized Box Stacks):</b> Plastic wrap smoothing individual borders.",
        body_s
    ))
    story.append(PageBreak())

    # Slide 6
    story.append(Paragraph("5. Part B: Hand-Written Reasoning & Guardrails", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>No Agentic Frameworks (Hard Constraint 1):</b> Pure Python in <code>app/reasoning.py</code>.<br/>"
        "• <b>Intent Routing:</b> Non-visual queries bypass detector; visual queries (COUNT, PRESENCE, SPATIAL) invoke RT-DETR.<br/>"
        "• <b>Three-Tier Guardrail:</b> High (>=0.50), Medium (0.25-0.49), Low (<0.25).<br/>"
        "• <b>Honest Refusal Payload:</b> Outputs <i>'Insufficient information to answer confidently'</i> when confidence < 0.25.",
        body_s
    ))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated Presentation Slides PDF.")


# ── 4. System Design Overview PDF ─────────────────────────────────────────────
def generate_system_design_pdf():
    out_pdf = RAP_DIR / "System Design" / "System_Design_Overview.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    story = []

    story.append(Paragraph("System Design & Architecture Specification", title_s))
    story.append(Paragraph("END-TO-END CV + REASONING PIPELINE ARCHITECTURE", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=6))

    story.append(Paragraph("1. High-Level Architecture Diagram", h1_s))
    arch_text = (
        "+-------------------------------------------------------------------------+\n"
        "|                             CLIENT / USER                               |\n"
        "|  (HTTP Requests: Image + Natural Language Question via Web UI / cURL)   |\n"
        "+-------------------------------------------------------------------------+\n"
        "                                     |                                     \n"
        "                                     v                                     \n"
        "+-------------------------------------------------------------------------+\n"
        "|                     FASTAPI APPLICATION GATEWAY                         |\n"
        "|  - CORS & Middleware Validation                                         |\n"
        "|  - Static Assets & HTML Landing Page                                    |\n"
        "+-------------------------------------------------------------------------+\n"
        "                  |                                     |                  \n"
        "                  v (POST /detect)                      v (POST /ask)      \n"
        "+----------------------------------+  +-----------------------------------+\n"
        "|      DETECTOR INFERENCE MODULE   |  |     PART B REASONING ENGINE       |\n"
        "|  - RT-DETR-L (PyTorch / GPU)     |  |  - Intent Parser (Regex/Keywords) |\n"
        "|  - Post-processing & BBoxes      |  |  - Conditional Detector Trigger   |\n"
        "+----------------------------------+  |  - 3-Tier Confidence Guardrail    |\n"
        "                                      +-----------------------------------+"
    )
    story.append(Paragraph(f"<code>{arch_text.replace(' ', '&nbsp;').replace('\n', '<br/>')}</code>", code_s))

    story.append(Paragraph("2. Core Subsystem Responsibilities", h1_s))
    story.append(Paragraph(
        "• <b>Dataset Pipeline:</b> Range-request streaming HTTP downloader + single-class deduplication filter.<br/>"
        "• <b>Model Inference Engine:</b> RT-DETR-L Transformer with AIFI (Intra-Scale Feature Interaction) and CCFM (Cross-Scale Feature Fusion).<br/>"
        "• <b>Reasoning Layer:</b> Deterministic intent router handling COUNT, PRESENCE, LIST, SPATIAL, and MOST_COMMON queries.<br/>"
        "• <b>Guardrail Enforcement:</b> Prevents hallucination by truncating low-confidence detections (<0.25).",
        body_s
    ))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated System Design PDF.")


# ── Copy & Populate Markdown Deliverables ──────────────────────────────────────
def populate_all_folders():
    # 1. API Usage Instructions
    (RAP_DIR / "API Usage Instructions" / "API_Usage_Instructions.md").write_text(
        "# API Usage Instructions\n\n"
        "## Base URLs\n"
        "- **Live Cloudflare Tunnel:** `https://prices-debug-match-twist.trycloudflare.com/`\n"
        "- **Swagger UI:** `https://prices-debug-match-twist.trycloudflare.com/docs`\n\n"
        "## Quick Examples\n"
        "```bash\n"
        "# 1. Detect objects\n"
        "curl -X POST \"https://prices-debug-match-twist.trycloudflare.com/detect\" \\\n"
        "  -F \"file=@photo.jpg\"\n\n"
        "# 2. Ask question\n"
        "curl -X POST \"https://prices-debug-match-twist.trycloudflare.com/ask\" \\\n"
        "  -F \"file=@photo.jpg\" \\\n"
        "  -F \"question=How many forklifts are visible?\"\n"
        "```\n",
        encoding="utf-8"
    )

    # 2. Demo Video
    (RAP_DIR / "Demo Video" / "DEMO_VIDEO_INFO.md").write_text(
        "# Demo Video Walkthrough & Presentation Script\n\n"
        "## Live Interactive Console\n"
        "Visit the live web app directly: https://prices-debug-match-twist.trycloudflare.com/\n\n"
        "## Video Script Highlights (3 Minutes)\n"
        "1. **0:00 - 0:45**: Introduction & Problem Statement (Non-COCO 5-class warehouse ontology).\n"
        "2. **0:45 - 1:30**: HTTP Range-request dataset streaming & single-class split pivot.\n"
        "3. **1:30 - 2:15**: RT-DETR-L model performance & 5 failure cases root-cause analysis.\n"
        "4. **2:15 - 3:00**: Part B Reasoning Layer demo & Confidence Guardrail refusal payload.\n",
        encoding="utf-8"
    )
    (RAP_DIR / "Demo Video" / "VIDEO_SCRIPT.txt").write_text(
        "LogiVision System Presentation Script\n"
        "====================================\n\n"
        "Welcome judges! Today I am presenting LogiVision - a Real-Time Logistics Object Detection\n"
        "and Reasoning API built using RT-DETR-Large...\n",
        encoding="utf-8"
    )

    # 3. Deployment
    (RAP_DIR / "Deployment" / "Deployment_Guide.md").write_text(
        "# Deployment Guide\n\n"
        "## Docker Compose (Recommended)\n"
        "```bash\n"
        "docker compose up --build\n"
        "```\n"
        "Access locally at http://localhost:8000\n",
        encoding="utf-8"
    )
    shutil.copy(ROOT / "docker-compose.yml", RAP_DIR / "Deployment" / "docker-compose.yml")

    # 4. GitHub Repository
    (RAP_DIR / "GitHub Repository" / "GitHub_Repository_Info.md").write_text(
        "# GitHub Repository Information\n\n"
        "- **Repository URL:** https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git\n"
        "- **Branch:** `main`\n"
        "- **Author:** Aadithya R\n",
        encoding="utf-8"
    )
    (RAP_DIR / "GitHub Repository" / "REPOSITORY_LINK.txt").write_text(
        "https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git\n",
        encoding="utf-8"
    )

    # 5. Memo
    if (ROOT / "docs" / "memo.pdf").exists():
        shutil.copy(ROOT / "docs" / "memo.pdf", RAP_DIR / "Memo" / "memo.pdf")
    if (ROOT / "docs" / "MEMO.md").exists():
        shutil.copy(ROOT / "docs" / "MEMO.md", RAP_DIR / "Memo" / "MEMO.md")

    # 6. Model Weights
    (RAP_DIR / "Model Weights" / "MODEL_WEIGHTS_INFO.md").write_text(
        "# Model Weights Information\n\n"
        "- **File Path:** `weights/best.pt`\n"
        "- **File Size:** ~263.6 MB\n"
        "- **Architecture:** RT-DETR-Large (Ultralytics implementation)\n"
        "- **Classes:** `cardboard box`, `forklift`, `freight container`, `wood pallet`, `truck`\n\n"
        "## Python Load Snippet\n"
        "```python\n"
        "from app.detector import get_detector\n"
        "detector = get_detector()\n"
        "```\n",
        encoding="utf-8"
    )
    (RAP_DIR / "Model Weights" / "WEIGHT_DOWNLOAD_LINK.txt").write_text(
        "Model Weights relative location in workspace: weights/best.pt\n"
        "Size: 263,681,309 bytes\n",
        encoding="utf-8"
    )

    # 7. Presentation
    (RAP_DIR / "Presentation" / "PRESENTATION_DECK.md").write_text(
        "# Presentation Slide Outline\n\n"
        "## Slide 1: Title & Overview\n"
        "## Slide 2: Domain & Non-COCO Class Compliance\n"
        "## Slide 3: Dataset Acquisition & Pivot\n"
        "## Slide 4: RT-DETR Architecture & Split Strategy\n"
        "## Slide 5: Failure Cases Root Cause Analysis\n"
        "## Slide 6: Part B Reasoning & Guardrails\n",
        encoding="utf-8"
    )

    # 8. System Design
    (RAP_DIR / "System Design" / "System_Architecture.md").write_text(
        "# System Architecture Specification\n\n"
        "## Pipeline Components\n"
        "1. **Data Ingestion Engine:** Selective HTTP Range-request streaming\n"
        "2. **Detector Model:** RT-DETR-L Transformer with Hybrid Encoder\n"
        "3. **Reasoning Layer:** Intent router and 3-tier confidence guardrail\n"
        "4. **API Gateway:** FastAPI + Uvicorn + Cloudflare Tunnel\n",
        encoding="utf-8"
    )
    (RAP_DIR / "System Design" / "Dataset_Schema_and_Verification.md").write_text(
        "# Dataset Verification Report\n\n"
        "- Total Images: 2,500\n"
        "- Unique SHA256 Hashes: 2,500\n"
        "- Single-class pure split: 500 per class\n",
        encoding="utf-8"
    )


if __name__ == "__main__":
    generate_api_instructions_pdf()
    generate_deployment_pdf()
    generate_presentation_pdf()
    generate_system_design_pdf()
    populate_all_folders()
    print("All RAP deliverables successfully generated!")
