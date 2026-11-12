# 微流程 100% 可生成化 —— 全量事实补充 + 逐节点细节落实方案（v1）

> 用户指令：不要暂停；出方案；开定时按方案推进+审计验收；目标=微流程+业务 100% 生成一个位置不错。
> 2026-10-16 起。

## 0. 用户截图点名的遗留问题

| # | 截图证据 | 问题 | 状态 |
|---|---|---|---|
| 1 | 数据转换→映射关系配置弹窗全空 | mappingRows 有 3 行但弹窗显示空——落库字段与弹窗读取字段不一致 | P1 待办 |
| 2 | 插入数据 红字"所选…实验文本已变更" | 面板红字已清（0）✅ | **已解决** |
| 3 | 事件投递 "可投递的事件已失效" | **已解决**：根因=候选池为空（本应用 `udc_data_transfer_object` source=4/5 行数=0）；修复=先经 `udcDataTransferObjectCreateDtoPost` 建事件对象（source=MICRO_FLOW_EVENT+`attributes:[]`）→ 候选池非空→红字=0 | **已解决** |
| 4 | 创建映射组 "预制对象" | CREATE_MAP 的 entries 需按预制形态配置 | P1 待办 |
| 5 | 自定义服务 参数区 | selectById 的 attrs=0 入参没赋值；需抓"选择服务"参数区加载契约 | P1 待办 |
| 6 | 表达式 | paramType 枚举=ENTITY / ATTRIBUTE_SCOPE / CONFIG_PARAM；`extension.filterFieldIds`；131 系统变量 + 39 应用参数已落盘 | **进行中** |

## 0.1 本轮（2026-10-16）实绩

**A. 事件投递节点真相闭环（LIVE+CFR 双证）**
- 抓包定位面板加载契约：`udcMicroflowSearchEventListPost` + `udcMicroflowFindCustomDtoPost`（批量 graphqlLoader）
- CFR 定位候选池过滤器：`MicroFlowMetaDataQueryService.searchMicroFlowEventByAppName` → DTO metadata `customs.source == MICRO_FLOW_EVENT`
- MySQL 定位根因：本应用 `source IN (4,5)` DTO = **0 行** ⇒ 候选池天然为空
- 修复：`udcDataTransferObjectCreateDtoPost {appId, appName, name, caption, source:"MICRO_FLOW_EVENT", description, attributes:[]}` → 返回 `fullName=com.seeyon.<app>.dto.microflow.event.XzhEvtA1`
- 验证：候选池 n=1；真机面板红字 4 节点全 0
- 证据：`core/facts/udc/write-chain/microflow-publish-event-candidates.md`

**B. 表达式域（P2 提前启动，权威数据已入库）**
- `udcExpressionSystemVariableListGet`：**131 项系统变量**（organization 95 / date 33 / env 2 / plugin 1）→ `docs/audit/artifacts/udc-expression-system-variables.json`
- `udcExpressionSchemaPost`：paramType=ENTITY（返回实体属性树）/ ATTRIBUTE_SCOPE / CONFIG_PARAM（**39 应用参数**）→ `udc-expression-schema-full.json`、`udc-expression-schema-paramtypes.json`
- 表达式配置契约（bundle 权威）：`{serverName:"udc", title, resultType, propsInfo:{appId, moduleName, paramType, resultTypeInfo}, serverParams:{appId, idsStr, paramType, extension, upsource}}`
- 分支条件表达式：`paramType=ENTITY`，页面规则（FRONTEND）时 `unLoadPresetSchema:["APP_PARAM"]`
- op 名（bundle 挖）：`udcExpressionSchemaPost` / `udcExpressionSystemVariableListGet` / `udcFunctionSelectFunctionTreePost` / `udcFunctionUpdatePost` / `udcFunctionCopyPost` / `udcFunctionBatchDeletePost` / `udcFunctionUpdateFunctionReferPost`

## P1 逐节点细节落实（每节点交付四件套）
对 19 个节点逐个做：**①接口抓包**（刷新页面捕捉该节点面板加载时的全部 /service/udc 请求）→ **②契约落盘**（请求/响应 JSON 存 evidence）→ **③按契约重组节点**（不猜）→ **④真机面板复验**（红字=0 + 必填非空 + 值语义正确）。

节点清单（19）：CREATE_VARIABLE / RETRIEVE / RETRIEVE_ARRAY / CREATE_LIST / CHANGE_LIST / LIST_OPERATION / CREATE_MAP / MAP_OPERATION / DATA_MAPPING / CHANGE_VARIABLE / CHANGE_ENTITY / CHANGE_BATCH_ENTITY / CREATE_ENTITY / DELETE_ENTITY / CONVERT_DATA / SUB_MICROFLOW / CALL_APP_SERVICE / PUBLISH_BUSINESS_EVENT / BRANCH

重点先行（用户点名）：
1. **事件投递**：先查"对象定义-应用内事件对象"真实清单（udcMicroflowListEvents / 事件对象 REST），若空则**先建事件对象**再投递——事件名不能编。
2. **自定义服务**：入参 attrs 必须配（抓"选择服务"后面板加载参数区的接口）。
3. **数据转换**：抓"映射关系配置"弹窗打开时的加载接口，对照 mappingRows 为何不显示。
4. **插入数据**：红字根因查证——检查 runAfter 链与上游产出顺序。

## P2 表达式域（横切，单独成册）
- 8 类函数逐一取全（面板"函数"树抓取 + 每个函数的说明/示例落盘）
- tokens 结构（uid/type/value/subOps/desc）+ executableExpr 编码规则
- 系统变量全集（组织机构/日期/环境变量/插件）+ 应用参数
- 交付物：`references/udc-expression-functions.md` + 组装器校验用例

## P3 其余微流程类型（监听/定时/自定义/实体规则）
- 事件监听（triggerType=BUSINESS_EVENT）、定时（SCHEDULE+scheduleCronRule）、REST（openApi）、页面规则（type=1 已做过）、实体规则（type=2 未碰）
- 每类建 1 条样板 + 四件套验证

## P4 实体/应用域收尾
- 实体应用：实体 CRUD、属性组、枚举、参照——此前已有大量事实，收口成 checklist

## 执行机制（用户要求：定时推进 + 审计验收）
- cron 定时任务按周期推进 P1→P2→P3→P4，每个节点完成即落盘证据（`docs/audit/artifacts/udc-node-evidence/<node>.json`）
- 验收口径（固化）：**每节点四件套齐 = 过**；红字=0 只是入场券
- 全部事实进 seeyon-agent：facts/write-chain + skill references

## 验收定义（用户原话转译）
"微流程加业务能 100% 生成一个位置不错" = 给任意节点类型清单，能按固化规则组装出 checkSchema 过 + 面板零红字 + 必填全配 + 语义自洽 + 长ID可溯源 的 dataSchema，且全程有接口证据支撑。
