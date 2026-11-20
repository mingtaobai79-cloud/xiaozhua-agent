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

## 落表

⚠️ **UNVERIFIED** —— 字节码索引不含 SQL/表名，本文件不写推测的表名。

取证路径（三条，任选其一，务必留证据）：

1. **jar 内 mapper**：`organization-biz` 里 `*.xml` / `*Mapper.java`
2. **库结构**：连 test2 的 MySQL 查 `information_schema.columns` 里 `tb_org_%`
3. **运行态**：开 SQL 日志跑一次写操作，看真实表名

在拿到上述证据前，本文件对「落哪张表」保持空。

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 5 接口 / 36 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 57 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 2 事件 / 1 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 35 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径 | 未取证 | `UNVERIFIED` |
| 落表 | 未取证 | `UNVERIFIED` |
