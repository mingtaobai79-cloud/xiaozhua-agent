---
name: v8-workbench-client-setup
description: Use when installing the V8 workbench MCP client.
version: 1.0.0
author: 小爪
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [MCP, Windows, 2小爪, v8]
---

# V8 开发工作台客户端安装（Windows）

## When to Use

当需要在这台 Windows 机器上安装/修复 V8 开发工作台（v8-workbench）MCP 客户端，或配置手册里的安装命令、排查安装报错时。

安装手册：http://<V8_WORKBENCH_HOST>/public/install （内网/VPN，免登录）。
MCP 地址：http://<V8_WORKBENCH_HOST>/mcp ，在线清单 http://<V8_WORKBENCH_HOST>/client/releases/latest.json 。

## 先判断该装哪个客户端（硬门禁）

**用户只说「帮我装这个」+ URL + 姓名时，不要自行选择客户端。** 装 openCode 意味着全局 npm 写入 + 新建配置目录 + 装一个用户没要的工具；这是系统级外部动作，先确认。

正确顺序：
1. 先探测本机已有哪些客户端：

```bash
for c in opencode codex claude cursor ccs pi hermes dsh; do printf "%-10s " "$c"; command -v $c 2>/dev/null || echo '-'; done
```

2. 本机已有 Codex / Hermes / Cursor 时，**直接接已有的**（手册「其他工具通用接入」只需两样：MCP 地址 + Skill 包），并告知用户「你已有 X，直接接上，不必装 openCode」。
3. 本机确实一个都没有时，才告知需要安装 openCode（说明它是什么、写哪些路径），等用户确认再装。

反例：手册默认写的是 openCode，照着装完才被用户问「一定需要 openCode 吗」。手册的默认客户端不等于本机的最优选择 —— 手册面向「全新机器」，本机得先看现状。

## 关键路径

- MCP 地址生成：页面 `data-mcp-generator` 用 `crypto.randomUUID()` 存 localStorage，拼成 `?v8_user_id=<uuid>&v8_display_name=<姓名>`。**UUID 一旦生成就复用它**（存 `~/.v8-workbench/identity.json`），换名不换号。
- 身份文件：`~/.v8-workbench/identity.json` → `{user_id, display_name}`
- Skill 包：`/client/v8-workbench-skills.zip` 或发布包内 `skills/v8-*`
- 各部分接入路径见手册「安装后写到哪里」段。

## 坑 1：厂商 Windows PS 安装器在 PowerShell 5.1 下必崩

`install-v8-workbench.ps1` 第 6 行 `$Value.IndexOfAny([char[]]@('"', '\\', "`r", "`n"))` 里的 `'\\'` 在 PowerShell 5.1 被解析成**两个字符**的字符串，转 `char[]` 时抛：
`无法将值“\\”转换为类型“System.Char”` / `InvalidCastParseTargetInvocation`。

PowerShell 7 里 `'\\'` 是两字符转义、只算一个反斜杠，才正常。**本机只有 5.1 时这条路径走不通，不要试图修厂商脚本。** 改用厂商的 sh 安装器（见下）。

排查同一文件里这类字面量的 shell 引号陷阱：`grep -n 'char\[\]' <file>` 然后 `sed -n 'Np' file | od -c` 看真实字节。

## 坑 2：安装器调 tar 时 MSYS 的 GNU tar 会劫持

Hermes 的 terminal 走 git-bash，`PATH` 首位是 MSYS，`/usr/bin/tar` 是 GNU tar。厂商脚本（PS 与 sh 都是）用 `tar -tzf/-xzf` 处理原生路径时：

```
tar (child): Cannot connect to C: resolve failed
```

GNU tar 把 `C:\...` 的 `C:` 当成远程主机名（rsh 语法）。修法：把 Windows 自带的 bsdtar 提到 PATH 最前，**Windows 10+ 自带**：

```powershell
$env:Path = '<PATH>' + $env:Path   # System32\tar.exe 是 bsdtar 3.8.x
```

## 推荐路径：用官方 sh 安装器（最稳）

在本机需要两个垫片：
1. 本机只有 `python`，没有 `python3`；
2. 原生 Windows python 不认 MSYS 的 `/c/Users/...` 路径。

