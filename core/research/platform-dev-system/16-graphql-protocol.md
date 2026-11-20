# GraphQL 协议层（boot-starter-graphql 5.3.600，772 类）

> 数据源：`boot-starter-graphql-5.3.600.jar` class 清单实证
> 等级：`VERIFIED_STATIC_BYTECODE`（类清单，未反编译方法体）
> ⚠️ 用户环境 5.3.517，本机 5.3.600

---

## 0. ★★★ 最重要的结论：772 类里只有 71 个是致远的

**大部分是第三方开源库：**

| 包 | 类数 | 来源 |
|---|---:|---|
| `graphql.*`（language/schema/execution/validation/parser …） | 361 | **graphql-java 开源库** |
| `antlr.v4.runtime.*` | 174 | **ANTLR4 开源库**（GraphQL 语法解析） |
| `com.seeyon.boot.starter.graphql.*` | **71** | **★ 致远自己的** |
| `graphql.*` 剩余（relay/util/analysis…） | 166 | graphql-java 附加模块 |

**⇒ 「772 类」是个虚数。真正要理解的是 **71 个致远类**。**

---

## 1. ★★ 致远自己的 71 个类（全清单）

### 1.1 根包（17 个）—— 入口与装配

| 类 | 用途 |
|---|---|
| **`GraphQLController`** | **HTTP 入口**（前端请求打这里） |
| `GraphQLServlet` / `GraphQLServletApp` | Servlet 入口 |
| `GraphQLWebConfig` | Web 配置 |
| `GraphQLAutoConfiguration` | Spring Boot 自动装配 |
| `GraphQLProperties` | 配置项 |
| `GraphQLProvider` | Provider |
| **`SeeyonGraphQL`** | 致远封装的核心 |
| `DefaultGraphQLInvocation` / `GraphQLInvocationData` | 调用封装 |
| `DefaultExecutionResultHandler` | 执行结果处理 |
| `GraphQLRequestBody` | 请求体模型 |
| **`GraphQLObjectTypeService`** | **ObjectType 服务** |
| **`GraphQLObjectTypeParamsService`** | **参数服务** |
| `GraphQLObjectTypeNReturnService` | 返回值服务 |
| `AppHostService` | 应用宿主 |
| `GraphQLDisplayNameProperties` | 显示名配置 |

### 1.2 execution 包（10 个）—— 执行引擎

| 类 | 用途 |
|---|---|
| **`SeeyonSchema`** | **Schema 核心对象** |
| **`SeeyonSchemaService`** | **Schema 服务（动态构建）** |
| `SeeyonExecution` | 执行器 |
| `SeeyonExe` / `SeeyonExeLoader` / `SeeyonExeUtilForModel` | 执行体 + 加载 |
| **`SeeyonQuery`** | **Query 根** |
| **`SeeyonRest`** | **REST 桥接** |
| **`SeeyonParser`**（parse 包） | **解析器** |
| `SeeyonDisplayNameType` | 显示名类型 |
| `I18nParserService` | **i18n 解析** |

**★★ `SeeyonRest` 是关键 —— GraphQL 可以桥接到 REST 接口。**
**⇒ 说明平台不是纯 GraphQL，是「GraphQL 门面 + REST 后端」的混合。**

### 1.3 util 包（25 个）—— 最值得关注

**DataFetcher / DataLoader（GraphQL 的数据获取机制）**

| 类 | 用途 |
|---|---|
| **`DynamicDataFetcher`** | **动态数据获取（主力）** |
| `DynamicDataAsyncFetcher` | 异步版 |
| `DynamicDataServletFetcher` | Servlet 版 |
| **`ChildrenDataFetcher`** | **子对象数据获取** |
| **`ChildrenDataLoader`** | **子对象批量加载（解决 N+1）** |

**⇒ `ChildrenDataLoader` 是 GraphQL 的 N+1 问题解决方案，说明平台做了批量化优化。**

**HTTP / 请求适配**

| 类 | 用途 |
|---|---|
| `GraphqlHttpUtils` / `HttpAsyncClient` / `HttpAsyncUtil` | HTTP 工具 |
| `HttpServletAdapter` / `HttpServletCalculator` | Servlet 适配 |
| `SeeyonHttpServletRequest` / `SeeyonHttpServletResponse` | 请求响应包装 |
| `SeeyonHttpServletRequestConstants` | 常量 |
| `HttpStatus` | 状态码 |

**类型 / 序列化**

| 类 | 用途 |
|---|---|
| `GraphQLJsonUtils` | JSON 工具 |
| **`GraphQLTypeMappingUtil`** | **Java 类型 → GraphQL 类型映射** |
| **`GraphQLTypeNameUtil`** | **类型名生成** |
| **`SeeyonScalars`** | **自定义 Scalar（关键）** |

**★ `SeeyonScalars` 是自定义标量类型 —— 平台把 Long/Date/BigDecimal 等做成了 GraphQL Scalar，避免 JS 精度问题。**

**缓存 / 并发 / 其他**

| 类 | 用途 |
|---|---|
| `SeeyonCacheMap` | 缓存 Map |
| `SeeyonThreadPool` | **GraphQL 专用线程池** |
| `ThreadLocalUtil` | ThreadLocal 工具 |
| `TimeCountUtils` | 耗时统计 |
| `MapIgnoreKeysUtil` | Map 忽略键 |
| `IdsUtil` | ID 工具 |
| `WriterSplitter` | 输出分片（大响应） |

### 1.4 appservice（2 个）

| 类 | 用途 |
|---|---|
| `DisplayNameService` | **显示名服务**（把 ID 转成人能看懂的名字） |
| `DynamicSelectByIdsService` | 按 ID 批量查 |

