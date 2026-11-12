"""One declared four-way source-category experiment with scalar presence export."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import gc
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
from tools.training import train_presence_finetune as binary
from tools.training.train_presence import save, sha

CLASSES = ('skirt_present', 'no_skirt_pants', 'no_skirt_shorts', 'no_skirt_dress')
CATEGORY_IDS = {'pants': 6, 'shorts': 7, 'skirt': 8, 'dress': 10}
NEGATIVE_SHA256 = '82009d40445a9091f7998ab8479cec10b5086826001b7b9f513862bd11da52d1'
ANNOTATIONS = 'data/external/fashionpedia_train/instances_attributes_train2020.json'
ANNOTATIONS_SHA256 = 'f6af94fb8712bd8170a49c857e842e1227e6806c4f33f32340db0c849133e006'
RAW_MANIFESTS = {
    'data/manifests/negative-candidates-v1.jsonl': 'c4306ef7afacfde2e35daf1c6d5144c026075e5944180e2f38d46b9730470d02',
    'data/manifests/negative-candidates-v2.jsonl': '12328ba062b158a7c238c4bc6c1b57252f0a16e82001b37911c3c57839f50e3d',
    'data/manifests/negative-candidates-v3.jsonl': '45c69c3db6697ca5b82eed9856d12c3cfde92ce85467f67be75c8e4f1f7209d7',
}


def derive_targets(rows, raw_rows, official_annotations, official_categories):
    """Hierarchical scene labels, not mutually exclusive physical garment truth."""
    category_names = {r['id']: r['name'] for r in official_categories}
    if any(category_names.get(value) != name for name, value in CATEGORY_IDS.items()):
        raise ValueError('Official target category vocabulary changed')
    by_image = {}
    seen_annotations = set()
    for annotation in official_annotations:
        if annotation['id'] in seen_annotations:
            raise ValueError('Duplicate official annotation ID')
        seen_annotations.add(annotation['id'])
        by_image.setdefault(annotation['image_id'], []).append(annotation)
    raw = {}
    for row in raw_rows:
        if row['sample_id'] in raw:
            raise ValueError('Duplicate raw negative identity')
        raw[row['sample_id']] = row
    derived = []
    for row in rows:
        source_id = int(row['source_item_id'])
        annotations = by_image.get(source_id, [])
        if not annotations:
            raise ValueError('Missing official source image annotations')
        if row['presence_target']:
            selected = row.get('source_labels', {}).get('annotation_id')
            chosen = [a for a in annotations if a['id'] == selected and a['category_id'] == CATEGORY_IDS['skirt']]
            if len(chosen) != 1:
                raise ValueError('Positive selected skirt annotation mismatch')
            target = 0
            annotation_ids = [selected]
            basis = 'Frozen reviewed skirt-present scene; other clothing may co-occur'
        else:
            original = raw.get(row['sample_id'])
            if original is None:
                raise ValueError('Admitted negative missing raw acquisition identity')
            fields = ('source_id', 'source_item_id', 'source_partition', 'original_path',
                      'sha256', 'source_url', 'group_id', 'source_license',
                      'sampling_bucket', 'source_labels')
            if any(original.get(key) != row.get(key) for key in fields):
                raise ValueError('Raw/admitted negative category, hash, source or group mismatch')
            copied = original['source_labels'].get('annotations', [])
            official = {a['id']: a for a in annotations}
            if len(copied) != len(official) or {a['id'] for a in copied} != set(official):
                raise ValueError('Incomplete copied source annotation membership')
            for item in copied:
                actual = official[item['id']]
                if (item.get('category_id') != actual['category_id']
                        or item.get('category') != category_names.get(actual['category_id'])
                        or item.get('bbox') != actual.get('bbox')):
                    raise ValueError('Copied source annotation content mismatch')
            relevant = {category_names[a['category_id']] for a in annotations
                        if a['category_id'] in CATEGORY_IDS.values()
                        or category_names[a['category_id']] == 'jumpsuit'}
            bucket = row.get('sampling_bucket')
            if (bucket not in ('pants', 'shorts', 'dress') or relevant != {bucket}
                    or row['source_labels'].get('skirt_annotation_count') != 0):
                raise ValueError('Ambiguous mixed or unsupported source scene categories')
            target = CLASSES.index('no_skirt_' + bucket)
            annotation_ids = sorted(a['id'] for a in annotations if a['category_id'] == CATEGORY_IDS[bucket])
            basis = 'Reviewed skirt absence plus sole source-category bucket; category is publisher supervision'
        derived.append({'sample_id':row['sample_id'], 'sha256':row['sha256'],
            'original_path':row['original_path'], 'group_id':row['group_id'],
            'group_hash':row['group_hash'], 'split':row['split'],
            'presence_target':row['presence_target'], 'category_target':target,
            'category_label':CLASSES[target], 'source_item_id':row['source_item_id'],
            'source_category_annotation_ids':annotation_ids, 'label_basis':basis,
            'independent_category_truth_verified':False})
    if len({row['sample_id'] for row in derived}) != len(rows):
        raise ValueError('Duplicate derived scene identity')
    for split in ('development_train', 'development_validation'):
        if {r['category_target'] for r in derived if r['split'] == split} != set(range(4)):
            raise ValueError('Each development partition needs all four source categories')
    return derived


def prepare_category_rows(root, negative_manifest):
    root = Path(root).resolve()
    negative_path = binary.safe_path(root, negative_manifest)
    if sha(negative_path) != NEGATIVE_SHA256:
        raise ValueError('Frozen negative-v3 manifest changed')
    rows, inputs = binary.prepare_rows(root, negative_path)
    raw = []
    sources = []
    for path, digest in RAW_MANIFESTS.items():
        file = binary.safe_path(root, path)
        if sha(file) != digest:
            raise ValueError('Frozen raw category-source manifest changed')
        raw.extend(json.loads(line) for line in file.read_text(encoding='utf-8').splitlines() if line.strip())
        sources.append({'path':path, 'sha256':digest})
    file = binary.safe_path(root, ANNOTATIONS)
    if sha(file) != ANNOTATIONS_SHA256:
        raise ValueError('Official source annotation snapshot changed')
    with file.open(encoding='utf-8') as stream:
        annotations = json.load(stream)
    # Retain only current source images before deriving targets; release the large source JSON before TensorFlow.
    ids = {int(row['source_item_id']) for row in rows}
    selected = [item for item in annotations['annotations'] if item['image_id'] in ids]
    categories = annotations['categories']
    del annotations
    targets = derive_targets(rows, raw, selected, categories)
    sources.append({'path':ANNOTATIONS, 'sha256':ANNOTATIONS_SHA256})
    gc.collect()
    return rows, inputs, targets, sources


def make_models(tf, weights_path):
    base = tf.keras.applications.MobileNetV2(include_top=False, weights=str(weights_path),
                                           input_shape=(224,224,3), pooling='avg')
    inp = tf.keras.Input((224,224,3), name='rgb')
    features = base(tf.keras.layers.Rescaling(1/127.5, offset=-1)(inp), training=False)
    z = tf.keras.layers.Dense(64, activation='relu')(features)
    z = tf.keras.layers.Dropout(.2)(z)
    probabilities = tf.keras.layers.Dense(4, activation='softmax', name='source_categories')(z)
    model = tf.keras.Model(inp, probabilities, name='category_presence')
    scalar = tf.keras.Model(inp, probabilities[:,0:1], name='skirt_presence')
    return base, model, scalar


def run(out, negative_manifest, cache_path, report, prepared=None):
    rows, inputs, targets, category_sources = prepared or prepare_category_rows(ROOT, negative_manifest)
    save(out/'inputs.json', rows)  # Byte-identical binary inputs retain cache compatibility.
    save(out/'source-category-targets.json', targets)
    report.update(inputs=[{'path':str(p.relative_to(ROOT)), 'sha256':sha(p)} for p in inputs],
                  frozen_inputs_sha256=sha(out/'inputs.json'),
                  category_sources=category_sources, category_targets_sha256=sha(out/'source-category-targets.json'))
    cached, report['joint_comparison_cache'] = binary.load_joint_cache(ROOT, cache_path, out/'inputs.json', rows)
    shutil.copyfile(binary.safe_path(ROOT, cache_path), out/'joint-comparison-cache.json')
    if sha(out/'joint-comparison-cache.json') != report['joint_comparison_cache']['sha256']:
        raise ValueError('Cache changed while archiving')
    report['joint_comparison_cache']['archived_path'] = 'joint-comparison-cache.json'
    report['split_hash'] = hashlib.sha256(json.dumps(sorted((r['sample_id'],r['group_hash'],r['split']) for r in rows)).encode()).hexdigest()
    report['class_counts_by_split'] = {s:dict(Counter(str(r['presence_target']) for r in rows if r['split']==s))
                                       for s in ('development_train','development_validation')}
    report['category_counts_by_split'] = {s:dict(Counter(r['category_label'] for r in targets if r['split']==s))
                                          for s in ('development_train','development_validation')}
    save(out/'run.json', report)
    import numpy as np
    from PIL import Image
    import tensorflow as tf
    gpus = tf.config.list_physical_devices('GPU')
    if not gpus:
        raise RuntimeError('GPU unavailable')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    tf.config.experimental.enable_tensor_float_32_execution(False)
    tf.keras.utils.set_random_seed(42)
    images = []
    for row in rows:
        with Image.open(ROOT/row['original_path']) as image:
            images.append(np.asarray(image.convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32))
    x = np.stack(images)
    y = np.asarray([r['category_target'] for r in targets], dtype=np.int32)
    binary_y = np.asarray([r['presence_target'] for r in rows], dtype=np.int32)
    train = np.asarray([i for i,r in enumerate(rows) if r['split']=='development_train'])
    val = np.asarray([i for i,r in enumerate(rows) if r['split']=='development_validation'])
    provenance_path = ROOT/'records/acquisitions/2026-10-04-mobilenetv2-weights.json'
    provenance = json.loads(provenance_path.read_text())
    weights_path = Path(provenance['path'])
    if not weights_path.is_file() or sha(weights_path) != provenance['sha256']:
        raise ValueError('Verified pretrained weights unavailable; no automatic download')
    base, model, scalar = make_models(tf, weights_path)
    weights = binary.balanced_weights([int(binary_y[i]) for i in train])
    report.update(class_weights=weights, class_weight_basis='Same binary scene weights as v4; no source-category rebalancing',
        gpu=[str(g) for g in gpus], versions={p:importlib.metadata.version(p) for p in ('tensorflow','keras','numpy','pillow')},
        initial_weights_provenance={'path':str(provenance_path.relative_to(ROOT)),
                                   'record_sha256':sha(provenance_path),'weights_sha256':sha(weights_path)},
        phase_invariants=[])
    rng = np.random.default_rng(42)
    best_rank = None
    history = []
    global_epoch = 0
    def predict():
        return np.concatenate([model(x[val[i:i+8]], training=False).numpy() for i in range(0,len(val),8)])
    for phase, epochs, lr in binary.phases():
        trainable = binary.configure_backbone(base, phase, tf.keras.layers.BatchNormalization)
        frozen = [layer for layer in base.layers if not layer.trainable]
        before = binary.weight_digest(frozen)
        model.compile(optimizer=tf.keras.optimizers.Adam(lr), loss='sparse_categorical_crossentropy')
        for epoch in range(epochs):
            global_epoch += 1
            order = rng.permutation(train)
            for start in range(0,len(order),8):
                index = order[start:start+8]
                batch = x[index].copy()
                flip = rng.random(len(index)) < .5
                batch[flip] = batch[flip,:,::-1,:]
                model.train_on_batch(batch,y[index],sample_weight=np.asarray([weights[int(v)] for v in binary_y[index]]))
            categories = predict()
            probability = categories[:,0]
            truth = binary_y[val]
            p = np.clip(probability,1e-7,1-1e-7)
            losses = -(truth*np.log(p)+(1-truth)*np.log(1-p))
            balanced = float((losses[truth==0].mean()+losses[truth==1].mean())/2)
            joint = binary.joint_metrics(cached,probability)
            rank = binary.selection_rank(balanced,joint)
            result = {'epoch':global_epoch,'phase':phase,'phase_epoch':epoch+1,'learning_rate':lr,
                'balanced_validation_bce':balanced,'skirt_recall':float((probability[truth==1]>=.5).mean()),
                'negative_rejection':float((probability[truth==0]<.5).mean()),
                'source_category_accuracy':float((categories.argmax(axis=1)==y[val]).mean()),
                'selection_rank':list(rank),'joint_metrics':joint}
            history.append(result)
            save(out/'history.json',history)
            # Preserve all epoch probabilities so selected and unselected count arithmetic can be independently replayed.
            save(out/f'epoch-{global_epoch:02d}-predictions.json',[
                {'sample_id':rows[i]['sample_id'],'category_target':int(y[i]),
                 'category_probabilities':[float(v) for v in probabilities]}
                for i,probabilities in zip(val,categories)])
            print(json.dumps(result),flush=True)
            if best_rank is None or rank < best_rank:
                best_rank = rank
                model.save_weights(out/'best.weights.h5')
                report.update(selected_epoch=global_epoch, selected_phase=phase,
                    selected_rank=list(rank),selected_joint_metrics=joint,selected_eligibility=joint['eligible'])
            if global_epoch == 1:
                report['early_export'], _ = binary.export_check(scalar,out/'early_export',x[val],probability,tf,np)
            if binary.weight_digest(frozen) != before:
                raise ValueError('Frozen backbone weights changed')
            save(out/'run.json',report)
        report['phase_invariants'].append({'phase':phase,'trainable_backbone_layers':trainable,
            'frozen_layer_names':[layer.name for layer in frozen],
            'frozen_weights_before_sha256':before,'frozen_weights_after_sha256':binary.weight_digest(frozen),
            'all_batch_normalization_frozen':all(not layer.trainable for layer in base.layers if isinstance(layer,tf.keras.layers.BatchNormalization))})
    model.load_weights(out/'best.weights.h5')
    categories = predict()
    probability = categories[:,0]
    model.save(out/'category-model.keras')
    scalar.save(out/'model.keras')
    report['export'], exported = binary.export_check(scalar,out/'final_export',x[val],probability,tf,np)
    shutil.copyfile(out/'final_export/model.tflite',out/'model.tflite')
    save(out/'validation-predictions.json',[{'sample_id':rows[i]['sample_id'],'split':rows[i]['split'],
        'group_hash':rows[i]['group_hash'],'target':int(binary_y[i]),'category_target':int(y[i]),
        'category_probabilities':[float(v) for v in probabilities],
        'probability':float(p),'tflite_probability':q}
        for i,probabilities,p,q in zip(val,categories,probability,exported)])
    truth = binary_y[val]
    confusion = [[int(sum((y[val]==a)&(categories.argmax(axis=1)==b))) for b in range(4)] for a in range(4)]
    report['metrics'] = {'positive_validation':int(sum(truth==1)), 'negative_validation':int(sum(truth==0)),
        'skirt_recall':float((probability[truth==1]>=.5).mean()),'negative_rejection':float((probability[truth==0]<.5).mean()),
        'source_category_accuracy':float((categories.argmax(axis=1)==y[val]).mean()),
        'source_category_confusion_true_rows_predicted_columns':confusion}
    report.update(selected_joint_metrics=binary.joint_metrics(cached,probability),
        any_epoch_eligible=any(item['joint_metrics']['eligible'] for item in history))
    report['selected_eligibility'] = report['selected_joint_metrics']['eligible']
    report['selection_fallback_used'] = not report['any_epoch_eligible']
    report['status'] = 'completed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--negative-manifest',type=Path,required=True)
    parser.add_argument('--joint-comparison-cache',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    # Full source-category admission is checked before creating outputs or importing a framework.
    prepared = prepare_category_rows(ROOT,args.negative_manifest)
    args.output.mkdir(parents=True,exist_ok=False)
    start = time.monotonic()
    report = {'status':'started','started_at':datetime.now(timezone.utc).isoformat(),
        'source_sha256':sha(__file__),'seed':42,'batch_size':8,'epochs':8,
        'phases':[{'name':p,'epochs':n,'learning_rate':lr} for p,n,lr in binary.phases()],
        'threshold':.5,'optimizer':'Adam','selection':binary.JOINT_SELECTION,
        'preprocessing':binary.PREPROCESSING,
        'augmentation':'Independent horizontal flip probability0.5 from seed42 generator',
        'architecture':'ImageNet MobileNetV2 avg + Dense64 ReLU + Dropout0.2 + softmax4; scalar export is skirt probability',
        'source_category_labels_in_output_order':list(CLASSES),
        'loss':'Sparse categorical cross-entropy with unchanged binary scene sample weights',
        'limitations':['Four hierarchical source scene classes are publisher supervision plus provisional no-skirt review, not human-confirmed physical garment truth',
            'Positive class means skirt present; other clothing may co-occur in those scenes',
            'Reused development groups motivated hypothesis and select checkpoint; selection optimism requires independent testing',
            'Only three source negative categories; empty, unknown, partial and multiple-garment scene rejection remains unverified',
            'One declared candidate; no threshold tuning or final-test access',
            'No physical garments, camera, calibrated geometry, public-use or Raspberry Pi verification']}
    for source in (Path(__file__),Path(binary.__file__),ROOT/'tools/training/train_presence.py',ROOT/'tools/training/train_skirt_baseline.py'):
        shutil.copyfile(source,args.output/source.name)
    report['executed_sources'] = [{'path':p.name,'sha256':sha(p)} for p in args.output.glob('*.py')]
    try:
        subprocess.run([sys.executable,str(ROOT/'tools/collect_environment.py'),'--role','training-wsl-category-presence',
                        '--output',str(args.output/'environment.json')],check=True)
        run(args.output,args.negative_manifest,args.joint_comparison_cache,report,prepared)
    except Exception as exc:
        report.update(status='failed',error=str(exc),traceback=traceback.format_exc())
    report.update(finished_at=datetime.now(timezone.utc).isoformat(),duration_seconds=time.monotonic()-start)
    save(args.output/'run.json',report)
    print(json.dumps(report),flush=True)
    return 0 if report['status']=='completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
