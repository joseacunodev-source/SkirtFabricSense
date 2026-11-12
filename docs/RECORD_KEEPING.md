# Engineering record workflow

The goal is a factual history the user can consult when updating the capstone paper, and enough detail to reproduce laptop training and Pi deployment. Do not write unsupported results into the paper or these records.

## Record locations

| Record | Location | Update when |
|---|---|---|
| Requirements and status | docs/REQUIREMENTS.md | Scope or acceptance changes |
| Decisions and rationale | docs/DECISIONS.md | Architecture, labels, hardware, thresholds or tools change |
| Completed changes | CHANGELOG.md | Every meaningful work session |
| Installed/removed dependencies | records/installations.jsonl | Every installation, removal, upgrade or failed attempt |
| Machine and package snapshots | records/environments/*.json | Before setup and after meaningful environment changes |
| Dataset acquisition and terms | data/registry.json | Source/download/license/provenance changes |
| Individual sample manifest | data/manifests/ (create during collection) | Images, annotations, grouping or splits change |
| Experiments | records/experiments/ (create when first run exists) | Every actual training/evaluation run |
| Model bundle records | records/models/ (create on export) | Each export/release |
| Physical deployment evidence | records/deployments/ (create with Pi) | OS image, wiring, camera, calibration, runtime or release changes |

Empty result directories and placeholder metrics are deliberately not presented as completed work.

## Environment distinctions

Use roles such as windows-host, training-wsl, edge-pi, and codex-bundled-tooling. The bundled Python is available to document generation; its packages do not prove the user's training environment is installed. System Python packages also do not constitute an isolated project environment.

For every package operation record date/time with offset, role, package/tool, exact source/version, command, outcome, verification command/output path, reason, and compatibility concerns. If a command would expose a token or signed URL, redact that portion and preserve a public source URL instead. Failed installations stay in the ledger.

Read installed versions after a successful operation. Do not merely log the version requested. Export resolved requirements from the tested environment; separate direct dependencies from the full resolved lock. Check exported files for local/private URLs before sharing. Preserve OS/architecture/Python versions and model-runtime versions as well as Python packages.

## Experiments

Copy templates/experiment.json into a uniquely named run record and fill fields with actual values. Include source revision or source file hashes, configuration, split and dataset hashes, seeds, pretrained weight source/license, parameters, runtime environment snapshot, training curves, results and failure cases. Null means not yet known; never use zero for an unmeasured metric.

Record sample counts as images AND independent specimens. Freeze validation/test membership; document how repeated views are aggregated for specimen-level analysis. Fit normalization, calibration and selection decisions using training/validation only. Record all meaningful candidate runs so the final result is not detached from its selection process.

## Model release

Copy templates/model-release.json. Include the model checksum, labels in tensor order, preprocessing, dimensions, patch strategy, calibration/thresholds, dataset/split, framework conversion versions, and before/after export evaluation. Hardware validation remains null until tested on a named Pi configuration.

## Hardware and deployment

Record board/RAM revision, storage, supply, camera model/firmware, lens/focus settings, capture resolution and compression, mounting geometry, lighting configuration, display, cooling, and enclosure revision. Record actual wiring/ports and cable types with photos once assembled. Preserve a clean-image installation command transcript, runtime locks, service configuration, test outputs and rollback instructions.

## Session closure checklist

1. State what changed and what remains proposed.
2. Update the appropriate records and relevant setup instructions.
3. Run targeted checks for actual changes; link evidence.
4. Record known failures and decisions that require user input.
5. Leave one clear next milestone; do not claim hardware or ML validation from plans.

## Continuation across agents and usage limits

Keep [the handoff](AGENT_HANDOFF.md), [task board](TASK_BOARD.md), and `records/continuation/latest.json` aligned at meaningful checkpoints. The machine record includes current model/package identities, hash-bound evidence, unfinished acceptance gates, last confirmed hardware access and the next concrete task. Never record a pending process as completed merely because its script exists.

Before stopping, preserve executed sources, failed attempts and completed outputs; identify any active process and its exact run directory. Before resuming, check the actual status and process state so an interrupted transcript does not trigger duplicate GPU training or overwrite a release. Existing environments, data and artifacts should be reused when their integrity checks pass. `tools/validate_records.py` also verifies nested local evidence hashes in the continuation record. Do not hash that record into itself or place mutable logs/caches inside immutable packages.
