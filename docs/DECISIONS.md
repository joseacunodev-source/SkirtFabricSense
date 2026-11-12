# Decision log

## November 11 - Public source repository and private asset portability

The user selected https://github.com/joseacunodev-source/SkirtFabricSense and authorized upload and repository metadata setup. The existing repository is public. Keep code, own engineering records, provenance and grouped manifests in Git; transfer acquired images, model payloads and raw source snapshots privately with exact SHA-256 verification. Preserve bytes through `.gitattributes`; recreate platform-specific environments separately. No blanket source license, visibility change or new deployment claim is inferred. [Working instructions](GITHUB_WORKFLOW.md), [asset policy](ASSET_TRANSFER.md).

November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.

## November 4 — Preserve actual subsystem partitions

Report each selected model's recorded train/validation inputs separately. Do not impose a generic three-way ratio on frozen or reused development data. Protected source sanity photos remain distinct from the uncollected final camera/garment test. Add read-only semantic checks; conflicting aliases and frozen catalog reassignment fail. No weights, thresholds, labels or memberships changed. [Evidence](DATASET_PARTITION_EVIDENCE.md), [diagrams](THESIS_DATASET_DIAGRAMS.md), [auditor](DATA_PARTITION_AUDIT.md).

November 4 latest: station-v8/research-v13 adds requested camera modes and actual decoded-size reporting; v7 is rollback. The user reconfirmed no Pi or webcam. Fifty-two mocked checks and 12 saved-image HTTP jobs pass; physical camera/display and Pi acceptance remain open. [Camera mode evidence](CAMERA_MODE_NOV04.md).

November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. [Waveshare 14447 layout](LCD_14447_LAYOUT.md).

## November 4 — Prepare a USB-camera Pi 5 station

Recommend Pi 5 8GB with official power and active cooling; retain 4GB as a budget alternative pending measurements. Prefer one autofocus USB camera for laptop collection and Pi deployment. Defer accelerator/display commitments until full-frame capture and CPU timing are measured. Preserve worn-primary scope, nine hemline classes, fabric toggle and research-only model status. Add capture-mode selection as the next software task; advertised 4K does not prove negotiated 4K. [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md).

## October22 — Keep motion short and independent of inference

Use CSS entrances/control transitions and optional changed-label effects. Keep all result writes/clearing synchronous, suppress repeated-label reveals and numeric-score animation, and respect reduced-motion preference changes. Preserve station-v5; select station-v6/research-v11 after focused tests and exact-HTML verification. No new dependency or inference timing change. [Contract](UI_MOTION_OCT22.md).

## Latest October22 — Adapt the UI reference without inventing measurements

Use the supplied example's visual hierarchy and cream/burgundy palette while preserving the established nine hemline labels, worn-primary workflow and fabric toggle. Do not infer centimetre thresholds, average-body dimensions, global confidence or YOLO implementation from the image. Display only current finite pleating scores, explicitly uncalibrated. Correct the reproduced startup-failure result leak before selecting station-v5/research-v10; preserve v3 rollback and unselected v4. [Evidence](REFERENCE_UI_OCT22.md).

## Later October22 — Preserve interruption state and source admission conditions

Select research-v8/station-v3 for desktop research after reproducing/fixing startup mute-state handling,17 simulated lifecycle cases and 12 saved-frame HTTP jobs. Preserve v2 as rollback and v1 as the older baseline. Models and research-only status are unchanged. Build through an explicit verified app input rather than editing immutable packages. [Evidence](CAMERA_SOURCE_UPDATE_OCT22.md).

Record the actual 2018 rules' acceptance condition without accepting them or importing other years' terms. Audit cached TextileNet metadata and retain duplicate/multi-tag evidence without converting it into confirmed skirt/specimen counts. Do not execute its test-first downloader or adopt test-based checkpoint selection. Applicable rights/attribution, original partitions and garment-specific association remain admission gates. [Source gate](FABRIC_SOURCE_GATE_OCT22.md).

## October22 — Select station-v2 for desktop research and preserve acceptance gates

