"""Conservative mask-to-hem extraction with independently observed wearer references.

This module does not run a pose model or establish observation/calibration truth.
All coordinates refer to the same upright, rectified full source frame.
"""
import math


QUALITY = ('full_skirt_visible', 'single_garment', 'reference_associated',
           'projection_valid', 'hem_visible', 'waist_reference_valid',
           'floor_reference_valid')


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def extract_worn_geometry(*, frame_id, camera_config_id, frame_size,
                          mask_record, wearer_record):
    """Return {status, reason, evidence}; unavailable always has evidence=None.

    A binary mask may be lower-resolution but must represent the entire source
    frame without crop/letterbox. Cell extent and declared model error contribute
    to the hem interval; no default accuracy or visibility threshold is invented.
    """
    def fail(reason):
        return {'status': 'unavailable', 'reason': reason, 'evidence': None}

    if (not _text(frame_id) or not _text(camera_config_id)
            or not isinstance(frame_size, (list, tuple)) or len(frame_size) != 2
            or any(type(n) is not int or n < 2 for n in frame_size)):
        return fail('invalid_source_identity')
    width, height = frame_size
    for record in (mask_record, wearer_record):
        if not isinstance(record, dict):
            return fail('upstream_evidence_required')
        if (record.get('frame_id') != frame_id
                or record.get('camera_config_id') != camera_config_id
                or record.get('frame_size') != list(frame_size)):
            return fail('upstream_frame_mismatch')
        if not _text(record.get('evidence_id')):
            return fail('upstream_provenance_required')
    if wearer_record.get('mode') != 'worn':
        return fail('worn_presentation_required')
    if (not _text(wearer_record.get('reference_id'))
            or not _text(wearer_record.get('person_id'))
            or mask_record.get('person_id') != wearer_record['person_id']):
        return fail('wearer_association_required')
    quality = wearer_record.get('quality')
    if not isinstance(quality, dict) or any(quality.get(k) is not True for k in QUALITY):
        return fail('geometry_quality_not_established')
    landmarks = wearer_record.get('landmarks')
    if not isinstance(landmarks, dict):
        return fail('observed_references_required')
    points = {}
    for key in ('waist_left', 'waist_right', 'floor_left', 'floor_right'):
        point = landmarks.get(key)
        if (not isinstance(point, dict) or point.get('observed') is not True
                or not _text(point.get('evidence_id'))):
            return fail('observed_references_required')
        expected = 'visible_waist_reference' if key.startswith('waist') else 'visible_foot_floor_contact'
        if point.get('kind') != expected:
            return fail('unsupported_anatomical_reference')
        for axis, limit in (('x', width), ('y', height)):
            interval = point.get(axis)
            if (not isinstance(interval, (list, tuple)) or len(interval) != 2
                    or any(not _number(v) or not 0 <= v <= limit - 1 for v in interval)
                    or interval[0] > interval[1]):
                return fail('invalid_landmark_interval')
        points[key] = point
    waist = [min(points[k]['y'][0] for k in ('waist_left', 'waist_right')),
             max(points[k]['y'][1] for k in ('waist_left', 'waist_right'))]
    floor = [min(points[k]['y'][0] for k in ('floor_left', 'floor_right')),
             max(points[k]['y'][1] for k in ('floor_left', 'floor_right'))]
    if waist[1] >= floor[0]:
        return fail('ambiguous_reference_order')
    if mask_record.get('mapping') != 'full_source_extent':
        return fail('unsupported_mask_mapping')
    error = mask_record.get('boundary_error_px')
    if (not _number(error) or error < 0
            or not _text(mask_record.get('boundary_error_evidence'))):
        return fail('mask_uncertainty_required')
    grid = mask_record.get('mask')
    if not isinstance(grid, (list, tuple)) or len(grid) < 3:
        return fail('invalid_binary_mask')
    if not isinstance(grid[0], (list, tuple)) or len(grid[0]) < 3:
        return fail('invalid_binary_mask')
    rows, cols = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != cols
           or any(type(v) not in (int, bool) or v not in (0, 1) for v in row) for row in grid):
        return fail('invalid_binary_mask')
    pixels = {(x, y) for y, row in enumerate(grid) for x, v in enumerate(row) if v}
    if not pixels:
        return fail('empty_mask')
    if any(x in (0, cols - 1) or y in (0, rows - 1) for x, y in pixels):
        return fail('mask_touches_frame_edge')
    remaining = set(pixels)
    stack = [remaining.pop()]
    while stack:
        x, y = stack.pop()
        for neighbor in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if neighbor in remaining:
                remaining.remove(neighbor)
                stack.append(neighbor)
    if remaining:
        return fail('disconnected_mask')
    bottoms = {}
    for x, y in pixels:
        bottoms[x] = max(y, bottoms.get(x, y))
    # Preserve ALL column endpoints: narrow/asymmetric tips may be real hem.
    # This deliberately avoids a percentile that silently discards short hems.
    hem = [min(bottoms.values()) * height / rows - error,
           (max(bottoms.values()) + 1) * height / rows + error]
    if hem[0] < 0 or hem[1] > height - 1:
        return fail('hem_uncertainty_outside_frame')
    if hem[0] < waist[1] or hem[1] > floor[0]:
        return fail('hem_reference_order_uncertain')
    evidence = dict(frame_id=frame_id, camera_config_id=camera_config_id,
                    frame_size=list(frame_size), mode='worn',
                    reference_id=wearer_record['reference_id'],
                    reference_kind='observed_body_landmarks',
                    hem_y=hem, waist_y=waist, floor_y=floor,
                    quality={key: quality[key] for key in QUALITY},
                    extraction={'method': 'all_column_bottom_cells_v1',
                                'mask_evidence_id': mask_record['evidence_id'],
                                'wearer_evidence_id': wearer_record['evidence_id'],
                                'person_id': wearer_record['person_id'],
                                'boundary_error_evidence': mask_record['boundary_error_evidence'],
                                'mask_size': [cols, rows]})
    return {'status': 'extracted', 'reason': None, 'evidence': evidence}
