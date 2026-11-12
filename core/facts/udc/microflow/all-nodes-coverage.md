# 微流程全节点覆盖（20 种类型实测）

> 状态：LIVE（2026-10-24）
> 产物：`xzhAllNodesFinal` = `805674370817996221`（本 app `datamigration9000000000000000001`）
> 结果：19 个顶层节点 / 20 种类型 → `check=True, errors=0` → `state=RELEASE`

## 一、微流程域到底有多少节点

前端 `node-catalog.json` 只有 5 个标 `MICROFLOW`，**那是节点面板的分组展示，不是可用集**。
按真实落库统计（`state=20` 的 4508 条流程）：

```
type=0 (SERVICE 微流程)   22 种 actionType, 10979 个节点
type=1 (前端/页面规则)     38 种, 16065 个节点
type=2 (实体规则)           4 种,    37 个节点
type=3 (CUSTOM)            data_schema 里无 nodes（走另一套）
```

**微流程域 = type=0 的 22 种**（按出现次数）：

```
CHANGE_VARIABLE 2413 / CREATE_VARIABLE 1785 / RETRIEVE 1683 / LIST_OPERATION 1095
CHANGE_LIST 822 / SUB_MICROFLOW 706 / RETRIEVE_ARRAY 523 / CREATE_LIST 508
CHANGE_ENTITY 374 / CALL_APP_SERVICE 296 / CONVERT_DATA 215 / CREATE_ENTITY 197
CHANGE_BATCH_ENTITY 87 / MAP_OPERATION 68 / PUBLISH_BUSINESS_EVENT 64
DELETE_ENTITY 39 / CREATE_BATCH_ENTITY 26 / CREATE_MAP 26 / DATA_MAPPING 20
BREAK 12 / CUSTOM_ERROR 11 / CALL_DATA_FLOW 9
```

外加非 actionType 的**结构节点**（只能靠 `type` 认，没有 `actionType`）：

```
FOR     计数循环（operator/forStep/forStart/forEnd + nodes）
BRANCH  conditions[] 里挂 CONDITION
BREAK   恒在 BRANCH 分支内
```

## 二、已实测通过的 20 种

| 类型 | 关键必填 | 备注 |
|---|---|---|
| `CREATE_VARIABLE` | `paramType` `title` `dataType` `output` | `paramType=BASIC` 时 `dataType` 取 STRING/BIGINTEGER/DECIMAL/BOOLEAN/DATE/DATETIME |
| `CREATE_VARIABLE`(实体) | + `app` `structure` `mappingType` | `paramType=ENTITY_OBJECT` `dataType=DTO` |
| `CREATE_LIST` | 同 CREATE_VARIABLE | `output.type="ARRAY"` |
| `CREATE_MAP` | `generics` `output` | `paramType`/`dataType` 都是 null |
| `CHANGE_VARIABLE` | `selectParam` | 指向前序 `_CREATE_VARIABLE_xxx`（含 `nodeInfo.nodeId`） |
| `LIST_OPERATION` | `selectParam` `operationType` `title` | **`operationType` 是对象** `{"type":"SIZE"}` |
| `CHANGE_LIST` | `selectParam` `action` | `selectParam` 必须 `type="ARRAY"`；`action` ∈ ADD/REPLACE/CLEAR/REMOVE |
| `MAP_OPERATION` | **`selectMap`** `operationType` `generics` | 字段名不是 `selectParam` |
| `RETRIEVE` | `app` `structure` `selectType` `scope` `methodLegal` `fetchType` `nullHandling` `title` `output` | `fetchType=COUNT` 可免条件 |
| `RETRIEVE_ARRAY` | 同上，`title` 换成 `variableTitle` | `output.type="ARRAY"` |
| `CREATE_ENTITY` | `app` `structure` `title` `methodLegal` `mappingType` `output` | |
| `CHANGE_ENTITY` | `selectParam` `title` `output` | |
| `CREATE_BATCH_ENTITY` | `selectParam` `title` `output` | |
| `CHANGE_BATCH_ENTITY` | `selectParam` `title` `output` | |
| `DELETE_ENTITY` | `app` `structure` `title` `methodLegal` `deleteType` `output` | |
| `SUB_MICROFLOW` | `mfService` | `mfService` 是扁平对象（见下） |
| `FOR` | `operator` `forStep` `forStart` `forEnd` `output` | `operator="<="`, `forStep=1` |
| `BRANCH`/`CONDITION` | `conditions` / `nodes` | 分支节点必须完整（见铁律 6） |
| `BREAK` | 无 | 父恒为 BRANCH |
| `CUSTOM_ERROR` | `type` `errorType` `error` | 见铁律 3 |

