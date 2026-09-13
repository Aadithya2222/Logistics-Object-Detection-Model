"""
scripts/deploy_to_hf.py

Automated script to deploy the Logistics Object Detection & Reasoning API
to Hugging Face Spaces (Docker SDK).
"""

import sys
import time
from pathlib import Path
from huggingface_hub import HfApi

ROOT = Path(__file__).parent.parent
REPO_ID = "Aadithya2201/logistics-object-detection"

api = HfApi()

def deploy():
    print(f"[HF Deploy] Creating/verifying Space repository: {REPO_ID} (sdk=docker)...")
    space_url = api.create_repo(
        repo_id=REPO_ID,
        repo_type="space",
        space_sdk="docker",
        exist_ok=True,
    )
    print(f"[HF Deploy] Space repository ready: {space_url}")

    # Define explicit files/folders required for inference
    included_files = [
        "Dockerfile",
        ".dockerignore",
        "requirements.txt",
        "README.md",
        "LICENSE",
    ]

    included_directories = [
        "app",
        "weights",
        "configs",
        "docs",
    ]

    print("[HF Deploy] Uploading inference code and model weights to Hugging Face...")
    
    # Upload folder with strict ignore patterns to prevent uploading dataset, secrets, or venv
    ignore_patterns = [
        ".venv/**",
        "data/**",
        ".git/**",
        "runs/**",
        ".pytest_cache/**",
        "__pycache__/**",
        "*.pyc",
        ".env*",
        "*.log",
        "RAP/**",
        "artifacts/**",
        "scratch/**",
    ]

    api.upload_folder(
        folder_path=str(ROOT),
        repo_id=REPO_ID,
        repo_type="space",
        ignore_patterns=ignore_patterns,
        delete_patterns=None,
    )

    print(f"[HF Deploy] Upload complete! Waiting for Hugging Face Space build and runtime status...")


if __name__ == "__main__":
    deploy()
