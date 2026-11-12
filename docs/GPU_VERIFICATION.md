# GPU verification gate

Run with the isolated WSL training interpreter after completing [GPU setup](GPU_SETUP.md):

```bash
python tools/training/gpu_smoke.py --output artifacts/runs/gpu-smoke-001
```

The output directory must be new. The command fails if TensorFlow is absent, no GPU is found, gradients are invalid, weights do not change, conversion fails or desktop TFLite parity exceeds tolerance. It records source hash, seed, versions, GPU device placement, SGD configuration, loss, elapsed step time and model hash. Inputs are synthetic; no dataset or split is used, and loss is not project accuracy. Memory and throughput benchmarks are not measured here.

The model is a small randomly initialized CNN. Export uses fixed batch-one input and built-in TFLite operations, with absolute tolerance 1e-5 and relative tolerance 1e-4 against TensorFlow output. This is an early toolchain gate; MobileNetV2 and INT8 conversion need their own verification. Raspberry Pi compatibility requires an actual ARM64 device test.

Current status on 2026-10-03: script prepared; successful GPU execution and conversion remain unverified because Windows restart and WSL/TensorFlow installation are pending. Preserve failed-run records. Follow with a real-data experiment only after task labels and validation class coverage are adequate.

## Actual result after restart

[Run 002](../records/experiments/2026-10-03-gpu-smoke-passed.json) passed on the RTX 3060 with TensorFlow 2.20.0. GPU placement, finite gradients and weight changes were verified; Keras-exported float TFLite matched within combined absolute/relative tolerance. Run 001 trained on GPU but failed export inference; its failure is retained. Use Keras `model.export` for this tested version combination. See [setup record](GPU_SETUP.md). No Pi or real-data accuracy claim follows from this result.
