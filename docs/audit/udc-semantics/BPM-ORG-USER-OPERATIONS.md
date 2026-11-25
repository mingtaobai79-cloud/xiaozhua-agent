# BPM / ORG / USER 应用 操作面（facade API 契约，反编译 5.3.x）

**证据源**（本地 Artifactory 构件）：
- `bpm-facade-5.3.374.jar`（30 AppService / 132 方法）
- `organization-facade-5.3.368.jar`（44 AppService / 342 方法）
- `ctp-user-facade-5.3.429.jar`（41 AppService / 199 方法）

**共 115 AppService / 673 方法**。facade 是这些应用的**对外 API 契约层**（Web/Controller 在运行时 pod，
本地只有 facade jar）。方法名即操作语义，是"页面功能 → 请求 → 后端处理"中**后端处理**的契约面。

> 方法论（同 UDC）：前端功能 → REST/JSON → biz service → 交互表。
> BPM/ORG/USER 的 biz 实现在运行时 pod（NS `lowcode-test`），facade 是接口契约；
> 需要具体 DTO 字段约束时，从运行时 pod 反编译对应 `*-biz` 构件。

## 方法目录


# bpm (bpm-facade-5.3.374.jar) — 30 AppService

## BpmActionAppService（0）

## BpmActivityAppService（0）

## BpmApiFormPermissionAppService（12）
  create
  update
  deleteById
  selectByTemplateId
  selectById
  selectPermissionIncludeContentById
  selectByApplicationName
  selectByIds
  createOrUpdateBatch
  createBatchOrUpdateContent
  selectContentListByPermissionIds
  checkFormPermissionBatch

## BpmApiNodePermissionAppService（4）
  bpmNodePermissionHandel
  selectNodePermissionById
  savePermission
  savePermissionList

## BpmApiPermissionAppService（0）

## BpmApiProcessAppService（1）
  selectDiagramDetailByTemplateCodeAndVersion

## BpmAppService（22）
  send
  saveDraft
  submit
  stepBack
  repeal
  stop
  takeBack
  replace
  multipleReplace
  pause
  cancelPause
  superviseRelive
  superviseReliveFull
  inform
  addExecuteMember
  cancelItems
  batchDeal
  selectFullCaseInfo
  counterSignNode
  addNode
  deleteDraft
  deleteDraftAffair

## BpmApplicationOperateLogAppService（3）
  saveApplicationOperateLog
  selectNewestLogInfo
  updateAppLogs

## BpmAutoApprovalAppService（4）
  designerCreate
  designerUpdate
  designerDelete
  designerSelect

## BpmCaseAppService（2）
  selectCaseById
  selectMainCaseBySubCaseId

## BpmCaseLogAppService（2）
  selectByCaseId
  selectByDto

## BpmCoMiAppService（0）

## BpmDeployAppService（6）
  upgradeBpmTemplateVersion
  deployBpmTemplatesIndependent
  afterFormAppDataInit
  upgradeCommon
  autoDeployStartAndAuth
  usedFrames

## BpmDetailAppService（1）
  selectDetail

## BpmNodeAppService（0）

## BpmNodePermissionOperationAppService（2）
  getNodePermissionOperation
  selectOperationSimpleByPermissionIds

## BpmNormalAppMultiVersionAppService（1）
  selectCurrentHighestVersionBatch

## BpmOpinionAppService（2）
  selectOpinionGroupByActivityNodeWithObjectId
  deleteOpinion

## BpmProcessLogAppService（5）
  create
  createBatch
  selectLogList
  selectOriginalI18nLogList
  selectLogOriginalListByCaseIds

## BpmProcessTrackAppService（1）
  selectProcessTrackList

## BpmSuperviseAppService（3）
  search
  cancelFocus
  skip

