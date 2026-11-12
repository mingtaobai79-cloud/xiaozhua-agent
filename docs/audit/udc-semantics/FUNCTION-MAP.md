# UDC 设计器「页面 → 功能 → 接口」功能地图 v2

> 日期：2026-10-13 | 证据：STATIC（前端 chunk + 后端 javap 657 契约）
> **证据分级**：direct_ops=可靠（页面自身模块）｜possible_ops=require闭包（被 store 洪泛，仅规模参考）
> op→后端契约映射 = 核心资产（前端 op 名 ↔ 后端 method+path）

## 1. op 目录（56 域）

| 域 | 写 | 读 | 其它 | 合计 |
|---|---|---|---|---|
| Page | 27 | 19 | 2 | 48 |
| Microflow | 15 | 28 | 12 | 55 |
| Entity | 17 | 17 | 6 | 40 |
| Application | 16 | 14 | 6 | 36 |
| Data | 14 | 10 | 2 | 26 |
| Sandbox | 12 | 12 | 12 | 36 |
| Meta | 0 | 18 | 2 | 20 |
| Udc | 5 | 8 | 2 | 15 |
| Deduction | 5 | 6 | 5 | 16 |
| Scalability | 5 | 5 | 2 | 12 |
| Event | 5 | 4 | 1 | 10 |
| Attribute | 7 | 1 | 0 | 8 |
| Function | 6 | 2 | 2 | 10 |
| Message | 6 | 2 | 0 | 8 |
| Backend | 3 | 4 | 0 | 7 |
| Form | 7 | 0 | 0 | 7 |
| Portal | 5 | 2 | 0 | 7 |
| Portlet | 6 | 1 | 0 | 7 |
| Micro | 5 | 1 | 0 | 6 |
| Refer | 4 | 2 | 0 | 6 |
| Custom | 4 | 1 | 1 | 6 |
| Index | 3 | 2 | 1 | 6 |
| Runtime | 3 | 2 | 1 | 6 |
| Affair | 2 | 2 | 1 | 5 |
| Associate | 2 | 2 | 3 | 7 |
| Collaboration | 3 | 1 | 1 | 5 |
| Deployment | 3 | 0 | 0 | 3 |
| Operation | 0 | 3 | 1 | 4 |
| Ctp | 2 | 0 | 1 | 3 |
| File | 0 | 2 | 1 | 3 |
| Image | 0 | 2 | 0 | 2 |
| Multi | 2 | 0 | 0 | 2 |
| Other | 0 | 2 | 1 | 3 |
| System | 1 | 1 | 0 | 2 |
| Attachment | 1 | 0 | 0 | 1 |
| Cdp | 0 | 1 | 0 | 1 |
| Design | 0 | 1 | 0 | 1 |
| Enum | 0 | 1 | 0 | 1 |
| Env | 0 | 1 | 0 | 1 |
| Excel | 0 | 1 | 0 | 1 |
| Expression | 0 | 1 | 1 | 2 |
| Feature | 0 | 1 | 0 | 1 |
| Manager | 0 | 1 | 1 | 2 |
| Node | 0 | 1 | 0 | 1 |
| Pinyin | 0 | 1 | 0 | 1 |
| Serial | 0 | 1 | 0 | 1 |
| Stereotype | 0 | 1 | 0 | 1 |
| Theme | 0 | 1 | 0 | 1 |
| User | 0 | 1 | 0 | 1 |
| Condition | 0 | 0 | 1 | 1 |
| Template | 0 | 0 | 1 | 1 |

## 2. 前端 op → 后端契约（核心映射）

前端 346 op 中 **173** 匹配后端 657 方法级契约。

