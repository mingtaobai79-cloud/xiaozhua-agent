# CHANGELOG

## 0.2.10 — 2026-11-25

新增自检工具 `xiaozhua_version`，把「改了不生效」这种事故从「靠人发现」变成「工具自己说」。

### 为什么加

0.2.9 修完覆盖度后，真实 MCP 通道仍然返回旧结果 —— 因为 MCP server 是**长驻进程**：
磁盘代码换成 0.2.9，进程内存里还是 0.2.8 的逻辑（11-24 与 11-25 17:00 启动的两对进程）。
查不到东西时，人和 AI 都容易误判成「索引坏了」，而实际是「进程旧了」。

### 做了什么

1. `platform_class_index.health()`：返回版本号、索引来源/规模、`processStart`，并判两种陈旧：
   - `code_stale`：磁盘 `VERSION` / `server.py` / 本模块 mtime 晚于进程启动 → 宿主没重载；
   - `index_stale`：签名库文件 mtime 晚于内存索引加载时刻。
2. 检索结果自带守卫：`search()` 的返回里带 `code_stale` / `index_stale` 与对应 `*_hint`。
   0 命中时不再只有「换个词试试」，还会说「你可能挂在旧进程上」。
3. 新 MCP 工具 `xiaozhua_version`（68 个工具）：返回 `{version, indexSource, classes, methods, ok | code_stale+action}`。
4. 顺手修了 `tests/test_mcp_tools_smoke.py` 的长期红灯：`logs_*` 三个工具需要 Loki 真环境，
   原来被判「没冒烟用例」；现在放进 `NEEDS_ENV` 白名单，并补一条「入口必须在」的闸门。

### 用法

```
查到 0 条 / 觉得「改了没用」→ 先跑 xiaozhua_version
  code_stale=true  → 重启宿主（或 xiaozhua update 后重连 MCP）
  index_stale=true → 同上，重建索引进程
  ok=true          → 索引没问题，安心换词/放宽过滤
```

### 验证

```
tests/test_index_data_resolution.py   17 passed（新增 5 条：health 字段、code_stale、index_stale、0 命中带提示、MCP 注册）
全量 pytest                            236 failed / 2694 passed（比 0.2.9 少 2 条红：冒烟白名单 + 文档计数）
xiaozhua_version                       实测 ok=true, classes=21389, methods=224320
```

## 0.2.9 — 2026-11-25

修 `platform_class_search` / `platform_class_methods` 的**覆盖度**问题：索引文件里明明有 21389 类，
工具只能查到 2669 类（12.5%），UDC 的 DTO / 枚举 / 非 AppService 接口全部 0 命中 ——
用户用 Claude Code 实测时表现为「查不到、以为索引缺件」，只能退回 javap。

### 根因

`_index()` 里有一句 `if _bucket(name):` —— `_bucket()` 只认三类
（`util` / `AppService` / `.spi.`），其余 **18720 类被直接丢弃**，而签名库本身是全量的。
`udc.*` 共 2947 类，只有 348 类能查到（11.8%）；`com.seeyon.udc.common.dto.UdcPageInfoSearchDto`
这种天天要用的 DTO 恰恰是查不到的那批。

### 改法

1. 全量入索引：`bucket = _bucket(name) or "other"`，`bucket` 从「准入门槛」降级为「标签/优先级」。
2. 排序加一层：匹配质量 → 常用桶优先（util/AppService/SPI）→ 方法数。
   「日期」「缓存」这类中文词仍然先出 `DateUtils` / 缓存工具类，不会被 18720 个 DTO 淹没。
3. `methods_of()` 对任何类都能列方法；找不到时提示「不在签名库里（21389 类）」并给相似候选。
4. `stats()` 的 `source` 改成解析出的真实路径，`byBucket` 多一个 `other` 计数。
5. MCP 工具描述与 README 数字同步：21389 类 / 224320 方法，其中 2669 类带中文标签并优先。