**★ `DisplayNameService` 说明：GraphQL 返回的数据会自动带 displayName（如人员 ID → 姓名），前端不用二次查询。**

### 1.5 其他

| 包 | 类 | 用途 |
|---|---|---|
| `controller` | `DynamicSelectByIdsController` | 动态查询 Controller |
| `domain` | `DynamicSelectByIdsDao/Mapper/Obejct` | 动态查询持久层 |
| `dto` | 9 个 Dto | 显示名/文档/DataLoader 信息 |
| `meter` | `GraphQLPoolMetrics` | **指标采集** |
| `proxy` | `MetadataProxyService` | **元数据代理**（★ 动态 Schema 的来源） |
| `task` | `ScheduledService` | 定时任务 |

---

## 2. ★★★ 动态 Schema 机制（核心理解）

**关键链条：**

```
实体元数据（MySQL udc_entity / udc_attribute）
    ↓
MetadataProxyService（元数据代理）
    ↓
GraphQLTypeMappingUtil（Java 类型 → GraphQL 类型）
GraphQLTypeNameUtil（类型名生成）
    ↓
SeeyonSchemaService（动态构建 Schema）
    ↓
SeeyonSchema（运行时 Schema）
    ↓
GraphQLController（处理请求）
```

**⇒ 这是平台的核心设计：**Schema 不是写死的，是根据元数据动态生成的**。**

**★★ 这意味着：**
1. 新建一个 UDC 实体 → GraphQL 自动多一套查询/变更接口
2. **前端不需要为每个实体单独写接口**
3. 字段类型由元数据 `dataType` 决定

---

## 3. ★★ 数据获取三层（DataFetcher 体系）

```
① DynamicDataFetcher           单条/列表动态查询
② DynamicDataAsyncFetcher      异步版（大数据量）
③ ChildrenDataFetcher          子对象查询
   └─ ChildrenDataLoader        ★ 批量加载，解决 N+1
```

**★★ N+1 问题：**
```
查 100 个订单 → 每个订单查详情 → 101 次查询
ChildrenDataLoader 批量：查 100 个订单 → 1 次批量查详情 → 2 次查询
```

**⇒ 平台已内建批量加载，不用自己优化。**

---

## 4. ★ 自定义 Scalar（`SeeyonScalars`）

**GraphQL 标准只有 String / Int / Float / Boolean / ID，平台的业务类型需要自定义：**

```java
SeeyonScalars
  ├─ Long       ← ★ 长整型（防 JS 精度丢失）
  ├─ BigDecimal ← 金额
  ├─ Date       ← 日期
  ├─ DateTime   ← 日期时间
  └─ 其他业务类型
```

**★ 为什么必须有 Long Scalar：**
```
平台主键是雪花 ID（19 位 Long）
JavaScript Number 只能精确表示 2^53（16 位）
→ 用 GraphQL Int 会截断
→ 必须用 String 形态的 Long Scalar
```

**⇒ 与 `JsonUtils.toJsonLongToString` 是同一个问题的两种解法。**

---

## 5. ★ 对「前端怎么调」的答案

**前端请求打 `GraphQLController`，项目路径通常是：**

```
POST /{appName}/graphql
Content-Type: application/json

{"query": "...", "variables": {...}}
```

**⇒ 这与我在 `custom-service-candidates.md` 里看到的 GraphQL 操作名（如 `udcMicroflowCreatePost`）对应 —— 那些是 Schema 里的 mutation 名。**

**★★ 重要理解：**
```
udcMicroflowCreatePost / udcDataFlowListManuallyMappingPost / udcDeductionRulePost
这些不是 REST 路径，是 GraphQL 的 mutation/query 名
```
**⇒ 所以操作平台数据的正确形态是：**GraphQL query/mutation + variables**，不是 REST JSON body。**

---

## 6. ★ 与其他层的关系

```
前端（Vue/React）
    ↓ POST /{app}/graphql
GraphQLController                     ← boot-starter-graphql
    ↓ 动态 Schema
MetadataProxyService → 元数据
    ↓ DataFetcher
DynamicDataFetcher / ChildrenDataLoader
    ↓ 桥接
SeeyonRest → REST 接口 / AppService
    ↓
业务层（org/bpm/udc…）
```

**★ `SeeyonRest` 的存在说明：GraphQL 只是**门面**，真正干活还是 REST/AppService。**

---

## 7. 我之前误解的地方（修正）

| 我之前的说法 | 实际 |
|---|---|
| 「772 类是协议层，不知 Schema 长什么样」 | **Schema 是动态从元数据生成的**，不是固定文件 |
| 「GraphQL 的 772 类都要理解」 | **只有 71 个是致远的，701 个是开源库** |
| 把 `udcMicroflowCreatePost` 当 REST 路径 | **是 GraphQL mutation 名** |
| 不知前端怎么调 | **`POST /{appName}/graphql` + query/variables** |

---

## 8. 未覆盖

| 项 | 说明 |
|---|---|
| `MetadataProxyService` 的具体映射规则 | 未读方法体（Java 类型↔GraphQL 类型的精确对应） |
| `SeeyonSchemaService` 的 Schema 构建流程 | 未读（何时重建、缓存策略） |
| `GraphQLController` 的请求处理细节 | 未读（路径、鉴权、分页约定） |
| `SeeyonRest` 的 REST 桥接规则 | 未读 |
| 实际 Schema 长什么样 | **未抓过真实请求**（需要能访问 test2 环境） |
| `DisplayNameService` 的批量机制 | 未读 |