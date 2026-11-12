# Fabric source resolution, October 17

Investigated a new source with publisher-supported physical item identities rather than repeating training on the 17-group appearance pilot. This is a **metadata acquisition and feasibility result**, not new photographs or a usable training release.

The [official DeepFashion attribute page](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/AttributePrediction.html) lists annotations and partitions but provides no Category/Attribute-to-product identity mapping on that page. The separate [Consumer-to-shop benchmark](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/Consumer2ShopRetrieval.html) advertises item correspondences, but that does not establish an exact mapping to the existing Anno_fine filenames. No defensible identity bridge was obtained. The 422 conflicted original-training references remain excluded and no original holdout was reassigned. This bounded investigation cannot establish that no mapping exists anywhere.

## Newly acquired official source

[Norway post-consumer garment data and images, version1.1](https://zenodo.org/records/20440761), published by NTNU researchers, records garments photographed after donation/discard collection and material information transcribed from care labels. The repository API declares **CC BY-SA4.0**. Preserve attribution to Pettersen, Aarak, Peña Benítez and Nourin Moury, the source title/version/DOI, the [license](https://creativecommons.org/licenses/by-sa/4.0/), and changes when distributing adapted source material. No model licensing conclusion is inferred here.

The downloaded CSV has **16,464 rows with 16,464 unique source item IDs**. The saved publisher README explicitly defines `ID (AXXXX)` as Item ID and category9 as Skirts. Offline parsing identifies **227 skirt metadata rows** across six collection areas:41 Ålesund,31 Oslo,45 Stavanger,35 Sandnes,48 Kristiansand and27 Trondheim. These are source item identifiers; photographs and duplicate-item checks have not been inspected.

Of the227 skirts, **172** have flags for a present/readable label and a nonmissing first fibre entry. Raw first-fibre outer-layer counts include55cotton,73polyester,25viscose and54missing entries, plus smaller categories. These counts do not mean pure composition or independent appearance classes. The original table retains multiple fibre percentages and layers. Cotton does not imply a denim weave, polyester does not imply chiffon, and these metadata must not be converted into the existing four-way appearance labels.

The official source does not establish a worn presentation. Photos may support a separate domain or composition study after inspection; they cannot replace target-camera worn-skirt examples without evidence.

## Actual acquisition and checks

Stored in [acquisition directory](../records/acquisitions/2026-10-17-fabric-source-resolution/acquisition.json):

- CSV:5,021,278bytes, publisher MD5 verified; SHA256 `127235b40fcbbd7f26053006cdbb3d6fa2c69f736393fdbb1d346a25e7c99d28`.
- Publisher README PDF:354,716bytes, publisher MD5 verified; SHA256 `8bb82e02358b7460247402137905c8ff9e9edf6783174264859a5b630ecd8785`.
- API record:9,200bytes, SHA256 `04b9115ec9704c5b091fbc4d7209d34847b8a7ee8c010bc4f3a8baced7a6361a`.
- Three bounded primary-page snapshots with URLs/hashes and a text extraction of the README retained alongside the originals.
- [Feasibility counts](../records/acquisitions/2026-10-17-fabric-source-resolution/feasibility.json) and227 metadata candidate rows retain source IDs/raw fields and explicitly mark `image_acquired:false` and `training_eligible:false`.
- Four focused tests passed: metadata-only counts, duplicate-ID rejection, missing-column rejection and absent-label handling. [Log](../records/acquisitions/2026-10-17-fabric-source-resolution/tests.log).

Zero photographs downloaded, zero training admissions, zero model changes, zero installations. Existing original-image count remains1,747. No source split is invented: this metadata release provides no benchmark train/validation/test assignments in its table/API record. Any future source-specific project split needs item-level grouping and full-photo duplicate review before freezing.

## Concrete next step

The six image7z archives total81,141,921,858bytes; the smallest is Trondheim at8,315,255,946bytes. No archive was requested. Before acquisition, establish whether the publisher offers individual-item delivery or whether archive indexing and selective HTTP-range extraction can work within an explicit storage/network bound. A7z archive is not assumed to support independent file reads. Then retrieve a small predeclared item-ID sample, verify archive-photo-ID joins, inspect full visibility/presentation and duplicate groups, and assess label suitability without training. If bounded retrieval fails, retain this as a metadata source rather than downloading81GB by default. No contact message was sent to the publisher.

For the immediate worn appearance target, distinct full-view worn skirt examples with garment/item identity and a reviewed appearance taxonomy remain necessary. This investigation advances source evidence but does not close live fabric acceptance.

Reproduce counts without network using the existing Python runtime:

```text
python tools/datasets/fabric_source_resolution.py --analyze --output records/acquisitions/2026-10-17-fabric-source-resolution
python -m unittest tests.test_fabric_source_resolution -v
```

The offline command verifies the acquired CSV hash/size before parsing. A fresh metadata-only acquisition uses the same command without `--analyze` and requires a new output directory. Its hard allowlist excludes every image archive.
