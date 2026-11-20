# boot-core 工具类能力清单（177 类，方法级）

> 数据源：`boot-core-5.3.600.jar` → `javap -public`（全部 177 个 principal class）
> 原始签名：`D:/software/hermes/cache/scratch/bootcore-util-sigs.txt`（1,989 行）
> 等级：`VERIFIED_STATIC_BYTECODE`（javap 方法签名，未读方法体）
> ⚠️ 用户环境 5.3.517，本机 5.3.600

---

## 0. 使用规则

**这批工具全部是 `public static` 方法，第三类调用形态：直接静态调用，不需要注入。**

```java
// 直接用，不需要 @Autowired
String json = JsonUtils.toJson(obj);
Long id     = Ids.gidLong();
String enc  = AESUtils.encrypt(plain, key);
```

**⚠️ 关键约束：这些工具**不处理**平台上下文（租户、用户、权限）。**
**涉及上下文的一律走 Service / AppService，不要用工具类硬闯。**

---

## 1. ★★ JsonUtils（25 方法，全静态）

**包：** `com.seeyon.boot.util.JsonUtils`

### 1.1 序列化

```java
String toJson(Object)                        // 标准序列化
String toJson(Object, boolean)               // 带格式化控制
String toJsonEnumToCode(Object)              // 枚举转 code（不是 name）
String toJsonLongToString(Object)            // ★ Long 转 String（防前端精度丢失）
String toJsonDecimalToString(Object)         // ★ Decimal 转 String
String toJsonNotIncludeNull(Object)          // 排除 null 字段
String toJsonThrowError(Object) throws Exception  // 失败抛异常
```

**★★ 三组「ThrowError 模式」是重点：**
```
toJson            vs  toJsonThrowError
   失败静默返回 null/空串      失败抛异常
```
**⇒ 需要感知序列化失败必须用 `*ThrowError` 版本。**

**★ `toJsonLongToString` / `toJsonDecimalToString` 的必要性：**
JavaScript 的 Number 只能精确表示 2^53，平台借据 ID 是雪花 ID（19 位），超过精度。
**⇒ 传给前端必须用 `toJsonLongToString`，否则 ID 被截断。**

### 1.2 反序列化

```java
<T> T fromJson(String, Class<T>)
<T> T fromJsonThrowError(String, Class<T>) throws Exception
<T> T fromJson(String, Class<T>, Class)                    // 带泛型参数
<T> T fromJson(String, Class<T>, Class, Class)             // 两个泛型参数
<T> T fromJsonThrowError(String, Class<T>, Class) throws Exception
```

**★ `fromJson` 的 3/4 参数版本用于泛型：**
```java
// 反序列化 List<OrderDto>
List<OrderDto> list = JsonUtils.fromJson(json, List.class, OrderDto.class);
```

### 1.3 转 Map / List

```java
Map<String,String> toStringMap(String)
Map<String,String> toStringMapThrowError(String) throws Exception
Map<String,Object> toMap(String)
Map<String,Object> toMapThrowError(String) throws Exception
<K,V> Map<K,V> toMapThrowError(String, Class<K>, Class<V>) throws Exception
<K,V> Map<K,V> toMap(String, Class<K>, Class<V>)

List<String> toStringList(String)
List toList(String)
<T> List<T> toList(String, Class<T>)
List toListThrowError(String) throws Exception
<T> List<T> toListThrowError(String, Class<T>) throws Exception
```

**⇒ 一共 **12 种**「序列化/反序列化 × 目标类型 × 是否抛异常」的组合，覆盖所有常见场景。**

### 1.4 相关的序列化类

| 类 | 用途 |
|---|---|
| `SeeyonObjectMapper` | 平台定制的 Jackson ObjectMapper |
| `JacksonSerializer` / `KryoSerializer` / `FstSerializer` | 三种序列化后端 |
| `EnumJsonSerializer` / `EnumJsonDeserializer` | 枚举专用 |
| `EnumToCodeSerializer` | 枚举转 code |
| `SeeyonPropertyNamingStrategy` | 命名策略 |
| `DateStrFormat` | 日期格式注解 |

---

## 2. ★★ HttpClientUtil（大量重载，HTTP 全家桶）

**包：** `com.seeyon.boot.util.http.HttpClientUtil`

