# VERSION-COMPATIBILITY｜Canonical 版本规范 + 差异矩阵模板（A5）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是其 §一.1"Seeyon 版本兼容"与
> §二"Version Adapter"的展开，不新增定位/阶段）。
> 配套：`ARCHITECTURE.md`（第七节 Canonical 铁律）、`EVIDENCE-MODEL.md`（A4 四层 + OperationStatus 归并口径）。
> 铁律：**Canonical 版本 = 客户当前仓库**；版本差异走 **Version Adapter**，Agent 不自行判断版本分支；
> 凭据 0 入仓；无在盘证据的版本/格子标 **UNVERIFIED**，不编。本文只描述规范/模板/在盘事实映射，不改运行代码。
>
> **引用更正（truth over label）**：本 HANDOFF/ROUTE 完成标准引 "ROADMAP-v2 §一.1/§九"。实测
> `ROADMAP-v2.md`（71 行）章节仅 §一~§七，**无 §九**。本文件严格对齐**真实存在**的
> §一.1（定位 1：Seeyon 版本兼容，Canonical + Version Adapter）与 §二（目录骨架 `adapters/`、`sandbox/`
> 版本维度），**不引用不存在的 §九**；此更正已随 RESULT 回报 main（ROUTE 归属方）。

---

## 一、Canonical 版本规范（对齐 ROADMAP-v2 §一.1）

ROADMAP-v2 §一.1 原文：**"Seeyon 版本兼容（对内）：客户当前仓库版本为 Canonical，能力定义稳定，
差异走 Version Adapter（adapter-5.3 / adapter-5.4 / …），Agent 不自行判断版本分支。"**

据此给规范三要素：

| 要素 | 定义 | 在盘落点 |
|---|---|---|
| **Canonical 版本** | = 客户**当前仓库**实际部署的 Seeyon 版本。本轮在盘所有 UDC 能力契约锚定的版本 | **5.3.517**（`registry.py` 106 处 artifact 锚点；`udc-starter-runtime/entity/page/flow/customplan 5.3.517.jar` 全 5.3.517；test2 LIVE 环境版本，见 §三） |
| **Version Adapter** | 承接版本差异的适配层（`adapter-5.3`/`adapter-5.4`/…），按版本注入差异，不改变能力定义 | 目录骨架 `adapters/`（§二）+ Global 层 Version 能力（`ARCHITECTURE.md` 第三节）；**本轮未建实现**（目标态，归 A6/A8 后续） |
| **Agent 不判分支** | Agent 侧能力声明版本无关（以 Canonical 为准），不内嵌"if 版本 X 走 A 分支"的运行时判断 | 能力定义稳定=registry 契约不随版本变体复制；差异由 Adapter 在暴露面注入 |

**规范结论**：能力契约的"当前真相"永远锚 **Canonical（=客户当前仓库）**；
`registry.py` / `deployment.py` / `docs/audit/**` 全部证据在盘 = **5.3.517**，故本轮 Canonical=5.3.517。

---

## 二、差异矩阵模板（Capability × 版本 × 证据等级 三维）

### 2.1 模板结构（ROUTE 完成标准 A5 的 b：三维模板）

- **行 = Capability**（registry `operation_id`；UDC 列取 01 UDC，见 A2/MODULE-INVENTORY）。
- **列 = 版本**：`客户当前版本（Canonical）` × `上一版本` × `下一版本`（横向扩展 5.3.x / 5.4.x / …）。
- **单元格 = 证据等级**：填 A4 四层归并枚举——`STATIC / VERIFIED / LIVE / GENERATED(待证) /
  UNVERIFIED / UNKNOWN`（对应 A4 §二 的 OperationStatus 归并口径）；**空值=UNVERIFIED 登记，不编**。
- **差异（可选列）**：该版本相对 Canonical 的已知差异描述；无在盘差异证据则留 `—`（不臆造差异）。

