# REST/GraphQL 暴露机制（后端权威，字节码实证）

**证据级**：`VERIFIED_STATIC_BYTECODE`
**证据源**：
- `boot-starter-scanner-5.3.358.jar` → `com.seeyon.boot.starter.scanner.MetadataScanner`（CFR）
- `boot-starter-web-5.3.358.jar` → `com.seeyon.boot.starter.web.filter.AppContextFilter`（CFR）
- `boot-core-5.3.358.jar` → `com.seeyon.boot.annotation.{RestApi,AppService,AppServiceOperation}`（CFR）
- `boot-starter-graphql-5.3.358.jar` → `GraphQLProvider` / `proxy.MetadataProxyService`（CFR）

## 1. 结论（本轮核心，含对上轮假设的证伪）

**udc-web 的 54 个 Controller 不是唯一暴露面。** Spring 只认 @RestController + @RequestMapping；
所有这类类（跨全部构件）经**同一台扫描器** MetadataScanner 汇聚成运行期元数据，
GraphQL op 再从该元数据派生。因此：

```
GraphQL op 面 = 全应用（全构件）所有 @RestApi Controller × 方法
              ≠ udc-web 一个构件的 674 个方法（更不等于旧记的 657）
```

### 1.1 完成量化：674 个 mapping 端点中 **666** 个真正进 op 面（本轮新增，字节码实证）

`MetadataScanner#collectRestMetadata` 的守卫是 `if (restApi == null || op == null) continue;`
（第 74-75 行，见下 §2 代码摘录）—— **类级 `@RestApi` 与方法级 `@RestApiOperation` 缺一不可**。
本条此前只是文字引用，本轮用独立 class 文件解析器（直读常量池 + 方法表，不经 javap 文本）
对 `udc-web-5.3.517.jar` 全量量化：

| 分类 | 数 | 说明 |
| --- | --- | --- |
| 带 HTTP mapping 注解的端点 | **674** | 契约 `_api_full.json` 的总量 |
| 其中**真正进 op 面** | **666** | 类级 `@RestApi` ∧ 方法级 `@RestApiOperation` |
| 排除：类级无 `@RestApi` | 6 | **`ParameterController` 全部**（该类字节码 `class_anns` 为空，唯一一个无类级注解的 Controller） |
| 排除：方法级无 `@RestApiOperation` | 2 | `UdcFileController.download` / `.metadataDownload` |

⇒ 契约 674 是**方法级 REST 契约**的权威量；**op 面**是 666。两者口径不同，不可混用。
（`ParameterController` 的 6 条仍是有 mapping 的真实 handler，只是不经 `@RestApi` 暴露机制；
故 674 作为「REST 契约」是对的，作为「GraphQL op 面」则高估 8 条。）

### 1.1 证伪：@AppService 不是第二套 REST 暴露机制

上一轮把未归位 op 归因于「@AppService / @AppServiceOperation 的第二套暴露机制」。**不成立**：

- `boot-starter-appservice-5.3.358.jar` **全 41 个类无反编译到任何 HTTP 映射**：
  - `AppServiceAutoConfiguration`：注册 `AppServiceBeanPostProcessor` + AOP advisor（事务/日志/幂等）
  - `AppServiceBeanPostProcessor#postProcessBeforeInitialization` → `appServiceMethodInterceptor()`
    → `AppServiceMethodInterceptor.getInstance().register(method)`（**业务切面注册**，非 RequestMapping）
  - 全包无 `@RequestMapping` / `@GetMapping` / `@PostMapping` / `HandlerMapping`
- `@AppServiceOperation.value()` 是**中文操作名**（如 获取沙箱应用角色），不是路径
- `boot-starter-web` 的 `ComponentDynamicRegister` 实现只有 `ControllerDynamicRegister`
  （模块热插拔重扫 `RequestMappingHandlerMapping.detectHandlerMethods`），与 AppService 无关

