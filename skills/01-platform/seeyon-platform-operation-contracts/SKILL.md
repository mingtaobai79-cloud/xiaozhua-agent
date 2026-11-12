---
name: seeyon-platform-operation-contracts
description: "Use for Seeyon Gateway and platform operation contracts."
version: 0.1.0
author: 小爪 🐾
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [seeyon, gateway, udc, operation-contract, evidence, nacos]
    related_skills: [seeyon-low-code-environment, seeyon-udc-runtime, codebase-extraction]
---

# Seeyon Platform Operation Contracts

## Purpose

Use this skill when the goal is to make Seeyon Agent operate existing Seeyon platform capabilities as a user through verified APIs, rather than reproducing UDC's Java source generator.

The target is a reusable operation layer:

```text
User requirement
  → intent/task
  → capability selection
  → operation contract
  → shared Gateway access
  → target component operation
  → readback/evidence
```

This skill covers the shared Gateway boundary and capability-contract work for UDC, BPM, Connector, Integration, and Runtime. UDC is one component under Seeyon Agent, not the whole architecture. SPI is an exception: model it as an extension lifecycle, not as a low-code user-operation contract.

## Non-goals

Do not:

- generate a parallel Java implementation of UDC;
- treat generated Entity/DTO/Controller classes as templates to clone;
- connect directly to a Pod IP as the stable Agent interface;
- promote a class name, frontend token, or similar method name into a verified call edge;
- perform POST, publish, restart, database, Redis, or cache writes while only doing contract discovery;
- let Entity/Attribute consume the entire UDC research scope while Page, MicroFlow, Publish, and Runtime remain unmodeled.

## Three contract layers

Keep these objects distinct:

```text
Capability Catalog
  What capabilities appear to exist, and what evidence level supports them?

Operation Contract
  How does one concrete capability accept input, return output, and support readback?

Gateway Access Contract
  How do all platform requests reach a service through Gateway, discovery, filters, and response handling?
```

Relationship:

```text
Capability Catalog
  → selects capability
Operation Contract
  → uses shared transport boundary
Gateway Access Contract
  → Gateway → discovery → target service
```

`UNKNOWN` is a valid value. An incomplete contract must remain incomplete instead of being made executable by inference.

## Architecture boundary

```text
Seeyon Agent
├── Core
│   ├── intent/task
│   ├── planning
│   ├── execution
│   ├── evidence
│   └── safety
├── Platform Operation Layer
│   ├── Gateway Access Layer
│   ├── UDC Adapter
│   ├── BPM Adapter
│   ├── Connector Adapter
│   ├── Integration Adapter
│   └── Runtime Adapter
├── SPI Extension Layer
├── Providers
└── Workflows
```

Gateway is shared infrastructure. UDC, BPM, and Connector are peer components. Do not put Gateway routing assumptions into every module adapter.

## Workflow

### 1. Lock environment and evidence scope

For test2 use the verified access path:

```text
Windows → SSH 10.0.0.1 → kubectl --kubeconfig=configtest2 → namespace from remote context
```

Confirm namespace and target deployment before extracting facts. Keep environment, artifact version, and source path in each evidence record.

### 2. Build Gateway Access Contract before module adapters

Inspect the running Gateway artifact and record facts in:

```text
docs/operation-contracts/gateway/gateway-access-v0.1.json
```

Minimum fields:

```json
{
  "gateway": {},
  "routing": {},
  "filters": {},
  "authentication": {},
  "request": {},
  "response": {},
  "errors": {},
  "evidence": [],
  "unknowns": []
}
```

Never implement the client before the route, discovery, authentication, and response boundaries are sufficiently evidenced.

### 3. Extract dynamic route behavior from Gateway bytecode

For Spring Cloud Gateway, inspect the route locator and discovery classes. Record exact behavior:

```text
RouteDefinitionLocator
  → service list
  → service instances
  → route ID
  → URI expression
  → predicates
  → filters
```

Verified Seeyon Gateway behavior:

