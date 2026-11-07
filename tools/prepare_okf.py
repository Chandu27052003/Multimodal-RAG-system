"""Prepare one JSON preprocessing request per OKF concept on stdout."""

import argparse
import json
from pathlib import Path
import sys

from shared.okf import OKFError, load_bundle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Local OKF bundle directory")
    parser.add_argument("--bundle-id", required=True, help="Stable, unique bundle namespace")
    args = parser.parse_args(argv)
    try:
        requests = [c.preprocessing_request(args.bundle_id) for c in load_bundle(args.bundle)]
        # Validate the whole bundle before emitting any JSON records.
        output = "".join(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n" for r in requests)
    except (OKFError, OSError) as exc:
        print(f"OKF preparation failed: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
