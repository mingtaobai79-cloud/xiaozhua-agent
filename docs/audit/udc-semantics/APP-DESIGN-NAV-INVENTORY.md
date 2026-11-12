# UDC 设计器左导航全量清单 + 微前端架构取证

日期：2026-10-12
主线：`<XIAOZHUA_AGENT_ROOT>`
环境：test2 (`lowcode-test2.example.com`)，UDC 镜像 5.3.496（`config/environments.yaml`）
证据来源：真实前端 bundle（OSS 拉取，Cookie 鉴权）；来源 chunk 全部列在每节。

## 0. 本文件修正的认知错误

在此之前 `page-menu-source-audit.md` 等只覆盖了「udc 内部页面」，把 BI/流程/角色权限当作 udc 内部功能。
实测：**设计器左导航 15 个菜单里，5 个是挂载外部微应用（Module Federation），不是 udc 自己的代码**。
这解释了此前「udc 主 store 里 0 个 BI op / 0 个流程 op」的现象——它们根本不在 udc 的 op 命名空间。

## 1. 左导航 15 菜单（权威来源：真实 bundle 常量）

来源 chunk：`udc/src_components_app-design_app_components_theme_app-style-designer-model_tsx-...7042b6.f96d7e03.js`（575700B）
导航项结构：`{name, path, identityCAF, type}`

| # | 菜单名 | path | identityCAF | type |
|---|--------|------|-------------|------|
| 1 | 应用 | `/app-design/basic-info` | `MENUS_FORM_BASIC_INFO` | formBasicInfo |
| 2 | 基本信息 | `/app-design/app-basic-info` | `MENUS_BASIC_INFO` | basicInfo |
| 3 | 实体 | `/app-design/entity` | `MENUS_ENTITY` | entity |
| 4 | 菜单 | `/app-design/page-manage/functions` | `MENUS_FUNCTION_DESIGN` | functionDesign |
| 5 | 页面 | `/app-design/page-manage` | `MENUS_PAGE_DESIGN` | pageDesign |
| 6 | 外框 | `/app-design/pageFrame` | `MENUS_PAGE_FRAME` | pageFrame |
| 7 | 参数 | `/app-design/third-form-param` | `MENUS_THIRD_FORM_PARAM` | thirdFormParam |
| 8 | 操作权限 | `/app-design/third-form-permission` | `MENUS_THIRD_FORM_PERMISSION` | thirdFormOperationAuthority |
| 9 | 规则 | `/app-design/rule` | `MENUS_RULE` | rule |
| 10 | 流程 | `/app-design/flow` | `MENUS_WORKFLOW` | workFlow |
| 11 | BI | `/app-design/analytic-statistics` | `MENUS_ANALYTIC_STATISTICS` | analyticStatistics |
| 12 | 栏目 | `/app-design/page-manage/portlet` | `MENUS_PORTLET` | portlet |
| 13 | RPA | `/app-design/cip-rpa` | `MENUS_CIP_RPA` | rpa |
| 14 | 设置 | `/app-design/basic-setting` | `MENUS_BASIC_SETTING` | basicSetting |
| 15 | 高级设置 | `/app-design/advance-setting` | `MENUS_ADVANCE_SETTING` | advanceSetting |

CAF 常量全集（`src_redux_store_ts.14dc061e.js`，`n.d(t,{un:...})`）另有 `MENUS_BUSINESS_RULES`（业务规则）在枚举里但不在当前导航数组——业务规则是「规则」下的子页/后续版本入口。

## 2. 页面 chunk 清单（权威来源：udc remoteEntry `e.u` 映射）

来源：`udc/remoteEntry.js`，chunk var `e`，pattern `"NAME"===e?""+e+".HASH.js"`。app-design 相关 40 个 chunk：

