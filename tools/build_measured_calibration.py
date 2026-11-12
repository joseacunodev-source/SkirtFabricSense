"""Build boundaries from reviewed development measurements, never defaults."""
import argparse
from datetime import date
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.geometry import validate_profile
from app.hemline import LABELS, MODES


QUALITY = ('full_skirt_visible', 'single_garment', 'reference_associated',
           'projection_valid', 'hem_visible', 'waist_reference_valid', 'floor_reference_valid')
REFERENCE_KINDS = {'worn': ('observed_body_landmarks',),
                   'hanging': ('calibrated_standard_body',),
                   'held': ('calibrated_standard_body',),
                   'mannequin': ('observed_mannequin_landmarks', 'calibrated_standard_body')}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def valid_source_path(value):
    # Canonical forward-slash relative paths work consistently on Windows/Linux.
    return (text(value) and not value.startswith('/') and '\\' not in value and ':' not in value
            and all(part not in ('', '.', '..') for part in value.split('/')))


def build_profile(document, assignments, *, annotation_sha256, split_sha256):
    """Validate declared observations and propagate interval endpoints.

    This checks evidence structure and declared inventory consistency. It cannot
    certify that a human's measurements or an inventory's completeness are true.
    """
    if (not isinstance(document, dict) or type(document.get('schema_version')) is not int
            or document['schema_version'] != 1):
        raise ValueError('annotation schema_version must be 1')
    if document.get('data_kind') != 'observed_development_annotations':
        raise ValueError('observed development annotations required')
    for key in ('profile_id', 'camera_config_id', 'reference_id', 'measurement_evidence'):
        if not text(document.get(key)):
            raise ValueError(key + ' required')
    mode = document.get('mode')
    if mode not in MODES:
        raise ValueError('one supported presentation mode required')
    if document.get('projection') != 'upright_rectified_vertical':
        raise ValueError('verified upright rectified projection required')
    size = document.get('frame_size')
    if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or v <= 0 for v in size):
        raise ValueError('invalid frame_size')
    for value in (annotation_sha256, split_sha256):
        if not valid_hash(value):
            raise ValueError('source file SHA256 required')
    if not isinstance(assignments, list) or not assignments:
        raise ValueError('complete frozen split inventory required')
    split_map, group_splits = {}, {}
    for assignment in assignments:
        if not isinstance(assignment, dict):
            raise ValueError('invalid split assignment')
        if any(not text(assignment.get(k)) for k in ('sample_id', 'garment_group_id', 'split')):
            raise ValueError('split sample, garment group and membership required')
        sid, group = assignment['sample_id'], assignment['garment_group_id']
        if sid in split_map:
            raise ValueError('duplicate split sample')
        split_map[sid] = assignment
        group_splits.setdefault(group, set()).add(assignment['split'])
    examples = document.get('examples')
    if not isinstance(examples, list) or not examples:
        raise ValueError('observed examples required')
    seen_samples, seen_frames, group_labels = set(), set(), {}
    intervals = {label: [] for label in LABELS}
    provenance = []
    for example in examples:
        if not isinstance(example, dict):
            raise ValueError('invalid example')
        for key in ('sample_id', 'garment_group_id', 'frame_id', 'reviewer', 'review_evidence'):
            if not text(example.get(key)):
                raise ValueError(key + ' required')
        try:
            if date.fromisoformat(example['review_date']).isoformat() != example['review_date']:
                raise ValueError('invalid review date')
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('ISO review_date required') from exc
        if example.get('observed') is not True or example.get('reviewed') is not True:
            raise ValueError('explicit observed and reviewed evidence required')
        sid, group, frame = (example[k] for k in ('sample_id', 'garment_group_id', 'frame_id'))
        if sid in seen_samples or frame in seen_frames:
            raise ValueError('duplicate example sample or frame')
        seen_samples.add(sid)
        seen_frames.add(frame)
        assignment = split_map.get(sid)
        if (example.get('split') != 'development_calibration' or assignment is None
                or assignment['split'] != 'development_calibration'
                or assignment['garment_group_id'] != group
                or group_splits[group] != {'development_calibration'}):
            raise ValueError('calibration sample/group overlaps or lacks frozen calibration assignment')
        if not valid_source_path(example.get('original_path')) or not valid_hash(example.get('image_sha256')):
            raise ValueError('canonical relative original_path and lowercase image_sha256 required')
        if (assignment.get('original_path') != example['original_path']
                or assignment.get('image_sha256') != example['image_sha256']):
            raise ValueError('calibration assignment original path/hash mismatch')
        label = example.get('label')
        if label not in LABELS:
            raise ValueError('unsupported measured label')
        if group in group_labels and group_labels[group] != label:
            raise ValueError('same garment group has conflicting labels')
        group_labels[group] = label
        evidence = example.get('geometry')
        if not isinstance(evidence, dict):
            raise ValueError('explicit source-frame geometry required')
        if evidence.get('frame_id') != frame:
            raise ValueError('geometry frame identity mismatch')
        evidence_size = evidence.get('frame_size')
        if not isinstance(evidence_size, list) or any(type(v) is not int for v in evidence_size):
            raise ValueError('geometry frame_size must contain integers')
        for key in ('camera_config_id', 'reference_id', 'frame_size', 'projection', 'mode'):
            if evidence.get(key) != document[key]:
                raise ValueError('geometry ' + key + ' mismatch')
        if evidence.get('reference_kind') not in REFERENCE_KINDS[mode]:
            raise ValueError('unsupported reference evidence')
        quality = evidence.get('quality')
        if not isinstance(quality, dict) or any(quality.get(k) is not True for k in QUALITY):
            raise ValueError('all geometry quality observations must be explicitly true')
        coordinates = []
        for key in ('hem_y', 'waist_y', 'floor_y'):
            interval = evidence.get(key)
            if (not isinstance(interval, list) or len(interval) != 2
                    or any(type(v) not in (int, float) or not math.isfinite(v)
                           or not 0 <= v <= size[1] - 1 for v in interval)
                    or interval[0] > interval[1]):
                raise ValueError('invalid pixel interval: ' + key)
            coordinates.append(interval)
        hem, waist, floor = coordinates
        if waist[1] >= floor[0]:
            raise ValueError('waist/floor reference order ambiguous')
        ratios = [(h - w) / (f - w) for h, w, f in product(hem, waist, floor)]
        interval = [min(ratios), max(ratios)]
        if interval[0] < 0 or interval[1] > 1:
            raise ValueError('measured hem outside waist-to-floor coordinate')
        intervals[label].append(interval)
        provenance.append({'sample_id': sid, 'garment_group_id': group, 'frame_id': frame,
                           'original_path': example['original_path'], 'image_sha256': example['image_sha256'],
                           'label': label, 'ratio_interval': interval})
    if any(not intervals[label] for label in LABELS):
        raise ValueError('every one of the nine labels needs measured support')
    envelopes = {label: [min(v[0] for v in intervals[label]), max(v[1] for v in intervals[label])]
                 for label in LABELS}
    boundaries = []
    for left, right in zip(LABELS, LABELS[1:]):
        low, high = envelopes[left][1], envelopes[right][0]
        if low >= high:
            raise ValueError('adjacent class evidence overlaps or is unordered: ' + left + '/' + right)
        boundaries.append((low + high) / 2)
    profile = {'schema_version': 1, 'profile_id': document['profile_id'],
               'reference_id': document['reference_id'], 'camera_config_id': document['camera_config_id'],
               'frame_size': size, 'projection': document['projection'], 'coordinate': 'waist_to_floor',
               'labels': list(LABELS), 'supported_modes': [mode], 'boundaries': boundaries,
               'calibration_evidence': document['measurement_evidence'],
               'provenance': {'annotation_sha256': annotation_sha256, 'split_sha256': split_sha256,
                              'boundary_method': 'midpoint_between_separated_class_envelopes',
                              'class_envelopes': envelopes, 'examples': provenance,
                              'images': len(provenance), 'declared_garment_groups': len(group_labels)},
               'physical_calibration_verified': False,
               'status': 'candidate_requires_independent_physical_acceptance'}
    errors = validate_profile(profile)
    if errors:
        raise ValueError('generated profile invalid: ' + ', '.join(errors))
    return profile


