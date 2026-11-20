# 专题 1：应用与元数据体系

> 状态：**研究中（第一轮）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 数据源：`docs/audit/reference/udc-platform-5.3.517.tar.gz`
> 统计脚本：`scripts/research/stats_registry.py`
> 最近更新：2026-11-17

---

## 1. 研究目标

搞清平台有哪些元数据对象、它们怎么存、怎么改、谁参与生成、谁参与运行时。

---

## 2. 元数据对象全景（已核实）

### 2.1 六个 stereotype（版型）

来源：`udc-biz-5.3.517/resources/stereotype/*/config.json`（6 份，全部解析成功）

| name | caption | order | dataFlowEnabled | necessaryFeatures | availableFeatures |
|---|---|---|---|---|---|
| `basicData` | 基础资料 | 0 | **false** | `basic` | `secretLevel` |
| `form` | 表单 | 0 | true | `basic`, `formBasic` | `secretLevel` |
| `standard` | 标准 | 0 | true | `basic` | `secretLevel` |
| `bill` | 单据 | 1 | true | `basic`, `approve`, `organization`, `billBasic`, `termination`, `suspend`, `nullify` | `secretLevel` |
| `archive` | 平铺档案 | 2 | true | `basic`, `archiveBasic`, `approve`, `archiveTiled` | `secretLevel` |
| `archiveTree` | 树形档案 | 3 | true | `basic`, `archiveBasic`, `approve`, `treeEntity` | `secretLevel` |

**★ 新发现 1：`dataFlowEnabled`（生单规则开关）**

- `basicData` 是 **false**，其余 5 种是 **true**
- ⇒ **基础资料实体不支持数据流/生单规则**，这是 stereotype 级的硬约束
- 证据等级：`STATIC_RULE`（config.json 逐字）
- 待证：运行时是否真的按此开关拦截

**★ 新发现 2：`availableFeatures` 只有 `secretLevel`**

- 六种 stereotype 的可选特性都只有 `secretLevel` 一个
- ⇒ 其余 17 个特性都是**通过 necessaryFeatures 强制绑定**，不是用户可选
- 证据等级：`STATIC_RULE`
- 待证：`availableFeatures` 是否还有运行时追加（如 UI 上的额外勾选）

### 2.2 十八个 feature（特性）

来源：`resources/feature/*/config.json`
**修正：v4 写的「26 份」有误。实测 22 个 config.json，其中 18 个是特性定义、4 个是模板声明。**

| id | name | caption | stereotypeBind | order | attributeSet | 互斥 |
|---|---|---|---|---|---|---|
| 0 | `basic` | 基础 | false | 0 | `basic` | — |
| 2 | `billBasic` | 单据基本 | **true** | 2 | `billBasic` | — |
| 3 | `archiveBasic` | 档案基本 | **true** | 3 | `archiveBasic` | — |
| 4 | `disable` | 禁用 | false | 4 | `disable` | — |
| 5 | `validityPeriod` | 有效期 | false | 5 | `validityPeriod` | — |
| 6 | `attributeScalability` | 属性扩展 | false | 6 | （空） | — |
| 7 | `attributeScalabilityGlobal` | 全局属性扩展 | false | 7 | （空） | — |
| 8 | `fulltextSearch` | 全文检索 | false | 8 | `fulltextSearch` | — |
| 9 | `treeEntity` | 树形实体 | false | 9 | `treeEntity` | — |
| 12 | `approve` | 审批 | false | 12 | `approve` | — |
| 13 | `organization` | 组织 | false | 13 | `organization` | — |
| 13 | `archiveTiled` | 平铺档案 | **true** | 13 | `archiveTiled` | **互斥 `treeEntity`** |
| 14 | `sendDown` | 下发 | false | 14 | `sendDown` | — |
| 20 | `nullify` | 作废 | false | 20 | `nullify` | — |
| 21 | `termination` | 终止 | false | 21 | `termination` | — |
| 22 | `suspend` | 挂起 | false | 22 | `suspend` | — |
| 50 | `formBasic` | 表单基本 | **true** | 50 | `formBasic` | — |
| 51 | `secretLevel` | 密级等级 | false | 60 | `secretLevel` | — |

**★ 新发现 3：`stereotypeBind` 语义**

- `true` 的 4 个：`billBasic` / `archiveBasic` / `archiveTiled` / `formBasic`
- ⇒ 这 4 个特性**与版型强绑定**，只能由对应 stereotype 携带，不能单独勾选
- 其余 14 个是**独立特性**，可自由组合
- 证据等级：`STATIC_RULE`

**★ 新发现 4：`archiveTiled` 与 `treeEntity` 互斥**

```json
"mutuallyExclusiveFeatures": ["treeEntity"]
```
⇒ 平铺档案与树形档案不能共存。这是唯一的互斥声明。
证据等级：`STATIC_RULE`

**⚠️ 数据异常：`organization` 与 `archiveTiled` 的 id 都是 13。**
这可能是平台数据问题，也可能是两个不同的 id 命名空间。
**不得推断**，标记 `UNVERIFIED`，待查是否有 id 冲突处理。

**★ 新发现 5：所有 feature 的 `attributes` 和 `behaviors` 都是空数组**

```json
"attributes": [], "behaviors": []
```
⇒ 特性本身**不直接声明字段**，字段通过 `attributeSet` 引用。
⇒ **特性 → 字段的映射是「特性名 → attributeSet 名」的间接引用**，不是内联。
证据等级：`STATIC_RULE`

### 2.3 十八个字段集与 122 个预置字段

来源：`resources/presetData/attributeSet.json`（18 项，全部解析）

