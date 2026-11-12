# registry-entries.md — 流程域(BPM集成) 只读契约 → UdcOperationContract 建议条目
- 供 UDC-MERGE 任务照抄，本轮不实际改 registry.py（registry.py 属冻结文件）。
- 字段照 components/platform_operations/models.py 的 UdcOperationContract 位置签名（frozen dataclass，10 字段按序）：
  `UdcOperationContract(operation_id, method, path, request_type, response_type, status, write, evidence, required_inputs, verification_rules)`
- status 一律 `OperationStatus.VERIFIED_STATIC_BYTECODE`；只读条 `write=False`；evidence 为 `list[dict]`（键: source/artifact/version/class/method/class_sha256/javap/evidence_level）；required_inputs / verification_rules 为 tuple。
- path 逐字 = 类级 @RequestMapping + 方法级 @*Mapping，不拼网关前缀；class_sha256 取 manifest.txt 实测值。

## 只读条目（9 条，write=False）

### 1. udc.flow.bpm_node_info_search
```python
contracts["udc.flow.bpm_node_info_search"] = UdcOperationContract(
    "udc.flow.bpm_node_info_search", "POST", "node-info/search",
    "CBpmNodePermissionRequestDto(SingleRequest)",
    "SingleResponse<BpmNodePermission4PageDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-customplan-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.customplan.controller.BpmNodeInfoController",
      "method": "selectByComplexCondition",
      "class_sha256": "95e1752d83c9152e6236d825b2aaea1e82fd60516b1f7c2a3c2f2249df395bb2",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/BpmNodeInfoController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("CBpmNodePermissionRequestDto(user_id 由 RequestContext 回填),",),
    ("同一条件回读节点权限 identity_matches", "响应 BpmNodePermission4PageDto 非空",
     "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

### 2. udc.flow.function_node_tree
> 【跨域重叠·必标注】本条 = UdcFunctionNodeController.selectFunctionNodeTreeMetaData，已被并发微流程会话登记为 `udc.microflow.function_node_tree`（registry.py L45-46，同 controller+method+同 class_sha256 efd8f914...）。UDC-MERGE 时去重归一，勿新增重复 operation_id —— 建议 MERGE 时将本 flow 域该操作归一到已存在的 `udc.microflow.function_node_tree`，不重复登记；若保留本域命名，须在 MERGE 时删一留一。
```python
# 与 udc.microflow.function_node_tree 同 controller+method+class_sha256，MERGE 去重归一
contracts["udc.flow.function_node_tree"] = UdcOperationContract(
    "udc.flow.function_node_tree", "GET", "udc-runtime/meta-data/select-function-node-tree/{appName}",
    "String appName(SingleRequest)",
    "ListResponse<UdcFunctionNodeMetadataDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController",
      "method": "selectFunctionNodeTreeMetaData",
      "class_sha256": "efd8f9143d0fd44d4e3033a4bb4877c09e891a1049f66382df1ae1d7d08a7748",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("appName",),
    ("同一 appName 回读节点树 identity_matches", "响应非空 UdcFunctionNodeMetadataDto 列表"))
```

### 3. udc.flow.form_data_query
```python
contracts["udc.flow.form_data_query"] = UdcOperationContract(
    "udc.flow.form_data_query", "POST", "udc-runtime/data/query",
    "EntityDataRequestDto(SingleRequest)",
    "SingleResponse<EntityDataResponseDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController",
      "method": "queryFormData",
      "class_sha256": "cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/UdcFormDataQueryController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("EntityDataRequestDto(entity_code+业务键),",),
    ("同一业务键回读实体数据 identity_matches", "响应 EntityDataResponseDto 命中目标实体"))
```

### 4. udc.flow.data_flow_map_get_by_id
```python
contracts["udc.flow.data_flow_map_get_by_id"] = UdcOperationContract(
    "udc.flow.data_flow_map_get_by_id", "GET", "udc-runtime/data-flow-map/{id}",
    "Long id(SingleRequest)",
    "SingleResponse<DataFlowRtMapDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController",
      "method": "selectById",
      "class_sha256": "455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("id",),
    ("同一 id 回读 dataFlowMap identity_matches", "响应 DataFlowRtMapDto.id 与入参一致"))
