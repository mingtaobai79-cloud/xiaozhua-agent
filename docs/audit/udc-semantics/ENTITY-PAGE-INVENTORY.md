# 实体页面功能盘点（6 tab × 功能 × 接口 × 权限 × 边界）

> 日期：2026-10-12 | 主线：`<SEEYON_AGENT_ROOT>` | 本轮只读，无 test2 写入
> 触发：用户提供 11 张实体页面截图 + 表达式接口真实报文，指示「弄通实体那个页面所有功能，不着急联通……权限、边界都没弄清楚」
> 证据分级沿用仓内约定：LIVE / VERIFIED_STATIC_SOURCE / STATIC（前端 bundle/javap）/ UNVERIFIED / BLOCKED

---

## 0. 已有证据先读（别重复挖）

| 文档 | 覆盖 | 位置 |
|---|---|---|
| **`entity-settings-source-audit.md`**（315 行） | 字段创建 12 步链、字段校验规则、**默认值三机制**、多选人员四要件、索引=实体加载一部分、字段集走 AttributeGroup、**实体规则三类型**、事件 REST、枚举/Excel 边界、扣减独立对象、主线缺口 7 条、证据等级表 | `docs/audit/udc-semantics/` 同目录 |
| `UDC-MAINLINE-AUDIT.md` | 搭建语义总审计：页面/页面规则/过滤方案/实体规则的区分 | 同目录 |
| `SETTINGS-TABS-CALLCHAIN.md` | 设置模块 13 tab 五段链 + tab 定义对象法 | 同目录 |
| `docs/audit/artifacts/`（**23 个 artifact javap**） | udc-web/entity/page/menu/flow/runtime/common/bi/resource/publish 等 5.3.517 全景——**本轮只用了 udc-web 一个，其余待查** | |

---

## 1. 页面结构（STATIC：截图 + 前端 bundle）

### 1.1 顶部 6 tab（图 8/17 逐字确认）

`基本` `字段` `规则` `参照` `事件` `索引`

### 1.2 左侧模块菜单 15 项（chunk：`app-style-designer-...f96d7e03-88040.js`，数组 `let _=[...]`）

| 菜单 | identityCAF（i18n key） | type | path |
|---|---|---|---|
| 应用 | `layout_left.menus.form_basic_info` | formBasicInfo | `/app-design/basic-info` |
| 基本信息 | `layout_left.menus.basic_info` | basicInfo | `/app-design/app-basic-info` |
| **实体** | **`layout_left.menus.entity`**（常量 `MENUS_ENTITY`） | entity | **`/app-design/entity`** |
| 菜单 | `layout_left.menus.function_design` | functionDesign | `/app-design/page-manage/functions` |
| 页面 | `layout_left.menus.page_design` | pageDesign | `/app-design/page-manage` |
| 外框 | `layout_left.menus.page_frame` | pageFrame | `/app-design/pageFrame` |
| 参数 | `layout_left.menus.third_form_param` | thirdFormParam | `/app-design/third-form-param` |
| 规则 | `layout_left.menus.rule` | rule | `/app-design/rule` |
| 流程 | `layout_left.menus.workflow` | workFlow | `/app-design/flow` |
| BI | `layout_left.menus.analytic_statistics` | analyticStatistics | `/app-design/analytic-statistics` |
| 栏目 | `layout_left.menus.portlet` | portlet | `/app-design/page-manage/portlet` |
| RPA | `layout_left.menus.cip_rpa` | rpa | `/app-design/cip-rpa` |
| 设置 | `layout_left.menus.basic_setting` | basicSetting | `/app-design/basic-setting` |
| 高级设置 | `layout_left.menus.advance_setting` | advanceSetting | `/app-design/advance-setting` |
| 角色权限 | **`layout_left.tools.role_permission`**（常量 `TOOLS_ROLE_PERMISSION`，非 MENUS_ 前缀） | rolePermission | `/app-design/role-permission` |

**CAF 权限模型（本轮修正）**：前端持有的 `identityCAF` 是**国际文案 key**（`layout_left.menus.<key>`），不是硬编码权限字符串；真值在平台 CAF 服务端按 key 解析。→ 要拿"谁能看到实体菜单"的权限值，得查 CAF 资源配置（DB/Nacos），**不是读前端 bundle**。UNVERIFIED。

### 1.3 Route 表 39 条（同 chunk，`<p.Route title path component>`）

实体域相关：

| title | path | comp | 说明 |
|---|---|---|---|
| **实体** | `/app-design/entity` | **k** | **主实体页面（菜单入口，6 tab）** |
| 实体 | `/app-design/entity-modeling` | w | 另一实体路由（并存，关系 UNVERIFIED） |
| 实体 | `/app-design/entity-enum` | S | 实体枚举 |
| 实体 | `/app-design/enum-manger/field/:id` | A | 枚举项 |
| 实体扩展 | `/app-design/entity/custom-extension/:id` | I | 扩展实体 |
| **实体规则** | `/app-design/entity-rule`（+ `/snapshot`） | **G** | **实体规则有独立路由**（≠ 字段 defaultValue） |
| 页面规则 | `/app-design/page-rule`（+ create/editor/snapshot） | z | |
| 公共页面规则 | `/app-design/pagerules` | U | |
| 规则 | `/app-design/rule` | P | 规则模块首页（含 microflow/dataflow/deductflow） |
| 微流程 | `/app-design/microflow` | F | |

其余：页面/菜单/外框/栏目/子页面/主题/页面设计/流程/BI/日志(+详情)/角色权限/设置(+ :id)/RPA/业务规则/配置参数/四类快照。

**component → chunk 绑定（2026-10-12 补齐，经 route chunk 的 lazy 定义解析）**：route 表 chunk = `src_components_app-design_app_components_theme_app-style-designer-model_tsx-src_components_ap-7042b6.<hash>.js`（575KB，含 42 个 `<Route>`），各 component 是 `i().lazy(()=>Promise.all([l.e("chunkA"), l.e("chunkB")...]))`：

| comp | route | lazy chunk 列表（关键件） |
|---|---|---|
| **k** | `/app-design/entity` **实体页面** | 11 chunks：icon-library / lodash-fp-get / immutability-helper+image-selector / antd-tree+lodash / **`data-source-container_entity-select_use-relation-entiti`** / page-params+page-selector / page-frame copy-actions / component-select+navbar-create / **`operate-list_operateCmp`** / **`style-selector`** / **`entity-collections`** |
| w | `/app-design/entity-modeling` | entity-fieldset + data-type instance_switch+parent-entity |
| I | `/app-design/entity/custom-extension/:id` | custom-extension + page-manage_main(+page-frame) |
| S | `/app-design/entity-enum` | entity-collections + enum-manger_enum-field |
| A | `/app-design/enum-manger/field/:id` | enum-field + custom-extension + page-manage_main |
| **G** | **`/app-design/entity-rule`（实体规则）** | **`src_pages_app-design_rule_microflow_entity-rule_tsx`** + page-content |
| P | `/app-design/rule` | rule_index + rule_microflow_index + **rule_microflow_entity-rule** + dataflow_relation-graph + biz-udc-graph |
| z | `/app-design/page-rule` | rule_microflow_page-rule + entity-select |
| M | `/app-design/basic-setting` | 9 chunks（basic-setting + parameter-definition + extension-plan + template-manage + cip-rpa + biz-basic-data/excel…） |
| _ | `/app-design/page-manage` + `…/functions` | page-manage_main(+page-frame+sub-page) |
| N | `/app-design/pageFrame` | page-manage_main_page-frame(+sub-page+snapshot) |
| T | `/app-design/flow` | flow_FlowEntry + entity-fieldset |
| h | `/app-design/parameter-definition` | parameter-definition(+edit-model) + business-rules + app-home |
| B | `/app-design/role-permission` | role-permission + icon-library |
| x | `/app-design/basic-info` / `app-basic-info` | basic-info + semver + flow_FlowEntry + entity-fieldset |

**跳转带 tab**：路由跳转 `t.push({pathname:"/app-design/entity", state:{entityId, tab}})`；type→tab key 映射 `ei={attribute:"attributeSet", rule:"rule", refer:"refer", event:"event", relation:"relation", index:"index", data:"data", basic:"basicInfo"}`；规则跳转 `/app-design/entity-rule/editor/{id}`；DTO 跳 `basic-setting` + `state:{key:"objectDefinition"}`。

---

## 2. 六个 tab：功能 × 接口 × 后端 × 权限

op 权威源 = **主 store chunk `src_redux_store_ts.14dc061e.js`（2.45MB，在 `scratch/udc-pod-chunks/`），791 个 `udc*` op**。
后端 = `docs/audit/artifacts/udc-web-5.3.517-javap/_full_api_map.json`（54 controller）。

### 2.0 tab → op 域映射（逐按钮绑定的实质层，2026-10-12 补齐）

tab 组件模块 id（自 259KB `style-selector` chunk 的 require 解出）→ 该 tab 的 op 域（op 名前缀即功能域，主 store 791 op 分组）：

