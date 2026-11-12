# standard-product｜core jar 工具类与平台注解（环境无关）

> 本格只讲**包内有什么、怎么调**。不涉及任何具体应用/工程/环境。
> 适用：扩展代码要写工具逻辑前，先确认平台是否已有实现；以及给自己的 DTO/实体/接口加平台注解。

分级：`VERIFIED_STATIC_BYTECODE`（javap 逐类，见 §8）。

## 1. Capability

`boot-core`（507 类 / 85 接口 / 3783 方法）里最常用的两块：

- **工具类**：JSON / 日期 / 字符串 / Bean / 数据库 / IO / 加密 / 缓存 / ID
- **平台注解**：`@AppService` / `@AppServiceOperation` / `@EntityInfo` / `@RestApi` / `@OpenApi` /
  `@HasRole` / `@ResourcePermission` / `@Safety` / `@Maskable`

不证：各工具的边界行为（null 处理、时区、异常策略）—— 用前读实现或自测。

## 2. Version

`com.seeyon:boot-core` 5.3.358

## 3. Input

`boot-core-<ver>.jar`；包前缀 `com/seeyon/boot/util/`、`com/seeyon/boot/annotation/`。

## 4. Required

无前置（纯静态读 jar）。

## 5. Execution

按包前缀抽签名，按用途分组。见 §7。

## 6. Side Effects

只读 jar。

## 7. Known Constraints

### 7.1 工具类（实测方法数，先找现成的，不要重写）

```
JsonUtils(28)        toJson / toJsonNotIncludeNull / toJsonLongToString / toJsonDecimalToString
                     toJsonEnumToCode / toJsonThrowError / fromJson(String, Class)
DateUtils(61)        format / formatDate / formatDatetime / parse / parseDate / parseDatetime
                     registerPattern / unRegisterPattern / getTime
StringUtils(35)      camelToUnderline / toPinyin* / compareVersion / getMajorVersion / bigVersion
                     mask(String,int,int[,char]) / isBlankDefault / matcher
ToStringUtils(44)
DatabaseUtils(47)
IoUtils(28)  FileUtils(21)  IpUtils(21)
BeanUtils(7)         getFieldValue / setFieldValue / getterName / setterName / getDefaultClassLoader
TypeConverterManager(11)  register/unregister/getTypeConverter/containsType
SeeyonCache(8)       size/isEmpty/containsKey/get/put/remove/putAll/clear
IdentifierGenerator(3)    generateLong() / generateString() / analyze(Long)
```

三条实用点：

- **`toJson` 有多个变体**：`toJsonNotIncludeNull`（去 null）、`toJsonLongToString`（Long 转字符串，
  避免前端精度丢失）、`toJsonDecimalToString`（金额精度）、`toJsonEnumToCode`（枚举输出 code 而非 name）。
  前后端交互时按需要选，别一律 `toJson`。
- **`StringUtils.mask(String, int, int[, char])`** —— 脱敏直接用，别自己 substring 拼星号。
- **`IdentifierGenerator.generateLong()`** 出 Long 主键；`analyze(Long)` 反解（能拿回时间/机器等信息）。

### 7.2 类型转换是可注册的：`TypeConverterManager`

```java
public interface TypeConverter<T> {
    Class<T> getTargetType();
    List<Class<?>> getSupportedSourceTypes();
    T convert(Object src, Class<? extends T> target);
    T convert(Map<?,?> ctx, Object src, Class<? extends T> target);
    <M extends AccessibleObject> T convert(Map<?,?> ctx, M member, Object src, Class<? extends T> target);
}
public interface TypeConverterManager {
    <S,T> void register(Class<? extends S> src, Class<T> tgt, TypeConverter<? extends T> conv);
    void register(TypeConverter<?> conv);
    <S,T> TypeConverter<T> unregister(Class<S> src, Class<T> tgt);
    <T> Collection<TypeConverter<T>> getTypeConverter(Class<T> tgt);
    <S,T> TypeConverter<T> getTypeConverter(Class<S> src, Class<T> tgt);
    boolean containsType(Class<?> t);  boolean containsType(Class<?> s, Class<?> t);
}
```

⇒ 自定义类型（如「字符串 → 你的枚举/DTO」）**注册一个 `TypeConverter` 即可**，
平台在参数绑定/属性拷贝时会用它。不要在各处写 `if (type == X) ...` 的转换分支。

### 7.3 平台注解：给自己的契约加「平台能力」

