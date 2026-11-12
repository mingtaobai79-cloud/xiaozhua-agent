# UDC 语义理解检查点

> ✅ **P6 裁决（2026-11-07）：保留原地，不移动、不删除。**
> 本文件是 2026-10-11 的理解检查点快照（前端机制 / 页面保存链 / 能力矩阵），
> 数字与结论属当时时点，**未随之后 20+ 轮更新**。当前状态见 `docs/audit/udc-semantics/PROGRESS.md`。
> 保留理由：§3「已确认的前端真实机制」与 §4「页面保存/构建链」是全仓**唯一**系统性叙述——
> `core/facts/udc/write-chain/` 有保存协议（`designer-save-protocol.md`）与 page-schema 形状
> （`page-schema-protocol.md`），但**没有** UdcForm / UdcSubPage / UdcReference / UdcPanel
> 的组件语义与 `buildin|widget|microflow|enevtThrow` 动作枚举。零代码读取、零正文引用，
> 但内容无替代，删掉即断。已登记于 `docs/audit/README.md` 第六节。

日期：2026-10-11
主线仓库：`<SEEYON_AGENT_ROOT>`
审计边界：只读；本轮不执行 test2 设计态写入、不改页面、不改微流程、不触发构建。

## 1. 先定性：主线项目与 Hermes Skill 的关系

`seeyon-agent` 是主线实现。Hermes 下的 `seeyon-*` skill 是操作规程、证据规则和环境笔记，不等于 `seeyon-agent` 已经实现对应能力。

当前仓库的真实宿主入口是 `seeyon_host_bootstrap.py`：

- `bootstrap()` 装配 `udc`、`runtime`、`integration` 三个组件；见 `seeyon_host_bootstrap.py:25-40`。
- `generate()` / `generate_from_requirement()` 生成声明级 Java skeleton 和页面定义骨架；见 `seeyon_host_bootstrap.py:46-92`。
- `live_probe()` 是显式允许网络后的只读探测；见 `seeyon_host_bootstrap.py:94-116`。
- `deploy_plan()` 只输出方案数据，写操作由宿主执行；见 `seeyon_host_bootstrap.py:118-130`。
- 返回能力表明确 `readonly_only=True`、`credential_mode=path-ref-only`；见 `seeyon_host_bootstrap.py:136-149`。

`components/udc/component.py:14-98` 也明确：UDC 组件是 read-only，`dry_run` 不执行写入。`components/platform_operations/layer.py:17-24` 对非只读 GET 契约统一返回 `DENIED`。

因此，当前项目不是“已经能按自然语言自动搭完整 UDC 应用”的实现；它是“证据目录 + 只读审计 + 方案生成 + 宿主适配”的第一阶段能力。

## 2. 用户需求拆成可验收对象

用户提出的目标不是一条操作，而是以下对象链：

1. 应用/实体：订单实体，订单信息、人员多选、流程关联等字段。
2. 字段语义：数据类型、人员多选、枚举、参照、默认值、可搜索、必填、字段集、索引。
3. 页面：列表页、详情页、菜单入口、页面标题/文字标签、列宽、搜索、导入导出、编辑/删除/新增。
4. 页面组件：表单、表格、过滤器、工具栏、面板、子页面、外框；每个组件有注册 schema、属性、数据源和事件。
5. 页面事件：按钮事件、行事件、控件动作、内置动作、微流程动作、页面规则入口。
6. 微流程：服务定义、事件监听、定时任务、页面规则/子规则、实体规则；节点包括查询、转换、集合操作、生单、修改、删除、调用服务、调用子微流程、数据流等。
7. 运行链：设计态 JSON 保存 → 后端反序列化/校验 → 元数据/版本 → 构建生成物 → 运行态注册 → 调用与回读。
8. 验收链：每个对象必须有设计态回读、必要时构建记录/生成物回读、运行态回读；HTTP 200 或 `BOOT_0000` 不能单独算 PASS。

这些对象不能混成一个“页面 JSON”或一个“微流程 JSON”。页面过滤方案、页面规则微流程、实体规则、事件、索引、字段集属于不同数据模型。

## 3. 已确认的前端真实机制

