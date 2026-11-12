# udc.menu.bind（菜单绑定面）｜菜单绑定能力事实格（第 3/3 格）

> 基线仓库根：`<SEEYON_AGENT_ROOT>`（本件只写 `core/facts/udc/page/menu-bind.md`）。
> 九段固定序（1 Capability / 2 Version / 3 Input / 4 Required / 5 Execution / 6 Side Effects /
> 7 Known Constraints / 8 Evidence / 9 Verified）+ 尾部溯源索引。证据等级三档：`OBSERVED_LIVE` / `VERIFIED_STATIC_BYTECODE` / `UNVERIFIED`。
> 每段引在盘证据（路径 + 行号/字段名），无证据项如实标 `UNVERIFIED`；**凭据 0 入件**（只引路径/对象 id/`expires_epoch`）。
> 本轮范围：**只做菜单绑定面一格**；`list-page.md`、`detail-page.md` 均已 auditor PASS 并绑定 hash，**本件不改写该两件**。
> 硬约束（HANDOFF S3 + main DECISION 更正 1/2/3 + registry 基准钉死）：
> A. **0 处 V2 变体读面字面**（形如「appId 读面名 + `V2` 后缀」的写法；全库 0 命中已判作废；在盘只有 V1 `select-by-appId`，本件正文实测 0 处）；
> B. **不以前端 chunk 顶替后端契约**（`page-readonly-contracts.md` L21/L37 五层不可顶替）；
> C. 「菜单有独立 menu 接口」在盘无证据 → 只能标 `UNVERIFIED`，**禁升格**（`SCAN.md` §2 负证据在盘）；
> D. C1 功能节点树 **LIVE json**（`microflow/live-evidence/…`，各 187981 B）属微流程域、`SCAN.md` L50 明载不入菜单域候选 → 本件仅定位旁引、**节点计数 UNVERIFIED**；
>    但其 **javap / 审计文档面**（`menuCode` 归组机制，见 §1/§8 条 4）是绑定机制面，**可用**；
> E. 引 `registry.py` **仅 L58 + L108**（main DECISION 白名单）；menu 域文档内引的 LIVE 权威源（`main/…`、`scratch/…`）**实测不在盘** →
>    该处 LIVE 断言只作「**文档内转述**」并标 `UNVERIFIED`（见 §7 首行 + §9 条 11）。

---

## 1. Capability

**菜单绑定面 = 「UDC 无独立 menu 类」负证据 + 菜单↔页面绑定机制（按 `menuCode` 归组）+ 页面↔菜单编码字段 + 建页写入菜单元 + 页面-主机绑定读面 + 菜单域 GET 只读候选族（P1–P5）。**

- **域定位（负证据核心事实）**：UDC 域内**没有独立的 "menu" 类**；菜单域契约取 page / resource / role 语义控制器的只读端点——
  「菜单 = 功能节点 + 页面 + 资源权限的只读视图」（`docs/operation-contracts/udc/menu/SCAN.md` §1 L7-9 逐字）。
- **负证据（菜单关键词 0 命中）**：6 件 5.3.517 UDC jar（`udc-common` / `udc-facade` / `udc-starter-customplan` /
  `udc-starter-dataflow` / `udc-starter-lowcode` / `udc-starter-runtime`）对 `menu|menutree|topbar|sitemenu|resourcemen`
  **计数全 0**（同件 §2 L16-25）；`registry.py` 全文 case-insensitive `menu` 亦 **0 命中**（本刀实测，见 §8 条 11）。
  → 「菜单」**不能当类名/关键词去搜**，须靠功能节点/页面/资源/角色/日志/数据库**语义类**定位（§3 L28-38 的 7 控制器映射表）。
