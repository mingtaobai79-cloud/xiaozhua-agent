# 非 udc-web 构件 REST 归位 + udc-web 契约方法级双缺陷

> 证据边界：**VERIFIED_STATIC_BYTECODE**（javap -v 常量池 RuntimeVisibleAnnotations / Utf8），
> 构件来源：Artifactory `libs-release-local/com/seeyon`（本机匿名可达，`10.0.0.1:80`）。
> 生成脚本：`tools/core/extract_component_contracts.py`（**已移入 `_attic_pending/one-off/unsorted/extract_component_contracts.py`**，仓库内已无此路径）（**仅构件级定域，勿作方法级权威源**）。
> 本文件对应完成判据「平台操作面」的余量补采。
> **2026-10-15 更正（缺陷 A/B/C/D 已修）**：契约权威总量为 **674**（见第 2 节），
> 文内旧记的 657 / 663 均作废；跨构件归位 **32 -> 27**（5 条改判回 udc-web，见第 1 节）。
> **2026-10-15 第四轮追加**：归位 **27 -> 31**（新增 boot-starter-excel / -formula / -file 4 条，
> 见第 3 节）；余量 **66 -> 62**；并首次落盘「62 条名单 + 93=31+62 互斥穷尽」的机械复算物
> `frontend-udc-unlocated.json` 与护栏 `tests/udc/test_frontend_udc_unlocated.py`。

## 0. 更正：这些构件**在本地/Artifactory 有事实源**

上一轮结论「99 未归位 op 的归属构件不在本地仓库」**表述不准确**，本轮更正：

- 扫描根 `<MAVEN_REPO>/com/seeyon` 实测 **1518** jar，其中按名 grep `udc` 仅 17 项 —— 该判断本身没错；
- 但 **Artifactory `libs-release-local/com/seeyon` 下实有 539 个构件**，
  `udc-biz / udc-extend / udc-starter-runtime / udc-common / udc-plugins` **均有 5.3.517**。
  上一轮只按构件名搜 `*message*` / `*component*` 而漏。
- 已实拉 **22** jar 落 `<HERMES_HOME>/cache/scratch/artif/`。
- `udc-web-5.3.517.jar` 的 sha256 与 `<MAVEN_REPO>` 副本**完全一致**（`0d6b0a65…`），
  说明该构件本地早已存在，「事实源缺口」并未覆盖它。

## 1. 归位结果：**31 / 93**（31/31 独立字节验证）

| 构件 | 承接 op 数 | Controller |
| --- | --- | --- |
| `boot-starter-sandbox-5.3.289` | 22 | `SandboxAppRun` / `SandboxClient` / `SandboxSystemConfig` / `SandboxTenantConfig` |
| `udc-portal-5.3.517` | 4 | `UdcPortalSpaceController`（类级 mapping = `udc/portal/portal-space`，**无** `BaseComponentController` 继承） |
| `udc-cdpbi-5.3.517` | 1 | `UdcReportController` <- `udcCdpDataReportGetReportListPost`（`extends BaseController`，类级 mapping = `udc/cdp-data/report`） |
| `boot-starter-excel-5.3.318` | 1 | `ExcelController`（第四轮新增，见第 3 节） |
| `boot-starter-formula-5.3.318` | 1 | `ExpressionController`（第四轮新增） |
| `boot-starter-file-5.3.358` | 2 | `FileController`（第四轮新增） |

**原表另有 5 条标注 `udc-web-5.3.517` 的「归位」——本轮更正为误判，见第 1.5 节，已移出。**

**验证方式独立于解析器**：对每条归位，直接在 class 常量池查四类证据字面量 ——
(1) 类级 mapping (2) 方法级 mapping (3) 方法名 (4) HTTP 动词注解。**31/31 齐备**。

**前缀叠加机制的三类实例（区分清楚，勿一刀切）**：
- **sandbox 族 22 条**：类级 mapping 无 `udc`（如 `sandbox/client`），前缀由 Spring 层
  `addPathPrefix` 对 `BaseComponentController` 子类叠加 -> `/udc/sandbox/...`；
- **udc 族 12 条**（portal 4 / cdpbi 1 / excel 1 / formula 1 / file 2 中的 udc 侧）：
  - portal 的类级 mapping **自带** `udc`（`udc/portal/portal-space`），且**不继承** `BaseComponentController`；
  - excel / formula / file 三类**继承** `BaseComponentController` 但类级 mapping 是 `excel` / `expression` / `file`
    （**无** `udc`）-> 与 sandbox 同构，前缀由 `addPathPrefix` 叠加；
  - cdpbi 继承的是 `BaseController`，类级 mapping **自带** `udc`（`udc/cdp-data/report`）。
