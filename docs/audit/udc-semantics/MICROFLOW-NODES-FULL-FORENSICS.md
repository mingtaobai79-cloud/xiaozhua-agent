# UDC 微流程节点全量取证（24 类，LIVE）

> 2026-10-28 在 test2 真实编辑器（微流程 `小爪节点探针792`）逐节点实测。
> 每个节点都走完：**初始化 → 选择确定 → 必填 → 前端控制台 → 后端接口 → 全部可点击处**。

## 一、探测方法

脚本：`scratch/probe_node_full.py`（单节点）+ `scratch/probe_all_nodes.py`（批量）

对每个节点记录 5 个阶段：

| 阶段 | 记录内容 |
|---|---|
| `step0_clean` | 清理残留抽屉（不清理会遮住加号，后续全部 PANEL_MISSING） |
| `step1_init` | 加号坐标、右侧面板 24 项完整清单、控制台、网络 |
| `step2_pick` | 抽屉标题、表单项 + required 标记、可点击处、控制台、网络 |
| `step3_required` | 空提交后的 antd 精确错误、`__probe.errors`、控制台、网络 |
| `step4_clickables` | 全部可点击处（类型/文本/中心坐标/尺寸/class） |

## 二、24 个节点的实测结果

| # | 节点 | 抽屉 | 表单项 | 必填 | 可点击处 |
|---|---|---|---|---|---|
| 1 | 分支 | 无抽屉（控制节点） | 0 | 0 | 0 |
| 2 | 列表循环 | 列表循环 | 2 | 2 | 6 |
| 3 | 计数循环 | 计数循环 | 5 | 4 | 10 |
| 4 | 自定义错误 | 自定义错误 | 2 | 1 | 6 |
| 5 | 创建变量 | 创建变量 | 4 | 3 | 14 |
| 6 | 修改变量 | 修改变量 | 2 | 1 | 7 |
| 7 | 创建映射组 | 创建映射组 | 2 | 1 | 4 |
| 8 | 映射操作 | 映射操作 | 9 | 8 | 23 |
| 9 | 创建列表 | 创建列表 | 4 | 3 | 11 |
| 10 | 修改列表 | 修改列表 | 3 | 3 | 10 |
| 11 | 列表操作 | 列表操作 | 4 | 4 | 11 |
| 12 | 查询单条数据 | 查询单条数据 | 9 | 4 | 18 |
| 13 | 查询多条数据 | 查询多条数据 | 8 | 4 | 20 |
| 14 | 插入数据 | 插入数据 | 4 | 4 | 11 |
| 15 | 批量插入数据 | 批量插入数据 | 2 | 2 | 6 |
| 16 | 更新数据 | 更新数据 | 3 | 2 | 6 |
| 17 | 批量更新数据 | 批量更新数据 | 2 | 2 | 6 |
| 18 | 删除数据 | 删除数据 | 3 | 3 | 9 |
| 19 | 自定义服务 | 自定义服务 | 3 | 3 | 9 |
| 20 | 事件投递 | 事件投递 | 4 | 2 | 12 |
| 21 | 子微流程 | 子微流程 | 1 | 1 | 5 |
| 22 | 执行生单规则 | 执行生单规则 | 5 | 5 | 12 |
| 23 | 类型转换 | 类型转换 | 3 | 3 | 8 |
| 24 | 数据转换 | 数据转换 | 6 | 6 | 15 |

原始证据：`scratch/node-full-evidence/SUMMARY.json`（529KB，含每个节点的全部可点击处坐标）

## 三、必填属性的两个层次（重要）

实测发现**同一个节点有两套必填清单，且不一致**：

### 层次一：UI 表单必填（打开抽屉时可见的 `required`）

存于 `components/udc/microflow_constraints.py: NODE_REQUIRED_FIELDS`

### 层次二：保存校验必填（点「保存并提交」时前端逐节点校验）

存于 `components/udc/microflow_constraints.py: SAVE_REQUIRED_FIELDS`

来源是前端真实 console 输出，例如：

