"""Install the CI-only dependency and print runner-local provenance to the job log."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]
ROLE = "development-ci-ephemeral"
VERSION = "13.0.0"


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("CI-only installer: run this helper on GitHub Actions, not a local environment")
    command = [sys.executable, "-m", "pip", "install", f"Pillow=={VERSION}"]
    installation = subprocess.run(command, check=False)
    try:
        observed = importlib.metadata.version("Pillow")
    except importlib.metadata.PackageNotFoundError:
        observed = None
    verification_command = [sys.executable, "-c", (
        "from PIL import Image; "
        "assert Image.new('RGB', (2, 2), (10, 20, 30)).getpixel((0, 0)) == (10, 20, 30); "
        "print('Pillow import and RGB image operation passed')"
    )]
    verification = subprocess.run(verification_command, capture_output=True, text=True, check=False)
    snapshot = ROOT / "records" / "environments" / f"ci-{uuid.uuid4().hex}.json"
    snapshot_command = [sys.executable, str(ROOT / "tools" / "collect_environment.py"),
                        "--role", ROLE, "--output", str(snapshot)]
    snapshot_result = subprocess.run(snapshot_command, check=False)
    snapshot_bytes = snapshot.read_bytes() if snapshot.is_file() else None
    succeeded = installation.returncode == 0 and verification.returncode == 0 and observed == VERSION
    event = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "environment_role": ROLE,
        "action": "pip-install",
        "command": command,
        "status": "succeeded" if succeeded else "failed",
        "exit_code": installation.returncode,
        "observed_versions": {"Pillow": observed},
        "verification": {
            "command": verification_command, "exit_code": verification.returncode,
            "stdout": verification.stdout.strip(), "stderr": verification.stderr.strip(),
            "expected_version": VERSION, "version_matches": observed == VERSION,
        },
        "target_environment": {
            "python_executable": sys.executable,
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
            "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
            "source_commit": os.environ.get("GITHUB_SHA"),
        },
        "environment_snapshot": {
            "command": snapshot_command, "exit_code": snapshot_result.returncode,
            "path": snapshot.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(snapshot_bytes).hexdigest() if snapshot_bytes else None,
        },
        "limits": "Ephemeral hosted CI environment; not a local training or Raspberry Pi change. "
                  "Printed job logs expire under GitHub retention; no provenance is committed automatically.",
    }
    ledger = ROOT / "records" / "installations.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(event, ensure_ascii=False)
    with ledger.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(serialized + "\n")
    print("::group::CI installation event (runner-local ledger append)", flush=True)
    print(serialized, flush=True)
    print("::endgroup::", flush=True)
    print("::group::CI environment snapshot", flush=True)
    print(snapshot_bytes.decode("utf-8") if snapshot_bytes else "Snapshot was not created", flush=True)
    print("::endgroup::", flush=True)
    return 0 if succeeded and snapshot_result.returncode == 0 and snapshot_bytes else 1


if __name__ == "__main__":
    raise SystemExit(main())
