# 厂商脚本关键行为（0.2.19 实测）

## install.ps1（引导层，/client/install.ps1）
- 校验 `-AllowHttp`（内网 HTTP 必须显式带，否则抛「服务和更新地址必须是 HTTPS」）
- 只接受更新源文件名是 `latest.json`
- 校验 manifest：`product == 'v8-development-workbench'`、semver、`sha256` 64 位 hex
- 校验 `download_path` 与清单**同源**（scheme/host/port 都要一致）
- 用 `tar -tzf` / `tar -tvzf` 做路径穿越与符号链接检查 → **这里踩 MSYS tar 坑**
- 解包后要求 `release.json` 版本与 manifest 一致
- 调 `release/infra/scripts/install-v8-workbench.ps1`

## install-v8-workbench.ps1 / .sh（正式安装器）
参数：`--url` `--name` `--client opencode|codex` `--config` `--update-source` `--check` `--allow-http` `--allow-http-localhost`

写入：
| 目标 | opencode | codex |
|---|---|---|
| MCP 配置 | `~/.config/opencode/opencode.json` 的 `mcp.v8-workbench`（`{type: remote, url, enabled}`） | `~/.codex/config.toml` 的 `[mcp_servers.v8-workbench]` |
| Skills | `~/.config/opencode/skills/v8-*` | `~/.codex/skills/v8-*` |
| 身份（共用） | `~/.v8-workbench/identity.json` | 同左 |
| 更新脚本 | `~/.v8-workbench/bin/update-v8-workbench.*`、`archive-v8-knowledge.*` | 同左 |
| 安装元数据 | `~/.v8-workbench/installation.json` | 同左 |

其他行为：
- 写配置前会 `cp config config.bak`
- URL 会被剥离旧的 `v8_user_id`/`v8_display_name` 再重新追加（幂等）
- opencode 分支的 JSONC 解析会去掉注释和尾逗号（保留 `$schema`）
- codex 分支用 `# V8_WORKBENCH_BEGIN/END` 标记包裹，重装先删旧块
- `--check` 会校验 identity 格式、MCP 配置存在，并 GET `<url>/health/live`
- `update-v8-workbench.ps1` 内部的 latest.json → 脚本映射表是**写死的**，加客户端需要新的客户端包

## sh 安装器对 python3 的硬依赖
`--check` 的身份校验、URL 归一化、JSONC 解析、toml URL 转义全部走 `python3 - <<'PY'` heredoc。本机没有 python3 时装不上，必须垫片（见 SKILL.md）。垫片要处理 MSYS→原生路径转换，否则原生 python 打不开 `/c/Users/...`。

## MCP 服务端信息（实测）
- serverInfo: `v8-workbench` 1.29.0，protocol 2024-11-05
- 16 个工具；写入型 3 个：`create_incident_card`、`record_workbench_event`、`save_quality_report`（均要求脱敏，身份由连接自动绑定）
- 读型：`get_platform_context`、`search_v8_knowledge`、`get_development_context`、`get_quality_rules`、`diagnose_online_issue`、`search_v8_code`、`search_v8_public_apis`、`read_v8_code`、`find_v8_symbol`、`get_v8_type_source`、`resolve_v8_api`、`get_v8_usage_examples`、`get_v8_code_context`
- 返回的 `excerpt` 带 citation_id / path / version / module，符合「必须带引用、无命中要说知识不足」的服务端约束
