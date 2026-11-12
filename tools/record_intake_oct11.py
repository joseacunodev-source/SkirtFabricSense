"""Integrate the audited October 11 intake without promoting training labels."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def ref(path): return {'path':path, 'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}

def main():
    registry = read('data/registry.json')
    if registry['updated_date_asia_manila'] == '2026-10-11':
        raise ValueError('Already integrated; do not duplicate history')
    audit_path = 'records/validation/2026-10-11-combined-intake-audit.json'
    audit = read(audit_path)
    if audit['counts']['integrity_errors'] or audit['counts']['records'] != 1627:
        raise ValueError('Unexpected intake audit')
    additions = [
        ('fashionpedia-train2020-negative-candidates', 'data/manifests/negative-candidates-v1.jsonl', 'records/acquisitions/2026-10-11-negatives.json'),
        ('deepfashion-multimodal', 'data/manifests/fullview-fabric-candidates-v1.jsonl', 'records/acquisitions/2026-10-11-fullview-fabric/report.json')]
    for source, manifest, report in additions:
        registry['expansion_acquisitions'].append({'source_id':source, 'manifest':ref(manifest), 'report':ref(report), 'training_admitted':False})
    registry.setdefault('expansion_audit_history', []).append(registry['expansion_audit'])
    registry['expansion_audit'] = ref(audit_path)
    registry['updated_date_asia_manila'] = '2026-10-11'
    registry['status'] = 'negative_and_fullview_fabric_candidates_acquired_not_admitted'
    registry['downloaded_totals'].update(photographs=1627, unique_file_hashes=1627,
        unique_decoded_pixel_hashes=1627, negative_source_candidates=90, fullview_fabric_source_candidates=25)
    metadata = registry['supplementary_metadata'][0]
    metadata['evidence'].append(ref('records/review/2026-10-11-fabric-partition.json'))
    metadata['complete_images_added'] = 25
    metadata['partition_status'] = 'all_848_exactly_joined_367_train_224_query_257_gallery'
    registry.setdefault('diagnostic_evaluations', []).append(ref('records/validation/2026-10-11-negative-diagnostic.json'))
    (ROOT/'data/registry.json').write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    review = {'date_asia_manila':'2026-10-11', 'reviewer':'codex_root_visual_review',
              'independent_human_review':False, 'training_admitted':False,
              'negative_sheet_review':{'images_seen':90, 'sheet_manifest':ref('records/acquisitions/2026-10-11-negatives/contact-sheets.json'),
                  'observations':['Pants, shorts and dresses are visible in sampled subjects',
                      'Some figures are cropped, occluded by coats, seated or surrounded by other people',
                      'Thumbnails cannot certify skirt absence or garment identity; no hard-negative truth assigned']},
              'fabric_sheet_review':{'images_seen':25, 'sheet':ref('records/acquisitions/2026-10-11-fullview-fabric/contact-sheet.jpg'),
                  'position_map':ref('records/acquisitions/2026-10-11-fullview-fabric/contact-sheet.json'),
                  'observations':['Source lower-clothing appearance is not fiber composition',
                      'Some waistbands are hidden by tops; a seated example changes visible garment geometry',
                      'Source worn images do not validate held/hanging/mannequin modes'],
                  'full_resolution_followup':{'sample_id':'deepfashion-multimodal-WOMEN-Skirts-id_00004335-02_1_front',
                      'finding':'Thumbnail suggested shorts; full-resolution image shows a continuous denim skirt hem. Initial suspicion corrected; no exclusion applied.'}}}
    with (ROOT/'records/review/2026-10-11-intake-visual.json').open('x',encoding='utf-8') as stream:
        json.dump(review, stream, indent=2)
    new_pairs = [pair for pair in audit['near_duplicate_candidates'] if any('negative-candidate' in s or 'deepfashion-multimodal' in s for s in pair['sample_ids'])]
    print(json.dumps({'original_images':1627, 'integrity_errors':0, 'new_near_duplicate_pairs':len(new_pairs), 'pairs':new_pairs}))

if __name__ == '__main__': main()
