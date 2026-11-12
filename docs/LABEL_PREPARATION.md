# Label preparation, version 1

Prepared 2026-10-03. Original images and the existing development split are unchanged. Machine-readable evidence: [preparation report](../data/labels/skirt-preparation-v1/report.json), [48 visual reviews](../data/labels/skirt-visual-reviews-v1.jsonl), and [sheet index](../records/review/label-sheet-index.json).

All 1,000 source skirt records have a review queue entry. Explicit source attributes contain 137 `pleat` and 510 `no special manufacturing technique` records, with no overlap. The remaining 353 cannot be assigned either label. Absence of `pleat` never means non-pleated.

The agent inspected 48 annotated skirt ROI crops with context: the first 24 sorted records from each explicit source category. This is a targeted review, not a representative error-rate estimate. Thirty-five reviewed records were withheld from the auxiliary subset due to framing, uncertainty or visual disagreement. Agent review is not independent human verification.

| Prepared task | Train | Validation | Meaning |
|---|---:|---:|---|
| Source manufacturing annotations | 489 | 123 | 118 source pleat and 494 source no-special-manufacturing; noisy auxiliary supervision |
| Single-agent reviewed full-skirt appearance | 12 | 1 | 5 pleated and 8 non-pleated; pending second review |
| Complete review queue | 810 | 190 | All 1,000 candidates; most still require visual review |

The appearance validation subset has only one pleated example and no negative examples. **It is not adequate for classifier evaluation.** Do not report an accuracy score from it or move examples across the frozen split to improve scores. The source manufacturing task is not the final pleated/non-pleated task: its negative category has a different meaning and source annotation errors were observed.

`tools/datasets/prepare_labels.py` preserves connected-group assignments from the existing split and rejects protected/unknown partitions, conflicting groups, duplicate identities and mismatched review hashes. To reproduce, select a new output directory:

```text
python tools/datasets/prepare_labels.py --output data/labels/skirt-preparation-reproduction
```

No physical length, fiber composition or independently verified garment identity is derived from these images. No held-out seed images are admitted. Dataset image count remains 1,512. Completion of the queue and source mapping is not completion of final ground-truth annotation: 952 skirt images still lack visual review, and all reviewed appearance labels need independent confirmation before final evaluation use.

Next label work: review both development partitions without consulting model predictions, inspect complete originals where ROI context is insufficient, record garment/duplicate relationships, and collect single-view camera-domain specimens with physical measurements and supplier/tag evidence. Preserve review versions and regroup only through an explicitly versioned split revision before experiments, never by silently reshuffling an existing evaluation.

## Version 2 completed October 4

The earlier 48-review status is historical. All 1,000 candidates have been visually inspected across three batches, with per-image evidence saved. Eight prior/new conflicts were quarantined. Version2 contains 375 full-view appearance candidates; the stricter frozen baseline removes three otherwise eligible suspected garment repeats, leaving 372. Source-manufacturing auxiliary admission is 256 after all reviews; it remains a separate task. Agent review is not independent human ground truth. [Counts, exclusions and baseline](BASELINE_RESULTS.md).
