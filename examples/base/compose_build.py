"""One compose-image builder for the CTF benchmark family (Layer 2).

A benchmark whose targets are ``docker compose`` stacks has to build their
images *before* a run: the target server launches with ``--no-build`` and
refuses a stack whose ``build:`` service has no image yet. That is the same job
for every such benchmark, and it was being solved three times over — once in
``agent_pentest_bench``, once in ``xbow``, and once more in ``cybench`` — with
two of them differing on details that decide whether the resulting image is
even correct.

The details that are easy to get wrong, and are settled here once:

  - **``compose_env`` reaches the build.** XBOW bakes its flag through
    ``build.args.FLAG`` fed by ``compose_env``; drop it and every image is built
    with an empty flag and every trial is unscorable.
  - **The builder matches the launch-time builder.** ``DOCKER_BUILDKIT`` follows
    ``TARGET_SERVER_DOCKER_BUILDKIT``, so an image built here is what a
    launch-time build would have produced.
  - **An image is built once.** pass@k hands the same challenge over more than
    once; the second request skips instead of racing the first for the tag.
  - **Already-built images are skipped** unless ``rebuild``.

Nothing here knows a benchmark name: it reads the launch spec the challenge
declares and builds what that spec says to build.
"""

from __future__ import annotations

import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from cage.benchmarks import BenchmarkBuildResult, BenchmarkBuildSummary
from cage.target.adapters import build_default_registry
from cage.target.compose_files import expand_compose_env_values, load_compose_stack

Reporter = Callable[[str, dict[str, Any]], None]


def _image_exists(image: str) -> bool:
    """True when this exact tag is already in the local docker image store."""

    return (
        subprocess.run(
            ["docker", "image", "inspect", image], capture_output=True, text=True
        ).returncode
        == 0
    )


def _compose_env(spec: Any) -> dict[str, str]:
    return {
        str(key): str(value)
        for key, value in (spec.runtime_patches.get("compose_env", {}) or {}).items()
    }


def _build_env(spec: Any) -> dict[str, str]:
    env = os.environ.copy()
    # Match the target server's builder choice so an image built here is what a
    # launch-time build would have produced.
    env["DOCKER_BUILDKIT"] = os.getenv("TARGET_SERVER_DOCKER_BUILDKIT", "0")
    env.update(_compose_env(spec))
    return env


def _build_entries(spec: Any) -> list[tuple[str, str]]:
    """``(service, image)`` for every service this stack builds from source.

    Raises when a ``build:`` service declares no ``image:`` — the target server
    lints for exactly that, so failing here names the challenge instead of
    letting the run die at launch.
    """

    compose_env = _compose_env(spec)
    config = expand_compose_env_values(
        load_compose_stack(list(spec.compose_files), compose_env=compose_env), compose_env
    )
    entries: list[tuple[str, str]] = []
    for service_name, service in (config.get("services") or {}).items():
        if not isinstance(service, dict) or "build" not in service:
            continue
        image = str(service.get("image") or "").strip()
        if not image:
            raise ValueError(f"service {service_name!r} declares 'build:' but no 'image:'")
        entries.append((str(service_name), image))
    return entries


def _project_directory(spec: Any) -> Path:
    """Where relative ``build:`` contexts are anchored.

    The compose file's own directory, not the challenge root — which is what
    the target server anchors to when it materializes a stack for launch. The
    two differ for any challenge that keeps its compose file in a subdirectory
    (``dist/docker-compose.yml`` with ``build: ./blog`` beside it): anchoring at
    the challenge root there resolves every context one level too high and the
    build fails on a missing directory.
    """

    if spec.compose_files:
        return Path(spec.compose_files[0]).resolve().parent
    return Path(spec.working_directory).resolve()


def _build_command(spec: Any) -> list[str]:
    command = ["docker", "compose", "--project-directory", str(_project_directory(spec))]
    for compose_file in spec.compose_files:
        command.extend(["-f", str(compose_file)])
    command.append("build")
    return command


