"""Bounded official full-view fabric candidate intake; never admits training labels."""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
import zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.datasets.bounded_zip import BoundedZip

PUBLIC_URL = 'https://drive.google.com/uc?export=download&id=1U2PljA7NE57jcSSzPs21ZurdIPXdYZtN'
SIZE = 6822188210
LABELS = ROOT / 'records/acquisitions/2026-10-09-deepfashion-multimodal/labels-response.bin'
JOIN = ROOT / 'records/acquisitions/2026-10-11-fabric-partition/skirt-partition-join.jsonl'
NAMES = ['denim', 'cotton', 'leather', 'furry', 'knitted', 'chiffon', 'other', 'NA']

class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__(); self.action = None; self.fields = {}; self.inside = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form' and attrs.get('id') == 'download-form':
            self.action = attrs.get('action'); self.inside = True
        if self.inside and tag == 'input' and attrs.get('name'):
            self.fields[attrs['name']] = attrs.get('value', '')
    def handle_endtag(self, tag):
        if tag == 'form': self.inside = False

def resolve_download():
    with urlopen(PUBLIC_URL, timeout=40) as response:
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return PUBLIC_URL
        body = response.read(262145)
    if len(body) > 262144: raise ValueError('Confirmation page exceeds cap')
    form = DownloadForm(); form.feed(body.decode('utf-8'))
    parsed = urlparse(form.action or '')
    if parsed.scheme != 'https' or parsed.hostname not in ('drive.usercontent.google.com', 'drive.google.com'):
        raise ValueError('Public download unavailable or unexpected confirmation host')
    return form.action + '?' + urlencode(form.fields)

def candidates(per_class):
    if hashlib.sha256(LABELS.read_bytes()).hexdigest() != 'aa911ac1753f906df292a5a7a77aa32c029d3e5c09414772c64fff6a643d59b9':
        raise ValueError('Source labels changed')
    with zipfile.ZipFile(LABELS) as archive:
        rows = [line.split() for line in archive.read('labels/texture/fabric_ann.txt').decode().splitlines()]
    joins = {r['filename']:r for r in map(json.loads, JOIN.read_text().splitlines())}
    chosen = []; used = set(); counts = Counter()
    for row in sorted(rows):
        if len(row) != 4 or not row[0].startswith('WOMEN-Skirts-'): continue
        if joins[row[0]]['official_split'] != 'train': continue
        match = re.fullmatch(r'WOMEN-Skirts-(id_\d+)-[^/\\]+\.jpg', row[0])
        if not match: raise ValueError('Unexpected skirt source filename')
        label = int(row[2]); item = match[1]
        if not 0 <= label < len(NAMES): raise ValueError('Unknown source fabric label')
        if label == 7 or item in used or counts[label] >= per_class: continue
        chosen.append((row[0], item, label, joins[row[0]]['official_item_id'])); used.add(item); counts[label] += 1
    return chosen

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--per-class', type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.per_class <= 10: raise ValueError('Bound per-class selection to 1..10')
    out = ROOT / 'records/acquisitions/2026-10-11-fullview-fabric'
    out.mkdir(parents=True, exist_ok=False)
    destination = ROOT / 'data/external/deepfashion_multimodal_candidates'
    destination.mkdir(parents=True, exist_ok=True)
    manifest = ROOT / 'data/manifests/fullview-fabric-candidates-v1.jsonl'
    if manifest.exists(): raise FileExistsError(manifest)
    ledger = []; rows = []; error = None
    try:
        url = resolve_download()
        def fetch(start, end):
            if not 0 <= start <= end < SIZE or end-start+1 > 16*1024*1024:
                raise ValueError('Range outside bounds')
            request = Request(url, headers={'Range':f'bytes={start}-{end}'})
            with urlopen(request, timeout=45) as response:
                expected = f'bytes {start}-{end}/{SIZE}'
                if response.status != 206 or response.headers.get('Content-Range') != expected:
                    raise ValueError('Server did not honor exact archive range')
                body = response.read(end-start+2)
            if len(body) != end-start+1: raise ValueError('Truncated/oversized response')
            ledger.append({'start':start, 'end':end, 'bytes':len(body), 'sha256':hashlib.sha256(body).hexdigest()})
            return body
        archive = BoundedZip(fetch, SIZE)
        index = archive.index()
        names = {}
        for member in index:
            name = member.rsplit('/',1)[-1]
            if name in names: raise ValueError('Ambiguous archive basenames')
            names[name] = member
        for filename, item, label, official_item in candidates(args.per_class):
            body = archive.read(names[filename])
            with Image.open(io.BytesIO(body)) as image:
                if image.width*image.height > 20_000_000: raise ValueError('Oversized image')
                image.load(); width, height = image.size
            path = destination / filename
            with path.open('xb') as stream: stream.write(body)
            row = {'sample_id':'deepfashion-multimodal-'+filename[:-4], 'original_path':path.relative_to(ROOT).as_posix(),
                   'sha256':hashlib.sha256(body).hexdigest(), 'size_bytes':len(body), 'width':width, 'height':height,
                   'source_id':'deepfashion-multimodal', 'source_url':PUBLIC_URL, 'archive_member':names[filename],
                   'source_item_token':item, 'group_id':'deepfashion-inshop-WOMEN-Skirts-'+item,
                   'physical_garment_verified':False, 'source_partition':'train', 'official_item_id':official_item, 'project_split':None,
                   'source_lower_fabric_label_id':label, 'source_lower_fabric_label':NAMES[label],
                   'label_semantics':'Source visual appearance annotation; not verified fiber composition',
                   'full_skirt_visibility':'unreviewed', 'training_admitted':False,
                   'terms_reference':'records/acquisitions/2026-10-09-deepfashion-multimodal/LICENSE'}
            rows.append(row)
            with manifest.open('a', encoding='utf-8') as stream: stream.write(json.dumps(row)+'\n')
            print(json.dumps({'downloaded':len(rows), 'filename':filename}), flush=True)
    except Exception as exc:
        # Do not persist transient signed URLs from network exception messages.
        error = type(exc).__name__
        if isinstance(exc, (ValueError, KeyError)): error += ': '+str(exc)
    report = {'date_asia_manila':'2026-10-11', 'status':'completed' if error is None else 'partial_or_failed',
              'error':error, 'complete_images':len(rows), 'label_counts':dict(Counter(r['source_lower_fabric_label'] for r in rows)),
              'archive_size_bytes':SIZE, 'public_url':PUBLIC_URL, 'range_requests':ledger,
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'reader_sha256':hashlib.sha256((ROOT/'tools/datasets/bounded_zip.py').read_bytes()).hexdigest(),
              'training_admitted':False, 'source_partition_status':'Only exact original train matches selected; no query/gallery images acquired',
              'partition_join_sha256':hashlib.sha256(JOIN.read_bytes()).hexdigest(),
              'manifest':{'path':manifest.relative_to(ROOT).as_posix(), 'sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()} if manifest.exists() else None}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'range_requests'}))
    return 0 if error is None else 1

if __name__ == '__main__': raise SystemExit(main())
