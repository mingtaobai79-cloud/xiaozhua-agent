# 微流程生成闸门与批量生成配方

目标：**生成即正确**。平台真正的错（`04000` / `04004`）只在
`CheckUtils.parseNodes → ActivityNode.nodeLogicCheck` 才暴露，`checkSchema` 是浅校验，
所以每条踩过的错都要在本地生成期变成可判定规则。规则不过 → 不生成、不提交。

## 1. 闸门实现位置与调用

```python
from components.udc.microflow.gates import run_gates
problems = run_gates(schema, dep_apps=<本应用依赖 appName 集合>, app_name=<appName>)
if problems:
    raise SystemExit("\n".join(problems))
```

`dep_apps` 从活体取，不要传空集：

```sql
SELECT dep_app_name FROM udc_dependent_application WHERE app_id = <appId>;
```

传空集会把 `bpm`、`boot-starter-serialnumber` 这类真实平台应用误报成 G5。

## 2. 八道闸门

| 闸门 | 平台报错（活体原文） | 判定规则 |
|---|---|---|
| G1 | `UDC_CE_MICRO_FLOW_04000 未知异常 java.util.ArrayList.rangeCheck` | `len(tokens) == 段数(translation)`；段先剥节点显示名 `名称(1).`，再按 `2*运算符数+1` 计 |
| G2 | `UDC_MICRO_FLOW_04004 前序节点发生变更请重新选择` | `SelectParam.outputName` 必须命中本流程节点 `output.name` 或 `_FLOW_INPUT_*` |
| G3 | `不是根实体对象(x)` / `不是文本类型(x)` / `对象类型不匹配(x)` | 实体写入类只收 DTO / DTO 列表；`CHANGE_LIST` 只收基础类型列表 |
| G4 | 提交门禁 `DATA_MAPPING.mappingRule 缺 'name'` | `mappingRule.name/caption` 显式写 |
| G5 | `依赖应用已删除` | 跨应用 `app.appName` ∈ 依赖清单 或 `inApp=true` |
| G6 | `必填参数未配置，请点击该节点参数设置` | `attrs[].attrType.id` 以 `selectMethod.parameter.item.itemType` 为前缀 |
| G7 | `propertyKey=pageInfo, PROPERTY_IS_REQUIRED`（节点面板同样报「必填参数未配置」） | `pageSearch=true` ⇒ `pageInfo` 必须是非空对象（指向 `com.seeyon.boot.transport.PageInfo` 的 `CREATE_VARIABLE`），`pageInfo=null` 一律拦下 |
| G8 | 与 G2 同文案的 `04004 前序节点发生变更请重新选择` | 引用必须指向**它前面**已出现的节点出参（按 nodes 数组顺序遍历，边看边往 `seen` 里加）；分页变量建在 `RETRIEVE_ARRAY` 之后就是典型触发 |

G1 的段数口径和直觉不同，按活体样本校准：`a.b+system.x` = 3 个 token；
节点显示名里的括号（`查询单条数据(1).文本字段+当前时间`）**不是**表达式语法，计段前必须用 `re.sub(r"\(\d+\)\.", ".", s)` 剥掉；
剥完仍含括号（函数调用如 `size(vList)`）时口径未证实 —— 闸门直接返回 -1 拒收，
**宁可不生成函数调用，也不要赌 token 形状**（错一个就是整条流程发不出去）。

## 3. 固定构造顺序（照做就不会出上述错）

1. 先声明上下文：`input`、变量节点、`PageInfo` 分页对象，**收集全部 `output.name`**；
2. 再建引用型节点（查询 / 服务 / 变量赋值）：所有 `SelectParam` 从已收集集合里取，**禁止手写名字**；
3. 表达式按段生成 token（VARIABLE / OPERATOR / SYSTEM / FUNCTION），段数即 token 数；
4. 跨应用服务：先确保 `udc_dependent_application` 有记录，再按 `parameter.item.itemType` 生成 `attrs`；
5. `run_gates` → 空列表才 `build_schema` / 提交；
6. 提交后仍要跑 UI「检查」（`.ant-table-body tr` 逐行看），因为 G1–G7 是本地近似，平台才是终审。

### 3.1 提交与读回：只走接口，别拿 DB 当验证通道

- 读回用 `GET /service/udc/microflow/findById/{id}`（仓库封装 `components/udc/microflow/read.py`
  的 `find_service / list_services / state_of / is_release`）；批量列表用 `list_services(appId)`。
- **不要给提交脚本加 `--db-env` 之类回读**：DB 只是取证便利，客户环境常常没有 DB 权限，
  而且「接口 0000 + DB 对上」验证的是存储层，不是平台契约。
