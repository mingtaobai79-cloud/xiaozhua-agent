# 流程域(BPM集成) 只读操作契约 — flow-contracts.md
- 轮次: R2 (P1 证据+契约) | 证据单元: 本地 Maven 5.3.517（全离线，禁相邻版本混写，禁 LIVE/连网关）
- 证据底座: docs/audit/artifacts/udc-flow-5.3.517/（3 jar class-list + 5 controller javap -p -v 全量 + manifest.txt）
- class_sha256 一律取 manifest.txt 实测值（sha256_r2.py 落盘时 zipfile 读 .class 字节，非记忆）。
- 控制器原路径 = 类级 @RequestMapping value + 方法级 @*Mapping value，逐字拼接，**不拼任何网关前缀**。
- 只读契约 9 条（≥4 达标）+ 写侧 3 条单列「登记 write=true 未放开」，写侧不混入只读计数。

## 只读契约（9 条）

### R2-C1 · BpmNodeInfoController.selectByComplexCondition
- operation_id: udc.flow.bpm_node_info_search
- HTTP method: POST
- 控制器原路径: node-info/search
- 参数形态: @RequestBody CBpmNodePermissionRequestDto（com.seeyon.boot.starter.customplan.dto）；方法内从 RequestContext.get().getUserId() 回填 userId（不信任入参 userId）
- 返回 DTO: com.seeyon.boot.transport.SingleResponse<com.seeyon.bpm.dto.BpmNodePermission4PageDto>
- evidence: artifact=udc-starter-customplan / version=5.3.517 / class=com.seeyon.boot.starter.customplan.controller.BpmNodeInfoController / method=selectByComplexCondition / class_sha256=95e1752d83c9152e6236d825b2aaea1e82fd60516b1f7c2a3c2f2249df395bb2
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务可达 + 有效 UDC 会话 token + 指定 appCode/节点参数；回读判定 BpmNodePermission4PageDto 列表非空且含 nodeId 字段。

### R2-C2 · UdcFunctionNodeController.selectFunctionNodeTreeMetaData
- operation_id: udc.flow.function_node_tree
- HTTP method: GET
- 控制器原路径: udc-runtime/meta-data/select-function-node-tree/{appName}
- 参数形态: @PathVariable appName（String，路径占位 {appName}）
- 返回 DTO: com.seeyon.boot.transport.ListResponse<com.seeyon.udc.common.dto.UdcFunctionNodeMetadataDto>
- evidence: artifact=udc-starter-runtime / version=5.3.517 / class=com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController / method=selectFunctionNodeTreeMetaData / class_sha256=efd8f9143d0fd44d4e3033a4bb4877c09e891a1049f66382df1ae1d7d08a7748
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 真实 appCode；判定 ListResponse.data 非空且含 nodeName/nodeType 字段。

### R2-C3 · UdcFormDataQueryController.queryFormData
- operation_id: udc.flow.form_data_query
- HTTP method: POST
- 控制器原路径: udc-runtime/data/query
- 参数形态: @RequestBody EntityDataRequestDto（com.seeyon.boot.starter.udcrt.dto）
- 返回 DTO: com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.EntityDataResponseDto>
- evidence: artifact=udc-starter-runtime / version=5.3.517 / class=com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController / method=queryFormData / class_sha256=cabd312210665274361568181b6d41b9a86f7ed13f1dba7e3f844dc2e5ea5584
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 合法 entityCode/业务键；判定 EntityDataResponseDto.dataMap 命中目标实体。

### R2-C4 · DataFlowRtMapController.selectById
- operation_id: udc.flow.data_flow_map_get_by_id
- HTTP method: GET
- 控制器原路径: udc-runtime/data-flow-map/{id}
- 参数形态: @PathVariable id（Long，路径占位 {id}）
- 返回 DTO: com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.dataflow.dto.DataFlowRtMapDto>
- evidence: artifact=udc-starter-dataflow / version=5.3.517 / class=com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController / method=selectById / class_sha256=455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 已存在的 dataFlowMap 主键；判定 SingleResponse.data.id 与入参一致。

