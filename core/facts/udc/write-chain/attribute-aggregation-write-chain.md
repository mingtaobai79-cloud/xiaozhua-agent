# 属性「汇总值」写链（calculate=AGGREGATION）—— AggregationDto 契约

> 领域：UDC 实体属性 `udc_attribute.calculate` 第三态
> 状态：**LIVE PASS**（test2）+ **VERIFIED_STATIC_BYTECODE**（udc-biz 5.3.517 CFR）
> 代码：`components/udc/attribute_expression_constraints.py`；护栏 `tests/udc/test_attribute_expression_constraints.py`（+17 项）
> 关联：同家族的 NORMAL / COMPUTE 见同模块 §表达式引擎；本件只讲第三态。

## 0. 一句话

`calculate` 有 **三态**（`NORMAL(0)` / `COMPUTE(1)` / `AGGREGATION(2)`，CFR `AttributeCalculateEnum`）。
**`AGGREGATION` 不是 `expressionRuntimeData` 的另一种写法，而是另一个 DTO 家族**：
`expressionRuntimeData` 要装 `AggregationDto`（12 键 + 嵌套 `condition`），
与 `COMPUTE` 的 `{"executableExpr": ...}` **互不通用**。

## 1. 权威字节码（CFR，udc-biz 5.3.517）

| 类 | 作用 | 关键行 |
|---|---|---|
| `com/seeyon/boot/starter/extmetadata/enums/AttributeCalculateEnum` | 三态 + code | `NORMAL(0) COMPUTE(1) AGGREGATION(2)`（boot-starter-extmetadata 5.3.318） |
| `com/seeyon/udc/dto/AggregationDto{,+$Condition}` | 载体本体 12+2 字段 | 逐字见 §2 |
| `com/seeyon/udc/enums/AggregationTypeEnum` | 汇合函数 | `SUM(0) COUNT(1) MAX(2) MIN(3)` |
| `com/seeyon/udc/enums/EntityTypeEnum` | 实体型 | `PRIMARYWITHCHILD(0) PRIMARYONLY(1) CHILD(2)` |
| `EntityRelationMultiplicityEnum`（extmetadata 5.3.318） | 关系基数 | `ONE2ONE(0) ONE2MANY(1)` —— **无 MANY2MANY** |
| `AttributeEventListener#checkAggregation:447-462` | **唯一写侧校验** | 见 §3 |
| `com/seeyon/udc/utils/ObjectUtils#existFieldIsNull:42-55` | 判据实现 | 反射遍历全部字段，任一 null 即 `true` |
| `Expression4EntityUtil#filterComputeAttributeDto:138-140` | 计算环图过滤 | 只认 `COMPUTE` |

## 2. AggregationDto 字段（CFR 逐字）

```jsonc
{
  "sourceEntityId": <Long>,        "targetEntityId": <Long>,
  "sourceFieldId":  <Long>,        "targetFieldId":  <Long>,
  "entityType":     "PRIMARYWITHCHILD|PRIMARYONLY|CHILD",
  "functionType":   "SUM|COUNT|MAX|MIN",
  "entityName":     <String>,      "relation": "ONE2ONE|ONE2MANY",
  "targetDataType": <String>,      "targetFieldName": <String>,
  "sourceDataType": <String>,      "sourceFieldName": <String>,
  "condition": { "expressionDesignData": <String|null>,
                 "expressionRuntimeData": <String|null> }   // 可整键省略
}
```

## 3. ★ 服务端真正强制的只有一条：null 形状门

```java
// AttributeEventListener.checkAggregation:447-462（CFR 反编译）
List<AttributeDto> list = attributeDtoList.stream()
    .filter(a -> a.getCalculate() == AttributeCalculateEnum.AGGREGATION).toList();
if (CollectionUtils.isEmpty(list)) return;
list.forEach(a -> {
    AggregationDto d = JsonUtils.fromJson(a.getExpressionRuntimeData(), AggregationDto.class);
    if (Objects.isNull(d.getCondition())) d.setCondition(new AggregationDto.Condition());  // ← 先补默认值
    if (ObjectUtils.existFieldIsNull(d)) throw new BusinessException("UDC_ATTR_0006");
});
```

**两条由 CFR 直接推出的推论，均已被 LIVE 逐条证实**：

1. **判据集 = 12 键**：`condition` 在判据之前被补成 `new Condition()` ⇒ 它对 `existFieldIsNull`
   **永远非 null** ⇒ **不进判据**（可整键省略）。
2. **是"形状门"不是"语义校验"**：只判 null，不判任何一致性。

## 4. LIVE 实测（test2，app 8704025620829192834 / 实体 474806313816300867 / 字段 expText 8016904624316689195）

| # | 动作 | 结果 |
|---|---|---|
| P1 | 12 键齐全 + `condition` 全 null | **`BOOT_0000`**；REST 回读 `calculate=AGGREGATION`；DB `calculate=2` |
| P2 | **逐键删一**（12 次） | **12/12** 均 `UDC_ATTR_0006 Incorrect summary field parameters` |
| P3 | `condition` 整键缺失 | `BOOT_0000`（与 §3 推论 1 一致） |
| P4 | `condition` 两子键全 null | `BOOT_0000`（两层嵌套，子键不进顶层判据） |
| P5 | `functionType` SUM/COUNT/MAX/MIN | 4/4 `BOOT_0000` |
| P6 | `functionType=AVG` | `BOOT_3000`（枚举反序列化失败） |
| P7 | `entityType` 三值 + 数字码 `0/1/2` | 6/6 `BOOT_0000`；`BOGUS` → `BOOT_3000` |
| P8 | `relation` 两值 + 数字码 `0/1` | 4/4 `BOOT_0000`；`MANY2MANY`/`BOGUS` → `BOOT_3000` |
| N1 | `targetDataType` 与目标字段类型不符 | **`BOOT_0000` 通过** |
| N2 | `targetFieldName` 与 `targetFieldId` 不符 | **`BOOT_0000` 通过** |
| N3 | 源实体 = 目标实体 | **`BOOT_0000` 通过** |
| N4 | `calculate=COMPUTE` 但 runtimeData 填 AggregationDto | **`BOOT_0000` 通过** |

⇒ N1–N3 证明 `UDC_ATTR_0006` **不校验语义**；N4 证明服务端**不校验 calculate 与 runtimeData 的形态耦合**。
**写链侧必须自行保证这些一致性**（本模块把这四条钉成常量，防止后来者误以为服务端会拦）。

检测面：写完 AGGREGATION 后 `ERROR=0 / WARN=2`（`04003`×2，与本字段无关）⇒ **不引入新检测码**。

## 5. 前端同源（bundle 逐字）

`src_pages_app-design_entity-modeling_entity-field_components_rule-Form/module-62746.js`：

```js
// 子树选中后组装 l（= 上述 12 键 + 可选 condition），然后：
if (l.condition === undefined) { delete l.condition; }   // 前端显式省略
setEntityFormula(l);
setCalculate("AGGREGATION");
```

⇒ 与 §3 推论 1 完全自洽：**前端也认为 `condition` 是可省的**。

## 6. 与 COMPUTE 的真实区别

- `COMPUTE` 的 runtimeData = `{"executableExpr": <加密表达式>}`，参与
  `Expression4EntityUtil.resolveAggInfiniteLoop` 的**环检测**；`AGGREGATION` **不进该环图**
  （`filterComputeAttributeDto` 只认 `COMPUTE`）⇒ 汇总属性被排除在计算死循环检测之外。
- 但服务端**不阻止**你写反（N4）—— 这是设计器约定，不是服务端契约；误写不会报错、但语义必然错。
