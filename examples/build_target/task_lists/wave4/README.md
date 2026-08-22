# wave4 build-target queue

This queue is generated from the 1,456-record Pwn/Web static-material index.
It excludes environments that already have R3 build plus CAGE launch/address/close
evidence. Only confirmed D3-D5 records enter the runnable queue. D0 and D1 are
policy-dropped, candidate-only upgrades are not treated as confirmed, and D2 is
kept outside the runnable queue.

| Bucket | Count |
|---|---:|
| Build tasks | 377 |
| Pwn build tasks | 171 |
| Web build tasks | 206 |
| Build tasks with a known prior runtime blocker | 5 |
| Deferred D2 | 1 |
| Already generated | 210 |
| Candidate D3-D5 but confirmed D0/D1 | 431 |
| Dropped D0/D1 | 437 |

Pwn ordering:

| Material priority | Count |
|---|---:|
| dockerfile_writeup_attachments | 69 |
| dockerfile_attachments | 99 |
| incomplete | 3 |

Files:

- build_tasks.jsonl: runnable D3-D5 queue in deterministic order.
- build_tasks.tsv: compact reader-facing task list.
- build_task_ids.txt: one ordered environment ID per line.
- deferred_d2.jsonl: retained for audit, not part of the default run.
- candidate_only.jsonl: apparent D3-D5 material shapes that remain confirmed D0/D1.
- completed.jsonl: prior R3 successes removed from the queue.
- excluded.jsonl: completed plus D0/D1 policy exclusions.
- summary.json: counts, policy, source hashes, and queue ID hashes.

Each build record contains a task object that can be materialized as task.json
for the CAGE build_target benchmark. Image tags are explicit and never use latest.