- `udcApplicationAppVersionAppGuidPost` → ApplicationController.selectAppVersionByAppGuid `/udc/application/appVersion/{appGuid}`
- `udcApplicationCopyGet` → ApplicationController.copyApp `/udc/application/copy`
- `udcApplicationCopyPost` → ApplicationController.copyApp `/udc/application/copy`
- `udcApplicationCreateFromTemplatePost` → ApplicationController.createFromTemplate `/udc/application/create-from-template`
- `udcApplicationDeleteByGuidPost` → ApplicationController.deleteByGuid `/udc/application/delete-by-guid`
- `udcApplicationDeletePost` → ApplicationController.deleteById `/udc/application/delete-rename`
- `udcApplicationDependentApplicationCreateBatchPost` → ApplicationController.createDepAppBatch `/udc/application/dependent-application/create-batch`
- `udcApplicationDependentApplicationDeleteByIdPost` → ApplicationController.deleteDepAppsByAppId `/udc/application/dependent-application/delete-by-app-id`
- `udcApplicationDependentApplicationSelectByConditionPost` → ApplicationController.selectDepByCondition `/udc/application/dependent-application/select-by-condition`
- `udcApplicationDependentApplicationVersionUpdateBatchPost` → ApplicationController.updateBatchDepAppVersion `/udc/application/dependent-application/version/update-batch`
- `udcApplicationDependentApplicationVersionUpdatePost` → ApplicationController.updateDepAppVersion `/udc/application/dependent-application/version/update`
- `udcApplicationDetailGet` → ApplicationController.selectDetailById `/udc/application/detail/{id}`
- `udcApplicationDoDetectionPost` → ApplicationController.detectionByAppId `/udc/application/do/detection`
- `udcApplicationDoDetectionStatePost` → ApplicationController.runDetectionState `/udc/application/do/detection-state`
- `udcApplicationFetchLastVersionMetadataPost` → ApplicationController.fetchLastVersionMetadata `/udc/application/fetch-last-version-metadata`
- `udcApplicationGet` → ApplicationController.create `/udc/application/create-layout-app`
- `udcApplicationMultiVersionPost` → ApplicationController.selectMultiVersion `/udc/application/multi-version`
- `udcApplicationPost` → ApplicationController.create `/udc/application/create-layout-app`
- `udcApplicationRenewalAppEditingTimeGet` → ApplicationController.renewalAppEditingTime `/udc/application/renewal-app-editing-time/{id}`
- `udcApplicationSaveAsPost` → ApplicationController.saveAsTemplate `/udc/application/saveAsTemplate`
- `udcApplicationSchemaDownloadIdPost` → ApplicationController.downloadAppPackage `/udc/application/schema/download/{id}`
- `udcApplicationSearchDetectionPost` → ApplicationController.selectDetectionListByAppId `/udc/application/search/detection`
- `udcApplicationSearchNewWithVersionListPost` → ApplicationController.selectAppPageByConditionsWithVersion `/udc/application/search-new-with-version-list`
- `udcApplicationSearchPageByGuidPost` → ApplicationController.selectAppPageByGuid `/udc/application/search-page-by-guid`
- `udcApplicationSearchTemplatePost` → ApplicationController.selectTemplateAppPageByConditions `/udc/application/search-template`
- `udcApplicationUpdatePost` → ApplicationController.update `/udc/application/update`
- `udcApplicationVersionPlatformGet` → ApplicationController.selectPlatformVersion `/udc/application/version/platform`
- `udcApplicationVersionPlatformServiceGet` → ApplicationController.selectPlatformVersionMap `/udc/application/version/platform-service`
- `udcAttributeGroupEntityGet` → AttributeGroupController.selectListByEntityId `/udc/attribute-group/{entityId}`
- `udcAttributeGroupOperateBatchPost` → AttributeGroupController.operateBatch `/udc/attribute-group/operate-batch`
- `udcAttributeSetDeletePost` → AttributeSetController.deleteById `/udc/attributeSet/delete`
- `udcAttributeSetPost` → AttributeSetController.create `/udc/attributeSet`
- `udcAttributeSetSearchTermPost` → AttributeSetController.selectListByTerm `/udc/attributeSet/search/term`
- `udcAttributeSetUpdatePost` → AttributeSetController.update `/udc/attributeSet/update`
- `udcCollaborationAppGet` → AppCollaborationController.selectCollaborationRecordsByAppId `/udc/collaboration/{appId}`
- `udcDataFlowAppAppGet` → DataFlowDesignController.selectByAppId `/udc/data-flow/app/{appId}`
- `udcDataFlowListEntityPost` → DataFlowDesignController.selectEntityListByCondition `/udc/data-flow/list/entity`
- `udcDataFlowListManuallyMappingPost` → DataFlowDesignController.selectManuallyMapping `/udc/data-flow/list/manually/mapping`
- `udcDataFlowMappingGet` → DataFlowDesignController.selectMappingCountByEntityId `/udc/data-flow/mapping/count`
- `udcDataFlowMappingInitDataPost` → DataFlowDesignController.selectMappingInitData `/udc/data-flow/mapping/init-data`
- `udcDataTransferObjectCreateDtoPost` → DataTransferObjectController.createDtoWithAttrs `/udc/data-transfer-object/create-dto`
- `udcDataTransferObjectCreateDtoWithAttrsPost` → DataTransferObjectController.createDtoWithAttrsAndRefDtos `/udc/data-transfer-object/create-dto-with-attrs`
- `udcDataTransferObjectDeleteDtoWithAttrsPost` → DataTransferObjectController.deleteDtoWithAttrsAndRefDtos `/udc/data-transfer-object/delete-dto-with-attrs`
- `udcDataTransferObjectDeletePost` → DataTransferObjectController.deleteById `/udc/data-transfer-object/delete`
- `udcDataTransferObjectGet` → DataTransferObjectController.create `/udc/data-transfer-object/创建数据传输对象`
- `udcDataTransferObjectSelectDtoGet` → DataTransferObjectController.selectDtoWithAttrsById `/udc/data-transfer-object/select-dto/{id}`
- `udcDataTransferObjectSelectDtoWithAttrsGet` → DataTransferObjectController.selectDtoWithAttrsAndRefDtos `/udc/data-transfer-object/select-dto-with-attrs/{id}`
- `udcDataTransferObjectUpdateDtoPost` → DataTransferObjectController.updateDtoWithAttrs `/udc/data-transfer-object/update-dto`
- `udcDataTransferObjectUpdateDtoWithAttrsPost` → DataTransferObjectController.updateDtoWithAttrsAndRefDtos `/udc/data-transfer-object/update-dto-with-attrs`
- `udcDataTypeDataTypesByAppIdAppGet` → DataTypeController.selectDataTypesByAppId `/udc/data-type/data-types-by-app-id/{appId}`
- `udcDataTypeDataTypesParamGet` → DataTypeController.selectParameterDataTypes `/udc/data-type/data-types/param`
- `udcDataTypeSelectByParamsPost` → DataTypeController.selectDataTypeByParams `/udc/data-type/select-by-params`
- `udcDeductionEntityListPost` → DeductionRuleController.selectEntityListByCondition `/udc/deduction/entity/list`
- `udcDeductionMapAppAppGet` → DeductionRuleController.selectByAppId `/udc/deduction/map/app/{appId}`
- `udcDeductionMapDeletePost` → DeductionRuleController.deleteById `/udc/deduction/map/delete`
- `udcDeductionMapGet` → DeductionRuleController.create `/udc/deduction/map`
- `udcDeductionMapPost` → DeductionRuleController.create `/udc/deduction/map`
- `udcDeductionMapUpdatePost` → DeductionRuleController.update `/udc/deduction/map/update`
- `udcDeductionRuleDeletePost` → DeductionRuleController.deleteRuleById `/udc/deduction/rule/delete`
- `udcDeductionRuleGet` → DeductionRuleController.createRule `/udc/deduction/rule`
- `udcDeductionRuleInitDataPost` → DeductionRuleController.initData `/udc/deduction/rule/init-data`
- `udcDeductionRulePost` → DeductionRuleController.createRule `/udc/deduction/rule`
- `udcDeductionRuleSearch` → DeductionRuleController.selectRuleListByCondition `/udc/deduction/rule/search`
- `udcDeductionRuleUpdatePost` → DeductionRuleController.updateRule `/udc/deduction/rule/update`
- `udcDeductionValidRulePost` → DeductionRuleController.validRule `/udc/deduction/validRule`
- `udcDesignMetadataAggEntityExcludeBootGet` → UdcDesignMetadataController.selectAggEntityMetadataExcludeBoot `/udc/design-metadata/agg-entity-exclude-boot`
- `udcEntityAttributeBatchDeletePost` → EntityController.deleteAttributeByIds `/udc/entity/attribute/batch-delete`
- `udcEntityAttributeGet` → AttributeGroupController.selectListByEntityId `/udc/attribute-group/{entityId}`
- `udcEntityAttributeGroupBathUpdatePost` → EntityController.selectEntityAttributeGroupList `/udc/entity/attribute-group/bath-update`
- `udcEntityAttributePost` → AttributeGroupController.selectListByEntityId `/udc/attribute-group/{entityId}`
- `udcEntityAttributeSelectByPrimaryGet` → EntityController.selectByPrimaryEntityId `/udc/entity/attribute/select-by-primary/{id}`
- `udcEntityAttributeUpdatePost` → EntityController.updateAttribute `/udc/entity/attribute/update`
- `udcEntityBatchDeletePost` → EntityController.deleteByIds `/udc/entity/batch-delete`
- `udcEntityDeletePost` → EntityController.deleteById `/udc/entity/delete`
- `udcEntityPost` → AttributeGroupController.selectListByEntityId `/udc/attribute-group/{entityId}`
- `udcEntityPrimarySelectByAppidAppGet` → EntityController.selectPrimaryEntityByAppId `/udc/entity/primary/select-by-appid/{appId}`
- `udcEntitySelectAllByAppidAppGet` → EntityController.selectAllEntitiesByAppId `/udc/entity/select-all-by-appid/{appId}`
- `udcEntitySelectAllByEntityIdGet` → EntityController.selectAllEntitiesByAppId `/udc/entity/select-all-by-appid/{appId}`
- `udcEntitySelectEventDataByEntityIdGet` → EntityController.selectEventDatasByEntityId `/udc/entity/select-event-data-by-entityId/{id}`
- `udcEntityUpdatePost` → EntityController.update `/udc/entity/update`
- `udcEventCreateWithDataPost` → EventController.createWithEventData `/udc/event/create-with-data`
- `udcEventDeleteBatchPost` → EventController.deleteByIds `/udc/event/delete-batch`
- `udcEventDeletePost` → EventController.deleteById `/udc/event/delete`
- `udcEventGet` → DataFlowDesignController.selectEntityListByAppId `/udc/data-flow/list/event/entity`
- `udcEventListPost` → DataFlowDesignController.selectEntityListByAppId `/udc/data-flow/list/event/entity`
- `udcEventPost` → DataFlowDesignController.selectEntityListByAppId `/udc/data-flow/list/event/entity`
- `udcEventSearchTermPost` → EventController.selectListWithDataByTerm `/udc/event/search/term`
- `udcEventSelectWithDataGet` → EventController.selectEvents `/udc/event/select-with-data/{id}`
- `udcEventUpdatePost` → EventController.update `/udc/event/update`
- `udcEventUpdateWithDataPost` → EventController.updateWithEventData `/udc/event/update-with-data`
- `udcFeatureListGet` → FeatureController.list `/udc/feature/list`
- `udcFunctionBatchDeletePost` → FunctionNodeController.batchDeleteFunction `/udc/function/batch-delete`
- `udcFunctionCopyPost` → FunctionNodeController.copyFunction `/udc/function/copy`
- `udcFunctionDeletePost` → FunctionNodeController.deleteFunction `/udc/function/delete`
- `udcFunctionDeleteReferPagePost` → FunctionNodeController.deleteFunctionReferPage `/udc/function/delete/refer-page`
- `udcFunctionGet` → FunctionNodeController.createFunction `/udc/function`
- `udcFunctionPost` → FunctionNodeController.createFunction `/udc/function`
- `udcFunctionUpdatePost` → FunctionNodeController.updateFunction `/udc/function/update`
- `udcManagerComponentLogPost` → UdcManagerController.getComponentLogs `/udc/manager/component/log`
- `udcMetaDataMergeReferPost` → MetaDataController.mergeReferMetaData `/udc/meta-data/merge-refer-by-map`
- `udcMetaDataReferAndAppPost` → MetaDataController.selectReferAndAppMetadataByEntity `/udc/meta-data/refer-and-app`
- `udcMetaDataSearchAvailableAppMultiVersionPost` → MetaDataController.selectPageAvailableAppMultiVersionMetaDataByCondition `/udc/meta-data/search-available-app-multi-version`
- `udcMetaDataSearchAvailableUpgradeAppGet` → MetaDataController.selectAvailableUpgradeAppMetadataById `/udc/meta-data/search-available-upgrade-app/{id}`
- `udcMetaDataSelectAggregationEntityEntityGet` → MetaDataController.selectAggEntityIncludeAssociation `/udc/meta-data/select-aggregation-entity/{entityId}`
- `udcMetaDataSelectAggregationEntityPost` → MetaDataController.selectAggEntityIncludeAssociation `/udc/meta-data/select-aggregation-entity/{entityId}`
- `udcMetaDataSelectAllLayoutByAppPost` → MetaDataController.selectAllLayoutMetaDataByApp `/udc/meta-data/select-all-layout-by-app`
- `udcMetaDataSelectAppByIdPost` → MetaDataController.selectEntityMetaDataByAppId `/udc/meta-data/select-entity-by-app-id/{appId}`
- `udcMetaDataSelectCtpEnumAppGet` → MetaDataController.selectCtpEnumMetaDataListData `/udc/meta-data/select-ctp-enum-by-app`
- `udcMetaDataSelectCustomReferPageGet` → MetaDataController.selectCustomReferMetaDataByPageId `/udc/meta-data/select-custom-refer/{pageId}`
- `udcMetaDataSelectEntityByAppIdAppGet` → MetaDataController.selectEntityMetaDataByAppId `/udc/meta-data/select-entity-by-app-id/{appId}`
- `udcMetaDataSelectEntityPost` → MetaDataController.selectEntityMetaDataByAppId `/udc/meta-data/select-entity-by-app-id/{appId}`
- `udcMetaDataSelectJavaEnumByAppPost` → MetaDataController.selectJavaEnumMetaDataList `/udc/meta-data/select-java-enum-by-app`
- `udcMetaDataSelectJavaEnumItemPost` → MetaDataController.selectJavaEnumItemMetaDataList `/udc/meta-data/select-java-enum-item`
- `udcMetaDataSelectPageLayoutPost` → MetaDataController.selectPageLayoutInfoMetaData `/udc/meta-data/select-page-layout-info`
- `udcMicroFlowGroupBatchMovePost` → MicroFlowGroupController.batchMove `/udc/micro-flow-group/batch-move`
- `udcMicroFlowGroupCreatePost` → MicroFlowGroupController.create `/udc/micro-flow-group/create`
- `udcMicroFlowGroupDeleteBatchPost` → MicroFlowGroupController.deleteBatchGroupAndContent `/udc/micro-flow-group/delete-batch`
- `udcMicroFlowGroupDeletePost` → MicroFlowGroupController.deleteById `/udc/micro-flow-group/delete`
- `udcMicroFlowGroupSelectByTypePost` → MicroFlowGroupController.selectByAppId `/udc/micro-flow-group/select-by-type`
- `udcMicroFlowGroupUpdatePost` → MicroFlowController.updateOrderNoAndGroup `/udc/microflow/update/order-no-and-group`
- `udcMicroflowBatchMovePost` → MicroFlowController.batchMove `/udc/microflow/batch-move`
- `udcMicroflowCopy` → MicroFlowController.copyPageRuleBoundControl `/udc/microflow/copy/page-rule-bound-control`
- `udcMicroflowCopyPageRuleBoundControlPost` → MicroFlowController.copyPageRuleBoundControl `/udc/microflow/copy/page-rule-bound-control`
- `udcMicroflowCreateMessagePost` → MicroFlowController.createMessage `/udc/microflow/create-message`
- `udcMicroflowDeletePost` → MicroFlowController.deleteBySourceId `/udc/microflow/delete-by-source-id`
- `udcMicroflowFindByIdGet` → MicroFlowController.getMicroFlowDefinition `/udc/microflow/findById/{id}`
- `udcMicroflowMessageDtoDeletePost` → MicroFlowController.deleteMessageById `/udc/microflow/message-dto/delete`
- `udcMicroflowSearch` → DataTransferObjectController.selectMicroFlowCustomDtoByAppId `/udc/data-transfer-object/search-micro-flow-custom-dto/{appId}`
- `udcMicroflowSearchEntityRulePost` → MicroFlowController.selectEntityRulePageByEntityId `/udc/microflow/search/entityRule`
- `udcMicroflowSelectMessageGet` → MicroFlowController.selectMessageDtoWithAttrsById `/udc/microflow/select-message/{id}`
- `udcMicroflowUpdateMessagePost` → MicroFlowController.updateMessage `/udc/microflow/update-message`
- `udcOperationLogGet` → OperationLogController.search `/udc/operation-log/search`
- `udcPageInfoDeletePost` → PageInfoController.deleteById `/udc/page-info/delete`
- `udcPageInfoRelationInfoRelationGroupIdPost` → PageInfoController.findPageByRelationId `/udc/page-info/relation-info/relationGroupId`
- `udcPageLayoutRelationInfoIdPost` → PageLayoutController.findPageByRelationId `/udc/page-layout/relation-info/id`
- `udcPageTemplateDeleteByIdsPost` → PageTemplateController.deleteById `/udc/page-template/delete-by-ids`
- `udcPageTemplatePublishPost` → PageTemplatePublishedController.deleteById `/udc/page-template/published/delete-by-ids`
- `udcPageTemplatePublishedDeleteByIdsPost` → PageTemplatePublishedController.deleteById `/udc/page-template/published/delete-by-ids`
- `udcPortletCreatePortletPost` → PortletController.createPortlet `/udc/portlet/create-portlet`
- `udcPortletCreatePost` → PortletController.createPortlet `/udc/portlet/create-portlet`
- `udcPortletSortPost` → PortletController.portletSort `/udc/portlet/sort`
- `udcPortletUpdatePortletPost` → PortletController.updatePortlet `/udc/update-portlet`
- `udcPortletUpdatePost` → PortletController.updatePortlet `/udc/update-portlet`
- `udcReferConfigCreateConfigInfoPost` → ReferConfigController.createConfigInfo `/udc/refer-config/create-config-info`
- `udcReferConfigCreateOrUpdatePost` → ReferConfigController.createOrUpdate `/udc/refer-config/create-or-update`
- `udcReferConfigDeleteByGroupIdPost` → ReferConfigController.deleteByGroupId `/udc/refer-config/delete-by-group-id`
- `udcReferConfigListPost` → ReferConfigController.selectListByConditions `/udc/refer-config/list`
- `udcReferConfigUpdateConfigInfoPost` → ReferConfigController.updateConfigInfo `/udc/refer-config/update-config-info`
- `udcRuntimeDeployFormPost` → DeployController.deployForm `/udc/runtime/deploy-form`
- `udcRuntimeDeployPost` → DeployController.deployStop `/udc/runtime/deploy/stop/{deployId}`
- `udcScalabilityBatchDeletePost` → ScalabilityController.deleteByIds `/udc/scalability/batch-delete`
- `udcScalabilityDeletePost` → ScalabilityController.deleteById `/udc/scalability/delete`
- `udcScalabilityOptionDataTypeAppGet` → ScalabilityOptionController.selectScalabilityDataType `/udc/scalability-option/data-type/{appId}`
- `udcScalabilityOptionDeletePost` → ScalabilityOptionController.deleteById `/udc/scalability-option/delete`
- `udcScalabilityOptionOptionGet` → ScalabilityController.selectByOptionId `/udc/scalability/option/{optionId}`
- `udcScalabilityOptionPost` → ScalabilityController.selectByOptionId `/udc/scalability/option/{optionId}`
- `udcScalabilityOptionSelectByAppidTreeAppGet` → ScalabilityOptionController.selectByAppId `/udc/scalability-option/select-by-appid/tree/{appId}`
- `udcScalabilityOptionUpdatePost` → ScalabilityOptionController.update `/udc/scalability-option/update`
- `udcScalabilityPost` → ScalabilityController.create `/udc/scalability`
- `udcScalabilityUpdatePost` → ScalabilityController.update `/udc/scalability/update`
- `udcStereotypeListGet` → StereotypeController.list `/udc/stereotype/list`
- `udcUdcEnumCategoryDeletePost` → UdcEnumCategoryController.deleteById `/udc/udc-enum-category/delete`
- `udcUdcEnumCategoryPost` → UdcEnumCategoryController.create `/udc/udc-enum-category/创建枚举分类`
- `udcUdcEnumCategorySelectCategoryAndEnumPost` → UdcEnumCategoryController.selectCategoryAndEnum `/udc/udc-enum-category/select-category-and-enum`
- `udcUdcEnumCategoryUpdatePost` → UdcEnumCategoryController.update `/udc/udc-enum-category/update`
- `udcUdcEnumDeletePost` → UdcEnumCategoryController.deleteById `/udc/udc-enum-category/delete`
- `udcUdcEnumItemGet` → MetaDataController.selectCtpEnumItemList `/udc/meta-data/select-ctp-enum-item`
- `udcUdcEnumItemListPost` → UdcEnumItemController.selectListByConditions `/udc/udc-enum-item/list`
- `udcUdcEnumItemOperateBatchPost` → UdcEnumItemController.operateBatch `/udc/udc-enum-item/operate-batch`
- `udcUdcEnumItemSearch` → UdcCtpEnumController.selectByEnumCode `/udc/udc-enum-item/search-by-enum-code`
- `udcUdcEnumPost` → EntityController.selectParentEnumAttributes `/udc/entity/attribute/select-parent-enum-attrs`
- `udcUdcEnumSearch` → MicroFlowController.searchEnumByAppName `/udc/search/enum-by-appName`
- `udcUdcEnumUpdatePost` → UdcEnumCategoryController.update `/udc/udc-enum-category/update`

