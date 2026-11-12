# udc.page.create（DETAIL 面）｜详情页能力事实格

> 基线仓库根：`<XIAOZHUA_AGENT_ROOT>`（本件只写 `core/facts/udc/page/detail-page.md`）。
> 九段固定序（1 Capability / 2 Version / 3 Input / 4 Required / 5 Execution / 6 Side Effects /
> 7 Known Constraints / 8 Evidence / 9 Verified）。证据等级三档：`OBSERVED_LIVE` / `VERIFIED_STATIC_BYTECODE` / `UNVERIFIED`。
> 每段引在盘证据（路径 + 行号/字段名），无证据项如实标 `UNVERIFIED`；**凭据 0 入件**（只引路径/对象 id/`expires_epoch`）。
> 本轮范围：**只做详情页（DETAIL 面）一格**；列表页 `list-page.md` 已 auditor PASS 并绑定 hash（`sha256=639fa0e0…ed6a` / 22188B），
> **本件不改写该件**；菜单绑定留 S3，不扩散。
> 行号勘误口径（沿用 S1 VERDICT D1/D2 与本轮 ROUTE §3）：`LIVE-readback.md` 执行时间依据 = **L3**；
> C2a 三元组的**字段名**在盘出处 = `LIVE-readback.md` **L16/L32**（`registry.py` L57 仅作 DTO 类型依据）。

---

## 1. Capability

**建详情页（DETAIL 面）= 设计态写能力 `udc.page.create` 的 DETAIL 分支 + 详情页运行态回读读面 + 详情单条数据读面。**

- **主能力**：`udc.page.create` —— 一次设计态提交为某应用创建「一组页面（基础信息）」，方案中原值为
  **页面对 = LIST + DETAIL**（bill 族），平台为每组返回 `relationGroupId`；详情页 = 该数组中 `pageType="DETAIL"` 的那一项。
  依据：`components/platform_operations/deployment.py` L157-174（`DeploymentStep(op="udc.page.create", method="POST",
  path="/service/udc/page-info/base-info/create", body=[LIST 项 L160-164, DETAIL 项 L165-169])`；L172 `note` 逐字
  「页面对=LIST+DETAIL（bill 族）」）；`docs/audit/udc-design-time-deploy-write-contracts.md` L15
  （建页 ×2 全 `BOOT_0000`，**详情页 DETAIL id `2146495017352265083`**）、§二 L29-31
  （`PageInfoController` 类级 `/udc/page-info` + 方法级 `/base-info/create`，RestApiOperation 原文
  「创建新页面(只包含基础信息，会同时新建多个页面类型为一组)」）。
- **类型**：CONFIG 型 —— agent 出**只读方案 data**（`deploy_plan.steps`），宿主执行真实写端点；agent 侧写门恒拒（见 §5）。
- **详情页类型值**：`DETAIL` ∈ `PageTypeEnum` 12 值（LIVE javap 值域，audit §二 L39）。
  注：`DETAIL` 与 `LIST_DETAIL` 在该枚举中是**两个不同值**（audit §二 L39 逐字 12 值），本格只用 `DETAIL`。
- **配套只读读面（均 `write=False`，同域事实）**：
  | 读面 | operation_id | metadata_layer | 依据 |
  |---|---|---|---|
  | 运行态元数据读面（枚举页，返回 `UdcMainPageMetadataDto`，含 `pageType`/`relationGroupId`） | `udc.page_info.select_host_and_only_page`（C2b） | 运行态元数据层 FACT | `registry.py` L58；`docs/operation-contracts/udc/page/page-readonly-contracts.md` L31 |
  | 运行态元数据读面（存在性） | `udc.page_info.check_exists`（C2a） | 运行态元数据层 FACT | `registry.py` L57；同上 L30 |
  | 运行日志读面 | `udc.page_log.search`（C1a） | 运行态日志层（非 metadata 层）FACT | `registry.py` L55；同上 L28 |
  | 运行日志读面（元数据差异面） | `udc.page_log.search_non_metadata`（C1b） | 运行态日志层 FACT | `registry.py` L56；同上 L29 |
  | 详情单条数据读面 | `udc.runtime-data.read`（`core/facts/udc/runtime-data-read.md`） | 运行态数据层（`udc-runtime/data/query`） | `core/facts/udc/runtime-data-read.md` L1-17 |

## 2. Version

