"""Replay saved wearer/mask evidence against reviewed development annotations.

This runs the existing geometric extractor, not a landmark/segmentation model.
It never supplies missing observations, calibration or inferred anatomy.
"""
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageOps
from app.worn_geometry import QUALITY, extract_worn_geometry
from tools.build_measured_calibration import valid_hash, valid_source_path, text

CONVENTION = 'source_rgb_pixels_after_exif_transpose'
PROJECTION = 'upright_rectified_vertical'
AXES = ('hem_y', 'waist_y', 'floor_y')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def interval(value, height):
    return (isinstance(value, list) and len(value) == 2
            and all(number(v) and 0 <= v <= height - 1 for v in value)
            and value[0] <= value[1])


def ratio(geometry):
    values = [(h - w) / (f - w) for h, w, f in
              product(geometry['hem_y'], geometry['waist_y'], geometry['floor_y'])]
    return [min(values), max(values)]


def interval_discrepancy(predicted, truth):
    """Discrepancies against labelled intervals; midpoint is not measured truth."""
    return {'gap':max(0, truth[0] - predicted[1], predicted[0] - truth[1]),
            'midpoint_discrepancy':abs(sum(predicted) - sum(truth)) / 2,
            'maximum_endpoint_discrepancy':max(abs(a-b) for a, b in zip(predicted, truth)),
            'predicted_width':predicted[1] - predicted[0],
            'truth_width':truth[1] - truth[0],
            'contains_entire_truth_interval':predicted[0] <= truth[0] and predicted[1] >= truth[1]}


def truth_reason(example):
    if example.get('mode') != 'worn':
        return 'unsupported_presentation'
    if example.get('observed') is not True or example.get('reviewed') is not True:
        return 'truth_not_explicitly_observed_and_reviewed'
    if example.get('annotation_method') != 'manual_source_frame_intervals':
        return 'truth_annotation_method_not_declared_manual'
    if any(not text(example.get(k)) for k in ('reviewer', 'review_evidence')):
        return 'truth_review_provenance_missing'
    try:
        require(date.fromisoformat(example['review_date']).isoformat() == example['review_date'], 'date')
    except (KeyError, TypeError, ValueError):
        return 'truth_review_date_invalid'
    truth = example.get('truth')
    if not isinstance(truth, dict):
        return 'truth_geometry_missing'
    if (truth.get('reference_kind') != 'observed_body_landmarks'
            or truth.get('waist_kind') != 'visible_waist_reference'
            or truth.get('floor_kind') != 'visible_foot_floor_contact'):
        return 'unsupported_truth_anatomical_reference'
    quality = truth.get('quality')
    if not isinstance(quality, dict) or any(quality.get(k) is not True for k in QUALITY):
        return 'truth_geometry_quality_not_established'
    if any(not interval(truth.get(k), example['frame_size'][1]) for k in AXES):
        return 'truth_interval_invalid'
    if truth['waist_y'][1] >= truth['floor_y'][0]:
        return 'truth_reference_order_ambiguous'
    if truth['hem_y'][0] < truth['waist_y'][1] or truth['hem_y'][1] > truth['floor_y'][0]:
        return 'truth_hem_reference_order_ambiguous'
    return None


def validate_inventory(assignments):
    require(isinstance(assignments, list), 'Frozen split inventory must be a list')
    by_id, group_splits, hash_splits = {}, defaultdict(set), defaultdict(set)
    for row in assignments:
        require(isinstance(row, dict), 'Invalid split record')
        require(all(text(row.get(k)) for k in ('sample_id','garment_group_id','split')),
                'Split identity/group/membership required')
        require(valid_source_path(row.get('original_path')) and valid_hash(row.get('image_sha256')),
                'Split original path/hash required')
        require(row['sample_id'] not in by_id, 'Duplicate split identity')
        by_id[row['sample_id']] = row
        group_splits[row['garment_group_id']].add(row['split'])
        hash_splits[row['image_sha256']].add(row['split'])
    require(all(len(splits) == 1 for splits in group_splits.values()), 'Garment group crosses splits')
    require(all(len(splits) == 1 for splits in hash_splits.values()), 'Original file hash crosses splits')
    return by_id


def validate_original(example, assignment, root):
    require(isinstance(example, dict), 'Invalid annotation record')
    require(all(text(example.get(k)) for k in
                ('sample_id','garment_group_id','frame_id','camera_config_id','reference_id','person_id')),
            'Annotation sample/group/frame/camera/reference/person identity required')
    require(example.get('split') == 'development_validation' and assignment is not None
            and assignment['split'] == 'development_validation', 'Only frozen development_validation may be evaluated')
    require(all(example.get(k) == assignment[k] for k in
                ('garment_group_id','original_path','image_sha256')), 'Annotation/inventory original identity mismatch')
    size = example.get('frame_size')
    require(isinstance(size, list) and len(size) == 2 and all(type(v) is int and v >= 2 for v in size),
            'Invalid annotated source dimensions')
    original = (root / assignment['original_path']).resolve(strict=True)
    require(original.is_relative_to(root) and original.is_file(), 'Original path escapes source root')
    require(digest(original.read_bytes()) == assignment['image_sha256'], 'Original image SHA256 mismatch')
    with Image.open(original) as image:
        rgb = ImageOps.exif_transpose(image).convert('RGB')
        rgb.load()
        require(list(rgb.size) == size, 'Original dimensions do not match source coordinate convention')


