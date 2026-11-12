# 微流程节点写入契约

> 证据级：LIVE（2026-11-09，test2 现场全链实测）
> **本文件只讲「怎么正确造出一个节点并落库」。**
> 设计器画布是否渲染**不在本仓范围内**——微流程节点、触发器、schema 组装
> 已经是全通能力，直接生成即可（2026-11-10 裁决，不要再把画布当待办）。

## 一、实体选择器 —— 节点 structure 的唯一合法来源

```graphql
mutation graphqlLoader ($p: udcMicroflowSearchTreeEntityPostInputBody) {
  data0: udcMicroflowSearchTreeEntityPost(body: $p) {
    code data { content } message
  }
}
```

**入参（关键，少一个就报 `UDC_MICROFLOW_0024 non null hash key required`）**：

```json
{"appId": <appId>, "appName": "<应用标识><appId>"}
```

- `appId` 必须是 **Long 数字**，不能是字符串
- `appName` **必填**，等于 `<应用标识><appId>`
- `entityId` 可不传（传了也忽略）

**返回**（每条即一个可用的 structure）：

```json
{
  "fullName": "com.seeyon.<appName>.domain.entity.<Entity>",
  "dtoFullName": "com.seeyon.<appName>.dto.<Entity>Dto",
  "caption": "<实体 caption>",
  "dtoType": "MASTER_ENTITY",
  "udcApp": true,
  "relationEntity": "<实体 id>",
  "customs": {"name": "...", "guid": "...", "from": "udc", "id": "...",
              "stereotype": "standard", "entityCategory": "ENTITY"},
  "methodLegal": {"validate": true, "available": true,
                  "complexCondition": true, "seniorMethod": true,
                  "serviceType": "NONE", "interfaceClassFullName": null}
}
```

★ 顺带证实：**DTO 全名规则** `com.seeyon.<appName>.dto.<Entity>Dto` 是对的，
`appName = <应用标识> + <appId>`。

## 二、微流程详情读取

```graphql
query q($path: udcMicroflowFindByIdGetInputPath) {
  udcMicroflowFindByIdGet(path: $path) { code data { content } message }
}
```

`path` 是 **Map 不是 String**，传 `{"id": "<microFlowId>"}`。
（传字符串报 `java.lang.String cannot be cast to java.util.Map`）

## 三、节点构造器

`components/udc/microflow/nodes.py`：

```python
from components.udc.microflow import nodes

structure = {  # 直接来自上表 searchTreeEntity 的一条
    "key": rec["fullName"], "id": rec["dtoFullName"], "label": rec["caption"],
    "dataType": "DTO", "entity": rec["fullName"], "dtoType": rec["dtoType"],
    "udcApp": True, "fullName": rec["dtoFullName"],
    "relationEntity": rec["relationEntity"], "methodLegal": rec["methodLegal"],
}
app = {"appId": str(appId), "appName": appName, "caption": "<应用名>",
       "inApp": True, "udcApp": True, "dynamicDependency": False}
cond = nodes.condition_group([
    nodes.condition(nodes.left_param(rec["dtoFullName"], "probeName"), "EQ", "测试")
])
node = nodes.retrieve(app, structure, title="<实体caption>_1",
                      condition_=cond, caption="查询单条数据(1)")
```

`check_contracts(schema)` 通过。生成的节点 **21 个键**，与真实 RETRIEVE 节点**逐键一致**。

## 四、落库与回读

```
udcMicroflowUpdatePost        → BOOT_0000 content:1
udcMicroflowFindByIdGet       → dataSchema 完整回读（实测 2,678 B）
    nodes[0].nodeId   = RETRIEVE_xxxxxx
    nodes[0].actionType = RETRIEVE
    endNode.type      = END
    trigger.nodeId    = MFStartNode
```

MCP 侧对应 `seeyon_microflow_data_schema`（组装）+ `seeyon_microflow_publish`（发布）。

## 五、别踩的坑

- **不要手拼 structure/DTO 名**。`nodes.retrieve()` 的 docstring 明确写了
  「app / structure 必须来自实体选择器接口的真实返回，不能手拼」。
  手拼的名字碰巧对了（规则确实可推导），但 `MetaDataQueryDto` 那些必填参数
  一个都不会因此变对。
- **`findDtoByEntity` 不是实体选择器**。传 `{appId, entityId}` 永远回
  `UDC_MICROFLOW_0022 该实体数据没有暴露对应的对象`，即使 DTO 明明存在。
- **`MetaDataQueryDto.appId` 是 `Long` 且 `@NotNull`**。
  反编译件：`docs/audit/artifacts/decompiled/cfr-r31b/com/seeyon/udc/microflow/dto/MetaDataQueryDto.java`
- **`udcMicroflowSelectByIdPost` 这个 op 不存在**。用 `udcMicroflowFindByIdGet`。
- **`output` 不要留 null**。改成 `{"desc": "", "hasPagination": false}`，
  否则出参面板空白（这是**参数页**的问题，与画布无关）。
- **CDP 传含中文 body 禁用裸 `atob()`**（latin1 解码会乱），
  必须 `Uint8Array.from(atob(x), c=>c.charCodeAt(0))` + `TextDecoder('utf-8')`。
- **`Page.addScriptToEvaluateOnNewDocument` 前要先 `Page.enable`**，
  否则注入不生效（静默失败，抓到 0 条请求）。
