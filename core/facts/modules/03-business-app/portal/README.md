# 门户（portal）

## 一句话

`com.seeyon.portal` 域的**可调用接口面**：3 个构件、675 个类、5 个 facade 接口 / 36 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `portal-biz` | biz | 591 |
| `portal-facade` | facade | 49 |
| `portal-web` | web | 35 |
| **合计** | | **675** |

## 二、分层规律（写代码前必读）

`com.seeyon.portal` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

| 接口族 | 包 | 能力 | 什么时候用 |
|---|---|---|---|
| `*BaseAppService` | `api.core.*` | **含写**：create / update / 全字段查询 / dynamic | 要改数据，或要完整 DTO |
| `*CoreAppService` | `api.core.*` | **只读**：select*，Core DTO 字段精简 | 只查不改，性能敏感 |
| `OrgCommonAppService` | `api.common` | **业务聚合**：按选人数据解析、权限、组织域、扩展属性反查 | 需要「按规则找人」而不是按 id 查 |

调用顺序建议：

```
知道 id       →  XxxCoreAppService.selectXxxById        （最轻）
知道业务规则   →  OrgCommonAppService.selectXxxBySelectPeopleData
要写          →  XxxBaseAppService.create / update
```

## facade 层：5 个接口 / 36 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.portal.api` | 5 | 36 |
| **合计** | **5** | **36** |

### `com.seeyon.portal.api`

#### PortalConfigAppService

`com.seeyon.portal.api.PortalConfigAppService` · 构件 `portal-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `config` | `SingleRequest<PortalConfigParamDto> arg0` | `SingleResponse<Map<String, Object>>` | 门户：读写门户配置 |
| `about` | `—` | `SingleResponse<AboutDto>` | 门户：取关于信息（版本/授权） |

#### PortalPortletAppService

`com.seeyon.portal.api.PortalPortletAppService` · 构件 `portal-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createCategory` | `SingleRequest<PortletCategoryDesignerDto> arg0` | `SingleResponse<Long>` | 新建分类 |
| `updateCategory` | `SingleRequest<PortletCategoryDesignerDto> arg0` | `SingleResponse<Long>` | 修改分类 |
| `deleteCategoryByCodes` | `SingleRequest<List<String>> arg0` | `SingleResponse<Integer>` | 删除分类按编码 |
| `createPortlet` | `SingleRequest<PortletDefinitionDesignerDto> arg0` | `SingleResponse<Long>` | 新建Portlet |
| `deletePortletByIds` | `SingleRequest<List<String>> arg0` | `SingleResponse<Integer>` | 删除Portlet按 ids |
| `createBatchCategory` | `SingleRequest<UdcPortletCategoryListDto> arg0` | `SingleResponse<Integer>` | 批量新建分类 |
| `createBatchPortlet` | `SingleRequest<UdcPortletDefinitionListDto> arg0` | `SingleResponse<Integer>` | 批量新建Portlet |
| `updatePortletSortNos` | `SingleRequest<PortalPortletSortNoParamDto> arg0` | `SingleResponse<Integer>` | 修改排序PortletNos |
| `updatePortletName` | `SingleRequest<PortletDefinitionDesignerDto> arg0` | `SingleResponse<Long>` | 修改名称Portlet |
| `getPortalPortlet` | `SingleRequest<PortalPortletParamDto> arg0` | `SingleResponse<PortletDefinitionDesignerDto>` | 获取PortalPortlet |
| `deletePortlets` | `SingleRequest<PortletBatchOperateDto> arg0` | `SingleResponse<Integer>` | 删除Portlets |

#### PortalSetAppService

`com.seeyon.portal.api.PortalSetAppService` · 构件 `portal-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createPortal` | `SingleRequest<PortalSetDesignerDto> arg0` | `SingleResponse<Long>` | 新建Portal |
| `updatePortal` | `SingleRequest<PortalSetDesignerDto> arg0` | `SingleResponse<Long>` | 修改Portal |
| `exportPortalDesignInfo` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 导出PortalDesign |
| `importPortalDesignInfo` | `SingleRequest<PortalImportParamDto> arg0` | `SingleResponse<Long>` | 导入PortalDesign |
| `publishPortalDesignInfo` | `SingleRequest<Long> arg0` | `SingleResponse<String>` | 发布PortalDesign |
| `detection` | `SingleRequest<PortalDetectionRequestDto> arg0` | `ListResponse<PortalConsistenceDetectionDto>` | 检测检测 |
| `deletePortalDesignInfo` | `SingleRequest<List<Long>> arg0` | `SingleResponse<String>` | 删除PortalDesign |
| `multiVersionPortalDesignInfo` | `SingleRequest<List<Map>> arg0` | `SingleResponse<Void>` | 门户：多版本设计信息（按版本取布局） |
| `createPcTemplateData` | `SingleRequest<PortalSetDesignerDto> arg0` | `SingleResponse<Long>` | 新建模板数据Pc |
| `selectRootOrgPortalSet` | `SingleRequest<Long> arg0` | `SingleResponse<PortalSetDto>` | 查询根组织PortalSet |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<PortalSetDto>` | 查询PortalSet按 ids |

