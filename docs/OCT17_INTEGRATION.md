# Worn-first software integration

October 17, 2026. This integrates the work completed on October 16 and the subsequent review fixes. No dependencies installed, camera activated, new images downloaded or models promoted.

## Completed evidence

- Worn-presentation audit verifies all 372 frozen pleating originals and their split/group assignments. Twelve originals received actual visual review; all are worn, while 360 remain explicitly unknown. This is not a complete presentation review. [Audit](WORN_DATA_AUDIT.md).
- All 17 fabric pilot originals received individual presentation/framing review: all worn, ten with feet visible and seven cropped. Existing 12 training/five validation groups and appearance labels stay unchanged. These observations do not establish composition or calibrated geometry. [Fabric evidence](FABRIC_NEXT_GATE.md).
- A conservative mask-to-hem component preserves pixel/model uncertainty and requires independently observed, same-frame wearer references. It rejects hidden anatomy, mismatched identity and invalid masks. It is not a pose detector or a live length feature. [Contract](WORN_GEOMETRY_EXTRACTOR.md).
- Archived localizer comparison was joined to negative sampling categories: v1/v2/v3 falsely accept five of eight dresses; shorts false accepts are two/three/four of five, and pants two/three/five of six. Nine negatives are accepted by all three. No thresholds were tuned and no candidate is promoted. [Failure audit](../records/validation/2026-10-16-localizer-failures.json).
- Research-v6 packages the worn-first UI and the geometry helper with the unchanged selected pleating model. All 15 payload files passed inventory verification before and after three saved-frame HTTP results matched the existing reference. No webcam or Pi measurements follow from these checks. [HTTP evidence](../records/validation/2026-10-16-live-http-bundle.json).

## Verification

The October 16 desktop run completed 290 tests with one TensorFlow-specific skip, plus 14 mocked camera scenarios. The subsequent audit overwrite regression was tested separately. [Desktop log](../records/validation/2026-10-16-software-tests.log). Research-v6 inventory SHA-256: `3ae08c98f4cf6b00dab61cf7d6e0085dd4cd9447c38877a78c127c3c10346950`.

## Remaining acceptance gates

1. Finish the 360 pending presentation reviews before freezing a worn-specific evaluation subset. Preserve current validation membership and rights/group restrictions.
2. Improve rejection with appropriate training examples and evaluate both coverage and false acceptance. The persistent development failures do not justify a new threshold chosen to hide them.
3. Obtain a suitable actual wearer-reference detector and measured calibration; integrate it with source-aligned masks and assess the nine hemline classes. A helper that consumes observed references does not supply those observations.
4. Expand admissible rare-class fabric groups, resolve label policy and evaluate automatic crops before live fabric approval.
5. Test actual garments, camera conditions, unknown inputs and scene changes; then verify installation, inference, display, offline startup and sustained operation on the actual Raspberry Pi.

No claim that all remaining work is complete or that the supervised-demo completion target has been reached is supported by this integration. Software/data work remains as well as physical acceptance.

## Independent review fixes on October 17

Fixed hardcoded audit dates and rejection of blank/non-string visual evidence, with regression tests and a fresh [372-image audit](../records/review/2026-10-17-worn-readiness.json). Added a tapered-silhouette geometry regression; side edges can widen hem intervals, so this helper remains unvalidated for live use. Integrated the complete fabric presentation supplement into the [fabric readiness audit](../records/validation/2026-10-17-fabric-readiness.json): 17 worn records now count only after exact membership/provenance checks. Prior audits remain immutable.

Post-review verification: [43 focused tests passed](../records/validation/2026-10-17-review-tests.log), all four supplemental registry hashes matched, and research-v6 retained its verified 15-file inventory. No application runtime code changed during the October 17 audit fixes, so the existing HTTP run remains applicable.
