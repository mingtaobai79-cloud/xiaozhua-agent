# UDC 页面规则域 只读操作契约（page）

证据等级：VERIFIED_STATIC_BYTECODE（javap -p -v 全量输出 + class SHA-256，离线只读，未做 LIVE）。
artifact = udc-starter-runtime，version = 5.3.517（本地 Maven，<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar）。
路径纪律：控制器原路径 = 类级 @RequestMapping base + 方法注解 value，逐字取自 javap -v RuntimeVisibleAnnotations 字面值，**未拼任何网关前缀**（网关 service 前缀本地不可确证，标 UNVERIFIED）。
HTTP method 一律取注解字面动词（下列 4 条均为 @PostMapping，不按"读语义"改写）。写方法（create/update/delete/createBatch/deleteAll 等）不入契约。

## LIVE 回读状态（2026-09-19）

- 4 条 FACT（C1a/C1b/C2a/C2b）活体回读 = **LIVE PASS（已回读, 见 LIVE-readback.md, 判据 identity_matches 不变）**（C2a/C2b 真读回; C1a/C1b 空分页=读回面稳定, 非数据存在性证据）。**R22 s=-1 operator token 证据点**: human 23:47Z 刷新 operator 系统操作者 token 后新鲜重跑 4 端点, 逐端点终态 4/4 PASS（无鉴权失败）, 双发 md5 与 R20/R21 同值（同请求体同回读面, 区分靠凭据身份非 md5）; 详见 LIVE-readback.md/runtime.json（operator 态, per_endpoint_verdict 分列）。
- 11:43 刷新的 test2 只读 LIVE 凭据窗口 13:44:08 已关闭（`main/test2-web-credential.json`, `expires_epoch=1789796648`；仅引用路径，凭据明文 0 入本产物，禁止抄值）。
- human 08:16Z 指示：LIVE 暂缓，状态标「BLOCKED-等待新 token + UNVERIFIED」，**不阻塞离线部分**。
- 新 token 到位后 main 重建 ROUTE 重发 1 条 HANDOFF → 完成 C2b 枚举 → C2a identity → C1a/C1b 双发 identity 回读，届时产 `LIVE-readback.md` + `LIVE-readback-runtime.json` 并把本节升级为 **LIVE PASS**。
- C5/C6/C7/C8（HYPOTHESIS）维持原判定（HYP 未升级 FACT），同样 UNVERIFIED，随新 token 一并活体反查。

## UDC 元数据锚点规则对齐（human 084505）

**规则逐条落本域判定**：
- 规则①（meta-data 接口 = 平台首选读写面）：本域 C2a/C2b（`udc-runtime/meta-data/*`）为 meta-data 首选读面，已证，两条例 metadata_layer 判 FACT。
- 规则②（验收 = 回读元数据 identity_matches，HTTP 200/Boolean 不算证据）：C2a `check_exists` 返回 `ListResponse<Boolean>`，其 LIVE 回读条件已按本规则修订——判据改为「回读元数据 identity_matches」，Boolean/HTTP 200 仅作辅助信号，本身不构成验收证据。
- 规则③（设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis 缓存，5 层不可互相顶替）：各契约已逐条加 `metadata_layer` 标注行（本文件 7 要素 +1 项）；FACT 项 = 依据明确，HYPOTHESIS 项 = 如实标注未升级。
- 规则④（元数据结构随 UDC 大版本演进，按版本族隔离）：本证据**仅适用 5.3 族 5.3.517**（本地 Maven 构件），**禁跨版本推断**（test2 镜像 5.3.496 为独立证据单元，不可与 5.3.517 混写；相邻旧版本 5.3.345/349/358 更不可）。

**本域 metadata_layer 判定清单**（FACT/HYPOTHESIS 逐条）：

