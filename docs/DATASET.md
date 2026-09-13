# Dataset documentation — see README.md Section 4 for full details.
# This file will be updated after dataset acquisition.

## Source

- URL: https://universe.roboflow.com/large-benchmark-datasets/logistics-sz9jr
- Workspace: large-benchmark-datasets
- Project: logistics-sz9jr
- License: CC BY 4.0

## Selected Subset

We selected exactly 2,500 images from this dataset.

| Class | Train | Val | Test | Total |
|-------|-------|-----|------|-------|
| cardboard box | 300 | 100 | 100 | 500 |
| forklift | 300 | 100 | 100 | 500 |
| freight container | 300 | 100 | 100 | 500 |
| wood pallet | 300 | 100 | 100 | 500 |
| truck | 300 | 100 | 100 | 500 |
| **TOTAL** | **1500** | **500** | **500** | **2500** |

## Class ID Mapping

| ID | Class |
|----|-------|
| 0 | cardboard box |
| 1 | forklift |
| 2 | freight container |
| 3 | wood pallet |
| 4 | truck |

## Annotation Format

YOLO format: `class_id cx cy w h` (normalized 0–1).

## Acquisition Process

See `scripts/prepare_dataset.py` and `artifacts/dataset_acquisition.log`.
