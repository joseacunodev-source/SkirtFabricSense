# Working from another computer

Repository: [joseacunodev-source/SkirtFabricSense](https://github.com/joseacunodev-source/SkirtFabricSense). Git records deliberate commits; it does not synchronize unsaved work or running processes. Push before changing computers, then pull on the next computer.

## What a clone contains

The repository carries source, tests, configuration, documentation, experiment records, dataset/split manifests and the portable project skill. Large acquired photographs, model binaries, downloaded archives, caches, virtual environments and hardware-specific installations travel separately. A successful clone is enough to continue code, documentation and task planning. It is not a restored training machine or a ready camera station.

The selected desktop research station is **station-v9 / research-v14**, with v8 retained for rollback. Selection does not establish accepted camera, garment, fabric, calibration or Raspberry Pi performance. Read the current checkpoint rather than inferring readiness from historical paragraphs.

## First checkout

Install Git and a suitable Python only if missing. For Windows, use a workspace outside OneDrive or another actively synchronized folder, for example `C:/Projects/SkirtFabricSense`. Do not let OneDrive and Git synchronize the same working tree concurrently. Authenticate through GitHub's supported browser/Git credential flow; never put a token in a remote URL, command record or committed file.

```powershell
git clone https://github.com/joseacunodev-source/SkirtFabricSense.git C:/Projects/SkirtFabricSense
cd C:/Projects/SkirtFabricSense
git status --short --branch
git remote -v
```

Read these in order before implementation:

1. `AGENTS.md` and `README.md`.
2. `docs/AGENT_HANDOFF.md` and `records/continuation/latest.json`.
3. `docs/DOCUMENTATION_INDEX.md`, `docs/TASK_BOARD.md`, requirements, decisions and the relevant subsystem plan.

Check referenced hashes and actual local processes before resuming any interrupted task. Missing excluded assets on a new clone are missing inputs, not evidence that a historical experiment failed. Do not rewrite references to conceal absent files.

The portable guidance is `skills/skirt-fabric-project/SKILL.md`. An assistant can read it directly; assistants that install skills must keep their installed copy identical. It is guidance, not a Pi package.

## Code-only checks

The GitHub workflow runs a selected synthetic-fixture suite. It needs Python 3.12 and Pillow 13.0.0, without acquired images, model weights, TensorFlow, a GPU or a camera. This is a small **test environment**, separate from training and edge runtime locks.

Example Windows setup on a new computer:

```powershell
py -3.12 -m venv .venv-checks
.venv-checks/Scripts/python.exe -m pip install Pillow==13.0.0
.venv-checks/Scripts/python.exe tools/collect_environment.py --role development-checks --output records/environments/new-computer-checks.json
.venv-checks/Scripts/python.exe -m unittest tests.test_live_state tests.test_hemline tests.test_dataset_partitions tests.test_continuation_records tests.test_raw_http_records tests.test_fabric_evidence_review tests.test_geometry_annotation tests.test_training_contract tests.test_worn_geometry_evaluation tests.test_project_assets -v
```

On Linux/macOS use `python3.12 -m venv .venv-checks` and `.venv-checks/bin/python` in place of the Windows interpreter path. Log actual installation commands, environment, resulting versions and verification in `records/installations.jsonl`; never record an example command as an executed installation. Give the environment snapshot a computer-specific filename rather than overwriting earlier evidence.

The selected tests cover stale-frame handling, hemline uncertainty, split auditing, reference hashes, failed HTTP evidence, fabric-review contracts, geometry annotations/evaluation, training-input contracts and synthetic asset transfers. Git is needed for the inventory fixture; platform permissions may skip its symlink fixture. They do not train models or measure prediction accuracy. Browser, complete dataset integrity, export parity, live capture, display/touch and Pi acceptance need their own inputs and checks. The full record validator expects excluded evidence and the matching installed skill; it is not the asset-free CI command.

The hosted workflow uses `tools/record_ci_environment.py` to execute the pinned Pillow installation on its ephemeral runner, check the resulting version and a Pillow image operation, append the actual installation event to that runner's `records/installations.jsonl`, and invoke `tools/collect_environment.py` for a separate `development-ci-ephemeral` snapshot. The step prints the new event and full snapshot in the **CI installation event** and **CI environment snapshot** log groups. Installation, verification or snapshot failure fails the step. The helper refuses normal local execution; use the explicit local setup commands above for a reviewed local environment.

These records describe the hosted CI environment only. They do not change the local training or Pi installation history, and the workflow does not commit its temporary ledger/snapshot back to Git. GitHub job logs expire according to repository retention; copy relevant log evidence into reviewed project records when permanent provenance is needed. Inspect the actual run and commit rather than assuming every future workflow run passed.

## Restore training and station assets

Use the [asset transfer instructions](ASSET_TRANSFER.md) and the committed `config/project-assets-v2.json`. Version 2 includes the required DTD annotations archive omitted from the original v1 manifest/private ZIP. The published v1 manifest is preserved as history; a passing v1 verification does not restore that missing input. Keep the matching v2 archive in private storage you control; dataset and pretrained-weight terms still apply. Do not add the asset bundle or restricted photographs to this public repository or a public release.

```powershell
python tools/project_assets.py verify --manifest config/project-assets-v2.json
```

On a fresh clone this reports missing excluded files until an authorized asset bundle is restored. After restoration, run verification again. A manifest is an inventory and integrity contract, not an automatic downloader or a grant to redistribute its contents. Preserve the matching code commit and asset manifest together.

Review `requirements/README.md`, `docs/ENVIRONMENT.md`, `records/installations.jsonl` and the relevant training/setup records before rebuilding an environment. `requirements/training-wsl-py312.lock.txt` belongs to the recorded WSL/Linux Python 3.12 training environment; review platform, Python, driver and framework compatibility before reproducing it. Do not install it blindly into native Windows or the Pi. Virtual environments and the laptop GPU driver do not transfer through Git.

On the Raspberry Pi, follow `docs/RASPBERRY_PI_DEPLOYMENT.md` and record a separate ARM64 OS/Python/runtime environment. A desktop model export and passing CI are not target-device evidence. Verify the actual selected display, camera modes, model execution and latency on the Pi before marking deployment accepted.

## Each working session

Use one active computer per branch. Before starting, save or commit any current work and inspect status:

```powershell
git status --short --branch
git pull --ff-only
```

If pull reports local changes or divergent history, stop and reconcile deliberately. Do not use a hard reset, force push or blanket overwrite to make the message disappear. For a bounded change, start a separate branch such as `git switch -c fix/fabric-review-export`.

After the change, run appropriate checks and update task evidence, documentation and continuation records. Review the exact diff and staged files, including newly added files:

```powershell
git diff
git status --short
git add path/to/changed-file
git diff --cached
git commit -m "Describe the implemented change"
git push -u origin HEAD
```

Replace `path/to/changed-file` with the files actually reviewed. Check the push result and the commit on GitHub before switching computers. The other computer must check out that branch and pull it. Merging a pull request into `main` makes the reviewed change available on the shared default branch.

The repository preserves exact file bytes through `.gitattributes`; many JSON/text records are SHA-256 bound. Do not mass-convert line endings, autoformat frozen records or regenerate splits as a portability fix. If a record must change, create the appropriate new version and update its references and checkpoint intentionally.

## Handoff checklist

- Commit and push the code, documentation and updated progress records; note the commit/branch.
- Update `docs/AGENT_HANDOFF.md`, `docs/TASK_BOARD.md` and `records/continuation/latest.json` with actual outcomes, hash references and next actions.
- Record the exact asset-manifest version and where its authorized private bundle is kept, without credentials or signed private URLs.
- State which commands passed, which inputs are absent and whether any process is still running. A process on one computer does not follow a checkout.
- The next assistant verifies those facts before restarting work. GitHub check results supplement the project record; they do not replace independent label review or hardware acceptance.

Workflow dependency references: [checkout](https://github.com/actions/checkout), [setup-python](https://github.com/actions/setup-python), and [Pillow 13.0.0 metadata](https://pypi.org/pypi/Pillow/13.0.0/json). The workflow is defined in source; only an actual GitHub Actions run establishes its hosted-runner outcome.