## BpmTemplateAppService（32）
  createOrUpdate
  deleteById
  updateCategoryByApplicationId
  publishCheck
  publishCheckByAppInfo
  publishLock
  publishLockByAppInfo
  publishFinish
  cleanCacheByApplicationName
  startCheck
  start
  startByTemplateId
  startByTemplateIdWithoutAuth
  stop
  stopByTemplateId
  deleteByApps
  selectByApplicationName
  updateEffectTimeByTemplateId
  updateEffectTime
  updateAuthorized
  selectById
  selectByTemplateUrlId
  selectEffectedDiagramListByAppName
  selectTemplateUserGuidInfo
  selectTemplateById
  selectTemplateIdsByName
  selectTemplateByRootEntityId
  selectTemplateByParams
  selectUserTemplatePageList
  selectTemplateGuidByCategoryCode
  updateByAppName
  selectNodeDetail

## BpmTemplateManageAppService（8）
  grayAuthTemplate
  closeLowerVersionGrayAndStarted
  startByAppName
  selectFormalAuthTemplateList
  selectFormalAuthTemplateListByQueryDto
  selectGrayAuthTemplateList
  updateAuth
  invalidAppTemplatesByAppGuid

## BpmThirdTemplateSyncAppService（4）
  createBatch
  updateBatch
  createActivityResponsibilities
  createTemplateRecent

## BpmWorkItemAppService（0）

## BpmApiParamAppService（6）
  saveParamSchema
  saveParamData
  loadParamSchema
  loadParamTypes
  loadParamSchemaByOrigin
  deleteSettingByIds

## BpmApiSplitImportAppService（3）
  selectTemplateByAppName
  prepareApp
  splitImport

## BpmApiTransportAppService（6）
  saveAs
  getApplicationInitData
  getApplicationInitDataAsync
  exportTemplateInfo
  importTemplateInfo
  asyncTransportRequest

## BpmUpgrade51To52AppService（1）
  upgradeExtensionPlan

## BpmApiSimulationAppService（1）
  selectProcessPredictionResult

小计方法: 132

# org (organization-facade-5.3.368.jar) — 44 AppService

## OrgAffairAppService（1）
  selectByIdOrCode

## OrgAppCommonAppService（2）
  selectAccessViewMember
  selectAccessViewOrg

## AuthorizationAppService（1）
  registerAppResourceAndPermission

## OrgEdocAppService（1）
  selectSortByIds

## OrgMobileAppService（2）
  selectPagePhoneNumber
  selectOfflineStorageKey

## OcipLevelAppService（4）
  pushAll
  pushAllByIncrement
  pushBatch
  pushLevelIncrement

## OcipMemberAppService（4）
  pushAll
  pushAllByIncrement
  pushBatch
  pushMemberIncrement

## OcipPostAppService（4）
  pushAll
  pushAllByIncrement
  pushBatch
  pushPostIncrement

## OcipUnitAppService（8）
  pushAccountAll
  pushAccountAllByIncrement
  pushAccountBatch
  pushAccountIncrement
  pushDepartmentAll
  pushDepartmentAllByIncrement
  pushDepartmentIncrement
  pushDepartmentBatch

## OrgPlatformAppService（1）
  selectWatermarkInfoByMemberId

## OrgPortalAppService（10）
  selectSwitchInstitution
  selectSwitchInstitutions
  selectSwitchInstitutionByMemberId
  selectLoginUserInfo
  selectCurrentLoginUserInfo
  isOrgAdmin
  selectMainMemberPostByMemberId
  selectMainMemberPostByMemberIdsIgnoreTenant
  selectMainMemberPostByMemberIdsAllTenant
  selectPeopleTabCustomSet

## OrgJobSyncAppService（3）
  selectByCodes
  createBatch
  selectPageByConditions

## OrgLevelSyncAppService（3）
  selectByCodes
  createBatch
  selectPageByConditions

## OrgMemberSyncAppService（12）
  createBatch
  selectByCodes
  selectByCondition
  createBatchMemberPost
  createBatchMemberMetadata
  fixCtpUserId
  disableMember
  selectNaturalMemberByPhoneNumber
  selectNaturalMemberByCodes
  selectNaturalMemberInfoPageListByCondition
  selectOutSideInstitutionManagerPageByCondition
  createBatchNaturalMember

