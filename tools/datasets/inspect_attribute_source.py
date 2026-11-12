"""Bounded official metadata feasibility intake; never downloads images or test labels."""
from pathlib import Path
import hashlib
import json
import re
import urllib.request
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'records/acquisitions/2026-10-14-attribute-metadata'
FOLDER = 'https://drive.google.com/drive/folders/19J-FY5NY7s91SiHpQQBo2ad3xjIB42iN'
LIMIT = 100_000_000

def parse_dictionary(text):
    lines = text.splitlines()
    rows = [line.split() for line in lines[2:] if line.strip()]
    if len(rows) != int(lines[0]) or any(len(row) != 2 for row in rows):
        raise ValueError('Malformed dictionary')
    names = [row[0] for row in rows]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate dictionary name')
    return rows


def summarize(paths, categories, attributes, category_names, attribute_names):
    if not len(paths) == len(categories) == len(attributes):
        raise ValueError('Parallel training files have different row counts')
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate image path')
    fabric_indices = [i for i, row in enumerate(attribute_names) if row[1] == '5']
    skirt_code = [row[0] for row in category_names].index('Skirt') + 1
    candidates = []
    for path, category, values in zip(paths, categories, attributes):
        if not re.fullmatch(r'img/[^/\\]+/img_\d+\.jpg', path) or '..' in path.split('/'):
            raise ValueError('Unexpected image path')
        if not 1 <= category <= len(category_names):
            raise ValueError('Category index out of range')
        if len(values) != len(attribute_names) or any(v not in (0, 1) for v in values):
            raise ValueError('Invalid binary attribute row')
        if category == skirt_code:
            candidates.append(dict(source_path=path, source_partition='Anno_fine/train',
                source_folder_token=path.split('/')[1],
                source_fabric_attributes=[attribute_names[i][0] for i in fabric_indices if values[i]],
                training_eligible=False))
    counts = {}
    for i in fabric_indices:
        name = attribute_names[i][0]
        selected = [r for r in candidates if name in r['source_fabric_attributes']]
        counts[name] = dict(image_references=len(selected),
            folder_tokens=len({r['source_folder_token'] for r in selected}))
    return dict(training_rows=len(paths), skirt_image_references=len(candidates),
        skirt_folder_tokens=len({r['source_folder_token'] for r in candidates}),
        fabric_counts=counts,
        fabric_label_cardinality=dict(sorted(Counter(len(r['source_fabric_attributes']) for r in candidates).items()))), candidates


