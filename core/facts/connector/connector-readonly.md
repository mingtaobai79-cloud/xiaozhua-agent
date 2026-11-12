# connector.connector-readonly｜集成连接器/数据流 只读事实格（九段式 · 阶段 2）

> 任务：`core/facts` 三 stub 之二 **connector（集成连接器）** 推进为有证据的九段式只读格。
> 仓库 `<XIAOZHUA_AGENT_ROOT>`，写前实测 HEAD `dc12ef3d16a292116128ddc110c5cb1cd1cb4e8d`。
> 只读、0 写请求；凭据 0 入件（仅键名/长度/时效声明）；证据分级 STATIC_CONTRACT < VERIFIED_STATIC_BYTECODE < LIVE；
> 无 LIVE 接口如实标 UNVERIFIED，**不编**。本批经 REWORK（E6）坐实真实 connector 接口 LIVE：`data-flow-map/search` LIVE=PASS（非空+traceId）；
> **阶段 4（E7）A 域剩余 5 只读路由已逐路由 LIVE 单发**：网关可达（200+traceId+类型化信封）但业务 `data` 空 ⇒ 逐路由维持 UNVERIFIED、不冒充 PASS（增量坐实 `search-original` 需 `dataFlowId`+`sourceEntityId`、`init-data` 需 `sourceEntity`）；B 域 `udc/microflow` 仍 UNVERIFIED；控制端点 `meta-data` LIVE=PASS（不同域）。

---

## 1. Capability（能力面）
"集成连接器 / 微流程 connector" 的**只读**事实面 = 两套字节码坐实的读面：
- **A. 运行态数据流（DataFlow）只读面**（`com.seeyon.boot.starter.dataflow`，`udc-starter-dataflow-5.3.517`）——
  即 HANDOFF 指向的 `POST /udc-runtime/*` connector 相关接口：微流程连接器运行态"映射/初始化"的查询读面。
  3 控制器共 6 读路由：
  | 控制器 | 路由（方法 基路径/子路径） | AppService |
  |---|---|---|
  | `DataFlowRtMapController` | POST `udc-runtime/data-flow-map/search` | `DataFlowMapAppService.selectByCondition` |
  | `DataFlowRtMapController` | GET  `udc-runtime/data-flow-map/{id}` | `DataFlowMapAppService.selectById` **（E8 LIVE=PASS，`{id}`=数值记录 id）** |
  | `DataFlowRtMappingController` | POST `udc-runtime/data-flow-mapping/search-original` | `DataFlowMappingAppService.selectOriginalMappingList` |
  | `DataFlowRtMappingController` | GET  `udc-runtime/data-flow-mapping/{id}` | `DataFlowMappingAppService.selectById` |
  | `DataFlowRtMappingController` | POST `udc-runtime/data-flow-mapping/init-data` | `DataFlowMappingAppService.selectMappingInitData` |
  | `DataFlowRtMappingController` | POST `udc-runtime/data-flow-mapping/detail` | `DataFlowMappingAppService.selectDetailByCondition` |
  （同 jar 另有 **写**路由 `.../data-flow-mapping/update`、`.../state` 与 `DataFlowForBpmController` 的
  POST `udc-runtime/bpm/fill-data`（`fillErrorFlowData`）——均属**写**面，**不入本只读格**。）
- **B. 设计态连接器枚举面**（`com.seeyon.udc.controller.MicroFlowController`，`udc-web-5.3.517`，部署件
  `udc-assemble-5.3.517-deployed`）：`findCallConnectorAppService` → GET
  `udc/microflow/select-call-connector-app-service/{appId}`（`@RequestMapping udc/microflow`，
  `@HasRole udcAppDesigner/udcSystemAdmin`，接口注 `@Deprecated`，RestApiOperation "6.6 获取微流程中使用的所有连接器信息"，
  返回 `SingleResponse<Map<String,List<String>>>`）。接口另有 `findCallIntegrationAppService`（返回
  `MicroFlowIntegrationAppInfoDto`）——**仅接口方法、无暴露 REST 路由**（本控制器未映射它）。
  B 属设计态（`udc/microflow` 非 `/udc-runtime/*`），环境事实（§7）载 `GET /udc/* 实测 404`，
  且本批活体网关 TLS 中断、**路由级 404 不可判定**，故 B 只登记 STATIC/字节码层，**不声称 LIVE**。

## 2. Version（版本 / 在盘源码）
- 运行态数据流：`udc-starter-dataflow-5.3.517`（`com.seeyon.boot.starter.dataflow.controller.*`）。
- 设计态连接器：`udc-web-5.3.517` / 部署件 `udc-assemble-5.3.517-deployed`（`com.seeyon.udc.controller.MicroFlowController`）。
- 接口：`udc-facade-5.3.517` → `com.seeyon.udc.api.MicroFlowInfoAppService`
  （`findCallConnectorAppService` @Deprecated / `findCallIntegrationAppService`）。