## OrgPostSyncAppService（3）
  createBatch
  selectByCodes
  selectPageByConditions

## OrgTeamSyncAppService（4）
  selectByCode
  selectPageByConditions
  create
  createBatch

## OrgUnitSyncAppService（7）
  createBatch
  createBatchUnitMetadata
  selectByCodes
  selectChildrenByCondition
  selectPageChildrenByCondition
  disableOrganization
  selectPageByConditions

## OrgWorkFlowAppService（30）
  selectMemberPostBySelectPeople
  selectMemberPostBySelectPeoples
  selectListByCondition
  selectListByMetaCondition
  isOfUp
  selectOfUp
  selectPreParameterKey
  selectMemberOfUnitMetadataOfMemberIds
  selectMemberOfMemberMetadataOfMemberIds
  selectMetadataListOfUnitMetadataOfMemberId
  selectMetadataListOfMemberMetadataOfMemberId
  funcMemberIn
  funcOrgIn
  funcMultMemberIn
  funcMultOrgIn
  funcOrgRoleIn
  selectMemberPostById
  getSelectPeopleDataWfJson
  selectSplitUnitNodeInfo
  selectSplitMemberNodeInfo
  selectNodeName
  selectNamesByIds
  getEntityNameBySelectPeoples
  selectPeopleCodeDataDto
  selectPeopleDataDtoFromTransData
  selectPeopleIdsCodeData
  selectPeopleIdsDataDtoFromTransData
  checkSelectPeopleData
  selectSortField
  selectMemberPostListByCondition

## OrgCommonAppService（35）
  selectMemberInfoById
  selectMemberDepartmentInfoById
  selectMemberBySelectPeopleData
  selectPageMemberBySelectPeopleData
  selectMemberBySelectPeopleDatas
  selectMemberBySelectPeopleDataJson
  selectPageMemberBySelectPeopleDataJson
  selectMemberBySelectPeopleDataJsons
  isMemberInSelectPeopleDataJson
  selectMemberByOrgId
  selectPageMemberByOrgId
  selectMemberCountByOrgId
  selectMemberByPostId
  selectMemberByJobId
  selectMemberByLevelId
  selectMemberByUserId
  selectChildrenOrgIdByCondition
  selectChildrenOrgByCondition
  selectOrgMetadataColumnList
  selectParentIds
  selectRoot
  selectOrgUnitTeamList
  isRole
  selectMemberOfUnitMetadataOfMemberId
  selectManagerDepartmentByMemberId
  selectLeaderDepartmentByMemberId
  selectAllDomainIdsByMemberId
  selectDomainIdsByMemberId
  selectDomainMapByMemberId
  fillSelectPeopleData
  canManage
  selectSecretMemberIds
  selectManageOrgByRole
  selectInOrgScopeIds
  selectEntityIdByCode

## OrgBusinessBaseAppService（10）
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions

## OrgBusinessCoreAppService（1）
  selectBusinessListByCondition

## OrgInstitutionExecutiveAppService（1）
  checkUserExecutiveHide

## OrgJobBaseAppService（14）
  create
  update
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  selectJobListPropertiesByJobIds
  selectJobPageListPropertiesByCondition
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions

## OrgJobCoreAppService（6）
  selectJobById
  selectJobByIds
  selectJobListByCondition
  selectJobPageListByCondition
  selectJobListPropertiesByJobIds
  selectJobPageListPropertiesByCondition

## OrgLevelBaseAppService（14）
  create
  update
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  selectLevelListPropertiesByLevelIds
  selectLevelPageListPropertiesByCondition
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions

## OrgLevelCoreAppService（6）
  selectLevelById
  selectLevelByIds
  selectLevelListByCondition
  selectLevelPageListByCondition
  selectLevelListPropertiesByLevelIds
  selectLevelPageListPropertiesByCondition

## OrgMemberBaseAppService（16）
  create
  update
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectMemberListByCondition
  selectPageByConditions
  selectMemberPageListByCondition
  selectMemberListPropertiesByMemberIds
  selectMemberPageListPropertiesByCondition
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions

## OrgMemberCoreAppService（13）
  selectMemberById
  selectMemberInfoById
  selectMemberByIds
  selectMemberByIdsIgnoreTenantId
  selectMemberInfoByIds
  selectMemberListByCondition
  selectMemberPageListByCondition
  selectMemberInfoListByCondition
  selectMemberInfoPageListByCondition
  selectMemberByCodeIgnoreTenant
  modifyMemberInfoBySelf
  selectMemberListPropertiesByMemberIds
  selectMemberPageListPropertiesByCondition

## OrgMemberPostBaseAppService（12）
  create
  update
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  dynamicJoinSelect
  selectMemberPostListPropertiesByMemberIds
  selectMemberPostPageListPropertiesByCondition
  dynamicSelect

## OrgMemberPostCoreAppService（5）
  selectMemberPostListByCondition
  selectMemberPostListByMemberIds
  selectMemberPostPageListByCondition
  selectMemberPostListPropertiesByMemberIds
  selectMemberPostPageListPropertiesByCondition

## OrgMemberRoleBaseAppService（11）
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions
  createOrUpdateBatch

## OrgMemberRoleCoreAppService（4）
  selectById
  selectByIds
  selectListByConditions
  selectPageByConditions

## OrgMetadataCoreAppService（12）
  selectOrgMetadataColumnListByCondition
  selectMetadataColumnList
  selectPageMetadataColumnList
  selectOrgByUnitMemberMetadata
  selectMemberByUnitMetadata
  selectMemberByUnitMemberMetadata
  selectMemberMetadataInfo
  selectOrgMetadataInfo
  selectOrgRoleByMemberMetadata
  selectOrgIdByMemberIdInInstitution
  selectEntityIdByMetadataValue
  selectEntityIdsByMetadataValue

## OrgRoleBaseAppService（11）
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions
  createOrUpdateBatch

## OrgRoleCoreAppService（4）
  selectById
  selectByIds
  selectListByConditions
  selectPageByConditions

## OrgPostBaseAppService（14）
  create
  update
  selectById
  selectByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectPageByConditions
  dynamicSelect
  selectPostListPropertiesByPostIds
  selectPostPageListPropertiesByCondition
  dynamicJoinSelect
  selectCascadeByConditions
  selectCascadeListByConditions

## OrgPostCoreAppService（6）
  selectPostById
  selectPostByIds
  selectPostListByCondition
  selectPostPageListByCondition
  selectPostListPropertiesByPostIds
  selectPostPageListPropertiesByCondition

## OrgSystemTeamCoreAppService（5）
  selectTeamMemberByTeamId
  selectTeamMemberByTeamIds
  selectTeamById
  selectTeamByIds
  selectTeamByCondition

## OrgUnitBaseAppService（20）
  create
  update
  selectById
  selectByIds
  selectOrgById
  selectOrgByIds
  selectCascadeById
  selectCascadeByIds
  selectListByConditions
  selectOrgListByCondition
  selectPageByConditions
  selectOrgPageListByCondition
  selectOrgListPropertiesByOrgIds
  selectOrgPageListPropertiesByCondition
  selectLegalByMemberId
  selectLegalIdByMemberId
  dynamicJoinSelect
  dynamicSelect
  selectCascadeByConditions
  selectCascadeListByConditions

## OrgUnitCoreAppService（13）
  selectOrgById
  selectOrgInfoById
  selectOrgByIds
  selectOrgByIdsIgnoreTenantId
  selectOrgInfoByIds
  selectOrgListByCondition
  selectOrgPageListByCondition
  selectOrgInfoListByCondition
  selectOrgInfoPageListByCondition
  selectMetadataPropertiesByOrgIds
  selectOrgListPropertiesByOrgIds
  selectOrgPageListPropertiesByCondition
  selectTraditionToSimpleNameByCondition

## OrgUnitTeamCoreAppService（6）
  create
  delete
  selectUnitTeamById
  selectUnitTeamByIds
  selectUnitTeamListByCondition
  selectUnitTeamPageListByCondition

