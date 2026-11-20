# U2 · 泛化调用：`AppServiceInvokeDto` 九个字段怎么填

## Capability

**回答「不用 facade jar，怎么按字符串调标品 AppService」。**

给 Agent 用：当你要调一个**带 `@DubboService`** 的标品服务、但不想引 facade 依赖，或者要从配置/脚本里动态调，
就用这条路。**字段填错不会报错，会静默返回空 —— 所以本格把每个字段的来源都写死。**

## Version

| 构件 | 版本 |
|---|---|
| `AppServiceInvokeDto` | `boot-starter-dubbo-5.3.600.jar` |
| `AppServiceProxy` | 同上 |
| `GenericService`（平台封装） | `udc-starter-runtime-5.3.605.jar` |

---

## 一、★★★★★ 先看：介子里有 9 个字段，不是 5 个

`AppServiceInvokeDto` 的真实字段（`javap -p` 逐个读出）：

```java
public class AppServiceInvokeDto extends CommandDto {
    private String  interfaceName;      // ① 接口全名
    private String  methodName;         // ② 方法名
    private String  paramType;          // ③ 参数类型（全名，多个用逗号）
    private String  genericType;        // ④ 返回值泛型类型
    private String  subGenericType;     // ⑤ 泛型的泛型（List<X> 里的 X）
    private String  paramJson;          // ⑥ 参数 JSON
    private String  beanName;           // ⑦ Spring bean 名（本地调用时用）
    private Boolean returnJson;         // ⑧ 是否返回 JSON 字符串
    private Boolean bodyZip;            // ⑨ 是否压缩 body
}
```

**★★★ 我先前只记了前 5 个 —— `subGenericType` / `beanName` / `returnJson` / `bodyZip` 完全漏了。**
其中 **`returnJson` 漏了会拿不到值**（返回 `Object` 你没法直接当 DTO 用）。

---

## 二、九个字段逐个说清（这是本格的价值）

| # | 字段 | 怎么填 | 填错的后果 |
|---|---|---|---|
| ① | `interfaceName` | **接口**全名，不是实现类。`com.seeyon.organization.api.common.OrgCommonAppService` | 报 `No provider` / 找不到服务 |
| ② | `methodName` | 方法名，`selectMemberInfoById` | 报方法不存在 |
| ③ | `paramType` | 参数**类型**全名，多个用逗号：`com.seeyon.boot.transport.SingleRequest` | 反序列化失败，`BOOT_3002` |
| ④ | `genericType` | **返回值**泛型实参。返回 `SingleResponse<Map<String,Object>>` → `java.util.Map` | 返回 `null` 或 ClassCast |
| ⑤ | `subGenericType` | 泛型的泛型。`Map<String,Object>` → 填 `java.lang.String,java.lang.Object` | 嵌套泛型取不到值 |
| ⑥ | `paramJson` | 参数对象的 JSON 串（**整个入参**，不是字段） | 空参数 / 反序列化失败 |
| ⑦ | `beanName` | 仅**同 JVM 本地调用**时用，远程留空 | 远程调用填了会被忽略 |
| ⑧ | `returnJson` | `true` → 返回 JSON 字符串；`false`/null → 返回对象 | **漏填→拿到 Object 无法直接用** |
| ⑨ | `bodyZip` | 请求体大（>1MB）时 `true` | 大请求超时/截断 |

### 2.1 ★★ `interfaceName` 填接口，不是实现类

```
✅ com.seeyon.organization.api.common.OrgCommonAppService
❌ com.seeyon.organization.appservice.api.common.OrgCommonAppServiceImpl
```

**判据**：`@DubboService` 标在**实现类**上，但 Dubbo 注册用的是**接口名**。
**⇒ 对着 facade jar 里的接口名填，不是 biz jar 里的 Impl 名。**

### 2.2 ★★ `genericType` 与 `subGenericType` 的关系

真实签名举例：

```java
// OrgCommonAppService 的真实返回
SingleResponse<Map<String, Object>> selectMemberInfoById(SingleRequest<Long>)
```

对应填法：

```java
dto.setGenericType("java.util.Map");                       // ④ 外层泛型
dto.setSubGenericType("java.lang.String,java.lang.Object"); // ⑤ 内层泛型
```

**★★★ 只填 `genericType` 不填 `subGenericType` → Map 的 value 会是 `LinkedHashMap`，
你再往下取字段就取不到。**

### 2.3 ★★★ `returnJson=true` 是最稳的用法

