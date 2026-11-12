"""Frozen-feature skirt presence pilot with reviewed grouped negatives.

Development-only binary gate; not a replacement for mask geometry/quality checks.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, data): Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')

def validate(rows):
    groups = {}; ids = set(); hashes = set()
    for row in rows:
        if row['presence_target'] == 0:
            if (row.get('training_eligibility', {}).get('approved') is not True
                    or row.get('label') != 'no_skirt'
                    or row.get('grouping_review_pending') is not False
                    or row.get('label_evidence', {}).get('original_inspected') is not True):
                raise ValueError('Negative lacks explicit reviewed training admission')
        if row['sample_id'] in ids or row['sha256'] in hashes: raise ValueError('Duplicate image')
        ids.add(row['sample_id']); hashes.add(row['sha256'])
        if row['source_partition'] != 'train2020': raise ValueError('Protected source partition')
        if row['split'] not in ('development_train','development_validation'): raise ValueError('Invalid split')
        group = row['group_hash']
        if group in groups and groups[group] != row['split']: raise ValueError('Cross-split group')
        groups[group] = row['split']
    for split in ('development_train','development_validation'):
        if {r['presence_target'] for r in rows if r['split'] == split} != {0,1}:
            raise ValueError('Both classes required in each development partition')

def run(out, report, epochs, negative_manifest=None):
    import numpy as np
    from PIL import Image
    positive = ROOT/'data/labels/skirt-baseline-v1.jsonl'
    negative = negative_manifest or ROOT/'data/labels/negative-reviewed-v1.jsonl'
    negative = negative.resolve()
    if not negative.is_relative_to(ROOT.resolve()): raise ValueError('Negative manifest outside workspace')
    rows = [{**json.loads(line), 'presence_target':1} for line in positive.read_text().splitlines()]
    negatives = [json.loads(line) for line in negative.read_text().splitlines()]
    negatives = [r for r in negatives if r.get('split') in ('development_train','development_validation')]
    if any(r['label'] != 'no_skirt' for r in negatives): raise ValueError('Unexpected negative label')
    rows += [{**row, 'presence_target':0} for row in negatives]
    validate(rows)
    report['inputs'] = [{'path':str(p.relative_to(ROOT)), 'sha256':sha(p)} for p in (positive,negative)]
    report['class_counts_by_split'] = {split:dict(Counter(str(r['presence_target']) for r in rows if r['split']==split)) for split in ('development_train','development_validation')}
    save(out/'inputs.json', rows)
    report['frozen_inputs_sha256'] = sha(out/'inputs.json')
    report['split_hash'] = hashlib.sha256(json.dumps(sorted((r['sample_id'],r['group_hash'],r['split']) for r in rows)).encode()).hexdigest()
    x = []
    for row in rows:
        path = ROOT/row['original_path']
        if sha(path) != row['sha256']: raise ValueError('Changed image')
        with Image.open(path) as im: x.append(np.asarray(im.convert('RGB').resize((224,224),Image.Resampling.BILINEAR), dtype=np.float32))
    x=np.stack(x); y=np.array([r['presence_target'] for r in rows],dtype=np.float32)[:,None]
    train=np.array([i for i,r in enumerate(rows) if r['split']=='development_train'])
    val=np.array([i for i,r in enumerate(rows) if r['split']=='development_validation'])
    import tensorflow as tf
    gpus=tf.config.list_physical_devices('GPU')
    if not gpus: raise RuntimeError('GPU unavailable')
    for gpu in gpus: tf.config.experimental.set_memory_growth(gpu,True)
    tf.config.experimental.enable_tensor_float_32_execution(False); tf.keras.utils.set_random_seed(42)
    base=tf.keras.applications.MobileNetV2(include_top=False,weights='imagenet',input_shape=(224,224,3),pooling='avg');base.trainable=False
    inp=tf.keras.Input((224,224,3),name='rgb')
    feature=base(tf.keras.layers.Rescaling(1/127.5,offset=-1)(inp),training=False)
    z=tf.keras.layers.Dense(64,activation='relu')(feature)
    z=tf.keras.layers.Dropout(.2)(z)
    model=tf.keras.Model(inp,tf.keras.layers.Dense(1,activation='sigmoid',name='skirt_presence')(z))
    model.compile(optimizer=tf.keras.optimizers.Adam(.001),loss='binary_crossentropy')
    weights={label:len(train)/(2*sum(int(y[i,0])==label for i in train)) for label in (0,1)}
    report.update(seed=42, epochs=epochs, batch_size=16, learning_rate=.001, optimizer='Adam',
        architecture='Frozen ImageNet MobileNetV2 avg + Dense64 ReLU + Dropout0.2 + sigmoid1',
        preprocessing='Full RGB resize224 Pillow bilinear; float32 0..255; normalization inside model',
        class_weights=weights, threshold=.5, selection='Minimum class-balanced development-validation BCE',
        initial_weights_provenance='records/acquisitions/2026-10-04-mobilenetv2-weights.json',
        gpu=[str(g) for g in gpus], versions={'tensorflow':tf.__version__,'numpy':np.__version__})
    rng=np.random.default_rng(42); best=float('inf'); history=[]
    def predict(indices):return np.concatenate([model(x[indices[i:i+16]],training=False).numpy() for i in range(0,len(indices),16)])[:,0]
    for epoch in range(epochs):
        order=rng.permutation(train)
        for start in range(0,len(order),16):
            idx=order[start:start+16]; bx=x[idx].copy(); flip=rng.random(len(idx))<.5; bx[flip]=bx[flip,:,::-1,:]
            model.train_on_batch(bx,y[idx],sample_weight=np.array([weights[int(v)] for v in y[idx,0]]))
        probability=predict(val); truth=y[val,0]; p=np.clip(probability,1e-7,1-1e-7)
        losses=-(truth*np.log(p)+(1-truth)*np.log(1-p))
        balanced_loss=float((losses[truth==0].mean()+losses[truth==1].mean())/2)
        metrics={'epoch':epoch+1,'balanced_validation_bce':balanced_loss,
                 'skirt_recall':float((probability[truth==1]>=.5).mean()),
                 'negative_rejection':float((probability[truth==0]<.5).mean())}
        history.append(metrics);save(out/'history.json',history);print(json.dumps(metrics),flush=True)
        if balanced_loss<best:best=balanced_loss;model.save_weights(out/'best.weights.h5');report['selected_epoch']=epoch+1
    model.load_weights(out/'best.weights.h5'); probabilities=predict(val)
    model.save(out/'model.keras');model.export(str(out/'saved_model'),input_signature=[tf.TensorSpec([1,224,224,3],tf.float32)])
    converter=tf.lite.TFLiteConverter.from_saved_model(str(out/'saved_model'));converter.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS]
    blob=converter.convert();(out/'model.tflite').write_bytes(blob)
    interpreter=tf.lite.Interpreter(model_content=blob,num_threads=2);interpreter.allocate_tensors();exported=[]
    for index in val:
        interpreter.set_tensor(interpreter.get_input_details()[0]['index'],x[index:index+1]);interpreter.invoke()
        exported.append(float(interpreter.get_tensor(interpreter.get_output_details()[0]['index'])[0,0]))
    delta=float(np.max(np.abs(np.array(exported)-probabilities)))
    report['export']={'sha256':sha(out/'model.tflite'),'bytes':len(blob),'maximum_absolute_error':delta,'tolerance':.001,'pi_verified':False}
    if delta>.001:raise RuntimeError('Export parity failed')
    save(out/'validation-predictions.json',[{'sample_id':rows[i]['sample_id'],'target':int(y[i,0]),'probability':float(p),'tflite_probability':q} for i,p,q in zip(val,probabilities,exported)])
    report['metrics']={'positive_validation':int(sum(y[val,0]==1)),'negative_validation':int(sum(y[val,0]==0)),
                       'skirt_recall':float((probabilities[y[val,0]==1]>=.5).mean()),
                       'negative_rejection':float((probabilities[y[val,0]==0]<.5).mean())}
    report['status']='completed'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--epochs',type=int,default=10);parser.add_argument('--negative-manifest',type=Path);args=parser.parse_args()
    if not 1 <= args.epochs <= 100: parser.error('Epoch count must be 1..100')
    args.output.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    report={'status':'started','started_at':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(__file__),
            'limitations':['Small agent-reviewed development negative pool; not independent human truth',
                           'All negatives previously used in a development diagnostic, not untouched final testing',
                           'No camera/Pi verification; presence scores are uncalibrated',
                           'Presence gate does not improve mask geometry or prove full-skirt framing']}
    shutil.copyfile(__file__,args.output/'training_source.py')
    try:
        subprocess.run([sys.executable,str(ROOT/'tools/collect_environment.py'),'--role','training-wsl-presence','--output',str(args.output/'environment.json')],check=True)
        run(args.output,report,args.epochs,args.negative_manifest)
    except Exception as exc:report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report.update(finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-start)
    save(args.output/'run.json',report);print(json.dumps(report),flush=True)
    return 0 if report['status']=='completed' else 1

if __name__=='__main__':raise SystemExit(main())
