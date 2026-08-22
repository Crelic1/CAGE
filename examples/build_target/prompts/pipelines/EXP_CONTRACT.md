# build_target EXP-gate contract (R5 fusion tier) — v3

Single source of truth binding the **prompt side** (`pipelines/full/instance.j2`
+ route/category fragments) and the **validator side** (`benchmark.py`
`_run_exploit_validation` + `_write_managed_runtime_compose` flag injection).
Both halves MUST agree on the field names below.

## The rehost ladder, extended by one rung

    R3  build + boot + port liveness              (existing)
    R4  build + boot + semantic runtime_probe     (existing)
    R5  build + boot + INTENDED EXPLOIT captures a freshly-minted random flag  (NEW)

R5 is a **bonus rung above R4** for the persisted score: a failed exploit does
not erase build/runtime evidence already earned at R3/R4. During a joint live
episode, however, `cage-check` returns a non-zero objective checkpoint result
until R5 capture succeeds, so the agent can repair and retry instead of learning
about failure only after it exits.

Both live validation and final scoring mint private random flags. Live feedback
returns pass/capture status, bounded per-attempt metadata, and, when safe, a
bounded solver-output tail; output containing the private minted value is never
returned. Final scoring
then repeats the same clean-instance protocol with new flags, preserving the
independent-replay and anti-hardcoding property.

## What the agent produces (read by the validator)

1. **`solve/`** — a directory holding the exploit. Self-contained; targets the
   address the harness passes in via env, never a hardcoded host/port.

2. **`challenge.json` additions** (all optional; validator supplies defaults):

   ```jsonc
   {
     // ... existing compose_files / target_ports / runtime_probes ...
     "flag_contract": {
       "inject": "file",            // "file" | "env"
       "service": "challenge",      // compose service the flag lands in
       "path": "/flag.txt",         // inject=="file": absolute path inside the service
       "env": "FLAG",               // inject=="env": env var name on the service
       "format": "FAKE{...}"        // authoritative prefix/shape hint; body is fresh
     },
     "solve": {
       "entry": "python3 solve.py", // how to run the exploit; CWD is /solve
       "service": "challenge",      // which target service the exploit hits
       "image": "cage/build-target-solver:2026-08-v1" // OPTIONAL solver runtime; default below
     }
   }
   ```

   Defaults when absent: `flag_contract = {inject:"file", service:<first target
   service>, path:"/flag.txt"}`; `solve.service = <first target service>`;
   `solve.image = cage/build-target-solver:2026-08-v1`; `solve.entry` is required for the
   gate to run (no entry -> gate is skipped, build stays at R3/R4).

3. **`solve_report.json`** — `status` (`solved`|`unresolved`),
   `material_profile`, `pipeline_route`, `exploit_source`, `entry`, `primitive`,
   `success_signal`, env-fidelity changes, and (for `unresolved`) a non-empty
   `blockers[]`. The captured flag observation is quoted here on success, but the
   validator's independent capture — not this file — is what grants R5.

## What the validator does (the R5 gate)

Slots into `_run_validation` immediately after the probe block, before `_pass`,
guarded by `contract["exploit_required"]` and `solve.entry` present:

1. **Build once** with the authoritative managed Compose build. The resulting
   image is retained for the whole R5 replay series.
2. Before **each** solver invocation, destroy the preceding Compose target and
   its non-external volumes, mint a new flag whose ordinary `PREFIX{...}` prefix
   comes from `flag_contract.format`, and recreate the target with
   `--no-build --force-recreate --renew-anon-volumes`. Invalid/unusual format
   hints safely fall back to `FAKE{...}`.
3. **Inject** that attempt's flag before its target boots, via the managed
   Compose overlay:
   - `inject=="file"`: write `flag` to a temp file, bind-mount it read-only at
     `path` on `service` (overwrites any placeholder baked into the image).
   - `inject=="env"`: set `environment: {<env>: flag}` on `service`.
4. **Resolve the recreated target** again: record its new container ID, network,
   address, and the non-secret fingerprint of its new flag. Never reuse the
   endpoint/state object captured for a preceding container.
