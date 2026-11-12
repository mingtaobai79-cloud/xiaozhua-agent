# DATA_MAPPING（数据转换）运行时契约

> 实测：`RETRIEVE_ARRAY(3 条) → DATA_MAPPING(sourceTable→taskId) → CREATE_BATCH_ENTITY`
> 写回 3 行 `task_id='DM-SRC'`，未映射字段为空 —— 证明是映射产物而不是原样复制。

## 1. 形态

```json
{"actionType":"DATA_MAPPING","type":"ACTIVITY",
 "selectParam": {源，type=ARRAY，dtoType=MASTER_ENTITY，position=parent},
 "structure":  {目标实体，key="<源实体全名>_<目标实体全名>"},
 "mappingRule": {uuid, id=目标 dto 全名, caption, subobjects:[], targetType:"ENTITY",
                mappingRows:[{uuid, targetField:{...}, mappingMode:"REFERENCE",
                              value:{reference:{...}}}]},
 "output": {type:"ARRAY", javaType:<目标 dto>, dataType:"DTO"}}
```

同实体自映射也要拼 `structure.key` 的两段（`<dto>_<dto>`），不能只写一段。

## 2. 三条硬约束

1. **上游必须是列表**（G29）。单对象主实体上游 → 生成代码把输出声明成 `List<Dto>` 再对单对象取字段
   → 构建 FAIL `找不到符号 getXxx()`。语料 39 条样本里也没有单对象形态。
2. **`output.type="ARRAY"` 的赋值必须在 `_entity_output(entity, ...)` 之后。**
   `_entity_output` 会整体覆盖 `output`，写在前面的 ARRAY 判定会退回 OBJECT，
   下游 `LIST_OPERATION` 一引用就被 G31 判「type=ARRAY 与出参声明 OBJECT 不一致」。
3. **映射行的两端字段要从 DSL 传进来**（`src_field` / `dst_field`），默认 `name→name` 只适用于
   真有 `name` 字段的实体；`taskId`/`sourceTable` 这类实体直接 KeyError。
   透传要改两处：`LogicGraphRunner._do_data_mapping` 和 `MicroflowComposer._st_data_mapping`，
   只改一处等于没改。

## 3. 已知未修

`LIST_OPERATION(FIRST_ONE)` 接手 DATA_MAPPING 的输出会丢 `javaType`，生成代码把
`_LIST_OPERATION_xxx` 当类名引用 → 构建「找不到符号: 类 _LIST_OPERATION_xxx」。
需要单对象时先用 `CREATE_BATCH_ENTITY` 绕开；要彻底修就得让 `list_operation` 的
FIRST_ONE/LAST_ONE/PICK_ONE 分支回填 `id`/`javaType`，并加一条闸门守住。

## 4. 未覆盖

多字段映射行、跨实体映射（源/目标异构）、子表映射。当前证据只到「单字段 / 同实体 / 列表上游」。
