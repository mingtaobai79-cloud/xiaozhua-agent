# UDC extmetadata Entity read-chain evidence

## Source artifact

- JAR: `<MAVEN_REPO>/com/seeyon/boot-starter-extmetadata/5.3.318/boot-starter-extmetadata-5.3.318.jar`
- JAR SHA-256: `14e1c96ed59827b3672cd809a3d08139578de9f727efb19cc03ba118a1cbee11`
- Extracted bytecode evidence: `docs/audit/artifacts/extmetadata-5.3.318/`

## Verified static call chain

```text
UdcMetaDataController
  ↓
UdcMetaDataAppV2Service
  ↓
UdcEntityMetaDataService
  ↓
MetadataQueryAppService
  ↓
EntityMetadataDto / AggEntityMetadataDto
  ↓
MetadataConvertUtil.entityMetaDataDto2UdcExcludeAttribute
   or MetadataConvertUtil.attributeMetaData2Udc
  ↓
UdcEntityMetaDataDto / UdcAttributeMetaDataDto
```

The bytecode references establish these concrete edges:

- `UdcMetaDataController.selectEntity(...)` delegates to `UdcMetaDataAppV2Service.selectEntity(...)`.
- `UdcMetaDataAppV2Service.selectEntity(...)` delegates to `UdcEntityMetaDataService.selectEntity(...)`.
- `UdcMetaDataController.selectEntityByAppName(...)` delegates through the same app-service layer to `UdcEntityMetaDataService.selectEntityByAppName(...)`.
- `UdcEntityMetaDataService` injects `com.seeyon.ctp.metadata.api.MetadataQueryAppService`.
- Entity reads call `MetadataQueryAppService.selectEntityMetadataList(...)` / `selectEntityMetadataListExcludeBoot(...)` and aggregation reads call the corresponding aggregation methods.
- Entity metadata is converted into UDC DTOs by `MetadataConvertUtil`.
- Attribute conversion explicitly consumes `EntityAttributeMetadataDto` and produces `UdcAttributeMetaDataDto`.
- The resulting UDC entity DTO contains attributes and the entity/table metadata used by `UdcAppInfoController`.

## Controller route evidence

The targeted bytecode contains these REST operation names:

```text
select-all-entity-by-app-name/{appName}
select-aggregation-entity/list/{appName}
select-entity
select-aggregation-entity
select-refer-by-entity
```

These are REST routes in the extmetadata component, not the GraphQL `udcEntityGet` field itself. They prove the UDC-facing metadata read facade and its backend service path, but do not yet prove the GraphQL resolver maps `udcEntityGet` to this exact controller/service method.

## Important boundary

This is a strong static read-chain result, not a complete write-chain result:

- It proves UDC extmetadata read composition over the generic MetadataQueryAppService.
- It does not prove `udcEntityPost` / `udcEntityUpdatePost` invokes `UdcEntityMetaDataService` or `MetadataModifyAppService`.
- It does not identify the concrete implementation of `EntityAppService.create(EntityDto)`.
- It does not prove the physical metadata table, object-storage key, or database write for Entity creation.
- It does not prove generated Java source or a runtime consumer for a newly created entity.
- Artifact version is `5.3.318`; the UDC facade evidence currently targets `5.3.517`. Version alignment remains required before using this as same-version proof.

## Status

`VERIFIED_STATIC_BYTECODE` for the UDC extmetadata Entity read composition.
`UNVERIFIED` for GraphQL-to-controller mapping, Entity write implementation, persistence, generation, and runtime linkage.