```
analytic-statistics_index_tsx                              -> ext cdp-data/AnalyticStatistics   <-- BI 外挂
app-home_index_tsx                                         -> udc 内部
app-home_space-manage_SpaceManger_tsx                      -> udc 内部（空间管理）
basic-info_index_tsx (+icon-library)            85245B     -> udc 内部（应用/表单基础信息，最大）
basic-setting_index_tsx (+basic-data dst)       37801B     -> ext ctp-user/RolePermission       <-- 设置外挂角色权限页
business-rules_index_tsx                          601B      -> 壳（延迟加载）
cip-rpa_index_tsx                                 340B      -> ext cip-rpa/CipRpa                <-- RPA 外挂
entity-modeling_custom-extension_index_tsx                 -> udc 内部（自定义扩展）
entity-modeling_entity-collections_index_tsx                -> udc 内部（实体集合）
entity-modeling_entity-field_components_rule-Formulas      -> udc 内部（字段公式）
entity-modeling_entity-fieldset_index_tsx        48371B     -> udc 内部（字段集）
entity-modeling_enum-manger_enum-field_index_tsx           -> udc 内部（枚举管理）
excute-log_index_tsx                              292B      -> 壳
extension-plan_index_tsx                         21923B     -> udc 内部（扩展方案）
flow_FlowEntry_tsx                                969B      -> ext bpm/Flow                      <-- 流程外挂
page-manage_main_index_tsx                        493B      -> 壳（页面设计主容器）
page-manage_main_page-frame_tsx                   460B      -> 壳（外框 tab）
page-manage_main_portlet_tsx                      455B      -> 壳（栏目 tab）
page-manage_main_snapshot_tsx                     457B      -> 壳（快照 tab）
page-manage_main_sub-page_tsx                     456B      -> 壳（子页面 tab）
page-rules_index_tsx (+page-content)             6090B      -> udc 内部（页面规则）
role-permission_index_tsx                         634B      -> ext ctp-user/RolePermission       <-- 操作权限外挂
rule_index_tsx (+udc-graph dist)                59950B     -> udc 内部（规则主容器）
rule_microflow_index_tsx / entity-rule / page-rule          -> udc 内部（微流程：实体规则/页面规则）
rule_dataflow_relation-graph_index_tsx         131929B     -> udc 内部（数据流关系图，最大）+ entry/log-content
rule_deductflow_log-content_index_tsx             7434B     -> udc 内部（扣减流日志）
template-manage_index_tsx                         9311B     -> udc 内部（模板管理）
theme-configuration_index_tsx                      231B     -> 壳（主题配置）
```

判定规则：chunk 内出现 `url:".../remoteEntry.js",scope:"...",module:"..."` 即外挂微应用。

## 3. 外挂微应用清单（Module Federation）

| 子应用 | remoteEntry | scope | 被哪个菜单挂载 | 模块 |
|--------|-------------|-------|----------------|------|
| BI / 分析统计 | `/cdp-data/remoteEntry.js` | `cdp-data` | 菜单 11 | `AnalyticStatistics` |
| 流程 | `/bpm/remoteEntry.js` | `bpm` | 菜单 10 | `Flow` |
| 角色权限 | `/ctp-user/remoteEntry.js` | `ctp-user` | 菜单 8、设置 | `RolePermission` |
| RPA | `/cip-rpa/remoteEntry.js` | `cip-rpa` | 菜单 13 | `CipRpa` |
| 门户 | `/portal/remoteEntry.js` | `portal` | 栏目/门户 | `Entry` |

其余 `v8/ctp/office/analyze/analysis/dashboard/datareport/mobile` 等 `remoteEntry.js` 全 404，排除。

### 3.1 各子应用 exposes（对外暴露模块）

`/cdp-data/remoteEntry.js`（75796B）exposes：`./AnalyticStatistics ./Entry ./MyReport ./ReportCategory ./ReportComponent ./ReportSelect ./SearchCloud ./SearchCloudSet ./SearchConfig ./SearchInput`