- 活体目标：test2（`https://lowcode-test2.example.com`，app `app9000000000000000001`，
  网关前缀 `/service/app9000000000000000001`，数字 appId `3289082814923688017`）。
- 字节码/CFR 双源原件（VERBATIM 复制入 evidence/bytecode/，sha256 与原件相等，见 §8）：
  `MicroFlowReadPlane.javap.txt`（`udc-assemble-5.3.517-deployed`，含 MicroFlowController 全量）、
  `udc-facade-5.3.517-MicroFlowInfoAppService.java`（CFR 反编译接口）、
  `DataFlowRtMapController.javap.txt`、`DataFlowRtMappingController.javap.txt`、`DataFlowForBpmController.javap.txt`
  （均 `docs/audit/artifacts/udc-flow-5.3.517/`）。

## 3. Input（入参）
- A（数据流只读）：
  - `POST .../data-flow-map/search`：`DataFlowRtMapQueryDto`（条件查询，body）。
  - `GET .../data-flow-map/{id}`：路径 `id`（`Long`，`@PathVariable id`）。
  - `POST .../data-flow-mapping/search-original`：`OriginalDataFlowMappingListQueryDto`（字段 javap 在盘：`dataFlowId`、`sourceEntityId`、`targetEntityId`、`caption`；活体坐实 `dataFlowId`+`sourceEntityId` 必填，见 §8 E7）。
  - `GET .../data-flow-mapping/{id}`：路径 `id`（`Long`；活体判 E6 guid 非此 `id` 键，见 §8 E7 `id_key_semantics`）。
  - `POST .../data-flow-mapping/init-data`：`DataFlowMappingInitQueryDto`（`com.seeyon.udc.common.dto`；字段 javap 在盘：`sourceEntity`/`targetEntity`（`EntityInitParam{appId,appName,entityFullName}`）；活体坐实 `sourceEntity` 必填，见 §8 E7）。
  - `POST .../data-flow-mapping/detail`：`DataFlowOriginalMappingQueryDto`（字段 javap 在盘：`appId`、`guid`、`terminalType`、`convertDetailDto`、`transferListSchema`、`convertEntityInfo`；见 §8 E7）。
- **入参 DTO 字段清单**：3 个 mapping 侧 DTO（`OriginalDataFlowMappingListQueryDto`/`DataFlowMappingInitQueryDto`/`DataFlowOriginalMappingQueryDto`）已于阶段 4 经 javap 落 `evidence/bytecode/`（见 §8 E7-DTO），字段类型确定；`@NotNull` 类注解不在字段表内，具体必填以活体 BOOT_1001 逐条坐实（不外推）。

## 4. Required（前置 / 鉴权）
- 走 test2 网关（`config/environments.yaml::environments.test2.credential`，`test2-web-credential`，只读 scope；值 0 入件）。
- Cookie 由 `make_cookie_headers_resolver` 现渲染（`sy_access_token`/`tk_exp`/`sy_uid` 三占位），仅 on-wire、不持久化。
- A 运行态读面：网关 cookie 鉴权（同 §item-mgmt 的 `POST /udc-runtime/*` 鉴权面）。
- **真实返回结构（E8 LIVE 坐实，`GET data-flow-map/{数值记录id}`）**：网关信封 `{status,code=BOOT_0000,message=SUCCESS,traceId,data}`；`data = {content: {validate, id, guid, appId, caption, definition, description, state, createTime, updateTime}}`——**单对象**（非 E6 search 的列表），`definition` 可为 null；鉴权 cookie 命中记录即返回全字段。
- B 设计态：`@HasRole udcAppDesigner` / `udcSystemAdmin`（bytecode 注解坐实）——需设计态角色，**非**运行态数据面。

## 5. Execution（执行链，字节码坐实）
- A：`DataFlowRtMap(RtMapping)Controller.{method}` → `SingleRequest.from(dto|id)` →
  `DataFlowMap(App)Service.selectByCondition/selectById/selectOriginalMappingList/selectMappingInitData/selectDetailByCondition`
  → `SingleResponse/ListResponse<...Dto>`。返回体经网关包 `{status,code,message,traceId,data}`（与 item-mgmt LIVE 件同壳）。
- B：`MicroFlowController.findCallConnectorAppService(Long)` → `SingleRequest.from(appId)` →
  `MicroFlowInfoAppService.findCallConnectorAppService` → `Map<String,List<String>>`（appService→方法 的连接器调用信息）。
