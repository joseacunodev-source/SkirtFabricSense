import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from app.review import ReviewStore


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.image = self.root / 'data/external/fashionpedia_train/images/example.jpg'
        self.image.parent.mkdir(parents=True)
        self.image.write_bytes(b'original-image')
        self.sha = hashlib.sha256(self.image.read_bytes()).hexdigest()
        self.sid = 'fashionpedia-train2020-85'
        self.row = {'sample_id': self.sid, 'source_id': 'fashionpedia-train2020',
                    'source_partition': 'train2020', 'original_path': str(self.image.relative_to(self.root)),
                    'sha256': self.sha, 'width': 20, 'height': 40,
                    'source_labels': {'attributes': ['secret']}, 'project_labels': {'secret': 'pleated'}}
        self.manifest = self.root / 'data/manifests/skirt_candidates.jsonl'
        self.manifest.parent.mkdir(parents=True)
        self.write_manifest()
        self.splits = self.root / 'data/manifests/source-skirt-development-splits.json'
        self.splits.write_text(json.dumps({'assignments': [{'sample_id': self.sid,
            'split': 'development_validation', 'group_hash': 'frozen-group'}]}))
        self.payload = {'sample_id': self.sid, 'image_sha256': self.sha, 'reviewer': 'Reviewer A',
                        'appearance_label': 'unknown', 'full_skirt_view': False,
                        'evidence': 'Waistband obscured; cannot judge pleating.'}

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.row)+'\n', encoding='utf-8')

    def test_blind_queue(self):
        result = ReviewStore(self.root).queue()
        self.assertEqual(set(result['records'][0]), {'sample_id', 'image_sha256', 'width', 'height'})
        self.assertNotIn('secret', json.dumps(result))

    def test_append_preserves_sources_and_split(self):
        store = ReviewStore(self.root)
        before = self.manifest.read_bytes(), self.splits.read_bytes()
        first = store.save(self.payload)
        store.save({**self.payload, 'appearance_label': 'pleated'})
        events = [json.loads(x) for x in store.events.read_text().splitlines()]
        self.assertEqual(len(events), 2)
        self.assertNotEqual(events[0]['event_id'], events[1]['event_id'])
        self.assertEqual(events[0]['split'], 'development_validation')
        self.assertEqual(events[0]['group_hash'], 'frozen-group')
        self.assertFalse(first['training_approved'])
        self.assertEqual(events[0]['status'], 'pending_reconciliation')
        event = events[0].copy()
        expected = event.pop('event_sha256')
        self.assertEqual(expected, hashlib.sha256(json.dumps(event, sort_keys=True, separators=(',', ':')).encode()).hexdigest())
        self.assertEqual(before, (self.manifest.read_bytes(), self.splits.read_bytes()))
        self.assertEqual(store.queue()['samples_with_submitted_reviews'], 1)

    def test_reject_protected_and_path_escape(self):
        for key, value in [('source_partition', 'val2020'), ('original_path', '../../outside.jpg')]:
            original = self.row[key]
            self.row[key] = value
            self.write_manifest()
            with self.assertRaises(ValueError):
                ReviewStore(self.root)
            self.row[key] = original

    def test_unknown_sample_and_bad_hash(self):
        store = ReviewStore(self.root)
        for override in ({'sample_id': '../secrets'}, {'image_sha256': '0'*64}):
            with self.assertRaises(ValueError):
                store.save({**self.payload, **override})
        self.assertFalse(store.events.exists())

    def test_changed_original_and_manifest_rejected(self):
        store = ReviewStore(self.root)
        self.image.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            store.save(self.payload)
        self.image.write_bytes(b'original-image')
        self.manifest.write_text(self.manifest.read_text()+'\n')
        with self.assertRaises(ValueError):
            store.save(self.payload)

    def test_annotation_validation(self):
        store = ReviewStore(self.root)
        for override in ({'evidence': '  '}, {'reviewer': 'x'*101}, {'full_skirt_view': 'false'},
                         {'appearance_label': 'straight'}, {'reviewer': None}, {'extra': True}):
            with self.assertRaises(ValueError):
                store.save({**self.payload, **override})

    def test_protected_split_rejected(self):
        self.splits.write_text(json.dumps({'assignments': [{'sample_id': self.sid, 'split': 'test'}]}))
        with self.assertRaises(ValueError):
            ReviewStore(self.root)


if __name__ == '__main__':
    unittest.main()