```
CONVERT_DATA_qYvHBI 的所有必填属性=> ["convertType","selectParam","title"]
MAP_OPERATION_byvldO 的所有必填属性=> ["selectMap","operationType","theKey","paramType","basic","arrayOrObject","title","nullPromptMessage"]
CUSTOM_ERROR_PaMs96 的所有必填属性=> ["sourceData","selectParam","attrType","attrError"]
FOR_F9Jlvj 的所有必填属性=> ["forStart","forEnd","forStep","targetName"]
```

### 26 类节点的保存校验必填（运行时权威）

| actionType | 保存校验必填字段 |
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

### 条件必填（并集里出现但不恒需）

| 节点 | 字段 | 条件 |
|---|---|---|
| RETRIEVE | nullPromptMessage | 仅 nullHandling=TERMINATION |
| CUSTOM_ERROR | attrError/attrType/selectParam/sourceData | 仅 errorType=POSITION |
| MAP_OPERATION | theKey | 仅 operationType=GET |
| MAP_OPERATION | basic | 仅 paramType=BASIC |
| MAP_OPERATION | nullPromptMessage | 仅 nullHandling=TERMINATION |
| CREATE_VARIABLE | otherType | 仅 paramType=其他 |

## 四、UI 表单与保存校验的真实分歧（5 项）

存于 `UI_VS_SAVE_DIVERGENCE`。这些字段在 UI 上标 required 但保存校验不要，或反之：

| 节点 | 字段 | 说明 |
|---|---|---|
| CHANGE_LIST | dataSource | UI 必填，保存校验未列入（有默认值） |
| CREATE_ENTITY | value | UI 必填，保存校验要 `attrs`（attrs 才是真实提交字段） |
| DELETE_ENTITY | condition | UI 必填，保存校验要 `value`（条件查询用 value 承载） |
| CUSTOM_ERROR | error | GLOBAL 模式字段；保存清单是 POSITION 模式并集 |
| DATA_MAPPING | mappingRows | UI 必填，保存校验要整个 `mappingRule` 对象 |

**生成节点时两者都要满足**，否则要么 UI 报错、要么保存被拦。

## 五、空提交时的 antd 精确错误（最权威的必填来源）

以「类型转换」为例，空提交后 `__probe.errors` 捕获到：

```json
{
  "values": {"convertType": null, "selectParam": null, "title": "类型转换的结果_1"},
  "errorFields": [
    {"name": ["convertType"], "errors": ["请输入变量类型"]},
    {"name": ["selectParam"], "errors": ["请输入选择数据"]}
  ]
}
```

这是 antd Form 的校验结果，`errorFields[].name` 就是真实必填字段名。

## 六、后端接口

| 场景 | 接口 | 说明 |
|---|---|---|
| 打开抽屉 | 无请求 | 节点配置全在前端完成 |
| 空提交（必填未填） | 无请求 | 前端 antd 校验拦截，不发请求 |
| 打开编辑器 | `udcMultiEditLockPost` ×2 | 编辑锁（GET + 释放） |
| 保存并提交 | `udcMicroflowUpdatePost` | 需全部必填通过才发 |
| 保存后校验 | `POST /service/udc/microflow/checkSchema/update` | CheckSchema |

**关键**：必填没填满时**不会发任何请求**，错误只在前端 antd + console。所以「HTTP 200」不能作为成功判据，必须后端回读。

## 七、踩坑记录

1. **批量探测必须清理残留抽屉** —— 不清理会遮住加号，后续节点全部 `PANEL_MISSING`
2. **画布滚动要用 `scrollWidth * 0.95`** —— 直接设 `scrollWidth` 会滚过头（16850/17353），加号跑出视口
3. **`Network.getResponseBody` 不能在回调线程调用** —— 会死锁，需在主线程用 `fetch_bodies()` 补取
4. **console 劫持必须记录全部级别** —— 保存校验的必填清单只走 `console.log`，不是 `error`
5. **单元素元组必须带尾逗号** —— `("title")` 是字符串，`tuple("title")` → `('t','i','t','l','e')`

## 八、自证

```bash
cd <XIAOZHUA_AGENT_ROOT>

# 单节点探针
python scratch/probe_node_full.py 类型转换

# 批量（24 个）
python scratch/probe_all_nodes.py

# 从保存校验提取必填
python scratch/extract_required.py

# 对比静态 vs 运行时
python scratch/diff_required.py

# 单测
.venv\Scripts\python.exe -m pytest tests/test_microflow_save_required.py -q
```
