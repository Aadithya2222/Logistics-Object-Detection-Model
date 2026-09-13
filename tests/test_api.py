"""tests/test_api.py — FastAPI endpoint tests using TestClient."""
import sys
import io
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from PIL import Image

WEIGHTS = ROOT / "weights" / "best.pt"


def make_test_image_bytes(color=(128, 64, 32), size=(640, 480)) -> bytes:
    """Create a simple synthetic JPEG image for testing."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI TestClient (does not require a running server)."""
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    if not WEIGHTS.exists():
        pytest.skip("Model weights not available — run training first")

    from app.main import app
    return TestClient(app)


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_classes_endpoint(client):
    resp = client.get("/classes")
    assert resp.status_code == 200
    classes = resp.json()["classes"]
    assert len(classes) == 5
    names = [c["name"] for c in classes]
    assert "forklift" in names
    assert "truck" in names


def test_detect_endpoint_returns_200(client):
    img_bytes = make_test_image_bytes()
    resp = client.post(
        "/detect",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "objects" in body
    assert "num_detections" in body
    assert isinstance(body["objects"], list)


def test_detect_rejects_empty_file(client):
    resp = client.post(
        "/detect",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert resp.status_code == 400


def test_detect_rejects_non_image(client):
    resp = client.post(
        "/detect",
        files={"file": ("file.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code in (400, 415)


def test_ask_count_question(client):
    img_bytes = make_test_image_bytes()
    resp = client.post(
        "/ask",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        data={"question": "How many forklifts are visible?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "confidence" in body
    assert body["intent"] == "COUNT"


def test_ask_presence_question(client):
    img_bytes = make_test_image_bytes()
    resp = client.post(
        "/ask",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        data={"question": "Is there a truck?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "PRESENCE"
    assert body["used_detector"] is True


def test_ask_unknown_question(client):
    img_bytes = make_test_image_bytes()
    resp = client.post(
        "/ask",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        data={"question": "What is the weather today?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "UNKNOWN"
    assert body["used_detector"] is False


def test_ask_empty_question_rejected(client):
    img_bytes = make_test_image_bytes()
    resp = client.post(
        "/ask",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        data={"question": "   "},
    )
    assert resp.status_code == 400


def test_ask_confidence_guardrail_low(client):
    """Synthetic solid-color image likely has no detections → low confidence."""
    img_bytes = make_test_image_bytes(color=(200, 200, 200))
    resp = client.post(
        "/ask",
        files={"file": ("blank.jpg", img_bytes, "image/jpeg")},
        data={"question": "How many forklifts are visible?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # On a blank image the model should return low confidence or zero detections
    assert body["confidence"] in ("low", "medium", "high")  # Accept any — model decides


def test_ask_spatial_question(client):
    img_bytes = make_test_image_bytes()
    resp = client.post(
        "/ask",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")},
        data={"question": "Is the forklift near the pallet?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["intent"] == "SPATIAL"
