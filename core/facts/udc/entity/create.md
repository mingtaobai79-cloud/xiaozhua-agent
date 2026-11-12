# udc.entity.create｜单据实体创建（B1 样板格）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`。九段式能力事实文档（TASK-GOAL 交付物 B 首件，
> `core/facts/udc/entity/create.md`），内容取自在盘 LIVE 实证（非臆造），逐段可溯源至 audit/八件套。
> 本件**只做 `udc.entity.create` 一格**（attribute/page/deploy 归 B2 起）；只写事实文档，不实现代码，
> 不改 components/；凭据 0 入仓（仅引对象标识/证据等级，不引 token/凭据值）。

---

## 1. Capability

**`udc.entity.create`** — 建单据实体。
- **类型**：CONFIG 型（agent 出**只读方案 data**，宿主执行写步；A3 §三/§五 口径）。
- **位置**：`components/platform_operations/deployment.py` `build_deployment_plan()` 的 `DeploymentStep`
  op=`udc.entity.create`（step1），经 `xiaozhua_host_bootstrap.deploy_plan()` 暴露给宿主。
- **语义**：在指定应用下创建一个 stereotype=`bill` 的单据实体（含完整单据族 features），
  返回实体 id，供后续建属性/建页/构建引用。

## 2. Version

- **Canonical = 5.3.517**（A5 核定；`registry.py` 106 处 5.3.517 artifact 锚点 + udc 全 jar 5.3.517，
  A1 第四节/A5 第三节在盘实测）。
- **差异机制**：版本差异走 **Version Adapter**（`adapter-5.3/5.4/…`，ROADMAP §一.1）；
  **Adapter 未建 → UNVERIFIED**（A5 §一 结论：本轮 Canonical=5.3.517，其他版本无在盘 UDC 证据）。
- **能力定义稳定**：以 Canonical 为准，Agent 不自行判版本分支（A5 铁律）。

## 3. Input

`deploy_plan(application_id, entity_name, attributes, caption, stereotype="bill")` 产出的 **step1 声明**
（A3 §三 真例 + audit §五 L60-64 宿主接口）：

```
op      = udc.entity.create
method  = POST
path    = /service/udc/entity
body    = {
    "appId":         <app_id_num>,      # application_id 转数字（_to_app_id）
    "name":          <entity_name>,
    "caption":       <caption or entity_name>,
    "stereotype":    "bill",            # 默认；出实测值域 {archive,standard,bill,archiveTree} 即进 unknowns
    "entityNature":  "MAIN",            # 缺 → UDC_ENTITY_0010
    "features":      "basic,approve,organization,billBasic,termination,suspend,nullify",  # 照已建 bill 实体（完整单据族）
    "multiplicity":  "ONE2MANY",
    "category":      "ENTITY",
    "parentEntityId":"0",
    "superior":      "0",
    "validate":      true
  }
```

> 值域 `features` 等形态照 test2 已建 bill 实体（OBSERVED_LIVE 回读统计，deployment.py step1 `note`）；
> 非发明，随活体复核刷新（audit §七 铁律 2）。

## 4. Required（必填链与缺省推断）

- **必填**：`appId`（数字）、`name`、`entityNature`、`stereotype` 缺失即拒
  （deployment.py step1 `note`："bill 单据族完整形态；entityNature/stereotype 缺会报 UDC_ENTITY_0010/BOOT_1001"，
  audit §二/§七）。
- **缺省推断（不臆造）**：`stereotype` 出实测值域 `{archive,standard,bill,archiveTree}` → 进 `unknowns`
  （audit §五 L67："stereotype 出值域进 unknowns"）；本件固定 `stereotype="bill"`（默认，在值域内，不触发 unknowns）。
- **证据**：`stereotype` 值域 = test2 目标应用 169 实体回读统计（OBSERVED_LIVE，deployment.py `evidence[]`）；
  推断项一律进 `unknowns` 交宿主确认，不静默臆造（A3 铁律）。

## 5. Execution

- **宿主调真实端点**：`POST /service/udc/entity`（网关 service 前缀 `{gateway_base}{prefix}/udc/entity`，
  deployment.py docstring："所有 path 走网关 service 前缀，调用方/宿主拼"，audit §七 铁律 040402）。
- **agent 侧不出写**：写门 `layer.py:22` `if contract.write or contract.method != "GET" or not contract.effective:`
  → `OperationStatus.DENIED` + `ErrorKind.POLICY_DENIED`（A4 §二/§三 已核，audit §一 L6-7、§五 L70）；
  agent 只出方案 data，**宿主授权执行**，readonly 纪律不破。
