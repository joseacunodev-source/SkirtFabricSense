"""Create deterministic grouped development splits for explicitly admitted tasks."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

try:
    from .audit_candidates import ROOT, audit, load_records, protected, sha256, write_json
except ImportError:
    from audit_candidates import ROOT, audit, load_records, protected, sha256, write_json


def components(records, report):
    parent = {record["sample_id"]: record["sample_id"] for record in records}

    def find(item):
        while item != parent[item]:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left, right):
        a, b = sorted((find(left), find(right)))
        parent[b] = a

    keys = {}
    for record in records:
        sample_id = record["sample_id"]
        for field in ("group_id", "source_group_id", "garment_id", "specimen_id", "session_id", "video_id", "source_item_id"):
            value = record.get(field)
            if value:
                # Physical IDs/group IDs are project-global; source items are source-scoped.
                key = (field, str(value), record.get("source_id") if field == "source_item_id" else None)
                if key in keys:
                    union(sample_id, keys[key])
                keys[key] = sample_id
        parent_id = record.get("parent_sample_id")
        if parent_id:
            if parent_id not in parent:
                raise ValueError(f"Missing parent {parent_id} for {sample_id}; include parent manifest")
            union(sample_id, parent_id)
    for group in report["exact_duplicate_groups"] + report["pixel_duplicate_groups"]:
        for sample_id in group[1:]:
            union(group[0], sample_id)
    for pair in report["near_duplicate_candidates"]:
        union(*pair["sample_ids"])
    result = {}
    for sample_id in sorted(parent):
        result.setdefault(find(sample_id), []).append(sample_id)
    return list(result.values())


def admission_errors(record, task):
    reasons = []
    if protected(record):
        reasons.append("source_or_project_partition_protected_or_unknown")
    if not record.get("source_id") or not record.get("terms_reference"):
        reasons.append("missing_provenance_or_terms_reference")
    if not (record.get("group_id") or record.get("source_group_id") or record.get("garment_id") or record.get("source_item_id")):
        reasons.append("missing_conservative_grouping")
    label = record.get("project_labels", {}).get(task)
    if not isinstance(label, dict) or label.get("status") != "approved" or not label.get("evidence") or label.get("value") is None:
        reasons.append("task_label_not_explicitly_approved_with_evidence")
    eligibility = record.get("training_eligibility", {}).get(task)
    if not isinstance(eligibility, dict) or eligibility.get("approved") is not True or not eligibility.get("reason"):
        reasons.append("task_training_eligibility_not_explicitly_approved")
    return reasons


def prepare(records, report, task, seed=42, validation_fraction=0.2):
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if report["counts"]["integrity_errors"]:
        raise ValueError("Integrity audit failed; do not create splits")
    by_id = {r["sample_id"]: r for r in records}
    assignments, excluded, groups = [], [], components(records, report)
    eligible_groups = 0
    for members in sorted(groups):
        group_hash = hashlib.sha256("\n".join(members).encode()).hexdigest()
        group_protected = any(protected(by_id[item]) for item in members)
        group_assignments = []
        for item in members:
            reasons = admission_errors(by_id[item], task)
            if group_protected:
                reasons.append("related_to_protected_or_unknown_source_partition")
            if reasons:
                excluded.append({"sample_id": item, "reasons": sorted(set(reasons)), "group_hash": group_hash})
            else:
                label = by_id[item]["project_labels"][task]["value"]
                group_assignments.append({"sample_id": item, "label": label, "group_hash": group_hash})
        if group_assignments:
            eligible_groups += 1
            score = int(hashlib.sha256(f"{seed}:{group_hash}".encode()).hexdigest(), 16) / 2**256
            split = "development_validation" if score < validation_fraction else "development_train"
            assignments.extend(dict(item, split=split) for item in group_assignments)
    counts = Counter(item["split"] for item in assignments)
    label_counts = {}
    for item in assignments:
        label_counts.setdefault(item["split"], Counter())[json.dumps(item["label"], sort_keys=True)] += 1
    warnings = ["Development only: source groups are not verified independent physical garments.",
                "Hash assignment preserves groups but is not stratified; review per-class coverage before training.",
                "Near-duplicate candidates are grouped conservatively, including possible false positives.",
                "Supply all existing holdout manifests for cross-source leakage checks; unseen data cannot be checked."]
    if not counts.get("development_train") or not counts.get("development_validation"):
        warnings.append("One or both development partitions are empty; this release is not ready for training/evaluation.")
    distinct_labels = {json.dumps(item["label"], sort_keys=True) for item in assignments}
    if len(distinct_labels) < 2:
        warnings.append("Fewer than two labels: not a complete supervised classification dataset.")
    return {"schema_version": 1, "task": task, "seed": seed, "validation_fraction": validation_fraction,
            "purpose": "auxiliary_or_project_development_only_no_final_device_test",
            "assignments": sorted(assignments, key=lambda r: r["sample_id"]),
            "excluded": sorted(excluded, key=lambda r: r["sample_id"]),
            "counts": {"admitted_records": len(assignments), "excluded_records": len(excluded),
                       "conservative_components": len(groups), "admitted_components": eligible_groups,
                       "partitions": dict(counts), "labels_by_partition": label_counts},
            "near_distance": report["near_distance"], "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--task", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-fraction", type=float, default=0.2)
    parser.add_argument("--near-distance", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = load_records(args.manifest)
    report = audit(records, args.root, args.near_distance)
    result = prepare(records, report, args.task, args.seed, args.validation_fraction)
    result["input_manifests"] = [{"path": str(p), "sha256": sha256(p)} for p in args.manifest]
    result["source_hashes"] = {p.name: sha256(p) for p in (Path(__file__), Path(__file__).with_name("audit_candidates.py"))}
    write_json(args.output, result)
    print(json.dumps({"counts": result["counts"], "split_manifest_sha256": sha256(args.output)}))


if __name__ == "__main__":
    main()
