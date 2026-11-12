# 节点契约：真实保存态 vs 前端新建态

> 证据来源：客户样例应用 `样例平台应用（已脱敏）` 的 **643 条 RELEASE 微流程、7937 个节点**，
> 以及数据迁移样例应用 `datamigration9000000000000000001` 的 **9 条真实业务流程**（已剔除助手生成的测试流程）。
> 机器可读契约：`core/facts/udc/microflow/node-contract-from-samples.json`
> 生成脚本：`scratch/build_contract.py`（只读，不写平台）

## 1. 为什么这层契约必须单独建

平台有三层校验，一层比一层深：

| 层 | 判据 | 能放过什么 |
|---|---|---|
| `checkSchema` | 后端 REST `/checkSchema/update` | 只查结构完整性，字段多余/形态错都能过 |
| UI 抽屉逐节点「确定」 | 前端表单必填 | 放过「checkSchema 要的字段」以外的语义错 |
| **真实保存态同形** | **643 条生产流程的字段集** | 前两层都过、但生产里根本不这么写的字段 |

前两层全绿 ≠ 生成正确。实测：一条 `checkSchema=True errors=0`、UI 20 个节点 0 红字的流程，
按生产契约仍有 **15 处不合规**。

## 2. 模板 ≠ 保存态

`fixtures/microflow/node_templates/` 是前端 `addNode` 的**新建态**骨架。
真实保存链路会丢掉/改写部分字段。25 个模板逐字段对照结果：

### 2.1 模板有、真实保存态从来没有（6 个，保存前必须剥）

| 节点 | 字段 | 真实样本 |
|---|---|---|
| `CUSTOM_ERROR` | `actionType` | 25 条全无 |
| `FOR_EACH` | `actionType` | 384 条全无 |
| `CREATE_MAP` | `paramType`、`dataType` | 4 条全无 |
| `SUB_MICROFLOW` | `pageInfo` | 251 条全无 |
| `CALL_DATA_FLOW` | `selectParam` | 1 条无（有 `condition`） |

### 2.2 模板没有、真实保存态必有（2 个，构造器必须补）

| 节点 | 缺失字段 | 真实形态 |
|---|---|---|
| `CREATE_LIST` | `value` | **数组**：`[]`(181/239) / `[SelectParam]`(42) / `null`(16) |
| `CALL_DATA_FLOW` | `condition` | `[GROUP{conditions:[CONDITION]}]` |

### 2.3 键相同但值形态不同（3 个，只看键名发现不了）

| 节点 | 字段 | 模板 | 真实 |
|---|---|---|---|
| `FOR_EACH` | `foreach` | `{sourceItemes:[...]}` | **`null`**（384/384） |
| `LIST_OPERATION` | `output` | `null` | **对象**（654/654） |
| `SUB_MICROFLOW` | `outputName` | `null` | **字符串**（215/251） |

`FOR_EACH.foreach` 这条最容易踩：`{sourceItemes:[]}` 只是前端新建节点的临时占位，
保存后落成 `null`，真正决定循环源的是 `selectParam`。

## 3. 各节点真实字段契约（MUST = 该类型全部样本都有的键）

### 控制节点：`actionType` 恒为 `null`，只能靠 `type` 取

| 节点 | 样本 | `actionType` |
|---|---|---|
| `BRANCH` | 941 | 0 个有 |
| `CONDITION` | 1981 | 0 个有 |
| `FOR` | 32 | 0 个有 |
| `FOR_EACH` | 384 | 0 个有 |
| `CUSTOM_ERROR` | 25 | 0 个有 |
| `BREAK` | 8 | **8 个都有**（唯一例外，两种都兼容） |

### 数据类节点

| 节点 | MUST 字段（除公共 10 键外） |
|---|---|
| `RETRIEVE` | `fetchType` `app` `structure` `title` `nullHandling` `selectType` `scope` `methodLegal` |
| `RETRIEVE_ARRAY` | 同 `RETRIEVE` |
| `CREATE_ENTITY` | `app` `structure` `title` `mappingType` `attrs` |
| `CHANGE_ENTITY` | `selectParam` `title`（**无 `mappingType`**） |
| `DELETE_ENTITY` | `deleteType` `title`；`SELECT_PARAM` 模式带 `selectParam`，`CONDITION` 模式带 `app`+`structure`+`condition`+`methodLegal`（**无 `entity`**） |
| `CREATE_BATCH_ENTITY` | `selectParam` `title`（**只有这两个**，无 `app`/`attrs`/`mappingType`/`structure`） |
| `CHANGE_BATCH_ENTITY` | 同 `CREATE_BATCH_ENTITY` |

### 变量 / 列表 / 映射

