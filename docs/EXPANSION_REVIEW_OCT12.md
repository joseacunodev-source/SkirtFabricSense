# Independent expansion review — October 12, 2026

This review checks acquisition code, metadata and preserved source contracts. It does not certify visual labels or independent physical garment identity. New candidates require visual, grouping and duplicate review before training admission.

## Source limits independently checked

The saved exact DeepFashion InShop partition join contains **131 original-training item groups**: 116 cotton-source, 9 denim-source, 3 leather-source and 3 chiffon-source groups. No item group crosses original training and query/gallery membership. The existing 25-image intake already covers all 15 non-cotton training groups. Therefore, new distinct-item acquisition from this source can expand cotton coverage only; more views of existing rare groups cannot increase independent item counts or resolve class balance.

The preserved DeepFashion-MultiModal terms permit noncommercial research and internal copies at one site within the same organization; they prohibit further dataset copying/publication/distribution. Source appearance labels do not establish fiber composition. Original query/gallery rows must remain outside training expansion.

Fashionpedia annotation licensing does not replace per-image licensing. Intake should select explicit permitted image-license evidence and retain source attribution, without admitting missing-skirt annotations as verified negatives. Existing reviewed and quarantined images must not be silently reintroduced through new IDs or derivatives.

## Review status

The existing bounded ZIP reader checks range lengths, archive boundaries, local member identity, decompression size and CRC. Fabric intake also checks exact HTTP range responses. Newly prepared expansion scripts and actual outputs are reviewed separately below as they become available. No download, installation, or training was performed by this review.
