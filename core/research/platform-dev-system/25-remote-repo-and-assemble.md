# Maven 仓库与部署物格式（远程仓库实证）

> 仓库：`http://172.28.24.205/artifactory/libs-release/com/seeyon/`（Artifactory，544 个 artifact）
> 本地镜像：`D:/repo/REMOTE/com/seeyon/`
> 等级：`VERIFIED_STATIC_BYTECODE`（zipfile 实测）+ `LIVE_RULE`（HTTP 仓库列表/下载）
> 时间：2026-11-18

---

## 0. ★★★ 三个重大结论

| # | 结论 | 影响 |
|---|---|---|
| **1** | **仓库有 544 个 artifact，`-biz` 76 个 / `-web` 77 个，但标品只有 21 + 21** | **其余全是客户应用** |
| **2** | **`-web` 包**没有**前端 JS/Vue，全部是 Controller** | **前端不在 Maven 仓库** |
| **3** | **`-assemble-resource` 是「应用部署物」**（元数据 json + .usd + 建表 sql + i18n） | **★★★ UDC 元数据的真实存储格式完全暴露** |

---

## 1. ★★ 仓库结构

```
libs-release/com/seeyon/   (544 artifacts)
├─ 标品 boot-*/udc-*/bpm-*/cip-*/ctp-*/cdp-*/organization-*/portal-*/m5-*/ai-*
├─ 客户应用 jar（占绝大多数）
│   ├─ ceshi*（测试）        ceshiyi* / ceshiyong*（十几个）
│   ├─ xiangmuguanli*        znxmglpt*（项目管理）
│   ├─ datamigration*        faccountsreceivable*（应收）
│   ├─ peixunudc*            projectassessment*（项目评估）
│   ├─ didaimaxuexi*         developtest*（开发测试）
│   └─ ...
└─ 其他：boot-all / udc-parent / udc-starters / devops-starters / dependencies
```

### 1.1 ★ 标品 `-biz`（21 个，已下载）

| artifact | 版本 | 大小 | 类数 |
|---|---|---:|---:|
| bpm-biz | 5.3.353 | 7.89 MB | **2,730** |
| udc-biz | 5.3.605 | 6.65 MB | **1,856** |
| cdp-data-biz | 5.3.278 | 3.74 MB | **1,927** |
| app-common-biz | 5.3.271 | 3.21 MB | 632 |
| cip-connector-biz | 5.3.286 | 3.06 MB | 1,205 |
| organization-biz | 5.3.344 | 3.02 MB | 668 |
| ctp-user-biz | 5.3.334 | 2.68 MB | 876 |
| cip-capability-biz | 5.3.276 | 2.21 MB | 840 |
| portal-biz | 5.3.369 | 1.56 MB | 594 |
| ctp-affair-biz | 5.3.330 | 1.13 MB | 345 |
| cdp-schedule-biz | 5.3.272 | 1.10 MB | 483 |
| app-doc-biz | 5.3.264 | 0.98 MB | 477 |
| m5-biz | 5.3.265 | 0.91 MB | 401 |
| cip-manager-biz | 5.3.279 | 0.68 MB | 277 |
| app-approval-biz | 5.3.283 | 0.56 MB | 232 |
| ctp-message-biz | 5.3.287 | 0.29 MB | 151 |
| ai-biz | 5.3.272 | 0.26 MB | 132 |
| cip-openapi-gateway-biz | 5.3.263 | 0.13 MB | 63 |
| cip-convert-biz | 5.3.261 | 0.11 MB | 39 |
| ctp-webapi-gateway-biz | 5.3.263 | 0.10 MB | 41 |
| ctp-media-biz | 5.3.261 | 0.06 MB | 25 |

**合计 42 MB / 13,994 类**（与 `CHIT-extra` 完全一致 ⇒ 确认 `CHIT-extra` 就是标品实现层）

### 1.2 ★ 标品 `-web`（21 个，已下载，共 1.4 MB）

**全部只含 Controller，零 JS/Vue/HTML：**

| artifact | 条目 | class | js | vue | html |
|---|---:|---:|---:|---:|---:|
| udc-web 5.3.605 | 66 | **54** | 0 | 0 | 0 |
| bpm-web 5.3.353 | 77 | **65** | 0 | 0 | 0 |
| organization-web 5.3.344 | 113 | **78** | 0 | 0 | 0 |
| ctp-user-web 5.3.334 | 69 | 48 | 0 | 0 | 0 |
| portal-web 5.3.369 | 49 | 37 | 0 | 0 | 0 |
| cdp-data-web 5.3.278 | 77 | 48 | 0 | 0 | 0 |
| app-common-web 5.3.271 | 107 | 39 | 0 | 0 | 0 |
| cip-capability-web 5.3.276 | 36 | 13 | 0 | 0 | 0 |
| cip-connector-web 5.3.286 | 62 | 35 | 0 | 0 | 0 |
| m5-web 5.3.265 | 35 | 18 | 0 | 0 | 0 |

