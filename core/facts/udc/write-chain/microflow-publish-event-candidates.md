# UDC 微流程「事件投递」节点事件候选池 —— 权威契约与根因（LIVE + CFR 双证）

> 2026-10-16。方法：CDP 抓包（编辑器面板加载真实请求）+ cfr 反编译（udc-biz 5.3.517）+ MySQL 直连。
> 本轮结论推翻了此前"直接挂对象定义事件对象"的做法。

## 1. 面板真实加载契约（抓包 LIVE）

打开编辑器 → 点「流程」tab → 双击「事件投递」节点，前端发出**唯一一个** graphql 批量请求：

    POST /service/udc/graphql?udcMicroflowSearchEventListPost&udcMicroflowFindCustomDtoPost

    mutation graphqlLoader(
      $params0: udcMicroflowSearchEventListPostInputBody,
      $params1: udcMicroflowFindCustomDtoPostInputBody) {
      data0: udcMicroflowSearchEventListPost(body:$params0) { code data { content { fullName caption source dtoType udcApp } } message status }
      data1: udcMicroflowFindCustomDtoPost(body:$params1)   { code data { content { attributes caption fullName type relationEntityId methodLegals dtoType udcApp refApp entity } } message status }
    }

    variables = {
      "params0": { "appId": "<APP>", "appName": "<APPNAME>" },
      "params1": { "appId": "<APP>", "appName": "<APPNAME>",
                   "dtoFullName": "<当前节点 selectEvent.fullName>", "needChildren": true }
    }

**关键**：`params0` **不带任何事件名**——它是"列本应用全部可投递事件"的候选池查询；`params1` 才按已选事件取参数结构。
（此前我用 `{appId, appName}` 单发 data0 报 `BOOT_3000 Required request body is missing` 是**误判**：批量 graphqlLoader 形态下同样的 variables 可正常返回 `content: []`。单发时 graphqlLoader 的批量包装缺失导致 body 未透传。）

## 2. 候选池过滤条件（CFR 字节码，udc-biz 5.3.517）

`MicroFlowAppService.searchMicroFlowEventList(SingleRequest<MetaDataQueryDto>)`
→ `MicroFlowMetaDataQueryService.searchMicroFlowEventByAppName(query)`:

    searchMetadataDto.setAppId(query.getAppId());
    dtoMetadataList = metadataQueryService.queryDesign(searchMetadataDto, selectDtoMetadataExcludeBoot)...
    mfEventFilterCondition = i -> Optional.ofNullable(i.getCustoms())
        .map(j -> j.get("source"))
        .map(j -> DtoSourceEnum.valueOf(String.valueOf(j)))
        .map(arg -> DtoSourceEnum.MICRO_FLOW_EVENT.equals(arg)).orElse(false);
    return dtoMetadataList.stream().filter(mfEventFilterCondition).map(this::buildMfDtoItem)...

**候选池 = 设计态 DTO metadata 中 `customs.source == DtoSourceEnum.MICRO_FLOW_EVENT` 的项**。
不是「对象定义-事件对象」表（`udc_event`），二者是不同的东西。

## 3. 本应用现状（MySQL 直连 LIVE）

    udc_data_transfer_object WHERE app_id=8704025620829192834 AND source IN (4,5)  →  0 行
    全租户 WHERE name LIKE '%Xzh%'  →  0 行
    udc_last_version_metadata WHERE metadata_schema LIKE '%MICRO_FLOW_EVENT%'  →  0 行
    udc_event (本应用)  →  4 行（xzhBusListener / xzhMfEventListener / xzhEntityEvent / xzhEvtObj1）—— 但这是「事件表」，不是候选池来源

`source` 分布（全租户）：`1=1316`（普通 DTO）、`4=60`（事件对象）、`5=48`（事件投递对象）。
**本应用 source=4/5 = 0 ⇒ 候选池天然为空 ⇒ 面板红字「所选"可投递的事件"已失效」。**

## 4. 结论（防复发铁律）

