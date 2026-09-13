"""tests/test_dataset.py — Unit tests for dataset integrity."""
import sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest

DATA_DIR = ROOT / "data" / "logistics_2500"
CLASS_NAMES = {0: "cardboard box", 1: "forklift", 2: "freight container",
               3: "wood pallet", 4: "truck"}
ALLOWED_IDS = set(CLASS_NAMES.keys())


def get_images(split):
    d = DATA_DIR / split / "images"
    if not d.exists():
        return []
    return list(d.glob("*.jpg")) + list(d.glob("*.jpeg")) + list(d.glob("*.png"))


def get_labels(split):
    d = DATA_DIR / split / "labels"
    if not d.exists():
        return []
    return list(d.glob("*.txt"))


@pytest.fixture(scope="session")
def dataset_exists():
    return DATA_DIR.exists() and (DATA_DIR / "train" / "images").exists()


def test_data_directory_exists():
    assert DATA_DIR.exists(), f"Dataset directory not found: {DATA_DIR}"


@pytest.mark.skipif(not (DATA_DIR / "train" / "images").exists(),
                    reason="Dataset not downloaded yet")
def test_train_image_count():
    imgs = get_images("train")
    assert len(imgs) == 1500, f"Expected 1500 train images, got {len(imgs)}"


@pytest.mark.skipif(not (DATA_DIR / "val" / "images").exists(),
                    reason="Dataset not downloaded yet")
def test_val_image_count():
    imgs = get_images("val")
    assert len(imgs) == 500, f"Expected 500 val images, got {len(imgs)}"


@pytest.mark.skipif(not (DATA_DIR / "test" / "images").exists(),
                    reason="Dataset not downloaded yet")
def test_test_image_count():
    imgs = get_images("test")
    assert len(imgs) == 500, f"Expected 500 test images, got {len(imgs)}"


@pytest.mark.skipif(not (DATA_DIR / "train" / "labels").exists(),
                    reason="Dataset not downloaded yet")
def test_labels_exist_for_all_train_images():
    labels_dir = DATA_DIR / "train" / "labels"
    imgs = get_images("train")
    missing = []
    for img in imgs:
        lbl = labels_dir / (img.stem + ".txt")
        if not lbl.exists():
            missing.append(img.name)
    assert len(missing) == 0, f"{len(missing)} images missing labels: {missing[:5]}"


@pytest.mark.skipif(not (DATA_DIR / "train" / "labels").exists(),
                    reason="Dataset not downloaded yet")
def test_only_allowed_class_ids():
    bad = []
    for split in ["train", "val", "test"]:
        lbls_dir = DATA_DIR / split / "labels"
        if not lbls_dir.exists():
            continue
        for lbl_path in lbls_dir.glob("*.txt"):
            for line in lbl_path.read_text().strip().splitlines():
                parts = line.strip().split()
                if not parts:
                    continue
                try:
                    cls_id = int(parts[0])
                    if cls_id not in ALLOWED_IDS:
                        bad.append(f"{lbl_path.name}:cls={cls_id}")
                except ValueError:
                    pass
    assert len(bad) == 0, f"Unexpected class IDs: {bad[:10]}"


@pytest.mark.skipif(not (DATA_DIR / "train" / "labels").exists(),
                    reason="Dataset not downloaded yet")
def test_bounding_boxes_valid():
    bad = []
    for split in ["train", "val", "test"]:
        lbls_dir = DATA_DIR / split / "labels"
        if not lbls_dir.exists():
            continue
        for lbl_path in lbls_dir.glob("*.txt"):
            for line in lbl_path.read_text().strip().splitlines():
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                try:
                    cx, cy, w, h = map(float, parts[1:5])
                    if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
                        bad.append(f"{lbl_path.name}: cx={cx} cy={cy} w={w} h={h}")
                except ValueError:
                    bad.append(f"{lbl_path.name}: parse error")
    assert len(bad) == 0, f"{len(bad)} invalid bboxes: {bad[:5]}"
