# UDC PageTree / FunctionNode 第一条事实调用链

状态：`PARTIAL / STATIC_CHAIN_CANDIDATE`

范围：优先闭合已有前端 readonly 调用 `udcMetaDataSelectFunctionNodeWithPageTreePost`。不把它命名为 Menu，不执行写操作。

## 1. 前端调用事实

来源：

```text
docs/audit/frontend/chunks/src_constants_design_page-type_ts-src_services_design_pag-93bb09.6494d14a.js
```

已确认调用：

```text
loader: a.wh.load
fieldType: udcMetaDataSelectFunctionNodeWithPageTreePost
paramsType: udcMetaDataSelectFunctionNodeWithPageTreePostInputBody
paramsKey: body
```

调用函数：`O(n)`。

参数：

```json
{
  "appId": "required",
  "hasAssociateApp": true,
  "params": {
    "urlType": "terminal when supplied",
    "pageType": "pageType when supplied"
  },
  "sort": {
    "orders": [
      {"direction": "ASC", "property": "createTime"}
    ]
  }
}
```

响应使用：

```text
result.content
```

同一查询上下文中观察到的内容结构：

```text
id
name
caption
uniqueKey
functionNodes
pages[]
```

`pages[]` 字段：

```text
appId
appName
caption
id
pageType
pageUrl
sourceType
urlType
fullName
relationGroupId
inApp
inParams
masterEntity
isDraftPage
```

当前前端证据等级：

```text
fieldType：FACT
input type：FACT
params key：FACT
参数结构：FACT（静态编译代码）
response.content：FACT（前端读取方式）
后端含义：UNVERIFIED
```

## 2. 当前后端候选事实

### 2.1 PageMetadataQuery4SfAppService

来源：

```text
docs/audit/modules/decompiled/udc-facade-5.3.517-PageMetadataQuery4SfAppService.java
```

确认接口只有：

```java
SingleResponse<UdcApplicationMetaData4SfDto>
selectAppMetaDataByAppName(SingleRequest<String> request)
```

结论：

```text
PageMetadataQuery4SfAppService 存在：FACT
它直接对应 udcMetaDataSelectFunctionNodeWithPageTreePost：未证明
```

不能因为名称包含 PageMetadata 就把它认定为该 fieldType 的后端实现。

### 2.2 DesignMetadataQueryAppService

来源：

```text
docs/audit/modules/decompiled/udc-facade-5.3.517-DesignMetadataQueryAppService.java
```

确认存在：

```java
selectPageMetadataList(SingleRequest<SearchDesignMetadataDto>)
```

以及 Entity/DTO/Agg 等元数据查询方法。

结论：

```text
设计元数据查询能力：FACT
与 FunctionNodeWithPageTree fieldType 的直接对应：UNVERIFIED
```

### 2.3 UdcFunctionNodeService / UdcDynamicResourceServiceImpl

来源：

```text
docs/audit/modules/targeted-code-index.json
```

确认类型出现在 UDC 5.3.517 运行时静态索引中：

```text
UdcFunctionNodeService
UdcDynamicResourceServiceImpl
ResourcePermissionService
UdcPageInfoMetaDataEnhancedService
```

当前仅能证明：

```text
相关运行时类存在：FACT
它们被该 fieldType 调用：UNVERIFIED
```

## 3. 数据源事实

### 3.1 Nacos / UDC 配置

来源：

```text
docs/audit/evidence/nacos-udc.yaml
docs/audit/evidence/nacos-test2-manifest.json
```

已确认：

```text
environment: test2
tenant: xiaozhua-test2
group: xiaozhua
dataId: udc
dataId: udc-app-yaml
database: udc_test2
storage-type: oss
ferryboat-storage-type: oss
frontend build URI: udc-app-runtime/build/app
frontend deploy URI: udc-app-runtime/deploy/app
```

说明：

```text
UDC 页面/运行态相关配置存在 OSS 存储配置
```

