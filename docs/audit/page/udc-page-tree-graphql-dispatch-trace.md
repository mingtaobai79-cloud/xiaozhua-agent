# UDC GraphQL Dispatch Fact Closure

状态：`PARTIAL / DISPATCH_TRANSPORT_CONFIRMED`

目标 fieldType：

```text
udcMetaDataSelectFunctionNodeWithPageTreePost
```

## 一、当前已经闭合的分发层

### 1. UDC 前端 loader

前端使用：

```text
loader: a.wh.load
fieldType: udcMetaDataSelectFunctionNodeWithPageTreePost
paramsType: udcMetaDataSelectFunctionNodeWithPageTreePostInputBody
paramsKey: body
```

### 2. UDC GraphQL proxy Controller

来源：

```text
docs/audit/artifacts/udc-runtime-5.3.517/GraphqlProxyController.javap.txt
```

已确认：

```text
com.seeyon.boot.starter.udcrt.controller.GraphqlProxyController
    doGraphql(GraphqlProxyRequestDto)
        ↓
GraphqlProxyAppService.doGraphQL(SingleRequest<GraphqlProxyRequestDto>)
```

字节码调用边：

```text
GraphqlProxyController.doGraphql
→ SingleRequest.from(dto)
→ GraphqlProxyAppService.doGraphQL
```

### 3. GraphQL Proxy AppService

来源：

```text
docs/audit/artifacts/udc-runtime-5.3.517/GraphqlProxyAppServiceImpl.javap.txt
```

已确认：

```text
com.seeyon.boot.starter.udcrt.appservice.GraphqlProxyAppServiceImpl
    doGraphQL(SingleRequest<GraphqlProxyRequestDto>)
```

方法实际行为：

```text
读取 GraphqlProxyRequestDto
→ 读取 RequestContext
   → traceId
   → userId
   → loginOrgId
   → tenantId
→ 构造 HttpHeader
→ 根据 appName / appType 计算目标 URL
→ GraphqlProxyRequestDto 序列化为 JSON
→ HttpClientUtil.post
→ SingleResponse.from(response)
```

GraphQL 请求头中已通过字节码确认加入：

```text
traceId
userId
loginOrgId
tenantId
Accept-Language（缺失时取当前 Locale）
```

### 4. GraphQL 目标 URL

`GraphqlProxyAppServiceImpl.getUrl(appName, appType)` 的字节码确认：

基础地址：

```text
http://127.0.0.1:{Apps.getHttpPort()}/{Apps.getAppName()}
```

当 `appType == FORM` 且 appName 非空时：

```text
http://127.0.0.1:{httpPort}/{hostAppName}/graphql-app/{appName}/graphql
```

非 FORM 分支：

```text
http://127.0.0.1:{httpPort}/{hostAppName}/graphql
```

当前可确认的分发传输链：

```text
UDC 前端 fieldType
    ↓
GraphQL loader 组装 GraphqlProxyRequestDto
    ↓
GraphqlProxyController.doGraphql
    ↓
GraphqlProxyAppService.doGraphQL
    ↓
GraphqlProxyAppServiceImpl
    ↓
HTTP POST
    ↓
/graphql 或 /graphql-app/{appName}/graphql
```

## 二、这条证据解决了什么

已闭合：

```text
GraphQL 请求的 UDC 服务端代理入口
GraphQL Proxy Controller → AppService
GraphQL Proxy AppService → HTTP POST
请求上下文 Header 注入
GraphQL proxy URL 生成规则
```

这说明当前 fieldType 不是直接映射成某个 REST Controller，而是进入 GraphQL 请求/代理链。

更准确的模型是：

```text
fieldType
→ frontend loader
→ GraphQL request body
→ GraphqlProxyController
→ GraphqlProxyAppServiceImpl
→ GraphQL HTTP endpoint
→ GraphQL schema/resolver
→ 具体业务 AppService/Service
```

## 三、当前仍未闭合的核心三段

目前还没有在已有 Artifact 中找到精确字符串：

```text
udcMetaDataSelectFunctionNodeWithPageTreePost
udcMetaDataSelectFunctionNodeWithPageTreePostInputBody
selectFunctionNodeWithPageTree
FunctionNodeWithPageTree
```

因此以下边仍然是 `UNVERIFIED`：

```text
GraphQL field
→ GraphQL schema/resolver/handler

GraphQL resolver/handler
→ 具体 Java 业务 AppService method

具体 Java AppService method
→ Domain Service
→ 数据库 / OSS / Redis / 远程服务
```

当前不能把：

```text
udcMetaDataSelectFunctionNodeWithPageTreePost
→ PageMetadataQuery4SfAppService
```

或：

```text
udcMetaDataSelectFunctionNodeWithPageTreePost
→ UdcFunctionNodeService
```

