# 缓存与流水号（boot-starter-cache 50 类 + boot-starter-serialnumber 85 类）

> 数据源：`boot-starter-cache-5.3.600.jar` / `boot-starter-serialnumber-5.3.603.jar`
> 等级：`VERIFIED_STATIC_BYTECODE`（javap 全部方法签名 + DTO 字段实测）
> ⚠️ 用户环境 5.3.517，本机 cache 5.3.600 / serialnumber 5.3.603

---

# 第一部分：缓存（boot-starter-cache）

## 1. ★ 50 类里的三分法

| 分组 | 类数 | 是什么 |
|---|---:|---|
| `redis.embedded.*` | **28** | **嵌入式 Redis**（测试/单体部署用，不是业务代码） |
| `util.*` | **4** | **★ 真正要用的：CacheUtils / RedisUtils / TenantUtils** |
| `share.*` | 4 | CacheProxy / CacheRedis / LocalCacheMap / RedisCacheMap |
| `declarative.*` | 7 | Spring Cache 抽象（DefaultCache / CacheManager） |
| `limit.*` | 2 | 限流（RateChecker / RedisRateChecker） |
| `inspection.*` / `meter.*` / `init.*` | 6 | 巡检 / 指标 / 租户初始化 |
| 根包 | 4 | AutoConfiguration / Properties / Serializer |

**⇒ **真正的 API 只有 `RedisUtils`（12 方法）和 `CacheUtils`（6 方法）两个类**，其余是基础设施。**

## 2. ★★★ RedisUtils（12 方法）—— 分布式缓存主入口

```java
// 写
static boolean set(String key, Object value)
static boolean set(String key, Object value, long expire)     // 带过期

// 读
static Object getKey(String key)                              // ★ 注意方法名是 getKey 不是 get

// 存在性
static boolean hasKey(String key)

// 过期
static boolean expire(String key, long seconds)
static boolean expire(String key, long timeout, TimeUnit unit)

// 删（三种入参）
static void del(String... keys)
static void del(List<String> keys)
static void del(Set<String> keys)

// 常量
static final long DEFAULT_EXPIRE
static final TimeUnit TIME_UNIT
```

**★★ 关键约束：`RedisUtils` 只有 `String` / `Object` 两种值形态。**
**⇒ 复杂对象要自己序列化（用 `JsonUtils.toJsonLongToString`）再 set。**

**★ `DEFAULT_EXPIRE` / `TIME_UNIT` 是平台约定的默认过期时间 —— 不确定该设多久就用这个，别自己定。**

## 3. ★★ CacheUtils（6 方法）—— ★ 缓存 key 的构造规范

```java
static String getCompleteCacheKey(String appName, String key)
static String getCompleteCacheKeyWithBuildVersion(String, String, String)  // 带构建版本
static String getCompleteCacheKeyWithoutTenantId(String, String)
static String getCompleteCacheKeyWithoutAppName(String, String)
static String getCacheKeyWithoutTenantIdAndAppName(String, String)
```

**★★★ 这是本节最重要的发现：平台的缓存 key **强制包含租户 + 应用**。**

**推测的 key 结构（基于方法名，未读方法体）：**
```
{tenantId}:{appName}:{key}                     ← getCompleteCacheKey
{tenantId}:{appName}:{buildVersion}:{key}      ← WithBuildVersion
{appName}:{key}                                ← WithoutTenantId
{tenantId}:{key}                               ← WithoutAppName
{key}                                          ← WithoutTenantIdAndAppName
```

**⇒ 直接用 `RedisUtils.set("myKey", v)` 会导致**跨租户串数据**。**
**⇒ 正确做法：`RedisUtils.set(CacheUtils.getCompleteCacheKey(appName, "myKey"), v)`**

**⚠️ 但 `RedisUtils` 是否内部自动加前缀，我没读方法体，**不确定**。**

## 4. ★ 租户（TenantUtils，5 方法）

