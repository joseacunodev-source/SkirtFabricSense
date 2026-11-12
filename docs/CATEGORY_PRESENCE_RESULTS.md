# Category-aware presence candidate — October 21, 2026

The exported category-aware candidate preserves v4's aggregate skirt coverage and correct pleating while rejecting three additional negatives on the same development groups. Localizer v2 plus the new gate accepts **44/66** skirt examples, gives **38/66** correct pleating results and rejects **42/52** negatives. V4 gives 44, 38 and 39 respectively. This is a research improvement on repeatedly reused source-domain development data, not independent camera accuracy or demonstration approval.

| Actual exported path | Accepted skirts / 66 | Correct pleating / 66 | Rejected negatives / 52 |
|---|---:|---:|---:|
| Experimental localizer v1 baseline | 41 | 33 | 29 |
| Localizer v2 without presence | 50 | 44 | 21 |
| Localizer v2 + presence v4 | 44 | 38 | 39 |
| Localizer v2 + category-aware presence v1 | **44** | **38** | **42** |

All 118 outcomes were recomputed from the [actual exported-model comparison](../records/validation/2026-10-21-category-presence-comparison.json). Both mask and scalar presence thresholds remain 0.5. The new path still falsely accepts 10/52 negatives and makes 22/66 skirt examples unavailable. Accepted pleating accuracy remains 38/44 (86.36%) at 44/66 (66.67%) coverage; overall correct available pleating remains 38/66 (57.58%). These do not satisfy the broader [product acceptance targets](EVALUATION.md).

## Inputs and experiment

The [declared protocol](CATEGORY_PRESENCE_PROTOCOL.md) changes the presence head and supervision while preserving the frozen 538 originals, source groups and splits: 265 worn positive/155 negative training images and 66 positive/52 negative validation images. No source holdout or final-test image was moved into fitting. The derived target file binds each original, group, split, category and source annotation IDs separately from the unchanged binary inputs.

The fixed category order is `skirt_present`, `no_skirt_pants`, `no_skirt_shorts`, `no_skirt_dress`. These are hierarchical source scene targets. A positive scene may contain other clothing; the negative auxiliary category comes from publisher annotations joined to provisional skirt-absence review. It is not independent human-confirmed physical garment truth.

Training retains seed 42, batch size 8, MobileNetV2 with internal normalization, Dense64 ReLU, dropout 0.2 and training-only horizontal flips. The head is softmax4 with sparse categorical cross-entropy. Binary scene sample weights retain half of total training weight on positive scenes and half on all negatives; no additional four-class reweighting is introduced. Three frozen-head epochs use Adam 0.001, followed by five block13-onward epochs at Adam 0.00001, with BatchNormalization frozen and called in inference mode.

The selected four-way Keras model is retained for audit. Its shared-weight scalar Keras/TFLite export outputs softmax component0 with shape `[1,1]`, matching the existing presence adapter. The standalone scalar gate accepts 55/66 positive examples and rejects 39/52 negatives. Its four-way argmax accuracy is 89/118 (75.42%); this is diagnostic source-category accuracy and does not select a checkpoint or establish broad unknown-input rejection.

## Selection and regression accounting

All eight epochs retain per-original four-class probabilities. The independent review recomputed every epoch's binary balanced BCE, composed mask/gate counts, eligibility and lexicographic rank. **Epoch7** wins with rank `[0,-42,-38,-44,0.4889628476675465]`; it is eligible and no fallback is used. Thresholds and source membership did not change after the failure review.

The same development groups motivated this experiment and selected its checkpoint. This creates selection optimism; the improvement cannot establish generalization or be attributed to a single isolated factor relative to the earlier binary runs.

| Source negative category | Validation originals | V4 false accepts | Category-aware false accepts |
|---|---:|---:|---:|
| Pants | 17 | 3 | 2 |
| Shorts | 15 | 0 | 1 |
| Dress | 20 | 10 | 7 |
| Total | 52 | 13 | 10 |

Relative to v4, four earlier false accepts become rejected, one earlier rejection becomes a false accept and nine false accepts remain. For positive examples, 41 remain accepted, three earlier rejections become accepted, three earlier accepted examples become unavailable and 19 remain unavailable. Aggregate preservation therefore does not mean every individual case is preserved. Frozen labels and denominators remain unchanged.

## Independent artifact and CPU verification

The [independent audit](../records/validation/2026-10-21-category-presence-artifact-review.json) passed **115 checks**, using the saved [executable audit source](../records/validation/2026-10-21-category-presence-artifact-review.py). It rehashed all 538 originals, executed sources, frozen inputs, raw category manifests, derived targets, cache and official annotation snapshot; checked source/group disjointness and every derived target binding; replayed all eight epochs; and recomputed actual exported-chain metrics and the v4 comparison.

The review independently checked copied per-image category evidence and its exact raw/curated bindings. The complete 542MB official JSON join was not rerun in this audit: its hash is verified, while the full join remains recorded executed-trainer/preflight evidence. Neither integrity checks nor publisher category names replace independent human truth.

| Selected artifact | SHA256 |
|---|---|
| Four-way `category-model.keras` | `4c442ef2e01028d6fcbd9a210c981359301a7f366a1f54edb060fe0b9e21b78f` |
| Scalar `model.keras` | `a5208c08164db35be7969e249c260d140b732eb1b3db7596a8688b5673bf3b97` |
| Scalar float TFLite | `f47ddf148102f905d0a81e6a1fe3001b8a4944fd86e0c1c2d635d975f8fdc34d` |

The final TFLite model contains 9,188,656 bytes. Archived training parity covers all 118 validation originals: early-export maximum absolute error 0.0000017285 and final-export error 0.0000059009, both below tolerance 0.001. The early export was independently rehashed; its historical Keras checkpoint was not recreated.

The independent WSL CPU review reopened the four-way Keras, scalar Keras and scalar TFLite models and executed all 118 original validation images with the recorded RGB bilinear224 preprocessing and values 0–255. Scalar Keras output exactly matched four-way component0. Maximum scalar Keras/TFLite difference was **0.0000042319** against tolerance 0.001; all threshold decisions matched. Reopened TFLite outputs exactly matched archived exported predictions and the actual comparison. The actual reopened trainable layers and frozen-weight digest agree with the fine-tuning records.

Review runtime: Python 3.12.3, TensorFlow 2.20.0, Keras 3.15.1 and NumPy 2.5.3, with GPU devices hidden for CPU verification. The tensor contract remains one float32 RGB `[1,224,224,3]` input and one float32 `[1,1]` output. This is desktop export evidence, not ARM64 compatibility or latency measurement.

No packages were installed, no weights were fitted during review and no deployment defaults were changed. Real garments, live camera classification, measured wearer geometry/calibration, empty/unknown/partial/multiple-garment rejection and Raspberry Pi operation remain unverified. Root integration must retain this candidate's research status and all prior attempts while completing those acceptance gates.
