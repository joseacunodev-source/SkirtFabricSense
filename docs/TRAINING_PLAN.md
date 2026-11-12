# Training and model delivery plan

November 4: the existing selected chain was assessed on fixed synthetic brightness and blur changes to the same 118 reused development originals. No model was trained or promoted. [Robustness results](IMAGE_ROBUSTNESS_NOV04.md); [thesis figure pack](THESIS_FIGURES.md). Physical camera, independently verified labels, calibrated length and Pi acceptance remain open.

October22: the declared category-aware experiment is complete, archived and independently reviewed. It preserves44 accepted skirts/38 correct pleating and raises negative rejection to42/52 versus v4's39/52 on the reused development set. Station-v2 is selected only for research. No repeat fit is pending; next priorities are credible new fabric data/labels, camera-domain challenge groups and observed wearer geometry. [Results](CATEGORY_PRESENCE_RESULTS.md), [current handoff](AGENT_HANDOFF.md).

October19: source/label follow-up and the frozen155/52 negative extension support two archived presence runs. V3 loses coverage; v4's fixed-threshold chain-aware checkpoint selection passes the relative development criteria and actual-export/HTTP checks. It remains research-only because development groups are repeatedly reused and camera/Pi acceptance is absent. Next priorities are credible worn-fabric labels/groups, independent label confirmation and validated wearer references. [Results](OCT19_RECOVERY.md), [v4 selection protocol](PRESENCE_JOINT_SELECTION_PROTOCOL.md).

October17 active queue: presentation review and the265/66 worn subset are complete. Next are source/label corrections, diverse negative groups and joint coverage/rejection improvement, then fabric ontology/rare-class expansion and validated wearer-reference extraction. Existing failed candidates stay unpromoted. See S01–S06 in the [task board](TASK_BOARD.md); the original scheduling sections below are historical planning targets.

October 16 priority update: prioritize worn-skirt detection, pleating, full-frame fabric evidence and actual-wearer geometry. Future review must record presentation and report worn results separately. Do not silently filter or reassign existing frozen train/validation groups; any worn-only subset needs a new hashed manifest and documented exclusions. Include worn pants, shorts and dresses as reviewed negatives. Secondary presentations remain in scope. [Plan](WORN_PRIMARY.md).

Status: proposed implementation plan; no training run or model performance is claimed here. Reviewed 2026-10-02, Asia/Manila. This file documents engineering work and evidence needed for the project; it does not revise the capstone manuscript.

## Fixed product requirement

One camera must keep the whole skirt visible and automatically produce skirt style/pleating, length, and image-based fabric estimates from that view. Fabric patches may be cropped in software from the original frame. A separate close-up, a second camera, or asking the user to move the fabric toward the camera is outside scope.

The application must run offline on the selected Raspberry Pi. Training and conversion run on the laptop. The provisional deployment target is Raspberry Pi 5 with 64-bit Raspberry Pi OS and CPU inference using exported `.tflite` models. Compatibility means successful installation and measured operation on an actual Pi, not merely successful conversion on the laptop.

Fabric recognition from this view is the highest uncertainty. A full-skirt image may show drape, sheen, and coarse texture while lacking fiber or weave detail. The pilot must establish which agreed categories can be estimated under the allowed capture conditions. Higher image resolution does not undo blur or establish fiber composition.

## Decisions to settle before expensive training

| Decision | Working position | Required record |
|---|---|---|
| Skirt labels | Pleated/non-pleated; nine separate hemline labels: Micro, Mini, Above knee, On knee, Below knee, Midi, Tea, Maxi, Full | Versioned definitions and calibrated boundaries; do not reuse the superseded short/long taxonomy |
| Straight versus non-pleated | Treat these as different concepts; do not relabel one as the other silently | Final vocabulary and mapping from any imported labels |
| Fabric labels | Unresolved: cotton/polyester are fiber labels; satin/chiffon/denim describe fabric categories and can overlap | Taxonomy, label evidence, blends/mixed-material policy, unknown policy |
| Presentation geometry | Support worn, hanging, mannequin and held modes from one full-skirt frame | Per-mode reference association, calibrated projection, supported placement tolerance |
| Length meaning | Body-relative hemline; hanging/held use a calibrated standard body/mannequin reference and are labelled estimates | Eight calibrated boundaries, reference identity, uncertainty intervals and borderline policy |
| Worn skirts | Required by the user; observed body reference and separate evaluation | Same-frame body/hem evidence, garment grouping and worn-mode evaluation |
| Camera | Compare current webcam and shortlisted replacement at the same full-skirt framing | Native image dimensions, exposure/focus settings, actual garment pixel coverage |