- **Canonical = `udc-starter-runtime` 5.3.517**：`registry.py` L53/L54 evidence dict 逐字
  `"artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517"`，并带 `"javap"` 路径
  （L53 = `…/UdcRtPageLogController.javap.txt`，L54 = `…/UdcRtPageInfoController.javap.txt`）。
- **版本族隔离（规则④）**：本件全部契约证据（bytecode SHA-256 / base / 方法 / DTO / metadata_layer 判定）绑定
  5.3 族 **5.3.517 单一构件**；test2 部署态镜像 **5.3.496** 为独立证据单元，**禁混写**
  （`page-readonly-contracts.md` L22、L39）。
- **版本单元注记（不得升级）**：C2b 请求体 `UdcPagesMetaDataSearchDto` 的**继承链字段**来自
  `boot-starter-extmetadata` **5.3.318** javap（本地无 5.3.517 extmetadata 构件），注记原文未写入 C2b evidence
  （`docs/audit/artifacts/udc-page-5.3.517/LIVE-readback.md` L33）→ 该 DTO 在 5.3.517 下的完整字段清单 = **UNVERIFIED**（§9）。
- **设计态与运行态构件分属**：建页端点出自设计态 `udc-web-5.3.517.jar`（audit §二 L29 逐字）；
  运行态读面出自 `udc-starter-runtime-5.3.517.jar`（`registry.py` L53/L54）。两者同族不同构件，**不得互相顶替**。

## 3. Input

`deploy_plan(application_id, entity_name, attributes, caption)` 产出的 **step3 声明**中 DETAIL 项
（`deployment.py` L157-174；DETAIL 项 **L165-169**，数组闭合 L170，verify L171，note L172-174）：

```
op       = udc.page.create
method   = POST
path     = /service/udc/page-info/base-info/create
body[1]  = {
    "appId":           <app_id_num>,          # application_id 转数字（_to_app_id）
    "caption":         "{caption}详情",
    "pageType":        "DETAIL",              # PageTypeEnum 12 值之一（≠ LIST_DETAIL）
    "masterEntityIds": "<entity_id>",         # 实体数字 id
    "pageUrl":         "{entity_name.lower()}detail",
    "curTerminalType": "PC",
    "pageItems": [ { "pageUrl": "{entity_name.lower()}detail", "urlType": "PC",
                     "menuName": "{caption}详情", "actionType": "NORMAL", "orderNo": 1 } ]
}
```

- **同次提交的兄弟项**：`body[0]` = LIST 项（`deployment.py` L160-164）——详情页不单独提交，与列表页同批成组
  （L172 `note`「页面对=LIST+DETAIL（bill 族）」）。
- **DTO 关键字段**：`PageDefinitionDto` = `appId(数字)/caption/pageType/masterEntityIds/pageUrl/curTerminalType/pageItems[]`
  （audit §二 L40，LIVE javap 实测字段清单）。
- **读面入参形态**（回读该组页/该详情页）：
  - C2b：`@RequestBody UdcPagesMetaDataSearchDto`（LIVE 实测 body `{"appName":"app9000000000000000001"}`）；
    参数名 `request` 经 javap LocalVariableTable 逐字实取（`registry.py` L58；`registry-entries.md` L57）。
  - C2a：`@RequestBody List<UdcRtPageExistsDto> pageExistsDtoList`，三元组字段名
    `appName`+`pageUrl`+`terminalType`（**字段名出处**：`LIVE-readback.md` L16 LIVE body / L32 javap 实证；
    `registry.py` L57 提供 DTO 类型与参数名依据）。
  - C1a/C1b：`@RequestBody PageDtoRequest<UdcRtPageLogSearchDto> query`，LIVE 包装 = `{"pageInfo":{"pageNo":1,"pageSize":20}}`
    （`LIVE-readback-runtime.json` L65-71 / L83-89）；非 `pageInfo` 包装形态 UNVERIFIED。
- **详情单条数据读面入参**：`POST {gateway}/{PF}/udc-runtime/data/query`，body SingleRequest 包装 `{"data":{...}}`，
  三参数字典 = `appName 应用编码; dataId 数据id; entityFullName 实体FullName`（LIVE BOOT_3000 原文，
  `core/facts/udc/runtime-data-read.md` L13-16）。

## 4. Required（必填链、值域与错误码）

同一端点、同一必填链、同一提交体 —— DETAIL 项与 LIST 项**共用**下列约束（audit §二 L33-37，LIVE 逐步试出）：

