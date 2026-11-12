# UDC resource（静态资源 / 文件 / 附件）域只读契约 — 5.3.517 单 jar 取证（只读候选 5 条 + 写形态 5 条排除）

- 域模块: udc-resource（资源 / 文件 / 附件模板 / jar 包下载导出）
- 版本单元: 5.3.517（本地 Maven `<MAVEN_REPO>\com\xiaozhua`，只读离线证据）
- 证据单元（scope）: **单 jar** `udc-starter-runtime-5.3.517.jar`
  （`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`，
  sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，861880 B）
- 证据等级: **VERIFIED_STATIC_BYTECODE**（三层扫描计数 + 131 端点行逐条词干判定 + 35 类 `javap -p -v` 落盘）
  + **OBSERVATION**（域归属语义判读 / Servlet 流式下载面 / 构件边界 / `ParameterInfo` 文案不符举例，均不升级）
- 生成: implementer · 依据本会话 `main/ROUTE.md` §1 R2 与 `main/HANDOFF-R2.md`；方法论照抄
  `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`（三层扫描法 + 双口径一致性 + 伪命中族排除）+
  R1（publish 域）先例
- 会话引用基点: 协作会话根目录 = `<COLLAB_ROOT>\agent-collaboration\session-20261008-213135-b84a9517\`；
  仓库内件相对 `<XIAOZHUA_AGENT_ROOT>\` 解析；证据件相对 `docs\audit\artifacts\udc-resource-5.3.517\` 解析

## 结论（唯一判定）
**UDC 5.3.517（本 jar）resource 域 = 非真空：只读候选 5 条（全部未登记过 → registry 建议 5 条新增）。**
1. **只读候选 CANDIDATE = 5 条**：
   - **C1** `AttachmentTemplateController.selectByGuid`（`GET`，`udc-runtime/attachment-template/{guid}`）
   - **C2** `AttachmentTemplateController.selectByGuids`（`POST`，`udc-runtime/attachment-template/select-by-guids`；**查询形态**）
   - **C3** `AttachmentTemplateController.selectByAppId`（`GET`，`udc-runtime/attachment-template/app/{appId}`）
   - **C4** `DynamicJarController.download`（`GET`，`udc-runtime/dynamic/jar/download`；Servlet 流式下载）
   - **C5** `DynamicJarController.downloadApp`（`POST`，`udc-runtime/dynamic/jar/download/{appName}`；注解文案「导出应用」）
2. **写形态 WRITE-EXCLUDED = 5 条**（**不入契约，仅标注**）：`AttachmentTemplateController.create`（`/create`）、
   `createBatch`（`/create-batch`）、`delete`（`/delete/{guid}`）、`deleteByGuids`（`/delete-by-guids`）、
   `RuntimeCOLISplitController.upload`（`upload/result`，MultipartFile 上传）；另 `DynamicJarController.importJar`
   （`/import`，入参 `storageKey`）与 `RuntimeCOLISplitController.upgrade`（`upgrade`）属同族写形态但**端点路径无 resource 词干**
   （见「域边界」段，按词干口径未入本域表）。
3. **registry 去重**：`registry.py`（本轮实测 49 条 `UdcOperationContract`）中 **无任何 attachment / download / dynamic-jar /
   template / resource 条目** → 5 条候选 **全部为新增建议**（见 `registry-entries.md`）。
4. 词干层完备性：L-A 类名层 0 个 controller 承载（`attachment`/`attach`/`template` 命中 6 类中仅 1 个 controller）；
   L-C 常量池层 `resource` 命中 155 条去重后 20 类**全为非 controller 位**（`UdcLoadResourceService` 类型描述符/字段名等）。

## 三层证据（逐层计数 + 判定）
| 层 | 口径 | 覆盖量 | resource 判定结果 | 证据等级 |
|---|---|---|---|---|
| L-A 类名层 | 346 class FQCN × 强 12 词（resource/attachment/upload/download/file/asset/static/doc/skin/theme/media/image）+ 弱 10 词 + 中文 11 词，宽口径子串 → 逐类核 mapping-bearing 资格 | 346 class | **controller 类名承载 = 1**（`AttachmentTemplateController`）；`attachment`/`attach`/`template` = 同族 6 类（服务/DAO/实体/DTO 非遗端点承载）；`resource` 2 类 = 服务层；`file` 1 类 = 事件类；`path` 13 类 + `url` 13 类 = **REST 路径解析器族伪命中**（`{pageUrl}` 路径变量）；`upload`/`download`/`static`/`asset`/`doc`/`skin`/`theme`/`media`/`image` 类名层 0 命中 | VERIFIED_STATIC_BYTECODE |
| L-B 端点路径字面量层 | **131 行逐条词干判定**（24 类级基路径 + 107 方法级），路径取注解原值 | 346 class 全量 → mapping-bearing 类 **27** | 含词干端点行 **10**：CANDIDATE **5**（GET 3 + 非 GET 查询/下载 2）/ WRITE-EXCLUDED **5**；EXCLUDED-NO-STEM = 121；类级基路径含词干 = 1（`udc-runtime/attachment-template`）+ 2 伪命中（`{pageUrl}` 路径变量） | VERIFIED_STATIC_BYTECODE（35 类 `javap -p -v` 落盘 + class_sha256） |
| L-C 常量池全量层 | 346 类的**全部**常量池 Utf8（38646 条，含中文）逐条词干扫描 + 去重 | 346 class / 38646 Utf8 | 命中行 2107（去重后逐词干计数见扫描报告 §L-C）：`resource` 20 类 155 条**全落非 controller 位**（`UdcLoadResourceService` 描述符/字段名、`ResourcePermissionService`、`UdcDynamicResourceServiceImpl`）；`attachment`/`attach`/`template` 命中载体 = 附件模板族 6 类；`file` 346 类（**每类必含 `SourceFile: *.java`** → 结构性伪命中族，非语义命中）；`stream`/`path`/`url`/`storage`/`pic` = 通用词伪命中族；**mapping-bearing 载体命中串全列于扫描报告，无一为端点路径声明**（唯一路径形态 `/download/{appName}` 已在 L-B 表） | VERIFIED_STATIC_BYTECODE（扫描计数）；**语义判读为 OBSERVATION** |
| 双口径一致性 | L-B 自实现 JVMS 常量池 + `RuntimeVisibleAnnotations` 解析器 vs `javap -p -v` 已解码文本独立再提取的 (annotation, path 原值) 集合等值 | 27/27 类 | **mismatch = 0** | VERIFIED_STATIC_BYTECODE |

- 完备性三查（`r1_step5_completeness.json`）：
  - **查 A**: `@RestController`/`@Controller` 类 **24** 个 → 全部在 mapping-bearing 集内（缺口 0）；
  - **查 A'**: mapping-bearing 类内 `@interface` = **0**；仅 `@Component`（非 controller）类 36 个（旁证）；
  - **查 B**: 全类常量池「以 `/` 开头」字面量 40 条，含 resource 词干者 **1** 条（`/download/{appName}`，已在端点表内）→ 无表外新路径；
  - **查 C**: 双口径 27/27 类 mismatch = 0。
- 证据件: `docs/audit/artifacts/udc-resource-5.3.517/resource-endpoint-literal-scan.md`（L-A/L-B/L-C 全量表 +
  27 类 provenance + 完备性表 + 词干判定）+ **35 个 `r1-<Class>.javap.txt`**（`javap -J-Dstdout.encoding=UTF-8 -p -v`
  原始输出，每件 11 字段 provenance 头：source_jar / source_jar_path / jar_sha256 / class_fqcn / class_entry /
  class_sha256 / class_bytes / command / exit_code / run_at_utc / evidence_level）+ 4 个可复跑脚本 + 3 件原始 JSON 计数。

## C1 — udc.attachment.template_get_by_guid

| 要素 | 值 |
|---|---|
| 1. operation_id | `udc.attachment.template_get_by_guid` |
| 2. HTTP method | `GET`（javap 原值 `@GetMapping`） |
| 3. 控制器原路径 | 类级 `@RequestMapping(value=["udc-runtime/attachment-template"])` + 方法级 `{guid}` → 原值拼接 `udc-runtime/attachment-template/{guid}`（**禁拼网关前缀**） |
| 4. 参数形态 | `java.lang.Long guid`；参数注解逐字：`@PathVariable(value="guid")` + `@ParameterInfo(value="附件模板guid")` |
| 5. 返回 DTO | `com.seeyon.boot.transport.SingleResponse<com.seeyon.udc.common.dto.CommonFileDto>`（Signature `(Ljava/lang/Long;)Lcom/seeyon/boot/transport/SingleResponse<Lcom/seeyon/udc/common/dto/CommonFileDto;>;`）；`RestApiOperation(value="根据guid获取附件模板记录")` |
| 6. evidence | artifact=`udc-starter-runtime-5.3.517.jar`（jar_sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`）· class=`com.seeyon.boot.starter.udcrt.controller.AttachmentTemplateController` · class_sha256=`72241cb3ae302c91cd3baba690eaa25656adcedc13e7cdf25413deebd31444f3` · class_bytes=4744 · method=`selectByGuid` · javap=`docs/audit/artifacts/udc-resource-5.3.517/r1-AttachmentTemplateController.javap.txt` · evidence_level=VERIFIED_STATIC_BYTECODE |
| 7. LIVE 回读条件 | **本轮不做 LIVE**。触发条件：① 部署态网关可达 + 授权 token；② 取得**存在的** `guid`（Long，附件模板记录主键）；③ 判据 = HTTP 200 + envelope `BOOT_0000/SUCCESS` + `identity_matches`（同 guid 双读）+ `data != null`（`CommonFileDto`）。**禁连网关（本轮全离线）** |

