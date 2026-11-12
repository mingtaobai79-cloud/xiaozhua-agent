# udc.page.create（LIST 面）｜列表页能力事实格

> 基线仓库根：`<XIAOZHUA_AGENT_ROOT>`（本件只写 `core/facts/udc/page/list-page.md`，新建 `core/facts/udc/page/`）。
> 九段固定序（1 Capability / 2 Version / 3 Input / 4 Required / 5 Execution / 6 Side Effects /
> 7 Known Constraints / 8 Evidence / 9 Verified）。证据等级三档：`OBSERVED_LIVE` / `VERIFIED_STATIC_BYTECODE` / `UNVERIFIED`。
> 每段引在盘证据（路径 + 行号/字段名），无证据项如实标 `UNVERIFIED`；**凭据 0 入件**（只引路径/对象 id/`expires_epoch`）。
> 本轮范围：**只做列表页（LIST 面）一格**；详情页（DETAIL）与菜单绑定留 S2/S3，不扩散。

---

## 1. Capability

**建列表页（LIST 面）= 设计态写能力 `udc.page.create` 的 LIST 分支 + 其运行态回读读面族。**

- **主能力**：`udc.page.create` —— 在设计态为某应用创建「一组页面（基础信息）」，一次提交含 LIST 与 DETAIL 两个页面项，
  平台为每组返回 `relationGroupId`。列表页 = 该数组的 `pageType="LIST"` 那一项。
  依据：`components/platform_operations/deployment.py` L157-174（`DeploymentStep(op="udc.page.create", method="POST",
  path="/service/udc/page-info/base-info/create", body=[LIST 项, DETAIL 项])`）；`docs/audit/udc-design-time-deploy-write-contracts.md`
  L15（LIVE 建页 ×2 全 `BOOT_0000`）、§二 L29-31（`PageInfoController` 类级 `/udc/page-info` + 方法级 `/base-info/create`，
  RestApiOperation 原文「创建新页面(只包含基础信息，会同时新建多个页面类型为一组)」）。
- **类型**：CONFIG 型 —— agent 出**只读方案 data**（`deploy_plan.steps`），宿主执行真实写端点；agent 侧写门恒拒
  （见 §5）。依据：`deployment.py` L175-180（`udc.deploy.normal` step 与宿主执行边界）、`docs/audit/udc-design-time-deploy-write-contracts.md` L5-7、L69-71。
- **列表页类型值**：`PageTypeEnum` 12 值中 `LIST`（LIVE javap 实测值域，audit §二 L39）；本格只用 `LIST`。
- **配套只读读面族（同域事实，均 `write=False`）**：
  | 读面 | operation_id | metadata_layer | 依据 |
  |---|---|---|---|
  | 运行态元数据读面（枚举） | `udc.page_info.select_host_and_only_page`（C2b） | 运行态元数据层 FACT | `registry.py` L58；`docs/operation-contracts/udc/page/page-readonly-contracts.md` L31 |
  | 运行态元数据读面（存在性） | `udc.page_info.check_exists`（C2a） | 运行态元数据层 FACT | `registry.py` L57；同上 L30 |
  | 页面运行日志读面 | `udc.page_log.search`（C1a） | 运行态日志层（非 metadata 层）FACT | `registry.py` L55；同上 L28 |
  | 页面运行日志读面（元数据差异面） | `udc.page_log.search_non_metadata`（C1b） | 运行态日志层 FACT | `registry.py` L56；同上 L29 |
  | 列表数据查询面 | `udc.runtime-data.read`（`core/facts/udc/runtime-data-read.md`） | 运行态数据层（`data/query`） | `core/facts/udc/runtime-data-read.md` L1-17 |

## 2. Version

- **Canonical = `udc-starter-runtime` 5.3.517**：`registry.py` L53/L54 evidence dict 逐字 `"artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517"` +
  `"javap": "docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt"`（L53 对应 `UdcRtPageLogController.javap.txt`）。
- **版本族隔离（规则④）**：本件全部契约证据（bytecode SHA-256 / base / 方法 / DTO / metadata_layer 判定）绑定 5.3 族 **5.3.517 单一构件**；
  test2 部署态镜像 **5.3.496** 为独立证据单元，禁混写（`page-readonly-contracts.md` L22、L39）。
