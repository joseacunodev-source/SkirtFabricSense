# Worn-skirt presence v3 — October 18, 2026

The candidate improves non-skirt rejection but fails the predeclared development coverage criterion. It remains unpromoted. The primary composed candidate (localizer v2 plus presence v3) accepts 39/66 worn skirts versus 41/66 for the experimental localizer v1 baseline. Both paths classify 33 skirts correctly; negative rejection improves from 29/52 to 42/52.

| Path | Accepted worn skirts / 66 | Correct pleating / 66 | Rejected negatives / 52 |
|---|---:|---:|---:|
| Localizer v1 baseline | 41 | 33 | 29 |
| Localizer v2 | 50 | 44 | 21 |
| Localizer v1 + presence v3 | 32 | 24 | 44 |
| Localizer v2 + presence v3 | 39 | 33 | 42 |

These counts were independently recomputed from all 118 saved per-example outputs in the [paired comparison](../records/validation/2026-10-18-detection-candidate.json). Presence and mask thresholds remain 0.5. The standalone presence model accepts 52/66 skirts and rejects 39/52 negatives; composition also depends on localization success. Accepted-result accuracy alone would hide the coverage loss.

## Data and training

The frozen run inputs contain 265 worn positive and 155 negative training images, plus 66 worn positive and 52 negative validation images. These are source images with agent review; physical specimen identity and independent human truth remain unresolved. The [negative admission audit](../records/validation/2026-10-18-negative-v3-admission-audit.json) records the separate review, quarantine and split checks.

The ImageNet MobileNetV2 backbone feeds a 64-unit ReLU layer, dropout of 0.2 and a sigmoid presence output. Training uses seed 42, batch size 8, horizontal flips and class-balanced training weights. Three frozen-backbone head epochs use Adam at 0.001; five fine-tuning epochs use Adam at 0.00001 with block 13 onward trainable, excluding BatchNormalization. BatchNormalization runs in inference mode. Recorded frozen-weight hashes match before/after each phase; the reopened Keras model retains the reported trainable-layer and frozen-BatchNormalization configuration.

Minimum class-balanced validation binary cross-entropy selects epoch 7 in the fine-tuning phase. The worn subset, expanded negatives and optimization changed together, so this is not a controlled single-factor comparison. This validation pool selected the checkpoint and informed candidate comparisons; the results are development evidence, not an independent test or camera accuracy.

## Artifact verification

The [independent artifact review](../records/validation/2026-10-18-presence-v3-artifact-review.json) passed 34 checks: executed source copies, input/split hashes, all 538 original image hashes, disjoint source groups, output membership, phase records, fixed thresholds, recomputed metrics and reopened models. The comparison source is archived alongside the executed training sources; live trainer edits do not redefine v3.

| Artifact | SHA-256 |
|---|---|
| Keras model | `f97a55015bd9160be5f0ad7e7ba965d1040e8fd88faa097fbf6ccb08df919f62` |
| Final float TFLite | `f85607f2c01f83b95217c1a5fa3ec774fadc3c5d3e39bb869e91c13a7213a348` |
| Epoch1 early float export | `6c378913f41c91ce6fe376c5df42f434f506b54980fae061d3eb7df0cc2b6026` |

Both exports contain 9,186,664 bytes. The archived training parity check covers all 118 validation images: early-export maximum absolute error 0.0000020862 and final-export error 0.0000052154 against tolerance 0.001. A separate WSL CPU reopen checked three actual original images against saved Keras/TFLite outputs; the largest error was 0.0000013113. Runtime tensors are one float32 RGB input `[1,224,224,3]` and one float32 output `[1,1]`; RGB bilinear resizing produces values 0–255, with normalization inside the model.

No packages were installed, no new training was performed during this review, and no deployment default changed. No physical camera classification, measured calibration, real garments or Raspberry Pi behavior was verified. Further candidates need to preserve accepted skirt coverage while improving rejection before any promotion decision.
