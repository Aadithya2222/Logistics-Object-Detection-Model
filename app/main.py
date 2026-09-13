"""
app/main.py

FastAPI application exposing:
  POST /detect  — run RT-DETR on uploaded image, return structured detections
  POST /ask     — run RT-DETR + deterministic reasoning to answer a question

Run with:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse

from app.detector import get_detector
from app.reasoning import answer_question
from app.schemas import AskResponse, DetectResponse, Detection, BBox
from app.utils import load_image_bytes

app = FastAPI(
    title="Logistics Object Detection & Reasoning API",
    description=(
        "RT-DETR based object detection and question answering for "
        "warehouse / logistics imagery. "
        "Classes: cardboard box, forklift, freight container, wood pallet, truck."
    ),
    version="1.0.0",
)


# ── Root route ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Meta"])
async def root(request: Request):
    """Root endpoint welcoming visitors and directing to /docs and health check."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Logistics Object Detection & Reasoning API</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px 20px; display: flex; justify-content: center; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; max-width: 800px; width: 100%; padding: 36px; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }
    h1 { color: #38bdf8; margin-top: 0; font-size: 1.8rem; display: flex; align-items: center; gap: 10px; }
    p { color: #94a3b8; line-height: 1.6; font-size: 1.05rem; }
    .badge { display: inline-block; background: #0369a1; color: #e0f2fe; padding: 6px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; margin: 3px; }
    .badge.non-coco { background: #b45309; color: #fef3c7; }
    .btn { display: inline-block; background: #0284c7; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-right: 12px; margin-top: 15px; transition: background 0.2s; }
    .btn:hover { background: #0369a1; }
    .btn-secondary { background: #334155; }
    .btn-secondary:hover { background: #475569; }
    .section { margin-top: 28px; border-top: 1px solid #334155; padding-top: 20px; }
    code { background: #0f172a; color: #38bdf8; padding: 3px 8px; border-radius: 4px; font-size: 0.9rem; }
    pre { background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; overflow-x: auto; color: #e2e8f0; font-size: 0.88rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>📦 Logistics Object Detection & Reasoning API</h1>
    <p>Welcome! This API serves an end-to-end <strong>RT-DETR (Real-Time Detection Transformer)</strong> model fine-tuned on industrial warehouse logistics imagery, paired with a deterministic natural language reasoning engine.</p>
    
    <div>
      <a class="btn" href="/docs">🚀 Open Interactive Swagger UI</a>
      <a class="btn btn-secondary" href="/health">🩺 Health Check</a>
      <a class="btn btn-secondary" href="/classes">🏷️ Supported Classes</a>
    </div>

    <div class="section">
      <h3>🏷️ Supported Object Classes (Including 3 Non-COCO Categories)</h3>
      <span class="badge non-coco">0: cardboard box (Non-COCO)</span>
      <span class="badge">1: forklift</span>
      <span class="badge non-coco">2: freight container (Non-COCO)</span>
      <span class="badge non-coco">3: wood pallet (Non-COCO)</span>
      <span class="badge">4: truck</span>
    </div>

    <div class="section">
      <h3>📡 Quick API Test (cURL)</h3>
      <pre># Ask a natural language question about an image
curl -X POST "https://termination-consists-amazing-servers.trycloudflare.com/ask" \\
  -F "file=@warehouse_photo.jpg" \\
  -F "question=How many freight containers are in this image?"</pre>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_content, status_code=200)
    return {
        "message": "Logistics Object Detection & Reasoning API",
        "docs": "/docs",
        "health": "/health",
        "classes": "/classes",
        "status": "online",
        "model": "RT-DETR-Large",
    }


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