`/bpm/remoteEntry.js`（74237B，245 chunks）exposes（32）：
`./ActionSetting ./AdvancedSetting ./AppFlowList ./AppFlowPath ./ApplicationDetail ./ApprovalCard ./BasicInfo ./CollaborationPage ./ConsultDetail ./ConsultList ./DoneList ./EditFlow ./Entry ./Flow ./FlowDesignList ./FlowDesinEdit ./FlowPath ./FollowList ./FormAndNodePermission ./OperationAuth ./PendingList ./ProcessAuthority ./ProcessManageRefDesign ./ProcessManageRefRuntime ./ProcessNode ./QuickProcess ./ReadyList ./SearchAndReplace ./SentList ./SuperviseList ./SuperviseSetting ./ThirdRemoteComp`

`/portal/remoteEntry.js`（33444B，111 chunks）exposes（16）：
`./BackstageManageEntry ./BaseInfo4App ./BulletinBoardsEditor ./Entry ./MainPortalDesign ./MemorabiliaContentSetting ./NavMenuData ./OtherSystemAccounts ./PortalSetting ./RichText ./SettingTabPane ./SpaceDesignAndSpacePreview ./SpaceManageEdit ./SpaceManageTable ./TemplateLibrary ./WebMenuModal`

`/ctp-user/remoteEntry.js`（15328B，68 chunks）exposes：见 §5。
`/cip-rpa/remoteEntry.js`（397B）——极薄壳，见 §6。

## 4. BI 域（分析统计 / cdp-data）API 全表

