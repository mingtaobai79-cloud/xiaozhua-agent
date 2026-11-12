# 微流程数据流设计 + 节点能力矩阵

> 状态：LIVE（2026-10-24）
> 样板：`xzhDFv6` = `-1369717027536293915`（RELEASE，17 顶层节点 / 17 种类型）
> 验证：`check=True, errors=0` + 页面画布 0 条必填告警
> 生成器：`tools/core/microflow/{dataflow_builder,build_dataflow_demo}.py`

## 一、先纠正一个根本性的错

「每种 actionType 出现一次」不等于「节点用对了」。前者能过 `checkSchema`，
但每个节点都是空壳（Map 空、修改变量没值、列表空、条件不选），页面一打开就满屏必填告警。

**判据应该是：每个节点的取值都来自上游真实产出。** 见第二节的数据流。

## 二、真实数据流（样板结构）

```
入参 _FLOW_INPUT_xxx  STRING  「文本字段」
 │
 ├─1 CREATE_VARIABLE  BASIC  vText            空壳，等赋值
 ├─2 CHANGE_VARIABLE  vText ← 入参            mappingType=value + SelectParam
 ├─3 CREATE_LIST      BASIC  vTexts
 ├─4 CHANGE_LIST      ADD    vTexts ← vText   列表真的有数据
 ├─5 LIST_OPERATION   SIZE   vTexts → 计数     非空计数
 ├─6 RETRIEVE  条件 f01text = 入参，nullHandling=TERMINATION + nullPromptMessage
 ├─7 CREATE_ENTITY  mappingType=attrs  字段映射 f01text ← vText
 ├─8 CHANGE_ENTITY  selectParam=第6步，字段映射
 ├─9 RETRIEVE_ARRAY 条件 f01text = 入参，scope=ARRAY，size=20
 ├─10 CREATE_MAP → MAP_OPERATION PUT(k←vText,v←计数) → GET → KEY_SET
 ├─11 DELETE_ENTITY 条件 id = -1（永假，防误删）
 ├─12 SUB_MICROFLOW
 ├─13 CUSTOM_ERROR  error=Expression（引用计数拼消息）
 └─14 FOR 1..3 { BRANCH(计数 > 0) { BREAK } else {} }
```

## 三、节点能力矩阵（对照真实库）

```
CREATE_VARIABLE.paramType     BASIC 473 / ENTITY_OBJECT 442 / DEFAULT_OBJECT 129 / OTHER 38 / MESSAGE 1
CREATE_LIST.paramType         ENTITY_OBJECT 258 / BASIC 71 / DEFAULT_OBJECT 19
CREATE_MAP                    paramType、dataType 恒为 null
CHANGE_VARIABLE.mappingType   None 942 / attrs 551 / value 24 / mapping 13
CHANGE_LIST.action            ADD 486 / REPLACE 37 / CLEAR 22 / REMOVE 6
LIST_OPERATION.operationType  14 种：FILTER 169 / FIRST_ONE 149 / MAP 87 / SUM 58 / PICK_ONE 52
                              / DISTINCT 42 / LAST_ONE 38 / SIZE 23 / SORT 16 / MAX 14 / SUBTRACT 8
                              / GROUP_AND_SUM 5 / MIN 2 / INTERSECT 1
MAP_OPERATION.operationType   GET 21 / PUT 13 / KEY_SET 4
RETRIEVE.fetchType            CONDITION 730 / IDS 335 / COUNT 1
RETRIEVE_ARRAY.fetchType      CONDITION 295 / IDS 28 / OTHERS 22 / COUNT 18
RETRIEVE_ARRAY.scope          ARRAY 362 / OBJECT 1        ← 必须 ARRAY
RETRIEVE.nullHandling         CONTINUE 944 / TERMINATION 122
CREATE_ENTITY.mappingType     attrs 64 / value 50
DELETE_ENTITY.deleteType      CONDITION 10 / SELECT_PARAM 9 / IDS 1
CONVERT_DATA.convertType      6 种（符号拆分文本 / 多选转长整数列表 / 长整数列表拼多选 / 基础转文本 / 文本转长整数 / 文本转整数）
PUBLISH_BUSINESS_EVENT        eventType: IN_APP / AMONG_APP
```

## 四、铁律（这一轮新打的，全是 BOOT_3000 / 必填告警逼出来的）

