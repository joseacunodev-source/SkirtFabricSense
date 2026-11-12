# Skirt image expansion

Completed 2026-10-02. **1,000 distinct original images** were acquired from the official Fashionpedia `train2020` archive, with original skirt annotations. This is separate from the 12 previously downloaded validation images.

## Evidence

- [Acquisition report](../records/acquisitions/skirt_expansion.json)
- [Candidate manifest](../data/manifests/skirt_candidates.jsonl)
- [Combined integrity audit](../records/validation/dataset-expansion-combined-audit.json)
- [Local sample contact sheet](../records/review/skirt-contact-sheet.jpg)
- [Intake code](../tools/datasets/acquire_skirts.py)

The script selected one annotated skirt instance per image, using seed 20261002 and prioritizing Creative Commons-labelled sources. Images were selectively extracted with HTTP byte ranges from the official 3.34 GB archive. The complete archive was not downloaded. Image bytes total **76,214,531**; original training metadata is separately retained. All selected images decode and match the original annotation dimensions and archive CRC. Each has a SHA-256 hash, source image ID, source URL, license record, box, mask and attribute list. No augmentation increased the count.

## Labels and limits

Source attributes include 137 images annotated with `pleat`, 178 with `a-line`, 179 with `pencil`, and 224 with `straight`. These attributes overlap and must not be added as disjoint class totals. Missing `pleat` is not automatically a verified non-pleated project label. Source fashion length attributes do not establish measured physical length in the project fixture.

The explicit auxiliary admission `source_skirt_presence` means the official source identifies a skirt region. It does not approve project fabric/style/length labels or prove an independent physical garment. One positive class alone is not a complete presence classifier; localization development can use the actual region annotations. Related-image grouping and negative data remain relevant.

Visual sample review found diverse runway, event, street and product imagery. Some images have hidden waistbands, truncated hemlines, occlusion or dress-like appearances despite source skirt annotations. The collection is useful source data; it is not 1,000 verified examples of the final controlled full-skirt station. See [review findings](DATASET_REVIEW.md).

## Usage terms

[Fashionpedia's terms](https://fashionpedia.github.io/home/data_license.html) license annotations separately from photographs. Source-image license counts in this sample are:

| Source license description | Images |
|---|---:|
| Attribution-NonCommercial-NoDerivatives | 444 |
| Attribution | 135 |
| Attribution-NonCommercial-ShareAlike | 118 |
| Attribution-ShareAlike | 70 |
| Attribution-NonCommercial | 128 |
| Attribution-NoDerivatives | 105 |

These are publisher metadata preserved at acquisition, not independent current license revalidation. Do not apply a blanket CC BY license to the image collection or release redistributed/modified images without checking each source's terms. Retain original source links and license versions in the manifest.

## Rechecking

```powershell
python tools/datasets/acquire_skirts.py --verify-only
```

This verifies local hashes and decoding without network. Default acquisition mode may revisit archive metadata/terms even when the desired image count is already present; use verify-only for routine checks.
