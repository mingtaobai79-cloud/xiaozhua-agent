# 自定义服务节点：可选应用与可调接口的完整来源

> 状态：LIVE（2026-10-24，四路接口实测 + 反编译定位）
> 节点：`CALL_APP_SERVICE`（画布显示「自定义服务」）

## 铁律

- 自定义服务节点的可选范围 = **当前应用 + 依赖应用**，不是全平台；`searchApps` 返回里 `inApp:true` 才是本应用
- 可调对象分三类：**AppService（Java 服务实现）**、**REST 接口（含微流程自身暴露的 Controller）**、**连接器**，三套候选集接口不同
- 所有候选集接口**必须带 `appId`**，漏了就 `BOOT_1001 当前应用Id 不能为null`（不是「没权限」，别误判）
- 微流程本身会暴露成 REST Controller（`MFSERVICE*Controller`），因此微流程可以被另一个微流程当自定义服务调用
- 扩展接口不是「配置出来的」，是**依赖加进来之后自动出现在候选集里**的，加依赖走 `udcApplicationDependentApplicationCreateBatchPost`

## 1. 节点权威定义（前端 bundle 逐字）

```js
{
  group:"base", name:"自定义服务", type:"CALL_APP_SERVICE",
  settings: [
    {key:"app", label:"选择应用", type:"applicationSelector", required:true,
     description:"可以选择当前应用或者依赖应用",
     needBootStarter:true, needConnectorApp:true,
     setEmptyBeforeChanged:["structure","selectMethod","value","attrs","mappingType"],
     defaultval: <当前应用>},
    {key:"selectMethod", label:"选择服务", type:"serviceMetadataMethodSelector",
     required:true,
     dependency:{inApp:"$app.inApp", appName:"$app.appName",
                 fullName:"$structure.fullName", entityFullName:"$structure.entityFullName",
                 fetchType:"DTO"},
     fetchType:"DTO",
     setEmptyBeforeChanged:["value","attrs","mappingType"]},
    {key:"condition", label:"过滤条件", type:"whereCondition", mode:"BACKEND", ...},
    {key:"value", label:"参数", type:"valueComponent",
     valueType:["CONSTANT","EXPRESSION","CONTEXT_VARIABLE"], required:true, ...},
    ...
  ]
}
```

节点必填（`requiredTop`，来自 node-catalog）：
`app / selectMethod / value / mappingType / selectParam / pageInfo / outputName`

★ 切换 `app` 会**清空** `structure / selectMethod / value / attrs / mappingType` ——
  所以生成器改应用时必须连带重建下游字段，否则读到脏值。

## 2. 三路候选集接口（LIVE 实测）

| 用途 | GraphQL op | body | 实测返回 |
|---|---|---|---|
| 可选应用 | `udcMicroflowSearchAppsPost` | `{appId}` | 12 条：本应用 `inApp:true` + 11 个依赖/基础应用 |
| AppService 列表 | `udcMicroflowSearchAppServiceByAppNamePost` | `{appId, appName, needDynamicConnector}` | 19 条 `{caption, fullName}` |
| 按 DTO 找服务 | `udcMicroflowSearchAppServicePost` | `{appId, appName, dtoFullName, entityFullName}` | 需给 DTO fullName |
| 方法 | `udcMicroflowSearchMethodByNamePost` | `{appId, appName, dtoFullName, methodFullName}` | 需给方法 fullName |
| REST 接口 | `udcMicroflowSearchRestExcludeBootPost` | `{appId, appName}` | 3 条 `MFSERVICE*Controller` |
| 禁用节点 | `udcMicroflowDisableNodePost` | `{appId, sourceType}` | `content[{actionType}]` |

调用形态（统一 GraphQL mutation）：

```js
POST /service/udc/graphql?<opName>
{"query":"mutation g($p: <Op>InputBody){ data0: <Op>(body:$p){ code data { content } message status } }",
 "variables":{"p": <body>}}
```

★ `appId` 漏传 → `BOOT_1001 当前应用Id 不能为null`。这是**最容易被误读成权限问题**的坑。

## 3. 微流程自身暴露成 REST

