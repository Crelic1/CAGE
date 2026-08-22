"""Tests for how the CLI reports failures the user can actually fix.

A `cage run` that dies on a typo'd model id, an unregistered agent kind, or a
missing model registry used to print Python's default traceback: ~25 lines of
``runpy`` and ``click`` frames with the one useful sentence at the bottom. The
message content was mostly fine — the presentation made an ordinary config typo
look like a framework crash, and buried the fix.

These cover the two halves of the contract:

  * diagnosed conditions (`CageError`) render as a message and exit 1;
  * everything else keeps its traceback, because an unexpected exception is a
    bug report and the stack is the evidence.
"""
from __future__ import annotations

import click
import pytest

from cage.agents import register_builtin_agents
from cage.agents.base.registry import get_agent_type
from cage.contracts.exceptions import CageError, ConfigError
from cage.models.registry import load_models


def _cli_module():
    """Return the ``cage.cli.main`` *module*.

    ``cage/cli/__init__.py`` re-exports the click Group under the name
    ``main``, which shadows the submodule of the same name — so
    ``import cage.cli.main as m`` binds the Group, not the module.
    """
    import importlib
    import sys

    importlib.import_module('cage.cli.main')
    return sys.modules['cage.cli.main']


def test_missing_model_registry_names_the_file_to_copy(tmp_path):
    """The most common first-run failure must carry its own remedy."""
    missing = tmp_path / "config" / "models.yml"
    with pytest.raises(ConfigError) as exc:
        load_models(missing)
    message = str(exc.value)
    assert "Model registry not found" in message
    assert "models.example.yml" in message   # what to copy
    assert "cp " in message                  # the literal command


def test_unknown_agent_kind_lists_the_registered_kinds():
    register_builtin_agents()
    with pytest.raises(ConfigError) as exc:
        get_agent_type("not_a_real_agent")
    message = str(exc.value)
    assert "not_a_real_agent" in message
    assert "claude_code" in message          # what is actually available
    assert "kind:" in message                # where to change it


def test_unknown_model_suggests_close_matches():
    """A typo'd id in a 47-entry registry should not send the user to the file."""
    from cage.config.experiment import _unknown_model_message

    models = {"glm-5.1-qb": object(), "glm-5.2": object(), "kimi-k2.6": object()}
    message = _unknown_model_message("glm-5.1-qbb", models, "/cfg/models.yml")
    assert "glm-5.1-qbb" in message
    assert "Did you mean" in message
    assert "glm-5.1-qb" in message
    assert "cage model list" in message


def test_unknown_model_without_a_near_match_still_says_where_to_look():
    from cage.config.experiment import _unknown_model_message

    message = _unknown_model_message("zzzz", {"glm-5.2": object()}, "/cfg/models.yml")
    assert "Did you mean" not in message
    assert "cage model list" in message
    assert "1 model(s) registered" in message


def test_preflight_error_is_part_of_the_taxonomy():
    """Preflight has already diagnosed the problem; it must render, not crash."""
    from cage.experiment.engine.preflight import PreflightError

    assert issubclass(PreflightError, CageError)
    # Still a RuntimeError so existing `except RuntimeError` callers are unaffected.
    assert issubclass(PreflightError, RuntimeError)


def _run_cli(monkeypatch, capsys, exc: BaseException, argv: list[str]):
    """Invoke the real ``cli()`` wrapper around a command that raises ``exc``."""
    cli_main = _cli_module()

    @click.command("boom", context_settings={"ignore_unknown_options": True})
    @click.argument("argv_rest", nargs=-1, type=click.UNPROCESSED)
    def boom(argv_rest):
        raise exc

    monkeypatch.setattr(cli_main, "main", boom)
    monkeypatch.setattr("sys.argv", ["cage", *argv])
    with pytest.raises(SystemExit) as excinfo:
        cli_main.cli()
    return excinfo.value.code, capsys.readouterr()


def test_cage_error_renders_as_a_message_not_a_traceback(monkeypatch, capsys):
    code, out = _run_cli(
        monkeypatch, capsys, ConfigError("Model 'x' not found\n  Did you mean: y"), [],
    )
    assert code == 1
    assert "Model 'x' not found" in out.err
    assert "Did you mean: y" in out.err
    assert "Re-run with -v" in out.err
    assert "Traceback" not in out.err


def test_verbose_re_raises_so_the_stack_is_still_reachable(monkeypatch, capsys):
    """The escape hatch: -v is for when the stack itself is what you're debugging."""
    cli_main = _cli_module()

    @click.command("boom", context_settings={"ignore_unknown_options": True})
    @click.argument("argv_rest", nargs=-1, type=click.UNPROCESSED)
    def boom(argv_rest):
        raise ConfigError("nope")

    monkeypatch.setattr(cli_main, "main", boom)
    monkeypatch.setattr("sys.argv", ["cage", "-v", "boom"])
    with pytest.raises(ConfigError):
        cli_main.cli()


def test_unexpected_errors_keep_their_traceback(monkeypatch, capsys):
    """A genuine framework bug must not be flattened into a tidy message."""
    cli_main = _cli_module()

    @click.command("boom", context_settings={"ignore_unknown_options": True})
    @click.argument("argv_rest", nargs=-1, type=click.UNPROCESSED)
    def boom(argv_rest):
        raise RuntimeError("a genuine framework bug")

    monkeypatch.setattr(cli_main, "main", boom)
    monkeypatch.setattr("sys.argv", ["cage", "boom"])
    with pytest.raises(RuntimeError, match="a genuine framework bug"):
        cli_main.cli()


