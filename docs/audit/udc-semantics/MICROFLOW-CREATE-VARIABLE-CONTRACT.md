# 创建变量节点 —— 7 种 paramType × 7 种 dataType 全覆盖落库

测试环境：探针流程 `xzhNodeProbe907792`（mid `-6371737850148111694`）
节点：`CREATE_VARIABLE_P3SPbN`
验证方式：每次点「确认」→ `udcMicroflowUpdatePost` → `read_schema` 回读后端 `dataSchema`

---

## 一、7 种 paramType 的表单差异（实测）

所有 paramType 共用同一个抽屉，但**字段集合完全不同**：

| paramType | radio 文案 | 表单字段（* 必填） | 联动 dataType |
|---|---|---|---|
| `BASIC` | 基本类型 | 变量类型* / 数据类型* / 默认值 / 节点出参名称* | 用户选（7 选 1） |
| `ENTITY_OBJECT` | 实体对象 | 变量类型* / 选择应用* / 实体对象* / 节点出参名称* | **自动 = DTO** |
| `DEFAULT_OBJECT` | 自定义对象 | 变量类型* / 选择应用* / 自定义对象* / 节点出参名称* | **自动 = DTO** |
| `ENUM` | 选项集 | 变量类型* / 选择应用* / 选项集* / 默认值 / 节点出参名称* | **自动 = ENUM** |
| `METADATA` | 元数据 | 变量类型* / 选择应用* / 元数据类型* / 选择元数据* / 节点出参名称* | **自动 = METADATA** |
| `MESSAGE` | 事件对象 | 变量类型* / 选择应用* / 事件对象* / 节点出参名称* | **自动 = DTO** |
| `OTHER` | 其他 | 变量类型* / 其他类型* / 选择应用* / 自定义对象* / 排序规则* / 节点出参名称* | **自动 = DTO** |

**关键规则：只有 BASIC 让用户选数据类型，其余 6 种由 paramType 决定。**

---

## 二、7 种 paramType 的落库结构（全部回读确认）

### BASIC（基本类型）

```json
{
  "paramType": "BASIC",
  "dataType": "STRING",
  "title": "objVar2",
  "value": {"type": "Simple", "simple": "abc", "desc": "abc"}
}
```

`value` 是 `{type:"Simple", simple:<原始值>, desc:<同值>}`。
切换 dataType 会把 `value` 重置为 `null`（`setemptybeforechanged="value"`）。

### ENTITY_OBJECT（实体对象）

```json
{
  "paramType": "ENTITY_OBJECT",
  "dataType": "DTO",
  "title": "变量_1",
  "value": null,
  "structure": {
    "key": "com.seeyon.<app>.domain.entity.XzhExp950795",
    "id": "com.seeyon.<app>.dto.XzhExp950795Dto",
    "label": "小爪实验实体950795V2",
    "dataType": "DTO",
    "entity": "com.seeyon.<app>.domain.entity.XzhExp950795",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true,
    "fullName": "com.seeyon.<app>.dto.XzhExp950795Dto",
    "relationEntity": "474806313816300867",
    "methodLegal": {"available":true,"complexCondition":true,"seniorMethod":true,"serviceType":"NONE","interfaceClassFullName":null}
  },
  "output": {
    "id": "com.seeyon.<app>.dto.XzhExp950795Dto",
    "javaType": "com.seeyon.<app>.dto.XzhExp950795Dto",
    "dataType": "DTO",
    "type": "OBJECT",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true
  }
}
```

### DEFAULT_OBJECT（自定义对象）

```json
{
  "paramType": "DEFAULT_OBJECT",
  "dataType": "DTO",
  "value": null,
  "structure": {
    "key": "com.seeyon.<app>.dto.microflow.XzhOutItemDto",
    "fullName": "com.seeyon.<app>.dto.microflow.XzhOutItemDto",
    "label": "出参明细对象",
    "dataType": "DTO",
    "dtoType": "CUSTOM"
  },
  "output": {
    "name": "_CREATE_VARIABLE_3kwr4G",
    "dataType": "DTO",
    "dtoType": "CUSTOM",
    "javaType": "com.seeyon.<app>.dto.microflow.XzhOutItemDto",
    "id": "com.seeyon.<app>.dto.microflow.XzhOutItemDto"
  }
}
```

注意路径带 `.dto.microflow.` 段（自定义对象在 microflow 子包）。

### ENUM（选项集）

```json
{
  "paramType": "ENUM",
  "dataType": "ENUM",
  "title": "enumVar",
  "value": null,
  "structure": {
    "label": "小爪扣减单据状态",
    "key": "com.seeyon.<app>.enums.XzhDedBillbillStatus",
    "value": "com.seeyon.<app>.enums.XzhDedBillbillStatus",
    "fullName": "com.seeyon.<app>.enums.XzhDedBillbillStatus"
  }
}
```

`key` / `value` / `fullName` 三者相同，都在 `.enums.` 下。

### METADATA（元数据）

```json
{
  "paramType": "METADATA",
  "dataType": "METADATA",
  "title": "metaVar",
  "value": null,
  "structure": null,
  "output": {
    "id": "8643109752427203840",
    "javaType": "java.lang.String",
    "dataType": "METADATA",
    "type": "OBJECT",
    "desc": "metaVar",
    "udcApp": true,
    "name": "_CREATE_VARIABLE_oAFOMN"
  }
}
```