> `AppServiceBeanPostProcessor` 内的次序断言是「为保证 @FacadeService 正确提供能力，
> 需要保证 dubbo / facade / aop 三个 BPP 的相对顺序」—— 是**次序约束**，不是路由。
> @AppService 的方法不因此变成 HTTP 端点。

## 2. 真实机制：一台 MetadataScanner，两条并列分支

`MetadataScanner#collectMetadataByClass`（第 556 行起，本轮逐行核对）：

```java
Map<MetadataTypeEnum, Map> collectMetadataByClass(String appName, ...,
        List<Class> restClassList, List<Class> appServiceClassList, ...) {
    // 分支一：@RestApi -> RestApiMetadataDto / RestMethodMetadataDto
    if (oldVersionDynamicOrNormalApp)
        collectRestMetadata(appName, restClassList, dtoClassList, enumClassList, restApiMetadataMap);
    else
        collectDynamicRestMetadata(restClassList, ...);
    // 分支二：@AppService -> AppServiceMetadataDto（独立 map，不进 GraphQL）
    collectAppServiceMetadata(appName, appServiceClassList, dtoClassList,
                              appServiceMetadataMap, openApiMetadataMap);
    result.put(MetadataTypeEnum.RestApi, restApiMetadataMap);
}
```

| 维度 | 分支一：@RestApi | 分支二：@AppService |
| --- | --- | --- |
| 类注解 | @RestApi(TYPE) | @AppService(TYPE)，元注解 @Service @Primary |
| 方法注解 | @RestApiOperation | @AppServiceOperation |
| 路径来源 | RequestMappingHandlerMapping.getHandlerMethods() 的 mapping.getPatternsCondition() | **无 HTTP 路径**，只收方法签名/DTO |
| 元数据类型 | RestApiMetadataDto | AppServiceMetadataDto |
| 进 GraphQL op 面 | 是（GraphQLProvider#addMethod） | 否 |

**collectRestMetadata 路径提取（权威，第 1368 行起）**：

```java
RequestMappingHandlerMapping handlers = ...getBean("requestMappingHandlerMapping");
Map handlerMethods = handlers.getHandlerMethods();          // Spring 实际已注册路由
for (entry : handlerMethods.entrySet()) {
    RequestMappingInfo mapping = entry.getKey();
    HandlerMethod restMethod = entry.getValue();
    RestApi   restApi = controller.getAnnotation(RestApi.class);
    RestApiOperation op = restMethod.getMethodAnnotation(RestApiOperation.class);
    if (restApi == null || op == null) continue;             // 两个注解缺一不可
    String path = mapping.getPatternsCondition().getPatterns().iterator().next();
    if (Apps.isMonolithic() && BaseComponentController.class.isAssignableFrom(controller) && appName != null)
        path = path.replace("/a9/", "/" + appName + "/");     // 单体应用前缀改写
    if (SystemEnvironment.isHostSandbox())
        path = path.replace("/app-sandbox/", "/" + appName + "/");  // 宿主沙箱前缀改写
    restMethodDto.setPath(path);
    restMethodDto.setHttpMethod(...RequestMethod...name());
}
```

> 关键：**path 取自 Spring 实际注册表**，不是从注解字面量拼的。任何构件只要有
> @RestController + @RequestMapping 且标了 @RestApi/@RestApiOperation，都会进 op 面。
> 量化见 §1.1：udc-web 674 个 mapping 端点中 **666** 满足双注解（`ParameterController` 6 + `UdcFileController` 2 不满足）。

## 3. GraphQL op 面是元数据的下游，按 appName 拉取

`GraphQLProvider#addMethod` → `metadataProxyService.selectRestApiMetadata(appName)`
→ `metadataService.selectForMap(MetadataTypeEnum.RestApi, {appName})`。

即「op 面按**应用**维度查询，而非构件维度」。所以 93 个未归位 op 只说明
**它们不属于 udc-web 构件**，不能说它们「不存在」或「无构件可归」。

## 4. 对上轮负面结论的更正（诚实标注）

上一轮记录：「**全仓 572 jar 逐 class 字节搜索，无任何 jar 含这些域的 REST 路径字面量**」。

