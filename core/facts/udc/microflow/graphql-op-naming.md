# GraphQL op 名与类型名的生成规则

> 状态：VERIFIED_STATIC_BYTECODE（`boot-starter-graphql 5.3.358` 反编译）+ LIVE 交叉验证
> 取证：`docs/audit/modules/decompiled/graphql-starter/`

## 铁律

- **op 名不是 Java 方法名**，是元数据 `path + httpMethod` 算出来的。
- **类型名 = appName(camel) + DTO 全限定名，去掉所有非字母数字**。
- AppService 方法**只注册成 GraphQL，不暴露 REST**（探 9 条路径全 404）。
- 想读某个 DTO，**先算出 op 名**：拿到元数据里该方法的 path 即可。

## 1. op 名生成（`GraphQLProvider.pathToCamel`）

```java
String methodTypeName = GraphQLProvider.pathToCamel(
    methodDto.getPath() + "/" + methodDto.getHttpMethod().toLowerCase());
```

```java
private static String pathToCamel(String path) {
    path = path.replaceAll("\\{", "");          // 去掉路径参数花括号
    path = path.replaceAll("\\}", "");
    path = toCamelCase(path, false, '-', '/', '_');   // 首字母不大写
    path = path.replaceAll("[^A-Za-z0-9]", "");       // 去掉一切非字母数字
    path = path.replaceAll("Id$", "");                // 去掉结尾 Id
    path = path.replaceAll("IdGet$", "Get");
    path = path.replaceAll("SearchPost$", "Search");
    return path;
}
```

★ 注意顺序：先 `Id$` 再 `IdGet$`。
  `xxxIdGet` → 先不动（不是 Id 结尾）→ 再变 `xxxGet`。
  `xxxSearchPost` → 而不是 `xxxSearch`。

**验证案例（LIVE）**：

| 元数据 path | httpMethod | 算出的 op 名 | 实测 |
|---|---|---|---|
| `/udc/microflow/serviceList` | POST | `udcMicroflowServiceListPost` | ✓ 可用 |
| `/udc/microflow/searchApps` | POST | `udcMicroflowSearchAppsPost` | ✓ 可用 |
| `/udc/microflow/searchAppServiceByName` | POST | `udcMicroflowSearchAppServiceByNamePost` | ✓ 可用 |
| `/udc/microflow/disableNode` | POST | `udcMicroflowDisableNodePost` | ✓ 可用 |

⇒ 规则正确。**op 名可以正向算、也可以反向解**（去掉 `Post` 后缀即为 path）。

## 2. 类型名生成（`GraphQLTypeNameUtil.touchName`）

```java
public static String touchName(String dtoFullName, String appName, boolean isInput) {
    String s = appNameToCamel(appName) + getSimpleNameFromFullName(dtoFullName);
    if (isInput) s = s + "InputBody";
    return s.replaceAll("[^A-Za-z0-9]", "");
}
// getSimpleNameFromFullName 直接原样返回 fullName（名字与行为不符，注意）
```

**验证（LIVE 报错原文）**：

```
Field 'pageInfo' in type 'UdccomseeyonudcmicroflowdtodefinitionMicroFlowSubMfDto' is undefined
```

拆开看：

```
appName    = "udc"  → toCamelCase → "Udc"
dtoFullName= "com.seeyon.udc.microflow.dto.definition.MicroFlowSubMfDto"
拼接       = "Udccom.seeyon.udc.microflow.dto.definition.MicroFlowSubMfDto"
去非字母数字= "UdccomseeyonudcmicroflowdtodefinitionMicroFlowSubMfDto"   ✓ 完全一致
```

⇒ **看到 FieldUndefined 的类型名，可以直接反推是哪个 DTO**。

Input 类型再多一个 `InputBody` 后缀（如 `XXXInputBody`）。

## 3. 为什么 op 名 ≠ 方法名

`@AppServiceOperation` **只有中文 `value`，没有 op 名**：

```java
@AppServiceOperation(value="跟据ID查询微流程")
public SingleResponse<MicroFlowDefinitionDto> getMicroFlowDefinition(SingleRequest<Long> r)
```

