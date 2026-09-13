"""
app/detector.py

RT-DETR inference wrapper with Non-Maximum Suppression (NMS) duplicate filtering
and coordinate validation.

Loads the trained best.pt checkpoint and provides a clean detect() interface.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
import torch
from torchvision.ops import batched_nms, nms

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
DEFAULT_CROSS_CLASS_IOU = 0.65
DEFAULT_IMGSZ = 640


class RTDETRDetector:
    """
    Wrapper around Ultralytics RTDETR for inference with duplicate suppression.
    Thread-safe once loaded (model.predict() is stateless per call).
    """

    def __init__(
        self,
        weights: Path = DEFAULT_WEIGHTS,
        conf_threshold: float = DEFAULT_CONF,
        iou_threshold: float = DEFAULT_IOU,
        cross_class_iou: float = DEFAULT_CROSS_CLASS_IOU,
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
        self.cross_class_iou = cross_class_iou
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
            f"Detector ready (conf={self.conf_threshold}, iou={self.iou_threshold}, imgsz={self.imgsz})"
        )

    def detect(
        self,
        image: Image.Image,
        conf_override: Optional[float] = None,
        iou_override: Optional[float] = None,
    ) -> list[dict]:
        """
        Run RT-DETR inference on a PIL Image and apply NMS post-processing to eliminate duplicate predictions.

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
        img_array = np.array(image)

        # Run Ultralytics predict
        results = self.model.predict(
            source=img_array,
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

        # 1. Class-wise NMS (suppresses overlapping predictions of the same class)
        keep_classwise = batched_nms(
            boxes_tensor,
            scores_tensor,
            classes_tensor.long(),
            iou_threshold=iou_thresh,
        )

        b_nms = boxes_tensor[keep_classwise]
        s_nms = scores_tensor[keep_classwise]
        c_nms = classes_tensor[keep_classwise]

        # 2. Cross-class NMS (suppresses ghost predictions across different classes with near-identical boxes)
        if self.cross_class_iou is not None and b_nms.numel() > 0:
            keep_cross = nms(b_nms, s_nms, iou_threshold=self.cross_class_iou)
            b_final = b_nms[keep_cross]
            s_final = s_nms[keep_cross]
            c_final = c_nms[keep_cross]
        else:
            b_final, s_final, c_final = b_nms, s_nms, c_nms

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
