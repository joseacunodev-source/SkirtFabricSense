"""Register verified second-intake originals without promoting training labels."""
import hashlib
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def ref(path):
    return {'path':path, 'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--negative-only', action='store_true')
    args = parser.parse_args()
    registry = read('data/registry.json')
    audit_path = 'records/validation/2026-10-13-expansion-v2-audit.json'
    audit = read(audit_path)
    if audit['counts']['integrity_errors']:
        raise ValueError('Intake integrity failed')
    additions = [
        ('fashionpedia-train2020-negative-candidates-v2', 'data/manifests/negative-candidates-v2.jsonl',
         'records/acquisitions/2026-10-13-negatives-v2/report.json'),
        ('deepfashion-multimodal-v2', 'data/manifests/fullview-fabric-candidates-v2.jsonl',
         'records/acquisitions/2026-10-13-fabric-v2/report.json')]
    if args.negative_only:
        additions = additions[:1]
    current = {item['manifest']['path'] for item in registry['expansion_acquisitions']}
    if any(manifest in current for _,manifest,_ in additions):
        raise ValueError('Expansion already registered; do not count twice')
    counts = []
    for source, manifest, report in additions:
        rows = [json.loads(line) for line in (ROOT/manifest).read_text().splitlines() if line.strip()]
        if not rows:
            raise ValueError('Cannot register an empty acquisition')
        reference = next(item for item in audit['input_manifests'] if item['path']==manifest)
        if reference != ref(manifest):
            raise ValueError('Manifest changed after audit')
        registry['expansion_acquisitions'].append({'source_id':source, 'manifest':ref(manifest),
            'report':ref(report), 'training_admitted':False})
        counts.append(len(rows))
    if registry['downloaded_totals']['photographs'] + sum(counts) != audit['counts']['records']:
        raise ValueError('Combined audit count does not reconcile')
    registry.setdefault('expansion_audit_history',[]).append(registry['expansion_audit'])
    registry['expansion_audit']=ref(audit_path)
    totals=registry['downloaded_totals']
    totals['photographs']=audit['counts']['records']
    totals['unique_file_hashes']=audit['counts']['unique_file_hashes']
    totals['unique_decoded_pixel_hashes']=audit['counts']['unique_decoded_pixel_hashes']
    totals['negative_source_candidates']+=counts[0]
    totals['fullview_fabric_source_candidates']+=counts[1] if len(counts)>1 else 0
    for source in registry.get('supplementary_metadata',[]):
        if source.get('source')=='DeepFashion-MultiModal':
            source['complete_images_added']=totals['fullview_fabric_source_candidates']
            source['new_v2_candidates_training_admitted']=False
    registry['updated_date_asia_manila']='2026-10-13'
    registry['status']='expanded_candidates_audited_review_pending_existing_pilots_not_promoted'
    (ROOT/'data/registry.json').write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'registered':counts,'originals':totals['photographs'],'new_training_admission':False}))


if __name__=='__main__':
    main()
