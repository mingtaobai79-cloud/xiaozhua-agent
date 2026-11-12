# registry-entries — UDC BI 域（udc/bi）

- 生成: implementer · R2 · VACUUM 分支（依 main/ROUTE.md R2）
- 权威参照: `components/platform_operations/models.py:29-40`（29 = `@dataclass(frozen=True)` 装饰行，30 = `class UdcOperationContract` 行，31–40 = 10 个字段；只读核对，未改）—— 本件套全文统一采此行号口径（R3 D-3）
- 落库策略: **本域不新增任何 UdcOperationContract 条目（0 条）**，由 UDC-MERGE 任务照抄本文件。

## 结论：0 条 + 真空说明
UDC 5.3.517 域内 0 条真 BI 只读契约（详见同目录 `bi-vacuum-contract.md` 7 要素负证据 + `docs/audit/artifacts/udc-bi-5.3.517/` 扫描/javap 证据）。
因此 MERGE 任务在本域 registry 上**不追加** UdcOperationContract 条目；本文件仅登记「真空」这一事实，避免后续误以为漏扫。

**真空的三层证据口径（R2 收口，取代此前的单层类名扫描说法）**:
1. **类名层**: 6 jar / 1217 class（.class 条目含内部类；顶层类去 `$` = 1111）× 13 BI 关键词宽口径子串 → 真 BI controller/服务 0；`bi` 子串 29 条逐条排除（biginteger/integer/bill/biz/scalability/combination/compatibility + `BiLinkedList` 已 `javap -p -v` 确认为通用双端链表）。
2. **端点路径字面量层**: mapping-bearing 类 **38** 个（customplan 6 + dataflow 5 + runtime 27；common/facade/lowcode = 0）→ 端点行 **219 条**（35 类级基路径 + 184 方法级）**逐条判定**，CANDIDATE(真 BI) = **0**，4 条伪命中全为 `stat` 词干被 state/status 包含。证据 = `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md` §0/§3/§3.1 + 38 个 `r1-<Class>.javap.txt`。
3. **常量池全量层**: 1217 类全部常量池 Utf8（含中文）BI 词干扫描、排除伪命中族后 84 条，**其中属于 mapping-bearing 类的 = 0 条**； bearing 类 `/` 开头字面量的 2 条未过滤命中与端点表完全重复 → 常量池层无端点表之外的新路径。证据 = `bi-endpoint-literal-scan.md` §5 + `r1_step5_completeness.json`。
   - 双口径一致性: 自实现常量池/注解解析 vs `javap -p -v` 解码文本，**38/38 类 mismatch = 0**。
   - 该层的「报表/数据集」邻近词属 **OBSERVATION**（被引用/被导航的对象类型，无端点声明），不得据此把本域升级为「BI 承载模块在外部构件」的 FACT。

**可复跑（MERGE 若需复核，禁改 `components/platform_operations/registry.py`）**: `docs/audit/artifacts/udc-bi-5.3.517/` 下 6 个脚本 `r1_scan_mapping_bearing.py` / `r1_extract_endpoints.py` / `r1_javap_dump.py` / `r1_completeness_checks.py` / `r1_build_report.py` / `r1_bi_judge.py`（末件自述 =「R1 步骤4: 生成端点全量表 + BI 语义判定」，是 `r1_step4_bi.json` 即伪命中判定口径的生成者；R3 D-2 补齐枚举，此前漏列该件）；`javap` 必须带 `-J-Dstdout.encoding=UTF-8`；筛类必须按映射注解描述符（按 `@RestController` 筛只有 35 类、会漏 53 行端点）。


## MERGE 照抄指令
- 新增条目数: **0**
- registry 变更: **无**（`contracts["udc.bi.*"]` 不写入）
- 备注: 若 MERGE 需要显式占位以便审计可追溯，可写一条 status=`OperationStatus.UNKNOWN`、write=False 的哨兵（不推荐；本任务默认不加哨兵，保持 0 条纯净）。

## 未来补齐的证据入口（供 MERGE 参考，不实际写 registry.py）
若未来 BI 模块 jar / 部署态可得，把契约转正时，单条 UdcOperationContract 的证据风格（照抄 registry.py 现有 microflow/datatype/applog 条目）如下。

**UdcOperationContract 字段（权威签名，`components/platform_operations/models.py:29-40` —— 29 = `@dataclass` 装饰行、30 = class 行、31–40 = 10 个字段；`components/platform_operations/registry.py:40/44/46/49/51` 以位置参数调用）:**
```python
UdcOperationContract(
    operation_id,      # 1 str
    method,            # 2 str（只读契约 = "GET"）
    path,              # 3 str（控制器原值，禁拼网关前缀）
    request_type,      # 4 str
    response_type,     # 5 str
    status,            # 6 OperationStatus（离线=VERIFIED_STATIC_BYTECODE 或 UNKNOWN）
    write,             # 7 bool（只读=False）
    evidence,          # 8 list[dict]
    required_inputs,   # 9 tuple[str, ...]
    verification_rules # 10 tuple[str, ...]
)
```
> 事实注记（reversible，非验收变更）: main/ROUTE.md 文案称「11 参签名」；权威源 `models.py` 实际为 **10 字段** dataclass（registry.py 位置调用亦为 10 参）。本文件按权威源 10 参写，供 MERGE 照抄。

