# 微流程节点类型全表（56 种 actionType）

> 证据级：LIVE（DB 回读 4,943 个真实微流程的 `udc_microflow_info.data_schema` 统计）
> 口径：`data_schema.nodes[].actionType`（BRANCH/FOR_EACH 这类结构性节点没有
> actionType，取其 `type`）。次数为该节点在全库出现的频次，可用于判断哪些是主流路径。

## 一、频次表（从高到低）

| actionType | 次数 | 中文名 | 关键字段 |
|---|---:|---|---|
| `BRANCH` | 2,573 | 分支 | `conditions` |
| `CALL_MICRO_FLOW` | 1,460 | 调用微流程 | `mfService`, `mappingType`, `value` |
| `RETRIEVE` | 910 | 查询单条数据 | `fetchType`, `app`, `structure`, `condition`, `output` |
| `CREATE_VARIABLE` | 752 | 创建变量 | `paramType`, `dataType`, `structure`, `mappingType` |
| `VALUE_HANDLE` | 637 | 值操作 | `items` |
| `CHANGE_VARIABLE_FRONT` | 537 | 修改变量（前端） | `selectParam`, `mappingType`, `attrs` |
| `FOR_EACH` | 488 | 列表循环 | `foreach`, `targetName`, `nodes` |
| `CREATE_LIST` | 389 | 创建列表 | `paramType`, `dataType`, `structure` |
| `CREATE_VARIABLE_FRONT` | 382 | 创建变量（前端） | `paramType`, `mappingType`, `attrs` |
| `RETRIEVE_ARRAY` | 320 | 查询列表 | 同 RETRIEVE + `pageSearch` |

## 二、全部 56 种（字母序）

```
ATTACHMENT_DOWNLOAD      ATTACHMENT_PREVIEW      ATTACHMENT_UPLOAD
BRANCH                   CALL_APP_SERVICE        CALL_DATA_FLOW
CALL_DATA_FLOW_FRONT     CALL_FRONT_FLOW         CALL_MICRO_FLOW
CHANGE_BATCH_ENTITY      CHANGE_ENTITY           CHANGE_LIST
CHANGE_LIST_FRONT        CHANGE_VARIABLE         CHANGE_VARIABLE_FRONT
CLOSE_PAGE               CONFIRM_CLOSE_PAGE      CONTROL_ACTION
CONTROL_STATUS           CONVERT_DATA            CONVERT_DATA_FRONT
CREATE_BATCH_ENTITY      CREATE_ENTITY           CREATE_LIST
CREATE_LIST_FRONT        CREATE_MAP              CREATE_VARIABLE
CREATE_VARIABLE_FRONT    CUSTOM_ERROR            DATA_MAPPING
DELETE_ENTITY            ENTITY_EXPORT           ENTITY_IMPORT
ENTITY_REFRESH           ENTITY_SAVE             ENTITY_SAVE_DRAFT
FED_LIST_OPERATION       FLOW_ACTION             FOR
FOR_EACH                 FORM_CONVERT            LIST_OPERATION
LOCATION_CMP             MAP_OPERATION           MESSAGE_INFO
MODAL                    OPEN_LINK               OPEN_PAGE
PUBLISH_BUSINESS_EVENT   RELOAD_PAGE             RETRIEVE
RETRIEVE_ARRAY           SUB_MICROFLOW           THROW_EVENT
VALUE_HANDLE             VISIBLE
```

## 三、节点对象通用形状

两种 `type`：

**结构性节点**（`BRANCH` / `FOR_EACH`）没有 `actionType`，`type` 直接是类型名：

```json
{"nodeId":"BRANCH_28vudK","name":"userBranch","type":"BRANCH","caption":"分支(1)",
 "description":"","runAfter":null,"conditions":[...]}
```

**活动节点**统一 `type:"ACTIVITY"` + `actionType`：

```json
{"nodeId":"RETRIEVE_z1wgOL","name":null,"type":"ACTIVITY","caption":"查询单条数据(1)",
 "description":null,"runAfter":null,"input":null,"output":{...},"isCompleted":true,
 "actionType":"RETRIEVE", ...该类型专属字段}
```

