# standard-product｜P2 对账（module_catalog 标注 / UdcOperationRegistry 59 口径 / 标品域↔客开域边界）

> 会话：`session-20260929-184027-7f85bd1f` ｜ 授权：main/`main/ROUTE.md` §3b HANDOFF-2（dedupe_key=`handoff-2-reconciliation`）
> 目标仓库：`<XIAOZHUA_AGENT_ROOT>` ｜ 口径：**纯静态、零活体**——未连 test2、未发任何 HTTP、未建测试应用
> **P1 冻结**：本轮**未改写** P1 绑定件。复核一致：`standard-product-contracts.md` sha256=`13a828343e8559640af103400c73f10b8af96d4ea81ebca38af098ec8cded168`（=P1-DECISION 绑定值），`evidence/bytecode/manifest.json` sha256=`4e53e5f0d5fa1b3e2444eea2559d884ec21da26e110510ab285ec4699003aa44`。
> 本件产物：本文件 + `evidence/reconciliation/`（复现脚本与实测输出）。全部落在 `core/facts/standard-product/**`。
> 凭据 0 入件；无证据一律 `UNVERIFIED`，不编。

---

## 0. 实测环境与复现入口

| 项 | 值 |
|---|---|
| 复现脚本 | `core/facts/standard-product/evidence/reconciliation/count_registry_contracts.py` ｜ sha256 `611e73990acc0b660526e85a7ad8ace650ab09391b093e47995a9bc5b22e9ab0` |
| 实测输出 | `core/facts/standard-product/evidence/reconciliation/count_registry_contracts.out.json` ｜ sha256 `3a07224c06d1e52b5338c3ca89aa91294536e36d2b8c8665822ae644848f9d72` |
| 运行命令 | `python <脚本>`（本机 `python`=3.11.16；**禁内联单行 python**，脚本先落盘再跑） |
| 运行性质 | 进程内 `UdcOperationRegistry.default()`，**零网络、零活体、零宿主** |
| 复现确定性 | 同脚本自 staged 位置原地重跑，`cmp` 与已存输出**逐字节相同（IDENTICAL）** |

脚本读数口径要点（避免误用 API）：`UdcOperationRegistry.all()` 返回 **`dict(operation_id -> UdcOperationContract)`**（`registry.py:137-138`），`len()` 即条目数；迭代得 **key**（字符串）。本脚本按 key 取值后逐条判型，不假定 list。

---

## 1. 对账一｜`module_catalog` 标注层级对齐（模块级 STATIC ≠ 件级 VERIFIED_STATIC_BYTECODE）

**在盘实据**：`components/module_catalog.py` ｜ sha256 `aaec8e8acd06693f16640d1ffbf1e450ae27474bcaeb19a969005c05a0a10bee`

- `module_catalog.py:8`（逐字）：
  `{"id": "standard-product", "kind": "standard_product_application", "status": "FACT", "verification_level": "STATIC"}`
