"""Prespecified worn-skirt presence candidate; run only after negative admission."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
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
DEFAULT_SELECTION = 'Minimum class-balanced development-validation BCE across both phases'
JOINT_SELECTION = ('Eligible v2 mask plus new presence gate before ineligible epochs; '
                   'maximize rejected negatives, correct pleating, accepted skirts, then minimize balanced BCE; '
                   'fallback minimum balanced BCE if no epoch is eligible')


def load_joint_cache(root, cache_path, inputs_path, rows):
    """Verify immutable mask-only evidence; old presence fields are never consulted."""
    root = Path(root).resolve()
    path = safe_path(root, cache_path)
    cache = json.loads(path.read_text())
    if (cache.get('status') != 'completed' or cache.get('inputs_sha256') != sha(inputs_path)
            or cache.get('fixed_presence_threshold') != .5 or cache.get('fixed_mask_threshold') != .5):
        raise ValueError('Joint cache completion, inputs hash or fixed thresholds mismatch')
    source_hash = cache.get('source_sha256')
    if (not isinstance(source_hash, str) or len(source_hash) != 64
            or any(c not in '0123456789abcdef' for c in source_hash)):
        raise ValueError('Joint cache source hash missing or malformed')
    model_hashes = cache.get('models', {}).get('masks', {})
    for name in ('v1', 'v2'):
        directory = root / f'artifacts/models/skirt-localizer-{name}'
        model_path = safe_path(root, directory / 'model.tflite')
        run = json.loads(safe_path(root, directory / 'run.json').read_text())
        actual = sha(model_path)
        if (run.get('status') != 'completed' or run.get('export', {}).get('sha256') != actual
                or model_hashes.get(name) != actual):
            raise ValueError('Joint cache mask model hash or completed export mismatch')
    pleating_directory = root / 'artifacts/releases/skirt-finetune-v1-desktop-research-v7'
    pleating_path = safe_path(root, pleating_directory / 'model.tflite')
    pleating_manifest = json.loads(safe_path(root, pleating_directory / 'manifest.json').read_text())
    pleating_hash = sha(pleating_path)
    model_records = [item for item in pleating_manifest.get('files', []) if item.get('path') == 'model.tflite']
    if len(model_records) != 1 or model_records[0].get('sha256') != pleating_hash:
        raise ValueError('Historical pleating bundle model hash mismatch')
    validation = [r for r in rows if r['split'] == 'development_validation']
    expected = {r['sample_id']: r for r in validation}
    items = cache.get('results')
    if not isinstance(items, list) or len(expected) != len(validation) or len(items) != len(validation):
        raise ValueError('Joint cache validation membership mismatch')
    by_id = {}
    for item in items:
        sample_id = item.get('sample_id')
        if sample_id not in expected or sample_id in by_id:
            raise ValueError('Joint cache duplicate or unexpected validation identity')
        row = expected[sample_id]
        target = item.get('presence_target')
        label = row['label'] if row['presence_target'] else None
        if type(target) is not int or target != row['presence_target'] or item.get('expected_pleating') != label:
            raise ValueError('Joint cache target or expected pleating mismatch')
        # Copy only the original masks and resulting pleating. Ignore cached gated paths,
        # presence probabilities, summary metrics and historical selection decisions.
        clean = {'sample_id': sample_id, 'presence_target': target, 'expected_pleating': label, 'paths': {}}
        for name in ('v1', 'v2'):
            mask = item.get('paths', {}).get(name, {})
            accepted, prediction = mask.get('accepted'), mask.get('pleating_prediction')
            status = mask.get('localization', {}).get('status')
            if (type(accepted) is not bool
                    or status not in ('provisional', 'unavailable')
                    or accepted != (status == 'provisional')
                    or (accepted and prediction not in ('pleated', 'non_pleated'))
                    or (not accepted and prediction is not None)
                    or mask.get('localization', {}).get('model_sha256') != model_hashes[name]):
                raise ValueError('Joint cache mask acceptance, pleating or model identity mismatch')
            clean['paths'][name] = {'accepted': accepted, 'pleating_prediction': prediction}
        by_id[sample_id] = clean
    if set(by_id) != set(expected):
        raise ValueError('Joint cache missing validation identity')
    return [by_id[r['sample_id']] for r in validation], {
        'path': str(path.relative_to(root)), 'sha256': sha(path),
        'comparison_source_sha256': source_hash, 'inputs_sha256': cache['inputs_sha256'],
        'mask_model_sha256': {name: model_hashes[name] for name in ('v1', 'v2')},
        'pleating_lineage': {'path': str(pleating_path.relative_to(root)), 'sha256': pleating_hash,
            'basis': 'Historical comparison generator uses immutable research-v7; cache does not contain an explicit pleating model hash'},
        'validation_images': len(validation),
        'used_fields': 'Original v1/v2 mask acceptance and pleating only; historical presence ignored'}


def joint_metrics(cached_rows, probabilities):
    """Recompute coupled outcomes at fixed 0.5 using this epoch's probabilities."""
    if len(cached_rows) != len(probabilities):
        raise ValueError('Joint selection probability membership mismatch')
    predictions = [float(p) for p in probabilities]
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in predictions):
        raise ValueError('Joint selection probabilities must be finite within zero and one')
    result = {}
    for name in ('v1', 'v2_plus_presence'):
        counts = dict(positive_count=0, positive_accepted=0, correct_pleating=0,
                      negative_count=0, negative_rejected=0)
        mask_name = 'v1' if name == 'v1' else 'v2'
        for row, probability in zip(cached_rows, predictions):
            mask = row['paths'][mask_name]
            accepted = mask['accepted'] and (name == 'v1' or probability >= .5)
            if row['presence_target']:
                counts['positive_count'] += 1
                counts['positive_accepted'] += int(accepted)
                counts['correct_pleating'] += int(accepted and mask['pleating_prediction'] == row['expected_pleating'])
            else:
                counts['negative_count'] += 1
                counts['negative_rejected'] += int(not accepted)
        result[name] = counts
    candidate, baseline = result['v2_plus_presence'], result['v1']
    criteria = {'accepted_skirts_preserved': candidate['positive_accepted'] >= baseline['positive_accepted'],
                'correct_pleating_preserved': candidate['correct_pleating'] >= baseline['correct_pleating'],
                'negative_rejection_improved': candidate['negative_rejected'] > baseline['negative_rejected']}
    result['development_criteria'] = criteria
    result['eligible'] = all(criteria.values())
    return result


