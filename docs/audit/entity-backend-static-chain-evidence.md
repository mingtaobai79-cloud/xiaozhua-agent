# Entity Construction Chain — backend static evidence

## Scope

This update follows the Entity Modeling frontend operation rather than starting from a guessed Java service. All statements below are static evidence from compiled frontend and targeted decompiled interfaces; no mutation or database write was executed.

## `udc-facade-5.3.517-EntityAppService.java`

- SHA-256: `fe11c35f36c122033662b1bcc650a5d11455c4b9c1e6cc8832b1c3e768182822`

```java
11:  *  com.seeyon.udc.common.dto.EntityDto
21: import com.seeyon.udc.common.dto.EntityDto;
25: public interface EntityAppService {
26:     public SingleResponse<Long> create(SingleRequest<EntityDto> var1);
28:     public SingleResponse<Integer> update(SingleRequest<EntityDto> var1);
30:     public SingleResponse<Integer> deleteById(SingleRequest<Long> var1);
32:     public SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>> var1);
34:     public SingleResponse<EntityDto> selectById(SingleRequest<Long> var1);
36:     public ListResponse<EntityDto> selectByIds(SingleRequest<List<Long>> var1);
38:     public SingleResponse<EntityDto> selectByName(SingleRequest<Long> var1, SingleRequest<String> var2);
40:     public PageResponse<EntityDto> selectPageByCondition(PageRequest var1);
42:     public ListResponse<EntityDto> selectListByConditions(SingleRequest<Map<String, Object>> var1, Sort var2);
44:     public ListResponse<EntityDto> selectListByTerm(SingleRequest<Long> var1, SingleRequest<String> var2, Sort var3);
46:     public SingleResponse<EntityDto> selectParentById(SingleRequest<Long> var1);
48:     public ListResponse<EntityDto> selectEntitiesByAppId4Tree(SingleRequest<Long> var1);
50:     public ListResponse<EntityDto> selectAggregationEntitiesByAppId4Tree(SingleRequest<Long> var1);
52:     public PageResponse<EntityDto> selectChildrenByCondition(PageRequest var1);
54:     public ListResponse<EntityDto> selectPrimaryEntityByAppId(SingleRequest<Long> var1);
56:     public SingleResponse<EntityDto> selectByPrimaryEntityId(SingleRequest<Long> var1);
58:     public SingleResponse<Long> selectRootId(SingleRequest<Long> var1);
60:     public ListResponse<EntityDto> selectEntityByIdsLoadAttribute(SingleRequest<List<Long>> var1);
```

## `udc-facade-5.3.517-ApplicationManagerAppService.java`

- SHA-256: `2abee3dd241c6308ab23268e410815de2993227122f90dd61339ed6916e9dad6`

