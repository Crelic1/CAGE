"""``cage tune`` — adjust a run that is already executing.

A separate command rather than a flag on ``cage run``, for the reason every
other tool lands on the same shape (``docker update``, ``kubectl scale``,
``systemctl set-property``): changing something that is *already running* is a
different act from starting it. ``cage run --resume`` still runs trials;
``cage tune`` runs none — it validates a change, writes it, and exits.

Keeping it separate also means this command carries only the knobs that can
actually take effect mid-run. Bolted onto ``cage run`` it would have had to
reject most of that command's options one by one, which was the tell that it
did not belong there.

What it changes reaches the run through
``<run-dir>/endpoint_concurrency.json`` — see
:mod:`cage.experiment.engine.live.run_tuning`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from cage.experiment.engine.live.liveness import locate_run_dir
from cage.experiment.engine.live.run_heartbeat import run_process_is_alive
from cage.experiment.engine.live.run_tuning import read_tuning, write_tuning


def parse_source_caps(entries: tuple[str, ...]) -> dict[str, int]:
    """``("box1:16", "box2:0")`` → ``{"box1": 16, "box2": 0}``.

    A bare ``box3`` is rejected. At launch a bare id means "uncapped", but here
    it is almost always a dropped number, and silently doing nothing would be
    the worst possible response to a command someone just typed.
    """
    caps: dict[str, int] = {}
    for raw in entries:
        text = str(raw).strip()
        head, sep, tail = text.rpartition(":")
        if not sep or not head.strip() or not tail.strip().isdigit():
            raise click.UsageError(
                f"a capacity is required for {text!r} "
                f"(e.g. --model-source {text}:16, or :0 to drain it)"
            )
        caps[head.strip()] = int(tail)
    return caps


def tune_search_roots(target: str | None) -> list[Path]:
    """Where to look for ``<run_id>``: the benchmark's own runs dir, then CWD."""
    roots: list[Path] = []
    if target:
        candidate = Path(target)
        base: Path | None = None
        if candidate.is_file():
            base = candidate.parent
        elif candidate.is_dir():
            base = candidate
        else:
            try:  # a bare benchmark id like "arvo"
                from cage.benchmarks import registry

                base = Path(registry.resolve_benchmark(target).project_file).parent
            except Exception:  # noqa: BLE001 - fall back to CWD below
                base = None
        if base is not None:
            roots.append(base / ".cage_runs")
    roots.append(Path.cwd() / ".cage_runs")
    return roots


def _cap_text(cap: int | None) -> str:
    if cap is None:
        return "unset"
    return "drained (0)" if cap == 0 else str(cap)


def _registry_check(caps: dict[str, int], models_file: str | None) -> None:
    """Fail fast on an endpoint the registry does not know.

    The run would refuse it too, but only into its own log — where whoever just
    typed this command is not looking. Catching it here turns a silently
    ineffective tune into an immediate, fixable error.
    """
    try:
        from cage.config import resolve_models_file
        from cage.models import load_models

        path = resolve_models_file(models_file, repo_root=Path.cwd())
        registry = load_models(path)
    except Exception:  # noqa: BLE001 - can't check here; the run still validates
        return
    unknown = sorted(sid for sid in caps if sid not in registry)
    if unknown:
        raise click.UsageError(
            f"not registered in {path}: {', '.join(unknown)}\n"
            f"Register the endpoint first (see `cage model list`), then tune again."
        )


