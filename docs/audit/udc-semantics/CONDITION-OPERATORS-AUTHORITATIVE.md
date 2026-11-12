# UDC 过滤条件（where）—— 权威操作符与结构（反编译 boot-starter-condition 5.3.318）

**证据源**：`<MAVEN_REPO>/com/seeyon/boot-starter-condition/5.3.318/boot-starter-condition-5.3.318.jar`（原 5.3.308，2026-10 对账升级，操作符集合不变）
反编译（CFR）：
- `com.seeyon.boot.starter.condition.enums.OperatorEnum`
- `com.seeyon.boot.starter.condition.enums.ParamTypeEnum` / `NullRightValueConditionEnum` / `RelationEnum`
- `com.seeyon.boot.starter.condition.dto.SingleConditionDto`（含 `Type` / `LeftParamDto` / `RightParamDto` / `ConditionOperatorDto`）
- udc 侧：`com.seeyon.udc.microflow.domain.bo.ConditionInfo` / `param.ConditionParam` / `ConditionLeftParam` / `ConditionRightParam`

★ 权威 > 前端推断：前端 `seeyon-biz-where` 只暴露 20 个操作符，**后端 OperatorEnum 是 22 个**（多 `ZERO`/`NOTZERO`），且 `NEQ` 的 SQL 值是 `<>` 不是 `!=`。

---

## 1. 操作符全表（OperatorEnum，22 个）

| 枚举 | SQL 值 | 显示名 | 右参数个数 |
| --- | --- | --- | --- |
| EQ | `=` | 等于 | 1 |
| NEQ | `<>` | 不等于 | 1 |
| GT | `>` | 大于 | 1 |
| LT | `<` | 小于 | 1 |
| GE | `>=` | 大于等于 | 1 |
| LE | `<=` | 小于等于 | 1 |
| RLIKE | `like` | 右匹配 | 1 |
| LLIKE | `like` | 左匹配 | 1 |
| LIKE | `like` | 全匹配 | 1 |
| NOTLIKE | `not like` | 不匹配 | 1 |
| IN | `in` | 包含 | 1 |
| NOTIN | `not in` | 不包含 | 1 |
| NULL | `is null` | 为空 | 0 |
| NOTNULL | `not null` | 不为空 | 0 |
| ZERO | `= 0` | 为零 | 0 |
| NOTZERO | `<> 0` | 不为零 | 0 |
| BETWEEN | `between` | 介于 | 2 |
| NOTBETWEEN | `not between` | 不介于 | 2 |
| INCLUDEALL | `include all` | 包含全部 | 1 |
| INCLUDEANY | `include any` | 包含任一个 | 1 |
| NOTINCLUDEALL | `not include all` | 不包含全部 | 1 |
| NOTINCLUDEANY | `not include any` | 不包含任一个 | 1 |

- **size=0**：NULL / NOTNULL / ZERO / NOTZERO → rightParams 必须为空
- **size=2**：BETWEEN / NOTBETWEEN → rightParams 恰 2 个
- 其余 size=1

## 2. 条件对象结构（后端权威）

```
ConditionInfo {
  title: string,
  schema: string,
  conditionParamResults: [ ConditionParam ]
}
ConditionParam {
  leftParam: ConditionLeftParam,
  rightParams: [ ConditionRightParam ],
  originalLeftParamDto: SingleConditionDto.LeftParamDto,
  operator: SingleConditionDto.ConditionOperatorDto,
  uuid: string
}
ConditionLeftParam {          # 左值（字段）
  field, dataType, id, type
}
ConditionRightParam {         # 右值（常量/表达式/上下文变量）
  key, type,                  # type ∈ {CONSTANT, EXPRESSION, CONTEXT_VARIABLE}
  value, selectParam, expression
}
```