def replay_prediction(example, prediction):
    if prediction is None:
        return {'status':'unavailable','reason':'prediction_missing','evidence':None}
    binding = ('sample_id','original_path','image_sha256','frame_id','frame_size',
               'camera_config_id','reference_id','person_id')
    if any(prediction.get(k) != example[k] for k in binding):
        return {'status':'unavailable','reason':'prediction_source_identity_mismatch','evidence':None}
    mask, wearer = prediction.get('mask_record'), prediction.get('wearer_record')
    if (not isinstance(mask, dict) or not isinstance(wearer, dict)
            or wearer.get('reference_id') != example['reference_id']
            or any(record.get('person_id') != example['person_id'] for record in (mask, wearer))):
        return {'status':'unavailable','reason':'prediction_wearer_or_reference_mismatch','evidence':None}
    return extract_worn_geometry(frame_id=example['frame_id'], camera_config_id=example['camera_config_id'],
                                 frame_size=example['frame_size'], mask_record=mask, wearer_record=wearer)


def evaluate(document, assignments, predictions, *, source_root, annotation_sha256,
             split_sha256, allow_synthetic=False):
    require(isinstance(document, dict) and type(document.get('schema_version')) is int
            and document['schema_version'] == 1,
            'Unsupported annotation schema')
    kind = document.get('data_kind')
    require(kind == 'observed_development_geometry_annotations'
            or (kind == 'synthetic_fixture' and allow_synthetic),
            'Observed annotations required; synthetic replay needs explicit opt-in')
    require(document.get('coordinate_convention') == CONVENTION
            and document.get('projection') == PROJECTION, 'Unsupported annotation coordinate convention/projection')
    require(valid_hash(annotation_sha256) and valid_hash(split_sha256), 'Input file hashes required')
    require(isinstance(predictions, dict) and type(predictions.get('schema_version')) is int
            and predictions['schema_version'] == 1
            and predictions.get('prediction_kind') == 'saved_geometry_extractor_inputs', 'Unsupported prediction schema')
    require(predictions.get('annotation_sha256') == annotation_sha256
            and predictions.get('split_sha256') == split_sha256, 'Prediction input hash binding mismatch')
    require(predictions.get('coordinate_convention') == CONVENTION
            and predictions.get('projection') == PROJECTION, 'Prediction coordinate convention/projection mismatch')
    producer = predictions.get('producer')
    require(isinstance(producer, dict) and text(producer.get('name'))
            and text(producer.get('evidence')) and valid_hash(producer.get('source_sha256')),
            'Saved prediction producer name/source hash/evidence required')
    inventory = validate_inventory(assignments)
    examples = document.get('examples')
    require(isinstance(examples, list), 'Annotation examples must be a list')
    example_ids, frames, original_hashes = set(), set(), set()
    root = Path(source_root).resolve(strict=True)
    require(root.is_dir(), 'Source root must be a directory')
    for example in examples:
        require(isinstance(example, dict), 'Invalid annotation record')
        validate_original(example, inventory.get(example.get('sample_id')), root)
        require(example['sample_id'] not in example_ids and example['frame_id'] not in frames
                and example['image_sha256'] not in original_hashes, 'Duplicate annotated sample/frame/original')
        example_ids.add(example['sample_id']); frames.add(example['frame_id'])
        original_hashes.add(example['image_sha256'])
    rows = predictions.get('predictions')
    require(isinstance(rows, list), 'Predictions must be a list')
    predicted = {}
    for row in rows:
        require(isinstance(row, dict) and row.get('sample_id') in example_ids
                and row['sample_id'] not in predicted, 'Duplicate or unknown predicted identity')
        predicted[row['sample_id']] = row
    results, excluded, abstentions = [], Counter(), Counter()
    groups = defaultdict(lambda: [0, 0])
    for example in examples:
        row = {k:example[k] for k in ('sample_id','garment_group_id','frame_id','original_path','image_sha256')}
        unsupported = truth_reason(example)
        if unsupported:
            excluded[unsupported] += 1
            row.update(status='annotation_excluded',reason=unsupported)
        else:
            groups[example['garment_group_id']][0] += 1
            outcome = replay_prediction(example, predicted.get(example['sample_id']))
            row.update(status=outcome['status'],reason=outcome['reason'])
            if outcome['status'] == 'extracted':
                groups[example['garment_group_id']][1] += 1
                truth, evidence = example['truth'], outcome['evidence']
                row['predicted_geometry'] = evidence
                row['truth_intervals'] = {key:truth[key] for key in AXES}
                row['interval_discrepancies_px'] = {key:interval_discrepancy(evidence[key],truth[key]) for key in AXES}
                row['waist_to_floor_ratio_discrepancy'] = interval_discrepancy(ratio(evidence),ratio(truth))
            else:
                abstentions[outcome['reason']] += 1
        results.append(row)
    eligible = sum(total for total, _ in groups.values())
    accepted = [r for r in results if r['status'] == 'extracted']
    summary = {}
    for axis in AXES:
        values = [r['interval_discrepancies_px'][axis] for r in accepted]
        summary[axis] = {key:(sum(v[key] for v in values)/len(values) if values else None)
                         for key in ('gap','midpoint_discrepancy','maximum_endpoint_discrepancy',
                                     'predicted_width','truth_width','contains_entire_truth_interval')}
    synthetic = kind == 'synthetic_fixture'
    return {'schema_version':1,'status':'synthetic_replay_only' if synthetic else 'development_saved_input_replay',
        'data_kind':kind,'annotation_sha256':annotation_sha256,'split_sha256':split_sha256,
        'coordinate_convention':CONVENTION,'projection':PROJECTION,'producer':producer,
        'counts':{'annotated_originals':len(examples),'eligible_reviewed_originals':eligible,
                  'observed_development_examples':0 if synthetic else eligible,
                  'synthetic_examples':len(examples) if synthetic else 0,
                  'annotation_excluded':sum(excluded.values()),'extracted':len(accepted),
                  'abstained':eligible-len(accepted),'declared_eligible_garment_groups':len(groups)},
        'annotation_exclusion_reasons':dict(excluded),'abstention_reasons':dict(abstentions),
        'image_coverage':len(accepted)/eligible if eligible else None,
        'declared_group_macro_coverage':sum(ok/total for total,ok in groups.values())/len(groups) if groups else None,
        'interval_discrepancy_means_px':summary,'results':results,
        'extractor_source_sha256':digest((ROOT/'app/worn_geometry.py').read_bytes()),
        'evaluation_source_sha256':digest(Path(__file__).read_bytes()),
        'model_inference_performed':False,'length_categories_evaluated':False,
        'physical_calibration_verified':False,'live_provider_enabled':False,'pi_verified':False,
        'limitations':['Saved inputs only; does not run a wearer or segmentation detector.',
            'Producer source hash is a declaration retained for audit, not independently verified model lineage.',
            'Human observations, association and group completeness are declarations, not certified by this tool.',
            'Midpoint/endpoint discrepancies compare uncertainty intervals; they are not physical-length MAE.',
            'Interval discrepancy means are image-weighted diagnostics; repeated views are correlated.',
            'Frame counts and declared source groups do not establish independent physical specimen counts.',
            'Excluded annotations stay listed; extraction coverage uses only eligible reviewed annotations.',
            'Unannotated validation inventory members are reported separately and do not enter coverage.',
            'All-column mask endpoints can include tapered side contours; replay preserves this known limitation.'],
        'unannotated_validation_inventory_members':sorted(sid for sid,row in inventory.items()
            if row['split'] == 'development_validation' and sid not in example_ids)}