If the required output includes both fiber and construction, use separately labelled outputs with missing-label masks where evidence is absent. Do not force an example labelled “polyester satin” into mutually exclusive polyester-versus-satin classes. If a single vocabulary is required, document a defensible operational mapping before training. Do not invent ground truth from appearance or a product title alone.

Length is not learned from a normalized crop without a reference: resizing removes absolute scale. Start with calibrated image geometry and detected waistband/hem positions. A pixel-to-centimetre mapping is valid only within the tested plane and perspective. Recalibrate after moving the camera or fixture. A “maxi” label must not be used as a synonym for every skirt placed in the long class.

## Training environment and installation evidence

Hardware reported by the main project inspection: ASUS TUF Dash F15; Intel i5-11300H, 4 cores/8 threads; RTX 3060 Laptop GPU with 6 GB VRAM; about 16 GB RAM; Windows 11. WSL was absent at that inspection. These are inventory inputs, not a completed ML environment validation.

Suggested route: WSL2 Ubuntu, an isolated Python virtual environment, TensorFlow/Keras GPU training, and TensorFlow's `.tflite` converter. Current TensorFlow guidance routes newer CUDA-enabled Windows installations through WSL2; native Windows GPU support ended with TensorFlow 2.10. Select compatible releases when installing and record the tested versions rather than assuming that “latest” forms a working set. [TensorFlow installation guide](https://www.tensorflow.org/install/pip)

