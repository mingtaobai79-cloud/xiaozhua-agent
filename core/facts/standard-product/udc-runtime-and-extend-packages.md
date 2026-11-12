# standard-product｜UDC 运行时与扩展点包用法（环境无关）

> 本格只讲**包内怎么用**。不涉及任何具体应用/工程/环境。
> 适用：写 UDC 运行时扩展、按平台模式扩展低代码对象能力、跨服务调标品。

分级：`VERIFIED_STATIC_BYTECODE`（javap + cfr 双路，见 §8）。

## 1. Capability

三件事：

- UDC 运行时的**调用链路与挂载点**（REST → proxy controller → proxy appservice → domain service）
- 平台自己扩展低代码对象的**四类扩展点族**（照这个模式挂行为，不要另造钩子）
- 跨服务调用标品的 **Dubbo 泛化**入口

不证：各运行时方法的具体业务语义；也不证运行期调用时序。

## 2. Version

- `com.seeyon:udc-starter-runtime` 5.3.517（`appservice` / `domain/service` / `proxy` / `util` 四包）
- `com.seeyon:udc-extend` 5.3.517（扩展点族）
- `com.seeyon:boot-starter-dubbo` 5.3.358（泛化）

## 3. Input

- jar 坐标 + 包前缀：
  `udc-starter-runtime` → `com/seeyon/boot/starter/udcrt/{appservice,domain/service,proxy,util}/`
  `udc-extend` → `com/seeyon/udc/extend/`
  `boot-starter-dubbo` → `com/seeyon/boot/starter/dubbo/`
- 命令见 §8（`extract_jar_symbols.py --limit 200`）。

## 4. Required

无前置（纯静态读 jar）。

## 5. Execution

按包前缀逐批抽签名，归纳链路与扩展点族。见 §7。

## 6. Side Effects

只读 jar。

## 7. Known Constraints

### 7.1 运行时链路：扩展代码挂在后两层，不挂 controller

```
REST 请求
  → proxy controller         UdcBaseGeneralController / UdcReferController / Form*/Normal* 四族
  → proxy appservice         UdcPageProxyAppService / MicroFlowProxyAppMicroFlow / …
  → domain service           业务语义层（EntityRuntimeService / FormServiceProxy / UdcAppLogService …）
```

proxy 层的实测规模：`UdcPageProxyAppService` 单类 **56 个方法**（页面运行最大面）；
`UdcBaseGeneralController` 40 个方法；`UdcReferController` 16 个。

⇒ **加行为要挂在 domain service 或 appservice**。挂 controller 会被平台自身路由逻辑绕过，
且不同入口（页面/微流程/接口）走的是不同 controller。

### 7.2 微流程侧的被调入口

```java
class MicroFlowProxyAppMicroFlow {
    Object invokeAppServiceMethod(MicroFlowRestRequestDto request);
    Object wrapDisplayNameResponse(ListResponse<Map<String, ?>> mapListResponse,
                                   BaseResponse originalResponse,
                                   InvokeMethodMetadata methodMetadata);
    RuntimeEntityDataSourceDto getRuntimeEntityDataSourceByJsonFileName(String jsonFileName);
}
```

⇒ 微流程「调用 AppService」这一类节点，最终落点是 `invokeAppServiceMethod`；
返回值包装（含显示名）由 `wrapDisplayNameResponse` 统一处理 —— 自己实现节点时不要另写一套包装。

### 7.3 ★ 扩展低代码对象的四类扩展点族（按这个模式挂，不要另造钩子）

`udc-extend` 里每种能力都是**一套四个角色**，实测覆盖 7 种能力：

```
<Capability>MetaDataPostProcessor     元数据后处理
<Capability>SaveAsHandler             另存为
<Capability>ImporterBase              导入
<Capability>TransportHandler          传输
```

实测存在的 `<Capability>` 集合（逐字来自类名）：

```
CtpEnum(枚举) · CtpExcelExport(导入导出模板) · CtpQrCodeRule(二维码规则) ·
FormConvert(表单转换) · GanttChart(甘特图) · SerialNumber(流水号) · CtpParameter(参数)
```

⇒ 要给某类低代码对象加行为，**先在这四个族里找对应的类名**去继承/替换，
这样才落进平台的注册与执行链；自己新定义一个同功能的钩子不会被调用。

### 7.4 跨服务调用标品：Dubbo 泛化

```java
interface DubboFactory {
    <T> T getProxy(Class<T>);
    <T> T getProxy(Class<T>, String);
    <T> T getProxy(Class<T>, String, int);
    <T> T getProxy(Class<T>, String, String);
    <T> T getProxy(Class<T>, String, String, int);
}
interface AppServiceProxy {
    SingleResponse<Object> invokeAppService(SingleRequest<AppServiceInvokeDto>);
    <T> SingleResponse reliableInvokeAppService(SingleRequest<AppServiceReliableInvokeDto<T>>);
}
interface AppServiceProxyCallback {
    SingleResponse<String> callback(SingleRequest<CommandCallbackDto>);
}
```