### 量化

```
索引类数     2,669  →  21,389      （方法 26,235 → 224,320）
udc 类可见    348  → 2,947
UdcPageInfoSearchDto    0 命中 → 1 命中（10 个方法可列）
PageUrlTypeEnum         0 命中 → 1 命中
建索引耗时   0.29s → 0.67s（进程内缓存一次）  搜索单次 0.05–0.07s
```

### 闸门

`tests/test_index_data_resolution.py` 增 3 条：全量覆盖（≥21000 类 / ≥220000 方法 / other ≥18000）、
UDC DTO 与枚举可搜可列方法、`docs/` 与 `fixtures/` 两份签名库 sha256 一致（防漂移）。
`tests/test_platform_class_index.py` 的「不在索引里」断言跟着更新。

### 验证

```
tests/test_index_data_resolution.py   12 passed
tests/test_platform_class_index.py    18 passed
全量 pytest                            238 failed / 2684 passed（既有失败，差集为空）
```

## 0.2.8 — 2026-11-25

修 0.2.7 引入的回归：装机环境里 `xiaozhua_platform_class_search` / `platform_class_methods`
报「signatures.txt.gz 不存在（缺件，索引不可用）」。

### 根因

签名库躺在 `docs/audit/signatures.txt.gz`，而 `docs/` 是工作区（审计报告、客户证据），
0.2.7 收紧安装树时被 `installer/selfupdate.py::IGNORE_DIRS` 整个排除 —— 装机树里没有这个文件，
代码却只认那一个路径。两个工具、同一个死路径。

### 改法

1. **索引数据挪到发行位置**：`fixtures/reference/signatures.txt.gz`（2.1 MB，随产品走）。
   `fixtures/` 不在安装排除列表里，装机树会带上；`docs/` 仍排除。
2. **新增 `core/index_data.py`** 统一解析顺序：

   ```
   1. $XIAOZHUA_INDEX_DIR/<name>        显式覆盖
   2. <src>/fixtures/reference/<name>    发行位置（installed 也有）
   3. <src>/docs/audit/<name>            工作区旧位置（兼容）
   4. <src>/docs/audit/reference/<name>
   5. ~/.xiaozhua/data/<name>            用户自备/热更新
   ```

3. 两个工具改走 `resolve()`，不再拼死路径。
4. 缺件报错改成可执行提示：列出自试过的所有路径，并给出三条自修路径
   （`xiaozhua update` / 复制到 `~/.xiaozhua/data/` / 设 `XIAOZHUA_INDEX_DIR`）。

### 回归闸门（`tests/test_index_data_resolution.py`，9 条）

- 签名库必须在 `fixtures/reference/` 且在 git 里；
- `resolve()` 命中发行位置、缺件返回 None；
- 缺件提示必须含三条自修路径；
- 安装排除表：`docs` 在、`fixtures` 不在；
- 两个工具源码里不许再出现 `docs/audit` 硬拼路径；
- 端到端：`Utils` / `AppService` 能搜到类，`JsonUtils` 能列出 28 个方法。

### 验证

```
tests/test_index_data_resolution.py   9 passed
tests/test_documentation_contract.py  6 passed（测试收集数 3317 → 3326 同步）
全量 pytest                            238 failed / 2681 passed（既有失败，差集为空）
```

## 0.2.7 — 2026-11-25

发行面与工作区分开、安装器 UTF-8 全链路、现场报告迁出与客户标识占位、自定义微流程分层事实修正。
本版以「仓库能装到别人机器上而不带环境」为主线，功能面不变。

### 1. 发行面 vs 工作区（`f6bbfba` `bd26b9c`）

- 仓库只带骨架：真实主机/namespace/appId/租户/桶名/凭据路径一律进 `~/.xiaozhua/config` 或
  `config/environments.local.yaml`（该文件 gitignore，`test_local_overlay_is_not_tracked` 盯着）。
- 装机树不再复制工作区；安装件里不带本机覆盖层与内部笔记。