```java
static Long getTenantIdByName(String tenantName)              // 名称 → ID
static TenantInfo getTenantInfo()                             // 当前租户
static TenantInfo getTenantInfo(Long tenantId)
static List<TenantInfo> getAllActiveTenant()                  // 所有活跃租户
```

**★ `getAllActiveTenant` 是遍历租户做批量任务的入口。**

## 5. Spring Cache 抽象（declarative 包）

**平台实现了标准 Spring Cache，可以用注解：**

```java
// DefaultCache 实现 org.springframework.cache.Cache
String getName()
Object getNativeCache()
ValueWrapper get(Object key)
<T> T get(Object key, Class<T>)
<T> T get(Object key, Callable<T>)          // ★ 缓存未命中则执行 Callable
void put(Object, Object)
ValueWrapper putIfAbsent(Object, Object)
void evict(Object key)                      // ★ 失效单条
void clear()                                // ★ 清空整个 cache
Object doit(Object, BiFunction<...>)        // ★ 原子操作
```

**⇒ 所以可以用标准注解：**
```java
@Cacheable("xxx")       // 读缓存
@CachePut("xxx")        // 写缓存
@CacheEvict("xxx")      // 失效
```

**★ `CtpLocalCacheManager` 说明：平台有**本地缓存 + Redis 两级**设计。**

## 6. ★ 限流（RateChecker）

```java
// 接口
boolean check(String key, Integer limit, Long windowSeconds)

// 实现：RedisRateChecker（基于 Redis 的分布式限流）
```

**⇒ 限流已内建，不用自己写令牌桶。**

## 7. share 包（4 个）

| 类 | 用途 |
|---|---|
| `CacheProxy` | 动态代理缓存方法（`invoke` + `createCacheMap`） |
| `CacheRedis` | Redis 缓存（set / setNx / get / delete） |
| `LocalCacheMap` | 本地 Map（size/isEmpty/containsKey/get/put/putAll/remove/clear） |
| `RedisCacheMap` | Redis Map（put/putAll/remove/clear/replace） |

**★ `CacheRedis.setNx(key, value, timeout, unit)` —— SETNX，**分布式锁的基础**。**

## 8. ★ 缓存使用判断

| 需求 | 用什么 |
|---|---|
| 简单 KV 存取 | `RedisUtils.set/getKey` |
| 要 Spring 注解 | `@Cacheable` / `@CacheEvict`（平台已配） |
| 要本地缓存（单机） | `LocalCacheMap` / `LocalCache`（boot-core） |
| 分布式锁 | `CacheRedis.setNx` |
| 限流 | `RedisRateChecker.check` |
| 租户信息 | `TenantUtils` |
| ★ **构造 cache key** | **`CacheUtils.getCompleteCacheKey`（防跨租户）** |

**⚠️ 三个坑：**
1. **`RedisUtils.getKey` 方法名容易写成 `get`** —— 编译不过才发现
2. **不加租户前缀 → 跨租户串数据**
3. **`RedisUtils` 只有 String/Object，复杂对象要序列化**

---

# 第二部分：流水号（boot-starter-serialnumber）

## 9. ★★★ 流水号的数据模型（这是核心）

**5 张表 / 5 个实体：**

```
SerialScheme    ← 编号规则（scheme = 方案）
  ├─ SerialSection    ← 组成段（每段是常量/日期/流水号/字段）
  ├─ SerialCondition  ← 生效条件（建单/发布时用哪个方案）
  └─ SerialCurrent    ← 当前值（每个方案的当前流水）
       └─ SerialRange ← 号段（预占/未使用号）
SerialHistory   ← 历史（用过的号）
```

**⇒ 这是经典的「号段模式」设计，不是每次 count 一条。**

## 10. ★★★ SerialSchemeDto 字段（编号规则定义）

