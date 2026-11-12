---
name: seeyon-udc-design-time-build
description: Use when building UDC entities/apps and metadata on the live designer.
version: 1.8.0
author: operator-a, Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [seeyon, udc, low-code, design-time, deploy, entity, attribute, build, physical-table]
    related_skills: [seeyon-udc-runtime, seeyon-low-code-environment]
---

# Seeyon UDC 设计态搭建（实体/属性/构建）

> 节点数据补全（「所选数据已变更」红字两类根因 / 候选集权威源 / 重写器顺序 / 编辑锁假阴性 / 跨应用引用处置）见 references/microflow-node-data-completion.md。

## When to Use

- 在活的 test2/uat 设计器里通过 API **创建**实体、字段、**页面**、应用，而不是本地手拼 8 个 Java 文件（本地骨架只是审计参照，不是交付）。
- 用户点了"立即构建/发布"后，验证物理表真建到库里没有。
- 把"建实体→建属性→建页(LIST+DETAIL)→RELEASE 构建"整条写链路固化成可复用产物。
- 要弄清设计器某个 tab/功能调什么接口（前端页面 → 调用链 → 后端代码）。

## 探测隔离铁律（用户红线，先于一切写操作）

- "建一个测试应用"永远指**平台级独立应用**（自己的 appGuid，走 `POST /service/udc/application` 平铺 ApplicationDto），绝不在任何现网业务应用内建实体/建页面/触发部署。用户授权过一次不等于对每个宿主应用都授权；动手前先向用户复述目标应用与范围。
- 在业务应用内建实体+跑 deploy-normal 会把该应用推新版本（编译→artifactory→沙箱重启）——即使无业务数据写入也是真实变更，用户视为污染。探测残留（UNPUBLISH 实体）必须清理：实体删除走 GraphQL `mutation udcEntityDeletePost($body: udcEntityDeletePostInputBody) { udcEntityDeletePost(body: $body) { code message status data { content } } }`，body `{"id": "<实体数字id>"}`，发 `POST /service/udc/graphql`（content=1 即成功），删后 GET `/udc/entity/{id}` 回读确认。introspection 被拒，mutation 名从前端 chunk（src_redux_store_ts）提取。
- 建应用卡租户配额 `UDC_APP_0030` 时按下方配额契约处理，业务应用一个都不能动。
- **用户点名的目标应用不等于干净沙箱——先回读它的对象清单判性质再动手。** 读 `GET /service/udc/entity/primary/select-by-appid/{appId}`（或设计器实体树）看它同时装了什么：真实业务构件 + 历史探测实体混居 = 这个应用已被当过探测宿主（如 datamigration 既含 migrationPlan/migrationDatasource/fileMigration/MigrationLog 等真实迁移构件，又含 `xzh*` 探测实体）。往这种宿主里继续建只是加固既有污染，动手前把「该应用里已有 X/Y/Z，我这次要再加 A/B」复述给用户拿确认——「用那个应用建」是选宿主，不是建实体授权。`xzh*` / `zzprobe*` 一类前缀可当历史探测残留的识别标记；用户说某应用「被我删除了」时，先按上方报告节的 API 回读口径确认对象是否真的不在，别顺着删除的说法走。
- **★ 探测残留的代价是复利，不是单次：每个 `xzh*`/`zzprobe*` 对象都可能在后续构建里变成阻断项。** 残留实体自带 `domain.message.<实体小写>` 包的 import（见下方「删除探测残留的连锁失败」），一旦它引用的微流程被清、包不再生成，整个应用构建就炸。⇒ 探测用的实体/微流程/事件只在**专用试验应用**里建；已在业务应用里留下的，清理时按依赖图逆序删（先微流程/事件、再实体），并在删前查 `udc_event`/`udc_attribute`/`data_schema` 三处引用。用户为此亲自手工删过几十条，并明确表达过不满——这不是“下次注意”级别的事。

核心认知（用户反复纠正过的重点）：本地生成的 8 类 Java 文件 **不等于** 平台产物。真正的交付 = 平台设计态落库 + RELEASE 构建后物理表 DDL。本地骨架只在 `docs/audit` 当证据，不进 git 当成果。

## 通道优先级（用户标准，先于选型）

**REST/GraphQL 是主路径，CDP 是兜底。** 用户原话口径：「这些最后都会通过 rest 接口实现，而不是 cdp；cdp 是在实在没招了才推进的」。落地：

1. 先找**服务端契约**（`_api_full.json` / javap / 前端 bundle 里的 op 描述），把写链做成可重跑的 urllib/curl 脚本。
2. CDP 只用于**取证与兜底**：抓设计器真实 Network 请求定形未明的按钮通道、读 redux 内存态、自动点 UI 表单（如建应用这种无 REST 可靠通道的环节）。
3. **每次用 CDP 拿到的东西，回头都要落成 REST 形态**——CDP 只产出「真相」，REST 脚本才是可重复交付物。收口报告里明确说明哪一步用了 CDP、哪一步已回到 REST。
4. 宁可多花一步把 REST 通道试通（用报错原文当参数字典），也别用 CDP 把页面点一遍就交。CDP 点出来的结果无法被人以 API 复现，不算完成的写链。

## 关键区分：两条不同链路，别混

1. **实体级 publish（要密码）**：`PublishStateController.update(PublishStateUpdateDto)`，校验链 `entityClassName → ids[] → password`（`password must not be null`）。这是设计器"发布"弹窗的确认密码，**不在任何 Nacos 配置/凭据文件里**。找它是死路，方向就错了。
2. **应用级 RELEASE/TEST 构建（sandbox 流水线，无密码）**：`DeployController.deployNormal(DeployNormalDto)` 是已核实的后端构建操作契约。除非当前目标版本设计器的 Network/CDP 请求已逐字捕获并比对 method、path、body、前置保存和响应处理，否则不得声称这是页面“构建”按钮实际通道，也不得用 REST 请求冒充用户要求的页面按钮操作。执行体静态定位为 `boot-starter-sandbox` 的 `UdcAppDeployService`（PipelineProperties 流水线 + SandboxK8sService + Redis 锁 + MQ 异步）；实际运行仍以目标版本和 deploy record 回读确认。

判定：先区分实体级 publish、应用级 TEST/RELEASE build、ON_ONLINE 上线发布和设计器页面按钮。要证明页面按钮通道，先用登录态 CDP 捕获真实 Network 请求并核对完整调用链；没有抓包时标 `UNVERIFIED`，不能把相似 endpoint 推定为等价。

## 微流程/页面事件 API 保存通道（udcMicroflowUpdatePost + submitPage，全链 LIVE）

- 微流程保存 = `udcMicroflowUpdatePost`（/service/udc/graphql），mutation 名从前端 chunk grep `fieldType:"udcMicroflow` 提取。body 必带 `id`+`guid`（不带报 BOOT_4002 无权限）；`type/triggerType` 用 DB 数字枚举（udc_microflow_info 实值 type=0 SERVICE、triggerType=2 MANUAL），字符串拒。`dataSchema` 是 JSON **字符串**非嵌套对象。
- dataSchema 骨架 deep-copy 既有行（udc_microflow_info.data_schema），别手拼：`{sourceType, trigger(MFStartNode/MANUAL), endNode(END_NODE), nodes[]}`。
- **节点分两类，保存通≠节点合法**：后端代码生成节点 = 在锁定版本的 udc-biz jar 里能按 `autocode/JAVA/<ver>/templates/microflow/` 枚举到模板的节点（`<Type>Activity.java.ftl` 族；2.9 目录下 flat 模板 21 个 = 18 个 `<X>Activity` + CreateList/ChangeList + MicroFlowDomainService，另有嵌套子目录）；**别把节点种类数写死**（“20 种”这类硬编码会随版本漂移，且漏掉非 Activity 后缀的模板）——以落库产物 `docs/audit/artifacts/udc-biz-<ver>/_codegen_templates.json` 为权威名册，不从记忆或旧口径抄；`MESSAGE_INFO` 等 web 类节点无后端模板，生成器 switch 静默跳过——构建成功但零 Java 生成，不报错。**用 MESSAGE_INFO 只能验保存通道，不能当微流程功能验证**；需真实功能时节点必须选带模板的后端类型。**★ `messageSource=MESSAGE`（MQ 消息监听）的微流程，根 `input` 必须非空且带 `javaType`+`name`，否则构建在代码生成期崩**：报错形态 `freemarker.core.InvalidReferenceException: ... evaluated to null or missing: ==> microFlowBo.input [in template "autocode/JAVA/2.9/templates/microflow/event/BusinessEventListener.java.ftl" at line 117]`。模板机理：L117 `subscribedMessageDto?then("...MessageDto", microFlowBo.input.javaType)` 是惰性求值——真分支只取字面量不碰 input、走到 L119 `input.name?cap_first` 才炸；假分支直接求值 `input.javaType` 炸在 117:109。⇒ **两种形态（input 为 null / input 缺 javaType）都必炸**，本地校验要两条都查。平台 `checkSchema` 对此**不报**（只查必填键与类型，不查这条跨层依赖），修法是在本地模型加规则（`components/udc/microflow_model.py` 的 `_validate_message_trigger_root_input`）；EVENT/CONNECTOR 等其他 messageSource 走不同模板分支，不套这条规则。模板全清单必须从锁定版本的 udc-biz jar 按所有 `autocode/JAVA/*/templates/microflow/` 目录枚举；不能只盯住 2.9，也不能把 jar 某版本模板存在当作 test2 目标微流程已生成。
- **实体规则也走代码生成**：udc-biz jar 里有 `autocode/JAVA/2.9/templates/entityrule/`（AssignValueActivity / DefaultValueActivity / AttributeUniqueActivity / AttributeRequiredActivity / ShowMessageActivity / ruleservice.java 等）——实体规则三组（VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE）不是只存库的元数据，同样会被代码生成器翻译成 Java；「规则建了但没生成代码」的排查方向同微流程（看生成产物里有没有对应类）。
- **微流程节点参数有强类型 BO 系统**（`com.seeyon.udc.model.parser.MicroflowNodeParserFactory` javap 暴露）：`ConditionInfo`/`ConditionParam`/`ConditionRightParam`/`SelectParam`/`AttrType`/`AttrValue`/`SelectObjectAttr`/`RetrieveSortParam`/`RuleActivityParam`/`Structure`——构造 dataSchema 富结构时这些就是节点的参数类型名，比从 DB 样本反推更权威。
- **微流程只有 state=20（已发布）才进代码生成器**：构建只处理 `udc_microflow_info.state=20` 的行；state=10（草稿）的微流程构建**不报错、不生成任何 Java 类、jar 里查无 `<名>Service.class`**。验收生成是否发生：解开沙箱 pod 的 `biz jar`，看 `com/seeyon/<app>/domain/service/microflow/` 下是否出现 `<微流程name>Service.class`（带 RETRIEVE 逻辑的真实现，可 javap -c 看注入 dynamicSelectAppService 等）——构建成功但目录里没有该类 = 该微流程没被生成，回头查 state 或 schema 合法性，不要当作「构建没跑」。成熟应用（几十条微流程）的 biz jar 里每个 state=20 的微流程都有对应 `<名>Service.class`，这是判定基准。
- 页面事件绑定在 `childById[控件].events[]`（顶层 eventDefine/pageDefinedEvents 标品页同为空，别在那找）；eventDefine[] 仅登记元数据。microflow 类事件 `microFlow` 字段填 udc_microflow_info.id。改完照 submitPage 全 body 重提交，DB 回读 events[] 确认。

### 微流程 dataSchema 构造铁律（用户红线：照库里加载的内容对齐，禁止手拼）

- 先锁定主线仓库（当前产品主线是 `seeyon-agent`）；Hermes skill 只是辅助规程，不能当成主线已有实现。用户要求“先理解/先检查”时，保持只读：先审 `seeyon-agent` 当前代码和 tests，再追前端 bundle、目标版本 Controller/DTO/service、schema/parser/template 和只读样本，产出带 `path:line` 的审计；不得继续写 test2、改页面/微流程或触发构建。将旧源码、5.3.517 静态 artifact、目标 test2 镜像版本分开记录，不能跨版本拼成一条已验证链。
- 把页面保存区分为草稿与正式提交；`draft_page_schema`、`page_schema`、独立 PageDataSource、FilterPlan、FunctionNode、PageLayout 都需各自定义输入/保存/副作用/回读，不能因一个大 JSON 或单个成功响应推断对象都已同步。页面规则 FRONTEND 微流程、列表 FilterPlan、ENTITYRULE 也要分对象描述。
- 对每个节点按 `NodeType → Activity parser → 输入字段/SelectParam/作用域 → output/副作用 → 版本对应模板 → 发布态 → 运行回读` 建证据矩阵。源码字段和模板只证明静态解析/生成路径，不证明目标应用已生成或运行；将 output/NodeInfo 槽位与真实运行返回值分开写。

- **节点 JSON 逐字段从标品微流程行映射，只替换实体/DTO/ID/文案**：取一条同应用或他应用里**已生成过 Java 代码**的微流程（udc_microflow_info.data_schema）当干净模板（如 RETRIEVE+CHANGE_ENTITY 两节点的最简行），逐键深拷贝，只替换 `appName/appId/entityFullName/dtoFullName/relationEntity 数字id/条件字段/attrs`。键位集合与模板做 diff：零缺失零多余才算对齐——多一个键（如给 CONDITION 型 RETRIEVE 加 `value:None`）都可能让校验静默不过。
- **CHANGE_ENTITY 的 `attrs[]` 是富结构，不是扁平 `{name,value,DATA,T}`**：每条 attr = `{name, value, attrType}`，`attrType` 是完整属性元数据（`id=DTO.fullName.<attr>`、`fullName`、`refId`、`javaType`、`dataType`、`filterDataType/filterRelationEntity/filterType/filterFullName`、`dataI18n`、`sort`(=udc_attribute.order_no)、`description`，约 18 键）——从 `udc_attribute` 真实行映射，别手拼。`value` 按 dataType 取平台原生形态：CTPENUM=`{type:"CtpEnum",ctpEnum:{id},desc}`、引用型=`{type:"SelectParam",selectParam:{...},desc}`、表达式=`{type:"Expression",expression:{schema:...}}`、布尔/字面量=`{type:"Simple",simple:<v>,desc:<v>}`。形态不确定就全库扫 `data_schema LIKE '%CHANGE_ENTITY%'` 按 dataType 采样对齐。
- **RETRIEVE 的条件查询形态**：`fetchType:"CONDITION"` + `condition:[{type:GROUP,uuid,conditions:[{type:CONDITION,leftParam:{id:DTO.field,javaType,dto:"_x",field,desc,dataType},operator:{value:"EQ",desc:"="},rightParams:[{type:"CONTEXT_VARIABLE",value:<入参SelectParam的JSON字符串>,desc}],uuid,logicalOperator}]}]`，`sortParams:[]`、`nullHandling:"CONTINUE"`、`selectType:"DTO"`、`scope:"OBJECT"`。ID 查询形态 `fetchType:"IDS"` 用 `value` 键不用 condition。照干净模板抄，别两种混拼。
- **保存→发布→构建的正确序列**（乱序会静默无效）：① `udcMicroflowUpdatePost` resave（body 里写 `state:RELEASE` **会被 API 忽略，落库仍是 10 草稿**——这是 API 行为不是 bug，resave 的作用是刷新内容指纹）→ ② 直接 DB `UPDATE udc_microflow_info SET state=20 WHERE id=<微流程id>`（无单独「发布微流程」API 可用时）→ ③ 再 `deploy-normal`。只要 ① 改了内容指纹，构建就不会被去重跳过；只改 ② 不改内容，构建**按 metadata 指纹去重直接跳过**（响应 200 SUCCESS 但 DB 无新 deploy 记录、沙箱日志无踪迹）——"构建没跑"先查是否指纹未变，别当成构建失败。
- **触发构建后必须拿到「真的跑了」的证据再验收**：deploy-normal 返回 200 只代表入队。确认执行看沙箱 pod 日志 `BuildTask:…启动耗时:[…]MS,结果:[SUCCESS]` 或 DB `udc_deploy_record` 新增该 deployId 的行（state 0→1）；两者都没有 = 被去重/锁跳过，回到「改内容再触发」。最后才是 jar 类文件验收（上一条铁律）。
- **dataSchema 的另一权威源：`udc_microflow_preset_template` 预置模板表**（全库仅 4 行：SelectOneByThirdPartiesEntityId / SelectListByThirdPartiesEntityId / DynamicMfSearch / DynamicMfSearchCount，每行一份 `${appId}/${entityId}/${entityDtoFullName}...` 占位符的完整 dataSchema 模板，顶层键位与手工行完全一致）。构造新微流程时优先用这张表当模板（比应用既有行更干净、含 input/output/trigger/endNode 全键），占位符替换真实值即可；应用既有行只作键位交叉核对。
- **元信息分诊（规则/事件/索引/参照/字段集/BI 先全租户取证再动手；body 字典与样本值域见 `references/metadata-artifact-apis.md`）**：查某表 0 行只证明该表/当前数据范围没有样本，不能据此断言功能未启用。继续核对实际功能入口、controller/service、版本差异、功能开关、替代存储和租户/应用过滤范围；仍无证据时标 `UNKNOWN/UNVERIFIED`，不得臆造对象或写入。查到样本后也要按对应版本和对象关系逐列核验，再决定是否可复用：事件、DTO、监听微流程分属不同对象；索引通过字段 id 关联属性；字段集与属性分开；`udc_filter_plan` 是列表查询过滤方案，不是页面规则；参照和规则配置是否自动创建必须以当前版本服务实现及回读证明。

### 事件/索引/字段集/页面规则 + 事件挂动作（REST 直建，DB 回读 LIVE）

- **实体「事件」tab 的「新建事件」主链是 GraphQL `udcEventCreateWithDataPost`，不是 `udcEventPost`**（组件 77200 `createEventWithData` 逐字：`load({fieldType:"udcEventCreateWithDataPost", paramsType:"…InputBody", paramsKey:"body", params:e})`）。`udcEventPost` 是「裸事件」形态，两者都在 catalog 但 tab 主链是前者——按名字猜成 `udcEventPost` 是错映射（曾犯）。事件 body 与裸事件结构**不同**：`{appId, caption, name, source:"MICRO_FLOW", sourceId:<实体id>, eventDataType:"OBJECT", description, eventDataList:{appId,name,caption,source:"MICRO_FLOW_MESSAGE",sourceId:<实体id>,attributes:[…]}, messageType}`。
  - `eventDataList.attributes[]` 每条来自**微流程节点输出参数**（`selectParam`）：`{name:outputName, caption:description, dataType, dataTypeCategory, type, description:""}`；`dataType` 规则 = Dto/Enum 类型取 `javaType` 否则取 `dataType` 原值；`type` 规则 = `selectParam.type.toUpperCase()=="ARRAY" ? "LIST" : "OBJECT"`。
  - **字面值从 bundle 挖，不臆造**：`eventDataType:d.pe.Object` 是符号引用，`pe` = module 65420 的 dataType 枚举，其 `Object` 键值实为 **`"OBJECT"`**（不是 `"Object"`）。同枚举即 35 值 dataType 全集（SELECTPEOPLE/CURRENCY/ATTACHMENT/CTPENUM/…），与 deployment 快照的 11 值 `DATATYPES` **非同源**（快照=已落库子集），两处独立登记勿互覆盖（见 `attribute_semantics.BUNDLE_DATATYPE_ENUM`）。