Select the independently reviewed category-aware gate with localizer-v2 in portable station-v2: it preserves aggregate skirt coverage/correctness while rejecting three more development negatives than v4. Both package HTTP modes pass; preserve station-v1 for rollback. Selection is research-only because10/52 negatives remain false accepts,22/66 skirt examples are unavailable and development groups are repeatedly reused. Do not enable guessed geometry, promote the tiny fabric smoke, or declare Pi compatibility. Preserve original source/copy failures and immutable runs. [Completed review](OCT22_INTEGRATION.md).

Use one agent entry point and hash-bound continuation record to prevent duplicate fits and stale readiness claims after limits. Prioritize iMaterialist2018 terms/grouping/material association before new fabric photos; image-level labels and repo code licences alone do not authorize skirt-specific fabric admissions. The geometry replay remains preparatory with zero actual observations.

## October19 — Preserve development improvement and remaining acceptance gates

Archive failed presence v3 without changing thresholds. V4 selects checkpoints using fixed-threshold complete-chain criteria declared before its training; it passes relative development coverage, correct-pleating and rejection counts, but those reused groups do not establish independent generalization. Keep it optional with localizer v2, preserve defaults/research-v7 and require real-garment acceptance before promotion. Register five selectively acquired composition-source originals as unadmitted: one category conflict and two visibility exclusions prevent automatic metadata admission. Preserve fibre transcriptions separately from visual appearance labels. [Evidence](OCT19_RECOVERY.md), [selection protocol](PRESENCE_JOINT_SELECTION_PROTOCOL.md).

## October 17 — Explicit opt-in research attributes

Finish presentation review without inventing certainty for six isolated product views; preserve direct-original versus sheet evidence and frozen groups. Keep presence v2 unpromoted after48/80→27/80 coverage loss. Permit fabric smoke and body-keypoint candidates only through explicit experimental launch flags, preserving unapproved status and unavailable calibrated length. This supersedes the earlier blanket disconnection of fabric only for research diagnostics; it does not approve the17-item model for demonstration claims. [Evidence](OCT17_NEXT_MILESTONE.md).

## October 17 — Preserve observation and deployment boundaries

Keep supplemental presentation labels separate from frozen training labels. Do not promote v2/v3 after repeated negative failures. A source-mask hem extractor requires independently observed wearer references and measured uncertainty; do not substitute pose hips for visible waist or enable live length from synthetic fixtures. Preserve research-v5 and package source changes as research-v6. [Evidence](OCT17_INTEGRATION.md).

## October 16 — Worn skirts primary, other presentations secondary

User explicitly confirmed keeping hanging, held and mannequin modes secondary. Prioritize worn-skirt UI guidance, future data review and geometry integration; preserve all four mode values and existing frozen datasets/models. Supersedes equal presentation priority and the hanging-first collection proposal, not historical experiment evidence. [Implementation and next gates](WORN_PRIMARY.md).

## October15 — Keep failed candidates and conflicting metadata out of deployment

V3 tests image-class balanced loss only, on unchanged development inputs; it worsens non-skirt rejection and is not promoted. Runtime preprocessing/threshold/tensor-count mismatches now fail before inference. Fine-subset train metadata is not interchangeable with the original benchmark partition: retain exact joins, mark encountered broader-holdout labels as exposed metadata, and exclude unresolved folder overlap from admission. No new fabric images or model claims follow from metadata counts. [Evidence](RECOVERY_OCT15.md).

## October14 — Supervised demo scope and localizer v2

The user clarified85% as project completion for a supervised capstone demonstration, not prediction accuracy. Keep the full feature scope and physical acceptance requirements. V2 localization learns empty masks from reviewed negatives, preserves earlier splits and uses a fixed0.5 mask threshold. Its improved positive coverage does not offset worse negative rejection; archive it without changing the live default. [Evidence](LOCALIZER_V2_RESULTS.md), [demo acceptance](SUPERVISED_DEMO.md).

## October 14 — Close interrupted intake without promoting candidates

Register only the 120 successfully acquired negative originals; preserve the stopped fabric attempt separately with zero new images. Source absence annotations, thumbnail review and unique hashes do not constitute label approval or garment identity. Keep current validation assignments and original query/gallery protection. Prioritize rare-class fabric sources instead of treating more cotton or alternate views as balanced independent training data. [Evidence](DATA_EXPANSION_OCT13.md).

## October 12 — Preserve failed candidates as evidence