```
                 ┌────────────────────────────────────────────────────────────────┐
                 │ Capability │ Canonical(5.3.517) │ 上一版本 │ 下一版本 │ 差异   │
 Capability ─────┤  证据等级  │      证据等级       │ 证据等级 │ 证据等级 │ (文本) │
  udc.entity.*  ─┼────────────┼─────────────────────┼─────────┼─────────┼───────┤
  udc.deploy.*  ─┼────────────┼─────────────────────┼─────────┼─────────┼───────┤
  ...            └────────────────────────────────────────────────────────────────┘
```

**填格纪律**：
1. Canonical 列只填**在盘已证**等级（引 A1/A3/A4 已核定值，不新增）；
2. 上一版本 / 下一版本列，**无在盘证据一律 UNVERIFIED**（不得因"应该有差异"臆造等级或差异文本）；
3. 单元格等级沿用 A4 归并口径（VSB→STATIC、OBSERVED→LIVE、UNKNOWN→不可归并单列、UNVERIFIED→GENERATED 待证）。

---

## 三、UDC 列填充（在盘事实填第一列=Canonical 5.3.517）

**版本锚点（实测）**：
- **Canonical = 5.3.517**：`registry.py` 中 106 处 `5.3.517` artifact 锚点；`udc-starter-runtime/entity/
  page/flow/customplan` 全部 `-5.3.517.jar`；test2 LIVE 实证（`docs/audit/udc-design-time-deploy-write-contracts.md`）
  基于 5.3.517（如 `udc-web-5.3.517.jar` 活体 javap）。
- **上一版本 = 在盘存在但非 UDC 证据锚**：`5.3.358`（`metadata-artifact-5.3.358-evidence.md`，该文件 5 处 / 全 docs/audit 43 处）、
  `5.3.496`（全 docs/audit 53 处 / 最大单文件 28 处，属 metadata 证据）等在盘有证据，但 **UDC entity/deploy 契约证据未锚这些版本**（`registry.py` 实测仅含 5.3.517，无 5.3.358/496）→ UDC 行的"上一版本"
  对 entity/deploy 契约 = **UNVERIFIED**（不能把 5.3.358 的 metadata 证据当 UDC entity 的证据）。
- **下一版本（5.4.x）= UNVERIFIED**：全库 grep `5.4.` **零命中**，无在盘 5.4 任何证据 → 一律 UNVERIFIED，
  Version Adapter `adapter-5.4` 属 ROADMAP §二 目标态（未建）。

**差异矩阵（UDC 行，第一列 Canonical=5.3.517 填已核定等级；上一/下一版本按纪律全 UNVERIFIED）**：

| Capability（registry op） | Canonical 5.3.517 | 上一版本（5.3.358 等） | 下一版本（5.4.x） | 差异 |
|---|---|---|---|---|
| `udc.entity.create` | **LIVE**（`OBSERVED_LIVE`，169 实体回读；`deployment.py` step1） | UNVERIFIED（无 5.3.358 entity 证据） | UNVERIFIED（5.4 零证据） | — |
| `udc.entity.attribute.create` | **LIVE**（`OBSERVED_LIVE`，51 属性回读；step2） | UNVERIFIED | UNVERIFIED | — |
| `udc.page.create` | **STATIC**（`VERIFIED_STATIC_BYTECODE`，PageInfoController javap；step3） | UNVERIFIED | UNVERIFIED | — |
| `udc.deploy.normal` | **LIVE**（registry 状态 `OBSERVED`；构建成功 state=1） | UNVERIFIED | UNVERIFIED | — |
| `udc.deploy.search_status` | **UNVERIFIED/GENERATED 待证**（registry 态 `OBSERVED`（`210aa72`），完整路由活体未证） | UNVERIFIED | UNVERIFIED | — |
| registry 64 契约（整体） | **STATIC 53 / UNKNOWN 9 / LIVE 2**（A1 §五 分布口径；registry 态 OBSERVED 2/UNVERIFIED 0） | UNVERIFIED | UNVERIFIED | — |

