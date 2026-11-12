# Fabric source expansion

Completed 2026-10-02. **500 distinct images** were acquired from the publisher's FabNet-3k release: **250 in the Cotton folder and 250 in the Polyester folder**. These are source-labelled texture candidates, not verified pure-fiber examples or full-skirt camera images.

## Source and records

- Publisher: Isadchenko Yevhen, [FabNet-3k repository](https://github.com/kolon3d-prog/FabNet-3k), release `1.0.0`.
- [Acquisition report](../records/acquisitions/fabric_expansion.json)
- [Candidate manifest](../data/manifests/fabric_candidates.jsonl)
- [Decode/hash audit](../records/validation/fabric-expansion-audit.json)
- [Local sample contact sheet](../records/review/fabric-contact-sheet.jpg)
- [Acquisition code](../tools/datasets/acquire_fabrics.py)

The publisher declares CC BY 4.0 for the dataset. Individual original photo creator/provenance records are not supplied; retain that limitation and the publisher's attribution. The downloaded README is retained in the source metadata directory. The release archive is 1,673,285,719 bytes; only selected ranges were downloaded. Selected image bytes total **283,607,465**. Full image decoding, ZIP CRC and SHA-256 checks passed.

Four exact-content duplicate candidates were skipped and replaced during selection, including cross-folder Cotton/Polyester duplicates. Their cached originals may remain under the raw source directory, but they are not counted in the 500 unique manifest images. Source folders therefore do not constitute independently verified composition ground truth.

## Issues found in review

1. The README advertises train/val folders, but the actual archive contains class folders directly. The manifest preserves `unspecified_in_archive` rather than inventing an official training partition.
2. Some filenames/descriptions mention multiple fibers or other fibers despite their folder labels. A simple review-keyword scan flagged 23 of the 500 descriptions (7 Cotton, 16 Polyester); this is a review queue, not proof that every other label is correct.
3. Images show fabric surfaces, folds and patterns at close distance. They do not establish performance from a full-skirt camera view.
4. The publisher's Cotton and Polyester labels do not provide the project's denim/chiffon/satin construction labels. Descriptions containing these words cannot automatically become verified labels.
5. Independent physical specimen IDs are not available. Near-duplicate and product-description review must precede split approval.

No FabNet record is currently admitted as a verified project fabric label. Future work can evaluate source-label pretraining after documented source-partition, grouping and label review. Keep source-label results separate from device-domain results.

## TextileNet attempts

The official fabric training URL metadata was downloaded for investigation. It is retained as metadata only. Sample old Wish image URLs returned HTTP 403, and an official archive inspected by the agent was approximately 12 GB; no full TextileNet archive or image subset was acquired in this task. These failures are not evidence that every TextileNet image is unavailable. FabNet-3k was used as a bounded supplementary source, not a replacement for required full-view data.

## Rechecking

```powershell
python tools/datasets/acquire_fabrics.py --verify-only
```

No new packages were installed. Existing Python 3.11.9 and Pillow 12.3.0 handled acquisition and decoding. Temporary GitHub redirect URLs are kept in memory and are not saved as durable download sources.