```java
dto.setReturnJson(true);
// 拿到的是 JSON 字符串，自己再用 JsonUtils.fromJson 转
String json = response.getData().getContent().toString();
Map<String,Object> data = JsonUtils.fromJson(json, Map.class);
```

**好处：绕开泛型擦除，不用猜 `genericType`。**
**代价：多一次序列化。**

**⇒ Agent 第一次调陌生接口时，建议 `returnJson=true` + 打印 JSON，看真实结构后再决定要不要强类型。**

---

## 三、三种调用姿势（按推荐度）

### 姿势 1：平台封装 `GenericService`（★ 最省事）

`com.seeyon.boot.starter.udcrt.util.GenericService`（`udc-starter-runtime`）真实签名：

```java
public <T> SingleResponse<Object> invoke(
        String interfaceName,   // 参数名实测
        String methodName,
        T      requestDto);     // 直接给 DTO 对象，不用自己拼 JSON
```

**它内部帮你做了**（`javap -l` 局部变量表实测）：

```
requestDto  → SingleRequest         (偏移 6)
            → AppServiceInvokeDto    (偏移 15)
            → AppServiceProxy.invokeAppService
```

**★ 所以最简写法是：**

```java
@Autowired
private com.seeyon.boot.starter.udcrt.util.GenericService genericService;

// 调组织服务 —— 不用拼 9 个字段
SingleResponse<Object> resp = genericService.invoke(
        "com.seeyon.organization.api.common.OrgCommonAppService",
        "selectMemberInfoById",
        SingleRequest.from(memberId));

Object data = resp.getData().getContent();
```

**⚠️ 它只支持单参方法**（签名只有一个 `T requestDto`）。

### 姿势 2：`AppServiceProxy` 直接调（★ 完整控制）

```java
@Autowired
private com.seeyon.boot.starter.dubbo.api.AppServiceProxy appServiceProxy;

AppServiceInvokeDto dto = new AppServiceInvokeDto();
dto.setInterfaceName("com.seeyon.organization.api.common.OrgCommonAppService");
dto.setMethodName("selectMemberInfoById");
dto.setParamType("com.seeyon.boot.transport.SingleRequest");
dto.setGenericType("java.util.Map");
dto.setSubGenericType("java.lang.String,java.lang.Object");
dto.setParamJson(JsonUtils.toJson(SingleRequest.from(memberId)));
dto.setReturnJson(true);

SingleResponse<Object> resp = appServiceProxy
        .invokeAppService(SingleRequest.from(dto));
```

**三个变体（真实存在）：**

```java
invokeAppService(...)           → SingleResponse<Object>    // 单个
invokeAppServiceForList(...)    → ListResponse<Object>      // 列表
invokeAppServiceForPage(...)    → PageResponse<Object>      // 分页
reliableInvokeAppService(...)   → SingleResponse<T>         // 带可靠投递
```

**★★★ 返回 List 用 `ForList`，返回 Page 用 `ForPage` —— 用错会 ClassCast。**

### 姿势 3：裸 Dubbo `GenericService`（不推荐）

```java
// 需要自己拿 Dubbo ReferenceConfig，太底层
GenericService gs = ...;
Object r = gs.$invoke(methodName, paramTypes, args);
```

**⇒ 平台已经把上面这些包好了。除非你要绕过 `@AppService` 框架，否则别用裸的。**

---

## 四、完整可跑示例

**需求**：不引 facade jar，按成员 id 查人。

```java
@Service
public class CrossAppCallDemo {

    @Autowired
    private com.seeyon.boot.starter.dubbo.api.AppServiceProxy proxy;

    public Map<String, Object> getMember(Long memberId) {

        AppServiceInvokeDto dto = new AppServiceInvokeDto();

        // ① 接口全名（facade 里的接口，不是 Impl）
        dto.setInterfaceName("com.seeyon.organization.api.common.OrgCommonAppService");
        // ② 方法名
        dto.setMethodName("selectMemberInfoById");
        // ③ 入参类型（SingleRequest 是标准包装）
        dto.setParamType("com.seeyon.boot.transport.SingleRequest");
        // ④⑤ 返回值泛型：SingleResponse<Map<String,Object>>
        dto.setGenericType("java.util.Map");
        dto.setSubGenericType("java.lang.String,java.lang.Object");
        // ⑥ 入参 JSON（整个 SingleRequest 对象）
        dto.setParamJson(com.seeyon.boot.util.JsonUtils.toJson(
                com.seeyon.boot.transport.SingleRequest.from(memberId)));
        // ⑧ 返回 JSON，避免泛型擦除
        dto.setReturnJson(true);

        SingleResponse<Object> resp = proxy.invokeAppService(
                com.seeyon.boot.transport.SingleRequest.from(dto));

        Object content = resp.getData().getContent();
        if (content == null) return null;
        return com.seeyon.boot.util.JsonUtils.fromJson(content.toString(), Map.class);
    }
}
```

