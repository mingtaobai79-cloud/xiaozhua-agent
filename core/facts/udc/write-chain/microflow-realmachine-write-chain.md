# 微流程真机写链 + 检查日志取证

> 来源：CDP 真机设计器 + DB 聚合（500 条）+ CFR 契约 + REST 实测
> 状态：**微流程创建 LIVE PASS（含 RETRIEVE 节点）+ checkSchema 通过 + 操作日志可拉**

## 1. 前端数据层真相（bundle 取证）

前端**不直接拼 GraphQL**，走封装：
```js
udcQueryLoader.load({ fieldType:"udcMicroflowFindByIdGet", paramsType:"udcMicroflowFindByIdGetInputPath",
                      paramsKey:"path", queryFields:"...", params })
udcMutationLoader.load({ fieldType:"udcMicroflowUpdatePost", paramsType:"udcMicroflowUpdatePostInputBody",
                         paramsKey:"body", queryFields:"content", params, showLoading })
```
→ 实际发 `POST /service/udc/graphql?<fieldType>`，body = `{query, variables:{body|path: params}}`。

## 2. ★ 微流程 op 面（61 个，frontend_ops.json）

| 用途 | op | 入参类型 |
|---|---|---|
| **创建** | `udcMicroflowCreatePost` | `MicroFlowDefinitionDto` → `content=id` |
| **更新（强制草稿态）** | `udcMicroflowUpdatePost` | `MicroFlowDefinitionDto` |
| **校验 schema** | `udcMicroflowCheckSchemaUpdatePost` | `MicroFlowDefinitionDto` → `{check,errors,errorMessage[]}` |
| 仅校验不更新 | `udcMicroflowCheckSchemaPost` | 同上 |
| 读 | `udcMicroflowFindByIdGet` | `{id}` → 含 dataSchema |
| 搜索 | `udcMicroflowSearch` | 分页 |
| 分组 | `udcMicroFlowGroupSelectByTypePost` / `CreatePost` / `UpdatePost` / `BatchMovePost` |
| 删除 | `udcMicroflowDelete` | |
| 节点 | `udcMicroflowFindNodesGet` / `FindNodeSchemaPost` / `DisableNodePost` |
| DTO | `udcMicroflowFindDtoByEntityPost` / `FindCustomDtoPost` / `TreeEntityDtoPost` |
| 检查相关 | `udcMicroflowCheckDtoMetadataExistPost` / `CheckMicroFlowCaptionPost` |
| 调用关系 | `udcMicroflowFindCallInfoUpstreamPost` / `DownstreamPost` |

## 3. `MicroFlowDefinitionDto` 契约（CFR udc-biz）

```jsonc
{
  name*,          // @NotNull @Size(1,45)  编码
  caption*,       // @NotNull @Size(1,100) 显示名
  appId, versionCode:int, creationMethod, type, triggerType, groupType,
  description,    // @Size(max=200)
  scheduleCaption, businessEventCaption, orderNum, state, sourceId,
  jsonSchema,     // 图形（nodes/lines）JSON 字符串
  microFlowGroupId,
  dataSchema,     // ★ 业务数据 JSON 字符串（trigger/endNode/nodes/input/output）
  serviceInterface = "CustomMicroFlowAppService"
}
CheckSchemaDto { boolean check; int errors; List<ParseCheckResultDto> errorMessage }
ParseCheckResultDto { errorCode, errorType, level, message, nodeCaption, nodeId, path, propertyKey }
```

## 4. 枚举真值（CFR udc-common）

| 枚举 | 值 |
|---|---|
| `MicroFlowTypeEnum` | `SERVICE(0)` / `FRONTEND(1)` / `ENTITY_RULE(2)` / `CUSTOM(3)` / `FUNCTION(4)` |
| `MicroFlowTriggerTypeEnum` | `BUSINESS_EVENT(0)` / `SCHEDULE(1)` / `MANUAL(2)` / `FRONTEND_PARAM(3)` |
| `GroupTypeEnum` | `DEFAULT(0)` / `VALIDATE(1)` / `ASSIGN_VALUE(2)` / `DEFAULT_VALUE(3)` |
| `MicroFlowDataStateEnum` | `DRAFT(10)` / `RELEASE(20)` |
| `CreationMethodEnum` | `MANUAL(0)` / `FROM_TEMPLATE(1)` / `PAGE_LAYOUT(2)` |

