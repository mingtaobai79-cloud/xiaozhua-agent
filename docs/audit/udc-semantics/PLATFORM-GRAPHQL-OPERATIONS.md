# UDC 平台 GraphQL 操作面全景（反编译 udc-biz 5.3.517）

**证据源**：`<MAVEN_REPO>/com/seeyon/udc-biz/5.3.517/udc-biz-5.3.517.jar`
反编译 `com.seeyon.udc.api.*` 共 **29 个 AppService / 240+ 方法**。
运行时版本确认：udc-*-5.3.517（pod `udc-7cbfc587f5-*` / `datamigration*`，ns `lowcode-test`）。

每个方法 = 一个网关可路由的 GraphQL 操作（经 `POST /service/udc/graphql?<op>Post` 或 REST `GET /service/udc/...`）。
**这是"页面每个交互 → 请求 → 后端处理"的平台能力全集**，也是生成器可依附的操作面。

> 说明：udc-biz 的 api 包只覆盖 metadata / entity / dto / enum / refer / event / sandbox / stereotype 等
> **元数据与设计态能力**；微流程的 graphql 操作在 `com.seeyon.udc.microflow`（已另有文档）。二者合起来才是完整操作面。

## 服务清单（按方法数）


### AttributeGroupAppService（7 方法）
  create
  update
  cancel
  remove
  swap
  operateBatch
  selectListByEntityId

### AttributeSetAppService（13 方法）
  create
  createBatch
  deleteById
  deleteByIds
  update
  selectById
  selectByIds
  selectByName
  selectListByConditions
  selectListByAppId
  selectListByNames
  selectListByNamesWithAttributes
  selectListByTerm

### DataTransferObjectAppService（22 方法）
  create
  createDtoWithAttrs
  update
  updateDtoWithAttrs
  deleteById
  selectById
  selectDtoWithAttrsById
  selectPageByConditions
  selectListByConditions
  createDtoWithAttrsAndRefDtos
  createDtoWithAttrs4EntityEvent
  updateDtoWithAttrs4EntityEvent
  updateDtoWithAttrsAndRefDtos
  selectDtoWithAttrsAndRefDtos
  selectListBySourceId
  selectMicroFlowCustomDtoByAppId
  selectAllByMicroFlowId
  deleteDtoWithAttrsAndRefDtos
  checkExists
  searchSelectableDtoList
  searchPageMicroFlowDtos
  check

### DataTypeAppService（7 方法）
  getAll
  selectBaseDataTypes
  selectParameterDataTypes
  selectDataTypeByName
  selectDataTypeByAppId
  selectDataTypeByParams
  selectScalabilityDataType

### DtoAttributeAppService（8 方法）
  create
  createBatch
  update
  deleteById
  deleteByIds
  selectById
  selectPageByConditions
  selectListByConditions

### EntityGroupAppService（7 方法）
  create
  update
  updateBatch
  deleteById
  deleteByIds
  selectById
  selectByAppId

### EntityOpenApiAppService（1 方法）
  selectOpenApiData

### EntityPresetAppService（6 方法）
  selectPresetByEntityId
  uploadInItData
  create
  update
  createDefaultExcelTemplate
  selectListByAppId

### EventAppService（9 方法）
  create
  selectPageByConditions
  selectListByConditions
  selectById
  deleteById
  deleteByIds
  update
  selectBusinessEvent
  selectEvents

### EventWithDataAppService（5 方法）
  createWithEventData
  updateWithEventData
  selectWithEventData
  selectListWithDataByConditions
  selectListWithDataByTerm

### FeatureAppService（3 方法）
  list
  listSystemAttributeNames
  upgrade

### IndexAppService（7 方法）
  create
  deleteById
  deleteByIds
  update
  selectById
  selectByEntityId
  selectMatchesAttributeByEntityId

### InnerEntityAppService（4 方法）
  selectEntitiesByEntityId4Tree
  copyEntity
  attributeTransfer
  selectMasterEntityCount

### MicroFlowUpgradeAppService（6 方法）
  upgradeThirdEntity
  upgradeThirdServiceByNames
  batchUpgradeThirdEntity
  upgradeExtendFullNameByAppId
  upgradeCallExtendAppService
  upgradeEntityEventFullName

### ParameterAppService（7 方法）
  create
  update
  deleteById
  deleteByIds
  selectById
  selectByIds
  selectPageByCondition

### PreSetAttributeCapacityAppService（2 方法）
  getAllPreSetAttributeCapacity
  getPreSetAttributeCapacity