- **事件挂动作的绑定位置在监听微流程的 `data_schema.trigger`，不在 `udc_event` 表**（该表无指向微流程的列）：动作 = 新建 `trigger_type=0` 监听微流程，`trigger.type=BUSINESS_EVENT` + `messageInfo`。自定义事件走 MESSAGE 源（topic=`UDC_<APPNAME大写>_MQ`、eventDataFullName=`com.seeyon.<appName>.dto.microflow.message.<Pascal(事件name)>`）；标准生命周期事件走 EVENT 源（8 类：TransactionSuccessUpdate/Create/Delete、AfterCreate/Update/Delete、BeforeCreate/Update）。两形态照 `udc_microflow_info` 里 `trigger_type=0` 样本行抄，别自造。
- **新建微流程走 REST `POST /service/udc/microflow/create`（字符串枚举 `triggerType=BUSINESS_EVENT|MANUAL|SCHEDULE`、`type=SERVICE`、`state=DRAFT`），与 `udcMicroflowUpdatePost`（GraphQL 数字枚举）是两套契约，别互套**；DTO 模板用 `GET /service/udc/microflow/findById/{id}`（方法级注解路径——按 Java 方法名拼 URL 会 404）。create 是**扁平 DTO body**（`{appId,name,caption,type,triggerType,groupType,description,nodes:[],sourceType:"PAGE"}`，不包 graphql 外套），返回 `data.content` = **id 字符串**；**create 后 `data_schema` 落库为 NULL**（骨架不在 create 生成）——必须 `findById` 回读 DTO、补完整 schema 再 `update`（与 GraphQL `udcMicroflowCreatePost` 空基座同病）。**REST `update` 同样吃 findById 回读的全量 DTO 原样回传**（含字符串枚举形态）；配对的读面 `GET /udc/microflow/findById/{id}` 返回完整 DTO（dataSchema 是 JSON 字符串）。另有 GraphQL `udcMicroflowCreatePost`（接受字符串枚举 type:"CUSTOM"/triggerType:"MANUAL"，拖拉拽链路用 CUSTOM），⚠️ 空基座 create 成功但 dataSchema 落库为 null，设计器打开报「微流程数据加载失败」——create 后必须 findById 回读、补照真实微流程逐字段对齐的 dataSchema（input/output 的 name/desc 必填，别留空）再 update 回传（详见 references/designer-frontend-call-chain.md「写链 v4」）。
- **微流程三触发族的创建模型 = 前端 `ZK` 类型表 + `lZ()` body（别手拼、别无脑用同一个 type/triggerType）**：`createType → {type, triggerType, caption}` 是**矩阵不是自由组合**——`customServicedefinition`=CUSTOM/MANUAL「自定义微流程」、`customEventmonitor`=CUSTOM/BUSINESS_EVENT「自定义事件监听」、`customTimingtask`=CUSTOM/SCHEDULE「自定义定时任务」、`servicedefinition/eventmonitor/timingtask`=SERVICE 型的 MANUAL/BUSINESS_EVENT/SCHEDULE（=标准微流程）、`frontend`/`frontendfunction`/`entityrule` 各自独立。前端 UI 的「微流程类型=自定义」才走 custom*（否则是可接手工开发微流程的标准型）。建前先过重名校验 **`udcMicroflowCheckMicroFlowCaptionPost`**（`content=false` 才创建，true=重名）。**create 时直接带 dataSchema 即可一次建成**（实测带全 lZ 形状 + dataSchema 落库即有值，不必二次 update 补）。SCHEDULE 必须在 trigger 上补 **`scheduleCronRule`**（`{jobCode,jobCaption,cronRules:[{cycleType,startTime,endTime,rotationType,type,value}]}` + `isCompleted:true`，cycleType ∈ YEAR/MONTH/WEEK/DAY/HOUR/SIMPLE，非 SIMPLE 时 type ∈ FIRST/LAST/ANY，ANY 带 `value`）；BUSINESS_EVENT 必须补 **`trigger.messageInfo`**（required，**候选源是选择器自带的 `udcMicroflowFilterEventPost`，不是「现有事件对象列表」那两个 query**：body `{appId, id:<微流程id>, sourceTypes:["ENTITY"], eventTypes:["ENTITY_EVENT"]}` → 返回实体派生的生命周期事件；见 references/designer-frontend-call-chain.md「写链 v5」⑤ 与「事件选择器候选源」节。**事件选择器有两个 tab，候选源是两套不同 interface**：①**『应用内』**=`udcMicroflowFilterEventPost` body `{appId, id:<微流程id>, sourceTypes:["ENTITY"], eventTypes:["ENTITY_EVENT"]}`（该 tab 枚举窄到只有 `ENTITY`/`ENTITY_EVENT`，塞别的值报 `BOOT_3002 No enum constant`）→ 实体派生的生命周期事件；②**『应用间』**=先 `udcMicroflowSearchAppsPost` 选应用、再 `udcMicroflowFilterMqPost` body `{appId, appName, microFlowId}` → 跨应用 MQ 消息——**BPM 流程事件（流程发起/结束/回退/终止…）、组织模型、消息中心、连接器回调全在这**，不在『应用内』tab。**别因为『应用内』枚举塞不进 BPM 就断定 BPM 不可选**（也见 references/designer-frontend-call-chain.md「写链 v5」⑤）。只有确实要自建事件对象时才走：应用间 `udcMicroflowCreateMessagePost`+`source:"MICRO_FLOW_MESSAGE"`、应用内 `udcDataTransferObjectCreateDtoPost`+`source:"MICRO_FLOW_EVENT"`，body 的 `attributes[]` **不能为空**；`udcMicroflowSearchMicroFlowEventAppGet`/`udcMicroflowSearchMicroFlowMessageAppGet` 只列**已落库的**事件/消息对象，它们返回 0 条**不代表选择器为空**）。建成的微流程落 `state=RELEASE / publishState=UNPUBLISH`（设计态可见、未上线）。全表、body 模板与值域见 `references/designer-frontend-call-chain.md` 的「写链 v5」节。
- **标品（`type:SERVICE`）微流程 + 活动节点（`type:"ACTIVITY"`）编排**：用户「建标品的」= 新建表单「标准微流程」（`servicedefinition/eventmonitor/timingtask` → SERVICE/MANUAL|BUSINESS_EVENT|SCHEDULE），与 `type:CUSTOM`（自定义/接手工开发）相对；**标品才用活动节点编排**。创建同 `udcMicroflowCreatePost`（键位照 v5 `lZ`，仅 `type:"SERVICE"`）
  - **★ 说“标准/标品微流程”就必须落 `type=0`，这是用户反复纠正过的红线**：REST `POST /service/udc/microflow/create` 的 body 里 `type:"SERVICE"`（**不是 CUSTOM**）、`serviceInterface:"CustomMicroFlowAppService"`、`state:"DRAFT"`、`versionCode:100`、`openApi:"STOP"`、`restApi:"DISABLED"`。落库后立即 DB 回读断言 **`type==0 && state==10 && service_interface=='CustomMicroFlowAppService'`**，三项任一不符就是建错了——**别信 create 返回的 BOOT_0000**。传 `type:"CUSTOM"` 会安静落成 `type=3`（自定义微流程），外观与标准流程几乎一样、checkSchema 也会过，只有 build 阶段表现不同，事后极难察觉。
  - **这条已因重复重犯被提升为硬门槛**：用户说「自定义微流程而非标准节点微流程」= 同一错误第二次发生。create 之后、写 schema 之前，先把 `type/state/service_interface` 三项打出来核对；不符立刻删掉重建，**不要用 update 去改 type**（update 吃回读 DTO，改 type 会连带其他字段，风险高于重建）。
  - **标准微流程 dataSchema 的真实顶层形状：`input`/`output` 可以是 `null`**（实测 `type=0` 成熟样本如此），顶层键固定 `{input, output, endNode, sourceType, trigger, nodes}`。**给 `output` 填空对象 `{}` 反而会招 `root.output.id PROPERTY_IS_REQUIRED`** —— 要么给完整 DTO 引用（`id/javaType/appName/dataType/type/desc/name`），要么直接 `null`。`trigger` 最简形态 `{caption,description,id,nodeId:"MFStartNode",input:null,output:null,type:"MANUAL"}`。
  - **RETRIEVE_ARRAY 节点的必填集（checkSchema 实证，缺一个报一条）**：`actionType/caption/nodeId/type:"ACTIVITY"`、`structure{key,id,label,dataType,entity,dtoType,udcApp,fullName,relationEntity,methodLegal}`、`fetchType`（值域枚举，取 `"CONDITION"`）、`size`（**整数**，如 `999`）、`output`（DTO 引用，`type:"ARRAY"`）、`app{appId,appName,caption,inApp,udcApp,dynamicDependency}`、`methodLegal{available,complexCondition,seniorMethod,serviceType,interfaceClassFullName}`、`scope:"ARRAY"`、`selectType:"DTO"`、`pageSearch:"false"`、`variableTitle`、`sortParams:[]`、`condition:[{type:"GROUP",uuid,conditions:[]}]`。取一条同应用 `type=0 AND state=20 AND data_schema LIKE '%RETRIEVE_ARRAY%'` 的成熟行逐键对照最稳。

  以下为既有条目，保持：，**`trigger.nodeId` 按触发族定**：MANUAL（服务定义）必须 `MFStartNode`（预置 `SERVICE_<nanoid6>` 会挡住 aT 自动补 MFStartNode，入参面板空白）；SCHEDULE/BUSINESS_EVENT 用 `${type}_${nanoid6}`（真实样本 `MigrationScheduler`=`SERVICE_Et34XS`）。MANUAL 触发直接带 `paramType/basic/output` 入参。**活动节点目录权威源 = 前端 module-83128（90 个 `export const X={group:"base",name,type,settings}`），不是后端 `udcMicroflowFindNodesGet`**（该 op 的 GraphQL 类型名在本版本 schema 不存在 + introspection 被拒）；节点公共字段 `nodeId/name/type/caption/description/runAfter/input/output/isCompleted/actionType`，容器 `ACTIVITY`、分支 `BRANCH`。真实节点结构、常用 actionType 清单见 `references/designer-frontend-call-chain.md` 的「写链 v6」「写链 v7」节。**画布节点是否显示红字「设置节点数据」由 `nodeDesc(node)` 是否为空决定**（不是 `isCompleted`）：RETRIEVE 需 `title`+`output`、**RETRIEVE_ARRAY 需 `variableTitle`（★不是 title）**+`output`、DATA_MAPPING 需 `structure.id`；只写 `{nodeId,type,caption,actionType}` 的空结构会一直红字。**只堆节点不配 `condition`/`sortParams`/`mappingRule` = 空转**——过滤条件/排序/字段映射的真实结构见 v7 节。完整字段契约、出参 `entityObject` 必填、实体 DTO 硬命名（`com.seeyon.<appName>.dto.<Entity>Dto`）、事件选择 `entityId` 必须 Long 的坑同见 v6/v7 节。
- **★「形状对」≠「合法」：每个节点字段都有值域/依赖/联动约束，写前必须过约束（用户核心纠正「你知道渲染模式但不知道限制条件，导致生成的错误」）**：操作符值域（`NOTNULL` 而非 `IS_NOT_NULL`）、`dataType→operator` 匹配（BOOLEAN 只 EQ/NEQ、ATTACHMENT 只 NULL/NOTNULL）、`rightParams` 个数（NULL/NOTNULL 空、BETWEEN 两个）、`mappingMode` 值域、空 mappings=空转。**权威源是反编译后端 Activity 解析器，不是前端 chunk**：前端只暴露面板选项，`parseActivityNode()` 里 `NodeUtils.getXxx("f", node, <required>, ...)` 的 required 标志才是字段必填/依赖的权威；`boot-starter-condition` jar 的 `OperatorEnum` 才是操作符权威（22 个，比前端多 `ZERO`/`NOTZERO`，`NEQ` 值是 `<>` 非 `!=`）。CFR 逐类反编译 + 提取配方、被后端纠正的前端推断值对照表（`mappingRows`≠`mappings`、`REFERENCE|CONSTANT`≠`FieldCopy`、`ENTITY|DTO`≠`ENTITY_OBJECT`、`pageSearch:"false"` 字符串布尔）、条件 GROUP/CONDITION 嵌套结构、DATA_MAPPING `mappingRule` 字节级实证 —— 全在 `references/microflow-node-authoritative-constraints.md`。**把约束落成离线校验器**（`components/udc/microflow_model.py` 的 `parse_data_schema` + `CONDITION_*`/`MAPPING_MODES` 常量 + `components/udc/microflow_constraints.py` 节点必填/枚举模型 + 测试），生成节点后、POST 前先跑校验清空 errors，别靠记忆逐字段对。终态验收 = 仅凭约束从零手写多节点微流程，`parse_data_schema(...).status()=="PASS"`（`tests/udc/test_author_from_constraints.py`）。同类教训泛化：面板字段空/查询返 0/枚举拒值都只证「这条探测路径」不通，不证功能不存在——先枚举全部 tab/通道再下结论。
- **create 前过 `POST /service/udc/microflow/checkSchema`（同 body）**：`content.check=true, errors=0` 才创建；它逐节点给 `nodeId/path/errorCode=DATA_INVALID/errorType=PARSE`（实测抓出 IDS 型 RETRIEVE 的 `value` 缺 `{"type":"SelectParam","selectParam":{...}}` 外层包装），比 create 后翻错误便宜。**★ 它对「必填/类型/枚举」有效，对「语义值域」无效——两个方向都要记**：
  - **有效面（LIVE 实测 4/4 命中）**：`PROPERTY_IS_REQUIRED`（root.output.id 缺、节点 `structure` 缺）、`NOT_MATCH_ENUM`（`fetchType` 传了值域外的字符串）、`NOT_INTEGER`（`size` 传 `"100"` 字符串）——它确实逐节点查必填键与类型。
  - **无效面（LIVE 负向对照 4/4 全过）**：注入非法 `actionType`、非法 `operator.name`、非法 `trigger.paramType`、`nodes=[]`，一律返回 `check:true, errors:0`——这些都是自由字符串字段，不查值域。
  - ⇒ 结构/值域闸门仍是**本地约束模型**（`parse_data_schema` + `validate_node_fields`）。但别因为「它是浅校验」就跳过它：必填缺失这一类它比本地模型还全（`root.output.id`、节点 `structure` 本地模型都不查）。
- **本地校验器自身也会崩，崩了会静默放行**：`CONVERT_DATA` 节点的 `convertType` 在真实库里可能是 `{type,dataType,...}` 对象而非枚举字符串，直接做 `ct not in frozenset(...)` 抛 `TypeError: unhashable type: 'dict'`，把整条微流程的解析打断——上层若 `except` 兜住就变成「校验没跑」的假阴性。凡对 `raw.get(<字段>)` 做**集合成员判定**前先 `isinstance(v, str)` 收窄；遇到对象形态记 warning 不判硬错。批量校验全应用微流程时，先确认「解析异常」不是校验器自己崩，再谈配置对错。
- **★ `checkSchema` 的业务成功码与校验结论是两个字段（踩过的假放行）**：校验不通过时响应仍是 `HTTP 200` + `code:"BOOT_0000"` + `status:0`，真正结论只在 **`data.content`**：`{check:false, errors:4, errorMessage:[...]}`。
  判据必须写 `resp.data.content.check is True`，**不能只判 `status==0`**——只判信封会把 4 条必填错误当成功继续 `update`，把必炸的 schema 硬写进库。写任何「checkSchema → update」序列时，`check=false` 一律中止并打印 `errorMessage[].path/propertyKey/errorCode`（那是最省事的字段字典）。
  **「形状对、约束错」会静默通过 create+update 并落库**；真正的结构/值域闸门是**本地约束模型**（`components/udc/microflow_model.py` 的 `parse_data_schema` + `components/udc/microflow_constraints.py` 的 `validate_node_fields`），生成前置必须跑它清空 errors，别把 checkSchema 的绿灯当合法性证明。
- **入参/出参定义结构（用户截图实证的前端校验，别再漏）**：设计器参数 tab 保存时前端校验 `desc`（参数名称）必填——报错形态 `errorFields:[{errors:["请输入参数名称"], name:["desc"]}]`，。**但面板绑定的不是 `dataSchema.input/output`**（见下方第 1 条子项）——只写 `input.desc` 会出现「update 返回 content=1、回读也确有值，面板入参名称仍空白」：写的是后端正规键，不是面板绑定键。权威结构从画布组件源码挖（module-18573 参数选择器 / module-17642 校验 / module-83128 字段 schema / module-64734 参数 Card + 保存按钮 / module-37302 Uu 解析 / module-18640 aT+RF thunk / module-65420 pe 枚举）：
  - **绑定链（LIVE 修正，此前按 input 写是错的）**：入参 Card 的 formData = `flowNodes["MFStartNode"]` 去掉 `{id,nodeId,type,actionType,canRollback,runAfter}`，出参 Card 同法取 `flowNodes["MFEndNode"]`（module-64734 的 `let k / let V = useMemo(...,[flowNodes?.[D]])`）；`flowNodes` 由 module-37302 `Uu` 从 dataSchema 装出（`flowNodes[trigger.nodeId]=clone(trigger)`、`nodes.push(endNode)`），module-18640 `aT` 再执行 `B.endNode={...B.endNode, desc: output?.desc, hasPagination: output?.hasPagination}`。⇒ **入参定义读 `dataSchema.trigger`；出参定义读 `dataSchema.endNode`（其 desc 被 `output.desc` 覆盖）**。面板显示空白但库里明明有值 = 写错了绑定键。排查法：先在渲染模块找 formData 的 `useMemo` 派生源，再回溯 `Uu`/`aT` 的构造链定位真正该写的键。
  - `paramType` 三值域：`BASIC`(基本数据) | `ENTITY_OBJECT`(实体对象) | `DEFAULT_OBJECT`(自定义对象)；BASIC 子字段 `basic` + `isArray`；ENTITY_OBJECT/DEFAULT_OBJECT 需 `app`（选择应用）+ `value`（实体/自定义对象）。`basic` 值域以前端 `pe` 枚举（module-65420）为准：`STRING 文本|INTEGER 整数|LONG 长整数|BIGINTEGER 大整数|DECIMAL 小数|BOOLEAN 布尔|DATE 日期|DATETIME 日期时间|OBJECT|DTO|ARRAY|MULTILINESTRING`——**`LONG` 与 `BIGINTEGER` 是两个不同值，别只列一个**；面板「数据类型」下拉的 BASIC 子集 = 文本/整数/长整数/小数/布尔/日期/日期时间。
  - 面板字段 key（module-83128 `FLOW_INPUT/FLOW_OUTPUT.items`）：`paramType` / `basic` / `app` / `entityObject` / `defaultObject` / `hasPagination` / `isArray` / `desc`(参数名称 required placeholder「请输入显示名称」)。`desc` = 参数名称（必填，≤20 字符，中文显示名）；`name` = 参数标识（`_FLOW_INPUT_<nano>`）。**`input`/`output`/`trigger`/`endNode` 四处 desc 要写一致**，否则落库值与面板显示打架。
  - 保存链：画布 state → `M = {...flowBasicInfo, dataSchema: JSON.stringify(画布组装)}` → 有 id 走 `updateMicroflowSchema`，新建走 `saveMicroflowSchema`；非 DRAFT 先过 `checkAndUpdateMicroflowSchema`（节点校验不通过给 `errorMessage[].message` 逐节点报错，画布滚动定位）。
  - trigger 三大类 = MANUAL（标准/自定义手动）| SCHEDULE（定时任务）| 事件（BUSINESS_EVENT 监听）；微流程列表 body 三段结构 `{pageInfo:{needTotal,pageNumber,pageSize,pages,total}, params:{appId, IN_type:["SERVICE","CUSTOM"]}, sort:{orders:[…]}}`（从 module-18640 的 `R(type, sourceId)` 组装函数逐字拿），响应字段路径 = `data.content[]`（op 类型直接包 data，非标准 code 包装；queryFields 带 pageInfo/content 会报 FieldUndefined，因为该网关版本 op 返回类型就是 `data{content}`）。SERVICE 型 = 手写后端微流程、CUSTOM 型 = 设计器拖拉拽，列表参数用 `IN_type` 区分——把 SERVICE 型的 schema 结构套到拖拉拽链路是类别错误。
- 端点 body 字典与样本字段值域见 `references/metadata-artifact-apis.md`。建完 state=10 草稿，必须走上文「保存→发布→构建」序列推 20 才进代码生成器。

## 规则域 REST 直建（事件 / 参照 / 生单规则 / 映射规则 / 扣减规则，全链 LIVE）

**这五类是独立端点域，各写各的表；契约在哪个 jar 里别猜**：`EventDto` / `ReferConfigDto` 在 **`udc-plugin-api`**，`DataFlowMappingSaveDto` / `DataFlowListSchemaDto` 在 **`udc-dataflow`**，都不在 udc-web / udc-common。**缺类先探 Artifactory 直连**（`http://10.0.0.1/artifactory/libs-release/com/seeyon/<artifact>/<ver>/<artifact>-<ver>.jar`，HTTP 200 即存在）——**不要因本地仓搜不到就判「契约不可得」并据此收口**（本仓这样错误收口过一次，随后发现该 jar 直接可拉）。端点表、必填链、DTO 全字段、枚举值域、图 JSON 形状见 `references/metadata-artifact-apis.md` 的「规则域补充端点」节。

- **生单规则**：`POST /udc/data-flow`（`DataFlowDto`，caption 必填）→ id。
- **映射规则**：`POST /udc/data-flow/mapping`；入参 `DataFlowMappingSaveDto` **extends `DataFlowDto`** —— 顶层要带 `appId/caption/id`，只包一层 `dataFlowMappingDto` 会一路停在 `appId must not be null`。校验错误链本身就是构造顺序，逐层补齐（见 reference）。
- **★ 图/映射里的 `node.id` 必须是实体 id（`"id_" + <实体id>`）**：伪造 id 会被检测判「图内实体不存在」（`UDC_CE_DATA_FLOW_05005` × 节点数），因为检测器按 `node.id` 反查 `udc_entity`。改回实体 id 后 `POST /udc/data-flow/update` 重存 `definition` 即归零（LIVE VERIFIED）。
- **扣减规则**：`POST /udc/deduction/rule`；出参是 `DeductionResultDto`（`{validate,id,affectCount,existRuleCount}`）**不是裸 Long**——按 Long 解析会拿错 id 再去拼 URL。`operatorEnum` 用 `SUBTRACT_EQUAL`。
- **事件**：`POST /udc/event`（`EventDto`，类级根）三类均可直建；`sourceId` 对非 ENTITY 来源必填、业务事件 `eventData`/`eventDataFullName` 必填。**`trigger_type` 不是 `udc_event` 表列**（`triggerType` 落 `exp_design_data`/`exp_runtime_data`），回读校验别查它。与前端 tab 主链 `udcEventCreateWithDataPost` 并存，勿互相覆盖。
- **参照**：`POST /udc/refer-config/create`；`sourceType` 传 **DB 数值 0**（传枚举名报 `BOOT_3002 No enum constant`）；`configInfo` 必填。**★ PC 参照必须与 MOBILE 参照的 `displayName`/`columns`/`orders`（含 `direction`）逐项一致，否则 `UDC_CE_ENTITY_02119` Configuration is inconsistent × 路径数**——只建一端就报；把另一端对齐已存在那条的同名字段即归零（LIVE VERIFIED）。
- **检测面复核顺序固定**：`POST /udc/application/do/detection`（**类级映射是 `udc/application`**，`/udc/do/detection` 报 404）→ 轮询 `do/detection-state` 至非 `EXECUTING` → `POST /udc/graphql?udcApplicationSearchDetectionPost`，**body 必须带 `query` 字符串**（只发 variables 报 `GraphQL-3001 Invalid Syntax '<EOF>'`）。每建一个对象就复核一次；判据是「目标码消失且无新分支」而非条数。

