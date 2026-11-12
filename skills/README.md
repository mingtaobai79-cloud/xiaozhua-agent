# seeyon-agent / skills

本目录的 skill 是**给 seeyon-agent 仓库自身定规矩的资产**，不是致远工作手册的镜像。

> **权威方向按目录族分（2026-11-07 裁决，详见 `docs/SKILL-DISTRIBUTION.md` §0）**：
> `01-platform`/`02-udc`/`03-v8-extension`/`04-integration`/`06-delivery`/`07-office-collaboration`
> 是 **Hermes → 仓库的脱敏快照**，别在仓库侧编辑正文；
> `05-agent` 与顶层 4 个是 **仓库 → Hermes 的源**，在仓库侧改才有效。
> 两者不矛盾——前者是操作手册（该带真实环境），后者是仓库规矩（与环境无关）。

## 边界（2026-10-22 立的规矩）

```
进仓库     纯平台机制 / 仓库规矩 / 方法论，无客户环境信息
           判据：PII 闸门（tests/test_deidentification.py）能过

留 Hermes  带真实环境的工作手册（测试环境域名、客户组织、工号、人名、凭据路径）
           位置：<HERMES_HOME>/skills/seeyon/<层>/<skill>/
           理由：它们本来就该写真实环境，是操作手册不是交付物
```

**权威副本在 Hermes**，仓库只是选择性镜像。禁止在仓库侧编辑 skill 正文，
否则会与 Hermes 漂移（已发生过：`seeyon-udc-module-landing` 仓库版 13KB
停在旧版本、Hermes 版 51KB）。

同步/检查工具：

```bash
python tools/core/_meta/sync_skills_from_hermes.py --check   # 只报告差异
```

## 目录内容

### 01-platform / 02-udc / 03-v8-extension / 04-integration / 06-delivery / 07-office-collaboration

历史镜像，**内容已过期**（Hermes 侧持续更新）。保留原因：被 tests 断言路径存在。

#### 02-udc —— 2026-11-08 抽入 3 个（含两个大件）

| skill | 作用 | 脱敏 | 文件 / 字节 |
|---|---|---|---|
| `udc-microflow-expression-nodes` | 微流程节点写点表达式/分支条件/子微流程传参 | 1 处表达式加密串实例值 → `<加密串>` | 9 / 130,840 |
| `seeyon-udc-custom-extension-engine` | UDC 扩展工程：从 jar 抽平台能力事实 | `datamigration<19位应用ID>` → 占位符；`gitlab.<客户域名>（真实域名只留 Hermes 侧）` → `<gitlab域名>`；`references/` 里 2 处内网 IP | 3 / 53,931 |
| `seeyon-udc-microflow-generation` | 建/改/验 UDC 微流程全流程（62 文件大件） | 人名 → 「用户」；客户组织 → `<客户组织>`；`scripts/regress_gates.py` 里示例 appId → `znxmglpt<应用ID>` | 61 / 740,284 |

> 三个都做了**整目录**复扫（含 `references/`、`scripts/`），不是只扫 `SKILL.md`。
> 抽入后全量跑 `tests/test_deidentification.py` + `tests/udc/test_docs_py_refs_alive.py` 全绿。
其中 `02-udc/seeyon-udc-setting`、`02-udc/seeyon-udc-module-landing` 被
`tests/udc/test_setting_*_asset_layout.py` 断言，改动需同步改测试。

#### 03-v8-extension —— 2026-11-08 首次实质抽取（7 个）

此前只有 3 个（`seeyon-excel-import-export-migration` / `seeyon-v8-spi` / `v8-iframe-sso-bridge`），
V8 工作流主线在仓库侧是**空的**。本轮从 Hermes 抽入 7 个，**逐文件**过三道扫（客户标识 / 内网 IP / 凭据值），
全部零命中才落盘；`references/` 子目录一并扫，不只扫 `SKILL.md`。

| skill | 作用 | 文件 / 字节 |
|---|---|---|
| `v8-framework-development` | 按官方客开通路写/改代码（含 `references/udc-custom-page.md`） | 2 / 29,849 |
| `v8-implementation-planning` | 出《开发实现方案》文档，不直接写代码 | 1 / 4,104 |
| `v8-knowledge-capture` | 把确认过的经验归档进 V8 知识库 | 1 / 2,879 |
| `v8-knowledge-query` | 检索知识库答开发问题，答案必须带来源 | 1 / 3,621 |
| `v8-online-diagnosis` | 脱敏日志 + 知识库/源码证据查线上问题 | 1 / 685 |
| `v8-quality-inspection` | 代码审计/质量检查，出 HTML 报告（含 7 份 `references/` 标准） | 8 / 71,834 |
| `v8-source-navigation` | 在已挂载源码里定位模块与符号 | 1 / 4,876 |