| # | 项 | 要求 | 缺/错后果（LIVE 错误码原文） | 依据 |
|---|---|---|---|---|
| 1 | `pageType` | 必填（本格取 `DETAIL`） | `BOOT_1001 pageType must not be null` | audit §二 L33 |
| 2 | `pageUrl` | 必填（**顶层与 `pageItems[]` 皆需**） | `BOOT_1001 pageUrl must not be null` | audit §二 L34 |
| 3 | `curTerminalType` | 必填 | `BOOT_1000 页面终端信息为空，请选择` | audit §二 L35 |
| 4 | `actionType` | ∈ `{NORMAL, INSERT, UPDATE, DELETE}`（`com.seeyon.boot.enums.ActionType` javap） | `VIEW` 不存在 → `BOOT_3002` | audit §二 L36 |
| 5 | `masterEntityIds` | = 实体数字 id | — | audit §二 L37 |
| 6 | `urlType` | ∈ `{PC, MOBILE}`（`TerminalTypeEnum` 同源） | — | audit §二 L37 |

- 与方案声明一致：`deployment.py` L172-173 `note` 逐字列必填链
  「`appId/pageType/masterEntityIds/pageUrl/curTerminalType/pageItems[].{pageUrl,urlType,menuName,actionType=NORMAL}`；
  缺 `pageUrl` 或 `curTerminalType` → `BOOT_1001`/`BOOT_1000`「页面终端信息为空」；`actionType` 枚举 `{NORMAL,INSERT,UPDATE,DELETE}`」。
- **DETAIL 分支的方案侧取值**（非必填性断言，仅为原值）：`caption="{caption}详情"`、`pageUrl="{entity_name.lower()}detail"`、
  `pageItems[].menuName="{caption}详情"`、`actionType="NORMAL"`、`orderNo=1`（`deployment.py` L165-169）。
- **枚举快照**：`PageTypeEnum` 12 值 = `PORTAL/WELCOME/REPORT_FORM/**DETAIL**/LIST/APPROVAL/PORTLET/SEARCH_LIST/EDIT_LIST/LIST_DETAIL/ASSIST_INFO/OTHER`
  （audit §二 L39）。值域 = 活体快照，**非永久常量**（audit §四 L50-55、§七 L83）。
- **读面必填**：C2b `appName`（LIVE 唯一入参键）；C2a 三元组 `appName+pageUrl+terminalType`（字段名出处见 §3）；
  C1a/C1b `pageInfo` 包装键（LIVE 实证）。
- **详情单条数据读面必填**：`appName` + `entityFullName` + `dataId` 三键语义并列（逐键必填性未单键实测 → 标注，
  `runtime-data-read.md` L20）。

## 5. Execution

- **agent 侧不出写**：写门 `components/platform_operations/layer.py:22`
  `if contract.write or contract.method != "GET" or not contract.effective:` → `OperationStatus.DENIED` + `ErrorKind.POLICY_DENIED`
  （本刀直读原文）。建详情页属设计态写，**只能由宿主按 `steps` data 授权执行**。
- **本域 4 条读契约在 agent 执行链上同样不放行**：均为 `@PostMapping` 注解字面动词
  （`UdcRtPageInfoController.javap.txt` L136-137 `value=["check-page-exists"]`、L168-169 `value=["select-host-and-only-page-pages"]`；
  类级 `@RequestMapping value=["udc-runtime/meta-data"]` 见同文件 L181-182；`registry.py` L55-58 逐条 `write=False`、method=`POST`）
  → `effective()` 三条件（GET + VERIFIED_STATIC_BYTECODE + write=False）不满足 → `DENIED/POLICY_DENIED`
  （`page-readonly-contracts.md` L6「HTTP method 一律取注解字面动词，不按读语义改写」；`registry.py` L59 `note` 同边界）。
  读面 LIVE 回读由宿主/系统操作者凭据执行（§8 证据 4）。
- **宿主执行姿势（建页）**：`POST /service/udc/page-info/base-info/create` → LIVE `BOOT_0000`
  （audit L15；网关 service 前缀由调用方拼，契约原路径禁拼前缀，见 §7）。