```java
// 声明一个 AppService（标品同类契约）
public @interface AppService {
    String value(); String description(); int sort(); Custom[] customs();
}
// 声明一个可被外部调用的操作（含开放 API 开关）
public @interface AppServiceOperation {
    String value(); String description(); String returnValue();
    OpenApi openApi(); int sort(); int requestMaxSize(); String plugins(); boolean ignoreVersion();
    Custom[] customs();
}
// 把能力开放成 OpenAPI —— 就是加这个注解
public @interface OpenApi {
    boolean isOpenApi(); String url(); boolean async(); int sort(); Custom[] customs();
}
// 权限 / 资源
public @interface HasRole        { String[] value(); String orgId(); }
public @interface ResourcePermission { String pageInfo(); String resourceInfo(); }
// 安全（加密/审计/脱敏）
public @interface Safety {
    EncryptionEnum encryption(); boolean auditLog(); boolean permission();
    boolean sensitive(); boolean openApiEncrypt();
}
public @interface Maskable { MaskType type(); String[] maskKeys(); int start(); int end(); }
// REST 面
public @interface RestApi          { String value(); int sort(); String group(); Custom[] customs(); }
public @interface RestApiOperation { String value(); String description(); String returnValue();
                                     Custom[] customs(); AuditMode auditMode(); int sort(); }
// 实体/枚举元数据
public @interface EntityInfo { String value(); String description(); EntityType entityType();
                               String historyEntity(); String plugins(); boolean fullTextSearch();
                               boolean permission(); boolean isPublic(); boolean export();
                               boolean isLogicDelete(); }
public @interface EntityIndex / EnumInfo / DtoInfo / MessageInfo / ParameterInfo
```

⇒ **「把接口开放到 OpenAPI」不是一个开关，而是注解组合**：`@AppService` 声明契约 +
`@AppServiceOperation(openApi=@OpenApi(isOpenApi=true, url="..."))` 声明该操作开放。
`@Safety(encryption=..., sensitive=true, auditLog=true)` 控制加密/脱敏/审计，
`@Maskable(type=..., start=..., end=...)` 控制返回值的脱敏区间。

### 7.4 敏感/加密的 SPI 在 `boot-spi`

```java
public interface EntityEncryption { String encrypt(String); String decrypt(String); }
public interface SensitiveSpi     { String sensitiveProcess(String); }
public interface DataSignExecution { Boolean envEnable(); Map SignatureList(); String Signature();
                                     Boolean Verify(); Map VerifyList(); }
```

⇒ 要替换加密/脱敏/验签实现，实现这三个 SPI；**不要**在业务代码里硬编码加解密。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/batch2/boot-core.json
        （507 类 / 85 接口 / 3783 方法 / 字段亦已抽）
        batch2/boot-spi.json（3 接口 / 8 方法）
② 复现  uv run --no-project python tools/core/platform/extract_jar_symbols.py \
          --jar "<按 Maven 坐标 com.seeyon:<artifact>:<ver> 解析出的 jar>" \
          --include com/seeyon/boot/ --javap <javap 原生路径> --limit 1000 --emit <out.json>
③ 校验  本格每个工具类名/方法数都能在 out.json 里逐字命中；
        §7.3 的每个注解属性名在 classes[].symbols.methods[]（注解方法即属性）里逐个可核。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 工具类与方法数（JsonUtils 28 / DateUtils 61 / StringUtils 35 …） | `VERIFIED_STATIC_BYTECODE` |
| `JsonUtils` 的 5 个 toJson 变体 | `VERIFIED_STATIC_BYTECODE` |
| `TypeConverterManager` 可注册转换 | `VERIFIED_STATIC_BYTECODE` |
| 9 类平台注解及其全部属性名 | `VERIFIED_STATIC_BYTECODE`（注解方法=属性，逐字） |
| `@OpenApi` 嵌在 `@AppServiceOperation` 内 | `VERIFIED_STATIC_BYTECODE`（属性类型逐字） |
| `boot-spi` 三个 SPI | `VERIFIED_STATIC_BYTECODE` |
| 各工具的实际边界行为（null/时区/异常） | **UNVERIFIED**（未跑用例） |

## 铁律

- 写工具逻辑前先查 `boot-core` 的 `com/seeyon/boot/util/`：JSON/日期/字符串/Bean/DB/IO/加密/缓存/ID 都已具备。
- `toJson` 按场景选变体：去 null 用 `toJsonNotIncludeNull`，Long 精度用 `toJsonLongToString`，枚举输出 code 用 `toJsonEnumToCode`。
- 脱敏用 `StringUtils.mask(...)`，不要自己 substring 拼星号。
- 自定义类型转换注册 `TypeConverter` 到 `TypeConverterManager`，不要写散落的 if-else 转换分支。
- 把能力开放成 OpenAPI 用注解组合：`@AppService` + `@AppServiceOperation(openApi=@OpenApi(isOpenApi=true,...))`。
- 加密/脱敏/验签替换实现走 `boot-spi` 的 `EntityEncryption`/`SensitiveSpi`/`DataSignExecution`，不要在业务里硬编码。
- 主键用 `IdentifierGenerator.generateLong()`，不要自拼雪花/时间戳。