- **版本单元注记（本格引用时不得升级）**：C2b 请求体 `UdcPagesMetaDataSearchDto` 的**继承链字段**来自 `boot-starter-extmetadata` **5.3.318** javap
  （本地无 5.3.517 extmetadata 构件），该注记原文未写入 C2b evidence（`docs/audit/artifacts/udc-page-5.3.517/LIVE-readback.md` L33）；
  故 5.3.517 下该 DTO 完整字段清单 = **UNVERIFIED**（见 §9）。

## 3. Input

`deploy_plan(application_id, entity_name, attributes, caption)` 产出的 **step3 声明**中 LIST 项（`deployment.py` L157-164，`body[]` 第一项）：

```
op      = udc.page.create
method  = POST
path    = /service/udc/page-info/base-info/create
body[0] = {
    "appId":           <app_id_num>,          # application_id 转数字（_to_app_id）
    "caption":         "{caption}列表",
    "pageType":        "LIST",                # PageTypeEnum 12 值之一
    "masterEntityIds": "<entity_id>",         # 实体数字 id
    "pageUrl":         "{entity_name.lower()}list",
    "curTerminalType": "PC",
    "pageItems": [ { "pageUrl": "{entity_name.lower()}list", "urlType": "PC",
                     "menuName": "{caption}列表", "actionType": "NORMAL", "orderNo": 1 } ]
}
```

- **DTO 关键字段**：`PageDefinitionDto` = `appId(数字)/caption/pageType/masterEntityIds/pageUrl/curTerminalType/pageItems[]`
  （audit §二 L40，LIVE javap 实测字段清单）。
- **读面入参形态**（回读同一 LIST 页）：
  - C2b：`@RequestBody UdcPagesMetaDataSearchDto`（LIVE 实测 body `{"appName":"app9000000000000000001"}`）；
    参数名 `request` 经 javap LocalVariableTable 逐字实取（`registry.py` L58；`docs/operation-contracts/udc/page/registry-entries.md` L57）。
  - C2a：`@RequestBody List<UdcRtPageExistsDto> pageExistsDtoList`，三元组 `{appName, pageUrl, terminalType}`
    （LIVE body `[{"appName":"…","pageUrl":"hj","terminalType":"PC"}]`，样本取自 C2b 非空枚举）；
    参数名 `pageExistsDtoList` = javap LocalVariableTable 实取（`registry.py` L57）。
  - C1a/C1b：`@RequestBody PageDtoRequest<UdcRtPageLogSearchDto> query`，LIVE 包装 = `{"pageInfo":{"pageNo":1,"pageSize":20}}`
    （`docs/audit/artifacts/udc-page-5.3.517/LIVE-readback-runtime.json` L65-71 / L83-89；非 `pageInfo` 包装的入参形态 UNVERIFIED）。
- **列表数据查询面入参**：`POST {gateway}/{PF}/udc-runtime/data/query`，body SingleRequest 包装 `{"data":{...}}`，
  三参数字典 = `appName 应用编码; dataId 数据id; entityFullName 实体FullName`（LIVE BOOT_3000 原文，
  `core/facts/udc/runtime-data-read.md` L13-16）。

## 4. Required（必填链、值域与错误码）

| # | 项 | 要求 | 缺/错后果（LIVE 错误码原文） | 依据 |
|---|---|---|---|---|
| 1 | `pageType` | 必填 | `BOOT_1001 pageType must not be null` | audit §二 L33 |
| 2 | `pageUrl` | 必填（**顶层与 `pageItems[]` 皆需**） | `BOOT_1001 pageUrl must not be null` | audit §二 L34 |
| 3 | `curTerminalType` | 必填 | `BOOT_1000 页面终端信息为空，请选择` | audit §二 L35 |
| 4 | `actionType` | ∈ `{NORMAL, INSERT, UPDATE, DELETE}`（`com.seeyon.boot.enums.ActionType` javap） | `VIEW` 不存在 → `BOOT_3002` | audit §二 L36 |
| 5 | `masterEntityIds` | = 实体数字 id | — | audit §二 L37 |
| 6 | `urlType` | ∈ `{PC, MOBILE}`（`TerminalTypeEnum` 同源） | — | audit §二 L37 |

- 与方案声明一致：`deployment.py` L172-173 `note` 逐字列必填链
  「`appId/pageType/masterEntityIds/pageUrl/curTerminalType/pageItems[].{pageUrl,urlType,menuName,actionType=NORMAL}`；
  缺 `pageUrl` 或 `curTerminalType` → `BOOT_1001`/`BOOT_1000`「页面终端信息为空」；`actionType` 枚举 `{NORMAL,INSERT,UPDATE,DELETE}`」。
