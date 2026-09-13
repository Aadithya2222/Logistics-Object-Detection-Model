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
        self.drawString(36, h - 28, "RAP SUBMISSION DELIVERABLE | RT-DETR LOGISTICS VISION & REASONING API")
        
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
    out_dir = RAP_DIR / "API Usage Instructions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = out_dir / "API_Usage_Instructions.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    story = []

    story.append(Paragraph("API Usage & Integration Guide", title_s))
    story.append(Paragraph("LOGISTICS OBJECT DETECTION & REASONING REST API", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=6))

    story.append(Paragraph("1. Base URLs & Swagger Documentation", h1_s))
    story.append(Paragraph(
        "• <b>Live AWS Production Base URL:</b> <code>http://13.233.255.22</code><br/>"
        "• <b>Interactive Swagger UI Console:</b> <code>http://13.233.255.22/docs</code><br/>"
        "• <b>Local Server Fallback:</b> <code>http://localhost:7860</code>",
        body_s
    ))

    story.append(Paragraph("2. Endpoint Summary Table", h1_s))
    ep_data = [
        [Paragraph("Endpoint", th_s), Paragraph("HTTP Method", th_s), Paragraph("Content-Type", th_s), Paragraph("Description", th_s)],
        [Paragraph("<code>/detect</code>", tcl_s), Paragraph("POST", tc_s), Paragraph("multipart/form-data", tc_s), Paragraph("Returns bounding boxes, class names, and confidence scores with 4-stage post-processing guardrails.", tcl_s)],
        [Paragraph("<code>/ask</code>", tcl_s), Paragraph("POST", tc_s), Paragraph("multipart/form-data", tc_s), Paragraph("Natural language question answering with 3-tier confidence floor guardrail.", tcl_s)],
        [Paragraph("<code>/health</code>", tcl_s), Paragraph("GET", tc_s), Paragraph("application/json", tc_s), Paragraph("Liveness probe returning model load status.", tcl_s)],
        [Paragraph("<code>/classes</code>", tcl_s), Paragraph("GET", tc_s), Paragraph("application/json", tc_s), Paragraph("Returns the 5 supported industrial object categories.", tcl_s)],
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
        "<code>curl -X POST \"http://13.233.255.22/detect\" \\\n"
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
        "      \"confidence\": 0.5321,\n"
        "      \"bbox\": { \"x1\": 76.53, \"y1\": 23.41, \"x2\": 589.8, \"y2\": 597.75 }\n"
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
        "<code>curl -X POST \"http://13.233.255.22/ask\" \\\n"
        "  -H \"Accept: application/json\" \\\n"
        "  -F \"file=@warehouse_photo.jpg\" \\\n"
        "  -F \"question=How many freight containers are visible?\"</code>",
        code_s
    ))
    story.append(Paragraph(
        "<b>Sample Response Payload (High Confidence Answer):</b><br/>"
        "<code>{\n"
        "  \"answer\": \"There is 1 freight container visible.\",\n"
        "  \"used_detector\": true,\n"
        "  \"confidence\": \"high\",\n"
        "  \"detections\": [\n"
        "    {\n"
        "      \"class\": \"freight container\",\n"
        "      \"confidence\": 0.5321,\n"
        "      \"bbox\": { \"x1\": 76.53, \"y1\": 23.41, \"x2\": 589.8, \"y2\": 597.75 }\n"
        "    }\n"
        "  ],\n"
        "  \"intent\": \"COUNT\"\n"
        "}</code>",
        code_s
    ))

    story.append(Paragraph("5. Python Integration Example", h1_s))
    py_code = (
        "import requests\n\n"
        "url = 'http://13.233.255.22/ask'\n"
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
    out_dir = RAP_DIR / "Deployment"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = out_dir / "Deployment_Guide.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    story = []

    story.append(Paragraph("Deployment & System Architecture Guide", title_s))
    story.append(Paragraph("AWS EC2, TERRAFORM, DOCKER COMPOSE & NGINX SETUP", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=6))

    story.append(Paragraph("1. System Specifications & Production Environment", h1_s))
    story.append(Paragraph(
        "• <b>Host Platform:</b> AWS EC2 <code>t3.small</code> (2 vCPU, 2 GiB RAM, x86_64, Ubuntu 24.04 LTS)<br/>"
        "• <b>Root Storage:</b> 40 GiB gp3 EBS encrypted root volume<br/>"
        "• <b>Memory Safety Buffer:</b> 2 GB <code>/swapfile</code> configured on EBS<br/>"
        "• <b>Public Gateway:</b> Nginx reverse proxy on Port 80 (Internal proxy to 127.0.0.1:7860)<br/>"
        "• <b>Process Management:</b> Docker Compose with <code>restart: unless-stopped</code>",
        body_s
    ))

    story.append(Paragraph("2. Method 1: Infrastructure as Code (Terraform)", h1_s))
    story.append(Paragraph(
        "<code>cd terraform\n"
        "cp terraform.tfvars.example terraform.tfvars\n"
        "# Set admin_cidr_blocks = [\"YOUR_PUBLIC_IP/32\"]\n"
        "terraform init\n"
        "terraform apply</code>",
        code_s
    ))

    story.append(Paragraph("3. Method 2: Docker Compose (Local or Host)", h1_s))
    story.append(Paragraph(
        "<code>git clone https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git\n"
        "cd Logistics-Object-Detection-Model\n"
        "docker compose up -d --build</code>",
        code_s
    ))

    story.append(Paragraph("4. Security Group Rules", h1_s))
    story.append(Paragraph(
        "• <b>TCP 22:</b> SSH restricted to administrator IP only.<br/>"
        "• <b>TCP 80:</b> HTTP open for public web API access.<br/>"
        "• <b>TCP 443:</b> HTTPS open (Reserved for future SSL configuration).<br/>"
        "• <b>TCP 7860:</b> Isolated internally (NOT exposed publicly).",
        body_s
    ))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated Deployment Guide PDF.")


# ── 3. Presentation Slides PDF ────────────────────────────────────────────────
def generate_presentation_pdf():
    out_dir = RAP_DIR / "Presentation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = out_dir / "Presentation_Slides.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=landscape(letter), leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    
    slide_title = ParagraphStyle('STitle', parent=title_s, fontSize=18, leading=22)

    story = []

    # Slide 1
    story.append(Paragraph("Logistics Object Detection & Reasoning API", slide_title))
    story.append(Paragraph("PRE-HACKATHON SCREENING PRESENTATION • TRACK: COMPUTER VISION + APPLIED ML", sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=10))
    story.append(Paragraph(
        "<b>Presenter:</b> Aadithya R | <b>Backbone:</b> RT-DETR-Large | <b>Stack:</b> FastAPI + Docker + Terraform + AWS EC2<br/>"
        "<b>Live Production URL:</b> <code>http://13.233.255.22</code><br/>"
        "<b>Key Innovations:</b> 5-class ontology (3 non-COCO), 4-stage post-processing guardrails, deterministic intent routing, and 3-tier confidence floor.",
        body_s
    ))
    story.append(PageBreak())

    # Slide 2
    story.append(Paragraph("1. Domain & Supported Class Ontology", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Industrial Domain:</b> Warehouse Material Handling & Freight Hub Perception.<br/>"
        "• <b>5-Class Ontology:</b> <code>cardboard box</code> (0), <code>forklift</code> (1), <code>freight container</code> (2), <code>wood pallet</code> (3), <code>truck</code> (4).<br/>"
        "• <b>Non-COCO Compliance:</b> <i>Cardboard box</i>, <i>freight container</i>, and <i>wood pallet</i> are custom non-COCO classes.<br/>"
        "• <b>Operational Purpose:</b> Real-time inventory auditing, cargo volume estimation, and workplace safety monitoring.",
        body_s
    ))
    story.append(PageBreak())

    # Slide 3
    story.append(Paragraph("2. Dataset & Split Strategy", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Source:</b> Roboflow Universe Logistics Benchmark (<code>large-benchmark-datasets/logistics-sz9jr</code>).<br/>"
        "• <b>Curated Benchmark Dataset (2,500 Images):</b><br/>"
        "  - <b>Train (60%):</b> 1,500 images (300 per class)<br/>"
        "  - <b>Validation (20%):</b> 500 images (100 per class)<br/>"
        "  - <b>Test (20% Held-Out):</b> 500 images (100 per class)<br/>"
        "• <b>Programmatic Verification:</b> 12-point audit script (zero SHA256 collisions).",
        body_s
    ))
    story.append(PageBreak())

    # Slide 4
    story.append(Paragraph("3. Held-Out Test Set Evaluation Benchmark", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Overall Test Set Metrics:</b> mAP@0.5 = <b>0.5040 (50.40%)</b> | mAP@0.5:0.95 = <b>0.3408 (34.08%)</b> | Precision = <b>0.5734</b> | Recall = <b>0.4873</b><br/>"
        "• <b>Per-Class mAP@0.5 Results:</b><br/>"
        "  - <i>wood pallet:</i> 0.6708 (67.08%) | <i>truck:</i> 0.6515 (65.15%) | <i>forklift:</i> 0.6151 (61.51%)<br/>"
        "  - <i>cardboard box:</i> 0.4144 (41.44%) | <i>freight container:</i> 0.1683 (16.83%)<br/>"
        "• <b>Deployed Checkpoint:</b> <code>weights/best.pt</code> (Epoch 1 / <code>epoch0.pt</code>, best fitness 0.40391).",
        body_s
    ))
    story.append(PageBreak())

    # Slide 5
    story.append(Paragraph("4. Post-Processing & Failure Root-Cause Analysis", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "<b>4-Stage Post-Processing Pipeline:</b> Class-aware NMS (0.45) $\\rightarrow$ Same-class IoS containment (0.65) $\\rightarrow$ Cross-class high-IoU suppression (0.80) $\\rightarrow$ Boundary artifact filter.<br/><br/>"
        "<b>5 Genuine Failure Cases Diagnosed:</b><br/>"
        "1. <i>Sub-region container duplicates</i> (Mitigated via IoS containment suppression).<br/>"
        "2. <i>Cross-class prediction overlap</i> (Mitigated via cross-class IoU suppression).<br/>"
        "3. <i>Long container partitioning</i> (Active limitation; non-overlapping boxes).<br/>"
        "4. <i>Wood crate vs pallet texture ambiguity</i> (Active limitation; slatted wood features).<br/>"
        "5. <i>Low-confidence boundary artifacts</i> (Mitigated via boundary filter).",
        body_s
    ))
    story.append(PageBreak())

    # Slide 6
    story.append(Paragraph("5. Reasoning Layer, Guardrails & Production AWS Hosting", slide_title))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))
    story.append(Paragraph(
        "• <b>Deterministic Reasoning:</b> Hand-written pure Python router in <code>app/reasoning.py</code> (Zero LangChain / LLM overhead).<br/>"
        "• <b>6 Supported Intents:</b> <code>COUNT</code>, <code>PRESENCE</code>, <code>LIST</code>, <code>SPATIAL</code>, <code>MOST_COMMON</code>, <code>UNKNOWN</code>.<br/>"
        "• <b>Confidence Floor Guardrail ($0.25$):</b> Returns explicit <i>'Insufficient information to answer confidently'</i> payload when evidence is weak.<br/>"
        "• <b>Production AWS Hosting:</b> Deployed on AWS EC2 <code>t3.small</code> via Terraform, Nginx, and Docker Compose at <code>http://13.233.255.22</code>.",
        body_s
    ))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated Presentation Slides PDF.")


