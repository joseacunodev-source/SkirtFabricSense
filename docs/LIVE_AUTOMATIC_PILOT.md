# Automatic camera pilot — October 10, 2026

October22 current configuration: [station-v2 launch/rollback](STATION_PACKAGE.md) supersedes the older commands below. The category gate improves development rejection to42/52 while retaining44 accepted skirts/38 correct pleating. It is research-only; fabric quality, calibrated length and real-camera/Pi acceptance remain open. [Latest integration](OCT22_INTEGRATION.md).

## Optional October19 research configuration

The current research-v7 app can load localizer v2 plus presence v4. The actual118-image export comparison passes the relative development gate, and three saved-frame HTTP cases reproduce it. This remains a research configuration:13/52 development negatives still receive skirt results; calibrated length and accepted fabric recognition are unfinished. [Evidence](OCT19_RECOVERY.md). The dated October10 evaluation below is historical.

From PowerShell in the project directory, using the existing WSL environment:

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --cd /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense --exec /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python -B -m app.server --bundle artifacts/releases/skirt-finetune-v1-desktop-research-v7 --port 8766 --no-review --experimental-localizer artifacts/models/skirt-localizer-v2 --experimental-presence artifacts/models/skirt-presence-v4
```

Open http://127.0.0.1:8766/ and use Start camera when a working camera is available. Stop the server with Ctrl+C. The command loads optional models from the project; it is not a dataset-free Pi installation. Fabric remains unavailable in this launch. Its earlier source-appearance smoke model can be connected only as described in [fabric research evaluation](FABRIC_AUTOMATIC_EVALUATION.md), with its toggle and independent uncertainty; it is not an accepted fabric classifier.

## Historical October10 pilot

The camera page now submits frames automatically to the local worker. Experimental full-frame skirt localization supplies the pleating crop without drawing a box or confirming each frame. Fabric and hemline outputs remain unavailable: no verified fabric model or calibrated geometry adapter exists. This is a development pilot, not a finished classifier.

## Run on the configured laptop

From the project directory in PowerShell:

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --cd /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense --exec /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python -m app.server --bundle artifacts/releases/skirt-finetune-v1-desktop-live-v3 --experimental-localizer artifacts/models/skirt-localizer-v1 --port 8766 --no-review
```

Open http://127.0.0.1:8766/ and choose Start camera. The camera selector becomes available after Stop. The browser requests video only, never audio. Frames go to this loopback app, remain in memory and are not recorded. `/analysis` retains manual saved-image testing. Omit `--no-review` to load the original 1,000-image review queue; loading through the WSL mount can delay startup. Omit `--experimental-localizer` to keep automatic pleating unavailable. The opt-in flag is intentional because rejection of non-skirt inputs is unverified.

No packages were installed for this milestone. The existing isolated WSL TensorFlow runtime supplies TFLite, NumPy and Pillow. The new application bundle contains the pleating model and application; the optional localizer remains a separately hashed research artifact under `artifacts/models/skirt-localizer-v1`. Dependency wheels, a clean Pi installation and physical device benchmarking are not supplied by this bundle.

## Actual model evidence

The [archived run](../records/experiments/20261009-localizer-v1/run.json) used the unchanged 292 training / 80 development-validation originals, official skirt polygons and seed 42. A frozen ImageNet MobileNetV2 feature extractor plus a small mask head trained for ten epochs; epoch 10 was selected by minimum validation weighted binary cross-entropy. Full RGB images are resized to 224×224, with model-internal normalization and a 56×56 skirt-probability output. Every source, split, training script and environment is linked from the [model record](../records/models/2026-10-10-skirt-localizer-v1.json).

| Check | Observed result |
|---|---:|
| Mean development mask IoU | 0.6601 |
| Median mask IoU | 0.6963 |
| Images with mask IoU ≥0.5 | 66/80 |
| TFLite size | 3,048,752 bytes |
| Maximum desktop export difference | 0.00001091; tolerance 0.001 |
| Automatic ROI accepted | 48/80 (60% coverage) |
| Correct pleating among accepted images | 38/48 (79.17%) |
| Correct pleating over all eligible images | 38/80 (47.5%) |

[Automatic-path evaluation](../records/validation/2026-10-10-automatic-pilot.json) includes every validation result. The decoder rejected 23 images with multiple regions and nine with a region touching the frame edge. It uses uncalibrated defaults: probability 0.5, at least nine grid pixels, one connected component, no frame-edge contact. These settings do not establish full-skirt visibility or skirt presence. Three uniform synthetic images abstained; this does not measure false acceptance on real negative scenes. Development images all contain skirts and labels still await independent human review. The earlier 81.25% pleating result used annotated crops and must not be substituted for automatic-path performance.

## Software and camera checks

`POST /api/live` accepts one image plus a boolean `fabric_enabled` and one of `worn`, `hanging`, `mannequin`, `held`. It returns a job ID; `GET /api/jobs?id=...` returns `state`, including `pending` or `complete`. Options and pixels are copied before processing. One active and one replaceable pending frame bound the worker queue. No live request asserts human framing confirmation.

The browser clears old predictions on new acquisition, settings changes, camera interruption and Stop. An acquisition-age limit of 1,000 ms rejects late responses and expires displayed results; timer delays remain possible under browser suspension/load, so physical freshness acceptance is still open. Preview runs independently of inference. One browser tab should control a station; jobs are station-scoped, so another analysis tab supersedes current work.

Root integration passed [156 Python tests](../records/validation/2026-10-10-software-tests-after-http-fix.log). An initial [failed run](../records/validation/2026-10-10-software-tests.log) exposed Windows connection resets when rejecting a request before reading its body. Bounded draining of rejected bodies fixed this, with repeated-request regression coverage. Fourteen mocked browser scenarios cover job polling, deadline expiry, stale completion, permission denial, Stop/disconnect and fabric/presentation changes. These mock tests are not camera accuracy measurements.

An [actual browser connection check](../records/validation/2026-10-10-webcam-connection.json) observed camera-on at 640×480, a live `multiple_regions` response, and camera-off after Stop. The selected browser device label was `Integrated Camera (0c45:64ab)`; the user reports an external webcam and no integrated camera. Physical device identity was not established from that generic label. No frame was saved, no garment truth was available, and no accuracy, focus-quality or latency claim follows from this check.

## Remaining work

Software/data work: acquire and group negative examples; improve automatic localization and assess coverage/false acceptance; independent human review; resolve fabric source partition evidence and acquire/review a full-view appearance subset; train/export an eligible fabric pilot; implement body/garment landmark and calibrated reference adapters; evaluate combined outputs; complete target-specific packaging once the runtime is verified.

Physical acceptance: representative worn/hanging/mannequin/held garments, reference measurements/calibration, camera quality and replacement comparison, Raspberry Pi installation/runtime benchmarks, small-screen checks and sustained operation. Neither a low-quality webcam preview nor a desktop export closes these gates.
