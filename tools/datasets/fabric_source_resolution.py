"""Bounded metadata-only investigation of the official NPCGA garment source.

Never fetches photographs or archives and never admits rows to training.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
import urllib.request

API = 'https://zenodo.org/api/records/20440761'
ALLOWED = {'NPCGA_datatable_1.1.csv': 6_000_000,
           'README_for_datatable.pdf': 500_000}


def analyze_table(data):
    rows = list(csv.DictReader(io.StringIO(data.decode('utf-8-sig')), delimiter=';'))
    required = {'ID (AXXXX)', 'Product type (#)', 'Care Label Present (0,1)',
                'Readable label (0,1)', 'Fibre 1 Layer 1', 'Area'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('missing required source fields')
    ids = [row['ID (AXXXX)'] for row in rows]
    if len(set(ids)) != len(ids) or any(not item for item in ids):
        raise ValueError('missing or duplicate source item IDs')
    skirts = [row for row in rows if row['Product type (#)'] == '9']
    missing = {'', 'NaN', 'nan', 'unknown'}
    first = Counter(row['Fibre 1 Layer 1'] for row in skirts)
    known = sum(row['Care Label Present (0,1)'] == '1' and
                row['Readable label (0,1)'] == '1' and
                row['Fibre 1 Layer 1'] not in missing for row in skirts)
    summary = {'source_rows': len(rows), 'unique_source_item_ids': len(set(ids)),
               'skirt_metadata_rows': len(skirts),
               'skirt_by_collection_area': dict(Counter(row['Area'] for row in skirts)),
               'first_fibre_outer_layer_raw_counts': dict(first),
               'skirts_with_present_readable_label_and_first_fibre': known,
               'original_images_downloaded': 0, 'training_admissions': 0,
               'image_item_join_verified': False, 'worn_presentation_verified': False,
               'appearance_label_conversion_performed': False,
               'original_split': 'not supplied in metadata record; no project split assigned'}
    return summary, skirts


def fetch(url, cap):
    request = urllib.request.Request(url, headers={'User-Agent': 'SkirtFabricSense-source-audit/1'})
    with urllib.request.urlopen(request, timeout=45) as response:
        if int(response.headers.get('Content-Length', '0')) > cap:
            raise ValueError('response exceeds byte cap')
        data = response.read(cap + 1)
    if len(data) > cap:
        raise ValueError('response exceeds byte cap')
    return data


def acquire(output):
    output.mkdir(parents=True, exist_ok=False)
    raw = fetch(API, 1_000_000)
    record = json.loads(raw)
    (output / 'zenodo-record.json').write_bytes(raw)
    acquired = []
    for entry in record['files']:
        name = entry['key']
        if name not in ALLOWED:
            continue
        if entry['size'] > ALLOWED[name]:
            raise ValueError('published size exceeds byte cap')
        url = entry['links']['self']
        if not url.startswith(API + '/files/'):
            raise ValueError('unexpected download origin')
        data = fetch(url, ALLOWED[name])
        if len(data) != entry['size']:
            raise ValueError('published size mismatch')
        if entry['checksum'] != 'md5:' + hashlib.md5(data).hexdigest():
            raise ValueError('publisher checksum mismatch')
        (output / name).write_bytes(data)
        acquired.append({'path': str(output / name).replace('\\', '/'),
                         'source_url': url, 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(),
                         'publisher_checksum_verified': entry['checksum']})
    report = {'date': '2026-10-17', 'source': API,
              'license': record['metadata'].get('license'),
              'original_images_downloaded': 0, 'training_admissions': 0,
              'metadata': acquired,
              'record_sha256': hashlib.sha256(raw).hexdigest(),
              'no_archives_requested': True}
    (output / 'acquisition.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    summary, skirts = analyze_table((output / 'NPCGA_datatable_1.1.csv').read_bytes())
    (output / 'feasibility.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (output / 'skirt-metadata-candidates.jsonl').write_text(
        ''.join(json.dumps({'source_item_id': row['ID (AXXXX)'], 'source_row': row,
                            'training_eligible': False, 'image_acquired': False,
                            'group_id_proposal': 'NPCGA:' + row['ID (AXXXX)']}) + '\n'
                for row in skirts), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--analyze', action='store_true')
    args = parser.parse_args()
    if args.analyze:
        data = (args.output / 'NPCGA_datatable_1.1.csv').read_bytes()
        acquisition = json.loads((args.output / 'acquisition.json').read_text(encoding='utf-8'))
        binding = next(entry for entry in acquisition['metadata']
                       if entry['path'].endswith('/NPCGA_datatable_1.1.csv'))
        if len(data) != binding['bytes'] or hashlib.sha256(data).hexdigest() != binding['sha256']:
            raise ValueError('saved table does not match acquisition binding')
        summary, skirts = analyze_table(data)
        (args.output / 'feasibility.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        (args.output / 'skirt-metadata-candidates.jsonl').write_text(
            ''.join(json.dumps({'source_item_id': row['ID (AXXXX)'], 'source_row': row,
                               'training_eligible': False, 'image_acquired': False,
                               'group_id_proposal': 'NPCGA:' + row['ID (AXXXX)']}) + '\n'
                    for row in skirts), encoding='utf-8')
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(acquire(args.output), indent=2))
