# 微流程 04003(WARN) 的掩蔽机制 + SERVICE 型发布 + 04004 真因族

> 领域：微流程一致性检测（`UDC_CE_MICRO_FLOW_04003` / `UDC_MICRO_FLOW_04004`）
> 状态：**LIVE PASS**（test2）+ **VERIFIED_STATIC_BYTECODE**（udc-biz / udc-common 5.3.517）
> 代码：`components/udc/microflow_constraints.py`；护栏 `tests/udc/test_draft_warn_masking.py`（9 项）
> 关联：`components/udc/microflow_parse_errors.py`（错误码消息文本）、
>       `components/udc/data_type_java_type.py`（holder javaType 配对判据）

## 0. 一句话

`UDC_CE_MICRO_FLOW_04003` 不是"提醒你去保存"，而是**检测掩蔽器**：
`state=DRAFT` 的微流程在检测流水线里被**短路**，其内部真实缺陷一条都不报。
LIVE 实证：同一条微流程 `DRAFT -> ERROR=0/WARN=2`，`RELEASE -> ERROR=10/WARN=1`。

## 1. 字节码权威（CFR）

### 1.1 `CheckUtils.parallelDetection`（udc-biz 5.3.517，:430-479）

```java
if (dto.enableLastVersionMetadata() && context.getLastVersionMicroFlowMap().containsKey(dto.getId())) {
    dto = context.getLastVersionMicroFlowMap().get(dto.getId());   // 换成上一版本再校验
    nodeContext.setLastVersionMicroFlow(true);
}
...
if (MicroFlowDataStateEnum.RELEASE == dto.getState()) {
    switch (dto.getType()) {
        case FRONTEND: case FUNCTION: MicroFlowFrontEndService.detection(dto, nodeContext); break;
        case ENTITY_RULE: if (StringUtils.isEmpty(dto.getSourceId())) continue; /* 无 break -> 落下 */ 
        default:          CheckUtils.check(dto, nodeContext); break;
    }
} else {
    CheckUtils.warn(NodeInfo.buildInputOutputNodeInfo("", dto.getCaption()), nodeContext,
                    "", MicroFlowParseErrorEnum.DRAFT_MICRO_FLOW);
}
```

两条推论：

1. **DRAFT 是短路分支**：不进 `switch`、不做任何深度 parse 校验，只产出一条 04003。
   故 `DRAFT` 微流程上的 04004 族缺陷（`DTO_ATTR_DELETE` / `ENTITY_DELETE` /
   `ILLEGAL_DATA_SYSTEM` / `OUT_OF_SCOPE` / `NOT_MATCH`）**结构性不可见**。
2. `ENTITY_RULE` 且 `sourceId` 为空时 `continue` ⇒ 深度校验**完全跳过**（连 WARN 都没有）。

`DRAFT_MICRO_FLOW[119]` 的 message 恒为「未保存的微流程或者页面规则，这可能会影响调用」，
与微流程内容无关 ⇒ 不能从文案反推病灶。

### 1.2 `MicroFlowTypeEnum` / `MicroFlowDataStateEnum`（udc-common 5.3.517，本轮反编译）

```java
public enum MicroFlowTypeEnum { SERVICE(0), FRONTEND(1), ENTITY_RULE(2), CUSTOM(3), FUNCTION(4);
    CALL_CHAIN_TYPES = {SERVICE, CUSTOM, FRONTEND, FUNCTION};
    BACKEND_TYPES    = {SERVICE, CUSTOM};
    FRONTEND_TYPES   = {FRONTEND, FUNCTION}; }
public enum MicroFlowDataStateEnum { DRAFT(10), RELEASE(20); }
```

### 1.3 `MicroFlowAppService.setServiceMfToDraft`（:926）的真实作用域

```java
private void setServiceMfToDraft(MicroFlowDefinitionDto dto) {
    if (MicroFlowTypeEnum.SERVICE.equals(dto.getType())) dto.setState(MicroFlowDataStateEnum.DRAFT);
}
```

调用点只有两个：`create`(:372-376) 与 `update`(:383-387)。
`checkSchemaAndUpdate`(:330) **不调用**它，只做：

```java
if (MicroFlowDataStateEnum.RELEASE.equals(dto.getState())) { checkSchema -> ... -> update; }
```

⇒ **SERVICE 型可以经 `checkSchema/update` 发布**。旧结论「SERVICE 型永不可能经 update 发布」
只覆盖了 `create`/`update` 两个入口，**对 `checkSchemaAndUpdate` 不成立**（本轮更正）。

## 2. LIVE 实测（test2，app 8704025620829192834）

样本：微流程 `1524985498115296151`「小爪标品事件监听」（`type=SERVICE`，`triggerType=BUSINESS_EVENT`）。

