"""Hemline rules for upstream geometry evidence; never infer a body from a crop."""
import math

LABELS=('micro','mini','above_knee','on_knee','below_knee','midi','tea','maxi','full')
MODES=('worn','hanging','mannequin','held')


def classify_hemline(*, mode, hem_interval=None, profile=None, reference_id=None):
    """Classify a hem interval on a calibrated waist(0)-floor(1) coordinate.

    Intervals and eight ordered class boundaries must come from the SAME
    reference/profile geometry. This function is not a pixel/body detector.
    There are deliberately no universal default boundaries.
    """
    def unavailable(reason):
        return {'status':'unavailable','label':None,'reason':reason,'mode':mode}
    if mode not in MODES:
        raise ValueError('Unsupported presentation mode')
    if profile is None or reference_id is None:
        return unavailable('body_reference_required')
    if (not isinstance(profile,dict) or not isinstance(profile.get('profile_id'),str)
            or not profile['profile_id'] or profile.get('reference_id')!=reference_id
            or not isinstance(reference_id,str) or not reference_id):
        raise ValueError('Geometry must identify its calibration and matching reference')
    if profile.get('coordinate')!='waist_to_floor' or profile.get('labels')!=list(LABELS):
        raise ValueError('Unsupported coordinate or label order')
    if mode not in profile.get('supported_modes',[]):
        return unavailable('reference_not_valid_for_presentation')
    boundaries=profile.get('boundaries')
    def finite(v):
        return type(v) in (int,float) and math.isfinite(v)
    if (not isinstance(boundaries,list) or len(boundaries)!=8
            or any(not finite(v) or not 0<v<1 for v in boundaries)
            or any(a>=b for a,b in zip(boundaries,boundaries[1:]))):
        raise ValueError('Eight calibrated, strictly ordered boundaries are required')
    if hem_interval is None:
        return unavailable('hem_geometry_required')
    if (not isinstance(hem_interval,(list,tuple)) or len(hem_interval)!=2
            or any(not finite(v) for v in hem_interval)):
        raise ValueError('Hem uncertainty interval must contain two finite coordinates')
    low,high=hem_interval
    if low>high:
        raise ValueError('Hem uncertainty interval is reversed')
    if low<0 or high>1:
        return unavailable('hem_outside_calibrated_range')
    if any(low<=b<=high for b in boundaries):
        return {'status':'uncertain','label':None,'reason':'category_boundary',
                'mode':mode,'profile_id':profile['profile_id'],'reference_id':reference_id}
    label=LABELS[sum(low>b for b in boundaries)]
    return {'status':'estimate','label':label,'mode':mode,
            'profile_id':profile['profile_id'],'reference_id':reference_id,
            'hem_interval':list(hem_interval),'score':None,
            'reason':'relative_to_named_reference_not_a_physical_length_measurement'}
