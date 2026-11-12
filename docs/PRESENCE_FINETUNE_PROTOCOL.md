# Prespecified worn presence fine-tuning candidate

October 17, 2026. Source preparation only: no candidate training or performance result is established by this document. Run after the new negative extension has passed review and has a frozen admission manifest. The existing worn manifest remains immutable; this experiment explicitly reuses its 265 training and 66 validation positives for research. It does not promote the manifest to independently confirmed labels.

The candidate jointly changes positive presentation scope, negative data and optimization compared with earlier presence runs. Improvements cannot be attributed to fine-tuning alone. Use shared-subset predictions when comparing older models, and report new-domain groups separately. There is no untouched final-test or physical-camera claim.

Prespecified procedure:

- Seed42; batch8; full RGB bilinear resize224, float32 0..255, model-internal MobileNet normalization; independent horizontal flip probability0.5 on training only.
- ImageNet MobileNetV2 average features, Dense64 ReLU, Dropout0.2 and sigmoid1.
- Three head epochs with the entire backbone frozen, Adam0.001.
- Five fine-tuning epochs with block13 expansion onward trainable, Adam0.00001. Every BatchNormalization layer stays frozen and the backbone is invoked with `training=False`. Earlier backbone layers stay frozen.
- Training weights `N/(2*N_class)` from admitted training scenes only. Validation selection is mean positive BCE and negative BCE with equal class weight, across all eight epochs. Fixed threshold0.5; no threshold tuning.
- Verify unchanged frozen backbone weights each epoch, recording phase layer lists and hashes. Export after epoch1 to catch conversion faults early; export the globally selected checkpoint at the end. Require float32 `[1,224,224,3]` input and `[1,1]` output, built-in TFLite operators, and maximum absolute probability difference at most0.001 over every admitted validation image.

`tools/training/train_presence_finetune.py --negative-manifest data/labels/negative-reviewed-v3.jsonl --output /home/skirttrain/skirt-fabric-sense/runs/UNIQUE_RUN` must execute with the recorded training interpreter. The output directory must be new. The future v3 manifest is not assumed to exist or be acceptable. The loader rejects missing/escaping paths, changed original bytes, protected source partitions, cross-split groups, duplicate images, missing negative admission/review and mismatched frozen positive assignments or presentation hashes. Quarantined negative records remain in the source manifest and are excluded from fitting.

The run records exact input/assignment hashes, expanded rows, actual split/class counts, executed source copies/hashes including reused validators, environment snapshot, package versions, cached pretrained weight provenance/hash, phase history, selected checkpoint, validation predictions and export checks. Pretrained weights must already match the recorded cache hash; no automatic download or installation occurs. Failures retain a failed run record. Counts derive from the actual input manifest; no fixed99-image denominator is imposed.

Promotion requires comparison of both usable skirt coverage and non-skirt rejection through the complete localization/pleating chain, review of failures and independent acceptance evidence. Presence scores do not establish full-skirt visibility, body-reference validity, physical accuracy or Pi compatibility. The model remains experimental until those gates pass.

## October18 review and comparison criteria

Before fitting, pin the existing worn manifest and source assignment hashes and verify every supplied negative review hash/identity. Both inherited hash conventions (`sha256` and `image_sha256`) must agree when present. Regression checks and an actual cached-weight Keras freeze audit passed.

The exported development comparison evaluates four fixed paths on identical frozen validation inputs: v1 mask alone, v2 mask alone, and each mask with the new presence gate. Primary candidate is v2 mask plus presence, motivated by the earlier v2 mask coverage gain and rejection weakness. For this development comparison, require at least baseline-v1 accepted skirts, at least baseline correct pleating, and strictly more rejected negatives together. Thresholds remain0.5; no threshold fitting occurs. Criteria were recorded before reading candidate evaluation outputs. Passing these relative development checks cannot establish demonstration or Pi acceptance.
