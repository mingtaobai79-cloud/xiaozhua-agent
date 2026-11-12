# registry-entries.md — 页面规则域 UdcOperationContract 建议条目（件 3）

状态：**只建议，不改 registry.py**（registry.py 为冻结文件，由 UDC-MERGE 任务统一落库）。
风格来源：逐字段照抄 `components/platform_operations/registry.py` 现有条目构造签名（只读参考，本会话实测）：

```python
# registry.py 现有条目风格（只读摘录，禁改原文件）
contracts[operation_id] = UdcOperationContract(
    operation_id,            # "udc.page_log.search"
    method,                  # "POST"
    path,                    # "udc-runtime/rt-page-log/search"
    request_type,            # "PageDtoRequest<UdcRtPageLogSearchDto> (RequestBody)"
    response_type,           # "PageResponse<UdcRtPageLogSearchResultDto>"
    OperationStatus.VERIFIED_STATIC_BYTECODE,   # 状态
    False,                   # write —— 本域全部只读，逐条固定 write=False
    [evidence],              # evidence dict 列表
    ("query",),             # inputs tuple
    ("…readback 判据…",)    # readback tuple
)
# evidence dict 字段风格（registry.py 现有）:
{"source": "...", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517",
 "class": "<fqcn>", "method": "<method>", "class_sha256": "<sha256>",
 "javap": "docs/audit/artifacts/udc-page-5.3.517/<Class>.javap.txt",
 "evidence_level": "VERIFIED_STATIC_BYTECODE"}
```

jar_sha1（对照 .sha1 文件，实测一致）：`e3e27271fab53b0610a954d83dadab003cabad62`（udc-starter-runtime-5.3.517.jar）。

---

## 条目 1 — udc.page_log.search（FACT）

