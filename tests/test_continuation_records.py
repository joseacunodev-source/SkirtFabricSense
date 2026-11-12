import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.validate_records import verify_reference_tree


class ContinuationReferenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root/'evidence.json').write_bytes(b'{"actual":true}')
        self.ref = {'path':'evidence.json',
                    'sha256':hashlib.sha256((self.root/'evidence.json').read_bytes()).hexdigest()}

    def test_nested_evidence_is_verified(self):
        errors = []
        count = verify_reference_tree(self.root,{'sources':[self.ref]},errors)
        self.assertEqual(count,1)
        self.assertEqual(errors,[])

    def test_changed_and_missing_evidence_is_reported(self):
        for path in ('evidence.json','missing.json'):
            with self.subTest(path=path):
                errors = []
                count = verify_reference_tree(self.root,{'path':path,'sha256':'0'*64},errors)
                self.assertEqual(count,0)
                self.assertEqual(len(errors),1)

    def test_outside_root_and_invalid_paths_are_rejected(self):
        for path in ('../outside',str(self.root.parent/'outside'),None,3):
            with self.subTest(path=path):
                errors = []
                self.assertEqual(verify_reference_tree(self.root,{'path':path,'sha256':'0'*64},errors),0)
                self.assertEqual(len(errors),1)


if __name__ == '__main__':
    unittest.main()