## 部署构建 body 形态（活体实测成功）

**设计器「测试/立即构建」按钮的真实通道是 GraphQL，不是裸 REST（CDP 抓包逐字，datamigration 应用）**：点「测试」弹「应用测试」对话框（纯前端，无请求），「立即构建」发 4 个请求，入队主请求：

```
POST /service/udc/graphql?udcRuntimeDeployNormalPost
{"query":"query graphqlLoader ($params0: udcRuntimeDeployNormalPostInputBody) { data0: udcRuntimeDeployNormalPost(body: $params0) { code data { content{appId,deployId,deployType,projectType,terminalType} } message status } }",
 "variables":{"params0":{"deployDto":{"projectType":"ALL","terminalType":"ALL","deployType":"RELEASE","appId":"<数字appId>","generateLog":true}}}}
→ BOOT_0000 + content.deployId
```

- **「测试」按钮发的也是 deployType:RELEASE**（RELEASE=测试发布；ON_ONLINE=上架被「先测试后上线」闸门拦，实测 toast「当前应用有修改,请先测试发布后再上线!」；DELTA=增量）——别按字面把 RELEASE 当成正式上线。伴随请求：`udcDeploymentAppReadyStatePost`+`udcSandboxBuildInfoAppGet` 联合、`POST /udc/runtime/expect-deploy-time`（body deployParamDto 同构，回秒数字符串）、`udcDeploymentLatestTestInfoPost`。
- **状态轮询走 GraphQL `udcRuntimeSearchDeployStatusDeployIdPost`**（variables `params0={deployId}`），content[0] 全字段：`validate,id,deployId,appId,appGuid,sourceType,appName,projectType,terminalType,state(SUCCESS|FAIL|RUNNING),msg,appVersion,schemaStorageKey,sqlStorageKey,deployType,createTime,creator,schemaMd5,businessType,imageUrl,buildVersion(yyyyMMddHHmmss),jarVersion,udcVersion,pushEnv,compileLogUrl`——字段比 appVersion 读面全（含构建指纹）。就绪态 `udcDeploymentAppReadyStatePost` 的 `state:RUNNING,msg:DEPLOY_SUCCESS` 是「应用运行中」而非「本次构建成功」。
- **前端读/写统一走 `/service/udc/graphql?<opName>`**：op 名 = 控制器方法 camelCase（udcRuntimeDeployNormalPost ↔ DeployController#deployNormal）。REST 裸路径同样存在且契约如上，但**复刻工作流优先按前端真实形态（GraphQL）发**。
- 「发布」对话框（推送到实施/生产 radio + 锁定应用 switch + 版本 checkbox）三关逐个拦：未勾版本提交 →「请选择发布版本」；勾选后 →「当前应用有修改,请先测试发布后再上线!」。测试发布 SUCCESS 后才放行。

真实入口（javap 类级注解确认 + 活体 200）：

```text
POST /service/udc/runtime/deploy-normal
{"deployDto": {"appId": <数字Long>, "deployType": "TEST", "projectType": "ALL", "terminalType": "ALL"}}
```

- **body 必须按参数名包一层 `deployDto`。** `deployNormal` 的参数注解是 Seeyon Boot 的 `@MultiRequestBody`（**不是** `@RequestBody`），按**参数局部变量名**从 JSON 顶层取值。裸平铺 body 会把 DTO 绑成 null，请求**HTTP 200** 返回 `status:3` + `BOOT_3000 EL1007E: Property or field 'appId' cannot be found on null`——报错指向 DTO 的第一个字段而不指向包装，极易误判成字段名写错。**判成功看响应信封 `status/code`，不看 HTTP 状态码。**
- **别把"包装体"推广到所有设计态写接口——两种绑定形态并存，逐接口实测。** `deployNormal` 是 `@MultiRequestBody`，而 `ApplicationController.create`（`POST /service/udc/application`）是标准 `@RequestBody` **平铺**。喂错的组合不报 4xx，而是把字段说成"没传"：包装体喂平铺 handler → `BOOT_1001 caption must not be blank`；平铺体喂 MultiRequestBody handler → `BOOT_3000 EL1007E: Property or field 'x' cannot be found on null`。判定法：同一最小 body 的平铺/包装两版各发一次，**保留"错误往前推进到下个必填字段"的那版**。
- `DeployParamDto`（`DeployNormalDto` 继承它）字段：`deployId / appId(Long) / deployType / projectType / terminalType / pushEnv / extraParamMap`；`DeployNormalDto` 另有 `lockCompatibility / generateLog / entityFullNameCondition`。
- `deployType` 枚举：TEST / RELEASE / ON_ONLINE / DELTA（`udc_deploy_record.deploy_type` 数字编码 **TEST=0、RELEASE=2**）。
- `projectType`：FRONTEND / BACKEND / ALL。`terminalType`：ALL / PC / MOBILE。
- `appId` 必须是**数字 Long**（不是 app name）。app name 末尾数字段即 appId。
- **顺序门槛：没成功 TEST 过就不能 RELEASE**——RELEASE 直接报 `应用未成功发布过，请先【测试】操作`。要打通"建应用→构建→发布"，先跑 `deployType:TEST`，成功后再 RELEASE。
- **类级前缀从字节码读，不要靠试 URL。** `javap -v` 把**类级**注解打在 `SourceFile:` **之后**、整个输出的最末尾（常量池里 `#NN = Utf8 RuntimeVisibleAnnotations` 的条目和各方法级块都在它前面），所以 `grep RuntimeVisibleAnnotations` 会先命中常量池条目而说谎。用 `sed -n '/^SourceFile/,$p'` 截尾段再解 `#NN` 引用。`DeployController` = 类级 `udc/runtime` + 方法 `deploy-normal`（类级**无** `@HasRole`）；兄弟类 `DeploymentController` = 类级 `udc/deployment`，**类级挂着** `@HasRole(udcAppDesigner, udcSystemAdmin, OpsAdmin, BpmSystemManager)`。
- **404 常是鉴权拒绝而不是路由不存在。** `@HasRole` 不通过返回 Spring Whitelabel 404，而且 pod 里仍会留下 `AppContextFilter` 的 request 行——"日志没记录"不能证明路由不存在。最便宜的探针是 `405 Method Not Allowed`：405 说明路由在、只是动词不对。**405 同样可能是鉴权伪装**：同一 POST，外部客户端（urllib/curl 无 cookie）返回 405 Whitelabel，换登录态浏览器内 `fetch`（带 session cookie）即 200 带业务校验错误——先换浏览器态重放再下"路由/动词不对"的结论。CDP 浏览器自动化配方（起 Edge、登录、带 cookie fetch、URL 结构、菜单数据源）见 `references/udc-web-console-cdp.md`。

## 设计态建实体 / 建属性（LIVE 实测通过的最小形态）

- 建实体 `POST /service/udc/entity`（EntityController.create）：body 需 `stereotype` + `entityNature=MAIN`，否则报 `UDC_ENTITY_0010`/`BOOT_1001 stereotype must not be blank`。**`features` 的权威来源是 jar 内版型配置**（`stereotype/<name>/config.json` 的 `necessaryFeatures` 逗号拼接）——不是照既有实体反推（反推已过时，见「udc-biz 资源」条）：bill=`basic,approve,organization,billBasic,termination,suspend,nullify`、standard/basicData=`basic`、form=`basic,formBasic`、archive=`basic,archiveBasic,approve,archiveTiled`、archiveTree=`basic,archiveBasic,approve,treeEntity`。固化模型见 `components/udc/platform_mechanism_model.py` 的 `features_for_stereotype()`。
- 建应用 `POST /service/udc/application`（`ApplicationController.create`，类级根 + **平铺** body）。字段校验规则（LIVE 错误码）：`name/code` 小写字母开头、只含小写字母数字（`UDC_APP_0023`）；`terminalType` 缺省报 `BOOT_1001 终端类型 不能为null`。字段校验全过后卡在**租户配额** `UDC_APP_0030`（详见下方配额契约）。**create 返回的 19 位雪花 id 是应用 guid，不是 deploy-normal 要的 appId**（13 位数字，如 znxmglptcopy=5791640252914287064）——拿 guid 直接喂 deployDto.appId 报 `UDC_APP_0001 应用不存在`；无数字后缀的 app name（如 zzprobenew1）无法从 name 推 appId，需管理端应用列表或 DB 查映射。`appVersion` 合法值回读既有应用详情获取：`GET /service/udc/application/{id}` 返回 `appVersion:"1.0.0"`，整份响应即建应用 body 的字段模板。`select-platform-version` 这条读取路由被 `/application/{id}` 吞掉（报 String→Long 转换错），别拿它取版本。
- **建枚举约束链（LIVE 错误码逐个试出）**：`appId` 必须数字 Long（字符串报 BOOT_1001）；`name` 大写字母开头只含字母数字（`UDC_ENUM_0001 The code must start with an uppercase letter`）；`udcEnumType` ∈ DEFAULT|CONNECTOR|DYNAMIC_DEPENDENCY（传 SYSTEM 报 No enum constant）；**枚举与枚举项必须分两步**（带 udcEnumItemDtoList 一体建报 enumId must not be null，先 POST /udc/udc-enum 拿 id，再逐条 POST /udc/udc-enum-item）；枚举项 `code` 必填 Integer。索引 `fieldIds/fieldNames/fieldCaptions` 是逗号分隔**字符串**不是数组（数组报 fieldIds must not be empty）；索引列表回读 body 形态未通（SingleRequest 包装，entityId 字符串/数字/顶层/content 四形态均 BOOT_3002）——创建成功即可用，回读待调。
- **REST create 是半成品陷阱，不要用它建应用**（浏览器态登录会话里 LIVE 实测）：即使 body 全过校验返回 `BOOT_0000` + guid，服务端也只落一条**缺宿主应用信息**的残记录——管理列表（backstageManage）不显示、deploy-normal 报 `UDC_APP_0001 应用不存在`、详情页显示"数据不存在或无权限查看"、全部 REST 删除端点（delete/delete-by-guid/delete-rename）content:0 够不到（删除内部联查宿主信息先炸，字节码注释原话标记该端点已被改名 delete-rename）。UI 表单比 REST 多**所属机构/应用所属人**字段——正是 REST 缺的落库要件。**建应用一律走 backstageManage UI 表单**；REST create 只当字段校验探针用（拿它的错误码反推参数字典）。误建出的残记录 REST 删不掉，只能 DB 清理或留给平台；建前先查配额余量，建废一次就占一次试验成本。
- **UI 表单建应用全链已 LIVE 打通（CDP 自动化）**：`/main/backstageManage/udc/apps` → 新建 → 表单（名称/编码，机构与所属人默认带出）→ 确定 → 提示"应用【xx】创建成功"→ 列表即时出现。数字 appId 从"去设计"跳转 URL 拿（`/main/child-frame/udc/app-design/app-basic-info?appId=...`，hook window.open 或读 target 列表）。表单 React 输入用 CDP `Input.insertText`（native setter 在该表单无效），详见 `references/udc-web-console-cdp.md`。
- **UI 设计器内建实体已 LIVE 打通**：设计器左侧"实体"菜单 → 树顶部两个图标按钮（lined-folder=新建分组、lined-plus=新建实体）→ 表单（实体显示名称 + 编码自动生成拼音，可清掉重输）→ 确定 → 实体进树 + 字段编辑器打开 → 添加字段（默认 ziduan1 文本50，点名称单元格可改名）→ 保存 → "保存成功"通知。React 表单输入必须 CDP `Input.insertText` 真实键盘事件，native setter 填完点确定会报"请输入实体名称"。**编辑器内改名用 select+execCommand('delete')+insertText 而不是 native setter**（antd 表格行内编辑同受控组件约束）。新应用空应用无法直接 deploy-normal（报应用不存在）——先在设计器内建实体等内容再走设计器内构建。CDP 操作细节见 `references/udc-web-console-cdp.md`。
- 建属性 `POST /service/udc/entity/attribute`：需 `appId + entityId + dataType`（缺 dataType 报 BOOT_1001）。`uniqueness` 是 **Boolean**（传字符串报 BOOT_3002 to type Boolean）；多选人员字段 = `dataType:"ENTITY" + multiSelect:true + relationType:1 + relationEntity:"com.seeyon.organization.domain.core.entity.OrgMember" + relationApp:"organization"`（LIVE 建后回读 multi_select=1）。设计器真实引用的平台人员实体全名是 `com.seeyon.organization.domain.core.entity.OrgMemberMetadata`（在 datamigration 应用上 LIVE 建成）——两个 fullName 都出现过，以目标版本回读为准。字段类型×控件 LIVE 矩阵全通（datamigration）：STRING/INPUT 文本、DATETIME/DATE 日期、INTEGER/INPUTNUMBER 整数、BOOLEAN/SWITCH 布尔、CTPENUM/SELECT 枚举（relationEntity=enumId）、ENTITY/LIST+multiSelect 人员多选。**字段修改与实体修改都是全量回传**：先 `select-all-by-entity-id`/`findById` 回读单项/实体全量 DTO，改动后 `POST .../attribute/update` 与 `POST /udc/entity/update` 直接过（datamigration 双 LIVE）。
- **CTPENUM（枚举引用）字段必填四件套，缺 `relation_entity_name` 即报 `UDC_CE_ENTITY_02104 Attr relation ctpEnum not exist`（LIVE 定论）**：`relation_entity`=枚举 id、`relation_entity_name`=枚举 **caption**、`relation_code`=枚举 **name**、`relation_app`=归属 appId（另有 `relation_type=1`/`relation_entity_category=0`）。只填 `relation_entity`（枚举 id 正确）不足以过检测——平台真实 CTPENUM 字段四列齐备才是常态，用 `SELECT ... FROM udc_attribute WHERE data_type='CTPENUM'` 采样对照即可发现缺口。修复 = `GET /udc/entity/attribute/{id}` 取全量 DTO → 补三列 → `POST /udc/entity/attribute/update`（回传用读面的枚举字符串形态，别拿 DB 数字码回写）。**修完必须调 `do/detection` 重算再验**（见检测面节）。
- **建属性 body 必须单条对象，不能数组批量**：`{"appId": <Long>, "entityId": <Long>, "name", "caption", "dataType"}`——数组包装报 `BOOT_3002 Failed to deserialize ... to type AttributeDto`（LIVE 实测，zzprobe 2026-10）。逐条循环发送，全 5/5 BOOT_0000。
- **字段名撞平台保留字会被 UDC_ENTITY_0002 拒**（message 含 "system reserved field"）：`orderNo` 被拒、`orderCode` 同场通过——遇到 0002 换名重试而不是怀疑 body 形态；R2 先例 `ZzprobeR2FieldA`（大写开头）可用，说明不是大小写问题。`dataType=DECIMAL/DATE` 直通，无需附加字段。
- **REST 建实体要求应用已至少成功部署过一次**：对刚建未发布的新应用 POST /service/udc/entity 报 `BOOT_1001 应用不能为空`（appId 数字形态也不行）——先在设计器内建实体并走一次设计器构建，之后 REST 建实体对该 appId 直接可用。对已发布应用（如 znxmglpt）无此限制。
- **stereotype 值域** `archive / standard / bill / archiveTree`、**dataType 值域** 等受控词表，**不要发明**——从目标应用既有实体回读统计（`GET /udc/entity/primary/select-by-appid/{appId}` 数实体、`GET .../attribute/select-all-by-entity-id/{entityId}` 数属性）。值域是活体快照，随活体复核刷新，别当永久常量硬编码进调用方。

## 设计态建页（`PageInfoController.createBaseInfo`，LIVE 实测）

**前端页面不是构建送的**——页面是独立设计态动作，必须建实体后显式创建，再随构建发布。deploy_plan 的步骤顺序即此：建实体→建属性→建页(LIST+DETAIL)→构建。

**页面定义查询/删除走 GraphQL（实测可用）**：全量清单 = `udcPageInfoSearchNoPagePost`（variables `body.params.appId`=数字 appId 字符串），返回每页 id/guid/pageType(SEARCH_LIST|DETAIL|PORTLET)/pageUrl/urlType(PC|MOBILE)/masterEntityIds/schemaState；删除 = mutation `udcPageInfoDeletePost`（body `{"id":"<页面id>"}`，content:1 即成功）——**清理空页面阻断项就靠这两个**（空页面清单从 pod 日志 `UDC_CE_PAGE_03907` 的 document 字段拿）。**改写已有页面走 mutation `udcPageInfoUpdatePost`（LIVE 全链打通）**，其必填结构与最小可用 pageSchema 见下方「页面设计态可用 API 构造」一节。REST 等价通道 `POST /service/udc/page-info/update-draf`（LIVE）：平铺 body `{id:<udc_page_info.id 数字Long>, appId, caption, name, pageType, urlType, pageUrl, masterEntityIds, draftPageSchema:<页面schema JSON字符串>}` → BOOT_0000 content:1，落 `draft_page_schema` 列（page_schema 仍空，发布/构建才合并）。**页面有三个 id，别混**：create 返回的 `content.id`、select-by-appId 树里的 `id`/`relationGroupId` **都不等于** `udc_page_info.id`（实测 content.id=3936722146787982313、relationGroupId=435027454249697022，而真 id=-4954373828832737419）——update-draf 只认真 id，取法 = DB 按 caption 查 `udc_page_info`；喂错 id 报 `UDC_PAGE_0004 页面不存在`，body 只给 id+schema（缺整条元数据）报 `BOOT_3000` 空消息，两种报错别混判。

- 入口：`POST /service/udc/page-info/base-info/create`（类级 `/udc/page-info` + 方法级 `/base-info/create`）。
- 必填链（缺一即拒，均为 LIVE 实测错误码，逐个试出错得来）：
  1. 缺 `pageType` → `BOOT_1001 pageType must not be null`
  2. 缺 `pageUrl`（**顶层和 pageItems[] 都要**）→ `BOOT_1001 pageUrl must not be null`
  3. 缺 `curTerminalType` → `BOOT_1000 页面终端信息为空，请选择`
  4. `actionType` ∈ `{NORMAL, INSERT, UPDATE, DELETE}`——`VIEW` 不存在，报 `BOOT_3002 No enum constant`（值域从 `com.seeyon.boot.enums.ActionType` javap 拿，别猜）
  5. `masterEntityIds` = 实体**数字 id**（建实体返回的那个，不是实体名）。**形态是裸字符串，不是数组**——`udcPageInfoUpdatePost` 传 `["<id>"]` 报 `BOOT_3002 Failed to deserialize the value of property masterEntityIds to type String`；schema 内的 `masterEntityIds` 同样是字符串（`"474806313816300867"`），不是 `[id]`。
  6. **页面必需绑定归属资源** = `pageItems[].menuId` 指向已存在的菜单——先 GraphQL `udcFunctionPost`（batch 形态 `?op`，body `{appId,name,caption,type:"MENU",terminalType:"PC",parentId:"0",orderNo:999}`，LIVE 通）建菜单，再建页面带 `menuId+menuName`；缺它报 `BOOT_1000 页面必需绑定归属资源`，顶层塞任何 `terminalType/urlType/terminals` 变体都过不了这关。
- bill 单据族建页对 = LIST + DETAIL 各一；`urlType` ∈ `{PC, MOBILE}`。
- **deploy_plan 生成的页面 body 实证可用**：把 step3 body 里的 `"<entity_id>"` 占位符替换为真实实体数字 id 后直接 POST `base-info/create`，LIST+DETAIL 双页全 BOOT_0000（zzprobe LIVE 验证）。回读验收：`select-by-appId` 返回的是**树形结构**（顶层节点 caption 为 null，真实页面嵌在 `pageList[]` 里）——递归走 `pageList` 再按 caption 搜，别在顶层找。
- 回读验收用 `GET /service/udc/page-info/select-by-appId/{appId}`（按 appId 全量，搜 caption 命中即成）。**按 id 回读 detail/{id} 会报"page does not exist"**——该读面只认 relationGroupId，不是页面建失败；`/detail/{id}` 路由存在但语义不同。
- C2b 运行态元数据面（`udc-runtime/meta-data/select-host-and-only-page-pages`）**只回读已发布页**——新建设计稿在该面 0 命中是预期行为，别误判"没建成"；设计态读面（page-info）才能看到。

## 设计器内建菜单/栏目/枚举/微流程（UI 全链 LIVE 打通，2026-09-30 zzprobe）

