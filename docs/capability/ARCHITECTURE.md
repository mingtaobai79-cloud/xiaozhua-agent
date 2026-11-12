# ARCHITECTURE｜2小爪 Agent v2 总架构（A1）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是 §一/§二/§三/§五 的展开，不新增定位）。
> 任务：seeyon-v2-capability-phase1 交付物 A1。证据纪律：STATIC / VERIFIED / LIVE 为事实，
> GENERATED 仅假设；无在盘证据处标 **UNVERIFIED**，不臆造。
> 本文件只描述架构与在盘事实引用，不含实现代码改动。
> 本文是 ROADMAP-v2 的目标架构展开；仓库实现与目录职责视图见 `../ARCHITECTURE.md`。
> 文中的数量、路径存在性和验证结果是编写时点的记录，不代表当前安装或宿主验收状态。

---

## 一、定位：两级兼容模型（展开 ROADMAP-v2 §一）

2小爪 Agent v2 的核心原则（引自 ROADMAP-v2 §一）：**不造新的 Agent，而是把 2小爪 现有能力、
代码、事实、运行环境和版本差异固化成 Agent 可调用、可验证、可兼容的 Capability——再以
"可安装的 Agent 角色与能力包"形态嵌入已有宿主。**

据此有两级兼容：

1. **2小爪 版本兼容（对内）**：客户当前仓库版本为 **Canonical**，能力定义稳定；
   版本差异走 **Version Adapter**（`adapter-5.3` / `adapter-5.4` / …），Agent 不自行判断版本分支。
2. **Agent Host 兼容（对外）**：2小爪 Agent = 可安装的 **Agent 角色 + 能力包**
   （Role / Facts / Skills / Tools / Code / Sandbox），经 Adapter 进入不同宿主；
   **不自研 Agent Loop / 记忆 / Planner / Agent OS**。

---

## 二、总架构图（两层 + Registry 契约总线 + 宿主 Adapter）

与 ROADMAP-v2 §二（目录骨架）逐项对齐。图：

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  宿主层 HOSTS（不自研 Agent Loop；只提供 Loop/记忆/Planner）                    │
│    Hermes 宿主   │   Codex 宿主   │   Claude Code 宿主                          │
└───────▲──────────────────▲──────────────────▲───────────────────────────────┘
        │                  │                  │
        └──────────┬───────┴──────────┬───────┘
                   │  adapters/{hermes,codex,claude-code}/   （AGENT-ADAPTER.md=A8）
                   │  暴露形态：MCP tool 清单 / Skill 文件 / 角色提示词包
                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  REGISTRY 契约总线（components/platform_operations/registry.py:              │
│                     UdcOperationRegistry.default()）                          │
│    · 登记 operation 契约：op_id / method / path / request / response /        │
│      status(证据等级) / write(写门) / inputs / verify 断言                    │
│    · 读写二分由 layer.py 写门执行：写契约 → POLICY_DENIED（agent 不出写）      │
└───────▲───────────────────────────────────────▲──────────────────────────────┘
        │（读面派发/回读）                        │（写方案 data，宿主执行）
        │                                       │
┌───────┴───────────────────────────────────────┴──────────────────────────────┐
│  GLOBAL 层（横向：Runtime / Sandbox / Evidence / Version / Registry / Adapter）│
│    Runtime   ：能力执行与环境探针（components/runtime/、platform_operations/   │
│                live_readonly.py）                                            │
│    Sandbox   ：CODE 能力隔离执行（ROADMAP §二 sandbox/）——现状未建，见 A6       │
│    Evidence  ：四层事实体系（STATIC→VERIFIED→LIVE→GENERATED），见 A4          │
│    Version   ：Canonical=客户当前仓库，差异走 Version Adapter，见 A5           │
│    Registry  ：契约总线本体（上框）                                            │
│    Adapter   ：宿主适配规范，见 A8                                            │
└───────▲───────────────────────────────────────▲──────────────────────────────┘
        │                                       │
