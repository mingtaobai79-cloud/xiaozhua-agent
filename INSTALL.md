# 一条命令装好

## Windows

```powershell
irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1 | iex
```

只装一个宿主：

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1))) -Hosts hermes
```

## macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.sh | bash
```

只装一个宿主：

```bash
curl -fsSL https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.sh | bash -s -- --host hermes
```

Windows 安装器的输出是英文（`[ok]` / `[..]` / `[fail]`）。这不是偷懒：`install.ps1` 必须纯 ASCII
且不带 BOM，否则 `irm | iex` 在 PowerShell 5.1 上直接解析失败（BOM 会让 `[CmdletBinding()]`
报"意外属性"；中文无 BOM 又会被按 ANSI 码页解成乱码）。中文说明只放在本文件里。

脚本做的事（全程不碰系统 Python、不动任何全局配置）：

```
1 找 Python ≥ 3.11（macOS 自带 3.9 不够，会自动去找 brew/uv/pyenv 的 3.11+；Windows 会查 py 注册表、uv、常见安装目录，跳过 Microsoft Store 的空壳别名）
2 拉代码 → ~/.xiaozhua/src      （Windows: %USERPROFILE%\.xiaozhua\src）
3 建 venv → ~/.xiaozhua/venv    （依赖只装在这里）
4 生成宿主配置 → ~/.xiaozhua/pkg（hermes / codex / claude-code 三选一或 all）
5 写 xiaozhua 命令 → ~/.xiaozhua/bin
6 自检：真起一次 MCP 服务数工具，数到 0 就报错退出
```

## 版本下限是 3.11（不是 3.12）

一开始写 3.12 是保守估计。实测 3.11.16 上：`compileall` 全通过、MCP 服务器正常起来
（self-check tools=64）、安装器自身单测通过 —— 所以放宽到 **3.11**。
3.12 以上当然更好，脚本会优先挑高版本。

## 网络不好 / git 被限速 / 没有 git 怎么办

安装器取代码有三条路，按顺序自动试：

```
1 本地目录   设了 XIAOZHUA_SRC 就直接复制（最快，完全不走网络）
2 git clone  --depth 1，最多等 180 秒
3 zip 下载   前两条都失败 → 从 codeload.github.com 下 zip 解开（不需要 git）
```

**手上已经有仓库副本时，直接这样装**（PowerShell）：

```powershell
$env:XIAOZHUA_SRC = 'C:\Users\你\xiaozhua-agent'
irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1 | iex
```

macOS / Linux：

```bash
XIAOZHUA_SRC=~/xiaozhua-agent curl -fsSL https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.sh | bash
```

用本地源装的，`xiaozhua update` 会**从这个目录重新同步**（不碰网络）。
那份仓库自己 `git pull` 一下，再 `xiaozhua update`，装好的那份就跟着更新了。

## MCP 会自动接进宿主

安装（和每次 `xiaozhua update`）之后，安装器调用各宿主**自己的 CLI** 注册 `xiaozhua`：

| 宿主 | 命令 | 落在哪 |
|---|---|---|
| Hermes | `hermes mcp add xiaozhua --command <venv python> --args <server.py>` | `hermes config path` 指向的 config.yaml |
| Codex | `codex mcp add xiaozhua -- <venv python> <server.py>` | `~/.codex/config.toml` |
| Claude Code | `claude mcp add xiaozhua --scope user -- ...` | `~/.claude.json` |

只有装了的宿主才会连（没装就跳过，不算失败）。不想自动连就加 `-NoLink`。

```
xiaozhua link --dry-run     # 只看会执行什么
xiaozhua link               # 手动重连（路径变了用这个）
xiaozhua unlink             # 从所有宿主移除
xiaozhua doctor             # 逐宿主核对：那条 xiaozhua 是不是指向本安装
```

**接完要重启宿主才生效**：Hermes 里用 `/reload-mcp`（新会话自动加载），Codex / Claude Code
重开进程。宿主的 `mcp list` 里应该看到 `xiaozhua` 指向 `~/.xiaozhua/src/adapters/mcp/server.py`。

## 装完先体检

```bash
xiaozhua doctor
```

```
 ✓ Python 3.11.16（要求 ≥ 3.11）
 ✓ 依赖 齐
 ✓ git 06e736a · 工作区干净 · 最新
 ✓ MCP serverInfo=xiaozhua-mcp tools=64
 ✗ 宿主 all → C:\Users\你\.xiaozhua\pkg
```

前四项 ✓ 就对了。✗ 逐条对应：依赖缺 → `xiaozhua update`；代码落后 → `xiaozhua update`；
宿主目录不存在 → `xiaozhua install --host all --write`。