5. **Run the solver** from a player vantage in a disposable sidecar, up to
   five independent attempts:
   `docker run --rm --network <target_net> -e TARGET_HOST=<container_addr>
   -e TARGET_PORT=<internal_port> --mount
   type=bind,src=<ws>/solve,dst=/solve,readonly -w /solve <image>
   sh -c "<entry>"`. Each invocation has its own timeout and captured
   stdout+stderr. Stop early on success.
6. **Oracle (1-of-5)**: an attempt passes when that attempt's exact minted flag
   occurs in stdout/stderr. Any one of the five attempts promotes the
   environment to `validated_rehost_tier="R5"`; 5/5 success is not required.
   Exit code, timeout-after-capture, and output-limit-after-capture are retained
   as separate solver-hygiene evidence and do not revoke environment R5. If all
   attempts fail to capture an exact flag, keep
   the R3/R4 verdict and attach an **attribution-neutral** observation — a failed
   `(env, exploit)` pair is never auto-blamed on one side.

The solver's own retry loop follows the same independence rule. Expected
per-attempt exceptions are caught inside that loop, and mutable library state is
reset before reconnecting. A common example is pwntools `ELF.address`: rebasing
changes `symbols`, so save the original offset or reset `.address = 0` before
computing another base. Production success is gated by an exact declared-format
flag match in received target bytes; non-empty output, a shell prompt, a
successful read, or rc=0 alone is never its success predicate. Validate the
production loop and its exception path, not only a one-off diagnostic call.
The `/solve` mount is read-only: after emitting the exact flag, flush and exit
zero without trying to persist the flag or optional debug artifacts there. A
dirty exit remains a bug to fix, but it does not erase the exact capture.
Library `timeout=` parameters may be idle deadlines that reset on continuous
input, so the production solver also needs a monotonic whole-process deadline
and a received-byte bound. Stop as soon as the exact flag is found. The harness
terminates a solver once combined stdout/stderr exceeds 8 MiB.

Only the image build is shared. Target processes, heap/VM state, writable
volumes, and private flags are not shared between attempts. A failed attempt
may crash or permanently mutate its target without poisoning the next one.

## Env contract the harness passes to the exploit

- `TARGET_HOST` — the target service container IP on the isolated network.
- `TARGET_PORT` — its internal port.
- CWD is `/solve` (the agent's `solve/` mounted read-only).
- The solver image carries pwntools / requests / pycryptodome (default
  `cage/build-target-solver:2026-08-v1`, built once on the runner). It is a
  CAGE-reserved tag: challenge Compose may reference neither it nor the legacy
  `buildtarget/solver:latest` on a service with `build:`. At run start the
  validator checks its ownership/dependencies and pins the tag to a content ID.

## Live recovery and final replay

- `cage-check` first freezes the whole submitted workspace, records its digest,
  then validates that immutable copy through contract, build/boot, and any
  semantic runtime probe. Host scheduling waits on that submission rather than
  asking the agent to poll and resubmit mutable files.
- When the route requires an exploit and `exploit_gate` is enabled, a result
  below R5 is returned as checkpoint `exploit_capture=FAIL` with factual
  observation and per-attempt return-code evidence. R3/R4 remains recorded as
  the highest reached tier.
- R5 returns `exploit_capture=PASS`; the agent stops the retained runtime and
  exits. `cage-check stop` seals live success only if build/solve/contracts still
  match the passing runtime signature; report-only finalization may change.
- A retained diagnostic target has a `runtime_id` and generation. Before using
  an address from an earlier result, `cage-check status --json` must confirm the
  same current lease and that the agent is attached to its network.
- The ordinary scorer repeats the entire validation with a newly minted flag.

## Feature flag / rollout

- New scorer behaviour -> **force a fresh run-id** (`--resume` refuses cross-scorer).
- Gated by `BuildTarget(exploit_gate=<bool>)` (default OFF until obs-validated),
  independent of `pipeline_prompts`. When OFF, behaviour is byte-identical to today.