## 3. 页面 UI 骨架 + 直接 op

### src_pages_udc_sandbox_pages_elastic-deployment_index_tsx.b0321575.js

- 按钮：删除成功、查看应用
- 组件：—
- 拖拽：无
- **直接调用接口**（15）：udcCtpManagerSandboxUsePost、udcSandboxAppCheckAlertPost、udcSandboxAppCleanRestartAppPost、udcSandboxAppReleaseAppPost、udcSandboxAppReleaseAppStatusPost、udcSandboxAppStartAppPost、udcSandboxAppStopAppPost、udcSandboxAppUnLoadAppPost、udcSandboxClientCheckAllStatusGet、udcSandboxClientCheckAllTaskGet、udcSandboxClientCreateGet、udcSandboxClientDeleteGet、udcSandboxClientRestartGet、udcSandboxClientSearch、udcSandboxSystemConfigSetReleaseConfigPost

### src_pages_udc_sandbox_pages_sandbox-resource_index_tsx-src_pages_udc_sandbox_c

- 按钮：保存成功、删除、删除成功、取消、新增、新增成功、是否确定删除、查看、确定、编辑
- 组件：Form.useForm、Radio.Group、Select.Option
- 拖拽：无
- **直接调用接口**（15）：udcCtpManagerSandboxUsePost、udcSandboxAppCheckAlertPost、udcSandboxAppCleanRestartAppPost、udcSandboxAppReleaseAppPost、udcSandboxAppReleaseAppStatusPost、udcSandboxAppStartAppPost、udcSandboxAppStopAppPost、udcSandboxAppUnLoadAppPost、udcSandboxClientCheckAllStatusGet、udcSandboxClientCheckAllTaskGet、udcSandboxClientCreateGet、udcSandboxClientDeleteGet、udcSandboxClientRestartGet、udcSandboxClientSearch、udcSandboxSystemConfigSetReleaseConfigPost