#### PortalShortcutAppService

`com.seeyon.portal.api.PortalShortcutAppService` · 构件 `portal-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `create` | `SingleRequest<PortalShortcutDto> arg0` | `SingleResponse<Long>` | 新建PortalShortcut |
| `update` | `SingleRequest<PortalShortcutDto> arg0` | `SingleResponse<Integer>` | 修改PortalShortcut |
| `deleteById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除按 id（SingleRequest） |
| `selectById` | `SingleRequest<Long> arg0` | `SingleResponse<PortalShortcutDto>` | 查询PortalShortcut按 id |
| `selectListByConditions` | `ListRequest arg0` | `ListResponse<PortalShortcutDto>` | 列表查询PortalShortcut按条件 |
| `selectByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<PortalShortcutDto>` | 查询PortalShortcut按 ids |

#### PortalSpaceAppService

`com.seeyon.portal.api.PortalSpaceAppService` · 构件 `portal-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deleteSpaceById` | `SingleRequest<Long> arg0` | `SingleResponse<Integer>` | 删除Space按 id |
| `createSpace` | `SingleRequest<PortalSpaceDesignerDto> arg0` | `SingleResponse<Long>` | 新建Space |
| `updateSpace` | `SingleRequest<PortalSpaceDesignerDto> arg0` | `SingleResponse<Long>` | 修改Space |
| `selectDesignSpaceList` | `SingleRequest<List<Long>> arg0` | `ListResponse<PortalSpaceDesignerDto>` | 列表查询DesignSpace |
| `saveAsPortalSpaceCopy` | `SingleRequest<UdcPortalSpaceAndInstanceDto> arg0` | `SingleResponse<Map<String, Long>>` | 保存AsPortalSpaceCopy |
| `selectAllSectionsByUserIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Map<Long, List<Map<String, Object>>>>` | 全部查询Sections按用户 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 57 个领域服务，下表列**方法数最多的 40 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `PortalSetService` | 243 | PortalSet · 获取×46 / 查询×36 / 新建×22 |
| `PortalSpaceService` | 173 | PortalSpace · 查询×63 / 获取×35 / 删除×9 |
| `PortalCacheService` | 91 | PortalCache · 获取×37 / 判断有×22 / 判断×5 |
| `PortalPortletDefinitionService` | 87 | PortalPortletDefinition · 查询×19 / 获取×12 / 修改×9 |
| `PortalTemplateDataService` | 71 | 模板 · 获取×22 / 新建×10 / 保存×9 |
| `PortalSpaceNavService` | 66 | PortalSpaceNav · 获取×28 / 保存×8 / 查询×7 |
| `PortalPortletCategoryService` | 41 | 分类 · 查询×10 / 删除×7 / 获取×6 |
| `PortalBaseService` | 40 | Portal · 获取×12 / 判断有×5 / 新增×4 |
| `PortalFileService` | 31 | 文件 · 办理×14 / 获取×9 / 解析×2 |
| `PortalSpaceInstanceService` | 28 | PortalSpaceInstance · 查询×8 / 获取×5 / 删除×3 |
| `FullIndexService` | 27 | FullIndex · 新建×9 / 修改×4 / 移除×2 |
| `MainTemplateService` | 26 | 主模板 · 查询×13 / 获取×5 / 新建×2 |
| `PortalRoleConfigService` | 26 | 角色配置 · 获取×9 / 查询×4 / 修改×3 |
| `PortalTemplateDesignService` | 22 | 模板 · 获取×6 / 保存×3 / 重置×3 |
| `PortalParameterService` | 20 | 参数 · 查询×14 / 修改×5 / 转换×1 |
| `PortalSpaceNavConfigService` | 19 | 配置 · 获取×4 / 查询×4 / 修改×3 |
| `PortalElementPropertyService` | 18 | 属性 · 修改×8 / 获取×3 / 删除×2 |
| `PortalFrontUserService` | 17 | 用户 · 获取×14 / 新建×1 / 排序×1 |
| `MainOperationDefinitionService` | 16 | 主 · 查询×8 / 获取×2 / 注册×1 |
| `PortalConfigService` | 16 | 配置 · 处理×5 / 获取×3 / 查询×1 |
| `PortletShortcutResourceService` | 16 | 资源 · 新建×9 / 升级×4 / 查询×1 |
| `MainLoginPageService` | 15 | 主登录页面 · 查询×8 / 新建×2 / 修改×2 |
| `PortalOrgService` | 14 | 组织 · 获取×8 / 判断×5 |
| `PortalShortcutService` | 14 | PortalShortcut · 获取×3 / 保存×2 / 修改×2 |
| `PortalCheckVersionService` | 11 | 版本 · 检查×7 / 获取×2 / 新建×1 |
| `PortalSpacePersonalService` | 11 | PortalSpacePersonal · 删除×4 / 保存×3 / 获取×3 |
| `MainElementDefinitionService` | 10 | 主 · 校验×3 / 查询×3 / 注册×1 |
| `PortalInstanceRelationService` | 10 | PortalInstanceRelation · 查询×3 / 获取×3 / 删除×2 |
| `PortalPortletFrameService` | 10 | PortalPortletFrame · 查询×6 / 新建×1 / 修改×1 |
| `MemorabiliaService` | 10 | Memorabilia · 查询×5 / 修改×2 / 删除×2 |
| `AppResourceCategoryService` | 9 | 应用资源分类 · 查询×4 / 新建×3 / 注册×1 |
| `MemorabiliaTypeService` | 9 | 类型 · 查询×3 / 修改×2 / 新建×1 |
| `UdcOperateLogService` | 9 | 日志 · 构建×2 / 处理×2 / 对比×2 |
| `PortalCategoryService` | 8 | 分类 · 查询×2 / 判断有×2 / 新建×1 |
| `PortalHolidayConfigService` | 8 | 配置 · 查询×3 / 删除×2 / 新建×1 |
| `MainOperationConfigService` | 7 | 主配置 · 保存×5 / 设置×1 / 修改×1 |
| `PortalSpaceLayoutService` | 7 | 布局 · 获取×2 / 查询×2 / 新建×1 |
| `AppResourceDefinitionService` | 7 | 应用资源 · 查询×3 / 注册×1 / 新建×1 |
| `PortalRecycleService` | 7 | PortalRecycle · 新建×2 / 查询×2 / 初始化×1 |
| `PortalSetPersonalService` | 6 | PortalSetPersonal · 修改×2 / 新建×1 / 获取×1 |

