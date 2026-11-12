# UDC 设计器 15 导航活体审计 · 第 2 轮（深入子页/tab）

日期：2026-10-12 深夜
接续：`NAV-LIVE-CAPTURE-20261012.md`（第 1 轮：9 个导航域入口 API 全 LIVE PASS）。
方法同前：CDP 9222 + cookie 注入 + 壳内真实点击。原始抓包 `cache/scratch/udc-live-capture*.jsonl`（capture3-15，未全入库，关键片段摘录如下）。

## 1. 本轮新证实的端点（全部 LIVE PASS，BOOT_0000）

### 规则域（udc）
| 端点 | 触发 | 结果 |
|------|------|------|
| `udcDeductionMapAppAppGet` | 左侧切"扣减规则" | 扣减映射列表（空） |
| `udcMicroFlowGroupSelectByTypePost` | 规则页分组树 | 分组：默认分组(preset)/日志专用/… |
| `udcMicroflowSearch` | 微流程列表 | total=9 真实数据：`{id,name:SyncNowData,caption:"1.0 立即同步",type:CUSTOM,triggerType:MANUAL,groupType:DEFAULT,state:RELEASE,publishState:UNPUBLISH,…}` |
| `udcMultiEditLockPost` / `udcMultiEditUnlockPost` | 打开实体/参照详情 | **多编辑锁机制**：holdLock/expireTimeStamp，退出自动解锁 |
| `udcEntityGet`（单查）+ `udcAttributeSetSelectByAppidPost` | 实体-基本 tab | 实体全量属性 + 属性集 |
| `udcStereotypeListGet` | 实体-基本 tab | 构造型：standard(caption 标准)，availableFeatures=[secretLevel] |
| `udcEntityOpenApiSelectGet` | 实体-基本 tab | OpenAPI 选项：创建=[create,createBatch,create4bpm]、删除=… |
| `udcApplicationFetchLastVersionMetadataPost&udcFeatureListGet&udcScalabilityOptionSelectByApp…`（batch） | 实体-基本 tab | 特性列表 + 扩展选项 |
| `udcReferConfigGroupListPost&udcMetaDataSelectPageInfoListPost`（batch） | 实体-参照 tab | 参照配置组 + 元数据分页 |
| `udcMetaDataSelectAggregationEntityEntityGet` | 实体-参照 tab | 聚合实体（含平台预置 `com.seeyon.organization.domain.core.entity.OrgMemberMetadata`） |
| `udcEventListPost` | 实体-事件 tab | 事件列表 |
| `udcIndexEntityListPost` | 实体-索引 tab | 索引列表 |
| `udcEntityAssociationEntityAppGet&udcDataTypeDataT…`（batch） | 实体-字段 tab | 关联实体 + 数据类型 |

### BI 域（cdp-data）
| 端点 | 触发 | 结果 |
|------|------|------|
| `/service/cdp-data/udc/stream/get-list-page` | BI-数据流 tab | 数据流分页（空） |
| `/service/cdp-data/udc/indicator/derive/select-page-list` | BI-指标管理 tab | 派生指标分页（空） |
| `/service/cdp-data/udc/report-design/get-report-page` | BI-报表管理 tab | 报表分页（空） |

BI 页签结构（页面 DOM 实证）：数据分析 = **数据集 / 数据流 / 指标管理 / 报表管理** 四个 tab。

### 流程域（bpm）
页面 DOM 实证：流程页 = **流程模板 / 流程配置** 两 tab；模板分"固定流程/自由流程"两类，空态文案"前往创建"。API 面仅见 `bpmTemplateSelectByAppIdGroupByTagPost`（设计态）。

### 部署/沙箱（应用壳级，设计器所有页面共用）
| 端点 | 用途 | 结果 |
|------|------|------|
| `POST /service/udc/deployment/latest-test-info` | 最近测试部署信息 | LIVE PASS |
| `GET /service/udc/application/user-role?appName=udc` | 当前用户全部角色码 | LIVE PASS（含 admin-datamigration…Admin） |
| `GET /service/udc/sandbox/delta-build-info/{appId}` | 沙箱增量构建状态 | state=NONE |
| `udcSandboxSelectAppGet` / `udcSandboxBuildInfoAppGet` | 沙箱状态/构建日志 | **本轮发现该 app 最近一次构建 FAIL**：`appVersion 1.0.0 showVersion 1.0.2 state FAIL failReason 流水线回调:业务异常[后端失败:…backBuild.log ERROR Failed to execute…`，build progress 82% 失败 |
| `udcApplicationAppVersionAppGuidPost` | 版本列表（含失败原因） | LIVE PASS |
| `udcOperationLogSearchInitDataAppGet` | 设计日志筛选元数据 | **operation log subModule 全集**：生单规则=DATAFLOW、扣减规则=DEDUCTION、菜单节点=FUNCTION_NODE、控件=WIDGET、栏目节点=PORTLET、页面=PAGE、外框=LAYOUT、实体=ENTITY_BASE、实体字段=ENTITY_ATTR…（操作日志模块枚举的权威来源） |

