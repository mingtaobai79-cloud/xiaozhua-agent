# LIST_OPERATION（列表处理）运行时语义

> 2026-11-03 实测于 test2。654 条语料，14 种操作，本轮验证 10 种。

## 1. 操作 × 附加键 × 出参

| 操作 | 语料数 | 附加键 | 出参 |
|---|---|---|---|
| SIZE | 15 | — | OBJECT 标量 |
| FIRST_ONE / LAST_ONE | 106 / 10 | — | OBJECT 元素（DTO） |
| PICK_ONE | 38 | `indexValue{Simple}` | OBJECT 元素（DTO） |
| SORT | 18 | `sortParams[{sortType, attrType}]` | **ARRAY** |
| DISTINCT | 34 | `countAttrs`（按字段去重，**必填**） | **ARRAY** |
| MAP | 106 | `countAttrs[{字段}]` | **ARRAY**（元素=字段类型） |
| SUM / MIN / MAX | 132 / 2 / 2 | `countAttrs[{字段}]` | OBJECT 标量（随字段类型） |
| FILTER | 176 | `expression{title, schema}` | ARRAY |
| SUBTRACT / INTERSECT | 11 / 3 | — | ARRAY |
| GROUP_AND_SUM | 1 | — | ARRAY |

## 2. 运行时实测（同事务自造 3 行 processedRows=1/2/3）

| 操作 | 结果 | 断言 |
|---|---|---|
| SIZE | 3 | ✓ |
| SORT(processedRows DESC) → FIRST_ONE | 3 | ✓ |
| SORT(processedRows DESC) → LAST_ONE | 1 | ✓ |
| SUM | 6 | ✓ |
| MIN / MAX | 1 / 3 | ✓ |
| MAP(processedRows) → SIZE | 3 | ✓ |
| DISTINCT(sourceTable)，3 行同值 | 1 | ✓（塌缩正确） |

### PICK_ONE 的索引语义（易错）

```
PICK_ONE(1) → 3     PICK_ONE(2) → 2     PICK_ONE(3) → 1
PICK_ONE(0) → 平台拒绝：LIST_OPERATION_PICK_ONE_LESS_THAN_ONE
```

**1 基索引**，且按检索顺序（RETRIEVE_ARRAY 默认 id 倒序）定位。
写成 0 基会发布失败；写成 1 基但假设升序会取错元素。

## 3. 两个坑

1. **DISTINCT 必须给 countAttrs**：不给 → 发布被拒 `PROPERTY_IS_REQUIRED`。
   语料样本里没这个键，是旧版本形态，不能照抄。
2. **SORT/DISTINCT 出参是 ARRAY**，不是标量。写成标量 → 下游引用被判类型不一致（G31）。
   `data_mapping` 也有同类问题：ARRAY 判定必须放在 `output` 被整体覆盖之后。

## 4. 未验证

- **FILTER（176 条）**：需要元素字段的表达式条件，而含字段引用的
  `executableExpr` 只能是占位，必须进设计器点「确定」由平台重算
  （expression-engine.md §十四 / §十五）→ 无头环境做不了，与「UI 抽屉路径不通」同类阻塞。
- SUBTRACT 11 / INTERSECT 3 / GROUP_AND_SUM 1：语料太少，未构造。

## 5. 验收环境提醒

应用里**别的流程会清这张表的数据**（实测种子被删，列表变空，聚合全返回 0）。
隔离测试必须把造数据放进被测流程本身，同一事务内自洽，不能依赖外部 SQL 种子。

## 6. 补验（2026-11-03 下午）：SUBTRACT / INTERSECT

二元操作，两个入参放在不同键上：

```
selectParam    = 左列表（被减 / 左集）
operationParam = 右列表（减数 / 右集）   ← 语料样本里就是这个键
SUBTRACT      需 countAttrs 指定比较键（如 id）
INTERSECT     对 DTO 列表无效，必须先 MAP 成标量列表再交（语料样本也是标量）
```

实测（4 行，取 processedRows>2 为右集）：