证据来源：`core/facts/udc/frontend-assembly-protocol.md`、前端 chunk `<EVIDENCE_ROOT>/seeyon-customer-evidence/frontend/chunks/src_redux_store_ts.14dc061e.js` 及页面设计 bundle 的模块切片。

### 3.1 控件不是数据库字典，也不是我可以随意发明的 JSON

前端启动时将控件实现和 schema 合并注册：

```text
m.hG.init({
  pcControls: s._,
  pcSchemas: {...d.O, ...window.SeeyonUISchema},
  mobileControls: s.L,
  mobileSchemas: {...d.n, ...window.SeeyonMUISchema}
})
```

`getControlSchema(type, terminal)` 从 schema cache 取组件定义；自定义控件还会按 package、copVersion、schemaModule 通过 dynamic import 加载。

因此有三层来源：

- 内置/标品 schema：设计器 bundle 注册表。
- 自定义控件 schema：应用/宿主提供的 remote entry 或 package 动态加载。
- 页面实例：拖拽实例化后才写入 `udc_page_schema.page_schema` / `draft_page_schema`。

当前 `seeyon-agent` 没有实现 bundle schema 解析器，也没有实现组件注册表到页面实例的构造器。`components/construction/page_definition.py` 只输出 18 个页面元数据字段的声明级骨架，不能生成可运行的 `childById` 控件树。

### 3.2 页面 JSON 的基本形状

页面实例是 `PAGE → children → childById` 树。控件节点至少涉及：

```text
id / type / parentId / settings / dataSource / events /
uiModel / uiModelSchema / children / extraChildren
```

`dataSource` 在控件顶层，不在 `settings` 内。实体列表数据源至少要有：

```text
type / subType / key / isRoot / isRef / dataShape /
entity / fields / dataTarget / fieldBindMap / hiddenFields
```

网格列不是简单的 `dataIndex + width`；标品列包含 `componentName`、`title`、`hide`、`sorter`、`headerAlign`、`uiModel`、`dateFormat`、`autoGrow` 等大量键。当前项目没有页面 schema validator，也没有标品控件 deep-copy + 字段替换的正式 builder。

### 3.3 已确认的组件语义

前端 schema 中已看到的真实组件定义：

- `UdcForm`：单一记录表单，`dataSource.dataShape="SINGLE"`，控制动作有 `create/edit/view/delete`；基础设置包含实体数据源和条件查询。
- `UdcSubPage`：子页面，控制动作是 `switch`；属性包含高度、关联子页面、激活规则、自动触发激活规则。它不是普通容器，也不是随便放一个 panel 就等于子页面。
- `UdcReference`：参照类组件，实际由字段数据类型和 `relationEntity/relationApp/relationType` 决定可用 schema。
- 人员选择使用平台注册的 `UiBusinessSelectPeople`，不是一个自定义的 `UserSelect` 字符串类型。
- 数据列表/表格组件包括 `UdcDataGridView` 等；事件有单元格点击、标题点击、列图标事件等动态事件。
- `UdcPanel` 的打开/关闭是控件动作 `CONTROL` + `targetAction=panel_openPanel/panel_closePanel`，前端代码确实有这两个动作；“显示弹窗”不能用一个不存在的 Modal 控件名代替。

当前项目没有把上述组件 schema、属性约束、动作枚举、数据源容器约束正式纳入代码能力。

### 3.4 事件动作真实枚举

前端动作类型是：

```text
buildin | widget | microflow | enevtThrow
```

常见动作名包括：

```text
OPEN_PAGE
ENTITY_SAVE
ENTITY_DELETE
CALL_MICRO_FLOW
CONVERT_DATA
CREATE_LIST
CREATE_VARIABLE
RETRIEVE
CHANGE_ENTITY
MESSAGE_INFO
EVENT_THROW
```

页面事件挂在具体控件 `childById[controlId].events[]`，`eventType` 必须是触发控件/按钮的 id。顶层 `eventDefine` 只是元数据登记，不能替代实际事件绑定。

前面临时页面 JSON 的 `ENTITY_EDIT`、错误的控件类型、未绑定按钮、把页面规则当作过滤方案，均不能进入主线实现。

## 4. 已确认的页面保存/构建链

### 4.1 页面保存

前端 store 里真实 mutation：