```text
routeId = routeIdPrefix + ServiceInstance.serviceId
routeIdPrefix = configured DiscoveryLocatorProperties.routeIdPrefix
  or default "seeyon-"
uri = DiscoveryLocatorProperties.urlExpression evaluated against ServiceInstance
metadata = copy(ServiceInstance.metadata)
route order = Integer.MAX_VALUE
predicate arguments = SpEL evaluated against ServiceInstance
```

The route locator adds:

```text
SeeyonStripPrefix
ProcessHeader
Retry(retries=2, methods=GET,POST,
      exception=io.netty.channel.unix.Errors$NativeIoException)
```

Nacos discovery selects:

```text
NamingService.selectInstances(serviceId, group, true)
```

and rejects instances that are not both enabled and healthy. Do not infer the actual UDC `serviceId` from its deployment name; obtain it from Nacos, route definitions, configuration, or runtime evidence.

### 4. Treat filters as separate evidence problems

Record class existence separately from behavior:

```text
SeeyonStripPrefixGatewayFilterFactory
ProcessHeaderGatewayFilterFactory
SignVerificationFilter
RequestTimeFilter
CtpCsrfFilter
TongWebResponseFilter
GlobalExceptionHandler
```

Known constants from the target artifact may be recorded as facts:

```text
GatewayConstant.PREFIX = "service"
RequestTimeFilter constant = "requestTimeBegin"
CSRF cookie = "XSRF-TOKEN"
CSRF header = "X-XSRF-TOKEN"
```

Do not claim exact signature headers, timestamp acceptance, path-strip count, token/domain headers, response envelope, or error envelope until implementation or configuration proves them.

### Classify side effects through the callee

- During static discovery, inspect the implementation before classifying a check/init/search/export endpoint as read-only. Validation can persist imported templates, publish async events, update task caches, or notify users. Keep unexamined actions `state_changing=UNKNOWN`, `can_execute=false`; HTTP method and operation name do not settle the policy.
- Keep artifact-template evidence separate from source-template evidence. A template present in one jar supports that entry only; a template absent from that jar may belong to a sibling module. Record the scoped absence, not a platform-wide absence.
- Build offline evidence replay with source/range hashes and exact extraction comparison. Verify that tampered route, side-effect classification and execution flags are rejected, and that missing local source/config returns a structured nonzero failure. Replay PASS only proves evidence integrity, never live execution or business success.

### 5. Catalog broad capabilities, then create contracts

Keep the catalog broad:

```text
UDC
├── Application
├── Resource/Menu
├── Entity/Attribute
├── Page
├── MicroFlow
├── DataFlow
├── Publish
├── Build/Sandbox
└── Runtime
```

Recommended order:

```text
P0 Gateway
P1 Application / Resource / Menu
P2 Entity / Attribute
P3 Page
P4 MicroFlow
P5 Publish / Build / Runtime
```

For each capability, create a contract only when request shape, transport mapping, response, and readback path have evidence. A frontend chunk or GraphQL field name is discovery evidence, not automatically an executable contract.

### 6. Separate frontend GraphQL evidence from backend REST evidence

Frontend may contain:

```text
fieldType: udcEntityPost
paramsType: udcEntityPostInputBody
paramsKey: body
```

Backend may contain:

```text
@RequestMapping("udc/entity")
@PostMapping
create(EntityDto)
```

Record both, but keep the bridge explicit:

```text
frontend GraphQL field
  → GraphQL loader
  → Gateway
  → resolver/handler
  → backend controller/service
```

Only mark the bridge verified when schema, resolver, request trace, or equivalent direct evidence proves it. Static similarity is not proof.

### 7. Keep module capabilities first-class

The Agent-facing plan should look like:

```text
resolve application
  → resolve resource/menu
  → create/update entity
  → create attributes
  → create/update page
  → bind data source
  → add widgets
  → create/update microflow
  → publish/build
  → readback
```

The reasoning layer must not call GraphQL directly. Use:

