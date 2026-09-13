# API Documentation

### Public Live URL (Cloudflare Tunnel):
- **Base URL:** `https://prices-debug-match-twist.trycloudflare.com`
- **Interactive Swagger Docs:** [https://prices-debug-match-twist.trycloudflare.com/docs](https://prices-debug-match-twist.trycloudflare.com/docs)
- **Local Fallback:** `http://127.0.0.1:8000`

---

## Endpoints

### GET /health
Liveness check.
```bash
curl http://127.0.0.1:8000/health
```
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

### GET /classes
List the five supported detection classes.
```bash
curl http://127.0.0.1:8000/classes
```

---

### POST /detect

Detect logistics objects in an image.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/detect \
  -F "file=@/path/to/image.jpg"
```

**Response:**
```json
{
  "objects": [
    {
      "class": "freight container",
      "confidence": 0.618,
      "bbox": {
        "x1": 83.64,
        "y1": 22.29,
        "x2": 587.44,
        "y2": 601.26
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5429,
      "bbox": {
        "x1": 66.87,
        "y1": 20.91,
        "x2": 529.49,
        "y2": 593.88
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5259,
      "bbox": {
        "x1": 85.39,
        "y1": 20.74,
        "x2": 589.68,
        "y2": 616.49
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4925,
      "bbox": {
        "x1": 189.41,
        "y1": 112.31,
        "x2": 292.83,
        "y2": 200.68
      }
    },
    {
      "class": "freight container",
      "confidence": 0.442,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4302,
      "bbox": {
        "x1": 66.5,
        "y1": 26.28,
        "x2": 579.97,
        "y2": 604.1
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.3983,
      "bbox": {
        "x1": -33.65,
        "y1": 332.6,
        "x2": 591.2,
        "y2": 623.58
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3912,
      "bbox": {
        "x1": 385.56,
        "y1": 259.19,
        "x2": 443.97,
        "y2": 353.46
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3763,
      "bbox": {
        "x1": 69.2,
        "y1": 27.09,
        "x2": 585.2,
        "y2": 604.54
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.3554,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3369,
      "bbox": {
        "x1": 68.31,
        "y1": 31.21,
    
```

---

### POST /ask

Answer a natural-language question about an image.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -F "file=@/path/to/image.jpg" \
  -F "question=How many forklifts are visible?"
```

**Supported intents:**

| Intent | Example question |
|--------|-----------------|
| COUNT | "How many forklifts are visible?" |
| PRESENCE | "Is there a truck?" |
| LIST | "What objects are in the image?" |
| MOST_COMMON | "What is the most common object?" |
| SPATIAL | "Is the forklift near the pallet?" |
| UNKNOWN | "What is the weather?" (unsupported — safe response) |

**Example response (COUNT):**
```json
{
  "answer": "There is 1 forklift visible.",
  "used_detector": true,
  "confidence": "medium",
  "detections": [
    {
      "class": "freight container",
      "confidence": 0.618,
      "bbox": {
        "x1": 83.64,
        "y1": 22.29,
        "x2": 587.44,
        "y2": 601.26
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5429,
      "bbox": {
        "x1": 66.87,
        "y1": 20.91,
        "x2": 529.49,
        "y2": 593.88
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5259,
      "bbox": {
        "x1": 85.39,
        "y1": 20.74,
        "x2": 589.68,
        "y2": 616.49
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4925,
      "bbox": {
        "x1": 189.41,
        "y1": 112.31,
        "x2": 292.83,
        "y2": 200.68
      }
    },
    {
      "class": "freight container",
      "confidence": 0.442,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4302,
      "bbox": {
        "x1": 66.5,
        "y1": 26.28,
        "x2": 579.97,
        "y2": 604.1
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.3983,
      "bbox": {
        "x1": -33.65,
        "y1": 332.6,
        "x2": 591.2,
        "y2": 623.58
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3912,
      "bbox": {
        "x1": 385.56,
        "y1": 259.19,
        "x2": 443.97,
        "y2": 353.46
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3763,
      "bbox": {
        "x1": 69.2,
        "y1": 27.09,
        "x2": 585.2,
        "y2": 604.54
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.3554,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3369,
      "bbox": {
        "x1": 68.31,
        "y1": 31.21,
        "x2": 580.19,
        "y2": 617.09
      }
    },
    {
      "class": "freight container",
      "confidence": 0.336,
      "bbox": {
        "x1": 67.43,
        "y1": 0.08,
        "x2": 590.2,
        "y2": 639.98
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3121,
      "bbox": {
        "x1": 86.26,
        "y1": 137.96,
        "x2": 119.56,
        "y2": 195.91
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3022,
      "bbox": {
        "x1": 62.36,
        "y1": 24.69,
        "x2": 585.23,
        "y2": 612.54
      }
    },
    {
      "class": "forklift",
      "confidence": 0.2997,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2962,
      "bbox": {
        "x1": 65.39,
        "y1": -2.38,
        "x2": 581.43,
        "y2": 637.6
      }
    },
    {
      "class": "freight container",
      "confidence": 0.296,
      "bbox": {
        "x1": 139.48,
        "y1": 23.95,
        "x2": 583.12,
        "y2": 594.45
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2941,
      "bbox": {
        "x1": 198.01,
        "y1": 114.67,
        "x2": 292.07,
        "y2": 152.16
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2936,
      "bbox": {
        "x1": 69.32,
        "y1": -0.8,
        "x2": 590.02,
        "y2": 639.14
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2888,
      "bbox": {
        "x1": 65.66,
        "y1": 3.21,
        "x2": 592.08,
        "y2": 636.1
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.2869,
      "bbox": {
        "x1": -110.38,
        "y1": -281.48,
        "x2": 150.13,
        "y2": 349.62
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2842,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2828,
      "bbox": {
        "x1": -110.38,
        "y1": -281.48,
        "x2": 150.13,
        "y2": 349.62
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2805,
      "bbox": {
        "x1": 335.88,
        "y1": 119.61,
        "x2": 377.08,
        "y2": 196.69
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.279,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2769,
      "bbox": {
        "x1": 61.92,
        "y1": 23.84,
        "x2": 590.17,
        "y2": 612.18
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2652,
      "bbox": {
        "x1": -19.0,
        "y1": 262.85,
        "x2": 620.98,
        "y2": 733.65
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2646,
      "bbox": {
        "x1": 80.2,
        "y1": 39.86,
        "x2": 566.04,
        "y2": 381.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2646,
      "bbox": {
        "x1": 184.63,
        "y1": 24.26,
        "x2": 573.35,
        "y2": 597.92
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2627,
      "bbox": {
        "x1": 86.55,
        "y1": 39.89,
        "x2": 571.69,
        "y2": 341.57
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.2615,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2566,
      "bbox": {
        "x1": 52.3,
        "y1": 24.68,
        "x2": 591.65,
        "y2": 621.14
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2557,
      "bbox": {
        "x1": 65.17,
        "y1": 83.49,
        "x2": 594.22,
        "y2": 623.13
      }
    }
  ],
  "intent": "COUNT"
}
```

**Example response (PRESENCE):**
```json
{
  "answer": "Yes, there is 1 forklift visible.",
  "used_detector": true,
  "confidence": "medium",
  "detections": [
    {
      "class": "freight container",
      "confidence": 0.618,
      "bbox": {
        "x1": 83.64,
        "y1": 22.29,
        "x2": 587.44,
        "y2": 601.26
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5429,
      "bbox": {
        "x1": 66.87,
        "y1": 20.91,
        "x2": 529.49,
        "y2": 593.88
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5259,
      "bbox": {
        "x1": 85.39,
        "y1": 20.74,
        "x2": 589.68,
        "y2": 616.49
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4925,
      "bbox": {
        "x1": 189.41,
        "y1": 112.31,
        "x2": 292.83,
        "y2": 200.68
      }
    },
    {
      "class": "freight container",
      "confidence": 0.442,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4302,
      "bbox": {
        "x1": 66.5,
        "y1": 26.28,
        "x2": 579.97,
        "y2": 604.1
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.3983,
      "bbox": {
        "x1": -33.65,
        "y1": 332.6,
        "x2": 591.2,
        "y2": 623.58
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3912,
      "bbox": {
        "x1": 385.56,
        "y1": 259.19,
        "x2": 443.97,
        "y2": 353.46
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3763,
      "bbox": {
        "x1": 69.2,
        "y1": 27.09,
        "x2": 585.2,
        "y2": 604.54
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.3554,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3369,
      "bbox": {
        "x1": 68.31,
        "y1": 31.21,
        "x2": 580.19,
        "y2": 617.09
      }
    },
    {
      "class": "freight container",
      "confidence": 0.336,
      "bbox": {
        "x1": 67.43,
        "y1": 0.08,
        "x2": 590.2,
        "y2": 639.98
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3121,
      "bbox": {
        "x1": 86.26,
        "y1": 137.96,
        "x2": 119.56,
        "y2": 195.91
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3022,
      "bbox": {
        "x1": 62.36,
        "y1": 24.69,
        "x2": 585.23,
        "y2": 612.54
      }
    },
    {
      "class": "forklift",
      "confidence": 0.2997,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2962,
      "bbox": {
        "x1": 65.39,
        "y1": -2.38,
        "x2": 581.43,
        "y2": 637.6
      }
    },
    {
      "class": "freight container",
      "confidence": 0.296,
      "bbox": {
        "x1": 139.48,
        "y1": 23.95,
        "x2": 583.12,
        "y2": 594.45
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2941,
      "bbox": {
        "x1": 198.01,
        "y1": 114.67,
        "x2": 292.07,
        "y2": 152.16
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2936,
      "bbox": {
        "x1": 69.32,
        "y1": -0.8,
        "x2": 590.02,
        "y2": 639.14
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2888,
      "bbox": {
        "x1": 65.66,
        "y1": 3.21,
        "x2": 592.08,
        "y2": 636.1
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.2869,
      "bbox": {
        "x1": -110.38,
        "y1": -281.48,
        "x2": 150.13,
        "y2": 349.62
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2842,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2828,
      "bbox": {
        "x1": -110.38,
        "y1": -281.48,
        "x2": 150.13,
        "y2": 349.62
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2805,
      "bbox": {
        "x1": 335.88,
        "y1": 119.61,
        "x2": 377.08,
        "y2": 196.69
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.279,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2769,
      "bbox": {
        "x1": 61.92,
        "y1": 23.84,
        "x2": 590.17,
        "y2": 612.18
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2652,
      "bbox": {
        "x1": -19.0,
        "y1": 262.85,
        "x2": 620.98,
        "y2": 733.65
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2646,
      "bbox": {
        "x1": 80.2,
        "y1": 39.86,
        "x2": 566.04,
        "y2": 381.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2646,
      "bbox": {
        "x1": 184.63,
        "y1": 24.26,
        "x2": 573.35,
        "y2": 597.92
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2627,
      "bbox": {
        "x1": 86.55,
        "y1": 39.89,
        "x2": 571.69,
        "y2": 341.57
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.2615,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2566,
      "bbox": {
        "x1": 52.3,
        "y1": 24.68,
        "x2": 591.65,
        "y2": 621.14
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2557,
      "bbox": {
        "x1": 65.17,
        "y1": 83.49,
        "x2": 594.22,
        "y2": 623.13
      }
    }
  ],
  "intent": "PRESENCE"
}
```

**Example response (UNKNOWN):**
```json
{
  "answer": "I can only answer questions about the five detected object classes: cardboard box, forklift, freight container, wood pallet, and truck. Please ask about counting, presence, or spatial relationships between these objects.",
  "used_detector": false,
  "confidence": "low",
  "detections": [
    {
      "class": "freight container",
      "confidence": 0.618,
      "bbox": {
        "x1": 83.64,
        "y1": 22.29,
        "x2": 587.44,
        "y2": 601.26
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5429,
      "bbox": {
        "x1": 66.87,
        "y1": 20.91,
        "x2": 529.49,
        "y2": 593.88
      }
    },
    {
      "class": "freight container",
      "confidence": 0.5259,
      "bbox": {
        "x1": 85.39,
        "y1": 20.74,
        "x2": 589.68,
        "y2": 616.49
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4925,
      "bbox": {
        "x1": 189.41,
        "y1": 112.31,
        "x2": 292.83,
        "y2": 200.68
      }
    },
    {
      "class": "freight container",
      "confidence": 0.442,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.4302,
      "bbox": {
        "x1": 66.5,
        "y1": 26.28,
        "x2": 579.97,
        "y2": 604.1
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.3983,
      "bbox": {
        "x1": -33.65,
        "y1": 332.6,
        "x2": 591.2,
        "y2": 623.58
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3912,
      "bbox": {
        "x1": 385.56,
        "y1": 259.19,
        "x2": 443.97,
        "y2": 353.46
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3763,
      "bbox": {
        "x1": 69.2,
        "y1": 27.09,
        "x2": 585.2,
        "y2": 604.54
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.3554,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3369,
      "bbox": {
        "x1": 68.31,
        "y1": 31.21,
        "x2": 580.19,
        "y2": 617.09
      }
    },
    {
      "class": "freight container",
      "confidence": 0.336,
      "bbox": {
        "x1": 67.43,
        "y1": 0.08,
        "x2": 590.2,
        "y2": 639.98
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3121,
      "bbox": {
        "x1": 86.26,
        "y1": 137.96,
        "x2": 119.56,
        "y2": 195.91
      }
    },
    {
      "class": "freight container",
      "confidence": 0.3022,
      "bbox": {
        "x1": 62.36,
        "y1": 24.69,
        "x2": 585.23,
        "y2": 612.54
      }
    },
    {
      "class": "forklift",
      "confidence": 0.2997,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2962,
      "bbox": {
        "x1": 65.39,
        "y1": -2.38,
        "x2": 581.43,
        "y2": 637.6
      }
    },
    {
      "class": "freight container",
      "confidence": 0.296,
      "bbox": {
        "x1": 139.48,
        "y1": 23.95,
        "x2": 583.12,
        "y2": 594.45
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2941,
      "bbox": {
        "x1": 198.01,
        "y1": 114.67,
        "x2": 292.07,
        "y2": 152.16
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2936,
      "bbox": {
        "x1": 69.32,
        "y1": -0.8,
        "x2": 590.02,
        "y2": 639.14
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2888,
      "bbox": {
        "x1": 65.66,
        "y1": 3.21,
        "x2": 592.08,
        "y2": 636.1
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.2869,
      "bbox": {
        "x1": -110.38,
        "y1": -281.48,
        "x2": 150.13,
        "y2": 349.62
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2842,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2828,
      "bbox": {
        "x1": -110.38,
        "y1": -281.48,
        "x2": 150.13,
        "y2": 349.62
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2805,
      "bbox": {
        "x1": 335.88,
        "y1": 119.61,
        "x2": 377.08,
        "y2": 196.69
      }
    },
    {
      "class": "wood pallet",
      "confidence": 0.279,
      "bbox": {
        "x1": -7.65,
        "y1": 180.51,
        "x2": 629.62,
        "y2": 646.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2769,
      "bbox": {
        "x1": 61.92,
        "y1": 23.84,
        "x2": 590.17,
        "y2": 612.18
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2652,
      "bbox": {
        "x1": -19.0,
        "y1": 262.85,
        "x2": 620.98,
        "y2": 733.65
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2646,
      "bbox": {
        "x1": 80.2,
        "y1": 39.86,
        "x2": 566.04,
        "y2": 381.77
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2646,
      "bbox": {
        "x1": 184.63,
        "y1": 24.26,
        "x2": 573.35,
        "y2": 597.92
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2627,
      "bbox": {
        "x1": 86.55,
        "y1": 39.89,
        "x2": 571.69,
        "y2": 341.57
      }
    },
    {
      "class": "cardboard box",
      "confidence": 0.2615,
      "bbox": {
        "x1": 121.61,
        "y1": 125.55,
        "x2": 150.73,
        "y2": 206.54
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2566,
      "bbox": {
        "x1": 52.3,
        "y1": 24.68,
        "x2": 591.65,
        "y2": 621.14
      }
    },
    {
      "class": "freight container",
      "confidence": 0.2557,
      "bbox": {
        "x1": 65.17,
        "y1": 83.49,
        "x2": 594.22,
        "y2": 623.13
      }
    }
  ],
  "intent": "UNKNOWN"
}
```

---

## Confidence Guardrail

All `/ask` responses include a `confidence` field: `high`, `medium`, or `low`.

- `high`: Strong evidence (detection conf ≥ 0.50)
- `medium`: Moderate evidence
- `low`: Insufficient evidence — do not rely on the answer

When confidence is `low`, the answer text explicitly states:
> *"Insufficient information to answer confidently."*
