import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.review import ReviewStore
from tools.datasets.reconcile_human_reviews import audit, main


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        image = self.root / 'data/external/fashionpedia_train/images/a.jpg'
        image.parent.mkdir(parents=True)
        image.write_bytes(b'fixture-original')
        self.image = image
        self.sid = 'fashionpedia-train2020-1'
        self.hash = hashlib.sha256(image.read_bytes()).hexdigest()
        self.manifest = self.root / 'data/manifests/skirt_candidates.jsonl'
        self.manifest.parent.mkdir(parents=True)
        self.manifest.write_text(json.dumps(dict(sample_id=self.sid, source_partition='train2020',
            source_id='fashionpedia-train2020', sha256=self.hash,
            original_path=image.relative_to(self.root).as_posix(), width=10, height=10))+'\n')
        self.split = self.manifest.with_name('source-skirt-development-splits.json')
        self.split.write_text(json.dumps({'assignments':[dict(sample_id=self.sid,
            split='development_validation', group_hash='group1')]}))
        self.store = ReviewStore(self.root)

    def save(self, label='pleated', reviewer='human-a'):
        self.store.save(dict(sample_id=self.sid, image_sha256=self.hash, reviewer=reviewer,
            appearance_label=label, full_skirt_view=True, evidence='Visible folds in fixture'))

    def tamper(self, field, value, rehash=False):
        event = json.loads(self.store.events.read_text())
        event[field] = value
        if rehash:
            event.pop('event_sha256')
            event['event_sha256'] = hashlib.sha256(json.dumps(event,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.store.events.write_text(json.dumps(event)+'\n')

    def test_empty_is_not_review_completion(self):
        report = audit(self.root)
        self.assertEqual(report['status'], 'no_human_events')
        self.assertFalse(report['training_approved'])
        self.assertFalse(self.store.events.exists())

    def test_valid_review_preserves_validation_split_and_every_input(self):
        self.save()
        paths = [self.image,self.manifest,self.split,self.store.events]
        before = [p.read_bytes() for p in paths]
        report = audit(self.root)
        self.assertEqual(report['invalid_event_count'], 0)
        self.assertEqual(report['samples'][0]['split'], 'development_validation')
        self.assertFalse(report['samples'][0]['training_approved'])
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_conflicts_and_revisions_keep_history(self):
        self.save()
        self.save('non_pleated')
        self.save('pleated','human-b')
        report = audit(self.root)
        self.assertEqual(len(report['events']),3)
        self.assertTrue(report['samples'][0]['historical_disagreement'])
        self.assertEqual(len(report['samples'][0]['reviewers_with_revisions']['human-a']),2)

    def test_event_tampering(self):
        self.save()
        self.tamper('evidence','Changed')
        self.assertIn('event_hash_mismatch', audit(self.root)['events'][0]['errors'])

    def test_unknown_or_protected_sample(self):
        self.save()
        self.tamper('sample_id','fashionpedia-val2020-1',True)
        self.assertIn('unknown_or_protected_sample',audit(self.root)['events'][0]['errors'])

    def test_resplit_rejected_even_with_valid_event_hash(self):
        self.save()
        self.tamper('split','development_train',True)
        self.assertIn('split_mismatch',audit(self.root)['events'][0]['errors'])

    def test_stale_manifest_hash(self):
        self.save()
        self.manifest.write_text(self.manifest.read_text()+'\n')
        self.assertIn('source_manifest_sha256_mismatch',audit(self.root)['events'][0]['errors'])

    def test_original_tampering(self):
        self.save()
        self.image.write_bytes(b'changed')
        report=audit(self.root)
        self.assertEqual(report['status'],'integrity_errors')
        self.assertIn(self.sid, report['image_integrity_errors'])

    def test_duplicate_event_id(self):
        self.save()
        self.store.events.write_text(self.store.events.read_text()*2)
        self.assertIn('duplicate_event_id', audit(self.root)['events'][1]['errors'])

    def test_malformed_event_retained(self):
        self.store.events.parent.mkdir(parents=True)
        self.store.events.write_text('invalid json\n')
        report=audit(self.root)
        self.assertEqual(report['invalid_event_count'],1)
        self.assertEqual(report['events'][0]['raw'],'invalid json')

    def test_cli_refuses_to_overwrite_report(self):
        output = self.root / 'audit.json'
        output.write_text('prior immutable report')
        with patch('sys.argv', ['audit', '--root', str(self.root), '--output', str(output)]):
            with self.assertRaises(FileExistsError):
                main()
        self.assertEqual(output.read_text(), 'prior immutable report')

    def test_protected_assignment_rejected(self):
        split = json.loads(self.split.read_text())
        split['assignments'][0]['split'] = 'test'
        self.split.write_text(json.dumps(split))
        with self.assertRaisesRegex(ValueError, 'protected frozen split'):
            audit(self.root)


if __name__ == '__main__':
    unittest.main()