| 字段集 | caption | 字段数 |
|---|---|---|
| `basic` | 系统字段集 | 6 |
| `creator` | 创建人字段集 | 4 |
| `updater` | 更新人字段集 | 1 |
| `archiveBasic` | 档案基本字段集 | **36** |
| `archiveTiled` | 平铺档案字段集 | 0 |
| `billBasic` | 单据基本字段集 | **13** |
| `suspend` | 挂起字段集 | 7 |
| `termination` | 终止字段集 | 7 |
| `nullify` | 作废字段集 | 7 |
| `disableFeature` | 禁用字段集 | 1 |
| `fulltextSearch` | 全文检索字段集 | 0 |
| `treeEntity` | 树形实体字段集 | 5 |
| `validityPeriod` | 有效期字段集 | 0 |
| `approve` | 审批字段集 | 0 |
| `organization` | 组织字段集 | 0 |
| `sendDown` | 下发字段集 | 0 |
| `formBasic` | 表单基本字段集 | **33** |
| `secretLevel` | 密级等级 | 2 |

**总计 122 个预置字段。**

**★ 新发现 6：`basic` 字段集 = 6 个系统字段（逐字）**

| 字段 | dataType | system | hidden | edit | caption |
|---|---|---|---|---|---|
| `id` | BIGINTEGER | true | true | false | ID |
| `tenantId` | BIGINTEGER | true | true | false | 租户ID |
| `createTime` | DATETIME | true | — | false | 创建时间 |
| `updateTime` | DATETIME | true | — | false | 更新时间 |
| `version` | INTEGER | true | true | false | 版本号 |
| `draft` | BOOLEAN | true | true | false | 是否草稿 |

**⇒ 重要推论（待证）：**
- `version` INTEGER → **乐观锁版本号**，对应 DAO 的
  `updateColumnsIgnoreVersion` / `versionNoUpdateIgnoreVersion` / `versionNoUpdateBatchIgnoreVersion`
- `draft` BOOLEAN → **草稿标志**，单据"保存草稿 vs 提交"的字段级基础
- `tenantId` → **多租户隔离的字段级基础**
- 证据等级：`STATIC_RULE`（字段存在）→ 语义为 `UNVERIFIED`（需实测）

**★ 新发现 7：字段类型分布（122 个）**

| dataType | 数量 |
|---|---|
| `ENTITY` | **44** |
| `DATETIME` | 28 |
| `STRING` | 27 |
| `ENUM` | 9 |
| `BOOLEAN` | 4 |
| `BIGINTEGER` | 3 |
| `INTEGER` | 3 |
| `Serial` | 2 |
| `MULTILINESTRING` | 1 |
| `CTPENUM` | 1 |

**⇒ `ENTITY` 占 36%（44/122）**，说明**关联字段是平台字段体系的主体**。
这对专题 3（主子表、关联写入）是关键前提。

**★ 新发现 8：`billBasic` 13 个字段揭示了「单据与普通实体的区别」**

| 字段 | dataType | caption |
|---|---|---|
| `caseSendTime` | DATETIME | 发起时间 |
| `caseSender` | ENTITY | 发起人 |
| `caseSenderInstitution` | ENTITY | 发起机构 |
| `caseSenderDepartment` | ENTITY | 发起部门 |
| `caseSenderPost` | ENTITY | 发起岗位 |
| `billCode` | **Serial** | 单据编号 |
| `billDate` | DATETIME | 单据日期 |
| `applicant` | ENTITY | 申请人 |
| `deductionInfo` | MULTILINESTRING | 扣减规则信息 |
| `templateId` | ENTITY | **流程模板** |
| `caseId` | ENTITY | **流程实例** |
| `caseTitle` | STRING | 流程标题 |
| `caseFinishTime` | DATETIME | 流程结束时间 |

**⇒ 单据的本质区别（字段级证据）：**
1. **与 BPM 流程强绑定**：`templateId`（流程模板）+ `caseId`（流程实例）+ `caseTitle` + `caseSendTime` + `caseFinishTime`
2. **有流水号**：`billCode` 是 `Serial` 类型
3. **有发起人五元组**：`caseSender` + 机构 + 部门 + 岗位 + 时间
4. **有扣减规则**：`deductionInfo`（MULTILINESTRING）

**⇒ 推论（待证）：单据不能像普通实体那样直接 `Dao.create` 就完事，
必须有 `caseId` 才能走流转。但「如何获得 caseId」属于专题 3。**

**★ 新发现 9：挂起/终止/作废是「三套对称状态」**

三组各 7 个字段，结构完全对称：

| 组 | 原状态字段 | 撤销字段 |
|---|---|---|
| `suspend` | `suspenderId` / `suspendTime` / `suspendReason` / `suspendStatusType` | `cancelSuspenderId` / `cancelSuspendTime` / `cancelSuspendReason` |
| `termination` | `terminatorId` / `terminateTime` / `terminateReason` / `terminateStatusType` | `cancelTerminatorId` / `cancelTerminateTime` / `cancelTerminateReason` |
| `nullify` | `nullifyId` / `nullifyTime` / `nullifyReason` / `nullifyStatusType` | `cancelNullifyId` / `cancelNullifyTime` / `cancelNullifyReason` |

**⇒ 单据状态是「可撤销的叠加态」**，不是单一状态字段。
**⇒ `*StatusType` 是 ENUM，记录「操作时的单据状态」**（快照，不是当前状态）。
证据等级：`STATIC_RULE`

**★ 新发现 10：`treeEntity` 5 个字段 = 路径式树**

| 字段 | dataType | caption |
|---|---|---|
| `treePath` | STRING | ID路径 |
| `treeParentId` | BIGINTEGER | 上级 |
| `isLeaf` | BOOLEAN | 是否末级 |
| `treeLevel` | INTEGER | 级次 |
| `treeCaptionPath` | STRING | 显示名称路径 |

**⇒ 树形是「物化路径（Materialized Path）」实现**，不是递归查询。
**⇒ 这与 `EntityFileTemplate#getEntityReferAgg4CodeDto` 的聚合机制可能相关，待证。**

### 2.4 特性如何影响代码生成（★ 本轮最重要发现）

来源：`resources/feature/{disable,tree_entity,attribute_scalability,attribute_scalability_global}/template/config.json`

**这 4 个文件是「特性 → 生成类」的声明式映射。**

#### 2.4.1 classType 枚举（7 种，从配置实测得出）

