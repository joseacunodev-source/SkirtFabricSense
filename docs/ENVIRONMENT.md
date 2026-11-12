# Environment inventory and setup status

October22 current state: the existing WSL training environment is installed and has completed real GPU fitting/export plus CPU checks. The category run preserves [its actual environment snapshot](../records/experiments/20261021-category-presence-v1/environment.json); [GPU setup](GPU_SETUP.md) and [agent handoff](AGENT_HANDOFF.md) give current paths. No dependency installation/change occurred in the October20–22 recovery batch. The pre-install inventory below is historical. No Pi environment or verified edge lock exists yet.

Updated 2026-10-02, Asia/Manila. This records observed environments and the tools installed for documentation. It is not a claim that model training or Pi deployment is ready.

## Observed laptop

| Item | Observed value |
|---|---|
| Model | ASUS TUF Dash F15 FX516PM |
| CPU | Intel Core i5-11300H, 4 cores / 8 logical processors |
| GPU | NVIDIA GeForce RTX 3060 Laptop GPU, 6,144 MiB VRAM |
| GPU driver | 581.80 |
| RAM | 15.7 GiB reported by inventory |
| OS | Windows 11 Home Single Language, build 26200 |
| Free C: space | 101.7 GiB at the October 2 snapshot; transient |
| Host Python | 3.11.9, outside a project virtual environment |
| Git | 2.47.0.windows.1 |
| WSL | Not installed at inspection |
| Training framework | TensorFlow, Keras and PyTorch absent in inspected host and bundled interpreters |

Evidence: [Windows snapshot](../records/environments/2026-10-02-windows-host.json). Python 3.11's generic platform field reports release `10`; the Windows CIM caption and build identify Windows 11. NVIDIA inventory does not prove framework GPU access. `nvidia-smi`'s CUDA version is a driver capability, not proof of an installed training toolkit.

## Environments kept separate

| Environment | Actual state | Evidence |
|---|---|---|
| Windows host | Existing Python/Git/NVIDIA; existing Pillow 12.3.0 | Windows snapshot above |
| Codex bundled tooling | Existing Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, Pillow 12.3.0, pypdf 6.10.0, pdfplumber 0.11.9 | [Bundled snapshot](../records/environments/2026-10-02-codex-bundled-tooling.json) |
| Project documentation tools | `.venv-tools` created using host Python 3.11.9; PyYAML 6.0.3 installed for the skill validator | [Tooling snapshot](../records/environments/2026-10-02-project-documentation-tools.json), [package report](../records/package-installs/2026-10-02-pyyaml.json) |
| WSL training | Proposed, not installed | [Training setup requirements](TRAINING_PLAN.md) |
| Raspberry Pi edge | Hardware absent, no runtime installed | [Deployment plan](RASPBERRY_PI_DEPLOYMENT.md) |

The bundled interpreter was used to inspect the PDF and some dataset/tooling operations. It must not become the unrecorded training environment. No additional ML packages or GPU drivers were installed during this planning work.

## Documentation tool installation performed

From the project root, these operations were executed:

```powershell
& 'C:/Users/Administrator/AppData/Local/Programs/Python/Python311/python.exe' -m venv .venv-tools
& '.venv-tools/Scripts/python.exe' -m pip install PyYAML --report records/package-installs/2026-10-02-pyyaml.json
& '.venv-tools/Scripts/python.exe' -m pip check
```

PyYAML resolved to 6.0.3. The report preserves the wheel URL and SHA-256. The dependency check passed. The system skill validator initially failed in bundled Python because PyYAML was absent; it subsequently passed in this isolated tooling environment. No change was made to the bundled or host package installations.

For rebuilding only this Windows tooling environment, [tools-windows-py311.txt](../requirements/tools-windows-py311.txt) pins and hashes the actual installed PyYAML wheel. This is not the future Linux training or ARM64 edge lock. The base virtual-environment pip/setuptools inventory is preserved separately in [tools freeze](../records/environments/2026-10-02-tools-freeze.txt).

## Future setup sequence

1. Select the training OS/Python/framework combination and required disk allocation from official compatibility guidance.
2. Snapshot the relevant host before changes. Install into an isolated training environment and append every outcome to the installation ledger.
3. Verify real GPU execution, a forward/backward step, export, and inference. Save logs and resolved dependencies.
4. When the Pi arrives, record actual OS image, architecture, Python, camera and display. Resolve its edge stack independently.
5. Verify exported-model parity and complete camera/UI operation on that Pi before freezing the edge lock.

Use [the standard-library collector](../tools/collect_environment.py) from each environment's interpreter. Existing output paths are refused to preserve history. It collects selected package/tool versions and limited machine information; it does not prove imports or inference and does not replace a complete resolved dependency lock.

## 2026-10-03 WSL prerequisite change

Both Windows WSL and VirtualMachinePlatform features were enabled with NoRestart; the result requires a restart. WSL runtime/Ubuntu/TensorFlow remain uninstalled. Driver 581.80 and RTX 3060 6,144 MiB were re-observed. [Before snapshot](../records/environments/2026-10-03-before-gpu-setup.json), [after snapshot](../records/environments/2026-10-03-after-wsl-features.json), and [setup handoff](GPU_SETUP.md) preserve the state. Failed installation attempts are logged. A host smoke-script preflight failed on absent NumPy before any training; this is [failure evidence](../records/experiments/2026-10-03-gpu-host-preflight-failed.json), not a successful GPU test. No Python packages were installed this session.

## After-restart completion

The WSL training environment is installed and GPU training/export smoke checks passed. See [exact versions, paths and evidence](GPU_SETUP.md). The previous restart-required state is historical. Pip artifact hashes cover all 51 installed packages; OS package inventory and actual environment snapshot are retained. No Linux NVIDIA display driver was installed.
