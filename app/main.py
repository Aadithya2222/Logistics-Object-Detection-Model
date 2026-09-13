"""
app/main.py

FastAPI application exposing:
  POST /detect  — run RT-DETR on uploaded image, return structured NMS-filtered detections
  POST /ask     — run RT-DETR + deterministic reasoning to answer a question
  GET /health   — liveness probe & model status
  GET /classes  — supported logistics object categories

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

import time
import logging
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.detector import get_detector
from app.reasoning import answer_question, classify_intent
from app.schemas import AskResponse, DetectResponse, Detection, BBox
from app.utils import load_image_bytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api")

ROOT = Path(__file__).parent.parent
STATIC_DIR = ROOT / "app" / "static"
TEMPLATES_DIR = ROOT / "app" / "templates"

app = FastAPI(
    title="Logistics Object Detection & Reasoning API",
    description=(
        "RT-DETR based object detection and question answering for "
        "warehouse / logistics imagery. "
        "Classes: cardboard box, forklift, freight container, wood pallet, truck."
    ),
    version="1.0.0",
)

# Mount static files for images and assets
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Root route ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Meta"])
async def root(request: Request):
    """Root endpoint serving the high-fidelity UI landing page."""
    accept = request.headers.get("accept", "")
    if "application/json" in accept and "text/html" not in accept:
        return {
            "message": "Logistics Object Detection & Reasoning API",
            "docs": "/docs",
            "health": "/health",
            "classes": "/classes",
            "status": "online",
            "model": "RT-DETR-Large",
        }

    template_file = TEMPLATES_DIR / "index.html"
    if template_file.exists():
        return HTMLResponse(content=template_file.read_text(encoding="utf-8"), status_code=200)

    return RedirectResponse(url="/docs")


# ── /detect ───────────────────────────────────────────────────────────────────

@app.post(
    "/detect",
    response_model=DetectResponse,
    summary="Detect logistics objects in an image",
    tags=["Detection"],
)
async def detect(
    file: UploadFile = File(..., description="Image file (jpg, png, webp)"),
):
    """
    Upload an image and receive structured bounding-box detections with NMS duplicate suppression.
    """
    start_time = time.time()
    logger.info(f"POST /detect request received: filename={file.filename}, content_type={file.content_type}")

    if file.content_type and not (file.content_type.startswith("image/") or file.content_type == "application/octet-stream"):
        logger.warning(f"Unsupported content-type: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Upload an image.",
        )

    raw = await file.read()
    if len(raw) == 0:
        logger.warning("Empty file uploaded")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        image = load_image_bytes(raw)
    except Exception as e:
        logger.error(f"Image decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode image: {e}",
        )

    try:
        detector = get_detector()
        raw_detections = detector.detect(image)
    except Exception as e:
        logger.error(f"Model inference failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Object detection inference failed.",
        )

    detections = [
        Detection(
            **{"class": d["class"]},
            confidence=d["confidence"],
            bbox=BBox(**d["bbox"]),
        )
        for d in raw_detections
    ]

    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"POST /detect completed: {len(detections)} final detections in {duration_ms}ms")

    return DetectResponse(
        objects=detections,
        num_detections=len(detections),
        image_size=(image.width, image.height),
    )


# ── /ask ──────────────────────────────────────────────────────────────────────

@app.post(
    "/ask",
    response_model=AskResponse,
    summary="Answer a natural-language question about an image",
    tags=["Reasoning"],
)
async def ask(
    file: UploadFile = File(..., description="Image file"),
    question: str = Form(..., description="Natural-language question about the image"),
):
    """
    Upload an image and ask a question about its contents.
    Executes intent classification, conditional RT-DETR detection with NMS, and confidence-guarded reasoning.
    """
    start_time = time.time()
    logger.info(f"POST /ask request received: filename={file.filename}, question='{question}'")

    if not question.strip():
        logger.warning("Empty question submitted")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    intent = classify_intent(question)
    logger.info(f"Classified intent: '{intent}'")

    # If intent does not require detection (e.g. conversational/meta), skip detector
    if intent == "UNKNOWN":
        result = answer_question(question, [])
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"POST /ask completed (bypassed detector) in {duration_ms}ms")
        return AskResponse(
            answer=result["answer"],
            used_detector=False,
            confidence=result["confidence"],
            detections=None,
            intent=intent,
        )

    raw = await file.read()
    if len(raw) == 0:
        logger.warning("Empty file uploaded")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        image = load_image_bytes(raw)
    except Exception as e:
        logger.error(f"Image decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode image: {e}",
        )

    try:
        detector = get_detector()
        raw_detections = detector.detect(image)
    except Exception as e:
        logger.error(f"Model inference failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Object detection inference failed.",
        )

    # Run reasoning over final post-processed detections
    result = answer_question(question, raw_detections)

    detections_out = [
        Detection(
            **{"class": d["class"]},
            confidence=d["confidence"],
            bbox=BBox(**d["bbox"]),
        )
        for d in raw_detections
    ] if raw_detections else None

    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(f"POST /ask completed: answer='{result['answer']}', confidence={result['confidence']} in {duration_ms}ms")

    return AskResponse(
        answer=result["answer"],
        used_detector=result["used_detector"],
        confidence=result["confidence"],
        detections=detections_out,
        intent=intent,
    )


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
async def health():
    """Liveness check — confirms API is running and model weights are ready."""
    try:
        detector = get_detector()
        model_loaded = detector.model is not None
    except Exception:
        model_loaded = False

    return {
        "status": "ok" if model_loaded else "degraded",
        "version": "1.0.0",
        "model_loaded": model_loaded,
    }


@app.get("/classes", tags=["Meta"])
async def classes():
    """Return the five supported object classes."""
    return {
        "classes": [
            {"id": 0, "name": "cardboard box"},
            {"id": 1, "name": "forklift"},
            {"id": 2, "name": "freight container"},
            {"id": 3, "name": "wood pallet"},
            {"id": 4, "name": "truck"},
        ]
    }
