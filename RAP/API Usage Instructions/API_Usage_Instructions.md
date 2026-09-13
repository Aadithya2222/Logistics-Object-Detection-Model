# API Usage Instructions

## Base URLs
- **Live AWS Production Base URL:** `http://13.233.255.22`
- **Interactive Swagger UI Console:** `http://13.233.255.22/docs`
- **Local Docker Fallback:** `http://localhost:7860`

## Endpoint Reference & cURL Examples

### 1. Health Check
```bash
curl -X GET "http://13.233.255.22/health"
```
**Response (200 OK):**
```json
{"status": "ok", "version": "1.0.0", "model_loaded": true}
```

### 2. Supported Classes
```bash
curl -X GET "http://13.233.255.22/classes"
```

### 3. Object Detection (POST /detect)
```bash
curl -X POST "http://13.233.255.22/detect" \
  -F "file=@sample.jpg"
```

### 4. Natural Language Reasoning (POST /ask)
```bash
curl -X POST "http://13.233.255.22/ask" \
  -F "file=@sample.jpg" \
  -F "question=How many freight containers are visible?"
```
