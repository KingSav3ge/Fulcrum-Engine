#!/usr/bin/env python3
"""Engine-side qualification of explicitly selected App and Catalog sources.

Runs fresh-process, loopback-only HTTP checks over temporary synthetic saves.
Original Catalog consumer declarations and committed App pins remain unchanged.
This records candidate source compatibility, not a new joined release approval.
"""
import argparse
from contextlib import ExitStack
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ENGINE = Path(__file__).resolve().parents[1]
SELECTED = {}
MODULES = {}
EVIDENCE = {}


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def initialize(app, catalog):
    app, catalog = app.resolve(), catalog.resolve()
    roots = {'engine': ENGINE, 'app': app, 'catalog': catalog}
    for name, root in roots.items():
        if not (root/'.git').exists():
            raise ValueError('Select a Git checkout for ' + name)
        SELECTED[name] = {'root': str(root), 'commit': git(root, 'rev-parse', 'HEAD')}
        if name != 'engine' and git(root, 'status', '--porcelain'):
            raise ValueError('Select clean App/Catalog checkouts; preserve their independent work')
    SELECTED['app']['committed_pins'] = {name: git(app, 'rev-parse', 'HEAD:'+name)
                                       for name in ('Engine', 'Catalog')}
    os.environ['IRGS_ENGINE_ROOT'] = str(ENGINE/'IRGS_3_3')
    os.environ['IRGS_CATALOG_ROOT'] = str(catalog/'IRGS_Catalog')
    sys.path[:0] = [str(app/'IRGS_Web'), str(ENGINE/'IRGS_3_3/runtime'), str(catalog/'IRGS_Catalog')]
    imports = {'engine': ('core_world', 'phase_contract', 'shared_runtime', 'response_depot',
                          'offline_responses', 'runtime_contracts', 'starting_selection',
                          'historical_campaigns', 'settlement_setup', 'solo_provider', 'openai_proposals',
                          'process_runtime', 'scene_actions', 'settlement_runtime', 'r9_runtime'),
               'app': ('server', 'process_bridge', 'local_presentation', 'engine_paths', 'catalog_paths'),
               'catalog': ('response_depot_compatibility', 'solo_evaluation', 'scripted_responses')}
    for owner, names in imports.items():
        for name in names:
            module = importlib.import_module(name)
            if not Path(module.__file__).resolve().is_relative_to(roots[owner]):
                raise ValueError('Another checkout supplied '+name+'; use a fresh process')
            MODULES[name] = module
    EVIDENCE['imported_modules'] = {name: str(Path(module.__file__).resolve()) for name, module in MODULES.items()}
    fixture = MODULES['response_depot_compatibility']
    EVIDENCE['fixture'] = fixture.validate_fixture()
    EVIDENCE['original_fixture_consumers'] = fixture.load_fixture()['consumers']
    EVIDENCE['fixture_identity_preserved'] = hashlib.sha256((catalog/'IRGS_Catalog'/fixture.FIXTURE/'manifest.json').read_bytes()).hexdigest()
    EVIDENCE['qualification_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class ComponentInteractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='irgs-engine-component-')
        self.addCleanup(self.temp.cleanup)
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.dispatch = self.stack.enter_context(patch('solo_provider.CapabilityBroker.dispatch',
            side_effect=AssertionError('No inference in component qualification')))
        self.transport = self.stack.enter_context(patch('openai_proposals.OpenAIProposalTransport.__call__',
            side_effect=AssertionError('No provider transport in component qualification')))
        self.stack.enter_context(patch('http.server.BaseHTTPRequestHandler.log_message', return_value=None))
        self.server = MODULES['server']
        self.store = self.server.Store(self.temp.name)
        source = MODULES['response_depot_compatibility']
        self.manifest = source.load_fixture()
        self.inputs = {name: source.export_actor_input(name) for name in ('rise', 'quay')}
        self.oracle = source.load_evaluator_data()  # Evaluator-only; never sent as actor input.
        selected = MODULES['solo_evaluation'].load_evaluator_data()['setup']['choices']
        import rise_campaigns
        rise = rise_campaigns.create(self.store, {'name': 'Synthetic Engine compatibility Rise',
            'choices': selected, 'review_digest': MODULES['settlement_setup'].preview(selected)['review_digest'],
            'request_id': 'engine-compat-rise-create'})
        selection = dict(self.manifest['contexts']['quay']['selection'])
        opening = selection.pop('opening_id')
        entry = MODULES['historical_campaigns'].historical_entry(selection['entry_id'])
        selection['snapshot_sha256'] = entry['snapshot_sha256']
        reviewed = MODULES['starting_selection'].starting_options(**selection)
        quay = self.store.create('Synthetic Engine compatibility quay', **selection,
            selection_digest=reviewed['selection_digest'], request_id='engine-compat-quay-create', creator=False,
            character={'kind': 'new', 'name': 'Synthetic compatibility courier', 'species': 'human',
                       'background': '', 'opening_id': opening})
        self.keys = {'rise': rise['id'], 'quay': quay['id']}
        self.actors = {'rise': 'founder', 'quay': self.store.read(quay['id'])['state']['player_actor_ids'][0]}
        for key in self.keys.values():
            record = self.store.read(key)
            record['state'].setdefault('site_conditions', {})['evaluator_only'] = {'marker': self.oracle['hidden_marker']}
            self.store.write(record)
        self.host = self.server.make_server(0, self.store.folder, solo_configuration=None)
        self.thread = threading.Thread(target=self.host.serve_forever, daemon=True)
        self.thread.start(); self.addCleanup(self.stop)
        self.url = 'http://127.0.0.1:'+str(self.host.server_port)
        self.token = self.http('/api/campaigns')[1]['token']

    def tearDown(self):
        self.dispatch.assert_not_called(); self.transport.assert_not_called()

    def stop(self):
        self.host.shutdown(); self.host.server_close(); self.thread.join()

    def http(self, path, body=None):
        headers = {'X-IRGS-Token': getattr(self, 'token', '')}
        if body is not None: headers['Content-Type'] = 'application/json'
        request = Request(self.url+path, data=None if body is None else json.dumps(body).encode(), headers=headers)
        try:
            with urlopen(request, timeout=15) as response: return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def view(self, context):
        code, result = self.http('/api/playthrough/'+self.keys[context]+'?actor_id='+self.actors[context])
        self.assertEqual(code, 200, result); self.safe(result)
        return result

    def safe(self, result):
        serialized = json.dumps(result)
        for forbidden in (self.oracle['hidden_marker'], 'state_digest', 'params_digest', 'PRIVATE_COMPONENT_FAILURE'):
            self.assertNotIn(forbidden, serialized)

    def action(self, context, case):
        view = self.view(context)
        body = {'id': self.keys[context], 'actor': self.actors[context], 'revision': view['revision'],
                'request_id': case['request_id']}
        if context == 'rise':
            body['action'] = case['action_id']; endpoint = '/api/rise/action'
        else:
            option = next(row for row in view['supported_actions'] if row.get('action_id') == case['action_id'])
            body.update(kind='scene_action', action_id=case['action_id'], text=option['text']); endpoint = '/api/action'
        code, result = self.http(endpoint, body)
        self.assertEqual(code, 200, result); self.safe(result)
        return body, result

    def test_catalog_nine_cases_execute_real_http_outcomes_and_conserved_final_state(self):
        cases = []
        for context in ('rise', 'quay'):
            for case in self.inputs[context]['cases']:
                body, result = self.action(context, case)
                expected = self.oracle['cases'][case['case_id']]
                self.assertEqual(result['status'], expected['status'])
                elapsed = result['elapsed_time']['seconds' if context == 'rise' else 'duration_seconds']
                self.assertEqual(elapsed, expected['duration_seconds'])
                self.assertEqual(self.store.read(self.keys[context])['state']['elapsed_time']['seconds'], expected['total_seconds'])
                presentation = result['presentation']
                self.assertTrue(presentation['text'].startswith(result['outcome']['summary']))
                self.assertEqual(presentation['catalog_library']['id'], 'irgs-response-depot-v1')
                self.assertEqual(presentation['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
                before = self.store.path(self.keys[context]).read_bytes()
                code, replay = self.http('/api/action-result/'+self.keys[context]+'/'+body['request_id']+'?actor_id='+body['actor'])
                self.assertEqual(code, 200); self.assertEqual(replay, result)
                self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)
                cases.append({'case_id': case['case_id'], 'status': result['status'], 'elapsed_seconds': elapsed})
        quay = self.store.read(self.keys['quay'])['state']
        self.assertEqual(quay['stocks'][self.actors['quay']]['sealed_dispatch'], self.oracle['quay_final']['dispatch_with_actor'])
        destinations = sum(stock.get('sealed_dispatch', 0) for key, stock in quay['stocks'].items() if key != self.actors['quay'])
        self.assertEqual(destinations, self.oracle['quay_final']['dispatch_in_tray'])
        EVIDENCE['actual_catalog_cases'] = cases

    def test_catalog_and_engine_runtime_intake_the_same_exact_depot_and_drafts_submit_nothing(self):
        formatter, library = MODULES['local_presentation']._catalog()
        engine_bytes = MODULES['response_depot'].DEPOT.read_bytes()
        catalog_bytes = (Path(SELECTED['catalog']['root'])/'IRGS_Catalog/responses/depot_v1/library.json').read_bytes()
        self.assertEqual(engine_bytes, catalog_bytes)
        self.assertEqual(formatter.validate_library(library)['variants'], 1000)
        for context in ('rise', 'quay'):
            before = self.store.path(self.keys[context]).read_bytes()
            view = self.view(context)
            self.assertEqual(view['local_responses']['catalog_library']['id'], 'irgs-response-depot-v1')
            self.assertEqual({d['source'] for d in view['local_responses']['drafts']}, {'engine', 'catalog'})
            for draft in view['local_responses']['drafts']:
                self.assertFalse(draft['automatic_execution']); self.assertTrue(draft['requires_explicit_submission'])
            self.assertEqual(self.store.path(self.keys[context]).read_bytes(), before)
        EVIDENCE['depot_sha256'] = hashlib.sha256(engine_bytes).hexdigest()

    def start_phase(self, context):
        if context == 'rise':
            self.action(context, {'action_id': 'walk_clearing', 'request_id': 'phase-fixture-walk'})
            self.action(context, {'action_id': 'found', 'request_id': 'phase-fixture-found'})
        record = self.store.read(self.keys[context]); actor = self.actors[context]
        world = MODULES['core_world'].CoreWorld(state=record['state'])
        service = MODULES['process_bridge'].ProcessService(self.store)
        scope = service.scope(record)
        phases = MODULES['phase_contract']
        view = phases.actor_view(world, actor, branch_id=scope.branch_id, restore_id=scope.restore_id)
        kind = 'work' if context == 'rise' else 'observation'
        option = next(row for row in view['start_options'] if row['kind'] == kind
                      and row['action_id'] == ('build' if context == 'rise' else 'look-quay'))
        request = phases.prepare_start(world, actor=actor, capability_id=option['capability_id'],
            process_id='engine-started', phase_id='engine-fixture-start', intention='Explicit synthetic '+kind,
            source_ref='engine-component-qualified-fixture', branch_id=scope.branch_id, restore_id=scope.restore_id)

        def persist(expected, candidate, received):
            current = self.store.read(record['id'])
            self.assertEqual(service.scope(current), expected)
            candidate_world = MODULES['core_world'].CoreWorld.load(candidate)
            public = {'request_id': 'engine-fixture-start', 'campaign_id': record['id'], 'actor': actor,
                'kind': 'process_phase', 'status': 'completed_successfully', 'revision': current['revision']+1,
                'outcome': {'summary': received['summary']}, 'receipt': {'event_id': 'process:'+request.phase_id},
                'process': {key: received[key] for key in MODULES['process_bridge'].PUBLIC_PHASE},
                'elapsed_time': {'axis': candidate_world.s['elapsed_time']['axis'],
                    'duration_seconds': received['elapsed_seconds'], 'total_seconds': received['elapsed_total']}}
            public['presentation'] = MODULES['local_presentation'].receipt_presentation(candidate_world, public,
                engine_presentation=received['presentation'])
            current.setdefault('gameplay_requests', {})['engine-fixture-start'] = {
                'campaign_id': record['id'], 'actor': actor, 'kind': 'process_phase', 'result': public}
            self.store.commit(current, candidate_world, public)
        return phases.execute(world, request, current_scope=scope, persist=persist, explicitly_accepted=True)

    def phase(self, context, command, details=None):
        view = self.view(context); key = self.keys[context]
        body = {'id': key, 'actor': self.actors[context], 'revision': view['revision'],
            'view_token': view['process_control']['view_token'], 'request_id': 'phase-'+str(view['revision']),
            'process_id': 'engine-started', 'command': command, 'details': details or {},
            'intention': '  Exact '+command+' intention.\nDo only this.  '}
        before = self.store.path(key).read_bytes()
        code, prepared = self.http('/api/process/prepare', body); self.assertEqual(code, 200, prepared)
        self.assertEqual(self.store.path(key).read_bytes(), before)
        accepted = {'id': key, 'actor': body['actor'], 'request_id': body['request_id'], 'explicitly_accepted': True}
        code, result = self.http('/api/process/execute', accepted); self.assertEqual(code, 200, result)
        self.assertEqual(result['process']['phase_intention'], body['intention'])
        self.assertEqual(result['process']['phase_id'], prepared['phase_id']); self.safe(result)
        after = self.store.path(key).read_bytes()
        code, replay = self.http('/api/process/execute', accepted)
        self.assertEqual(code, 200); self.assertEqual(replay, result)
        self.assertEqual(self.store.path(key).read_bytes(), after)
        return result

    def test_new_engine_phase_contract_and_existing_app_commands_interoperate_in_both_contexts(self):
        contexts = []
        for context in ('rise', 'quay'):
            start = self.start_phase(context); view = self.view(context)
            received = view['process_control']['processes'][0]
            self.assertEqual(received['received']['phase_id'], start['phase_id'])
            self.assertEqual(set(received['commands']), {c['command'] for c in start['supported_commands']})
            self.phase(context, 'pause'); self.phase(context, 'resume')
            span = 3600 if context == 'rise' else start['remaining_seconds']
            result = None
            for _ in range(5):
                result = self.phase(context, 'advance', {'seconds': span})
                if result['process']['terminal']: break
            self.assertEqual(result['process']['status'], 'completed')
            self.assertEqual(result['process']['worked_seconds'], start['remaining_seconds'])
            if context == 'rise':
                self.assertEqual(self.store.read(self.keys[context])['state']['stocks']['founder-home']['timber'], 3)
            code, original = self.http('/api/action-result/'+self.keys[context]+'/engine-fixture-start?actor_id='+self.actors[context])
            self.assertEqual(code, 200); self.assertEqual(original['process']['worked_seconds'], 0)
            contexts.append({'context': context, 'kind': start['kind'], 'worked_seconds': result['process']['worked_seconds'],
                'pause_resume': True, 'replay_once': True, 'new_engine_start_existing_app_continuation': True})
        EVIDENCE['phase_interaction'] = contexts

    def test_app_start_discovery_matches_actual_engine_capabilities_without_mutation(self):
        context = 'quay'; record = self.store.read(self.keys[context])
        world = MODULES['core_world'].CoreWorld(state=record['state']); before = world.save()
        discovered = MODULES['phase_contract'].actor_view(world, self.actors[context], branch_id=record['id'], restore_id='fixture-review')
        self.assertTrue(discovered['start_options'])
        public = self.view(context)['process_control']
        self.assertEqual(public['start_options'], discovered['start_options'])
        self.assertEqual(public['start_available'], bool(discovered['start_options']))
        self.assertEqual(world.save(), before)
        EVIDENCE['app_start_adapter_available'] = True

    def test_missing_text_keeps_real_http_outcome_without_paid_fallback(self):
        with patch('offline_responses._library', side_effect=OSError('PRIVATE_COMPONENT_FAILURE')), \
             patch('local_presentation._catalog', side_effect=OSError('PRIVATE_COMPONENT_FAILURE')):
            _, result = self.action('quay', self.inputs['quay']['cases'][0])
            self.assertTrue(result['presentation']['text'].startswith(result['outcome']['summary']))
            self.assertEqual(result['presentation']['mode'], 'literal_receipt')
            self.assertEqual(result['presentation']['render_usage'], {'provider_calls': 0, 'model_tokens': 0})
            self.safe(result)


def qualify(app, catalog):
    initialize(app, catalog)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ComponentInteractionTests)
    names = [case.id() for case in suite]
    output = io.StringIO(); result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError(output.getvalue())
    return {'schema_version': 1, 'status': 'PASS_EXPLICIT_COMPONENT_SOURCES_WITH_LIMITS',
        'target_iteration': 'IRGS 3.4.1 development', 'sources': SELECTED,
        'selection': 'Explicit latest-head overrides; committed App pins and original Catalog consumer identities preserved',
        'tests_run': result.testsRun, 'passed': result.testsRun, 'skipped': len(result.skipped), 'test_ids': names,
        'evidence': EVIDENCE, 'provider_calls': 0, 'model_tokens': 0, 'user_saves_used': False,
        'source_sha256': {str(Path(module.__file__).resolve().relative_to(Path(SELECTED[owner]['root']))):
            hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
            for owner in ('engine', 'app', 'catalog') for module in MODULES.values()
            if Path(module.__file__).resolve().is_relative_to(Path(SELECTED[owner]['root']))},
        'remaining': ['Coordinator exact-set joined/package qualification',
            'Communication/offer participant and received-source contract remains the next Engine bounded task']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-root', type=Path, required=True)
    parser.add_argument('--catalog-root', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = qualify(args.app_root, args.catalog_root)
    if args.output: args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'tests_run', 'passed', 'skipped')}))