- **发布失败是静默的**：`POST /udc/microflow/update` 传 `state=20` 常返回 `BOOT_0000 SUCCESS`，
  但流程仍停在 `DRAFT`——深度校验（04004/04007 等）不过时后端不报错，只降级保存。
  所以发布后**必须**用 `findById` 读 `state`，等于 `RELEASE` 才算成功；`update` 的返回码不能作为验收依据。
- 诊断「为什么停在 DRAFT」：拿 `findById` 回来的 `dataSchema` 打 `udcMicroflowCheckSchemaUpdatePost`，
  读 `content.check/errors/errorMessage[]`，`errorMessage[].propertyKey` 直接给出缺哪个字段。

### 3.2 微流程 name 命名规则（批量提交必踩）

`create` 的 `name` 必须是**字母数字组合、首位为字母**；带 `-` 或 `_` 会报
`UDC_ENTITY_0001 [<name>]不合法，必须使用字母和数字组合，且首位为字母`。
批量脚本里从文件名派生时先转小驼峰（`verifyPagedScan-v1` → `verifyPagedScanV1`），
`caption` 可保留中文与连字符。

### 3.3 批量产物清理（自测完就删，别留在客户应用里）

```
GraphQL mutation udcMicroflowDeletePost  {"id": "<microflowId>"}
→ {"code":"BOOT_0000","data":{"content":true}}
```

参数只有 `{id}`——传 `{ids:[...]}` 或加 `appId` 都报 BOOT_4002。逐条删、逐条复查剩余条数与残留 caption；不要只看返回码。
批量自测流程一律用统一前缀（如 `gen`），以便按前缀一次性清理。

### 3.4 全量列表必须用 udcMicroflowSearch，不要用 udcMicroflowServiceListPost

`udcMicroflowServiceListPost` 的查询硬编码 `triggerType=MANUAL`（反编译
`MicroFlowService.selectServicePageByAppId`：andEqualTo(TRIGGER_TYPE, MANUAL)），**只返回服务定义微流程**，
事件监听/定时任务永远查不到——按它清点会漏掉 2/3 的流程、按它清理会漏删。
参数里塞 `triggerType`/`state`/数字枚举都无效（服务端忽略）。
全量列表用 GraphQL `udcMicroflowSearch`（body：`{pageInfo:{pageSize:999}, params:{appId, IN_type:["SERVICE","CUSTOM"]}}`），
返回所有触发方式（content 元素含 id/name/caption/type/triggerType/state），`params.name` 是精确匹配不是 like，按前缀筛在客户端做。
发布状态清理按 `state!="RELEASE"` 判定（DRAFT 即未保存成功）。

## 4. 分页 + 双层循环的结构

```
CREATE_VARIABLE(PageInfo 自定义对象)
  → RETRIEVE_ARRAY(pageSearch=true, pageInfo=该变量)      # 第 1 页
  → LIST_OPERATION(SIZE) + 表达式算总页数
  → FOR(页)                                              # 外层
        → RETRIEVE_ARRAY(取本页数据)
        → FOR(行)                                        # 内层
              → 表达式取值 → CREATE_VARIABLE → CHANGE_VARIABLE
              → CHANGE_LIST(基础类型列表)
              → CHANGE_VARIABLE(实体字段，改循环对象)
        → 末次判定 → BREAK（BREAK 的父必须是 BRANCH，BRANCH 的 conditions[] 必须是完整 CONDITION）
  → CHANGE_BATCH_ENTITY(列表来源 = 循环前那次查询的对象)
```

- 循环外那次查询的**出参对象**才是批量更新的数据源；循环内再查会换掉来源。
- `CUSTOM_ERROR` 之后不能再挂节点（平台报「请勿在该节点后配置其他操作」），只能放分支末尾。

## 5. 批量生成（多业务 × 多变体）

- 把业务写成 `(业务名, 中文名, 业务说明, 配方, 实体)` 的表格，配方是一串离散步骤码
  （建变量 / 单条查 / 多条查 / 循环 / 插入 / 修改 / 批量更新 / 删除 / 列表 / 拆文 / 映射 / 服务 / 子流程 / 分支错误）；
- 每条按同一顺序装配，节点类型自然铺开、可重复出现；
- 每条生成后先 `validate_schema` 再 `run_gates`，两条都 0 才落盘；
- 交付目录含 `INDEX.md`（业务说明 / 节点数 / **逐条列出真实节点类型清单** / 两条校验的问题数）与 `COVERAGE.md`（节点类型出现次数，**递归统计**循环/分支内嵌节点）；
  只给「类型数」不给类型名等于没给——用户看索引就是要判断“这条用了哪些节点”；
