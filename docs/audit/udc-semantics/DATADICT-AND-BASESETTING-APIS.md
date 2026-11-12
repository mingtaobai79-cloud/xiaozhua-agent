# UDC 数据字典 / 基础设置 / 页面字典 / 构建 接口审计

- 审计时间: 2026-10-12 (CST)
- 目标应用: appId=8704025620829192834 (datamigration9000000000000000001, caption=数据迁移)
- 环境: https://lowcode-test2.example.com (test2, UDC 5.3.517)
- 凭据: 使用 shared-credentials/test2-web-credential.json 的 cookie（本文一律脱敏为 [REDACTED]）
- 纪律: 全程只读。唯一执行的写端点 = 无；构建 op 仅抽取字段，未触发。
- 证据来源标注: 【curl 实测】【chunk 原文】【javap】【DB 查询】【DTO 常量池】

## 1. datadictionary 接口实测 (curl 实测)

### 1.1 请求
```
GET https://lowcode-test2.example.com/service/udc/application/datadictionary/8704025620829192834
Cookie: [REDACTED]
```
- HTTP 状态: **200 OK**
- Content-Type: **`text/html;charset=UTF-8`**（非 JSON 信封，直接返回 HTML 文档）
- 响应体大小: 49,567 字节
- 结论: 该接口**没有** status/code/message JSON 信封；它是把 `SingleResponse<String>` 的 content（HTML 字符串）直接以 text/html 吐出（成功才 200）。原始响应存档: `<HERMES_HOME>/cache/scratch/dd_raw.json`。

### 1.2 响应结构树（HTML 三段式数据字典）
```
<html>  <title>数据字典</title>
<h1> {应用 caption}数据字典        →  实例值: "数据迁移数据字典"
<h2>实体列表</h2>
  表格列: 序号 | 实体名称(锚点 #entity_{id}) | 编码 | 表名 | 父实体 | 类型(主表/子表/ [标准])
  实例 (8 行, 7 个数据迁移实体 + 1 个我建的 smokeEnt):
    1 数据源配置信息   migrationDatasource     migration_6624154496755977791
    2 文件上传中间表   fileMigration           filemigra_m2707966435769299397
    3 日志方案信息     LogSchemeInformatio     logscheme_7361890036342148391  (主表)
    4   迁移日志       MigrationLog            migration_m4456719055659251797 (子表, 父=日志方案信息)
    5 迁移方案配置     migrationPlan           migration_m2561447780012437779 (主表)
    6   表级别 JOIN 配置 migrationPlanJoin     migration_m3124038816937981587  (子表, 父=迁移方案配置)
    7   迁移字段配置   migrationPlanField      migration_3324850346838279553   (子表, 父=迁移方案配置)
    8 实体冒烟V2       smokeEnt=4959872207057160792
<h2>字段列表</h2>  (按实体的 <h3 id="entity_{id}"> 分块, 共 8 个 h3)
  表格列: 序号 | 名称 | 编码 | 数据库列名 | 字段类型 | 数据类型 | 多选 | 必填 | 默认值 | 系统字段 | 备注
  样例行 (迁移日志, entity_1627860264017874938):
    id / id / 长整数 / BIGINT / 系统
    tenantId / tenant_id / 长整数 / BIGINT / 系统
    draft / draft / 布尔值 / TINYINT / 默认值 false / 系统
    parentId / parent_id / 实体-日志方案信息(锚点互链) / BIGINT
    joinType(迁移方案) / 枚举-JOIN连接枚举 / BIGINT / 默认值 "左连接 (4120495978993240656)"
  样例行 (实体冒烟V2): smokeStr/smoke_str/单行文本/VARCHAR/备注 0-100; smokeInt/INT; smokeDec/DECIMAL;
    smokeDate/DATE; smokeTime/DATETIME; smokeBool/TINYINT
<h2>选项集列表</h2>   ← 该应用**空**（无 CTP 枚举选项集）
```
- 脱敏说明: 响应含真实表名/列名/实体 id，均为该测试租户的非敏感元数据；无个人敏感值。
- 无 404，无需路径变体探测。

