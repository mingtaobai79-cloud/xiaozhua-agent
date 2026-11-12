# 2小爪 Agent 微流程 + 表达式：权威事实提示词（FACTS ONLY）

> 用途：给任何 AI/人接手微流程与表达式生成工作时，作为唯一事实依据。
> 来源：仓库内 LIVE 实测事实文件 + 权威构造器，全部注明出处。
> 铁律：**与本文冲突时以本文所引源文件为准；源文件之间冲突时以 LIVE 实测为准。**

---

## 第一部分：微流程生成

### 1.1 三层权威材料（必须按此顺序读，缺一不可）

1. `components/udc/microflow/nodes.py` — 从全库真实节点反推的构造器（480 行）
2. `fixtures/microflow/node_templates/<ACTION>.json` — 25 个节点完整模板（UI 添加→确认后抓的 nodeConfig 快照，含 md5、methodLegal、模板默认值）
3. `core/facts/udc/microflow/` 事实文件群

### 1.2 最高铁律（违反必被打回）

> `node-authoring-contract.md` §二：**「整包 POST dataSchema 绕过前端逐节点回填，生成出来一定缺东西」**
>
> 正道 = node_templates 完整结构 + 只做参数替换（换应用/实体/字段/引用/表达式），**绝不重写结构**。
> 反例（契约 §五 明令禁止）：
> - ❌ Builder 手拼十几个字段当节点 → UI 缺 md5、缺模板默认值
> - ❌ 40 条同构配方复制凑数量 → 用户判定"空壳"打回
> - ❌ 生成后拿脚本改 schema → 掩盖根因，下一批还会错

### 1.3 节点构造铁律

- 节点 JSON 一律来自 node_templates，**引用/条件/值只做整块替换**，绝不逐字段手写（ref-and-condition-contract.md §四）
- 无出参的节点写 `output=None`，不许造假（nodes.py 硬约束 3）
- 选择器字段不能自造：`RETRIEVE` 的 app/structure/title、`CALL_APP_SERVICE` 的 app/selectMethod、`SUB_MICROFLOW` 的 mfService——**必须来自平台选择器接口的真实返回**（nodes.py 硬约束 2）
- `type` 恒为 `ACTIVITY`，真实类型看 `actionType`（node-ui-contracts-22.md §0.4）

### 1.4 关键字段形态（全部 LIVE 实测，写错必错）

| 项 | 正确形态 | 出处 |
|---|---|---|
| condition | **GROUP 数组** `[{type:"GROUP", uuid, conditions:[...]}]` | ref-and-condition-contract.md §三 |
| GROUP | 历史成功样本**无** logicalOperator（从第 2 个子条件起才必须有） | nodes.py condition_group |
| operator | `{value:"EQ", desc:"="}` 短码：EQ/NEQ/GT/LT/GE/LE | ref-and-condition-contract.md §七 |
| leftParam | `{id: "<DTO>.<字段>", type:"OBJECT", javaType, dto:"_<字段>", field, desc, dataType, multiSelect:false}` | ref-and-condition-contract.md §三 |
| selectParam | 要 position + javaType + dtoType + appName + nodeInfo；`name=outputName`（带下划线） | ref-and-condition-contract.md §一 |
| MAP_OPERATION.operationType | **字符串** `GET/PUT/REMOVE/KEYS`，**不是对象** | node-authoring-contract.md §五.5 |
| LIST_OPERATION.operationType | 对象 `{"type":"SIZE"}` | 本轮 LIVE |
| FOR | 计数循环：operator/forStep/forStart/forEnd 四项全必填，foreach 恒为 null；BREAK 必须挂在 BRANCH 下 | nodes.py for_each |
| CUSTOM_ERROR | `type:"CUSTOM_ERROR"`，**不是 "ACTIVITY"** | node-authoring-contract.md §五.5 |
| CHANGE_ENTITY | 真实必填 selectParam + title（不是 mappingType） | nodes.py change_entity |
| CREATE_VARIABLE | 真实必填 paramType + title + dataType（不是 metaDataType/otherType） | nodes.py create_variable |
| 服务节点 attrs[].attrType.id | 必须以 selectMethod.parameter.item.itemType 为前缀 | generation-gates.md G6 |
| 实体引用 | entityObject：key/entity=domain 类，id/fullName=DTO 类，**不能互换** | ref-and-condition-contract.md §十二 |
| 入参定义载体 | trigger.paramType（NONE/BASIC/ENTITY_OBJECT/DEFAULT_OBJECT），**不是顶层 input** | ref-and-condition-contract.md §十一 |

### 1.5 表达式接口（/check + /transform）

- 前端从不调 /expression/schema（对 MICROFLOW 返 BOOT_3000），直接 POST：
  - `/service/udc/expression/check` → `content:true` = 高可信校验
  - `/service/udc/expression/expression/transform` → BOOT_0000 = 结构完整
