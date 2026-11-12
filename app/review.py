"""Blind, append-only annotation intake; never modifies training releases."""
from __future__ import annotations

import hashlib
import json
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewStore:
    """Allow only original Fashionpedia training candidates with frozen splits.

    The server must serialize access through this instance (the lock covers
    threaded requests). Reviewer names are self-reported, not authenticated.
    """

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.manifest = self.root / "data/manifests/skirt_candidates.jsonl"
        self.splits = self.root / "data/manifests/source-skirt-development-splits.json"
        self.events = self.root / "records/human-review/events.jsonl"
        self._lock = threading.Lock()
        self._manifest_hash = digest(self.manifest)
        self._split_hash = digest(self.splits)
        assignments = json.loads(self.splits.read_text(encoding="utf-8"))["assignments"]
        self._assignments = {}
        for item in assignments:
            sid = item["sample_id"]
            if sid in self._assignments:
                raise ValueError("Duplicate frozen split sample")
            self._assignments[sid] = item
        self._records = {}
        for line in self.manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            sid = row["sample_id"]
            if (row.get("source_partition") != "train2020"
                    or row.get("source_id") != "fashionpedia-train2020"
                    or not re.fullmatch(r"fashionpedia-train2020-\d+", sid)):
                raise ValueError("Review manifest includes unsupported/protected source")
            if sid in self._records:
                raise ValueError("Duplicate review sample")
            if self._assignments.get(sid, {}).get("split") not in {
                    "development_train", "development_validation"}:
                raise ValueError("Missing or protected frozen split")
            if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
                raise ValueError("Invalid image hash")
            self._records[sid] = row
            self._safe_image(row)

    def _safe_image(self, row: dict) -> Path:
        path = (self.root / row["original_path"]).resolve()
        allowed = (self.root / "data/external/fashionpedia_train/images").resolve()
        if not path.is_relative_to(allowed) or not path.is_file():
            raise ValueError("Image is outside permitted originals or missing")
        return path

    def image_path(self, sample_id: str) -> Path:
        if not isinstance(sample_id, str) or sample_id not in self._records:
            raise ValueError("Unknown review sample")
        row = self._records[sample_id]
        path = self._safe_image(row)
        if digest(path) != row["sha256"]:
            raise ValueError("Original image hash changed")
        return path

    def queue(self) -> dict:
        # Explicit allowlist: no source attributes, prior labels or model output.
        with self._lock:
            reviewed = set()
            if self.events.exists():
                for line in self.events.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        reviewed.add(json.loads(line)["sample_id"])
            rows = [{"sample_id": sid, "image_sha256": r["sha256"],
                     "width": r["width"], "height": r["height"]}
                    for sid, r in sorted(self._records.items())]
        return {"records": rows, "total": len(rows),
                "samples_with_submitted_reviews": len(reviewed & self._records.keys()),
                "status": "Annotations await reconciliation and a versioned training release.",
                "reviewer_identity": "self_reported_not_authenticated"}

    def save(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("Review must be an object")
        allowed = {"sample_id", "image_sha256", "reviewer", "appearance_label",
                   "full_skirt_view", "evidence"}
        if set(payload) != allowed:
            raise ValueError("Review fields must match the annotation contract")
        for field, limit in (("reviewer", 100), ("evidence", 4000)):
            value = payload[field]
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"{field} is required and must be at most {limit} characters")
            if any(ord(c) < 32 and c not in "\n\t" for c in value):
                raise ValueError(f"{field} contains unsupported control characters")
        if payload["appearance_label"] not in ("pleated", "non_pleated", "unknown"):
            raise ValueError("Unsupported appearance label")
        if type(payload["full_skirt_view"]) is not bool:
            raise ValueError("full_skirt_view must be a boolean")
        with self._lock:
            if digest(self.manifest) != self._manifest_hash or digest(self.splits) != self._split_hash:
                raise ValueError("Review inputs changed; restart and reconcile before continuing")
            self.image_path(payload["sample_id"])
            row = self._records[payload["sample_id"]]
            if payload["image_sha256"] != row["sha256"]:
                raise ValueError("Submitted image hash does not match original")
            assignment = self._assignments[payload["sample_id"]]
            event = {"schema_version": 1, "event_id": str(uuid.uuid4()),
                     "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
                     **payload, "reviewer": payload["reviewer"].strip(),
                     "evidence": payload["evidence"].strip(),
                     "reviewer_identity": "self_reported_not_authenticated",
                     "status": "pending_reconciliation", "training_approved": False,
                     "source_partition": "train2020", "split": assignment["split"],
                     "group_hash": assignment.get("group_hash"),
                     "source_manifest_sha256": self._manifest_hash,
                     "split_manifest_sha256": self._split_hash}
            event["event_sha256"] = hashlib.sha256(json.dumps(
                event, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            target = self.events.resolve()
            if not target.is_relative_to(self.root / "records"):
                raise ValueError("Review output is outside records")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(event, ensure_ascii=False) + "\n")
                stream.flush()
            return {"event_id": event["event_id"], "event_sha256": event["event_sha256"],
                    "status": event["status"], "training_approved": False}
