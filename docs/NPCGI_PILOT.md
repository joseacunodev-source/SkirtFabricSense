# NPCGI selective image pilot — October 18, 2026

Five original JPEGs were acquired from [Norway post-consumer garment data and images, version 1.1](https://zenodo.org/records/20440761) using exact ranges from the verified [Trondheim archive index](FABRIC_ARCHIVE_INDEX.md). The five requests returned exact HTTP206 responses and **19,643,287 body bytes total**; each original passed its archive CRC32, JPEG decoding and file/pixel hashing. No full archive was downloaded. No packages were installed.

The [selection](../records/acquisitions/2026-10-18-npcgi-pilot/selection.json) was saved before any photograph retrieval or viewing: readable care-label records were sorted by source item ID within first-fibre cotton and polyester groups, then interleaved until five IDs were selected. This is a bounded feasibility sample, not representative or class-balanced training data. Multiple fibre percentages and layers remain as raw source fields. Cotton is not mapped to denim, and polyester is not mapped to chiffon.

## Actual photo inspection

All five original photographs were displayed for one agent's visual inspection; their source-ID cards match the filenames. They are flat-laid garment photographs, not care-tag-only images. None is a worn-skirt example.

| Predeclared source ID | Observation | Status |
|---|---|---|
| F1564 | Sleeveless belted dress; neck opening, arm openings and bodice visible | Quarantined: source skirt category conflicts with image |
| F0848 | Plaid skirt; waistband-to-hem outline contained | Full-view skirt candidate; unadmitted |
| F1810 | White elastic-waist garment is bunched/folded; full silhouette/hem uncertain | Quarantined: visibility uncertain |
| F0870 | Dark skirt-like garment reaches and is cut by the upper image border | Quarantined: incomplete frame |
| F1350 | Dark skirt; waistband/hem contained, with material folds | Full-view skirt candidate; unadmitted |

The [hash-bound review](../records/acquisitions/2026-10-18-npcgi-pilot/photo-review.json) supplements the immutable acquisition manifest. **Zero training admissions, zero split assignments, zero new appearance labels and zero model changes.** Source care-label transcriptions are retained as publisher evidence, not verified fibre measurements or visual appearance truth. Five unique file and decoded RGB hashes were checked; there were no exact file duplicates against the other project manifests. Near-duplicate and independent physical-identity validation remains incomplete.

## Provenance and rights

Preserve attribution to Johan Berg Pettersen, Solveig Aarak, Vanessa Peña Benítez and Nazia Nourin Moury; the full source title *Norway post-consumer garment data and images: 16 464 clothing samples from donations and discards*, version 1.1, [DOI 10.5281/zenodo.20440761](https://doi.org/10.5281/zenodo.20440761), and [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Original bytes are unchanged; the acquisition operation is selective extraction from the publisher archive. The [candidate manifest](../data/manifests/npcgi-pilot-candidates.jsonl) records exact archive filenames, source item IDs, offsets, sizes, CRCs, hashes, raw multilayer metadata and `NPCGI:<item ID>` grouping. The collection provides no source benchmark split; `split` and `source_split` remain null. The license does not by itself establish an interpretation of model licensing.

The source-ID category conflict found in this five-item pilot is a reason to inspect future images rather than accept category metadata automatically. These photographs have a different presentation from the worn-skirt target. Two full-view skirt candidates cannot establish live fabric feasibility or accuracy.

## Tool and verification

The [acquisition tool](../tools/datasets/acquire_npcgi_pilot.py) re-verifies the CRC-bound encoded header and reconstructs the archive index before selection. It accepts only independent Copy streams with defined image CRCs. Policy limits are five requests, 32 MiB total HTTP body bytes and 8 MiB per image. It rejects redirects, HTTP200, unexpected Content-Range/encoding/length before body consumption; reads at most the requested size plus one byte; and refuses to overwrite existing evidence or originals. No whole-archive fallback exists.

All **16 focused tests passed**: nine header parser tests and seven acquisition tests. Checks cover real saved-header reconstruction and deterministic IDs, unsupported stream layouts, duplicate metadata IDs, response validation before reads, truncated/overlong bodies and request/byte bounds. [Tests](../records/acquisitions/2026-10-18-npcgi-pilot/tests.log), [actual network report](../records/acquisitions/2026-10-18-npcgi-pilot/report.json), and [execution/hash record](../records/acquisitions/2026-10-18-npcgi-pilot/execution.json) are retained. The existing evidence directory is intentionally not reusable for another download.

```text
python -m unittest tests.test_fabric_7z_header tests.test_npcgi_pilot -v
```

The next useful source step is a separately bounded, predeclared image review with category-conflict handling and an operational composition/appearance study. Expanding this flat-laid sample alone does not resolve the worn-domain training requirement.
