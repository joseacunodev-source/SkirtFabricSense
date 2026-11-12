# GPU setup and restart handoff

## Verified after restart — 2026-10-03

The laptop training environment is now installed and its synthetic GPU training/export test passed. Earlier restart/pending statements below are historical.

- WSL 2.7.13.0, kernel 6.18.33.2-2; Ubuntu 24.04.5 LTS, x86-64.
- Python 3.12.3, TensorFlow 2.20.0, Keras 3.15.1, NumPy 2.5.3, Pillow 12.3.0; CUDA runtime 12.9.79 and cuDNN 9.27.0.42 from pip. Windows driver remains 581.80.
- Environment: `/home/skirttrain/skirt-fabric-sense/.venv-training`, owned by dedicated Linux user `skirttrain`. This user has a locked password and no sudo membership; run through `wsl -d Ubuntu-24.04 -u skirttrain`. Root was used only for OS setup. Interactive Ubuntu first-user configuration was not needed for this explicit-user workflow.
- `pip check` passed. GPU prediction tensor was on GPU:0, gradients were finite/nonzero, and weights changed. A single synthetic training step took 0.565 seconds; this is not a steady-state training benchmark.
- Float32 TFLite export passed desktop parity with maximum absolute difference 0.000023365, within atol 0.00001 plus rtol 0.0001. Model size 2,356 bytes. This tiny synthetic model is not the skirt classifier.

The first export failed: generic `tf.saved_model.save` left variable operations that failed in TFLite. Keras `model.export` produced a working export. Both runs and diagnostics are retained. TensorFlow's bundled TFLite interpreter emits a deprecation warning; this verified desktop route is version-pinned, and the Pi runtime must be selected/tested separately.

Evidence: [successful run](../records/experiments/2026-10-03-gpu-smoke-passed.json), [failed first export](../records/experiments/2026-10-03-gpu-first-export-failed.json), [environment snapshot](../records/environments/20261003-161124-training-wsl.json), [hashed package lock](../requirements/training-wsl-py312.lock.txt), [lock verification](../records/validation/2026-10-03-training-lock.json), [installation ledger](../records/installations.jsonl).

Run another smoke test from PowerShell using a **new** output directory:

```powershell
wsl -d Ubuntu-24.04 -u skirttrain --exec /home/skirttrain/skirt-fabric-sense/.venv-training/bin/python /mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense/tools/training/gpu_smoke.py --output /home/skirttrain/skirt-fabric-sense/runs/gpu-smoke-003
```

Active environments/checkpoints are outside OneDrive. Reports and dependency records are copied into this workspace. The 51-package lock matches the complete installed pip inventory and includes artifact hashes from pip reports; a fresh-environment reinstall has not been tested. Dataset/model training and Raspberry Pi hardware validation remain outstanding.

Observed 2026-10-03. The RTX 3060 Laptop GPU has 6,144 MiB VRAM and Windows driver 581.80. This is hardware detection, not successful TensorFlow execution.

## Work performed

The existing Windows WSL launcher returned exit 1 and "WSL not installed" for installation attempts. Both required Windows features were disabled. The following elevated operation completed successfully without restarting the laptop:

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux,VirtualMachinePlatform -All -NoRestart
```

The result explicitly reports `RestartNeeded: true`. Subsequent feature inspection reports both enabled, but the WSL launcher still cannot install the runtime before this restart. TensorFlow, Ubuntu and CUDA Python dependencies have **not** been installed. No framework GPU step or export has run.

Evidence: [feature result](../records/package-installs/2026-10-03-wsl-features.json), [feature inspection](../records/environments/2026-10-03-wsl-feature-state.json), [host snapshot](../records/environments/2026-10-03-after-wsl-features.json), and [installation ledger](../records/installations.jsonl). Failed attempts are retained in the ledger.

## Resume after saving work and restarting Windows

These are planned commands, not completed installation evidence. Run from elevated PowerShell and record output and exit codes:

```powershell
wsl --install -d Ubuntu-24.04 --no-launch
wsl --list --verbose
wsl --version
```

If the launcher still fails after restarting, use Microsoft's WSL installation troubleshooting before changing the training framework. Initialize Ubuntu interactively and create its local Linux user. Verify the distribution uses WSL version 2. Inside Ubuntu, verify `nvidia-smi` before installing the framework. Do not install a Linux NVIDIA display driver inside WSL: the Windows driver supplies GPU access.

Use Ubuntu 24.04's Python 3.12 as the initial candidate, subject to the selected TensorFlow release's actual package requirements. Keep the training environment and active checkpoints on the Linux filesystem, for example `~/skirt-fabric-sense`, outside OneDrive. The authoritative Windows workspace is mounted at `/mnt/c/Users/Administrator/OneDrive/Documents/ChatGPT/SkirtFabricSense`. Copy dataset originals using a manifest and verify SHA-256 after copying; do not change the frozen split.

Planned sequence inside Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip
mkdir -p ~/skirt-fabric-sense
python3 -m venv ~/skirt-fabric-sense/.venv-training
source ~/skirt-fabric-sense/.venv-training/bin/activate
python -m pip install --upgrade pip
python -m pip install 'tensorflow[and-cuda]' Pillow
python -m pip check
```

At execution time, add `--report` paths to pip installation commands, preserve terminal transcripts and resolved `pip freeze --all`, and append each apt/venv/pip operation (including failures) to the installation ledger. Run the project environment collector with this venv's interpreter. The unpinned commands above describe first resolution; they are **not** a tested lock file. Freeze actual installed versions after successful verification. Do not copy these Linux x86-64 packages into the Raspberry Pi environment.

Acceptance requires the synthetic GPU training/export verification in [GPU verification](GPU_VERIFICATION.md), followed by a real labelled-data baseline. Record GPU tensor placement, nonzero finite gradients, changed weights, elapsed time and desktop TFLite parity. Synthetic smoke-test metrics are not skirt/fabric accuracy. Raspberry Pi ARM64 runtime and camera tests remain separate gates.

Official references checked for this setup: [TensorFlow pip and WSL GPU guidance](https://www.tensorflow.org/install/pip), [Microsoft WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install), [manual feature enablement and restart](https://learn.microsoft.com/en-us/windows/wsl/install-manual), and [NVIDIA CUDA on WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).