来源 chunk：`cdp-data/src_services_request_ts.8711f912.js`（17726B）。
基址变量（同 chunk）：
```
j = "/cdp-am"       语义模型 / 指标（REST）
R = "/cdp-df"       数据流（REST）
T = "/udc/cdp-data"
x = window.isInUdc ? "/cdp-data/udc" : "/cdp-am"
P = window.isInUdc ? "/cdp-data/udc" : "/cdp-df"
```
即 **UDC 内嵌时（isInUdc）基址切换为 `/cdp-data/udc`**；独立 BI 站点用 `/cdp-am`、`/cdp-df`。
请求统一走 `postApi/`ajax`，并在 body 注 `appName` + `cdpDataStatus`（内嵌=DESIGN，独立=RUNNING）。

| URL 键 | 路径 | 域 |
|--------|------|-----|
| renameModalFolderUrl | `/cdp-am/semantic-model/rename-folder` | 语义模型 |
| delModalFolderUrl | `/cdp-am/semantic-model/delete-folder` | 语义模型 |
| createMFolderUrl | `/cdp-am/semantic-model/create-folder` | 语义模型 |
| deleteModalUrl | `/cdp-am/semantic-model/delete` | 语义模型 |
| deleteMBatchUrl | `/cdp-am/semantic-model/delete-batch` | 语义模型 |
| getModelDetailUrl | `/cdp-am/semantic-model/get-list-page` | 语义模型 |
| getModalListUrl | `/cdp-am/semantic-model/get-category-tree` | 语义模型（目录树） |
| getModalListUrl(树) | `/cdp-data/udc/semantic-model/get-model-tree` | 语义模型（模型树） |
| createSFolderUrl | `/cdp-df/stream/create-folder` | 数据流 |
| renameSFolderUrl | `/cdp-df/stream/rename-folder` | 数据流 |
| delSFolderUrl | `/cdp-df/stream/delete-folder` | 数据流 |
| delSBatchUrl | `/cdp-data/udc/stream/delete-batch` | 数据流 |
| delStreamUrl | `/cdp-data/udc/stream/delete` | 数据流 |
| getStreamListAddBillUrl / AddUrl | `/cdp-df/stream/get-stream-tree` | 数据流 |
| getStreamListDetailUrl | `/cdp-data/udc/stream/get-list-page` | 数据流 |
| getStreamListUrl(分类) | `/cdp-df/stream/get-category-tree` | 数据流 |
| getStreamListUrl(树) | `/cdp-df/stream/stream-tree` | 数据流 |
| createIdcModalFolderUrl | `/cdp-am/indicator/table-category/create` | 指标·汇总表 |
| delIdcModalFolderUrl | `/cdp-am/indicator/table-category/delete` | 指标·汇总表 |
| renameIdcModalFolderUrl | `/cdp-am/indicator/table-category/update` | 指标·汇总表 |
| getIdcModalListPublishUrl | `/cdp-am/indicator/table-category/category-tree/published` | 指标·汇总表 |
| getIdcModalListUrl(树) | `/cdp-am/indicator/table-category/get-category-tree` | 指标·汇总表 |
| getIdcModalListUrl(表树) | `/cdp-am/indicator/table-category/get-table-tree` | 指标·汇总表 |
| deleteIndicatorUrl | `/cdp-data/udc/indicator/table/delete` | 指标·汇总表 |
| deleteIndicatorBatchUrl | `/cdp-data/udc/indicator/table/delete-batch` | 指标·汇总表 |
| getSummaryDetailUrl | `/cdp-data/udc/indicator/table/select-page-list` | 指标·汇总表 |
| createAtomFolderUrl | `/cdp-am/indicator/atom/category/create` | 指标·原子 |
| delAtomFolderUrl | `/cdp-am/indicator/atom/category/delete` | 指标·原子 |
| renameAtomFolderUrl | `/cdp-am/indicator/atom/category/update` | 指标·原子 |
| delAtomUrl | `/cdp-am/indicator/atom/delete` | 指标·原子 |
| delAtomBatchUrl | `/cdp-am/indicator/atom/delete-batch` | 指标·原子 |
| getAtomListDetailUrl | `/cdp-am/indicator/atom/select-page-list` | 指标·原子 |
| getAtomListUrl | `/cdp-am/indicator/atom/category/get-category-tree`、`/cdp-am/indicator/atom/category/get-atom-tree` | 指标·原子 |
| createDeriveFolderUrl | `/cdp-am/indicator/derive/category/create` | 指标·派生 |
| delDeriveFolderUrl | `/cdp-am/indicator/derive/category/delete` | 指标·派生 |
| renameDeriveFolderUrl | `/cdp-am/indicator/derive/category/update` | 指标·派生 |
| delDeriveUrl | `/cdp-data/udc/indicator/derive/delete` | 指标·派生 |
| delDeriveBatchUrl | `/cdp-data/udc/indicator/derive/delete-batch` | 指标·派生 |
| getDeriveListDetailUrl | `/cdp-data/udc/indicator/derive/select-page-list` | 指标·派生 |
| getDeriveListUrl | `/cdp-am/indicator/derive/category/get-category-tree`、`/cdp-data/udc/indicator/derive/get-derive-tree` | 指标·派生 |

BI 域结构 = **语义模型（Semantic Model）+ 数据流（Stream）+ 指标（汇总表/原子/派生，各带分类树）**，每类都有 folder CRUD + 树 + 分页列表。响应构造见 `z(e)`：`status<500` 直返；`code` 含 `0000`→200；含 `1004`→`noPermission`（"没有授权！"）。

## 5. 角色权限域（ctp-user / RolePermission）

来源：`ctp-user/remoteEntry.js`；页面 chunk `ctp-user/src_pages_role-permission_entry_tsx.ebba5ac6.js`（16180B）。
被菜单 8「操作权限」和「设置」挂载。页面结构：角色列表 + 编辑弹窗。
弹窗字段可见：`name`（角色名，object 时 JSON.stringify）、`relationOrgRoleCode`（关联组织角色码，逗号分隔数组）。
读取详情走 `m.Qk(id)` → 返回 `{content}`；保存走 `useDispatch` 的 roleListReducer action。
（完整 API 面待补：需挖 ctp-user 其余 service chunk。）

## 6. RPA 域（cip-rpa / CipRpa）与门户（portal）

- **RPA**：`/cip-rpa/remoteEntry.js` 仅 397B（空壳，无 chunk 映射），说明 test2 该环境未部署 CIP/RPA 子应用内容，或走其它加载路径。**当前状态：BLOCKED（环境未提供内容）**。
- **门户**：`/portal/remoteEntry.js`（111 chunks，16 exposes）。服务层 chunk 含 `apps/portal-manage/services/home-setting`、`apps/designer/services/select-resource`、`select-cmpts`。门户设计 = 主页设计（MainPortalDesign）+ 空间管理（SpaceManage*）+ 栏目/公告（BulletinBoards/Memorabilia）+ 模板库（TemplateLibrary）+ 导航菜单（NavMenuData）。

## 7. 各菜单完成度（诚实版，覆盖「说过的应用/实体/设置」）

| 菜单 | 静态证据 | 活体验证 | 完成度 | 缺口 |
|------|----------|----------|--------|------|
| 1 应用 basic-info | 85KB chunk 八面 GraphQL | 部分 | 70% | testPage/testVersion/version/dependent/team/member/state 7 个 tab 未活体 |
| 2 基本信息 app-basic-info | chunk 未细挖 | 无 | 20% | 整块未做 |
| 3 实体 entity | ENTITY-PAGE-INVENTORY.md 373 行 | 多轮 | 95% | 写链未验（见下） |
| 4 菜单 function_design | page-menu-source-audit.md | 无 | 45% | 菜单功能节点写入未活体 |
| 5 页面 page_design | page-menu-source-audit.md | 无 | 40% | 设计器保存/控件/事件绑定链未活体 |
| 6 外框 pageFrame | page-menu-source-audit.md（PageLayout） | 无 | 40% | 外框 CRUD 未活体 |
| 7 参数 third-form-param | 无 | 无 | 5% | 整块未做 |
| 8 操作权限 role-permission | ctp-user entry 16180B | 无 | 25% | 角色 CRUD 未活体 |
| 9 规则 rule（含微流程） | microflow-source-audit.md 18KB | 实体规则读活体 | 55% | 规则列表页/画布保存、页面规则、数据流、扣减流未活体 |
| 10 流程 workflow | bpm 32 exposes | 无 | 15% | 流程设计器 API 面未挖、未活体 |
| 11 BI analytic-statistics | §4 全表 43 接口 | 无 | 40% | 未活体（只读测试可做） |
| 12 栏目 portlet | portal 16 exposes | 无 | 30% | 未活体 |
| 13 RPA cip-rpa | 397B 空壳 | 无 | 0% | 环境未提供内容（BLOCKED） |
| 14 设置 basic-setting | SETTINGS-TABS-CALLCHAIN.md 27KB | 多轮 | 85% | 少量 tab |
| 15 高级设置 advance-setting | 无 | 无 | 5% | 整块未做 |

**结论：15 菜单里 6 个 ≤25%（参数、RPA、高级设置、基本信息、流程、操作权限），BI/页面/菜单/外框/规则/栏目都在 30-55% 区间。距「每个地方都测试到」还有显著距离。**

## 8. 下一步（审计测试计划）

按证据可获取性排序：
1. **BI 域活体只读**：对 §4 的树接口逐个 GET/POST（`get-category-tree`、`get-model-tree`、`stream-tree`），验证基址 `/cdp-data/udc` 与 appId 注入。→ 可立即做。
2. **流程域 API 面**：挖 bpm 245 chunks 里的 service 层，出流程设计器 API 表。→ 大工作量。
3. **角色权限 CRUD 只读**：列角色列表接口。→ 小。
4. **页面/菜单/外框**：从 page-menu-source-audit.md 的 Controller 路径转前端 GraphQL op，做只读查询验证。
5. 应用 7 个 tab、参数、高级设置：逐块静态+活体。

验收门槛：每项须有 (a) 真实请求 URL/方法/body；(b) 真实响应（区分 HTTP 200 vs 业务成功）；(c) 与源码/chunk 的对应证据。
