# P0-3B Design-time Artifact Discovery Audit

更新时间：2026-09-04

## Task

Find the server-side artifact that implements the design-time mutation:

```text
udcEntityPost
udcEntityPostInputBody
```

The search is intentionally bounded. Runtime CRUD (`BaseEntityCurdService`) is closed and not reopened.

## Search scope executed

### Local repository / source workspaces

```text
<MAVEN_REPO>
<EVIDENCE_ROOT>
<USER_HOME>/...
<USER_HOME>/...
<USER_HOME>/...
```

### Installation/deployment candidate roots checked when present

```text
C:/Program Files
C:/Program Files (x86)
C:/tomcat
D:/tomcat
C:/seeyon
D:/seeyon
```

### Targeted artifacts and forms

```text
udc-biz
udc-web
udc-assemble
udc-cicd
udc-upgrade
udc-extend
udc-starter-autocode
JAR / WAR / ZIP
Java/class resources
GraphQL / SDL / JSON / JS / schema candidates
```

Exact byte search terms:

```text
udcEntityPost
udcEntityPostInputBody
```

Supporting terms were used only for bounded candidate discovery:

```text
entityPost, createEntity, EntityAppService, EntityDto,
GraphQL, graphql, mutation, resolver, handler
```

## Results

### Design-time implementation artifact

```text
FOUND: NO
```

No physical UDC design-time implementation artifact containing the exact server-side literals was found in the checked local repository, workspace, temporary decompile products, installation roots, or deployment-style roots.

The only `udc-web-5.3.517.jar` outside the real repository was a pytest fixture (255 bytes, one class) and is excluded from evidence. It is not a product artifact.

### Runtime/facade artifacts

The following are real local artifacts, but they do not contain the design-time GraphQL literals:

```text
udc-common-5.3.517.jar
udc-facade-5.3.517.jar
udc-starter-lowcode-5.3.517.jar
udc-starter-runtime-5.3.517.jar
```

Their roles remain separated:

```text
udc-facade          = contract
udc-starter-lowcode = runtime CRUD semantics
udc-starter-runtime = runtime dynamic invocation / proxy
```

No claim is made that these artifacts implement `udcEntityPost`.

### GraphQL schema / introspection

```text
FOUND: NO
```

No local `schema.graphql`, `schema.graphqls`, introspection JSON, generated GraphQL schema, gateway schema, or BFF schema containing the exact target names was found in the bounded roots.

The frontend bundle contains the request-side field token, but that is not server schema evidence.

## Required chain status

```text
UDC Frontend
  ↓ VERIFIED_STATIC_SOURCE
createEntity(payload)
  ↓ VERIFIED_STATIC_SOURCE
udcMutationLoader.load(...)
  ↓ VERIFIED_STATIC_SOURCE
fieldType = udcEntityPost
paramsType = udcEntityPostInputBody
paramsKey = body
  ↓ UNKNOWN / MISSING ARTIFACT
GraphQL Field
  ↓ UNKNOWN
Resolver / Handler
  ↓ UNKNOWN
Java Class
  ↓ UNKNOWN
Java Method
  ↓ VERIFIED_STATIC_BYTECODE (contract only)
EntityAppService.create(SingleRequest<EntityDto>)
  ↓ UNKNOWN
EntityDto formation in this design-time chain
  ↓ UNKNOWN
Entity Definition / Metadata
  ↓ UNKNOWN
Construction / Publish / Generator Bridge
```

## Evidence ledger

| Item | Status | Evidence |
|---|---|---|
| Frontend `createEntity` request construction | VERIFIED_STATIC_SOURCE | `docs/audit/frontend/entity-api-module-64527-evidence.md`（**客户场景证据，已迁出至 `xiaozhua-customer-evidence/frontend/`**，仓库内已无此路径）; chunk SHA-256 `6051e1df6c574df74c842f9e4c0714fae5c7ff0df6e86e5ffa5b2d4f994f387d` |
| `udcEntityPost` frontend field token | VERIFIED_STATIC_SOURCE | module `64527` in same chunk |
| `udcEntityPostInputBody` frontend input token | VERIFIED_STATIC_SOURCE | module `64527` in same chunk |
| GraphQL server field definition | UNKNOWN | no local schema artifact |
| Resolver / Handler | UNKNOWN | no design-time implementation artifact |
| Resolver Java class/method | UNKNOWN | no design-time implementation artifact |
| `EntityAppService.create` signature | VERIFIED_STATIC_BYTECODE | `udc-facade-5.3.517`; SHA-256 `7e531005de3b94aaaa0ac847328551eaf6e014d743cedf5b79d4bab4769c6501` |
| `udcEntityPost → EntityAppService.create` invocation | UNKNOWN | no caller edge |
| EntityDto formation in this chain | UNKNOWN | no caller/mapper edge |
| Entity definition / metadata write | UNKNOWN | no design-time caller edge |
| Generator bridge | UNKNOWN | no producer edge |

## Correct conclusion

The current environment is missing the design-time GraphQL implementation artifact and local GraphQL schema/introspection evidence needed to close Bridge 1.

```text
P0-3B Bridge 1 = PAUSED
Reason = Design-time GraphQL implementation artifact unavailable
```

This is an audit result, not a failed search. The absence is valuable evidence that the available local set is primarily runtime/facade code plus frontend request artifacts, while the design-time server implementation is deployed or stored elsewhere.

## Stop condition applied

The following bounded paths have been checked:

```text
local Maven cache
source/workspace roots
temporary decompile outputs
installation/deployment-style roots available locally
Docker-style local artifacts available to the scan
local GraphQL schema/introspection candidates
```

No broader search is performed. No server mutation, deployment change, container start, or database operation was executed.

## Required next input

To resume Bridge 1, obtain one of:

```text
UDC design-time server JAR/WAR
UDC design-time server lib directory
GraphQL gateway/BFF artifact
schema.graphql / schema.graphqls
GraphQL introspection JSON
read-only listing/extraction of the deployed design-time service filesystem
```

Once obtained, inspect only:

```text
udcEntityPost
udcEntityPostInputBody
GraphQL field binding
Resolver / Handler class and method
EntityDto mapping
EntityAppService.create caller
```

Do not promote any edge from naming or interface existence alone.
