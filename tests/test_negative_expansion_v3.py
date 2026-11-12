import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

PATH = Path(__file__).resolve().parents[1] / 'tools/datasets/expand_negatives_v3.py'
spec = importlib.util.spec_from_file_location('negative_v3', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class NegativeExpansionV3Tests(unittest.TestCase):
    def image(self, fmt='PNG'):
        buf = io.BytesIO(); Image.new('RGB',(80,90),'red').save(buf,format=fmt)
        return buf.getvalue()

    def test_pixels_detect_reencoded_identical_image(self):
        first, second = self.image('PNG'), self.image('BMP')
        self.assertNotEqual(mod.source.digest(first),mod.source.digest(second))
        self.assertEqual(mod.pixel_hash(first),mod.pixel_hash(second))

    def data(self):
        data = {'categories':[{'id':i,'name':n} for i,n in [(6,'pants'),(7,'shorts'),(8,'skirt'),(10,'dress')]],
                'licenses':[{'id':0,'name':'Attribution License','url':mod.previous.LICENSE_URLS['Attribution License']}], 'images':[], 'annotations':[]}
        for i,cat in enumerate([6,7,10,8,6],1):
            data['images'].append({'id':i,'license':0,'width':100,'height':100,'original_url':f'https://live.staticflickr.com/2/{i}_abc123.jpg'})
            data['annotations'].append({'image_id':i,'category_id':cat,'bbox':[10,10,60,60]})
        return data

    def test_excludes_ids_canonical_urls_and_skirts(self):
        ids,urls={'2'},{'flickr-photo-5'}
        selected = mod.select(self.data(),ids,urls)
        self.assertEqual({r[0]['id'] for r in selected},{1,3})
        self.assertEqual(ids,{'2'}); self.assertEqual(urls,{'flickr-photo-5'})

    def test_invalid_license_and_clipped_target_rejected(self):
        data=self.data()
        data['licenses'][0]['url']='https://creativecommons.org/licenses/by-nd/2.0/'
        self.assertEqual(mod.select(data,set(),set()),[])
        data=self.data(); data['annotations'][0]['bbox']=[0,10,60,60]
        self.assertNotIn(1,{r[0]['id'] for r in mod.select(data,set(),set())})

    def test_verify_rejects_prior_pixels_and_admission(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); base=root/'v3'; base.mkdir()
            body=self.image(); (base/'image.png').write_bytes(body)
            row={'original_path':'v3/image.png','sha256':mod.source.digest(body),'decoded_pixel_sha256':mod.pixel_hash(body),'size_bytes':len(body),
                 'source_url':'https://live.staticflickr.com/2/999_abc123.jpg','source_item_id':'999','canonical_source_key':'flickr-photo-999',
                 'source_partition':'train2020','split':None,'training_eligibility':{'approved':False},'width':80,'height':90,
                 'source_license':{'name':'Attribution License','url':mod.previous.LICENSE_URLS['Attribution License']}}
            with patch.object(mod,'ROOT',root),patch.object(mod,'BASE',base):
                empty=(set(),set(),set(),set(),[])
                mod.verify([row],empty)
                with self.assertRaisesRegex(ValueError,'duplicate'):
                    mod.verify([row],(set(),set(),set(),{mod.pixel_hash(body)},[]))
                row['training_eligibility']['approved']=True
                with self.assertRaisesRegex(ValueError,'admitted'):
                    mod.verify([row],empty)

    def test_review_pages_have_at_most_twelve_original_links(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); record=root/'records'; record.mkdir()
            (root/'im.png').write_bytes(self.image())
            rows=[{'sample_id':str(i),'original_path':'im.png','sha256':'x','source_item_id':str(i),'sampling_bucket':'pants'} for i in range(13)]
            with patch.object(mod,'ROOT',root),patch.object(mod,'RECORD',record):
                mod.sheets(rows)
            import json
            pages=json.loads((record/'review-sheets.json').read_text())
            self.assertEqual([len(p['members']) for p in pages],[12,1])


if __name__=='__main__':
    unittest.main()