### 2. 安装器（`3c926f7` `36c6927` `e93cbdb`）

- 子进程统一 UTF-8 解码 —— GBK 控制台下 `doctor` 不再抛 `UnicodeDecodeError` 崩线程。
- 安装树不再复制工作区（避免把内部笔记/证据带进用户机器）。
- `install.ps1` 注释改回 ASCII：PowerShell 5.1 无 BOM 时非 ASCII 注释会乱码，`irm | iex` 直接挂。

### 3. 事实修正：自定义微流程是**两层**（`748a09d`）

原文把两层的签名混成一条。实测（`billarchive2776130152975518413`，build 5.3.81，facade jar）：

```
custom/service/microflow/CustomMicroFlowService.class     ← 扩展入口，裸 DTO
  (PageDtoRequest<…>)PageData<…>           分页用平台分页类型，仍不是 SingleRequest
api/microflow/CustomMicroFlowAppService.class             ← 对外，平台实现
  (SingleRequest<…>)SingleResponse<Void>    包装只在这一层
```

判据：**类在 `custom.service.microflow` 包里、签名无 `SingleRequest` ⇒ 这是你要实现的接口**；
名字是 `XxxCustomMicroFlowService` 还是 `<Xxx>ServiceService` 随模板版本变，不能按应用名拼。

### 4. 现场报告治理（`d0e764e` … `3d5f36a`，11 个提交）

- 55 份零引用现场报告迁出仓外，落 `_attic_pending/` 台账并逐处标「已迁出至 …」。
- `docs/` 正文客户标识占位：真实 appId → `900000000000000000{1..4}`，域名 → `example.com`。
- **`artifacts/` 与 `live-evidence/` 保留原值** —— `test_evidence_data_may_retain_platform_ids`
  把「可复核性」当前提，洗掉就按不了 path:line 复核。
- **环境约定保留**（各环境的 kubeconfig 名、namespace 前缀）：它是操作知识，不是客户标识。

### 5. 卫生基线收紧

| 项 | 之前 | 现在 |
|---|---|---|
| `LEGACY` 白名单 | 6 条 | 2 条（盘点表 + docstring 证据锚点） |
| `BASELINE_FACTS_HITS` | 200 | 93 |
| 分发脱敏表 `SCRUBS` | 2 个 appId | 4 个 appId + 库名 |

### 验证

```
tests/test_distribution_hygiene.py           5 passed
tests/udc/test_{column_discovery,udc_semantics,entity_field_matrix}_index  7/6/7 passed
全量 pytest                                   238 failed / 2672 passed（既有失败，差集为空）
```

## 0.2.6 — 2026-11-24

运行期日志接进 MCP：`logs_search` / `logs_labels` / `logs_envs`（Loki，经 Grafana proxy，只读）。

### 为什么走 Grafana 而不是 Loki 3100

`loki-read:3100` 是集群内地址，本机不可达；Grafana 的 datasource proxy 已经把鉴权和租户选好了：

```
{grafana}/api/datasources/proxy/{id}/loki/api/v1/query_range
```

### 仓库里只放机制，不放环境

**工具本身不认识任何具体环境** —— 没有写死的主机、namespace、app、pod，也没有默认 env。
环境名、Grafana 地址、datasource 全在使用者自己的 `~/.xiaozhua/logs.yaml`（模板
`config/logs.example.yaml` 只有占位符），该文件不进 git。

```yaml
environments:
  <env-name>:
    grafana: https://grafana.example.com
    datasource: <datasource 名字或数字 id>   # 名字会先查 /api/datasources
```

凭据只认环境变量：`GRAFANA_USER` + `GRAFANA_PASSWORD`，或 `GRAFANA_TOKEN`（优先）。
仓库、安装件、日志里零凭据、零客户主机。

### 工具口径

