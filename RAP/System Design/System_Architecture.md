# System Architecture Specification

## Pipeline Components
1. **Dataset Benchmark:** 2,500 images (1500 train, 500 val, 500 test)
2. **Detector Model:** RT-DETR-L Transformer with 4-stage post-processing
3. **Reasoning Layer:** Intent router and 3-tier confidence floor guardrail
4. **Production Infrastructure:** AWS EC2 t3.small + Terraform + Docker Compose + Nginx