```java
25:  *  com.seeyon.udc.common.dto.EntityDto
70: import com.seeyon.udc.common.dto.EntityDto;
97: public interface ApplicationManagerAppService {
98:     public SingleResponse<Long> create(SingleRequest<ApplicationDto> var1);
100:     public ListResponse<OnlyPageApplicationDto> createOnlyPageApplication(SingleRequest<CreateOnlyPageApplicationDto> var1);
102:     public SingleResponse<Void> createNewLayoutAfterCall(SingleRequest<NewLayoutCreateAfterCallDto> var1);
104:     public SingleResponse<OnlyPageApplicationDto> copyOnlyPageApp(SingleRequest<ApplicationCopyDto> var1);
106:     public SingleResponse<OnlyPageApplicationUpgradeResultDto> upgradeOnlyPageApplication(SingleRequest<OnlyPageApplicationUpgradeDto> var1);
108:     public SingleResponse<IntegrationApplicationDto> createIntegrationApplication(SingleRequest<IntegrationApplicationDto> var1);
110:     public SingleResponse<LayoutApplicationDto> createLayoutApplication(SingleRequest<LayoutApplicationDto> var1);
112:     public SingleResponse<LayoutApplicationDto> copyLayoutApp(SingleRequest<ApplicationCopyDto> var1);
114:     public SingleResponse<ApplicationDto> selectById(SingleRequest<Long> var1);
116:     public SingleResponse<Integer> update(SingleRequest<ApplicationDto> var1);
118:     public SingleResponse<Integer> updateWithMember(SingleRequest<ApplicationWithMemberDto> var1);
120:     public SingleResponse<Integer> updateAppCategoryBatch(SingleRequest<AppCategoryDto> var1);
122:     public SingleResponse<Integer> deleteById(SingleRequest<Long> var1);
124:     public SingleResponse<ApplicationDto> copyApp(SingleRequest<ApplicationCopyDto> var1);
126:     public SingleResponse<String> copyAppAsync(SingleRequest<ApplicationCopyDto> var1);
128:     public SingleResponse<Integer> createMember(SingleRequest<MemberAddDto> var1);
130:     public ListResponse<AppCollaborationDto> selectCollaborationRecordsByAppId(SingleRequest<Long> var1);
132:     public SingleResponse<Void> deleteMemberById(SingleRequest<Long> var1);
134:     default public SingleResponse<Integer> handoverApp(SingleRequest<AppHanoverDto> appHanoverDto) {
138:     public SingleResponse<ApplicationDto> createReturnDto(SingleRequest<ApplicationDto> var1);
140:     public SingleResponse<Integer> deleteFormAppByGuid(SingleRequest<Long> var1);
142:     public SingleResponse<Integer> deleteFormAppByName(SingleRequest<String> var1);
144:     public SingleResponse<DeployParamDto> deployNormal(SingleRequest<DeployNormalDto> var1);
146:     public SingleResponse<DeployResultDto> deployForm(SingleRequest<DeployFormDto> var1);
148:     public SingleResponse<ApplicationDto> selectLatestDesignAppByGuid(SingleRequest<Long> var1);
150:     public SingleResponse<ApplicationWithMemberDto> selectLatestDesignAppWithMemberByGuid(SingleRequest<Long> var1);
152:     public SingleResponse<Map<String, Long>> selectAppNameAndIdMapByAppNames(SingleRequest<List<String>> var1);
154:     public ListResponse<ApplicationDto> selectDesignAppByGuid(SingleRequest<Long> var1);
156:     public PageResponse<ApplicationDto> selectAppByUser(SingleRequest<ApplicationSearchDto> var1);
158:     public ListResponse<ApplicationDto> selectAppByUserAndGuid(SingleRequest<ApplicationSearchDto> var1);
160:     public SingleResponse<ApplicationDto> selectAppByUserAndId(SingleRequest<ApplicationSearchDto> var1);
162:     public ListResponse<ApplicationExportDto> exportAppInfos(SingleRequest<AppInfoExportDto> var1);
164:     public SingleResponse<AppVersionDto> selectAppDeployState(SingleRequest<QueryFormInfoDto> var1);
166:     default public SingleResponse<String> downloadApp(SingleRequest<Long> request) {
170:     default public SingleResponse<String> downloadAppAsync(SingleRequest<Long> request) {
174:     default public SingleResponse<String> downloadAppByHost(SingleRequest<Long> request) {
178:     default public SingleResponse<Long> importApp(SingleRequest<String> request) {
182:     default public SingleResponse<Long> importAppWithDto(SingleRequest<ApplicationImportDto> request) {
186:     default public SingleResponse<String> batchDownloadAppAsync(SingleRequest<List<Long>> request) {
190:     default public SingleResponse<String> batchTransferAppAsync(SingleRequest<List<String>> request, SingleRequest<Map<String, Object>> params) {
194:     default public ListResponse<ImportValidationInfo> importFormValidate(String storageKey, ApplicationCopyDto applicationCopyDto) {
198:     default public SingleResponse<String> importFormApp(String storageKey, ApplicationCopyDto applicationCopyDto) {
202:     default public SingleResponse<Long> transfer(SingleRequest<String> request) throws IOException {
206:     default public SingleResponse<Long> transfer(SingleRequest<String> request, SingleRequest<Map<String, Object>> params) throws IOException {
210:     default public SingleResponse<ShelfDependResponseDto> getShelfDepend(SingleRequest<ShelfDependRequestDto> request) {
214:     default public ListResponse<DependentApplicationDto> getDependsByAppId(SingleRequest<Long> request) {
218:     default public ListResponse<DependentApplicationDto> getDependsLayoutAppInfo(SingleRequest<BaseApplicationSearchDto> request) {
222:     default public SingleResponse<ShelfCompatibilityLockResultDto> shelfCompatibilityLock(SingleRequest<ShelfCompatibilityLockRequestDto> request) {
226:     default public SingleResponse<Long> migrationApp(SingleRequest<DeployFerryDto> request) {
230:     default public ListResponse<DeployRecordDto> selectDeployRecordById(SingleRequest<Long> request) {
234:     public PageResponse<ApplicationDto> selectAppPageByConditions(PageRequest var1);
236:     default public SingleResponse<Long> createEntity(SingleRequest<EntityDto> request) {
240:     default public ListResponse<AttributeGroupDto> operateBatch(SingleRequest<List<AttributeGroupDto>> attributeGroupDtoList) {
```

