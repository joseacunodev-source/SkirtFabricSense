# Bounded fabric archive probe — October 18, 2026

The smallest publisher image archive, [NPCGI_Fxxxx.7z](https://zenodo.org/api/records/20440761/files/NPCGI_Fxxxx.7z/content), contains 8,315,255,946 bytes according to the previously saved [official Zenodo record](https://zenodo.org/records/20440761). A bounded probe received **two exact HTTP206 responses and 72 body bytes total**: bytes0–31 (32-byte 7z signature/start header), then bytes8,315,255,906–8,315,255,945 (40-byte next header). Both start-header and next-header CRC32 checks passed. This verifies those header ranges only; the publisher's whole-archive MD5 has not been verified.

The next header starts with marker `0x17`, indicating an **encoded header**. No filenames, photo-to-item mappings, file counts, compression blocks or solid/non-solid layout have been decoded. Selective extraction therefore remains **unresolved**. HTTP Range support alone does not establish independent-file extraction from a7z archive. The 227 skirt metadata references remain metadata candidates; zero original images and zero training admissions result from this probe.

The [tool](../tools/datasets/probe_fabric_archive.py) uses the Python standard library and chooses the smallest NPCGI image archive from the saved publisher record. It enforces a2MiB body budget, maximum three requests,20-second per-request timeout and a1MiB next-header limit. It rejects HTTP200, redirects, unexpected Content-Range/encoding/length before reading the response body. Reads are explicitly bounded and incomplete/overlong bodies fail. It refuses to overwrite an existing evidence directory. No packages were installed; no7z executable was found through PowerShell command lookup, and no archive extraction was attempted.

Evidence: [actual network report](../records/acquisitions/2026-10-18-fabric-archive-probe/report.json), [execution and hashes](../records/acquisitions/2026-10-18-fabric-archive-probe/execution.json), and [test log](../records/acquisitions/2026-10-18-fabric-archive-probe/tests.log). The start/next header binary files are retained beside the report. Only the public publisher URL is recorded; private redirected/signed URLs are not collected. Eight tests passed, covering ignored Range without body consumption, malformed Content-Range, signatures and CRCs, oversize/invalid next-header offsets, body-length/budget enforcement, and complete synthetic probe/archive selection.

The next bounded feasibility step is parsing the40-byte encoded-header descriptor offline, then declaring a separate byte/request/memory budget before retrieving any referenced header stream. Its compression, size, dictionary requirements and solid-block layout must be established before requesting photo payloads. No8GB full archive request is authorized by the probe tool.

Reproduce the network probe only into a new output directory:

```text
python tools/datasets/probe_fabric_archive.py --output records/acquisitions/fabric-archive-probe-new
python -m unittest tests.test_fabric_archive_probe -v
```
