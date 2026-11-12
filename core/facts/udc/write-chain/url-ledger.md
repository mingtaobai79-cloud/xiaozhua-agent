
## 前端页面 URL 台账（zzprobe 全链测试期间实测，2026-09-30）

> 用户纪律：访问过的每个页面、每条网关分发路径都必须记录。持续追加。

### 全局结构
- 网关统一入口: `https://lowcode-test2.example.com`
- REST 前缀: `/service/{appId或服务名}/...`（网关按 appId/服务名分发到对应 pod）
- 平台服务名: `udc`(设计态 udc-web) / `udc-runtime`(运行态) / `ctp-user`(登录) / `portal` / `app-common` / `ctp-application` / `organization` / `ctp-message`

### 页面路由（前端 SPA 基座 /main）
| 页面 | URL | 说明 |
|---|---|---|
| 登录 | /login/ | 密码+短信 |
| 门户 | /main/portal | 登录后首页 |
| UDC应用页面 | /main/portal/{appName}/{pageName} | 运行态页面(如 /main/portal/znxmglptcopy5791640252914287064/jidukaoheliebiaoPcopy) |
| 后台管理-应用管理 | /main/backstageManage/udc/apps | 应用列表+新建+设计/测试/发布 |
| 后台管理-应用设计器 | /main/child-frame/udc/app-design/app-basic-info?appId={数字appId} | 实体/菜单/规则/流程/BI/栏目/设置/角色 |
| 应用设置(首页管理) | /main/portal/portalManage/detail/{appId} | 基本信息/PC空间/移动空间 |
| 生单规则 | /main/portal/{appName}/_dataflow | 特殊页 |
| 枚举管理 | /main/portal/{appName}/_enum | 特殊页 |
| 导入导出模板 | /main/portal/{appName}/_excelSetting | 特殊页 |
| 标签模板 | /main/portal/{appName}/_labelPrintTemplateManage | 特殊页 |
| 微前端 remote | /{appName}/remoteEntry.js | 每个应用一个 remote(如 /udc/remoteEntry.js, /portal/remoteEntry.js, /portal-frame/remoteEntry.js) |
| 设计器子框架 | /main/child-frame/udc/... | app-design 系列页面 |

### 关键接口（网关分发实测）
| 接口 | 方法 | 用途 |
|---|---|---|
| /service/udc/application | POST | 创建应用(ApplicationDto: caption/name/code/featureType/terminalType)——**持久化不完整, 建应用须走 UI** |
| /service/udc/application/{id} | GET | 按 id 查应用（缺宿主信息时报错） |
| /service/udc/application/delete | POST | 删除应用(裸数字 body) |
| /service/udc/application/delete-rename | POST | 删除(被改名过, 字节码注释:'有人在删除应用暂时改名') |
| /service/udc/application/delete-by-guid | POST | 按 guid 删 |
| /service/udc/entity | POST | 创建/查实体（appId 数字 + name + stereotype 等） |
| /service/udc/entity/{id} | GET | 查实体 |
| /service/udc/runtime/deploy-normal | POST | 部署（deployDto.appId 要 13位数字 appId, 非雪花 guid） |
| /service/{appName}/app-info/deploy-info | GET | 查应用部署信息（网关按 appName 路由到沙箱 pod） |
| /service/udc/runtime/meta-data/select-entity | POST | 元数据查实体（fullName+appName） |
| /service/udc/graphql | POST | UDC GraphQL 面（udcEntityDeletePost 等mutation） |
| /service/ctp-user/auth/token | POST | 登录换 token |
| /service/ctp-application/appcenter/search-app-edition | POST | 应用中心查询（参数形态未明, BOOT_3000） |
| /service/portal/config?portalType=PC | GET | 门户配置 |

## 记录分类纪律（2026-09-30 用户指令）
每个模块的探索结果按三类归档：
- **【事实】**：可直接记录的（URL、接口路径、字段结构、报错原文、页面元素位置）→ 入台账/事实格
- **【需组装配置】**：UI 操作序列才能完成的（表单填写顺序、依赖选择、级联配置）→ 记操作步骤
- **【通道判定】**：接口能做 vs 只能页面做 → 每个功能标注通道

## 模块通道判定表（zzprobe 全链测试）
| 功能模块 | 接口通道 | 页面通道 | 状态 |
|---|---|---|---|
| 创建应用 | ❌ REST持久化不完整 | ✅ backstageManage/udc/apps 表单 | UI已通 |
| 创建实体 | ⚠️ REST /udc/entity 对已发布应用可用 | ✅ 设计器实体tab+plus按钮 | 双通道已通 |
| 菜单管理 | graphql: udcFunctionSelectFunctionTreePost | ✅ 添加菜单表单(页面名称/类型/实体) | ✅ UI已通(zzprobe首页) |
| 应用部署 | ✅ deploy-normal (appId需13位) | ✅ 设计器"测试"按钮 | 接口appId形态待解 |
| 字段添加 | 待测(疑似仅UI) | ✅ 设计器实体详情"添加" | UI已通(标题字段) |
| 枚举管理 | graphql: udcEnumCategorySearch/udcEnumSearchNoPagePost | ✅ 设置tab→枚举管理→lined-plus→表单 | ✅ UI已通(枚举+2枚举项) |
| 角色 | udcCtpUserRoleSelectListPost 等 | ✅ 角色tab | 只读已探(3预置角色) |
| BI | cdp-data 服务(数据集/数据流/指标/报表) | ✅ BI tab | 探明(独立服务) |
| 流程 | bpm 服务 bpmTemplateSelectByAppIdGroupByTagPost | ✅ 流程tab | 探明(独立bpm服务) |
| 栏目 | udcPortletSelectByAppIdAppGet | ✅ 栏目tab | 探明(空,待建) |

