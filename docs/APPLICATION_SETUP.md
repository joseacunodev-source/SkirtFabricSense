# Local application setup

**Current October22 launch:** use [portable research station-v2](STATION_PACKAGE.md). It includes the app and selected model files, serves the camera-first page and preserves station-v1 rollback. Actual desktop HTTP checks pass; fabric is an explicit unapproved research opt-in and calibrated length remains unavailable. Older launch commands below are dated development history. No new dependencies were installed.

October19: the opt-in localizer-v2/presence-v4 combination passes relative source-domain development criteria and three saved-frame HTTP checks. It is research-only, with13/52 negative false accepts and no physical-camera/Pi acceptance. Use the [current optional launch and limitations](LIVE_AUTOMATIC_PILOT.md); default startup is unchanged. [Evidence](OCT19_RECOVERY.md).

October 17: research-v7 supports optional `--experimental-pose artifacts/models/movenet-lightning-f16-v4` and `--experimental-fabric artifacts/models/fabric-smoke-v1` (fabric requires the localizer flag). These models are separate from the bundle; the default remains unchanged. Fabric output is research-only source appearance; pose does not enable length. [Flags, results and limits](OCT17_NEXT_MILESTONE.md).

October 15 runtime hardening: incompatible localizer preprocessing or threshold is rejected before loading a runtime; input/output tensor counts are checked before indexing. Existing valid model behavior is unchanged. The research-v5 desktop bundle passed saved-frame HTTP checks. [Bundle evidence](OFFLINE_RELEASE.md). A malformed model is a visible load failure, never a silent fallback to guessed preprocessing.

October 12: `--experimental-presence PATH` requires `--experimental-localizer PATH`; the archived presence candidate is not recommended for the normal launch because it loses skirt coverage. `--calibration-profile PATH` validates and loads a profile but does not create an extractor or establish a camera calibration. Fabric has no live-approved model. [Results](OCT12_INTEGRATION.md) and [geometry contract](GEOMETRY_INTEGRATION.md).

**Current camera launch:** use [the automatic camera pilot instructions](LIVE_AUTOMATIC_PILOT.md). The root page submits frames automatically; provisional pleating requires the explicit experimental localizer flag. The saved-image instructions below remain for `/analysis`. `--no-review` skips loading the original review dataset for quicker camera startup. Fabric and calibrated length remain unavailable.

The file-image development app uses the existing WSL training environment. No additional packages were installed for this milestone. It predicts pleated/non-pleated appearance only. Fabric and length remain unavailable; this is not the final automatic live-camera system.

## Launch on the configured laptop

Run this from PowerShell (keep the terminal open):

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --cd /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense --exec /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python -m app.server --bundle artifacts/releases/skirt-finetune-v1-desktop-async-v2 --port 8765
```

Wait for the printed workspace URL, then open http://127.0.0.1:8765 in a browser. Initial startup can take time while TensorFlow loads and the original-image paths are checked through the Windows mount. Stop with Ctrl+C. Relaunch after restarting the laptop; no automatic startup service is installed.

Choose a saved full-skirt image, draw the skirt bounds, confirm that waistband and hem are visible, then analyze. Bounds use source pixels, with a 5% crop margin and the training model's 224-pixel letterbox preprocessing. EXIF orientation is applied before cropping. Changing the image, bounds or confirmation clears the old result. Scores are uncalibrated model outputs, not measured accuracy. Uploaded analysis images are kept in memory and not saved.

## Blind label review

Open the Label review tab. The queue contains the 1,000 original Fashionpedia training candidates and hides prior annotations and predictions. Enter your reviewer name, appearance label, framing observation and visual evidence. Use unknown whenever evidence is inadequate. Saving creates an append-only event in `records/human-review/events.jsonl`; corrections should be another event with explanatory evidence. Identity is self-reported, not authenticated. No submitted event automatically enters training: reconciliation, group review and a new explicit versioned release are required.

Tests use temporary fixtures and must never be counted as human annotation. No protected source validation images appear in this queue.

## Dependencies and packaging

The tested laptop path uses Python 3.12, Pillow, NumPy and TensorFlow's TFLite interpreter already recorded in the training environment. The loader can select installed ai_edge_litert, tflite_runtime or TensorFlow; alternative runtimes are supported code paths, not independently verified installations. TensorFlow currently emits a deprecation warning for its interpreter. Do not copy the GPU training environment onto the Pi.

See [offline release](OFFLINE_RELEASE.md) for building a bundle and the unresolved ARM64 acceptance gates. A dataset-free bundle can serve image analysis; label-review endpoints return an explicit unavailable response. To run the copied application, change into the bundle directory and use a compatible existing interpreter with `python -m app.server --bundle .`. Dataset-free startup is covered by HTTP integration checks; actual clean-machine runtime installation remains unverified.

The HTTP server binds only to 127.0.0.1. It is a local development server without user accounts or production network-service hardening. Application files are inventoried separately from the model manifest. The model and contract hashes are checked at load time. No camera permissions, external assets, uploads to third parties or package installation are required for normal file analysis.

## Validation

```text
python -m unittest tests.test_inference_contract tests.test_review_workflow tests.test_release_builder tests.test_server -q
```

Use an interpreter with the already installed Pillow and NumPy. See the [application evidence](../records/validation/2026-10-05-application.json). No laptop result establishes Raspberry Pi speed, memory use, camera behavior or final classification accuracy.

## Background worker update

The current server/UI use job submission and polling. See [async API, cancellation and limits](ASYNC_APPLICATION.md). The original bundle is retained. Saved-image results stay visible for the unchanged selection; this is not live-camera freshness.

## Camera-first page

The root URL now opens the camera station. Click Start camera to request browser video access. The main view is currently preview-only; classification is not connected. Saved-image analysis remains at `/analysis`. See [camera UI](CAMERA_UI.md).