## C2 — udc.attachment.template_list_by_guids

| 要素 | 值 |
|---|---|
| 1. operation_id | `udc.attachment.template_list_by_guids` |
| 2. HTTP method | `POST`（javap 原值 `@PostMapping`）——**查询形态**（方法名 `selectByGuids`，`RestApiOperation(value="根据guids获取附件模板记录(批量查询)")`，入参 `@RequestBody` 只读主键列表；对照 registry L86 `udc.application.search.no_page` 同形态 POST 查询 + write=False 先例。**若 main 采「仅 GET」严格口径，本条降为标注、不入建议**，此口径问题属可选边界，已在此如实声明） |
| 3. 控制器原路径 | 类级 `udc-runtime/attachment-template` + 方法级 `/select-by-guids` → `udc-runtime/attachment-template/select-by-guids`（禁拼网关前缀） |
| 4. 参数形态 | `java.util.List<java.lang.Long> guids`；参数注解逐字：`@RequestBody`（无 `@ParameterInfo`） |
| 5. 返回 DTO | `com.seeyon.boot.transport.ListResponse<com.seeyon.udc.common.dto.CommonFileDto>`（Signature `(Ljava/util/List<Ljava/lang/Long;>;)Lcom/seeyon/boot/transport/ListResponse<...CommonFileDto;>;`） |
| 6. evidence | 同 C1（class=`...AttachmentTemplateController`，class_sha256=`72241cb3…`，class_bytes=4744，method=`selectByGuids`，javap=`r1-AttachmentTemplateController.javap.txt`，jar_sha256 同）· evidence_level=VERIFIED_STATIC_BYTECODE |
| 7. LIVE 回读条件 | **本轮不做**。触发条件：① 网关可达 + token；② body = 已存在 guid 的 JSON 数组（注意 `@RequestBody` 直接绑定 `List<Long>`）；③ 判据 = 200 + `BOOT_0000/SUCCESS` + `identity_matches`（同 body 双读）+ `data` 列表长度与请求 guid 数一致（或条件致空亦自证） |