- 只读：本轮 0 写；`update`/`state`/`bpm/fill-data` 三写路由**未调用**。

## 6. Side Effects（副作用）
- 只读探测：无落库副作用（数据流"映射查询/初始化"读语义）；仅网关鉴权会话消耗。
- 显式**不触发**写：`data-flow-mapping/update`（改映射）、`/state`（改映射状态）、`udc-runtime/bpm/fill-data`
  （`fillErrorFlowData` 写错误流数据）均只登记、不发送。

## 7. Known Constraints（已知约束 / 边界）
- **LIVE 本批不可达成 = 网关 TLS 中断（环境阻塞，非 404/无路由）**：本轮 3 发 connector LIVE（2 POST 数据流 + 1 GET 设计态）
  全 `transport=unavailable`（`SSL: UNEXPECTED_EOF_WHILE_READING`，HTTP 状态 null、0 字节、traceId 无）；
  且**上一阶段已坐实 LIVE 的控制端点** `GET udc-runtime/meta-data/select-function-node-tree/{app}`（item-mgmt evidence send#1，
  09-29 12:48 曾 200/BOOT_0000）在 14:02 复测**同样 TLS 失败** → 判为 test2 网关 TLS 层瞬时中断，非 connector 路由不存在。
  故按"无 LIVE 接口如实标 UNVERIFIED、不编 404"，A/B 全部接口本轮 **LIVE=UNVERIFIED**。
  **main 14:17 只读探针实测**：裸 TLS 握手已 HANDSHAKE_OK（较 14:02 全失败有变化），但 HTTP 层请求仍 `UNEXPECTED_EOF`
  → 判**传输层瞬时抖动**（非路由缺失）；据此按 main 指令**立即重发一次（14:26，含控制端点共 4 发，0 写）**：
  控制 `node-tree` + `data-flow-map/search` + `data-flow-mapping/search-original` + 设计态连接器枚举，
  **4 发全 `transport=unavailable`（HTTP null/0 字节/无 traceId，`SSL: UNEXPECTED_EOF_WHILE_READING`）**——
  网关 TLS 仍未恢复 → **结果 B**：connector 冻结为 `VERIFIED_STATIC_BYTECODE`、`LIVE=UNVERIFIED`，
  如实标"网关 TLS 瞬时中断（环境），非路由缺失"，LIVE 收口登记为**带时间戳的后续独立 pass**（§9）。
  **（本轮 18:37 E5 已解除：main 18:32 实测 `HTTP_LAYER_UP` + 15:2x 人指解除冻结，控制端点单发 200/BOOT_0000 + 非空 + traceId，本约束闭环）**
- 环境事实（ROUTE/collaboration 记载）：`GET /udc/* 实测 404`（设计态 B 走 `/service/{app}/udc/*`，非运行态数据面）；
  活体只读面为 `POST /udc-runtime/*`（A 属之）。
- 无写路径授权；本轮 0 写请求；禁改 `components/ core/tools/ adapters/ tests/ xiaozhua_cli/ xiaozhua_host_bootstrap`。
- 入参 DTO 字段清单：本批未逐一落盘（javap 仅类型签名）→ 具体字段要求仍 UNVERIFIED，不外推、不臆造字段。
  **非空业务样本**：E6 已取到 `data-flow-map/search` 非空样本（901 B 数据流映射列表，见 §8 E6）；
  `data-flow-mapping/search-original` 本轮空结果，非空样本未取得（UNVERIFIED）。

