# P0-3A Runtime CRUD Boundary — Audit Conclusion

## Decision

```text
P0-3A = CLOSED
```

This closure is deliberately narrow: `BaseEntityCurdService` has been defined as the runtime CRUD semantic boundary. It is not treated as a design-time construction or generator implementation.

## Verified runtime chain

```text
Generated AppServiceImpl
  ↓
Generated DomainService
  ↓
BaseEntityCurdService.createWithResult(dto)
  ↓
create(dto)
  ↓
preprocessing / validation / lifecycle callbacks
  ↓
recursive child handling
  ↓
BeanCopier.copy(dto, entityClass)
  ↓
EntityBeanContainer.findDao(entityClass)
  ↓
EntityClassContext.withEntityClass(..., BaseDao.create(entity))
  ↓
afterCreate / EntityEventHelper events
  ↓
return result
```

Batch variant:

```text
createBatch(dtoList)
  ↓
preCreateBatch / beforeCreate
  ↓
recursive child handling
  ↓
BeanCopier.copyList(dtoList, entityClass)
  ↓
EntityBeanContainer.findDao(entityClass)
  ↓
BaseDao.createBatch(entityList)
  ↓
afterCreate / runtime events
```

`createWithResult` is a wrapper:

```text
createWithResult(dto)
  → create(dto)
  → setActionType(NORMAL)
  → recursive DTO normalization
  → return dto
```

## Evidence status

- DAO invocation: `OBSERVED`, `VERIFIED_STATIC_BYTECODE`.
- DTO → Entity conversion: `OBSERVED`, `VERIFIED_STATIC_BYTECODE`.
- Child traversal: `OBSERVED`, `VERIFIED_STATIC_BYTECODE`.
- Runtime lifecycle/event callbacks: `OBSERVED`, `VERIFIED_STATIC_BYTECODE`.
- Direct MetadataCreate/MetadataService call in inspected create path: not observed.
- Direct Generator call in inspected create path: not observed.
- Normal create transaction boundary: `UNVERIFIED` at this class level.
- Physical DB table/SQL mapping: outside this boundary, not pursued.

## Stop rule applied

Runtime investigation stops here. It may be reopened only if P0-3B discovers a concrete bridge from design-time Entity construction into this runtime class or its event helper. Otherwise, the next主线 is exclusively:

```text
udcEntityPost
  → GraphQL
  → Resolver / Handler
  → EntityAppService.create
  → EntityDto
  → Entity Definition / Metadata
  → Generator Bridge
```

## Raw evidence

```text
<SEEYON_AGENT_ROOT>/docs/audit/artifacts/runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt
```

Artifact:

```text
<MAVEN_REPO>/com/seeyon/udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar
```