| classType | className 模式 | 层 | 出现次数 |
|---|---|---|---|
| `WEB_CONTROLLER` | `$Class{entityName}Controller` | Web 层 | 1 |
| `FACADE_APP_SERVICE` | `$Class{entityName}AppService` | **AppService 接口** | 1 |
| `BIZ_APP_SERVICE_IMPL` | `$Class{entityName}AppServiceImpl` | **AppService 实现** | 1 |
| `BIZ_DOMAIN_SERVICE` | `$Class{entityName}Service` | **Service 业务域** | 10 |
| `BIZ_DOMAIN_DAO` | `$Class{entityName}Dao` | **DAO** | 3 |
| `BIZ_DOMAIN_ENTITY` | `$Class{entityName}ExtensionEntity` | Entity（扩展） | 3 |
| `FACADE_DTO` | `$Class{entityName}Dto` | DTO | 6 |

**⇒ 这直接回答了「平台生成的三类 service / appservice / dao 层怎么命名」：**

```
{EntityName}Controller        WEB_CONTROLLER
{EntityName}AppService        FACADE_APP_SERVICE      ← 对外接口
{EntityName}AppServiceImpl    BIZ_APP_SERVICE_IMPL    ← 对外实现
{EntityName}Service           BIZ_DOMAIN_SERVICE      ← 业务域服务
{EntityName}Dao               BIZ_DOMAIN_DAO          ← 数据访问
{EntityName}Entity            BIZ_DOMAIN_ENTITY
{EntityName}Dto               FACADE_DTO
```

**证据等级：** `STATIC_RULE`（配置逐字）
**⚠️ 边界：** 这是**特性扩展类**的声明；主生成物的命名需从 `_codegen_templates.json` 的 `2.7/entity` 模板名和 `EntityFileTemplate` 的 OutPath 交叉确认。**两者不能混为一谈。**

**⚠️ 未找到 `BaseService` 对应的 classType。**
模板清单有 `baseservice.java.ftl`，但 classType 里没有 `BASE_SERVICE`。
**⇒ 推论（待证）：`baseservice.java.ftl` 生成的就是 `{EntityName}Service`（BIZ_DOMAIN_SERVICE）。**
**不得作为结论，标记 `UNVERIFIED`。**

#### 2.4.2 classMode 枚举（2 种）

| classMode | 含义 | 出现次数 |
|---|---|---|
| `CLASS_NEW` | **新建一个类** | 12 |
| `CLASS_SAME` | **在已有类上追加** | 13 |

**⇒ `CLASS_SAME` 是「特性给主生成类追加方法/字段」的机制。**
**⇒ 这解释了为什么 `attribute_scalability` 会两次声明 `$Class{entityName}Service` + `CLASS_SAME`。**

#### 2.4.3 methodType 与 joinPoints（★ 代码织入机制）

来源：`feature/tree_entity/template/config.json` 的 methods 定义

| methodType | 含义 | 示例 |
|---|---|---|
| `APPEND` | **新增一个方法** | `selectImmediateChildren(@NotNull Long id)` |
| `JOIN` | **在已有方法的切点插入代码** | 见下 |

**实测到的 joinPointName：**

| joinPointName | 归属方法 | 用途 |
|---|---|---|
| `preCreateBatch` | `createBatch` | 批量创建**前置** |
| `middle` | `createBatch` | 批量创建**中间** |
| `preUpdateBatch` | `updateBatch` | 批量更新**前置** |
| `afterUpdate` | `updateBatch` | 更新**后置** |
| `after` | `deleteByIds` | 删除**后置** |

**实测到的真实方法签名（Freemarker 语法）：**

```
selectImmediateChildren(@NotNull Long id)
selectAllChildren(@NotNull Long id)
selectParent(@NotNull Long id)
createBatch(List<${entityName?cap_first}Dto> ${uncapEntityName}DtoList)
updateBatch(List<${entityName?cap_first}Dto> ${uncapEntityName}DtoList)
deleteByIds(List<Long> ids)
```

**⇒ 这是本轮最重要的发现：**

1. **平台生成代码时，特性通过「切点织入」修改已生成的方法**，而不是重新生成整个类
2. **切点位置是固定的枚举**（`preCreateBatch` / `middle` / `preUpdateBatch` / `afterUpdate` / `after`）
3. **这直接给出「生成代码 vs 手写代码边界」的答案**：
   - 主生成类里的方法体由模板生成
   - 特性在固定切点插入额外逻辑
   - 开发者的自定义逻辑应写在哪一层，需要看有没有对应切点
4. **`createBatch` 的签名是 `List<XxxDto>`**，不是单条
5. **`deleteByIds` 参数是 `List<Long>`**

**证据等级：** `STATIC_RULE`（配置逐字，含真实 Java 代码片段）
**待证：** 这些切点是否也适用于非特性场景（即开发者能否自己用）

#### 2.4.4 特性声明的完整类清单

| 特性 | 声明的类 | classMode |
|---|---|---|
| `attribute_scalability` | `{E}ExtensionService` / `{E}ExtensionDao` / `{E}ExtensionEntity` / `{E}ExtensionDto` | 全部 `CLASS_NEW` |
| | `{E}Service`（×2）/ `{E}Dto` | `CLASS_SAME` |
| `attribute_scalability_global` | `ExtensionGlobalService` / `ExtensionGlobalDao` / `ExtensionGlobalEntity` / `ExtensionGlobalDto` | 全部 `CLASS_NEW` |
| | `{E}Service`（×2）/ `{E}Dto` | `CLASS_SAME` |
| `disable` | 与 `attribute_scalability` **完全相同**（7 项） | — |
| `tree_entity` | `{E}Controller` / `{E}AppService` / `{E}AppServiceImpl` / `{E}Service` | 全部 `CLASS_SAME`，tplName 全空 |

**⚠️ 异常发现：`disable` 的 7 项与 `attribute_scalability` 完全相同**（className、classType、tplName 都一致）。
可能是配置复制，也可能 `disable` 依赖 `attributeScalability`。
**标记 `UNVERIFIED`，不得推断。**

**⚠️ `tree_entity` 的 tplName 全为空**，说明它复用主模板 + 追加 imports/fields/methods。

### 2.5 平台级服务依赖（17 个）

