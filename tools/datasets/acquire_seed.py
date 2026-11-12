"""Acquire a small research seed using only Python's standard library.

Run from the project root: python tools/datasets/acquire_seed.py
No source scripts are executed. Existing downloads are retained and hash checked.
This is metadata plus a small, attributed external evaluation sample, not a
training-ready fabric dataset. See docs/DATASETS.md.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
import re
import time
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "external"
MANIFEST = BASE / "acquisition_manifest.json"
MAX_FILE_BYTES = 30 * 1024 * 1024
SAMPLE_COUNT = 12
TEXTILENET_COMMIT = "6b4f0579b2abc18422192afea07882f84dcb83e4"
FASHIONPEDIA_COMMIT = "d291e52663ecfb17bba9b953b2f8e1f2bf3fbd1e"
HEADERS = {"User-Agent": "SkirtFabricSense-research-seed/0.1"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request(url: str) -> tuple[bytes, str]:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as response:
        advertised = int(response.headers.get("Content-Length", "0"))
        if advertised > MAX_FILE_BYTES:
            raise ValueError("File exceeds 30 MiB seed acquisition limit")
        body = response.read(MAX_FILE_BYTES + 1)
        if len(body) > MAX_FILE_BYTES:
            raise ValueError("Response exceeds 30 MiB seed acquisition limit")
        return body, response.url


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def atomic_write(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(body)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def verify_manifest(manifest: dict, root: Path) -> dict:
    root = root.resolve()
    seen = set()
    for artifact in manifest["artifacts"]:
        path = (root / artifact["path"]).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Artifact path escapes project root")
        if path in seen:
            raise ValueError(f"Duplicate artifact: {artifact['path']}")
        seen.add(path)
        body = path.read_bytes()
        if len(body) != artifact["size_bytes"] or digest(body) != artifact["sha256"]:
            raise ValueError(f"Hash/size mismatch: {artifact['path']}")
    return {"verified_artifacts": len(seen),
            "images": sum(a["kind"] == "image" for a in manifest["artifacts"]),
            "network_used": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="Verify local hashes and sizes without network or writes")
    args = parser.parse_args()
    if args.verify_only and not MANIFEST.exists():
        raise FileNotFoundError("No acquisition manifest exists")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {
        "schema_version": 1, "created_at_utc": now(), "artifacts": [], "attempts": []
    }
    verified = verify_manifest(manifest, ROOT)
    if args.verify_only or verified["images"] >= SAMPLE_COUNT:
        print(json.dumps(verified, indent=2))
        return
    by_path = {a["path"]: a for a in manifest["artifacts"]}

    def save() -> None:
        BASE.mkdir(parents=True, exist_ok=True)
        atomic_write(MANIFEST, (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))

    def acquire(relative: str, url: str, kind: str, license_note: str, extra=None):
        path = BASE / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        key = path.relative_to(ROOT).as_posix()
        if path.exists() and key in by_path:
            body = path.read_bytes()
            if digest(body) != by_path[key]["sha256"]:
                raise ValueError(f"Hash mismatch: {key}")
            return by_path[key]
        if path.exists():
            raise ValueError(f"Untracked existing file; audit before acquiring: {key}")
        body, resolved = request(url)
        if kind == "image" and not body.startswith(b"\xff\xd8\xff"):
            raise ValueError("Image response is not a JPEG; no file written")
        atomic_write(path, body)
        entry = {
            "path": key, "source_url": url, "resolved_url": resolved,
            "retrieved_at_utc": now(), "size_bytes": len(body), "sha256": digest(body),
            "kind": kind, "license_note": license_note,
        }
        if extra:
            entry.update(extra)
        manifest["artifacts"].append(entry)
        by_path[key] = entry
        save()
        return entry

    assets = [
        ("fashionpedia/instances_attributes_val2020.json", "https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_val2020.json", "annotations", "Annotations CC BY 4.0; image rights separate."),
        ("fashionpedia/source_README.md", f"https://raw.githubusercontent.com/cvdfoundation/fashionpedia/{FASHIONPEDIA_COMMIT}/README.md", "source_documentation", "Source README retained for provenance."),
        ("fashionpedia/terms_snapshot.html", "https://fashionpedia.github.io/home/data_license.html", "license_evidence", "Terms snapshot: annotations/ontology CC BY 4.0; images retain source terms."),
        ("textilenet/fabric_label.txt", f"https://raw.githubusercontent.com/hahashu/TextileNet/{TEXTILENET_COMMIT}/labels/fabric_label.txt", "taxonomy", "Repository has MIT code license; image license unresolved."),
        ("textilenet/fibre_label.txt", f"https://raw.githubusercontent.com/hahashu/TextileNet/{TEXTILENET_COMMIT}/labels/fibre_label.txt", "taxonomy", "Repository has MIT code license; image license unresolved."),
        ("textilenet/source_README.md", f"https://raw.githubusercontent.com/hahashu/TextileNet/{TEXTILENET_COMMIT}/README.md", "source_documentation", "CC BY sentence concerns manuscripts; do not infer blanket photo permission."),
        ("textilenet/LICENSE", f"https://raw.githubusercontent.com/hahashu/TextileNet/{TEXTILENET_COMMIT}/LICENSE", "license_evidence", "MIT license for repository code; not proof of underlying photo rights."),
        ("dtd/source_README.txt", "https://www.robots.ox.ac.uk/~vgg/data/dtd/download/README.txt", "source_documentation", "Dataset website states research purposes; no blanket commercial clearance inferred."),
        ("dtd/dtd-r1.0.1-labels.tar.gz", "https://www.robots.ox.ac.uk/~vgg/data/dtd/download/dtd-r1.0.1-labels.tar.gz", "annotations_archive", "Dataset website states research purposes; no photos downloaded."),
    ]
    for relative, url, kind, license_note in assets:
        acquire(relative, url, kind, license_note)

    fp = json.loads((BASE / "fashionpedia/instances_attributes_val2020.json").read_text())
    attrs = {a["id"]: a["name"] for a in fp["attributes"]}
    categories = {a["id"]: a["name"] for a in fp["categories"]}
    if categories.get(8) != "skirt" or attrs.get(304) != "pleat":
        raise ValueError("Source label IDs changed; update the reviewed sampling policy")
    skirts = [a for a in fp["annotations"] if a["category_id"] == 8]
    grouped = {a["image_id"]: a for a in skirts}
    if len(grouped) != len(skirts):
        raise ValueError("Multiple skirt instances per image need an explicit sampling policy")
    candidates = [i for i in fp["images"] if i["id"] in grouped and i["license"] == 0]
    candidates.sort(key=lambda i: (304 not in grouped[i["id"]]["attribute_ids"], i["id"]))
    # Preserve completed acquisitions on partial retries rather than losing
    # attribution when previously visited source pages become unavailable.
    samples = [dict(a) for a in manifest["artifacts"] if a["kind"] == "image"]
    completed_ids = {s["fashionpedia_image_id"] for s in samples}
    for img in candidates:
        if len(samples) >= SAMPLE_COUNT:
            break
        if img["id"] in completed_ids:
            continue
        match = re.search(r"/(\d+)_[^/]+\.jpg", img["original_url"])
        if not match:
            continue
        photo_id = match.group(1)
        try:
            _, photo_page = request("https://www.flickr.com/photo.gne?id=" + photo_id)
            embed_url = "https://www.flickr.com/services/oembed/?" + urllib.parse.urlencode({"format": "json", "url": photo_page})
            meta_entry = acquire(f"fashionpedia/sample_metadata/{img['id']}_oembed.json", embed_url, "image_attribution", "Acquisition-time Flickr license and creator metadata; cached records are not refreshed.")
            meta = json.loads((ROOT / meta_entry["path"]).read_text())
            if meta.get("license_url") != "https://creativecommons.org/licenses/by/2.0/":
                raise ValueError("Stored source license is not the allowed CC BY 2.0 license")
            if not meta.get("author_name") or not meta.get("web_page"):
                raise ValueError("Missing creator attribution")
            annotation = grouped[img["id"]]
            record = {
                "fashionpedia_image_id": img["id"], "fashionpedia_annotation_id": annotation["id"],
                "original_split": "val2020", "project_use": "external_sanity_only_not_training",
                "author": meta["author_name"], "author_url": meta["author_url"],
                "title": meta["title"], "source_page": meta["web_page"],
                "license_url": meta["license_url"], "modifications": "none",
                "download_width": meta["width"], "download_height": meta["height"],
                "annotation_width": img["width"], "annotation_height": img["height"],
                "attributes": [{"id": a, "name": attrs[a]} for a in annotation["attribute_ids"]],
                "geometry_status": "Not registered against Fashionpedia masks; validate resize/alignment before using boxes or masks.",
                "fabric_label": None,
            }
            artifact = acquire(f"fashionpedia/sample_images/{img['id']}.jpg", meta["url"], "image", "CC BY 2.0 confirmed by Flickr oEmbed at acquisition; attribution preserved.", record)
            record.update({"path": artifact["path"], "sha256": artifact["sha256"]})
            samples.append(record)
        except (urllib.error.URLError, ValueError, KeyError, json.JSONDecodeError) as exc:
            manifest["attempts"].append({"at_utc": now(), "fashionpedia_image_id": img["id"], "status": "skipped", "reason": str(exc)[:180]})
            save()
        time.sleep(0.15)
    summary = {
        "generated_at_utc": now(), "images_in_metadata": len(fp["images"]),
        "annotations_in_metadata": len(fp["annotations"]), "skirt_instances": len(skirts),
        "skirt_images": len(grouped), "pleated_skirt_instances": sum(304 in a["attribute_ids"] for a in skirts),
        "skirt_images_marked_cc_by_2_0": len(candidates), "downloaded_image_count": len(samples),
        "samples": samples,
    }
    atomic_write(BASE / "fashionpedia/seed_summary.json", (json.dumps(summary, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    lines = ["# Image attribution", "", "Downloaded without visual edits for local research sanity checks. These are Fashionpedia validation images; do not train on them.", ""]
    for s in samples:
        lines.append(f"- `{s['path']}`: [{s['title']}]({s['source_page']}) by [{s['author']}]({s['author_url']}), [CC BY 2.0]({s['license_url']}). No edits; source dimensions may differ from the annotation image.")
    atomic_write(BASE / "fashionpedia/ATTRIBUTION.md", ("\n".join(lines) + "\n").encode("utf-8"))
    save()
    print(json.dumps({"artifacts": len(manifest["artifacts"]), "images_downloaded": len(samples), "total_bytes": sum(a["size_bytes"] for a in manifest["artifacts"]), "manifest": str(MANIFEST)}, indent=2))


if __name__ == "__main__":
    main()
