import copy
import unittest

from app.geometry import estimate_hemline
from app.hemline import LABELS
from app.worn_geometry import QUALITY, extract_worn_geometry


def fixture():
    identity = dict(frame_id='synthetic-frame', camera_config_id='synthetic-camera', frame_size=[100, 100])
    mask = [[int(2 <= x <= 7 and 2 <= y <= 5) for x in range(10)] for y in range(10)]
    landmarks = {}
    for name, x, y in [('waist_left', 30, 20), ('waist_right', 70, 20),
                       ('floor_left', 40, 90), ('floor_right', 60, 90)]:
        landmarks[name] = dict(x=[x, x], y=[y, y], observed=True,
            evidence_id='synthetic-only', kind='visible_waist_reference' if name.startswith('waist')
            else 'visible_foot_floor_contact')
    return dict(**identity,
        mask_record=dict(**identity, evidence_id='synthetic-mask', person_id='person', mask=mask,
                         mapping='full_source_extent', boundary_error_px=1,
                         boundary_error_evidence='synthetic-error-only'),
        wearer_record=dict(**identity, evidence_id='synthetic-wearer', person_id='person', mode='worn',
                           reference_id='reference', landmarks=landmarks,
                           quality={key: True for key in QUALITY}))


class WornGeometryTests(unittest.TestCase):
    def test_cell_extent_and_declared_error(self):
        args = fixture(); before = copy.deepcopy(args)
        result = extract_worn_geometry(**args)
        self.assertEqual(result['status'], 'extracted')
        self.assertEqual(result['evidence']['hem_y'], [49, 61])
        self.assertEqual(args, before)

    def test_asymmetric_hem_preserves_range(self):
        args = fixture(); args['mask_record']['mask'][6][7] = 1
        self.assertEqual(extract_worn_geometry(**args)['evidence']['hem_y'], [49, 71])

    def test_inward_taper_keeps_side_edge_uncertainty(self):
        args = fixture()
        for y in (4, 5):
            args['mask_record']['mask'][y][2] = 0
            args['mask_record']['mask'][y][7] = 0
        # Outer column endpoints can be side edges, not the true flat hem.
        # Conservatively retain them until a validated hem contour exists.
        self.assertEqual(extract_worn_geometry(**args)['evidence']['hem_y'], [29, 61])

    def test_identity_mismatch(self):
        for record in ('mask_record', 'wearer_record'):
            for key, value in [('frame_id', 'old'), ('camera_config_id', 'other'), ('frame_size', [50, 50])]:
                args = fixture(); args[record][key] = value
                self.assertEqual(extract_worn_geometry(**args)['reason'], 'upstream_frame_mismatch')

    def test_person_association(self):
        args = fixture(); args['mask_record']['person_id'] = 'other'
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'wearer_association_required')

    def test_each_quality_gate(self):
        for key in QUALITY:
            args = fixture(); args['wearer_record']['quality'][key] = False
            self.assertIsNone(extract_worn_geometry(**args)['evidence'])

    def test_hidden_anatomy_rejected(self):
        for key in fixture()['wearer_record']['landmarks']:
            args = fixture(); args['wearer_record']['landmarks'][key]['observed'] = False
            self.assertEqual(extract_worn_geometry(**args)['reason'], 'observed_references_required')

    def test_hip_is_not_waist(self):
        args = fixture(); args['wearer_record']['landmarks']['waist_left']['kind'] = 'pose_hip'
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'unsupported_anatomical_reference')

    def test_invalid_point(self):
        for value in ([float('nan'), 20], [21, 20], [True, 20], [0, 100]):
            args = fixture(); args['wearer_record']['landmarks']['waist_left']['y'] = value
            self.assertEqual(extract_worn_geometry(**args)['reason'], 'invalid_landmark_interval')

    def test_uncertainty_required(self):
        for value in (None, -1, float('inf'), True):
            args = fixture(); args['mask_record']['boundary_error_px'] = value
            self.assertEqual(extract_worn_geometry(**args)['reason'], 'mask_uncertainty_required')

    def test_mask_contract(self):
        for value in (None, [], [[0]], [[0, 0, 0], [0, .5, 0], [0, 0, 0]], [[0]*3, [0]*4, [0]*3]):
            args = fixture(); args['mask_record']['mask'] = value
            self.assertEqual(extract_worn_geometry(**args)['reason'], 'invalid_binary_mask')
        args = fixture(); args['mask_record']['mapping'] = 'cropped_roi'
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'unsupported_mask_mapping')

    def test_empty_disconnected_edge(self):
        args = fixture(); args['mask_record']['mask'] = [[0]*10 for _ in range(10)]
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'empty_mask')
        args = fixture(); args['mask_record']['mask'][8][8] = 1
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'disconnected_mask')
        args = fixture(); args['mask_record']['mask'][0][3] = 1
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'mask_touches_frame_edge')

    def test_held_is_not_worn(self):
        args = fixture(); args['wearer_record']['mode'] = 'held'
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'worn_presentation_required')

    def test_reference_order(self):
        args = fixture(); args['wearer_record']['landmarks']['floor_left']['y'] = [10, 15]
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'ambiguous_reference_order')
        args = fixture(); args['mask_record']['boundary_error_px'] = 35
        self.assertEqual(extract_worn_geometry(**args)['reason'], 'hem_reference_order_uncertain')

    def test_existing_adapter_consumes_evidence_but_needs_calibration(self):
        args = fixture(); evidence = extract_worn_geometry(**args)['evidence']
        identity = {k: args[k] for k in ('frame_id', 'camera_config_id', 'frame_size')}
        self.assertEqual(estimate_hemline(**identity, mode='worn', evidence=evidence)['status'], 'unavailable')
        profile = dict(schema_version=1, profile_id='synthetic-only', reference_id='reference',
            camera_config_id=args['camera_config_id'], frame_size=args['frame_size'],
            calibration_evidence='synthetic-only', coordinate='waist_to_floor', labels=list(LABELS),
            supported_modes=['worn'], boundaries=[.1,.2,.3,.4,.5,.6,.7,.8],
            projection='upright_rectified_vertical')
        result = estimate_hemline(**identity, mode='worn', evidence=evidence, profile=profile)
        self.assertEqual(result['status'], 'uncertain')


if __name__ == '__main__':
    unittest.main()
