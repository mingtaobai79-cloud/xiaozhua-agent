# 真实业务微流程骨架（643 条 RELEASE 实测，智能项目管理平台）

> 语料：`scratch/pmp_schemas.json`（643 条 RELEASE / 7937 节点）
> 用途：生成器该先打什么靶。**不要用「能拼出 20 节点的复杂流程」当能力证明。**

## 一、规模真相：真实业务极少是复杂流程

| 规模档 | 条数 | 占比 |
|---|---|---|
| **1-3 节点（极简）** | **294** | **46%** |
| 4-8 节点（简单） | 153 | 24% |
| 9-15 节点（中等） | 82 | 13% |
| 16-30 节点（复杂） | 75 | 12% |
| 31+ 节点（超复杂） | 39 | 6% |

节点数（递归拍平）：最少 0 / **中位数 4** / 最多 250 / 平均 9.3。

**结论：先把「1-8 节点」这 70% 打穿，比把 20 节点流程拼漂亮重要得多。**

## 二、零节点不是残废，是 CUSTOM 型

128 条零节点流程中 **122 条是 `type=CUSTOM`**（自定义微流程）：只声明出入参，无节点链。
这是 6 组合矩阵里的合法形态，不是缺陷。

CUSTOM 出入参组合（122 条实测）：

| (trigger.paramType, endNode.paramType) | 条数 |
|---|---|
| DEFAULT_OBJECT / DEFAULT_OBJECT | 31 |
| BASIC / BASIC | 27 |
| BASIC / DEFAULT_OBJECT | 25 |
| DEFAULT_OBJECT / BASIC | 24 |
| DEFAULT_OBJECT / ENTITY_OBJECT | 4 |
| NONE / DEFAULT_OBJECT | 4 |
| ENTITY_OBJECT / DEFAULT_OBJECT | 3 |

**入参和出参类型可以不同**（如 BASIC 入 / DEFAULT_OBJECT 出，25 条）。
顶层 `input` / `output` 必须与 `trigger.output` / `endNode.output` 是同一对象（副本）。

## 三、高频顶层骨架（同一串节点序列在多少条流程里出现）

| 出现次数 | 骨架 | 业务含义 |
|---|---|---|
| 128 | （空） | CUSTOM 型，纯出入参 |
| 56 | `RETRIEVE` | 单个查单条 |
| 40 | `RETRIEVE → CREATE_VARIABLE → BRANCH` | 查一条 → 取字段 → 判空分支 |
| 38 | `SUB_MICROFLOW` | 单个调子流程 |
| 33 | `RETRIEVE → BRANCH` | 查一条 → 判空分支 |
| 15 | `CREATE_VARIABLE → BRANCH` | 建变量 → 分支 |
| 10 | `CREATE_LIST → LIST_OPERATION → CREATE_LIST → FOR_EACH → CHANGE_BATCH_ENTITY` | 列表加工 → 循环批量改 |
| 9 | `RETRIEVE → CREATE_LIST → BRANCH` | |
| 9 | `CREATE_VARIABLE` | |
| 8 | `CREATE_VARIABLE → RETRIEVE → BRANCH` | |
| 7 | `RETRIEVE_ARRAY → BRANCH` | |
| 6 | `CREATE_VARIABLE → FOR_EACH` | |
| 6 | `CALL_APP_SERVICE` | |
| 6 | `RETRIEVE_ARRAY → LIST_OPERATION` | |

**这三条是 70% 业务的真身**：
```
RETRIEVE                                   （单查，56+33+40 的一部分）
RETRIEVE → CREATE_VARIABLE → BRANCH        （查出→取字段→判空，40 条）
SUB_MICROFLOW                              （单调用，38 条）
```

## 四、极简业务真实样例（1-3 节点，摘录）