设计器左侧 8 个模块（应用/实体/菜单/规则/流程/BI/栏目/设置/角色）全部 UI 通道已走通，且各有独立后端服务——**模块↔服务映射本身就是事实**：规则/实体/菜单/栏目/设置走 udc，流程走独立 bpm 服务（graphql `bpmTemplateSelectByAppIdGroupByTagPost`），BI 走独立 cdp-data 服务（数据集/数据流/指标/报表），角色跨 ctp-user。逐模块接口测绘：实体=udcEntitySelectAllByAppidAppGet 系（另有容量 `udcEntitySelectMasterEntityCountAppGet`、预置属性 `udcEntityAttributePresetAttributeCapacityAllAppGet`、属性组 `udcAttributeGroupEntityGet`），菜单=udcFunctionSelectFunctionTreePost + `udcApplicationAppVersionAppGuidPost`，规则=入口批量 `udcMicroflowSearch`（微流程清单权威源），栏目=REST `udc/page-info/select-by-appId/{appId}` + udcPortletSelectByAppIdAppGet，设置-枚举=udcEnumCategorySearch/udcEnumSearchNoPagePost，角色=udcCtpUserRoleSelectListPost（预置 3 角色）+ `udcCtpUserRoleAppResourceGet`（资源矩阵 PC/PC_LAYOUT），应用=依赖应用 `udcApplicationDependentApplicationSelectByConditionPost` + 详情/版本/就绪态 batch（含 `udcDeploymentAppReadyStatePost`）。以上全部 LIVE PASS（datamigration 应用，抓包在 seeyon-agent `docs/audit/udc-semantics/NAV-LIVE-CAPTURE-20261012.md` + evidence/*.jsonl）。未活体：页面主 tab、外框、参数、高级设置、规则画布保存链、BI 语义模型/指标写链。

- **建菜单（LIVE）**：菜单 tab → 树顶 lined-plus（tooltip「添加页面」）→ 表单（页面名称 + 页面标识自动生成拼音可改 + 页面类型【列表页/详情页/全表编辑页/其它】+ 页面对应实体 + 适配终端 + 归属分组）→ 确定 → 菜单树出现新项并自动打开页面设计器（标题区/内容区 + 控件/大纲/数据/规则面板 + 暂存草稿/保存并提交）。页面对应实体是 **TreeSelect**：选项点 `.ant-select-tree-treenode`，不是 `.ant-select-item-option`。
- **建栏目（LIVE）**：栏目 tab → 同位置 lined-plus → 表单（栏目名称/栏目标识自动拼音/适配终端 web端/归属/模板=空白页面）→ 确定 → 栏目树出现(草稿) + 页面设计器打开。多 label 表单定位用「label 文本向上 6 层找 input」法，别按 input 索引猜——index 会随表单增减漂移。
- **建枚举+枚举项（LIVE）**：设置 tab → 枚举管理 → 树区 lined-plus（区分 ant-empty 空态提示的假按钮）→ 表单（名称/编码/分类可空/状态启用/可扩展/平级层级）→ 确定；选中枚举 → 「新建」按钮 → 枚举项弹窗（名称/值/排序号，placeholder 全是'请输入'，按 DOM 顺序定位）→ 确定。枚举项操作：编辑/停用/删除。
- **建微流程（LIVE）**：规则 tab → lined-plus → 表单（类型=标准微流程，触发方式=服务定义/事件监听/定时任务，名称/编码/分组）→ 确定 → 微流程画布打开（开始→结束节点 + 右侧动作面板 + 流程/参数/配置 tab）。空流程存草稿，动作从右侧面板添加。
- 设计器各 tab 的接口清单用 CDP `Network.enable` + `requestWillBeSent` 事件收集（fetch/XHR hook 只覆盖主 frame，微前端 iframe 里抓不到）；每 tab 的 graphql mutation/query 名即该模块的 API 面。
- **活体审计的目标应用以用户指定为准，绝不擅自换应用**（用户红线）：换 app 会拿到完全不同的 API 面/权限响应，还污染证据归属。zzprobe 只用于平台级写链探测，设计器导航测绘要在用户指名的应用上做。
- **BI/流程等微前端子应用的请求依赖 `window.xcbpbi` 注入 app 上下文**（appName+appId）：直接深链 `child-frame` URL 时 xcbpbi 为空，BI 域报 `cdp.udc.app.no.auth`（即使 appId 在 URL 里、cookie 有效）。正确姿势：先落到壳 `app-design/basic-info?appId=<数字>` 等壳完全加载（~12-14s），再点击左导航 `<a href>`（SPA 路由），子应用 chunk 懒加载再等 3-8s。
- **导航绝不用 `location.hash` 拼路由**：hash 会拼进 appId 参数（`870402...#/app-design/...`），后端报 `BOOT_3000 For input string` 反序列化失败——该批抓包整批作废，别混进证据。判据：报错里出现 `&quot;` 包着的 `appId#路径` 即此坑。
- **进角色/操作权限页是隐性写操作**：页面加载即触发 `POST /service/udc/ctp-user/role/create-system-admin`（幂等但真实写库）——「导航=只读」不成立，自动化过导航时要知道自己写过什么。
- **网关按 `/service/{第一段}` 路由到微服务**（udc/bpm/cdp-data/ctp-user 各域）；BI 的独立基址 `/cdp-am`、`/cdp-df` 在 test2 网关 404，只存在于独立 BI 站点，内嵌态一律 `/service/cdp-data/udc/*`。微流程列表在「规则」域（`udcMicroflowSearch`），不在流程域——bpm 域只管 BPM 流程模板，两个“流程”不同物。
- **同一目标的静态法（不开浏览器，先用它）**：`/udc/remoteEntry.js` 的 `.u` 链定位 tab 懒加载 chunk → 抽 `load({fieldType,paramsType,paramsKey,params,queryFields})` 描述符与内联 query 原文，一次拿到 op 名/入参类型/参数键/返回字段；CDP 留给要真实请求序列或静态取不到的桩。大 chunk 按 module id 手工 grep 字节偏移前先试 `wakaru --unpack --provenance` 自动拆模块（Windows 用 `@wakaru/cli-win32-x64` 原生 exe；配方与边界见 `references/webpack-bundle-unpack.md`）。设置模块 13 tab 的 chunk/op/Controller 对照、pageType（`LAYOUT`=外框）、选项集(`Enum`)≠枚举(`CtpEnum`)配对、tab 定义对象（`basic-setting` chunk 内对象字面量：JS key 与中文标签交叉错位、`uniformityKey`、组件模块→chunk 归属、页面模板与外框模板**同一组件靠 `category:"PAGE"|"LAYOUT"` prop 分流**）、五种调用形态与 op 名前缀三种取法见 `references/designer-frontend-call-chain.md`。
- React 受控输入（尤其 antd Modal/表单）统一用 `Input.insertText` 真实键盘事件；value setter + dispatchEvent 在这些表单上 value 读回正常但提交时报"请输入xx"。多 label 相邻字段（如栏目名称/栏目标识）填完一个后重新按 label 定位下一个，不要复用旧索引。
- **每访问一个新页面/新接口都落盘到模块证据件（用户明确纪律）**：URL、网关分发路径、接口名、参数形态全部记入 `core/facts/udc/write-chain/url-ledger.md`（页面路由表 + 接口清单 + 通道判定表）。每个条目三分类：【事实】可直接记录 /【需组装配置】UI 操作序列 /【通道判定】接口能做 vs 只能页面做。落地归属：网关路由契约归 gateway 事实格（多线并行时本线只写 write-chain/** 并标注待合并），不越界代写其它线领地。

## 运行态数据面读取（LIVE 实测，建完实体后的录数/查数闭环）

- 单条查询入口 `{PF}/udc-runtime/data//query`——**双斜杠逐字保留**，归一化掉就 404；语义是按 dataId 查单条，三个必填键 `appName / dataId / entityFullName`。
- **参数字典从校验错误原文里挖，不要去猜也不要去翻 DTO**：POST 一个空/最小 body，Spring 的 400/BOOT_1001 消息会把必填键名直接列出来——比反编译 jar 或猜字段名都快都准。错误并列的键名就是权威参数表。
- 建→建页→构建通了不等于闭环：只有用 data/query 读回一条真实数据（identity 匹配）才算"能录数据"，此前全停在骨架面。
- **运行态路由按页面能力动态注册，路由缺失 ≠ 部署失败**：只有 SEARCH_LIST 页面的应用（LIVE 实测）网关上只挂 `POST /service/{app}/udc-runtime/data/query`，其余 `/udc-runtime/*` 候选路径全 404 是"没有 CRUD/表单页面所以没注册写路由"，不是应用没部署成功。参数字典用空 body 的报错原文拿（`appName 应用编码; dataId 数据id; entityFullName 实体FullName`）。运行态 controller 的 URL 由 `UdcRestPathParse` 按功能节点动态解析（`udc-starter-runtime` jar 字节码证据：`UdcFormDataQueryController` 类级 `udc-runtime/data` 只挂 `/query`；`UdcBaseGeneralController` 有完整 create/select/update/deleteById 但路径动态生成，`NormalAppPcController` 是空壳 extends 它）——判"写路由存不存在"以活体探测为准，别从 jar 猜静态路径。R4 写入探测的完整路径清单、通道判定口径与解阻路径见 `references/runtime-data-write-probe.md`。
- **找应用的物理表别在 udc 库里翻**：物理表落 `{appName}_{env}` 应用专属 schema（如 `zzprobenew<appId>_test2`）。最快定位：拿一个已知业务列名反查 `information_schema.COLUMNS WHERE COLUMN_NAME='<业务列>'`，一次命中 schema+表名；表名 `{entity拼音}_m{随机段}` 应与 `udc_entity.table_name` 一致，对不上就是查错库。
- **回读验证优先用 API 而不是 DB 直插后的裸 SQL 查**：写一行基准数据（DB 直插或 API）后，用 `data/query` 三键回读并断言 `id==dataId` + 业务列逐字一致，这样同时验证了平台查询协议；只 `SELECT` 自己插的行只证了 DB 层。`data/query` 查无此行返回 `BOOT_3000`，与端点错误同码——空表上回读必踩，先插行再验。

## 微流程写链：校验、落库、红字判定（先读这一节）

- **先判红字类别再动手**：服务端 `udcMicroflowCheckSchemaUpdatePost` 返回 `check=true, errorMessage=null` 而画布仍飘红 ⇒ 红字是**纯前端**（候选集不匹配 / 跨节点 `outputName` 悬空），别去改后端或业务逻辑。两类根因与修复顺序（类名映射优先于 app 前缀、显式最长匹配重定向、逐键路径复扫）见 references/microflow-node-data-completion.md。
- **check 必须传 DB 全字段**（只传 `{appId,id}` 报 `caption must not be null`）：先 `SELECT * FROM udc_microflow_info WHERE id=<id>` 取整行，替换 `dataSchema` 后发一次（precheck 不落库），通过再 `udcMicroflowUpdatePost` 落库；`jsonSchema` 必须 NULL，否则编辑器 `reading 'map'` 崩。写完从 DB 回读核验：节点数不变 + 外部引用 token 0 + 类名全本应用化。
- **真机复验前先确认编辑器无编辑锁**：持锁时顶部显示「…正在对页面进行编辑，仅支持查看」，画布不渲染、属性面板点不开——此时任何「红字 0」统计都是假阴性，不能当通过。
- **跨应用引用要显式决策**：`SUB_MICROFLOW.mfService.id` / `CALL_APP_SERVICE` 指向的目标不在本应用 `udc_microflow_info` 列表里就是跨应用引用，不保留也不伪造，按本应用真实流程替换或交用户拍板。

## 验证物理表落库（验收铁律）

- 构建成功后物理表落**应用自身库**（`{app}_test2` / `{app}_uat`），**不是 `udc_test2`**。连错库会误判"没建"。
- 表名形态 `{entity拼音}_m{随机段}`，DDL 带业务列 + 全套单据系统列（中文注释）。
- 因果确证查 `udc_test2.udc_deploy_record`：`state=1` msg=内部流水线构建成功，`state=2` 是失败（msg 带原因 + 报错位置，常见 `一致性检测未通过`，报错点 `com.seeyon.udc.pipeline.AbstractDeployService.doParallel(AbstractDeployService.java:242)`；编译失败则是 maven 错误 + backBuild.log storageKey）。
- **构建有多个状态面，只有 `udc_deploy_record` 是地面真值。** `sandbox/build-info/{appId}` 在整个 `deploy-normal` 运行期间恒为 `state:NONE`（它跟的是另一条 sandbox 构建），`deployment/latest-test-info` 在测试真成功前恒 `testSuccess:false`。拿这两个面判断会得出"构建根本没跑起来"的假结论——实际上流水线正在执行并已失败。**部署历史回读真面（LIVE）**：`POST /service/udc/application/appVersion/{appGuid}`（appGuid=应用族 guid，从 `GET /udc/application/{id}` 的 `guid` 字段取；**必须 POST** 带 body `{}`，GET 报 405）返回该应用全部部署记录 `deployType / state(SUCCESS|FAIL) / failReason / deployTime`——比连库快，旧 registry 路径 `deploy/search-status/{id}` 作废。成功时 `failReason="udc发布成功"`（双观测：业务应用 RELEASE+ON_ONLINE 均 SUCCESS、副本应用 TEST FAIL，与 deploy_record 逐项吻合）。
- 失败明细在 Redis：`test2:udc:<ver>:DetectionError:Data::<appId>:{ENTITY|PAGE|MICRO}:<类全名>`——**生命周期 = 单次构建会话**，构建结束即被清，事后 KEYS 归零。要条目级明细必须"发起构建 + 每 ~10s 轮询 Redis"作为一个组合动作执行，拆成两步就永远拿不到；事后只能读构建日志 hash（`test2:redis:build:log:*`，TTL≈2.9 天，含逐任务耗时与最终失败文案）和 `POST /udc/application/search/front-detection`（body `{"appId":"<id>"}`，注意 count=0 是"明细已清"不是"曾通过"）。**别再扫 MySQL 找检测明细**：`information_schema` 里 `%detect%`/`%check%` 无表（已实测）。连接材料/读取命令见 `references/test2-env-access.md`。
- **配额契约（字节码确诊，`ApplicationService.checkTenantLicenseAppCount`）**：建应用配额只数 `sourceType=NORMAL && jsonPrefab=false` 的应用，上限 = 租户配置 `SandboxTenantConfigDto.createAppNum`（test2=10）。`dynamic*` 集成应用（`source_type=1`）**不占配额**。建新应用前先查余量：RDS `SELECT name,source_type FROM udc_test2.udc_application`，NORMAL 行数即已用额度。配额满是环境硬约束，业务应用一个都不能动——别在这条路上空耗，改走既有测试应用或让用户调租户配置。
- **「页面控件配置的字段不存在，<gridId>->null」= dataSource.fields/fieldBindMap 存空，不是实体字段缺失（LIVE 三方对账确诊）**：一致性检测报这个错时，把 `udc_page_schema.page_schema` 的该控件（columns dataIndex）、`udc_attribute`（entity_id 过滤 is_system=0）、报错原文三方对账——列字段全在实体里而控件 `dataSource.fields:[]` + `fieldBindMap:{}` = 字段绑定清单被某次页面保存存空（前一次构建成功 + schema_state=2 + 中途保存过即佐证）。修复 = 设计器打开报错链接指向的页面补全表格字段绑定，**不是去实体加字段**。检测并行跑（`AbstractDeployService.doParallel:242`），不过不进编译，progress 低位（如 18）+ FAIL 即此形态。
- 一致性检测未通过时按日志固定点位归因（udc pod）：`PageControllerTask:643`（runtime 对应的页面数据源不存在）、`ReferUtil:114`（参照悬空）、`MetadataConvertUtil:1287`（关联枚举元数据为空）、`PageExpressionDetectionUtil:310` / `PageDetectionTask:419`（页面表达式失效/NPE）。被拷应用自带页面与参照时这几类会成百出现——那是**应用自身数据悬空**，不是构建链路缺陷；不要为了"修构建"去改流水线代码。
- **★ 检测面有两个口径：`search` 读快照，`do/detection` 才重算（LIVE 定论，取代旧「Redis 缓存」说法）**：`POST /service/udc/application/do/detection`（body `{appId}`）触发重算；`POST /service/udc/application/do/detection-state`（body `{appId}`）返回 `{validate,status,count,errorCount,seriouCount,warnCount}`；重算后再 `POST /service/udc/application/search/detection` 读条目明细。**只读 `search` 会拿到改前的结论**——不调 `do/detection` 就断言「改了没生效」是错的（本仓踩过：属性/微流程/页面三处都已落库改动，`search` 仍报旧内容，被误判成平台缓存机制并写成结论）。修复闭环必须把 `do/detection → sleep ~10s → do/detection-state → search/detection` 当成**一个组合动作**执行。别用反复触发 deploy 来「刷新」检测——deploy 才是真跑流水线（分钟级）。
- **检测明细有生命周期**：`do/detection` 的结果会被后续重算覆盖；要条目级历史必须每次重算后立即读 `search/detection` 并落盘。构建会话级明细（`test2:udc:<ver>:DetectionError:Data::*`）与构建同生命周期，构建结束即清。
- **检测面读数与 DB 回读冲突时的判据顺序**：①先确认目标行/接口真的落了（DB 或 `findById` 回读逐字段比）；②再调 `do/detection` 重算；③仍不变才怀疑读源分族（不同校验器读源不统一是**可能**存在的，属 UNVERIFIED，需单独取证），不要一上来就归因缓存。
- **检码字典与读面口径全表见 `references/detection-codes.md`**（03103/03104/03108/03907/02104/04004 逐码的病灶+修法、`search` vs `do/detection` 两面口径、字段绑定存空的 03907 变体对账法）。排构建失败先读检测面拿结构化条目（带 path/element），比翻流水线截断 msg 精确一个量级。
- **检测条目集合的变化才是修法的判据，不是条数**：改一处后必须 `do/detection` 重算，逐条对比「哪些消了、哪些新冒」，再下结论。**重算后条数变多不是改坏了——快照面本来就没算全，真算会展开更多校验器**；只有「目标码消失且无新分支」才算修复。
- **修法方向未经重算验证前一律标 UNVERIFIED，不得写进报告当修复**：微流程 `UDC_MICRO_FLOW_04004` 就是反例——把 BASIC 参数的 `appName/inApp/udcApp` 置 null 后 REST `checkSchema`+`update` 均成功、DB 回读确实为 null，但重算后 04004 从 1 条变 4 条并新冒「所选应用与当前微流程的 OpenApi 标识不一致」。只回读 DB 就宣布修好 = 假成功。
- **新建菜单绑定的空白页面会阻断部署**：菜单建页面时选了实体但页面画布没放控件，构建的一致性检测报 `UDC_CE_PAGE_03907`（ERROR，document=[页面名:WEB端或移动端], element=[菜单]或[栏目]）→ `发布失败: 业务异常[一致性检测未通过]`。WARN 级（如 `UDC_CE_MICRO_FLOW_04003` 未保存的微流程）不阻断。检测明细同时写 Kafka 部署通知消息体（`DeployNoticeMsgDto`），grep pod 日志消息内容即得，不用连 Redis。修复 = 往页面放控件后重新构建；**空详情页可用「克隆成熟页 schema」法补齐（REST 直做，不必手拖），配方见 `references/page-schema-api-construction.md`「空页面补齐」节**——但克隆会把模板页的 `events[]` 一起带过来，指向目标应用里不存在的微流程/页面，反而新报 `UDC_CE_PAGE_03104`（page widget event association microFlow not exist）/`03103`，**克隆后必须清事件**（顶层 `eventDefine={}` + 各控件 `events=[]`+`eventDefine={}`）再保存。
- **勾选的每个适配终端各生成一份独立页面定义，空一份就阻断一份**：建菜单勾 web端+移动端 → graphql `udcPageInfoSearchNoPagePost`（variables `body.params.appId`=数字 appId 字符串）返回 PC 与 MOBILE 两份定义（`urlType` 字段区分）。拖控件只能补一份，另一份照样空页面照样 FAIL。**部署失败→清空页面的完整循环**（不依赖拖拽）：deploy-normal → FAIL → grep udc pod 日志 `UDC_CE_PAGE_03907` 拿 `document=[页面名:终端]` 定位空页面 → graphql `udcPageInfoDeletePost`（mutation，body `{"id":"<空页面定义id>"}`）删除 → 再 deploy-normal → 重复直到检测全绿。实测：首页 MOBILE、列表页 PC+MOBILE、栏目 PORTLET 四个空页面逐个删完后 v1.0.2 构建一致性检测全绿 → SUCCESS。
- 流水线可观测阶段（udc pod 日志）：`UdcBpmDetectionUtil ==>buildAppInfo` → `CdpDeployTask 应用发布任务-数据中台-数据预置`（~2s）→ `CdpDataDetectionTask 一致性检测`（~108s）→ `AbstractDeployService.doParallel(:242)`。
- **部署收敛等待期旧 Error pod 会拖住整个部署**：sandbox 部署完成检查轮询 `podlist[app]` 要求全部 pod 收敛（日志 `获取podlist成功,size:[N]` 每分钟刷一次）；历史构建留下的 `0/1 Error` 旧 ReplicaSet pod 只要还在，podlist 永远含未 ready 项，部署长时间停在"部署完成"前不翻 state=1（state 0 可能挂十几分钟）。解法：`kubectl delete pod <旧Error pods> --force --grace-period=0`（普通 delete 会被 ReplicaSet 重新拉起，要 force），清完等一次轮询周期（~10s）部署即收敛。只删**非当前构建 ReplicaSet** 的 Error pod，别误删正在跑的新 pod。
- **新应用(纯新建)的设计器内建实体通道不受“应用不能为空”限制**：REST POST /service/udc/entity 对未发布应用报 `BOOT_1001 应用不能为空`，但设计器 UI（实体 tab → lined-plus → 表单）对新应用直接可用——实体进树+字段编辑器+保存全链 LIVE 通过。原因：设计器内走的是设计态草稿链，不走 REST 的运行态校验。
- 读 RDS：本机 python + pymysql 直连（凭据在 seeyon-low-code-environment/.env 的 SEEYON_DB_*，已验证可直查 udc_test2 拿 schema 样本）；本机不通再退跳板 host 的 python3+pymysql（host 上常无 mysql client 但有 pymysql）。密码含 `&` 用 base64 包探针脚本传过去，避开 shell 转义。token 自主续期 / RDS 访问 / Redis 明细读取的现状与可用入口，见 `references/test2-env-access.md`。
- 只页应用 `POST /service/udc/application/create-page-app`（`CreateOnlyPageApplicationDto`，平铺）：`masterEntity` 是 **String（实体 fullName 裸字符串，非 id 非表名非 JSON）**——字节码证实它被直接 `UdcEntityMetaDataSearchDto.setFullName(masterEntity)`，而 appName 取自 `hostAppName` 参数。主实体必须已注册进元数据中心（先建实体→deploy-normal 全链成功后 `meta-data/select-entity` 查得到，全链 ~19min）。**宿主应用元数据有悬空依赖时该接口直接 NPE**（`CustomPageInfoService.create4CustomPage:892`，依赖应用 stream→toSet() 中 `.apply` null，实体元数据匹配已通过后仍炸）——与一致性检测的参照/枚举悬空同源，是宿主数据病，不是调用姿势问题；bill 模板与 standard 简模板双复现，换宿主或修数据前此路不通。`status:2` 静默业务失败的真实原因不在响应体，必须 grep pod 日志 traceId 拿 `ExceptionHandleFilter` 的 MESSAGE。

## 把链路固化进 seeyon-agent 仓库（`<SEEYON_AGENT_ROOT>`）

- 部署全链耗时的真实分布（LIVE 双观测）：代码生成+打包上传 ~2.5min → 沙箱后端编译 ~3.7min（mvnd）→ 前端构建 → 沙箱重启 → DeployChangeEvent state=SUCCESS。判定部署完成不靠时间猜——`POST /service/udc/application/appVersion/{appGuid}` 查 deploy_record，或捞 udc pod 日志 traceId 的 DeployEventListener 行。deploy 触发后元数据注册有延迟，`select-entity` 查不到≠失败。

- agent 保持 **readonly**：写契约在 `layer.py` 仍判 `DENIED`（`contract.write` → POLICY_DENIED），宿主（Hermes/CC/Codex）拿方案 data 自己执行。新增的是**部署方案生成器**（`components/platform_operations/deployment.py` 的 `build_deployment_plan` + `seeyon_host_bootstrap.deploy_plan()`），出可执行 steps data（4 步：entity→attribute→page→deploy），不出写。
- **生成面能力清单（2026-10，离线声明级，宿主执行）**：`build_deployment_plan` 属性语义键白名单 `_ATTR_SEMANTIC_KEYS` = **multiSelect / relationType / relationApp / relationEntity / uniqueness（仅此 5 键，逐键须有 AttributeDto 受键的 LIVE/静态证据才入白名单）**——`indexSource` 属索引对象（udc_index.index_source）不是属性键；`required/length/defaultValue` 无建属性 create 受键证据，白名单外键宿主带了也白搭（平台不认 → BOOT_3002 或静默忽略），要带须先取证再扩白名单。attribute step body 必须带 `appId`(数字 Long) + `entityId`(`<entity_id>` 占位，宿主建实体返回后替换，与 page step 同约定)——只出 name/caption/dataType 的计划宿主照做必 BOOT_1001；body 是逐条列表，note 必须讲清数组包装一次性 POST 报 BOOT_3002 须逐条循环。`infer_datatype` 的 java 类型映射顺序敏感——`LocalDateTime` 必须先于 `Date` 子串判断（都含 "Date"，旧顺序把 LocalDateTime 误判 DATE）；`UdcPlanner.plan` 遍历 spec 全部 entities/pages/microflows（早期只取每类第一个，多对象应用漏对象）；`components/construction/page_schema.py` 的 `PageSchemaRenderer` 出列表页 pageSchema 声明级骨架（三控件 UdcFilter/UdcToolBar/UdcDataGridView + collectComponentStatus 三 operate 键 + grid dataSource 11 键控件顶层 + 属性→列映射），列 ~58 全键/guid/按钮对象/搜索字段进 `unverified_fields` 由宿主照标品 deep-copy 补齐，不臆造；`components/construction/microflow.py` 出微流程 create/checkSchema body 骨架：`build_microflow_create_body`（19 键照 REST create 键位字典，dataSchema 必须 `json.dumps` 字符串化，triggerType 走字符串枚举 `BUSINESS_EVENT|MANUAL|SCHEDULE`，值域外进 unknowns 不臆造）、`check_schema_body`（create 同 body 剔 unknowns）、`fill_schema_template`（模板 `${占位符}` 递归替换，未解析占位符原样保留并返回 unresolved 列表，宿主必须补齐才提交）——填充前后键位集合必须不变（递归 keyset 比对作测试断言，落实「零缺失零多余键」铁律，多一个键 checkSchema 可能静默不过）；节点富结构（RETRIEVE condition / CHANGE_ENTITY attrType ~18 键）离线不可证，不进构造器，宿主照标品既有行/preset_template deep-copy 补真值。`generate_from_requirement` 是自然语言需求离线入口。
- **执行层已支持通用契约分派 + 活体校准（2026-10 实测 5/5 活体 PASS）**：`_request` 按 registry 契约通用构建路由（不再 4-op 硬编码），占位符填充 = `required_inputs` ∪ 路径实际占位符 ∪ intent.context；`{id}` 语义消歧（entity_id 显式 > application_id 回退）；缺参 raise 不臆造。**{appId}/{id} 类 Long 占位符必须取数字形态**——字符串 app 名（前缀+数字）被 Spring NumberFormatException 拒（BOOT_3000 实测），取数字段（write-chain R1R2 证据同源）；identity 比对同步数字归一。**网关前缀双形态**：`/udc/*` 设计态 → `/service/udc/...`；`udc-runtime/*` 运行态 → `/service/udc/udc-runtime/...`（单拼 `/service` 会变成 `/serviceudc-runtime/...` 全 404——全量推送测试抓出的真 bug）。post-read 型契约 `effective=False` 是有意门控（执行链只放 GET），活体验证走 live_probe 旁路。
- 活体证据文档落 `docs/audit/udc-design-time-deploy-write-contracts.md`（全链表 + 页面契约错路标定 + 未验证项）。
- registry `default()` 里登记写契约用真实枚举（`OperationStatus.OBSERVED`，不是 `OBSERVED_LIVE`——写错名会让整个 registry 构造炸，所有契约测试连带挂）。
- **固化产物 `components/udc/live_write_templates.py`（LIVE 写链模板，planner 可直接引用）**：11 条写链（8 REST + 3 GraphQL，含 `page_schema_draft`）每条带真实 path/op + javap 权威 body 模板 + LIVE 回执（id+回读数）+ 约束清单；`build_order()` 依赖序（枚举→枚举项→实体→字段→索引→菜单→页面→微流程）；`VALIDATION_RULES` 收录实测错误码换来的约束。配套读接口回读模板 9 条。有测试钉住（含依赖序：菜单先于页面、枚举先于枚举字段）。LIVE 细节见 `references/designer-frontend-call-chain.md` 的「写链 LIVE 全通」节。
- **planner 与 LIVE 模板已对接**：`UdcPlanner._step()` 新增 `live_template` 参数——挂了模板的 step 证据级自动升为 `LIVE`（低级证据才升，OBSERVED_LIVE 保留原级）；e2e 测试的 `ALLOWED_EVIDENCE` 白名单已加入 `"LIVE"`。`page_create_base` step 的 op 已修正为真实路径 `/udc/page-info/base-info/create`（旧 `/udc/page-layout/base-info/create` 是错的）。新增证据级时同步改三处：`_BUILD_EVIDENCE_LEVELS`、e2e 的 `ALLOWED_EVIDENCE`、test_planner_build 的分级断言。加新 step（如 `page_schema_formal`）时同步三处步数断言：test_planner_build 的 `sequence_order` 动作清单、test_order_app_e2e 的步数展开公式（每页 2 步变 3 步）、以及模板数断言（`len(WRITE_TEMPLATES) == N`）。
- **页面 schema 必须真绑实体，空壳 schema 是伪交付（用户当场揪出）**：只塞 `settings.entity` 的 UdcDataGridView 能过 `update-draf`（BOOT_0000、schemaState 翻 DRAFT），但没有 dataSource 绑定、没有列定义，不是设计器真实产物——「接口能通」≠「做出真东西」。真绑三要素（dataSource ENTITY + entity.fullName 硬格式 / columns 逐字段映射 / uiModel）与保存双链（update-draf→update，body 同构字段名不同）见 `references/designer-frontend-call-chain.md` 的「写链 v3」节与 `docs/audit/udc-semantics/PAGE-SCHEMA-REAL-BIND.md`。构造前先解剖同应用一个成熟页的 schema（`page-info/detail/{id}`，41KB 级）当结构基准，别手拼。
- **组件全参数 + 业务列两条用户定理（页面 schema 的验收标准）**：①做任何组件操作必须带全该组件的参数类型字段与可设置项——最小桩/空壳即使保存通过也不是交付，对照同应用成熟页逐键对齐；②表格 columns 只放业务字段，9 个系统预置字段（creator/updater/createTime/updateTime/tenantId/draft/version/creatorDepartment/creatorPost/creatorInstitution，新建实体自动生成）不写进列——成熟页 13 列零系统字段实证这是设计器默认行为，把系统列摆给业务用户会被当场打回。
- **行/工具栏按钮的 openPage 事件必须指向真实存在的详情页，且字段带全**：详情页（pageType=DETAIL + UdcForm 绑实体）先于列表页行按钮建（LIST+DETAIL 成对）；openPage 事件除 actionType/actionName 外必须带 `pageInfoId`（详情页真实 id）、`pageUrl`、`inApp:true`、`openType`、`masterEntity`、`paramsMapping`（preset_id + PRESET_DETAIL_PAGE_OPEN_MODE，值 create/edit/view）——缺目标页或缺参数映射，设计器事件面板渲染 `undefined [undefined]` 且行为无落地（用户截图实证）。按钮↔事件关联 = `addOperates[].id == events[].eventType`。页面规则（udc-runtime/filter-plan）是独立对象，建页面不自动带，按模块功能推进时单独建。
- **bundle 抽出的 op 目录必须双向对账才收口**：从主 store bundle 正则抽 op 建目录后，用双向 verifier 核对（仓内 `tools/scan_write_ops.py --verify <bundle>`）——「目录有 bundle 无」= 凭记忆/跨源臆造（实测抓到：单属性删除 op 只在 LIVE 冒烟用过、主 store bundle 根本没有它的 fieldType 定义；这类 LIVE-only op 移出 bundle 目录，单列 `LIVE_EVIDENCED_OPS` 分源登记，证据锚点分开）；「bundle 有目录无」= 漏登记（实测漏了 33 条读链 GET——页面加载必需面，只登记写链会让读面被当成"不存在"）。verb（读写语义）永远只是名字推断，带 `?` 输出，不作事实断言。
- **主 store bundle 里 op 有两条 service 约定并存，扫描/对账器必须都抓**：(a) saga 描述符 `load({fieldType:"X",paramsType,paramsKey})`；(b) 内联 raw Apollo 文档字符串 `"\nmutation udcXxxPost ($body: udcXxxPostInputBody) { ... }"`。只 grep `fieldType:` 会静默漏掉所有走 Apollo 字符串的 op（实测一次就漏 18 个，含参照 ConfigInfo 4 个）。对账的"臆造"判定要按"命中 (a) 或 (b) 任一"通过；(b) 的三元组由变量声明归一（`$body`→`…InputBody`、`$path`→`…InputPath`、`$query`→`…InputQuery`），与 (a) 同构登记。**(b) 的正则前缀绝不能用 `\b`**：bundle 里这些文档字符串嵌在 JS 转义里（`o="\nmutation udcXxx…`），`mutation` 前一个字符是字面的 `n`（转义 `\n` 的第二字符），`n` 与 `m` 都是 word 字符 → `\b` 不成立 → 该 op 静默漏扫。用 `(mutation|query)\s+(udc[A-Za-z0-9]+)` 即可（op 名必须 `udc` 前缀 + 紧跟 `(`，误中率≈0）。排障法：单测正则对一份干净样本能匹配、对 bundle 却 0 命中，就是这种边界前缀被转义字符吃掉——去掉前缀锚点再验。
- **主 store bundle 里 op 有第三条约定：op 名由字符串拼接** `fieldType:"".concat("udc","UdcRuntimeFilterPlanPost")`（webpack 压缩后常见），或变量前缀 `"".concat(n,"UdcXxx")` 且 `n="udcUdc"` 同 chunk 绑定。只覆盖前两条约定（saga load / raw Apollo 字符串）会把整族 op 漏在视野外（实测漏 10+ 个 FilterPlan/pageInfo 族）。扫描器须三条并抓，拼接的 paramsType/paramsKey 在 match 后 ~260 字符窗口内多为明文可直读（读不到才按后缀推，不猜前缀名）；对账的「臆造」判定改为「命中 a/b/c 任一」。
- **抽枚举/值域表必须逐个实跑取全量，别凭名字组合猜**：反编译枚举类时每个 `@GetMapping`/`@PostMapping` 的完整 value、枚举常量构造参数、DTO 的 `@NotNull` 字段都要逐个 java -jar cfr 跑出来计数，不能只跑前几个就外推全部（`OperatorEnum` 22 个、`ParamTypeEnum` 5 个、`MetadataTypeEnum` 14 个都是实跑出的全量）。猜出的值域 deployed 到校验器里就是误报源。
- **LIVE 探针证据优先于静态 bundle 推断；两者冲突时先想「是不是两条不同通道」，不要急着推翻已 LIVE 的契约**（曾犯：把 `build_filter_plan_body` 从 LIVE 坐实的 REST `/udc-runtime/filter-plan/create-new` + 数字码 planType 改成 bundle 读到的 GraphQL `udcUdcRuntimeFilterPlanPost` + 字符串 `"FILTER"`，属误推翻）。实测澄清：`udc_filter_plan` 有**两条并存通道**——设计器前端走 GraphQL `udcUdcRuntimeFilterPlanPost`（planType 字符串），LIVE 探针走的 REST 写面收**数字码** planType（0=FILTER 隐藏 / 2=LIST 可见，响应回读 FILTER/LIST，DB 存数字码）。同对象的两条链并存，勿互相覆盖；静态 bundle 只能证「设计器通道」，改 LIVE 已证的构造器前必须先找该探针证据（skill 各条 + references）比对，冲突先登记为「双通道」而非「旧的是错的」。写面/读面/DB 三层形态不同是平台常态（`planType:2`→`"LIST"`、`source:5`→`MICRO_FLOW_MESSAGE`、`actionType:1`→`UPDATE`）。
- **参照「设置参照内容」向导的提交链按 `id` 分流两个不同 op，不是单个 createOrUpdate**：`module53993` 组件 `onClick → … → module332.Jt → udcApolloQuery( e.id ? udcReferConfigUpdateConfigInfoPost : udcReferConfigCreateConfigInfoPost )`；读=`udcReferConfigListPost`、删=`udcReferConfigDeleteByGroupIdPost`。写 body 前先看组件提交 handler 拿的是哪个 op（有 id 走更新、无 id 走新建），别只按名字里的 createOrUpdate 猜。
- **导航域覆盖审计矩阵（用户「每个地方都要测试到」的落地形）**：用一份测试（`tests/udc/test_domain_coverage.py`）把设计器每个导航域（应用/实体/菜单/规则/流程/BI/栏目/设置/角色）的**可执行落点**（builder/validator/op 目录/registry op）逐一断言存在，缺域即 FAIL——这是「用法进了代码没有」的完整性验收面，不是 live 行为验收（两者分开声称）。新增域模型时必须同步进该矩阵的落点清单，别只加模块不加断言。
- **构建面计划器（plan_build）与只读计划器（plan）必须分开**：`UdcPlanner.plan()`/`plan_application()` 是既有只读契约（有硬测试钉住 `mode=="dry-run"` + `write_operations==[]`），永不能改产写操作；新增构建面逻辑一律另开 `plan_build(spec)` 方法。构建计划的每步带 `channel(graphql|rest)` + `op` + `body_builder` + `evidence` 分级；**引用 op 必须经内部 `op_entry(op)` 解析成功才入步，解析不出 → 落 unknowns，绝不臆造 op 名**（列表里未声明的对象也不臆造生成，只落 unknowns 提示扩展 spec）。破坏性步骤（Deploy ON_ONLINE）标 `destructive` 交宿主先确认；`executed/writes_performed` 恒 False（agent 不出写）。
- **`body_builder` 字符串必须指真实可导入的模块全路径，否则宿主找错模块**：曾把 `construction/metadata_artifacts.py` 里的构造器写成裸 `metadata_artifacts.xxx`（宿主会去 udc/ 下找而落空）。统一写 `construction.metadata_artifacts.*` / `construction.microflow.*`（`components/construction/` 下），udc 内的写 `attribute_semantics.*` / `layout_model.*` 等同级模块名。**加一条可解析性测试钉住**：正则抽出计划里每个 `模块.符号`，`importlib.import_module` 后 `hasattr` 断言存在——防再指错。
- **spec 模型扩展只用带默认值的可选字段，向后兼容**：给 dataclass 加新字段一律给默认值（`field(default_factory=list)` / `None` / `""`），既有调用方的位置/关键字构造不破；`to_dict` 只序列化非默认值（保持旧输出形状）。验证法：一条旧式最小构造 + 一条全语义构造各跑一次，断言旧输出字典逐键不变。
- **离线计划生成器交付前必做「宿主执行视角」审计（多遍复核法）**：部署计划/方案 data 是宿主逐字执行的，交付前至少换四个角度逐行过一遍——①证据角：每个透传键/白名单键回查 skill 与源码证据，无证据键剔除（键还容易跨对象错置：属性键 ≠ 索引键 ≠ 页面键）；②执行角：假设宿主照 body 原样 POST，必填键在不在（appId/entityId 类占位符）、容器形态对不对（列表=逐条发 vs 数组包装=BOOT_3002）；③边界角：默认值/未提供输入是否被臆造进输出——**推不出的值出显式占位符（`<entity_full_name>`、`<numeric_app_id>`），绝不生成「看起来对」的 plausible 假值**：浅包名 `com.seeyon.{app}.{Entity}` 能骗过粗审，真值是深包名 `com.seeyon.<pkg>.domain.entity.<Pascal>`，离线无从推起；app name 无尾数段时 appId 同理（可推就提尾数段，推不出就占位，别回落成 app name）；④异常角：宿主传错输入时抛**带格式要求 + 平台实测错误码的 `ValueError`**，别放裸 `AttributeError`/`TypeError` 出去——裸异常只描述崩溃点（`NoneType.group`、`int() argument`），宿主分不清是自己输入错还是生成器坏，更拿不到「该改成什么形态」（`_to_app_id` 无尾数段、枚举项 `code` 传 None/非数字须引 `BOOT_3002 to type Int` 说明整型要求）；⑤已知值角：**调用时已知的值必须设为必填参数，绝不留占位符**——平台 `validate:true` 会把 `<pageUrl>`、`<entity_id>`、`<uuid>` 原样存库，方案建成、planType/plan_type 也对，但条件运行时永不命中，而 validate:true 又让人误判全对（占位符只留给真·推不出的运行时值，承接③边界角）。复核是多轮独立视角，不是把同一套绿灯重跑一遍——每轮换手段：批跑边界探针（空列表/None/非法类型/无尾数段一批跑完看谁崩）、全仓 `py_compile`、`git status --porcelain` 核对改动面；用户会明确要求「多审计检查几遍」，按这个标准交。审计发现的真缺陷立即 TDD 收口（RED 复现 → 修 → 全量回归），别只登记不动。`LiveReadonlyRunner` 信封门（`_envelope_gates`：HTTP 2xx + status==0）就是这条路的产物。
- **文档计数契约**：`test_documentation_contract` 强制 README/agent-version-audit/code-reality-audit 里 `N passed` = pytest 收集数。加测试必须同步改这 3 个文档的数字，否则全挂；测试计数还被 CLAUDE.template.md、Hermes-SKILL.md、EVIDENCE-DISCIPLINE.md、ARCHITECTURE.md、STATUS.md 引用——批量改用脚本做 `376→395` 这类全文替换后，跑全量 pytest 验证文档契约测试归零。计数更新后用 `_documented_count` 语义检查：同文件内残留旧数字（如正文叙述里）也会使断言失败，需全文归一。**流程：先 `pytest tests --collect-only -q` 拿新收集数（注意是收集数不是 passed 数，含契约自检）→ `grep -n <旧数>` 逐个文件归一所有出现处（表格行/代码块注释/叙述三处形态都有）→ 全量 pytest 归零**。每批新增测试都会触发一次，一批一次，别攒到最后。
- **★ 改文档只做「定长字节替换」，别用正则扫数字或 `write_text` 回写**：三条硬坑一次性叠在同一处——① `re.sub(rb'15[0-9][0-9]', ...)` 这种宽泛数字正则会命中正文里的行号/日期/版本号，一次破掉多处；② 变量取空时会把数字替换成**空串**，把「N passed」写成「 passed」，而且改完后 grep `1532` 一个都搜不到，看起来像“没改动”；③ Python `Path.write_text()` 在 Windows 下默认文本模式会把 **LF 转成 CRLF**，原文件是 LF 时全文件变脏，13 行的真实改动会胀成 900+ 行 diff。
  ⇒ 定式：`sed 's/^$//'` 式精确串替换用 `path.read_bytes().replace(b'<旧>', b'<新>')` + `write_bytes`（零换行改写）；先 `sys.exit(1)` 级断言新数非空再写；破了大就用 `git checkout -- <file>` 回原状重做，**不要在已破的文件上继续打补丁**。
- **写盘前先看目标文件的历史换行符**：本轮把三份 LF 文档误写成 CRLF 后 diff 膨胀，已提交前的自查手段 = `git show HEAD:<file>` 与当前 `read_bytes()` 各数一遍 `\r\n` 与纯 LF，对不上就归一化回原状再提交。
- **测试隔离夹具进 conftest.py 而不是环境变量猜**：**只对真正不能入仓的资产**（客户 golden 样本等）在 `tests/conftest.py` 里解析资产根路径 + `pytest.mark.skipif` 自动跳过——保证「仓库干净」与「测试可跑」互不牺牲；清理仓库时先跑全量测试确认零断链再提交。
- **平台/公开产物不是「仓库外资产」，要入仓**：从 OSS/Artifactory/远端拉回的 bundle/chunk/jar 快照无客户数据、可复现，应提交进仓（如 `docs/audit/artifacts/udc-frontend-<ver>/chunks/`），让断言每次都真跑；只有带客户数据的样本才走 skipif。**别把断言的权威证据只放 scratch**：scratch 24h 空闲即被清，测试据此 `skipif` 会**静默 skip 而非 FAIL**——全量跑报「N passed」看着全绿，其实覆盖率已丢（本仓踩过：3 个 `test_graphql_write_ops.py` 断言 store chunk 的测试因快照仅存 scratch 被清而 skip，全量只报 `699 passed, 3 skipped`）。修法：权威快照入仓 + 测试路径优先仓内件、退化 scratch（`BUNDLE = _REPO if _REPO.exists() else _SCRATCH`）；**看到 skip 先查夹具是不是 scratch-only**，别把 skipped 当绿。
- **跑仓内测试/导入仓内模块一律用仓自带 venv 的解释器**：`<SEEYON_AGENT_ROOT>/.venv/Scripts/python.exe -m pytest tests -q`。环境里裸 `python -m pytest` 报 `No module named pytest`、`import components.platform_operations.registry` 报 `No module named 'yaml'`——都不是仓坏了，是解释器选错；别据此判依赖缺失或去改 import。测试失败优先看是不是自己新动的那块，仓有长期存在的护栏若与本次无关（例如把可变域计数当契约的扫描护栏），独立如实标注、别当成自己引入的回归。
- **测试里算仓根路径必须 `Path(__file__).resolve().parents[N]`，别省 `.resolve()`**：pytest 下 `__file__` 可能是相对路径（如 `tests/udc/xxx.py`），裸 `parents[1]` 会解析成 `tests/` 而非仓根，读仓内产物文件报 FileNotFoundError——而且**只在 pytest 里暴露，单跑脚本正常**，别据此判文件不存在。`tests/udc/` 下的测试是 `parents[2]`。
- 凭据 0 入仓：DB 密码 / Nacos token / eyJ 串提交前 grep 复扫；凭据只走 `config/` 路径引用（铁律 040402）。
- 本地骨架预览目录（`.hermes-preview-*`）加进 `.gitignore`，别 `git add .` 带进仓库。
- 宿主集成面（bootstrap 五能力签名、adapters/mcp server 约束、扩展纪律）见 `references/seeyon-agent-capability-faces.md`。

## 源码面全量测绘（Artifactory 拉 JAR → javap 全景，标品模块通用模式）

- JAR 源 = `http://10.0.0.1/artifactory/libs-release/com/seeyon/<artifact>`；版本清单用 `/artifactory/api/storage/libs-release/com/seeyon/<artifact>` 的 `children` 枚举，再下对应 `.jar`。**jar 本体落本地 Maven 库**（约定在 `config/environments.yaml` 的 `local-maven.maven_root`，默认 `<MAVEN_REPO>/com/seeyon`），路径 = `{maven_root}/{artifact}/{version}/{artifact}-{version}.jar`；**jar / class 一律不入 git**（`.gitignore` 已排除 `tools/jars/*.jar`、`*.class`），入仓的只有 javap 文本产物。用户口径：**「拉下来本地 repo」= jar 落到 `{maven_root}` 且真的 javap 出产物落仓，不是只在 pod 里 SSH 跑一次 javap 就完事**——pull + extract 是同一件事的两半。拉完**必校 sha256**：`sha256sum <local>` 比 `/artifactory/api/storage/libs-release/com/seeyon/<artifact>/<ver>/<artifact>-<ver>.jar` 响应里的 `checksums.sha256`，一致才算下载完整。**本机 JDK 可用**（`<LOCAL_ROOT>/java/bin/javap.exe` / `jar.exe`，JDK 21）——不必再 SSH 到 pod 跑 javap；`jar xf` 解 class 用 native 路径，别用 MSYS `/tmp`。`udc-web` 5.3.517 内含**全部 54 个设计态 Controller**——一次反编译即得设计态 REST 全景（671 个 API），不要逐模块猜 URL。
- **udc-web / udc-biz 都有 javap 产物落仓**：udc-web → `docs/audit/artifacts/udc-web-5.3.517-javap/`（54 .javap.txt + `_API-PANORAMA.md` + `_full_api_map.json`）、`docs/audit/artifacts/udc-web-5.3.517-contracts/`（机器提取的类级路径+@HasRole+**方法级完整 URL `_api_full.json`**，见下）与 `docs/audit/artifacts/udc-web-5.3.517-methods/`（方法级 `_methods.json`）；udc-biz → `docs/audit/artifacts/udc-biz-5.3.517/`（`_codegen_templates.json` 代码生成模板全景 + `_package_census.json` 包结构 + `_UDC-BIZ-PANORAMA.md` + `resources/` 机制配置 + 关键类 javap），生成脚本 `tools/core/decompile/extract_udc_biz.py`（`--jar` + `--classes`）/ `tools/core/decompile/extract_udc_biz_resources.py` / `tools/core/decompile/extract_udc_web_contracts.py` / `tools/core/decompile/extract_udc_web_methods.py` / `tools/core/decompile/merge_udc_web_api.py`（均可重跑）。新一轮模块测绘先查这些产物再补增量，别重扫。**`_full_api_map.json` 的 `class_mapping` 字段不可靠**（实测 EntityController 显示 `search/term`）——类级路径只用 javap 实证的 `_contracts.json`，方法级取 `_methods.json`/`_api_full.json`。udc-biz 包结构量级：`microflow` 455 / `autocode` 362 / `detection` 314 / `entity` 207 class。
- **udc-biz 的 1063 个非 class 资源是平台机制的权威配置，别只当打包杂物**：`auth/{draft,deploy}-auth.json`（设计态 vs 部署态权限）、`openApi/entityOpenApi.json`（openAPI 四操作→方法清单）、`stereotype/<name>/config.json`（版型 necessaryFeatures/availableFeatures/dataFlowEnabled）、`feature/<name>/config.json`（18 特征→attributeSet）、`presetData/*.json`（预置实体/属性能力矩阵/枚举/字段集）、`microflow/*WhiteList.json`（9 标准事件全类名/服务白名单）。提取脚本 `tools/core/decompile/extract_udc_biz_resources.py` → `docs/audit/artifacts/udc-biz-<ver>/resources/`；固化模型 `components/udc/platform_mechanism_model.py`。**jar 内配置是比「照标品实体反推」高一级的证据**（平台自身声明，非观测推断）——能取到就优先信它。关键：openAPI 创建=`create,createBatch,create4bpm`（删除/更新各 3，查询 11）；设计态允许 entity/attribute 增删改、部署态禁 update+delete = 「已上架版本无法 添加/复制/转移」的服务端机制根因。全表见 `references/udc-biz-config-resources.md`。
- **javap -v 常量池 Utf8 顺序 = 注解声明顺序**，一次抽全 54 controller 的类级路径 + 角色：`RequestMapping` 后紧跟的那个 Utf8 就是类级路径（如 `udc/entity`）；`HasRole` 后连续字面量是被引用角色名（用已知角色集过滤混入的类型名）。脚本 `tools/core/decompile/extract_udc_web_contracts.py` 产 `docs/audit/artifacts/udc-web-<ver>-contracts/`（`_contracts.json` + per-controller `.javap.txt` + `_CONTROLLER-CONTRACTS.md`）。实测主门 `udcAppDesigner` 覆盖 46 controller、`udcSystemAdmin` 45；类级无 `@HasRole` 仅 5 个（MetaData/OperationLog/Parameter/UdcDesignMetadata/UdcFile）。与人工审计逐条吻合，可作对账基线。
- **方法级 REST 契约全量提取：javap -v 每个方法的注解块印在它自己的 Code 之后**（`RuntimeVisibleAnnotations:` 在方法属性区），归属 = **其前最近的方法签名**，块内 javap 已渲染成可读形态 `value="更新"` / `value=["update"]`。**不要按常量池 `#N` 顺序找「方法名后紧跟注解」**——注解类型/描述是共享常量池条目，按序列扫会跨方法串位（实测把 `copyFunction` 配到 `/cancel/app-biz-home`、`findMenuTree` 配到 `findPageInParams`）。完整 URL = 类级路径 + 方法级 value；**方法级 mapping 无 value → 真路径 = 类级根**（`createFunction` 无 value → `POST /udc/function`，别自行补 `/createFunction`）；方法级 value 以 `/` 开头**仍拼在类级路径下，不是绝对路径**（Spring 语义：类级 `udc/page-info` + 方法级 `/base-info/create` = `/udc/page-info/base-info/create`；按「绝对路径」拼成 `/udc/base-info/create` 线上 404 实测——`_api_full.json` 里此类条目（base-info/create、update-draf 族）就是这个错，引用前先对照 skill 建页节的 LIVE 路径）。**无任何 mapping 注解的 public 方法不是端点**（如 `ApplicationController.saveAsTemplate`）——按方法名兜底会把非 API 算进总数，须过滤（657 比旧 `_full_api_map` 的 671 更准，剔的就是这类）。脚本 `tools/core/decompile/extract_udc_web_methods.py` → `tools/core/decompile/merge_udc_web_api.py` 产 `_api_full.json`（54 controller / 657 方法 / 654 带编号中文描述如 `1.1:创建实体`）；与手录 `FUNCTION_ENDPOINTS` 逐字吻合（`/udc/function/create/function-refer`、`/udc/entity/{id}/parent`、`/udc/function/page/in_params/{referId}`）。**`.javap.txt` 是 GBK**：`read_bytes().decode("gbk")`；javap 已把注解值渲染成可读中文，**不要再 `_gbk()` 二次转**（latin1→gbk 会对已解码文本二次损坏，desc 全变乱码）。
- **8 导航域 API 归类模型**（`components/udc/nav_domain_model.py`）：把 udc-web 657 方法全归入侧边栏 8 域（应用/实体/菜单/规则/栏目/设置走 udc；**流程=bpm、BI=cdp-data 是两个独立服务域**，另表登记），逐域给 controller/API/POST 数 + `domain_full_paths()` 完整 URL 清单；`tests/udc/test_nav_domain_api.py` 断言全归类无遗漏无重复、合计=657。各域子菜单/对象映射与**新增子域模型清单**（`*_api_model` 系列：application/entity/entity_sub/column/menu/microflow/rule_sub/settings_sub/design_metadata/enum）见 `references/udc-web-api-panorama.md`。
- **域级缺口对账法**（`tools/domain_api_gap.py` —— **已移入 `_attic_pending/one-off/unsorted/`**，仓库内无此路径；方法本身仍适用）：判定某 API「已被模型引用」必须**既扫源码文本、又跑各 `*_api_model` 的语义映射函数**（`_model_resolved_paths()` 收集运行时解析出的 full_path 并集）。只做文本扫描会把已建模的 API 全判成空白（假阳性）——模型在运行时解析出 `full_path`，源码里只出现语义键/方法名，`full_path` 字面量根本不在文本里。修此判定后再逐域补齐，收口标准 = 657/657 全引用、空白 0。
- 批量 javap 的坑：解压 class 用 zipfile；subprocess 必须 list 形式传参（路径含空格，cmd 字符串拼接会静默失败）；输出按 GBK/utf-8 errors='replace' 读（`.javap.txt` 是 **GBK**，按 utf-8 读全是乱码、中文 group 名直接废）；产物全空 = 编码/参数炸了，先单文件调通再批量。**本机 git-bash 常没有 `javap`/`strings`（JDK 工具不在 PATH）**：直接用 Python `struct` 解 class 常量池逐条读 Utf8（magic→常量池循环），类级 `@RequestMapping`、方法路径、`@RestApiOperation` 中文描述、`@HasRole` 角色名全是明文 Utf8，比 javap 还快、无需 JDK。**expression 端点不在 udc 系 jar**——udc-web 54 个 controller / udc-biz / udc-starter-runtime 全无，它在 `boot-starter-formula`（`com.seeyon.boot.starter.formula.controller.ExpressionController`，类级 `expression`、无 @HasRole）；端点字典见 `references/metadata-artifact-apis.md`。
- **设计器拖拽生成的元数据直查 DB，别让用户逐控件手拖采样**：页面 schema 在 `udc_test2.udc_page_schema`（PAGE → childById → 控件树 JSON；标品复杂页 70KB+、13+ 控件类型）；微流程定义在 `udc_microflow_info`（`{type,triggerType,nodes[]}`）。拿标品应用的行当样本即可还原 JSON 结构。
- 用户纪律：每个标品模块都按「JAR 反编译 → Controller 映射 → 前端包元数据 → DB schema 样本」扫代码链路，读懂前后端代码自己推协议；发现的每个接口当场落 URL 台账/事实格——事后补记曾被视为失职。

## 页面设计态可用 API 构造（拖拽只是前端 Redux 状态，不是协议限制）

**不要因为"设计态要拖控件"就判定该通道只能人工。** 拖拽写入的是 Redux 里的控件树，保存动作就是一个 GraphQL mutation，请求体完全可从前端包源码里读出来直接构造——已 LIVE 打通「构造列表页 → 保存 → deploy-normal → jar 1.0.4 成功」。正确顺序：拉前端 `src_redux_store_ts` 找 `submitPage` 的 action creator → 读出 mutation 名与 variables 结构 → 按标品 `udc_page_schema` 行反推 schema JSON 骨架 → 直接 POST。**前端 bundle 是第一协议源**：mutation 名、body 字段、GraphQL 双层 variables、参数类型全在 chunk 源码里（grep `udcPageInfo` / `submitPage` / `addPage`），比反编译 jar 快且准——服务端只能告诉你错，前端告诉你对的写法。chunk 的取法（`/udc/remoteEntry.js` → `.u` 链 → `/udc/<chunk>.<hash>.js`）、`queryLoader.load` 描述符契约与取不到时的处理见 `references/designer-frontend-call-chain.md`。
- **控件是前端 JSON 注册，不是存数据库**：设计器左侧每个控件该拼哪些 settings/dataSource/uiModel 键，定义在前端 bundle 的控件 schema 注册表（`getControlSchema(type, terminal)` 返回每控件一份内置 schema，经 Redux `cmps.byId[terminal]` 消费），拖入画布即实例化这份默认 JSON 进页面树；DB `udc_page_schema` 只存**实例化后**的页面 schema，不存控件定义。→ 某控件"必填哪些字段"的权威源是前端内置控件 schema；深拷贝标品页 DB 行是可行代理，但源头在 bundle 注册表。读不到 bundle 注册表时退回"照标品同类控件 deep-copy"。
- **组装前先读懂前端组装+校验规矩，别靠浏览器试错**（用户方法论）：构造任何 pageSchema 前，先读前端代码搞清（1）JSON 怎么组装（childById 树 + 每控件必填键）（2）怎么校验——前端 schema 驱动（`getControlSchema(type)`），后端 submitPage 不校验结构、部署时一致性检测才拦。"每次加控件→保存→看一致性错误→修"是兜底迭代，不是首选；首选按前端 schema 规矩一次构造对。
- **单点探测否定不了功能（用户方法论纠正：「别死抓一个示例不放」）**：某 panel 字段空着、某候选 query 返 0、某枚举拒绝某个值，都只证明「这一条探测路径」不通，**不证明功能不存在**——先把该面板的全部 tab/变体/通道枚举出来（例：「事件选择器」有『应用内』`udcMicroflowFilterEventPost` 与『应用间』`udcMicroflowSearchAppsPost`+`udcMicroflowFilterMqPost` 两个 tab，BPM 流程事件只在后者），**再从前端渲染 chunk 顺链定位**：chunk 名即源码路径（`src_pages_*`/`src_components_*`）→ `wakaru --unpack auto` 解出该页/面板的渲染模块 → 读按钮 `onClick` 与组件 `onConfirm` 的组装 → 得真实 op + body/JSON → 翻译成字段语义。有 REA 逆向工具（`analyze_web_bundle` / `recover_javascript_sources` / `analyze_javascript_application`）时优先用它做 bundle 结构分析与源码恢复，别只靠文本 grep 死磕。

- **鉴权走 Cookie 不走 header**：写操作必须带 `Cookie: SY_ACCESS_TOKEN=<jwt>`（配套 `TK_EXP` / `SY_UID`）。发 `accessToken` header 会得到 `BOOT_1006` 跳 SSO，且响应看似 200——别把 header 形态当契约，读前端 fetch 拦截器确认实际挂载位置。token 续期后从登录响应的 `Set-Cookie` 头同步取 cookie 三件套（续期流程见 `references/test2-env-access.md`）。另：本机 python urllib 直连 test2 会间歇 `SSL: UNEXPECTED_EOF_WHILE_READING`（带 retry 也复现）——subprocess 调 `curl --retry 3 --retry-delay 2` 稳定；GraphQL body 大时写临时文件用 `--data-binary @file`，避开 shell 转义。
- **★ 用户红线：不要自己导出/复用 token；人工登录好之后，写操作只在那个标签页里发 `fetch`**（`credentials:'include'`，配方见 `references/udc-web-console-cdp.md`「带 cookie 调 Seeyon REST」）。从浏览器 cookie 抄出 `SY_ACCESS_TOKEN` 再去 urllib 直连，等于给用户手工建立的会话另开一条出口：平台一旦判定为新登录/异常会话就把该 token 打进黑名单（`BOOT_1006 token黑名单`），用户正开着的页面当场失效。用户对此的原话是「不是你别自己获取 token 啊，直接就黑名单了」。
  **连带坑（本轮实测）**：从页面 cookie 读出 token 后**用它向服务端发请求做验证**（哪怕只是 GET 探活）也算「自己获取 token」——用户建好的会话不该被复制出去用。验证渠道是否可用，应该**在那个已登录的标签页里用 `fetch` 试**，而不是把 token 抄到脚本里。页内 fetch 抓到请求原文（`window.fetch` 包装器记录 url + body）既能拿到接口形态，又不碰 token。
- **同平台多账号会互相踢号，旧 token 立即进黑名单**：平台侧一个用户只保留一个有效会话，登录 B 账号会把 A 已有 token 拉黑（实测 `BOOT_1006`），**不分浏览器 profile、不分调试端口**。⇒ 引入第二个账号前先确认它**对目标应用有权限**（用它的 token 直呼该 app 的设计态读面，403 / `server_404` 就是没权限），否则代价是「新号顶不上 + 原号被拉黑」双输。多账号不能用来隔离并行任务，只能当只读探针。
- **GraphQL mutation 的统一包装形态（`graphqlLoader` + `$params0` + `body:`）**：除少数带 `id/path` 直参数的特例外，绝大多数写 op 都是这个骨架——
  ```
  POST /service/udc/graphql?<opName>
  {"query":"mutation graphqlLoader ($params0: <opName>InputBody) { data0: <opName>(body: $params0) { code data { content } message status } }",
   "variables":{"params0":{...真 body...}}}
  ```
  三个易错点逐个对应一种报错长相：① `query` 必须是 GraphQL 字符串，只发 JSON 对象 → `Invalid Syntax : offending token '<EOF>' at line 1 column 1`；② 参数必须走 `$params0` 变量 + `body: $params0`，把字段名当实参（`ids:`/`id:`/`input:`…）→ `UnknownArgument: Unknown field argument X`；③ 静态类型从报错里反推——`Field 'X' in type 'Y' is undefined` 说明选错了返回字段名，`UnknownArgument` 说明实参名错，两者都写成 JSON 报 `Invalid Syntax`。
  **不要去猜参数名**：`UnknownArgument` 的暴力试错成本是 N 次往返，而正确形态只有一种；猜两轮不中就改抓页面真实请求（或问用户要一段现成 Network 报文），比继续枚举快一个量级。
  `introspection` 在本平台被禁（`{"__schema..."}` 返回 `GraphQL未生成接口:__schema`），所以无法用标准内省发现 schema——字段/参数只能从前端 chunk、报错反馈或真实抓包得到。
- **GraphQL body 的 params 层数逐 query 实测，别当全局规则**：多数 search 类 query 确实是双层 `{"variables":{"body":{"params":{"params":{...},"sort":{...}}}}}`——筛选条件在内层 `params`，少一层返回空列表而非报错，静默失败。**但 `udcPageInfoSearchNoPagePost` 是单层 `body.params.appId`**：套双层会报 `UDC_APP_0001 The application is not exist`（层多了不是静默，是报「应用不存在」——见到这个错先怀疑 params 层数多了一层，不是应用真不存在）。层数以 skill 各 query 条目记的形态为准，拿不准先发单层看报错。
- **`paramsType` 不只有 `InputBody/InputPath/InputQuery`，禁止按命名规律猜**：同 bundle 里另有 `Long`（`udcIndexEntityListPost`——必须传裸实体 id，套 `{entityId:{…}}` 对象静默空返且无 code）、`String`、`Map`、`[String]`、以及 **`[XxxInputBody]` 数组包装（10 个批量 op，含 DTO Create/UpdateDtoWithAttrsPost、AttributeGroup/EntityGroup 批量族）**。参数容器形态以 chunk 抽到的 `paramsType` 原文为准，猜错的失败长相是「HTTP 200 + code 空 + content null」，不是报错。
- **业务码成功 ≠ 数据变动（删除类必查 `content`）**：`code==BOOT_0000` 但 `content=0` = 一行没删——批量删 `[<id>]` 与 `[{id}]` 两种数组传法实测都得 0，**单删 op（`{id}`）才 `content=1`**。删除验收必须断言 `content>=1` + 回读确认对象已不存在；只看 code 会把假成功当 PASS（比「HTTP 200 不算成功」更隐蔽一层：信封也是成功形态，数据没动）。
- **前端代码生成引擎有硬契约**：`component-status-deps.js` 里 `collectComponentStatus` 无条件遍历 `settings.topOperates` / `settings.actionColumnOperates` / `settings.operateButtons`（可用但不可省），任一缺失 → 生成期 `TypeError` → 部署 `state=2`，**错误指向空对象而不是缺失字段名**——两次部署报的字段名不同（先 topOperates 后 actionColumnOperates）就是同一契约在逐字段暴露。`UdcDataGridView` 还必须带 `settings.dataSource.entity.{id,name,fullName,appName,caption}`。写任何组件 schema 前先照标品页面的这三个键补齐。失败明细直接读 `udc_deploy_record.msg`（含完整 TypeError 栈 + frontBuild.log 的 storageKey 下载链接），改 schema → 重新 submitPage → 再 deploy-normal 即可迭代，无需去 pod 翻构建日志。
- **部署 state 语义（实测修正）**：`udc_deploy_record.state` = 2 失败（msg 带原因）、0 构建中/过渡、1 成功终态——连续六个成功部署（jar 1.0.5→1.0.9）终态全为 1，成功行也曾在中途读到 0 后翻转为 1，所以**单次读到 0/1 都不是终态，轮询到连续两次不变再定论**。`state=0` 过渡态是分钟级；`update_time` 小时级不再动且 state 恒 0 = 异常滞留（全库基线：每天仅 1-2 条滞留 0 vs 15-21 条翻 1），别再空等轮询，转查去重跳过/锁/流水线未启动——**`build_id`/`flow_id` 在成功行同样为 NULL，不能当流水线是否启动的判据**。msg 空串佐证成功。**jar 版本号 +1 是"确实跑过流水线"的旁证，但不能替代 state**。数字枚举拿不准时，以 `POST /udc/application/appVersion/{appGuid}` 回读的 `state:SUCCESS|FAIL` 字符串字段仲裁。
- 最小可用列表页骨架（filter + toolbar + datagrid 的字段与 operate 键位）见 `references/page-schema-api-construction.md`。建**新页**（非改写）走 mutation `addPage → udcPageInfoBaseInfoCreatePost`；终端信息报错时缺的是 `curTerminalType`（顶层 body 字段），不是 urlType。`addPage` 的 `appId` 必须数字 Long（字符串报 `BOOT_3002 Failed to deserialize ... to type Long`）——`submitPage` 的 body 里 `appId` 却接受字符串，两个 mutation 的类型契约不同，别互相套。
- **controller 代跑后必须归档作废的 pending HANDOFF**：直接完成某环工作后，把对应的过时 `<UTC>-main-to-implementer-HANDOFF.json` 从 `<session>/inbox/` 移入 `<session>/history/inbox/`（归档勿删），再向 main 发一条 HUMAN_MESSAGE 写明结果+证据路径+「勿重派同一 HANDOFF」——否则 watcher 下次唤醒会让 implementer 重跑已完成的任务，产生重复数据/重复写面。
- **列定义照标品深拷贝，禁止手拼字段**：渲染引擎要求每列 ~58 个键，`componentName:"列"` 缺失时渲染器不识别该列（表格显示异常的头号根因），`title`/`hide`/`sorter`/`headerAlign`/`uiModel`/`dateFormat`/`showFormat` 等同样缺一不可；grid 顶层另需 `borderStyles`/`zebra`/`paginationAlign`/`inputPagenationNum`/`showSetting`/`enableOrderNumber`（序号列）。手拼 33 键的列部署成功但渲染残缺，且部署 state=0 不报错——**部署通过 ≠ 渲染正确**。做法：`udc_page_schema` 里 `LIKE '%actionColumnOperates%'` 找同类型标品页，deepcopy 一列当模板只替换 columnId/columnIndex/dataIndex/dataFieldId/fieldPath/dataFieldCaption/fullName/dataType/widthValue。**最终验收拉部署产物 metadata zip 对照运行时渲染 schema**（拉法与对照点见 `references/runtime-data-write-probe.md` 的 metadata zip 节）——设计态 DB 对 ≠ 运行时渲染对。
- **按钮组合按数据语义选型，别套单据模板**：明细/字典类列表不放 新增/导出（无 DETAIL 表单页时 ENTITY_NEW 无落地页，导出无报表配置，点击即空转）；行操作放**操作列**（`enableActionColumn:true` + `settings.actionColumnOperates`，`buttonType:"link"`），不放顶部 topOperates；数据刷新由表格控件经 filterSetting/dataSource 自理，页面顶部不放刷新按钮。先问"这页的数据语义是什么"再选按钮集，用户按业务常识核对 UI，套错模板一眼就穿帮。
- **顶部操作列删除 vs 行内删除的语义差**：顶部删除按钮（配 rowSelect 勾选）是单据批量删除模式；明细表用**操作列删除**（标品取证：actionColumnOperates 内 删除项 + grid events 里 `actionType:"widget"`+`actionName:"ENTITY_DELETE"`+`target:<表格id>`+`callbackDataType:"ROW_DATA"`+`noticeEntitys`）。用户看到顶部删除会直接质疑"删除啥"——按钮位置本身就是数据语义的 UI 表达。
- **列表页行「编辑」走 openPage 穿透详情，不用 ENTITY_EDIT 行内编辑**：标品行操作事件全是 `actionType:buildin/actionName:openPage` + `pageInfoType:DETAIL` + `paramsMapping`（`preset_id` 取 `CURRENT_ROW id <表格id>`，`PRESET_DETAIL_PAGE_OPEN_MODE` 常量 create/edit/view 区分新增/编辑/查看）；ENTITY_EDIT 是行内编辑语义，标品页不出现——用户看到 ENTITY_EDIT 和自造事件会直接质疑「事件绑定和标品对不上」。**交付前列页四查**（用户点名过的四类缺陷）：①行操作事件形态逐条对照标品页；②顶栏 `enableTopOperates:true` 且每个按钮在 `events[]` 有绑定（没绑 = 按钮无行为）；③filter `advancedSetting.<entityId>.fields` 挂齐搜索字段（只挂 quickSearch 无字段 = 「没有搜索」）；④过滤方案 planType 见 metadata-artifact-apis.md（planType:0 页面不可见）。**多挂标品没有的事件（如自作主张的 onDataLoad→微流程）与漏绑同罪**。
- **grid 的 dataSource 是控件顶层字段，且必须带完整 11 键**（`type/subType/key/isRoot/isRef/dataShape/entity/fields/dataTarget/fieldBindMap/hiddenFields`，entity 含 id/name/fullName/caption/stereotype/category/supportOrderNo/appName/appId）：放错进 `settings` 就是渲染层「重复表查询没选实体」——页面画布上数据源显示为空。`componentName:"重复表查询"` 等控件级标识也只在顶层。最终验证拉 metadata zip 对照（见 `references/runtime-data-write-probe.md`）。
- **同模式适用微流程（dataSchema JSON，udcMicroflowUpdatePost 已 LIVE 打通）；建应用仍是唯一需要 UI 表单的环节（REST create 落残记录，见上）。**
- **微流程节点分前后端两类，保存通道通≠节点合法**：后端代码生成节点（有 `autocode/JAVA/*/templates/microflow/<Type>Activity.java.ftl` 模板）＝ CreateVariable/ChangeVariable/CreateList/ChangeList/CreateMap/MapOperation/PublishBusinessEvent/ListOperation/SubMicroFlow/CallAppService/CallDataFlow/Connector/Retrieve/RetrieveArray/CreateEntity/CreateBatchEntity/ChangeBatchEntity/DeleteEntity/ConvertData/DataMapping；`MESSAGE_INFO` 等 web 类节点**无后端模板**，代码生成器 switch 静默跳过——构建不报错、也不生成任何 Java（用 MESSAGE_INFO 验"保存通道"可以，验"微流程功能"不行；需真实功能验证时节点必须选带模板的后端类型）。生成模板全清单从 udc-biz jar 的 `autocode/JAVA/2.9/templates/microflow/` 枚举，别猜节点类型。保存 body：`udcMicroflowUpdatePost`（`/service/udc/graphql`），`{id,guid,appId,name,caption,dataSchema:JSON串,type:0,triggerType:2,versionCode:100,groupType:0,state,sourceId,orderNum,microFlowGroupId,serviceInterface}`——**不带 id 报 BOOT_4002 无权限**；type/triggerType 传 DB 数字枚举（udc_microflow_info 实值），传字符串形态会被拒。dataSchema 骨架 `{sourceType,trigger:MFStartNode,endNode:END_NODE,nodes[]}`（照 udc_microflow_info.data_schema 既有行 deep-copy）。
- **页面事件绑定在 `childById[控件].events[]`，不在顶层 eventDefine**（标品页顶层两字段同为空，别在那找）；eventDefine[] 只是登记元数据（key/name/params/paramsKeys）。一条事件 `{id:nanoId, eventType, condition, actionType:microflow, actionName:microflow, microFlow:<微流程id>}`——actionType=microflow 时 microFlow 字段填 udc_microflow_info.id。改完照 submitPage 全 body 重提交（沿用实体绑定/页面字段），BOOT_0000 后 DB 回读 events[] 确认。
- **token 续期端点与 cookie 形态**：`POST /service/ctp-user/auth/token`（body 含 loginName/password/clientType/loginDevice/captchaId/locale/guestUri，凭据放独立 JSON 不进 git），响应取 `data.content['access-token']`（键名带连字符），**Set-Cookie 头带三件套 `SY_ACCESS_TOKEN / TK_EXP / SY_UID`**——续期脚本必须从响应头护 cookie，只读 body 会漏。token 窗口约 19h。该凭据 JSON 的 note 应写明续期接口用法，让下个会话不用再问人。
- **续期报密码不符立即停手；「已过期」要先探再信**：续期返回 `USER_0055`（用户名/密码不符）说明密码已改，**不要重试**——响应 message 明示连续失败 N 次后触发验证码锁，自动重试是在烧锁定额度。另外凭据 JSON 里记的过期时间是保守估计，token 服务端可能仍有效：先拿旧 cookie 发一个只读请求探活，再下「已过期」的结论（实测本地记录过期次日 cookie 仍通）。
- **GraphQL 双通道不在同一面**：设计态（/service/udc/graphql）与各服务（/service/ctp-user/graphql、/service/portal/graphql、/service/app-common/graphql）各自独立，schema 不互通——在 ctp-user 面上查 udc 的 query 报 FieldUndefined。UI 页面加载时全部发到本域的 `/service/<bundle>/graphql`，按 bundle 路由到对应服务。
- **构造出的按钮"没行为"= settings.events[] 没绑，不是页面构造失败**：控件行为挂在 `page_schema.childById.<控件>.events[]` 数组（不在顶层 eventDefine/pageDefinedEvents——标品页这两个字段同样为空）。一条事件：`{id:nanoId, eventType:<按钮的 addOperates[].id>, condition:false, actionType:<见下>, actionName:<动作枚举>, microFlow:<微流程id 仅 microflow>, condEvents:[], enableValidate:false}`；eventType 填按钮 id 就是"把行为挂到该按钮"的机制。**actionType 值域实为 buildin | widget | microflow | eventThrow 四类**（第四类的值字符串平台拼错为 `enevtThrow`，照抄别修正；另有页面动作枚举 `VALIDATE_ENTITY`，与实体规则的 VALIDATE 组无关，别混）：widget 用于"对控件生效"的行操作（ENTITY_DELETE/ENTITY_EDIT 必须带 `callbackDataType:"ROW_DATA"` + `target:<表格控件id>` + `noticeEntitys:[实体fullName]`——noticeEntitys 是删除后刷新表格的机制，漏了删完不刷新）；buildin 用于 openPage 类跳转（小写 `openPage`，带 `paramsMapping`，当前行取参写 `CONTEXT_VARIABLE` 值 `CURRENT_ROW <字段> <表格id>`）；microflow 类必须先建微流程拿 id。内置动作枚举 60+

## 设计态搭建管线实证（2026-10 zzprobe 全链，REST 直连）

REST 直连设计态写链在**已部署过一次的应用**上全链可用（deploy_plan step body 实证）：

1. **建实体** `POST /service/udc/entity`，body `{appId:Long, name, caption, stereotype:"bill", entityNature:"MAIN", features:"basic,approve,...", multiplicity, category, parentEntityId:"0", superior:"0", validate:true}` → `BOOT_0000` + `data.content=实体数字id`；回读 `GET select-all-by-entityId/{id}` 拿 `tableName`（如 `dingdan_599...`）。
2. **建属性** 单条循环（见上），回读 `select-all-by-entity-id/{entityId}` 确认业务属性 entityId 归属全部正确、无孤儿。
3. **建页面** LIST+DETAIL 双页，`deploy_plan` step3 body 把 `<entity_id>` 替换后直接可用。
4. **微流程/BI 设计态保存端点证据不足时不猜**：MicroFlowController 在 udc-web 设计器包（maven 无此构件，当时从 pod 取），graphql 依赖运行态（未部署报 server_404"请重启服务或重新发布"）；BI `gantt-chart-schema/search` 路由到 udc-web 但报「接口错误」参数形态未取证。阻断如实登记到 write-chain 证据件，不瞑试端点。
5. **需求→实体模型**：`RequirementParser` 输入格式约束——实体行 `新建一个实体「X」标题：Y`（冒号必须有，中文后缀会破捕获），字段行 `- name：类型别名`（行尾带中文说明会破 `$` 锚导致整行不匹配；Decimal 要写 `小数` 或 `BigDecimal`）。
6. 全链证据落 `core/facts/udc/write-chain/evidence/DESIGN-BUILD-*.json`（建成的 id/tableName/页面 id + 协议新知 + 阻断项）。

### 建实体必填：`stereotype` + `category`（两个不同字段，别只给一个）

LIVE 逐层报错链（缺一个推开一层）：

```
POST /service/udc/entity {appId,appName,name,caption}
  → BOOT_1001 「业务版型 archive/standard/bill/archiveTree/form 选一 不能为空」   ⇒ 缺 stereotype
