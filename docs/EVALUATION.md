# Evaluation and release protocol

November 4: the existing selected chain was assessed on fixed synthetic brightness and blur changes to the same 118 reused development originals. No model was trained or promoted. [Robustness results](IMAGE_ROBUSTNESS_NOV04.md); [thesis figure pack](THESIS_FIGURES.md). Physical camera, independently verified labels, calibrated length and Pi acceptance remain open.

Status: proposed protocol, no measured results. Reviewed 2026-10-02, Asia/Manila. Numeric thresholds below are engineering targets to confirm before the locked evaluation, not performance claims.

The release must satisfy two separate questions: whether unseen garments are classified usefully from one full-skirt camera view, and whether the complete offline application operates reliably on the chosen Raspberry Pi. A model-only accuracy score answers neither question by itself.

## Evaluation units and protected data

The primary statistical unit is an independent garment/specimen, not an adjacent video frame or a crop. Use grouped assignments from `TRAINING_PLAN.md`. No image, crop, related product photo, or video frame from a final-test garment may appear in development, representative quantization data, or calibration data.

Keep these pools distinct:

| Pool | Permitted use |
|---|---|
| Training | Weight fitting and realistic training augmentation; source of INT8 representative examples |
| Model validation | Architecture, stopping epoch, preprocessing and patch-policy selection |
| Calibration/threshold validation | Confidence calibration, decision thresholds, smoothing and quality settings |
| Locked test | Once-per-release final accuracy and live behavior assessment |
| Diagnostic challenge set | Named difficult conditions; explicitly labelled as development or locked-test |

Source-domain holdouts and locally captured test garments are reported separately. Mixing public dataset images with local camera samples into one overall score can conceal a deployment-domain failure. If a test result leads to further tuning, that test version is no longer independent for the revised model; collect a new holdout or report the result as development evidence.

Report exact independent garment counts, source counts, class counts, and presentation counts. For the final phase, aim to reserve at least 15-20 unseen garments per fabric category when feasible, distributed across the skirt combinations. These are additional to the development garments targeted in `TRAINING_PLAN.md`; prioritize absolute class counts over an illustrative split percentage. This is a practical acquisition aim, not a sample-size guarantee; fewer samples require explicitly wider uncertainty and narrower conclusions. Repeat placements improve robustness measurement but do not add independent garments.

## Ground truth before predictions

Freeze the taxonomy and annotation guide, then review test labels without seeing model predictions. Record labels, evidence, disagreements, resolutions, and exclusions. Use verified composition information only where it actually supports a fiber label; a construction label does not establish composition.

Measure physical skirt length consistently using the agreed waistband-to-hem rule. Document the fixture's classification threshold and a predeclared boundary band based on repeat measurement/calibration error. Report borderline specimens separately and in the overall result according to the frozen policy. Do not remove difficult specimens after examining errors.

For mixed-material skirts, establish a rule in advance: label the specified dominant visible panel, use appropriate multiple labels, or return unsupported/mixed. Missing or uncertain truth is not an incorrect model prediction by default; list such examples separately with counts.

## Metrics to compute

| Output | Required measurements |
|---|---|
| Pleating/style | Per-class precision, recall, F1 and support; macro F1; confusion matrix |
| Length class | Per-class recall/F1; threshold-boundary errors; invalid-reference rejection |
| Physical length, if output | MAE and absolute-error distribution in centimetres; fixture/calibration conditions |
| Fabric | Per-class precision/recall/F1, macro F1, confusion matrix, category coverage, verified-label counts |
| Combined result | Fraction of eligible presentations where all required fields are correct; fraction where all are available |
| Presence/non-skirt gate | False acceptance of negative presentations; false rejection of supported valid skirts |
| Uncertainty | Accepted accuracy/risk, coverage, per-class coverage, abstentions, calibration metrics |
| Live behavior | Time to first stable correct result, label changes during a held presentation, stale-result clearing time |
| Runtime | End-to-end latency p50/p95, prediction update rate, preview rate, peak memory, thermal/power faults |

The report must include raw classification performance before abstention as well as accepted-result performance after abstention. A result that abstains on a valid skirt counts as unavailable in the overall task-success denominator.

Definitions:

- Coverage = accepted eligible presentations / all eligible presentations.
- Selective error = incorrect accepted predictions / accepted predictions.
- Valid-input rejection = rejected supported presentations / all supported presentations.
- Negative false acceptance = negative presentations receiving a supported skirt result / all negative presentations.
- End-to-end task success = eligible presentations with all required outputs present and correct / all eligible presentations.