The exported presence candidate stays disabled: paired skirt coverage drops from 48/80 to 25/80, despite rejection rising from 1/3 to 3/3 negatives. Three negatives are insufficient for promotion. The unchanged v1 localizer remains experimental; no mask retraining occurred. Fabric training is a 17-item source-appearance smoke only, with five validation items, and is not connected to the fabric toggle. Keep these actual results rather than reporting completed training as improved product quality.

Length requires independently supplied same-frame geometry and a measured reference profile. The new adapter/profile validator abstains on absent or inconsistent evidence, and extractor failure affects length only. Do not infer a body reference from a segmentation rectangle. No actual calibration or Pi compatibility is claimed. [Review](OCT12_INTEGRATION.md).

October 11: preserve original DeepFashion InShop train/query/gallery membership after the exact filename join. Do not import query/gallery examples to fill missing knitted/other training classes. Acquire a bounded original-train appearance sample and keep all new fabric/negative candidates unadmitted until visibility, labels, grouping and source rights are checked. The 40/90 negative-candidate acceptance diagnostic does not justify threshold tuning or deployment promotion. [Evidence and next experiment gate](DATA_INTAKE_OCT11.md).

October 10 implementation decisions: enable automatic camera frame submission, but require an explicit `--experimental-localizer` launch flag for provisional automatic pleating. The localization pilot has no image-level negative validation; masks do not prove presence or full visibility. Keep fabric and hemline unavailable until evidence-backed adapters exist. Use a 1,000 ms browser acquisition-age ceiling for current results, separate from the longer manual-image worker TTL. Keep the original source split and 372-image pilot unchanged; archive the localization model separately from the pleating release. [Implementation and evidence](LIVE_AUTOMATIC_PILOT.md).

All dates use Asia/Manila. Status values: accepted constraint, proposed, unresolved, superseded. Proposals are not measured outcomes.

| ID | Date | Decision/status | Reason and consequence |
|---|---|---|---|
| D001 | 2026-10-01 | Accepted: one full-skirt view | User rejected two-view and sequential close-up options. Native crops from one source frame are allowed. |
| D002 | 2026-10-01 | Accepted: include fabric, skirt attributes and length | Fabric is a core feasibility task, not silently removed from the project. |
| D003 | 2026-10-01 | Accepted: live automatic output | Deliberate capture may save a record but is not required for each prediction. |
| D004 | 2026-10-01 | Proposed: Pi 5 CPU deployment | Early lightweight baseline, export and on-device verification before accelerator purchases. Pi4 in the source proposal is not assumed fixed. |
| D005 | 2026-10-01 | Proposed: TensorFlow/Keras GPU training through WSL2 | Fits the CNN/export path. WSL2 absent; no training environment yet installed. Current GPU driver presence does not prove framework operation. |
| D006 | 2026-10-01 | Proposed: separate style and fabric baselines | Different image evidence and failure modes. Compare whole-view and native crop fabric inputs empirically. |
| D007 | 2026-10-01 | Unresolved: fabric ontology | Fiber versus construction labels overlap. Must establish annotation rules before final labels or training claims. |
| D008 | 2026-10-01 | Unresolved: style taxonomy and length boundary | Four combinations proposed; non-pleated is not synonymous with straight, long is not synonymous with maxi. |
| D009 | 2026-10-01 | Accepted: technical records are part of every change | User wants evidence for later paper updates and complete Pi installation notes. Main paper is outside scope. |
| D010 | 2026-10-01 | Accepted: bounded multi-agent work | User authorized groupmates. Current research divided into data, ML, deployment and root integration. |
| D011 | 2026-10-01 | Accepted: obtain internet datasets with provenance | Actual metadata/image acquisition distinguished from access links; no authentication bypass. |
| D012 | 2026-10-01 | Proposed: eight-week plan, week-four prototype | Current assets are limited; feasibility and data precede polish. |
| D013 | 2026-10-01 | Accepted: install relevant skills, keep minimal scope | Jupyter workflow plus project-specific guidance; skills are not Pi runtime packages. |
| D014 | 2026-10-02 | Accepted: expand toward 1,000 images with delegated review | Acquired 1,000 source skirt images plus 500 supplementary fabric candidates; root audited files and tests after agent interruptions. |
| D015 | 2026-10-02 | Accepted engineering safeguard: source labels stay distinct | FabNet archive lacks documented train/val split and contains possible blend conflicts. Preserve unknown partition and candidate status; do not infer composition. |

