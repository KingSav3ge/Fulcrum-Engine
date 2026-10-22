"""Qualify an explicitly pinned Catalog archive using only the Engine reader."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'IRGS_3_3/runtime'))
from historical_archive import from_catalog_manifest
from historical_parts import HistoricalPartsError


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--manifest-sha256', required=True)
    parser.add_argument('--cache-dir', required=True, type=Path)
    args = parser.parse_args()
    try:
        library = from_catalog_manifest(args.manifest, args.manifest_sha256, cache_dir=args.cache_dir)
        result = library.verify_delivery()
    except HistoricalPartsError as exc:
        print(json.dumps({'status': exc.code, 'error': str(exc)}))
        return 2
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print(json.dumps({'status': 'unavailable_or_invalid', 'error': type(exc).__name__}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
