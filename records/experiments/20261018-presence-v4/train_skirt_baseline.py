"""Recorded, grouped-development MobileNetV2 pleating pilot. No test-set access."""
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
LABELS = ['non_pleated', 'pleated']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def validate_rows(rows, assignments):
    """Fail closed before loading a framework or fitting any weights."""
    seen, groups = set(), {}
    counts = {'development_train': Counter(), 'development_validation': Counter()}
    for row in rows:
        sid = row['sample_id']
        if sid in seen:
            raise ValueError('Duplicate sample ID')
        seen.add(sid)
        if row['source_partition'] != 'train2020' or sid not in assignments:
            raise ValueError('Protected or unassigned source')
        assignment = assignments[sid]
        if row['split'] != assignment['split'] or row['group_hash'] != assignment['group_hash']:
            raise ValueError('Frozen split assignment changed')
        if row['split'] not in counts or row['label'] not in LABELS:
            raise ValueError('Unsupported split or label')
        review = row['label_evidence']
        if (review['full_skirt_view'] is not True or review.get('exclude_auxiliary', False)
                or review.get('review_conflict', False) or review['appearance_label'] != row['label'] or not review['evidence']):
            raise ValueError('Missing full-view visual evidence')
        if review['image_sha256'] != row['sha256']:
            raise ValueError('Review hash mismatch')
        group = row['group_hash']
        if group in groups and groups[group] != row['split']:
            raise ValueError('Connected group crosses development split')
        groups[group] = row['split']
        counts[row['split']][row['label']] += 1
    # Small pilot gate, not a claim of adequate final evaluation power.
    for label in LABELS:
        if counts['development_train'][label] < 10 or counts['development_validation'][label] < 5:
            raise ValueError('Insufficient class coverage for this pilot: ' + str(counts))
    return {split: dict(count) for split, count in counts.items()}


def metrics(truth, probabilities):
    import numpy as np
    predicted = np.argmax(probabilities, axis=1)
    confusion = np.zeros((2, 2), dtype=int)
    for actual, guess in zip(truth, predicted):
        confusion[actual, guess] += 1
    scores = []
    for i in range(2):
        tp = int(confusion[i, i])
        support, guesses = int(confusion[i].sum()), int(confusion[:, i].sum())
        precision = tp / guesses if guesses else 0.0
        recall = tp / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores.append(dict(label=LABELS[i], support=support, precision=precision, recall=recall, f1=f1))
    return dict(count=len(truth), accuracy=float(np.mean(predicted == truth)),
                macro_f1=sum(s['f1'] for s in scores)/2, per_class=scores,
                confusion_matrix_actual_rows_predicted_columns=confusion.tolist())


