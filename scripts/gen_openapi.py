#!/usr/bin/env python3
"""Write the serve API's OpenAPI schema to ``docs/openapi.json``.

The running server already publishes its schema at ``/openapi.json`` (plus
``/docs`` and ``/redoc``), generated from the code, so that copy can never drift.
This script exists for everyone who needs the contract *without* a running
server — reviewing a change in a diff, generating a client in CI, handing the
spec to an integrator before anything is deployed.

The committed copy is therefore a snapshot, and a stale snapshot is worse than
none: ``tests/test_openapi_spec_is_current.py`` fails the build when this file
and the code disagree, so regenerating is part of changing the API, not an
afterthought.

    python scripts/gen_openapi.py            # rewrite docs/openapi.json
    python scripts/gen_openapi.py --check    # exit 1 if it is out of date
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "docs" / "openapi.json"


def render_spec() -> str:
    """The current schema, serialized the one way the committed copy stores it.

    Keys are sorted so the file is a stable diff: an endpoint added today must
    not reshuffle unrelated lines, or reviewers stop reading the diff.
    """
    sys.path.insert(0, str(REPO_ROOT))
    from cage.target.server.challenge_server import app

    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write; exit 1 if docs/openapi.json is out of date.",
    )
    args = parser.parse_args()

    current = render_spec()
    on_disk = SPEC_PATH.read_text(encoding="utf-8") if SPEC_PATH.is_file() else ""

    if args.check:
        if current == on_disk:
            print(f"up to date: {SPEC_PATH.relative_to(REPO_ROOT)}")
            return 0
        print(
            f"STALE: {SPEC_PATH.relative_to(REPO_ROOT)} does not match the code.\n"
            f"  regenerate with:  python scripts/gen_openapi.py",
            file=sys.stderr,
        )
        return 1

    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(current, encoding="utf-8")
    verb = "unchanged" if current == on_disk else "updated"
    print(f"{verb}: {SPEC_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