| tab | 组件模块 | op 域（主 store 计数） | 关键 op |
|---|---|---|---|
| `attributeSet` 字段 | `c.A` ← **`c=l(48998)`**（`66835` 是 CAF 转发模块，**旧记录错**） | `udcEntityAttribute*`（CRUD/Batch/Transfer/Preset）+ `udcEntityAttributeGroup*` + `udcAttributeGroup*` + 表达式 `udcExpression*` | `udcEntityAttributePost`/`UpdatePost`/`BatchPost`、`udcEntityAttributeGroup{CreateUpdate,CanceGroup,BathUpdate}Post` |
| `rule` 规则 | `v.Ay` ← **`v=l(61145)`** | `udcMicroflow*EntityRule*` + 规则族 | `udcMicroflowSearchEntityRulePost`（`params:{sourceId}`，返回 `groupType`）+ `deleteRule` |
| `refer` 参照 | `p.A` ← **`p=l(53993)`** | `udcReferConfig*`（31，含 `udcMetaData*Refer*`、`udcFunction*Refer*`） | `udcReferConfigCreateOrUpdatePost`/`GroupListPost`/`DeleteByGroupIdPost` |
| `event` 事件 | `m.A` ← **`m=l(77200)`** | `udcEvent*`（34）+ `udcEntitySelectEventDataByEntityIdGet` | `udcEventPost`/`CreateWithDataPost`/`UpdatePost`/`DeleteBatchPost`/`ListPost` |
| `index` 索引 | `s.A` ← **`s=l(4985)`** | `udcIndex*`（11） | `udcIndexPost`/`UpdatePost`/`DeleteBatchPost`/`EntityListPost`/`AttributeEntityGet` |
| `basicInfo` 基本 | `u.A` ← **`u=l(82704)`**（在 `en.slice(1)` 之外单独渲染） | `udcEntity*`（79）+ `udcEntityGroup*` + 版型 `udcEntityStereoEntityAppGet` + openApi `udcEntityOpenApiSelectGet` | `udcEntityPost`/`UpdatePost`/`EntityCopyPost`/`SelectAllByAppidAppGet` |
| 辅助：实体树侧栏 | `d.A` ← **`d=l(53777)`**（`useMemo` 包装，`handleSelectEntity` 等） | 实体清单/分组 | `udcEntitySelectAllByAppidAppGet`、`udcEntityGroupSelectByAppidAppGet` |
| 辅助：徽标/拼音 | `T`←`l(75427)`、`b`←`l(58694)` | 拼音（实体编码自动生成） | `udcPinyinGet` + `udcI18nResourceStrToPinyinGet`（`InputQuery`） |
| 辅助：tab 框架 | `_`=o.Tabs.TabPane、`C.F7`（`C`←`l(28509)`，逐 tab `element:k.bV.<ADDR>` 包装）、`k`=94974（`k.bV.*` 地址常量族） | 无 op | — |

**残余（如实标注）**：单个按钮级（如「新建索引」按钮→`udcIndexPost` 的一一对应）需进 `48998`/`77200` 等组件模块抽 `load({fieldType})`——**op 前缀与 tab 已一一对应**，按钮级映射未逐条验证（UNVERIFIED，成本高、收益低）。

**勘误（2026-10-12 二轮核实）**：上一版表格把组件模块写成 `66835/27932/6898/14830/31623/76212`——**全错**（`66835` 实为 CAF hook 转发模块 `n.d(t,{Ay:→r.E,W7:→r.m,fe:→r.n}); r=n(98021)`，`14830` 在 166 chunk 中不存在）。正确值来自 style-selector 的 **module `74964`**（`74964:` @ 249312，259KB 文件 `…da1efd.d0f55ffa.js`；同前缀共 5 个 chunk，取 259011b 那个）。

### 2.1 基本 tab（图 18）

UI：基础设置 = `*实体名称`（"实体显示名称，如人员"）、`*实体编码`（自动生成可修改，如 Person）、`第三方实体`、`*实体类型 ⓘ = 标准/单据/平铺档案/树形档案`、`字段集 ⓘ`、`父实体`（**= 主子表**）、`*实体分组`；高级设置 = `扩展实体 ⓘ`、`数据权限`开关（"开启后，运行时可管控数据的权限"）、**`openAPI ⓘ = 创建/删除/更新/查询`**、`密级管理`开关（"开启后将预置【密级】字段，且开启后无法关闭"）。顶部右上：`检查`、`页面调试(beta)`、`测试`、`更多`。

| 面 | 证据 |
|---|---|
| op | `udcEntityPost`/`udcEntityUpdatePost`/`udcEntityDeletePost`/`udcEntityBatchDeletePost`/`udcEntityEntityCopyPost`/`udcEntityGetInputPath`/`udcEntitySelectAllByAppidAppGet`/`udcEntitySelectMasterEntityCountAppGet`/`udcEntityStereoEntityAppGet`(版型=实体类型)/`udcEntityOpenApiSelectGet`/`udcEntityUpdateExtensionLinkagePost`/`udcEntityBatchUpdateEntityGroupIdAndOrdernoPost` |
| 分组 | `udcEntityGroup{Create,Update,Delete,BatchDelete,UpdateBatch,SelectByAppidAppGet}Post` |
| 后端 | `EntityController`（**类级 `@RequestMapping("udc/entity")`、`@RestApi(group="实体管理接口")`、`@HasRole({udcAppDesigner, udcSystemAdmin})`**，55 api）+ `EntityGroupController` `udc/entity-group` + `StereotypeController` `udc/stereotype`（版型）+ `EntityOpenApiController` `udc/entity-open-api` |
| openAPI 四操作 | `EntityOpenApiController`（1 api）+ 实体表 openApi 开关；**创建/删除/更新/查询的粒度绑定 UNVERIFIED** |
| 密级/数据权限 | 前端开关有；后端落点 UNVERIFIED |
| 证据 | STATIC（截图+bundle+javap）；字段创建链为 VERIFIED_STATIC_SOURCE（旧源码树，`entity-settings-source-audit.md` §2） |

### 2.2 字段 tab（图 8/9/11）