## biz 层：事件与监听

事件 2 个 · 监听器 1 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| PortalLoginPreEnable | `PortalLoginPreEnableEvent` |
| PortalNavSpaceAppend | `PortalNavSpaceAppendEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `PortalFileAfterTenantEventListener` | 3 |

## web 层：Controller

共 35 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `MainController` | 42 |
| 核心实体 CRUD | `PortalSpaceController` | 41 |
| 核心实体 CRUD | `PortalSetController` | 33 |
| 核心实体 CRUD | `PortletController` | 29 |
| 核心实体 CRUD | `MainTemplateController` | 25 |
| 核心实体 CRUD | `PortalTemplateInstanceController` | 18 |
| 核心实体 CRUD | `PortalRoleConfigController` | 15 |
| 核心实体 CRUD | `PortalTemplateDesignController` | 15 |
| 核心实体 CRUD | `PortalSpaceNavController` | 14 |
| 核心实体 CRUD | `PortalShortCutController` | 12 |
| 核心实体 CRUD | `MemorabiliaController` | 10 |
| 核心实体 CRUD | `PortalPortletFrameController` | 9 |
| 核心实体 CRUD | `MemorabiliaTypeController` | 8 |
| 核心实体 CRUD | `PortalCheckVersionController` | 8 |
| 核心实体 CRUD | `PortalHolidayReminderController` | 8 |
| 核心实体 CRUD | `PortalParameterController` | 8 |
| 核心实体 CRUD | `MainLoginPageController` | 7 |
| 核心实体 CRUD | `MainOperationController` | 6 |
| 核心实体 CRUD | `PortalLoginPreConfigController` | 6 |
| 核心实体 CRUD | `PortalSpaceLayoutController` | 6 |
| 核心实体 CRUD | `PortalAppResourceController` | 5 |
| 核心实体 CRUD | `PortalCategoryController` | 5 |
| 核心实体 CRUD | `NoticeBoardController` | 4 |
| 核心实体 CRUD | `PortalSpaceVersionController` | 4 |
| 核心实体 CRUD | `MainElementController` | 3 |
| 核心实体 CRUD | `PortalBannerImageController` | 3 |
| 核心实体 CRUD | `PortalBaseController` | 3 |
| 核心实体 CRUD | `PortalConfigController` | 3 |
| 核心实体 CRUD | `PortalPersonalConfigController` | 2 |
| 核心实体 CRUD | `PortalRecycleController` | 2 |
| 核心实体 CRUD | `UserInfoController` | 2 |
| 核心实体 CRUD | `WeatherController` | 2 |
| 核心实体 CRUD | `MainPcSysResourceController` | 1 |
| 核心实体 CRUD | `PortalConnectorController` | 1 |
| 核心实体 CRUD | `VideoController` | 1 |

## 入参 DTO（字段级）

> 字段来自字节码 `fields`（含继承链，最多 3 层）；**字段名即 JSON 键名**（平台用 Jackson 默认命名，`shortName` 对应库列 `short_name`）。
> 包装类已揭开：`SingleRequest<T>` / `ListResponse<T>` 里看的是 `T` 的字段。
> 等级 `VERIFIED_STATIC_BYTECODE`。全量字段表：`docs/audit/artifacts/dto/DTO-portal.md`

本模块 **17** 个入参/返回 DTO，**17** 个能取到字段。Top 12（按出现次数）：

| DTO | 出现 | 字段数 | 关键字段 |
|---|---:|---:|---|
| `PortalShortcutDto` | 5 | 17 | `id`, `spaceId`, `parentId`, `orgId`, `userId`, `operationType`, `property`, `shortcutGroupDtoList` |
| `PortletDefinitionDesignerDto` | 3 | 22 | `id`, `portletId`, `name`, `defaultName`, `appId`, `mobileAppId`, `enablePc`, `enableMobile` |
| `PortalSetDesignerDto` | 3 | 20 | `id`, `dataId`, `name`, `orgId`, `userId`, `imgId`, `enablePc`, `enableMobile` |
| `PortalSpaceDesignerDto` | 3 | 18 | `id`, `dataId`, `name`, `portalId`, `sortNo`, `orgId`, `userId`, `spaceIcon` |
| `PortletCategoryDesignerDto` | 2 | 10 | `id`, `categoryCode`, `parentCategoryCode`, `categoryName`, `sortNo`, `appCode`, `originalAppId`, `originalId` |
| `PortalSetDto` | 2 | 79 | `id`, `name`, `portalType`, `orgId`, `masterOrgId`, `ownerOrgId`, `userId`, `categoryId` |
| `PortalConfigParamDto` | 1 | 5 | `portalType`, `sid`, `pageLoginPageType`, `uri`, `validate` |
| `AboutDto` | 1 | 9 | `productInfo`, `deploymentType`, `userNum`, `pcOnlineNum`, `mobileOnlineNum`, `webOnlineNum`, `envInfo`, `language` |
| `UdcPortletCategoryListDto` | 1 | 2 | `categoryDesignerDtoList`, `validate` |
| `UdcPortletDefinitionListDto` | 1 | 2 | `definitionDesignerDtoList`, `validate` |
| `PortalPortletSortNoParamDto` | 1 | 3 | `portletSortNoMap`, `appCode`, `validate` |
| `PortalPortletParamDto` | 1 | 3 | `appCode`, `portletId`, `validate` |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **53** 张（来源构件：`portal-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `portal_space_data` | 空间实例 | 4 |
| `portal_template` | 门户模板 | 4 |
| `portal_template_data` | 门户模板子表 | 4 |
| `portlet_banner_image` | 门户横幅图片 | 4 |
| `portlet_memorabilia` | 大事记信息 | 4 |
| `portlet_shortcut` | 门户磁贴栏目 | 4 |
| `portal_operation_config` | 门户系统操作配置信息 | 2 |
| `portal_role_config` | 角色化配置表 | 2 |
| `udc_enum` | — | 2 |
| `bpm_template` | 流程模板 | 1 |
| `portal_app_resource_category` | 门户应用资源分类 | 1 |
| `portal_app_resource_definition` | 门户应用资源信息 | 1 |
| `portal_category` | 门户分类 | 1 |
| `portal_element_definition` | 门户元素定义信息表 | 1 |
| `portal_element_property` | 门户元素属性表 | 1 |
| `portal_element_template` | 门户元素模版表 | 1 |
| `portal_file` | 门户附件 | 1 |
| `portal_holiday_history` | 节假日提醒记录表 | 1 |
| `portal_holiday_reminder` | 节假日提醒配置表 | 1 |
| `portal_instance_relation` | 门户实例模板关系表 | 1 |
| `portal_issue` | 门户下发表 | 1 |
| `portal_issue_log` | 门户下发日志表 | 1 |
| `portal_login_page` | 登录页配置表 | 1 |
| `portal_login_page_version` | — | 1 |
| `portal_operation_definition` | 门户系统操作信息 | 1 |
| `portal_pc_sys_resource` | 门户PC系统操作资源 | 1 |
| `portal_personal_config` | 门户个人配置表 | 1 |
| `portal_portlet_category` | 门户栏目分类 | 1 |
| `portal_portlet_definition` | 门户栏目定义 | 1 |
| `portal_portlet_frame` | 门户栏目外框 | 1 |
| `portal_portlet_style_sheet` | 栏目样式定义表 | 1 |
| `portal_portlet_use_detail` | 栏目使用详情 | 1 |
| `portal_portlet_usual` | 常用栏目关联表 | 1 |
| `portal_publish_id_relation` | 门户发布数据Id关联表 | 1 |
| `portal_recycle` | 回收站信息表 | 1 |
| `portal_role_config_history` | 角色化配置历史表 | 1 |
| `portal_set` | 门户表 | 1 |
| `portal_set_personal` | 门户模板个性化 | 1 |
| `portal_space` | 空间 | 1 |
| `portal_space_basic` | 空间基础表 | 1 |
| `portal_space_layout` | 门户空间布局 | 1 |
| `portal_space_nav_config` | 门户空间导航配置信息表 | 1 |
| `portal_space_nav_control` | 门户空间导航控制信息表 | 1 |
| `portal_space_personal` | 普通用户性化空间记录 | 1 |
| `portal_space_version` | 空间版本记录表 | 1 |
| `portal_template_history` | 门户模版实例版本表 | 1 |
| `portal_template_version` | 门户版本记录表 | 1 |
| `portal_update_version_data` | 门户更新提醒记录表 | 1 |
| `portlet_memorabilia_type` | 大事记类别信息 | 1 |
| `portlet_notice_board` | 公示板 | 1 |
| `portlet_shortcut_resource` | 磁贴资源表 | 1 |
| `udc_enum_category` | — | 1 |
| `udc_enum_item` | — | 1 |

