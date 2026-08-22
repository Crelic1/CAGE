# Training Corpus — `cage corpus`

Every trial records each model call in `proxy/proxy.jsonl`. `cage corpus`
turns finished runs into training rows: one row per complete conversation, in
ms-swift `messages + loss` shape, each traceable back to the trial it came from.

```bash
cage corpus runs                                # what is available
cage corpus gates --run <run-id>                # what this benchmark refuses, and why
cage corpus export --run <run-id> --dry-run     # what those filters would yield
cage corpus export --run <run-id> --out sft.jsonl
cage corpus show <run-id>/<trial-id>            # read one trial's rows
```

The inspector offers the same thing as a button, on a run page and on a trial
page. It does not stream the export into the response: the work runs behind the
request, so a browser that disconnects costs nothing and a repeat click joins
the export already running instead of starting a second scan of the same
gigabytes. The page polls for progress, and the finished corpus is served as an
ordinary file — with a length, and with ranges honoured, so an interrupted
download resumes. Results are cached under `.cage_corpus/` (override with
`CAGE_CORPUS_CACHE`) and keyed by a fingerprint of the run's contents, so a run
that has grown or been re-scored is exported again rather than served stale.

## What a row is

One **complete conversation**, not a per-turn sample. The prefix is lifted
verbatim from a real request: every recorded request carries its full message
history, so the last request of a conversation already contains every earlier
turn exactly as the model received it. Appending that request's own response
gives the whole conversation with nothing reassembled.

Per-turn expansion is not offered because it costs enormously and supervises
nothing extra: n turns become n rows of O(n) prefix each, so the file grows
roughly 20× while the supervised token count is unchanged.

```json
{
  "messages": [
    {"role": "system",    "content": "...",                    "loss": 0},
    {"role": "user",      "content": "...",                    "loss": 0},
    {"role": "assistant", "content": "<think>…</think>\n\n…",  "loss": 1},
    {"role": "tool",      "content": "...",                    "loss": 0}
  ],
  "tools": [ ... ],
  "id": "<run-id>/<trial-id>#<segment>",
  "task": "...", "src_model": "...", "_view": "expert_trajectory",
  "_meta": { "run_id": "...", "trial_id": "...", "segment": 1, "n_segments": 2, ... }
}
```

`_meta.run_id` + `_meta.trial_id` locate the source directory exactly:
`.cage_runs/<agent>:<model>:<lifecycle>/<run-id>/trials/<trial-id>/`.
`_meta.served_model` is the name the endpoint actually reported — a model slot is
a label for an endpoint and can be repointed between runs, so reproducing a
result later needs the name the endpoint gave, not the label we used.

## Compaction: why one trial can produce several rows

When the context fills, the harness asks the model to summarise and then
**replaces** the history with that summary. No single context the model ever saw
spans both sides of that boundary, so a conversation joining them would be
fabricated. Each side is complete on its own: N compactions give N+1 rows,
numbered by `_meta.segment`.

**How the boundary is found matters.** The default reconstructs the delegation
tree (`--splitter forest`) rather than watching the message count drop. A
harness makes one-shot auxiliary calls that carry the *main* agent's system
prompt and three messages; a count-based heuristic reads each of those as a
fresh compaction. On one real trial that turned a single compaction into twelve
near-duplicate segments of the same conversation — 58, 59, 60 … 69 turns —
instead of two. `--splitter system_prompt` reproduces the old behaviour and
exists only for reproducing an existing corpus byte-for-byte.

Two consequences worth knowing when you consume the corpus:

- **The summary is in the corpus, on the input side.** It opens the next
  segment as a `loss=0` user message, which is where the model really saw it.
  What is not there is a row that supervises *writing* a summary — that turn is
  the harness's bookkeeping, not the agent's work. `--no-drop-compaction-call`
  is available if you want to train summarisation.
- **A segment after a compaction does not restate the task.** The original
  instruction is gone; the summary stands in for it. Those rows carry
  `opens_with_summary: true` and `real_task_present: false`, so a consumer that
  wants only task-opened conversations can filter on them (or use
  `--first-segment-only`).

## Contamination is refused; preference is filtered

The exporter refuses **only** what would be wrong to learn from at all, and that
judgement belongs to the benchmark, not the framework. A benchmark answers
`Benchmark.admit_for_training` with **gate codes** — short opaque identifiers it
chooses. The framework matches them against `--allow` and prints them in
reports; it never interprets one, so a benchmark adds a rule without the
framework learning its name.

```bash
cage corpus gates --run <run-id>       # ask the benchmark what it defines
cage corpus export --run <run-id> --allow answer_lookup --out sft.jsonl
```

Everything else is a **selection preference** and is off by default: solved and
unsolved trials both come out, no per-task cap, no reasoning threshold. Those
are decisions for whoever assembles the training mix. An export that silently
returns less than was asked for is the one failure this design will not
tolerate, so every drop — gate, filter or build defect — is counted and printed,
and `--report` writes the tally as JSON.

## Filters

Framework-level, because the framework knows what these are:

| Flag | Selects |
|---|---|
| `--run`, `--run-glob`, `--benchmark` | which runs |
| `--agent`, `--model`, `--served-model` | which agent / endpoint |
| `--task`, `--task-file` | which samples |
| `--passed` / `--failed` | solved or unsolved (default: both) |
| `--compacted` / `--no-compacted` | rows from compacted trials |
| `--first-segment-only`, `--segment N` | which segment |
| `--min-turns`, `--max-turns` | conversation length |
| `--think-ratio-min` | fraction of supervised turns carrying reasoning |
| `--per-task-cap`, `--limit`, `--sample --seed` | how many |
| `--split-by run\|model` | one file per run or model |

Benchmark-level, through two generic knobs — the framework carries no flag named
after any domain's rule:

| Flag | Selects |
|---|---|
| `--allow CODE` | release one of the benchmark's admission gates |
| `--where KEY=VALUE` | match a benchmark provenance field |

A benchmark that grades on a scale rather than passing or failing (its scorers
leave `answer` empty and put the signal in `value`) reports `passed: null`, not
`passed: false` — reporting a graded run as uniformly failed would be a claim
its scorer never made. `_meta.score` carries the number in that case.

Trials superseded by a resume (`<trial>.before_resume_*`) are skipped: they
describe the same task as the live trial beside them, so exporting both ships
near-duplicate trajectories and inflates the task count.

Cheap filters are applied before anything is parsed. Most questions (agent,
model, task, pass/fail) are answerable from small per-trial files, while segment
shape and reasoning ratio need the proxy log, which routinely exceeds 100 MB.
That ordering is what makes `--dry-run` over a large run practical.

## Faithful to what the model received

A row reproduces the input the model was actually given at inference time —
not what the agent sent, and not a tidied-up version of either. The two are not
the same thing, because the proxy sits between them: it may strip a header,
inject a hint, or apply a system-prompt template on the way upstream. The
recorded upstream body is the ground truth, and that is what the exporter reads.

This is the whole point. A row whose prefix differs from the real inference-time
input teaches the model a context it will never see again, and the difference
does not have to be large to matter — a separator, a header line, a dropped
reasoning block. `scripts/corpus_fidelity.py` checks exported rows against the
recorded upstream body turn by turn.

Concretely, nothing is edited on the way out:

| Content | Why it stays | Flag to remove |
|---|---|---|
| `You are powered by the model <teacher>.` | the model received it | — |
| `x-anthropic-billing-header: …` | the model received it, on whichever path the run took — the proxy drops it only when translating to OpenAI, and only in sidecar builds that have that fix | `--strip-billing-header` |
| A director hint Cage injected | the model received it; rows carrying one are counted in the report so it is never a surprise | `--strip-director` |
| Claude Code's `<system-reminder>` blocks | the model received them | `--no-strict` |
| A bare `</think>` with no opening tag | that is what the model emitted | `--repair-think-tags` |

One thing is deliberately not a verbatim copy of the wire, and it is required
for consistency rather than in tension with it: **assistant turns are rendered
as the student emits them.** Upstream carries structured `reasoning_content` and
`tool_calls`; the row carries `<think>…</think>` and the Qwen/Hermes
`<tool_call><function=…>` form. That is the form a model served through Cage
produces and Cage parses back (`_XML_FUNCTION_RE` in `cage/proxy/sidecar.py`),
so training on it is what makes generation and parsing agree.

### Where the prompt comes from

From the body the proxy sent **upstream**, not the request the agent made. The
two differ, and not predictably: some sidecar builds strip Claude Code's billing
header on the way out, so the agent's body carries a line the model never saw —
an 86-character difference in the system prompt, present in some runs and absent
in others depending on the image the run used. Reading the upstream body is
right for all of them without having to know which transforms that build
applied. A user turn's text blocks arrive already joined with a single newline
for the same reason; the pipeline this replaces joined them with two, a
separator the model never saw.

`_meta.source_call_index` records which recorded call a row came from, so a row
can be checked against the exact body that produced it.

## Path redaction

Host paths are redacted; **the container path is not**. `/home/agent/workspace`
exists inside the container, is what the system prompt declares, and is what the
evaluation environment presents again at inference time. Rewriting it yields a
sample that contradicts itself — the system prompt names one directory and the
commands use another — and a model trained on that learns to ignore the system
prompt and address a directory that does not exist.

The exporter enforces this rather than trusting it — by checking the **rule**,
not the output. Before writing a segment it asks the redactor what it would do
to the working directory the system prompt declares; if the answer is anything
but "leave it alone", the export refuses and says which pattern is too broad.

Scanning turns for the placeholder instead does not work, and the attempt is
instructive: a target application with its own `/workspace/models/...`
directory, and a Java source file quoting `D:/workspace/img`, both trip it with
nothing whatsoever having been rewritten. Substring evidence cannot tell "the
redactor rewrote a real path" from "the text legitimately says /workspace".

Which prefixes count as private is a property of the installation, so the
patterns are configuration (`Redactor.host_path_patterns`), not code.

## Adding a benchmark's gates

```python
class MyBenchmark(Benchmark):
    def admit_for_training(self, trial):
        verdict = TrainingAdmission.ok(passed=self.trial_passed(trial))
        if ...:
            verdict = verdict.rejected("answer_in_workspace", "the agent held the answer")
        return verdict.with_provenance(difficulty=...)
```

`trial` is a `TrialCorpusView`: a read-only handle exposing scores, meta, run
config, workspace and `scan_tool_commands(pattern)` — so a gate never joins
storage paths itself and keeps working when the layout changes. Gates that must
read the whole trajectory should run last, and only when nothing cheaper has
already refused.