⇒ 归位判定只能靠「类级 mapping + 方法级 mapping 恒拼接 + 前缀机制」，**不能**靠「类级 mapping 字符串里有没有 udc」。

### 1.5 更正：5 条「非 udc-web 归位」实为 udc-web 真实端点

`udcEntityAttributeGroupSearch` / `udcMetaDataMergeReferPost` /
`udcMetaDataSelectAggregationEntityPost` / `udcMetaDataSelectAppByIdPost` / `udcMicroflowSearch`
曾被记为「归到 udc-web 之外」。实为**缺陷 A 的次级症状**：提取器按方法名做 dict key，
同名重载后写覆盖前写，这 5 条端点在旧契约里**直接消失**，
于是「规则推不出」被误读成「不属 udc-web」。缺陷 A 修复（657 -> 674）后
5 条全部由 udc-web 契约产出（各自在 `EntityController` / `MetaDataController` / `MicroFlowController` 有独立 `@PostMapping` value）。
故跨构件归位由 32 更正为 **27**，剩余未归位 `udc*` op 由 67 更正为 **66**。
关键点：常量池里类级与方法级是**分开的 UTF8 项**，不存在拼接串 —— 这是首版验证脚本假失败的原因。

**机制再实证**：`javap` 实测 `Sandbox{Client,AppRun,SystemConfig,TenantConfig,Flexible}Controller`
五个类**全部 `extends com.seeyon.boot.starter.web.BaseComponentController`**，
其类级 mapping 字面量是 `sandbox/client`（**无 `udc`**），而 op 是 `udcSandboxClient*` ——
与 `addPathPrefix(Apps.getAppName(), BaseComponentController.class::isAssignableFrom)` 断言吻合，
前缀确由 Spring 层叠加。

## 2. 新发现：udc-web 持久化契约的**方法级双缺陷**

用**修正后的**类级+方法级扫描复算 `udc-web-5.3.517.jar`，与持久化
`docs/audit/artifacts/udc-web-5.3.517-contracts/_api_full.json` 比对：

- 站点真实路径数 **674**，持久化（旧）**657**；
- **18 个真实 op 无法由旧持久化契约推导**（site-only）；
- **1 个旧持久化 op 线上不存在**（persisted-only 幻影：`udcApplicationSaveAsTemplate`）；
- 净额 **657 + 18 - 1 = 674**（旧记「多 11 幻影」本身是旧扫描脚本漏读裸 mapping 的假差异，已归零）；
- 根因**不是**解析器不精确，而是 `tools/core/decompile/extract_udc_web_methods.py` 的实质缺陷：

### 缺陷 A：`methods` 以**方法名**为 dict key -> 重载被静默丢弃（15 处）

`parse_javap` 用 `methods: dict[str, dict]`（key = 方法名）登记方法。
javap 中**同名重载**（不同 DTO 入参、**不同 `@PostMapping` value**）落在同一 key，后写覆盖前写。

字节码实证（`MetaDataController`）：
```
public ListResponse<UdcReferMetaDataDto> mergeReferMetaData(UdcReferMetaDataSearch4PageDto);
    RuntimeVisibleAnnotations:
        RestApiOperation( value="3.3:【参照】通过实体 id/fullName ..." )
        PostMapping( value=["merge-refer"] )            <-- 丢失
public ListResponse<UdcReferMetaDataDto> mergeReferMetaData(java.util.Map<String,Object>);
    RuntimeVisibleAnnotations:
        RestApiOperation( value="3.3.2:【参照】通过实体 id/fullName ..." )
        PostMapping( value=["merge-refer-by-map"] )      <-- 保留（覆盖前者）
```
`_api_full.json` 中 `MetaDataController` 只留下 `merge-refer-by-map`。

独立计数（javap 源码级，非本解析器）：**15 个**「同名重载不同 mapping」实例，分布 9 个 Controller：
`ApplicationController`（create x3 / downloadFormAppPackage x2 / importAppSchema x2）、
`AttachmentTemplateController.delete`、`BackendComponentController.selectAppPageByConditions`、
`EntityController.selectEntityAttributeGroupList`、`MetaDataController`（4 组）、
`MicroFlowController.selectPageByCondition`、`MicroFlowUpgradeController.thirdEntity`、
`PageTemplateController.deleteById`、`PageTemplatePublishedController.deleteById`。

