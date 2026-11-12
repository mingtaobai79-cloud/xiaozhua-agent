# RETRIEVE（查询单条数据）节点契约

取证方式：前端抽屉逐项真操作 → 点确认 → `udcMicroflowFindByIdGet` 回读 `dataSchema` 对比。
本文只写**跨应用稳定的机制**，不含任何具体应用/实体/字段。

---

## 一、表单项全集（顺序即 UI 顺序）

| # | label | 控件 | 说明 |
|---|---|---|---|
| 1 | 查询方式 | radio | `条件查询 CONDITION` / `ID查询 IDS` |
| 2 | 选择应用 | select | 默认当前应用 |
| 3 | 选择实体 | tree-select | 切换后**重置 structure 并清空 condition** |
| 4 | 过滤条件 | 点击区 | 仅 `CONDITION` 出现，点开独立弹窗 |
| 5 | （ID 值） | input | 仅 `IDS` 出现，必填「请输入选择该记录的ID」 |
| 6 | 排序规则 | 添加规则按钮 + 行 | 可 0~N 行 |
| 7 | 查询聚合对象 | radio | `关闭` / `开启` → `needCascade` |
| 8 | 节点出参名称 | input | 写 `title` |
| 9 | 未查到数据时 | radio | `TERMINATION` / `CONTINUE` |
| 10 | 提示内容 | textarea `#nullPromptMessage` | 仅 `TERMINATION` 出现且必填 |

### 两条联动铁律

- **切 `IDS` 会隐藏过滤条件、显示 ID 输入框**；切回 `CONDITION` 反之。两个分支的必填集不同，
  在 `IDS` 下直接提交会报 `structure: 请输入选择实体` + `value: 请输入选择该记录的ID`。
- **改「选择实体」= 清空 condition 和 structure**。实测把实体从 A 换成 B 再保存，
  `condition` 变成 `null`、`structure` 换成 B。所以调实体必须在配条件之前。

---

## 二、落库字段

```json
{
  "actionType": "RETRIEVE",
  "fetchType": "CONDITION",          // CONDITION | IDS
  "nullHandling": "TERMINATION",     // TERMINATION | CONTINUE
  "nullPromptMessage": "...",        // 仅 TERMINATION；CONTINUE 时为 null
  "needCascade": false,              // 查询聚合对象
  "title": "查询结果",                // 节点出参名称
  "selectType": "DTO",
  "scope": "OBJECT",
  "structure": { "key": "<domain 全名>", "id": "<dto 全名>", "label": "<实体中文名>",
                 "dataType": "DTO", "entity": "<domain 全名>", "dtoType": "MASTER_ENTITY",
                 "udcApp": true, "fullName": "<dto 全名>", "relationEntity": "<实体数字 id>" },
  "condition": [ { "type": "GROUP", "uuid": "...", "conditions": [ ... ] } ],
  "sortParams": [ { "sortType": "ASC", "attrType": { ...字段完整属性... } } ],
  "output": { "id": "<dto 全名>", "javaType": "<dto 全名>", "dataType": "DTO",
              "type": "OBJECT", "dtoType": "MASTER_ENTITY", "udcApp": true,
              "name": "_RETRIEVE_xxxxxx" }
}
```

判据：`output.id` 必须等于 structure 的 `dto` 全名。写成 `null` / `""` 说明节点已损坏。

---

## 三、过滤条件弹窗（独立 `.ant-modal`，标题「过滤条件」）

### 行结构

```
条件  [字段 tree-select]  [运算符 select]  [右值区]
                                   └─ input + 「+」按钮 → popover「高级模式」→ 表达式面板
```

DOM 类名（跨应用稳定）：

- 字段：`.ant-col-8 .ant-select.ant-tree-select`
- 运算符：`.condition-item__operator .ant-select`
- 右值区：`.condition-item__rightParams`

### 右值三种形态（`rightParams[].type`）

| type | 落库 value |
|---|---|
| `CONSTANT` | 原始字符串 |
| `CONTEXT_VARIABLE` | SelectParam 对象 |
| `EXPRESSION` | `{"designData":{...},"runtimeData":{...}}` 字符串，走 `/expression/transform` |

### 右值可编辑的前置条件

**必须「选字段 + 选运算符」之后右值输入框才 `readOnly=false`。**
只选字段时 `readOnly=true`，直接 setInput 会被忽略——这是最容易被误判为「填不进去」的坑。

### 运算符集合随字段类型变化

实测同一个节点、不同字段类型的运算符列表不同：

```
数值型：= != 在 不在 < <= > >= 介于 不介于
日期型：= != < <= > >= 介于 不介于 为空 不为空
```

所以不能写死运算符全集，必须每次打开下拉现取。

### 条件组的真实行为

「添加」是 dropdown trigger，菜单两项：`添加条件` / `添加条件组`。
**实测两者产生的 DOM 完全一样**——都是同一个 `conditionGroupHorizontal` 里追加一行，
行首出现「且」连接，**不会产生嵌套 GROUP**。

结论：多条件是「平铺 + AND 逻辑符」，UI 层不提供嵌套条件组。

---

## 四、排序规则

- 「添加规则」按钮：`button.ant-btn-block`（在 `排序规则` 这个 form-item 内），可重复点加多行
- 每行两个 select：`[选择字段]` `[升序/降序]`，加 `sy-icon.lined-remove-circle` 删除图标
- 字段选项格式：`<字段中文名> [<dataType 中文>]`，如 `实验数量 [整数]`
- `attrType` 落的是字段完整属性（含 md5 / customs.id / javaType / sort），不是仅名字
- 升序 `ASC` / 降序 `DESC`

**行定位必须按子行索引**，不能按「选择字段」占位文本筛：前一行填好后占位文本消失，
筛出来的数组长度从 2 变 1，索引立刻错位。

---

## 五、前端校验（`errorFields` 实测文案）

| 场景 | errorFields |
|---|---|
| IDS 未选实体 | `structure: 请输入选择实体` |
| IDS 未填 ID | `value: 请输入选择该记录的ID` |
| 排序规则未选字段 | `sortParams[i].attrType: 请选择字段` |
| 条件字段未选 | 条件弹窗内不关，`确定` 无效 |

---

## 六、自动化脚本

- `scratch/mf/env.py` —— 环境发现（app/实体/字段/schema），零硬编码
- `scratch/mf/ui.py` —— 抽屉/下拉/提交操作层
- `scratch/retrieve_probe.py` —— 本节点穷举脚本
- `scratch/cond_flow.py` —— 配一条完整过滤条件（字段/运算符/值由命令行传入）