| 契约 | operation_id | metadata_layer | 判定 |
|---|---|---|---|
| C1a | udc.page_log.search | 运行态日志层（5 层中非 metadata 层） | FACT |
| C1b | udc.page_log.search_non_metadata | 运行态日志层（5 层中非 metadata 层） | FACT |
| C2a | udc.page_info.check_exists | 运行态元数据层 | FACT |
| C2b | udc.page_info.select_host_and_only_page | 运行态元数据层 | FACT |
| C5 | udc.page_general.get_cascade_default_value | 设计态配置层 | HYPOTHESIS（需 LIVE 反查数据来源） |
| C6 | udc.page_refer.select_tree | 实体参照数据层 | HYPOTHESIS（需 LIVE 反查确认） |
| C7 | udc.page_refer.select_by_id | 实体参照数据层 | HYPOTHESIS（需 LIVE 反查确认） |
| C8 | udc.page_refer.search_list_by_conditions | 实体参照数据层 | HYPOTHESIS（需 LIVE 反查确认） |

**5 层不可顶替声明**：设计态配置 / 运行态元数据 / 生成物 / 物理表 / Redis 缓存 五层各自独立，契约标注的 metadata_layer 仅声明本接口回读的数据源层，不得以「布尔结果 / HTTP 200 / 相邻版本 / 其他层」顶替；HYPOTHESIS 项（C5/C6/C7/C8）在 LIVE 反查确认数据源层前**不得升级 FACT**。

**版本族隔离声明**：本文件全部契约证据（bytecode SHA-256 / base / 方法 / DTO）绑定 `udc-starter-runtime` 5.3 族 5.3.517 单一构件；跨版本族（含 5.3.496 / 5.3.345-358）不得复用本判定。

---

## C1a udc.page_log.search

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_log.search` |
| HTTP method | `POST`（注解字面：@PostMapping value=["search"]） |
| 控制器原路径 | `udc-runtime/rt-page-log/search`（base `udc-runtime/rt-page-log` + `search`，逐字） |
| 参数形态 | `@RequestBody PageDtoRequest<UdcRtPageLogSearchDto> query`（javap Signature: `(Lcom/seeyon/boot/transport/PageDtoRequest<Lcom/seeyon/udc/common/dto/UdcRtPageLogSearchDto;>;)`） |
| 返回 DTO | `PageResponse<UdcRtPageLogSearchResultDto>`（Signature: `PageResponse<Lcom/seeyon/udc/common/dto/UdcRtPageLogSearchResultDto;>`） |
| evidence | artifact=udc-starter-runtime, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.controller.UdcRtPageLogController`, method=`search`, class_sha256=`86efc8a3b0924cb46f4d8ca11b527ba9129f3dd6d938e345c5cb11be15038c5e`（javap: docs/audit/artifacts/udc-page-5.3.517/UdcRtPageLogController.javap.txt） |
| metadata_layer | **运行态日志层（5 层中的非 metadata 层）— FACT**：UdcRtPageLog = 页面运行日志读回，属运行态数据/日志，**不是平台搭建生成的元数据载体**（不可顶替 meta-data 层）；依据明确（DTO=UdcRtPageLogSearchResultDto，运行日志语义） |
| LIVE 回读条件（本轮不做） | 需要：可访问 UDC 运行环境/网关（service 前缀 UNVERIFIED，需在线确证完整 URL）+ 合法登录态 + 一个存在页面日志数据的 UDC 应用；回读判据 = 同一 query 条件两次调用 identity_matches、PageResponse.data 为 UdcRtPageLogSearchResultDto 分页列表且 total 稳定。（LIVE PASS（已回读, 见 LIVE-readback.md, 判据 identity_matches 不变；C1a/C1b 空分页 total=0/content=[]=该 test2 应用当前无页面运行日志数据, 双发读回面稳定, **非数据存在性证据**） |