- **菜单↔页面绑定机制（main DECISION 更正 3 新增面，本格最贴近主题）**：`UdcFunctionNodeService.selectFunctionNodeTreeMetaData(appName)`
  组装 `param`（`appId=appName`、**`type=ResourceTypeEnum.MENU`**、`dataStatus=1`），按 `path`/`sortNumber` 分页读 CTP 资源，
  取页面元数据（`UdcPageInfoMetaDataService.selectPageInfoListByAppName`）与 **OSS 页面信息**（`UdcPageMetadata4OssService.getPageInfoListByAppNameWithoutSchema(appName)`），
  **按 `menuCode` 归组**后递归写入 FunctionNode 的 `pageMetadataDtoList`，最终按 `sortNo` 排序。
  依据：`docs/audit/udc-page-tree-function-node-dispatch-audit-20260906.md` L38-47（业务与数据来源）+ 证据行 L51-54；
  `docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeService.javap.txt` L157（`menuCodePageMetadataDtoListMap`）、L187（`menuCode`）、
  L784/L792（局部变量 `menuCodePageMetadataDtoListMap` 类型 `Map<String, List<UdcPageMetadataV2Dto>>`）、L965/L1047（`menuCode: String`）。
  等级 = javap 符号 `VERIFIED_STATIC_BYTECODE` + **归组语义 = 文档表述**（audit 文档 L38-47；其证据行 L51-54 指向 javap L906-977，未逐指令复核）；**运行时真实调用/回读 UNVERIFIED**（同件 L92-95）。
- **页面↔菜单编码字段**：`menuCode` ∈ `PAGE_DEFINITION_FIELDS`（`UdcMainPageMetadataDto`，C2b LIVE 421 样本逐字段观测，
  `components/construction/page_definition.py` L18-24）。
- **建页写入的菜单元**：`pageItems[].menuName`（`components/platform_operations/deployment.py` L164 LIST / L169 DETAIL +
  L172-174 `note` 必填链含 `pageItems[].{pageUrl,urlType,menuName,actionType=NORMAL}`）。
- **页面-主机绑定读面**：`udc.page_info.select_host_and_only_page`（C2b，`registry.py` L58，`write=False`，`VERIFIED_STATIC_BYTECODE`）。
- **菜单域 GET 只读候选族（P1–P5）**：P1 `udc-role/has-system-admin/{appName}`、P2 `app-log/datalog/{id}`、
  P3 `app-log/datalog/list-by-dataid/{dataId}`、P4 `serial-config/select-entity-list`、P5 `database/query-data`
  （`SCAN.md` §4 L42-50；构造见 `docs/operation-contracts/udc/menu/registry-entries.md` L49-56）。

## 2. Version

- **Canonical = `udc-starter-runtime` 5.3.517**：菜单域 javap / 负证据 / 契约构造绑定 5.3.517 单一构件
  （`SCAN.md` 头 L3；`menu/registry-entries.md` L8「jar 基线 `<MAVEN_REPO>/.../udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`，
  jar sha256=`74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`」）。
- **绑定机制面同族**：`UdcFunctionNodeService.javap.txt` 出自 `docs/audit/artifacts/udc-runtime-5.3.517/`（5.3.517）；
  其下游页面元数据链引 `extmetadata-5.3.318` javap（`udc-page-tree-function-node-dispatch-audit-20260906.md` L65/L78）
  → **extmetadata 5.3.318 为独立版本单元**（同 S1/S2 口径，禁与 5.3.517 混写）。
- **负证据覆盖 6 件 5.3.517 jar**（`SCAN.md` §2 L18-23 表）。
- **版本族隔离（规则④）**：test2 部署态 5.3.496 为独立证据单元，**禁混写**（`page-readonly-contracts.md` L22/L39）。

## 3. Input

