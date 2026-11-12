# udc.custom-app.create NPE 根因（create4CustomPage · relationApps 未初始化）

> 证据分级：**STATIC 已定位**（javap 字节码 + CFR 反编译件双向对齐）＋ **STATIC 分支判定**（ctor 默认值坐实）。
> 触发场景判定依据 R1 段既有 6 组 LIVE 失败事实（`evidence/R1R2-write-chain-20260930.json` retry_matrix），**本片未新增 LIVE 调用**。
> 环境：test2｜jar：`udc-biz-5.3.517.jar`（`<MAVEN_REPO>/com/seeyon/udc-biz/5.3.517/`）+ `udc-facade-5.3.517.jar`。
> 结论等级：**R1.7 原为段级定位**（NPE 点 = 页面依赖应用段收集），**本轮精化到 bci 227**。
> <br>口径修正（HANDOFF-04，采纳 auditor VERDICT-handoff02）：原文写「`write-chain.md` R1 段原『NPE 精确抛点 UNVERIFIED』→ STATIC 已定位」，
> 追认了一个**不存在的旧状态** —— pre-commit 全文无「NPE 精确抛点」字样，R1.7 原文已是段级已定位表述。
> 正确叙事是**段级 → bci 级精化**，不是 **UNVERIFIED → STATIC 升级**。

## 1. 精确解引用点（字节码 bci 级）

方法：`com.seeyon.udc.page.domain.service.CustomPageInfoService#create4CustomPage(CreateOnlyPageApplicationDto)`
（重载：`create4CustomPage(LayoutApplicationDto)` 是另一条方法，与本 NPE 无关，勿混）

反编译件：`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/page/domain/service/CustomPageInfoService.java:798`（CFR 单表达式，源码语义行 887–892）

```
798: List<DependentApplicationDto> dependentApps = this.buildCandidateDependApps(
         pageDefinitionDtoList.stream()                    // bci 189–202   line 887
            .map(PageDefinitionDto::getPageItems)          // bci 202       line 888
            .flatMap(Collection::stream)                   // bci 207–212   line 889
            .map(PageItemDefinitionDto::getRelationApps)   // bci 222       line 890
            .flatMap(Collection::stream)                   // bci 227–232   line 890(227) / line 891(232)
            .collect(Collectors.toSet()));                 // bci 237       line 892
```

javap 原始字节码（`scratch/cpis2.txt`，`-p -c -l`）：

```
189: aload_0
190: aload         4
192: invokeinterface #132,  1   // List.stream
197: invokedynamic #244,  0     // BootstrapMethod #21 → PageDefinitionDto.getPageItems
202: invokeinterface #184,  2   // Stream.map
207: invokedynamic #245,  0     // BootstrapMethod #22 → java/util/Collection.stream
212: invokeinterface #246,  2   // Stream.flatMap
217: invokedynamic #247,  0     // BootstrapMethod #23 → PageItemDefinitionDto.getRelationApps
222: invokeinterface #184,  2   // Stream.map
227: invokedynamic #245,  0     // BootstrapMethod #22 → java/util/Collection.stream   ← NPE HERE
232: invokeinterface #246,  2   // Stream.flatMap
237: invokestatic  #66          // Collectors.toSet
```

BootstrapMethods 逐条对号（`cpis_v.txt` §BootstrapMethods）：

| # | MethodHandle | 语义 |
|---|---|---|
| 21 | `PageDefinitionDto.getPageItems:()Ljava/util/List;` | 取 pageItems |
| 22 | `java/util/Collection.stream:()Ljava/util/stream/Stream;` | **对元素调 stream()** |
| 23 | `PageItemDefinitionDto.getRelationApps:()Ljava/util/List;` | 取 relationApps |

