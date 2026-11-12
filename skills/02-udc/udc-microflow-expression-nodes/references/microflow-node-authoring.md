# 微流程节点必须“前端确认过”，不是拼 JSON

## 1. 前端真实链路（控制台原文，可复现）

在管理器里手动加一个节点，控制台依次打印：

```
添加节点 => addNode {type: 'udc-microflow-edit/addNode', payload: {…}}
回填 nodeConfig {description: '', foreach: {...}, isCompleted: false}
attributes[key] {validate: true, id: '<DTO>.f01text', name: 'f01text', md5: '3289788337887872601', ...}
## 右值组件表达式参数: {config: {...}, ExpressionComponent: ƒ}
```

只有前端做得到、整包 POST `dataSchema` 做不到的三件事：

1. **nodeConfig 回填**：`description` / `foreach` / `isCompleted` 等默认值由前端按节点类型补；
2. **attributes 带 md5**：实体每个字段随节点配置下发 `{id, name, fullName, md5}`；
   手写 `attrType` 缺 md5（或 md5 与当前实体不一致）→ 面板红条「所选‘数据’已变更」；
3. **右值组件**：值编辑器（含表达式）由前端 `ExpressionComponent` 挂载时生成 `config`；
   手写的 `expression.schema` 只是它的持久化形态，没有组件态就没有右值。

## 2. 现象 ↔ 根因（一张表定位）

| UI 现象 | 根因 |
|---|---|
| 所选‘数据’已变更 / 所选数据已失效 | attrType 缺 md5，或引用的属性 id 与当前实体不一致 |
| 「请选择」（应用/实体下拉空） | 节点级 `app` / `structure` 没走前端回填 |
| 分支面板整片空白 | BRANCH 的 `conditions[]` 没按前端 nodeConfig 生成 |
| 「节点开发中…」 | `selectMethod` 不完整，前端无法渲服务节点 |
| 修改变量不赋值 / 循环写死 | 生成器只铺了结构，没填业务值（属“空壳”，会被打回） |
| 面板开关都正常但发布仍在 DRAFT | 深度校验失败静默降级（见 gates §3.1） |

## 3. 正确做法：模板来自真实流程，生成器只做替换

### 3.0 先 harvest：从既有真实流程抽模板（最快、可批量）

不必先把每类节点手动加一遍：平台里已有的流程（客户标准流程 + 已验收流程）本身就是前端回填后的产物。

```python
svcs = list_services(c, APP)          # 只有摘要，没有 dataSchema
d = GET /service/udc/microflow/findById/<id>   # 取 data.content.dataSchema
# 递归 walk(nodes + conditions[].nodes)，按 actionType 分组，
# 每类取 json 长度最大的那条当模板 → fixtures/microflow/node_templates/<ACTION>.json
# 索引写 _index.json（count / bytes / 来自哪几条流程）
```

实测一次可拿到 20+ 类（CREATE_VARIABLE / RETRIEVE / RETRIEVE_ARRAY / CREATE_ENTITY / CHANGE_ENTITY /
CHANGE_VARIABLE / BRANCH / FOR / BREAK / CUSTOM_ERROR / DELETE_ENTITY / CALL_APP_SERVICE /
SUB_MICROFLOW / DATA_MAPPING / CALL_DATA_FLOW …）。

选模板的判断：**同类型里字段最全的那条**（字节数最大），而不是最新那条；
官方/客户流程优先于自己生成的流程 —— 自己生成的节点本身就是缺字段的。

### 3.1 手动补模板（harvest 缺某类时才做）

1. 在某个草稿里**手动**添加目标节点 → 点「确认」触发前端校验与回填 →
   从 store（`udc-microflow-edit/addNode` 之后的 nodeConfig）或保存后的 `dataSchema` 取该节点快照；
2. 每类节点存一份：`fixtures/microflow/node_templates/<ACTION_TYPE>.json`；
   实体属性全量表（含 md5）存 `fixtures/microflow/entity_attrs.json`；
3. 生成器只替换：应用 / 实体 / 字段 / 引用(`SelectParam`) / 右值；
   **`attrType` 整块照抄模板**（含 md5），只换 `value`；
4. 表达式沿用模板的 `runtimeData.executableExpr` 前缀与 `uniformityParams`，只换 tokens/translation；
5. 引用只能指向**前面**已存在节点的出参（顺序闸门 G8）；
6. 先只生成 1 条，在 UI 里逐节点点开验到零异常，再批量。

## 4. 验收口径（逐节点，不是看徽标）

```python
# 每个节点：scrollIntoView → CDP 真实鼠标事件 → 读面板
c.evaluate("document.querySelectorAll('.udc-microflow-editor-node.opration').length")
# 面板文本判红：已失效 / 请重新选择 / 必填参数未配置 / 请选择 / 不能为空
```