## C3 — udc.attachment.template_list_by_app_id

| 要素 | 值 |
|---|---|
| 1. operation_id | `udc.attachment.template_list_by_app_id` |
| 2. HTTP method | `GET`（javap 原值 `@GetMapping`） |
| 3. 控制器原路径 | 类级 `udc-runtime/attachment-template` + 方法级 `/app/{appId}` → `udc-runtime/attachment-template/app/{appId}`（禁拼网关前缀） |
| 4. 参数形态 | `java.lang.Long appId`；参数注解逐字：`@PathVariable(value="appId")` + `@ParameterInfo(value="附件模板guid")` —— **注意：该 `ParameterInfo` 文案与形参名 `appId` 不符**（源码共用了同一注解文案），此处**逐字照录**，语义判读记为 OBSERVATION，不改为「appId」 |
| 5. 返回 DTO | `com.seeyon.boot.transport.ListResponse<com.seeyon.udc.common.dto.CommonFileDto>`；`RestApiOperation(value="根据appId获取附件模板记录")` |
| 6. evidence | 同 C1（method=`selectByAppId`，class_sha256=`72241cb3…`，javap=`r1-AttachmentTemplateController.javap.txt`）· evidence_level=VERIFIED_STATIC_BYTECODE |
| 7. LIVE 回读条件 | **本轮不做**。触发条件：① 网关可达 + token；② 已知 `appId`（Long）；③ 判据 = 200 + `BOOT_0000/SUCCESS` + `identity_matches` + `data` 为 `CommonFileDto` 列表 |