## `udc-starter-runtime-5.3.517-EntityAppServiceInvokeService.java`

- SHA-256: `43b1b669da3e35757ead389f962f93fd2ca9fb4713b128f153f5b85ecb4bff31`

```java
10:  *  com.seeyon.ctp.metadata.api.MetadataQueryAppService
30: import com.seeyon.ctp.metadata.api.MetadataQueryAppService;
44: public class EntityAppServiceInvokeService {
45:     private static final Logger log = LoggerFactory.getLogger(EntityAppServiceInvokeService.class);
47:     private MetadataQueryAppService metadataQueryAppService;
54:         SingleResponse response = this.metadataQueryAppService.selectAppServiceMetadataByFullName(SingleRequest.from((Object)fullNameDto));
62:     public SingleResponse invokeMethod(AppServiceMetadataDto appServiceMetadata, String methodName, String data, String appName) {
65:             String interfaceClass = methodMetadata.getInterfaceClass();
81:     public PageResponse invokePageMethod(AppServiceMetadataDto appServiceMetadata, String methodName, String data, String appName) {
84:             String interfaceClass = methodMetadata.getInterfaceClass();
```

## `udc-starter-runtime-5.3.517-EntityRuntimeService.java`

- SHA-256: `4cb0e688038b4e954d05c084cbbea2c371e7592f18298ae0575a64aebecf6025`

```java
89: public class EntityRuntimeService
91:     private static final Logger log = LoggerFactory.getLogger(EntityRuntimeService.class);
92:     private static final String CUSTOM_DATA_TYPE = "customDataType";
93:     private static final String GET = "get";
94:     private static final String FORM_PERMISSION_ID = "formPermissionId";
95:     private static final String FORM_PERMISSION_DATA = "formPermissionData";
96:     private static final String FORM_BPM_INFO = "bpmInfo";
98:     private UdcSerialConfigService serialConfigService;
100:     private FormPermissionAuthService formPermissionAuthService;
158:     private <T extends BaseEntityActionDto> BpmFromPermissionCheckDto<T> getBpmFromPermissionCheckDto(EntityMeta entityMeta, T oldData, T newData, Map<String, Object> extraParamMap) {
198:     private void setSerialValue(BaseDto dto, Class<? extends BaseEntity> entityClass, List<Field> serialFields) {
256:     private BpmFormPermissionIncludeContentDto mapToBpmFormPermissionIncludeContentDto(Map<String, Object> dataMap) {
322:     private BpmFormPermissionContentDto mapToBpmFormPermissionContentDto(Map<String, Object> map) {
```

