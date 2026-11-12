# Entity runtime and deployment boundary evidence (5.3.517)

## Verified findings

### 1. Runtime Entity consumption

```text
UdcProxyEntityAppService.selectById/selectByIds
  ↓
UdcProxyAppServiceComponent.proxyEntityAppServiceMethod
  ↓
FormHandler.getClass(appName, dtoFullName)
  ↓
FormHandler.getBeanObject(interfaceClass, appName)
  ↓
reflective method(methodName, SingleRequest.class)
  ↓
JSON → metadata-declared parameter DTO
  ↓
Method.invoke(bean, SingleRequest.from(paramDto))
```

### 2. AppService metadata resolution

```text
EntityAppServiceInvokeService.findAppServiceMetaData(entityAppName, entityFullName)
  ↓
BeanNameConvert.entity4NameTo4Name(entityFullName, APPSERVICEIMPL)
  ↓
MetadataQueryAppService.selectAppServiceMetadataByFullName(...)
```

The invoke path selects an `AppServiceMethodMetadataDto` by method-name suffix, reads `interfaceClass` and `parameter.item.itemType`, deserializes that parameter class, and invokes the generated bean.

### 3. GraphQL transport

```text
GraphqlProxyController.doGraphql
  ↓
GraphqlProxyAppServiceImpl.doGraphQL
  ↓
POST http://127.0.0.1:{httpPort}/graphql-app/{appName}/graphql
```

The serialized envelope is `GraphqlProxyRequestDto`: `appName`, `appType`, `query`, `operationName`, `variables`.

### 4. Application deployment persistence

`CustomApplicationService.create(CustomApplicationDto)` is a separate application-registry path. Its bytecode shows:

```text
CustomApplicationService.create
  ↓
createBatch
  ↓
CustomApplicationDao.createBatch
  ↓
publish CustomApplicationCreateEvent
```

This proves persistence and event publication for the custom-application registry, not Entity metadata creation. `CustomApplicationService` also consumes deployment notices and updates deployment state through `CustomApplicationDao.update`, with event publication on relevant state changes.

### 5. Runtime load event

`AppLoadEventListener.onCompleteLoad(AppInfoDto)` publishes an application-load notification through `StringRedisTemplate.convertAndSend(...)` containing `appName`, `appVersion`, and `traceId`. `onUnLoad` clears `EntityRelationHandler` cache.

## Evidence boundary

The current 5.3.517 runtime artifact does not contain a class named `EntityAppServiceImpl`, `MetadataCreateAppService`, or an obvious code-generator implementation. The artifact contains the runtime consumer and registry/deployment mechanics. Therefore:

- Generated Entity AppService consumption: `VERIFIED_STATIC_BYTECODE`.
- Custom application registry DB write and create event: `VERIFIED_STATIC_BYTECODE`.
- Entity design-time `create(EntityDto)` implementation: `UNVERIFIED`.
- Entity metadata write / physical table: `UNVERIFIED`.
- Code-generation trigger and generated source: `UNVERIFIED`.
- Application-load event as a runtime cache boundary: `VERIFIED_STATIC_BYTECODE`.

Do not merge the CustomApplication registry write with Entity metadata persistence. They are separate object families and must remain separate evidence nodes.