| 工具 | 作用 |
|---|---|
| `xiaozhua_logs_search` | 时间窗查日志；`query` 给了就原样当 LogQL，否则按 namespace/app/pod/grep 拼；返回 `{ts,pod,app,line}` 倒序 + `truncated` |
| `xiaozhua_logs_labels` | 列 label 名/取值，用来发现有哪些 app / pod / namespace |
| `xiaozhua_logs_envs` | 配了哪些环境 + 每个环境能否列 label（连通性自检） |

### 验证

```
tests/test_logs_loki.py        10 条，全离线（monkeypatch 掉 HTTP）
tests/test_distribution_hygiene.py  断言发行面不含客户/环境标识
MCP tools/list                 67 个
```

### 还没做的

- K8s 侧（pods / pod / logs / 容器内文件 / restart）：`providers/kubernetes_readonly.py`
  目前只有 fixture、网络禁用；本机无 kubectl。下一步加 `k8s_*`，写操作（restart）走确认门。

## 0.2.5 — 2026-11-23

一条命令装完就把 MCP 接进宿主（hermes / codex / claude-code），更新时自动跟着刷新。

### 之前的问题

安装器只往 `~/.xiaozhua/pkg/` 写"配置片段"，宿主真正的 `config.yaml` / `config.toml` /
`.claude.json` 一动不动 —— 所以装完了宿主里看到的还是旧路径（甚至直接看不到）。
`xiaozhua update` 更不会碰宿主配置，路径变了也不会自己修。

### 现在的做法

安装/更新之后调用各宿主**自己的 CLI**（不手改配置文件，schema 和校验交给宿主）：

```
hermes mcp add xiaozhua --command <venv python> --args <server.py>
codex  mcp add xiaozhua -- <venv python> <server.py>
claude mcp add xiaozhua --scope user -- <venv python> <server.py>
```

- 安装默认连（`-NoLink` 可关），state 记 `link: true` + `link_hosts`
- `xiaozhua update` 发现 `link` 就自动重连一次 → **安装目录变了也能刷**
- 新增 `xiaozhua link` / `xiaozhua unlink`（`--dry-run` 只打印命令）
- `xiaozhua doctor` 会逐宿主核对"那条 xiaozhua 是不是指向本安装"，指错就红

### 踩到的两个坑（已固化成测试）

1. **`hermes mcp add` 是交互式的**：列出 64 个工具后问
   `Enable all 64 tools? [Y/n/select]:`。没有 stdin 时它回 `Cancelled.`
   而**退出码仍是 0** —— 只看 returncode 会判成功，实际是把宿主里原有的条目删掉了。
   现在喂 `Y`，并把 `Cancelled` 一律判失败。
2. **已存在时 claude 直接报 `already exists`**：所以顺序是 remove → add，
   且 add 失败会立刻重试一次，失败必须显式报红，不许静默。

### 实测（本机三家全部核对过）

```
hermes mcp list   xiaozhua  C:/Users/白明涛/.xiaozhua/ve...  all  ✓ enabled
codex  mcp get    xiaozhua  enabled: true  stdio  ~/.xiaozhua/venv/Scripts/python.exe
claude mcp list   xiaozhua: ~/.xiaozhua/venv/.../python.exe ~/.xiaozhua/src/adapters/mcp/server.py  ✔ Connected
xiaozhua doctor   ✓ MCP 已连 hermes、codex、claude-code
```

## 0.2.4 — 2026-11-23

启动器写死绝对路径的坑：中文用户名变成 `???`，`xiaozhua` 直接不可用。

### 现象（本机真跑出来的）

```
PS> xiaozhua doctor
python.exe: can't open file 'C:\Users\???\.xiaozhua\src\installer\selfupdate.py': [Errno 22]
```

shim 用 `Set-Content -Encoding ASCII` 写盘，`C:\Users\白明涛\...` 落成 `C:\Users\???\...`；
cmd 找不到解释器，退回 PATH 里的 uv python，再拿 `???` 路径去开脚本。

### 改法

