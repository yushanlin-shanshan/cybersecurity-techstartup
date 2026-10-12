"""Integration checks against the existing backend, using an isolated temporary dataset."""
import time
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.config import Settings


def test_status_lifecycle_persists_and_filters(tmp_path):
    settings = Settings(data_dir=tmp_path / 'data', llm_enabled=False)
    with TestClient(create_app(settings)) as client:
        job = client.post('/api/v1/jobs/batch', json={'records': [{
            'timestamp': '2022-01-21T00:00:00Z', 'source_ip': '192.0.2.1',
            'host': 'test-host', 'severity': 5, 'sensor': 'endpoint',
            'description': 'Test review lifecycle',
        }]}).json()['id']
        for _ in range(300):
            state = client.get(f'/api/v1/jobs/{job}').json()
            if state['status'] in ('ready', 'failed'):
                break
            time.sleep(.02)
        assert state['status'] == 'ready'
        queue = f'/api/v1/jobs/{job}/incidents'
        ident = client.get(queue).json()['items'][0]['id']
        path = f'{queue}/{ident}'
        for status in ['investigating', 'resolved', 'dismissed', 'new']:
            # A duplicate can be dismissed without declaring it benign.
            value = {'status': status, 'disposition': 'unreviewed', 'note': f'Checked {status}.'}
            result = client.patch(path + '/feedback', json=value)
            assert result.status_code == 200
            assert result.json()['review'] == value
            assert client.get(queue, params={'status': status, 'include_dismissed': True}).json()['total'] == 1
            assert client.get(queue).json()['total'] == (0 if status == 'dismissed' else 1)
        invalid = client.patch(path + '/feedback', json={**value, 'status': 'invalid'})
        assert invalid.status_code == 422
        assert client.get(path).json()['incident']['review'] == value
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get(path).json()['incident']['review'] == value