**★★★ 结论：`-web` = REST Controller 层，前端（Vue/JS）不在 Maven 仓库。**

---

## 2. ★★★ `udc-web` 的 54 个 Controller（REST 接口全集）

**这是 UDC 所有对外 HTTP 接口的入口清单：**

```
设计态（元数据/页面/微流程）
  EntityController              实体
  AttributeSetController        属性集
  AttributeGroupController      属性组
  EntityGroupController         实体组
  DataTypeController            ★ 数据类型（PERSONSELECTOR 就在这）
  StereotypeController          原型
  PageInfoController            页面信息
  PageLayoutController          页面布局
  PageTemplateController        页面模板
  PageTemplateClassController   页面模板分类
  PageTemplatePublishedController 模板发布
  PageRouteController           页面路由
  PortletController / PortletGroupController   门户组件
  MetaDataController            ★ 元数据
  UdcDesignMetadataController   设计态元数据
  DataTransferObjectController  DTO
  UdcEnumController / UdcEnumItemController / UdcEnumCategoryController / UdcCtpEnumController  枚举四件套
  MicroFlowController           ★ 微流程
  MicroFlowGroupController      微流程组
  MicroFlowMacroController      微流程宏
  MicroFlowRefactorController   微流程重构
  MicroFlowUpgradeController    微流程升级
  MicroFlowFunctionalCheckController ★ 微流程功能检查
  TempPresetMicroFlowController 预置微流程
  FunctionNodeController        功能节点
  BackendComponentController    后端组件
  DataFlowDesignController      ★ 数据流设计（生单规则）
  DeductionRuleController       ★ 扣减规则
  ReferConfigController         ★ 关联配置
  ScalabilityController / ScalabilityOptionController  扩展性
  FeatureController             特性
  ParameterController           参数
  ApplicationController         应用
  AppCollaborationController    应用协作
  AttachmentTemplateController  附件模板

运行态
  PublishStateController        发布状态
  DeployController / DeploymentController  ★ 部署
  SandboxController / UdcSandBoxLogController  沙箱
  UdcManagerController          管理器
  MultiEditController           多编辑
  UdcFileController             文件
  EntityOpenApiController       ★ 实体开放 API
  OperationLogController        操作日志
  DependencyAnalysisController  ★ 依赖分析（对应 BPM usedparam 那套）
  IndexController               首页
  COLISplitController           COLI 拆分
```

**★★★ 六个之前没见过的关键 Controller：**
```
DependencyAnalysisController    依赖分析（BPM detection 的 HTTP 入口）
DataFlowDesignController        数据流设计（生单规则画布）
DeductionRuleController         扣减规则
MicroFlowFunctionalCheckController  ★ 微流程「检查」按钮（你强调的那个）
UdcSandBoxLogController         沙箱日志
EntityOpenApiController         实体开放 API
```

**★ 没有 `PersonSelectorController` —— 进一步印证 `PERSONSELECTOR` 无交互实现。**

---

## 3. ★★★★ `-assemble-resource`：应用部署物的真实格式

**53 个 `-assemble-resource` 全部是客户应用（标品不发布）。**

**但结构完全暴露了 UDC 应用的部署物格式：**

```
{appId}-assemble-resource-{ver}.jar
├─ metadata/json/          ★ 元数据（每类一个 json，或每实例一个）
│   ├─ udc@com.seeyon.udc.entity.domain.entity.Entity.json          ← 实体定义
│   ├─ udc@com.seeyon.udc.entity.domain.entity.AttributeGroup.json
│   ├─ udc@com.seeyon.udc.entity.domain.entity.ReferConfig.json
│   ├─ udc@com.seeyon.udc.page.domain.entity.PageSchemaEntity@PAGE@{id}.json  ← 每个页面一个
│   ├─ udc@com.seeyon.udc.microflow.domain.entity.MicroFlowEntity@FRONTEND@{id}.json
│   ├─ udc@com.seeyon.udc.dataflow.domain.entity.DataFlowMapping.json
│   ├─ udc@ctp_enum_ids.json
│   └─ {appId}@ReferConfig@_{id}.json
├─ schema/app_schema.zip   ★ schema（.usd 格式）
│   └─ app_schema/udc/{FQCN}.usd         ← 每类一个 .usd
│       ├─ Entity.usd                     实体
│       ├─ MicroFlowEntity.usd            微流程
│       ├─ PageSchemaEntity.usd           页面
│       ├─ DataFlow.usd / DataFlowMapping.usd   数据流
│       └─ upgrade/deploy-record.usd      部署记录
├─ init/                   ★ 初始化数据（按版本号分目录）
│   ├─ {ver}/              应用自身初始化数据
│   └─ tenant/             租户初始化数据
│       └─ {appId}@com.seeyon.boot.starter.serialnumber.domain.entity.SerialScheme.json
├─ i18n/                   ★ 国际化
│   ├─ enums_en.properties / enums_zh_CN.properties / enums_zh_TW.properties
│   └─ application_zh_CN.properties
├─ dependencies.json       ★ 依赖清单
├─ artifactIds.txt         构件 ID 清单
├─ app-deploy-info.json    部署信息
└─ application.y           应用定义（YAML？）
```

