# 批量写节点运行时契约（CREATE_BATCH_ENTITY / CHANGE_BATCH_ENTITY）

> 2026-11-02 实测于 test2（appId=8704025620829192834，实体=迁移断点）。
> 只写跑过、有数据库证据的结论；推断标注。

## 1. 两个节点的形态（语料 95 个样本一致）

| 项 | 值 |
|---|---|
| 必填 | `selectParam`（实体对象列表）+ `output.name` |
| `attrs` | **没有**（95 个样本 0 个带 attrs） |
| 出参 | `dataType=INTEGER / type=OBJECT / desc="批量更新…成功的数量_1"` = **影响行数** |
| 语义 | 不做字段映射，把**列表元素自带的字段值**原样落库 |

真实依据：业务流 `r44_e1_orig`、前端抓包 `real-type0-node-structures`，
以及 `fixtures/microflow/node_modals/*.json` 的弹窗说明
（只有「选择记录列表」和「节点出参名称」两个字段）。

★ 仓库里曾有两套实现：`microflow_nodes_batch.py`（attrs + DTO 数组出参，**错**）
和 `microflow_nodes_extra.py`（无 attrs + INTEGER，**对**）。已把前者改为转发，
避免「导入哪个模块决定生成对不对」。

## 2. ★★★ CREATE_BATCH 的列表元素必须**没有 id**

**踩坑实录**：直接拿 `RETRIEVE_ARRAY` 的列表去批量插入 →

```
运行日志节点：批量插入 success=False
errorMsg: 违反主键约束
```

因为 RETRIEVE_ARRAY 返回的是**已落库的 DTO，带 id**，批量插入会拿原 id 再插一遍。

**正确做法**（已验证）：

```
CREATE_VARIABLE(entity, fields={…})   → 一个新的、内存里的实体对象
CREATE_LIST_ENTITY(entity)            → 空实体对象列表（paramType=ENTITY_OBJECT, value=[]）
CHANGE_LIST_ADD(list=空列表, item=对象) → 列表里有 1 个元素
CREATE_BATCH_ENTITY(list=该列表)      → 插入
```

实测结果：`批量插入成功：1条数据`，库内 1 行，
`task_id/last_offset/processed_rows/last_pk` 与 CREATE_VARIABLE 里配的值逐一对上，
`id` 由平台生成（不是配置里给的）。

## 3. ★★ CHANGE_BATCH 写的是「列表元素的值」

因为节点没有 attrs，唯一可能的语义就是「把列表里每个 DTO 的当前字段值写回数据库」。
用一组对照实验证明：

```
1 CREATE_ENTITY(111) ×2
2 RETRIEVE_ARRAY(taskId=MARK)        → 列表 [d1@111, d2@111]
3 RETRIEVE(by_id=ce1) → CHANGE_ENTITY(999)   → 库内 row1 = 999
4 CHANGE_BATCH_ENTITY(步骤 2 的列表)  → 把 111 写回去
```

实测库内：

| id | last_offset | version | update_time |
|---|---|---|---|
| 1573776132924538060 (t_b1) | **111**（步骤 3 刚改成 999） | 1 | 17:10:01.339 |
| 5683794467914762646 (t_b2) | 111 | 1 | 17:10:01.339 |

- 999 零残留 → 被步骤 4 覆盖掉了
- 两行 `update_time` **完全相同**且晚于 `create_time` → 最后是一条批量 UPDATE 同时改了两行
- 节点出参 `批量更新成功：2条数据`

这就同时证明了「执行了 UPDATE」和「写的是列表元素的值」。

## 4. CHANGE_LIST 没有出参（原地改列表）

真实样本（含 3 条业务流）`CHANGE_LIST.output` **恒为 null**。
它原地修改列表变量，**不产出新列表**。

所以：

```python
mc.step("create_list_entity", "cl", entity=ENT)        # 空列表
mc.step("change_list_add", "cl2", list_node="cl", item="cv")   # 往 cl 里加元素
mc.step("create_batch_entity", "cbC", entity=ENT, list_node="cl")   # ★ 引 cl，不是 cl2
```

引 `cl2` 会让 batch 的 `selectParam.outputName` 为空 →
本地全部闸门放行，publish 才被拒：

```
check=false errors=[('[4-批量插入]', '….selectParam.outputName', 'PROPERTY_IS_REQUIRED')]
```

闸门 **G37** 已拦（引用槽 outputName 为空 / 悬空引用）。

## 5. 仍不能证明的

- 批量写**部分失败**的行为（比如 10 条里第 5 条违反约束）——本轮只跑了全成功路径。
- `IDS` 模式、`FOR_EACH` 循环里逐条改再批量提交的组合未验证。
- 大批量（上千条）的分批/超时行为未验证。

## 6. 运维注意：定时流程删掉之前会一直跑

`rotationType=MINUTE, value=1` 的定时流程不是「跑一次就停」——
本轮 CREATE_BATCH 那条流程在 17:18 / 17:23 / 17:28 各跑了一次，
每次插入 1 行（id 不同，不冲突）。删掉流程后定时才停（实测 75 秒后无新行）。

**验证流程的收尾顺序**：先删流程 → 再按唯一标记清数据 → 等一个周期复查残留。
只清数据不删流程，数据会持续长出来。
