"""Verify a portable research station using saved source frames; no camera."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
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
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from tools.station_package import launch_command, verify_station
from tools.check_detection_http import validate_comparison


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def detection_matches(result, case, models):
    expected = case['paths']['v2_plus_presence']
    accepted = result['style']['status'] == 'provisional'
    require(accepted == expected['accepted'], 'Station detection differs from reference')
    actual = result['metadata']['presence']
    require(actual['model_sha256'] == models['presence']
            and actual['accepted'] == case['presence']['accepted'], 'Station presence identity/decision mismatch')
    score = actual['score']
    require(type(score) in (int, float) and math.isfinite(score)
            and abs(score-case['presence']['score']) <= .001, 'Station presence score mismatch')
    if actual['accepted']:
        region = result['metadata']['localization']
        expected_region = case['paths']['v2']['localization']
        require(region['model_sha256'] == models['masks']['v2']
                and region['status'] == expected_region['status']
                and region.get('roi') == expected_region.get('roi'), 'Station localization differs from reference')
    else:
        require('localization' not in result['metadata'], 'Rejected presence should skip downstream localization')
    if accepted:
        require(result['style']['label'] == expected['pleating_prediction']
                and result['metadata']['pleating_model_sha256'] == models['pleating'],
                'Station pleating differs from reference')
    require(result['length']['status'] == 'unavailable', 'Station cannot supply calibrated length')
    return accepted


def run(package, comparison_path, output, port):
    package, output = package.resolve(), output.resolve()
    require(not output.exists(), 'Refusing to overwrite station HTTP evidence')
    before = verify_station(package)
    inventory_hash = sha(package/'station-inventory.json')
    comparison = validate_comparison(json.loads(comparison_path.read_text(encoding='utf-8')))
    config = json.loads((package/'station.json').read_text(encoding='utf-8'))
    require(config['models']['presence']['sha256'] == comparison['models']['presence']
            and config['models']['localizer']['sha256'] == comparison['models']['masks']['v2']
            and sha(package/'application/model.tflite') == comparison['models']['pleating'],
            'Station models do not match saved development reference')
    positives = [r for r in comparison['results'] if r['presence_target']
                 and r['paths']['v2_plus_presence']['accepted']][:2]
    negatives = [r for r in comparison['results'] if not r['presence_target']
                 and r['paths']['v2']['accepted'] and not r['presence']['accepted']][:1]
    require(len(positives) == 2 and len(negatives) == 1, 'Two accepted and one gated case required')
    source_rows = {}
    for name in ('data/manifests/worn-pleating-development-v1.jsonl','data/labels/negative-reviewed-v3.jsonl'):
        source_rows.update({r['sample_id']:r for r in map(json.loads,(ROOT/name).read_text(encoding='utf-8').splitlines())})

    # Import the independent direct adapter from the verified copied application.
    # Neither the child servers nor this reference process use the GPU.
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    sys.path.insert(0,str(package/'application'))
    from app.fabric import FabricSmokePredictor
    from PIL import Image, ImageOps
    import app.fabric
    require(Path(app.fabric.__file__).resolve().is_relative_to(package/'application'),
            'Reference adapter must come from the verified package')
    direct = FabricSmokePredictor(package/'models/fabric')
    checks, commands, stops = [], [], []
    log_path = output.with_suffix('.server.log')
    with log_path.open('x',encoding='utf-8') as log:
        for mode, fabric_opt_in in enumerate((False, True)):
            selected_port = port+mode
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',selected_port))
            address = f'http://127.0.0.1:{selected_port}'
            def request(path, payload=None):
                data = json.dumps(payload).encode() if payload is not None else None
                with urlopen(Request(address+path,data=data,headers={'Content-Type':'application/json'}),timeout=10) as response:
                    return json.load(response)
            def analyze(raw, enabled):
                job = request('/api/live',{'image_base64':base64.b64encode(raw).decode(),
                                          'fabric_enabled':enabled,'presentation':'worn'})
                deadline = time.monotonic()+20
                while time.monotonic() < deadline:
                    state = request('/api/jobs?id='+job['id'])
                    if state['state'] == 'complete':
                        return state['result']
                    require(state['state'] == 'pending', 'Saved-frame station job failed')
                    time.sleep(.05)
                raise TimeoutError('Saved-frame station job timed out')
            command = launch_command(package,selected_port,fabric_opt_in)
            commands.append(command)
            child = subprocess.Popen(command,cwd=package/'application',
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='-1',PYTHONDONTWRITEBYTECODE='1'),
                stdout=log,stderr=log)
            try:
                deadline = time.monotonic()+60
                while True:
                    require(child.poll() is None, 'Station server exited; inspect log')
                    try:
                        request('/api/status'); break
                    except OSError:
                        pass
                    if time.monotonic() > deadline:
                        raise TimeoutError('Station startup timeout')
                    time.sleep(.2)
                with urlopen(address+'/',timeout=10) as response:
                    ui = response.read()
                require(ui == (package/'application/app/static/index.html').read_bytes(),
                        'Station must serve the exact packaged camera UI')
                for case in positives+negatives:
                    row = source_rows[case['sample_id']]
                    raw = (ROOT/row['original_path']).read_bytes()
                    require(hashlib.sha256(raw).hexdigest() == row['sha256'], 'Changed saved source original')
                    off, on = analyze(raw,False), analyze(raw,True)
                    accepted = detection_matches(off,case,comparison['models'])
                    detection_matches(on,case,comparison['models'])
                    require(off['style'] == on['style'], 'Fabric setting must preserve independent style result')
                    require(off['fabric']['status'] == 'disabled', 'Fabric off must disable inference output')
                    if fabric_opt_in and accepted:
                        actual = on['fabric']
                        require(actual['status'] == 'research_only' and actual['live_approved'] is False
                                and actual['composition_verified'] is False and actual['pi_verified'] is False,
                                'Fabric output must retain research-only semantics')
                        roi = case['paths']['v2']['localization']['roi']
                        with Image.open(ROOT/row['original_path']) as original:
                            image = ImageOps.exif_transpose(original).convert('RGB')
                            expected = direct.predict(image,roi)
                        require(actual['label'] == expected['label']
                                and actual['model_sha256'] == direct.model_sha256
                                and actual['roi_xyxy'] == roi
                                and actual['source_frame_size'] == list(image.size)
                                and isinstance(actual.get('source_frame_id'),str) and bool(actual['source_frame_id']),
                                'Fabric source/model/ROI/label identity mismatch')
                        require(len(actual['scores']) == 4
                                and all(math.isfinite(a) and abs(a-b) <= .001
                                        for a,b in zip(actual['scores'],expected['scores']))
                                and abs(actual['score']-expected['score']) <= .001,
                                'Fabric HTTP probabilities differ from direct packaged reference')
                        fabric_label = actual['label']
                    else:
                        require(on['fabric']['status'] == 'unavailable'
                                and 'model_sha256' not in on['fabric'],
                                'Unloaded or gated fabric must remain unavailable')
                        fabric_label = None
                    checks.append({'sample_id':row['sample_id'],'image_sha256':row['sha256'],
                        'fabric_launch_opt_in':fabric_opt_in,'accepted':accepted,
                        'fabric_off':'disabled','fabric_on':on['fabric']['status'],
                        'fabric_label':fabric_label,'style_matches_development':True,
                        'length_unavailable':True})
            finally:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=5)
                stops.append(child.poll() is not None)
    after = verify_station(package)
    require(before == after and sha(package/'station-inventory.json') == inventory_hash,
            'Station changed during HTTP verification')
    execution_path = output.with_suffix('.execution.json')
    execution = {'recorded_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'source_sha256':sha(Path(__file__)),'python_executable':sys.executable,
        'versions':{name:importlib.metadata.version(name) for name in ('tensorflow','numpy','Pillow')},
        'commands':commands,'working_directory':str(package/'application'),
        'environment_overrides':{'CUDA_VISIBLE_DEVICES':'-1','PYTHONDONTWRITEBYTECODE':'1'},
        'packages_installed':0,'gpu_used':False,'owned_servers_stopped':stops,
        'direct_reference_module_sha256':sha(Path(app.fabric.__file__))}
    with execution_path.open('x',encoding='utf-8') as stream:
        json.dump(execution,stream,indent=2); stream.write('\n')
    report = {'recorded_at':execution['recorded_at'],'status':'passed','checks':checks,
        'saved_originals':3,'http_inference_jobs':12,'server_configurations':2,
        'packaged_ui_matches':True,'ui_sha256':hashlib.sha256(ui).hexdigest(),
        'models':config['models'],'pleating_sha256':comparison['models']['pleating'],
        'station_inventory_sha256':inventory_hash,'station_unchanged':True,
        'source_sha256':sha(Path(__file__)),'comparison_sha256':sha(comparison_path),
        'execution_sha256':sha(execution_path),'all_owned_servers_stopped':all(stops),
        'camera_used':False,'pi_verified':False,'packages_installed':0,
        'limitations':['Three reused saved development originals; no new accuracy estimate.',
            'No browser camera, physical garments, measured calibration or Pi was tested.',
            'Fabric remains the unapproved 17-group source-appearance smoke model.',
            'No fabric model identity/output appears on gated negative results; this does not instrument internal call counts.',
            'Direct server argv equals the verified launcher command; the wrapper process was not the HTTP server.']}
    with output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2); stream.write('\n')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',type=Path,required=True)
    p.add_argument('--comparison',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,default=18820)
    a = p.parse_args()
    require(1 <= a.port < 65535, 'Two adjacent valid ports required')
    result = run(a.package,a.comparison,a.output,a.port)
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'},indent=2))


if __name__ == '__main__':
    main()
