#!/usr/bin/env python3
"""Byte-compare ``cage.corpus`` output against the scripts it replaces.

The reference is not a re-run of the old code but its *shipped product*: the
trajectory files the previous pipeline wrote. Comparing against those catches
accidental drift across the whole chain.

It is the weaker of the two checks here, and the reason is worth stating: this
only ever proves agreement with an implementation, and that implementation is
now known to have been wrong in three places (below). ``corpus_fidelity.py``
compares against what the model actually received, which is the property a
training corpus needs. Use this one to notice unintended change; use that one
to know the corpus is right.

    python3 scripts/corpus_parity.py --store /path/traj_store --runs /path/.cage_runs -n 50
"""

from __future__ import annotations

import argparse
import collections
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cage.corpus.build import BuildOptions, build_segments  # noqa: E402


def load_manifest(store: Path) -> list[dict]:
    rows = []
    for line in (store / "manifest.jsonl").read_text(errors="replace").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def find_trial(runs_root: Path, run_id: str, trial_id: str) -> Path | None:
    for slot in runs_root.iterdir():
        candidate = slot / run_id / "trials" / trial_id
        if candidate.is_dir():
            return candidate
    return None


# Three deliberate deviations from the scripts this replaces. Normalised here so
# the comparison stays honest about what it proves — everything else is
# byte-identical — rather than quietly passing or noisily failing.
#
#  1/2. The reference stripped Claude Code's billing header and rewrote the
#       model identity line. The exporter edits neither: both were in what the
#       agent sent, and deciding they do not belong in a training set is the mix
#       owner's call.
#    3. The reference joined a user turn's text blocks with "\n\n". The
#       Anthropic→OpenAI translator joins them with "\n" before sending them
#       upstream, so "\n\n" is a separator the model never saw.
_BILLING = re.compile(r"^x-anthropic-billing-header:[^\n]*\n?", re.M)
_IDENTITY = re.compile(r"You are powered by (?:the model[^\n]*|a large language model\.[^\n]*)")


def _normalize_system(text: str) -> str:
    text = _BILLING.sub("", text)
    return _IDENTITY.sub("<identity>", text).strip()


def _normalize_user(text: str) -> str:
    """Collapse the block separator so only real content differences show."""

    return re.sub(r"\n{2,}", "\n", text)


def compare(reference: list[dict], produced: list[dict]) -> str:
    if len(reference) != len(produced):
        return f"message count {len(reference)} != {len(produced)}"
    for i, (a, b) in enumerate(zip(reference, produced)):
        if a.get("role") != b.get("role"):
            return f"msg[{i}] role {a.get('role')} != {b.get('role')}"
        if a.get("loss") != b.get("loss"):
            return f"msg[{i}] loss {a.get('loss')} != {b.get('loss')}"
        ac, bc = a.get("content") or "", b.get("content") or ""
        if a.get("role") == "system":
            ac, bc = _normalize_system(ac), _normalize_system(bc)
        elif a.get("role") == "user":
            ac, bc = _normalize_user(ac), _normalize_user(bc)
        if ac != bc:
            at = next((k for k in range(min(len(ac), len(bc))) if ac[k] != bc[k]), min(len(ac), len(bc)))
            return (
                f"msg[{i}] role={a.get('role')} content differs at char {at} "
                f"(len {len(ac)} vs {len(bc)})\n"
                f"      ref: {ac[max(0, at - 60):at + 60]!r}\n"
                f"      new: {bc[max(0, at - 60):at + 60]!r}"
            )
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--splitter", default="system_prompt")
    ap.add_argument("--compacted-only", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    store, runs_root = Path(args.store), Path(args.runs)
    rows = [r for r in load_manifest(store) if r.get("admitted") and r.get("path")]
    if args.compacted_only:
        rows = [r for r in rows if r.get("compacted")]

    by_trial: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_trial[(row["run_id"], row["trial_id"])].append(row)

    keys = sorted(by_trial)
    random.Random(args.seed).shuffle(keys)
    keys = keys[: args.n]

    verdict = collections.Counter()
    failures: list[str] = []
    for run_id, trial_id in keys:
        trial_dir = find_trial(runs_root, run_id, trial_id)
        if trial_dir is None:
            verdict["trial gone"] += 1
            continue
        proxy = trial_dir / "proxy" / "proxy.jsonl"
        if not proxy.is_file():
            verdict["proxy gone"] += 1
            continue

        try:
            segments, problems = build_segments(
                proxy, BuildOptions(splitter=args.splitter)
            )
        except Exception as exc:  # noqa: BLE001
            verdict["build raised"] += 1
            failures.append(f"{run_id}/{trial_id}: raised {type(exc).__name__}: {exc}")
            continue

        expected = sorted(by_trial[(run_id, trial_id)], key=lambda r: r.get("segment", 0))
        if len(segments) != len(expected):
            verdict["segment count differs"] += 1
            failures.append(
                f"{run_id}/{trial_id}: {len(expected)} reference segments, "
                f"{len(segments)} produced (problems: {problems})"
            )
            continue

        trial_ok = True
        for row, segment in zip(expected, segments):
            reference = json.loads((store / row["path"]).read_text(errors="replace"))
            diff = compare(reference["messages"], segment.messages)
            if diff:
                trial_ok = False
                verdict["messages differ"] += 1
                failures.append(f"{run_id}/{trial_id}#{row.get('segment')}: {diff}")
                break
            if reference.get("tools") != segment.tools:
                trial_ok = False
                verdict["tools differ"] += 1
                failures.append(f"{run_id}/{trial_id}#{row.get('segment')}: tools differ")
                break
        if trial_ok:
            verdict["identical"] += 1
            if problems:
                verdict["identical (with new-check problems)"] += 1

    print(f"compared {len(keys)} trials (splitter={args.splitter})")
    for key, count in verdict.most_common():
        print(f"  {count:5d}  {key}")
    if failures:
        print(f"\nfirst {min(len(failures), 10)} failures:")
        for line in failures[:10]:
            print(f"  - {line}")
    return 0 if verdict["identical"] == len(keys) else 1


if __name__ == "__main__":
    sys.exit(main())
