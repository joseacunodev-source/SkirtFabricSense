import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from tools.training import train_category_presence as candidate


def fixture():
    rows, raw, annotations = [], [], []
    categories = [{'id':value,'name':name} for name,value in candidate.CATEGORY_IDS.items()]
    categories.append({'id':1,'name':'top, t-shirt, sweatshirt'})
    for split_index, split in enumerate(('development_train','development_validation')):
        for index, label in enumerate(candidate.CLASSES):
            image_id = split_index*10+index
            bucket = 'skirt' if index == 0 else label.removeprefix('no_skirt_')
            annotation = {'id':image_id+100,'image_id':image_id,
                          'category_id':candidate.CATEGORY_IDS[bucket],'bbox':[0,0,1,1]}
            annotations.append(annotation)
            row = {'sample_id':str(image_id),'presence_target':int(index==0),
                'source_id':'fashionpedia-train2020','source_item_id':str(image_id),
                'source_partition':'train2020','original_path':f'{image_id}.jpg',
                'sha256':str(image_id).zfill(64),'source_url':f'example:{image_id}',
                'group_id':f'g{image_id}','group_hash':f'h{image_id}','split':split,
                'source_license':{'id':1},'sampling_bucket':bucket,
                'source_labels':{'annotation_id':annotation['id']} if index == 0 else {
                    'skirt_annotation_count':0,'annotations':[{
                        'id':annotation['id'],'category_id':annotation['category_id'],
                        'category':bucket,'bbox':annotation['bbox']}]}}
            rows.append(row)
            if index:
                raw.append(copy.deepcopy(row))
    return rows, raw, annotations, categories


class CategoryAdmissionTests(unittest.TestCase):
    def test_hierarchy_targets_preserve_membership_hashes_groups_and_splits(self):
        rows, raw, annotations, categories = fixture()
        result = candidate.derive_targets(rows,raw,annotations,categories)
        self.assertEqual([r['category_target'] for r in result],[0,1,2,3,0,1,2,3])
        for before, after in zip(rows,result):
            for key in ('sample_id','sha256','original_path','group_id','group_hash','split','presence_target'):
                self.assertEqual(after[key],before[key])
            self.assertFalse(after['independent_category_truth_verified'])

    def test_skirt_present_scene_can_include_other_categories(self):
        rows, raw, annotations, categories = fixture()
        annotations.append({'id':999,'image_id':0,'category_id':10,'bbox':[0,0,1,1]})
        result = candidate.derive_targets(rows,raw,annotations,categories)
        self.assertEqual(result[0]['category_target'],0)

    def test_negative_mixed_pants_dress_scene_fails(self):
        rows, raw, annotations, categories = fixture()
        extra = {'id':999,'image_id':1,'category_id':10,'bbox':[0,0,1,1]}
        annotations.append(extra)
        for row in (rows[1],raw[0]):
            row['source_labels']['annotations'].append({'id':999,'category_id':10,'category':'dress','bbox':[0,0,1,1]})
        with self.assertRaisesRegex(ValueError,'Ambiguous mixed'):
            candidate.derive_targets(rows,raw,annotations,categories)

    def test_negative_with_actual_skirt_fails_even_when_review_says_absent(self):
        rows, raw, annotations, categories = fixture()
        annotations.append({'id':999,'image_id':1,'category_id':8,'bbox':[0,0,1,1]})
        for row in (rows[1],raw[0]):
            row['source_labels']['annotations'].append({'id':999,'category_id':8,'category':'skirt','bbox':[0,0,1,1]})
        with self.assertRaisesRegex(ValueError,'Ambiguous mixed'):
            candidate.derive_targets(rows,raw,annotations,categories)

    def test_missing_raw_or_duplicate_raw_fails(self):
        for mutation in ('missing','duplicate'):
            with self.subTest(mutation=mutation):
                rows, raw, annotations, categories = fixture()
                if mutation == 'missing':
                    raw.pop(0)
                else:
                    raw.append(copy.deepcopy(raw[0]))
                with self.assertRaises(ValueError):
                    candidate.derive_targets(rows,raw,annotations,categories)

    def test_raw_source_hash_group_or_category_mismatch_fails(self):
        for key in ('sha256','group_id','source_item_id','sampling_bucket'):
            with self.subTest(key=key):
                rows, raw, annotations, categories = fixture()
                rows[1][key] = 'changed'
                with self.assertRaises(ValueError):
                    candidate.derive_targets(rows,raw,annotations,categories)

    def test_copied_membership_cannot_hide_other_annotations(self):
        rows, raw, annotations, categories = fixture()
        annotations.append({'id':999,'image_id':1,'category_id':1,'bbox':[0,0,1,1]})
        with self.assertRaisesRegex(ValueError,'membership'):
            candidate.derive_targets(rows,raw,annotations,categories)

    def test_source_annotation_content_and_category_names_fail_closed(self):
        for key, value in (('category','dress'),('bbox',[1,1,2,2]),('category_id',10)):
            with self.subTest(key=key):
                rows, raw, annotations, categories = fixture()
                for row in (rows[1],raw[0]):
                    row['source_labels']['annotations'][0][key] = value
                with self.assertRaisesRegex(ValueError,'content'):
                    candidate.derive_targets(rows,raw,annotations,categories)

    def test_missing_positive_selected_skirt_annotation_fails(self):
        rows, raw, annotations, categories = fixture()
        rows[0]['source_labels']['annotation_id'] = 999
        with self.assertRaisesRegex(ValueError,'Positive'):
            candidate.derive_targets(rows,raw,annotations,categories)

    def test_duplicate_official_annotation_and_changed_vocabulary_fail(self):
        rows, raw, annotations, categories = fixture()
        annotations.append(copy.deepcopy(annotations[0]))
        with self.assertRaisesRegex(ValueError,'Duplicate official'):
            candidate.derive_targets(rows,raw,annotations,categories)
        rows, raw, annotations, categories = fixture()
        categories[0]['name'] = 'changed'
        with self.assertRaisesRegex(ValueError,'vocabulary'):
            candidate.derive_targets(rows,raw,annotations,categories)

    def test_missing_source_class_in_partition_fails(self):
        rows, raw, annotations, categories = fixture()
        rows.pop()
        with self.assertRaisesRegex(ValueError,'all four'):
            candidate.derive_targets(rows,raw,annotations,categories)

    def test_frozen_negative_manifest_changed_before_framework_import_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'negative.jsonl').write_text('{}\n')
            with self.assertRaisesRegex(ValueError,'Frozen negative-v3'):
                candidate.prepare_category_rows(root,'negative.jsonl')

    def test_binary_scene_weight_mass_stays_half_positive_half_negative(self):
        labels = [1]*265+[0]*155
        weights = candidate.binary.balanced_weights(labels)
        self.assertAlmostEqual(sum(weights[y] for y in labels if y==1),210)
        self.assertAlmostEqual(sum(weights[y] for y in labels if y==0),210)


