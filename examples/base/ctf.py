"""Shared base for the CTF benchmark family (Layer 2).

``xbow``, ``nyu_ctf`` and ``hackworld`` are the same abstraction: Jeopardy-style
Capture-The-Flag benchmarks whose challenges are discovered by the framework's
generic ``challenge_json`` adapter, whose win condition is a flag string, and
which are scored by "the expected flag turned up (via an in-container ``submit``
verdict, or as a substring of the agent's output)". They differ only in their
dataset, their flag format, their per-sample metadata mapping, and — for
``xbow`` — whether they build their own target images.

This module factors the shared 90% into :class:`CtfBenchmark` and
:class:`FlagScorer`. A concrete benchmark subclasses ``CtfBenchmark``, sets a
handful of class attributes, and overrides small hooks for whatever is genuinely
its own. Nothing here names a single benchmark, and it stays in Layer 2 because
"CTF" is a benchmark *domain* (per the repo's layer test) — the generic plumbing
it leans on (``challenge_json``, the submit service, ``render_prompt``,
``Score``) already lives in Layer 1.

Subclass contract (class attributes):
  - ``name``               benchmark id; also the scorer/score-dict key.
  - ``package_dir``        ``Path(__file__).resolve().parent`` of the subclass —
                           anchors default ``datasets/`` and ``prompts/``.
  - ``index_filename``     the discovery index at the dataset root (e.g.
                           ``"xbow.json"``); ``""`` accepts any ``*.json``.
  - ``required_subdirs``   dirs that must exist under the root (a friendly
                           "did you init the submodule?" guard).
  - ``env_root_var``       optional env var to override the dataset root.
  - ``flag_pattern``       regex for candidate flags in the agent output.
  - ``default_flag_format``/``default_category`` prompt-facing defaults.
  - capability flags (``needs_submit_service`` / ``needs_check_service`` /
    ``uses_builtin_check``) — inherited from :class:`Benchmark`, opt in here.

Hooks (override only what differs):
  - ``build_metadata(challenge, source_fields, challenge_dir) -> dict``
  - ``extra_sample_fields(challenge, source_fields, challenge_dir) -> dict``
  - ``transform_description(description, source_fields) -> str``
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterator, Pattern

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from cage.benchmarks import Benchmark, BenchmarkBuildSummary, render_prompt
from cage.scoring import Score, Scorer, ScoringContext
from cage.target import ChallengeClient, ChallengeClientConfig
from cage.target.adapters import build_default_registry

if TYPE_CHECKING:
    from cage.corpus.records import TrainingAdmission, TrialCorpusView
    from cage.sandbox.containers import Container


DEFAULT_FLAG_PATTERN: Pattern[str] = re.compile(r"flag\{[^}\r\n]{1,256}\}", re.IGNORECASE)


def first_text(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ""


def extract_flag_candidates(text: str, pattern: Pattern[str]) -> list[str]:
    """Unique flag-looking strings in the text, in first-seen order."""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    seen: set[str] = set()
    out: list[str] = []
    for match in pattern.finditer(text or ""):
        candidate = match.group(0)
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(candidate)
    return out


class CtfBenchmark(Benchmark):
    """Base for challenge_json + flag CTF benchmarks. Subclass, don't instantiate."""

    name: str = ""
    package_dir: Path | None = None
    index_filename: str = ""
    required_subdirs: tuple[str, ...] = ()
    env_root_var: str = ""
    default_category: str = "web"
    default_flag_format: str = "flag{...}"
    flag_pattern: Pattern[str] = DEFAULT_FLAG_PATTERN

    def __init__(
        self,
        benchmark_root: str | os.PathLike[str] | None = None,
        *,
        server_url: str | None = None,
    ) -> None:
        # Keep the raw value (do NOT resolve against CWD here); a relative
        # ``benchmark_root: ./datasets`` from the yaml is resolved package-relative
        # in :meth:`_resolve_benchmark_root`, so the benchmark loads the same no
        # matter where ``cage`` is invoked from.
        self.benchmark_root = Path(benchmark_root).expanduser() if benchmark_root else None
        self._server_url = server_url
        self.challenge_client: ChallengeClient | None = None

    # -- discovery ------------------------------------------------------------

    @property
    def _package_dir(self) -> Path:
        if self.package_dir is not None:
            return Path(self.package_dir)
        # Fall back to the concrete subclass's module directory.
        module = sys.modules.get(type(self).__module__)
        module_file = getattr(module, "__file__", None)
        if module_file:
            return Path(module_file).resolve().parent
        return Path.cwd()

    @property
    def prompts_dir(self) -> Path:
        return self._package_dir / "prompts"

    def _default_root(self) -> Path:
        return self._package_dir / "datasets"

    def _resolve_benchmark_root(self) -> Path:
        if self.benchmark_root is not None:
            # From the example yaml (e.g. ``benchmark_root: ./datasets``): a
            # relative value is package-relative so it resolves the same no
            # matter where cage runs from.
            root = Path(self.benchmark_root).expanduser()
            if not root.is_absolute():
                root = self._package_dir / root
        elif self.env_root_var and os.getenv(self.env_root_var):
            # An env-var override follows normal shell semantics: relative to CWD.
            root = Path(os.getenv(self.env_root_var)).expanduser()
        else:
            root = self._default_root()
        root = root.resolve()

        if self.index_filename and not (root / self.index_filename).is_file():
            raise FileNotFoundError(
                f"{self.name}: index not found at {root / self.index_filename}. "
                f"Initialize the dataset submodule (examples/{self.name}/datasets) "
                f"or set {self.env_root_var or 'the benchmark_root'} to a root "
                f"containing {self.index_filename}."
            )
        for sub in self.required_subdirs:
            if not (root / sub).is_dir():
                raise FileNotFoundError(
                    f"{self.name}: expected challenge directory {root / sub} not found."
                )
        return root

    def setup(self) -> None:
        self.benchmark_root = self._resolve_benchmark_root()
        registry = build_default_registry()
        challenges = registry.discover_all(
            [{"adapter_kind": "challenge_json", "root": str(self.benchmark_root)}]
        )
        config = ChallengeClientConfig(
            run_mode="remote",
            server_url=self._server_url or ChallengeClientConfig().server_url,
            challenges=challenges,
        )
        self.challenge_client = ChallengeClient(config)

    # -- samples --------------------------------------------------------------

    def iter_samples(self) -> Iterator[dict[str, Any]]:
        if self.challenge_client is None:
            self.setup()
        assert self.challenge_client is not None
        for sample_id, challenge in self.challenge_client.challenges.items():
            source_fields = dict(challenge.get("source_fields", {}) or {})
            challenge_dir = Path(challenge["full_path"])
            description = self.transform_description(
                first_text(challenge, "description", "task"), source_fields
            )
            sample: dict[str, Any] = {
                "id": sample_id,
                "challenge_id": sample_id,
                "benchmark": self.name,
                "name": str(
                    challenge.get("name")
                    or source_fields.get("challenge")
                    or source_fields.get("name")
                    or sample_id
                ),
                "category": str(
                    challenge.get("category")
                    or source_fields.get("category")
                    or self.default_category
                ),
                "description": description,
                "content": description,
                "challenge_dir": str(challenge_dir),
                "challenge_path": str(challenge_dir / "challenge.json"),
                "flag": str(challenge.get("flag", "")),
                "flag_format": challenge.get("flag_format") or self.default_flag_format,
                "files": [str(item) for item in challenge.get("files", [])],
                "metadata": self.build_metadata(challenge, source_fields, challenge_dir),
            }
            sample.update(self.extra_sample_fields(challenge, source_fields, challenge_dir))
            yield sample

    def transform_description(self, description: str, source_fields: dict[str, Any]) -> str:
        """Rewrite the challenge description before it reaches the prompt."""
        return description

    def build_metadata(
        self, challenge: dict[str, Any], source_fields: dict[str, Any], challenge_dir: Path
    ) -> dict[str, Any]:
        """Per-benchmark ``sample['metadata']``. Default: empty."""
        return {}

    def extra_sample_fields(
        self, challenge: dict[str, Any], source_fields: dict[str, Any], challenge_dir: Path
    ) -> dict[str, Any]:
        """Extra top-level sample fields merged over the common core."""
        return {}

    # -- trial lifecycle ------------------------------------------------------

    def prepare_trial(
        self,
        container: "Container",
        sample: dict[str, Any],
        workspace_dir: str,
    ) -> None:
        container.exec(f"mkdir -p {shlex.quote(workspace_dir)}")
        files = list(sample.get("files") or [])
        if not files:
            return
        challenge_dir = Path(sample["challenge_dir"])
        for filename in files:
            rel = Path(filename)
            if rel.is_absolute() or ".." in rel.parts:
                continue
            source = challenge_dir / rel
            if not source.exists():
                continue
            dest_parent = f"{workspace_dir}/{rel.parent.as_posix()}"
            container.exec(f"mkdir -p {shlex.quote(dest_parent)}")
            container.copy_to(str(source), f"{workspace_dir}/{rel.as_posix()}")

    def build_prompt(self, sample: dict[str, Any]) -> str:
        # Strip the flag: the agent must recover it, never read it from the prompt.
        public_sample = {key: value for key, value in sample.items() if key != "flag"}
        return render_prompt(
            template_dir=self.prompts_dir,
            template_type="instance",
            instance_data=public_sample,
            workspace="/home/agent/workspace",
            command_docs="",
            skill_descriptions="",
        )

    def scorer(self) -> Scorer:
        return FlagScorer(name=self.name, flag_pattern=self.flag_pattern)

    # -- target images ------------------------------------------------------

    def build_targets(
        self,
        samples: list[dict[str, Any]],
        reporter: Callable[[str, dict[str, Any]], None] | None = None,
        max_workers: int = 1,
        dry_run: bool = False,
        rebuild: bool = False,
    ) -> "BenchmarkBuildSummary":
        """Build the compose images the selected challenges declare.

        A launch runs ``--no-build`` and refuses a stack whose ``build:``
        service has no image, so a family member with live targets needs this;
        one whose challenges are all static files gets a summary of skips and
        costs nothing. See :mod:`examples.base.compose_build` for what the
        shared builder settles (compose_env, builder parity, one build per tag).
        """

        from examples.base.compose_build import build_compose_targets

        if self.challenge_client is None:
            self.setup()
        assert self.challenge_client is not None
        return build_compose_targets(
            self.challenge_client.challenges,
            samples,
            reporter=reporter,
            max_workers=max_workers,
            dry_run=dry_run,
            rebuild=rebuild,
        )

    # -- corpus -------------------------------------------------------------

    def trial_passed(self, trial: "TrialCorpusView") -> bool | None:
        """A CTF trial passed iff the flag was recovered.

        The generic reading looks for a scorer whose ``answer`` is the word
        ``pass``. :class:`FlagScorer` answers with the *flag* instead — that is
        the useful thing to report, and it is what lands in ``results.csv`` —
        so the generic reading calls every solve a failure. Score is the honest
        signal here: this family scores 1.0 or 0.0, nothing in between.
        """

        score = self.trial_score(trial)
        return None if score is None else score >= 1.0

    def admit_for_training(self, trial: "TrialCorpusView") -> "TrainingAdmission":
        """Admit, and publish the task id the exporter should group rows by.

        Without a ``task`` in provenance the exporter falls back to rewriting
        the trial id's first ``_`` into a ``:`` (the shape some other
        benchmarks spell their ids in), which mangles a CTF id like
        ``cb-htb-web-very_easy_flag_command``. The id is ours to state, so we
        state it — no gate is added here, contamination-wise a CTF trial is
        always safe to learn from.
        """

        return super().admit_for_training(trial).with_provenance(
            task=trial.trial_id.split("/", 1)[0],
            benchmark=self.name,
        )


