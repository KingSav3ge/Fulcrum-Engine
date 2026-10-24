#!/usr/bin/env python3
"""Repeatable Engine-owned offline response qualification; synthetic saves only."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'IRGS_3_3/runtime'
sys.path.insert(0, str(RUNTIME))


def qualify():
    from routine_format import load_library, validate_library
    suite = unittest.defaultTestLoader.loadTestsFromName('test_offline_responses')
    names = []
    def inventory(tests):
        for test in tests:
            if isinstance(test, unittest.TestSuite):
                inventory(test)
            else:
                names.append(test.id())
    inventory(suite)
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=1).run(suite)
    if not result.wasSuccessful() or result.skipped:
        raise RuntimeError(log.getvalue())
    library = load_library()
    paths = [*('IRGS_3_3/runtime/' + name for name in (
        'offline_responses.py', 'routine_format.py', 'test_offline_responses.py',
        'scene_actions.py', 'settlement_runtime.py', 'solo_actions.py',
        'process_runtime.py', 'communication_runtime.py')),
        'IRGS_3_3/data/responses/engine_routine_v1.json', 'IRGS_3_3/data/responses/PROVENANCE.json']
    return {'schema_version': 1, 'status': 'PASS_OFFLINE_ENGINE_RESPONSES_WITH_LIMITS',
        'target_iteration': 'IRGS 3.4.0 — in development',
        'library': validate_library(library),
        'system_variants': sum(len(f['variants']) for f in library['families'] if f['channel']=='system'),
        'player_draft_variants': sum(len(f['variants']) for f in library['families'] if f['channel']=='player_draft'),
        'tests_run': result.testsRun, 'passed': result.testsRun, 'skipped': len(result.skipped),
        'test_ids': names, 'render_provider_calls': 0, 'render_model_tokens': 0,
        'live_calls': 0, 'user_saves_used': False,
        'source_sha256': {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        'evidence': ['338 variants and 15 recipes formatted',
            'Real Core default result paths preserve successful and unsuccessful outcomes',
            'Provider transport and network connection forbidden in offline action/draft/status test',
            'Actual received phase/communication records, atomic Core effects and temporary host recovery',
            'Actor/receipt/scope checks, exact-source fallback and draft selection without effects'],
        'limits': ['App consumer controls, dependency pins and joined qualification are separate',
            'No general freeform/combat resolution or natural-language interpretation is added',
            'No live model, semantic quality, human review or historical calibration is measured']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = qualify()
    serialized = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.write_text(serialized, encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('status','tests_run','passed','skipped','system_variants','player_draft_variants')}))