**2026-11-08 第二批：脱敏后抽入 3 个**

| skill | 作用 | 脱敏了什么 | 文件 / 字节 |
|---|---|---|---|
| `v8-patch-deploy` | 打 V8 平台 BP 补丁（v8patchctl 全流程） | `author` 字段里的人名；`references/` 里 1 处内网 IP | 2 / 16,052 |
| `v8-workbench-client-setup` | 装/修 V8 工作台 MCP 客户端 | 安装示例里 `--name <人名>`、工作台内网地址 → `<V8_WORKBENCH_HOST>` | 2 / 10,142 |
| `v8-workbench-update` | 检查/更新本机 V8 Skill 与更新脚本 | 8 处工作台内网地址 → `<V8_WORKBENCH_HOST>` | 1 / 3,312 |

> ⚠ `v8-workbench-client-setup` 脱敏后**地址是占位符**，真地址只在 Hermes 侧同名 skill 里 ——
> 仓库版是「怎么装」的方法论，不是能直接贴的命令。

> **14 个真缺口至此清零**（12 个进 `02-udc`/`03-v8-extension`，见上两节）。
> 唯一没进 `skills/` 的是 `seeyon-agent-hermes` —— 它是**宿主适配层**，源件在
> `adapters/hermes/Hermes-SKILL.md`，由 `installer/install.py` 物化，不该在 `skills/` 里再放一份。
>
> **全量镜像仍不做**：`tools/core/_meta/sync_skills_from_hermes.py --check` 当前报「补 1827」，其中含
> `config/environments.yaml`、`scripts/*.py` 等带真实环境的操作件 —— Hermes 是操作手册，本来就该带环境；
> 仓库只收「纯平台机制 / 仓库规矩 / 方法论」。**按 skill 逐个脱敏后抽，不做 `--apply` 全量。**

### 05-agent —— 本目录的核心

| skill | 作用 | PII |
|---|---|---|
| `seeyon-agent-component-architecture` | 组件分层与边界 | 通过 |
| `seeyon-agent-evidence-driven` | 证据优先交付 | 通过 |
| **`seeyon-agent-fact-protocol`** | ★ 往本仓库落事实/证据/skill 的通用规矩：五层归位、测试值只进 tools、R-E8 三样、六条口述硬规矩、可复用 vs 一次性脚本 | 通过 |
| `seeyon-constraint-extraction` | 从 jar / 前端 bundle 提取权威约束并落成校验模型 | 通过 |
| `seeyon-extension-usage`（02-udc） | 写扩展代码时的平台包用法：transport 出入参包装 / AppService 调用约定与框架 AOP / UDC 运行时链路与四类扩展点族 / 前端三包导出面与请求路由约定。只写环境无关的包内用法，环境结论留在证据区 | 通过 |

### seeyon-agent（根级）

宿主接入说明：`seeyon_host_bootstrap.bootstrap()` 的装配方式、四个能力、
离线/活体两种模式。**只存在于仓库**，Hermes 侧没有对应项。

### sdd-protocol / udc-trace-to-api

- `sdd-protocol` —— 三 Agent 协作协议 / VERDICT 规范
- `udc-trace-to-api` —— 浏览器抓包还原 UDC REST 契约

## 明确不在本目录的（留在 Hermes）

```
seeyon-low-code-environment        含 .env / kubeconfig / 人名
seeyon-udc-setting / runtime / design-time-build / page-debug
                                   含测试环境域名 + 客户组织
04-integration/*                   含客户实例名
v8-* （8 个）                       V8 工作台，与 seeyon-agent 仓库无关
```

## 新增 skill 的判定流程

```
1. 先问：这是「仓库规矩/平台机制」还是「某客户环境的操作手册」？
2. 跑 PII 预检（正则见 tests/test_deidentification.py）
3. 通过 → 放 skills/<层>/<skill>/，并在此表登记
   不通过 → 留 Hermes，不要脱敏后再塞（脱敏会破坏工作手册的可用性）
```