- **枚举快照**：`PageTypeEnum` 12 值 = `PORTAL/WELCOME/REPORT_FORM/DETAIL/LIST/APPROVAL/PORTLET/SEARCH_LIST/EDIT_LIST/LIST_DETAIL/ASSIST_INFO/OTHER`
  （audit §二 L39；javap 实测值域）。**值域 = 活体快照，非永久常量**（audit §七 L83）。
- **读面必填**：C2b `appName`（LIVE 唯一入参键）；C2a 三元组 `appName+pageUrl+terminalType`（`registry.py` L57）；
  C1a/C1b `pageInfo` 包装键（LIVE 实证，缺包装形态 UNVERIFIED）。
- 列表数据查询面必填：`appName` + `entityFullName` + `dataId` 三键语义并列（逐键必填性未单键实测 → 标注），
  `runtime-data-read.md` L20。

## 5. Execution

- **agent 侧不出写**：写门 `components/platform_operations/layer.py:22`
  `if contract.write or contract.method != "GET" or not contract.effective:` → `OperationStatus.DENIED` + `ErrorKind.POLICY_DENIED`
  （本刀实测原文；与 audit §一 L5-7、L69-71 口径一致）。故建页只能由**宿主按 `steps` data 授权执行**。
- **本域 4 条读契约在 agent 执行链上同样不放行**：均为 `@PostMapping` 注解字面动词（javap `UdcRtPageInfoController.javap.txt`
  L136-137 `@PostMapping value=["check-page-exists"]`、L168-169 `value=["select-host-and-only-page-pages"]`；
  `UdcRtPageLogController.javap.txt` 同目录在盘），`registry.py` L55-58 逐条 `write=False`、method=`POST` →
  `effective()` 三条件（GET + VERIFIED_STATIC_BYTECODE + write=False）不满足 → `PlatformOperationLayer` 判 `DENIED/POLICY_DENIED`
  （`page-readonly-contracts.md` L6「HTTP method 一律取注解字面动词，不按读语义改写」；`registry.py` L59 `note` 同边界）。
  读面 LIVE 回读由宿主/系统操作者凭据执行（§8 证据 4）。
- **宿主执行姿势（建页）**：`POST /service/udc/page-info/base-info/create` → LIVE `BOOT_0000`
  （audit L15；网关 service 前缀由调用方拼，契约原路径禁拼前缀，见 §7）。
- **宿主回读 verify**：`GET /service/udc/page-info/select-by-appId/{appId}` 回读新页 `caption + relationGroupId`
  （`deployment.py` L171）；LIVE 200、验收单 2 命中（`id=-6629355753974142446 / -6832321505567116615` 即 relationGroupId；
  按 `id` 回读 404 = 该读面仅认 `relationGroupId`，UNVERIFIED）（audit L16）。
- **运行态回读 URL 姿势（LIVE 实证）**：`base=https://lowcode-test2.example.com` + 网关前缀
  `/service/app9000000000000000001` + 控制器原路径逐字（`LIVE-readback.md` L5；`LIVE-readback-runtime.json` L7-9）。
- **列表数据查询面执行**：`POST {gateway}/{PF}/udc-runtime/data/query`，LIVE `BOOT_0000` 级响应路径打开；
  无 `udc-runtime/` 直挂 service 前缀被 nginx 403/404（`runtime-data-read.md` L21-22）。
  **本端点语义 = 按 `dataId` 查单条**，`pageNo/pageSize` 被忽略（同件 L17）→ 列表分页读面 UNVERIFIED（§9）。

## 6. Side Effects

- **建页 = 设计态写**，不直接落物理表、不改运行态元数据：`deployment.py` L174 `note` 逐字
  「C2b 运行态元数据面只回读**已发布页**，新建设计稿在该面不可见是预期行为」。
- **页面随 RELEASE 构建发布**：`deployment.py` L180 `note`「放在建页之后：页面设计稿随构建发布」；
  audit L24-25 关键认知修正「前端页面**不是构建送的**：页面是独立设计态动作（`PageInfoController.createBaseInfo`），
  需在建实体后显式创建，再随构建发布」。
