# Presence pilot: trained, exported, not promoted

Reviewed October 12, 2026. The completed October 11 GPU run adds a binary presence gate before the unchanged mask localizer. It does not retrain or improve mask geometry. The paired desktop result loses too much skirt coverage to justify connecting this candidate to the normal live launch.

## Data and training

[Negative review](NEGATIVE_REVIEW.md) admitted 12 of 90 originals: 9 training and 3 development validation, with 78 quarantined. All 90 received contact-sheet review and 22 received original-image inspection; every admitted original was inspected. Rights metadata, uncertain sessions and ambiguous visibility remain conservative exclusion gates. The three validation negatives are one pants, one shorts and one dress image, not a representative negative test set.

The existing 292 positive training and 80 positive validation images were unchanged. [Frozen executed inputs](../records/experiments/20261011-presence-v1/inputs.json) contain 384 images, with no exact-image or group overlap between partitions. These are agent-reviewed development labels; no independent human truth or final test was used. All 90 negative candidates had already appeared in a development diagnostic.

Training used frozen ImageNet MobileNetV2 features, a 64-unit ReLU head, dropout 0.2 and sigmoid output; Adam 0.001, seed 42, batch 16 and 10 epochs. Full RGB originals were resized to 224 × 224 using Pillow bilinear interpolation. Normalization is inside the model. Class weighting used training counts only. Epoch 1 had the minimum class-balanced validation binary cross-entropy. The threshold stayed at 0.5.

[Run and export evidence](../records/experiments/20261011-presence-v1/run.json) records the GPU, environment, hashes and 79.877-second run duration. The gate alone retained 45/80 skirts and rejected 2/3 negatives. Float TFLite export is 9,186,664 bytes; maximum probability difference over all 83 validation images was 0.00000238419, below the predeclared 0.001 tolerance. This is desktop parity, not Raspberry Pi compatibility.

## Paired desktop comparison

[Actual TFLite comparison](../records/validation/2026-10-12-presence-comparison.json) ran both fixed paths on the same 80 skirt and 3 negative validation originals, with original hashes checked. Positive acceptance means a provisional localized ROI that produces a pleating result; it does not establish complete framing or accurate geometry.

| Metric | Existing localizer | Presence gate + existing localizer |
|---|---:|---:|
| Skirt images accepted | 48/80 (60%) | 25/80 (31.25%) |
| Correct pleating among accepted | 38/48 (79.17%) | 19/25 (76%) |
| Correct pleating over all skirts | 38/80 (47.5%) | 19/80 (23.75%) |
| Reviewed negatives rejected | 1/3 | 3/3 |

The additional rejection is accompanied by a loss of 23 accepted skirts and 19 correct pleating outputs. Three negative examples cannot support a reliable general rejection claim. The candidate is archived for reproducibility and remains disabled by default; no threshold adjustment was made to improve these numbers. No webcam, physical garment, fabric, hemline or Pi accuracy follows from this evaluation.

## Archive, audit and reproduction

- [Model directory](../artifacts/models/skirt-presence-v1/) contains Keras, TFLite and the original run record.
- [Experiment archive](../records/experiments/20261011-presence-v1/) contains the original executed source, inputs, predictions, history and environment. SHA256 inventory is in `archive-integrity.json`.
- Model SHA256: `f2ce3e5e405bede28587166dce4d402e73c7d346bea0a4734429e836da4bb1c8`.
- Frozen inputs SHA256: `537574c1172f1c655c8fc24d9894c97563380756507a60861bf5ccb0a24df313`.
- Combined split SHA256: `84a1fa4b07df726e9e5bcd0e1c1b569c532411313893566d3d0a92141778e477`.

Review found that the training script originally trusted a negative's split without independently requiring its explicit admission fields. The actual frozen inputs pass the strengthened checks. Future runs now fail closed on unapproved negatives, unresolved grouping, missing original inspection or a missing no-skirt label. The archived executed source is preserved unchanged; this is a future-run safeguard, not a claim that the original run used revised code. Tests cover approval failure, protected partitions and group leakage.

From the existing WSL training environment, rerun the comparison with a new output filename:

```text
python tools/check_presence_comparison.py --output records/validation/presence-comparison-new.json
python -m unittest tests.test_negative_admission tests.test_presence_training_admission -v
```

No dependency was installed or changed. Next model work needs more rights-documented, unambiguous negative source groups and broader development validation, followed by a fresh candidate and paired comparison. Do not relax quarantine rules, count augmentations as independent specimens, or repeatedly tune against three validation negatives. An improved deployable presence/localization model remains outstanding.