来源：`resources/presetData/dependencyGraph.json`

**★ 修正：该文件不是「元数据对象依赖图」，而是「应用对平台服务的依赖清单」。**

```json
{"copVersion": "test", "dependList": [17 项]}
```

| name | caption | type | version |
|---|---|---|---|
| `organization` | 组织机构 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `ctp-user` | 用户中心 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `bpm` | BPM引擎 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `ctp-affair` | 事项中心 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `ctp-message` | 消息中心 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `cip-connector` | 连接器 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `cdp-data` | 数据中台 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `portal` | 门户 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `app-common` | 基础设置 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `cip-capability` | 基础能力接入 | SERVICE | 3.12.0-TEST-SNAPSHOT |
| `udc` | 低代码平台 | SERVICE | 3.12.0-DEV-SNAPSHOT |
| `FRONTEND` | 前端控件 | FRONTEND | beta |
| `starter` | starter组件 | STARTER | 3.12.0-TEST-SNAPSHOT |
| `boot-extend` | 平台拓展组件 | STARTER | 3.12.0-TEST-SNAPSHOT |
| `udc-starters` | udc运行态组件 | STARTER | 3.12.0-TEST-SNAPSHOT |
| `boot-starter-file` | 文件组件 | STARTER | 3.12.0-TEST-SNAPSHOT |
| `boot-starter-opinion` | 意见组件 | STARTER | 3.12.0-TEST-SNAPSHOT |

**⇒ 价值：这是「UDC 应用可依赖哪些平台服务」的权威清单。**
对专题 5（接口调用）和专题 6（基础组件）直接有用。

**⚠️ `copVersion: "test"`** 说明这份配置来自测试环境快照，生产可能有差异。

### 2.7 单据状态机（★ 决定单据流转的权威定义）

来源：`presetData/billEnum.json`（2 个枚举）

**`billStatus`（单据状态，8 个状态）**

| code | name | caption |
|---|---|---|
| 0 | `DRAFT` | 草稿 |
| 1 | `TO_BE_SUBMITTED` | 待提交 |
| 2 | `PENDING_REVIEW` | 提交中 |
| 3 | `COME_INTO_FORCE` | 已生效 |
| 4 | `TERMINATED` | 已终止 |
| 5 | `NULLIFIED` | 已作废 |
| 6 | `SUSPENDED` | 已挂起 |
| 7 | `FAILED` | 不通过 |

**`billSendState`（发送状态，2 个）**

| code | name | caption |
|---|---|---|
| 0 | `SEND_SUCCESS` | 发送成功 |
| 1 | `SENDING` | 发送中 |

**⇒ 关键推论：**
1. **8 个状态与 3 个操作特性一一对应**：
   - `SUSPENDED`(6) ← `suspend` 特性
   - `TERMINATED`(4) ← `termination` 特性
   - `NULLIFIED`(5) ← `nullify` 特性
   - `DRAFT`(0) / `TO_BE_SUBMITTED`(1) ← `draft` 字段
   - `PENDING_REVIEW`(2) / `COME_INTO_FORCE`(3) / `FAILED`(7) ← `approve` 特性 + BPM
2. **`billStatus` 与 `billSendState` 是两个独立维度**（业务状态 vs 发送状态）
3. **单据流转是「状态机 + BPM 流程」双轨**：`caseId` 管流程，`billStatus` 管业务状态

**证据等级：** `STATIC_RULE`（枚举定义逐字）
**待证：** 状态迁移的合法路径（谁能从 0 到 1？谁触发 2→3？）→ 专题 3

**对照：`formEnum.json` / `archiveEnum.json` 有同样的 8 状态结构**
（`formStatus` / `archiveStatus`），说明**表单与档案也走同一状态机**。

### 2.8 实体事件机制（★ 事务边界的直接证据）

来源：`presetData/event/defaultevent.json`（9 个事件）

| 事件名 | actionType | triggerType | caption |
|---|---|---|---|
| `BeforeCreateEvent` | CREATE | **BEFORE** | 新增事件(操作前) |
| `AfterCreateEvent` | CREATE | **AFTER** | 新增事件(操作后) |
| `TransactionSuccessCreateEvent` | CREATE | **TRANSACTION_SUCCESS** | 新增事件(操作成功) |
| `BeforeUpdateEvent` | UPDATE | BEFORE | 更新事件(操作前) |
| `AfterUpdateEvent` | UPDATE | AFTER | 更新事件(操作后) |
| `TransactionSuccessUpdateEvent` | UPDATE | TRANSACTION_SUCCESS | 更新事件(操作成功) |
| `BeforeDeleteEvent` | DELETE | BEFORE | 删除事件(操作前) |
| `AfterDeleteEvent` | DELETE | AFTER | 删除事件(操作后) |
| `TransactionSuccessDeleteEvent` | DELETE | TRANSACTION_SUCCESS | 删除事件(操作成功) |

**⇒ 这是本轮最重要的发现之一：**

1. **3 种动作 × 3 种触发时机 = 9 个标准事件**
2. **`TRANSACTION_SUCCESS` 的存在直接证明平台有事务边界概念**：
   - `BEFORE` / `AFTER` 在方法执行前后
   - `TRANSACTION_SUCCESS` 在**事务提交成功后**才触发
3. **⇒ 事务边界推论（待证）：**
   - 平台至少区分「方法级」和「事务级」两个粒度
   - `TransactionSuccess*Event` 适合做「事务成功后才有副作用」的逻辑（发消息、调外部接口）
   - 这与用户复盘文档里「状态由真正干活的方法回写，监听器只兜底」的经验吻合

**⚠️ 但不得直接断言「一次 create 是单事务」。**
`TRANSACTION_SUCCESS` 只证明「有事务提交后的回调」，不证明「事务范围多大」。
**标记 `UNVERIFIED`，需实测。**

**证据等级：** `STATIC_RULE`（事件定义）
**待证：** 事件的注册方式、执行线程、异常是否回滚事务 → 专题 3 / 专题 4

**关联：** `resources/microflow/entityEventWhiteList.json` 约束哪些事件可被微流程使用。

