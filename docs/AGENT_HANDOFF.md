# Agent handoff — November 11, 2026

November 12: [GitHub setup and complete migration verification](GITHUB_SETUP_NOV12.md) are finished. The public main branch contains code and progress records; private asset manifest v2 and its prepared ZIP restore all2,804 listed files. Fresh-clone145 tests, exact checkout bytes, restored-record integrity and hosted CI pass. Use the actual checkout root on another computer; recreate environments separately. Station-v9/research-v14 remains research-only; human review, geometry/calibration and physical/Pi acceptance remain open.

November 11 repository preparation: [cross-computer GitHub workflow](GITHUB_WORKFLOW.md) and [private asset transfer](ASSET_TRANSFER.md) are prepared. Public Git carries source, manifests and progress evidence; acquired photos/models/source snapshots and environments stay excluded. Use the current asset manifest and restore privately before model/data checks. Publication status is recorded separately in the current checkpoint.

November 11 implementation: **R01–R04 software tasks are complete**. [Recovery and tool instructions](RECOVERY_IMPLEMENTATION_NOV11.md). Station-v9/research-v14 is selected, with v8 rollback. The 21 raw HTTP failures are preserved and verified as transport evidence; fabric/geometry reviewer tools are tested and documented; essential controls/results fit800 ×480. Human labels, automatic wearer geometry/calibration and physical camera/Pi acceptance remain open.

November 11 current review: [recovery findings and ordered next tasks](PROJECT_REFRESH_NOV11.md). No unfinished GPU run or active scoped station/training process was found. Fabric reviewer server/HTML are partial, the geometry annotation editor is absent, and the completed background attempt acquired zero photos. Twenty-one raw HTTP error responses saved as JSON still fail record parsing. The user reconfirmed no Pi, webcam or skirts. Resume record recovery R01, then reviewer completion R02; do not restart completed fits.

November 11: [progress-report screenshots](PROGRESS_SCREENSHOTS_NOV11.md) capture the actual camera-off UI and implemented source. Five images visually reviewed; temporary server stopped. Earlier label, geometry and hardware acceptance tasks remain open.

November 4 dataset follow-up: four additional [training/validation/test diagrams](THESIS_DATASET_DIAGRAMS.md) and [actual membership evidence](DATASET_PARTITION_EVIDENCE.md) are complete. The [partition auditor](DATA_PARTITION_AUDIT.md) passes 19 focused tests and five actual assignment-set checks. No model was retrained or promoted. Independent labels, final camera/garment tests, calibration and Pi acceptance remain open.

November 4: the existing selected chain was assessed on fixed synthetic brightness and blur changes to the same 118 reused development originals. No model was trained or promoted. [Robustness results](IMAGE_ROBUSTNESS_NOV04.md); [thesis figure pack](THESIS_FIGURES.md). Physical camera, independently verified labels, calibrated length and Pi acceptance remain open.

November 4 latest: station-v8/research-v13 adds requested camera modes and actual decoded-size reporting; v7 is rollback. The user reconfirmed no Pi or webcam. Fifty-two mocked checks and 12 saved-image HTTP jobs pass; physical camera/display and Pi acceptance remain open. [Camera mode evidence](CAMERA_MODE_NOV04.md).

November 4: user selected Waveshare 14447 (800 × 480, HDMI video and USB resistive touch). Station-v7/research-v12 contains the compact landscape UI, verified with 45 mocked cases and 12 saved-image HTTP jobs. Station-v6 is rollback. Physical screen, touch, camera and Pi performance remain unverified. [Waveshare 14447 layout](LCD_14447_LAYOUT.md).

Earlier November 4 review (historical): [November 4 purchase/project review](PURCHASE_REVIEW_NOV04.md). Pi/webcam purchase is planned, not confirmed. Station-v6 remains selected; 73 focused tests and package verification pass. The interrupted October 23 records are reconciled; no preview/training process matched the scoped WSL check. Next software task: explicit camera-mode selection and negotiated-mode reporting, then actual camera/garment collection and ARM64 parity.

This is the continuation entry point for a new AI or human collaborator. Read the current [task board](TASK_BOARD.md) before acting; this document records the recovery checkpoint and operating rules, while new result records establish whether a pending operation actually finished. Dated history is retained rather than rewritten as current status.