- **宿主回读 verify**：`GET /service/udc/page-info/select-by-appId/{appId}` 回读新页 `caption + relationGroupId`
  （`deployment.py` L171）；LIVE 200、验收单 **2 命中**（`-6629355753974142446` / `-6832321505567116615`，即 `relationGroupId`；
  **按页 id 回读 404** = 该读面仅认 `relationGroupId`，UNVERIFIED）（audit L16）。
- **运行态回读 URL 姿势（LIVE 实证）**：`base=https://lowcode-test2.example.com` + 网关前缀
  `/service/app9000000000000000001` + 控制器原路径逐字（`LIVE-readback.md` L5；`LIVE-readback-runtime.json` L7-9）。
- **详情单条数据读面执行**：`POST {gateway}/{PF}/udc-runtime/data/query`，LIVE `BOOT_0000` 级响应路径打开；
  无 `udc-runtime/` 直挂 service 前缀被 nginx 403/404（`runtime-data-read.md` L21-22）。
  **语义 = 按 `dataId` 查单条**，`pageNo/pageSize` 被忽略（同件 L17）→ 该面与「详情页数据装载」的绑定关系 UNVERIFIED（§9）。
- **层级纪律**：上述读面分属运行态元数据层（C2a/C2b）/ 运行态日志层（C1a/C1b）/ 运行态数据层（`data/query`），
  **不等于**设计态建页配置，也不等于生成物/物理表（`page-readonly-contracts.md` L21、L37）。

## 6. Side Effects

- **建页 = 设计态写**，不直接落物理表、不改运行态元数据：`deployment.py` L174 `note` 逐字
  「C2b 运行态元数据面只回读**已发布页**，新建设计稿在该面不可见是预期行为」。
- **详情页随 RELEASE 构建发布**：`deployment.py` L180 `note`「放在建页之后：页面设计稿随构建发布」；
  audit L24-25 关键认知修正「前端页面**不是构建送的**：页面是独立设计态动作（`PageInfoController.createBaseInfo`），
  需在建实体后显式创建，再随构建发布」。
- **物理表落应用自身库**（`{app}_test2` / `{app}_uat`），**非 `udc_test2`**（audit L18 实测、§七 L84 铁律 3）。
  注：该 LIVE 实证的物理表为验收单 **bill 实体**表 `yanshouda_m5654091886000795633`；
  **详情页自身的物化面/列映射 UNVERIFIED**（§9）。
- **读面零副作用**：4 端点 `scope=read-only`、零写操作、无 publish/deploy（`LIVE-readback.md` L4、L39 红线自证）。
- 建页 LIVE 关联链（同批实证）：建实体 `7670732978062038177`、建属性 ×4、建页 ×2（LIST+DETAIL）、
  RELEASE 构建 `deploy_type=2 state=1`（audit L13-18）。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| 网关 service 前缀 **UNVERIFIED** | 契约原路径**禁拼前缀**当可用 URL；仅宿主拼 `{gateway_base}{prefix}` | `registry.py` L55-58 各条 `verification_rules` 末项；audit §三 L45-48 |
| 4 读契约 `method=POST` | `effective()=False` → 执行层 `DENIED/POLICY_DENIED`（非 FAIL） | `page-readonly-contracts.md` L6；`registry.py` L59 `note`；`layer.py:22` |
| **按页 id 回读 404** | 运行态回读面**仅认 `relationGroupId`**；不得用页 id 当读面身份 | audit L16（原文标 UNVERIFIED） |
| metadata_layer **五层不可顶替**（设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis 缓存） | 不得以「Boolean 结果 / HTTP 200 / 相邻版本 / 其他层 / 前端生成物」顶替 | `page-readonly-contracts.md` L21、L37（判定表 L26-35） |
| 版本族隔离 | test2 部署态 5.3.496 / 旧版 5.3.345-358 **禁与 5.3.517 混写** | `page-readonly-contracts.md` L22、L39 |
| 值域/枚举 = 活体快照 | 非永久常量，不得硬编码进调用方 | audit §四 L50-55、§七 L83 |
| `pageUrl` 是 UDC 生成的**运行态路由字面** | 离线不可证 → 标 UNVERIFIED，不臆造 | `components/construction/page_definition.py` L69-71 |
| 双 operation_id 同物理端点 | `registry.py` L57/L58（page 域）与 L62/L60（meta-data 域）指向同一对端点 → 归域/去重留裁定，本件只记事实 | `docs/operation-contracts/udc/page/registry-entries.md` L171（D 项） |
| 凭据纪律 | 只引路径 + `expires_epoch`；token 明文 0 入件 | `LIVE-readback.md` L4、L37-43 |
| 引用定位（本轮勘误口径） | 执行时间依据 = `LIVE-readback.md` L3；C2a 三元组字段名依据 = 同件 L16/L32 | ROUTE §3 勘误注（源自 auditor VERDICT S1 D1/D2） |