def apply_tune(
    *,
    run_id: str,
    model_sources: tuple[str, ...],
    clear: bool,
    search_roots: list[Path],
    dry_run: bool = False,
    models_file: str | None = None,
    echo: Any = click.echo,
) -> int:
    """Write the tuning for ``run_id``. Returns a process exit code."""
    if clear and model_sources:
        raise click.UsageError(
            "--clear restores the launch configuration; it cannot be combined "
            "with --model-source. Run it alone, then tune again."
        )
    if not clear and not model_sources:
        raise click.UsageError(
            "nothing to change — pass --model-source <id>:<n>, "
            "or --clear to restore the launch configuration"
        )
    if not run_id:
        raise click.UsageError("--run-id is required")

    run_dir = locate_run_dir(run_id, search_roots=search_roots)
    if run_dir is None:
        raise click.UsageError(
            f"no run directory found for run id {run_id!r}; "
            f"searched {', '.join(str(r) for r in search_roots)}"
        )

    alive = run_process_is_alive(run_dir)
    if alive is False:
        raise click.UsageError(
            f"run {run_id!r} is not running — a tune would never be read.\n"
            f"Restart it with the new values instead:\n"
            f"  cage run <benchmark> --run-id {run_id} --resume "
            f"--model-source <id>:<n> ..."
        )
    if alive is None:
        echo(
            f"warning: cannot confirm run {run_id!r} is alive "
            f"(no runtime_status.json) — writing the tune anyway"
        )

    # The run directory IS ``.cage_runs/<agent label>/<run id>/``, so the label
    # the running scheduler keys its pools by is right there — no need to make
    # the user restate it and risk a mismatch.
    agent_label = run_dir.parent.name

    tuning = read_tuning(run_dir) or {}
    agents = dict(tuning.get("agents") or {})
    entry = dict(agents.get(agent_label) or {})
    before = dict(entry.get("sources") or {})
    launched_with = dict((tuning.get("launch") or {}).get(agent_label) or {})

    echo(f"Tuning run {run_id}  [{agent_label}]")
    echo(f"  {run_dir}")
    echo("")

    if clear:
        if not launched_with:
            raise click.UsageError(
                "this run recorded no launch configuration, so there is nothing "
                "to restore. It was probably started before `cage tune` existed."
            )
        for sid in sorted(set(before) | set(launched_with)):
            now, orig = before.get(sid), launched_with.get(sid)
            if now != orig:
                echo(f"  {sid:<20} {_cap_text(now)} -> {_cap_text(orig)}   (launch value)")
        if before == launched_with:
            echo("  already at the launch configuration — nothing to do")
        after = dict(launched_with)
    else:
        caps = parse_source_caps(model_sources)
        _registry_check(caps, models_file)
        after = {**before, **caps}
        for sid in sorted(caps):
            note = "   drains; in-flight trials finish" if caps[sid] == 0 else ""
            echo(f"  {sid:<20} {_cap_text(before.get(sid))} -> {_cap_text(caps[sid])}{note}")
    echo("")

    if dry_run:
        echo("Dry run — nothing written.")
        return 0

    entry["sources"] = after
    agents[agent_label] = entry
    tuning["agents"] = agents
    path = write_tuning(run_dir, tuning)
    echo(f"Written to {path}")
    echo("Applies to the next trial that starts; in-flight trials are unaffected.")
    return 0


@click.command()
@click.argument("target", metavar="BENCHMARK_OR_PROJECT", required=False)
@click.option("--run-id", "run_id", default="", help="The run to adjust. Required.")
@click.option(
    "--model-source", "model_sources", multiple=True, metavar="ID:N",
    help=(
        "Set an endpoint's concurrency on the running run (repeatable): "
        "`--model-source glm-box1:32`. `:0` drains it — no new trials, "
        "in-flight ones finish. An endpoint the run did not start with is "
        "adopted from config/models.yml, so a machine registered after launch "
        "can be brought online. Endpoints you do not name are left alone."
    ),
)
@click.option(
    "--clear", "clear", is_flag=True,
    help="Discard every tuning and restore the concurrency the run launched with.",
)
@click.option(
    "--dry-run", "dry_run", is_flag=True,
    help="Print what would change without writing anything.",
)
@click.option(
    "--models-file", "models_file", default=None,
    help="Model registry to validate endpoint ids against (default: repo config).",
)
def tune(
    target: str | None,
    run_id: str,
    model_sources: tuple[str, ...],
    clear: bool,
    dry_run: bool,
    models_file: str | None,
) -> None:
    """Adjust a run that is already executing, without stopping it.

    Endpoint concurrency is what this changes today: scale a box up, bring a
    newly registered one online, or drain one so it stops taking trials while
    the ones on it finish. The change applies to the next trial that starts;
    nothing in flight is disturbed.

    \b
      cage tune arvo --run-id R1 --model-source glm-box1:32
      cage tune arvo --run-id R1 --model-source glm-box2:0     # drain
      cage tune arvo --run-id R1 --clear                       # back to launch

    BENCHMARK_OR_PROJECT only narrows where the run directory is searched for;
    omit it to search ./.cage_runs.
    """
    raise SystemExit(
        apply_tune(
            run_id=run_id,
            model_sources=model_sources,
            clear=clear,
            search_roots=tune_search_roots(target),
            dry_run=dry_run,
            models_file=models_file,
        )
    )


__all__ = ["apply_tune", "parse_source_caps", "tune", "tune_search_roots"]