### 2.9 属性扩展机制（30 个预置扩展列）

来源：`presetData/scalability.json` + `scalabilityGlobal.json`

**应用级扩展（`SystemPresetCustomExpansionPlan`）**

| prefix | 数量 | dataType | caption | 属性 |
|---|---|---|---|---|
| `extVarchar` | 10 | STRING | 扩展字符串字段 | `{"length":50}` |
| `extDate` | 10 | DATE | 扩展时间字段 | `{}` |
| `extNumber` | 10 | BIGINTEGER | 扩展数字字段 | `{"length":20}` |

**⇒ 每个实体预置 30 个扩展列**（10 字符串 + 10 日期 + 10 数字）

**全局扩展（`SystemPresetGlobalExpansionPlan`）**
- prefix 为 `extGlobalVarchar` / `extGlobalDate` / `extGlobalNumber`
- 结构相同，用于跨应用共享

**⇒ 关键推论：**
1. **「属性扩展」不是动态建列，而是预置 30 个通用列 + 映射**
2. 这解释了 `attribute_scalability` 特性为什么要生成 `{E}ExtensionService` / `{E}ExtensionDao` / `{E}ExtensionEntity` / `{E}ExtensionDto` 四个类
3. **⇒ 扩展字段的读写走独立的 Extension 层，不污染主实体**

**证据等级：** `STATIC_RULE`
**待证：** 30 列的实际表结构、映射方式 → 专题 3

### 2.10 字段权限矩阵（58 个字段的可编辑性）

来源：`presetData/attribute/presetAttributeCapacity.json`（58 项）

每个字段声明 **33 个 `canEdit*` 开关**：

```
canEditCaption          canEditName             canEditColumnName
canEditDataType         canEditEnum             canEditCtpenum
canEditEntity           canEditSerial           canEditParentctpenum
canEditMultiSelect      canEditDecimalDigits    canEditDefaultValue
canEditCalculate        canEditNotNull          canEditUniqueness
canEditMinLength        canEditMaxLength        canEditMin
canEditMax              canEditPattern          canEditPatternMessage
canEditSensitive        canEditEncryption       canEditSensitiveWordCheck
canEditHeterogeneousSystemEncryption
enableEditOpenApiEncrypt
canEditDataI18n         canEditAuditLog         canEditSearchable
canEditDescription      canEditWidgetConfig
```

**样本（`creator`）：** `canEditCaption: true`，其余全部 `false`
⇒ **系统字段只允许改显示名，不允许改类型/列名/约束**

**⇒ 关键推论：**
1. 这是**字段级的设计态权限**（谁能改什么），不是运行时数据权限
2. 58 个字段 × 33 个开关 = 设计态编辑能力的完整矩阵
3. **⇒ 平台对系统字段的保护是「配置级」的，不是代码级**

**证据等级：** `STATIC_RULE`
**待证：** 自定义字段的 capacity 是否不同 → 专题 1 下一轮

### 2.11 其他 presetData 文件

| 文件 | 实测内容 | 状态 |
|---|---|---|
| `entity.json` | **3 项**：`standard` / `archive` / `bill`（预置实体模板，含 `features` 字段） | 已解析 |
| `attribute.json` | **2 项**：`parentId`（ENTITY，聚合父节点ID）/ `orderNo` | 已解析 |
| `attributeSet.json` | 18 字段集 / 122 字段 | 已解析 |
| `presetAttributeCapacity.json` | **58 项**，33 个 canEdit* 开关 | 已解析 |
| `customerAttributeSet.json` | **1 项**：`cyclicity`（周期性设置），`sourceType: APP` | 已解析 |
| `basicDataEntityExtension.json` | **4 项**：`relationInfo` 等，含 `componentType: EntitySelector` | 已解析 |
| `billEnum.json` | **2 个枚举**：billStatus(8) + billSendState(2) | 已解析 |
| `formEnum.json` | 2 个枚举：formStatus(8) + ... | 已解析 |
| `archiveEnum.json` | 2 个枚举：archiveStatus(8) + ... | 已解析 |
| `scalability.json` | 30 个扩展列（10+10+10） | 已解析 |
| `scalabilityGlobal.json` | 全局扩展方案 | 已解析 |
| `event/defaultevent.json` | **9 个实体事件**（3 动作 × 3 时机） | 已解析 |

**⇒ 全部 13 个 presetData 文件已解析完毕，无剩余。**

**★ 修正：`attribute.json` 不是字段全集，只有 2 项。**
v4 假设它是「字段定义」，错误。真正的字段目录是 `attributeSet.json`。

**★ 重要：`entity.json` 只有 3 个预置实体（standard/archive/bill），不是 6 个。**
说明 `form` / `basicData` / `archiveTree` 没有预置实体实例，只有 stereotype 定义。

**★ `parentId` 的 dataType 是 `ENTITY`，description 是「聚合父节点ID」。**
这是「聚合（主子表）」在字段级的直接证据。
**⇒ 主子表关系可能通过 `parentId` 字段实现，而非独立的外键字段。待证。**

**★ `basicDataEntityExtension.json` 的 `relationInfo`：**
```json
{"name": "relationInfo", "caption": "关联实体", "dataType": "STRING",
 "componentType": "EntitySelector",
 "componentProps": {"name": "relationEntity", "placeholder": "请选择实体"},
 "rules": [{"required": true}]}
```
⇒ **`relationEntity` 是前端组件名，`relationInfo` 是字段名。**
这是「关联字段」在元数据层的定义形式。**待证它与 `ENTITY` 类型的区别。**

### 2.12 元数据对象关系图（当前可证部分）

#### 2.12.1 从 DTO 结构反推（★ 本轮新增的硬证据）

来源：`docs/audit/signatures.txt.gz` → `com.seeyon.udc.common.dto.*`

**`EntityDto`（37 方法 / 18 getter）**

