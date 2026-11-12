import copy
import json
import unittest
from tools.datasets.fabric_readiness import ROOT, MANIFEST, SPLITS, audit, summarize, validate_presentation_review

REVIEW = 'records/review/2026-10-16-fabric-presentation.json'


class FabricReadinessTests(unittest.TestCase):
    def setUp(self):
        self.rows = [json.loads(x) for x in (ROOT / MANIFEST).read_text().splitlines()]
        self.assignments = json.loads((ROOT / SPLITS).read_text())['assignments']
        self.review = json.loads((ROOT / REVIEW).read_text())

    def test_valid_supplement_reports_worn_without_promoting(self):
        before = copy.deepcopy(self.rows)
        report = audit(presentation_review=REVIEW)
        self.assertTrue(report['integrity_passed'])
        self.assertEqual(report['evidence_counts']['explicit_worn_presentation'], 17)
        self.assertEqual(report['evidence_counts']['composition_verified'], 0)
        self.assertEqual(report['evidence_counts']['independent_human_review'], 0)
        self.assertFalse(report['live_approved'])
        self.assertFalse(any('annotations are absent' in gap for gap in report['blocking_evidence_gaps']))
        self.assertEqual(self.rows, before)

    def test_overlay_hash_binding(self):
        for key in ('source_manifest_sha256', 'source_split_manifest_sha256'):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review[key] = '0' * 64
                errors, joined = validate_presentation_review(review, self.rows)
                self.assertTrue(errors)
                self.assertEqual(joined, {})

    def test_overlay_membership(self):
        for mutation in ('missing', 'duplicate', 'unknown'):
            with self.subTest(mutation=mutation):
                review = copy.deepcopy(self.review)
                if mutation == 'missing':
                    review['review'].pop()
                elif mutation == 'duplicate':
                    review['review'][-1] = copy.deepcopy(review['review'][0])
                else:
                    review['review'][0]['sample_id'] = 'not-in-pilot'
                errors, joined = validate_presentation_review(review, self.rows)
                self.assertTrue(errors)
                self.assertEqual(joined, {})

    def test_overlay_identity_matches_all_fields(self):
        for key in ('sha256', 'original_path', 'group_id', 'split', 'source_partition', 'source_label_preserved'):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review['review'][0][key] = 'changed'
                errors, joined = validate_presentation_review(review, self.rows)
                self.assertIn('presentation_review_mismatch:' + key, errors)
                self.assertEqual(joined, {})

    def test_overlay_requires_original_opened_and_attribution(self):
        self.review['review'][0]['original_opened'] = False
        self.assertIn('presentation_review_original_not_opened',
                      validate_presentation_review(self.review, self.rows)[0])
        for key in ('reviewer', 'review_method'):
            review = copy.deepcopy(self.review)
            review[key] = ' '
            self.assertIn('presentation_review_missing:' + key,
                          validate_presentation_review(review, self.rows)[0])

    def test_overlay_cannot_add_composition_or_admission_claims(self):
        for key in ('composition_verified', 'independent_human_review', 'new_training_admission'):
            review = copy.deepcopy(self.review)
            review[key] = True
            self.assertIn('presentation_review_unsupported_claim:' + key,
                          validate_presentation_review(review, self.rows)[0])
        self.review['review'][0]['composition_verified'] = True
        self.assertIn('presentation_review_unsupported_claim:composition_verified',
                      validate_presentation_review(self.review, self.rows)[0])

    def test_overlay_does_not_trust_summary(self):
        self.review['summary']['presentation_counts']['worn'] = 999
        errors, joined = validate_presentation_review(self.review, self.rows)
        self.assertEqual(errors, [])
        self.assertEqual(sum(v == 'worn' for v in joined.values()), 17)

    def test_missing_overlay_fails_closed(self):
        report = audit(presentation_review='records/review/does-not-exist.json')
        self.assertFalse(report['integrity_passed'])
        self.assertEqual(report['evidence_counts']['explicit_worn_presentation'], 0)

    def test_current_inputs_and_counts(self):
        report = audit()
        self.assertTrue(report['integrity_passed'])
        self.assertEqual((report['images'], report['source_groups']), (17, 17))
        self.assertEqual(report['per_class']['source_cotton_appearance']['development_train']['images'], 6)
        self.assertEqual(len(report['validation_single_group_classes']), 3)
        self.assertFalse(report['live_approved'])
        self.assertIsNone(report['verified_independent_specimens'])
        self.assertEqual(report['evidence_counts']['explicit_worn_presentation'], 0)

    def test_preserves_input_and_order_independent(self):
        original = copy.deepcopy(self.rows)
        self.assertEqual(summarize(self.rows, self.assignments),
                         summarize(self.rows[::-1], self.assignments[::-1]))
        self.assertEqual(self.rows, original)

    def test_protected_partition_rejected(self):
        self.rows[0]['source_partition'] = 'gallery'
        self.assertIn('protected_source_partition', summarize(self.rows, self.assignments)['integrity_errors'])

    def test_duplicate_assignment_rejected(self):
        self.assignments.append(copy.deepcopy(self.assignments[0]))
        self.assertIn('duplicate_split_assignment', summarize(self.rows, self.assignments)['integrity_errors'])

    def test_cross_split_group_rejected(self):
        self.rows[1]['group_id'] = self.rows[0]['group_id']
        self.assignments[1]['group_id'] = self.rows[0]['group_id']
        self.assertIn('group_split_overlap', summarize(self.rows, self.assignments)['integrity_errors'])

    def test_missing_class_rejected(self):
        rows = [r for r in self.rows if r['label'] != 'source_chiffon_appearance']
        assignments = [a for a in self.assignments if a['sample_id'] in {r['sample_id'] for r in rows}]
        self.assertIn('missing_class_in_split', summarize(rows, assignments)['integrity_errors'])

    def test_duplicate_content_rejected(self):
        self.rows[1]['sha256'] = self.rows[0]['sha256']
        self.assertIn('duplicate_sample_or_content', summarize(self.rows, self.assignments)['integrity_errors'])

    def test_wrong_admission_scope_rejected(self):
        self.rows[0]['admission_scope'] = 'production'
        self.assertIn('invalid_smoke_admission', summarize(self.rows, self.assignments)['integrity_errors'])


if __name__ == '__main__':
    unittest.main()
