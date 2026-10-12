from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict
from pathlib import Path
from typing import Annotated, Literal
import hmac
import hashlib
import json
import re
import tempfile
import time

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
from .config import Settings
from .store import Store
from .pipeline import process_job
from .explain import explain, selected_records
from .ml import RelatedIndex

class Options(BaseModel):
    scenario: str | None = Field(default=None, max_length=100, pattern=r'^[\w-]+$')
    gap_minutes: float = Field(default=15, gt=0, le=1440)
    max_span_minutes: float = Field(default=60, gt=0, le=1440)
    syslog_year: int = Field(default=2022, ge=1970, le=2100)
    limit: int = Field(default=0, ge=0, le=3_000_000)

class Batch(Options):
    filename: str = Field(default='custom.jsonl', max_length=150)
    records: list[dict] = Field(min_length=1, max_length=50000)

class Ask(BaseModel):
    question: str = Field(default='Explain this incident', min_length=1, max_length=1000)
    use_llm: bool = False

class Feedback(BaseModel):
    status: Literal['new', 'investigating', 'resolved', 'dismissed']
    disposition: Literal['unreviewed', 'suspicious', 'benign', 'confirmed']
    note: str = Field(default='', max_length=2000)

class RequestSizeLimit:
    """Bound upload bodies before multipart parsing, including chunked requests."""
    def __init__(self, app, maximum):
        self.app = app; self.maximum = maximum

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] != 'POST' or scope['path'] not in ('/api/v1/jobs', '/api/v1/jobs/batch'):
            return await self.app(scope, receive, send)
        maximum = self.maximum + 64 * 1024  # multipart framing allowance
        headers = dict(scope.get('headers', []))
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await JSONResponse({'detail': 'Invalid Content-Length'}, 400)(scope, receive, send)
        if length > maximum:
            return await JSONResponse({'detail': 'Request body exceeds configured upload limit'}, 413)(scope, receive, send)
        with tempfile.SpooledTemporaryFile(max_size=1024 * 1024) as body:
            size = 0
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                chunk = message.get('body', b''); size += len(chunk)
                if size > maximum:
                    return await JSONResponse({'detail': 'Request body exceeds configured upload limit'}, 413)(scope, receive, send)
                body.write(chunk)
                if not message.get('more_body', False):
                    break
            body.seek(0)
            async def replay():
                chunk = body.read(1024 * 1024)
                return {'type': 'http.request', 'body': chunk, 'more_body': body.tell() < size}
            await self.app(scope, replay, send)


