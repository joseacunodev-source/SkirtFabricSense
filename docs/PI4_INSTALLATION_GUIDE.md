# Raspberry Pi 4 installation guide

Prepared November 18, 2026. This guide installs the **research station**, using a candidate Raspberry Pi OS 64-bit Desktop / Trixie / CPython 3.13 environment. Neither the Pi nor webcam was available for project testing at preparation time. The kit can be prepared and checked on the laptop; successful installation, physical operation and demonstration acceptance must be recorded on the actual Pi.

The station provides one live camera view and experimental skirt-presence/pleating inference. Fabric appearance is an optional, unapproved research feature; calibrated hemline output remains unavailable without validated wearer geometry and calibration. Installing packages does not close those model-quality requirements.

## 1. Prepare the equipment and operating system

Use the selected **Raspberry Pi 4**, a suitable Pi 4 USB-C power supply, a reliable microSD card, cooling/ventilation, one USB UVC webcam, and the Waveshare **5inch HDMI LCD (G), SKU 14447**. Have a keyboard/mouse available during setup. Record the Pi's actual memory size, webcam SKU and display revision rather than assuming them from a shopping plan.

On another computer, use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to select Raspberry Pi 4 and **Raspberry Pi OS (64-bit) with Desktop, based on Trixie**. A human must identify the correct microSD card before writing it: the selected card is erased. Create a normal desktop account and record the image filename/release, source URL and SHA-256. When downloading an image file directly, retain its publisher checksum and verify it before flashing. See [official OS images](https://www.raspberrypi.com/software/operating-systems/).

Boot to the desktop and check in a terminal:

```bash
uname -m
getconf LONG_BIT
python3 --version
cat /etc/os-release
tr -d '\0' < /sys/firmware/devicetree/base/model
```

This kit requires 64-bit ARM userspace, a Pi 4 board identity, Trixie and ordinary system **CPython 3.13**. Record the actual patch version. Stop and review a mismatch; do not replace the operating system's Python or use `--break-system-packages`. Bookworm, 32-bit systems, another Python ABI and other Pi models require a separately prepared and verified profile.

## 2. Connect the display and webcam

With power disconnected, connect Pi 4 HDMI video through the appropriate micro-HDMI cable/adapter to the display, and connect the display's USB touch/data interface according to its actual connector markings and manufacturer power instructions. Connect the one webcam to a Pi USB port. Confirm that power provision remains adequate with both peripherals attached.

The selected LCD's native layout is **800 × 480**, landscape, with USB resistive single-touch input. Verify video, touch position, rotation and physical legibility in the desktop before assessing the application. Use [Waveshare's model-specific guide](https://www.waveshare.com/wiki/5inch_HDMI_LCD_%28G%29) together with [current Raspberry Pi display configuration](https://www.raspberrypi.com/documentation/computers/configuration.html). Older manufacturer examples include legacy display/X11 settings; they are not a verified Trixie configuration. Do not apply an old `config.txt`, FKMS or `LCD-show` block as part of this installation. Preserve the actual display configuration and the result of each change. If 800 × 480 or touch cannot be established under the chosen OS, keep display acceptance open and resolve that configuration before kiosk setup.

## 3. Copy and verify the compact installation kit

Obtain the complete prepared Pi 4 kit folder from the project owner, keeping its files together. It contains the selected station, candidate runtime wheels, hash lock, synthetic model reference, installation tools and this guide. It does **not** need the full laptop training dataset, WSL environment or the 1.8 GB cross-computer asset collection. The supplied wheelhouse alone is about 36 MB; use the kit inventory for its exact total size.

Copy the kit privately by USB/storage to a location such as `Downloads/SkirtFabricSense-pi4-kit-v1`. Copying only the public Git repository does not supply its excluded model/wheel payloads. Dataset/model terms still apply.

Set these variables in the Pi terminal, adjusting only the kit folder if copied elsewhere:

```bash
SKIRT_KIT="$HOME/Downloads/SkirtFabricSense-pi4-kit-v1"
SKIRT_DEST="$HOME/SkirtFabricSense-pi4-v1"
SKIRT_RECORDS="$HOME/skirtfabric-records"
mkdir -p "$SKIRT_RECORDS"
python3 -B "$SKIRT_KIT/tools/pi_kit.py" verify "$SKIRT_KIT"
```

Continue only when verification reports `"status": "passed"`. It checks declared file membership, hashes, station identity, wheel/profile/lock agreement and reference identity. It does not execute ARM64 binaries on the laptop or establish Pi compatibility. Do not edit the kit or place logs inside it.

## 4. Install the operating-system prerequisites and retain records

This step needs access to the configured OS package repositories unless the packages are already supplied. The later Python installation uses the kit's local wheels offline. The required Trixie package names are [python3-venv](https://packages.debian.org/trixie/python3-venv), [chromium](https://packages.debian.org/trixie/chromium) and [v4l-utils](https://packages.debian.org/trixie/v4l-utils). No TensorFlow training stack, OpenCV or Picamera2 package is required for the current browser/USB-camera route.

To log each actual OS preparation command and its outcome, define this Bash helper once in the same terminal:

```bash
skirt_os_step() {
  python3 - "$SKIRT_RECORDS" "$@" <<'PY'
from datetime import datetime, timezone
from pathlib import Path
import json, subprocess, sys, uuid
folder = Path(sys.argv[1]); folder.mkdir(parents=True, exist_ok=True)
command = sys.argv[2:]
log = folder / ("os-step-" + uuid.uuid4().hex + ".log")
with log.open("x", encoding="utf-8") as stream:
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line, end="", flush=True); stream.write(line)
    code = process.wait()
versions = subprocess.run(
    ["dpkg-query", "-W", "python3", "python3-venv", "chromium", "v4l-utils"],
    capture_output=True, text=True)
event = {"recorded_at": datetime.now(timezone.utc).isoformat(),
         "environment_role": "edge-pi4-os", "action": "os-package-preparation",
         "command": command, "status": "succeeded" if code == 0 else "failed",
         "exit_code": code, "log": str(log),
         "observed_package_versions": versions.stdout.strip(),
         "package_query_exit_code": versions.returncode,
         "verification": "Command exit status and dpkg inventory; not model/Pi acceptance"}
with (folder / "installations.jsonl").open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(event) + "\n")
sys.exit(code)
PY
}
skirt_os_step sudo apt-get update &&
skirt_os_step sudo apt-get install -y python3-venv chromium v4l-utils
```

Use this only in an interactive terminal where `sudo` can request the normal account authorization. Keep failed attempts and stop on an unsuccessful command. Then capture the resulting OS environment:

```bash
SKIRT_OS_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
python3 -B "$SKIRT_KIT/tools/collect_environment.py" --role edge-pi4-os \
  --output "$SKIRT_RECORDS/os-environment-$SKIRT_OS_STAMP.json"
```

Record any additional OS updates or driver changes with their real commands and versions as well. This guide does not install experimental firmware or change display drivers automatically.

## 5. Review the installation plan

Run as the **normal desktop user**, without `sudo`:

```bash
python3 -B "$SKIRT_KIT/tools/pi_install.py" plan \
  --kit "$SKIRT_KIT" --destination "$SKIRT_DEST" --records "$SKIRT_RECORDS"
```

The plan must report `planned_not_installed` with an empty blocker list. It checks the target profile and requires a new destination under the current user's home, separate from the immutable kit and records. An existing destination is preserved; choose a new versioned destination instead of overwriting it. A laptop is expected to fail the hardware checks.

Fabric loading is off by default. If intentionally testing the unapproved fabric-appearance model, add `--fabric-research` to **both** the plan and install commands. This is distinct from the on-screen fabric switch: the backend must load the model before that switch can request appearance inference.

## 6. Install into the isolated release directory

```bash
python3 -B "$SKIRT_KIT/tools/pi_install.py" install \
  --kit "$SKIRT_KIT" --destination "$SKIRT_DEST" --records "$SKIRT_RECORDS"
```

The installer copies the verified kit into `$SKIRT_DEST/kit`, creates `$SKIRT_DEST/venv`, and installs only local binary wheels with `--no-index`, `--require-hashes` and the kit's lock. It checks dependencies, records installed versions/environment and runs all four exported models against the synthetic desktop reference in an isolated probe. The probe includes the fabric model even when that optional UI feature is disabled.

A successful result is `installed_model_checks_passed_physical_acceptance_open`. The report deliberately retains `pi_verified: false` and `full_live_acceptance: false`. A failed result is not a usable release: inspect the preserved logs, retain the partial directory, and prepare a new destination after resolving the cause. Do not bypass a hash/ABI/operator/parity failure or silently switch inference packages.

The result prints `records_directory`. Set `SKIRT_RUN` to **that exact directory**, for example the actual `install-YYYYMMDDTHHMMSS-<8hex>` subfolder under `$SKIRT_RECORDS`; do not guess its timestamp. Retain `plan.json`, stage logs, `installed-versions.json`, `environment.json`, `model-probe.json` and `installation-result.json`. The shared ledger is `$SKIRT_RECORDS/installations.jsonl`.

```bash
read -r -p "Paste the records_directory path printed by the installer: " SKIRT_RUN
test -f "$SKIRT_RUN/installation-result.json"
```

## 7. Start the backend in the foreground

Before enabling automatic startup:

```bash
"$SKIRT_DEST/venv/bin/python" -B \
  "$SKIRT_DEST/kit/station/station_package.py" launch \
  "$SKIRT_DEST/kit/station" --port 8766
```

Append `--fabric-research` only for the deliberate research mode described above. Keep this terminal open. In a second terminal, a basic service response can be checked with:

```bash
"$SKIRT_DEST/venv/bin/python" -c \
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8766/api/status', timeout=5).read().decode())"
```

The server is local to the Pi. Opening this address on a different computer would access that computer's loopback interface, not the Pi.

## 8. Give Chromium camera permission and test the actual station

Open Chromium on the Pi's graphical desktop at **http://127.0.0.1:8766/**. Select the connected webcam, press **Start camera**, and grant this local application's camera permission when requested. Do not use fake-camera, camera-permission-bypass or browser-security-disabling flags. Select **Worn by a person** for the primary workflow and keep one complete skirt visible. Length assessment also needs appropriate visible body references and validated calibration; a bounding box alone is insufficient.

Check the actual negotiated frame size, focus at the full-skirt distance, lighting and display legibility. Available UVC devices/modes can be inspected with `v4l2-ctl --list-devices` and `v4l2-ctl --device /dev/videoN --list-formats-ext`, replacing `/dev/videoN` with the observed camera node. Do not assume the first video node is the correct stream.

Exercise Start/Stop, unplug/reconnect, scene changes, unsupported objects, fabric off/on and all touch controls. Stale predictions must clear after capture stops or the scene changes. Appearance labels remain research estimates, model scores are uncalibrated, and unavailable hemline results must not be presented as measured lengths.

The browser rejects a result once it is **1,000 ms old from acquisition**. Pi 4 may invoke the models successfully yet take too long for usable live results. Measure the whole capture/decode/inference/display path, not just the probe's invocation timings. Do not relax this limit silently to claim success.

For a repeatable operator/parity recheck with a fresh output filename:

```bash
SKIRT_PROBE_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
"$SKIRT_DEST/venv/bin/python" -B "$SKIRT_DEST/kit/tools/pi_probe.py" \
  --station "$SKIRT_DEST/kit/station" \
  --reference "$SKIRT_DEST/kit/reference/model-probe.json" \
  --output "$SKIRT_RECORDS/model-probe-$SKIRT_PROBE_STAMP.json" --iterations 3
```

This synthetic probe verifies operators/reference parity; it does not measure classification accuracy or full live-camera performance.

## 9. Enable the backend user service only after foreground checks pass

Press Stop in the camera UI and stop the foreground backend with `Ctrl+C` before starting another backend on port 8766. The installer generates inactive startup files under `SKIRT_RUN`; it does not enable services or desktop autologin.

Inspect `skirtfabric.service` and confirm its `ExecStart` points to the intended new release. If a unit already exists at the destination below, stop and preserve/review that configuration first. For the first installation:

```bash
mkdir -p "$HOME/.config/systemd/user"
cp -n "$SKIRT_RUN/skirtfabric.service" "$HOME/.config/systemd/user/skirtfabric.service"
systemctl --user daemon-reload
systemctl --user cat skirtfabric.service
systemctl --user enable --now skirtfabric.service
systemctl --user status skirtfabric.service
journalctl --user -u skirtfabric.service -n 100 --no-pager
```

This is a user service, normally started with that user's session. No root service or lingering-login policy is enabled. Record the activation command and verify the actual service state, logs and reboot behavior before treating automatic startup as working.

## 10. Test kiosk mode, then configure desktop startup

From the logged-in graphical desktop, test the generated script:

```bash
sh "$SKIRT_RUN/start-skirtfabric-kiosk.sh"
```

It waits up to 60 seconds for the local backend, then opens the station in Chromium with a dedicated persistent browser profile. If the backend remains unavailable, inspect the user-service logs rather than treating the kiosk launch as successful. Grant camera permission in this profile too if it has not already been granted. Press Start camera manually. Keep a keyboard available so `Alt+F4` can close the kiosk for maintenance.

For Trixie/labwc automatic desktop startup, follow [Raspberry Pi's kiosk instructions](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/). Preserve the existing `~/.config/labwc/autostart` content, then add one command containing the **actual absolute path** of `start-skirtfabric-kiosk.sh`, in quotes, followed by `&`. Do not place the temporary shell variable `$SKIRT_RUN` in that file. Retain its generated record directory because the script lives there. The generated `skirtfabric.desktop` is also available for a desktop launcher/autostart mechanism supported by the actual session; configure one startup route, not both. Log out/in or reboot and verify video, touch, backend readiness and the maintenance exit path.

## 11. Recovery and physical acceptance

To stop automatic backend execution:

```bash
systemctl --user disable --now skirtfabric.service
```

Close Chromium and remove/comment only this project's kiosk startup entry through the desktop/editor. Preserve unrelated startup entries, the old release and all installation records. A rollback uses the earlier preserved release's reviewed unit/foreground command; reload the user daemon and verify its logs before resuming. Do not delete or hard-reset a failed installation to conceal the failure.

Before supervised demonstration acceptance, record actual garment results, independent label truth, geometry/calibration, camera settings, LCD/touch behavior, full-frame-age coverage, offline operation, sustained load/temperature/memory, reboot, disconnect recovery and rollback. Follow the project's deployment and supervised-demo acceptance records. The completed installation is the start of that physical validation, not its substitute.

## Rebuilding the kit on the engineering computer

Use a new output directory and the exact station, resolved wheelhouse, candidate lock, synthetic reference and profile recorded in the current project checkpoint:

```text
python -B tools/pi_kit.py build --station STATION_DIRECTORY --wheelhouse WHEELHOUSE_DIRECTORY --lock CANDIDATE_LOCK_FILE --reference DESKTOP_PROBE_JSON --profile PROFILE_JSON --guide docs/PI4_INSTALLATION_GUIDE.md --output NEW_KIT_DIRECTORY
```

Replace the uppercase arguments with actual recorded paths. Verify the resulting kit before transfer. Do not run its ARM64 wheels on an x86 laptop, modify a frozen station, copy training environments to the Pi, or call the candidate lock hardware-tested before actual Pi evidence exists.