## C4 — udc.jar.download

| 要素 | 值 |
|---|---|
| 1. operation_id | `udc.jar.download` |
| 2. HTTP method | `GET`（javap 原值 `@GetMapping`） |
| 3. 控制器原路径 | 类级 `@RequestMapping(value=["udc-runtime/dynamic/jar"])` + 方法级 `download` → `udc-runtime/dynamic/jar/download`（禁拼网关前缀） |
| 4. 参数形态 | `(javax.servlet.http.HttpServletRequest, javax.servlet.http.HttpServletResponse)`；**无参数注解**（javap 该方法无 `RuntimeVisibleParameterAnnotations`） |
| 5. 返回 DTO | **`void`** —— Servlet 流式下载（无 `SingleResponse`/`ListResponse` transport envelope），HTTP body 即 jar 字节流（OBSERVATION：写回响应流，未做 LIVE 确证） |
| 6. evidence | artifact=`udc-starter-runtime-5.3.517.jar`（jar_sha256 `74ae50bd…a66f`）· class=`com.seeyon.boot.starter.udcrt.controller.DynamicJarController` · class_sha256=`0eb1fd79e96e09eb0122c0aafd77d8922ee3163f46f5436a44c98b476726def2` · class_bytes=5796 · method=`download` · javap=`docs/audit/artifacts/udc-resource-5.3.517/r1-DynamicJarController.javap.txt` · evidence_level=VERIFIED_STATIC_BYTECODE |
| 7. LIVE 回读条件 | **本轮不做**。触发条件：① 网关可达 + token；② 该类无 `RestApi` 之外的方法级文案，**下载对象（哪个 jar）离线不可确证** → LIVE 需先确证 ② 与 blob 落盘判据；③ 判据 = HTTP 200 + `Content-Type`/`Content-Length` 类响应头 + 落盘字节非空（**不适用 transport envelope 判据**） |

## C5 — udc.jar.export_app

| 要素 | 值 |
|---|---|
| 1. operation_id | `udc.jar.export_app` |
| 2. HTTP method | `POST`（javap 原值 `@PostMapping`）——注解语义为**导出**（`RestApiOperation(value="导出应用", description="导出应用,按照应用名称导出最新的jar包")`）；**非 GET**，按 HANDOFF 词干口径（GET 查询/下载入契约）属边界项，**在此如实标注为「POST 读取/导出形态」候选**，如 main 采严格 GET-only 口径则降为标注 |
| 3. 控制器原路径 | 类级 `udc-runtime/dynamic/jar` + 方法级 `/download/{appName}` → `udc-runtime/dynamic/jar/download/{appName}`（禁拼网关前缀） |
| 4. 参数形态 | `java.lang.String appName`；参数注解逐字：`@PathVariable(value="appName")`（无 `@ParameterInfo`） |
| 5. 返回 DTO | `com.seeyon.boot.transport.SingleResponse<java.lang.String>` |
| 6. evidence | 同 C4（method=`downloadApp`，class_sha256=`0eb1fd79…`，class_bytes=5796，javap=`r1-DynamicJarController.javap.txt`）· evidence_level=VERIFIED_STATIC_BYTECODE |
| 7. LIVE 回读条件 | **本轮不做**。触发条件：① 网关可达 + token；② 已知 `appName`（且该应用有已构建 jar）；③ 判据 = 200 + `BOOT_0000/SUCCESS` + `identity_matches` + `data`（String，jar 名/路径或内容摘要）；**副作用未确证**（离线只见名称与注解文案，未见写库/写盘证据） |