- 草稿编辑器的 URL `/microflow/editor/<id>?appId=…` 会跳回 `editor/create`；
  **草稿只能从列表点进去**，列表树项要先 `scrollIntoView({block:'center'})` 再发 `Input.dispatchMouseEvent`
  （`CdpClient.send`，不是 `.cdp`）；只点标题 span 有时不跳编辑器，需点行尾「更多 → 编辑」。
- 工具栏的「创建微流程」按钮 className 含 `add-button`，**不是**画布上节点之间的“+”插点；
  按 `add-button` 点击会弹出新建流程弹窗（类型/触发方式/名称/编码），误判成“菜单打不开”。
  画布插点是连接线上的小方块，坐标要用**节点元素**（`.udc-microflow-editor-node.opration`）自身的
  `getBoundingClientRect()` 推算，且必须先 `scrollIntoView`，否则 y 落在视口外、合成事件静默无效。
- 类名普遍带哈希后缀（`index-module_add-button__lXXXX`），**不要用精确类选择器**；
  用 `[...document.querySelectorAll('button,div')].filter(e => String(e.className).includes('xxx'))`。
- 注入 JS 时避免 `\s`、`\n` 这类转义（Python 字符串会先吃掉一层，导致 `evaluate` 报 Uncaught）：
  换行用 `String.fromCharCode(10)`，空白归一用 `replace(/[ ]+/g,' ')`。
- 面板只有 30–50 字符通常意味着该节点几乎没配置，按“空壳”处理。

## 4.1 查询条件的真实形制（RETRIEVE / RETRIEVE_ARRAY）

`condition` 不是单个对象，而是**条件组数组**，右值是 JSON 字符串：

```jsonc
"condition": [{
  "type": "GROUP", "uuid": "…",
  "conditions": [{
    "type": "CONDITION",
    "leftParam": {"id": "<DTO>.sourceDatasourceId", "type": "OBJECT", "javaType": "java.lang.Long",
                  "dto": "_sourceDatasourceId", "field": "sourceDatasourceId",
                  "desc": "源数据源ID", "dataType": "BIGINTEGER", "multiSelect": false},
    "operator": {"value": "EQ", "desc": "="},
    "rightParams": [{"type": "CONTEXT_VARIABLE",
                      "value": "{\"key\":\"_FLOW_INPUT_xxx.f01text\",…}"}],
    "logicalOperator": "…"
  }]
}]
```

生成的节点若缺 `needCascade` / `selectType` / `scope` / `methodLegal` / `app` / `structure`，
面板会显示空下拉——这些字段从模板整块照抄，只替换 `structure`（实体 DTO）与 `leftParam/rightParams`。

## 4.2 引用（SelectParam）与流程输入的精确形态（手写必错，照抄真实样本）

**基本类型变量引用**（来自真实流程 `小爪全节点24-V16`）——修改变量/取值时用它：

```jsonc
{"id": null,                      // 基本变量 id 是 null（实体变量才是 DTO fullName）
 "javaType": "java.lang.String", "dataType": "STRING", "type": "OBJECT",
 "desc": "vText",                 // = 变量标题(title)，不是 nodeId
 "name": "_CREATE_VARIABLE_xxx",  // = outputName（带下划线前缀）
 "outputName": "_CREATE_VARIABLE_xxx",
 "position": "parent", "description": "vText",
 "nodeInfo": {"nodeId": "CREATE_VARIABLE_xxx",   // nodeId 不带下划线
              "type": "ACTIVITY", "actionType": "CREATE_VARIABLE"}}
```

关键约定（错一个就「变量」下拉空白）：
- `output.name` = `"_" + nodeId`；`nodeInfo.nodeId` = 不带下划线的 nodeId。
- 基本变量引用**没有** `key` / `path` 字段；实体变量引用才有
  `dtoType/udcApp/relationEntity/id=<DTO fullName>`（此时 id 不是 null）。
- 手写常犯：`name` 写成 title、`id` 写成 outputName、漏 `nodeInfo`。

**流程输入（_FLOW_INPUT_xxx）是「参数」页定义的 CUSTOM 微流程入参 DTO，不是实体 DTO。**
拿实体 DTO（如 `YsFull6956Dto`）冒充流程输入、再引用 `_FLOW_INPUT_xxx.f01text`，字段在真实入参里
不存在 → 查询条件右值渲染为空、报「值不能为空」。先到「参数」页签确认入参字段再引用；
不确定字段时右值先用常量跑通，再接输入引用。

**替换 conditions 必须整组替换，不是只改 `conditions[0]`。**
harvest 来的模板可能带 N 条旧条件（如 1.10 的 targetDatasourceId/enabled/targetTable/ID）；只改第一条会
残留其余旧字段。正确做法：`node['condition'] = [<一条新 GROUP>]` 整体覆盖，别逐条 patch。

