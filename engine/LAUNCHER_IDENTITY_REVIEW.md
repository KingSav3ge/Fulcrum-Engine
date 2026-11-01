# Launcher build identity — Engine review candidate

Status: **source candidate; no launcher fixture has been executed**.
Published Engine base `ecca8094a2d2cdb8a11e018a085487288b26e88d`;
joined 3.4.8 pins App `c04ba5524ae95316c7e826fc63085a4916d7dd67`
and Catalog `a18cb48928da25d40d057a182c69f71ef149ce80`.

## Behavior under review

The Engine launcher formerly accepted any loopback listener returning an
IRGS-shaped Core catalog and a session token. It now obtains the installed
selection through the existing App `build_identity.running_build()` interface.
The launcher checks the schema, edition, classification and all six existing
App, Engine and Catalog manifest/source SHA-256 fingerprints against the
running host's startup snapshot from `/api/campaigns`. Missing or malformed
identity is not a match. It separately checks the selected Engine manifest and
Core hashes against this launcher's suite, so an unintended Engine override is
not silently accepted. The Engine release verification still runs before reuse
or launch. These public fingerprints identify selected files; they are not
cryptographic proof of process ownership or full component integrity.

A matching healthy host remains eligible for reuse. A mismatched, unidentified,
unrelated or inconclusively probed listener is left running and produces an
alternate-port instruction. Only a connection-refused result is treated as a
free port. The selected local identity and host state are checked again after
verification and immediately before reuse or acknowledging a new host. The
launcher never sends a shutdown signal. This does not introduce a new host
authority, change API routes, or claim protection against a malicious local
process that fabricates the same public fingerprints.

## Checks required before adoption

`IRGS_3_3/runtime/test_launcher_build_identity.py` contains nine synthetic
loopback fixture cases: exact reuse, each individual changed fingerprint,
edition/schema/classification mismatch, missing/null/malformed identity,
unrelated or incomplete health, occupied-listener preservation, a free port,
selected-build calculation and Engine-root mismatch, and an optional actual
pinned App metadata check. These tests have not run in the owner environment.

- Run `python -B tools/verify_components.py --component engine` and the
  safe-fixture runtime suite at the exact review commit.
- The fixture class is skipped unless PowerShell exists and
  `IRGS_LAUNCHER_TEST_POLICY_ALLOWED=1` is explicitly set in an environment
  where running the script is already permitted. To exercise the actual selected
  App metadata as well, point `IRGS_TEST_APP_ROOT` at the pinned App's
  `IRGS_Web` directory and set its normal Engine/Catalog selection variables.
  These are test selections, not policy overrides. The fixture invokes PowerShell
  without execution-policy switches.
- The Windows relay's earlier dot-source attempt was denied **before any HTTP
  fixture request**. Do not retry or route around that denial without a
  supported change that permits it. No Linux result qualifies native Windows.
- App's published `IRGS_Web/tests/test_launcher.py` has older fixtures that
  omit the build snapshot and use an execution-policy bypass. The App owner
  must update those fixtures and run them only where execution is permitted;
  this Engine candidate does not change App source or authorize that bypass.

Owner-local checkout parity is unknown. Later restoration must reconcile
unique old work. No test pass, release, 5.0 qualification, or main-branch
publication is claimed by this review candidate.
