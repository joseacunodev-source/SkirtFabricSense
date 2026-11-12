# Worn-presentation audit

## Complete supplemental review — October 17

Superseding the bounded counts below: all372 records reviewed,331 worn/27 hanging/8 mannequin/6 unknown. Methods:22 direct originals and350 contact-sheet samples. All30 sheet hashes/index bindings checked; six unknowns also inspected individually. Worn development subset preserves265train/66validation. [Complete evidence and exclusions](OCT17_NEXT_MILESTONE.md).

October 16, 2026. This is a coverage audit and a bounded visual review, not a new training release or a complete 372-image presentation review.

The audit verifies all 372 original file hashes and checks that their group hashes and frozen split assignments match the source split manifest. It preserves 292 training and 80 validation images. Existing pleating notes are retained verbatim; words such as “hanging” in free text are not automatically converted into presentation labels.

Twelve full originals were actually opened and inspected, separately from the earlier contact-sheet pleating reviews. The initial selection was the first two records per split/pleating class in frozen manifest order; four additional training records at positions 5–8 in the training sequence were inspected. This is a deterministic convenience sample, not a random or representative estimate of the whole dataset.

| Coverage | Training | Validation | Total |
|---|---:|---:|---:|
| Original images audited | 292 | 80 | 372 |
| Visually confirmed worn presentation | 8 | 4 | 12 |
| Presentation still unknown in this audit | 284 | 76 | 360 |

Of those twelve, ten show feet/shoes and a support surface; two crop the lower legs. Nine have a discernible waistband portion and three obscure it with outer clothing or a belt. All twelve have a visible hem. These observations do **not** establish anatomical keypoints, a valid projection, body proportions, calibrated geometry or any length label. Several have striding/crossed legs, heels, spectators, side/rear poses or asymmetric hems. Boolean visibility means the feature is discernible in this visual review; `false` means it was not established, not a pixel-level occlusion annotation.

All observations are single-agent reviews, not independent human ground truth. There are zero newly admitted training examples, zero measured geometry references and no new verified physical-garment count. Existing dataset licenses, grouping limitations, split assignments, models and metrics are unchanged. No package was installed and no camera was activated.

## Reproduce

```text
python -m unittest tests.test_worn_readiness -v
python tools/datasets/audit_worn_readiness.py --reviews records/review/2026-10-16-worn-readiness-observations.jsonl --output records/review/2026-10-16-worn-readiness-rerun.json
```

Seven targeted tests passed on the existing Windows Python 3.11 environment. They check hash binding, duplicate/foreign review rejection, split changes, group leakage, explicit observation requirements and preservation of unknowns. The CLI additionally checked every original's bytes against its frozen SHA-256. The report records input/tool hashes and provides all 360 pending sample IDs for continued review.

Subsequent root review hardened report creation: output files now use exclusive creation and cannot overwrite an existing evidence record. An eighth test verifies that a rejected overwrite leaves the original bytes untouched. The historical audit report and its recorded pre-hardening source hash remain unchanged; reruns must select a fresh output filename and will record the current source hash. This implementation fix does not change audit observations or counts.

- [Audit and pending review queue](../records/review/2026-10-16-worn-readiness.json)
- [Actual visual observations](../records/review/2026-10-16-worn-readiness-observations.jsonl)
- [Audit tool](../tools/datasets/audit_worn_readiness.py)

Complete the remaining presentation/visibility review before freezing a worn-only subset. Retain existing groups and splits; resolve source usage and physical-item grouping rather than equating image count with garment count. Worn-only metrics require an explicit versioned subset and paired evaluation; the existing aggregate 65/80 pleating result cannot be renamed worn accuracy.

October 17 independent review fixed stale audit dates and rejected whitespace/non-string reviewer notes. Use `--audit-date 2026-10-17` to record the explicit current review date; otherwise the tool uses the current Asia/Manila date. Historical reports remain unchanged. These changes affect audit integrity, not presentation labels.
