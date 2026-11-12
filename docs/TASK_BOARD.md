# Project task board

November 12: [GitHub setup and complete migration verification](GITHUB_SETUP_NOV12.md) are finished. The public main branch contains code and progress records; private asset manifest v2 and its prepared ZIP restore all2,804 listed files. Fresh-clone145 tests, exact checkout bytes, restored-record integrity and hosted CI pass. Use the actual checkout root on another computer; recreate environments separately. Station-v9/research-v14 remains research-only; human review, geometry/calibration and physical/Pi acceptance remain open.

November 11 repository preparation: [cross-computer GitHub workflow](GITHUB_WORKFLOW.md) and [private asset transfer](ASSET_TRANSFER.md) are prepared. Public Git carries source, manifests and progress evidence; acquired photos/models/source snapshots and environments stay excluded. Use the current asset manifest and restore privately before model/data checks. Publication status is recorded separately in the current checkpoint.

November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.

November 4 dataset follow-up: four additional [training/validation/test diagrams](THESIS_DATASET_DIAGRAMS.md) and [actual membership evidence](DATASET_PARTITION_EVIDENCE.md) are complete. The [partition auditor](DATA_PARTITION_AUDIT.md) passes 19 focused tests and five actual assignment-set checks. No model was retrained or promoted. Independent labels, final camera/garment tests, calibration and Pi acceptance remain open.

November 4: the existing selected chain was assessed on fixed synthetic brightness and blur changes to the same 118 reused development originals. No model was trained or promoted. [Robustness results](IMAGE_ROBUSTNESS_NOV04.md); [thesis figure pack](THESIS_FIGURES.md). Physical camera, independently verified labels, calibrated length and Pi acceptance remain open.

November 4 latest: station-v8/research-v13 adds requested camera modes and actual decoded-size reporting; v7 is rollback. The user reconfirmed no Pi or webcam. Fifty-two mocked checks and 12 saved-image HTTP jobs pass; physical camera/display and Pi acceptance remain open. [Camera mode evidence](CAMERA_MODE_NOV04.md).

November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. [Waveshare 14447 layout](LCD_14447_LAYOUT.md).

Earlier November 4 review (historical): [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md). Pi/webcam purchase is planned, not confirmed. Station-v6 remains selected; 73 focused tests and package verification pass. The interrupted October 23 records are reconciled; no preview/training process matched the scoped WSL check. Next software task: explicit camera-mode selection and negotiated-mode reporting, then actual camera/garment collection and ARM64 parity.

Updated November 11, 2026. This is the active checklist. Worn skirts are primary; hanging, held and mannequin remain secondary. Completed research is distinct from accepted product behavior. [Agent handoff](AGENT_HANDOFF.md). Earlier work is preserved in [task history](TASK_HISTORY.md).

## Completed

- [x] Audit actual train/validation memberships and protected source roles; independently review four [dataset diagrams](THESIS_DATASET_DIAGRAMS.md).
- [x] Add partition-leakage and frozen-assignment checks; fix review findings and pass 19 tests plus five actual input-set audits. [Evidence](DATA_PARTITION_AUDIT.md).