### 缺陷 B：注解块边界误判 -> `RestApiOperation` 值被当作 mapping 路径（2 处）

`parse_javap` 对 `RuntimeVisibleAnnotations` 块内每个 FQ 注解名取其**之后 400 字符内第一个引号串**
作为 value。当注解顺序为 `@PostMapping`（**裸注解，无 value**）在前、`@RestApiOperation` 在后时，
`@PostMapping` 之后的第一个引号串其实是 `RestApiOperation.value`（中文描述），被误登记为 `path_value`。

字节码实证（`DataTransferObjectController`）：
```
public SingleResponse<Long> create(DataTransferObjectDto);
    RuntimeVisibleAnnotations:
        org.springframework.web.bind.annotation.PostMapping          <-- 裸，无 value
        com.seeyon.boot.annotation.RestApiOperation( value="创建数据传输对象" )
```
产物里出现 `"path": "创建数据传输对象"`、`"full_path": "/udc/data-transfer-object/创建数据传输对象"` —— **中文描述当路径**。
同类：`UdcEnumCategoryController.create` -> `"创建枚举分类"`。

实测：javap 全量中**裸 mapping 14 处 / 带 value 660 处**；其中落在「裸 mapping + 其后 RestApiOperation」
模式的仅 2 处被污染，另 12 处无后续中文串故侥幸未污染（缺陷面 14，污染 2）。

### 缺陷 C：无 HTTP 注解的方法被登记为「方法名路径」

`ApplicationController.saveAsTemplate` 在 javap 中**无 `RuntimeVisibleAnnotations`**（无任何 mapping），
但 `parse_javap` 对全部方法签名先 `setdefault(path_value=name)` 兜底，且 `merge_udc_web_api.py` 对
`path_value is None` 亦回退方法名 -> 产出幻影 `/udc/application/saveAsTemplate`（`http: null`）。
实测：`_methods.json` 中 `http=None` 仅此 1 条。

### 2.4 净效应：18 个真实 op 缺失（逐条列表）

```
udcApplicationPost                                   ApplicationController           POST /udc/application
udcApplicationCreatePageAppPost                      ApplicationController           POST /udc/application/create-page-app
udcApplicationImportPost                             ApplicationController           POST /udc/application/import
udcApplicationSchemaFormDownloadBatchFileNumTimeStampGet  ApplicationController      GET  /udc/application/schema/form/download/batch/{fileNum}/{timeStamp}
udcAttachmentTemplateDeleteGuidPost                  AttachmentTemplateController    POST /udc/attachment-template/delete/{guid}
udcBackendComponentSearch                            BackendComponentController      POST /udc/backend-component/search
udcDataTransferObjectSearchListPost                  DataTransferObjectController    POST /udc/data-transfer-object/search-list
udcEntityAttributeGroupSearch                        EntityController                POST /udc/entity/attribute-group/search
udcEventListEventsPost                               EventController                 POST /udc/event/list/events
udcMetaDataMergeReferPost                            MetaDataController              POST /udc/meta-data/merge-refer
udcMetaDataSelectAggregationEntityPost               MetaDataController              POST /udc/meta-data/select-aggregation-entity
udcMetaDataSelectAppByIdPost                         MetaDataController              POST /udc/meta-data/select-app-by-id
udcMetaDataSelectCtpEnumByApp1Post                   MetaDataController              POST /udc/meta-data/select-ctp-enum-by-app1
udcMicroflowSearch                                   MicroFlowController             POST /udc/microflow/search
udcMicroFlowUpgradeThirdEntityAppGet                 MicroFlowUpgradeController      GET  /udc/micro-flow-upgrade/thirdEntity/{appId}
udcMicroFlowUpgradeUpgradeCallExtendAppServiceAppGet MicroFlowUpgradeController      GET  /udc/micro-flow-upgrade/upgrade/call-extend-app-service/{appId}
udcPageTemplateDeleteByIdPost                        PageTemplateController          POST /udc/page-template/delete-by-id
udcPageTemplatePublishedDeleteByIdPost               PageTemplatePublishedController POST /udc/page-template/published/delete-by-id
```