### src_pages_udc_application_index_tsx.a0f20272.js

- 按钮：上传文件、删除、发布、发布应用、发布版本、发布目标环境、取消、复制、复制应用、导入应用、导入应用包、导入方式、导出、导出应用、导出应用成功、应用包导入失败、应用包导入成功、应用复制失败、确定、请先上传应用包、请选择发布版本
- 组件：Form.Item、Form.useForm、Menu.Item、Radio.Group、Select.Option
- 拖拽：无
- **直接调用接口**（10）：udcFileDownloadUrlGet、udcFormUpgradeDeployDeletePost、udcFormUpgradeDeployExportRecordPost、udcFormUpgradeDeployListInfoPost、udcFormUpgradeDeployListRecordPost、udcFormUpgradeDeployNodeLastUpgradeResultGet、udcFormUpgradeDeployOneClickUpgradePost、udcFormUpgradeDeploySilentUpdatePost、udcRuntimeUpgradeAppListPost、udcRuntimeUpgradeHostAppNameListPost

### src_pages_udc_upgrade-deploy_index_tsx.0c901b15.js

- 按钮：删除成功、发布中、发布失败、发布成功、发布状态、发布类型、启用状态、已启用、未发布、未启用、移动端、自动生成不可编辑
- 组件：Checkbox.Group、Form.Item、Form.useForm
- 拖拽：无
- **直接调用接口**（10）：udcFileDownloadUrlGet、udcFormUpgradeDeployDeletePost、udcFormUpgradeDeployExportRecordPost、udcFormUpgradeDeployListInfoPost、udcFormUpgradeDeployListRecordPost、udcFormUpgradeDeployNodeLastUpgradeResultGet、udcFormUpgradeDeployOneClickUpgradePost、udcFormUpgradeDeploySilentUpdatePost、udcRuntimeUpgradeAppListPost、udcRuntimeUpgradeHostAppNameListPost