**evidence dict 风格（照抄 registry.py:45/48/50）:**
```python
{
    "source": "local-maven-53517",
    "artifact": "<bi-module>-<ver>.jar",
    "version": "<ver>",
    "class": "com.seeyon...BIXxxController",
    "method": "getXxx",
    "class_sha256": "<整 class 的 sha256, 逐字节实测>",
    "javap": "docs/audit/artifacts/udc-bi-<ver>/<Class>.javap.txt",
    "evidence_level": "VERIFIED_STATIC_BYTECODE",
}
```

**未来转正示例（仅示意，占位值，MERGE 拿到真 BI jar 后替换）:**
```python
contracts["udc.bi.<op>"] = UdcOperationContract(
    "udc.bi.<op>", "GET", "<controller 原值路径, 禁拼网关前缀>",
    "<request 形态>", "<SingleResponse<XXDto>>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [ {evidence dict, 如上} ],
    ( "<入参名>", ),
    ( "同一 target 回读 identity_matches", "响应非空 XXDto 列表",
      "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）" ),
)
```

## 未改任何冻结文件
本文件与 `bi-vacuum-contract.md` 均为本域新目录 `docs/operation-contracts/udc/bi/` 下的建议/负证据件；`components/platform_operations/registry.py` / `components/platform_operations/layer.py` / `seeyon_cli.py` / `tests/*` 一律未触（MERGE 任务统一落库）。

## 追加节 · 5.3.260 独立版本单元（R7，HUMAN 2026-10-08 13:56 授权）

> 本节为**追加**，不改写上文「0 条」正文与 5.3.517 单元判定。字段 = `components/platform_operations/models.py:31-40` 的 **10 字段同名同序**（29=装饰行 / 30=class 行 / 31–40=字段）；`write=False`；**evidence 内 version = 5.3.260**。
> 结论 = **非真空（5.3.260 单元）**: 只读形态候选 5 条，逐条构造参数如下。命名冲突核对（只读 grep `registry.py`）= 5 个 id 均**净新增**，且 `udc.bi.*` 前缀现存 **0** 条。

```python
contracts["udc.bi.ganttchart_running_dynamic_select_by_entity"] = UdcOperationContract(
    "udc.bi.ganttchart_running_dynamic_select_by_entity", "POST", "gantt-chart/dynamic-select-by-entity",
    "ListRequest", "ListResponse<java.lang.Object>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartRunningController", "method": "dynamicSelectByEntity", "class_sha256": "8d43516d96edfb6c38ef7a9c8a5cdb1e00c9cdf03a8be47d2025b84ff0176f84", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartRunningController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("entity 查询条件(ListRequest)",),
    ("同一入参二次回读 identity_matches", "响应为 ListResponse<java.lang.Object> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"),)
```

```python
contracts["udc.bi.ganttchart_schema_select_by_id"] = UdcOperationContract(
    "udc.bi.ganttchart_schema_select_by_id", "POST", "gantt-chart-schema/select-by-id",
    "java.lang.Long", "SingleResponse<setting.GanttChartSchemaDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectById", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("id",),
    ("同一入参二次回读 identity_matches", "响应为 SingleResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"),)
```

```python
contracts["udc.bi.ganttchart_schema_select_by_code"] = UdcOperationContract(
    "udc.bi.ganttchart_schema_select_by_code", "GET", "gantt-chart-schema/{code}",
    "java.lang.String", "SingleResponse<setting.GanttChartSchemaDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectByCode", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("code", "方案编码",),
    ("同一入参二次回读 identity_matches", "响应为 SingleResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"),)
```

```python
contracts["udc.bi.ganttchart_schema_search_list"] = UdcOperationContract(
    "udc.bi.ganttchart_schema_search_list", "POST", "gantt-chart-schema/search-list",
    "java.util.Map<java.lang.String, java.lang.Object>, Sort", "ListResponse<setting.GanttChartSchemaDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectByConditions", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("conditions(Map)", "sort",),
    ("同一入参二次回读 identity_matches", "响应为 ListResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"),)
```

```python
contracts["udc.bi.ganttchart_schema_search"] = UdcOperationContract(
    "udc.bi.ganttchart_schema_search", "POST", "gantt-chart-schema/search",
    "PageInfo, java.util.Map<java.lang.String, java.lang.Object>, Sort", "PageResponse<setting.GanttChartSchemaDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53260", "artifact": "boot-starter-ganttchart-5.3.260.jar", "version": "5.3.260", "class": "com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController", "method": "selectPageByConditions", "class_sha256": "cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb", "javap": "docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("conditions(Map)", "sort",),
    ("同一入参二次回读 identity_matches", "响应为 PageResponse<setting.GanttChartSchemaDto> 非空（或条件致空亦自证）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"),)
```

**注（供 MERGE）**: 位置 4 `request_type` 取描述符入参侧原值、位置 5 `response_type` 取声明返回类型原值（含泛型），二者均来自 javap；POST 形态 + `write=False` 与既有 `registry.py:55-58` 风格一致。本节**不实际修改 `registry.py`**（冻结件）。

