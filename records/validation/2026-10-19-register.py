"""Register the recovered October18 data/exports after October19 verification."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def ref(path):
    return {'path':path,'sha256':hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def write(path, record, exclusive=False):
    with (ROOT / path).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as stream:
        json.dump(record,stream,indent=2,ensure_ascii=False); stream.write('\n')


def model_record(version, comparison_path):
    folder = f'artifacts/models/skirt-presence-{version}'
    archive = f'records/experiments/20261018-presence-{version}'
    run, comparison = load(folder+'/run.json'), load(comparison_path)
    model = ref(folder+'/model.tflite')
    if (run['status'] != 'completed' or comparison['status'] != 'completed'
            or model['sha256'] != run['export']['sha256']
            or model['sha256'] != comparison['models']['presence']
            or comparison['inputs_sha256'] != run['frozen_inputs_sha256']):
        raise ValueError('Incomplete or inconsistent research export')
    record = load('templates/model-release.json')
    record.update(release_id=f'skirt-presence-{version}',
        status='exported_development_candidate_not_deployment_approved',
        source_run_id=f'20261018-presence-{version}',
        model_files_and_sha256=[model,ref(folder+'/model.keras')],
        labels_in_output_order=['skirt_presence_probability'],
        input_output_tensor_contract={'input':{'shape':[1,224,224,3],'dtype':'float32'},
                                      'output':{'shape':[1,1],'dtype':'float32'}},
        preprocessing_version=run['preprocessing'],patch_strategy='Full source frame; no manual ROI',
        quantization_parameters=None,calibration_dataset_hash=None,
        thresholds_and_temporal_settings={'presence':.5,'mask':.5,'temporal_settings_changed':False},
        training_environment=ref(archive+'/environment.json'),
        conversion_environment=ref(archive+'/environment.json'),target_environment=None,
        pre_export_metrics=run['metrics'],post_export_metrics=comparison['metrics'],
        pi_validation_record=None,camera_calibration_id=None,
        known_limitations=run['limitations']+comparison['limitations'],
        rollback_release_id='skirt-finetune-v1-desktop-research-v7',
        executed_run=ref(archive+'/run.json'),input_manifest=ref(archive+'/inputs.json'),
        split_hash=run['split_hash'],selected_epoch=run['selected_epoch'],selection=run['selection'],
        early_export=run['early_export'],final_export=run['export'],comparison=ref(comparison_path),
        development_criteria_passed=comparison['development_criteria_passed'],
        deployment_approved=False,pi_verified=False)
    path = f'records/models/2026-10-18-skirt-presence-{version}.json'
    write(path,record,True)
    return ref(path)


def main():
    audit_path = 'records/validation/2026-10-18-combined-intake-audit.json'
    audit = load(audit_path)
    counts = audit['counts']
    if (counts['records'] != 1932 or counts['decoded_images'] != 1932
            or counts['unique_file_hashes'] != 1932
            or counts['unique_decoded_pixel_hashes'] != 1932 or counts['integrity_errors']):
        raise ValueError('Combined original audit failed')
    registry = load('data/registry.json')
    registry['updated_date_asia_manila'] = '2026-10-19'
    registry['status'] = 'negative_v3_frozen_presence_followup_exported_fabric_pilot_unadmitted'
    totals = registry['downloaded_totals']
    totals.update(photographs=1932,unique_file_hashes=1932,unique_decoded_pixel_hashes=1932,
                  composition_source_pilot_originals=5)
    totals['note'] = 'Original images only; five NPCGI originals include one dress/category conflict and two visibility exclusions; no verified physical specimen count.'
    registry['expansion_audit_history'].append(registry['expansion_audit'])
    registry['expansion_audit'] = ref(audit_path)
    registry['expansion_acquisitions'].append({
        'source_id':'ntnu-npcgi-1.1-five-image-pilot',
        'manifest':ref('data/manifests/npcgi-pilot-candidates.jsonl'),
        'report':ref('records/acquisitions/2026-10-18-npcgi-pilot/report.json'),
        'training_admitted':False,'originals':5,'fullview_skirt_candidates':2,
        'quarantined_visual_examples':3,'worn_examples':0,
        'note':'Source composition transcription retained separately from visual appearance; all candidates unadmitted with null splits.'})
    source = next(item for item in registry['supplementary_metadata'] if item['source'].startswith('NTNU'))
    source.update(complete_images_added=5,image_item_join_verified=True,
                  image_item_join_scope='Five filename/source-ID cards match; one image conflicts with publisher skirt category',
                  archive_index_exact_skirt_metadata_joins=25,fullview_skirt_candidates=2,
                  quarantined_visual_examples=3,worn_presentation_verified=False,training_admitted=False)
    source['evidence'].extend(ref(p) for p in (
        'records/acquisitions/2026-10-18-fabric-archive-index/parsed/report.json',
        'records/acquisitions/2026-10-18-npcgi-pilot/selection.json',
        'records/acquisitions/2026-10-18-npcgi-pilot/report.json',
        'records/acquisitions/2026-10-18-npcgi-pilot/photo-review.json',
        'records/validation/2026-10-19-npcgi-pilot-independent-review.json'))
    registry['development_experiments'].extend([
        model_record('v3','records/validation/2026-10-18-detection-candidate.json'),
        model_record('v4','records/validation/2026-10-19-detection-v4-comparison.json')])
    write('data/registry.json',registry)
    print('Registered1932 originals; two research exports; zero new fabric admissions.')


if __name__ == '__main__':
    main()
