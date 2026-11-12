"""Verify an explicit research detection combination through saved-frame HTTP."""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_comparison(comparison):
    """Fail closed before choosing a small saved-frame integration sample."""
    require(comparison.get('status') == 'completed', 'Completed comparison required')
    require(comparison.get('primary_candidate') == 'v2_plus_presence'
            and comparison.get('baseline') == 'v1', 'Unsupported comparison paths')
    require(comparison.get('fixed_presence_threshold') == .5
            and comparison.get('fixed_mask_threshold') == .5, 'Unsupported comparison thresholds')
    models = comparison.get('models', {})
    for value in (models.get('presence'), models.get('pleating'), models.get('masks', {}).get('v2')):
        require(isinstance(value, str) and len(value) == 64
                and all(c in '0123456789abcdef' for c in value), 'Explicit model SHA256 identities required')
    rows = comparison.get('results')
    require(isinstance(rows, list) and bool(rows), 'Comparison results required')
    seen = set()
    for case in rows:
        require(isinstance(case.get('sample_id'), str) and bool(case['sample_id'])
                and case['sample_id'] not in seen, 'Unique comparison sample IDs required')
        seen.add(case['sample_id'])
        require(type(case.get('presence_target')) is int and case['presence_target'] in (0, 1),
                'Invalid comparison target')
        gate = case.get('presence', {})
        score = gate.get('score')
        require(type(score) in (float, int) and math.isfinite(score) and 0 <= score <= 1,
                'Invalid comparison presence score')
        require(type(gate.get('accepted')) is bool and gate['accepted'] == (score >= .5)
                and gate.get('threshold') == .5 and gate.get('model_sha256') == models['presence'],
                'Comparison presence contract mismatch')
        paths = case.get('paths', {})
        for name in ('v1', 'v2', 'v1_plus_presence', 'v2_plus_presence'):
            path = paths.get(name, {})
            require(type(path.get('accepted')) is bool, 'Incomplete comparison paths')
            label = path.get('pleating_prediction')
            require(label in ('pleated', 'non_pleated') if path['accepted'] else label is None,
                    'Invalid comparison pleating prediction')
        for name in ('v1', 'v2'):
            require(paths[name + '_plus_presence']['accepted'] == (paths[name]['accepted'] and gate['accepted']),
                    'Inconsistent gated comparison path')
        region = paths['v2'].get('localization', {})
        require(region.get('model_sha256') == models['masks']['v2'], 'Comparison localization identity mismatch')
        require((region.get('status') == 'provisional') == paths['v2']['accepted'],
                'Comparison localization acceptance mismatch')
        if paths['v2']['accepted']:
            roi = region.get('roi')
            require(isinstance(roi, list) and len(roi) == 4 and all(type(x) is int for x in roi)
                    and 0 <= roi[0] < roi[2] and 0 <= roi[1] < roi[3], 'Invalid comparison ROI')
    return comparison


def verify_identities(comparison, presence_run, localizer_run, bundle_model_sha256):
    models = comparison['models']
    require(presence_run.get('status') == 'completed' and localizer_run.get('status') == 'completed',
            'Completed model runs required')
    require(models['presence'] == presence_run['export']['sha256'], 'Comparison/presence identity mismatch')
    require(models['masks']['v2'] == localizer_run['export']['sha256'], 'Comparison/localizer identity mismatch')
    require(models['pleating'] == bundle_model_sha256, 'Comparison/bundle pleating identity mismatch')


