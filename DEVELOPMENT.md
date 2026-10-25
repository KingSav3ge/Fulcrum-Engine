# IRGS Engine development guide

Current guide: 25 October 2026. Owner: `KingSav3ge/IRGS-Engine/main`.
Start with [CHAT_CONTINUATION.md](CHAT_CONTINUATION.md), then the stable DEV list.

## Qualified baseline and scope

IRGS **3.4.0 development**, Core compatibility **3.3**. Develop shared systems
across campaigns and themes. Rise R00 and the existing non-Rise authored opening
are actual supported regression contexts. Synthetic theme/profile checks prove
their recorded formatting/declaration behavior, not new campaign mechanics.

The [coordinator integration](https://github.com/KingSav3ge/IRGS/blob/65351ebcfe2538d880f576a3ce4aa2230537e08d/provenance/qa/shared_response_integration_3_4_0_review.json) qualified joined `65351ebcfe2538d880f576a3ce4aa2230537e08d`:

| Component source | Qualified commit |
| --- | --- |
| Engine | `2f9476c6090878257d17cab3ad3a83a7ce18a5dc` |
| App/Web | `aae8a25656c890181e0aa569df2c716968ec3642` |
| Catalog | `27fff8385d1c01fdfe9ad7254b7647e6bc12a01e` |

Recorded integration results: 680 Core tests run (679 passed, one private-fixture
policy skip); 201 Web run (194 passed, seven Windows skips); 105 interface checks;
104 Catalog checks; eight independent HTTP checks. Two-context Chromium and
clean-package qualification passed with zero live inference. These are attributed
prior results, not tests newly executed by this guide update.

Later guide-only commits do not alter this qualified source set. Preserve
independent content/schema versions and historical evidence. See
[shared scope](IRGS_SYSTEMS_SCOPE.md), [continuation](CHAT_CONTINUATION.md) and
[the work order](COORDINATOR_WORK_ORDER.md).

## Completed foundation and current interfaces

- `runtime_contracts.py` / `shared_runtime.py`: actor scope, actual capabilities,
  exact accepted intent, mandatory host persistence, legitimate sources and receipts.
- `response_depot.py`: exact Catalog-authored 1,000-variant neutral depot bundled
  for independent Engine use. The 338-variant compatibility API remains available.
- Existing process and communication typed APIs, observed dependencies, immutable
  phase receipts and reviewed inference accounting have scoped synthetic evidence.
- App consumes existing Engine receipt/draft interfaces and selected Catalog
  semantic drafts; joined integration and packaging of that set are complete.

Read [shared API](engine/SHARED_SYSTEMS_API.md),
[continuation/communication API](engine/CONTINUATION_COMMUNICATION_API.md),
[provider API](engine/SOLO_PROVIDER_API.md), [roadmap](ROADMAP.md),
[DEV criteria](DEVELOPMENT_LIST.md) and [dated records](CONTINUATION_STATUS.md).
Current App usage does not imply every Engine API already has player controls.

## Next bounded increment

The selected observation/Rise work phase contract is delivered in
[phase API v1](engine/PHASE_CAPABILITY_API.md), initially published at
`8ab620099090413ed706aa70894065544347fbf3`. Its
[execution record](engine/PHASE_CAPABILITY_VALIDATION.json) qualifies actor-safe
options/status/commands, actual dependency reads and rejection, competing
stock/actor claims, pause/resume/cancel, mandatory CAS and restart/restore.
It is additive to the already integrated shared-response baseline. New App phase
controls/pins and coordinator joined qualification remain a separate handoff.

**Next bounded task:** expose the existing typed communication/offer participant
and received-source contract for supported selected channels. Build actor-safe
participant/offer views from actual legitimate received records; retain exact
utterances as testimony and original offer statuses/terms. Expose only actual
supported commands and keep private dependency evidence, hidden whereabouts,
stock feasibility and unreceived participant/source facts out of views. Reuse
explicit acceptance, current Core authority, selected custody/channel rules and
atomic host CAS; qualify rejected/withdrawn/superseded/fulfilled meanings,
competing claims and restart/restore. Preserve the delivered phase API. No NPC
choice, universal speech duration, travel/stock rule or generic dialogue resolver
is introduced by an adapter. Broader DEV-06–DEV-17/C2 scope remains open.

## Check the Engine

For current App/Catalog interoperability, use the independently owned checkout
selectors and [Engine-side checker](engine/COMPONENT_INTERACTION.md):
`python -B tools/qualify_component_interaction.py --app-root ../IRGS-APP-WEB --catalog-root ../IRGS-Catalog`.
It needs loopback sockets and records exact sources while preserving App pins and
Catalog's original consumer identities. This qualification does not add a Core
dependency on either checkout or replace coordinator joined review.

```bash
python -B tools/verify_components.py --component engine
python -B tools/qualify_shared_systems.py
python -B -m unittest discover -s IRGS_3_3/runtime -p test_process_runtime.py -v
python -B -m unittest discover -s IRGS_3_3/runtime -p test_communication_runtime.py -v
python -B IRGS_3_3/catalog/campaigns/kira/verify_kira.py
```

Core and bundled depot checks require no App/Catalog checkout. Optional
`tools/qualify_solo_provider.py --catalog-root ../IRGS-Catalog/IRGS_Catalog`
qualifies the selected original R00 contract; it is not live inference.

For the full standalone suite, use the same explicit private-fixture policy as
coordinator QA. In Bash, from this repository root:

```bash
python -B - <<'PY'
import sys, unittest
external = 'test_suite.SuiteTests.test_legacy_ast_save_load_does_not_rewrite'
def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item
class PrivateFixtureSkip(unittest.TestCase):
    def id(self):
        return external
    @unittest.skip('External private save excluded by development policy')
    def runTest(self):
        pass
suite = unittest.defaultTestLoader.discover('IRGS_3_3/runtime')
cases = [PrivateFixtureSkip() if case.id() == external else case for case in flatten(suite)]
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(cases))
sys.exit(0 if result.wasSuccessful() else 1)
PY
```

After intentional Engine source changes:
`python -B tools/refresh_component_releases.py --component engine`, then verify
again. Keep actual new evidence in the owner record; disclose incomplete paths.

## Rules for every increment

Keep one authoritative Core and the nine K-owners; provider work retains the six
existing Director categories. Distinguish intent, authorization, committed effects,
received information and presentation. Only actual actor-legitimate records may
support a response. Testimony and uncertain information retain their status.
Keep storage revision, causal order, elapsed spans, civil dates and information
times distinct. Select real rules/adapters; themes and text create no capability.

Routine responses require no provider, key or model tokens. Preserve exact
receipts, negation, actual zero/absent durations, editable intentions and explicit
submission. Missing text or rules retain a literal/unresolved result and cannot
authorize paid fallback. Keep pinned code/content intake on the exact verified
bytes; retain the component-update regression in App.

Use temporary synthetic saves. Never read/migrate user campaigns or run the
external private-save fixture. Preserve original archives, source records,
rights, adopted canon and 44 previews. Historical Details is fully delivered;
archive reacquisition is complete. Preview/content presence grants no release
or mechanical authority. General freeform/combat, generated dialogue, sustained
institutions, full C2, live model quality and wider hosting retain their open
requirements; Co-op remains deferred.

## Deliver the increment

Keep completed, active and remaining work current. After an actual source edit,
refresh only the owning component release, run relevant behavioral checks and
verify source integrity. Hash refresh and planning alone qualify no feature.
Use Python 3.12+ without `-O`; interface/browser tooling uses Node 20+.

Push only this repository's `main`. Return the full pushed SHA, actual changed
behavior, APIs/adapters, exact dependencies, commands/results/skips and remaining
limits to IRGS Enviroment. Coordinator imports product source only after all
three viable updates, compatible App pins and fresh joined qualification.
Root guide/work-order edits alone need no component release refresh or invented
runtime delivery. Preserve local work before pulling; avoid resets and force pushes.

Previous guide: [dated history](DEVELOPMENT_HISTORY_2026-10-25.md).
