"""Recheck unchanged pilot checkpoint/export with TF32 disabled, without retraining."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf

ROOT=Path(__file__).resolve().parents[2]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Output exists')
    gpus=tf.config.list_physical_devices('GPU')
    for gpu in gpus:tf.config.experimental.set_memory_growth(gpu,True)
    previous=tf.config.experimental.tensor_float_32_execution_enabled()
    tf.config.experimental.enable_tensor_float_32_execution(False)
    model=tf.keras.models.load_model(a.run/'model.keras',compile=False)
    interpreter=tf.lite.Interpreter(model_path=str(a.run/'model.tflite'),num_threads=2)
    interpreter.allocate_tensors()
    coordinates={r['sample_id']:r for r in json.loads((a.run/'preprocessing-records.json').read_text())}
    rows=[json.loads(x) for x in (a.run/'dataset.jsonl').read_text().splitlines()]
    predictions=[]; elapsed=[]
    for row in rows:
        if row['split']!='development_validation':continue
        source=ROOT/row['original_path']
        if sha(source)!=row['sha256']:raise ValueError('Changed image')
        with Image.open(source) as im:
            roi=im.convert('RGB').crop(coordinates[row['sample_id']]['box_xyxy'])
            x=np.array(ImageOps.pad(roi,(224,224),method=Image.Resampling.BILINEAR,color=(128,128,128)),dtype=np.float32)[None]
        y=model(x,training=False).numpy()
        interpreter.set_tensor(interpreter.get_input_details()[0]['index'],x)
        start=time.perf_counter();interpreter.invoke();elapsed.append(time.perf_counter()-start)
        q=interpreter.get_tensor(interpreter.get_output_details()[0]['index'])
        if not np.isfinite(y).all() or not np.isfinite(q).all():raise ValueError('Nonfinite output')
        predictions.append(dict(sample_id=row['sample_id'],actual=row['label'],tensorflow=y[0].tolist(),tflite=q[0].tolist(),
                                maximum_absolute_error=float(np.max(np.abs(y-q)))))
    delta=max(r['maximum_absolute_error'] for r in predictions)
    report=dict(status='passed' if delta<=.001 else 'failed',source_sha256=sha(Path(__file__)),
                parent_run_sha256=sha(a.run/'run.json'),checkpoint_sha256=sha(a.run/'model.keras'),
                tflite_sha256=sha(a.run/'model.tflite'),dataset_sha256=sha(a.run/'dataset.jsonl'),
                tensorflow_version=tf.__version__,tf32_default_observed=previous,tf32_enabled_for_verification=False,
                retrained=False,export_changed=False,count=len(predictions),maximum_absolute_error=delta,tolerance_absolute=.001,
                argmax_agreement=float(np.mean([np.argmax(r['tensorflow'])==np.argmax(r['tflite']) for r in predictions])),
                desktop_tflite_invoke_median_seconds=float(np.median(elapsed[1:])),pi_verified=False,predictions=predictions)
    a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='predictions'},indent=2))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
