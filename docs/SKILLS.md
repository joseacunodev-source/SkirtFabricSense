# Skills and engineering capabilities

Updated 2026-10-02 (Asia/Manila). Skills are instructions used by Codex. They do not install TensorFlow, Jupyter, camera drivers, or Raspberry Pi application dependencies.

| Skill | State | Role |
|---|---|---|
| jupyter-notebook | Installed from openai/skills curated catalogue during this work | Reproducible experiment notebooks when notebook creation begins |
| skirt-fabric-project | Created for this project; portable source at skills/skirt-fabric-project/SKILL.md | Single-camera constraints, research/data routing, evidence and Pi handoff |
| skill-installer / skill-creator | Existing system skills, used | Discover/install and maintain focused skills |
| pdf:pdf | Existing plugin skill, used for source proposal review | Inspect the proposal when engineering scope needs comparison |
| computer-use | Existing available capability, not needed in this documentation session | Future camera or graphical application checks when suitable |
| documents / spreadsheets | Existing available skills, not used to author this Markdown pack | Optional later Word reports or spreadsheet evaluation artifacts |

The installed curated catalogue has a notebook workflow but no dedicated Pi/fabric-training skill was selected. The project skill and maintained technical plans cover that specialized workflow without adding unrelated plugins.

## Locations and provenance

- Installed notebook skill: `C:/Users/Administrator/.codex/skills/jupyter-notebook/SKILL.md`.
- Installed project skill: `C:/Users/Administrator/.codex/skills/skirt-fabric-project/SKILL.md`.
- Portable project skill: [SKILL.md](../skills/skirt-fabric-project/SKILL.md).
- Installation records and final file hashes: [ledger](../records/installations.jsonl).
- Upstream notebook source: https://github.com/openai/skills/tree/main/skills/.curated/jupyter-notebook

Skills installed or completed in this session are available for discovery on the next turn. The notebook skill installation does not mean a project Jupyter server/kernel is installed; consult environment snapshots.

When modifying the project skill, keep the portable and installed copies identical and validate with the system skill-creator validator. Do not put experimental metrics or host-specific dependency locks inside the skill; link the maintained project records instead.
