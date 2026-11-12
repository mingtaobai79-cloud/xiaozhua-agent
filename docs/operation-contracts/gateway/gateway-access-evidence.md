# Gateway Access Contract Evidence

更新时间：2026-09-04

## 当前目标

当前主线已从“研究 UDC Generator”切换为：

```text
User
  → AI Agent
  → Operation Intent
  → Platform Operation Layer
  → Gateway Access Layer
  → ctp-webapi-gateway
  → Nacos / Service Discovery
  → UDC / target service
  → Readback / Verification
```

UDC EntityService → EntityDao 的既有静态审计保留为背景证据，不再作为当前主线。

## 已从真实 test2 获取的事实

访问路径：

```text
SSH root@10.0.0.1
kubectl --kubeconfig=configtest2
namespace=lowcode-test
```

已观察到的 Gateway 资源：

```text
Deployment: ctp-webapi-gateway
Service: ctp-webapi-gateway
Service ClusterIP: 10.0.0.1
Service port: 80
```

另有：

```text
Deployment: cip-openapi-gateway
Service: cip-openapi-gateway
Service ClusterIP: 10.0.0.1
Service port: 80
```

当前不把 `cip-openapi-gateway` 认定为 UDC 设计态入口。

## Gateway Artifact

此前从真实 Gateway 运行包确认：

```text
ctp-webapi-gateway-web-5.3.266.jar
ctp-webapi-gateway-biz-5.3.266.jar
gateway-spi-5.3.260.jar
gateway-filter-5.3.260.jar
spring-cloud-gateway-server-3.1.9.jar
```

已确认类：

```text
com.seeyon.ctp.webapi.gateway.discovery.CtpDiscoveryClientRouteDefinitionLocator
com.seeyon.ctp.webapi.gateway.discovery.nacos.NacosReactiveDiscovery
com.seeyon.ctp.webapi.gateway.filter.SeeyonStripPrefixGatewayFilterFactory
com.seeyon.ctp.webapi.gateway.filter.ProcessHeaderGatewayFilterFactory
com.seeyon.ctp.webapi.gateway.filter.SignVerificationFilter
com.seeyon.ctp.webapi.gateway.filter.RequestTimeFilter
com.seeyon.ctp.webapi.gateway.filter.CtpCsrfFilter
com.seeyon.ctp.webapi.gateway.filter.TongWebResponseFilter
```

## 已确认的路由生成逻辑

```text
routeId = routeIdPrefix + serviceInstance.serviceId
routeIdPrefix 默认值：seeyon-
route URI = DiscoveryLocatorProperties.urlExpression evaluated against ServiceInstance
route metadata = ServiceInstance.metadata copy
route order = Integer.MAX_VALUE
healthy instance = enabled && healthy
Nacos selection = selectInstances(serviceId, group, true)
```

已确认的默认过滤器组成：

```text
SeeyonStripPrefix
ProcessHeader
Retry(retries=2, methods=GET,POST)
```

## 已确认但尚未闭合的事实

```text
Gateway public ingress host/path                    UNKNOWN
ctp-webapi-gateway → UDC service name               UNKNOWN
UDC service name in Nacos                           UNKNOWN
UDC /udc/graphql 是否经过 ctp-webapi-gateway       UNKNOWN
StripPrefix 的实际 path mapping                     UNKNOWN
ProcessHeader 的实际 header 名和值                  UNKNOWN
SignVerification 必需 header / 算法                  UNKNOWN
RequestTime 必需 header / 接受窗口                    UNKNOWN
CSRF 的实际 ignore list                              UNKNOWN
成功响应 envelope                                    UNKNOWN
错误响应 envelope                                    UNKNOWN
```

UDC Pod 日志已观察到：

```text
request url:/udc/graphql
```

这证明 UDC 收到了 GraphQL 请求，但没有证明该请求经过 `ctp-webapi-gateway`，也没有暴露 GraphQL field 或 Gateway route。

## 当前合同边界

已允许：

```text
GET
只读 HTTP 查询
结构化 response/error
脱敏 request/response evidence
```

当前实现仍未把 GraphQL query 宣称为真实闭环，因为通用 GraphQL 服务通常使用 POST，而当前合同明确禁止 POST。只有取得 Gateway 实际允许的只读 GraphQL 传输方式后，才升级为真实 GraphQL readonly operation。

禁止：

```text
POST
PUT
PATCH
DELETE
publish
apply
restart
数据库写入
Redis 写入
Nacos 修改
```

## Agent 代码

新增：

```text
components/gateway/models.py
components/gateway/client.py
components/gateway/discovery.py
components/gateway/filters.py
components/gateway/adapter.py
components/gateway/__init__.py
tests/test_gateway_adapter.py
```

当前 Adapter 默认 `allow_network=False`，只有显式配置才允许 GET 网络访问。

## 当前状态

```text
Gateway deployment/service inventory             VERIFIED_LIVE_K8S (此前已验证)
Gateway artifact/module inventory                VERIFIED_LIVE_STATIC_ARTIFACT
RouteDefinitionLocator behavior                 VERIFIED_STATIC_BYTECODE
Nacos discovery class existence                  VERIFIED_STATIC_ARTIFACT
Nacos service → Gateway route instance           PARTIAL
Gateway → UDC real route                        BLOCKED（当前 VPN 断开，无法查询 test2）
Gateway filter class existence                   VERIFIED_STATIC_ARTIFACT
Filter exact runtime contract                    UNVERIFIED
Success/error envelope                          UNVERIFIED
Agent readonly client structure                 VERIFIED_LOCAL_COMPILE
Agent → Gateway → UDC real readonly operation   BLOCKED（当前 VPN 断开）
```

## 单次连接诊断（2026-09-04）

本轮仅执行一次网络诊断，未重复 SSH 重试：

```text
本机 Sangfor SSL VPN VNIC：媒体已断开连接
10.0.0.1:22：TCP timeout
10.0.0.1：ICMP 单包超时
lowcode-test2.example.com：DNS 无法解析
lowcode-openapi-test2.客户方.com：DNS 无法解析
SSH 私钥：本机存在
kubeconfig：本机存在
```

归类：`VPN / 内网连接未建立`。由于 TCP 尚未到达 SSH 握手阶段，当前不能归因于 SSH 服务、私钥或认证；也不能判定目标主机故障或网络策略阻断。

恢复 VPN 后的唯一下一步：只读取 Gateway/UDC Pod、Service、Endpoint、Gateway 配置与 Nacos 服务实例，以闭合 `gateway path → route_id → service_id → UDC target path`。恢复前不扩展 Adapter、不猜 route/service/header，也不执行任何写操作。

## 证据限制

- 本文件不记录密码、token、私钥或 kubeconfig 内容。
- 不用 UDC Pod IP、客户应用 Deployment 名称或前端 fieldType 猜测 Gateway service name。
- 没有真实 Gateway request/response 之前，不把 contract 状态升级为 COMPLETE。
