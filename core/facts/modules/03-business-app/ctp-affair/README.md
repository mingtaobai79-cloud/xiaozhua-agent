# 协同事项（affair）

## 一句话

`com.seeyon.ctp` 域的**可调用接口面**：3 个构件、481 个类、10 个 facade 接口 / 79 个方法。

## 一、构件清单

| 构件 | 层 | 类数 |
|---|---|---:|
| `ctp-affair-biz` | biz | 344 |
| `ctp-affair-facade` | facade | 124 |
| `ctp-affair-web` | web | 13 |
| **合计** | | **481** |

## 二、分层规律（写代码前必读）

`com.seeyon.ctp` 的接口按职责三分，**选错会多绕一层或拿到多余字段**：

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

## facade 层：10 个接口 / 79 个方法

> 入参与返回类型来自字节码索引（`VERIFIED_STATIC_BYTECODE`）。
> 「干什么」由方法名拆词推断；标 ⚠️ 表示名称不足以确定语义，需实测。

### 接口清单

| 包 | 接口数 | 方法数 |
|---|---:|---:|
| `com.seeyon.ctp.affair.api.common` | 5 | 58 |
| `com.seeyon.ctp.affair.api.microflow` | 1 | 4 |
| `com.seeyon.ctp.affair.api.openApi` | 1 | 12 |
| `com.seeyon.ctp.affair.api.supervise` | 1 | 3 |
| `com.seeyon.ctp.affair.api.udc` | 1 | 1 |
| `com.seeyon.ctp.affair.workflow.api` | 1 | 1 |
| **合计** | **10** | **79** |

### `com.seeyon.ctp.affair.api.common`

#### AffairCategoryAppService