def test_interrupt_exits_130_without_extra_noise(monkeypatch, capsys):
    """Ctrl+C: the conductor already persisted results and printed the summary."""
    from cage.contracts.exceptions import CageInterrupt

    code, out = _run_cli(monkeypatch, capsys, CageInterrupt(), [])
    assert code == 130
    assert "Traceback" not in out.err


# ---------------------------------------------------------------------------
# a dead agent's own words
# ---------------------------------------------------------------------------


def test_dead_agent_stderr_is_lifted_into_the_status_detail():
    """"Agent exited with code 1" names the symptom and withholds the cause.

    Cage does not re-implement any agent CLI's validation — the CLI already
    reports its own problems precisely. What it owes the user is making that
    report *visible*. The stderr below is verbatim from kimi-cli 1.43.0/1.44.0
    given a config missing a field it requires.
    """
    from cage.agents.base.output import failure_banner
    from cage.contracts.trial_phase import TrialPhase
    from cage.experiment.engine.termination import classify_trial_termination
    from cage.sandbox.exec import ExecResult

    stderr = (
        "Invalid configuration file /home/agent/.kimi/config.toml: "
        "1 validation error for Config\nmodels.cage-model.max_context_size\n"
        "  Field required [type=missing]\n"
    )
    recorded = failure_banner(
        ExecResult(command="kimi", stdout="", stderr=stderr, exit_code=1, duration_ms=1)
    )
    info = classify_trial_termination(
        exit_code=1, timed_out=False, terminated_by_limit=False, error="",
        output=recorded, failed_phase=TrialPhase.RUNNING_AGENT.value,
    )
    assert info.reason.value == "agent_exit_nonzero"
    assert info.detail.startswith("Agent exited with code 1: ")
    assert "Invalid configuration file" in info.detail


def test_a_normal_transcript_is_never_promoted_into_the_detail():
    """The banner is the licence to lift, not the non-zero exit itself.

    A trial whose agent produced a real transcript and *then* exited non-zero
    must not have an arbitrary line of that transcript become its status.
    """
    from cage.contracts.trial_phase import TrialPhase
    from cage.experiment.engine.termination import classify_trial_termination

    info = classify_trial_termination(
        exit_code=1, timed_out=False, terminated_by_limit=False, error="",
        output="I will now examine the binary.\nFound a buffer overflow.",
        failed_phase=TrialPhase.RUNNING_AGENT.value,
    )
    assert info.detail == "Agent exited with code 1"


def test_a_killed_agents_banner_keeps_the_end_of_stderr_not_just_the_start():
    """Where the cause sits depends on *how* the agent died.

    A CLI that refuses to start explains itself in its first lines. A CLI
    killed mid-run explains itself in its last ones — and the banner used to
    keep only ``stderr[:1000]``, so every timeout kill recorded whatever
    startup banner the CLI happened to print. A real two-hour qwen_code trial
    (174 model calls, 32.8M input tokens) had its entire agent output reduced
    to qwen's "running headless with --yolo" warning.
    """
    from cage.agents.base.output import failure_banner
    from cage.contracts.agent_output import STDERR_ELISION_MARKER
    from cage.sandbox.exec import ExecResult

    stderr = (
        "Warning: running headless with --yolo and no sandbox.\n"
        + "routine progress chatter\n" * 400
        + "FATAL: connection to 10.0.0.5 reset by peer\n"
    )
    banner = failure_banner(
        ExecResult(command="qwen", stdout="", stderr=stderr, exit_code=-1, duration_ms=1)
    )

    assert "running headless with --yolo" in banner  # the start still survives
    assert "FATAL: connection to 10.0.0.5 reset by peer" in banner  # and now the end
    assert STDERR_ELISION_MARKER in banner  # and the gap is admitted, not hidden


def test_the_elision_marker_is_never_promoted_into_a_status_detail():
    """It is our bookkeeping, not a word the agent said."""
    from cage.contracts.agent_output import (
        AGENT_FAILURE_BANNER_PREFIX,
        STDERR_ELISION_MARKER,
        agent_failure_first_line,
    )

    detail = agent_failure_first_line(
        f"{AGENT_FAILURE_BANNER_PREFIX}1]\n{STDERR_ELISION_MARKER}\nreal cause here\n"
    )
    assert detail == "real cause here"


def test_only_an_agent_that_stopped_itself_has_a_final_output():
    """A killed agent's last turn is where it got to, not what it concluded."""
    from cage.experiment.engine.termination_model import (
        TerminationReason,
        agent_was_cut_off,
    )

    # Stopped on its own terms — its parting words are the answer.
    assert not agent_was_cut_off(TerminationReason.COMPLETED.value)
    assert not agent_was_cut_off(TerminationReason.AGENT_EXIT_NONZERO.value)
    # The trial finished; only the scorer afterwards blew up.
    assert not agent_was_cut_off(TerminationReason.SCORING_ERROR.value)

    # Cut off from outside, whoever swung the axe.
    assert agent_was_cut_off(TerminationReason.EXECUTION_TIMEOUT.value)
    assert agent_was_cut_off(TerminationReason.MAX_ROUNDS_REACHED.value)
    assert agent_was_cut_off(TerminationReason.MODEL_CONTEXT_OVERFLOW.value)
    assert agent_was_cut_off(TerminationReason.USER_INTERRUPTED.value)
    assert agent_was_cut_off(TerminationReason.OOM_KILLED.value)

    # A reason nobody has taught it yet defaults to the humbler claim.
    assert agent_was_cut_off("some_reason_added_next_year")

    # Silence is not evidence of either: a running trial, or a run dir written
    # before the field existed, must not be labelled cut off.
    assert not agent_was_cut_off("")
    assert not agent_was_cut_off(None)  # type: ignore[arg-type]