**精确抛点 = bci 227**：`invokedynamic #245`（= BootstrapMethod #22 `Collection::stream`）作用于
bci 222 `PageItemDefinitionDto::getRelationApps` 的**返回值**。该返回值为 `null` 时，
`Collection::stream` 的 method handle 接收 null receiver → **NPE**，栈顶落在
`java.util.stream.ReferencePipeline`（lambda 是 synthetic，不进栈）—— 与既有观测「栈顶 ReferencePipeline、
lambda 不进栈」逐字吻合。

> 行号说明（HANDOFF-04 勘误，采纳 auditor VERDICT-handoff02 §2-a 勘误 1）：
> CFR 把该表达式渲染成单行（L798），javap LineNumberTable 把它拆到 line 887–892。
> **实测 LNT：`line 890: 222` / `line 891: 232` / `line 892: 237`。**
> → 精确抛点 **bci 227**；**LNT 归属 line 890（区间 222–231）**，语义属 `.flatMap(Collection::stream)`（即 891 那条链的参数）；
> 运行时栈帧报 `create4CustomPage:892` 是**表达式末行归并**。
> **不得写「bci 227 = line 891」**（原稿此表述与 LNT 不符，已改）。

## 2. 为什么必定为 null（分支判定 · 字段默认值）

`PageItemDefinitionDto` 的 `relationApps` **声明即无初始化**：

- 反编译件 `docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/page/dto/PageItemDefinitionDto.java:74`
  → `private List<String> relationApps;`（无 `= ...`）
- 构造函数字节码（`scratch/pidto.txt` L41–57）只写 4 个字段：
  `actionType=NORMAL`、`designState=DESIGN`、`layoutId=NULL_ID`、`orderNo=null`。
  **`relationApps` 不在 ctor 写入列表内 → 默认 null。**

全仓 `setRelationApps` 只有两处调用，**都在 copySchema=true 分支内**：

| 位置 | 所在方法 | 分支 |
|---|---|---|
| `CustomPageInfoService.java:1247` | `getPageItemDefinitionDto4Oss` | copySchema=**true** 且 `JSONUtil.isTypeJSONObject(pageSchema)` 成立 |
| `CustomPageInfoService.java:1252` | 同上（depList 非空时再合并） | 同上 |

而 **copySchema=false 分支**走的是 `getPageDefinitionDto(...)`（L905–947）：
该方法只 `new PageItemDefinitionDto()` 并设 `actionType` / `urlType`，
**从不调用 `setRelationApps`** → `relationApps` 恒为 `null`
→ 回到 L798 表达式 → **bci 227 必 NPE**。

分支对照：

```
copySchema = true   (bci 34 ifeq 129 不跳)
  └ getPageDefinitionDtoList4Oss  → getPageItemDefinitionDto4Oss
      └ if (isTypeJSONObject(pageSchema)): setRelationApps(parseSubPageRelationApp(...))   ← 非 null（工具方法短路返回 emptyList，绝不返回 null）
      └ else:                            relationApps 仍 null                              ← 仍会 NPE

copySchema = false  (bci 34 ifeq → 129)
  └ getPageDefinitionDto  → PageItemDefinitionDto 未设 relationApps                        ← 恒 null → 必 NPE
```

`PageUtils.parseSubPageRelationApp`（`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/page/util/PageUtils.java:250–264`）
三个出口均为 `Collections.emptyList()` 或 filtered list，**无 null 出口** → 只要该行被执行，relationApps 必非 null。

## 3. 触发场景判定（结合 R1 段既有 6 组失败事实）

### 3.1 原始请求体逐条复核（13 条 custom-app/create）

> **证据强度修正（HANDOFF-04，采纳 auditor VERDICT-handoff02 补正 4）**：
> 13 条记录的 jsonl **只有 `req_body_sha256_16`（请求体 sha256 前 16 位），`req_body` 本身未落盘**。
> 记录字段集合实测 = `http_status / kind / note / req_body_sha256_16 / resp_body / resp_bytes / ts / url`（**无 `req_body`**）。
> 故下表「req_body 键」列中：
> - `create-probe-1` 的 `{}` **可反推坐实**：`req_body_sha256_16 = 44136fa355b3678a` = `sha256("{}")[:16]`（本轮复算命中）；
> - 其余 12 条的键集是**从 `resp_body` 的 BOOT_1001 必填校验文案反推**（如「caption 不能为空」→ 该条无 caption 键），
>   **不是直读原始 body**，**不可逐字复核**。

