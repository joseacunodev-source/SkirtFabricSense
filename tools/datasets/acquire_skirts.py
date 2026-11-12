"""Acquire bounded, original Fashionpedia train2020 skirt images via ZIP ranges.

No ZIP code is executed. Keep source partitions and original image bytes. Requires
existing Pillow solely to decode intake images. No packages are installed here.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import random
import struct
import tempfile
import time
import urllib.request
import zlib

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data/external/fashionpedia_train"
MANIFEST = ROOT / "data/manifests/skirt_candidates.jsonl"
REPORT = ROOT / "records/acquisitions/skirt_expansion.json"
ARCHIVE = "https://s3.amazonaws.com/ifashionist-dataset/images/train2020.zip"
ANNOTATIONS = "https://s3.amazonaws.com/ifashionist-dataset/annotations/instances_attributes_train2020.json"
TERMS = "https://fashionpedia.github.io/home/data_license.html"


def digest(b):
    return hashlib.sha256(b).hexdigest()


def atomic(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
            name = f.name
            f.write(body)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def save_json(path, value):
    atomic(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())


def request(url, start=None, end=None, cap=16 * 1024 * 1024):
    headers = {"User-Agent": "SkirtFabricSense-research-acquisition/1.0"}
    if start is not None:
        headers["Range"] = f"bytes={start}-{end}"
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45) as r:
                if start is not None:
                    expected = f"bytes {start}-{end}/"
                    if r.status != 206 or not r.headers.get("Content-Range", "").startswith(expected):
                        raise ValueError("Server did not honor exact bounded byte range")
                b = r.read(cap + 1)
                if len(b) > cap:
                    raise ValueError("Response exceeds byte cap")
                if start is not None and len(b) != end - start + 1:
                    raise ValueError("Truncated range")
                return b
        except Exception as exc:
            last = exc
            time.sleep(attempt + 1)
    raise last


def get_index():
    with urllib.request.urlopen(urllib.request.Request(ARCHIVE, method="HEAD"), timeout=45) as r:
        size = int(r.headers["Content-Length"])
        etag = r.headers.get("ETag")
    tail = request(ARCHIVE, size - 65536, size - 1)
    pos = tail.rfind(b"PK\x05\x06")
    if pos < 0:
        raise ValueError("Missing ZIP end record")
    end = struct.unpack_from("<4s4H2LH", tail, pos)
    count, cdsize, offset = end[4:7]
    if cdsize > 16 * 1024 * 1024 or offset + cdsize > size:
        raise ValueError("Unsupported/unsafe central directory bounds")
    central = request(ARCHIVE, offset, offset + cdsize - 1)
    atomic(BASE / "archive_central_directory.bin", central)
    index = {}
    i = 0
    while i < len(central):
        fields = struct.unpack_from("<4s6H3L5H2L", central, i)
        if fields[0] != b"PK\x01\x02":
            raise ValueError("Invalid central directory signature")
        n, e, c = fields[10:13]
        name = central[i+46:i+46+n].decode("utf-8")
        if name in index:
            raise ValueError("Duplicate archive member")
        index[name] = {"offset": fields[-1], "compressed": fields[8],
                       "size": fields[9], "crc": fields[7], "compression": fields[4]}
        i += 46+n+e+c
    if len(index) != count:
        raise ValueError("Central directory member count mismatch")
    save_json(BASE / "archive_index.json", index)
    return index, {"url": ARCHIVE, "size_bytes": size, "etag": etag,
                   "central_directory_sha256": digest(central), "member_count": count}


def extract(member, entry):
    if entry["size"] > 16*1024*1024 or entry["compressed"] > 16*1024*1024:
        raise ValueError("Member exceeds 16MiB bound")
    # One bounded request includes local header/name/extra and compressed bytes.
    offset = entry["offset"]
    b = request(ARCHIVE, offset, offset+entry["compressed"]+4095, cap=17*1024*1024)
    fields = struct.unpack_from("<4s5H3L2H", b)
    if fields[0] != b"PK\x03\x04" or fields[2] & 1:
        raise ValueError("Unsupported encrypted/invalid ZIP member")
    n, e = fields[-2:]
    if b[30:30+n].decode("utf-8") != member:
        raise ValueError("ZIP member identity mismatch")
    start = 30+n+e
    compressed = b[start:start+entry["compressed"]]
    if entry["compression"] == 8:
        decoder = zlib.decompressobj(-15)
        result = decoder.decompress(compressed, entry["size"]+1)
        if not decoder.eof or decoder.unconsumed_tail:
            raise ValueError("Invalid/oversized compressed member")
    elif entry["compression"] == 0:
        result = compressed
    else:
        raise ValueError("Unsupported compression")
    if len(result) != entry["size"] or zlib.crc32(result) != entry["crc"]:
        raise ValueError("ZIP content length/CRC mismatch")
    return result


def validate_image(body, meta):
    with Image.open(io.BytesIO(body)) as im:
        im.load()
        if im.size != (meta["width"], meta["height"]):
            raise ValueError("Decoded dimensions differ from official annotations")
        return im.size


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.count <= 2000 or not 1 <= args.workers <= 16:
        parser.error("Bound count to 1..2000 and workers to 1..16")
    existing = [json.loads(x) for x in MANIFEST.read_text().splitlines()] if MANIFEST.exists() else []
    for item in existing:
        p = (ROOT/item["original_path"]).resolve()
        if not p.is_relative_to(BASE.resolve()):
            raise ValueError("Manifest path outside source directory")
        b = p.read_bytes()
        if digest(b) != item["sha256"]:
            raise ValueError(f"Cached hash mismatch {p}")
        validate_image(b,item)
    if args.verify_only:
        print(json.dumps({"verified_images":len(existing),"unique_hashes":len({x['sha256'] for x in existing}),"network_used":False}))
        return
    BASE.mkdir(parents=True, exist_ok=True)
    annpath = BASE/"instances_attributes_train2020.json"
    if not annpath.exists():
        # Large annotations are streamed to a temporary file, never partially cached.
        temp = annpath.with_suffix(".download")
        try:
            with urllib.request.urlopen(ANNOTATIONS,timeout=60) as response, temp.open("wb") as out:
                total = 0
                while chunk := response.read(1024*1024):
                    total += len(chunk)
                    if total > 650*1024*1024:
                        raise ValueError("Annotations exceed bounded 650MiB download")
                    out.write(chunk)
            json.loads(temp.read_text())
            os.replace(temp,annpath)
        finally:
            if temp.exists(): temp.unlink()
    data = json.loads(annpath.read_text())
    assert next(c for c in data["categories"] if c["id"]==8)["name"] == "skirt"
    annotations = defaultdict(list)
    for a in data["annotations"]:
        if a["category_id"]==8: annotations[a["image_id"]].append(a)
    attrs = {a["id"]:a for a in data["attributes"]}
    licenses = {x["id"]:x for x in data["licenses"]}
    candidates = [i for i in data["images"] if len(annotations[i["id"]])==1]
    random.Random(20261002).shuffle(candidates)
    # Prefer explicitly licensed sources, then retain genuine archive metadata for all others.
    candidates.sort(key=lambda x: (0 if "creativecommons" in licenses[x["license"]].get("url","") else 1))
    index, archive_evidence = get_index()
    termbody = request(TERMS)
    atomic(BASE/"terms_snapshot.html",termbody)
    chosen = existing[:]
    used_ids = {x["source_item_id"] for x in chosen}
    used_hashes = {x["sha256"] for x in chosen}
    errors = []

    def obtain(meta):
        filename = meta["file_name"]
        if Path(filename).name != filename:
            raise ValueError("Unexpected image filename")
        member = "train/"+filename
        dest = BASE/"images"/filename
        body = dest.read_bytes() if dest.exists() else extract(member,index[member])
        width,height = validate_image(body,meta)
        # A cache must match the canonical archive checksum, even before manifest admission.
        if len(body)!=index[member]["size"] or zlib.crc32(body)!=index[member]["crc"]:
            raise ValueError("Existing image does not match archive CRC")
        atomic(dest,body)
        ann=annotations[meta["id"]][0]
        source_url=meta["original_url"]
        return {"schema_version":1,"sample_id":f"fashionpedia-train2020-{meta['id']}",
                "original_path":dest.relative_to(ROOT).as_posix(),"sha256":digest(body),"size_bytes":len(body),
                "source_id":"fashionpedia-train2020","source_partition":"train2020","source_item_id":str(meta["id"]),
                "source_url":source_url,"download_url":ARCHIVE,"archive_member":member,
                "terms_reference":[TERMS,licenses[meta["license"]].get("url","")],
                "source_license":licenses[meta["license"]],"terms_status":"source_license_record_preserved_not_blanket_annotation_license",
                "annotation_reference":annpath.relative_to(ROOT).as_posix(),
                "group_id":"fashionpedia-source-"+digest(source_url.encode())[:20],
                "garment_id":None,"parent_sample_id":None,"grouping_review_pending":True,
                "width":width,"height":height,"source_labels":{"category":"skirt","annotation_id":ann["id"],
                "bbox":ann["bbox"],"segmentation":ann["segmentation"],"attribute_ids":ann["attribute_ids"],
                "attributes":[attrs[x] for x in ann["attribute_ids"]]},
                "project_labels":{"source_skirt_presence":{"value":"skirt","status":"approved",
                "evidence":f"Official train2020 category 8 annotation {ann['id']}; original archive dimensions and CRC verified"}},
                "training_eligibility":{"source_skirt_presence":{"approved":True,"reason":"Official source annotation for auxiliary skirt localization/presence only; group audit required before split"}},
                "project_fabric_label":None,"project_length_label":None,"project_style_label":None,
                "acquired_at_utc":datetime.now(timezone.utc).isoformat()}

    remaining=[x for x in candidates if str(x["id"]) not in used_ids]
    # Batches bound overfetch; successful records are atomically persisted every batch.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        cursor=0
        while len(chosen)<args.count and cursor<len(remaining):
            batch=remaining[cursor:cursor+min(args.workers,args.count-len(chosen))]
            cursor+=len(batch)
            jobs={pool.submit(obtain,i):i for i in batch}
            for job in as_completed(jobs):
                try:
                    item=job.result()
                    if item["sha256"] in used_hashes:
                        errors.append({"image_id":item["source_item_id"],"error":"exact_duplicate_not_counted"})
                        continue
                    chosen.append(item);used_hashes.add(item["sha256"])
                except Exception as exc:
                    errors.append({"image_id":jobs[job]["id"],"error":str(exc)})
            chosen.sort(key=lambda x:int(x["source_item_id"]))
            atomic(MANIFEST,("\n".join(json.dumps(x,ensure_ascii=False) for x in chosen)+"\n").encode())
            print(f"Acquired {len(chosen)}/{args.count}; errors {len(errors)}",flush=True)
    subset_ids={int(x["source_item_id"]) for x in chosen}
    subset={k:data[k] for k in ("info","categories","attributes","licenses")}
    subset["images"]=[i for i in data["images"] if i["id"] in subset_ids]
    subset["annotations"]=[a for a in data["annotations"] if a["image_id"] in subset_ids]
    save_json(BASE/"selected_annotations.json",subset)
    report={"schema_version":1,"completed_at_utc":datetime.now(timezone.utc).isoformat(),
            "requested_images":args.count,"images":len(chosen),"unique_content_hashes":len(used_hashes),
            "verified_physical_garments":None,"verified_project_fabric_labels":0,
            "image_bytes":sum(x["size_bytes"] for x in chosen),"original_partition":"train2020",
            "candidate_single_skirt_images":len(candidates),"manifest":MANIFEST.relative_to(ROOT).as_posix(),
            "manifest_sha256":digest(MANIFEST.read_bytes()),"archive":archive_evidence,
            "annotations":{"url":ANNOTATIONS,"path":annpath.relative_to(ROOT).as_posix(),"size_bytes":annpath.stat().st_size,"sha256":digest(annpath.read_bytes())},
            "terms":{"url":TERMS,"sha256":digest(termbody)},
            "license_counts":dict(Counter(x["source_license"]["name"] for x in chosen)),
            "attribute_counts":dict(Counter(a["name"] for x in chosen for a in x["source_labels"]["attributes"])),
            "errors":errors,"sampling":"Seed 20261002, single source skirt instance, Creative Commons prioritized; not a representative or balanced benchmark",
            "verification":"JPEG decode, dimensions matching annotations, ZIP CRC, SHA256, source partition; physical garment grouping and visual suitability review remain pending",
            "source_code_sha256":digest(Path(__file__).read_bytes()),"python_pillow_used":"Existing host environment; no new installation"}
    save_json(REPORT,report)
    print(json.dumps({k:report[k] for k in ("images","image_bytes","license_counts","attribute_counts")}))


if __name__ == "__main__":
    main()