- schemas 装配：从 designData.context 转换，**每层加 `skip:true`**
- executableExpr 前缀 `93gDaq3/...=` 是**服务端固定产物**，可离线生成
- 出处：expression-layer-contract.md §六

### 1.6 三层数据模型（表达式同步机制）

| 层 | 位置 | 何时更新 |
|---|---|---|
| L1 | store.flowNodes[id].expression | 抽屉点「确定」立即写 |
| L2 | store.oldFlowSchema | 加载/保存时 |
| L3 | 后端 dataSchema | **只在「暂存草稿」/「保存并提交」时** |

- 点「确定」只写 L1，不写 L3
- 判据：UI 无红错=低可信；点验证成功=中；**后端 dataSchema 回读=唯一真判据**
- 出处：expression-layer-contract.md §一/§八

### 1.7 闸门清单（gates.py，生成期拦截）

| 闸门 | 拦什么 |
|---|---|
| G1 | tokens 数 == translation 段数（函数调用=1 段） |
| G2 | SelectParam.outputName / VARIABLE token 必须命中本流程某节点 output.name 或 _FLOW_INPUT_* |
| G3 | CREATE_ENTITY 只收 DTO；CHANGE_LIST 只收文本列表 |
| G4 | DATA_MAPPING.mappingRule 必须显式 name/caption |
| G5 | 跨应用节点 app.appName 必须在依赖清单或 inApp=true |
| G6 | 服务节点 attrs[].attrType.id 必须以 selectMethod.parameter.item.itemType 为 prefix |

### 1.8 校验接口

- 条件校验：`udcConditionCheckPost`（params0 是**条件组数组**）
- 实体选择：`udcMicroflowSearchTreeEntityPost`（返回 methodLegal 查询能力元数据）
- 条件表达式的 expression 是**形态 2**：`{title, schema}`，无 type/expression 包装
- 出处：ref-and-condition-contract.md §七/§八

### 1.9 提交契约

- GraphQL 变量名：`udcMicroflowUpdatePost` 用 `body`，不是 `p`（expression-fill-all-nodes.md §4.1）
- checkSchema 完整请求体见 ref-and-condition-contract.md §五（要 guid/publishState 等，REST body 缺这些会静默草稿）
- 读回 op：全量列表 `udcMicroflowSearch`，按 id 查详情 `udcMicroflowFindByIdGet`；`udcMicroflowServiceListPost` 查不到新草稿（本轮 LIVE 实测）

---

## 第二部分：表达式

### 2.1 五种 token

VARIABLE / OPERATOR / SYSTEM / CONSTANT / FUNCTION

### 按引用来源分两种形态（README.md §3）

| 场景 | context 根 | token.value | paramId |
|---|---|---|---|
| 字段默认值/计算值 | 实体 name（一层） | `<实体>.<字段>` | **有** |
| 规则条件 | 前序节点输出名 | `<根>.<根>.<字段>`（两层） | 无 |

### 2.3 SYSTEM 变量

- token 类型是 `SYSTEM`，schemas 可为空数组，**不受执行顺序限制**（expression-fill-all-nodes.md §3.2）
- 实测可用：system.currentUserId / currentUserName / currentUserCode / currentOrgName / currentDateTime

### 2.4 resultTypeInfo 只有 15 个合法值

```
INTEGER BIGINTEGER DECIMAL STRING MULTILINESTRING
DATETIME DATE TIME BOOLEAN CURRENCY ATTACHMENT
ARRAY ENTITY CTPENUM ENUM
```

- `OBJECT` 不在值域内（报 FORMULA_6003）
- DTO 场景用 `ENTITY` + 必须**带 resultTypeFullName**（否则 FORMULA_6901）
- 出处：expression-fill-all-nodes.md §3.3

### 2.5 类型名必须归一化

String→STRING, Long→BIGINTEGER, Object/Dto→DTO（expression-fill-all-nodes.md §3.4）

### 2.6 FUNCTION token

- value=函数英文名，subOps 是**二维数组** `[[参数组]]`
- 88 个函数清单：`core/facts/udc/expression/functions.md`（BACKEND 88 / FRONTEND 81）
- catalog：`components/udc/microflow/function_catalog.json`
- 参数是变量时必须带 `uniformityParams.paramId`

### 2.7 表达式两种包装形态

- 形态 1（值槽位）：`{type:"Expression", expression:{title, schema}, desc}`
- 形态 2（BRANCH 条件）：`{title, schema}`，无 type/expression 包装

### 2.8 executableExpr 拼接规律（LIVE 实测）

= base64 固定前缀 + token.value 拼接

- FUNCTION 递归为 `名(参数,参数)`，参数组用逗号分隔
- 出处：expression-layer-contract.md §6.4

### 2.9 值包装对象三形态

```json
{"type":"Simple","simple":0,"desc":0}              常量
{"type":"SelectParam","selectParam":{...}}          选变量
{"type":"Expression","expression":{"title","schema"}} 表达式
```

