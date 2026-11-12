# 微流程节点真机批量验证（10 类节点 LIVE + 检查/日志闭环）

> 来源：REST 真机建 + `udcMicroflowCheckSchemaUpdatePost` + 全应用检测 + 操作日志
> 状态：**10 类节点全部 LIVE PASS（checkSchema errors=0）+ 检查/日志闭环打通**

## 1. ★ 10 类节点真机建成（全部 checkSchema 通过）

| 节点 | actionType | id | checkSchema |
|---|---|---|---|
| 创建变量 | `CREATE_VARIABLE` | 2922209767551739721 | ✅ errors=0 |
| 提示消息 | `MESSAGE_INFO` | -117785897305033814 | ✅ |
| 保存记录 | `ENTITY_SAVE` | 7596338839015438121 | ✅ |
| 刷新实体 | `ENTITY_REFRESH` | 1380916200480320703 | ✅ |
| 查询多条 | `RETRIEVE_ARRAY` | 696411808324818098 | ✅ |
| 数据转换 | `CONVERT_DATA` | 4316804186876158290 | ✅ |
| 分支 | `BRANCH` | -3498336883307438798 | ✅ |
| 列表操作 | `LIST_OPERATION` | -2174712061631668166 | ✅ |
| 更新数据 | `CHANGE_ENTITY` | -6792455637689643255 | ✅ |
| 值操作 | `VALUE_HANDLE` | -2274503986616732857 | ✅ |

回读验证：`udcMicroflowFindByIdGet`（**query，不是 mutation**）→ `dataSchema` 往返一致，节点完整。

## 2. 各节点必填字段（真机实证）

```jsonc
// CREATE_VARIABLE
{ "paramType":"BASIC", "title":"<出参名>", "dataType":"STRING|BOOLEAN|INTEGER|...",
  "value":{"type":"Simple","simple":<值>,"desc":<值>},
  "output":{"id":"","javaType":"java.lang.String","dataType":"STRING","type":"OBJECT",
            "desc":"<名>","dtoType":"","name":"_CREATE_VARIABLE_xxx"} }

// MESSAGE_INFO
{ "messageType":"SUCCESS", "showInfo":{"type":"Simple","simple":"<文案>","desc":"<文案>"},
  "closeType":["AUTO_CLOSE"] }

// ENTITY_SAVE
{ "config":"{\"target\":\"udcForm_xxx\",\"actionName\":\"ENTITY_SAVE\"}",   // JSON 字符串
  "outputName":"出参_ID",
  "output":{"javaType":"java.lang.Long","dataType":"BIGINTEGER","type":"OBJECT","desc":"出参_ID","name":"_ENTITY_SAVE_xxx"} }

// ENTITY_REFRESH
{ "config":"{\"target\":\"udcForm_xxx\",\"actionName\":\"ENTITY_REFRESH\"}", "output":null }

// RETRIEVE_ARRAY
{ "fetchType":"CONDITION|IDS", "app":{appId,appName,caption,inApp,udcApp,dynamicDependency},
  "structure":{key:<entityFullName>,id:<dtoFullName>,label,dataType:"DTO",entity:<fullName>,
               dtoType:"MASTER_ENTITY",udcApp:true,fullName:<dto>,relationEntity:<entityId>},
  "condition":[], "sortParams":[], "pageSearch":false,
  "output":{id:<dto>,dataType:"DTO",type:"ARRAY",desc,dtoType:"MASTER_ENTITY",udcApp:true,
            javaType:<dto>,appName,name:"_RETRIEVE_ARRAY_xxx"} }

// CONVERT_DATA
{ "convertType":{"desc":"指定符号拆分文本","value":"Split","dataType":"STRING","type":"ARRAY"},
  "selectParam":{description,key,name,id,appName,position,path,outputName,dataType,type,
                 javaType,dtoType,udcApp,multiSelect},
  "regex":"PERIOD", "title":"<输出名>",
  "output":{"name":"_CONVERT_DATA_xxx","dataType":"STRING","type":"ARRAY","desc","javaType":"java.lang.String"} }

// BRANCH（type=BRANCH，无 actionType）
{ "nodeId":"BRANCH_xxx","name":"userBranch","type":"BRANCH","caption":"分支(1)",
  "conditions":[{ "nodeId":"CONDITION_xxx","name":"ifBranch","type":"CONDITION",
     "caption":"符合条件即进入该分支","description":"<表达式翻译>",
     "expression":{"title":"<翻译>","schema":"{\"designData\":{expressionTranslation,
        resultTypeInfo:\"BOOLEAN\",terminalType:\"BACKEND\",context:[],tokens:[...]}}"}}] }

// LIST_OPERATION
{ "operationType":"DEDUPLICATE|...", "selectParam":{...源列表...}, "countAttrs":[],
  "output":{id,javaType,type:"ARRAY",dataType:"DTO",appName,desc,dtoType,name} }

// CHANGE_ENTITY
{ "selectParam":{...源实体对象...}, "attrs":[], "title":"<输出名>",
  "output":{"id":null,"name":"_CHANGE_ENTITY_xxx","dataType":"INTEGER","type":"OBJECT",
            "desc":"更新成功数量","javaType":"java.lang.Integer"} }

// VALUE_HANDLE
{ "items":[ {"element":[{"id":<控件id>,"label":...,"dataType":...,"relationEntity":...}],
             "value":{"type":"SelectParam","selectParam":{...}}} ] }
```

