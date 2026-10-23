# IRGS Engine work order — solo-runtime-01

Target iteration: **IRGS 3.4.0 — in development**. Use 3.4.0 for this iteration's delivery and release notes. Preserve existing Core compatibility IDs, content/schema versions and historical qualification labels; the integrated release receives its 3.4.0 identity after qualification.

Assigned through IRGS Enviroment on 23 October 2026 following the user's direction to complete the systems needed to run IRGS. Owner: **IRGS Engine**. Push only to `KingSav3ge/IRGS-Engine/main`.

## Baseline and priority

Reviewed integrated Engine: `723627e629231b5e90f38b9d52b65c9a3967b92a`. Historical Details is complete and its previous work order is preserved in `COORDINATOR_WORK_ORDER_HISTORICAL_DETAILS_01.md`. App currently pins this Engine and Catalog `3e898acb2179f18a41d7967817bedf429df29d3f`. Do not repeat archive acquisition or wait for another historical import approval.

Read the coordinator's [Solo completion plan](https://github.com/KingSav3ge/IRGS/blob/main/SOLO_COMPLETION_PLAN.md), existing DEV list and `engine/AI_PROVIDER_PLAN.md`. The immediate delivery is the Engine boundary required for a continuing AI-assisted Solo action loop. Preserve the master C2 requirements, nine K-owners and six Director categories. Existing broader DEV work stays open; qualify the touched operations while implementing this delivery.

## First implementation

1. Implement typed actor-scoped request, proposed action, validated result and unavailable/error contracts beside the existing Core. Use existing registry/Capability Broker boundaries. Requests bind campaign/branch, actor, state/restore identity, exact player intention, allowed information and operations, source references, prompt/schema/config versions, deadline/output limits and explicit route/budget eligibility.
2. Implement disabled-by-default dispatch with fake transport, deterministic proposal/schema validation, finite concurrent reservations and an attempt/replay ledger. Keep technical inference accounting distinct from authoritative campaign state. Record requested versus reported route and known versus unknown usage; a failed or timed-out attempt is not automatically free. Retry, restart and late completion cannot silently authorize a second paid dispatch.
3. Map an accepted structured proposal to a real already supported local/Rise action handler. Selecting a proposal changes no state. Explicit player acceptance retains its original semantic payload, checks current actor control, rule, resources and freshness, and uses existing atomic effects and durable receipts. Unsupported freeform/combat remains unresolved until its actual rule exists. An AI result cannot commit arbitrary events or authorize itself.
4. Publish a small documented Engine API and passing offline commit early for App qualification. Then implement one opt-in direct adapter after checking its exact current official API/model contract. Keep keys server-side; build and test HTTP success/error/timeout/usage handling without needing live credentials. OpenAI direct is an initial candidate, not a measured model winner.
5. Narration derives from actor-legitimate committed results; dialogue expression cannot change accepted intent or invent player decisions. Expose sources and uncertainty needed for validation and disclose semantic/human-review limits. No full world/template or evaluator-only oracle enters actor/model context.

## Required evidence

Use Catalog's labelled synthetic R00-derived fixture when delivered; initial contract tests can use local temporary fixtures. Execute the applicable SOLO-01–SOLO-08 and AIP evaluation requirements, including denial, malformed/unsupported output, revoked authority, depleted stock, conflict, stale state/restore, cancellation/timeout, disallowed fallback, duplicate/concurrent delivery and exhausted reservations. Effect claims require the selected actual Core handler, not a fake world mutation. Reuse actual dependency observation and qualify relevant DEV-06–DEV-11 gaps for the operations exposed.

Run Engine integrity and meaningful runtime regressions. Include a two-action sequence and persisted/restarted recovery evidence. No key is needed for this offline implementation. Live smoke is separately pending until a server credential, account-available model, permitted workload and finite budget are configured; no paid call is authorized merely by this assignment. Do not report offline fake transport as live AI gameplay or model-quality evidence.

## Delivery and coordinator review

Work in your own component repository on `main`. Preserve existing work and adopted content. Return the exact pushed commit, changed executable behavior or validated test content, tested dependencies, executed checks, skips, remaining requirements and live prerequisites to **IRGS Enviroment**. Update completed, active and remaining work. Documentation and hash-only changes are not a viable runtime delivery.

The coordinator reviews an actual Engine/App/Catalog update set, checks exact App pins and tests an isolated joined candidate before integrating product source. No previous-cycle approval applies to a new commit. Test with temporary synthetic saves only. The original Historical Grand Archive remains exact, and no private campaign or reference payload is sent to a provider by this work order.

The coordinator can read these chats and publish repository work orders but has no direct chat-start/send tool. This file is the assignment; publication does not claim that your chat was resumed. The QA monitor tests pushed source, not development activity.
