"""Merge explicit presentation observations while preserving earlier review files."""
import argparse
import hashlib
import json
from pathlib import Path


def merge(previous, batches, overrides):
    records = {}
    for row in [*previous, *batches]:
        if row['sample_id'] in records:
            raise ValueError('Duplicate review identity')
        records[row['sample_id']] = row
    overridden = set()
    for row in overrides:
        sid = row['sample_id']
        if (sid not in records or sid in overridden
                or row['image_sha256'] != records[sid]['image_sha256']
                or row['original_path'] != records[sid]['original_path']
                or row['review_method'] != 'original_image_visual_inspection'):
            raise ValueError('Invalid full-original review override')
        overridden.add(sid)
        records[sid] = row
    return list(records.values())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous', type=Path, required=True)
    p.add_argument('--batch', type=Path, action='append', required=True)
    p.add_argument('--overrides', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    paths = [a.previous, *a.batch, a.overrides]
    def read(path):
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    rows = merge(read(a.previous), [row for path in a.batch for row in read(path)], read(a.overrides))
    if a.output.exists() or a.output.with_suffix('.sources.json').exists():
        raise FileExistsError('Choose a fresh output path')
    with a.output.open('x', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    provenance = {'inputs': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
                  'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'output_sha256': hashlib.sha256(a.output.read_bytes()).hexdigest(), 'observations': len(rows),
                  'scope': 'Supplemental agent presentation observations; no frozen labels or splits changed'}
    with a.output.with_suffix('.sources.json').open('x', encoding='utf-8') as stream:
        json.dump(provenance, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'observations': len(rows)}))


if __name__ == '__main__':
    main()