- 生成失败时改**配方与构造器**，不要改已生成的 schema；批量推送后逐条核对接口读回的 `state`，统计 RELEASE / DRAFT 数量并把未发布原因（`errorMessage[].propertyKey`）写进索引。

## 6. 反例

- ❌ 整节点搬用别的流程的 `CALL_APP_SERVICE`（attrs 留着源流程变量名）→ G2 必炸；只有 `selectMethod` / `output`（含 `id`）可复制。
- ❌ 拼串表达式 translation 写 3 段却只给 1 个 token（或反之）→ G1 必炸。
- ❌ 实体列表 assert 给 `CHANGE_LIST`、文本变量 assert 给实体写入节点 → G3 必炸。
- ❌ 生成完再写脚本补字段/改引用 —— 同一类错下次还会出现，必须回改构造器。

## 7. SERVICE 类型 endNode.value 必填（区别于 CUSTOM）

反编译 `MicroFlowOutputValueBo.parse`：`type=SERVICE` 时 `buildAttrValue("value", endNode, ..., required=true)`——
标准微流程的结束节点**必须带 `value`**（出参取值），缺了报 `[root]:必填参数未配置`；`type=CUSTOM` 时 `check()` 直接 return，
value 可空。标准流程 BASIC 出参的 value 用 SelectParam 引用前序变量出参：

```jsonc
"endNode": {..., "output": {BASIC 出参},
  "value": {"type":"SelectParam", "selectParam": basic_select_param(
      <前序变量节点 output.name>, "处理结果", "STRING", <节点id>, <actionType>)}, "desc": "处理结果"}
```

CUSTOM 微流程（无节点）endNode 不写 value。诊断技巧：同一构造器批量生成时 CUSTOM 全过、SERVICE 报 `[root]`，
对比成功/失败样本的 `endNode.value`（findById 读 dataSchema）即可锁定。

## 8. 定时任务周期的合法值域（rotationType ≠ ScheduleUnitEnum）

`scheduleCronRule.cronRules[].rotationType` 的合法值只有 **DAY/HOUR/MINUTE**（反编译
`RotationTypeEnum`——只有这三个枚举项）。写 WEEK/MONTH 不会报错文案，而是 `checkSchema` 返回
`check=null, errors=null`（解析器反序列化失败静默拒绝）且 update 后 state 静默停在 DRAFT——
看起来像偶发时序问题，实际是值域非法，重试永远失败。
注意别混淆：`ScheduleUnitEnum`（HOUR/MINUTE/DAY/WEEK/MONTH/YEAR/SIMPLE）是另一层单位枚举，
它的 WEEK/MONTH **不能**填进 rotationType。「每周/每月」要么用 CRON 类 cycleType 表达，要么换算成 DAY。
checkSchema 返回 `check=null`（连 check 布尔都没有）时优先怀疑枚举值非法，不要先归咎于时序重试。

## 9. 批量形制的用户验收标准（每轮重生成前先对齐）

- **出入参一律对象类型**（ENTITY_OBJECT 实体 / DEFAULT_OBJECT 自定义 DTO），不要 BASIC——除非用户当轮明说允许。
- 事件监听三种来源都要覆盖：应用内实体事件 + 应用内微流程事件（messageSource=MICRO_FLOW_EVENT）+ 应用间 MQ（MESSAGE 源，必填 topic）。
- 定时任务周期类型要轮换，且只能从 DAY/HOUR/MINUTE 里轮换（见 §8）。
- 服务节点（CALL_APP_SERVICE）参数必须填真实值（常量或引用），事件投递（PUBLISH_BUSINESS_EVENT）必须做映射——空 attrs/空参数算空壳。整对象引用用 `mappingType:"value"` + SelectParam 引前序实体节点（反编译 `BusinessEventActivity.parseMappingType`：value→buildAttrValue、attrs→buildSelectObjectAttrs）。
- ENTITY_OBJECT 入参的 entityObject 与 DEFAULT_OBJECT 的 defaultObject 结构从历史成功样本或 `udcMicroflowSearchTreeEntityPost`/`udcMicroflowSearchNonEntityDtoPost` 取，禁止手拼（字段见 §出参定义；defaultObject 的 fullName=DTO、标识用 dtoId）。
- 无节点（CUSTOM）流程的出参来源：endNode.value 用 SelectParam `position:"root"` 引 trigger.output 的入参名。
- 每轮交付前用 findById 全量读回逐条核对（state=RELEASE、trigger.output.desc=出参名、cronRules 合法、出入参 dataType=DTO），问题项列清单；update 后 checkSchema 空返回属时序，同 body 重试（sleep 1s ×3）后仍 DRAFT 的，用读回 schema 重发一次 update。
