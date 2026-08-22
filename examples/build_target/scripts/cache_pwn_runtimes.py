#!/usr/bin/env python3
"""Populate the local amd64 Pwn libc/loader bundle cache from Ubuntu images."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXAMPLE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = EXAMPLE_DIR / "pwn_runtime_catalog.json"
DEFAULT_CACHE = EXAMPLE_DIR / ".cage" / "build-target" / "pwn-runtimes"


def _run(
    command: list[str], *, capture: bool = True, timeout: int = 60
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=capture,
        timeout=timeout,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("bundles"), list):
        raise ValueError(f"invalid runtime catalog: {path}")
    return raw


def _image_inspect(docker: str, image: str) -> dict[str, Any] | None:
    result = subprocess.run(
        [docker, "image", "inspect", image],
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        return None
    payload = json.loads(result.stdout)
    return dict(payload[0]) if payload else None


def _ensure_image(docker: str, image: str, pull_policy: str) -> dict[str, Any]:
    inspected = _image_inspect(docker, image)
    if pull_policy == "always" or (pull_policy == "missing" and inspected is None):
        _run(
            [docker, "pull", "--platform", "linux/amd64", image],
            capture=False,
            timeout=600,
        )
        inspected = _image_inspect(docker, image)
    if inspected is None:
        raise RuntimeError(f"image {image} is not cached and pull policy is {pull_policy!r}")
    if inspected.get("Architecture") != "amd64":
        raise RuntimeError(
            f"image {image} has architecture {inspected.get('Architecture')!r}, expected amd64"
        )
    return inspected


def _copy_pair(
    docker: str,
    image: str,
    bundle: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, Path]:
    container_id = _run(
        [docker, "create", "--platform", "linux/amd64", image, "/bin/true"]
    ).stdout.strip()
    if not container_id:
        raise RuntimeError(f"docker create returned no container id for {image}")
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        libc_path = output_dir / "libc.so.6"
        loader_path = output_dir / "ld-linux-x86-64.so.2"
        _run(
            [
                docker,
                "cp",
                "-L",
                f"{container_id}:{bundle['libc_container_path']}",
                str(libc_path),
            ]
        )
        _run(
            [
                docker,
                "cp",
                "-L",
                f"{container_id}:{bundle['loader_container_path']}",
                str(loader_path),
            ]
        )
    finally:
        try:
            subprocess.run(
                [docker, "rm", "-f", container_id],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            pass
    for path in (libc_path, loader_path):
        path.chmod(0o755)
    return libc_path, loader_path


def _artifact(path: Path, staging_root: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(staging_root).as_posix(),
        "sha256": _sha256(path),
        "size": path.stat().st_size,
    }


def populate(
    *, catalog_path: Path, cache_dir: Path, docker: str, pull_policy: str
) -> dict[str, Any]:
    catalog = _load_catalog(catalog_path)
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pwn-runtimes-", dir=str(cache_dir.parent)) as temp_dir:
        staging_root = Path(temp_dir)
        manifest_bundles: list[dict[str, Any]] = []
        for catalog_bundle in catalog["bundles"]:
            bundle = dict(catalog_bundle)
            image = str(bundle["source_image"])
            inspected = _ensure_image(docker, image, pull_policy)
            bundle_dir = staging_root / str(bundle["id"])
            libc_path, loader_path = _copy_pair(docker, image, bundle, bundle_dir)
            expected_series = str(bundle["glibc_series"])
            if expected_series.encode() not in libc_path.read_bytes():
                raise RuntimeError(
                    f"{bundle['id']} libc does not contain expected glibc series {expected_series}"
                )
            manifest_bundles.append(
                {
                    **bundle,
                    "source_image_id": inspected.get("Id"),
                    "source_image_repo_digests": inspected.get("RepoDigests") or [],
                    "libc": _artifact(libc_path, staging_root),
                    "loader": _artifact(loader_path, staging_root),
                }
            )

        manifest = {
            "schema_version": "cage-pwn-runtime-cache-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "catalog_path": str(catalog_path.resolve()),
            "catalog_sha256": _sha256(catalog_path),
            "selection_policy": "deployment_or_writeup_evidence_not_container_self-report",
            "bundles": manifest_bundles,
        }
        (staging_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        previous = cache_dir.with_name(f"{cache_dir.name}.previous")
        if previous.exists():
            shutil.rmtree(previous)
        if cache_dir.exists():
            os.replace(cache_dir, previous)
        try:
            os.replace(staging_root, cache_dir)
        except Exception:
            if previous.exists() and not cache_dir.exists():
                os.replace(previous, cache_dir)
            raise
        if previous.exists():
            shutil.rmtree(previous)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--docker", default="docker")
    parser.add_argument(
        "--pull-policy",
        choices=("missing", "always", "never"),
        default="missing",
        help="Pull source images only when missing by default.",
    )
    args = parser.parse_args()
    manifest = populate(
        catalog_path=args.catalog.resolve(),
        cache_dir=args.cache_dir.resolve(),
        docker=args.docker,
        pull_policy=args.pull_policy,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
