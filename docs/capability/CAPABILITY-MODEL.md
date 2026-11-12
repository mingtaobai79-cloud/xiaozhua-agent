# CAPABILITY-MODEL｜CONFIG / CODE 二分的正式定义 + 声明格式 schema（A3）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是 §三"能力模型"的展开，不新增定位）。
> 配套：`ARCHITECTURE.md`（两层架构图 + Registry 总线 + 架构约束）、`MODULE-INVENTORY.md`（模块清单）。
> 证据纪律：STATIC / VERIFIED / LIVE 为事实，GENERATED 仅假设；无在盘证据处标 **UNVERIFIED**，不编。
> 本文只描述模型与在盘真例，**不实现代码**；CODE 型目标态（Sandbox）由 A6 定义，此处只引用不定义。

---

## 一、CONFIG / CODE 二分（正式定义，对齐 ROADMAP-v2 §三）

ROADMAP-v2 §三 原文：**"CONFIG 能力：Agent 产结构化声明，平台执行；CODE 能力：配置表达不了的，
必须走 Sandbox → Compile → Test → Validate → Execute，禁止 Agent 直出 Java 直跑。"**

据此给二分定界（判据=该动作能否被**结构化声明**完整表达）：

| 型 | 定义 | 判据 | 在盘执行边界 |
|---|---|---|---|
| **CONFIG 型** | Agent 产出**结构化声明**（`{"capability":"udc.entity.create","input":{...}}`），由平台/宿主执行。典型=建实体/建字段/建页面/配权限/配路由/配菜单（ROADMAP §三 举例）。 | 动作语义可被"名字 + 输入 + 值域 + 前置 + 副作用"完整表达，无需可执行代码 | agent 只出**方案 data**，写动作经写门（`layer.py`）`DENIED/POLICY_DENIED`，宿主按 steps 调真实端点（`deployment.py` 铁律 040402） |
| **CODE 型** | 配置表达不了的（复杂规则 / 校验 / 转换 / 三方调用），产出**可执行代码单元**，必须经 **Sandbox → Compile → Test → Validate → Execute** 五段 | 含任意业务逻辑分支/第三方依赖/生成物，声明无法穷举其语义 | **现状未建**——Sandbox 由 `SANDBOX-CONTRACT.md`（A6）定义目标态；本文只引用，不定义、不实现 |

**二分的落地形态**：
- CONFIG 型 = 一条"声明"（本文第二节 schema），映射到 registry 的一个 `operation_id`（`UdcOperationContract`，
  见第三节真例），由宿主执行、agent 不回写。
- CODE 型 = 一个"入口契约"（本文第二节 schema），声明**编译单元 / 测试绑定 / sandbox 依赖**三要素，
  供 A6 的 Sandbox 流水线消费；本轮不建执行体。

> 版本前提（铁律）：**Canonical 版本 = 客户当前仓库**。CONFIG/CODE 的能力定义以 Canonical 为基准稳定，
> 版本差异走 Version Adapter（adapter-5.3/5.4/…），Agent 不自行判版本分支（`ARCHITECTURE.md` 第七节）。

---

## 二、声明格式 schema

### 2.1 CONFIG 型 capability 声明结构

六要素（对齐 HANDOFF 规格 + 在盘 `UdcOperationContract` 实字段，`components/platform_operations/models.py`）：

| 要素 | 字段名（在盘对齐） | 语义 | 证据要求 |
|---|---|---|---|
| capability 名 | `operation_id` | 唯一声明名，如 `udc.entity.create` | STATIC（源码登记） |
| input | `request_type` + `required_inputs` | 入参结构与必填项（如 `EntityDto` + `["appId","name","caption","stereotype"]`） | STATIC |
| 执行语义 | `method` + `path` | HTTP 动词 + 路由（写动作标 `write=True`，走写门） | STATIC（javap/bytecode） |
| 证据等级 | `status`（`OperationStatus`） | `VERIFIED_STATIC_BYTECODE / OBSERVED / UNVERIFIED / UNKNOWN`（与 A4 四层体系归并） | 随证据刷新 |
| 前置条件 | `required_inputs` 中缺省即拒的项 + `enums` 值域 | 如建实体缺 `entityNature`/`stereotype` 报 `UDC_ENTITY_0010`/`BOOT_1001` | LIVE（在盘 `deployment.py` step note） |
| 副作用 | `evidence`（`level`+`src`）+ `verification_rules`（verify 断言） | 写动作落物理表/RDS 记录，须回读确证 | LIVE |

