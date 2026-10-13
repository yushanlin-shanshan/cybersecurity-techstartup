"""Public demo website gateway; backend credentials stay inside the service."""
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from .app import app as backend

READ = re.compile(r'/api/v1/jobs(?:/[A-Za-z0-9-]{1,64}(?:/incidents(?:/[A-Za-z0-9_-]{1,128}(?:/evidence)?)?)?)?')
REVIEW = re.compile(r'/api/v1/jobs/[A-Za-z0-9-]{1,64}/incidents/[A-Za-z0-9_-]{1,128}/feedback')

class Website:
    def __init__(self, api, directory):
        self.api = api
        self.static = StaticFiles(directory=directory, html=True)

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.api(scope, receive, send)
        path, method = scope['path'], scope['method']
        uploads = os.getenv('ENABLE_DATASET_UPLOADS', 'false').lower() == 'true'
        reviews = os.getenv('ENABLE_REVIEW_WRITES', 'false').lower() == 'true'
        async def error(message, status):
            await JSONResponse({'detail': message}, status)(scope, receive, send)
        if path == '/app-config.json':
            if method != 'GET':
                return await error('Method not allowed.', 405)
            return await JSONResponse({'job_id': 'demo', 'can_upload': uploads, 'can_review': reviews,
                'max_upload_bytes': self.api.state.settings.max_upload_bytes},
                headers={'Cache-Control': 'no-store'})(scope, receive, send)
        if path == '/health':
            return await self.api(scope, receive, send)
        if path.startswith('/api/'):
            allowed = method == 'GET' and READ.fullmatch(path)
            allowed = allowed or (uploads and method == 'POST' and path == '/api/v1/jobs')
            allowed = allowed or (reviews and method == 'PATCH' and REVIEW.fullmatch(path))
            if not allowed:
                return await error('Route not available.', 404)
            if method != 'GET':
                headers = dict(scope['headers'])
                origin = headers.get(b'origin', b'').decode()
                host = headers.get(b'host', b'').decode()
                if origin and (urlsplit(origin).netloc != host or urlsplit(origin).scheme not in ('https', 'http')):
                    return await error('Cross-origin writes are not allowed.', 403)
            token = self.api.state.settings.api_token
            forwarded = dict(scope)
            forwarded['headers'] = [(k,v) for k,v in scope['headers'] if k.lower() != b'authorization']
            if token:
                forwarded['headers'].append((b'authorization', ('Bearer ' + token).encode()))
            return await self.api(forwarded, receive, send)
        if path.startswith(('/docs', '/redoc', '/openapi', '/api-static')):
            return await error('Not found.', 404)
        return await self.static(scope, receive, send)

app = Website(backend, Path(os.getenv('FRONTEND_DIR', '/app/frontend')))