`nodeId` 命名规则：`<actionType>_<6 位大小写字母数字>`，例：
`RETRIEVE_z1wgOL`、`CREATE_VARIABLE_FbpSF5`、`CONTROL_ACTION_GsfM0i`、`BRANCH_wLxxE7`。
`FOR_EACH` 例外，用 `ForEach_<6 位>`。

`runAfter: null` 表示接在开始节点后；有依赖时填上游 `nodeId`。

## 四、RETRIEVE 节点完整结构（最常用的业务节点）

```json
{
  "nodeId": "RETRIEVE_xxxxxx",
  "name": null, "type": "ACTIVITY", "caption": "查询单条数据(1)",
  "description": null, "runAfter": null, "input": null, "isCompleted": true,
  "actionType": "RETRIEVE",
  "fetchType": "CONDITION",
  "selectType": "DTO",
  "scope": "OBJECT",
  "needCascade": false,
  "nullHandling": "CONTINUE",
  "title": "<实体 caption>",
  "app": {
    "appId": "<appId>", "appName": "<前缀><appId>", "caption": "<应用名>",
    "inApp": true, "udcApp": true, "dynamicDependency": false
  },
  "structure": {
    "key":   "com.seeyon.<appName>.domain.entity.<Entity>",
    "id":    "com.seeyon.<appName>.dto.<Entity>Dto",
    "label": "<实体 caption>",
    "dataType": "DTO",
    "entity": "com.seeyon.<appName>.domain.entity.<Entity>",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true,
    "fullName": "com.seeyon.<appName>.dto.<Entity>Dto",
    "relationEntity": "<实体 id>",
    "methodLegal": {
      "available": true, "complexCondition": true, "seniorMethod": true,
      "serviceType": "NONE", "interfaceClassFullName": null
    }
  },
  "output": {
    "appName": "<前缀><appId>",
    "id": "com.seeyon.<appName>.dto.<Entity>Dto",
    "javaType": "com.seeyon.<appName>.dto.<Entity>Dto",
    "dataType": "DTO", "type": "OBJECT", "desc": "<变量名>",
    "dtoType": "MASTER_ENTITY", "udcApp": true,
    "name": "_RETRIEVE_<6位>"
  },
  "condition": [
    {
      "type": "GROUP", "uuid": "<uuid4>",
      "conditions": [
        {
          "type": "CONDITION",
          "leftParam": {
            "id": "com.seeyon.<appName>.dto.<Entity>Dto.<field>",
            "type": "OBJECT", "javaType": "java.lang.String",
            "dto": "_<field>", "field": "<field>", "desc": "<字段 caption>",
            "dataType": "STRING", "multiSelect": false
          },
          "operator": {"value": "EQ", "desc": "="},
          "rightParams": [
            {"type": "CONTEXT_VARIABLE", "value": "{\"key\":\"...\",\"name\":\"...\",...}"}
          ]
        }
      ]
    }
  ],
  "sortParams": null
}
```

## 五、命名规则（从样本反推，UNVERIFIED 待本应用实测）

```
appName   = <应用标识前缀> + <appId>
           例：appId 7001530513149673721 → appName xiangmuguanlicopy7001530513149673721
DTO 全名  = com.seeyon.<appName>.dto.<EntityName>Dto
实体全名  = com.seeyon.<appName>.domain.entity.<EntityName>
```

`udc_entity` 表**没有** DTO 全名字段（`host_app_name` 为空，`table_name` 是物理表名），
DTO 名由运行时按上述规则生成。前缀取自运行态 URL 里的应用标识段
（`/main/portal/<appName><appId>/<pageUrl>`）。

## 六、怎么用这张表

1. **要加节点**：先按 §三 判断是结构性还是活动节点，再照 §四 填专属字段。
2. **要选类型**：优先用频次前 10 的（真实项目里 90% 的流程都是这些）。
3. **要查依赖**：`runAfter` 指向上游 `nodeId`；`null` = 直接接开始节点。
4. **要校验**：写完 `udcMicroflowUpdatePost` 落库后，必须打开设计器看节点是否渲染——
   和 dataSchema 骨架同理，字段缺了平台不报错，只在 UI 上表现出来。