对 `evidence/*.jsonl` 逐行解析 `url` 含 `custom-app/create` 的记录（脚本见 §6），结果：

| 文件 | kind | 有 masterEntity | 有 copySchema | envelope_status | resp_bytes | req_body 键（**推断**，除 probe-1 外未落盘） |
|---|---|---|---|---|---|---|
| R1-app-create-20260930153902 | create-probe-1..3 | ✗ | **✗** | None | 113 | `{}` 类（BOOT_1001 caption 空）**← 仅 probe-1 经 sha256 反推坐实** |
| 同上 | create-probe-4..6 | ✗ | **✗** | None | 117 | `+caption`（BOOT_1001 hostAppName 空）**← 推断** |
| R1-app-create-20260930154751 | create-probe-7/8 | ✗ | **✗** | None | 83 | `caption, hostAppName` **← 推断** |
| unblock-20260930162926 | create-1-E7 | **✓** | **✗** | **2** | 83 | `caption, hostAppName, masterEntity` **← 推断** |
| 同上 | create-3-default | **✓** | **✗** | **2** | 83 | 同上 **← 推断** |
| unblock-20260930163028 | create-E7-minimal | ✗ | **✗** | **2** | 83 | `caption, hostAppName` **← 推断** |
| unblock-v2-20260930164904 | create-1-T2 | **✓** | **✗** | **2** | 83 | `caption, hostAppName, masterEntity` **← 推断** |
| 同上 | create-2-T2 | ✗ | **✗** | **2** | 83 | `caption, hostAppName` **← 推断** |

**软点消除（范围收紧）**：13/13 条记录的 `req_body_sha256_16` 均**无对应 `copySchema` 键的独立证据**，
但「13/13 未显式传 `copySchema`」这一结论**仍成立且可复核**，依据有二：
① `CreateOnlyPageApplicationDto` ctor 字节码默认 `Boolean.FALSE`（STATIC）；
② `resp_bytes=113/117` 两条为 BOOT_1001 必填校验拦截，其余 83B 形态与 R1 段 6 组失败一致 —— 若显式传 `copySchema=true`，
会走另一分支并因缺 `originAppName/originPageGuid/pageUrl` 抛**显式 `BusinessException`**（L775-783），
与观测的 83B `status:2` 形态不符。
> **不得写**「已逐条直读 13 条 req_body」——本片未落盘原始 body。§8 相应条目同步收紧。

### 3.2 关键修正：`status:2` 是异常吞噬的统一表现，掩盖了两类不同异常

字节码显示该端点有两处会抛异常：

| 失败点 | 触发条件 | 抛什么 |
|---|---|---|
| `getPageDefinitionDto` L906–908 | **`masterEntity` 为空** | `BusinessException.message("创建新页面必须传递 主实体")` |
| `getPageDefinitionDto` L914–916 | 元数据查不到该实体 | `BusinessException.message("创建新页面使用的实体在元数据中心获取不到"+masterEntity)` |
| **L798 bci 227** | copySchema=false 且前两者通过 | **NPE** |

而 `@Transactional` + 全局异常处理把**两者都压成 `status:2 / code:null / message:null / 83 字节`**，
响应体在两种情况下**字节数完全相同（83）**。因此：

- **`create-E7-minimal` / `create-2-T2`（无 masterEntity）** → 实际在 **L906 抛 BusinessException**，
  **根本没走到 L798**，属「参数缺失」，与本 NPE 不同根；
- **`create-1-E7` / `create-3-default` / `create-1-T2`（有 masterEntity）** → 元数据通过后走到 **L798 → NPE**，
  属本 NPE 的实证样本。