> 等级引值均取 **A1（§五 registry 分布）、A3（§三 4 步 evidence.level）、A4（§三 deploy_plan 逐值）**
> 已核定结果，本文件**不新增臆造**；UDC 之外的 02–12 模块不进本矩阵（归 A2/后续批次）。

### 3.1 deployment.py 真实常量（落地示例，引在盘实值）

`components/platform_operations/deployment.py`（本轮核 L28–L37）的受控词表常量，**全部锚 5.3.517**：

| 常量 | 在盘值 | 来源（`deployment.py` 注释原话） |
|---|---|---|
| `STEREO_TYPES` | `("archive","standard","bill","archiveTree")` | "从 test2 目标应用 169 个真实实体回读统计" |
| `DATATYPES` | `("ENTITY","DATETIME","ENUM","STRING","MULTILINESTRING","BOOLEAN","BIGINTEGER","INTEGER","DECIMAL","DATE","Serial")` | "从 bill 单据实体 51 个属性回读统计" |
| `DEPLOY_TYPES` | `("TEST","RELEASE","ON_ONLINE","DELTA")` | "活体 pod 反编译 DeployParamDto / DeployTypeEnum (bytecode)" |
| `PROJECT_TYPES` | `("FRONTEND","BACKEND","ALL")` | "活体 pod 反编译 ProjectTypeEnum" |
| `TERMINAL_TYPES` | `("ALL","PC","MOBILE")` | "活体 pod 反编译 TerminalTypeEnum" |

> 这些是 **5.3.517 的活体/字节码快照**（A4 判 LIVE/STATIC）。铁律：它们是"平台侧受控词表的实测快照，
> 随活体复核刷新，非永久常量"（`deployment.py` 头注释 040402）——**换 Canonical 版本后须重新活体复核**，
> 不得跨版本硬编码；这正是 Version Adapter 要承接的差异。

---

## 四、边界与铁律自证

- **Canonical = 客户当前仓库**：本轮 = 5.3.517（在盘全证据锚点）；换客户仓库版本即换 Canonical，能力定义稳定、差异走 Adapter，Agent 不判分支。
- **凭据 0 入仓**：本文只引版本号/常量/证据等级，不含凭据值。
- **只描述规范/模板/在盘事实映射，不改运行代码**：未改 `deployment.py` / `registry.py` / `layer.py`。
- **不展开 02–12 模块**：矩阵只填 UDC（01）行；其余模块版本差异归后续批次。
- **不新增定位/阶段/验收**：Canonical/Version Adapter 引 ROADMAP-v2 §一.1/§二；证据等级引 A4；
  等级值引 A1/A3/A4 已核定，无自造口径。
- **UNVERIFIED 清单**：UDC 行"上一版本（5.3.358 等）/下一版本（5.4.x）"全列、`udc.deploy.search_status`
  完整路由、5.4 任何证据、`adapter-5.4` 实现（未建）——均标 UNVERIFIED，不编。

---

## 五、与 ROADMAP-v2 / 前件的对应

| 内容 | 来源 |
|---|---|
| Canonical=客户当前仓库 + Version Adapter + 不判分支 | ROADMAP-v2 §一.1 |
| 目录骨架 `adapters/`、`sandbox/` 版本维度 | ROADMAP-v2 §二 |
| Canonical 5.3.517 实据（106 锚点 + udc jars + test2 LIVE） | `registry.py`、`docs/audit/udc-design-time-deploy-write-contracts.md`（本轮 grep 实测） |
| 各 capability 证据等级 | A1 §五 / A3 §三 / A4 §三（已核定值） |
| 受控词表常量 | `components/platform_operations/deployment.py` L28–L37（本轮核） |
| 证据等级枚举口径 | A4 §二（OperationStatus 归并） |