## 2. 后端 controller 归属 (javap)

来源: `docs/audit/artifacts/udc-web-5.3.517-javap/ApplicationController.javap.txt` (GBK 解码)。

| 项 | 值 |
|---|---|
| 类 | `com.seeyon.udc.controller.ApplicationController` |
| 类级注解 | `@RestController` + `@RequestMapping("udc/application")` + `@RestApi(value="应用信息访问接口", group="应用")` |
| 类级权限 | `@HasRole("udcRootOrgAdmin","udcSystemAdmin","udcAppDesigner")` |
| 方法 | `public SingleResponse<String> dataDictionary(Long id)` |
| 方法注解 | `@RestApiOperation(value="生成应用的数据字典", description="生成应用的数据字典")`（GBK 解码, javap.txt 第 4178 行） |
| HTTP 映射 | `@GetMapping("datadictionary/{id}")`，参数 `@PathVariable("id") @ParameterInfo("应用信息id")` |
| 委托链 | `dataDictionaryGeneratorAppService.generateHtml(SingleRequest.from(id))` → `com.seeyon.udc.appservice.DataDictionaryGeneratorAppService`（j517 中存在该类与 `DataDictionaryGenerator`/`DataDictionaryBuilder` 源码结构: 实体列表+字段列表+选项集列表三段） |

完整 URL = gateway `/service/udc` + `udc/application` + `datadictionary/{id}` ✔ 与实测一致。

其他相关 controller（_full_api_map.json + 类级注解 javap）:
| Controller | @RequestMapping | @HasRole | 职责 |
|---|---|---|---|
| DeployController | `udc/runtime` (【javap】, _full_api_map 记为 deploy/stop，以 javap 类级注解 udc/runtime 为准) | udcAppDesigner, udcSystemAdmin（方法级 HasRole 常量） | deployNormal/deployForm/deployStop/authAccessUrl/expectDeployTime/statistics |
| DeploymentController | `udc/deployment` | udcAppDesigner, udcSystemAdmin, OpsAdmin, BpmSystemManager | appOnlineNew/latestTestInfo/getAppReadyStatus/appDeltaDeploy/restartApp |
| PageLayoutController | `udc/page-layout` | udcAppDesigner, udcSystemAdmin | 页面外框 CRUD/select |
| PageInfoController | `udc/page-info` | udcAppDesigner, udcSystemAdmin | 页面信息 CRUD/selectListByConditions |
| PageTemplateController | `udc/page-template` | UNVERIFIED（未读类级 HasRole） | 页面模板 |
| PageTemplatePublishedController | `udc/page-template/published` | udcRootOrgAdmin, udcAppDesigner, udcSystemAdmin | 已发布模板 |
| PageTemplateClassController | `udc/page-template-class` | UNVERIFIED | 模板分类 |

## 3. 基础设置 op 清单（主 store chunk 原文）

来源: `udc-pod-chunks/src_redux_store_ts.14dc061e.js`（2.45MB）。GraphQL 调用形态: POST `/service/udc/graphql`，body=`{operationName, query, variables}`，path op 变量在 `path`、body op 在 `body`。

