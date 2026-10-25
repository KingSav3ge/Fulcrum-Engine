"""Host-safe phase DTOs over selected actual Core observation and work."""
from dataclasses import replace
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core_world import CoreWorld
import phase_contract as api
from process_runtime import ProcessRequest
from runtime_contracts import WorldScope
from settlement_runtime import execute as settlement_action
from settlement_setup import initialize, preview
from test_scene_actions import fixture as scene_fixture
from test_settlement import choices
from test_solo_provider import AtomicTestHost


class PhaseContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.world = scene_fixture()
        self.actor = 'pc'
        self.host = AtomicTestHost(self.temp.name, self.world)
        self.counter = 0
        for target in ('solo_provider.CapabilityBroker.dispatch',
                       'openai_proposals.OpenAIProposalTransport.__call__', 'socket.socket.connect'):
            blocker = patch(target, side_effect=AssertionError('No provider/network in phase API'))
            blocker.start(); self.addCleanup(blocker.stop)

    def rise(self):
        c = choices(); c['permission'] = 'held'
        self.world = initialize(c, preview(c)['review_digest'], 'phase-contract-fixture')
        self.actor = 'founder'
        settlement_action(self.world, 'setup-walk', self.actor, 'walk_clearing', 'explicit synthetic setup')
        settlement_action(self.world, 'setup-camp', self.actor, 'found', 'explicit synthetic setup')
        self.host.install(self.world)

    def scope(self):
        return WorldScope(self.world.s['campaign_id'], 'branch-1', self.host.restore_id, self.world.checksum())

    def view(self):
        return api.actor_view(self.world, self.actor, branch_id='branch-1', restore_id=self.host.restore_id)

    def start_request(self, *, action=None, process_id='parent', phase_id=None):
        self.counter += 1
        action = action or ('build' if self.actor == 'founder' else 'look-quay')
        option = next(row for row in self.view()['start_options'] if row['action_id'] == action)
        return api.prepare_start(self.world, actor=self.actor, capability_id=option['capability_id'],
            process_id=process_id, phase_id=phase_id or 'phase-'+str(self.counter), intention='Exact selected '+action,
            source_ref='explicit synthetic phase contract', branch_id='branch-1', restore_id=self.host.restore_id)

    def command_request(self, command, details=None, *, process_id='parent'):
        self.counter += 1
        return api.prepare_command(self.world, actor=self.actor, process_id=process_id,
            phase_id='phase-'+str(self.counter), command=command, details=details or {},
            intention='Exact selected '+command, source_ref='explicit synthetic phase contract',
            branch_id='branch-1', restore_id=self.host.restore_id)

    def submit(self, request, **overrides):
        args = dict(current_scope=self.scope(), persist=self.host.persist, explicitly_accepted=True)
        args.update(overrides)
        return api.execute(self.world, request, **args)

    def command(self, command, details=None):
        return self.submit(self.command_request(command, details))

    def test_both_selected_contexts_expose_attemptable_starts_without_effects(self):
        for context in ('observation', 'work'):
            if context == 'work': self.rise()
            before = self.world.save(); view = self.view()
            self.assertEqual({r['kind'] for r in view['start_options']}, {context})
            for row in view['start_options']:
                self.assertTrue(row['source_refs'])
                self.assertTrue(row['requires_explicit_submission'])
                self.assertEqual(row['availability'], 'attemptable')
            self.start_request()
            self.assertEqual(self.world.save(), before)

    def test_observation_completes_once_with_actual_elapsed_and_received_knowledge(self):
        started = self.submit(self.start_request())
        self.assertFalse(started['terminal'])
        partial = self.command('advance', {'seconds': 2})
        self.assertEqual(partial['worked_seconds'], 2)
        self.assertNotIn('passage and the closed gate', partial['presentation']['text'])
        final = self.command('advance', {'seconds': 1})
        self.assertEqual(final['status'], 'completed')
        self.assertTrue(final['terminal'])
        self.assertEqual(final['elapsed_total'], 3)
        self.assertIn('You see the passage and the closed gate.', final['presentation']['text'])
        self.assertEqual([r['command'] for r in final['supported_commands']], ['inspect'])

    def test_work_uses_existing_project_reservations_and_conserved_inputs(self):
        self.rise(); started = self.submit(self.start_request())
        self.assertEqual(started['worked_seconds'], 0)
        self.assertEqual(self.world.s['stocks']['founder-home']['timber'], 6)
        self.assertEqual(self.world.s['projects']['shelter']['worker'], 'founder')
        boundary = self.command('advance', {'seconds': 3600})
        self.assertEqual(boundary['status'], 'active')
        self.assertGreater(boundary['worked_seconds'], 0)
        self.assertLess(boundary['worked_seconds'], 3600)  # Actual selected provision boundary.
        self.assertEqual(boundary['worked_seconds'], boundary['elapsed_seconds'])
        final = boundary
        for _ in range(4):
            if final['terminal']: break
            final = self.command('advance', {'seconds': 3600})
        self.assertEqual(final['status'], 'completed')
        self.assertEqual(final['worked_seconds'], 3600)
        self.assertEqual(self.world.s['stocks']['founder-home']['timber'], 3)
        self.assertEqual(len([k for k in self.world.s['material_flows'] if k == 'project:shelter']), 1)

    def test_safe_phase_and_shared_actor_views_omit_private_records_and_certificates(self):
        from shared_runtime import actor_view
        self.submit(self.start_request())
        before = self.world.save()
        view = actor_view(self.world, self.actor, branch_id='branch-1', restore_id=self.host.restore_id)
        self.assertEqual(view['continuations'], self.view())
        raw = json.dumps(view['continuations'])
        for forbidden in ('params_digest', 'rule_digest', 'dependencies', 'certificate', 'state_digest',
                          '"stocks"', '"projects"', '"journal"', '"task"'):
            self.assertNotIn(forbidden, raw)
        self.assertEqual(self.world.save(), before)
        self.assertEqual(view['continuations']['processes'][0]['status_basis'], 'received_phase')

    def test_original_received_phase_and_snapshot_are_bound_to_actor_branch_and_restore(self):
        result = self.submit(self.start_request())
        first = self.view()
        other = api.actor_view(self.world, self.actor, branch_id='another', restore_id=self.host.restore_id)
        self.assertNotEqual(first['snapshot_id'], other['snapshot_id'])
        for reader in (lambda: api.actor_view(self.world, 'absent', branch_id='b', restore_id='r'),
            lambda: api.received_phase(self.world, 'absent', result['phase_id'], branch_id='b', restore_id='r'),
            lambda: api.status(self.world, self.actor, 'absent', branch_id='b', restore_id='r')):
            with self.assertRaises(api.PhaseUnavailable): reader()

    def test_persistence_receives_the_same_filtered_public_result_as_acknowledgment(self):
        result = self.submit(self.start_request())
        stored = json.loads(self.host.path.read_text())['receipt']
        self.assertEqual(stored, result)
        self.assertNotIn('params_digest', stored)
        self.assertIn('params_digest', self.world.s['process_phase_receipts'][result['phase_id']])

    def test_explicit_acceptance_and_persistence_are_required_before_effects(self):
        request = self.start_request(); before = self.world.save()
        for overrides in ({'explicitly_accepted': False}, {'explicitly_accepted': 1}, {'persist': None}):
            with self.assertRaises(api.PhaseUnavailable): self.submit(request, **overrides)
        self.assertEqual(self.world.save(), before)

    def test_unsupported_contexts_and_generic_tags_do_not_create_phase_capabilities(self):
        self.world.s.pop('scene_rules'); self.host.install(self.world)
        self.assertEqual(self.view()['start_options'], [])
        with self.assertRaises(api.PhaseUnavailable):
            api.prepare_start(self.world, actor=self.actor, capability_id='observe', process_id='p', phase_id='x',
                intention='Observe.', source_ref='explicit', branch_id='b', restore_id='r')


if __name__ == '__main__': unittest.main()
