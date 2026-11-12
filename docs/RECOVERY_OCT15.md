# Hardware-independent recovery — October 15, 2026

The user confirmed that neither physical skirts nor a Raspberry Pi is available. Software and source-data work continues; this does not close camera-domain, calibration or Pi acceptance.

## Runtime and packaging

Recovered the localizer loader hardening: it rejects missing/mismatched preprocessing and thresholds before creating a runtime, and validates exactly one input and output before indexing tensor details. Valid v1/v2 model behavior remains unchanged.

The desktop recovery suite ran247 tests with one TensorFlow-specific test skipped in that interpreter. The separate training environment ran all three scene-balance tests, including the TensorFlow loss check. Fourteen mocked camera scenarios passed. The research-v5 bundle passed all14 payload hash checks before and after an actual private HTTP run; three saved-frame predictions exactly matched the selected baseline. The private server was stopped; no camera was activated.

- [Desktop recovery test log](../records/validation/2026-10-15-recovery-tests.log)
- [Actual bundle HTTP results](../records/validation/2026-10-15-live-http-bundle.json)
- [Bundle details and inventory hash](OFFLINE_RELEASE.md)

## Detection outcome

The interrupted October14 v3 folder contained inputs and environment evidence but no completed model or metrics. A fresh October15 run tested scene-balanced loss with the same frozen data, architecture and mask threshold. [Actual experiment and comparison](LOCALIZER_V3_RESULTS.md).

| Exported path | Accepted skirts | Correct pleating outputs | Rejected negatives |
|---|---:|---:|---:|
| Original localizer | 48/80 | 38/80 | 10/19 |
| V2, unbalanced scenes | 59/80 | 52/80 | 8/19 |
| V3, balanced scenes | 51/80 | 42/80 | 5/19 |

V3 is not promoted. Its export parity passed, but correctness of conversion cannot compensate for poor rejection. All figures come from reused agent-reviewed source-domain development data, not independent live-camera tests. Keep the current launch unchanged and do not call any of these paths public-ready.

## Fabric and remaining work

Recovered official attribute metadata identifies680 skirt references, including52 denim,74 chiffon and51 leather appearance annotations. These are neither downloaded photographs nor verified independent garments. [Source feasibility and partition limitations](ATTRIBUTE_SOURCE_FEASIBILITY.md). No source images are included in the demo bundle.

The exact original-split join subsequently found422 training,66 validation and192 test references within those680 fine-subset training rows. The broader holdout attribute rows had therefore already been encountered during metadata inspection; they were not used for training or evaluation. All422 original-training references share descriptive folder tokens with original holdouts. Because those tokens do not establish independent garments, the conservative intake policy admits zero images pending identity/group resolution. See the source feasibility record for the exact partition and exposure limits.

The next fabric milestone is defensible source-item grouping or another suitable source, followed by bounded image intake and original-image review. Detection needs a better-supported validity approach rather than repeated promotion of failed candidates. Automatic hem/body geometry extraction, measured calibration, suitable fabric inference, actual Pi installation and supervised garment rehearsal remain outstanding. The requested85% completion has not been achieved.