```java
Long    id
Integer version
String  code                    // 规则编码
String  name                    // 规则名称
String  appGuid                 // ★ 所属应用
String  appId
String  entityFullName          // ★ 绑定到哪个实体（用于自动编号）
String  orgId                   // ★ 组织隔离
Integer totalSize               // ★ 总位数
Boolean createUnused            // ★ 是否预生成未使用号
Boolean unusedPriority          // ★ 优先使用未使用号
Integer sortNum
Boolean containFlow             // ★ 是否含流程（流程中不占号？）
Boolean active                  // ★ 启用
SerialResetRuleEnum serialResetRule  // ★ 重置规则
Boolean editEntity              // 允许编辑实体
Boolean deleteFlag
Boolean preset                  // 预置
Boolean reset                   // 允许重置
SerialRuleTypeEnum serialType   // ★ 规则类型（APP/BIG/SMALL）
List<SerialSectionDto>   serialSectionDtoList      // ★ 各段定义
List<SerialConditionDto> serialConditionDtoList    // ★ 条件
String sourceAppName
String serialAppName
```

**★★ 关键字段解读：**

| 字段 | 作用 |
|---|---|
| `entityFullName` | **把规则绑到实体的某个字段 → 建单时自动生成编号** |
| `totalSize` | **编号总位数（不够就报错或截断）** |
| `createUnused` | **预生成未使用号（提升性能，避免并发抢）** |
| `unusedPriority` | **优先用未使用号（回收后可复用）** |
| `containFlow` | **是否走流程 —— 走流程的单据编号时机不同** |
| `serialResetRule` | **每年/每月/每日重置** |
| `orgId` | **组织级隔离（不同组织可以不同编号）** |

## 11. ★★★ SerialSectionDto 字段（一段怎么定义）

```java
Long   id
Long   serialSchemeId
Integer size                   // ★ 本段位数
SerialTypeEnum type            // ★ 段类型（关键）
String value                   // ★ 值（常量值 / 字段名 / 变量名）
String caption                 // 显示名
FillTypeEnum fillType          // ★ 补位方向（LEFT/RIGHT/NONE）
CutTypeEnum  cutType           // ★ 截断方向（LEFT/RIGHT/NONE）
String fillChar                // ★ 补位字符（如 '0'）
Boolean dateType               // ★ 是否日期段
String datePattern             // ★ 日期格式（如 yyyyMM）
Boolean show                   // 是否显示
Boolean flow                   // 是否随流程
Boolean increase               // ★ 是否递增
Integer sectionRank            // ★ 顺序（关键）
Long   serialCurrent           // 当前值
ActionType actionType          // 动作类型（boot 框架共用枚举）
Boolean deleteFlag
String sourceAppName
Long   startValue              // ★ 起始值
Long   endValue                // ★ 结束值
```

**★★ `SerialTypeEnum` 四种段类型（决定 `value` 填什么）：**

| 枚举 | value 填什么 | 例子 |
|---|---|---|
| `CONSTANT` | 字面常量 | `"PO"` → 输出 PO |
| `CONTEXT` | 上下文变量 | `"currentUser.name"` 等 |
| `ENTITY` | 实体字段 | 实体属性名 → 取字段值 |
| `SERIAL` | **流水号（自增）** | `increase=true` + `startValue/endValue` |

**⇒ 一个编号 = 多段拼接。例：`PO` + `yyyyMM` + `0001` = `PO2026110001`**

**★ `FillTypeEnum` 补位：`LEFT`（左补）/ `RIGHT` / `NONE` + `fillChar='0'`**
```
size=4, fillType=LEFT, fillChar='0'  →  1 变成 0001
```

**★ `CutTypeEnum` 截断：超过 size 时从哪边截**
```
size=2, cutType=RIGHT  →  "ABCD" 变 "AB"
```

## 12. ★★ 六个枚举全清单

