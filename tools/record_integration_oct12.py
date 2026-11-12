"""Register the recovered, explicitly non-promoted October 11 development pilots."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ref(path):
    return {'path': path, 'sha256': hashlib.sha256((ROOT/path).read_bytes()).hexdigest()}


def save(path, value):
    (ROOT/path).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def main():
    presence_record = 'records/models/2026-10-12-skirt-presence-v1.json'
    save(presence_record, {
        'release_id': 'skirt-presence-v1', 'status': 'development_candidate_not_promoted',
        'model_files_and_sha256': [ref('artifacts/models/skirt-presence-v1/'+name) for name in ('model.keras','model.tflite')],
        'run': ref('records/experiments/20261011-presence-v1/run.json'),
        'executed_source': ref('records/experiments/20261011-presence-v1/training_source.py'),
        'inputs': ref('records/experiments/20261011-presence-v1/inputs.json'),
        'comparison': ref('records/validation/2026-10-12-presence-comparison.json'),
        'input': {'shape':[1,224,224,3], 'dtype':'float32', 'range':[0,255],
                  'preprocessing':'Full RGB frame; Pillow bilinear resize224; model normalizes internally'},
        'output': {'shape':[1,1], 'meaning':'uncalibrated skirt-presence score', 'threshold':0.5},
        'promotion_reason':'Combined skirt coverage falls from 48/80 to 25/80; three negative validation cases insufficient',
        'pi_verified':False, 'camera_accuracy_verified':False})
    path = ROOT/'data/registry.json'
    registry = json.loads(path.read_text(encoding='utf-8'))
    registry['updated_date_asia_manila']='2026-10-12'
    registry['status']='small_development_pilots_reviewed_trained_exported_not_live_promoted'
    registry['label_preparation']['negative_pilot']={
        'manifest':ref('data/labels/negative-reviewed-v1.jsonl'),
        'report':ref('data/labels/negative-reviewed-v1.report.json'),
        'admitted':12,'quarantined':78,'train':9,'validation':3,'independent_human_review_complete':False}
    registry['label_preparation']['fabric_smoke']={
        'manifest':ref('data/labels/fabric-pilot-v1.jsonl'),
        'split':ref('data/labels/fabric-pilot-v1-splits.json'),
        'review':ref('records/review/2026-10-11-fabric-pilot.json'),
        'admitted':17,'train':12,'validation':5,'scope':'internal_source_appearance_pipeline_smoke_only',
        'verified_fiber_composition':False,'live_approved':False}
    for model in (presence_record, 'records/models/2026-10-12-fabric-smoke-v1.json'):
        registry['development_experiments']=[item for item in registry['development_experiments'] if item['path']!=model]
        registry['development_experiments'].append(ref(model))
    for source in registry.get('supplementary_metadata',[]):
        if source.get('source')=='DeepFashion-MultiModal':
            source['training_admitted']=True
            source['training_admission_scope']='17 source items for internal pipeline smoke only; not verified composition or live release'
    save('data/registry.json',registry)


if __name__ == '__main__':
    main()
