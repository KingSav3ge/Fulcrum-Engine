"""Actual new-world historical starts and existing Core observation effects."""
from dataclasses import replace
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from campaign_library import initial_campaign
from core_world import CoreWorld
from historical_campaigns import historical_entry
from runtime_contracts import AcceptedIntent, WorldScope
from shared_runtime import capabilities, execute_intent, prepare_intent
from solo_provider import CapabilityUnavailable
from starting_selection import initialize_player, options_for_world
import start_readiness as api
from test_solo_provider import AtomicTestHost

HENRY = 'HYW-HENRY-V'
JOHN = 'HYW-JOHN-BEDFORD'
OPENING = 'henry-1415-embarkation-v1'


def raw(entry='hyw-1415', campaign='synthetic-start-readiness'):
    preview = historical_entry(entry)
    return initial_campaign('military', campaign, scenario_id='hundred-years-war',
        entry_id=entry, snapshot_sha256=preview['snapshot_sha256'])


class StartReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.world = raw(); self.counter = 0
        for target in ('solo_provider.CapabilityBroker.dispatch',
                       'openai_proposals.OpenAIProposalTransport.__call__', 'socket.socket.connect'):
            guard = patch(target, side_effect=AssertionError('No network/provider in start qualification'))
            guard.start(); self.addCleanup(guard.stop)

    def create(self, character=None):
        self.character = character or {'kind':'existing','actor_id':HENRY,'opening_id':OPENING}
        options = options_for_world(self.world)
        self.world = initialize_player(self.world, self.character, selection_digest=options['selection_digest'],
                                       request_ref='explicit reviewed synthetic start')
        self.actor = self.world.s['player_actor_ids'][0]
        self.host = AtomicTestHost(self.temp.name, self.world)

    def view(self, actor=None):
        return api.actor_view(self.world, actor or self.actor, branch_id='branch-1', restore_id=self.host.restore_id)

    def scope(self):
        return WorldScope(self.world.s['campaign_id'],'branch-1',self.host.restore_id,self.world.checksum())

    def request(self, text='I observe the embarkation setting without issuing an order.'):
        self.counter += 1
        cap = next(c for c in capabilities(self.world,self.actor) if c.operation_id == 'execute_player_scene_action')
        return prepare_intent(self.world, request_id='observation-'+str(self.counter), actor_id=self.actor,
            intention=text, capability_id=cap.capability_id, branch_id='branch-1', restore_id=self.host.restore_id)

    def submit(self, request, **overrides):
        args = dict(current_scope=self.scope(),persist=self.host.persist,explicitly_accepted=True)
        args.update(overrides)
        return execute_intent(self.world,request,**args)

    def test_john_is_eligible_but_his_playable_mode_stays_held_without_personal_context(self):
        before = self.world.save()
        review = api.review_start(self.world, {'kind':'existing','actor_id':JOHN})
        self.assertTrue(review['character_eligible'])
        self.assertEqual(review['reference_status'],'verified_dated_reference')
        self.assertEqual(review['selected_mode']['status'],'declaration_only')
        self.assertEqual(review['playable_context']['status'],'held')
        self.assertEqual(review['presentation_opening']['status'],'presentation_only')
        self.assertFalse(review['presentation_opening']['grants_capabilities'])
        self.assertEqual(self.world.save(),before)

    def test_existing_henry_requires_a_separate_explicit_sourced_opening(self):
        default = api.review_start(self.world, {'kind':'existing','actor_id':HENRY})
        selected = api.review_start(self.world, {'kind':'existing','actor_id':HENRY,'opening_id':OPENING})
        self.assertEqual(default['selected_mode']['status'],'declaration_only')
        self.assertEqual(selected['selected_mode']['status'],'supported_slice')
        options = options_for_world(self.world)
        self.assertEqual(options['existing_character_openings'][0]['actor_id'],HENRY)
        self.assertEqual(options['existing_character_openings'][0]['review']['location_precision'],'embarkation_region_only')
        self.assertNotIn(OPENING,[r['id'] for r in options['playable_openings']])

    def test_new_authored_and_declaration_modes_are_distinct_from_existing_person(self):
        character = {'kind':'new','name':'Synthetic courier','species':'Human'}
        self.assertEqual(api.review_start(self.world,character)['selected_mode']['status'],'declaration_only')
        character['opening_id'] = 'quay-delivery-v1'
        self.assertEqual(api.review_start(self.world,character)['selected_mode']['status'],'supported_slice')
        character['species'] = 'elf'
        self.assertEqual(api.review_start(self.world,character)['selected_mode']['status'],'held')
        character.update(kind='existing',actor_id=JOHN)
        self.assertEqual(api.review_start(self.world,character)['selected_mode']['status'],'held')

    def test_precreation_contract_does_not_probe_hidden_resources_or_choose_a_winning_menu(self):
        character = {'kind':'existing','actor_id':HENRY,'opening_id':OPENING}
        before = api.review_start(self.world,character)
        self.world.s['actors'][JOHN]['current']['location'] = 'PRIVATE_SITE'
        self.world.s['private_fixture'] = {'stocks':123,'authority':'PRIVATE','weather':'PRIVATE'}
        self.assertEqual(api.review_start(self.world,character),before)
        self.assertNotIn('PRIVATE',json.dumps(before))

    def test_sourced_start_initializes_only_reviewed_personal_context_and_calendar(self):
        self.create(); current = self.world.s['actors'][HENRY]['current']
        self.assertEqual(set(current),{'location'})
        self.assertEqual(current['location']['value'],'portchester-solent-embarkation')
        self.assertFalse(self.world.s['stocks']); self.assertFalse(self.world.s['orders'])
        self.assertFalse(self.world.s['starting_control']['institutional_mandate_granted'])
        self.assertNotIn('authored_opening',self.world.s['gameplay_started'])
        known = self.world.s['knowledge'][HENRY]
        self.assertEqual(set(known),{'setup:scene-map','setup:scene-location','setup:civil-date'})
        self.assertFalse(self.world.s['knowledge'].get(JOHN))
        self.assertNotIn('Harfleur',json.dumps(self.view()['received_context']))

    def test_first_explicit_core_attempt_delivers_observation_and_actual_elapsed_without_free_stock(self):
        self.create(); before = copy.deepcopy(self.world.s['campaign_time'])
        known = len(self.world.s['knowledge'][HENRY]); request = self.request()
        result = self.submit(request)
        self.assertEqual(result['status'],'completed_successfully')
        self.assertEqual(result['intention'],request.intention)
        self.assertIn('Shipping is gathered',result['receipt']['exact_text'])
        self.assertEqual(result['receipt']['elapsed_seconds'],20)
        self.assertEqual(self.world.s['elapsed_time']['seconds'],20)
        self.assertEqual(len(self.world.s['knowledge'][HENRY]),known+1)
        self.assertEqual(self.world.s['campaign_time'],before)
        self.assertEqual(self.host.load().save(),self.world.save())
        self.assertFalse(self.world.s['stocks'])

    def test_plain_existing_selection_never_silently_receives_the_optional_scene(self):
        self.create({'kind':'existing','actor_id':HENRY})
        self.assertNotIn('scene_rules',self.world.s)
        self.assertEqual(self.view()['current_mode'],'declaration_only')
        self.assertEqual(set(self.world.s['knowledge'][HENRY]),{'setup:civil-date'})

    def test_civil_date_is_sourced_received_day_precision_separate_from_other_axes(self):
        self.create(); civil = self.view()['civil_time']
        self.assertEqual(civil['date'],'1415-08-11'); self.assertEqual(civil['calendar'],'julian')
        self.assertEqual(civil['precision'],'day'); self.assertEqual(civil['ordinal'],2238109)
        self.assertIsNone(civil['time']); self.assertIsNone(civil['opening_hour'])
        self.assertFalse(civil['elapsed_calendar_binding']); self.assertFalse(civil['current_calendar_binding'])
        self.assertEqual(self.world.s['campaign_time']['day'],0)
        self.assertGreater(self.world.s['clock'],0)
        self.assertEqual(self.world.s['elapsed_time']['seconds'],0)

    def test_unknown_civil_date_in_generic_profile_remains_unknown(self):
        self.world = initial_campaign('fantasy','generic-unknown-time')
        self.create({'kind':'new','name':'Synthetic traveller','species':'human'})
        self.assertIsNone(self.view()['civil_time'])
        self.assertNotIn('civil',self.world.s['campaign_time'])
        self.assertEqual(self.view()['current_mode'],'declaration_only')

    def test_failed_persistence_cannot_publish_observation_or_elapsed(self):
        self.create(); request = self.request(); before = self.world.save(); disk = self.host.path.read_bytes()
        def fail(*args): raise OSError('synthetic persistence failure')
        with self.assertRaises(OSError): self.submit(request,persist=fail)
        self.assertEqual(self.world.save(),before); self.assertEqual(self.host.path.read_bytes(),disk)


if __name__ == '__main__':
    unittest.main()
