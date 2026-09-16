"""Run with a wheel-installed interpreter, preferably outside the source checkout."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

import pymupdf as fitz
from pedit import __version__


def main():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix='pedit-wheel-') as folder:
        env = dict(os.environ, PEDIT_NO_BROWSER='1', PDF_EDITOR_PORT=str(port), PEDIT_DATA_DIR=folder)
        # Capture console output to a temporary log, avoiding pipe backpressure.
        with (Path(folder) / 'server.log').open('w', encoding='utf-8') as log:
            process = subprocess.Popen([sys.executable, '-m', 'pedit'], cwd=folder, env=env,
                                       stdout=log, stderr=log)
            try:
                base = f'http://127.0.0.1:{port}'

                def get(path, data=None):
                    req = Request(base + path, data=data)
                    with urlopen(req, timeout=5) as response:
                        return response.read()

                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError('Installed server exited before startup')
                    try:
                        health = json.loads(get('/api/health'))
                        break
                    except (URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Installed server did not become ready')
                assert health['version'] == __version__ == '0.1.0'
                assert b'Pedit OSS' in get('/')
                assert b'progressPayload' in get('/app.js')
                assert len(get('/styles.css')) > 100
                with fitz.open() as doc:
                    doc.new_page().insert_text((40, 80), 'TEST-A')
                    raw = doc.tobytes()
                sid = json.loads(get('/api/open', raw))['id']
                assert get(f'/api/page?id={sid}&page=0').startswith(b'\x89PNG')
                exported = get('/api/export', json.dumps({'id': sid, 'edits': []}).encode())
                with fitz.open(stream=exported, filetype='pdf') as doc:
                    assert 'TEST-A' in doc[0].get_text()
                print('PASS: installed wheel startup, health, UI assets, PDF import, render, export')
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == '__main__':
    main()