## `udc-facade-5.3.517-DesignMetadataQueryAppService.java`

- SHA-256: `f16383d85c5e87eab9c6f8809e10f1d3cd4340d56f379d38afe4257a82b0d8aa`

```java
50: public interface DesignMetadataQueryAppService {
51:     public SingleResponse<ServiceMetadataDto> selectServiceMetadata(SingleRequest<SearchDesignMetadataDto> var1);
53:     public ListResponse<EntityMetadataDto> selectEntityMetadata(SingleRequest<SearchDesignMetadataDto> var1);
55:     public ListResponse<EntityMetadataDto> selectEntityMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
57:     public SingleResponse<EntityMetadataDto> selectEntityMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
59:     public ListResponse<EntityMetadataDto> selectEntityMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
61:     public ListResponse<AggMetadataDto> selectAggMetadata(SingleRequest<SearchDesignMetadataDto> var1);
63:     public ListResponse<AggMetadataDto> selectAggMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
65:     public SingleResponse<AggMetadataDto> selectAggMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
67:     public ListResponse<AggMetadataDto> selectAggMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
69:     public ListResponse<EntityMetadataDto> selectEntityListByAgg(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
71:     public ListResponse<RestApiMetadataDto> selectRestApiMetadata(SingleRequest<SearchDesignMetadataDto> var1);
73:     public ListResponse<RestApiMetadataDto> selectRestApiMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
75:     public ListResponse<RestApiMetadataDto> selectRestApiMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
77:     public SingleResponse<RestApiMetadataDto> selectRestApiMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
79:     public ListResponse<DtoMetadataDto> selectDtoMetadata(SingleRequest<SearchDesignMetadataDto> var1);
81:     public ListResponse<DtoMetadataDto> selectDtoMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
83:     public ListResponse<DtoMetadataDto> selectDtoMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
85:     public SingleResponse<DtoMetadataDto> selectDtoMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
87:     public ListResponse<EnumMetadataDto> selectEnumMetadata(SingleRequest<SearchDesignMetadataDto> var1);
89:     public ListResponse<EnumMetadataDto> selectEnumMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
91:     public SingleResponse<EnumMetadataDto> selectEnumMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
93:     public ListResponse<AggEntityMetadataDto> selectAggEntityMetadata(SingleRequest<SearchDesignMetadataDto> var1);
95:     public ListResponse<AggEntityMetadataDto> selectAggEntityMetadataByCondition(SingleRequest<UdcAppMetaDataQueryDto> var1);
97:     public ListResponse<AggEntityMetadataDto> selectAggEntityMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
99:     public SingleResponse<AggEntityMetadataDto> selectAggEntityMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
101:     public ListResponse<AggEntityMetadataDto> selectAggEntityMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
103:     public ListResponse<OpenApiMetadataDto> selectOpenApiMetadata(SingleRequest<SearchDesignMetadataDto> var1);
105:     public ListResponse<OpenApiMetadataDto> selectOpenApiMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
107:     public SingleResponse<OpenApiMetadataDto> selectOpenApiMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
109:     public ListResponse<AppServiceMetadataDto> selectAppServiceMetadata(SingleRequest<String> var1);
111:     public ListResponse<AppServiceMetadataDto> selectAppServiceMetadataExcludeBoot(SingleRequest<String> var1);
113:     public ListResponse<AppServiceMetadataDto> selectAppServiceMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
115:     public SingleResponse<AppServiceMetadataDto> selectAppServiceMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
117:     public ListResponse<MqMetadataDto> selectMqMetadata(SingleRequest<SearchDesignMetadataDto> var1);
119:     public ListResponse<MqMetadataDto> selectMqMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
121:     public ListResponse<MqMetadataDto> selectMqMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
123:     public SingleResponse<MqMetadataDto> selectMqMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
125:     public ListResponse<DtoMetadataDto> selectEntityRelationDtoMetadata(SingleRequest<String> var1);
127:     public ListResponse<DtoMetadataDto> selectEntityRelationDtoMetadataExcludeBoot(SingleRequest<SearchDesignMetadataDto> var1);
129:     public ListResponse<DtoMetadataDto> selectDtoMetadataByEntityFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
131:     public SingleResponse<DtoMetadataDto> selectDtoMetadataByEntityFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
133:     public SingleResponse<AppServiceMetadataDto> selectAppServiceMetadataByDto(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
135:     public ListResponse<ReferMetadataDto> selectReferMetadataByEntity(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
137:     public SingleResponse<ReferAndAppMetadataDto> selectReferAndAppMetadataByEntity(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
139:     public ListResponse<EntityMetadataDto> selectBasicDataEntityMetadata(SingleRequest<SearchDesignMetadataDto> var1);
141:     public SingleResponse<EntityMetadataDto> selectBasicDataEntityMetadataByFullName(SingleRequest<SearchDesignMetadataByFullNameDto> var1);
143:     public ListResponse<EntityMetadataDto> selectBasicDataEntityMetadataByFullNames(SingleRequest<SearchDesignMetadataByFullNamesDto> var1);
145:     public ListResponse<PageMetadataDto> selectPageMetadataList(SingleRequest<SearchDesignMetadataDto> var1);
147:     public ListResponse<EnumMetadataDto> selectEnumMetadataList(SingleRequest<List<Long>> var1);
```