`doctor` 默认**不联网**，加 `--fetch` 才会 `git fetch` 比落后多少提交。

## 以后升级只有这一条

```bash
xiaozhua update
```

```
更新前 0.2.0 (06e736a)
代码 06e736a → 9f31c2b  版本 0.2.0 → 0.2.1
✓ 依赖 pip install -e .
  宿主配置 hermes → C:\Users\你\.xiaozhua\pkg
 ✓ 自检 serverInfo=xiaozhua-mcp tools=64

更新完成 0.2.1 (9f31c2b)  用时 12.4s
```

顺序固定：**拉代码 → 快进合并 → 装依赖 → 重装宿主配置 → 真起 MCP 自检 → 记状态**。
任何一步失败都停在原地并告诉你怎么修：

| 退出码 | 含义 | 处理 |
|---|---|---|
| 2 | 不是 git 检出（压缩包装的） | 改用上面的一键安装 |
| 3 | 工作区有未提交改动 | 先 commit/清理；确认不要了用 `--force` 丢弃 |
| 4 | 本地有分叉提交，无法快进 | `git -C ~/.xiaozhua/src log --oneline HEAD..origin/main` 看清楚再 rebase |
| 5 | 依赖装不上 | 看报错，通常是网络或 pip 源 |
| 6 | 宿主配置写不了 | 目标目录权限 |
| 7 | 自检数不到工具 | `xiaozhua doctor`，多数是 Python 版本或依赖 |

**不会自动 stash 你的改动**——那些可能是还没提交的证据，宁可停下问你。

## 这是什么

UDC 平台的**操作能力包**。给你 64 个 MCP 工具，用来在低代码平台上
建应用对象、建枚举、建实体字段、配事件、配参照、建微流程等。

它不是 SDK，不需要写代码调用。装好之后，你在 Hermes / Codex / Claude Code 里
直接说话，AI 用这些工具去操作平台。

## 环境要求

- Python **3.11 或更高**（一键安装脚本会自己找；手动装才要你确认）
- git（`xiaozhua update` 靠它拉代码）
- 网络能访问你的环境（例如 `lowcode-test2.<你的域名>`）

## 装完的目录长这样

```
~/.xiaozhua/
  src/      git 检出（xiaozhua update 更新的就是它）
  venv/     Python 虚拟环境（依赖只在这里）
  pkg/      宿主配置产物
    hermes/
      mcp_servers.yaml                  ← 贴进 Hermes 配置
      skills/xiaozhua-agent-hermes/SKILL.md
    codex/
      config.toml                       ← 贴进 Codex 配置
      AGENTS.md
    claude-code/
      .mcp.json                         ← 贴进 Claude Code 配置
      CLAUDE.md
    MANIFEST.json                       装了什么、装到哪、校验和
  bin/xiaozhua                          命令本体
  state.json                            上次装到哪、装了什么宿主
```

里面的 python 路径和 server.py 路径都是**按你机器的实际位置自动生成的**，
直接复制粘贴就能用。

卸载 = 删掉 `~/.xiaozhua` 一个目录，再把 PATH 里那行去掉。

## 手动装（离线 / 压缩包 / 内网）

```bash
unzip xiaozhua-agent-0.2.0.zip && cd xiaozhua-agent-0.2.0
pip install "pyyaml>=6.0" "websocket-client>=1.6"
python installer/install.py --host all --target ~/xiaozhua-pkg --write
```

压缩包装的没有 `.git`，`xiaozhua update` 会直接拒绝（退出码 2）并提示改用一键安装。

## 必须看到这个才算装好

```bash
xiaozhua doctor
```

或者手工数：

```bash
python -c "
import sys; sys.path.insert(0, '.')
from adapters.mcp.server import TOOL_KEYS
print('工具数:', len(TOOL_KEYS))
"
```

**必须 ≥ 54 且不是 0**（当前 64；README 里写 54 是早先快照）。
是 0 就是没装对，别往下走。

再验一次 MCP 真的能起（把两行 JSON 喂给它）：

```bash
printf '%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"t","version":"1"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  | python adapters/mcp/server.py
```

看到两行 JSON 返回、第二行里有几十个 `"name"` 就对了。

## 工具怎么用分两种

### 第一种：只出 body，你自己发（33 个）

像 `enum_body` / `dto_body` / `refer_config_body` 这些，调用只返回一个 JSON body。
要不要真的提交、提交到哪，你自己决定。

```python
from xiaozhua_host_bootstrap import bootstrap
b = bootstrap()
body = b["enum_body"](app_id, "枚举名", "enumCode")
print(body)   # → 一个可以直接 POST 的 JSON
```

### 第二种：自己发请求（4 个）

