# Full-skirt webcam collection guide

Prepared 2026-10-04. **This is a proposed collection procedure; no webcam has been activated and no local garments have been captured by this work.** Use the existing webcam first. This guide does not establish camera suitability, calibrated length accuracy, or fabric recognizability.

The model must receive one frame containing the entire skirt. Software may extract texture patches from that original frame, before resizing. Do not move the fabric closer or take a second close-up to supply inference. A care-tag photograph is permitted as separate annotation evidence; it must never enter the model input.

## First pilot

Current availability, confirmed by the user on October 4: **no physical skirts yet**. Begin by asking family, classmates or a clothing/sewing contact whether they can lend garments. Aim for several clearly pleated and clearly non-pleated skirts across light/dark colors and patterns; prioritize readable composition tags when available. Log each owner's identifier privately and keep it separate from shared dataset metadata. Do not buy a large collection before testing the existing webcam with a small borrowed set. Missing tags stay unknown; access to a skirt does not establish its fabric composition.

Start with **8–12 distinct available garments** as a development pilot, aiming for both clearly pleated and clearly non-pleated examples plus difficult folds, dark/light colors and patterns. This is a practical collection target, not an achieved count or an adequate final evaluation set. Record what is actually available; do not relabel garments to balance counts.

October 16 scope update: use a skirt worn by a consenting person as the primary arrangement. Standing front-facing with the full waistband, hem, feet and floor in the same frame is the initial development condition. Hanging, held and mannequin captures remain secondary. Capture three independently repositioned presentations per garment, preferably repeated in a second session. These are repeated observations of the same garment: 10 garments with six images each remain 10 independent garments. A second session does not create a new independent test set if the same garments occur in training.

The first pilot is for discovering capture and labeling problems. Keep its records as `development_pilot`, with training admission false until reviewed. Reserve different, previously unused garments for a later locked test **before viewing their model predictions**. Do not use the 12 protected internet seed images for tuning.

## Set up once per camera configuration

1. Fix the webcam securely and use an evenly lit, plain background. Remove unrelated garments and identifying personal details from the scene. Obtain permission for any identifiable person recorded; frame below the face where possible; worn skirts are the primary setup.
2. Frame the wearer so the whole waistband, hem, side boundaries, feet and floor fit with visible margins. Keep this full-skirt distance for every inference image and any software texture patches.
3. Inspect a native-resolution frame for blur, motion, glare, clipped highlights, deep shadows and compression blocks. Try stable lighting and placement within the existing camera's useful focus distance. Record unusable conditions rather than artificially sharpening them into accepted evidence.
4. Record the camera model if known, capture software/version, actual decoded width/height, pixel format and observed frame rate. Requested settings are not proof of negotiated settings. Record supported focus, exposure and white-balance values; use `null` plus a note if unavailable.
5. Assign a `camera_config_id` and `calibration_id` when applicable. Record camera-to-garment-plane distance, mount height, lighting positions and a setup photograph. Leave unmeasured values null. Preserve the original decoded frame without an additional resize; record its encoding and SHA-256.

Do not call this camera adequate for fabric recognition until a pilot shows repeatable cues at this same full-skirt distance. Current software training results do not establish that fact.

## Label before inspecting predictions

Assign each physical skirt a persistent `garment_id`, for example `local-garment-0001`. Use a new `session_id` for each capture session and a new `presentation_id` after removing and replacing the garment. Keep these identifiers even when filenames change.

Ask an independent human reviewer to label the originals without seeing model predictions or the earlier agent label. Record reviewer ID, date, label-guide version, evidence and uncertainty. Agent review remains a separate review entry, not a substitute for human confirmation.