### src_constants_design_page-type_ts-src_services_app-design_template_ts-src_serv

- 按钮：全表编辑页、移动端
- 组件：—
- 拖拽：无
- **直接调用接口**（8）：udcFunctionFindTreeAndGroupPost、udcMetaDataSelectAllPageByAppPost、udcMetaDataSelectFunctionNodeWithPageTreePost、udcPageInfoPresetListAppGet、udcPageInfoSearchNoPagePost、udcPageTemplateClassSelectTreeCategoryGet、udcPageTemplateGet、udcPageTemplateSearchWithRightsPost

### src_pages_udc_sandbox_pages_application-test_index_tsx.ed62315f.js

- 按钮：删除、删除成功、新增、查看、编辑
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 拖拽：无
- **直接调用接口**（7）：udcSandboxAppCleanRestartAppPost、udcSandboxAppReleaseAppPost、udcSandboxAppReleaseAppStatusPost、udcSandboxAppStartAppPost、udcSandboxAppStopAppPost、udcSandboxAppUnLoadAppPost、udcSandboxSystemConfigSetReleaseConfigPost

### src_pages_app-design_basic-info_index_tsx-node_modules_seeyon_biz-icon-library

- 按钮：保存失败、保存成功、发布中、发布失败、发布成功、发布时间、发布版本、发布状态、取消、团队设置、已发布、未发布、添加成员、确定、确定删除吗、确认、移动端、移除成功、组件已停用、页面发布中、页面发布失败、页面发布开始、页面发布成功、页面发布资源不足、页面发布超时
- 组件：Collapse.Panel、Form.Item、Form.useForm、Menu.Item、Radio.Group
- 拖拽：无
- **直接调用接口**（6）：udcPageComponentAnalysisPackageGet、udcPageComponentRefreshGet、udcPageComponentSelectAllListByConditionsPost、udcPageComponentSelectByGet、udcPageComponentUpdatePost、udcPageComponentUploadGet

