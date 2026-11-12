# Dependency and reproducibility plan

Planning baseline: **1 October 2026, Asia/Manila**; reviewed **2 October 2026**. This directory currently contains a dependency plan, **not an installable or tested lockfile**. Software listed below is proposed unless the project installation ledger separately records successful installation and verification. Documentation tooling already available to Codex is not automatically a project dependency.

## Separate environments

| Environment | Purpose | Isolation and version evidence |
|---|---|---|
| Windows host | Editor, repository, device inspection, optional USB capture | Record Windows build, GPU driver, tools actually used, and host-level changes |
| WSL2 Linux training | GPU training, evaluation, conversion | Proposed; record WSL/distribution/kernel, NVIDIA driver integration, Python and complete environment lock |
| Optional laptop capture environment | Same USB camera capture protocol before Pi arrives | Only if needed outside WSL; record Windows backend, camera controls, and its own Python dependencies |
| Raspberry Pi edge runtime | Camera, preprocessing, model execution, live UI, logs | OS/architecture/system-Python-aware environment; lock only after on-device smoke test |
| Development/test tooling | Data checks, formatting, meaningful unit/integration tests, reports | Keep test/report-only packages outside the final edge environment unless needed for acceptance diagnostics |

The current TensorFlow installation guide supports GPU use through WSL2 on Windows; native-Windows CUDA support ended after TensorFlow 2.10. This justifies the proposed training route, but does not mean WSL or TensorFlow has been installed here. Resolve a currently supported TensorFlow/Python/CUDA pairing during setup and verify a real GPU operation. [TensorFlow installation guide](https://www.tensorflow.org/install/pip).

## Proposed dependency groups

| Group | Candidate components | Selection / documentation requirement |
|---|---|---|
| Training OS/GPU | WSL2, supported Linux distribution, compatible Windows NVIDIA driver | Record exact driver and WSL versions. Follow the selected framework's WSL instructions; avoid adding an unrelated Linux display driver or duplicate CUDA toolkit. |
| Python training | Python, TensorFlow/Keras, converter supplied by the chosen TensorFlow release | Version pending installation and exported-model compatibility tests. Use a single framework baseline first. |
| Data/image processing | NumPy, Pillow, OpenCV where needed | Pin preprocessing behavior and versions; install one OpenCV distribution per environment. |
| Metrics and analysis | scikit-learn, pandas if used, plotting library for reports | Training/evaluation only unless application code actually requires one. |
| Experiment records | Standard-library JSON/CSV/logging, structured configs; TensorBoard if used | Prefer local records first; record seeds, split hashes, data versions, metrics, and model hashes. |
| Dataset acquisition | Standard-library HTTP/download helpers or a selected package; archive readers | Add Kaggle/Hugging Face clients only if a selected source requires them. Credentials remain outside source control. |
| Annotation | Selected desktop/web labeling tool | Decide after label/schema pilot. Record tool version, project export format, label definitions, and annotation provenance. |
| Pi base OS | Raspberry Pi OS 64-bit, stable kernel/firmware, Python/venv, system service/display components | Record exact image plus installed package inventory; OS image alone does not lock later updates. |
| CSI camera route | OS `libcamera`, `rpicam-apps`, `python3-picamera2` and dependencies | Install from matching OS repositories; use system Python and system-site-packages venv. Only if CSI selected. |
| USB camera route | Linux UVC/V4L2, selected OpenCV capture package, `v4l-utils` for diagnostics | Only if USB selected. Record actual modes and device permissions. |
| Pi inference | `ai-edge-litert` candidate; legacy `tflite-runtime` only if a tested alternative | Check Python ABI/ARM64/glibc wheels and operator/API support. Do not install both automatically. |
| UI option A | Local Python service, chosen minimal server package, locally packaged browser UI, kiosk browser | Only if chosen. Build tooling such as Node belongs on the development host; prebuilt assets go to Pi. |
| UI option B | Native UI toolkit and matching display/platform libraries | Only if chosen. Confirm ARM64 packaging and touchscreen/display behavior. |
| Logging/export | Standard-library logging, CSV/JSON, SQLite if needed | Define log retention and export format before adding a database dependency. |
| Tests/tooling | `pytest`, formatter/linter if adopted, license/package inventory tooling | Exact tools pending implementation. Test important split, preprocessing, quantization, stale-result, and release-contract behavior. |
| Optional video diagnostics | FFmpeg or similar only if used | Record command/version and encoding settings so capture artifacts are reproducible. |

See [Pi deployment compatibility gate](../docs/RASPBERRY_PI_DEPLOYMENT.md) for the observed publisher wheel metadata. A published ARM64 wheel is evidence of a possible installation path, not proof that the complete application works.

## Lockfiles to produce after validation

These are planned deliverables; no fake pins or placeholder requirements files should be treated as usable installation instructions.

| Planned artifact | What it must establish |
|---|---|
| Training input requirements | Explicit direct dependencies and supported Python/framework choice |
| Training lock | Exact direct/transitive versions, hashes, platform/Python context, tested resolver/install command |
| Edge input requirements | Only direct application dependencies for the selected camera/runtime/UI route |
| Edge lock | Pi OS/Python/architecture-specific resolved Python packages and hashes; matching camera bindings policy |
| Optional Windows capture lock | Separate dependency set when collecting with the USB camera on Windows |
| OS package manifest | Package names/versions, source repositories, architecture, kernel/firmware and image hash |
| Model environment manifest | Exporter/runtime versions, model/converter settings, operator requirements, golden-input parity results |
| Offline bundle inventory | Approved wheel files and hashes, application/model/assets, license notices, installer/recovery version |

A raw `pip freeze` is useful inventory but does not by itself prove reproducibility: it omits the OS, camera firmware, source artifacts/hashes, and hardware configuration. A CSI environment also sees OS-provided packages; record those separately and avoid resolving a second incompatible copy with pip.

## Installation ledger rule

For **every actual install, upgrade, removal, or setup change**, append to `records/installations.jsonl` and record:

1. Date/time with timezone, host/environment, operator, and purpose.
2. Exact command or installer name; source URL, version, and checksum where applicable.
3. Direct and transitive package inventories before/after as appropriate.
4. Result: succeeded, failed, rolled back, or partially configured; include diagnostic/log path.
5. Verification performed and result. “Installed” is different from “GPU verified,” “Pi import verified,” or “model parity passed.”
6. Effect on lockfiles, model compatibility, startup behavior, and restoration procedure.

Do not present a plan, downloaded installer, or existing unrelated package as a completed project installation. Record rejected approaches briefly so they are not repeated without cause.

After a meaningful environment change, run `tools/collect_environment.py` from that environment and retain its snapshot under `records/environments/`. Use separate roles/records for Windows, WSL training, and Pi deployment; a package found by the Windows interpreter is not evidence that it is installed in WSL or on the Pi. Skills guide the agent and are inventoried in `docs/SKILLS.md`; they are not Python dependencies or packages to copy to the Pi.

## Release-time reproduction checklist

- Resolve packages in a fresh environment appropriate to each host; inspect conflicts and package licenses.
- Run package integrity/dependency checks and project smoke tests.
- Keep any environment variables and required system libraries in the installation instructions; do not store secrets there.
- Record pretrained weight source, license, download hash, and conversion history alongside the software dependencies.
- Rebuild/export from the documented training environment and run the selected models on the Pi.
- Preserve a tested Pi recovery image or complete repeatable reconstruction path, plus an offline application bundle.
- Update documentation and ledger in the same change as implementation. No dependency is “done” until its installation, version, and verification are traceable.

## Installed WSL training lock

[training-wsl-py312.lock.txt](training-wsl-py312.lock.txt) pins all 51 installed package artifacts with SHA-256. Use `python -m pip install --require-hashes -r requirements/training-wsl-py312.lock.txt` inside a fresh Linux x86-64 CPython3.12 venv when reproducing. This is not the Pi lock. [Freeze inventory](training-wsl-py312-freeze.txt) matches the lock; initial install used retained pip reports. Clean reinstallation has not been tested. GPU update and export parity passed in the original environment; see [setup record](../docs/GPU_SETUP.md).
