# EVIDENCE-MODEL｜四层事实体系 + registry OperationStatus 映射归并（A4）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是 §四"四层事实体系"的展开，不新增定位）。
> 配套：`ARCHITECTURE.md`（第五节 Registry 实测口径）、`CAPABILITY-MODEL.md`（第四节 4 步 evidence.level）。
> 证据铁律：STATIC / VERIFIED / LIVE 为事实，GENERATED 仅假设；**GENERATED_HYPOTHESIS 永不进
> VERIFIED_RULE**；无在盘证据处标 **UNVERIFIED**，不编。本文只描述规范与归并映射，不改运行代码。

---

## 一、四层事实体系（正式规范，对齐 ROADMAP-v2 §四）

ROADMAP-v2 §四 原文：`STATIC（源码/javap）→ VERIFIED（测试/调用）→ LIVE（真实环境）→
GENERATED（仅假设）`；`GENERATED_HYPOTHESIS 永不进入 VERIFIED_RULE`。据此给四层各自：
**判定标准 / 可复现动作 / 反例（何物算伪造或臆测）**。

| 层 | 判定标准（达到才升层） | 可复现动作（谁、用什么重跑） | 反例（=臆测/伪造，须退回下层） |
|---|---|---|---|
| **STATIC** | 事实可追溯到源码或字节码（javap 反编译 / 离线 jar），不依赖运行态 | `javap -p -v <class>` 读字段/方法签名；源码定位行号；`docs/audit/artifacts/**` 留 jar sha256 | 凭类名/方法名"应该有"但无字节码支撑；把"文档说能"当能 |
| **VERIFIED** | STATIC 结论经**测试或调用**重跑复现（离线确定性测试，或本地调用断言） | `.venv/Scripts/python.exe -m pytest tests -q`（本轮 375 passed）；本地调 `build_deployment_plan()` 断言字段 | 测试未覆盖却写"已验证"；用别处数据顶替本契约断言 |
| **LIVE** | 事实在**真实环境**（test2 活体 / 网关 / RDS / 物理表）回读确证，附时间戳 + 对象标识 | test2 实测（如 2026-09-24 `udc_deploy_record` 15:52 行 `deploy_type=2 state=1`）；活体 pod 反编译；RDS 直连 SHOW TABLES | 拿 LIVE 样例当全量常量；把"某次构建成功"泛化成"总是成功" |
| **GENERATED** | 仅**假设/推断**（agent 生成、未见实证）；**永不进入 VERIFIED_RULE**，只能作待证项 | 无——须人工/活体复核后才可能升级 STATIC/LIVE；升级前始终标 GENERATED_HYPOTHESIS | 把假设写进能力契约当事实；把 GENERATED 升 VERIFIED_RULE（禁） |

**升级铁律**：只可"由低到高"升级且须留可复现动作；**GENERATED_HYPOTHESIS 永不直接进
VERIFIED_RULE**——这是 ROADMAP-v2 §四 明令，防止 agent 自证假设。

---

## 二、registry `OperationStatus` 映射归并（在盘实存状态 → 四层）

在盘枚举 = `components/platform_operations/models.py` `OperationStatus`（**8 值**，实测）：
`PASS / BLOCKED / UNVERIFIED / FAIL / DENIED / VERIFIED_STATIC_BYTECODE / OBSERVED / UNKNOWN`。
其中**契约登记态**（registry 实值，全 64 条分布：`VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 /
OBSERVED 2`，口径同 A1 第五节）与**执行期态**（layer 运行返回）分两类归并。

### 2.1 归并口径（registry 契约登记态 → 四层）

