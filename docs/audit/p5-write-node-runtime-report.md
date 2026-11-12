# P5 写节点运行时验证阶段报告（CHANGE_ENTITY / DELETE_ENTITY）

日期：2026-11-02
环境：lowcode-test2（appId=8704025620829192834）
实体：迁移断点（MigrationCheckpoint），物理表 `migration_1962926556161096741`

## 一、结论

| 能力 | 之前 | 现在 | 证据类型 |
|---|---|---|---|
| `CREATE_ENTITY` | RUNTIME_VERIFIED | 保持 | 插入返 ID + 库内行 |
| `CHANGE_ENTITY` | BUILD_VERIFIED | **RUNTIME_VERIFIED** | 库内两字段变更 + version 0→1 + update_time 变化 |
| `DELETE_ENTITY` | BUILD_VERIFIED | **RUNTIME_VERIFIED** | 目标 id 查 0 行 + 对照 id 查 1 行 + 无逻辑删除列 |

三项都是**数据库级**证据，不是「节点返回成功」。

## 二、完整链路

### 流程 A：六节点全链路（含删除）

```
CREATE_ENTITY(123) → RETRIEVE → CHANGE_ENTITY(999) → RETRIEVE
                   → DELETE_ENTITY(SELECT_PARAM) → RETRIEVE
```

- 流程 `p5wrt607524`，mid `-2789882774368064327`
- 构建 `SUCCESS 234s`，deployId `3791034822499556797`
- 执行 `2026-11-02 16:24:00 success=true 774ms`
- 各节点：CREATE `插入成功返回ID：-3560250340828831341`、
  CHANGE `更新成功`、DELETE `共删除:1条数据`

### 流程 B：只改不删（为拿数据库证据）

```
CREATE_ENTITY(123,7) → RETRIEVE → CHANGE_ENTITY(999,77) → RETRIEVE
```

- 流程 `p5chg608177`，mid `5320699889716593731`，构建 `SUCCESS 244s`
- 执行 `2026-11-02 16:35:00 success=true`
- 库内：`last_offset=999`、`processed_rows=77`、`version=1`、
  `create_time=...467` / `update_time=...904`

## 三、为什么必须分两条流程

运行日志的节点 output 是**流程结束时的对象快照**。流程 A 里「查初始值」那个
RETRIEVE 在 CHANGE 之前执行，日志却显示 999——因为 CHANGE 就地改了同一个 DTO 对象。
所以流程 A 的日志不能证明 123→999，只能证明「删除后记录没了」。

流程 B 不删记录，跑完直接查库，才拿到「改后值持久化」的硬证据。

## 四、本轮修掉的两个真实缺陷

### 1. `DELETE_ENTITY` 契约写错（会拦死所有删除节点）

`node_contracts.py` 原写 `present = ["selectParam"]`，注释称「语料 8/8 selectParam=null」。
实测 8 个真实样本，**含该键的是 0 个**。照原契约生成 → 被自己的闸门拦死。

### 2. `_id_ref` 把 BASIC 标量当 DTO 引用

`CREATE_ENTITY` 的 output 是 `BIGINTEGER` 插入 ID，不是 DTO。
对它取 `.id` 字段会生成 `id=<Dto>.id / dtoType=MASTER_ENTITY` 的错误形态（G17 拦下）。
已加 is_basic 分支：BASIC 引用 `id="" dtoType=""`，整个值就是 ID。

## 五、新增能力

- **G36 闸门**：DELETE_ENTITY 模式与字段自洽。
  把「4 分钟构建 + 无提示的 BOOT_1001」变成「生成期一句话」。
- **`delete_entity(from_node=...)`**：走 SELECT_PARAM，动态记录删除的唯一可用路径。
- **6 条 G36 测试** + 双向契约测试同步。

## 六、安全与清理

- 只操作本轮创建的记录（`task_id` 前缀 `P5WRT` / `P5CHG` / `P5VFY`），未碰业务数据。
- 所有写操作的目标记录由 `CREATE_ENTITY` 返回值动态指定，无硬编码 ID。
- 清理：13 条实验流程全部删除；测试数据 38 行（含上一轮 `P5VFY` 定时流程累积的 37 行）
  按 `task_id` 精确删除，复查残留 0。
- 删除前先查影响范围（GROUP BY 确认 1+37），未做无范围删除。

## 七、仍不能证明

- 批量写（`CREATE_BATCH_ENTITY` / `CHANGE_BATCH_ENTITY`）未跑过。
- `IDS` 模式删除未实测。
- 并发/失败路径未验证。
- 其他实体的删除语义未查——是否逻辑删除取决于该表有无 `deleted` 列，必须逐表确认。
