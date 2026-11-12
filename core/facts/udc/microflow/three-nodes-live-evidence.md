# 三个节点真机实证（来自智能项目管理平台 643 条 RELEASE 微流程）

取证方式：只读拉取 `样例平台应用（已脱敏）` 全部 RELEASE 微流程的
`dataSchema`（643 条），统计 + 挖样本。**没有创建、修改、删除任何对象。**

样本基数：
- 413 个实体（169 主实体）
- 678 条微流程，其中 643 条 RELEASE
- 1438 个分支条件节点，nodeTypeList 26 类节点全部出现过（除 CONNECTOR）

---

## 1. CONDITION（分支条件）— 真实形态与三种分支

### 结论：CONDITION 不是独立节点，永远内嵌在 BRANCH.conditions[]

`nodeTypeList` 里**没有** CONDITION（26 项不含它）。画布上「分支」节点的两个/多个
分支口就是 CONDITION，`type:"CONDITION"`，`actionType` 为 `null`。

### 真实分布（1981 个 CONDITION / 326 条流程）

| name | 数量 | caption | expression |
|---|---|---|---|
| `ifBranch` | 952 | 符合条件即进入该分支 | **必填**（有表达式 1040 个） |
| `elseBranch` | 941 | 不符合条件即进入该分支 | **恒为 null** |
| `elseIfBranch` | 88 | （第三个分支口） | 有表达式 |

**三种 name 是同一个 `type:"CONDITION"`，靠 `name` 区分语义。**
`elseBranch` 的 `expression` 必须是 `null`——给它赋表达式是错的。

### ifBranch 权威结构（真机样本 keys 顺序）

```json
{"nodeId":"CONDITION_GKCBbp", "name":"ifBranch", "type":"CONDITION",
 "caption":"符合条件即进入该分支",
 "description":"<表达式中文原文，与 expression.title 相同>",
 "runAfter":null,
 "expression":{
   "title":"不为空(微流程.查询单条数据(1).投标报备申请_1 [投标报备申请].本部实体)&& ...",
   "schema":"{\"designData\":{\"expressionTranslation\":\"...\",\"resultTypeInfo\":\"BOOLEAN\",
             \"resultTypeFullName\":null,\"terminalType\":\"BACKEND\",\"isMultiSelect\":false,
             \"context\":[...]},\"runtimeData\":{...}}"   // ← schema 是 JSON 字符串！
 },
 "isCompleted":true,
 "nodes":[]}
```

关键契约：
- **`expression.schema` 是字符串**（内嵌 JSON），不是对象。`designData` / `runtimeData` 两层。
- **`resultTypeInfo` 必须是 `"BOOLEAN"`**，`resultTypeFullName` 为 `null`。
- **`descripption` 与 `expression.title` 都是表达式的中文 `expressionTranslation`**，
  不是业务描述文案。真机 952 个 ifBranch 全部如此。
- **`isCompleted:true` 才会被保存校验放行**；`nodes:[]` 是该分支下的子节点链。
- `expression.title` 为空串 + `schema:null` = 未配置，保存报「请配置分支条件」。

### elseBranch 权威结构

```json
{"nodeId":"CONDITION_MObryz", "name":"elseBranch", "type":"CONDITION",
 "caption":"不符合条件即进入该分支", "description":"", "runAfter":null,
 "expression":null}
```

只有 6 个键，**没有 `isCompleted`，没有 `expression` 对象**。

### 生成器契约

- 新建分支模板固定两个 CONDITION：`ifBranch`（expression 空壳）+ `elseBranch`（null）
- 要三分支就得自己插 `elseIfBranch`
- 条件表达式必须走 `/expression/transform` 生成 `schema`（含 BOOLEAN 的 resultTypeInfo），
  **不能手拼** `designData`
- `description` 要同步写 `expressionTranslation`，否则画布上分支标签是空的

---

## 2. PUBLISH_BUSINESS_EVENT（事件投递）— 两种 eventType

### 结论：已在生产大量使用（24 节点 / 9 条流程），两种模式字段集完全不同

### 模式 A：`eventType:"IN_APP"`（应用内事件）

```json
{"nodeId":"PUBLISH_BUSINESS_EVENT_ik7C3V", "caption":"事件投递(1)",
 "actionType":"PUBLISH_BUSINESS_EVENT",
 "eventType":"IN_APP",
 "selectEvent":{...事件定义...},          // ← 注意是 selectEvent 不是 selectMq
 "mappingType":"attrs",
 "attrs":[{...}]}
```