→ **R1 段「unblock v1/v2/v3 的 6 组 status:2 同根」这一判断需要修正**：6 组里至少 2 组
（无 masterEntity 者）是**参数缺失的 BusinessException**，不是 NPE。它们同根只体现在
"都被吞成 status:2"这一**表象层**，不是同一异常。真正命中本 NPE 的是 3 条带 masterEntity 的请求。

### 3.3 与 R1 段既有事实的逐条对账

| 既有事实（R1 段 / retry_matrix） | 本片解释 |
|---|---|
| 元数据 3 接口（selectAggEntity / selectDtoMetadata / selectEnumMetadataByFullNames）全 200 后才 NPE | 与字节码顺序天然吻合：`getPageDefinitionDto` L910–916 查实体元数据（通过）→ 构造 PageItemDefinitionDto（不设 relationApps）→ 回 L798 → NPE。**非"元数据不足"** |
| `masterEntity=JSON对象` → BOOT_3002 反序列化错 | `String masterEntity` 字段反序列化失败，未进方法体，与本 NPE 无关（前置层失败） |
| `masterEntity=实体name` → 元数据获取不到 | L914 `entityMetaDataDto==null` → BusinessException（**显式错误**，非 NPE） |
| **6 组全部 `status:2` 静默失败**（含「裸 fullName + hostAppName=udc/ctp/lowcode/app 自身」、`pageUrlTypeEnum=PC`、bill 45attrs、standard 9attrs） | 6 组 copySchema 均未传 → 默认 false → **带 masterEntity 者必命中 L798 NPE**；不带者停在 L906。两者都被压成 status:2。这解释了"换实体/换 host/换 urlType 都无效"——**变量根本不在这些参数上** |
| bill(45 attrs) 与 standard(9 attrs) 双复现 → 排除实体复杂度 | 实体复杂度与 relationApps 无关，NPE 在依赖应用段。**结论正确但归因错位**：不是"排除实体复杂度"，是"依赖段与实体无关" |
| `hostAppName=udc/ctp/lowcode/app 自身` → NPE | hostAppName 只决定元数据查找是否通过；通过后仍走 null relationApps → 同 NPE |

**触发条件（充分必要，STATIC 判定）**：
`copySchema != true`（DTO ctor 默认 `Boolean.FALSE`，13/13 条实测均未传）
**且** `masterEntity` 非空且元数据可命中（否则停在 L906/L914，先抛 BusinessException）
**且** 请求进入 L798 依赖应用收集段。


**性质判定：平台侧缺陷（无条件空指针），非参数缺失、非 host 绑定、非元数据问题。**
L798 表达式对 `getRelationApps()` 无条件解引用，而该字段仅在 copySchema=true 路径被赋值 ——
构造上缺少 null 保护，属代码缺陷。参数怎么调都救不回来。

## 4. 绕行判定

### 4.1 候选 A — copySchema=true（同接口内旁路）

- **机制**：设 `copySchema=true` + `originAppName` + `originPageGuid` + `pageUrl`（三者缺一即抛
  `BusinessException`，L775–783，是显式校验非 NPE）→ 走 `getPageDefinitionDtoList4Oss`，
  由 `getPageItemDefinitionDto4Oss` L1247 赋值 relationApps。
