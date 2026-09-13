"""
scripts/prepare_dataset.py

Streams and extracts exactly 2,500 images from the Roboflow Universe logistics
dataset (large-benchmark-datasets/logistics-sz9jr) using HTTP range requests.
Avoids downloading the full 5.2GB (99k-image) archive by reading only the
central zip index and extracting the specific 2,500 images and remapped labels.

Target breakdown (Locked):
    cardboard box:     300 train | 100 val | 100 test (total 500)
    forklift:          300 train | 100 val | 100 test (total 500)
    freight container: 300 train | 100 val | 100 test (total 500)
    wood pallet:       300 train | 100 val | 100 test (total 500)
    truck:             300 train | 100 val | 100 test (total 500)
    ─────────────────────────────────────────────────────────────
    TOTAL:            1500 train | 500 val | 500 test = 2500 images

Usage:
    python scripts/prepare_dataset.py
"""

import io
import os
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
import requests
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TARGET_CLASSES = {
    "cardboard box": {"train": 300, "val": 100, "test": 100},
    "forklift": {"train": 300, "val": 100, "test": 100},
    "freight container": {"train": 300, "val": 100, "test": 100},
    "wood pallet": {"train": 300, "val": 100, "test": 100},
    "truck": {"train": 300, "val": 100, "test": 100},
}

CLASS_NAME_TO_TARGET_ID = {
    "cardboard box": 0,
    "forklift": 1,
    "freight container": 2,
    "wood pallet": 3,
    "truck": 4,
}

DATA_DIR = ROOT / "data" / "logistics_2500"
ARTIFACTS_DIR = ROOT / "artifacts"
LOG_FILE = ARTIFACTS_DIR / "dataset_acquisition.log"


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


class RemoteZipFile(io.RawIOBase):
    """Seekable stream that reads remote files via HTTP Range requests with a read-ahead cache."""

    def __init__(self, url: str, buffer_size: int = 16 * 1024 * 1024):
        self.url = url
        self.buffer_size = buffer_size
        r = requests.head(url, allow_redirects=True)
        r.raise_for_status()
        self.final_url = r.url
        self.size = int(r.headers.get("Content-Length", 0))
        if not self.size:
            raise ValueError(f"Could not determine Content-Length from {url}")
        self.pos = 0
        self.cache_pos = -1
        self.cache = b""

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self.pos = offset
        elif whence == io.SEEK_CUR:
            self.pos += offset
        elif whence == io.SEEK_END:
            self.pos = self.size + offset
        else:
            raise ValueError(f"Invalid whence: {whence}")
        return self.pos

    def tell(self) -> int:
        return self.pos

    def read(self, size: int = -1) -> bytes:
        if size == -1 or self.pos + size > self.size:
            size = self.size - self.pos
        if size <= 0:
            return b""

        # Check if requested range is in cache
        if not (self.cache_pos <= self.pos and self.pos + size <= self.cache_pos + len(self.cache)):
            fetch_size = max(size, self.buffer_size)
            fetch_size = min(fetch_size, self.size - self.pos)
            headers = {"Range": f"bytes={self.pos}-{self.pos + fetch_size - 1}"}
            resp = requests.get(self.final_url, headers=headers)
            resp.raise_for_status()
            self.cache = resp.content
            self.cache_pos = self.pos

        offset = self.pos - self.cache_pos
        data = self.cache[offset:offset + size]
        self.pos += len(data)
        return data

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True


def get_api_key() -> str:
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("ROBOFLOW_API_KEY="):
                k = line.split("=", 1)[1].strip()
                if k:
                    return k
    k = os.environ.get("ROBOFLOW_API_KEY", "")
    if k:
        return k
    raise ValueError("ROBOFLOW_API_KEY not found in .env or environment")


def get_export_url(api_key: str) -> str:
    """Fetch the export download URL for version 1 in yolov8 format."""
    import roboflow.adapters.rfapi as rfapi
    log("Requesting dataset export link from Roboflow API...")
    info = rfapi.get_version_export(
        api_key=api_key,
        workspace_url="large-benchmark-datasets",
        project_url="logistics-sz9jr",
        version="1",
        format="yolov8",
    )
    link = info["export"]["link"]
    log(f"Received export link: {link[:60]}...")
    return link