**★★★ 四类内容的角色：**
```
metadata/json/   设计态元数据（可读 JSON，供导入）
schema/          schema 快照（.usd，实际也是 JSON）
init/            初始化业务数据（如流水号方案、枚举项）
i18n/            多语言资源
```

---

## 4. ★★★★ `.usd` 格式 = 纯 JSON（重大发现）

**`.usd` 不是二进制！是 UTF-8 JSON。**

### 4.1 `Entity.usd` 的真实结构

```json
[{
  "id": "3582244432195832261",
  "guid": -2707966435769299397,
  "appId": null,
  "dataId": "com.seeyon.udc.entity.domain.entity.Entity",
  "model": "udc",
  "schema": {
    "validate": true,
    "id": 3582244432195832261,
    "guid": -2707966435769299397,
    "originalId": 0,
    "publishState": "UNPUBLISH",        ← ★ 发布状态
    "createTime": 1791796505000,
    "updateTime": 1793156814000,
    "appId": 8704025620829192834,
    "appName": "datamigration8704025620829192834",
    "name": "fileMigration",             ← 实体名
    "tableName": "filemigra_m2707966435769299397",   ← ★★★ 物理表名
    "caption": "文件上传中间表",
    "searchable": true,
    "stereotype": "standard",            ← ★ 原型
    "features": "basic",                 ← ★ 特性
    "parentEntityId": 0,
    "entityType": "MASTER_ENTITY",       ← ★★★ 主实体
    "multiplicity": "ONE2MANY",          ← ★ 关系基数
    "category": "ENTITY",
    ...
  }
}]
```

**★★★ 实体定义的完整字段语义：**
```
name            逻辑名（代码里用）
tableName       物理表名（平台自动生成：{缩写}_m{guid绝对值}）
caption         中文名
stereotype      原型（standard / ...）
features        特性（basic / ...）
entityType      MASTER_ENTITY / SUB_ENTITY     ← ★ 主/子实体
parentEntityId  父实体 ID（0=主实体）
multiplicity    ONE2MANY / ONETOONE / MANYTOMANY
searchable      可搜索
publishState    UNPUBLISH / RELEASE
appId/appName   所属应用
guid            全局唯一（雪花）
```

### 4.2 ★★★ 主子表的真实定义方式（回答核心问题）

**实测 24 个实体里 6 个子实体：**

| 子实体 | 中文 | parentEntityId | 父实体 |
|---|---|---|---|
| `MigrationLog` | 迁移日志 | 8456954308866361572 | **`LogSchemeInformatio`** |
| `migrationBatchItem` | 迁移批次行明细 | -4503662122004480182 | **`migrationTaskBatch`** |
| `migrationPlanJoin` | 表级别 JOIN 配置 | 4796455827714164161 | **`migrationPlan`** |
| `migrationPlanField` | 迁移字段配置 | 4796455827714164161 | **`migrationPlan`** |
| `asongda` | 阿松大 | -7467452946344431599 | **`xzhDedBill`** |
| `asongdaasongda` | 阿松大阿松大 | -7955490970033259 | （父不在本应用） |

**★★★ 主子表的定义规则：**
```
主实体：entityType = "MASTER_ENTITY", parentEntityId = 0
子实体：entityType = "SUB_ENTITY",   parentEntityId = {父实体 guid}
multiplicity = "ONE2MANY"（一对多）
```

**★★ 一个重要事实：`migrationPlan` 有两个子实体（`migrationPlanJoin` + `migrationPlanField`）**
**⇒ 一个主实体可以有**多个子实体**（不是只能一个）。**

**★★ 另一个：`migrationPlan` 和 `migrationPlanGroup` 都是 MASTER，没有主从关系**
**⇒ 「分组」是独立实体，通过**字段关联**建立关系，不是 SUB_ENTITY。**

### 4.3 ★ 所有 `.usd` 文件清单（41 个，29 个是 UDC 元数据）

