# Additional fabric source feasibility

October 15, 2026. Recovered the interrupted metadata-only analysis. No photographs were downloaded or admitted, and no dependencies were installed. The existing original-image total is unchanged.

The official DeepFashion **Anno_fine** training metadata contains 14,000 image references, of which 680 have category `Skirt` (one-based category 33). Its dictionary has 26 fine attributes, distinct from the broader benchmark's 1,000-attribute dictionary. Exactly one type-5 source attribute is present per skirt row in these files; this source encoding is not evidence that real textile properties are mutually exclusive.

| Source attribute | Skirt image references | Descriptive folder tokens |
|---|---:|---:|
| denim | 52 | 23 |
| chiffon | 74 | 50 |
| cotton | 465 | 198 |
| leather | 51 | 25 |
| faux | 1 | 1 |
| knit | 37 | 22 |

There are 241 distinct folder tokens across all 680 references. Tokens overlap between attributes and are descriptive titles, not garment IDs. These numbers are **metadata candidates**, not usable training images or independent garments. No originals have been inspected for full visibility, label fit, or related-item duplication. Do not turn cotton into a verified fiber label or infer actual leather from an appearance annotation.

The five saved input files were checked against acquisition SHA-256 hashes and byte sizes before row-order joining. Dictionary lengths, category bounds, binary attribute dimensions, unique paths and safe path patterns are checked. The [feasibility record](../records/acquisitions/2026-10-14-attribute-metadata/feasibility.json) holds all hashes and exact counts; the [reference manifest](../records/acquisitions/2026-10-14-attribute-metadata/skirt-attribute-references.jsonl) retains `Anno_fine/train` and marks every row ineligible for training. The original [October 14 acquisition report](../records/acquisitions/2026-10-14-attribute-metadata/report.json) is preserved unchanged.

The subsequent exact original-partition join found **422 train / 66 validation / 192 test** references among these 680 fine-training rows. The two benchmark splits do not coincide. Although separate test/validation attribute files were never requested, the fine-training metadata already loaded includes attributes for 258 broader-benchmark holdout references. This exposure is now explicitly documented; none was used in model training or evaluation. The earlier acquisition report's `test_labels_accessed: false` refers only to separate fine test files and must not be generalized to the broader benchmark.

The public original partition mapping was acquired under a 30 MB cap: 22,150,149 bytes and 289,222 unique rows, SHA-256 `ccad42e707ecbb430d55e88f310a0be4540ee7c17655304789c73ee2945e0bca`. Every exact match succeeded. All 422 original-training references belong to descriptive folder tokens also occurring in original validation/test partitions. Under conservative whole-folder grouping, **zero candidates are eligible for acquisition/admission**. This may overgroup different products sharing a title; it is preferable to claiming independent garments without evidence. See [partition feasibility](../records/acquisitions/2026-10-14-attribute-metadata/partition-feasibility.json) and [joined references](../records/acquisitions/2026-10-14-attribute-metadata/skirt-original-partition-join.jsonl).

Next step: obtain a publisher-supported item-identity mapping that can resolve descriptive-folder ambiguity without shifting original holdouts, or use a different source with verified garment groups. The present source does not unblock fabric training safely. Do not download this pool as if its fine `train` label ensures project eligibility. Full-view appearance feasibility remains separate from composition evidence.

The [official benchmark page](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/AttributePrediction.html) and [terms](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html) were checked on October 15. The terms restrict use to noncommercial research and internal copies within one organization, with no further distribution. Research-source images must not be added to the public demo package. Earlier saved source-page observations and folder provenance are in the [October 14 research report](../records/acquisitions/2026-10-14-fabric-source-research/report.json).

Reproduce offline analysis with `python tools/datasets/inspect_attribute_source.py --analyze`; `--join-partitions` reuses the saved partition file or fetches the bounded public metadata when absent. Focused checks: `python -m unittest discover -s tests -p test_attribute_source.py` (12 tests). This does not train a model or establish live fabric accuracy.