| 面 | 入参 | 绑定/形态 | 依据 |
|---|---|---|---|
| 菜单↔页面绑定机制 | `appName` | `param`: `appId=appName`、`type=ResourceTypeEnum.MENU`、`dataStatus=1`；排序 `path`,`sortNumber`；`menuCode` 归组 OSS 页面信息 | audit dispatch L40-47 |
| 页面↔菜单编码字段 | `menuCode`（页面主元数据字段之一） | 19 字段 `PAGE_DEFINITION_FIELDS` 成员 | `page_definition.py` L18-24（C2b LIVE 421 样本） |
| 建页写入菜单元 | `pageItems[].menuName` | LIST/DETAIL body 原值（LIST `{caption}列表` / DETAIL `{caption}详情`） | `deployment.py` L164 / L169 |
| 页面-主机绑定读面（C2b） | `UdcPagesMetaDataSearchDto`（LIVE body `{"appName":"app9000000000000000001"}`） | 参数名 `request`（javap LocalVariableTable 实取） | `registry.py` L58；`LIVE-readback.md` L15 |
| P1 权限判定读 | `appName`（`@PathVariable`） | `GET udc-runtime/udc-role/has-system-admin/{appName}` → `SingleResponse<Boolean>` | `menu/registry-entries.md` L50 |
| P2 按 id 读单条日志 | `id`（`@PathVariable`） | `GET udc-runtime/app-log/datalog/{id}` → `SingleResponse<UdcEntityMonitorLogDto>` | `SCAN.md` §3 L35 |
| P3 按 dataId 读日志列表 | `dataId`（`@PathVariable`） | `GET udc-runtime/app-log/datalog/list-by-dataid/{dataId}` → `ListResponse<UdcEntityMonitorLogDto>` | `menu/registry-entries.md` L53 |
| P4 流水配置实体列表 | `appName`（`@MultiRequestBody`） | `GET udc-runtime/serial-config/select-entity-list` → `SingleResponse<EntityGroupAndItemDto>` | `menu/registry-entries.md` L56 |
| P5 运行时数据库查询 | 入参无显式绑定注解 | `GET udc-runtime/database/query-data` → `SingleResponse<UdcRuntimeDatabaseQueryRespDto>`（HYPOTHESIS） | `SCAN.md` §3 L38 / §4 L48 |

> 注：P2 在 `registry.py` 已登记为 `udc.applog.select_by_id`（同路径/同 controller/同 method，`class_sha256 f6a2111d…`），
> 菜单域 P2 契约**不新增条目、直接复用**（`menu/registry-entries.md` L16 逐字）。

## 4. Required

| 面 | 必填/约束 | 依据 |
|---|---|---|
| 绑定机制 | `appName` 非空校验（字节码第 1 步）；`type=ResourceTypeEnum.MENU` 为机制内固定值 | audit dispatch L40-41 |
| `menuCode` | 19 字段可证字段集成员；**单字段必填性 UNVERIFIED**（本件仅证 C2b 样本可见该字段，非必填性断言） | `page_definition.py` L18-24 |
| `pageItems[].menuName` | 在建页必填链内（`note` 逐字列 `pageItems[].{pageUrl,urlType,menuName,actionType=NORMAL}`）；缺项后果与列表/详情共用同端点错误码 | `deployment.py` L172-174 |
| P1 / P4 入参 | `appName` 必填 | `menu/registry-entries.md` L50/L56 `required_inputs=("appName",)` |
| P3 入参 | `dataId` 必填 | 同上 L53 |
| P5 入参 | **HYPOTHESIS**（方法块无 `RuntimeVisibleParameterAnnotations`，全文件 0 次；不入 registry） | `menu/registry-entries.md` L18 |
| P4 传参形态 | `@MultiRequestBody` 经 GET 的**通用**传参约定 = **UNVERIFIED**（离线负证据：全域 52 POST 先例 0 GET，P4 为 GET+@MultiRequestBody 唯一法）；在盘 LIVE 侧 URL 组装式实证 `?appName={default_app_id}` 可通 | `menu/registry-entries.md` L56 内注；`docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md` L24 |

## 5. Execution

- **零写纪律**：P1–P5 全部 `write=False`（`menu/registry-entries.md` L49-56 逐条 `False`；`SCAN.md` §5 L52-62 排除项把
  `delete/clear/unload/set/update` 语义全排除）→ 菜单域**无独立写端点**；菜单写入面 = 建页 `pageItems[].menuName`（设计态写，宿主授权，见 §6）。
- **GET 只读候选可执行性**：P1/P2/P3/P4 = `GET + VERIFIED_STATIC_BYTECODE + write=False` → `effective()=True`
  （`menu/registry-entries.md` L49-56 构造）；但**网关 service 前缀 UNVERIFIED，宿主拼 `{gateway_base}{prefix}`**（各条 `verification_rules` 末项逐字）。
  P5 = 入参绑定 HYPOTHESIS、**不入 registry**（L18）。
