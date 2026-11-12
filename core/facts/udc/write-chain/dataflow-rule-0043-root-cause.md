# UDC 生单规则 —— 0043 根因闭环与权威写链契约

> 2026-10-16。LIVE（CDP 抓包 + GraphQL 实测）+ CFR（udc-dataflow-5.3.517）双证。

## 1. `UDC_DATAFLOW_0043` 根因（已定位到字节码行）

抛出点 `com.seeyon.udc.dataflow.utils.DataFlowDataCheckUtil`:

    public static void assertNull(Object dto, String fullName, DataFlowObjectNotExistEnum type) {
        if (Objects.isNull(dto)) {
            log.error("已经不存在，fullName：{}", fullName);
            throw new BusinessException("UDC_DATAFLOW_0043", new String[]{type.getText()});
        }
    }

唯二调用者 = `dataCheck4Field(DataFlowMappingFieldDto fieldDto, EntityData4DataFlowCheckBo checkBo, boolean source)`：

    if (fieldDto.getEntityId() == null)      throw UDC_DATAFLOW_0003 ["entityId"];
    type = source ? SOURCE_ENTITY : TARGET_ENTITY;
    assertNull(checkBo.getEntity(fieldDto.getEntityId()), fieldDto.getEntityFullName(), type);   // ← 0043 此处
    if (fieldDto.getAttributeId() == null)    throw UDC_DATAFLOW_0003 ["attributeId"];
    attributeDto = checkBo.getAttributeDto(fieldDto.getAttributeId());
    attrType = source ? SOURCE_FIELD : TARGET_FIELD;
    assertNull(attributeDto, fieldDto.getAttributeFullName(), attrType);                          // ← 0043 此处

**0043 = mapping field 的 entityId/attributeId 在 checkBo 里解析不到**（不是 definition 缺失）。

`msg` 文本对应 `DataFlowObjectNotExistEnum.getText()`：源实体/源字段/目标实体/目标字段。

## 2. 此前误判的根因链（自我纠正）

1. 我此前把 mapping 的 `rule_info`（`{validate, rules}`）**发到了 `definition` 字段**。
2. 查库发现 `udc_data_flow_mapping` **没有 `definition` 列**（列清单：`rule_info` 才是）。
3. 本轮查询 `udcDataFlowGet` 响应：`definition` = **画布**（`{lines, nodes, transform}`，nodes 形如 `id_<entityId>`）。
4. 结论：`udc_data_flow.definition` = 画布；`udc_data_flow_mapping.rule_info` = `mappingDetailDto`（`{validate, rules}`）。
   把 `{validate, rules}` 塞进 `definition` ⇒ 画布解析失败 ⇒ entityDto 无法从画布建立 ⇒ field 解析不到 ⇒ **0043**。

## 3. 权威契约（实测）

### 3.1 读
    query udcDataFlowMappingGet ($path: udcDataFlowMappingGetInputPath) {
      udcDataFlowMappingGet(path: $path) { code message status
        data { content { appId appName bindEvent bindEventCaption caption dataFlowId description id mappingDetailDto } } } }
    → variables: { "path": { "id": "<mappingId>" } }

**`mappingDetailDto` ≡ `udc_data_flow_mapping.rule_info`**（同构，已验证）。

    content 另含：createTime creator guid lastModifier
    mappingDetailDto.rules[] = { validate, operationType, keyAttribute[], autoProcess,
                                 entityMappingRelation[], mappingArea[], listSchema, writeBackRuleList[] }
    mappingArea[] = { uuid, checkRuleJson, entityFullName, entityId, conditionJson,
                      frontendConditionList[], mappingRow[], uuid }
    mappingRow[]   = { mappingMode("FieldCopy"), personalization, uuid,
                       source{validate, entityId, entityFullName, attributeId, attributeFullName, formulaJson, fixedValue{value,type,dataType,desc,extension}},
                       target{...同构...} }
    entityMappingRelation[] = { validate, targetEntity{validate,entityId,entityFullName},
                                sourceEntity[{validate,entityId,entityFullName}] }

### 3.2 写
    udcDataFlowMappingPost(body: udcDataFlowMappingPostInputBody)        # 新建
    udcDataFlowMappingUpdatePost(body: udcDataFlowMappingUpdatePostInputBody)  # 更新
    udcDataFlowMappingDeletePost(body: {id})                              # 删除
    → 返回 { affectCount, dataFlowMappingId, mappingsCount }

