"""Audit presentation coverage without changing the frozen training release.

Free-text pleating notes are retained, never mined as presentation truth. An
optional visual-review overlay binds explicit observations to exact originals.
"""
import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_report(path, report):
    """Create a new evidence record; existing historical reports are immutable."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")


def verify_contact_reviews(reviews, indices, root):
    """Bind sheet observations to their source originals and actual sheet bytes."""
    lookup = {}
    for entry in indices:
        sid = entry['sample_id']
        if sid in lookup:
            raise ValueError('duplicate inspection index identity')
        lookup[sid] = entry
    for review in reviews:
        if review['review_method'] != 'contact_sheet_visual_inspection':
            continue
        entry = lookup.get(review['sample_id'])
        if not entry or any(review.get(k) != entry[k] for k in
                            ('inspection_sheet', 'sheet_position', 'sheet_sha256', 'original_path')):
            raise ValueError('sheet review index mismatch')
        if review['image_sha256'] != entry['sha256']:
            raise ValueError('sheet original hash mismatch')
        path = (root / entry['inspection_sheet']).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file() or digest(path) != entry['sheet_sha256']:
            raise ValueError('missing or changed inspection sheet')


def audit(rows, assignments, reviews=(), audit_date=None):
    audit_date = audit_date or datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    if not isinstance(audit_date, str) or date.fromisoformat(audit_date).isoformat() != audit_date:
        raise ValueError("audit_date must be ISO YYYY-MM-DD")
    source = {}
    for row in rows:
        sid = row["sample_id"]
        if sid in source:
            raise ValueError("duplicate source sample")
        source[sid] = row
    split_map = {}
    for row in assignments:
        sid = row["sample_id"]
        if sid in split_map:
            raise ValueError("duplicate split assignment")
        split_map[sid] = row
    overlay = {}
    for review in reviews:
        sid = review["sample_id"]
        if sid not in source or sid in overlay:
            raise ValueError("unknown or duplicate review sample")
        if review.get("image_sha256") != source[sid]["sha256"]:
            raise ValueError("review image hash mismatch")
        if review.get("presentation") not in {"worn", "hanging", "held", "mannequin", "unknown"}:
            raise ValueError("invalid presentation")
        if review.get("review_method") not in {"original_image_visual_inspection", "contact_sheet_visual_inspection"} or any(not isinstance(review.get(k), str) or not review[k].strip() for k in ("reviewer", "evidence")):
            raise ValueError("missing explicit visual review evidence")
        if review['review_method'] == 'contact_sheet_visual_inspection' and (
                type(review.get('sheet_position')) is not int or not 1 <= review['sheet_position'] <= 12
                or not isinstance(review.get('inspection_sheet'), str)
                or not isinstance(review.get('sheet_sha256'), str) or len(review['sheet_sha256']) != 64):
            raise ValueError('missing sheet review provenance')
        if any(type(review.get(key)) is not bool for key in ["waistband_visible", "hem_visible", "feet_and_support_surface_visible"]):
            raise ValueError("visibility must be explicit boolean observations")
        overlay[sid] = review
    result = []
    groups = {}
    for sid, row in source.items():
        assignment = split_map.get(sid, {})
        if assignment.get("split") != row["split"] or assignment.get("group_hash") != row["group_hash"]:
            raise ValueError("frozen split/group mismatch")
        group = row["group_hash"]
        if group in groups and groups[group] != row["split"]:
            raise ValueError("group crosses split")
        groups[group] = row["split"]
        review = overlay.get(sid)
        result.append({
            "sample_id": sid, "original_path": row["original_path"], "sha256": row["sha256"],
            "split": row["split"], "group_hash": group, "label": row["label"],
            "presentation": review["presentation"] if review else "unknown",
            "presentation_evidence": review,
            "prior_pleating_evidence": row.get("label_evidence"),
            "geometry_calibrated": False,
            "new_training_admission": False,
        })
    coverage = {}
    for split in sorted({r["split"] for r in result}):
        subset = [r for r in result if r["split"] == split]
        coverage[split] = {"images": len(subset), "presentation_counts": dict(Counter(r["presentation"] for r in subset)),
                           "label_counts": dict(Counter(r["label"] for r in subset))}
    return {"schema_version": 1, "date_asia_manila": audit_date, "source_images": len(result),
            "reviewed_originals": sum(r['review_method'] == 'original_image_visual_inspection' for r in overlay.values()),
            "reviewed_via_sheet": sum(r['review_method'] == 'contact_sheet_visual_inspection' for r in overlay.values()),
            "reviewed_samples": len(overlay), "unknown_presentation": sum(r["presentation"] == "unknown" for r in result),
            "by_split": coverage, "verified_independent_garments": None, "calibrated_geometry_examples": 0,
            "new_training_admissions": 0,
            "pending_original_review_sample_ids": [r["sample_id"] for r in result if r["presentation_evidence"] is None],
            "rows": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/labels/skirt-baseline-v1.jsonl"))
    parser.add_argument("--splits", type=Path, default=Path("data/manifests/source-skirt-development-splits.json"))
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--audit-date", help="ISO date; defaults to current Asia/Manila date")
    parser.add_argument('--sheet-index', type=Path, action='append', default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reviews = jsonl(args.reviews) if args.reviews else []
    indices = [row for path in args.sheet_index for row in json.loads(path.read_text(encoding='utf-8'))]
    verify_contact_reviews(reviews, indices, Path.cwd())
    report = audit(jsonl(args.manifest), json.loads(args.splits.read_text())["assignments"], reviews, audit_date=args.audit_date)
    # Check every original so a matching metadata hash cannot conceal a replaced file.
    for row in report["rows"]:
        if digest(row["original_path"]) != row["sha256"]:
            raise ValueError("original image hash mismatch: " + row["sample_id"])
    report["inputs"] = {key: {"path": path.as_posix(), "sha256": digest(path)} for key, path in
                        [("manifest", args.manifest), ("splits", args.splits), ("reviews", args.reviews), ("tool", Path(__file__))] if path}
    report['sheet_indices'] = [{'path': p.as_posix(), 'sha256': digest(p)} for p in args.sheet_index]
    write_report(args.output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in {"rows", "inputs", "pending_original_review_sample_ids"}}))


if __name__ == "__main__":
    main()
