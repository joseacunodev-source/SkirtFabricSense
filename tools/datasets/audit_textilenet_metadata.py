"""Offline identity audit of TextileNet URL manifests; never downloads/admit images.

Source filenames, Wish webimage tokens and URL paths are identity leads, not verified
physical garments. Protected manifests are optional, local-only identity checks; their
label distributions are deliberately omitted. No skirt-specific material assignment
can be established by the three-column upstream schema.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def read_rows(path, *, max_bytes=32 * 1024 * 1024, max_rows=300000):
    if (type(max_bytes) is not int or max_bytes <= 0 or
            type(max_rows) is not int or max_rows <= 0):
        raise ValueError("Bounds must be positive integers")
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError("Metadata exceeds the declared byte limit")
    with path.open("rb") as stream:
        body = stream.read(max_bytes + 1)
    if len(body) > max_bytes:
        raise ValueError("Metadata grew beyond the declared byte limit")
    rows = json.loads(body)
    if not isinstance(rows, list) or len(rows) > max_rows:
        raise ValueError("Expected a bounded list of metadata rows")
    for index, row in enumerate(rows):
        if (not isinstance(row, list) or len(row) != 3 or
                any(not isinstance(value, str) or not value.strip() for value in row)):
            raise ValueError(f"Row {index}: expected three nonempty strings")
        name, _, url = row
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise ValueError(f"Row {index}: filename must be a basename")
        if any(ord(c) < 32 for value in row for c in value):
            raise ValueError(f"Row {index}: control character")
        parsed = urlsplit(url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname or
                parsed.username is not None or parsed.password is not None):
            raise ValueError(f"Row {index}: expected an HTTP(S) URL without credentials")
        try:
            parsed.port
        except ValueError as error:
            raise ValueError(f"Row {index}: invalid URL port") from error
    return rows, {"path": path.as_posix(), "sha256": hashlib.sha256(body).hexdigest(),
                  "bytes": len(body), "rows": len(rows)}


def identities(row):
    name, _, url = row
    parsed = urlsplit(url)
    result = {"filename": name, "exact_url": url,
              "host_and_path": (parsed.hostname.lower(), parsed.port, parsed.path)}
    match = re.fullmatch(r"(\d+)_imaterial\.jpe?g", name, flags=re.IGNORECASE)
    if match:
        result["imaterial_filename_id"] = match.group(1)
    match = re.fullmatch(r"/api/webimage/([0-9a-fA-F]{24})(?:-[^/]*)?", parsed.path)
    if parsed.hostname.lower() == "contestimg.wish.com" and match:
        result["wish_webimage_token"] = match.group(1).lower()
    return result


def summarize(rows, *, include_labels):
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        for kind, token in identities(row).items():
            groups[kind][token].append(row[1] if include_labels else None)
    summary = {"rows": len(rows), "identity_groups": {}}
    for kind, values in sorted(groups.items()):
        repeated = [labels for labels in values.values() if len(labels) > 1]
        counts = {"distinct": len(values), "rows_with_identity": sum(map(len, values.values())),
                  "repeated_groups": len(repeated),
                  "rows_in_repeated_groups": sum(map(len, repeated)),
                  "excess_rows": sum(len(labels) - 1 for labels in repeated)}
        if include_labels:
            counts["groups_with_multiple_source_labels"] = sum(
                len(set(labels)) > 1 for labels in values.values())
        summary["identity_groups"][kind] = counts
    if include_labels:
        summary["source_label_counts"] = dict(sorted(Counter(r[1] for r in rows).items()))
    return summary


def audit(train_path, protected_paths=(), *, max_bytes=32 * 1024 * 1024, max_rows=300000):
    train, train_ref = read_rows(train_path, max_bytes=max_bytes, max_rows=max_rows)
    train_ids = defaultdict(set)
    for row in train:
        for kind, token in identities(row).items():
            train_ids[kind].add(token)
    protected = []
    for path in protected_paths:
        rows, reference = read_rows(path, max_bytes=max_bytes, max_rows=max_rows)
        protected_ids = defaultdict(set)
        for row in rows:
            for kind, token in identities(row).items():
                protected_ids[kind].add(token)
        protected.append({"input": reference, "summary": summarize(rows, include_labels=False),
                          "train_shared_identity_groups": {
                              kind: len(tokens & train_ids[kind])
                              for kind, tokens in sorted(protected_ids.items())}})
    return {"schema_version": 1, "status": "metadata_identity_audit_only",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "input_schema": ["filename", "source_material_label", "source_url"],
            "train_input": train_ref, "train_summary": summarize(train, include_labels=True),
            "protected_inputs": protected,
            "protected_overlap_checked": bool(protected),
            "protected_labels_used_for_training": False,
            "garment_category_field_present": False,
            "instance_material_association_verified": False,
            "physical_garment_identity_verified": False,
            "source_partition_of_underlying_imaterial_images_verified": False,
            "source_urls_requested": 0, "new_images": 0, "training_admissions": 0,
            "limitations": [
                "A source train filename is not proof of the original upstream source partition.",
                "Distinct filenames, URL paths and webimage tokens are not specimen counts.",
                "Multiple material labels can be legitimate overlap and are not relabelled.",
                "No garment categories, full-skirt visibility or image rights are inferred.",
                "Absent protected manifests leave cross-partition overlap untested."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path)
    parser.add_argument("--protected", action="append", default=[], type=Path,
                        help="Optional existing local protected manifest; identities only")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-bytes", type=int, default=32 * 1024 * 1024)
    parser.add_argument("--max-rows", type=int, default=300000)
    args = parser.parse_args()
    if args.max_bytes <= 0 or args.max_rows <= 0:
        parser.error("Bounds must be positive")
    result = audit(args.train, args.protected, max_bytes=args.max_bytes, max_rows=args.max_rows)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "rows": result["train_input"]["rows"],
                      "new_images": 0, "training_admissions": 0}))


if __name__ == "__main__":
    main()