## 8. Evidence（在盘证据；禁转述；字节码 VERBATIM + LIVE 尝试如实）
### E1 字节码（VERIFIED_STATIC_BYTECODE；sha256 与 `docs/audit` 原件逐位相等，复制入 `core/facts/connector/evidence/bytecode/`）
| 件 | 源 | 字节 | sha256 | 路由/方法锚 |
|---|---|---|---|---|
| `MicroFlowController-readplane.javap.txt` | `docs/audit/artifacts/udc-assemble-5.3.517-deployed/MicroFlowReadPlane.javap.txt` | 272344 B | `86848cb9fb757d5ad5ed49a30736d005a9298c38f0f95ea19211cea79e321b77` | L2328 `findCallConnectorAppService`；L529 `#403 select-call-connector-app-service/{appId}`；L528 "6.6获取微流程中使用的所有连接器信息"；L446 `#420 udc/microflow` |
| `MicroFlowInfoAppService.cfr.java` | `docs/audit/modules/decompiled/udc-facade-5.3.517-MicroFlowInfoAppService.java` | 782 B | `50a8ab7273fef8ea5d14b8663d1ff6e7251de0a129eedaed09d437fa17582979` | L19 `findCallConnectorAppService`(@Deprecated)；L21 `findCallIntegrationAppService` |
| `DataFlowRtMapController.javap.txt` | `docs/audit/artifacts/udc-flow-5.3.517/` 同名 | 11621 B | `28a27f3daae5f785da249ba5caeed26e8c5f8de308542b8444cac090b42654bd` | L61 `#49 udc-runtime/data-flow-map`；L127 POST `search`；L160 GET `{id}` |
| `DataFlowRtMappingController.javap.txt` | 同上 | 24210 B | `85ba145669783de4e4da7583c0948a1b1fb08de97f2728011260f96edada348e` | L91 `#79 udc-runtime/data-flow-mapping`；L161 POST `search-original`；L194 GET `{id}`；L233 POST `init-data`；L332 POST `detail` |
| `DataFlowForBpmController.javap.txt` | 同上 | 8816 B | `d0131b34824a6fbef58206a58826acd9b0d415ea2c96baec2aac53ee289148f9` | L48 `#36 udc-runtime/bpm`；L43 POST `fill-data`（**写**，仅登记） |

### E2 LIVE 只读尝试（本轮，网关 TLS 中断，如实记录，不冒充 PASS/404）
`core/facts/connector/evidence/live-probe-connector-readonly.json`（**2731 B**，sha256 `536c5c3cda8645bbfad88872e4c04515b519fc4e530a06b7466c758d5f3d2df8`）
| send# | 端点 | 方法 | HTTP | traceId | 结果 |
|---|---|---|---|---|---|
| 1 | `udc-runtime/data-flow-map/search` | POST | null(unavailable) | 无 | transport `SSL: UNEXPECTED_EOF_WHILE_READING` |
| 2 | `udc-runtime/data-flow-mapping/search-original` | POST | null(unavailable) | 无 | 同上 |
| 3 | `udc/microflow/select-call-connector-app-service/3289082814923688017` | GET | null(unavailable) | 无 | 同上（设计态+网关前缀，路由 404/无路由 不可判定） |
- `no_retry_bombing=true`（3 发封顶，不循环轰炸）；`nonempty=false`（未取到非空业务样本，如实标注，不冒充非空）。
- 凭据：键名/cookie 长度(67)/声明时效(`expires_gmt8 2026-09-28 19:40:14`，**声明过期但声明≠裁定**)入件，**值 0 入件**。

### E3 网关可达性诊断（判"环境中断"而非"路由无"的关键对照）
`core/facts/connector/evidence/live-unreachable-diag.json`（**544 B**，sha256 `602957a3f831d0f8534fbcdcad23658bdffa9aac319756ff266e8a7ef62cc660`）
- `dns_ip=10.0.0.1`、`tcp443=OPEN`、控制端点（item-mgmt send#1，上一阶段 LIVE）复测 `control_http=null / bytes=0`
  → `verdict=GATEWAY_TLS_UNREACHABLE(UNEXPECTED_EOF)`：DNS/TCP 通、TLS 握手层被网关掐断。
  这是**瞬时环境阻塞**，非 connector 路由 404/无路由；LIVE 复测须待网关 TLS 恢复（main 决策）。

### E4 LIVE 重发尝试（main 指令一次重发，14:26，0 写，凭据 0 入件）
`core/facts/connector/evidence/live-probe-connector-retry.json`（**3166 B**，sha256 `ccf88dc57412404157ddc89c795c46acdb05862961213ed53f80a6bdf7103d82`）
| tag | 端点 | 方法 | HTTP | traceId | 结果 |
|---|---|---|---|---|---|
| control-node-tree | `udc-runtime/meta-data/select-function-node-tree/{app}` | GET | null(unavailable) | 无 | transport `SSL: UNEXPECTED_EOF_WHILE_READING`（上一阶段 12:48 曾 LIVE 的控制端点，14:26 仍 TLS 失败 → 坐实网关层非路由层） |
| data-flow-map-search | `udc-runtime/data-flow-map/search` | POST | null(unavailable) | 无 | 同上 |
| data-flow-mapping-search-original | `udc-runtime/data-flow-mapping/search-original` | POST | null(unavailable) | 无 | 同上 |
| design-connector-enum | `udc/microflow/select-call-connector-app-service/3289082814923688017` | GET | null(unavailable) | 无 | 同上（设计态+网关前缀，路由 404/无路由 不可判定） |
- `no_retry_bombing=true`（E2+E4 两轮共 7 发，均单次收口、不循环轰炸）；`nonempty=false`（未取到非空业务样本，不冒充非空）。
- `outcome_rule`：任一发 nonempty+traceId ⇒ A（升级 LIVE）；全 UNEXPECTED_EOF/无 HTTP ⇒ **B（冻结 UNVERIFIED，本件即 B 证据）**。

