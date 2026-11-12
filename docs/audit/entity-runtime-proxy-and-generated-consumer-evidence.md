# Entity runtime proxy / generated consumer evidence (5.3.517)

## Artifacts

- Runtime JAR: `<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`
- SHA-256: `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`
- Extracted evidence: `docs/audit/artifacts/udc-runtime-5.3.517/`
- Common DTO JAR: `<MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar`
- Common DTO SHA-256: `30085724949703b1c2f96a37e72813a6ed9e7b752ebc206c7a47d26afceb30d7`

## Verified static chain

```text
GraphqlProxyController.doGraphql(GraphqlProxyRequestDto)
    ↓
GraphqlProxyAppService.doGraphQL(SingleRequest<GraphqlProxyRequestDto>)
    ↓
GraphqlProxyAppServiceImpl
    ↓
UdcJsonUtils.toJsonNotIncludeNull(request DTO)
    ↓
HttpClientUtil.post(url, json, propagated context headers)
    ↓
URL = http://127.0.0.1:{Apps.getHttpPort()}/graphql-app/{appName}/graphql
```

`GraphqlProxyRequestDto` carries the exact proxy envelope fields:

```text
appName
appType (default FORM)
query
operationName
variables
```

The proxy copies request context headers for:

```text
Accept-Language
userId
loginOrgId
tenantId
traceId
```

For normal generated Entity runtime calls, the runtime uses a different path:

```text
UdcProxyEntityAppService.selectById / selectByIds
    ↓
UdcEntityRequestDto
    ├── entityHostAppName
    ├── entityAppName
    ├── entityFullName
    ├── methodMetadata
    └── data = SingleRequest(id) or List(ids)
    ↓
UdcProxyAppServiceComponent.proxyEntityAppServiceMethod(...)
    ↓
FormHandler.getClass(appName, dtoFullName)
    ↓
FormHandler.getBeanObject(interfaceClass, appName)
    ↓
reflection: declared method(methodName, SingleRequest.class)
    ↓
UdcJsonUtils.fromJson(requestJson, parameterClass)
    ↓
Method.invoke(bean, SingleRequest.from(paramDto))
```

`EntityAppServiceInvokeService` obtains the generated app-service metadata from `MetadataQueryAppService.selectAppServiceMetadataByFullName(...)`, selects a method whose full name ends with the requested method name, obtains its `interfaceClass` and parameter item type, deserializes the request, and invokes the generated bean reflectively.

## EntityDto contract

`udc-common 5.3.517` defines `com.seeyon.udc.common.dto.EntityDto` with:

```text
EntityBaseDto inherited identity/application/name/caption/description fields
capFirstName / unCapFirstName
fullName
dtoFullName
attributes: List<AttributeDto>
parent: EntityDto
children: List<EntityDto>
events: List<EventQueryResultDto>
hasChild
hasValidateRule
hasAssignValueRule
hasDefaultValueRule
generateAggregateValidateClass
generateAggregateAssignClass
generateAggregateDefaultValueClass
hasOrderNo
hasDefaultValueSystemVariable
indexes: List<IndexDto>
```

The constructor initializes the boolean feature flags to false. `getCapFirstName()` and `getUnCapFirstName()` derive names from the base `name` field.

## Boundary / status

This closes a real runtime-consumer path for already generated Entity app services and a real GraphQL proxy transport path. It does not establish that the design-time mutation `udcEntityPost` itself creates the generated classes, nor does it identify the concrete implementation behind `EntityAppService.create(EntityDto)`. The creation/generation trigger and physical persistence remain `UNVERIFIED`.
