import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from tools.datasets.verify_fabric_v2 import verify

class FabricIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = []
        joins = []
        for i in (1, 2):
            filename = f'WOMEN-Skirts-id_0000000{i}-front.jpg'
            Image.new('RGB', (8, 10), (i * 40, 0, 0)).save(self.root / filename)
            body = (self.root / filename).read_bytes()
            row = dict(sample_id=str(i), original_path=filename, size_bytes=len(body),
                       sha256=hashlib.sha256(body).hexdigest(), width=8, height=10,
                       official_item_id=str(i), source_lower_fabric_label_id=1,
                       source_lower_fabric_label='cotton', training_admitted=False, project_split=None)
            self.rows.append(row)
            joins.append(dict(filename=filename, official_item_id=str(i), official_split='train', lower_fabric_source_code=1))
            self.write(f'data/manifests/fullview-fabric-candidates-v{i}.jsonl', json.dumps(row))
        self.write('records/acquisitions/2026-10-11-fabric-partition/skirt-partition-join.jsonl', '\n'.join(map(json.dumps, joins)))
        self.write('records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE', 'fixture')

    def write(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)

    def test_valid_candidates(self):
        result = verify(self.root)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['manifest_counts'], [1, 1])
        self.assertFalse(result['training_admitted'])

    def test_corrupt_image(self):
        self.write(self.rows[1]['original_path'], 'corrupt')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            verify(self.root)

    def test_unexpected_admission(self):
        self.rows[1]['training_admitted'] = True
        self.write('data/manifests/fullview-fabric-candidates-v2.jsonl', json.dumps(self.rows[1]))
        with self.assertRaisesRegex(ValueError, 'admitted'):
            verify(self.root)

    def test_duplicate_is_reported(self):
        self.write('data/manifests/fullview-fabric-candidates-v2.jsonl', json.dumps(self.rows[0]))
        result = verify(self.root)
        self.assertEqual(result['status'], 'duplicates_found')
        self.assertEqual({r['kind'] for r in result['duplicates']}, {'file', 'pixels', 'source_group'})

if __name__ == '__main__':
    unittest.main()