def create_app(settings=None):
    settings = settings or Settings.from_env()
    store = Store(settings.data_dir)
    related_cache = OrderedDict()
    related_lock = __import__('threading').Lock()
    explanation_cache = OrderedDict()
    explanation_lock = __import__('threading').Lock()

    def detail_explanation(g, records):
        if not settings.llm_enabled:
            return explain(settings, g, records, 'Explain this incident')
        # Hash all inputs so changed evidence or review data invalidates the result.
        key = hashlib.sha256(json.dumps([settings.openai_model, g, records], sort_keys=True).encode()).hexdigest()
        # Serialize first generations to avoid duplicate provider calls on refresh.
        with explanation_lock:
            cached = explanation_cache.get(key)
            if cached and time.monotonic() - cached[0] < 600:
                explanation_cache.move_to_end(key)
                return cached[1]
            result = explain(settings, g, records, 'Explain this incident', use_llm=True)
            if result['mode'] == 'llm':
                explanation_cache[key] = (time.monotonic(), result)
                explanation_cache.move_to_end(key)
                if len(explanation_cache) > 128:
                    explanation_cache.popitem(last=False)
            else:
                explanation_cache.pop(key, None)
            return result

    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        app.state.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='alert-worker')
        yield
        app.state.executor.shutdown(wait=True)

    app = FastAPI(title='Blue Team Incident API', version='1.0.0', lifespan=lifespan,
                  description='Ingest AIT-ADS or canonical JSONL alerts, correlate incidents, rank with local ML, and explain using source evidence.')
    app.state.store = store
    app.state.settings = settings
    app.add_middleware(RequestSizeLimit, maximum=settings.max_upload_bytes)

    @app.middleware('http')
    async def authenticate(request: Request, call_next):
        if settings.api_token and request.url.path.startswith('/api/') and request.method != 'OPTIONS':
            supplied = request.headers.get('Authorization', '')
            if not hmac.compare_digest(supplied, 'Bearer ' + settings.api_token):
                return JSONResponse({'detail': 'Invalid or missing API token'}, status_code=401)
        return await call_next(request)

    def ready(job_id):
        job = store.job(job_id)
        if not job:
            raise HTTPException(404, 'Job not found')
        if job['status'] != 'ready':
            raise HTTPException(409, dict(message='Job is not ready', status=job['status'], phase=job['phase']))
        return job

    def incident(job_id, incident_id):
        ready(job_id)
        g = store.incident(job_id, incident_id)
        if not g:
            raise HTTPException(404, 'Incident not found')
        return g

    def queue_check():
        if sum(j['status'] in ('queued', 'running') for j in store.jobs()) >= 4:
            raise HTTPException(429, 'Processing queue is full; wait for an existing job to finish')

    def safe_filename(name):
        name = re.split(r'[/\\]', name or 'alerts.jsonl')[-1]
        name = re.sub(r'[^A-Za-z0-9_.-]', '_', name)[:150]
        if Path(name).suffix.lower() not in ('.zip', '.json', '.jsonl', '.ndjson'):
            raise HTTPException(415, 'Upload a ZIP or a JSONL alerts file (.json/.jsonl/.ndjson)')
        return name

    @app.get('/health')
    def health():
        return dict(status='ok', version='1.0.0', llm_enabled=settings.llm_enabled and bool(settings.openai_api_key), ml='IsolationForest + TF-IDF')

    @app.get('/api/v1/jobs')
    def jobs():
        return dict(items=store.jobs())

    @app.post('/api/v1/jobs', status_code=202)
    async def upload(request: Request, file: Annotated[UploadFile, File()],
                     scenario: Annotated[str | None, Form()] = None,
                     gap_minutes: Annotated[float, Form(gt=0, le=1440)] = 15,
                     max_span_minutes: Annotated[float, Form(gt=0, le=1440)] = 60,
                     syslog_year: Annotated[int, Form(ge=1970, le=2100)] = 2022,
                     limit: Annotated[int, Form(ge=0, le=3_000_000)] = 0):
        queue_check()
        filename = safe_filename(file.filename)
        try:
            options = Options(scenario=scenario or None, gap_minutes=gap_minutes, max_span_minutes=max_span_minutes, syslog_year=syslog_year, limit=limit)
        except ValueError as e:
            await file.close()
            raise HTTPException(422, 'Invalid analysis options') from e
        job = store.create_job(options.model_dump())
        path = store.folder(job['id']) / filename
        written = 0
        try:
            with path.open('wb') as f:
                while chunk := await file.read(1024 * 1024):
                    written += len(chunk)
                    if written > settings.max_upload_bytes:
                        raise HTTPException(413, 'Upload exceeds configured size limit')
                    f.write(chunk)
            if written == 0:
                raise HTTPException(400, 'Empty upload')
            request.app.state.executor.submit(process_job, store, settings, job['id'], path)
        except Exception:
            path.unlink(missing_ok=True)
            store.update_job(job['id'], 'failed', 'upload_failed', error='Upload could not be saved')
            raise
        finally:
            await file.close()
        return store.job(job['id'])

    @app.post('/api/v1/jobs/batch', status_code=202)
    async def batch(request: Request, payload: Batch):
        queue_check()
        filename = safe_filename(payload.filename)
        if Path(filename).suffix == '.zip':
            raise HTTPException(415, 'Batch filename must be a JSONL extension')
        options = Options(**payload.model_dump(exclude={'filename', 'records'}))
        job = store.create_job(options.model_dump())
        path = store.folder(job['id']) / filename
        try:
            with path.open('w') as f:
                for record in payload.records:
                    f.write(json.dumps(record) + '\n')
            request.app.state.executor.submit(process_job, store, settings, job['id'], path)
        except Exception:
            store.update_job(job['id'], 'failed', 'upload_failed', error='Batch could not be saved')
            raise
        return store.job(job['id'])

    @app.get('/api/v1/jobs/{job_id}')
    def job(job_id: str):
        result = store.job(job_id)
        if not result:
            raise HTTPException(404, 'Job not found')
        return result

    @app.get('/api/v1/jobs/{job_id}/stats')
    def stats(job_id: str):
        ready(job_id)
        return store.stats(job_id)

    @app.get('/api/v1/jobs/{job_id}/incidents')
    def incidents(job_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                  scenario: str | None = None, band: Literal['high', 'medium', 'low'] | None = None,
                  status: Literal['new', 'investigating', 'resolved', 'dismissed'] | None = None,
                  search: str | None = Query(None, max_length=200), min_priority: float = Query(0, ge=0, le=100),
                  include_dismissed: bool = False):
        ready(job_id)
        return store.list_incidents(job_id, limit, offset, scenario, band, status, search, min_priority, include_dismissed)

    @app.get('/api/v1/jobs/{job_id}/incidents/{incident_id}')
    def detail(job_id: str, incident_id: str):
        g = incident(job_id, incident_id)
        records = selected_records(store, job_id, g)
        return dict(incident=g, representative_evidence=records, explanation=detail_explanation(g, records))

    @app.get('/api/v1/jobs/{job_id}/incidents/{incident_id}/evidence')
    def evidence(job_id: str, incident_id: str, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
        incident(job_id, incident_id)
        return store.evidence(job_id, incident_id, limit, offset)

    @app.get('/api/v1/jobs/{job_id}/incidents/{incident_id}/related')
    def related(job_id: str, incident_id: str, limit: int = Query(5, ge=1, le=20)):
        incident(job_id, incident_id)
        with related_lock:
            if job_id not in related_cache:
                related_cache[job_id] = RelatedIndex(store.all_groups(job_id))
                if len(related_cache) > 2:
                    related_cache.popitem(last=False)
            related_cache.move_to_end(job_id)
            items = related_cache[job_id].related(incident_id, limit)
        return dict(items=items)

    @app.post('/api/v1/jobs/{job_id}/incidents/{incident_id}/ask')
    def ask(job_id: str, incident_id: str, payload: Ask):
        g = incident(job_id, incident_id)
        return explain(settings, g, selected_records(store, job_id, g), payload.question, payload.use_llm)

    @app.patch('/api/v1/jobs/{job_id}/incidents/{incident_id}/feedback')
    def feedback(job_id: str, incident_id: str, payload: Feedback):
        incident(job_id, incident_id)
        return store.feedback(job_id, incident_id, payload.status, payload.disposition, payload.note)

    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False,
                       allow_methods=['GET', 'POST', 'PATCH'], allow_headers=['Content-Type', 'Authorization'])
    return app

app = create_app()
