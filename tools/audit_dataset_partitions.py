"""Read-only metadata check of already assigned dataset partitions.

This does not create splits, open images, certify labels/rights, or authorize a fit.
Supply the complete related catalog, including protected records, for useful checks.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TRAIN_SOURCE_PARTITIONS = {"train", "training", "train2020"}
SPLIT_ROLES = {
    "train": "training", "training": "training", "development_train": "training",
    "validation": "model_validation", "val": "model_validation",
    "development_validation": "model_validation", "model_validation": "model_validation",
    "calibration_validation": "calibration_validation", "threshold_validation": "calibration_validation",
    "test": "locked_test", "final_test": "locked_test", "locked_test": "locked_test",
    "external_holdout_sanity": "protected_source_holdout",
}
DEVELOPMENT_ROLES = {"training", "model_validation", "calibration_validation"}
IDENTITY_FIELDS = ("group_hash", "group_id", "source_group_id", "garment_id",
                   "specimen_id", "session_id", "video_id")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_rows(path):
    """Accept current JSONL, array, assignments-object and samples-object records."""
    path = Path(path)
    content = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".jsonl":
        value = [json.loads(line) for line in content.splitlines() if line.strip()]
    else:
        value = json.loads(content)
        if isinstance(value, dict):
            keys = [key for key in ("assignments", "samples") if key in value]
            if len(keys) != 1:
                raise ValueError(f"Expected one assignments/samples array: {path}")
            value = value[keys[0]]
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"Expected an array of records: {path}")
    return value


def audit_partitions(assignments, catalog=()):
    """Audit recorded connections transitively; absent connections are not inferred."""
    issues = []

    def issue(code, sample_ids, **details):
        issues.append(dict(code=code, sample_ids=sorted(set(sample_ids)), **details))

    versions = defaultdict(list)
    assignment_ids = []
    roles = defaultdict(set)
    declared_roles = defaultdict(set)
    for origin, records in (("assignment", assignments), ("catalog", catalog)):
        for index, row in enumerate(records):
            sample_id = row.get("sample_id")
            if not isinstance(sample_id, str) or not sample_id.strip():
                raise ValueError(f"Missing sample_id in {origin} row {index}")
            versions[sample_id].append(row)
            row_roles = set()
            declared_splits = [(field, row[field]) for field in ("split", "project_split")
                               if row.get(field) is not None]
            for field, value in declared_splits:
                if isinstance(value, str) and value in SPLIT_ROLES:
                    row_roles.add(SPLIT_ROLES[value])
                elif origin == "assignment":
                    issue("unknown_assignment_split", [sample_id], field=field, split=value)
            declared_roles[sample_id].update(row_roles)
            if len(row_roles) > 1:
                issue("conflicting_split_aliases", [sample_id], roles=sorted(row_roles))
            if origin == "assignment":
                assignment_ids.append(sample_id)
                if not declared_splits:
                    issue("unknown_assignment_split", [sample_id], split=None)
                roles[sample_id].update(row_roles)
    if not assignment_ids:
        issue("empty_assignment_manifest", [])
    for sample_id, count in Counter(assignment_ids).items():
        if count > 1:
            issue("duplicate_assignment_sample_id", [sample_id], rows=count)

    parent = {sample_id: sample_id for sample_id in versions}

    def find(item):
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left, right):
        a, b = sorted((find(left), find(right)))
        parent[b] = a

    key_owner = {}
    source_values = defaultdict(set)
    protected_project = set()
    for sample_id, records in sorted(versions.items()):
        hashes = set()
        for row in records:
            keys = []
            for field in IDENTITY_FIELDS:
                value = row.get(field)
                if value is not None and value != "":
                    if not isinstance(value, str):
                        issue("invalid_identity_value", [sample_id], field=field)
                    else:
                        keys.append((field, value))
            for field in ("sha256", "image_sha256", "pixel_sha256"):
                value = row.get(field)
                if value is not None:
                    if not isinstance(value, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", value):
                        issue("invalid_hash", [sample_id], field=field)
                    else:
                        namespace = "pixel_sha256" if field == "pixel_sha256" else "file_sha256"
                        keys.append((namespace, value.lower()))
                        if namespace == "file_sha256":
                            hashes.add(value.lower())
            item = row.get("source_item_id")
            if item is not None and str(item):
                source = row.get("source_id")
                if isinstance(source, str) and source:
                    keys.append(("source_item_id", source, str(item)))
                else:
                    issue("source_item_missing_namespace", [sample_id])
            for key in keys:
                if key in key_owner:
                    union(sample_id, key_owner[key])
                else:
                    key_owner[key] = sample_id
            parent_id = row.get("parent_sample_id")
            if parent_id:
                if not isinstance(parent_id, str) or parent_id not in versions:
                    issue("missing_parent_record", [sample_id], parent_sample_id=parent_id)
                elif parent_id == sample_id:
                    issue("self_parent_reference", [sample_id])
                else:
                    union(sample_id, parent_id)
            for field in ("source_partition", "original_split"):
                source_partition = row.get(field)
                if isinstance(source_partition, str) and source_partition.strip():
                    source_values[sample_id].add(source_partition.strip().lower())
                elif source_partition is not None:
                    issue("invalid_source_partition", [sample_id], field=field)
        if declared_roles[sample_id].intersection({"locked_test", "protected_source_holdout"}):
            protected_project.add(sample_id)
        if len(declared_roles[sample_id]) > 1:
            issue("conflicting_project_partition_declarations", [sample_id], roles=sorted(declared_roles[sample_id]))
        if len(hashes) > 1:
            issue("conflicting_sample_file_hashes", [sample_id])
        if len(source_values[sample_id]) > 1:
            issue("conflicting_source_partitions", [sample_id], partitions=sorted(source_values[sample_id]))

    components = defaultdict(list)
    for sample_id in sorted(versions):
        components[find(sample_id)].append(sample_id)
    assigned_components = []
    for members in components.values():
        assigned = [sample_id for sample_id in members if sample_id in roles]
        if not assigned:
            continue
        component_roles = sorted({role for sample_id in assigned for role in roles[sample_id]})
        component_declared_roles = sorted({role for sample_id in members for role in declared_roles[sample_id]})
        assigned_components.append({"members": members, "assigned_members": assigned, "roles": component_roles})
        if len(component_declared_roles) > 1:
            issue("connected_component_crosses_partitions", members, roles=component_declared_roles)
        if DEVELOPMENT_ROLES.intersection(component_roles):
            forbidden = [sample_id for sample_id in members
                         if source_values[sample_id] - TRAIN_SOURCE_PARTITIONS or sample_id in protected_project]
            unknown = [sample_id for sample_id in members if not source_values[sample_id]]
            if forbidden:
                issue("development_component_contains_protected_or_unknown_source", members, flagged_members=forbidden)
            if unknown:
                issue("development_component_missing_source_partition", members, flagged_members=unknown)
    role_counts = Counter(role for values in roles.values() for role in values)
    return {
        "schema_version": 1,
        "status": "failed" if issues else "passed_metadata_checks",
        "assignment_rows": len(assignments),
        "unique_assigned_samples": len(set(assignment_ids)),
        "catalog_and_assignment_unique_samples": len(versions),
        "unique_sample_counts_by_role": dict(sorted(role_counts.items())),
        "assigned_connected_components": len(assigned_components),
        "components_by_role": dict(sorted(Counter(role for comp in assigned_components for role in comp["roles"]).items())),
        "issues": issues,
        "final_test_readiness": "not_established_by_metadata_audit",
        "limits": [
            "Only supplied metadata connections checked; omitted catalogs and unrecorded near-duplicates cannot be detected.",
            "No images opened or file hashes recomputed; this complements, not replaces, image integrity and duplicate audits.",
            "Source groups are not verified physical garments; no label, license, unseen-test, camera or Pi acceptance inferred.",
            "Each model input set must be audited separately; do not combine historic models into one split.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--catalog", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_partitions([row for path in args.manifest for row in load_rows(path)],
                              [row for path in args.catalog for row in load_rows(path)])
    result["recorded_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["inputs"] = [{"path": str(path), "sha256": digest(path), "role": role}
                        for role, paths in (("assignments", args.manifest), ("catalog", args.catalog)) for path in paths]
    result["source"] = {"path": "tools/audit_dataset_partitions.py", "sha256": digest(__file__)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
    print(json.dumps(result, indent=2))
    return int(bool(result["issues"]))


if __name__ == "__main__":
    raise SystemExit(main())
