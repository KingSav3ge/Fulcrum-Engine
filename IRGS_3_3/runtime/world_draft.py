"""Bounded data-only draft contract for the existing reviewed Rise initializer.

A draft is not a campaign. No paths, scripts, hidden rules or creator data are
executed. Durable storage, atomic publication and access control belong to host.
"""
import copy
from irgs_reference import digest
from settlement_setup import preview as rise_preview, initialize as rise_initialize

SCHEMA_VERSION = 'irgs-world-draft-1'
VALIDATION_VERSION = 'irgs-world-validation-1'


def inspect(draft):
    """Return a validation DTO, including a public diagnostic for invalid drafts."""
    try:
        return validate(draft)
    except ValueError as error:
        return {'schema_version': VALIDATION_VERSION, 'status': 'invalid',
                'errors': [{'code': 'invalid_draft', 'message': str(error)}], 'committed': False}


def validate(draft):
    if not isinstance(draft, dict) or set(draft) != {'schema_version', 'draft_id', 'classification', 'profile_id', 'choices'}:
        raise ValueError('Supply only the supported world draft fields')
    if draft['schema_version'] != SCHEMA_VERSION:
        raise ValueError('Unsupported world draft schema')
    if not isinstance(draft['draft_id'], str) or not draft['draft_id'].strip() or len(draft['draft_id']) > 128:
        raise ValueError('Invalid draft identity')
    if draft['classification'] != 'fictional' or draft['profile_id'] != 'rise-r00':
        raise ValueError('Only the selected fictional Rise R00 draft is supported')
    review = rise_preview(copy.deepcopy(draft['choices']))
    return {'schema_version': VALIDATION_VERSION, 'draft_id': draft['draft_id'], 'status': 'valid',
            'classification': 'fictional', 'profile_id': 'rise-r00',
            'draft_digest': digest(draft), 'review_digest': review['review_digest'],
            'review': review, 'proposed_initializer': 'settlement_setup.initialize',
            'unsupported': ['historical or mixed draft', 'custom geography or entities',
                            'custom scripts and rules', 'world-pack import/export'],
            'committed': False}


def initialize(draft, *, draft_digest, review_digest, campaign_id, explicitly_accepted):
    if explicitly_accepted is not True:
        raise ValueError('Explicit draft acceptance is required')
    if not isinstance(campaign_id, str) or not campaign_id.strip() or len(campaign_id) > 128:
        raise ValueError('Invalid new campaign identity')
    reviewed = validate(draft)
    if draft_digest != reviewed['draft_digest'] or review_digest != reviewed['review_digest']:
        raise ValueError('Draft or selected rules changed; review again')
    return rise_initialize(copy.deepcopy(draft['choices']), review_digest, campaign_id)