**连带结论（对未归位名单的影响）**：缺陷修复后，前端 346 op 中 **230** 条可由 udc-web 契约推导
（旧计 224）；剩余 `udc*` 未归位由 99 修正为 **93**（其中 27 条已跨构件归位，见第 1 节），
**余 66 条 UNVERIFIED**（第四轮后为 **62**，见第 3 节）。此外 `udcApplicationPost -> ApplicationController`
（POST `/udc/application`，裸 mapping，类级根）亦由修复后契约精确归位。

### 2.5 与上轮「21 处不一致」的关系（解释并收敛）

上轮用未校准脚本对同一 jar 复算得 19 个 Controller 计数不符（11 多 / 10 少），当时归因「解析器不可靠」。
本轮定位为**持久化契约侧的真实缺陷**（A/B/C），而非仅解析器问题：

- 「多解析」= 站点有、契约无 -> 缺陷 A/B/C 的 18 条；
- 「少解析」= 契约有、站点无 -> 上一版**扫描脚本自身**漏读裸 mapping（无 `value=` 形式）的**假差异**；
  修正扫描（识别无括号 mapping）后该类**归零**（persisted-only 由 11 降至 0，换算见 2.3）。

结论：**旧持久化契约的 657 是「漏 18、多 1」的净额，不是权威真值**。
**本轮已完成覆盖**：`tools/core/decompile/extract_udc_web_methods.py` 的 A/B/C 缺陷（+ 声明门缺陷 D）已修，
`_api_full.json` 已按修正后提取器重算为 **674**；并以**独立的 class 文件解析器**
（不经 javap 文本，直读常量池 + 方法表）逐 Controller 复核 —— **54/54 类逐条一致、0 差异**，
`class_mapping` 亦逐类一致。674 个带 mapping 端点里 `derive_ops` 产出 **673** 个不同 op，**同一 (full_path, http) 无碰撞**。

**口径收口（2026-10-15 第三轮，三个数不可混用）**：
- **674** = 方法级 mapping 端点数（`_api_full.json` 的 `api_count` 合计，含 `ParameterController` 6 条）；
- **673** = `derive_ops` 产出的 distinct op 数。差额 **1** = `ParameterController.create`：
  该类**无类级 mapping / @RestApi**（`class_mapping=None`），方法级又是**裸 `@PostMapping`**，
  故其 `full_path` 落成 `/`，`derive_ops` 里 `strip("/")` 后为空即跳过（不产出 op）；
- **666** = 真正进 op 面（exposure gate：类级 `@RestApi` ∧ 方法级 `@RestApiOperation`，见 REST-EXPOSURE-MECHANISM.md）。
旧稿「674 -> 674 个不同 op」**证伪**（漏计上述 1 条，非丢数据）。护栏：
`tests/udc/test_udc_web_contract_defects.py::test_derived_ops_count_is_673_vs_674_endpoints`

## 3. 第四轮：新增 4 条归位（27 -> 31）+ 余 62 条名单落盘

### 3.1 新增 4 条（`javap -v` 常量池，4/4 VERIFIED_STATIC_BYTECODE）

构件取自 Artifactory `libs-release-local/com/seeyon`（本机匿名可达 `10.0.0.1:80`），
落 `<HERMES_HOME>/cache/scratch/cand/`；`javap -v -p` 全文落 `scratch/v4out/*.txt`。

| op | 构件 :: Controller | 类级 mapping | 方法级 mapping | 方法名 | 动词注解 | javap 行 |
| --- | --- | --- | --- | --- | --- | --- |
| `udcExcelSearchListByConditionsPost` | `boot-starter-excel-5.3.318` :: `ExcelController` | `excel` (L1116) | `search-list-by-conditions` (L576) | `selectListByConditions` (L541) | `@PostMapping` (L575) | 4/4 |
| `udcExpressionSystemVariableListGet` | `boot-starter-formula-5.3.318` :: `ExpressionController` | `expression` (L567) | `system-variable/list` (L341) | `listSystemVariable` (L318) | `@GetMapping` (L340) | 4/4 |
| `udcFileDownloadUrlGet` | `boot-starter-file-5.3.358` :: `FileController` | `file` (L3540) | `download-url` (L1290) | `generateDownloadUrl` (L1263) | `@GetMapping` (L1289) | 4/4 |
| `udcFileDownloadUrlsPost` | `boot-starter-file-5.3.358` :: `FileController` | `file` (L3540) | `download-urls` (L1323) | `generateDownloadUrl` (L1293) | `@PostMapping` (L1322) | 4/4 |

- 三条类**均 `extends com.seeyon.boot.starter.web.BaseComponentController`**（常量池 `super_class` 直读），
  与 sandbox 族同构 -> `udc` 前缀由 `addPathPrefix` 叠加；
