# Build a candidate from measured development calibration

Implemented October 17, 2026. `tools/build_measured_calibration.py` prepares a calibration candidate from reviewed pixel measurements and a frozen garment-group split inventory. No actual measured annotation set or production calibration profile exists. This tool does not detect the wearer, label skirt lengths, rectify a camera or verify physical measurements.

Run only after measured development evidence exists:

```text
python tools/build_measured_calibration.py --annotations PATH_TO_REVIEWED_ANNOTATIONS --splits PATH_TO_COMPLETE_SPLIT_INVENTORY --source-root PATH_TO_ORIGINALS_ROOT --output NEW_PROFILE_PATH
```

Output creation is exclusive: an existing file is never overwritten. Input errors produce exit code 1 and no output. A successful output satisfies `app.geometry.validate_profile`; it still has `physical_calibration_verified=false` and status `candidate_requires_independent_physical_acceptance`. Loading this file alone cannot enable live length estimation. `--source-root` defaults to the annotation file's parent directory when omitted. Every included original is resolved beneath that root and its actual bytes are hashed before output creation. Absolute paths, traversal segments, backslashes, drive/stream syntax and resolved paths escaping the root are rejected. Use canonical forward-slash relative paths. This binds measurements to specific source bytes; it does not decode images or independently verify declared source dimensions or annotation accuracy.

## Annotation document

The JSON document requires:

- `schema_version`: integer 1; `data_kind`: `observed_development_annotations`.
- Nonempty `profile_id`, `camera_config_id`, `reference_id`, and `measurement_evidence`. The evidence identifies the actual measurement/rectification record, with documented label definitions and annotator procedure.
- `frame_size`: source `[width,height]` positive integers; `projection`: `upright_rectified_vertical`; `mode`: one of worn, hanging, held or mannequin. Build a separate profile for a different reference, station or presentation; this tool does not pool modes into shared boundaries.
- `examples`: reviewed observations, each with nonempty `sample_id`, `garment_group_id`, `frame_id`, `reviewer`, `review_evidence`, ISO `review_date`, `observed=true`, `reviewed=true`, `split=development_calibration`, and a `label` from the nine-label vocabulary. Each also requires `original_path` relative to the source root and the original's lowercase 64-hex-character `image_sha256`.

Each example's `geometry` requires the same `frame_id` as its example, and the document's exact `camera_config_id`, `reference_id`, `frame_size`, `projection` and `mode`. It includes `reference_kind`, `hem_y`, `waist_y`, `floor_y`, and `quality` following [the source-frame geometry contract](GEOMETRY_INTEGRATION.md). Each y value is an inclusive finite two-number pixel interval inside the source image. Waist and floor intervals must be strictly ordered. All seven geometry quality observations must explicitly be true. Worn examples require `observed_body_landmarks` associated with the actual wearer; standard-body references cannot substitute for the wearer. The tool cannot establish these truths from a declaration.

The measured label order is micro, mini, above_knee, on_knee, below_knee, midi, tea, maxi, full. Every label must have measured support. A group cannot carry conflicting labels in this builder; label ambiguities require review rather than manufactured separation. Repeated frames or sample IDs are rejected.

## Frozen split inventory and leakage checks

The split input is a JSON list of assignments, each containing `sample_id`, `garment_group_id` and `split`. Relevant calibration assignments must also contain `original_path` and `image_sha256`, exactly matching the corresponding measurement example. It must cover the entire relevant group inventory, including training, validation, protected holdouts and calibration observations, so all related-group memberships can be checked. Preserve official-source holdouts and all image/crop/session relations when constructing this inventory. Calibration acquisition must have been authorized for development use under the source protocol before assigning it `development_calibration`.

Each annotation must match its declared frozen calibration assignment. Any related garment group listed with a different split rejects the build, including training, development validation and test. Missing assignments, duplicate sample assignments and group mismatches also reject the build. These checks cannot discover omitted relations or prove that an incomplete inventory is complete. Existing frozen datasets are not changed or repartitioned by the tool. Do not relabel protected samples to make this validator pass.

## Boundary derivation and uncertainty

For every example, compute the minimum and maximum of `(hem-waist)/(floor-waist)` over all interval endpoint combinations. Reject values outside zero through one. For each class, retain the full envelope spanning all its observations. Adjacent class envelopes must be strictly separated in the prescribed order. Touching, overlap, reversed order or a missing label rejects the entire build; there is no fallback threshold or guessed anatomical proportion. A numerical separation gap is required between supported neighboring classes. The boundary is the midpoint of that observed gap.

The output records exact SHA256 hashes and paths of the annotation and split files, the resolved source root, every included original path/hash, sample/frame/group and propagated interval, class envelopes, counts and the boundary method. File-based builds record `original_bytes_verified=true` only after all original hashes match. The pure `build_profile` function performs structural validation without accessing files and makes no byte-verification claim. Counts refer to images and declared groups; they are not independently verified physical specimens. A valid fit to calibration examples does not measure performance on unseen garments. Sparse support can yield unstable boundaries even when structural checks pass. Freeze the candidate before testing on separately held-out garments and measure boundary errors, uncertainty coverage, posture effects and calibration stability. Calibration samples cannot serve as independent test evidence.

## Verification

Fourteen focused tests passed under the existing bundled Windows Python environment on October 17 after original-byte binding was added. Tests cover gap-derived boundaries, all-nine-class support, overlapping/touching/reversed evidence, identity mismatches, false observation/quality flags, training/validation/test group leakage, missing assignments, invalid intervals, repeated samples, conflicting garment labels, exact provenance hashes, changed-original rejection before profile creation, missing/mismatched source identities, path traversal rejection, an explicit original-file root and exclusive output creation.

All successful numeric examples are synthetic fixtures used only in tests, with generated profile files confined to temporary directories. No dependency was installed, camera used, physical calibration performed or production profile created. Real garments, reviewed measured examples and a verified camera setup remain necessary.
