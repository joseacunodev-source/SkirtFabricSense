# Geometry integration contract

October 17 next milestone: an optional actual MoveNet runtime produces same-frame candidate keypoints, but no validated observed waist or foot-floor contact. Length remains unavailable. The measured-calibration builder requires explicit nine-class development evidence; no physical profile was generated. [Preparation](MEASURED_CALIBRATION.md), [runtime evidence](OCT17_NEXT_MILESTONE.md).

October 17: the new [worn extraction helper](WORN_GEOMETRY_EXTRACTOR.md) supplies this adapter with conservative mask-derived hem intervals only when independent wearer/reference evidence is present. Its tests are synthetic; live extraction/calibration remains outstanding.

October 16: implement and evaluate worn-mode extraction first. Waist/hem and actual-wearer reference must share source coordinates and identity. Skirts may hide knees; hidden anatomy is not observed evidence. Preserve abstention until a validated estimator and measured calibration exist. Secondary modes retain their current contracts. [Priorities](WORN_PRIMARY.md).

Implemented October 11, 2026. `app/geometry.py` converts explicit geometry from one source frame into the nine categories in `app/hemline.py`. It is an evidence adapter, not a body-landmark or hem detector. No production calibration profile or automatic landmark extractor exists yet. Tests are synthetic and do not measure hemline accuracy.

Call `estimate_hemline(frame_id=..., camera_config_id=..., frame_size=[width,height], mode=..., evidence=..., profile=...)`. Missing, invalid or mismatched inputs return an unavailable result. Valid evidence produces an estimate, or uncertain when the propagated interval touches a category boundary. Result provenance retains frame, camera, reference and profile identities. Scores are not invented.

## Calibration profile

Required fields:

- `schema_version`: 1.
- `profile_id`, `reference_id`, `camera_config_id`: nonempty identifiers. Camera configuration must identify lens, resolution, orientation, crop and projection calibration; changing any of these requires a matching profile.
- `calibration_evidence`: nonempty record identifier/path describing how reference dimensions, projection and boundaries were established. Structural validation cannot verify the truth or existence of this evidence.
- `frame_size`: integer source width and height.
- `projection`: `upright_rectified_vertical`. The adapter only supports a vertical axis in an already rectified source coordinate system. Arbitrary perspective, tilted scenes and bent reference poses are not supported by this calculation.
- `coordinate`: `waist_to_floor`.
- `labels`: the exact ordered nine-label list from `app.hemline.LABELS`.
- `supported_modes`: the calibrated subset of worn, hanging, mannequin and held.
- `boundaries`: eight finite strictly increasing values between zero and one, derived from calibration/development evidence. No default thresholds are supplied.

Validate a saved profile with `python tools/validate_calibration.py path/to/profile.json`. Exit status 0 means structural validity only; exit 1 means invalid/unreadable. The JSON response explicitly reports physical calibration unverified. The synthetic fixture in `tests/test_geometry.py` must never become a production profile.

## Per-frame evidence

Required fields are `frame_id`, `camera_config_id`, `frame_size`, `mode`, `reference_id`, `reference_kind`, `hem_y`, `waist_y`, `floor_y`, and `quality`. Each y field is an inclusive two-number uncertainty interval in the original rectified frame, within 0 through height minus one. Source frame identity is checked against the current request; the existing live controller remains responsible for capture-age expiry.

Worn mode requires `reference_kind=observed_body_landmarks`, with waist and floor references associated with the actual wearer. A generic standard body cannot replace this evidence. Hanging and held require `calibrated_standard_body`, matching the user's selected estimate policy. Mannequin supports `observed_mannequin_landmarks` or `calibrated_standard_body`. Standard-body waist/floor coordinates must come from the calibrated fixture/reference projected into the same source frame, not guessed from the skirt box or the holder's anatomy.

Every `quality` field must be explicitly true: `full_skirt_visible`, `single_garment`, `reference_associated`, `projection_valid`, `hem_visible`, `waist_reference_valid`, `floor_reference_valid`. These flags must come from an actual upstream detector/calibration validation stage; they are not permission switches or a way to declare unseen anatomy measured. The current segmentation model alone cannot establish them.

The adapter evaluates `(hem_y - waist_y) / (floor_y - waist_y)` over all interval endpoint combinations, retaining conservative lower/upper bounds. Overlapping waist/floor intervals abstain. Hems outside the calibrated waist-to-floor range abstain. Wide/asymmetric or uncertain hems should produce a wider hem interval rather than a forced midpoint class.

## Verification and remaining work

On October 11, Windows Python 3.11 ran `python -m unittest tests.test_geometry tests.test_hemline`: **20 tests passed** (12 adapter/CLI plus 8 existing rules). They cover all presentation reference policies, camera/frame mismatch, quality failures, invalid pixels, uncertainty propagation and CLI valid/invalid synthetic profiles. No dependency installation occurred.

Remaining real work: obtain reference/body/hem evidence and development calibration examples; validate perspective and source-coordinate alignment; freeze category boundaries; implement the upstream extraction stage; then measure coverage and per-class errors on held-out garments. Real camera geometry and Raspberry Pi execution remain unverified. The live app should stay unavailable for hemline until these inputs exist, even if pleating is available.

## Application adapter review — October 12

`AutomaticPredictor` now accepts an optional geometry provider and calibration profile. It passes the original image, localized region and frame options to the provider, then checks the resulting evidence with this adapter. A provider exception makes length unavailable while preserving the independent pleating result. Missing or stale evidence never produces a length label.

The server's `--calibration-profile` option validates and loads a profile only. The server currently supplies no verified camera-configuration identity and no automatic geometry provider; therefore loading a profile does not enable live length estimation. Do not copy the synthetic test identity or coordinates into a real station.

October 12 review ran the bundled Windows Python 3.12.14 full suite: **223 tests passed**, plus **14 mocked camera/live-loop scenarios** under Node. Seven new tests cover the optional presence model contract, rejection before downstream processing, same-frame geometry, missing/stale evidence and independent output behavior after an extractor failure. This is software behavior evidence, not physical geometry or learned accuracy validation. No packages were installed.