def prepare_dataset():
    start_time = time.time()
    log("=" * 70)
    log("DATASET PREPARATION (REMOTE STREAMING & SELECTIVE EXTRACTION)")
    log("Target: 2,500 images | 5 classes | 500 per class | 1500/500/500 split")
    log("=" * 70)

    api_key = get_api_key()
    export_url = get_export_url(api_key)

    log("Connecting to remote zip archive...")
    remote_file = RemoteZipFile(export_url, buffer_size=16 * 1024 * 1024)
    log(f"Remote dataset size: {remote_file.size / (1024 * 1024 * 1024):.2f} GB")

    log("Reading zip central directory...")
    zf = zipfile.ZipFile(remote_file)
    all_names = set(zf.namelist())
    log(f"Total entries in archive: {len(all_names):,}")

    # Read data.yaml to verify source classes
    raw_yaml = zf.read("data.yaml").decode("utf-8")
    data_cfg = yaml.safe_load(raw_yaml)
    source_names = data_cfg.get("names", [])
    log(f"Source classes ({len(source_names)}): {source_names}")

    # Source class name -> source class id
    source_name_to_id = {name: i for i, name in enumerate(source_names)}
    target_to_source_ids = {}
    for target_class in TARGET_CLASSES:
        if target_class in source_name_to_id:
            src_id = source_name_to_id[target_class]
            target_to_source_ids[target_class] = src_id
            log(f"  Mapping: '{target_class}' -> Source ID {src_id} -> Target ID {CLASS_NAME_TO_TARGET_ID[target_class]}")
        else:
            raise ValueError(f"Target class '{target_class}' not found in source dataset classes!")

    source_id_to_target_id = {
        src_id: CLASS_NAME_TO_TARGET_ID[t_cls]
        for t_cls, src_id in target_to_source_ids.items()
    }

    # Splits configuration: (source_split_prefix, dest_split_name)
    split_configs = [
        ("test", "test"),
        ("valid", "val"),
        ("train", "train"),
    ]

    selected_files_by_split = {}  # dest_split -> list of (img_entry, lbl_entry, remapped_label_content)
    used_base_stems = set()

    for src_prefix, dest_split in split_configs:
        log(f"\n--- Scanning labels for split: {src_prefix} -> {dest_split} ---")
        lbl_files = [
            x for x in all_names
            if x.startswith(f"{src_prefix}/labels/") and x.endswith(".txt")
        ]
        log(f"Found {len(lbl_files):,} label files in {src_prefix}/labels/")

        # Sort label files by zip header_offset for contiguous linear reads
        lbl_infos = [zf.getinfo(x) for x in lbl_files]
        lbl_infos.sort(key=lambda x: x.header_offset)

        # Map: target_class -> list of (lbl_info, class_set, remapped_lines)
        candidates_per_class = {cls: [] for cls in TARGET_CLASSES}
        quota_needed = {cls: TARGET_CLASSES[cls][dest_split] for cls in TARGET_CLASSES}

        log(f"Scanning labels to fulfill quotas: {quota_needed}")
        scan_count = 0
        t_scan = time.time()

        for info in lbl_infos:
            stem = Path(info.filename).stem
            # Deduplicate by base stem to prevent identical augmented images
            base_stem = stem.split("_jpg.rf.")[0].split(".rf.")[0]
            if base_stem in used_base_stems:
                continue

            # Check if corresponding image exists
            img_candidate = f"{src_prefix}/images/{stem}.jpg"
            if img_candidate not in all_names:
                img_candidate = f"{src_prefix}/images/{stem}.png"
                if img_candidate not in all_names:
                    continue

            try:
                content = zf.read(info).decode("utf-8").strip()
            except Exception:
                continue
            if not content:
                continue

            classes_in_file = set()
            has_unwanted_class = False
            remapped_lines = []
            for line in content.splitlines():
                parts = line.strip().split()
                if not parts:
                    continue
                try:
                    c_id = int(parts[0])
                except ValueError:
                    continue
                if c_id in source_id_to_target_id:
                    new_id = source_id_to_target_id[c_id]
                    remapped_lines.append(f"{new_id} {' '.join(parts[1:])}")
                    classes_in_file.add(new_id)
                else:
                    has_unwanted_class = True

            if not remapped_lines:
                continue

            # Select pure single-class images with no unwanted classes
            # This guarantees exact 300 / 100 / 100 per class without multi-class overlap
            if len(classes_in_file) == 1 and not has_unwanted_class:
                target_id = list(classes_in_file)[0]
                target_class = [k for k, v in CLASS_NAME_TO_TARGET_ID.items() if v == target_id][0]
                if len(candidates_per_class[target_class]) < quota_needed[target_class]:
                    candidates_per_class[target_class].append((img_candidate, info.filename, "\n".join(remapped_lines)))
                    used_base_stems.add(base_stem)

            scan_count += 1
            # Check if all quotas satisfied
            if all(len(candidates_per_class[cls]) >= quota_needed[cls] for cls in TARGET_CLASSES):
                log(f"All quotas met for {dest_split} after inspecting {scan_count} labels in {time.time() - t_scan:.1f}s!")
                break

        # Collect selected for this split
        split_selected = []
        for target_class, items in candidates_per_class.items():
            count = len(items)
            needed = quota_needed[target_class]
            log(f"  [{dest_split}] {target_class}: {count}/{needed} selected")
            if count < needed:
                log(f"WARNING: Insufficient images for [{dest_split}] {target_class} (found {count}, needed {needed})")
            for img_name, lbl_name, remapped_content in items:
                split_selected.append((img_name, lbl_name, remapped_content))

        selected_files_by_split[dest_split] = split_selected
        log(f"Total selected for {dest_split}: {len(split_selected)} images")

    # Overall summary
    total_selected = sum(len(v) for v in selected_files_by_split.values())
    log(f"\nTotal selected across all splits: {total_selected} images")

    # Now download and extract ONLY the selected images and labels
    log("\n" + "=" * 70)
    log("DOWNLOADING & EXTRACTING SELECTED IMAGES")
    log("=" * 70)

    for dest_split, items in selected_files_by_split.items():
        img_dest_dir = DATA_DIR / dest_split / "images"
        lbl_dest_dir = DATA_DIR / dest_split / "labels"
        img_dest_dir.mkdir(parents=True, exist_ok=True)
        lbl_dest_dir.mkdir(parents=True, exist_ok=True)

        # Sort items by image header_offset in the zip archive for optimal sequential I/O
        items_with_info = [(zf.getinfo(img), img, lbl, remapped) for img, lbl, remapped in items]
        items_with_info.sort(key=lambda x: x[0].header_offset)

        log(f"Extracting {len(items_with_info)} images for {dest_split}...")
        t_ext = time.time()
        for i, (img_info, img_name, lbl_name, remapped) in enumerate(items_with_info):
            # Extract image bytes
            img_data = zf.read(img_info)
            dest_img_path = img_dest_dir / Path(img_name).name
            with open(dest_img_path, "wb") as f:
                f.write(img_data)

            # Write remapped label
            dest_lbl_path = lbl_dest_dir / (Path(img_name).stem + ".txt")
            with open(dest_lbl_path, "w", encoding="utf-8") as f:
                f.write(remapped + "\n")

            if (i + 1) % 100 == 0 or (i + 1) == len(items_with_info):
                elapsed = time.time() - t_ext
                rate = (i + 1) / elapsed if elapsed > 0 else 0
                log(f"  Extracted {i + 1}/{len(items_with_info)} images ({rate:.1f} imgs/s)")

    # Write configs/data.yaml
    configs_dir = ROOT / "configs"
    configs_dir.mkdir(parents=True, exist_ok=True)
    yaml_content = f"""# Logistics Object Detection Dataset
# 2,500 images, 5 classes, YOLO format

path: {DATA_DIR.as_posix()}

train: train/images
val: val/images
test: test/images

nc: 5

names:
  0: cardboard box
  1: forklift
  2: freight container
  3: wood pallet
  4: truck
"""
    yaml_path = configs_dir / "data.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    log(f"Written data.yaml to {yaml_path}")

    total_time = time.time() - start_time
    log("=" * 70)
    log(f"DATASET PREPARATION COMPLETED SUCCESSFULLY in {total_time:.1f}s ({total_time / 60:.1f} min)")
    log(f"Dataset location: {DATA_DIR}")
    log("=" * 70)


if __name__ == "__main__":
    prepare_dataset()