POST + {stereotype:"bill"}
  → 仍报同类错（提示语指向「实体性质」）                                     ⇒ 缺 category
POST + {stereotype:"standard", category:"ENTITY"}
  → BOOT_0000 + data.content = 实体数字 id
```

- **`category` 才是「实体性质」，值取 `"ENTITY"`**；`stereotype` 才是「业务版型/版型」，值 `standard`/`bill`/`archive`/`archiveTree`/`form`。把“实体性质”当 stereotype 重传同一个字段会原地打转。
- **报错文案会误导**：「业务版型」与「实体性质」两条文案相似，看不出缺的是哪个字段。逐层补齐直到成功，别猜。
- 两个字段的合法值**从同应用既有实体回读拿，不靠猜**：`GET /service/udc/entity/select-all-by-appid/{appId}` 取一条成熟实体，直接看它的 `stereotype`/`category`/`features`/`multiplicity` 原值，照抄后在同应用用。
- 建字段 `POST /service/udc/entity/attribute`（单条对象，不数组）：`{appId,appName,entityId,entityName,name,caption,dataType,orderNo,required,unique,searchable,dataFormat,length,precisionValue}`；STRING 用 `length`、DECIMAL 用 `precisionValue:"18,2"`、DATE 用 `dataFormat:"yyyy-MM-dd"`、BOOLEAN 无附加。回读 `GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}` 逐条核 `name/dataType`。
- **建实体成功 ≠ 可用**：它还要走本 skill「保存→发布→构建」序列才会生成物理表；单次 create 只算设计态落库。

## 应用上线/健康端点（DeploymentController，实测命中）

- `POST /service/udc/deployment/app-ready-state`（body `{"appId":<数字>}`）→ `state:"RUNNING", msg:"DEPLOY_SUCCESS"` = 沙箱健康、数据链路可用；这是最便宜的运行态健康探针。
- `POST /service/udc/deployment/app-online` / `app-online-new`（body 为 `DeployNormalDto`：appId/deployType/pushEnv 字符串/DeployEnvInfoDto{currentEnv,pushEnv,gitBranch,hasHandWrittenPage}）= 应用上线/跨环境发布。**pushEnv 合法取值 `"TEST"`（LIVE，解掉旧「目标环境为空」未解项）**：**平铺** body `{appId:数字Long, deployType:"RELEASE", projectType:"ALL", terminalType:"ALL", pushEnv:"TEST"}` → BOOT_0000 + `data.content=deploy_id` 并新增 `udc_deploy_record`（入队 state=0；入队≠成功，构建结果仍按 state 轮询判）。同接口喂**包装体** `{deployDto:{...}}` 反报 `UDC_APP_0001 应用不存在`——app-online-new 是平铺绑定，与 deploy-normal 的 `@MultiRequestBody` 包装相反，同一部署族两形态并存，别互相套。**用户纪律：交付构建必须走设计器页面「构建」按钮触发**（按钮真实请求未与 app-online-new 逐字比对前，别拿 REST 触发冒充按钮构建交付；按钮请求可用 CDP `Network.requestWillBeSent` 抓包定形）。DTO 结构（`udc-common` 5.3.517）：`DeployNormalDto extends DeployParamDto{deployId, appId:Long, deployType, projectType, terminalType, pushEnv:String}` + `lockCompatibility/generateLog/entityFullNameCondition`。搜服务端错误文本定位类时，该字符串不在 udc-web/udc-common/udc-biz/boot-core/gateway-biz 已盘 jar 中——先确认错误抛在网关层再扫 jar。
- 注意区分：`app-online`（应用上线/发布到环境）≠ `deploy-normal`（构建部署）。构建成功后 `codeConfig.json` 里 `publishState:"UNPUBLISH"` 是预期态，不是部署失败的信号。

## 前缀不明时的取证顺序（别猜 URL）

1. `javap -v` 截尾段读类级注解（`sed -n '/^SourceFile/,$p'`）——优先，成本最低。
2. pod 访问日志枚举真实命中：`kubectl logs <udc-pod> --since=72h | grep -oE 'request url:[^,]*' | sort | uniq -c | sort -rn | head -25`。
3. 动词探针：405 = **该路径**已映射、动词错；404 且日志有 `AppContextFilter` 行 = 鉴权拒绝；404 且无日志行 = 前缀/网关没匹配上。**405 不等于"这就是那个操作"**——字面子路径会被兄弟 `/{id}` 映射吞掉：`POST /service/udc/application/create` 的 405 是 GET `/application/{id}` 把 `create` 当 id 匹配了，真正建应用在**类级根** `POST /service/udc/application`；同族真子路径为 `create-page-app` / `create-layout-app` / `create-from-template` / `appVersion/{appGuid}`。**create 常是裸 `@PostMapping`（方法级注解无 value）→ 真路径 = 类级根**：IndexController/EventController 的 create 均如此（`POST /service/udc/index`、`POST /service/udc/event`）——方法级注解读不到子路径时别自行补 `/create`，先读方法级 RuntimeVisibleAnnotations 再拼 URL。路径以 `javap -v` 常量池 `Utf8` 字面量为准。
4. 定位 DTO/枚举用 `javap -classpath '<jar目录>/*'`，不必先找到类归属哪个 jar。
5. **404 响应体的 `path` 字段直接回显服务端实际收到的路径 ——用它当“我到底请求了什么”的地面真值，比对自己拼的字符串可靠得多**：`{"status":404,"error":"Not Found","path":"/udc/enum/select-all-by-appid/8704..."}` 说明网关剥掉 `/service/` 后剩下的是 `/udc/...`。两个高频错觉都由它纰正：①**控制器类名 ≠ 路径段**——`UdcEntityController` 的类级路径是 `udc/entity`，拼成 `/service/udc/udc-entity` 会 404 且回显 `/udc/udc-entity`，见到回显里多一个名字段就是自己叠了一层；②**`/service/udc` 后面直接接资源名**（`/service/udc/entity/select-all-by-appid/{appId}`、`/service/udc/entity/attribute`），不是再接一个 `udc`。⇒ 探路径时先发一次、**读回显的 path 再决定下一版**，不要连续盲猜。
6. **405 是“路径存在、方法/绑定不对”的强信号，但要把两种 405 分开**：路由真的只挂了别的动词（换成 GET 即通），或者参数是 PathVariable 而你在用 query（`?id=999...` 报 `Failed to convert value of type 'java.lang.String' to required type 'java.lang.Long'` = 值从路径/其他绑定源取了字符串，**换参数名无效，换绑定位置才有效**）。

- **双发 identity 验收器必须配信封门，两次响应相同 ≠ 成功**：`LiveReadonlyRunner` 原逻辑只比同一请求双发的 md5 identity + auth-fail 判定，HTTP 500 与业务 `status=3` 的响应两次相同也会判 `PASS`（验收器不可信）。已修：`_envelope_gates` 检查 HTTP 2xx + 业务信封 `status==0`，任一不成立判 BLOCKED 并记 gate 原因；body 无 status 键（流式下载等）不臆造业务检查。自建任何双读/回读验收器时，identity 只证稳定性，必须与成功判据（HTTP 区间 + Seeyon 信封 status/code）组合作门槛，否则错误响应会静默通过验收。

## 删除探测残留的连锁失败（删前必读）

**删微流程/实体不会同步清理已生成的 Java 源码引用，下次构建才炸。** 典型形态：

```
XxxEntityService.java:[169] 程序包 com.seeyon.<app>.domain.message.<entity小写> 不存在
```

- **根因链**：`domain.message.<entity>` 包只在该实体**还有微流程引用**时才由生成器产出。删掉引用它的微流程后包不再生成，但实体自身生成的 `<Entity>Service.java` 仍 import 它 → 编译失败。实体和事件都还在，看起来「什么都没动」，实际是依赖被抽走。
- **删前必须画依赖图**：实体 ← 事件(`udc_event.source/source_id`) / 微流程(`data_schema` 里引用) / 页面 / 规则 / 菜单。先只读全表扫引用，确认零引用再删；顺序是**先删引用者、再删被引用者**，反过来必然留悬空。
- **报「删干净了还是构建失败」时**，不要默认是平台缓存或构建没跑——先按报错里的 Java 包名反查它在引用哪个实体，再查该实体还有哪些对象挂着。
- 删对象前先确认有无软删除/备份表（`udc_microflow_info_history` / `_del` / `_bak_<date>` 常不存在），没有就只能靠事前依赖图，事后无法还原。

## 清理枚举时的范围纪律

页面「枚举管理」列的是 `udc_enum` + `ctp_enum` 两表合集，**归属看 `app_id` 不看在哪个表**：`udc_enum` 带 `app_id` 的是本应用自建；`ctp_enum` 同时装着系统共享枚举和各应用枚举，`app_id` 为空/0 才是平台级（不可删）。

成熟应用动辄几百条枚举（业务枚举占绝大多数），**不要把整个集合当垃圾**。筛选用多条命中判据而不是「全部」：

- 实验标记：`code`/`name` 含 `xzh`/`zxj`/`小爪`/`实验` 等本次探测前缀
- 测试串：纯数字、`111`/`123`/`test`/`demo`
- 已软删：`is_delete=1`（页面已不可见，清不清物理行对构建无收益，**默认不清**）

筛选结果必须先列清单给用户确认再删。`ctp_enum.name` 可能是 `{"zh_CN":"..."}` 的 JSON 串，过滤前要解包再匹配，否则中文判据全部失效。

**引用扫描面（删前必跑，缺一面就会误删）**——枚举的真实引用只在这几处，别漏：

| 引用源 | 表/字段 | 判据 |
|---|---|---|
| 实体字段 | `udc_attribute` where `data_type='CTPENUM'` | `relation_entity`=枚举 id、`relation_code`=枚举 code |
| 微流程 | `udc_microflow_info.data_schema` | 文本 `LIKE '%<code>%'` |
| 页面 | `udc_page_schema.page_schema` / `.draft_page_schema` | 文本包含 code（**载体表是 `udc_page_schema`，不是 `udc_page_info`**——后者没有 `page_schema` 列，只有 `draft_page_schema`/`layout_info`/`page_url` 等） |
| 规则/生单 | `udc_data_flow` / `udc_data_flow_mapping` 的 schema 文本列 | 文本包含 code |

**★ 页面/资源/导出模板的权威载体是 `ctpEnumInfo` 块，不是任意文本子串**：

```jsonc
{"ctpEnumInfo": {"id": "<枚举id>", "code": "<枚举code>", "appId": "<应用id>",
                 "caption": "业务类型",
                 "CTPENUM": {"appName": "...", "fullName": "...",
                             "currentAppId": "...", "id": "<枚举id>"},
                 "relationCtpEnum": {"enumType": "SAME_LEVEL", "enumLevel": 0}}}
