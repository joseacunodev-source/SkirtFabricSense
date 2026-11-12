# Worn-skirt presence v4 — reviewed October 19, 2026

The exported v4 candidate passes the relative development criteria, while remaining experimental and unpromoted. Localizer v2 plus presence v4 accepts **44/66** worn skirts, produces **38/66** correct pleating results and rejects **39/52** non-skirt images. The experimental localizer v1 baseline gives 41, 33 and 29 respectively. These are repeatedly reused source-domain development groups, not independent test or camera accuracy.

| Path | Accepted worn skirts / 66 | Correct pleating / 66 | Rejected negatives / 52 |
|---|---:|---:|---:|
| Localizer v1 baseline | 41 | 33 | 29 |
| Localizer v2 | 50 | 44 | 21 |
| Localizer v1 + presence v4 | 37 | 29 | 41 |
| Localizer v2 + presence v4 | 44 | 38 | 39 |

All 118 outcomes were independently recomputed from the [actual exported-model comparison](../records/validation/2026-10-19-detection-v4-comparison.json). Mask and presence thresholds remain 0.5. The primary chain still misses 22/66 supported skirts and falsely accepts 13/52 negatives. Accepted pleating accuracy is 38/44 (86.36%), with 44/66 (66.67%) coverage; correct available pleating across all skirts is 38/66 (57.58%). Passing this relative experiment gate does not satisfy the broader product targets in [evaluation](EVALUATION.md).

## Selection and data

Training completed on October 18; this independent review and exported-chain comparison completed on October 19, using Asia/Manila dates. The frozen run contains 265 worn positive and 155 negative training images, plus 66 worn positive and 52 negative validation images. Source groups and earlier split assignments remain unchanged. Physical specimen identity and independent human truth remain unresolved; see the [negative admission audit](../records/validation/2026-10-18-negative-v3-admission-audit.json).

The [chain-aware selection protocol](PRESENCE_JOINT_SELECTION_PROTOCOL.md) changes checkpoint selection relative to [v3](PRESENCE_V3_RESULTS.md), preserving its input bytes, seed 42, batch size 8, architecture, preprocessing, augmentation, class weights and optimization schedule. ImageNet MobileNetV2 feeds Dense64 ReLU, dropout 0.2 and a sigmoid presence output. Three frozen-head epochs use Adam at 0.001; five fine-tuning epochs use Adam at 0.00001 with block 13 onward trainable and BatchNormalization frozen in inference mode.

Eligible epochs must preserve baseline accepted skirts and correct pleating while improving negative rejection. Among eligible epochs, selection maximizes negative rejection, then correct pleating, then accepted skirts, then minimizes balanced validation BCE. **Epoch 5** wins with rank `[0,-39,-38,-44,0.4961041212081909]`; no fallback is used. Minimum BCE alone would select epoch 7, which loses coverage. Every epoch's saved rank and eligibility was checked against the declared rule. Unselected epochs retain counts and ranks rather than individual probabilities; those counts were not independently regenerated during this review.

The historical cache supplies only fixed v1/v2 mask acceptance and pleating predictions. Its input, model and archived generator hashes were verified; its old presence probabilities and summary decisions do not select v4. All cached mask outcomes match the new actual-export comparison. The standalone presence model accepts 58/66 skirts and rejects 35/52 negatives, illustrating why the composed chain must be evaluated separately.

The same validation groups motivated this follow-up and selected its checkpoint. This introduces selection optimism. These results do not establish unseen-garment performance or justify moving any final-test sample into training.

## Independent artifact verification

The [artifact review](../records/validation/2026-10-19-presence-v4-artifact-review.json) passed **71 checks**, covering archived executed sources, input/split/cache hashes, all 538 original file hashes, disjoint source groups and file hashes, all validation identities, selection arithmetic, frozen-weight records, model identities, fixed thresholds and all composed metrics. The reopened Keras model retains the reported trainable layers and frozen BatchNormalization; its actual frozen fine-tuning weights match the recorded digest.

| Artifact | SHA-256 |
|---|---|
| Keras model | `124368b0dd22465df4d711c1dc982e1851828beba002c59df700aa26c2d1fd25` |
| Final float TFLite | `7bf9df9b1bacc757956c069f688345ff154ee480a65198ee5948fbe80bbcdb87` |
| Epoch 1 early float export | `6c378913f41c91ce6fe376c5df42f434f506b54980fae061d3eb7df0cc2b6026` |

Both TFLite files contain 9,186,664 bytes. Archived training parity covers all 118 validation originals: early-export maximum absolute error 0.0000020862 and final-export error 0.0000046492, against tolerance 0.001. A separate WSL CPU reopen executed the saved Keras and final TFLite models on **all 118 validation originals**, compared them with each other and the archived outputs, and found maximum absolute error **0.0000039935**. All threshold decisions matched. Early-export parity remains archived training evidence; this review rehashed that export without independently recreating its historical Keras checkpoint.

The reopened runtime is Python 3.12.3, TensorFlow 2.20.0, Keras 3.15.1 and NumPy 2.5.3. The tensor contract is one float32 RGB input `[1,224,224,3]` and one float32 output `[1,1]`. Pillow bilinear resizing supplies values 0–255; normalization is inside the model. WSL CPU execution is desktop evidence only.

No packages were installed, no training occurred during this review, and no deployment default changed. Live camera classification, real garments, measured calibration and Raspberry Pi operation remain unverified. Independent garment evaluation and stronger non-skirt rejection remain necessary before demonstration approval.
