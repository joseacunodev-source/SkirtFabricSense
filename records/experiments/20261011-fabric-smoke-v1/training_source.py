"""CPU-only source-appearance pipeline smoke. Never a deployable fabric model."""
import argparse, hashlib, json, os, shutil, subprocess, sys, time, traceback
from pathlib import Path
from datetime import datetime, timezone

os.environ['CUDA_VISIBLE_DEVICES']='-1'
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.datasets.prepare_fabric_pilot import CLASSES, sha

def save(p,v): Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')

def validate(rows, splits):
    assignments={r['sample_id']:r for r in splits['assignments']}
    if len(assignments)!=len(splits['assignments']) or len(rows)!=len(assignments): raise ValueError('Duplicate/missing split assignments')
    groups, hashes, ids = {}, set(), set()
    for r in rows:
        if r['sample_id'] in ids or r['sha256'] in hashes: raise ValueError('Duplicate sample')
        ids.add(r['sample_id']); hashes.add(r['sha256'])
        if r['source_partition']!='train' or r['admission_scope']!='internal_pipeline_smoke_only' or not r['training_admitted']: raise ValueError('Not admitted')
        if r['label'] not in CLASSES or r['split'] not in ['development_train','development_validation']: raise ValueError('Unknown label/split')
        if r['group_id'] in groups and groups[r['group_id']]!=r['split']: raise ValueError('Group leakage')
        groups[r['group_id']]=r['split']
        a=assignments.get(r['sample_id'])
        if not a or a['group_id']!=r['group_id'] or a['split']!=r['split']: raise ValueError('Split mismatch')
    for s in ['development_train','development_validation']:
        if {r['label'] for r in rows if r['split']==s}!=set(CLASSES): raise ValueError('Missing class')

