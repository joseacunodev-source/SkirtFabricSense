"""Evidence-gated source-frame geometry adapter; no detector or default calibration."""
import math
from itertools import product

from app.hemline import LABELS, MODES, classify_hemline


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_profile(profile):
    """Return structural errors. A valid structure does not verify calibration accuracy."""
    if not isinstance(profile, dict):
        return ['profile_must_be_object']
    errors = []
    for key in ('profile_id', 'reference_id', 'camera_config_id', 'calibration_evidence'):
        if not _text(profile.get(key)):
            errors.append(key + '_required')
    if type(profile.get('schema_version')) is not int or profile['schema_version'] != 1:
        errors.append('unsupported_schema_version')
    if profile.get('coordinate') != 'waist_to_floor' or profile.get('labels') != list(LABELS):
        errors.append('unsupported_coordinates_or_labels')
    modes = profile.get('supported_modes')
    if not isinstance(modes, list) or not modes or any(m not in MODES for m in modes) or len(set(modes)) != len(modes):
        errors.append('invalid_supported_modes')
    size = profile.get('frame_size')
    if not isinstance(size, list) or len(size) != 2 or any(type(v) is not int or v <= 0 for v in size):
        errors.append('invalid_frame_size')
    bounds = profile.get('boundaries')
    if (not isinstance(bounds, list) or len(bounds) != 8
            or any(not _number(v) or not 0 < v < 1 for v in bounds)
            or any(a >= b for a, b in zip(bounds, bounds[1:]))):
        errors.append('invalid_calibrated_boundaries')
    if profile.get('projection') != 'upright_rectified_vertical':
        errors.append('unsupported_projection')
    return errors


def estimate_hemline(*, frame_id, camera_config_id, frame_size, mode, evidence=None, profile=None):
    """Convert same-frame y intervals into a conservative waist-to-floor interval.

    Caller supplies independently obtained geometry and current frame identity.
    Missing evidence abstains. This does not extract landmarks from an image.
    """
    def unavailable(reason):
        return {'status': 'unavailable', 'label': None, 'score': None,
                'mode': mode, 'reason': reason}
    if mode not in MODES:
        return unavailable('unsupported_presentation')
    if profile is None:
        return unavailable('calibrated_profile_required')
    if validate_profile(profile):
        return unavailable('invalid_calibration_profile')
    if mode not in profile['supported_modes']:
        return unavailable('reference_not_valid_for_presentation')
    if (not _text(camera_config_id) or camera_config_id != profile['camera_config_id']
            or not isinstance(frame_size, (tuple, list))
            or any(type(v) is not int for v in frame_size)
            or list(frame_size) != profile['frame_size']):
        return unavailable('camera_configuration_mismatch')
    if not isinstance(evidence, dict):
        return unavailable('geometry_evidence_required')
    if (not _text(frame_id) or evidence.get('frame_id') != frame_id
            or evidence.get('camera_config_id') != camera_config_id
            or evidence.get('frame_size') != list(frame_size)
            or evidence.get('mode') != mode):
        return unavailable('geometry_frame_or_mode_mismatch')
    if evidence.get('reference_id') != profile['reference_id']:
        return unavailable('geometry_reference_mismatch')
    allowed = {'worn': ('observed_body_landmarks',),
               'hanging': ('calibrated_standard_body',),
               'held': ('calibrated_standard_body',),
               'mannequin': ('observed_mannequin_landmarks', 'calibrated_standard_body')}
    if evidence.get('reference_kind') not in allowed[mode]:
        return unavailable('unsupported_reference_evidence')
    quality = evidence.get('quality')
    required = ('full_skirt_visible', 'single_garment', 'reference_associated',
                'projection_valid', 'hem_visible', 'waist_reference_valid', 'floor_reference_valid')
    if not isinstance(quality, dict) or any(quality.get(key) is not True for key in required):
        return unavailable('geometry_quality_not_established')
    intervals = []
    for key in ('hem_y', 'waist_y', 'floor_y'):
        interval = evidence.get(key)
        if (not isinstance(interval, (list, tuple)) or len(interval) != 2
                or any(not _number(v) or not 0 <= v <= frame_size[1] - 1 for v in interval)
                or interval[0] > interval[1]):
            return unavailable('invalid_pixel_geometry')
        intervals.append(interval)
    hem, waist, floor = intervals
    if waist[1] >= floor[0]:
        return unavailable('ambiguous_reference_order')
    # All interval endpoint combinations bound the linear-fractional ratio.
    ratios = [(h - w) / (f - w) for h, w, f in product(hem, waist, floor)]
    result = classify_hemline(mode=mode, hem_interval=[min(ratios), max(ratios)],
                              profile=profile, reference_id=profile['reference_id'])
    result.update(frame_id=frame_id, camera_config_id=camera_config_id,
                  reference_kind=evidence['reference_kind'], geometry_source='supplied_source_frame_evidence')
    return result
