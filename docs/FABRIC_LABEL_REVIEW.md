# Fabric source-label review

The 2026-10-03 audit triaged all 500 FabNet candidate descriptions and verified their image hashes. It is lexical evidence review, not visual composition identification or supplier verification. Evidence: [summary](../records/review/fabric-label-review-2026-10-03.json) and [per-image queue](../records/review/fabric-label-review-2026-10-03.jsonl).

There are 250 Cotton-folder and 250 Polyester-folder candidates. The expanded dictionary flags 47 descriptions mentioning a fiber other than their folder, 35 mentioning multiple fibers, nine possible truncated fiber tokens and 148 without the folder fiber explicitly present. Flags overlap. Fifty-six records have high review priority; the other 444 are not thereby verified correct. These counts replace the earlier narrow keyword screen for triage purposes.

Cotton/polyester are fiber terms; satin/chiffon/denim and other textile terms are separate descriptive attributes. Preserve both axes and blends. Filenames mentioning a construction can also describe a print or color; do not auto-promote them to ground truth. No composition percentages are inferred.

All 500 remain outside project fabric training and source-folder pretraining admission: source partition is unspecified, physical specimen grouping is unresolved, and verified composition/construction evidence is absent. Close-up images also cannot establish performance from one full-skirt view. The publisher's original folder and terms remain preserved; no source partition was changed.

Reproduce the audit with a new output prefix:

```text
python tools/datasets/review_fabric_labels.py --self-test
python tools/datasets/review_fabric_labels.py --output-prefix records/review/fabric-label-review-reproduction
```

To release usable fabric labels, obtain linked supplier/tag records (including blend percentages), verified specimen identity and an explicit split policy. Capture full-skirt images of those specimens at the intended station. Each native-resolution software patch inherits the same frame, garment and split. Unavailable evidence stays unknown; acquiring more texture thumbnails does not resolve this gap.
