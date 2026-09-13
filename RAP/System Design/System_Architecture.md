# System Architecture Specification

## Pipeline Components
1. **Data Ingestion Engine:** Selective HTTP Range-request streaming
2. **Detector Model:** RT-DETR-L Transformer with Hybrid Encoder
3. **Reasoning Layer:** Intent router and 3-tier confidence guardrail
4. **API Gateway:** FastAPI + Uvicorn + Cloudflare Tunnel