Earlier motion checkpoint: **station-v6/research-v11**, with v5 rollback. Eighteen lifecycle scenarios, 21 score cases and six motion cases pass; exact served HTML and inventories verify. October 23 process inspection found no previous preview or training process; the older running-preview entry is historical. [Motion contract](UI_MOTION_OCT22.md).

Latest availability: the user confirms **no Raspberry Pi or webcam on October 23**. Actual skirts were last confirmed unavailable on October 20. Saved-image work can continue; physical calibration, camera acceptance and Pi verification cannot be claimed from it. The [17-item blind fabric queue](FABRIC_EVIDENCE_REVIEW.md) is ready with zero submitted observations; it does not resolve label truth or approve another fit.

Earlier UI checkpoint: **station-v5/research-v10** is selected, with v3 rollback. The supplied UI reference is implemented without changing nine hemline labels, fabric semantics or measurement requirements. A reproduced startup-failure leak was fixed; 18 lifecycle scenarios, 21 score cases and 12 saved-frame HTTP jobs pass. V4/research-v9 is a preserved unselected intermediate. A loopback preview on 8766 intentionally remains running with camera off; verify the process state before restarting it. [Current UI evidence](REFERENCE_UI_OCT22.md).

Earlier October22 checkpoint: station-v3/research-v8 is selected after fixing camera startup interruption status; v2 is rollback and v1 remains preserved. The source rules and cached TextileNet identities were audited without new photos/admissions. Read [the latest batch](CAMERA_SOURCE_UPDATE_OCT22.md) and [fabric gate](FABRIC_SOURCE_GATE_OCT22.md). Full-feature and physical acceptance remain open.

Starter prompt for another AI:

```text
Continue SkirtFabricSense in C:/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense.
Read AGENTS.md, docs/AGENT_HANDOFF.md and records/continuation/latest.json, then the
mandatory project/subsystem records they reference. Verify the current files, hashes,
run status and active processes before fitting or rebuilding anything. Do not restart
completed or active experiments. Follow docs/TASK_BOARD.md for the next open task;
preserve frozen groups, source rights, failed attempts and the one-live-view requirement.
Separate software evidence from real-garment/Pi acceptance, and update the handoff and
continuation record with actual results and the next concrete action before stopping.
```

`records/continuation/latest.json` is the lead agent's machine-readable continuation pointer; if absent, report that absence and audit the saved evidence before relying on an older narrative checkpoint. Its timestamps/status must agree with the actual referenced files.

## Read first

1. [AGENTS.md](../AGENTS.md), [README](../README.md), [requirements](REQUIREMENTS.md) and [decisions](DECISIONS.md).
2. [Active tasks](TASK_BOARD.md), this handoff and the [documentation index](DOCUMENTATION_INDEX.md).
3. The relevant subsystem plan, [record keeping](RECORD_KEEPING.md), and the installed `skirt-fabric-project` skill. Its portable copy is [here](../skills/skirt-fabric-project/SKILL.md).
4. For model/data work, read [training](TRAINING_PLAN.md), [evaluation](EVALUATION.md), [datasets](DATASETS.md) and [the registry](../data/registry.json) before changing inputs.

The user's newer instructions take priority. Preserve one automatic live camera view containing the entire skirt; crops from that same frame are allowed. Worn skirts are primary; hanging, held and mannequin are secondary. Keep pleated/non-pleated, nine hemline categories and the fabric toggle. Main capstone manuscript writing is outside this engineering workspace's scope.

## Verified baseline and unfinished work

