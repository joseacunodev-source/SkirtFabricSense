"""Read-only inventory of the current interpreter and relevant host tools.

Uses only the standard library. Does not install software or import ML packages.
Reports package availability, not successful GPU/model execution.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


PACKAGES = (
    "tensorflow", "tensorflow-cpu", "tensorflow-intel", "keras", "torch",
    "torchvision", "ai-edge-litert", "tflite-runtime", "numpy", "Pillow",
    "opencv-python", "opencv-python-headless", "scikit-learn", "pandas",
    "matplotlib", "jupyterlab", "ipykernel", "pytest", "PyYAML", "picamera2",
    "pypdf", "pdfplumber",
)


def command(argv: list[str], timeout: int = 15) -> dict:
    executable = shutil.which(argv[0])
    if executable is None:
        return {"command": argv, "status": "not_found"}
    try:
        result = subprocess.run(
            [executable, *argv[1:]], capture_output=True, timeout=timeout,
            check=False,
        )
        def decode(value: bytes) -> str:
            encoding = "utf-16le" if b"\x00" in value[:100] else "utf-8"
            return value.decode(encoding, errors="replace").strip()[:16000]
        return {
            "command": argv, "executable": executable,
            "status": "completed" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "stdout": decode(result.stdout), "stderr": decode(result.stderr),
        }
    except subprocess.TimeoutExpired:
        return {"command": argv, "status": "timeout"}
    except OSError as error:
        return {"command": argv, "status": "error", "error": str(error)}


def collect(role: str) -> dict:
    packages = {}
    for package in PACKAGES:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    result = {
        "schema_version": 1,
        "recorded_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "timezone": "Asia/Manila",
        "environment_role": role,
        "collector_version": "1.0",
        "platform": {"system": platform.system(), "release": platform.release(),
                     "version": platform.version(), "machine": platform.machine()},
        "python": {"version": platform.python_version(), "executable": sys.executable,
                   "prefix": sys.prefix, "base_prefix": sys.base_prefix,
                   "isolated_venv": sys.prefix != sys.base_prefix},
        "package_versions": packages,
        "verification_limits": "Inventory only; no package import, GPU training, model conversion or Pi inference verified.",
        "tools": {
            "git": command(["git", "--version"]),
            "pip_current_interpreter": command([sys.executable, "-m", "pip", "--version"]),
            "nvidia": command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
        },
    }
    if platform.system() == "Windows":
        script = (
            "$c=Get-CimInstance Win32_ComputerSystem; "
            "$p=Get-CimInstance Win32_Processor; "
            "$o=Get-CimInstance Win32_OperatingSystem; "
            "[pscustomobject]@{Model=$c.Model;RAM_GB=[math]::Round($c.TotalPhysicalMemory/1GB,1);"
            "CPU=$p.Name;Cores=$p.NumberOfCores;LogicalProcessors=$p.NumberOfLogicalProcessors;"
            "OS=$o.Caption;Build=$o.BuildNumber;"
            "FreeDiskC_GB=[math]::Round((Get-PSDrive C).Free/1GB,1)}|ConvertTo-Json -Compress"
        )
        result["hardware"] = command(["powershell", "-NoProfile", "-Command", script])
        result["tools"]["wsl"] = command(["wsl", "--list", "--verbose"])
    elif platform.system() == "Linux":
        # Do not read device serials, user environments, network or account configuration.
        os_release = Path("/etc/os-release")
        result["os_release"] = os_release.read_text() if os_release.exists() else None
        cpu_path = Path("/proc/cpuinfo")
        memory_path = Path("/proc/meminfo")
        result["hardware"] = {
            "cpu_summary": [line for line in cpu_path.read_text().splitlines()
                            if line.startswith(("model name", "Hardware", "Model"))][:8]
                           if cpu_path.exists() else [],
            "memory_summary": [line for line in memory_path.read_text().splitlines()
                               if line.startswith(("MemTotal:", "MemAvailable:"))]
                              if memory_path.exists() else [],
            "free_disk_gb": round(shutil.disk_usage(Path.cwd()).free / 2**30, 1),
        }
        result["tools"]["glibc"] = command(["ldd", "--version"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, help="E.g. windows-host, training-wsl, edge-pi")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse accidental overwrites of historical evidence.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(collect(args.role), stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
