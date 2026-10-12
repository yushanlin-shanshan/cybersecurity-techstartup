"""Serve SignalDesk and forward its read-only API through the same origin.

Run: python3 serve.py
Operator configuration: BACKEND_URL, SIGNALDESK_JOB_ID, PORT.
The browser never asks the user to choose a backend or import data.
"""
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent / 'dist'
BACKEND = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')
JOB = os.getenv('SIGNALDESK_JOB_ID', 'demo')


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
            self.reply(200, json.dumps({'job_id': JOB}).encode())
            return
        if path.startswith('/api/v1/'):
            # The upstream is operator-controlled, never supplied by page content.
            try:
                request = Request(BACKEND + self.path, headers={'Accept': 'application/json'})
                with urlopen(request, timeout=25) as response:
                    self.reply(response.status, response.read(), response.headers.get('Content-Type', 'application/json'))
            except HTTPError as error:
                self.reply(error.code, error.read(), error.headers.get('Content-Type', 'application/json'))
            except (URLError, TimeoutError, OSError):
                self.reply(502, b'{"detail":"Investigation service unavailable"}')
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None


if __name__ == '__main__':
    url = urlsplit(BACKEND)
    if url.scheme not in ('http', 'https') or not url.netloc or url.query or url.fragment or url.username or url.password:
        raise SystemExit('BACKEND_URL must be a plain HTTP(S) service URL.')
    port = int(os.getenv('PORT', '5173'))
    print(f'SignalDesk: http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