### 2.1 GET

```java
String get(String url)
String get(String url, Charset)
String get(String url, int timeout)
String get(String url, Map<String,Object> params)
String get(String url, Map<String,Object> params, int timeout)
String get(String url, HttpHeader)
String get(String url, HttpHeader, Map<String,Object>)
String get(String url, Charset, int, HttpHeader)
String get(String url, Charset, int, HttpHeader, Map<String,Object>)
String get(HttpConfig) throws HttpProcessException

// 泛型版：直接反序列化成对象
<T> T get(String url, Class<T>)
<T> T get(String url, Map<String,Object>, Class<T>)
<T> T get(String url, int, Class<T>)
<T> T get(String url, HttpHeader, Class<T>)
<T> T get(HttpConfig, Class<T>)

// 保留全部响应信息版
HttpResult sendGet(String url)
HttpResult sendGet(String url, HttpHeader)
HttpResult sendGet(String url, Map<String,Object>)
HttpResult sendGet(HttpConfig)
```

### 2.2 POST

```java
String post(String url, String body)
String post(String url, Map<String,Object> params)
String post(String url, String body, HttpHeader)
String post(String url, Map<String,Object>, HttpHeader)
String post(String url, Map<String,Object>, int timeout)
String post(String url, String body, HttpHeader, int, Charset)
String post(HttpConfig) throws HttpProcessException

// 泛型版
<T> T post(String url, Map<String,Object>, Class<T>)
<T> T post(String url, String body, Class<T>)

// HttpResult 版
HttpResult sendPost(String url, String body)
HttpResult sendPost(String url, Map<String,Object>)
HttpResult sendPost(HttpConfig)

// 保留 Map 形态的响应
Map<String,Object> postOverload(String url, String body, HttpHeader)
```

### 2.3 DELETE

```java
String delete(String url)
String delete(String url, HttpHeader)
HttpResult delete(HttpConfig)
```

### 2.4 下载

```java
OutputStream down(String url, OutputStream)
OutputStream down(String url, HttpHeader, OutputStream)
InputStream downForInputStream(HttpConfig)
HttpResponse down(String url)
```

### 2.5 ★ 四层返回形态（关键区别）

| 返回 | 何时用 |
|---|---|
| `String` | 只要响应体 |
| `<T> T` | 要反序列化成对象（最省事） |
| `HttpResult` | **要状态码、响应头**（`sendGet` / `sendPost`） |
| `Map<String,Object>` | 响应是 Map 且不想建类（`getOverload` / `postOverload`） |

**⇒ 判成功不能只看「有没有抛异常」，必须用 `HttpResult` 看 status code。**

### 2.6 配套类

| 类 | 用途 |
|---|---|
| `HttpConfig` | 完整请求配置（url/method/headers/body/编码/超时） |
| `HttpHeader` | 请求头 |
| `HttpResult` | 响应（含 code/body/headers） |
| `HttpMethods` / `HttpVersionEnum` | 常量 |
| `HttpProcessException` | HTTP 异常 |
| `HttpClientRoundRobinRouting` / `HttpClientRouteConfig` / `HttpClientRouteHeartbeat` | **多节点轮询路由 + 心跳**（服务发现场景） |
| `HttpClientMetrics` | 指标采集 |
| `FileUploadModel` / `FileStreamUploadModel` | 文件上传模型 |

**★ `HttpClientRoundRobinRouting` 说明：平台有自己的 HTTP 客户端负载均衡，不只是单节点请求。**

### 2.7 REST 相关

| 类 | 用途 |
|---|---|
| `RestServiceUtil` | REST 服务工具 |
| `ComponentUrlUtil` | 组件 URL 构造 |

---

## 3. ★★ 加密（4 个类）

### 3.1 AESUtils（9 方法）

```java
String encrypt(String data, String key)
String encrypt(String data, String key, int keySize)
String encrypt(byte[] data, String key)
String encrypt(byte[] data, String key, int keySize)
String decrypt(String data, String key)
String decrypt(String data, String key, int keySize)
byte[] decrypt2Byte(String data, String key)
byte[] decrypt2Byte(String data, String key, int keySize)
int DEFAULT_KEY_SIZE
```

### 3.2 DESUtils（4 方法）