## Closed static chain so far

```text
Entity Modeling frontend
  → module 64527 export createEntity(payload)
  → udcMutationLoader.load
  → fieldType: udcEntityPost
  → paramsType: udcEntityPostInputBody
  → paramsKey: body
  → params: {...payload, appId: currentAppId}
  → queryFields: content
  → return content

Entity update uses udcEntityUpdatePost / udcEntityUpdatePostInputBody.
Entity list uses udcEntitySelectAllByAppidAppGet / udcEntitySelectAllByAppidAppGetInputPath / path:{appId}.
Entity detail uses udcEntityGet / udcEntityGetInputPath / path:{id}; response includes tableName and nested attributes.

Backend facade contract:
  EntityAppService.create(SingleRequest<EntityDto>) → SingleResponse<Long>
  EntityAppService.update(SingleRequest<EntityDto>) → SingleResponse<Integer>
  EntityAppService.selectById(SingleRequest<Long>) → SingleResponse<EntityDto>
  EntityAppService.selectEntityByIdsLoadAttribute(...) → ListResponse<EntityDto>

Additional facade surface:
  ApplicationManagerAppService.createEntity(SingleRequest<EntityDto>) → default SingleResponse<Long>
  ApplicationManagerAppService.operateBatch(SingleRequest<List<AttributeGroupDto>>) → default ListResponse<AttributeGroupDto>

Runtime-side static consumer:
  EntityAppServiceInvokeService queries MetadataQueryAppService for AppServiceMetadataDto, resolves method metadata/interfaceClass/parameter item type, deserializes JSON into the parameter DTO, then reflectively invokes the target bean method.
```

## Evidence status

| Segment | Status |
|---|---|
| Frontend Entity CRUD operation mapping | STATIC_RULE |
| Facade method signatures and DTO boundary | VERIFIED_STATIC_BYTECODE |
| Resolver/controller route | UNVERIFIED |
| Concrete service implementation | UNVERIFIED |
| Metadata/DB write | UNVERIFIED |
| Code generation/generated source | UNVERIFIED |
| Runtime consumer for generated Entity CRUD | STATIC_RUNTIME_SUPPORT, not linked to this specific UDC entity |

## Important correction

`ApplicationManagerAppService.createEntity` is only a default interface method returning `SingleResponse.ok()` in the targeted facade artifact. It must not be reported as the concrete persistence implementation. The concrete Entity CRUD contract is the separate `EntityAppService` interface, while its implementation is not present in the current targeted decompile set.