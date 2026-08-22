#!/usr/bin/env python3
"""Reconstruct binary-only grading data straight from ``n132/arvo`` image tars.

CyberGym's *binary* grading backend (``binary_dir:`` in the experiment YAML)
runs a tiny base runner over **prebuilt** vul/fix artifacts laid out as::

    <binary_dir>/arvo/<id>/<mode>/
        arvo            # the image's /bin/arvo entrypoint script (verbatim)
        out/<fuzzer>    # the task entrypoint plus required /out runtime tree
        libs/           # the fuzzer's shared-lib closure minus base-system libs

Upstream publishes this layout (``cybergym-server-data.7z``) only for the **1507
CyberGym tasks** — it is a *downloaded*, already-built artifact; nothing in the
codebase builds it. The 3480-task *arvo-external* catalog has no such download,
but we usually hold its per-task ``n132/arvo:<id>-<mode>`` image tars. This tool
reconstructs the binary layout from those tars so arvo-external can run in binary
mode too.

Principle: we do **not** ``docker load`` the multi-GB images (that floods the
docker overlay store and reads the whole NAS tar). An ``n132/arvo`` tar is an OCI
archive — ``manifest.json`` + gzipped rootfs layer blobs — so we open it as a
plain archive and pull the three things we need straight out of the layers, with
no docker daemon involved at all:

  * **arvo**: the merged-filesystem ``/bin/arvo`` (top layer wins, whiteouts honoured);
  * **out/**: the task entrypoint the ``arvo`` script invokes (``/out/<name>
    /tmp/poc``), plus the direct runtime data/sidecars that wrapper scripts
    reference (for example ``jazzer_driver``, ``.pkg`` loaders, jars/classes),
    plus any in-image ``/out/lib/...`` dependencies resolved via ``$ORIGIN``;
  * **libs/**: the fuzzer's transitive ``DT_NEEDED`` closure (parsed statically
    from the ELF — no ``ldd``, no execution) restricted to libraries whose
    basename is NOT in :data:`BASE_SYSTEM_LIBS`. The base runner ships those at a
    compatible version; everything else (openssl/krb5/gnutls/sqlite/…, plus
    libatomic/libutil) is bundled with its exact build-time version. The denylist
    was derived empirically from all 1368 upstream ``libs/`` dirs and the result
    verified byte-for-byte (see ``--verify-against``).

Binary mode needs BOTH builds, so by default a task is emitted only when both its
vul and fix tars exist (``--only-both``); the rest are reported skipped (their fix
image is simply absent — a data gap binary mode cannot invent). Resumable: a task
whose output already exists is skipped. No docker, no local image store growth.

Usage
-----
    # Reconstruct the arvo-external binaries we hold both images for:
    python scripts/extract_server_binaries.py \
        --image-cache /path/to/arvo-external/image-cache \
        --catalog datasets/arvo.json \
        --out /your/arvo-external-server-data

    # Validate the contract against the shipped upstream layout (writes to tmp):
    python scripts/extract_server_binaries.py \
        --image-cache datasets/image-cache \
        --task-ids 10400,10865,20694 \
        --out /tmp/verify --verify-against datasets/server-binary
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import posixpath
import re
import struct
import sys
import tarfile
from pathlib import Path

# Per-task image tar layout inside an image cache: ``<cache>/n132_arvo/<tag>.tar``
# (mirrors CyberGym's _cache_tar_path: repo "n132/arvo" -> "n132_arvo").
TAR_SUBDIR = "n132_arvo"
MODES = ("vul", "fix")

# The entrypoint script lives at /bin/arvo, but on merged-usr image bases
# (/bin -> /usr/bin) the real file is /usr/bin/arvo. Accept either.
ARVO_PATHS = ("bin/arvo", "usr/bin/arvo")

# Directories an ldd-style search would consult for a SONAME, in resolution order.
LIB_DIRS = (
    "lib/x86_64-linux-gnu", "usr/lib/x86_64-linux-gnu", "usr/local/lib",
    "lib/i386-linux-gnu", "usr/lib/i386-linux-gnu",
    "usr/lib", "lib", "lib64", "usr/lib64", "usr/local/lib64",
    "lib32", "usr/lib32",
)

# Libraries the base runner (oss-fuzz-base-runner, Ubuntu 16.04/glibc) provides at
# a compatible version, so they are NOT bundled — overriding the loader or one
# glibc member while the rest come from the runner is unsafe, and the rest are
# stock. Everything else in the closure IS bundled at its exact build-time
# version. Derived from all 1368 upstream libs/ dirs: these basenames never
# appear there; every app lib does.
BASE_SYSTEM_LIBS = frozenset({
    "ld-linux-x86-64.so.2", "ld-linux.so.2", "linux-vdso.so.1", "linux-gate.so.1",
    "libc.so.6", "libm.so.6", "libdl.so.2", "libpthread.so.0", "librt.so.1",
    "libresolv.so.2", "libnsl.so.1", "libgcc_s.so.1",
    "libstdc++.so.6", "libz.so.1", "libbz2.so.1.0", "liblzma.so.5",
    "libcom_err.so.2", "libkeyutils.so.1",
})

_OUT_TOKEN = re.compile(r"/out/([A-Za-z0-9_.\-]+)")
_SCRIPT_TOKEN = re.compile(r"(?<![A-Za-z0-9_.\-])([A-Za-z0-9_.\-]+)(?![A-Za-z0-9_.\-])")


def _is_fuzz_aux(base: str) -> bool:
    """libFuzzer/AFL build & fuzzing artifacts that are NOT runtime data for a
    single-PoC reproduction (and which upstream excludes): the corpus, the
    mutation dictionary, the per-target ``.options`` (read by libFuzzer at run
    time — could alter crash behaviour), static driver archives, afl tooling.
    Real runtime data (``magic.mgc``, hunspell ``.dic``/``.aff``, …) is NOT here.
    """
    return (
        base.endswith((".dict", ".options", ".a"))
        or "seed_corpus" in base
        or base.startswith(("afl-", "afl_"))
    )


# --------------------------------------------------------------------------- #
# OCI image-tar reading (no docker)
# --------------------------------------------------------------------------- #

def _layer_blobs(outer: tarfile.TarFile) -> list[str]:
    """Ordered layer blob member names (base -> top) from the image manifest."""
    man = json.loads(outer.extractfile("manifest.json").read())
    return list(man[0]["Layers"])


def _norm(name: str) -> str:
    return name[2:] if name.startswith("./") else name


def _iter_layer_members(outer: tarfile.TarFile, blob: str):
    """Yield (TarInfo, layer_tar) for a rootfs layer blob.

    Layer blobs may be gzip-compressed (docker-save / OCI ``...tar.gzip``) or a
    plain tar (some ``crane`` tarball outputs). Read them as a streaming tar so
    large ARVO images do not need a full in-memory decompression of the whole
    layer blob before we can inspect the few files we actually keep.
    """
    layer_stream = outer.extractfile(blob)
    if layer_stream is None:
        return
    with tarfile.open(fileobj=layer_stream, mode="r|*") as layer:
        for m in layer:
            yield m, layer


def _is_lib(path: str) -> bool:
    base = path.rsplit("/", 1)[-1]
    if ".so" not in base:
        return False
    head, _, _ = path.rpartition("/")
    return head in LIB_DIRS or head == "out" or head.startswith("out/")


def _collect_merged(
    outer: tarfile.TarFile,
) -> tuple[bytes | None, dict[str, bytes], dict[str, str]]:
    """One base->top sweep: merged /bin/arvo bytes, candidate lib file bytes, and
    candidate lib SYMLINKS (path -> target).

    SONAMEs in DT_NEEDED (e.g. ``libgnutls.so.30``) are usually symlinks to the
    real versioned file, so we must capture links too and resolve them — upstream
    stores the dereferenced content under the SONAME name. Honours OCI whiteouts
    (``.wh.<name>``); processing layers base->top makes a later re-add win.
    """
    arvo: bytes | None = None
    files: dict[str, bytes] = {}
    links: dict[str, str] = {}
    for blob in _layer_blobs(outer):
        for m, layer in _iter_layer_members(outer, blob):
            name = _norm(m.name)
            base = name.rsplit("/", 1)[-1]
            if base.startswith(".wh."):
                victim = name[: -len(base)] + base[len(".wh."):]
                files.pop(victim, None)
                links.pop(victim, None)
                if victim in ARVO_PATHS:
                    arvo = None
                continue
            if name in ARVO_PATHS and m.isfile():
                arvo = layer.extractfile(m).read()
            elif _is_lib(name):
                if m.isfile():
                    files[name] = layer.extractfile(m).read()
                    links.pop(name, None)
                elif m.issym() or m.islnk():
                    links[name] = m.linkname
                    files.pop(name, None)
    return arvo, files, links


def _collect_out(outer: tarfile.TarFile) -> tuple[dict[str, bytes], dict[str, str]]:
    """Merged ``/out`` regular files + symlinks (any depth, whiteouts honoured)."""
    files: dict[str, bytes] = {}
    links: dict[str, str] = {}
    for blob in _layer_blobs(outer):
        for m, layer in _iter_layer_members(outer, blob):
            name = _norm(m.name)
            if not name.startswith("out/"):
                continue
            base = name.rsplit("/", 1)[-1]
            if base.startswith(".wh."):
                victim = name[: -len(base)] + base[len(".wh."):]
                files.pop(victim, None)
                links.pop(victim, None)
                continue
            if m.isfile():
                files[name] = layer.extractfile(m).read()
                links.pop(name, None)
            elif m.issym() or m.islnk():
                links[name] = m.linkname
                files.pop(name, None)
    return files, links


# --------------------------------------------------------------------------- #
# Minimal static ELF DT_NEEDED reader (ELF32/ELF64 LE) — no execution, no ldd
# --------------------------------------------------------------------------- #

def _elf_needed(data: bytes) -> list[str]:
    """Return the DT_NEEDED sonames of an ELF32/ELF64 little-endian object."""
    if len(data) < 52 or data[:4] != b"\x7fELF" or data[5] != 1:
        return []
    elf_class = data[4]
    if elf_class == 2:  # ELF64
        if len(data) < 64:
            return []
        e_shoff = struct.unpack_from("<Q", data, 0x28)[0]
        e_shentsize = struct.unpack_from("<H", data, 0x3A)[0]
        e_shnum = struct.unpack_from("<H", data, 0x3C)[0]
        sh_offset_off, sh_size_off, sh_link_off = 0x18, 0x20, 0x28
        dyn_unpack = "<qQ"
        dyn_entry_size = 16
    elif elf_class == 1:  # ELF32
        e_shoff = struct.unpack_from("<I", data, 0x20)[0]
        e_shentsize = struct.unpack_from("<H", data, 0x2E)[0]
        e_shnum = struct.unpack_from("<H", data, 0x30)[0]
        sh_offset_off, sh_size_off, sh_link_off = 0x10, 0x14, 0x18
        dyn_unpack = "<iI"
        dyn_entry_size = 8
    else:
        return []
    if not e_shoff or not e_shnum or not e_shentsize:
        return []
    if e_shoff + e_shnum * e_shentsize > len(data):
        return []
    dyn_off = dyn_region_size = strtab_idx = None
    sections = []
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        sh_type, = struct.unpack_from("<I", data, base + 4)
        sh_offset = struct.unpack_from("<I" if elf_class == 1 else "<Q", data, base + sh_offset_off)[0]
        sh_size = struct.unpack_from("<I" if elf_class == 1 else "<Q", data, base + sh_size_off)[0]
        sh_link = struct.unpack_from("<I", data, base + sh_link_off)[0]
        sections.append((sh_type, sh_offset, sh_size, sh_link))
        if sh_type == 6:  # SHT_DYNAMIC
            dyn_off, dyn_region_size, strtab_idx = sh_offset, sh_size, sh_link
    if dyn_off is None or strtab_idx is None or strtab_idx >= len(sections):
        return []
    if dyn_region_size is None or dyn_off + dyn_region_size > len(data):
        return []
    str_off, str_size = sections[strtab_idx][1], sections[strtab_idx][2]
    if str_off + str_size > len(data):
        return []
    strtab = data[str_off: str_off + str_size]
    needed: list[str] = []
    for off in range(dyn_off, dyn_off + dyn_region_size, dyn_entry_size):
        d_tag, d_val = struct.unpack_from(dyn_unpack, data, off)
        if d_tag == 0:  # DT_NULL
            break
        if d_tag == 1:  # DT_NEEDED
            end = strtab.find(b"\x00", d_val)
            if 0 <= d_val < len(strtab):
                if end < 0:
                    end = len(strtab)
                needed.append(strtab[d_val:end].decode("utf-8", "replace"))
    return needed


# SONAME search order: rpath ``$ORIGIN`` (the fuzzer's dir, /out) first, then the
# standard library directories — what the dynamic loader would consult.
SEARCH_DIRS = ("out", "out/lib", "out/lib64", "out/bin") + LIB_DIRS


def _resolve_path_with_name(
    path: str,
    files: dict[str, bytes],
    links: dict[str, str],
    depth: int = 0,
) -> tuple[str | None, bytes | None]:
    """Resolve an image path to (final_path, file_bytes), following symlinks."""
    if depth > 40:
        return None, None
    if path in files:
        return path, files[path]
    if path in links:
        tgt = links[path]
        parent = path.rsplit("/", 1)[0] if "/" in path else ""
        nxt = posixpath.normpath(tgt).lstrip("/") if tgt.startswith("/") \
            else posixpath.normpath(posixpath.join(parent, tgt))
        return _resolve_path_with_name(nxt, files, links, depth + 1)
    return None, None


def _resolve_path(path: str, files: dict[str, bytes], links: dict[str, str], depth: int = 0) -> bytes | None:
    """Resolve an image path to file bytes, following symlinks within the image."""
    return _resolve_path_with_name(path, files, links, depth)[1]


def _resolve_soname(soname: str, files: dict[str, bytes], links: dict[str, str]) -> tuple[str | None, bytes | None]:
    for d in SEARCH_DIRS:
        path, data = _resolve_path_with_name(f"{d}/{soname}", files, links)
        if data is not None:
            return path, data
    return None, None


def _script_sidecars(target: bytes, direct_paths: list[str]) -> set[str]:
    """Direct /out siblings that a wrapper script references by basename."""
    if target[:4] == b"\x7fELF":
        return set()
    text = target.decode("utf-8", "replace")
    refs: set[str] = set()
    for path in direct_paths:
        base = path.split("/", 1)[1]
        if _is_fuzz_aux(base):
            continue
        if _SCRIPT_TOKEN.search(base) and re.search(
            rf"(?<![A-Za-z0-9_.\-]){re.escape(base)}(?![A-Za-z0-9_.\-])", text
        ):
            refs.add(path)
    return refs


def _extract_out(
    out_files: dict[str, bytes],
    out_links: dict[str, str],
    fuzzer: str,
) -> dict[str, bytes]:
    """Merged ``/out`` runtime tree to ship for one task.

    Keep:
      * the task entrypoint itself;
      * direct non-ELF runtime data files (``magic.mgc``, jars/classes, etc.);
      * direct siblings explicitly referenced by a wrapper script (for example
        ``jazzer_driver`` or ``fuzz_search.pkg``).
    Additional nested ``out/lib/...`` dependencies are added later from the ELF
    closure once we know which binaries actually run.
    """
    target_path = f"out/{fuzzer}"
    _, target = _resolve_path_with_name(target_path, out_files, out_links)
    if target is None:
        return {}
    selected: dict[str, bytes] = {fuzzer: target}
    direct_paths = sorted(
        path for path in ({*out_files.keys(), *out_links.keys()})
        if path.startswith("out/") and path.count("/") == 1
    )
    for path in direct_paths:
        base = path.split("/", 1)[1]
        if base == fuzzer:
            continue
        _, data = _resolve_path_with_name(path, out_files, out_links)
        if data is None:
            continue
        if data[:4] != b"\x7fELF" and not _is_fuzz_aux(base):
            selected[base] = data
    for path in _script_sidecars(target, direct_paths):
        base = path.split("/", 1)[1]
        _, data = _resolve_path_with_name(path, out_files, out_links)
        if data is not None:
            selected[base] = data
    return selected


def _closure_libs(
    out_tree: dict[str, bytes],
    files: dict[str, bytes],
    links: dict[str, str],
) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """Bundle the transitive DT_NEEDED closure of every selected ELF.

    Returns:
      * ``libs/`` payloads for non-base-system libs resolved from image lib dirs;
      * additional ``out/...`` entries for dependencies resolved via the image's
        in-tree runtime layout (for example ``out/lib/librnp-0.so.0``).
    """
    bundled: dict[str, bytes] = {}
    extra_out: dict[str, bytes] = {}
    seen: set[str] = set()
    stack: list[bytes] = [data for data in out_tree.values() if data[:4] == b"\x7fELF"]
    while stack:
        data = stack.pop()
        for soname in _elf_needed(data):
            if soname in seen:
                continue
            seen.add(soname)
            resolved_path, resolved = _resolve_soname(soname, files, links)
            if resolved is None:
                continue
            stack.extend([resolved] if resolved[:4] == b"\x7fELF" else [])
            if resolved_path and resolved_path.startswith("out/"):
                extra_out[resolved_path.split("/", 1)[1]] = resolved
            elif soname not in BASE_SYSTEM_LIBS:
                bundled[soname] = resolved
    return bundled, extra_out


# --------------------------------------------------------------------------- #
# Per-task extraction
# --------------------------------------------------------------------------- #

def _fuzzer_from_arvo(arvo: bytes) -> str | None:
    text = arvo.decode("utf-8", "replace")
    for line in text.splitlines():
        m = _OUT_TOKEN.search(line)
        if m and "/tmp/poc" in line:
            return m.group(1)
    m = _OUT_TOKEN.search(text)
    return m.group(1) if m else None


def _extract_one(image_tar: Path, dest: Path) -> dict:
    """Extract arvo + out/<fuzzer> + libs/ for a single build into ``dest``."""
    with tarfile.open(image_tar) as outer:
        arvo, files, links = _collect_merged(outer)
        out_files_all, out_links = _collect_out(outer)
        if arvo is None:
            raise RuntimeError("no /bin/arvo in image")
        fuzzer = _fuzzer_from_arvo(arvo)
        if not fuzzer:
            raise RuntimeError("could not parse fuzz target from /bin/arvo")
        out_files = _extract_out(out_files_all, out_links, fuzzer)
        if fuzzer not in out_files:
            raise RuntimeError(f"no /out/{fuzzer} in image")

    bundled, extra_out = _closure_libs(out_files, files, links)
    out_files.update(extra_out)

    dest.mkdir(parents=True, exist_ok=True)
    # arvo script + fuzz target must be executable (the runner does
    # `/bin/bash /arvo` -> `/out/<fuzzer>`); upstream ships them 0755. tarfile
    # write_bytes drops the mode, so set it explicitly or grading dies with 126.
    (dest / "arvo").write_bytes(arvo)
    (dest / "arvo").chmod(0o755)
    out_dir = dest / "out"
    out_dir.mkdir(exist_ok=True)
    for name, data in out_files.items():     # target fuzzer + its data files
        path = out_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if data[:4] == b"\x7fELF" or data.startswith(b"#!"):
            path.chmod(0o755)
    (out_dir / fuzzer).chmod(0o755)
    libs_dir = dest / "libs"
    libs_dir.mkdir(exist_ok=True)
    for name, data in bundled.items():
        (libs_dir / name).write_bytes(data)
    return {"fuzzer": fuzzer, "libs": sorted(bundled)}


def _tar_for(cache: Path, ident: str, mode: str) -> Path:
    return cache / TAR_SUBDIR / f"{ident}-{mode}.tar"


def _run_task(job: tuple[str, str, str, bool]) -> dict:
    """Process one task (both builds). Module-level so it pickles for the pool.

    Returns a status record: ``status`` is one of skip_missing / skip_done /
    extracted / failed. Each task writes its own ``arvo/<id>/`` subtree, so tasks
    never collide and can run fully in parallel.
    """
    ident, cache_s, out_s, only_both = job
    cache, out = Path(cache_s), Path(out_s)
    tars = {m: _tar_for(cache, ident, m) for m in MODES}
    present = [m for m in MODES if tars[m].is_file()]
    if (only_both and len(present) < 2) or not present:
        return {"ident": ident, "status": "skip_missing"}
    task_dir = out / "arvo" / ident
    if all((task_dir / m / "arvo").is_file() for m in present):
        return {"ident": ident, "status": "skip_done"}
    try:
        info = {m: _extract_one(tars[m], task_dir / m) for m in present}
        return {"ident": ident, "status": "extracted", "info": info}
    except Exception as exc:  # noqa: BLE001
        return {"ident": ident, "status": "failed", "msg": str(exc)}


def _wanted_ids(args: argparse.Namespace, cache: Path) -> list[str]:
    if args.task_ids:
        raw = args.task_ids
        if Path(raw).is_file():
            raw = ",".join(
                l.strip() for l in Path(raw).read_text().splitlines()
                if l.strip() and not l.strip().startswith("#")
            )
        return [t.split(":", 1)[-1].strip() for t in raw.split(",") if t.strip()]
    if args.catalog:
        cat = json.loads(Path(args.catalog).read_text())
        return [k.split(":", 1)[-1] for k in cat if (cat[k].get("source") or "arvo") == "arvo"]
    return sorted({p.name[:-len("-vul.tar")] for p in (cache / TAR_SUBDIR).glob("*-vul.tar")})


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "MISSING"


def _verify(dest_root: Path, gt_root: Path, ident: str) -> list[str]:
    problems: list[str] = []
    for mode in MODES:
        a, b = dest_root / "arvo" / ident / mode, gt_root / "arvo" / ident / mode
        if not b.is_dir():
            continue
        if _sha(a / "arvo") != _sha(b / "arvo"):
            problems.append(f"{ident}/{mode}: arvo script differs")
        ao = {p.name: _sha(p) for p in (a / "out").glob("*")} if (a / "out").is_dir() else {}
        bo = {p.name: _sha(p) for p in (b / "out").glob("*")} if (b / "out").is_dir() else {}
        if ao != bo:
            problems.append(f"{ident}/{mode}: out/ differs ({sorted(ao)} vs {sorted(bo)})")
        al = {p.name: _sha(p) for p in (a / "libs").glob("*")} if (a / "libs").is_dir() else {}
        bl = {p.name: _sha(p) for p in (b / "libs").glob("*")} if (b / "libs").is_dir() else {}
        if set(al) != set(bl):
            problems.append(
                f"{ident}/{mode}: libs set differs (+{sorted(set(al)-set(bl))} -{sorted(set(bl)-set(al))})"
            )
        elif al != bl:
            problems.append(f"{ident}/{mode}: libs content differs {[k for k in al if al[k]!=bl[k]]}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--image-cache", required=True, type=Path, help="holds n132_arvo/<id>-<mode>.tar")
    ap.add_argument("--out", required=True, type=Path, help="binary_dir to populate (arvo/<id>/<mode>/)")
    ap.add_argument("--catalog", type=Path, help="task catalog json (e.g. datasets/arvo.json)")
    ap.add_argument("--task-ids", help="comma list or @file of ids to restrict to")
    ap.add_argument("--only-both", action="store_true", default=True,
                    help="emit a task only if BOTH vul+fix tars exist (default)")
    ap.add_argument("--allow-partial", dest="only_both", action="store_false")
    ap.add_argument("--verify-against", type=Path, help="ground-truth binary_dir to diff against")
    ap.add_argument("--limit", type=int, default=0, help="cap number of tasks (0 = all)")
    ap.add_argument("--jobs", "-j", type=int, default=1,
                    help="parallel worker processes (gzip is CPU-bound; tasks independent)")
    args = ap.parse_args()

    cache, out = args.image_cache.resolve(), args.out.resolve()
    ids = _wanted_ids(args, cache)
    if args.limit:
        ids = ids[: args.limit]
    out.mkdir(parents=True, exist_ok=True)

    stats = {"extracted": 0, "skipped_missing": 0, "skipped_done": 0, "failed": 0, "problems": []}
    jobs = [(ident, str(cache), str(out), bool(args.only_both)) for ident in ids]
    n = len(jobs)

    def _tally(i: int, rec: dict) -> None:
        ident, status = rec["ident"], rec["status"]
        if status == "skip_missing":
            stats["skipped_missing"] += 1
            return
        if status == "skip_done":
            stats["skipped_done"] += 1
        elif status == "extracted":
            stats["extracted"] += 1
            for m, r in rec.get("info", {}).items():
                print(f"[{i}/{n}] arvo:{ident} {m}: {r['fuzzer']} (+{len(r['libs'])} libs)")
        elif status == "failed":
            stats["failed"] += 1
            print(f"[{i}/{n}] arvo:{ident}: FAILED {rec.get('msg')}", file=sys.stderr)
            return
        if args.verify_against:
            probs = _verify(out, args.verify_against.resolve(), ident)
            stats["problems"].extend(probs)
            for p in probs:
                print(f"  VERIFY MISMATCH {p}", file=sys.stderr)
            if not probs:
                print(f"  verify OK arvo:{ident}")

    if args.jobs <= 1:
        for i, job in enumerate(jobs, 1):
            _tally(i, _run_task(job))
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futures = {ex.submit(_run_task, job): job[0] for job in jobs}
            for i, fut in enumerate(as_completed(futures), 1):
                _tally(i, fut.result())

    (out / "extract_manifest.json").write_text(json.dumps(stats, indent=2))
    print(f"\nextracted={stats['extracted']} done={stats['skipped_done']} "
          f"missing={stats['skipped_missing']} failed={stats['failed']} problems={len(stats['problems'])}")
    return 1 if (stats["failed"] or stats["problems"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
