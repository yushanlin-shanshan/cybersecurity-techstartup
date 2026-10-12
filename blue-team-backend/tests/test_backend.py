import io
import json
import time
import zipfile
from dataclasses import replace

import httpx
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.config import Settings
from backend.explain import explain
from backend.ml import enrich


def record(time='2022-01-21T00:00:00Z', src='10.0.0.1', description='Remote command execution'):
    return dict(timestamp=time, source_ip=src, destination_ip='10.0.0.2', host='10.0.0.2', severity=12,
                sensor='endpoint', rule_id='42', description=description, raw_log='An original evidence line')


def wait_job(client, job_id):
    for _ in range(300):
        result = client.get(f'/api/v1/jobs/{job_id}').json()
        if result['status'] in ('ready', 'failed'):
            return result
        time.sleep(.02)
    pytest.fail('Job did not complete')

@pytest.fixture
def service(tmp_path):
    settings = Settings(data_dir=tmp_path / 'data')
    app = create_app(settings)
    with TestClient(app) as client:
        yield client, app


def test_full_batch_api_roundtrip(service):
    client, app = service
    original = [record(), record('2022-01-21T00:10:00Z'), record('2022-01-21T02:00:00Z')]
    response = client.post('/api/v1/jobs/batch', json={'records': original})
    assert response.status_code == 202
    job_id = response.json()['id']
    status = wait_job(client, job_id)
    assert status['status'] == 'ready', status
    assert status['summary']['counts']['accepted'] == 3
    assert status['summary']['groups'] == 2
    page = client.get(f'/api/v1/jobs/{job_id}/incidents').json()
    assert page['total'] == 2
    assert page['items'][0]['priority'] >= page['items'][1]['priority']
    ident = page['items'][0]['id']
    base = f'/api/v1/jobs/{job_id}/incidents/{ident}'
    details = client.get(base).json()
    assert details['explanation']['mode'] == 'local'
    ev = client.get(base+'/evidence?limit=1').json()
    assert ev['items'][0]['original_record'] in original
    assert ev['items'][0]['normalized']['sensor'] == 'endpoint'
    assert ev['limit'] == 1
    assert client.get(base+'/related').status_code == 200
    answer = client.post(base+'/ask', json={'question':'Why is this ranked highly?', 'use_llm': True}).json()
    assert answer['mode'] == 'local'
    assert answer['fallback_reason']
    for claim in answer['claims']:
        fetched = app.state.store.evidence_ids(job_id, ident, claim['evidence_ids'])
        assert len(fetched) == len(set(claim['evidence_ids']))
    response = client.patch(base+'/feedback', json={'status': 'dismissed', 'disposition':'benign', 'note':'Authorized test'})
    assert response.status_code == 200
    assert client.get(f'/api/v1/jobs/{job_id}/incidents').json()['total'] == 1
    assert client.get(f'/api/v1/jobs/{job_id}/incidents?include_dismissed=true').json()['total'] == 2
    assert client.get(f'/api/v1/jobs/{job_id}/stats').json()['total_incidents'] == 2
    assert client.get(f'/api/v1/jobs/{job_id}/incidents?search=%27%20OR%201=1').json()['total'] == 0
    assert client.get(base+'/evidence?limit=100000').status_code == 422
    assert client.get('/api/v1/jobs/missing/incidents').status_code == 404


def test_zip_ingestion_scenario_isolation_and_rejects(service):
    client, _ = service
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('fox_wazuh.json', json.dumps(record())+'\nmalformed\n')
        z.writestr('shaw_wazuh.json', json.dumps(record())+'\n')
    response = client.post('/api/v1/jobs', files={'file':('alerts.zip', blob.getvalue(), 'application/zip')})
    job = wait_job(client, response.json()['id'])
    assert job['status'] == 'ready', job
    assert job['summary']['counts']['accepted'] == 2
    assert job['summary']['counts']['rejected'] == 1
    assert job['summary']['groups'] == 2
    ids = client.get(f"/api/v1/jobs/{job['id']}/incidents").json()['items']
    assert {g['scenario'] for g in ids} == {'fox', 'shaw'}
    assert client.get(f"/api/v1/jobs/{job['id']}/incidents/{ids[0]['id']}/related").json()['items'] == []


def test_upload_validation_and_failed_job(service):
    client, _ = service
    assert client.post('/api/v1/jobs', files={'file':('script.py', b'bad')}).status_code == 415
    assert client.post('/api/v1/jobs', files={'file':('empty.jsonl', b'')}).status_code == 400
    assert client.post('/api/v1/jobs', files={'file':('alerts.jsonl', b'bad')}, data={'gap_minutes':'-1'}).status_code == 422
    result = client.post('/api/v1/jobs', files={'file':('alerts.zip', b'not a zip')}).json()
    failed = wait_job(client, result['id'])
    assert failed['status'] == 'failed'
    assert client.get(f"/api/v1/jobs/{failed['id']}/incidents").status_code == 409


