# Documentation index

November 11 repository preparation: [cross-computer GitHub workflow](GITHUB_WORKFLOW.md) and [private asset transfer](ASSET_TRANSFER.md) are prepared. Public Git carries source, manifests and progress evidence; acquired photos/models/source snapshots and environments stay excluded. Use the current asset manifest and restore privately before model/data checks. Publication status is recorded separately in the current checkpoint.

November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.

November 11 current review: [recovery findings and ordered next tasks](PROJECT_REFRESH_NOV11.md). No unfinished GPU run or active scoped station/training process was found. Fabric reviewer server/HTML are partial, the geometry annotation editor is absent, and the completed background attempt acquired zero photos. Twenty-one raw HTTP error responses saved as JSON still fail record parsing. The user reconfirmed no Pi, webcam or skirts. Resume record recovery R01, then reviewer completion R02; do not restart completed fits.

November 11: [progress-report screenshots](PROGRESS_SCREENSHOTS_NOV11.md) capture the actual camera-off UI and implemented source. Five images visually reviewed; temporary server stopped. Earlier label, geometry and hardware acceptance tasks remain open.

November 4 dataset follow-up: four additional [training/validation/test diagrams](THESIS_DATASET_DIAGRAMS.md) and [actual membership evidence](DATASET_PARTITION_EVIDENCE.md) are complete. The [partition auditor](DATA_PARTITION_AUDIT.md) passes 19 focused tests and five actual assignment-set checks. No model was retrained or promoted. Independent labels, final camera/garment tests, calibration and Pi acceptance remain open.

November 4: the existing selected chain was assessed on fixed synthetic brightness and blur changes to the same 118 reused development originals. No model was trained or promoted. [Robustness results](IMAGE_ROBUSTNESS_NOV04.md); [thesis figure pack](THESIS_FIGURES.md). Physical camera, independently verified labels, calibrated length and Pi acceptance remain open.

November 4 latest: station-v8/research-v13 adds requested camera modes and actual decoded-size reporting; v7 is rollback. The user reconfirmed no Pi or webcam. Fifty-two mocked checks and 12 saved-image HTTP jobs pass; physical camera/display and Pi acceptance remain open. [Camera mode evidence](CAMERA_MODE_NOV04.md).

November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. [Waveshare 14447 layout](LCD_14447_LAYOUT.md).

Earlier November 4 review (historical): [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md). Pi/webcam purchase is planned, not confirmed. Station-v6 remains selected; 73 focused tests and package verification pass. The interrupted October 23 records are reconciled; no preview/training process matched the scoped WSL check. Next software task: explicit camera-mode selection and negotiated-mode reporting, then actual camera/garment collection and ARM64 parity.

Use [the agent handoff](AGENT_HANDOFF.md) to resume work and [the task board](TASK_BOARD.md) to identify current open tasks. The index routes to evidence rather than treating every dated status paragraph as current. Newer user instructions and verified records take priority over historical plans.

## Core documents

| Need | Read |
|---|---|
| Project instructions and invariants | [AGENTS.md](../AGENTS.md), [README](../README.md), [portable project skill](../skills/skirt-fabric-project/SKILL.md) |
| Current state and remaining actions | [Agent handoff](AGENT_HANDOFF.md), [task board](TASK_BOARD.md), [latest motion update](UI_MOTION_OCT22.md), [reference UI](REFERENCE_UI_OCT22.md), [earlier camera/source batch](CAMERA_SOURCE_UPDATE_OCT22.md), [machine checkpoint](../records/continuation/latest.json) |
| Scope and acceptance | [Requirements](REQUIREMENTS.md), [decisions](DECISIONS.md), [supervised demonstration](SUPERVISED_DEMO.md), [worn-first scope](WORN_PRIMARY.md) |
| Recording and ownership | [Record keeping](RECORD_KEEPING.md), [changelog](../CHANGELOG.md); assign bounded agent file ownership before edits |
| Initial schedule and historical estimates | [Project plan](PROJECT_PLAN.md), [progress estimate](PROJECT_PROGRESS.md), [task history](TASK_HISTORY.md); these do not establish current completion |

## Subsystem routes