op 名由**元数据**决定：

```java
// MetadataProxyService
public List<RestApiMetadataDto> selectRestApiMetadata(String appName) {
    SearchMetadataDto d = new SearchMetadataDto();
    d.setAppName(appName);
    Map map = this.metadataService.selectForMap(MetadataTypeEnum.RestApi, d);
    ...
}
```

`RestMethodMetadataDto` 提供 `getPath()` / `getHttpMethod()` / `getCaption()`。

⇒ 所以 `searchApps` / `searchAppServiceByAppName` 能对上方法名纯属巧合
  （path 恰好等于方法名）；`serviceList` / `disableNode` 就完全对不上。

⇒ **`serviceList` 等方法不在已反编译的 `MicroFlowAppService` 里**，
  而是由另一个 AppService（未反编译）以同一 `udcMicroflow` 前缀注册。

## 4. AppService 不暴露 REST

探 9 条路径、每条 4 种 body，全部 404：

```
/service/udc/microflow/getMicroFlowDefinition   404
/service/udc/microflow/definition               404
/service/udc/microflow/findById                 404
/service/udc/microflow/detail                   404
/service/udc/microflow/selectDetailsBySourceId  404
/service/udc/microflow/selectListByCondition    404
/service/udc/microflow/selectListByQuery        404
/service/udc/microflow/serviceList              404   ← 但 GraphQL 同名 op 可用
```

404 响应体里的 `path` 已去掉 `/service` 前缀（网关剥层）：

```json
{"status":404,"error":"Not Found","path":"/udc/microflow/serviceList"}
```

⇒ **AppService 只注册 GraphQL mutation，不建 Spring MVC mapping**。
  `GraphQLProvider.seeyonRest` 只是把 `{path, httpMethod}` 塞进
  `ThreadLocal` 的 `SeeyonSchema.addRest(...)`，用于内部转发，不是对外 REST。

## 5. 剩下的缺口：读 dataSchema（已确认不可达）

有 `dataSchema` 的 DTO 是 `MicroFlowDefinitionDto`，来自：

```
getMicroFlowDefinition(SingleRequest<Long>)        → SingleResponse<MicroFlowDefinitionDto>
selectDetailsBySourceId(SingleRequest<String>)     → ListResponse<MicroFlowDefinitionDto>
```

**用已验证的 op 名规则反向爆破（15 个候选 path × 2 种 method = 30 个 op 名），全部 FieldUndefined**：

```
/udc/microflow/definition              /udc/microflow/getMicroFlowDefinition
/udc/microflow/microFlowDefinition     /udc/microflow/definitionById
/udc/microflow/selectDefinitionById    /udc/microflow/selectById
/udc/microflow/selectDetailsBySourceId /udc/microflow/detailsBySourceId
/udc/microflow/selectBySourceId        /udc/microflow/detail
/udc/microflow/get                     /udc/microflow/find
/udc/microflow/schema                  /udc/microflow/getSchema
/udc/microflow/loadDefinition                      （× POST/GET）
⇒ 命中 0 / 30
```

⇒ **这两个方法根本没进 RestApi 元数据**，所以没有 GraphQL op。
  要么它们是从未被调用的死代码，要么只走内部 Dubbo 调用。

**所以当前边界（已确认，不再尝试）**：

| 能力 | 通道 | 状态 |
|---|---|---|
| 读流程列表 + state | `udcMicroflowServiceListPost` | ✅ 可用 |
| 读流程元信息（path/method/type/trigger/hasInput/hasOutput） | 同上 | ✅ 可用 |
| 读节点 dataSchema | **无接口** | ❌ 不可达 |
| 写（create/update/checkSchema） | REST | ✅ 可用 |

★ 读回 schema 的实际需求是「验证平台是否改写了 schema」（presetData 回填等），
  这个需求目前只能用 DB 做，属于**已知缺口**，不作为交付路径。
  生成器写进去什么，就是什么 —— 需要比对时再单独取证。