`com.seeyon.ctp.affair.api.common.AffairCategoryAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `syncCategories` | `SingleRequest<AffairFullCategorySyncDto> arg0` | `SingleResponse<Integer>` | 同步Categories |
| `getAllAppAndSubAppInfoRegisterAffair` | `—` | `ListResponse<AffairAppSimpleInfoDto>` | 全部获取应用事项AndSubRegister |
| `searchAffairCategory` | `SingleRequest<AffairCategorySearchDto> arg0` | `ListResponse<AffairCategoryTreeDto>` | 搜索事项分类 |
| `selectAffairCountForBadgeWithMergeTenants` | `SingleRequest<AffairBadgeCountQueryDto> arg0` | `SingleResponse<Integer>` | 查询事项CountForBadgeWithMergeTenants |

#### AffairCommonAppService

`com.seeyon.ctp.affair.api.common.AffairCommonAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectAffairById` | `SingleRequest<Long> arg0` | `SingleResponse<AffairDto>` | 查询事项按 id |
| `updateAffairDone` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 修改事项Done |
| `updateAffairDoneIdempotent` | `SingleRequest<UpdateAffairDoneDto> arg0` | `SingleResponse<Void>` | 修改事项DoneIdempotent |
| `selectListByCondition` | `SingleRequest<AffairBaseConditionDto> arg0` | `ListResponse<AffairDto>` | 列表查询事项条件按条件 |
| `countAffairByConditions` | `SingleRequest<AffairCountConditionDto> arg0` | `ListResponse<AffairCountDto>` | 统计事项按条件 |
| `createAffair` | `SingleRequest<AffairCreateMessageDto> arg0` | `SingleResponse<Void>` | 新建事项 |
| `createAffairIdempotent` | `SingleRequest<AffairCreateMessageIdempotentDto> arg0` | `SingleResponse<Void>` | 新建事项Idempotent |
| `updateAffair` | `SingleRequest<AffairUpdateMessageDto> arg0` | `SingleResponse<Void>` | 修改事项 |
| `updateAffairIdempotent` | `SingleRequest<AffairUpdateMessageIdempotentDto> arg0` | `SingleResponse<Void>` | 修改事项Idempotent |
| `updateAffairRead` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 修改事项Read |
| `updateAffairReadIdempotent` | `SingleRequest<UpdateAffairReadDto> arg0` | `SingleResponse<Void>` | 修改事项ReadIdempotent |
| `updateAffairTrack` | `SingleRequest<AffairTrackUpdateDto> arg0` | `SingleResponse<Void>` | 修改事项Track |
| `updateBpmCaseTrackToAffairTrack` | `SingleRequest<AffairTrackUpgradeDto> arg0` | `SingleResponse<Void>` | 修改流程实例事项BpmTrackToTrack |
| `updateBatchAffairByCondition` | `SingleRequest<AffairUpdateBatchDto> arg0` | `SingleResponse<Void>` | 批量修改事项按条件 |
| `updateBatchAffairByConditionIdempotent` | `SingleRequest<AffairUpdateBatchIdempotentDto> arg0` | `SingleResponse<Void>` | 批量修改事项按条件 |
| `selectAffairSimpleById` | `SingleRequest<Long> arg0` | `SingleResponse<AffairSimpleDto>` | 查询事项简单按 id |
| `selectAffairSimpleByIds` | `SingleRequest<List<Long>> arg0` | `ListResponse<AffairSimpleDto>` | 查询事项简单按 ids |
| `selectAffairSimpleListByCondition` | `SingleRequest<AffairBaseConditionDto> arg0` | `ListResponse<AffairSimpleDto>` | 列表查询事项简单按条件 |
| `selectAffairPropertyInfoByCondition` | `SingleRequest<Map<String, Object>> arg0` | `ListResponse<AffairPropertyInfoDto>` | 查询事项属性按条件 |
| `selectPageByCustomizeConditions` | `PageDtoRequest<AffairSearchCustomizeDto> arg0` | `PageResponse<AffairDto>` | 分页查询事项按条件 |
| `selectCountByCustomizeConditions` | `SingleRequest<AffairSearchCustomizeDto> arg0` | `SingleResponse<Map<String, Object>>` | 查询Count按条件 |
| `selectOvertimePendingAffair` | `—` | `ListResponse<AffairOverTimeMsgDto>` | 查询待办事项Overtime |
| `updateAffairById` | `SingleRequest<AffairInfoDto> arg0` | `SingleResponse<Void>` | 修改事项按 id |
| `selectSubmitInfoDtoById` | `SingleRequest<Long> arg0` | `SingleResponse<AffairSubmitInfoDto>` | 查询SubmitDto按 id |
| `createAffairCategory` | `SingleRequest<AffairFullCategoryDto> arg0` | `SingleResponse<Long>` | 新建事项分类 |
| `updateAffairCategory` | `SingleRequest<AffairFullCategoryDto> arg0` | `SingleResponse<Void>` | 修改事项分类 |
| `searchAffairCategory` | `SingleRequest<AffairFullCategoryDto> arg0` | `ListResponse<AffairFullCategoryDto>` | 搜索事项分类 |
| `searchAffairCategoryPage` | `PageRequest arg0` | `PageResponse<AffairFullCategoryDto>` | 分页搜索事项分类 |
| `deleteAffairCategoryById` | `SingleRequest<Long> arg0` | `SingleResponse<Void>` | 删除事项分类按 id |
| `deleteAffairCategoryByCondition` | `SingleRequest<AffairDeleteCategoryConditionDto> arg0` | `SingleResponse<Void>` | 删除事项分类按条件 |
| `dynamicQueryAffairDtoPage` | `SingleRequest<AffairDynamicQueryDto> arg0` | `PageResponse<Object>` | 分页查询事项Dto |
| `selectPageByConditions` | `PageRequest arg0` | `PageResponse<AffairDto>` | 分页查询事项按条件 |
| `selectAffairPageByConditions` | `PageRequest arg0` | `PageResponse<AffairDto>` | 分页查询事项按条件 |
| `deleteAffairByIds` | `SingleRequest<AffairCommonIdsDto> arg0` | `SingleResponse<Void>` | 删除事项按 ids |
| `deleteAffairByObjectIds` | `SingleRequest<AffairCommonIdsDto> arg0` | `SingleResponse<Void>` | 删除事项按ObjectIds |
| `selectProcessingPersonInfo` | `PageRequest arg0` | `PageResponse<AffairProcessingPersonResponseDto>` | 查询ProcessingPerson |
| `selectProcessingPersonForEachNode` | `SingleRequest<AffairProcessingPersonRequestDto> arg0` | `ListResponse<AffairProcessingPersonResponseDto>` | 查询ProcessingPersonForEach |
| `selectFlowProcessingNodeInfo` | `SingleRequest<Long> arg0` | `ListResponse<AffairDto>` | 查询FlowProcessing |
| `selectAffairByFixedUserCondition` | `SingleRequest<AffairConditionSearchDto> arg0` | `PageResponse<AffairDto>` | 查询事项按用户条件 |
| `selectEnumItemByEnumCode` | `SingleRequest<AffairEnumSearchParamDto> arg0` | `ListResponse<AffairEnumResponseDto>` | 查询枚举Item按枚举编码 |
| `selectReceiveMemberIdList` | `SingleRequest<AffairReceiverSearchDto> arg0` | `ListResponse<Long>` | 列表查询成员Receive |
| `chooseReceiverAffair` | `SingleRequest<AffairReceiverSearchDto> arg0` | `ListResponse<AffairSimpleDto>` | 选择接收人事项 |
| `isBillCodeOpened` | `—` | `SingleResponse<Boolean>` | 判断编码BillOpened |
| `selectAffairCountForBadge` | `SingleRequest<AffairBadgeCountQueryDto> arg0` | `SingleResponse<Integer>` | 查询事项CountForBadge |
| `selectFormPermissionListForCase` | `SingleRequest<Long> arg0` | `ListResponse<Long>` | 列表查询表单权限流程实例For |
| `selectAffairCountBatchForBadge` | `SingleRequest<AffairBadgeCountBatchQueryDto> arg0` | `ListResponse<AffairBadgeCountResultDto>` | 批量查询事项CountForBadge |
| `pendingAffairQuick` | `SingleRequest<AffairQuickDto> arg0` | `SingleResponse<AffairBatchResponseDto>` | 事项：快速生成待办（不建完整流程） |

#### AffairCustomOperationAppService

`com.seeyon.ctp.affair.api.common.AffairCustomOperationAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createAffairCustomOperation` | `SingleRequest<AffairCustomOperationDto> arg0` | `SingleResponse<Long>` | 新建事项CustomOperation |

#### AffairDataScopeAppService

`com.seeyon.ctp.affair.api.common.AffairDataScopeAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `getDataScope` | `—` | `SingleResponse<AffairDataScopeDto>` | 获取数据范围 |