| getter | 返回类型 | 说明 |
|---|---|---|
| `getAttributes()` | `List<AttributeDto>` | 实体 → 字段（1:N） |
| `getParent()` | **`EntityDto`** | 实体 → 父实体（**自引用**） |
| `getChildren()` | **`List<EntityDto>`** | 实体 → 子实体列表（**自引用**） |
| `getHasChild()` | `Boolean` | 是否有子实体 |
| `getEvents()` | `List<EventQueryResultDto>` | 实体 → 事件 |
| `getIndexes()` | `List<IndexDto>` | 实体 → 索引 |
| `getHasValidateRule()` | `Boolean` | 有校验规则 |
| `getHasAssignValueRule()` | `Boolean` | 有赋值规则 |
| `getHasDefaultValueRule()` | `Boolean` | 有默认值规则 |
| `getGenerateAggregateValidateClass()` | **`Boolean`** | **是否生成聚合校验类** |
| `getGenerateAggregateAssignClass()` | **`Boolean`** | **是否生成聚合赋值类** |
| `getGenerateAggregateDefaultValueClass()` | **`Boolean`** | **是否生成聚合默认值类** |
| `getHasOrderNo()` | `Boolean` | 有排序号 |
| `getHasDefaultValueSystemVariable()` | `Boolean` | 默认值含系统变量 |
| `getCapFirstName()` / `getUnCapFirstName()` | `String` | 首字母大写/小写名 |
| `getFullName()` / `getDtoFullName()` | `String` | 全名 |

**⇒ 决定性结论 1：主子表 = `EntityDto` 的自引用树**

```
EntityDto.getParent(): EntityDto          ← 指向父
EntityDto.getChildren(): List<EntityDto>  ← 指向子
EntityDto.getHasChild(): Boolean
```

**⇒ 主子表不是「两张独立的表 + 外键」，而是「实体树」。**
**⇒ 这解释了 `parentId` 字段（dataType=ENTITY, description=聚合父节点ID）的用途。**

**⇒ 决定性结论 2：聚合规则是「三类可选生成」**

```
getGenerateAggregateValidateClass()      校验规则
getGenerateAggregateAssignClass()        赋值规则
getGenerateAggregateDefaultValueClass()  默认值规则
```

**⇒ 主子表的规则（校验/赋值/默认值）可以在聚合层生成独立类。**
**⇒ 这与 `EntityRuleAggregateTemplate` 的存在吻合。**

**`Entity4CodeDto`（33 方法 / 15 getter）— 生成时的实体视图**

| getter | 返回类型 | 说明 |
|---|---|---|
| `getAttributes()` | `List<AttributeDto>` | 字段列表 |
| `getAttributeDtoMap()` | `Map<Long, AttributeDto>` | **按 ID 索引的字段** |
| `getAttributeDto4StrKeyMap()` | `Map<String, AttributeDto>` | 按名索引 |
| `getParent()` | **`Entity4CodeDto`** | 父实体 |
| `getChildren()` | **`List<Entity4CodeDto>`** | 子实体 |
| `getParentEntityId()` | `Long` | 父实体 ID |
| `getMultiplicity()` | **`EntityRelationMultiplicityEnum`** | **关联重数** |
| `getCategory()` | **`EntityCategoryEnum`** | **实体分类** |
| `getEntityRule4CodeDto()` | `EntityRule4CodeDto` | 实体规则 |
| `getHasEntityRule()` | `Boolean` | 有实体规则 |
| `getId()` / `getName()` / `getCaption()` | — | 标识 |

**⇒ `Entity4CodeDto` 是 `EntityDto` 的「生成期视图」，多带 `multiplicity` / `category` / `entityRule`。**

**`AttributeDto`（91 方法 / 45 getter）— 最丰富的元数据对象**

按语义分组：

| 组 | getter | 类型 |
|---|---|---|
| **标识** | `getName` / `getColumnName` / `getAppId` / `getEntityId` | String / Long |
| **类型** | `getDataFormat` | String |
| **约束** | `getUniqueness` / `getPermission` / `getOrderNo` / `getInCondition` / `getInDataMapping` | Boolean / Integer |
| **系统** | `getSystem` / `getHidden` / `getEdit` | Boolean |
| **★ 表达式** | `getExpressionDesignData` | **String** |
| | `getExpressionRuntimeData` | **String** |
| | `getDefaultValueExpressionDesignData` | **String** |
| | `getDefaultValueExpressionRuntimeData` | **String** |
| | `getValueScopeExpression` | String |
| | `getCalculate` | — |
| **★ 默认值** | `getDefaultValueIsChange` | **Boolean** |
| | `getDefaultValueSystemVariable` | — |
| | `getDefaultValueCaption` | String |
| **关联** | `getRelationCtpEnum` | `RelationCtpEnumDto` |
| | `getParentEnumAttributeId` | Long |
| **序列** | `getSerialNumberName` / `getSerialNumberCode` / `getSerialNumberGuid` | String |
| **安全** | `getEnableEncryption` / `getEncryption` / `getEnableDesensitization` / `getDesensitization` / `getEnableSensitiveWordCheck` / `getEnableOpenApiEncrypt` | Boolean / — |
| **来源** | `getSourceType` | `AttributeSourceTypeEnum` |
| | `getSourceId` | — |
| **其他** | `getExistDto` / `getDataI18n` / `getWidgetConfig` / `getUseSnapshot` / `getAuditLog` | Boolean / — |
| **全名** | `getAttributeFullName` / `getAttribute4DtoFullName` / `getUniqueKey` | String |

**★★ 决定性结论 3：表达式在元数据层就分「设计态 / 运行态」两份**

```java
getExpressionDesignData(): String          ← 设计态
getExpressionRuntimeData(): String         ← 运行态
getDefaultValueExpressionDesignData(): String
getDefaultValueExpressionRuntimeData(): String
```

**⇒ 这直接回答了专题 4 的核心问题：**
**「表达式定义」与「表达式执行」在元数据层就是两个字段，不是同一份数据的不同视图。**

**⇒ 与 `ExpressionCodeGenerator` 形成完整链路（待证）：**
```
设计态数据 (DesignData)
  → ExpressionCodeGenerator#generateCode
  → 运行态数据 (RuntimeData) + exp<雪花ID> 方法
```

**★ 决定性结论 4：`getDefaultValueIsChange(): Boolean`**

