"""Independent saved-artifact/CPU review; never fits weights or alters inputs."""
from collections import Counter
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT/'records/experiments/20261021-category-presence-v1'
MODELS = ROOT/'artifacts/models/skirt-category-presence-v1'
OUTPUT = ROOT/'records/validation/2026-10-21-category-presence-artifact-review.json'
CLASSES = ['skirt_present','no_skirt_pants','no_skirt_shorts','no_skirt_dress']
checks = {}
report = {'schema_version':1,'date_asia_manila':datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'reviewer':'agent_handoff_docs_oct21','checks':checks,'packages_installed':0,
          'training_performed':False,'camera_used':False,'pi_verified':False,
          'deployment_approved':False}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def check(name, condition):
    checks[name] = bool(condition)
    if not checks[name]:
        raise ValueError('Review failed: '+name)


def recompute_joint(rows, cached, probabilities):
    result = {}
    for name, mask in [('v1','v1'),('v2_plus_presence','v2')]:
        counts = dict(positive_count=0,positive_accepted=0,correct_pleating=0,
                      negative_count=0,negative_rejected=0)
        for row,p in zip(rows,probabilities):
            path = cached[row['sample_id']]['paths'][mask]
            accepted = path['accepted'] and (name == 'v1' or p >= .5)
            if row['presence_target']:
                counts['positive_count'] += 1
                counts['positive_accepted'] += int(accepted)
                counts['correct_pleating'] += int(accepted and path['pleating_prediction'] == row['label'])
            else:
                counts['negative_count'] += 1
                counts['negative_rejected'] += int(not accepted)
        result[name] = counts
    baseline,candidate = result['v1'],result['v2_plus_presence']
    criteria = {'accepted_skirts_preserved':candidate['positive_accepted'] >= baseline['positive_accepted'],
                'correct_pleating_preserved':candidate['correct_pleating'] >= baseline['correct_pleating'],
                'negative_rejection_improved':candidate['negative_rejected'] > baseline['negative_rejected']}
    return dict(result,development_criteria=criteria,eligible=all(criteria.values()))


def rank(joint,bce):
    if not joint['eligible']:
        return (1,0,0,0,bce)
    counts = joint['v2_plus_presence']
    return (0,-counts['negative_rejected'],-counts['correct_pleating'],-counts['positive_accepted'],bce)


def path_metrics(rows, name):
    positives = [r for r in rows if r['presence_target']]
    negatives = [r for r in rows if not r['presence_target']]
    accepted = [r for r in positives if r['paths'][name]['accepted']]
    correct = sum(r['paths'][name]['pleating_prediction'] == r['expected_pleating'] for r in accepted)
    rejected = sum(not r['paths'][name]['accepted'] for r in negatives)
    return dict(positive_count=len(positives),positive_accepted=len(accepted),
                positive_coverage=len(accepted)/len(positives),correct_pleating=correct,
                accepted_pleating_accuracy=correct/len(accepted) if accepted else None,
                negative_count=len(negatives),negative_rejected=rejected,
                negative_rejection=rejected/len(negatives))