def build_from_files(annotations, splits, output, *, source_root=None):
    raw_annotations, raw_splits = Path(annotations).read_bytes(), Path(splits).read_bytes()
    document, assignments = json.loads(raw_annotations), json.loads(raw_splits)
    profile = build_profile(document, assignments, annotation_sha256=digest(raw_annotations),
                            split_sha256=digest(raw_splits))
    root = Path(source_root).resolve(strict=True) if source_root is not None else Path(annotations).resolve().parent
    if not root.is_dir():
        raise ValueError('source root must be a directory')
    for example in profile['provenance']['examples']:
        original = (root / example['original_path']).resolve(strict=True)
        if not original.is_relative_to(root) or not original.is_file():
            raise ValueError('original image must be a file confined to source root')
        if digest(original.read_bytes()) != example['image_sha256']:
            raise ValueError('original image bytes/hash mismatch: ' + example['sample_id'])
    profile['provenance'].update(annotation_path=str(annotations), split_path=str(splits))
    profile['provenance'].update(source_root=str(root), original_bytes_verified=True)
    with Path(output).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(profile, indent=2, allow_nan=False) + '\n')
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--annotations', type=Path, required=True)
    parser.add_argument('--splits', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-root', type=Path, help='Confined original-file root; defaults to annotation directory')
    args = parser.parse_args()
    try:
        profile = build_from_files(args.annotations, args.splits, args.output, source_root=args.source_root)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'created': False, 'error': str(exc)}))
        return 1
    print(json.dumps({'created': True, 'profile_id': profile['profile_id'],
                      'physical_calibration_verified': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