| 枚举 | 值 | 含义 |
|---|---|---|
| **`SerialTypeEnum`** | CONSTANT / CONTEXT / ENTITY / SERIAL | 段类型 |
| **`SerialResetRuleEnum`** | NONE / YEAR / MONTH / DAY | 重置周期 |
| **`SerialRuleTypeEnum`** | APP / BIG / SMALL | 规则类型（应用级/大号段/小号段） |
| **`FillTypeEnum`** | LEFT / RIGHT / NONE | 补位方向 |
| **`CutTypeEnum`** | LEFT / RIGHT / NONE | 截断方向 |
| **`SerialRangeTypeEnum`** | RESERVE / UNUSED | 号段类型（预占/未使用） |

## 13. ★★ SerialConditionDto（条件 —— 什么时候用这个规则）

```java
Long   id
Long   serialSchemeId
Long   entityId
String entityFullName
String createExpression        // ★ 建单时的表达式
String releaseExpression       // ★ 发布时的表达式
```

**★★ 两个表达式是关键：**
```
createExpression   新建单据时，用什么变量值生成号
releaseExpression  发布单据时，用什么变量值生成号
```

**⇒ 同一实体在不同场景可以用不同编号规则，由表达式判断。**

**★ `SerialConditionAppService.evalExpression` 用于**试算表达式**（配置时预览）。**

## 14. ★★★ SerialNumberAppService（14 方法）—— 业务调用入口

**全部是 `SingleRequest/Response` 形态（Dubbo / @Autowired 通用）：**

```java
// 取号（四种）
SingleResponse<String> getSerialNumber(SingleRequest<SerialNumberDto>)
SingleResponse<String> getSerialNumberByCondition(SingleRequest<SerialNumberConditionDto>)
ListResponse<String>   batchSerialNumber(SingleRequest<SerialNumberBatchDto>)   // ★ 批量
SingleResponse<String> getSerialNumberForUdc(SingleRequest<SerialSchemeExtendDto>)  // ★ UDC 专用

// 预览（不占号）
SingleResponse<String> previewSerialNumber(SingleRequest<SerialNumberDto>)

// 改号 / 重置
SingleResponse<Boolean> updateSerialNumber(SingleRequest<SerialUpdateNumberDto>)
SingleResponse<Boolean> resetSerialNumber(SingleRequest<SerialResetDto>)
SingleResponse<Boolean> resetSerialNumberByAppId(SingleRequest<...>)

// 回收
SingleResponse<Boolean> recoverSerialNumber(SingleRequest<UnusedRecoverSerialDto>)
SingleResponse<Integer> setNoRecoverSerialNumber(SingleRequest<...>)   // ★ 设为不可回收

// 当前值维护
SingleResponse<Long> createOrUpdateSerialCurrent(SingleRequest<...>)
ListResponse<SerialCurrentDto>  selectSerialCurrent(...)
PageResponse<SerialCurrentDto>  selectSerialCurrentByPage(...)
```

**★★ `getSerialNumberForUdc` 是**给 UDC 用的专用入口**，说明 UDC 取号走这条线。**
**★★ `previewSerialNumber` 只预览不占号 —— 表单上「预览编号」用它。**
**★★ `batchSerialNumber` 批量取号 —— 大数据量导入时必须用，不然一个个取会慢死。**

## 15. ★ 配置侧（SerialSchemeAppService，18 方法）

```java
SingleResponse<Long>    create(SingleRequest<SerialSchemeDto>)
SingleResponse<Long>    createEasyScheme(SingleRequest<SerialEasySchemeDto>)   // ★ 简易创建
SingleResponse<Integer> update(SingleRequest<SerialSchemeDto>)
SingleResponse<Integer> updateActive(SingleRequest<SerialSchemeActiveDto>)     // ★ 启停
SingleResponse<Integer> updatePresetBatch(ListRequest<...>)                    // 批量预置
SingleResponse<Integer> deleteById / deleteByIds / runTimeDeleteById
SingleResponse<SerialSchemeDto>       selectById / selectByCodeAndAppId
ListResponse<SerialSchemeDto>         selectByAppId / selectByCode / selectByIds
PageResponse<SerialSchemeDto>         selectPageByCondition
SingleResponse<Integer> schemeCopy(SingleRequest<SerialSchemeCopyDto>)         // ★ 复制规则
SingleResponse<Integer> getMaxSortNumByAppId
```

