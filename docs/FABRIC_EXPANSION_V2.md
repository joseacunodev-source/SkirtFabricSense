# Fabric expansion recovery — October 13, 2026

The bounded acquisition selected 30 previously unused original-training item groups, all carrying the source's cotton appearance label. **Zero new images were downloaded successfully.** The process was stopped after several minutes with no completed-image progress. The precise network stage and cause were not observable; this is not evidence of a quota error or source removal. No retry was made without an identified transient cause.

The existing fabric pool therefore remains 25 original images. The selection does not add specimens, training examples or verified composition labels. Existing original query/gallery partitions remain protected. All 15 available non-cotton training groups in this source were already represented in the first intake; the remaining 106 unused groups are cotton-source only. More acquisition from this source cannot fix rare-class coverage.

## Preserved evidence

- [Interruption report](../records/acquisitions/2026-10-13-fabric-v2/report.json): zero completed images, source/partition/terms hashes and actual UTC recording time.
- [Selected metadata](../records/acquisitions/2026-10-13-fabric-v2/selection.json): 30 source groups, no project split or admission.
- [Executed source snapshot](../records/acquisitions/2026-10-13-fabric-v2/acquisition_source.py): original attempt retained separately from later tooling improvements.
- [Targeted checks](../records/acquisitions/2026-10-13-fabric-v2/tests.log): four selection tests and four offline integrity tests passed using installed Windows Python 3.11.9/Pillow. No packages were installed or changed.

The original attempt buffered request telemetry until completion; no completed-request evidence survived interruption. The current [acquisition tool](../tools/datasets/expand_fabric_v2.py) now saves atomic progress checkpoints before download resolution and each range request, after completed ranges, and after saved images. Checkpoints exclude transient signed URLs. This improvement is source-reviewed; it was not exercised by another live download. Existing output directories are deliberately refused to preserve the interrupted record; a future retry needs a fresh versioned output location and unchanged candidate-only policy.

The prepared [offline verifier](../tools/datasets/verify_fabric_v2.py) checks files, dimensions, original train membership, source labels, source groups and exact RGB duplicates against v1. Its four tests use synthetic fixtures; there is no real v2 manifest to verify yet. Near-duplicate and visual label review still require actual images. The source terms permit restricted noncommercial research/internal copies and prohibit redistribution; these are source appearance annotations, not fiber-composition evidence.

Next acquisition work should prioritize a separately licensed source with additional independent non-cotton skirt groups, while retaining the current fabric smoke model as an unpromoted pipeline experiment.