```text
savePageDraf($body: udcPageInfoUpdateDrafPostInputBody)
  → udcPageInfoUpdateDrafPost

submitPage($body: udcPageInfoUpdatePostInputBody)
  → udcPageInfoUpdatePost
```

页面基础字段、实体绑定、事件/参数、布局和 `pageSchema: JSON.stringify(pageSchema)` 一起提交。当前项目有保存协议文档，但没有把这个协议实现成页面构造、schema 校验和回读 verifier。

### 4.2 页面规则不是列表过滤方案

前端创建类型映射已确认：

```text
frontend              → type=FRONTEND, triggerType=MANUAL, caption=页面规则
frontendparam         → type=FRONTEND_PARAM, triggerType=FRONTEND_PARAM, caption=子规则
frontendfunction      → type=FUNCTION, triggerType=MANUAL, caption=公共页面规则
entityrule            → type=ENTITYRULE, triggerType=MANUAL, caption=实体规则
```

因此：

- `udc_filter_plan` 是列表/表格的查询过滤方案。
- 页面规则是 `FRONTEND` 类型微流程/规则入口。
- 实体规则是 `ENTITYRULE` 类型对象。
- `udc_event` 是事件定义，监听动作要由事件监听微流程的 trigger/messageInfo 绑定。

之前把 `udc_filter_plan` 叫作“页面规则”是错误分类，必须更正。

### 4.3 构建与上线不是一回事

前端 store 的真实调用：

```text
udcRuntimeDeployNormalPost
  params: { deployDto: e }

udcDeploymentAppOnlineNewPost
  params: {...e, deployType: "ON_ONLINE"}
```

前者是构建/部署链，后者是上线/ON_ONLINE 链。前面用 `app-online-new` 触发 TEST 并不能证明用户在页面上点击了“构建”按钮；也不能把它叫作页面构建。页面按钮的真实 Network 请求还需要 CDP 抓包核对后才可声明“页面按钮等价”。

## 5. 当前微流程理解边界

微流程完整源码审计报告现已补充：`docs/audit/udc-semantics/microflow-source-audit.md`。该报告提供旧源码 `MicroFlowNodeTypeEnum`、`ActivityNodeTypeEnum`、各 Activity parser 输入字段/输出变量语义、`checkSchema` Controller 到 `MicroFlowService.checkSchema` 的直接调用链，以及 5.3.517 jar 模板清单。它仍然是静态机制审计，不等于目标 test2 应用的微流程完整构建和运行验证。

当前已能逐类解释静态 parser 的输入和 output/NodeInfo 槽位；DataFlow/Deduction 与 Excel 的保存、生成、触发、输入输出和异步副作用契约已补充到 `flow-excel-source-audit.md`、`flow-excel-contracts.json`。目标应用的版本绑定、生成物和运行回读仍未验证。

已确认的前端类型映射：

```text
servicedefinition      → SERVICE + MANUAL
customServicedefinition→ CUSTOM + MANUAL
eventmonitor           → SERVICE + BUSINESS_EVENT
timingtask             → SERVICE + SCHEDULE
frontend               → FRONTEND + MANUAL（页面规则）
frontendparam          → FRONTEND_PARAM（子规则）
entityrule             → ENTITYRULE + MANUAL
customEventmonitor     → CUSTOM + BUSINESS_EVENT
customTimingtask       → CUSTOM + SCHEDULE
```

已确认的动作节点候选：

```text
OPEN_PAGE / CREATE_LIST_FRONT / CREATE_VARIABLE_FRONT /
CALL_FRONT_FLOW / CONVERT_DATA / FOR_EACH / CREATE_VARIABLE /
CREATE_LIST / CREATE_MAP / MAP_OPERATION / RETRIEVE /
RETRIEVE_ARRAY / LIST_OPERATION / CREATE_ENTITY /
CREATE_BATCH_ENTITY / CHANGE_ENTITY / CHANGE_BATCH_ENTITY /
DELETE_ENTITY / CALL_APP_SERVICE / SUB_MICROFLOW /
CALL_DATA_FLOW / DATA_MAPPING
```

`dataSchema` 是 JSON 字符串；平台后端需要将它反序列化为微流程 BO/节点结构，再根据 actionType 找到解析器/Activity。平台 5.3.517 `udc-biz` jar 中存在真实后端模板，例如：

