"""Exercise PHP routes, CSRF, persistence and management access with an isolated database."""
import http.cookiejar
import os
from pathlib import Path
import re
import socket
import sqlite3
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    db_path = str(Path(folder) / 'requests.sqlite3')
    with socket.socket() as socket_handle:
        socket_handle.bind(('127.0.0.1', 0))
        port = socket_handle.getsockname()[1]
    environment = dict(os.environ, SURRENT_DATABASE=db_path, SURRENT_ADMIN_EMAIL='admin@example.test', DJANGO_ADMIN_PASSWORD='local-test-only')
    with open(Path(folder) / 'server.log', 'w') as log:
        server = subprocess.Popen(['php', '-S', f'127.0.0.1:{port}', '-t', 'public', 'tests/router.php'], cwd=ROOT, env=environment, stdout=log, stderr=log)
        try:
            client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            base = f'http://127.0.0.1:{port}'
            def request(path, data=None):
                encoded = urllib.parse.urlencode(data).encode() if data is not None else None
                try:
                    response = client.open(base + path, data=encoded, timeout=5)
                except urllib.error.HTTPError as error:
                    response = error
                return response.status, response.read().decode(errors='replace')
            for _ in range(50):
                try:
                    status, body = request('/healthz')
                    break
                except urllib.error.URLError:
                    time.sleep(.1)
            assert (status, body) == (200, 'ok')
            status, body = request('/')
            assert status == 200 and 'Surren Technologies' in body and '{%' not in body
            token = re.search(r'name="csrf_token" value="([^"]+)"', body)[1]
            assert request('/consult', {'email': 'person@example.test'})[0] == 403
            assert request('/consult', {'email': 'invalid', 'csrf_token': token})[0] == 422
            assert request('/consult', {'email': 'bot@example.test', 'website': 'spam', 'csrf_token': token})[0] == 200
            assert request('/consult', {'email': 'person@example.test', 'csrf_token': token})[0] == 200
            db = sqlite3.connect(db_path)
            assert db.execute('SELECT email FROM consult_requests').fetchall() == [('person@example.test',)]
            assert request('/manage-console/')[0] == 200
            assert 'person@example.test' not in request('/manage-console/')[1]
            status, body = request('/manage-console/', {'email': 'admin@example.test', 'password': 'local-test-only', 'csrf_token': token})
            assert status == 200 and 'person@example.test' in body
            admin_token = re.search(r'name="csrf_token" value="([^"]+)"', body)[1]
            assert request('/manage-console/', {'action': 'handled', 'id': '1', 'csrf_token': admin_token})[0] == 200
            assert db.execute('SELECT handled FROM consult_requests').fetchone()[0] == 1
            assert request('/manage-console/', {'action': 'logout', 'csrf_token': admin_token})[0] == 200
            assert 'person@example.test' not in request('/manage-console/')[1]
            for path in ['/app.php', '/home.php', '/.env', '/passenger_wsgi.py', '/missing']:
                assert request(path)[0] == 404, path
            assert request('/assets/logo.png')[0] == 200
            print('PHP checks passed: routes, assets, CSRF, validation, honeypot, persistence, admin login, handled status and logout.')
        finally:
            server.terminate()
            server.wait(timeout=5)