```

### 5. udc.flow.data_flow_map_search
```python
contracts["udc.flow.data_flow_map_search"] = UdcOperationContract(
    "udc.flow.data_flow_map_search", "POST", "udc-runtime/data-flow-map/search",
    "DataFlowRtMapQueryDto(SingleRequest)",
    "ListResponse<DataFlowRtMapDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController",
      "method": "selectByCondition",
      "class_sha256": "455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMapController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("DataFlowRtMapQueryDto(过滤条件),",),
    ("同一过滤条件回读列表 identity_matches", "响应非空 DataFlowRtMapDto 列表"))
```

### 6. udc.flow.data_flow_mapping_get_by_id
```python
contracts["udc.flow.data_flow_mapping_get_by_id"] = UdcOperationContract(
    "udc.flow.data_flow_mapping_get_by_id", "GET", "udc-runtime/data-flow-mapping/{id}",
    "Long id(SingleRequest)",
    "SingleResponse<DataFlowRtMappingDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController",
      "method": "selectById",
      "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("id",),
    ("同一 id 回读 dataFlowMapping identity_matches", "响应 DataFlowRtMappingDto.id 与入参一致"))
```

### 7. udc.flow.data_flow_mapping_search_original
```python
contracts["udc.flow.data_flow_mapping_search_original"] = UdcOperationContract(
    "udc.flow.data_flow_mapping_search_original", "POST", "udc-runtime/data-flow-mapping/search-original",
    "OriginalDataFlowMappingListQueryDto(SingleRequest)",
    "ListResponse<DataFlowRtMappingDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController",
      "method": "selectOriginalMappingList",
      "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("OriginalDataFlowMappingListQueryDto(源映射条件),",),
    ("同一条件回读源映射列表 identity_matches", "响应非空 DataFlowRtMappingDto 列表"))
```

### 8. udc.flow.data_flow_mapping_init_data
```python
contracts["udc.flow.data_flow_mapping_init_data"] = UdcOperationContract(
    "udc.flow.data_flow_mapping_init_data", "POST", "udc-runtime/data-flow-mapping/init-data",
    "DataFlowMappingInitQueryDto(SingleRequest)",
    "SingleResponse<DataFlowRtEditInitialDataDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController",
      "method": "selectMappingInitData",
      "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("DataFlowMappingInitQueryDto(初始化条件),",),
    ("同一条件回读编辑初始数据 identity_matches", "响应 DataFlowRtEditInitialDataDto 字段齐备"))
```

### 9. udc.flow.data_flow_mapping_detail
```python
contracts["udc.flow.data_flow_mapping_detail"] = UdcOperationContract(
    "udc.flow.data_flow_mapping_detail", "POST", "udc-runtime/data-flow-mapping/detail",
    "DataFlowOriginalMappingQueryDto(SingleRequest)",
    "SingleResponse<DataFlowRtMappingDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, False,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController",
      "method": "selectDetailByCondition",
      "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("DataFlowOriginalMappingQueryDto(详情条件),",),
    ("同一条件回读映射详情 identity_matches", "响应 DataFlowRtMappingDto 返回目标详情"))
```

## 写侧条目（3 条，登记 write=True，策略门控未放开，MERGE 时仅入 registry 不启用）
```python
# DataFlowForBpmController.fillErrorFlowData（dataflow）
contracts["udc.flow.bpm_fill_error_data"] = UdcOperationContract(
    "udc.flow.bpm_fill_error_data", "POST", "udc-runtime/bpm/fill-data",
    "FillFlowReqDto(SingleRequest)", "SingleResponse<Boolean>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, True,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowForBpmController",
      "method": "fillErrorFlowData",
      "class_sha256": "8b31f788f981eaa9a1ee025b72410f9bf71b4dd214b6a8cb3e41d566103ba5e4",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowForBpmController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("FillFlowReqDto(流转错误数据),",),
    ("write=true 策略门控未放开", "仅登记，不进入只读契约计数"))

# DataFlowRtMappingController.update（dataflow）
contracts["udc.flow.data_flow_mapping_update"] = UdcOperationContract(
    "udc.flow.data_flow_mapping_update", "POST", "udc-runtime/data-flow-mapping/update",
    "DataFlowRtMappingSaveDto(SingleRequest)", "SingleResponse<DataFlowRtMappingDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, True,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController",
      "method": "update",
      "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("DataFlowRtMappingSaveDto(保存数据),",),
    ("write=true 策略门控未放开", "仅登记，不进入只读契约计数"))