字段集：`eventType` + **`selectEvent`** + `mappingType` + `attrs`。
**没有 `app`、没有 `messageType`、没有 `executeTime`。**

### 模式 B：`eventType:"AMONG_APP"`（应用间消息/MQ）

```json
{"nodeId":"PUBLISH_BUSINESS_EVENT_ksZT7c", "caption":"事件投递(3)",
 "actionType":"PUBLISH_BUSINESS_EVENT",
 "eventType":"AMONG_APP",
 "selectMq":{"key":"UDC_ZNXMGLPT3289082814923688017_MQ.com.seeyon.<app>.dto.microflow.message.<Name>",
             "label":"延迟判断事项状态发送邮件", "value":"UDC_ZNXMGLPT3289082814923688017_MQ..."},
 "app":{"appId":"3289082814923688017","appName":"znxmglpt...","caption":"智能项目管理平台",
        "inApp":true,"udcApp":true,"dynamicDependency":false},
 "messageType":"...",                     // 可选（有的节点有，有的没有）
 "executeTime":"...",                     // 仅延时消息才有
 "mappingType":"attrs",
 "attrs":[{...}]}
```

字段集：`eventType` + **`selectMq`** + `app` + `mappingType` + `attrs`
（+ 可选 `messageType` / `executeTime`）。

**陷阱**：`selectEvent`（IN_APP）和 `selectMq`（AMONG_APP）是两个不同字段，
用错字段 checkSchema 通过但事件选不上。

### attrs 字段映射的真实三种 value 形态

真机 24 个节点的 attrs 里出现过：

| 形态 | 真实样本 | 用途 |
|---|---|---|
| DTO 对象引用 | `{dataType:"DTO", outputName:"_CREATE_VARIABLE_diIGcF", dtoType:"CUSTOM", position:"parent", path:"comseeyon..."}` | 整个自定义对象映射到消息 DTO |
| 字段级引用 | `{key:"_RETRIEVE_PjOUCi_com.seeyon.<app>.dto.TbbbsqDto.id", name:"id", id:"...TbbbsqDto.id", appName:"...", position:"children"}` | 实体字段 → 消息字段（**field 级**） |
| 列表引用 | `{id:"com.seeyon.ctp.affair.dto.table.AffairDto.id", javaType:"java.lang.Long", type:"ARRAY", dataType:"BIGINTEGER", dtoType:"MASTER_ENTITY"}` | 列表型入参 |

字段级引用的 `key` = `<节点出参名>_<DTO全名>.<字段名>`。
DTO 级引用用 `outputName` + `path`（去点全名）。

### 延时事件

`executeTime` 字段存在即延时消息。前端说明原文：
「对于普通事件，直接发布；对于延时事件，根据配置的时间发布。
在其他模块或者微流程中可订阅此事件，收到事件后能获得事件中携带的参数数据。
注意：延时事件无法保证能够按顺序执行！」

---

## 3. CONNECTOR（连接器）— 643 条生产流程中 0 次使用

### 结论：它是真实存在的第 26 类节点，但本项目全量生产未使用

`nodeTypeList` 第 22 项确认存在：

```
22   连接器    ACTIVITY    CONNECTOR    TRANSFER
```

但在 643 条 RELEASE 微流程里 **`actionType:"CONNECTOR"` 出现 0 次**。

### 已确认的事实（前端 bundle）

- 它和「事件投递」**共用同一个配置组件** `type:"BusinessEvent"`
- 依赖应用 `cip-connector`（中文名「连接器」，`udcApp:false`，是平台内置应用）
- `messageSource:"CONNECTOR"` 属于**外部消息源**（`EXTERNAL`），
  与 `EVENT`/`MICRO_FLOW_EVENT`（`INTERNAL`）对立
- 依赖缺失时提示：**「连接器依赖已移除，请在应用管理添加依赖后使用」**
- 代码里 `["CONNECTOR"]` 是一个特殊依赖检查列表

### 仍未验证的

- 它的独立 `selectConnector` 字段形态（因 0 样本，无法从数据反推）
- 必填集（`SAVE_REQUIRED_FIELDS` 里没有 CONNECTOR 条目）
- 是否真的等同「事件投递 + messageSource=CONNECTOR」还是独立表单

**判定**：`CONNECTOR` 需要现场开抽屉验证，无生产样本可参考。
如果业务用不到连接器，可以暂不补；用到时必须先补测。

---

## 4. 附：26 类节点真实使用频次（643 条 RELEASE 流程）

