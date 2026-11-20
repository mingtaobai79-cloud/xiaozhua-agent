# U3 · `com.seeyon.boot.util` 工具类全表（176 个）

## Capability

**回答「平台自带的工具类有哪些、各干什么、哪个方法直接用」。**

给 Agent 用：写代码前**先来这里找**，别自己 `new SimpleDateFormat()` 或引第三方库。

**这些类是纯静态工具，不需要 `@Autowired`，直接 `类名.方法()`。**

## 数量声明

| 项 | 数 |
|---|---:|
| `com.seeyon.boot.util` 下类数（源） | **176** |
| 本格收录 | **176** |
| 差 | **0** |

> 本格数量由脚本 `gen_tools_index.py` 从 `interfaces-full.json` 直接生成，
> 源变则重跑，**不许手改行数**。

## 一、按用途分组速查

| 我要做什么 | 去哪个子包 | 类数 |
|---|---|---:|
| 对象拷贝 / Bean 操作 | `bean` | 55 |
| 根包工具（JsonUtils / StringUtils 等） | `(root)` | 37 |
| Excel 读写 | `excel` | 20 |
| HTTP 调用 | `http` | 18 |
| 加解密 / 摘要 | `encrypt` | 9 |
| 序列化 | `serialize` | 9 |
| 缓存 | `cache` | 7 |
| ID 生成 | `id` | 7 |
| 校验 | `validate` | 5 |
| jwt | `jwt` | 3 |
| qrcode | `qrcode` | 2 |
| teanant | `teanant` | 2 |
| 压缩 | `zip` | 2 |

## 二、全表（一行一个类）

