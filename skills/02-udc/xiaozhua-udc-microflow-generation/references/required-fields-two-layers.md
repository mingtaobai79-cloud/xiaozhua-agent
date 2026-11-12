# 必填的两层：UI 表单 vs 保存校验

生成或校验 UDC 微流程节点时，必填字段有**两个独立来源**，不一致，必须都满足。

| 层 | 采集方式 | 代码位置 | 语义 |
|---|---|---|---|
| UI 表单层 | 打开节点抽屉，读 `.ant-form-item-required` | `NODE_REQUIRED_FIELDS` | 生成节点时要填什么 |
| 保存校验层 | 点「保存并提交」，读 console 的 `X 的所有必填属性=> [...]` | `SAVE_REQUIRED_FIELDS` | 提交前的最终闸门 |

保存校验层是**运行时权威**：前端真实执行，含条件必填。UI 表单层是「打开抽屉时看得见的红星」，会被 `ishidden` 条件隐藏，且与保存校验存在真实分歧。

## 一、怎么取保存校验清单（一次操作拿全 26 类）

不必逐节点点开抽屉。只要流程里已有各类节点，点一次「保存并提交」就能拿到全部：

```python
d.eval("(()=>{window.__clog=[];return 1})()")          # 清空
ui.click_react(d, "document.getElementById('microflow_save')")
time.sleep(9)
items = json.loads(d.eval("JSON.stringify((window.__clog||[]).slice(-80))"))
```

解析（`re.match(r'^(\S+) 的所有必填属性=> (\[.*\])$', msg)`）：

```
CONVERT_DATA_qYvHBI 的所有必填属性=> ["convertType","selectParam","title"]
MAP_OPERATION_byvldO 的所有必填属性=> ["selectMap","operationType","theKey","paramType","basic","arrayOrObject","title","nullPromptMessage"]
CUSTOM_ERROR_PaMs96 的所有必填属性=> ["sourceData","selectParam","attrType","attrError"]
```

**节点 ID 前缀含下划线，不能 `split('_')[0]`**——那样 `CALL_APP_SERVICE_x` 会变成 `CALL`、`DATA_MAPPING_x` 变成 `DATA`。用最长前缀匹配表（`SUB_MICROFLOW_` 先于 `SUB_`、`RETRIEVE_ARRAY_` 先于 `RETRIEVE_`、`CALL_DATA_FLOW_FRONT_` 先于 `CALL_DATA_FLOW_`），`ForEach_`→FOR_EACH、`For_`→FOR、`MFStartNode`→START、`MFEndNode`→END 单独列。

保存校验的 console 只走 `console.log`，**不是 `error`**——钩子只挂 `error/warn` 会完全抓不到。

## 二、26 类保存校验必填（运行时实测）

| actionType | 必填字段 |
|---|---|
| START / END / BRANCH / CONDITION / BREAK | （无） |
| CREATE_VARIABLE | dataType, otherType, paramType, title |
| CHANGE_VARIABLE | selectParam |
| CREATE_LIST | dataType, paramType, title |
| CHANGE_LIST | action, selectParam |
| CREATE_MAP | title |
| MAP_OPERATION | arrayOrObject, basic, nullPromptMessage, operationType, paramType, selectMap, theKey, title |
| LIST_OPERATION | operationType, selectParam, title |
| RETRIEVE | app, nullPromptMessage, structure, title |
| RETRIEVE_ARRAY | app, pageInfo, structure, variableTitle |
| CREATE_ENTITY | app, attrs, mappingType, structure, title |
| CHANGE_ENTITY | selectParam, title |
| CREATE_BATCH_ENTITY | selectParam, title |
| CHANGE_BATCH_ENTITY | selectParam, title |
| DELETE_ENTITY | app, deleteType, structure, title, value |
| CONVERT_DATA | convertType, selectParam, title |
| DATA_MAPPING | app, mappingRule, selectParam, structure, targetType, title |
| SUB_MICROFLOW | mappingType, mfService, outputName |
| CALL_APP_SERVICE | app, outputName, selectMethod |
| CUSTOM_ERROR | attrError, attrType, selectParam, sourceData |
| FOR | forEnd, forStart, forStep, targetName |
| FOR_EACH | selectParam, targetName |