# ── 4. System Design Overview PDF ─────────────────────────────────────────────
def generate_system_design_pdf():
    out_dir = RAP_DIR / "System Design"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = out_dir / "System_Design_Overview.pdf"
    doc = SimpleDocTemplate(str(out_pdf), pagesize=letter, leftMargin=36, rightMargin=36, topMargin=46, bottomMargin=46)
    title_s, sub_s, h1_s, body_s, code_s, th_s, tc_s, tcl_s = get_pdf_styles()
    story = []

    story.append(Paragraph("System Design & Architecture Specification", title_s))
    story.append(Paragraph("END-TO-END CV + REASONING PIPELINE ARCHITECTURE", sub_s))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=6))

    story.append(Paragraph("1. High-Level Architecture Diagram", h1_s))
    arch_text = (
        "+-------------------------------------------------------------------------+\n"
        "|                            PUBLIC INTERNET                              |\n"
        "|                 (Client HTTP Requests: Image + Question)                |\n"
        "+-------------------------------------------------------------------------+\n"
        "                                     |                                     \n"
        "                                     v                                     \n"
        "+-------------------------------------------------------------------------+\n"
        "|                       NGINX REVERSE PROXY (:80)                         |\n"
        "|               - Proxy Pass to 127.0.0.1:7860                            |\n"
        "|               - client_max_body_size 50M                                |\n"
        "+-------------------------------------------------------------------------+\n"
        "                                     |                                     \n"
        "                                     v                                     \n"
        "+-------------------------------------------------------------------------+\n"
        "|                  FASTAPI APPLICATION CONTAINER (:7860)                  |\n"
        "|               - Uvicorn ASGI Server (restart: unless-stopped)           |\n"
        "+-------------------------------------------------------------------------+\n"
        "                  |                                     |                  \n"
        "                  v (POST /detect)                      v (POST /ask)      \n"
        "+----------------------------------+  +-----------------------------------+\n"
        "|     DETECTOR INFERENCE MODULE    |  |     PART B REASONING ENGINE       |\n"
        "|  - RT-DETR-L (PyTorch / GPU)     |  |  - Deterministic Intent Router    |\n"
        "|  - 4-Stage Post-Processing       |  |  - Conditional Detector Trigger   |\n"
        "+----------------------------------+  |  - 3-Tier Confidence Floor        |\n"
        "                                      +-----------------------------------+"
    )
    story.append(Paragraph(f"<code>{arch_text.replace(' ', '&nbsp;').replace('\n', '<br/>')}</code>", code_s))

    story.append(Paragraph("2. Core Subsystem Responsibilities", h1_s))
    story.append(Paragraph(
        "• <b>Dataset Pipeline:</b> 2,500 image benchmark dataset (1500 train, 500 val, 500 test).<br/>"
        "• <b>Model Inference Engine:</b> RT-DETR-L Transformer with 4-stage post-processing (Class-aware NMS, Same-class IoS containment, Cross-class IoU, Boundary filter).<br/>"
        "• <b>Reasoning Layer:</b> Deterministic intent router handling COUNT, PRESENCE, LIST, SPATIAL, MOST_COMMON, and UNKNOWN queries.<br/>"
        "• <b>Guardrail Enforcement:</b> Prevents hallucination by truncating low-confidence detections (<0.25).<br/>"
        "• <b>Infrastructure:</b> Managed via Terraform IaC on AWS EC2 <code>t3.small</code> with Docker Compose and Nginx.",
        body_s
    ))

    doc.build(story, canvasmaker=PageNumCanvas)
    print("Generated System Design PDF.")


