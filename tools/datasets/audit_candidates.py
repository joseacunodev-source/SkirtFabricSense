"""Offline candidate integrity/duplicate audit. No training admission is inferred."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
TRAIN_PARTITIONS = {"train", "training", "train2020"}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    """Refuse replacement of existing evidence; write a new report atomically."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Evidence already exists: {path}; choose a new output")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False, suffix=".tmp") as handle:
        temporary = Path(handle.name)
        handle.write((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    try:
        # Hard-link creation fails if another writer created the destination meanwhile.
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_records(manifests):
    records, seen = [], set()
    for manifest in manifests:
        for number, line in enumerate(Path(manifest).read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            sample_id = record.get("sample_id")
            if not isinstance(sample_id, str) or not sample_id or sample_id in seen:
                raise ValueError(f"Missing/duplicate sample_id at {manifest}:{number}")
            seen.add(sample_id)
            records.append(record)
    return records


def partition(record):
    return str(record.get("source_partition", record.get("original_split", "unknown"))).lower()


def protected(record):
    # Unknown and non-training source partitions are never silently admitted.
    return partition(record) not in TRAIN_PARTITIONS or record.get("project_split") in {
        "test", "final_test", "external_holdout_sanity", "locked_test", "validation", "val"
    }


def inspect_image(record, root):
    relative = record.get("original_path", record.get("path"))
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("original_path must be a relative file path")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("image path escapes workspace root")
    digest = sha256(path)
    if digest != record.get("sha256"):
        raise ValueError("SHA-256 mismatch")
    with Image.open(path) as image:
        image.load()  # Decode pixels; an image header alone is insufficient.
        dimensions = list(image.size)
        expected = record.get("native_dimensions")
        if expected is None and "width" in record and "height" in record:
            expected = [record["width"], record["height"]]
        if expected is not None and dimensions != list(expected):
            raise ValueError(f"dimension mismatch: decoded {dimensions}, expected {expected}")
        rgb = ImageOps.exif_transpose(image).convert("RGB")
        pixel_hash = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
        tiny = rgb.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(tiny.getdata())
        dhash = 0
        for row in range(8):
            for col in range(8):
                dhash = (dhash << 1) | (pixels[row * 9 + col] > pixels[row * 9 + col + 1])
    return {"sample_id": record["sample_id"], "original_path": relative,
            "sha256": digest, "native_dimensions": dimensions,
            "pixel_sha256": pixel_hash, "dhash": f"{dhash:016x}", "status": "ok"}


def audit(records, root=ROOT, near_distance=4):
    if not 0 <= near_distance <= 16:
        raise ValueError("near_distance must be between 0 and 16")
    results = []
    for record in records:
        try:
            results.append(inspect_image(record, Path(root)))
        except (OSError, ValueError, TypeError, Image.DecompressionBombError) as error:
            results.append({"sample_id": record["sample_id"], "status": "error", "error": str(error)})
    good = [item for item in results if item["status"] == "ok"]
    exact, pixels = {}, {}
    for item in good:
        exact.setdefault(item["sha256"], []).append(item["sample_id"])
        pixels.setdefault(item["pixel_sha256"], []).append(item["sample_id"])
    near = []
    for index, left in enumerate(good):
        for right in good[index + 1:]:
            if left["pixel_sha256"] == right["pixel_sha256"]:
                continue
            distance = (int(left["dhash"], 16) ^ int(right["dhash"], 16)).bit_count()
            if distance <= near_distance:
                near.append({"sample_ids": [left["sample_id"], right["sample_id"]], "distance": distance})
    garments = {r["garment_id"] for r in records if r.get("garment_id") and r.get("garment_identity_status") == "verified"}
    return {"schema_version": 1, "counts": {"records": len(records), "decoded_images": len(good),
            "unique_file_hashes": len(exact), "unique_decoded_pixel_hashes": len(pixels),
            "original_records": sum(not r.get("parent_sample_id") for r in records),
            "verified_physical_garment_ids": len(garments),
            "unknown_physical_garment_records": sum(r.get("garment_identity_status") != "verified" for r in records),
            "integrity_errors": len(records) - len(good)}, "images": results,
            "exact_duplicate_groups": [v for v in exact.values() if len(v) > 1],
            "pixel_duplicate_groups": [v for v in pixels.values() if len(v) > 1],
            "near_duplicate_candidates": near, "near_distance": near_distance,
            "limitations": ["dHash is a conservative candidate detector, not proof of the same garment.",
                            "Undetected same-garment views remain possible; physical identity requires review.",
                            "Decoded files do not establish label validity, usage rights or training admission."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--near-distance", type=int, default=4)
    args = parser.parse_args()
    report = audit(load_records(args.manifest), args.root, args.near_distance)
    report["input_manifests"] = [{"path": str(p), "sha256": sha256(p)} for p in args.manifest]
    report["audit_source_sha256"] = sha256(__file__)
    write_json(args.output, report)
    print(json.dumps(report["counts"]))
    return 1 if report["counts"]["integrity_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
