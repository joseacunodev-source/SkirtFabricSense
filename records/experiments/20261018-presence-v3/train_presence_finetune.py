"""Prespecified worn-skirt presence candidate; run only after negative admission."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.training.train_presence import validate, sha, save
from tools.training.train_skirt_baseline import validate_rows

PREPROCESSING = 'Full RGB resize224 Pillow bilinear; float32 0..255; normalization inside model'
WORN_MANIFEST_SHA256 = '876bb315009592fdbcf0a646703b21d99801756f4e37b1807a66675bdbd98ec2'
SOURCE_SPLIT_SHA256 = 'df3b096e4d131db55852b20de075d811c95520d23766648928555d755fe8812c'


def phases():
    return [('head', 3, .001), ('finetune', 5, .00001)]


def safe_path(root, path):
    root = Path(root).resolve()
    path = (root / path).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError('Missing file or path outside workspace')
    return path


def prepare_rows(root, negative_manifest):
    root = Path(root).resolve()
    positive_path = safe_path(root, 'data/manifests/worn-pleating-development-v1.jsonl')
    negative_path = safe_path(root, negative_manifest)
    split_path = safe_path(root, 'data/manifests/source-skirt-development-splits.json')
    if sha(positive_path) != WORN_MANIFEST_SHA256 or sha(split_path) != SOURCE_SPLIT_SHA256:
        raise ValueError('Frozen positive manifest or source assignments changed')
    positives = [json.loads(s) for s in positive_path.read_text().splitlines() if s.strip()]
    assignments = {r['sample_id']: r for r in json.loads(split_path.read_text())['assignments']}
    validate_rows(positives, assignments)
    if Counter(r['split'] for r in positives) != {'development_train': 265, 'development_validation': 66}:
        raise ValueError('Frozen worn subset count changed')
    for row in positives:
        p = row.get('presentation_review', {})
        if (row.get('presentation') != 'worn' or p.get('presentation') != 'worn'
                or p.get('image_sha256') != row['sha256']
                or p.get('review_method') not in ('original_image_visual_inspection', 'contact_sheet_visual_inspection')
                or any(not isinstance(p.get(k), str) or not p[k].strip() for k in ('reviewer', 'evidence'))):
            raise ValueError('Missing hash-bound worn presentation')
    negatives = [json.loads(s) for s in negative_path.read_text().splitlines() if s.strip()]
    # Quarantined rows stay recorded in the manifest but cannot enter training.
    admitted = [r for r in negatives if r.get('training_eligibility', {}).get('approved') is True]
    for row in admitted:
        evidence = row.get('label_evidence', {})
        hashes = [evidence[k] for k in ('sha256', 'image_sha256') if k in evidence]
        if (not hashes or any(value != row['sha256'] for value in hashes)
                or ('sample_id' in evidence and evidence['sample_id'] != row['sample_id'])
                or ('original_path' in evidence and evidence['original_path'] != row['original_path'])):
            raise ValueError('Negative review hash or source identity does not match admission')
    rows = [{**r, 'presence_target': 1} for r in positives] + [{**r, 'presence_target': 0} for r in admitted]
    validate(rows)
    for row in rows:
        image = safe_path(root, row['original_path'])
        if sha(image) != row['sha256']:
            raise ValueError('Changed original image')
    return rows, (positive_path, negative_path, split_path)


def configure_backbone(base, phase, batch_norm_class):
    if phase not in ('head', 'finetune'):
        raise ValueError('Unknown phase')
    names = [layer.name for layer in base.layers]
    if 'block_13_expand' not in names:
        raise ValueError('MobileNetV2 block13 boundary missing')
    boundary = names.index('block_13_expand')
    base.trainable = phase == 'finetune'
    for index, layer in enumerate(base.layers):
        layer.trainable = (phase == 'finetune' and index >= boundary
                           and not isinstance(layer, batch_norm_class))
    return [layer.name for layer in base.layers if layer.trainable and layer.weights]


def balanced_weights(targets):
    counts = Counter(targets)
    if set(counts) != {0, 1}:
        raise ValueError('Both training classes required')
    return {k: len(targets) / (2 * counts[k]) for k in (0, 1)}


def weight_digest(layers):
    h = hashlib.sha256()
    for layer in layers:
        for weight in layer.weights:
            array = weight.numpy()
            h.update(layer.name.encode()); h.update(str(array.shape).encode())
            h.update(str(array.dtype).encode()); h.update(array.tobytes())
    return h.hexdigest()


def export_check(model, directory, x, expected, tf, np):
    directory.mkdir(exist_ok=False)
    model.export(str(directory / 'saved_model'), input_signature=[tf.TensorSpec([1, 224, 224, 3], tf.float32)])
    converter = tf.lite.TFLiteConverter.from_saved_model(str(directory / 'saved_model'))
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    blob = converter.convert()
    (directory / 'model.tflite').write_bytes(blob)
    interpreter = tf.lite.Interpreter(model_content=blob, num_threads=2)
    interpreter.allocate_tensors()
    inputs, outputs = interpreter.get_input_details(), interpreter.get_output_details()
    if (len(inputs) != 1 or len(outputs) != 1 or list(inputs[0]['shape']) != [1,224,224,3]
            or list(outputs[0]['shape']) != [1,1] or inputs[0]['dtype'] != np.float32
            or outputs[0]['dtype'] != np.float32):
        raise ValueError('Export tensor contract mismatch')
    result = []
    for image in x:
        interpreter.set_tensor(inputs[0]['index'], image[None]); interpreter.invoke()
        result.append(float(interpreter.get_tensor(outputs[0]['index'])[0,0]))
    delta = float(np.max(np.abs(np.asarray(result) - expected)))
    if not np.isfinite(delta) or delta > .001:
        raise ValueError('Export parity failed')
    return {'sha256': sha(directory/'model.tflite'), 'bytes': len(blob),
            'maximum_absolute_error': delta, 'tolerance': .001,
            'validation_images': len(result), 'pi_verified': False}, result


def run(out, negative_manifest, report):
    rows, inputs = prepare_rows(ROOT, negative_manifest)
    report['inputs'] = [{'path':str(p.relative_to(ROOT)), 'sha256':sha(p)} for p in inputs]
    save(out/'inputs.json', rows)
    report['frozen_inputs_sha256'] = sha(out/'inputs.json')
    report['split_hash'] = hashlib.sha256(json.dumps(sorted((r['sample_id'],r['group_hash'],r['split']) for r in rows)).encode()).hexdigest()
    report['class_counts_by_split'] = {s: dict(Counter(str(r['presence_target']) for r in rows if r['split']==s))
                                        for s in ('development_train','development_validation')}
    save(out/'run.json', report)
    import numpy as np
    from PIL import Image
    import tensorflow as tf
    gpus = tf.config.list_physical_devices('GPU')
    if not gpus: raise RuntimeError('GPU unavailable')
    for gpu in gpus: tf.config.experimental.set_memory_growth(gpu, True)
    tf.config.experimental.enable_tensor_float_32_execution(False)
    tf.keras.utils.set_random_seed(42)
    arrays = []
    for row in rows:
        with Image.open(ROOT/row['original_path']) as image:
            arrays.append(np.asarray(image.convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32))
    x = np.stack(arrays)
    y = np.asarray([r['presence_target'] for r in rows],dtype=np.float32)[:,None]
    train = np.asarray([i for i,r in enumerate(rows) if r['split']=='development_train'])
    val = np.asarray([i for i,r in enumerate(rows) if r['split']=='development_validation'])
    provenance_path = ROOT/'records/acquisitions/2026-10-04-mobilenetv2-weights.json'
    provenance = json.loads(provenance_path.read_text())
    weights_path = Path(provenance['path'])
    if not weights_path.is_file() or sha(weights_path) != provenance['sha256']:
        raise ValueError('Verified pretrained weights unavailable; no automatic download')
    base = tf.keras.applications.MobileNetV2(include_top=False,weights=str(weights_path),input_shape=(224,224,3),pooling='avg')
    inp = tf.keras.Input((224,224,3),name='rgb')
    z = base(tf.keras.layers.Rescaling(1/127.5,offset=-1)(inp),training=False)
    z = tf.keras.layers.Dense(64,activation='relu')(z)
    z = tf.keras.layers.Dropout(.2)(z)
    model = tf.keras.Model(inp,tf.keras.layers.Dense(1,activation='sigmoid',name='skirt_presence')(z))
    weights = balanced_weights([int(y[i,0]) for i in train])
    report.update(class_weights=weights, gpu=[str(g) for g in gpus],
                  versions={p:importlib.metadata.version(p) for p in ('tensorflow','keras','numpy','pillow')},
                  initial_weights_provenance={'path':str(provenance_path.relative_to(ROOT)),
                                               'record_sha256':sha(provenance_path),'weights_sha256':sha(weights_path)})
    report['phase_invariants'] = []
    rng = np.random.default_rng(42); best = float('inf'); history = []; global_epoch = 0
    def predict():
        return np.concatenate([model(x[val[i:i+8]],training=False).numpy() for i in range(0,len(val),8)])[:,0]
    for phase, epochs, lr in phases():
        trainable = configure_backbone(base, phase, tf.keras.layers.BatchNormalization)
        frozen = [layer for layer in base.layers if not layer.trainable]
        before = weight_digest(frozen)
        model.compile(optimizer=tf.keras.optimizers.Adam(lr),loss='binary_crossentropy')
        for epoch in range(epochs):
            global_epoch += 1; order = rng.permutation(train)
            for start in range(0,len(order),8):
                index = order[start:start+8]; bx = x[index].copy()
                flip = rng.random(len(index)) < .5; bx[flip] = bx[flip,:,::-1,:]
                model.train_on_batch(bx,y[index],sample_weight=np.asarray([weights[int(v)] for v in y[index,0]]))
            probability = predict(); truth = y[val,0]; p = np.clip(probability,1e-7,1-1e-7)
            loss = -(truth*np.log(p)+(1-truth)*np.log(1-p))
            balanced = float((loss[truth==0].mean()+loss[truth==1].mean())/2)
            if not np.isfinite(balanced): raise ValueError('Nonfinite validation loss')
            result = {'epoch':global_epoch,'phase':phase,'phase_epoch':epoch+1,'learning_rate':lr,
                      'balanced_validation_bce':balanced,'skirt_recall':float((probability[truth==1]>=.5).mean()),
                      'negative_rejection':float((probability[truth==0]<.5).mean())}
            history.append(result); save(out/'history.json',history); print(json.dumps(result),flush=True)
            if balanced < best:
                best = balanced; model.save_weights(out/'best.weights.h5'); report['selected_epoch'] = global_epoch
                report['selected_phase'] = phase
            if global_epoch == 1:
                report['early_export'], _ = export_check(model,out/'early_export',x[val],probability,tf,np)
            if weight_digest(frozen) != before: raise ValueError('Frozen backbone weights changed')
            save(out/'run.json',report)
        report['phase_invariants'].append({'phase':phase,'trainable_backbone_layers':trainable,
                                          'frozen_layer_names':[l.name for l in frozen],
                                          'frozen_weights_before_sha256':before,'frozen_weights_after_sha256':weight_digest(frozen),
                                          'all_batch_normalization_frozen':all(not l.trainable for l in base.layers if isinstance(l,tf.keras.layers.BatchNormalization))})
    model.load_weights(out/'best.weights.h5'); probability = predict()
    model.save(out/'model.keras')
    report['export'], exported = export_check(model,out/'final_export',x[val],probability,tf,np)
    shutil.copyfile(out/'final_export/model.tflite',out/'model.tflite')
    save(out/'validation-predictions.json',[{'sample_id':rows[i]['sample_id'],'split':rows[i]['split'],
        'group_hash':rows[i]['group_hash'],'target':int(y[i,0]),'probability':float(p),'tflite_probability':q}
        for i,p,q in zip(val,probability,exported)])
    truth = y[val,0]
    report['metrics'] = {'positive_validation':int(sum(truth==1)),'negative_validation':int(sum(truth==0)),
                         'skirt_recall':float((probability[truth==1]>=.5).mean()),
                         'negative_rejection':float((probability[truth==0]<.5).mean())}
    report['status'] = 'completed'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--negative-manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    # Fail admission before output creation or importing training frameworks.
    prepare_rows(ROOT,args.negative_manifest)
    args.output.mkdir(parents=True,exist_ok=False)
    start = time.monotonic()
    report = {'status':'started','started_at':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(__file__),
              'seed':42,'batch_size':8,'epochs':8,'phases':[{'name':p,'epochs':n,'learning_rate':lr} for p,n,lr in phases()],
              'threshold':.5,'optimizer':'Adam','selection':'Minimum class-balanced development-validation BCE across both phases',
              'preprocessing':PREPROCESSING,'augmentation':'Independent horizontal flip probability0.5 from seed42 generator',
              'architecture':'ImageNet MobileNetV2 avg + Dense64 ReLU + Dropout0.2 + sigmoid1; block13 onward finetuning excluding all BatchNorm',
              'limitations':['Joint worn-positive/negative-data and finetuning candidate; not a controlled single-change comparison',
                             'Agent-reviewed development data; independent human truth pending',
                             'No threshold tuning, untouched final-test evaluation, physical camera or Raspberry Pi verification',
                             'Frozen worn subset is reused explicitly for this research experiment; historical manifest remains immutable']}
    for source in (Path(__file__), ROOT/'tools/training/train_presence.py',ROOT/'tools/training/train_skirt_baseline.py'):
        shutil.copyfile(source,args.output/source.name)
    report['executed_sources'] = [{'path':p.name,'sha256':sha(p)} for p in args.output.glob('*.py')]
    try:
        subprocess.run([sys.executable,str(ROOT/'tools/collect_environment.py'),'--role','training-wsl-presence-finetune',
                        '--output',str(args.output/'environment.json')],check=True)
        run(args.output,args.negative_manifest,report)
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report.update(finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-start)
    save(args.output/'run.json',report)
    print(json.dumps(report),flush=True)
    return 0 if report['status']=='completed' else 1


if __name__ == '__main__': raise SystemExit(main())
