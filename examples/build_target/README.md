# Build Target benchmark

`build_target` is an artifact benchmark: an agent receives classified CTF
materials and produces a runnable CAGE target. Input material is classified by
role so the prompt does not treat every challenge as attachment-only Pwn.

## Prompt routing

The benchmark combines three independent prompt layers: the declared/inferred
`D0`-`D5` data tier, one build profile, and one category profile. D-tier prompts
set evidence limits and stop conditions; they do not grant an R level. The build
profile selects the reconstruction method:

| Build profile | Selected when | Required behavior |
|---|---|---|
| `official_deployment` | Dockerfile/Compose material exists | Reuse and minimally repair upstream deployment |
| `source_rebuild` | Service source exists without deployment | Derive a minimal deployment from source |
| `artifact_rehost` | Player artifacts exist without service source | Rehost only evidence-backed behavior |
| `triage` | Core material is missing | Report a structured blocker; do not fabricate a target |

Category profiles currently provide independent requirements for `web`, `pwn`,
and a `generic` fallback. An explicit `build_profile`/`build_strategy` in
`task.json` overrides automatic selection.

For Pwn, the queue records this fixed material priority:

1. Dockerfile/deployment + Writeup + attachments
2. Dockerfile/deployment + attachments
3. Writeup + attachments
4. source + attachments without Dockerfile/Writeup (fallback)
5. attachments only

The last class may still produce a speculative R3 image, but its historical
runtime authenticity remains `unverified_until_exp`; an ELF attachment alone
does not prove the glibc minor version.

## Local Pwn runtime bundles

Populate the local amd64 cache once from Ubuntu source images:

```bash
sg docker -c 'uv run --frozen python examples/build_target/scripts/cache_pwn_runtimes.py'
```

The catalog maps Ubuntu 16.04/18.04/20.04/22.04/24.04 to the glibc
2.23/2.27/2.31/2.35/2.39 series. The generated, gitignored cache contains a
matched `libc.so.6` and `ld-linux-x86-64.so.2` pair for each entry plus a
manifest with source image digests and file SHA256 values. CAGE copies the cache
read-only to `/opt/cage/pwn-runtimes` in Pwn agent containers; only the selected
pair should enter the produced build context.

Selection is evidence-driven: use the official Dockerfile when present;
otherwise infer from concrete Writeup clues. Checking `ldd --version` in the
newly constructed image is explicitly not historical validation because it only
reports the runtime the builder selected.

## Dataset contract

Each dataset child directory contains a `task.json`. `material_root` may point to
an external immutable source package; relative paths are resolved from the task
directory.

```json
{
  "id": "saj-2021-web-build-a-panel",
  "name": "build-a-panel",
  "category": "web",
  "data_tier": "D4",
  "material_root": "/data/sources/web/challenges/saj-2021-web-build-a-panel",
  "materials": {
    "deployment": ["source/docker-compose.yml", "source/app/Dockerfile"],
    "source": ["source/app"],
    "attachments": ["public/build-a-panel.tar.gz"],
    "writeups": ["evidence/writeups/community/writeup.md"]
  },
  "service_contract": {
    "protocol": "http",
    "internal_port": 31337,
    "readiness_path": "/"
  },
  "flag_contract": {
    "injection": "environment",
    "env_var": "FLAG",
    "format": "flag{...}"
  },
  "build_environment": {
    "network": "restricted"
  },
  "image_name": "ctfenv/web-build-a-panel-wave1:d4-r3-x0"
}
```

The legacy top-level `attachments` list is still accepted and classified by
filename. New datasets should use `materials` explicitly. Secret flag values do
not belong in `flag_contract`; only the injection mechanism and public format do.
All non-triage tasks require an explicit, non-`latest` `image_name` or
`image_names` tag.

## Remaining Wave 4 queue

The reproducible remaining-task queue lives under
examples/build_target/task_lists/wave4. It consumes the 1,456 Pwn/Web static
records, removes the 210 environments already admitted by the first three CAGE
build waves, keeps only confirmed D3-D5 in the runnable list, isolates D2, and policy-drops
D0/D1. Admission uses the confirmed tier, never the higher candidate tier;
candidate-only D3-D5 shapes remain in candidate_only.jsonl. The compact reader
list is build_tasks.tsv; build_tasks.jsonl carries the complete task contract
and provenance for materialization.

Regenerate it with:

    uv run --frozen python examples/build_target/scripts/build_task_list.py --static-materials /mnt/olddata/home/yihe/workspace/ctf-env-collection/catalog/static_materials.jsonl --source-repo /mnt/olddata/home/yihe/workspace/ctf-env-collection --completed-manifest /mnt/olddata/home/yihe/workspace/ctf-env-collection/work/env-candidates/cage-wave1/metadata/inventory.json --completed-manifest /mnt/olddata/home/yihe/workspace/ctf-env-collection/work/cage-wave2/FINAL_SUCCESS.json --completed-manifest /mnt/olddata/home/yihe/workspace/ctf-env-collection/work/cage-pwn-wave3/FINAL_SUCCESS.json --wave wave4 --output-dir examples/build_target/task_lists/wave4

## R3 and R4 validation

`target_maturity.rehost` controls the independent gate:

- `R3`: clean Compose build, stable target containers, exact local archival
  image tag, and retained image ID.
- `R4`: all R3 checks plus `challenge.json.runtime_probes`. Each HTTP/TCP probe
  must assert challenge-specific response content, cite a supplied
  Writeup/solve file, and pass when executed by the host-side CAGE validator.

The validator writes `runtime_probe_evidence.json`; agent-authored
`service_output.txt`, a listening port, or container liveness cannot promote an
environment to R4. R5 remains separate and requires current-instance
vulnerability/flag-chain evidence.

For a small audited calibration subset, materialize explicit IDs from the
generated queue and promote their target/image maturity to R4:

```bash
uv run --frozen python examples/build_target/scripts/materialize_r4_calibration.py \
  --queue examples/build_target/task_lists/wave4/build_tasks.jsonl \
  --ids /path/to/calibration_ids.txt \
  --output-dir .cage/build-target/calibration-r4-datasets \
  --run-root examples/build_target/.cage_runs
```

The materializer rejects candidates without confirmed deployment and Writeup
evidence, missing Docker closure references, known prior runtime blockers, or a
previous `image_manifest.json`. Pwn candidates must belong to the strongest
Dockerfile + Writeup + attachments class.

## Checks and execution

```bash
cage benchmark check build_target --sample SAMPLE --show-prompt
cage run build_target --sample SAMPLE --agent AGENT --model MODEL --passk 1
```

The scorer independently executes `docker compose up --build`, checks every
declared target service, enforces the Compose safety policy, verifies every
archival tag belongs to a build-backed service, and retains passing images in
the local Docker daemon. For R4 tasks it then executes the source-backed
semantic probes before writing `image_manifest.json`. Random-flag and exploit
validation are intentionally not inferred from this result.

The Compose safety policy rejects `privileged`, host namespaces, host mounts,
devices, `cap_add: [ALL]`, host-administration capabilities such as
`cap_add: [SYS_ADMIN]`, and unconfined AppArmor/seccomp profiles.
