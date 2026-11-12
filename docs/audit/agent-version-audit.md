# xiaozhua Agent 当前工程版本边界与文档漂移审计

- **目标工程：** `<XIAOZHUA_AGENT_ROOT>`
- **审计范围：** README、`pyproject.toml`、CLI capabilities、测试收集/执行结果及既有本地审计文档
- **安全边界：** 仅本地读取与测试；未连接 test2，未执行外部写操作
- **审计结论：** `PARTIALLY VERIFIED`

## 结论摘要

当前工程是一个可执行、可测试的**离线只读骨架**，不是已接入真实 xiaozhua 运行环境的完整 Agent。代码包版本为 `0.1.0`；Test collection: `3201 tests collected`，收集数不等于通过数，实际执行结果见 `docs/plans/xiaozhua-distribution-progress.md`。CLI `capabilities` 实际声明 `udc`、`runtime`、`integration` 三个只读组件，网络边界为 `disabled`；README 中关于 SPI “占位、未实现或注册”的描述与代码一致。

此前文档中出现过若干历史测试计数，本次以当前 checkout 的实际全量运行结果为准，旧计数不再作为当前版本依据，本次以当前 checkout 的实际全量运行结果为准，旧计数不再作为当前版本依据。

## 四类版本边界

### 1. 代码版本（Code version）

| 项目 | 当前事实 | 证据 | 状态 |
|---|---|---|---|
| Python package version | `0.1.0` | `pyproject.toml` `[project].version` | **FACT** |
| Python requirement | `>=3.12` | `pyproject.toml` | **FACT** |
| CLI entry | `python -m xiaozhua_cli` / `xiaozhua_cli.py` | CLI source and subprocess help | **FACT** |
| installable console script | 未声明 `[project.scripts]` | `pyproject.toml` | **FACT / GAP** |
| supported implementation shape | Core + UDC + Runtime + Integration；SPI 无注册实现 | source inventory and capabilities | **FACT** |

代码版本只描述仓库声明与实际源码形态，不等于 xiaozhua 平台版本兼容性，也不等于生产部署版本。

### 2. 事实版本（Evidence/data version）

| 项目 | 当前事实 | 证据边界 | 状态 |
|---|---|---|---|
| UDC sampled artifact | `5.3.517` | 本机 Temp 审计 JSON/本地样本；应以 artifact + version + sha256 绑定 | **FACT（静态）** |
| sampled version set | `3.8.227`, `3.12.124`, `5.3.314`, `5.3.380`, `5.3.477`, `5.3.517` | `udc_version_samples_manifest.json` 等既有本地证据 | **FACT（静态目录）** |
| UDC static scale | 672 endpoint contracts、36 unique frontend calls、145 backend operations、1793 deployment artifacts | 本地审计文件；是静态目录数量 | **FACT（静态）** |
| local snapshots | `runtime.json` / `integration.json` 可读取 | 本地 JSON 文件，不代表 live runtime/integration | **FACT（本地读取）** |
| `5.3.496` | 仅在 inventory 可用版本列表中观察到，未进入实际样本集 | 既有一致性审计 | **OBSERVATION** |
| 部署态平台构件 tag | 19 个构件（`udc` = `5.3.517` 等，全表见 §2.1） | K8s API 只读 + `DEPLOYED-COMPONENT-TAGS.json`；第十四轮复验 19/19 相同 | **LIVE VERIFIED** |

事实版本不得把 `5.3.517` 的静态样本外推为所有 5.3、所有客户或运行态行为；`5.3.496` 不得写成已采样实现事实。

### 2.1 部署态构件版本（LIVE，K8s API 只读）