```
MAP(id)全量 SUBTRACT MAP(id)>2 → 2   （P6FX01-SUB）
MAP(id)全量 INTERSECT MAP(id)>2 → 2  （P6FX01-INT）
```

## 7. 补验：RETRIEVE_ARRAY 的 sortParams

构造器原先写死 `sortParams: []`。真实形态是
`[{"sortType": "DESC", "attrType": <字段活引用>}]`，`attrType` 必须是实体属性对象
（含 id/fullName/md5/dataType），不能只写字段名。

```
倒序查 processedRows DESC → FIRST_ONE = 4（P6FX01-SORT）
```

## 8. FIRST_ONE 接 DATA_MAPPING 的老 bug 已消

之前编译报 `找不到符号: 类 _LIST_OPERATION_xxx`，当时靠换写法绕过。
根因就是 SelectParam 的 `name` 写成 `<节点输出名>.<字段>`（见 §4.22 技能条目）。
修正后 `retrieve → data_mapping(sourceTable→taskId) → FIRST_ONE → 写` 直接构建成功，
映射值逐字落到库（task_id='P6FX01-M'）。

## 9. ★★ FILTER：不需要设计器（推翻旧结论）

旧结论说「含字段引用的表达式必须进设计器点确定」，**这是错的**。

实测（2026-11-03）：把语料里一条真实 FILTER 表达式原样重放给
`/expression/check` + `/expression/transform` → `BOOT_0000`，
返回的 `executableExpr` 与设计器产出的**逐字节一致**。
旧结论只对「本地手拼 designData + 占位 executableExpr」那条降级路径成立。

### 构造要点（三个都错一次才通）

1. **context 要两级对象**
   ```
   根  name=<DTO 去点>  description=过滤条件  type=OBJECT  selectable=false
     └ 子  name=<DTO 去点>  description=<列表名>  type=OBJECT  selectable=true
          └ 字段  name=<字段名>  description=<中文名>  type=<字段类型>
   ```
   `uniformityParams.paramId` 用**带点**的 DTO 全名。

2. **token 形态分两种**
   - `OPERATOR`（==、>、<、and、or）：**平铺** `[VARIABLE, OPERATOR, CONSTANT]`，不带 subOps
   - `FUNCTION`（文本包含、不为空）：单个 token，参数放 `subOps`

   按「全部带 subOps」构造 → `FORMULA_6070 Operator: =, input error!`

3. **变量路径是 DTO 名重复两次**
   `value = "<DTO去点>.<DTO去点>.<字段名>"`

### 实测

```
FILTER processedRows > 2          → 2 条（种子 4 行）
FILTER taskId == '<MARK>-S3'      → 1 条
```

### 还有一条：设计器里的操作顺序

UI 里「列表操作」抽屉要先选**选择列表**，操作类型才有「过滤」选项；
选了列表之后操作类型会被重置，必须重选；过滤条件是一个
「设置过滤条件」输入框，点了才弹「表达式设置」模态。
这条只是记录现象，不是必需路径 —— 离线构造已经覆盖。

## 10. GROUP_AND_SUM：分组 + 汇总

语料只有 1 条，形态已锁定：

```
selectParam   = 源列表（ARRAY）
operationType = {type: "GROUP_AND_SUM"}
groupByAttrs  = [分组字段的 attrType]
countAttrs    = [被汇总字段的 attrType]
output        = ARRAY（元素 DTO 与输入相同，不是新 DTO）
```

DSL：

```json
{"kind": "list_operation", "list_node": "ra", "op_type": "GROUP_AND_SUM",
 "group_by": ["sourceTable"], "count_fields": ["processedRows"]}
```

实测：3 行同组（1、2、5）→ 组数 1、汇总 8。

★ 取分组结果里的字段时，写节点字段引用要用点号形式
`{"field": "f1.processedRows"}`；写成 `{"field": "f1", "from_field": ...}`
会被当成「整个元素引用」，平台报 `selectParam.javaType PROPERTY_IS_REQUIRED`。
