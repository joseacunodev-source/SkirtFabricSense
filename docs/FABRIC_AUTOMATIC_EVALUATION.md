# Automatic fabric appearance smoke evaluation

October 17, 2026, Asia/Manila. This is an observed desktop saved-image experiment. The fabric smoke remains excluded from the default live application and is not approved for deployment.

## What was implemented and checked

`app/fabric.py` adds `FabricSmokePredictor` for the existing archived four-output appearance model only. Loading requires the completed smoke run, exact ordered source-appearance classes, exact recorded preprocessing, unchanged pinned TFLite SHA-256, and one float32 input `[1,224,224,3]` / output `[1,4]`. It rejects invalid, nonfinite or non-softmax output. The adapter uses original source pixels, crops before resizing, and applies the training bilinear aspect-preserving 224 padding with gray128. It does not apply pleating's extra 5% ROI expansion. Integer ROIs outside the source frame fail rather than silently clipping.

Predictions explicitly return `research_only`, uncalibrated scores, `composition_verified=false`, `live_approved=false` and `pi_verified=false`. The archived model, frozen data and splits are unchanged. No dependencies were added.

Five focused tests passed in the existing bundled Windows Python. They exercise native-pixel crop order and padding, invalid ROIs, hash/class/preprocessing mismatches, tensor count/shape/dtype, and invalid runtime scores. These synthetic checks establish contract handling rather than model accuracy.

## Actual paired experiment

The existing WSL TensorFlow2.20.0 / NumPy2.5.3 environment executed the exported smoke model and the exported v1 localizer on the same five frozen fabric development-validation originals. GPU was disabled for this CPU check. Every original, frozen input manifest and split hash was verified. No thresholds or model weights were changed, and no final-test examples were used.

| Path | Predictions available | Matches source annotation | Correct / all five | Accuracy among available | Macro F1 among available |
|---|---:|---:|---:|---:|---:|
| Frozen manually reviewed ROI | 5/5 | 4 | 4/5 | 0.80 | 0.70 |
| Automatic v1 localizer ROI | 4/5 | 3 | 3/5 | 0.75 | 0.6667 |

The automatic path rejected cotton source item `id_00000334` because the unchanged mask decoder found multiple regions. Cotton item `id_00000003`, leather item `id_00002711` and denim item `id_00004513` matched their source labels. Chiffon item `id_00004182` was wrong on both paths: manual crop predicted source cotton appearance, automatic crop predicted source denim appearance. Coverage and correctness therefore both need improvement; completed adapter wiring does not satisfy the product fabric requirement.

The appearance labels are source cotton, denim, leather and chiffon annotations, with unverified composition. Five agent-reviewed source images and one validation example for three classes cannot support generalization or confidence calibration. The localizer's acceptance does not establish genuine skirt presence or full visibility. All seventeen smoke originals were separately reviewed as worn, but this tiny saved-image comparison still provides no live wearer, camera-domain, calibrated geometry, latency or Raspberry Pi evidence.

## Evidence and reproduction

- [Exact predictions, ROIs, scores, versions and hashes](../records/validation/2026-10-17-fabric-automatic.json)
- [Original smoke data and model limitations](FABRIC_PILOT.md)
- [Strict research adapter](../app/fabric.py)
- [Paired evaluation script](../tools/check_fabric_automatic.py)
- [Focused contract tests](../tests/test_fabric_runtime.py)

Use the existing WSL training interpreter from the project root:

```text
python -m unittest tests.test_fabric_runtime -v
python tools/check_fabric_automatic.py --output records/validation/fabric-automatic-new-check.json
```

The evaluation refuses to overwrite an existing report. Next gates remain more independent, rights-compatible, credibly annotated worn-skirt groups, frozen group-preserving evaluation, uncertainty/rejection evaluation and actual garment/Pi validation. An optional research path may use this adapter only with its experimental status preserved; it does not justify enabling fabric by default.

## Explicit optional app path

The source app now accepts `--experimental-fabric artifacts/models/fabric-smoke-v1` together with `--experimental-localizer artifacts/models/skirt-localizer-v1`. Omitting the fabric flag keeps its provider absent and fabric unavailable. This is an explicit research path, not model promotion. It does not enable calibrated length or certify empty-scene rejection.

For an existing compatible desktop runtime, from the project source root:

```text
python -m app.server --bundle artifacts/releases/skirt-finetune-v1-desktop-research-v6 --no-review --experimental-localizer artifacts/models/skirt-localizer-v1 --experimental-fabric artifacts/models/fabric-smoke-v1
```

The UI's fabric switch must also be on. With it off, fabric inference is skipped. Accepted localization passes the original current image and its source-pixel ROI into the fabric adapter, independently of pleating's expanded ROI. A failed fabric provider leaves available pleating intact. Research outputs preserve source appearance labels, unapproved status and the source frame ID. An unavailable localization or rejected presence gate prevents fabric inference.

Seven synthetic integration tests cover these conditions in `tests/test_fabric_integration.py`. These tests and the saved-image results above provide no physical-camera or Pi validation; the unchanged five-image limitations still apply. Immutable older bundles do not acquire source-app changes automatically.