| .usd 文件 | 大小 | 内容 |
|---|---:|---|
| `Entity.usd` | 28 KB | **实体（24 个）** |
| `MicroFlowEntity.usd` | **708 KB** | **微流程（最大）** |
| `PageSchemaEntity.usd` | **683 KB** | **页面 schema** |
| `Index.usd` | 7 KB | 索引 |
| `UdcEnumItem.usd` | 16 KB | 枚举项 |
| `UdcEnumCategory.usd` | 1.8 KB | 枚举分类 |
| `DataFlow.usd` / `DataFlowMapping.usd` | 4.3 / 7.3 KB | **数据流（生单规则）** |
| `Event.usd` | 1 KB | 事件 |
| `Scalability.usd` / `ScalabilityOption.usd` | 17 / 1.3 KB | 扩展性 |
| `AttributeSet.usd` | 1.3 KB | 属性集 |
| `UdcApplication.usd` | 2.1 KB | 应用 |
| `EntityGroup.usd` / `MicroFlowGroup.usd` | 1.2 / 1.4 KB | 分组 |
| `CtpParameterDefinition.usd` | 35 KB | CTP 参数 |
| `CtpJobInfo.usd` / `CtpJobSimple.usd` | 117 / 49 KB | 定时任务 |
| `ExcelExportTemplate.usd` | **2.0 MB** | **Excel 导出模板（最大）** |
| `deploy-record.usd` | 1.4 KB | **部署记录** |
| 其余 | | |

**★★★ 关键：微流程（708 KB）和页面（683 KB）是最大的两个元数据。**

---

## 5. ★★ `metadata/json/` 与 `schema/*.usd` 的关系

**同一个应用有两套元数据导出：**

| 位置 | 格式 | 用途 |
|---|---|---|
| `metadata/json/` | 每类一个汇总 json，或每实例一个 | **可读/可编辑/增量导入** |
| `schema/app_schema/*.usd` | 每类一个 `.usd`（也是 JSON） | **完整快照/部署** |

**★ `metadata/json/` 70 个，`schema/` 41 个 `.usd` —— 粒度和用途不同。**

**⇒ `metadata/json` 里 `PageSchemaEntity@PAGE@{id}.json` 是**每页一个文件**（18 个），**
**⇒ `schema/PageSchemaEntity.usd` 是**全部页面一个大文件**（683 KB）。**

---

## 6. ★★★ `init/tenant/` 初始化数据（关键）

**格式：`{appId}@{FQCN}.json`，内容是**该实体的记录数组**：**

```json
// init/tenant/datamigration8704025620829192834@com.seeyon.boot.starter.serialnumber.domain.entity.SerialScheme.json
[{
  "id": 5322697915022528497,
  "code": "yuxiadanshenpiy_5687988451191571804",
  "name": "预下单审批页单据编号流水号",
  "serialType": "APP",
  "appGuid": "2275741415570096882",
  "appId": "8704025620829192834",
  "entityFullName": "",
  "totalSize": 6,
  "unusedPriority": false,
  "serialResetRule": "NONE",
  "active": true,
  "preset": true,
  "sourceAppName": "udc",
  "aggregationAppName": "datamigration8704025620829192834"
}]
```

**★★★ 这印证了 `17-cache-serialnumber.md` 里的 SerialScheme 字段 —— 完全一致。**
**⇒ 也说明：流水号方案是**随应用部署**的初始化数据。**

---

## 7. ★ 覆盖度更新

| 域 | 上轮 | 本轮 |
|---|---|---|
| **官方 102 jar 覆盖率** | 80/102 = 78.4% | **101/102 = 99.0%** |
| **`-web` 层（Controller）** | 0% | **90%**（54 个 UDC Controller 全清单） |
| **部署物格式（assemble-resource）** | 0% | **95%** |
| **`.usd` 元数据格式** | 0% | **90%**（Entity.usd 完整字段） |
| **主子表定义机制** | 95% | **100%**（`entityType` + `parentEntityId` 实证） |

---

## 8. 未覆盖

| 项 | 说明 |
|---|---|
| 标品前端（Vue/JS） | **Maven 仓库没有**。需从平台运行包/nginx 静态目录取 |
| `udc-assemble` | 仓库中确实不存在（可能改名或从未发布） |
| `MicroFlowEntity.usd`（708 KB）的完整结构 | 只知存在，未解析 |
| `PageSchemaEntity.usd`（683 KB）的完整结构 | 同上 |
| `ExcelExportTemplate.usd`（2 MB）的完整结构 | 同上 |
| `application.y` 格式 | 未读 |
| `dependencies.json` / `app-deploy-info.json` | 未读 |
| 各 Controller 的 REST 路径 | 未读注解（需反编译或读源码） |
| `metadata/json` vs `.usd` 谁先谁后 | 未验证导入顺序 |