**未覆盖（4 种）**：`CALL_APP_SERVICE`（需真实 `selectMethod` 签名）、
`CONVERT_DATA`（需字段级 `selectParam` 且语义匹配）、`DATA_MAPPING`（`mappingRows` 复杂）、
`PUBLISH_BUSINESS_EVENT`（需事件 DTO）、`CALL_DATA_FLOW`（需数据流对象）。

## 三、铁律

1. **`LIST_OPERATION` 是「列表处理」，不是增删**。
   `operationType` 取值全是 `{"type": FILTER/SIZE/SUM/MAP/FIRST_ONE/PICK_ONE/DISTINCT/SORT/MAX/MIN/...}`。
   增删元素要到 `CHANGE_LIST.action`（ADD/REPLACE/CLEAR/REMOVE）。
   传字符串 `"ADD"` 会直接报错。

2. **每个会产出的节点都必须有 `output`**，包括 `FOR` 和 `CUSTOM_ERROR` 之外的绝大多数。
   `output.name` 必须与 `nodeId` 同源：`_<ACTION>_<6位>`。

3. **`CUSTOM_ERROR` 三处都和直觉不同**：
   ```
   type      = "CUSTOM_ERROR"        （不是 "ACTIVITY"）
   errorType = "GLOBAL"              （不是 "ERROR"/"WARN"）
   error     = {"type":"Simple","simple":<msg>,"desc":<msg>}   （不是字符串）
   ```

4. **`MAP_OPERATION` 的字段名是 `selectMap`**，指向 `CREATE_MAP` 的 output。

5. **实体类节点的 `output` 必须是完整 DTO 形态**：
   ```
   {"id": "<pkg>.dto.XxxDto", "javaType": 同上, "dataType": "DTO", "type": "OBJECT"/"ARRAY",
    "desc": ..., "appName": ..., "dtoType": "MASTER_ENTITY", "udcApp": true,
    "relationEntity": "<实体id>", "name": "_<ACTION>_<6位>"}
   ```
   只给 `param()` 会报 `output.id 必填`。

6. **`BRANCH.conditions[]` 必须是完整 CONDITION 节点**：
   ```
   {"nodeId":"CONDITION_xxxxxx","name":"ifBranch"|"elseIfBranch"|"elseBranch",
    "type":"CONDITION","caption":...,"description":...,"runAfter":null,
    "expression":...（elseBranch 为 null）,"isCompleted":true,"nodes":[...]}
   ```
   只写 `{name, nodes}` 会报 `type 必填`（报错里 nodeId 是空串，很难定位）。

7. **`BREAK` 的父节点恒为 `BRANCH`**（40 条真实样本 100%）。
   要"跳出循环"必须写成 `FOR { BRANCH { ifBranch: [BREAK] } }`，不能直接放 FOR 的 nodes 里。

8. **`FOR` 是计数循环**，不是列表遍历：`forStart`/`forEnd` 是 Simple 或 SelectParam，
   `foreach` 恒为 null。四项 `operator`/`forStep`/`forStart`/`forEnd` 缺一不可。

9. **`SUB_MICROFLOW.mfService` 是扁平对象**（不是完整微流程定义）：
   ```
   {"id","appCaption","appId","appName","caption","description","hasInput","hasOutput",
    "hostPath","input","method","name","output","path","triggerType","type","restType"}
   ```
   `type` 只能是 `SERVICE(0)` / `CUSTOM(3)`，`type=1` 前端微流程不可引用。

10. **`checkSchema/update` 的 body 必须是完整 create body**：
    `name`/`caption`/`type`/`triggerType`/`creationMethod`/`serviceInterface`/`dataSchema`。
    - 只给 `{appId,id,dataSchema}` → `BOOT_3002`
    - `type`/`triggerType`/`creationMethod` 传数字 → `BOOT_3000`（必须枚举名）
    - 校验不过时 `update` 仍返回 `BOOT_0000`，但 state 被静默丢弃回 DRAFT

11. **枚举名对照**：
    ```
    MicroFlowTypeEnum        SERVICE(0) FRONTEND(1) ENTITY_RULE(2) CUSTOM(3) FUNCTION(4)
    MicroFlowTriggerTypeEnum BUSINESS_EVENT(0) SCHEDULE(1) MANUAL(2) FRONTEND_PARAM(3)
    CreationMethodEnum       MANUAL(0) FROM_TEMPLATE(1) PAGE_LAYOUT(2)
    ```

## 四、生成器入口

