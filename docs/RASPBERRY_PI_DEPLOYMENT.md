# Raspberry Pi deployment specification

November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.

November 11 review: station-v8/research-v13 is the selected desktop research payload; station-v7 is rollback. The user reconfirms no Pi, webcam or skirts. Start with the [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md). Existing Interpreter loaders, edge preflight and station verification are implemented; clean ARM64 installation, full live benchmarks, service integration and physical acceptance remain unverified. Earlier dated package/runtime notes below are historical candidates, not a current tested Pi lock.

October22 preparation: [station-v2](STATION_PACKAGE.md) supplies a self-contained app/model research payload and tested desktop launch paths. It supplies no dependency wheels, ARM64 lock or physical calibration. On an actual Pi, first establish OS/Python/runtime/operator compatibility and all remaining gates below; desktop HTTP success does not close them. User last confirmed no Pi on October20.

Planning baseline: **1 October 2026, Asia/Manila**; reviewed **2 October 2026**. This is a deployment plan. **No Pi is currently available; none of the installation commands, model smoke tests, or performance checks below has been executed on a Pi.**

## Deployment contract

The target is a standalone, offline station using one full-skirt camera view. Its release contains the inference application, locally stored UI assets, exported models, preprocessing rules, label definitions, thresholds, camera configuration, calibration, and recovery instructions. The laptop retains training dependencies and original datasets; they are not copied indiscriminately to the Pi.

Provisional hardware is Raspberry Pi 5 using its CPU for inference. Do not assume CUDA or desktop GPU delegates exist on this target. See [hardware plan](HARDWARE.md) and [dependency plan](../requirements/README.md).

## OS and runtime compatibility gate

The official Raspberry Pi OS documentation currently identifies **Trixie** as the latest base; Pi 5 also supports Bookworm. Start by evaluating a named **64-bit Raspberry Pi OS desktop image** so camera/display bring-up is straightforward. Record the downloaded image's filename, release date, SHA-256, edition, architecture, and source URL. A Lite image is a later option only if its required graphical components are explicitly installed and tested. [Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html), [Pi 5 OS support](https://www.raspberrypi.com/products/raspberry-pi-5/).

Do not write `pip install tflite-runtime` into a universal installer. Package availability depends on the actual Python ABI, CPU architecture, glibc, and release. Current publisher metadata was inspected without downloading/installing a runtime:

| Candidate | Publisher evidence rechecked on 2 October 2026 | Interpretation |
|---|---|---|
| `ai-edge-litert==2.2.0` | Published wheel `ai_edge_litert-2.2.0-cp313-cp313-manylinux_2_27_aarch64.whl`; uploaded 2026-08-12 | A Python 3.13 ARM64 candidate exists. This is metadata evidence, not a successful Pi install or model execution. |
| `tflite-runtime==2.14.0` | ARM64 release files cover CPython 3.8–3.11 and carry `manylinux_2_34_aarch64` tags | Requires a matching Python ABI and glibc 2.34 or newer; do not assume compatibility with a Python 3.13 OS environment. |