## 5. 清理（批量自测产物）

```
POST /service/udc/microflow/delete  {"appId":"<appId>","id":"<microflowId>"}
→ {"code":"BOOT_0000","content":true}
```

逐条删、逐条 `list_services` 复查；删完打印剩余条数与残留 caption，不要只看返回码。

## 6. checkSchema 完整请求体契约（拿到 errorMessage 明细的唯一口径）

REST 最小 body（只有 appId/name/caption/type/dataSchema/state）打 `udcMicroflowCheckSchemaUpdatePost`
会 `BOOT_1001 参数错误`；完整契约必须带这些字段（`guid` 从 `findById` 拿，必填）：

```jsonc
POST /service/udc/graphql?udcMicroflowCheckSchemaUpdatePost
variables.params0 = {
  "appId":"…","caption":"…","name":"…","type":"SERVICE","triggerType":"MANUAL",
  "id":"<流程id>","guid":"<guid>",
  "state":"RELEASE","publishState":"UNPUBLISH",
  "groupType":"DEFAULT","versionCode":0,"sourceType":"PAGE",
  "creationMethod":"MANUAL","serviceInterface":"CustomMicroFlowAppService",
  "openApi":"STOP","microFlowGroupId":"0","restApi":"DISABLED","restPath":"",
  "businessEventCaption":"-","scheduleCaption":"-","sourceId":null,
  "lastVersionMetadataState":"DISABLED","lastEnableTime":null,"lastEnableVersion":null,
  "dataSchema":"<整段 JSON 字符串>"}
```

响应 `content{check, errors, errorMessage[{errorCode,errorType,level,message,nodeCaption,nodeId,path,propertyKey}]}`。
`update` 返回 `BOOT_0000 SUCCESS` 但流程仍 `DRAFT` = 深度校验失败静默降级；只有这个端点（或 UI「检查」按钮）
能拿到具体是哪条 —— 不要拿 `update` 的返回码当发布成功的证据。

## 7. 元数据重载依赖链（最重要的机制，用户反复强调）

每个节点的字段下拉、多选、值编辑器选项**都不是固定的**，而是跟着**前序节点出参的实体类型**走：

1. 选一个「来源数据/变量」后（如 更新数据=选择更新的数据=vKey[小爪实验实体950795V2]），
   前端**按这个实体的元数据重载**字段列表（attributes 带 md5）；
2. 点「确定」一个节点 → 它的元数据重载完成 → **下游节点可选的字段随之更新**；
3. 修改变量/更新数据/插入数据 等节点的字段赋值，来源是「它引用的那个实体」的 metadata，不是别的实体。

对生成器的硬约束：**节点必须按顺序生成（前序先落定），不能整包并行写**；
每个节点的字段赋值必须从「它引用的实体」的 metadata 取字段（含 md5），拿别的实体字段硬填 = 「所选数据已变更」。

这是「链路」的普遍规律：**每个节点的选择/勾选都触发一个接口，后端加载该节点要用的依赖数据**，
不止前端校验。选什么 → 触发什么接口 → 加载什么数据，是节点配置的真实骨架：

| 操作 | 触发接口/加载数据 |
|---|---|
| 子微流程：选中某个微流程服务 | `udcMicroflowServiceListSubMfPost` 列子微流程 → 再加载所选子微流程自己的 入参(参数配置) 和 出参(出参描述) |
| 更新/插入数据：选实体 | 加载该实体 attributes（含 md5） |
| 查询节点：选实体 | 加载字段（筛选/排序/聚合候选） |
| 选「来源数据/变量」 | 按该实体元数据重载字段列表 |

所以生成器不能只凭一套静态字段模板硬填——必须先走接口拿真实依赖数据（字段/入参/出参），
再填下游字段，否则「少很多东西」。取证同理：节点能展示什么、能选什么，去抓它点击时发的接口，别查 DB。

### 7.1 接口命名规律 + 抓取方法

所有节点配置接口都是 GraphQL，POST `/service/udc/graphql`，query string 里带 operation 名，
命名 = `udcMicroflow` + 动词 + 对象 + Post/Get（读=Get，写=Post），多 operation 用 `&` 合并批量：

- 选择应用 → `udcMicroflowSearchAppsPost`；选择实体（`ant-tree-select` 树形）→ `udcMicroflowSearchTreeEntityPost`
- 选择自定义对象/DTO → `udcMicroflowFindCustomDtoPost`；选择子微流程 → `udcMicroflowServiceListSubMfPost`
- 读流程详情 → `udcMicroflowFindByIdGet`；保存前检查 → `udcMicroflowCheckSchemaUpdatePost`；图标名 → `appCommonIconNameListPost`

