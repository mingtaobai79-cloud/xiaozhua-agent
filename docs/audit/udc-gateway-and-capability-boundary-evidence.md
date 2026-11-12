# UDC Gateway and Capability Boundary Evidence

结论：Gateway 已确认是独立的 Seeyon Agent 平台基础设施组件；UDC 请求不能直接抽象为“直连 UDC Pod”。当前已确认 Gateway 的部署、Artifact、动态服务发现和过滤器构成。UDC Entity/Attribute 契约已进入 operation catalog；菜单、页面、微流程尚未完成可执行契约，只完成入口盘点和部分静态证据。

## 1. Component boundary

```text
Seeyon Agent
├── Core
├── Components
│   ├── UDC
│   ├── BPM
│   ├── SPI
│   ├── Connector
│   └── Integration
├── Gateway / Platform access
├── Providers
└── Workflows
```

Gateway 不是 UDC 子模块，也不是普通业务组件。它是多个业务组件共同使用的平台访问层；Agent 的 UDC Adapter 应通过 Gateway contract 访问 UDC，而不是把 UDC Pod IP/Service 作为稳定外部入口。

## 2. Live test2 gateway deployment facts

Environment: `test2`
Path: SSH `10.0.0.1` → `kubectl --kubeconfig=configtest2`
Namespace: `lowcode-test`

Observed deployments/services:

```text
ctp-webapi-gateway-5fc4d9988-gnmv8
  image process: /app/ctp-webapi-gateway-assemble.jar --server.port=80
  service: ctp-webapi-gateway
  ClusterIP: 10.0.0.1
  port: 80

cip-openapi-gateway-d9cfb77bb-s475w
  image process: /app/cip-openapi-gateway-assemble.jar --server.port=80
  service: cip-openapi-gateway
  ClusterIP: 10.0.0.1
  port: 80
```

The target UDC Pod is separate:

```text
udc-7cbfc587f5-kwjdd
  image: udc:5.3.517
  Pod IP: 10.0.0.1
```

The target application has a debug NodePort, but this is not evidence that normal external requests bypass the gateway:

```text
app9000000000000000001-debug
  NodePort: 31653
```

## 3. Gateway artifact facts

From the live `ctp-webapi-gateway-assemble.jar`:

```text
ctp-webapi-gateway-web-5.3.266.jar
ctp-webapi-gateway-biz-5.3.266.jar
gateway-spi-5.3.260.jar
gateway-filter-5.3.260.jar
spring-cloud-gateway-server-3.1.9.jar
```

Gateway classes include:


```text
com.seeyon.ctp.webapi.gateway.config.GatewayConfig
com.seeyon.ctp.webapi.gateway.config.WebApiProperties
com.seeyon.ctp.webapi.gateway.discovery.ReactiveDiscovery
com.seeyon.ctp.webapi.gateway.discovery.CtpDiscoveryClientRouteDefinitionLocator
com.seeyon.ctp.webapi.gateway.discovery.nacos.NacosReactiveDiscovery
com.seeyon.ctp.webapi.gateway.cache.GatewayCache
com.seeyon.ctp.webapi.gateway.filter.SeeyonStripPrefixGatewayFilterFactory
com.seeyon.ctp.webapi.gateway.filter.ProcessHeaderGatewayFilterFactory
com.seeyon.ctp.webapi.gateway.filter.SignVerificationFilter
com.seeyon.ctp.webapi.gateway.filter.RequestTimeFilter
com.seeyon.ctp.webapi.gateway.filter.CtpCsrfFilter
com.seeyon.ctp.webapi.gateway.filter.TongWebResponseFilter
com.seeyon.ctp.webapi.gateway.utils.RequestUtil
```

Separate gateway SPI/filter artifacts include:

```text
com.seeyon.gateway.spi.SPIJarLoader
com.seeyon.gateway.spi.SPIClassloader
com.seeyon.gateway.spi.SPIProperties
com.seeyon.gateway.spi.filter.SpiGlobalFilter
com.seeyon.gateway.filter.GatewayBeforeFilter
com.seeyon.gateway.filter.GatewayAfterFilter
```

## 4. What is proven and what is not

Proven by live deployment and jar inventory:


- Requests are handled by a Spring Cloud Gateway-based service.
- Gateway discovers service instances using Nacos-related discovery classes and maintains a service-instance cache.
- Gateway has explicit prefix stripping, process-header, request-time, CSRF, signature-verification and response filters.
- Gateway contains a separate SPI loading/filter mechanism.
- UDC and Gateway are separate deployments/artifacts.

Not yet proven:


- Exact public request URL accepted by `ctp-webapi-gateway` for `/udc/graphql`.
- Whether UDC design-time GraphQL requests are routed by service name, a static route, or another gateway mapping.
- Exact path rewrite/strip-prefix behavior for `/udc/graphql`.
- Required authentication/signature/CSRF headers for a real external request.
- Exact response transformation by `TongWebResponseFilter`.
- Whether `cip-openapi-gateway` or `ctp-webapi-gateway` is the correct ingress for each UDC operation.