### 2.10 可表达式化判据

- 表达式只能引用**本节点之前**节点的输出（system.* 除外）
- DTO 槽位优先用自带 selectParam 构造 schemas
- `RETRIEVE_ARRAY.pageInfo` 是结构选择器，**不许表达式化**（FORMULA_6901）
- 恒等式 `x > x` 检测：len(var_tokens)==2 且相同 = 恒 false，校验能过但语义无效
- 出处：expression-fill-all-nodes.md §3.1/3.5/3.6/§五

### 2.11 悬空引用判定

拿 tokens[].value 的**第一段**比对本流程所有节点的 output.name；不在其中=悬空。
节点重建时 nodeId 保留但 output.name 换新——token 路径不会跟着变。
出处：expression-layer-contract.md §四

---

---

### 1.10 活体复刻正道（2026-10-29 LIVE 实测，取代手拼构造）

**全节点验收流程的正道 = 活体母版复刻**：

1. 母版 = `fixtures/microflow/backup/xzhAllNodesV16.schema.json`（30 节点/21 类，
   UI 逐节点「添加→确认」搭出后从后端抓回的活体，表达式自带正确 runtimeData）
2. 复刻 = schema 一字不动，只换 name/caption → GraphQL create(DRAFT) →
   checkSchema/update(RELEASE) → udcMicroflowSearch 读回
3. 验收判据（后端 check=True 只是浅校验，不算数）：
   - **后端 FindByIdGet 回读 state=RELEASE**（唯一真判据）
   - UI 编辑器 flowNodes 逐节点 `isCompleted=true`、无 noConfig 节点
   - 画布卡片全部渲染（37/37）
4. 实测结果：id=5364541617832407000，40 flowNodes 全过
5. 实现：`scratch/republish_master.py`（复刻）+ `scratch/ui_check_nodes5.py`（逐节点验证）
6. 手拼构造（上一轮 tests/test_microflow_all_nodes.py 路径）产物 UI 缺胳膊少腿，
   12 条测试流程已全部删除——**不要再用这条路做验收**

---

### 1.11 活引用解析层（2026-10-29 LIVE，解决"写死引用"问题）

复刻/构造的流程里，**外部引用必须运行时从环境拉活**，不许写死：
（上轮复刻版带死引用 xzhSubflowStub 被用户抓到——母版制作时引用还在，发布时已删）

- `components/udc/microflow/live_refs.py`（LIVE 证活）：
  - `entity()` ← udcMicroflowSearchTreeEntityPost（实体树含 methodLegal）
  - `sub_mf_candidates()` ← udcMicroflowSearch，**只收 RELEASE**（DRAFT 不可被引用）
  - `app_service_method()` ← udcMicroflowSearchMethodByNamePost
    body: `{appId, appName, dtoFullName=<方法全名>, methodFullName=<方法全名>}`
    返回 selectMethod 完整签名（含 md5/parameter/returnValue）
  - 实体属性（含 md5）← udcMicroflowFindCustomDtoPost
  - 查不到即抛 LookupError（G7 语义：拉不到就不许生成）
- 发布契约：**guid 必须从 FindByIdGet 取 DB 真值**（猜 guid → BOOT_1001 Parameter Error）；
  versionCode 必须 100（0 → 静默问题）；REST /checkSchema/update 用 create 的 15 字段 body 即可
- 条件右值是**裸形态** `{type:"CONSTANT", value:0, desc:"0"}`——
  **不是**值包装 `{"type":"Simple",...}`（混用 → BOOT_1001 无明细，是本轮最坑的一处）
- MAP_OPERATION：output 必填（非 null）；paramType=BASIC
- CREATE_MAP：generics 是对象 `{keyType, valueType}`，不是数组
- CREATE/CHANGE/DELETE_ENTITY + 批量：**output 必须完整实体 DTO 形态**（非 null）
- LIST_OPERATION.selectParam 引用实体列表时带全 DTO 键（dtoType/udcApp/appName/id/javaType/relationEntity）
- SUB_MICROFLOW.mfService 需要 path/method/hostPath
- 成果：活引用重建V2-8477 id=928266606312292632 RELEASE，25 flowNodes isCompleted 全 true，
  SUB_MICROFLOW→MFSERVICERFlOt9（活）、CALL_APP_SERVICE→FileAppService（实时签名含 md5）

---

## 使用规则

1. 生成/修复节点 → 先读 node_templates 对应模板，只替换参数
2. 表达式 → 按 §2 事实构造，构造完跑 /check + /transform 复验
3. 提交 → 按 §1.9 契约，用 udcMicroflowSearch 读回验证
4. 遇到与本文不符 → 以源文件为准并更新本文（注明出处与日期）
5. 本文件只收录经 LIVE/源文件证实的内容；新增事实必须带出处