UI：`+ 添加`/`删除`/`新建分组`/`转移至`/`保存`/**`生成页面`**；表头 `序号/名称/编码/类型/阈值设置/默认值ⓘ/计算值ⓘ/必填/唯一/默认显示ⓘ/更多`；每行属性勾选 `列表项/详情信息/快捷搜索项`；分组折叠（系统/流程/单据/订单状态）；底部 `在底部添加：N 行 添加`；字符计数 `1767/16000`。

**计算值/默认值表达式弹窗**（图 11 + 用户报文）：标题 `订单金额 = 在下方选择字段变量或者函数，且在英文输入法下编辑`；按钮 `全量复制/部分复制/粘贴/清空/验证` + `取消/确定`；运算符 `+ - × ÷ mod = != > < >= <= and or not true false ( ) 为空 不为空 包含(全部) 属于`；左「可选范围」= 系统变量(组织机构/日期/环境变量/插件) + 当前实体字段(带数据类型)；中「函数」8 类 = 基础/日期/数学/文本/条件/聚合/变化/枚举函数；右为函数说明（示例 `isNull(扣缴义务人)`）。

| 面 | 证据 |
|---|---|
| op（属性 CRUD） | `udcEntityAttribute{Post,UpdatePost,Get,BatchPost,BatchUpdatePost,BatchDeletePost,SelectByPrimaryGet,TransferPost,SelectParentEnumAttrsPost,PresetAttributeCapacityAllAppGet}` |
| op（属性组） | `udcEntityAttributeGroup{CreateUpdatePost,CanceGroupPost,BathUpdatePost,Search}`（**拼写原样：`Cance`/`Bath`，禁"修正"）+ `udcAttributeGroup{EntityGet,OperateBatchPost}` |
| op（表达式） | **`udcExpressionSchemaPost`(body)** + **`udcExpressionSystemVariableListGet`(path)** ← 系统变量列表来源 |
| REST（用户提供） | `POST /service/udc/expression/schema`、`/expression/preset/list`、`/expression/transform`；响应 `{"resultTypeInfo":"DECIMAL","schemas":[…uniformityParams{paramId,paramCategory:Entity|Attr}],"tokens":[{uid,type:FUNCTION,value:roundOff,desc:取整,subOps:[[VARIABLE Dingdan.id]]}],"isMultiSelect":false,"terminalSupportType":"BACKEND"}`；transform 前端 JSON = `{"type":"__EXPRESS_TOKENS","data":[…tokens…]}` |
| 后端 | `AttributeGroupController` `udc/attribute-group`（"字段分组访问接口"，7 api）+ `AttributeSetController` `udc/attributeSet`（"字段集管理接口"，10 api）+ `DataTypeController` `udc/data-type`（"实体-数据类型"，6 api）；属性 CRUD 挂在 `EntityController` 内（createAttribute/updateAttribute/deleteAttributeById…） |
| **表达式后端** | **BLOCKED/UNVERIFIED**：`ExpressionController` 不在 23 个已盘 artifact 任何 javap 里（含 `udc-flow`/`udc-runtime`/`udc-common`）；`AppParamExpressionRtSchemaLoadServiceImpl`、`ExpressionEntityParamRtServiceImpl`、`CustomExpressionRightParamParser`（均为 `com.seeyon.boot.starter.udcrt.*`）出现在 udc-runtime 类清单 → 疑在 **`udc-starter-runtime`**，需拉新 jar 或查 pod |
| 默认值三机制 | `defaultValue` / `defaultValueSystemVariable`(JSON) / `defaultValueExpressionDesignData`(+`RuntimeData`/`Caption`/`IsChange`)——**不能只给一个 defaultValue 字符串**（`entity-settings-source-audit.md` §3） |
| 字段校验 | 编码字母开头+字母数字下划线、≤30；SERIAL 须指定序列号规则；String 唯一字段 >100 拒；全实体 DB 总长度检查（§2.2） |
| 生成页面弹窗（图 10） | 「选择生成页面类型」：基于实体快速生成列表页+详情页并建菜单关联；`页面所属=创建菜单/分组`+所属(订单列表)+web端(基础设置)/移动端(默认分组)；列表页模板 `树表查询`、详情页模板 `单据详情_主子分组`；`重复生成页面时,修改页面标识,会生成新页面`；按钮 `切换模板/取消/生成` |

### 2.3 规则 tab（图 13）

UI：条件分支流程画布（`开始 → 条件分支[① 符合条件即进入该分支 / ② 不符合条件即进入该分支=默认分支] → 结束`），右侧「请选择一个活动节点」：**`逻辑活动=分支`、`参数操作=设置值`、`基础服务=子微流程`**；左上 `描述: 1`。

用户口径：规则用于「更复杂的多条件赋值」（选项 A/B → 文本赋值 aa，C → 不赋值）与**「校验」= 数据准入规则，仅对新增/更新生效**（如不能补上个月的打卡信息）。

| 面 | 证据 |
|---|---|
| **语义权威** | `EntityService.loadEntityRule`（旧源码 `EntityService.java:1404-1425`）：`microFlowService.loadHasRuleEntityId(appId)` 按 `GroupTypeEnum` 分组 → **`VALIDATE`→`hasValidateRule`（= 校验/准入）、`DEFAULT_VALUE`→`hasDefaultValueRule`（= 默认值规则）、`ASSIGN_VALUE`→`hasAssignValueRule`（= 赋值规则）**。**三类规则都是 MicroFlow 体系，不是字段 defaultValue 的别名**（§4.3） |
| op | **`udcMicroflowSearchEntityRulePost`(body)** —— 完整调用（主 store module 52745，导出 `fetchRuleList/searchRuleList/deleteRule`）：<br>`{fieldType:"udcMicroflowSearchEntityRulePost", paramsType:"...InputBody", paramsKey:"body", queryFields:"pageInfo{…} content{id name appId versionCode caption type description orderNum state createTime updateTime **groupType**}", params:{pageInfo:{needTotal:true,pageNumber:1,pageSize:10}, params:{**sourceId:<实体id>**}}}` → **`groupType` 字段就是 VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE 的区分键**。删除 = 同族 op + `params:{id}` + `queryFields:"content"`。另有 `udcMicroflowCopyPageRuleBoundControlPost`（页面规则绑定控件复制）+ `udcMicroflowFindByIdGet`/`CreatePost`/`CheckMicroFlowCaptionPost`（用户 DevTools 抓到） |
| 独立路由 | `/app-design/entity-rule`（+ `/snapshot`，comp=G）与 `/app-design/page-rule`、`/app-design/pagerules` **三者不等同** |
| 后端 | `MicroFlowController` `udc/microflow`（67 api）+ `MicroFlowGroupController` `udc/micro-flow-group`；扣减规则另属 `DeductionRuleController` `udc/deduction`（16 api，"扣减规则接口"） |
| 分辨 | **扣减 ≠ 字段默认值**：`udc_deduction_rule/algorithm/rule_detail/map` 四表，生成 BeforeCreate/Update/Delete 监听器（§7.1/7.2） |
| 校验规则的独立 op | UNVERIFIED：主 store 里 `Valid` 仅命中 `udcDeductionValidRulePost`（扣减侧）；`VALIDATE` 组的 CRUD 应在 `udcMicroflow*` 内按 groupType 过滤，待证 |

### 2.4 参照 tab（图 14）

UI 两步：`① 选择参照模板 ✓ → ② 设置参照内容`；web/移动 双端（各带角标）；子 tab = `*显示列` / `条件` / `排序` / `搜索` / `穿透页面` / `新增页面`；字段 `*实体`(订单)、`*参照显示字段`（空则红字"参照显示字段不能为空"）、`参照下拉字段`、`数据关联`（复选"关联结果为两个实体的交集"）、`分页条数`(10)；左字段树（订单→系统/流程/单据分组）、右已选列表（显示列/列宽设置/隐藏/操作）+ `添加自定义列`。

用户口径：建字段选择实体或参照后即可配置，届时**携带字段过来显示**。

| 面 | 证据 |
|---|---|
| op | `udcReferConfig{CreateOrUpdatePost, CreateConfigInfoPost, DeleteByGroupIdPost, GroupListPost}` + `udcMetaData{MergeReferPost, ReferAndAppPost, SelectCustomReferPageGet}` + 功能节点侧 `udcFunction{CreateFunctionReferPost, UpdateFunctionReferPost, UpdateNameFunctionReferPost, DeleteReferPagePost, PageInParamsReferGet}` |
| 后端 | **`ReferConfigController` `udc/refer-config`（12 api，"参照配置接口"，`@HasRole({OrgAdmin, udcAppDesigner, udcSystemAdmin})`）** |
| 易混 | `udc_page_schema` 里的 refer ≠ 参照配置对象；`ReferUtil:114` 参照悬空是一致性检测报错点之一（部署侧） |
| 证据 | STATIC（op+controller），UI→op 的逐一绑定 UNVERIFIED |

### 2.5 事件 tab（图 15/16）

UI：左 `事件说明`/搜索/`删除`/`新建` + 列表（事件名称/事件编码/触发条件，空态"暂无数据"）；右 `*事件名称`、`*事件编码`、`*事件数据`(设置按钮)、**`*触发时机 = 修改时/新增时/删除时`**、`触发条件`(点击设置条件)、`事件描述`。
说明文案原文：「事件，是为了解决跨应用的事件通知，实体数据的新增、修改、删除，都可作为事件的触发条件。事件触发器支持在微流程、流程中，作为触发条件使用。」

| 面 | 证据 |
|---|---|
| op | `udcEvent{Post, CreateWithDataPost, UpdatePost, DeletePost, DeleteBatchPost, ListPost, SearchTermPost, Get, SelectWithDataGet}` + `udcEntitySelectEventDataByEntityIdGet` + 生单侧 `udcDataFlowListEvent{Data,Entity,s}Post` |
| 后端 | `EventController` `udc/event`（12 api，"事件访问接口"，`@HasRole({udcAppDesigner, udcSystemAdmin})`）；旧源码路由：`POST /udc/event`、`/create-with-data`、`/update`、`/update-with-data`、`/list/business-event`、`/list/events` |
| **边界（关键）** | `EventController → 事件定义/事件数据` ≠ `MicroFlow trigger BUSINESS_EVENT + messageInfo → 监听动作`。**`udc_event` 建一行不等于它触发了哪个动作**；绑定位置在监听微流程的 `data_schema.trigger`，`udc_event` 表无指向微流程的列（§5 + metadata-artifact-apis.md） |
| 触发时机→后端 | `修改时/新增时/删除时` ↔ 事件 `actionType`；标准生命周期 8 类（TransactionSuccessUpdate/Create/Delete、AfterCreate/Update/Delete、BeforeCreate/Update）见 metadata-artifact-apis.md。**前端文案词典**（主 store `event` 段）：`{caption:事件名称, name:事件编码, condition:触发条件, data:事件数据, actionType:{label:触发时机, update:修改时, create:新增时, delete:删除时}, placeholder:{name:"默认自动生成，可修改默认逻辑", condition:"点击设置条件", data:"点击编辑事件数据"}, tips:{delete:{title:"您确定要删除此事件吗？"}}}` |
| **`actionType` 值域（本轮修正为 4 类）** | 主 store 枚举：`BUILD_IN="buildin"`、`WIDGET="widget"`、`MICRO_FLOW="microflow"`、**`EVENT_THROW="enevtThrow"`**（值拼写有误，平台原样照抄）—— 比 skill 原记的 3 类多一类。另发现**页面动作枚举**含 `VALIDATE_ENTITY="VALIDATE_ENTITY"`（页面"校验实体"动作，**与实体规则的 VALIDATE 组不是一回事**，别混） |

### 2.6 索引 tab（图 17）

UI：`删除`(置灰)/`新建` + 列表（索引名称/索引编码/字段/类型），样例 `订单状态索引 / idx_4317890813011251043 / 订单状态 / 普通索引`；右表单 `*名称`、`*字段`（"请选择字段，**最多选择5个**"）、`*类型 = 普通索引|唯一索引`、`描述`。

| 面 | 证据 |
|---|---|
| op | `udcIndex{Post, UpdatePost, DeletePost, DeleteBatchPost, EntityListPost, AttributeEntityGet}` |
| 后端 | `IndexController` `udc/index`（7 api，"索引访问接口"，`@HasRole({udcAppDesigner, udcSystemAdmin})`） |
| 字段约束 | 最多 5 字段（截图）；`fieldIds` 传**逗号分隔字符串**、给数组报 `BOOT_3002 to type String`（metadata-artifact-apis.md） |
| 语义 | 索引是**实体元数据装配的一部分**（`EntityService.loadEntityAndAttribute → indexService.selectByEntityAttributeMap`），但 ≠ 字段集（§4.1） |
| 样本 | `index_source` 0=平台建实体自动默认、1=自定义；`name=code=idx_<雪花>`；本会话 A 层 LIVE：索引 `4046527061344862471` |

---

## 2.7 写链 body 字典 + paramsType 特例（2026-10-12 活体推进）

### 2.7.1 各 tab 写 op 的 params 形态（主 store 调用点逐个抽出）

| tab | 写 op | params 构造 | queryFields |
|---|---|---|---|
| 基本 | `udcEntityPost` | **`{...e, appId: <当前appId 由前端注入>}`**（`i.sZ`） | `content` |
| 基本 | `udcEntityUpdatePost` | 同上 | `content` |
| 字段 | `udcEntityAttributePost` / `udcEntityAttributeUpdatePost` | `params: e`（**body 由组件构造**，三分支按 `t` 选 create/update） | `content` |
| 字段组 | `udcAttributeGroupEntityGet` | key=**path** | 见 §2.8.2 完整字段清单 |
| 索引 | `udcIndexPost` | `params: e` | `content` |
| 索引 | `udcIndexUpdatePost` | `params: e` | `content` |
| 索引 | `udcIndexDeletePost` | `params: {id: e}` | `content` |
| 索引 | `udcIndexDeleteBatchPost` | `params: {ids: e}`（数组） | `content` |
| **索引** | **`udcIndexEntityListPost`** | **`paramsType="Long"` → `variables.body = <裸实体id>`** | `content{caption name fieldIds fieldNames fieldCaptions remark indexSource entityId type id guid code}` |
| 事件 | `udcEventPost` | `params: e` | `content` |
| 参照 | `udcReferConfigCreateOrUpdatePost` | `params: e` | `content` |
| 参照 | `udcMetaDataSelectCustomReferPageGet` | key=path，`params:{pageId: e}` | `content` |
| 规则 | `udcMicroflow{Create,Update,Delete,CheckSchemaUpdate,BatchMove,UpdateOrderNoAndGroup}Post` | 全部 key=body、type=`…InputBody` | — |
| 读 | `udcEntitySelectAllByAppidAppGet` | key=path，`params:{appId}` | 实体全字段（见 §2.7.3） |
| 读 | `udcStereotypeListGet` | 零入参 | `content{features availableFeatures necessaryFeatures name caption description order deprecated dataFlowEnabled …}` ← **版型特性清单（密级在 `features` 里）** |

### 2.7.2 `Attribute` 完整字段清单（自 `udcAttributeGroupEntityGet` 的 queryFields，字段 tab 的 body 字典）

```
顶层：appId caption entityId guid id orderNo preset publishState virtual uniqueKey
attributeDtoList[] 每条：
  identity: id guid entityId appId attributeFullName attributeGroup attributeGroupId auditLog actionType
  基本: caption name dataType dataTypeDisplayName decimalDigits dataFormat dataI18n description orderNo edit hidden
        existDto preset publishState virtual uniqueKey quickSearch
  默认值三机制: defaultValue / defaultValueSystemVariable / defaultValueExpressionDesignData
              / defaultValueExpressionRuntimeData / defaultValueIsChange
  表达式计算值: expressionDesignData / expressionRuntimeData
  关系: relationEntity relationEntityName relationCode relationType relationApp multiSelect
  枚举: relationCtpEnum{enumLevel enumType}
  安全: desensitization enableDesensitization encryption enableEncryption
        enableSensitiveWordCheck enableOpenApiEncrypt
  其他: calculate createTime
```
（`desensitization/enableSensitiveWordCheck/enableOpenApiEncrypt` = 密级/脱敏相关字段，与 `SecretLevelFeature` 呼应）

### 2.7.3 `Entity` 字段清单（自 `udcEntitySelectAllByAppidAppGet` queryFields，与 `udc_entity` 列一一对应）

```
id name caption orderNo category features attributeSetIds multiplicity
entityGroup entityGroupId parentEntityId customScalabilityGlobal customScalabilityId
permission stereotype superior hasChild parent publishState originalId linkageExtFiled
```

### 2.7.4 `paramsType` 特例 14 个（**不能按 `InputBody` 猜**）

| paramsType | op |
|---|---|
| **`Long`** | `udcIndexEntityListPost` ← 活体验证：传裸 id |
| **`String`** | `udcSandboxClearDataPost` |
| **`Map`** | `udcEntityAttributeSelectParentEnumAttrsPost` |
| **`[XxxInputBody]`（数组包装 10 个）** | `udcEntityAttributeGroupBathUpdatePost`、`udcEntityAttributeBatchUpdatePost`、`udcEntityAttributeGroupCreateUpdatePost`、`udcEntityGroupUpdateBatchPost`、`udcEntityBatchUpdateEntityGroupIdAndOrdernoPost`、`udcUdcEnumItemOperateBatchPost`、`udcDataTransferObjectCreateDtoWithAttrsPost`、`udcDataTransferObjectUpdateDtoWithAttrsPost`、`udcConditionCheckPost`、`udcApplicationDependentApplicationCreateBatchPost` |
| **`[String]`** | `udcMicroflowFilterNotVirtualPost` |

### 2.7.5 expression 四接口活体 PASS（2026-10-12）

| 接口 | 请求 body | 结果 |
|---|---|---|
| `POST /service/udc/expression/preset/list` | `{}` | ✅ `BOOT_0000` → `presetVariableInfo[].items[]`：`system.currentUserId`(BIGINTEGER, relationEntity=OrgMember)、`system.currentUserName`、`system.currentUserCode`… |
| `POST /service/udc/expression/schema` | **`{ids:["<实体id>"], paramType:"ENTITY", upsource:true, serverName:"udc"}`** —— **2026-10-15 就地更正**：旧口径写「传 appId」，**LIVE 实测带 `appId` 即报 `BOOT_3000`**，必须**省略** appId（另 `idsStr/extension:null` 报 `BOOT_3002`） | ✅ `BOOT_0000` → `[{name:"Dingdan", description:"订单", type:"OBJECT", properties:[{name:id,type:BIGINTEGER,uniformityParams.paramId}, createTime…]}]`（首次传 `idsStr/extension:null` 报 `BOOT_3002`） |
| `POST /service/udc/expression/transform` | `ExpressionSaveDto` 全字段（= 用户报文：`resultTypeInfo/schemas/tokens/isMultiSelect/terminalSupportType/sourceAppName/version`） | ✅ `BOOT_0000` → `content.designData.expressionTranslation = "roundOff(订单.ID)"` |
| `POST /service/udc/expression/check` | 同上 | ✅ `BOOT_0000` → `content: true` |

### 2.7.6 索引列表活体 PASS（含失败原因修正）

- ❌ 首次：`variables:{body:{entityId:"<id>"}}`（按 `InputBody` 猜）→ 无 code/content null
- ✅ **`variables:{body: <裸Long>}`**（按 `paramsType:"Long"`）→ `BOOT_0000`，返回
  `[{"caption":"订单状态索引","name":"idx_4317890813011251043","fieldIds":"3729580767880732084","fieldNames":"order_status","fieldCaptions":"订单状态","indexSource":"MANUAL_CREATE","entityId":"5678466719436905487","type":"NORMAL","id":"5741019122070734111","guid":"-6772332740116591607","code":"idx_4317890813011251043"}]`
  —— 与图17 截图（订单状态索引 / idx_4317890813011251043 / 订单状态 / 普通索引）**逐字段对上**；`type:"NORMAL"`=普通索引、`indexSource:"MANUAL_CREATE"`=自定义（数字码 1 的枚举名形态）。

**事件数据选择器已通（2026-10-12 修正）**：`udcEntitySelectEventDataByEntityIdGet`（key=path）→ **`path:{id:<数字Long>}` + 完整 queryFields** 才 `BOOT_0000`；返回 `content[{attributes{id name caption dataType entityId multiSelect relationEntity relationEntityName relationCode relationType relationApp description publishState attributeFullName}, children{…}, hasChild appId appName …}]`（样本：`relationType:"Many2OneAssociation"`、`description:"ID-系统属性"`、`attributeFullName:"com.seeyon.zzprobenew…"`)。**两个变量同时改的（字符串 id→数字 id、简化字段→完整字段），具体哪个决定性未隔离** —— 构造时照前端原文传两处。

### 2.7.7 写链最小闭环 LIVE（2026-10-12，zzprobe / Dingdan 实体）

| 步 | 请求 | 结果 |
|---|---|---|
| 创建字段 | GraphQL `udcEntityAttributePost`，`body:{appId:<数字>, entityId:<实体id>, name:"smokeChainChk", caption:"写链冒烟", dataType:"STRING"}` | ✅ `BOOT_0000` → `content:"5385522468957535834"` |
| 回读 | `GET /service/udc/entity/attribute/{id}` | ✅ identity **5/5**（id/name/caption/dataType/entityId） |
| 批量删（形态1） | `udcEntityAttributeBatchDeletePost` + `body:[<裸id>]` | ⚠️ `BOOT_0000` 但 **`content=0`** → **字段仍在** |
| 批量删（形态2） | 同 op + `body:[{id:"<id>"}]`（对象数组） | ⚠️ `BOOT_0000` 但 **`content=0`** → **仍没删** |
| **单删** | **`udcEntityAttributeDeletePost` + `body:{id:"<id>"}`** | ✅ **`content=1`** → 回读字段已不存在 |

**平台陷阱（重要）**：`udcEntityAttributeBatchDeletePost` 返回 `BOOT_0000` **不代表删了**——**`content` 是影响行数，`0` = 一行没删**。两种数组传法（裸 id / 对象）都得 0，而**单删 `udcEntityAttributeDeletePost` 的 `{id}` 得 1**。→ 任何删除操作必须断言 `content >= 1` 并回读确认，不能只看 `code==BOOT_0000`（与「HTTP 200 不算成功」同族纪律，但这是更隐蔽的一层：**业务码也成功，数据没动**）。

---

## 2.8 实体页面实现层（2026-10-12 补齐：tab 定义对象 + 渲染 switch + 组件绑定）

主组件在 chunk **`src_components_design_settings_common_style-selector_index_module_less-src_components_app-…`（259KB）**（module 16345 是 `entity-collections` 壳，仅 545 字节，`t.default=()=>{useSelector(appDetails)}`，真身在 style-selector chunk）。

### tab 定义对象 `R`（8 个 key，同 basic-setting 的 `D` 法）

```js
R = {
  basicInfo:    g.un.ENTITY_CREATE_PAGE_TABS_BASIC_INFO,
  attributeSet: g.un.ENTITY_CREATE_PAGE_TABS_ATTRIBUTE_SET,
  rule:         g.un.ENTITY_CREATE_PAGE_TABS_RULE,
  refer:        g.un.ENTITY_CREATE_PAGE_TABS_REFER,
  event:        g.un.ENTITY_CREATE_PAGE_TABS_EVENT,
  relation:     g.un.ENTITY_CREATE_PAGE_TABS_RELATION,   // 第7个（截图未见）
  index:        g.un.ENTITY_CREATE_PAGE_TABS_INDEX,
  data:         g.un.ENTITY_CREATE_PAGE_TABS_DATA         // 第8个（截图未见）
}
en = useMemo(() => Object.keys(R).filter(e => el(R[e])), [el])   // el = (0,g.Ay)() ← CAF 谓词
```

- **8 个 key**，截图场景只渲染 6 个（`relation`/`data` 未进 switch，见下）。
- `en` 经 **CAF 谓词 `el(identityCAF)`** 过滤 → **tab 可见性由 CAF 体系决定**（数据源在服务端，前端只有常量名）。

### 渲染 `switch(e)`（逐 case 条件，STATIC）

| tab key | 中文 | 显示条件 | 组件（`{entityId:V}` 传入） | 风格地址 |
|---|---|---|---|---|
| `basicInfo` | 基本 | `en.includes("basicInfo")` | `u.A`（+`currentTag/disabledParent/handleSelectEntity`） | `er("基本","basic")` → `k.bV.BASIC` |
| `attributeSet` | 字段 | 无额外条件（默认 tab） | `c.A` | `k.bV.ATTRIBUTE` |
| `rule` | 规则 | **`!Y && !eo`** | `v.Ay` | 动态 `"MICRO_&_entity_&_"+V` → `k.bV.RULE` |
| `refer` | 参照 | **`entityDetails.multiplicity === "ONE2MANY"`** | `p.A` | `k.bV.REFER` |
| `event` | 事件 | **`!Y && !eo`** | `m.A` | `k.bV.EVENT` |
| `index` | 索引 | **`!Y && !eo`** | `s.A` | `k.bV.INDEX` |
| `relation` / `data` | （关联/数据） | **switch 无 case → 返回 null**（key 在 `R` 但不渲染） | — | — |

### 2.8.2 组件内 service 层的 body 构造（最后一层，2026-10-12）

组件模块（`48998` 字段 104KB / `77200` 事件 52KB / `82704` 基本 54KB / `53993` 参照 25KB / `61145` 规则 7.5KB / `4985` 索引 7.5KB）**内无 `.load()`**——三层结构：**组件 → dispatch(service/thunk) → loader.load**。body 在 service 层拼。

**① 事件创建 = `createEventWithData`（`77200` 组件内 `B=async`，完整原文）**
```js
M=(e)=>{let{caption,name,attrs}=e; if(!Array.isArray(attrs))return null;
  return{appId:sZ, name, caption,
    source:"MICRO_FLOW_MESSAGE",        // 事件数据的消息源
    sourceId:f.id,                      // 当前实体 id
    attributes:attrs.map(a=>{let sp=a.selectParam; return{
      name:sp.outputName, caption:sp.description,
      dataType:(sp.dataType===Dto||sp.dataType===Enum)?sp.javaType:sp.dataType,
      dataTypeCategory:dataType(sp.dataType),
      type:String(sp.type).toUpperCase()==="ARRAY"?"LIST":"OBJECT",
      description:""}})}
B=async()=>{let{event:t,structure:n,attrs:a}=await form.validateFields();
  let eventDataList=M({...n,attrs});
  let body={appId:sZ, caption:t.caption, name:t.name,
    source:"MICRO_FLOW",                // ← 事件源=微流程
    sourceId:f.id, eventDataType:pe.Object, description:t.description,
    eventDataList, messageType:t.messageType};
  V7.createEventWithData(body)}         // 成功 message("消息创建成功！")
```
- **事件数据的 attributes 来自微流程节点输出参数**（`selectParam.outputName/description/dataType/javaType/type`）；Dto/Enum 类型取 `javaType`
- 删除：`V7.deleteEvent({id})` + `Modal.confirm("您确定要删除吗")`

**② 字段 create/update 同一 service 分支**（`48998` → service 模块）
```js
async function postEntityAttribute(e, t){   // t=isUpdate
  return t ? load({fieldType:"udcEntityAttributeUpdatePost", paramsKey:"body", params:e})
           : load({fieldType:"udcEntityAttributePost",     paramsKey:"body", params:e})}
```

**③ 实体 create = `appId` 从 redux 注入**（基本组件 service）
```js
async function create(e, showLoading=true){
  let n=await load({fieldType:"udcEntityPost", params:{...e, appId:i.sZ}, queryFields:"content", showLoading});
  return n.content}
// updateEntity(e) 同族；导出 21 个 service（含 updateIndexes/fetchIndexesListByEntityId/
//   fetchEntityOpenApi/fetchStereotypeList/fetchAppFieldSetList/fetchEntityOrGroupBatchDelete…）
```

**④ 事件列表 body 带排序**：`fetchEventList({params:{sourceId:<实体id>, sort:{orders:[{direction:"DESC", property:"createTime"}]}}})`

**⑤ 规则列表完整 queryFields**（`52745`：`fetchRuleList/searchRuleList/deleteRule`）
- `fetchRuleList(entityId)` → `body:{pageInfo:{needTotal:true,pageNumber:1,pageSize:10}, params:{sourceId:entityId}}`
- `queryFields` = `pageInfo{pageNumber pageSize pages total needTotal} content{id name appId versionCode caption type description orderNum state createTime updateTime groupType}`（比简化版多 `versionCode/orderNum/description`）
- `searchRuleList(body)` = 同 op 直传完整 body；`deleteRule` → `udcMicroflowDeletePost`

**⑥ 数据类型能力表**（字段编辑器的数据类型下拉）
`udcDataTypeDataTypesByAppIdAppGet(path:{appId})` → `content{caption name order enableCalculable enableAggregation enableDecimalDigits enableDefaultValue enableEncryption enableIndex enableLengthRange enableLog enableMaxAndMin enableMultiSelect enablePattern enableRequired enableSensitive enableUnique enableSearch enableSensitiveWordCheck custom baseDataType enableI18n list detail quickSearch}`
——**每种数据类型能做什么（默认值/索引/唯一/必填/脱敏/正则）由这个表驱动**（`enableDefaultValue` 等），不是前端写死。

### 2.8.3 索引/规则/参照三个组件的 body 与校验（2026-10-12）

**① 索引组件 `4985`（7.5KB，form name=`indexes-edit`）**
- **索引名前缀**：`name` 生成 `"idx_"`，`type==="UNIQUE"` → `"uk_"`（与活体返回 `idx_4317890813011251043` 对上）
- **`fieldIds` 是逗号分隔字符串**，回填时 `y.fieldIds.split(",").map(String)`
- **六字段禁用矩阵 `_(e)`**（`l`=isNew、`I`=isLastVersionApp、`N`=entityDetails、`y`=editData）：
  | 字段 | 可编辑条件 |
  |---|---|
  | `CAPTION/REMARK/SUBMIT` | `isNew && !isLastVersionApp` |
  | `FIELD_IDS/TYPE` | 同上 **或** `indexSource==="MANUAL_CREATE"` 反面（非自建不可改） |
  | `NORMAL/UNIQUE` | 同上 **或** `entityDetails.publishState==="PUBLISHED"` 反面（已发布不可改） |
  | `DELETE` | 非新建 且 非自建 → 禁删 |
- 删除：`deleteIndexes(editData.id)` → `message.success("删除成功！")`；可选类型来源 `fetchEntityAttributeListByEntityId(entityId)`
- 包装：`p.F7{property:{id:…}}`（`p`=28509）

**② 规则组件 `61145`（7.5KB，新建 modal）**
```js
checkMicroFlowCaption({appId:sZ, caption, description,
  name:"name_"+Date.now(),        // ← name 自动生成
  sourceId:<实体id>, type:"ENTITY_RULE", triggerType:"MANUAL", dataSchema:""})
// content===false → message.error("规则名称重复, 请修改后重试！")  ← 重复检查
```
→ 新建实体规则的初始 body：`type:"ENTITY_RULE"`、`triggerType:"MANUAL"`、`dataSchema:""`（空，后续编辑器填）；删除 `deleteRule` via `g.Mr`。它 import `v=l(27932)`（规则编辑器子组件）与 `o=l(76212)`（基本组件）。

**③ 参照组件 `53993`（21KB 主模块 + lazy 步骤2 `R=l(95695)`）**
- **Steps 三节点**：`选择参照模板` → `设置参照内容` → `（空 icon 第三步）`；删除确认 `确定删除参照 [caption] ?`（按钮 `#F59E0B`）
- **默认配置**：`X={caption:"", type:"List", id:""}`；redux = `appDesign.entityReferenceReducer`
- **步骤1→2 校验 `tE`**：`validateFields()` + `caption.trim()` + **本地重复检查** `findIndex(list.filter(id!==ee.id), ["caption", caption])>-1 → "参照名称不能重复"` → `setConfigs({...ee})` + `setTerminal(er[0])` + `setStep(1)`
- **步骤2 条件 `e5`**：`whereCond = where[0].validateFields()`（失败 → `"<术语>条件配置不完整, <errors>"`）；`type===k.Sv.LeftTreeRightList` 额外 `treeWhereCond`（树条件）+ `treeColumns`；多终端 `er.length>1 ? PC : ND` → `terminalList` 表单字段
- **配置 body 骨架**：`{…baseInfo, whereCond, treeWhereCond, columns, treeColumns, configs, terminal, terminalList}`
- `createOrUpdate` service 调用在 lazy 子组件内，**未直接抓到**（UNVERIFIED，但配置结构已明）
  - **坐实（7dcbc10）**：提交链逐字闭环——`53993.onClick(790)→validateFields(e4)→e3→handleSaveWhereData(716)→e2(668)→e1(614 组 body)→module332.Jt/p(670)`
    → `l._n.udcApolloQuery( e.id ? a.DA : a._H, {body:e}, {showLoading:true} )`；
    `module332` 导出映射 `DA→o=udcReferConfigUpdateConfigInfoPost`、`_H→i=udcReferConfigCreateConfigInfoPost`
    （`module95432` raw Apollo 文档字符串，`$body: …InputBody`），故**有 id 走 Update、无 id 走 Create**；
    读 `sZ=l=udcReferConfigListPost`、删 `pA=r=udcReferConfigDeleteByGroupIdPost`。
    4 op 已入 `graphql_write_ops`（raw Apollo 约定，§双约定），§5#8 关闭。

### 2.8.1 switch 原文级证据（module `74964`，勘误后重抽）

```js
R={basicInfo:g.un.ENTITY_CREATE_PAGE_TABS_BASIC_INFO, attributeSet:…ATTRIBUTE_SET, rule:…RULE,
   refer:…REFER, event:…EVENT, relation:…RELATION, index:…INDEX, data:…DATA}
en = Object.keys(R).filter(e => el(R[e]))        // ← el = CAF 谓词，R[e] 是 CAF 常量值
switch(e){
 case"attributeSet": return <TabPane tab={er("字段", k.bV.ATTRIBUTE)} key="attributeSet">
        F7(element:k.bV.ATTRIBUTE) <c.A key=V entityId=V/></TabPane>;      // 条件: "entity"===F && "attributeSet"===O
 case"rule":    !Y&&!eo && <TabPane tab={er("规则","MICRO_&_entity_&_"+V)}> <v.Ay entityId=V/></TabPane>;
 case"refer":   G.multiplicity==="ONE2MANY" && <TabPane tab={er("参照",k.bV.REFER)}> <p.A entityId=V/></TabPane>;
 case"event":   !Y&&!eo && <TabPane tab={er("事件",k.bV.EVENT)}> <m.A entityId=V/></TabPane>;
 case"index":   !Y&&!eo && <TabPane tab={er("索引",k.bV.INDEX)}> <s.A entityId=V/></TabPane>;
} return null
// basicInfo 单独渲染：en.includes("basicInfo") && <TabPane tab={er("基本","basic")}><u.A currentTag=X …/></TabPane>
// 其余：en.slice(1).map(ed)     （en[0]=basicInfo）
```

- **`Y`/`eo`**：`isThirdEntity` / 第三方或扩展判断（switch 前 `let{… isThirdEntity:…}` 解构；`!Y&&!eo` = 规则·事件·索引三 tab 的隐藏条件）
- **`F`** = `pathname` 尾段（`entity` 时才渲染字段 tab）、**`O`** = `entityTabActiveKey`、**`V`** = `selectedEntityId`、**`G`** = `entityDetails`、**`M`** = `isEntityEditMode`、**`B`** = `createEntityType`
- **tab key**：`er(中文, 地址)` —— `k.bV.ATTRIBUTE|RULE|REFER|EVENT|INDEX|BASIC`，规则用 `MICRO_&_entity_&_`+实体id
- **顶栏**：`tabBarStyle:{backgroundColor:"#2C3644",height:40}` ✅（与图11 深色条对上）
- **tab 切换**：`attributeSet` 或 `et` 直接切；**否则先 `(0,A.A)()` 未保存检查** → `.then(通过则切)` `.catch(console.error+message.error("实体保存报错"))` ✅
- **`basicInfo` 激活时** dispatch `(0,y.sR)(V)` + `(0,y.vV)(!1)`
- **tab 区显示门**：`(M || (!M && B!=="parentEntity" && B!=="childEntity"))` —— 编辑模式或非主子实体
- **空态**：`I.A`（`elementName`/`entityName` 空提示）

**`relation`/`data` 已定性（2026-10-12）**：CAF 常量值 `layout_content.entity.create_page.tabs.relation` / `.data`，**全 bundle 仅 enum 定义处各出现 1 次、无任何消费**→ **当前版本预留 key，不实现**（不是我漏看的隐藏 tab）。顺带抽到参照流程常量 `ENTITY_CREATE_PAGE_TABS_REFER_STEP_1_MODEL_TYPE_LEFT_TREE_RIGHT_LIST` = `layout_content.entity.create_page.tabs.refer.step_1.model_type.left_tree_right_list`（步骤1「左树右列表」模型类型）。

**变量真值（从 `useSelector` 解出）**：
- **`Y = entityReducer.isThirdEntity`** → **第三方实体隐藏 规则/事件/索引**
- **`eo = entityDetails.category === "EXT"`** → **扩展实体同样隐藏**
- `O = entityTabActiveKey`、`V = selectedEntityId`、`G = entityDetails`、`M = isEntityEditMode`、`B = createEntityType`、`U = entityTreeData`、`K = entityGroupList`、`q = entityList`、`F = pathname 末段`
- `H = entityFieldTableReducer.unsavedEntityId`、`et = entityFieldTableReducer.saved`
- **新建实体默认值 `J`**：`{parentEntityId: undefined, multiplicity: "ONE2MANY", stereotype: appFeatures.entity.stereotype.defaultStereotype || "standard", customScalabilityId: "0", category: "ENTITY", publishState: "UNPUBLISH"}`

### 行为细节（可验收）

1. **tab 切换带未保存检测**：`onChange` 里 `"attributeSet"===e || et ? 直接切 : (0,A.A)().then(l => l ? 切 : 报错)`，失败弹 `message.error("实体保存报错")`。
2. **选中实体强制回 `attributeSet`**：`ea=async e=>{H&&H!==e&&await (0,A.A)(); ei(e); P(setEntityTabActiveKey("attributeSet")); ...}`
3. **跳转状态消费**：`location.state={entityId, tab}` → `tab` 直接设 `entityTabActiveKey`（`hasSet` 防重复）。
4. **空态**：无实体 →「欢迎来到实体空间」+「请创建实体」（点击置 `parentEntity` + `basicInfo` tab）。
5. **tab 标签 = `er(label, address)`**：address 含 `/_&_/` → 静态 `T.A({address})` 徽标；否则 `T.A({path:{element, moduleProperty:{entityId}}})`。徽标组件与 basic-setting 的 `F.A` 同源，`address` 形如 `UDC_BASIC_SETTING_&_enum_&_`。
6. **布局**：`PageWrapper{noPadding, sider}` → 左侧实体树（`d.A`，`handleSelectEntity`）+ 右侧 `C.jh{module:"ENTITY", property:{entityId}}` + 顶部深色 `Tabs{tabBarStyle:{backgroundColor:"#2C3644"}}`（与截图一致）。
7. **版本约束**：`已上架版本无法{添加|复制|转移}{实体|字段|字段集|索引}，请另存版本后操作`（主 store 文案）。

---

## 3. 权限模型（本轮补的两层，此前混淆）

### 第 1 层：后端角色门 `@HasRole`（javap 5.3.517，类级）

- **49/54 controller 有类级 `@HasRole`**；角色值域 8 个：`udcAppDesigner`、`udcSystemAdmin`、`udcRootOrgAdmin`、`OrgAdmin`、`OpsAdmin`、`BpmDesigner`、`BpmManager`、`BpmSystemManager`、`cipAdmin`。
- 实体域类级配置：`EntityController` / `EntityGroupController` / `IndexController` / `EventController` / `AttributeGroupController` / `AttributeSetController` / `DataTypeController` / `ReferConfigController`(含 OrgAdmin) / `StereotypeController` = **`{udcAppDesigner, udcSystemAdmin}`**（ReferConfig 另含 `OrgAdmin`）。
- **类级无 `@HasRole` 的 8 个**（按本轮精确抽取）：`DependencyAnalysis`、`Deploy`、`MetaData`、`OperationLog`、`Parameter`、`UdcDesignMetadata`、`UdcFile`、`UdcManager` —— 其中 `Deploy`/`DependencyAnalysis`/`UdcManager` 的 HasRole 在**方法级**（全文 grep 有、类级无），粒度需逐方法核；`MetaData`/`OperationLog`/`Parameter`/`UdcDesignMetadata`/`UdcFile` **全类无**（疑似靠过滤器或确实开放）。
- 54/54 已盘（amap 与 txt 差集为空）。

### 第 2 层：CAF identity（**本轮修正：不是权限，是布局位置树路径**）

`identityCAF` 是一枚 **TS enum 编译产物**（模块 `97239`，8010 字符全是一个 enum），值为**完整 UI 布局树路径**：

```
LAYOUT_TOP = "layout_top"                HEADER = "layout_top.header"
LAYOUT_LEFT = "layout_left"              MENUS = "layout_left.menus"
MENUS_ENTITY = "layout_left.menus.entity"  MENUS_RULE = "layout_left.menus.rule"  …（17 个 MENUS_*）
FUNCTION_DESIGN_ADVANCED_SETTING = "layout_content.function_design.layout_slide.advanced_setting"
PAGE_DESIGN_PAGE_SETTING_TERMINAL_PC = "layout_content.page_design.layout_right.page_setting.terminal.pc"
```

- **共 28 个常量**：17 个 `MENUS_*` + `TOOLS_ROLE_PERMISSION`（角色权限，非 MENUS 前缀）+ 10 个 `BASIC_SETTING_TABS_*`；实体页面另有 8 个 `ENTITY_CREATE_PAGE_TABS_*`（§2.7）。另有 `ENTITY_STEREOTYPES_{STANDARD,FORM,BILL,ARCHIVE,ARCHIVETREE}` = 图18 的实体类型枚举。
- **消费机制（已定位）**：hook `Ay`（模块 97239 导出 `un`/`Ay`/`ND`）返回**谓词函数**，用法 `el = (0,g.Ay)(); en = Object.keys(R).filter(e => el(R[e]))`、`B.filter(e => eS(e.identityCAF))`、菜单 `filter(e => !e.divider && S(e.identityCAF))` → **决定该 UI 元素/tab/菜单项是否可用**。
- **`uniformityKey` + `address`** 配套：`uniformityKey` 存在时渲染徽标组件（`F.A`/`T.A`，`address` 形如 `UDC_BASIC_SETTING_&_enum_&_`、`MICRO_&_entity_&_ <entityId>`）→ 统一风格/可配置 UI 体系。
- **结论**：CAF 是**统一风格 + 可配置 UI 位置体系**；前端只持位置路径常量，**判定数据源在平台 CAF 服务端**（前端 bundle 里没有权限值）。→ 要拿"谁能看实体菜单"的权限矩阵，必须查 CAF 服务端配置，不是读 bundle。

### 真权限 = 后端 `@HasRole` + 角色资源表

- `udc_role`(88 行：`code`/`name`(i18n JSON)/`type`/`is_admin`/`app_id`/`role_level`) —— **应用级业务角色**（如「智慧营销结算平台普通人员」）。
- `udc_role_resource`(11068 行：`action`(0/1/2)/`resource_id`/`resource_type`/`role_id`) —— 角色→资源授权。
- `udc_resource`(5602 行：`name`/`path`(url)/`type`/`data_type`/`parent_code`/`app_id`) —— 运行态资源（页面/菜单）。
- 注意：这三张是**运行态应用级权限**；`ctp_manager_resource` 实为**租户配额表**（`active_num/pod_num/db_num`，0 行），不是 CAF 资源表。

### 权限缺口更新（本轮已补 3 项）

| 项 | 状态 |
|---|---|
| `@HasRole` 方法级差异 | ✅ **已核 8 个实体域 controller**（Entity/Index/Event/ReferConfig/AttributeGroup/AttributeSet/EntityGroup/Stereotype）：方法级与类级**完全一致**（如 `selectMatchesAttributeByEntityId` 同为 `{udcAppDesigner,udcSystemAdmin}`；`selectGroupListByConditions` 同为 `{OrgAdmin,udcAppDesigner,udcSystemAdmin}`）→ 实体域内无放宽/收紧 |
| 实体页面 6 tab 的 CAF key | ✅ `ENTITY_CREATE_PAGE_TABS_{BASIC_INFO,ATTRIBUTE_SET,RULE,REFER,EVENT,RELATION,INDEX,DATA}`（§2.7） |
| CAF key → 权限真值 | ✅ **已定位为"非权限"**：CAF=布局位置树+可配置 UI 体系，判定在服务端；权限真值在 `udc_role_resource` + `@HasRole` |
| openAPI 四操作粒度 | ✅ **已补** | `udc_entity.open_api_data` = **逗号分隔方法名清单**（DB 分布：空 1699 / 只读集 16 / 增删改全集 11 / 增改查无删 1）→ 图18 四复选 = 四组方法：**创建**=`create,createBatch,create4bpm`、**删除**=`deleteById,deleteByIds,deleteByComplexConditions`、**更新**=`update,updateBatch,update4bpm`、**查询**=`selectCascadeById,selectCascadeByIds,selectById,selectByIds,selectCountByConditions,selectPageByConditions,selectListByComplexConditions,selectPageByComplexConditions,selectCountByComplexConditions,selectAllChildren,selectListFuncByComplexConditions`（另带 `create4bpm/update4bpm` = BPM 场景）。后端 `EntityOpenApiController`：类级 `@RequestMapping("udc/entity-open-api")` + `@RestApi(group="实体", "实体openApi访问接口")` + `@HasRole({udcAppDesigner,udcSystemAdmin})`，注入 `EntityOpenApiAppService`（1 api）。**数据权限开关** = `udc_entity.permission`（DB 分布 0=1722 / 1=5，全库仅 5 个实体开启） |

---

## 4. 边界（三张地图交叉）

### 4.1 对象归属地图（`entity-settings-source-audit.md` §1，权威）

实体页面**不是一个 JSON**，至少分属 7 组独立对象：

```
Entity / Attribute / AttributeGroup / Index
CtpEnum / CtpEnumItem / UdcEnum / UdcEnumItem
ReferConfig / Relation metadata
Event / EventData / BusinessEvent listener
MicroFlow / EntityRule            ← 规则 tab（含 VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE）
DataFlow / DeductionRule / DeductionMap   ← 扣减、生单（独立，不属字段默认值）
Page / FunctionNode / Excel import-export ← 生成页面/导入导出
```

### 4.2 后端 `@RestApi(group=…)` 官方分组（javap 常量池，GBK 已解码）

实体域：`实体管理接口`(udc/entity) / `实体分组访问接口`(udc/entity-group) / `实体openApi访问接口`(udc/entity-open-api) / `字段分组访问接口`(udc/attribute-group) / `字段集管理接口`(udc/attributeSet) / `实体-数据类型`(udc/data-type) / `索引访问接口`(udc/index) / `参照配置接口`(udc/refer-config) / `事件访问接口`(udc/event) / `版型接口`(udc/stereotype) / `UDC枚举访问接口|分类|项`(udc/udc-enum*) / `数据传输对象接口`(udc/data-transfer-object) / `微流程管理接口`(udc/microflow) / `扣减规则接口`(udc/deduction) / `页面管理`(udc/page-info) / `页面外框`(udc/page-layout) / `页面模板|分类|已公开`(udc/page-template*) / `应用信息访问接口`(udc/application) / `应用发布接口`(udc/runtime) / `应用部署`(udc/deployment) / `设计态操作日志`(udc/operation-log) / `元数据-设计态`(udc/design-metadata) / `页面设计器元数据查询`(udc/meta-data) / `多人编辑控制接口`(udc/multi-edit) / `01沙箱管理`(udc/sandbox) / `udc管理接口`(udc/manager) 等 54 条全表（见 §附录获取法）。

### 4.3 容易越界的四条线

1. **规则 tab ≠ 字段默认值**：规则是 MicroFlow groupType 三组；字段默认值是 `Attribute.defaultValue*` 三个不同字段。
2. **扣减/生单 ≠ 规则 tab**：独立对象 + 独立四表 + 独立 controller。
3. **事件定义 ≠ 事件动作**：`udc_event` 无指向微流程的列。
4. **枚举项 Excel 导入导出 ≠ 实体数据导入导出**：前者 `UdcEnumItemController:126-143`；后者 `POST /udc/entity/preset/create-default-excel-template`（默认模板落 `ctp_excel_export_template`）+ 生成的 `pageEntityController` import/export 路由，两条链不能互替。

---

## 5. 缺口清单（2026-10-12 收口状态：9 项全部落地，含 service 层 body 构造；残余 1 项 UNVERIFIED）

| # | 缺口 | 状态 | 结论/补法 |
|---|---|---|---|
| 1 | **expression 后端 controller** | ✅ **已补** | `com.seeyon.boot.starter.formula.controller.ExpressionController`（jar `boot-starter-formula-5.3.318.jar`，非 udc 系列）。类级 `@RequestMapping("expression")` + `@RestApi("表达式相关接口")`，**无 `@HasRole`**。10 方法见 §5.1 |
| 2 | 实体页面 component → chunk | ✅ **已补** | route chunk 的 `lazy(Promise.all([...]))` 解析（§1.3）；主组件 = 259KB `style-selector` chunk，module 16345 是 545B 壳 |
| 3 | CAF key → 权限真值 | ✅ **已补（结论=非权限）** | CAF = 布局位置树 enum + `Ay` 谓词 + 统一风格徽标；判定数据在服务端；真权限 = `@HasRole` + `udc_role_resource`（§3） |
| 4 | `@HasRole` 方法级粒度 | ✅ **已补** | 8 个实体域 controller 方法级=类级，无放宽（§3） |
| 5 | `VALIDATE` 组规则的 CRUD op | ✅ **已补** | `udcMicroflowSearchEntityRulePost`，`body:{params:{sourceId:<实体id>}}`，返回字段含 **`groupType`**（=VALIDATE/DEFAULT_VALUE/ASSIGN_VALUE 区分键）；同模块导出 `fetchRuleList/searchRuleList/deleteRule` |
| 6 | openAPI 四操作落点 | ✅ **已补** | `udc_entity.open_api_data` 列 + `EntityOpenApiController` + `udcEntityOpenApiSelectGet`；四操作权限粒度未证 |
| 7 | 密级/数据权限开关后端 | ✅ **已补** | 密级 = **stereotype feature**：`com.seeyon.udc.entity.stereotype.feature.SecretLevelFeature` + `feature/secret_level` 资源 + `UdcSecretCheckService`（`udc-starter-runtime`）；数据权限 = `RoleResourceAndDataPermissionAuthCheck` + `udc_entity.permission` 列（`udc_entity` 还有 `attribute_set_ids`=字段集、`parent_entity_id`=主子表、`custom_scalability_id/ids`+`scalability_option_id`=扩展实体、`features`、`open_api_data`） |
| 8 | 6 tab 的 UI↔op 逐一绑定 | ✅ **已补** | tab→组件模块（勘误后正确值 48998/61145/53993/77200/4985/82704，§2.7）→ **service 层 body 构造全部抽出**（§2.8.2/§2.8.3：事件 createEventWithData 完整 body、字段 create/update 分支、实体 appId 注入、索引 idx_/uk_+禁用矩阵、规则 checkMicroFlowCaption、参照三步配置）；**参照提交链坐实（7dcbc10）**：53993.onClick→e1→module332.Jt→udcApolloQuery(有id?UpdateConfigInfo:CreateConfigInfo)，§2.8.3③ 关闭 |
| 9 | 6 tab tab 定义对象 | ✅ **已补** | `R` 对象 8 key + CAF 常量 + `switch(e)` 显示条件 + 组件绑定（§2.7） |

### 5.1 ExpressionController 完整 API（Java class 常量池直解，`boot-starter-formula-5.3.318.jar`）

```
@RestController  @RequestMapping("expression")  @RestApi("表达式相关接口")   ← 无 @HasRole
extends com.seeyon.boot.starter.web.BaseComponentController；@Autowired ExpressionAppService
```

| HTTP | 方法 | 入参 | 返回 | 用途（@RestApiOperation 原文） |
|---|---|---|---|---|
| POST `/expression/schema` | `selectSchemaByParamType` | `VariableSchemaLoadDto`（**含 `serverName`**，由 `getServerName()` 用 `requestURI.split()` 回填） | `ListResponse<SchemaStructureDto>` | 根据参数类型信息加载可选变量schema ← 用户抓的 `/expression/schema` |
| POST `/expression/transform` | `transform` | `ExpressionSaveDto` | `SingleResponse<ExpressionDefinitionDto>` | 转换表达式 ← 用户抓的 `/expression/transform` |
| POST `/expression/preset/list` | `listPresetInfo` | `PresetLoadConditionDto` | `SingleResponse<PresetInfoDto>` | **加载表达式组件预置信息(包含系统变量、函数等信息)** ← 用户抓的 `/expression/preset/list` |
| POST `/expression/check` | `check` | `ExpressionSaveDto` | `SingleResponse<Boolean>` | 校验表达式 |
| GET `/expression/operator/list` | `listAllOperator` | — | `SingleResponse<QuickSymbolDto>` | 加载所有的操作符 |
| GET `/expression/system/values` | `getSystemVariableResult` | — | `SingleResponse<Map>` | 获取所有的系统变量计算值 |
| GET `/expression/system/values/{type}` | 同上 | `@PathVariable type` | `SingleResponse<Map>` | 按类型获取系统变量 |
| GET `/expression/system-variable/list` | `listSystemVariable` | — | `ListResponse<SystemPresetVariableDto>` | 加载所有系统变量定义 |
| POST `/expression/system-variable/list/by-condition` | `listSystemVariableByCondition` | `@MultiRequestBody Map` | `ListResponse<SystemPresetVariableDto>` | 按条件加载系统变量定义 |
| POST `/expression/system/list` | `loadSystemVariable` | `@MultiRequestBody name`（`@ParameterInfo("系统变量名称")`） | `SingleResponse<SystemPresetVariableDto>` | 加载系统变量信息 |

同 jar 关键类：`ExpressionService` / `ExpressionEvaluator` / `ExpressionValidator` / `ExpressionPresetRunner`（预置公式装载）/ `ExpressionCache` / `ExpressionConfigUtil` / `ExpressionDesignDataDto` / `ExpressionToken` / `ExpressionSaveDto` / `ExpressionDefinitionDto`。

**注意**：类级 mapping 是 `expression`（无 `udc/` 前缀），实际外部路径 `/service/udc/expression/*` 的 `udc/` 段来自网关/`BaseComponentController` 拼接；方法级路径 `/schema`、`/transform`、`/check` **带前导斜杠**而 `preset/list`、`operator/list` 不带 —— 照抄，别统一。

---

## 6. 附录：本轮证据获取法（可复现）

- **54 controller 权限/分组表**：读 `docs/audit/artifacts/udc-web-5.3.517-javap/*.txt` 的 **GBK**（`raw.decode("gbk")`，按 utf-8 读全是乱码），取 `SourceFile` 之后常量池：`#N = Utf8 Lcom/seeyon/boot/annotation/HasRole;` 后连续 Utf8 = 角色；`RestApi;` 后 1~3 个 Utf8 取非注解非路径者 = group 中文；`RequestMapping;` 后下一个 Utf8 = 类级 mapping。
- **左侧菜单/chunk**：本地 `webpack-modules` 中文件名含 `app-style-designer` 且 size≈44411 的 chunk（**别按 `p.name[:70]` 截断名选文件，会撞一堆同名**）。
- **Route 表**：同族含 `keyFun` 且 <20KB 的 chunk（`f96d7e03-88040.js`），39 条 `title/path/component`。
- **op 全集**：`scratch/udc-pod-chunks/src_redux_store_ts.14dc061e.js`（2,530,725 字节，791 个 `udc*` op）。
- **11 张截图**：`<HERMES_HOME>\images\clip_20261012_14153{2,3}_*` ~ `_142323_18.png`（用户 2026-10-12 提供）。
