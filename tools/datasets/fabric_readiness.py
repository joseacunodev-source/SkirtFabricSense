"""Offline audit of frozen fabric smoke inputs; never grants deployment approval."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = 'data/labels/fabric-pilot-v1.jsonl'
SPLITS = 'data/labels/fabric-pilot-v1-splits.json'
EXPECTED = {
    MANIFEST: '92a80e4f974b9730f4631da75fed99b3f628751c882bfe179b39322d20247523',
    SPLITS: 'e076033aa293ebad2058cec0ed2395292202f87bec9a78bfe2d350fa38e06c57',
    'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE':
        '383efc1e19406703d591d32fa73b64f44914550456ecff4c0764b451e871b641',
}
CLASSES = ('source_cotton_appearance', 'source_denim_appearance',
           'source_leather_appearance', 'source_chiffon_appearance')
PARTITIONS = ('development_train', 'development_validation')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows, assignments):
    """Validate provenance/split constraints and count source groups, not specimens."""
    errors = []
    ids, hashes, assignment_ids = set(), set(), set()
    lookup = {}
    for a in assignments:
        if a['sample_id'] in assignment_ids:
            errors.append('duplicate_split_assignment')
        assignment_ids.add(a['sample_id'])
        lookup[a['sample_id']] = a
    groups = defaultdict(set)
    counts = {label: {split: {'images': 0, 'source_groups': set()}
                     for split in PARTITIONS} for label in CLASSES}
    for r in rows:
        sid = r['sample_id']
        if sid in ids or r['sha256'] in hashes:
            errors.append('duplicate_sample_or_content')
        ids.add(sid)
        hashes.add(r['sha256'])
        if r['source_partition'] != 'train':
            errors.append('protected_source_partition')
        if r.get('admission_scope') != 'internal_pipeline_smoke_only' or r.get('training_admitted') is not True:
            errors.append('invalid_smoke_admission')
        a = lookup.get(sid)
        if not a or any(a[k] != r[k] for k in ('group_id', 'split')):
            errors.append('split_assignment_mismatch')
        if not r.get('group_id'):
            errors.append('missing_group')
        groups[r['group_id']].add(r['split'])
        if r['label'] not in CLASSES or r['split'] not in PARTITIONS:
            errors.append('unknown_label_or_split')
            continue
        cell = counts[r['label']][r['split']]
        cell['images'] += 1
        cell['source_groups'].add(r['group_id'])
    if ids != assignment_ids:
        errors.append('assignment_membership_mismatch')
    if any(len(splits) > 1 for splits in groups.values()):
        errors.append('group_split_overlap')
    for label in counts:
        for split in counts[label]:
            cell = counts[label][split]
            cell['source_groups'] = len(cell['source_groups'])
            if cell['images'] == 0:
                errors.append('missing_class_in_split')
    return {
        'integrity_errors': sorted(set(errors)),
        'images': len(rows), 'source_groups': len(groups),
        'verified_independent_specimens': None,
        'per_class': counts,
        'evidence_counts': {
            'independent_human_review': sum(r.get('independent_human_review') is True for r in rows),
            'composition_verified': sum(r.get('composition_verified') is True for r in rows),
            'explicit_worn_presentation': sum(r.get('presentation') == 'worn' for r in rows),
        },
        'validation_single_group_classes': [c for c in CLASSES
            if counts[c]['development_validation']['source_groups'] == 1],
        'live_approved': False,
        'approval_note': 'This audit cannot approve a model or replace independent evaluation.',
    }


def validate_presentation_review(review, rows):
    """Join a complete, provenance-bound visual supplement without changing labels."""
    errors = []
    for key, expected in (
        ('schema_version', 1), ('source_manifest', MANIFEST),
        ('source_manifest_sha256', EXPECTED[MANIFEST]),
        ('source_split_manifest', SPLITS),
        ('source_split_manifest_sha256', EXPECTED[SPLITS]),
    ):
        if review.get(key) != expected:
            errors.append('presentation_review_invalid:' + key)
    for key in ('reviewer', 'review_method'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            errors.append('presentation_review_missing:' + key)
    # A visual overlay cannot supply stronger admission/composition claims.
    for key in ('independent_human_review', 'composition_verified',
                'frozen_inputs_changed', 'new_training_admission', 'model_metrics_recomputed'):
        if review.get(key) is not False:
            errors.append('presentation_review_unsupported_claim:' + key)
    entries = review.get('review')
    if not isinstance(entries, list):
        return ['presentation_review_invalid_entries'], {}
    lookup = {r['sample_id']: r for r in rows}
    seen, presentations = set(), {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('sample_id'), str):
            errors.append('presentation_review_invalid_entry')
            continue
        sid = entry['sample_id']
        if sid in seen:
            errors.append('presentation_review_duplicate_sample')
        seen.add(sid)
        original = lookup.get(sid)
        if original is None:
            errors.append('presentation_review_unknown_sample')
            continue
        for key in ('sha256', 'original_path', 'group_id', 'split', 'source_partition'):
            if entry.get(key) != original[key]:
                errors.append('presentation_review_mismatch:' + key)
        if entry.get('source_label_preserved') != original['label']:
            errors.append('presentation_review_mismatch:source_label_preserved')
        if entry.get('original_opened') is not True:
            errors.append('presentation_review_original_not_opened')
        for key in ('composition_verified', 'independent_human_review'):
            if entry.get(key) is not False:
                errors.append('presentation_review_unsupported_claim:' + key)
        value = entry.get('presentation')
        if value not in ('worn', 'hanging', 'held', 'mannequin', 'unknown'):
            errors.append('presentation_review_invalid_presentation')
        else:
            presentations[sid] = value
    if seen != set(lookup) or len(entries) != len(rows) or len(rows) != 17:
        errors.append('presentation_review_incomplete_membership')
    return sorted(set(errors)), {} if errors else presentations


def audit(root=ROOT, presentation_review=None):
    evidence, errors = [], []
    for relative, expected in EXPECTED.items():
        path = root / relative
        actual = sha(path)
        evidence.append({'path': relative, 'sha256': actual, 'expected_sha256': expected})
        if actual != expected:
            errors.append('frozen_input_hash_mismatch:' + relative)
    rows = [json.loads(line) for line in (root / MANIFEST).read_text().splitlines() if line.strip()]
    splits = json.loads((root / SPLITS).read_text())
    report = summarize(rows, splits['assignments'])
    report['presentation_evidence_scope'] = 'frozen_manifest_only'
    if presentation_review is not None:
        path = Path(presentation_review)
        if not path.is_absolute():
            path = root / path
        try:
            review = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(review, dict):
                raise ValueError('Review must be an object')
            overlay_errors, presentations = validate_presentation_review(review, rows)
            errors.extend(overlay_errors)
            evidence_path = path.resolve().relative_to(root.resolve()).as_posix() if path.resolve().is_relative_to(root.resolve()) else str(path)
            evidence.append({'path': evidence_path, 'sha256': sha(path),
                             'role': 'supplemental_visual_presentation'})
            if not overlay_errors:
                report['presentation_evidence_scope'] = 'validated_supplemental_agent_review'
                report['evidence_counts']['explicit_worn_presentation'] = sum(
                    value == 'worn' for value in presentations.values())
                report['presentation_counts'] = {value: sum(v == value for v in presentations.values())
                    for value in ('worn', 'hanging', 'held', 'mannequin', 'unknown')}
        except (OSError, ValueError, TypeError) as exc:
            errors.append('presentation_review_unreadable:' + type(exc).__name__)
    terms = set()
    for r in rows:
        path = (root / r['original_path']).resolve()
        if not path.is_relative_to(root.resolve()):
            errors.append('image_path_escape:' + r['sample_id'])
        elif not path.is_file() or sha(path) != r['sha256'] or path.stat().st_size != r['size_bytes']:
            errors.append('image_integrity_failure:' + r['sample_id'])
        terms.add(r['terms_reference'])
    for relative in sorted(terms):
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            errors.append('missing_or_unsafe_terms:' + relative)
        else:
            evidence.append({'path': relative, 'sha256': sha(path), 'legal_revalidation': False})
    report['integrity_errors'] += errors
    report.update(schema_version=1, inputs=evidence, tool_sha256=sha(Path(__file__)),
                  integrity_passed=not report['integrity_errors'],
                  status='smoke_only_not_live_ready',
                  scope='Offline input audit; no new labels, images, training or camera evaluation',
                  blocking_evidence_gaps=[
                      'Operational appearance taxonomy and independent label confirmation remain unresolved.',
                      'Source item groups are not verified physical garments.',
                      ('Presentation annotations are absent from the frozen manifest; no supplement was validated.'
                       if report['presentation_evidence_scope'] == 'frozen_manifest_only' else
                       'Supplemental agent presentation annotations are available; worn-specific model performance remains unevaluated.'),
                      'Only five development validation groups; three classes have one each.',
                      'Manual ROI smoke does not evaluate automatic localization-to-fabric crops.',
                      'No target-camera garment evaluation, unknown-input calibration or Pi verification.',
                  ])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--presentation-review', type=Path,
                        help='Optional complete visual review bound to frozen pilot inputs')
    args = parser.parse_args()
    report = audit(presentation_review=args.presentation_review)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Preserve evidence: callers must choose a fresh output path.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'integrity_passed': report['integrity_passed'],
                      'images': report['images'], 'live_approved': False}))
    return 0 if report['integrity_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