# ── Copy & Populate Markdown Deliverables ──────────────────────────────────────
def populate_all_folders():
    # 1. API Usage Instructions
    out_api = RAP_DIR / "API Usage Instructions"
    out_api.mkdir(parents=True, exist_ok=True)
    (out_api / "API_Usage_Instructions.md").write_text(
        "# API Usage Instructions\n\n"
        "## Base URLs\n"
        "- **Live AWS Production Base URL:** `http://13.233.255.22`\n"
        "- **Interactive Swagger UI Console:** `http://13.233.255.22/docs`\n"
        "- **Local Docker Fallback:** `http://localhost:7860`\n\n"
        "## Endpoint Reference & cURL Examples\n\n"
        "### 1. Health Check\n"
        "```bash\n"
        "curl -X GET \"http://13.233.255.22/health\"\n"
        "```\n"
        "**Response (200 OK):**\n"
        "```json\n"
        "{\"status\": \"ok\", \"version\": \"1.0.0\", \"model_loaded\": true}\n"
        "```\n\n"
        "### 2. Supported Classes\n"
        "```bash\n"
        "curl -X GET \"http://13.233.255.22/classes\"\n"
        "```\n\n"
        "### 3. Object Detection (POST /detect)\n"
        "```bash\n"
        "curl -X POST \"http://13.233.255.22/detect\" \\\n"
        "  -F \"file=@sample.jpg\"\n"
        "```\n\n"
        "### 4. Natural Language Reasoning (POST /ask)\n"
        "```bash\n"
        "curl -X POST \"http://13.233.255.22/ask\" \\\n"
        "  -F \"file=@sample.jpg\" \\\n"
        "  -F \"question=How many freight containers are visible?\"\n"
        "```\n",
        encoding="utf-8"
    )

    # 2. Demo Video
    out_video = RAP_DIR / "Demo Video"
    out_video.mkdir(parents=True, exist_ok=True)
    (out_video / "DEMO_VIDEO_INFO.md").write_text(
        "# Demo Video Walkthrough & Presentation Script\n\n"
        "## Live Interactive Console\n"
        "Visit the live web API console directly: http://13.233.255.22/docs\n\n"
        "## Video Script Highlights (3 Minutes)\n"
        "1. **0:00 - 0:45**: Introduction & Problem Statement (Non-COCO 5-class warehouse ontology).\n"
        "2. **0:45 - 1:30**: Dataset split strategy & RT-DETR-L fine-tuning benchmark.\n"
        "3. **1:30 - 2:15**: 4-Stage post-processing guardrails & 5 failure cases root-cause analysis.\n"
        "4. **2:15 - 3:00**: Part B Reasoning Layer demo & Confidence Floor guardrail refusal payload.\n",
        encoding="utf-8"
    )
    (out_video / "VIDEO_SCRIPT.txt").write_text(
        "Logistics Object Detection & Reasoning System Script\n"
        "===================================================\n\n"
        "Welcome! Presenting an Autonomous Logistics Object Detection and Visual Reasoning API\n"
        "built using RT-DETR-Large, FastAPI, Docker, Terraform, and AWS EC2...\n",
        encoding="utf-8"
    )

    # 3. Deployment
    out_deploy = RAP_DIR / "Deployment"
    out_deploy.mkdir(parents=True, exist_ok=True)
    (out_deploy / "Deployment_Guide.md").write_text(
        "# Production Deployment Guide\n\n"
        "## AWS EC2 & Docker Compose\n"
        "Live URL: http://13.233.255.22\n\n"
        "### Local / Server Execution\n"
        "```bash\n"
        "docker compose up -d --build\n"
        "```\n"
        "Access locally at http://localhost:7860\n",
        encoding="utf-8"
    )
    if (ROOT / "docker-compose.yml").exists():
        shutil.copy(ROOT / "docker-compose.yml", out_deploy / "docker-compose.yml")

    # 4. GitHub Repository
    out_git = RAP_DIR / "GitHub Repository"
    out_git.mkdir(parents=True, exist_ok=True)
    (out_git / "GitHub_Repository_Info.md").write_text(
        "# GitHub Repository Information\n\n"
        "- **Repository URL:** https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git\n"
        "- **Branch:** `main`\n"
        "- **Author:** Aadithya R\n",
        encoding="utf-8"
    )
    (out_git / "REPOSITORY_LINK.txt").write_text(
        "https://github.com/Aadithya2222/Logistics-Object-Detection-Model.git\n",
        encoding="utf-8"
    )

    # 5. Memo
    out_memo = RAP_DIR / "Memo"
    out_memo.mkdir(parents=True, exist_ok=True)
    if (ROOT / "docs" / "memo.pdf").exists():
        shutil.copy(ROOT / "docs" / "memo.pdf", out_memo / "memo.pdf")
    if (ROOT / "docs" / "MEMO.md").exists():
        shutil.copy(ROOT / "docs" / "MEMO.md", out_memo / "MEMO.md")

    # 6. Model Weights
    out_weights = RAP_DIR / "Model Weights"
    out_weights.mkdir(parents=True, exist_ok=True)
    (out_weights / "MODEL_WEIGHTS_INFO.md").write_text(
        "# Model Weights Information\n\n"
        "- **File Path:** `weights/best.pt`\n"
        "- **Architecture:** RT-DETR-Large (Ultralytics implementation)\n"
        "- **Checkpoint Origin:** Epoch 1 (`epoch0.pt`, SHA256: `455f8478266cbd48...`)\n"
        "- **Best Fitness:** 0.40391 (based on mAP50-95)\n"
        "- **Classes:** `cardboard box`, `forklift`, `freight container`, `wood pallet`, `truck`\n\n"
        "## Python Load Snippet\n"
        "```python\n"
        "from app.detector import get_detector\n"
        "detector = get_detector()\n"
        "```\n",
        encoding="utf-8"
    )
    (out_weights / "WEIGHT_DOWNLOAD_LINK.txt").write_text(
        "Model Weights relative location in workspace: weights/best.pt\n"
        "SHA256: 455f8478266cbd4881d77a06041ec1a91726a4c2810a9cf186355fa3e0436855\n",
        encoding="utf-8"
    )

    # 7. Presentation
    out_pres = RAP_DIR / "Presentation"
    out_pres.mkdir(parents=True, exist_ok=True)
    (out_pres / "PRESENTATION_DECK.md").write_text(
        "# Presentation Slide Outline\n\n"
        "## Slide 1: Title & Overview\n"
        "## Slide 2: Domain & Non-COCO Class Ontology\n"
        "## Slide 3: Dataset & Split Strategy\n"
        "## Slide 4: Held-Out Test Set Evaluation Benchmark\n"
        "## Slide 5: Post-Processing & Failure Root Cause Analysis\n"
        "## Slide 6: Part B Reasoning, Guardrails & Production AWS Hosting\n",
        encoding="utf-8"
    )

    # 8. System Design
    out_sd = RAP_DIR / "System Design"
    out_sd.mkdir(parents=True, exist_ok=True)
    (out_sd / "System_Architecture.md").write_text(
        "# System Architecture Specification\n\n"
        "## Pipeline Components\n"
        "1. **Dataset Benchmark:** 2,500 images (1500 train, 500 val, 500 test)\n"
        "2. **Detector Model:** RT-DETR-L Transformer with 4-stage post-processing\n"
        "3. **Reasoning Layer:** Intent router and 3-tier confidence floor guardrail\n"
        "4. **Production Infrastructure:** AWS EC2 t3.small + Terraform + Docker Compose + Nginx\n",
        encoding="utf-8"
    )
    (out_sd / "Dataset_Schema_and_Verification.md").write_text(
        "# Dataset Verification Report\n\n"
        "- Total Images: 2,500\n"
        "- Unique SHA256 Hashes: 2,500\n"
        "- Balanced split: 500 images per class\n",
        encoding="utf-8"
    )


if __name__ == "__main__":
    generate_api_instructions_pdf()
    generate_deployment_pdf()
    generate_presentation_pdf()
    generate_system_design_pdf()
    populate_all_folders()
    print("All RAP deliverables successfully generated!")