- **物理表落应用自身库**（`{app}_test2` / `{app}_uat`），**非 `udc_test2`**（audit L18 实测、§七 L84 铁律 3）。
  注：该 LIVE 实证的物理表为验收单 **bill 实体**表 `yanshouda_m5654091886000795633`；
  **列表页自身的物理表/列映射 UNVERIFIED**（§9）。
- **读面零副作用**：4 端点 `scope=read-only`、零写操作、无 publish/deploy（`LIVE-readback.md` L4、L39 红线自证）。
- 建页 LIVE 关联链（同批实证）：建实体 `7670732978062038177`、建属性 ×4、建页 ×2、RELEASE 构建 `deploy_type=2 state=1`
  （audit L13-18）。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| 网关 service 前缀 **UNVERIFIED** | 契约原路径**禁拼前缀**当可用 URL；仅宿主拼 `{gateway_base}{prefix}` | `registry.py` L55-58 各条 `verification_rules` 末项；audit §三 L45-48 |
| 4 读契约 `method=POST` | `effective()=False` → 执行层 `DENIED/POLICY_DENIED`（非 FAIL） | `page-readonly-contracts.md` L6；`registry.py` L59 `note`；`layer.py:22` |
| metadata_layer **五层不可顶替**（设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis 缓存） | 不得以「Boolean 结果 / HTTP 200 / 相邻版本 / 其他层」顶替 | `page-readonly-contracts.md` L21、L37（判定表 L26-35） |
| 版本族隔离 | test2 部署态 5.3.496 / 旧版 5.3.345-358 **禁与 5.3.517 混写** | `page-readonly-contracts.md` L39 |
| 值域/枚举/数字编码 = 活体快照 | 非永久常量，不得硬编码进调用方 | audit §四 L50-55、§七 L83 |
| `pageUrl` 是 UDC 生成的**运行态路由字面** | 离线不可证 → 标 UNVERIFIED，不臆造 | `components/construction/page_definition.py` L69-71 |
| 双 operation_id 同物理端点 | `registry.py` L57/L58（page 域）与 L62/L60（meta-data 域）指向同一对端点 → 归域/去重留裁定，本件只记事实 | `docs/operation-contracts/udc/page/registry-entries.md` L169-171（D 项） |
| 凭据纪律 | 只引路径 + `expires_epoch`；token 明文 0 入件 | `LIVE-readback.md` L4、L37-43 |

## 8. Evidence（逐条在盘，可直接对盘）

1. **建页 LIVE 全链** — `docs/audit/udc-design-time-deploy-write-contracts.md` L15（`POST /service/udc/page-info/base-info/create` ×2，
   验收单列表 **LIST id `1871471844026226944`** / 详情 DETAIL id `2146495017352265083`，全 `BOOT_0000`，test2 活体 2026-09-24，文档头 L3）、
   L16（回读 200 / 仅认 relationGroupId）、§二 L29-40（契约路由、必填链、`PageTypeEnum` 12 值、`PageDefinitionDto` 字段）。
   **等级 = `OBSERVED_LIVE`。**
2. **方案声明（step3）** — `components/platform_operations/deployment.py` L157-174（op/body/verify/note；LIST 项 L160-164）。
3. **registry 契约行** — `components/platform_operations/registry.py` L55 `udc.page_log.search` / L56 `udc.page_log.search_non_metadata` /
   L57 `udc.page_info.check_exists` / L58 `udc.page_info.select_host_and_only_page`（均 `method="POST"`、`OperationStatus.VERIFIED_STATIC_BYTECODE`、`write=False`、
   evidence dict 含 `class_sha256` 与 `javap` 路径）。行号本刀 `grep -n` 复验；`registry.py` 本刀实测 sha256 前 16 = `a31bd9a86419bb59`。
4. **4 端点 LIVE 双发回读** — `docs/audit/artifacts/udc-page-5.3.517/LIVE-readback.md` L13-22（表格 + 终结行）+ 同目录
   `LIVE-readback-runtime.json`：C2b `bytes 601463/601463`、`md5 53a8c57d…`、`list_len=421` 非空枚举（L30-39）；
   C2a `109/109`、`md5 8c3c5afa…`、`content=[true]`、`traceId 3239761250497857724`（L41-63）；
   C1a `202/202`、`md5 f1daa06c…`、`traceId 3239761258500589756`、`total=0`（L64-81）；
   C1b `202/202`、`md5 f1daa06c…`、`traceId 3239761266754980028`、`total=0`（L82-99）；
   执行时间 `2026-09-20T16:13Z`（`LIVE-readback.md` L2 / `runtime.json` L2），凭据仅引路径 + `expires_epoch=1789926325`（L4-6）。
   **等级 = `OBSERVED_LIVE`**（C1a/C1b 为空分页 = 读回面稳定，非数据存在性，`runtime.json` L102）。
