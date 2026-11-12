# Worn mask and wearer-reference extraction

Implemented October 16, 2026 in `app/worn_geometry.py`. This is a dependency-free geometric component, not an installed pose model, automatic waistband detector, calibrated system or live-length feature. It extracts a conservative hem interval from a binary segmentation mask and assembles independently observed wearer references for the existing `app.geometry.estimate_hemline` adapter. No production boundaries, detector error margins or visibility thresholds are supplied.

## Interface

Call `extract_worn_geometry(frame_id=..., camera_config_id=..., frame_size=[width,height], mask_record=..., wearer_record=...)`. It returns `status="extracted"` with `evidence` on success; otherwise `status="unavailable"`, a specific `reason` and `evidence=None`. Pass only successful evidence to `estimate_hemline`. The latter still requires a measured matching calibration profile. No input is mutated.

Both records must contain the current `frame_id`, `camera_config_id`, original `frame_size`, a nonempty `evidence_id`, and the same nonempty `person_id`. The upstream association stage must identify the actual wearer, rather than associating a held skirt with its holder. Identity strings do not independently prove that association.

The mask record contains:

- `mask`: rectangular nested lists of binary integer/boolean values, at least 3 by 3. Convert a NumPy mask using `.tolist()`; probability thresholding belongs to the versioned segmentation contract.
- `mapping="full_source_extent"`: the grid covers the complete already rectified source frame. Cropped, letterboxed or otherwise transformed masks are rejected rather than guessed into alignment.
- `boundary_error_px`: a finite nonnegative source-pixel margin, plus `boundary_error_evidence` identifying its development evaluation. Zero is permitted only as an explicitly supplied value, not inferred from perfect synthetic checks. Structural acceptance cannot establish the truth of this evidence.

The wearer record contains `mode="worn"`, `reference_id` matching the eventual calibration profile, all seven existing geometry `quality` flags explicitly true, and four `landmarks`: `waist_left`, `waist_right`, `floor_left`, `floor_right`. Each landmark contains inclusive source-pixel uncertainty intervals `x` and `y`, `observed=true`, an `evidence_id`, and a semantic `kind`. Waist kind is `visible_waist_reference`; floor kind is `visible_foot_floor_contact`.

Do not rename generic pose hip landmarks into waist landmarks or ankle landmarks into floor contact. Pose confidence alone does not establish visibility, foot contact, upright projection, complete skirt visibility or correct wearer association. Hidden inferred landmarks must remain unobserved. The recorded observation and quality evidence must be produced by independently validated upstream stages, not set true to enable output. This component verifies their contract, not their physical truth.

## Computation and abstention

The mask must be nonempty, have exactly one four-connected component and not touch the frame boundary. Every occupied column contributes its bottom cell. The earliest bottom-cell upper edge and latest bottom-cell lower edge define a conservative interval mapped to source pixels; the declared boundary error expands both ends. This preserves low-resolution cell extent and asymmetric hems. It deliberately does not discard tips or outliers by percentile. Side contours, mask noise and slits can consequently widen the interval substantially. An apparently precise mask does not establish a precise physical hem.

Left/right waist and floor intervals are merged conservatively. Ambiguous waist/floor order, hem intervals crossing those reference intervals, out-of-frame uncertainty, unsupported presentations, stale frames, mismatched cameras and unobserved landmarks abstain. Success preserves mask/wearer evidence IDs, person ID, mask dimensions and extraction method. Existing category-boundary handling may still return uncertain instead of a label.

The current localizer returns a bounding ROI, not this mask record; its output must not be substituted as a mask or used to manufacture quality flags. A future geometry provider for `AutomaticPredictor` can obtain the source mask and wearer records from the same image, call this component and return its successful evidence. Keep the current unavailable live state until that provider, camera configuration and measured calibration are implemented and validated. No changes to `app/localization.py` or the server are made by this component.

## Verification and next dependencies

Windows Python 3.11.9 ran `python -m unittest tests.test_worn_geometry -v`: **14 synthetic tests passed** on October 16. Coverage includes source identity, same-person association, every quality gate, hidden anatomy, hip/waist mismatch, invalid coordinates, mask mapping, disconnected/edge masks, asymmetric hem uncertainty, immutable inputs and consumption by the existing calibration adapter. No dependencies were installed and no camera was activated. These checks establish software behavior only, not extraction accuracy, model speed or Raspberry Pi operation.

Remaining: select and benchmark an actual wearer/waist/foot detector; expose calibrated source-aligned segmentation; validate visibility, association and projection; estimate mask/landmark errors using development examples; collect measured worn calibration; then evaluate held-out garments and wearer variation. Knee-relative categories still require demonstrated anatomical correspondence of the calibrated waist-to-floor model. This component does not resolve that scientific validation requirement.

## October 17 review: tapered silhouettes

All-column endpoints can include side edges on an inward-tapered skirt. A synthetic flat hem with tapered sides yields a conservative interval [29,61] rather than [49,61]. This may cause abstention even when the true hem is clear. A regression test preserves this known limitation; the extractor must not be described as validated hem-contour detection. A validated contour method is still needed before live use.
