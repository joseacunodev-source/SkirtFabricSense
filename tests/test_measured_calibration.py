"""Synthetic fixtures exercise mechanics only; no real profile is generated."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from app.geometry import validate_profile
from app.hemline import LABELS
from tools.build_measured_calibration import QUALITY, build_from_files, build_profile


def fixture():
    document = dict(schema_version=1, data_kind='observed_development_annotations',
                    profile_id='synthetic-test-only', camera_config_id='synthetic-camera',
                    reference_id='synthetic-reference', frame_size=[640, 1000], mode='worn',
                    projection='upright_rectified_vertical', measurement_evidence='synthetic-fixture-only',
                    examples=[])
    splits = []
    for i, label in enumerate(LABELS):
        sid = 'synthetic-' + label
        example = dict(sample_id=sid, garment_group_id=sid, frame_id=sid,
                       original_path=sid + '.bin', image_sha256=hashlib.sha256(sid.encode()).hexdigest(),
                       split='development_calibration', observed=True, reviewed=True,
                       reviewer='synthetic-test', review_evidence='synthetic arithmetic fixture',
                       review_date='2026-10-17', label=label,
                       geometry=dict(frame_id=sid, camera_config_id='synthetic-camera',
                                     reference_id='synthetic-reference', frame_size=[640, 1000],
                                     projection='upright_rectified_vertical', mode='worn',
                                     reference_kind='observed_body_landmarks',
                                     waist_y=[100, 100], floor_y=[900, 900],
                                     hem_y=[140 + i * 88, 144 + i * 88],
                                     quality={key: True for key in QUALITY}))
        document['examples'].append(example)
        splits.append(dict(sample_id=sid, garment_group_id=sid, split='development_calibration',
                           original_path=example['original_path'], image_sha256=example['image_sha256']))
    return document, splits


def build(document, splits):
    return build_profile(document, splits, annotation_sha256='a' * 64, split_sha256='b' * 64)


class MeasuredCalibrationTests(unittest.TestCase):
    def test_separated_evidence_yields_eight_gap_midpoints(self):
        document, splits = fixture()
        profile = build(document, splits)
        self.assertEqual(validate_profile(profile), [])
        self.assertEqual(len(profile['boundaries']), 8)
        self.assertAlmostEqual(profile['boundaries'][0], ((144 - 100) / 800 + (228 - 100) / 800) / 2)
        self.assertEqual(profile['supported_modes'], ['worn'])
        self.assertFalse(profile['physical_calibration_verified'])
        self.assertEqual(profile['provenance']['declared_garment_groups'], 9)

    def test_missing_class_rejected(self):
        document, splits = fixture()
        document['examples'].pop(3)
        with self.assertRaisesRegex(ValueError, 'nine labels'):
            build(document, splits)

    def test_overlap_and_touching_rejected(self):
        for interval in ([141, 145], [144, 146], [130, 135]):
            document, splits = fixture()
            document['examples'][1]['geometry']['hem_y'] = interval
            with self.assertRaisesRegex(ValueError, 'overlaps or is unordered'):
                build(document, splits)

    def test_frame_camera_reference_mode_projection_mismatch(self):
        for key, value in [('frame_id', 'stale'), ('camera_config_id', 'changed'),
                           ('reference_id', 'other'), ('mode', 'held'),
                           ('projection', 'tilted'), ('frame_size', [320, 240])]:
            document, splits = fixture()
            document['examples'][0]['geometry'][key] = value
            with self.assertRaises(ValueError):
                build(document, splits)

    def test_false_observation_review_or_quality_rejected(self):
        for field in ('observed', 'reviewed'):
            document, splits = fixture()
            document['examples'][0][field] = False
            with self.assertRaises(ValueError):
                build(document, splits)
        for field in QUALITY:
            document, splits = fixture()
            document['examples'][0]['geometry']['quality'][field] = False
            with self.assertRaises(ValueError):
                build(document, splits)

    def test_training_validation_and_test_group_overlap_rejected(self):
        for split in ('development_train', 'development_validation', 'test', 'external_holdout'):
            document, splits = fixture()
            splits.append(dict(sample_id='related', garment_group_id=splits[0]['garment_group_id'], split=split))
            with self.assertRaisesRegex(ValueError, 'overlaps'):
                build(document, splits)

    def test_undeclared_and_wrong_sample_assignment_rejected(self):
        for mutate in ('missing', 'group', 'split'):
            document, splits = fixture()
            if mutate == 'missing':
                splits.pop(0)
            elif mutate == 'group':
                splits[0]['garment_group_id'] = 'wrong'
            else:
                splits[0]['split'] = 'development_train'
            with self.assertRaises(ValueError):
                build(document, splits)

    def test_bad_intervals_and_reference_rejected(self):
        for interval in ([2, 1], [-1, 2], [1, 1000], [True, 140], [float('nan'), 140], [99, 101]):
            document, splits = fixture()
            document['examples'][0]['geometry']['hem_y'] = interval
            with self.assertRaises(ValueError):
                build(document, splits)
        document, splits = fixture()
        document['examples'][0]['geometry']['reference_kind'] = 'calibrated_standard_body'
        with self.assertRaises(ValueError):
            build(document, splits)

    def test_duplicates_and_conflicting_group_labels_rejected(self):
        document, splits = fixture()
        document['examples'].append(copy.deepcopy(document['examples'][0]))
        with self.assertRaises(ValueError):
            build(document, splits)
        document, splits = fixture()
        document['examples'][1]['garment_group_id'] = splits[0]['garment_group_id']
        splits[1]['garment_group_id'] = splits[0]['garment_group_id']
        with self.assertRaisesRegex(ValueError, 'conflicting labels'):
            build(document, splits)

    def test_files_record_exact_hashes_and_never_overwrite(self):
        document, splits = fixture()
        with tempfile.TemporaryDirectory() as directory:
            annotations, memberships, output = (Path(directory) / name for name in ('a.json', 's.json', 'p.json'))
            annotations.write_text(json.dumps(document), encoding='utf-8')
            memberships.write_text(json.dumps(splits), encoding='utf-8')
            for example in document['examples']:
                (Path(directory) / example['original_path']).write_bytes(example['sample_id'].encode())
            profile = build_from_files(annotations, memberships, output)
            self.assertEqual(profile['provenance']['annotation_sha256'], hashlib.sha256(annotations.read_bytes()).hexdigest())
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                build_from_files(annotations, memberships, output)
            self.assertEqual(output.read_bytes(), original)

    def test_original_identity_fields_required_and_match_assignment(self):
        for key, value in [('original_path', None), ('image_sha256', 'bad'),
                           ('image_sha256', 'A' * 64), ('original_path', 'different.bin')]:
            document, splits = fixture()
            document['examples'][0][key] = value
            with self.assertRaises(ValueError):
                build(document, splits)
        document, splits = fixture()
        splits[0]['image_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'path/hash mismatch'):
            build(document, splits)

    def test_changed_original_rejected_before_profile_creation(self):
        document, splits = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            annotations, memberships, output = (root / name for name in ('a.json', 's.json', 'p.json'))
            annotations.write_text(json.dumps(document), encoding='utf-8')
            memberships.write_text(json.dumps(splits), encoding='utf-8')
            for example in document['examples']:
                (root / example['original_path']).write_bytes(example['sample_id'].encode())
            (root / document['examples'][0]['original_path']).write_bytes(b'changed-original')
            with self.assertRaisesRegex(ValueError, 'bytes/hash mismatch'):
                build_from_files(annotations, memberships, output)
            self.assertFalse(output.exists())

    def test_traversal_absolute_and_windows_special_paths_rejected(self):
        for path in ('../outside.bin', 'sub/../outside.bin', '/outside.bin', 'C:/outside.bin',
                     'sub\\outside.bin', 'sub//outside.bin', 'image.bin:stream'):
            document, splits = fixture()
            document['examples'][0]['original_path'] = path
            splits[0]['original_path'] = path
            with self.assertRaisesRegex(ValueError, 'canonical relative'):
                build(document, splits)

    def test_explicit_source_root_and_hash_provenance(self):
        document, splits = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sources = root / 'sources'
            sources.mkdir()
            annotations, memberships, output = (root / name for name in ('a.json', 's.json', 'p.json'))
            annotations.write_text(json.dumps(document), encoding='utf-8')
            memberships.write_text(json.dumps(splits), encoding='utf-8')
            for example in document['examples']:
                (sources / example['original_path']).write_bytes(example['sample_id'].encode())
            profile = build_from_files(annotations, memberships, output, source_root=sources)
            self.assertEqual(profile['provenance']['source_root'], str(sources.resolve()))
            self.assertTrue(profile['provenance']['original_bytes_verified'])
            for observed, expected in zip(profile['provenance']['examples'], document['examples']):
                self.assertEqual(observed['image_sha256'], expected['image_sha256'])
                self.assertEqual(observed['original_path'], expected['original_path'])


if __name__ == '__main__':
    unittest.main()
