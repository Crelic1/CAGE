# `scripts/` — 仓库级工具

这里只放**换一台机器、换一个月还会再跑一次**的可执行工具。

一次实验的运维脚本不属于这里。判据很具体：脚本里如果写死了某台主机的 IP、
某个仓库的绝对路径、或者某几个 run-id，它就是那次实验的产物，
应该放 `artifacts/ops/`（已 gitignore），而不是入库。
任务清单、报告、台账同理，放 `artifacts/` 下对应位置。

| | `scripts/` | `artifacts/` |
|---|---|---|
| 性质 | 代码 | 数据与一次性运维 |
| 版本控制 | 入库 | gitignore |
| 例子 | `agent_firewall.py` | `ops/watch_runs.sh`、`task_lists/tier1_head2500.txt`、`RUN_CONTRACT.md` |

**例外**：`agent_firewall_allowlist*.txt` 虽是配置，但脚本用
`Path(__file__).with_name(...)` 就近查找，搬走会直接弄坏它，所以留在旁边。
`.local.txt` 后缀是本机私有覆盖，已 gitignore。

---

## 采集与安全

| 脚本 | 作用 |
|---|---|
| `agent_firewall.py` | 起一个 squid 白名单网络，让 agent 容器只能出网到允许的域名。`examples/cybergym/default_arvo.yml` 已接好，每台机起一次即可 |
| `reap_grading_scratch.sh [大小] [静默分] [轮询秒]` | 收割判分暂存区里超大、且已判完的 PoC。给「已经在跑、吃不到 `examples/cybergym/benchmark.py` 里 PoC 上限」的 run 兜底 |

## 凭证守护

保持宿主上的 OAuth 凭证不过期，供容器里的 agent 取用。

| 脚本 | 作用 |
|---|---|
| `refresh_claude_oauth.py` | 刷新 Claude Code 的 `.credentials.json`（单次） |
| `refresh_claude_oauth_loop.sh` | 上面那个的常驻守护版 |
| `refresh_codex_oauth.py` | Codex CLI 的 ChatGPT-OAuth 版本 |

## 开发与数据

| 脚本 | 作用 |
|---|---|
| `gen_openapi.py` | 不起服务就把 serve API 的 OpenAPI schema 写到 `docs/openapi.json` |
| `export_trajectory_events.py` | 从 `proxy/proxy.jsonl` 导出精简的轨迹事件 |
| `build_claude_code_trace_cyber_dataset.py` | 把多个 run 压成紧凑的 trace 数据集（源日志里每条请求都重复整段上下文，直接用会爆） |

RL 集成的冒烟设施在 `tests/rl_smoke.py` 和 `tests/rl_mock_gateway.py`——
它们走真实 cage 代码路径，属于测试而不是工具。