| op | paramsKey | paramsType | params | 关键 queryFields |
|---|---|---|---|---|
| udcApplicationGet | path | udcApplicationGetInputPath | `{id}` | content{ id name caption sourceType terminalType portalId guid hostAppName featureType enableRelationEntitySelect enableEditEntityTableName copVersion publishState } |
| udcApplicationDetailGet | path | udcApplicationDetailGetInputPath | `{id}` | content{ icon iconBgColor caption name id appFrame categoryId description style terminalType publishState featureType pcAppModel mobileAppModel pcThumbnail mobileThumbnail sourceType minResolution portalId appVersion scalabilityOptionId createTime guid copVersion } |
| udcApplicationAppVersionAppGuidPost | path | ...InputPath（op 名与类型名不一致, 按 chunk 原文） | `{appGuid}` | content{ id appId appVersion showVersion state failReason deployType deployTime appName } |
| udcApplicationCopyGet | path | udcApplicationCopyGetInputPath | `{deployDto}`（chunk 原文如此, 语义 UNVERIFIED） | content |
| udcApplicationIsLastVersionAppGet | path | ...InputPath | `{appId}` | content |
| udcApplicationRenewalAppEditingTimeGet | path | ...InputPath | `{id}` | content |
| udcApplicationMultiVersionPost | body | ...InputBody | `{searchDto}` | content |
| udcApplicationSearchNewWithVersionListPost | body | ...InputBody | （未截到） | content{ appVersion basePackage caption description icon iconBgColor id name publishState sourceType terminalType creator guid versionList copVersion isCreator collaboration enableMultipleVersion udcRootOrgAdmin roleControlResource{appCopy appCreate appDelete appDesign appExport appImport appPublish ...} } |
| udcApplicationVersionPlatformServiceGet | path(原样) | udcApplicationVersionPlatformServiceGetInputBody | `{deployDto}` | content |
| udcCollaborationAppGet | path | udcCollaborationAppGetInputPath | `{appId...}` | content{ appId guid id isCreator memberId memberName role } |
| udcDataTypeDataTypesByAppIdAppGet | path | ...InputPath | `{appId}` | content{ caption name order enable*开关位... } |
| udcEntitySelectAllByAppidAppGet | path | ...InputPath | `{appId}` | content{ id name caption orderNo category features attributeSetIds multiplicity entityGroup parentEntityId publishState originalId linkageExtFiled ... } |
| udcEntityGroupSelectByAppidAppGet | path | ...InputPath | `{appId}` | content{ caption id orderNo preset publishState } |
| udcEntityPrimarySelectByAppidAppGet | path | ...InputPath | `{appId}` | content{ appId caption id } |
| udcMetaDataSelectAppByIdPost | body | ...InputBody | `{appId, searchType:["ENTITY"]}` | content{ id fullName name caption appId udcApp hostAppName entityMetaDataDtos{ id fullName name caption stereotype features parentEntityId appName appId hasChildren entityType multiplicity } } |
| udcFeatureListGet | body | udcEntityBatchDeletePostInputBody（chunk 原文如此，疑似 store 内 paramsType 复用 bug, UNVERIFIED） | 未截到 | content{ id name caption description order configuration attributeSet attributes{...} } |
| udcDeductionMapAppAppGet | path | ...InputPath | `{appId}` | content{ appId id caption } |
| udcDeploymentAppReadyStatePost | body | ...InputBody | `{appId}` | content |
| udcDeploymentLatestTestInfoPost | body | ...InputBody | `{appId}` | content |
| udcRuntimeAuthAccessUrlPost | body | ...InputBody | `{appName}` | content |
| udcManagerRequestStatusRequestGet | path | ...InputPath | 路径参数 | content |

### 活体验证（curl 实测, GraphQL POST）
| op | 变量 | code | message | 结果 |
|---|---|---|---|---|
| udcApplicationDetailGet | path:{id:8704025620829192834} | **BOOT_0000** | SUCCESS | content: id/name=caption 数据迁移/sourceType NORMAL/terminalType ALL/featureType BUSINESS/publishState UNPUBLISH/appFrame 0/guid 2275741415570096882/copVersion 5.3 |
| udcApplicationGet | path:{id:同上} | **BOOT_0000** | SUCCESS | content: id name caption sourceType terminalType publishState |
| udcPageInfoSearchNoPagePost | body:{params:{appId,urlType:"CUSTOM"},sort...} | BOOT_4000 | DB Error | 带 urlType=CUSTOM 报 DB Error；**去掉 urlType 键**（body:{params:{appId},sort:{orders:[{direction:ASC,property:createTime}]}}）→ **BOOT_0000 SUCCESS**，返回该应用页面行: `{id:8643109752427203840, caption:"导入导出模板管理", pageUrl:"_excelSetting", sourceType:"PRESET"}`, `{id:5175227629061096197, caption:"数据源配置信息列表页", pageUrl:"sjypzxxListPage", sourceType:"TEMPLATE"}` 等 |
| udcPageLayoutDetailGet | path:{id:6401563406455381090(冒烟分组id)} | **UDC_PAGE_0025** | The page outline does not exist | 说明冒烟分组 id 不是 pageLayout id；该应用 pageLayout 列表为空（下节） |
| udcPageLayoutSelectListByConditionsPost | body:{params:{appId},pageInfo} | **BOOT_0000** | SUCCESS | content: [] （该应用无 LAYOUT 外框页） |
| udcPageLayoutDesignerSelectDetailListByConditionsPost | 同上 | **BOOT_0000** | SUCCESS | content: [] |
| udcPageTemplatePublishedSearch | body:{params:{appId,classId:""},pageInfo} | **BOOT_1001** | 请指定模板类别 | 缺模板类别入参；未再猜参数（纪律） |