- [x] Install and verify laptop GPU training/export environment; preserve separate dependency records.
- [x] Acquire and audit 1,932 original images with provenance and protected source partitions; no exact/pixel duplicates or corrupt originals.
- [x] Complete all 372 pilot presentation reviews: 331 worn, 27 hanging, eight mannequin, six unknown. Zero unreviewed samples; unknowns remain uncertain after review.
- [x] Freeze the worn development subset: 265 training / 66 validation, preserving original group/split membership.
- [x] Complete 180 new negative-original reviews and freeze 207 total negative examples: 155 training/52 validation. Preserve every prior record/split and excluded candidate.
- [x] Train/export pleating, localization and presence candidates and compare coverage/rejection. Failed candidates remain unpromoted.
- [x] Review all 17 fabric pilot originals and run manual-versus-automatic ROI evaluation.
- [x] Implement camera-first preview, automatic frame submission, bounded inference, stale-result clearing and fabric toggle.
- [x] Connect optional research-only fabric appearance and body-keypoint adapters; preserve independent unavailable/error states.
- [x] Implement conservative geometry adapter, hem extraction and measured-calibration builder with source-image hash checks.
- [x] Package research-v7; verify default and optional research paths through saved-frame HTTP checks.
- [x] Review agents' changes, correct discovered issues, and record tests/model/data hashes.
- [x] Train/archive presence v3 and v4; verify v4's relative development improvement and actual-export HTTP results without changing deployment defaults.
- [x] Inspect all 13 remaining negative false accepts and all 28 positive failures, with hash-bound observations and preserved evaluation denominators.
- [x] Recover selective fabric-archive indexing; acquire and inspect five originals with source-ID composition metadata. Two full-view skirt candidates, three quarantines, zero admissions.
- [x] Implement read-only edge preflight; desktop correctly reports Pi verification still pending. [Instructions](EDGE_PREFLIGHT.md).
- [x] Train/archive the category-aware presence candidate; independent115-check audit and all 118 actual Keras/TFLite cases pass. New development counts44 accepted/38 correct/42 negative rejections.
- [x] Build and verify portable station-v1/v2; each passes 12 saved-frame HTTP jobs. Select v2 for desktop research and preserve v1 for rollback.
- [x] Implement/test worn-geometry replay and map the frozen inventory: zero observed geometry annotations, null coverage,66 unannotated validation members.
- [x] Audit existing fabric attributes and research new sources with bounded metadata acquisition; zero new image/label admissions.
- [x] Create root handoff, documentation index and hash-bound continuation checkpoint; verify current model/package identities and preserve unfinished acceptance gates.
- [x] Correct camera startup mute-state handling; 17 mocked lifecycle scenarios pass against the packaged UI. Build research-v8/station-v3 and verify12 saved-frame HTTP jobs, preserving previous packages.
- [x] Read the actual 2018 source rules and audit155,393 cached TextileNet URL rows against the official blob; add bounded offline identity checks with seven passing tests. No new photos/admissions.
- [x] Implement the user's cream/burgundy UI reference while retaining nine hemline classes and the fabric switch. Verify18 lifecycle scenarios, 21 score cases and 12 saved-frame HTTP jobs; select station-v5, retain v3 rollback and mark intermediate v4 unselected. [Evidence](REFERENCE_UI_OCT22.md).

- [x] Improve animations with reduced-motion support and immediate clearing; 18 lifecycle, 21 score and six motion cases pass. Station-v6 is selected with v5 rollback. [Evidence](UI_MOTION_OCT22.md).
- [x] Prepare a blind fabric-evidence queue for all 17 frozen pilot originals, with append-only pending observations and 30 passing tests. Zero observations have been submitted; no labels, groups or admissions changed. [Review guide](FABRIC_EVIDENCE_REVIEW.md).

## Immediate recovery and software preparation

All four requested software items are complete. [Implementation evidence and next actions](RECOVERY_IMPLEMENTATION_NOV11.md). No fit, acquisition or test server remains active.

- [x] **R01 — Recover acquisition records.** All21 HTTP failure bodies and historical hashes are preserved with typed copies and a checked index. Ordinary malformed JSON still fails. [Recovery](ACQUISITION_RECOVERY_NOV11.md).
- [x] **R02 — Finish the fabric reviewer.** Complete browser save/download/unknown/security checks and reviewer guide;41 tests pass. Production17-item queue still awaits actual observations. [Use the reviewer](FABRIC_REVIEW_UI.md).
- [x] **R03 — Build the geometry annotation editor.** Full-original bands/unknowns, hash-bound pending export, cancellation/date handling and guide complete;14 tests and browser roundtrip pass. [Use the editor](GEOMETRY_ANNOTATION.md).
- [x] **R04 — Improve800 ×480 usability.** Essential preview/settings/actions/four values/fabric switch fit without initial scrolling. Source mocked/browser checks and station-v9 HTTP/inventory checks pass; physical LCD/touch testing remains open. [Layout](COMPACT_LAYOUT_NOV11.md).

## Next software and data work, in priority order

