"""Archive the completed localizer evidence in the project model register."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def ref(relative):
    path = ROOT / relative
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    run = Path('records/experiments/20261009-localizer-v1')
    r = json.loads((ROOT / run / 'run.json').read_text())
    if r['status'] != 'completed':
        raise ValueError('Run incomplete')
    model = ref('artifacts/models/skirt-localizer-v1/model.tflite')
    if model['sha256'] != r['export']['sha256']:
        raise ValueError('Export checksum mismatch')
    m = json.loads((ROOT / 'templates/model-release.json').read_text())
    m.update(release_id='skirt-localizer-v1', status='experimental_desktop_export_verified',
             source_run_id=run.as_posix(), model_files_and_sha256=[model, ref('artifacts/models/skirt-localizer-v1/model.keras')],
             labels_in_output_order=['skirt_pixel_probability'],
             input_output_tensor_contract={'input': {'shape': [1,224,224,3], 'dtype': 'float32', 'range': [0,255]},
                                           'output': {'shape': [1,56,56,1], 'dtype': 'float32', 'range': [0,1]}},
             preprocessing_version=r['preprocessing'], patch_strategy='Full source resize; separate experimental ROI decoder',
             thresholds_and_temporal_settings={'mask_threshold': .5, 'min_component_pixels': 9,
                 'reject_multiple_components': True, 'reject_frame_edge_contact': True, 'calibrated': False},
             training_environment=ref(run / 'environment.json'), conversion_environment=ref(run / 'environment.json'),
             pre_export_metrics=r['metrics'], post_export_metrics={'maximum_absolute_error': r['export']['maximum_absolute_error'],
                                                                  'tolerance': r['export']['tolerance']},
             known_limitations=r['limitations'])
    m['experiment_artifacts'] = [ref(p.relative_to(ROOT)) for p in sorted((ROOT / run).iterdir()) if p.is_file()]
    m['automatic_evaluation'] = ref('records/validation/2026-10-10-automatic-pilot.json')
    record = ROOT / 'records/models/2026-10-10-skirt-localizer-v1.json'
    with record.open('x', encoding='utf-8') as stream:
        json.dump(m, stream, indent=2)
    path = ROOT / 'data/registry.json'
    registry = json.loads(path.read_text())
    registry['updated_date_asia_manila'] = '2026-10-10'
    registry['development_experiments'].append(ref(record.relative_to(ROOT)))
    registry['status'] = 'pleating_and_localization_development_pilots_exported_fabric_unavailable'
    path.write_text(json.dumps(registry, indent=2)+'\n', encoding='utf-8')
    print('Recorded experimental localizer; original image counts unchanged.')

if __name__ == '__main__':
    main()
