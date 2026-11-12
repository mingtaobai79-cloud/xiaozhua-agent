# 微流程全节点表达式填充：方法与实测

> 2026-10-28 LIVE。目标：把微流程里每个「值」字段都升级为表达式，一个不漏。
> 结果：**26 个值槽位 / 24 个已表达式化 / 25 条表达式全部通过后端 /check + /transform**。

## 一、值槽位全景（26 个）

微流程 schema 里每个「值」都是一个值包装对象：

```json
{"type": "Simple", "simple": 0, "desc": 0}                    常量
{"type": "SelectParam", "selectParam": {...}}                 选变量
{"type": "Expression", "expression": {"title", "schema"}}     表达式
```

按节点类型统计（去重后 26 个槽位）：

| 节点 | 字段 | 数量 |
|---|---|---|
| CREATE_MAP ×3 | `entries[0].key` / `entries[0].value` | 6 |
| SUB_MICROFLOW ×2 | `attrs[0..2].value` | 6 |
| BRANCH 子节点 | `conditions[*].nodes[*]` 的值 | 4 |
| FOR | `forStart` / `forEnd` | 2 |
| CHANGE_ENTITY | `attrs[0].value` | 1 |
| CREATE_ENTITY | `attrs[0].value` | 1 |
| DELETE_ENTITY | `value` | 1 |
| CHANGE_VARIABLE | `value` | 1 |
| MAP_OPERATION | `theKey` | 1 |
| CUSTOM_ERROR | `attrError` | 1 |
| RETRIEVE_ARRAY | `pageInfo` | 1 |
| **合计** | | **26** |

## 二、结果：24/26 已表达式化

```
已转表达式   24
保留 SelectParam 1   （RETRIEVE_ARRAY.pageInfo）
另 1 个 DTO 槽位无法表达式化（见 §5）
```

25 条表达式（24 个新填 + 原先已存在的 BRANCH 条件）全部 `PASS`：

```
PASS [BRANCH          ] conditions[0].expression      实验数量 > 0
PASS [BRANCH          ] conditions[0].nodes[0].attrs  登录人员姓名
PASS [BRANCH          ] conditions[0].nodes[1].attrs  登录人员姓名
PASS [BRANCH          ] conditions[0].nodes[7].value  更新结果_成功行数 + 0
PASS [BRANCH          ] conditions[1].nodes[0].value  登录人员姓名
PASS [CHANGE_ENTITY   ] attrs[0].value.expression     登录人员姓名
PASS [CREATE_ENTITY   ] attrs[0].value.expression     登录人员姓名
PASS [DELETE_ENTITY   ] value.expression              更新结果_成功行数 + 0
PASS [CHANGE_VARIABLE ] value.expression              登录人员姓名
PASS [FOR             ] forStart.expression           更新结果_成功行数 + 0
PASS [FOR             ] forEnd.expression             更新结果_成功行数 + 0
PASS [CREATE_MAP      ] entries[0].key.expression     登录人员姓名      ×3
PASS [CREATE_MAP      ] entries[0].value.expression   登录人员姓名      ×3
PASS [MAP_OPERATION   ] theKey.expression             登录人员姓名
PASS [SUB_MICROFLOW   ] attrs[0].value.expression     更新结果_成功行数 + 0  ×2
PASS [SUB_MICROFLOW   ] attrs[1].value.expression     更新结果_成功行数 + 0  ×2
PASS [SUB_MICROFLOW   ] attrs[2].value.expression     映射值结果        ×2
PASS [CUSTOM_ERROR    ] attrError.expression          映射值结果

PASS 25 / 25    FAIL 0
```

节点结构未被破坏：27 节点、ID 集合一致；全字段审计 29/29 干净。

## 三、六条硬约束（全部踩过）

### 3.1 执行顺序

**表达式只能引用本节点之前已执行节点的输出。**

第 20 号输出 `_MAP_OPERATION_ThCnMw` 之后的节点才能用它；前面的节点引用它 = 运行时拿不到值。

实现：`walk_ordered()` 保证条件分支内节点先于后续兄弟被遍历，
`available_vars(ordered, idx)` 只取 `idx` 之前的输出。

### 3.2 系统变量不受顺序限制

`system.*` 走全局表，**任何位置都可用**，而且：

- token 类型是 `SYSTEM`，不是 `VARIABLE`
- `schemas` 可以为空数组（不进变量树）

```json
{"type":"SYSTEM","value":"system.currentUserName","desc":"登录人员姓名"}
```

实测可用的（部分）：