- 字段级布尔，语义为「默认值是否变更」
- **极可能与 `copyNeedResetNull` 相关**（判断是否需要重置为 null 后重新算默认值）
- **⚠️ 但不得断言。** `copyNeedResetNull` 零调用者，两者关联是推测
- **标记 `UNVERIFIED`，需两边反编译**

**★ 结论 5：`getEntityId(): Long` 证明字段属于实体（N:1）**

**★ 结论 6：`getSourceType(): AttributeSourceTypeEnum`**

配置中实测到的取值（来自 `attributeSet.json`）：
- `UDC` — 低代码平台字段
- `SYSTEM` — 系统字段
- `APP` — 应用字段（`customerAttributeSet.json` 的 `cyclicity`）
- `ATTRIBUTESET` — 来自字段集（`cyclicity` 的子字段）

#### 2.12.2 对象关系模型（已证部分）

```
Application (appId)
  │
  ├─ Entity (EntityDto)
  │    ├─ getAttributes() ──────────→ AttributeDto (1:N)
  │    ├─ getParent() ──────────────→ EntityDto   (自引用，聚合父)
  │    ├─ getChildren() ────────────→ EntityDto[] (自引用，聚合子 = 主子表)
  │    ├─ getEvents() ──────────────→ EventQueryResultDto[]
  │    ├─ getIndexes() ─────────────→ IndexDto[]
  │    └─ getGenerateAggregate*Class() → Boolean (三类聚合规则类)
  │
  └─ AttributeDto
       ├─ getEntityId() ────────────→ Entity (N:1，归属)
       ├─ getRelationCtpEnum() ─────→ RelationCtpEnumDto (关联枚举)
       ├─ getParentEnumAttributeId()→ AttributeDto (父枚举字段，自引用)
       ├─ getExpressionDesignData() ──────→ String (设计态)
       ├─ getExpressionRuntimeData() ─────→ String (运行态)
       ├─ getDefaultValueExpressionDesignData() → String
       ├─ getDefaultValueExpressionRuntimeData() → String
       └─ getSerialNumber*() ───────→ Serial 定义
```

**⇒ 这是目前能证的最完整关系图，全部来自签名返回类型（`VERIFIED_STATIC_BYTECODE`）。**

**⚠️ 仍未证：**
- `EntityCategoryEnum` / `EntityRelationMultiplicityEnum` 的取值（枚举常量不在签名库）
- 元数据的**存储位置**（MySQL/Redis/OSS 分工）
- 元数据的**创建/修改 API**

### 2.13 表达式样本（★ 意外收获，留给专题 4）

来源：`udc-expression-samples.json`（25 个样本，21 个含 designData）

**样本结构：**
```json
{
  "source_file": "docs/audit/artifacts/udc-node-evidence/real_CALL_APP_SERVICE.json",
  "locator": "[0].node.attrs[0].value",
  "title": "{登录人员ID}",
  "designData": {
    "expressionTranslation": "登录人员ID ",
    "resultTypeInfo": "BIGINTEGER",
    "terminalType": "BACKEND",
    "isMultiSelect": false,
    "context": [],
    "tokens": [{"uid": "...", "type": "SYSTEM", "value": "system.currentUserId"}]
  },
  "executableExpr": "93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=currentUserId%28%29"
}
```

**⇒ 关键观察：**
1. **`executableExpr` 格式 = `<固定前缀>=<URL编码表达式>`**
   - `currentUserId%28%29` → `currentUserId()`
   - `uniqueMark%28%29` → `uniqueMark()`
   - 前缀 `93gDaq3/...=` 在多个样本中**相同**（可能是应用级密钥）
2. **`designData.tokens` 是表达式的最小单元**，`type` 实测有 `SYSTEM` / `FUNCTION`
3. **`designData.context`** 承载变量上下文（如微流程节点输出）
4. **`resultTypeInfo`** 声明结果类型（`BIGINTEGER` / `STRING`）

**⇒ 这为专题 4 提供了「设计态 → executableExpr」的直接样本。**

**⚠️ 注意：`note` 说「designData 为 None 表示该样本源只含 runtimeData」，
但实测 25 个样本中 `runtimeData` 字段全为空（0 个）。
⇒ 该文件的实际字段名是 `executableExpr`，不是 `runtimeData`。**

---

## 3. 证据清单

| # | 结论 | 证据等级 | 源文件 | 类/方法 | 版本 |
|---|---|---|---|---|---|
| 1 | 6 种 stereotype 及 necessaryFeatures | `STATIC_RULE` | `resources/stereotype/*/config.json` | — | 5.3.517 |
| 2 | `basicData` 不支持 dataFlow | `STATIC_RULE` | `stereotype/basic_data/config.json` | `dataFlowEnabled: false` | 5.3.517 |
| 3 | 18 个 feature 定义 | `STATIC_RULE` | `resources/feature/*/config.json` | — | 5.3.517 |
| 4 | 4 个 feature 有 `stereotypeBind=true` | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 5 | `archiveTiled` 与 `treeEntity` 互斥 | `STATIC_RULE` | `feature/archive_tiled/config.json` | `mutuallyExclusiveFeatures` | 5.3.517 |
| 6 | 18 个字段集 / 122 字段 | `STATIC_RULE` | `presetData/attributeSet.json` | — | 5.3.517 |
| 7 | `basic` 6 个系统字段（含 version/draft/tenantId） | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 8 | 字段类型 10 种，ENTITY 占 44/122 | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 9 | 单据 billBasic 13 字段（含 caseId/templateId/billCode） | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 10 | 挂起/终止/作废三套对称 7 字段 | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 11 | 树形用物化路径（treePath/treeLevel/isLeaf） | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 12 | classType 7 种分层枚举 | `STATIC_RULE` | `feature/*/template/config.json` | — | 5.3.517 |
| 13 | classMode 2 种（CLASS_NEW / CLASS_SAME） | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 14 | methodType 2 种（APPEND / JOIN） | `STATIC_RULE` | `feature/tree_entity/template/config.json` | — | 5.3.517 |
| 15 | 5 个 joinPointName（preCreateBatch/middle/preUpdateBatch/afterUpdate/after） | `STATIC_RULE` | 同上 | — | 5.3.517 |
| 16 | 平台服务依赖 17 项 | `STATIC_RULE` | `presetData/dependencyGraph.json` | — | 5.3.517 |
| 17 | `entity.json` 只有 3 个预置实体 | `STATIC_RULE` | `presetData/entity.json` | — | 5.3.517 |
| 18 | `parentId` 是 ENTITY 类型，description=聚合父节点ID | `STATIC_RULE` | `presetData/attribute.json` | — | 5.3.517 |

