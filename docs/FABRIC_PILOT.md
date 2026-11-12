# Fabric appearance pipeline smoke

Reviewed and archived October 12, 2026. Training completed October 11 using the existing WSL environment. No packages were installed or changed. **This model is not approved for the live application.**

## Reviewed data and split

The agent reviewed the 25 acquired full-view DeepFashion-MultiModal originals. Eight remain excluded because a top hides the waistband, a handbag obscures the skirt, or a seated lace/net example has ambiguous source chiffon interpretation. Seventeen images from seventeen source item groups are admitted only for an internal pipeline smoke experiment. Source item groups are not independently verified physical garments, and styling, model and background correlations remain.

| Source appearance annotation | Training | Validation | Total |
|---|---:|---:|---:|
| Cotton | 6 | 2 | 8 |
| Denim | 4 | 1 | 5 |
| Leather | 1 | 1 | 2 |
| Chiffon | 1 | 1 | 2 |
| Total | 12 | 5 | 17 |

These words are retained as **source appearance annotations**, not verified fiber composition. The classes are named `source_cotton_appearance`, `source_denim_appearance`, `source_leather_appearance`, and `source_chiffon_appearance`. They do not establish the final product taxonomy. The 500 supplementary texture candidates remain outside this experiment.

Only the original source training partition is used; query and gallery images remain excluded. Each admitted source item has one original image and one manually reviewed skirt ROI. Crops do not increase the specimen count. Deterministic group ranking with seed 42 freezes the development split; no final test is created or consumed.

- [Review and exclusion reasons](../records/review/2026-10-11-fabric-pilot.json)
- [Admitted labels](../data/labels/fabric-pilot-v1.jsonl), SHA-256 `92a80e4f974b9730f4631da75fed99b3f628751c882bfe179b39322d20247523`
- [Frozen split](../data/labels/fabric-pilot-v1-splits.json), SHA-256 `e076033aa293ebad2058cec0ed2395292202f87bec9a78bfe2d350fa38e06c57`
- [Source terms](../records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE): noncommercial research; internal copies at one organization/site; no source dataset redistribution.

## Actual training and export

The CPU-only run used frozen ImageNet MobileNetV2 pooled features and a four-output softmax head. Input is a manually reviewed original-pixel skirt crop, RGB, bilinear aspect-preserving padding to 224×224 with gray 128, float32 pixels 0–255, with normalization inside the model. The head trained ten fixed epochs with Adam 0.001, batch four, seed 42 and inverse-frequency class weights. Validation did not select the checkpoint. The recorded duration was 21.83 seconds in TensorFlow 2.20.0 / NumPy 2.5.3; this is one desktop run, not an inference latency benchmark.

On five development images, four predictions matched the source annotations: accuracy 4/5, macro F1 0.70. The single chiffon image was predicted as cotton. With only one validation item for three classes, **these results do not establish fabric-recognition feasibility or generalization**. The majority baseline was 2/5.

The float TFLite export contains 8,881,248 bytes, SHA-256 `81f144a1c7cd4910989374a1a86c85e955fb4f65cd81ef88c26e7cbcf1158bfd`. Original Keras/export parity had maximum absolute score error 0.000002265 and class agreement on all five images. Reopening the archived Keras and TFLite models on October 12 again passed the unchanged 0.001 tolerance, maximum error 0.000002384, and reproduced the saved predictions within tolerance.

- [Actual run and limitations](../records/experiments/20261011-fabric-smoke-v1/run.json)
- [Environment snapshot](../records/experiments/20261011-fabric-smoke-v1/environment.json)
- [Validation predictions](../records/experiments/20261011-fabric-smoke-v1/validation-predictions.json)
- [Model record and hashes](../records/models/2026-10-12-fabric-smoke-v1.json)
- [Independent archive reopening/parity check](../records/validation/2026-10-12-fabric-desktop-parity.json)
- [Ten passing data/split tests](../records/validation/2026-10-12-fabric-tests.log)

The archived training and preparation sources match their recorded hashes. Models are stored under `artifacts/models/fabric-smoke-v1`; small reproducibility records are in `records/experiments/20261011-fabric-smoke-v1`. The original SavedModel remains in the WSL run directory. Models and source data are not added to the distributable live-app bundle.

## Reproduce checks

From the project root, using the existing WSL training interpreter:

```text
python -m unittest tests.test_fabric_pilot -v
python tools/check_fabric_pilot.py --output records/validation/fabric-desktop-parity-recheck.json
```

To repeat the experiment in a new output directory:

```text
python tools/training/train_fabric_pilot.py --output /home/skirttrain/skirt-fabric-sense/runs/fabric-smoke-reproduction
```

The script refuses an existing output directory. No installation is necessary in the recorded environment. Archived source copies document the original run; dependency or input changes require a new record.

## Remaining admission and product work

More distinct, rights-compatible, source-labelled full-skirt groups are needed, especially leather and chiffon. Resolve the operational taxonomy and obtain independent label confirmation. Keep physical tags/supplier evidence separate from visual appearance when claiming composition. Expand and freeze adequately supported groups before training a candidate for deployment.

Automatic localization-to-fabric cropping, uncertain/unsupported inputs, calibration, real webcam data and all four presentations need separate evaluation. The smoke run uses manual ROIs and proves none of those capabilities. The live fabric toggle remains available, with model-unavailable output until a suitable candidate passes those checks. Raspberry Pi runtime, speed and hardware behavior remain unverified.
