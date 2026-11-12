"""Close out the verified recovery batch; no training or dataset mutation."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def ref(path):
    return {'path':path, 'sha256':hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    registry = load('data/registry.json')
    checked = set()
    def verify_refs(value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                p = (ROOT / value['path']).resolve()
                if not p.is_relative_to(ROOT) or not p.is_file():
                    raise ValueError('Missing or external registry reference')
                if hashlib.sha256(p.read_bytes()).hexdigest() != value['sha256']:
                    raise ValueError('Changed registry reference: '+value['path'])
                checked.add(value['path'])
            for child in value.values():
                verify_refs(child)
        elif isinstance(value, list):
            for child in value:
                verify_refs(child)
    for key in ('supplementary_metadata','source_label_followup_oct17',
                'presentation_review_oct17','presentation_review_completed_oct17'):
        verify_refs(registry[key])
    for version in ('v3','v4'):
        verify_refs(load(f'records/models/2026-10-18-skirt-presence-{version}.json'))
    comparison = load('records/validation/2026-10-19-detection-v4-comparison.json')
    if not comparison['development_criteria_passed'] or comparison['deployment_approved']:
        raise ValueError('Unexpected candidate acceptance status')
    if registry['downloaded_totals']['photographs'] != 1932:
        raise ValueError('Unexpected original count')
    test_log = (ROOT/'records/validation/2026-10-19-tests.log').read_text(encoding='utf-8-sig')
    training_log = (ROOT/'records/validation/2026-10-19-training-tests.log').read_text(encoding='utf-8-sig')
    if not re.search(r'Ran 418 tests',test_log) or 'OK (skipped=2)' not in test_log:
        raise ValueError('Desktop test log not passed')
    if not re.search(r'Ran 34 tests',training_log) or not re.search(r'^OK\s*$',training_log,re.M):
        raise ValueError('Training-environment test log not passed')
    integrity = load('records/validation/2026-10-19-final-records.json')
    http = load('records/validation/2026-10-19-presence-v4-http.json')
    if integrity['status'] != 'passed' or http['status'] != 'passed' or not http['server_stopped']:
        raise ValueError('Integration evidence incomplete')
    evidence = [
        'data/registry.json', 'records/validation/2026-10-18-combined-intake-audit.json',
        'records/validation/2026-10-18-negative-v3-admission-audit.json',
        'records/validation/2026-10-18-presence-v3-artifact-review.json',
        'records/validation/2026-10-19-presence-v4-artifact-review.json',
        'records/validation/2026-10-19-npcgi-pilot-independent-review.json',
        'records/validation/2026-10-19-detection-v4-comparison.json',
        'records/validation/2026-10-19-presence-v4-http.json',
        'records/validation/2026-10-19-tests.log',
        'records/validation/2026-10-19-training-tests.log',
        'records/validation/2026-10-19-final-records.json',
        'records/review/2026-10-19-presence-v4-negative-failures.json',
        'records/review/2026-10-19-presence-v4-positive-failures.json',
        'docs/OCT19_RECOVERY.md','docs/PRESENCE_V4_FAILURE_REVIEW.md','docs/TASK_BOARD.md']
    report = {'date_asia_manila':'2026-10-19','status':'passed_recovery_batch_not_product_acceptance',
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'evidence':[ref(path) for path in evidence],
        'extra_registry_and_nested_model_references_verified':len(checked),
        'original_images':1932,'negative_development_images':207,
        'new_fabric_training_admissions':0,'desktop_tests':{'run':418,'passed':416,'skipped':2},
        'focused_wsl_tests':{'run':34,'passed':34,'skipped':0},
        'primary_candidate_metrics':comparison['metrics']['v2_plus_presence'],
        'deployment_defaults_changed':False,'packages_installed':0,'camera_used':False,
        'pi_verified':False,'supervised_demo_accepted':False,
        'limits':'Reused agent-labelled development groups; optional research candidate. Fabric labels, wearer geometry, calibration, unseen garments and Pi acceptance remain open.'}
    with (ROOT/'records/validation/2026-10-19-integration.json').open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2); stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'evidence'},indent=2))


if __name__ == '__main__':
    main()