**该结论的搜索域不成立**：当时扫描根是 `<MAVEN_REPO>/com/seeyon`（本地仓库，本轮实测 **1518** 个 jar），
而 93 op 的归属构件（udc-portal / udc-cdpbi / udc-upgrade / udc-affair / udc-app-common /
udc-m5 / udc-user / udc-bpm / udc-cip / boot-starter-sandbox）**不在本地仓库**——
本地 `com/seeyon` 下不存在这些 artifact（`ls com/seeyon | grep -i udc` 仅 17 项，无 portal/cdpbi/sandbox）。

正确表述：**这些构件只存在于 test2 pod 的 `/app/udc-assemble.jar` 的 `BOOT-INF/lib/` 内**，
本地缺件是事实源缺口，不是「不存在」。

本轮对本地 1518 个 jar 再跑一次子域字面量扫描（确认性负面证据，`/d/software/hermes/cache/scratch`）：

| 子域字面量 | 本地 1518 jar 命中 |
| --- | --- |
| `udc/portal/portal-space` | 0 |
| `udc/form-upgrade` | 0 |
| `udc/page-component` | 0 |
| `udc/custom-data-type` | 0 |
| `udc/page-admin` | 0 |
| `udc/affair` | 0 |
| `udc/excel-search` | 0 |
| `udc/cdp-data-report` | 0 |
| `udc/ctp-manager` | 0 |
| `udc/file-download` | 0 |
| `udc/env` / `udc/pinyin` | 0 |
| `udc/sandbox` | 5（`AppContextFilter` 3 版 + udc-web `SandboxController`/`UdcSandBoxLogController`，均为已知） |

> 注：`udc/expression`（100）、`udc/message`（30）命中是 `udc-biz` 的模板/DTO 类（如
> `autocode/template`、`udc/message/*Message`），**不是 REST 路径**，不计入归位证据。
> 这组 0 命中**不证明不存在**，只证明本地仓库不含这些构件 —— 与上表 pod 侧命中互为对照。

## 5. 本轮归档：pod 侧字节扫描的 artifact 级命中（上一轮产出）

来源：`<HERMES_HOME>/cache/scratch/probe99/podscan_out.txt`（pod 内 blob 扫描，覆盖 8 个候选构件）。
12 条 `MATCH|片段|jar|次数` 全部可映射到未归位名单中的 op：

| 命中片段 | 构件（pod） | 对应 op |
| --- | --- | --- |
| check-all-status | boot-starter-sandbox-5.3.289 | udcSandboxClientCheckAllStatusGet |
| check-all-task | boot-starter-sandbox-5.3.289 | udcSandboxClientCheckAllTaskGet |
| clean-restart-app | boot-starter-sandbox-5.3.289 | udcSandboxAppCleanRestartAppPost |
| clean-restart-by-app | boot-starter-sandbox-5.3.289 | udcSandboxAppCleanRestartByAppPost |
| config-all-tenant | boot-starter-sandbox-5.3.289 | udcSandboxTenantConfigConfigAllTenantGet |
| get-app-limit | boot-starter-sandbox-5.3.289 | udcSandboxSystemConfigGetAppLimitGet |
| sandbox-log-url | boot-starter-sandbox-5.3.289 | udcSandboxClientSandboxLogUrlPost |
| start-by-app | boot-starter-sandbox-5.3.289 | udcSandboxAppStartByAppPost（及 CleanRestart 系列） |
| get-report-list | udc-cdpbi-5.3.517 | udcCdpDataReportGetReportListPost |
| space-save-copy | udc-portal-5.3.517 | udcPortalPortalSpaceSpaceSaveCopyPost |

### 5.1 反向规则复算（9/9 精确命中）