# DataFlowRtMappingController.updateMappingState（dataflow）
contracts["udc.flow.data_flow_mapping_update_state"] = UdcOperationContract(
    "udc.flow.data_flow_mapping_update_state", "POST", "udc-runtime/data-flow-mapping/state",
    "DataFlowMappingStateUpdateDto(SingleRequest)", "SingleResponse<OperationResultDto>",
    OperationStatus.VERIFIED_STATIC_BYTECODE, True,
    [{"source": "local-maven-53517", "artifact": "udc-starter-dataflow-5.3.517.jar",
      "version": "5.3.517",
      "class": "com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController",
      "method": "updateMappingState",
      "class_sha256": "ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8",
      "javap": "docs/audit/artifacts/udc-flow-5.3.517/DataFlowRtMappingController.javap.txt",
      "evidence_level": "VERIFIED_STATIC_BYTECODE"}],
    ("DataFlowMappingStateUpdateDto(状态),",),
    ("write=true 策略门控未放开", "仅登记，不进入只读契约计数"))
```

## MERGE 说明
- 只读 9 条 write=False（计入「≥4 只读」验收）；写侧 3 条 write=True 单列，不混入只读计数。
- 第 2 条 udc.flow.function_node_tree 与微流程域 udc.microflow.function_node_tree 跨域重叠 → MERGE 去重归一（删一留一），勿新增重复 operation_id。
- 写侧 fillErrorFlowData 的 class_sha256=8b31f788…5e4 与 javap 全量（DataFlowForBpmController.javap.txt）已于 R4 补证落盘，evidence_level 升 VERIFIED_STATIC_BYTECODE，pending 已消除；写侧仍 write=True 策略门控未放开（仅登记，不进入只读计数），MERGE 若放开须另行授权。
- 【R7/R8 裁定·移交项 ④】`com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController`（runtime/proxy，无类级 @RequestMapping 前缀）：R7 字节码扫描真命中 proxy 层 flow/microflow 透明路径 = `create-bpm` / `update-bpm`（写侧）+ `dataflow/{entityName}/{restMappingName}` / `dataflow/{entityName}/{restMappingName}/dynamic/select` + `microflow/{microFlowName}` / `host/microflow/{microFlowName}`。主任务裁定**不扩流程域边界**（理由：microflow 属微流程域、create-bpm/update-bpm 为写侧非只读契约、本任务非目标"不评价其他域"）→ MERGE 时与微流程域合并裁定该 proxy controller，**勿入本域 6 controller 专属只读契约**；仅登记，本任务不落地、不构造 UdcOperationContract。

## R5 可构造性核验
脚本：`docs/audit/artifacts/udc-flow-5.3.517/registry-construct-check.py`（只 import models.py + 读本文件，绝不写 registry.py/layer.py/tests/冻结件）；stdout 落 `docs/audit/artifacts/udc-flow-5.3.517/registry-construct-check.txt`。
- 构造结果：**12/12 块 construct=OK，总判定 PASS**。块数核对：总 "UdcOperationContract(" 提及 14 处 = 代码块内 12（只读 9 + 写 3，可构造）+ 正文/示意 2（preamble 第 4 行签名示意 + R5 小节 L230 本句自身，各 1 处；非代码块，显式区分，不计入构造）；```python 围栏 10（只读 9 各 1 + 写侧 3 共用 1）。
- `.effective` 判定表（门控：status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} 且 write=False 且 method=="GET"）：
  - GET 只读 → **True**（3 条）：udc.flow.function_node_tree、udc.flow.data_flow_map_get_by_id、udc.flow.data_flow_mapping_get_by_id
  - POST 读型（write=False）→ **False**（6 条）：udc.flow.bpm_node_info_search、udc.flow.form_data_query、udc.flow.data_flow_map_search、udc.flow.data_flow_mapping_search_original、udc.flow.data_flow_mapping_init_data、udc.flow.data_flow_mapping_detail
  - 写型（write=True）→ **False**（3 条）：udc.flow.bpm_fill_error_data、udc.flow.data_flow_mapping_update、udc.flow.data_flow_mapping_update_state
- MERGE 门控说明（一句话）：『POST 只读条目 `.effective=False`，MERGE 时须走与普通只读 POST 相同的 auth_scope 通道，勿依赖 `.effective` 自动放行』。
