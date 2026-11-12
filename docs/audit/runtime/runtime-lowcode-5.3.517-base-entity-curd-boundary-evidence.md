# BaseEntityCurdService Runtime CRUD Boundary Evidence

## Scope

Artifact:

```text
<MAVEN_REPO>/com/seeyon/udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar
```

Class:

```text
com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService
```

Evidence source:

```text
javap -p -c -s
```

Raw evidence:

```text
<XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt
```

SHA-256 of runtime JAR:

```text
51d1a5e048623f5c26e41d8b5cd605c0adb3321ca4d0919b4ff598c12983cf16
```

## Boundary conclusion

`BaseEntityCurdService` is a runtime CRUD semantic boundary. The inspected create path performs runtime validation, lifecycle callbacks, entity conversion, DAO persistence, and runtime entity events. The inspected bytecode contains no call to `MetadataCreateAppService`, `MetadataService`, or a code-generator class in the create/createBatch path.

Absence here is a scoped observation of this class's inspected bytecode; it is not proof that no other listener or outer layer can connect runtime CRUD to metadata or generation.

## createWithResult

Observed bytecode:

```text
createWithResult(D dto)
  → create(dto)
  → setActionType(NORMAL)
  → DtoConvertUtil.forEach(entityMeta, dto, callback)
  → return dto
```

It is a result-returning wrapper around runtime `create`; it does not itself invoke metadata creation or a generator.

## create(D) exact order

Observed order for the single-record path:

```text
1. printTransactionInfo()
2. assert master entity
3. handlerCaseId(dto)
4. DtoConvertUtil.resetInsertHandle(entityMeta, dto, callback)
5. wrap dto as one-element list
6. DtoConvertUtil.forEach(entityMeta, list, callback)
7. permissionCallBack.buildInitialValue(...)        [conditional]
8. preCreateBatch(list)
9. permissionCallBack.requiredValidate(...)          [conditional]
10. beforeCreate(list)
11. EntityEventHelper.beforeEvent(eventContainer)    [master entity]
12. afterBeforeEventCheck(list)
13. EntityExceptionThrower.throwing(list)
14. OperateContext.enter()
15. SecretCallBack.checkSecret(list)                 [conditional]
16. recursiveCheck(entityMeta, list, null)
17. recursiveCreate(entityMeta, list)                [child entity handling]
18. middleCreate(list)
19. BeanCopier.copy(dto, entityClass)                [DTO → Entity]
20. getMapper()                                      [EntityBeanContainer.findDao(entityClass)]
21. EntityClassContext.withEntityClass(dao, entityClass, dao.create(entity))
22. afterCreate(list)
23. EntityEventHelper.afterEvent(eventContainer)
24. OperateContext.leave()
25. resetNormal(list)
26. EntityEventHelper.transactionSuccessEvent(eventContainer)
27. return DAO result count
```

The single-record DAO call is directly evidenced by the synthetic lambda:

```text
BaseDao.create(BaseEntity)
```

## createBatch(List<D>)

Observed order:

```text
1. empty list → return 0
2. assert master entity
3. reset insert handling for each DTO
4. preCreateBatch(list)
5. beforeCreate(list)
6. EntityEventHelper.beforeEvent(INSERT event)
7. afterBeforeEventCheck(list)
8. EntityExceptionThrower.throwing(list)
9. OperateContext.enter()
10. SecretCallBack.checkSecret(list)                [conditional]
11. recursiveCheck(entityMeta, list, null)
12. recursiveCreate(entityMeta, list)
13. middleCreate(list)
14. BeanCopier.copyList(list, entityClass)           [DTO list → Entity list]
15. getMapper() → EntityBeanContainer.findDao(entityClass)
16. EntityClassContext.withEntityClass(..., dao.createBatch(entityList))
17. afterCreate(list)
18. EntityEventHelper.afterEvent(eventContainer)
19. OperateContext.leave()
20. resetNormal(list)
21. EntityEventHelper.transactionSuccessEvent(eventContainer)
22. return DAO result count
```

The batch DAO call is directly evidenced by the synthetic lambda:

```text
BaseDao.createBatch(List)
```

## DAO resolution

`getMapper()` is directly implemented as:

```text
entityBeanContainer.findDao(entityClass)
```

The DAO is therefore resolved from the runtime `EntityBeanContainer` using the runtime-resolved Entity class. The generated application-specific DAO is supplied through this container; this report does not infer its registration mechanism.

## Entity metadata usage inside runtime CRUD

The create path directly consumes runtime `EntityMeta` for:

```text
resetInsertHandle
forEach
recursiveCheck
recursiveCreate
OperateContext
entityClass
```

This is runtime entity metadata required to execute CRUD. It is not evidence that the path creates or modifies design-time metadata through `MetadataCreateAppService`/`MetadataService`.

## Transactions

The class declares an injected:

```text
org.springframework.transaction.PlatformTransactionManager transactionManager
```

The inspected create/createBatch bytecode does not show a direct `PlatformTransactionManager.getTransaction()` call. Explicit transaction-manager usage was observed in `doParallelSelectCascadeById`, not in the normal create path. Therefore:

```text
create transaction boundary: UNVERIFIED at this class level
```

The runtime may obtain transaction semantics from an outer proxy, DAO, interceptor, or caller; no claim is made without evidence.

## Runtime events and cache/metadata boundary

The create path directly invokes:

```text
EntityEventHelper.beforeEvent
EntityEventHelper.afterEvent
EntityEventHelper.transactionSuccessEvent
```

This proves runtime entity-event hooks exist around CRUD. The inspected create path does not directly invoke Redis, `MetadataCreateAppService`, `MetadataService`, or a generator class.

Whether an event listener outside this class consumes these runtime events for another purpose remains unverified.

## Child entities

`recursiveCreate(entityMeta, list)` traverses `EntityMeta.children`. For non-master entity metadata it resolves a DAO through:

```text
entityBeanContainer.findDao(childEntityMeta.getEntityClass())
```

and performs child creation through the recursive path. The parent `create` path therefore handles aggregate child persistence before the parent DAO create call.

## Evidence labels

### OBSERVED

- `createWithResult` calls `create`, normalizes action type, traverses DTO data, and returns the DTO.
- `create` converts DTO to the runtime Entity class with `BeanCopier.copy`.
- DAO resolution uses `EntityBeanContainer.findDao(entityClass)`.
- Single create invokes `BaseDao.create(entity)`.
- Batch create invokes `BaseDao.createBatch(entityList)`.
- Runtime lifecycle hooks and `EntityEventHelper` events are invoked.
- Child entities are traversed using `EntityMeta.children` and recursive creation.
- No direct metadata-service or generator invocation appears in the inspected create/createBatch bytecode.

### INFERRED

- The generated application DAO is supplied/registered through runtime `EntityBeanContainer`.
- The generated application is the provider of the concrete Entity class and DAO consumed by this runtime boundary.

### UNVERIFIED

- Outer transaction proxy/interceptor for normal create/createBatch.
- Any external listener consuming `EntityEventHelper` events.
- Any relationship between runtime CRUD events and design-time metadata or code generation.
- Physical database table and SQL mapping for the sample application.

## Runtime CRUD boundary snapshot

```text
BaseEntityCurdService.createWithResult(dto)
  → create(dto)
  → runtime preprocessing / validation / callbacks
  → recursive child handling
  → BeanCopier.copy(dto, entityClass)
  → EntityBeanContainer.findDao(entityClass)
  → EntityClassContext.withEntityClass(dao, entityClass, BaseDao.create(entity))
  → afterCreate / EntityEventHelper events
  → dto.actionType = NORMAL
  → return dto
```

This is the boundary needed by the construction audit. It is not a design-time construction or generation path.

## Closure decision

```text
P0-3A Runtime CRUD Boundary = CLOSED
```

Closed means the runtime CRUD semantic boundary is sufficiently defined for the construction audit and will not be pursued as an open-ended low-code runtime investigation. Further runtime digging is allowed only if P0-3B finds a concrete bridge that requires one additional lookup.

This boundary is explicitly separate from the design-time construction entry `udcEntityPost`.
