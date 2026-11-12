---
name: skirt-fabric-project
description: Continue SkirtFabricSense data preparation, training, application work, or Raspberry Pi deployment with reproducible engineering records. Use for this single-camera skirt and fabric project; not for unrelated fashion or generic ML tasks.
---

# SkirtFabricSense workflow

Work in the user's SkirtFabricSense workspace. Read its `AGENTS.md`, `README.md`, `docs/REQUIREMENTS.md`, and `docs/DECISIONS.md` first. This skill is agent guidance; it is not installed on the Raspberry Pi as runtime software.

## Product invariants

- Use one full-skirt camera view for automatic live style, length and fabric estimates. Native-resolution crops from that same source frame are allowed. Do not replace the workflow with another camera or a user-presented close-up.
- A fabric label ontology remains open until recorded otherwise. Cotton/polyester and satin/chiffon/denim can overlap. Preserve supported annotation evidence rather than silently forcing exclusive labels.
- Read geometry/calibration requirements before implementing length. Resized garment crops alone do not establish absolute size or wearer knee position.
- The RTX 3060 laptop trains models; the Pi runs exported inference offline. Pi5, separate lightweight style/fabric models and WSL2 TensorFlow are proposals until current records establish their status.

## Route to the relevant project records

For data work, read `docs/DATASETS.md`, `data/registry.json`, and the split protocol in `docs/TRAINING_PLAN.md`. Keep originals immutable and record source terms, hashes, specimen groups, parent frames/crops, and actual acquisition status. Preserve official source split memberships. Downloaded labels or external images do not establish a deployment-ready fabric dataset.

For experiments, read `docs/TRAINING_PLAN.md` and `docs/EVALUATION.md`. Record each run using `templates/experiment.json`; keep associated code, data/split hashes, pretrained-weight provenance, settings, environment, predictions and metrics. Treat all derivatives and views of a specimen as related. Do not tune on the final test set. Distinguish score calibration from representative data for integer quantization. Use the jupyter-notebook skill when authoring notebooks.

For device work, read `docs/HARDWARE.md`, `docs/RASPBERRY_PI_DEPLOYMENT.md`, and `requirements/README.md`. Check actual OS/ARM64/Python/runtime availability, camera mode and exporter operators together. Export early, compare desktop predictions, then verify on real hardware. A published wheel or completed conversion is not on-device validation.

For application work, read `docs/ARCHITECTURE.md`. Keep capture/inference/preview independent and queues bounded; expire predictions after scene change or camera failure. Preserve frame-to-patch provenance and independent uncertainty for each output.

## Evidence and handoff

Read `docs/RECORD_KEEPING.md`. Log dependency changes, failures and actual verification in `records/installations.jsonl`; snapshot the changed environment using `tools/collect_environment.py` from its own interpreter. Do not copy training dependencies wholesale onto the Pi. Preserve separate tested locks and OS/camera records.

Update relevant plans, decisions and `CHANGELOG.md` with implementation changes. Use `templates/model-release.json` for releases. Mark plans, installations and verified behavior distinctly; unmeasured values remain null. Report meaningful limitations and the next concrete milestone. Main capstone writing is outside scope unless the user asks for it.

Parallel work is appropriate for independent subsystems; assign non-overlapping file ownership and centrally reconcile interfaces and shared records.