| 变量 | 类型 |
|---|---|
| `system.currentUserId` | BIGINTEGER |
| `system.currentUserName` | STRING |
| `system.currentUserCode` | STRING |
| `system.currentOrgName` | STRING |
| `system.currentDateTime` | DATETIME |

**这一条解决了 14 个「前置无 STRING 变量」的死局。**

### 3.3 resultTypeInfo 只有 15 个合法值

`OBJECT` 不在值域内，用了报 `FORMULA_6003`：

```
INTEGER BIGINTEGER DECIMAL STRING MULTILINESTRING
DATETIME DATE TIME BOOLEAN CURRENCY ATTACHMENT
ARRAY ENTITY CTPENUM ENUM
```

DTO 场景必须用 `ENTITY`，并且**必须带 `resultTypeFullName`**，
否则报 `FORMULA_6901`（类型不匹配）。

### 3.4 类型名必须归一化

后端同一概念存在多种写法，不归一会「明明有变量却匹配不到」：

```
String       → STRING
Long         → BIGINTEGER
Object / Dto → DTO
```

实测踩过：`_CONVERT_DATA_kQ8HsT` 的 dataType 是 `String`（小写 s），
按 `STRING` 比较匹配不上，导致 14 个字段被误判为「无可用变量」。

### 3.5 DTO 槽位优先用自带 selectParam

若字段自身带 `selectParam.id`，用它构造 schemas 最准 ——
字段期望的 paramId 可能与候选变量不同。

### 3.6 不是所有槽位都该表达式化

`RETRIEVE_ARRAY.pageInfo` 指向 `com.seeyon.boot.transport.PageInfo` 实例，
是**结构选择器**而非普通值。强行表达式化 → `FORMULA_6901`。

正确处理：**保留 `SelectParam`**。这不是偷懒，是类型契约不允许。

## 四、写入链路

```
1. read_schema_page → {id, dataSchema}
2. 逐槽位替换 {type:"Expression", expression:{title, schema}}
3. 结构自检：节点数 + nodeId 集合不变
4. udcMicroflowFindByIdGet → 取全量 DTO（34 字段）
5. DTO.dataSchema = JSON.stringify(newSchema)
6. udcMicroflowUpdatePost  ← ★ GraphQL 变量名必须是 body，不是 p
7. 后端回读 → 逐槽位确认 type=="Expression"
8. 每条表达式 /check + /transform 复验
```

### 4.1 两个必须知道的接口细节

**`read_schema_page` 只返回 `{id, dataSchema}`**，不是全量 DTO。
提交前必须再调一次 `udcMicroflowFindByIdGet` 拿 34 字段的完整记录
（`appId` / `caption` 都在里面），否则 `BOOT_1001 微流程名称所属应用ID 不能为null`。

**GraphQL 变量名**：`gql_page()` 把变量名固定成 `{p: ...}`，
但 `udcMicroflowUpdatePost` 要的是 `{body: ...}`。必须自定义请求。

## 五、验收判据

| 判据 | 可信度 | 本次结果 |
|---|---|---|
| 本地替换成功 | 低 | 24/24 |
| 结构自检（节点/ID 不变） | 中 | 27→27，一致 |
| 提交返回 `BOOT_0000` | 中 | `content: 1` |
| **后端回读 type=="Expression"** | **高** | 24/24 |
| **每表达式 `/check`=true** | **高** | 25/25 |
| **每表达式 `/transform`=BOOT_0000** | **高** | 25/25 |
| 全字段审计无回归 | 高 | 29/29 干净 |

## 六、实现

`components/udc/microflow/expression_fill.py`

```python
norm_type(dt)                       # String→STRING, Long→BIGINTEGER
iter_value_slots(node)              # 产出 (path, slot)，跳过 output/input/mfService
slot_want_type(slot)                # 槽位期望的表达式结果类型
build_expression_dto(var, want)     # 构造 ExpressionSaveDto（含系统变量分支）
pick_variable(pool, want)           # 按类型挑变量
walk_ordered(nodes)                 # 按执行顺序遍历
available_vars(ordered, idx, sys)   # 前置输出 + 系统变量
```

`tests/test_microflow_expression_fill.py` — 28 项契约测试。

## 七、证据

| 项 | 路径 |
|---|---|
| 改造计划 | `scratch/expr-fill/fill-plan-strict.json` |
| 备份（回滚用） | `scratch/expr-fill/schema-backup-*.json` |
| 写入后 schema | `scratch/expr-fill/schema-after.json` |
| 逐条校验结果 | 运行 `scratch/verify_all_api.py` |

**证据等级**：全部 `LIVE`（test2 真实写入 + 后端回读 + 逐条接口校验）。