### E5 LIVE 单发收口（main HANDOFF `phase2-connector-live-pass-1790677996`，18:37，0 写，凭据 0 入件）→ **结果 A（控制端点）**
`core/facts/connector/evidence/live-probe-connector-live-pass.json`（**1630 B**，sha256 `b471f820e861d117ae4673684bb0b5c5b3fdcd0ef67fb2a7632eca57b19d95b7`）
| tag | 端点 | 方法 | HTTP | code | traceId | 非空 | 结果 |
|---|---|---|---|---|---|---|---|
| node-tree-control | `udc-runtime/meta-data/select-function-node-tree/{app}` | GET | 200 | `BOOT_0000` | `3252469236123044028` | 是（205298 B） | **控制端点 LIVE PASS** |
- **等级如实界定（REWORK 修正）**：本 1 发是 **`meta-data` 控制端点**（与 item-mgmt 格 send#1 同端点、同壳、同网关/同 cookie 鉴权），
  坐实"test2 网关 HTTP 层可应答 + `udc-runtime/*` 只读面可达"。它**属 meta-data 控制面，**非**本格 A/B 域 connector 接口**（A 域 = `data-flow-map`/`data-flow-mapping`，B 域 = `udc/microflow`）——
  故**不得**据此宣称"A/B 域 connector 接口 LIVE=PASS"（那是过度声明）。控制端点 LIVE PASS ≠ connector 接口 LIVE PASS。
- A 域 6 读路由本轮**未逐路由单独发**（E5 单发约束仅发控制端点 1 发）⇒ **A/B 域 connector 接口本轮 LIVE=UNVERIFIED**，逐路由非空样本未取得，不冒充。
- `no_retry_bombing=true`（E2+E4+E5 三轮共 8 发，均单次收口）；凭据值 0 入件（仅键名 / cookie 长度 375 / 声明时效 `expires_epoch 1790595614`）。

### E6 本轮 A 域数据流单发（main REWORK HANDOFF `phase2-connector-livepass-rework-b-1790679753`，19:0x，0 写，凭据 0 入件）→ ① 真 connector 接口 LIVE=PASS
`core/facts/connector/evidence/live-probe-connector-dataflow.json`（**2342 B**，sha256 `f0c1fe480b0f1f90d05ba4ee5d583af4699421f90f112090f08a8a2332684290`）
| tag | 端点 | 方法 | HTTP | code | traceId | 非空 | 结果 |
|---|---|---|---|---|---|---|---|
| data-flow-map-search | `udc-runtime/data-flow-map/search` | POST | 200 | `BOOT_0000` | `3252497685650868412` | 是（901 B，映射列表含 合同复制/… 非空样本） | **LIVE=PASS（connector A 域接口）** |
| data-flow-mapping-search-original | `udc-runtime/data-flow-mapping/search-original` | POST | 200 | `BOOT_1001` | `3252497689257969852` | 否（124 B，空结果） | **UNVERIFIED（已调用但业务数据未验证）** |
- 判据：①`data-flow-map/search` 返回**真实非空业务体（901 B 数据流映射列表）+ 200/BOOT_0000 + traceId** ⇒ **该 connector 路由 LIVE=PASS**（connector 接口 LIVE 达成）。
- ②`data-flow-mapping/search-original` 空结果（`BOOT_1001`，data 空）⇒ **UNVERIFIED，不冒充 PASS**（已调用但业务数据未验证；min body `{}` 未臆造字段值）。
- B 域设计态 `udc/microflow` 本轮未发，保持 UNVERIFIED（环境 `GET /udc/*` 404）。
- `no_retry_bombing=true`（E6 新增 2 发，各 1 次）；凭据值 0 入件。

