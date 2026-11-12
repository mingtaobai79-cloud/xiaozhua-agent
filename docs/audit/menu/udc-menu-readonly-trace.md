# UDC Resource / Menu 第一条事实追溯

状态：`BLOCKED / STATIC_EVIDENCE_INCOMPLETE`

范围：UDC Resource / Menu readonly 第一条调用链。
版本基线：UDC captured frontend chunks + UDC 5.3.517 static artifact index。

## 当前已经确认的事实

### 1. Resource 页面入口

来源：

```text
docs/audit/frontend/chunks/src_app4Exposes_tsx.1714867c.js
docs/audit/frontend/udc-remoteEntry.js
```

确认：

```text
React route: /resource
lazy chunk: src_pages_udc_resource_index_tsx
built file: a49eacdd.js
```

当前本地证据目录没有 `a49eacdd.js` 真实字节。

### 2. Resource 前端 chunk 多源恢复结果

已按当前可访问的本地来源检查：

```text
<PATH>
<PATH>
<PATH>
<EVIDENCE_ROOT>
<USER_HOME>/...
<USER_HOME>/... Data
<USER_HOME>/... Data
```

结果：

```text
a49eacdd.js：NOT FOUND
src_pages_udc_resource_index_tsx：只在 remoteEntry / 路由索引中出现
浏览器 HAR：未找到
本地 source map：未找到
服务器访问日志：未找到
```

此前保存的前端入口事实只能证明：

```text
remoteEntry：已保存
manifest：已保存
部分相关 chunk：已保存
Resource 页面 chunk：未保存
```

### 3. RemoteEntry 中的构建映射

来源：`docs/audit/frontend/udc-remoteEntry.js`

确认映射：

```text
src_pages_udc_resource_index_tsx → a49eacdd.js
```

该映射证明 chunk 文件名，不证明 chunk 内容、页面 handler 或请求接口。

### 4. 已保存前端代码中的页面树/功能节点读取

来源：

```text
docs/audit/frontend/chunks/src_constants_design_page-type_ts-src_services_app-design_template_ts-src_services_design_pag-93bb09.6494d14a.js
```

确认：

```text
loader: a.wh.load
fieldType: udcMetaDataSelectFunctionNodeWithPageTreePost
paramsType: udcMetaDataSelectFunctionNodeWithPageTreePostInputBody
paramsKey: body
```

请求结构：

```text
appId
hasAssociateApp: true
params: {}
params.urlType = terminal       # terminal 存在时
params.pageType = pageType      # pageType 存在时
sort.orders = [{direction: ASC, property: createTime}]
```

响应使用：

```text
content
```

可见字段：

```text
id
name
caption
uniqueKey
functionNodes
pages[]
```

`pages[]` 可见字段：

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

当前状态：

```text
前端调用：TRACED
页面树/功能节点语义：TRACED
Resource/Menu 语义：UNKNOWN
```

不能直接升级为 `udc.menu.list`。

### 5. 页面信息读取候选

同一前端代码中确认：

```text
fieldType: udcPageInfoSearchNoPagePost
paramsType: udcPageInfoSearchNoPagePostInputBody
paramsKey: body
```

可见请求参数：

```text
appId
terminal
pageType
id
sort.orders
```

可见响应字段：

```text
id
name
caption
pageType
pageUrl
relationGroupId
urlType
sourceType
masterEntityIds
```

这条可以作为：

```text
Menu → Page / Route dependency read
```

但目前不是 Resource/Menu 主 operation 的事实证明。

### 6. 后端静态线索

来源：

```text
docs/audit/modules/targeted-code-index.json
docs/audit/modules/decompiled/manifest.json
```

已确认的相关类型：

```text
com.seeyon.udc.api.PageMetadataQuery4SfAppService
com.seeyon.udc.common.dto.PageInfoItemDto
com.seeyon.udc.common.dto.PageReferDto
com.seeyon.udc.common.dto.ApplicationRoleControlResourceDto
com.seeyon.boot.starter.udcrt.domain.service.UdcDynamicResourceServiceImpl
com.seeyon.boot.starter.udcrt.domain.service.UdcFunctionNodeService
com.seeyon.boot.starter.udcrt.domain.service.ResourcePermissionService
```

这些只是静态类型/服务线索，尚未形成：

```text
frontend operation
→ GraphQL schema/resolver
→ Controller/Handler
→ AppService/Service
→ DB/Redis/MinIO
→ response
```

### 7. Nacos/运行态已有事实

来源：

```text
docs/audit/evidence/nacos-test2-manifest.json
docs/audit/evidence/nacos-udc.yaml
docs/audit/evidence/nacos-udc-app-yaml.yaml
```

已确认：

```text
environment: test2
tenant: xiaozhua-test2
group: xiaozhua
dataId: udc
dataId: udc-app-yaml
UDC database name: udc_test2
frontend build URI: udc-app-runtime/build/app
frontend deploy URI: udc-app-runtime/deploy/app
frontDomain: http://lowcode-test2.example.com
```

这些事实说明 UDC 有前端构建/部署配置和运行态配置，但还不能证明：

```text
a49eacdd.js 的实际对象路径
Resource chunk 的实际部署目录
Resource chunk 是否来自 MinIO
Resource chunk 是否来自 Pod 文件系统
Resource chunk 是否经过 Nginx/Gateway
```

## 当前完整链路状态

```text
/resource 路由
→ a49eacdd.js
    BLOCKED：本地、缓存、source map、日志均未恢复
→ Resource 页面列表 handler
    UNKNOWN
→ Resource/Menu fieldType
    UNKNOWN
→ Gateway route/service
    UNKNOWN
→ 后端 Controller/Resolver
    UNKNOWN
→ DTO
    UNKNOWN
→ Service
    UNKNOWN
→ DB/Redis/MinIO
    UNKNOWN
→ response / 前端状态更新
    UNKNOWN
```

## 当前不能做的事

```text
不能把页面树接口命名为 udc.menu.list
不能创建 Resource/Menu Adapter
不能猜 Resource Controller
不能猜数据库表
不能猜 Redis key/TTL
不能猜 MinIO bucket/object
不能执行 Menu 写操作
```

## 当前唯一下一步

继续执行 `UDC Resource Frontend Fact Recovery`，但不再重复 DNS 请求。

优先寻找真实部署来源：

```text
1. UDC 前端构建产物目录
2. Nginx/Gateway 静态资源映射
3. UDC Pod/容器文件系统
4. 浏览器/WebView 缓存
5. manifest/source map/remoteEntry 衍生地址
6. Resource chunk 访问日志
```

恢复后只追：

```text
/resource
→ 首次列表加载
→ 列表 handler
→ fieldType / paramsType / paramsKey
→ payload
→ response fields
→ 前端状态更新
```

然后针对第一个确认的 readonly operation，立即追后端、运行态，并落对应 Agent 代码。

## 状态结论

```text
UDC / Resource-Menu：IN PROGRESS
/resource 路由：FACT
lazy chunk 映射：FACT
a49eacdd.js 真实字节：BLOCKED
页面树/功能节点读取：TRACED
页面信息读取：TRACED
Resource 页面真实操作：BLOCKED
Menu 语义：UNKNOWN
Operation Contract：NOT CREATED
Agent Adapter：NOT CREATED
真实 readonly 调用：BLOCKED
```

## Non-claims

```text
没有执行任何写操作。
没有修改数据库、Redis、MinIO 或 Nacos。
没有把页面树事实升级为 Menu 事实。
没有把后端类名升级为 Resource 调用链。
没有把历史 HTTP 200 观察升级为当前 live chunk 已恢复。
```
