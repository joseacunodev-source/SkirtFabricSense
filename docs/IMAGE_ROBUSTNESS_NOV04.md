# Saved-image robustness diagnostic — November 4

The existing desktop research chain was evaluated on its 118 frozen development-validation images using the unchanged category-presence-v1, localizer-v2 and pleating-v1 exports. Two fixed independent transformations were applied to each original: Pillow brightness factor 0.8 and Gaussian blur radius 1 source pixel. The [protocol](../records/experiments/20261104-image-robustness/protocol.json) and [executed source](../records/experiments/20261104-image-robustness/executed_source.py) were recorded before inference. Every original image hash and the complete frozen input and split identities were checked. No held-out test was used, no model trained, no threshold adjusted and no model promoted.

| Input condition | Skirts accepted | Correct pleating / all skirts | Negatives rejected |
|---|---:|---:|---:|
| Original | 44 / 66 | 38 / 66 | 42 / 52 |
| Brightness × 0.8 | 41 / 66 | 36 / 66 | 41 / 52 |
| Gaussian blur radius 1 | 44 / 66 | 38 / 66 | 40 / 52 |

All 118 original paired chain outputs matched the existing archived comparison. The brightness condition moved three previously correct skirts to unavailable and one previously wrong accepted skirt to correct; two previously rejected negatives became accepted and one prior false accept became rejected. Blur changed individual results even though the aggregate positive counts stayed equal: one correct skirt became unavailable and another unavailable skirt became correct; two previously rejected negatives became falsely accepted. The [full result](../records/experiments/20261104-image-robustness/results.json) preserves the predictions, scores, ROI records, original source/group identities and transition counts.

This is a diagnostic on repeatedly reused, source-domain development images, not a locked test or evidence of camera accuracy. Pixel radius 1 and brightness factor 0.8 are digital operations, not measured autofocus or lighting conditions. Appearance can become less legible after transformation; inherited labels are provisional and not re-reviewed for the transformed views. Different views of one original are not new garments or independent samples. Results do not establish real-world robustness, fabric quality, calibrated length, Raspberry Pi compatibility or a claim that retraining improved accuracy.

The run used the existing WSL desktop CPU environment with TensorFlow 2.20, Pillow and NumPy recorded in its result, with GPU hidden. Three focused tests passed, covering deterministic transform semantics, unavailable-result denominators and paired membership/truth guards. The original-input identity and exported model hashes are pinned in the run. An initial `status.json` was updated to completed after the immutable [completion record](../records/experiments/20261104-image-robustness/completion.json) was created.

Reproduce with the existing WSL interpreter. Use a new versioned output folder or preserve the current one; the script intentionally refuses to overwrite it. Altering transforms or using results to select thresholds constitutes a new development protocol and does not establish independent performance.

```text
python -B -m unittest tests.test_image_robustness -v
python -B tools/evaluate_image_robustness.py
```