def build_compose_targets(
    challenges: dict[str, Any],
    samples: list[dict[str, Any]],
    *,
    reporter: Reporter | None = None,
    max_workers: int = 1,
    dry_run: bool = False,
    rebuild: bool = False,
) -> BenchmarkBuildSummary:
    """Build the compose images the selected samples need.

    ``challenges`` is the benchmark's normalized challenge map (what
    ``ChallengeClient.challenges`` holds). Samples whose challenge has no
    compose stack are reported as skipped rather than dropped, so the summary
    accounts for everything that was asked for.
    """

    max_workers = max(1, int(max_workers or 1))
    registry = build_default_registry()
    results: list[BenchmarkBuildResult] = []
    plan: list[tuple[str, Any, list[tuple[str, str]]]] = []
    claimed: set[str] = set()

    for sample in samples:
        challenge_id = str(sample.get("challenge_id") or sample.get("id") or "").strip()
        if not challenge_id:
            results.append(
                BenchmarkBuildResult(
                    target_id="?", status="failed", error="sample has no challenge_id or id"
                )
            )
            continue

        challenge = challenges.get(challenge_id)
        if challenge is None:
            results.append(
                BenchmarkBuildResult(
                    target_id=challenge_id,
                    status="failed",
                    error="target not found in benchmark source",
                )
            )
            continue

        try:
            adapter = registry.get(str(challenge.get("adapter_kind") or "challenge_json"))
            spec = adapter.build_launch_spec(challenge)
        except Exception as exc:  # noqa: BLE001 - one bad challenge must not sink the batch
            results.append(
                BenchmarkBuildResult(
                    target_id=challenge_id, status="failed", error=f"launch-spec error: {exc}"
                )
            )
            continue

        if spec.mode != "compose":
            results.append(
                BenchmarkBuildResult(
                    target_id=challenge_id,
                    status="skipped",
                    detail="static challenge: no image to build",
                )
            )
            continue

        try:
            entries = _build_entries(spec)
        except Exception as exc:  # noqa: BLE001
            results.append(
                BenchmarkBuildResult(target_id=challenge_id, status="failed", error=str(exc))
            )
            continue

        if not entries:
            results.append(
                BenchmarkBuildResult(
                    target_id=challenge_id,
                    status="skipped",
                    detail="no build: services (images are pulled)",
                )
            )
            continue

        wanted = [
            (service, image)
            for service, image in entries
            if image not in claimed and (rebuild or not _image_exists(image))
        ]
        if not wanted:
            results.append(
                BenchmarkBuildResult(
                    target_id=challenge_id,
                    status="skipped",
                    command=_build_command(spec),
                    detail=f"already built: {', '.join(image for _s, image in entries)}",
                )
            )
            continue

        claimed.update(image for _service, image in wanted)
        plan.append((challenge_id, spec, wanted))

    if reporter is not None:
        reporter("plan", {"total_targets": len(plan), "selected_samples": len(samples)})

    total = len(plan)

    def run_one(
        index: int, challenge_id: str, spec: Any, entries: list[tuple[str, str]]
    ) -> BenchmarkBuildResult:
        command = _build_command(spec)
        details = [f"{service}->{image}" for service, image in entries]

        if dry_run:
            if reporter is not None:
                reporter(
                    "dry-run",
                    {
                        "target_id": challenge_id,
                        "index": index,
                        "total": total,
                        "kind": "compose image",
                        "status": "planned",
                        "command": command,
                        "details": details,
                    },
                )
            return BenchmarkBuildResult(
                target_id=challenge_id,
                status="planned",
                command=command,
                detail=", ".join(details),
            )

        if reporter is not None:
            reporter(
                "start",
                {
                    "target_id": challenge_id,
                    "index": index,
                    "total": total,
                    "kind": "compose image",
                    "command": command,
                    "details": details,
                },
            )

        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=str(_project_directory(spec)),
                env=_build_env(spec),
                capture_output=True,
                text=True,
            )
        except OSError as exc:
            duration = time.monotonic() - started
            if reporter is not None:
                reporter(
                    "finish",
                    {
                        "target_id": challenge_id,
                        "index": index,
                        "total": total,
                        "status": "failed",
                        "duration_s": duration,
                        "error": str(exc),
                    },
                )
            return BenchmarkBuildResult(
                target_id=challenge_id,
                status="failed",
                command=command,
                error=str(exc),
                detail=", ".join(details),
                duration_s=duration,
            )

        duration = time.monotonic() - started
        status = "built" if completed.returncode == 0 else "failed"
        error = "" if status == "built" else (completed.stderr or "").strip()[-2000:]
        if reporter is not None:
            reporter(
                "finish",
                {
                    "target_id": challenge_id,
                    "index": index,
                    "total": total,
                    "status": status,
                    "duration_s": duration,
                    "returncode": completed.returncode,
                    "error": error,
                },
            )
        return BenchmarkBuildResult(
            target_id=challenge_id,
            status=status,
            command=command,
            returncode=completed.returncode,
            stdout=(completed.stdout or "")[-4000:],
            stderr=(completed.stderr or "")[-4000:],
            error=error,
            detail=", ".join(details),
            duration_s=duration,
        )

    if max_workers == 1 or total <= 1:
        for index, (challenge_id, spec, entries) in enumerate(plan, start=1):
            results.append(run_one(index, challenge_id, spec, entries))
    else:
        with ThreadPoolExecutor(max_workers=min(max_workers, total)) as pool:
            futures = {
                pool.submit(run_one, index, challenge_id, spec, entries): index
                for index, (challenge_id, spec, entries) in enumerate(plan, start=1)
            }
            done: dict[int, BenchmarkBuildResult] = {}
            for future in as_completed(futures):
                done[futures[future]] = future.result()
            results.extend(done[index] for index in sorted(done))

    return BenchmarkBuildSummary.from_results(results)
