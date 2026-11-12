# Actual training, validation and test memberships

Audited November 4, 2026 from saved manifests and archived experiment inputs. The [machine-readable audit](../records/validation/2026-11-04-dataset-partitions-audit.json) records source hashes, exact counts and metadata consistency checks. No model was trained, no split was changed and no protected photograph was opened or evaluated during this audit.

There is **no collected and frozen final project camera/garment test set**. There are protected external source partitions; those must remain separate from the project's final test. A generic three-way percentage diagram would incorrectly describe the experiments already performed.

## Recorded research datasets

| Dataset or selected model | Training images | Development-validation images | Total | What these numbers describe |
|---|---:|---:|---:|---|
| Original source-skirt development pool | 810 | 190 | 1,000 | Fashionpedia original `train2020` photographs, before full-view pleating eligibility; 803/188 conservative connected groups |
| Pleating fine-tune v1 | 292 | 80 | 372 | Full-view pilot: training 60 pleated + 232 non-pleated; validation 20 + 60 |
| Localizer v2 | 348 | 99 | 447 | Training 292 skirt + 56 negative images; validation 80 + 19 |
| Worn subset | 265 | 66 | 331 | Subset of the 372-image pilot: training 52 pleated + 213 non-pleated; validation 17 + 49 |
| Category-presence v1 | 420 | 118 | 538 | Training 265 worn-skirt + 155 negative images; validation 66 + 52 |
| Negative development extension | 155 | 52 | 207 | Reviewed negatives contained in the category-presence row |
| Fabric appearance smoke | 12 | 5 | 17 | Original source-training photographs from 17 source item IDs; four provisional appearance annotations |

The selected live research chain combines models with **different training histories**. The 420/118 partition describes category-presence v1 and the current comparison population. It is not the original training partition of pleating fine-tune v1 or localizer v2. The worn-only subset also does not mean the original pleating/localization models were retrained on worn images alone.

These rows overlap intentionally: all 372 pleating images are in the localizer inputs; 331 are in category-presence inputs; localizer and category-presence share 406 images. Do not sum the rows to calculate a dataset size. The entire registered collection remains 1,932 original images, including candidates excluded from these experiments. Crops and synthetic transformations add no independent originals or garments.

All curated rows have one stored source/connected-group ID per original image at this checkpoint. That is an identifier count, **not independent verification of physical garment identity**. The larger 1,000-image source pool has 991 connected groups because some related images remain grouped. Known membership and source-group relationships are preserved; unresolved garment/session correlations remain a limitation.

## Fabric appearance class counts

| Provisional source appearance label | Training | Development validation |
|---|---:|---:|
| Cotton appearance | 6 | 2 |
| Denim appearance | 4 | 1 |
| Leather appearance | 1 | 1 |
| Chiffon appearance | 1 | 1 |
| Total | 12 | 5 |

These are publisher appearance labels with agent visibility review, not independently confirmed composition measurements. The five-image validation set is a pipeline smoke check. It is too small to establish reliable deployment accuracy. The 500 supplementary texture candidates are not part of this experiment.

## Protected source data versus final project testing

Twelve downloaded Fashionpedia original `val2020` seed photographs remain assigned to `external_holdout_sanity`. They are excluded from training, augmentation selection and threshold tuning. They are not the final capstone camera test set; their project attribute labels and mask registration remain unresolved.

The DeepFashion-MultiModal partition join also preserves 848 **metadata references**: 367 original training, 224 query and 257 gallery. Query/gallery are the publisher's retrieval test partitions, may share source items, and were not admitted to project training. These counts do not represent 848 downloaded photographs.

An earlier DeepFashion attribute-metadata join identified 422 training, 66 validation and 192 test references among 680 rows. The broader holdout attributes had been exposed during an earlier fine-training metadata load before that join; this is explicitly recorded, and none was used by a model. No images from that candidate batch were acquired or admitted. It would therefore be inaccurate to claim that no test-related metadata has ever been accessed.

For project final testing, the recorded state is **not collected/frozen**, with no manifest or accuracy result. Actual wearer/hem geometry has zero observed annotations; the 66 mapped validation inventory members are unannotated, not 66 geometry validation observations. Final tests need independent garment groups, reviewed labels and the actual capture conditions. Training, model-selection validation, threshold/calibration validation and final testing must retain distinct roles; the illustrative future allocation in [the training plan](TRAINING_PLAN.md) is not an executed split.

## Checks and reporting limits

All 173 references in the continuation checkpoint matched their recorded SHA-256 values at this audit. The audit confirmed that original source assignments survive in the pleating and worn subsets, category inputs equal the worn subset plus admitted negatives, fabric labels match the archived split, and localizer labelled inputs match archived sample IDs, hashes, groups and splits. No matching sample ID, image hash or stored grouping key crosses a training/validation boundary in the audited sets; no selected model has a conflicting assignment for the same sample. The 12 protected seed IDs and recorded image hashes do not overlap the selected components' development inputs.

These checks detect known metadata conflicts. They cannot prove absence of unrecorded near duplicates, shared physical garments or source-session correlations. No images were decoded or newly compared visually for this partition audit. Repeated validation use for checkpoint selection and diagnostics also means current scores must be called **development results**, even when the recorded partitions are disjoint.

For thesis captions, use “images” or “recorded source groups,” name the exact subsystem and state that final camera/garment testing remains pending. Pair a current-state diagram with a separately marked proposed evaluation workflow; do not draw a completed test branch or report test accuracy where no such evaluation exists.
