# 微流程 vs 页面规则 —— 节点域分离（权威纠正）

> **用户纠正**：① 我把微流程和页面规则的节点混用了；② 建了一堆"单节点"流程，应该**一条流程里融合所有节点**。
> 状态：**边界已用 500 条微流程数据实证；一条融合 18 种标准节点的流程已建成**

## 1. ★★ 两个域，节点几乎不相交（数据实证）

聚合全库 500 条微流程的 `data_schema.nodes[].actionType`，按 `type` 列分组：

### 标准微流程（`type=0 SERVICE`）—— **后端流转，独立于应用**
```
独有 17 种（+BRANCH 共 18）：
  RETRIEVE            查询单条数据
  RETRIEVE_ARRAY      查询多条数据
  CREATE_VARIABLE     创建变量
  CHANGE_VARIABLE     修改变量
  CREATE_LIST         创建列表
  CHANGE_LIST         修改列表
  LIST_OPERATION      列表操作
  MAP_OPERATION       映射操作
  DATA_MAPPING        数据转换/映射
  CHANGE_ENTITY       更新数据
  CHANGE_BATCH_ENTITY 批量更新数据
  CREATE_ENTITY       插入数据
  DELETE_ENTITY       删除数据
  CONVERT_DATA        类型转换
  SUB_MICROFLOW       子微流程
  CALL_APP_SERVICE    自定义服务
  PUBLISH_BUSINESS_EVENT 事件投递
  BRANCH              分支（两域共用）
```

### 页面规则 / 前端微流程（`type=1 FRONTEND`）—— **依赖应用（页面/控件）**
```
独有 26 种（+BRANCH 共 27）：
  CALL_MICRO_FLOW     调用微流程（跨域桥）
  CALL_FRONT_FLOW     调用前端流程
  CALL_DATA_FLOW_FRONT 执行生单规则
  VALUE_HANDLE        值操作
  CREATE_VARIABLE_FRONT / CHANGE_VARIABLE_FRONT   创建/修改变量(前端)
  CREATE_LIST_FRONT / CHANGE_LIST_FRONT / FED_LIST_OPERATION  列表(前端)
  CONTROL_ACTION / CONTROL_STATUS   控件动作/状态
  ENTITY_SAVE / ENTITY_SAVE_DRAFT / ENTITY_REFRESH   保存/暂存/刷新（页面表单）
  MESSAGE_INFO        提示消息
  MODAL               弹窗
  CONFIRM_CLOSE_PAGE  确认关闭页面
  OPEN_PAGE / OPEN_LINK / RELOAD_PAGE   页面跳转
  THROW_EVENT         抛出页面事件
  ATTACHMENT_UPLOAD / ATTACHMENT_DOWNLOAD   附件
  ENTITY_IMPORT / ENTITY_EXPORT   导入/导出
  FLOW_ACTION         流程动作
  CONVERT_DATA_FRONT  类型转换(前端)
  BRANCH
```

### ★ 唯一共用节点：`BRANCH`（分支）

**判定口诀**：
- 名字带 `_FRONT` / `FED_` → 前端
- 操作**页面控件**（MODAL/OPEN_PAGE/CONTROL_ACTION/THROW_EVENT/附件/提示）→ 前端
- 操作**实体数据**（RETRIEVE/CHANGE_ENTITY/ENTITY_SAVE 等）→ 看 `type`：
  - `type=0` 用 `CREATE_ENTITY`/`CHANGE_ENTITY`/`DELETE_ENTITY`/`RETRIEVE`（后端实体操作）
  - `type=1` 用 `ENTITY_SAVE`/`ENTITY_SAVE_DRAFT`/`ENTITY_REFRESH`（页面表单操作）
- 跨域调用：前端用 `CALL_MICRO_FLOW` 调后端微流程；后端用 `SUB_MICROFLOW` 调子微流程。

## 2. 我的错误（已纠正）

| 错误 | 纠正 |
|---|---|
| 把 `ENTITY_SAVE`/`MESSAGE_INFO`/`CONVERT_DATA(前端用法)` 建进标准微流程 | 这些是**前端专属**；标准微流程用 `CREATE_ENTITY`/`CHANGE_ENTITY`/`DELETE_ENTITY` |
| 建了 12+ 条**单节点**流程 | 应**一条流程融合所有节点**（runAfter 串联） |
| `type` 用 CUSTOM(3) | 标准是 `SERVICE(0)` |

## 3. ★ 一条融合 18 种标准节点的流程（LIVE PASS）

```
caption: 小爪标准微流程-全节点流转
id:      -3924426994436768028
type:    SERVICE (0)
state:   DRAFT
checkSchema: {check:true, errors:0}
output:  有（_FLOW_OUTPUT_s1, DTO/ARRAY/MASTER_ENTITY）
```

节点链（`runAfter` 串联）：