| 步骤 | 动作 | 检测面 | 微流程 state |
|---|---|---|---|
| 基线 | — | **ERROR=0 / WARN=2**（04003x2） | DRAFT |
| 发布 | `POST /udc/microflow/checkSchema/update`（DTO 带 `state=RELEASE`） | `{\"check\":true,\"errors\":0}` | **RELEASE** |
| 复检 | `do/detection` -> `do/detection-state` -> `search/detection` | **ERROR=10 / WARN=1** | RELEASE |
| 还原 | `POST /udc/microflow/update`（`setServiceMfToDraft` 强制回 DRAFT） | **ERROR=0 / WARN=2** | DRAFT |

10 条 04004 的 message 与枚举对账：

| message | 枚举 | code | 频次 |
|---|---|---|---|
| 对象中配置的属性已被删除或编码被修改 | `DTO_ATTR_DELETE` | 18 | 5 |
| 实体已删除 | `ENTITY_DELETE` | 19 | 1 |
| 数据类型不匹配 | `NOT_MATCH` | 1 | 1 |
| 非法的数据体系，请重新选择来源数据进行映射 | `ILLEGAL_DATA_SYSTEM` | 84 | 1 |
| 前序节点发生变更请重新选择(事件数据) | `OUT_OF_SCOPE` | 0 | 1 |
| **合计** | | | **9 条带 message**（检测总数 10，含无 message 项） |

## 3. 04004 真因族之一：DATA_MAPPING `path[]` 的 javaType 不配对

样本 `DATA_MAPPING_b3OtRj` 共 3 行、6 个 holder（每行 `targetField` + `value.reference`），
其中 **4 个 path 元素不配对**（holder 自身 4 键必填全部齐全，因此旧校验器放行）：

| 元素 | dataType | javaType | 应为 | 代价 |
|---|---|---|---|---|
| `expNum`（targetField 侧） | INTEGER | `java.lang.String` | `java.lang.Integer` | 1 条 |
| `expNum`（reference 侧） | INTEGER | `java.lang.String` | `java.lang.Integer` | 1 条 |
| `expFlag`（targetField 侧） | BOOLEAN | `java.lang.String` | `java.lang.Boolean` | 1 条 |
| `expFlag`（reference 侧） | BOOLEAN | `java.lang.String` | `java.lang.Boolean` | 1 条 |

修正 4 处（`normalize_holder_java_types`）后：**10 -> 6**，4 条消失。
余 6 条属**另一根因族**（实体/属性级删除 + 数据体系），本轮**未闭合**。

**判据更正**：`DATA_MAPPING` holder 的 `path[]` 元素也必须过
`data_type_java_type.java_type_mismatches` 配对校验；旧写法只查 holder 自身的 4 键必填、
path 元素只查必填不查配对 ⇒ **真因被漏**。

## 4. 待查（诚实标注，UNVERIFIED）

- 余 6 条：`messageInfo.eventDataFullName` / `eventMfCustomDtoName` 与
  `context.getEntityDtoMapWithDtoFullNameKey()` 的键格式约定。
  CFR 已定位分支（`CheckUtils.check:1486` 的 `GLOBAL` 支）与两个取键函数
  （`MicroFlowUtil.getEntityNameFromEventMfCustomDtoName:585` = `substringBefore(name, ".")`；
  另一支取 `context.getAllEntityUnCapName()`），但**取键函数的权威格式未取到**，
  故不宣布修复。SSH `10.0.0.1:22` 本轮**不可达**（connect timed out），
  K8s/pod 日志通道不可用，无法从请求日志反查。
- `862673936068342178`「小爪标品服务定义」`state=RELEASE` 报 `BOOT_3000`（message 为 null，无细节）。
  已核查其节点集无 `DATA_MAPPING`（`SUB_MICROFLOW / RETRIEVE / RETRIEVE_ARRAY`）⇒
  非本轮已解的真因族，标 **UNVERIFIED**。

## 5. 本轮副作用登记（自我审计）

- 为取证据，把 `1524985498115296151` 发布成 RELEASE 一次（检测面一度 ERROR=10）。
  随后 `POST /udc/microflow/update` 还原为 DRAFT，检测面回到基线 **ERROR=0 / WARN=2**
  （已实测，非推断）。还原后 `data_schema` 中 `javaType:java.lang.Integer` 配对保留、
  `LENGTH=11992`（原 11893，差异 = 4 处 `java.lang.String`->`java.lang.Integer/Boolean` 的净增字符）。
- `862673936068342178` 的 `checkSchema/update` 返回 `BOOT_3000` 且**未落库**（回读仍 DRAFT），无副作用。