★ 注意：`trigger.type`（dataSchema 内）用 `MANUAL/BUSINESS_EVENT/SCHEDULE` 字符串；DB 列 `trigger_type` 用数字（MANUAL=2）。

## 5. ★ 真机 LIVE 验证

```jsonc
// (1) 创建（含一个 RETRIEVE 节点）
POST /service/udc/graphql?udcMicroflowCreatePost
body = MicroFlowDefinitionDto{ name:"xzhRealTest01", caption:"小爪真机测试微流程", appId, type:"CUSTOM",
        triggerType:"MANUAL", groupType:"DEFAULT", creationMethod:"MANUAL", state:"DRAFT",
        dataSchema:"{input,output,trigger{nodeId:MFStartNode,type:MANUAL},endNode{MFEndNode,END_NODE},
                     nodes:[{nodeId:RETRIEVE_xzh01,actionType:RETRIEVE,caption:查询单条数据(1),
                             fetchType:IDS,app:{...},structure:{entity,dtoType:MASTER_ENTITY,relationEntity},
                             output:{dataType:DTO,javaType:<dto>,dtoType:MASTER_ENTITY,relationEntity}}]}" }
→ {"code":"BOOT_0000","data":{"content":"2849884343658019231"}}

// (2) checkSchema（真机校验）
POST /service/udc/graphql?udcMicroflowCheckSchemaUpdatePost
→ {"check":true,"errors":0,"errorMessage":null}      ← ✅ 通过

// (3) 全应用一致性检测
→ 4 WARN / 0 ERROR；新增 WARN = UDC_CE_MICRO_FLOW_04003「小爪真机测试微流程:未保存的微流程或者页面规则」
  （因为 create 后未走「保存并提交」→ state=10 草稿）
```

**结论**：契约建的微流程节点（RETRIEVE）**真机 schema 校验通过**，检测仅报"未保存"WARN（正常草稿态），无 ERROR。

## 6. 检查日志（操作日志）拉取

```
POST /service/udc/graphql?udcOperationLogSearch
body = { pageInfo:{needTotal:true,pageNumber:1,pageSize:20}, params:{ appId: <Long，不是数组！> } }
→ content[]: { appId, operatorId, operatorCaption, module, subModule, moduleCaption, subModuleCaption,
               logElement:"[\"微流程\\\\微流程分组\\\\微流程[小爪真机测试微流程]\"]",
               elementsSize, recordVersion, logPath:"ruleId=2849884343658019231",
               actionType:"CREATE", createTime }
```
★ `params.appId` 必须是 **Long**，传数组报 `BOOT_3002 Failed to deserialize ... to type Long`。
`logPath` 形如 `ruleId=<id>`，可直接定位到具体模块对象。

## 7. 检查/日志的分工（真机口径）

| 层 | 入口 | 返回 |
|---|---|---|
| 微流程 schema 校验 | `udcMicroflowCheckSchemaUpdatePost` | `{check,errors,errorMessage[]{errorCode,nodeId,path,message}}` |
| 全应用一致性检测 | `do/detection` → 轮询 → `udcApplicationSearchDetectionPost` | `content[]{detectionType,code,path,elementProperty,...}` |
| 检查日志（谁改了什么） | `udcOperationLogSearch` | `content[]{module,subModule,logElement,logPath,actionType}` |
| 运行日志（微流程运行） | `udc_rt_data_flow_log` / 微流程运行日志面板 | 运行期 |
| 服务端异常 | pod `/var/log/webapps/udc/udc-error.log` | 堆栈 |

## 8. 边界（未做）

- 未走真机 UI 点「保存并提交」（前端闭包门拦截）；改走 `udcMicroflowUpdatePost` + 检测。
- 其余 47 种节点类型未逐个真机建（本次只验 RETRIEVE；结构已在 `microflow-node-catalog.md`）。
- `jsonSchema`（图形 lines/nodes）未构造（只给空 `{nodes:[],lines:[]}`，schema 校验仍通过）。
- 微流程**运行期**未触发（只验设计态 + 校验 + 检测 + 日志）。

## 9. 复现

```bash
node cdp_login.js "<微流程编辑器 URL>"      # 真机打开
python mf_real_build.py                     # create（含 RETRIEVE 节点）
python mf_check2.py                         # checkSchema + 检测
python oplog.py                             # 操作日志
```
