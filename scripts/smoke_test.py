"""
scripts/smoke_test.py

End-to-end API smoke test. Starts uvicorn in a subprocess,
tests /detect and /ask endpoints with real test images,
saves example responses.

Usage:
    python scripts/smoke_test.py
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

DOCS_DIR = ROOT / "docs"
API_BASE = "http://127.0.0.1:8000"
TEST_IMG_DIR = ROOT / "data" / "logistics_2500" / "test" / "images"
RESULTS = []


def start_server() -> subprocess.Popen:
    """Start uvicorn in a subprocess."""
    python = sys.executable
    proc = subprocess.Popen(
        [python, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    # Wait for server to start
    for _ in range(30):
        time.sleep(1)
        try:
            resp = httpx.get(f"{API_BASE}/health", timeout=2)
            if resp.status_code == 200:
                print(f"[Server] Ready at {API_BASE}")
                return proc
        except Exception:
            pass
    proc.kill()
    raise RuntimeError("Server failed to start after 30 seconds")


def get_test_image() -> Path:
    """Return first available test image."""
    for ext in ["*.jpg", "*.jpeg", "*.png"]:
        imgs = list(TEST_IMG_DIR.glob(ext))
        if imgs:
            return imgs[0]
    raise FileNotFoundError(f"No test images in {TEST_IMG_DIR}")


def test_health(client: httpx.Client):
    print("\n-- Test: GET /health ----------------------------")
    resp = client.get("/health")
    assert resp.status_code == 200, f"FAIL: {resp.status_code}"
    print(f"  Status : {resp.status_code}")
    print(f"  Body   : {resp.json()}")
    RESULTS.append(("GET /health", "PASS", resp.json()))


def test_classes(client: httpx.Client):
    print("\n-- Test: GET /classes ---------------------------")
    resp = client.get("/classes")
    assert resp.status_code == 200
    print(f"  Status : {resp.status_code}")
    print(f"  Body   : {resp.json()}")
    RESULTS.append(("GET /classes", "PASS", resp.json()))


def test_detect(client: httpx.Client, img_path: Path):
    print(f"\n-- Test: POST /detect ({img_path.name}) -------------")
    with open(img_path, "rb") as f:
        resp = client.post("/detect", files={"file": (img_path.name, f, "image/jpeg")})
    assert resp.status_code == 200, f"FAIL {resp.status_code}: {resp.text}"
    body = resp.json()
    print(f"  Status     : {resp.status_code}")
    print(f"  Detections : {body['num_detections']}")
    for obj in body["objects"][:3]:
        print(f"    {obj['class']} (conf={obj['confidence']:.3f}) bbox={obj['bbox']}")
    RESULTS.append(("POST /detect", "PASS", body))
    return body


def test_ask(client: httpx.Client, img_path: Path, question: str, label: str):
    print(f"\n-- Test: POST /ask - {label} ---------------------")
    print(f"  Question: {question}")
    with open(img_path, "rb") as f:
        resp = client.post(
            "/ask",
            files={"file": (img_path.name, f, "image/jpeg")},
            data={"question": question},
        )
    assert resp.status_code == 200, f"FAIL {resp.status_code}: {resp.text}"
    body = resp.json()
    print(f"  Intent  : {body.get('intent')}")
    print(f"  Answer  : {body['answer']}")
    print(f"  Conf    : {body['confidence']}")
    RESULTS.append((f"POST /ask [{label}]", "PASS", body))
    return body


def write_api_docs(results: list):
    """Write docs/API.md with example requests and responses."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Find example results
    detect_ex = next((r[2] for r in results if "detect" in r[0].lower()), {})
    ask_count = next((r[2] for r in results if "COUNT" in r[0]), {})
    ask_presence = next((r[2] for r in results if "PRESENCE" in r[0]), {})
    ask_spatial = next((r[2] for r in results if "SPATIAL" in r[0]), {})
    ask_unknown = next((r[2] for r in results if "UNKNOWN" in r[0]), {})

    lines = [
        "# API Documentation",
        "",
        "Base URL: `http://127.0.0.1:8000`",
        "",
        "---",
        "",
        "## Endpoints",
        "",
        "### GET /health",
        "Liveness check.",
        "```bash",
        "curl http://127.0.0.1:8000/health",
        "```",
        f"```json",
        json.dumps({"status": "ok", "version": "1.0.0"}, indent=2),
        "```",
        "",
        "---",
        "",
        "### GET /classes",
        "List the five supported detection classes.",
        "```bash",
        "curl http://127.0.0.1:8000/classes",
        "```",
        "",
        "---",
        "",
        "### POST /detect",
        "",
        "Detect logistics objects in an image.",
        "",
        "**Request:**",
        "```bash",
        "curl -X POST http://127.0.0.1:8000/detect \\",
        '  -F "file=@/path/to/image.jpg"',
        "```",
        "",
        "**Response:**",
        "```json",
        json.dumps(detect_ex, indent=2)[:2000] if detect_ex else '{"objects": [...]}',
        "```",
        "",
        "---",
        "",
        "### POST /ask",
        "",
        "Answer a natural-language question about an image.",
        "",
        "**Request:**",
        "```bash",
        "curl -X POST http://127.0.0.1:8000/ask \\",
        '  -F "file=@/path/to/image.jpg" \\',
        '  -F "question=How many forklifts are visible?"',
        "```",
        "",
        "**Supported intents:**",
        "",
        "| Intent | Example question |",
        "|--------|-----------------|",
        '| COUNT | "How many forklifts are visible?" |',
        '| PRESENCE | "Is there a truck?" |',
        '| LIST | "What objects are in the image?" |',
        '| MOST_COMMON | "What is the most common object?" |',
        '| SPATIAL | "Is the forklift near the pallet?" |',
        '| UNKNOWN | "What is the weather?" (unsupported — safe response) |',
        "",
        "**Example response (COUNT):**",
        "```json",
        json.dumps(ask_count, indent=2) if ask_count else "{}",
        "```",
        "",
        "**Example response (PRESENCE):**",
        "```json",
        json.dumps(ask_presence, indent=2) if ask_presence else "{}",
        "```",
        "",
        "**Example response (UNKNOWN):**",
        "```json",
        json.dumps(ask_unknown, indent=2) if ask_unknown else "{}",
        "```",
        "",
        "---",
        "",
        "## Confidence Guardrail",
        "",
        "All `/ask` responses include a `confidence` field: `high`, `medium`, or `low`.",
        "",
        "- `high`: Strong evidence (detection conf ≥ 0.50)",
        "- `medium`: Moderate evidence",
        "- `low`: Insufficient evidence — do not rely on the answer",
        "",
        "When confidence is `low`, the answer text explicitly states:",
        '> *"Insufficient information to answer confidently."*',
        "",
    ]

    out_path = DOCS_DIR / "API.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[INFO] API docs saved: {out_path}")