For per-attribute metrics, state which truth labels are known and eligible. For joint metrics, use only presentations with truth for every required field and disclose that denominator. Do not multiply marginal attribute accuracies to estimate joint accuracy.

Use garment-level summaries so garments with longer clips do not dominate. Supplement with frame-level data only as a timing/stability measure. Report 95% uncertainty intervals using garment-cluster bootstrap for aggregate metrics when sample counts support it; resample the garment with all of its presentations together. For sparse classes, show raw counts and clearly identify unstable intervals. Keep paired garment predictions for fair model comparisons.

## Confidence, rejection, and calibration

Softmax output is a model score, not observed system accuracy or proof of the fabric's composition. Evaluate reliability diagrams, negative log-likelihood, Brier score, and a documented calibration-error summary on suitable held-out data. Record binning and sample counts; small samples can make calibration estimates unstable. [Scikit-learn calibration guidance](https://scikit-learn.org/stable/modules/calibration.html)

Temperature scaling is a candidate after model selection, fitted on calibration data only. Validate its effect on the deployed float/quantized outputs and store its parameter with that exact model. It improves neither missing visual information nor unsupported-input detection by itself. [Guo et al., On Calibration of Modern Neural Networks](https://proceedings.mlr.press/v70/guo17a.html)

Develop separate quality, presence, per-attribute uncertainty, and temporal-stability checks. A low top-class score alone is not a reliable general detector of unknown fabrics or non-skirts. Use real negative data and a challenge set; keep some negative object types unseen during threshold selection.

Plot coverage versus selective error and compare per-class rejection. Select thresholds on calibration/validation evidence, then freeze them. A skirt may receive a valid style/length result while fabric remains uncertain. The interface must distinguish “uncertain fabric” from “no skirt,” “bad framing,” and “camera unavailable.”

## Proposed acceptance targets

Confirm or revise these during the pilot, before final test access. Record changes with rationale rather than rewriting targets after seeing final results.

| Area | Initial engineering target | Interpretation |
|---|---|---|
| Pleating/style | Macro F1 at least 0.90 on the agreed supported domain | Target, not a promise; disclose every class |
| Length category | At least 0.90 balanced accuracy within the calibrated fixture | Boundary and off-plane cases also reported |
| Fabric | Macro F1 at least 0.80 before abstention | High-risk target requiring feasibility evidence |
| Accepted fabric predictions | At least 0.90 accepted accuracy at at least 0.70 coverage | Report both plus per-class coverage and raw counts |
| Negative false acceptance | No more than 0.05 on the locked negative set | Estimate with denominator and uncertainty |
| Prediction responsiveness | First stable result p95 within 2 seconds of valid steady presentation | Includes smoothing delay, not just model time |
| Live preview | At least 15 displayed frames/second under normal target conditions | Separate from inference update rate |
| Stale results | Cleared within 1 second after object removal/invalid feed | Test removal and frozen/camera-disconnected feed |
| Sustained operation | 60-minute run with no crash, unbounded memory growth, or accumulating frame delay | Log resource trends and any throttling |
| Quantization | No more than 2 percentage points macro-F1 loss as an initial tolerance | Compare identical examples, all attributes and coverage |

Targets are diagnostic: failure should drive a documented fix or limitation, not automatic relabeling or exclusion. Pi throughput is unknown until measured. A slower prediction update rate may still satisfy the display and response targets if latest-frame handling remains correct.

## Controlled experiment matrix

Use the same held-out development groups for ablations; promote the chosen configuration to locked testing only after decisions are frozen.

| Comparison | Keep fixed | Report |
|---|---|---|
| Whole-skirt versus fabric patches | Data groups, backbone, labels, evaluation presentations | Fabric macro F1, per-class recall, latency, patch rejection |
| One versus three patches | Native image, patch policy, model | Benefit per extra inference and quality failures |
| Optional direct four-combination model versus style plus calibrated length | Groups, label semantics, available scale/reference information, resource budget | Joint and marginal errors; invalid-geometry rejection |
| Color versus grayscale diagnostic | Same test examples and comparable training conditions | Dependence on color shortcuts; not a new final model by default |
| Masked/neutralized background diagnostic | Garment content preserved | Background/source shortcut evidence |
| Float versus INT8 | Model checkpoint, input data, output policy | Per-example disagreements, metric delta, latency and size |
| Raw versus temporally smoothed output | Same prerecorded sequences and timestamps | Flicker reduction, response delay, stale-output risk |
| Local-only versus supplemental public pretraining/data | Local split manifests | Whether public data helps actual device-domain results |

Cross-category balancing is essential: avoid a test where every satin example is pleated or all denim is blue. Collect counterexamples and tabulate style-by-fabric, color-by-fabric, and source-by-fabric coverage. A classifier can exploit legitimate cues while still failing on categories that share them; these slices expose that problem.

## Device and robustness sessions

Record the exact camera, output mode, focus/exposure/white-balance behavior, camera-to-fixture distance, skirt pixel height/width, lighting placement, Pi model/RAM, OS image, kernel, Python/runtime, model hash, thread count, power supply, cooling, and screen settings.

Conduct the following within the allowed one-full-skirt view:

1. Normal presentation: whole skirt visible, waistband at reference, stable illumination, camera at validated distance.
2. Repositioning: repeated placement and small allowed lateral/depth changes; remove and reintroduce each garment.
3. Lighting: defined dimmer/brighter conditions, shadows, glare on shiny fabrics, warm/cool shifts. Record measured settings or a repeatable fixture setting.
4. Appearance: plain/patterned, dark/light, reflective, translucent, fine/coarse pleats, blends and mixed panels.
5. Invalid framing: missing waistband/hem, skirt too small in frame, occlusion, multiple garments, moving garment, blur/focus hunting.
6. Negatives: empty station, people/hands, trousers, shorts, dresses, towels/loose fabric and other objects. Separate known-development negatives from unseen test types.
7. Transitions: rapid garment changes, removal, camera unplug/replug, frozen frame, application restart, and wrong calibration profile.

For feasible final sessions, use three predefined presentations per garment, not dozens of cherry-picked frames. Balance order and note lighting/session blocks. Save timestamped predictions and the permitted source clips so failures can be replayed. Ground truth must be linked before predictions are reviewed.

## Runtime measurement method

Warm up the model and separately record cold-start time. Timestamp frame acquisition, preprocessing, each model call, aggregation/smoothing, and screen update with a monotonic clock. End-to-end age is display time minus the acquisition time of the evidence behind that result. Do not time only `invoke()` and label it response time.

Use a latest-frame buffer and count dropped/superseded frames. Processing every queued frame can create a smooth-looking but delayed result; report maximum queue/result age. Track which frame supplied each attribute, and expire attributes independently if they are updated on different schedules.

Record at least several hundred inference cycles in a normal sustained session where practical, alongside the 60-minute stability run. Report p50/p95 rather than only averages. Measure at the intended capture resolution, display mode, screen, cooling, and simultaneous models. Compare single- and multiple-thread settings as a bounded benchmark, not an assumed speedup.

Log CPU utilization, RAM, temperature, available storage, power/throttle flags, runtime exceptions, camera reconnects, and model load failures. Thermal or undervoltage events are test findings, not excluded timing samples. A timing result from a laptop GPU is never substituted for a Pi result.

## Verification sequence and release evidence

1. Validate manifest integrity: no cross-split connected groups, no missing required evidence, no overlapping source derivatives.
2. Verify preprocessing with fixed permitted images: RGB/BGR order, resize/letterboxing, patch coordinates, normalization, labels, and quantized tensor handling.
3. Compare original-model, laptop-runtime, and Pi-runtime predictions using documented tolerances. Investigate label-order or preprocessing differences before measuring accuracy.
4. Test corrupt/missing model files, wrong label map, absent camera, full output storage, and invalid calibration. The application must explain the fault without presenting an old classification as current.
5. Freeze code, models, settings, dependency lock, input taxonomy, split hashes, and protocol version.
6. Run the locked evaluation; preserve every result, including invalid/rejected cases and runtime failures.
7. Produce a release report with metrics, counts, uncertainty, environment, raw prediction file references, known limits, and an explicit pass/fail/unevaluated entry for every target.
8. Verify a clean Pi installation from documented instructions, model checksums, startup/recovery, and offline operation. Keep the installed versions and smoke-test outputs.

Suggested evidence artifacts are a model card, `predictions.csv`, garment-level summary, confusion matrices, coverage-risk and calibration plots, runtime timing CSV, resource log, deployment manifest, and signed-off checklist. Use tables and raw exports as the durable evidence; screenshots are supporting material only.

## Limits that must remain visible

- Visually indistinguishable fabrics and fiber blends may be unresolvable from a distant RGB image. Report estimates and uncertainty with the actual tested taxonomy.
- A calibrated physical-length result is valid only for the tested geometry; worn or off-plane garments need their own reference and evaluation.
- A small independent test set supports limited conclusions even when it contains many frames.
- Public texture-swatch performance is not evidence of full-skirt performance.
- An abstaining system must disclose coverage, including fabric-specific and garment-specific gaps.
- A successful `.tflite` conversion is not an installation, speed, or hardware-reliability result.
