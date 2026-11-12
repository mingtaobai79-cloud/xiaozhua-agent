# RETRIEVE_ARRAY（查询多条数据）

> 语料：217 条真实样本 / 126 条流程（另一应用 643 条 RELEASE 流程 dump）

## 1. fetchType 决定出参形态（关键结论）

| fetchType | output.type | output.dataType | 样本 |
|---|---|---|---|
| CONDITION | ARRAY | DTO | 184 |
| IDS | ARRAY | DTO | 19 |
| COUNT | OBJECT | INTEGER | 13 |
| OTHERS | OBJECT | DECIMAL | 1 |

**结论：只要是「取记录」，出参一定是 ARRAY；OBJECT 只出现在 COUNT/OTHERS 这类聚合。
单条记录不会降级成 OBJECT** —— 形态由 `fetchType` 决定，与命中行数无关。

这条正好回答「单条记录读取会不会意外降为 OBJECT」：不会，除非你用的是 COUNT。

## 2. 节点结构

顶层键（217/217）：`nodeId / name / type / caption / description / runAfter / input /
output / isCompleted / actionType / fetchType / app`，
CONDITION 形态额外有：`structure / condition / sortParams / pageSearch / variableTitle /
size / selectType / scope / methodLegal`。

`condition` 是标准条件组：

```json
[{"type":"GROUP","uuid":"...","conditions":[
   {"type":"CONDITION","leftParam":{"id":"<dto>.<field>","type":"OBJECT",
     "javaType":"java.lang.String","dto":"_field","field":"<field>",
     "desc":"...","dataType":"STRING","multiSelect":false},
    "operator":{"value":"EQ","desc":"="},
    "rightParams":[{"type":"CONSTANT","value":"10","desc":"10"}],
    "uuid":"...","logicalOperator":"AND"}]}]
```

## 3. 构造器修正（2026-11-02）

| 位置 | 问题 | 修正 |
|---|---|---|
| `microflow_nodes_extra.list_operation` | 出参一律写死 INTEGER/OBJECT，`FIRST_ONE` 取元素造不出来 | 按 op 分型：FIRST_ONE/LAST_ONE/PICK_ONE → OBJECT + 元素 DTO；其余沿用标量 |
| `expression_refs._lookup_field` | 只认 `node.structure`，元素节点没有 structure 就解析不了字段 | 用 `output.id`（DTO 全名）反查实体模型兜底 |

`LIST_OPERATION` 654 条样本的 op × 出参：
`FILTER/…→ARRAY`、`FIRST_ONE(93)/LAST_ONE(9)/PICK_ONE(34)→OBJECT 元素`、
`SIZE(15)/SUM/MIN/MAX→OBJECT 标量`。

## 4. 运行时验证（2026-11-02，RUNTIME_VERIFIED）

一条定时流程覆盖六种情形（实体：迁移断点；种子：M 组 3 条 / O 组 1 条 / X 组 0 条）：

```
ra_multi = RETRIEVE_ARRAY(taskId EQ P5RA…-M) → 3 条
ra_one   = RETRIEVE_ARRAY(taskId EQ P5RA…-O) → 1 条
ra_none  = RETRIEVE_ARRAY(taskId EQ P5RA…-X) → 0 条
sz_*     = LIST_OPERATION(SIZE)      → 写回 processed_rows
f_one    = LIST_OPERATION(FIRST_ONE) → 分支比对 f_one.sourceTable == "S-ONE"
```

读侧结果（同一秒写入）：

| 行 | processed_rows | 含义 |
|---|---|---|
| R1 | **3** | 多条读取正确 |
| R2 | **1** | 单条读取正确，且仍是 ARRAY（SIZE 能用） |
| R3 | **0** | 空列表语义正确（不是 null） |
| ELEM-OK | — | 取元素后字段值 == "S-ONE"，元素结构与声明一致 |

证据：`evidence/retrieve-array-runtime-2026-11-02.json`

### 4.1 两个踩到的坑（都已修）

**① 条件右值 `{"const": x}` 原样透传 → 条件静默失效**

平台把 `rightParams` 解析成 `value=""`、`desc=""`，于是 RETRIEVE_ARRAY 返回整张表：
三个 SIZE 全返回同一个数（23），构建 SUCCESS、运行 success=true，**只有读侧数据不对**。
修：`composer._cond_right()` 归一 + 新增闸门 **G39**（右值必须有 type，CONSTANT 必须有 value）。

**② SQL 造的测试数据 `tenant_id=0` → 平台查不到**

