"""Reconcile the verified experiment, metadata research and research station."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def ref(path):
    return {'path':path,'sha256':hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def save(path,value,exclusive=False):
    with (ROOT/path).open('x' if exclusive else 'w',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False); stream.write('\n')


def main():
    archive = 'records/experiments/20261021-category-presence-v1'
    model = 'artifacts/models/skirt-category-presence-v1'
    comparison_path = 'records/validation/2026-10-21-category-presence-comparison.json'
    review_path = 'records/validation/2026-10-21-category-presence-artifact-review.json'
    http_path = 'records/validation/2026-10-21-station-v2-http.json'
    run, comparison, review, http = map(load,(archive+'/run.json',comparison_path,review_path,http_path))
    checks = review['checks']
    if (run['status'] != 'completed' or not all(checks.values())
            or comparison['models']['presence'] != ref(model+'/model.tflite')['sha256']
            or http['status'] != 'passed' or not http['all_owned_servers_stopped']
            or not comparison['development_criteria_passed']):
        raise ValueError('Required completed evidence failed')
    metrics = comparison['metrics']['v2_plus_presence']
    if (metrics['positive_accepted'],metrics['correct_pleating'],metrics['negative_rejected']) != (44,38,42):
        raise ValueError('Unexpected metrics; review integration decision')
    record = load('templates/model-release.json')
    record.update(release_id='skirt-category-presence-v1',
        status='desktop_research_only_not_demonstration_approved',source_run_id='20261021-category-presence-v1',
        model_files_and_sha256=[ref(model+'/'+name) for name in ('model.tflite','model.keras','category-model.keras')],
        labels_in_output_order=['skirt_present_probability'],
        auxiliary_category_labels=run['source_category_labels_in_output_order'],
        input_output_tensor_contract={'input':{'shape':[1,224,224,3],'dtype':'float32'},
                                      'output':{'shape':[1,1],'dtype':'float32'}},
        preprocessing_version=run['preprocessing'],patch_strategy='One full source frame',
        thresholds_and_temporal_settings={'presence':.5,'mask':.5,'temporal_settings_changed':False},
        training_environment=ref(archive+'/environment.json'),conversion_environment=ref(archive+'/environment.json'),
        target_environment=None,pre_export_metrics=run['metrics'],post_export_metrics=comparison['metrics'],
        pi_validation_record=None,camera_calibration_id=None,known_limitations=run['limitations'],
        rollback_release_id='skirt-research-station-v1',executed_run=ref(archive+'/run.json'),
        input_manifest=ref(archive+'/inputs.json'),category_targets=ref(archive+'/source-category-targets.json'),
        split_hash=run['split_hash'],selection=run['selection'],selected_epoch=run['selected_epoch'],
        early_export=run['early_export'],final_export=run['export'],comparison=ref(comparison_path),
        independent_review=ref(review_path),station_http=ref(http_path),
        selected_for_desktop_research=True,deployment_approved=False,pi_verified=False,
        record_note='Archived cache lineage text predates explicit pleating hashes; independent review verified the actual explicit identity. Future helper now checks it. Immutable executed sources/run are unchanged.')
    record_path = 'records/models/2026-10-21-skirt-category-presence-v1.json'
    save(record_path,record,True)
    registry = load('data/registry.json')
    registry.update(updated_date_asia_manila='2026-10-22',
                    status='research_station_v2_desktop_verified_product_acceptance_open')
    registry['development_experiments'].append(ref(record_path))
    registry['physical_garment_access'] = {'date':'2026-10-20','source':'user_reconfirmation',
                                          'status':'neither_skirts_nor_raspberry_pi_available'}
    registry['selected_research_station'] = {
        'inventory':ref('artifacts/stations/skirt-research-station-v2/station-inventory.json'),
        'configuration':ref('artifacts/stations/skirt-research-station-v2/station.json'),
        'scope':'Optional desktop research; not accepted public demonstration or Pi deployment',
        'rollback':'artifacts/stations/skirt-research-station-v1','deployment_approved':False}
    registry['research_updates_oct22'] = {
        'category_targets':ref(archive+'/source-category-targets.json'),
        'category_labels_status':'Publisher-supervised hierarchical scene targets; independent human truth unverified',
        'existing_fabric_source_audit':ref('records/review/2026-10-20-fabric-source-attribute-audit.json'),
        'fabric_source_search':ref('records/review/2026-10-21-fabric-source-search.json'),
        'fabric_source_acquisition':ref('records/acquisitions/2026-10-21-fabric-source-research/acquisition.json'),
        'geometry_inventory_map':ref('records/geometry/2026-10-21-readiness/mapping.json'),
        'geometry_readiness':ref('records/validation/2026-10-21-geometry-readiness.json'),
        'observed_geometry_examples':0,'new_original_images':0,'new_training_admissions':0,
        'source_splits_changed':False,'verified_fabric_labels_added':0}
    if registry['downloaded_totals']['photographs'] != 1932:
        raise ValueError('Original image total changed unexpectedly')
    save('data/registry.json',registry)
    print('Registered category export and selected station-v2 for research; originals remain1932; product acceptance open.')


if __name__ == '__main__':
    main()