```

载体位置：页面 → `udc_page_schema.{page_schema,draft_page_schema}`；资源 → `udc_resource.{url_parameters,out_parameters}`；导出模板 → `ctp_excel_export_template.{metadata_content,excel_head_info}`。

**引用扫描必须带阳性/阴性对照**：
- **阳性对照**（取「实体属性正在用」的枚举 code）必须 100% 检出。检不出 → 检测方法有缺口，此时「无引用」结论**不成立**，不许下删除结论。
- **阴性对照**（取几个确定不存在的枚举 code）必须一个都不检出。命中 → 泛化子串匹配在误判（短 code 如 `bool` 会命中 `"boolean"`）。

**引用方自己已删的不算活引用**：判引用时必须把引用方的 `is_deleted` 一起查出来（`SELECT is_deleted` 漏了就会把已删资源误判成活引用，得到「这枚举不能删」的假警报）。活引用 = 引用方有效；死引用 = 引用方已删（仍要留档，说明「先删引用方才敢删枚举」是对的）。

- 扫描命中率与枚举 code 长度强相关：**短 code（如 `type`/`status`/`enums`）会在任何文本里随机命中**，所以“被引用”这一档要人工复核命中位置，不能只看计数。本仓实测：`type` 类枚举命中 20 处全来自微流程文本，而 372 个枚举里只有 7 个真正被 `CTPENUM` 字段引用。
- **页面 schema 不在 `page_schema` 列上时不要当“0 引用”报出去**：`udc_page_info` 有 `layout_info`/`page_url`/`draft_page_schema` 等多个长文本列，先 `describe_table` 把列名列全再选列；拿错列会得出“页面 0 引用”的假结论，而这一条往往就是误删的入口。检测不到就说检测不到，别把未覆盖写成零。
- 实体字段引用（`CTPENUM`）比微流程文本引用更硬：删掉会让字段悬空、下一次构建直接炸。用户说“微流程引用的不删”时，**实体字段引用同样要保留**——两者的后果都是构建期编译失败，没有区别。

**枚举删除端点 = GraphQL `udcEnumBatchDeletePost`（LIVE 批量删除成功）**，不是 REST `GET /udc/enum/delete`。后者是死路：`?id=`/`?enumId=` 一律报 `String→Long` 转换错、路径变量 `/delete/{id}` 报 404、POST/PUT/DELETE 全 405 ——见到这一串别再逐参数名/逐动词试，直接切 GraphQL。

```
POST /service/udc/graphql?udcEnumBatchDeletePost
{"query":"mutation graphqlLoader ($params0: udcEnumBatchDeletePostInputBody) { data0: udcEnumBatchDeletePost(body: $params0) { code data { content } message status } }",
 "variables":{"params0":{"ids":["<枚举id>",...]}}}