def run(args, report):
    import numpy as np
    from PIL import Image, ImageOps
    rows = [json.loads(line) for line in args.manifest.read_text(encoding='utf-8').splitlines() if line]
    original_split = ROOT/'data/manifests/source-skirt-development-splits.json'
    assignments = {r['sample_id']: r for r in json.loads(original_split.read_text())['assignments']}
    counts = validate_rows(rows, assignments)
    report.update(dataset_manifest_sha256=sha(args.manifest), split_manifest_sha256=sha(original_split),
                  image_counts=counts, independent_specimen_counts=None,
                  label_schema_version='reviewed_pleating_appearance_v1')
    shutil.copyfile(args.manifest, args.output/'dataset.jsonl')
    cache = Path('/home/skirttrain/skirt-fabric-sense/data-cache')
    cache.mkdir(parents=True, exist_ok=True)
    arrays, targets, selected, crop_records = {}, {}, {}, []
    for split in ['development_train', 'development_validation']:
        selected[split] = [r for r in rows if r['split'] == split]
        images, labels = [], []
        for row in selected[split]:
            source = (ROOT/row['original_path']).resolve()
            if not source.is_relative_to(ROOT) or sha(source) != row['sha256']:
                raise ValueError('Invalid source image path/hash: '+row['sample_id'])
            dest = cache/(row['sha256']+source.suffix)
            if not dest.exists():
                shutil.copyfile(source, dest)
            if sha(dest) != row['sha256']:
                raise ValueError('Corrupt training cache')
            with Image.open(dest) as original:
                image = original.convert('RGB')
                x, y, width, height = row['source_labels']['bbox']
                box = (max(0, math.floor(x-width*.05)), max(0, math.floor(y-height*.05)),
                       min(image.width, math.ceil(x+width*1.05)), min(image.height, math.ceil(y+height*1.05)))
                if box[2] <= box[0] or box[3] <= box[1]:
                    raise ValueError('Invalid source ROI')
                crop = ImageOps.pad(image.crop(box), (224,224), method=Image.Resampling.BILINEAR, color=(128,128,128))
                images.append(np.asarray(crop, dtype=np.uint8))
            labels.append(LABELS.index(row['label']))
            crop_records.append(dict(sample_id=row['sample_id'], source_sha256=row['sha256'],
                                     box_xyxy=box, split=split, group_hash=row['group_hash']))
        arrays[split], targets[split] = np.stack(images), np.array(labels)
    write(args.output/'preprocessing-records.json', crop_records)
    import tensorflow as tf
    gpus = tf.config.list_physical_devices('GPU')
    if not gpus:
        raise RuntimeError('A GPU is required for this training run')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    tf.keras.utils.set_random_seed(args.seed)
    if args.parent:
        tf.config.experimental.enable_tensor_float_32_execution(False)
    report['training_tf32_enabled'] = tf.config.experimental.tensor_float_32_execution_enabled()
    report['versions'] = {name: importlib.metadata.version(name) for name in ['tensorflow','keras','numpy','Pillow']}
    report['gpu_devices'] = [str(gpu) for gpu in gpus]
    report['architecture'] = 'ImageNet MobileNetV2 alpha1.0 frozen, global-average pooling, Dense2 softmax'
    report['preprocessing'] = 'Source annotated bbox plus 5% each side; RGB Pillow bilinear letterbox224; padding128; model Rescaling(1/127.5,offset=-1) exactly once'
    report['limitations'] = ['Development validation only; no final-test use', 'Agent appearance labels require independent confirmation',
        'Physical garment identity unresolved despite connected-group split', 'Manual source ROI; no automatic camera localization',
        'Web-image domain; no webcam, length, fabric or Raspberry Pi verification', 'No probability calibration or rejection threshold',
        'Source image and pretrained-weight redistribution rights require review before publishing weights']
    with tf.device('/GPU:0'):
        if args.parent:
            parent = json.loads((args.parent/'run.json').read_text())
            if parent['dataset_manifest_sha256'] != sha(args.manifest) or parent['split_manifest_sha256'] != sha(original_split):
                raise ValueError('Parent data/split differs; cannot silently change comparison')
            if parent['labels_in_output_order'] != LABELS:
                raise ValueError('Parent label order mismatch')
            model = tf.keras.models.load_model(args.parent/'model.keras', compile=False)
            base = next(layer for layer in model.layers if isinstance(layer, tf.keras.Model))
            base.trainable = True
            for i, layer in enumerate(base.layers):
                layer.trainable = i >= len(base.layers)-30 and not isinstance(layer, tf.keras.layers.BatchNormalization)
            report['parent'] = dict(run_id=parent['run_id'], report_sha256=sha(args.parent/'run.json'),
                                    checkpoint_sha256=sha(args.parent/'model.keras'))
            report['architecture'] = 'MobileNetV2 last30 backbone layers fine-tuned except BatchNorm; inherited head; BN inference mode'
        else:
            base = tf.keras.applications.MobileNetV2(input_shape=(224,224,3), include_top=False, weights='imagenet', pooling='avg')
            base.trainable = False
            inputs = tf.keras.Input((224,224,3), dtype=tf.float32, name='rgb_0_255')
            features = base(tf.keras.layers.Rescaling(1/127.5, offset=-1)(inputs), training=False)
            outputs = tf.keras.layers.Dense(2, activation='softmax', name='pleating')(features)
            model = tf.keras.Model(inputs, outputs)
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-5 if args.parent else 1e-3), loss='sparse_categorical_crossentropy', jit_compile=False)
        report['trainable_backbone_layers'] = [layer.name for layer in base.layers if layer.trainable]
        proof = model(arrays['development_train'][:1].astype(np.float32))
        if 'GPU:0' not in proof.device:
            raise RuntimeError('Forward pass did not execute on GPU')
        report['prediction_device'] = proof.device
    weights = Path.home()/'.keras/models/mobilenet_v2_weights_tf_dim_ordering_tf_kernels_1.0_224_no_top.h5'
    report['pretrained_weights'] = dict(path=str(weights), sha256=sha(weights),
        source='https://storage.googleapis.com/tensorflow/keras-applications/mobilenet_v2/'+weights.name,
        training_source='ImageNet', code_license='Keras Apache-2.0', weight_redistribution_status='not independently cleared')
    report['hyperparameters'] = dict(epochs=args.epochs, batch_size=args.batch_size, optimizer='Adam', learning_rate=1e-5 if args.parent else .001,
        backbone_frozen=not bool(args.parent), augmentation='horizontal flip p=.5; per-image brightness multiplier uniform[.9,1.1]' if args.augment else 'none', seed=args.seed,
        deterministic_ops=False, selection='minimum development validation cross entropy', threshold='argmax, uncalibrated')
    write(args.output/'run.json', report)
    train_x, train_y = arrays['development_train'], targets['development_train']
    val_x, val_y = arrays['development_validation'], targets['development_validation']
    nclass = np.bincount(train_y, minlength=2)
    sample_weights = len(train_y)/(2*nclass[train_y])
    rng = np.random.default_rng(args.seed)
    best_loss, history = float('inf'), []
    if args.parent:
        initial = np.concatenate([model(val_x[i:i+16].astype(np.float32), training=False).numpy() for i in range(0,len(val_y),16)])
        best_loss = float(-np.mean(np.log(np.maximum(initial[np.arange(len(val_y)),val_y],1e-7))))
        report['initial_validation_loss'] = best_loss
        report['selected_epoch'] = 0
        model.save_weights(args.output/'best.weights.h5')
    start = time.perf_counter()
    for epoch in range(args.epochs):
        order = rng.permutation(len(train_y))
        model.reset_metrics()
        for offset in range(0,len(order),args.batch_size):
            batch=order[offset:offset+args.batch_size]
            batch_x=train_x[batch].astype(np.float32)
            if args.augment:
                flip=rng.random(len(batch))<.5
                batch_x[flip]=batch_x[flip,:,::-1,:]
                batch_x=np.clip(batch_x*rng.uniform(.9,1.1,size=(len(batch),1,1,1)),0,255).astype(np.float32)
            model.train_on_batch(batch_x, train_y[batch], sample_weight=sample_weights[batch])
        probability = np.concatenate([model(val_x[i:i+16].astype(np.float32), training=False).numpy() for i in range(0,len(val_y),16)])
        if not np.isfinite(probability).all():
            raise RuntimeError('Nonfinite model predictions')
        loss = float(-np.mean(np.log(np.maximum(probability[np.arange(len(val_y)),val_y],1e-7))))
        result = dict(epoch=epoch+1, validation_loss=loss, **metrics(val_y, probability))
        history.append(result)
        write(args.output/'history.json',history)
        print(json.dumps(result),flush=True)
        if loss < best_loss:
            best_loss = loss
            model.save_weights(args.output/'best.weights.h5')
            report['selected_epoch'] = epoch+1
    model.load_weights(args.output/'best.weights.h5')
    tf.config.experimental.enable_tensor_float_32_execution(False)
    report['evaluation_tf32_enabled'] = False
    report['training_duration_seconds'] = time.perf_counter()-start
    report['gpu_memory'] = tf.config.experimental.get_memory_info('GPU:0')
    probability = np.concatenate([model(val_x[i:i+16].astype(np.float32), training=False).numpy() for i in range(0,len(val_y),16)])
    majority = int(np.argmax(nclass))
    majority_prob = np.tile(np.eye(2)[majority], (len(val_y),1))
    report['metrics'] = dict(model=metrics(val_y, probability), train_majority_baseline=metrics(val_y, majority_prob))
    model.save(args.output/'model.keras')
    model.export(str(args.output/'saved_model'), input_signature=[tf.TensorSpec([1,224,224,3],tf.float32)])
    converter = tf.lite.TFLiteConverter.from_saved_model(str(args.output/'saved_model'))
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    blob = converter.convert()
    (args.output/'model.tflite').write_bytes(blob)
    interpreter = tf.lite.Interpreter(model_content=blob,num_threads=2)
    interpreter.allocate_tensors()
    exported=[]
    for example in val_x:
        interpreter.set_tensor(interpreter.get_input_details()[0]['index'], example[None].astype(np.float32))
        interpreter.invoke()
        exported.append(interpreter.get_tensor(interpreter.get_output_details()[0]['index'])[0])
    exported=np.stack(exported)
    if not np.isfinite(exported).all():
        raise RuntimeError('Nonfinite TFLite output')
    delta=float(np.max(np.abs(exported-probability)))
    report['export'] = dict(sha256=hashlib.sha256(blob).hexdigest(), bytes=len(blob), maximum_absolute_error=delta,
        argmax_agreement=float(np.mean(np.argmax(exported,1)==np.argmax(probability,1))),
        tolerance_absolute=1e-3, metrics=metrics(val_y,exported), pi_verified=False)
    predictions=[dict(sample_id=row['sample_id'],group_hash=row['group_hash'], actual=LABELS[int(actual)],
         probabilities=p.tolist(),tflite_probabilities=q.tolist(),predicted=LABELS[int(np.argmax(p))])
         for row,actual,p,q in zip(selected['development_validation'],val_y,probability,exported)]
    write(args.output/'validation-predictions.json',predictions)
    if delta > 1e-3:
        raise RuntimeError('Export exceeded prespecified absolute parity tolerance')
    report['status']='completed'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=5)
    parser.add_argument('--seed',type=int,default=42)
    parser.add_argument('--parent',type=Path)
    parser.add_argument('--augment',action='store_true')
    parser.add_argument('--batch-size',type=int,default=16)
    args=parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error('epochs and batch size must be positive')
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(run_id=args.output.name,status='started',started_at=datetime.now(timezone.utc).isoformat(),
                source_sha256=sha(__file__),labels_in_output_order=LABELS)
    write(args.output/'run.json',report)
    shutil.copyfile(__file__,args.output/'training_source.py')
    try:
        subprocess.run([sys.executable,str(ROOT/'tools/collect_environment.py'),'--role','training-wsl-baseline',
                        '--output',str(args.output/'environment.json')],check=True)
        report['environment_snapshot'] = {'path':'environment.json','sha256':sha(args.output/'environment.json')}
        run(args,report)
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report['completed_at']=datetime.now(timezone.utc).isoformat()
    write(args.output/'run.json',report)
    print(json.dumps(report,indent=2),flush=True)
    return 0 if report['status']=='completed' else 1


if __name__=='__main__':
    raise SystemExit(main())
