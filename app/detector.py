"""
app/detector.py

RT-DETR inference wrapper.
Loads the trained best.pt checkpoint and provides a clean detect() interface.
"""

import sys
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

CLASS_NAMES = [
    "cardboard box",
    "forklift",
    "freight container",
    "wood pallet",
    "truck",
]

DEFAULT_WEIGHTS = ROOT / "weights" / "best.pt"
DEFAULT_CONF = 0.25
DEFAULT_IMGSZ = 640


class RTDETRDetector:
    """
    Thin wrapper around Ultralytics RTDETR for inference.
    Thread-safe once loaded (model.predict() is stateless per call).
    """

    def __init__(
        self,
        weights: Path = DEFAULT_WEIGHTS,
        conf_threshold: float = DEFAULT_CONF,
        imgsz: int = DEFAULT_IMGSZ,
        device: Optional[str] = None,
    ):
        try:
            from ultralytics import RTDETR
            import torch
        except ImportError:
            raise RuntimeError(
                "ultralytics not installed. Run: pip install ultralytics"
            )

        self.weights = Path(weights)
        self.conf_threshold = conf_threshold
        self.imgsz = imgsz

        if device is None:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        if not self.weights.exists():
            raise FileNotFoundError(
                f"Model weights not found: {self.weights}\n"
                "Run: python scripts/train.py"
            )

        print(f"[Detector] Loading RT-DETR from {self.weights} on {self.device}")
        self.model = RTDETR(str(self.weights))
        print(f"[Detector] Ready (conf={self.conf_threshold}, imgsz={self.imgsz})")

    def detect(
        self,
        image: Image.Image,
        conf_override: Optional[float] = None,
    ) -> list[dict]:
        """
        Run RT-DETR inference on a PIL Image.

        Returns:
            list of dicts:
                {
                    "class": str,
                    "confidence": float,
                    "bbox": {"x1": float, "y1": float, "x2": float, "y2": float}
                }
        """
        conf = conf_override if conf_override is not None else self.conf_threshold

        # Convert PIL → numpy (model accepts numpy)
        img_array = np.array(image)

        results = self.model.predict(
            source=img_array,
            conf=conf,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )

        detections = []
        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf_val = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()

                cls_name = (
                    CLASS_NAMES[cls_id]
                    if 0 <= cls_id < len(CLASS_NAMES)
                    else f"class_{cls_id}"
                )

                detections.append({
                    "class": cls_name,
                    "confidence": round(conf_val, 4),
                    "bbox": {
                        "x1": round(xyxy[0], 2),
                        "y1": round(xyxy[1], 2),
                        "x2": round(xyxy[2], 2),
                        "y2": round(xyxy[3], 2),
                    },
                })

        # Sort by confidence descending
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections


# Module-level singleton — loaded once on first import
_detector_instance: Optional[RTDETRDetector] = None


def get_detector() -> RTDETRDetector:
    """Return the shared detector instance (lazy-loaded)."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = RTDETRDetector()
    return _detector_instance
