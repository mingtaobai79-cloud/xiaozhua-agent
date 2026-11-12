# 表达式 token 四个形态坑 + context 合并（P4 阶段实测）

> 全部回 `BOOT_3000`（无 message），极难定位。形态按语料 1040 条真实表达式裁决。

## 一、四个 token 形态坑

| # | 错写 | 正确 | 语料证据 |
|---|---|---|---|
| 1 | `&&` / `\|\|` | 单字符 `&` / `\|` | OPERATOR 集合只有 `&` `\|` |
| 2 | `=` | `==` | `'=='` 325 次；`'='` 只作 desc，从不作 value |
| 3 | token 缺 `uid` | 每个 token 都要 uid | VARIABLE/OPERATOR/FUNCTION/CONSTANT 全有 |
| 4 | OPERATOR 缺 `desc` | `&`→`and`、`\|`→`or`、`==`→`=` | 802 个 OPERATOR 全有 desc |

另外 `expressionTranslation` 的等号也必须用 `==`（与 token 一致）。

## 二、★ context 必须合并字段（P2 遗留，最难查）

`X.name` 和 `X.driverClassName` 是**两次** `register_node_output` 调用。

早期实现：

```python
if name in self._registered:
    return          # ← 第二个字段直接丢了
```

后果：context 里只有第一个字段，第二个字段在 context 中不存在 →
**checkSchema 回 BOOT_3000**，而 token / translation / 字段元数据看起来**全部正确**，
根本无从下手。

修法（已落地）：已注册时把新字段合并进 `_context_attrs[name]`，
然后 `self.context[i] = self._build_context_entry(name, ref, merged)` **重建**该项。

只要表达式引用了同一节点的两个以上字段就会踩，必查。

## 三、引用完整性核验要递归

`microflow_composer._run_gates` 的 `known` 集合早期只取 `self.nodes` 顶层，
循环体/分支体内节点不算 known → 循环内 `attrs` 引用本体的 RETRIEVE 一律误判「引用悬空」。

```python
from components.udc.microflow.gates import _walk_nodes as _wn
known = {n.get("nodeId") for n in _wn(schema.get("nodes"))}
```

## 四、SUB_MICROFLOW 出参不能留 null

模板 `fixtures/microflow/node_modals/SUB_MICROFLOW.json` 的 `output` 是 `null`，
但真实 305 个样本都有 `output.name`。拿不到子流程自身出参声明时按 BOOLEAN 兜底
（真实样本里最常见：出参「结果」），并补 `outPutDesc` / `outputName`。