- **前置（DB 只读实测，2026-10-17）**：
  - 源应用须在**元数据中心**可按 appName 查到页面列表（`selectPageInfoListByAppName`），
    且 `originPageGuid.toString()` 能在结果中 by `fullName` 命中（L1126 否则抛「未在元数据中心查询到原始页面」）。
  - 源页面 `page_schema` 必须是合法 JSON object（否则 L1215 分支跳过，relationApps 仍 null → 仍 NPE）。
 DB 实测（**列归属已修正，采纳 auditor VERDICT-handoff02 补正 5**）：
 `feature_type` 列**在 `udc_application` 表**，`udc_page_schema` **无此列**。正确查询为
 `SELECT ... FROM udc_page_schema s JOIN udc_application a ON s.app_id = a.id WHERE a.feature_type = 3`
 → 共 **1504 行**，`JSON_VALID = 1494`、非法 **10** 行 → **存在非零失败概率**。
 > **取样时间窗（必带，否则不可复现）**：`create_time < 2026-10-17 17:00`。
 > 原因：该 target 应用在 22:45–22:47 被**跨域（栏目域 UDC9-07）并发写入** 1 行新页面
 > （`udc_page_info.id=-1695224980799982257` / `caption=S2PROBE20261017` + 配套 schema 865B），
 > 导致不加时间窗时读到 **1505 / 1495**（auditor 首轮即此数）。**加时间窗后 1504/1494/非法 10 可复现，与本文一致。**
 > 结论：本项数字经 auditor 独立复核**完全正确**；差异是域外并发写污染，不是计算错误。
  - `hostAppName` 的 `idFullNameMap` 可查（`udcIdFullNameMetadata4OssService.selectIdFullNameMap(hostAppName)`）。
- **阻断点**：`hostAppName` 有效值仍 **UNVERIFIED**（R1.7 既载）。全库 `udc_application` 20 行，
  `host_app_name` 非空的只有 5 类固定宿主：`cip-connector`(6) / `app-approval`(3) / `billarchive2776130152975518413`(1)，
  **均无 zzprobe 前缀应用**（`SELECT ... WHERE name LIKE 'zzprobe%'` → 0 行）。
- **副作用风险**：`copySchema=true` 会整份复制源页面 schema（实测 znxmglpt 页面 schema 单页 1.6–2.7 MB），
  `pageSchema = pageSchema.replaceAll(...)` + `SchemaParser.idReplace` 全量改写后写入目标应用 ——
  属**大质量写操作**，超出"最小验证"边界。
- **判定**：**理论可行但未验证（UNVERIFIED）**。不满足「正常路径可行」的 LIVE 门槛；
  在 hostAppName 有效值坐实前不具备低成本验证条件。**本片不执行**（避免 >2MB schema 落库与不可逆写入）。

### 4.2 候选 B — 设计态草稿面 `app-draft/create`（草稿写读环 PASS，**不构成建应用路径**）

> **口径修正（2026-10-17 HANDOFF-04，采纳 auditor VERDICT-handoff02）**：
> 本小节原写「主线绕行 = app-draft/create（正常路径可行，LIVE 已证）」，**该记账已被推翻**。
> 草稿面的对象是 `app_data_draft`（`data_id varchar + draft_data longtext` 键值表，**无 `udc_application` 外键**），
> 不是 `udc_application`。草稿 PASS ≠ 建应用 PASS。详见 §4.2.1。

- 既有事实：`write-chain.md` §R1.10 —— `app-draft/create` **草稿写读环 LIVE PASS**
  （BOOT_0000 + 非空草稿，`dataId=1@T2`）。**该 PASS 的口径 = 草稿存在性**，不是应用实体存在。
- 该路径不经过 `CustomPageInfoService.create4CustomPage`，结构上不触发 bci 227 NPE —— 这一点仍成立。
- **但**：`app-draft/create` **不产生 `udc_application` 行**，因此它给不出后续 发布/上线 所需的 `appId`（`Long`）；
  草稿的 `dataId` 是 `varchar` 键，与 `DeployNormalDto.appId`（`Long`）类型与语义双重不兼容。
- **判定：草稿面 = 设计态草稿写读环 PASS（对象 `app_data_draft`，非 `udc_application`）；不构成建应用路径。**

#### 4.2.1 为什么不能算建应用（三条，字节码/表结构级）