┌───────┴───────────────────────────────────────┴──────────────────────────────┐
│  UDC 模块层（第一套完整样板，modules/udc/；本轮只做 UDC，禁止扩散）             │
│    Entity（实体/属性）  │  Page（页面 LIST/DETAIL）  │  MicroFlow（函数节点）     │
│    │  Metadata（页面树/元数据）                                              │
│    每模块统一流水线（ROADMAP §五）：Module → Capability Inventory →            │
│    CONFIG/CODE 分型 → 事实证据 → Tool Contract → Skill → Test →               │
│    Sandbox 需求 → Agent Adapter 暴露                                          │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
   基础设施面（证据来源，只读引用）：test2 活体环境 / 网关 / RDS / 物理表
```

**图的读法**：宿主向下经 Adapter 进入 Registry 契约总线；总线把动作分派到 Global 层横向能力
（Runtime/Sandbox/Evidence/Version/Registry/Adapter）与 UDC 模块层纵向能力（Entity/Page/
MicroFlow/Metadata）。写动作 agent 侧被写门拦下，只产出"方案 data"由宿主执行——这是本架构
"只读 agent + 宿主执行"的根本边界。

---

## 三、Global 层（横向能力，展开 ROADMAP-v2 §二 sandbox/ 与 §三/§四）

Global 层是六项横向能力，对所有模块（UDC/BPM/…/Gateway）通用：

| 能力 | 目标态位置（ROADMAP §二） | 在盘现状引用 | 证据等级 |
|---|---|---|---|
| Runtime | `sandbox/`（Global 级）+ 运行态契约 | `components/runtime/`；`components/platform_operations/live_readonly.py` | VERIFIED（测试覆盖）|
| Sandbox | `sandbox/`、`modules/sandbox/` | **未建**——本轮只写契约不建实现（见 A6） | UNVERIFIED |
| Evidence | `core/facts/` | 四层事实体系见 A4；registry `OperationStatus` 携证据等级 | VERIFIED |
| Version | `adapters/`（版本维度） | Canonical=客户当前仓库；registry 全部契约 artifact=5.3.517 | STATIC |
| Registry | `core/capabilities/` | `components/platform_operations/registry.py` | VERIFIED |
| Adapter | `adapters/{hermes,codex,claude-code}/` | `seeyon_host_bootstrap.py`（v1 adapter 入口，见 A8） | VERIFIED |

说明：ROADMAP-v2 §二 的目标态目录为 `core/ role|facts|skills|tools|capabilities`、
`modules/ udc|gateway|sandbox|item-mgmt`、`adapters/ hermes|codex|claude-code`、`installer/`、
`sandbox/`。**当前在盘仓库尚未重组为该目录形态**（现存为 `components/`、`core/registry.py`、
`docs/` 等）；本文件描述的是目标态架构，现存资产的映射见 A2 MODULE-INVENTORY 与 A7。

---

## 四、UDC 模块层（纵向能力，展开 ROADMAP-v2 §五）

ROADMAP-v2 §五 定义模块清单（编号 01–12）：01 UDC（样板）｜02 BPM｜03 SPI｜04 Connector｜
05 Standard Product｜06 Runtime｜07 Integration｜…｜11 事项管理｜12 Gateway。
**第一批只做 UDC 样板跑通全链，不扩散**——本文件只展开 UDC 层，其余模块仅进 A2 清单。

UDC 模块层四个能力域（ROADMAP §二 `modules/udc/`）：

| 能力域 | 语义 | 在盘契约（registry op_id，实测） | 证据等级 |
|---|---|---|---|
| Entity | 单据实体与属性 | `udc.entity.create` / `udc.entity.attribute.create` / `udc.entity.primary.by_app` / `udc.entity.attribute.all_by_entity` 等 | 见第五节 |
| Page | 设计态页面（LIST/DETAIL） | `udc.page_info.*`；设计态建页走 deploy_plan 第 3 步（非 registry op） | LIVE（见第六节）|
| MicroFlow | 函数节点/流 | `udc.microflow.function_node_tree`、`udc.flow.*` | VERIFIED_STATIC_BYTECODE |
| Metadata | 页面树/元数据 | `udc.metadata.page_tree`、`udc.metadata.page_exists_check` | VERIFIED_STATIC_BYTECODE |

> Metadata 注：`udc.metadata.page_tree` 端点 javap 原文为 `@PostMapping`，执行层只放行 GET，
> 故该契约在 PlatformOperationLayer 上为 `DENIED/POLICY_DENIED`，直至运行态确证其为只读读面。
> 属**已知边界**，非缺陷（依据：`components/platform_operations/registry.py` 该契约 note 字段）。

---

## 五、Registry 契约总线：在盘实测（不得臆造，以实测为准）

**来源文件更正**：任务描述写作 `core/registry.py`。实测 `core/registry.py`（52 行）是
`ComponentRegistry` 组件注册/派发类（`register/get/names/capabilities/discover/dispatch`），
**不含** 59+2 业务契约；业务契约的实际在盘位置为
**`components/platform_operations/registry.py`**（`UdcOperationRegistry.default()`）。
本文件以实测位置为准登记。

**实测数字**（脚本直接调用 `UdcOperationRegistry.default()`，见 `implementer/count_ops.py`）：

| 口径 | 数值 | 说明 |
|---|---|---|
| 登记项总数 | **64** | registry 字典条目数 |
| 去别名后 | **61** | 减 3 条别名：`udc.entity.get` / `udc.entity.list` / `udc.attribute.list` |
| 其中 R18 设计态部署契约 | **2** | `udc.deploy.normal` / `udc.deploy.search_status` |
| **基础契约** | **59** | 61 − 2 → 与任务口径 "59+2" 一致 |
| 读写二分 | write **7** / read **57** | `write=True` 的 7 条为写契约（写门 DENIED） |
| 证据等级分布 | VERIFIED_STATIC_BYTECODE **53** / UNKNOWN **9** / OBSERVED **2** | 与 A4 四层体系归并 |

> 结论：任务口径 "registry 59+2 契约" 可由在盘数据复现，但**仅当**口径定义为
> "去 3 条别名后的 61 条 = 59 基础 + 2 条 R18 部署契约"。裸数 64 与别名 3 条须一并登记，避免口径漂移。

契约总线职责（`registry.py` + `layer.py`）：登记 op_id/method/path/request/response/证据等级，
并按 `write` 标志经写门（`layer.py` 的 write/effective 判定）决定放行或 `POLICY_DENIED`。

---

## 六、宿主 Adapter 面：deploy_plan 四步（在盘事实引用）

**入口**：`seeyon_host_bootstrap.py` 的 `bootstrap()` 返回 `host["deploy_plan"]`
（`deploy_plan()` 定义在 `seeyon_host_bootstrap.py:119` 附近），实现体
`components/platform_operations/deployment.py: build_deployment_plan()`。

**四步（实测 `components/platform_operations/deployment.py`）**：

| # | op | method | path | verify |
|---|---|---|---|---|
| 1 | `udc.entity.create` | POST | `/service/udc/entity` | `GET /service/udc/entity/{id}` → publishState/tableName |
| 2 | `udc.entity.attribute.create` | POST | `/service/udc/entity/attribute` | `GET .../attribute/select-all-by-entity-id/{entityId}` |
| 3 | `udc.page.create` | POST | `/service/udc/page-info/base-info/create` | `GET /service/udc/page-info/select-by-appId/{appId}` 回读 caption+relationGroupId |
| 4 | `udc.deploy.normal` | POST | `/service/udc/runtime/deploy-normal`（body 包 `deployDto`） | RDS `udc_test2.udc_deploy_record` 最新行（deploy_type=2 state=1）+ 应用库 SHOW TABLES |

即 **建实体 → 建属性 → 建页 → RELEASE 构建**。方案 data 形状：`schema=seeyon-deployment-plan.v1`、
`readonly_plan=True`、`steps[]/enums/evidence/unknowns`。

**写门边界**：agent 侧 `deploy_plan` 只出方案 data，不发写；`udc.deploy.normal` 在写门仍判
`DENIED（POLICY_DENIED）`，宿主按 steps 执行真实端点并 verify。

**证据文件**：`docs/audit/udc-design-time-deploy-write-contracts.md`（6473 B，在盘）——
登记 2026-09-24 test2 全链 LIVE 实证：建实体 `BOOT_0000`（YanshouDan/验收单 id `7670732978062038177`）、
建属性 ×4 SUCCESS、建页 ×2（LIST `1871471844026226944` / DETAIL `2146495017352265083`）、
RELEASE 构建 `deploy_type=2 state=1`、物理表落应用库 `9000000000000000001_test2`。

---

## 七、架构约束（铁律，展开 ROADMAP-v2 §三）

1. **CONFIG / CODE 二分**（ROADMAP §三）：CONFIG 能力 = Agent 产结构化声明
   （`{"capability":"udc.entity.create","input":{...}}`）由平台执行（建实体/建字段/建页面/配权限/
   配路由/配菜单）；CODE 能力 = 配置表达不了的复杂规则/校验/转换/三方调用，**必须**走
   **Sandbox → Compile → Test → Validate → Execute**，**禁止 Agent 直出 Java 直跑**。
   deploy_plan 四步为 CONFIG 真例（结构化 steps，见第六节）。
2. **Canonical 版本 = 客户当前仓库**（ROADMAP §一）：能力定义稳定，版本差异走 Version Adapter
   （adapter-5.3 / adapter-5.4 / …）；**Agent 不自行判断版本分支**。
3. **不自研 Agent Loop / 记忆 / Planner / Agent OS**（ROADMAP §一）：只做"可安装的 Agent 角色 +
   能力包"，嵌入 Hermes / Codex / Claude Code 等已有宿主（见第二节宿主层）。
4. **证据纪律**（ROADMAP §四）：STATIC→VERIFIED→LIVE→GENERATED，GENERATED_HYPOTHESIS 永不进入
   VERIFIED_RULE；本文件所有事实引用附等级，无证据即标 UNVERIFIED。
5. **只做 UDC 样板不扩散**（ROADMAP §五）：其余模块（BPM/Gateway/…）只进 A2 清单，不执行审计。
6. **凭据 0 入仓**：registry / deploy_plan 一律"路径引用"凭据，不写机器值（见 deployment.py 铁律 040402）。

---

## 八、在盘事实引用表（本文件全部事实的来源）

| 事实 | 来源（在盘） | 等级 |
|---|---|---|
| ROADMAP 定位/骨架/能力模型/模块推进 | `docs/capability/ROADMAP-v2.md` @ `d76f7af` | STATIC |
| registry 64 条目 = 59+2+3 别名 | `components/platform_operations/registry.py` | VERIFIED（脚本实测）|
| 写门 DENIED / POLICY_DENIED | `components/platform_operations/layer.py` | VERIFIED |
| deploy_plan 四步 | `seeyon_host_bootstrap.py`、`components/platform_operations/deployment.py` | VERIFIED |
| 设计态写链 LIVE 实证 | `docs/audit/udc-design-time-deploy-write-contracts.md` | LIVE |
| 375 测试全绿 | `.venv/Scripts/python.exe -m pytest tests -q` → `395 passed`（09-28 实测，README L30 基线） | VERIFIED |
| 组件注册类 | `core/registry.py`（ComponentRegistry，52 行） | STATIC |

## 九、UNVERIFIED / 未建清单（不得当事实）

- **Sandbox 能力**：ROADMAP §二 目标态 `sandbox/`，现状**未建**，本轮只写契约（A6）。
- **目标态目录重组**：`core/{role,facts,skills,tools,capabilities}`、`modules/`、`adapters/`、
  `installer/` 尚未在盘落地——现存为 `components/` 等旧结构。
- **网关前缀**：多个运行态契约的 `网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）`
  （registry 契约 note 字段原话）。
- **registry UNKNOWN 9 条**：状态非 VERIFIED_STATIC_BYTECODE，须运行态回读确证后方可升级。
- **前端页面是否随 RELEASE 构建生成**：UNVERIFIED（见 audit 文档 §六）。
- **生成 Java 工程是否落 OSS/仓库**：UNVERIFIED（同上）。

## 十、与 ROADMAP-v2 的对应关系

| ROADMAP-v2 节 | 本文件节 |
|---|---|
| §一 定位（两级兼容模型） | 第一节 + 第七节约束 2/3 |
| §二 目录骨架 | 第二节总架构图 + 第三节 Global 层表 |
| §三 能力模型（CONFIG/CODE 二分） | 第七节约束 1 |
| §五 模块推进（Module Inventory） | 第四节 UDC 模块层 |

> 阶段/范围/验收标准不在本文件定义；本文件严格沿用 ROADMAP-v2，不新增定位。
