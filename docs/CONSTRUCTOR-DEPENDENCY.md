# 构造器模块依赖图（现状 → 目标分组）

> 审计 components/construction/ 节点构造器分布，输出目标分组。**本轮只记录依赖，不移动文件。**

## 1. 现状：5 个文件 + 重复定义

| 文件 | 角色 | 定义的节点构造器 |
|---|---|---|
| `microflow_nodes.py` | 值/字段/表达式原语 | value_select_param、expr_context_dto、expr_context_var、value_expression、token、create_entity_node、replace_node |
| `microflow_nodes_v2.py` | 数据节点（V2） | retrieve、retrieve_by_id、retrieve_array、create_entity、change_entity、delete_entity、create_variable、change_variable、convert_data、call_data_flow、break_node、create_variable_page_info |
| `microflow_nodes_extra.py` | 集合/逻辑/服务（X） | create_list、change_list、list_operation、create_map、map_operation、custom_error、branch、for_count、create_batch_entity、change_batch_entity、convert_data、create_list_entity、change_list_add、list_size、sub_microflow、call_app_service、publish_business_event、call_data_flow |
| `microflow_nodes_svc.py` | 服务（S，早期分组） | call_app_service、call_data_flow、sub_microflow、type_convert、data_mapping、for_each、event_delivery |
| `microflow_nodes_batch.py` | 转发（已合并） | 只 `from .microflow_nodes_extra import ...`，24 行转发，保留为兼容模块名扫描 |

composer 引用：`microflow_nodes_v2 as V2`、`microflow_nodes_extra as X`、`microflow_nodes_svc as S`。

## 2. 重复定义清单（核心问题）

| actionType | 重复位置 | 份数 |
|---|---|---|
| `call_app_service` | extra(656) + svc(37) | 2 |
| `call_data_flow` | v2(691) + extra(697) + svc(115) | 3 |
| `convert_data` | v2(652) + extra(498) | 2 |
| `sub_microflow` | extra(628) + svc(157) | 2 |
| `create_batch_entity`/`change_batch_entity` | extra + batch（已合并，转发） | 已解决 |

**「导入哪个模块决定生成对不对」是真实存在的分叉**（batch 文件注释已自述此坑）。
这正是需要 Node Registry 统一入口的根子：消除同一 actionType 多份不一致定义。

## 3. 目标分组（规划，不移动）

```
components/construction/
├── registry/
│   ├── node_registry.py         # 统一节点发现入口（actionType → 唯一构造器）
│   └── capability_registry.py   # 能力矩阵（已存在，迁入）
├── nodes/
│   ├── data/                    # retrieve/retrieve_array/create_entity/change_entity/delete_entity
│   ├── control/                 # branch/for_each/for_count/custom_error/break
│   ├── collection/              # create_list/change_list/list_operation/create_map/map_operation/batch
│   ├── integration/             # call_app_service/call_data_flow/data_mapping/sub_microflow/publish_event
│   └── variable/                # create_variable/change_variable/convert_data/type_convert
├── expression/                  # microflow_nodes.py 的原语 + expression_*
├── logic_graph/                 # logic_graph.py + loop_scope.py
├── requirement/                 # requirement_compiler.py + requirement_parser.py + intent_draft_schema.py
├── lineage/                     # lineage_audit.py
└── pipeline/                    # p5_*.py + finalizer
```

## 4. 迁移原则（用户定，不能先移动再修 import）

1. **先建立 Node Registry**，把 actionType → 唯一构造器的映射收口（消除重复定义）。
2. **按依赖审计逐步迁入**，不是一把梭移动 5 个文件。
3. 迁移顺序：先 registry（新增）→ 再逐域迁入 nodes/ → 最后删重复定义。
4. 每次迁移跑回归（`pytest tests/` 2628 全绿）。
5. 保留 `microflow_nodes_batch.py` 这类转发模块，直到按模块名扫描的工具（microflow_coverage.py）也迁到 registry。

## 5. 本轮交付

【现状】只输出依赖图和目标分组，**不移动、不合并、不删重复定义**。
真正的迁移是阶段 D（用户定：Skill 分发、Facts 分层、构造器模块化之后）。