- 同表旁证（`module_catalog.py:7-11`）：`udc`→`udc_platform`/FACT/**STATIC**；`spi`→**STATIC_CONTRACT**；`integration`→PARTIALLY_VERIFIED/**SNAPSHOT_ONLY**；`runtime`→PARTIALLY_VERIFIED/**LIVE_READ_ONLY**。
- 留存口径（`module_catalog.py:35-38`）：`retention_policy.durable_scope` 含 `"standard contracts"`；`limitations`（`:39-44`）第 2 条=「Standard Product Application and SPI remain separate modules from UDC.」

**层级关系（关键：两级不可混为一级）**

| 层级 | 载体 | 值 | 语义 | 可核验性 |
|---|---|---|---|---|
| 模块级标注 | `components/module_catalog.py:8` | `kind=standard_product_application` / `status=FACT` / `verification_level=STATIC` | 断言「该模块**存在**且其证据当前为静态证据等级」——是**模块登记**，不是能力/契约计数 | 源码在盘，逐字可读 |
| 件级核验 | `core/facts/standard-product/standard-product-contracts.md`（P1，sha256 `13a82834…d168`） | 契约格 A/B = **`VERIFIED_STATIC_BYTECODE`** | 断言「**这一件**（jar 内 class 条目）的接口签名/注解/类型引用已字节码实测，源 jar 在盘且 sha256 与 profile 逐字一致，可现场重跑」 | cfr 反编译 + jar/class 双层 sha256，见 `evidence/bytecode/` |

**对齐关系**：两者**方向一致、粒度不同**——模块级 `STATIC` 是「模块总体证据等级」的**声明**；件级 `VERIFIED_STATIC_BYTECODE` 是**对单件逐条落证的实测等级**。件级实测是模块级 `STATIC` 的**下钻证据**，但**不因下钻成功而升级模块级口径**（模块级仍是 STATIC，不因 P1 而变 VERIFIED/LIVE）。
**差异（须登记，禁合并）**：
1. 命名同名易混：`STATIC`（模块级）/ `STATIC_CONTRACT`（spi 模块级）/ `VERIFIED_STATIC_BYTECODE`（件级实测）是**三套**标签，分别出自 `module_catalog.py` 与件级事实格，**不得互相替代**。
2. 计数语义不同：`module_catalog` 的 `status=FACT` **不产生 capability 计数**（见 §3 与 MODULE-INVENTORY `#05`「Capability 数 = 0」）。
3. **模块级 STATIC 不覆盖**：本件未复核 `module_catalog` 内 `standard-product` 的 `STATIC` 是否覆盖全部三件 artifact（bpm-facade / ctp-user-api / cip-connector-api）→ 覆盖完备性 `UNVERIFIED`（本轮边界外）。

**结论**：模块级标注与件级核验**口径一致、层级不同、计数不互推**；对齐关系登记完毕，未混为一级。

---

## 2. 对账二｜`UdcOperationRegistry` 基础契约口径 = **59**（实测复现，非转述）

**口径来源锚（逐字）**
- `docs/capability/ARCHITECTURE.md` §五 ｜ sha256 `921913375da0c5fdd89a6395d5f8d58b681fa2944746bbcc5a483778f22c843b`：
  - `:121` 节题「五、Registry 契约总线：在盘实测（不得臆造，以实测为准）」
  - `:123-127` 来源更正：`core/registry.py`（52 行，`ComponentRegistry`）**不含**业务契约；实位=`components/platform_operations/registry.py`（`UdcOperationRegistry.default()`）
  - `:133` 登记项总数 **64**｜`:134` 去别名后 **61**（减 3 条别名 `udc.entity.get`/`udc.entity.list`/`udc.attribute.list`）｜`:135` 其中 R18 设计态部署契约 **2**（`udc.deploy.normal`/`udc.deploy.search_status`）｜`:136` **基础契约 59**（61−2，与任务口径「59+2」一致）
  - `:137` 读写二分 write **7** / read **57**｜`:199` 在盘事实引用表「registry 64 条目 = 59+2+3 别名 ｜ VERIFIED（脚本实测）」
- `docs/capability/MODULE-INVENTORY.md` §二 ｜ sha256 `54b96e3a7a0ee2f23b4604cfffd12ed90063ceb8568ce2fc513af60812a76121`：
  - `:38` 节题「二、Capability 数口径说明（沿用 A1 第五节纪律）」｜`:40` registry 实位=…`UdcOperationRegistry.default()`（本轮脚本实测）｜`:41` 裸数 64 → 去别名 3 → 61 → 去 R18 2 → **59 基础**；写 7 / 读 57

**实测结果（本脚本输出，与上锚逐项对齐）**

| 口径 | 锚值 | 本轮实测 | 判定 |
|---|---|---|---|
| 登记项总数 `len(reg.all())` | 64 | **64** | MATCH |
| 别名条数（结构性检出） | 3 | **3** | MATCH |
| R18 部署契约条数 | 2 | **2** | MATCH |
| 去别名后（非别名条目） | 61 | **61** | MATCH |
| **基础契约** `64−3−2` | **59** | **59** | **MATCH（与 TASK-GOAL「59」逐字一致）** |
| write / read | 7 / 57 | **7 / 57** | MATCH |
| registry 内非 `udc.*` 前缀条目 | 0 | **0**（`non_udc_prefix_entries=[]`） | MATCH |

**别名 3 条（结构性检出：与同签名条目逐字段同形、仅 `operation_id` 不同——来源 `registry.py:42-44` 的 `replace(...)`）**

| 别名 ID | 同形对端（original） |
|---|---|
| `udc.entity.get` | `udc.entity.select` |
| `udc.entity.list` | `udc.entity.all.by_app` |
| `udc.attribute.list` | `udc.entity.attribute.all_by_entity` |

**R18 部署契约 2 条**（`registry.py:123-128`，设计态构建/部署写族）：`udc.deploy.normal`（`OperationStatus.OBSERVED`, `write=True`）、`udc.deploy.search_status`（`OperationStatus.OBSERVED`）。

**非别名 61 分段（与 MODULE-INVENTORY `#01` 分段实测逐段一致 → 无漂移）**：
`entity 25 / flow 8 / application 6 / applog 6 / metadata 2 / microflow 1 / database 1 / datatype 1 / deploy 2 / entity_data 1 / page_info 2 / page_log 2 / role 1 / serial 2 / appinfo 1`（合计 61）。

**「写法口径」≠「运行期条目数」（main 早期 47 的口径澄清，禁混）**
以 `components/platform_operations/registry.py`（sha256 `e6680504a9c54bec7324f53a43e49d0c95fcd8a002cdbde5d2698d0a176369ec`，138 行）源码点计数：

| 源码口径 | 计数 |
|---|---|
| 含 `contracts[` 的行 | 46 |
| `contracts[...] =` 赋值语句 | 45 |
| `UdcOperationContract(` 构造调用点 | 42（其中 **1 处在 `:41` 的 `for` 循环内 → 代表 20 条 specs**；其余 41 处各 1 条） |
| `replace(` 调用点 | 3（`:42-44` 别名） |

→ 运行期条目数 = **20（`for` 批量生成）+ 41（循环外直构）+ 3（`replace` 别名）= 64**。
**结论**：源码「写法口径」（45/46 行、或 42 个构造点）与运行期 `dict` 长度 **64 不可互推**：`for` 循环使 **1 行源码代表 20 条**，`replace` 生成的别名在部分 grep 口径下被漏计。main 早期用 `grep contracts[...]` 得 **47 条**属此类**写法口径**（系统性少计），**非** registry 裸数 64——本件登记该区别，**59 基础口径只认运行期实测 64/3/2→59**，不认写法口径。

---

## 3. 对账三｜标品域 ↔ 客开域（UDC）边界

**客开/UDC 侧（registry = 客开域登记）**
- 实测：registry **全部 64 条前缀均为 `udc.*`**；非 `udc.*` 前缀条目 **0**（`non_udc_prefix_entries=[]`，`prefix_census` 见输出 JSON）。
- `docs/capability/MODULE-INVENTORY.md:43-45`（逐字）：**「registry 现网唯一前缀 = `udc.*`」**；「故 01 UDC 的 Capability 数 = 61（去别名口径），02–12 各模块 = 0」；「02–12 的『0』是**登记事实**（当前未登记），不代表『无能力』」。

**标品域侧（standard-product）**
- 实测：**标品域在 registry 登记数 = 0**（脚本 `standard_product_registry_count=0`：对 `bpm./ctp./cip./connector./sso./mobile./standard./spi./gateway.` 九类前缀全库扫描零命中）。
- `MODULE-INVENTORY.md:27`（`#05` 行，逐字摘）：「**05 | Standard Product** | `docs/audit/modules/standard-product-module-profile.json`（FACT / STATIC，bpm-facade-3.12.101.jar 484 类 + sha256）；`docs/audit/modules/udc-standard-code-evidence.json`；`module_catalog.py` 标 `FACT/STATIC` | **0** | P1」——**「Capability 数 = 0」为 registry 口径的登记事实**。
- 标品域侧实证（P1，未改写）：`cip-connector-api` 5.3.286 的 `com/seeyon/cip/connector/api/**` **20 个条目、20 个均为 `interface`**（P1 `standard-product-contracts.md:291-294`，sha256 `13a82834…d168`）——即标品域契约**由 jar 内接口定义承载，未进 registry**。

**标品域三 artifact（`docs/audit/modules/standard-product-module-profile.json` ｜ sha256 `38d1143ddde2c00ecbd78a2282489d6a5c3a9e2857ca13dd54dc7fbbf8ea8d07`）**

| 行 | artifact | version | class_count | sha256（profile 登记） | 本线分级 |
|---|---|---|---|---|---|
| `:9-13` | `bpm-facade` | 3.12.101 | 484 | `26b312fdd40cc921a4cd8d08239f6b8d857c02a5ac8d4db271d07f6fcbd98af0` | 补充格（jar 本体缺失） |
| `:16-20` | `ctp-user-api` | 3.8.215 | 49 | `5b1ec52abd87ba79abe962453776e54fa9bc27551aa171e76981d211a5950543` | UNVERIFIED（本体与产物均缺） |
| `:23-27` | `cip-connector-api` | 5.3.286 | 124 | `de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91` | VERIFIED_STATIC_BYTECODE（jar 在盘） |

- profile `:35` `scope`（逐字）：**「Independent Standard Product Application module; artifacts are not UDC core.」**
- profile `:38` `limitations`（逐字）：**「Versions are separate evidence units and must not be merged.」**

**边界结论**：两域**独立**——客开域契约登记于 `UdcOperationRegistry`（全部 `udc.*`，59 基础 + 2 R18 + 3 别名 = 64）；标品域契约由标品 jar 的接口定义承载，**在 registry 登记数 = 0**。二者靠 `module_catalog.RELATIONS` 的**声明式关系**相连（`module_catalog.py:17`：`customer-udc-application --calls--> standard-product`，`evidence` 逐字=「requires exact source/call-site evidence; relation not yet closed」）→ 该关系为**待核验的声明依赖**，**非** 运行期调用的 FACT（`module_catalog.py:43` limitations 第 4 条同义）。

---

## 4. 口径漂移登记（本轮发现，均如实登记、未静默对齐）

**D1（真差异）**：`ARCHITECTURE.md:138` 行「证据等级分布 VERIFIED_STATIC_BYTECODE **53** / UNKNOWN **9** / OBSERVED **1** / UNVERIFIED **1**」**本轮不可复现**。
- 实测 `OperationStatus` 分布 = `VERIFIED_STATIC_BYTECODE 53 / OBSERVED 2 / UNKNOWN 9`（**OBSERVED 2、UNVERIFIED 0**；合计 64，与锚一致）。
- 差异点定位（**F2 精确更正**，替换原句「`UNVERIFIED` 字样仅存于 `registry.py:126`」——该串全 `registry.py` 实测 **38** 处、多为 note 内「网关 service 前缀 UNVERIFIED」，字面不成立）：`registry.py:128` `udc.deploy.search_status` 的 `OperationStatus` 现为 **`OBSERVED`**。**可核验表述**：`OperationStatus.UNVERIFIED` 契约承载 = **0/64**；`evidence_level="UNVERIFIED"` 全 `registry.py` **仅 `:126` `deploy_search_evidence` 一处**，且该变量**定义后无引用（dead）**；`:128` 实引 `:127` `deploy_hist_evidence`（`OBSERVED_LIVE`）。⇒ 文档行疑为**较早时点**口径（当时 search_status 承载 UNVERIFIED），现行 registry 已移为 OBSERVED。
- **D1 第二上游站点（F1 补登）**：`docs/capability/MODULE-INVENTORY.md:41-42` 的「状态分布 VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 / OBSERVED 1 / UNVERIFIED 1」与 `ARCHITECTURE.md:138` **逐字同串**——同属上游文档时点漂移，本线不代改，仅登记。
- **方法学注记（F3）**：本件数值捕获命令 = `python evidence/reconciliation/count_registry_contracts.py > out.json`；Windows stdout 重定向产生 **CRLF**（`count_registry_contracts.out.json` 实测 103 CR + 103 LF，非纯 LF），比较须同法重跑 `cmp` 才一致；通用换行比较会假报不符。
- **影响面**：主口径 **64 / 3 / 2 / 59** 与「写 7 / 读 57」**不受影响**（均已复现）；受影响的仅是 `:138` 的状态分布行。**不代改**上游文档（非本线领地），只登记。

**D2（轴混用提示）**：`:138` 行标题写「证据等级分布」，但所列四桶（`VERIFIED_STATIC_BYTECODE`/`UNKNOWN`/`OBSERVED`/`UNVERIFIED`）是 **`OperationStatus`** 枚举值，非 `evidence[].evidence_level`。按 `evidence_level` 轴实测 = `VERIFIED_STATIC_BYTECODE 62 / OBSERVED_LIVE 2`（合计 64）。**两轴数值不同，引用时须写明轴**，否则即产生口径漂移。

**D3（正向确认，无漂移）**：`MODULE-INVENTORY.md:23` 的 UDC 分段实测（entity 25 / … / appinfo 1）与本轮**非别名 61 视图**逐段一致；`all64` 视图 entity 27 = 25 + 2 别名（`udc.entity.get`/`udc.entity.list`），差值可由别名集合解释 → **不是漂移**，是别名口径差。

**D4（登记，非漂移）**：`ARCHITECTURE.md:123-127` 已自述「任务描述写的 `core/registry.py` 实为 `ComponentRegistry`，业务契约实位在 `components/platform_operations/registry.py`」——本轮实测确认该更正成立（`core/registry.py` 52 行；业务 64 条在 `components/platform_operations/registry.py`）。

---

## 5. 结论与边界自证

**三条对账结论**
1. **module_catalog 标注**：`standard-product` 模块级 = `kind=standard_product_application` / `status=FACT` / `verification_level=STATIC`（`module_catalog.py:8` 逐字在位）；与 P1 件级 `VERIFIED_STATIC_BYTECODE` **层级不同、不互推**，对齐关系已写明。
2. **registry 口径**：**64 − 3 别名 − 2 R18 = 59 基础**，由 `UdcOperationRegistry.default()` **进程内实测复现**（脚本+输出已落盘，重跑逐字节一致）；与 TASK-GOAL「**59**」逐字 MATCH；「写法口径」（45/46 行、或 42 构造点、main 早期 47）与运行期 64 **不可混**，已登记机制。
3. **域边界**：registry 全部 `udc.*`（客开域），标品域登记数 **0**；标品域契约由标品 jar 接口定义承载（P1 已证 `cip-connector-api api/**` 20 接口）；两域以声明式 `RELATIONS` 相连（`customer-udc-application --calls--> standard-product`，**未闭合，非 FACT**）。

**边界自证（本轮）**
- 写入范围：仅 `core/facts/standard-product/**`（新增本文件 + `evidence/reconciliation/` 两件）。**未改写 P1 绑定件**（`standard-product-contracts.md` / `evidence/bytecode/**` sha256 复核 = P1 绑定值，未变）。
- 只读未写：`components/`、`core/tools/`、`adapters/`、`tests/`、`xiaozhua_cli.py`、`xiaozhua_host_bootstrap.py`、兄弟线领地 `core/facts/item-mgmt|connector|spi`。
- 零活体：无 HTTP、无 test2 连接、无测试应用创建；脚本为纯进程内静态读取。凭据 0 入件。

**UNVERIFIED / 未覆盖（不得当事实）**
- `module_catalog` 模块级 `STATIC` 是否覆盖全部三件 artifact 的完备性 → `UNVERIFIED`（本轮边界外）。
- `runtime --hosts-observes--> standard-product`（`module_catalog.py:21`）等 RELATIONS 的运行期事实性 → `UNVERIFIED`（无活体）。
- `ctp-user-api` 3.8.215 契约 → `UNVERIFIED`（本体与产物均缺，承 P1）。
- P3（`core/facts/INDEX.md` standard-product 行、`STATUS.md` 小节）→ 本 HANDOFF **不做**。