**★ `createEasyScheme` —— 简易方案创建，说明有「快速配置编号」的简化入口。**
**★ `schemeCopy` —— 复制规则（跨应用复制编号规则）。**

## 16. ★ 号段管理（SerialRangeAppService，13 方法）

```java
create / createUnused                 建号段 / 未使用号段
createBatchUnused                     批量建未使用号
createUnusedBySerialNumber            按具体号建未使用
recoverNumber                          ★ 回收号码
updateForbiddenFlag                   禁用标记
deleteById / deleteByIds
selectById / selectPage
```

**★ `recoverNumber` 是「单据作废后号码回收」的入口，配合 `unusedPriority` 复用。**

## 17. ★ SerialNumberService（26 方法）—— 内部实现（不该直接调）

**关键方法（理解机制用）：**

```java
String getSerialNumber(SerialNumberDto)
String getSerialNumberByCache(SerialNumberDataDto)   // ★ 缓存路径
String getCurrentNumberByInitCache(Long, String)     // ★ 初始化缓存
String getSerialNumber(SerialSchemeDto, ...)
String invokeGetSerialNumberForUdc(SerialSchemeExtendDto)   // 真正调 UDC

void preInitSerialNumber(...)                        // ★ 预初始化
void preProductNumber(...)                           // ★ 预生产号
Long consumeUnusedSerialNumber(String)               // ★ 消费未使用号
Pair<List<Long>,Integer> consumeUnusedSerialNumbers(...)  // 批量
Boolean produceUnusedSerialNumber(String, Long, Long)     // ★ 生产未使用号
Boolean delUnusedSerialNumber(String, Long)
Boolean updateSerialNumber(SerialUpdateNumberDto)
Boolean resetSerialNumber(SerialResetDto)
void recoveryUnusedSerial(UnusedRecoverSerialDto)
```

**★★ 性能机制：**
```
preProductNumber        → 预生产一批号到「未使用池」
consumeUnusedSerialNumber → 从池里取，取不到才走 DB
```
**⇒ 这就是「createUnused / unusedPriority」的实现 —— **用空间换并发性能**。**

**★ `getSerialNumberByCache` —— 走缓存的取号路径。**

## 18. ★ SerialNumberUtil（17 方法，静态）

```java
static String getSerialSchemePrefixKey(String, String)      // 缓存 key
static String getPreProdSerialNumberKey(Long, String)
static String getSerialNumberUnusedKey()
static String getSerialNumberHistoryKey()
static String getSerialNumberHistoryHashKey(Long, String)
static String getNewKey(Long, String)
static String getIncrKey(SerialSchemeDto, Map)
static List<SystemPresetVariableDto> getListSystemVariables(...)   // ★ 系统变量清单
static void initOldContext(SerialSchemeDto, Map<String,Object>)    // ★ 初始化上下文
static String getVariableValue(SerialSchemeDto, ...)
static String redisKeyAddTenantId(String)                    // ★ 加租户前缀
static String resolveSerialNumber(String, SerialNumberDataDto)  // ★ 解析编号
static String fillIn(String, SerialSectionDto)               // ★ 补位实现
static long getSerialNumberMaxValue(SerialSectionDto)
static String fullNameToAppName(String)
```

**★★ `getListSystemVariables` —— 系统预设变量清单（编号里能引用哪些变量）。**
**★ `redisKeyAddTenantId` —— 与 `CacheUtils` 一样，缓存 key 必须带租户。**

## 19. ★ 扩展点（SerialSchemaExtendService）

```java
Object serialBeforeCreate(SerialBeforeCreateDto<...>)   // ★ 建号前钩子
Object serialBeforeUpdate(SerialBeforeUpdateDto<...>)   // ★ 更新前钩子
```

**⇒ 这是**标准 SPI 扩展点**，可以在取号前改值。**
**★ 这是「自定义微流程之外」的另一种扩展形态。**

