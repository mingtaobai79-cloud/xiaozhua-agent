---
name: v8-workbench-update
description: 按用户明确要求检查或更新本机 V8 Skill 与更新脚本。适用于“更新工作台、更新 Skill、检查版本、升级客户端”；不要用于普通 V8 开发、知识检索、写代码或首次安装。
---

# V8 工作台更新

只在用户明确说“更新工作台”“更新 V8 Skill”“检查工作台版本”“升级客户端”时使用。普通开发问题不得自动更新，也不得因为检索失败自行改本机配置。

用户说“更新/升级”即已授权执行更新，不要再二次确认。若只说“检查/看看有没有新版本”，则只跑检查，不安装。

## 现网边界

> 仓库版把工作台地址写成 `<V8_WORKBENCH_HOST>`；真实地址（公司内网 HTTP，办公网/VPN 通用）只在 Hermes 侧同名 skill 里。

- 长期地址是公司内网 HTTP：`http://<V8_WORKBENCH_HOST>`。办公网和 VPN 都用它，不要改成 HTTPS，也不要改成本机 `127.0.0.1`。
- 员工侧只更新 `~/.config/opencode/skills/v8-*` 和 `~/.v8-workbench/bin` 里的更新脚本；保留已有 `v8-workbench` MCP 和其他 MCP。历史 Codex 安装才更新 `~/.codex/skills/v8-*`。
- 服务端版本由管理员发 Docker。可先调用 `get_platform_context` 看服务端版本，再对比本机 `~/.v8-workbench/installation.json`。

## 更新源和 HTTP 许可

先读 `~/.v8-workbench/installation.json` 和 `~/.v8-workbench/update-source`。

1. 从 `mcp_url` 推导同源清单：`{origin}/client/releases/latest.json`。例如 MCP 是 `http://<V8_WORKBENCH_HOST>/mcp`，更新源就是 `http://<V8_WORKBENCH_HOST>/client/releases/latest.json`。
2. 若本机 `update-source` 缺失、指向 `127.0.0.1`/`localhost`，或不是上述内网清单，改用第 1 步推导的地址，并用 `--source`/`-Source` 显式传入。
3. 内网 HTTP 必须带 `--allow-http` / `-AllowHttp`。本机 `127.0.0.1` 验证才用 `--allow-http-localhost` / `-AllowHttpLocalhost`。旧客户端不会自动继承许可，对话更新时始终带上对应开关。
4. 未完成安装时，引导去 `http://<V8_WORKBENCH_HOST>/public/install`，不要猜测下载地址，也不要重装 MCP。

## 操作

Windows（PowerShell）：

```powershell
& "$HOME\.v8-workbench\bin\update-v8-workbench.ps1" -Check -AllowHttp -Source http://<V8_WORKBENCH_HOST>/client/releases/latest.json
& "$HOME\.v8-workbench\bin\update-v8-workbench.ps1" -AllowHttp -Source http://<V8_WORKBENCH_HOST>/client/releases/latest.json
```

Mac / Linux：

```bash
~/.v8-workbench/bin/update-v8-workbench.sh --check --allow-http --source http://<V8_WORKBENCH_HOST>/client/releases/latest.json
~/.v8-workbench/bin/update-v8-workbench.sh --allow-http --source http://<V8_WORKBENCH_HOST>/client/releases/latest.json
```

先跑检查命令，汇报当前版本和新版本；用户要求更新时再跑第二条。更新后提醒重启 openCode。

## 安全约束

- 不删除其他 MCP，不改 `opencode.json` / `config.toml` 里非 `v8-workbench` 的条目，不上传身份文件或口令。
- 发布包必须含 `skills/`；脚本会校验 SHA-256 并拒绝路径穿越。失败时保留备份，不声称成功。
- 汇报旧版本、新版本、更新了几个 V8 Skill、备份目录，以及 MCP 配置是否保持不变。