Sources: [LiteRT 2.2.0 publisher metadata](https://pypi.org/pypi/ai-edge-litert/2.2.0/json), [tflite-runtime 2.14.0 publisher metadata](https://pypi.org/pypi/tflite-runtime/2.14.0/json). Metadata SHA-256 for the specific LiteRT CPython 3.13 ARM64 wheel above: `37da7ff26c5c9a3312f1a19d9190cd7d2270aeb65b3ee55a05e1047c5244bdae`. Recheck publisher metadata at installation; this is not a complete dependency lock.

The current LiteRT Python documentation describes CPU execution through `CompiledModel`. A legacy `Interpreter` implementation is a separate candidate and must be verified against the chosen package version; do not silently mix APIs. [Official Python API](https://developers.google.com/edge/litert/next/python). The older embedded Python guide describes `tflite_runtime`, whose published wheel matrix must still be checked. [Official embedded Python guide](https://developers.google.com/edge/litert/microcontrollers/python).

Release gate:

1. Read the Pi's actual OS release, architecture, system Python version, and glibc version.
2. Resolve the chosen runtime and every dependency for that environment, requiring suitable wheels unless a documented source-build route is deliberately chosen.
3. Install in a virtual environment; import the selected API and inspect the model's tensor names, shapes, dtypes, and quantization parameters.
4. Load and invoke a small exported project model using real test inputs. Confirm required operators are supported; prefer the built-in operator set without custom/Flex dependencies for the first deployment.
5. Compare the same inputs with the laptop reference. Account for intentional quantization differences and report prediction/metric changes.
6. Run camera, preprocessing, model, and UI together before locking this combination.
7. Freeze exact versions and hashes only after this passes. If it fails, record the failure and change the runtime/OS/export pairing explicitly; do not replace the OS's Python to force camera bindings to load.

## Installation sequence to implement

These are tasks for the implementation phase, not an existing setup script:

1. Flash the selected image to a verified target card and record the image metadata. Configure device identity, locale/timezone, and maintenance access as needed.
2. Apply standard stable OS package updates; capture the resulting kernel, firmware, package, and repository versions. Avoid experimental firmware as the normal path.
3. Install only the selected camera, runtime, UI, and diagnostic dependencies listed in the dependency plan.
4. Bring up the camera before adding the ML application; verify framing, format, focus, and exposure at the accepted full-skirt mode.
5. Create the app environment, resolve/install its tested lock, and run dependency checks. Keep the system Python intact.
6. Copy a checksummed application/model bundle; validate its manifest and calibration/configuration references.
7. Run functional and sustained-load acceptance checks below.
8. Add autostart and recovery behavior; repeat checks after a cold reboot and while disconnected from the internet.
9. Capture a recovery image and prove restoration to a spare card/device when available.

### Camera-specific packages and environment

For a **CSI camera**, use the supported `libcamera` / `rpicam-apps` / Picamera2 stack. Raspberry Pi recommends installing Picamera2 through APT; a virtual environment should inherit system packages so it can access the OS-provided camera bindings. The legacy `picamera`/`raspistill` stack is not the implementation target. [Camera software](https://www.raspberrypi.com/documentation/computers/camera_software.html), [Picamera2 manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf).

The following Bash commands are **unexecuted examples**, to be adapted to the chosen image and recorded installation procedure:

```bash
# Read-only environment observations.
cat /etc/os-release
uname -m
python3 --version
ldd --version

# Example CSI installation, after OS selection and stable package update.
sudo apt install python3-venv python3-picamera2 rpicam-apps
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Camera enumeration; does not prove inference compatibility.
rpicam-hello --list-cameras
```

For a **USB UVC camera**, use the selected V4L2/OpenCV capture adapter instead. Record camera device identity and supported formats/controls; do not assume `/dev/video0` is stable or that autofocus can be controlled. Picamera2 is not required for that route. A future diagnostic script should enumerate devices with `v4l2-ctl` if installed. Camera access errors must be reported explicitly.

Use one tested source of each binary library. In a system-site-packages environment, record both OS and Python packages and avoid accidentally shadowing the OS NumPy/OpenCV/camera dependencies with incompatible pip versions.

## Required release contents

Names below describe the intended artifact contract; they do not imply those files already exist.

| Artifact | Required contents |
|---|---|
| Release manifest | Application version/commit, build date, target environment ID, file SHA-256 values, model IDs, dependency-lock IDs |
| Model files | Selected `.tflite` exports and format/runtime requirements; model size and operator report |
| Model metadata | Ordered class IDs/names; output meaning; task; expected dimensions and tensor names; input/output dtypes and quantization scales/zero points |
| Preprocessing specification | Camera pixel format and RGB/BGR conversion, rotation/mirroring, resize interpolation, crop/letterbox mapping, normalization, patch selection/aggregation, masking behavior |
| Decision configuration | Per-task thresholds, calibrated confidence transformation if used, stability window, unknown/reject conditions, result expiry |
| Station calibration | Camera mode and parameters, fixture/reference dimensions, geometry mapping, calibration ID/date and uncertainty/validity conditions |
| Validation evidence | Fixed reference inputs with permitted redistribution, expected outputs/tolerances, aggregate accuracy and rejection metrics, timing report |
| Dependency records | OS package inventory and repository configuration; environment lock and wheel hashes; third-party licenses and notices |
| Operations configuration | Startup entry, storage paths/limits, logs, maintenance/export controls, shutdown and camera reconnect behavior |

Preprocessing must be shared or covered by the same reference-input tests across training, laptop preview, and Pi inference. Avoid double normalization or applying signed/unsigned quantization incorrectly.

## Live application behavior

- Keep a bounded latest-frame buffer; a slow model must not accumulate a queue of old frames.
- Link each prediction to its source frame ID, capture timestamp, station calibration ID, and model version. Ignore late results from a removed/replaced garment.
- Generate whole-skirt and fabric-patch inputs from the same frame. Extract fabric patches before downsampling the full frame. Keep background/hem/skin out where the crop policy requires it.
- Run preview and inference independently. Update visible labels only after the configured stability rule; immediately expire invalid/stale results.
- Show explicit camera unavailable, no skirt, poor framing/focus, processing, stable result, and uncertain states. Each attribute may be uncertain independently.
- Bound log/image storage and handle full disk without freezing preview. Save original images only through the documented capture/logging policy.
- Load fonts, scripts, styles, and model files locally. Verify functionality with internet access disabled.

UI implementation remains a design choice: either a lightweight local browser interface or a native graphical application. Choose one after the Pi display/memory test, then record its complete runtime. A browser-based choice needs a local service and kiosk browser; a native choice needs its actual Qt/other toolkit and platform plugins. Do not add both by default.

## Startup, recovery, and maintenance

Provide a tested startup entry appropriate to the selected desktop session. If a local backend is used, manage it separately as a service with restart/backoff and health status; start the display UI after the graphical session is ready. Do not launch a GUI blindly from a root boot service.

Handle camera disconnect, invalid model/configuration, storage failure, and inference exceptions with a visible state and diagnostic log. Restarting must clear old predictions. Keep the previous known-good release so an update can be rolled back; validate hashes before switching releases. Expose a deliberate exit/maintenance path and normal shutdown control for the device operator.

The final installer, smoke-test utility, benchmark runner, startup files, export utility, and recovery instructions must be implemented and versioned. **They are currently planned, not runnable deliverables.**

## Acceptance and evidence

| Check | Evidence to retain |
|---|---|
| Environment reproduction | Clean installation log, package manifests, wheel hashes, exact OS image hash; second install or recovery rehearsal |
| Model parity | Reference-input results and deltas against laptop inference, separately for float and selected quantized export |
| Complete workload | Preview FPS, prediction update rate, p50/p95 frame-to-result latency and age of displayed result, warm-up separately |
| Resource use | Peak resident memory, CPU/thread settings, temperature, power/throttling status, disk usage during sustained operation |
| One-view integrity | Captured frame and mapped skirt/fabric inputs proving all results derive from the same camera view |
| Failure recovery | Removal/replacement of garment, camera disconnect/reconnect where supported, bad model/config, full storage, restart, reboot |
| Offline readiness | Cold boot to working UI without internet; no missing remote assets or attempted model downloads |
| Sustained operation | Proposed minimum 60-minute representative session; repeat timing checks near the end to detect thermal slowdown or memory growth |

Performance numbers must be measured against the provisional targets in [EVALUATION.md](EVALUATION.md), linked by [REQUIREMENTS.md](REQUIREMENTS.md); none are claimed here as achieved. Record camera resolution, model versions, patch count, model input sizes, runtime thread count, display mode, and cooling configuration with every benchmark so runs are comparable.

## Sources and change discipline

The initial source review was recorded on **1 October 2026**. OS documentation, LiteRT API guidance, and both runtime release-file matrices were rechecked on **2 October 2026**. Recheck them at implementation, because current package availability is not a durable lock. Every actual installation/change must update `records/installations.jsonl` with date, host, exact command, package/version, source, reason, result, and rollback/recovery notes where needed. Collect a separate Pi snapshot using `tools/collect_environment.py` after meaningful setup changes; a Windows or WSL snapshot does not describe the Pi.
