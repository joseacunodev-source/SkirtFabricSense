import io
import unittest
from tools.datasets.acquire_npcgi_pilot import (
    BoundedImages, ProbeError, select_candidates, verified_index, META, FILE_LIMIT,
)
import json

class Response(io.BytesIO):
    def __init__(self, body, status=206, content_range='bytes 32-34/100'):
        super().__init__(body)
        self.status = status
        self.headers = {'Content-Range':content_range,'Content-Length':str(len(body))}
        self.read_calls = 0
    def read(self,n=-1):
        self.read_calls += 1
        return super().read(n)

class Opener:
    def __init__(self,response): self.response=response
    def open(self,request,timeout): return self.response

class NpcgiPilotTests(unittest.TestCase):
    def test_exact_range(self):
        reader=BoundedImages('https://zenodo.org/example',100,Opener(Response(b'abc')))
        self.assertEqual(reader.fetch(32,3),b'abc')
        self.assertEqual(reader.bytes_read,3)

    def test_http200_and_wrong_range_no_read(self):
        for response in (Response(b'abc',200),Response(b'abc',206,'bytes 0-2/100')):
            reader=BoundedImages('https://zenodo.org/example',100,Opener(response))
            with self.assertRaisesRegex(ProbeError,'no body read'):reader.fetch(32,3)
            self.assertEqual(response.read_calls,0)

    def test_bounds_before_request(self):
        for start,length in ((0,1),(32,FILE_LIMIT+1),(99,2),(32,0)):
            reader=BoundedImages('https://zenodo.org/example',100)
            with self.assertRaises(ProbeError):reader.fetch(start,length)
            self.assertEqual(reader.requests,[])

    def test_request_and_byte_limits(self):
        reader=BoundedImages('https://zenodo.org/example',100)
        reader.requests=[{}]*5
        with self.assertRaises(ProbeError):reader.fetch(32,3)
        reader.requests=[]
        reader.bytes_read=32*1024*1024-3
        with self.assertRaises(ProbeError):reader.fetch(32,3)

    def test_incomplete_and_overlong(self):
        for body in (b'a',b'abcd'):
            response=Response(body)
            response.headers.pop('Content-Length')
            with self.assertRaisesRegex(ProbeError,'length mismatch'):
                BoundedImages('https://zenodo.org/example',100,Opener(response)).fetch(32,3)

    def test_real_verified_index_selection(self):
        _,parsed=verified_index()
        metadata=[json.loads(r) for r in META.read_text().splitlines()]
        selected=select_candidates(parsed,metadata)
        self.assertEqual([r['source_item_id'] for r in selected],['F1564','F0848','F1810','F0870','F1350'])
        self.assertTrue(all(r['crc32'] is not None for r in selected))

    def test_noncopy_and_duplicate_metadata_rejected(self):
        _,parsed=verified_index()
        metadata=[json.loads(r) for r in META.read_text().splitlines()]
        with self.assertRaises(ProbeError):select_candidates(parsed,metadata+metadata[:1])
        for folder in parsed['streams']['folders']:folder['codec_hex']='21'
        with self.assertRaisesRegex(ProbeError,'Copy stream'):select_candidates(parsed,metadata)

if __name__=='__main__': unittest.main()