### R2-C5 · DataFlowRtMapController.selectByCondition
- operation_id: udc.flow.data_flow_map_search
- HTTP method: POST
- 控制器原路径: udc-runtime/data-flow-map/search
- 参数形态: @RequestBody DataFlowRtMapQueryDto（com.seeyon.boot.starter.dataflow.dto）
- 返回 DTO: com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.dataflow.dto.DataFlowRtMapDto>
- evidence: artifact=udc-starter-dataflow / version=5.3.517 / class=com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController / method=selectByCondition / class_sha256=455df593d43558055e01d69f4aacc70ce337ec80b4f7275adc471c49a22d1d95
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 有效过滤条件；判定 ListResponse.data 列表与过滤条件匹配。

### R2-C6 · DataFlowRtMappingController.selectById
- operation_id: udc.flow.data_flow_mapping_get_by_id
- HTTP method: GET
- 控制器原路径: udc-runtime/data-flow-mapping/{id}
- 参数形态: @PathVariable id（Long，路径占位 {id}）
- 返回 DTO: com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.dataflow.dto.DataFlowRtMappingDto>
- evidence: artifact=udc-starter-dataflow / version=5.3.517 / class=com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController / method=selectById / class_sha256=ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 已存在的 dataFlowMapping 主键；判定 SingleResponse.data.id 与入参一致。

### R2-C7 · DataFlowRtMappingController.selectOriginalMappingList
- operation_id: udc.flow.data_flow_mapping_search_original
- HTTP method: POST
- 控制器原路径: udc-runtime/data-flow-mapping/search-original
- 参数形态: @RequestBody OriginalDataFlowMappingListQueryDto（com.seeyon.boot.starter.dataflow.dto）
- 返回 DTO: com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.dataflow.dto.DataFlowRtMappingDto>
- evidence: artifact=udc-starter-dataflow / version=5.3.517 / class=com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController / method=selectOriginalMappingList / class_sha256=ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 有效源映射查询条件；判定列表非空。

### R2-C8 · DataFlowRtMappingController.selectMappingInitData
- operation_id: udc.flow.data_flow_mapping_init_data
- HTTP method: POST
- 控制器原路径: udc-runtime/data-flow-mapping/init-data
- 参数形态: @RequestBody DataFlowMappingInitQueryDto（com.seeyon.udc.common.dto）
- 返回 DTO: com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.dataflow.dto.DataFlowRtEditInitialDataDto>
- evidence: artifact=udc-starter-dataflow / version=5.3.517 / class=com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController / method=selectMappingInitData / class_sha256=ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 合法初始化查询；判定编辑初始数据字段齐备。

### R2-C9 · DataFlowRtMappingController.selectDetailByCondition
- operation_id: udc.flow.data_flow_mapping_detail
- HTTP method: POST
- 控制器原路径: udc-runtime/data-flow-mapping/detail
- 参数形态: @RequestBody DataFlowOriginalMappingQueryDto（com.seeyon.boot.starter.dataflow.dto）
- 返回 DTO: com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.dataflow.dto.DataFlowRtMappingDto>
- evidence: artifact=udc-starter-dataflow / version=5.3.517 / class=com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController / method=selectDetailByCondition / class_sha256=ee742c7031134a77d5ae0d10b1e3fee06e86335e0985e05d5c845e83951531e8
- LIVE 回读条件（本轮不做）: 需 5.3.517 服务 + 有效 token + 合法详情查询；判定 SingleResponse.data 返回目标映射详情。

## 写侧候选（单列，登记 write=true 未放开，不混入只读契约计数）
| 类 | 方法 | HTTP | 控制器原路径 | 参数 | 返回 | 处置 |
|---|---|---|---|---|---|---|
| DataFlowForBpmController | fillErrorFlowData | POST | udc-runtime/bpm/fill-data | @RequestBody FillFlowReqDto | SingleResponse<Boolean> | 写/填流转错误数据，write=true，仅登记不放开 |
| DataFlowRtMappingController | update | POST | udc-runtime/data-flow-mapping/update | @RequestBody DataFlowRtMappingSaveDto | SingleResponse<DataFlowRtMappingDto> | 写，write=true，仅登记 |
| DataFlowRtMappingController | updateMappingState | POST | udc-runtime/data-flow-mapping/state | @RequestBody DataFlowMappingStateUpdateDto | SingleResponse<OperationResultDto> | 写，write=true，仅登记 |

> 注：R2-C2（udc.flow.function_node_tree）与并发微流程会话 registry.py 已登记的 udc.microflow.function_node_tree 共享同一 controller+method（UdcFunctionNodeController.selectFunctionNodeTreeMetaData）→ 跨域重叠，registry-entries.md 单独标注去重归一。