1. **`RETRIEVE_ARRAY.size` / `pageSearch` 是节点顶层字段**，不是 `pageInfo.size`。
   写成 `pageInfo: {size: 20}` 会报 `[节点].size 必填`，报错路径是 `节点.size` 而不是 `节点.pageInfo.size`。

2. **`MAP_OPERATION` 的键字段叫 `theKey`**（GET 时），不是 `key`；
   而且 GET 还要带出参类型：`paramType` / `basic` / `arrayOrObject` / `dataType` / `nullHandling`。

3. **`MAP_OPERATION.entries` 是前端无条件必填** —— GET / KEY_SET 也一样，
   给空数组会报必填。GET 只用 key 部分，value 塞同一个引用即可。

4. **`CUSTOM_ERROR.error` 必须带 `{"type":"Expression","expression":{title,schema}}` 外层包装**，
   少了这层后端反序列化失败，表现为 `checkSchema/update` 报 `BOOT_3000`，而 `create` 却成功。

5. **`VARIABLE` token 的 value 是 `<outputName>.<outputName>`**（两段都是出参名，带前导下划线），
   **不是 `nodeId.<outputName>`**。用 nodeId 会 BOOT_3000。
   真实样本：`_LIST_OPERATION_Rg4IMN._LIST_OPERATION_Rg4IMN`

6. **tokens 里有 `VARIABLE` 时，`designData.context` 必须给出变量树**，不能是 `[]`。
   结构：
   ```
   [{"name": <outputName>, "description": <节点caption>, "type": "OBJECT",
     "selectable": false, "enableDataI18n": false,
     "properties": [{"name": <outputName>, "description": <字段名>, "type": <标量类型>,
                     "selectable": true, "enableDataI18n": false,
                     "uniformityParams": {"paramId": "", "paramCategory": <dataType>,
                                          "extensionProperties": "", "pageNodeExtension": null}}]}]
   ```

7. **`runtimeData.executableExpr` = 固定前缀 + URL 编码的明文表达式**
   ```
   前缀  93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=
   拼法  前缀 + urllib.parse.quote_plus("( _LIST_OPERATION_x._LIST_OPERATION_x > 0 )")
   ```
   解码真实样本可验证：`( ( currentMonth() >= 1 ) && ( currentMonth() <= 3 ) )`

8. **`build_schema` 不能自己重算入参名** —— 节点里的 `CONTEXT_VARIABLE` / `SelectParam`
   引用的是生成器算好的 `_FLOW_INPUT_xxx`，换名会让引用悬空（同样表现为 BOOT_3000）。

9. **`RETRIEVE` 用 `nullHandling=TERMINATION` 时必须给 `nullPromptMessage`**。

10. 前端权威必填表（页面 console 的 requiredFields）：
    ```
    CREATE_VARIABLE     paramType dataType title          （基础）
                        paramType app structure title     （实体）
    CREATE_LIST         paramType dataType title
    CREATE_MAP          title
    CHANGE_VARIABLE     selectParam
    LIST_OPERATION      selectParam operationType title
    CHANGE_LIST         selectParam action dataSource
    MAP_OPERATION       selectMap operationType entries
    RETRIEVE            app structure title
    RETRIEVE_ARRAY      app structure variableTitle
    CREATE_ENTITY       app structure mappingType value title
    CHANGE_ENTITY       selectParam title
    CREATE_BATCH_ENTITY selectParam title
    CHANGE_BATCH_ENTITY selectParam title
    DELETE_ENTITY       deleteType app structure condition title
    SUB_MICROFLOW       mfService
    FOR                 forStart forEnd forStep targetName
    CUSTOM_ERROR        error
    BRANCH / CONDITION / BREAK   无
    ```

## 五、怎么用

```bash
./.venv/Scripts/python.exe tools/core/microflow/build_dataflow_demo.py \
  --app-id <appId> --app-name <appName> \
  --entity <实体name> --entity-id <实体id> --entity-caption <中文名> \
  --in-field <入参对应字段> --in-caption <字段中文名> \
  --subflow-id <子流程id> --subflow-name <name> \
  --out scratch/dataflow.json

./.venv/Scripts/python.exe tools/core/microflow/build_microflow.py \
  --app-id <appId> --caption "..." --name <流程name> --spec scratch/dataflow.json
```

★ `all_nodes_demo.py` 是「每型一个」的空壳版，只用来看节点形状；
  **要做真实流程用 `build_dataflow_demo.py`**。