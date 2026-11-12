# Four-way source-category presence protocol — October 20, 2026

Executed October21 and reconciled October22: [completed results and independent audit](CATEGORY_PRESENCE_RESULTS.md). The actual run ID is `20261021-category-presence-v1`; the October20 command example below was a preparation target, not an executed fit. No rerun is pending. Current helper provenance checks are documented in the [integration record](OCT22_INTEGRATION.md); immutable executed sources remain archived.

This is one declared research experiment addressing the [v4 failure review](PRESENCE_V4_FAILURE_REVIEW.md): ten of its 13 remaining false accepts are dresses, while the other three are trousers. A binary head may benefit from supervision that distinguishes the negative categories. This is a hypothesis, not a completed result or an accepted fix. Preserve v3/v4 and every unsuccessful outcome.

## Frozen inputs and source supervision

Use the exact 538 original inputs from the frozen worn subset plus reviewed negative-v3: 265 skirts and 155 negatives for fitting; 66 skirts and 52 negatives for development validation. Original image hashes, groups, rights and assignments remain unchanged. The raw 390 negative-candidate records remain separate from the 207 curated admissions. No held-out source or final-test image may be added.

The new trainer first reuses all v4 admission checks and pins the negative-v3 manifest, three raw acquisition manifests and the official annotation snapshot by their SHA256 values. It then joins every admitted negative to its raw acquisition row using sample ID, image hash/path, source item/URL, original source partition, source group, source license, sampling bucket and copied annotations. Every copied annotation ID/category/name/bounding box must exactly match the complete official per-image annotation membership. A negative must contain exactly one supported lower-body/whole-body bucket (pants, shorts or dress), no skirt and no jumpsuit conflict. Mixed or missing source-category evidence fails before framework import or output creation.

The categories are hierarchical **scene targets**, in fixed output order:

1. `skirt_present`: the frozen reviewed positive scene, with its exact selected official skirt annotation. Other clothing can co-occur.
2. `no_skirt_pants`: admitted reviewed skirt absence and pants as the sole supported source bucket.
3. `no_skirt_shorts`: admitted reviewed skirt absence and shorts as the sole supported source bucket.
4. `no_skirt_dress`: admitted reviewed skirt absence and dress as the sole supported source bucket.

This avoids claiming that an entire positive scene contains only one garment category. The auxiliary negative category is publisher supervision joined to provisional visual absence review; it is not independent human-confirmed category truth. Current source metadata has 53 pants/44 shorts/58 dresses in training and 17/15/20 in validation. Admission is checked against actual files each time, rather than trusting these documented counts.

These three negative buckets do not establish rejection of empty scenes, unknown objects, partial garments or multiple garments. The categorical head is not a general open-set detector or proof of complete framing.

Keep byte-identical binary `inputs.json` for cache compatibility. Save additional targets to a separate hash-bound `source-category-targets.json`, including sample/image/group/split identity and selected official annotation IDs. All four categories must occur in each development partition. Training and conversion never rewrite historical manifests or labels.

## One candidate and fixed selection

Retain v4's pretrained MobileNetV2, full-frame Pillow RGB bilinear 224 input, float32 values 0–255 with internal normalization, Dense64 ReLU/dropout0.2, seed42, batch8 and independent training-only horizontal flip0.5. Replace the sigmoid head with softmax4 and use sparse categorical cross-entropy. Retain exactly v4's binary scene sample weights: half of total training weight on skirt scenes and half on all negative scenes. Do not introduce a separate four-class balancing change. Three frozen-head epochs use Adam0.001; five block13-onward epochs use Adam0.00001, keeping all BatchNormalization frozen and executing it in inference mode.

At each epoch, take softmax component0 as the skirt probability and apply inclusive0.5 acceptance. Use the same verified v1/v2 mask-only cache and the same [chain selection protocol](PRESENCE_JOINT_SELECTION_PROTOCOL.md): eligibility preserves baseline accepted skirts and correct pleating, and strictly improves negative rejection. Among eligible epochs maximize rejection, correct pleating and accepted skirts, then minimize binary balanced BCE. If no epoch is eligible, retain the minimum-BCE fallback with eligibility false. Exact ties retain the first epoch. Four-class accuracy is diagnostic only; it cannot select the checkpoint.

Save every epoch's per-image four-class probabilities, counts, rank and eligibility so a reviewer can replay selection arithmetic independently. The reused development groups have already informed both this hypothesis and earlier experiments; no apparent gain is an independent generalization result. Thresholds, source membership and frozen truth are not tuned from failures.

## Export and execution

The application still consumes one scalar probability. Save the selected four-way `category-model.keras` for audit and a shared-weight `model.keras` that slices softmax component0 with shape `[1,1]`. The exported float32 TFLite model uses one `[1,224,224,3]` RGB input and one `[1,1]` output, matching the current `PresenceGate` contract. Export immediately after epoch1 and again after selection; execute all 118 validation originals and require maximum absolute error at most0.001. Keep original source-frame preprocessing and fixed thresholds.

The focused actual-framework test constructs this graph from the verified existing pretrained cache, checks scalar/softmax agreement, saves/reopens both Keras models and converts/executes two synthetic images **without fitting weights**. It uses the trainer's strict-FP32, seed and head-freeze setup. An initial harness omitted that complete setup and failed parity; correcting the harness preserves the original0.001 tolerance. This is an export contract check, not a training result, camera evidence or Pi compatibility proof. No package install or automatic model download is required.

Root runs fitting only after code/test review, using a new output directory:

```text
python tools/training/train_category_presence.py --negative-manifest data/labels/negative-reviewed-v3.jsonl --joint-comparison-cache records/validation/2026-10-19-detection-v4-comparison.json --output /home/skirttrain/skirt-fabric-sense/runs/20261020-category-presence-v1
```

Run this from the existing WSL training environment so `inputs.json` retains the byte-level newline convention of the historical cache. The trainer records executed source copies, environment, frozen inputs/derived targets/cache, seed/optimization schedule, all epoch probabilities, selected Keras models, scalar export parity and limitations. Root must then independently run the exported complete chain, compare v4 as well as the v1 baseline, review per-category failures and verify desktop HTTP behavior. Relative development improvement alone does not approve demonstration use, calibrated length or Pi deployment.