| # | 节点 | actionType | runAfter |
|---|---|---|---|
| 1 | 创建变量 | `CREATE_VARIABLE` | — |
| 2 | 查询单条数据 | `RETRIEVE` | CREATE_VARIABLE_s1 |
| 3 | 查询多条数据 | `RETRIEVE_ARRAY` | RETRIEVE_s2 |
| 4 | 创建列表 | `CREATE_LIST` | RETRIEVE_ARRAY_s3 |
| 5 | 修改列表 | `CHANGE_LIST` | CREATE_LIST_s4 |
| 6 | 列表操作 | `LIST_OPERATION` | CHANGE_LIST_s5 |
| 7 | 映射操作 | `MAP_OPERATION` | LIST_OPERATION_s6 |
| 8 | 数据转换 | `DATA_MAPPING` | MAP_OPERATION_s7 |
| 9 | 修改变量 | `CHANGE_VARIABLE` | DATA_MAPPING_s8 |
| 10 | 更新数据 | `CHANGE_ENTITY` | CHANGE_VARIABLE_s9 |
| 11 | 批量更新数据 | `CHANGE_BATCH_ENTITY` | CHANGE_ENTITY_s10 |
| 12 | 插入数据 | `CREATE_ENTITY` | CHANGE_BATCH_ENTITY_s11 |
| 13 | 删除数据 | `DELETE_ENTITY` | CREATE_ENTITY_s12 |
| 14 | 类型转换 | `CONVERT_DATA` | DELETE_ENTITY_s13 |
| 15 | 子微流程 | `SUB_MICROFLOW` | CONVERT_DATA_s14 |
| 16 | 自定义服务 | `CALL_APP_SERVICE` | SUB_MICROFLOW_s15 |
| 17 | 事件投递 | `PUBLISH_BUSINESS_EVENT` | CALL_APP_SERVICE_s16 |
| 18 | 分支 | `BRANCH` | PUBLISH_BUSINESS_EVENT_s17 |

回读确认：`type=SERVICE`、18 节点、`runAfter` 链路完整、`output` 与 `endNode.output` 齐全。

## 4. 标准节点结构要点（真机/DB 实证）

```jsonc
// CREATE_ENTITY（插入数据，后端）—— 注意不是 ENTITY_SAVE
{ "app":{appId,appName,caption,inApp,udcApp,dynamicDependency}, "structure":<entity>,
  "attrs":[], "mappingType":"attrs", "title":"插入结果",
  "output":{"name":"_CREATE_ENTITY_xxx","dataType":"BIGINTEGER","type":"OBJECT",
            "desc":"插入后的ID","javaType":"java.lang.Long"} }

// CHANGE_LIST（修改列表）
{ "selectParam":<列表>, "action":"ADD", "dataSource":[] }

// CHANGE_BATCH_ENTITY（批量更新）
{ "selectParam":<列表ARRAY>, "title":"批量更新结果",
  "output":{"name":"_CHANGE_BATCH_ENTITY_xxx","dataType":"INTEGER","type":"OBJECT","javaType":"java.lang.Integer"} }

// MAP_OPERATION（映射操作）
{ "paramType":"BASIC","title":"...","basic":{"key":"STRING","dataType":"STRING"},
  "selectMap":{...MAP 类型上游...}, "operationType":"GET","theKey":"key1","nullHandling":false,
  "output":{"javaType":"java.lang.String","dataType":"STRING","type":"ARRAY|OBJECT","desc","generics":{...}} }

// CALL_APP_SERVICE（自定义服务，Dubbo）
{ "app":{appId:"bpm",appName:"bpm",inApp:false,udcApp:false},
  "selectMethod":{"caption","description","dubbo":true,"dubboVersion":"1.0",
                  "fullName":"<implClass>.<method>","implClass","interfaceClass"},
  "attrs":[], "mappingType":"attrs", "outputName":"服务结果", "pageInfo":null }

// DATA_MAPPING（数据转换）
{ "targetType":"ENTITY","app":<app>,"structure":<entity>,"selectParam":<源>,"mappingRule":{} }

// CHANGE_VARIABLE（修改变量）
{ "selectParam":<变量>,"attrs":[],"mappingType":"attrs","value":{"type":"Simple","simple":...} }
```

## 5. 边界（未做）

- 前端/页面规则域（type=1）的 26 种节点**未在标准微流程里建**（它们不属于这里）；待做页面规则时单独验证。
- `MAP_OPERATION` / `CALL_APP_SERVICE` 的完整参数（selectMap 明细、方法签名）用了最小可用值，未逐个跑通业务语义。
- 未走应用构建验证 04003 消除；微流程运行期未触发。

## 6. 复现

```bash
python split2.py           # 两域节点差集（权威边界）
python std_only.py         # 标准微流程独有节点真实结构
python std_all_nodes.py    # 一条融合 18 节点流程 create + checkSchema
python std_all_verify.py   # 回读 + 检测
```
