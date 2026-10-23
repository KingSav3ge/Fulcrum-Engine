# Solo proposal API, version 1

Delivery target: **IRGS 3.4.0 — in development**. Core compatibility remains 3.3;
the proposal schema's independent version remains `solo-proposal-1`.

`solo_provider.py` and `solo_actions.py` implement the first bounded Capability
Broker beside Core 3.3. Dispatch and every route default to disabled. The only
task is `propose_local_action`, assigned to the existing Local Director category.
No Director, K-owner, resource ledger or world authority is added.

## Host integration

Import from `IRGS_3_3/runtime`, as with the existing Core modules. Authenticate
the host session and actor before invoking these **server-only** functions.
Never deserialize an ActorRequest supplied by a browser or provider into an
authorized request. The host builds it from its selected CoreWorld:

```python
request = prepare_request(
    world, request_id=submission_id, actor_id=authenticated_actor,
    intention=exact_player_text, branch_id=current_branch,
    restore_id=current_restore_identity, allowed_routes=(approved_route_id,),
    classification=reviewed_classification, policy_ref=reviewed_transfer_policy,
    config_version=selected_config_version, deadline=time.time() + 30)
result = broker.dispatch(request, approved_route_id, transport)
```

Construct `AttemptLedger(private_runtime_dir / 'inference.sqlite',
budget_units=explicit_finite_ceiling, max_inflight=explicit_limit)` outside source,
then `CapabilityBroker(SpecialistRegistry(routes), ledger, enabled=True,
scope_reader=host_current_authorized_scope)` only
after explicit operator configuration. The API does not choose a budget, rate,
credential, workload permission or host policy for the operator.

The immutable request binds campaign, branch, restore identity, whole-state
digest, actor, exact intention, received information, allowed actions/routes,
classification/policy, prompt/schema/config versions, deadline and output limits.
New dispatch has a maximum 300-second horizon. Request/output/context sizes are
bounded. A route needs explicit qualification, tested schema capability, workload,
classification, policy/config agreement, versioned price/ceiling and approval.
Missing values stay unavailable. There are no automatic retries or fallbacks.
The required `scope_reader(request)` returns the host's currently authorized
`WorldScope`, or `None` for a closed/inaccessible session. It is checked before
dispatch, after transport and before returning a cached proposal. Stale replies
therefore remain unavailable before presentation as well as before acceptance.

`transport(model_input, route, timeout=..., max_output_tokens=...)` returns a
`TransportReply`. Only `request.model_input()` enters transport: actor ID, exact
intention, received evidence (with status/provenance/receipt time), received
options and allowed action/source IDs. Private world/restore hashes, full saves,
rules, unreceived evidence, hidden stock/blockers and evaluator oracles are absent.
Source records are data, never instructions or transfer authorization. The host
must review rights and policy for the complete scoped input before dispatch.

## Draft, acceptance and persistence

The sole proposal schema is:

```json
{"intention":"exact original text","action_id":"received-action-id","source_refs":["received-evidence-id"]}
```

Additional/duplicate keys, changed intent, unknown sources/actions, unexpected
route identity, excessive output or provider error produce an unavailable result.
`ValidatedResult.status` is `proposal_ready` or `unavailable`; the latter has a
bounded `code`. Validation establishes structure and references, **not semantic
agreement between prose and action**. Show the exact intention, selected action
and source references together for player review. Draft selection changes no
campaign state. Unsupported freeform/combat stays `declared_not_resolved` in the
existing declaration flow; this API cannot resolve it.

On explicit player acceptance, call:

```python
public_result = accept_proposal(
    current_world, ledger, request_id=result.request_id,
    proposal_digest=result.proposal.proposal_digest,
    actor_id=authenticated_actor, intention=exact_accepted_text,
    branch_id=current_branch, restore_id=current_restore_identity,
    explicitly_accepted=True, persist=host_atomic_compare_and_save, clock=time.time)
```

The callback `persist(expected_scope, candidate_save, public_receipt)` **must**
serialize against every host writer and atomically compare campaign, branch,
restore identity and state digest, then durably save candidate and receipt, or
raise. Reuse the host's existing save transaction; do not create another world
store. A missing callback is unavailable. Candidate execution uses the actual
`execute_scene_action` handler and its execution-derived dependency certificate.
Current control, rules, location, commitments and resources retain that handler's
checks. Failed physical attempts retain its supported unsuccessful outcome and
authored elapsed time; they never become a fabricated successful transfer.

The Core event retains the exact accepted intention and structured action.
Result narration is exclusively the committed handler's actor-legitimate summary
and observations. Private dependency certificates stay in the technical ledger.
No generated dialogue, new player decisions or arbitrary event API is exposed.

**Host obligations:** rotate restore identity whenever restoring a save, including
identical bytes; keep branch identity stable and explicit; invalidate/close old
requests on navigation or session closure using `ledger.cancel(request_id)`;
reload the durable save after an ambiguous persistence acknowledgment. Old
scope/state/control fails before new effects. A committed event returns its
original receipt without effects, including a lost acknowledgment. Competing
acceptors serialize via the shared technical database plus the mandatory host
save CAS. This is not qualification of another host's persistence implementation.

## Accounting and recovery

An attempt and its full conservative reservation are committed before transport.
The ledger stores request identity/versions, requested and reported route,
provider request ID, start/completion times, validation result, known token reports
and a private acceptance certificate. No credentials or provider error bodies are
stored. Null/empty usage means **unknown**, never zero cost. Reported tokens are
not a verified bill; actual charges remain unknown. Reservation units are an
operator-defined worst-case ceiling for the approved input/output limits and
versioned prices, separate from campaign money/resources.

Reservations remain consumed for this ledger's lifetime, including failures,
timeouts and cancellations. No automatic refund/reconciliation exists. Concurrent
claims atomically check budget and in-flight limits. A timed-out/cancelled worker
retains its concurrency slot until it actually finishes; a late completion may
record accounting but cannot publish a proposal. A crash with an ambiguous attempt
retains its reservation/slot and returns `in_progress_or_in_doubt` on restart.
There is no automatic redispatch, billing guess or silent budget reset. An operator
must reconcile uncertainty before deliberately provisioning a new budget/attempt.
Use a fresh explicit request ID for a new authorized attempt; never auto-generate
one as a retry. Reopening with different budget limits is rejected.

The database retains exact submitted text and received context for durable
validation. Protect it like the host's private campaign storage; never include it
in source, diagnostics exports, model context for another actor, or browser status.

## Executed scope and remaining gates

`test_solo_provider.py` uses temporary synthetic saves and offline transport.
It exercises actual local movement, observation, blocked movement and conserved
delivery, two successive actions, reload/replay, lost acknowledgment, concurrent
acceptance, host CAS failure, stale state/restore, revoked control, conflicting
commitments, depleted stock, malformed/unsupported output, denial, timeout,
cancellation, late reply, disabled/missing policy, fallback denial and finite budget.
It does not certify general simultaneous-frontier allocation or interrupted phases.

DEV-06–DEV-11 remain open beyond this handler's observed reads/writes, bounded
atomic action/receipt and host-assisted restore/replay contract. App session/save
integration, Catalog R00 fixture adoption when delivered, exact joined pair,
semantic/character human review, calibration and model quality remain separate.
The direct HTTP adapter and conditional live smoke are subsequent gates; no paid
call is authorized or claimed by these offline tests.