---

## 五、Side Effects

| 调用 | 副作用 |
|---|---|
| `GenericService.invoke` | 远端执行（**不在本地事务内**） |
| `AppServiceProxy.invokeAppService` | 同上，且走 `@AppService` 的日志/权限/幂等切面 |
| `reliableInvokeAppService` | 带可靠投递（失败会重试/补偿） |

**⚠️ 泛化调用和 `@DubboReference` 一样，跨进程，本地回滚不回滚远端。**

## 六、Known Constraints

| # | 约束 |
|---|---|
| 1 | **`interfaceName` 填接口名，不是 `...Impl`** |
| 2 | **目标服务必须带 `@DubboService`**（见 `U1-invocation-decision.md`） |
| 3 | **`returnJson` 不填 → 拿到 `Object` 无法直接当 DTO** |
| 4 | **嵌套泛型必须填 `subGenericType`**，否则 Map 的 value 是 `LinkedHashMap` |
| 5 | **`paramJson` 是「整个入参对象」的 JSON**，不是单字段 |
| 6 | **返回 List 用 `ForList`，Page 用 `ForPage`**，用错 ClassCast |
| 7 | **`beanName` 只对同 JVM 有效**，远程调用填了会被忽略 |
| 8 | **平台封装的 `GenericService.invoke` 只支持单参方法** |
| 9 | **泛化调用跨进程，不在本地事务内** |
| 10 | **环境 `seeyon.dubbo.provider.enable=false` 时调不到**（见 U1 §2.2） |

## 七、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `AppServiceInvokeDto` 9 个字段 | `javap -p` 全部 private 字段逐个读出 | **VERIFIED_STATIC_BYTECODE** |
| `AppServiceProxy` 4 个方法（invoke / ForList / ForPage / reliable） | `javap -p` | **VERIFIED_STATIC_BYTECODE** |
| `GenericService.invoke(String, String, T)` 及参数名 `interfaceName`/`methodName`/`requestDto` | `javap -l -p` 的 `LocalVariableTable` | **VERIFIED_STATIC_BYTECODE** |
| `GenericService` 内部转 `SingleRequest` → `AppServiceInvokeDto` → `AppServiceProxy` | 同上，局部变量槽 4/5 + 偏移 6/15 | **VERIFIED_STATIC_BYTECODE** |
| `selectMemberInfoById` 返回 `SingleResponse<Map<String,Object>>` | `javap -p` 接口签名 | **VERIFIED_STATIC_BYTECODE** |
| 泛化调用真实跑通 | 未实测 | **UNVERIFIED** |

## 八、Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：9 个字段、4 个 Proxy 方法、`GenericService` 签名与内部链路（全部 javap 逐个）
- ⚠️ **UNVERIFIED**：真实调用跑通（需 provider 在线 + 实参）
- ⚠️ **UNVERIFIED**：`subGenericType` 的精确分隔符（字节码看到 `String` 类型，分隔符需实测确认是逗号）

## 九、给 Agent 的判据

```
问「不用 facade jar 怎么调标品」
  → GenericService.invoke(接口名, 方法名, 入参对象)   ← 最省事，只支持单参
  → 或 AppServiceProxy + AppServiceInvokeDto（9 字段）

问「interfaceName 填接口还是实现类」
  → 接口。com.seeyon.organization.api.common.OrgCommonAppService
  → 不是 ...AppServiceImpl

问「AppServiceInvokeDto 要填几个字段」
  → 9 个字段，不是 5 个
  → 必填 6 个：interfaceName / methodName / paramType / paramJson / (genericType)
  → ★ returnJson=true 强烈建议

问「调完拿不到值」
  → ① returnJson 填了吗？
  → ② genericType/subGenericType 匹配真实返回类型吗？
  → ③ 返回的是 List 却用了 invokeAppService（该用 ForList）

问「Map 里取不到字段」
  → subGenericType 没填，value 变成 LinkedHashMap
  → 填 "java.lang.String,java.lang.Object"

问「GenericService.invoke 报参数不对」
  → 它只支持单参方法（签名只有一个 T requestDto）

问「这个服务能泛化吗」
  → 先查 U1-invocation-decision.md，看实现类有没有 @DubboService
```