"""
app/detector.py

RT-DETR inference wrapper with standard class-aware NMS and Intersection-over-Smaller (IoS)
same-class containment suppression.

Loads trained best.pt checkpoint and provides a clean detect() interface.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
import torch
from torchvision.ops import batched_nms

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logger = logging.getLogger("detector")

CLASS_NAMES = [
    "cardboard box",
    "forklift",
    "freight container",
    "wood pallet",
    "truck",
]

DEFAULT_WEIGHTS = ROOT / "weights" / "best.pt"
DEFAULT_CONF = 0.25
DEFAULT_IOU = 0.45
DEFAULT_CONTAINMENT_THRESHOLD = 0.65
DEFAULT_CROSS_CLASS_IOU_THRESHOLD = 0.80
DEFAULT_BOUNDARY_CONF_THRESHOLD = 0.30
DEFAULT_INSIDE_RATIO_THRESHOLD = 0.50
DEFAULT_IMGSZ = 640


def suppress_contained_boxes(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    classes: torch.Tensor,
    containment_threshold: float = DEFAULT_CONTAINMENT_THRESHOLD,
) -> torch.Tensor:
    """
    Suppress lower-confidence detections that are substantially contained inside a
    higher-confidence detection of the SAME CLASS.

    Intersection-over-Smaller (IoS / Containment Ratio):
        IoS(A, B) = Area(A ∩ B) / min(Area(A), Area(B))

    If a lower-scoring candidate box B of the same class is contained >= threshold
    (e.g., 65%) within a higher-scoring anchor box A, box B is identified as an
    internal sub-region false positive and suppressed.

    Args:
        boxes: (N, 4) tensor [x1, y1, x2, y2]
        scores: (N,) tensor of confidence scores
        classes: (N,) tensor of class indices
        containment_threshold: float, threshold ratio (default 0.65)

    Returns:
        keep: (K,) 1D LongTensor of indices to retain
    """
    if boxes.numel() == 0:
        return torch.empty((0,), dtype=torch.long, device=boxes.device)

    order = scores.argsort(descending=True)
    keep = []

    while order.numel() > 0:
        idx = order[0].item()
        keep.append(idx)
        if order.numel() == 1:
            break

        box_curr = boxes[idx]
        cls_curr = classes[idx]
        area_curr = (box_curr[2] - box_curr[0]) * (box_curr[3] - box_curr[1])

        other_indices = order[1:]
        boxes_other = boxes[other_indices]
        classes_other = classes[other_indices]

        # Pairwise intersection coordinates
        x1 = torch.max(box_curr[0], boxes_other[:, 0])
        y1 = torch.max(box_curr[1], boxes_other[:, 1])
        x2 = torch.min(box_curr[2], boxes_other[:, 2])
        y2 = torch.min(box_curr[3], boxes_other[:, 3])

        inter = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)
        areas_other = (boxes_other[:, 2] - boxes_other[:, 0]) * (boxes_other[:, 3] - boxes_other[:, 1])

        min_areas = torch.min(area_curr, areas_other)
        ios = inter / (min_areas + 1e-6)

        # Suppress ONLY if same class AND containment ratio >= threshold
        suppress = (classes_other == cls_curr) & (ios >= containment_threshold)
        order = order[1:][~suppress]

    return torch.tensor(keep, dtype=torch.long, device=boxes.device)


def suppress_cross_class_duplicates(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    classes: torch.Tensor,
    iou_threshold: float = DEFAULT_CROSS_CLASS_IOU_THRESHOLD,
) -> torch.Tensor:
    """
    Suppress lower-confidence detections that share high IoU (>= threshold) with a
    higher-confidence detection of a DIFFERENT CLASS.

    Process:
    - Sort detections by descending confidence score.
    - For each detection, keep it and compare against remaining lower-confidence detections.
    - If a remaining lower-confidence candidate box has a DIFFERENT class AND IoU >= iou_threshold (0.80),
      suppress the candidate box.

    Args:
        boxes: (N, 4) tensor [x1, y1, x2, y2]
        scores: (N,) tensor of confidence scores
        classes: (N,) tensor of class indices
        iou_threshold: float, IoU cutoff ratio (default 0.80)

    Returns:
        keep: (K,) 1D LongTensor of indices to retain
    """
    if boxes.numel() == 0:
        return torch.empty((0,), dtype=torch.long, device=boxes.device)

    order = scores.argsort(descending=True)
    keep = []

    while order.numel() > 0:
        idx = order[0].item()
        keep.append(idx)
        if order.numel() == 1:
            break

        box_curr = boxes[idx]
        cls_curr = classes[idx]
        area_curr = (box_curr[2] - box_curr[0]) * (box_curr[3] - box_curr[1])

        other_indices = order[1:]
        boxes_other = boxes[other_indices]
        classes_other = classes[other_indices]

        # Pairwise intersection coordinates
        x1 = torch.max(box_curr[0], boxes_other[:, 0])
        y1 = torch.max(box_curr[1], boxes_other[:, 1])
        x2 = torch.min(box_curr[2], boxes_other[:, 2])
        y2 = torch.min(box_curr[3], boxes_other[:, 3])

        inter = torch.clamp(x2 - x1, min=0) * torch.clamp(y2 - y1, min=0)
        areas_other = (boxes_other[:, 2] - boxes_other[:, 0]) * (boxes_other[:, 3] - boxes_other[:, 1])
        union = area_curr + areas_other - inter

        iou = inter / (union + 1e-6)

        # Suppress ONLY if DIFFERENT class AND IoU >= iou_threshold
        suppress = (classes_other != cls_curr) & (iou >= iou_threshold)
        order = order[1:][~suppress]

    return torch.tensor(keep, dtype=torch.long, device=boxes.device)


def suppress_boundary_artifacts(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    img_w: float,
    img_h: float,
    conf_cutoff: float = DEFAULT_BOUNDARY_CONF_THRESHOLD,
    inside_ratio_cutoff: float = DEFAULT_INSIDE_RATIO_THRESHOLD,
) -> torch.Tensor:
    """
    Suppress low-confidence detection boxes that extend substantially outside the image boundary.

    Inside Ratio:
        Area_raw = (x2_raw - x1_raw) * (y2_raw - y1_raw)
        Area_clipped = Area of intersection with [0, img_w] x [0, img_h]
        Inside Ratio = Area_clipped / Area_raw

    If confidence < conf_cutoff (0.30) AND Inside Ratio < inside_ratio_cutoff (0.50),
    the detection is identified as a boundary-clipping false positive and suppressed.

    Args:
        boxes: (N, 4) raw tensor [x1, y1, x2, y2]
        scores: (N,) tensor of confidence scores
        img_w: image width float
        img_h: image height float
        conf_cutoff: float (default 0.30)
        inside_ratio_cutoff: float (default 0.50)

    Returns:
        keep: (K,) 1D LongTensor of indices to retain
    """
    if boxes.numel() == 0:
        return torch.empty((0,), dtype=torch.long, device=boxes.device)

    raw_x1 = boxes[:, 0]
    raw_y1 = boxes[:, 1]
    raw_x2 = boxes[:, 2]
    raw_y2 = boxes[:, 3]

    raw_w = torch.clamp(raw_x2 - raw_x1, min=0)
    raw_h = torch.clamp(raw_y2 - raw_y1, min=0)
    raw_area = raw_w * raw_h

    c_x1 = torch.clamp(raw_x1, min=0.0, max=img_w)
    c_y1 = torch.clamp(raw_y1, min=0.0, max=img_h)
    c_x2 = torch.clamp(raw_x2, min=0.0, max=img_w)
    c_y2 = torch.clamp(raw_y2, min=0.0, max=img_h)

    clipped_w = torch.clamp(c_x2 - c_x1, min=0)
    clipped_h = torch.clamp(c_y2 - c_y1, min=0)
    clipped_area = clipped_w * clipped_h

    inside_ratio = clipped_area / (raw_area + 1e-6)

    # Suppress ONLY if score < conf_cutoff AND inside_ratio < inside_ratio_cutoff
    suppress = (scores < conf_cutoff) & (inside_ratio < inside_ratio_cutoff)
    keep_indices = torch.nonzero(~suppress, as_tuple=True)[0]

    return keep_indices


class RTDETRDetector:
    """
    Wrapper around Ultralytics RTDETR for inference with class-aware NMS,
    same-class IoS containment suppression, cross-class high-IoU suppression,
    and boundary artifact suppression.
    """

    def __init__(
        self,
        weights: Path = DEFAULT_WEIGHTS,
        conf_threshold: float = DEFAULT_CONF,
        iou_threshold: float = DEFAULT_IOU,
        containment_threshold: float = DEFAULT_CONTAINMENT_THRESHOLD,
        imgsz: int = DEFAULT_IMGSZ,
        device: Optional[str] = None,
    ):
        try:
            from ultralytics import RTDETR
        except ImportError:
            raise RuntimeError(
                "ultralytics not installed. Run: pip install ultralytics"
            )

        self.weights = Path(weights)
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.containment_threshold = containment_threshold
        self.imgsz = imgsz

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        if not self.weights.exists():
            raise FileNotFoundError(
                f"Model weights not found: {self.weights}\n"
                "Run: python scripts/train.py"
            )

        logger.info(f"Loading RT-DETR from {self.weights} on device={self.device}")
        self.model = RTDETR(str(self.weights))
        logger.info(
            f"Detector ready (conf={self.conf_threshold}, iou={self.iou_threshold}, containment={self.containment_threshold}, imgsz={self.imgsz})"
        )

    def detect(
        self,
        image: Image.Image,
        conf_override: Optional[float] = None,
        iou_override: Optional[float] = None,
    ) -> list[dict]:
        """
        Run RT-DETR inference on a PIL Image, apply class-aware NMS,
        same-class IoS containment suppression, cross-class high-IoU suppression,
        and boundary artifact suppression.

        Returns:
            list of dicts:
                {
                    "class": str,
                    "confidence": float,
                    "bbox": {"x1": float, "y1": float, "x2": float, "y2": float}
                }
        """
        conf = conf_override if conf_override is not None else self.conf_threshold
        iou_thresh = iou_override if iou_override is not None else self.iou_threshold

        img_w, img_h = image.width, image.height

        # Run Ultralytics predict
        results = self.model.predict(
            source=image,
            conf=conf,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )

        if not results or results[0].boxes is None or len(results[0].boxes) == 0:
            return []

        res = results[0]
        boxes_tensor = res.boxes.xyxy.detach().cpu()   # (N, 4)
        scores_tensor = res.boxes.conf.detach().cpu()  # (N,)
        classes_tensor = res.boxes.cls.detach().cpu()  # (N,)

        if boxes_tensor.numel() == 0:
            return []

        # 1. Standard Class-Aware NMS (suppresses overlapping boxes of the same class)
        keep_nms = batched_nms(
            boxes_tensor,
            scores_tensor,
            classes_tensor.long(),
            iou_threshold=iou_thresh,
        )

        b_nms = boxes_tensor[keep_nms]
        s_nms = scores_tensor[keep_nms]
        c_nms = classes_tensor[keep_nms]

        # 2. Same-Class IoS Containment Suppression (suppresses smaller sub-boxes inside a larger box of the SAME class)
        keep_ios = suppress_contained_boxes(
            b_nms,
            s_nms,
            c_nms,
            containment_threshold=self.containment_threshold,
        )

        b_ios = b_nms[keep_ios]
        s_ios = s_nms[keep_ios]
        c_ios = c_nms[keep_ios]

        # 3. Cross-Class High-IoU Duplicate Suppression (suppresses lower-conf duplicate boxes of DIFFERENT classes with IoU >= 0.80)
        keep_cross = suppress_cross_class_duplicates(
            b_ios,
            s_ios,
            c_ios,
            iou_threshold=DEFAULT_CROSS_CLASS_IOU_THRESHOLD,
        )

        b_cross = b_ios[keep_cross]
        s_cross = s_ios[keep_cross]
        c_cross = c_ios[keep_cross]

        # 4. Boundary Clipping Artifact Suppression (suppresses low-confidence boxes with >50% area outside canvas)
        keep_bound = suppress_boundary_artifacts(
            b_cross,
            s_cross,
            img_w=float(img_w),
            img_h=float(img_h),
            conf_cutoff=DEFAULT_BOUNDARY_CONF_THRESHOLD,
            inside_ratio_cutoff=DEFAULT_INSIDE_RATIO_THRESHOLD,
        )

        b_final = b_cross[keep_bound]
        s_final = s_cross[keep_bound]
        c_final = c_cross[keep_bound]

        detections = []
        for bbox, score, cls_tensor in zip(b_final, s_final, c_final):
            cls_id = int(cls_tensor.item())
            conf_val = float(score.item())
            raw_xyxy = bbox.tolist()

            # Clip bounding boxes strictly to image dimensions
            x1 = round(max(0.0, min(float(img_w), raw_xyxy[0])), 2)
            y1 = round(max(0.0, min(float(img_h), raw_xyxy[1])), 2)
            x2 = round(max(0.0, min(float(img_w), raw_xyxy[2])), 2)
            y2 = round(max(0.0, min(float(img_h), raw_xyxy[3])), 2)

            # Skip degenerate boxes
            if x2 <= x1 or y2 <= y1:
                continue

            cls_name = (
                CLASS_NAMES[cls_id]
                if 0 <= cls_id < len(CLASS_NAMES)
                else f"class_{cls_id}"
            )

            detections.append({
                "class": cls_name,
                "confidence": round(conf_val, 4),
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                },
            })

        # Sort final detections by confidence descending
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections


# Singleton instance
_detector_instance: Optional[RTDETRDetector] = None


def get_detector() -> RTDETRDetector:
    """Return the shared detector instance (lazy-loaded)."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = RTDETRDetector()
    return _detector_instance
