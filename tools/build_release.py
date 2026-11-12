"""Build a checksummed local development bundle; never installs dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat

BUNDLE_ID = "skirt-finetune-v1"
RECORD = "records/models/2026-10-04-skirt-finetune-v1.json"
MODEL = "artifacts/models/skirt-finetune-v1/model.tflite"
CONTRACT = "artifacts/models/skirt-finetune-v1/contract.json"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def reject_links(path: Path) -> None:
    """Reject symlinks and Windows junction/reparse points in all ancestors."""
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f"Symlink not permitted: {item}")
        if item.exists() and getattr(item.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
            raise ValueError(f"Reparse point not permitted: {item}")


def source_file(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    if not relative or p.is_absolute() or ".." in p.parts or "\\" in relative or ":" in relative:
        raise ValueError(f"Unsafe relative path: {relative}")
    path = root.joinpath(*p.parts)
    reject_links(path)
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Missing or unsafe source: {relative}")
    return path


def build(root: Path, output: Path, include_app: bool = False) -> dict:
    root = Path(os.path.abspath(root))
    output = Path(os.path.abspath(output))
    reject_links(root)
    reject_links(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")
    # All source validation occurs before creating the destination.
    record_path = source_file(root, RECORD)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("release_id") != BUNDLE_ID:
        raise ValueError("Unexpected release identity")
    entries = record["model_files_and_sha256"]
    model_entries = [x for x in entries if x.get("path") == MODEL]
    if len(model_entries) != 1 or record["contract"].get("path") != CONTRACT:
        raise ValueError("Unexpected model/contract source paths")
    files = [(MODEL, "model.tflite", model_entries[0]["sha256"]),
             (CONTRACT, "contract.json", record["contract"]["sha256"])]
    payload = []
    for relative, target, expected in files:
        path = source_file(root, relative)
        if digest(path) != expected:
            raise ValueError(f"Source checksum mismatch: {relative}")
        payload.append((path, target, expected))
    if include_app and (root / "app").exists():
        reject_links(root / "app")
        for path in sorted((root / "app").glob("*.py")):
            relative = path.relative_to(root).as_posix()
            source_file(root, relative)
            payload.append((path, relative, digest(path)))
        static = root / "app/static"
        reject_links(static)
        if static.exists():
            for path in sorted(static.iterdir()):
                reject_links(path)
                if not path.is_file():
                    raise ValueError(f"Only flat static files are supported: {path}")
                relative = path.relative_to(root).as_posix()
                source_file(root, relative)
                payload.append((path, relative, digest(path)))
    manifest = {"schema_version": 1, "bundle_id": BUNDLE_ID,
                "model": "model.tflite", "contract": "contract.json",
                "files": [{"path": target, "sha256": expected} for _, target, expected in payload[:2]],
                "status": "development_only", "pi_verified": False}
    output.mkdir(parents=True, exist_ok=False)
    # A failed copy leaves no manifest: consumers must require the manifest.
    inventory = []
    for source, relative, expected in payload:
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        if digest(target) != expected:
            raise ValueError(f"Copied checksum mismatch: {relative}")
        inventory.append({"path": relative, "sha256": expected, "bytes": target.stat().st_size})
    metadata = {"schema_version": 1, "bundle_id": BUNDLE_ID,
                "status": "development_only", "pi_verified": False,
                "source_record": {"path": RECORD, "sha256": digest(record_path)},
                "builder_sha256": digest(Path(__file__)), "files": inventory,
                "dependencies_included": False,
                "limitations": ["No Pi verification", "No dependency wheels or installer",
                                "Local development use; redistribution rights require review"]}
    with (output / "inventory.json").open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2)
        stream.write("\n")
    with (output / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-app", action="store_true")
    args = parser.parse_args()
    result = build(args.root, args.output, args.include_app)
    print(json.dumps({"output": str(args.output), "files": len(result["files"]),
                      "status": result["status"], "pi_verified": False}))


if __name__ == "__main__":
    main()