- [ ] **S01 — Complete independent label confirmation.** Six uncertain originals and their exact source annotations were checked; sample 34099 is source-annotated wrap/skirt and was not relabelled from suspicion. Human confirmation and any justified versioned correction remain open. [Follow-up](SOURCE_LABEL_FOLLOWUP.md).
- [ ] **S02 — Add camera-domain negative diversity.** The 180-original expansion and 132 new admissions are complete. Empty scenes, difficult backgrounds, partial/multiple garments and independent camera-domain groups remain missing. Preserve source/group splits and count physical specimens separately.
- [ ] **S03 — Confirm detection quality beyond reused development.** Selected category gate plus localizer-v2 accepts 44/66 skirts, gives38 correct pleating and rejects 42/52 negatives; v4 gave44/38/39. Independent export/HTTP checks pass, but10 negatives are still falsely accepted and 22 skirt examples unavailable. Dress/unknown-input rejection, minority pleating and frozen unseen-garment/camera evaluation remain required. [Results](CATEGORY_PRESENCE_RESULTS.md).
- [ ] **S04 — Resolve fabric labels and expand worn groups.** The actual 2018 rules are now readable: use is conditioned on acceptance, which has not occurred. TextileNet's cached155,393-row manifest is audited, including repeated URLs and missing garment/product mapping; applicable photo terms/attribution and original source partitions remain unresolved. Before bounded photo intake, satisfy the source-use gate and material-to-skirt/grouping checks. Confirm appearance vocabulary, mixed/unknown policy and independent labels. [Current gate and tooling](FABRIC_SOURCE_GATE_OCT22.md), [earlier search](FABRIC_SOURCE_SEARCH_OCT21.md), [unadmitted flat-laid pilot](NPCGI_PILOT.md).
- [ ] **S05 — Train/evaluate a stronger fabric candidate.** Compare automatic native-source crops, unsupported inputs, class errors and coverage. The current five-image validation and research-only live path do not close this task. Acceptance: approved evaluation protocol, candidate results and export checks before promotion.
- [ ] **S06 — Validate actual wearer references and hem contours.** The replay evaluator is complete; actual reviewed geometry observations and a validated upstream producer are missing. Establish wearer/skirt association, visible waistband/floor references, posture/visibility and tapered/asymmetric hem uncertainty. Pose candidates cannot supply observed truth. [Evaluator and remaining gate](WORN_GEOMETRY_EVALUATION.md).
- [ ] **S07 — Freeze an accepted full-feature release.** Station-v9 includes the compact UI and camera-mode controls; v8 is rollback. Fabric/reference/calibration acceptance remains missing. After those pass, test physical freshness/recovery and freeze the accepted configuration. [Current package and limits](STATION_PACKAGE.md).

Independent human confirmation is a required input to label acceptance; additional agent reviews alone do not close it. S06 software development can proceed now, but calibrated length acceptance also depends on P02 below.

## Work requiring garments or hardware

Latest availability: the user reconfirms no Raspberry Pi, webcam or actual skirts on November 11. Earlier webcam access does not establish current availability. Continue saved-image work without claiming physical acceptance.

- [ ] **P01 — Obtain development and held-out garments.** Record garment identities, consent where applicable and credible fabric-label evidence; reserve separate test garments before examining predictions.
- [ ] **P02 — Measure the camera/reference setup and calibrate hemline.** Collect reviewed nine-class development observations, rectify/validate geometry and build a hash-bound candidate. Test wearer proportions, borderline categories and camera movement. The builder is complete; physical calibration is not.
- [ ] **P03 — Evaluate the actual camera.** Compare available/replacement camera at the same full-skirt framing; record negotiated resolution, focus, lighting, blur and usable texture detail.
- [ ] **P04 — Test unseen garments end to end.** Measure per-class pleating/fabric/length errors, coverage, non-skirt rejection, motion/occlusion, scene changes/disconnection and prediction age in the demonstration setup.
- [ ] **P05 — Obtain and bring up the Raspberry Pi station.** Record board, power, storage, cooling, display and camera; choose and verify the actual ARM64 OS/Python/runtime pairing.
- [ ] **P06 — Reproduce Pi installation and benchmark.** Log installs, capture an edge-specific environment/lock, verify model parity, offline operation, latency/memory/temperature, startup, recovery and rollback.
- [ ] **P07 — Rehearse and accept the supervised demonstration.** Freeze accepted versions and operating limits, repeat the demo on the real station and preserve the final evidence bundle. [Acceptance checklist](SUPERVISED_DEMO.md).

## Secondary presentations

- [ ] **M01 — Verify hanging/held/mannequin behavior separately.** Preserve their interface options and mode-specific references; hanging/held lengths remain estimates relative to a calibrated standard body. Complete their own calibration and evaluation after the primary worn workflow.

No date or completion percentage is inferred from this checklist. Current research functionality does not close model-quality, physical-calibration or Pi acceptance tasks.