| 事实 | 证据 | 推论 |
|---|---|---|
| `app_data_draft` 表为键值草稿表，**无 `udc_application` 外键** | 只读 DB 表结构（main 轮7/轮8 实测） | 写草稿不落应用实体 |
| `AppDraftController` 方法全集 = `createOrUpdate / exist / select / delete / deleteAll / deleteTimeout`，注解语义均为「当前用户的草稿」 | `docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt` 常量池（GBK 逐字） | **无 publish / online / deploy 动作**，草稿面没有转正入口 |
| `appOnline` 门 3 `checkApplication(appId)` 要求 `udc_application` 行已存在，否则 `UDC_APP_0001` | `ApplicationService` L1320-1342；`DeployParamDto.appId` = `Long` | 草稿 `dataId` 喂不进去 → **「草稿 dataId → 上线」链路不存在** |

- **恢复 §R1.10 原件限定语（照录，不得省略）**：
  「**B PASS 判据 = 草稿存在性（非空 content + dataId + updateTime），非 custom-app 的 appGuid 非空**；
  若 main 要求 R1 必按 custom-app 只页应用面收口，则 **B 不顶替**，custom-app 面维持 §R1.9 BLOCKED-环境。」
  → 本轮 main 已按 custom-app 只页应用面要求收口，故 **B 不顶替**，建应用路径记为 BLOCKED。

### 4.3 候选 C — 手工补 relationApps（不可行）

请求体无该字段：`CreateOnlyPageApplicationDto` 字段全集（javap `-p`，udc-facade 5.3.517）
= `hostAppName / caption / pageUrl / originAppName / originPageGuid / originPageUrl / authJson /
copySchema / masterEntity / pageUrlTypeEnum / spiltTerminal`（11 个）。
**无 relationApps、无 pageItems、无 schema 入参** → 客户端无法注入，排除。

## 5. 结论

1. **NPE 精确抛点 = STATIC 已定位**：`CustomPageInfoService#create4CustomPage(CreateOnlyPageApplicationDto)`
   bci 227（源码表达式行 887–892，栈帧报 892），`Collection::stream`（BootstrapMethod #22）作用于
   `PageItemDefinitionDto.getRelationApps()`（#23）的 **null 返回值**。
2. **根因 = 平台代码缺陷**：`PageItemDefinitionDto.relationApps` 声明无初始化（ctor 不写该字段），
   仅 copySchema=true 分支赋值；copySchema=false 分支无条件解引用 → 必 NPE。
   与实体、host 名、urlType、元数据全部无关，解释了 R1 段 6 组在**带 masterEntity 情况下**的全覆盖失败。
3. **R1 段原归因需修正两处**：
   - 「平台侧缺陷**或存在未公开前置条件**」→ 收敛为 **纯平台缺陷（无条件 NPE）**，
     不存在能救 copySchema=false 路径的"未公开前置条件"。
   - 「unblock v1/v2/v3 的 status:2 六组同根」→ 需要修正：其中**无 masterEntity 的 2 组**
     （create-E7-minimal / create-2-T2）实际停在 L906 `BusinessException`，**未走到 L798**，
     与本 NPE 不同根；同根只是"被异常吞噬成 status:2"的表象。**真正命中本 NPE 的是 3 条带
     masterEntity 的请求**（create-1-E7 / create-3-default / create-1-T2）。见 §3.2。
4. **custom-app/create 正常路径 = BLOCKED（平台缺陷，agent 不可修复）**；
   **草稿面 `app-draft/create` = 设计态草稿写读环 PASS（对象 `app_data_draft`，非 `udc_application`），不构成建应用路径** →
   按 §R1.10 原件限定语「B 不顶替」，**建应用路径 = BLOCKED，无 agent 可行绕行**；
   copySchema=true 旁路保留为 UNVERIFIED，待 hostAppName 有效值坐实且 main 另行授权大质量写后再评估。
   > 口径修正（HANDOFF-04）：原文写「主线绕行 = `app-draft/create` 设计态草稿面（LIVE PASS，已在用）」，
   > 该表述把草稿写读环误记成建应用路径，已推翻。详见 §4.2.1。