- **菜单域候选的在盘 LIVE 实证（改引 entity 域 LIVE 回读，取代不可达源）** ——
  `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md`：L24 P4 `select-entity-list?appName={default_app_id}`
  （HTTP 200 / 3561 B / `BOOT_0000` / SUCCESS / identity MATCH）、L25 P2 `app-log/datalog/1`（200 / 107 B / `BOOT_0000` / MATCH）、
  L26 P3 `app-log/datalog/list-by-dataid/1`（200 / 598076 B / `BOOT_0000` / MATCH）、L27 P1 `udc-role/has-system-admin/{default_app_id}`
  （200 / 107 B / `BOOT_0000` / MATCH）；逐条明细 §4 L34-39 / L41-46 / L48-53 / L55-60；
  URL 组装式 L11-12（`URL = {gateway_base} + /service/{default_app_id} + <控制器原路径>`，键出自 `config/environments.yaml:environments.test2`）。
  **等级 = `OBSERVED_LIVE`**（文档 L3-4 载明窗口 2026-09-18 内完成、现为离线结果记录、不再复跑）。
- **P5 可达性亦在盘 LIVE**：同件 L29 / 明细 L69-74（HTTP 200 / 90 B / `BOOT_3000` 空结果业务码 / identity MATCH，
  「无查询体 → 空结果业务码，只读 GET 无副作用」）→ 可达性 `OBSERVED_LIVE`；**入参绑定仍 HYPOTHESIS**（§4）。
- **页面-主机绑定读面（C2b）执行链边界**：`udc.page_info.select_host_and_only_page` 为 `@PostMapping` 注解字面动词（`registry.py` L58；
  javap 原文 `@PostMapping`），该条 `write=False`、method=`POST` → `effective()` 三条件（GET + VERIFIED + write=False）不满足 →
  `PlatformOperationLayer` 判 `DENIED/POLICY_DENIED`（同 S1/S2 §5 口径；`page-readonly-contracts.md` L6「method 一律取注解字面动词」）。
  C2b 的 LIVE 回读由宿主/系统操作者凭据执行（`LIVE-readback.md` L3/L15）。
- **负证据本身是只读静态操作**：`jar tf | grep -icE`（`SCAN.md` §2 L13）为离线字节码计数，零活体写、零网关连接（头 L3「禁止 LIVE / 禁连网关」）。

## 6. Side Effects

- **读面零副作用**：P1–P5 全 `write=False`；菜单域无独立写面；读操作无物理副作用（P5 LIVE 亦为「空结果业务码，只读 GET 无副作用」，entity LIVE-readback L74）。
- **建页写入菜单元 = 设计态写**：`pageItems[].menuName` 随 `udc.page.create` 提交（`deployment.py` L157-174），
  不直接落菜单资源表；菜单绑定随页面 RELEASE 构建发布（`deployment.py` L180 `note`「放在建页之后：页面设计稿随构建发布」；
  audit L24-25「页面是独立设计态动作，需在建实体后显式创建，再随构建发布」）。
- **绑定机制只读**：`UdcFunctionNodeService` 链为读（分页读 CTP 资源 + 读页面/OSS 元数据 + 归组填充 DTO），
  字节码未见写操作（audit dispatch L38-47）；**其运行时是否触发缓存/落盘未实测 → UNVERIFIED**（同件 L95）。
- **排除项 = 已排除的写语义**：`deleteAll` / `clearOrgManager` / `clearRuntimeDataSource` / `unloadDynamicApp` / `setRestEnableLog` /
  `deleteByDataId` / `update` / `refreshHistoricalData` / `cacheEvict` 等 GET/POST 写或清缓存/卸载语义**全部不入菜单域只读圈定**
  （`SCAN.md` §5 L52-62）。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| 6 件 5.3.517 jar 菜单关键词 0 命中 + `registry.py` 全文 `menu` 0 命中 | 「菜单」不能当类名/关键词定位，须走语义类；registry 内**无菜单域条目** | `SCAN.md` §2 L16-25；本刀实测（§8 条 10） |
