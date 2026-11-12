# SkirtFabricSense

November 11 implementation: [all four recovery/software tasks are complete](docs/RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected for desktop research; v8 is rollback. Human review, model-quality and physical acceptance remain open.

November 11: [refreshed project status and next tasks](docs/PROJECT_REFRESH_NOV11.md). Station-v8 remains the desktop research selection. Recover interrupted evidence/reviewer work before more training; the user confirms no Pi, webcam or skirts yet.

November 4: added [training/validation/test diagrams](docs/THESIS_DATASET_DIAGRAMS.md) and verified actual per-model memberships with a read-only partition auditor. The 420/118 split belongs to category presence; final camera/garment testing remains uncollected. [Current continuation entry point](HANDOFF.md).

November 4: five [thesis figures](docs/THESIS_FIGURES.md) and a [saved-image robustness diagnostic](docs/IMAGE_ROBUSTNESS_NOV04.md) are available. This is reused development evidence, not improved or independent accuracy.

November 4 latest: station-v8/research-v13 requests camera modes and displays actual decoded dimensions. [Details](docs/CAMERA_MODE_NOV04.md). No Pi or webcam is currently available.

November 4: station-v7/research-v12 contains the compact 800 × 480 layout for the selected Waveshare 14447. [Layout and limitations](docs/LCD_14447_LAYOUT.md). Pi and physical screen verification remain open.

November 4: reviewed the project before planned Pi/webcam purchase. [Buying recommendation and bring-up order](docs/PURCHASE_REVIEW_NOV04.md). Station-v6 inventory and 73 focused tests pass; fabric, wearer geometry and Pi acceptance remain open. No purchase, installation or new model improvement is claimed.

**Continuing with another AI or after a limit:** read [HANDOFF.md](HANDOFF.md), [the detailed agent handoff](docs/AGENT_HANDOFF.md), [the current checkpoint](records/continuation/latest.json), and [the documentation index](docs/DOCUMENTATION_INDEX.md). The checkpoint separates verified results, selected research versions and unfinished acceptance tasks.

Current animation update: **station-v6/research-v11**, with v5 rollback. Added restrained transitions, reduced-motion support and changed-label reveals; immediate clearing is preserved. [Motion evidence](docs/UI_MOTION_OCT22.md).

Current actions: [active task board](docs/TASK_BOARD.md), with completed work separated from prioritized software/data tasks and garment/Pi dependencies. Historical task notes are preserved in [task history](docs/TASK_HISTORY.md).

Earlier October22: **station-v5/research-v10** adapts the supplied cream/burgundy UI reference, preserves nine hemline categories and the fabric toggle, and fixes startup-failure clearing. Eighteen lifecycle scenarios, 21 score cases and 12 saved-frame HTTP jobs pass. V3 is rollback; v4 is an unselected intermediate. Models/data are unchanged, and fabric quality, calibrated length and physical/Pi acceptance remain open. [UI evidence and hardware-free tasks](docs/REFERENCE_UI_OCT22.md), [launch/rollback](docs/STATION_PACKAGE.md).

Earlier October22: station-v3 added startup interruption handling and verified desktop integration. Fabric source terms/URL identity checks added no photos or admissions. [Earlier batch](docs/CAMERA_SOURCE_UPDATE_OCT22.md), [recovered training](docs/OCT22_INTEGRATION.md).

October19 recovery: **1,932 audited originals**; all 180 new negatives reviewed,132 newly admitted into a frozen207-example negative extension. Presence v4 plus localizer v2 passes the relative development comparison (44/66 skirts accepted, 38 correct pleating,39/52 negatives rejected) and saved-frame HTTP checks. It remains optional research; fabric, calibrated length and real-garment/Pi acceptance are unfinished. [Results and next gates](docs/OCT19_RECOVERY.md).

October 17 next milestone: all372 presentation records reviewed (331 worn), frozen265/66 worn subset, expanded presence experiment, opt-in fabric/pose research paths, and research-v7 HTTP verification. Presence still loses too much coverage; calibrated length and physical/Pi acceptance remain open. [Evidence and remaining tasks](docs/OCT17_NEXT_MILESTONE.md).

October 17: integrated worn-presentation and fabric review records, conservative mask-to-hem extraction, localizer failure analysis and the verified research-v6 desktop bundle. Live length/fabric remain unfinished. [Completed evidence and remaining gates](docs/OCT17_INTEGRATION.md).

October 16: worn skirts are now the primary workflow; hanging, held and mannequin presentations remain secondary by user request. Camera guidance and collection priorities follow this order. This changes scope priorities, not model accuracy or calibration readiness. See [worn-first implementation plan](docs/WORN_PRIMARY.md).

Engineering workspace for an offline Raspberry Pi system that estimates skirt attributes, length, and fabric category automatically from **one live camera showing the complete skirt**.

## Current state

October15: recovered and completed the balanced-localizer experiment, but rejection worsened, so it remains unpromoted. Hardened model-loading contracts and verified a new desktop bundle with saved-frame HTTP checks. Additional fabric metadata was joined to original partitions; holdout and unresolved grouping conflicts prevent new admissions. [Recovery evidence and remaining work](docs/RECOVERY_OCT15.md). No physical skirts or Pi are available yet.

Latest October14 improvement: all120 new originals reviewed;63 new negative admissions yield56training/19validation negatives. Localizer v2 improves accepted skirts to59/80 and correct pleating to52/80, but worsens non-skirt rejection, so it is not enabled by default. [Results](docs/LOCALIZER_V2_RESULTS.md). The user's85% target means completion for a [supervised capstone demonstration](docs/SUPERVISED_DEMO.md); it has not been reached.

October 14: interrupted intake records are reconciled. The collection now has **1,747 audited originals**, including 120 newly acquired negative candidates awaiting full-original label/group review. The fabric expansion attempt downloaded zero images and is recorded separately. All 43 targeted recovery/data tests passed. Overall completion is estimated at **about 45%**, with model quality, automatic geometry and real Pi validation still outstanding. [Progress estimate and remaining milestones](docs/PROJECT_PROGRESS.md), [intake evidence](docs/DATA_EXPANSION_OCT13.md).

October 12: reviewed and archived the presence and fabric runs. Negative review admitted 12/90 candidates; fabric review admitted 17/25 only for a smoke experiment. The presence gate reduces accepted skirts from 48/80 to 25/80, so it is **not promoted**. Fabric remains disconnected from live inference. The hemline evidence adapter is implemented; automatic geometry extraction and measured calibration remain outstanding. [Current review and remaining work](docs/OCT12_INTEGRATION.md). Dated entries below are historical.

As of **2026-10-10**, the laptop GPU environment is installed and verified. Two pleating pilots and a full-frame localization pilot have been trained. The fine-tuned pleating model achieved **65/80 correct (81.25%), macro F1 0.7540** using annotated crops. The experimental automatic path accepted 48/80 images and classified 38 correctly. These are agent-labelled development results, not independent test or webcam accuracy. Raspberry Pi execution remains unverified.

As of October 11, the dataset contains **1,627 original images**: 1,000 skirt candidates, 500 supplementary texture candidates, 12 protected seeds, 90 new non-skirt candidates and 25 new full-view fabric candidates. The new candidates are not admitted to training. The frozen pleating pilot remains 292 training / 80 validation images. [Intake, resolved source partitions and rejection diagnostic](docs/DATA_INTAKE_OCT11.md). Human label confirmation and verified fabric ground truth remain outstanding.

A camera-first local application now submits frames automatically, with optional experimental localization and pleating. A physical browser preview connected at 640×480 and was stopped after testing. Fabric recognition, calibrated length and real Pi integration remain unfinished. See [current pilot and launch instructions](docs/LIVE_AUTOMATIC_PILOT.md), [bundle instructions](docs/OFFLINE_RELEASE.md) and the [task board](docs/TASK_BOARD.md).

The user wants the strongest practical software and hardware implementation within approximately one to two months. These are engineering records for later use in the capstone paper; the paper itself is outside the work scope.

## Start here

1. [Project plan and milestones](docs/PROJECT_PLAN.md)
2. [Requirements and acceptance checks](docs/REQUIREMENTS.md)
3. [Architecture](docs/ARCHITECTURE.md)
4. [Training plan](docs/TRAINING_PLAN.md) and [evaluation](docs/EVALUATION.md)
5. [Datasets and acquisition status](docs/DATASETS.md), with [machine-readable provenance](data/registry.json)
6. [Hardware shortlist](docs/HARDWARE.md) and [Raspberry Pi deployment](docs/RASPBERRY_PI_DEPLOYMENT.md)
7. [Environment and dependency records](docs/ENVIRONMENT.md) and [dependency strategy](requirements/README.md)
8. [Documentation workflow](docs/RECORD_KEEPING.md), [decisions](docs/DECISIONS.md), and [skills](docs/SKILLS.md)

## Important boundaries

- One full-skirt view is fixed. Fabric patches may be cropped from the original frame in software; a second camera or user-presented close-up is not part of the product.
- Fabric class definitions remain unresolved: cotton/polyester are fibers while satin/chiffon/denim describe other textile properties. Do not silently treat them as mutually exclusive ground truth.
- A fixed capture station and a physical scale/reference are proposed for repeatable length estimates. Arbitrary viewpoints or wearer-relative lengths are not yet supported.
- Raspberry Pi 5 is the provisional target, not a purchased or verified configuration.
- Internet data supplements deployment-camera data. Downloaded metadata is not equivalent to a ready-to-train image dataset.
- Confidence scores are model outputs, not measured accuracy or fiber composition percentages.

## Reproducibility

Run the standard-library environment collector using the interpreter being documented:

```text
python tools/collect_environment.py --role training --output records/environments/my-training-environment.json
```

It checks a limited list of tools and packages without installing software, reading environment variables, recording serial numbers, or importing training frameworks. It does record local executable paths. The actual initial snapshots live in [records/environments](records/environments/).

Record changes as they happen, not from memory at the end. Use [templates](templates/) for installations, experiments, and model releases. See [CHANGELOG](CHANGELOG.md) for completed work.

## October 3 preparation update

Versioned label preparation now covers all 1,000 skirt records: 612 source-annotation auxiliary examples and 13 single-agent reviewed full-skirt appearance examples. Final ground-truth labelling is incomplete; the latter has inadequate validation coverage. Fabric text triage covers all 500 candidates, with zero verified composition labels. See [label preparation](docs/LABEL_PREPARATION.md) and [fabric review](docs/FABRIC_LABEL_REVIEW.md). WSL prerequisite features were enabled, but Windows explicitly requires a restart; TensorFlow GPU setup remains pending. See [GPU setup handoff](docs/GPU_SETUP.md).

## GPU setup verified

After the October 3 restart, WSL/Ubuntu and isolated TensorFlow 2.20.0 were installed. A synthetic GPU training step and corrected float TFLite export/parity passed. This supersedes the earlier pending GPU status. No dataset classifier has been trained. See [GPU setup evidence and run command](docs/GPU_SETUP.md).

## First model trained â€” October 4

All 1,000 skirt candidates have agent visual reviews. A conservative 372-image pleating pilot (292 training / 80 validation) produced the first MobileNetV2 model. Selected-checkpoint validation accuracy is 78.75%, macro F1 0.7213; majority baseline accuracy is 75%. Float TFLite parity passed after strict-FP32 verification. These are provisional agent-labelled development results, not live-camera or Pi accuracy. [Results, model files and limits](docs/BASELINE_RESULTS.md).

## Fine-tuned candidate â€” October 4

A controlled follow-up improved development accuracy to81.25% (65/80) and macro F1 to0.7540. Float TFLite parity and frozen-layer checks passed. Original model remains preserved. [Comparison and model files](docs/FINETUNING_RESULTS.md). The user has no physical skirts yet; [borrowing/capture guide](docs/WEBCAM_CAPTURE_GUIDE.md) prepares the next data stage.