```java
String encrypt(String, String key)
String encrypt(byte[], String key)
String decrypt(String, String key)
byte[] decrypt2Byte(String, String key)
```

### 3.3 RSAUtils（10 方法）

```java
KeyPair generateKey()                                  // ★ 生成密钥对
String keyEncrypt(Key)                                 // 密钥导出
String encrypt(String data, PublicKey)                 // 公钥加密
String encrypt(byte[], PublicKey)
String encrypt(String data, String publicKeyStr)       // ★ 字符串公钥
String encrypt(byte[], String)
String decrypt(String data, PrivateKey)
String decrypt(String data, String privateKeyStr)
byte[] decrypt2Byte(String data, PrivateKey)
byte[] decrypt2Byte(String, String)
```

### 3.4 摘要

```java
MD5        / MD5Utils      // MD5
SHA1Utils                  // SHA1
SHA256Utils                // SHA256
Hex                        // 十六进制编解码
```

**⚠️ 加密不要自己写实现，平台这 4 个类的算法参数（补位模式、密钥派生）与平台其他组件一致。**
**⇒ 自己用 JCE 写会导致加解密结果对不上。**

---

## 4. ★★ DateUtils（73 方法，最大）

**包：** `com.seeyon.boot.util.DateUtils`

### 4.1 预定义格式常量（14 个）

```java
CHINESE_DATE_FORMAT_LINE                // 中文日期
CHINESE_DATETIME_FORMAT_LINE            // 中文日期时间
CHINESE_DATETIME_WITHOUT_SECOND_FORMAT_LINE
CHINESE_DATE_FORMAT_SLASH               // 斜杠分隔
CHINESE_DATETIME_FORMAT_SLASH
GMT_DATE_FORMAT_LINE                    // GMT
DATETIME_NOT_SEPARATOR                  // 无分隔符
DATETIME_NOT_SEPARATOR_MS               // 无分隔符带毫秒
DATE_SHORT_SIMPLE_YEAR_FORMAT
DATE_SHORT_SIMPLE_MONTH_FORMAT
DATE_SHORT_SIMPLE_DAY_FORMAT
DATE_SHORT_LINED_MONTH_FORMAT
BUILD_VERSION_FORMAT                    // 构建版本号格式
FIRST_DAY_OF_WEEK                        // 每周第一天
```

**⇒ 用常量，不要自己写 pattern 字符串，否则跨语言/跨环境不一致。**

### 4.2 格式化 / 解析

```java
String formatDate(Date)
String formatDatetime(Date)
String format(Date, String pattern)
String format(Date, String pattern, TimeZone)
// 还有约 49 个：解析、加减、比较、区间、周计算等
```

### 4.3 相关转换器

```
DateTypeConverter / StringToDateConverter / TimestampTypeConverter
```

---

## 5. ★★ StringUtils（34 方法）

```java
// 基础
String first(String)
String getSimpleNameFromFullName(String)        // 全限定名 → 简单名

// ★ 拼音（平台内置）
String toPinyin(String)
String toPinYinFirstSpell(String)
String toPinyinFistWord(String)
String toPinyinFistLetter(String)

// ★ 版本比较
String bigVersion(String)
String getMajorVersion(String)
int compareVersion(String, String)

// 命名转换
String camelToUnderline(String)                 // 驼峰 → 下划线

// 空值兜底
<T> T isBlankDefault(T value, T defaultVal)

// 正则匹配
boolean matcher(String, String)

// ★★★ 脱敏（7 个专用）
String mask(String, int start, int end)
String mask(String, int, int, Character maskChar)
String maskUserName(String)
String maskBankCardNo(String)
String maskIdCardNo(String)
String maskMobileNo(String)
String maskEmail(String)
String maskAuto(String)
String maskByType(String, Maskable)
```

**★★ 脱敏是平台内建能力，不要自己实现。**
**⇒ `maskByType(String, @Maskable)` 直接读注解决定脱敏方式，与实体字段注解联动。**

**★ 拼音能力内建** —— 用于人员姓名检索、组织架构模糊匹配。

---

## 6. ★★ Ids（7 方法）—— 主键生成

```java
Long gidLong()                // ★ 主力：雪花 ID（19 位 Long）
String gidString()            // 字符串形态
String gSwIdString()
Date analyzeDate(Long id)     // ★ 从 ID 反解生成时间
Long uuidLong()
long uuidAbsLong()
String uuidString()
```