## OrgUnitVerticalCoreAppService（1）
  selectUnitVerticalListByCondition

## OrgParameterCoreAppService（1）
  selectValueByParamsKey

## TenantManageAppService（1）
  selectEnableUnitNumIgnoreTenant

小计方法: 342

# user (ctp-user-facade-5.3.429.jar) — 41 AppService

## CtpApplicationBaseAppService（4）
  create
  update
  updateStatus
  updateOnlineStatus

## CtpApplicationCommonAppService（9）
  selectCategoryApplications
  selectCategorySetting
  selectApplicationsByCategoryAndClientScope
  selectAdminAppIdsByUserIdAndOrgId
  selectEnabledApplications
  isEnabled
  selectUserMenuAndPortal
  selectEntityManageOrgIdByAppId
  register

## CtpApplicationAuthCoreAppService（4）
  selectApplicationAuthByAppId
  selectAuthAppIdsByOrgId
  selectAuthAppIds
  selectWithOutAuthAllAppIdsByOrgId

## CtpApplicationCoreAppService（3）
  selectListByConditions
  selectPageByConditions
  selectAppStatusListIgnoreTenantId

## CtpCapabilityCoreAppService（1）
  selectListByConditions

## CtpCategoryCoreAppService（2）
  selectListByConditions
  selectQuickListByConditions

## CtpPersonalPlanCoreAppService（3）
  createOrUpdateBatch
  createRedirectBatch
  deleteByIds

## CtpManagerTenantAppService（14）
  create
  updateByUseTenantId
  deleteByUseTenantId
  updateStatusByUseTenantId
  selectByUseTenantId
  selectByUseTenantCode
  retryInit
  selectStatusByUseTenantId
  selectInitStatus
  applicationList
  replenishInit
  activationLicence
  bindingTenant
  updateTenantAdmin

## ThirdPermissionAppService（1）
  checkPermissionByUser

## CtpUserBpmAppService（1）
  selectUserResourceIgnoreTenant

## CtpDeviceBindCommonAppService（3）
  bindDevice
  batchUnbindDevice
  selectByConditions

## CtpMenuCommonAppService（2）
  selectChildrenByCode
  selectListByConditions

## CtpResourceCommonAppService（2）
  selectDesignResources
  deleteDesignResources

## CtpSecretCommonAppService（12）
  selectSecretEnable
  selectSecretLevelEnumItem
  selectOrgSecretLevelEnumItem
  selectSecretLevelEnumItemByValue
  selectSecretLevelEnumItemByOrderNo
  selectOrgSecretLevelEnumItemByOrderNo
  selectSecretLevelOrderNoByValue
  selectSecretLevelValueByOrderNo
  selectListByConditions
  selectOrgToSystemSecretMap
  selectSystemToOrgSecretMap
  getAccessSecretEnumIds

## CtpUserCommonAppService（3）
  getUserInfo
  selectUserByLoginName
  getLoginPageSetParameter

## CtpUserDefaultIdentityCommonAppService（3）
  selectDefaultSwitchAdminOrg
  selectUDefaultseIdentityInfo
  selectFrontUserDefaultTenant

## CtpUserPermissionCommonAppService（15）
  selectUserResourceCode
  checkUserResourceCode
  selectUserResource
  selectUserResource
  checkUserResource
  checkUserAppPermission
  selectControlMenus
  selectUserMenus
  selectAdminMenus
  selectUserRoleCode
  selectUserRoleCodeByOrg
  selectUserRole
  selectUserDataPermission
  hasAdminRole
  selectAdminOrgIdList

## CtpUserRoleCommonAppService（5）
  selectUserByRoleCode
  selectPageUserByRoleCode
  selectUserByRoleCodeSearch
  selectUserIdByRoleCode
  hasRoleByOrgCode

## CtpAuthCoreAppService（12）
  authenticate
  switchAdmin
  switchOrg
  switchUser
  getLoginUserInfo
  selectTenantList
  switchTenant
  refreshAccessToken
  getAccessToken
  selectTenantListByUserId
  selectTicketByToken
  getTempAccessToken