平台写入的行是 `tenant_id=-8112660841495312922 / creator=-1`，查询带租户过滤。
SQL 直接插的种子（tenant 0）三条全查不到（全 0）。修：种子改成应用租户。
**结论：隔离测试数据必须用应用租户，否则「条件对了但查不到」会被误判成条件失效。**

## 5. 未覆盖

- `IDS`（19 条样本）/ `COUNT`（13 条）/ `OTHERS`（1 条）三种 fetchType 未跑
- 分页（`pageSearch`/`pageInfo`）未跑
- 排序（`sortParams`）、`scope`、`selectType` 未跑
- 多条件 GROUP（AND/OR 组合）未跑（本轮是单条件）

## 5. 补验（2026-11-03）：COUNT / IDS / 多条件

同事务自造 4 行（processedRows=1..4，sourceTable=MARK-M）：

```
CONDITION 单条件 → SIZE = 4
fetchType=COUNT  → 4        （出参 OBJECT/INTEGER，不是列表）
fetchType=IDS    → SIZE = 4 （value 引用 MAP(id) 产生的 ARRAY<BIGINTEGER>，condition 为空）
多条件 AND       → 2        （sourceTable=… && processedRows>1 && processedRows<=3）
```

### 两个易错点

1. **COUNT 出参是标量**：写成 ARRAY 下游会类型不匹配。
2. **IDS 不用 condition，用 value**：`value` 是 SelectParam，指向一个
   `ARRAY<BIGINTEGER>` 出参（如 `LIST_OPERATION(MAP, count_fields=['id'])`）。
   构造器校验 cond_field 时必须按 fetchType 收窄，否则 IDS 会被「字段不存在」拦下。

3. **多条件断言必须自带隔离条件**：只写 `processedRows>1 && <=3` 会把表里
   别的流程的行一起算进来（实测返回 6 而不是 2）。加上 `sourceTable=<本批标记>`
   才是一次有效断言。

### 仍未验

分页（`pageSearch` + `pageInfo` 需 PageInfo 对象）、`sortParams` 排序、OTHERS、OR 语义。

## 6. ★★ 分页：pageInfo 是一个 PageInfo 变量对象

旧结论说「分页需要一个 PageInfo 对象，无头构造方式未找到」——**已解决**。

### 真实形态（44 条 `pageSearch=true` 样本）

查询节点：

```
pageSearch = "true"                      ← 字符串，不是布尔
pageInfo   = {type: "SelectParam", selectParam: {...}}   ← 指向 PageInfo 变量
```

PageInfo 变量由 `CREATE_VARIABLE` 造：

```
paramType   = OTHER
otherType   = SYSTEM_PAGE_INFO
dataType    = DTO
mappingType = attrs
attrs       = [pageNumber, pageSize, needTotal]，value 都是 Simple 常量
output.id   = javaType = com.seeyon.boot.transport.PageInfo
```

### 三个必填坑（平台连拦两轮）

`pageInfo.selectParam` 少一个属性就 `PROPERTY_IS_REQUIRED`：

```
PROPERTY_IS_REQUIRED  pageInfo.selectParam.type      ← 补 OBJECT
PROPERTY_IS_REQUIRED  pageInfo.selectParam.dtoType   ← 补 CUSTOM
```

完整需要：`type=OBJECT`、`dataType=DTO`、`dtoType=CUSTOM`、`udcApp=true`、
`appName`、`javaType`、`path`、`desc`、`outputName`。

### DSL

```json
{"id": "pg", "kind": "page_info", "page_number": 1, "page_size": 2}
{"id": "ra", "kind": "retrieve_array", ..., "page_info_from": "pg"}
```

### 实测

```
种子 5 行
  无分页                 → SIZE = 5
  page_size=2            → SIZE = 2
```

## 循环内 RETRIEVE 的 from_field 语义（2026-11-04）

`{"kind":"retrieve","entity":"A","by_id_from":"each","from_field":"外键"}` 里，
`from_field` 是循环项 `each` 的**元素字段**（外键属于源列表元素实体，如报价的 supplierId），
**不是** entity A（查询目标，如供应商）的字段。

`requirement_compiler` 归一化阶段曾把 `from_field` 与 `cond_field`/`by_field` 一起按
entity 归一化/校验，导致「外键字段属于源列表元素实体、不属于查询目标实体」被误报
`FIELD_NOT_FOUND`（MF-01 搭建暴露）。已修：`from_field` 从归一化里拆出（跳过 entity
校验，它是英文真名、不需要中文转真名）。