抓接口两条路（`providers/cdp.py::CdpClient`）：
1. `install_fetch_recorder()` 装页面 fetch/XHR 拦截器 → 操作页面 → `read_captured()` 读最近 50 条（url/reqBody/respBody 截断）；
2. 补历史清单：`performance.getEntriesByType('resource')` 过滤 `graphql?`，按 `&` 拆 query string 拿全部已触发的 operation 名。

坑：前端对已加载数据有缓存，**接口只在首次加载触发，事后重放点击不重发**。要抓全某节点每个下拉的接口，
必须首次操作时同步抓，或去前端懒加载 chunk 里 grep 全部 `udcMicroflow*Post` 定义（主 bundle 里接口名是动态拼接，grep 不到）。

打开画布节点的配置抽屉：点**节点中心**（不是标题 span，点标题只开「参数配置」），用
`Input.dispatchMouseEvent` 三连（mouseMoved/pressed/released）发真实鼠标事件。

## 8. 24 类节点全量清单 + 每类弹窗的必填契约

节点面板分组（权威，来源=节点面板，共 24 类，注意没有独立的「跳出循环」顶层节点，BREAK 是循环内部子动作）：

- 逻辑活动：分支 / 列表循环 / 计数循环 / 自定义错误
- 变量活动：创建变量 / 修改变量
- 映射活动：创建映射组(CREATE_MAP) / 映射操作(MAP_OPERATION)
- 列表活动：创建列表 / 修改列表(CHANGE_LIST) / 列表操作(LIST_OPERATION)
- 数据活动：查询单条(RETRIEVE) / 查询多条(RETRIEVE_ARRAY) / 插入(CREATE_ENTITY) / 批量插入(CREATE_BATCH_ENTITY) / 更新(CHANGE_ENTITY) / 批量更新(CHANGE_BATCH_ENTITY) / 删除(DELETE_ENTITY)
- 基础服务：自定义服务 / 事件投递(PUBLISH_BUSINESS_EVENT) / 子微流程 / 执行生单规则(CALL_DATA_FLOW)
- 数据加工：类型转换(CONVERT_DATA) / 数据转换(DATA_MAPPING)

每类节点弹窗的**必填字段清单 + 校验规则**逐类抓（`fixtures/microflow/node_modals/<ACTION>.json`）：
点开某类节点弹窗 → 读可见 `.ant-modal/.ant-drawer`（`offsetParent!==null` 的最后一个）里的 `.ant-form-item`，
label + 红星(`[class*=required]`) + 控件类型/占位。生成器逐节点过这份必填清单，缺一个必填就不许过 ——
因为「写进 JSON ≠ 确认」，必填没填全照样报错。

### 8.1 分页对象必须先创建（不是凭空写 PageInfo）

`pageSearch=true` 的 `pageInfo` 指向一个**分页对象变量**，它由「创建变量」产生：

```
创建变量 → 变量类型 = 「其他」 → 其他类型 = 「系统分页对象」(com.seeyon.boot.transport.PageInfo)
```

然后查询多条数据里 `分页查询=是` → `分页数据(请选择参数)` 引用这个变量。

### 8.2 查询多条 4 种查询方式（字段随方式变化）

- 条件查询：筛选条件/排序/分页查询/分页数据
- ID集合查询：选择该记录的ID集合（引用变量，无分页）
- 查询总数：筛选条件（出参=总数）
- 其他聚合查询：聚合方法(求和/求平均值/求最大值/求最小值) + 计算字段（实体字段下拉）

### 8.3 节点语义速记（用代码类比秒懂节点干什么）

| 节点 | 语义类比 | 要点 |
|---|---|---|
| 计数循环 | `for(i=起; i<=止; i+=步)` | 循环体内取「循环变量」（序号） |
| 列表循环 | `for-each` | 循环体内引用「当前遍历的那条数据」 |
| 映射组 / 映射操作 | `Map` / `get·put·remove·keySet` | 映射组=Map 自定义对象；操作4种=获取/赋值/删除/获取键列表 |
| 分支 | `if/else if/else` | 每个「符合条件」分支的条件=布尔表达式，点「条件设置」直接开表达式编辑器 |
| 自定义错误 | `throw new Xxx + 回滚事务` | 阻断流程；提示方式=全局提示 / 定位到页面元素 |
| 批量插入/更新/删除 | 吃**实体列表**（多条数据） | 列表来源3种：创建列表出参 / 前序出参带列表 / 查询多条(RETRIEVE_ARRAY)出参 |
| 删除(指定删除) | 引用前序实体，单条或列表都行 | 只要前序节点出参即可删 |
| 事件投递 | `publish(event)` | 事件对象≠设置里的自定义对象；分「应用间(异步)/应用内(同步)」事件对象，监听事件节点能收到同一事件 |