def run(out,report):
    import numpy as np
    from PIL import Image, ImageOps
    import tensorflow as tf
    tf.config.set_visible_devices([], 'GPU')
    tf.config.threading.set_inter_op_parallelism_threads(1)
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.keras.utils.set_random_seed(42)
    manifest=ROOT/'data/labels/fabric-pilot-v1.jsonl'; split=ROOT/'data/labels/fabric-pilot-v1-splits.json'
    rows=[json.loads(x) for x in manifest.read_text().splitlines()]; validate(rows,json.loads(split.read_text()))
    report.update(dataset_manifest_sha256=sha(manifest),split_manifest_sha256=sha(split),classes=CLASSES)
    shutil.copyfile(manifest,out/'inputs.jsonl');shutil.copyfile(split,out/'splits.json')
    xs=[]
    for r in rows:
        p=ROOT/r['original_path']
        if sha(p)!=r['sha256']: raise ValueError('Changed source image')
        with Image.open(p) as im:
            rgb=im.convert('RGB').crop(r['roi_xyxy'])
            xs.append(np.asarray(ImageOps.pad(rgb,(224,224),method=Image.Resampling.BILINEAR,color=(128,128,128)),dtype=np.float32))
    x=np.stack(xs); y=np.array([CLASSES.index(r['label']) for r in rows])
    train=np.array([i for i,r in enumerate(rows) if r['split']=='development_train']); val=np.array([i for i,r in enumerate(rows) if r['split']=='development_validation'])
    base=tf.keras.applications.MobileNetV2(include_top=False,pooling='avg',weights='imagenet',input_shape=(224,224,3));base.trainable=False
    inp=tf.keras.Input((224,224,3),name='rgb');features=base(tf.keras.layers.Rescaling(1/127.5,offset=-1)(inp),training=False)
    encoder=tf.keras.Model(inp,features)
    features=np.concatenate([encoder(x[i:i+4],training=False).numpy() for i in range(0,len(x),4)])
    head=tf.keras.Sequential([tf.keras.Input((1280,)),tf.keras.layers.Dense(4,activation='softmax')])
    head.compile(optimizer=tf.keras.optimizers.Adam(.001),loss='sparse_categorical_crossentropy')
    # Fixed ten epochs; validation is never used for selection in this smoke run.
    counts=np.bincount(y[train],minlength=4);weights=len(train)/(4*counts)
    history=[];rng=np.random.default_rng(42)
    for epoch in range(10):
        order=rng.permutation(train)
        losses=[]
        for j in range(0,len(order),4):
            b=order[j:j+4];losses.append(float(head.train_on_batch(features[b],y[b],sample_weight=weights[y[b]])))
        history.append({'epoch':epoch+1,'reported_cumulative_training_loss':float(np.mean(losses))})
    model=tf.keras.Model(inp,head(encoder(inp),training=False))
    prob=model(x[val],training=False).numpy();pred=prob.argmax(1);truth=y[val]
    confusion=np.zeros((4,4),dtype=int)
    for a,b in zip(truth,pred):confusion[a,b]+=1
    f1=[]
    for c in range(4):
        tp=confusion[c,c];den=confusion[c,:].sum()+confusion[:,c].sum();f1.append(float(2*tp/den) if den else 0.)
    report.update(image_counts={'train':len(train),'validation':len(val)},independent_specimen_counts=None,source_item_counts={'train':len(train),'validation':len(val)},
      seed=42, architecture='Frozen ImageNet MobileNetV2 pooled features plus four-way softmax Dense',
      input_preprocessing='Manual reviewed source-pixel skirt ROI; RGB; PIL bilinear aspect-preserving pad224 gray128; float32 0..255; model normalization inside',
      augmentation='none',hyperparameters={'epochs':10,'batch':4,'optimizer':'Adam','learning_rate':.001,'class_weights':weights.tolist()},selection_rule='Fixed final epoch; validation not used for selection',
      versions={'tensorflow':tf.__version__,'numpy':np.__version__},pretrained_weights_source_and_license='records/acquisitions/2026-10-04-mobilenetv2-weights.json',
      metrics={'accuracy':float(np.mean(pred==truth)),'correct':int(np.sum(pred==truth)),'macro_f1':float(np.mean(f1)),'per_class_f1':f1,'confusion_matrix':confusion.tolist(),'majority_baseline_accuracy':float(np.mean(truth==counts.argmax()))},device='CPU only; GPU disabled')
    save(out/'history.json',history)
    save(out/'validation-predictions.json',[{'sample_id':rows[i]['sample_id'],'label':CLASSES[int(t)],'prediction':CLASSES[int(p)],'scores':v.tolist()} for i,t,p,v in zip(val,truth,pred,prob)])
    model.save(out/'model.keras');model.export(str(out/'saved_model'),input_signature=[tf.TensorSpec([1,224,224,3],tf.float32)])
    converter=tf.lite.TFLiteConverter.from_saved_model(str(out/'saved_model'));converter.target_spec.supported_ops=[tf.lite.OpsSet.TFLITE_BUILTINS]
    blob=converter.convert();(out/'model.tflite').write_bytes(blob)
    interpreter=tf.lite.Interpreter(model_content=blob,num_threads=2);interpreter.allocate_tensors();exported=[]
    for i in val:
        interpreter.set_tensor(interpreter.get_input_details()[0]['index'],x[i:i+1]);interpreter.invoke();exported.append(interpreter.get_tensor(interpreter.get_output_details()[0]['index'])[0])
    delta=float(np.abs(np.stack(exported)-prob).max())
    report['export']={'sha256':sha(out/'model.tflite'),'bytes':len(blob),'maximum_absolute_error':delta,'tolerance':.001,'class_agreement':bool(np.array_equal(np.stack(exported).argmax(1),pred)),'pi_verified':False,'live_approved':False}
    if delta>.001 or not report['export']['class_agreement']:raise RuntimeError('Export parity failed')
    report['status']='completed'

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    report={'run_id':a.output.name,'status':'started','started_at':datetime.now(timezone.utc).isoformat(),'objective':'Internal source-appearance pipeline smoke only','source_revision_or_hash_manifest':{'training':sha(__file__),'preparation':sha(ROOT/'tools/datasets/prepare_fabric_pilot.py')},'errors_and_limitations':['17 agent-reviewed source images only; 12 train and 5 validation','Two source item groups each for leather/chiffon; no credible performance estimate','Cotton/source fabric words are appearance labels, not composition','No final test, camera domain, hanging, held, mannequin or Pi verification','Manual ROIs do not validate automatic fabric integration','Not a deployment candidate; do not connect to live classifier']}
    shutil.copyfile(__file__,a.output/'training_source.py');shutil.copyfile(ROOT/'tools/datasets/prepare_fabric_pilot.py',a.output/'preparation_source.py')
    start=time.monotonic()
    try:
        subprocess.run([sys.executable,str(ROOT/'tools/collect_environment.py'),'--role','training-wsl-fabric-cpu-smoke','--output',str(a.output/'environment.json')],check=True)
        run(a.output,report)
    except Exception as exc:report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report.update(completed_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-start)
    save(a.output/'run.json',report);print(json.dumps(report),flush=True)
    return 0 if report['status']=='completed' else 1
if __name__=='__main__':raise SystemExit(main())