| Area | Evidence at this checkpoint | What is still open |
|---|---|---|
| Data | 1,932 audited original images; 207 admitted development negatives, 155 training/52 validation; worn subset 265/66 | Independent human truth, camera-domain diversity and verified physical specimen identity |
| Pleating/detection | Selected station-v8: same localizer-v2 + category-presence-v1;44/66 accepted skirts, 38 correct pleating, 42/52 negatives rejected | 22 source-domain skirt examples unavailable, 10 negatives falsely accepted; no independent camera accuracy |
| Fabric | 17-group source-appearance smoke and five additional unadmitted flat-laid composition-source photos | Final ontology, credible worn rare-class groups, independently confirmed labels and accepted model |
| Length | Geometry adapters, conservative hem helper, measured-calibration builder; October 20 replay evaluator has 19 focused tests | Zero real geometry annotations, automatic validated wearer references and measured calibration |
| Application | Camera-first UI, bounded worker, stale clearing and startup mute fix; v1/v2/v3/v5 pass 12 HTTP jobs each; v5 UI passes18 lifecycle and 21 score cases | Full-feature acceptance, actual garment/camera tests and target runtime |
| Hardware | Laptop GPU training/export verified | No Pi, webcam or skirts on November 11. Camera suitability and every Pi acceptance gate remain open |

The new category comparison passes relative research criteria and preserves v4's aggregate skirt results while rejecting three more negatives. It is not an accepted public demonstration release. Its validation groups were reused for hypothesis and checkpoint selection. No verified project fabric-composition labels or independently verified physical garment count exists. Image/crop counts must never be advertised as specimen counts. The earlier 45% completion figure is historical; do not infer 85% completion from tests or training.

The [latest integration](OCT22_INTEGRATION.md), [category results](CATEGORY_PRESENCE_RESULTS.md), [station launch/rollback instructions](STATION_PACKAGE.md) and [current checkpoint](../records/continuation/latest.json) establish this state. The [October 19 baseline](OCT19_RECOVERY.md), [v4 results](PRESENCE_V4_RESULTS.md) and [failure review](PRESENCE_V4_FAILURE_REVIEW.md) remain historical evidence; failed candidates stay preserved.

## Recovered work — do not repeat completed runs

These results are completed and hash-bound. Verify the files/process state when resuming; do not start another fit merely because a transcript was interrupted.

| Work item | Actual recovery checkpoint | Next action |
|---|---|---|
| Four-way category presence | October 21 run completed and archived under `records/experiments/20261021-category-presence-v1`; epoch 7, actual export44/38/42; independent115-check audit reopened all 118 originals | No repeat fit pending. Next model work needs justified new data/protocol and independent garment validation |
| Portable research station | [Station-v6](../artifacts/stations/skirt-research-station-v6/station.json) selected for motion update;28 files,18 lifecycle/21 score/6 motion cases and exact served HTML verified | October 23: previous preview no longer running. [V5](../artifacts/stations/skirt-research-station-v5/station.json) is rollback with prior12-job HTTP evidence. V4 is unselected; physical acceptance remains open |
| Geometry replay | [Evaluator](../tools/evaluate_worn_geometry.py), [tests](../tests/test_worn_geometry_evaluation.py) and [contract](WORN_GEOMETRY_EVALUATION.md) implemented; [readiness run](../records/validation/2026-10-21-geometry-readiness.json) records zero observed annotations, null coverage and 66 unannotated validation members | Obtain independently reviewed observations and a validated same-frame upstream producer; the [inventory mapping](../records/geometry/2026-10-21-readiness/mapping.json) is not a geometry annotation set |
| Fabric source audit/search | [Existing audit](FABRIC_SOURCE_ATTRIBUTE_AUDIT_OCT20.md), [search](FABRIC_SOURCE_SEARCH_OCT21.md) and [October22 gate/URL audit](FABRIC_SOURCE_GATE_OCT22.md) completed;155,393 cached rows audited, zero new photos/admissions | Source-rule acceptance or another applicable basis, photo attribution, original partitions/product groups and skirt-specific material association must precede intake; do not run the upstream test-first downloader |

The category protocol's original example names an October 20 output folder. The actual root-run folder above is October 21. No October 20 fitting result may be invented from the prepared source or export-only test. The new head uses four hierarchical source scene classes and exports only the skirt probability; it is not a general unknown-object detector. [Protocol](CATEGORY_PRESENCE_PROTOCOL.md).

## Locations and interpreters

| Purpose | Exact location |
|---|---|
| Windows workspace | `C:/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense` |
| Same workspace in WSL | `/mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense` |
| Existing Windows tooling Python | `C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe` |
| Existing WSL training Python | `/home/skirttrain/skirt-fabric-sense/.venv-training/bin/python` |
| WSL distribution/user | `Ubuntu-24.04` / `skirttrain` |
| Active training outputs | `/home/skirttrain/skirt-fabric-sense/runs` |
| Windows access to those outputs | `\\wsl.localhost\Ubuntu-24.04\home\skirttrain\skirt-fabric-sense\runs` |
| Browser lifecycle test runtime | `C:/Program Files/nodejs/node.exe` |