1. **事件投递节点不能挂「对象定义」的事件对象**（`udc_event` / `udcEventListPost` 返回的 `xzhEvtObj1` 等），必须挂 **`customs.source=MICRO_FLOW_EVENT` 的 DTO**，其 fullName 形如 `com.seeyon.<appName>.dto.microflow.event.<EventName>`。
2. **手工编造事件 fullName 一定红字**（我此前用 `XzhBusinessEvent` / `Htxqcqrct7yk` 皆错）。
3. **投递前必须先在本应用创建事件对象**（DTO），创建入口 = 事件投递面板「可投递的事件」下拉的「新建」→
   `udcDataTransferObjectCreateDtoPost`（`createDtoWithAttrs`）；对象定义面相关 op 见 §5。
4. **验证口径**：候选池非空 ⇔ `udcMicroflowSearchEventListPost` 返回的 `data0.content` 长度 > 0。
   该调用是只读的、可重复的，应作为事件投递节点的**前置断言**。

## 5. 对象/DTO 相关 op 清单（bundle 权威，模块 55374）

| op | 用途 |
|---|---|
| `udcDataTypeSelectByParamsPost` | 数据类型下拉 |
| `udcDataTransferObjectGet` (paramsKey=path, {id}) | 按 id 取 DTO |
| `udcDataTransferObjectSelectDtoGet` (path, {id}) | 取 DTO 详情+属性（含 source、publishState） |
| `udcDataTransferObjectCreateDtoPost` | **创建 DTO**（事件对象创建入口） |
| `udcDataTransferObjectUpdateDtoPost` | 更新 DTO |
| `udcDataTransferObjectDeletePost` | 删除 DTO |
| `udcMicroflowTreeEntityDtoPost` | 实体/DTO 候选树 |
| `udcMicroflowSelectMessageGet` (path, {id}) | 取消息对象 |
| `udcMicroflowCreateMessagePost` | 创建消息对象（source=5） |
| `udcMicroflowUpdateMessagePost` | 更新消息对象 |
| `udcMicroflowMessageDtoDeletePost` | 删除消息对象 |
| `udcMicroflowSearchEventListPost` | **事件投递候选池** |
| `udcMicroflowFindCustomDtoPost` | 按 dtoFullName 取 DTO 属性 |

## 6. 面板 items 契约（bundle 权威，事件投递 settings）

    { key:"selectEvent", label:"可投递的事件", type:"treeListSelector", required:true,
      dependency:{ appName: eventType==="AMONG_APP" ? "$app.appName" : h.FU.appName },
      dataListInfo: eu,                       // IN_APP 分支
      setEmptyBeforeChanged:["value","attrs","mappingType","messageType"],
      ishidden: eventType !== "IN_APP" }

    { key:"selectMq", label:"可投递的事件", ... dataListInfo: eventType==="AMONG_APP" ? ed : eu ... }

    // 候选项构造（eu）
    t.map(e => ({ key:e.fullName, label:e.caption, value:e.fullName,
                  fullName:e.fullName, caption:e.caption, source:e.source,
                  dtoType:e.dtoType, udcApp:e.udcApp }))

**面板红字组件（bundle 权威）**：`treeListSelector` 内部用
`j = useMemo(() => { let e=false; const t=(n,a)=>{ n.forEach(n => { n.key===a && (e=true); n.children && t(n.children,a) }) }; t(候选树, 已选值); return e })`
—— **匹配键是候选项的 `key`，即 `fullName`**；找不到 ⇒ 红字 `所选"<label>"已失效，请重新选择`。
（另一组件 `SelectContainer` 用 `keyCode` 默认 `key` 匹配，红字文案 `所选数据已变更`。）

## 7. 表达式函数库（同一批抓包的副产物）

同一次面板加载还触发了**系统函数/变量全集**接口，响应已落盘：
`docs/audit/artifacts/udc-expression-functions-raw.json`（含 `type=SYSTEM`、`functionName`、`name`、`resultType`、`relationEntity`、`description` 分组项）。
→ P2 表达式域的权威数据源。
