# 字段赋值来源策略 + 数据血缘审计（Data Lineage Audit）

> 任务书（2026-11-04 用户纠偏）：每个写实体字段都要能追溯来源，来源策略落 DSL，
> 输出 lineage-report.json + 统计，评估「节点串得少、关联性不强」的问题。
> 工具：`components/construction/lineage_audit.py`；测试：`tests/test_lineage_audit.py`。

## 7 种来源（枚举 + DSL 值槽形态）

| 来源 | 枚举 | DSL 值槽形态 | 说明 |
|---|---|---|---|
| 固定值 | `CONSTANT` | `{"const": <bool\|int\|float\|str>}` | 字面量；基础数据/枚举/固定状态允许 |
| 触发入参 | `TRIGGER_INPUT` | `{"input": <入参名>}` 或 `{"field": "$input.<名>"}` | 流程 MANUAL 入参 |
| 前序节点 | `PREVIOUS_NODE` | `{"field": <别名>}` | 引用前序节点整节点出参（标量） |
| 前序节点字段 | `PREVIOUS_NODE_FIELD` | `{"field": <别名>.<字段>}` | 引用前序节点 DTO 的字段 |
| 循环项 | `LOOP_ITEM` | `{"item": <循环别名>, "field": <字段>}` 或 `{"field": <循环别名>.<字段>}` | for_each 循环项字段 |
| 表达式 | `EXPRESSION` | `{"op"/"arith"/"fn": ...}` | 计算（算术/比较/函数） |
| 系统值 | `SYSTEM_VALUE` | `{"system": <名>}` | 系统变量（当前时间/用户等，预留） |

值槽三态（`intent_draft_schema.py` VALUE_SLOTS）是 const/field/input，表达式内扩展
op/arith/fn/item。`classify_value()` 的判定顺序敏感：const/input 优先 → 表达式 →
item（循环项）→ field（别名/字段级/整节点三级）。

## 来源策略落 DSL（每个字段显式可追溯）

写节点 fields 的值槽本身就是来源声明——`{"field": "req.totalAmount"}` 即
PREVIOUS_NODE_FIELD。不额外加 `source` 键，靠 `classify_value` 从值槽形态推断，
避免「声明与值槽不一致」的双源问题。审计时逐个字段分类、统计。

## 血缘审计输出（lineage-report.json）

```python
from components.construction.lineage_audit import audit_lineage
rep = audit_lineage(draft)   # draft = build_draft() 的逻辑图
# rep = {
#   "fields": [{node, kind, entity, field, source, ref?, value}, ...],
#   "metrics": {
#     "sources": {7 种来源: 字段数},
#     "const_fields": N, "prev_node_refs": N, "field_refs": N,
#     "loop_item_refs": N, "expr_refs": N, "trigger_input_refs": N,
#     "isolated_nodes": [有数据出参却没被引用的节点 id],
#     "hardcoded_links": [{node, field, value, hint}...],
#   },
# }
```

CLI：`python components/construction/lineage_audit.py <draft.json>` 或 stdin。

## 两个高级指标（判「关联性不强」）

- **孤立节点**：`DATA_NODE_KINDS`（retrieve/retrieve_array/create_variable/
  list_operation）有数据出参却没被任何下游引用。读出来不用 = 链上断了，
  是「节点串得少」的直接证据。写节点/分支/子流程出参本可不被引用，不算孤立。
- **硬编码关联**（HINT，非硬拦）：同一写节点里，有字段引用前序上下文，另一些
  字段却是固定值——提示「本应继承前序结果却硬编码」，需人工核查业务语义
  （固定枚举/状态允许 const，不误报）。

## 引用目标提取（孤立检测的依据）

`_extract_refs` 递归全 draft，认两类引用：
1. 值槽引用 `{"field": <别名>...}` / `{"item": <别名>}`（第一段=别名）；
2. 裸字符串引用键 `list_node/by_id_from/from_node/list/ids_from/page_info_from`。
不碰实体字段名（`sort_by/cond_field` 等不是节点引用）。

## 实战（MF-01 采购申请与供应商比价）

```
字段血缘：
  wOk.taskId         CONSTANT          MF01-BUDGET-OK
  wOk.processedRows  PREVIOUS_NODE     <- bestId（引用最优报价）
  wNo.taskId         CONSTANT          MF01-BUDGET-NO
  wNo.processedRows  CONSTANT          1
孤立节点：['items']（查了申请明细却没参与比价——真孤立，业务上该用）
硬编码提示：wOk.taskId = MF01-BUDGET-OK（同节点有 bestId 引用，taskId 却硬编码）
```

判据：孤立节点非空 = 有读节点没用上；`field_refs/loop_item_refs/expr_refs` 全 0 =
只有整节点引用和常量，没有字段级数据流转，正是「各是各的」的信号。

## 案例质量评分（score_case）

`score_case(draft)` 把血缘指标折成一个 0-100 分 + 分级（S≥90/A≥75/B≥60/C<60）：

- 数据流密度：非 const 字段占比（引用/表达式/入参 = 节点间数据流转），低于 50% 扣分（最多 30）
- 孤立节点：每个扣 20（读而不用是硬伤）
- 硬编码关联：每个扣 10（该引用却硬编码）

纯读流程（无写字段）给 100（无可评字段，不误扣）。实测 6 正式流程：

| 流程 | 分 | 级 | 引用率 | 备注 |
|---|---|---|---|---|
| MF-02 采购订单生成 | 80 | A | 0.62 | 字段级引用+循环项，最好 |
| MF-03 仓库收货 | 70 | B | 0.56 | 硬编码 3 |
| MF-04 发票核对付款 | 60 | B | 0.33 | 硬编码 3 |
| MF-01 采购申请比价 | 55 | C | 0.25 | 孤立 items + 硬编码，最差 |
| MF-00 审批子流程 | 70 | B | 0.00 | 单字段全 const（状态更新，业务合理） |

评分是**相对排序工具**，不是绝对判据——MF-00 审批子流程「更新状态=已审批」用 const 是
业务上合理的（固定状态值），引用率 0 不代表差；MF-01 查了明细却不用才是真问题。
低分先看「孤立节点」和「硬编码提示」两条，再决定是业务合理还是该改。
