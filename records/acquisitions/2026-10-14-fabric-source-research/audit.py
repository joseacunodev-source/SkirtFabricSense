"""Bounded metadata audit. Never downloads images or reads protected splits."""
import collections
import hashlib
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    annotation = ROOT / 'data/external/fashionpedia_train/instances_attributes_train2020.json'
    data = json.loads(annotation.read_text())
    attrs = {a['id']: a for a in data['attributes']}
    images = {i['id']: i for i in data['images']}
    leather = {k for k, a in attrs.items() if a['supercategory'] == 'leather'}
    candidates = []
    for a in data['annotations']:
        selected = sorted(set(a['attribute_ids']) & leather)
        if a['category_id'] != 8 or not selected:
            continue
        im = images[a['image_id']]
        candidates.append(dict(image_id=im['id'], annotation_id=a['id'], source_partition='train2020',
                               attributes=[attrs[k]['name'] for k in selected], license_id=im['license'],
                               original_url=im['original_url'], training_admitted=False,
                               source_group_verified=False, full_skirt_reviewed=False))
    (OUT / 'fashionpedia-leather-subtype-candidates.json').write_text(json.dumps(candidates, indent=2)+'\n')
    join = ROOT / 'records/acquisitions/2026-10-11-fabric-partition/skirt-partition-join.jsonl'
    rows = [json.loads(s) for s in join.read_text().splitlines()]
    counts = []
    for code in sorted({r['lower_fabric_source_code'] for r in rows}):
        train = [r for r in rows if r['official_split']=='train' and r['lower_fabric_source_code']==code]
        counts.append(dict(code=code, train_images=len(train), train_source_items=len({r['official_item_id'] for r in train})))
    sources = {
        'deepfashion-attribute': 'https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion/AttributePrediction.html',
        'deepfashion-terms': 'https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html',
        'fashionpedia-terms': 'https://fashionpedia.github.io/home/data_license.html',
        'attribute-folder': 'https://drive.google.com/drive/folders/0B7EVK8r0v71pWGplNFhjc01NbzQ?resourcekey=0-BU3lAk-Nc7HscJu-CyC1yA',
        'attribute-fine-folder': 'https://drive.google.com/drive/folders/19J-FY5NY7s91SiHpQQBo2ad3xjIB42iN',
        'attribute-coarse-folder': 'https://drive.google.com/drive/folders/0B7EVK8r0v71pWWxJeGVqMjRkUVE?resourcekey=0-sICGfjSkFn6dLpFAwLx8pw',
    }
    observations = []
    for name,url in sources.items():
        try:
            with urllib.request.urlopen(url,timeout=30) as response:
                payload=response.read(2_000_001)
                if len(payload)>2_000_000:
                    raise ValueError('Metadata response exceeds 2 MB cap')
                html=payload.decode('utf-8')
                # Store hashes and visible listing labels, never cookies or login tokens.
                labels=re.findall(r'aria-label="([^"\n]+)" data-handled-by-drag-and-drop',html)
                observations.append(dict(name=name,url=url,status=response.status,bytes=len(payload),
                                         response_sha256=hashlib.sha256(payload).hexdigest(),visible_items=labels))
        except Exception as exc:
            observations.append(dict(name=name,url=url,error=type(exc).__name__+': '+str(exc)))
    report=dict(date='2026-10-14',scope='Metadata-only research; zero images downloaded or admitted',
                fashionpedia_source_sha256=sha(annotation),
                fashionpedia_exact_requested_attributes=[a for a in attrs.values() if a['name'] in ['denim','cotton','chiffon','leather','satin','knitted']],
                fashionpedia_subtype_instances=len(candidates),fashionpedia_subtype_images=len({r['image_id'] for r in candidates}),
                fashionpedia_subtype_counts=dict(collections.Counter(n for r in candidates for n in r['attributes'])),
                fashionpedia_subtype_license_counts=dict(collections.Counter(r['license_id'] for r in candidates)),
                existing_partition_join_sha256=sha(join),deepfashion_multimodal_training_ceiling=counts,
                online_observations=observations)
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
