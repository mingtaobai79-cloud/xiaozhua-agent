# CHANGE_ENTITY / DELETE_ENTITY 运行时契约（实测）

> 2026-11-02 实测于 test2（appId=8704025620829192834，实体=迁移断点）。
> 本文只写**跑过、有数据库或平台回读证据**的结论；推断一律标注。

## 1. DELETE_ENTITY 有两种模式，动态删除只能走 SELECT_PARAM

语料 `deleteType` 分布：`CONDITION 10 / SELECT_PARAM 9 / IDS 1`。

| 模式 | 字段 | 右值能不能引用节点 |
|---|---|---|
| `CONDITION` | `app` `structure` `condition` `methodLegal` | ❌ **不能**（填 SelectParam 必被拒） |
| `SELECT_PARAM` | 只要 `deleteType` + `title` + `selectParam` | ✅ 引用前序 DTO 出参 |
| `IDS` | — | 未实测 |

### ★ CONDITION + 节点引用 = BOOT_1001，且没有任何提示

```
发布被拒 code=BOOT_1001 message=Parameter Error
```

响应体里**没有字段级错误**（`data=null`），只能靠二分定位到「加了这个 DELETE 节点就挂」。
实测二分：1/2/3/4 节点全部 publish OK，加 DELETE 立刻 BOOT_1001；
把 DELETE 的条件右值换成 `CONSTANT` 常量 → 立刻 OK。

所以「按动态记录删除」的正确写法是：

```python
mc.step("delete_entity", "de", entity=ENT, from_node="r2", caption="删除")
# → deleteType=SELECT_PARAM + selectParam 引用 r2 的 DTO 出参
# → 必须去掉 app / structure / condition / methodLegal（混带也会被拒）
```

闸门 **G36** 已拦这两种错法。

### ★ 契约曾经是错的（已修）

`node_contracts.py` 原写 `DELETE_ENTITY.present = ["selectParam"]`，
注释称「语料 CONDITION 8/8 selectParam=null（键在即可）」。
实测全量 fixtures：**8 个 DELETE_ENTITY 样本，含 selectParam 键的是 0 个**——
注释与语料自相矛盾。照原契约生成会被自己的闸门拦死，而平台样本根本没有这个键。
已改为 `present: []`。

## 2. ★★ 运行日志的节点输出是「流程结束时的对象快照」

**这是本轮最危险的陷阱，会让所有中间态断言失效。**

一条 `CREATE(123) → RETRIEVE → CHANGE(999) → RETRIEVE → DELETE` 的流程，
运行日志里「查初始值」那个 RETRIEVE 的输出显示 **lastOffset=999**——
但它执行时数据库里明明是 123。

原因：CHANGE_ENTITY 就地修改了 RETRIEVE 返回的**同一个 DTO 对象**，
日志在流程结束时才序列化，看到的是被改过的值。

佐证：该 RETRIEVE 的 `version=0`（读取时的行版本），而下一个 RETRIEVE 是 `version=1`
（CHANGE 后重新读库）——version 没被内存修改影响，lastOffset 被改了。

**判据修正：**

| 想证明 | 不能用 | 必须用 |
|---|---|---|
| CREATE 写入值 | 日志里 CREATE 的输出 | **数据库行** 或 INSERT 返回后的独立回读 |
| CHANGE 生效 | 日志里 CHANGE 的「更新成功」 | **数据库行**（改后值）或新流程重新查 |
| 中间态 | 日志里任意节点的 output | 独立快照（写进另一个变量/另起流程查） |

## 3. 实体物理表 ≠ 实体名，必须查 information_schema 确认

`迁移断点(MigrationCheckpoint)` 的数据**不在** `migration_checkpoint` 表
（那张表是另一个实体的，主键是 `(task_id, source_table)`，且全表 0 行）。

真实物理表：`migration_1962926556161096741`（17 列，`id` BIGINT 主键）。

**怎么找**：先按业务字段名在全库筛候选表，再用历史数据验证表是活的：

```sql
SELECT table_name, column_name FROM information_schema.columns
 WHERE table_schema='<appDb>' AND column_name IN ('task_id','taskid');
-- 然后逐表 COUNT(*) WHERE task_id LIKE 'P5%'，非 0 的那张才是
```

★ 只查「删后是不是 0 行」不算证据——**表本身可能就是空的**。
必须先确认该表有历史数据（本例 43 行，其中 P5VFY 的记录 `last_offset=123` 保留至今）。

## 4. 删除语义：该实体是物理删除

表 `migration_1962926556161096741` 的列里**没有任何逻辑删除字段**
（`information_schema` 查 `column_name LIKE '%del%'` 返回 0 行）。

因此该实体的删除契约就是物理删除。**别的实体不一定**——判据是先查该表有没有
`deleted` / `is_deleted` / `del_flag` 列，有就按逻辑删除判（查 `deleted=1`），
不能只凭「查不到」下结论。

## 5. 本轮踩过的另外两个坑

- **`_id_ref` 把 BASIC 标量当 DTO 引用**（G17 拦截）：
  `CREATE_ENTITY` 的 output 是 `BIGINTEGER` 插入 ID，不是 DTO。
  对它取 `.id` 字段会生成 `id=<Dto>.id / dtoType=MASTER_ENTITY` 的错误形态。
  正确做法：BASIC 引用 `id="" dtoType=""`，整个值就是 ID 本身。
- **流程名不能带下划线**：`create` 报 `UDC_ENTITY_0001 ... must use a combination
  of letters and numbers that first are letters`。用 `p5wrt607524`，不要 `p5_wrt`。

## 6. 本轮达成的 RUNTIME_VERIFIED 证据（2026-11-02）

### CHANGE_ENTITY

流程 `p5chg608177`：`CREATE(123,7) → RETRIEVE → CHANGE(999,77) → RETRIEVE`，构建 SUCCESS 244s，
执行 `2026-11-02 16:35:00 success=true`。

库内（物理表 `migration_1962926556161096741`）：

```
id            = -4358467840967823245
last_offset   = 999        ← CREATE 写的是 123
processed_rows= 77         ← CREATE 写的是 7
version       = 1          ← CREATE 后是 0
create_time   = 2026-11-02 16:35:00.467
update_time   = 2026-11-02 16:35:00.904   ← 晚于 create_time
```

两个字段都变了 + version 递增 + update_time 变化 → **更新已真实持久化**。

### DELETE_ENTITY

同一条 6 节点流程 `p5wrt607524`（构建 SUCCESS 234s，执行 774ms）：
`CREATE → RETRIEVE → CHANGE → RETRIEVE → DELETE(SELECT_PARAM) → RETRIEVE`，
DELETE 节点输出 `共删除:1条数据`。

库内按 CREATE 返回的 id 查：

```
id = -3560250340828831341  → 0 行     （被删记录）
id = -8721202769169562145  → 1 行     （对照组：已知存在的记录）
```

对照组存在 → 查询有效、表是活的；目标记录 0 行 → 删除生效。
该表无任何逻辑删除列 → 是**物理删除**。

★ 完整证据 JSON：`core/facts/udc/microflow/evidence/write-node-runtime-2026-11-02.json`

## 7. 仍不能证明的

- **批量写**（`CREATE_BATCH_ENTITY` / `CHANGE_BATCH_ENTITY`）仍未跑过，停在 SCHEMA_VERIFIED。
- **`IDS` 模式的删除**未实测。
- **并发/失败路径**未验证（比如删除时记录已被别人删掉会怎样）。
- **其他实体**的删除语义未查——逻辑删除与否取决于该表有没有 `deleted` 列，
  必须逐表确认，不能把本实体的结论外推。
