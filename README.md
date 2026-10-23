# IRGS Engine

IRGS develops a persistent world simulation connecting individual action, institutions, resources and history. Its design centers on one shared world, actions constrained by actual authority and resources, and information received by the acting character or institution. See the [Engine model](engine/ENGINE_MODEL.md) for these principles and their current implementation limits.

Independent Engine development for IRGS, selected Core 3.3. This repository owns `IRGS_3_3/`, the applied design under `engine/`, Engine milestones and source provenance. The App develops separately in [IRGS-APP-WEB](https://github.com/KingSav3ge/IRGS-APP-WEB); [IRGS/main](https://github.com/KingSav3ge/IRGS) joins both components.

Publish Engine updates to **KingSav3ge/IRGS-Engine**, on its `main` branch. The [development roadmap](ROADMAP.md) separates completed work, work in progress and remaining work; the [DEV checklist](DEVELOPMENT_LIST.md) supplies task IDs and completion criteria, and the [continuation log](CONTINUATION_STATUS.md) records delivered increments and verification limits. Update these records as Engine work progresses.

```bash
python -B tools/verify_components.py --component engine
python -B -m unittest discover -s IRGS_3_3/runtime -v
python -B tools/refresh_component_releases.py --component engine
```

Core verification and tests require no App checkout. Python 3.12+ is required; do not use `-O`. Run `python -B IRGS_3_3/catalog/campaigns/kira/verify_kira.py` for Kira canon/archive consistency. Historical external-save tests can explicitly skip absent private fixtures; use only synthetic temporary saves.

Engine source pins are in `IRGS_3_3/release.json`; App pins belong to its repository. Refresh pins after intentional edits, execute meaningful runtime checks, then commit/push `main`. Do not change rules merely to match an imported proposal. General C2 completion remains work; bounded handlers and 37 dated Century starts do not qualify a complete historical simulation.

The App pins an Engine commit through its `Engine` submodule. Qualify the pair before updating that pointer or joined IRGS. See [joined integration instructions](https://github.com/KingSav3ge/IRGS/blob/main/COMPONENT_REPOSITORIES.md). Historical operation/evidence documents retain the source identities of their original joined runs; they are not fresh standalone or all-branch certification.

Kira v0.5 is adopted working setting canon, with a [six-region illustrated atlas and regional foundations](IRGS_3_3/catalog/campaigns/kira/atlas/README.md) beside its worldbook. It initializes no player, resources, numerical magic rules or future outcomes. Source/provenance archives remain labelled historical material. No user saves are included or migrated.

The [Historical Details reader contract](engine/HISTORICAL_DETAILS_API.md) supports pinned multipart archives and existing explicit ZIP attachments. Catalog's real 32-part delivery and ten reader collections are verified. Catalog owns the full payload; App owns Creator browsing and its reviewed dependency pins. Connected App/joined qualification remains separate.

**IRGS 3.4.0 — in development:** the [Solo provider/action API](engine/SOLO_PROVIDER_API.md) now supplies disabled-by-default scoped proposals, durable technical accounting and explicit acceptance through existing local/Rise Core handlers. The [direct OpenAI adapter](engine/OPENAI_ADAPTER_REVIEW.md) is opt-in and tested with synthetic HTTP; [Catalog R00 execution](engine/SOLO_CATALOG_VALIDATION.json) qualifies ten offline cases. No live inference, model-quality winner or new joined release is claimed. Broader work remains in the [AI provider plan](engine/AI_PROVIDER_PLAN.md).