### 接口 → 表（3 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `PortalSetAppService` | `PortalSet` | `portal_set` | `stem` |
| `PortalShortcutAppService` | `PortalShortcut` | `portlet_shortcut` | `stem` |
| `PortalSpaceAppService` | `PortalSpace` | `portal_space` | `stem` |

## REST 路由

> 证据：`javap -v` 读 Controller 字节码里的 `@RequestMapping`/`@PostMapping` 注解值。
> 等级 `VERIFIED_STATIC_BYTECODE`（注解值是常量，非推断）。

**拼法**（以 `organization` 为例，`:8080` 之类按环境）：

```
POST /service/{类级路径}/{方法级路径}
      ↑ 类级路径的第一段就是应用 code（organization / bpm / udc …），不要再加一层
  例：POST /service/udc/runtime/deploy-normal
      = DeployController 类级 `udc/runtime` + 方法级 `deploy-normal`（线上实测过）
```

控制器 **34** 个、路由 **337** 条（来源：`portal-web`）。

> `{id}`、`ids` 这类方法级路径不带类级前缀，拼时必须补上。
> 完整清单（含 java 方法名）：`docs/audit/artifacts/rest/ROUTES-portal.md`

| Controller | 类级路径 | 路由 |
|---|---|---:|
| `PortalSpaceController` | `portal/portal-space` | 40 |
| `MainController` | `portal/main` | 33 |
| `PortalSetController` | `portal/portal-set` | 32 |
| `PortletController` | `portal/portal-portlet` | 26 |
| `MainTemplateController` | `portal/template` | 25 |
| `PortalTemplateInstanceController` | `portal/portal-instance` | 18 |
| `PortalTemplateDesignController` | `portal/template-design` | 15 |
| `PortalSpaceNavController` | `portal/space-nav` | 14 |
| `PortalRoleConfigController` | `portal/portal-role` | 13 |
| `PortalShortCutController` | `portal/shortcut` | 11 |
| `MemorabiliaController` | `portal/memorabilia` | 10 |
| `PortalPortletFrameController` | `portal/portlet-frame` | 9 |
| `MemorabiliaTypeController` | `portal/memorabilia-type` | 8 |
| `PortalHolidayReminderController` | `portal/portlet-holiday` | 8 |
| `PortalParameterController` | `portal/portal-parameter` | 8 |
| `PortalCheckVersionController` | `portal/check-version` | 8 |
| `MainLoginPageController` | `portal/login-page` | 6 |
| `MainOperationController` | `portal/portal-operation` | 6 |
| `PortalSpaceLayoutController` | `portal/space-layout` | 6 |
| `PortalAppResourceController` | `portal/app-resource` | 5 |
| `PortalLoginPreConfigController` | `portal/login-pre-config` | 5 |
| `PortalCategoryController` | `portal/portal-category` | 5 |
| `NoticeBoardController` | `portal/notice-board` | 4 |
| `PortalSpaceVersionController` | `portal/version-record` | 4 |
| `PortalBannerImageController` | `portal/banner-image` | 3 |
| `MainElementController` | `portal/element` | 3 |
| `PortalPersonalConfigController` | `portal/personal-config` | 2 |
| `PortalConfigController` | `portal/config` | 2 |
| `WeatherController` | `portal/weather` | 2 |
| `PortalRecycleController` | `portal/portal-recycle` | 2 |
| `VideoController` | `portal/video` | 1 |
| `PortalConnectorController` | `portal/portal-connector` | 1 |
| `MainPcSysResourceController` | `portal/sys-resource` | 1 |
| `UserInfoController` | `portal/user-info` | 1 |

前 15 条（其余见明细）：

| 方法 | 全路径 |
|---|---|
| `PostMapping` | `/service/portal/main/login` |
| `PostMapping` | `/service/portal/main/switch-admin` |
| `PostMapping` | `/service/portal/main/switch-admin-new` |
| `PostMapping` | `/service/portal/main/switch-user` |
| `PostMapping` | `/service/portal/main/switch-tenant` |
| `GetMapping` | `/service/portal/main/user-info` |
| `GetMapping` | `/service/portal/main/pc-user-info` |
| `GetMapping` | `/service/portal/main/mobile-user-info` |
| `GetMapping` | `/service/portal/main/org-list` |
| `GetMapping` | `/service/portal/main/admin-menus` |
| `PostMapping` | `/service/portal/main/admin-org-list` |
| `GetMapping` | `/service/portal/main/org-portal-info` |
| `GetMapping` | `/service/portal/main/main-portal-info` |
| `PostMapping` | `/service/portal/main/portal-info` |
| `GetMapping` | `/service/portal/main/org-space-info` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 5 接口 / 36 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 57 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 2 事件 / 1 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 35 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（337 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| REST 真机验证 | 176/176 条安全路由命中（100%） | `LIVE` |
| 落表（56 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