## 4. 页面字典 op 清单 + DB 现状

### 4.1 op（chunk 原文）
| op | paramsKey | 完整 GraphQL 骨架（chunk 原文） |
|---|---|---|
| udcPageLayoutDetailGet | path | `query udcPageLayoutDetailGet($path: udcPageLayoutDetailGetInputPath){ udcPageLayoutDetailGet(path:$path){ code data{ content{ pageSchema inParams inPortletParams defaultPlan caption pageUrl } } message status } }` |
| udcPageLayoutSelectListByConditionsPost | body | `mutation ...($body: ...InputBody){ ...Post(body:$body){ code message status data{ content{ createTime caption description relationGroupId pageUrl sourceType templateType publishState guid id terminalType originalId } } } }` |
| udcPageLayoutDesignerSelectDetailListByConditionsPost | body | content{ pageSchema inParams outParameters inPortletParams appId createTime relationGroupId caption description pageUrl terminalType sortNo sourceType templateType referConfigParameters publishState id guid defaultPlan designerVersion isDraftPage } |
| udcPageLayoutRelationInfoIdPost | body | `mutation udcPageLayoutRelationInfoIdPost($body:...InputBody){...content{ appId caption description pageUrl sourceType pageLayoutItems{ actionType sourceId terminalType id guid } curTerminalType }}` |
| udcPageTemplatePublishedSearch | body | content{ appId appGuid appCaption caption classId defaultOpenType creator creator___displayname{name} createTime description guid id inParams microFlows name pageSchema pageType pageUrl relationGroupId sortNo sourceId sourceType storageKey templateVariable urlType templateType stereotype entityTypeTag } + pageInfo{ needTotal ... } |
| udcPageTemplateClassSelectTreeCategoryGet | path | content{ childList{id name childList{...深拷贝 7 层嵌套...}} } |
| udcPageInfoSearchNoPagePost | body | content{ caption pageUrl id sourceType }（另一调用点: content{ appId caption defaultOpenType description groupId guid id name pageType pageUrl relationGroupId sortNo urlType }） |

### 4.2 MySQL udc_page_template_published 现状
- **UNEXECUTED**: DB 查询被用户拒绝（pymysql SHOW COLUMNS / SELECT 均未执行）。
- 由活体 GraphQL 替代取证: `udcPageLayoutSelectListByConditionsPost` 与 `DesignerSelectDetailListByConditionsPost` 对该 appId 返回 **空列表**（BOOT_0000）→ 该应用**没有 LAYOUT 外框页/已发布页面模板**；`udcPageInfoSearchNoPagePost` 返回 PRESET/TEMPLATE 页面行（如 sjypzxxListPage）→ 页面现状 = 预置+模板列表页，无自定义外框。

## 5. deployDto 字段清单（前端拼装原文 + DTO 常量池）

### 5.1 前端 chunk 原文（chunk 原文）
主 store 内所有构建调用均为透传: `params:{deployDto:e}`（e 为调用方拼装对象），实测拼装点:
- RELEASE 全量构建: `(0,o.oB)({projectType:"ALL", terminalType:"ALL", deployType:"RELEASE", appId:t.id, generateLog:true|e})`（4 处: 测试构建弹窗/重新构建/发布）
- DELTA 前端增量: `(0,d.u)({deployType:"DELTA", appId, projectType:"FRONTEND", terminalType:"ALL"})`
- 页面调试: `(0,A.D)({appId, projectType:"FRONTEND", terminalType:a})`（a=PC/MOBILE）
- udcDeploymentAppOnlineNewPost: `params:{...e, deployType:"ON_ONLINE"}`