## 写形态（WRITE-EXCLUDED，**不入契约**，仅标注）
| # | 端点 | 判据 |
|---|---|---|
| W1 | `AttachmentTemplateController.create` `@PostMapping("/create")`，入参 `AttachmentTemplateDto` `@RequestBody`，返回 `SingleResponse<AttachmentTemplateDto>` | 创建（写） |
| W2 | `AttachmentTemplateController.createBatch` `@PostMapping("/create-batch")`，入参 `List<AttachmentTemplateDto>` `@RequestBody` | 批量创建（写） |
| W3 | `AttachmentTemplateController.delete` `@PostMapping("/delete/{guid}")`，入参 `Long guid` `@PathVariable`，返回 `SingleResponse<Integer>` | 删除（写） |
| W4 | `AttachmentTemplateController.deleteByGuids` `@PostMapping("/delete-by-guids")`，入参 `List<Long>` `@RequestBody` | 批量删除（写） |
| W5 | `RuntimeCOLISplitController.upload` `@PostMapping("upload/result")`，入参 `org.springframework.web.multipart.MultipartFile`，返回 `SingleResponse<UploadResultDto>` | 上传动作（写） |
| 备注 | `DynamicJarController.importJar`（`@PostMapping("/import")`，入参 `String storageKey` `@ParameterInfo`+`@MultiRequestBody`）与 `RuntimeCOLISplitController.upgrade`（`@PostMapping("upgrade")`）为同族写形态，但**端点路径无 resource 词干** → 未入本域 L-B 判定表（仅在此登记，避免漏项） | 写（导入/升级） |

## 域边界与不扩扫声明（OBSERVATION，非验收变更）
- **本契约证据单元 = 单 jar `udc-starter-runtime-5.3.517.jar`**（任务声明构件）；未扫其他 5.3.517 `udc-*` jar、未扫 `customer-*` 构件，**不构成「其他构件无 resource 域端点」的结论**。
- 词干口径边界（如实登记，未扩表）：`DynamicJarController.getRequestStatus`（`GET import/status/{requestId}`，返回 `SingleResponse<RequestStatusDto>`，注解「导入状态查询」）为**只读端点**，但其路径/方法名不含本域任何词干 → 按词干口径**未计入本域 5 条候选**；若 main 认为「jar 导入面」应属 resource 域，可另行开 HANDOFF 扩表（本任务不自行扩）。
- `proxy.controller.FormAppMbController`/`FormAppPcController` 类级基路径含 `{pageUrl}`（弱词干 `url` 命中）= **伪命中**（页面路径变量，非静态资源面），不计入。
- `event.event.ExternalFileEvent` / `domain.service.ResourcePermissionService` / `domain.service.UdcDynamicResourceServiceImpl` = 事件/服务层，**非端点承载者**，不入契约。
- 跨版本禁写：证据仅 5.3.517；本地相邻版本单元（如 5.3.496 test2、5.3.260 ganttchart）不得与本单元混写。

## 交付三件套索引（TASK-GOAL 三件齐）
1. 本契约: `docs/operation-contracts/udc/resource/udc-resource-readonly-contracts.md`
2. registry 建议: `docs/operation-contracts/udc/resource/registry-entries.md`（**5 条新增建议** + 10 字段构造 + 去重实测说明）
3. javap 证据落盘: `docs/audit/artifacts/udc-resource-5.3.517/` —— `resource-endpoint-literal-scan.md` +
   **35 个 `r1-<Class>.javap.txt`**（11 字段 provenance 头 + class_sha256）+ 4 个可复跑脚本
   （`r1_scan_mapping_bearing.py` / `r1_javap_dump.py` / `r1_completeness_checks.py` / `r1_build_report.py`，
   骨架复用 R1 五脚本并改词干）+ 原始计数 `r1_step1_raw.json` / `r1_step3_dump_report.json` /
   `r1_step5_completeness.json` + 过程输出 `r1_step1_stdout.txt` / `r1_step3_stdout.txt` / `r1_step5_stdout.txt`

## 红线自查
- 写面仅 `docs/operation-contracts/udc/resource/**` + `docs/audit/artifacts/udc-resource-5.3.517/**`；
  `docs/operation-contracts/udc/publish/**` 与 R1 证据目录 **本轮零改动**（R1 已完成 VERDICT PASS，禁再动）；
  `registry.py` / `tests/**` / 其他域契约目录零改动（registry 仅只读 grep 复核）。
- 无 LIVE / 无网关 / 无 `.207`；路径全部取注解原值、**未拼任何网关前缀**（类级基路径均无前导 `/`，方法级前导 `/` 混用，逐字照录）；
  写形态（create/delete/upload/import/upgrade）**未混入契约**（W 段单列标注）。
- 证据等级未越级：域归属、Servlet 流式下载面、`ParameterInfo` 文案不符、构件边界均标 **OBSERVATION**。
- 版本归属 5.3.517 单一；`git` 写操作全禁（主控代提交）。
