"""Classify preserved failed HTTP bodies without rewriting historical evidence."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
INDEX = 'records/recoveries/raw-http-responses-v1.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Canonical relative evidence path required')
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or ':' in relative or str(p) != relative:
        raise ValueError('Unsafe evidence path')
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise ValueError('Missing or outside-root evidence: '+relative)
    return resolved


def checked(root, reference):
    if not isinstance(reference, dict):
        raise ValueError('Evidence reference required')
    p = local(root, reference.get('path'))
    if sha(p) != reference.get('sha256'):
        raise ValueError('Evidence hash differs: '+str(reference.get('path')))
    return p


def verified_raw_responses(root, index=INDEX):
    """Return only exact failed response paths tied to intact acquisition evidence.

    A missing index means no exceptions. An invalid index never authorizes any
    raw-body exceptions, and must be reported by the calling validator.
    """
    root = Path(root)
    if not (root/index).exists():
        return set()
    data = json.loads(local(root, index).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data.get('schema_version') != 1 or data.get('data_kind') != 'preserved_failed_http_responses':
        raise ValueError('Unsupported raw-response index')
    entries = data.get('entries')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Nonempty explicit response entries required')
    acq = json.loads(checked(root, data['acquisition']).read_text(encoding='utf-8'))
    log = json.loads(checked(root, data['request_log']).read_text(encoding='utf-8'))
    if not isinstance(acq, dict) or not isinstance(log, dict):
        raise ValueError('Acquisition and request-log objects required')
    if acq.get('images_acquired') != 0 or acq.get('training_admissions') != 0:
        raise ValueError('This recovery applies only to a zero-photo zero-admission attempt')
    if (not isinstance(acq.get('artifacts'), list) or any(not isinstance(r, dict) for r in acq['artifacts'])
            or not isinstance(log.get('requests'), list)):
        raise ValueError('Acquisition artifacts and request arrays required')
    artifacts = {r['path']: r for r in acq['artifacts']}
    requests = log['requests']
    approved, seen_indices = set(), set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError('Each raw-response entry must be an object')
        p = checked(root, item['body'])
        relative = item['body']['path']
        if not relative.startswith('records/acquisitions/') or p.suffix != '.json' or relative in approved:
            raise ValueError('Duplicate or unsupported raw response path')
        ix = item['request_index']
        if type(ix) is not int or not 0 <= ix < len(requests) or ix in seen_indices:
            raise ValueError('Invalid or repeated request index')
        req = requests[ix]
        if not isinstance(req, dict) or not isinstance(req.get('headers'), dict):
            raise ValueError('Request object and response headers required')
        status = req.get('status')
        media = req.get('headers', {}).get('Content-Type', '').split(';')[0].strip().lower()
        if (type(status) is not int or not 400 <= status <= 599 or req.get('outcome') != 'failed'
                or media != 'text/plain' or status != item.get('http_status') or media != item.get('media_type')):
            raise ValueError('Failed text/plain HTTP evidence required')
        artifact = artifacts.get(relative, {})
        if (req.get('body_path') != relative or req.get('sha256_consumed_body') != sha(p)
                or artifact.get('sha256') != sha(p) or artifact.get('size_bytes') != p.stat().st_size
                or req.get('consumed_body_bytes') != p.stat().st_size):
            raise ValueError('Response does not match original request/acquisition')
        copy = checked(root, item['typed_copy'])
        if not item['typed_copy']['path'].startswith('records/recoveries/') or copy.suffix != '.txt' or copy.read_bytes() != p.read_bytes():
            raise ValueError('Typed response copy differs')
        try:
            json.loads(p.read_text(encoding='utf-8-sig'))
        except json.JSONDecodeError:
            pass
        else:
            raise ValueError('Parsed JSON must not be exempted from JSON validation')
        approved.add(relative)
        seen_indices.add(ix)
    return approved


def recover(root, acquisition, request_log, index=INDEX):
    """Create a new explicit index and .txt copies; never edit source evidence."""
    root = Path(root)
    if (root/index).exists():
        raise FileExistsError('Recovery index already exists')
    acq_path, log_path = local(root, acquisition), local(root, request_log)
    acq = json.loads(acq_path.read_text(encoding='utf-8'))
    requests = json.loads(log_path.read_text(encoding='utf-8'))['requests']
    artifacts = {r['path']: r for r in acq['artifacts']}
    entries = []
    for ix, request in enumerate(requests):
        relative = request.get('body_path', '')
        if not relative.endswith('.json'):
            continue
        p = local(root, relative)
        try:
            json.loads(p.read_text(encoding='utf-8-sig'))
        except json.JSONDecodeError:
            if (request.get('status') != 429 or request.get('outcome') != 'failed'
                    or request.get('headers', {}).get('Content-Type') != 'text/plain'
                    or request.get('sha256_consumed_body') != sha(p)
                    or artifacts.get(relative, {}).get('sha256') != sha(p)):
                raise ValueError('Unexplained malformed JSON; cannot classify '+relative)
            dest = 'records/recoveries/http-bodies-20261111/'+p.stem+'.response.txt'
            (root/dest).parent.mkdir(parents=True, exist_ok=True)
            with (root/dest).open('xb') as f:
                f.write(p.read_bytes())
            entries.append({'body': {'path': relative, 'sha256': sha(p)}, 'request_index': ix,
                            'http_status': 429, 'media_type': 'text/plain',
                            'typed_copy': {'path': dest, 'sha256': sha(root/dest)}})
    data = {'schema_version': 1, 'data_kind': 'preserved_failed_http_responses',
            'acquisition': {'path': acquisition, 'sha256': sha(acq_path)},
            'request_log': {'path': request_log, 'sha256': sha(log_path)}, 'entries': entries,
            'meaning': 'Raw failed response evidence, not parsed metadata or acquired photos. Original bytes and historical hashes remain intact.'}
    (root/index).parent.mkdir(parents=True, exist_ok=True)
    with (root/index).open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2); f.write('\n')
    verified_raw_responses(root, index)
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--create', action='store_true')
    args = parser.parse_args()
    if args.create:
        result = recover(ROOT, 'records/acquisitions/2026-11-04-backgrounds/acquisition.json',
                         'records/acquisitions/2026-11-04-backgrounds/requests.json')
        print(json.dumps({'typed_failed_responses': len(result['entries']), 'photos_added': 0}))
    else:
        print(json.dumps({'verified_raw_responses': len(verified_raw_responses(ROOT))}))