> 在盘样例（`registry.py` R1 段，如实）：
> `("udc.entity.create","POST","/udc/entity","com.seeyon.udc.common.dto.EntityDto","SingleResponse<Long>",True,True,())`
> → 映射到 `UdcOperationContract(operation_id, method, path, request_type, response_type, status, write, evidence, required_inputs, verification_rules)`。

### 2.2 CODE 型 capability 入口契约字段

三要素（HANDOFF 规格；目标态执行体归 A6，此处只声明契约面）：

| 要素 | 字段 | 语义 | 现状 |
|---|---|---|---|
| 编译单元 | `compile_unit` | 可编译的代码单元标识（如目标 Java 模块 / 包路径） | UNVERIFIED（Sandbox 未建） |
| 测试绑定 | `test_binding` | 该单元关联的 Test（Sandbox 流水线 Compile→Test 段消费） | UNVERIFIED |
| sandbox 依赖 | `sandbox_dep` | 运行时依赖（JDK/三方 jar/pipeline 配置），Sandbox→Compile 段前置 | UNVERIFIED |

> 五段流水线（Sandbox → Compile → Test → Validate → Execute）为**目标态定义**，落在
> `SANDBOX-CONTRACT.md`（A6）；本文仅声明"CODE 型入口须携带上述三要素"，不定义执行体、不建实现。

---

## 三、CONFIG 真例：deploy_plan 4 步逐条映射

在盘真例 = `build_deployment_plan()`（`components/platform_operations/deployment.py:115`，
HANDOFF 引 `L115`）产出的 4 个 `DeploymentStep`，全部是 **CONFIG 型声明**——agent 出方案 data、
宿主执行、agent 不出写。证据文件 `docs/audit/udc-design-time-deploy-write-contracts.md`（LIVE 实证）。

| # | capability 名（`op`） | input（`body`，在盘原值节选） | 执行语义（method+path） | 证据等级（step `evidence`/audit） | 前置条件（step `note`） | 副作用（`verify` 断言） |
|---|---|---|---|---|---|---|
| 1 | `udc.entity.create` | `{appId, name, caption, stereotype:"bill", entityNature:"MAIN", features:"basic,approve,...", multiplicity:"ONE2MANY", category:"ENTITY", ...}` | POST `/service/udc/entity` | bill 族形态=OBSERVED_LIVE（169 实体回读）；缺 `entityNature`/`stereotype`→`UDC_ENTITY_0010`/`BOOT_1001` | 值域 `stereotype∈{archive,standard,bill,archiveTree}` | GET `/service/udc/entity/{id}`→publishState/tableName；物理表落应用库 |
| 2 | `udc.entity.attribute.create` | `[{name,caption,dataType}]`（dataType 缺省按名推断并进 `unknowns`，不臆造） | POST `/service/udc/entity/attribute` | `dataType` 值域=OBSERVED_LIVE（51 属性回读）；dataType 必填否则 `BOOT_1001` | 需带 `appId`+`entityId`；平台自动补单据族系统属性 | GET `.../attribute/select-all-by-entity-id/{entityId}` |
| 3 | `udc.page.create` | `[{appId,caption:"…列表",pageType:"LIST",masterEntityIds,pageUrl,curTerminalType:"PC",pageItems:[{actionType:"NORMAL",...}]}, {…DETAIL…}]` | POST `/service/udc/page-info/base-info/create` | `actionType∈{NORMAL,INSERT,UPDATE,DELETE}`=VERIFIED_STATIC_BYTECODE（PageTypeEnum javap）；缺 `pageUrl`/`curTerminalType`→`BOOT_1001`/`BOOT_1000` | 必填链 appId/pageType/masterEntityIds/pageUrl/curTerminalType/pageItems | GET `/service/udc/page-info/select-by-appId/{appId}` 回读 caption+relationGroupId |
| 4 | `udc.deploy.normal` | `{"deployDto":{appId, deployType:"RELEASE", projectType:"ALL", terminalType:"ALL"}}` | POST `/service/udc/runtime/deploy-normal` | RELEASE=`deploy_type=2`/TEST=`0`；成功 `state=1`/失败 `2`=OBSERVED_LIVE（`udc_deploy_record`）；枚举=VERIFIED_STATIC_BYTECODE（pod javap） | 触发 sandbox 流水线（`UdcAppDeployService`）；构建即部署（非实体级 publish）；硬门=一致性检测（未过整单失败） | RDS `udc_test2.udc_deploy_record` 最新行 + 应用库 SHOW TABLES |