Use these existing environments for the current tools; no installation is required merely to resume. Windows tooling and host Python are not the TensorFlow training environment. The verified GPU route is WSL; package presence alone does not prove GPU execution. Consult [GPU setup](GPU_SETUP.md), actual run `environment.json` files and [separate locks](../requirements/README.md). Older environment documents contain dated pre-install snapshots, not current absence of WSL.

`app/` is mutable source. `artifacts/models/` holds individual exports. Station-v5 copies the new immutable research-v10 app plus unchanged localizer-v2, category-presence-v1 and fabric smoke. V2 retains research-v7 with those same models; v1 retains presence-v4. Dependencies are not included. Linux run output becomes project evidence after executed sources, inputs, environment, predictions and exports are archived under `records/experiments/`.

## Frozen identity checks

The following SHA256 values were rechecked from saved files for this handoff. Match the entire digest, not a short prefix.

| Artifact | SHA256 |
|---|---|
| [Worn subset](../data/manifests/worn-pleating-development-v1.jsonl) | `876bb315009592fdbcf0a646703b21d99801756f4e37b1807a66675bdbd98ec2` |
| [Negative-v3 freeze](../data/labels/negative-reviewed-v3.jsonl) | `82009d40445a9091f7998ab8479cec10b5086826001b7b9f513862bd11da52d1` |
| [Original grouped split](../data/manifests/source-skirt-development-splits.json) | `df3b096e4d131db55852b20de075d811c95520d23766648928555d755fe8812c` |
| Pleating `skirt-finetune-v1/model.tflite` | `c1d8f49e221a2672c20adb87fe4ae5d2f6966f125ee99cb212ff2eb56fffdbf0` |
| Localizer-v2 `model.tflite` | `f2f5f73d34cd99c3fb46502cb806ddbc347c6664e8ce24b8fe06a548c70090de` |
| Presence-v4 `model.tflite` | `7bf9df9b1bacc757956c069f688345ff154ee480a65198ee5948fbe80bbcdb87` |
| Category-presence-v1 `model.tflite` | `f47ddf148102f905d0a81e6a1fe3001b8a4944fd86e0c1c2d635d975f8fdc34d` |
| Fabric-smoke-v1 `model.tflite` | `81f144a1c7cd4910989374a1a86c85e955fb4f65cd81ef88c26e7cbcf1158bfd` |
| Research-v7 `inventory.json` | `0128196438e5b3fb61ba2bab224b351b3de9e9b1e6eb50a171711804bc231eb5` |
| Station-v1 `station-inventory.json` | `7e1e8fea3bfbd8d15614b1f457768d8cecb6bec059658079b0f20374e50ab0a4` |
| Earlier station-v2 `station-inventory.json` | `19444a4ea1622a26822d795bfccb61c558a27383df3741ed84bbeea1544b38f4` |
| Earlier station-v3 `station-inventory.json` | `ec865f2c45a635f7e3abb9fe8bd17dbf0c5b389d47ae110182cf37bee90390f8` |
| Research-v8 `inventory.json` | `97bbfdfe2405528f6ea42eaa2f66ade161a83537feb9a85f1ef41d174cfe822f` |
| Rollback station-v5 `station-inventory.json` | `4d7b14594fd7c85cc7a4e62bb008beb7c18019378bcce10d0e680495f98b0a7d` |
| Selected station-v6 `station-inventory.json` | `2089658f98e34db6d68d29f33f0b51a08cb3a6c8ad625e786aab497b4f0191da` |
| Research-v10 `inventory.json` | `64c91a57f24894b8d5cc406e5629b6359982a28b644755d272437e3f4e0dff7c` |

