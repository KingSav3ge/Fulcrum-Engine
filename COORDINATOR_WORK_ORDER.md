# Alpha 4.0 work order — IRGS-Engine

## Coordinator review and world-builder direction — 28 October 2026

Read [the current review](COORDINATOR_REVIEW_2026_10_28.md) and
[its executed scope](COORDINATOR_REVIEW_2026_10_28.json). This priority supersedes
older first-task ordering below; existing task IDs and historical evidence remain.

Continue A4-ENG-01's independent current-context qualification and actual offer
prerequisites; publish A4-ENG-02 selected travel and A4-ENG-03 supported-intent DTOs.
Do not add NPC consent or elapsed speech merely to make a fixture pass.
WB-ENG-01 world-authoring contracts can proceed alongside that work.

The user directs a shared development/Creator Workshop world builder:
[implementation plan and owner tasks](WORLD_BUILDER_PLAN.md).
The uploaded executable remains uninspected/unmatched after the transfer limit,
but the public v0.35.4 GPL source has now been assessed separately:
[reference findings](WORLD_BUILDER_REFERENCE_ASSESSMENT.md).
Do not claim binary equivalence, runtime qualification or an implemented editor.
Use the observed source workflows to inform original IRGS contracts and UI,
keeping one Core and the Alpha gameplay critical path.

Current edition remains 3.4.3 Pre-Alpha. A joined 3.4.4 publication is held for
the review's fixes, compatible pins, fresh execution capture and final qualification.
No Alpha gate is closed by this documentation update.

Current product: **3.4.3 Pre-Alpha**. Target: **functional 4.0.0 Alpha**.
This replaces the old start-adoption ordering. The coordinator already published
the compatible 3.4.3 set; do not wait for its completed App adoption.

## Ownership and first delivery

Own IRGS_3_3/, engine/, technical initializers and selected rules. App host/viewer
and Catalog content/evaluation stay with their owners. Retain stable DEV IDs and
the C2 acceptance inventory; new A4 IDs supplement them.

**Start A4-ENG-01 now**, publishing the normal-start communication contract and
ordinary-path evidence. Then deliver A4-ENG-02 over the existing native travel
process. Expose real capabilities, not more scenario descriptions or tests that
inject participants only after campaign creation. Send App/Catalog early DTO,
status/error, example and recovery handoffs. No need to wait for their whole Alpha.

## Implementation queue

| Task | Work and completion evidence | Dependencies; gates |
| --- | --- | --- |
| A4-ENG-01 | Expose legitimate participants, channels, received sources and offers in selected ordinary starts through existing communication APIs. Initialization must be explicit, reviewed, idempotent and preserve source uncertainty. A fresh ordinary App start can reach a participant; unknown/private parties stay hidden. No channel/consent/stock invented by the viewer or test harness. | Existing start/communication APIs; G02/G05; DEV-14–16,18/20 |
| A4-ENG-02 | Publish host-safe selected native travel, movement and perception over existing process/scene handlers. Preserve actual route/access, location, selected duration, actor/goods commitments, interruption and received arrival. Exercise competing claims, partial progress, stop/resume, save/restart/retry/restore and changed access. Adopt no unsupported return/cancellation rule. | Existing process/phase contracts; G04; DEV-06–14 |
| A4-ENG-03 | Define and implement the common supported-intent contract used by suggestions, own responses and optional AI. Separate parse/proposal, supported operation, required clarification, authorization, prepare, explicit acceptance and execution. Publish operation/status/error DTOs and examples; ambiguity or unsupported commands preserve the exact text and commit no invented effects. Demonstrate multiple consecutive real operations after normal creation. | Can publish DTOs alongside 01/02; G03; DEV-02/04–08,14/24 |
| A4-ENG-04 | Complete selected dialogue, offers/counteroffers, consent/refusal, obligations and fulfillment through actual Core handlers. NPC decisions use their own authority and scoped knowledge, not player impersonation. Revalidate stock, authority and competing obligations. Prove contradictory testimony, private terms, withdrawal, stale acceptance and original-result retry across normal starts. | 01/03; G05; DEV-15–17 |
| A4-ENG-05 | Implement bounded recurring NPC and local institutional reviews through existing owners/processes. Goals/plans/received information lead to proposed actions, not direct world edits. At least one person and one institution react to changed state, compete for shared capacity and retain commitments after reload. Compare continuous/resumed progression and document scheduling/time rules. | 02–04; G06/G10; DEV-17/19,21–23 |
| A4-ENG-06 | Complete the selected Alpha material/needs/work/recovery and risk/conflict profile. First inventory adopted rules and unresolved decisions with Catalog; version any needed concrete design before implementation. Account for inventory/custody, consumed inputs, actor capacity, justified elapsed work and persistent consequences. Demonstrate rejection, scarcity, success/failure/withdrawal and recovery. Shared owners must serve both Alpha contexts. | 02/03; Catalog A4-CAT-02 source/rule review; G04/G07; DEV-05–14 and applicable C2 cases |
| A4-ENG-07 | Finish one existing provider path for scoped intent/dialogue/narration. Publish protected request/response and accounting contracts for App. Validate untrusted output, ground narration in authorized receipts, retain finite budgets/cancellation and prevent stale responses after restore. Fake transport qualifies protocol only; support a separate approved live quality run without changing Core authority. | 03–05; App 01/05; G08; existing AIP plan, DEV-14/17/24 |
| A4-ENG-08 | Maintain a per-operation DEV/C2 coverage map and close durability/dependency gaps for all Alpha-exposed handlers. Exercise failed saves, conflicts, authority revocation, duplicated delivery, lost reply, phase continuation, restart and discarded-future restore. Keep wider DEV/C2 requirements open where not implemented. | Throughout, then full candidate; G09/G12; DEV-03/05–11/19/23/26–27 |