- 四条 `path_to_op` 规则复算精确命中（`components/udc/graphql_op_naming.path_to_op`），
  且四条**均不由** udc-web 契约产出（`_api_full.json` 674 端点全扫，0 命中）；
- 四条在 bundle 内**均为字面量 op**（`grep -roh` 命中 1-3 次），非规则反推；
- **jar sha256（前 16 位）**：excel `443a4be662ae2b73` / formula `10b8e243096bb8c4` / file `5ed92f654eacd8f0`。

> 说明（诚实标注）：本轮 `javap` 工具路径为 `<LOCAL_ROOT>/java/bin/javap.exe`
> （`PATH` 中没有 `javap`，`javapath` 目录只有 java/javac）。改用绝对路径后一次成功。

### 3.2 余 62 条仍未归位（UNVERIFIED，未以规则臆造）

**首次落盘权威名单**（此前文档只有计数、没有名单）：
`docs/audit/udc-semantics/frontend-udc-unlocated.json`（机械复算产物，非人工抄录）+ 护栏
`tests/udc/test_frontend_udc_unlocated.py`（62 条逐条参数化）。

口径（**互斥且穷尽**，可机械复算）：
```
346 前端 op = 230（可由 udc-web 674 端点的 673 op 推导）+ 116（不可推导）
116 中 udc* 前缀     = 93
93 = 31（跨构件已归位，字节码 VERIFIED）+ 62（仍 UNVERIFIED）
```
族分布（62，机械复算，见 `frontend-udc-unlocated.json#remaining_families`）：
`sandbox 11` / `message 8` / `formUpgradeDeploy 7` / `customDataType 6` / `pageComponent 6` /
`affair 5` / `ctpManager 3` / `application 2` / `entity 2` / `metaData 2` / `portal 2` /
`runtimeUpgrade 2` / `env 1` / `microflow 1` / `pageAdmin 1` / `pageInfo 1` / `pinyin 1` /
`runtime-deploy 1`（`udcRuntimeDeployPost`，无族前缀）。

**负面扫描（本轮复算口径）**：对本地 616 jar 做路径字面量扫描，余 62 条**零命中**；
新拉 12 个候选构件（`ctp-message-web/-biz`、`ctp-affair-web`、`cdp-data-web`、
`boot-starter-{excel,formula,file,enums,serialnumber,basicdata,datamigration,upgrade}`）
只解出上表 4 条 —— 说明余 62 条另有 `udc-*` 构件承接（`ctp-*` 拿到手却未见 `udcMessage*`）。

**store_registry 入参契约（新证据源，首次量化，非路径归属）**：
`frontend-extraction.json#store_registry`（291 op，含 `paramsType`/`paramsKey`/`queryFields`）
覆盖余 62 条中的 **25 条**（旧轮记 26，本轮按 62 条口径重算为 25）。
命名规约**并非**铁律：全 291 op 中标准 `<op>InputBody`(207) / `<op>InputPath`(56) 为主，
但 **13 条偏离**（跨 op 类型复用 7 + 标量类型 3 + `paramsKey` 异常 3）。
⇒ 构建请求体**必须读 registry 的 `paramsType` 原值，禁止按 op 名臆造 DTO**（已入护栏）。

## 4. 诚实边界

- 第 1 节 31 条：**VERIFIED_STATIC_BYTECODE**（四类字面量齐备，独立脚本复核 27/27 + 第四轮 javap 4/4）。
- 第 2 节：契约 **674** 为**字节码直读 + 独立 class 解析器复核（0 差异）**；
  站点侧覆盖已完成（旧 657/663 作废）。
- 第 3 节 62 条：**UNVERIFIED**。未用 op 反推路径（会造臆造证据）。名单已落盘，可机械复核。
- LIVE：`conn.py selftest --env=test2` 仅 mysql / nacos 可达；`udc_history_metadata` 全表 3 行且
  `metadata_schema=[]`，`metadata_type=2`(RestApi) 槽位为空 -> **LIVE op 注册表仍未取到**，不算通过。
## 6. 第六轮：文档名幻影的口径更正 + 形态判据证伪 + 反编译丢失面

### 6.1 口径更正 raw / corrected（余 62 -> 60）

第五轮把 bundle 抓取物的**文档名**当成了 op；本轮把它显式分离为两视图（`frontend-udc-unlocated.json#reference_kind_correction`）：

