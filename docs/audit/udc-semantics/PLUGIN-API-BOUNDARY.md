# UDC 插件契约边界（udc-plugin-api 5.3.517）

**证据**：CFR 反编译 `<MAVEN_REPO>/com/seeyon/udc-plugin-api/5.3.517/udc-plugin-api-5.3.517.jar`；
`app_feature/{type}/backend_config.json` 为 jar 内资源（应用类型功能开关权威）。

## 1. 应用类型功能矩阵（6 种，jar 内 backend_config.json 权威）

落在 `components/udc/plugin_api_constraints.py`。

| 应用类型 | featureType | 动态服务 | 实体版型（stereotype） | 默认 | 宿主依赖 |
| --- | --- | --- | --- | --- | --- |
| 业务应用 | BUSINESS | false | archive / archiveTree / bill / standard | standard | 9 个（organization,bpm,ctp-affair,ctp-message,cip-connector,cdp-data,portal,ctp-user,app-common） |
| 标准应用 | STANDARD | false | **仅 standard** | standard | 6 个 |
| 表单应用 | FORM | true | standard / form | **form** | 5 个 |
| 集成应用 | INTEGRATION | true | 仅 standard | standard | 2 个（organization,ctp-user） |
| 布局应用 | LAYOUT | true | standard / form | standard | 4 个 |
| 单页应用 | ONLYPAGE | true | standard / form | standard | 3 个 |

**核心约束**：实体 stereotype 必须在所属应用类型允许的版型集合内（`validate_entity_stereotype_for_app`）。
此前 `ENTITY_STEREOTYPES` 是 5 种全量并集（archive/standard/bill/archiveTree/form），不知道
"标准应用建 bill 版型"是非法的——这是"数据约束不对"的又一个实例，现已按应用类型分级。

## 2. 权限模型（com.seeyon.udc.auth）

- `AuthOperationType`：CREATE(1) / DELETE(2) / UPDATE(3) / SELECT(4)，UNKNOWN(0)
- `AuthCheck`（接口）：`check(AuthOperationType, UdcBaseEntityDto|Long) -> AuthCheckResultDto`，`getModelName()`
- `AuthCheckFacade`：`check(AuthModel, AuthOperationType, UdcBaseEntityDto|Long)`
- `@AuthModel(name=...)` 注解标记模型；`AuthCheckResultDto = {success, message, msgParams}`
- 横向：`LateralAuthChecker` / `ExtendAppOperationAuthCheck`

## 3. 插件契约层（24 个 AppService，方法数）

`PLUGIN_API_SERVICES`。关键：
- `ApplicationAppService`（**52 方法**）：应用全生命周期——create / update / deleteById /
  selectPageByConditions / copyApp / saveAsTemplate / createFromTemplate /
  deployNormal / deployForm / selectMultiVersion / importAppZipIntoCurrentApp /
  createDepApp / updateDepAppBatch / detectionByAppId / downloadApp 等
- `UdcSerialSchemeAppService`（5）：selectSerialScheme / selectSerialSchemeById /
  selectSerialRange / **createEasyScheme**（简易流水号方案）/ selectDepAppSerialScheme
- `UdcCtpEnumAppService`（16）/ `UdcCtpEnumProxyAppService`（6）：枚举契约
- `UdcPortalPortletAppService`（7）：门户 Portlet
- `PluginEntityAppService`（2）/ `PluginAttributeAppService`（1）/ `PluginPageInfoAppService`（5）
- `ConsistenceDetectionAppService`（4）：一致性检测（应用发布前检查）

## 4. 与运行态/元数据面关系

| 面 | 构件 | 职责 |
| --- | --- | --- |
| 插件契约 | udc-plugin-api | 应用生命周期/流水号方案/枚举/门户的对外接口（无 Controller，纯 AppService） |
| 设计态 REST | udc-web | Controller 化的操作面 |
| 运行态 | udc-starter-runtime / boot-starter-extmetadata | 运行时查询与元数据 |
| 元数据 | boot-starter-metadata | 应用元数据本身 |

流水号方案的两层：udc-plugin-api 定义契约（UdcSerialSchemeAppService），
udc-starter-runtime 的 UdcSerialConfigController 提供运行时配置面（list/update）。