## C1b udc.page_log.search_non_metadata

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_log.search_non_metadata` |
| HTTP method | `POST`（注解字面：@PostMapping value=["search-non-metadata"]） |
| 控制器原路径 | `udc-runtime/rt-page-log/search-non-metadata`（逐字） |
| 参数形态 | `@RequestBody PageDtoRequest<UdcRtPageLogSearchDto> query` |
| 返回 DTO | `PageResponse<UdcRtPageLogSearchResultDto>` |
| evidence | artifact=udc-starter-runtime, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.controller.UdcRtPageLogController`, method=`searchNonMetadata`, class_sha256=`86efc8a3b0924cb46f4d8ca11b527ba9129f3dd6d938e345c5cb11be15038c5e` |
| metadata_layer | **运行态日志层（5 层中的非 metadata 层）— FACT**：同 C1a，UdcRtPageLog = 页面运行日志读回（searchNonMetadata 为同类方法的元数据差异面），属运行态数据/日志，**非平台搭建元数据权威层**；依据明确 |
| LIVE 回读条件（本轮不做） | 需要：同 C1a；判据 = 同一条件两次调用 identity_matches，且与 C1a 结果差异仅限元数据字段（方法语义差异待 LIVE 样本确认，此处仅记录所需条件，不做推断）。（LIVE PASS（已回读, 见 LIVE-readback.md, 判据 identity_matches 不变；同 C1a 空分页注记） |

## C2a udc.page_info.check_exists

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_info.check_exists` |
| HTTP method | `POST`（注解字面：@PostMapping value=["check-page-exists"]） |
| 控制器原路径 | `udc-runtime/meta-data/check-page-exists`（base `udc-runtime/meta-data` + `check-page-exists`，逐字） |
| 参数形态 | `@RequestBody List<UdcRtPageExistsDto> pageExistsDtoList`（javap Signature: `(Ljava/util/List<Lcom/seeyon/boot/starter/udcrt/dto/UdcRtPageExistsDto;>;)`，参数名取 LocalVariableTable `pageExistsDtoList`） |
| 返回 DTO | `ListResponse<Boolean>` |
| evidence | artifact=udc-starter-runtime, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController`, method=`checkPageExistsByConditions`, class_sha256=`7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02`（javap: docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt） |
| metadata_layer | **运行态元数据层 — FACT**：平台 meta-data 首选读面（human 084505 规则①点名），回读 = 页面存在性的运行态元数据 |
| LIVE 回读条件（本轮不做） | 需要：UDC 运行环境 + 登录态 + 已知存在/不存在的页面条件样本各一；**判据 = 回读元数据 identity_matches**（以 meta-data 接口回读该页面的运行态元数据并比对，规则②）；`check_exists` 返回的 `ListResponse<Boolean>` 与 HTTP 200 **仅作辅助信号，本身不构成验收证据**（HTTP 200/Boolean 不算证据）。（LIVE PASS（已回读, 见 LIVE-readback.md, 判据 identity_matches 不变；R21 精化=human 指定样本 pageUrl=hj + caption=函件(terminalType=PC), appName 取 C2b 枚举值, 已核实该样本存在于 C2b 非空枚举(非臆造), 真 ListResponse<Boolean> 读回 content=[true]） |