## 8. Evidence（逐条在盘，可直接对盘）

1. **建页 LIVE 全链（含 DETAIL）** — `docs/audit/udc-design-time-deploy-write-contracts.md` L15
   （`POST /service/udc/page-info/base-info/create` ×2，验收单列表 LIST id `1871471844026226944` /
   **详情 DETAIL id `2146495017352265083`**，全 `BOOT_0000`，test2 活体 2026-09-24，文档头 L3）、
   L16（回读 200、仅认 `relationGroupId` `-6629355753974142446` / `-6832321505567116615`；按 id 404=UNVERIFIED）、
   §二 L27（章节定位）/L29-31（类级+方法级路由、RestApiOperation 原文）/L33-37（必填链错误码）/L39（`PageTypeEnum` 12 值含 `DETAIL`）/L40（`PageDefinitionDto` 字段）。
   **等级 = `OBSERVED_LIVE`。**
2. **方案声明（step3 DETAIL 项）** — `components/platform_operations/deployment.py` L157-174
   （op/method/path L157-158；body 数组起始 L159；LIST 项 L160-164；**DETAIL 项 L165-169**；数组闭合 L170；verify L171；note L172-174）。
   本刀实测 sha256 前 16 = `59e92dfeb4d33d4f`。
3. **registry 契约行** — `components/platform_operations/registry.py` L53-62：L53（`page_log` evidence：method/class_sha256/javap 路径）、
   L54（`page_info` evidence 同构）、L55 `udc.page_log.search`、L56 `udc.page_log.search_non_metadata`、L57 `udc.page_info.check_exists`、
   L58 `udc.page_info.select_host_and_only_page`（均 `method="POST"`、`OperationStatus.VERIFIED_STATIC_BYTECODE`、`write=False`）、
   L59（元数据锚点 evidence `note`：`@PostMapping` → `DENIED/POLICY_DENIED` 属已知边界）、
   L60/L62（meta-data 域同物理端点重叠条，只记事实不代决）。本刀实测 sha256 前 16 = `a31bd9a86419bb59`。
4. **4 端点 LIVE 双发回读** — `docs/audit/artifacts/udc-page-5.3.517/LIVE-readback.md` **L3**（执行时间 `2026-09-20T16:13Z`）、
   L13-22（逐端点终态表与终结行：C2b `601463/601463` `53a8c57d…` `len=421`；C2a `109/109` `8c3c5afa…` `content=[true]`；
   C1a/C1b `202/202` `f1daa06c…` `total=0`）、**L16**（C2a 三元组字段名＝LIVE body 出处）、L18（`PASS（读回面稳定, 非数据存在性）`）、
   **L32**（`UdcRtPageExistsDto` 三元组＝5.3.517 javap 实证）、L4（凭据仅引路径 + `expires_epoch=1789926325`）；同目录
   `LIVE-readback-runtime.json` L2（`generated_at`）/L7-9（base/app_id/gateway_prefix）/L24-39（C2b）/L41-63（C2a，`traceId 3239761250497857724`）/
   L64-81（C1a，`traceId 3239761258500589756`）/L82-89（C1b，`traceId 3239761266754980028`）/L102（`note_c1a_c1b_empty`）。
   **等级 = `OBSERVED_LIVE`**（C1a/C1b 为空分页 = 读回面稳定，**非数据存在性**）。
5. **元数据锚点规则与版本纪律** — `docs/operation-contracts/udc/page/page-readonly-contracts.md` L6（method 取注解字面）、
   L21（规则③ 五层不可顶替）、L22（规则④ 版本族隔离）、L26-35（C1a/C1b/C2a/C2b 判定表）、L37（五层声明）、L39（版本族隔离声明）。