## 设计态协议台账（2026-10-01 zzprobe 全链实测补录）

### 【事实】REST/GraphQL 接口清单（全部 LIVE 验证）
| 功能 | 通道 | 接口 | 参数要点 |
|---|---|---|---|
| 页面定义查询 | GraphQL | udcPageInfoSearchNoPagePost | params.appId=数字appId → 14页面全量(含layoutInfo/schemaState) |
| 页面删除 | GraphQL | udcPageInfoDeletePost | body.id — **空页面会阻断一致性检测**(UDC_CE_PAGE_03907) |
| 页面更新 | GraphQL | udcPageInfoUpdatePost | 存在, 完整参数待抓(需真实保存请求样本) |
| 应用创建 | REST | POST /service/udc/application | **持久化不完整!** 缺宿主信息落库, 必须走UI表单 |
| 应用部署记录 | REST | POST /service/udc/application/appVersion/{appGuid} | 空body → 部署历史(含state/failReason) |
| 部署信息 | REST | GET /service/{appName}/app-info/deploy-info | 按appName路由沙箱pod |
| 应用部署 | REST | POST /service/udc/runtime/deploy-normal | deployDto.appId=13位数字 |
| 一致性检测 | 部署流水线内嵌 | AbstractDeployService.doParallel:242 | ERROR阻断: UDC_CE_PAGE_03907(空页面/菜单不一致); WARN放行: UDC_CE_MICRO_FLOW_04003(未保存微流程) |
| 实体创建 | REST | POST /service/udc/entity | appId(数字)+name(小写)+stereotype(standard/bill)+features |
| 实体删除 | GraphQL | udcEntityDeletePost | body.id |
| 数据查询 | REST | POST /service/{app}/udc-runtime/data/query | appName+entityFullName+dataId |
| 登录 | REST | POST /service/ctp-user/auth/token | loginName/password/clientType |
| 元数据查实体 | GraphQL | udcMetaDataSelectAppByIdPost | fullName+appName |

### 【事实】设计器8模块接口面（zzprobe应用实测）
| 模块 | 子功能 | 接口(GraphQL除注明) |
|---|---|---|
| 实体 | 列表/分组/属性/预置容量/锁 | udcEntitySelectAllByAppidAppGet + 8个 |
| 菜单 | 功能树/应用/版本 | udcFunctionSelectFunctionTreePost + 2个 |
| 规则(微流程) | 搜索/分组 | udcMicroflowSearch, udcMicroFlowGroupSelectByTypePost |
| 流程 | 模板选择 | bpm服务: bpmTemplateSelectByAppIdGroupByTagPost |
| BI | 数据集/数据流/指标/报表 | cdp-data服务: env/variable, udc/dataset/get-list-page |
| 栏目 | 列表/端口 | udcPortletSelectByAppIdAppGet + REST page-info |
| 设置 | 枚举 | udcEnumCategorySearch, udcEnumSearchNoPagePost |
| 角色 | 列表/预置 | udcCtpUserRoleSelectListPost + REST create-system-admin |

### 【事实】一致性检测码
| 检测码 | 级别 | 含义 | 修复方式 |
|---|---|---|---|
| UDC_CE_PAGE_03907 | ERROR(阻断) | 菜单绑定页面无内容(WEB端/移动端) | 拖控件或删空页面 |
| UDC_CE_MICRO_FLOW_04003 | WARN(放行) | 微流程未保存/无动作节点 | 添加动作节点后保存 |

### 【需组装配置】页面创建流程（UI）
1. backstageManage/udc/apps → 点"新建"
2. 表单: 应用名称+应用编码(小写字母开头)+所属机构+所属人
3. 创建后 → 设计器 → 菜单tab → lined-plus"添加菜单"
4. 表单: 页面名称 + 页面类型(列表页/详情页/全表编辑页/其它) + 页面对应实体(TreeSelect)
5. 确定 → 自动打开页面设计器 → 拖控件(布局控件/数据控件/录入控件) → 保存并提交
6. **注意**: 画布为空会阻断部署(一致性检测)

### 【通道判定】更新
| 功能 | REST API | UI 操作 | 结论 |
|---|---|---|---|
| 创建应用 | ❌ 持久化不完整 | ✅ | **只能UI** |
| 创建实体 | ✅ POST /udc/entity | - | **API可** |
| 部署 | ✅ deploy-normal | ✅ | **API可** |
| 页面设计 | ❌ 保存协议未抓全 | ✅ 拖拽 | **只能UI(isTrusted限制)** |
| 删除页面 | ✅ udcPageInfoDeletePost | - | **API可** |
| 数据查询 | ✅ data/query | - | **API可** |
| 数据写入 | ❌ 待抓保存协议 | 待配CRUD页 | **待定** |
