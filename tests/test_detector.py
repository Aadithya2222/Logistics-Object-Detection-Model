"""tests/test_detector.py — Tests for the RT-DETR detector wrapper and duplicate suppression."""
import math
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
def test_detection_schema_and_validity():
    """Each detection must have valid class, confidence, and bounded bbox."""
    from PIL import Image
    from app.detector import RTDETRDetector

    det = RTDETRDetector(weights=WEIGHTS)
    imgs = list(TEST_IMG_DIR.glob("*.jpg"))[:3]
    if not imgs:
        pytest.skip("No test images available")

    for img_path in imgs:
        img = Image.open(img_path).convert("RGB")
        w, h = img.width, img.height
        result = det.detect(img)

        for d in result:
            assert "class" in d
            assert "confidence" in d
            assert "bbox" in d
            
            bbox = d["bbox"]
            assert not math.isnan(d["confidence"])
            assert not math.isinf(d["confidence"])
            assert 0.0 <= d["confidence"] <= 1.0

            x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
            assert not any(math.isnan(v) or math.isinf(v) for v in (x1, y1, x2, y2))
            assert 0.0 <= x1 <= w
            assert 0.0 <= y1 <= h
            assert 0.0 <= x2 <= w
            assert 0.0 <= y2 <= h
            assert x2 > x1
            assert y2 > y1
            assert d["class"] in [
                "cardboard box", "forklift", "freight container", "wood pallet", "truck"
            ]


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_duplicate_suppression():
    """Ensure NMS suppresses duplicate overlapping bounding boxes for the same object."""
    from PIL import Image
    from app.detector import get_detector

    det = get_detector()
    test_img_path = TEST_IMG_DIR / "-1-DRY-CONTAINER-_-_png_jpg.rf.af49c95763d7179243f25c6bb47f3050.jpg"
    if not test_img_path.exists():
        pytest.skip("Specific test image not found")

    img = Image.open(test_img_path).convert("RGB")
    result = det.detect(img)

    # Calculate pairwise IoU for same-class boxes to ensure NMS suppressed extreme overlaps
    containers = [d for d in result if d["class"] == "freight container"]
    for i in range(len(containers)):
        for j in range(i + 1, len(containers)):
            b1, b2 = containers[i]["bbox"], containers[j]["bbox"]
            x1 = max(b1["x1"], b2["x1"])
            y1 = max(b1["y1"], b2["y1"])
            x2 = min(b1["x2"], b2["x2"])
            y2 = min(b1["y2"], b2["y2"])
            inter = max(0, x2 - x1) * max(0, y2 - y1)
            area1 = (b1["x2"] - b1["x1"]) * (b1["y2"] - b1["y1"])
            area2 = (b2["x2"] - b2["x1"]) * (b2["y2"] - b2["y1"])
            union = area1 + area2 - inter
            iou = inter / (union + 1e-6)
            # Pairwise IoU must be less than the NMS threshold (0.45)
            assert iou < 0.45, f"Duplicate boxes detected with IoU {iou:.3f} >= 0.45"


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detector_singleton():
    """get_detector() should return the same instance."""
    from app.detector import get_detector
    d1 = get_detector()
    d2 = get_detector()
    assert d1 is d2
