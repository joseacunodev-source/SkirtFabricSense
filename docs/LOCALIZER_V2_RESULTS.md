# Localizer with reviewed negatives — October 14, 2026

The new candidate improves localized skirt coverage and pleating outputs on the frozen positive development set, but **is not promoted** because non-skirt rejection regresses. These are source-image development results, not camera accuracy or readiness for a public demonstration.

## Admission and experiment

Agents inspected all 120 new original images. Root integrated their evidence with prior visual/session flags and the combined duplicate audit. Ambiguous or linked cases were conservatively quarantined; no physical identity or independent human confirmation is claimed. The extension admits 63 new negatives. Together with the earlier 12, it contains **56 training / 19 validation negatives**. Every original v1 row and split is preserved; all 292 positive training / 80 positive validation examples remain unchanged.

[Frozen extension report](../data/labels/negative-reviewed-v2.report.json) binds both review records, source hashes and grouping evidence. Four new tests check incomplete/changed reviews, unresolved links, protected partitions, source terms and preservation of previous assignments.

The GPU run used frozen ImageNet MobileNetV2 block13 features and the existing 56×56 mask head, ten epochs, seed42, batch8, Adam0.001 and horizontal flips. Reviewed negatives receive empty masks. Model selection used equally weighted positive/negative validation losses, with pixel weighting unchanged (skirt5, background1). Threshold0.5 and region decoding stayed fixed. Epoch8 was selected. Training used 348 images; validation used99. [Actual run](../records/experiments/20261014-localizer-v2/run.json).

## Paired exported desktop results

| Metric | Previous localizer | New localizer |
|---|---:|---:|
| Accepted skirt images | 48/80 | 59/80 |
| Correct pleating outputs over all skirts | 38/80 | 52/80 |
| Pleating correct among accepted images | 38/48 (79.17%) | 52/59 (88.14%) |
| Rejected negatives | 10/19 | 8/19 |

The 88.14% figure excludes rejected skirts and does not represent whole-system or webcam accuracy. End-to-end pleating success across all positive development images is52/80 (65%). New candidate false acceptance is11/19 negatives, which is unsuitable evidence for public readiness. The user requested85% project completion, not an accuracy threshold, and none of these figures substitute for that objective.

[Paired comparison](../records/validation/2026-10-14-localizer-v2-comparison.json) preserves each sample's old/new regions and pleating outputs. Mean positive-mask IoU increased from the prior run's0.6601 to0.7161; this still does not establish full-skirt framing or body geometry.

TFLite export is3,048,752bytes, with maximum Keras/TFLite difference0.000005782 on all99 validation images, below0.001 tolerance. [Model record](../records/models/2026-10-14-skirt-localizer-v2.json) and [archive checks](../records/experiments/20261014-localizer-v2/archive-integrity.json) retain source, inputs, environment and file hashes. SavedModel remains in the WSL run directory. No packages were installed.

## Decision and remaining work

Keep the current live launch unchanged. Next detection work must improve non-skirt rejection while preserving useful coverage, followed by an independent camera-domain evaluation. Calibration and automatic geometry, sufficient fabric groups, actual Pi operation and a supervised rehearsal remain outstanding. [Demonstration target](SUPERVISED_DEMO.md). Root's27 focused admission/localization tests passed; [test log](../records/validation/2026-10-14-localizer-v2-tests.log).
