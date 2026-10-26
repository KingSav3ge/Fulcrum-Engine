# IRGS Engine — 3.4.3 development

Current start increment: [readiness and sourced existing-person API](engine/START_READINESS_API.md), with 33 dedicated cases and 772 full-runtime passes plus one prescribed skip. Henry has one optional sourced observation; other unsupported modes remain held. [App/Catalog adoption and exact-set review](engine/START_DELIVERY_VALIDATION.json) remain pending, including three old App assertions requiring empty historical starting knowledge.

[Current adoption handoff](engine/START_ADOPTION_HANDOFF.md) supplies a repeatable
six-context HTTP diagnostic and exact Engine examples. It reproduces blocked App
adoption, including a wrong result-axis label, with unchanged Engine runtime/data.
App/Catalog owners and exact-set coordinator qualification remain dependencies;
selected native travel follows adoption. [Fresh results](engine/START_ADOPTION_VALIDATION.json)
keep passing backend checks separate from three failing App expectations.

Current coordinated edition: **3.4.3**; previous release: **3.3.3**.
See [version policy](VERSION_POLICY.md). Earlier baseline tables and execution
records below retain their original tested development identities.

Current development: [guide](DEVELOPMENT.md) · [chat continuation](CHAT_CONTINUATION.md).

IRGS develops a persistent world simulation connecting individual action, institutions, resources and history. Its design centers on one shared world, actions constrained by actual authority and resources, and information received by the acting character or institution. See the [Engine model](engine/ENGINE_MODEL.md) for these principles and their current implementation limits.

Independent Engine development for IRGS, selected Core 3.3. This repository owns `IRGS_3_3/`, the applied design under `engine/`, Engine milestones and source provenance. The App develops separately in [IRGS-APP-WEB](https://github.com/KingSav3ge/IRGS-APP-WEB); [IRGS/main](https://github.com/KingSav3ge/IRGS) joins both components.

The [shared Engine API](engine/SHARED_SYSTEMS_API.md) now provides common actor/capability views, exact accepted intentions, atomic execution, received records and committed receipts across selected authored-scene and Rise handlers. It bundles Catalog's exact neutral **750 system / 250 draft** depot with 32 recipes and requires no provider or App/Catalog checkout. [Independent qualification](engine/SHARED_SYSTEMS_VALIDATION.json) separates actual non-Rise/Rise effects from four-theme text portability. Unsupported intentions stay unresolved; broader mechanics retain their existing scope.

[Phase capabilities v1](engine/PHASE_CAPABILITY_API.md) adds actor-safe selected observation/Rise work options, received status/commands and filtered phase outcomes through the existing typed continuation/CAS API. [Qualification](engine/PHASE_CAPABILITY_VALIDATION.json) covers actual handler reads, scarcity, lifecycle and recovery. Shared actor views expose `continuations`. App now supports selected phase start discovery and continuation; current exact-set pin/joined review remains separate.

[Current three-component compatibility](engine/COMPONENT_INTERACTION.md) now verifies latest App/Catalog development sources against this Engine through real HTTP and Chromium, preserving their committed pins and original fixture identities. The later [26 October source check](engine/COMMUNICATION_COMPONENT_INTERACTION_VALIDATION.json) also passes current App start discovery and continuation against this communication increment. Exact joined/pin review remains separate.

[Communication capabilities v1](engine/COMMUNICATION_CAPABILITY_API.md) adds received participant/source and offer views, exact testimony/terms and sanitized atomic execution. Shared views include `communications`; forwarding testimony grants no private offer access. [32 dedicated cases](engine/COMMUNICATION_CAPABILITY_VALIDATION.json) pass, and the full runtime suite runs 740 cases with 739 passes and one prescribed private-save skip. App communication controls and exact-set integration remain separate.

Publish Engine updates to **KingSav3ge/IRGS-Engine**, on its `main` branch. The [development roadmap](ROADMAP.md) separates completed work, work in progress and remaining work; the [DEV checklist](DEVELOPMENT_LIST.md) supplies task IDs and completion criteria, and the [continuation log](CONTINUATION_STATUS.md) records delivered increments and verification limits. Update these records as Engine work progresses.

```bash
python -B tools/verify_components.py --component engine
python -B tools/qualify_shared_systems.py
python -B tools/refresh_component_releases.py --component engine
```

Core verification and tests require no App checkout. Python 3.12+ is required; do not use `-O`. Run `python -B IRGS_3_3/catalog/campaigns/kira/verify_kira.py` for Kira canon/archive consistency. Historical external-save tests can explicitly skip absent private fixtures; use only synthetic temporary saves.

Engine source pins are in `IRGS_3_3/release.json`; App pins belong to its repository. Refresh pins after intentional edits, execute meaningful runtime checks, then commit/push `main`. Do not change rules merely to match an imported proposal. General C2 completion remains work; bounded handlers and 37 dated Century starts do not qualify a complete historical simulation.

The App pins an Engine commit through its `Engine` submodule. Qualify the pair before updating that pointer or joined IRGS. See [joined integration instructions](https://github.com/KingSav3ge/IRGS/blob/main/COMPONENT_REPOSITORIES.md). Historical operation/evidence documents retain the source identities of their original joined runs; they are not fresh standalone or all-branch certification.

Kira v0.5 is adopted working setting canon, with a [six-region illustrated atlas and regional foundations](IRGS_3_3/catalog/campaigns/kira/atlas/README.md) beside its worldbook. It initializes no player, resources, numerical magic rules or future outcomes. Source/provenance archives remain labelled historical material. No user saves are included or migrated.

The [Historical Details reader contract](engine/HISTORICAL_DETAILS_API.md) supports pinned multipart archives and existing explicit ZIP attachments. Catalog's real 32-part delivery and ten reader collections are verified. Catalog owns the full payload; App owns Creator browsing and its reviewed dependency pins. Connected App/joined qualification remains separate.

**IRGS 3.4.0 — in development:** the [Solo provider/action API](engine/SOLO_PROVIDER_API.md) now supplies disabled-by-default scoped proposals, durable technical accounting and explicit acceptance through existing local/Rise Core handlers. The [direct OpenAI adapter](engine/OPENAI_ADAPTER_REVIEW.md) is opt-in and tested with synthetic HTTP; [Catalog R00 execution](engine/SOLO_CATALOG_VALIDATION.json) qualifies ten offline cases. No live inference, model-quality winner or new joined release is claimed. Broader work remains in the [AI provider plan](engine/AI_PROVIDER_PLAN.md).

The [Solo lifecycle continuation](engine/SOLO_LIFECYCLE_VALIDATION.json) fixes early cancellation, expired cached drafts and interfering duplicate-route requests, with durable dispatch admission and legacy uncertainty preserved.

[Engine offline responses](engine/OFFLINE_RESPONSES_API.md) now render committed local/Rise actions, phases and received dialogue without an API key or network call. The Engine owns a bundled 338-variant library with 15 mixing recipes, editable player drafts and exact receipt fallback. Supported result APIs include local `presentation` automatically; [Engine-specific qualification](engine/OFFLINE_RESPONSES_VALIDATION.json) records actual execution and remaining App integration.

[Engine continuation/communication APIs](engine/CONTINUATION_COMMUNICATION_API.md) now implement selected phased work/travel/observation, attributed local speech and explicitly fulfilled stock offers, plus reviewed technical charge reconciliation. [Executed task evidence](engine/ENGINE_TASKS_VALIDATION.json) separates Core qualification from new App controls, general C2 mechanics and live/model-quality gates.

For the full runtime suite, use the private-fixture policy runner in DEVELOPMENT.md. The external historical-save fixture is excluded even when present.
