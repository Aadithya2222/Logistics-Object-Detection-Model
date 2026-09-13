"""
app/main.py

FastAPI application exposing:
  POST /detect  — run RT-DETR on uploaded image, return structured detections
  POST /ask     — run RT-DETR + deterministic reasoning to answer a question

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.detector import get_detector
from app.reasoning import answer_question
from app.schemas import AskResponse, DetectResponse, Detection, BBox
from app.utils import load_image_bytes

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
    Upload an image and receive structured bounding-box detections.

    Returns every detected object with:
    - class name
    - confidence score
    - bounding box (x1, y1, x2, y2) in pixel coordinates
    """
    # Validate content type
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Upload an image.",
        )

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        image = load_image_bytes(raw)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode image: {e}",
        )

    detector = get_detector()
    raw_detections = detector.detect(image)

    detections = [
        Detection(
            **{"class": d["class"]},
            confidence=d["confidence"],
            bbox=BBox(**d["bbox"]),
        )
        for d in raw_detections
    ]

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

    The system:
    1. Routes the question to a deterministic intent classifier.
    2. Runs RT-DETR to get structured detections.
    3. Reasons over the detections to produce a natural-language answer.
    4. Applies a confidence guardrail — returns 'low' confidence if evidence is insufficient.

    Supported question types:
    - COUNT: "How many forklifts are visible?"
    - PRESENCE: "Is there a truck?"
    - LIST: "What objects are in the image?"
    - MOST_COMMON: "What is the most common object?"
    - SPATIAL: "Is the forklift near the pallet?"
    """
    if not question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    raw = await file.read()
    if len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        image = load_image_bytes(raw)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not decode image: {e}",
        )

    # Always run detector (reasoning layer decides whether to use results)
    detector = get_detector()
    raw_detections = detector.detect(image)

    # Run reasoning
    result = answer_question(question, raw_detections)

    detections_out = [
        Detection(
            **{"class": d["class"]},
            confidence=d["confidence"],
            bbox=BBox(**d["bbox"]),
        )
        for d in raw_detections
    ] if raw_detections else None

    return AskResponse(
        answer=result["answer"],
        used_detector=result["used_detector"],
        confidence=result["confidence"],
        detections=detections_out,
        intent=result.get("intent"),
    )


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Meta"])
async def health():
    """Liveness check — confirms API is running."""
    return {"status": "ok", "version": "1.0.0"}


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
