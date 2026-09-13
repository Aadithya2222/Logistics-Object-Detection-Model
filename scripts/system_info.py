"""
scripts/system_info.py
Collect and print system hardware + software information.
Saves output to artifacts/system_info.txt
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = ARTIFACTS_DIR / "system_info.txt"


def run(cmd: list[str], default="N/A") -> str:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() or default
    except Exception:
        return default


def bytes_to_gb(b) -> str:
    return f"{b / 1e9:.2f} GB"


def collect_info() -> dict:
    info = {}

    # ── OS ────────────────────────────────────────────────────────────────
    info["timestamp"] = datetime.now().isoformat()
    info["os"] = platform.system()
    info["os_release"] = platform.release()
    info["os_version"] = platform.version()
    info["machine"] = platform.machine()
    info["node"] = platform.node()

    # ── Python ────────────────────────────────────────────────────────────
    info["python_version"] = sys.version
    info["python_executable"] = sys.executable

    # ── CPU ───────────────────────────────────────────────────────────────
    info["cpu"] = platform.processor()
    try:
        import psutil
        info["cpu_cores_physical"] = psutil.cpu_count(logical=False)
        info["cpu_cores_logical"] = psutil.cpu_count(logical=True)
        vm = psutil.virtual_memory()
        info["ram_total"] = bytes_to_gb(vm.total)
        info["ram_available"] = bytes_to_gb(vm.available)
        disk = psutil.disk_usage("C:\\")
        info["disk_total_c"] = bytes_to_gb(disk.total)
        info["disk_free_c"] = bytes_to_gb(disk.free)
    except ImportError:
        info["cpu_cores_physical"] = "psutil not installed"
        info["ram_total"] = "psutil not installed"

    # ── GPU ───────────────────────────────────────────────────────────────
    nvidia_smi = run(["nvidia-smi",
                      "--query-gpu=name,memory.total,driver_version,compute_cap",
                      "--format=csv,noheader"])
    info["gpu_info"] = nvidia_smi

    cuda_version_from_nvcc = run(["nvcc", "--version"], "nvcc not found")
    info["nvcc_version"] = cuda_version_from_nvcc

    # ── PyTorch ───────────────────────────────────────────────────────────
    try:
        import torch
        info["torch_version"] = torch.__version__
        info["torch_cuda_available"] = torch.cuda.is_available()
        info["torch_cuda_version"] = torch.version.cuda
        if torch.cuda.is_available():
            info["torch_gpu_name"] = torch.cuda.get_device_name(0)
            info["torch_gpu_vram"] = bytes_to_gb(
                torch.cuda.get_device_properties(0).total_memory
            )
            info["torch_cuda_device_count"] = torch.cuda.device_count()
        else:
            info["torch_gpu_name"] = "CPU only"
            info["torch_gpu_vram"] = "N/A"
    except ImportError:
        info["torch_version"] = "not installed"

    # ── Ultralytics ───────────────────────────────────────────────────────
    try:
        import ultralytics
        info["ultralytics_version"] = ultralytics.__version__
    except ImportError:
        info["ultralytics_version"] = "not installed"

    # ── Other packages ────────────────────────────────────────────────────
    for pkg in ["numpy", "cv2", "PIL", "fastapi", "roboflow"]:
        try:
            mod = __import__(pkg if pkg != "PIL" else "PIL")
            ver = getattr(mod, "__version__", "unknown")
            if pkg == "cv2":
                ver = mod.__version__
            info[f"pkg_{pkg}"] = ver
        except ImportError:
            info[f"pkg_{pkg}"] = "not installed"

    return info


def format_report(info: dict) -> str:
    lines = [
        "=" * 60,
        "SYSTEM INFORMATION",
        f"Generated: {info.get('timestamp', 'N/A')}",
        "=" * 60,
        "",
        "── Operating System ──────────────────────────────────────",
        f"  OS          : {info.get('os')} {info.get('os_release')}",
        f"  OS Version  : {info.get('os_version')}",
        f"  Machine     : {info.get('machine')}",
        f"  Node        : {info.get('node')}",
        "",
        "── Python ───────────────────────────────────────────────",
        f"  Version     : {info.get('python_version')}",
        f"  Executable  : {info.get('python_executable')}",
        "",
        "── CPU ──────────────────────────────────────────────────",
        f"  CPU         : {info.get('cpu')}",
        f"  Cores (P/L) : {info.get('cpu_cores_physical')} / {info.get('cpu_cores_logical')}",
        "",
        "── Memory ───────────────────────────────────────────────",
        f"  RAM Total   : {info.get('ram_total')}",
        f"  RAM Avail   : {info.get('ram_available')}",
        "",
        "── Disk ─────────────────────────────────────────────────",
        f"  Disk Total  : {info.get('disk_total_c')}",
        f"  Disk Free   : {info.get('disk_free_c')}",
        "",
        "── GPU ──────────────────────────────────────────────────",
        f"  nvidia-smi  : {info.get('gpu_info')}",
        f"  nvcc        : {info.get('nvcc_version')}",
        f"  Torch GPU   : {info.get('torch_gpu_name')}",
        f"  VRAM        : {info.get('torch_gpu_vram')}",
        "",
        "── PyTorch ──────────────────────────────────────────────",
        f"  torch       : {info.get('torch_version')}",
        f"  CUDA avail  : {info.get('torch_cuda_available')}",
        f"  CUDA ver    : {info.get('torch_cuda_version')}",
        "",
        "── Ultralytics ──────────────────────────────────────────",
        f"  ultralytics : {info.get('ultralytics_version')}",
        "",
        "── Other Packages ───────────────────────────────────────",
        f"  numpy       : {info.get('pkg_numpy')}",
        f"  opencv      : {info.get('pkg_cv2')}",
        f"  Pillow      : {info.get('pkg_PIL')}",
        f"  fastapi     : {info.get('pkg_fastapi')}",
        f"  roboflow    : {info.get('pkg_roboflow')}",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    info = collect_info()
    report = format_report(info)
    print(report)
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(f"\n[INFO] System info saved to: {OUTPUT_FILE}")
