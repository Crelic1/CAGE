# ARVO local data workspace

This directory stores local ARVO metadata and derived gendesc views. The actual
binary environments are outside this tree at
`/path/to/cybergym-bin/arvo-external-server-data/arvo/<id>/`.

## Layout

| Path | Role | Canonical? |
|---|---|---|
| `catalog/environments.jsonl` | one verified binary-ready environment per row | yes |
| `catalog/features_external_built.json`, `classification_external.tsv` | regenerated classification views | no |
| `scripts/` | catalog, selection, snapshot, and delivery-export tools | yes |
| `selections/<dated-batch>/` | historical candidate selections | historical |
| `reports/` | dated classification and gap reports | historical/derived |
| `snapshots/<capture-id>/` | immutable materialized views of catalog + gendesc results | yes, per capture |

The generated directories (`catalog`, `selections`, `reports`, `snapshots`) are
local and ignored by Git. Scripts and the two root documents are source.

## Current snapshot

`snapshots/20260728-gendesc-ready3074-c16/` records the pre-retry state of the
ready-3,074 gendesc run. Read its `SUMMARY.md` and `manifest.json` first.

For a new capture after a run finishes:

```bash
python examples/cybergym/external_arvo/scripts/build_local_snapshot.py \
  --run-dir examples/cybergym/.cage_runs/claude_code:glm-5.2-sii:stateless/gendesc-glm52-ready3074-c16-20260723 \
  --out-dir examples/cybergym/external_arvo/snapshots/<capture-id>
```

See `PACKAGING.md` for making a shareable subset from trial outputs.
