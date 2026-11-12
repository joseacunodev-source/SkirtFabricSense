# Working on SkirtFabricSense

Read README.md, docs/REQUIREMENTS.md, docs/DECISIONS.md, and the relevant subsystem plan before implementation. The human user's newer instructions take priority; update the records when scope changes.

For continuation after a usage limit or with another AI, first read docs/AGENT_HANDOFF.md, records/continuation/latest.json, docs/DOCUMENTATION_INDEX.md, and docs/TASK_BOARD.md. Verify their referenced hashes and the actual run/process state before restarting any task. Do not infer current readiness from older dated paragraphs. Update this handoff/checkpoint with actual outcomes and remaining actions before stopping.

- Preserve one live full-skirt camera view. Software crops from that frame are allowed. Do not substitute a two-camera or sequential close-up workflow without a user-requested scope change.
- Keep observed evidence separate from proposed designs, installed packages, and hardware-verified behavior. Never fabricate measurements, versions, training results, or download completion.
- Log each dependency installation/removal or version change in records/installations.jsonl. Record commands, target environment, version, outcome, and verification; exclude credentials and private signed download URLs.
- After a meaningful environment change, collect a snapshot with tools/collect_environment.py from that environment. Training and Pi environments need separate locks and records.
- For dataset changes, update data/registry.json and docs/DATASETS.md. Preserve provenance, actual terms, hashes, and garment/source grouping. Do not move test samples into training or tune thresholds on the locked test set.
- Keep all frames/crops/augmentations from a garment together. Reject a fabricated dataset size inferred by counting crops as independent specimens.
- Every experiment records its data manifest and split hash, source revision, seed, preprocessing, versions, training parameters, metrics, and known limitations.
- Validate export early. A desktop export is not Pi compatibility evidence; benchmark on the target ARM64 OS/Python/runtime before declaring deployment verified.
- On application changes update requirements traceability, relevant design/setup docs, decisions, and CHANGELOG.md. Use appropriate checks; avoid broad retesting for wording-only edits.
- Parallel agents may own bounded subsystems. Agree file ownership before edits and integrate findings centrally. The user has authorized agents for this project; do not create separate user chats for subtasks.
- The installed skirt-fabric-project skill captures this workflow; its portable copy is skills/skirt-fabric-project/SKILL.md. Use the installed jupyter-notebook skill for notebook work. Skills are agent guidance, not dependencies installed on the Pi.
