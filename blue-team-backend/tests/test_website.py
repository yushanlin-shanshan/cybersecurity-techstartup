import importlib
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.config import Settings

def test_website_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv('FRONTEND_DIR', str(tmp_path))
    monkeypatch.setenv('DATA_DIR', str(tmp_path / 'module-data'))
    (tmp_path / 'index.html').write_text('<h1>sigsig</h1>')
    Website = importlib.import_module('backend.website').Website
    api = create_app(Settings(data_dir=tmp_path / 'jobs', api_token='test-internal-secret'))
    app = Website(api, tmp_path)
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        config = client.get('/app-config.json').json()
        assert config['can_upload'] is False
        assert 'test-internal-secret' not in str(config)
        assert client.get('/api/v1/jobs').status_code == 200
        assert client.post('/api/v1/jobs').status_code == 404
        assert client.get('/openapi.json').status_code == 404
        monkeypatch.setenv('ENABLE_DATASET_UPLOADS', 'true')
        assert client.get('/app-config.json').json()['can_upload'] is True
        assert client.post('/api/v1/jobs', headers={'Origin': 'https://evil.example'}).status_code == 403
        assert client.post('/api/v1/jobs', headers={'Origin': 'https://testserver'}).status_code == 422
        monkeypatch.setenv('ENABLE_REVIEW_WRITES', 'true')
        review = {'status':'resolved','disposition':'benign','note':'test'}
        assert client.patch('/api/v1/jobs/demo/incidents/test/feedback', json=review, headers={'Origin':'https://evil.example'}).status_code == 403
        assert client.post('/api/v1/jobs/batch', json={}).status_code == 404
    with TestClient(api) as direct:
        assert direct.get('/api/v1/jobs').status_code == 401