写一个 `shim/python3`（必须纯 bash，`#!/bin/bash`）：

```bash
#!/bin/bash
args=()
for a in "$@"; do
  if [[ "$a" =~ ^/([a-zA-Z])/(.*)$ ]]; then
    drive="${BASH_REMATCH[1]^^}"
    a="${drive}:/${BASH_REMATCH[2]}"
  fi
  args+=("$a")
done
exec python "${args[@]}"
```

然后：

```bash
cd <scratch>/v8
curl -s http://<V8_WORKBENCH_HOST>/client/releases/latest.json -o latest.json
# 校验 sha256 后解包
mkdir -p rel && tar -xzf client.tar.gz -C rel
chmod +x shim/python3
PATH="$(pwd)/shim:$PATH" bash rel/infra/scripts/install-v8-workbench.sh \
  --url http://<V8_WORKBENCH_HOST>/mcp \
  --name <你的名字> \
  --client <opencode|codex> \
  --update-source http://<V8_WORKBENCH_HOST>/client/releases/latest.json \
  --allow-http
```

装完自查：

```bash
PATH="$(pwd)/shim:$PATH" bash rel/infra/scripts/install-v8-workbench.sh --client <c> --url http://<V8_WORKBENCH_HOST>/mcp --check --allow-http
```

## 中文姓名传参（PS 5.1）

从 bash 传中文参数给 PS 5.1 会被当 GBK 解，且**无 BOM 的 UTF-8 .ps1 里的中文注释会吞掉换行**导致语法错（`Join-Path 无法绑定参数 Path`）。规避：
- 驱动脚本写**纯 ASCII**；
- 中文名走 sidecar JSON：`Get-Content -Raw -Encoding UTF8 name.json | ConvertFrom-Json`。

## Hermes 接入（其他工具不用装客户端）

**不要手改 config.yaml** —— agent 写 Hermes config 会被 gate 拒（security-sensitive）。用 CLI：

```bash
hermes config set mcp_servers.v8-workbench.url '<带 v8_user_id/v8_display_name 的完整 URL>'
hermes config set mcp_servers.v8-workbench.enabled true
hermes config set mcp_servers.v8-workbench.timeout 180
```

Skill：复制 `v8-*` 到 `<HERMES_HOME>\skills\<分类>\`（本机 Hermes 主目录 = <HERMES_HOME>，不是 ~/.hermes）。

**实测**：

```bash
hermes mcp test v8-workbench
```

期望：`✓ Connected` + `✓ Tools discovered: 16`。

连通≠可用：`hermes mcp test` 只证明握手和工具发现。再用 MCP python 客户端真调一次只读工具，确认返回真实数据（本工作台的 `get_platform_context` 会回 chunks/documents 数，能同时验证身份绑定）。跨 skill 参考：`native-mcp`（其 references 里的 mcp-client-verification 记录了客户端 API 形态与异常组读法）。

**避免重启的话术坑**：加 MCP server 后不要断言「必须重启」。实测本次 `hermes mcp test` 之前，运行中的 gateway 已热加载该 server（日志 `Added servers: v8-workbench`，当前会话工具列表就位）；但 `hermes config set` 自身不会宣告这件事。据实描述：「本次已即时生效」或「需重启」。

**装完必须只留用户要的那一个客户端**：用户说接 Hermes 却已被装了 openCode/Codex 时，把多装的都回滚（见下），并报告每项的实际移除证据（`npm ls -g` 输出、配置文件行数、进程数），不要只说「已清理」。

## 装错客户端要回滚

1. `npm uninstall -g opencode-ai`（npm 11 会拦 postinstall，包留着但无 bin，也是脏的）
2. 删/移 `~/.config/opencode`（安装前不存在的话）
3. **Codex**：删 config.toml 里 `# V8_WORKBENCH_BEGIN` 到 `# V8_WORKBENCH_END` 之间，以及 `[mcp_servers.v8-workbench]` 表；移走 `~/.codex/skills/v8-*`
4. `~/.v8-workbench/identity.json` 保留（复用 UUID，避免下次换号）

注意顺序坑：**先装 openCode 再装 Codex 不会改 UUID**（installer 只在文件缺失时生成），所以多装一次的代价只是脏文件，不是身份变更。
