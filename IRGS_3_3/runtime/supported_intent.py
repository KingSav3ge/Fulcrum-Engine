"""Explicit, provider-independent review of selected shared Core actions.

A host authenticates the actor and retains the native request privately. Text is
never parsed into an operation and no review, rejection or draft commits a world.
"""
import json

from irgs_reference import digest
from runtime_contracts import AcceptedIntent, WorldScope
import shared_runtime as shared

SCHEMA_VERSION = 'irgs-supported-intent-1'


def offer_prerequisites(world, *, actor_id, channel_id, recipient, branch_id, restore_id):
    """Report received attemptable offer selection without probing hidden facts."""
    import communication_contract as communication
    view = communication.actor_view(world, actor_id, branch_id=branch_id, restore_id=restore_id)
    channel = next((row for row in view['channels'] if row['channel_id'] == channel_id), None)
    participant = next((row for row in (channel or {}).get('participants', [])
                        if row['actor_id'] == recipient), None)
    status = ('participant_unavailable' if participant is None else
              'attemptable' if 'offer' in participant['supported_commands'] else 'offer_not_selected')
    return {'schema_version': SCHEMA_VERSION, 'actor_id': actor_id, 'status': status,
            'channel_id': channel_id, 'recipient': recipient,
            'requires_explicit_terms': True, 'requires_explicit_acceptance': True,
            'authority_and_resources': 'checked_on_execution', 'committed': False}


def review(world, *, actor_id, intention, capability_id, branch_id, restore_id):
    if not isinstance(intention, str) or not intention.strip() or len(intention) > 4096:
        raise ValueError('Supply exact intention text using 1–4096 characters')
    scope = WorldScope(world.s['campaign_id'], branch_id, restore_id, world.checksum()); scope.validate()
    capabilities = shared.capabilities(world, actor_id)
    if capability_id is not None and (not isinstance(capability_id, str) or not capability_id.strip() or len(capability_id) > 256):
        raise ValueError('Invalid capability identity')
    capability = next((item for item in capabilities if item.capability_id == capability_id), None)
    status = ('clarification_required' if capability_id is None else
              'supported' if capability is not None and capability.operation_id != shared.DECLARE else 'unsupported')
    selection = None if status != 'supported' else {
        'capability_id': capability.capability_id, 'operation_id': capability.operation_id,
        'action': json.loads(capability.action_json), 'title': capability.title,
        'source_refs': list(capability.source_refs)}
    identity = 'intent-review:' + digest([SCHEMA_VERSION, scope.campaign_id, branch_id, restore_id,
                                        scope.state_digest, actor_id, intention, capability_id, selection])
    return {'schema_version': SCHEMA_VERSION, 'review_id': identity, 'actor_id': actor_id,
            'intention': intention, 'status': status, 'selection': selection,
            'authorization': 'checked_on_execution', 'requires_explicit_acceptance': True,
            'committed': False, 'provider_calls': 0}


def prepare(world, *, request_id, actor_id, intention, capability_id, review_id,
            branch_id, restore_id, source_ref='explicit-player-submission'):
    reviewed = review(world, actor_id=actor_id, intention=intention, capability_id=capability_id,
                      branch_id=branch_id, restore_id=restore_id)
    if reviewed['status'] != 'supported':
        raise shared.SharedActionUnavailable('intent_not_supported')
    if review_id != reviewed['review_id']:
        raise shared.SharedActionUnavailable('review_stale')
    return shared.prepare_intent(world, request_id=request_id, actor_id=actor_id, intention=intention,
        capability_id=capability_id, branch_id=branch_id, restore_id=restore_id, source_ref=source_ref)


def _result(native):
    return {'schema_version': SCHEMA_VERSION, 'request_id': native['request_id'],
            'actor_id': native['actor_id'], 'intention': native['intention'],
            'capability_id': native['capability_id'], 'status': native['status'],
            'receipt': native['receipt'], 'presentation': native['presentation']}


def execute(world, request, *, current_scope, persist, explicitly_accepted):
    if not isinstance(request, AcceptedIntent):
        raise shared.SharedActionUnavailable('invalid_request')
    if request.operation_id == shared.DECLARE:
        raise shared.SharedActionUnavailable('intent_not_supported')
    if not callable(persist):
        raise shared.SharedActionUnavailable('persistence_required')
    def bridge(expected_scope, candidate_save, result):
        persist(expected_scope, candidate_save, _result(result))
    return _result(shared.execute_intent(world, request, current_scope=current_scope,
                                         persist=bridge, explicitly_accepted=explicitly_accepted))
