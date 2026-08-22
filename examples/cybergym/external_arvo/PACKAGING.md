# Packaging gendesc results for sharing

The run directory is evidence, not the delivery dataset. First materialize a
snapshot; then export a self-contained bundle from that snapshot.

## 1. Capture the run

Run this only after the target gendesc run is terminal, so the snapshot has one
stable `latest` result per task.

```bash
python examples/cybergym/external_arvo/scripts/build_local_snapshot.py \
  --run-dir examples/cybergym/.cage_runs/claude_code:glm-5.2-sii:stateless/gendesc-glm52-ready3074-c16-20260723 \
  --out-dir examples/cybergym/external_arvo/snapshots/20260729-gendesc-final
```

Inspect `manifest.json`. The fields `latest_with_descriptions` and
`latest_with_understanding` are the first delivery-quality counters.

## 2. Export a recipient bundle

Metadata plus descriptions/understanding, for all tasks:

```bash
python examples/cybergym/external_arvo/scripts/export_delivery_bundle.py \
  --snapshot-dir examples/cybergym/external_arvo/snapshots/20260729-gendesc-final \
  --out-dir /tmp/arvo-gendesc-20260729
```

For a few tasks to inspect manually, repeat `--task-id`:

```bash
python examples/cybergym/external_arvo/scripts/export_delivery_bundle.py \
  --snapshot-dir examples/cybergym/external_arvo/snapshots/20260729-gendesc-final \
  --out-dir /tmp/arvo-review \
  --task-id arvo:344 --task-id arvo:14717
```

Add `--include-binaries` only when the recipient needs to execute the PoC. It
copies each selected `vul/`, `fix/`, and `poc`, so it can be large.

## Bundle contract

```text
bundle/
├── manifest.json          # counts, source snapshot, selected ids
├── dataset.jsonl          # one portable environment + latest gendesc row
├── evidence/arvo_<id>/
│   ├── descriptions.json
│   └── understanding.md   # only when produced
└── environments/arvo_<id>/  # only with --include-binaries
    ├── vul/
    ├── fix/
    └── poc
```

`dataset.jsonl` keeps provenance and descriptions but replaces host-specific
artifact paths with paths relative to the bundle. The original run remains the
audit trail; the bundle is the artifact sent to others.