6. **页面定义可证字段集** — `components/construction/page_definition.py` L18-24 `PAGE_DEFINITION_FIELDS`
   （注释原文「C2b LIVE 实证的页面定义字段集（`UdcMainPageMetadataDto`，421 样本逐字段观测）」；**本刀实测 19 字段**：
   `appName, caption, clientType, fullName, inApp, inParams, layout, masterEntity, menuCode, name, outParameters,
   pageType, pageUrl, publicAccess, relationGroupId, sourceType, subPages, urlType, validate` —— 与 auditor VERDICT S1「19 字段」核定一致）、
   L58-64（渲染侧 known 简表）、L69-71（`pageUrl` → UNVERIFIED）。本刀实测 sha256 前 16 = `1c6c7508d4716e60`。
7. **javap 实证** — `docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt` L136-137（`@PostMapping value=["check-page-exists"]`）、
   L168-169（`value=["select-host-and-only-page-pages"]`）、L181-182（类级 `@RequestMapping value=["udc-runtime/meta-data"]`）、
   L144（方法签名 `ListResponse<UdcMainPageMetadataDto> selectHostAppAndOnlyPageAppPages(...)`）；
   `docs/audit/artifacts/udc-page-5.3.517/UdcRtPageLogController.javap.txt`（同目录在盘，15844 B）。
   **等级 = `VERIFIED_STATIC_BYTECODE`。**
8. **详情单条数据读面** — `core/facts/udc/runtime-data-read.md` L13-17（`data/query` 端点 + `{"data":{...}}` 包装 + 三参数字典 + 单条语义）、
   L20-27（三键并列 / 网关前缀实测 / 生成态模板存在性与路由 UNVERIFIED）、L38-40（LIVE 2026-09-25，
   `traceId 3246998001134078140` / `3246998500625352892`）。
9. **口径样板** — `core/facts/udc/entity/create.md`（B1 全格；本刀实测 sha256 前 16 = `f5476b8b948cedfa`）、
   `core/facts/udc/readonly-faces-batch2.md`（合并式 LIVE 格）。
10. **同域已 PASS 的冻结件（口径锚点，本刀未改）** — `core/facts/udc/page/list-page.md`：
    22188 B / `sha256=639fa0e008328547cd121daf62fbae9ee1ac7c4ea710bc01c39581877b94ed6a`（auditor A1 PASS 绑定值，本刀复测一致）。
11. **目标目录现状（写件时点实测）** — `core/facts/udc/page/` 写前仅 `list-page.md`（22188 B）；
    注：`core/facts/` 级与他线目录（`INDEX.md` / `serial/` / `{bpm,gateway,runtime}/`）非本会话三角色产物，**不作口径源**。

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `udc.page.create` DETAIL 分支契约声明（op/method/path/body/verify/note） | `VERIFIED_STATIC_BYTECODE` | `deployment.py` L157-174（DETAIL 项 L165-169） |
| 建详情页 LIVE（POST → `BOOT_0000`，**DETAIL id `2146495017352265083`**，与 LIST 同批成组） | `OBSERVED_LIVE` | audit L15、§二 L29-31/L39/L40 |
| `PageTypeEnum` 12 值含 `DETAIL`（且 `DETAIL` ≠ `LIST_DETAIL`） | `VERIFIED_STATIC_BYTECODE`(javap) | audit §二 L39 |
| 必填链与错误码 `BOOT_1001` / `BOOT_1000` / `BOOT_3002`（DETAIL 与 LIST 共用同端点同链） | `OBSERVED_LIVE` | audit §二 L33-37；`deployment.py` L172-173 |
| 运行态回读：`select-by-appId` 200、**仅认 `relationGroupId`**（2 命中） | `OBSERVED_LIVE` | audit L16；`deployment.py` L171 |
| 运行态元数据读面：C2b 非空枚举 421 条（`UdcMainPageMetadataDto`，字段含 `pageType`/`relationGroupId`）/ C2a `content=[true]`（双发 identity 一致） | `OBSERVED_LIVE` | `LIVE-readback.md` L13-22 + `runtime.json` L24-63；`page_definition.py` L18-24 |
| 运行日志读面 C1a/C1b 回读面稳定（空分页 `total=0`，**非数据存在性**） | `OBSERVED_LIVE`（读回面） | `LIVE-readback.md` L18 + `runtime.json` L102 |
| registry 4 读契约行（POST / VERIFIED_STATIC_BYTECODE / write=False）+ 同端点重叠条 | `VERIFIED_STATIC_BYTECODE` | `registry.py` L55-58、L60/L62 |
| 详情单条数据读面（`data/query` 参数字典、单条语义、响应形态） | `OBSERVED_LIVE` | `runtime-data-read.md` L13-17、L38-40 |
| 设计态写 agent 侧恒拒（`DENIED/POLICY_DENIED`） | `VERIFIED_STATIC_BYTECODE` | `layer.py:22`（本刀直读） |
| 详情页随 RELEASE 构建发布；物理表落应用自身库 | `OBSERVED_LIVE`（bill 实体表实证） | audit L17-18、L24-25、L84 |

