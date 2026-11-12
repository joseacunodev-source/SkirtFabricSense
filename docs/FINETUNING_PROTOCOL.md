# Controlled fine-tuning candidate — 2026-10-04

Prespecified before execution. Continue the saved first pilot on exactly the same 292 training and 80 development-validation images. Do not relabel examples after seeing model errors. No protected or final-test image is used.

Initialize from the saved baseline checkpoint. Unfreeze the last30 MobileNetV2 backbone layers except BatchNormalization; retain the backbone's inference-mode call so batch statistics stay fixed. Train for five epochs with Adam1e-5, batch8, the existing inverse-frequency training weights and seed42. During training only, randomly flip horizontally with probability0.5 and multiply image brightness by a factor uniformly sampled from0.9 to1.1, clipping to0–255. Preserve full skirt geometry; do not crop or vertically flip. Disable TF32 for this run's training and evaluation to avoid the previous parity discrepancy.

Compare this combined fine-tuning/augmentation candidate to the archived baseline. This is not an ablation isolating either change's effect. Select minimum validation cross entropy among the starting checkpoint (epoch0) and five fine-tuned checkpoints; a worse candidate must not overwrite the original. Keep validation preprocessing unchanged. Save every epoch, selected checkpoint, per-image probabilities and confusion metrics. Verify float TFLite on all80 validation images with the existing0.001 maximum absolute probability tolerance.

Repeated model selection on these80 examples makes them development validation, not an independent test. All original label, garment-identity, manual-ROI, web-domain and Pi limitations remain. Do not present a higher score as proven real-world accuracy. Stop after this single controlled candidate and inspect evidence before expanding the search.
