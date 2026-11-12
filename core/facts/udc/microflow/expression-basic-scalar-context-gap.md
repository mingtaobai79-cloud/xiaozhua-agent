# 表达式引擎：BASIC 标量变量（SUM/SIZE/MIN/MAX 出参）的 context 注册（已修复）

## 症状

branch 的 condition 里引用 SUM/SIZE 等聚合出的**标量**（dataType=BIGINTEGER/INTEGER），
比较操作符报错：

```
expression/check 失败: code=FORMULA_6161 content=None msg=operator not Math,
  失败总数._LIST_OPERATION_801dd5 > 0
```

`FORMULA_6161` = `OPERATOR_TYPE_ERROR`（操作符类型错误）——`>` 期望 Math 类型操作数，
但拿到的 context 类型是 DTO。

## 根因

`components/udc/microflow/expression_model.py` 的 `_build_context_entry`（约 264 行）：

```python
fake_node = {"output": {"name": name, "id": dto, "dataType": "DTO",  # ← 硬编码 DTO
                        "type": "ARRAY" if ref.get("is_array") else "OBJECT"}, ...}
```

它把**所有**节点出参的 context 都注册成 `dataType="DTO"` 的三级树
（节点 → DTO → 字段），没有「BASIC 标量（dataType=BIGINTEGER/INTEGER/...）→ 两级」
的分支。而 `_node_ref`（`expression_dsl.py`）生成的 ref dict 又**没带 dataType 键**
（只有 outputName/title/field/dto_id/fields），register_node_output 无从判断它是标量还是 DTO。

token 侧其实**已经正确**：`expression_model._go` 里 `field == outputName` 时生成两级
`X.X`（`f == n` 分支）。坏的只是 context 侧注册成了 DTO 三级树。

## 语料佐证

`scratch/pmp_schemas.json`（643 条 RELEASE 流程）里**没有**「表达式里引用 BASIC 标量变量」
的样本——扫描 context 里 type 是 BOOLEAN/INTEGER/BIGINTEGER 的子项，0 条命中。
所以两级 context 的确切落库形态**语料无法佐证**，不能凭猜修复。

## 影响范围

- 值槽引用标量出参（`{"field": "sz"}` 写回写节点）**不受影响**——走的是 SelectParam
  引用，不走表达式 context，P7-E2E-1/2 已 RUNTIME_VERIFIED。
- 表达式里引用标量出参（branch condition 的 `{"ref": "sum"}`、FILTER 里比标量）**受影响**，
  报 FORMULA_6161。
- 表达式里引用 DTO 字段（`{"field": "ra.taskId"}`）**不受影响**——三级树正确。

## 反推的合法形态（/expression/check 实测，不是猜）

用 `/expression/check` 试探两种形态：

- 形态 A（顶层 OBJECT + 子项 type=标量）→ **BOOT_0000 SUCCESS** ✅
- 形态 B（顶层直接标量，无 OBJECT 包装）→ FORMULA_6058（变量不存在）❌

合法形态是**形态 A**：顶层 OBJECT + 子项 type=标量类型（无 properties 字段层），
子项 uniformityParams.paramId=标量 javaType（如 java.lang.Long）。

## 修复（已完成）

1. `expression_build.py`：加 `basic_scalar_context_entry(name, title, data_type)`，
   生成形态 A 的两级 context。
2. `expression_dsl.py::_node_ref`：ref dict 加 `node_dtype` 键（= output.dataType）。
3. `expression_model.py::_build_context_entry`：`node_dtype` 非空且非 "DTO" 时
   走 `basic_scalar_context_entry`，否则走原来的三级 DTO 树。

## 验证

P7-E2E-2 验收 6 个场景全部 READY + 构造成功（含条件分支引用 SUM 出参）。
回归测试 `test_basic_scalar_variable_uses_two_level_context` 锁定两级形态。

## 边界

- DTO 对象/数组出参仍走三级 DTO 树（node_dtype=="DTO"），不受影响。
- 值槽引用标量出参（`{"field":"sz"}` 写回写节点）走 SelectParam，不走这里，本就正常。