| 视图 | 前端 op | 可由 udc-web 推导 | `udc*` 未归位 | 跨构件归位 | 余量 |
| --- | --- | --- | --- | --- | --- |
| raw（抓取产物原值，**特意不改**） | 346 | 230 | 93 | — | — |
| corrected（去 2 幻影 + 补 2 真 op） | 346 | **231** | **92** | **32** | **60** |

- `udcMicroflowCopy` 是文档名，真字段 op = `udcMicroflowCopyPost`
  （`MicroFlowController.copy` -> `POST /udc/microflow/copy`，**属 udc-web**）=> matched 230 -> 231；
- `udcPinyinGet` 是文档名，真字段 op = `udcI18nResourceStrToPinyinGet`
  （`I18nResourceController.toPinYin` -> `GET /udc/i18n-resource/str-to-pinyin`，
  `boot-starter-i18n-5.3.358`，`extends BaseComponentController`）=> **非 udc-web**，跨构件归位 31 -> 32。
- 复算工具：`tools/core/correct_frontend_op_reference.py [--check]`；分类工具：`tools/core/_misc/classify_frontend_op_reference.py`。

### 6.2 ★ 形态判据已证伪（本轮自我更正）

第五轮把幻影的理由写成「文档名恒不带 HTTP 动词小写后缀，而 path->op 规则恒追加该后缀 => 按构造不可达」。
**该理由是错的**：`udcPinyinGet` 恰恰以 `Get` 结尾 —— 它作为文档名的名字本身就长得像 op。
实测（在仓内快照 `docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`）：

| 字符串 | 文档头槽（紧跟 `mutation|query`） | 字段槽（后接 `(` 实参） |
| --- | --- | --- |
| `udcMicroflowCopy` | 1 | 0 |
| `udcPinyinGet` | 1 | 0 |
| `udcMicroflowCopyPost` | 0 | 1 |
| `udcI18nResourceStrToPinyinGet` | 0 | 1 |

=> 正确判据是**位置槽**，不是字符串形态。全 346 条按位置槽扫描：**只有这 2 条**是「仅出现在文档头槽」。
护栏已把该判据写成可复算断言（`test_document_name_phantoms_cannot_return_to_remaining_list`）。

### 6.3 ★ 反编译丢失面（新发现的证据管缺口，影响「bundle 内 0 命中」类结论）

把 346 条逐条在**原始 chunk** 与 **wakaru 解包产物**（`unpacked/`，1474 js）两侧同时找。

证据源与可复现边界（诚实标注）：解包侧 = `<HERMES_HOME>/cache/scratch/udc-frontend/unpacked/`
（1474 js，与 `frontend-op-loader-contract.json` 的 `source_bundle` 同源）；原始 chunk 侧 =
`<HERMES_HOME>/cache/scratch/udc-frontend/chunks/`（**158 个 js，11MB**）——注意**两处都在 scratch**，
受 24h 闲置清理约束；仓内快照 `docs/audit/artifacts/udc-frontend-5.3.496/chunks/` **只含 store 那个 chunk**
（2.5MB），故本条结论**当前只能在 scratch 存活期内原样复现**。

- **6 条在原始 chunk 内存在、却在解包产物中消失**（解包丢失，非「前端不存在」）：
  `appCommonImageSearch` / `appCommonImageStoreCategoryGet` /
  `cipManagerManageSelectActivexCapabilityEnumGet` / `organizationOrgMemberAvatarIdsPost` /
  `udcDesignMetadataAggEntityExcludeBootGet` / `udcPageInfoDeletePost`。
  其中 **2 条属 udc 且由 udc-web 契约推导**（`udcDesignMetadataAggEntityExcludeBootGet`、
  `udcPageInfoDeletePost`）=> 反证「解包产物是完整事实源」的假设。
- **方法学后果**：任何「在 bundle/unpacked 里 0 命中」的负面结论，**必须**用原始 chunk 复检，
  否则可能把「解包丢失」误读成「前端不存在」。本轮已按此复检余量名单：**60/60 在解包产物内均有 >=1 处字面量**
  （站点直方图 1:33 / 2:23 / 3:3 / 4:1），故 60 条名单不受该缺口影响；
  `frontend-op-loader-contract.json` 的 60 条记录同理不受影响（其范围即该 60 条）。
  该缺口**仍待处理**：`frontend-extraction.json` 的 346 条里那 6 条如需重采证据，须改从原始 chunk 取。
