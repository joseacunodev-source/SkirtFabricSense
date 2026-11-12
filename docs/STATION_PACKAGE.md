# Portable research station package

November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.

November 4 latest: station-v8/research-v13 adds requested camera modes and actual decoded-size reporting; v7 is rollback. The user reconfirmed no Pi or webcam. Fifty-two mocked checks and 12 saved-image HTTP jobs pass; physical camera/display and Pi acceptance remain open. [Camera mode evidence](CAMERA_MODE_NOV04.md).

November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. [Waveshare 14447 layout](LCD_14447_LAYOUT.md).

Updated October22, 2026. Station-v6/research-v11 is selected for desktop research after the reference-inspired UI and startup-error correction; station-v5 is rollback. See [current UI evidence](REFERENCE_UI_OCT22.md). These packages make the camera-first research app and model files portable as one directory. They are not an accepted demonstration, dependency installer or verified Raspberry Pi deployment.

Six immutable packages are retained. Each contains 28 inventoried payload files plus its outer `station-inventory.json`. V1/v2 preserve research-v7; v3 contains research-v8; v4 is an unselected research-v9 intermediate; v5 contains research-v10. All inner apps have 17 payload files. No dataset originals, dependency wheels, GPU environment or measured calibration profile are included.

| Package | Presence model | Actual exported development result | Review/selection state |
|---|---|---|---|
| [Station v1](../artifacts/stations/skirt-research-station-v1/) — built October 20 | Presence v4 | 44/66 accepted skirts, 38 correct pleating, 39/52 negatives rejected | Previous research baseline and rollback; HTTP passed |
| [Station v2](../artifacts/stations/skirt-research-station-v2/) — built October 21 | Category-presence v1, scalar skirt probability | 44/66 accepted skirts, 38 correct pleating, 42/52 negatives rejected | Earlier research baseline |
| [Station v3](../artifacts/stations/skirt-research-station-v3/) — built October22 | Same models as v2 | Same saved development reference; no new accuracy estimate | Research-v8 startup correction;12 HTTP jobs passed; current rollback |
| [Station v4](../artifacts/stations/skirt-research-station-v4/) — built October22 | Same models as v2 | Not reevaluated | Unselected UI intermediate; startup-error regression found before selection; no HTTP acceptance claimed |
| [Station v5](../artifacts/stations/skirt-research-station-v5/) — built October22 | Same models as v2 | Same saved development reference; no new accuracy estimate | Research-v10 reference UI, startup-error fix; 18 lifecycle/21 score cases and 12 HTTP jobs pass; previous research selection |
| [Station v6](../artifacts/stations/skirt-research-station-v6/) — built October22 | Same models as v5 | No new inference run; prior v5 evidence retained | Motion update:18 lifecycle/21 score/6 motion cases; exact served HTML verified; selected |

Station-v3 keeps the [independently reviewed models](CATEGORY_PRESENCE_RESULTS.md) from v2 and corrects camera status during pending playback. V2 and v1 remain intact and hash-verified. The gate's [118-image comparison](../records/validation/2026-10-21-category-presence-comparison.json) reuses the same development groups; the three additional rejected negatives versus v1 do not establish independent generalization. [Current batch evidence](CAMERA_SOURCE_UPDATE_OCT22.md).

| Component | Included version | Launch behavior |
|---|---|---|
| Camera app and pleating | V6: research-v11; older app versions retained / same pleating fine-tune v1 | Served locally; camera starts only when the operator chooses Start camera |
| Skirt localization | Localizer v2 | Required automatic source-frame ROI |
| Presence gate | V1: presence v4; V2/v3/v4/v5/v6: scalar category-presence v1 | Fixed0.5 threshold before downstream localization |
| Fabric appearance | Fabric smoke v1 | Loaded only with `--fabric-research`; browser toggle independently controls each frame |
| Calibrated length | None | Remains unavailable |

Packaging does not itself improve model results or establish camera accuracy. The category-trained model exports only its scalar skirt probability to the existing presence adapter; the UI does not acquire four new garment outputs. The fabric model has only 17 admitted source groups and five validation examples; its labels are `source_*_appearance`, not verified fibre composition. [Previous detection evidence](PRESENCE_V4_RESULTS.md), [category protocol](CATEGORY_PRESENCE_PROTOCOL.md), [fabric limits](FABRIC_AUTOMATIC_EVALUATION.md).

