"""
scripts/verify_dataset.py

Programmatic dataset verification with 12 checks.
Saves output to artifacts/dataset_verification.txt.

Expected structure:
    data/logistics_2500/
        train/images/  (1500 images, 300 per class)
        train/labels/
        val/images/    (500 images, 100 per class)
        val/labels/
        test/images/   (500 images, 100 per class)
        test/labels/

Expected classes:
    0 = cardboard box
    1 = forklift
    2 = freight container
    3 = wood pallet
    4 = truck
"""

import hashlib
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from PIL import Image, UnidentifiedImageError
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARN] Pillow not installed. Image corruption check will be skipped.")

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    print("[WARN] imagehash not installed. Perceptual hash check will be skipped.")

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "logistics_2500"
ARTIFACTS_DIR = ROOT / "artifacts"
OUTPUT_FILE = ARTIFACTS_DIR / "dataset_verification.txt"

CLASS_NAMES = {
    0: "cardboard box",
    1: "forklift",
    2: "freight container",
    3: "wood pallet",
    4: "truck",
}
ALLOWED_CLASS_IDS = set(CLASS_NAMES.keys())
NUM_CLASSES = 5

EXPECTED = {
    "total": 2500,
    "train": 1500,
    "val": 500,
    "test": 500,
    "per_class_per_split": {
        "train": 300,
        "val": 100,
        "test": 100,
    },
}

RESULTS = {}
ERRORS = []
WARNINGS = []


def log(msg: str):
    print(msg)


def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    RESULTS[name] = {"status": status, "detail": detail}
    icon = "✓" if passed else "✗"
    log(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))
    if not passed:
        ERRORS.append(f"{name}: {detail}")


def get_image_files(split: str) -> list[Path]:
    d = DATA_DIR / split / "images"
    if not d.exists():
        return []
    return sorted(
        [p for p in d.iterdir()
         if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}]
    )


def get_label_files(split: str) -> list[Path]:
    d = DATA_DIR / split / "labels"
    if not d.exists():
        return []
    return sorted([p for p in d.iterdir() if p.suffix == ".txt"])


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_label(label_path: Path) -> list[tuple]:
    """Parse YOLO label file. Returns list of (class_id, cx, cy, w, h)."""
    annotations = []
    for line in label_path.read_text(encoding="utf-8").strip().splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        try:
            cls_id = int(parts[0])
            coords = [float(x) for x in parts[1:5]]
            annotations.append((cls_id, *coords))
        except (ValueError, IndexError):
            pass
    return annotations