```
scratch/build_allnodes2.py        阶段 1：变量/列表/Map（9 节点）
scratch/build_entity_nodes.py     阶段 2：实体类（8 节点）
scratch/build_service_nodes.py    阶段 3：子流程 + 循环/分支/跳出
scratch/build_all_final.py        合并成终版（19 顶层 / 20 类型）

tools/core/microflow/build_microflow.py
  --spec <json>            生成并发布
  --draft-only             只建草稿
  --resume <id>            对已有草稿继续发布
  --resume <id> --check-only --db-env test2   只跑校验、打印全部错误（迭代时用这个）
```

---

# 追加：24 种全覆盖（2026-10-24 LIVE PASS）

> 产物 `小爪全节点24-V15` = `4336030677586697794`（本 app）
> 25 个顶层节点 / 24 种 actionType → `check=True, errors=0` → `state=RELEASE` → 画布 0 业务告警

## 新增的 5 类节点真实形状

| 类型 | 关键结构 |
|---|---|
| `CALL_APP_SERVICE` | `selectMethod` 必须是完整签名对象（fullName/implClass/parameter/returnValue/md5）；`app.dynamicDependency` 在此节点是**字符串 "NONE"**；`attrs[].attrType` 用完整属性对象 |
| `CONVERT_DATA` | `convertType={desc,value:"Split",dataType:"STRING",type:"ARRAY"}` + `regex:"MIDLINE"`；`selectParam` **只能挂文本字段**，挂 DTO 报 `NOT_STR 该操作只支持文本…` |
| `PUBLISH_BUSINESS_EVENT` | `eventType:"IN_APP"`（事件总线）/`AMONG_APP`（队列）；`selectEvent` 必须是 `customs.source=MICRO_FLOW` 的 DTO（先到「对象定义→应用内事件对象」创建） |
| `CALL_DATA_FLOW` | `dataFlow={id,key,value,title,appId,appUrl,caption,name,sourceEntityId,g_l_index}`；`entityId` 校验读的是 **`structure.entityId`**，节点顶层给了也不认 |
| `DATA_MAPPING` | `mappingRule` 需 `uuid/type/javaType/name/subobjects/targetType/mappingRows`；`mappingRows[].value={reference:{id,path,name,desc,dataType,type,javaType}}` |

## 三条新铁律（都是踩出来的）

1. **条件右值禁用 `{"type":"Simple"}`**。
   用它作为 `condition[].conditions[].rightParams[]`，平台返回 `BOOT_1001「参数错误」`，
   **不指节点、不指字段**，整条请求解析失败。合法值：`CONSTANT` / `EXPRESSION` / `CONTEXT_VARIABLE`。
   二分定位：同一 body 只把 Simple 换成 CONSTANT → `check=True`。

2. **`leftParam.dto` 是 `"_" + 字段名`，不是 `"_" + 实体名`**。
   真实样本 `dto:"_kehumingcheng"`。写成 `_ysFull6956` 会让字段下拉渲染成裸 JSON。
   同源规则见 `dataflow-and-node-matrix.md`。

3. **`CREATE_ENTITY.mappingType=attrs` 时 `value` 可空**。
   真实样本 31 个 attrs、无 value；前端 requiredFields 只覆盖「对象引用」那一支。
   本地校验器已按此放行（`components/udc/microflow_constraints.py`）。

## 其余节点改造（按用户要求）

- `RETRIEVE` / `RETRIEVE_ARRAY`：必须配 **条件 + 排序**（只选「条件查询」不填条件 = 空壳）。
  `sortParams=[{sortType:"ASC|DESC", attrType:{完整属性对象}}]`；列表加 `size=999, pageSearch:"false"`。
- `CHANGE_VARIABLE`（实体对象）：`mappingType:"attrs"` + `attrs[{attrType,value,desc}]`，
  `value` 可为 `Simple` / `SelectParam` / `Expression`。
  **表达式只能复用真实编译产物**（`runtimeData.executableExpr` 是后端编译的 blob，不能自己编），
  现只有 `expression_templates.json` 的 `boolean_true` 可用。

## 未完成（明确记）

- `CALL_DATA_FLOW` 的「生单规则」下拉在界面显示的是 **id 而不是中文名**：`udc_data_flow` 表**没有 name 列**，
  节点里的 `dataFlow.name` 无处落地，映射关系待查。
- `DATA_MAPPING` 的「映射关系配置」弹窗渲染仍需按界面真实抓包校准（当前行显示方式与预期不符）。
- 生单映射（`POST /udc/data-flow/mapping`）仍卡 `BOOT_3000`：`source+target` 同时存在即失败，
  需抓一次 UI 真实请求。
