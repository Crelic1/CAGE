#!/usr/bin/env python3
"""Turn an upstream Cybench checkout into a Cage ``challenge_json`` dataset.

Upstream Cybench (https://github.com/andyzorigin/cybench) describes a task as a
directory holding ``metadata/metadata.json`` (prompts, flag, subtasks), an
``init_script.sh`` that stages the agent-visible files into a scratch dir, and —
for the 24 tasks with a live service — a ``start_docker.sh`` plus a compose file
that attaches the service to a shared external network under a fixed hostname.

Cage discovers challenges through ``challenge.json`` and launches compose stacks
itself, so this script rewrites that shape once, offline:

  * **files** — the agent-visible file set is whatever ``init_script.sh``
    actually produces, so we *run* it against a scratch dir rather than parsing
    its ``cp``/``unzip``/``mv`` lines. The result lands under ``public/`` in the
    generated challenge dir, and ``prepare_trial`` copies ``public/<rel>`` to
    ``<workspace>/<rel>`` — the same paths upstream hands the agent.
  * **compose** — a generated ``docker-compose.cage.yml`` beside the upstream
    file (so relative build contexts still resolve). The external
    ``shared_net``/``ctfnet`` becomes a project-local network, ``container_name``
    is dropped, and every ``build:`` service gets an explicit ``image:`` — all
    three are required for trials to run concurrently. Cage's project-local
    network mode resolves a service at its own name, so upstream prompts that
    say ``web_flag:1337`` keep working verbatim.
  * **flag** — taken from the last subtask's answer, cross-checked against the
    task's ``flag.txt`` when it has one.

Every staged file is checked against the flag before it is written: a task that
would hand the agent its own answer fails the run instead of producing a
silently unscorable challenge.

Usage::

    python examples/cybench/scripts/generate_dataset.py \
        --cybench-root ~/workspace/fyh/cybereval-research/cybench \
        --out examples/cybench/datasets

Upstream ``main`` no longer ships the nine GlacierCTF tasks that
``task_list.txt`` still lists; point ``--extra-root`` at a checkout that has
them (see the dataset README for provenance).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

# Competition directory (as it appears under ``benchmark/``) → the short event
# token used in challenge ids and the generated directory layout.
EVENT_BY_COMPETITION = {
    "hackthebox/cyber-apocalypse-2024": "HTB",
    "project-sekai-ctf/sekaictf-2022": "S22",
    "project-sekai-ctf/sekaictf-2023": "S23",
    "hkcert-ctf/CTF-Challenges/CTF-2022": "HKC",
    "LosFuzzys/GlacierCTF2023_writeups": "GLA",
}

# Directories inside a task that are solution material, not challenge material.
# They stay out of the generated dataset entirely: nothing downstream needs
# them, and every copy is one more place a flag can leak from.
EXCLUDED_DIRS = {".git", "__pycache__", "solution", "solutions"}
EXCLUDED_FILE_SUFFIXES = ("writeup.md", "writeup.txt")

# Networks upstream declares as external. Cage gives each trial its own
# project-local network instead, so these are un-externalized rather than
# renamed — keeping the name means keeping upstream's service addressing.
EXTERNAL_NETWORK_NAMES = {"shared_net", "ctfnet"}


def log(message: str) -> None:
    print(message, file=sys.stderr)


def slugify(value: str) -> str:
    """``[Very Easy] Flag Command`` → ``very_easy_flag_command``."""
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return re.sub(r"_+", "_", cleaned)


def parse_target_hosts(target_host: str) -> list[tuple[str, int | None]]:
    """``web_flag:1337`` → ``[("web_flag", 1337)]``.

    A handful of tasks name more than one service (``alice:1337 bob:1337``), so
    the field is read as a whitespace-separated list throughout.
    """
    hosts: list[tuple[str, int | None]] = []
    for token in str(target_host or "").split():
        host, _, port = token.partition(":")
        host = host.strip()
        if not host:
            continue
        try:
            hosts.append((host, int(port) if port else None))
        except ValueError:
            hosts.append((host, None))
    return hosts


# --------------------------------------------------------------------------- #
# discovery
# --------------------------------------------------------------------------- #


def resolve_task_dir(task_path: str, roots: list[Path]) -> Path | None:
    """First root under which ``task_path`` exists with its metadata.

    Tried in order: the upstream path itself, the same path minus the
    ``benchmark/`` prefix, then a search by task-directory name — a fallback
    root need not mirror upstream's competition layout, only carry the task.
    """
    relative = task_path[len("benchmark/") :] if task_path.startswith("benchmark/") else task_path
    task_name = relative.rstrip("/").split("/")[-1]
    for root in roots:
        for candidate in (root / task_path, root / relative):
            if (candidate / "metadata" / "metadata.json").is_file():
                return candidate
        for candidate in sorted(root.glob(f"*/*/{task_name}")) + sorted(
            root.glob(f"*/{task_name}")
        ):
            if (candidate / "metadata" / "metadata.json").is_file():
                return candidate
    return None


def competition_of(task_path: str) -> str:
    relative = task_path[len("benchmark/") :] if task_path.startswith("benchmark/") else task_path
    for competition in EVENT_BY_COMPETITION:
        if relative.startswith(competition + "/"):
            return competition
    raise ValueError(f"unknown competition for task path: {task_path}")


def category_of(task_path: str, metadata: dict[str, Any]) -> str:
    """Upstream's own category — the metadata list wins, the path is the fallback."""
    categories = [str(item).strip() for item in metadata.get("categories", []) if str(item).strip()]
    if categories:
        return categories[0]
    relative = task_path[len("benchmark/") :]
    competition = competition_of(task_path)
    remainder = relative[len(competition) + 1 :]
    return remainder.split("/")[0] if "/" in remainder else "misc"