### E7 阶段 4 A 域剩余 5 只读路由逐路由 LIVE 单发（main HANDOFF `phase4-connector-aroute-live-closure-1790797756`，2026-10-01 03:55，0 写，凭据 0 入件）
`core/facts/connector/evidence/live-probe-connector-aroute-live.json`（sha256 `be70e8c71ad76c29f279de0c6c6150996e8a515b2355ec405b62856f9e148390`）
DTO 字段 javap 新增 3 件（`evidence/bytecode/`）：`OriginalDataFlowMappingListQueryDto.javap.txt`（803 B / `b0a929442591e3c2…`）、`DataFlowOriginalMappingQueryDto.javap.txt`（1175 B / `555a39f839449f11…`）、`DataFlowMappingInitQueryDto.javap.txt`（658 B / `14507ce332f45e5e…`）。
| tag | 端点 | 方法 | HTTP | code | traceId | 非空 | 结果 |
|---|---|---|---|---|---|---|---|
| route1 | `udc-runtime/data-flow-map/8128016104943011258`（E6 guid） | GET | 200 | `UDCRT_DATAFLOW_0005` | `3254480346657327292` | 否（136 B "diagram does not exist"） | **UNVERIFIED** |
| route2 | `udc-runtime/data-flow-mapping/search-original`（`{dataFlowId:8128016104943011258}`） | POST | 200 | `BOOT_1001` | `3254480556238309564` | 否（119 B "sourceEntityId must not be null"） | **UNVERIFIED** |
| route3 | `udc-runtime/data-flow-mapping/8128016104943011258`（min 探测，route2 未导出 id） | GET | 200 | `UDCRT_DATAFLOW_0008` | `3254480600647600316` | 否（143 B "mapping scheme does not exist"） | **UNVERIFIED** |
| route4 | `udc-runtime/data-flow-mapping/init-data`（`{}`，禁臆造 entity 全名） | POST | 200 | `BOOT_1001` | `3254480650996025532` | 否（117 B "sourceEntity must not be null"） | **UNVERIFIED** |
| route5 | `udc-runtime/data-flow-mapping/detail`（`{appId:3289082814923688017,guid:8128016104943011258}`） | POST | 200 | `UDCRT_DATAFLOW_0008` | `3254480734177462460` | 否（143 B "mapping scheme does not exist"） | **UNVERIFIED** |
- 网关本轮 **UP**（5 发全 200 + traceId，无 TLS EOF）；逐路由返回**类型化信封但 `data` 空**⇒ 判据"非空业务体+BOOT_0000"**未达成** ⇒ 逐路由 **LIVE=UNVERIFIED，不冒充 PASS**。
- **新增坐实（业务事实增量）**：`search-original` 除 `dataFlowId`（E6 已坐实）外 `sourceEntityId` 亦必填；`init-data` `sourceEntity` 必填。`data-flow-map/{id}` 与 `data-flow-mapping/{id}` 以 E6 guid 作 `{id}` 报 "does not exist" ⇒ 该路径 `{id}` 键为记录数值 id（E6 `id` 字段 `-1595651527290089449` 一类），非业务 guid；本轮无在盘可导出的合法 mapping `id` ⇒ 依 HANDOFF min 合法探测 1 发、如实记。
- `no_retry_bombing=true`（每路由 ≤1 发，共 5 发 ≤6 发上限）；0 写（`update`/`state`/`bpm/fill-data` 未调用）；凭据值 0 入件；既有 6 证据件 + 5 控制器字节码件未动（仅新增 E7 + 3 DTO javap）；B 域 `udc/microflow` 未探。

### E8 阶段 4 route1 正确键重探（main HANDOFF `evt-1790835845881-p4r1`，dedupe `phase4-route1-correct-key-reprobe-resend-1790900000`，2026-10-01 06:25 UTC，0 写，凭据 0 入件）→ **route1 LIVE=PASS**
`core/facts/connector/evidence/live-probe-connector-route1-correct-key.json`（**2699 B**，sha256 `819588e41ed9e9ff4d0c66f780d6374098aa108ae1e34dcbf9cc8b62a0bb6260`）
| tag | 端点 | 方法 | HTTP | code | traceId | 非空 | 结果 |
|---|---|---|---|---|---|---|---|
| route1-correct-key | `udc-runtime/data-flow-map/-1595651527290089449`（E6 在盘导出数值记录 id） | GET | 200 | `BOOT_0000` | `3255114172781824188` | 是（336 B，`data.content` 单记录：id `-1595651527290089449`、guid `8128016104943011258`、appId `3289082814923688017`、caption 合同复制、state ON、createTime/updateTime） | **LIVE=PASS** |
- **判据达成**：非空业务体 + 200/BOOT_0000 + traceId ⇒ **route1（`GET data-flow-map/{id}` → `DataFlowMapAppService.selectById`）升 LIVE=PASS**；首发达标 ⇒ 第二发（备选 id `-7296522931834678836`）预算**未用**，本批总发数 = **1**（≤2 上限，`no_retry_bombing` 成立）。
- 参数来源：`-1595651527290089449` **逐字取自 E6 `live-probe-connector-dataflow.json` 的 `data_preview`（在盘导出）**，0 臆造、0 越界枚举。
- **键语义坐实（区分 E7 失败因）**：同一路由 E7 以 guid `8128016104943011258` 作 `{id}` → `UDCRT_DATAFLOW_0005 does not exist`；本轮以 E6 数值记录 id 作 `{id}` → `BOOT_0000` + 真实记录 ⇒ **`{id}` 为数值记录 id（`selectById(java.lang.Long)`），键类型不符是 E7 空返回之因，非路由缺失、非记录不存在**。
- 边界：只写 `core/facts/connector/**`；E6 `f0c1fe48`、E7 `be70e8c7`、既有 6 证据件 + 5 控制器字节码逐字节未动（仅新增本件）；②③④⑤ 与 B 域未探；0 写；凭据值 0 入件（仅路径引用）。