- **回读验证**：`GET /service/udc/entity/{id}` → `publishState`/`tableName`（deployment.py step1 `verify`）。

## 6. Side Effects

- **物理表随 RELEASE 构建落应用自身库**（`{app}_test2` / `{app}_uat`），**非 `udc_test2`**
  （audit §一 L18 实测 + §七 铁律 3："物理表落应用自身库，非 udc_test2——验证时连对库"）。
- test2 实证：RDS 直连 `9000000000000000001_test2`，表 `yanshouda_m5654091886000795633` 存在，
  DDL 带 4 业务列 + 全套单据系统列（中文注释）（audit §一 L18，OBSERVED_LIVE）。
- 建实体本身（设计态写）不直接落物理表；物理表由第 4 步 `udc.deploy.normal`（RELEASE 构建，应用级
  sandbox 部署）触发生成（audit §一"关键认知修正"+"构建走应用级 sandbox 部署"，A6 §三）。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| 缺 `entityNature` / `stereotype` | `UDC_ENTITY_0010` / `BOOT_1001` | deployment.py step1 `note`；audit §二 |
| 值域/枚举/数字编码 = 活体快照 | **非永久常量**，随活体复核刷新，不得硬编码进调用方 | audit §四/§七 铁律 2 |
| 写门对写契约恒 DENIED | agent 不出写；宿主授权执行，`layer.py` POLICY_DENIED | audit §一/§五；A4 §二 |
| 网关 service 前缀 | 完整可拼前缀 **UNVERIFIED**（不拼前缀当可用 URL，宿主拼 `{gateway_base}{prefix}`） | deployment.py docstring；A1 第五节 |

## 8. Evidence（LIVE 实证行，非臆造）

**建实体 LIVE 实证**（`docs/audit/udc-design-time-deploy-write-contracts.md` §一 L13，逐字）：

> `POST /service/udc/entity` → `BOOT_0000`，实体 id `7670732978062038177`
> （YanshouDan/验收单，stereotype=bill） | **OBSERVED_LIVE**

- 关联链（同 audit §一，供溯源）：建属性 ×4 SUCCESS、建页 ×2（LIST/DETAIL）`BOOT_0000`、
  RELEASE 构建 `deploy_type=2 state=1`（15:52 行）、物理表 `yanshouda_m5654091886000795633` 落
  `9000000000000000001_test2` —— 全链 2026-09-24 test2 活体实证，非声明。
- **证据等级 = OBSERVED_LIVE**（活体观测；A4 §三 归并到 LIVE 层，同 deployment.py `evidence[]` 原值）。

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `udc.entity.create` 契约登记（method/path/request/response） | **VERIFIED_STATIC** | `registry.py` `UdcOperationContract`，`OperationStatus.VERIFIED_STATIC_BYTECODE`（A1 §五/A4 §二 归并） |
| 建实体全链（POST→BOOT_0000→YanshouDan id→物理表） | **OBSERVED_LIVE** | audit §一 L13/L18（test2 2026-09-24 活体） |
| 写门 DENIED/POLICY_DENIED（agent 不出写） | **VERIFIED_STATIC** | `layer.py:22`（A4 已核） |
| 生成物（Java 工程/OSS 存储对象）是否已落 | **UNVERIFIED**（未直读） | audit §六："`schema_storage_key`/`sql_storage_key` 指向的存储对象 → 未直读" |
| 前端页面/列表是否随 RELEASE 构建生成 | **UNVERIFIED**（未活体回读） | audit §六："前端页面/列表是否随 RELEASE 构建生成 → 需活体回读页面面确认（本轮未探）" |

> **收口**：`udc.entity.create` 一格已按九段式落盘，逐段锚定在盘 LIVE/STATIC 实据；
> **未直读项（生成物落 OSS、前端随构建生成）如实标 UNVERIFIED，不臆造**。attribute/page/deploy 三格归 B2 起，
> 本件不扩散。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| Input/Required/verify 真值 | `components/platform_operations/deployment.py` step1（L143-151） |
| 契约登记 + status 实值 | `components/platform_operations/registry.py`（A1 §五 64 条口径） |
| 写门 DENIED/POLICY_DENIED | `components/platform_operations/layer.py:22`（A4 §二 已核） |
| LIVE 实证全链 + 物理表 | `docs/audit/udc-design-time-deploy-write-contracts.md` §一 L13/L18、§五 L60-70、§六、§七铁律 |
| CONFIG/写边界、Canonical 版本 | `docs/capability/CAPABILITY-MODEL.md` §三、`VERSION-COMPATIBILITY.md`（A5） |