def evaluate_from_files(annotations, splits, predictions, output, *, source_root, allow_synthetic=False):
    sources = [Path(p) for p in (annotations,splits,predictions)]
    raw = [p.read_bytes() for p in sources]
    report = evaluate(*map(json.loads,raw),source_root=source_root,
                      annotation_sha256=digest(raw[0]),split_sha256=digest(raw[1]),allow_synthetic=allow_synthetic)
    report['input_files'] = [{'path':str(p),'sha256':digest(body)} for p,body in zip(sources,raw)]
    rendered = json.dumps(report,indent=2,allow_nan=False) + '\n'
    with Path(output).open('x',encoding='utf-8') as stream:
        stream.write(rendered)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('annotations','splits','predictions','output','source-root'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--allow-synthetic',action='store_true',help='Test-only replay; observed count remains zero')
    args = parser.parse_args()
    try:
        report = evaluate_from_files(args.annotations,args.splits,args.predictions,args.output,
                                     source_root=args.source_root,allow_synthetic=args.allow_synthetic)
    except (OSError,ValueError,TypeError,KeyError) as error:
        print(json.dumps({'created':False,'error':str(error)})); return 1
    print(json.dumps({'created':True,'status':report['status'],'counts':report['counts'],
                      'image_coverage':report['image_coverage'],'pi_verified':False})); return 0


if __name__ == '__main__':
    raise SystemExit(main())
