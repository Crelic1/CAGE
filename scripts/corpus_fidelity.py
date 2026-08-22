#!/usr/bin/env python3
"""Check an export against what the model actually received.

The stronger of the two checks in ``scripts/``. ``corpus_parity.py`` compares
against the previous pipeline's output, which catches accidental drift but only
ever proves agreement with an implementation — and that implementation turned
out to be wrong in three places. This one compares against the ground truth: the
request body the proxy recorded on its way upstream, which *is* what the model
was given.

That is the property a training corpus has to have. A row whose prefix differs
from the real inference-time input teaches a context the model will never see
again, and the difference does not have to be large to matter — a separator, a
header line, a dropped reasoning block.

Only rows are checked, not every turn: a row's prefix is exactly one request's
message list, so checking that request answers the question, and checking every
turn is quadratic for no extra coverage.

Assistant turns are compared after rendering the upstream message the way the
exporter would. They are the one place where the row deliberately differs from
the wire — upstream carries structured ``reasoning_content`` and ``tool_calls``,
while the row carries ``<think>…</think>`` and the Qwen/Hermes
``<tool_call><function=…>`` form that a model served through Cage emits and Cage
parses back (``_XML_FUNCTION_RE`` in ``cage/proxy/sidecar.py``). Rendering both
sides the same way is what makes the comparison meaningful; comparing parsed
structures instead is ambiguous, because a tool argument that *is* a JSON string
parses back into a list.

    python3 scripts/corpus_fidelity.py --runs /path/.cage_runs -n 25
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cage.corpus.build import BuildOptions, build_segments, iter_entries  # noqa: E402
from cage.corpus.render import tool_call_xml  # noqa: E402


def _translated(entry: dict) -> bool:
    """Did this call carry a separate upstream body to compare against?

    True only on the Anthropic→OpenAI translation path. A passthrough forwards
    the agent's own body, so comparing would be comparing with itself.
    """

    request = entry.get("openai_request") or {}
    messages = request.get("messages") or []
    return bool(entry.get("anthropic_request")) and any(
        isinstance(m, dict) and m.get("role") == "system" for m in messages
    )


def _render_upstream_assistant(message: dict) -> str:
    segments: list[str] = []
    reasoning = (message.get("reasoning_content") or message.get("reasoning") or "").strip()
    if reasoning:
        segments.append(f"<think>\n{reasoning}\n</think>")
    text = message.get("content")
    if isinstance(text, str) and text.strip():
        segments.append(text.strip())
    for call in message.get("tool_calls") or []:
        if not isinstance(call, dict):
            continue
        function = call.get("function") or {}
        arguments = function.get("arguments") or "{}"
        try:
            parsed = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            parsed = {"raw": arguments}
        segments.append(tool_call_xml(function.get("name") or "", parsed))
    return "\n\n".join(segments).strip()


def _where(a: str, b: str) -> str:
    at = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    return (
        f"at char {at} (len {len(a)} vs {len(b)})\n"
        f"      upstream: {a[max(0, at - 70):at + 70]!r}\n"
        f"      exported: {b[max(0, at - 70):at + 70]!r}"
    )


def check_trial(
    proxy: Path,
    options: BuildOptions,
    verdict: collections.Counter,
    failures: list[str],
    label: str,
) -> None:
    segments, _problems = build_segments(proxy, options)
    if not segments:
        verdict["trial exports no rows"] += 1
        return
    # Keyed by the call each row came from. Message counts repeat within a
    # trial, so matching on those compares a row against some other call's body
    # and reports a difference in the per-call billing nonce that is entirely an
    # artefact of the mismatch.
    pending = {s.stats["source_call_index"]: s for s in segments}

    for index, entry in iter_entries(proxy):
        if not pending:
            break
        segment = pending.pop(index, None)
        if segment is None:
            continue
        if not _translated(entry):
            verdict["row from a passthrough call (no separate upstream body)"] += 1
            continue
        upstream = entry["openai_request"]["messages"]
        if len(upstream) != len(segment.messages) - 1:
            verdict["message count differs"] += 1
            failures.append(
                f"{label}: {len(upstream)} upstream vs {len(segment.messages) - 1} exported"
            )
            continue
        exported = segment.messages[:-1]

        ok = True
        for i, (up, mine) in enumerate(zip(upstream, exported)):
            role = up.get("role")
            if role != mine.get("role"):
                verdict["role differs"] += 1
                failures.append(f"{label} msg[{i}]: {role} vs {mine.get('role')}")
                ok = False
                break
            if role == "assistant":
                a, b = _render_upstream_assistant(up), (mine.get("content") or "").strip()
            else:
                a, b = up.get("content") or "", mine.get("content") or ""
            if a != b:
                verdict[f"{role} content differs"] += 1
                failures.append(f"{label} msg[{i}] role={role} differs {_where(a, b)}")
                ok = False
                break
        if ok:
            verdict["row matches what the model received"] += 1

    for _ in pending:
        verdict["row's source call not found in the log"] += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("-n", type=int, default=25, help="trials to check")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--splitter", default="forest")
    args = ap.parse_args()

    trials = sorted(Path(args.runs).glob("*/*/trials/*/proxy/proxy.jsonl"))
    random.Random(args.seed).shuffle(trials)
    trials = trials[: args.n]

    options = BuildOptions(splitter=args.splitter)
    verdict: collections.Counter = collections.Counter()
    failures: list[str] = []
    for proxy in trials:
        label = f"{proxy.parents[3].name}/{proxy.parents[1].name}"
        try:
            check_trial(proxy, options, verdict, failures, label)
        except Exception as exc:  # noqa: BLE001
            verdict[f"raised {type(exc).__name__}"] += 1
            failures.append(f"{label}: {exc}")

    print(f"checked {len(trials)} trials against the body the proxy sent upstream")
    for key, count in verdict.most_common():
        print(f"  {count:7d}  {key}")
    if failures:
        print(f"\nfirst {min(len(failures), 6)} failures:")
        for line in failures[:6]:
            print(f"  - {line}")
    bad = sum(v for k, v in verdict.items() if "differs" in k or "raised" in k)
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