shim 里不写任何绝对路径，改为按自身位置定位：

- `xiaozhua.cmd` → `powershell -File "%~dp0xiaozhua.ps1" %*`
- `xiaozhua.ps1` → `$XzHome = Split-Path -Parent $PSScriptRoot`，再拼 venv / src

两个文件保持纯 ASCII，中文用户名、目录搬家都不受影响。

### 顺带把 zip 安装的 update 补真

之前安装器提示"zip 装的 update 会重新下 zip"，实际没实现。现在 `sync_from_zip()` 用
`urllib` + `zipfile` 整包重下再覆盖，没 git 也能升级。

### 实测

```
irm|iex              clone 180s 超时 → 自动转 zip（约 50s）→ tools=64
xiaozhua doctor      5 项全绿，本地源那行显示源目录
xiaozhua update      本地源重新同步 → 依赖 → 宿主 → tools=64，12.1s
```

## 0.2.3 — 2026-11-23

代码来源不再只有 git clone：加本地目录与 zip 两条路，解决"GitHub 拉不动就装不上"。

### 起因

你机器上 `irm | iex` 走到 clone 就停住：`git clone --depth 1` 420 秒没完成（GitHub 被限速）。
之前只认 git clone，网络一慢就必然失败，而且没有任何退路。

### 三条取代码路径（按顺序自动试）

1. **本地目录**：设 `XIAOZHUA_SRC` 直接复制工作树（不碰网络，最快）
2. **git clone**：`--depth 1`，`Start-Job` + 180 秒超时
3. **zip 下载**：`codeload.github.com/<slug>/zip/refs/heads/<branch>`，`Expand-Archive` —— 这条**不需要 git**

### 顺带

- `xiaozhua update` 支持本地源安装：state 里记住 `source`，update 时从该目录重新同步
- doctor 区分三种安装形态（git 检出 / 本地源 / zip），不再一律说"无法自动更新"
- install.sh 同样支持 `XIAOZHUA_SRC`（rsync 或 tar 复制，不依赖 git）
- 取代码失败时直接给出修法：`$env:XIAOZHUA_SRC='...'` 指向本地仓库

### 实测

```
本地源安装（干净 PATH，模拟你的终端）：Python 3.11.16 → 复制 → venv → 依赖 → 宿主 → tools=64
xiaozhua doctor                      5 项全绿（本地源那行显示源目录）
xiaozhua update                      从源目录重新同步 → 依赖 → 宿主 → tools=64，10.6s
shallow 仓库 update                   c121523 → 68d7ff1，仍是 shallow（depth-1 拉取，没拉全历史）
```

## 0.2.2 — 2026-11-23

把 Python 下限从 3.12 放到 3.11，并让 Windows 安装器真的能找到解释器。

### 起因（用户真机）

`irm | iex` 报 `[fail] Python 3.12+ is required`。查下来这台机器上：

- 系统级只有 **Python 3.11.9（32 位）** + uv 管的 **3.11.16（x64）**，没有 3.12；
- 用户 PATH 里有 Python311-32 的条目，但路径被写成了乱码（`C:\Users\??????\...`），等于没有 python；
- `python` 只在 Hermes 进程里可见，用户自己的终端里根本不存在。

### 修法

1. 下限 3.12 → **3.11**。实测 3.11.16：`compileall` 全通过、MCP 起得来自检 tools=64、
   安装器单测通过。`pyproject.requires-python` 同步改成 `>=3.11`，否则 `pip install -e .`
   会被 metadata 拒（`requires a different Python: 3.11.16 not in '>=3.12'`）。
2. Windows 解释器发现顺序重写：`XIAOZHUA_PYTHON` → `py -0p` 注册表清单（**64 位优先、
   版本高优先**，避免 32 位 3.11 抢跑）→ `py -3.13/3.12/3.11/3` → PATH 的 python/python3 →
   `LocalAppData\Programs\Python`、`%APPDATA%\uv\python`、`Program Files`、`C:\Python3*`。
   Microsoft Store 的 `WindowsApps` 空壳别名直接跳过。
