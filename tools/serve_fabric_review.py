"""Loopback-only human interface for pending blind fabric appearance evidence.

Uses the existing immutable queue and append-only review contract. No camera,
model, data admission, composition verification or new dependency is involved.
"""
from __future__ import annotations

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.datasets import fabric_evidence_review as review

DEFAULT_DIRECTORY = ROOT / 'records/review/2026-10-23-fabric-evidence-review'
HTML = Path(__file__).resolve().parent / 'static/fabric_review.html'
MAX_BODY = 32768


class ReviewSession:
    """Only test code may override root/pins; CLI has no pin-override option."""
    def __init__(self, directory=DEFAULT_DIRECTORY, *, root=ROOT, expected=None):
        self.root = Path(root).resolve()
        self.directory = Path(directory).resolve()
        self.expected = expected
        review.verify(self.root, self.directory, self.expected)
        self.queue, _ = review._package(self.root, self.directory, self.expected)
        self.queue_hash = review.sha(self.directory / review.QUEUE)
        self.records = {r['review_id']: r for r in self.queue['records']}
        self.token = secrets.token_urlsafe(32)
        self._save_lock = threading.Lock()

    def current(self):
        result = review.verify(self.root, self.directory, self.expected)
        if result['queue_sha256'] != self.queue_hash:
            raise ValueError('Review queue changed; stop and investigate')
        events = (self.directory / review.EVENTS).read_text(encoding='utf-8').splitlines()
        reviewed = {json.loads(line)['payload']['review_id'] for line in events}
        return {
            'queue_sha256': self.queue_hash, 'session_token': self.token,
            'records': [{'review_id': r['review_id'],
                         'image': {'url': '/api/image/'+r['review_id'], 'sha256': r['image']['sha256'],
                                   'width': r['image']['width'], 'height': r['image']['height']},
                         'has_pending_observation': r['review_id'] in reviewed}
                        for r in self.queue['records']],
            'pending_items': result['pending_samples'],
            'submitted_events': result['observations_submitted'],
            'status': 'pending_reconciliation', 'training_approved': False,
            'independent_human_truth_established': False,
        }

    def image(self, rid):
        record = self.records.get(rid)
        if record is None:
            raise KeyError('Unknown review image')
        path = review._local(self.root, record['image']['path'], review.SOURCE_DIR)
        body = path.read_bytes()
        if len(body) != record['image']['size_bytes'] or hashlib.sha256(body).hexdigest() != record['image']['sha256']:
            raise ValueError('Original image changed; stop and investigate')
        return body

    def validate(self, payload):
        self.current()
        # Browser form is deliberately appearance-only. Documentary claims stay
        # in the separately recorded evidence workflow, not a visual guess.
        if payload.get('composition_evidence') != {'status': 'not_observed', 'unverified_claim': None}:
            raise ValueError('This form records appearance only, not composition claims')
        if payload.get('source_evidence_references') != []:
            raise ValueError('Use the documentary-evidence workflow for source references')
        review.validate_payload(self.root, payload, self.queue, self.queue_hash)

    def append(self, payload):
        # A repeated browser submission must not inflate the observation count.
        # Corrections with changed evidence remain separate append-only events.
        with self._save_lock:
            self.validate(payload)
            fingerprint = review.object_sha(payload)
            for line in (self.directory / review.EVENTS).read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                if review.object_sha(event['payload']) == fingerprint:
                    return {'event_id': event['event_id'], 'event_sha256': event['event_sha256'],
                            'status': 'pending_reconciliation', 'training_approved': False,
                            'duplicate': True}
            return dict(review.append(self.root, self.directory, payload, self.expected), duplicate=False)


class ReviewServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, session, port=8771):
        # No arbitrary bind address: this is a local review tool, not a service.
        super().__init__(('127.0.0.1', port), ReviewHandler)
        self.session = session
        self.origin = 'http://127.0.0.1:'+str(self.server_port)
        self.authority = '127.0.0.1:'+str(self.server_port)


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = 'LocalEvidenceReview/1'

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def log_message(self, fmt, *args):
        # Do not put observation text, reviewer identity or tokens in logs.
        pass

    def respond(self, code, body, mime='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Content-Security-Policy',
                         "default-src 'none'; img-src 'self'; connect-src 'self'; "
                         "style-src 'unsafe-inline'; script-src 'nonce-"+self.server.session.token+"'; "
                         "base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def allowed(self, post=False):
        hosts = self.headers.get_all('Host', [])
        if hosts != [self.server.authority]:
            self.respond(403, {'error': 'Use the displayed loopback address'})
            return False
        origins = self.headers.get_all('Origin', [])
        if origins and origins != [self.server.origin]:
            self.respond(403, {'error': 'Cross-origin request rejected'})
            return False
        if self.headers.get('Sec-Fetch-Site') not in (None, 'same-origin', 'none'):
            self.respond(403, {'error': 'Cross-site request rejected'})
            return False
        tokens = self.headers.get_all('X-Review-Token', [])
        if post and (origins != [self.server.origin] or len(tokens) != 1 or
                     not secrets.compare_digest(tokens[0], self.server.session.token)):
            self.respond(403, {'error': 'Reload the local reviewer page before submitting'})
            return False
        return True

    def route(self):
        url = urlsplit(self.path)
        if url.scheme or url.netloc or url.query or url.fragment:
            return None
        return url.path

    def do_GET(self):
        if not self.allowed():
            return
        route = self.route()
        try:
            if route == '/':
                body = HTML.read_text(encoding='utf-8').replace('__NONCE__', self.server.session.token).encode('utf-8')
                self.respond(200, body, 'text/html; charset=utf-8')
            elif route == '/api/queue':
                self.respond(200, self.server.session.current())
            elif route and route.startswith('/api/image/'):
                self.respond(200, self.server.session.image(route[len('/api/image/'):]), 'image/jpeg')
            else:
                self.respond(404, {'error': 'Not found'})
        except KeyError:
            self.respond(404, {'error': 'Not found'})
        except (ValueError, OSError, TypeError):
            self.respond(409, {'error': 'Evidence integrity check failed; stop and ask the project maintainer'})

    def do_POST(self):
        if not self.allowed(post=True):
            return
        route = self.route()
        if route not in {'/api/validate', '/api/observations'}:
            self.respond(404, {'error': 'Not found'})
            return
        lengths = self.headers.get_all('Content-Length', [])
        if (len(lengths) != 1 or not lengths[0].isdigit() or self.headers.get('Transfer-Encoding') or
                self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json'):
            self.close_connection = True
            self.respond(400, {'error': 'A bounded JSON request with one content length is required'})
            return
        length = int(lengths[0])
        if not 0 < length <= MAX_BODY:
            self.close_connection = True
            self.respond(413, {'error': 'Observation is too large or empty'})
            return
        try:
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('Incomplete request')
            payload = json.loads(body.decode('utf-8'))
            if not isinstance(payload, dict):
                raise ValueError('Expected an observation object')
            self.server.session.validate(payload)
            if route == '/api/validate':
                self.respond(200, {'submission': payload, 'saved': False})
            else:
                result = self.server.session.append(payload)
                self.respond(200 if result['duplicate'] else 201,
                             dict(result, saved=True, composition_verified=False))
        except FileExistsError:
            self.respond(409, {'error': 'Another writer or a preserved recovery lock exists; no automatic lock removal'})
        except (ValueError, KeyError, TypeError) as exc:
            self.respond(422, {'error': str(exc)})
        except (OSError, TimeoutError):
            self.close_connection = True
            self.respond(409, {'error': 'Save failed; inspect the event log before retrying'})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, default=DEFAULT_DIRECTORY)
    p.add_argument('--port', type=int, default=8771)
    args = p.parse_args()
    if not 0 <= args.port <= 65535:
        p.error('Port must be between 0 and 65535')
    session = ReviewSession(args.directory)
    with ReviewServer(session, args.port) as server:
        print('Blind fabric review: '+server.origin+'/', flush=True)
        print('Explicit saves append pending observations only. Stop with Ctrl+C.', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
