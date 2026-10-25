"""Run pinned Catalog R00 cases through the actual Engine proposal/Core bridge.

Offline only. Catalog exports remain physically separate from evaluator data;
no live inference, App host, model-quality or joined qualification is claimed.
"""
import argparse
from dataclasses import replace
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'IRGS_3_3/runtime'))
from core_world import CoreWorld
from irgs_reference import canon
from settlement_runtime import location
from settlement_setup import initialize, preview
from solo_actions import accept_proposal, prepare_request
from solo_provider import (AttemptLedger, CapabilityBroker, CapabilityUnavailable, RISE_OPERATION,
                           SpecialistRegistry, WorldScope)
from test_solo_provider import AtomicTestHost, FakeTransport, route

CATALOG_COMMIT = '2e4f389882df0807fc8064c1a0b533aaa3b1bcd3'
MANIFEST_SHA256 = '2d30e863c4f769f0e2039469807ca0c6eeef3f30edd17d96778cebcba65bdbe5'
LOADER_SHA256 = '444fb338b7ade0e78fbd2f014c15bd90546cee4e203966ed6284ba73cfdecc97'


def qualify(catalog_root):
    catalog_root = Path(catalog_root).resolve()
    fixture = catalog_root / 'evaluation/solo_r00_v1'
    for path, expected in ((fixture / 'manifest.json', MANIFEST_SHA256),
                           (catalog_root / 'solo_evaluation.py', LOADER_SHA256)):
        assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest() == expected
    spec = importlib.util.spec_from_file_location('qualified_solo_catalog', catalog_root / 'solo_evaluation.py')
    catalog = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(catalog)
    validated = catalog.validate_fixture(fixture)
    evaluator = catalog.load_evaluator_data(fixture)
    # This separate evaluator namespace never enters make_request/transport input.
    oracle, setup = evaluator['oracle'], evaluator['setup']
    choices = setup['choices']
    world = initialize(choices, preview(choices)['review_digest'], 'catalog-solo-provider-qualification')
    seen, records, model_inputs = {}, [], []
    with tempfile.TemporaryDirectory(prefix='irgs-solo-provider-') as temporary:
        host = AtomicTestHost(temporary, world)
        ledger_path = Path(temporary) / 'inference.sqlite'
        ledger = AttemptLedger(ledger_path, budget_units=100, max_inflight=1)
        classification = 'synthetic-evaluation-actor-input-only'
        selected_route = route(operations=(RISE_OPERATION,), classifications=(classification,))
        registry = SpecialistRegistry([selected_route])

        def broker():
            return CapabilityBroker(registry, ledger, enabled=True,
                scope_reader=lambda request: WorldScope(world.s['campaign_id'], 'branch-1',
                                                        host.restore_id, world.checksum()))

        def make_request(case, actor_doc, *, include_export=True):
            request = prepare_request(world, request_id=case['request_id'], actor_id=actor_doc['actor_id'],
                intention=actor_doc['user_intent'], branch_id='branch-1', restore_id='restore-1',
                allowed_routes=('offline',), classification=classification,
                policy_ref=selected_route.policy_ref, config_version=selected_route.config_version,
                deadline=time.time()+30)
            if include_export:
                # The trusted, hash-checked actor export is an evaluation input;
                # it cannot initialize, authorize or overwrite any Core fact.
                context = json.loads(request.context_json)
                context['catalog_actor_export'] = actor_doc
                request = replace(request, context_json=canon(context),
                    source_refs=(*request.source_refs, actor_doc['source_ref'], actor_doc['intent_ref']))
            return request

        def propose(request, action):
            fake = FakeTransport(action)
            result = broker().dispatch(request, 'offline', fake)
            model_inputs.extend(fake.inputs)
            return result

        def accept(request, proposal, intention=None):
            return accept_proposal(world, ledger, request_id=request.request_id,
                proposal_digest=proposal.proposal_digest, actor_id='founder',
                intention=request.intention if intention is None else intention,
                branch_id='branch-1', restore_id='restore-1', explicitly_accepted=True,
                persist=host.persist, clock=time.time)

        def expect_error(code, fn):
            before = world.save()
            try:
                fn()
            except CapabilityUnavailable as error:
                assert error.code == code, (error.code, code)
            else:
                raise AssertionError('expected ' + code)
            assert world.save() == before

        stale_case = next(case for case in oracle['cases'] if case['kind'] == 'stale')
        # Prepare at revision zero from actually received runtime records. The
        # later actor export describes revision one and must not travel backward.
        stale_doc = catalog.export_actor_input(stale_case['case_id'], fixture)
        stale_request = make_request(stale_case, stale_doc, include_export=False)
        stale_proposal = propose(stale_request, stale_case['action_id']).proposal
        assert stale_proposal is not None

        for case in oracle['cases']:
            actor_doc = catalog.export_actor_input(case['case_id'], fixture)
            assert not any(marker in canon(actor_doc) for marker in oracle['hidden_markers'])
            kind, outcome = case['kind'], None
            if kind == 'stale':
                expect_error('stale_state', lambda: accept(stale_request, stale_proposal))
                assert broker().dispatch(stale_request, 'offline', FakeTransport()).code == 'stale_scope_or_state'
                outcome = 'stale_state'
            elif kind == 'replay':
                original_request, original_proposal, original_result = seen[case['replay_of']]
                # Retry prose is a receipt lookup, not permission to rewrite the
                # previously accepted intention. An altered resubmission rejects.
                expect_error('acceptance_changed',
                             lambda: accept(original_request, original_proposal, actor_doc['user_intent']))
                before = world.save()
                assert accept(original_request, original_proposal) == original_result
                assert world.save() == before
                outcome = 'original_receipt'
            else:
                request = make_request(case, actor_doc)
                result = propose(request, case['action_id'])
                if kind in ('unsupported', 'changed_replay'):
                    expected = 'unsupported_action' if kind == 'unsupported' else 'request_identity_conflict'
                    assert result.code == expected, result
                    outcome = expected
                elif kind == 'denied':
                    assert result.proposal is not None
                    expect_error('action_unavailable', lambda: accept(request, result.proposal))
                    certificate = json.loads(ledger.lookup(request.request_id)['dependencies'])
                    assert certificate['status'] == 'rejected_no_effects' and not certificate['writes']
                    outcome = 'rejected_no_effects'
                else:
                    assert result.proposal is not None
                    public = accept(request, result.proposal)
                    seen[case['case_id']] = (request, result.proposal, public)
                    outcome = 'committed'
                    world = host.load()
                    ledger = AttemptLedger(ledger_path, budget_units=100, max_inflight=1)
            project = world.s['projects'].get('shelter', {})
            actual = {'revision': host.writes, 'clock': world.s['clock'],
                'elapsed_seconds': world.s['elapsed_time']['seconds'], 'location': location(world.s, 'founder'),
                'camp_established': 'camp' in world.s['settlements'],
                'founder_timber': world.s['stocks']['founder-home']['timber'],
                'npc_timber': world.s['stocks']['oren-home']['timber'],
                'shelter_status': project.get('status', 'absent'), 'shelter_worked_seconds': project.get('worked', 0)}
            assert actual == case['expected'], (case['case_id'], actual, case['expected'])
            records.append({'case_id': case['case_id'], 'kind': kind, 'result': outcome, 'status': 'PASS'})
        final = oracle['final_state']
        assert world.s['stocks']['founder-home'] == final['founder_inventory']
        assert world.s['stocks']['oren-home'] == final['npc_inventory']
        consumption = {material: sum(f['quantity'] for f in world.s['material_flows'].values()
                                    if f['material']==material) for material in world.s['opening_stock']}
        assert consumption == final['material_consumption']
        assert sum(a['places'] for a in world.s['assets'].values()
                   if a['household']=='founder-home') == final['shelter_places']
        for material, opening in world.s['opening_stock'].items():
            assert sum(stock.get(material,0) for stock in world.s['stocks'].values()) == opening-consumption[material]
        serialized_inputs = canon(model_inputs)
        assert not any(marker in serialized_inputs for marker in oracle['hidden_markers'])
        for forbidden in ('evaluator_only', 'hidden_facts', 'opening_npc_inventory', 'npc_inventory',
                          'settlement_model', 'material_flows', 'projects', 'journal', 'state_digest'):
            assert '"'+forbidden+'"' not in serialized_inputs
        return {'schema_version': 1, 'status': 'PASS_OFFLINE_ENGINE_CATALOG_WITH_LIMITS',
            'target_iteration': 'IRGS 3.4.0 — in development', 'catalog_commit': CATALOG_COMMIT,
            'engine_sources_sha256': {name: hashlib.sha256((ROOT/'IRGS_3_3/runtime'/name).read_bytes()).hexdigest()
                for name in ('core_world.py', 'settlement_runtime.py', 'scene_actions.py',
                             'solo_provider.py', 'solo_actions.py', 'r9_runtime.py', 'r8_dependencies.py',
                             'offline_responses.py', 'routine_format.py', 'process_runtime.py',
                             'communication_runtime.py', 'runtime_contracts.py')},
            'engine_response_data_sha256': {name: hashlib.sha256((ROOT/'IRGS_3_3/data/responses'/name).read_bytes()).hexdigest()
                for name in ('engine_routine_v1.json', 'PROVENANCE.json')},
            'manifest_sha256': MANIFEST_SHA256, 'loader_sha256': LOADER_SHA256,
            'fixture': validated, 'operation': RISE_OPERATION, 'cases': records,
            'successful_actions': host.writes, 'elapsed_seconds': world.s['elapsed_time']['seconds'],
            'material_consumption': consumption, 'shelter_places': final['shelter_places'],
            'actor_oracle_separation': True, 'temporary_save_reload_after_each_commit': True,
            'transport': 'synthetic offline transport', 'live_calls': 0, 'skipped': 0,
            'limits': ['Temporary synthetic host CAS only; actual App integration unqualified',
                       'Actor export is evaluation content, not initialization or world authority',
                       'No live model, semantic/human quality or exact joined set qualification']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog-root', type=Path, required=True, help='Pinned IRGS_Catalog directory')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = qualify(args.catalog_root)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(result, ensure_ascii=False))
