# UDC 扣减规则 / 生单规则 —— 数据模型与权威契约（MySQL LIVE + CFR）

> 2026-10-16。来源：test2 MySQL 直连（本应用 8704025620829192834 真实数据）+ udc-dataflow-5.3.517.jar cfr 反编译。

## 1. 表族（15 张）

| 表 | 行数(本环境) | 角色 |
|---|---|---|
| `udc_deduction_map` | 1 | 扣减映射（顶层容器） |
| `udc_deduction_rule` | 1 | 扣减规则（主表） |
| `udc_deduction_rule_detail` | 0 | 规则明细（单据状态/校验/通知） |
| `udc_deduction_algorithm` | 1 | 扣减算法（字段间运算） |
| `udc_deduction_id_mapping` | 0 | 规则迁移时的 id 映射 |
| `udc_rt_deduction_*` | 0 | 运行态（*_rt_*）对应表 |
| `udc_data_flow` | 59 | 生单规则主表 |
| `udc_data_flow_mapping` | 56 | 生单规则字段映射 |
| `udc_rt_data_flow_*` | 0 | 生单规则运行态 |

`*_rt_*` 前缀 = 运行态；无前缀 = 设计态。**设计态权威源 = 无前缀表**。

## 2. 扣减规则四层结构

    udc_deduction_map (id)  ←── deduction_map_id ──  udc_deduction_rule
                                                         │
                                                         ├── search_condition (JSON)
                                                         ├── extend_info (JSON)
                                                         └── id ── deduction_rule_id ──> udc_deduction_rule_detail
                                                                                          └── deduction_algorithm_id ──> udc_deduction_algorithm (algorithm_content JSON)

### 2.1 udc_deduction_rule 关键列

`id, app_id, caption, name, deduction_map_id, order_no, runtime_modify_state,
 search_condition, extend_info, source_entity_id, source_end_entity_id,
 target_entity_id, target_end_entity_id, source_entity_full_name, ...`
（`source_entity_id`=起点实体, `source_end_entity_id`=终点实体；target 同构——支持链路扣减）

### 2.2 search_condition（配对的正式形态）

    [{
      "validate": true,
      "searchMethod": "EQUAL",
      "target": { "validate": true, "fixedValue": null,
                  "attributeFullName": "com.seeyon.<app>.domain.entity.<Entity>.<attr>",
                  "attributeId": <bigint> },
      "source": { "validate": true, "fixedValue": null,
                  "attributeFullName": "...<attr>", "attributeId": <bigint> },
      "uuid": "sc-1"
    }]

**注意**：`target` 与 `source` 各自独立给 `attributeFullName`/`attributeId`，**未配对时也能落库**（无校验配对）。`attributeFullName` 用 **domain.entity** 前缀（不是 dto）。

### 2.3 extend_info

    { "validate": true,
      "conditionExt": { "validate": true, "dataNotFoundStrategy": "ERROR", "toast": "" } }

`dataNotFoundStrategy`：`ERROR`（找不到数据报错）/ 其它值见面板。

### 2.4 algorithm_content（扣减算法）

    [{
      "validate": true,
      "target": { "validate": true, "fixedValue": null,
                  "attributeFullName": "...<Entity>.expNum", "attributeId": <bigint> },
      "source": { "validate": true, "fixedValue": null,
                  "attributeFullName": "...<Entity>.expNum", "attributeId": <bigint> },
      "operatorEnum": "SUBTRACT_EQUAL",
      "uuid": "ac-1"
    }]

`operatorEnum` 实测值：`SUBTRACT_EQUAL`（-=）。`target`=被改写的字段，`source`=运算来源字段。

### 2.5 udc_deduction_rule_detail（明细，可为空）

`bill_status_info`（单据状态）、`check_rule`（校验规则）、`notice`（通知）、`deduction_algorithm_id`。

### 2.6 udc_deduction_map

`id, caption, definition, source_entity_id, source_entity_full_name, order_no`
—— 本环境该行为 `caption=1, definition=NULL`（骨架态，未配画布）。

## 3. 生单规则（udc_data_flow）

- 主表 `udc_data_flow`：`id, app_id, caption, definition(画布), source_entity_id, target_entity_id, trigger_point, bind_event, source_entity_full_name, target_entity_full_name`
- 映射表 `udc_data_flow_mapping`：`rule_info`（三层契约 validate/rules[]/operationType/entityMappingRelation）+ `definition` 画布
- `definition` 画布 nodes 用 `id_<entityId>` 格式 + `lines`(M path) + `transform{x,y,scale}`
- mapping `field` 五键：`validate/entityId/entityFullName/attributeId/attributeFullName`