5. **页面定义可证字段集** — `components/construction/page_definition.py` L18-24 `PAGE_DEFINITION_FIELDS`（注释原文「C2b LIVE 实证的页面定义字段集（`UdcMainPageMetadataDto`，421 样本逐字段观测）」）；
   **本刀实测字段数 = 19**：`appName, caption, clientType, fullName, inApp, inParams, layout, masterEntity, menuCode, name,
   outParameters, pageType, pageUrl, publicAccess, relationGroupId, sourceType, subPages, urlType, validate`
   （注：HANDOFF 转述「18 字段」与在盘实测不符，**以实测 19 为准**）；渲染侧 known/UNVERIFIED 面 L58-64、L69-71。
   本刀实测 sha256 前 16 = `1c6c7508d4716e60`。
6. **页面规则域契约** — `docs/operation-contracts/udc/page/page-readonly-contracts.md` L26-39（metadata_layer 判定表、5 层不可顶替声明、版本族隔离声明）、L43-93（C1a/C1b/C2a/C2b 四要素表）；
   `docs/operation-contracts/udc/page/registry-entries.md` L57（C2b 参数名 `request` javap LocalVariableTable FACT）、L169-171（双端点重叠事实记录）。
7. **javap 实证** — `docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt` L136-137 / L168-169（@PostMapping 动词字面）、L45/L46/L55（常量池）；
   `docs/audit/artifacts/udc-page-5.3.517/UdcRtPageLogController.javap.txt`（同目录在盘，15844 B）。**等级 = `VERIFIED_STATIC_BYTECODE`。**
8. **列表数据查询面** — `core/facts/udc/runtime-data-read.md` L13-17（`data/query` 三参数字典 + 单条语义）、L38-40（LIVE 09-25 `traceId 3246998001134078140 / 3246998500625352892`）；
   `registry.py` L101-102（双斜杠条 `udc.entity_data.query_form_data`，`udc-runtime/data//query` 逐字保留）。
9. **口径样板** — `core/facts/udc/entity/create.md`（B1 全格，本刀实测 sha256 前 16 = `f5476b8b948cedfa`）、
   `core/facts/udc/readonly-faces-batch2.md`、`core/facts/udc/runtime-data-read.md`（合并式 LIVE 格）。
10. **目标目录缺口实测** — `<XIAOZHUA_AGENT_ROOT>/core/facts/udc/` 本刀实测仅 `entity/`、`readonly-faces-batch2.md`、
    `runtime-data-read.md`，**`page/` 不存在** → 本件新建 `core/facts/udc/page/`（符合缺口定位）。

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `udc.page.create` LIST 分支契约声明（op/method/path/body/verify） | `VERIFIED_STATIC_BYTECODE` | `deployment.py` L157-174 |
| 建列表页 LIVE 全链（POST → `BOOT_0000`，LIST id `1871471844026226944`） | `OBSERVED_LIVE` | audit L15、§二 L29-40 |
| `PageTypeEnum` 12 值含 `LIST`；`actionType` 枚举；`TerminalTypeEnum` 同源 `urlType` | `VERIFIED_STATIC_BYTECODE`(javap) | audit §二 L36、L39 |
| 必填链与错误码 `BOOT_1001` / `BOOT_1000` / `BOOT_3002` | `OBSERVED_LIVE` | audit §二 L33-37 |
| 运行态元数据读面：C2b 非空枚举 421 条 / C2a `content=[true]`（双发 identity 一致） | `OBSERVED_LIVE` | `LIVE-readback.md` L15-16 + `runtime.json` L24-63 |
| 页面运行日志读面：C1a/C1b 回读面稳定（空分页 `total=0`，**非数据存在性**） | `OBSERVED_LIVE`（读回面） | `LIVE-readback.md` L17-18 + `runtime.json` L102 |
| registry 页面域 4 契约行（POST / VERIFIED_STATIC_BYTECODE / write=False） | `VERIFIED_STATIC_BYTECODE` | `registry.py` L55-58 |
| 页面定义字段集 19 字段（`UdcMainPageMetadataDto`，421 样本） | `VERIFIED_STATIC_BYTECODE`（字段名）+ 样本 LIVE 来历 | `page_definition.py` L18-24 |
| 列表数据查询面（`udc.runtime-data.read`）参数字典与响应形态 | `OBSERVED_LIVE` | `runtime-data-read.md` L13-17、L38-40 |
| 设计态写 agent 侧恒拒（`DENIED/POLICY_DENIED`） | `VERIFIED_STATIC_BYTECODE` | `layer.py:22`（本刀实测） |
| 页面随 RELEASE 构建发布；物理表落应用自身库 | `OBSERVED_LIVE`（bill 实体表实证） | audit L17-18、L24-25、L84 |