`searchRestExcludeBoot` 返回的 3 条全是平台为本应用生成的 Controller：

```
MFSERVICERFlOt9Controller   微流程-1.10删除方案数据
MFSERVICEHbICrpController   微流程-1.9 判断当前启用方案是否存在指向同一张表
GetMigrationsourceController 微流程-1.7 获取数据迁移数据信息
```

前端里对应的暴露形态（bundle 逐字）：

```js
{method:"POST", path:"/microflow/".concat(i.name), triggerType:"MANUAL",
 type:"SERVICE", restType:"POST", hasInput:!!...}
```

⇒ **微流程 = 可被外部 HTTP 调用，也可被别的微流程当自定义服务调用**。
  这解释了为什么「自定义服务」里能选到微流程。

## 4. 依赖 → 扩展接口的链路

```
应用A 加依赖应用B（dependentAppType: SERVICE）
  → searchApps 在 A 的上下文里返回 B（inApp:false）
  → 自定义服务节点选 app=B
  → searchAppServiceByAppName 列出 B 的 AppService
  → selectMethod 选中某个方法的 fullName
```

依赖写接口：

```js
udcApplicationDependentApplicationCreateBatchPost
  [{appId, depAppName, depAppCaption, depAppVersion, depAppBasePackage,
    dependentAppType:"SERVICE"}]

udcApplicationDependentApplicationSelectByConditionPost   // 查已有依赖
udcApplicationDependentApplicationDeleteByIdPost          // 删依赖
udcApplicationDependentApplicationVersionUpdateBatchPost  // 升版本
```

## 5. 微流程域 GraphQL 操作全景（218 个，bundle 提取）

与画布三域 + 生单 + 扣减相关的分组：

```
微流程本体    udcMicroflowCreatePost / UpdatePost / DeletePost / CheckSchemaUpdatePost
              udcMicroflowServiceListPost / ServiceDetailsDynamicPost / ServiceListSubMfPost
              udcMicroflowSearchEntityRulePost（实体规则列表）
              udcMicroflowDisableNodePost / FilterNotVirtualPost / FilterEventPost / FilterMqPost
              udcMicroflowFindCallInfoUpstreamPost / DownstreamPost（调用关系）
候选集        udcMicroflowSearchAppsPost / SearchAppServicePost /
              SearchAppServiceByAppNamePost / SearchMethodByNamePost /
              SearchRestExcludeBootPost / SearchEnumByAppNamePost /
              SearchTreeEntityPost / TreeEntityDtoPost / SearchNonEntityDtoPost
分组          udcMicroFlowGroupCreatePost / UpdatePost / DeletePost / SelectByTypePost /
              BatchMovePost
生单规则      udcDataFlowDeleteContentPost / ListEventEntityPost / ListEventsPost /
              EntityNotExistIdsPost
扣减规则      udcDeductionRulePost / UpdatePost / DeletePost / CountPost / InitDataPost /
              ValidRulePost / udcDeductionMapPost / UpdatePost / DeletePost / DeleteContentPost /
              udcDeductionEntityListPost / EntityNotExistIdsPost
```

## 6. 对生成器的含义

- `CALL_APP_SERVICE` 的 `app` 不能由生成器凭空造，必须先查 `searchApps` 拿到合法 `appName`
- `selectMethod.fullName` 必须来自 `searchAppServiceByAppName` 或 `searchRestExcludeBoot` 的真实返回
- 生成器若改 `app`，必须同时重建 `selectMethod / value / attrs / mappingType`
- `disableNode` 为空 ≠ 所有节点可用，它只反映**当前上下文**的禁用；节点域限制仍以 `rule_domain_scope` 为准

## 7. 方法级 fullName 与连接器（本轮补齐）

### 7.1 方法 fullName 形态（LIVE 确认）

```
服务类 fullName   com.seeyon.<appName>.appservice.XxxAppServiceImpl
方法 fullName     com.seeyon.<appName>.appservice.XxxAppServiceImpl.<方法名>
```

`searchAppServiceByAppName` **不返回 methods**（实测 `methods=0`），列方法必须再调一次：

