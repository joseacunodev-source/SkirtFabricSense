"""Read-only HTTP smoke check against archived development samples; not accuracy evaluation."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8765')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    def request(path, data=None):
        body = json.dumps(data).encode() if data is not None else None
        with urlopen(Request(args.url+path, data=body, headers={'Content-Type':'application/json'}), timeout=30) as response:
            return json.load(response)
    def analyze(payload):
        job=request('/api/jobs',payload)
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            state=request('/api/jobs?id='+job['id'])
            if state['state']=='complete':return state['result']
            if state['state']!='pending':raise RuntimeError(str(state))
            time.sleep(.1)
        raise TimeoutError('Analysis job did not complete')
    status = request('/api/status')
    assert status['camera_enabled'] is False
    queue = request('/api/review')
    assert queue['total'] == 1000
    assert all(set(r)=={'sample_id','image_sha256','width','height'} for r in queue['records'])
    source = root/'data/labels/skirt-baseline-v1.jsonl'
    rows = {r['sample_id']:r for r in map(json.loads, source.read_text().splitlines())}
    archive = root/'records/experiments/20261004-skirt-finetune-v1/validation-predictions.json'
    checks = []
    # Three fixed existing development images; never protected test samples.
    for old in json.loads(archive.read_text())[:3]:
        row = rows[old['sample_id']]
        x,y,w,h = row['source_labels']['bbox']
        coordinates = [x,y,x+w,y+h]
        assert all(v == int(v) for v in coordinates)
        raw = (root/row['original_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        payload = {'image_base64':base64.b64encode(raw).decode(),
                   'roi':[int(v) for v in coordinates], 'full_skirt_confirmed':True}
        result = analyze(payload)
        delta = abs(result['style']['score']-max(old['tflite_probabilities']))
        assert result['style']['label']==old['predicted'] and delta < 1e-4
        assert result['fabric']['status']==result['length']['status']=='unavailable'
        payload['full_skirt_confirmed']=False
        assert analyze(payload)['style']['status']=='unavailable'
        checks.append({'sample_id':row['sample_id'],'image_sha256':row['sha256'],
                       'archived_score_delta':delta,'result':result})
    evidence = {'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'status':'passed',
                'test':'real_model_http_smoke','source_manifest_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
                'queue_total':queue['total'],'submitted_reviews':queue['samples_with_submitted_reviews'],
                'checks':checks,'limitations':'Three existing development images; not new accuracy evidence, live-camera or Pi verification.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(evidence,stream,indent=2)
        stream.write('\n')
    print(json.dumps({'status':'passed','samples':len(checks),'max_score_delta':max(c['archived_score_delta'] for c in checks)}))


if __name__=='__main__':
    main()
