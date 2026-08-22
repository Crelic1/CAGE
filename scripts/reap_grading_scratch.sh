#!/bin/bash
# 判分暂存区收割：把已判分完毕的超大 PoC 从本地盘上摘掉。
#
# 为什么需要它：
#   判分服务把 agent 提交的每个 PoC 落到 /tmp/cage-cybergym-grade-*/<agent>/poc-NNN，
#   trial 结束才整目录回收。个别 agent 会做「尺寸倍增试探」——
#   134MB → 512MB → 805MB → 1.6GB —— 一条 trial 就能吃掉几个 G。
#   40G 的根分区扛不住，打满会让整批 trial 变成 container_error。
#
#   根治手段是判分服务侧的 10MB 上限（benchmark.py DEFAULT_MAX_POC_MB），
#   但那个上限只在 run 启动时实例化，对已经在跑的 run 不生效。
#   这个脚本就是给「已经在跑的 run」用的兜底。
#
# 为什么删了是安全的：
#   判分是同步的——文件落盘 → 跑靶标 → 返回结论。结论（vul_exit_code）
#   记在判分服务的内存记录里，不再回读文件。回读只发生在 trial 收尾时
#   把 PoC 拷进产物目录，那一步 `src.is_file()` 为假就跳过。
#   所以代价仅仅是这条 trial 少了离线复判的原始 PoC——
#   而几百 MB 的 PoC 本来也不该拷到 NFS 上去。
#
#   靠 mtime 保证不碰在判的文件：只收割 QUIET_MIN 分钟内没动过的。
#
# 用法:  reap_grading_scratch.sh [大小阈值 默认10M] [静默分钟 默认3] [轮询秒 默认120]
set -u
SIZE=${1:-10M}
QUIET=${2:-3}
INTERVAL=${3:-120}
LOG=${REAP_LOG:-$HOME/reap_grading.log}

echo "=== reap_grading_scratch 启动 $(date '+%F %T')  >$SIZE 且 ${QUIET}min 未动  每 ${INTERVAL}s ===" | tee -a "$LOG"

while :; do
  total=0; n=0
  for root in /tmp/cage-cybergym-grade-*; do
    [ -d "$root" ] || continue
    while IFS=$'\t' read -r sz path; do
      [ -n "${path:-}" ] || continue
      rm -f -- "$path" && { total=$((total + sz)); n=$((n + 1)); }
    done < <(find "$root" -type f -size +"$SIZE" -mmin +"$QUIET" -printf '%s\t%p\n' 2>/dev/null)
  done
  if [ "$n" -gt 0 ]; then
    avail=$(df -h / | awk 'NR==2{print $4}')
    printf '%s  收割 %d 个文件 %.2fG  根分区剩余 %s\n' \
      "$(date '+%F %T')" "$n" "$(echo "$total" | awk '{print $1/1073741824}')" "$avail" | tee -a "$LOG"
  fi
  sleep "$INTERVAL"
done