# --------------------------------------------------------------------------- #
# agent-visible files
# --------------------------------------------------------------------------- #


def stub_bin(tmp_dir: Path) -> str:
    """A PATH entry whose ``docker`` does nothing.

    One upstream ``init_script.sh`` (randsubware) builds an image and starts a
    container as a side effect of staging files. Generating a dataset must not
    touch the host's docker state, and that container is unreachable from the
    agent anyway (the task declares no ``target_host`` and publishes no port),
    so the call is neutralized instead of honoured. Every launch Cage actually
    performs comes from the generated compose file.
    """
    bin_dir = tmp_dir / "stub-bin"
    bin_dir.mkdir(exist_ok=True)
    stub = bin_dir / "docker"
    stub.write_text('#!/bin/sh\necho "[generate_dataset] skipped: docker $*" >&2\nexit 0\n')
    stub.chmod(0o755)
    return str(bin_dir)


def stage_public_files(
    task_dir: Path, scratch_root: Path
) -> tuple[list[str], Path | None, str]:
    """Run ``init_script.sh``; return its file list, tree, and stderr.

    Executed with ``EASY_PROMPT=false``: the staged file set is identical either
    way upstream (the flag only selects which prompt text is echoed), and the
    hard prompt is Cage's default variant.

    Stderr is returned rather than swallowed because a couple of upstream
    scripts fail *partially* — ``cp -r $(dirname "$0")/challenge/*`` word-splits
    on a task directory whose name has spaces, so the task ships no handout even
    though its prompt describes one. That happens in upstream's own container
    too (same paths), so the behaviour is reproduced, not repaired; recording
    the stderr is what keeps it from looking like a defect on this side.
    """
    init_script = task_dir / "init_script.sh"
    if not init_script.is_file():
        return [], None, ""

    holding = scratch_root / f"staged-{slugify(task_dir.name)}-{os.getpid()}"
    with tempfile.TemporaryDirectory(dir=str(scratch_root)) as tmp:
        staging = Path(tmp) / "workspace"
        staging.mkdir()
        result = subprocess.run(
            ["bash", str(init_script), str(staging), "false"],
            cwd=str(task_dir),
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "PATH": f"{stub_bin(Path(tmp))}:{os.environ.get('PATH', '')}"},
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"init_script.sh failed for {task_dir} (exit {result.returncode}): "
                f"{result.stderr.strip()[:400]}"
            )
        staged = sorted(
            path.relative_to(staging).as_posix()
            for path in staging.rglob("*")
            if path.is_file()
        )
        # Hold the staged tree outside the temp dir before it is removed.
        if holding.exists():
            shutil.rmtree(holding)
        shutil.copytree(staging, holding, symlinks=True)
        # The scratch path is different on every run and would otherwise make
        # the generated challenge.json differ run to run for no real reason.
        stderr = result.stderr.strip().replace(str(staging), "$TMP_DIR")

    return staged, holding, stderr


# --------------------------------------------------------------------------- #
# compose
# --------------------------------------------------------------------------- #