## 9. Verified（逐接口证据分级；本轮结论）
- **A 运行态数据流只读面（`udc-runtime/data-flow-map`+`data-flow-mapping`，6 读路由）**：
  `VERIFIED_STATIC_BYTECODE`（§8 E1，3 javap VERBATIM 在盘）；**LIVE 分级按路由（E6 实测）**：
  - `POST data-flow-map/search`：**LIVE=PASS**（E6 单发 200/BOOT_0000 + 非空 901 B 数据流映射列表 + traceId `3252497685650868412`，**connector 接口 LIVE 达成**）。
  - `POST data-flow-mapping/search-original`：**UNVERIFIED**（E6 min `{}`→BOOT_1001 dataFlowId 必填；E7 带 `dataFlowId`=E6 guid→BOOT_1001 `sourceEntityId must not be null`，即再坐实一必填，data 空，非空样本未取得，不冒充 PASS）。
  - `GET data-flow-map/{id}`：**LIVE=PASS**（E8，2026-10-01 06:25 UTC 正确键重探：E6 在盘导出数值记录 id `-1595651527290089449` 作 `{id}` → 200/`BOOT_0000` + 非空 336 B（`data.content` 单记录，caption 合同复制，state ON）+ traceId `3255114172781824188`；E7 曾以 guid 误键 → `UDCRT_DATAFLOW_0005`，已由正确键翻正，键语义 = 数值记录 id 坐实）。
  - `GET data-flow-mapping/{id}`（E7 route3，min 探测）：**UNVERIFIED**（200/`UDCRT_DATAFLOW_0008` "mapping scheme does not exist" + traceId，data 空）。
  - `POST data-flow-mapping/init-data`（E7 route4，`{}`）：**UNVERIFIED**（200/`BOOT_1001` `sourceEntity must not be null` + traceId，坐实必填，data 空，禁臆造 entity 全名）。
  - `POST data-flow-mapping/detail`（E7 route5，`{appId,guid}` 均 E6 在盘导出）：**UNVERIFIED**（200/`UDCRT_DATAFLOW_0008` "mapping scheme does not exist" + traceId，data 空；guid 非 mapping-scheme 键）。
  - **E7 小结**：A 域 6 读路由现已 **6/6 逐路由 LIVE 单发**；唯 `data-flow-map/search`（E6）取得非空业务体 = LIVE=PASS；其余 5 路由网关可达（200+traceId+类型化信封）但业务 `data` 空 ⇒ **逐路由 LIVE=UNVERIFIED，不冒充**（无在盘可导出的合法 `{id}`/`sourceEntityId`/`entityFullName`，且无重试预算）。
  - **E8 修正（2026-10-01 route1 正确键重探）**：E7 route1 的 `{id}` 键类型误用（guid）已被纠正——E6 在盘 `data_preview` 即含数值记录 id，改用后 route1 = **LIVE=PASS**。A 域现 **PASS 2 / UNVERIFIED 4**（①search、`data-flow-map/{id}`；②search-original、③mapping/{id}、④init-data、⑤detail 仍 UNVERIFIED，缺口=值不在盘，见 §9 末）。route1 升 PASS 后，**剩余 4 条 UNVERIFIED 所需 `sourceEntityId`/mapping 数值 id/entityFullName 确不在盘**（补齐须跨模块实体/mapping 枚举 = 新边界，须 main 决策并向 human 报备）⇒ connector A 域**既有授权边界内**逐路由 LIVE 收口就此穷尽。
  - （E5 控制端点 `meta-data/select-function-node-tree` LIVE PASS 属**不同域**——meta-data 控制面，非 A 域 connector 接口；据此不得推"A 域全 LIVE"。）
- **B 设计态连接器枚举（`GET udc/microflow/select-call-connector-app-service/{appId}`）**：
  `VERIFIED_STATIC_BYTECODE`（MicroFlowReadPlane L2328/L529）；`findCallIntegrationAppService` 仅接口方法（无路由）；
  **LIVE = UNVERIFIED**（环境事实 `GET /udc/*` 404；main 18:32 探针"控制端点→404"同指此类 `/udc/*` 设计态路由，非运行态数据面，不编造）。
