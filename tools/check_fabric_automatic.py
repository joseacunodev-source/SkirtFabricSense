"""Paired saved-original manual/automatic ROI fabric appearance smoke check."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def metrics(rows, key, labels):
    accepted = [r for r in rows if r[key] is not None]
    matrix = [[0]*len(labels) for _ in labels]
    for row in accepted:
        matrix[labels.index(row['label'])][labels.index(row[key]['label'])] += 1
    correct = sum(matrix[i][i] for i in range(len(labels)))
    f1 = []
    for i in range(len(labels)):
        den = sum(matrix[i]) + sum(row[i] for row in matrix)
        f1.append(2*matrix[i][i]/den if den else 0.)
    return dict(total=len(rows), accepted=len(accepted), correct=correct,
                coverage=len(accepted)/len(rows), correct_fraction_all=correct/len(rows),
                accuracy_accepted=correct/len(accepted) if accepted else None,
                macro_f1_accepted=sum(f1)/len(f1), confusion_matrix_accepted=matrix)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    import tensorflow as tf
    import numpy as np
    from PIL import Image, __version__ as pillow_version
    tf.config.set_visible_devices([], 'GPU')
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    from app.fabric import FabricSmokePredictor, LABELS
    from app.localization import SkirtLocalizer
    from tools.training.train_fabric_pilot import validate
    archive = ROOT/'records/experiments/20261011-fabric-smoke-v1'
    model = ROOT/'artifacts/models/fabric-smoke-v1'
    localizer_dir = ROOT/'artifacts/models/skirt-localizer-v1'
    run = json.loads((model/'run.json').read_text())
    if sha(archive/'inputs.jsonl') != run['dataset_manifest_sha256']:
        raise ValueError('Frozen fabric input hash mismatch')
    if sha(archive/'splits.json') != run['split_manifest_sha256']:
        raise ValueError('Frozen fabric split hash mismatch')
    rows = [json.loads(x) for x in (archive/'inputs.jsonl').read_text().splitlines()]
    validate(rows,json.loads((archive/'splits.json').read_text()))
    rows = [r for r in rows if r['split']=='development_validation']
    if len(rows)!=5:raise ValueError('Expected five frozen development examples')
    fabric = FabricSmokePredictor(model)
    localizer = SkirtLocalizer(localizer_dir)
    predictions=[]
    for row in rows:
        path=ROOT/row['original_path']
        if sha(path)!=row['sha256']:raise ValueError('Changed source image')
        with Image.open(path) as opened:
            image=opened.convert('RGB')
        manual=fabric.predict(image,row['roi_xyxy'])
        region=localizer.locate(image)
        automatic=fabric.predict(image,region['roi']) if region['status']=='provisional' else None
        predictions.append(dict(sample_id=row['sample_id'],group_id=row['group_id'],
            image_sha256=row['sha256'],original_path=row['original_path'],label=row['label'],
            source_frame_size=list(image.size),manual=manual,localization=region,automatic=automatic))
    report=dict(status='completed',date_asia_manila=datetime.now(ZoneInfo('Asia/Manila')).date().isoformat(),
        objective='Paired frozen saved-image manual ROI versus v1 automatic ROI fabric appearance smoke',
        source_sha256=dict(check=sha(__file__),adapter=sha(ROOT/'app/fabric.py'),
                           localizer=sha(ROOT/'app/localization.py')),
        dataset_manifest_sha256=run['dataset_manifest_sha256'],split_manifest_sha256=run['split_manifest_sha256'],
        model_sha256=fabric.model_sha256,model_run_sha256=fabric.run_sha256,localizer_sha256=localizer.sha256,
        versions=dict(tensorflow=tf.__version__,numpy=np.__version__,pillow=pillow_version),
        device='WSL desktop CPU; GPU disabled',labels=LABELS,
        manual_metrics=metrics(predictions,'manual',LABELS),automatic_metrics=metrics(predictions,'automatic',LABELS),
        predictions=predictions,pi_verified=False,camera_verified=False,live_approved=False,
        limitations=['Five source-appearance development images only; no independent human ground truth.',
                     'Source appearance annotations do not establish fiber composition.',
                     'Automatic acceptance is a mask decoder output, not verified skirt presence or full visibility.',
                     'No threshold tuning, model retraining, final-test consumption or new admission.',
                     'No camera, Pi, latency benchmark or calibration evidence.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8') as f:
        f.write(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ['status','manual_metrics','automatic_metrics']}))


if __name__=='__main__':main()
