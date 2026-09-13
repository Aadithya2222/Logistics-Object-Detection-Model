"""
scripts/upload_to_space.py

Uploads all inference code, configuration, Dockerfile, and weights
to Hugging Face Space Aadithya2201/logistics-object-detection.
"""

import sys
from pathlib import Path
from huggingface_hub import HfApi

ROOT = Path(__file__).parent.parent
REPO_ID = "Aadithya2201/logistics-object-detection"

api = HfApi()

def upload_all():
    print(f"Uploading files to Hugging Face Space: {REPO_ID}")

    files_to_upload = [
        "Dockerfile",
        ".dockerignore",
        "requirements.txt",
        "README.md",
        "LICENSE",
    ]

    for f_name in files_to_upload:
        p = ROOT / f_name
        if p.exists():
            print(f"Uploading file: {f_name}...")
            api.upload_file(
                path_or_fileobj=str(p),
                path_in_repo=f_name,
                repo_id=REPO_ID,
                repo_type="space",
            )

    directories_to_upload = ["app", "weights", "configs", "docs"]

    for d_name in directories_to_upload:
        p = ROOT / d_name
        if p.exists():
            print(f"Uploading directory: {d_name}/...")
            api.upload_folder(
                folder_path=str(p),
                path_in_repo=d_name,
                repo_id=REPO_ID,
                repo_type="space",
                ignore_patterns=["__pycache__/**", "*.pyc", ".pytest_cache/**"],
            )

    print("All files successfully uploaded to Hugging Face Space!")

if __name__ == "__main__":
    upload_all()
