# 业务数据流构造：值编辑器三态 + 字段引用 RETRIEVE 中转

> 触发场景：用户纠偏「节点覆盖率高但流程像互不相关的 CRUD 堆」——写实体字段全用 const，
> 没验证节点间数据传递。2026-11-04 业务链（采购申请汇总）验证。
> 对应 skill §4.33。

## 结论一：值槽三态的真实分布（写字段别默认全 const）

643 条 RELEASE 流程字段级统计（`value-literal-contexts.md`）：

| 类型 | 生产出现 | 语义 |
|---|---|---|
| SelectParam（引用） | 2482（最多） | 引用前序节点 / 字段 |
| Expression（表达式） | 998 | 计算 |
| Simple（常量） | 757 | 固定值 |

写实体字段优先用引用/表达式；但基础测试数据、枚举、固定状态允许 const。
不要为刷引用数造无意义依赖——真正要检查的是「业务上应继承前序结果的字段不许无理由硬编码」。

## 结论二：字段级引用前必须 RETRIEVE 中转成 DTO（G20 同源）

CREATE_ENTITY / CHANGE_ENTITY / DELETE_ENTITY 及 batch 的出参是**标量 id**（BIGINTEGER），
没有字段可引。写 `{"field": "req.totalAmount"}`（req 是 CREATE_ENTITY）会被解析成
**整节点引用**（parent/BIGINTEGER），字段部分静默丢弃、不报错。

正确：

```
retrieve(采购申请, by_id_from=req) → reqDto（DTO 出参，有 totalAmount 字段）
create_entity(报价, totalAmount={"field": "reqDto.totalAmount"})
  → SelectParam position=children / dataType=DECIMAL   ← 正确
```

判据：dump 写节点 attrs，看字段引用的 `selectParam.position` 是 `children`（字段级）还是
`parent`（整节点）。写 STRING/DECIMAL 字段却看到 parent+BIGINTEGER，就是引用了标量节点、字段丢了。

## 结论三：change_entity 目标必须是 DTO，不是 CREATE_ENTITY 标量 id

`CHANGE_ENTITY.selectParam` 引用前序 **RETRIEVE 的 DTO 出参**（dataType=DTO /
dtoType=MASTER_ENTITY）。引用 CREATE_ENTITY（标量 id）被 G31 拦
「引用 dataType=DTO 与出参声明 BIGINTEGER 不一致」。

更新刚创建的记录 = 先 RETRIEVE 查成 DTO 再 change_entity。

## 结论四：循环内累加（明细金额汇总）的表达式形态

```python
{"id": "acc", "kind": "create_variable", "title": "totalAmt", "data_type": "DECIMAL",
 "value": {"const": 0}}
{"id": "loop", "kind": "for_each", "list": "items", "body": [
    {"id": "accStep", "kind": "change_variable", "target": "acc",
     "value": {"arith": "ADD", "items": [
         {"field": "acc"},
         {"arith": "MUL", "items": [
             {"field": "loop.quantity"}, {"field": "loop.estimatedPrice"}]},
     ]}},
]}
```

- 表达式算术键是 `arith` = 运算符名字符串（`"ADD"`/`"MUL"`/`"SUB"`/`"DIV"`），
  **不是** `{"op":"ADD"}`——写成 dict 报「arith 不支持运算符」。
- 循环项字段引用 `{"field":"loop.xxx"}`，loop 是 for_each 节点的 id（`loop_frame_from`
  用 `alias=n["id"]`），生成 context 带循环项字段类型。
- 累加器 `{"field":"acc"}` 引用 CREATE_VARIABLE 标量出参，走表达式（Expression），
  不是 SelectParam（标量出参走 `_scalar_value_slot`，见 node-list-operation 相关）。

## 结论五：两层测试要分开

节点形态测试（第一层，单节点参数组合）+ 业务组合测试（第二层，多表数据流转），
不能拿第一层通过率冒充第二层。业务链最小形态：

CREATE_ENTITY(父) → CREATE_ENTITY(子,引用父ID) → RETRIEVE_ARRAY(按父ID) →
FOR_EACH(循环项字段) → 表达式累加 → CHANGE_ENTITY(回写父) → RETRIEVE(回读) → 断言。

字段来源逐条标：CONSTANT / PREVIOUS_NODE / PREVIOUS_NODE_FIELD / LOOP_ITEM / EXPRESSION。

## 结论六：字段级引用类型必须匹配，否则前端「所选'X'已变更」（假绿）

`{\"field\": \"reqDto2.totalAmount\"}`（字段级引用，children）把 **DECIMAL** 的 totalAmount
赋给 **BIGINTEGER** 的 processedRows 字段，前端抽屉标红「所选'总金额'已变更」，
但运行时 BigDecimal 自动转 Long（1000.0→1000），读库是 1000——**假绿**，用户一眼看到前端红。

判据：dump 写节点 attrs，字段级引用的 `selectParam.dataType` 必须等于目标字段 dataType：
- `taskId`(STRING) ← requestCode(STRING) → children/STRING ✅
- `processedRows`(BIGINTEGER) ← totalAmount(DECIMAL) → children/DECIMAL ❌ 前端「已变更」

正确做法：
- **类型匹配** → 用 SelectParam（选值），引用同类型字段（行数就引用 SIZE 出参）。
- **类型不匹配** → 用表达式（resultType 用目标字段 dataType）。
- **标量出参**（SIZE/SUM/MIN/MAX）引用到写字段 → 走 `_scalar_value_slot` 表达式，
  resultType 用字段 dataType（可能宽化 INTEGER→BIGINTEGER，见 §4.22 / 5cdcc974），
  这是正确形态，不会「已变更」。

业务语义上「已处理行数」不该承载「总金额」，是类型错位 + 语义错位一起犯。字段赋值先问：
这个字段业务上该装什么值、什么类型，再决定用引用还是表达式。