| 节点 | MUST 字段 |
|---|---|
| `CREATE_VARIABLE` | `paramType` `title` `dataType` `value` `mappingType` |
| `CHANGE_VARIABLE` | `selectParam` `value` |
| `CREATE_LIST` | `paramType` `title` `dataType` `value`（数组） |
| `CHANGE_LIST` | `selectParam` `action` `dataSource`（**无 `operationType`/`value`**） |
| `LIST_OPERATION` | `selectParam` `operationType`(=`{"type":"SIZE"}` 等) `title` `output`(对象) |
| `CREATE_MAP` | `entries` `title` `generics`（**无 `paramType`/`dataType`**） |
| `MAP_OPERATION` | `selectMap` `operationType` `generics`（**无 `selectParam`/`nullPromptMessage`**）；GET 模式另有 `paramType` `basic` `theKey` `arrayOrObject` `nullHandling` `dataType` `structure`，PUT 模式有 `entries` |

### 加工 / 服务

| 节点 | MUST 字段 |
|---|---|
| `CONVERT_DATA` | `convertType`（**对象** `{desc,value,dataType,type}`）`selectParam` `title` |
| `DATA_MAPPING` | `app` `structure` `title` `dataType` `targetType` `mappingRule` |
| `CALL_APP_SERVICE` | `app` `selectMethod` `outPutDesc`(=**null**) `outputName`（**无 `selectParam`**） |
| `SUB_MICROFLOW` | `mfService`（**无 `pageInfo`**） |
| `PUBLISH_BUSINESS_EVENT` | `eventType`；`IN_APP`→`selectEvent`，`AMONG_APP`→`selectMq`+`app` |

`CONVERT_DATA.convertType` 全量只有 5 种取值：
`Split` / `multiAssociation2List` / `List2multiAssociation` / `BasicData2String` / `String2Long`

## 4. 跨应用可复用性：结构可复用，值不可复用

用两个**独立应用**对照（智能项目管理 643 条 vs 数据迁移 9 条真实业务流程）：

- 共有的 **9 类节点，契约冲突 0 个** —— 字段集是平台级契约，可跨应用复用
- 但每个字段的**值**都带应用专有信息，必须运行时拉取：

| 值里的东西 | 例子 | 处理 |
|---|---|---|
| `appName` / `appId` | `样例平台应用（已脱敏）` | 活引用 |
| `id` / `javaType` / `fullName` | `com.seeyon.<app>.dto.XxxDto` | 活引用（实体元数据） |
| `relationEntity` | `-1953145006229338661` | 活引用 |
| `path` / `key` | `comseeyon...dtoXxxDto.field` | 活引用（字段元数据） |
| `md5` | 服务签名 | 活引用（`app_service_method`） |

**判据**：任何 `com.seeyon.<某个应用>` 字面量、任何裸数字 id，
出现在生成代码里就是错的 —— 必须来自 `LiveRefs`。

### 反面教材（本轮实测）

把数据迁移应用里**助手自己生成的流程**当成真实样本，得出「18 个跨应用契约冲突」，
结论完全反向。剔除后真实冲突是 **0**。做跨应用对照前必须先清洗掉自己的产物，
否则是在拿生成器跟生成器比。

## 5. 保证机制：三层闸门 + 一个测试

| 机制 | 位置 | 挡什么 |
|---|---|---|
| 契约表 | `core/facts/udc/microflow/node-contract-from-samples.json` | 事实来源，26 类节点 MUST/USUAL/OPT + 值形态 |
| `normalize_node()` | `components/udc/microflow/contract_gate.py` | 剥掉真实样本从未出现的键（挂在 `NodeBuilder.build()` 上自动生效） |
| `check_schema()` | 同上 | 缺 MUST / 多字段 / 控制节点写 actionType / 值形态错 |
| 构造器覆盖率（**原测试已删**） | `tools/microflow_coverage.py` | **22 类节点逐个查有无构造路径**；`tests/test_constructor_contract.py` 已于 `9fa07b76` 删除（依赖固定客户 APP_ID + `os.chdir` 绝对路径），**现在没有等价的 22/22 契约断言** ⇒ 覆盖率可算，契约合规不自动验 |
| 发布前闸门 | 生成脚本里的 `contract_gate` 调用 | 不合规 `SystemExit`，发布不出去 |

四道一起用才叫保证：
- 只有契约表 → 文档，没人执行
- 只有 `normalize` → 静默改数据，看不出错在哪
- 只有 `check` → 报错但不阻止发布
- 只有测试 → 覆盖不到新写的节点

## 6. 已知证据薄弱处

| 节点 | 样本量 | 风险 |
|---|---|---|
| `CALL_DATA_FLOW` | 1 | 只见到一种 `CONDITION` 模式，其他模式未知 |
| `CREATE_MAP` | 4 | `entries` 结构只见过 2 种 |
| `CREATE_BATCH_ENTITY` | 6 | |
| `MAP_OPERATION` | 24 | GET/PUT 两模式已覆盖 |
| `CONNECTOR` | **0** | 无任何生产样本；`cip-connector` 在本环境无已注册服务，需先进集成平台配置 |

样本量 <10 的节点，契约只能当「已见形态」用，不能当完备契约。