**唯一一个 `structure: null` 的类型** —— 元数据信息全在 `output.id`（数字 id）+ 表单里的「元数据类型 / 选择元数据」两段式选择。
元数据类型选项：页面 / 表单 / …（实测选了「页面」→「导入导出模板管理 [web端]」）。

### MESSAGE（事件对象）

```json
{
  "paramType": "MESSAGE",
  "dataType": "DTO",
  "title": "msgVar",
  "value": null,
  "structure": {
    "key": "com.seeyon.<app>.dto.YsEvtData2",
    "label": "验收新增事件2",
    "id": "com.seeyon.<app>.dto.YsEvtData2",
    "value": "com.seeyon.<app>.dto.YsEvtData2",
    "dataType": "DTO",
    "dtoType": "CUSTOM",
    "udcApp": false,
    "fullName": "com.seeyon.<app>.dto.YsEvtData2"
  }
}
```

`udcApp:false` —— 事件 DTO 不属于 UDC 应用层。

### OTHER（其他 —— 系统排序对象）

```json
{
  "paramType": "OTHER",
  "otherType": "SYSTEM_SORT_OBJECT",
  "dataType": "DTO",
  "title": "otherVar",
  "value": null,
  "structure": {
    "label": "出参明细对象",
    "dataType": "DTO",
    "dtoType": "CUSTOM",
    "key": "com.seeyon.<app>.dto.microflow.XzhOutItemDto",
    "fullName": "com.seeyon.<app>.dto.microflow.XzhOutItemDto"
  },
  "sortParams": [{
    "sortType": "ASC",
    "attrType": {
      "validate": true,
      "id": "com.seeyon.<app>.dto.microflow.XzhOutItemDto.concatText",
      "name": "concatText",
      "fullName": "com.seeyon.<app>.dto.microflow.XzhOutItemDto.concatText",
      "md5": "3292839912956..."
    }
  }],
  "output": {
    "name": "_CREATE_VARIABLE_aRjsCh",
    "dataType": "DTO",
    "dtoType": "CUSTOM",
    "javaType": "com.seeyon.boot.transport.Sort",
    "id": "com.seeyon.boot.transport.Sort"
  }
}
```

**独有 `sortParams`**，且 `output.javaType` 固定为 `com.seeyon.boot.transport.Sort`。

「排序规则」不是 select，是一个「**添加规则**」按钮：
点击后出现 `[选择字段 ▾] [升序 ▾] [添加规则]`，可加多行。
字段选项来自所选自定义对象的属性（示例只列出 2 个：`拼接文本 [文本]`、`计算结果 [小数]`）。

---

## 三、7 种 dataType 全部实测落库（BASIC）

| dataType | 中文 | 落库确认 | value |
|---|---|---|---|
| `STRING` | 文本 | ✓ | `{type:"Simple", simple:"abc", desc:"abc"}` |
| `INTEGER` | 整数 | ✓ | null（切类型被清空） |
| `BIGINTEGER` | 长整数 | ✓ | null |
| `DECIMAL` | 小数 | ✓ | null |
| `BOOLEAN` | 布尔 | ✓ | null |
| `DATE` | 日期 | ✓ | null |
| `DATETIME` | 日期时间 | ✓ | null |

下拉选项顺序固定：`文本 / 整数 / 长整数 / 小数 / 布尔 / 日期 / 日期时间`。

对照（创建变量节点的落库）：
```
previous dataType: DATETIME  →  dataType: INTEGER ... 等逐个切换
```
每次切换后 `value` 必被清空（`setemptybeforechanged="value"`），需重新填默认值。

---

## 四、操作要点（本轮新增）

### 1. `setFieldValue` 对自定义 setting 控件无效

这些字段是 `settingkey` 驱动的自定义组件（`<div settingkey="dataType" ishidden="paramType != 'BASIC'">`），
`form.setFieldValue()` 只改 form 值、**不重算 `ishidden`、不改 UI**。

必须**真实点击 radio**（`label.ant-radio-button-wrapper` 的 `.click()` 即可）才能切换。

### 2. 下拉 `width=0` 的真相是 `document.hidden`

症状：点开下拉后 `.ant-select-dropdown` 存在、有 N 个选项，但 `w=0 h=0 opacity=0`。
原因：`document.hidden === true`，antd 的动画/测量不跑。

**`document.hidden` 会反复变回 true**（不是一次修复永久有效）。
解法：**每次点击前都调** `F.ensure_visible(d)`，且点击后校验下拉宽度，为 0 就重试。

封装见 `scratch/basic_datatypes.py::open_select()`。

### 3. 抽屉里 label 精确匹配的坑

`.ant-form-item label` 会把 radio 的 `<label class="ant-radio-button-wrapper">` 也算进去，
读取表单字段列表要用 `.ant-form-item > .ant-col > .ant-form-item-label label`。

「排序规则」行里的两个 select 属于子 form-item（label 为空），
要按 `placeholder === '选择字段'` 定位，不能按 label。

### 4. 提交仍用 Enter

7×7 全部通过 `submit_drawer`（Enter 优先）提交成功，`errorFields:[] outOfDate:true` 不再阻塞。

---

## 五、产物

- `scratch/paramtype_all.py` / `.log` / `.json` —— 6 种 paramType 自动化
- `scratch/basic_datatypes.py` / `.log` / `.json` —— 7 种 dataType 自动化
- `scratch/enum_all.json` —— 全部 24 节点的 radio/select 选项快照
