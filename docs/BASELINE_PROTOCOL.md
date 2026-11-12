# First pleating baseline protocol

Specified before training, 2026-10-04. This is a development experiment, not final evaluation or a deployment release.

Use the versioned visual-review manifest. Retain only a clear pleated/non-pleated appearance judgment with a complete visible skirt. Source manufacturing labels remain separate. Quarantine review conflicts and suspected repeated garments, including their existing connected components. Preserve the original development train/validation assignments; the 12 protected source-val images are never read by the training script. All selected image hashes are verified before copying into the WSL cache.

Labels in tensor order: `non_pleated`, `pleated`. Pleating means visible constructed repeated pleats; loose folds, gathering or uncertain ruffles are not automatically pleating. Agent labels are provisional visual annotations, not independent human ground truth. Physical garment identity is not fully verified.

Initial model: ImageNet MobileNetV2 alpha 1.0, frozen backbone, global-average pooling, two-way softmax head. Train the head for five epochs with Adam learning rate 0.001, batch size 16, seed 42. Weight training examples inversely by training-class frequency. Use no augmentation in this first reproducible baseline. Select the epoch with minimum development validation cross entropy. Do not tune rejection thresholds or use the protected test pool.

Inputs use the source-annotated skirt bounding box expanded 5% on each side and clipped to the source image. Convert to RGB, bilinear letterbox to 224 by 224 with gray128 padding. The exported model accepts float32 RGB values from 0 to255 and normalizes once to [-1,1]. This annotated ROI is a feasibility aid; live automatic localization has not been implemented. No physical length is inferred from these crops.

Training must have at least ten examples of each class and validation at least five of each. This prevents a degenerate pilot, but is not evidence of statistical adequacy. Report exact class counts, confusion matrix, per-class precision/recall/F1, macro F1 and accuracy. Compare against the training-majority predictor on the identical validation set. Preserve every validation probability and mistake. These are image-level development results; do not describe them as independent-garment or camera accuracy.

Export the selected checkpoint via Keras `model.export` to float32 TFLite built-in operators, fixed batch one. Compare all validation outputs with TensorFlow; prespecified maximum absolute probability difference is 0.001. Record class agreement and post-export metrics. Quantization, webcam behavior and Raspberry Pi execution remain separate future tests.

Every run gets an immutable directory containing source-code copy/hash, dataset/split hashes, environment snapshot, original-to-crop coordinates, seed/parameters, pretrained-weight source/hash, epoch history, selected checkpoint, model files and predictions. Failed runs remain recorded. Model/weight redistribution terms require review before public release; this pilot does not publish source images or weights.