按「覆盖流程数」降序，这决定生成器的优先级：

| 节点 | 出现次数 | 覆盖流程数 | 优先级 |
|---|---|---|---|
| RETRIEVE 查询单条数据 | 639 | 357 | 极高 |
| CONDITION（分支条件） | 1981 | 326 | 极高 |
| BRANCH 分支 | 941 | 326 | 极高 |
| CREATE_VARIABLE 创建变量 | 712 | 302 | 极高 |
| CHANGE_VARIABLE 修改变量 | 1053 | 292 | 极高 |
| FOR_EACH 列表循环 | 384 | 199 | 高 |
| LIST_OPERATION 列表操作 | 654 | 176 | 高 |
| SUB_MICROFLOW 子微流程 | 251 | 156 | 高 |
| CREATE_LIST 创建列表 | 239 | 138 | 高 |
| CHANGE_LIST 修改列表 | 317 | 135 | 高 |
| RETRIEVE_ARRAY 查询多条 | 217 | 126 | 高 |
| CHANGE_ENTITY 更新数据 | 103 | 78 | 中 |
| CALL_APP_SERVICE 自定义服务 | 105 | 65 | 中 |
| CONVERT_DATA 类型转换 | 114 | 58 | 中 |
| CHANGE_BATCH_ENTITY 批量更新 | 41 | 37 | 中 |
| FOR 计数循环 | 32 | 31 | 中 |
| CREATE_ENTITY 插入数据 | 32 | 24 | 中 |
| DATA_MAPPING 数据转换 | 17 | 10 | 低 |
| PUBLISH_BUSINESS_EVENT 事件投递 | 24 | 9 | 低 |
| MAP_OPERATION 映射操作 | 24 | 8 | 低 |
| CUSTOM_ERROR 自定义错误 | 25 | 15 | 低 |
| BREAK 跳出循环 | 8 | 8 | 低 |
| DELETE_ENTITY 删除数据 | 13 | 13 | 低 |
| CREATE_MAP 创建映射组 | 4 | 4 | 低 |
| CREATE_BATCH_ENTITY 批量插入 | 6 | 6 | 低 |
| CALL_DATA_FLOW 执行生单规则 | 1 | 1 | 低 |
| CONNECTOR 连接器 | **0** | **0** | **未验证** |

### endNode 形态 100% 一致

643 条流程**全部**是 `type:"END"` + `actionType:"END_NODE"`，
0 条缺失、0 条形态异常——印证 G11 闸门的判据正确。

---

## 5. 补充：CONNECTOR 为什么 0 样本（已查证）

不只是「本项目没用」，而是有结构原因：

`udcMicroflowSearchAppServiceByAppNamePost` 查 `cip-connector` 应用的可用服务，
返回 **`content: []`**（空）。也就是说：

- `cip-connector`（连接器，`udcApp:false`，平台内置）在本环境**没有任何已注册服务方法**
- 连接器节点必须先到「集成平台」（`cip-manager`）里配置连接器和消息，
  应用侧才有东西可选
- 没有前置配置时，节点即使能拖出来，抽屉里的下拉也是空的

**结论**：CONNECTOR 不是纯代码可构造的节点，它依赖集成平台的运行时配置。
本环境未配置 → 0 生产样本 → 无法从数据反推字段契约。

要用连接器时的正确顺序：
1. 先在「集成平台 / cip-manager」配置连接器与消息
2. 再在微流程里加 CONNECTOR 节点，从下拉里选
3. 抓一次真实抽屉，补 `SAVE_REQUIRED_FIELDS["CONNECTOR"]` 与 `selectConnector` 字段形态

在此之前，生成器**不应该**尝试构造 CONNECTOR 节点——生成的必然是空引用。
G14 闸门就是为此设的：出现 CONNECTOR 且无 app 时直接拦。

---

## 6. 附：一条流程里 CONDITION 的真实嵌套深度

实测「合同档案状态发生值变化时更新合同审批状态」这条流程，
`nodes[3]` 是 `FOR_EACH`，其内部递归有 **59 个节点**，
再里面套 3 层 BRANCH，最深路径形如：

```
root.nodes[3].nodes[1].conditions[0].nodes[5].conditions[0].nodes[1].conditions[0].nodes[2]
```

**闸门的递归遍历必须能下到这种深度，且每一层的 CONDITION 都要 yield。**
只遍历顶层 `nodes` 或只 yield `conditions[].nodes` 会整层看丢——
这类漏洞不会报错，只会静默返回「0 问题」。
