"""Bounded public primary-source metadata only; zero garment-photo requests."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPRedirectHandler, Request

HERE = Path(__file__).resolve().parent
BUDGET = 2 * 1024 * 1024
PER_RESPONSE = 512 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def main():
    report_path = HERE / 'acquisition.json'
    if report_path.exists():
        raise FileExistsError(report_path)
    opener = build_opener(NoRedirect())
    records, total = [], 0
    def fetch(url, filename):
        nonlocal total
        remaining = min(PER_RESPONSE, BUDGET-total)
        if remaining <= 0:
            raise ValueError('Metadata byte budget exhausted')
        record = {'url':url,'path':filename,'requested_at':datetime.now(timezone(timedelta(hours=8))).isoformat()}
        try:
            try:
                response = opener.open(Request(url,headers={'User-Agent':'SkirtFabricSense-source-research/1.0',
                    'Accept-Encoding':'identity','Accept':'application/json,text/plain,text/html'}),timeout=30)
            except HTTPError as error:
                response = error
            with response:
                record['http_status'] = response.status
                record['content_type'] = response.headers.get('Content-Type')
                encoding = response.headers.get('Content-Encoding','identity')
                if encoding not in ('','identity'):
                    raise ValueError('Unexpected content encoding')
                length = response.headers.get('Content-Length')
                if length is not None and int(length) > remaining:
                    raise ValueError('Response exceeds remaining metadata budget before read')
                body = response.read(remaining+1)
                total += len(body)
                if len(body) > remaining:
                    raise ValueError('Response exceeds bounded body limit')
                with (HERE/filename).open('xb') as stream:
                    stream.write(body)
                record.update(body_bytes=len(body),sha256=hashlib.sha256(body).hexdigest(),
                              outcome='saved' if response.status == 200 else 'saved_http_error_body')
                records.append(record)
                return body if response.status == 200 else None
        except Exception as error:
            record.update(outcome='failed',error=str(error))
            records.append(record)
            return None
    resolved = {}
    for nickname, repo in [('imaterialist2018','visipedia/imat_fashion_comp'),
                            ('imaterialist2020','visipedia/imat_comp'),
                            ('textilenet','hahashu/TextileNet')]:
        body = fetch('https://api.github.com/repos/'+repo,nickname+'-repo.json')
        if body is None:
            continue
        metadata = json.loads(body)
        branch = metadata['default_branch']
        body = fetch('https://api.github.com/repos/'+repo+'/commits/'+branch,nickname+'-commit.json')
        if body is None:
            continue
        revision = json.loads(body)['sha']
        resolved[nickname] = {'repository':repo,'revision':revision,'default_branch':branch}
        prefix = 'https://raw.githubusercontent.com/'+repo+'/'+revision+'/'
        fetch(prefix+'README.md',nickname+'-README.md')
        if nickname == 'imaterialist2018':
            fetch(prefix+'iMat_fashion_2018_label_map_228.csv','imaterialist2018-label-map.csv')
        else:
            fetch(prefix+'LICENSE',nickname+'-LICENSE.txt')
    fetch('https://arxiv.org/html/2301.06160v1','textilenet-paper.html')
    fetch('https://arxiv.org/html/1806.08317v2','fashiongen-paper.html')
    fetch('https://fashion-gen.com/','fashiongen-homepage.html')
    report = {'date_asia_manila':'2026-10-21','status':'bounded_primary_metadata_research',
              'total_body_bytes_read':total,'body_budget_bytes':BUDGET,
              'per_response_body_limit_bytes':PER_RESPONSE,'requests':records,
              'resolved_repository_revisions':resolved,'garment_photos_requested':0,
              'garment_photos_acquired':0,'training_admissions':0,'packages_installed':0,
              'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),
              'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'command':'python records/acquisitions/2026-10-21-fabric-source-research/acquire_metadata.py',
              'limits':'Metadata availability and publisher claims only; no verified image rights, garment identity or model quality.'}
    with report_path.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2); stream.write('\n')
    print(json.dumps({'responses':len(records),'body_bytes':total,
                      'saved':sum(r['outcome'].startswith('saved') for r in records),
                      'photos_acquired':0,'admissions':0}))


if __name__ == '__main__':
    main()
