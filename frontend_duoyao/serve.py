"""Serve sigsig and forward its investigation and review API through the same origin.

Run: python3 serve.py
Operator configuration: BACKEND_URL, SIGNALDESK_JOB_ID, PORT.
The browser uses same-origin APIs for dataset uploads, analysis, and review.
"""
import json
import os
import re
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent / 'dist'
BACKEND = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')
JOB = os.getenv('SIGNALDESK_JOB_ID', 'demo')
CAN_UPLOAD = os.getenv('ENABLE_DATASET_UPLOADS', 'true').lower() == 'true'
MAX_UPLOAD = int(os.getenv('MAX_UPLOAD_MB', '150')) * 1024 * 1024
CAN_REVIEW = os.getenv('ENABLE_REVIEW_WRITES', 'true').lower() == 'true'


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def reply(self, status, payload, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/app-config.json':
            self.reply(200, json.dumps({'job_id': JOB, 'can_review': CAN_REVIEW, 'can_upload': CAN_UPLOAD, 'max_upload_bytes': MAX_UPLOAD}).encode())
            return
        if path.startswith('/api/v1/'):
            # The upstream is operator-controlled, never supplied by page content.
            try:
                request = Request(BACKEND + self.path, headers={'Accept': 'application/json'})
                with urlopen(request, timeout=55) as response:
                    self.reply(response.status, response.read(), response.headers.get('Content-Type', 'application/json'))
            except HTTPError as error:
                self.reply(error.code, error.read(), error.headers.get('Content-Type', 'application/json'))
            except (URLError, TimeoutError, OSError):
                self.reply(502, b'{"detail":"Investigation service unavailable"}')
            return
        super().do_GET()

    def do_POST(self):
        if urlsplit(self.path).path != '/api/v1/jobs':
            self.reply(404, b'{"detail":"Route not available."}')
            return
        if not CAN_UPLOAD:
            self.reply(403, b'{"detail":"Dataset uploads are disabled for this deployment."}')
            return
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            self.reply(403, b'{"detail":"Cross-origin uploads are not allowed."}')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            length = 0
        if not 0 < length <= MAX_UPLOAD + 65536:
            self.reply(413, json.dumps({'detail': f'Choose a non-empty file no larger than {MAX_UPLOAD // 1024 // 1024} MB.'}).encode())
            return
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data;'):
            self.reply(415, b'{"detail":"Upload a multipart log file."}')
            return
        # Spool large uploads to disk, rather than buffering the whole file in memory.
        try:
            with tempfile.SpooledTemporaryFile(max_size=2*1024*1024) as body:
                remaining = length
                while remaining:
                    chunk = self.rfile.read(min(1024*1024, remaining))
                    if not chunk:
                        self.reply(400, b'{"detail":"The upload was interrupted."}')
                        return
                    body.write(chunk)
                    remaining -= len(chunk)
                body.seek(0)
                request = Request(BACKEND + '/api/v1/jobs', data=body, method='POST', headers={'Content-Type':content_type, 'Content-Length':str(length), 'Accept':'application/json'})
                with urlopen(request, timeout=55) as response:
                    self.reply(response.status, response.read(), 'application/json')
        except HTTPError as error:
            self.reply(error.code, error.read(), 'application/json')
        except (URLError, TimeoutError, OSError):
            self.reply(502, b'{"detail":"Upload could not be confirmed. Check the dataset list before trying again."}')

    def do_PATCH(self):
        path = urlsplit(self.path).path
        expected = r'/api/v1/jobs/' + (r'[A-Za-z0-9-]{1,64}' if CAN_UPLOAD else re.escape(JOB)) + r'/incidents/[A-Za-z0-9_-]{1,128}/feedback'
        if not re.fullmatch(expected, path):
            self.reply(404, b'{"detail":"Route not available."}')
            return
        if not CAN_REVIEW:
            self.reply(403, b'{"detail":"Review editing is disabled for this deployment."}')
            return
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            self.reply(403, b'{"detail":"Cross-origin review updates are not allowed."}')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16384 or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise ValueError()
            value = json.loads(self.rfile.read(length))
            if not isinstance(value, dict) or value.get('status') not in ('new', 'investigating', 'resolved', 'dismissed') or value.get('disposition') not in ('unreviewed', 'suspicious', 'benign', 'confirmed') or not isinstance(value.get('note'), str) or len(value['note']) > 2000:
                raise ValueError()
            payload = json.dumps({k: value[k] for k in ('status', 'disposition', 'note')}).encode()
        except (ValueError, UnicodeDecodeError):
            self.reply(400, b'{"detail":"Invalid review. Choose a valid status and assessment, and limit notes to 2,000 characters."}')
            return
        try:
            request = Request(BACKEND + path, data=payload, method='PATCH', headers={'Accept':'application/json', 'Content-Type':'application/json'})
            with urlopen(request, timeout=15) as response:
                self.reply(response.status, response.read(), 'application/json')
        except HTTPError as error:
            self.reply(error.code, error.read(), 'application/json')
        except (URLError, TimeoutError, OSError):
            self.reply(502, b'{"detail":"Review could not be saved. Check the service and try again."}')

    def list_directory(self, path):
        self.send_error(404)
        return None


if __name__ == '__main__':
    url = urlsplit(BACKEND)
    if url.scheme not in ('http', 'https') or not url.netloc or url.query or url.fragment or url.username or url.password:
        raise SystemExit('BACKEND_URL must be a plain HTTP(S) service URL.')
    port = int(os.getenv('PORT', '5173'))
    print(f'sigsig: http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