| 在盘 `OperationStatus` | 归并层 | 归并依据（在盘实值） |
|---|---|---|
| `VERIFIED_STATIC_BYTECODE` | **STATIC** | 契约证据 `evidence_level=VERIFIED_STATIC_BYTECODE`，溯源 javap/bytecode（`registry.py` 各契约 `evidence[]` 带 `class_sha256`+`javap` 路径） |
| `OBSERVED` | **LIVE** | 活体回读实证；全 64 条中 `udc.deploy.normal`（write=True）与 `udc.deploy.search_status`（write=False）为 OBSERVED，证据=test2 活体 `udc_deploy_record` 行 |
| `UNVERIFIED` | **GENERATED（待证）** | 登记为"已知但活体未确证"，禁止升 VERIFIED；全 64 条承载 = 0/64（`udc.deploy.search_status` registry 态已于提交 `210aa72` 升 OBSERVED，见上表 OBSERVED 行；其完整路由活体证据另列，不属本行状态分布） |
| `UNKNOWN` | **登记为未取证，不可归并任一实证层** | 契约已声明但证据未达 STATIC/LIVE；全 64 条 9 条 UNKNOWN（= 59 基础中 9 条，R18 两条均非 UNKNOWN） |

**归并结论**：
- `VERIFIED_STATIC_BYTECODE`(53) → STATIC；`OBSERVED`(2) → LIVE；`UNVERIFIED`(0) → GENERATED 待证（当前无契约承载）；
  `UNKNOWN`(9) → **不可归并**（未取证），单列"待补证"登记项。
- 59 基础口径下：`VERIFIED_STATIC_BYTECODE 50` + `UNKNOWN 9`（=59）；两条 R18（OBSERVED 2）
  另计——与全 64 分布 `53/9/2`（UNVERIFIED 0/64）自洽。

### 2.2 执行期状态（layer.py 运行返回，**不属于证据层，单列不并入四层**）

`layer.py` `execute()` 返回的以下状态是**执行结果/门控态**，不是"事实来源"，故**不归并**到四层，
按"执行态"独立登记（避免把"执行结果"误当"证据等级"）：

| 执行态 | 语义 | 归并处理 |
|---|---|---|
| `PASS` | GET-only 有效契约回读 + identity 匹配成功 | 运行时成功，非证据层 |
| `BLOCKED` | 缺执行上下文 / 连接 / 凭据解析失败 / 超时 | 门控/环境态 |
| `FAIL` | 业务未找到 / 回读空 / 校验不符 | 运行时失败态 |
| `DENIED` + `ErrorKind.POLICY_DENIED` | 写/非 GET 契约被写门拒（`layer.py:22`：`contract.write or method!='GET' or not effective` → POLICY_DENIED）；或 auth scope 外（`:24` AUTH_SCOPE_DENIED） | 写门纪律态，readonly 不破 |
| `UNVERIFIED`（执行期） | 响应 identity 无法确认（`layer.py` 末段：verified 但 unknowns） | 回读未确证，回登记态 |

> 说明：`UNVERIFIED` 同时出现于**登记态**（registry 契约缺活体证据）与**执行态**（回读 identity
> 未确证）两处，语义不同，归并时按上表分列，不混。

---

## 三、落地示例（逐条标层，引 A3 已核定的值）

### 3.1 deploy_plan 4 步各自证据等级（`deployment.py` `evidence[]` 实测）

`build_deployment_plan()` 每步 `evidence.level` 实测值（本轮脚本重跑 `build_deployment_plan()` 打印）：

| step | op | 关键事实 | 实测 `level` | 归并层 | `src`（在盘原值） |
|---|---|---|---|---|---|
| 1 | `udc.entity.create` | stereotype 值域 | `OBSERVED_LIVE` | LIVE | GET /udc/entity/primary/select-by-appid（**169 实体**） |
| 2 | `udc.entity.attribute.create` | dataType 值域 | `OBSERVED_LIVE` | LIVE | GET /udc/entity/attribute/select-all-by-entity-id（**51 属性**） |
| 3 | `udc.page.create` | （页面契约经 javap） | `VERIFIED_STATIC_BYTECODE` | STATIC | pod javap PageInfoController/PageTypeEnum（PageInfoController 必填链） |
| 4 | `udc.deploy.normal` | deploy 枚举/deployNormal 路径 | `VERIFIED_STATIC_BYTECODE` | STATIC | pod javap DeployController/DeployParamDto/DeployTypeEnum |
| —（R18 补充事实） | `udc.deploy.normal` | RELEASE=deploy_type 2、构建成功 state 1 | `OBSERVED_LIVE` | LIVE | udc_deploy_record 2026-09-24 15:52 行 |
| —（R18 补充事实） | `udc.deploy.normal` | 物理表落应用库非 udc_test2 | `OBSERVED_LIVE` | LIVE | RDS SHOW TABLES `yanshouda_m5654091886000795633` @ `9000000000000000001_test2` |

