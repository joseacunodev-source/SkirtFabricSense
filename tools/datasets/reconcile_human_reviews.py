"""Read-only integrity and disagreement audit; never grants training approval."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))
from app.review import ReviewStore


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(root: Path) -> dict:
    """Validate immutable inputs and all event history without changing either."""
    store = ReviewStore(root)
    manifest_bytes = store.manifest.read_bytes()
    split_bytes = store.splits.read_bytes()
    event_bytes = store.events.read_bytes() if store.events.exists() else b""
    manifest_hash, split_hash = sha(manifest_bytes), sha(split_bytes)
    if (manifest_hash, split_hash) != (store._manifest_hash, store._split_hash):
        raise ValueError("Inputs changed during initialization")
    assignments = store._assignments
    if set(assignments) != set(store._records):
        raise ValueError("Frozen assignments and candidate IDs differ")
    groups = defaultdict(set)
    for item in assignments.values():
        if not isinstance(item.get("group_hash"), str) or not item["group_hash"]:
            raise ValueError("Missing frozen group identity")
        groups[item["group_hash"]].add(item["split"])
    if any(len(splits) != 1 for splits in groups.values()):
        raise ValueError("Frozen group crosses splits")
    bad_images = {}
    for sid in store._records:
        try:
            store.image_path(sid)
        except ValueError as exc:
            bad_images[sid] = str(exc)
    history = defaultdict(list)
    records, seen = [], set()
    for line_number, raw in enumerate(event_bytes.decode("utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        errors = []
        try:
            event = json.loads(raw)
            if not isinstance(event, dict):
                raise ValueError("Event must be an object")
        except (ValueError, json.JSONDecodeError) as exc:
            records.append({"line": line_number, "raw": raw, "errors": [str(exc)]})
            continue
        payload = {key: value for key, value in event.items() if key != "event_sha256"}
        expected = sha(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        if expected != event.get("event_sha256"):
            errors.append("event_hash_mismatch")
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            errors.append("invalid_event_id")
        elif event_id in seen:
            errors.append("duplicate_event_id")
        else:
            seen.add(event_id)
        sid = event.get("sample_id")
        row = store._records.get(sid) if isinstance(sid, str) else None
        if row is None:
            errors.append("unknown_or_protected_sample")
        else:
            checks = {
                "image_sha256": row["sha256"], "source_partition": "train2020",
                "source_manifest_sha256": manifest_hash, "split_manifest_sha256": split_hash,
                "split": assignments[sid]["split"], "group_hash": assignments[sid]["group_hash"],
                "status": "pending_reconciliation", "reviewer_identity": "self_reported_not_authenticated",
            }
            errors.extend(key + "_mismatch" for key, value in checks.items() if event.get(key) != value)
            if sid in bad_images:
                errors.append("original_image_hash_mismatch")
        if type(event.get("schema_version")) is not int or event["schema_version"] != 1:
            errors.append("unsupported_schema")
        if event.get("training_approved") is not False:
            errors.append("training_approval_not_allowed")
        if event.get("appearance_label") not in ("pleated", "non_pleated", "unknown"):
            errors.append("invalid_appearance_label")
        if type(event.get("full_skirt_view")) is not bool:
            errors.append("invalid_full_skirt_view")
        for key, limit in (("reviewer", 100), ("evidence", 4000)):
            value = event.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                errors.append("invalid_" + key)
        try:
            if datetime.fromisoformat(event.get("recorded_at_utc", "")).utcoffset() is None:
                raise ValueError()
        except (ValueError, TypeError):
            errors.append("invalid_timestamp")
        records.append({"line": line_number, "event": event, "errors": errors})
        if not errors:
            history[sid].append(event)
    summaries = []
    for sid, events in sorted(history.items()):
        reviewers = defaultdict(list)
        for event in events:
            reviewers[event["reviewer"]].append(event)
        opinions = {(e["appearance_label"], e["full_skirt_view"]) for e in events}
        summaries.append({"sample_id": sid, "split": assignments[sid]["split"],
                          "event_ids": [e["event_id"] for e in events],
                          "reviewers_with_revisions": {r: [e["event_id"] for e in es]
                                                       for r, es in reviewers.items() if len(es) > 1},
                          "historical_disagreement": len(opinions) > 1,
                          "status": "pending_human_reconciliation", "training_approved": False})
    if (store.manifest.read_bytes() != manifest_bytes or store.splits.read_bytes() != split_bytes
            or (store.events.read_bytes() if store.events.exists() else b"") != event_bytes):
        raise ValueError("Inputs changed during audit; rerun against stable inputs")
    invalid = sum(bool(r["errors"]) for r in records)
    return {"schema_version": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "integrity_errors" if invalid or bad_images else ("no_human_events" if not records else "pending_human_reconciliation"),
            "training_approved": False, "source_manifest_sha256": manifest_hash,
            "split_manifest_sha256": split_hash, "events_sha256": sha(event_bytes),
            "events_file_present": store.events.exists(), "candidate_count": len(store._records),
            "event_count": len(records), "invalid_event_count": invalid,
            "image_integrity_errors": bad_images, "samples": summaries, "events": records,
            "limitations": ["Reviewer identity is self-reported, not authenticated.",
                            "Hashes detect inconsistency, not malicious rewriting of all evidence.",
                            "Agreement does not approve labels or establish garment independence.",
                            "No labels, original images or split assignments were modified."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("status", "candidate_count", "event_count", "invalid_event_count")}))
    return 1 if report["status"] == "integrity_errors" else 0


if __name__ == "__main__":
    raise SystemExit(main())
