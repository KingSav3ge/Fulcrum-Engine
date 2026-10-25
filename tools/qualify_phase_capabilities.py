#!/usr/bin/env python3
"""Qualify the bounded host-safe phase API with actual synthetic Core effects."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'IRGS_3_3/runtime'))


def qualify():
    suite = unittest.defaultTestLoader.loadTestsFromName('test_phase_contract')
    names = []
    def inventory(items):
        for item in items:
            if isinstance(item, unittest.TestSuite): inventory(item)
            else: names.append(item.id())
    inventory(suite)
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError(output.getvalue())
    paths = ['IRGS_3_3/runtime/'+name for name in (
        'phase_contract.py', 'test_phase_contract.py', 'process_runtime.py', 'shared_runtime.py',
        'runtime_contracts.py', 'player_actions.py', 'core_world.py', 'scene_actions.py',
        'settlement_runtime.py', 'r9_runtime.py', 'r8_dependencies.py', 'offline_responses.py',
        'response_depot.py', 'routine_format.py')]
    paths += ['IRGS_3_3/data/responses/'+name for name in (
        'depot_v1/library.json', 'depot_v1/SOURCE.json', 'engine_routine_v1.json')]
    return {'schema_version': 1, 'status': 'PASS_SELECTED_PHASE_CAPABILITY_CONTRACT_WITH_LIMITS',
        'date_utc': '2026-10-25', 'target_iteration': 'IRGS 3.4.0 development',
        'python': platform.python_version(), 'api_schema': 'irgs-phase-capabilities-1',
        'pulled_base_commit': '28c0ebe9c74a16c0baf2f18141d8024d1a12aad6',
        'initial_api_commit': '8ab620099090413ed706aa70894065544347fbf3',
        'tests_run': result.testsRun, 'passed': result.testsRun, 'skipped': len(result.skipped), 'test_ids': names,
        'actual_handler': 'Core continue_player_process through process_runtime.execute and host CAS bridge',
        'contexts': {
            'non_rise_observation': 'Received selected authored three-second observe action; 2+1 seconds delivers knowledge only at completion',
            'rise_work': 'One existing shelter project; 3600 worked seconds across actual provision boundaries, three founder timber consumed once',
            'reservations': 'Paused observation retains actual actor reservation; work cancellation retains physical progress and new explicit resume reuses the project',
            'availability': 'Attemptable selected contexts, no hidden stock/permission feasibility menu',
            'received_status': 'Immutable received phases and supported attempts; external live work is not probed, explicit inspect refreshes'},
        'dependencies': 'Actual R9 handler success/rejection reads include control, rules, locations, stocks and reservations; private certificate evidence is excluded from public DTOs',
        'scarcity': 'Two competing observations and stock/work frontier claims defer both in either event order',
        'recovery': ['Mandatory atomic host save/result CAS', 'Same safe persisted and returned receipt',
            'Failed save leaves original world unchanged', 'Concurrent phase delivery once',
            'Lost acknowledgment and pending native JSON restart', 'Terminal replay retains the original receipt',
            'Changed identity payload rejects', 'Discarded future restore request rejects'],
        'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths},
        'provider_calls': 0, 'model_tokens': 0, 'user_saves_used': False,
        'remaining': ['New App phase controls/adapter, exact reviewed pins and coordinator joined qualification',
            'Next bounded communication/offer participant and received-source contract',
            'Travel remains native-only; no universal travel/stock/timing rule is introduced',
            'Broader DEV-06–DEV-17, general freeform/combat, sustained institutions and full C2 remain open',
            'Distributed host durability, live inference and model/human evaluation remain outside this evidence']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = qualify()
    if args.output:
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'tests_run', 'passed', 'skipped')}))