**UNVERIFIED（如实标注，不臆造）**：

1. **列表页生成态 controller 路由** —— 生成态路由字面未直读；`pageUrl` 属「UDC 生成的运行态路由字面，离线不可证」
   （`page_definition.py` L69-71）；模板存在性有记录但路由形态标 UNVERIFIED（`runtime-data-read.md` L26-27）。依据：−（负证据）。
2. **列表页物理表列映射** —— audit L18 实证的是验收单 **bill 实体**物理表，非列表页专用表；生成的 Java 工程是否已落 OSS
   亦「未直读」（audit §六 L78）。依据：−（负证据）。
3. **前端列表生成物是否随 RELEASE 构建生成** —— audit §六 L77 逐字「需活体回读页面面确认（本轮未探）」。
4. **列表数据分页查询读面**（按页/条件返回列表数据） —— 已实测的 `data/query` 是**按 `dataId` 查单条**，`pageNo/pageSize` 被忽略
   （`runtime-data-read.md` L17）；列表分页读面端点未实测。
5. **`UdcPagesMetaDataSearchDto` 5.3.517 完整字段清单** —— 本地无 5.3.517 extmetadata 构件，仅有 5.3.318 继承链 javap 注记
   （`LIVE-readback.md` L33）；版本族隔离禁跨版本复写。
6. **C1a/C1b 是否有页面运行日志数据** —— 空分页仅证明读回面稳定（`runtime.json` L102）。
7. **网关 service 前缀** —— 离线不可确证，禁拼前缀（`registry.py` L55-58 `verification_rules`）。
8. **C1a/C1b 缺 `pageInfo` 包装的入参形态** —— 仅实证 `{"pageInfo":{...}}` 包装可通（`runtime.json` L65-71）。
9. **按 `id` 回读页面（`select-by-appId` 的 id 语义面）** —— LIVE 404，该读面仅认 `relationGroupId`（audit L16 原注 UNVERIFIED）。

> **收口**：列表页（LIST 面）一格已按九段式落盘，逐段锚定在盘 LIVE / STATIC 实据；
> 未直读项（生成态路由、物理表列映射、前端生成物、列表分页读面、5.3.517 DTO 全字段）**如实标 UNVERIFIED，不臆造**。
> 详情页（DETAIL）与菜单绑定归 S2/S3，本件不扩散。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| §1 能力定位 / 写面宿主边界 | `components/platform_operations/deployment.py` L157-180；audit L5-7、L15、§二 L29-31、L69-71 |
| §2 版本 / 版本族隔离 | `registry.py` L53-54（artifact/version）；`page-readonly-contracts.md` L22、L39；`LIVE-readback.md` L33 |
| §3 Input / §4 Required | `deployment.py` L157-174；audit §二 L33-40；`registry.py` L55-58 |
| §5 Execution 写门与执行链 | `layer.py:22`；`page-readonly-contracts.md` L6；`registry.py` L59；`LIVE-readback.md` L5 |
| §6 Side Effects | `deployment.py` L174、L180；audit L17-18、L24-25、L84；`LIVE-readback.md` L4、L39 |
| §7 Known Constraints | `registry.py` L55-58；`page-readonly-contracts.md` L21、L26-39；audit §四 L50-55、§七 L83；`page_definition.py` L69-71 |
| §8 Evidence | 本件 §8 逐条路径（含 `LIVE-readback-runtime.json` 全量行号） |
| §9 Verified / UNVERIFIED | 本件 §9 逐项依据；负证据：audit §六 L77-78、`runtime-data-read.md` L17、L26-27 |