Do not defer all gameplay until a general natural-language resolver exists.
Deliver structured supported operations and their real contracts first. App can
map reviewed text into these operations; neither AI nor App gains mutation authority.

## Interface and QA handoff

Read engine/START_READINESS_API.md, engine/COMMUNICATION_CAPABILITY_API.md,
engine/PHASE_CAPABILITY_API.md, engine/SHARED_SYSTEMS_API.md and
engine/SOLO_PROVIDER_API.md. Evolve their versioned contracts deliberately and
preserve compatibility or document an explicit consumer migration. For every new
capability publish initialization prerequisites, actor filtering, accepted intent,
effects/time, failure states, CAS/retry/restore behavior and executable examples.

Use Python 3.12+ without -O. From the repository root:

~~~bash
python -B tools/verify_components.py --component engine
python -B tools/qualify_shared_systems.py
python -B IRGS_3_3/catalog/campaigns/kira/verify_kira.py
~~~

Run focused new-handler and existing start/shared/phase/communication/process
regressions; before a runtime delivery run the full runtime discovery with the
project's private-fixture policy and report the actual skip. The single excluded
identity is test_suite.SuiteTests.test_legacy_ast_save_load_does_not_rewrite;
replace it with an explicit policy skip before execution, without opening a save.
The coordinator's [full-suite recipe](https://github.com/KingSav3ge/IRGS/blob/9dc27f82f7f49e6f8b1de66573b991b22e68cb2a/tools/qa_irgs.py)
and [capture policy](https://github.com/KingSav3ge/IRGS/blob/9dc27f82f7f49e6f8b1de66573b991b22e68cb2a/tools/coverage_capture.py)
show this replacement. Do not omit other tests or import a user's files to make
the suite pass. Record the skip separately from passing cases.
After intentional Engine source edits, refresh only Engine hashes, then verify
and rerun applicable behavioral checks:

~~~bash
python -B tools/refresh_component_releases.py --component engine
python -B tools/verify_components.py --component engine
~~~

Check normal App creation and actions against exact published consumer sources;
record overrides/import paths separately from App's committed pins. An
Engine-only check does not qualify App controls or Catalog acceptance.

## Required boundaries and delivery

Follow [the shared plan](ALPHA_4_0_PLAN.md), [acceptance register](ALPHA_4_0_ACCEPTANCE.json)
and [version policy](VERSION_POLICY.md). Keep one Core, nine K-owners, six Director
categories, actual authority/resources, actor-scoped knowledge and explicit
review before atomic acceptance. Preserve immutable original results, recovery
fences and the distinctions between intent, effect, outcome and presentation.
No guessed universal durations, stock, permissions, dice or historical hours.

Use synthetic temporary stores and exact declared dependencies. Preserve original
archive bytes/citations, adopted canon, historical evidence and legacy fixture
identities. Credentials, user saves, personal configuration, caches and runtime
logs are not test inputs or committed source. Live provider evaluation requires
a separately authorized finite budget; do not delay independent offline work.

Publish only this repository. Deliver one meaningful implement/test/report
increment at a time. Report task/gate IDs, full pushed SHA, exact dependencies and
App pins, commands and actual passes/failures/skips, evidence, capability limits,
next task and specific blockers. A schema, guide, hash refresh or fixture alone
does not complete product behavior. Keep 3.4.3 metadata during component
development; the coordinator controls the next unified edition and Alpha gate.
