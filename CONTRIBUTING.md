# Contributing to SkirtFabricSense

Read `AGENTS.md`, the [current handoff](docs/AGENT_HANDOFF.md), [checkpoint](records/continuation/latest.json) and [task board](docs/TASK_BOARD.md) before starting. Then read requirements, decisions and the subsystem plan for the change. The [GitHub workflow](docs/GITHUB_WORKFLOW.md) explains how to continue from another computer and restore excluded assets.

Keep one full-skirt live view; crops from that frame are allowed. Worn skirts remain primary, with other presentations secondary. Keep nine body-relative hemline categories and optional fabric appearance. Do not invent labels, acquisition completion, measured accuracy, physical lengths or deployment evidence.

Work on a bounded branch, agree file ownership when using agents and submit a reviewable diff. Describe the concrete behavior changed, validation performed and remaining limitations. Check the staged files before committing; local credentials, environments, downloaded photographs and binary model bundles do not belong in the public repository.

For code-only changes, run the selected synthetic-fixture command in [GITHUB_WORKFLOW.md](docs/GITHUB_WORKFLOW.md) or the equivalent GitHub workflow. Run additional checks appropriate to the subsystem; a green software check does not establish model quality or target-device operation. Report commands and results without claiming unexecuted checks passed.

For data or training work, preserve source rights, provenance, hashes and garment/source groups. Keep protected source/test partitions out of training and threshold tuning. Record each experiment's manifest/split hashes, source revision, seed, preprocessing, parameters, versions, metrics and limitations. Update `data/registry.json` and `docs/DATASETS.md` when dataset state changes. An asset archive is transferred privately under its sources' terms; see [third-party notices](THIRD_PARTY_NOTICES.md).

Record actual package changes in `records/installations.jsonl` and collect an environment snapshot with `tools/collect_environment.py`. Keep training, development and Pi environments separate. Do not overwrite historical evidence to make a new environment appear identical.

For application changes, update requirements traceability, relevant design/setup documents, decisions and `CHANGELOG.md`. Before handing off, update the task board, handoff and continuation checkpoint with actual outcomes and remaining actions. Preserve exact bytes of frozen hash-bound records; do not perform blanket line-ending or formatting rewrites.

Project-wide source licensing has not yet been selected. Do not add a blanket license or imply permission to redistribute third-party data/weights without the project owner's decision and source-specific review.
