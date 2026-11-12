# Fabric archive index recovery — October 18, 2026

The smallest NPCGI publisher archive can be selectively read without retrieving its full 8,315,255,946 bytes. This conclusion is specific to the verified layout of `NPCGI_Fxxxx.7z` in [source version 1.1](https://zenodo.org/records/20440761); it is not a general claim about 7z archives.

The original [network report](../records/acquisitions/2026-10-18-fabric-archive-index/report.json) records one exact HTTP206 body of 23,592 bytes at archive offsets 8,315,232,314–8,315,255,905. The encoded header decodes to 97,602 bytes and passes the archive's CRC32. Its SHA256 is `3ad473ff52925123210368b13c483a3e05f8a9a6f29757b226617479be212d5d`. Initial parsing stopped because alignment-padding FilesInfo properties recur. This stopped report is preserved.

The parser now permits repeated dummy alignment padding while still rejecting repeated substantive properties. [Offline recovery](../records/acquisitions/2026-10-18-fabric-archive-index/parsed/report.json) reused the acquired header stream, verified it again and decoded **2,066 filenames and 2,066 independent Copy streams, with zero solid folders**. Every packed stream size equals its unpacked size. Offsets are bounded below the encoded header. Copy streams need no image decompression; each selected image still requires its own size and archive CRC check after retrieval. The publisher whole-archive checksum has not been verified.

Exact filename stems join **25 of the 27 Trondheim skirt metadata IDs**. No fuzzy identity mapping is used; unmatched source items remain unmatched. Matched payloads range from 3,498,421 to 4,731,172 bytes. The [filename joins](../records/acquisitions/2026-10-18-fabric-archive-index/parsed/filename-joins.json) and [archive stream index](../records/acquisitions/2026-10-18-fabric-archive-index/parsed/archive-index.json) preserve names, offsets, sizes and CRCs. Header acquisition and indexing downloaded zero photographs and admitted zero training samples.

Nine parser tests pass, including integer decoding, CRC/decode limits, dictionary bounds, unsafe/duplicate filenames, exact ID joins, solid substreams, repeated padding and payload/header range separation. [Recovery execution evidence](../records/acquisitions/2026-10-18-fabric-archive-index/recovery-execution.json) binds current code and acquired files to the checks. No packages were installed.

The separately bounded five-item [NPCGI pilot](NPCGI_PILOT.md) uses only verified independent Copy ranges. Its acquisition, inspections and limitations are separate from this header-only result.

Offline reproduction into a new evidence directory:

```text
python tools/datasets/inspect_fabric_7z_header.py --packed-header records/acquisitions/2026-10-18-fabric-archive-index/packed-header.bin --output records/acquisitions/fabric-archive-index-offline-new
python -m unittest tests.test_fabric_7z_header -v
```
