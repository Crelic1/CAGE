"""``cage corpus`` — export recorded trajectories as training data."""

from __future__ import annotations

import collections
import itertools
import json
from pathlib import Path

import click

from cage.artifacts.run_storage import discover_runs, is_trial_dir
from cage.contracts.style import style


def _roots(root: tuple[str, ...]) -> list[Path]:
    if root:
        return [Path(r).expanduser().resolve() for r in root]
    from cage.gc.runner import default_cage_runs_roots

    return default_cage_runs_roots()


def _parse_where(pairs: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    out: list[tuple[str, str]] = []
    for pair in pairs:
        if "=" not in pair:
            raise click.BadParameter(f"expected key=value, got {pair!r}", param_hint="--where")
        key, value = pair.split("=", 1)
        out.append((key.strip(), value.strip()))
    return tuple(out)


def _selection(**kwargs) -> "Selection":  # noqa: F821
    from cage.corpus.export import Selection

    return Selection(
        run_ids=tuple(kwargs.get("run") or ()),
        run_globs=tuple(kwargs.get("run_glob") or ()),
        benchmarks=tuple(kwargs.get("benchmark") or ()),
        agents=tuple(kwargs.get("agent") or ()),
        models=tuple(kwargs.get("model") or ()),
        served_models=tuple(kwargs.get("served_model") or ()),
        tasks=tuple(kwargs.get("task") or ()),
        passed=kwargs.get("passed"),
        allow=frozenset(kwargs.get("allow") or ()),
        where=_parse_where(tuple(kwargs.get("where") or ())),
        compacted=kwargs.get("compacted"),
        first_segment_only=bool(kwargs.get("first_segment_only")),
        segment=kwargs.get("segment"),
        min_turns=kwargs.get("min_turns"),
        max_turns=kwargs.get("max_turns"),
        think_ratio_min=kwargs.get("think_ratio_min"),
        per_task_cap=kwargs.get("per_task_cap"),
        limit=kwargs.get("limit"),
        sample=kwargs.get("sample"),
        seed=kwargs.get("seed", 0),
    )


def _filter_options(fn):
    """The filters shared by ``export`` and ``gates``.

    Split by layer. The framework's own filters are named flags because the
    framework knows what a run, an agent or a pass is. A benchmark's rules reach
    the same command through two generic knobs — ``--allow`` for its gate codes
    and ``--where`` for its provenance keys — because the framework must not
    learn the name of any one domain's rule.
    """

    options = [
        click.option("--run", multiple=True, help="Run id. Repeatable."),
        click.option("--run-glob", multiple=True, help="Run id glob, e.g. 'boyue-*-20260801'."),
        click.option("--benchmark", multiple=True, help="Benchmark dir name. Repeatable."),
        click.option("--agent", multiple=True, help="Agent code, e.g. claude_code."),
        click.option("--model", multiple=True, help="Model slot label. Repeatable."),
        click.option("--served-model", multiple=True, help="Model name the endpoint reported."),
        click.option("--task", multiple=True, help="Task or trial id. Repeatable."),
        click.option(
            "--passed/--failed",
            "passed",
            default=None,
            help="Keep only solved / only unsolved trials. Default: both.",
        ),
        click.option(
            "--allow",
            multiple=True,
            metavar="CODE",
            help="Release a benchmark admission gate by its code "
            "(see `cage corpus gates`). Repeatable.",
        ),
        click.option(
            "--where",
            multiple=True,
            metavar="KEY=VALUE",
            help="Match a benchmark provenance field, e.g. --where difficulty=level1.",
        ),
        click.option(
            "--compacted/--no-compacted",
            "compacted",
            default=None,
            help="Keep only rows that do / do not come from a compacted trial.",
        ),
        click.option(
            "--first-segment-only",
            is_flag=True,
            help="Only the segment that starts from the real task, not from a summary.",
        ),
        click.option("--segment", type=int, default=None, help="Keep only this segment index."),
        click.option("--min-turns", type=int, default=None, help="Minimum assistant turns."),
        click.option("--max-turns", type=int, default=None, help="Maximum assistant turns."),
        click.option(
            "--think-ratio-min",
            type=float,
            default=None,
            help="Minimum fraction of supervised turns carrying reasoning.",
        ),
        click.option("--per-task-cap", type=int, default=None, help="Max rows per task."),
        click.option("--limit", type=int, default=None, help="Stop after N rows."),
        click.option(
            "--root",
            multiple=True,
            type=click.Path(),
            help="Where to look for .cage_runs. Default: auto-discovered.",
        ),
        click.option(
            "--repair-think-tags",
            is_flag=True,
            help="Prepend the <think> tag a chat template counted as prompt, so the "
            "tags pair. Off by default: a model whose reasoning arrives inline emits "
            "only the closing tag, and that is what it produced.",
        ),
        click.option(
            "--strip-director",
            is_flag=True,
            help="Remove hint blocks Cage's director injected. Off by default: the "
            "agent really received them, and an export that removes them quietly "
            "has made a training decision on the consumer's behalf.",
        ),
        click.option(
            "--strip-billing-header",
            is_flag=True,
            help="Remove Claude Code's per-call x-anthropic-billing-header line from "
            "the system prompt. Off by default — the agent really sent it.",
        ),
        click.option(
            "--drop-compaction-call/--no-drop-compaction-call",
            "drop_compaction_call",
            default=True,
            show_default=True,
            help="Drop the turn where the harness asked for a context summary. "
            "That turn is bookkeeping, not the agent's work; the summary itself "
            "still appears as input at the head of the next segment. Keep it to "
            "train summarisation.",
        ),
        click.option(
            "--splitter",
            type=click.Choice(["forest", "system_prompt"]),
            default="forest",
            show_default=True,
            help="How main-agent turns and compaction boundaries are identified. "
            "'forest' reconstructs the delegation tree; 'system_prompt' reproduces "
            "the older message-count heuristic, which mistakes a harness's one-shot "
            "auxiliary calls for compaction boundaries. Use it only to reproduce an "
            "existing corpus byte-for-byte.",
        ),
    ]
    for option in reversed(options):
        fn = option(fn)
    return fn


@click.group("corpus")
def corpus_group() -> None:
    """Export recorded trajectories as training data.

    A row is one complete conversation, taken verbatim from what the model
    actually received, with every assistant turn supervised. A trial produces
    more than one row only where the harness compacted its context.

    Start with `cage corpus runs` to see what is available, then `cage corpus
    export --dry-run` to see what a set of filters would yield before writing
    anything.
    """


@corpus_group.command("runs")
@click.option("--root", multiple=True, type=click.Path(), help="Where to look for .cage_runs.")
@click.option("--glob", "run_glob", default="", help="Only runs whose id matches this glob.")
def runs_cmd(root: tuple[str, ...], run_glob: str) -> None:
    """List the runs a corpus could be exported from."""

    import fnmatch

    rows = []
    for base in _roots(root):
        for ref in discover_runs(base):
            if run_glob and not fnmatch.fnmatch(ref.run_id, run_glob):
                continue
            trials = ref.run_dir / "trials"
            n = sum(1 for p in trials.iterdir() if is_trial_dir(p)) if trials.is_dir() else 0
            rows.append((ref.benchmark, ref.agent, ref.model, ref.run_id, n))
    if not rows:
        click.echo("no runs found")
        return
    rows.sort(key=lambda r: (r[0], r[3]))
    click.echo(f"{'benchmark':<14}{'agent':<14}{'model':<26}{'trials':>7}  run")
    for benchmark, agent, model, run_id, n in rows:
        click.echo(f"{benchmark:<14}{agent:<14}{model:<26}{n:>7}  {run_id}")
    click.echo(f"\n{len(rows)} runs")


@corpus_group.command("gates")
@_filter_options
@click.option("--sample-trials", type=int, default=200, show_default=True,
              help="How many trials to probe per run.")
def gates_cmd(sample_trials: int, **kwargs) -> None:
    """Show which admission gates the selected runs' benchmark defines, and what they catch.

    Gate codes are the benchmark's own. This command asks it rather than listing
    anything the framework knows, so a new benchmark's rules show up here with
    no framework change.
    """

    from cage.corpus.export import _load_benchmark_for_run
    from cage.corpus.records import TrialCorpusView

    selection = _selection(**kwargs)
    counts: collections.Counter = collections.Counter()
    detail: dict[str, str] = {}
    provenance_keys: collections.Counter = collections.Counter()
    seen = 0

    for base in _roots(tuple(kwargs.get("root") or ())):
        for ref in discover_runs(base):
            if not selection.matches_run(ref):
                continue
            benchmark = _load_benchmark_for_run(ref)
            if benchmark is None:
                continue
            trials = ref.run_dir / "trials"
            if not trials.is_dir():
                continue
            for trial_dir in itertools.islice(
                sorted(p for p in trials.iterdir() if is_trial_dir(p)), sample_trials
            ):
                view = TrialCorpusView(
                    trial_dir=trial_dir, run_dir=ref.run_dir, trial_id=trial_dir.name,
                    run_id=ref.run_id, benchmark=ref.benchmark, agent=ref.agent, model=ref.model,
                )
                try:
                    admission = benchmark.admit_for_training(view)
                except Exception:
                    continue
                seen += 1
                for code in admission.reasons:
                    counts[code] += 1
                    if code in admission.detail and code not in detail:
                        detail[code] = admission.detail[code]
                for key in admission.provenance:
                    provenance_keys[key] += 1

    if not seen:
        click.echo("no trials probed (no runs matched, or no benchmark could be loaded)")
        return
    click.echo(f"probed {seen} trials\n")
    click.echo(style("gate codes  (release with --allow <code>)", "bold"))
    if counts:
        for code, n in counts.most_common():
            click.echo(f"  {n:>7}  {code}")
            if code in detail:
                click.echo(f"           {detail[code]}")
    else:
        click.echo("  (none fired)")
    click.echo("\n" + style("provenance keys  (filter with --where <key>=<value>)", "bold"))
    for key, n in provenance_keys.most_common():
        click.echo(f"  {n:>7}  {key}")


@corpus_group.command("export")
@_filter_options
@click.option("--out", type=click.Path(), default="", help="Output .jsonl (or dir with --split-by).")
@click.option(
    "--split-by",
    type=click.Choice(["run", "model"]),
    default=None,
    help="Write one file per run or per model into --out as a directory.",
)
@click.option("--sample", type=int, default=None, help="Uniformly sample N rows from the result.")
@click.option("--seed", type=int, default=0, show_default=True, help="Sampling seed.")
@click.option("--dry-run", is_flag=True, help="Report what would be written; write nothing.")
@click.option("--report", type=click.Path(), default="", help="Write the tally here as JSON.")
def export_cmd(
    out: str, split_by: str | None, sample: int | None, seed: int, dry_run: bool, report: str, **kwargs
) -> None:
    """Export the selected runs' trajectories as training rows.

    Only the benchmark's contamination gates apply by default: everything a run
    collected that is safe to learn from comes out, solved and unsolved alike.
    Every filter beyond that is opt-in, and everything dropped is counted in the
    report — an export that quietly returns less than was asked for is worse
    than one that refuses.
    """

    from cage.corpus.build import BuildOptions
    from cage.corpus.export import Tally, iter_rows, reservoir_sample, write_jsonl

    if not dry_run and not out:
        raise click.UsageError("--out is required unless --dry-run is given")

    selection = _selection(**kwargs, sample=sample, seed=seed)
    build_options = BuildOptions(
        splitter=kwargs.get("splitter") or "forest",
        drop_compaction_call=bool(kwargs.get("drop_compaction_call", True)),
        strip_director=bool(kwargs.get("strip_director")),
        strip_billing_header=bool(kwargs.get("strip_billing_header")),
        repair_think_tags=bool(kwargs.get("repair_think_tags")),
    )
    tally = Tally()

    def rows():
        for base in _roots(tuple(kwargs.get("root") or ())):
            yield from iter_rows(base, selection, build_options, tally)

    written: dict[str, int] = {}
    if dry_run:
        for _ in rows():
            pass
    elif sample is not None:
        picked = reservoir_sample(rows(), sample, seed)
        tally.rows = len(picked)
        written = write_jsonl(iter(picked), Path(out), split_by or "", tally)
    else:
        written = write_jsonl(rows(), Path(out), split_by or "", tally)

    _print_tally(tally, written, dry_run)
    if report:
        payload = tally.as_dict()
        payload["files"] = written
        Path(report).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        click.echo(f"\nreport -> {report}")


def _print_tally(tally, written: dict[str, int], dry_run: bool) -> None:
    click.echo(
        f"\nruns {tally.runs}   trials scanned {tally.trials_seen}   "
        f"trials used {tally.trials_kept}   rows {tally.rows}"
    )
    if tally.rows:
        click.echo(
            f"unique tasks {len(tally.tasks)}   from compacted trials {tally.compacted_rows}   "
            f"opening from a summary {tally.summary_opened_rows}"
        )
        if tally.director_hint_rows:
            click.echo(
                f"⚠ {tally.director_hint_rows} rows carry a director hint Cage "
                f"injected (kept verbatim; --strip-director removes them)"
            )
    if tally.gates:
        click.echo("\nrefused by benchmark gates (release with --allow <code>):")
        for code, n in tally.gates.most_common():
            click.echo(f"  {n:>7}  {code}")
    if tally.filters:
        click.echo("\ndropped by filters:")
        for name, n in tally.filters.most_common():
            click.echo(f"  {n:>7}  {name}")
    if tally.problems:
        click.echo("\nunusable (build-time defects):")
        for name, n in tally.problems.most_common(10):
            click.echo(f"  {n:>7}  {name}")
    if written:
        click.echo("")
        for path, n in sorted(written.items()):
            click.echo(f"  {n:>7} rows -> {path}")
        if tally.bytes_written:
            click.echo(f"  {tally.bytes_written / 2**20:.1f} MiB written")
    elif dry_run:
        click.echo("\n(dry run — nothing written)")


@corpus_group.command("show")
@click.argument("target")
@click.option("--root", multiple=True, type=click.Path(), help="Where to look for .cage_runs.")
@click.option("--segment", type=int, default=None, help="Which segment (default: all).")
@click.option("--chars", type=int, default=220, show_default=True, help="Chars per turn to print.")
@click.option(
    "--splitter", type=click.Choice(["forest", "system_prompt"]), default="forest"
)
@click.option("--drop-compaction-call/--no-drop-compaction-call", default=True)
def show_cmd(
    target: str, root: tuple[str, ...], segment: int | None, chars: int,
    splitter: str, drop_compaction_call: bool,
) -> None:
    """Print what one trial exports as. TARGET is ``<run-id>/<trial-id>``."""

    from cage.corpus.build import BuildOptions, build_segments

    if "/" not in target:
        raise click.UsageError("TARGET must be <run-id>/<trial-id>")
    run_id, trial_id = target.rsplit("/", 1)

    for base in _roots(root):
        for ref in discover_runs(base):
            if ref.run_id != run_id:
                continue
            trial_dir = ref.run_dir / "trials" / trial_id
            if not trial_dir.is_dir():
                continue
            proxy = trial_dir / "proxy" / "proxy.jsonl"
            segments, problems = build_segments(
                proxy,
                BuildOptions(splitter=splitter, drop_compaction_call=drop_compaction_call),
            )
            click.echo(f"{ref.benchmark} / {ref.agent} / {ref.model} / {run_id} / {trial_id}")
            click.echo(f"{len(segments)} segment(s){'; problems: ' + str(problems) if problems else ''}\n")
            for seg in segments:
                if segment is not None and seg.index != segment:
                    continue
                click.echo(style(
                    f"=== segment {seg.index}/{seg.n_segments - 1}  "
                    f"{len(seg.messages)} messages  {seg.n_turns} supervised turns  "
                    f"think {seg.stats.get('think_ratio', 0):.0%}"
                    f"{'  opens from a summary' if seg.opens_with_summary else ''} ===",
                    "bold",
                ))
                for message in seg.messages:
                    tag = message["role"] + ("*" if message.get("loss") else "")
                    body = (message.get("content") or "").replace("\n", " ")
                    click.echo(f"  [{tag:>10}] {body[:chars]}")
                click.echo("")
            return
    click.echo(f"not found: {target}")