但尚未证明：

```text
FunctionNode page tree 的具体数据是否来自 OSS
具体 bucket/object key
Redis 是否参与该查询
数据库表/查询 SQL
```

### 3.2 已确认的相关存储类型

从现有配置可确认：

```text
UDC datasource database: udc_test2
数据库驱动/URL：MySQL JDBC URL（现有配置证据）
Redis：Lettuce，database 0，JSON serializer，expire-time 3600
对象存储：OSS
```

这些是运行配置事实，但不是 FunctionNode 查询的实际数据源调用证明。

当前数据源状态：

```text
数据库类型：FACT（配置）
具体 page-tree 表：UNKNOWN
OSS 参与 page-tree：UNKNOWN
Redis 参与 page-tree：UNKNOWN
```

## 4. 当前调用链状态

```text
前端 O(n)
  ↓ FACT
udcMetaDataSelectFunctionNodeWithPageTreePost
  ↓ FACT
udcMetaDataSelectFunctionNodeWithPageTreePostInputBody / body
  ↓ UNVERIFIED
GraphQL schema / resolver / handler
  ↓ UNVERIFIED
具体 Controller / AppService
  ↓ UNVERIFIED
UdcFunctionNodeService / PageMetadata service / other service
  ↓ UNVERIFIED
数据库 / OSS / Redis / remote service
  ↓ FACT（前端读取 envelope）
response.content
  ↓ FACT（字段观察）
functionNodes / pages[]
```

当前不能写成：

```text
fieldType → PageMetadataQuery4SfAppService
```

也不能写成：

```text
fieldType → UdcFunctionNodeService
```

因为目前缺少真实 resolver/handler 或服务字节码调用边。

## 5. 第一条能力的实现准入

按照当前要求，只有这一段闭合后才落代码：

```text
fieldType
→ schema/resolver/handler
→ service
→ 实际数据源
→ response DTO
```

当前准入状态：

```text
PageTree Operation Contract：NOT_CREATED
UdcPageTreeAdapter：NOT_CREATED
UdcPageTreeApplicationService：NOT_CREATED
```

原因不是继续扩大研究，而是后端入口和实际数据源尚未接上。现在创建实现会把候选类误当成事实。

## 6. a49eacdd.js 独立状态

```text
a49eacdd.js：仍为 Resource UI handler 恢复任务
```

它不再阻断当前 PageTree/FunctionNode 后端链路追踪。

当前两条线分开：

```text
PageTree/FunctionNode readonly：继续追后端
Resource 页面真实 handler：继续多源恢复，独立记录
```

## 7. 下一条取证动作

只继续追现有 `fieldType` 的后端实现：

```text
udcMetaDataSelectFunctionNodeWithPageTreePost
→ GraphQL field/schema 定义
→ resolver/handler
→ 目标 Java class/method
→ AppService 调用
→ Service 实现
→ DB/OSS/Redis/远程服务调用
```

优先使用已有 UDC 5.3.517 服务器 Artifact、反编译目录、运行日志和 Nacos 配置，不进行写操作。

## 当前 Stop Point

```text
UDC PageTree / FunctionNode Readonly Fact Chain Closure
```

完成标准：

```text
1. fieldType 后端入口确认
2. handler → service 调用边确认
3. 实际数据源确认
4. response.content DTO 确认
5. functionNodes/pages[] 来源确认
6. PageTree Operation Contract 建立
7. UdcPageTreeAdapter 建立
8. ApplicationService 建立
9. 本地组合测试通过
10. 真实 readonly PASS 或明确 BLOCKED
```

当前准确状态：

```text
前端 fieldType：FACT
前端参数：FACT
前端响应读取：FACT
后端入口：UNVERIFIED
Service 链：UNVERIFIED
数据源：PARTIAL / UNVERIFIED
Operation Contract：NOT_CREATED
Agent 实现：NOT_CREATED
真实 readonly：BLOCKED / UNVERIFIED
```