@unittest.skipUnless(importlib.util.find_spec('tensorflow') and os.name != 'nt',
                     'Actual Keras/export checked in existing WSL training environment')
class CategoryScalarContractTests(unittest.TestCase):
    def test_actual_softmax_slice_scalar_export_without_training(self):
        import numpy as np
        import tensorflow as tf
        tf.config.experimental.enable_tensor_float_32_execution(False)
        tf.keras.utils.set_random_seed(42)
        provenance = json.loads((candidate.ROOT/'records/acquisitions/2026-10-04-mobilenetv2-weights.json').read_text())
        weights = Path(provenance['path'])
        self.assertEqual(candidate.sha(weights),provenance['sha256'])
        base, model, scalar = candidate.make_models(tf,weights)
        candidate.binary.configure_backbone(base,'head',tf.keras.layers.BatchNormalization)
        x = np.zeros((2,224,224,3),dtype=np.float32)
        x[1] = 127.5
        probabilities = model(x,training=False).numpy()
        expected = scalar(x,training=False).numpy()[:,0]
        np.testing.assert_allclose(expected,probabilities[:,0],rtol=0,atol=1e-7)
        self.assertEqual(scalar.output_shape,(None,1))
        self.assertEqual(model.output_shape,(None,4))
        with tempfile.TemporaryDirectory() as temp:
            scalar.save(Path(temp)/'scalar.keras')
            model.save(Path(temp)/'categories.keras')
            scalar_reopened = tf.keras.models.load_model(Path(temp)/'scalar.keras')
            categories_reopened = tf.keras.models.load_model(Path(temp)/'categories.keras')
            np.testing.assert_allclose(scalar_reopened(x,training=False).numpy()[:,0],expected,rtol=0,atol=1e-7)
            np.testing.assert_allclose(categories_reopened(x,training=False).numpy(),probabilities,rtol=0,atol=1e-7)
            report, values = candidate.binary.export_check(scalar,Path(temp)/'scalar-export',x,expected,tf,np)
            self.assertLessEqual(report['maximum_absolute_error'],.001)
            self.assertEqual(len(values),2)
        tf.keras.backend.clear_session()


if __name__ == '__main__':
    unittest.main()