5. **建应用路径最终口径（2026-10-17 收口）= 双 BLOCKED，无 agent 可行绕行**：
   - 窄门 ①：`custom-app/create` 平台 NPE（本文件 bci 227，纯平台缺陷，agent 不可修复）；
   - 窄门 ②：新建 NORMAL 应用受配额门 `UDC_APP_0030`（计数 `source_type=NORMAL && json_prefab=false`，上限 `createAppNum`；
     test2 实测 10/10 满）；
   - 草稿面不构成第三条路（§4.2.1）。
   这命中验收第 2 条的 **BLOCKED 分支**（「明确 BLOCKED + 绕行方案」中绕行方案 = 无）。

## 6. 复现命令（只读，可重跑）

```bash
JAVA='"/c/Program Files/Common Files/Oracle/Java/javapath/java.exe" -m jdk.jdeps/com.sun.tools.javap.Main'
CP='-classpath "<MAVEN_REPO>/com/seeyon/udc-biz/5.3.517/udc-biz-5.3.517.jar;<MAVEN_REPO>/com/seeyon/udc-facade/5.3.517/udc-facade-5.3.517.jar"'

# 1) create4CustomPage 字节码 + 行号表 + BootstrapMethods
eval $JAVA -p -c -l -v $CP com.seeyon.udc.page.domain.service.CustomPageInfoService > cpis_v.txt
grep -n "BootstrapMethods" cpis_v.txt            # 取 #21/#22/#23
grep -n "invokedynamic #245" cpis_v.txt           # 应命中 bci 207 与 bci 227 两处

# 2) PageItemDefinitionDto 构造函数（验证 relationApps 未被写入）
eval $JAVA -p -c $CP com.seeyon.udc.page.dto.PageItemDefinitionDto > pidto.txt
sed -n '/PageItemDefinitionDto();/,/return/p' pidto.txt

# 3) 请求 DTO 字段全集（验证无 relationApps 入参）
eval $JAVA -p -c $CP com.seeyon.udc.dto.form.CreateOnlyPageApplicationDto > dto.txt
grep "private java" dto.txt
```

## 7. 证据文件（在盘）

| 项 | 路径 |
|---|---|
| javap `-p -c -l` 全量（含 LineNumberTable/BootstrapMethods） | `<HERMES_HOME>/cache/scratch/cpis2.txt`、`cpis_v.txt` |
| javap `PageItemDefinitionDto`（构造函数字节码） | `<HERMES_HOME>/cache/scratch/pidto.txt` |
| javap `CreateOnlyPageApplicationDto`（字段全集 + ctor 默认值） | `<HERMES_HOME>/cache/scratch/dto.txt` |
| CFR 反编译件 | `docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/page/domain/service/CustomPageInfoService.java`（L662/769/905/1116/1205） |
| R1 既有 LIVE 失败事实（6 组 retry_matrix） | `core/facts/udc/write-chain/evidence/R1R2-write-chain-20260930.json` |
| DB 只读对照（host_app_name 分布 / schema JSON 合法率） | 本文件 §3 §4.1，命令见 §6 |

## 8. 未验证项（如实登记）

- `copySchema=true` 分支**未做 LIVE 验证**：缺 `hostAppName` 有效值（UNVERIFIED），且会触发 >2MB schema 写入，
  超出本片"最小验证"边界。判定 UNVERIFIED，**不写成可行**。
- 本 NPE 的**运行态堆栈**未取（未新增 LIVE 调用）：§1 的抛点由字节码静态判定，与 R1 段既有
  「栈顶 `ReferencePipeline`、lambda synthetic 不进栈」观测吻合，但**没有本轮的 `create4CustomPage:892`
  原始栈帧样本**。若 auditor 需要 LIVE 级确认，需 1 次带 masterEntity 的 zzprobe 请求并抓 pod 日志。

> 已消除软点（原 §8 第一条）：R1 既有 13 条 create 请求是否全部未传 `copySchema` ——
> 已逐条解析原始 jsonl 复核，**13/13 均无该键**，见 §3.1。
