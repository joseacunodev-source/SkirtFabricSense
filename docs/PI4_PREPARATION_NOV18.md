# Raspberry Pi 4 preparation results - November 18, 2026

The user selected Raspberry Pi 4 and confirmed that the Pi and webcam are still unavailable. The project now has a compact, verified **research installation kit** and [a complete installation guide](PI4_INSTALLATION_GUIDE.md). It is ready for the first hardware installation attempt; an accepted Pi deployment has not been established.

## Delivered kit

The kit wraps the unchanged station-v9 / research-v14. It contains the existing four models, ten candidate ARM64 wheels, a hash-pinned candidate lock, deterministic desktop model outputs, installer/probe/verifier tools, and the standalone guide. Training data and the WSL environment are excluded.

| Item | Actual result |
|---|---|
| Kit folder | `artifacts/pi-kits/skirt-pi4-research-kit-v1` |
| Payload | 50 inventoried payload files; 51 files including inventory; 66,479,739 bytes total |
| Private ZIP | `Downloads/SkirtFabricSense-Pi4/SkirtFabricSense-pi4-kit-v1.zip`, 63,716,791 bytes |
| ZIP SHA-256 | `847ada9552925512d4ee3b6e318662f7aedf3529af109ebe32f5d720f8459d0c` |
| Kit inventory SHA-256 | `65ee2fb89daf2288804e0c594f0974e0acde66329ce285bf222c17d2f1efb896` |
| Candidate environment | Pi OS 64-bit Desktop/Trixie, system CPython 3.13, glibc ≥2.28, LiteRT 2.3.0, NumPy 2.3.5, Pillow 13.0.0 |
| Dependencies | Ten downloaded wheels, 36,111,568 bytes; hashes matched exact publisher metadata |

The ZIP's membership and every expanded member hash were checked. The ZIP, model payloads and binary wheels remain private local transfer files. The public repository carries their code, hashes and records. The earlier full project asset manifest v2 describes the November 12 baseline; this new Pi kit is a separate transfer.

## Software checks completed

- **37 focused tests passed**, zero skips: package identity/tamper checks, wheel/profile/lock consistency, installer platform/path/failure logging, inactive startup configuration and isolated model probe contracts.
- All four existing models invoked successfully on the laptop's existing WSL CPU TensorFlow environment with deterministic synthetic RGB input.
- The copied kit probe repeated those operations and compared all outputs with the desktop reference: all four passed, maximum absolute difference zero on this same desktop runtime.
- The copied installer plan correctly rejected the Windows laptop and created no destination or installation-record directory.
- No local dependency was installed or upgraded. Wheels were downloaded only. No models, labels, source partitions or acceptance thresholds changed.

Evidence: [focused tests](../records/validation/2026-11-18-pi4-preparation-tests.json), [kit build](../records/validation/2026-11-18-pi4-kit-build.json), [desktop reference](../records/validation/2026-11-18-pi-desktop-reference.json), [copied-kit parity](../records/validation/2026-11-18-pi4-kit-desktop-parity.json), [non-target guard](../records/validation/2026-11-18-pi4-non-target-guard.json), [archive verification](../records/validation/2026-11-18-pi4-private-kit-archive.json), [wheel acquisition](../records/acquisitions/2026-11-18-pi4-runtime-wheels/acquisition.json), and [desktop reference environment](../records/environments/20261118-pi4-reference-wsl.json).

## Installation behavior

The installer validates the exact kit and target profile, requires an ordinary desktop user and a new release directory, creates a separate virtual environment, and installs local wheels using `--no-index`, `--only-binary` and `--require-hashes`. It records commands, failures, installed versions and an environment snapshot. Before generating startup files, all four models must invoke in an isolated process and match the desktop reference. Native runtime crashes, timeouts or parity failures produce failed evidence rather than activating a release.

The generated service and kiosk files are inactive until deliberately enabled. The backend binds to loopback. Chromium runs in the graphical user session, waits for backend readiness, and uses normal camera permission and the application's Start camera control. No system Python replacement, root GUI, camera-permission bypass or automatic display-driver change is included.

## Remaining acceptance work

1. Install on the actual Pi 4 and retain its exact RAM/board, OS image, package and runtime records. ARM64 wheel metadata is not proof of native execution.
2. Verify USB capture, focus/full-skirt framing, Waveshare 14447 video and resistive touch, offline startup, failure recovery and reboot behavior.
3. Measure full capture-to-displayed-result latency, memory, temperature and sustained operation. The current 1,000 ms frame-age limit may prevent usable results on a slow Pi 4 even if individual model calls work; do not silently relax it.
4. Complete independent fabric-label review, accepted model-quality evaluation, wearer geometry and measured hemline calibration, followed by unseen-garment tests and a supervised demonstration rehearsal.

The installer and probe retain `pi_verified=false` and `full_live_acceptance=false`. Synthetic model invocation and invocation-only timings do not establish camera accuracy, fabric composition, physical length, live FPS or demonstration acceptance.