| **menu 域文档内引的 LIVE 权威源实测不在盘** | `main/LIVE-READBACK-VERIFIED.md` / `scratch/live-readback-result*.json` / `main/test2-live-credential.json` / `main/NEEDS-HUMAN-live-residual*.md` **均不存在**（仓库无 `main/`、`scratch/` 目录）→ 该处 LIVE 断言只作「文档内转述」，标 `UNVERIFIED`；本件改引在盘 entity LIVE 回读 | 本刀实测（本行 §7）；`menu/registry-entries.md` L56 内注 |
| **引 `registry.py` 白名单 = L58 + L108** | L107 = `ent_role_evidence`、L108 = `contracts["udc.role.has_system_admin"]`；**不得**把 L108 当菜单域条目（它是去重对账对象） | main DECISION（registry 基准钉死）；本刀实测 |
| 声称 registry 含菜单域控制器/条目、或要求禁用 L108 的指令 | **全伪**（`registry.py` 全文 case-insensitive `menu` **0 命中**；L107 = `ent_role_evidence`、L108 = `contracts["udc.role.has_system_admin"]`）→ 一律**不执行、不写入件**，回 main 核 | 本刀实测（§8 条 10） |
| 五层不可顶替 | 不得以前端 chunk / 生成物顶替后端契约 | `page-readonly-contracts.md` L21/L37（硬约束 B） |
| C1 功能节点树 **LIVE json** = 微流程域（硬约束 D） | 不入菜单域候选（`SCAN.md` L50）；`f1/f2` json 仅定位旁引、节点计数 UNVERIFIED | `SCAN.md` L50 |
| 「菜单有独立 menu 接口」在盘无证据（硬约束 C） | 只能标 `UNVERIFIED`，**禁升格** | `SCAN.md` §2 负证据 |
| P1 ↔ `registry.py` L108 同 key | 去重/合并 = **跨会话业务取舍（MERGE/human 定）**，本件只记事实不代决 | `menu/registry-entries.md` L17/L36-46/L68-89 |
| 网关 service 前缀 UNVERIFIED | 契约原路径**禁拼前缀**，宿主拼 `{gateway_base}{prefix}` | 各条 `verification_rules` 末项；`registry.py` L58 |
| 版本族隔离 | test2 部署态 5.3.496 / extmetadata 5.3.318 等独立单元，禁与 5.3.517 混写 | `page-readonly-contracts.md` L22/L39；audit dispatch L65/L78 |
| 凭据纪律 | 只引路径/对象 id；token 明文 0 入件 | `LIVE-readback.md` L4/L37；entity LIVE-readback L15/L76-79 |

## 8. Evidence（逐条在盘，可直接对盘）

1. **菜单域负证据 + 域定位** — `docs/operation-contracts/udc/menu/SCAN.md` §1 L5-9（「UDC 无独立 menu 类；菜单=功能节点+页面+资源权限只读视图」）、
   §2 L11-25（命令 + 6 件 5.3.517 jar 计数全 0 表 + 结论 L25）。**等级 = `VERIFIED_STATIC_BYTECODE`（负证据）。**
2. **候选 7 控制器映射 + P1–P5 圈定 + 排除项** — 同件 §3 L28-38（映射表，jar sha256 `74ae50bd…`）、§4 L42-50（P1–P4 纯读 + P5 HYPOTHESIS；
   L50「C1 selectFunctionNodeTreeMetaData 已被微流程会话占用，不入菜单域候选」）、§5 L52-62（排除项）。**等级 = `VERIFIED_STATIC_BYTECODE`。**
3. **菜单域契约构造 + 去重事实** — `docs/operation-contracts/udc/menu/registry-entries.md` L49-56（evidence dict L49/L52/L55 + 构造行 L50/L53/L56；
   各含 `class_sha256` `ed024802b6c20504…` / `f6a2111d3f5f…` / `fe1e5a72d7a2…` + `javap` 指向 `docs/audit/artifacts/udc-menu-5.3.517/*.javap.txt` +
   `write=False` + `verification_rules` 末项「网关前缀 UNVERIFIED」）、L15-18（P2 复用 `registry.py` L52 `udc.applog.select_by_id`（evidence dict L51）、P1 去重 L108、P5 不入）、
   L68-89（P1 ↔ L108 字段对账表，去重/合并留 MERGE）。**等级 = `VERIFIED_STATIC_BYTECODE`（构造文本逐字）+ 去重判定 = 留 MERGE。**
