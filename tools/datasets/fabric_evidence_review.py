"""Offline blind fabric evidence intake, never a training or composition approval."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import uuid

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "data/labels/fabric-pilot-v1.jsonl"
SPLITS = "data/labels/fabric-pilot-v1-splits.json"
TERMS = "records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE"
EXPECTED = {
    MANIFEST: "92a80e4f974b9730f4631da75fed99b3f628751c882bfe179b39322d20247523",
    SPLITS: "e076033aa293ebad2058cec0ed2395292202f87bec9a78bfe2d350fa38e06c57",
    TERMS: "383efc1e19406703d591d32fa73b64f44914550456ecff4c0764b451e871b641",
}
SOURCE_DIR = "data/external/deepfashion_multimodal_candidates"
PARTITIONS = {"development_train", "development_validation"}
HASH = re.compile(r"[0-9a-f]{64}\Z")
ZERO_HASH = "0" * 64
QUEUE = "blind-queue.json"
BINDINGS = "bindings.private.json"
EVENTS = "events.jsonl"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _keys(value, keys, name):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{name} fields must match the contract")


def _text(value, name, limit=2000):
    if (not isinstance(value, str) or not value.strip() or len(value) > limit
            or any(ord(c) < 32 and c not in "\n\t" for c in value)):
        raise ValueError(f"Invalid {name}")
    return value


def _local(root, relative, prefix=None):
    if (not isinstance(relative, str) or "\\" in relative or ":" in relative
            or Path(relative).is_absolute() or ".." in Path(relative).parts):
        raise ValueError("Expected a project-relative local path")
    path = (root / relative).resolve()
    allowed = (root / prefix).resolve() if prefix else root.resolve()
    if not path.is_relative_to(allowed) or not path.is_file():
        raise ValueError("Missing or unsafe local evidence path")
    return path


def _jpeg_dimensions(path):
    """Read original JPEG SOF dimensions without a new image dependency.

    This is a bounded header check, not a full JPEG decode or orientation check.
    The originals already have a separate decode audit.
    """
    body = path.read_bytes()
    if body[:2] != b"\xff\xd8":
        raise ValueError("Original must be a JPEG")
    pos = 2
    while pos < len(body):
        if body[pos] != 255:
            raise ValueError("Invalid JPEG marker")
        while pos < len(body) and body[pos] == 255:
            pos += 1
        if pos >= len(body):
            break
        marker = body[pos]
        pos += 1
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD8:
            continue
        if pos + 2 > len(body):
            break
        length = struct.unpack(">H", body[pos:pos + 2])[0]
        if length < 2 or pos + length > len(body):
            raise ValueError("Invalid JPEG segment")
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if length < 8:
                raise ValueError("Invalid JPEG frame")
            height, width = struct.unpack(">HH", body[pos + 3:pos + 7])
            return width, height
        pos += length
    raise ValueError("JPEG has no supported dimension header")


def load_inputs(root=ROOT, expected=None):
    """Verify pinned provenance and all originals; custom pins are test-only API."""
    root = Path(root).resolve()
    expected = EXPECTED if expected is None else expected
    if set(expected) != {MANIFEST, SPLITS, TERMS}:
        raise ValueError("All frozen input pins are required")
    for relative, digest in expected.items():
        if not HASH.fullmatch(digest) or sha(_local(root, relative)) != digest:
            raise ValueError("Frozen input hash mismatch: " + relative)
    rows = [json.loads(line) for line in (root / MANIFEST).read_text(
        encoding="utf-8").splitlines() if line.strip()]
    assignments = json.loads((root / SPLITS).read_text(encoding="utf-8"))["assignments"]
    lookup = {}
    for assignment in assignments:
        if assignment["sample_id"] in lookup:
            raise ValueError("Duplicate frozen assignment")
        lookup[assignment["sample_id"]] = assignment
    ids, image_hashes, paths, groups = set(), set(), set(), defaultdict(set)
    for row in rows:
        sid = row["sample_id"]
        if (sid in ids or row["sha256"] in image_hashes
                or row["original_path"] in paths):
            raise ValueError("Duplicate sample, content or original path")
        ids.add(sid)
        image_hashes.add(row["sha256"])
        paths.add(row["original_path"])
        if (row["source_id"] != "deepfashion-multimodal"
                or row["source_partition"] != "train"
                or row["split"] not in PARTITIONS):
            raise ValueError("Protected or unsupported partition/source")
        if (row.get("admission_scope") != "internal_pipeline_smoke_only"
                or row.get("training_admitted") is not True
                or row.get("composition_verified") is not False
                or row.get("independent_human_review") is not False
                or row.get("physical_garment_verified") is not False):
            raise ValueError("Unsupported source admission or truth claim")
        _text(row["group_id"], "group_id", 200)
        assignment = lookup.get(sid)
        if not assignment or any(assignment[k] != row[k] for k in ("group_id", "split")):
            raise ValueError("Frozen group/split mismatch")
        groups[row["group_id"]].add(row["split"])
        image = _local(root, row["original_path"], SOURCE_DIR)
        if (not HASH.fullmatch(row["sha256"]) or sha(image) != row["sha256"]
                or type(row["size_bytes"]) is not int
                or image.stat().st_size != row["size_bytes"]):
            raise ValueError("Original image hash/size mismatch")
        if _jpeg_dimensions(image) != (row["width"], row["height"]):
            raise ValueError("Original image dimension mismatch")
        if row["terms_reference"] != TERMS:
            raise ValueError("Unpinned source terms")
    if ids != set(lookup) or not rows:
        raise ValueError("Frozen membership mismatch")
    if any(len(value) != 1 for value in groups.values()):
        raise ValueError("Source group overlaps frozen splits")
    return rows, dict(expected)


def documents(rows, pins):
    """Explicit blind allowlist; labels, scores, groups/splits stay out of queue."""
    blind, private = [], []
    for row in sorted(rows, key=lambda r: r["sample_id"]):
        rid = "fabric-" + object_sha([pins[MANIFEST], row["sample_id"]])[:24]
        blind.append({"review_id": rid, "image": {"path": row["original_path"],
                      "sha256": row["sha256"], "size_bytes": row["size_bytes"],
                      "width": row["width"], "height": row["height"]}})
        private.append({"review_id": rid, "original_source_record": row})
    queue = {"schema_version": 1, "purpose": "blind_appearance_evidence_only",
             "reviewer_identity": "self_reported_not_authenticated",
             "label_ontology_finalized": False, "training_approved": False,
             "records": blind}
    bindings = {"schema_version": 1, "role": "administrator_only_not_access_control",
                "frozen_inputs": pins, "blind_queue_content_sha256": object_sha(queue),
                "records": private}
    return queue, bindings


def _write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def build(root, output, expected=None):
    rows, pins = load_inputs(root, expected)
    output = Path(output).resolve()
    if not output.is_relative_to((Path(root).resolve() / "records/review").resolve()):
        raise ValueError("Queue output must be a new folder under records/review")
    output.mkdir(parents=True, exist_ok=False)
    queue, bindings = documents(rows, pins)
    _write_new(output / QUEUE, queue)
    _write_new(output / BINDINGS, bindings)
    (output / EVENTS).touch(exist_ok=False)
    return {"queue_records": len(rows), "observations_submitted": 0,
            "source_groups": len({r["group_id"] for r in rows}),
            "split_counts": dict(Counter(r["split"] for r in rows)),
            "verified_physical_specimens": None, "training_approved": False,
            "queue_sha256": sha(output / QUEUE), "bindings_sha256": sha(output / BINDINGS)}


def _package(root, directory, expected=None):
    directory = Path(directory).resolve()
    root = Path(root).resolve()
    if not directory.is_relative_to((root / "records/review").resolve()):
        raise ValueError("Review directory must remain under records/review")
    rows, pins = load_inputs(root, expected)
    queue, bindings = documents(rows, pins)
    for filename, value in ((QUEUE, queue), (BINDINGS, bindings)):
        actual = json.loads(_local(root, (directory / filename).relative_to(root).as_posix()).read_text(encoding="utf-8"))
        if actual != value:
            raise ValueError("Review package changed: " + filename)
    return queue, bindings


def validate_payload(root, payload, queue, queue_hash):
    _keys(payload, ("review_id", "queue_sha256", "image_sha256", "reviewer",
                    "original_viewed", "observations", "composition_evidence",
                    "source_evidence_references"), "Submission")
    lookup = {r["review_id"]: r for r in queue["records"]}
    if not isinstance(payload["review_id"], str) or payload["review_id"] not in lookup:
        raise ValueError("Unknown review id")
    if (payload["queue_sha256"] != queue_hash
            or payload["image_sha256"] != lookup[payload["review_id"]]["image"]["sha256"]):
        raise ValueError("Submission image or queue binding mismatch")
    _keys(payload["reviewer"], ("display_name", "actor_kind"), "Reviewer")
    _text(payload["reviewer"]["display_name"], "reviewer name", 100)
    if payload["reviewer"]["actor_kind"] not in {"human", "agent"}:
        raise ValueError("Actor kind must be human or agent, self-reported only")
    if payload["original_viewed"] is not True:
        raise ValueError("Reviewer must attest to viewing the original")
    obs = payload["observations"]
    _keys(obs, ("appearance_status", "appearance_descriptors", "material_to_skirt_association",
                "presentation", "full_skirt_visibility", "texture_detail", "notes"), "Observations")
    for name, allowed in {
        "appearance_status": {"single_appearance", "mixed_appearance", "unknown"},
        "material_to_skirt_association": {"clear", "uncertain", "not_skirt"},
        "presentation": {"worn", "hanging", "held", "mannequin", "unknown"},
        "full_skirt_visibility": {"full", "partial", "uncertain"},
        "texture_detail": {"sufficient_for_description", "insufficient", "uncertain"},
    }.items():
        if not isinstance(obs[name], str) or obs[name] not in allowed:
            raise ValueError("Unsupported observation: " + name)
    labels = obs["appearance_descriptors"]
    if not isinstance(labels, list) or len(labels) > 8:
        raise ValueError("Appearance descriptors must be a bounded list")
    for value in labels:
        _text(value, "appearance descriptor", 120)
    if len(set(labels)) != len(labels):
        raise ValueError("Duplicate appearance descriptors")
    if ((obs["appearance_status"] == "unknown" and labels)
            or (obs["appearance_status"] != "unknown" and not labels)):
        raise ValueError("Unknown appearance has no descriptors; known appearance needs evidence")
    if obs["material_to_skirt_association"] != "clear" and obs["appearance_status"] != "unknown":
        raise ValueError("Uncertain/non-skirt association must abstain from skirt descriptors")
    _text(obs["notes"], "observed evidence notes", 4000)
    comp = payload["composition_evidence"]
    _keys(comp, ("status", "unverified_claim"), "Composition evidence")
    if comp["status"] == "not_observed":
        if comp["unverified_claim"] is not None:
            raise ValueError("No composition evidence cannot carry a claim")
    elif comp["status"] == "unverified_document_claim":
        _text(comp["unverified_claim"], "unverified document claim", 1000)
    else:
        raise ValueError("Visual intake cannot verify fibre composition")
    refs = payload["source_evidence_references"]
    if not isinstance(refs, list) or len(refs) > 8:
        raise ValueError("Evidence references must be a bounded local-file list")
    seen = set()
    document_support = False
    for ref in refs:
        _keys(ref, ("path", "sha256", "kind", "item_association"), "Evidence reference")
        if ref["kind"] not in {"source_annotation", "terms", "garment_tag", "supplier_document", "other"}:
            raise ValueError("Unknown evidence kind")
        if ref["item_association"] not in {"claimed_skirt", "scene_only", "unresolved"}:
            raise ValueError("Evidence association is unsupported")
        evidence_path = _local(Path(root), ref["path"])
        if (ref["path"] in seen or not isinstance(ref["sha256"], str)
                or not HASH.fullmatch(ref["sha256"]) or sha(evidence_path) != ref["sha256"]):
            raise ValueError("Duplicate or changed source evidence")
        seen.add(ref["path"])
        document_support |= ref["kind"] in {"garment_tag", "supplier_document"} and ref["item_association"] == "claimed_skirt"
    if comp["status"] == "unverified_document_claim" and not document_support:
        raise ValueError("Document claim needs a tag/supplier reference tied to the claimed skirt")


def verify(root, directory, expected=None):
    queue, bindings = _package(root, directory, expected)
    directory = Path(directory).resolve()
    event_path = _local(Path(root).resolve(), (directory / EVENTS).relative_to(Path(root).resolve()).as_posix())
    body = event_path.read_bytes()
    if body and not body.endswith(b"\n"):
        raise ValueError("Incomplete event log tail")
    head, event_ids, reviewed, events = ZERO_HASH, set(), set(), []
    queue_hash = sha(directory / QUEUE)
    for line in body.decode("utf-8").splitlines():
        if not line:
            raise ValueError("Blank event rows are not permitted")
        event = json.loads(line)
        _keys(event, ("schema_version", "event_id", "recorded_at_utc", "previous_event_sha256",
                      "payload", "reviewer_identity", "status", "training_approved",
                      "composition_verified", "event_sha256"), "Event")
        if (type(event["schema_version"]) is not int or event["schema_version"] != 1
                or event["status"] != "pending_reconciliation"
                or event["training_approved"] is not False or event["composition_verified"] is not False
                or event["reviewer_identity"] != "self_reported_not_authenticated"):
            raise ValueError("Event cannot establish training approval or truth")
        if (not isinstance(event["event_id"], str)
                or str(uuid.UUID(event["event_id"])) != event["event_id"]
                or event["event_id"] in event_ids):
            raise ValueError("Invalid/duplicate event identity")
        recorded = datetime.fromisoformat(event["recorded_at_utc"])
        if recorded.tzinfo is None or recorded.utcoffset().total_seconds() != 0:
            raise ValueError("Event timestamp must have a UTC offset")
        digest_body = {k: v for k, v in event.items() if k != "event_sha256"}
        if event["previous_event_sha256"] != head or object_sha(digest_body) != event["event_sha256"]:
            raise ValueError("Event hash chain mismatch")
        validate_payload(root, event["payload"], queue, queue_hash)
        head = event["event_sha256"]
        event_ids.add(event["event_id"])
        reviewed.add(event["payload"]["review_id"])
        events.append(event)
    return {"schema_version": 1, "integrity_passed": True,
            "queue_records": len(queue["records"]), "observations_submitted": len(events),
            "source_groups": len({r["original_source_record"]["group_id"] for r in bindings["records"]}),
            "split_counts": dict(Counter(r["original_source_record"]["split"] for r in bindings["records"])),
            "samples_with_submitted_observations": len(reviewed),
            "pending_samples": len(queue["records"]) - len(reviewed),
            "pending_reconciliation_events": len(events), "event_chain_head_sha256": head,
            "event_log_sha256": sha(event_path), "queue_sha256": queue_hash,
            "bindings_sha256": sha(directory / BINDINGS),
            "frozen_inputs": bindings["frozen_inputs"],
            "training_approved": False, "composition_verified": False,
            "independent_human_truth_established": False,
            "verified_physical_specimens": None}


@contextmanager
def _lock(directory):
    path = Path(directory) / ".append.lock"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.close(fd)
        yield
    finally:
        path.unlink()


def append(root, directory, payload, expected=None):
    """Single-writer append; correction is a new event, never an overwritten row."""
    directory = Path(directory).resolve()
    if not directory.is_dir() or not directory.is_relative_to((Path(root).resolve() / "records/review").resolve()):
        raise ValueError("Append target must be an existing project review directory")
    with _lock(directory):
        report = verify(root, directory, expected)
        queue, _ = _package(root, directory, expected)
        validate_payload(root, payload, queue, report["queue_sha256"])
        event = {"schema_version": 1, "event_id": str(uuid.uuid4()),
                 "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                 "previous_event_sha256": report["event_chain_head_sha256"],
                 "payload": payload, "reviewer_identity": "self_reported_not_authenticated",
                 "status": "pending_reconciliation", "training_approved": False,
                 "composition_verified": False}
        event["event_sha256"] = object_sha(event)
        with (Path(directory) / EVENTS).open("ab") as stream:
            stream.write(canonical(event) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    return {"event_id": event["event_id"], "event_sha256": event["event_sha256"],
            "status": event["status"], "training_approved": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build", help="Prepare a new blind queue, no observations")
    build_parser.add_argument("--output", type=Path, required=True)
    for command in ("verify", "append"):
        child = sub.add_parser(command)
        child.add_argument("--directory", type=Path, required=True)
        if command == "append":
            child.add_argument("--submission", type=Path, required=True)
        else:
            child.add_argument("--output", type=Path, help="Optional new report path")
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(ROOT, args.output)
        elif args.command == "append":
            result = append(ROOT, args.directory, json.loads(args.submission.read_text(encoding="utf-8")))
        else:
            result = verify(ROOT, args.directory)
            if args.output:
                _write_new(args.output, result)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"integrity_passed": False, "error": str(exc), "training_approved": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