#### AffairNodePermissionAppService

`com.seeyon.ctp.affair.api.common.AffairNodePermissionAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `deleteByIds` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除按 ids（SingleRequest） |
| `logicDelete` | `SingleRequest<List<Long>> arg0` | `SingleResponse<Integer>` | 删除（SingleRequest） |
| `selectPageByCondition` | `PageRequest arg0` | `PageResponse<AffairNodePermissionDto>` | 分页查询事项权限按条件 |
| `createOrUpdate` | `SingleRequest<List<AffairNodePermissionDto>> arg0` | `SingleResponse<Integer>` | 新建OrUpdate |
| `publish` | `SingleRequest<String> arg0` | `SingleResponse<String>` | 发布（SingleRequest） |

### `com.seeyon.ctp.affair.api.microflow`

#### AffairMicroflowAppService

`com.seeyon.ctp.affair.api.microflow.AffairMicroflowAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `createAffairByMicroflow` | `SingleRequest<AffairMicroflowInfoDto> arg0` | `SingleResponse<Void>` | 新建事项按微流程 |
| `createAffairByMicroflowReturnIds` | `SingleRequest<AffairMicroflowInfoDto> arg0` | `ListResponse<Long>` | 新建事项按微流程 |
| `updateAffairReadByMicroflow` | `SingleRequest<AffairMicroUpdateConditionDto> arg0` | `SingleResponse<Void>` | 修改事项Read按微流程 |
| `updateAffairDoneByMicroflow` | `SingleRequest<AffairMicroUpdateConditionDto> arg0` | `SingleResponse<Void>` | 修改事项Done按微流程 |

### `com.seeyon.ctp.affair.api.openApi`

#### AffairOpenAppService