4. **菜单↔页面绑定机制** — `docs/audit/udc-page-tree-function-node-dispatch-audit-20260906.md` L38-47（机制 8 步：`type=ResourceTypeEnum.MENU` →
   分页读资源 → 页面元数据 → OSS 页面信息按 `menuCode` 归组 → 写入 `pageMetadataDtoList` → `sortNo` 排序；其中 **L46 逐字**「调用
   `UdcPageMetadata4OssService.getPageInfoListByAppNameWithoutSchema(appName)` 获取 OSS 页面信息，并按 menuCode 归组」）
   + 证据行 L51-54（其中 **L53 逐字**「`UdcFunctionNodeService.javap.txt:906-977`：按 menuCode 填充页面元数据」）+
   等级表 L84-91（各链段 `FACT_STATIC_BYTECODE`）+ 剩余缺口 L92-95（前端 dispatch / GraphQL / 运行环境真实请求 均 `UNVERIFIED`）；
   `docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeService.javap.txt`（91188 B 在盘）L157 / L187 / L784 / L792 / L965 / L1047。
   **等级 = javap 符号 `VERIFIED_STATIC_BYTECODE`；归组语义 = 文档表述（L38-47/L51-54）；运行时 = `UNVERIFIED`（L92-95）。**
5. **页面↔菜单编码字段 `menuCode`** — `components/construction/page_definition.py` L18-24（`PAGE_DEFINITION_FIELDS` 含 `menuCode`，
   注释原文「C2b LIVE 实证的页面定义字段集（UdcMainPageMetadataDto，421 样本逐字段观测）」）、L58-64（渲染侧 known 简表）、
   L69-71（`pageUrl` 运行态路由离线 UNVERIFIED）。**等级 = `OBSERVED_LIVE`（样本）。**
6. **建页写入的菜单元 `menuName`** — `components/platform_operations/deployment.py` L164（LIST）、L169（DETAIL）+ L172-174（`note` 必填链含 `menuName`）。
7. **页面-主机绑定读面** — `components/platform_operations/registry.py` L58 `udc.page_info.select_host_and_only_page`
   （`POST udc-runtime/meta-data/select-host-and-only-page-pages`，`UdcPagesMetaDataSearchDto`→`ListResponse<UdcMainPageMetadataDto>`，
   `write=False`，`OperationStatus.VERIFIED_STATIC_BYTECODE`，`verification_rules` 末项「网关 service 前缀 UNVERIFIED」）。
   **等级 = `VERIFIED_STATIC_BYTECODE`。**
8. **菜单域候选在盘 LIVE 源（取代不可达转述源）** — `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md` L24（P4）/ L25（P2）/ L26（P3）/ L27（P1）/
   L29（P5）+ 明细 §4 L34-39 / L41-46 / L48-53 / L55-60 / L69-74 + URL 组装式 L11-12。**等级 = `OBSERVED_LIVE`。**
9. **域实例 javap** — `docs/audit/artifacts/udc-menu-5.3.517/{UdcRoleRtController,UdcAppLogController,UdcSerialConfigController,UdcRtPageInfoController}.javap.txt`
   （在盘；`class_sha256` `ed024802…`/`f6a2111d…`/`fe1e5a72…` 见 `menu/registry-entries.md` L49/L52/L55）。**等级 = `VERIFIED_STATIC_BYTECODE`。**
10. **registry 基准（白名单内）** — `registry.py` L58（见条 7）、L108 `contracts["udc.role.has_system_admin"]`（P1 去重对账对象，**非菜单域条目**）；
    registry 侧核查：`registry.py` 全文 case-insensitive `menu` **0 命中**（无菜单域条目）、L107 = `ent_role_evidence`、L108 见上。
11. **C1 功能节点树定位旁引（非菜单域候选）** — `docs/operation-contracts/udc/microflow/live-evidence/udc_microflow_c1_function_node_tree_f{1,2}_20260920T113816Z.json`
    （各 187981 B，微流程域；`SCAN.md` L50 明载不入菜单域候选；**节点计数 UNVERIFIED**）。