### PublishStateAppService（1 方法）
  updateState

### ReferConfigAppService（8 方法）
  create
  createOrUpdate
  update
  deleteById
  selectById
  selectPageByCondition
  selectListByCondition
  convertToMobile

### ReferConfigGroupAppService（4 方法）
  createConfigInfo
  updateConfigInfo
  deleteById
  selectListByConditions

### ScalabilityAppService（6 方法）
  create
  update
  deleteById
  deleteByIds
  selectById
  selectByOptionId

### ScalabilityOptionAppService（7 方法）
  create
  update
  deleteById
  selectById
  selectByAppId
  selectByAppIdWithDetail
  selectAllOptionName

### StereotypeAllAppService（2 方法）
  getAll
  get

### StereotypeAppService（2 方法）
  list
  upgrade

### UdcDataBaseSqlGenerator（3 方法）
  getChangeList
  getDropChangeList
  filterSet

### UdcEnumAppService（8 方法）
  create
  selectPageByConditions
  selectListByConditions
  selectById
  deleteById
  deleteByIds
  update
  selectListByTerm

### UdcEnumCategoryAppService（8 方法）
  create
  selectPageByConditions
  selectListByConditions
  selectById
  deleteById
  deleteByIds
  update
  selectCategoryAndEnum

### UdcEnumItemAppService（11 方法）
  create
  selectPageByConditions
  selectListByConditions
  selectById
  selectByEnumId
  deleteById
  deleteByIds
  update
  operateBatch
  selectListByTerm
  importExcel

### UdcMetaDataAppService（33 方法）
  selectAppMetaData4PageCode
  selectAvailableUpgradeAppMetadataById
  selectPageAvailableAppMetaDataByCondition
  selectPageAvailableAppMultiVersionMetaDataByCondition
  selectReferMetaDataByEntity
  mergeReferMetaData
  selectCustomReferMetaDataByPageId
  selectReferAndAppMetadataByEntity
  selectEntityMetaData
  selectAggEntityIncludeAssociationByEntityId
  selectAggEntityIncludeAssociation
  selectAggEntity
  selectEntitiesMetaDataByAppId
  selectSimpleAggEntityMetaDataByAppName
  selectEnumMetaDataByAppId
  selectAppMetaListData
  selectCtpEnumMetaDataListData
  selectParentEnumByCode
  selectCtpEnumMetaDataListData1
  selectCtpEnumAndApplicationMetaDataList
  selectCtpEnumItemList
  selectPageMetaData
  selectPageInfoMetaData
  selectPageMetaDataByMasterApp
  selectAllLayoutMetaDataByAppIncludeHost
  selectPageLayoutInfoMetaData
  selectPageLayoutMetaData
  selectAllPageLayoutMetaDataByApp
  selectPageSchema4Bpm
  selectJavaEnumMetaDataList
  selectJavaEnumItemMetaDataList
  selectEntitiesByEntityId4Tree
  selectFunctionNodeWithPageInfoDtoTreeByApp

### UdcSandBoxAppService（6 方法）
  search
  searchDetails
  searchDetails4FlowLog
  searchPageLog
  searchPageLogNonMetadata
  dataTransfer

## 关键观察
- **UdcMetaDataAppService（33）** = 元数据读取核心：entity metadata、page metadata、enum、refer、app metadata、
  java enum、layout、page schema 供 BPM 使用。
- **DataTransferObjectAppService（22）** = DTO / 实体结构 CRUD（实体设计态）。
- **AttributeSetAppService（13）/ DtoAttributeAppService（8）** = 实体属性 / DTO 属性。
- **UdcEnum*（27 合计）** = 枚举分类 / 枚举 / 枚举项三级。
- **EventAppService（9）/ EventWithDataAppService（5）** = 事件与事件数据（对应微流程事件监听的候选源）。
- **ScalabilityAppService（6）/ ScalabilityOptionAppService（7）** = 扩展点 / 扩展选项（SPI 相关）。
- **EntityOpenApiAppService（1）/ PublishStateAppService（1）** = 开放 API / 发布态。
- **UdcDataBaseSqlGenerator（3）** = 元数据 → DDL 生成（设计态发布建表）。
- **MicroFlowUpgradeAppService（6）** = 微流程版本升级。

## 待补
- 各方法入参 DTO 字段约束（SingleRequest/PageRequest/具体 Search DTO）
- 微流程 graphql 操作的全量清单（另档 MICROFLOW-*.md）
- 前端 bundle 里每个设计器按钮 → 上述操作的映射（chunk → op）