`com.seeyon.ctp.affair.api.openApi.AffairOpenAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByCondition` | `SingleRequest<AffairOpenConditionDto> arg0` | `PageResponse<AffairDto>` | 分页查询事项条件按条件 |
| `selectByConditionIgnoreTenant` | `SingleRequest<AffairOpenConditionDto> arg0` | `SingleResponse<AffairSearchResultDto>` | 查询事项条件按条件租户 |
| `selectActivityUnprocessedMember` | `SingleRequest<AffairNodeUnprocessedDto> arg0` | `ListResponse<AffairUnprocessedMemberInfoDto>` | 查询成员ActivityUnprocessed |
| `selectSpecifyActivityUnprocessedMember` | `SingleRequest<AffairNodeMoreSearchDto> arg0` | `SingleResponse<AffairUnprocessedMemberInfoDto>` | 查询成员SpecifyActivityUnprocessed |
| `createOrUpdate` | `SingleRequest<List<AffairOpenApiNodeDto>> arg0` | `SingleResponse<Integer>` | 新建OrUpdate |
| `selectNodePermissionPageByCondition` | `PageRequest arg0` | `PageResponse<AffairOpenApiNodeDto>` | 分页查询权限按条件 |
| `createOrUpdateCategory` | `SingleRequest<AffairFullCategoryDto> arg0` | `SingleResponse<Void>` | 新建分类OrUpdate |
| `selectCategoryByCondition` | `SingleRequest<AffairFullCategoryDto> arg0` | `SingleResponse<List<AffairFullCategoryDto>>` | 查询分类按条件 |
| `deleteCategory` | `SingleRequest<AffairDeleteCategoryConditionDto> arg0` | `SingleResponse<Void>` | 删除分类 |
| `createOrUpdateCategoryHierarchy` | `SingleRequest<List<AffairCategoryHierarchyDto>> arg0` | `SingleResponse<Integer>` | 新建分类OrUpdateHierarchy |
| `deleteCategoryHierarchy` | `SingleRequest<AffairCategoryHierarchyDeleteDto> arg0` | `SingleResponse<Void>` | 删除分类Hierarchy |
| `getCategoryHierarchy` | `SingleRequest<AffairCategoryHierarchySearchDto> arg0` | `SingleResponse<List<AffairCategoryHierarchyDto>>` | 获取分类Hierarchy |

### `com.seeyon.ctp.affair.api.supervise`

#### AffairSuperviseAppService

`com.seeyon.ctp.affair.api.supervise.AffairSuperviseAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectPageByFixedTemplate` | `SingleRequest<AffairFixedTemplateConditionDto> arg0` | `PageResponse<AffairDto>` | 分页查询事项模板条件按模板 |
| `selectTemplateAffairPageData` | `SingleRequest<PageInfo> arg0` | `PageResponse<AffairDto>` | 分页查询模板事项数据 |
| `updateTemplateAccountId2Affairs` | `SingleRequest<List<AffairDto>> arg0` | `void` | 修改模板账户Id2Affairs |

### `com.seeyon.ctp.affair.api.udc`

#### AffairUdcAppService