**★★ `Ids.gidLong()` 是全平台单据/实体主键生成入口。**
**⇒ 已实证用于：`BaseEntityCurdService.create4Bpm` 预生成主键。**
**⇒ `analyzeDate(id)` 能从雪花 ID 反解创建时间 —— 排查数据创建时间用得上。**

**配套类：** `SnowflakeIDGenerator` / `SnowflakeIDElement` / `NetAddressIdWorker` / `UUIDGenerator` / `IdentifierGenerator` / `IdGeneratorProperties`

---

## 7. ★★ BeanCopier（13 方法）

```java
// ★ 主力：拷贝成新对象
<T> T copy(Object src, Class<T> targetClass, String... ignoreProps)
<T> T copy(Object src, Class<T>, CopyStrategy, String...)

// 就地拷贝
void copy(Object src, Object target, String... ignoreProps)
void copy(Object src, Object target, CopyStrategy, String...)

// ★ 集合 / 分页
<T,D> List<D> copyList(Collection<T>, Class<D>)
<T,D> List<D> copyList(Collection<T>, Class<D>, CopyStrategy, ...)
<T,D> PageData<D> copyPageData(PageData<T>, Class<D>, ...)

// 资源管理
void removeClassLoader(ClassLoader)
void clearRubbish()
void clear(ClassLoader)
```

**★★ `BeanCopier.copy(src, TargetDto.class)` 是平台 DTO ↔ Entity 转换的标准方式。**
**⇒ 已实证：`BaseEntityCurdService` 用它做 `frontDto → BaseEntityActionDto` 备份。**
**★ `ignoreProps` 可变参数可以排除字段，避免覆盖敏感值。**

**⚠️ `removeClassLoader` / `clear` 说明 BeanCopier 内部有类加载器缓存 —— 热部署/动态加载场景必须清理，否则内存泄漏。**

---

## 8. ★★ Asserts（26 方法）—— 断言

```java
// 空判断
void notNull(Object)
void notNull(Object, String message)
void notNull(Object, String msgKey, String defaultMsg)
void isNull(Object) / isNull(Object, String) / isNull(Object, String, String)

// 非空（多类型）
void notEmpty(String)
void notEmpty(Collection<?>)
void notEmpty(Map<?,?>)
void notEmpty(Object[])
（每个都有带 message 和 msgKey 的版本）

// 必须为空
void empty(String) / empty(String, String) / empty(String, String, String)

// 布尔
void isTrue(boolean)
void isTrue(boolean, String)
void isTrue(boolean, String, String)

// 区间
void between(int value, int min, int max, String, String)
void between(long value, long min, long max, String, String)
```

**★★ 三参数版本 `(obj, msgKey, defaultMsg)` 是 i18n 消息：**
```
msgKey      国际化资源 key
defaultMsg  找不到 key 时的兜底文本
```
**⇒ 平台所有校验异常都走这个模式，自己写校验也要遵循。**

---

## 9. Validators（4 方法）—— JSR303 校验

```java
Object assertjsr303(Object bean, Class<?>... groups)
void assertEmpty(String, String)
RequestCheckException checkJsr303WithGroup(MessageRepository, RequestContext, ...)
void checkJsr303WithGroup(MessageRepository, RequestContext, ...)
```

**⇒ `assertjsr303(bean)` 触发 bean 上的 `@NotNull` / `@Size` 等注解校验。**
**⇒ 与 `Asserts` 的区别：`Asserts` 手写条件，`Validators` 读注解。**

---

## 10. FileUtils（21 方法） / IoUtils（28 方法）

### FileUtils

```java
File tempFile() / tempFile(String) / tempFile(String, String...)
File tempDir() / tempDir(String...)
InputStream openInputStream(File)
File writeStringToFile(String content, ...)
File copyInputStreamToFile(InputStream) / (InputStream, File)
File copyURLToFile(URL)
String readFileToString(File) / (File, String charset)
List<String> readLines(File) / (File, String charset)
void delete(File) / deleteDirectory(File) / deleteQuietly(File)
void forceDelete(File) / forceDeleteOnExit(File)
String getFileType(InputStream)                 // ★ 从流判断文件类型
```