## Launch on this configured laptop

From PowerShell, using the already installed WSL environment:

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --cd /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/artifacts/stations/skirt-research-station-v9 --exec /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python -B station_package.py launch . --port 8766
```

Open http://127.0.0.1:8766/ in the browser. Choose Start camera when a working camera is available. Stop the foreground process with Ctrl+C. Do not start a second server on the same port. The documented command does not install anything or automatically start the webcam.

For rollback, replace `skirt-research-station-v9` with `skirt-research-station-v8` in the `--cd` path. V1 is also retained as the older presence-v4 baseline. Each package keeps its own copied launcher.

To load the unapproved fabric research model, append `--fabric-research` to that command. With the default launch, enabling the browser fabric toggle still reports unavailable because the model is not loaded. With research opt-in, the toggle shows source-appearance results only when the presence/localization path accepts the frame. Fabric errors or disabling it preserve independent pleating results. Length stays unavailable in both configurations.

The package also works with relative paths after relocation, provided a compatible Python/runtime is already installed. In a terminal inside the copied package:

```text
python -B station_package.py verify .
python -B station_package.py launch . --check-only
python -B station_package.py launch . --port 8766
```

These commands do not make an arbitrary Python environment compatible. The runtime observed by the HTTP check is the existing WSL x86-64 TensorFlow environment. Actual ARM64 OS/Python/runtime installation, camera/display operation and performance must be established separately. [Pi gates](RASPBERRY_PI_DEPLOYMENT.md), [read-only edge preflight](EDGE_PREFLIGHT.md).

## Verification and integrity

The [builder/launcher](../tools/station_package.py) verifies the inner release and all included model hashes before copying. It refuses existing output and refuses output nested inside any immutable input bundle/model directory. The outer inventory covers the inner release metadata, copied app, all model/run files, launcher, verifier and `station.json`. Extra files/directories, changed hashes, unsafe paths/links and unsupported verified-Pi or calibrated-length declarations are rejected before launch.

The inventories bind the launcher/verifier versions copied at each build. V1/v2 keep their original code; v3 adds the builder's explicit `--application` option so a verified new app bundle can be selected without changing older releases. The default builder input remains research-v7 for reproducibility. Launchers suppress bytecode output; the server also runs with `-B` and `PYTHONDONTWRITEBYTECODE=1`. Keep packages immutable: save logs/images/caches elsewhere. Hash verification establishes local consistency, not publisher authentication or distribution rights. No third-party images are bundled.

The actual [station-v1 HTTP check](../records/validation/2026-10-21-station-http.json), [station-v2 HTTP check](../records/validation/2026-10-21-station-v2-http.json) and [station-v3 HTTP check](../records/validation/2026-10-22-station-v3-http.json) each passed the following separately:

- Outer station and inner application inventories verified before and after; the package remained unchanged.
- Exact packaged camera HTML served at `/`, with matching SHA256.
- Two accepted skirt originals and one presence-gated negative tested with fabric off/on in both default and fabric-research configurations: 12 HTTP inference jobs.
- Presence decisions/scores, localizer identities/ROIs and pleating labels matched the saved development reference.
- With opt-in, fabric labels and all four scores matched a direct adapter imported from the verified packaged application, using the same original image and unexpanded ROI.
- Disabled, unloaded and gated fabric states remained distinct; style stayed unchanged when toggling fabric and length stayed unavailable.
- Both owned loopback servers stopped afterward; no camera, GPU training or installation was used.

The check observes no fabric model identity/output on gated negatives; it does not instrument internal model call counts. It launches the exact argv produced by the verified launcher directly, so these HTTP results do not separately test wrapper-process shutdown behavior. The verifier's structural `runtime_verified=false` remains intentional; the separate HTTP report records observed desktop execution without asserting Pi compatibility.

Actual commands, versions, CPU environment overrides and adapter/source hashes are in the [v1 execution record](../records/validation/2026-10-21-station-http.execution.json), [v2 execution record](../records/validation/2026-10-21-station-v2-http.execution.json) and [v3 execution record](../records/validation/2026-10-22-station-v3-http.execution.json). Each smoke uses three reused saved originals; repeated jobs are not independent specimens or a new recognition-accuracy estimate, browser webcam session, measured geometry or physical acceptance.

Station-v1 outer inventory SHA256 remains `7e1e8fea3bfbd8d15614b1f457768d8cecb6bec059658079b0f20374e50ab0a4`. Station-v2 outer inventory SHA256 is `19444a4ea1622a26822d795bfccb61c558a27383df3741ed84bbeea1544b38f4`. Both remained unchanged during their HTTP checks. V1 was verified again after building/testing V2.

Station-v3 outer inventory SHA256 is `ec865f2c45a635f7e3abb9fe8bd17dbf0c5b389d47ae110182cf37bee90390f8`; research-v8 inventory SHA256 is `97bbfdfe2405528f6ea42eaa2f66ade161a83537feb9a85f1ef41d174cfe822f`. Root reverified all three stations after v3 HTTP checks. The camera-startup regression is tested against the exact copied v3 HTML.

## Reproduce the HTTP check

Run from the project with the existing WSL interpreter and a new output filename:

```text
python -B tools/check_station_http.py --package artifacts/stations/skirt-research-station-v1 --comparison records/validation/2026-10-19-detection-v4-comparison.json --output records/validation/a-new-station-http-check.json
```

The tool uses private adjacent ports 18820/18821 by default. It refuses an occupied port rather than stopping another application. Reports/logs are written outside the package; previous evidence is never overwritten.

To check station-v2, use its package directory and `records/validation/2026-10-21-category-presence-comparison.json`, with a new output filename. The recorded V2 run used `--port 18822`, giving private ports 18822/18823. Neither run changed the source app, previous releases, package files or installed dependencies.

For station-v3, use its directory with that same comparison and a new output filename. Its recorded run used `--port 18824`. To reproduce v3 construction, first build a new application bundle with `tools/build_release.py --include-app --output <new-app-path>`, then use `tools/station_package.py build --application <new-app-path> --presence artifacts/models/skirt-category-presence-v1 --output <new-station-path>`. Existing output and nested immutable-input paths are refused. Verify and test the new package before selecting it.

For another agent, use the [task board](TASK_BOARD.md) for current acceptance work. A newer training candidate is not automatically substituted into this frozen package. Compare, archive and approve a new research configuration explicitly, then build a new package directory while preserving this one for rollback.

## Latest UI package verification

[Station-v5 HTTP evidence](../records/validation/2026-10-22-station-v5-http.json) and [execution record](../records/validation/2026-10-22-station-v5-http.execution.json) pass the same 12 saved-frame jobs on private ports 18828/18829, with owned test servers stopped and the package unchanged. The loopback review server on 8766 is separate and intentionally remains available with its camera off. Its process/session is recorded in the current continuation pointer. Check for that server before launching another.

Station-v5 inventory SHA256: `4d7b14594fd7c85cc7a4e62bb008beb7c18019378bcce10d0e680495f98b0a7d`. Research-v10 inventory SHA256: `64c91a57f24894b8d5cc406e5629b6359982a28b644755d272437e3f4e0dff7c`. The only application payload changed from research-v8 is `app/static/index.html`; no model or contract changed. Station-v4/research-v9 remains an unselected intermediate and should not be launched for the new UI.

Actual build commands, with existing outputs protected:

```text
python -B tools/build_release.py --include-app --output artifacts/releases/skirt-finetune-v1-desktop-research-v10
python -B tools/station_package.py build --application artifacts/releases/skirt-finetune-v1-desktop-research-v10 --presence artifacts/models/skirt-category-presence-v1 --output artifacts/stations/skirt-research-station-v5
```

These are completed commands, not pending work. Preserve these directories and choose new names for any future changes.

## Current motion package

Station-v6/research-v11 adds [UI motion](UI_MOTION_OCT22.md). Its 28-file inventory verifies and its exact HTML is served on 8766. Models/backend bytes match v5; 18 lifecycle, 21 score and six motion cases pass. No new HTTP model inference run is claimed; the v5 saved-frame evidence remains historical. V5 is rollback; v4 remains unselected.

Station-v6 inventory SHA256: `2089658f98e34db6d68d29f33f0b51a08cb3a6c8ad625e786aab497b4f0191da`. Preserve immutable packages when changing UI code.