| 流程名 | 骨架 |
|---|---|
| 根据智能报备ID查询智能报备相关信息 | `RETRIEVE` |
| 1.13合同申请查询合同模板配置 | `RETRIEVE` |
| 查询登录人员是否为平台管理员 | `CALL_APP_SERVICE` |
| 1.7添加预留补偿计划 | `CREATE_ENTITY` |
| 根据文件StorageKey查询对应文件信息 | `CALL_APP_SERVICE` |
| 选择后删除OA报备数据 | `DELETE_ENTITY` |
| 发票解析后附件类型转换 | `CREATE_VARIABLE` |
| 1.8根据合同号查询预留补偿计划 | `RETRIEVE_ARRAY` |
| 查询合同变更审批记录 | `RETRIEVE → RETRIEVE` |
| 页面关闭时更新当前单据占用信息 | `RETRIEVE → CHANGE_ENTITY` |
| 1.13取用章申请第一条附件 | `RETRIEVE → LIST_OPERATION` |
| 根据报备ID查询人脸签中间表 | `RETRIEVE_ARRAY → LIST_OPERATION` |
| 6.5根据费用申请ID查询费用申请明细 | `CREATE_LIST → RETRIEVE_ARRAY` |
| 查询分公司配置表 | `RETRIEVE → SUB_MICROFLOW` |
| 获取枚举项名称 | `CALL_APP_SERVICE → SUB_MICROFLOW` |

**注意命名即业务**：这些名字直接说明「查什么、干什么」——
「根据 X 查询 Y」「根据 X 更新 Y」「X 后删除 Y」。
生成器应该能直接从这类**单句业务描述**生成对应骨架。

## 五、复杂度分布（决定实现优先级）

| 特征 | 条数 | 占比 |
|---|---|---|
| 含分支 BRANCH | 326 | 51% |
| 含循环 FOR/FOR_EACH | 203 | 32% |
| 含子流程 SUB_MICROFLOW | 156 | 24% |

**分支是一半业务的刚需**，循环三分之一，子流程四分之一。

## 六、对生成器的要求（按这些结论反推）

1. **必须先支持「单句业务 → 1-3 节点流程」**：
   - 「根据 X 查询 Y」→ `RETRIEVE(entity=Y, cond=X)` 或 `RETRIEVE_ARRAY`
   - 「查询 A 和 B」→ `RETRIEVE → RETRIEVE`
   - 「查 X 并更新 Y」→ `RETRIEVE → CHANGE_ENTITY`
   - 「查 X 然后调用 Z」→ `RETRIEVE → SUB_MICROFLOW`
   - 「删除 X」→ `DELETE_ENTITY`
   - 「新增 X」→ `CREATE_ENTITY`
2. **查完必判空的要走 `RETRIEVE → CREATE_VARIABLE → BRANCH`**（40 条，最高频复合骨架）。
3. **CUSTOM 型必须支持**：122 条（19%）是纯出入参无节点，生成器现在根本不会造这种。
4. 复杂流程（16+ 节点，18%）优先级最低，不要拿它当能力证明。

## 七、生成器当前差距（实测）

`scratch/form_coverage.py` 结论：9 个 actionType 存在多形态，共 **79 种真实子形态**，
构造器只实现 9 种，**覆盖率 11%**：

| 节点 | 真实形态 | 构造器 | 最高频缺失形态 |
|---|---|---|---|
| CHANGE_VARIABLE | 23 | 1 | `attrs[1..5]` 字段级映射（304 次真实用法） |
| SUB_MICROFLOW | 16 | 1 | `attrs[N]+mappingType` 参数映射（56 次） |
| RETRIEVE_ARRAY | 8 | 1 | `pageSearch+sortParams`（133 次） |
| CREATE_ENTITY | 8 | 1 | `mappingType+value` 整体对象引用（16 次） |
| CALL_APP_SERVICE | 6 | 1 | `mappingType+attrs[N]` DTO 多参数（68 次） |
| BRANCH | 5 | 1 | 3/4/5/6 分支（58 次） |
| CHANGE_ENTITY | 5 | 1 | 多字段 attrs（23 次） |
| CREATE_VARIABLE | 4 | 1 | `structure` 实体型（247 次，最高频） |
| RETRIEVE | 4 | 1 | `value{}` ID 查询（246 次，最高频） |

**最高优先级的两个**：`RETRIEVE.value{}`（ID 查询，246 次）和
`CREATE_VARIABLE.structure`（实体型，247 次）——它们是极简业务骨架的主力。