### src_pages_udc_cmps_index_tsx-node_modules_seeyon_biz-icon-library_dist_index_c

- 按钮：停用、前端组件同步日志、前端组件导入、启用、组件导入成功
- 组件：Form.Item、Form.useForm、Menu.Item、Radio.Group
- 拖拽：无
- **直接调用接口**（6）：udcPageComponentAnalysisPackageGet、udcPageComponentRefreshGet、udcPageComponentSelectAllListByConditionsPost、udcPageComponentSelectByGet、udcPageComponentUpdatePost、udcPageComponentUploadGet

### src_components_app-design_app_components_theme_app-style-designer-model_tsx-sr

- 按钮：—
- 组件：—
- 拖拽：无
- **直接调用接口**（2）：udcScalabilityOptionPost、udcScalabilityOptionUpdatePost
    - `udcScalabilityOptionPost` → ScalabilityController.selectByOptionId /udc/scalability/option/{optionId}
    - `udcScalabilityOptionUpdatePost` → ScalabilityOptionController.update /udc/scalability-option/update

### src_pages_udc_sandbox_pages_app-environment_index_tsx.c5de5775.js

- 按钮：删除、删除成功、新增、查看、编辑
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 拖拽：无
- **直接调用接口**（2）：udcCtpManagerTransferSavePost、udcCtpManagerTransferSelectGet

