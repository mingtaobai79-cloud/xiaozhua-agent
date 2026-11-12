# Entity Metadata write contract evidence

## Artifact

- `<MAVEN_REPO>/com/seeyon/boot-starter-metadata/5.3.358/boot-starter-metadata-5.3.358.jar`
- SHA-256: `926c28022df0502bfd988df0cf31417fb70e0603af3d39df98015e65a7028431`
- Evidence directory: `docs/audit/artifacts/metadata-5.3.358/`

## Verified static write contract

```text
MetadataCreateAppService.createAllEntityMetadata(
    SingleRequest<ServiceEntityMetadataDto>
)
    ↓
ServiceEntityMetadataDto
    ├── appName
    ├── appVersion
    └── metadatas: Map
    ↓
MetadataService.createMetadata(
    MetadataTypeEnum.Entity,
    appName,
    appVersion,
    metadatas,
    booleanFlag
)
```

The same facade exposes a separate AppService metadata write operation:

```text
createAllAppServiceMetadata(SingleRequest<ServiceAppServiceMetadataDto>)
    ↓
MetadataService.createMetadata(
    MetadataTypeEnum.AppService,
    appName,
    appVersion,
    metadatas,
    booleanFlag
)
```

Attribute modification is a separate contract:

```text
MetadataModifyAppService.modifyEntityAttribute(
    SingleRequest<EntityAttributeModifyDto>
)
    ↓
MetadataService.modifyEntityAttribute(EntityAttributeModifyDto)
```

Batch replacement is also separate:

```text
coverAllModifyEntityAttribute(
    SingleRequest<List<EntityAttributeModifyDto>>
)
    ↓
MetadataService.coverAllModifyEntityAttribute(List<...>)
```

## What this proves

- Entity metadata and AppService metadata are distinct `MetadataTypeEnum` values and are written through the same generic `createMetadata` primitive.
- The write payload is application/version scoped and carries a metadata map.
- Entity attribute updates do not use the Entity creation method directly; they have dedicated modify/cover-all contracts.
- The generic metadata service is the verified write boundary for metadata.

## What remains unproven

- No evidence yet connects frontend GraphQL `udcEntityPost` to `createAllEntityMetadata`.
- No evidence yet connects `EntityAppService.create(EntityDto)` to this MetadataCreateAppService.
- The physical persistence implementation inside `MetadataService.createMetadata` still needs a focused read of its bytecode.
- Code generation and generated-source publication remain unverified.
- Artifact is `5.3.358`, while the UDC facade/runtime target is `5.3.517`; same-version linkage is not claimed.

## Status

`VERIFIED_STATIC_BYTECODE` for the generic Entity Metadata write contract.
`UNVERIFIED` for frontend-to-write mapping, physical storage, generation, and same-version integration.
