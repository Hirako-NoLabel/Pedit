from pathlib import Path
import importlib.util
import json
import socket
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen

import pytest

from pedit import app, scan_engine


@pytest.fixture(autouse=True)
def offline_core(monkeypatch):
    """Exercise the core without optional OCR or outbound network access."""
    monkeypatch.setattr(scan_engine, 'RapidOCR', None)
    monkeypatch.setattr(scan_engine, 'pytesseract', None)
    connect = socket.socket.connect

    def local_connect(sock, address):
        if isinstance(address, tuple) and address[0] not in ('127.0.0.1', '::1'):
            raise AssertionError('Core tests must not contact an external service')
        return connect(sock, address)

    monkeypatch.setattr(socket.socket, 'connect', local_connect)


@pytest.fixture(scope='session')
def samples():
    path = Path(__file__).resolve().parent / 'fixtures/pdf_factory.py'
    spec = importlib.util.spec_from_file_location('pdf_factory', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(app, 'WORKDIR', tmp_path)
    monkeypatch.setattr(app, 'SESSIONS', {})
    server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()

    def request(path, data=None, raw=False):
        headers = {}
        if data is not None and not isinstance(data, bytes):
            data = json.dumps(data).encode()
            headers['Content-Type'] = 'application/json'
        if isinstance(data, bytes) and path == '/api/open':
            headers['X-Filename'] = 'test.pdf'
        req = Request(f'http://127.0.0.1:{server.server_port}{path}', data=data, headers=headers)
        with urlopen(req, timeout=20) as response:
            result = response.read()
            return result if raw else json.loads(result)

    yield request
    server.shutdown()
    server.server_close()
    worker.join(timeout=5)
