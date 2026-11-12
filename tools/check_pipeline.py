"""Exercise the worker/controller with real saved development images and TFLite."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.inference import SkirtPredictor
from app.pipeline import ImagePipeline


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    predictor=SkirtPredictor(args.bundle)
    manifest=ROOT/'data/labels/skirt-baseline-v1.jsonl'
    archive=ROOT/'records/experiments/20261004-skirt-finetune-v1/validation-predictions.json'
    rows={r['sample_id']:r for r in map(json.loads,manifest.read_text().splitlines())}
    pipeline=ImagePipeline(predictor,max_frame_age=30,max_result_age=30)
    checks=[]
    try:
        for old in json.loads(archive.read_text())[:3]:
            row=rows[old['sample_id']]
            path=ROOT/row['original_path']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
            x,y,w,h=row['source_labels']['bbox']
            with Image.open(path) as image:
                submitted=pipeline.submit(image.convert('RGB'),roi=(x,y,x+w,y+h),valid=True,
                                          full_skirt_confirmed=True,scene_changed=True)
            assert submitted['accepted'] and pipeline.wait_idle(30)
            state=pipeline.snapshot()
            result=state['result']
            assert result is not None and result['frame_id']==submitted['frame_id']
            prediction=result['prediction']
            delta=abs(prediction['style']['score']-max(old['tflite_probabilities']))
            assert prediction['style']['label']==old['predicted'] and delta<1e-4
            assert prediction['fabric']['status']==prediction['length']['status']=='unavailable'
            checks.append({'sample_id':row['sample_id'],'archived_score_delta':delta,'result':result})
        pipeline.set_connected(False)
        assert pipeline.snapshot()['result'] is None
    finally:
        if not pipeline.close(5):
            raise RuntimeError('Worker did not stop within timeout')
    sources=['app/pipeline.py','app/live_state.py','app/inference.py','tools/check_pipeline.py']
    record={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'status':'passed',
            'kind':'saved_image_worker_integration','checks':checks,
            'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
            'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
            'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'runtime':predictor.runtime,'age_limits_seconds':30,
            'age_limit_status':'smoke_test_only_not_product_configuration',
            'worker_shutdown_verified':True,'camera_opened':False,'pi_verified':False,
            'limitations':'Three fixed development images and explicit scene/validity events; no detector, webcam accuracy or deployment benchmark.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(record,stream,indent=2)
        stream.write('\n')
    print(json.dumps({'status':'passed','real_images':len(checks),'max_score_delta':max(c['archived_score_delta'] for c in checks)}))


if __name__=='__main__':
    main()