def run_verification():
    log("=" * 65)
    log("DATASET VERIFICATION")
    log(f"Timestamp : {datetime.now().isoformat()}")
    log(f"Data dir  : {DATA_DIR}")
    log("=" * 65)

    splits = ["train", "val", "test"]

    # ── Collect image and label paths ─────────────────────────────────────
    images = {s: get_image_files(s) for s in splits}
    labels = {s: get_label_files(s) for s in splits}

    total_images = sum(len(v) for v in images.values())
    log(f"\n[Found] train:{len(images['train'])} | val:{len(images['val'])} | test:{len(images['test'])} | total:{total_images}")

    log("\n── CHECK 1: Total image count ─────────────────────────────────────")
    check("1_total_images", total_images == EXPECTED["total"],
          f"found {total_images}, expected {EXPECTED['total']}")

    log("\n── CHECK 2: Train split count ─────────────────────────────────────")
    check("2_train_count", len(images["train"]) == EXPECTED["train"],
          f"found {len(images['train'])}, expected {EXPECTED['train']}")

    log("\n── CHECK 3: Val split count ───────────────────────────────────────")
    check("3_val_count", len(images["val"]) == EXPECTED["val"],
          f"found {len(images['val'])}, expected {EXPECTED['val']}")

    log("\n── CHECK 4: Test split count ──────────────────────────────────────")
    check("4_test_count", len(images["test"]) == EXPECTED["test"],
          f"found {len(images['test'])}, expected {EXPECTED['test']}")

    # ── Per-class distribution ────────────────────────────────────────────
    log("\n── CHECK 5: Class distribution per split ──────────────────────────")
    class_counts = {s: defaultdict(int) for s in splits}
    all_annotations = {s: [] for s in splits}

    for split in splits:
        labels_dir = DATA_DIR / split / "labels"
        for img_path in images[split]:
            lbl_path = labels_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue
            anns = parse_label(lbl_path)
            all_annotations[split].extend(anns)
            seen_ids = set()
            for ann in anns:
                cls_id = ann[0]
                if cls_id not in seen_ids:
                    class_counts[split][cls_id] += 1
                    seen_ids.add(cls_id)

    log(f"\n  Per-class image count (images containing ≥1 annotation of that class):")
    dist_ok = True
    for split in splits:
        expected_per_cls = EXPECTED["per_class_per_split"][split]
        log(f"\n  [{split}] (expected {expected_per_cls} per class):")
        for cls_id in sorted(ALLOWED_CLASS_IDS):
            count = class_counts[split].get(cls_id, 0)
            ok = count == expected_per_cls
            icon = "✓" if ok else "✗"
            log(f"    [{icon}] {CLASS_NAMES[cls_id]:20s}: {count}")
            if not ok:
                dist_ok = False
    check("5_class_distribution", dist_ok,
          "all classes match expected per-split counts" if dist_ok
          else "one or more classes have incorrect counts")

    # ── Check 6: Only allowed classes ─────────────────────────────────────
    log("\n── CHECK 6: Only allowed class IDs ────────────────────────────────")
    found_ids = set()
    for split in splits:
        for ann in all_annotations[split]:
            found_ids.add(ann[0])
    unexpected = found_ids - ALLOWED_CLASS_IDS
    check("6_only_allowed_classes",
          len(unexpected) == 0,
          f"unexpected IDs: {unexpected}" if unexpected
          else f"all IDs in {sorted(found_ids)} are allowed")

    # ── Check 7: Every image has annotation ───────────────────────────────
    log("\n── CHECK 7: Every image has a corresponding annotation ─────────────")
    missing_labels = []
    for split in splits:
        labels_dir = DATA_DIR / split / "labels"
        for img_path in images[split]:
            lbl_path = labels_dir / (img_path.stem + ".txt")
            if not lbl_path.exists() or lbl_path.stat().st_size == 0:
                missing_labels.append(str(img_path))
    check("7_annotations_exist", len(missing_labels) == 0,
          f"{len(missing_labels)} images missing labels"
          if missing_labels else "all images have non-empty label files")
    if missing_labels[:5]:
        for p in missing_labels[:5]:
            log(f"    MISSING: {p}")

    # ── Check 8: Valid class IDs in annotations ────────────────────────────
    log("\n── CHECK 8: All annotations reference valid class IDs ─────────────")
    bad_class_refs = []
    for split in splits:
        labels_dir = DATA_DIR / split / "labels"
        for img_path in images[split]:
            lbl_path = labels_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue
            for ann in parse_label(lbl_path):
                if ann[0] not in ALLOWED_CLASS_IDS:
                    bad_class_refs.append(
                        f"{lbl_path.name}: class_id={ann[0]}"
                    )
    check("8_valid_class_ids", len(bad_class_refs) == 0,
          f"{len(bad_class_refs)} invalid class references"
          if bad_class_refs else "all class IDs valid")

    # ── Check 9: No corrupt images ────────────────────────────────────────
    log("\n── CHECK 9: No corrupt images ─────────────────────────────────────")
    corrupt = []
    if PIL_AVAILABLE:
        for split in splits:
            for img_path in images[split]:
                try:
                    with Image.open(img_path) as img:
                        img.verify()
                except Exception as e:
                    corrupt.append(f"{img_path.name}: {e}")
        check("9_no_corrupt_images", len(corrupt) == 0,
              f"{len(corrupt)} corrupt images" if corrupt
              else "all images are valid")
    else:
        check("9_no_corrupt_images", False,
              "SKIPPED — Pillow not installed")

    # ── Check 10: No duplicate filenames ─────────────────────────────────
    log("\n── CHECK 10: No duplicate filenames ───────────────────────────────")
    all_names = []
    for split in splits:
        all_names.extend([p.name for p in images[split]])
    name_counts = defaultdict(int)
    for n in all_names:
        name_counts[n] += 1
    dup_names = [n for n, c in name_counts.items() if c > 1]
    check("10_no_dup_filenames", len(dup_names) == 0,
          f"{len(dup_names)} duplicate filenames" if dup_names
          else "all filenames unique")

    # ── Check 11: No duplicate content (SHA256) ───────────────────────────
    log("\n── CHECK 11: No duplicate image content (SHA256) ──────────────────")
    sha_map = defaultdict(list)
    for split in splits:
        for img_path in images[split]:
            h = sha256_file(img_path)
            sha_map[h].append(str(img_path))
    dup_content = {h: paths for h, paths in sha_map.items() if len(paths) > 1}
    check("11_no_dup_content", len(dup_content) == 0,
          f"{len(dup_content)} groups of duplicate content"
          if dup_content else "all image contents unique")
    if dup_content:
        for h, paths in list(dup_content.items())[:3]:
            log(f"    DUP {h[:12]}: {paths}")

    # ── Check 12: Valid bounding boxes ────────────────────────────────────
    log("\n── CHECK 12: Valid bounding boxes ─────────────────────────────────")
    bbox_errors = []
    for split in splits:
        labels_dir = DATA_DIR / split / "labels"
        for img_path in images[split]:
            lbl_path = labels_dir / (img_path.stem + ".txt")
            if not lbl_path.exists():
                continue
            for ann in parse_label(lbl_path):
                cls_id, cx, cy, w, h = ann
                errors = []
                if not (0.0 <= cx <= 1.0):
                    errors.append(f"cx={cx} out of [0,1]")
                if not (0.0 <= cy <= 1.0):
                    errors.append(f"cy={cy} out of [0,1]")
                if not (0.0 < w <= 1.0):
                    errors.append(f"w={w} not in (0,1]")
                if not (0.0 < h <= 1.0):
                    errors.append(f"h={h} not in (0,1]")
                if cx - w / 2 < 0 or cx + w / 2 > 1:
                    errors.append("box x-range outside [0,1]")
                if cy - h / 2 < 0 or cy + h / 2 > 1:
                    errors.append("box y-range outside [0,1]")
                if errors:
                    bbox_errors.append(
                        f"{lbl_path.name}: {errors}"
                    )
    check("12_valid_bboxes", len(bbox_errors) == 0,
          f"{len(bbox_errors)} invalid bounding boxes"
          if bbox_errors else "all bounding boxes valid")
    if bbox_errors[:3]:
        for e in bbox_errors[:3]:
            log(f"    BBOX ERR: {e}")

    # ── Summary ───────────────────────────────────────────────────────────
    log("\n" + "=" * 65)
    log("VERIFICATION SUMMARY")
    log("=" * 65)

    passed = sum(1 for r in RESULTS.values() if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS.values() if r["status"] == "FAIL")
    total_checks = len(RESULTS)

    log(f"\n  Total checks : {total_checks}")
    log(f"  PASSED       : {passed}")
    log(f"  FAILED       : {failed}")

    log(f"\n  Dataset Stats:")
    log(f"    Train images : {len(images['train'])}")
    log(f"    Val images   : {len(images['val'])}")
    log(f"    Test images  : {len(images['test'])}")
    log(f"    Total images : {total_images}")
    log(f"\n    Annotations per split:")
    for split in splits:
        log(f"      {split:5s}: {len(all_annotations[split])} annotations "
            f"across {len(images[split])} images")

    log(f"\n    Class distribution (annotation counts):")
    for split in splits:
        counts = defaultdict(int)
        for ann in all_annotations[split]:
            counts[ann[0]] += 1
        log(f"      [{split}]")
        for cls_id in sorted(ALLOWED_CLASS_IDS):
            log(f"        {CLASS_NAMES[cls_id]:20s}: {counts.get(cls_id, 0)} annotations")

    overall = "PASS" if failed == 0 else "FAIL"
    log(f"\n  OVERALL STATUS: {overall}")
    log("=" * 65)

    # Save to file
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    report_lines = []
    report_lines.append("DATASET VERIFICATION REPORT")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append(f"Data dir: {DATA_DIR}")
    report_lines.append("")
    for name, result in RESULTS.items():
        report_lines.append(f"  {result['status']:4s}  {name}: {result['detail']}")
    report_lines.append("")
    report_lines.append(f"Total: {total_checks} | PASS: {passed} | FAIL: {failed}")
    report_lines.append(f"OVERALL: {overall}")

    OUTPUT_FILE.write_text("\n".join(report_lines), encoding="utf-8")
    log(f"\n  Report saved: {OUTPUT_FILE}")

    return failed == 0


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