def analyze(directory=OUT):
    acquisition = json.loads((directory/'report.json').read_text(encoding='utf-8'))
    names = ['list_attr_cloth.txt', 'list_category_cloth.txt', 'train.txt', 'train_cate.txt', 'train_attr.txt']
    source_files = []
    texts = {}
    for name in names:
        payload = (directory/name).read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        matches = [r for r in acquisition['observations'] if r.get('name') == name and r.get('sha256') == digest and r.get('bytes') == len(payload)]
        if len(matches) != 1:
            raise ValueError('Acquisition hash/size mismatch: ' + name)
        source_files.append(dict(name=name, sha256=digest, bytes=len(payload), url=matches[0]['url']))
        texts[name] = payload.decode('utf-8-sig')
    report, candidates = summarize(texts['train.txt'].splitlines(),
        [int(v) for v in texts['train_cate.txt'].splitlines()],
        [[int(v) for v in line.split()] for line in texts['train_attr.txt'].splitlines()],
        parse_dictionary(texts['list_category_cloth.txt']), parse_dictionary(texts['list_attr_cloth.txt']))
    manifest = directory/'skirt-attribute-references.jsonl'
    manifest.write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in candidates), encoding='utf-8')
    report.update(date='2026-10-15', source_files=source_files,
        acquisition_report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        references_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
        original_images_downloaded=0, samples_admitted=0, test_labels_accessed=False,
        source_partition='Anno_fine/train; original broader benchmark membership not joined',
        limitations=['Folder tokens are descriptive titles, not verified garment identities.',
            'No images inspected; full-skirt visibility and duplicate identity remain unknown.',
            'Source material attributes do not establish fiber composition or project labels.',
            'Parallel rows are joined by publisher row order; no image bytes or original benchmark split join verified.',
            'Noncommercial research/internal copies only; do not redistribute source data.'])
    (directory/'feasibility.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


def join_partitions(text, rows):
    lines = text.splitlines()
    mapping = {}
    folder_splits = {}
    for line in lines[2:]:
        fields = line.split()
        if len(fields) != 2 or fields[1] not in ('train', 'val', 'test'):
            raise ValueError('Invalid original partition row')
        path, split = fields
        if path in mapping:
            raise ValueError('Duplicate original partition path')
        mapping[path] = split
        folder_splits.setdefault(str(Path(path).parent).replace('\\', '/'), set()).add(split)
    if len(mapping) != int(lines[0]):
        raise ValueError('Original partition count mismatch')
    joined = []
    for row in rows:
        path = row['source_path']
        if path not in mapping:
            raise ValueError('Missing original partition match: ' + path)
        splits = sorted(folder_splits[str(Path(path).parent).replace('\\', '/')])
        joined.append(dict(row, original_benchmark_split=mapping[path],
            folder_original_partitions=splits,
            acquisition_eligible=mapping[path] == 'train' and splits == ['train'],
            physical_garment_identity_verified=False,
            conservative_group_id='deepfashion-attribute-folder:' + row['source_folder_token']))
    return joined, len(mapping)


def partition_analysis(directory=OUT):
    url = 'https://drive.google.com/uc?export=download&id=0B7EVK8r0v71pdS1FMlNreEwtc1E&resourcekey=0-_AL8Vhcl1UUYuw7NbGnZtA'
    target = directory/'original-partitions.txt'
    if not target.exists():
        with urllib.request.urlopen(url, timeout=45) as response:
            payload = response.read(30_000_001)
            if len(payload) > 30_000_000 or b'<html' in payload[:1000].lower():
                raise ValueError('Partition metadata invalid or exceeds budget')
        target.write_bytes(payload)
    payload = target.read_bytes()
    reference_path = directory/'skirt-attribute-references.jsonl'
    joined, total = join_partitions(payload.decode('utf-8-sig'),
        [json.loads(line) for line in reference_path.read_text(encoding='utf-8').splitlines()])
    output = directory/'skirt-original-partition-join.jsonl'
    output.write_text(''.join(json.dumps(row, sort_keys=True)+'\n' for row in joined), encoding='utf-8')
    eligible = [row for row in joined if row['acquisition_eligible']]
    report = dict(date='2026-10-15', partition_url=url, partition_bytes=len(payload),
        partition_sha256=hashlib.sha256(payload).hexdigest(), original_partition_rows=total,
        source_reference_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        join_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        source_revision_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        joined_rows=len(joined), original_splits=dict(Counter(r['original_benchmark_split'] for r in joined)),
        acquisition_eligible_rows=len(eligible), acquisition_eligible_folder_tokens=len({r['source_folder_token'] for r in eligible}),
        eligible_fabric_counts=dict(Counter(label for r in eligible for label in r['source_fabric_attributes'])),
        folder_cross_partition_exclusions=sum(r['original_benchmark_split']=='train' and not r['acquisition_eligible'] for r in joined),
        original_images_downloaded=0, samples_admitted=0, separately_requested_test_attribute_files=False,
        broader_holdout_attribute_rows_previously_loaded=sum(r['original_benchmark_split'] != 'train' for r in joined),
        exposure_note='Anno_fine/train attribute rows were previously loaded before the broader split join; 66 validation and 192 test image references are included. No model used these rows.',
        policy='Only original train with train-only descriptive folder group eligible for later image acquisition; all training admission remains false.')
    (directory/'partition-feasibility.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    observations = []
    total = 0
    def fetch(name, url, cap):
        nonlocal total
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                chunks = []
                size = 0
                while True:
                    part = response.read(min(65536, cap-size+1, LIMIT-total+1))
                    if not part:
                        break
                    size += len(part)
                    total += len(part)
                    if size > cap or total > LIMIT:
                        raise ValueError('Metadata byte budget exceeded')
                    chunks.append(part)
                payload = b''.join(chunks)
                observations.append(dict(name=name, url=url, bytes=size, status=response.status,
                    sha256=hashlib.sha256(payload).hexdigest(), content_type=response.headers.get('Content-Type')))
                if name.endswith('.txt') and b'<html' in payload[:1000].lower():
                    raise ValueError('HTML response is not metadata; no access workaround attempted')
                (OUT/name).write_bytes(payload)
                return payload.decode('utf-8-sig')
        except Exception as exc:
            observations.append(dict(name=name, url=url, error=type(exc).__name__ + ': ' + str(exc)))
            return None
    listing = fetch('folder.html', FOLDER, 2_000_000)
    items = dict((name, fileid) for fileid, name in re.findall(
        r'data-id="([\w-]+)" jsname="vtaz5c"[^>]*data-tooltip="([^"]+) Text"', listing or ''))
    # Only original-training labels and dictionaries; no val/test labels.
    for name in ['list_attr_cloth.txt', 'list_category_cloth.txt', 'train.txt', 'train_cate.txt', 'train_attr.txt']:
        if name not in items:
            observations.append(dict(name=name, error='Not found in official listing'))
            continue
        fetch(name, 'https://drive.google.com/uc?export=download&id=' + items[name], 60_000_000)
    report = dict(date='2026-10-14', original_images_downloaded=0, samples_admitted=0,
        downloaded_bytes=total, byte_budget=LIMIT, official_folder=FOLDER, visible_metadata=items,
        observations=observations, terms_url='https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html',
        restrictions='Noncommercial research; no redistribution; internal same-organization copies only.',
        test_labels_accessed=False, source_revision_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze', action='store_true', help='Analyze existing verified metadata offline')
    parser.add_argument('--join-partitions', action='store_true', help='Fetch bounded original partition metadata and join, no images or attribute labels')
    args = parser.parse_args()
    if args.join_partitions:
        print(json.dumps(partition_analysis(), indent=2))
    elif args.analyze:
        print(json.dumps(analyze(), indent=2))
    else:
        main()
