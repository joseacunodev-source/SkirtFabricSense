"""Reproduce hash-bound source context for six manually inspected originals.

This supplemental review does not alter any frozen labels or split assignments.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'records/review/2026-10-17-source-label-followup.json'
OBSERVATIONS = {
    26955: ('Tan straight garment with cut-out decoration and fringed lower edge. Upper edge reaches frame boundary; complete waistband not established.', 'No category conflict established; unsuitable for wearer geometry.'),
    29141: ('Black isolated garment has broad top band and regularly repeated vertical pleats; no wearer or display support visible.', 'Source accordion skirt and pleat attributes agree with visible construction; presentation remains unknown.'),
    34099: ('Black-and-white isolated lower garment has diagonal overlapping front edge and a central lower notch/divided-looking outline. No wearer or separate display support visible.', 'Possible wrap skirt or skort/shorts construction cannot be resolved from this front view. Source explicitly labels wrap skirt; do not convert to negative or claim confirmed shorts.'),
    46766: ('Pink isolated fitted garment has continuous lower edge and visible top band; no wearer or display support visible.', 'No category conflict established; source hobble/peg skirt designation is compatible with the visible fitted outline.'),
    49867: ('Blue distressed isolated lower garment has waistband, fly, pockets and continuous lower edge; no visible wearer or display support.', 'No category conflict established. Denim-like appearance is not verified fiber composition.'),
    50322: ('Black top and lower garment are arranged separately with a white gap. Lower garment occupies the lower image and has an asymmetric-looking layered edge; no person visible.', 'Whole image contains another garment, but source skirt target is the lower ROI only. This is not a wearer or source-category conflict.'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    baseline_path = ROOT / 'data/labels/skirt-baseline-v1.jsonl'
    presentation_path = ROOT / 'records/review/2026-10-17-presentation-complete.jsonl'
    annotation_path = ROOT / 'data/external/fashionpedia_train/instances_attributes_train2020.json'
    baseline = {r['sample_id']: r for r in map(json.loads, baseline_path.read_text().splitlines())}
    presentations = {r['sample_id']: r for r in map(json.loads, presentation_path.read_text().splitlines())}
    annotation = json.loads(annotation_path.read_text())
    categories = {r['id']: r['name'] for r in annotation['categories']}
    attributes = {r['id']: r['name'] for r in annotation['attributes']}
    rows = []
    for image_id, (observation, assessment) in OBSERVATIONS.items():
        sample_id = f'fashionpedia-train2020-{image_id}'
        row = baseline[sample_id]
        p = presentations[sample_id]
        actual_hash = digest(ROOT / row['original_path'])
        if actual_hash != row['sha256'] or actual_hash != p['image_sha256']:
            raise ValueError(f'Original hash mismatch: {sample_id}')
        if p['presentation'] != 'unknown':
            raise ValueError(f'Presentation changed: {sample_id}')
        source_annotations = [a for a in annotation['annotations'] if a['image_id'] == image_id]
        target = next(a for a in source_annotations if a['id'] == row['source_labels']['annotation_id'])
        if target['category_id'] != 8 or target['segmentation'] != row['source_labels']['segmentation']:
            raise ValueError(f'Source target mismatch: {sample_id}')
        rows.append({
            'sample_id': sample_id, 'original_path': row['original_path'],
            'image_sha256': actual_hash, 'frame_size': [row['width'], row['height']],
            'historical_split': row['split'], 'historical_pleating_label': row['label'],
            'historical_group_id': row['group_id'], 'presentation': p['presentation'],
            'wearer_association_established': False, 'geometry_eligible': False,
            'method': 'full_original_visual_inspection_and_exact_source_annotation_join',
            'observation': observation, 'assessment': assessment,
            'source_target_annotation_id': target['id'],
            'source_target_category': categories[target['category_id']],
            'source_target_bbox': target['bbox'],
            'source_target_segmentation': target['segmentation'],
            'source_target_attributes': [attributes[v] for v in target.get('attribute_ids', [])],
            'whole_image_source_annotations': [
                {'id': a['id'], 'category_id': a['category_id'],
                 'category': categories[a['category_id']], 'bbox': a['bbox']}
                for a in source_annotations],
            'proposed_action': ('Quarantine from future new whole-image skirt-positive/classification releases until construction/category independently resolved; retain historical labels and excluded worn membership. Do not use as a negative.'
                                if image_id == 34099 else
                                'Keep excluded from worn subset; retain original source ROI and historical labels. No correction justified by this review.'),
            'independent_human_review': False, 'frozen_data_changed': False,
        })
    report = {
        'schema_version': 1, 'date_asia_manila': '2026-10-17',
        'reviewer': 'codex-source-label-followup', 'originals_viewed': 6,
        'independent_human_review': False, 'source_partition': 'train2020',
        'protected_source_images_opened': 0, 'frozen_labels_or_splits_changed': False,
        'inputs': [{'path': str(p.relative_to(ROOT)).replace('\\', '/'), 'sha256': digest(p)}
                   for p in (baseline_path, presentation_path, annotation_path)],
        'tool_sha256': digest(Path(__file__)), 'observations': rows,
        'closure': 'Agent source-context follow-up completed; independent category/label acceptance remains open. No confirmed shorts correction or future negative admission follows from this review.',
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(OUTPUT), 'sha256': digest(OUTPUT), 'originals_verified': len(rows), 'frozen_data_changed': False}))


if __name__ == '__main__':
    main()
