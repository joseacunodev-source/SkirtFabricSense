"""Deterministic source-text triage, never a composition-label annotator.

No packages or network access required. Outputs are new immutable review artifacts;
the input manifest and project labels are never edited.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FIBERS = ("cotton", "polyester", "wool", "silk", "viscose", "rayon", "nylon",
          "acrylic", "bamboo", "acetate", "cupro", "linen", "hemp", "elastane", "spandex")
# These remain source descriptive terms: not a mutually exclusive ontology.
FABRIC_TERMS = ("satin", "sateen", "chiffon", "denim", "twill", "poplin", "voile",
                "velvet", "velour", "corduroy", "organza", "taffeta", "crepe",
                "georgette", "jacquard", "brocade", "fleece", "jersey", "knit",
                "mesh", "tulle", "lawn", "flannel", "tweed", "canvas", "felt")
BASE_BLOCKERS = ["no_verified_composition_or_construction_evidence",
                 "source_partition_unspecified", "physical_specimen_grouping_unresolved",
                 "closeup_source_does_not_validate_full_skirt_domain"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mentions(description: str, terms: tuple[str, ...]) -> list[dict]:
    # Hyphens/underscores in archive filenames are separators, not literal words.
    text = description.replace("_", " ")
    hits = []
    for term in terms:
        for match in re.finditer(r"\b" + re.escape(term) + r"\b", text, re.I):
            hits.append({"term": term, "text": description[match.start():match.end()],
                         "span": [match.start(), match.end()]})
    return sorted(hits, key=lambda h: (h["span"][0], h["term"]))


def review(record: dict) -> dict:
    folder = record["source_labels"]["publisher_folder"]
    description = record["source_labels"].get("description", "")
    fibers = mentions(description, FIBERS)
    found = {hit["term"] for hit in fibers}
    other = sorted(found - {folder.lower()})
    flags = []
    if other:
        flags.append("other_fiber_mentioned")
    if len(found) > 1:
        flags.append("multiple_fibers_mentioned")
    if folder.lower() not in found:
        flags.append("folder_fiber_not_explicit_in_description")
    if re.search(r"\bblend\w*\b", description, re.I):
        flags.append("blend_word_present")
    if re.search(r"\bstretch\b", description, re.I):
        flags.append("stretch_word_requires_composition_check")
    # Source filenames can be truncated. A final partial fiber token is merely a
    # review cue; do not expand it into a fiber claim.
    ending = re.search(r"([A-Za-z]+)[^A-Za-z]*$", description)
    partial = []
    if ending:
        word = ending.group(1).lower()
        partial = [fiber for fiber in FIBERS if len(word) >= 4 and fiber.startswith(word) and fiber != word]
        if partial:
            flags.append("possible_truncated_fiber_token")
    priority = "high" if other or partial or "blend_word_present" in flags else "normal"
    return {"schema_version": 1, "sample_id": record["sample_id"],
            "original_path": record["original_path"], "sha256": record["sha256"],
            "source_item_id": record["source_item_id"], "source_partition": record["source_partition"],
            "publisher_folder": folder, "source_description": description,
            "fiber_text_mentions": fibers, "fabric_text_mentions": mentions(description, FABRIC_TERMS),
            "other_fiber_terms": other, "possible_terminal_fiber_completions": partial,
            "flags": flags, "review_priority": priority,
            "review_method": "deterministic lexical triage; not visual or supplier verification",
            "review_status": "source_text_triaged_ground_truth_unverified",
            "project_fiber_composition": None, "project_fabric_construction": None,
            "training_eligibility": {"project_fabric": False, "source_folder_pretraining": False},
            "blockers": BASE_BLOCKERS.copy(),
            "required_review": "Retrieve linked supplier/tag evidence with composition percentages and construction; resolve identity and partition policy before admission."}


def self_test() -> None:
    def row(text, folder="Cotton"):
        return review({"source_labels": {"publisher_folder": folder, "description": text},
                       "sample_id": "test", "original_path": "none", "sha256": "none",
                       "source_item_id": "test", "source_partition": "unspecified_in_archive"})
    assert row("Cotton and Polyester Twill")["other_fiber_terms"] == ["polyester"]
    assert row("Wool-Cotton Twill")["other_fiber_terms"] == ["wool"]
    assert row("Polyester and Cotto", "Cotton")["possible_terminal_fiber_completions"] == ["cotton"]
    assert row("Cotton Sateen")["fabric_text_mentions"][0]["term"] == "sateen"
    assert not mentions("Cottonwood polyesters", FIBERS)
    assert row("Nylon_Mesh", "Polyester")["other_fiber_terms"] == ["nylon"]
    assert not any(row("100% Cotton")["training_eligibility"].values())
    print("7 lexical/evidence checks passed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="data/manifests/fabric_candidates.jsonl")
    parser.add_argument("--output-prefix", default="records/review/fabric-label-review-2026-10-03")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    source = ROOT / args.manifest
    output = ROOT / args.output_prefix
    queue_path = output.with_suffix(".jsonl")
    report_path = output.with_suffix(".json")
    if queue_path.exists() or report_path.exists():
        raise SystemExit("Refusing to replace existing review evidence; choose a new prefix")
    records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r["sample_id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate sample IDs")
    for record in records:
        if record["source_labels"]["publisher_folder"] not in ("Cotton", "Polyester"):
            raise ValueError("Unexpected source class")
        if record["source_partition"] != "unspecified_in_archive":
            raise ValueError("Partition changed: revisit explicit blocker policy")
        if record.get("project_labels") or record.get("training_eligibility"):
            raise ValueError("Existing decisions require review; never overwrite them")
        path = (ROOT / record["original_path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or digest(path) != record["sha256"]:
            raise ValueError("Source image path/hash verification failed")
    rows = sorted((review(r) for r in records), key=lambda r: (r["review_priority"] != "high", r["sample_id"]))
    output.parent.mkdir(parents=True, exist_ok=True)
    queue_bytes = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")
    summary = {"schema_version": 1, "review_date": "2026-10-03", "method": "lexical triage, not verified truth",
               "source_manifest": {"path": args.manifest, "sha256": digest(source)},
               "review_tool": {"path": "tools/datasets/review_fabric_labels.py", "sha256": digest(Path(__file__))},
               "queue": {"path": str(queue_path.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(queue_bytes).hexdigest()},
               "images_hash_verified": len(records), "records_reviewed": len(rows),
               "publisher_folder_counts": dict(Counter(r["publisher_folder"] for r in rows)),
               "priority_counts": dict(Counter(r["review_priority"] for r in rows)),
               "flag_counts": dict(Counter(f for r in rows for f in r["flags"])),
               "fiber_mention_counts": dict(Counter(t for r in rows for t in {h["term"] for h in r["fiber_text_mentions"]})),
               "fabric_mention_counts": dict(Counter(t for r in rows for t in {h["term"] for h in r["fabric_text_mentions"]})),
               "project_training_admitted": 0, "source_pretraining_admitted": 0,
               "verified_composition_labels": 0, "verified_construction_labels": 0,
               "blockers": BASE_BLOCKERS,
               "limitations": ["Descriptions may be truncated and incomplete", "No flag does not mean correct label", "Bamboo is preserved as a source term without inferring fiber processing", "Textile words may name colors/prints rather than construction", "No physical specimens independently verified", "No source partitions altered"]}
    with queue_path.open("xb") as handle:
        handle.write(queue_bytes)
    with report_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
