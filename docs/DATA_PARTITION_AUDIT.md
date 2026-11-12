# Auditing assigned data partitions

The [partition auditor](../tools/audit_dataset_partitions.py) checks metadata for **existing** model input sets. The original split builder performs grouping before assignment; the general record validator checks integrity hashes. This additional check detects semantic contamination when archived inputs or a future versioned release are assembled. It never creates or changes a split, opens an image, or trains a model.

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/audit_dataset_partitions.py --manifest records/experiments/20261021-category-presence-v1/inputs.json
```

Supply each model's assignment set separately. `--manifest` can be repeated for non-overlapping shards of that same set. It accepts JSON arrays, JSON objects with `assignments` or `samples`, and JSONL. Every assigned row requires a sample ID and supported split. Optional `--catalog` files supply original metadata and related protected records, including parents outside the input subset. Catalog rows do not become assignments. Assignment-only manifests need catalog provenance, for example:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B tools/audit_dataset_partitions.py --manifest data/labels/fabric-pilot-v1-splits.json --catalog data/labels/fabric-pilot-v1.jsonl
```

Append `--output records/validation/NEW-UNIQUE-NAME.json` to save a report. Existing output files are never overwritten. A failed check exits with code 1; invalid inputs also exit nonzero. Standard-library Python is sufficient; no packages were installed for this tool.

Recorded parent, group, garment, specimen, session, video, source-item and exact/pixel-hash links form connected components. Transitive components cannot span training, model validation, calibration validation, locked test or protected source holdout roles. File-hash aliases are linked consistently. Source-item identifiers are scoped to their recorded source. Both `source_partition` and `original_split` are inspected; neither can hide conflicting source evidence. Recognized `split` and `project_split` aliases normalize to the same role, including `validation` as model validation, while conflicting declarations fail. Explicit catalog assignments remain frozen: moving a sample or connected catalog member between roles is an error. Unrecognized catalog-only status values are not interpreted as assignments. Unknown or non-training original-source partitions and explicitly protected project records cannot be part of a development component. Missing parents, malformed identity/hash values, duplicate assignment IDs and conflicting original provenance are errors. The source training allowlist is `train`, `training`, `train2020`; introducing another provenance schema requires an explicit implementation and test change, not substituting a training label for an unknown source partition.

The November 4 scoped execution on category-presence-v1 records passed: 538 unique assigned images, 420 training and 118 model validation, with no recorded cross-partition component. These 538 recorded singleton components do not prove 538 distinct garments. The check reads supplied metadata only, so undisclosed relationships, near duplicates and omitted catalogs remain outside its evidence. Label truth, reuse rights, garment identity and actual image integrity require their separate reviews. A `locked_test` membership count never establishes an untouched or accepted test; every report explicitly leaves final-test readiness unestablished.

Nineteen focused adversarial tests pass, covering transitive parent/session leakage, protected originals joined by hash aliases, a held-out catalog member, conflicting source/split aliases, frozen catalog assignment drift, validation aliases, incomplete lineage, duplicate counting, source namespaces and output overwrite protection. Run them with:

```powershell
& 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -B -m unittest tests.test_dataset_partitions -v
```

This is an additional pre-fit and pre-evaluation check under [the training protocol](TRAINING_PLAN.md) and [evaluation protocol](EVALUATION.md). It does not close independent labels, final-garment collection, calibrated length or Raspberry Pi acceptance.
