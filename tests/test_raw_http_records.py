import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools.raw_http_records import INDEX, recover, verified_raw_responses


class RawResponseTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.acq = 'records/acquisitions/attempt/acquisition.json'
        self.log = 'records/acquisitions/attempt/requests.json'
        self.raw = 'records/acquisitions/attempt/123_metadata.json'
        body = b'You are making too many requests to the API.\n'
        self.put(self.raw, body)
        sha = hashlib.sha256(body).hexdigest()
        self.putjson(self.acq, {'images_acquired': 0, 'training_admissions': 0,
            'artifacts': [{'path': self.raw, 'sha256': sha, 'size_bytes': len(body)}]})
        self.putjson(self.log, {'requests': [{'body_path': self.raw, 'status': 429, 'outcome': 'failed',
            'headers': {'Content-Type': 'text/plain'}, 'sha256_consumed_body': sha, 'consumed_body_bytes': len(body)}]})

    def put(self, p, body):
        file = self.root/p; file.parent.mkdir(parents=True, exist_ok=True); file.write_bytes(body)

    def putjson(self, p, value):
        self.put(p, (json.dumps(value)+'\n').encode())

    def freeze(self):
        return recover(self.root, self.acq, self.log)

    def editindex(self, mutate):
        data = json.loads((self.root/INDEX).read_text()); mutate(data); self.putjson(INDEX, data)

    def test_missing_index_does_not_ignore_anything(self):
        self.assertEqual(verified_raw_responses(self.root), set())

    def test_non_object_index_reports_value_error(self):
        self.putjson(INDEX, [])
        with self.assertRaises(ValueError): verified_raw_responses(self.root)

    def test_non_object_entry_reports_value_error(self):
        self.freeze(); self.editindex(lambda d: d.update(entries=[None]))
        with self.assertRaises(ValueError): verified_raw_responses(self.root)

    def test_original_and_historical_files_unchanged_and_typed_copy_verified(self):
        before = {p: (self.root/p).read_bytes() for p in [self.raw,self.acq,self.log]}
        result = self.freeze()
        self.assertEqual(verified_raw_responses(self.root), {self.raw})
        self.assertEqual((self.root/result['entries'][0]['typed_copy']['path']).read_bytes(), before[self.raw])
        for p, content in before.items(): self.assertEqual((self.root/p).read_bytes(), content)

    def test_changed_original_or_copy_rejected(self):
        result = self.freeze()
        for p in [self.raw, result['entries'][0]['typed_copy']['path']]:
            before = (self.root/p).read_bytes(); self.put(p, b'changed')
            with self.assertRaises(ValueError): verified_raw_responses(self.root)
            self.put(p, before)

    def test_changed_source_record_rejected(self):
        self.freeze(); self.putjson(self.acq, {'images_acquired': 1})
        with self.assertRaises(ValueError): verified_raw_responses(self.root)

    def test_duplicate_exception_or_request_rejected(self):
        self.freeze(); self.editindex(lambda d: d['entries'].append(d['entries'][0]))
        with self.assertRaises(ValueError): verified_raw_responses(self.root)

    def test_path_escape_and_unrelated_file_rejected(self):
        self.freeze()
        self.editindex(lambda d: d['entries'][0]['body'].update(path='../outside.json'))
        with self.assertRaises(ValueError): verified_raw_responses(self.root)

    def test_success_response_cannot_be_classified_as_failed(self):
        log = json.loads((self.root/self.log).read_text()); log['requests'][0]['status'] = 200
        self.putjson(self.log, log)
        with self.assertRaises(ValueError): self.freeze()

    def test_genuine_json_not_eligible_for_raw_exception(self):
        self.put(self.raw, b'{"error":"429"}')
        with self.assertRaises(ValueError): self.freeze()

    def test_json_error_response_type_cannot_bypass_parser(self):
        log = json.loads((self.root/self.log).read_text())
        log['requests'][0]['headers']['Content-Type'] = 'application/json'
        self.putjson(self.log, log)
        with self.assertRaises(ValueError): self.freeze()

    def test_index_request_fields_checked_even_if_index_edited(self):
        self.freeze(); self.editindex(lambda d: d['entries'][0].update(http_status=500))
        with self.assertRaises(ValueError): verified_raw_responses(self.root)

    def test_existing_recovery_never_overwritten(self):
        self.freeze(); before = (self.root/INDEX).read_bytes()
        with self.assertRaises(FileExistsError): self.freeze()
        self.assertEqual((self.root/INDEX).read_bytes(), before)

    def test_record_validator_only_exempts_verified_bodies_and_fails_closed(self):
        from tools.validate_records import validate
        self.freeze()
        self.put('README.md', b''); self.put('CHANGELOG.md', b'')
        self.putjson('data/external/acquisition_manifest.json', {'artifacts': []})
        self.putjson('data/provenance/seed_audit.json', {})
        def reference(p):
            return {'path': p, 'sha256': hashlib.sha256((self.root/p).read_bytes()).hexdigest()}
        self.putjson('data/registry.json', {
            'acquisition_manifest': reference('data/external/acquisition_manifest.json'),
            'verification_audit': reference('data/provenance/seed_audit.json')})
        self.put('records/unclassified.json', b'new malformed evidence')
        first = validate(self.root)
        self.assertEqual(first['raw_http_failure_bodies_verified'], 1)
        self.assertTrue(any('unclassified.json' in e for e in first['errors']))
        self.assertFalse(any('123_metadata.json' in e for e in first['errors']))
        self.put(self.raw, b'tampered')
        second = validate(self.root)
        self.assertEqual(second['raw_http_failure_bodies_verified'], 0)
        self.assertTrue(any('recovery invalid' in e for e in second['errors']))
        self.assertTrue(any('123_metadata.json' in e for e in second['errors']))


if __name__ == '__main__': unittest.main()
