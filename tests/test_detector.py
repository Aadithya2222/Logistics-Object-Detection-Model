"""tests/test_detector.py — Tests for RT-DETR detector, NMS, and IoS containment suppression."""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
import torch
from app.detector import suppress_contained_boxes, get_detector, RTDETRDetector

WEIGHTS = ROOT / "weights" / "best.pt"
TEST_IMG_DIR = ROOT / "data" / "logistics_2500" / "test" / "images"


def test_suppress_contained_boxes_unit():
    """Unit test for suppress_contained_boxes algorithm."""
    # 1. Large box + contained small box of SAME CLASS -> small box suppressed
    boxes = torch.tensor([
        [10.0, 10.0, 500.0, 500.0],  # Large box (area 240,100)
        [100.0, 100.0, 200.0, 200.0], # Small box 100% inside (area 10,000)
    ])
    scores = torch.tensor([0.90, 0.60])
    classes = torch.tensor([2, 2])  # Same class (freight container)

    keep = suppress_contained_boxes(boxes, scores, classes, containment_threshold=0.65)
    assert len(keep) == 1
    assert keep[0].item() == 0  # Only the large, higher-confidence box is retained

    # 2. Two legitimate separate same-class boxes -> both retained
    boxes_sep = torch.tensor([
        [10.0, 10.0, 100.0, 100.0],   # Box A
        [200.0, 200.0, 300.0, 300.0], # Box B (no overlap)
    ])
    scores_sep = torch.tensor([0.85, 0.80])
    classes_sep = torch.tensor([2, 2])

    keep_sep = suppress_contained_boxes(boxes_sep, scores_sep, classes_sep, containment_threshold=0.65)
    assert len(keep_sep) == 2  # Both separate boxes retained

    # 3. Different-class contained boxes -> NOT automatically suppressed
    boxes_diff = torch.tensor([
        [10.0, 10.0, 500.0, 500.0],  # Container (Class 2)
        [100.0, 100.0, 200.0, 200.0], # Cardboard box inside container (Class 0)
    ])
    scores_diff = torch.tensor([0.90, 0.70])
    classes_diff = torch.tensor([2, 0])  # Different classes!

    keep_diff = suppress_contained_boxes(boxes_diff, scores_diff, classes_diff, containment_threshold=0.65)
    assert len(keep_diff) == 2  # Different class contained box is NOT suppressed


def test_suppress_boundary_artifacts_unit():
    """Unit test for suppress_boundary_artifacts algorithm."""
    from app.detector import suppress_boundary_artifacts

    img_w, img_h = 640.0, 640.0

    # 1. Low-confidence + heavily clipped box -> SUPPRESSED
    # Raw box: [-85.0, -240.0, 115.0, 320.0], area = 200 * 560 = 112,000
    # Clipped box: [0, 0, 115, 320], area = 115 * 320 = 36,800 -> Inside Ratio = 0.328 (< 0.50)
    # Score = 0.26 (< 0.30)
    boxes = torch.tensor([
        [-85.0, -240.0, 115.0, 320.0],
    ])
    scores = torch.tensor([0.26])

    keep = suppress_boundary_artifacts(boxes, scores, img_w, img_h, conf_cutoff=0.30, inside_ratio_cutoff=0.50)
    assert len(keep) == 0, "Low-confidence heavily clipped box should be suppressed"

    # 2. Low-confidence + mostly-inside box -> RETAINED
    # Raw box: [-10.0, 100.0, 200.0, 300.0], area = 210 * 200 = 42,000
    # Clipped box: [0, 100, 200, 300], area = 200 * 200 = 40,000 -> Inside Ratio = 0.952 (>= 0.50)
    # Score = 0.26
    boxes_mostly_in = torch.tensor([
        [-10.0, 100.0, 200.0, 300.0],
    ])
    scores_mostly_in = torch.tensor([0.26])

    keep_mostly_in = suppress_boundary_artifacts(boxes_mostly_in, scores_mostly_in, img_w, img_h)
    assert len(keep_mostly_in) == 1, "Low-confidence mostly-inside box should be retained"

    # 3. High-confidence + heavily clipped box -> RETAINED
    # Raw box: [-85.0, -240.0, 115.0, 320.0], Inside Ratio = 0.328
    # Score = 0.75 (>= 0.30)
    scores_high_conf = torch.tensor([0.75])

    keep_high_conf = suppress_boundary_artifacts(boxes, scores_high_conf, img_w, img_h)
    assert len(keep_high_conf) == 1, "High-confidence heavily clipped box should be retained"

    # 4. Normal legitimate detection (fully inside) -> RETAINED
    boxes_normal = torch.tensor([
        [100.0, 100.0, 300.0, 300.0],
    ])
    scores_normal = torch.tensor([0.85])

    keep_normal = suppress_boundary_artifacts(boxes_normal, scores_normal, img_w, img_h)
    assert len(keep_normal) == 1, "Normal legitimate box should be retained"