```

- **body 必须是 GraphQL 查询字符串**：只发 `{"ids":[...]}` 这类 JSON 对象会报 `Invalid Syntax : offending token '<EOF>' at line 1 column 1`；参数名不是 `ids/enumIds/idList/input/list/...` 任一自由名，而是 `$params0` + `body:` 变量传递（`UnknownArgument` 逐个反驳即此坑）。
- **假 id 预检的返回值语义**：19 位合法 Long（如 `999999999999999999`）返回 `BOOT_4002 数据不存在或无权限查看` = 格式正确、路由命中；返回 `Invalid Syntax`/`UnknownArgument` = 请求形态错；返回 `Index: 0, Size: 0` = 无参调用。

**枚举删除是逻辑删除（`is_delete=1`），物理行留在表里**：删完 `SELECT COUNT(*) ... WHERE app_id=X` 数字不变是**预期**，不是没删成功——验收必须数 `is_delete=0` 的行数，别数总行数。同理批量接口个别批次返回 `BOOT_4000 数据库错误` 时，数据往往已经生效（`is_delete` 已翻），改按 `is_delete` 回读判定，别当成整批失败重发。分 20 个一批稳定，收尾以「剩余 `is_delete=0` 数 == 保留清单数」为唯一判据。

删除前仍应用假 id 探一次；真删前的清单确认、备份（`ctp_enum` + `ctp_enum_item` 两个表全量导 JSON）与依赖分析照上文「范围纪律」执行。

### 枚举分组（分类）是独立对象，不是枚举的一个字段

枚举树的「分组」= `UdcEnumCategoryController`，端点 **GraphQL `udcEnumCategoryPost`（创建，LIVE）** / `udcEnumCategorySearch`（查询）。

- **落表是 `ctp_enum_category`，不是 `udc_enum_category`（LIVE 踩过）**：`ctp_enum_category` 列 = `id / tenant_id / create_time / update_time / version / guid / name / description / parent_id / order_no / is_delete / app_id / app_guid / host_app_name / is_preset / data_status / aggregation_app_name / original_id`。`udc_enum_category` 是另一张表（每应用只有一条 `name=默认分组, preset=1`），**新建的分组不会进它**——按 `udc_enum_category` 回读会得出「创建返回了 id 但没落库」的假结论，然后去怀疑 appGuid/参数，白绕一大圈。建完直接查 `ctp_enum_category WHERE app_id=<appId>` 验。
- 创建 body（逐字，LIVE `BOOT_0000`）：
  ```
  POST /service/udc/graphql?udcEnumCategoryPost
  {"query":"mutation graphqlLoader ($params0: udcEnumCategoryPostInputBody) { data0: udcEnumCategoryPost(body: $params0) { code data { content } message status } }",
   "variables":{"params0":{"name":"{\"zh_CN\":\"分组名\"}","orderNo":1,"appGuid":"<udc_application.guid>","hostAppName":null,"appId":"<数字appId 字符串>","dataStatus":false}}}
  ```
  `content` 返回分组 id。**`name` 是 `{"zh_CN":"..."}` 的 i18n JSON 字符串**（不是裸文本），`appGuid` 必填且取自 `udc_application.guid`（不是枚举表的 guid）。
- 本地构造器 = `components/construction/metadata_artifacts.build_enum_category_body`，校验器 = `components/udc/enum_constraints.validate_enum_category_body`（同文件的 `validate_enum_body` / `validate_enum_item_body` 把 `orderNo` 必填、`code` 必须整数、`name` 只允许大写字母+下划线三条约束变成可执行断言）。⚠️ **构造器产的是「语义 body」，与 GraphQL 实际的 i18n 形态不同**——提交前要把 `caption` 包成 `{"zh_CN":...}`、`name` 放英文编码，别把构造器输出直接当 `params0` 发。
- **枚举本身走 `udcEnumPost`（LIVE），字段语义与直觉相反**：`name` 放 `{"zh_CN":"显示名"}`（i18n 字符串 = 中文名），`code` 才是英文编码。把 `name` 当英文编码传会报 `BOOT_1001 枚举编码 不能为空`——报错里的「枚举编码」指的就是 `name` 槽位。分组归属用 `categoryId`。
- **枚举项 `udcEnumItemPost` 的标识字段已定（枚举项 body）**：`enumId` 与 `enumCode` **两个都要给**（只给 `enumId` 报「所属枚举编码 不能为 null」，只给 `enumCode` 报「所属枚举ID 不能为 null」）。真正的值槽位是 **`itemValue`**（字符串，缺它报「枚举项编码 不能为空」），**不是** `code`；上级项槽位是 **`parentId`**（顶层项填 `"0"`，缺它报「上级枚举项ID 不能为 null」）。完整 body：`{appId, enumId, enumCode, name(i18n JSON), itemValue, parentId, itemLevel:1, leaf:1, enable:1, orderNo, appGuid, hostAppName:null, dataStatus:false}`。落库表 `ctp_enum_item`，关键列 `item_value/enum_code/enum_id/parent_id/item_level/leaf`。老写法 `code`/`caption` 不是平台槽位，给 `code` 就报「枚举项编码 不能为空」。

## 报告

**用户问「九大模块（应用/实体/菜单/规则/流程/BI/栏目/设置/角色）各到什么程度」时，答案必须是可复算的实测数**——取数命令、分层口径、已知硬缺口形状、输出格式见 `references/domain-status-audit.md`（用仓内 venv 跑测试、SQL 数对象、`test_domain_coverage.py` 抽矩阵）。永远给「写链 LIVE 覆盖表」（✅已通/⚠️部分/⛔未通），并把「已 LIVE 打通」与「仅契约/仅只读」分开列。

结论分 LIVE PASS / 已调用但业务数据未验证 / 明确问题 / 未测。**报「完成度」必须分层，禁止把单层 100% 说成整体完成**（用户当场质疑过）：后端 API 契约层 100% ≠ 该域完成。逐层给百分比并注明口径：L1 契约（类级路径+方法级 URL+角色）／ L2 语义模型（语义键→API 映射）／ L3 请求体构造器 ／ L4 机制/规则 ／ L5 执行接线（planner plan_build）／ L6 LIVE 实机验证。且任何百分比都标「静态评估 or LIVE 结论」——契约/语义两层是静态源码事实，L6 必须真跑回读才算。**前端 UI 元素层（每个 tab 的按钮/拖拽/启用条件）是独立轴，不是契约层的子集**：它多半不产生后端请求，反向接口法根本抓不到；只有逐页拉前端 chunk 解析组件树+按钮事件绑定+拖拽配置，再换角色点验权限，才算记录。本仓现状：仅实体页 6 tab 做到按钮级，其余域 UI 元素层基本空白——被问及「按钮/拖拽都记录了吗」时如实说这个缺口，别用契约层数字糊弄。
- **推进序：前端页面功能是需求真相源，先前端 → 再对后端 → 最后执行**（用户定的顺序）：先逐页盘前端功能（页面→tab→每个按钮/拖拽/弹窗→触发接口→权限），盘完再与后端接口对账（前端调什么、后端有没有、缺什么），最后才谈执行。反过来先盘后端会整片漏掉「页面能点但属前端本地行为、根本不产生请求」的功能（拖拽排序、按权限隐藏/禁用、tab 懒加载、字段联动显隐），这类反向接口法抓不到。
- **先建前端全量基线再逐页盘**：一次性把 designer 全部 chunk 拉落本地建基线（配方与脚本见 `references/designer-frontend-call-chain.md` 的「全量 chunk 基线拉取」节），别用到哪挖到哪——碎片式取证回答不了「某域每个 tab 都记录了吗」。逐页盘 UI（文案/按钮/拖拽/事件）的解包抽取配方看同 reference 的「页面功能地图抽取」节；op 注册表在 `src_redux_store_ts`（1 次 grep 得全量 291 op），**单个页面 chunk 里 fieldType 命中≈0**（页面经共享 service 层间接调用，跨 chunk 变量 / React props），扫单 chunk 得 0 不代表该页不调接口——跨 chunk 桥接与连死边界见同 reference 的「op 注册表在 store chunk」节。**op 有三种抽取模式（saga load / apollo 串 / concat），只认 fieldType 会整批漏；op 分派中心 `getRequestByAppName` 有 8 个域命名空间（udc/bpm/ctpMetadata/portal/main/appCommon/ctpUser/appApproval），流程/BI 不在 udc 命名空间是代码级实证；页面→op 走 `X.xxxActions.method()` redux thunk** —— 三节配方见同 reference 的「op 分派中心」「页面 → action → op 链路」；前端 op 与后端的对账法见同 reference 的「前后端对账」节（两套命名不能直接比，命中率≈0）。**sourcemap 先探（test2 无 map）；minified 静态解析到顶后用 Node 运行时拦截拿 fn→op 真值（323 函数/322 op，见 designer-frontend-call-chain.md「运行时拦截」节）；微流程节点面板定义内置在 store chunk（31 条，与后端 microflow_model 值域交叉一致）；前端 UI 能力 = 前端代码 + 后端元数据 API（除微流程节点外面板值都运行时拉）** —— 见同 reference 的「sourcemap 探测 + 前端内置面板数据」节。**推进类任务自定方案一口气推到收口再汇报，中途不把选择题抛回用户**（用户多次只说「继续推进」「你自己一直推进」）：自己排顺序、自己定验收、自己清理探测残留，最后一次性列结果+残余；每步都问 = 把任务开销转嫁给用户。HTTP 200 或空结果不算通过，必须回读（元数据 identity / 物理表 DDL / deploy_record state），且**回读 identity 按读面实际形态断言**——REST 读面常把写面数字码展开成枚举名（`planType:2`→`"LIST"`、`source:5`→`MICRO_FLOW_MESSAGE`），拿写面值硬比会把 LIVE PASS 误判成失败；先打印回读原文再写断言，API + DB 双层全中才收口（读面清单与完整映射表见 `references/metadata-artifact-apis.md`）。**用户报告「我没看到 / 这对象是不是被删了」时同样先 API 回读（`findById/{id}` 逐条 + 列表 op + 应用/父对象详情）确认对象是否仍在，再查前端显示层（刷新缓存 + 展开折叠分组），不要顺着用户对原因的判断走**——数据在而 UI 不可见的头号原因是左侧树分组默认折叠、新建对象落在业务分组里，不是对象被删。**验收类元信息搭建（事件/索引/字段集/过滤方案等）需求未指定时，自定「最小合理业务需求」直接建一版交付验收（用户口径：你自己搞个需求，写就行），别把需求定义推回给用户；交付时写清业务语义——哪个事件挂什么动作、索引建在哪个字段、规则过滤什么——供验收。**本地生成的代码 = 未验证审计参照，绝不声明"已建成"。

## 生成器活体冒烟（A 层）：验证「离线生成器→活体」通路的最短序列

1. **续期 token**（见上凭据小节）；已过期别猜密码，直接走 `POST /service/ctp-user/auth/token`。
2. **当场重取目标 id，不用会话记忆**：`GET /service/udc/entity/primary/select-by-appid/<appId>` 取实体 → `GET /service/udc/entity/attribute/select-all-by-entity-id/<entityId>` 取属性；要页面/控件 id 就 DB 读 `udc_page_schema.page_schema`，在 `childById` 里找 `UdcDataGridView` 拿后缀与驱动实体。
3. **生成器产 body → POST 一次** → 记返回 id；同一对象别重复 POST（幂等但每次新建 id，授权测试应用上的产物越堆越多）。
4. **API 回读 identity 逐字段比**（按读面形态断言，见「报告」）。
5. **DB 双证**：元数据表 `SELECT` 对应行（索引/枚举/枚举项/DTO 属性/事件/过滤方案/属性各一），API + DB 全中才收 LIVE PASS。
6. **交付报告列产物清单**（对象 + id + 用途）让用户拍板保留还是清理——不默默删、也不默默堆在授权测试应用上。

含密码/新 token 的请求与响应临时文件**成败两路都要删**（脚本在写回阶段崩了也会把它们留在 TMPDIR）；凭据本体始终只走 `shared-credentials` 路径引用，不进仓、不进对话。

## 修共享仓库时防跨线误伤（多线并行时必读）

seeyon-agent 仓库常有多条线并行写不同目录（bpm facts、mcp adapter、demo 记录各自归各自的任务）。主线程只提交自己这轮的文件时，**用路径排除式 add 而不是 `git add -A`**：`git add -A -- <自己的文件列表> ':!core/facts/<别的线>' ':!adapters/<别的线>'`。提交前 `git status --porcelain` 过一眼，把属于其它会话的未收口改动留在工作区——它们是并行任务的过程态，主线程代提交会把半成品固化进历史。收口报告里把"已提交 / 完成但未提交（属其它线）"分开列，用户看进度时两条口径都要给。