def main():
    print("=" * 65)
    print("SMOKE TEST — Logistics Object Detection & Reasoning API")
    print("=" * 65)

    img_path = get_test_image()
    print(f"Test image: {img_path}")

    server_proc = None
    try:
        server_proc = start_server()

        with httpx.Client(base_url=API_BASE, timeout=60) as client:
            test_health(client)
            test_classes(client)
            test_detect(client, img_path)

            # Test 7 question types
            test_ask(client, img_path, "How many forklifts are visible?", "COUNT")
            test_ask(client, img_path, "How many trucks are in the image?", "COUNT")
            test_ask(client, img_path, "Is there a forklift?", "PRESENCE")
            test_ask(client, img_path, "Is a freight container present?", "PRESENCE")
            test_ask(client, img_path, "What objects are in the image?", "LIST")
            test_ask(client, img_path, "What is the most common object?", "MOST_COMMON")
            test_ask(client, img_path, "Is the forklift near the pallet?", "SPATIAL")
            test_ask(client, img_path, "What is the weather like?", "UNKNOWN")
            test_ask(client, img_path, "Is there more than one truck?", "PRESENCE")
            test_ask(client, img_path, "How many pallets are visible?", "COUNT")

    except Exception as e:
        print(f"\n[FAIL] {e}")
        RESULTS.append(("smoke_test", "FAIL", str(e)))
    finally:
        if server_proc:
            server_proc.kill()
            server_proc.wait()
            print("\n[Server] Stopped.")

    # Write API docs
    write_api_docs(RESULTS)

    # Summary
    print("\n" + "=" * 65)
    print("SMOKE TEST SUMMARY")
    passed = sum(1 for r in RESULTS if r[1] == "PASS")
    failed = sum(1 for r in RESULTS if r[1] == "FAIL")
    for name, status, _ in RESULTS:
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"  {icon} {name}: {status}")
    print(f"\n  PASSED: {passed} | FAILED: {failed}")
    print("=" * 65)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