`FOR` 的 `operator` 不在内（有默认 `<=`）；`RETRIEVE_ARRAY` 用 `variableTitle` 而非 `title`。

## 三、条件必填（并集里出现，但不恒需）

| 节点 | 字段 | 条件 |
|---|---|---|
| RETRIEVE | nullPromptMessage | 仅 nullHandling=TERMINATION |
| CUSTOM_ERROR | attrError / attrType / selectParam / sourceData | 仅 errorType=POSITION |
| MAP_OPERATION | theKey | 仅 operationType=GET |
| MAP_OPERATION | basic | 仅 paramType=BASIC |
| MAP_OPERATION | nullPromptMessage | 仅 nullHandling=TERMINATION |
| CREATE_VARIABLE | otherType | 仅 paramType=其他 |

校验器按并集报错就会误伤：`RETRIEVE` 在 `nullHandling=CONTINUE` 时不该要求 `nullPromptMessage`。条件字段必须单独建模，不能塞进无条件表。

## 四、UI 表单 vs 保存校验的真实分歧

| 节点 | UI 表单要 | 保存校验要 | 说明 |
|---|---|---|---|
| CHANGE_LIST | dataSource | （未列入） | UI 必填但保存不校验，该字段有默认值 |
| CREATE_ENTITY | value | attrs | `attrs` 才是真实提交字段 |
| DELETE_ENTITY | condition | value | 条件查询用 `value` 承载 |
| CUSTOM_ERROR | error | sourceData/selectParam/attrType/attrError | 保存清单是 POSITION 模式并集；GLOBAL 模式只填 `error` |
| DATA_MAPPING | mappingRows | mappingRule | 保存校验要整个对象，不是行数组 |

登记这类分歧时配一条「分歧必须真实存在」的测试（`(field in ui) != (field in save)`），否则分歧表会退化成垃圾桶，把真漏的字段也放进去。

## 五、空提交的 antd errorFields（最精确的字段名来源）

抽屉里什么都不填直接点「确定」，antd 抛的 `unhandledrejection` 里 `errorFields[].name` 就是真实表单字段名，`errors[0]` 是中文提示：

```json
{"values":{"convertType":null,"selectParam":null,"title":"类型转换的结果_1"},
 "errorFields":[{"name":["convertType"],"errors":["请输入变量类型"]},
                {"name":["selectParam"],"errors":["请输入选择数据"]}],
 "outOfDate":false}
```

用途：确认某个字段的**真实 key**（出参名是 `title` 不是 `name`；`convertType` 不是 `dataType`）。比猜字段名快得多。

注意与 `outOfDate:true` 区分：`errorFields` 空 + `outOfDate:true` 是时序断言（可绕过），`errorFields` 非空是真业务校验（禁止绕过）。

## 六、落库实现的两个坑

**单元素元组必须带尾逗号。** 用脚本批量改写必填表时，`("title")` 是字符串不是元组，下游 `set()`/迭代会把它拆成 `('t','i','t','l','e')`，校验静默失效且不报错：

```python
('"%s": ("%s",),' % (action, fields[0]))   # 单字段
('"%s": (%s),' % (action, ', '.join('"%s"' % f for f in fields)))  # 多字段
```

写完后必须实测一次 `all(len(f) > 1 for f in fields)`。

**批量改写前先备份，改完跑全量测试。** 必填表被离线构造路径和测试同时依赖，覆盖式修改会让十几条测试同时红——红的那些要逐条判断是「旧期望错了」还是「新表过严」，不能一把改测试迁就。