| Field | Record | Abstain when |
|---|---|---|
| Pleating appearance | `pleated`, `non_pleated`, or `unknown`; deliberate repeated pleat structure versus incidental folds, with a short rationale | Folds, gathering, panels, blur or occlusion make the distinction unclear. Missing source `pleat` is not a negative label. |
| Framing | Waistband, hem and both side boundaries visible; occlusion and multiple-garment flags | Any required boundary is missing. Preserve the image as a named challenge example, not as an accepted full-view sample. |
| Fiber composition | Exact tag/supplier statement, fiber names and stated percentages only when supplied; evidence reference and provenance | No credible statement exists, the statement concerns lining instead of visible shell, or mixed panels cannot be mapped. Appearance alone is insufficient. |
| Construction | Separate evidence for satin, chiffon, denim or other agreed constructions | The construction is only guessed from appearance. Cotton/polyester and construction labels are not mutually exclusive classes. |
| Physical length | Repeated waistband-to-hem measurements, units, instrument and agreed measurement path | The method or reference is not defined. A resized crop cannot provide centimetres. |

Record shell/lining/panel scope explicitly. Copying tag text does not prove its accuracy; store evidence status such as `tag_statement_recorded`, separate from independent verification. Unknown fabric labels do not prevent using a reviewed pleating label. Resolve reviewer disagreement with a separate adjudication record; retain both original opinions. Do not silently overwrite them or use a model prediction to break the tie.

## Length calibration

Agree the physical measurement rule before classifying length. A proposed rule is waistband top to hem along a specified front panel on a consistently supported garment, without stretching; document treatment of asymmetric hems and elastic waistbands before acceptance. Take repeated measurements and retain each value rather than only an average.

Place a reference of known dimensions in the garment plane. Record reference points in native pixels, physical dimensions, mapping method and calibration residuals. Check the mapping using an additional known distance that was not used to fit it. Draping out of that plane can invalidate the estimate; document tested depth/placement tolerance.

Do not invent a short/long threshold, use an average person's height, or equate long with maxi. Keep `length_class` null until its definition and a borderline policy based on measured uncertainty are approved. Recalibrate after moving the camera/fixture, changing zoom, or changing the output crop/resolution mapping. Worn presentation needs a separate body-reference protocol; mounted calibration cannot be reused automatically.

## Capture each presentation

- Confirm garment ID, session, presentation, camera configuration and permission record.
- Show the full skirt, allow motion to settle, and retain the original frame. Note actual focus/lighting problems and visible boundaries.
- Store capture time with timezone and a unique frame/sample ID. A video-derived frame also needs parent clip ID, timestamp/index and clip hash.
- Record the original file hash and native dimensions. Any crop inherits the garment/session/split, parent frame ID and hash, and native-pixel crop coordinates. Never count crops as new garments.
- Save labels/evidence separately from any predictions. Keep care-tag images outside the model-input image directory and identify their role as `annotation_evidence_only`.
- Remove and replace the garment for the next planned presentation. Retain planned failures with reasons; do not keep only frames the model classified correctly.

After normal examples, collect a separately named development challenge set: empty station, non-skirt object, partial hem, partial waistband, multiple garments, motion and poor light. Give non-garment scenes their own persistent `scene_group_id`. Do not mix their unsupported inputs into a binary pleating accuracy denominator.

## Records and release check

Copy [the capture template](../templates/garment-capture.json) for each source frame. It is a blank record template, not an implemented validation schema. Store originals under a new local capture directory, for example `data/raw/local/<session_id>/`, and records in `data/manifests/`; create these only when data are collected. Use project-relative paths and SHA-256 references for originals and evidence. Preserve originals and version corrections.

Before a local training release:

1. Check files decode, dimensions and hashes match, and sample IDs are unique.
2. Review frame suitability and each task's label/evidence independently. Keep unknowns masked for that task rather than inventing labels.
3. Audit duplicate/related garments and scenes. Keep **all sessions, frames, clips, crops and augmentations of each garment in the same split**; union any additional related groups. Never overwrite frozen internet assignments or shuffle them to improve metrics.
4. Record garment counts separately from image counts, per-class counts, source/domain, exclusions and unresolved disagreements. Report local-camera metrics separately from internet-image metrics.
5. Freeze a versioned local split and manifest with hashes before fitting. Preserve test membership and exclude test garments from augmentation, quantization representatives, calibration and threshold selection.
6. Update `data/registry.json`, [dataset documentation](DATASETS.md), acquisition/label records and the experiment's data references. The guide alone does not update acquired-data counts.

See [evaluation](EVALUATION.md) for protected-test and calibration policies, and [record keeping](RECORD_KEEPING.md) for experiment evidence.