```text
Intent
  → Operation Planner
  → Capability Registry
  → Operation Contract
  → Gateway Access
  → Component Adapter
  → platform
  → readback verifier
```

For MicroFlow capture separately:

```text
Definition / Group / Trigger / Node / Parameter / Data Mapping / Runtime Invocation
```

For Page capture separately:

```text
Page Schema / Layout / Widget / Data Source / Page Rule
```

Do not confuse generated customer `MicroFlow*Controller` runtime endpoints with design-time UDC save APIs.

## Safety and execution gates

During contract discovery:

```text
read-only artifact inspection: allowed
frontend static analysis: allowed
Kubernetes inventory/log/config read: allowed
real write request: blocked until explicitly authorized
```

Before any write, require:

```text
verified Gateway route
verified authentication context
verified request payload
verified response interpretation
defined readback target
explicit user authorization
```

After a write, read back the same target and distinguish API, business, persistence, publish/build, and runtime success.

### UDC workflow acceptance

1. Resolve services, event objects, entity attributes and expression functions from actual candidate APIs or authoritative metadata before assembling a node; never invent ids, signatures, event names or expression tokens. Keep reusable platform mechanics in the library and customer-specific inventories in temporary task evidence.
2. Preserve the workflow kind and interface from authoritative metadata when updating; do not convert a standard service microflow into a custom microflow as a save workaround. Keep backend microflows and page-bound rules separate.
3. Trace each node's dynamic configuration request and capture its loaded values, then save and reopen that exact node. Check mandatory highlighted fields, mapping rows, parameter types, candidate validity and visible captions; zero red messages or a successful schema check alone is insufficient.
4. Verify nested save DTOs field by field. Distinguish outer rule ids from inner mapping ids and canvas definition strings from mapping-detail JSON strings; follow service assignments rather than similarly named fields. Check source/target attribute types and canvas/mapping references before updating.
5. Read back persisted content, then verify the actual UI and business behavior. When the user's acceptance requires clicking Build on the page, perform that page action and verify its result; a direct deploy endpoint is not a substitute. Report each untested layer explicitly and never call a write-chain response a complete generation guarantee.

## Design-time write chain (live-verified on test2; agent emits plan data, host executes)

The full requirement→platform chain below is LIVE-verified end to end. The agent never sends writes itself (the policy gate returns POLICY_DENIED for `write=True` contracts by design); it emits executable plan data and the host (Hermes/CC/Codex, authorized) executes the steps:

```text
POST /service/udc/entity                       EntityController.create(EntityDto)
POST /service/udc/entity/attribute             createAttribute(AttributeDto) — appId+entityId+dataType all required
POST /service/udc/page-info/base-info/create   PageInfoController.createBaseInfo(PageDefinitionDto) — LIST+DETAIL pair
POST /service/udc/runtime/deploy-normal        DeployController.deployNormal(DeployNormalDto) — sandbox app build
                                               body is NAME-WRAPPED: {"deployDto": {...}}
```

Hard-won rules:

- **EntityDto needs the FULL bill-family shape**, not minimal fields: `appId`(numeric Long, not the app-name string), `stereotype`, `entityNature:"MAIN"`, `features`, `multiplicity:"ONE2MANY"`, `category:"ENTITY"`. Missing stereotype/entityNature → `BOOT_1001` / `UDC_ENTITY_0010`. When `appId` arrives as an app-name string, extract the trailing numeric guid — the DTO deserializes it as Long (`Failed to deserialize ... appId to type Long`).
- **Controlled vocabularies are live-snapshot facts, not inventions.** stereotype ∈ {archive, standard, bill, archiveTree} (statistically read from 169 real entities via `GET /udc/entity/primary/select-by-appid/{numericAppId}` — note the entity read route takes the numeric id, not the app-name string). dataType ∈ {ENTITY, DATETIME, ENUM, STRING, MULTILINESTRING, BOOLEAN, BIGINTEGER, INTEGER, DECIMAL, DATE, Serial} (read from 51 real attributes). DeployTypeEnum {TEST, RELEASE, ON_ONLINE, DELTA}, ProjectTypeEnum {FRONTEND, BACKEND, ALL}, TerminalTypeEnum {ALL, PC, MOBILE} (pod javap). When inventing a value outside the snapshot is tempting, flag it into the plan's `unknowns` instead.
- **Resolve payloads from the real frontend request and backend binder before probing writes.** Capture the UI loader/body, trace the matching controller DTO and service assignments, and compare a genuine persisted sample. Use validation errors only for bounded, authorized confirmation of an evidenced candidate; stop repeated body guessing when source or a live request is available. An error moving to another validator proves only that validation advanced, not persistence or resolution of the original defect. For example, pageType → pageUrl → curTerminalType identifies required fields, while `actionType` must come from its real enum {NORMAL, INSERT, UPDATE, DELETE}, not an invented `VIEW`.
- **App-level build ≠ entity-level publish — two different chains.** The working build path is `POST /service/udc/runtime/deploy-normal` with a NAME-WRAPPED body `{"deployDto": {appId, deployType:RELEASE, projectType:ALL, terminalType:ALL}}` → sandbox pipeline (`UdcAppDeployService` + `PipelineProperties` + `SandboxK8sService`), recorded in `udc_test2.udc_deploy_record` with `deploy_type=2`=RELEASE and `state=1`=build success. The entity-level `PublishStateController.update` path demands `entityClassName/ids/password` (a designer deploy password that is not in Nacos) — do not conflate the two when a publish seems blocked.
- **Physical tables land in the application's OWN database** (`<appName>_<env>`, e.g. znxmglpt9000000000000000002_test2), NOT in udc_test2. Verifying "did the build create the table" against udc_test2 returns a false negative; query SHOW TABLES against the app DB.
- **Pages are NOT created by the build.** Page creation is a separate design-time action that must run before the build so the pages ship with it; the runtime C2b metadata face only returns published pages, so a freshly created design page reading as absent there is expected, not a failure. Verify page creation via `GET /service/udc/page-info/select-by-appId/{appId}` (reads by relationGroupId; a read by page id on that surface 404s).
- **Platform auto-fills the bill-family system attributes** (billCode, caseTitle, statusType, creator… ~51 columns) when the entity is created with a bill stereotype — do not hand-create them.
- Frozen implementation of the plan generator: repo `components/platform_operations/deployment.py` (`build_deployment_plan` → steps entity.create → attribute.create → page.create → deploy.normal, each with body + verify + note) exposed to hosts as `seeyon_host_bootstrap.deploy_plan()`; registry R18 pins `udc.deploy.normal` (write=True, OBSERVED) and `udc.deploy.search_status` no longer needs to stay unpinned for a prefix reason: `DeploymentController` is class-level `udc/deployment` (reads `/latest-test-info`, `/app-ready-state`, `/restart`, `/app-online`, `/app-online-new`, `/app-delta-deploy`) and carries class-level `@HasRole(udcAppDesigner, udcSystemAdmin, OpsAdmin, BpmSystemManager)`.
- **Resolve a controller's class-level prefix from bytecode; never probe it by URL guessing.** `javap -v` prints CLASS-level annotations *after* the `SourceFile:` line at the very END of the output, while `#NN = Utf8 RuntimeVisibleAnnotations` constant-pool entries and per-method blocks appear earlier — so grepping for the annotation name returns the field/method annotation and hides the class one. Read it with `sed -n '/^SourceFile/,$p'`, then resolve the referenced `#NN` ids in the constant pool. `DeployController` = class `udc/runtime` + method `deploy-normal` → working URL `/service/udc/runtime/deploy-normal`.
- **A Seeyon Boot 404 is usually an authorization denial, not a missing route.** `@HasRole` failure renders a Spring Whitelabel 404, and the request still writes an `AppContextFilter` line into the pod log (so "nothing logged" never proves the route is absent). Cheap verb probe: `405 Method Not Allowed` proves the route PATH is mapped. Caveat: a literal segment can be captured by a sibling `/{id}` route, so a 405 on a guessed sub-path means "this exact path exists", not "this is the operation" — `POST /service/udc/application/create` 405s through the GET-mapped `/application/{id}` matching `create` as an id, while the real create route is the class ROOT `POST /service/udc/application` (siblings `create-page-app`, `create-layout-app`, `create-from-template`, `appVersion/{appGuid}` do exist). Resolve literal segments from `javap -v` constant-pool `Utf8` entries. Confirm role membership by reading the pod's `SecurityService` role-code dump instead of concluding the route is unregistered.
- **`@MultiRequestBody` binds by PARAMETER NAME, not by the DTO's fields.** Seeyon Boot's binder pulls each argument from the JSON top level under its local-variable name, so a body carrying the DTO's own keys binds as `null` and fails later with a SpEL complaint about the first field it tried to read — `EL1007E: Property or field 'appId' cannot be found on null`, returned as **HTTP 200 with `"status":3`**. Wrap under the parameter name (`{"deployDto": {...}}`); read the response envelope, never the HTTP status, to judge success.
- **Both binding flavours are live platform-wide; measure per endpoint, never generalize.** `@MultiRequestBody` (binds by parameter name → wrapped body) and plain `@RequestBody` (flat body) coexist in the design-time surface: `deploy-normal` is `@MultiRequestBody`, while `ApplicationController.create` (`POST /service/udc/application`) is flat `@RequestBody`. The wrong pairing does not 4xx — it reports the FIELDS as absent, so it reads like a wrong field name: wrapped body into a flat handler → `BOOT_1001 caption must not be blank`; flat body into a `@MultiRequestBody` handler → `BOOT_3000 EL1007E: Property or field 'x' cannot be found on null`. Discriminator: POST both variants of the same minimal body and keep the one whose validation error MOVES ON to the next missing field instead of repeating the first-field complaint.
- **`javap -classpath '<jarpath>/*'` resolves any class** without first hunting its owning jar; use it before spending calls on `unzip -l` scanning.
- **One build exposes several status surfaces; only `udc_deploy_record` is ground truth.** `sandbox/build-info/{appId}` reports `state:NONE` for the whole life of a `deploy-normal` run (it tracks the separate sandbox build, not the publish pipeline), and `deployment/latest-test-info` keeps `testSuccess:false` until a test actually succeeds. Judging the run by those yields a false "the build never started" — the pipeline was in fact executing and failing.

