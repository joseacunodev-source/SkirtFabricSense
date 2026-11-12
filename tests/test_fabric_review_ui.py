"""Temporary synthetic queues only; no real reviewer events are submitted."""
import copy
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import unittest

from PIL import Image
from tools import serve_fabric_review as ui
from tools.datasets import fabric_evidence_review as review

ROOT = Path(__file__).resolve().parents[1]
NODE = Path('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')


def fixture(root):
    rows = []
    for i, split in enumerate(('development_train', 'development_validation')):
        path = root / review.SOURCE_DIR / f'ui-fixture-{i}.jpg'
        path.parent.mkdir(parents=True, exist_ok=True)
        # Decodable browser image, explicitly a plain synthetic test rectangle.
        Image.new('RGB', (160+i, 180), ('#547a80', '#95744c')[i]).save(path)
        rows.append(dict(sample_id=f'synthetic-ui-{i}', source_id='deepfashion-multimodal',
                         source_partition='train', split=split, group_id=f'fixture-group-{i}',
                         admission_scope='internal_pipeline_smoke_only', training_admitted=True,
                         composition_verified=False, independent_human_review=False,
                         physical_garment_verified=False, label='PRIVATE_SOURCE_LABEL',
                         original_path=path.relative_to(root).as_posix(), sha256=review.sha(path),
                         size_bytes=path.stat().st_size, width=160+i, height=180,
                         terms_reference=review.TERMS))
    terms = root / review.TERMS
    terms.parent.mkdir(parents=True, exist_ok=True)
    terms.write_text('Synthetic test terms only.', encoding='utf-8')
    manifest = root / review.MANIFEST
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(''.join(json.dumps(r)+'\n' for r in rows), encoding='utf-8')
    (root/review.SPLITS).write_text(json.dumps({'assignments': [
        {k:r[k] for k in ('sample_id','group_id','split')} for r in rows]}), encoding='utf-8')
    pins = {p:review.sha(root/p) for p in (review.MANIFEST, review.SPLITS, review.TERMS)}
    directory = root/'records/review/synthetic-ui'
    review.build(root, directory, pins)
    session = ui.ReviewSession(directory, root=root, expected=pins)
    row = session.queue['records'][0]
    payload = dict(review_id=row['review_id'], queue_sha256=session.queue_hash,
                   image_sha256=row['image']['sha256'],
                   reviewer={'display_name':'Synthetic test actor', 'actor_kind':'agent'},
                   original_viewed=True,
                   observations=dict(appearance_status='unknown', appearance_descriptors=[],
                       material_to_skirt_association='uncertain', presentation='unknown',
                       full_skirt_visibility='uncertain', texture_detail='insufficient',
                       notes='Synthetic fixture observation only, not a real garment review.'),
                   composition_evidence={'status':'not_observed', 'unverified_claim':None},
                   source_evidence_references=[])
    return session, payload


class FabricReviewUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session, self.payload = fixture(self.root)
        self.server = ui.ReviewServer(self.session, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        self.assertFalse(self.thread.is_alive())

    def call(self, method='GET', path='/api/queue', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        opts = {'Host':self.server.authority}
        if method == 'POST':
            opts.update({'Origin':self.server.origin, 'Content-Type':'application/json',
                         'X-Review-Token':self.session.token})
        opts.update(headers or {})
        conn.request(method, path, body, opts)
        response = conn.getresponse()
        data = response.read()
        result = response.status, response.headers, data
        conn.close()
        return result

    def post(self, payload=None, path='/api/observations', headers=None):
        return self.call('POST', path, json.dumps(payload or self.payload).encode(), headers)

    def count(self):
        return len((self.session.directory/review.EVENTS).read_text().splitlines())

    def test_blind_queue_and_headers(self):
        status, headers, body = self.call()
        self.assertEqual(status, 200)
        for secret in (b'PRIVATE_SOURCE_LABEL', b'fixture-group', b'development_train', b'original_path'):
            self.assertNotIn(secret, body)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Frame-Options'], 'DENY')
        self.assertIn('frame-ancestors', headers['Content-Security-Policy'])
        self.assertNotIn('Access-Control-Allow-Origin', headers)

    def test_only_allowlisted_images(self):
        rid = self.payload['review_id']
        status, headers, data = self.call(path='/api/image/'+rid)
        self.assertEqual(status, 200)
        self.assertEqual(headers.get_content_type(), 'image/jpeg')
        self.assertEqual(data, self.session.image(rid))
        for route in ('/bindings.private.json','/api/image/../bindings.private.json',
                      '/api/image/%2e%2e%2fprivate','/api/queue?expose=true','/tools/serve_fabric_review.py'):
            self.assertEqual(self.call(path=route)[0], 404)

    def test_wrong_host_origin_site_and_token_rejected(self):
        for headers in ({'Host':'example.org'}, {'Origin':'https://example.org'},
                        {'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.call(headers=headers)[0], 403)
        for headers in ({'Origin':''}, {'X-Review-Token':'wrong'}, {'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.post(headers=headers)[0], 403)
        self.assertEqual(self.count(), 0)

    def test_duplicate_token_header_rejected(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        body=json.dumps(self.payload).encode()
        conn.putrequest('POST','/api/observations',skip_host=True)
        for name,value in [('Host',self.server.authority),('Origin',self.server.origin),
            ('Content-Type','application/json'),('Content-Length',str(len(body))),
            ('X-Review-Token',self.session.token),('X-Review-Token',self.session.token)]:
            conn.putheader(name,value)
        conn.endheaders(body)
        response=conn.getresponse();self.assertEqual(response.status,403);response.read();conn.close()
        self.assertEqual(self.count(),0)

    def test_validate_download_does_not_append(self):
        status, _, body = self.post(path='/api/validate')
        self.assertEqual(status,200)
        self.assertEqual(json.loads(body)['submission'],self.payload)
        self.assertFalse(json.loads(body)['saved'])
        self.assertEqual(self.count(),0)

    def test_save_duplicate_and_correction_are_safe(self):
        first=self.post();self.assertEqual(first[0],201)
        self.assertFalse(json.loads(first[2])['duplicate'])
        second=self.post();self.assertEqual(second[0],200)
        self.assertTrue(json.loads(second[2])['duplicate'])
        self.assertEqual(self.count(),1)
        altered=copy.deepcopy(self.payload);altered['observations']['notes']+=' Correction.'
        self.assertEqual(self.post(altered)[0],201)
        report=review.verify(self.root,self.session.directory,self.session.expected)
        self.assertEqual(report['observations_submitted'],2)
        self.assertEqual(report['samples_with_submitted_observations'],1)
        self.assertFalse(report['training_approved'])
        self.assertFalse(report['independent_human_truth_established'])

    def test_simultaneous_same_submission_adds_one_event(self):
        results=[]
        jobs=[threading.Thread(target=lambda:results.append(self.session.append(self.payload))) for _ in range(2)]
        for thread in jobs:thread.start()
        for thread in jobs:thread.join(10)
        self.assertEqual(self.count(),1)
        self.assertEqual(sorted(r['duplicate'] for r in results),[False,True])

    def test_validation_rejects_truth_promotion_or_unknown_descriptors(self):
        for key,value in [('training_approved',True),('composition_verified',True)]:
            payload=copy.deepcopy(self.payload);payload[key]=value
            self.assertEqual(self.post(payload)[0],422)
        payload=copy.deepcopy(self.payload);payload['observations']['appearance_descriptors']=['inferred cotton']
        self.assertEqual(self.post(payload)[0],422)
        payload=copy.deepcopy(self.payload);payload['composition_evidence']={'status':'unverified_document_claim','unverified_claim':'Cotton'}
        self.assertEqual(self.post(payload)[0],422)
        self.assertEqual(self.count(),0)

    def test_wrong_image_hash_and_changed_original_fail_closed(self):
        payload=copy.deepcopy(self.payload);payload['image_sha256']='a'*64
        self.assertEqual(self.post(payload)[0],422)
        record=self.session.queue['records'][0]
        path=self.root/record['image']['path'];path.write_bytes(path.read_bytes()+b'changed')
        self.assertEqual(self.call(path='/api/image/'+record['review_id'])[0],409)
        self.assertEqual(self.post()[0],422)
        self.assertEqual(self.count(),0)

    def test_lock_retained_and_bad_requests_do_not_write(self):
        lock=self.session.directory/'.append.lock';lock.write_text('test held lock')
        self.assertEqual(self.post()[0],409)
        self.assertTrue(lock.exists());self.assertEqual(self.count(),0)
        lock.unlink()
        self.assertEqual(self.call('POST','/api/observations',b'not json')[0],422)
        self.assertEqual(self.post(headers={'Content-Type':'text/plain'})[0],400)
        self.assertEqual(self.call('POST','/api/observations',b'x'*(ui.MAX_BODY+1))[0],413)
        self.assertEqual(self.count(),0)

    @unittest.skipUnless(NODE.exists(),'Bundled browser runtime unavailable')
    def test_browser_download_save_navigation_and_unknown_roundtrip(self):
        cmd=[str(NODE),str(ROOT/'tests/fabric_review_browser.cjs'),self.server.origin,str(self.root)]
        result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['checks_passed'],14)
        self.assertEqual(self.count(),2)
        # Optional explicit artifact capture; ordinary test runs leave no files.
        if os.environ.get('FABRIC_UI_VALIDATION_OUTPUT'):
            output=Path(os.environ['FABRIC_UI_VALIDATION_OUTPUT'])
            output.mkdir(parents=True,exist_ok=True)
            for name in ('browser-synthetic-review.png','download.json'):
                shutil.copyfile(self.root/name,output/name)
            (output/'browser-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    unittest.main()
