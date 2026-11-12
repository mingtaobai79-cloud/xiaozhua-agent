# 节点形态备忘（含尚未运行时验证的几类）

覆盖口径：643 条语料 5956 个节点实例里，这几类共 405 个（6.8%），曾是最大缺口。
**SUB_MICROFLOW / CALL_APP_SERVICE / DATA_MAPPING 已全部升为 RUNTIME_VERIFIED**
（详见 `node-sub-microflow.md`、`node-call-app-service.md`、`node-data-mapping.md`）；
FOR 已有构造器与语料形态，仍未单独立运行时用例。本节保留结构样例与形态限制，升级结论以能力矩阵为准。

## 1. SUB_MICROFLOW（子微流程，251）
**语义**：在当前流程里同步调用另一条 RELEASE 的子微流程，等它返回再继续。相当于方法调用。

```json
{"actionType":"SUB_MICROFLOW","type":"ACTIVITY","caption":"子微流程(1)",
 "isCompleted":true,"output":{...},"input":null,"mappingType":"attrs","attrs":[...],
 "mfService":{"id":"-4653990252107149853","appId":"3289082814923688017",
   "caption":"合同审批人获取","hasInput":true,"hasOutput":true,
   "input":{DTO 入参},”output”:{出参},"method":"POST","name":"MFSERVICEEnXdwj",
   "path":"/microflow/MFSERVICEEnXdwj","triggerType":"MANUAL","type":"SERVICE"}}
```

生成要点（**以 `node-sub-microflow.md` 为准，本节仅留结构样例**）：
- `mfService` 不能手搓：必须读目标流程**当前**的 `ds.input`/`ds.output`
  （`LiveRefs.microflow_detail(mf_id)`）；`sub_mf_candidates` 只回 id/name/caption，不含契约；
- **标量入参**（`dataType != DTO`）：`mappingType="value"` + `value` 引用槽，
  **不是** `attrs`；只有 DTO 入参才用 `mappingType="attrs"` + `attrs[]` 逐字段映射；
- 出参类型照抄目标流程的 `output`，不要自己推；
- 状态：**RUNTIME_VERIFIED**（父子流程自建，入参/出参全链 + 契约变更检测均已实测）。

## 2. CALL_APP_SERVICE（调用应用服务，105）
**语义**：直接调另一个应用暴露的 AppService 方法（dubbo/本地 service），比子微流程更底层。

```json
{"actionType":"CALL_APP_SERVICE","caption":"自定义服务(5)",
 "selectMethod":{...},"value":{...},"outputName":"...","outPutDesc":"...","output":{...}}
```

生成要点（三步链路，全部走 GraphQL）：
1. `udcMicroflowSearchAppServiceByAppNamePost` 选服务；
2. `udcMicroflowSearchMethodByNamePost` 选方法 → 后端反射返回 `parameter`/`returnValue`（含 DTO fullName + md5）；
3. 入参是 DTO 时再调 `udcMicroflowFindCustomDtoPost` 拿 `attributes` 渲染参数映射。
**参数定义是后端返回的，不是写死的**——不要按业务名猜字段。

状态：**RUNTIME_VERIFIED**（starter 流水号组件，连取三轮递增落库）。
三个必对细节见 SKILL.md §4.20 与 `node-call-app-service.md`：
starter 归属自动推导（`boot-starter-<stem>` / `inApp=false`）、attrs 用字段级 attrType、
简单类型返回值 `dataType` 不能默认 DTO。

## 3. FOR（计数循环，32）
**语义**：按数字区间循环（不是遍历列表）。和 FOR_EACH 并列，是两个不同的控制节点。

```json
{"type":"FOR","caption":"计数循环(1)","isCompleted":true,
 "forStart":{"type":"Simple","simple":0,"desc":0},
 "forEnd":{"type":"Simple","simple":5,"desc":5},
 "forStep":1,"operator":"<=","targetName":"计数循环变量_1",
 "output":{"dataType":"INTEGER","javaType":"java.lang.Integer",
           "desc":"计数循环变量_1","name":"_FOR_liP50k"}}
```

生成要点：出参是 INTEGER 计数器；`forStep` 是数字不是表达式；子节点放 `nodes[]`。

## 4. DATA_MAPPING（数据转换，17）
**语义**：把一个实体/列表按规则转成另一个结构（源 DTO → 目标 DTO），可一对多、可字段改名。

```json
{"actionType":"DATA_MAPPING","caption":"数据转换(1)",
 "selectParam":{源数据},”structure”:{目标实体},"mappingRule":{...},"targetType":...,
 "app":{...},"dataType":"DTO","output":{转换后的 DTO/ARRAY}}
```

生成要点：`selectParam` 是源，`structure` 是目标；`mappingRule` 空会生成空对象；
与 CREATE_VARIABLE(实体对象) 的区别是 **可以跨实体**，且按规则批量映射。

**★ 形态限制（真实构建实测；checkSchema/UI/检测全不拦，只有构建炸）**：
代码生成器把 DATA_MAPPING 按「列表转换」产码——上游必须是子表/列表形态
（语料 39 条：SUB_ENTITY/children 13、空引用 22、CUSTOM 3；`selectParam.name` 形如 `xxxDtoList`）。
上游为单对象主实体（dtoType=MASTER_ENTITY + position=parent）时，生成代码把节点输出声明成
`List<Dto>` 再对它取字段 → `找不到符号 getName()`，构建 82% 处 FAIL。
闸门 G29 已拦；构造器 `microflow_nodes_svc.data_mapping` 已泛化
（src_field/dst_field/target_entity 参数）。最小验证需要带子表的实体，纯主实体应用造不出合法形态。

状态：**RUNTIME_VERIFIED**（`RETRIEVE_ARRAY(3 条) → DATA_MAPPING(sourceTable→taskId) → CREATE_BATCH_ENTITY`，
写回 3 行 `task_id='DM-SRC'`）。已确认的两个坑：ARRAY 判定必须写在 `_entity_output()` **之后**
（否则被覆盖回 OBJECT，G31 判死）；DSL 的 `src_field`/`dst_field` 要在 `_do_data_mapping` 与
`_st_data_mapping` 两处都透传。`FIRST_ONE` 接手映射输出会丢 javaType（未修）。
详见 `node-data-mapping.md`。