```text
autocode/JAVA/2.7/templates/microflow/RetrieveActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/ConvertDataActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/CreateEntityActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/ChangeEntityActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/BusinessEventActivity.java.ftl
autocode/JAVA/2.7/templates/microflow/event/BusinessEventListener.java.ftl
autocode/JAVA/2.7/templates/microflow/schedule/MicroFlowSchedule.java.ftl
```

这说明节点不是任意 JSON；必须同时满足：

1. 前端节点 schema/参数约束；
2. `checkSchema` 的节点校验；
3. 后端 `NodeParser`/Activity 解析；
4. 对应代码模板存在；
5. 微流程发布态/构建态条件满足；
6. 生成类、运行入口和实际业务回读闭环。

当前 `seeyon-agent` 没有实现上述 JSON 解析、节点合法性校验、模板映射、参数/输入输出图校验或微流程构造器。因此前面临时拼的 `RETRIEVE + CONVERT_DATA + CREATE_VARIABLE` 只能算一次平台 API 探针，不能算“订单人员、流程信息、流转日志、意见列表已经实现”。尤其“流转日志和意见列表拼接”没有真实 CALL_APP_SERVICE/CALL_MICRO_FLOW/数据流契约和回读证据。

## 6. 当前项目能力矩阵

| 能力 | 当前 seeyon-agent 状态 | 证据 | 结论 |
|---|---|---|---|
| UDC 只读事实/报告 | 已有 | `components/udc/component.py` | 可用，属于审计能力 |
| 需求解析 | 已有但确定性 | `components/construction/requirement_parser.py` | 只生成模型，不搭建 |
| Java skeleton | 已有 | `components/construction/skeleton.py` | 声明级骨架，不是平台代码生成 |
| 页面定义骨架 | 已有 | `components/construction/page_definition.py` | 只填有限元数据字段，非 pageSchema builder |
| 组件 schema 注册 | 缺失 | 前端 `getControlSchema` 在 bundle，项目无等价实现 | 未实现 |
| 页面 childById 构造 | 缺失 | 项目只有协议/事实文档 | 未实现 |
| 页面 schema 校验 | 缺失 | 无组件级 validator | 未实现 |
| 页面规则 builder | 缺失 | 只有 filter/metadata 证据，未有 frontend microflow builder | 未实现 |
| 页面事件 builder | 缺失 | 没有 `events[]` 结构化 builder/verifier | 未实现 |
| 菜单/function tree 操作 | 只读/证据 | 前端存在 `udcFunctionSelectFunctionTreePost` 查询 | 创建/绑定未形成项目能力 |
| 子页面/外框 | 缺失 | 前端 schema 中 `UdcSubPage` 与 layout 字段已发现 | 未实现 |
| 微流程 dataSchema builder | 缺失 | `components/udc` 未提供 | 未实现 |
| 节点 schema/模板映射 | 缺失 | 真实模板在 udc-biz jar，项目无映射层 | 未实现 |
| deploy plan | 已有 | `components/platform_operations/deployment.py` | 只覆盖实体、属性、页面占位、deploy；不覆盖完整页面/微流程/菜单 |
| 写操作执行器 | 明确禁止 | `layer.py:23-24` | 写门 DENIED，不应伪装已搭建 |
| 真实页面按钮构建验证 | 未实现 | 仅有前端请求静态证据，未有 CDP Network 证据 | UNVERIFIED |

## 7. 本轮结论

当前可以确认“Seeyon Agent 已具备 UDC 证据与方案生成骨架”，不能确认“Seeyon Agent 已经理解并能自动搭建用户要求的完整订单应用”。

下一步不是继续在 test2 里试写 JSON，而是按主线补实现：

1. 先把前端组件注册表、页面实例 schema、组件属性和事件动作抽成版本化模型；
2. 再把实体/字段/参照/枚举/默认值/索引/字段集/事件/过滤方案/页面规则分别建模；
3. 再把微流程类型、节点输入输出、解析器和模板映射建立成可校验的 graph；
4. 再接页面保存/微流程保存/菜单查询等操作契约；
5. 最后才做宿主执行、页面按钮构建抓包和完整回读。

任何未经过上述模型校验、平台真实回读和构建产物验证的 JSON，都只能标记为 `UNVERIFIED_PROBE`，不能作为搭建结果。
