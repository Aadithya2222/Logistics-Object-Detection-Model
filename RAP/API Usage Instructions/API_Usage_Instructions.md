# API Usage Instructions

## Base URLs
- **Live Cloudflare Tunnel:** `https://prices-debug-match-twist.trycloudflare.com/`
- **Swagger UI:** `https://prices-debug-match-twist.trycloudflare.com/docs`

## Quick Examples
```bash
# 1. Detect objects
curl -X POST "https://prices-debug-match-twist.trycloudflare.com/detect" \
  -F "file=@photo.jpg"

# 2. Ask question
curl -X POST "https://prices-debug-match-twist.trycloudflare.com/ask" \
  -F "file=@photo.jpg" \
  -F "question=How many forklifts are visible?"
```
