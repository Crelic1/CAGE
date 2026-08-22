"""The committed OpenAPI schema must match the code that serves it.

A running server publishes its schema from the code (`/openapi.json`, `/docs`,
`/redoc`), so that copy cannot drift. The committed `docs/openapi.json` is a
snapshot for everyone without a running server — reviewers reading a diff, CI
generating a client, an integrator handed the contract before deployment — and a
stale snapshot is worse than none, because it is trusted and wrong. This test is
what keeps regenerating it part of changing the API.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = REPO_ROOT / "docs" / "openapi.json"


def test_committed_spec_matches_the_app():
    sys.path.insert(0, str(REPO_ROOT))
    from cage.target.server.challenge_server import app

    expected = json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert SPEC_PATH.is_file(), f"{SPEC_PATH} is missing — run scripts/gen_openapi.py"
    actual = SPEC_PATH.read_text(encoding="utf-8")
    if actual != expected:
        live = json.loads(expected)
        stored = json.loads(actual)
        added = sorted(set(live["paths"]) - set(stored["paths"]))
        removed = sorted(set(stored["paths"]) - set(live["paths"]))
        raise AssertionError(
            "docs/openapi.json is out of date — regenerate with "
            "`python scripts/gen_openapi.py`.\n"
            f"  paths only in the code: {added or 'none'}\n"
            f"  paths only in the file: {removed or 'none'}"
        )


def test_generator_check_mode_agrees():
    """`--check` is what CI would call; it must reach the same verdict."""
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "gen_openapi.py"), "--check"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_spec_is_environment_independent():
    """Regenerating must not depend on whether cage is pip-installed.

    ``info.version`` is the API contract's version, not the distribution's —
    binding it to the installed package made the snapshot differ between a dev
    checkout and a deployed host, which would make this whole check flaky.
    """
    from cage.target.server.challenge_server import SERVE_API_VERSION

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["info"]["version"] == SERVE_API_VERSION
    assert "unknown" not in spec["info"]["version"]


def test_spec_documents_the_endpoints_external_callers_drive():
    """The published contract must cover the whole PULL loop, not a subset."""
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    for path in ("/challenges", "/launches", "/prompt/{run_id}",
                 "/submit/{run_id}", "/rescores", "/rescores/{run_id}"):
        assert path in spec["paths"], f"{path} missing from the published spec"


def test_challenge_summary_publishes_the_scoring_denominator():
    """A caller must be able to read the denominator straight from the spec."""
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    props = spec["components"]["schemas"]["ChallengeSummary"]["properties"]
    assert "objective_count" in props and "objective_kind" in props


# --- the hand-written reference ---------------------------------------------- #
# docs/serve-api.md explains what each field MEANS, which no generator can do —
# so it is written by hand, and hand-written docs rot silently. These keep it
# honest: add a field to the contract without explaining it and the build fails.

REFERENCE_PATH = REPO_ROOT / "docs" / "serve-api.md"

# FastAPI's own validation envelopes and the multipart body wrapper are
# machinery, not contract an integrator reasons about.
_INTERNAL_SCHEMAS = {
    "HTTPValidationError",
    "ValidationError",
    "Body_submit_challenge_submit__run_id__post",
}


def _reference_text() -> str:
    assert REFERENCE_PATH.is_file(), f"{REFERENCE_PATH} is missing"
    return REFERENCE_PATH.read_text(encoding="utf-8")


def test_every_published_field_is_explained():
    import re

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    doc = _reference_text()
    undocumented = [
        f"{name}.{field}"
        for name, schema in spec["components"]["schemas"].items()
        if name not in _INTERNAL_SCHEMAS
        for field in schema.get("properties", {})
        if not re.search(rf"`{re.escape(field)}`", doc)
    ]
    assert not undocumented, (
        "these response/request fields are in the API but not explained in "
        f"docs/serve-api.md: {undocumented}"
    )


def test_every_endpoint_is_documented():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    doc = _reference_text()
    missing = [p for p in spec["paths"] if p not in doc]
    assert not missing, f"endpoints missing from docs/serve-api.md: {missing}"


def test_the_reference_invents_no_types():
    """Guard the other direction: a documented type must actually exist."""
    import re

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    real = set(spec["components"]["schemas"])
    suffixes = ("Response", "Summary", "Result", "Status", "Request", "Error", "Info", "Url")
    referenced = {
        n for n in re.findall(r"`(\w+)\[?\]?`", _reference_text())
        if n.endswith(suffixes)
    }
    invented = sorted(referenced - real)
    assert not invented, f"docs/serve-api.md names types that do not exist: {invented}"