## C2b udc.page_info.select_host_and_only_page

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_info.select_host_and_only_page` |
| HTTP method | `POST`（注解字面：@PostMapping value=["select-host-and-only-page-pages"]） |
| 控制器原路径 | `udc-runtime/meta-data/select-host-and-only-page-pages`（逐字） |
| 参数形态 | `@RequestBody UdcPagesMetaDataSearchDto`（类型 `com.seeyon.boot.starter.extmetadata.dto.request.UdcPagesMetaDataSearchDto`，签名 `(Lcom/seeyon/boot/starter/extmetadata/dto/request/UdcPagesMetaDataSearchDto;)`） |
| 返回 DTO | `ListResponse<UdcMainPageMetadataDto>`（`com.seeyon.boot.starter.extmetadata.dto.UdcMainPageMetadataDto`） |
| evidence | artifact=udc-starter-runtime, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController`, method=`selectHostAppAndOnlyPageAppPages`, class_sha256=`7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02` |
| metadata_layer | **运行态元数据层 — FACT**：返回 `UdcMainPageMetadataDto` = 页面主元数据（平台搭建生成的运行态元数据载体，meta-data 首选读面，规则①） |
| LIVE 回读条件（本轮不做） | 需要：UDC 运行环境 + 登录态 + 一个主应用/仅页应用的 appName 样本；判据 = 同一 UdcPagesMetaDataSearchDto 两次调用 identity_matches，响应为 UdcMainPageMetadataDto 非空列表（或按条件返回空列表亦可自证）。（LIVE PASS（已回读, 见 LIVE-readback.md, 判据 identity_matches 不变；非空枚举 len=421） |

## C5（可选） udc.page_general.get_cascade_default_value — base UNRESOLVED-in-5.3.517（HYPOTHESIS 级）

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_general.get_cascade_default_value` |
| HTTP method | `GET`（注解字面：@GetMapping value=["{entityAppName}/{entityName}/{controlId}/get-cascade-default-value"]） |
| 控制器原路径 | **base = UNRESOLVED-in-5.3.517（HYPOTHESIS 级，不可升级 FACT）**：`UdcBaseGeneralController` 类级注解只有 `attributes: 1`（无自身 @RequestMapping，javap -v 验证），base 继承自 `com.seeyon.boot.starter.web.BaseComponentController`。**全库 537 jar 检索负证据**（docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md）: 该类仅命中 boot-starter-web 的 5.3.345/5.3.349/5.3.358 三个**相邻旧版本**（5.3.517 全 112 模块 0 命中），且 3 旧版本中 `BaseComponentController extends 抽象 BaseController`、类级注解 0 个、全文 0 处 @RequestMapping（父类结构 javap 已验），即继承链上**无任何类级 base 路径字面值可提取**；旧版本类信息禁止混写为 5.3.517 FACT（版本单元纪律）。方法 value 逐字 = `{entityAppName}/{entityName}/{controlId}/get-cascade-default-value`，完整路径 = `<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{controlId}/get-cascade-default-value` |
| 参数形态 | 3 × `String`：`entityAppName`, `entityName`, `controlId`（LocalVariableTable 实名字面；注解为 @PathVariable，参数注解区验证） |
| 返回 DTO | `SingleResponse<Map<String, ?>>` |
| evidence | artifact=udc-starter-runtime, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController`, method=`getCascadeDefaultValue`, class_sha256=`19c40f0353d2346bd0e5c374e8e7a79b9268b739f18cc1049435c12b37e664c8`（javap: docs/audit/artifacts/udc-page-5.3.517/UdcBaseGeneralController.javap.txt；全库 537 jar 负证据: docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md）。注：本条 base 段为 UNRESOLVED-in-5.3.517（HYPOTHESIS 级，全库检索无类级 base 字面值可提取），method/value/参数/返回均为 FACT（javap 字面） |
| metadata_layer | **设计态配置层 — HYPOTHESIS（如实标注，未升级 FACT）**：控件默认值推定属设计态配置数据；**离线 javap 无法确证其数据源层**（设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis 缓存，规则③ 不可互相顶替），**需 LIVE 反查数据来源确认**后方可定层；在确认前本层判定维持 HYPOTHESIS |
| LIVE 回读条件（本轮不做） | 需要：先在线解析 BaseComponentController 基址（LIVE 反查或取得含该类的构件）+ 级联控件样本（entityAppName/entityName/controlId）；判据 = 同一三元组两次调用 identity_matches，Map 值 = 控件默认值；在 base 落地前本条不满足 VERIFIED 全要素，故列可选。（UNVERIFIED, 随新 token 一并活体反查） |

