# Fabric source gate — October 22

The 2018 iMaterialist rules are now readable in the browser. They list academic and non-commercial use after acceptance, with access/security and redistribution restrictions. No acceptance, login, competition entry, annotation-manifest download or photograph acquisition occurred. The [observation record](../records/review/2026-10-22-imaterialist2018-terms.json) records the exact source and inspected sections; it is an agent summary, not a copy of the entire rules.

The [current official rules](https://www.kaggle.com/competitions/imaterialist-challenge-fashion-2018/rules) replace the earlier *unreadable terms* finding. They do not establish that the project has accepted those rules or that a general photo licence exists. Future acquisition needs the user's review/acceptance or another applicable permission basis. Read-only investigation does not enter the competition. Do not apply another year's competition rules to this corpus.

Once that gate is satisfied, the proposed first intake is official training metadata only, with a declared byte/request limit and saved source hashes. No bulk photo download is needed to inspect schema, original partition, URL/source grouping and skirt/material co-occurrences. Before selecting any photographs, establish product/near-duplicate groups and a small review budget. Preserve original validation/test membership. Co-occurring tags still need material-to-skirt association from the original; they cannot automatically become garment-specific labels or fibre-composition truth.

## TextileNet metadata audit

The [offline audit](../tools/datasets/audit_textilenet_metadata.py) and [review record](../records/review/2026-10-22-textilenet-gate-agent.json) establish the cached training manifest's identity against the pinned official Git blob `1912c29bed175c7360b74a7c58eba588c77aee7f`. The existing file contains 155,393 rows and 18,496,507 bytes. This is metadata already on disk, not a new photo collection.

| Metadata identity | Observed count | Interpretation |
|---|---:|---|
| Exact URLs | 147,712 distinct | 5,223 repeated URL groups, with 7,681 excess rows |
| Filenames | 154,969 distinct | 161 repeated filename groups, with 424 excess rows |
| Exact URLs with multiple material tags | 125 groups | Retain all source tags; overlapping tags are not automatically errors |
| Confirmed skirts/material-to-skirt associations | 0 verified | The three fields are filename, material tag and URL; no garment category or product mapping |

There are no locally cached protected TextileNet manifests for this audit, so cross-partition overlap remains untested. An exact repeated URL supplies grouping evidence; distinct URLs and image IDs do not prove distinct products or physical garments. A TextileNet training filename does not establish original iMaterialist partition membership. The auditor never requests image URLs or emits protected label distributions, and enforces byte/row bounds even if a file grows after its initial size check. Seven focused tests pass; root independently recomputed the full cached summary and verified all three saved primary-response bodies and the official Git blob.

Do not execute the upstream `prepare_data.py` for a training-only intake. Inspection at the pinned revision found that normal operation downloads test images before training images; its `--test` option chooses ten protected test rows. Published training code also uses test results for checkpoint selection. The project must preserve its own held-out policy. Downloaded source code was read as evidence, never executed.

The source paper's Appendix F asserts dataset CC BY without specifying its version in that statement; the README's wording concerns manuscripts. Appendix C.2 additionally calls reconstructed iMaterialist CC BY4.0. That author assertion does not resolve the original 2018 rules' conditions or establish upstream per-photo attribution. Preserve these separate claims; neither the article's licence header nor the repository's MIT code licence supplies a blanket photo-use conclusion. See [the primary paper](https://arxiv.org/html/2301.06160v1) and [pinned repository](https://github.com/hahashu/TextileNet/tree/6b4f0579b2abc18422192afea07882f84dcb83e4).

Seven direct metadata requests read 129,919 response-body bytes under a 250,000-byte budget; three final response bodies are saved inside the review record with hashes. The earlier four inspection requests and their retention limits remain recorded separately. These requests acquired no photos or archives. Browser/web-tool reads are outside that direct-download accounting.

To reproduce the local identity audit with a new output filename:

```text
python -B tools/datasets/audit_textilenet_metadata.py --train data/external/fabric_expansion/metadata/fabric_train.json --output records/review/a-new-textilenet-identity-audit.json
```

Next: resolve applicable grant/version and attribution, join original source IDs/partitions, then declare a small training-only original-photo review. The cached schema cannot select confirmed full-view skirts by itself.

This work adds no photos, independent fabric labels or training admissions. The collection remains 1,932 originals and the existing 17-group fabric smoke remains research-only. Stronger fabric fitting, actual wearer references, calibrated length and physical/Pi acceptance remain open.