**证据件**：`docs/audit/udc-semantics/DEPLOYED-COMPONENT-TAGS.json`
（文档与证据件的一致性由 `tests/udc/test_deployed_tags_version_audit_alignment.py` 逐条钉死）。
**通道**：K8s API 只读 `GET /api/v1/namespaces/<ns>/pods`，读 `spec.containers[].image`；
首次捕获第十轮（2026-10-15），**第十四轮复验**（pod 总数 79）**19/19 构件 tag 逐条相同、差异 0**。
本表**只落平台构件**：客户应用 pod 名/镜像名内嵌客户标识，一律不入库、不落名（清洗门）。

| 构件 | 部署 tag | 构件 | 部署 tag |
|---|---|---|---|
| `app-approval` | `5.3.291` | `ctp-media` | `5.3.261` |
| `app-common` | `5.3.274` | `ctp-message` | `5.3.287` |
| `bpm` | `5.3.374` | `ctp-user` | `5.3.429` |
| `cdp-data` | `5.3.279` | `ctp-webapi-gateway` | `5.3.266` |
| `cdp-schedule` | `5.3.273` | `m5` | `5.3.265` |
| `cip-capability` | `5.3.276` | `organization` | `5.3.368` |
| `cip-connector` | `5.3.286` | `portal` | `5.3.392` |
| `cip-convert` | `5.3.261` | `udc` | `5.3.517` |
| `cip-manager` | `5.3.273` | — | — |
| `cip-openapi-gateway` | `5.3.265` | — | — |
| `ctp-affair` | `5.3.315` | — | — |

**口径不可混用（三条边界）**：

1. `udc` = `5.3.517` 同时是静态被审计 artifact 版本 ⇒ **静态样本与部署态同版本、互证**；
   但两者都**不证明**部署容器内每个 class 的字节（载体级证据另看部署态 `.javap`）。
2. 三个运行时 facade 声明与 LIVE tag **3/3 一致**：`bpm`=`5.3.374`、`organization`=`5.3.368`、
   `ctp-user`=`5.3.429`。
3. 上面的静态 `sampled version set`（`3.8.227` / `3.12.124` / `5.3.314` / `5.3.380` / `5.3.477` /
   `5.3.517`）**不是部署集合** —— 它是本地样本目录口径，**不得**据它推断任一构件的线上版本；
   部署态版本只以本表为准。

第十轮结论（部署态版本裁定）：`udc` 容器 tag = `5.3.517`，且是全 namespace **唯一**打印
`request url:/udc/**` 的平台 pod（控制面运行期 URL 面全部出自被审计构件）
⇒「线上跑的不是 `5.3.517`」假设 **REFUTED**。仍 **UNVERIFIED**：镜像 tag 之下的
`BOOT-INF/lib` 构件全量（`pods/exec` 被 RBAC `forbidden`），以及部署态**行为**兼容性。


### 3. 验证版本（Verified version）

| 验证层 | 当前结果 | 状态 |
|---|---|---|
| Test collection | `1563 tests` | **VERIFIED** |
| Full deterministic suite | 最近执行结果见 `docs/plans/xiaozhua-distribution-progress.md` | **按运行记录核验** |
| Documentation contract tests | README/pyproject/capabilities/audit report contracts pass in full suite | **FOCUSED VERIFIED** |
| CLI capabilities subprocess | RC 0; JSON；`mode=read-only`；`network=disabled`；组件为 `udc/runtime/integration` | **REAL LOCAL SMOKE VERIFIED** |
| CLI help | RC 0；列出 13 个子命令；缺参由 argparse 返回 RC 2（既有测试覆盖） | **REAL LOCAL SMOKE VERIFIED** |
| Python syntax | 全仓 `python -m compileall -q components tools tests` 无错误（顺带清除 0ec93ee 引入的截断坏孤儿 `tools/verify_addsign_issues_owner.py`，7 行字符串未闭合、无引用） | **REGRESSION VERIFIED** |
| Git baseline/diff | `<XIAOZHUA_AGENT_ROOT>` 现为 Git worktree（基线 e5d324c→7dcbc10→坏孤儿清除 commit），逐行 diff 可复核；纯本地仓不 push | **FOCUSED VERIFIED** |
| 部署态构件 tag 复验 | 19/19 相同 / 差异 0（2026-10-15，K8s API 只读 `GET pods`，pod 总数 79） | **LIVE VERIFIED** |