**逐条断言（CONFIG 型成立的证据）**：
- 4 步全为 `DeploymentStep(op, method, path, body, verify, note)` 结构化声明，**无生成/执行任意代码**，
  符合 CONFIG 型"声明即可表达语义"判据。
- agent 侧 `deploy_plan` 只 `to_dict()` 返回方案 data；`udc.deploy.normal` 在写门仍 `DENIED/POLICY_DENIED`
  （`layer.py`），readonly 纪律不破——**这是 CONFIG 型"平台执行、agent 不出写"的在盘实证**。
- 每步 `evidence.level` 明确（OBSERVED_LIVE / VERIFIED_STATIC_BYTECODE），`unknowns` 收集未证实项
  （如 dataType 由名推断）——**证据纪律落到声明字段内，不臆造**。

> 对照：第 4 步的 `UdcAppDeployService` 触发的是**平台既有 sandbox 流水线**（构建部署），
> 属于平台侧执行体，不是本 v2 待建的"CODE 型 Sandbox 契约"（A6）——两者勿混（依据 audit 文档 §一"关键认知修正"）。

---

## 四、边界与未验证项

- **本文只描述模型，不实现代码**：第二节 schema 是"声明契约面"的字段定义，不产出可执行配置/代码。
- **CODE 型现状=未建**：`compile_unit/test_binding/sandbox_dep` 三要素的**执行体**（Sandbox→…→Execute）
  由 `SANDBOX-CONTRACT.md`（A6）定义目标态；此处三要素均标 UNVERIFIED，不定义目标态细节。
- **不展开 02–12 模块**：本文只用 01 UDC 的 deploy_plan 作 CONFIG 真例；其余模块的 CONFIG/CODE 分型
  归 `MODULE-INVENTORY.md`（A2）与后续批次，不在本文新增。
- **不新增定位/阶段/验收**：CONFIG/CODE 定义、schema、真例均严格引自 ROADMAP-v2 §三 + 在盘
  `deployment.py` / `models.py` / `registry.py` / audit 文档；无自造口径。
- **UNVERIFIED 清单**：CODE 型三要素（A6）、deploy_plan 第 4 步 `pushEnv`/`extraParamMap` 必填性、
  网关 service 前缀（`deployment.py` 铁律 040402，调用方拼，registry 不拼前缀当可用 URL）。

---

## 五、与 ROADMAP-v2 / 前件的对应

| 内容 | 来源 |
|---|---|
| CONFIG/CODE 二分判据与举例 | ROADMAP-v2 §三 |
| 声明 schema 实字段（`operation_id/request_type/status/evidence/...`） | `components/platform_operations/models.py`（`UdcOperationContract`） |
| CONFIG 真例 4 步 | `components/platform_operations/deployment.py:115` `build_deployment_plan()` + `docs/audit/udc-design-time-deploy-write-contracts.md` |
| 写门 DENIED/POLICY_DENIED | `components/platform_operations/layer.py`（`ARCHITECTURE.md` 第五节） |
| Canonical 版本 / 证据纪律 | ROADMAP-v2 §一/§四；`ARCHITECTURE.md` 第七节 |
