# Entity Metadata storage evidence

## Artifact

- `<MAVEN_REPO>/com/seeyon/boot-starter-metadata/5.3.358/boot-starter-metadata-5.3.358.jar`
- SHA-256: `926c28022df0502bfd988df0cf31417fb70e0603af3d39df98015e65a7028431`
- Bytecode: `docs/audit/artifacts/metadata-5.3.358/MetadataService.javap.txt`

## Verified static chain

```text
MetadataCreateAppService.createAllEntityMetadata
    ↓
MetadataService.createMetadata(Entity, appName, appVersion, metadatas, flags)
    ↓
MetadataRedisKeyUtils.metadataRedisKey(Entity, appName)
MetadataRedisKeyUtils.md5Rediskey(Entity, appName)
    ↓
RedisTemplate value/hash operations
    ↓
MetadataMD5Utils.dataMd5(metadatas)
    ↓
MetadataService.onChange(...)
    ↓
MetadataService.createMultiVersionMetadata(Entity, appName, appVersion, metadatas, md5)
    ↓
syncSave2Storage(storageKey, map)
```

The bytecode also shows the tenant branch using tenant-specific metadata and MD5 keys, with storage synchronization and Redis hash/value updates. The exact storage-key string construction is delegated to `MetadataRedisKeyUtils`; this evidence does not invent its output.

## Attribute modification storage

```text
MetadataService.modifyEntityAttribute(EntityAttributeModifyDto)
    ↓
MetadataRedisKeyUtils.entityAttributeModifyRedisKey(appName)
MetadataRedisKeyUtils.entityAttributeModifyHashKey(dto)
    ↓
selectModifiedEntityAttributes(appName)
    ↓
syncSave2Storage(...)
    ↓
Redis hash putAll / expire
```

The batch `coverAllModifyEntityAttribute(List<...>)` follows the same persisted modification-map pattern and deletes the modification Redis key after storage synchronization.

## Boundary

This proves the generic Metadata service writes Entity metadata to a storage abstraction and maintains Redis cache/MD5/version/change state. It does not yet prove whether the configured `FileService` storage is a local file system, object storage, or another provider in the target deployment. It also does not connect the frontend `udcEntityPost` or `EntityAppService.create(EntityDto)` to this metadata write method. Artifact version is `5.3.358`; same-version linkage to the 5.3.517 UDC runtime is not claimed.

## Status

`VERIFIED_STATIC_BYTECODE` for MetadataService Entity storage behavior.
`UNVERIFIED` for design-time Entity create caller, physical provider, code generation, and end-to-end live mutation.
