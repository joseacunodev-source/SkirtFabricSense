"""Prepare versioned source-label and reviewed-appearance manifests without resplitting.

Source manufacturing annotations are auxiliary labels, not project pleating truth.
No dependency installations are required. Outputs must be new paths.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def source_label(row):
    names = {a["name"] for a in row["source_labels"]["attributes"]}
    positive = "pleat" in names
    negative = "no special manufacturing technique" in names
    if positive and negative:
        return None, "conflicting_source_annotations"
    if positive:
        return "source_pleat", "explicit_source_pleat"
    if negative:
        return "source_no_special_manufacturing", "explicit_source_no_special_manufacturing"
    return None, "no_explicit_supported_annotation"


def prepare(rows, split, reviews):
    assignments = {r["sample_id"]: r for r in split["assignments"]}
    if len(assignments) != len(split["assignments"]):
        raise ValueError("Duplicate split sample IDs")
    by_review = {r["sample_id"]: r for r in reviews}
    if len(by_review) != len(reviews):
        raise ValueError("Duplicate review IDs")
    ids = [r["sample_id"] for r in rows]
    if len(ids) != len(set(ids)) or set(by_review) - set(ids):
        raise ValueError("Duplicate sample or unknown review ID")
    queue, auxiliary, appearance = [], [], []
    group_splits = {}
    for row in sorted(rows, key=lambda r: r["sample_id"]):
        sid = row["sample_id"]
        if row["source_partition"] != "train2020" or sid not in assignments:
            raise ValueError("Protected, unknown, or unassigned source sample")
        assignment = assignments[sid]
        if assignment["split"] not in {"development_train", "development_validation"}:
            raise ValueError("Only existing development assignments are allowed")
        group = assignment["group_hash"]
        if group in group_splits and group_splits[group] != assignment["split"]:
            raise ValueError("Connected group crosses split")
        group_splits[group] = assignment["split"]
        review = by_review.get(sid)
        if review and review["image_sha256"] != row["sha256"]:
            raise ValueError("Review image hash mismatch")
        label, reason = source_label(row)
        common = dict(row, split=assignment["split"], group_hash=group)
        queue.append(dict(common, source_auxiliary_label=label, source_mapping_reason=reason,
                          appearance_review=review, review_status="agent_visual_review" if review else "pending",
                          physical_length_label=None, verified_fiber_composition=None))
        # Recorded image problems override source admission; no model predictions are labels.
        blocked = review and review.get("exclude_auxiliary", False)
        if label and not blocked:
            auxiliary.append(dict(common, task="source_manufacturing_annotation_v1", label=label,
                                  label_evidence=reason, label_status="publisher_annotation_not_project_truth"))
        if review and review["appearance_label"] in {"pleated", "non_pleated"} and review["full_skirt_view"]:
            if not review.get("evidence"):
                raise ValueError("Appearance label requires review evidence")
            appearance.append(dict(common, task="reviewed_pleating_appearance_v1", label=review["appearance_label"],
                                   label_evidence=review, label_status="single_agent_visual_review_pending_second_review"))
    return queue, auxiliary, appearance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/skirt_candidates.jsonl"))
    parser.add_argument("--split", type=Path, default=Path("data/manifests/source-skirt-development-splits.json"))
    parser.add_argument("--reviews", type=Path, default=Path("data/labels/skirt-visual-reviews-v1.jsonl"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = read_jsonl(args.manifest)
    split = json.loads(args.split.read_text(encoding="utf-8"))
    queue, auxiliary, appearance = prepare(rows, split, read_jsonl(args.reviews))
    # Never overwrite an earlier label release.
    args.output.mkdir(parents=True, exist_ok=False)
    summaries = {}
    for name, values in [("review-queue", queue), ("source-manufacturing", auxiliary), ("reviewed-appearance", appearance)]:
        path = args.output / (name + ".jsonl")
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in values), encoding="utf-8")
        summaries[name] = {"path": path.as_posix(), "sha256": digest(path), "count": len(values),
                           "split_counts": dict(Counter(r["split"] for r in values)),
                           "label_split_counts": dict(Counter(r["split"] + ":" + str(r.get("label")) for r in values))}
    report = {"schema_version": 1, "date": datetime.now().astimezone().date().isoformat(), "inputs": [
        {"path": p.as_posix(), "sha256": digest(p)} for p in [args.manifest, args.split, args.reviews]],
        "code_sha256": digest(__file__), "outputs": summaries,
        "limits": ["No new original images", "No physical garment identity verification", "No verified fiber or physical length labels",
                   "No final test set created or modified", "Source manufacturing task is auxiliary noisy supervision",
                   "Visual labels are one agent's appearance review, not independent human validation"]}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