```
udcMicroflowSearchAppServiceByNamePost
  body: {appId, appName, serviceFullName}
  → data.content = {caption, fullName,
                    methods:[{caption, description, fullName, group, available}]}
```

`udcMicroflowSearchMethodByNamePost` 是**精确查**不是列方法 ——
`methodFullName` 为空直接 `BOOT_1001 方法名称不能为空`。

### 7.2 连接器 = 同一套候选集，不同字段名

前端 `fetchConnectorAppServiceByAppName({appName, fullName})` 内部调用的仍是
`udcMicroflowSearchAppServiceByNamePost`（同一个 op，`serviceFullName` 传 `fullName`）。

| 节点 | 选择应用 | 选择目标 | 选择方法 |
|---|---|---|---|
| 自定义服务 `CALL_APP_SERVICE` | `app` | `selectMethod`（`serviceMetadataMethodSelector`） | 同左 |
| 连接器 `Connector` | `app`（`needConnectorApp`/`needDependency`） | `connector`（`serviceConnectorSelector`） | `connectorMethod`（`serviceConnectorMethodSelector`） |

连接器依赖：`connector` 依赖 `{appName, isIntergrationApp}`；
`connectorMethod` 依赖 `{appName, fullName}`（`fullName` = `connector.fullName`）。

★ 结论：**两条线共用同一个服务候选集接口**，实现时不需要两套取数逻辑，
  只需要按节点类型映射字段名。

### 7.3 GraphQL 查询的两个硬坑（都踩过）

1. **`data` 层不能省**：`{ code data { content } message status }`。
   写成 `{ content }` 会报 `Field 'content' ... is undefined`，看起来像字段名错，其实是缺层。
2. **queryFields 必须从 `fieldType:"<op>"` 之后取**。
   向前找会抓到上一个 op 的字段，结果是 `code=None` 且**不报错**，
   排查成本极高（本次在这一条上绕了三轮）。

## 8. 真实 selectMethod 形态（DB 权威，39 个节点实测）

```json
{
  "fullName": "com.seeyon.<app>.appservice.XxxAppServiceImpl.getSerialNumber",
  "implClass": "com.seeyon.<app>.appservice.XxxAppServiceImpl",
  "parameter": {
    "caption": null,
    "type": "com.seeyon.boot.transport.SingleRequest",
    "item": {"enums": null, "itemType": "com.seeyon.<app>.domain.dto.SerialNumberDto",
             "item": null}
  },
  "returnValue": {
    "caption": "流水号",
    "type": "com.seeyon.boot.transport.SingleResponse",
    "item": {"enums": null, "itemType": "java.lang.String", "item": null}
  }
}
```

★ **`type` 是全限定名**，不是短名 `SingleRequest`。
★ **`item.itemType` 是作用域键**：`attrs[].attrType.id` 必须以它为前缀，
  绑错类型平台不拦、运行期才炸 —— 所以这个值**不能猜**。
★ `app.appId` 真实值是 **null**，只有 `appName` 有效。

### 8.1 mappingType 的两个分支（24 vs 15）

| 入参 itemType | mappingType | 传参方式 | 实测 |
|---|---|---|---|
| DTO（`com.x.…Dto`） | `"attrs"` | `attrs[]` 字段映射 | 24 个 |
| 标量（`java.lang.Long` / `java.lang.String`） | **null（不写）** | `value` 传单值 | 15 个 |

★ 按「必须 attrs」一刀切会把 38% 的合法节点判非法。

### 8.2 约束器修正（阳性对照 83/83）

本轮用 DB 里 83 个真实 `CALL_APP_SERVICE` 节点对 `validate_call_app_service`
做阳性对照，暴露两处过度约束：

```
修正前：83 个真实节点 → 83 个被判非法（100% 误杀）
  ① 类型只比短名，真实值是 FQN
  ② mappingType 一律要求 attrs，标量入参的 15 个节点本来就没有
修正后：83 个真实节点 → 0 个被判非法
```

★ 教训：**约束器写完必须拿真实正例跑一遍**。
  只跑反例（错误输入能被拦）证明不了约束正确，只能证明它「会拦东西」。