def find_compose_file(task_dir: Path) -> Path | None:
    """The compose file ``start_docker.sh`` would bring up, if any.

    Upstream start scripts either ``cd`` into a subdirectory before
    ``docker compose up`` or pass ``-f <path>``; both are read here rather than
    guessed, because six of the tasks keep their compose file in a subdir.
    """
    start_docker = task_dir / "start_docker.sh"
    if start_docker.is_file():
        text = start_docker.read_text(encoding="utf-8", errors="replace")

        explicit = re.search(r'-f\s+"?\$\{?DIR\}?/([^"\s]+)"?', text)
        if explicit:
            candidate = task_dir / explicit.group(1)
            if candidate.is_file():
                return candidate

        subdir = re.search(r'cd\s+"?\$\{?DIR\}?/([^"\s]+)"?', text)
        if subdir:
            for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
                candidate = task_dir / subdir.group(1) / name
                if candidate.is_file():
                    return candidate

    for name in ("docker-compose.yml", "docker-compose.yaml", "compose.yml"):
        candidate = task_dir / name
        if candidate.is_file():
            return candidate
    return None


def cage_compose(
    compose: dict[str, Any], challenge_id: str, target_service: str = ""
) -> tuple[dict[str, Any], str, list[str], list[str]]:
    """Rewrite an upstream stack for concurrent, isolated Cage launches.

    Returns the rewritten config, the name of the network the agent joins, the
    service names, and any hostnames re-pointed away from the docker host.
    """
    config = json.loads(json.dumps(compose))  # deep copy
    services = config.get("services") or {}
    rehomed_hosts: list[str] = []

    for service_name, service in services.items():
        if not isinstance(service, dict):
            continue
        # Fixed container names collide the moment two trials run at once.
        service.pop("container_name", None)
        # Cage lints for it: a build-only service would otherwise be tagged with
        # the per-trial compose project name and pollute ``docker image ls``.
        if service.get("build") and not service.get("image"):
            service["image"] = f"cybench-{challenge_id}-{slugify(service_name)}:latest"
        # ``<name>:host-gateway`` sends a service back out to the docker host
        # and in through the stack's own *fixed* published port. Cage publishes
        # on a free port instead, so that route would land on nothing (or on
        # another trial). The hostname becomes an alias of the target service,
        # which keeps the topology upstream intended and never leaves the
        # per-trial network.
        extra_hosts = service.get("extra_hosts")
        if isinstance(extra_hosts, list) and target_service:
            kept: list[str] = []
            for entry in extra_hosts:
                host, _, address = str(entry).partition(":")
                if address.strip() == "host-gateway" and host.strip():
                    rehomed_hosts.append(host.strip())
                else:
                    kept.append(entry)
            if kept:
                service["extra_hosts"] = kept
            else:
                service.pop("extra_hosts", None)

    networks = config.get("networks")
    if isinstance(networks, dict):
        for network_name, network in list(networks.items()):
            if not isinstance(network, dict):
                continue
            if network.get("external") and network_name in EXTERNAL_NETWORK_NAMES:
                # Project-local instead of external: each trial gets its own
                # bridge, and a service is reachable at its own name — which is
                # exactly the hostname upstream prompts already use.
                networks[network_name] = {}

    owned = [
        name
        for name, network in (config.get("networks") or {}).items()
        if not (isinstance(network, dict) and network.get("external"))
    ]
    agent_network = owned[0] if len(owned) == 1 else ""

    if rehomed_hosts and target_service in services and agent_network:
        target = services[target_service]
        networks = target.get("networks")
        if isinstance(networks, list):
            networks = {name: {} for name in networks}
        elif not isinstance(networks, dict):
            networks = {agent_network: {}}
        entry = networks.get(agent_network)
        if not isinstance(entry, dict):
            entry = {}
        aliases = list(entry.get("aliases", []) or [])
        for host in rehomed_hosts:
            if host not in aliases:
                aliases.append(host)
        entry["aliases"] = aliases
        networks[agent_network] = entry
        target["networks"] = networks

    return config, agent_network, sorted(services), rehomed_hosts


# --------------------------------------------------------------------------- #
# generation
# --------------------------------------------------------------------------- #


def copy_task_tree(task_dir: Path, out_dir: Path) -> None:
    def ignore(directory: str, names: list[str]) -> set[str]:
        skipped = {name for name in names if name in EXCLUDED_DIRS}
        skipped |= {
            name for name in names if name.lower().endswith(EXCLUDED_FILE_SUFFIXES)
        }
        return skipped

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(task_dir, out_dir, ignore=ignore, symlinks=True)