## CtpDataAuditCoreAppService（1）
  create

## CtpLoginLogCoreAppService（1）
  selectPageByConditions

## CtpLoginPreConfigAppService（6）
  selectByOrgId
  createOrUpdate
  allowChildCustomDefine
  allowChildCustomDefine
  selectByUri
  hasRepeatName

## CtpResourceCoreAppService（8）
  register
  registerBatch
  registerResourcePermissionBatch
  updateByCode
  deleteByConditions
  selectByCode
  selectListByConditions
  selectPageByConditions

## CtpResourcePermissionCoreAppService（4）
  register
  deleteByResourceCode
  selectByResourceCode
  selectListByConditions

## CtpResourceTypeCoreAppService（1）
  selectListByConditions

## CtpRoleCoreAppService（8）
  create
  update
  selectById
  selectByCode
  selectByIds
  selectListByConditions
  selectPageByConditions
  deleteByConditions

## CtpRoleResourceCoreAppService（0）

## CtpThirdPlatformConfigCoreAppService（7）
  create
  update
  deleteByIds
  selectById
  selectOneByConditions
  selectListByConditions
  selectPageByConditions

## CtpUserBindMappingAppService（7）
  saveUpdate
  selectOneByCondition
  selectListByConditions
  pageUserMappingByUserIds
  listUserMappingByUserIds
  listUserMappingForPending
  selectPageByConditions

## CtpUserCoreAppService（15）
  beforeCreateCheck
  create
  createBatch
  beforeUpdateCheck
  update
  updateBatch
  selectById
  selectByIds
  selectSimpleByIds
  selectOneByCondition
  selectListByConditions
  selectPageByConditions
  selectUserIgnoreTenant
  syncCreateBatch
  syncUpdateBatch

## CtpUserResourceCoreAppService（4）
  createBatch
  deleteByConditions
  selectListByConditions
  selectPageListByConditions

## CtpUserRoleAppService（4）
  selectCascadeById
  selectCascadeByIds
  dynamicJoinSelect
  dynamicSelect

## CtpUserRoleCoreAppService（8）
  createBatch
  createUserRule
  createAuthorizationRule
  deleteAuthorizationRuleById
  deleteByIds
  deleteByConditions
  selectListByConditions
  selectPageByConditions

## CtpAuthorizationRuleOrgAppService（8）
  create
  update
  delete
  selectPageByConditions
  selectAuthorizationObject
  selectAuthorizationEntity
  selectAuthorizationFuncList
  selectDuplicateRolesRule

## CtpOrgAdminOrgAppService（7）
  configAdmin
  selectByOrgId
  selectByOrgIds
  selectByUserId
  selectPageByConditions
  selectListByConditions
  selectManageScopeByOrgAndUser

## CtpOrgSelectPeopleAppService（1）
  selectPageByConditions

## CtpOrgUpgradeAppService（1）
  updateBatchUserCode

## CtpPermissionApprovalOrgAppService（4）
  update
  selectById
  batchKnow
  selectPageByConditions

## CtpSecretApprovalOrgAppService（2）
  create
  selectPendingInfo

## SyncOrgRoleTempAppService（1）
  syncOrgRole

## CtpAuthorizationUdcAppService（2）
  autoAuthAppRoles
  selectAppFirstLinks

小计方法: 199

## 归属说明
- **BPM**：流程（Process）/ 节点（Node）/ 权限（Permission）/ 表单权限 / 模拟 / 传输 / 部署。
- **ORG**：组织架构（Unit/Post/Level/Member/Job）、机构、授权（Authorization）。
- **USER**：租户/应用（CtpApplication*）、认证（CtpAuth*）、授权规则、登录、个人计划、菜单。

## 待补
- 各方法入参/出参 DTO 字段（需从运行时 pod 的 `*-biz` 反编译）
- 前端功能 → 方法的映射（BPM 前端在设计器内，`bpmNodePermission*` 等）