## 3. ★★ checkSchema 是**浅校验**（重要边界）

**实测**：故意建一个 `RETRIEVE` 节点、`structure=null`、`app=null`、`isCompleted=false`：

```jsonc
POST udcMicroflowCreatePost → 成功（id=3560153447602651824）
POST udcMicroflowCheckSchemaUpdatePost → {"check":true,"errors":0,"errorMessage":null}   ← 竟然通过！
```

⇒ **`checkSchema` 只做结构级（字段名/类型）校验，不校验业务完整性**（节点是否配了实体、是否连线）。
真正的业务校验在**应用构建/发布**阶段（`doParallel` 一致性检测），缺配节点会在构建时报 ERROR。
**别把 checkSchema 的 errors=0 当作"节点配好了"。**

## 4. ★★ 微流程发布 ≠ 应用元数据更新（04003 机制）

实测：把 `小爪节点-创建变量` 用 `udcMicroflowUpdatePost` 置 `state=RELEASE`：

```
DB: state 10(DRAFT) → 20(RELEASE)   ✅ 微流程自身已发布
检测: UDC_CE_MICRO_FLOW_04003「小爪节点-创建变量:未保存的微流程或者页面规则」仍在
```

⇒ **04003 的判定不是看微流程 state，而是看应用元数据快照里有没有该微流程**。
微流程单独发布后，**必须再走一次应用构建/发布**（`udcRuntimeDeployNormalPost`），元数据快照更新后 04003 才消失。
这解释了为何草稿微流程长期挂着 04003：它们是新建但**从未随应用构建过**。

## 5. 检查 / 日志三层闭环（真机口径）

| 层 | op | 返回 | 用途 |
|---|---|---|---|
| 结构校验 | `udcMicroflowCheckSchemaUpdatePost` | `{check,errors,errorMessage[]}` | 字段级（浅） |
| 业务校验 | `do/detection` → `udcApplicationSearchDetectionPost` | `{detectionType,code,path,elementProperty}` | 构建前阻断 |
| 变更日志 | `udcOperationLogSearch` | `{module,subModule,logElement,logPath,actionType}` | 谁改了什么 |

**操作日志实测**（本轮 10 条 CREATE 全部留痕）：
```
CREATE | ["微流程\\微流程分组\\微流程[小爪节点-创建变量]"] | ruleId=2922209767551739721
CREATE | ["微流程\\微流程分组\\微流程[小爪节点-数据转换]"] | ruleId=4316804186876158290
...
```
`logPath=ruleId=<id>` → 直接定位到对象；`logElement` 是层级路径。

## 6. 检测面现状

本轮后：**14 WARN / 0 ERROR**（10 条新增 04003，全部为草稿态新微流程；不阻塞）。

## 7. 边界（未做）

- 48 种节点只真机验了 10 类高频；其余 38 类结构已在 `microflow-node-catalog.md`，未逐个真机建。
- 未走"应用构建"验证 04003 消除（构建为发布级操作，未在本轮执行）。
- 微流程**运行期**（真触发节点执行）未验；本轮只到设计态 + 校验 + 检测 + 日志。
- `jsonSchema`（图形 lines/nodes）未构造。

## 8. 复现

```bash
python node_batch.py      # 10 类节点 create + checkSchema
python node_verify.py     # 回读 + 检测 + 操作日志
python node_errchain.py   # 浅校验反证（缺 structure 仍通过）
python node_publish.py    # state→RELEASE + 04003 仍在（发布≠元数据更新）
```