`microflow_publish` / `entity_rule_publish` / `expression_verify` / `expression_filter`。
需要连上你浏览器里**已经登录**的页面，cookie 不会离开浏览器进程。

```python
# 先用调试端口起浏览器（Excel 之外都行）：
# chrome.exe --remote-debugging-port=9333
b["expression_verify"](tokens, context, cdp_port=9333)
```

**不需要把 cookie 复制到任何地方**。工具让页面自己发 `fetch(credentials:'include')`。

## 哪些工具能信

**不要凭本文判断，看权威清单**：`README.md` 第 2 节的工具表由
`docs/delivery/tool-status.json` 生成，每个工具都标了「只读/写/删」「是否需授权」
「已验证/未验证/已知不通」，并写明阻塞原因。

当前汇总（口径以 `docs/delivery/tool-status.json` 为准，下面是快照）：

```
67 个工具 = 平台侧 52 + 本地 15（含 3 个日志工具）

✅ 已验证      33   （平台侧 21 个在 test2 跑过完整闭环，本地 12 个装上即可用）
◐  部分验证     2   app_dependency_remove（REST 批删验过，GraphQL 单删未验）
                    expression_verify（传输通了，token 结构未定）
⚠  未验证      16   能出 body，不知道平台收不收
🔒 需授权       1   app_deploy_body（会触发真实构建，覆盖沙箱态）
❌ 已知不通     2   excel_template_body / excel_template_column
```

### 两个已知不通的

- `excel_template_body` / `excel_template_column`：test2 上
  `/service/udc/excel/template/create` 返回 Spring 404，
  `/udc/excel/template/create` 返回 OSS MethodNotAllowed。
  **不是工具写错，是链路缺失。** 换个环境可能就通了，用之前先探一次。

### 七个微流程工具要特别小心

`microflow_*` 七个全部**未验证**。后端 `checkSchema` 通过**不等于**前端能过 ——
必须在页面点「检查」，并逐个节点打开抽屉看有没有红字。前端绑定错只有前端认得出。

## ⚠ 会真删数据的工具

`app_dependency_remove` 调一次就真删。返回 `content: 1` 表示**删成功**，不是"接口通了"。

**只能删你自己刚 create 出来的行。** 拿列表里现成的行去试 = 事故
（本轮就发生过一次，见 `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md`）。

`enableDelete` 是准确的：`true` = 界面绿色「移除」可点，`false` = 灰色禁删。
但它只说「平台允许」，不说「你该拿它试接口」。

## 出问题看这里

| 现象 | 原因 | 解决 |
|---|---|---|
| `Python 3.11+ is required` / `需要 Python 3.11+` | 解释器太旧或 PATH 里没有 | macOS `brew install python@3.12`；Windows `winget install Python.Python.3.12`；已有解释器但没在 PATH：`set XIAOZHUA_PYTHON=C:\path\python.exe` |
| `缺 git` | 没装 git | 不装也能装：安装器会退回 zip 下载；或设 `XIAOZHUA_SRC` 指本地仓库 |
| `ModuleNotFoundError: No module named 'yaml'` | 没装 pyyaml | `xiaozhua update` |
| `ModuleNotFoundError: No module named 'websocket'` | 没装 websocket-client | `xiaozhua update` |
| 工具列表是空的 / internal error | python 版本太低 | `python --version` 要 ≥ 3.11 |
| `xiaozhua` 不是命令 | bin 不在 PATH | macOS 把 `export PATH="$HOME/.xiaozhua/bin:$PATH"` 加进 `~/.zshrc`；Windows 重开终端 |
| `update` 退出码 3 | 工作区有未提交改动 | 先 commit，或 `xiaozhua update --force` |
| clone 卡很久 | GitHub 被限速 | 等 180 秒自动转 zip；或设 `XIAOZHUA_SRC` 用本地副本 |
| `PageUnavailable: 调试端口 9333 不可达` | 浏览器没开调试端口 | 用 `--remote-debugging-port=9333` 重启浏览器 |
| `PageUnavailable: 没找到含 'lowcode-test2' 的页面` | 端口上的浏览器没打开你的环境 | 在那个浏览器里登录并打开平台首页 |
| 工具调用回 `BOOT_3000 message:null` | 参数形态不对，平台没给线索 | 对照 `docs/operation-contracts/` 下的契约 |

## 自己看细节

- `README.md` —— 九域能力表、安全边界、实测进度
- `docs/operation-contracts/` —— 99 份接口契约，每个接口的入参、错误码、坑
- `core/facts/` —— 事实格（反编译 + 实测得出）
- `docs/audit/mcp-setting-tools-live-batch1.md`、`mcp-tools-live-batch2.md`
  —— 哪些工具真跑过、跑出什么结果