```python
page_log_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageLogController", "method": "search", "class_sha256": "86efc8a3b0924cb46f4d8ca11b527ba9129f3dd6d938e345c5cb11be15038c5e", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcRtPageLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.page_log.search"] = UdcOperationContract("udc.page_log.search", "POST", "udc-runtime/rt-page-log/search", "PageDtoRequest<UdcRtPageLogSearchDto>(RequestBody)", "PageResponse<UdcRtPageLogSearchResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_log_evidence], ("query",), ("同一 query 条件回读 identity_matches", "响应 data 为 UdcRtPageLogSearchResultDto 分页列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

## 条目 2 — udc.page_log.search_non_metadata（FACT）

```python
contracts["udc.page_log.search_non_metadata"] = UdcOperationContract("udc.page_log.search_non_metadata", "POST", "udc-runtime/rt-page-log/search-non-metadata", "PageDtoRequest<UdcRtPageLogSearchDto>(RequestBody)", "PageResponse<UdcRtPageLogSearchResultDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_log_evidence], ("query",), ("同一 query 条件回读 identity_matches", "与 udc.page_log.search 差异仅限元数据字段（LIVE 样本确认前不作断言）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

## 条目 3 — udc.page_info.check_exists（FACT）

```python
page_info_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRtPageInfoController", "method": "checkPageExistsByConditions", "class_sha256": "7678734875e3c96aa463bd94084061b23ab80d846aa82e3cfe96f79db14a2e02", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.page_info.check_exists"] = UdcOperationContract("udc.page_info.check_exists", "POST", "udc-runtime/meta-data/check-page-exists", "List<UdcRtPageExistsDto>(RequestBody, 参数名 pageExistsDtoList)", "ListResponse<Boolean>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_info_evidence], ("pageExistsDtoList",), ("同一条件列表回读 identity_matches", "存在样本恒 true / 不存在样本恒 false", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

## 条目 4 — udc.page_info.select_host_and_only_page（FACT）

```python
contracts["udc.page_info.select_host_and_only_page"] = UdcOperationContract("udc.page_info.select_host_and_only_page", "POST", "udc-runtime/meta-data/select-host-and-only-page-pages", "UdcPagesMetaDataSearchDto(RequestBody, 参数名 request)", "ListResponse<UdcMainPageMetadataDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [page_info_evidence], ("request",), ("同一 UdcPagesMetaDataSearchDto 回读 identity_matches", "响应为 UdcMainPageMetadataDto 非空列表（或条件致空列表亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

注：条目 4 参数名 `request` 已 javap LocalVariableTable（slot 1，`Lcom/.../UdcPagesMetaDataSearchDto;`）逐字实取为 FACT，参数类型亦 FACT，本条全 FACT。

## 条目 5（可选）— udc.page_general.get_cascade_default_value（base UNRESOLVED-in-5.3.517，全条降级）

```python
base_general_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController", "method": "getCascadeDefaultValue", "class_sha256": "19c40f0353d2346bd0e5c374e8e7a79b9268b739f18cc1049435c12b37e664c8", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcBaseGeneralController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE(method/value/params);UNRESOLVED-in-5.3.517(base)", "negative_evidence": "docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md"}
contracts["udc.page_general.get_cascade_default_value"] = UdcOperationContract("udc.page_general.get_cascade_default_value", "GET", "<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{controlId}/get-cascade-default-value", "String entityAppName + String entityName + String controlId (PathVariable)", "SingleResponse<Map<String, ?>>", OperationStatus.UNKNOWN, False, [base_general_evidence], ("entityAppName", "entityName", "controlId"), ("先解析 BaseComponentController 基址（全库 537 jar 负证据：5.3.517 无此类，旧版本 5.3.345/349/358 亦无类级 @RequestMapping，需 LIVE 反查或取得含 5.3.517 版该类的构件）", "同一三元组回读 identity_matches，Map 值=控件默认值"))
```

- 状态降 `UNKNOWN` 而非 `VERIFIED_STATIC_BYTECODE`：base 路径段 = UNRESOLVED-in-5.3.517（全库 537 jar 扫描无此类于 5.3.517；父类 BaseComponentController 仅存于 5.3.345/349/358 相邻旧版本，类级 0 处 @RequestMapping，继承链无 base 字面值可提取；相邻旧版本类信息禁止混写为 5.3.517 FACT），整条不可全 FACT（与契约 C5 一致）。
- 若 MERGE 任务只收 FACT 条目，本条丢弃即可，前 4 条自成闭环（≥3 条验收线）。

---

## MERGE 集成注记（R4 补证，2026-09-17）

**照抄插入点**：`registry.py::UdcOperationRegistry.default()` 内 `contracts` dict（本文件 5 条 `contracts[oid] = UdcOperationContract(...)` 逐字块可直接粘入该 dict 构建处，与现有 `udc.entity.*`/`udc.application.get` 等条目同一作用域；evidence 变量 `page_log_evidence`/`page_info_evidence`/`base_general_evidence` 需随块一并带入，或按 default() 现有局部变量风格重命名，字段值逐字不变）。

**dry-run 结果指针**：`docs/audit/artifacts/udc-page-5.3.517/registry-entries-dryrun.md`（R4，overall PASS：5 条逐字可实例化 + UdcOperationRegistry(dict) 构造成功 + EXIT=0；stdout 全量在档）。

**operation_id 冲突检查结果**：本域 5 id（udc.page_log.search / udc.page_log.search_non_metadata / udc.page_info.check_exists / udc.page_info.select_host_and_only_page / udc.page_general.get_cascade_default_value）与既有 `default()` 的 27 个 operation_id **零冲突**（dry-run STEP 3 实测 disjoint，既有全集含 udc.entity.* / udc.attribute.* / udc.application.get / udc.microflow.function_node_tree / udc.datatype.get_all / udc.applog.select_by_id）。

**effective() 门控事实标注（MERGE 业务取舍点，本任务只标注不代决）**：`UdcOperationContract.effective()`（models.py:47-50）判据 = `status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} AND NOT write AND method.upper()=="GET"`。本域 4 条读契约 method=POST（@PostMapping 注解字面值，禁按读语义改）→ 4 条 `effective()=False`；C5 虽 method=GET 但 status=UNKNOWN → 亦 `effective()=False`。**UDC-MERGE 若按 `effective()` 过滤，本域 5 条全部被排除**——须 MERGE 任务决策（调整门控 / 另立只读契约就绪判据 / 保留为参考条目），本会话越权不判。

**registry.py 照抄前后 sha256 自证零改动**：pre=`e9a195b2b2a75689cd9d9d812445011b32797c3a8dc15766a9c482aec016a43e` = post（dry-run STEP 5 只读实测，本轮未写该文件；MERGE 实际落库时的前后 sha 由 MERGE 任务自证）。

> ⚠ 基线演进注记（下文各行 sha/计数均为历史时点记录，非当前基线）：registry.py 本域落库后 sha 已多次漂移——`8451672…`（wake-19 落库后）→ `332299c5…`（R6 config 化）→ `6b630df0…`（他会话加 metadata.page_tree）→ **`44f4b07849bc`（主线 b8b5ac83 当前基线）**。本节「27 ids / 8451672…」等数值绑定历史基线，**最新一致性以文件末『基线对齐注记（44f4b078）』节为准**。

**有效条目计数（R5-C 更新，2026-09-18）**：本件 3 建议条目共 8 条 —— **条目 1-4（page_log/page_info）已按 UDC-MERGE（wake-19, human 真正授权）入册 registry.py PASS（registry.py sha=`8451672…`）**；条目 5（C5, status=UNKNOWN）授权丢弃未入册；**条目 6/7/8（refer 读面）为 forward 候选，是否入册=独立 MERGE 决策（须 human 再授权解冻 + LIVE 解析 BaseComponentController 基址），本刀 registry.py 零改动**（详见本文件末「R5 refer 读面 门控注记」节）。

---

## 条目 6 — udc.page_refer.select_tree（refer 读面，base UNRESOLVED-in-5.3.517）

```python
refer_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.proxy.controller.UdcReferController", "method": "selectTree", "class_sha256": "912383403dcd0e9e445225308b82a117850fbc98494e54243b6f2d454bf09664", "javap": "docs/audit/artifacts/udc-page-5.3.517/UdcReferController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE(method/value/params/return);UNRESOLVED-in-5.3.517(base)", "negative_evidence": "docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md"}
contracts["udc.page_refer.select_tree"] = UdcOperationContract("udc.page_refer.select_tree", "POST", "<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/select-tree", "String entityAppName + String entityName + String referGuid (PathVariable) + TreeQueryDto(级联树查询DTO，第4参 @RequestBody)", "ListResponse<Map<String, ?>>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [refer_evidence], ("entityAppName", "entityName", "referGuid", "treeQueryDto"), ("同一条件回读 identity_matches，ListResponse.data 为级联树 Map 列表", "base 段 UNRESOLVED-in-5.3.517（继承 BaseComponentController，全库 537 jar 无此类于 5.3.517，需 LIVE 反查基址）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

- 状态 = `VERIFIED_STATIC_BYTECODE`（method/value/参数/返回 均 javap 逐字 FACT）；**base 段 = UNRESOLVED-in-5.3.517**（同 C5，HYPOTHESIS 级：类级 @RequestMapping 命中 0，继承链无 base 字面值；负证据 docs/audit/artifacts/udc-page-5.3.517/C5-negative-evidence.md）。
- `effective()=False`（method=POST，@PostMapping 注解字面值禁改）。

## 条目 7 — udc.page_refer.select_by_id（refer 读面，**effective()=True**）

```python
contracts["udc.page_refer.select_by_id"] = UdcOperationContract("udc.page_refer.select_by_id", "GET", "<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/{objectId}", "String entityAppName + String entityName + String referGuid + Long objectId (PathVariable)", "SingleResponse<Object>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [refer_evidence], ("entityAppName", "entityName", "referGuid", "objectId"), ("同一 objectId 回读 identity_matches，SingleResponse.data 为该参照对象", "base 段 UNRESOLVED-in-5.3.517（同 C5，需 LIVE 解析 BaseComponentController 基址）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

- 状态 = `VERIFIED_STATIC_BYTECODE`（返回 `SingleResponse<Object>` 为 javap Signature 实测，非 UdcReferResultDto）；**base 段 = UNRESOLVED-in-5.3.517**。
- **`effective()=True`**（method=GET + status=VERIFIED_STATIC_BYTECODE + write=False，三条件全满足；本域 refer 面首条过门控，须入 MERGE 门控注记）。
- 附注：`selectV1ById` 同为 @GET + VERIFIED_STATIC_BYTECODE + write=False → **`effective()=True`**（与条目 7 同理，门控注记一并标注）。

## 条目 8 — udc.page_refer.search_list_by_conditions（refer 读面，base UNRESOLVED-in-5.3.517）

```python
contracts["udc.page_refer.search_list_by_conditions"] = UdcOperationContract("udc.page_refer.search_list_by_conditions", "POST", "<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/search-list-by-conditions", "ListRequest<?> listRequest (@RequestBody, 1 参, 泛型擦除为 ?)", "ListResponse<Map<String, ?>>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [refer_evidence], ("listRequest",), ("同一 ListRequest 条件回读 identity_matches，ListResponse.data 为参照结果 Map 列表", "base 段 UNRESOLVED-in-5.3.517（同 C5，需 LIVE 解析 BaseComponentController 基址）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

- 状态 = `VERIFIED_STATIC_BYTECODE`（method/value/参数/返回 javap 逐字 FACT）；**base 段 = UNRESOLVED-in-5.3.517**。
- `effective()=False`（method=POST，@PostMapping 注解字面值禁改）。

---

## R5 refer 读面 门控注记（R5-C，2026-09-18）

**条目来源**：条目 6/7/8 逐字镜像件 B（page-readonly-contracts.md C6/C7/C8）+ UdcReferController.javap.txt（SHA-256 第3行 `912383403dcd0e9e445225308b82a117850fbc98494e54243b6f2d454bf09664`）。控制器 `UdcReferController extends BaseComponentController`（类级 @RequestMapping 命中 0），base=UNRESOLVED-in-5.3.517，同 C5 模式，负证据引 C5-negative-evidence.md。

**effective() 门控结果**（models.py:47-50 判据）：
- **条目 7 `udc.page_refer.select_by_id` = `effective()=True`**（method=GET + VERIFIED_STATIC_BYTECODE + write=False）。
- **selectV1ById（未列入本刀 3 条）= `effective()=True`**（与条目 7 同理：@GET + VERIFIED + write=False；如需入册按同模板补一条）。
- 条目 6 `select_tree` / 条目 8 `search_list_by_conditions` = `effective()=False`（method=POST）。
- 对比：本域主条目 1-4（page_log/page_info）全 POST → effective()=False；条目 5（C5 get_cascade_default_value）GET 但 status=UNKNOWN → 亦 False。**故本域 refer 面首现 2 条 effective()=True（条目 7 + selectV1ById）**。

**forward 范围说明（本刀不代决、不落库）**：refer 3 条（条目 6/7/8）是否落 registry.py 为独立 MERGE 决策。本会话 UDC-MERGE（wake-19，human 真正授权）范围=仅 FACT 条目 1-4 入册、已执行 PASS（registry.py sha=`8451672…`）；refer 条目为 wake-16 后新发现，**不在该授权范围内**。若后续要落 refer，须：① human 再次授权解冻 registry.py 且明确纳入 refer 范围；② 且 base 段须先 LIVE 解析 BaseComponentController 基址（UNRESOLVED-in-5.3.517 → 落地后 3 条方可全 FACT）。在此之前 refer 3 条仅作为件 3 建议文档候选，registry.py 零改动。

---

## 元数据锚点规则对齐注记（R8, human 084505, 2026-09-18）

**规则来源**：human 084505「UDC 元数据锚点规则立即生效」4 条规则（①meta-data=平台首选读写面；②验收=回读元数据 identity_matches，HTTP 200/Boolean 不算证据；③设计态配置≠运行态元数据≠生成物≠物理表≠Redis 缓存不可顶替；④元数据结构随大版本演进按版本族隔离）。

**① C2a Boolean 判据修订（规则②强制）**：
- **修订前**（本文件条目 3 `udc.page_info.check_exists` 的 verification_rules，亦为 registry.py 已落库原文）：「同一条件列表回读 identity_matches / 存在样本恒 true / 不存在样本恒 false / 网关 service 前缀 UNVERIFIED」。
- **修订后（规则②）**：验收判据 = **回读元数据 identity_matches**（以 meta-data 接口回读该页面的运行态元数据并比对）；`check_exists` 返回的 `ListResponse<Boolean>` 与 HTTP 200 **仅作辅助信号，本身不构成验收证据**（HTTP 200/Boolean 不算证据）。
- **forward 建议（本刀不改 registry.py）**：registry.py 内 `udc.page_info.check_exists` 的 `verification_rules` 原文保留（已落库 4 条 FACT 为事实记录，human 未要求改已落库条目）；后续 UDC-MERGE/对齐任务可将规则②判据同步进该条目 `verification_rules`，本刀只在建议文档标注，registry.py 零改动。

**② 各条目 metadata_layer 标注表**（FACT=依据明确 / HYPOTHESIS=如实标注未升级）：

| 条目 | operation_id | metadata_layer | 判定 |
|---|---|---|---|
| 条目 1 | udc.page_log.search | 运行态日志层（5 层中非 metadata 层） | FACT |
| 条目 2 | udc.page_log.search_non_metadata | 运行态日志层（5 层中非 metadata 层） | FACT |
| 条目 3 | udc.page_info.check_exists | 运行态元数据层（meta-data 首选读面，规则①） | FACT |
| 条目 4 | udc.page_info.select_host_and_only_page | 运行态元数据层（UdcMainPageMetadataDto 页面主元数据） | FACT |
| 条目 5 | udc.page_general.get_cascade_default_value | 设计态配置层（控件默认值推定；离线无法确证数据源层） | HYPOTHESIS（需 LIVE 反查数据来源） |
| 条目 6 | udc.page_refer.select_tree | 实体参照数据层（级联树查询，非平台搭建元数据） | HYPOTHESIS（需 LIVE 反查确认） |
| 条目 7 | udc.page_refer.select_by_id | 实体参照数据层（级联参照按 ID，非平台搭建元数据） | HYPOTHESIS（需 LIVE 反查确认） |
| 条目 8 | udc.page_refer.search_list_by_conditions | 实体参照数据层（级联参照按条件，非平台搭建元数据） | HYPOTHESIS（需 LIVE 反查确认） |

**③ 版本族隔离声明**（规则④）：本文件全部条目证据（bytecode SHA-256 / base / 方法 / DTO / metadata_layer 判定）绑定 `udc-starter-runtime` 5.3 族 5.3.517 单一构件；跨版本族（含 test2 镜像 5.3.496 / 相邻旧版本 5.3.345-358）**不得复用本判定**。HYPOTHESIS 项（条目 5/6/7/8）在 LIVE 反查确认数据源层前**不得升级 FACT**（5 层不可顶替，规则③）。

---

## 基线对齐注记（合并自 4 份漂移注记，2026-09-18；唯一权威块，取代上方 160/181/196/208 各节）

> **本块为此后唯一基线对齐注记**。前几轮每漂移一级即追加一份新节，已堆叠 4 份相互矛盾（各锚定 44f4b078 / 37caf4d2 / c2d8e9f1 / 752b8264 的时点值）——本块将其合并为一份自洽记录，**不再追加新节**；若活体 registry.py 基线再变，仅更新本块「活体可复验锚点」一行 + 补 1 次 sha256sum+行号 re-grep 即可，不新增节。

**A. 对齐基准名（human 历次指定）**：human 21:33 起反复指定 **`c2d8e9f10a3b`** 为对齐基准。诚实边界：`c2d8e9f1` 内容本 checkout **不可达且已被活体越过**——三层只读 hunt（git commit-hash / 文件内容副本 / git blob 内容-hash 空间）均不可达（非 git 对象、无 remote 可 fetch、本地无并行 registry.py 副本、registry.py 内容 grep c2d8e9f1=0，reflog/stash/全 git blob/主线会话目录 五空间全搜命中=0）。故本刀**无法在 `c2d8e9f1` 上字节级复验 1-4，亦不臆造其字段值**（5 层不可顶替，HYPOTHESIS 不升 FACT）。
- **但 1-4 对齐一致性可用「additive 括号不变式」离线闭环（非臆造，是夹逼推导）**：漂移链 `37caf4d2`→〔c2d8e9f1〕→`752b8264`→`dc0512d2` 全程主线**纯加法式**（每步仅追加 `udc.*` 条目，从不改既有行、从不动 page 域 1-4）。已独立复验 **下界 37caf4d2 与上界 dc0512d2 两处 1-4 均 4/4 VERBATIM-OK 于行 55-58**（R17 本轮活体重核：上界由前活体漂至 dc0512d2）（行号未位移、refer 恒 0、M3 additive 未破）。因中段 c2d8e9f1 处在这两处已验证不变量之间、且链上无行级改动，**由单调加法不变式可推：c2d8e9f1 态下 1-4 行 55-58 亦逐字成立**。此结论性质=**行级稳定性夹逼（非 c2d8e9f1 字节级复验）**，满足「以 c2d8e9f1 为对齐基准使 1-4 保持一致」的离线要求；若日后需 c2d8e9f1 **字节级**直接锚定（更强），仍须主线把 c2d8e9f1 版 registry.py commit 到可 fetch ref / 合并共享树 / 或 human 给逐行内容或 diff，补 1 次 `sha256sum`+行号 re-grep。

**B. 活体可复验锚点（本地实测，随基线漂移只更新此值）**：本 checkout `registry.py` 活体实测 = **`dc0512d242c65c13…`**（`udc.*` LHS 注册口径 42 条，全量出现 45 含 3 行 `replace` 双引、去重 0；主线 b8b5ac83 R17 entity-13 additive MERGE 于 前活体基线(29 条) 之上纯加法新增至 42，本任务不涉及其新增域）。漂移链（逐级加法，均为主线未 commit 工作树值）：`8451672`→`332299c5`→`6b630df0`→`44f4b078`→`37caf4d2`→〔c2d8e9f1，human 指定基准名〕→`752b8264`→**`dc0512d2`（现活体，归因=微流程 b8b5ac83 R17 entity-13 additive，本域 1-4 行 55-58 逐字未动/未位移；前活体基线已被本步越过，历史步骤值 events/ROUTE 有档、本链不再携带）**。

**C. 本任务 1-4 逐字一致性（锚定活体 B=dc0512d2, 非 c2d8e9f1）**：registry-entries.md 条目 1-4 的 `UdcOperationContract(...)` 逐字块（行 35/41/48/54）与 `registry.py` 行 55-58 **4/4 VERBATIM-OK**（R17 活体重核于 dc0512d2：strip 前导空白后逐行 diff 实测 MATCH）。主线 additive 演进**未触碰 page 域**：本任务 1-4 行 55-58 逐字未动、行号未位移；`udc.page_refer`=0（6/7/8 未入册，符合预期）、`udc.page_general`=0（C5 授权丢弃，符合预期）；M3 微流程侧 `udc.metadata.page_exists_check` x2 + `udc.metadata.page_tree` x2（只记录不处置）。

**D. M3 跨域同端点重叠（事实记录，去重留 human 裁定）**：主线 b8b5ac83 新增条目与本任务已落库条目指向同一物理读面——`check-page-exists`（grep 2 命中）= 本任务行 57 `udc.page_info.check_exists` ↔ `udc.metadata.page_exists_check`；`select-host-and-only-page-pages`（grep 2 命中）= 本任务行 58 `udc.page_info.select_host_and_only_page` ↔ `udc.metadata.page_tree`。meta-data 域与 page 域对同一对端点各登一份契约，仅 operation_id/evidence dict/verification_rules 措辞不同。**归域 + 去重留 human 裁定项①/M3**，本任务无权合并/删除主线条目、不擅改自身已落库条目，仅记事实不代决。

**E. refer 3 条 zero-conflict（human 授权范围外，维持待授权）**：活体 grep `udc.page_refer` = 0 → refer 条目 6/7/8（本文件）尚未入册。zero-conflict 对任何基线均成立（refer id 不与任何 `udc.*` 条目冲突），**refer 落库仍属 human 授权项**，本文件仅更新一致性标注，不触发落库、不重发 HANDOFF。

**F. 本文件内部引用一致性**：上文 R4/R5/R8 各节引用的 registry.py sha（`8451672…`/`332299c5…`/`e9a195b2…`）为**历史时点记录**（各刀落库时自证值）；行 79/81 的「基线演进注记」为早期就地标注。条目 1-8 逐字照抄源因 1-4 逐字完好、refer 恒 0 而未改写。

**G. 结论（本块取代 4 份旧漂移注记）**：
- 1-4 逐字照抄源在**活体 additive 漂移下内容不变**（锚定 B=`dc0512d2`，4/4 VERBATIM-OK、refer 恒 0、M3 additive 未破）；**只要 1-4 行 55-58 逐字未动（additive-only 前提），照抄源始终有效**。
- `c2d8e9f1`（human 指定基准名）= 历史基线名，不可达且已被活体越过，**不直接作 1-4 锚点**；直接锚定待主线同步 c2d8e9f1 版 registry.py（解锁条件见 A 末）。
- 本刀零写 registry.py / 冻结件、零重发 HANDOFF、零落库（遵 human 限定）；主线基线 flux 收敛 / M3 去重 / refer 落库 / effective() 门控 / LIVE 凭据 仍属 human 裁定域，本任务只标不代决。

## 执行记录（回执行 · 条目 7）

- **2026-10-19 主控复核**：`udc.page_refer.select_by_id` 已由 implementer 按本文件「条目 7」python 块**逐字节**照抄落库`components/platform_operations/registry.py`（主控 program 级逐行 diff：契约构造行 + `refer_evidence` 定义行均 `BYTE-IDENTICAL`）。write=False、status=`OperationStatus.VERIFIED_STATIC_BYTECODE`。
- **base 段逐字保留**：path = `<BASE-UNRESOLVED-in-5.3.517>/{entityAppName}/{entityName}/{referGuid}/{objectId}`，**未臆造任何前缀**；base 的 LIVE 解析（继承 `BaseComponentController`，5.3.517 全库无此类）仍为 UNRESOLVED，verification_rules 内该项保留为待 LIVE 项。
- **授权与门控**：本条落库由 TASK-GOAL R1 第 7 条直接授权（覆盖本文件「refer 落库须 human 再授权」的旧门控）；`effective()=True`（GET + VERIFIED_STATIC_BYTECODE + write=False）。**条目 6/8（select_tree / search_list_by_conditions）本轮未落库**。
- **落库状态**：registry 有效键 HEAD `54bfdf9` 实测 76 → 78（含本条），本条全键 0 命中，无 key 覆盖。`registry.py` sha256（落盘实测）= `8a6e0390ce81eb4f790a11e671bca7b7330213fc29158865b45bdd80f0144148`。**待主控提交后回填 commit**。