入参 body 字段（从 `udcDataFlowMappingGet` 响应结构反推）：
`appId, appName, caption, description, dataFlowId, id(更新时), triggerPoint, bindEvent,
 sourceAppId, sourceAppName, sourceEntityId, sourceEntityFullName,
 targetEntityId, targetEntityFullName, sourceEntitySearchConditionJson, mappingDetailDto`

### 3.3 其他生单规则 op（bundle 实测）
`udcDataFlowAppAppGet(path:{appId})` | `udcDataFlowGet(path:{id})` | `udcDataFlowListEntityPost(body:{appId})` |
`udcDataFlowListApplicationAppGet` | `udcDataFlowListEventEntityPost` | `udcDataFlowListEventsPost` |
`udcDataFlowListEventDataPost` | `udcDataFlowDeleteContentPost` | `udcDataFlowEntityNotExistIdsPost` |
`udcDataFlowMappingGet / Post / UpdatePost / DeletePost`

### 3.4 编辑器路由（真机实证）
- 列表：`/main/child-frame/udc/app-design/rule/dataflow/list?appId=<APP>`
- 画布：`/main/child-frame/udc/app-design/rule/dataflow/graph/<FLOW_ID>?appId=<APP>`
- 左侧分组：`微流程 / 生单规则 / 扣减规则`

## 4. 本应用现状（2026-10-17 09:04 +08 LIVE 复核）

- `udc_data_flow` 2 条：`908877618948883045`（小爪生单规则，画布=XzhExp950795→XzhVerifyEntity）、`8873356045797376451`（`caption=1`，definition=NULL 空壳）。REST `GET /service/udc/data-flow/908877618948883045` 返回 `HTTP 200 / BOOT_0000`；画布两个 node id 与实体 id 一致，`state=ON`，`publishState=UNPUBLISH`。
- `udc_data_flow_mapping` 1 条：`7702563982566312936`。本轮 REST `GET /service/udc/data-flow/mapping/7702563982566312936` 返回 `HTTP 200 / BOOT_0000`；顶层 `sourceEntityId=474806313816300867`、`targetEntityId=-6338668863907875875`，与 `entityMappingRelation`、`mappingArea`、mapping row 两端完全一致；`triggerPoint=MANUALLY`，`mappingRow` 为 `expFlag(BOOLEAN) → draft(BOOLEAN)`。此前“目标实体仍为源实体”的陈旧记录已被 `udcDataFlowMappingUpdatePost` 修正。
- `udc_deduction_*` 见 `deduction-and-dataflow-rules-model.md`；本轮 REST `GET /service/udc/deduction/rule/-2339240514292888379` 返回 `HTTP 200 / BOOT_0000`，规则与 1 个算法完整回读，仍为设计态 `publishState=UNPUBLISH`。

### 4.1 本轮检测结果与边界

- 触发 `udcApplicationDoDetectionPost`：`BOOT_0000/SUCCESS`，traceId `3277981860713466044`。
- 轮询状态返回 `FAIL`（连续 10 次），随后 `udcApplicationSearchDetectionPost` 返回 **0 条记录**。因此本轮不能把“0 条”升级为 `0 ERROR/0 WARN`；检测闭环状态应记为 `UNVERIFIED/FAIL（检测状态失败，结果集为空）`。
- 证据件：`docs/audit/artifacts/udc-node-evidence/live-rule0043-deduction-audit.json`；检测结果 `<HERMES_HOME>/cache/scratch/detect_result.json`（空数组）。
- 0043 的“定义/映射字段可解析”已由 REST 回读和本地实体/属性白名单核对支持；**尚未执行一次真实生单/扣减运行语义**，因此不能称执行态 LIVE PASS。

## 5. 铁律

1. **`udc_data_flow.definition` 只能放画布**（`{lines, nodes, transform}`，nodes.id = `id_<entityId>`）；放 `rule_info` 会 0043。
2. **`rule_info` 只能放在 `udc_data_flow_mapping.rule_info`**，且必须与 `mappingDetailDto` 同构。
3. mapping 的 `source_entity_id/target_entity_id/source_entity_full_name/target_entity_full_name` 必须与 `entityMappingRelation` 及画布一致，否则 checkBo 建不出实体 → 0043。
4. 写链用 `udcDataFlowMappingPost/UpdatePost`，**不是** `udcMicroflow*`。