## 20. ★★★ 完整编号生成流程（基于以上结构推断）

```
① 单据新建 / UDC 取号
    ↓ SerialNumberAppService.getSerialNumber(SerialNumberDto)
    ↓ SerialNumberService.getSerialNumber
② 找到方案
    ├─ entityFullName + orgId + appId → SerialScheme
    ├─ 有多个方案 → SerialCondition 的 createExpression 判定
③ 拼编号
    for (section in serialSectionDtoList by sectionRank) {
        CONSTANT → value 直接拼
        CONTEXT  → 从上下文取变量
        ENTITY   → 从实体字段取值
        SERIAL   → 从 SerialCurrent 取当前值然后 +1
                   （先试未使用池 → 再试 DB）
        apply fillType / fillChar / size / cutType
    }
④ 校验 totalSize
⑤ 更新 SerialCurrent，可能触发 produceUnusedSerialNumber
⑥ 写 SerialHistory
```

**⚠️ 以上 ②~⑥ 是**基于字段和方法的推断**，`resolveSerialNumber` 的方法体我没读。**
**⇒ 等级：`UNVERIFIED`（结构确定，执行细节未验证）。**

## 21. ★ 流水号使用判断

| 需求 | 接口 |
|---|---|
| 单据自动编号 | `SerialSchemeAppService.create` + `entityFullName` 绑定 |
| 表单预览编号 | `SerialNumberAppService.previewSerialNumber` |
| 实际取号 | `SerialNumberAppService.getSerialNumber` |
| UDC 取号 | `SerialNumberAppService.getSerialNumberForUdc` |
| 批量取号 | `SerialNumberAppService.batchSerialNumber` |
| 作废回收 | `SerialNumberAppService.recoverSerialNumber` |
| 编号重置 | `SerialNumberAppService.resetSerialNumber` |
| 取号前改值 | `SerialSchemaExtendService.serialBeforeCreate` |
| 条件判断 | `SerialConditionDto.createExpression` / `releaseExpression` |

## 22. ★ 编号配置示例（把字段翻译成配置）

**要生成 `PO2026110001`（PO + 年月 + 4位流水）：**

```
SerialSchemeDto:
  code            = "PO_SERIAL"
  name            = "采购订单编号"
  entityFullName  = "xxx.PurchaseOrder"
  totalSize       = 10
  active          = true
  serialResetRule = MONTH        // 每月重置
  serialType      = APP
  createUnused    = true         // 预生成
  unusedPriority  = true         // 优先用未使用

  serialSectionDtoList = [
    { sectionRank:1, type:CONSTANT, value:"PO",    size:2, fillType:NONE,  show:true },
    { sectionRank:2, type:SERIAL,   value:"yyyyMM", size:6, dateType:true,
      datePattern:"yyyyMM",                      show:true },
    { sectionRank:3, type:SERIAL,   size:4, fillType:LEFT, fillChar:"0",
      increase:true, startValue:1, endValue:9999, show:true }
  ]
```

**⚠️ 上例的第 2 段我用了 `type:SERIAL` + `dateType:true`，这是我的**推断**（日期段可能归 SERIAL 类型）。**
**实际可能用 `CONSTANT` + 日期模式。**⇒ 等级：`UNVERIFIED`。**

---

## 23. 未覆盖

| 项 | 说明 |
|---|---|
| `RedisUtils` 是否自动加租户前缀 | 未读方法体，**不确定** |
| `resolveSerialNumber` / `fillIn` 方法体 | 未读，拼接细节是推断 |
| 日期段到底归哪个 `SerialTypeEnum` | **未验证**（上例标了） |
| 并发取号的具体锁机制 | 未读（可能用 `setNx` 分布式锁） |
| `SerialCurrent` / `SerialRange` 字段 | 未 dump |
| `SerialNumberController` 的 REST 路径 | 未读（前端怎么调配编号页） |
| `SerialQueueTaskService` 队列机制 | 未读 |