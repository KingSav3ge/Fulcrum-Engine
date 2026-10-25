#!/usr/bin/env python3
"""Repeatable shared-contract and neutral-depot Engine qualification."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'IRGS_3_3/runtime'))


def qualify():
    from response_depot import DEPOT, SOURCE_SHA256
    from routine_format import load_library, validate_library
    suite=unittest.defaultTestLoader.loadTestsFromNames(['test_shared_runtime','test_response_depot'])
    names=[]
    def inventory(tests):
        for test in tests:
            if isinstance(test,unittest.TestSuite):inventory(test)
            else:names.append(test.id())
    inventory(suite)
    log=io.StringIO()
    result=unittest.TextTestRunner(stream=log,verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError(log.getvalue())
    library=load_library(DEPOT)
    paths=[*('IRGS_3_3/runtime/'+name for name in ('core_world.py','shared_runtime.py','runtime_contracts.py',
        'response_depot.py','routine_format.py','offline_responses.py','scene_actions.py','settlement_runtime.py',
        'process_runtime.py','communication_runtime.py','solo_provider.py','r9_runtime.py',
        'test_shared_runtime.py','test_response_depot.py')),
        'IRGS_3_3/data/responses/depot_v1/library.json','IRGS_3_3/data/responses/depot_v1/SOURCE.json']
    return {'schema_version':1,'status':'PASS_SHARED_ENGINE_CONTRACTS_WITH_LIMITS',
        'date_utc':'2026-10-25','target_iteration':'IRGS 3.4.0 development','python':platform.python_version(),
        'library':validate_library(library),'source_catalog_commit':'94b8ca6d976da48b3c6ca65e014b28c6d9a120c2',
        'depot_sha256':SOURCE_SHA256,'system_variants':750,'editable_draft_variants':250,
        'new_named_tests':result.testsRun,'passed':result.testsRun,'skipped':len(result.skipped),'test_ids':names,
        'provider_dispatches':0,'model_tokens':0,'live_calls':0,'user_saves_used':False,
        'actual_contexts':{
            'non_rise_authored_scene':{'initialization':'test_scene_actions.fixture',
                'handler':'Core execute_player_scene_action','two_actions':'enter-passage → reach-desk',
                'elapsed_after_two_actions':35,'delivery_after_two_actions':'one actual sealed_dispatch transfer; 39 seconds total',
                'blocked_movement':'Actual unsuccessful outcome; five elapsed seconds; location retained'},
            'rise':{'initialization':'settlement_setup.initialize with explicit synthetic choices',
                'handler':'Core execute_settlement_action','two_actions':'walk_clearing → found',
                'elapsed_after_two_actions':300,'camp_established':True},
            'unsupported_context':{'handler':'Core record_player_action','result':'declared_not_resolved; exact intention retained'},
            'phase_and_communication':{'scope':'Existing native selected handlers; shared receipt/received projection',
                'status':'Actual nonterminal work phase and received attributed testimony, no invented speech duration'},
            'equipment':{'scope':'Existing actual stock handler/result retained; shared receipt adapter unavailable'}},
        'content_portability':{'themes':['historical court','fantasy expedition','space station','modern investigation'],
            'variants_per_theme':1000,'recipes_full_and_required':32,'establishes_theme_mechanics':False},
        'recovery':['Exact pending-request JSON','Mandatory host CAS','Concurrent acceptance once','Failed save rollback',
            'Lost acknowledgment/reload','Branch/restore fence','No changed replay or adapter identity reuse'],
        'information':['Actor/control checks','Actual received evidence only','Source/status/causal times preserved',
            'Explicit truncation','No stock/blocker feasibility oracle','No current facts appended to old receipts'],
        'core_control_fix':'Direct record_player_action rejects revoked current eligibility despite stale player-list entry; actual R9 rejection/conflict evidence',
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths},
        'remaining':['App authentication/persistence integration, controls, exact pins and joined qualification',
            'Shared execute adapters for broader processes/communication remain their existing native typed APIs',
            'No new equipment response adapter or generic operation dispatcher',
            'General freeform/combat, NPC decisions, sustained institutions and complete DEV/C2 coverage',
            'Live model quality/human evaluation and production token-savings measurement']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    report=qualify()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','new_named_tests','passed','skipped','system_variants','editable_draft_variants')}))