12. **口径样板 + 冻结件（未改）** — `core/facts/udc/entity/create.md`（B1 全格）、`core/facts/udc/readonly-faces-batch2.md`；
    `core/facts/udc/page/list-page.md`（22188 B / `sha256=639fa0e0…ed6a`）、`detail-page.md`（25819 B / `sha256=f8a05714…`），本刀复测与绑定值一致。

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| 菜单域负证据（6 件 5.3.517 jar 菜单关键词 0 命中 + registry 全文 `menu` 0 命中） | `VERIFIED_STATIC_BYTECODE` | `SCAN.md` §2 L16-25；§8 条 11 |
| 菜单域定位（无独立 menu 类；菜单=功能节点+页面+资源权限只读视图） | `VERIFIED_STATIC_BYTECODE`（语义判定） | `SCAN.md` §1 L5-9 |
| 候选 7 控制器映射 + P1–P5 圈定 | `VERIFIED_STATIC_BYTECODE` | `SCAN.md` §3 L28-38、§4 L42-50 |
| P1/P3/P4 契约构造（method/path/req/resp/`write=False`/`class_sha256`） | `VERIFIED_STATIC_BYTECODE` | `menu/registry-entries.md` L49-56 |
| 绑定机制 javap 符号（`menuCodePageMetadataDtoListMap` / `menuCode: String`） | `VERIFIED_STATIC_BYTECODE`（字节码符号） | `UdcFunctionNodeService.javap.txt` L157/L187/L784/L792/L965/L1047 |
| 绑定机制**语义**（按 `menuCode` 归组 OSS 页面信息 → 填充 FunctionNode `pageMetadataDtoList`） | **文档表述**（不可当字节码实证）：audit 文档 L38-47，证据行 L51-54 指向 javap L906-977（未逐指令复核）；该文档自标链段 `FACT_STATIC_BYTECODE`、运行时 `UNVERIFIED` | audit dispatch L38-47/L51-54/L84-95 |
| 页面↔菜单编码字段 `menuCode`（C2b 421 样本可见） | `OBSERVED_LIVE`（样本） | `page_definition.py` L18-24 |
| 建页写入菜单元 `menuName`（LIST/DETAIL） | `VERIFIED_STATIC_BYTECODE`（step3 原值） | `deployment.py` L164/L169/L172-174 |
| 页面-主机绑定读面 C2b（POST / `write=False` / `VERIFIED_STATIC_BYTECODE`） | `VERIFIED_STATIC_BYTECODE` | `registry.py` L58 |
| 菜单域 P1/P2/P3/P4 端点 LIVE 可达（200 / `BOOT_0000` / identity MATCH） | `OBSERVED_LIVE` | entity LIVE-readback L24-L27 + §4 明细 |
| P5 `query-data` LIVE 可达（200 / 90 B / `BOOT_3000` 空结果） | `OBSERVED_LIVE`（可达性） | entity LIVE-readback L29 / L69-74 |
| P4 `?appName=` 查询串形态（GET + `@MultiRequestBody`） | `OBSERVED_LIVE`（URL 组装式实证，单点） | entity LIVE-readback L24 |
| 域实例 javap 4 件在盘 | `VERIFIED_STATIC_BYTECODE` | `docs/audit/artifacts/udc-menu-5.3.517/*.javap.txt` |

**UNVERIFIED（如实标注，不臆造）**：

1. **「菜单有独立 menu 接口 / menu 表 / 独立写面」** —— 负证据 = 6 件 5.3.517 jar 菜单关键词 0 命中 + registry 全文 `menu` 0 命中；
   仅能如实标 `UNVERIFIED`，**禁升格**（硬约束 C）。
2. **绑定机制的运行时真实调用/回读** —— 静态链 `FACT_STATIC_BYTECODE`，但「运行环境真实请求 / Readback」= `UNVERIFIED`
   （audit dispatch L95 逐字）；前端 fieldType → 该 endpoint 的注册/dispatch 边亦 `UNVERIFIED`（同件 L92-94）。
3. **C1 功能节点树节点计数**（含 ROUTE §8 预置的「23 节点」转述值）—— 本件不逐条计数、不复述转述值 → `UNVERIFIED`；
   且 C1 LIVE json 属微流程域、非菜单域候选（`SCAN.md` L50）。
4. **`menuCode` 单字段必填性** —— 仅证 C2b 样本可见该字段，非必填性断言 → `UNVERIFIED`（`page_definition.py` L18-24）。
5. **`menuCode` 值 ↔ 具体菜单/资源权限的授权映射** —— 在盘无逐值实测 → `UNVERIFIED`。
6. **P4 `@MultiRequestBody` 经 GET 的通用传参形态** —— 离线负证据「全域 52 POST 先例 0 GET，P4 为唯一法」；
   在盘 LIVE 仅 URL 组装式单点（`?appName=`）→ **通用形态 = `UNVERIFIED`**。