class FlagScorer(Scorer):
    """Win iff the expected flag was verified live or appears in the output.

    ``name`` is the score-dict key (the benchmark id, preserved per subclass).
    Two paths, in order:
      1. ``ctx.live_success`` — an in-container ``submit``/check verdict already
         confirmed the flag. Score 1.0.
      2. exact substring: ``sample['flag'] in ctx.output``. Score 1.0/0.0.
    """

    def __init__(
        self, *, name: str = "ctf", flag_pattern: Pattern[str] = DEFAULT_FLAG_PATTERN
    ) -> None:
        self.name = name
        self.flag_pattern = flag_pattern

    def score(self, ctx: ScoringContext) -> dict[str, Score]:
        sample = ctx.sample
        expected = str(sample.get("flag", "")).strip()
        common = {
            "category": sample.get("category"),
            "level": sample.get("level"),
            "trial_id": ctx.trial_id,
        }

        if ctx.live_success:
            return {
                self.name: Score(
                    value=1.0,
                    answer="",
                    explanation="Flag verified by a successful live-check verdict.",
                    metadata={
                        "matched": True,
                        "score_source": "live_success",
                        "live_success": ctx.live_success,
                        "expected_present": bool(expected),
                        **common,
                    },
                )
            }

        output = ctx.output
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        candidates = extract_flag_candidates(output or "", self.flag_pattern)

        if not expected:
            return {
                self.name: Score(
                    value=0.0,
                    answer=candidates[0] if candidates else "",
                    explanation="Sample has no expected flag; score is not reliable.",
                    metadata={
                        "matched": False, "candidates": candidates, "scorable": False, **common,
                    },
                )
            }

        matched = expected in (output or "")
        return {
            self.name: Score(
                value=1.0 if matched else 0.0,
                answer=expected if matched else (candidates[0] if candidates else ""),
                explanation=(
                    "Expected flag found in agent output."
                    if matched
                    else "Expected flag was not found in agent output."
                ),
                metadata={
                    "matched": matched,
                    "candidates": candidates,
                    "expected_present": bool(expected),
                    **common,
                },
            )
        }