写成 FACT。

## 四、关于候选 Java 服务的准确结论

### PageMetadataQuery4SfAppService

当前接口事实：

```java
SingleResponse<UdcApplicationMetaData4SfDto>
selectAppMetaDataByAppName(SingleRequest<String>)
```

它与目标 fieldType 的直接对应：

```text
UNVERIFIED
```

### DesignMetadataQueryAppService

当前接口事实中存在：

```java
selectPageMetadataList(SingleRequest<SearchDesignMetadataDto>)
```

但与目标 fieldType 的直接对应：

```text
UNVERIFIED
```

### UdcFunctionNodeService / UdcDynamicResourceServiceImpl

当前只由 UDC 5.3.517 静态索引确认类存在：

```text
UdcFunctionNodeService
UdcDynamicResourceServiceImpl
ResourcePermissionService
UdcPageInfoMetaDataEnhancedService
```

它们被目标 GraphQL field 调用：

```text
UNVERIFIED
```

## 五、运行态数据源当前状态

已有 Nacos 配置确认：

```text
UDC database: udc_test2
数据库类型：MySQL 配置证据
对象存储：OSS 配置证据
Redis：Lettuce / JSON serializer / expire-time 3600
```

但尚未沿目标 resolver/service 调用确认实际读取模式：

```text
Service → MySQL：UNKNOWN
Service → Redis：UNKNOWN
Service → OSS JSON：UNKNOWN
Service → 内部 RPC：UNKNOWN
Service → 多源合成：UNKNOWN
```

## 六、当前精确调用链

```text
前端 O(n)
    ↓ FACT
udcMetaDataSelectFunctionNodeWithPageTreePost
    ↓ FACT：loader body
GraphQLProxyRequestDto
    ↓ FACT：UDC runtime proxy
GraphqlProxyController.doGraphql(GraphqlProxyRequestDto)
    ↓ FACT_STATIC_BYTECODE
GraphqlProxyAppService.doGraphQL(SingleRequest<GraphqlProxyRequestDto>)
    ↓ FACT_STATIC_BYTECODE
GraphqlProxyAppServiceImpl.doGraphQL
    ↓ FACT_STATIC_BYTECODE
HttpClientUtil.post(targetGraphqlUrl, serializedRequest, propagatedHeaders)
    ↓ FACT_STATIC_BYTECODE
/graphql 或 /graphql-app/{appName}/graphql
    ↓ UNVERIFIED
GraphQL schema/resolver/handler
    ↓ UNVERIFIED
具体 Java AppService method
    ↓ UNVERIFIED
Domain Service
    ↓ UNVERIFIED
MySQL / OSS / Redis / RPC
    ↓ FACT_STATIC_FRONTEND_READ
response.content
    ↓ FACT_STATIC_FRONTEND_READ
functionNodes / pages[]
```

## 七、实现准入状态

目前还未达到你定义的四项准入条件：

```text
fieldType → Handler/Resolver：未闭合
Handler → Java Service：未闭合
Service → 实际数据源：未闭合
response.content → Java DTO：未闭合
```

所以暂不创建：

```text
udc.function_node.page_tree.read
PageTreeOperationContract
UdcPageTreeAdapter
UdcPageTreeApplicationService
```

这不是扩大抽象，而是保持“精确 Java 方法和数据源必须先接上”的事实门槛。

## 八、a49eacdd.js 独立状态

```text
a49eacdd.js = Resource UI handler 恢复任务
```

它不阻断本 GraphQL Dispatch 追踪，也不改变本轮主线。

## 九、下一条取证动作

继续查 GraphQL schema/resolver 的实际来源，优先顺序：

```text
1. UDC 5.3.517 服务器运行包中的 GraphQL schema/registry
2. GraphQL metadata / operation descriptor
3. GraphqlProxyRequestDto 字段和序列化内容
4. UDC GraphQL endpoint 日志
5. GraphQL schema introspection（只读）
6. Resolver/handler 字节码
```

重点只查：

```text
udcMetaDataSelectFunctionNodeWithPageTreePost
```

确认它最终对应的：

```text
resolver class
resolver method
Java AppService method
response DTO
```

然后继续：

```text
AppService
→ Domain Service
→ 实际数据源
```

## 当前唯一 Stop Point

```text
UDC PageTree GraphQL Dispatch Fact Closure
```

当前进度：

```text
前端 fieldType / payload / response：FACT
GraphQL Proxy Controller：FACT
GraphQL Proxy AppService：FACT
GraphQL HTTP POST 传输：FACT
GraphQL schema/resolver：UNVERIFIED
Java 业务方法：UNVERIFIED
Domain Service：UNVERIFIED
实际数据源：UNVERIFIED
Operation Contract：NOT_CREATED
```