def test_suppress_cross_class_duplicates_unit():
    """Unit test for suppress_cross_class_duplicates algorithm."""
    from app.detector import suppress_cross_class_duplicates

    # 1. Different-class identical boxes (IoU = 1.0 >= 0.80) -> lower-confidence box SUPPRESSED
    boxes_identical = torch.tensor([
        [100.0, 100.0, 400.0, 400.0],  # Box 0: forklift (Class 1)
        [100.0, 100.0, 400.0, 400.0],  # Box 1: truck (Class 4)
    ])
    scores_identical = torch.tensor([0.75, 0.25])
    classes_identical = torch.tensor([1, 4])

    keep = suppress_cross_class_duplicates(boxes_identical, scores_identical, classes_identical, iou_threshold=0.80)
    assert len(keep) == 1
    assert keep[0].item() == 0, "Lower-confidence cross-class duplicate should be suppressed"

    # 2. Different-class IoU below 0.80 -> BOTH RETAINED
    boxes_partial = torch.tensor([
        [100.0, 100.0, 300.0, 300.0],  # Box 0: Class 1 (Area 40,000)
        [200.0, 200.0, 400.0, 400.0],  # Box 1: Class 4 (Area 40,000, Inter = 100x100 = 10,000, Union = 70,000, IoU = 0.143)
    ])
    scores_partial = torch.tensor([0.75, 0.65])
    classes_partial = torch.tensor([1, 4])

    keep_partial = suppress_cross_class_duplicates(boxes_partial, scores_partial, classes_partial, iou_threshold=0.80)
    assert len(keep_partial) == 2, "Different-class boxes with IoU < 0.80 should both be retained"

    # 3. Legitimate overlapping different-class boxes (e.g. Cardboard box inside Freight container, IoU < 0.80) -> RETAINED
    boxes_contained_diff = torch.tensor([
        [10.0, 10.0, 500.0, 500.0],   # Freight container: Class 2 (Area 240,100)
        [100.0, 100.0, 200.0, 200.0],  # Cardboard box inside: Class 0 (Area 10,000, IoU = 10,000 / 240,100 = 0.0416)
    ])
    scores_contained_diff = torch.tensor([0.90, 0.70])
    classes_contained_diff = torch.tensor([2, 0])

    keep_contained_diff = suppress_cross_class_duplicates(boxes_contained_diff, scores_contained_diff, classes_contained_diff, iou_threshold=0.80)
    assert len(keep_contained_diff) == 2, "Contained box of different class (IoU < 0.80) should be retained"



@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detector_loads():
    """Detector should load without error."""
    det = RTDETRDetector(weights=WEIGHTS)
    assert det is not None


@pytest.mark.skipif(not WEIGHTS.exists(), reason="Weights not trained yet")
def test_detector_returns_list():
    """detect() must return a list."""
    from PIL import Image

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
def test_duplicate_suppression_on_test_image():
    """Ensure NMS, IoS containment, and boundary artifact suppression work together."""
    from PIL import Image
    from app.reasoning import answer_question

    det = get_detector()
    test_img_path = TEST_IMG_DIR / "-1-DRY-CONTAINER-_-_png_jpg.rf.af49c95763d7179243f25c6bb47f3050.jpg"
    if not test_img_path.exists():
        pytest.skip("Specific test image not found")

    img = Image.open(test_img_path).convert("RGB")
    result = det.detect(img)

    containers = [d for d in result if d["class"] == "freight container"]
    # Exactly 1 freight container after containment and boundary artifact suppression
    assert len(containers) == 1, f"Expected exactly 1 freight container detection, got {len(containers)}"
    
    # Check that main container (area > 200,000 px^2) is retained
    main_container = containers[0]
    area = (main_container["bbox"]["x2"] - main_container["bbox"]["x1"]) * (main_container["bbox"]["y2"] - main_container["bbox"]["y1"])
    assert area > 200000, "Main freight container was missing or incorrect!"

    # Verify that /ask COUNT reasoning uses final /detect output
    ask_result = answer_question("How many freight containers are in this image?", result)
    assert "1 freight container" in ask_result["answer"] or "one freight container" in ask_result["answer"].lower()