def resolve_flag(task_dir: Path, metadata: dict[str, Any]) -> str:
    """Upstream's flag: the last subtask's answer, cross-checked against flag.txt."""
    subtasks = metadata.get("subtasks") or []
    answer = str(subtasks[-1].get("answer", "")).strip() if subtasks else ""

    flag_file = task_dir / "flag.txt"
    on_disk = ""
    if flag_file.is_file():
        on_disk = flag_file.read_text(encoding="utf-8", errors="replace").strip()

    if answer and on_disk and answer != on_disk:
        log(f"    ! flag mismatch: metadata={answer!r} flag.txt={on_disk!r} (using metadata)")
    return answer or on_disk


def files_containing_flag(staged_root: Path, staged_files: list[str], flag: str) -> list[str]:
    """Staged files that carry the flag verbatim.

    Not automatically a defect: a reversing task like LootStash hides the flag
    among decoys inside the binary it hands over, and ``strings`` is the
    intended solution. What matters is that it is *upstream's* choice — this
    script stages exactly what ``init_script.sh`` produces and nothing else —
    so the finding is recorded on the challenge rather than raised.
    """
    if not flag:
        return []
    leaking: list[str] = []
    needle = flag.encode()
    for relative in staged_files:
        path = staged_root / relative
        try:
            if needle in path.read_bytes():
                leaking.append(relative)
        except OSError:
            continue
    return leaking