3. 失败时不再只说一句 not found，会列出**检查过的每个候选及其版本**。
4. git 找不到时兜底查 `Program Files\Git\cmd`、`LocalAppData\Programs\Git\cmd`、`D:\software\Git\cmd`。
5. `pip install -e` 失败时打印 pip 的真实错误行（之前静默回退，3.11 被 metadata 拒都没看见）。
6. 新增测试 `test_min_python_matches_pyproject`：`MIN_PY` 与 `requires-python` 必须一致。

## 0.2.1 — 2026-11-23

修 Windows 一键安装的编码炸弹：`irm .../install.ps1 | iex` 在 PS 5.1 上直接解析失败。

### 根因（两条路各踩一个）

- **带 BOM + irm|iex**：BOM 成了字符串首字符，`[CmdletBinding()]` 前面凭空多出一个"语句"，
  解析报 `unexpected attribute CmdletBinding`（实测 5 个 parse error，L16 起）。
- **无 BOM + 中文 + powershell -File**：PS 5.1 按 ANSI 码页解码 UTF-8，中文变乱码，
  乱码里会夹出 ASCII 标点，仍然解析失败（前一轮就是"缺少右 }"）。

### 修法

`scripts/install.ps1` 改为 **纯 ASCII + 无 BOM**，用户可见文案改英文（`[ok]` / `[..]` / `[fail]`），
中文说明全部留在 `INSTALL.md`。这样 `irm|iex`、`Get-Content -Raw` + `iesx`、`powershell -File`
三种入口都能解析。

### 新增回归测试

`test_install_ps1_is_ascii_and_bomless` —— 断言无 BOM、无非 ASCII 字节，并保留 ensurepip 自愈。


## 0.2.0 — 2026-11-23

安装与升级变成一条命令，跨平台（Windows / macOS / Linux）。

### 新增

- `scripts/install.ps1` —— Windows 一键装：
  `irm https://raw.githubusercontent.com/mingtaobai79-cloud/xiaozhua-agent/main/scripts/install.ps1 | iex`
- `scripts/install.sh` —— macOS / Linux 一键装：
  `curl -fsSL .../scripts/install.sh | bash`
- `xiaozhua` 命令（`installer/selfupdate.py`，零第三方依赖）：
  - `xiaozhua update` 拉代码 → 快进合并 → 装依赖 → 重装宿主配置 → 真起 MCP 自检 → 记状态
  - `xiaozhua doctor` 体检（默认不联网，`--fetch` 才比落后提交）
  - `xiaozhua install` 转发 `installer/install.py`
  - `xiaozhua version`
- `tests/test_selfupdate.py` 11 条离线契约测试（含 `bash -n` 与文档 URL 同源校验）

### 行为细节（都是刻意的）

- **脏工作区不自动 stash**：本地改动可能是未提交证据，`update` 直接拒绝（退出码 3）
- `update` 每个失败态有独立退出码（2 非 git / 3 脏 / 4 分叉 / 5 依赖 / 6 宿主 / 7 自检）
- 安装全部落在 `~/.xiaozhua/{src,venv,pkg,bin}`，**不碰系统 Python**，卸载 = 删目录
- macOS：自动找 `python3.12`（系统自带 3.9 不够），避开 `readlink -f` 与 bash 4 语法
- Windows：`install.ps1` 存为 UTF-8 **带 BOM**（PS 5.1 否则按 GBK 读，中文变乱码并报"缺 }"）

### 清理

- 删除 34 个 `__pycache__` / `.pytest_cache`（不含 `.venv`）
- `docs/audit/p0-custom-trigger/cleanup-backup/` 入 `.gitignore`（原始抓包已汇总进审计文档，文件保留在盘上）

## 0.1.0 — 2026-11-12

