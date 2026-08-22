# Pipeline prompt authoring contract (build_target env-gen ⊕ exp-gen)

You are authoring **Jinja2 prompt fragments** for the build_target benchmark's
route-keyed generation pipelines. Read this whole contract before writing.

## Layout (where files go)

```
prompts/pipelines/
  env/instance.j2         # env-gen ENTRY (already written — do NOT edit)
  env/routes/<route>.j2   # per-route ENV strategy   <-- you may author these
  env/categories/<cat>.j2 # pwn|web|generic env specifics (reused from existing)
  exp/instance.j2         # exp-gen ENTRY (already written — do NOT edit)
  exp/routes/<route>.j2   # per-route EXP strategy   <-- you may author these
  exp/categories/<cat>.j2 # pwn|web|generic exp specifics
```

Each `instance.j2` includes exactly one `routes/<route>.j2` and one
`categories/<cat>.j2`. Your fragment is dropped under a `# ROUTE STRATEGY`
heading that the entry already prints — so **start at the body, no top-level
`#` heading of your own** (use `##` sub-headings if needed).

## The 9 routes (profile → route → sources)

| route | profile | build_source | exploit_source |
|---|---|---|---|
| fast_track_full | AWPB | use_build_material | adapt_existing |
| fast_track_no_writeup | APB | use_build_material | adapt_existing |
| build_then_solve | AB | use_build_material | generate_from_attachment |
| build_then_generate | AWB | use_build_material | generate_from_writeup |
| infer_env_from_exp | AP | infer_from_exploit | adapt_existing |
| infer_env_then_adapt | AWP | infer_from_writeup | adapt_existing |
| infer_both_from_writeup | AW | infer_from_writeup | generate_from_writeup |
| enrich_materials | A | none | none |
| candidate_inventory_only | NO_A | none | none |

Material bits: **A**=attachment, **W**=writeup, **P**=public exploit/solver,
**B**=build material (Dockerfile/compose/deploy).

## Jinja variables available in your fragment

- `instance_data.route.pipeline_route` / `.material_profile` / `.build_source` /
  `.exploit_source` / `.summary` / `.build_mode`
- `instance_data.route.env_context_roles` / `.exp_context_roles` — the material
  roles the entry already surfaced (attachments/writeups/exploit/deployment/source).
- `instance_data.materials.<role>` — list of paths for a role (may be empty).
- `instance_data.category_profile` (pwn|web|generic), `instance_data.name`,
  `instance_data.service_contract`, `instance_data.flag_contract`,
  `instance_data.image_names`, `instance_data.pwn_runtime`,
  `instance_data.pwn_material_priority`.
- `workspace` — the agent workspace path string.
Keep Jinja simple: `{% if %}`, `{% for %}`, `{{ ... }}`. No new includes.

## What an ENV route fragment must say (tailored to build_source)

- **use_build_material** (AWPB/APB/AB/AWB): the deployment (B) is the primary
  implementation. Audit and reuse it; smallest evidence-backed compatibility
  repairs only; each repair recorded in `build_report.json`. AWPB/AWB may use
  the writeup for behavioral understanding; APB/AB have none.
- **infer_from_exploit** (AP): there is NO build material. Reverse-engineer the
  runtime FROM the exploit — libc from leaked-address offsets / one_gadget /
  symbol assumptions, loader/arch from the binary, protections the exploit
  relies on (NX/PIE/canary/RELRO). Author a Dockerfile that realizes that
  inferred runtime. The environment and exploit co-evolve; the inference is a
  hypothesis the exploit stage will confirm or refute. Cite the exact exploit
  lines each inference rests on.
- **infer_from_writeup** (AWP/AW): no build material. Infer the runtime from the
  writeup's concrete clues (named Ubuntu/glibc, libc build-id, allocator notes,
  offsets). AWP additionally has the exploit as corroborating runtime evidence.

## What an EXP route fragment must say (tailored to exploit_source)

- **adapt_existing** (AWPB/APB/AP/AWP): a confirmed exploit/solver (P) exists.
  Port it to the rebuilt live target — fix addresses/offsets/endpoints for the
  actual instance, not the historical one. Do NOT rewrite the approach; adapt it.
- **generate_from_writeup** (AWB/AW): no exploit exists, but the writeup
  describes the intended path. Synthesize an exploit that follows the writeup's
  primitive and success signal.
- **generate_from_attachment** (AB): no exploit and no writeup. Derive the
  exploit from binary/attachment analysis (find the vuln, build the primitive).
  Hardest; be explicit about the analysis steps.

Every EXP fragment ends at the same success bar: the exploit, run from the
player vantage against a fresh clean instance, captures the harness-provisioned
flag (or triggers the intended crash/primitive). Never hardcode a flag.

## Style (match the existing build_target prompts)

- Terse, imperative, evidence-first. No filler, no "you should consider".
- Every inference must cite the exact supplied path it rests on.
- Prefer honest structured blockers over fabricated success.
- ~15–40 lines per fragment. Do not restate what the entry already covers
  (safety, output contract, validator workflow) — only the route-specific
  strategy.
