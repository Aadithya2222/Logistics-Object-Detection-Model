"""tests/test_detector.py — Tests for the RT-DETR detector wrapper."""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest

WEIGHTS = ROOT / "weights" / "best.pt"
TEST_IMG_DIR = ROOT / "data" / "logistics_2500" / "test" / "images"


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detector_loads():
    """Detector should load without error."""
    from app.detector import RTDETRDetector
    det = RTDETRDetector(weights=WEIGHTS)
    assert det is not None


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detector_returns_list():
    """detect() must return a list."""
    from PIL import Image
    from app.detector import RTDETRDetector

    det = RTDETRDetector(weights=WEIGHTS)
    imgs = list(TEST_IMG_DIR.glob("*.jpg"))[:1]
    if not imgs:
        pytest.skip("No test images available")

    img = Image.open(imgs[0]).convert("RGB")
    result = det.detect(img)
    assert isinstance(result, list)


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detection_schema():
    """Each detection must have class, confidence, bbox keys."""
    from PIL import Image
    from app.detector import RTDETRDetector

    det = RTDETRDetector(weights=WEIGHTS)
    imgs = list(TEST_IMG_DIR.glob("*.jpg"))[:1]
    if not imgs:
        pytest.skip("No test images available")

    img = Image.open(imgs[0]).convert("RGB")
    result = det.detect(img)

    for d in result:
        assert "class" in d
        assert "confidence" in d
        assert "bbox" in d
        assert "x1" in d["bbox"]
        assert "y1" in d["bbox"]
        assert "x2" in d["bbox"]
        assert "y2" in d["bbox"]
        assert 0.0 <= d["confidence"] <= 1.0
        assert d["class"] in [
            "cardboard box", "forklift", "freight container", "wood pallet", "truck"
        ]


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detector_singleton():
    """get_detector() should return the same instance."""
    from app.detector import get_detector
    d1 = get_detector()
    d2 = get_detector()
    assert d1 is d2
