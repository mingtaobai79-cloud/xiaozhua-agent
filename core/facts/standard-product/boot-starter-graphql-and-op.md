# boot-starter-graphql：GraphQL 端点、op 注册与调用

## Capability

**平台 GraphQL 的服务端全在 `boot-starter-graphql`；客开要做的只有两件事：**
①按模块打到正确端点（`/service/{module}/graphql`）；②让自己的 AppService 被注册成 op。
op 名生成规则见 `udc/microflow/graphql-op-naming.md`（本格不重复）。

## Version

`boot-starter-graphql` 5.3.600（jar 在盘，javap 全量抽取）。

## ★ 一、端点（LIVE 实测，2026-11-22）

```
POST https://<host>/service/udc/graphql       body {query, operationName, variables}
     → 200 {"traceId":"…","data":{...}}

POST https://<host>/service/graphql
     → 200 {"status":3,"code":"server_404","message":"graphql 服务不存在，请重启服务或重新发布应用后再试！"}
```

⇒ **端点按模块前缀区分**（`/service/udc/*` 属于 udc 模块），不存在全局 `/service/graphql`。
请求体就是三个字段：

```java
class GraphQLRequestBody { String query; String operationName; Map<String,Object> variables; }
```

## 二、错误码判读

```
GraphQL_3000  GraphQL未生成接口:<name>     op 名不对 / 该 AppService 没被注册
server_404    graphql 服务不存在          模块前缀错，或该模块应用未发布
BOOT_0000     平台层成功（业务结果另看 data）
```

★ `200 + traceId` 只代表**请求进了 GraphQL 层**，业务失败照样 200。

## ★ 三、op 是怎么被注册的（决定「接口找不到」）

```java
// GraphQLProvider：schema 由元数据生成，不是手写
void run(ListResponse<RestApiMetadataDto>, ListResponse<DtoMetadataDto>);
void run(ListResponse<RestApiMetadataDto>, ListResponse<DtoMetadataDto>,
         ListResponse<EntityMetadataDto>, SingleResponse<ServiceMetadataDto>);
void run(String appName, ...);                    // 按应用构建
GraphQL graphQL();                                // 全局 schema
GraphQL graphQL(String appName);                  // 应用级 schema
void removeApp(String appName);
Object refresh(String, String);                   // 运维口：刷新
Object getDoc(String, String);                    // 运维口：取文档
```

调用方（HTTP）：

```java
// GraphQLController（@RestController，class 级 @RequestMapping("/")）
Object graphqlPOST(GraphQLRequestBody body);
Object dynamicFormPOST(String path, GraphQLRequestBody body);
Object refresh(String, String) / cacheClear(String, String) / getDoc(String, String);
```

执行层：

```java
SeeyonGraphQL.execute(graphql.ExecutionInput, String appName);   // 单点执行入口
GraphQLInvocationData(query, operationName, variables, resp, req[, schemaQuery])
```

## 四、从 Java 里调平台 GraphQL

```java
// 方式一：HTTP（跨应用最稳，跟我们抓包一致）
HttpClientUtil.postJson(host + "/service/udc/graphql",
        "{\"query\":\"query($id:Long!){ udcMicroflowFindByIdGet(id:$id){ id name state } }\","
      + "\"variables\":{\"id\":123}}", cookie);

// 方式二：同 JVM 内直接执行（省一次 HTTP）
ExecutionResult r = seeyonGraphQL.execute(
        ExecutionInput.newExecutionInput().query(q).variables(vars).build(), "udc");
```

## Side Effects

- `refresh` / `cacheClear` 会重建 schema 缓存，生产上批量调用会抖。
- `removeApp(appName)` 会把整个应用的 op 摘掉，慎用。
- GraphQL 全量 schema 很大（本应用实测 node-tree 响应 205 KB 级），别在循环里 `getDoc`。

## Known Constraints

1. **AppService 注册的是 GraphQL，不是 REST**：同一接口 9 条 REST 路径实测 404（`udc/microflow/graphql-op-naming.md` 已记）。
2. op 名 ≠ 方法名，是 `pathToCamel(path + "/" + httpMethod.toLowerCase())` 推导出来的；
   拿不准就先用 `getDoc` 查 schema，别猜。
3 错误 `GraphQL_3000` 有两种成因：op 名写错，或该 AppService 没被元数据登记 —— 先查后者。
4. `variables` 里的类型要跟 schema 对齐（`Long!` vs `String!`），类型不符报的是 GraphQL 校验错，不是业务错。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `/service/udc/graphql` 可用（200 + traceId + `GraphQL_3000`） | 2026-11-22 单发实测 | LIVE |
| `/service/graphql` → `server_404 graphql 服务不存在` | 同上 | LIVE |
| `GraphQLRequestBody` 3 字段 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `GraphQLController` 5 入口（graphqlPOST/dynamicFormPOST/refresh/cacheClear/getDoc） | 同上 | VERIFIED_STATIC_BYTECODE |
| `GraphQLProvider` schema 由 4 类元数据驱动 | 同上 | VERIFIED_STATIC_BYTECODE |
| `SeeyonGraphQL.execute(ExecutionInput, appName)` | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 端点与错误码 LIVE（两条对照）
- ✅ 服务端 5 个入口 + 4 个元数据入参可逐字复核
- ⚠️ 未验证：`dynamicFormPOST` 的真实用途（无调用样本）

## 给 Agent 的判据

```
要调平台接口        → POST /service/{module}/graphql，body 三字段
接口 404 server_404 → 模块前缀错 / 应用没发布，不是 op 名问题
GraphQL_3000        → op 未生成：先确认 AppService 已登记元数据，再核对 op 名规则
要查有哪些 op       → GraphQLController.getDoc 或抓前端请求
要在 Java 内部执行   → SeeyonGraphQL.execute(ExecutionInput, appName)
改完元数据不生效     → refresh / 重新发布应用
```