WSL GPU support uses the Windows NVIDIA driver. Avoid installing a Linux NVIDIA display driver inside WSL. Follow the official WSL-specific instructions and record the Windows driver, WSL/kernel, distribution, and Python versions. [NVIDIA CUDA on WSL guide](https://docs.nvidia.com/cuda/wsl-user-guide/index.html)

Before marking the training environment ready:

1. Record disk capacity and reserve space for datasets, WSL, caches, checkpoints, and exports. Use a bounded dataset acquisition plan; avoid filling the system drive.
2. Log every installation command, date, outcome, package source, and reason in the project installation records. Keep secrets and access tokens out of logs.
3. Record Python, TensorFlow, Keras, CUDA runtime packages, NVIDIA driver, NumPy, image tooling, and evaluation tooling versions. Save a complete resolved dependency lock/environment export.
4. Verify that TensorFlow sees the RTX GPU and complete a small forward/backward training step. Save the command and output, not just a screenshot of a successful import.
5. Run a converter smoke test and execute the resulting model in the selected laptop interpreter.
6. Keep training data/caches inside an appropriate local filesystem, with a documented mapping to the Windows project. Avoid simultaneous OneDrive synchronization of active checkpoints or a running WSL virtual disk.
7. Add the exact corresponding runtime installation record when the Pi is available. CUDA, notebook tools, and the full training stack are not Pi runtime requirements.

Starting resource settings are batch size 16 at 224 x 224 and one training job at a time. Lower the batch size if measured VRAM use requires it. Mixed precision is optional after the float32 baseline works; preserve numerically suitable float32 outputs and retest conversion. Do not prescribe training time from GPU specifications alone.

## Dataset admission and split protocol

Internet data supplements local full-skirt data; it does not replace device-domain validation. Consult the project dataset catalogue for source URLs, license/access terms, requested/downloaded status, checksums, and task suitability. Acquisition is not proof that a dataset supports the required fabric labels.

Each image must have, as applicable:

| Field | Purpose |
|---|---|
| `sample_id`, `sha256`, `original_path`, `parent_sample_id` | Identity, exact-file integrity, and derivative lineage; use the canonical names in the versioned manifest schema |
| `source_id`, `source_url`, `source_item_id`, `license_id` | Provenance and reuse constraints |
| `garment_id`, `specimen_id`, `group_id` | Prevent the same physical item or related listing crossing partitions |
| `session_id`, `video_id`, `frame_timestamp` | Link correlated video frames and collection sessions |
| `camera_id`, settings, native dimensions, fixture/calibration version | Capture reproducibility |
| `pleating_label`, `style_label`, `length_label`, measured length | Separate attribute targets and geometry ground truth |
| `fabric_construction`, `fiber_composition`, evidence reference | Preserve overlapping textile facts and label confidence |
| `label_status`, reviewer, review date | Verified, disputed, unknown, or missing labels |
| `split`, `split_manifest_version` | Reproducible assignment |

Use only labels supported by that dataset's actual annotation. Missing fabric labels are missing, not “other fabric.” Original images remain immutable. Crops, resized files, extracted frames, and augmentation derivatives inherit the parent's group and split.

Split by connected groups of the same garment/specimen, product listing, session linkage, and duplicate/near-duplicate relationships. Exact hash matching alone cannot identify every duplicated product photo. Where identity cannot be resolved, quarantine the uncertain examples from final evaluation. Keep an internet source/domain holdout where practical to expose source-specific shortcuts.

For a small pilot, use grouped cross-validation inside the development pool and reserve a small separate set of unseen physical garments as an untouched feasibility check. As data grows, freeze explicit train, model-validation, calibration/threshold-validation, and final-test group manifests. A planning allocation is roughly 65/15/10/10 by independent groups, adjusted before training to ensure usable per-class counts. Ratios never justify a one-item class test. If counts are too small, use grouped cross-fitting within development data and report the limitation instead of pretending the percentages ensure validity.

Grouped splitters are designed to keep related samples together; class stratification is approximate and the resulting class counts still require inspection. [Scikit-learn grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data)

Do not tune model architecture, augmentation, camera settings, thresholds, calibration, patch selection, or smoothing on the final test set. Representative data used for INT8 conversion comes from training data only. Keep it distinct in records from data used to calibrate output confidence.

## Pilot capture and sample targets

These are acquisition targets for feasibility, not claims of adequate statistical power or guaranteed performance:

- Seek 10-15 distinct garments for each proposed fabric category, with varied colors/patterns and both pleating states where possible. A skirt may support multiple attribute records without becoming multiple independent specimens.
- Cover each provisional skirt combination with at least 10 distinct garments in the pilot if access permits. Record gaps and prioritize collection over repeated photos of the same skirt.
- Capture short full-skirt clips from repeat placements under normal light and a small number of controlled lighting changes. Store selected nonredundant frames; track every source clip.
- Reserve unseen garments across categories for the feasibility check. Report exact counts and uncertainty; a small pilot cannot support a final accuracy claim.
- Collect empty backgrounds and non-skirt items under the same station conditions. Include shorts, dresses, trousers, loose fabric, hands/people, and partial or multiple garments.
- Ensure fabrics occur across more than one color, style, and source. A category available in only one shape or color is a dataset gap.

For expansion, budget toward 30-50 distinct development garments per fabric category and broad style coverage, subject to access. The final-test aim in `EVALUATION.md` is an additional 15-20 unseen garments per category; those garments are reserved before development begins and are not borrowed for tuning. These are planning ranges, not requirements from a power calculation. Set absolute per-class counts before choosing split ratios: the illustrative 10% final-test allocation above is not appropriate when it leaves only three to five garments in a class. Learning curves and the number of independent held-out garments determine whether more data is needed. Record specimen counts first and image counts second, and document an explicit lower-data protocol if access cannot meet the aim.

## Model experiments, in order

| ID | Experiment | Question answered | Deliverable |
|---|---|---|---|
| M00 | Constant/majority baselines; geometry-only length baseline | What must a learned model beat? | Baseline metrics and calibration error |
| M01 | MobileNetV2 transfer learning on whole-skirt ROI, 224 x 224 | Can pleating/style generalize to unseen garments? | First trained checkpoint and float `.tflite` |
| M02 | Separate MobileNetV2 fabric baseline on whole-skirt ROI | Does full-image appearance contain a usable signal? | Grouped development results and confusion matrix |
| M03 | Same fabric backbone on native-resolution patches from that frame | Do preserved local details improve fabric performance? | Paired results versus M02 and patch compute cost |
| M04 | Combine whole-skirt and patch predictions only if M03 justifies it | Does fusion improve held-out performance enough for its cost? | Fixed fusion rule and ablation results |
| M05 | Optional four-combination classifier versus style classifier plus calibrated length rule | Does learned combination prediction add value when both approaches retain the same scale/reference information? | Per-attribute and joint results; geometry contract preserved |
| M06 | Float versus INT8; one smaller backbone/resolution if needed | Which tested model meets Pi accuracy and speed targets? | Pi benchmark and conversion report |
| M07 | Calibration, rejection, and temporal smoothing | Can stable automatic results remain honest on difficult inputs? | Frozen thresholds and live-sequence report |

Use pretrained MobileNetV2 as the initial candidate, not an architectural commitment. Its documented preprocessing maps image values to [-1, 1]; apply the chosen normalization exactly once and preserve the contract in the export metadata. [MobileNetV2 API](https://www.tensorflow.org/api_docs/python/tf/keras/applications/MobileNetV2)

M05 is a later ablation, not a replacement for the geometry baseline. A direct four-combination model requires a fixed calibrated station image that preserves garment extent relative to the reference, or explicit calibrated geometry features. Do not train it to predict physical short/long labels from individually resized, tightly cropped skirts with the scale removed. If reliable scale cannot be provided, omit this ablation and retain the separate length rule. Imported fashion-image length labels are not interchangeable with the station's physical threshold.

Train the new head with the backbone frozen, then cautiously fine-tune upper layers at a lower learning rate. Keep batch-normalization behavior explicit during fine-tuning. TensorFlow's transfer-learning guide provides the underlying workflow. [Transfer learning and fine-tuning](https://www.tensorflow.org/tutorials/images/transfer_learning)

Provisional search budget: one seed for initial screening; at most two plausible learning rates per candidate; up to 5-10 head epochs followed by 10-20 fine-tuning epochs with early stopping. Run the best one or two configurations with three seeds if time allows. These settings are starting ranges; save actual settings and stop based on validation behavior, not the desire for a higher training score. Compare models on the same manifests.

For M03, retain the captured frame at its actual resolution, identify the skirt region, then sample a small deterministic set of valid interior patches before whole-image resizing. Start with three patches and compare with one. Avoid background, trim, logos, occluders, and the hem border where possible. Record patch coordinates, size in original pixels, validity score, and aggregation. If no patch has sufficient visible detail, the fabric output can abstain while style remains available. This still uses one full-skirt view.

A manually annotated ROI may diagnose whether classification is feasible, but final reported end-to-end performance must use the automatic deployed ROI method. Start with a calibrated station ROI and presence/quality checks. Add localization or segmentation only when errors demonstrate a need. Account for its annotation effort, runtime, and licensing before adoption.

Use modest realistic changes in lighting, color balance, position, scale, compression, and blur for robustness. Do not add vertical flips or deformations that alter length, pleating, or fabric structure. Do not crop out the waistband or hem for the length task. A transform must preserve its label. Never augment validation/test inputs randomly during reported evaluation.

## Model export and Pi handoff

Export the first baseline during the first training week. The baseline path should use supported built-in operators and static batch-one inputs. A requirement for custom operators or Select TensorFlow Ops triggers an architecture/runtime decision; it must not appear unnoticed at final deployment.

Produce float32 first, then an INT8 candidate using representative training images covering the expected input range. Save representative example IDs and preprocessing. Check tensor input/output types, scale and zero-point handling, operator compatibility, prediction agreement, and evaluation deltas. Integer conversion can change outputs; performance improvement must be measured on the actual target. [Integer quantization guidance](https://developers.google.com/edge/litert/conversion/tensorflow/quantization/post_training_integer_quant)

LiteRT provides an interpreter route for Linux embedded devices, including ARM64. Available wheels, Python ABI, converter/runtime operator versions, and OS dependencies must be tested together on the selected Pi. Do not assume that an old `tflite-runtime` wheel or a current `ai-edge-litert` wheel fits every new Pi OS/Python release. [Linux interpreter guidance](https://developers.google.com/edge/litert/microcontrollers/python)

Every deployable model bundle must contain:

- Model file(s), SHA-256 checksums, architecture description, training run ID, code revision.
- Ordered label map and taxonomy version; supported/unsupported inputs.
- Input shape/dtype/color order, resizing/letterboxing/cropping rules, normalization location, quantization metadata.
- Patch selection and aggregation settings, ROI/localization method/version, length calibration requirements.
- Output names, semantics, calibrated/uncalibrated status, rejection thresholds, smoothing and stale-result timeout.
- Tested runtime, Python, OS/architecture, thread count/delegates, dependency lock, and installation log reference.
- Held-out evaluation summary, known failures, license/provenance for data and pretrained weights, model card.
- A small permitted verification image set with expected results/tolerances for laptop and Pi checks.

## Required experiment record

One immutable folder per run, suggested as `artifacts/runs/<run_id>/`, containing `config.json`, `environment.txt`, split manifest hashes, source-code revision, random seed, checkpoint, training log, metrics, per-example predictions, confusion matrices, and error-review notes. A failed run is recorded with its reason; it is not removed from the comparison history.

Record duration, peak VRAM/RAM, image/garment counts per class, label exclusions, pretrained-weight source/hash, freeze schedule, optimizer, learning rates, input contract, augmentation, stopping rule, and selected epoch. Save evaluation denominators and predictions so a later paper update does not depend on screenshots.

Set seeds and optionally enable deterministic TensorFlow operations for reproducibility; record whether this was enabled and any unsupported-operation limitations. Identical seeds do not establish identical results across every hardware/software stack. [TensorFlow determinism API](https://www.tensorflow.org/api_docs/python/tf/config/experimental/enable_op_determinism)

## Eight-week allocation

| Week from project start | Training focus | Gate |
|---|---|---|
| 1 | Resolve labels/geometry; verify environment; internet data intake and local pilot; first export | Reproducible inputs and working GPU/converter smoke tests |
| 2 | Whole-image/patch fabric comparison and unseen-garment feasibility | Evidence supports selected categories or documents a specific unresolved limitation |
| 3 | Expand diverse garments; improve dominant errors; first actual Pi benchmark | A compatible model bundle runs on target hardware |
| 4 | Live integration with separate attribute uncertainty | Automatic single-view prototype |
| 5 | Focused error correction, calibration, rejection, conversion selection | Release candidate and frozen protocol |
| 6 | Locked held-out device evaluation | Results with specimen counts, uncertainty, latency, and failure cases |
| 7 | Address engineering faults; package model/runtime evidence | Reproducible installation and recovery |
| 8 | Contingency and demonstration rehearsal | Tested final bundle and documentation archive |

A material taxonomy change resets affected labels, split manifests, and experiment comparisons. If fabric feasibility is weak, first examine labels, camera detail, lighting, and source shortcuts. Do not claim success by silently narrowing the test set or changing the one-view requirement. Escalate a documented limitation with concrete experiment evidence.

## Installed baseline environment

WSL2 Ubuntu 24.04.5 / Python 3.12.3 / TensorFlow 2.20.0 is now installed and synthetic GPU training plus float TFLite parity passed. Use the exact [training lock](../requirements/training-wsl-py312.lock.txt) and [environment instructions](GPU_SETUP.md). Keras `model.export` is the verified export path; generic SavedModel saving failed TFLite variable initialization in the first test. No real-data baseline has run.

## First real-data pilot executed October 4

The first pleating pilot trained MobileNetV2 on 292 agent-reviewed images and validated on 80 with the original grouped assignments. Epoch4 selected by prespecified validation loss; accuracy78.75%, macroF1 0.7213. Float export verified after TF32 was disabled for numerical comparison. This supersedes earlier no-training status. [Protocol](BASELINE_PROTOCOL.md) and [complete results](BASELINE_RESULTS.md). No fine-tuning, INT8, live localization, length or fabric training occurred.

## Controlled fine-tuning executed

A single prespecified fine-tuning/augmentation candidate improved the same development set to81.25% accuracy and0.7540 macro F1. Minimum-loss selection, fixed data and frozen BatchNorm checks were preserved. Stop this candidate search here pending label/camera evidence; do not describe the reused validation set as independent test data. [Protocol](FINETUNING_PROTOCOL.md), [results](FINETUNING_RESULTS.md).

## October 9 taxonomy supersession

The earlier tentative short/long and four-combination targets are superseded by the nine-category [hemline guide](HEMLINE_GUIDE.md). Worn, hanging, mannequin and held presentations are now explicitly in scope. Require mode-appropriate reference evidence; the existing pleating-only model does not provide length labels or geometry. No training samples have been relabelled.