def test_auth_cors_and_size_limit(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, api_token='test-token', max_upload_bytes=1))
    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
        assert client.get('/api/v1/jobs').status_code == 401
        assert client.get('/api/v1/jobs', headers={'Authorization':'Bearer test-token'}).status_code == 200
        preflight = client.options('/api/v1/jobs', headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'Authorization'})
        assert preflight.status_code == 200
        assert preflight.headers['access-control-allow-origin'] == 'http://localhost:3000'
        response = client.post('/api/v1/jobs', headers={'Authorization':'Bearer test-token'}, files={'file':('x.jsonl', b'x'*70000)})
        assert response.status_code == 413


def group(i, count=1):
    return dict(id=str(i), scenario='test', anchor=['source',f'10.0.0.{i}'], count=count, max_level=3, start='2022-01-21T00:00:00Z', end='2022-01-21T00:00:30Z',
                stages=[], sensors=['Wazuh'], hosts=['server'], destinations=[], signature_counts={'Routine update': count}, evidence=[], score=10,
                score_components={}, rarest_signature_fraction=.5)


def test_ml_runs_is_reproducible_and_ties_are_neutral():
    a=[group(i) for i in range(25)]
    enrich(a)
    assert all(g['ml']['enabled'] for g in a)
    assert all(g['ml']['anomaly_percentile'] == 50 for g in a)
    b=[group(i, count=1 if i<24 else 10000) for i in range(25)]
    c=[group(i, count=1 if i<24 else 10000) for i in range(25)]
    enrich(b);enrich(c)
    assert [g['priority'] for g in b] == [g['priority'] for g in c]
    assert next(g for g in b if g['id']=='24')['ml']['anomaly_percentile'] > 95
    assert all(0<=g['priority']<=100 for g in b)


def test_llm_response_validation_and_fallback(service):
    client, app = service
    job = wait_job(client, client.post('/api/v1/jobs/batch', json={'records':[record()]}).json()['id'])
    incident_id = client.get(f"/api/v1/jobs/{job['id']}/incidents").json()['items'][0]['id']
    g = app.state.store.incident(job['id'], incident_id)
    records = app.state.store.evidence(job['id'], incident_id)['items']
    settings = replace(app.state.settings, llm_enabled=True, openai_api_key='fake-key')
    def provider(cite):
        def handle(request):
            data=json.loads(request.content)
            assert data['store'] is False
            assert data['text']['format']['strict'] is True
            narrative=dict(answer='An execution indicator was observed.', claims=[dict(text='A record has an execution indicator.', evidence_ids=[cite])],next_steps=['Review this evidence.'],caveats=['Success is unconfirmed.'])
            return httpx.Response(200,json={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(narrative)}]}]})
        return httpx.MockTransport(handle)
    result=explain(settings,g,records,'Explain',True,provider(records[0]['alert_id']))
    assert result['mode']=='llm'
    bad=explain(settings,g,records,'Explain',True,provider(999999))
    assert bad['mode']=='local' and bad['fallback_reason']
    failure=explain(settings,g,records,'Explain',True,httpx.MockTransport(lambda _:httpx.Response(429,json={'error':'Rate limit'})))
    assert failure['mode']=='local'


def test_related_suggestions_have_entity_time_and_semantic_support(service):
    client, _ = service
    records=[record(), record('2022-01-21T00:30:00Z'), record('2022-01-22T00:30:00Z')]
    job=wait_job(client,client.post('/api/v1/jobs/batch',json={'records':records}).json()['id'])
    queue=client.get(f"/api/v1/jobs/{job['id']}/incidents").json()['items']
    first=next(g for g in queue if g['start'].startswith('2022-01-21T00:00:00'))
    related=client.get(f"/api/v1/jobs/{job['id']}/incidents/{first['id']}/related").json()['items']
    assert len(related)==1
    assert related[0]['similarity']>.99 and related[0]['same_anchor']
    assert related[0]['gap_minutes']==30


def test_chunked_upload_limit_and_auth_error_cors(tmp_path):
    app=create_app(Settings(data_dir=tmp_path,api_token='token',max_upload_bytes=1))
    with TestClient(app) as client:
        unauthorized=client.get('/api/v1/jobs',headers={'Origin':'http://localhost:3000'})
        assert unauthorized.status_code==401
        assert unauthorized.headers['access-control-allow-origin']=='http://localhost:3000'
        response=client.post('/api/v1/jobs/batch',headers={'Authorization':'Bearer token','Content-Type':'application/json'},content=(b'x'*35000 for _ in range(3)))
        assert response.status_code==413


def test_job_and_analyst_feedback_survive_restart(tmp_path):
    settings=Settings(data_dir=tmp_path)
    with TestClient(create_app(settings)) as client:
        job=wait_job(client,client.post('/api/v1/jobs/batch',json={'records':[record()]}).json()['id'])
        incident=client.get(f"/api/v1/jobs/{job['id']}/incidents").json()['items'][0]
        client.patch(f"/api/v1/jobs/{job['id']}/incidents/{incident['id']}/feedback",json={'status':'investigating','disposition':'suspicious','note':'Persist me'})
    with TestClient(create_app(settings)) as client:
        assert client.get(f"/api/v1/jobs/{job['id']}").json()['status']=='ready'
        review=client.get(f"/api/v1/jobs/{job['id']}/incidents/{incident['id']}").json()['incident']['review']
        assert review['note']=='Persist me' and review['status']=='investigating'
