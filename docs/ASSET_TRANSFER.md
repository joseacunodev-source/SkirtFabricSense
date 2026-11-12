# Moving datasets and model assets between computers

The Git repository contains code, documentation, labels, split manifests and experiment
records. Large model files, acquired images and raw acquisition snapshots stay outside
Git. A clone alone therefore does not reproduce the current trained application or a
complete dataset. This guide covers their separate, private transfer.

`config/project-assets-v2.json` records relative paths, byte sizes and SHA-256 hashes
of the current eligible local assets. Its file count describes files,
not independent garments or newly acquired images. The manifest does not grant rights
to publish the underlying files. Preserve the actual source terms recorded in
`data/registry.json` and `docs/DATASETS.md`; use an authorized private transfer location.
Do not upload this asset bundle to a public release or repository.

Version 2 supersedes the initial v1 migration inventory. The v1 manifest and private
ZIP omitted `data/external/dtd/dtd-r1.0.1-labels.tar.gz`, a required annotations archive
referenced by `data/external/seed/acquisition_manifest.json`. Passing verification
against v1 checks its listed files only and does not close this missing-input gap.
The published v1 manifest remains unchanged for historical integrity. Use a v2 bundle
for a complete transfer of the currently inventoried project inputs; a v1 ZIP cannot
be restored against the v2 manifest because exact membership is required.

## Check the source computer

Run from the repository root with Python 3.10 or newer. The transfer tool uses the
Python standard library; inventory additionally requires Git. No package installation
or internet access is needed for these commands.

```powershell
python tools/project_assets.py verify --manifest config/project-assets-v2.json
```

Continue only when verification reports `"status": "passed"`. Missing or mismatched
paths identify an incomplete copy or changes since that manifest was frozen. Preserve
the old manifest and investigate the difference before making a new version. Verification
does not execute a model, measure prediction accuracy or establish Raspberry Pi support.

## Create the private bundle

Choose a location outside the repository with enough free space for the archive.
The following command is an example; replace the drive/path for your computer.

```powershell
python tools/project_assets.py pack --manifest config/project-assets-v2.json --output D:/Backups/SkirtFabricSense-assets-v2.zip
```

Packing verifies the source first, streams each file with a size/hash check, and reports
the finished archive's byte size and SHA-256. Save that output alongside the private
backup so its recipient can also check the archive itself. An existing archive is
never overwritten. Copy the manifest from the same Git revision with the archive.
Packing does not upload anything or encrypt the ZIP; use a trusted private storage or
transfer service appropriate for these files. A v1 private bundle exists as historical
transfer evidence; its successful packaging does not establish a complete v2 restore.

## Restore on the other computer

Clone the repository, check out the source revision that supplied the manifest, and
place the private ZIP somewhere accessible. From the cloned repository root run:

```powershell
python tools/project_assets.py restore D:/Backups/SkirtFabricSense-assets-v2.zip --manifest config/project-assets-v2.json --destination .
python tools/project_assets.py verify --manifest config/project-assets-v2.json
```

Restore checks exact archive membership, sizes and hashes before copying any files
into the destination. It rejects traversal paths, duplicate or case-colliding names,
links/junctions, encrypted entries, unsupported compression and extra files. Existing
matching files are retained. An existing differing file stops the restore; preserve
and resolve that conflict explicitly instead of deleting it automatically.

The tool stages all expanded files in the operating system's temporary directory,
then copies missing files into the destination. Allow free space for the uncompressed
manifest total in that temporary location and for missing files at the destination,
in addition to the ZIP itself. A disk or process failure during copying can leave an
incomplete newly created file; rerun verification and preserve/resolve it before retrying.
Do not edit the source or destination assets while transfer commands are running.

After asset verification, follow `docs/GITHUB_WORKFLOW.md` to recreate the Python
environment from the recorded requirements and run the project checks. Environments
are recreated on each computer. Windows GPU/WSL and Raspberry Pi environments remain
separate, and a restored desktop model still needs target-device runtime verification.

## Inventory policy and later checkpoints

Inventory is deliberately limited to files that Git currently ignores inside these
project-relative families:

- `data/external/`, `data/raw/`, `data/processed/`, `data/cache/`, `data/candidates/`;
- `artifacts/` and `output/geometry-review/`;
- ignored user-provided reference files inside `docs/references/`;
- ignored image/model/array binaries inside `records/`;
- ignored raw snapshots inside `records/acquisitions/`, including JSON/text responses.

Project metadata retained by Git is not copied again into the asset bundle. The policy
excludes symlinks/junctions, virtual environments, `node_modules`, Python caches,
temporary directories, known credential filenames/key extensions, and archive
extensions (`.zip`, `.7z`, `.rar`, `.tar`, `.gz`, `.bz2`, `.xz`) to prevent recursive
backup inclusion. The only archive exception is the exact required source path
`data/external/dtd/dtd-r1.0.1-labels.tar.gz` (188,651 bytes; SHA-256
`d95422715cd7a0d76cc34235b85b4b14002d6c1687e68d5aa3b3517651da57e1`).
The transfer copies its frozen bytes without extracting them. Other source archives
and generated ZIPs remain excluded. Review and document any future exception before
relying on a newer manifest.
Path filtering is not a scan of arbitrary file contents for secrets; review new
acquisition material before choosing to transfer it.

External WSL training-run directories, system installations, browser sessions and
files outside these families are not covered. A passed asset verification is not a
whole-computer backup or a guarantee that every external training checkpoint exists.

After intentional asset changes, create a new manifest filename, review its counts and
scope, verify it, and commit that new manifest with the matching project records:

```powershell
python tools/project_assets.py inventory --output config/project-assets-v3.json
python tools/project_assets.py verify --manifest config/project-assets-v3.json
```

Inventory refuses to overwrite an existing manifest. Keep older versions for matching
older private bundles. No assets are downloaded, relabelled or changed by inventory.
Do not treat HTTP error-response files or derived crops as new dataset specimens.
