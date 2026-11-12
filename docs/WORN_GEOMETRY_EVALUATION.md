# Offline worn-geometry replay and evaluation

Implemented October 20, 2026. [The evaluator](../tools/evaluate_worn_geometry.py) replays saved mask/wearer evidence through the existing [worn extractor](WORN_GEOMETRY_EXTRACTOR.md), then compares its source-pixel intervals with reviewed manual annotations. No previous tool evaluated this extraction contract against an annotation/split/prediction triple; the measured-calibration builder instead derives category boundaries from a separate calibration pool.

This is evaluation infrastructure. It does not detect a wearer, infer a waistband, run a segmentation model, create calibration, enable live length or establish Raspberry Pi compatibility. No real wearer-geometry dataset or accuracy result was created by this implementation. All tests use explicitly synthetic source images and coordinates; their observed-development count remains zero.

## Inputs and identity

Supply three UTF-8 JSON files and an explicit original-file root. All paths inside the inventory use canonical relative forward-slash paths. Only frozen `development_validation` examples are eligible; training, calibration and protected test examples cannot be replayed. Original group and file-hash overlap across partitions fails validation, even when an identical original is assigned a different group name.

The complete frozen split inventory is a JSON list. Each row requires `sample_id`, `garment_group_id`, `split`, `original_path` and `image_sha256`. Do not silently reuse a differently shaped source manifest or reassign historical splits: a deliberate hash-bound mapping must preserve its original memberships and related-garment groups. Inventory completeness and physical group identity remain declarations; this tool cannot certify them.

The annotation document requires:

| Field | Required value or meaning |
|---|---|
| `schema_version` | Integer `1` |
| `data_kind` | `observed_development_geometry_annotations`; `synthetic_fixture` only with explicit test opt-in |
| `coordinate_convention` | `source_rgb_pixels_after_exif_transpose` |
| `projection` | `upright_rectified_vertical` |
| `examples` | List of reviewed frame annotations; empty is allowed and produces no accuracy/coverage claim |

Each example binds `sample_id`, `garment_group_id`, `split`, `original_path`, `image_sha256`, `frame_id`, `frame_size=[width,height]`, `camera_config_id`, `reference_id`, `person_id` and `mode`. Its file bytes must match the inventory hash; Pillow decodes the source, applies EXIF orientation and verifies the resulting dimensions. A repeated sample, frame ID or exact original file cannot inflate the annotation count. An unannotated inventory member is reported separately and does not silently enter or disappear from the coverage denominator.

Manual annotation provenance requires `observed=true`, `reviewed=true`, `annotation_method="manual_source_frame_intervals"`, `reviewer`, ISO `review_date` and `review_evidence`. These declarations retain responsibility/evidence; they do not independently establish human identity or certify the observation.

`truth` contains inclusive source-pixel `hem_y`, `waist_y` and `floor_y` intervals, plus:

- `reference_kind="observed_body_landmarks"`.
- `waist_kind="visible_waist_reference"` and `floor_kind="visible_foot_floor_contact"`.
- All seven [geometry quality flags](GEOMETRY_INTEGRATION.md) explicitly true.

Intervals must be finite, ordered and within the decoded source frame. Waist/floor order and the hem's position between those reference intervals must be unambiguous. Unsupported presentations, unreviewed/unobserved truth, wrong anatomical semantics, absent review evidence and unusable truth intervals are retained as named annotation exclusions. Identity, image-integrity or split failures reject the run rather than producing measurements from untrusted inputs.

## Saved prediction contract

The prediction document requires integer `schema_version=1`, `prediction_kind="saved_geometry_extractor_inputs"`, the same coordinate convention/projection, and exact `annotation_sha256`/`split_sha256` hashes of the actual input files. A `producer` object records `name`, `source_sha256` and `evidence`; its source hash is declared lineage, not an independently verified detector/model hash. The evaluator separately hashes its own source and the executed extractor.

Each entry in `predictions` repeats the annotation's source path/hash, sample/frame/dimensions, camera, reference and person identities, and contains `mask_record` and `wearer_record` as defined by the [existing extractor contract](WORN_GEOMETRY_EXTRACTOR.md). Duplicate or unknown prediction identities reject the run. Missing predictions count as abstentions. Stale frames, different people/reference IDs and unsupported raw records cannot yield scored geometry.

The saved wearer record must preserve actual observation state. `observed=false` model candidates remain unobserved and abstain. A hip cannot be renamed a visible waist reference, and an ankle cannot be renamed visible foot-floor contact. Quality flags and association must come from independently supported upstream evidence; the evaluator never copies truth coordinates or truth quality flags into prediction inputs.

## Outputs and interpretation

The report retains each annotated sample and its original hash. It reports:

- Annotated originals, eligible reviewed examples, explicit annotation exclusions and their reasons.
- Missing/rejected predictions with abstention reasons, accepted extraction count and image coverage.
- Macro coverage across declared garment groups; these are not independently verified physical specimens.
- Per-axis interval gap, midpoint discrepancy, maximum endpoint discrepancy, predicted/truth width and containment of the complete truth interval.
- The same interval comparison for the normalized waist-to-floor ratio, without category boundaries or a length label.
- Unannotated validation inventory identities, all three input file hashes and executed source hashes.

The means of pixel discrepancies are image-weighted diagnostics. Repeated views remain correlated; they must not be treated as extra independent garments or used to manufacture narrow uncertainty intervals. Midpoint discrepancy is a difference between interval midpoints, not a physical-length MAE. Containing a wide truth interval can reflect a very wide prediction; always read width, coverage and discrepancy together.

Empty/entirely unsupported annotations yield null coverage and null error means. Synthetic runs are labelled `synthetic_replay_only`, with zero observed-development examples. Structural validity is not measured physical calibration, actual frame-to-detector execution or live confidence calibration.

Replay preserves the extractor's known all-column endpoint limitation: tapered side contours can widen a hem interval and cause abstention. It does not silently replace the method with an unvalidated percentile or hide such cases.

## Reproduction

Use an existing Python environment with Pillow; no new runtime package is introduced. The command refuses to overwrite historical output:

```text
python tools/evaluate_worn_geometry.py --annotations path/to/reviewed-geometry.json --splits path/to/frozen-inventory.json --predictions path/to/saved-extractor-inputs.json --source-root path/to/originals --output path/to/new-replay-report.json
```

Use `--allow-synthetic` only for an explicit `synthetic_fixture` document. Do not rename test data to claim observed evidence. The existing [measured-calibration builder](MEASURED_CALIBRATION.md) remains separate: it requires calibration-only groups and all nine labelled classes, while this evaluator consumes development-validation groups and never generates boundaries.

All **19 focused tests passed** using the existing bundled Windows Python 3.12.14 and Pillow. They exercise actual extractor replay, integrity/split leakage, source identity, observation semantics, abstention/denominator behavior, interval arithmetic, real file hashing, exclusive output and rejection of non-finite metadata before output creation. [Tests](../tests/test_worn_geometry_evaluation.py). No dependencies were installed, no camera was activated and no app/default model was changed. Root integration records the command/output alongside the full software checks.

The remaining input is a hash-bound, independently reviewed annotation set with credible actual wearer, waist, floor-contact, hem and projection observations. A validated same-frame upstream producer is still required before this replay infrastructure can become evidence of automatic geometry quality.