These remain `UNVERIFIED`; no request is executed merely from class names.

## 4A. Gateway route-generation facts from bytecode

`CtpDiscoveryClientRouteDefinitionLocator` proves the following implementation behavior:

```text
routeId = routeIdPrefix + ServiceInstance.serviceId
routeIdPrefix = DiscoveryLocatorProperties.routeIdPrefix
  or default "seeyon-" when empty
uri = DiscoveryLocatorProperties.urlExpression evaluated against ServiceInstance
metadata = copy(ServiceInstance.metadata)
order = Integer.MAX_VALUE
predicates = DiscoveryLocatorProperties.predicates
  with every argument evaluated as SpEL against ServiceInstance
filters = SeeyonStripPrefix + ProcessHeader + Retry
Retry = retries=2, methods=GET,POST, exception=io.netty.channel.unix.Errors$NativeIoException

Nacos instance selection:
selectInstances(serviceId, group, true)
only enabled && healthy instances are converted
```

This is stronger than the previous v0.1 result, but it still does not identify the UDC service ID. The service ID must be obtained from the actual Nacos service list/config or a live route definition; it must not be inferred from the UDC deployment name.

Gateway filter facts:

```text
GatewayConstant.PREFIX = "service"
RequestTimeFilter constant = "requestTimeBegin"
CSRF cookie = "XSRF-TOKEN"
CSRF header = "X-XSRF-TOKEN"
WebApiProperties includes ignoreUrls, ignoreCsrfUrls, csrf, timeWindow, rt, domain, loginUrl
```

Exact signature header, timestamp acceptance rule, CSRF ignore list, domain/token header names, and response envelope remain UNKNOWN.

## 5. UDC capability status

### Entity / Attribute

```text
status: VERIFIED_STATIC_BYTECODE + STATIC_FRONTEND_CONTRACT
scope: design-time entity and attribute operations
```

Evidence:

- UDC `EntityController` 5.3.517 method annotations and descriptors.
- Frontend modules `64527` and `48659`.
- Frontend GraphQL field names such as `udcEntityPost`, `udcEntityGet`, `udcEntityAttributePost`.
- DTO field and response selection sets in captured compiled chunks.

### Application / Menu

```text
status: PARTIAL / STATIC_FRONTEND_DISCOVERY
```

Known frontend chunks include application pages and new-application pages. Application DTOs and application-related UDC classes are present in the static module index. A menu-specific write/read operation contract has not been extracted yet. “Menu” must not be inferred from application page chunks alone.

### Page / Page Rule

```text
status: PARTIAL / STATIC_FRONTEND_DISCOVERY
```

The remote entry exposes page-rule chunks, including page-rule editor routes. Page metadata classes and runtime page services exist in the UDC artifact index. Exact page save/publish payload and Gateway-routed operation contract are still missing.

### MicroFlow

```text
status: PARTIAL / STATIC_BACKEND_AND_FRONTEND_DISCOVERY
```

Frontend evidence:

```text
/app-design/rule/microflow/
/app-design/rule/microflow/editor/{microflowId}
```

Backend evidence:

```text
MicroFlowController
MicroFlowInfoAppService
MicroFlowAppServiceImpl
BaseMicroFlowService
MicroFlowControllerProxyUtils
MicroFlowAutoCodeUtil
```

Generated customer-application evidence already contains many `MicroFlow*Controller` classes. Those prove generated application endpoints and AppService delegation patterns, but do not by themselves prove the design-time UDC microflow save/update API.

### Publish / Build / Runtime

```text
status: PARTIAL / STATIC_ARTIFACT_DISCOVERY
```

UDC artifacts contain publish, sandbox, build and runtime-related services. The operation contract and readback verifier are not yet closed.

## 6. Correct implementation layers

```text
Seeyon Agent Core
  → Gateway Access Provider
      → Gateway request contract
          → UDC Operation Adapter
              → Entity / Attribute / Application / Page / MicroFlow operation
                  → UDC
                      → readback / evidence
```

Do not put Gateway routing knowledge inside every UDC operation. Keep:

```text
GatewayAccessContract
UDCOperationContract
UDCReadbackContract
```

as separate contracts.

## 7. Next evidence slice

1. Inspect the gateway route-definition locator and prefix-strip filter with targeted bytecode, one class per command.
2. Correlate Gateway Nacos/service-discovery names with the live UDC service name.
3. Extract the frontend GraphQL loader implementation that converts `fieldType` into `/udc/graphql` and headers.
4. Add application read-only contract and prove `application_id` to numeric `appId` mapping.
5. Extract page and microflow design-time API modules before any write operation.
6. Only after Gateway + auth + response contract is proven, implement a read-only live request.

No mutation, publish, restart, database write or cache write was executed for this evidence slice.