⇒ 跨应用/跨服务调标品用 `DubboFactory.getProxy`（重载差异在 serviceName / group / version / timeout 的组合）；
调别的应用的 AppService 用 `AppServiceProxy`（可靠版走 `reliableInvokeAppService` + 回调接口）。
**不要自己拼 Dubbo 直连地址**。

配套（Boot 侧）：`@ServiceBeanPostProcessor` / `SeeyonDubboExportBeanPostProcessor` 负责扫描与导出，
`DubboContextFilter` / `ConsumerLogFilter` / `ProviderLogFilter` 处理上下文与日志 ——
即「导出为 Dubbo 服务」是注解 + 后处理器的结果。

### 7.5 运行时工具类（写扩展时按名找，不要重写）

`udcrt/util` 实测 26 个类，按用途分组：

```
反射/对象     UdcReflectUtil(20) · UdcObjectUtil · UdcJsonUtils(8) · EntityEventDeepCopier
日志          UdcAppLogHelper(57) · OldUdcAppLogHelper(20) · UdcAppLogUtil · EntityLogUtil
              MicroFlowLogUtil · UdcRuleLogUtil · ActionTypeUtil
规则/表达式   EntityRuleUtil · ExpressionEnumUtil · ExpressionRuntimeUtil · SystemFunctionUtil
微流程        MicroFlowRuntimeUtil · GenericService
实体/权限     EntityAuthHelper · EntityRtDaoContainer · TreeEntityUtil
选择/树       UdcDynamicSelectUtil · LruCache · MessageUtil · DateUtil · AnnotationUtils
Bpm           BpmDataUtil
```

⇒ 需要「查实体权限」「翻译枚举」「取表达式运行时值」「写运行日志」这类横切能力时，
先在这个包里按名找，平台已有实现。

### 7.6 运行时读面 DTO

`udcrt/proxy/dto` 与 `udcrt/dto` 是请求/响应模型所在。写自定义读面时先找现成 DTO：

```
UdcMicroFlowRequestDto(8) · MicroFlowRestRequestDto(4) · MicroFlowRestPathMetadataDto(12)
UdcEntityRequestDto · UdcEntityIdsRequestDto · UdcDataFlowRequestDto · UdcReferTreeRequestDto
UdcRestPathParseDto(15) / UdcRestPathParseBaseDto(26)
```

⇒ 不要为「调一个已有读面」自造 DTO —— 平台 DTO 的字段名就是 GraphQL/REST 的字段名。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/
        batch2/udc-starter-runtime.json（306 类 / 2814 方法；含 appservice/service/proxy/util 四包）
        batch2/boot-starter-dubbo.json（48 类 / 220 方法）
        symbols-udc-extend.json（40 类 / 162 方法）★ 该包不在 84 包清单内，单独抽取
        这些文件内只有 artifact 名与版本，无工程/环境信息
② 复现  uv run --no-project python tools/core/platform/extract_jar_symbols.py \
          --jar "<按 Maven 坐标 com.seeyon:<artifact>:<ver> 解析出的 jar>" \
          --include com/seeyon/boot/starter/udcrt/appservice/ \
          --javap <javap 原生路径> --cfr <cfr.jar> --limit 200 --emit <out.json>
        （其余包换 --jar 与 --include）
③ 校验  本格每个类名与签名都能在对应 out.json 的 classes[].symbols 里逐字命中；
        §7.3 的七个 `<Capability>` 词根在 symbols-udc-extend.json 的类名里逐个可核（该件保留，未被 batch2 覆盖）。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 四层链路与各类方法数（proxy 221 / service 316 / appservice 257 / util 176） | `VERIFIED_STATIC_BYTECODE` |
| `MicroFlowProxyAppMicroFlow` 三个方法签名 | `VERIFIED_STATIC_BYTECODE` |
| 四类扩展点族 × 7 种能力 | `VERIFIED_STATIC_BYTECODE`（类名逐字） |
| Dubbo 泛化 3 接口签名 | `VERIFIED_STATIC_BYTECODE` |
| util 26 类分组 | `VERIFIED_STATIC_BYTECODE`（类名 + 方法数） |
| 运行期调用时序 / 织入顺序 | **UNVERIFIED** |

## 铁律

- 扩展代码挂 domain service 或 appservice；运行时链路是 REST → proxy controller → proxy appservice → domain service。
- 给低代码对象加行为，按 `<Capability>{MetaDataPostProcessor,SaveAsHandler,ImporterBase,TransportHandler}` 四族找类名，不要另造钩子。
- 微流程调用 AppService 的落点是 `MicroFlowProxyAppMicroFlow.invokeAppServiceMethod`，返回值包装由 `wrapDisplayNameResponse` 统一处理。
- 跨服务调标品用 `DubboFactory.getProxy`，调别的应用 AppService 用 `AppServiceProxy`，不要自拼 Dubbo 地址。
- 横切能力（权限/枚举/表达式/日志）先在 `udcrt/util` 按名找现成实现，不要重写。
- 调已有读面时用平台现成 DTO，不要自造请求模型。