---

## 4. 推翻/修正的旧结论

| # | 旧结论 | 修正 | 依据 |
|---|---|---|---|
| 1 | `dependencyGraph.json` 是元数据对象依赖图 | **是平台服务依赖清单（17 项）** | 逐字解析 |
| 2 | `attribute.json` 是字段定义全集 | **只有 2 项（parentId/orderNo）** | 逐字解析 |
| 3 | feature config 有 26 份 | **22 份（18 特性 + 4 模板声明）** | 脚本统计 |
| 4 | 特性内联声明字段（`attributes` 数组） | **`attributes` 全为空，字段走 attributeSet 引用** | 逐字解析 |
| 5 | `entity.json` 有 6 个预置实体 | **只有 3 个（standard/archive/bill）** | 逐字解析 |

---

## 5. 未解决问题

| # | 问题 | 阻塞原因 | 下一步 |
|---|---|---|---|
| 1 | 元数据对象间的真实依赖关系 | `dependencyGraph.json` 不是这个用途 | 从 `EntityDto`/`AttributeDto`/`Entity4CodeDto` 字段结构反推 |
| 2 | `baseservice.java.ftl` 对应哪个 classType | classType 无 BASE_SERVICE | 反编译 `EntityFileTemplate#getBaseServiceOutPath` |
| 3 | `organization` 与 `archiveTiled` id 都是 13 | 数据异常 | 查是否有 id 冲突处理逻辑 |
| 4 | `disable` 与 `attribute_scalability` 配置完全相同 | 疑似复制 | 查两者运行时行为是否真的相同 |
| 5 | joinPoints 是否对开发者开放 | 只有特性配置可见 | 查 `TemplateInterceptor` / `CodeParam` 扩展点 |
| 6 | `version`/`draft` 字段的真实运行时语义 | 需实测 | 专题 3 |
| 7 | 主子表是否真用 `parentId` 实现 | 只有字段定义 | 专题 3（需 jar 反编译或实测） |
| 8 | 剩余 presetData 文件（8 个未解析） | 本轮时间 | 下一轮 |

---

## 6. 下一轮任务

按优先级：

1. **解析剩余 8 个 presetData 文件**（billEnum/formEnum/archiveEnum/scalability/event 等）
2. **从 DTO 结构反推元数据对象关系**（`EntityDto` / `AttributeDto` / `Entity4CodeDto` 全字段）
3. **元数据 CRUD 机制**（`EntityService` 全部方法 + 元数据 API）
4. **转到专题 2**：CodeTask ↔ Template 映射（阶段 2 主任务）

---

## ★★★ A. EntityMeta 运行态加载机制（2026-11-17 新增，源码级）

**本节修正一个关键认知：`EntityMeta` 不是从数据库读的，是注解扫描构建的。**

**完整内容见：`01B-metadata-loading-CORRECTION.md`**

### A.1 三层区分（不矛盾的三个层次）

```
① 设计态元数据
   UDC 设计器 → 数据库 / OSS（用户配置的实体定义）
   ↓ 代码生成
② 生成物
   Java Entity 类（@EntityInfo / @EntityAttribute / @Table）
   Java DTO 类（@DtoInfo / @Maskable）
   ↓ 启动时扫描
③ 运行态 EntityMeta
   EntityRelationHandler.scanClass() → new EntityMeta() → LRU 缓存
```

**⇒ 本文前面说的「元数据存储」指 ①。**
**⇒ 本节说的是 ③ —— 运行时的 `EntityMeta` 对象内存结构。**

### A.2 关键构建规则（直接约束开发）

| 规则 | 违反后果 |
|---|---|
| 实体类必须有 `@EntityInfo("显示名")` | 不被扫描 |
| DTO 必须有 `@DtoInfo(entity="实体全限定名")` | `dtoClass` 为 null |
| 子实体必须有 `parentId` + `@EntityAttribute(relationType, relationEntity)` | 日志 warn，关系断掉 |
| 表名来自 `@Table(name=...)` | `entityTable` 为空 |
| `@Maskable` 打在 DTO 字段（不是 Entity） | 脱敏失效 |

### A.3 `dtoListName` 自动生成规则（最容易踩坑）

```java
convertDtoList(relationType, entityFullName):
  One2OneAggregation  → <简单名首字母小写> + "Dto"
  One2ManyAggregation → <简单名首字母小写> + "DtoList"     ← ★ 最常见
  Association / NONE  → <简单名首字母小写>
```

**⇒ 子实体 `OrderDetail` + `One2ManyAggregation` → DTO 字段名必须是 `orderDetailDtoList`**
**⇒ 名字不对 → 反射取不到 → 子表静默不写入，且不报错**

### A.4 枚举取值（源码级，之前未知）

```java
EntityType:    MASTER_ENTITY(0) / SUB_ENTITY(1)
RelationType:  NONE(0)
               Many2OneAssociation(1)
               One2OneAssociation(2)
               One2OneAggregation(3)     ← 一对一主子表
               One2ManyAggregation(4)    ← 一对多主子表
```

**⇒ 只有 `Aggregation` 才参与级联写入，`Association` 只是引用。**

### A.5 缓存

```
LRU_ENTITY_CACHE      容量 200，key = classLoader + appName
LRU_CLASS_SET_CHCHE   容量 200
清除：EntityRelationHandler.clearCache(classLoader, appName)
触发：ModuleUnloadEvent（部署/卸载）
```

**⇒ 改注解不重新部署 → 读到旧元数据。**
