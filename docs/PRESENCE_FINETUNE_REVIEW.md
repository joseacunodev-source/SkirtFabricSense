# Independent presence candidate admission review

October 18, 2026, Asia/Manila. Scope: source/admission review of [prepared trainer](../tools/training/train_presence_finetune.py), its [protocol](PRESENCE_FINETUNE_PROTOCOL.md), existing tests and imported validators. This review did not fit a candidate, evaluate model accuracy, calibrate thresholds, install packages or test a camera/Pi.

## Findings and correction

Two admission weaknesses were reported to root and corrected in the production loader before this review finished:

- Negative admission previously required an inspected original but did not bind the review's image hash to the admitted row. It now requires at least one review hash, rejects any conflicting present hash, and checks optional sample/path identity.
- Positive count and assignment checks did not pin the frozen manifest bytes. The loader now pins positive manifest SHA-256 `876bb315009592fdbcf0a646703b21d99801756f4e37b1807a66675bdbd98ec2` and source-split SHA-256 `df3b096e4d131db55852b20de075d811c95520d23766648928555d755fe8812c`. It also requires supported presentation-review method and nonblank reviewer/evidence.

The new [independent regression tests](../tests/test_presence_finetune_review.py) exercise stale, missing and conflicting negative hashes, wrong review sample identity, and actual changed positive/split bytes. Quarantined rows remain excluded; v3 data are not admitted by this review. Existing reviewed v2 inputs yielded 331 positives (265/66) and 75 negatives through the loader.

## Observed WSL checks

Interpreter: `/home/skirttrain/skirt-fabric-sense/.venv-training/bin/python`, Ubuntu-24.04 as `skirttrain`.

The actual cached pretrained file `/home/skirttrain/.keras/models/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224_no_top.h5` exists. Its SHA-256 is `f8aff69536bd77a692c594f559c798c19bf7f3f36668fc9fa00b21c6aab4797c`, matching [recorded provenance](../records/acquisitions/2026-10-04-mobilenetv2-weights.json). Actual Keras MobileNetV2 construction from that local path succeeded without downloading. The real Keras variable audit confirmed zero trainable backbone variables in the head phase, only eligible block13-and-later variables in the fine-tuning phase, and no trainable BatchNormalization variables. This checks configuration, not whether weights stay unchanged during fitting; the trainer's per-epoch digests must establish that during a real run.

Command from project WSL directory:

```text
/home/skirttrain/skirt-fabric-sense/.venv-training/bin/python -m unittest tests.test_presence_finetune tests.test_presence_finetune_review -v
```

Observed result: **14 tests passed in 17.035 seconds**. The original eight tests also passed separately before correction. The actual-Keras test skips in interpreters without TensorFlow; that skip is not equivalent to the recorded WSL pass.

## Training/export review limits

Source inspection confirms recompilation for each phase, a `training=False` backbone call, frozen BatchNormalization layers, per-epoch frozen-weight digests, training-only class weights, equal-class validation BCE selection over both phases, and fixed threshold 0.5. The intended conversion uses built-in TFLite operators and checks one float32 `[1,224,224,3]` input and one float32 `[1,1]` output. Early and final parity gates compare every admitted validation prediction at tolerance 0.001 with finite-difference checking.

**Conversion and parity were inspected, not executed by this review.** They still require the actual candidate run and archived evidence. No candidate performance, new negative-manifest admission, live acceptance or Pi compatibility is established here. Weight redistribution remains independently uncleared as recorded in the original acquisition provenance.