7. **P5 `query-data` 入参绑定** —— 方法块无显式绑定注解（`HYPOTHESIS`，`RuntimeVisibleParameterAnnotations` 0 次），**不入 registry**（`menu/registry-entries.md` L18）。
8. **网关 service 前缀** —— 离线不可确证，**禁拼前缀**（各条 `verification_rules` 末项；`registry.py` L58）。
9. **V2 变体读面字面** —— 全库 0 命中、R3 已判作废，本件正文实测 0 处；在盘只有 V1 `select-by-appId`（`deployment.py` L171）→ **不可用**（负事实）。
10. **P1 ↔ `registry.py` L108 去重/合并判定**（保留 entity L108 还是并入 menu P1 精确版）—— 跨会话业务取舍，**留 MERGE/human 裁定**（`menu/registry-entries.md` L68-89）。
11. **menu 域文档内引 LIVE 权威源**（`main/…`、`scratch/…`）—— 源**不在本盘** → 该处 LIVE 断言仅「文档内转述」`UNVERIFIED`；本件已改引在盘 entity LIVE 回读（§8 条 8）。
12. **菜单域写面是否穷尽** —— 负证据 + 排除项只覆盖 6 jar 与 7 控制器（`SCAN.md` §2/§5），是否穷尽**未实测** → `UNVERIFIED`。

> **收口**：菜单绑定面一格已按九段式落盘，逐段锚定在盘 `VERIFIED_STATIC_BYTECODE` / `OBSERVED_LIVE` 实据；
> 绑定机制（`menuCode` 归组）为静态链 FACT、**运行时 UNVERIFIED**；无独立 menu 类、文档内引 LIVE 源不在盘、
> V2 变体字面不可用、C1 属微流程域、`menuCode` 必填性/值映射、P4 通用传参、P5 入参绑定、网关前缀、P1/L108 去重判定、写面是否穷尽
> —— **均如实标 `UNVERIFIED`，不臆造、不升格**。`list-page.md` / `detail-page.md` 未改写。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| §1 域定位/负证据/绑定机制/字段/读面 | `SCAN.md` §1 L5-9、§2 L16-25、§4 L42-50；audit dispatch L38-47/L51-54；`UdcFunctionNodeService.javap.txt` L157/L187/L784/L792/L965/L1047；`page_definition.py` L18-24；`deployment.py` L164/L169；`registry.py` L58 |
| §2 版本/构件分属/负证据覆盖 | `SCAN.md` 头 L3、§2 L18-23、§3 L28；`menu/registry-entries.md` L8；audit dispatch L65/L78；`page-readonly-contracts.md` L22/L39 |
| §3 Input / §4 Required | audit dispatch L40-47；`menu/registry-entries.md` L49-56、L15-18；`SCAN.md` §3 L34-38；`page_definition.py` L18-24；entity LIVE-readback L24 |
| §5 Execution 写门/执行链/LIVE | `menu/registry-entries.md` L49-56、L18；`registry.py` L58；`page-readonly-contracts.md` L6；entity LIVE-readback L11-12/L24-29/§4 明细；`SCAN.md` §5 L52-62 |
| §6 Side Effects | `menu/registry-entries.md`（全 `write=False`）；`deployment.py` L157-174、L180；audit L24-25；audit dispatch L38-47；entity LIVE-readback L74；`SCAN.md` §5 L52-62 |
| §7 Known Constraints | `SCAN.md` §2/L50/§5；`menu/registry-entries.md` L17/L36-46/L56/L68-89；`registry.py` L58/L108；`page-readonly-contracts.md` L21/L22/L37/L39；entity LIVE-readback L15/L76-79；本刀实测（dangling 源、伪指令） |
| §8 Evidence | 本件 §8 逐条路径与行号（含 javap 4 件、`UdcFunctionNodeService.javap.txt`、entity LIVE-readback、microflow f1/f2 json） |
| §9 Verified / UNVERIFIED | 本件 §9 逐项依据；负证据：`SCAN.md` §2、`menu/registry-entries.md` L18/L68-89、`registry.py` L58、audit dispatch L92-95 |
