# Background acquisition evidence recovery

The November 4 Commons attempt completed with **zero photos, zero labels and zero training admissions**. Twenty-one failed requests returned HTTP 429 with `Content-Type: text/plain`, but the downloader retained those bodies under the requested metadata `.json` filenames. They are transport evidence, not malformed source metadata to repair by inventing JSON.

The [recovery index](../records/recoveries/raw-http-responses-v1.json) explicitly identifies these 21 responses. Original files, request logs, acquisition outcomes and their historical hashes remain unchanged. Byte-identical `.response.txt` copies are retained under [typed HTTP body copies](../records/recoveries/http-bodies-20261111). Nothing was downloaded again, relabelled or admitted. The registered image collection remains 1,932 originals.

## Validation behavior

[raw_http_records.py](../tools/raw_http_records.py) checks each indexed body against its exact request-log entry, HTTP status, content type, size, original acquisition artifact and SHA-256. It also verifies the typed text copy. Original paths must be canonical local acquisition paths; duplicate entries, changed bytes, missing sources, successful responses and genuine JSON are rejected. A missing index grants no exception; an invalid index grants none and is reported as an error.

[validate_records.py](../tools/validate_records.py) continues to parse ordinary JSON/JSONL. Only these explicitly verified raw bodies are counted separately under `raw_http_failure_bodies_verified`; they are not reported as successfully parsed JSON. This is a typed treatment of retained failed-response evidence, not a folder-wide parse-error exclusion. The immutable acquisition still records its original download failures.

The index is pinned by the current continuation/registry records. Local hashes establish consistency; a person with write access to every source and index could rewrite them together. Preserve historical checkpoints and backups. The recovery does not authenticate source servers or authorize reuse of photographs.

## Commands

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/raw_http_records.py
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest tests.test_raw_http_records tests.test_continuation_records -v
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/validate_records.py
```

Creation with `--create` was performed once and refuses an existing index or typed-copy output. Do not repeat it to overwrite evidence. Fourteen dedicated recovery tests cover byte/source tampering, duplicate entries, path escape, successful/JSON response rejection, malformed index structures, overwrite protection and the actual record-validator integration. Three existing continuation-reference tests also passed. The integration check confirms that unclassified malformed JSON still fails, and a changed indexed body removes all recovery exemptions and fails validation. A missing portable skill now reports an integrity error rather than crashing the validator.

## Future intake

Use a new versioned acquisition directory and predeclared request/size budget for any future attempt. Classify failed response bodies by their actual media type at capture time. Respect rate limits and preserve failure records; do not bypass a source's request controls or silently substitute thumbnails. Acquisition candidates still need rights, grouping and full-original review before admission. Internet backgrounds cannot establish deployment-camera accuracy.
