# Model Weights Information

- **File Path:** `weights/best.pt`
- **Architecture:** RT-DETR-Large (Ultralytics implementation)
- **Checkpoint Origin:** Epoch 1 (`epoch0.pt`, SHA256: `455f8478266cbd48...`)
- **Best Fitness:** 0.40391 (based on mAP50-95)
- **Classes:** `cardboard box`, `forklift`, `freight container`, `wood pallet`, `truck`

## Python Load Snippet
```python
from app.detector import get_detector
detector = get_detector()
```