## 2. 机制新知

1. **左导航真实可见集 = 9 项**：应用/实体/菜单/规则/流程/BI/栏目/设置/角色（`a[href]` 全量）。bundle 常量里的 15 项中：基本信息、参数、操作权限、外框、高级设置**不在当前渲染的导航里**——它们按 app feature 开关显隐（外框在「页面」tab 组内、操作权限=「角色」、参数/高级设置当前 app 未启用）。此前 APP-DESIGN-NAV-INVENTORY §1 的 15 项是全集常量，不是每个 app 都出现。
2. **微流程列表的分组树数据源**：`udcMicroFlowGroupSelectByTypePost`（默认分组 preset=true）+ `udcMicroflowSearch`（按 group 过滤）。列表"暂无数据"但接口 total=9 的原因：**未选左侧分组节点时列表区不渲染**；选中"数据迁移"分组后树形列表显示 9 条（1.0 立即同步/1.1 获取迁移进度/…/1.11 枚举定时同步(草稿)）。
3. **微流程画布入口仍未打开**：树节点单击只选中，双击/hover 均未触发设计器加载（URL 未变、无 microflowGet 请求）。画布打开方式待查（可能是右键菜单或行内图标）。**UNVERIFIED**：`rule/microflow?appId&id=` 深链路由被重定向回规则列表（防深链）。
4. **实体详情多编辑锁**：进入实体/参照编辑态先 `udcMultiEditLockPost`（resource=entityId，返回 holdLock+expireTimeStamp），离开 `udcMultiEditUnlockPost`。自动化操作实体时若强杀浏览器会留锁。
5. **应用版本状态机**：`udcApplicationAppVersionAppGuidPost` 返回每版 state（FAIL 带完整 failReason + backBuild.log 链接）。当前该 app 1.0.2 构建失败（进度 82%，backBuild.log ERROR），与沙箱构建 state=FAIL 一致——**该 app 的沙箱/发布链路当前是坏的**，自动化搭建若依赖"构建成功"会被这个挡住。

## 3. 完成度更新（对 APP-DESIGN-NAV-INVENTORY §7）

| 菜单 | 上轮 | 本轮 | 依据 |
|------|------|------|------|
| 规则（微流程/生单/扣减） | 55% | 70% | 三子域列表+分组+数据结构全 LIVE；画布打开链 UNVERIFIED |
| 实体 | 97% | 98% | 基本/字段/参照/事件/索引五 tab 全部 API LIVE；OpenAPI/stereotype/锁机制补齐 |
| BI | 55% | 65% | 四 tab 页签结构 + 数据集/数据流/派生指标/报表四分页 API LIVE（均空数据） |
| 流程 | 30% | 35% | 流程模板/配置双 tab + 固定/自由分类 DOM 实证；设计器 API 面仍缺 |
| 应用（基本信息/依赖/版本/沙箱） | 70% | 80% | 版本状态机+沙箱构建链+角色码接口 LIVE，发现 1.0.2 构建失败事实 |
| 页面/菜单/外框/设置/角色 | 不变 | 不变 | 第 1 轮已覆盖入口 |

## 4. 未尽事项（下轮）

1. 微流程画布打开的真实交互（右键/图标/行菜单）→ 抓 `udcMicroflowGet`/画布保存 API
2. 页面设计器（page-manage 主 tab）——导航无该入口，需从「菜单」树打开页面节点或从实体默认页进
3. BI 写链（新建数据集/报表）与流程模板创建（需 app 沙箱构建可用，当前 1.0.2 FAIL 会挡）
4. 参数/高级设置入口的 feature 开关来源（bundle 常量 vs 后端 feature 接口）
