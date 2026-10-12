import importlib.util
import io
import json
from email.message import Message
from pathlib import Path
from unittest.mock import MagicMock

spec = importlib.util.spec_from_file_location('frontend_server', Path(__file__).resolve().parents[1] / 'serve.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def request(value, origin='http://127.0.0.1:5173', path='/api/v1/jobs/demo/incidents/a/feedback'):
    payload = json.dumps(value).encode()
    handler = server.Handler.__new__(server.Handler)
    handler.path = path
    handler.headers = Message()
    for k, v in {'Content-Type': 'application/json', 'Content-Length': str(len(payload)), 'Origin': origin, 'Host': '127.0.0.1:5173'}.items():
        handler.headers[k] = v
    handler.rfile = io.BytesIO(payload)
    handler.reply = MagicMock()
    return handler


def test_local_gateway_forwards_only_valid_review(monkeypatch):
    value = {'status': 'investigating', 'disposition': 'suspicious', 'note': 'Checking the evidence.'}
    upstream = MagicMock()
    upstream.__enter__.return_value = upstream
    upstream.status = 200
    upstream.read.return_value = b'{"id":"a"}'
    send = MagicMock(return_value=upstream)
    monkeypatch.setattr(server, 'urlopen', send)
    monkeypatch.setattr(server, 'CAN_REVIEW', True)
    monkeypatch.setattr(server, 'CAN_UPLOAD', False)
    handler = request(value)
    handler.do_PATCH()
    assert handler.reply.call_args.args[0] == 200
    forwarded = send.call_args.args[0]
    assert forwarded.method == 'PATCH'
    assert json.loads(forwarded.data) == value
    for args, expected in [({'value': value, 'origin': 'https://other.example'}, 403),
                           ({'value': {**value, 'status': 'invalid'}}, 400),
                           ({'value': {**value, 'note': 'x'*2001}}, 400),
                           ({'value': value, 'path': '/api/v1/jobs/other/incidents/a/feedback'}, 404)]:
        handler = request(**args)
        handler.do_PATCH()
        assert handler.reply.call_args.args[0] == expected
    assert send.call_count == 1
    monkeypatch.setattr(server, 'CAN_REVIEW', False)
    handler = request(value)
    handler.do_PATCH()
    assert handler.reply.call_args.args[0] == 403
