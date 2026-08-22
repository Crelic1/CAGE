"""Cage framework error taxonomy.

These are the typed exceptions the framework raises and classifies. They live in
``contracts`` (layer 0) because they are vocabulary shared across every layer:
runtime raises them, the conductor catches them, and
``termination_info_from_exception`` maps them onto a terminal verdict. Keeping the
taxonomy here — rather than inside a runtime module — means a lower layer can
raise a ``CageError`` without importing up into the runtime.

The taxonomy answers one question: **whose fault was it?** A trial that dies
because the Docker daemon was saturated, because ``project.yml`` names a model
that does not exist, because a benchmark's ``prepare_trial`` raised, and because
a scorer crashed are four different problems with four different fixes.
Collapsing them into one generic error — which is what happens to any exception
that is not one of these — makes a failed run unactionable: the inspector can
only say "trial error" and the operator has to go read a log by hand.

Raising the right type is what lets that classification happen at the source,
where the cause is actually known. The runtime additionally infers a category
from the *lifecycle phase* an unrecognized exception escaped from (see
``cage.contracts.trial_phase``), so an untyped ``RuntimeError`` from deep inside
a container helper is still attributed to the container rather than to nothing.
A typed exception is always the more precise answer and wins over that
inference.
"""

from __future__ import annotations


class CageError(Exception):
    """Base class for all Cage framework errors."""


class CageInterrupt(CageError, KeyboardInterrupt):
    """Experiment interrupted by user (Ctrl+C / SIGINT).

    When caught by the conductor, partial results are persisted before the
    process exits.
    """


class TrialError(CageError):
    """Error during a single trial execution."""

    def __init__(self, trial_id: str, message: str) -> None:
        self.trial_id = trial_id
        super().__init__(f"Trial {trial_id}: {message}")


class TrialTimeout(TrialError):
    """Trial exceeded its allowed duration."""

    def __init__(self, trial_id: str, timeout_s: float) -> None:
        self.timeout_s = timeout_s
        super().__init__(trial_id, f"timed out after {timeout_s:.0f}s")


class ContainerError(CageError, RuntimeError):
    """Error in container lifecycle (start, exec, stop).

    Infra, not agent: the sandbox itself could not be created or driven — a
    saturated Docker daemon, a missing image, an exhausted disk, a container
    force-removed mid-exec.

    Kept a ``RuntimeError`` for the same backward-compatibility reason as
    ``ConfigError``'s ``ValueError`` base — the sandbox raised bare
    ``RuntimeError`` here before the taxonomy reached it.
    """

    def __init__(self, container_name: str, message: str) -> None:
        self.container_name = container_name
        super().__init__(f"Container {container_name}: {message}")


class ProxyError(CageError):
    """Error in the in-container proxy (start, health check, stop)."""


class ConfigError(CageError, ValueError):
    """Invalid or unusable configuration.

    A Layer-3 problem: ``project.yml`` / ``config/models.yml`` asked for
    something that cannot be resolved (unknown agent, unknown model, malformed
    section, missing credential). Distinct from every other error here in that
    re-running changes nothing until the user edits the config — which is
    exactly why resume must not treat it as a transient infra failure.

    Also a ``ValueError`` because that is what these sites raised before the
    taxonomy existed: config rejection *is* "this value is not acceptable", and
    keeping the base class means benchmark authors and callers with an existing
    ``except ValueError`` keep working.
    """


class AgentSetupError(CageError, RuntimeError):
    """The agent under test could not be prepared or launched.

    Covers credential seeding, CLI installation, version probing, and plugin
    installation — everything between "the container is up" and "the agent CLI
    is running". Distinct from ``ContainerError`` (the sandbox is fine) and from
    a non-zero agent exit (the agent ran, and failed on its own terms).

    Kept a ``RuntimeError`` for the same backward-compatibility reason as
    ``ConfigError``'s ``ValueError`` base.
    """


class TargetError(CageError):
    """The benchmark's target stack failed after coming up.

    A service died mid-trial, the network vanished, the check endpoint stopped
    answering. Launch-time failures have their own path and terminal reason
    (``target_unavailable``); this is the one that says the target was healthy
    and then was not.
    """


class BenchmarkError(CageError):
    """A ``Benchmark`` subclass raised while the framework called into it.

    Layer 2, not Layer 1: ``iter_samples`` / ``prepare_trial`` / ``build_prompt``
    and the lifecycle hooks are user-authored. Naming this separately keeps a bug
    in one benchmark from reading as a framework failure across every run.
    """


class ScoringError(CageError):
    """A ``Scorer`` subclass raised while scoring a trial.

    Also Layer 2. Deliberately distinct from ``BenchmarkError`` because a
    scoring failure leaves a *completed* trial whose result is still usable —
    the trial ran, only its verdict is missing, and ``cage score`` can recompute
    it offline without re-running the agent.
    """


__all__ = [
    "AgentSetupError",
    "BenchmarkError",
    "CageError",
    "CageInterrupt",
    "ConfigError",
    "ContainerError",
    "ProxyError",
    "ScoringError",
    "TargetError",
    "TrialError",
    "TrialTimeout",
]
