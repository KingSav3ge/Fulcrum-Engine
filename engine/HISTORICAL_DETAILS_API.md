# Historical Details reader — historical-details-01

The Engine can read a complete, pinned multipart historical ZIP through the existing read-only historical-reference API. Catalog owns the original archive bytes and their manifest; App owns selection, Creator/session restrictions and presentation. This reader creates no campaign facts, people, resources, player knowledge, events or saves.

## Contract and dependency status

The Catalog and App work orders for `historical-details-01` were reviewed. At Catalog commit `5c007e16be6ab8930b3bcd4ad10ab320733102a6`, no `IRGS_Catalog/historical_details/` manifest or payload is published. The original archive is also unavailable in this Engine environment. This document defines the implemented reader contract for Catalog/App coordination; compatibility with an actual Catalog delivery and the pinned three-component combination remains unqualified.

The coordinator's expected source identity is 533,064,680 bytes with SHA-256 `51246eb6898a228f42f0794ed19ce69af275a2a4661c0fb6a1d3baebe3efc773`. That is inherited source identity, not a fresh verification or a substitute for the archive. No real part hashes or completed delivery manifest have been invented.

## Manifest v1

Callers supply a manifest path and the SHA-256 of its exact bytes from a reviewed Catalog commit. The manifest is UTF-8 JSON, at most 1 MiB, with unique field names:

```json
{
  "schema_version": 1,
  "display_name": "Historical Details",
  "status": "complete",
  "archive": {
    "name": "IRGS_Historical_Grand_Archive_v1_1.zip",
    "bytes": 533064680,
    "sha256": "51246eb6898a228f42f0794ed19ce69af275a2a4661c0fb6a1d3baebe3efc773"
  },
  "part_size_bytes": 16777216,
  "parts": [
    {"ordinal": 1, "path": "parts/archive.0001", "bytes": 16777216, "sha256": "<actual part SHA-256>"}
  ]
}
```

This is an abbreviated format illustration, not a valid or complete source manifest. The expected source would require 32 actual parts. `status` must be `complete` before records become available. Additional descriptive/source metadata may be retained by Catalog; it does not override byte identity or establish historical truth.

Catalog delivery uses 16 MiB parts. The reader accepts positive declared part sizes up to 16 MiB, allowing small synthetic fixtures, with at most 4,096 parts. Every part except the last must have the declared size; the final size and part count must match the exact original archive size. Ordinals start at one and follow array order. Duplicate ordinals or paths, including case-only path aliases, are refused; the reader never sorts or deduplicates a faulty inventory.

Part paths use portable relative forward-slash names contained beneath the manifest directory. Absolute paths, traversal, empty components, backslashes, drive prefixes and source-directory escapes through links are refused. Archive names are ZIP basenames. All hashes use 64 lowercase hexadecimal characters. A list containing only selected collections is not a complete original archive.

## Engine API

```python
from historical_archive import from_catalog_manifest

library = from_catalog_manifest(
    selected_manifest_path,
    reviewed_manifest_sha256,
    cache_dir=installation_cache_path,
)
status = library.status()
page = library.search('chronology', '1415', offset=0, limit=20)
detail = library.record('chronology', page['results'][0]['row'])
```

The factory validates the pinned manifest; assembly is deferred until a read. `status`, `verify_collections`, `search` and `record` retain the existing ZIP reader interface. Multipart status adds `storage: catalog_parts` and `manifest_sha256`, and uses the title `Historical Details`. `sha256` and source-row reference addresses identify the original archive, preserving identity across ZIP and multipart storage. Search/detail results retain original names, dates, uncertainty, source IDs, citations, rights, duplicate-record boundaries and unresolved source references.

Before exposing records, the reader verifies every part's size, hash and position; reconstructed size and original archive SHA-256; the Grand 1.1 delivery manifest; and all ten supported collection/member hashes. It extracts no archive members and executes no supplied assets. Existing collection size, expanded JSONL and row bounds still apply.

## Installation cache and recovery

The caller explicitly supplies an installation cache outside the Historical Details source directory. For an Engine installation, `.cache/` at the repository root is ignored; an App installation can use its ignored `IRGS_Web/cache/` directory. Neither reconstructed ZIPs nor local attachment configuration belong in source distributions.

Assembly streams in blocks of at most 1 MiB into a new temporary directory. The verified complete directory is renamed atomically to `<cache>/<original_sha256>/archive.zip`. Concurrent readers validate and reuse an already published complete cache rather than replacing its file. A failed attempt removes its own temporary directory and publishes no partial archive. A hard interruption may leave an unreferenced temporary directory; subsequent attempts never read it and can retry independently. The cache is derived data, not a campaign durability mechanism.

Each read rechecks the manifest pin and source-part fingerprints. Changed or missing source parts cause failure even when a complete cache exists. Fingerprints include device, inode, size, modification and change times. Changed inputs undergo byte verification again; new reader instances verify the parts and existing cached ZIP. A corrupt cache is refused; removing that derived cache permits reconstruction from a valid complete source set. The reader does not silently fall back to a different source or local owner path.

## Registration and legacy compatibility

`from_registration(config_path)` continues to accept the existing local ZIP registration unchanged:

```json
{"schema_version": 1, "historical_archive": {"path": "<explicit ZIP path>", "sha256": "<archive SHA-256>"}}
```

An explicit multipart registration uses:

```json
{
  "schema_version": 1,
  "historical_archive": {
    "type": "catalog_parts",
    "manifest_path": "<selected manifest path>",
    "manifest_sha256": "<reviewed manifest SHA-256>",
    "cache_dir": "<installation cache path>"
  }
}
```

Multipart paths may be absolute or relative to the registration file's directory. The reader discovers no Catalog checkout, source archive or private owner directory. App must choose the reviewed manifest and preserve its existing explicit local ZIP option.

## Bounded failure states

`historical_parts.HistoricalPartsError` is a `ValueError` with a stable `.code` and a bounded, path-free display message:

| Code | Meaning |
| --- | --- |
| `unavailable` | Manifest cannot be read or a verification/cache write could not finish; a retry is safe. |
| `incomplete` | Delivery is not marked complete, a part is missing, or the part count cannot reproduce the stated archive size. |
| `invalid_manifest` | Unsupported version, invalid types/bounds, duplicate fields, unsafe paths, duplicate entries or wrong ordering. |
| `corrupt` | A pin, part size/hash, cache, ZIP or required collection binding fails verification, or inputs change during validation. |

App may map `invalid_manifest` to its corrupt/unusable presentation while retaining the diagnostic code. These errors grant no player access or Creator capability. Engine tests cover synthetic assembly, provenance equivalence, cache/retry recovery, source changes and concurrent publication; full dataset and App compatibility require the real Catalog delivery and separate qualification.