> 注：`OBSERVED_LIVE` 是 `deployment.py` 的 evidence level 字符串（活体观测），归并层=LIVE；
> 与 registry 契约登记态 `OBSERVED` 对应同一层。

### 3.2 UDC 建实体 169 实体 / 51 属性回读 = LIVE 实证

引 `docs/audit/udc-design-time-deploy-write-contracts.md`（LIVE 实证，2026-09-24 test2）：
- **建实体**：`POST /service/udc/entity` → `BOOT_0000`，实体 id `7670732978062038177`
  （YanshouDan/验收单，stereotype=bill）→ **LIVE**。
- **值域回读基准**：stereotype 值域=目标应用 **169 实体**回读统计；dataType 值域=bill 实体
  **51 属性**回读 → **LIVE**（非发明，随活体复核刷新）。
- **建属性 ×4 / 建页 ×2（LIST/DETAIL）/ RELEASE 构建 / 物理表落库**：全链 `OBSERVED_LIVE`（同文档 §一表）。

### 3.3 逐条标层小结

| 事实 | 层 | 备注 |
|---|---|---|
| stereotype / dataType 值域（169 / 51 回读） | LIVE | OBSERVED_LIVE，活体快照 |
| deploy 枚举 / deployNormal 路径 / 页面必填链 | STATIC | VERIFIED_STATIC_BYTECODE，javap |
| 构建成功 state=1 / 物理表落应用库 | LIVE | RDS + 活体 |
| `deploy.search_status` 完整路由 | **UNVERIFIED（GENERATED 待证）** | 类级前缀 LIVE 404，禁拼前缀执行 |
| `pushEnv` / `extraParamMap` 必填性 | **UNVERIFIED** | 未在活体确证（audit §六） |
| 前端页面是否随 RELEASE 构建生成 | **UNVERIFIED** | 未活体回读 |

---

## 四、边界与铁律自证

- **凭据 0 入仓**：本文只引证据等级与对象标识（实体 id、RDS 表名、jar sha256），不含任何凭据值
  （`deployment.py` 铁律 040402：凭据仅路径引用，值 0 入件）。
- **只描述规范与归并映射，不改运行代码**：第二节映射是"在盘状态 → 四层"的登记口径，
  未改 `registry.py` / `layer.py` / `models.py`。
- **不展开 02–12 模块**：示例仅用 01 UDC 的 deploy_plan（与 A3 同源）；其余模块证据归并后续批次。
- **不新增定位/阶段/验收**：四层定义、归并、示例均引自 ROADMAP-v2 §四 + 在盘
  `registry.py` / `layer.py` / `models.py` / `deployment.py` / `docs/audit/udc-design-time-deploy-write-contracts.md`。
- **UNVERIFIED 清单**：deploy.search_status 完整路由、pushEnv/extraParamMap 必填性、
  页面随构建生成、registry 9 条 UNKNOWN——全部标 UNVERIFIED，不编。

---

## 五、与 ROADMAP-v2 / 前件的对应

| 内容 | 来源 |
|---|---|
| 四层定义 + GENERATED 禁升 VERIFIED_RULE | ROADMAP-v2 §四 |
| OperationStatus 8 值枚举 | `components/platform_operations/models.py`（本轮实测） |
| 全 64 分布 53/9/2（UNVERIFIED 0/64）、59 基础 50/9 | `registry.py`（本轮脚本 `count_status.py` 实测，同 A1 第五节口径） |
| 写门 DENIED/POLICY_DENIED 行 | `layer.py:22`（本轮核） |
| 4 步 evidence.level 逐值 | `deployment.py`（本轮 `build_deployment_plan()` 重跑打印） |
| LIVE 全链实证（169/51/构建/物理表） | `docs/audit/udc-design-time-deploy-write-contracts.md` |