## C6 udc.page_refer.select_tree

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_refer.select_tree` |
| HTTP method | `POST`（注解字面：@PostMapping value=["{entityAppName}/{entityName}/{referGuid}/select-tree"]） |
| 控制器原路径 | **base = UNRESOLVED-in-5.3.517（HYPOTHESIS 级，同 C5）**：`UdcReferController extends com.seeyon.boot.starter.web.BaseComponentController`（类级 @RequestMapping 命中 0），base 继承链无字面值可提取（负证据 docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md，全库 537 jar 无此类于 5.3.517；3 命中旧版本 5.3.345/349/358 属相邻版本单元，禁混写为 5.3.517 FACT）。方法 value 逐字 = `{entityAppName}/{entityName}/{referGuid}/select-tree`，完整路径 = `<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/select-tree` |
| 参数形态 | 4 参：`entityAppName:String, entityName:String, referGuid:String` + 第 4 参内部 DTO（TreeQueryDto，含 treeType 等字段；以 javap Signature 为准） |
| 返回 DTO | `ListResponse<Map<String, ?>>`（以 javap.txt Signature 为准） |
| evidence | artifact=docs/audit/artifacts/udc-page-5.3.517/UdcReferController.javap.txt, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.proxy.controller.UdcReferController`, method=`selectTree`, class_sha256=`912383403dcd0e9e445225308b82a117850fbc98494e54243b6f2d454bf09664` |
| metadata_layer | **实体参照数据层 — HYPOTHESIS（如实标注，未升级 FACT）**：级联参照读回实体/参照数据（树查询），**非平台搭建元数据载体**；离线 javap 无法确证其数据源在 5 层中的确切归属，**需 LIVE 反查确认**；在确认前维持 HYPOTHESIS |
| LIVE 回读条件（本轮不做） | 需要：先在线解析 BaseComponentController 基址（LIVE 反查或取得含该类的构件）+ 级联参照样本（entityAppName/entityName/referGuid）+ TreeQueryDto 查询条件；判据 = 同条件两次调用 identity_matches，ListResponse.data 为级联树 Map 列表且稳定。base 落地前本条不满足 VERIFIED 全要素。（UNVERIFIED, 随新 token 一并活体反查） |

## C7 udc.page_refer.select_by_id

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_refer.select_by_id` |
| HTTP method | `GET`（注解字面：@GetMapping value=["{entityAppName}/{entityName}/{referGuid}/{objectId}"]） |
| 控制器原路径 | **base = UNRESOLVED-in-5.3.517（HYPOTHESIS 级，同 C5/C6）**：继承 BaseComponentController，类级 @RequestMapping 命中 0（负证据 docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md）。方法 value 逐字 = `{entityAppName}/{entityName}/{referGuid}/{objectId}`，完整路径 = `<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/{objectId}` |
| 参数形态 | 4 × `String`/`Long`：`entityAppName, entityName, referGuid`（String）+ `objectId`（Long）；注解 @PathVariable，参数名取 LocalVariableTable 字面 |
| 返回 DTO | `SingleResponse<Object>`（javap Signature 实测非 UdcReferResultDto，以 javap.txt 为准） |
| evidence | artifact=docs/audit/artifacts/udc-page-5.3.517/UdcReferController.javap.txt, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.proxy.controller.UdcReferController`, method=`selectById`, class_sha256=`912383403dcd0e9e445225308b82a117850fbc98494e54243b6f2d454bf09664` |
| metadata_layer | **实体参照数据层 — HYPOTHESIS（如实标注，未升级 FACT）**：级联参照按 ID 读回实体/参照对象，**非平台搭建元数据载体**；离线 javap 无法确证其数据源在 5 层中的确切归属，**需 LIVE 反查确认**；在确认前维持 HYPOTHESIS |
| LIVE 回读条件（本轮不做） | 需要：先在线解析 BaseComponentController 基址 + 级联参照样本（entityAppName/entityName/referGuid/objectId）；判据 = 同对象两次调用 identity_matches，SingleResponse.data 为该参照对象。（UNVERIFIED, 随新 token 一并活体反查） |
| **effective() 门控标注** | **effective()=True**（method==GET + status VERIFIED_STATIC_BYTECODE + write=False，`UdcOperationContract.effective()` 三条件全满足；本域首条 effective()=True。注：base 段虽 UNRESOLVED-in-5.3.517，但 status 取整体 VERIFIED_STATIC_BYTECODE 且 effective() 门控只查 method/status/write，故判 True；MERGE 按 effective 过滤时保留本条，须入 MERGE 门控注记） |