| Workstream | Plans/contracts | Current evidence and limits |
|---|---|---|
| Dataset acquisition and grouping | [Dataset catalogue](DATASETS.md), [data pipeline](DATA_PIPELINE.md), [registry](../data/registry.json) | [Negative-v3 expansion](NEGATIVE_EXPANSION_V3.md), [1,932-original audit](../records/validation/2026-10-18-combined-intake-audit.json), [admission audit](../records/validation/2026-10-18-negative-v3-admission-audit.json) |
| Human/source review | [Label preparation](LABEL_PREPARATION.md), [human reconciliation](HUMAN_RECONCILIATION.md), [blind fabric evidence intake](FABRIC_EVIDENCE_REVIEW.md) | [Source-label follow-up](SOURCE_LABEL_FOLLOWUP.md), [positive failures](../records/review/2026-10-19-presence-v4-positive-failures.json), [negative failures](../records/review/2026-10-19-presence-v4-negative-failures.json); 17 fabric items await observations and independent human confirmation remains open |
| Training and evaluation | [Training plan](TRAINING_PLAN.md), [evaluation protocol](EVALUATION.md), [GPU setup](GPU_SETUP.md) | [Pleating results](FINETUNING_RESULTS.md), [v3 failed-coverage result](PRESENCE_V3_RESULTS.md), [v4 research result](PRESENCE_V4_RESULTS.md), [v4 failure review](PRESENCE_V4_FAILURE_REVIEW.md) |
| Category-aware experiment | [Category protocol](CATEGORY_PRESENCE_PROTOCOL.md), [chain selection protocol](PRESENCE_JOINT_SELECTION_PROTOCOL.md) | [Completed results](CATEGORY_PRESENCE_RESULTS.md):44 accepted/38 correct/42 negative rejections; archived and independently audited. Research only |
| Fabric labels and sources | [Readiness/admission gate](FABRIC_NEXT_GATE.md), [fabric source next gate](FABRIC_SOURCE_NEXT.md) | [Current source rules/URL audit](FABRIC_SOURCE_GATE_OCT22.md), [earlier search](FABRIC_SOURCE_SEARCH_OCT21.md), [automatic smoke evaluation](FABRIC_AUTOMATIC_EVALUATION.md), [NTNU pilot](NPCGI_PILOT.md); no new fabric admission |
| Length and wearer geometry | [Hemline definition](HEMLINE_GUIDE.md), [adapter contract](GEOMETRY_INTEGRATION.md), [worn extractor](WORN_GEOMETRY_EXTRACTOR.md) | [Geometry replay evaluator](WORN_GEOMETRY_EVALUATION.md), [measured-calibration builder](MEASURED_CALIBRATION.md); real annotations, calibrated profile and validated upstream producer remain missing |
| Application and live behavior | [Architecture](ARCHITECTURE.md), [live controller](LIVE_CONTROLLER.md), [image worker](IMAGE_PIPELINE.md), [camera UI](CAMERA_UI.md) | [Launch/setup](APPLICATION_SETUP.md), [automatic pilot](LIVE_AUTOMATIC_PILOT.md), [v4 saved-frame HTTP](../records/validation/2026-10-19-presence-v4-http.json); saved-image/mocked checks are separate from camera acceptance |
| Packaging and target deployment | [Station-v6 launch/rollback](STATION_PACKAGE.md), [offline release](OFFLINE_RELEASE.md), [Pi plan](RASPBERRY_PI_DEPLOYMENT.md), [dependency strategy](../requirements/README.md) | V1/v2/v3/v5 pass 12 HTTP jobs each; v4 remains an unselected intermediate. [V5 evidence](../records/validation/2026-10-22-station-v5-http.json). [Edge preflight](EDGE_PREFLIGHT.md) is preparatory; every real Pi gate remains open |
| Hardware and capture preparation | [Hardware plan](HARDWARE.md), [borrowing/capture guide](WEBCAM_CAPTURE_GUIDE.md) | No Pi or webcam on October 23; skirts last unavailable October 20. Proposed shopping/runtime combinations and dated camera observations are not current hardware verification |

## Machine-readable record map

| Location | Meaning |
|---|---|
| `data/registry.json` | Registered acquisitions, original counts, admission references and model/data evidence hashes |
| `data/manifests/` and `data/labels/` | Immutable original/curated memberships, provenance, grouped splits and review eligibility; candidates are distinct from admissions |
| `records/acquisitions/` | Actual requests/download outcomes, source terms/metadata, selection and integrity evidence; preserve interrupted failures |
| `records/review/` | Hash-bound agent/human observations, uncertainties and grouping/source flags; observations do not silently become training truth |
| `records/experiments/` | Archived executed code, run/environment/settings, frozen inputs, all saved predictions, metrics and failed runs |
| `records/models/` | Export/release records tying contracts and models to run/data hashes; promotion and Pi status remain explicit |
| `records/validation/` | Test, parity, comparison, HTTP and record-integrity results; inspect each report's denominator and stated scope |
| `records/installations.jsonl`, `records/environments/`, `requirements/` | Actual dependency changes, environment-specific snapshots and separate locks; no universal Pi environment is implied |
| `artifacts/models/`, `artifacts/releases/`, `artifacts/stations/` | Individual exported candidates, immutable app bundles and portable research station payloads; these are not original datasets or clean-machine installers |

Use UTF-8 explicitly when reading/writing manifests. Keep source images, datasets and model artifacts immutable; create a new version when a reviewed correction is justified. A JSON record's existence, an installation plan, a successful conversion or a favorable development score is not evidence of real-garment calibration or ARM64 operation.