def check_prediction(result, case, models):
    expected = case['paths']['v2_plus_presence']
    accepted = result['style']['status'] == 'provisional'
    require(accepted == expected['accepted'], 'HTTP acceptance differs from desktop comparison')
    actual_gate = result['metadata']['presence']
    require(actual_gate['model_sha256'] == models['presence'], 'HTTP presence identity mismatch')
    require(actual_gate['accepted'] == case['presence']['accepted'], 'HTTP presence decision mismatch')
    score = actual_gate['score']
    require(type(score) in (float, int) and math.isfinite(score)
            and abs(score - case['presence']['score']) <= .001, 'HTTP presence score mismatch')
    if actual_gate['accepted']:
        actual_region = result['metadata']['localization']
        expected_region = case['paths']['v2']['localization']
        require(actual_region['model_sha256'] == models['masks']['v2'], 'HTTP localization identity mismatch')
        require(actual_region['status'] == expected_region['status'], 'HTTP localization status mismatch')
        require(actual_region.get('roi') == expected_region.get('roi'), 'HTTP localization ROI mismatch')
    if accepted:
        require(result['style']['label'] == expected['pleating_prediction'], 'HTTP pleating label mismatch')
        require(result['metadata']['pleating_model_sha256'] == models['pleating'], 'HTTP pleating identity mismatch')
    require(result['fabric']['status'] == 'disabled' and result['length']['status'] == 'unavailable',
            'Unexpected fabric or length output')
    return accepted


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True)
    p.add_argument('--presence', type=Path, required=True)
    p.add_argument('--comparison', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--port', type=int, default=18768)
    a = p.parse_args()
    bundle, output = a.bundle.resolve(), a.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    comparison = validate_comparison(json.loads(a.comparison.read_text()))
    run = json.loads((a.presence/'run.json').read_text())
    localizer = ROOT/'artifacts/models/skirt-localizer-v2'
    localizer_run = json.loads((localizer/'run.json').read_text())
    verify_identities(comparison, run, localizer_run, hashlib.sha256((bundle/'model.tflite').read_bytes()).hexdigest())
    positive = [r for r in comparison['results'] if r['presence_target'] == 1 and r['paths']['v2_plus_presence']['accepted']][:2]
    negative = [r for r in comparison['results'] if r['presence_target'] == 0 and r['paths']['v2']['accepted']
                and not r['presence']['accepted']][:1]
    if len(positive) != 2 or len(negative) != 1:
        raise ValueError('Representative accepted and gated comparison cases required')
    source_rows = {}
    for manifest in ('data/manifests/worn-pleating-development-v1.jsonl','data/labels/negative-reviewed-v3.jsonl'):
        source_rows.update({r['sample_id']:r for r in map(json.loads,(ROOT/manifest).read_text().splitlines())})
    subprocess.run([sys.executable,str(ROOT/'tools/verify_release.py'),str(bundle),'--require-app'],check=True)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',a.port))
    address = f'http://127.0.0.1:{a.port}'
    def request(path, payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        with urlopen(Request(address+path,data=data,headers={'Content-Type':'application/json'}),timeout=10) as response:
            return json.load(response)
    checks = []
    with output.with_suffix('.server.log').open('x') as log:
        child = subprocess.Popen([sys.executable,'-B','-m','app.server','--bundle',str(bundle),'--root',str(bundle),
            '--port',str(a.port),'--no-review','--experimental-localizer',str(localizer),
            '--experimental-presence',str(a.presence.resolve())],cwd=bundle,
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=log)
        try:
            deadline = time.monotonic()+60
            while True:
                if child.poll() is not None:
                    raise RuntimeError('Detection server exited; inspect log')
                try:
                    request('/api/status')
                    break
                except OSError:
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError('Detection server startup timeout')
                time.sleep(.2)
            with urlopen(address+'/',timeout=10) as response:
                ui = response.read()
            require(ui == (bundle/'app/static/index.html').read_bytes(), 'HTTP UI differs from immutable bundle')
            for case in [*positive,*negative]:
                row = source_rows[case['sample_id']]
                raw = (ROOT/row['original_path']).read_bytes()
                if hashlib.sha256(raw).hexdigest() != row['sha256']:
                    raise ValueError('Changed original')
                job = request('/api/live',{'image_base64':base64.b64encode(raw).decode(),
                                          'fabric_enabled':False,'presentation':'worn'})
                deadline = time.monotonic()+10
                while True:
                    state = request('/api/jobs?id='+job['id'])
                    if state['state'] != 'pending':
                        break
                    if time.monotonic() > deadline:
                        raise TimeoutError('Saved-frame job timeout')
                    time.sleep(.05)
                if state['state'] != 'complete':
                    raise AssertionError('Saved-frame job failed')
                result = state['result']
                accepted = check_prediction(result, case, comparison['models'])
                checks.append({'sample_id':row['sample_id'],'accepted':accepted,'desktop_match':True})
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait(timeout=5)
    subprocess.run([sys.executable,str(ROOT/'tools/verify_release.py'),str(bundle),'--require-app'],check=True)
    report = {'status':'passed','checks':checks,'server_stopped':child.poll() is not None,
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'comparison_sha256':hashlib.sha256(a.comparison.read_bytes()).hexdigest(),
              'models':comparison['models'],
              'ui_sha256':hashlib.sha256(ui).hexdigest(),
              'camera_used':False,'pi_verified':False,
              'limitations':'Three saved development frames; integration only, no new accuracy or physical evidence.'}
    with output.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2); f.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
