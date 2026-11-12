"""Replay contract tests use explicitly synthetic images/coordinates only."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from tests.test_worn_geometry import fixture as extractor_fixture
from tools.evaluate_worn_geometry import (CONVENTION, PROJECTION, evaluate,
                                         evaluate_from_files, interval_discrepancy)


def fixture(root):
    original = root/'source.png'
    Image.new('RGB',(100,100),'gray').save(original)
    image_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    inputs = extractor_fixture()
    example = dict(sample_id='synthetic-one',garment_group_id='synthetic-garment',
        split='development_validation',original_path='source.png',image_sha256=image_hash,
        frame_id=inputs['frame_id'],camera_config_id=inputs['camera_config_id'],
        frame_size=inputs['frame_size'],person_id='person',reference_id='reference',mode='worn',
        observed=True,reviewed=True,reviewer='synthetic-only',review_date='2026-10-20',
        annotation_method='manual_source_frame_intervals',
        review_evidence='Synthetic arithmetic test; not measured observations',
        truth=dict(reference_kind='observed_body_landmarks',waist_kind='visible_waist_reference',
            floor_kind='visible_foot_floor_contact',quality=copy.deepcopy(inputs['wearer_record']['quality']),
            waist_y=[20,20],floor_y=[90,90],hem_y=[49,61]))
    document = dict(schema_version=1,data_kind='synthetic_fixture',coordinate_convention=CONVENTION,
                    projection=PROJECTION,examples=[example])
    assignment = {k:example[k] for k in ('sample_id','garment_group_id','split','original_path','image_sha256')}
    prediction = {k:example[k] for k in ('sample_id','original_path','image_sha256','frame_id',
                                      'frame_size','camera_config_id','reference_id','person_id')}
    prediction.update(mask_record=inputs['mask_record'],wearer_record=inputs['wearer_record'])
    predictions = dict(schema_version=1,prediction_kind='saved_geometry_extractor_inputs',
        coordinate_convention=CONVENTION,projection=PROJECTION,annotation_sha256='a'*64,
        split_sha256='b'*64,producer=dict(name='synthetic fixture',evidence='No model involved',
                                        source_sha256='c'*64),predictions=[prediction])
    return document,[assignment],predictions


def run(root, document, splits, predictions, **kwargs):
    return evaluate(document,splits,predictions,source_root=root,
                    annotation_sha256='a'*64,split_sha256='b'*64,allow_synthetic=True,**kwargs)


class WornGeometryEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.document,self.splits,self.predictions = fixture(self.root)

    def replay(self):
        return run(self.root,self.document,self.splits,self.predictions)

    def test_synthetic_replay_preserves_zero_observed_claim(self):
        before = copy.deepcopy((self.document,self.splits,self.predictions))
        report = self.replay()
        self.assertEqual(report['status'],'synthetic_replay_only')
        self.assertEqual(report['counts']['observed_development_examples'],0)
        self.assertEqual(report['counts']['synthetic_examples'],1)
        self.assertEqual(report['image_coverage'],1)
        self.assertEqual(report['results'][0]['interval_discrepancies_px']['hem_y']['gap'],0)
        for flag in ('model_inference_performed','length_categories_evaluated','pi_verified','live_provider_enabled'):
            self.assertFalse(report[flag])
        self.assertEqual(before,(self.document,self.splits,self.predictions))

    def test_synthetic_requires_explicit_opt_in(self):
        with self.assertRaisesRegex(ValueError,'explicit opt-in'):
            evaluate(self.document,self.splits,self.predictions,source_root=self.root,
                     annotation_sha256='a'*64,split_sha256='b'*64)

    def test_changed_original_fails_integrity(self):
        (self.root/'source.png').write_bytes(b'not the source image')
        with self.assertRaisesRegex(ValueError,'SHA256'):
            self.replay()

    def test_dimensions_and_inventory_binding_checked(self):
        for field,value in [('frame_size',[101,100]),('image_sha256','d'*64),('garment_group_id','another')]:
            with self.subTest(field=field):
                old = self.document['examples'][0][field]
                self.document['examples'][0][field] = value
                with self.assertRaises(ValueError):
                    self.replay()
                self.document['examples'][0][field] = old

    def test_test_or_calibration_examples_cannot_be_replayed(self):
        for split in ('locked_test','development_calibration','development_train'):
            with self.subTest(split=split):
                self.document['examples'][0]['split'] = self.splits[0]['split'] = split
                with self.assertRaisesRegex(ValueError,'Only frozen development_validation'):
                    self.replay()

    def test_cross_split_garment_is_rejected(self):
        row = dict(self.splits[0],sample_id='different-frame',split='development_train')
        self.splits.append(row)
        with self.assertRaisesRegex(ValueError,'crosses splits'):
            self.replay()

    def test_renaming_group_does_not_hide_cross_split_original(self):
        self.splits.append(dict(self.splits[0],sample_id='renamed-original',
                                garment_group_id='renamed-group',split='development_train'))
        with self.assertRaisesRegex(ValueError,'file hash crosses splits'):
            self.replay()

    def test_boolean_schema_version_is_not_version_one(self):
        for document in (self.document,self.predictions):
            with self.subTest(document=document.get('data_kind','prediction')):
                document['schema_version'] = True
                with self.assertRaisesRegex(ValueError,'schema'):
                    self.replay()
                document['schema_version'] = 1

    def test_original_path_cannot_escape_source_root(self):
        for row in (self.splits[0],self.document['examples'][0]):
            row['original_path'] = '../outside.png'
        with self.assertRaisesRegex(ValueError,'original path/hash'):
            self.replay()

    def test_unreviewed_and_unsupported_truth_stay_explicit_exclusions(self):
        cases = [('observed',False,'truth_not_explicitly_observed_and_reviewed'),
                 ('mode','held','unsupported_presentation')]
        for field,value,reason in cases:
            with self.subTest(field=field):
                old = self.document['examples'][0][field]
                self.document['examples'][0][field] = value
                report = self.replay()
                self.assertEqual(report['annotation_exclusion_reasons'],{reason:1})
                self.assertIsNone(report['image_coverage'])
                self.assertEqual(report['counts']['extracted'],0)
                self.document['examples'][0][field] = old

    def test_truth_hip_and_ankle_are_not_reference_labels(self):
        truth = self.document['examples'][0]['truth']
        for name,value in [('waist_kind','pose_hip'),('floor_kind','pose_ankle')]:
            with self.subTest(name=name):
                old = truth[name]; truth[name] = value
                self.assertEqual(self.replay()['annotation_exclusion_reasons'],
                                 {'unsupported_truth_anatomical_reference':1})
                truth[name] = old

    def test_model_candidate_landmark_never_becomes_observed(self):
        point = self.predictions['predictions'][0]['wearer_record']['landmarks']['waist_left']
        point['observed'] = False
        report = self.replay()
        self.assertEqual(report['abstention_reasons'],{'observed_references_required':1})
        self.assertEqual(report['image_coverage'],0)
        self.assertIsNone(report['interval_discrepancy_means_px']['hem_y']['gap'])

    def test_missing_or_wrong_person_prediction_counts_as_abstention(self):
        saved = self.predictions['predictions']
        self.predictions['predictions'] = []
        self.assertEqual(self.replay()['abstention_reasons'],{'prediction_missing':1})
        self.predictions['predictions'] = saved
        saved[0]['wearer_record']['person_id'] = 'different-person'
        self.assertEqual(self.replay()['abstention_reasons'],{'prediction_wearer_or_reference_mismatch':1})

    def test_stale_frame_or_wrong_reference_is_not_scored(self):
        prediction = self.predictions['predictions'][0]
        for key,value in [('frame_id','old-frame'),('reference_id','other-reference')]:
            with self.subTest(key=key):
                old = prediction[key]; prediction[key] = value
                self.assertEqual(self.replay()['abstention_reasons'],{'prediction_source_identity_mismatch':1})
                prediction[key] = old

    def test_prediction_hash_binding_and_duplicate_membership_checked(self):
        self.predictions['annotation_sha256'] = 'd'*64
        with self.assertRaisesRegex(ValueError,'input hash binding'):
            self.replay()
        self.predictions['annotation_sha256'] = 'a'*64
        self.predictions['predictions'].append(copy.deepcopy(self.predictions['predictions'][0]))
        with self.assertRaisesRegex(ValueError,'Duplicate or unknown'):
            self.replay()

    def test_partial_annotations_do_not_hide_missing_inventory(self):
        self.splits.append(dict(self.splits[0],sample_id='not-annotated',garment_group_id='other-garment'))
        report = self.replay()
        self.assertEqual(report['unannotated_validation_inventory_members'],['not-annotated'])
        self.assertEqual(report['counts']['eligible_reviewed_originals'],1)

    def test_interval_statistics_have_explicit_overlap_and_discrepancy(self):
        result = interval_discrepancy([4,6],[8,10])
        self.assertEqual(result['gap'],2)
        self.assertEqual(result['midpoint_discrepancy'],4)
        self.assertEqual(result['maximum_endpoint_discrepancy'],4)
        self.assertFalse(result['contains_entire_truth_interval'])
        self.assertTrue(interval_discrepancy([2,12],[8,10])['contains_entire_truth_interval'])

    def test_file_wrapper_uses_real_hashes_and_refuses_overwrite(self):
        def write(name,value):
            path = self.root/name
            path.write_text(json.dumps(value),encoding='utf-8')
            return path
        annotations, splits = write('annotations.json',self.document), write('splits.json',self.splits)
        self.predictions.update(annotation_sha256=hashlib.sha256(annotations.read_bytes()).hexdigest(),
                                split_sha256=hashlib.sha256(splits.read_bytes()).hexdigest())
        predictions = write('predictions.json',self.predictions)
        output = self.root/'report.json'
        report = evaluate_from_files(annotations,splits,predictions,output,
                                     source_root=self.root,allow_synthetic=True)
        self.assertEqual(len(report['input_files']),3)
        self.assertEqual(json.loads(output.read_text())['counts']['observed_development_examples'],0)
        with self.assertRaises(FileExistsError):
            evaluate_from_files(annotations,splits,predictions,output,source_root=self.root,allow_synthetic=True)

    def test_nonfinite_extra_metadata_cannot_leave_partial_report(self):
        annotations, splits, predictions = [self.root/name for name in
                                            ('annotations.json','splits.json','predictions.json')]
        annotations.write_text(json.dumps(self.document),encoding='utf-8')
        splits.write_text(json.dumps(self.splits),encoding='utf-8')
        self.predictions.update(annotation_sha256=hashlib.sha256(annotations.read_bytes()).hexdigest(),
                                split_sha256=hashlib.sha256(splits.read_bytes()).hexdigest())
        self.predictions['producer']['invalid_extra'] = float('nan')
        predictions.write_text(json.dumps(self.predictions),encoding='utf-8')
        output = self.root/'must-not-exist.json'
        with self.assertRaises(ValueError):
            evaluate_from_files(annotations,splits,predictions,output,source_root=self.root,allow_synthetic=True)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