首个可分发的 MCP 能力包。**54 个工具**：平台侧 42 个（21 个真机验证过），本地 12 个。

### 能力

- **setting 域**：枚举 / 枚举项 / 枚举分类 / 选项集分类 / 字段集 / 字段集字段 / 参数 /
  二维码 / 扩展选项 / 扩展字段 / 流水号方案 / 流水号段 / 事件 / 事件数据
- **entity 域**：DTO / 索引 / 参照配置 / 部署方案
- **application 域**：版本列表 / 构建信息 / 依赖增删 / 部署 body
- **flow 域**：微流程节点构造、闸门校验、触发器、发布（未真机验证）
- **page 域**：列表页 / 详情页 schema 骨架、自定义页面脚手架（未真机验证）
- **expression 域**：89 个预设函数目录、表达式校验与过滤
- **本地工具**：仓库状态与同步、代码落点、工程形态、SPI 目录、需求生成骨架

### 真机验证（test2）

本轮新增验证 9 个工具并修复 4 个真 bug。

**验证通过（闭环 = create → 回读 → delete）**

| 工具 | 入口 |
|---|---|
| `serial_scheme_body` / `serial_section` | `udcSerialSchemeCreatePost` |
| `dto_body` | `udcDataTransferObjectPost` |
| `scalability_field_body` | `udcScalabilityPost` |
| `index_body` | `udcIndexPost` |
| `refer_config_body` | `udcReferConfigCreateConfigInfoPost` |
| `event_body` | `udcEventPost` |
| `event_data_body` | `udcEventCreateWithDataPost` |
| `app_version_list` | REST `search-app-edition` |
| `app_build_info` | `udcSandboxBuildInfoAppGet` |
| `app_dependency_body` | `udcApplicationDependentApplicationCreateBatchPost` |

### 修复

1. **`app_build_info` 参数类型** —— `udcSandboxBuildInfoAppGetInputBody` 在平台上不存在，
   必须是 `Map`。按名称猜 InputBody 在这个 operation 上不成立（`path:` 入参，平台未生成该类型）。
2. **`PageFetch` 命中 `/login/` 标签页** —— 同一浏览器同时开着登录页和工作页时会挑中登录页，
   请求全部打到登录页，平台回 `Unknown type xxxInputBody`，被误判成类型名写错。
   现在优先选非 `/login` 的页面。
3. **`scalability_field_body` 的 `dataTypeProperties`** —— 空字符串导致 `BOOT_3000`
   且 `message: null`（无任何线索）。缺省改为 `{}`；STRING/LONG/DATE/DOUBLE 四类实测均通过。
4. **`event_data_body`** —— `eventDataList` 必须是数组（传单对象报反序列化失败）；
   `attributes[].name` 增加回退到 `name` 键。

### 分发可用性

- **缺 pyyaml 时 `tools/list` 直接 internal error** —— 已改为延迟报错，
  缺依赖时仍能列出全部 54 个工具，只在真正读 config 时提示安装命令。
- **`pyproject.toml` 补 `websocket-client`** —— `PageFetch` 依赖它，原先未声明，
  远程装完一调用就 `ModuleNotFoundError`。
- **installer 删掉写死的 5 个 v1 工具名**。

### 已知不通

- `excel_template_body` / `excel_template_column`：test2 上
  `/service/udc/excel/template/create` 返回 Spring 404，
  `/udc/excel/template/create` 返回 OSS MethodNotAllowed。契约标 LIVE PASS，实测链路缺失。

### 操作纪律问题

- **误删 test2 应用依赖 `cip-manager`**（该行 `enableDelete: true`，平台允许删，
  界面为绿色「移除」）。已补回，**版本未变（5.3.273）**，仅行 id 变化。
  详见 `docs/audit/INCIDENT-20261112-deleted-builtin-dependency.md`。
  教训：验证删接口要 create 自己的数据再删，不要拿现成配置当试验品。

### 测试

`3172 passed / 23 skipped`（3195 collected）。