### `com.seeyon.boot.util.bean` —— 对象拷贝 / Bean 操作（55 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `AbstractArrayTypeConverterSupport` | 3 | arrayValue() / conver() |
| 2 | `AbstractPrimitiveUtils` | 38 | value() / value() / value() |
| 3 | `AbstractTypeConverter` | 3 | getSupportedSourceTypes() / convert() / convert() |
| 4 | `AbstractTypeConverterUtils` | 5 | convert() / convertValue() / getArrayTypeConvert() |
| 5 | `ArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 6 | `BeanCopier` | 17 | copy() / copy() / copy() |
| 7 | `BeanReflections` | 40 | invokeGetter() / invokeGetter() / invokeGetterToString() |
| 8 | `BeanUtils` | 7 | getFieldValue() / setFieldValue() / generateGetterSetter() |
| 9 | `BigDecimalTypeConverter` | 5 | bigDecValue() |
| 10 | `BigIntegerTypeConverter` | 5 | bigIntValue() |
| 11 | `BooleanPrimitiveArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 12 | `BooleanPrimitiveTypeConverter` | 5 | booleanValue() |
| 13 | `BooleanTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 14 | `BytePrimitiveArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 15 | `BytePrimitiveTypeConverter` | 5 | byteValue() |
| 16 | `ByteTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 17 | `CharArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 18 | `CharTypeConverter` | 5 | charValue() |
| 19 | `CharacterTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 20 | `ConverterNotFoundException` | 3 | getSourceType() / getTargetType() / toString() |
| 21 | `DateTypeConverter` | 5 | dateValue() |
| 22 | `DoublePrimitiveArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 23 | `DoublePrimitiveTypeConverter` | 5 | doubleValue() |
| 24 | `DoubleTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 25 | `EnumTypeConverter` | 6 | enumValue0() / enumValue() |
| 26 | `FloatPrimitiveArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 27 | `FloatPrimitiveTypeConverter` | 5 | floatcharValue() |
| 28 | `FloatTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 29 | `IntArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 30 | `IntTypeConverter` | 5 | intValue() |
| 31 | `IntegerTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 32 | `ListTypeConverter` | 5 | listValue() |
| 33 | `LongPrimitiveArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 34 | `LongPrimitiveTypeConverter` | 5 | longValue() |
| 35 | `LongTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 36 | `QueueTypeConverter` | 5 | queueValue() |
| 37 | `SetTypeConverter` | 5 | setValue() |
| 38 | `ShortPrimitiveArrayTypeConverter` | 2 | getTargetType() / getSupportedSourceTypes() |
| 39 | `ShortPrimitiveTypeConverter` | 5 | shortValue() |
| 40 | `ShortTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 41 | `SimpleTypeConverterManager` | 14 | registerDefaultConverter() |
| 42 | `StringToDateConverter` | 2 | convert() / convert() |
| 43 | `StringTypeConverter` | 6 | stringValue() / stringValue() |
| 44 | `TimestampTypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 45 | `TypeConversionException` | 0 | — |
| 46 | `TypeConverter` | 4 | getTargetType() / getSupportedSourceTypes() / convert() |
| 47 | `TypeConverterManager` | 11 | getTypeConverter() / getTypeConverter() / register() |
| 48 | `AutoClearable` | 0 | — |
| 49 | `ConcurrentReferenceMap` | 29 | getHashCode() / notNull() / access$000() |
| 50 | `SetFromMap` | 17 | clear() / size() / isEmpty() |
| 51 | `AbstractFinalizablePhantomReference` | 0 | — |
| 52 | `AbstractFinalizableSoftReference` | 0 | — |
| 53 | `AbstractFinalizableWeakReference` | 0 | — |
| 54 | `FinalizableReference` | 1 | finalizeReferent() |
| 55 | `FinalizableReferenceQueue` | 10 | getThreadName() / getInstance() / getCleanUpThreads() |

### `com.seeyon.boot.util.cache` —— 缓存（7 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `CacheEviction` | 2 | values() / valueOf() |
| 2 | `LocalCache` | 9 | size() / isEmpty() / containsKey() |
| 3 | `LocalCacheBuilder` | 8 | defaultBuilder() / roundUpToPowerOf2() |
| 4 | `LocalCacheSerializer` | 3 | serialize() / deserialize() / serializedSize() |
| 5 | `LocalInnerCache` | 41 | put() / put() / addOrReplace() |
| 6 | `MonitorCache` | 2 | incrementConsumer() / incrementProvider() |
| 7 | `SeeyonCache` | 8 | size() / isEmpty() / containsKey() |

### `com.seeyon.boot.util.encrypt` —— 加解密 / 摘要（9 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `AESUtils` | 8 | encrypt() / encrypt() / encrypt() |
| 2 | `DESUtils` | 4 | encrypt() / encrypt() / decrypt() |
| 3 | `MD5Utils` | 2 | md5() / md5() |
| 4 | `RSAUtils` | 10 | generateKey() / keyEncrypt() / encrypt() |
| 5 | `SHA1Utils` | 3 | encrypt() / encrypt() / encrypt2Byte() |
| 6 | `SHA256Utils` | 4 | encrypt() / encrypt() / encrypt2Byte() |
| 7 | `SM2Utils` | 9 | generateKey() / getPublicKey() / getPrivateKey() |
| 8 | `SM3Utils` | 6 | encrypt() / encrypt() / encrypt2Byte() |
| 9 | `SM4Utils` | 10 | encrypt() / encrypt2Byte() / encrypt2Byte() |

### `com.seeyon.boot.util.excel` —— Excel 读写（20 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `ExcelDataHandler` | 1 | handle() |
| 2 | `ExcelListener` | 5 | invoke() / setExcelDataHandler() / invoke() |
| 3 | `ExcelUtils` | 19 | readExcel() / readSheetCount() / readExcel() |
| 4 | `ExcelColumn` | 2 | value() / width() |
| 5 | `ExcelColumnWidth` | 1 | value() |
| 6 | `ExcelContentFontStyle` | 7 | fontName() / fontHeightInPoints() / italic() |
| 7 | `ExcelContentStyle` | 17 | dataFormat() / hidden() / locked() |
| 8 | `ExcelHeadFontStyle` | 7 | fontName() / fontHeightInPoints() / italic() |
| 9 | `ExcelHeadStyle` | 17 | dataFormat() / hidden() / locked() |
| 10 | `ExcelConstants` | 0 | — |
| 11 | `ExcelEnum` | 2 | values() / valueOf() |
| 12 | `SheetModel` | 24 | build() |
| 13 | `CellStyle` | 42 | getDataFormat() / getDataFormatStr() / isHidden() |
| 14 | `DataValidity` | 30 | getColNum() / getFirstRow() / getLastRow() |
| 15 | `FontStyle` | 18 | getFontName() / getFontHeightInPoints() / isItalic() |
| 16 | `SheetStyle` | 18 | getGlobalColumnWidth() / getHeadStyle() / getHeadFontStyle() |
| 17 | `SeeyonCellDataValidityStrategy` | 3 | beforeSheetCreate() / afterSheetCreate() / createDataValidation() |
| 18 | `SeeyonColumnWidthStyleStrategy` | 1 | columnWidth() |
| 19 | `SeeyonHiddenSheetStrategy` | 1 | afterWorkbookDispose() |
| 20 | `SeeyonRowHeightStyleStrategy` | 4 | setHeadColumnHeight() / setContentColumnHeight() / setHeadRowHeight() |

### `com.seeyon.boot.util.http` —— HTTP 调用（18 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `HttpClientUtil` | 93 | create() / get() / get() |
| 2 | `RestServiceUtil` | 4 | getSingleResponse() / getListResponse() / getPageResponse() |
| 3 | `HCB` | 6 | custom() |
| 4 | `HttpConfig` | 43 | custom() |
| 5 | `HttpHeader` | 4 | custom() |
| 6 | `HttpMethods` | 4 | values() / valueOf() |
| 7 | `HttpResult` | 9 | getHeaders() / getResult() / setResult() |
| 8 | `SSLs` | 3 | custom() |
| 9 | `Utils` | 5 | checkHasParas() / map2HttpEntity() / removeContentTypeCharset() |
| 10 | `HttpVersionEnum` | 3 | values() / valueOf() |
| 11 | `HttpProcessException` | 0 | — |
| 12 | `HttpClientRoundRobinRouting` | 14 | choose() / get() / get() |
| 13 | `HttpClientRouteConfig` | 1 | httpClientRouteHeartbeat() |
| 14 | `HttpClientRouteHeartbeat` | 2 | check() |
| 15 | `RoundRobinRoute` | 3 | getPosition() / getInstances() / setInstances() |
| 16 | `HttpClientMetrics` | 3 | success() / fail() |
| 17 | `FileStreamUploadModel` | 12 | getFileName() / getStream() / getInputName() |
| 18 | `FileUploadModel` | 12 | getFileName() / getFilePath() / getInputName() |

### `com.seeyon.boot.util.id` —— ID 生成（7 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `IdGeneratorProperties` | 4 | getEngine() / isAbsolute() / setEngine() |
| 2 | `IdentifierGenerator` | 3 | generateLong() / generateString() / analyze() |
| 3 | `Ids` | 8 | gSwIdString() / gidString() / gidLong() |
| 4 | `NetAddressIdWorker` | 4 | generateLong() / generateString() / analyze() |
| 5 | `SnowflakeIDElement` | 8 | getDate() / setDate() / getCenterId() |
| 6 | `SnowflakeIDGenerator` | 12 | setAbsolute() / getWorkerId() / getSequence() |
| 7 | `UUIDGenerator` | 4 | generateLong() / generateString() / analyze() |

### `com.seeyon.boot.util.jwt` —— jwt（3 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `JwtProperties` | 4 | getAccessTokenExp() / setAccessTokenExp() / setReLoginTime() |
| 2 | `JwtUtils` | 8 | generateJwt() / generateJwt() / generateJwt() |
| 3 | `SecretProperties` | 4 | getSecret() / licenseChange() / setLicenseKey() |

### `com.seeyon.boot.util.qrcode` —— qrcode（2 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `QrCodeUtils` | 10 | createImage() / resetWhiteBorder() / insertLogoImage() |
| 2 | `QrCodeParam` | 18 | getLogoPath() / getLogoWidth() / getLogoHeight() |

### `com.seeyon.boot.util.serialize` —— 序列化（9 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `DateStrFormat` | 1 | parse() |
| 2 | `EnumJsonDeserializer` | 5 | deserialize() / find() / getEnumClass() |
| 3 | `EnumJsonSerializer` | 5 | serialize() / handledType() / serializeWithType() |
| 4 | `EnumToCodeSerializer` | 3 | serialize() / handledType() / serialize() |
| 5 | `FstSerializer` | 6 | serialize() / serializeToStr() / deserialize() |
| 6 | `JacksonSerializer` | 6 | deserialize() / deserialize() / serialize() |
| 7 | `KryoSerializer` | 8 | destroy() / serialize() / serializeForObjectArray() |
| 8 | `SeeyonPropertyNamingStrategy` | 3 | getNameByMethod() / nameForGetterMethod() / nameForSetterMethod() |
| 9 | `SerializeUtils` | 6 | serialize() / serializeToStr() / deserialize() |

### `com.seeyon.boot.util.teanant` —— teanant（2 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `BootCacheUtils` | 2 | getCacheKeyWithoutTenantIdAndAppName() / getCacheKeyWithoutTenantId() |
| 2 | `TenantUtils` | 7 | getRedisTemplate() / getTenantIdByName() / getTenantInfo() |

### `com.seeyon.boot.util.validate` —— 校验（5 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `HibernateValidatorFactory` | 2 | getInstance() / clearCache() |
| 2 | `I18nMessageInterpolator` | 3 | getMessageRepository() / interpolate() / interpolate() |
| 3 | `SeeyonLocalVariableTableParameterNameDiscoverer` | 5 | getParameterNames() / getParameterNames() / doGetParameterNames() |
| 4 | `SeeyonParameterNameDiscoverer` | 1 | clearCache() |
| 5 | `Validators` | 6 | assertEmpty() / assertjsr303() / assertjsr303() |

### `com.seeyon.boot.util.zip` —— 压缩（2 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `ZipReader` | 10 | of() / of() / checkZipBomb() |
| 2 | `ZipWriter` | 13 | of() / of() / getZipOutputStream() |

### `com.seeyon.boot.util.` —— 根包工具（JsonUtils / StringUtils 等）（37 个）

| # | 类 | 方法数 | 代表方法 |
|---:|---|---:|---|
| 1 | `AopTargetUtils` | 3 | getTarget() / getCglibProxyTargetObject() / getJdkDynamicProxyTargetObject() |
| 2 | `Asserts` | 26 | between() / between() / notEmpty() |
| 3 | `ClassPoolUtils` | 3 | getClassPool() / clear() / clearRubbish() |
| 4 | `ClassScanner` | 18 | scan() / scan() / scan() |
| 5 | `ClassUtils` | 10 | getGenericClass() / getGenericClass() / getSuperClassGenricType() |
| 6 | `ComponentUrlUtil` | 6 | addUrl() / getComponentUrl() / isComponentUrl() |
| 7 | `DatabaseUtils` | 47 | mysqlToDm() / mysql2Oracle() / mysql2Postgre() |
| 8 | `DateUtils` | 60 | registerPattern() / unRegisterPattern() / sort() |
| 9 | `EnumArrayUtil` | 12 | hasArrayEnumField() / getEnumClass() / getEnumClassByEntity() |
| 10 | `FileUtils` | 21 | tempFile() / tempFile() / tempFile() |
| 11 | `Hex` | 9 | append() / append() / append() |
| 12 | `ImageUtils` | 10 | resize() / resize() / resize() |
| 13 | `IoUtils` | 28 | toString() / toString() / toString() |
| 14 | `IpUtils` | 21 | ip2Long() / long2Ip() / isPublicIpv4() |
| 15 | `JsonUtils` | 27 | main() / toJsonThrowError() / toJson() |
| 16 | `LockUtils` | 2 | tryLock() / releaseLock() |
| 17 | `MACAddressParser` | 1 | parse() |
| 18 | `MD5` | 4 | getMD5String() / getMD5String16() / hash() |
| 19 | `MimeTypeUtils` | 2 | getMimeType() / getDefaultMimeType() |
| 20 | `PageUtils` | 3 | paginate() / paginateData() / paginateList() |
| 21 | `PdfUtils` | 2 | parsePdf() / parsePdf() |
| 22 | `PomXmlUtil` | 14 | getGroupId() / getVersion() / getArtifactId() |
| 23 | `PropertiesBuilder` | 4 | buildProperties() / buildProperties() / build() |
| 24 | `ResourceUtils` | 12 | getAllClassPathResourceStr() / getAppClassPathResourceStr() / getAllClassPathResourceListStr() |
| 25 | `SQLWildcardEscaper` | 7 | getInstance() / getInstance() |
| 26 | `SQLWildcardUtil` | 6 | initEscape() / escape() / requireEscape() |
| 27 | `SeeyonDeserializationContext` | 6 | copy() / createInstance() / createDummyInstance() |
| 28 | `SeeyonObjectMapper` | 6 | _newReader() / _newReader() / _findRootDeserializer() |
| 29 | `SeeyonObjectReader` | 4 | getBaseObjectMapper() / _findRootDeserializer() / _findTreeDeserializer() |
| 30 | `SeeyonSerializerProvider` | 5 | copy() / withCaches() / createInstance() |
| 31 | `ServerUtils` | 2 | isPortUsing() / isActive() |
| 32 | `ShutdownHooks` | 12 | registShutdownHook() / registShutdownHook() / executeAllShutdownHooks() |
| 33 | `SqlCheckUtils` | 4 | injectSqlRedisKey() / veryLongSqlRedisKey() / isInject() |
| 34 | `StringUtils` | 35 | first() / getSimpleNameFromFullName() / toPinYinFirstSpell() |
| 35 | `ToStringUtils` | 44 | toString() / getPackageName() / toString() |
| 36 | `YamlUtil` | 9 | yamlString2Map() / switchToMap() / yaml2LinkedHashMap() |
| 37 | `ZipUtils` | 17 | zip() / zip() / zip() |

## 三、最常用的 12 个（按实际调用频次）

| 类 | 典型用法 | 说明 |
|---|---|---|
| `JsonUtils` | `JsonUtils.fromJson(json, Cls.class)` / `toJson(obj)` | **没有 `toBean`**，反序列化是 `fromJson` |
| `BeanCopier` | `BeanCopier.copy(src, Target.class)` | 比 BeanUtils 快，平台自己用它 |
| `Ids` | `Ids.gidLong()` / `gidString()` / `uuidString()` | **没有 `newId()`**；`analyzeDate(id)` 可反解时间 |
| `StringUtils` | `StringUtils.isBlank(s)` | 判空为主 |
| `DateUtils` | `DateUtils.format(d, pattern)` | 替代 SimpleDateFormat |
| `HttpClientUtil` | `HttpClientUtil.post(url, body)` | 平台封装，别引 OkHttp |
| `AESUtils` | `AESUtils.encrypt(...)` | 加解密（在 `encrypt` 子包） |
| `MD5Utils` | `MD5Utils.md5(s)` | 摘要（`encrypt` 子包）；根包另有 `MD5` |
| `FileUtils` | `FileUtils.readToString(f)` | 文件读写 |
| `ZipUtils` | `ZipUtils.zip(...)` | 压缩 |
| `BeanReflections` | `BeanReflections.getFieldValue(o, name)` | 反射取值（`bean` 子包） |
| `Validators` | `Validators.validate(obj)` | 校验（`validate` 子包）；根包另有 `Asserts` |

**★ 这 12 个的名称全部在 `interfaces-full.json` 里逐个核对过（2026-11-20）。**

## 四、Known Constraints

| # | 约束 |
|---|---|
| 1 | **这些类是静态工具，不要 `@Autowired`** —— 它们不是 Spring Bean |
| 2 | **`JsonUtils` 没有 `toBean`**，反序列化用 `fromJson(json, Class)` |
| 3 | **`Ids` 没有 `newId()`**，用 `gidLong()` / `gidString()` / `uuidString()` |
| 4 | **平台 id 必须用 `Ids`** —— 自己生成会与平台雪花 id 冲突 |
| 5 | **对象拷贝用 `BeanCopier.copy`** —— 平台 `updateBase` 偏移 768 就用它 |
| 6 | **JSON 一律用 `JsonUtils`**，不要引 Jackson/Fastjson 新实例 |

## 五、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 176 个类的完整清单与代表方法 | `interfaces-full.json`（`boot-core-5.3.600.jar` javap 全量） | **VERIFIED_STATIC_BYTECODE** |
| `JsonUtils` 有 `fromJson` 无 `toBean` | 同索引，方法名逐条核对 | **VERIFIED_STATIC_BYTECODE** |
| `Ids` 有 `gidLong`/`gidString`/`uuidString` 无 `newId` | 同上 | **VERIFIED_STATIC_BYTECODE** |
| `BeanCopier.copy` 被平台自身使用 | `BaseEntityCurdService.updateBase` 偏移 768 | **VERIFIED_STATIC_BYTECODE** |
| 各类的真实调用场景 | 未逐个实测 | **UNVERIFIED** |

## 六、给 Agent 的判据

```
问「平台有没有现成的 xxx 工具」
  → 先查本格 §二 全表（176 个，按子包分组）
  → 别自己写，别引第三方

问「JSON 怎么转对象」
  → JsonUtils.fromJson(json, MyDto.class)
  → 不是 toBean（不存在）

问「id 怎么生成」
  → Ids.gidLong()
  → 不是 newId（不存在）

问「对象怎么拷贝」
  → BeanCopier.copy(src, Target.class)

问「这些类能注入吗」
  → 不能。全是静态工具，直接 类名.方法()
```
