# Localizer v3 controlled scene-balance experiment — October 14, 2026

Pre-run plan: use the exact v2 frozen 292 positive / 56 negative training and
80 positive / 19 negative validation inputs. The single change is image-class
balanced training loss: each scene's pixel-weighted BCE is reduced spatially
before multiplying by its training-derived weight (348/(2*292) positive,
348/(2*56) negative). Validation selection remains the unweighted mean of the
positive and negative class BCE averages. Architecture, seed42, ten epochs,
batch8, Adam0.001, horizontal flips and threshold0.5 remain fixed.

This is one development ablation, with no promise of improvement and no default
application promotion. Compare exported results against both v1 and v2 on the
same 99 validation images. No protected test or physical camera/Pi is involved.
The saved run, predictions and parity determine the outcome below.

## Executed recovery and result — October 15, 2026

The interrupted October 14 folder held only input manifests, environment and
training source. No active training process, history, final run report or model
was found. These files were preserved in the
[interruption archive](../records/experiments/20261014-localizer-v3-interrupted/recovery.json).
The interruption cause is not established. A fresh run used a new directory;
the old run was not overwritten.

[Actual GPU run](../records/experiments/20261015-localizer-v3/run.json) completed
all ten epochs, selecting epoch 9 under the prespecified validation objective.
Its labelled-input SHA-256 is identical to v2:
`018a03dd78549e8a54a18d00116722eb4ffcc5c6208f17ae967e3c6158bd8c0c`.
The recorded training/export phase took 65.13 seconds; this is not inference
latency. No packages were installed. All three scene-balance unit tests passed
in the WSL training environment, including the TensorFlow loss calculation.

## Paired exported development results

| Metric | v1 | v2 | v3 balanced scenes |
|---|---:|---:|---:|
| Accepted skirts | 48/80 | 59/80 | 51/80 |
| Correct pleating outputs across all skirts | 38/80 | 52/80 | 42/80 |
| Correct among accepted skirts | 79.17% | 88.14% | 82.35% |
| Rejected negatives | 10/19 | 8/19 | 5/19 |

The [three-way comparison](../records/validation/2026-10-15-localizer-threeway.json)
joins the saved v2 and fresh v3 exported-runtime evaluations by exact sample ID,
verifying identical input hashes and baseline results on every image. It includes
every one of the 99 development images, with no threshold tuning. The current
v3 mean positive-mask IoU is 0.6427, compared with v2's 0.7161.

**Do not promote v3.** It worsens all three operational counts relative to v2,
and accepts 14/19 non-skirt scenes. A lower training objective does not establish
better rejection under the region decoder. These small, repeatedly used,
agent-reviewed source-domain development groups cannot establish independent
webcam accuracy or supervised demonstration readiness.

Float TFLite export is 3,048,752 bytes; maximum Keras/TFLite absolute difference
is 0.000005707, below the fixed 0.001 tolerance on all 99 validation images.
SHA-256: `ca2c135ede7ee760ac205db0e404fb7246739d1741f8fb43b6296ef3a5c7cc26`.
The [model record](../records/models/2026-10-15-skirt-localizer-v3.json) and
[archive integrity record](../records/experiments/20261015-localizer-v3/archive-integrity.json)
retain the weights, executed source, environment, masks and predictions.
Desktop export parity does not verify Raspberry Pi operation.

Next detection work should examine false-positive regions and expand independently
reviewed negative scene diversity before additional tuning on these same 19
negatives. No actual skirt, camera-domain classification or Pi test occurred.
