# GitHub setup and verified migration - November 12, 2026

The project is published on [joseacunodev-source/SkirtFabricSense](https://github.com/joseacunodev-source/SkirtFabricSense), on `main`. The repository was already public; its visibility was retained. Its description, six project topics, README with an actual UI screenshot, contribution guide, issue templates and software-check workflow are configured.

The selected application remains station-v9 / research-v14, with v8 rollback. This repository setup did not train models, acquire images, approve labels or verify camera/Pi behavior. The current [task board](TASK_BOARD.md) preserves those remaining tasks.

## Verification

| Check | Actual result |
|---|---|
| Fresh GitHub clone and fast-forward pulls | Successful; source revision `780120fb82976e35adfa83f2250cecb61b18f369` checked before this documentation closeout |
| Exact checkout bytes | All 960 tracked files matched their Git blob identities; no line-ending conversion differences |
| Software contracts in that clone | 145 passed, zero failures/errors/skips; existing source-machine Python 3.12.14 and Pillow 13.0.0 |
| Private v2 bundle restore | All 2,804 files restored; no missing files or hash mismatches; 1,800,977,570 uncompressed bytes |
| Restored-clone record validation | Passed: 932 local links, 4,905 parsed JSON records, 21 typed raw failures, 33 acquired seed artifacts, 1,920 expansion-image hashes and 325 continuation references |
| Hosted GitHub Actions | [Source/migration checks passed](https://github.com/joseacunodev-source/SkirtFabricSense/actions/runs/43146578893); [CI provenance helper and checks passed](https://github.com/joseacunodev-source/SkirtFabricSense/actions/runs/43147191365) |

Evidence: [checkout bytes](../records/validation/2026-11-12-github-clone-bytes-final.json), [clone tests](../records/validation/2026-11-12-github-clone-software-tests.json), [restored assets](../records/backups/2026-11-12-project-assets-v2-restored.json), [full restored-clone validation](../records/validation/2026-11-12-github-restored-clone-records-final.json), and [hosted job/step conclusions](../records/validation/2026-11-12-github-hosted-checks.json).

The first migration checks found two omitted dependencies. The v1 asset policy excluded a required DTD annotations archive; the unchanged v1 manifest is retained, and v2 adds that exact archive. The first full cloned-record check also found the curated progress-screenshot ZIP missing. Its 11 members exactly match already tracked project screenshots/code/captions, so a narrow Git exception retains this small report archive. The [initial failure](../records/validation/2026-11-12-github-restored-clone-records.json) is preserved alongside the passing final check.

## Continue elsewhere

Clone the repository and read [the GitHub workflow guide](GITHUB_WORKFLOW.md). Push reviewed changes before switching computers; pull before starting work. On a different computer, use that checkout's actual root instead of copying the source laptop's historical Windows/WSL absolute paths.

Code, project documentation, grouped manifests, provenance and experiment summaries are in Git. Acquired photographs, trained payloads, raw acquisition snapshots and the user-provided reference image transfer privately. The [current asset manifest](../config/project-assets-v2.json) is an integrity inventory, not a downloader or a redistribution license.

The prepared private ZIP is `SkirtFabricSense-assets-v2.zip`, located in the source computer's `Downloads/SkirtFabricSense-private-transfer/` folder with its README, manifest copy and SHA-256 file. It is **1,177,033,067 bytes**, SHA-256 `ccbc61ee115f0a9196aa2b92ef7d050c5e48bc2122ea1c9b20e5b56dfdc81444`. Copy it through private storage or a drive, then follow [the restore instructions](ASSET_TRANSFER.md). It has not been uploaded to GitHub or a cloud storage provider.

Virtual environments, GPU drivers, external WSL run folders and system installations are not in the archive. Recreate the needed environment from the separate recorded requirements; the fresh-clone check used the existing source-machine interpreter and does not establish another computer's GPU or Pi compatibility.

## Dependency evidence

No local package was installed or changed for this setup. Hosted CI installs the pinned test-only Pillow version. Its [CI-only helper](../tools/record_ci_environment.py) verifies the installed version and an image operation, runs the environment collector, appends the actual event to the runner-local installation ledger, and prints the event and snapshot in grouped job logs. These are ephemeral runner records; GitHub log retention applies, and they are not automatically committed to this repository. Preserve relevant logs separately when permanent environment evidence is needed.

Git authentication used the existing Git Credential Manager/browser flow. No credential was placed in the repository, remote URL or project records. Public upload candidates were reviewed against the ignore policy and checked for high-confidence credential/private-key/signed-URL patterns; this check is a limited screening measure rather than a guarantee.
