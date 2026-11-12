# First skirt pleating baseline — 2026-10-04

The first MobileNetV2 pilot is trained and its float32 TFLite export is verified on the laptop. This is preliminary development evidence, not camera accuracy or Raspberry Pi validation.

## Label preparation completed

All 1,000 skirt candidates received agent visual review. The merged judgments contain 533 non-pleated, 110 pleated and 357 unknown appearances; eight disagreements with earlier reviews were quarantined. Full waistband-to-hem visibility and known appearance left 375 candidates. Seven photos in three suspected repeated-garment groups, plus their existing connected components, were quarantined. Three otherwise eligible candidates were removed, leaving **372** pilot images.

| Split | Non-pleated | Pleated | Total |
|---|---:|---:|---:|
| Training | 232 | 60 | 292 |
| Development validation | 60 | 20 | 80 |

Original split membership is unchanged; the 12 protected seed images were not used. The 372 selected examples have distinct existing connected-group IDs, but these are not 372 independently verified physical garments. All labels still require independent human confirmation. Image collection totals remain 1,512, including the separate 500 fabric candidates.

Evidence: [merged reviews](../data/labels/skirt-visual-reviews-v2.jsonl), [merge report](../data/labels/skirt-visual-reviews-v2.report.json), [frozen baseline manifest report](../data/labels/skirt-baseline-v1.report.json), and [suspected garment groups](../records/review/batch-a/group-candidates.json). Root inspected the grouping comparison and spot-checked review imagery; agents' completion alone was not acceptance. Nine training-contract tests and a hand-calculated metric check passed.

## Experiment

Used the [prespecified protocol](BASELINE_PROTOCOL.md): ImageNet MobileNetV2 frozen backbone, 224-pixel annotated skirt ROI, class-weighted softmax head, Adam 0.001, batch16, seed42, five epochs. The selected checkpoint was **epoch4**, chosen by minimum validation cross entropy. Epochs with higher accuracy were not substituted after seeing the results.

| Metric on 80 validation images | Selected model | Training-majority baseline |
|---|---:|---:|
| Accuracy | 78.75% (63/80) | 75.00% (60/80) |
| Macro F1 | 0.7213 | 0.4286 |
| Pleated precision | 57.14% | 0% |
| Pleated recall | 60.00% (12/20) | 0% |
| Non-pleated recall | 85.00% (51/60) | 100% |

The accuracy improvement is only three images. This small, imbalanced, agent-labelled development set cannot establish reliable deployment performance. The model has learned useful class discrimination relative to the majority baseline, but remains an early pilot.

Confusion matrix (actual rows, predicted columns):

| Actual / predicted | Non-pleated | Pleated |
|---|---:|---:|
| Non-pleated | 51 | 9 |
| Pleated | 8 | 12 |

Five head-training epochs took about 20.9 seconds; this excludes setup, image preparation, weight download and export. TensorFlow reported peak GPU allocator memory of 1,489,161,216 bytes. These measurements are specific to this small frozen-backbone run.

## Export investigation and result

The original run trained successfully but its export gate failed: TensorFlow GPU inference with default TF32 enabled differed from TFLite by up to 0.002425, above the prespecified 0.001 absolute probability tolerance. All 80 predicted classes already agreed. The failure record is retained.

Re-evaluating the **unchanged** checkpoint and export with TensorFlow TF32 disabled reduced the maximum difference to **0.000003159**, passing the same tolerance. All 80 class predictions agreed again. No retraining, label changes, threshold tuning, or tolerance relaxation was used. Future pipeline evaluations explicitly disable TF32. The float32 model is 8,868,352 bytes. Median laptop TFLite invocation time was about 4.67 ms over 79 calls after discarding the first; this is not end-to-end latency or Pi performance.

Evidence: [original training and failed export gate](../records/experiments/20261004-skirt-baseline-v1/run.json), [strict-FP32 verification](../records/experiments/20261004-skirt-baseline-v1/export-fp32-verification.json), [epoch history](../records/experiments/20261004-skirt-baseline-v1/history.json), and [model bundle record](../records/models/2026-10-04-skirt-baseline-v1.json).

## Error review and remaining work

Root visually inspected the [17 error crops](../records/review/baseline-v1-errors.jpg). False positives include smooth flared/A-line skirts with broad drape folds. Missed positives include fine pale pleats, patterned pleats and broad box pleats. These are qualitative hypotheses for subsequent development, not established causal explanations. Some label boundaries still merit human reconciliation. No labels were changed after viewing predictions.

Next priorities are independent annotation checks, camera-domain examples, and a controlled fine-tuning/augmentation comparison on this frozen development split. The model does not detect skirts, estimate length, recognize fabric, calibrate confidence, or operate a live camera. The source annotated ROI must be replaced by a validated automatic method before an end-to-end claim. Raspberry Pi runtime, latency, thermals and accuracy remain unverified.

## Files and reproduction

The local bundle is [model.tflite](../artifacts/models/skirt-baseline-v1/model.tflite), [model.keras](../artifacts/models/skirt-baseline-v1/model.keras), and [input/output contract](../artifacts/models/skirt-baseline-v1/contract.json). Model inputs are RGB float32 values 0–255; normalization is inside the model. Output order is non-pleated then pleated, with uncalibrated scores.

The original executed training-source copy, environment snapshot, dataset, crop coordinates, predictions and history are preserved under `records/experiments/20261004-skirt-baseline-v1`. The working training script now includes the verified TF32 evaluation fix; its hash differs from the archived original. A new invocation must use a new output directory. No new Python dependencies were installed for this run. Downloaded ImageNet weight source/hash is recorded separately in [pretrained-weight acquisition](../records/acquisitions/2026-10-04-mobilenetv2-weights.json). Image and pretrained-weight redistribution rights have not been cleared for publishing this local research model.
