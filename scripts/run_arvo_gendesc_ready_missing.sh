#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-/home/yihe/workspace/CAGE-private}"
ARVO_ENV="${ARVO_ENV:-/home/yihe/workspace/arvo_env}"
SOURCE_IDS="${SOURCE_IDS:-$ARVO_ENV/metadata/datasets/arvo/non_cybergym_issue_first_ready_missing_description_ids.txt}"
PREFLIGHT_ROOT="${PREFLIGHT_ROOT:-$ARVO_ENV/metadata/datasets/arvo/preflight_scan}"
PREFLIGHT_SCAN_DIR="${PREFLIGHT_SCAN_DIR:-}"
PREFLIGHT_ALLOWLIST="${PREFLIGHT_ALLOWLIST:-}"
PROJECT="${PROJECT:-$REPO/examples/cybergym/local_gendesc_arvo_ready_missing.yml}"
INDEX="${INDEX:-$REPO/examples/cybergym/datasets/arvo_local_restored.json}"
TASK_IDS="${TASK_IDS:-$REPO/examples/cybergym/datasets/arvo_ready_missing_description_preflight_clean.txt}"
RUN_ID="${RUN_ID:-arvo-gendesc-ready-missing-20260717}"
MAX_CONCURRENT="${MAX_CONCURRENT:-32}"
MAX_ROUNDS="${MAX_ROUNDS:-60}"
TIMEOUT="${TIMEOUT:-0}"
SECRET_FILE="${SECRET_FILE:-$HOME/.config/cage/secrets/deepseek-v4-pro.env}"

[ -f "$SOURCE_IDS" ] || { echo "ERROR: missing source task list: $SOURCE_IDS" >&2; exit 1; }
[ -d "$PREFLIGHT_ROOT" ] || { echo "ERROR: missing preflight scan root: $PREFLIGHT_ROOT" >&2; exit 1; }
[ -f "$PROJECT" ] || { echo "ERROR: missing project config: $PROJECT" >&2; exit 1; }
[ -f "$SECRET_FILE" ] || { echo "ERROR: missing secret file: $SECRET_FILE" >&2; exit 1; }
[ -d "$ARVO_ENV/payloads-arvo/arvo" ] || { echo "ERROR: missing payload data" >&2; exit 1; }
[ -d "$ARVO_ENV/server-binary-arvo/arvo" ] || { echo "ERROR: missing binary data" >&2; exit 1; }

if [ -z "$PREFLIGHT_ALLOWLIST" ]; then
  if [ -n "$PREFLIGHT_SCAN_DIR" ]; then
    PREFLIGHT_ALLOWLIST="$PREFLIGHT_SCAN_DIR/ok_clean_task_ids.txt"
  else
    PREFLIGHT_ALLOWLIST="$(python - "$PREFLIGHT_ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
candidates = []
for child in root.iterdir():
    if not child.is_dir():
        continue
    allowlist = child / "ok_clean_task_ids.txt"
    if not allowlist.is_file():
        continue
    generated_at = ""
    summary_path = child / "summary.json"
    if summary_path.is_file():
        try:
            generated_at = str(json.loads(summary_path.read_text(encoding="utf-8")).get("generated_at") or "")
        except Exception:
            generated_at = ""
    candidates.append((generated_at, child.name, str(allowlist)))
if not candidates:
    raise SystemExit(f"ERROR: no ok_clean_task_ids.txt found under {root}")
print(max(candidates)[2])
PY
)"
  fi
fi
[ -f "$PREFLIGHT_ALLOWLIST" ] || { echo "ERROR: missing preflight clean allowlist: $PREFLIGHT_ALLOWLIST" >&2; exit 1; }
echo "Using preflight clean allowlist: $PREFLIGHT_ALLOWLIST"

set -a
# shellcheck disable=SC1090
source "$SECRET_FILE"
set +a
: "${DEEPSEEK_API_KEY:?DEEPSEEK_API_KEY is missing from secret file}"