The binary presence inputs have 538 images: 420 training and 118 validation. Archived `inputs.json` SHA256 is `5fd31356dad9333efaa82cb0e2a312533fe695b5c565278cd00136c9e693a1f7`; split hash is `2da2070b87f9107d4431c32289d3cad242a2929c49185002c1b06971db3ad04f`. Generate byte-compared inputs with the recorded WSL writer: Windows newline differences can change the hash without changing parsed rows. Do not weaken the check or rewrite a historical cache to make a new run pass.

## Commands and recovery rules

Run these from the Windows workspace in PowerShell. They use existing environments and do not install software:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/station_package.py verify artifacts/stations/skirt-research-station-v6
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' tools/validate_records.py
```

Before scheduling any new GPU job, check whether another job is active:

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --exec /usr/bin/pgrep -af '[t]rain_category_presence.py'
```

Read the exact run's `run.json`, `history.json`, copied executed sources, input/target/cache hashes and output files. A `started` record without a live process is incomplete; a successful export-only test is not fitting. Do not start a duplicate run, overwrite a run folder or delete a failed attempt. A restarted experiment needs a new identity and recorded rationale.

For a completed category run, the actual-export comparison command uses its archived inputs and scalar model directory. Those archive/model paths must first exist and verify; never substitute training history for exported inference. See [comparison tool](../tools/check_detection_candidate.py) and the category protocol. Preserve fixed inclusive `0.5` gate/mask thresholds, early conversion and final parity tolerance `0.001`. Evaluate v4 regressions as well as relative gains against v1. Do not promote from a favorable reused-development score alone.

First inspect the current pointer and actual process state for the intentional8766 preview; do not start a duplicate. After station runtime verification is recorded, a research launch from the copied package uses the existing WSL interpreter:

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --cd /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/artifacts/stations/skirt-research-station-v6 --exec /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python -B station_package.py launch . --port 8766
```

This starts only a loopback server; the operator starts the camera in the browser. `--fabric-research` explicitly opts into the unapproved appearance smoke. No flag creates observed waist/floor references or calibrated length. The packaged server's `--root` must point at `application`, because static assets are served from `root/app/static`; the wrapper handles that path. Never build a new package inside an immutable input bundle/model directory. Preserve release directories and run with bytecode writing disabled rather than adding cache files to their inventories.

Use targeted checks for actual changes. The October 22 full Windows suite ran 464 tests, with 461 passing and three framework-dependent skips. The October 21 WSL suite passed 20 actual-framework checks; each station passed 12 HTTP jobs. [Latest evidence](OCT22_INTEGRATION.md). Documentation-only edits need link/integrity checks, not another GPU fit. [Recording rules](RECORD_KEEPING.md).

The later batch ran 30 focused package/release tests and seven metadata tests, plus17 mocked camera scenarios against the packaged v3 UI. Root recomputed the cached metadata and source hashes. The earlier full-suite result is preserved as earlier evidence; no new full-suite count is claimed. [Focused root evidence](../records/validation/2026-10-22-camera-source-check.json).

## Work priorities and closure

- **S01–S03:** independently confirm disputed labels, collect camera-domain negatives, improve dress rejection/minority pleating and evaluate unseen garments. Preserve every frozen denominator and failed candidate.
- **S04–S05:** settle an operational fabric vocabulary and obtain rights-compatible, grouped worn evidence before a stronger fabric experiment. Missing fabric tags are not negatives; cotton/polyester cannot be silently substituted for denim/chiffon appearance.
- **S06:** supply credible same-frame wearer/hem observations and validate extraction using the replay evaluator. Pose hips/ankles remain unobserved candidates, not a waist/floor measurement. Synthetic tests provide zero real geometry accuracy.
- **S07/P01–P07/M01:** full-feature freeze, real garment/calibration/camera tests, actual ARM64 install/benchmark and supervised rehearsal, then separate secondary-mode evaluation. A desktop bundle or preflight cannot close these gates.

For every meaningful batch, root reconciles file ownership and reviews agents' results, updates the registry and dataset catalogue for data changes, links actual evidence in requirements/decisions/task board/changelog, and leaves one concrete next action. Record dependency changes and failures in `records/installations.jsonl`, then snapshot from the changed environment; training and Pi locks stay separate. Preserve provenance, terms, source partitions, group membership and all derivatives. Never tune on protected final-test samples. Do not mark the project complete while fabric, calibrated length, real-garment or Pi acceptance remains missing.