### src_components_design_settings_common_operate-list_operateCmp_operateCmp_tsx-s

- 按钮：—
- 组件：—
- 拖拽：无
- **直接调用接口**（1）：udcAttachmentTemplateCreateBatchPost

### src_pages_app-design_app-home_space-manage_SpaceManger_tsx.e54d3ae5.js

- 按钮：关闭、删除成功、请输入整数排序号
- 组件：Form.Item、Form.useForm、Radio.Group
- 拖拽：无
- **直接调用接口**（1）：udcPortalPortalSpaceDeletePost

### node_modules_seeyon_biz-enums_dist_index-7189faa2_js.4340c5f3.js

- 按钮：停用、取消、启用、排序号、排序号为必填项、新建、确定、编辑、编辑成功、请上传图片、连续新建
- 组件：Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-enums_dist_index-7e03e02d_js.a52b8615.js

- 按钮：停用、取消、启用、排序号、排序号为必填项、新建、确定、编辑、编辑成功、请上传图片、连续新建
- 组件：Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-enums_dist_index-9365ba29_js.e2c68411.js

- 按钮：停用、取消、启用、排序号、排序号为必填项、新建、确定、编辑、编辑成功、请上传图片、连续新建
- 组件：Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-enums_dist_index-d16a4f98_js.a84d1636.js

