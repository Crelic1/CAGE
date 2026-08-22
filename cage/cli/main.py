"""Cage CLI — entry point for running experiments."""

from __future__ import annotations

import sys

import click

from cage.agents import register_builtin_agents
from cage.cli.commands import agent as agent_commands
from cage.cli.commands import benchmark as benchmark_commands
from cage.cli.commands import corpus as corpus_commands
from cage.cli.commands import gc as gc_commands
from cage.cli.commands import inspect as inspect_commands
from cage.cli.commands import model as model_commands
from cage.cli.commands import run as run_commands
from cage.cli.commands import score as score_commands
from cage.cli.commands import tune as tune_commands
from cage.cli.commands import serve as serve_commands
from cage.contracts.exceptions import CageError, CageInterrupt
from cage.contracts.logging import LoggingConfig, setup_logging
from cage.contracts.style import should_color, style

register_builtin_agents()

@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Console log level",
)
@click.pass_context
def main(ctx: click.Context, verbose: bool, log_level: str) -> None:
    """CAGE — an evaluation framework for installed AI coding agents.

    CAGE runs each agent in its own container against a pluggable benchmark,
    intercepts every model call, snapshots state, and scores the trial.

    Start with `cage run`: it lists the benchmarks and walks you from a smoke
    trial to a full campaign. Every other command is one slice of a run —
    `benchmark` prepares it (and `benchmark serve` stands its targets up on
    their own as a browsable range, no run needed), `model` and `agent`
    configure it, `inspect` watches it, `score` re-grades it, `corpus` turns its
    trajectories into training data, and `gc` cleans up after it.

    Docs: https://github.com/AgentCyberRange/CAGE/tree/main/docs
    """
    ctx.ensure_object(dict)
    if verbose:
        log_level = "DEBUG"
    ctx.obj["log_level"] = log_level
    setup_logging(LoggingConfig(console_level=log_level))


main.add_command(agent_commands.agent_group)
main.add_command(benchmark_commands.benchmark_group)
main.add_command(corpus_commands.corpus_group)
main.add_command(gc_commands.gc)
main.add_command(inspect_commands.inspect)
main.add_command(model_commands.model_group)
main.add_command(run_commands.run)
main.add_command(score_commands.score)
main.add_command(tune_commands.tune)
# `serve` lives under the benchmark group — it stands up a benchmark's targets
# as a browsable range: `cage benchmark serve <benchmark>`.
benchmark_commands.benchmark_group.add_command(serve_commands.serve)


def cli() -> None:
    """Console entry point: render expected failures without a traceback.

    A ``CageError`` is a *diagnosed* condition — an unknown model id, an agent
    kind that is not registered, a preflight check that already said which image
    to build. Its message is the answer, so printing it under thirty lines of
    ``click`` and ``runpy`` internals buries the one line the user needs and
    makes an ordinary config typo look like a crash.

    Anything else keeps its traceback: an unexpected exception is a framework
    bug, and the traceback is the bug report. ``-v/--verbose`` re-raises
    ``CageError`` too, for when the stack itself is what you are debugging.
    """

    try:
        main(standalone_mode=False)
    except click.ClickException as exc:      # click renders its own errors
        exc.show()
        raise SystemExit(exc.exit_code)
    except click.Abort:
        click.echo("Aborted.", err=True)
        raise SystemExit(130)
    except CageInterrupt:
        # Ctrl+C: the conductor has already persisted partial results and the
        # reporter has already printed the summary.
        raise SystemExit(130)
    except CageError as exc:
        if "-v" in sys.argv or "--verbose" in sys.argv:
            raise
        label = style("Error:", "red", "bold", enabled=should_color(sys.stderr))
        click.echo(f"\n{label} {exc}", err=True)
        click.echo("\nRe-run with -v to see the full traceback.", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