### SingleConditionDto.LeftParamDto（@NotBlank → 必填）
`id`、`entityId`、`entityAppName`、**`dto`（必填）**、**`field`（必填）**、`desc`、`dataType`、`multiSelect`(=false)、
`type ∈ {OBJECT(0), ARRAY(1)}`、`javaType`、`nullRightValueCondType`

### 枚举
- `ParamTypeEnum`（5.3.318 实测全量 **5 个**）：CONSTANT（常量）/ CONTEXT_VARIABLE（上下文变量）/ SYSTEM_VARIABLE（系统变量）/ EXPRESSION（表达式）/ ENTITY_FIELD（实体字段）
- `NullRightValueConditionEnum`：IGNORE_IF_ANY_NULL / USE_DEFAULT_VALUE / INVALID_IF_ANY_NULL
- `RelationEnum`：ONE2ONE / ONE2MANY
- `RightParamDto.type`：CONSTANT / EXPRESSION / CONTEXT_VARIABLE

## 3. dataType → 操作符矩阵
见 `components/udc/microflow_model.py` `CONDITION_TYPE_OPERATORS`：
STRING→EQ NEQ LIKE NOTLIKE IN NOTIN RLIKE LLIKE NULL NOTNULL；INTEGER→EQ NEQ LT LE GT GE BETWEEN NOTBETWEEN **ZERO NOTZERO** NULL NOTNULL；
**BOOLEAN→EQ NEQ ZERO NOTZERO**；ENUM→EQ NEQ IN NOTIN NULL NOTNULL；DATETIME→EQ NEQ LT LE GT GE BETWEEN NOTBETWEEN **ZERO NOTZERO** NULL NOTNULL；
ENTITY→EQ NEQ IN NOTIN NULL NOTNULL；ATTACHMENT→仅 NULL NOTNULL；MULTI*→EQ NEQ INCLUDE分类+NULL NOTNULL。
**5.3.318 对账修正**：BIGINTEGER 补 NULL/NOTNULL（原缺）；INTEGER/DATETIME 补 ZERO/NOTZERO（原缺）。
**ConditionService.check 契约**（5.3.318 反编译）：leftParam/operator/rightParams 不可 null；GROUP 内从第 2 个条件起 logicalOperator 不可空；type 只能 GROUP/CONDITION。

## 4. 与前端 seeyon-biz-where 的差异

| 项 | 前端 | 后端权威 |
| --- | --- | --- |
| 操作符数量 | 20 | **22**（多 ZERO/NOTZERO） |
| NEQ 值 | `!=` | `<>` |
| BETWEEN 显示 | 介于 | 介于（一致） |
| 右参数约束 | 前端按 size 显示 | `OperatorEnum.size` 权威（0/1/2） |

## 5. 条件嵌套结构（★权威 `BaseConditionDto` @JsonSubTypes）

```
condition = [ GroupDto ]            # 顶层是 GROUP 数组（LIVE 证实）
GroupDto {
  type: "GROUP",
  uuid,
  conditions: [ ConditionDto ],     # 递归：可再嵌 GROUP
  logicalOperator: "AND" | "OR"     # BaseConditionDto$LogicalOperator
}
ConditionDto        # = SingleConditionDto，type:"CONDITION"
```
- **LogicalOperator**：`AND(desc="and", symbol="&&", value="and")` / `OR(desc="or", symbol="||", value="or")`
- `@JsonSubTypes({GROUP→ConditionGroupDto, CONDITION→SingleConditionDto})`
- **LIVE 实证**（test2 三个标品）：`condition=[{"type":"GROUP","uuid":"...","conditions":[{"type":"CONDITION","leftParam":{...},"rightParams":[...],"operator":{...},"uuid":"..."}]}]`
- **leftParam 真实字段**：`{id, type:"OBJECT", javaType, dto:"_expText", field:"expText", desc, dataType}`
  （与后端 `LeftParamDto` 一致；`dto` = `_<field>`，`id` = 全限定 `...Dto.<field>`）