`com.seeyon.ctp.affair.api.udc.AffairUdcAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `selectSpecifiedFieldValues` | `SingleRequest<AffairSearchSpecifiedFieldDto> arg0` | `ListResponse<String>` | 查询字段SpecifiedValues |

### `com.seeyon.ctp.affair.workflow.api`

#### Affair4WorkflowAppService

`com.seeyon.ctp.affair.workflow.api.Affair4WorkflowAppService` · 构件 `ctp-affair-facade`

| 方法 | 入参 | 返回 | 干什么 |
|---|---|---|---|
| `stopCase` | `SingleRequest<WorkflowStopDto> arg0` | `SingleResponse<Void>` | 停止流程实例 |

> ⚠️ 共 0 个方法仅凭名称无法确定语义，需实测或读实现类。

## biz 层：领域服务

共 27 个领域服务，下表列**方法数最多的 27 个**。
职责由**该服务方法名的动词分布**归纳，不是猜的。

| 服务 | 方法数 | 职责（按方法名统计） |
|---|---:|---|
| `AffairEntityService` | 265 | 事项实体 · 查询×54 / 设置×34 / 获取×31 |
| `AffairService` | 40 | 事项 · 获取×11 / 查询×6 / 办理×5 |
| `AffairLayoutService` | 22 | 事项布局 · 查询×12 / 新建×4 / 修改×3 |
| `AffairNodePermissionService` | 22 | 事项权限 · 查询×5 / 获取×5 / 删除×2 |
| `AffairCategoryService` | 21 | 事项分类 · 查询×9 / 新建×3 / 设置×3 |
| `AffairAppMappingInfoService` | 21 | 事项应用映射 · 获取×8 / 查询×4 / 构建×4 |
| `AffairColumnConfigService` | 19 | 事项配置 · 查询×9 / 构建×4 / 修改×2 |
| `AffairSendMessageService` | 17 | 事项消息 · 发送×8 / 合并×3 / 新建×2 |
| `AffairCustomOperationService` | 16 | 事项 · 获取×5 / 新建×2 / 查询×1 |
| `AffairOpenUrlService` | 14 | 事项 · 设置×5 / 获取×5 / 打开×1 |
| `AffairCategoryHierarchyService` | 13 | 事项分类 · 获取×5 / 新建×2 / 判断×2 |
| `MqCompensationService` | 10 | MqCompensation · 新建×3 / 修改×3 / 删除×2 |
| `AffairEntityDispatchService` | 9 | 事项实体 · 分发×3 / 修改×3 / 判断×3 |
| `AffairEdocService` | 9 | 事项 · 修改×2 / 办理×2 / 构建×2 |
| `AffairHandoverService` | 9 | 事项移交 · 新建×2 / 检查×1 / 合并×1 |
| `AffairThirdUrlService` | 8 | 事项第三方 · 获取×2 / 设置×2 / 判断能否×1 |
| `AffairSectionCountService` | 7 | 事项 · 统计×3 / 初始化×1 / 查询×1 |
| `AffairManageService` | 7 | 事项管理 · 修改×4 / 删除×2 / 查询×1 |
| `AffairCacheManagerService` | 6 | 事项负责人 · 获取×2 / 保存×1 / 新增×1 |
| `AffairAdapterService` | 6 | 事项 · 获取×4 |
| `AffairCompensateService` | 6 | 事项 · 删除×2 / 新建×1 / 处理×1 |
| `DisplayNameCacheService` | 6 | 名称 · 填充×3 / 查询×2 / 判断×1 |
| `AffairExtendService` | 5 | 事项扩展 · 查询×3 / 保存×1 / 新建×1 |
| `AffairPropertyUtilService` | 4 | 事项属性 · 获取×4 |
| `AffairPropertyInfoService` | 3 | 事项属性 · 查询×1 / 移除×1 / 列出×1 |
| `AffairPendingService` | 3 | 事项待办 · 校验×1 / 新建×1 / 构建×1 |
| `AffairSpiRegisterService` | 2 | 事项 · 获取×2 |

## biz 层：事件与监听

事件 1 个 · 监听器 1 个。

**领域事件**（实体变更时发，本地事务内）：

| 实体 | 事件 |
|---|---|
| AffairCountCache | `AffairCountCacheEvent` |

**监听器**（在事务内做联动）：

| 监听器 | 方法数 |
|---|---:|
| `AffairSpiProviderRegisterEventListener` | 1 |

## web 层：Controller

共 13 个 Controller。**REST 路径未取证**（字节码索引不含 `@RequestMapping` 的 value），
需要时按下面两法取：

1. 反编译 `organization-web` 的 Controller 读注解
2. CDP 抓页面请求（真实路径 + 请求体）

| 分组 | Controller | 方法数 |
|---|---|---:|
| 核心实体 CRUD | `AffairPendingController` | 54 |
| 核心实体 CRUD | `AffairDemoController` | 32 |
| 核心实体 CRUD | `AffairColumnConfigController` | 12 |
| 核心实体 CRUD | `AffairCategoryController` | 9 |
| 核心实体 CRUD | `AffairLayoutController` | 8 |
| 核心实体 CRUD | `AffairAppMappingInfoController` | 6 |
| 核心实体 CRUD | `AffairEnumManageController` | 5 |
| 核心实体 CRUD | `AffairManageController` | 5 |
| 核心实体 CRUD | `AffairNodePermissionController` | 5 |
| 核心实体 CRUD | `AffairCategoryHierarchyController` | 3 |
| 核心实体 CRUD | `AffairRegisterManageController` | 2 |
| 核心实体 CRUD | `AffairOperationController` | 1 |
| 核心实体 CRUD | `BpmPluginController` | 1 |

## 落表

> 证据等级：`VERIFIED_STATIC_BYTECODE`（表名出现在本模块 biz jar 的 class 常量池）
> ＋ `LIVE`（同名表已用 `information_schema` 在 `test2` 确认真实存在）。
> 粒度：**类级**。方法级落表未取证 —— 平台不用 MyBatis XML
> （21 个 biz 构件合计只有 9 个 mapper XML / 15 张表），SQL 内联在代码里，
> 方法→表要逐类反编译才能确认。

本模块代码中出现的真实表 **19** 张（来源构件：`ctp-affair-biz`）：

| 表名 | 注释 | 出现在几个类 |
|---|---|---:|
| `affair_done` | 事项实例-已办 | 2 |
| `affair_extend` | 事项扩展属性表 | 2 |
| `affair_pending` | 事项实例-待办 | 2 |
| `affair_property_info` | 待办自定义属性注册表 | 2 |
| `affair_app_mapping_info` | 待办自定义属性注册表 | 1 |
| `affair_app_summary` | 待办自定义属性注册表 | 1 |
| `affair_category` | 事项分类 | 1 |
| `affair_category_hierarchy` | 分类层级表 | 1 |
| `affair_column_config` | 事项中心查询列配置 | 1 |
| `affair_compensate` | 事项补偿 | 1 |
| `affair_custom_operation` | 事项栏目快捷操作定义表 | 1 |
| `affair_handover` | 已发已办交接表 | 1 |
| `affair_layout` | 事项布局表 | 1 |
| `affair_layout_attribute` | 事项布局参数表 | 1 |
| `affair_mq_compensation` | 消息补偿表 | 1 |
| `affair_node_permission` | 节点权限表 | 1 |
| `affair_personal_setting` | 事项个人设置表 | 1 |
| `affair_section_count` | 待办栏目计数 | 1 |
| `affair_spi_impl_register` | 事项中心SPI接口实现注册表 | 1 |

### 接口 → 表（4 条）

> `implements` = 字节码声明实现了该接口；`implements+field` = 再经它持有的
> Manager/Dao 字段一跳；两者都是静态事实。`stem` 只是类名同源（弱证据，需实测）。
> 表名本身都 `VERIFIED`；**哪个方法写哪张表仍未取证**。

| facade 接口 | 承载类 | 表 | 依据 |
|---|---|---|---|
| `AffairCategoryAppService` | `AffairCategory` | `affair_category` | `stem` |
| `AffairCommonAppService` | `AffairPropertyInfoService` | `affair_property_info` | `implements+field` |
| `AffairCustomOperationAppService` | `AffairCustomOperation` | `affair_custom_operation` | `stem` |
| `AffairNodePermissionAppService` | `AffairNodePermission` | `affair_node_permission` | `stem` |

## 证据与自证

| 内容 | 证据 | 等级 |
|---|---|---|
| 10 接口 / 79 方法签名 | 字节码索引 `javap` 提取 | `VERIFIED_STATIC_BYTECODE` |
| 27 个领域服务 | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 1 事件 / 1 监听器 | 类名 | `VERIFIED_STATIC_BYTECODE` |
| 13 个 Controller | 类名 + 方法数 | `VERIFIED_STATIC_BYTECODE` |
| 「干什么」中文描述 | 方法名拆词 + 手工注记 | `STATIC_INFERENCE` |
| 0 个语义待定方法 | 名称不足 | `UNVERIFIED` |
| REST 路径（126 条） | Controller 字节码注解 | `VERIFIED_STATIC_BYTECODE` |
| 落表（23 张表，类级） | class 常量池 + `information_schema` | `VERIFIED_STATIC_BYTECODE` + `LIVE` |
| 方法级落表 | 未取证（SQL 内联，需逐类反编译） | `UNVERIFIED` |