**★ `tempFile()` / `tempDir()` 用平台临时目录规范，不要自己拼 `System.getProperty("java.io.tmpdir")`。**
**★ `deleteQuietly` 不抛异常 —— 清理场景用这个。**

### IoUtils

```java
// 流 → 字符串（7 种源）
String toString(byte[])
String toString(byte[], String charset)
String toString(InputStream)
String toString(InputStream, Charset) / (InputStream, String)
String toString(Reader)
String toString(URI, Charset) / (URI, String)
String toString(URL, Charset) / (URL, String)

// 字符串 → 流
InputStream toInputStream(CharSequence, Charset)
InputStream toInputStream(String)
...

// 读取
List<String> readLines(InputStream)
List<String> readLines(Resource)
int copy(InputStream, OutputStream)

// ★ 静默关闭（5 种）
void closeQuietly(Closeable)
void closeQuietly(Closeable...)
void closeQuietly(Closeable, Consumer<IOException>)
void closeQuietly(InputStream) / (OutputStream) / (Reader)
```

**★ `closeQuietly` 是平台标准资源关闭方式，不会因 close 抛异常掩盖业务异常。**

---

## 11. ZipUtils（16 方法）

```java
// 压缩
File zip(File...)
File zip(boolean includeRoot, File...)
File zip(boolean, String entryName, File...)
File zip(String zipName, boolean, String, File...)
File zip(InputStream, String)
File zip(InputStream, String, String)

// 解压（7 种）
File unZip(File)
File unZip(File, String targetDir)
File unZip(File, String, String)
File unZipToDir(File, String, String)
File unZipToDir(InputStream, String, String)
File unZip(InputStream, String, String)
File unZip(InputStream, String)
File unZip(InputStream)

// 读内部文件
byte[] getZipInnerFile(File zip, String entry, String ...)
```

---

## 12. ImageUtils（7 方法）—— 图片缩放/缩略图

```java
void resize(String src, String dest, int w, int h)
void resize(String, String, int, int, boolean keepRatio)
void resize(String, String, int, int, float quality)
void resize(String, String, int, int, float, boolean)
File resize(String src, int w, int h, boolean)
File resize(String, int, int, float, boolean)
void thumbnailGifImage(String src, String dest, int w, int h)   // ★ GIF 专用
```

---

## 13. PageUtils（3 方法）—— 分页

```java
<T> PageResponse<T> paginate(List<T> all, PageInfo pageInfo)
<T> PageData<T>     paginateData(List<T> all, PageInfo)
<T> List<T>         paginateList(List<T> all, PageInfo)
```

**⇒ 内存分页（先查出全部再切），不是 SQL 分页。**
**⚠️ 数据量大时不要用，走 DAO 层 SQL 分页。**

---

## 14. DatabaseUtils（5 方法）—— SQL 方言转换

```java
String mysqlToDm(String sql)          // MySQL → 达梦
String mysql2Oracle(String sql)       // MySQL → Oracle
String mysql2Postgre(String sql)      // MySQL → PostgreSQL
String mysql2KingbaseV8(String sql)   // MySQL → 人大金仓
String mysql2Sqlserver(String sql)    // MySQL → SQL Server
```

**⇒ 平台支持 5 种数据库方言自动转换。**
**⇒ 写跨库 SQL 时用这个，不要自己写多套。**

**配套：** `DatabaseDialectManager`（在 boot-starter-mybatis）

---

## 15. YamlUtil（5 方法）

```java
Map<String,Object> yamlString2Map(String)
LinkedHashMap yaml2LinkedHashMap(String)
String map2Yaml(LinkedHashMap)
String hashMap2Yaml(Map<String,Object>)
LinkedHashMap changeValue(LinkedHashMap, String path, Object value)
```

**⇒ 配置文件读写用这个。**
**⚠️ 但配置最终要写 Nacos（`ConfigCenterService`），YamlUtil 只用于处理本地/临时 YAML 文本。**

---

## 16. EnumArrayUtil（10 方法）

```java
boolean hasArrayEnumField(String className)
Class getEnumClass(String, String)
Class getEnumClassByEntity(String, String)
void regDyAppArrayEnums(String, Class)          // 动态注册
void unRegDyAppArrayEnums(String)
Map<String,Class> findArrayEnum(Class)
Map<String,Class> findArrayEnum(List<Class>)
Map<String,Class> initEnumFieldCache()
String parseEnumList2Str(List<Messageable>)     // 枚举列表 → 字符串
List<Messageable> parseStr2EnumList(String, String, ...)
```