## 4. 与微流程节点面板的对应

微流程编辑器左侧分组（真机实测）：
`微流程 / 生单规则 / 扣减规则 / 默认分组`
—— 生单规则与扣减规则是**独立于微流程的规则类型**，节点面板不覆盖它们；需各自的编辑器入口与 REST 契约。

## 5. REST op 全清单（bundle 权威，实测）

### 5.1 扣减规则（16 个）
`udcDeductionMapGet / udcDeductionMapPost / udcDeductionMapUpdatePost / udcDeductionMapDeletePost /
 udcDeductionMapDeleteContentPost / udcDeductionMapAppAppGet /
 udcDeductionRuleSearch / udcDeductionRuleGet / udcDeductionRulePost / udcDeductionRuleUpdatePost /
 udcDeductionRuleDeletePost / udcDeductionRuleInitDataPost / udcDeductionRuleCountPost /
 udcDeductionValidRulePost / udcDeductionEntityListPost / udcDeductionEntityNotExistIdsPost`

### 5.2 生单规则（5 + 复用）
`udcDataFlowListApplicationAppGet / udcDataFlowListEventEntityPost / udcDataFlowListEventsPost /
 udcDataFlowDeleteContentPost / udcDataFlowEntityNotExistIdsPost`
（写链复用 `udcMicroflowCheckSchemaUpdatePost` 等）

### 5.3 微流程（核心）
`udcMicroflowFindByIdGet / udcMicroflowSearch / udcMicroflowCreatePost / udcMicroflowUpdatePost /
 udcMicroflowDeletePost / udcMicroflowCheckSchemaUpdatePost / udcMicroflowCheckMicroFlowCaptionPost /
 udcMicroflowRecoverPost / udcMicroflowFindNodesGet / udcMicroflowBatchMovePost /
 udcMicroflowUpdateOrderNoAndGroupPost / udcMicroflowDisableNodePost`
分组：`udcMicroFlowGroupCreatePost/UpdatePost/DeletePost/DeleteBatchPost/BatchMovePost/SelectByTypePost`
引用重构：`udcMicroflowRefactorRefactoredPost / udcMicroflowRefactorResolveNodesReferenceRelationshipsPost`
调用链：`udcMicroflowFindCallInfoUpstreamPost / udcMicroflowFindCallInfoDownstreamPost`
查询类：`udcMicroflowFindCustomDtoPost / udcMicroflowFindDtoByEntityPost / udcMicroflowSearchEntityRulePost /
 udcMicroflowSearchEnumByAppNamePost / udcMicroflowSearchTreeEntityPost / udcMicroflowTreeEntityDtoPost /
 udcMicroflowBatchFindAggDtoPost / udcMicroflowBatchFindJavaEnumPost / udcMicroflowFindFullAggDtoPost /
 udcMicroflowCheckDtoMetadataExistPost / udcMicroflowSearchNonEntityDtoPost`
消息/事件：`udcMicroflowSearchEventListPost / udcMicroflowSearchMicroFlowEventAppGet /
 udcMicroflowSearchMessageDtoPost / udcMicroflowSearchMicroFlowMessageAppGet / udcMicroflowSelectMessageGet /
 udcMicroflowCreateMessagePost / udcMicroflowUpdateMessagePost / udcMicroflowMessageDtoDeletePost /
 udcMicroflowFilterEventPost / udcMicroflowFilterMqPost / udcMicroflowFilterNotVirtualPost /
 udcMicroflowSearchSendMqListPost / udcMicroflowSearchRestExcludeBootPost`
服务：`udcMicroflowSearchAppsPost / udcMicroflowSearchAppServiceByAppNamePost /
 udcMicroflowSearchAppServicePost / udcMicroflowSearchAppServiceByNamePost / udcMicroflowSearchMethodByNamePost /
 udcMicroflowServiceListPost / udcMicroflowServiceFrontendListPost / udcMicroflowServiceListSubMfPost /
 udcMicroflowServiceDetailsGet / udcMicroflowServiceDetailsDynamicPost / udcMicroflowServiceCommonInputListPost`

## 6. 待办

- `udc_deduction_rule_detail` 有数据时的真实形态（本环境 0 行，需从其他应用取样）
- 生单规则 `UDC_DATAFLOW_0043`（`DataFlowDataCheckUtil` 抛出点）修复
- 扣减规则写链实测（`udcDeductionRuleUpdatePost`）
