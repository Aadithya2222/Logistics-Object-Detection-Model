"""
app/utils.py
Image loading utilities and bounding-box helpers.
"""

import io
from pathlib import Path

import numpy as np
from PIL import Image


def load_image_bytes(image_bytes: bytes) -> Image.Image:
    """Load a PIL Image from raw bytes."""
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def pil_to_numpy(img: Image.Image) -> np.ndarray:
    """Convert PIL Image to numpy array (H, W, C) uint8 RGB."""
    return np.array(img)


def box_center(bbox: dict) -> tuple[float, float]:
    """Return (cx, cy) of a bbox dict with x1,y1,x2,y2 keys."""
    cx = (bbox["x1"] + bbox["x2"]) / 2
    cy = (bbox["y1"] + bbox["y2"]) / 2
    return cx, cy


def box_area(bbox: dict) -> float:
    """Return pixel area of bbox."""
    return (bbox["x2"] - bbox["x1"]) * (bbox["y2"] - bbox["y1"])


def boxes_overlap(a: dict, b: dict) -> float:
    """Return IoU of two bboxes."""
    ix1 = max(a["x1"], b["x1"])
    iy1 = max(a["y1"], b["y1"])
    ix2 = min(a["x2"], b["x2"])
    iy2 = min(a["y2"], b["y2"])
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = box_area(a)
    area_b = box_area(b)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def box_distance(a: dict, b: dict) -> float:
    """Euclidean distance between box centers."""
    cx_a, cy_a = box_center(a)
    cx_b, cy_b = box_center(b)
    return ((cx_a - cx_b) ** 2 + (cy_a - cy_b) ** 2) ** 0.5


def relative_position(a: dict, b: dict) -> str:
    """
    Describe the position of box a relative to box b.
    Returns one of: 'left', 'right', 'above', 'below', 'overlapping'.
    """
    cx_a, cy_a = box_center(a)
    cx_b, cy_b = box_center(b)

    dx = cx_a - cx_b
    dy = cy_a - cy_b

    overlap = boxes_overlap(a, b)
    if overlap > 0.1:
        return "overlapping"

    if abs(dx) > abs(dy):
        return "right of" if dx > 0 else "left of"
    else:
        return "below" if dy > 0 else "above"