When a decision changes, add a dated entry and mark superseded entries. Include evidence path, alternatives considered, impact on collected labels/models, and which requirements changed. Never erase the reason an old experiment used different settings.

## 2026-10-03 decisions

- D016: Keep source manufacturing labels separate from project pleating truth. Explicit no-special-manufacturing is an auxiliary source class; missing pleat is unknown. Preserve original grouped assignments. See [label preparation](LABEL_PREPARATION.md).
- D017: Proceed with the D005 WSL2 TensorFlow route. Windows prerequisite enablement succeeded but requires restart. Do not replace it with obsolete native-Windows TensorFlow or claim GPU readiness. See [setup evidence](GPU_SETUP.md).

- D018 (2026-10-03): D005/D017 training route is installed and infrastructure-verified: WSL2, Ubuntu24.04, TensorFlow2.20, isolated non-admin Linux user environment. Use Keras export after observed generic SavedModel/TFLite variable failure. [Evidence](GPU_SETUP.md). Pi validation remains separate.

- D019 (2026-10-04): Freeze an agent-reviewed pleating pilot after quarantining review conflicts and suspected garment components; keep existing splits and source holdout untouched. Human verification remains pending.
- D020 (2026-10-04): First MobileNetV2 pilot uses frozen backbone and five head epochs; select by validation loss, not the highest observed accuracy. Retain unsuccessful parity gate; strict FP32 evaluation fixes TF32 numerical differences without changing weights, tolerance or predictions. [Evidence](BASELINE_RESULTS.md).

- D021 (2026-10-04): Compare one fine-tuning plus mild augmentation candidate against the archived baseline with identical data/splits. Preserve the original and select by validation loss. Weight invariants and export parity passed; apparent gain is preliminary. [Evidence](FINETUNING_RESULTS.md).
- D022 (2026-10-04): User has no physical skirts yet. Prepare borrowing/capture records; do not claim webcam-domain or fabric-composition evidence until garments are obtained and documented.


- D023 (2026-10-04): Implement a local browser file-image pilot to verify inference and annotation workflows before hardware is available. Preserve the final one-camera automatic requirement; manual ROI and framing confirmation are development-only. Human review events require reconciliation and a new explicit training release. Package models/app without datasets or training dependencies; Pi compatibility remains unverified.

- D024 (2026-10-05): Build and test the latest-frame controller independently of camera hardware. Retain one active inference claim and one waiting frame; invalidate results by generation and capture age. Explicit synthetic time limits are test configuration only. Do not clear an active claim on scene change because that would permit overlapping inference before the old worker exits.

- D025 (2026-10-05): Connect the controller through a single image-copying worker before camera integration. Require explicit validity/framing and scene events; do not portray them as automatic detection. Report shutdown timeout truthfully instead of pretending an in-flight interpreter was terminated.

- D026 (2026-10-05): Integrate the file-image UI through one station-level asynchronous worker. Keep only the current job, scope cancellation by opaque job ID and preserve browser generation checks. Saved-image results are explicitly distinct from future live-camera output. Preserve the original application bundle and build async-v2 without changing model weights.

- D027 (2026-10-06): User reaffirmed live automatic camera output and requested a plain UI. Make camera preview the default page and move image testing into a secondary development tool. Keep missing detection/fabric/length capabilities visibly unavailable; do not substitute manual uploads for the final workflow.

- D028 (2026-10-09): User requests nine hemline categories from their reference and independent pleated/non-pleated output, across worn, hanging, mannequin and held presentations. Supersede tentative short/long labels. Non-worn body-reference policy remains open; do not infer wearer-relative length from an unreferenced crop. Fabric remains in scope pending explicit user removal.

October 9 clarification: user selected a calibrated standard mannequin/body reference for hanging and held skirts; outputs must be labelled as estimates relative to that reference. The physical dimensions, camera calibration and class boundaries are not yet established. Fabric recognition remains required with an operator on/off switch. The camera UI switch persists locally and shows disabled or model-unavailable states; no fabric inference is claimed.
