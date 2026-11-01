"""Selected-build launcher probes; fixture execution requires explicit policy allowance.

Tests use loopback-only synthetic HTTP responses. Never bypass a host's script
execution policy; a denied Windows dot-source remains separately unqualified.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LAUNCHER = Path(__file__).resolve().parents[1] / 'Start-IRGS-3.3.ps1'
POWERSHELL = shutil.which('pwsh') or shutil.which('powershell.exe')
PERMITTED = os.environ.get('IRGS_LAUNCHER_TEST_POLICY_ALLOWED') == '1'
HASH_FIELDS = ('app_manifest_sha256', 'host_source_sha256', 'engine_manifest_sha256',
               'engine_core_sha256', 'catalog_manifest_sha256', 'catalog_portfolio_sha256')


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def identity():
    result = {'schema_version': 1, 'edition': '3.4.8', 'classification': 'pre_alpha'}
    result.update({field: format(i + 1, 'x') * 64 for i, field in enumerate(HASH_FIELDS)})
    return result


@unittest.skipUnless(POWERSHELL and PERMITTED,
                     'PowerShell fixture requires available runtime and explicitly allowed script policy')
class LauncherBuildIdentityTests(unittest.TestCase):
    def setUp(self):
        self.state = {'catalog': True, 'token': 'synthetic-local-token-only', 'build': identity()}
        state, paths = self.state, []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                paths.append(self.path)
                if self.path == '/api/catalog':
                    body = ({'core': {'id': 'IRGS-CORE-3.3', 'version': '3.3',
                                      'single_world_per_campaign': True}}
                            if state['catalog'] else {'other': True})
                elif self.path == '/api/campaigns':
                    body = {'campaigns': [], 'token': state['token']}
                    if state['build'] != '__omit__':
                        body['build'] = state['build']
                else:
                    self.send_error(404)
                    return
                raw = json.dumps(body).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.thread.join)
        self.addCleanup(self.server.shutdown)
        self.paths = paths

    def powershell(self, expression):
        result = subprocess.run([POWERSHELL, '-NoProfile', '-NonInteractive', '-Command', expression],
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def probe(self, expected):
        encoded = ps_quote(json.dumps(expected, separators=(',', ':')))
        command = ('. ' + ps_quote(LAUNCHER) + '; $expected = ' + encoded
                   + ' | ConvertFrom-Json; Get-IrgsHostState -HostPort '
                   + str(self.server.server_port) + ' -ExpectedBuild $expected')
        return self.powershell(command)

    def test_exact_selected_build_and_session_are_ready(self):
        self.assertEqual(self.probe(identity()), 'Ready')
        self.assertEqual(self.paths, ['/api/catalog', '/api/campaigns'])

    def test_each_component_and_build_field_must_match(self):
        for field in HASH_FIELDS:
            with self.subTest(field=field):
                self.state['build'] = identity()
                self.state['build'][field] = 'a' * 64
                self.assertEqual(self.probe(identity()), 'Occupied')
        for field, value in [('edition', '3.4.7'), ('classification', 'unclassified'),
                             ('schema_version', 2)]:
            with self.subTest(field=field):
                self.state['build'] = identity()
                self.state['build'][field] = value
                self.assertEqual(self.probe(identity()), 'Occupied')

    def test_missing_malformed_or_unknown_identity_never_reuses(self):
        for broken in (None, {}, {**identity(), 'engine_manifest_sha256': None},
                       {**identity(), 'catalog_portfolio_sha256': 'A' * 64},
                       {**identity(), 'schema_version': '1'}):
            with self.subTest(broken=broken):
                self.state['build'] = broken
                self.assertEqual(self.probe(identity()), 'Occupied')
        self.state['build'] = '__omit__'
        self.assertEqual(self.probe(identity()), 'Occupied')
        self.state['build'] = identity()
        self.assertEqual(self.probe(None), 'Occupied')
        missing_expected = identity()
        missing_expected['host_source_sha256'] = None
        self.assertEqual(self.probe(missing_expected), 'Occupied')

    def test_unrelated_or_incomplete_health_does_not_reuse(self):
        self.state['catalog'] = False
        self.assertEqual(self.probe(identity()), 'Occupied')
        self.assertEqual(self.paths, ['/api/catalog'])
        self.state['catalog'] = True
        self.state['token'] = 'short'
        self.assertEqual(self.probe(identity()), 'Occupied')

    def test_mismatched_existing_listener_is_not_stopped_or_replaced(self):
        self.state['build']['engine_core_sha256'] = 'a' * 64
        with tempfile.TemporaryDirectory(prefix='irgs-launcher-app-') as folder:
            (Path(folder) / 'server.py').write_text('# synthetic host entry\n', encoding='utf-8')
            bundled = Path(folder) / '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b'not executed')
            command = ('. ' + ps_quote(LAUNCHER) + '; $env:USERPROFILE = ' + ps_quote(folder)
                + '; $AppRoot = ' + ps_quote(folder)
                + '; $expected = ' + ps_quote(json.dumps(identity())) + ' | ConvertFrom-Json;'
                + ' function Get-IrgsExpectedBuild { return $expected };'
                + " function Start-Process { throw 'unexpected process start' };"
                + " try { Start-IrgsWebsite -HostPort " + str(self.server.server_port)
                + " -OpenBrowser $false -WaitSeconds 2; exit 9 }"
                + " catch { $_.Exception.Message }")
            output = self.powershell(command)
        self.assertIn('left running', output)
        self.assertIn('-Port', output)
        with socket.create_connection(('127.0.0.1', self.server.server_port), timeout=2):
            pass

    def test_matching_listener_is_reused_without_starting_another_process(self):
        with tempfile.TemporaryDirectory(prefix='irgs-launcher-app-') as folder:
            (Path(folder) / 'server.py').write_text('# synthetic host entry\n', encoding='utf-8')
            bundled = Path(folder) / '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b'not executed')
            command = ('. ' + ps_quote(LAUNCHER) + '; $env:USERPROFILE = ' + ps_quote(folder)
                + '; $AppRoot = ' + ps_quote(folder)
                + '; $expected = ' + ps_quote(json.dumps(identity())) + ' | ConvertFrom-Json;'
                + ' function Get-IrgsExpectedBuild { return $expected };'
                + ' function Confirm-IrgsRelease {};'
                + " function Start-Process { throw 'unexpected process start' };"
                + ' Start-IrgsWebsite -HostPort ' + str(self.server.server_port)
                + ' -OpenBrowser $false -WaitSeconds 2')
            output = self.powershell(command)
        self.assertIn('Reusing the existing website', output)
        with socket.create_connection(('127.0.0.1', self.server.server_port), timeout=2):
            pass

    def test_expected_identity_comes_from_selected_app_and_matching_engine(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix='irgs-identity-selection-') as root:
            root = Path(root)
            app, suite = root / 'app', root / 'suite'
            (suite / 'runtime').mkdir(parents=True)
            app.mkdir()
            (suite / 'release.json').write_bytes(b'selected engine manifest')
            (suite / 'runtime' / 'core_world.py').write_bytes(b'selected engine core')
            expected = identity()
            expected['engine_manifest_sha256'] = hashlib.sha256((suite / 'release.json').read_bytes()).hexdigest()
            expected['engine_core_sha256'] = hashlib.sha256((suite / 'runtime' / 'core_world.py').read_bytes()).hexdigest()
            (app / 'build_identity.py').write_text('def running_build():\n    return ' + repr(expected) + '\n', encoding='utf-8')
            call = ('Get-IrgsExpectedBuild -PythonPath ' + ps_quote(__import__('sys').executable)
                    + ' -HostFolder ' + ps_quote(app) + ' -SuiteFolder ' + ps_quote(suite))
            command = ('. ' + ps_quote(LAUNCHER) + '; $selected = ' + call
                       + '; $selected | ConvertTo-Json -Compress')
            self.assertEqual(json.loads(self.powershell(command)), expected)
            (suite / 'runtime' / 'core_world.py').write_bytes(b'other engine core')
            refused = ('. ' + ps_quote(LAUNCHER) + '; try { ' + call
                       + " | Out-Null; 'unexpected' } catch { $_.Exception.Message }")
            output = self.powershell(refused)
            self.assertIn('cannot establish the selected', output)
            self.assertIn('No application was stopped', output)
            (app / 'build_identity.py').write_text('def running_build():\n    return {}\n', encoding='utf-8')
            self.assertIn('cannot establish the selected', self.powershell(refused))

    @unittest.skipUnless(os.environ.get('IRGS_TEST_APP_ROOT'),
                         'Real pinned App/Catalog source is not selected')
    def test_expected_identity_uses_actual_pinned_app_metadata(self):
        import sys
        app = os.environ['IRGS_TEST_APP_ROOT']
        source = ('import json,sys;sys.path.insert(0,sys.argv[1]);'
                  'from build_identity import running_build;print(json.dumps(running_build()))')
        expected = json.loads(subprocess.check_output([sys.executable, '-B', '-c', source, app], text=True))
        command = ('. ' + ps_quote(LAUNCHER) + '; $selected = Get-IrgsExpectedBuild -PythonPath '
                   + ps_quote(sys.executable) + ' -HostFolder ' + ps_quote(app)
                   + ' -SuiteFolder ' + ps_quote(LAUNCHER.parent) + '; $selected | ConvertTo-Json -Compress')
        self.assertEqual(json.loads(self.powershell(command)), expected)

    def test_absent_listener_is_stopped(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.assertEqual(self.probe(identity()), 'Stopped')


if __name__ == '__main__':
    unittest.main()