| 推定路径 | 方法 | 规则产出 | 名单 op |
| --- | --- | --- | --- |
| /udc/sandbox/app/start-by-app | POST | udcSandboxAppStartByAppPost | 一致 |
| /udc/sandbox/app/clean-restart-by-app | POST | udcSandboxAppCleanRestartByAppPost | 一致 |
| /udc/sandbox/client/check-all-status | GET | udcSandboxClientCheckAllStatusGet | 一致 |
| /udc/sandbox/client/check-all-task | GET | udcSandboxClientCheckAllTaskGet | 一致 |
| /udc/sandbox/tenant-config/config-all-tenant | GET | udcSandboxTenantConfigConfigAllTenantGet | 一致 |
| /udc/sandbox/system-config/get-app-limit | GET | udcSandboxSystemConfigGetAppLimitGet | 一致 |
| /udc/sandbox/client/sandbox-log-url | POST | udcSandboxClientSandboxLogUrlPost | 一致 |
| /udc/cdp-data-report/get-report-list | POST | udcCdpDataReportGetReportListPost | 一致 |
| /udc/portal/portal-space/space-save-copy | POST | udcPortalPortalSpaceSpaceSaveCopyPost | 一致 |

> 证明：op 命名规则对**非 udc-web 构件**同样成立（规则属 boot-starter-graphql 的通用行为），
> 故归属判定的右端可跨构件复用。

### 5.2 宿主沙箱前缀（AppContextFilter 路由字面量）

`AppContextFilter#ignoreIntercept`（第 183 行）断言三条 bypass 字面量，同时给出沙箱子域路由基：

```
/app-sandbox/sandbox/server/download-war
/udc/sandbox/flexible/download-war
/udc-assemble/sandbox/flexible/download-war
```

结合 collectRestMetadata 的 isHostSandbox() 分支
（`path.replace("/app-sandbox/", "/" + appName + "/")`）→ 沙箱域名在**宿主沙箱态**下会被改写成应用名前缀；
udc-assemble 是独立装配件的路由基。

### 5.3 前端域级归属（上一轮产出）

`op_frontend_owner.json` + `op_domains.json`：99 op（缺陷修复后重算为 93）已全部按 bundle chunk 目录（≈ 原源码路径）归位。
其中 **48 个为 store-only**（只在 `src_redux_store_ts` 定义、无独立页面 chunk），
其余分布于 sandbox-pages / portal-space / form-upgrade / page-component / customtype / cdp-data-report 等。

### 5.4 前端 bundle 内 REST 路径字面量（本轮新增，本地可复核）

对 `udc-frontend/unpacked`（13MB）grep `/udc/*` 与 `/udc-runtime/*` 字面量，得 34 条；
与未归位 op 名单交叉命中 21 个 op 的调用点，关键锚点：

```
/udc/sandbox/app/search                    <- udcSandboxSandboxAppsByConditionPost 等
/udc/sandbox/system/config/is-deploy-war   <- sandbox 应用状态族
/udc/application/search/front-detection    <- udcSandboxAppStartByAppPost 等
/udc-sandbox/*  (app-sandbox)              <- 沙箱装配件
```

> 说明前端确实直连这些子域路径；与 §5 的构件级命中互为独立证据。

## 6. 尚未闭环（诚实边界）

| 项 | 状态 | 缺口 |
| --- | --- | --- |
| 机制本体（§2/§3） | STATIC_BYTECODE 已证 | — |
| 12 条 artifact 级命中 | pod blob 扫描（上一轮产出） | 只覆盖 8 个候选构件，非全量 |
| 未归位 op（93，余 66 UNVERIFIED）全量 artifact 级归属 | 部分 | 余量需 pod 侧 BOOT-INF/lib 全量构件扫描 |
| pod 内构件的本地副本 | 缺 | 本轮 10.0.0.1:22 不可达（connect timed out），无法补扫 |
| 网关路由表 | 未取 | 需 test2 ingress / 网关配置 |

## 7. 用法

```python
from components.udc.graphql_op_naming import path_to_op
path_to_op("/udc/sandbox/client/check-all-status", "GET")  # udcSandboxClientCheckAllStatusGet
```

回归护栏：`tests/udc/test_graphql_op_naming.py`（含 §5.1 的 9/9 复算）。
