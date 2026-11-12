# Fine-tuning comparison — 2026-10-04

The controlled candidate improved the same 80-image development-validation result modestly. Both models and all records are preserved; this is not independent test or webcam evidence.

| Metric | Original baseline | Fine-tuned candidate |
|---|---:|---:|
| Correct / total | 63/80 | 65/80 |
| Accuracy | 78.75% | 81.25% |
| Macro F1 | 0.7213 | 0.7540 |
| Pleated precision | 57.14% | 61.90% |
| Pleated recall | 60% | 65% |
| Non-pleated recall | 85% | 86.67% |

The new model corrected four prior errors and introduced two, leaving 15 errors. It was selected at epoch 5 by minimum validation cross entropy (0.35244), following the [prespecified protocol](FINETUNING_PROTOCOL.md). Epoch 3 had higher accuracy but was not substituted after seeing the results. The starting checkpoint was also eligible for selection; the baseline has not been overwritten.

Training continued from the saved baseline on the unchanged 292-image training split. Last 30 backbone layers were unfrozen except BatchNormalization, learning rate 1e-5, batch 8, five epochs, seed 42, with mild horizontal-flip/brightness augmentation. A direct weight comparison verified all frozen layers and BatchNormalization weights stayed unchanged, while ten intended convolution layers and the classifier head changed. Because fine-tuning and augmentation changed together, this experiment does not isolate either one's effect.

Float32 TFLite export passed on all 80 validation examples: maximum absolute probability difference 0.000007689, with 100% class agreement. The model is 8,868,352 bytes. Training took about 27.2 seconds, excluding data preparation and export; TensorFlow peak allocator memory was 1,498,963,456 bytes. TF32 was disabled for this experiment. No packages or runtime versions changed.

Evidence:

- [Run, versions, parameters and source/data hashes](../records/experiments/20261004-skirt-finetune-v1/run.json)
- [Paired comparison and changed predictions](../records/validation/2026-10-04-finetune-comparison.json)
- [Frozen-layer verification](../records/validation/2026-10-04-finetune-weights.json)
- [Model bundle record](../records/models/2026-10-04-skirt-finetune-v1.json)
- [TFLite model](../artifacts/models/skirt-finetune-v1/model.tflite), [Keras model](../artifacts/models/skirt-finetune-v1/model.keras), [input/output contract](../artifacts/models/skirt-finetune-v1/contract.json)

The two-image net gain is not proof of real-world improvement. The same small validation pool has been used for checkpoint/model selection, labels are agent-generated, physical garment identity remains incompletely verified, and ROIs come from source annotations. No fabric/length prediction, live localization, confidence calibration or Raspberry Pi verification is added by this result. Independent human review and new camera-domain garments are more informative next steps than repeatedly optimizing these 80 examples.

The user confirmed no physical skirts are available yet. The [webcam capture guide](WEBCAM_CAPTURE_GUIDE.md) now includes a borrowing-first plan, an initial 8–12 distinct-garment development target, independent label review, tag evidence, calibration and repeatable capture records. The [blank capture template](../templates/garment-capture.json) is documentation, not an implemented capture application or an acquired dataset. No webcam was activated and no local specimens were added.