### 5.2 后端 DTO 字段（udc-common jar class 常量池, 已解压证据）
`DeployNormalDto extends DeployParamDto`（javap 签名: `deployNormal(DeployNormalDto): SingleResponse<DeployParamDto>`）:
- **DeployParamDto**: `appId:Long`、`deployType:String`（枚举 RELEASE/DELTA/ON_ONLINE/...）、`projectType:String`（ProjectTypeEnum, 取值 ALL/FRONTEND 等）、`terminalType:String`（TerminalTypeEnum, 取值 ALL/PC/MOBILE）、`deployId:Long`、`pushEnv:String`（CtpSystemEnvEnum test/prod/system）、`extraParamMap:Map`
- **DeployNormalDto 附加**: `generateLog:boolean`、`lockCompatibility:boolean`、`entityFullNameCondition:Map<String,String>`（propName/propValue 形态）
- 响应 content 回显: udcRuntimeDeployNormalPost → `{appId, deployId, deployType, projectType, terminalType}`；udcRuntimeDeployPost → `{appId, clearSandboxData, copyright, debugMode, deployId, deployType, openSandbox, projectType}`（chunk 原文 queryFields；clearSandboxData/openSandbox/debugMode/copyright 字段在 jar 中未在 517 的 DeployNormalDto 常量池出现 → **UNVERIFIED，可能是 udcRuntimeDeployPost 独立入参形态**）
- 错误码样例: `UDC_DEPLOY_0002`（前端 catch 特判, 构建后触发重新构建逻辑）
- 状态枚举（前端内联）: NONE/STOP/RUNNING/PENDING/FAILED/UNKNOWN

未触发任何构建（纪律遵守）。

## 6. UNVERIFIED / 失败项
1. MySQL `udc_page_template_published` 直查: 用户拒绝执行 → 未取证列名/行数；用活体 GraphQL 替代（§4.2）。
2. `udcPageTemplatePublishedSearch` 成功形态: 需"模板类别"(classId 非空)入参，本次未猜参数 → 仅证明参数校验路径 BOOT_1001。
3. `udcFeatureListGet` 的 paramsType 写成了 `udcEntityBatchDeletePostInputBody`（chunk 原文），疑似前端 store bug 或 paramsType 宽松 → UNVERIFIED。
4. `udcApplicationCopyGet` 的 params `{deployDto:e}`（chunk 原文）语义不明（复制应用为何带 deployDto 变量名）→ UNVERIFIED。
5. udcRuntimeDeployPost 的 clearSandboxData/openSandbox/debugMode/copyright 字段在 517 版 jar 的 DeployFormDto 常量池（businessType/sandboxId/republish）不完全对应 → 该 op 的入参形态 UNVERIFIED。
6. DeployController 类级 @RestApi value/group 的中文名在 javap 里是 GBK 乱码未逐条还原 → 仅确认类级 @RequestMapping="udc/runtime" 与方法级 HasRole(udcAppDesigner, udcSystemAdmin)。
7. PageTemplateController / PageTemplateClassController 类级 @HasRole 未读 → UNVERIFIED。
8. udcPageLayoutDetailGet 传冒烟分组 id 得 UDC_PAGE_0025（对象不存在），真实 pageLayout id 未探（避免写操作）。

## 活体验证 code 汇总
- BOOT_0000: udcApplicationDetailGet / udcApplicationGet / udcPageInfoSearchNoPagePost(去 urlType) / udcPageLayoutSelectListByConditionsPost / udcPageLayoutDesignerSelectDetailListByConditionsPost
- 非成功: UDC_PAGE_0025(udcPageLayoutDetailGet, 无此外框) / BOOT_1001(udcPageTemplatePublishedSearch, 缺类别) / BOOT_4000(udcPageInfoSearchNoPagePost 带 urlType)
- datadictionary GET: HTTP 200 text/html（无信封）
