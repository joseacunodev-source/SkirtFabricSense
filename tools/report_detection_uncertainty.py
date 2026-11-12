"""Describe paired saved development predictions; never fit, infer or tune.

Intervals condition on reused development source groups. They do not correct
checkpoint-selection bias or establish independent garments/generalization.
Only Python's standard library is required.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
CLASSES = ('pleated', 'non_pleated')
PATH = 'v2_plus_presence'
DEFAULT_INPUTS = 'records/experiments/20261021-category-presence-v1/inputs.json'
DEFAULT_REPORTS = {
    'baseline': 'records/validation/2026-10-19-detection-v4-comparison.json',
    'candidate': 'records/validation/2026-10-21-category-presence-comparison.json',
}
DEFAULT_RUNS = {
    'baseline': 'records/experiments/20261018-presence-v4/run.json',
    'candidate': 'records/experiments/20261021-category-presence-v1/run.json',
}
LIMITATIONS = [
    'Reused source-domain development groups motivated hypotheses and selected checkpoints; these intervals do not correct selection optimism.',
    'Source groups are not independently verified physical garments; the observed group-size histogram is reported rather than assuming garment independence.',
    'Agent-reviewed labels lack independent human confirmation. No locked test, camera-domain accuracy, score calibration, public-demo acceptance or Raspberry Pi evidence is produced.',
    'Paired bootstrap conditions on these groups, their provisional labels and fixed saved predictions. Degenerate zero-delta intervals do not establish equivalence or a guaranteed absence of regression.',
    'Presence-stratified resampling holds the observed positive/negative group counts fixed; it does not estimate deployment class prevalence.',
    'Sparse per-class and negative-category slices are descriptive raw counts; their apparent rates are unstable.',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def split_hash(rows):
    """Exact serialization used by the archived training code."""
    return hashlib.sha256(json.dumps(sorted(
        (r['sample_id'], r['group_hash'], r['split']) for r in rows
    )).encode()).hexdigest()


def validate_inputs(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError('Nonempty archived input list required')
    ids, hashes, paths = set(), set(), set()
    group_splits, id_to_hash, hash_to_id, targets = {}, {}, {}, defaultdict(set)
    for row in rows:
        sid, digest, original = row.get('sample_id'), row.get('sha256'), row.get('original_path')
        if (not isinstance(sid, str) or not sid or not valid_hash(digest)
                or not isinstance(original, str) or not original):
            raise ValueError('Missing source image identity')
        if sid in ids or digest in hashes or original in paths:
            raise ValueError('Duplicate source image or sample identity')
        ids.add(sid); hashes.add(digest); paths.add(original)
        if row.get('source_partition') != 'train2020':
            raise ValueError('Protected or unsupported original source partition')
        split = row.get('split')
        if split not in ('development_train', 'development_validation'):
            raise ValueError('Invalid development split')
        target = row.get('presence_target')
        if type(target) is not int or target not in (0, 1):
            raise ValueError('Invalid presence truth')
        if row.get('label') not in (CLASSES if target else ('no_skirt',)):
            raise ValueError('Invalid pleating/absence truth')
        if not target and (
                row.get('training_eligibility', {}).get('approved') is not True
                or row.get('grouping_review_pending') is not False
                or row.get('label_evidence', {}).get('original_inspected') is not True):
            raise ValueError('Negative lacks archived original review/admission')
        gid, gh = row.get('group_id'), row.get('group_hash')
        if not isinstance(gid, str) or not gid or not valid_hash(gh):
            raise ValueError('Missing source group identity')
        if ((gid in id_to_hash and id_to_hash[gid] != gh)
                or (gh in hash_to_id and hash_to_id[gh] != gid)):
            raise ValueError('Source group aliases are inconsistent')
        id_to_hash[gid] = gh; hash_to_id[gh] = gid
        if gh in group_splits and group_splits[gh] != split:
            raise ValueError('Source group crosses development splits')
        group_splits[gh] = split; targets[gh].add(target)
    if any(len(value) != 1 for value in targets.values()):
        raise ValueError('Mixed-target source group cannot use presence-stratified bootstrap')
    for split in ('development_train', 'development_validation'):
        if {r['presence_target'] for r in rows if r['split'] == split} != {0, 1}:
            raise ValueError('Both presence classes required in each development split')
    return [r for r in rows if r['split'] == 'development_validation']


def validate_report(report, rows, inputs_digest, expected_split_hash):
    if (report.get('status') != 'completed'
            or report.get('inputs_sha256') != inputs_digest
            or report.get('split_hash') != expected_split_hash):
        raise ValueError('Saved comparison completion/input/split hash mismatch')
    if (type(report.get('fixed_presence_threshold')) not in (int, float)
            or report['fixed_presence_threshold'] != .5
            or type(report.get('fixed_mask_threshold')) not in (int, float)
            or report['fixed_mask_threshold'] != .5):
        raise ValueError('Fixed comparison thresholds changed')
    models = report.get('models', {})
    if not all(valid_hash(value) for value in (
            models.get('masks', {}).get('v2'), models.get('presence'), models.get('pleating'))):
        raise ValueError('Model identities missing or invalid')
    expected = {r['sample_id']: r for r in rows}
    results = report.get('results')
    if not isinstance(results, list) or len(results) != len(expected):
        raise ValueError('Saved comparison membership count mismatch')
    by_id = {}
    for item in results:
        sid = item.get('sample_id')
        if sid not in expected or sid in by_id:
            raise ValueError('Duplicate or unexpected validation identity')
        row = expected[sid]
        label = row['label'] if row['presence_target'] else None
        if (type(item.get('presence_target')) is not int
                or item['presence_target'] != row['presence_target']
                or item.get('expected_pleating') != label):
            raise ValueError('Saved comparison truth differs from frozen input')
        gate = item.get('presence', {})
        score = gate.get('score')
        if (type(score) not in (int, float) or not math.isfinite(score) or not 0 <= score <= 1
                or type(gate.get('accepted')) is not bool or gate['accepted'] != (score >= .5)
                or type(gate.get('threshold')) not in (int, float) or gate['threshold'] != .5
                or gate.get('model_sha256') != models['presence']):
            raise ValueError('Presence score/threshold/model/acceptance mismatch')
        for name in ('v2', PATH):
            path = item.get('paths', {}).get(name, {})
            accepted, prediction = path.get('accepted'), path.get('pleating_prediction')
            if (type(accepted) is not bool or (accepted and prediction not in CLASSES)
                    or (not accepted and prediction is not None)):
                raise ValueError('Saved acceptance/prediction inconsistent')
        mask, chain = item['paths']['v2'], item['paths'][PATH]
        localization = mask.get('localization', {})
        if (localization.get('status') not in ('provisional', 'unavailable')
                or mask['accepted'] != (localization['status'] == 'provisional')
                or localization.get('model_sha256') != models['masks']['v2']
                or (mask['accepted'] and localization.get('threshold') != .5)):
            raise ValueError('Mask threshold/model/status mismatch')
        accepted = mask['accepted'] and gate['accepted']
        if (chain['accepted'] != accepted
                or chain['pleating_prediction'] != (mask['pleating_prediction'] if accepted else None)):
            raise ValueError('Gated result differs from fixed saved mask/presence chain')
        by_id[sid] = item
    if set(by_id) != set(expected):
        raise ValueError('Missing validation identities')
    # Summary metrics are recomputed from the rows, not taken on trust.
    raw = raw_metrics(rows, by_id)
    archived = report.get('metrics', {}).get(PATH, {})
    for key in ('positive_count', 'positive_accepted', 'correct_pleating', 'negative_count', 'negative_rejected'):
        if type(archived.get(key)) is not int or archived[key] != raw[key]:
            raise ValueError('Archived aggregate count differs from saved rows')
    return by_id


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def raw_metrics(rows, predictions):
    positive = [r for r in rows if r['presence_target']]
    negative = [r for r in rows if not r['presence_target']]
    matrix = {label: {p: 0 for p in (*CLASSES, 'unavailable')} for label in CLASSES}
    for row in positive:
        path = predictions[row['sample_id']]['paths'][PATH]
        matrix[row['label']][path['pleating_prediction'] if path['accepted'] else 'unavailable'] += 1
    accepted = sum(matrix[label][p] for label in CLASSES for p in CLASSES)
    correct = sum(matrix[label][label] for label in CLASSES)
    rejected = sum(not predictions[r['sample_id']]['paths'][PATH]['accepted'] for r in negative)
    classes = {}
    for label in CLASSES:
        support = sum(matrix[label].values())
        n_accepted = support - matrix[label]['unavailable']
        tp = matrix[label][label]
        predicted_as = sum(matrix[truth][label] for truth in CLASSES)
        precision = ratio(tp, predicted_as)
        recall = ratio(tp, support)
        f1 = ratio(2 * tp, support + predicted_as)
        classes[label] = dict(support=support, accepted=n_accepted, unavailable=matrix[label]['unavailable'],
            correct=tp, wrong_accepted=n_accepted-tp, coverage=ratio(n_accepted, support),
            end_to_end_correctness=recall, accepted_accuracy=ratio(tp, n_accepted),
            precision_within_skirt_truth=precision, recall_including_unavailable=recall,
            f1_including_unavailable=f1)
    buckets = {}
    for bucket in sorted({r.get('sampling_bucket', 'unspecified') for r in negative}):
        members = [r for r in negative if r.get('sampling_bucket', 'unspecified') == bucket]
        n_rejected = sum(not predictions[r['sample_id']]['paths'][PATH]['accepted'] for r in members)
        buckets[bucket] = dict(count=len(members), rejected=n_rejected, falsely_accepted=len(members)-n_rejected)
    return dict(positive_count=len(positive), positive_accepted=accepted, positive_unavailable=len(positive)-accepted,
        positive_coverage=ratio(accepted, len(positive)), correct_pleating=correct,
        end_to_end_pleating_correctness=ratio(correct, len(positive)),
        accepted_pleating_accuracy=ratio(correct, accepted), negative_count=len(negative),
        negative_rejected=rejected, negative_falsely_accepted=len(negative)-rejected,
        negative_rejection=ratio(rejected, len(negative)),
        negative_false_acceptance=ratio(len(negative)-rejected, len(negative)),
        per_pleating_class=classes, confusion_matrix=matrix, negative_source_category_slices=buckets,
        precision_scope='Pleating precision uses true-skirt rows only; negative false acceptances are reported separately.')


def group_rates(rows, predictions):
    groups = defaultdict(list)
    for row in rows:
        path = predictions[row['sample_id']]['paths'][PATH]
        groups[row['group_hash']].append((row, path))
    result = {}
    for group, items in groups.items():
        target = items[0][0]['presence_target']
        result[group] = dict(target=target, count=len(items),
            accepted=sum(p['accepted'] for _, p in items)/len(items),
            correct=sum(r['presence_target'] == 1 and p['accepted'] and p['pleating_prediction'] == r['label']
                        for r, p in items)/len(items))
    return result


def aggregate_rates(groups, positive, negative):
    accepted = sum(groups[g]['accepted'] for g in positive)
    correct = sum(groups[g]['correct'] for g in positive)
    false_accepted = sum(groups[g]['accepted'] for g in negative)
    return dict(skirt_coverage=ratio(accepted, len(positive)),
        end_to_end_pleating_correctness=ratio(correct, len(positive)),
        accepted_pleating_accuracy=ratio(correct, accepted),
        negative_rejection=1-false_accepted/len(negative) if negative else None,
        negative_false_acceptance=ratio(false_accepted, len(negative)))


def percentile(values, q):
    """Linear interpolation of ordered finite values; no external library."""
    if not values:
        return None
    ordered = sorted(values)
    location = (len(ordered)-1)*q
    low = math.floor(location); high = math.ceil(location)
    return ordered[low] + (ordered[high]-ordered[low])*(location-low)


def paired_bootstrap(rows, baseline, candidate, *, resamples=2000, seed=42):
    if type(resamples) is not int or not 1 <= resamples <= 100000:
        raise ValueError('Resamples must be an integer in 1..100000')
    if type(seed) is not int:
        raise ValueError('Seed must be an integer')
    by_model = {name: group_rates(rows, value) for name, value in (('baseline', baseline), ('candidate', candidate))}
    positive = sorted(g for g, value in by_model['baseline'].items() if value['target'])
    negative = sorted(g for g, value in by_model['baseline'].items() if not value['target'])
    if not positive or not negative:
        raise ValueError('Both presence strata required for bootstrap')
    estimates = {name: aggregate_rates(value, positive, negative) for name, value in by_model.items()}
    samples = {name: defaultdict(list) for name in ('baseline', 'candidate', 'candidate_minus_baseline')}
    rng = random.Random(seed)
    for _ in range(resamples):
        pos = [rng.choice(positive) for _ in positive]
        neg = [rng.choice(negative) for _ in negative]
        pair = {name: aggregate_rates(value, pos, neg) for name, value in by_model.items()}
        for metric in estimates['baseline']:
            for name in ('baseline', 'candidate'):
                value = pair[name][metric]
                if value is not None:
                    samples[name][metric].append(value)
            a, b = pair['baseline'][metric], pair['candidate'][metric]
            if a is not None and b is not None:
                samples['candidate_minus_baseline'][metric].append(b-a)
    summary = {}
    for metric in estimates['baseline']:
        item = {}
        for name in samples:
            values = samples[name][metric]
            a, b = estimates['baseline'][metric], estimates['candidate'][metric]
            estimate = estimates[name][metric] if name in estimates else (b-a if a is not None and b is not None else None)
            item[name] = dict(estimate=estimate,
                percentile_95_interval=[percentile(values, .025), percentile(values, .975)] if values else None,
                defined_resamples=len(values), undefined_resamples=resamples-len(values))
        summary[metric] = item
    return dict(method='Paired source-group cluster bootstrap, stratified by frozen presence target; linear-interpolated percentile 2.5/97.5.',
        seed=seed, resamples=resamples, positive_source_groups=len(positive), negative_source_groups=len(negative),
        weighting='Equal source-group weight; within each group equal image weight. Accepted accuracy is ratio of group-mean correct to group-mean accepted, not mean of per-group accepted accuracies.',
        conditions='Same sampled groups, with all group members retained, are used for both models in every resample. No pleating-class stratification.',
        selection_bias_corrected=False, independent_generalization_established=False, metrics=summary)


def transitions(rows, baseline, candidate):
    positive, negative, changes = Counter(), Counter(), []
    for row in rows:
        sid = row['sample_id']
        a, b = baseline[sid]['paths'][PATH], candidate[sid]['paths'][PATH]
        def state(path):
            if not path['accepted']:
                return 'unavailable' if row['presence_target'] else 'rejected'
            if not row['presence_target']:
                return 'falsely_accepted'
            return 'correct' if path['pleating_prediction'] == row['label'] else 'wrong_pleating'
        sa, sb = state(a), state(b)
        (positive if row['presence_target'] else negative)[sa+' -> '+sb] += 1
        if a != b:
            changes.append(dict(sample_id=sid, group_id=row['group_id'], group_hash=row['group_hash'],
                presence_target=row['presence_target'], expected_pleating=row['label'] if row['presence_target'] else None,
                sampling_bucket=row.get('sampling_bucket'), baseline=a, candidate=b,
                baseline_state=sa, candidate_state=sb))
    return dict(skirt_states=dict(sorted(positive.items())), negative_states=dict(sorted(negative.items())),
        changed_results=changes, unchanged_results=len(rows)-len(changes))


def evaluate(rows, baseline, candidate, *, inputs_digest, resamples=2000, seed=42, expected_validation_count=None):
    if not valid_hash(inputs_digest):
        raise ValueError('Invalid input file hash')
    validation = validate_inputs(rows)
    if expected_validation_count is not None and len(validation) != expected_validation_count:
        raise ValueError('Frozen validation size differs from expected protocol')
    frozen_split = split_hash(rows)
    a = validate_report(baseline, validation, inputs_digest, frozen_split)
    b = validate_report(candidate, validation, inputs_digest, frozen_split)
    if (baseline['models']['masks']['v2'] != candidate['models']['masks']['v2']
            or baseline['models']['pleating'] != candidate['models']['pleating']):
        raise ValueError('Mask/pleating identities differ between paired reports')
    if any(a[sid]['paths']['v2'] != b[sid]['paths']['v2'] for sid in a):
        raise ValueError('Saved mask-only/pleating results differ between paired reports')
    return dict(schema_version=1, status='completed_saved_prediction_analysis',
        evidence_kind='Reused source-domain development; no new inference, fitting, threshold selection or final-test access.',
        limitations=list(LIMITATIONS), inputs_sha256=inputs_digest, split_hash=frozen_split,
        evaluated_path=PATH, fixed_presence_threshold=.5, fixed_mask_threshold=.5,
        inventory=dict(all_input_images=len(rows), all_source_groups=len({r['group_hash'] for r in rows}),
            training_images=sum(r['split'] == 'development_train' for r in rows),
            validation_images=len(validation), validation_source_groups=len({r['group_hash'] for r in validation}),
            validation_group_size_histogram=dict(Counter(str(n) for n in Counter(r['group_hash'] for r in validation).values())),
            mixed_target_groups=0, cross_split_groups=0, original_partition='train2020',
            independent_physical_garment_count=None, source_group_identity_verified_as_physical_garment=False),
        models=dict(baseline=baseline['models'], candidate=candidate['models']),
        raw_image_metrics=dict(baseline=raw_metrics(validation, a), candidate=raw_metrics(validation, b)),
        paired_transitions=transitions(validation, a, b),
        equal_source_group_bootstrap=paired_bootstrap(validation, a, b, resamples=resamples, seed=seed),
        new_inference_jobs=0, training_runs=0, thresholds_changed=False, deployment_approved=False,
        public_demonstration_accepted=False, pi_verified=False)


def safe_path(root, value):
    path = (root/value).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Evidence path escapes source workspace')
    return path


def validate_manifest_bindings(inputs, positives, negatives, assignments):
    """Join exact frozen rows, including truth, grouping, review and source split."""
    admitted = [r for r in negatives if r.get('training_eligibility', {}).get('approved') is True]
    expected = [{**r, 'presence_target':1} for r in positives] + [{**r, 'presence_target':0} for r in admitted]
    expected_by_id = {r['sample_id']:r for r in expected}
    actual_by_id = {r['sample_id']:r for r in inputs}
    if (len(expected_by_id) != len(expected) or len(actual_by_id) != len(inputs)
            or actual_by_id != expected_by_id):
        raise ValueError('Archived input truth/group/split/source rows differ from frozen manifests')
    by_id = {r['sample_id']:r for r in assignments}
    if len(by_id) != len(assignments):
        raise ValueError('Duplicate source split assignment')
    for row in positives:
        assigned = by_id.get(row['sample_id'], {})
        if any(row.get(k) != assigned.get(k) for k in ('sample_id', 'group_hash', 'split')):
            raise ValueError('Frozen positive differs from original grouped split assignment')


def evaluate_files(root, *, resamples=2000, seed=42):
    root = Path(root).resolve()
    evidence = {}
    def read(path):
        file = safe_path(root, path)
        evidence[path] = dict(path=path, sha256=sha(file))
        return json.loads(file.read_text(encoding='utf-8'))
    inputs = read(DEFAULT_INPUTS)
    digest = evidence[DEFAULT_INPUTS]['sha256']
    reports = {name: read(path) for name, path in DEFAULT_REPORTS.items()}
    runs = {name: read(path) for name, path in DEFAULT_RUNS.items()}
    required_manifests = {
        'data/manifests/worn-pleating-development-v1.jsonl',
        'data/labels/negative-reviewed-v3.jsonl',
        'data/manifests/source-skirt-development-splits.json',
    }
    for name, run in runs.items():
        if (run.get('status') != 'completed' or run.get('frozen_inputs_sha256') != digest
                or run.get('split_hash') != split_hash(inputs)
                or run.get('threshold') != .5
                or run.get('export', {}).get('sha256') != reports[name]['models']['presence']):
            raise ValueError('Completed archived run/input/split/export mismatch')
        references = run.get('inputs', [])
        if len(references) != 3 or {r.get('path') for r in references} != required_manifests:
            raise ValueError('Required frozen source manifest references missing')
        for reference in references:
            source = safe_path(root, reference['path'])
            if sha(source) != reference['sha256']:
                raise ValueError('Frozen source manifest changed')
            evidence[reference['path']] = dict(reference)
        for reference in run.get('executed_sources', []):
            source = safe_path(root, Path(DEFAULT_RUNS[name]).parent/reference['path'])
            if sha(source) != reference['sha256']:
                raise ValueError('Archived training source changed')
            path = source.relative_to(root).as_posix()
            evidence[path] = dict(path=path, sha256=sha(source))
        archived_inputs = safe_path(root, Path(DEFAULT_RUNS[name]).parent/'inputs.json')
        if sha(archived_inputs) != digest:
            raise ValueError('Paired archived input files differ')
        path = archived_inputs.relative_to(root).as_posix()
        evidence[path] = dict(path=path, sha256=digest)
    def jsonlines(path):
        return [json.loads(line) for line in safe_path(root, path).read_text(encoding='utf-8').splitlines() if line.strip()]
    assignments = json.loads(safe_path(root, 'data/manifests/source-skirt-development-splits.json').read_text(encoding='utf-8'))['assignments']
    validate_manifest_bindings(inputs, jsonlines('data/manifests/worn-pleating-development-v1.jsonl'),
                               jsonlines('data/labels/negative-reviewed-v3.jsonl'), assignments)
    # Bind reporting code and actual immutable exported bytes. No model runtime is loaded.
    checker = safe_path(root, 'tools/check_detection_candidate.py')
    if any(report.get('source_sha256') != sha(checker) for report in reports.values()):
        raise ValueError('Saved comparison source identity mismatch')
    evidence['tools/check_detection_candidate.py'] = dict(path='tools/check_detection_candidate.py', sha256=sha(checker))
    model_files = {
        'masks': 'artifacts/models/skirt-localizer-v2/model.tflite',
        'pleating': 'artifacts/releases/skirt-finetune-v1-desktop-research-v7/model.tflite',
    }
    for name, report in reports.items():
        files = dict(model_files, presence='artifacts/models/'+('skirt-presence-v4' if name == 'baseline' else 'skirt-category-presence-v1')+'/model.tflite')
        for kind, path in files.items():
            actual = sha(safe_path(root, path))
            expected = report['models']['masks']['v2'] if kind == 'masks' else report['models'][kind]
            if actual != expected:
                raise ValueError('Exported model bytes differ from saved comparison')
            evidence[path] = dict(path=path, sha256=actual)
    report = evaluate(inputs, reports['baseline'], reports['candidate'], inputs_digest=digest,
                      resamples=resamples, seed=seed, expected_validation_count=118)
    if report['inventory']['all_input_images'] != 538 or report['inventory']['training_images'] != 420:
        raise ValueError('Frozen full input membership size changed')
    source = Path(__file__).resolve()
    report.update(recorded_utc=datetime.now(timezone.utc).isoformat(),
        source=dict(path=source.relative_to(root).as_posix(), sha256=sha(source)),
        evidence=[evidence[k] for k in sorted(evidence)],
        runtime=dict(executable=sys.executable, python=sys.version, platform=platform.platform(),
                     dependencies='Python standard library only; no package installation or model runtime used.'))
    report['inventory']['original_image_bytes_rehashed_in_this_analysis'] = False
    report['inventory']['original_image_integrity_scope'] = 'Frozen image digests and metadata were joined; this report reads saved predictions and does not reopen original image bytes.'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--resamples', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Preserve completed report: '+str(args.output))
    result = evaluate_files(args.root, resamples=args.resamples, seed=args.seed)
    with args.output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(output=str(args.output), validation_images=result['inventory']['validation_images'],
        baseline=result['raw_image_metrics']['baseline']['negative_rejected'],
        candidate=result['raw_image_metrics']['candidate']['negative_rejected'], new_inference_jobs=0)))


if __name__ == '__main__':
    main()