- **写面（`update`/`state`/`bpm/fill-data`）**：仅字节码登记，未调用、不在只读格内。
- **本阶段结论（演进）**：
  - 首版（13:59，E2）+ 重发（14:26，E4）→ 网关 TLS 中断，**结果 B**（冻结 `VERIFIED_STATIC_BYTECODE`/`LIVE=UNVERIFIED`）。
  - **E5（18:37 控制端点单发）→ 控制端点（meta-data 控制面）LIVE=PASS**：200/BOOT_0000 + 非空 205298 B + traceId `3252469236123044028`；**属 meta-data 控制面，非 A/B 域 connector 接口**，据此仅坐实"网关/`udc-runtime` 只读面可达"，**不推 A/B 域 connector 接口 LIVE**。
  - **E6（本轮 REWORK，A 域 2 路由单发）→ 真 connector 接口 LIVE 分级**：① `data-flow-map/search` **LIVE=PASS**（非空 901 B + traceId）；② `data-flow-mapping/search-original` **UNVERIFIED**（空结果）；其余 4 路由未单发仍 UNVERIFIED。
- **结果 B 注记关闭 + REWORK 收口**：14:30 冻结所引"网关 TLS 瞬时中断"待办 LIVE pass 已由 E5（控制端点）解除；本轮 E6 补真实 connector A 域接口 LIVE 分级。
  **诚实分级（REWORK 后）**：控制端点 LIVE=PASS（不同域）；A 域 `data-flow-map/search` LIVE=PASS（connector 接口）；A 域 `data-flow-mapping/search-original` + 其余 4 路由 + B 域 `udc/microflow` 均 UNVERIFIED（不冒充）。
- **阶段 4（E7，2026-10-01，main HANDOFF `phase4-connector-aroute-live-closure`）A 域剩余 5 路由逐发收口**：
  A 域 6 读路由现 **6/6 逐路由 LIVE 单发**（`no_retry_bombing`，每路由 ≤1 发）。**唯 `data-flow-map/search`（E6）= LIVE=PASS**；其余 5 路由本轮网关可达（全 HTTP 200 + traceId + 类型化信封 `UDCRT_DATAFLOW_0005/0008`、`BOOT_1001`）但业务 `data` 空 ⇒ **逐路由维持 LIVE=UNVERIFIED，不冒充 PASS**。
  增量坐实：`search-original` 必填 = `dataFlowId`+`sourceEntityId`；`init-data` 必填 = `sourceEntity`；`{id}` 路径键 = 记录数值 id（非业务 guid）。未取得非空样本之因 = 无在盘可导出的合法 mapping `id`/`sourceEntityId`/`entityFullName`（跨模块枚举越出本单边界），且无重试预算。
  **connector 接口 LIVE 达成面未扩张**（仍唯一 `data-flow-map/search`），但 A 域逐路由 LIVE 分级已完整坐实（PASS 1 / UNVERIFIED 5，附类型化错误码与必填面）。
- **阶段 4 续（E8，2026-10-01，main HANDOFF `evt-1790835845881-p4r1`）route1 正确键重探**：
  `GET udc-runtime/data-flow-map/{id}` 以 E6 在盘导出数值记录 id `-1595651527290089449` 单发命中真实业务记录（200/BOOT_0000 + 非空 336 B + traceId `3255114172781824188`）⇒ **route1 升 LIVE=PASS**；本批 1 发（第二发预算未用），0 写，凭据 0 入件，仅新增 E8 证据件。
  **A 域逐路由 LIVE 现 PASS 2（`data-flow-map/search` E6 + `data-flow-map/{id}` E8）/ UNVERIFIED 4**；②③④⑤ 维持 UNVERIFIED（缺 `sourceEntityId` 值 / mapping 数值 id / `sourceEntity` 值，均不在盘；补齐 = 跨模块枚举新边界，须 main 决策报备 human），**connector A 域既有边界内 LIVE 收口就此穷尽**。
- **本 HANDOFF 边界内 RESULT**：阶段 2 connector 格 REWORK 完成（E6 在盘，双源 = 字节码 5 件 VERBATIM + LIVE：控制端点 PASS + `data-flow-map/search` PASS + 空/未发 UNVERIFIED）；凭据 0 入件、0 写、no_retry_bombing（E2+E4+E5+E6 共 10 发，均单次收口）；
  **connector 接口 LIVE 达成（`data-flow-map/search` 非空 + traceId 实记），未发/空路由如实 UNVERIFIED**，请 main 派 auditor 复核 E6 + §8/§9 修正后收口（阶段 3 由 main 触发）。
