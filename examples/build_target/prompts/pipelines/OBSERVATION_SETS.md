# Per-route observation sets (3 samples each)

Each route is optimized on a fixed 3-sample observation set. Runnable-now sets
are already materialized in `.cage/build-target/wave4-datasets`; the infer/enrich
routes need materialization from `ctf-env-collection/sources` first.

| route | profile | status | observation samples (3) |
|---|---|---|---|
| fast_track_full | AWPB | ✅ runnable | saj-2021-pwn-beyond-root, saj-2021-pwn-catastrophe, saj-2021-web-curly-fries |
| fast_track_no_writeup | APB | ✅ runnable | saj-2021-pwn-baby-ctf-simulator, saj-2021-pwn-bpf-badjmp, saj-2021-web-cookie-spinner |
| build_then_solve | AB | ✅ runnable | saj-2023-pwn-babyzeroday, saj-2023-pwn-fipc, saj-2021-web-saasme |
| build_then_generate | AWB | ⚠️ only 1 in wave4 | saj-2022-pwn-solidarity + 2 to materialize |
| infer_env_from_exp | AP | ❌ materialize | from DB: gh-0062f (contrail/babyheap), gh-00c37 (ais3/pwn2), gh-017ad (USCC/babybof64) |
| infer_env_then_adapt | AWP | ❌ materialize | gh-011a9 (htb/pandoras box), gh-03a9c (player/boring), gh-04555 (PicoCTF/gps) |
| infer_both_from_writeup | AW | ❌ materialize | gh-00215 (hitcon), gh-01d0a (WaniCTF/only-once), gh-035df (THM/precision) |
| enrich_materials | A | n/a (blocked) | — not production-eligible |
| candidate_inventory_only | NO_A | n/a (blocked) | — not production-eligible |

## Optimization loop (per route)

1. Run the 3 samples through the route-keyed pipeline (env-gen now; exp-gen once
   the `cage-exploit` validator lands).
2. Read the per-sample failure_class / feedback / build_report.
3. Adjust the route's `routes/<route>.j2` (and shared entry if systemic).
4. Re-run (fresh run-id — scorer/prompt change). Stop when the 3-set is stable.

Env-gen is observable today via the existing `cage-check` validator. Exp-gen
observation is gated on building the exp validator (fusion EXP-gate).
