# 运行态取证：不进设计器也能定位「为什么 null / 为什么没写」

设计态查不到（应用已删或账号无权限：`udcMicroflowSearch` → `UDC_APP_0001`，
`udcMicroflowFindByIdGet` → `BOOT_4002`）时，仍可从运行态拿到节点级证据。

## 1. 微流程节点级日志（定位失败节点与错误原文）

```
POST /service/{appName}/udc-runtime/app-log/search-details/microflow/flowLog
{"microFlowCode":"mFSERVICExxxxxx","subModuleType":"MICRO_FLOW_MANUAL","traceId":"<列表行 traceId>"}
```

- **`traceId` 是唯一能让它返回内容的键**；只给 `microFlowCode + subModuleType` → `data.content=null`。
- 缺 `microFlowCode` → `BOOT_1001 microFlowCode must not be null`；缺 `subModuleType` → `BOOT_1001 subModuleType must not be null`。
- `subModuleType` 取列表行原值：服务定义 = `MICRO_FLOW_MANUAL`，前端规则 = `MICRO_FLOW_FRONTEND`。
- 返回 `content.flowLogs[]`：`stepNum / activityType / activityCaption / nodeId / success / errorMsg / input / output / logStartTime`。
  节点级 `errorMsg` 才是真实原因（列表行只有 `success=false`，`errorMsg` 恒 null）。
- `/search-details/microflow`（不带 `/flowLog`）用 `requestId` / `id` / `dataId` / `signatureUuid` 试都回空数组，不要在这上面耗轮次。
- 列表行的 `dataId` 对服务流程来说就是**流程 id**（雪花号），可用于反查设计态（无权限时同样 `BOOT_4002`）。

判读要点：

- 单事务语义：某节点 `success=false` 后**后续节点一条都不出现**，是「串行 + 失败即中断」的直接证据。
- 失败节点之后的写节点没执行 → 业务表不会有任何变更；"页面提示成功" 与 "写库成功" 必须分开验。

## 2. 单条业务数据回读（查字段当前值、空值、枚举项 id）

```
POST /service/{appName}/udc-runtime/data/query
{"appName":"<appName>","dataId":"<记录id>","entityFullName":"com.seeyon.<app>.domain.entity.<Entity>"}
```

- 缺参数时报错文案就是字段名（`dataId 数据id`），据此补参即可。
- `data.content.data` 是完整 DTO（合同类实体 400+ 字段），适合查：作废/终止相关字段是否仍为初始值（`nullifyReason=""`、`nullifyTime=null`、`nullifyId="0"`）、枚举字段当前挂的是哪个 item id。
- 枚举项 id 与 label 的对应：DB 里 `ctp_enum_item` 一类表（id / name(i18n JSON) / item_value），别用 item_value 反推 id。

## 3. filter-plan 的 `{filterId}` 以后端 URL 末段为准

反编译 `UdcPageProxyAppService.dynamicJoinSelect`（udc-starter-runtime）：

```java
Long filterPlanGuid = Long.valueOf(parseDto.getFilterGuid());   // 取 URL 末段
ArrayList<Long> d = new ArrayList<>(); d.add(filterPlanGuid);
filterPlanDynamicSelectDto.setFilterPlanGuids(d);               // 覆盖 body 里的 filterPlanGuids
```

⇒ **换 body 里的 `filterPlanGuids` 测「有没有过滤」是无效实验**（永远走 URL 那个 plan）。
未配置 plan 时会抛 `未获取到筛选方案`；能返回 200 就说明该 guid 存在。
`searchParams` 走 `DynamicSearchParamDto`（`expressionValues` 按表达式 guid 传值；
API 形态的 `searchParam` 键形如 `EQ_<entity>_<field>`），落地由 `filterPlanAnalyzeService` 拼动态 SQL。

## 4. 「这个按钮到底改什么」：先读前端规则源码

构建产物 frontend 包（如 `<PATH><appName>-<ver>/pc/src/microflows/<flowId>.ts`）
里有每条前端规则的完整 TS：节点顺序、表达式、`CALL_MICRO_FLOW` 的 `mfServiceId` / `path` / 传参，一目了然。

两个反复踩的点：

1. **`CALL_MICRO_FLOW` 不校验被调微流程的返回值**。实测「调用作废」：服务流程空指针失败，
   前端照样往下走 `提示消息("作废成功")` + 关闭页面。→ **页面提示成功 ≠ 写库成功**，
   验收必须回读业务表。
2. 列表页按钮常常只是 `OPEN_PAGE`（开弹窗页）+ `ENTITY_REFRESH`（关窗后刷新），真正写库在弹窗页规则
   转给的服务流程里。定位要顺着：按钮 → 页面规则 ts → `CALL_MICRO_FLOW` 的 mfServiceId → 服务流程运行日志。

## 5. 元数据导出可能只有 FRONTEND 流

`metadata_<date>/<appId>/microflow/*.json` 这类导出实测可能 **1033 条全是 `type=FRONTEND`**，
SERVICE 流不在其中。别因为导出里搜不到某条服务流程就断言「流程不存在」——
它可能只是在导出范围外（服务流定义只在设计库/runtime 产物里）。
