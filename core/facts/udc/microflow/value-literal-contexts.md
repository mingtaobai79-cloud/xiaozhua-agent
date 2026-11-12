# 常量字面量：两个语境不能混用

> 证据：智能项目管理平台 643 条 RELEASE 微流程的字段级统计（`scratch/pmp_schemas.json`）
> 触发场景：组装路径首次真发布被 `checkSchema` 报 `value.type DATA_INVALID`

## 结论

同一个「常量」在两个位置是**两种不同类型**：

| 位置 | 正确类型 | 生产出现次数 |
|---|---|---|
| 值槽位 `value` / `attrs[].value` / `entries[].value` | `{"type": "Simple", "simple": ..., "desc": ...}` | **322** |
| 查询条件 `condition[].conditions[].rightParams[]` | `{"type": "CONSTANT", "value": ..., "desc": ...}` | **193** |

**`CONSTANT` 在值槽位出现 0 次。**

用错的表现：`checkSchema/update` 返回
```
code=BOOT_0000, check=false
[创建变量] CREATE_VARIABLE_xxx,创建变量.value.type → DATA_INVALID
[插入数据] CREATE_ENTITY_xxx,插入数据.attrs.value.type → DATA_INVALID
```

## 值槽位的完整类型集（全平台实测）

| 类型 | value 槽位 | attrs 槽位 |
|---|---|---|
| `SelectParam` | 711 | 1771 |
| `Expression` | 417 | 581 |
| `Simple` | 322 | 435 |
| `CtpEnum` | 12 | 77 |
| `Enum` | 0 | 16 |
| `CONSTANT` | **0** | **0** |

## 查询条件 rightParams 的类型集

| 类型 | 次数 | 说明 |
|---|---|---|
| `CONTEXT_VARIABLE` | 470 | 引用前序节点字段，`value` 是 JSON 字符串 |
| `CONSTANT` | 193 | 字面量 |
| `EXPRESSION` | 136 | 表达式，`value` 是 JSON 字符串 |

## 代码约定

`components/construction/microflow_fields.py` 两个函数各管一边：

```python
constant(v)  # {"type": "CONSTANT", "value": v, "desc": v}  ← 只用于查询条件
simple(v)    # {"type": "Simple", "simple": v, "desc": v}  ← 只用于值槽位
```

`microflow_composer.py` 用两个内部函数分流，避免调用方记错：

```python
_val(v)       # 值槽位：非 dict 就套 simple
_cond_val(v)  # 查询条件：非 dict 就套 constant
```

## 校验

契约闸门 `contract_gate.check_schema()` 会扫 `value` / `attrs` / `entries` / `mappingRule`
四个槽位，发现 `CONSTANT` 即报错。对 643 条真实流程回归 **0 误报**。

---

# dtoType：只在实体列表上必需

> 触发场景：把「LIST_OPERATION.selectParam 必须有 dtoType」写成一刀切，
> 在 643 条真实流程上误报 **168 次**

## 真实分布

| `selectParam.dtoType` | 数量 | 特征 |
|---|---|---|
| 有 | 803 | 全是实体/自定义 DTO：`SUB_ENTITY` 527 / `MASTER_ENTITY` 200 / `CUSTOM` 76 |
| 无 | 168 | 全是**基础类型列表**：`BIGINTEGER` 92 / `STRING` 70 / `DECIMAL` 6，`udcApp=None` |

## 正确判据

```python
is_entity_list = (sp.get("dataType") == "DTO"
                  or sp.get("udcApp") is True
                  or bool(sp.get("relationEntity")))
if is_entity_list and not sp.get("dtoType"):
    # 报错
```

基础类型列表缺 `dtoType` **是合法的**，不能要求必须有。

---

# 模板残留引用：构造器必须主动清

> 触发场景：`sub_microflow` 造出的节点被 G2 报「表达式引用悬空 `_RETRIEVE_KNCEzh`」

`fixtures/microflow/node_templates/SUB_MICROFLOW.json` 里带着模板录制时那条流程的
节点引用（`attrs[].value.selectParam` 指向 `_RETRIEVE_KNCEzh`）。
换流程后该节点不存在，G2 直接拦。

**规则**：构造器里凡是「有默认值的存在引用字段」，构造时必须显式覆盖或清空，
不能继承模板值。`sub_microflow` 现在在没传 `attrs` 时清掉
`attrs` / `mappingType` / `value` / `pageInfo`。

同类待查：任何模板里含 `_RETRIEVE_xxx` / `_CREATE_LIST_xxx` / `CREATE_VARIABLE_xxx`
字面量的节点模板。用
```bash
grep -l "_RETRIEVE_\|_CREATE_LIST_\|_BUSINESS_EVENT_" fixtures/microflow/node_templates/*.json
```
列出来逐一确认。

---

# 发布契约

```
1. create  : GraphQL udcMicroflowCreatePost      state=DRAFT
2. 取 guid : GraphQL udcMicroflowFindByIdGet     （create 返回不含 guid）
3. 发布    : REST  POST /service/udc/microflow/checkSchema/update
             ★ 必须带 appId —— 少它直接 BOOT_1001「appId must not be null」
             ★ 共 15 字段：appId id name caption type triggerType state dataSchema
               serviceInterface sourceType creationMethod groupType versionCode
               openApi restApi microFlowGroupId
4. 回读    : FindByIdGet 确认 state=RELEASE
```

**不能走 GraphQL `udcMicroflowUpdatePost` 发布**：提交 `state=RELEASE` 后回读仍是 `DRAFT`。

**副作用**：在 UI 编辑器里打开已发布流程会把状态打回 `DRAFT`，需要重新发布。

代码在 `components/udc/microflow/deploy.py`（`deploy()` 一步到位，失败自动删半成品）。