## C8 udc.page_refer.search_list_by_conditions

| 要素 | 值 |
|---|---|
| operation_id | `udc.page_refer.search_list_by_conditions` |
| HTTP method | `POST`（注解字面：@PostMapping value=["{entityAppName}/{entityName}/{referGuid}/search-list-by-conditions"]） |
| 控制器原路径 | **base = UNRESOLVED-in-5.3.517（HYPOTHESIS 级，同 C5/C6/C7）**：继承 BaseComponentController，类级 @RequestMapping 命中 0（负证据 docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md）。方法 value 逐字 = `{entityAppName}/{entityName}/{referGuid}/search-list-by-conditions`，完整路径 = `<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/search-list-by-conditions` |
| 参数形态 | 1 参：`listRequest:ListRequest<?>`（@RequestBody，泛型擦除为 `?`；以 javap Signature 为准） |
| 返回 DTO | `ListResponse<Map<String, ?>>`（以 javap.txt Signature 为准） |
| evidence | artifact=docs/audit/artifacts/udc-page-5.3.517/UdcReferController.javap.txt, version=5.3.517, class=`com.seeyon.boot.starter.udcrt.proxy.controller.UdcReferController`, method=`selectListByConditions`, class_sha256=`912383403dcd0e9e445225308b82a117850fbc98494e54243b6f2d454bf09664` |
| metadata_layer | **实体参照数据层 — HYPOTHESIS（如实标注，未升级 FACT）**：级联参照按条件读回实体/参照数据列表，**非平台搭建元数据载体**；离线 javap 无法确证其数据源在 5 层中的确切归属，**需 LIVE 反查确认**；在确认前维持 HYPOTHESIS |
| LIVE 回读条件（本轮不做） | 需要：先在线解析 BaseComponentController 基址 + 级联参照样本（entityAppName/entityName/referGuid）+ ListRequest 查询条件；判据 = 同条件两次调用 identity_matches，ListResponse.data 为参照结果 Map 列表且稳定。（UNVERIFIED, 随新 token 一并活体反查） |

---

写方法禁入契约记录（同包/同类写方法仅登记排除，非契约）：
- UdcReferController 为纯读控制器（9 读方法全集 selectHighestTree/selectAllChildren4HighestTree/selectTree/selectListByConditions/searchPageByCondition/selectV1ByIds/selectByIds/selectById/selectV1ById，无 create/update/delete 写方法）。本轮仅入 C6/C7/C8 三条高价值读面（树查询/按 ID/条件列表）；其余 6 读方法（selectHighestTree/selectAllChildren4HighestTree/searchPageByCondition/selectV1ByIds/selectByIds/selectV1ById）为同模式读方法，按需扩展，非本刀范围。selectV1ById 同 @GET+VERIFIED+write=False → effective()=True（与 C7 同理，MERGE 门控注记须一并标注）。
- UdcRtPageLogController#createBatch（@POST create-batch）、#deleteAll（@GET delete-all，注解字面是 GetMapping 但语义为删除，双重排除）。
- UdcBaseGeneralController#create/createBatch/update/updateBatch/deleteById/deleteByIds/runtimeCopy/importExcelData/executeDataFlow/forwardCascadeByConditions 等写/执行方法，全部不入契约。