def selection_rank(balanced_bce, joint=None):
    """Lower lexicographic rank wins; strict comparisons retain the first exact tie."""
    if not math.isfinite(balanced_bce):
        raise ValueError('Nonfinite selection loss')
    if joint is None:
        return (balanced_bce,)
    if not joint['eligible']:
        return (1, 0, 0, 0, balanced_bce)
    counts = joint['v2_plus_presence']
    return (0, -counts['negative_rejected'], -counts['correct_pleating'],
            -counts['positive_accepted'], balanced_bce)


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


def run(out, negative_manifest, report, joint_comparison_cache=None):
    rows, inputs = prepare_rows(ROOT, negative_manifest)
    report['inputs'] = [{'path':str(p.relative_to(ROOT)), 'sha256':sha(p)} for p in inputs]
    save(out/'inputs.json', rows)
    report['frozen_inputs_sha256'] = sha(out/'inputs.json')
    cached_rows = None
    if joint_comparison_cache is not None:
        cached_rows, report['joint_comparison_cache'] = load_joint_cache(ROOT, joint_comparison_cache, out/'inputs.json', rows)
        shutil.copyfile(safe_path(ROOT, joint_comparison_cache), out/'joint-comparison-cache.json')
        if sha(out/'joint-comparison-cache.json') != report['joint_comparison_cache']['sha256']:
            raise ValueError('Joint cache changed while copying')
        report['joint_comparison_cache']['archived_path'] = 'joint-comparison-cache.json'
        report['selection'] = JOINT_SELECTION
        report['limitations'].append('Checkpoint selection explicitly reuses development chain outcomes; selection optimism requires independent testing')
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
    rng = np.random.default_rng(42); best_rank = None; history = []; global_epoch = 0
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
            joint = joint_metrics(cached_rows, probability) if cached_rows is not None else None
            rank = selection_rank(balanced, joint)
            result['selection_rank'] = list(rank)
            if joint is not None:
                result['joint_metrics'] = joint
            history.append(result); save(out/'history.json',history); print(json.dumps(result),flush=True)
            if best_rank is None or rank < best_rank:
                best_rank = rank; model.save_weights(out/'best.weights.h5'); report['selected_epoch'] = global_epoch
                report['selected_phase'] = phase
                report['selected_rank'] = list(rank)
                if joint is not None:
                    report['selected_joint_metrics'] = joint
                    report['selected_eligibility'] = joint['eligible']
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
    if cached_rows is not None:
        report['selected_joint_metrics'] = joint_metrics(cached_rows, probability)
        report['selected_eligibility'] = report['selected_joint_metrics']['eligible']
        report['any_epoch_eligible'] = any(item['joint_metrics']['eligible'] for item in history)
        report['selection_fallback_used'] = not report['any_epoch_eligible']
    report['status'] = 'completed'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--negative-manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--joint-comparison-cache',type=Path,
                        help='Optional verified frozen mask comparison; default retains minimum balanced BCE selection')
    args = parser.parse_args()
    # Fail admission before output creation or importing training frameworks.
    prepare_rows(ROOT,args.negative_manifest)
    args.output.mkdir(parents=True,exist_ok=False)
    start = time.monotonic()
    report = {'status':'started','started_at':datetime.now(timezone.utc).isoformat(),'source_sha256':sha(__file__),
              'seed':42,'batch_size':8,'epochs':8,'phases':[{'name':p,'epochs':n,'learning_rate':lr} for p,n,lr in phases()],
              'threshold':.5,'optimizer':'Adam','selection':JOINT_SELECTION if args.joint_comparison_cache else DEFAULT_SELECTION,
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
        run(args.output,args.negative_manifest,report,args.joint_comparison_cache)
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report.update(finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-start)
    save(args.output/'run.json',report)
    print(json.dumps(report),flush=True)
    return 0 if report['status']=='completed' else 1


if __name__ == '__main__': raise SystemExit(main())
