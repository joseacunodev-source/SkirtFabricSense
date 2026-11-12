"""Independent checks of frozen v3 negative admission and source binding."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

from tools.datasets.prepare_negative_extension import prepare
from tools.datasets.expand_negatives_v2 import permitted_license, source_key
from tools.training.train_presence import validate

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

class FrozenNegativeV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen_path = ROOT/'data/labels/negative-reviewed-v3.jsonl'
        cls.frozen = rows(cls.frozen_path)
        cls.old_path = ROOT/'data/labels/negative-reviewed-v2.jsonl'
        cls.old = rows(cls.old_path)
        cls.candidates = rows(ROOT/'data/manifests/negative-candidates-v3.jsonl')
        cls.report = json.loads((ROOT/'data/labels/negative-reviewed-v3.report.json').read_text())
        cls.reviews = []
        for name in ('2026-10-17-negative-v3-a.json', '2026-10-18-negative-v3-b.json', '2026-10-18-negative-v3-c.json'):
            value = json.loads((ROOT/'records/review'/name).read_text())
            cls.reviews.extend(value if isinstance(value, list) else value['reviews'])
        cls.audit = json.loads((ROOT/'records/validation/2026-10-17-expansion-v3-audit.json').read_text())
        cls.flags = json.loads((ROOT/'records/review/2026-10-18-negative-v3-root-grouping.json').read_text())['flags']
        cls.ids = {r['sample_id'] for r in cls.candidates}
        cls.by_id = {r['sample_id']:r for r in cls.frozen}
        cls.excluded = set()
        for pair in cls.audit['near_duplicate_candidates']:
            cls.excluded.update(cls.ids.intersection(pair['sample_ids']))
        for review in cls.reviews:
            if review.get('related_sample_ids'):
                cls.excluded.add(review['sample_id'])
                cls.excluded.update(cls.ids.intersection(review['related_sample_ids']))
        for flag in cls.flags:
            cls.excluded.update(cls.ids.intersection(flag['sample_ids']))

    def test_complete_original_review_binding(self):
        self.assertEqual(len(self.candidates), 180)
        self.assertEqual(len(self.reviews), 180)
        self.assertEqual(Counter(r['sample_id'] for r in self.reviews), Counter(self.ids))
        reviews = {r['sample_id']:r for r in self.reviews}
        for row in self.candidates:
            review = reviews[row['sample_id']]
            self.assertEqual(review['sha256'], row['sha256'])
            self.assertIs(review['original_inspected'], True)
            self.assertIsInstance(review['approve_no_skirt'], bool)
            self.assertTrue(review['observation'].strip())
            self.assertEqual(self.by_id[row['sample_id']]['label_evidence'], {**review, 'independent_human_review':False})
            self.assertEqual(sha(ROOT/row['original_path']), row['sha256'])

    def test_frozen_inputs_and_preparation_code_hashes(self):
        self.assertEqual(sha(self.frozen_path), self.report['manifest_sha256'])
        for evidence in self.report['inputs']:
            self.assertEqual(sha(ROOT/evidence['path']), evidence['sha256'])
        self.assertEqual(sha(ROOT/'tools/datasets/prepare_negative_v3.py'), self.report['source_sha256'])
        self.assertEqual(sha(ROOT/'tools/datasets/prepare_negative_extension.py'), self.report['reused_preparation_source_sha256'])

    def test_prior_rows_preserved_and_reproduction(self):
        self.assertEqual(len(self.old), 210)
        self.assertEqual(self.frozen[:len(self.old)], self.old)
        self.assertEqual(self.frozen_path.read_bytes().splitlines()[:len(self.old)], self.old_path.read_bytes().splitlines())
        self.assertEqual(prepare(self.candidates, self.reviews, self.old, self.excluded), self.frozen)
        self.assertEqual(set(self.report['new_excluded_for_known_group_or_near_match']), self.excluded)

    def test_counts_and_quarantine_are_consistent(self):
        admitted = [r for r in self.frozen if r['training_eligibility']['approved']]
        new_admitted = [r for r in admitted if r['sample_id'] in self.ids]
        counts = {'rows':len(self.frozen), 'new_candidates':len(self.candidates), 'admitted':len(admitted),
                  'new_admitted':len(new_admitted), 'by_split':dict(Counter(r['split'] for r in admitted))}
        self.assertEqual(counts, self.report['counts'])
        self.assertEqual(len({r['sample_id'] for r in self.frozen}), len(self.frozen))
        for row in self.frozen:
            if row['training_eligibility']['approved']:
                self.assertEqual(row['label'], 'no_skirt')
                self.assertTrue(permitted_license(row['source_license']))
            else:
                self.assertIsNone(row['split'])
                self.assertIsNone(row['label'])

    def test_near_and_related_candidates_quarantined(self):
        pairs = [p for p in self.audit['near_duplicate_candidates'] if self.ids.intersection(p['sample_ids'])]
        self.assertEqual(len(pairs), 17)
        self.assertEqual(len(self.flags[0]['sample_ids']), 7)
        for sid in self.excluded:
            self.assertFalse(self.by_id[sid]['training_eligibility']['approved'], sid)
            self.assertIsNone(self.by_id[sid]['split'])

    def test_protected_groups_and_exact_duplicates(self):
        admitted = [r for r in self.frozen if r['training_eligibility']['approved']]
        positives = rows(ROOT/'data/manifests/worn-pleating-development-v1.jsonl')
        validate([{**r, 'presence_target':1} for r in positives] + [{**r, 'presence_target':0} for r in admitted])
        holdout = rows(ROOT/'data/provenance/external_holdout_samples.jsonl')
        self.assertFalse({r['sha256'] for r in admitted}.intersection(r['sha256'] for r in holdout))
        self.assertFalse({source_key(r['source_url']) for r in admitted}.intersection(source_key(r['source_group_id']) for r in holdout))
        self.assertFalse({source_key(r['source_url']) for r in admitted}.intersection(source_key(r['source_url']) for r in positives))
        self.assertFalse({r['group_id'] for r in admitted}.intersection(r['group_id'] for r in positives))
        self.assertEqual(len({r['sha256'] for r in self.frozen}), len(self.frozen))
        self.assertFalse(self.audit['exact_duplicate_groups'])
        self.assertFalse(self.audit['pixel_duplicate_groups'])
        self.assertEqual(self.audit['counts']['integrity_errors'], 0)

if __name__ == '__main__':
    unittest.main()