cd "$REPO"
ln -sfn "$ARVO_ENV/payloads-arvo" examples/cybergym/datasets/payloads-arvo
ln -sfn "$ARVO_ENV/server-binary-arvo" examples/cybergym/datasets/server-binary-arvo
python - "$SOURCE_IDS" "$PREFLIGHT_ALLOWLIST" "$TASK_IDS" <<'PY'
import sys
from pathlib import Path

src = Path(sys.argv[1])
allow = Path(sys.argv[2])
dst = Path(sys.argv[3])

def normalize(raw):
    value = raw.strip()
    if not value or value.startswith("#"):
        return None
    return value if ":" in value else f"arvo:{value}"

allowlist = set()
for line in allow.read_text(encoding="utf-8").splitlines():
    task_id = normalize(line)
    if task_id is not None:
        allowlist.add(task_id)
if not allowlist:
    raise SystemExit(f"ERROR: preflight clean allowlist is empty: {allow}")

task_ids = []
skipped = []
seen = set()
for line in src.read_text(encoding="utf-8").splitlines():
    task_id = normalize(line)
    if task_id is None or task_id in seen:
        continue
    seen.add(task_id)
    if task_id in allowlist:
        task_ids.append(task_id)
    else:
        skipped.append(task_id)

if not task_ids:
    raise SystemExit(
        f"ERROR: no source tasks survived preflight-clean filtering; "
        f"source={src} allowlist={allow}"
    )

dst.write_text("".join(f"{task_id}\n" for task_id in task_ids), encoding="utf-8")
print(
    f"Wrote {len(task_ids)} preflight-clean task ids to {dst} "
    f"(source={len(seen)} allowlist={len(allowlist)} skipped={len(skipped)})"
)
if skipped:
    print(f"Skipped {len(skipped)} source tasks absent from clean allowlist; first={skipped[:10]}")
PY

python examples/cybergym/scripts/build_cybergym_index.py from-data-dir \
  --data-dir "$ARVO_ENV/payloads-arvo" \
  --out "$INDEX"

python - "$INDEX" "$TASK_IDS" <<'PY'
import json
import sys
from pathlib import Path

index = json.loads(Path(sys.argv[1]).read_text())
wanted = {
    (line.strip() if ":" in line.strip() else f"arvo:{line.strip()}")
    for line in Path(sys.argv[2]).read_text().splitlines()
    if line.strip() and not line.strip().startswith("#")
}
missing = sorted(wanted - set(index))
if missing:
    raise SystemExit(
        f"ERROR: {len(missing)} preflight-clean ready-missing cases absent from generated index; first={missing[:10]}"
    )
print(f"Validated {len(wanted)} preflight-clean ready-missing cases in the generated index")
PY

cage model set deepseek-v4-pro \
  --provider anthropic \
  --model deepseek-v4-pro \
  --endpoint https://api.deepseek.com/anthropic \
  --api-key "${DEEPSEEK_API_KEY}"

cage benchmark check "$PROJECT" \
  --agent claude_code \
  --model deepseek-v4-pro \
  --sample "@${TASK_IDS}" \
  --set "eval.benchmark.task_ids=${TASK_IDS}" \
  --strict-exit

RUN_DIR="$REPO/examples/cybergym/.cage_runs/claude_code:deepseek-v4-pro:stateless/$RUN_ID"
RESUME_FLAG=""
if [ -d "$RUN_DIR" ]; then
  RESUME_FLAG="--resume"
  echo "Resuming existing run: $RUN_DIR"
else
  echo "Starting new run: $RUN_DIR"
fi

exec sg docker -c "cd '$REPO' && cage run '$PROJECT' \
  --agent claude_code \
  --model deepseek-v4-pro \
  --sample '@$TASK_IDS' \
  --set 'eval.benchmark.task_ids=$TASK_IDS' \
  --passk 1 \
  --max-concurrent '$MAX_CONCURRENT' \
  --max-rounds '$MAX_ROUNDS' \
  --timeout '$TIMEOUT' \
  --run-id '$RUN_ID' \
  $RESUME_FLAG"
