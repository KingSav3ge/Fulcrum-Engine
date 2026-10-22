# IRGS Engine

Independent Engine development for IRGS, selected Core 3.3. This repository owns `IRGS_3_3/`, the applied design under `engine/`, Engine milestones and source provenance. The App develops separately in [IRGS-APP-WEB](https://github.com/KingSav3ge/IRGS-APP-WEB); [IRGS/main](https://github.com/KingSav3ge/IRGS) joins both components.

```bash
python -B tools/verify_components.py --component engine
python -B -m unittest discover -s IRGS_3_3/runtime -v
python -B tools/refresh_component_releases.py --component engine
```

Core verification and tests require no App checkout. Python 3.12+ is required; do not use `-O`. Run `python -B IRGS_3_3/catalog/campaigns/kira/verify_kira.py` for Kira canon/archive consistency. Historical external-save tests can explicitly skip absent private fixtures; use only synthetic temporary saves.

Engine source pins are in `IRGS_3_3/release.json`; App pins belong to its repository. Refresh pins after intentional edits, execute meaningful runtime checks, then commit/push `main`. Do not change rules merely to match an imported proposal. General C2 completion remains work; bounded handlers and 37 dated Century starts do not qualify a complete historical simulation.

The App pins an Engine commit through its `Engine` submodule. Qualify the pair before updating that pointer or joined IRGS. See [joined integration instructions](https://github.com/KingSav3ge/IRGS/blob/main/COMPONENT_REPOSITORIES.md). Historical operation/evidence documents retain the source identities of their original joined runs; they are not fresh standalone or all-branch certification.

Kira v0.5 is adopted working setting canon. It initializes no player, resources, numerical magic rules or future outcomes. Source/provenance archives remain labelled historical material. No user saves are included or migrated.