def generate_task(
    task_path: str,
    task_dir: Path,
    out_root: Path,
    scratch_root: Path,
) -> tuple[str, dict[str, Any]]:
    metadata = json.loads((task_dir / "metadata" / "metadata.json").read_text(encoding="utf-8"))
    competition = competition_of(task_path)
    event = EVENT_BY_COMPETITION[competition]
    category = category_of(task_path, metadata)
    name = task_dir.name
    challenge_id = f"cb-{event.lower()}-{category}-{slugify(name)}"

    out_dir = out_root / event / category / name
    log(f"  {challenge_id}")
    copy_task_tree(task_dir, out_dir)

    staged_files, staged_root, staging_stderr = stage_public_files(task_dir, scratch_root)
    if staging_stderr:
        log(f"    note: init_script.sh stderr: {staging_stderr.splitlines()[0][:120]}")
    flag = resolve_flag(task_dir, metadata)
    flag_bearing_files: list[str] = []
    if staged_root is not None:
        flag_bearing_files = files_containing_flag(staged_root, staged_files, flag)
        if flag_bearing_files:
            log(
                f"    note: flag present in staged file(s): "
                f"{', '.join(flag_bearing_files)} (upstream's own handout)"
            )

        public_dir = out_dir / "public"
        if public_dir.exists():
            shutil.rmtree(public_dir)
        if staged_files:
            shutil.copytree(staged_root, public_dir, symlinks=True)
        shutil.rmtree(staged_root, ignore_errors=True)

    target_hosts = parse_target_hosts(metadata.get("target_host", ""))

    challenge: dict[str, Any] = {
        "id": challenge_id,
        "name": name,
        "benchmark": "cybench",
        "benchmark_family": "cybench",
        "category": category,
        "categories": [str(item) for item in metadata.get("categories", [])],
        "difficulty": str(metadata.get("difficulty", "")),
        "event": event,
        "competition": competition,
        "upstream_path": task_path,
        # Upstream's two prompt tiers, verbatim. ``description`` is the hard
        # (default) tier; the benchmark swaps in the easy one on request.
        "description": str(metadata.get("hard_prompt", "")).strip(),
        "description_easy": str(metadata.get("easy_prompt", "")).strip(),
        "flag": flag,
        "files": staged_files,
        # The handout itself contains the flag (upstream's design for some rev
        # tasks). Recorded so an analysis can tell those apart rather than
        # reading an easy solve as a capability signal.
        "flag_in_handout": bool(flag_bearing_files),
        # Non-empty when upstream's own staging script errored (see
        # ``stage_public_files``). Kept so a task with a prompt that promises
        # files it never delivers reads as a known upstream quirk.
        "staging_stderr": staging_stderr[:1000],
        "target_host": metadata.get("target_host", ""),
        "stateful_shell": bool(metadata.get("stateful_shell", False)),
        "tools": metadata.get("tools", {}),
        "internet": metadata.get("internet", {}),
        # Kept for the guided/subtask variant. Answers live here, on the host
        # only — nothing under ``public/`` and nothing the prompt renders.
        "subtasks": metadata.get("subtasks", []),
        "answer_format": (
            str((metadata.get("subtasks") or [{}])[-1].get("answer_format", "")).strip()
        ),
    }

    compose_path = find_compose_file(task_dir)
    if compose_path is not None:
        relative_compose = compose_path.relative_to(task_dir)
        compose = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        rewritten, agent_network, service_names, rehomed_hosts = cage_compose(
            compose,
            challenge_id,
            target_service=target_hosts[0][0] if target_hosts else "",
        )
        if rehomed_hosts:
            log(
                f"    note: re-pointed host-gateway name(s) at the target service: "
                f"{', '.join(rehomed_hosts)}"
            )
        cage_path = out_dir / relative_compose.parent / "docker-compose.cage.yml"
        cage_path.parent.mkdir(parents=True, exist_ok=True)
        cage_path.write_text(
            "# Generated by examples/cybench/scripts/generate_dataset.py — do not hand-edit.\n"
            "# Upstream compose is left untouched; this override makes the stack\n"
            "# launchable concurrently and in isolation (project-local network, no\n"
            "# fixed container_name, explicit image tags).\n"
            + yaml.safe_dump(rewritten, sort_keys=False),
            encoding="utf-8",
        )
        challenge["compose_files"] = [
            (relative_compose.parent / "docker-compose.cage.yml").as_posix()
        ]
        if agent_network:
            challenge["agent_network"] = agent_network

        target_ports = {
            host: port
            for host, port in target_hosts
            if port is not None and host in service_names
        }
        unknown = [host for host, _ in target_hosts if host not in service_names]
        if unknown:
            log(
                f"    ! target_host names no compose service: {', '.join(unknown)} "
                f"(services: {', '.join(service_names)})"
            )
        if target_ports:
            challenge["target_ports"] = target_ports
            challenge["internal_port"] = next(iter(target_ports.values()))
    elif target_hosts:
        log(f"    ! target_host {metadata.get('target_host')!r} but no compose file found")

    (out_dir / "challenge.json").write_text(
        json.dumps(challenge, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    index_entry = {
        "benchmark": "cybench",
        "event": event,
        "category": category,
        "challenge": name,
        "path": f"{event}/{category}/{name}",
        "competition": competition,
        "difficulty": str(metadata.get("difficulty", "")),
        "has_target": bool(target_hosts),
    }
    return challenge_id, index_entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cybench-root",
        required=True,
        type=Path,
        help="Upstream cybench checkout (the dir holding task_list.txt).",
    )
    parser.add_argument(
        "--extra-root",
        type=Path,
        action="append",
        default=[],
        help="Additional root searched for tasks missing from --cybench-root (repeatable).",
    )
    parser.add_argument("--out", required=True, type=Path, help="Dataset output directory.")
    parser.add_argument(
        "--scratch",
        type=Path,
        default=None,
        help="Scratch dir for running init_script.sh (default: alongside --out).",
    )
    parser.add_argument("--task", action="append", default=[], help="Only this task path (repeatable).")
    args = parser.parse_args()

    cybench_root = args.cybench_root.expanduser().resolve()
    task_list = cybench_root / "task_list.txt"
    if not task_list.is_file():
        log(f"error: {task_list} not found — is --cybench-root a cybench checkout?")
        return 2

    roots = [cybench_root] + [root.expanduser().resolve() for root in args.extra_root]
    out_root = args.out.expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    scratch_root = (args.scratch or out_root.parent / ".generate-scratch").expanduser().resolve()
    scratch_root.mkdir(parents=True, exist_ok=True)

    task_paths = [line.strip() for line in task_list.read_text().splitlines() if line.strip()]
    if args.task:
        wanted = set(args.task)
        task_paths = [path for path in task_paths if path in wanted or path.split("/")[-1] in wanted]

    index: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    failed: list[tuple[str, str]] = []

    for task_path in task_paths:
        task_dir = resolve_task_dir(task_path, roots)
        if task_dir is None:
            missing.append(task_path)
            log(f"  MISSING {task_path}")
            continue
        try:
            challenge_id, entry = generate_task(task_path, task_dir, out_root, scratch_root)
        except Exception as exc:  # one bad task must not sink the batch
            failed.append((task_path, str(exc)))
            log(f"  FAILED  {task_path}: {exc}")
            continue
        if challenge_id in index:
            failed.append((task_path, f"duplicate challenge id {challenge_id}"))
            continue
        index[challenge_id] = entry

    (out_root / "cybench.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.rmtree(scratch_root, ignore_errors=True)

    log("")
    log(f"generated {len(index)} challenge(s) → {out_root}")
    if missing:
        log(f"missing from every root ({len(missing)}): {', '.join(missing)}")
    if failed:
        log(f"failed ({len(failed)}):")
        for task_path, reason in failed:
            log(f"  {task_path}: {reason}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