## Evidence grades

```text
FACT
OBSERVATION
STATIC_FRONTEND_DISCOVERY
VERIFIED_STATIC_BYTECODE
UNVERIFIED
BLOCKED
```

Keep `Construction Rule`, `Runtime Contract`, and `Generation Causality` separate. Generated output does not prove its producer chain.

## Verification checklist

- [ ] Gateway is shared infrastructure, not a UDC child.
- [ ] UDC is one component under Seeyon Agent.
- [ ] Capability Catalog and Operation Contract are separate.
- [ ] Route ID, URI, discovery, and filter facts come from target artifact/config.
- [ ] Actual service ID is not guessed from deployment name.
- [ ] Frontend GraphQL evidence is not silently promoted to HTTP execution evidence.
- [ ] Application, Resource/Menu, Page, MicroFlow, Publish, and Runtime remain visible.
- [ ] Generated runtime controllers are not confused with design-time UDC APIs.
- [ ] No write is executed during static contract discovery.
- [ ] Unknowns are explicitly recorded.
- [ ] Existing tests are rerun after repository changes.

## References

- `references/test2-gateway-udc-contract-facts.md` — condensed facts from the live test2 Gateway and UDC artifact investigation, including route generation, filter constants, UDC capability status, and explicit non-claims.
- `references/udc-design-time-write-chain.md` — the live-verified write-chain detail: full request bodies, error-code oracle log per step, value-domain provenance, deploy-record semantics, and the repo deploy_plan mapping.
