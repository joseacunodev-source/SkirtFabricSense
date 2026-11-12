# Expansion code review — October 13, 2026

Independent agent review covered the negative and full-view fabric intake scripts and their archive readers. This review concerns data acquisition and isolation, not visual labels, physical garment identity, training quality or Raspberry Pi behavior. No dependencies were installed and the reviewer made no downloads.

## Findings and fixes

- Negative selection initially checked a permitted licence name and a generic Creative Commons URL prefix separately. The owning agent changed selection and cached verification to require an exact permitted name/URL pair. This prevents a permitted name from masking a NoDerivatives or unrelated URL.
- The negative image reader initially inherited a loader that decoded pixels before checking size. The new wrapper rejects more than 24 million pixels and annotation-dimension mismatches before loading pixels.
- Negative source identity now normalizes static Flickr size variants and Flickr photo-page URLs to the same photo ID. The old protected seed manifest uses `source_image_id` and `source_page`; the recovered selector now handles those fields. Existing candidate manifests remain exclusions, including previously quarantined examples.
- Negative cached verification checks content hash, decoded dimensions, file size, permitted terms, unique sample/canonical source identity, source partition and unadmitted status. Cross-intake duplicates and unresolved photo-session relationships still require the combined audit and visual review before admission.
- Fabric selection excludes every previously acquired v1 item, including rejected items, and every item with any original query/gallery view. It rejects inconsistent source labels within an item. No protected group is borrowed to balance classes.

The available new original-train fabric pool contains **106 source-cotton items only** after these exclusions. The selection chooses 30 items from that pool. This adds appearance diversity but cannot resolve scarce denim, leather or chiffon classes; source cotton annotation does not verify fiber composition.

## Read and write boundaries

Negative intake uses bounded ZIP-member reads, decoded-member size/CRC checks, safe local filenames and at most 132 member attempts with four workers. The shared reader can retry network requests, so member attempts are not an HTTP request count. Fabric intake uses the bounded ZIP/ZIP64 reader: exact inclusive ranges, central/local identity checks, CRC, decompression limits and no arbitrary archive extraction. The fabric HTTP adapter requires the exact requested Content-Range and reads at most one byte beyond the requested length to reject oversize responses. New manifests explicitly remain unadmitted and unsplit.

Fabric source terms remain internal, single-organization, noncommercial research use; images must not be included in public releases. Negative rights are recorded from source metadata, not freshly verified photographer permissions. Neither source's annotation is independent project ground truth.

## Checks actually run

Using the existing Codex bundled Python 3.12 environment with `-B -m unittest discover -s tests -p <file> -v`:

| Test file | Result |
|---|---:|
| `test_negative_expansion_v2.py` | 4 passed |
| `test_fabric_expansion.py` | 4 passed |
| `test_bounded_zip.py` | 20 passed |

The fabric selector test checks the actual saved source-partition join, including old and protected group exclusion. The reader tests include sparse ZIP64 offsets above four GiB, unsafe names, CRC errors, local header mismatches, decompression bounds and exact callback lengths. These **28 checks** cover contracts; they do not confirm finished downloads or fabric accuracy.

After the negative acquisition completed, the reviewer independently ran `expand_negatives_v2.py --verify-only`: **120 originals verified without network access**. These contain 40 source pants, 40 shorts and 40 dresses. An additional read-only comparison against all 1,627 prior manifested originals found zero shared canonical source keys and zero shared file hashes. The saved manifest digest matches `12328ba062b158a7c238c4bc6c1b57252f0a16e82001b37911c3c57839f50e3d` in the [acquisition report](../records/acquisitions/2026-10-13-negatives-v2/report.json). The source-selection buckets are not reviewed project labels.

Fabric completion and the combined decoded-pixel/near-duplicate assessment belong to the completed acquisition reports and root combined audit. Do not infer completed fabric image acquisition from the selection plan or these passing tests. Visual review, grouping and explicit admission remain required before another training run.