**UNVERIFIED（如实标注，不臆造）**：

1. **详情页生成态 controller 路由** —— 生成态路由字面未直读；`pageUrl` 属「UDC 生成的运行态路由字面，离线不可证」
   （`page_definition.py` L69-71）；生成态模板存在性有记录但路由形态标 UNVERIFIED（`runtime-data-read.md` L26-27）。
2. **详情页物理表列映射** —— audit L18 实证的是验收单 **bill 实体**物理表，非详情页专用表；生成工程落 OSS「未直读」（audit §六 L78）。
3. **前端详情生成物是否随 RELEASE 构建生成** —— audit §六 L77 逐字「需活体回读页面面确认（本轮未探）」。
4. **按页 id 回读面** —— LIVE **404**，该读面仅认 `relationGroupId`（audit L16 原注）。
5. **`UdcPagesMetaDataSearchDto` 5.3.517 完整字段清单** —— 本地无 5.3.517 extmetadata 构件，仅有 5.3.318 继承链 javap 注记
   （`LIVE-readback.md` L33）；版本族隔离禁跨版本复写。
6. **两条 `relationGroupId` 与 LIST/DETAIL 的逐页归属映射** —— 在盘只给出「验收单 2 命中」与两条 `relationGroupId` 值
   （audit L16），**未记载哪一条对应 DETAIL 页** → 不臆造。
7. **详情页数据装载路由（详情页打开时读哪条数据）** —— 已实测的 `data/query` 是**按 `dataId` 查单条**（`runtime-data-read.md` L17），
   其与详情页运行态装载的绑定关系未实测。
8. **C1a/C1b 是否有页面运行日志数据** —— 空分页仅证明读回面稳定（`runtime.json` L102）。
9. **网关 service 前缀** —— 离线不可确证，禁拼前缀（`registry.py` L55-58 `verification_rules`）。
10. **C1a/C1b 缺 `pageInfo` 包装的入参形态** —— 仅实证 `{"pageInfo":{...}}` 包装可通（`runtime.json` L65-71）。

> **收口**：详情页（DETAIL 面）一格已按九段式落盘，逐段锚定在盘 LIVE / STATIC 实据；
> 未直读项（生成态路由、物理表列映射、前端生成物、按 id 回读面、5.3.517 DTO 全字段、relationGroupId 逐页归属、
> 详情数据装载路由）**如实标 UNVERIFIED，不臆造**。菜单绑定归 S3，本件不扩散；`list-page.md` 未改写。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| §1 能力定位 / 写面宿主边界 | `deployment.py` L157-174；audit L15、§二 L29-31 |
| §2 版本 / 版本族隔离 / 构件分属 | `registry.py` L53-54；`page-readonly-contracts.md` L22、L39；`LIVE-readback.md` L33；audit §二 L29 |
| §3 Input / §4 Required | `deployment.py` L157-174；audit §二 L33-40；`registry.py` L55-58；`runtime-data-read.md` L13-16、L20 |
| §5 Execution 写门与执行链 | `layer.py:22`；`page-readonly-contracts.md` L6；`registry.py` L59；`UdcRtPageInfoController.javap.txt` L136-137/L168-169/L181-182；`LIVE-readback.md` L5 |
| §6 Side Effects | `deployment.py` L174、L180；audit L17-18、L24-25、L84；`LIVE-readback.md` L4、L39 |
| §7 Known Constraints | `registry.py` L55-58；`page-readonly-contracts.md` L6/L21/L22/L26-39；audit L16、§三 L45-48、§四 L50-55、§七 L83；`page_definition.py` L69-71；ROUTE §3 勘误注 |
| §8 Evidence | 本件 §8 逐条路径与行号（含 `LIVE-readback-runtime.json` 全量行号） |
| §9 Verified / UNVERIFIED | 本件 §9 逐项依据；负证据：audit L16、§六 L77-78、`runtime-data-read.md` L17、L26-27、`LIVE-readback.md` L33 |
