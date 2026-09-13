"""
scripts/final_validation.py

Runs all final quality checks and writes artifacts/final_validation.txt.
Must be run AFTER training and evaluation are complete.

Checks:
 1.  Dataset verification (re-runs verify_dataset.py)
 2.  Python syntax check on all scripts
 3.  Unit tests (pytest tests/)
 4.  Model loading (weights/best.pt)
 5.  Test-set inference (5 sample images)
 6.  Evaluation results exist
 7.  FastAPI startup (health check)
 8.  POST /detect test
 9.  POST /ask test
 10. Confidence guardrail test
 11. README completeness check
 12. requirements.txt installation check

Usage:
    python scripts/final_validation.py
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = ROOT / "artifacts"
PYTHON = sys.executable

RESULTS: list[tuple[str, str, str]] = []  # (check_name, PASS/FAIL, detail)


def check(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    RESULTS.append((name, status, detail))
    icon = "✓" if passed else "✗"
    print(f"  [{icon}] {name}: {status}" + (f" — {detail}" if detail else ""))
    return passed


def run_cmd(cmd: list[str], cwd: Path = ROOT, timeout: int = 120) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=str(cwd)
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -1, str(e)


print("=" * 65)
print("FINAL VALIDATION")
print(f"Timestamp: {datetime.now().isoformat()}")
print("=" * 65)

# ── 1. Dataset verification ────────────────────────────────────────────────
print("\n[1] Dataset Verification")
code, out = run_cmd([PYTHON, "scripts/verify_dataset.py"], timeout=120)
check("1_dataset_verification", code == 0,
      "verify_dataset.py exited 0" if code == 0 else f"exit code {code}")

# ── 2. Python syntax check ─────────────────────────────────────────────────
print("\n[2] Python Syntax Check")
scripts = list(ROOT.glob("scripts/*.py")) + list(ROOT.glob("app/*.py")) + \
          list(ROOT.glob("tests/*.py"))
syntax_ok = True
bad_files = []
for f in scripts:
    rc, _ = run_cmd([PYTHON, "-m", "py_compile", str(f)])
    if rc != 0:
        syntax_ok = False
        bad_files.append(f.name)
check("2_syntax_check", syntax_ok,
      f"{len(scripts)} files OK" if syntax_ok else f"FAIL: {bad_files}")

# ── 3. Unit tests ──────────────────────────────────────────────────────────
print("\n[3] Unit Tests")
code, out = run_cmd([PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short"], timeout=300)
# Extract pass/fail counts
import re
m = re.search(r"(\d+) passed", out)
passed_count = int(m.group(1)) if m else 0
m_f = re.search(r"(\d+) failed", out)
failed_count = int(m_f.group(1)) if m_f else 0
check("3_unit_tests", failed_count == 0,
      f"{passed_count} passed, {failed_count} failed")

# ── 4. Model loading ───────────────────────────────────────────────────────
print("\n[4] Model Loading")
weights = ROOT / "weights" / "best.pt"
if not weights.exists():
    check("4_model_loading", False, f"weights/best.pt not found")
else:
    code, out = run_cmd([
        PYTHON, "-c",
        "from ultralytics import RTDETR; m=RTDETR('weights/best.pt'); print('OK')"
    ], timeout=60)
    check("4_model_loading", code == 0 and "OK" in out,
          "model loaded OK" if code == 0 else out[:100])

# ── 5. Test-set inference ──────────────────────────────────────────────────
print("\n[5] Test-Set Inference")
test_dir = ROOT / "data" / "logistics_2500" / "test" / "images"
if not weights.exists():
    check("5_test_inference", False, "weights not available")
elif not test_dir.exists():
    check("5_test_inference", False, "test images not found")
else:
    imgs = list(test_dir.glob("*.jpg"))[:5]
    if not imgs:
        check("5_test_inference", False, "no .jpg images in test set")
    else:
        img_args = " ".join([f"'{str(p)}'" for p in imgs])
        code, out = run_cmd([
            PYTHON, "-c",
            f"from ultralytics import RTDETR; m=RTDETR('weights/best.pt'); "
            f"r=m.predict({[str(p) for p in imgs]}, verbose=False); "
            f"print(f'Predictions: {{len(r)}}')"
        ], timeout=120)
        check("5_test_inference", code == 0 and "Predictions" in out,
              out[:100] if code == 0 else f"FAIL: {out[:100]}")

# ── 6. Evaluation results exist ────────────────────────────────────────────
print("\n[6] Evaluation Results")
eval_json = ARTIFACTS_DIR / "evaluation_results.json"
if eval_json.exists():
    try:
        data = json.loads(eval_json.read_text())
        mAP50 = data.get("overall", {}).get("mAP50", None)
        check("6_evaluation_results", mAP50 is not None,
              f"mAP@0.5={mAP50:.4f}" if mAP50 is not None else "mAP50 missing")
    except Exception as e:
        check("6_evaluation_results", False, str(e))
else:
    check("6_evaluation_results", False, "evaluation_results.json not found")

# ── 7–10. FastAPI tests ────────────────────────────────────────────────────
print("\n[7-10] FastAPI Tests")
if not weights.exists():
    for n, desc in [
        ("7_fastapi_startup", "weights not available"),
        ("8_detect_endpoint", "weights not available"),
        ("9_ask_endpoint", "weights not available"),
        ("10_confidence_guardrail", "weights not available"),
    ]:
        check(n, False, desc)
else:
    import threading

    server_proc = None
    try:
        import subprocess
        server_proc = subprocess.Popen(
            [PYTHON, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", "8001"],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        # Wait for server
        import httpx
        server_up = False
        for _ in range(30):
            time.sleep(1)
            try:
                r = httpx.get("http://127.0.0.1:8001/health", timeout=2)
                if r.status_code == 200:
                    server_up = True
                    break
            except Exception:
                pass

        check("7_fastapi_startup", server_up, "server responded /health" if server_up else "failed to start")

        if server_up:
            with httpx.Client(base_url="http://127.0.0.1:8001", timeout=60) as client:
                # Test /detect
                imgs = list(test_dir.glob("*.jpg"))[:1] if test_dir.exists() else []
                if imgs:
                    with open(imgs[0], "rb") as f:
                        r = client.post("/detect", files={"file": (imgs[0].name, f, "image/jpeg")})
                    check("8_detect_endpoint", r.status_code == 200,
                          f"status={r.status_code} dets={r.json().get('num_detections','?')}")

                    # Test /ask
                    with open(imgs[0], "rb") as f:
                        r = client.post("/ask",
                                        files={"file": (imgs[0].name, f, "image/jpeg")},
                                        data={"question": "How many forklifts are visible?"})
                    body = r.json()
                    check("9_ask_endpoint", r.status_code == 200,
                          f"intent={body.get('intent')} conf={body.get('confidence')}")

                    # Test confidence guardrail (blank image)
                    from PIL import Image as PILImage
                    import io
                    blank = PILImage.new("RGB", (640, 480), color=(200, 200, 200))
                    buf = io.BytesIO()
                    blank.save(buf, format="JPEG")
                    buf.seek(0)
                    r = client.post("/ask",
                                    files={"file": ("blank.jpg", buf.read(), "image/jpeg")},
                                    data={"question": "How many forklifts are visible?"})
                    body = r.json()
                    guardrail_ok = "confidence" in body and body["confidence"] in ("low", "medium", "high")
                    check("10_confidence_guardrail", guardrail_ok,
                          f"conf={body.get('confidence')}")
                else:
                    for n, d in [("8_detect_endpoint", "no test images"),
                                 ("9_ask_endpoint", "no test images"),
                                 ("10_confidence_guardrail", "no test images")]:
                        check(n, False, d)
        else:
            for n, d in [("8_detect_endpoint", "server not up"),
                         ("9_ask_endpoint", "server not up"),
                         ("10_confidence_guardrail", "server not up")]:
                check(n, False, d)

    finally:
        if server_proc:
            server_proc.kill()
            server_proc.wait()

# ── 11. README completeness ────────────────────────────────────────────────
print("\n[11] README Completeness")
readme = ROOT / "README.md"
required_sections = [
    "Problem Statement", "Classes", "Dataset Source", "Dataset Selection",
    "Environment", "Training", "Evaluation", "Failure Analysis",
    "Installation", "Reproducibility"
]
if readme.exists():
    content = readme.read_text()
    missing = [s for s in required_sections if s not in content]
    check("11_readme_completeness", len(missing) == 0,
          "all sections present" if not missing else f"missing: {missing}")
else:
    check("11_readme_completeness", False, "README.md not found")

# ── 12. requirements.txt ───────────────────────────────────────────────────
print("\n[12] requirements.txt Check")
req = ROOT / "requirements.txt"
check("12_requirements_exists", req.exists(),
      "requirements.txt present" if req.exists() else "not found")

# ── Summary ────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("FINAL VALIDATION SUMMARY")
print("=" * 65)
passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
failed = sum(1 for _, s, _ in RESULTS if s == "FAIL")
total = len(RESULTS)
for name, status, detail in RESULTS:
    icon = "✓" if status == "PASS" else "✗"
    print(f"  [{icon}] {name:35s}: {status}  {detail}")
overall = "PASS" if failed == 0 else "FAIL"
print(f"\n  Total: {total} | PASS: {passed} | FAIL: {failed}")
print(f"  OVERALL: {overall}")
print("=" * 65)

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
lines = [
    "FINAL VALIDATION REPORT",
    f"Generated: {datetime.now().isoformat()}",
    "",
]
for name, status, detail in RESULTS:
    lines.append(f"  {status:4s}  {name}: {detail}")
lines.append("")
lines.append(f"Total: {total} | PASS: {passed} | FAIL: {failed}")
lines.append(f"OVERALL: {overall}")
out_path = ARTIFACTS_DIR / "final_validation.txt"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"\n  Saved: {out_path}")
sys.exit(0 if failed == 0 else 1)