- 按钮：停用、取消、启用、排序号、排序号为必填项、新建、确定、编辑、编辑成功、请上传图片、连续新建
- 组件：Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-enums_dist_index-dfa7dac0_js.4ccc658d.js

- 按钮：停用、取消、启用、排序号、排序号为必填项、新建、确定、编辑、编辑成功、请上传图片、连续新建
- 组件：Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-serial-scheme_dist_index-63bbd6cd_js.14fc2408.js

- 按钮：绑定实体
- 组件：—
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-serial-scheme_dist_index-a9cbbe00_js.c3e8b8dd.js

- 按钮：绑定实体
- 组件：—
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-serial-scheme_dist_index-aa2d4add_js.0de18369.js

- 按钮：绑定实体
- 组件：—
- 拖拽：无
- **直接调用接口**（0）：—

### node_modules_seeyon_biz-serial-scheme_dist_index-f62267af_js.f827461e.js

- 按钮：绑定实体
- 组件：—
- 拖拽：无
- **直接调用接口**（0）：—

### src_components_app-design_parameter-definition_entry_tsx-src_redux_enhancer_in

- 按钮：保存成功、取消、已设置、已设置表达式、排序号、新建参数、确定
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 拖拽：无
- **直接调用接口**（0）：—

### src_components_app-design_parameter-definition_index_tsx.d0a30409.js

- 按钮：保存成功、取消、已设置、已设置表达式、排序号、新建参数、确定
- 组件：Form.Item、Form.useForm、Radio.Group、Select.Option
- 拖拽：无
- **直接调用接口**（0）：—

### src_components_common_component-select_useComponentsTree_ts-src_components_des

- 按钮：已设置表达式、新建页面规则、新建页面规则失败
- 组件：Form.Item、Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### src_components_design_asidetool_trans-wrapper_tsx-src_components_design_shortc

- 按钮：向上添加、新建方案、移除
- 组件：Form.Item、Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### src_components_design_asidetool_trans-wrapper_tsx-src_components_design_shortc

- 按钮：向上添加、新建方案、移除
- 组件：Form.Item、Form.useForm
- 拖拽：无
- **直接调用接口**（0）：—

### src_components_design_data-source_index_tsx.ecc90bb0.js

- 按钮：展开、拖拽数据操作取消
- 组件：—
- 拖拽：无
- **直接调用接口**（0）：—