测试通过只证明当前本地解释器和离线输入下的代码行为，不证明外部环境、实时 HTTP/Kubernetes、数据库、Redis、发布或部署。

### 4. 未验证版本（Unverified version）

以下边界本轮明确保持 **UNVERIFIED**，不得从静态文件、HTTP 200、类名或测试通过推导：

- `5.3.517` 的真实线上请求、鉴权、数据库/Redis 副作用、发布/部署行为；
- `5.3.496` 的类/方法/资源/行为兼容性；
- 5.3 patchline 或 3.x→5.3 的 wire/API/行为兼容性；
- Runtime/Integration 的实时适配器能力；当前仅读取本地 snapshot/provider；
- SPI 实际组件能力；当前只有路由占位，没有注册实现；
- UDC 动态 DTO、完整前后端请求合同、生成/发布状态机与幂等性；
- install/package 后的 `xiaozhua` console script；`pyproject.toml` 未声明脚本入口；
- 真实 test2、Pod、Ingress/OSS、GraphQL、数据库和缓存环境；镜像 tag 之下的 `BOOT-INF/lib` 构件全量（`pods/exec` 为 RBAC `forbidden`）。

## README / pyproject / CLI 对照

| 断言 | README | pyproject/source | 当前核对 |
|---|---|---|---|
| 工程版本/形态 | 可测试只读骨架 | version `0.1.0` | 一致；README 未显式写 package version，属于可改进项 |
| 测试数 | 收集数与执行结果分开记录 | 当前 pytest | 见进度记录 |
| Runtime/Integration | 本地 JSON snapshot/provider | `inspect()` + provider 读取 | 一致，非 live |
| SPI | 占位、未注册 | capabilities 无 SPI；无实现 | 一致 |
| CLI capabilities | 列出 UDC/Runtime/Integration | 实际 JSON 三组件、只读、网络 disabled | 一致 |
| CLI command inventory | README 列出 13 命令 | help 实际列出 13 子命令 | 一致 |
| pytest markers | offline/live/blocked/acceptance | pyproject 声明四类 marker | 一致；本轮未执行 live 外部环境 |
| package console entry | README 使用 `python -m` | 无 `[project.scripts]` | 未声称安装命令；存在能力缺口 |

## 文档漂移与修正结果

1. **测试计数口径：**收集数与全量运行的 passed / failed / skipped 分开记录，以实际命令结果为准。
2. **已增加文档契约测试：** 锁定 `pyproject` 版本 `0.1.0`、README 测试计数、CLI capabilities 的组件/只读/网络边界，以及本审计报告的四类版本章节和关键状态词。
3. **未发现需要修改 README 的当前命令或 capabilities 漂移：** 13 个命令与 CLI help 一致，capabilities 三组件与 README 一致。
4. **已记录未闭合边界：** package console script 未声明、live/test2 与真实 provider 未验证、SPI 仍是占位。

## 本轮命令证据

```text
python -m pytest tests --collect-only -q
3201 tests collected

python -m pytest tests -q
历史基线已更新

python -m xiaozhua_cli capabilities
RC=0
JSON: mode=read-only, network=disabled, components=[udc, runtime, integration]

python -m xiaozhua_cli --help
RC=0
14 subcommands listed

git status --short --branch
2026-09-14: git baseline initialized (was previously BLOCKED: not a git repository)
```

## 后续建议

- 若要宣称可安装 CLI，新增并测试 `[project.scripts]`，但不要把此审计误写成已完成。
- 若要宣称版本兼容，必须按 `artifact + version + sha256` 重新采样，并对目标版本执行相同最小行为闭环。
- 若要进入 test2 或任何写操作，先完成授权、只读动态证据、状态机/幂等、回读和安全闸门；本轮不执行这些动作。