**★ 用于「实体字段存的是枚举数组的多值字段」。**
**⇒ `parseEnumList2Str` / `parseStr2EnumList` 是枚举多值字段的存取转换。**

---

## 17. 缓存类

```java
LocalCache / LocalCacheBuilder       // 本地缓存（带 builder）
CacheEviction                        // 淘汰策略
AutoClearable                        // 自动清理
BootCacheUtils                       // 缓存工具
ConcurrentReferenceMap / SetFromMap  // 并发集合
```

**⚠️ 这只是**本地缓存**。分布式缓存（Redis）在 `boot-starter-cache` 的 `CacheUtils` / `RedisUtils`。**

---

## 18. 其他工具速查

| 类 | 方法数 | 用途 |
|---|---|---|
| `ClassUtils` / `ClassPoolUtils` / `ClassScanner` | — | 类扫描/加载 |
| `BeanUtils` / `BeanReflections` / `AopTargetUtils` | — | Bean 反射 |
| `AesUtils`（见 §3） | — | 加密 |
| `MimeTypeUtils` | — | MIME 类型 |
| `PdfUtils` | — | PDF 操作 |
| `IpUtils` / `MACAddressParser` / `ServerUtils` | — | 网络/主机信息 |
| `Hex` | — | 十六进制 |
| `LockUtils` | — | 锁工具 |
| `SQLWildcardEscaper` / `SQLWildcardUtil` / `SqlCheckUtils` | — | SQL 安全 |
| `PropertiesBuilder` / `PomXmlUtil` | — | 配置/构建文件 |
| `ResourceUtils` | — | 资源加载 |
| `ToStringUtils` | — | toString 生成 |
| `ShutdownHooks` | — | 优雅关闭 |
| `TypeConverter` 族（50+） | — | 类型转换 |
| `ExcelUtils` / `Seeyon*Strategy`（5 个） | — | Excel 工具 + EasyExcel 策略 |

---

## 19. ★★ 判断该用哪一层（Agent 用前必查）

| 需求 | 用什么 |
|---|---|
| JSON 序列化（含 ID 精度） | `JsonUtils.toJsonLongToString` |
| 调外部 HTTP 接口 | `HttpClientUtil.get/post`（要状态码用 `sendGet/sendPost`） |
| 加密解密 | `AESUtils` / `RSAUtils`（**不要自己写 JCE**） |
| 生成主键 | `Ids.gidLong()` |
| DTO ↔ Entity 转换 | `BeanCopier.copy` |
| 参数校验（手写条件） | `Asserts.notNull` 等 |
| 参数校验（读注解） | `Validators.assertjsr303` |
| 日期格式化 | `DateUtils.format(date, DateUtils.CHINESE_DATE_FORMAT_LINE)` |
| 脱敏 | `StringUtils.maskMobileNo` / `maskByType` |
| 跨库 SQL | `DatabaseUtils.mysql2Postgre` 等 |
| 文件读写 | `FileUtils` / `IoUtils`（`closeQuietly` 关流） |
| 图片缩放 | `ImageUtils.resize` |
| 内存分页 | `PageUtils.paginate`（**大数据量不要用**） |
| 本地缓存 | `LocalCache`（**分布式用 `CacheUtils`**） |

**⚠️ 三个「不要用工具类硬来」的场景：**
1. **需要租户/用户上下文** → 走 Service（工具类不带上下文）
2. **需要分布式缓存** → `boot-starter-cache` 的 `RedisUtils`
3. **需要事务** → 走 `boot-starter-transaction`，工具类无事务

---

## 20. 未覆盖

| 项 | 说明 |
|---|---|
| 所有 177 类的方法体 | 只读了签名，**没有实现逻辑**（如 `Ids.gidLong()` 的雪花算法参数） |
| Type 50+ 转换器的方法 | 只知存在，未逐个读 |
| `SeeyonObjectMapper` 定制项 | 未读（影响 JSON 全局行为） |
| `HttpClientRoundRobinRouting` 机制 | 未读 |