def main():
    import numpy as np
    from PIL import Image
    run = load(ARCHIVE/'run.json')
    rows = load(ARCHIVE/'inputs.json')
    targets = load(ARCHIVE/'source-category-targets.json')
    target_map = {r['sample_id']:r for r in targets}
    val = [r for r in rows if r['split'] == 'development_validation']
    expected_ids = [r['sample_id'] for r in val]
    cache = load(ARCHIVE/'joint-comparison-cache.json')
    cached = {r['sample_id']:r for r in cache['results']}
    saved = load(ARCHIVE/'validation-predictions.json')
    history = load(ARCHIVE/'history.json')
    check('run_completed',run['status'] == 'completed')
    check('fixed_threshold_and_preprocessing',run['threshold'] == .5 and run['preprocessing'] ==
          'Full RGB resize224 Pillow bilinear; float32 0..255; normalization inside model')
    check('category_order',run['source_category_labels_in_output_order'] == CLASSES)
    check('exact_counts',len(rows) == 538 and len(val) == 118 and len(targets) == 538
          and Counter((r['split'],r['presence_target']) for r in rows) == {
              ('development_train',1):265,('development_train',0):155,
              ('development_validation',1):66,('development_validation',0):52})
    check('unique_source_and_target_ids',len({r['sample_id'] for r in rows}) == len(rows)
          and len(target_map) == len(targets))
    check('inputs_hash',sha(ARCHIVE/'inputs.json') == run['frozen_inputs_sha256'])
    check('derived_targets_hash',sha(ARCHIVE/'source-category-targets.json') == run['category_targets_sha256'])
    split_hash = hashlib.sha256(json.dumps(sorted((r['sample_id'],r['group_hash'],r['split']) for r in rows)).encode()).hexdigest()
    check('split_hash',split_hash == run['split_hash'])
    for source in run['executed_sources']:
        check('executed_'+source['path'],sha(ARCHIVE/source['path']) == source['sha256'])
    check('main_source_identity',sha(ARCHIVE/'train_category_presence.py') == run['source_sha256'])
    for source in run['inputs']+run['category_sources']:
        check('source_'+source['path'],sha(ROOT/source['path']) == source['sha256'])
    actual_hashes = {r['sample_id']:sha(ROOT/r['original_path']) for r in rows}
    check('all538_original_hashes',all(actual_hashes[r['sample_id']] == r['sha256'] for r in rows))
    report['original_files_rehashed'] = len(actual_hashes)
    train = [r for r in rows if r['split'] == 'development_train']
    check('no_cross_split_groups',not {r['group_hash'] for r in train}&{r['group_hash'] for r in val})
    check('no_cross_split_original_hashes',not {r['sha256'] for r in train}&{r['sha256'] for r in val})
    raw = {}
    for source in run['category_sources'][:-1]:
        raw.update({r['sample_id']:r for r in map(json.loads,(ROOT/source['path']).read_text(encoding='utf-8').splitlines())})
    for row in rows:
        target = target_map[row['sample_id']]
        for key in ('sample_id','sha256','original_path','group_id','group_hash','split','presence_target','source_item_id'):
            if target[key] != row[key]:
                raise ValueError('Derived target binding mismatch: '+row['sample_id'])
        if row['presence_target']:
            if target['category_target'] != 0 or target['source_category_annotation_ids'] != [row['source_labels']['annotation_id']]:
                raise ValueError('Positive target/annotation mismatch')
        else:
            original = raw[row['sample_id']]
            bucket = original['sampling_bucket']
            if bucket not in ('pants','shorts','dress') or target['category_target'] != CLASSES.index('no_skirt_'+bucket):
                raise ValueError('Negative target category mismatch')
            for key in ('source_id','source_item_id','source_partition','original_path','sha256','source_url','group_id','source_license','sampling_bucket','source_labels'):
                if original.get(key) != row.get(key):
                    raise ValueError('Raw negative binding mismatch')
            annotations = row['source_labels']['annotations']
            relevant = {a['category'] for a in annotations if a['category'] in ('pants','shorts','dress','skirt','jumpsuit')}
            expected_annotations = sorted(a['id'] for a in annotations if a['category'] == bucket)
            if relevant != {bucket} or target['source_category_annotation_ids'] != expected_annotations:
                raise ValueError('Negative scene category ambiguity')
        if target['category_label'] != CLASSES[target['category_target']] or target['independent_category_truth_verified'] is not False:
            raise ValueError('Category truth declaration mismatch')
    check('all538_derived_targets_match_raw_reviewed_inputs',True)
    category_counts = {s:dict(Counter(target_map[r['sample_id']]['category_label'] for r in rows if r['split']==s))
                       for s in ('development_train','development_validation')}
    check('category_counts',category_counts == run['category_counts_by_split'])
    check('cache_identity',sha(ARCHIVE/'joint-comparison-cache.json') == run['joint_comparison_cache']['sha256']
          == sha(ROOT/run['joint_comparison_cache']['path']))
    check('cache_inputs_and_validation_membership',cache['inputs_sha256'] == run['frozen_inputs_sha256']
          and set(cached) == set(expected_ids))
    check('all_saved_prediction_membership',[r['sample_id'] for r in saved] == expected_ids)
    check('eight_epochs_archived',len(history) == 8 and [r['epoch'] for r in history] == list(range(1,9)))
    candidate_ranks = []
    for record in history:
        epoch = record['epoch']
        predictions = load(ARCHIVE/f'epoch-{epoch:02d}-predictions.json')
        check(f'epoch{epoch}_prediction_membership',[r['sample_id'] for r in predictions] == expected_ids)
        matrix = np.asarray([r['category_probabilities'] for r in predictions],dtype=np.float64)
        check(f'epoch{epoch}_valid_probabilities',matrix.shape == (118,4) and np.isfinite(matrix).all()
              and (matrix>=0).all() and (matrix<=1).all() and np.allclose(matrix.sum(axis=1),1,rtol=0,atol=1e-5))
        check(f'epoch{epoch}_targets',all(p['category_target'] == target_map[r['sample_id']]['category_target'] for p,r in zip(predictions,val)))
        truth = np.asarray([r['presence_target'] for r in val])
        p = np.clip(matrix[:,0],1e-7,1-1e-7)
        loss = -(truth*np.log(p)+(1-truth)*np.log(1-p))
        bce = float((loss[truth==0].mean()+loss[truth==1].mean())/2)
        joint = recompute_joint(val,cached,matrix[:,0])
        epoch_rank = rank(joint,bce)
        check(f'epoch{epoch}_bce',abs(bce-record['balanced_validation_bce']) < 1e-6)
        check(f'epoch{epoch}_joint_and_eligibility',joint == record['joint_metrics'])
        check(f'epoch{epoch}_rank',list(epoch_rank[:-1]) == record['selection_rank'][:-1]
              and abs(epoch_rank[-1]-record['selection_rank'][-1]) < 1e-6)
        candidate_ranks.append((epoch_rank,epoch))
    selected = min(candidate_ranks)[1]
    check('selected_epoch_is_protocol_winner',selected == run['selected_epoch'] == 7)
    check('selected_eligible_no_fallback',run['selected_eligibility'] is True and run['any_epoch_eligible'] is True
          and run['selection_fallback_used'] is False)
    selected_probs = np.asarray([p['category_probabilities'] for p in load(ARCHIVE/f'epoch-{selected:02d}-predictions.json')])
    saved_probs = np.asarray([p['category_probabilities'] for p in saved])
    check('selected_probabilities_preserved',np.max(np.abs(selected_probs-saved_probs)) <= 1e-8)
    check('scalar_class0_saved_identity',all(r['probability'] == r['category_probabilities'][0] for r in saved))
    for phase in run['phase_invariants']:
        check(phase['phase']+'_frozen_digest',phase['frozen_weights_before_sha256'] == phase['frozen_weights_after_sha256'])
        check(phase['phase']+'_bn_frozen',phase['all_batch_normalization_frozen'] is True)
    check('model_run_copy',sha(MODELS/'run.json') == sha(ARCHIVE/'run.json'))
    check('scalar_export_hash',sha(MODELS/'model.tflite') == run['export']['sha256'])
    check('early_export_hash',sha(ARCHIVE/'early_export/model.tflite') == run['early_export']['sha256'])
    check('archived_export_parity',all(e['validation_images'] == 118 and e['tolerance'] == .001
          and e['maximum_absolute_error'] <= .001 for e in (run['early_export'],run['export'])))
    comparison_path = ROOT/'records/validation/2026-10-21-category-presence-comparison.json'
    comparison = load(comparison_path)
    old_path = ROOT/'records/validation/2026-10-19-detection-v4-comparison.json'
    old = load(old_path)
    check('comparison_completed_fixed_thresholds',comparison['status'] == 'completed'
          and comparison['fixed_presence_threshold'] == .5 and comparison['fixed_mask_threshold'] == .5)
    check('comparison_source_identity',comparison['source_sha256'] == sha(ARCHIVE/'check_detection_candidate.py'))
    check('comparison_inputs_split',comparison['inputs_sha256'] == run['frozen_inputs_sha256']
          and comparison['split_hash'] == run['split_hash'])
    check('comparison_export_identity',comparison['models']['presence'] == run['export']['sha256'])
    for name in ('v1','v2'):
        check('mask_'+name+'_identity',comparison['models']['masks'][name] == cache['models']['masks'][name]
              == sha(ROOT/f'artifacts/models/skirt-localizer-{name}/model.tflite'))
    check('comparison_pleating_identity',comparison['models']['pleating'] == old['models']['pleating']
          == sha(ROOT/'artifacts/releases/skirt-finetune-v1-desktop-research-v7/model.tflite'))
    check('comparison_exact_membership',[r['sample_id'] for r in comparison['results']] == expected_ids)
    for row in comparison['results']:
        source = next(r for r in val if r['sample_id'] == row['sample_id'])
        if row['presence_target'] != source['presence_target'] or row['expected_pleating'] != (source['label'] if source['presence_target'] else None):
            raise ValueError('Comparison truth binding mismatch')
        for name in ('v1','v2'):
            if row['paths'][name] != cached[row['sample_id']]['paths'][name]:
                raise ValueError('Historical mask outputs changed')
        for name in ('v1','v2'):
            accepted = row['paths'][name]['accepted'] and row['presence']['score'] >= .5
            if row['paths'][name+'_plus_presence']['accepted'] != accepted:
                raise ValueError('Comparison gate composition mismatch')
    check('cached_masks_and_composed_paths_reproduced',True)
    metrics = {name:path_metrics(comparison['results'],name) for name in ('v1','v2','v1_plus_presence','v2_plus_presence')}
    check('all_comparison_metrics_recomputed',metrics == comparison['metrics'])
    counts = recompute_joint(val,cached,[r['presence']['score'] for r in comparison['results']])
    check('actual_export_joint_matches_training',counts == run['selected_joint_metrics'])
    check('relative_development_gate',comparison['development_criteria_passed'] is True and comparison['deployment_approved'] is False)
    previous = old['metrics']['v2_plus_presence']
    current = metrics['v2_plus_presence']
    check('v4_comparable_frozen_inputs',old['inputs_sha256'] == comparison['inputs_sha256']
          and old['models']['masks'] == comparison['models']['masks']
          and old['fixed_presence_threshold'] == .5 and old['fixed_mask_threshold'] == .5)
    check('v4_coverage_and_correctness_preserved_rejection_improved',current['positive_accepted'] >= previous['positive_accepted']
          and current['correct_pleating'] >= previous['correct_pleating']
          and current['negative_rejected'] > previous['negative_rejected'])
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)
    check('cpu_only_review',not tf.config.list_physical_devices('GPU'))
    categories = tf.keras.models.load_model(MODELS/'category-model.keras')
    scalar = tf.keras.models.load_model(MODELS/'model.keras')
    check('keras_shapes',categories.input_shape == scalar.input_shape == (None,224,224,3)
          and categories.output_shape == (None,4) and scalar.output_shape == (None,1))
    bases = [layer for layer in categories.layers if layer.name.startswith('mobilenetv2')]
    check('single_reopened_backbone',len(bases) == 1)
    base = bases[0]
    check('reopened_bn_frozen',all(not layer.trainable for layer in base.layers if isinstance(layer,tf.keras.layers.BatchNormalization)))
    trainable = [layer.name for layer in base.layers if layer.trainable and layer.weights]
    check('reopened_trainable_layers',trainable == run['phase_invariants'][-1]['trainable_backbone_layers'])
    h = hashlib.sha256()
    for layer in [layer for layer in base.layers if not layer.trainable]:
        for weight in layer.weights:
            array = weight.numpy()
            h.update(layer.name.encode()); h.update(str(array.shape).encode())
            h.update(str(array.dtype).encode()); h.update(array.tobytes())
    check('reopened_actual_frozen_weights',h.hexdigest() == run['phase_invariants'][-1]['frozen_weights_after_sha256'])
    images = []
    for row in val:
        with Image.open(ROOT/row['original_path']) as image:
            images.append(np.asarray(image.convert('RGB').resize((224,224),Image.Resampling.BILINEAR),dtype=np.float32))
    x = np.stack(images)
    category_output = np.concatenate([categories(x[i:i+8],training=False).numpy() for i in range(0,len(x),8)])
    scalar_output = np.concatenate([scalar(x[i:i+8],training=False).numpy() for i in range(0,len(x),8)])[:,0]
    interpreter = tf.lite.Interpreter(model_path=str(MODELS/'model.tflite'),num_threads=2)
    interpreter.allocate_tensors()
    ins,outs = interpreter.get_input_details(),interpreter.get_output_details()
    check('tflite_tensor_contract',len(ins) == len(outs) == 1 and list(ins[0]['shape']) == [1,224,224,3]
          and list(outs[0]['shape']) == [1,1] and ins[0]['dtype'] == outs[0]['dtype'] == np.float32)
    lite = []
    for image in x:
        interpreter.set_tensor(ins[0]['index'],image[None]); interpreter.invoke()
        lite.append(float(interpreter.get_tensor(outs[0]['index'])[0,0]))
    lite = np.asarray(lite)
    check('all_reopened_predictions_valid',np.isfinite(category_output).all() and np.isfinite(scalar_output).all()
          and np.isfinite(lite).all() and np.allclose(category_output.sum(axis=1),1,rtol=0,atol=1e-5))
    errors = {'scalar_vs_category_component0':float(np.max(np.abs(scalar_output-category_output[:,0]))),
              'scalar_keras_vs_tflite':float(np.max(np.abs(scalar_output-lite))),
              'category_keras_vs_archived':float(np.max(np.abs(category_output-saved_probs))),
              'scalar_keras_vs_archived':float(np.max(np.abs(scalar_output-np.asarray([r['probability'] for r in saved])))),
              'tflite_vs_archived':float(np.max(np.abs(lite-np.asarray([r['tflite_probability'] for r in saved])))),
              'tflite_vs_actual_comparison':float(np.max(np.abs(lite-np.asarray([r['presence']['score'] for r in comparison['results']]))))}
    check('all118_reopened_parity',max(errors.values()) <= .001)
    check('scalar_class0_identity_all118',errors['scalar_vs_category_component0'] <= 1e-7)
    check('all118_threshold_decisions_preserved',np.array_equal(scalar_output>=.5,lite>=.5)
          and np.array_equal(lite>=.5,np.asarray([r['probability'] for r in saved])>=.5))
    truth = np.asarray([r['presence_target'] for r in val])
    targets_array = np.asarray([target_map[r['sample_id']]['category_target'] for r in val])
    winners = category_output.argmax(axis=1)
    confusion = [[int(sum((targets_array==a)&(winners==b))) for b in range(4)] for a in range(4)]
    check('standalone_metrics_and_confusion',float((scalar_output[truth==1]>=.5).mean()) == run['metrics']['skirt_recall']
          and float((scalar_output[truth==0]<.5).mean()) == run['metrics']['negative_rejection']
          and float((winners==targets_array).mean()) == run['metrics']['source_category_accuracy']
          and confusion == run['metrics']['source_category_confusion_true_rows_predicted_columns'])
    negative_categories = {}
    for label in CLASSES[1:]:
        selected_rows = [r for r in comparison['results'] if target_map[r['sample_id']]['category_label'] == label]
        negative_categories[label] = {'count':len(selected_rows),
            'accepted':sum(r['paths']['v2_plus_presence']['accepted'] for r in selected_rows),
            'rejected':sum(not r['paths']['v2_plus_presence']['accepted'] for r in selected_rows)}
    old_by_id = {r['sample_id']:r for r in old['results']}
    paired = {}
    for target,name in ((1,'positive'),(0,'negative')):
        counts = Counter((old_by_id[r['sample_id']]['paths']['v2_plus_presence']['accepted'],
                          r['paths']['v2_plus_presence']['accepted']) for r in comparison['results'] if r['presence_target']==target)
        paired[name] = {str(a)+'->'+str(b):count for (a,b),count in sorted(counts.items())}
    report.update(status='passed_artifact_and_development_checks_not_deployment_approval',
        category_counts=category_counts,selected_epoch=selected,selected_rank=run['selected_rank'],
        metrics=metrics,v4_reference_metrics=previous,negative_category_counts=negative_categories,
        paired_acceptance_v4_to_category=paired,
        actual_cpu_reopen={'originals':len(val),'models':['category-model.keras','model.keras','model.tflite'],
            'maximum_absolute_errors':errors,'tolerance':.001,'all_threshold_decisions_match':True},
        model_files=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
                     for p in (MODELS/'category-model.keras',MODELS/'model.keras',MODELS/'model.tflite')],
        source_files=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
                      for p in (ARCHIVE/'run.json',ARCHIVE/'inputs.json',ARCHIVE/'source-category-targets.json',
                                ARCHIVE/'history.json',comparison_path,old_path,Path(__file__))],
        review_runtime={'python':platform.python_version(),'tensorflow':tf.__version__,
                        'keras':importlib.metadata.version('keras'),'numpy':np.__version__,'device':'CPU'},
        limitations=['Repeated source-domain development groups informed the hypothesis and checkpoint selection; no independent test.',
            'Raw copied source-category joins were independently checked and official annotation bytes rehashed. The full542MB publisher JSON join was not independently rerun by this review; that join remains executed trainer/preflight evidence.',
            'Source scene categories and provisional absence reviews are not independent human-confirmed physical garment truth.',
            'This audit replays all eight saved epochs probabilities for selection arithmetic, but does not refit weights.',
            'Early scalar export was independently rehashed; its historical Keras checkpoint was not recreated.',
            'No live camera, actual garments, measured calibration, broad unknown-input rejection or Raspberry Pi verification.'])


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        report.update(status='failed',error=str(error))
        raise
    finally:
        report['checks_passed'] = sum(checks.values())
        report['checks_failed'] = sum(not result for result in checks.values())
        with OUTPUT.open('x',encoding='utf-8') as stream:
            json.dump(report,stream,indent=2,allow_nan=False); stream.write('\n')
        print(json.dumps({'status':report['status'],'checks_passed':report['checks_passed'],
                          'checks_failed':report['checks_failed'],'output':str(OUTPUT)}))
