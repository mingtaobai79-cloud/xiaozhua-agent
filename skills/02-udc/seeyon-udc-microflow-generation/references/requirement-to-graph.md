# P4 业务需求 → 逻辑图：分三步，LLM 只碰中间那步

> 代码：`components/construction/requirement_compiler.py::BusinessRequirementCompiler`。

## 职责边界（最重要，别越位）

```
用户业务需求
  ↓  【LLM】理解：识别实体、输入输出、条件、循环、异常
业务意图草稿（JSON）
  ↓  【Python】BusinessRequirementCompiler：真名解析 + 结构校验 + 歧义扫描 + 纠错
逻辑图（LogicGraph）
  ↓  【Python】LogicGraphRunner（见 logic-graph.md）
节点 schema → 保存 → checkSchema → 构建
```

两条硬约束：

- **LLM 不许直接产平台 JSON，也不许写 Python 调构造器。** 它只产出「业务意图草稿」。
- **Python 编译器不调 LLM、不联网。** 它只做确定性的名字解析与校验。
  这和仓库既有纪律一致（`requirement_parser.py` 同样声明「不调 LLM」，解析不出就 UNVERIFIED，不伪造）。

## 编译器的四件事

1. **归一化**（不改语义）：补别名、`for_each.source.ref → list` 等形态统一，每条改动进 `fixes` 留痕。
2. **真名解析**：实体必须是平台上真实存在的 caption 或 dtoFullName。
   - 精确命中 → 通过；dtoFullName 命中 → 回填 caption
   - 关键词**唯一**候选 → 自动纠正并留痕
   - **多候选 / 无候选 → 直接 BLOCKED，列候选给用户，绝不替他挑**
3. **业务语义歧义扫描**（原文级）：给候选 + 各自业务后果，不替用户选。
   常见四类：「其他」范围 / 「修改数据」改哪些字段 / 判断对象 / 匹配精度。
4. **业务陷阱自检**：写操作直引循环项这类会必然被 G20 拦的形态，提前换成可读中文提示。

## 三档产出（status）

| status | 含义 | 后续 |
|---|---|---|
| `READY` | 结构合法 + 真名全命中 | 交 LogicGraphRunner |
| `AMBIGUOUS` | 结构合法但有必须人拍板的歧义 | 带问题清单问用户 |
| `BLOCKED` | 结构非法或真名解析失败 | 必须改草稿，**`graph` 必须为 None** |

`BLOCKED` 时返回 `graph=None` 是硬性要求 —— 不许「带着问题上路」。

## 不能声称「全自动」的地方

含字段引用的表达式生成后带 `needs_ui_finalize=True`（原因见 expression-engine.md：
`executableExpr` 只能由设计器运行期生成）。交付时必须告诉用户进设计器点一次「确定」，
否则运行期表达式为空。**这是一条真实能力边界，不是待办。**

## 验收方式

用**不同复杂度**的真实业务需求跑，不要只做一个演示：
查询统计 / 查询修改 / 多条件判断 / 批量循环修改 / 批量复制 / 多层嵌套 / 调用子流程 / 异常处理。
每条记录：编译状态、纠错轮次、构造结果、保存结果、耗时。
失败用例要能说清是「编译器没拦住」还是「执行器/平台边界」——前者要补校验，后者要如实上报。
