# P0-3B Design-time Construction Entry — Audit Status

## Scope lock

This phase follows only:

```text
UDC Entity Design
  → udcEntityPost
  → GraphQL field
  → Resolver / Handler
  → EntityAppService.create(EntityDto)
  → Entity Definition / Metadata
  → Generator Bridge
```

Runtime `BaseEntityCurdService` is closed separately and is not reopened here.

## Current verified frontend edge

Source:

```text
<SEEYON_AGENT_ROOT>/docs/audit/frontend/chunks/src_redux_store_ts.14dc061e.js  ← 客户场景证据，已迁出至 `<EVIDENCE_ROOT>/seeyon-customer-evidence/frontend/chunks/`，本仓不再持有
```

Source SHA-256:

```text
6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d
```

Module `64527` exports:

```javascript
async function createEntity(payload) {
  const response = await udcMutationLoader.load({
    fieldType: "udcEntityPost",
    paramsType: "udcEntityPostInputBody",
    paramsKey: "body",
    params: { ...payload, appId: currentAppId },
    queryFields: "content",
    showLoading: true
  });
  return response.content;
}
```

The UI thunk then treats the returned `content` as the new entity id, refreshes the list, loads the entity detail, and moves to the attribute-set screen. This proves the frontend request-construction edge only.

## Facade contract edge

Artifact:

```text
<MAVEN_REPO>/com/seeyon/udc-facade/5.3.517/udc-facade-5.3.517.jar
```

Artifact SHA-256:

```text
7e531005de3b94aaaa0ac847328551eaf6e014d743cedf5b79d4bab4769c6501
```

Interface:

```text
com.seeyon.udc.api.EntityAppService
```

Contract:

```text
SingleResponse<Long> create(SingleRequest<EntityDto>)
SingleResponse<Integer> update(SingleRequest<EntityDto>)
SingleResponse<Integer> deleteById(SingleRequest<Long>)
```

This is a verified facade contract, not yet a resolver-to-method invocation edge.

## Targeted search result for P0-3B-1 / P0-3B-2

The local 5.3.517 platform JARs inspected in this bounded pass contain no class-file constant-pool hit for the literal strings:

```text
udcEntityPost
udcEntityPostInputBody
```

The checked platform artifacts include:

```text
udc-common-5.3.517
udc-facade-5.3.517
udc-starter-lowcode-5.3.517
udc-starter-runtime-5.3.517
```

The frontend literal is therefore not sufficient to identify the server-side GraphQL resolver. The design-time web/GraphQL implementation artifact is not present in the inspected local 5.3.517 set.

## Current chain

```text
UDC Frontend
  ↓ VERIFIED_STATIC_SOURCE
createEntity(payload)
  ↓ VERIFIED_STATIC_SOURCE
udcMutationLoader.load(fieldType=udcEntityPost, paramsType=udcEntityPostInputBody, paramsKey=body)
  ↓ UNKNOWN
GraphQL field definition / input type / arguments / return type
  ↓ UNKNOWN
Resolver / Handler Java class and method
  ↓ UNKNOWN
EntityDto formation
  ↓ VERIFIED_STATIC_BYTECODE (facade contract only; caller unknown)
EntityAppService.create(SingleRequest<EntityDto>)
  ↓ UNKNOWN
Entity Definition / Metadata
  ↓ UNKNOWN
Generator Bridge
```

## Six required answers status

| Question | Status | Conclusion |
|---|---|---|
| What is `udcEntityPost`? | PARTIAL | Frontend mutation field token confirmed; schema definition unknown |
| Who handles it? | UNKNOWN | No local resolver/handler class identified |
| Where is `EntityDto` formed? | UNKNOWN | No request-to-DTO mapper/caller evidence |
| Who calls `EntityAppService.create`? | UNKNOWN | Facade contract exists; caller edge not proven |
| What follows create? | UNKNOWN | No design-time create implementation in local set |
| Where does Generator connect? | UNKNOWN | No first generator call edge identified |

## Evidence discipline

```text
OBSERVED:
Frontend module 64527 constructs a mutation-loader request.

OBSERVED:
Facade declares EntityAppService.create(SingleRequest<EntityDto>).

INFERRED:
The mutation response content is treated by the UI as a new entity id.

UNVERIFIED:
GraphQL schema, resolver, Java implementation, EntityDto mapping, metadata write, generator bridge.
```

No inferred edge is promoted to `VERIFIED_STATIC_BYTECODE`.

## Next bounded action

Continue only with a read-only, bounded extraction from the design-time server/web artifact or its deployed/static schema source, if available. The next successful evidence must include the actual GraphQL field binding and the Java method invocation. Do not return to runtime CRUD, POM discovery, global Generator scanning, or customer business detail.

## Current phase status

```text
P0-3A Runtime CRUD Boundary: CLOSED
P0-3B-1 udcEntityPost contract: PARTIAL / frontend edge only
P0-3B-2 Resolver / Handler: UNKNOWN
P0-3B-3 EntityDto formation: UNKNOWN
P0-3B-4 EntityAppService.create caller: UNKNOWN
P0-3B-5 create → Metadata: UNKNOWN
P0-3B-6 Metadata → Generator Bridge: UNKNOWN
```
