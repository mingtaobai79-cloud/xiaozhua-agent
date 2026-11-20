# 专题 3：生成物与持久化体系

> 状态：**研究中（第一轮·静态）** · 未审计
> 平台版本：`udc-platform-5.3.517`
> 最近更新：2026-11-17
> ⚠️ 本专题的运行时部分（主键生成、外键回填、保存顺序、事务范围）**全部未验证**，需 test2 写操作批准

---

## 1. 研究目标

1. 七类生成物（Entity/DTO/AppService/Service/DAO/Mapper/XML）的职责与调用关系
2. 持久化全链路：CRUD、主键、查询、分页、批量、关联、单据、事务、隔离

---

## 2. 持久化分层（已证）

```
业务层
  Service（{E}Service，BIZ_DOMAIN_SERVICE）
    ↓
AppService 层（{E}AppService / {E}AppServiceImpl，FACADE_APP_SERVICE）
    ↓
DAO 层
  AllInOneBaseDao<T>（接口，41 方法）      com.seeyon.boot.starter.mybatis.inone.dao
  AbstractAllInOneBaseDao（抽象类，55 方法） com.seeyon.boot.starter.mybatis
    ↓
Mapper 层
  AllInOneBaseMybatisDao（接口）            com.seeyon.boot.starter.mybatis.inone.dao
  BaseMybatisDao<T>（接口，16 方法）        com.seeyon.boot.starter.mybatis
    ↓
框架层
  tk.mybatis（Mapper 框架）  ← 由 SeeyonSqlHelper 的 EntityColumn 参数证实
    ↓
数据库（10 种方言）
```

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名）
**⚠️ 未证：** 生成出来的 `{E}Dao` 具体继承哪个基类

---

## 3. `AllInOneBaseDao` 41 方法全表

### 3.1 写操作（8 个）

| 方法 | 签名 | 说明 |
|---|---|---|
| `create` | `(T): int` | 单条新增，返回影响行数 |
| `createBatch` | `(List<T>): int` | 批量新增 |
| `update` | `(T): int` | 更新（**带版本检查**） |
| `versionNoUpdateIgnoreVersion` | `(T): int` | **不递增版本号 + 忽略版本检查** |
| `updateColumns` | `(T, Set<String>): int` | 只更新指定列（**带版本检查**） |
| `updateColumnsIgnoreVersion` | `(T, Set<String>): int` | 指定列 + 忽略版本 |
| `updateBatch` | `(List<T>): int` | 批量更新 |
| `versionNoUpdateBatchIgnoreVersion` | `(List<T>): int` | 批量 + 不递增版本 + 忽略检查 |

**★ 版本控制的 4 个变体揭示了乐观锁语义：**

```
update(T)                                → 更新 + 版本号+1 + 校验版本
updateColumns(T, Set)                    → 指定列 + 版本号+1 + 校验版本
updateColumnsIgnoreVersion(T, Set)       → 指定列 + 版本号+1 + 不校验
versionNoUpdateIgnoreVersion(T)          → 全列 + 版本号不变 + 不校验
versionNoUpdateBatchIgnoreVersion(List)  → 批量 + 版本号不变 + 不校验
```

**⇒ `versionNoUpdate*` = 「不递增版本号」；`*IgnoreVersion` = 「不做乐观锁校验」。**
**⇒ 这两个是独立的两个维度，不是同一件事。**

**⚠️ 未证：** 版本冲突时抛什么异常、`update` 返回 0 时是「无数据」还是「版本冲突」

### 3.2 删除（6 个）

| 方法 | 签名 |
|---|---|
| `deleteById` | `(Long): int` |
| `deleteByIds` | `(List<Long>): int` |
| `deleteByCondition` | `(String, Object): int` |
| `deleteByConditions` | `(Map<String,Object>): int` |
| `deleteByComplexConditions` | `(Map<String,Object>): int` |
| `deleteByDynamicConditions` | `(Map<String,Object>): int` |
| `deleteByDynamicConditions` | `(List<SeeyonKeyMap>): int` |

### 3.3 查询 — 条件档位（★ 核心）

**四档条件，从简到繁：**

| 档位 | 方法参数 | 能力 |
|---|---|---|
| **1. 单条件** | `ByCondition(String field, Object value)` | 一个等值条件 |
| **2. 多条件 Map** | `ByConditions(Map<String,Object>)` | 多条件 AND（无序） |
| **3. 复杂条件** | `ByComplexConditions(LinkedHashMap<String,Object>)` | **保序**（可能表达 AND/OR 顺序） |
| **4. 动态条件** | `ByDynamicConditions(LinkedHashMap)` 或 **`List<SeeyonKeyMap>`** | **最灵活** |

**★ `SeeyonKeyMap` 的结构（逐字）：**

```java
com.seeyon.boot.starter.mybatis.util.SeeyonKeyMap
  # getKey(): String
  # getValue(): Object
  # setKey(String) / setValue(Object)
```

**⇒ 它就是一个 `{key, value}` 对，不是 Map 的替代品。**
**⇒ 用 `List<SeeyonKeyMap>` 而不是 `Map` 的意义：允许重复 key。**

**⇒ 推论（待证）：重复 key 用于表达「同字段多条件」或「OR 组合」。**

**⚠️ 不得断言。** 需反编译 `jdbcDynamicCondition` 确认。

### 3.4 查询 — 读操作（完整清单）

| 方法 | 返回 |
|---|---|
| `selectById(Long)` | `T` |
| `selectByIds(List<Long>)` | `List<T>` |
| `selectOneByCondition(String, Object)` | `T` |
| `selectOneByConditions(Map)` | `T` |
| `selectCountByCondition(String, Object)` | `int` |
| `selectCountByConditions(Map)` | `int` |
| `selectCountByComplexConditions(LinkedHashMap)` | `int` |
| `selectCountByDynamicConditions(LinkedHashMap)` | `int` |
| `selectCountByDynamicConditions(List<SeeyonKeyMap>)` | `int` |
| `selectListByCondition(String, Object, Sort)` | `List<T>` |
| `selectListByConditions(Map, Sort)` | `List<T>` |
| `selectListByComplexConditions(LinkedHashMap, Sort)` | `List<T>` |
| `selectListByDynamicConditions(LinkedHashMap, Sort)` | `List<T>` |
| `selectListByDynamicConditions(List<SeeyonKeyMap>, Sort)` | `List<T>` |
| `selectListPropertiesByConditions(String[], Map, Sort)` | `List<T>` |
| `selectListExcludeByConditions(String[], Map, Sort)` | `List<T>` |

**★ 列投影（2 个）：**
- `selectListPropertiesByConditions(String[] include, ...)` — **只查指定列**
- `selectListExcludeByConditions(String[] exclude, ...)` — **排除指定列**

**⇒ 大表查询应该用这两个，避免 `SELECT *`。**

### 3.5 分页（4 个 + 2 个投影版）

| 方法 | 返回 |
|---|---|
| `selectPageByCondition(PageInfo, String, Object, Sort)` | `PageData<T>` |
| `selectPageByConditions(PageInfo, Map, Sort)` | `PageData<T>` |
| `selectPageByComplexConditions(PageInfo, LinkedHashMap, Sort)` | `PageData<T>` |
| `selectPageByDynamicConditions(PageInfo, LinkedHashMap, Sort)` | `PageData<T>` |
| `selectPageByDynamicConditions(PageInfo, List<SeeyonKeyMap>, Sort)` | `PageData<T>` |
| `selectPagePropertiesByConditions(PageInfo, String[], Map, Sort)` | `PageData<T>` |
| `selectPageExcludeByConditions(PageInfo, String[], Map, Sort)` | `PageData<T>` |

**⇒ 返回 `PageData<T>`，不是 `PageResponse<T>`。**

**★★ `PageInfo` 结构（逐字）：**

```java
com.seeyon.boot.transport.PageInfo
  # getPageSize(): int
  # getPageNumber(): int
  # getPages(): int
  # getTotal(): int
  # isNeedTotal(): boolean      ← ★★ 可以关闭总数统计
  # isNeedMore(): boolean       ← ★★ 只要"还有没有更多"
  # setPageSize(int) / setPageNumber(int) / setTotal(int)
  # setNeedTotal(boolean) / setNeedMore(boolean)
```

**⇒ `isNeedTotal()` 是用户踩过的「604 次全量 COUNT」问题的直接解法。**
**⇒ `isNeedMore()` 提供「不算总数，只判断是否还有下一页」的轻量模式。**

**⚠️ 未证：** `needTotal=false` 时 `buildCountQueryString` 是否真的被跳过
→ 需反编译 `AllInOneDBDynamicSeeyonKeyMapUtil#selectDynamic` 或实测

**`PageData` 结构：**
```java
PageData.from(PageInfo, List<T>): PageData<T>
PageData#to(Class<D>): PageData<D>          ← 类型转换（Entity→Dto）
PageData#getPageInfo(): PageInfo
PageData#getContent(): List<T>
```

### 3.6 聚合（2 个）

| 方法 | 签名 |
|---|---|
| `selectListFuncByComplexConditions` | `(LinkedHashMap, Sort, String func, List<String> cols): String` |
| `selectListFuncByDynamicConditions` | `(LinkedHashMap, Sort, String func, List<String> cols): String` |

**⇒ 返回 `String` 不是数值类型。**
**⇒ 推论（待证）：可能需要调用方自行解析（如 BigDecimal），或者是 JSON。**

---

## 4. `BaseMybatisDao` 16 方法（底层 Mapper）

### 4.0 ★ `AbstractAllInOneBaseDao` 55 方法：比接口多 14 个

**逐方法对比 41（接口）vs 55（抽象类），抽象类新增的 14 个：**

| 方法 | 签名 | 说明 |
|---|---|---|
| **`putThreadContext`** | `(): void` | **★ 注入线程上下文** |
| **`removeThreadContext`** | `(): void` | **★ 清理线程上下文** |
| `notSupportedException` | `(): void` | 不支持操作抛异常 |
| `getT` | `(): Class<T>` | 取实体类型 |
| `createBatchNoClob` | `(List): int` | 无 CLOB 批量 |
| `createBatchIgnoreTime` | `(List): int` | 忽略时间 |
| `updateBatchIgnoreTime` | `(List): int` | 忽略时间 |
| `updateBatchIgnoreVersion` | `(List): int` | 忽略版本 |
| **`deleteByWrapper`** | `(Wrapper): int` | **★ Wrapper 删除** |
| **`selectOneByWrapper`** | `(Wrapper): Object` | **★ Wrapper 查询** |
| **`selectCountByWrapper`** | `(Wrapper): int` | **★ Wrapper 计数** |
| **`selectListByWrapper`** | `(Wrapper): List` | **★ Wrapper 列表** |
| **`selectPageByWrapper`** | `(PageInfo, Wrapper): PageData` | **★ Wrapper 分页** |
| `getFieldCount` | `(List): int` | 字段计数 |

**★★ 两个关键结论：**

1. **`putThreadContext()` / `removeThreadContext()` 证明 DAO 层有线程上下文机制**
   - 结合 `AllInOneDBDynamicSeeyonKeyMapUtil#tenantAdd(...)` 的自动租户注入
   - ⇒ **租户信息很可能来自 ThreadLocal**（未证）
   - ⇒ 这解释了为什么异步线程需要手动传递 `userId`/`tenantId`（用户复盘文档的坑）

2. **Wrapper 系列 5 个方法 = tk.mybatis 的 Example 风格条件构造器**
   - 比 `Map<String,Object>` 条件更强（支持 `or`、`in`、`like`、嵌套）
   - `Wrapper` 类本身在签名库无可见方法（可能是泛型基类或继承 tk.mybatis）

**⚠️ `Wrapper` 的实际能力未证，需反编译或查 tk.mybatis 文档。**

### 4.0.1 ★ Mapper 数量口径修正

**旧结论：`BaseMybatisDao` 由「22 个 Mapper」拼装。**

**实测：`extends` 子句共 23 项：**
```
BaseDao<T>                    ← 平台基础 Dao
tk.mybatis.mapper.common.Marker  ← tk.mybatis 标记接口
+ 21 个 Mapper 接口
```

**⇒ 精确口径：**
- **21 个 Mapper 接口**（全部在 `com.seeyon.boot.starter.mybatis.mapper`，实测 21/21 命中）
- **+ 1 个 Marker** = 22 个「可 mixin 的接口」
- **+ BaseDao** = 23 个 extends 项

**⇒ 旧结论「22 个 Mapper」实际是「21 Mapper + Marker」，不含 BaseDao。**

**21 个 Mapper 清单（逐字）：**
```
CreateMapper              CreateBatchMapper
UpdateMapper              UpdateBatchMapper
UpdateByConditionMapper   UpdateByWrapperMapper
UpdateBatchIgnoreVersionMapper   UpdateIgnoreVersionMapper
DeleteByIdMapper          DeleteByConditionMapper
DeleteByComplexConditionMapper   DeleteByDynamicConditionMapper
DeleteByWrapperMapper
SelectByIdMapper          SelectByConditionMapper
SelectFuncByConditionMapper      SelectFuncByComplexConditionMapper
SelectFuncByDynamicConditionMapper
SelectByComplexConditionMapper   SelectByDynamicConditionMapper
SelectByWrapperMapper
```

**⇒ 只想用几个方法就只 mixin 对应 Mapper，接口面更小。**

### 4.1 `BaseMybatisDao` 16 方法

#### 4.1.0 ★ 数据库方言：实际 **11 种**（修正旧文档「10 种」）

来源：`signatures.txt.gz` → `com.seeyon.boot.starter.mybatis.dialect.impl.*`

```
1.  Dm8SQLDatabaseDialect          达梦 8
2.  GBaseSQLDatabaseDialect        GBase
3.  KingbaseV8SQLDatabaseDialect   人大金仓 V8
4.  MySQLDatabaseDialect           MySQL
5.  OracleDatabaseDialect          Oracle
6.  OscarSQLDatabaseDialect        神通 Oscar
7.  PostgreSQLDatabaseDialect      PostgreSQL
8.  SequoiaDBSQLDatabaseDialect    巨杉 SequoiaDB
9.  SqlServerDatabaseDialect       SQL Server
10. TDSQLDatabaseDialect           TDSQL
11. TidbSQLDatabaseDialect         TiDB
```

**⇒ 实测 11 个实现类。**

**⚠️ 旧文档 `dao-and-mybatis.md` 写「10 种数据库方言」，但它自己列的清单是 11 项**
（MySQL / Oracle / PostgreSQL / SQLServer / 达梦 Dm8 / 人大金仓 KingbaseV8 / GBase /
神通 Oscar / 巨杉 SequoiaDB / TDSQL / TiDB）
**⇒ 这是**计数错误**，清单对、数字错。**

#### 4.1.1 ★ 方言只负责「分页 SQL」

```java
com.seeyon.boot.starter.mybatis.dialect.DatabaseDialect    ← interface
  # pageSql(PageInfo, String): String            ← ★ 唯一职责
  # getDatabaseType(): DatabaseType

com.seeyon.boot.starter.mybatis.dialect.DatabaseDialectManager
  # pageSql(PageInfo, String): String
  # register(DatabaseDialect): void               ← ★ 可注册自定义方言
```

**⇒ 方言接口只有 2 个方法，核心是 `pageSql`。**
**⇒ 方言**不管**其他 SQL 差异（类型映射、函数、DDL）。**

**⇒ 这解释了为什么 `AllInOneDBDynamicSeeyonKeyMapUtil#getPageSql(PageInfo, String)` 只有 2 个参数——
方言是内部按 `DatabaseType` 选的，调用方不感知。**

**⇒ `DatabaseDialectManager#register(...)` 说明方言可扩展（可加自定义数据库）。**

**证据等级：** `VERIFIED_STATIC_BYTECODE`（签名 + 类枚举）

| 方法 | 说明 |
|---|---|
| `updateBatch` | 批量更新 |
| `updateBatchIgnoreTime` | **忽略更新时间** |
| `updateBatchIgnoreVersion` | 忽略版本 |
| `versionNoUpdateBatchIgnoreVersion` | 不递增版本 + 忽略 |
| `createBatch` | 批量新增 |
| `createBatchNoClob` | **不含 CLOB** |
| `createBatchIgnoreTime` | 忽略创建时间 |
| `getFieldCount(List)` | 字段计数 |
| `deleteByIds` / `deleteByCondition` | 删除 |
| `selectOneByCondition` / `selectOneByConditions` | 单条 |
| `selectCountByCondition` | 计数 |
| `selectListByCondition` / `selectPageByCondition` | 列表/分页 |
| `selectOneByWrapper(Wrapper)` | **tk.mybatis Wrapper** |

**★ 关键：`createBatchNoClob` 的存在说明批量插入对 CLOB 字段有特殊处理。**
**⇒ 大文本字段（MULTILINESTRING 等）批量写入可能有坑，需注意。**

**★ `updateBatchIgnoreTime` / `createBatchIgnoreTime`**
**⇒ 平台默认会自动填充 `createTime` / `updateTime`，这两个方法可以跳过。**

---

## 5. 逻辑删除（已证机制）

```java
com.seeyon.boot.starter.mybatis.util.SeeyonSqlHelper
  # logicDeleteColumnEqualsValue(tk.mybatis.mapper.entity.EntityColumn, boolean): String
  # getLogicDeletedValue(tk.mybatis.mapper.entity.EntityColumn, boolean): int
  # updateSetColumns(Class<?>, String, boolean, boolean): String
  # updateSetColumns(Class<?>, String, boolean, boolean, Set<String>): String
  # getIfNotNull(String, EntityColumn, String, boolean): String
  # valueParser(Object, EntityColumn): Object
  # valueParser(Object, Class<?>): Object
```

**⇒ 逻辑删除的实现：**
1. `getLogicDeletedValue(EntityColumn, boolean): int` — 取逻辑删除值（整型）
2. `logicDeleteColumnEqualsValue(EntityColumn, boolean): String` — 生成 SQL 条件片段

**⇒ 逻辑删除是「整型标志位 + SQL 条件注入」，不是物理删除。**
**⇒ 但 `AllInOneBaseDao` 的 `deleteById` 等方法是否走逻辑删除，未证。**

**⚠️ `basic` 字段集里没有 `deleted` / `isDeleted` 字段。**
**⇒ 逻辑删除字段可能不在系统字段集里，而是按实体配置。**
**标记 `UNVERIFIED`，需查实体配置或实测。**

**★ 底层框架是 tk.mybatis**
证据：`SeeyonSqlHelper` 的参数类型是 `tk.mybatis.mapper.entity.EntityColumn`。

---

## 6. 多租户隔离（★ 已证机制）

```java
com.seeyon.boot.starter.mybatis.service.AllInOneDBDynamicSeeyonKeyMapUtil
  # tenantAdd(List<SeeyonKeyMap>, Boolean): void     ← ★ 自动注入租户条件
```

**⇒ 动态条件查询会自动追加租户条件。**
**⇒ 这是多租户隔离的实现点。**

**⚠️ 但 `tenantAdd` 的第二个 `Boolean` 参数含义未知**（可能是「是否启用」或「是否强制」）。
**标记 `UNVERIFIED`。**

**关联：`basic` 字段集有 `tenantId: BIGINTEGER`。**

---

## 7. SQL 构建（★ 直接拼 SQL 的工具）

```java
com.seeyon.boot.starter.mybatis.service.AllInOneDBDynamicSeeyonKeyMapUtil
  # selectDynamic(String[] cols, List<SeeyonKeyMap>, Boolean, PageInfo, Sort, Class<?>): List<Object>
  # selectDynamicCount(List<SeeyonKeyMap>, Boolean, PageInfo, Sort, Class<?>): int
  # selectDynamicFunc(List<SeeyonKeyMap>, Boolean, PageInfo, Sort, String, List, Class<?>): String
  # deleteDynamic(List<SeeyonKeyMap>, Boolean, Class<?>): int
  # tenantAdd(List<SeeyonKeyMap>, Boolean): void
  # jdbcDynamicCondition(StringBuilder, List<SeeyonKeyMap>, Map<String,Object>, Class<?>, SeeyonInteger...)
  # whereMatcher(String): String
  # buildQueryString(String, String[], Map<String,String>, String, PageInfo, Sort, Class<?>): String
  # buildFuncQueryString(String, String, PageInfo, Sort, String, List, Class<?>): String
  # buildCountQueryString(String, String, PageInfo, Sort, Class<?>): String
  # getSortSql(Sort, StringBuilder, Class<?>): void
  # getPageSql(PageInfo, String): String
  # appendClause(StringBuilder, String): void
  # appendColumns(StringBuilder, String[], Map<String,String>): void
  # appendColumns(StringBuilder, Map<String,String>): void
```

**⇒ 平台有「直接构建 SQL 字符串」的完整工具链：**
- `buildQueryString` — 查询 SQL
- `buildCountQueryString` — 计数 SQL（**`isNeedTotal` 可能在这里被判断**）
- `buildFuncQueryString` — 聚合 SQL
- `getPageSql` — 分页 SQL（**方言相关**）
- `getSortSql` — 排序 SQL

**⇒ `getPageSql(PageInfo, String)` 只有 2 个参数，说明方言是内部决定的。**
**⇒ 这对应 `dao-and-mybatis.md` 里记录的「10 种方言」。**

**另有 `AllInOneJdbcDao`（JDBC 版，不用 MyBatis）**，方法同名。

---

## 8. 主子表（聚合）

### 8.0 ★★ 核心发现：`BaseEntityCurdService`（**实测 81 个方法**）

```java
com.seeyon.boot.starter.lowcode.service.BaseEntityCurdService   ← abstract class
```

**继承链（javap 实测）：**

```java
public abstract class BaseEntityCurdService<D extends com.seeyon.udc.common.dto.BaseEntityActionDto>
  implements org.springframework.beans.factory.InitializingBean,
             com.seeyon.boot.starter.lowcode.core.BaseCurdService<D>,
             com.seeyon.boot.starter.lowcode.callback.PreCreateCallBack<D>,
             com.seeyon.boot.starter.lowcode.callback.PreUpdateCallBack<D>,
             com.seeyon.boot.starter.lowcode.callback.MethodCallBack<D>,
             com.seeyon.boot.starter.lowcode.callback.ValidateCallBack<D>,
             com.seeyon.boot.starter.lowcode.core.DataTransferService<D>,
             com.seeyon.boot.starter.lowcode.callback.PreCopyCallBack<D>
```

**⇒ 它实现了 6 个 callback 接口，这就是「扩展点」的落点。**

**★ 修正：旧文档写「199 方法」是错的。**
**实测 `runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt`（7985 行 javap 输出）：**
- 方法声明行 **81 条**（含 private/protected，去掉重复声明后 **76 个唯一方法名**）
- 之前的 199 可能是把字段、描述符行、或跨类统计混入了

**证据：** `runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt`
**等级：** `VERIFIED_STATIC_BYTECODE`

#### 8.0.0 关键依赖字段（javap 实测，说明它能做什么）

```java
EntityMeta entityMeta                        ← 实体元数据（递归依据）
EntityBeanContainer entityBeanContainer
EntityEventHelper entityEventHelper          ← 事件
PermissionCallBack permissionCallBack        ← 权限
ApprovalCallBack approvalCallBack            ← 审批
BillStateCallBack billStateCallBack          ← 单据状态
SecretCallBack secretCallBack                ← 密级
EntityAttrSnapshotCallBack entityAttrSnapshotCallBack  ← 属性快照
EventBus eventBus
PlatformTransactionManager transactionManager  ← 事务
DynamicProxySelectService dynamicProxySelectService  ← 动态 SQL
MultiThreadTransaction threadTransaction       ← 多线程事务
ExecutorService executorService                ← 并行
ModuleBeanFactory moduleBeanFactory
CommonDataTypes commonDataTypes
MessageRepository messageRepository            ← i18n
EntityConfig entityConfig
```

**⇒ 单据能力不是靠 `BaseEntityCurdService` 自己实现的，
而是通过 `ApprovalCallBack` / `BillStateCallBack` 注入。**

**⇒ 这解释了「单据 vs 普通实体」的机制区别。**

**⇒ 这是本轮最重要的发现，v4 计划完全没提到这个类。**

#### 8.0.1A ★★★ `recursiveCreate` 字节码还原（机制级证据）

**这是「主子表怎么入数据」最直接的证据——不是签名推断，是实际字节码。**

**源码位置：** `runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt` 第 714 行
**方法签名：** `private int recursiveCreate(EntityMeta, List<D>)`
**等级：** `VERIFIED_STATIC_BYTECODE`（可复现：javap -c 反汇编）

**字节码完整控制流还原：**

```java
private int recursiveCreate(EntityMeta meta, List<D> list) {
    AtomicInteger count = new AtomicInteger(0);

    // ---- 分支 A：该实体有子实体 ----
    if (isNotEmpty(meta.getChildren())) {
        if (isNotEmpty(list)) {
            list.stream().forEach(dto ->
                // lambda$recursiveCreate$14:
                //   对每个子 EntityMeta 递归调用自身
                meta.getChildren().forEach(childMeta ->
                    count.addAndGet(this.recursiveCreate(childMeta, childList))
                )
            );
        }
        // 注意：子表分支结束后直接跳到 84 返回，不执行分支 B
    }
    // ---- 分支 B：无子实体，且不是主实体 ----
    else if (meta.getEntityType() != EntityType.MASTER_ENTITY) {
        Optional.ofNullable(
            entityBeanContainer.findDao(meta.getEntityClass())
        ).ifPresent(dao -> {
            // lambda$recursiveCreate$18:
            //   BeanCopier.copyList(list, meta.getEntityClass())   ← DTO→Entity
            //   entityBeanContainer 拿 dtoClass
            //   dao 批量写入
        });
    }
    return count.get();
}
```

**字节码关键指令（可逐条核对）：**

| 偏移 | 指令 | 含义 |
|---|---|---|
| 0-8 | `new AtomicInteger` / `<init>(0)` / `astore_3` | 计数器初始化 |
| 10 | `EntityMeta.getChildren()` | **取子实体元数据** |
| 13 | `CollectionUtils.isNotEmpty` | 判断有无子表 |
| 16 | `ifeq 48` | 无子表 → 跳分支 B |
| 27-40 | `List.stream().forEach` | 有子表 → 遍历 |
| 35 | `invokedynamic #11` | **lambda 内递归调 `recursiveCreate`** |
| 48-55 | `EntityType.MASTER_ENTITY` + `getEntityType()` + `if_acmpeq 84` | **主实体不直接落库** |
| 58-66 | `entityBeanContainer.findDao(entityClass)` | **按实体类找 DAO** |
| 69-81 | `Optional.ifPresent` | DAO 存在才执行 |
| 85-88 | `AtomicInteger.get()` / `ireturn` | 返回累计条数 |

**⇒ 三条机制结论（字节码直接证明，非推断）：**

**① 递归依据是 `EntityMeta.getChildren()`，不是注解扫描。**
子表关系来自元数据树，运行时动态决定的。

**② 主实体（`MASTER_ENTITY`）不直接落库，只递归子表。**
`if_acmpeq 84` 跳过落库分支 —— 主表数据由调用方（`create`/`createBatch`）先写入。

**③ 落库动作是 `findDao(entityClass)` 拿到 DAO 再批量写，不是 Service 自调。**
所以主子表写入最终都落到 `BaseDao` 层。

**⚠️ 仍未证明的部分（必须标注）：**

- **主表 ID 何时生成** —— 字节码里 `recursiveCreate` 不产生 ID，说明在 `create()` 层已生成并回填到 DTO
- **子表外键何时赋值** —— `lambda$recursiveCreate$18` 里有 `BeanCopier.copyList`，但外键字段赋值需看该 lambda 完整体（下轮追）
- **事务边界在哪** —— `transactionManager` 是字段，但 `recursiveCreate` 自身没看到 `@Transactional`

**这三条是下轮 P0。**

#### 8.0.1B ★★★ `create()` 完整执行链（主键回填已证）

**这是「主表 ID 何时生成、何时回填」的答案 —— 字节码直证。**

**源码位置：** `runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt`（`create(D)` 方法体 253 行）
**等级：** `VERIFIED_STATIC_BYTECODE`

**完整调用序列（按字节码出现顺序）：**

```
create(D dto)
│
├─ printTransactionInfo()                                    ← 事务诊断
├─ Asserts.isTrue(isMasterEntity, ...)                       ← 必须主实体
├─ handlerCaseId(dto)                                        ← ★ 单据 caseId 处理
├─ DtoConvertUtil.resetInsertHandle(entityMeta, dto)         ← ★ 重置插入字段（ID/创建人等）
│
├─ ── 权限 ──
├─ permissionCallBack.checkXxx(entityMeta, ...)              ← 权限校验（主/从各一次）
│
├─ ── 前置回调 ──
├─ preCreateBatch(list)                                      ← PreCreateCallBack
├─ beforeCreate(list)                                        ← MethodCallBack
├─ EventContainer.builder()
│    .dtoClass(dtoClass)
│    .actionType(ActionType.INSERT)                          ← ★ 事件类型=INSERT
│    .eventData([dto]).build()
├─ entityEventHelper.beforeEvent(container)                  ← ★ beforeEvent
├─ afterBeforeEventCheck(list)
├─ EntityExceptionThrower.throwing(list)                     ← ★ 事件校验异常抛出
│
├─ OperateContext.enter()                                    ← ★ 进入操作上下文
│    .actionType(ActionType.INSERT)
│    .entityMeta(entityMeta)
│    .newData(list)
│
├─ ── 密级 ──
├─ secretCallBack.checkXxx(...)                              ← SecretCallBack 密级校验
│
├─ recursiveCheck(entityMeta, list, cache)                   ← ★ 递归校验（主+子）
├─ recursiveCreate(entityMeta, list)                         ← ★★ 递归创建子表
├─ middleCreate(list)                                        ← 中间回调
│
├─ ── 主表落库 ──
├─ BeanCopier.copy(dto, entityClass, ignoreFields)            ← ★ DTO → Entity
├─ BaseEntity 实例
├─ getMapper() → BaseDao                                     ← ★ 取 DAO
├─ EntityClassContext.withEntityClass(dao, entityClass, ...)  ← ★ 绑定实体类上下文
│    └─ Integer result = ...dao.insert...                    ← ★ 真正 INSERT
│
├─ afterCreate(list)                                         ← 后置回调
├─ entityEventHelper.afterEvent(container)                   ← ★ afterEvent
│
├─ ── ★★★ 主键回填 ──
├─ BaseEntity.getId() → Long id                              ← ★ 从 entity 读 ID
├─ BaseEntityActionDto.setId(id)                             ← ★★★ 写回 DTO
│
├─ OperateContext.leave()                                    ← ★ 退出上下文
├─ resetNormal(list)                                         ← ★ 重置普通字段
├─ entityEventHelper.transactionSuccessEvent(container)       ← ★ 事务成功事件
└─ 日志：entityMeta.getCaption() + dto.getId() + StopWatch.prettyPrint()
```

**⇒ 三条 P0 问题现在有答案：**

**① 主表 ID 何时生成？**
`DtoConvertUtil.resetInsertHandle(entityMeta, dto)` 在**最前面**就处理了插入字段（含 ID）。
真正 ID 由 `dao.insert()` 时 MyBatis 主键回填（`useGeneratedKeys`）或雪花算法生成，
**然后 `entity.getId()` → `dto.setId()` 显式回填。**

**② 子表外键何时赋值？**
顺序是 `recursiveCreate()` **在** `middleCreate()` 和主表 INSERT **之前**。
但子表要拿到主表 ID 才能设外键 —— 这说明：
- 要么 ID 在 `resetInsertHandle` 阶段已预生成（雪花 ID 可预生成）
- 要么子表外键在 `recursiveCreate` 内部通过 `EntityMeta` 关系推导

**⚠️ 这一点仍需看 `resetInsertHandle` 内部才能定论，标记为 PARTIAL。**

**③ 事务边界？**
`OperateContext.enter()` / `leave()` 包裹了整个写入过程。
`transactionSuccessEvent` 在最后触发 —— 说明**事件与事务绑定**。
但 `@Transactional` 注解在 javap 中不可见（运行时注解），需看 `EntityConfig` 或 AOP 配置。

**⇒ 额外重要发现：`ActionType.INSERT` 贯穿事件和上下文**
**⇒ 说明 UDC 的「事件/回调体系」是靠 ActionType 分发的，不是每个动作一个方法。**

**⇒ 还有 `middleCreate` 这个中间层，之前完全没发现。**

#### 8.0.1G ★★ `create()` 内部调用的**精确**修饰符（字节码直证）

**这决定了哪些能被覆写、哪些不能 —— 是扩展点设计的关键。**

| 方法 | 指令 | 修饰符 | 可覆写 | 归属 |
|---|---|---|---|---|
| `printTransactionInfo()` | `invokespecial` | private | ❌ | 本类 |
| `handlerCaseId(dto)` | **`invokestatic`** | **static** | ❌ | 本类（静态工具） |
| `preCreateBatch(List)` | `invokevirtual` | public/protected | ✅ | **父类 default** |
| `beforeCreate(List)` | `invokevirtual` | public/protected | ✅ | **父类 default** |
| `afterBeforeEventCheck(List)` | `invokevirtual` | public/protected | ✅ | **父类 default** |
| `recursiveCheck(...)` | `invokespecial` | private | ❌ | 本类 |
| `recursiveCreate(...)` | `invokespecial` | **private** | ❌ | 本类 |
| `middleCreate(List)` | `invokevirtual` | public/protected | ✅ | **父类 default** |
| `getMapper()` | `invokevirtual` | public | ✅ | **父类/接口** |
| `afterCreate(List)` | `invokevirtual` | public/protected | ✅ | **父类 default** |
| `resetNormal(List)` | `invokespecial` | private | ❌ | 本类 |

**⇒ 关键区分（指令不同，语义不同）：**

```
invokespecial  → private，本类私有，不可覆写
                  printTransactionInfo / recursiveCheck / recursiveCreate / resetNormal
invokestatic   → 静态方法
                  handlerCaseId
invokevirtual  → 可覆写（父类 default 或 public）
                  preCreateBatch / beforeCreate / afterBeforeEventCheck /
                  middleCreate / getMapper / afterCreate
```

**⇒★★ 直接回答「开发者能扩展什么、不能碰什么」：**

**可以覆写（6 个）：**
```
preCreateBatch / beforeCreate / afterBeforeEventCheck
middleCreate   / getMapper    / afterCreate
```

**不能碰（私有）：**
```
printTransactionInfo / recursiveCheck / recursiveCreate / resetNormal
```

**⇒ 「想改主子表递归逻辑」做不到（private）。**
**⇒ 只能通过 callback 接口，或覆写 `middleCreate` / `afterCreate` 介入。**

**⇒ 这是平台设计的硬边界，不是建议。**

#### 8.0.1H ★ `create()` 里的 3 个 lambda（从 invokedynamic 看）

| 偏移 | 指令 | 签名 | 推断用途 |
|---|---|---|---|
| 17 | `InvokeDynamic #6:accept:()BiConsumer` | `BiConsumer` | `resetInsertHandle` 的回调参数 |
| 45 | `InvokeDynamic #7:accept:()BiConsumer` | `BiConsumer` | `DtoConvertUtil.forEach` 的回调 |
| 409 | `InvokeDynamic #8:call:(BaseDao, BaseEntity)Function` | `Function<BaseDao, BaseEntity>` | **`EntityClassContext.withEntityClass` 的执行体** |

**⇒ 偏移 409 的 lambda 就是真正执行 insert 的地方：**
**⇒ 形式为 `withEntityClass(dao, entityClass, () -> dao.insert(entity))`。**

#### 8.0.1C ★★ 回调接口族全表（`interface-inventory.md` 实测）

**`create()` 链里出现的每个 callback，都在这里有对应统计。**

| 接口 | 抽象方法 | 具体方法 | 已知方法 |
|---|---|---|---|
| `ApprovalCallBack` | 0 | **6** | — （审批，单据核心）|
| `ApprovalCallBackExt` | 0 | **6** | — （审批扩展）|
| `BillStateCallBack` | 0 | **1** | — （单据状态）|
| `EntityAttrSnapshotCallBack` | 4 | 4 | `saveSnapshot(List,EntityMeta)` / `updateSnapshot(...)` / `deleteByDataMasterIds(List)` / `deleteDataIds(List)` |
| `EntityDataDiffCallBack` | 1 | 1 | `diffData(List, Map, List, Map, EntityMeta)` |
| `EntityRuntimeLogCallBack` | 0 | **28** | — （运行时日志，方法最多）|
| `MethodCallBack` | 0 | **10** | — （含 beforeCreate/afterCreate）|
| `PermissionCallBack` | 0 | 2 | — （权限）|
| `PreCopyCallBack` | 0 | 1 | — |
| `PreCreateCallBack` | 0 | 1 | `preCreateBatch(List)` （推断，1 方法）|
| `PreUpdateCallBack` | 0 | 1 | — |
| `SecretCallBack` | 1 | 1 | `checkSecret(Collection)` |
| `ValidateCallBack` | 0 | 1 | — |

**⇒ 单据能力分布（重要）：**

```
ApprovalCallBack       6 方法  ┐
ApprovalCallBackExt    6 方法  ├─ 共 12 个审批相关
BillStateCallBack      1 方法  ┘
```

**⇒ 单据的审批/状态能力全部在 callback 层，`BaseEntityCurdService` 只是调用方。**

#### 8.0.1D ★★ 接口继承体系（`BaseCurdService` 家族）

**`BaseEntityCurdService implements BaseCurdService<D>`，而 `BaseCurdService` 本身是组合接口。**

| 接口 | 抽象方法 | 具体方法 | 职责 |
|---|---|---|---|
| **`BaseCurdService`** | **0** | **35** | 总接口（全具体方法 → 是 default 方法集合）|
| `BaseService` | 1 | 3 | `getEntityClass()` |
| `QueryService` | 0 | **6** | 查询 |
| `UpdateService` | 0 | **15** | 更新 |
| `DataTransferService` | 1 | 1 | `importEntityInitData(ExcelImportTransDto)` |
| `BaseMybatisDao` | 0 | **16** | 底层 DAO |

**⇒ `BaseCurdService` 有 0 个抽象方法 + 35 个具体方法 → 它是纯 default 接口。**
**⇒ `middleCreate` / `afterCreate` / `preCreateBatch` / `beforeCreate` 这些
在 `BaseEntityCurdService` 里只被调用、没有定义 → 定义在 `BaseCurdService` 的 default 方法里。**

**⚠️ 但 `BaseCurdService.javap.txt` 不在本机资产中，具体 35 个方法名未取到。**
**⇒ 标记 `PARTIAL`：知道它在这，不知道它是什么。**

#### 8.0.1E ★ 事件体系接口（`EventHelper`）

| 接口 | 抽象 | 具体 | 方法 |
|---|---|---|---|
| **`EventHelper`** | 3 | 3 | `beforeEvent(EventContainer)` / `afterEvent(EventContainer)` / `transactionSuccessEvent(EventContainer)` |

**⇒ 与 `create()` 链里看到的三次调用完全对应：**
```
entityEventHelper.beforeEvent(container)          ← 对应 beforeEvent
entityEventHelper.afterEvent(container)           ← 对应 afterEvent
entityEventHelper.transactionSuccessEvent(container) ← 对应 transactionSuccessEvent
```

**⇒ 事件体系只有 3 个入口，靠 `EventContainer.actionType` 分发。**
**⇒ 这印证了前面的判断：`ActionType.INSERT` 是分发键，不是方法名。**

#### 8.0.1F ★ 其他相关接口

| 接口 | 抽象 | 具体 | 用途 |
|---|---|---|---|
| `OperateListener` | 1 | 1 | `onOperate(OperateContext)` — 操作监听（对应 create 链的 `OperateContext`）|
| `DataProcessor` | 2 | 2 | `dataProcess(OperateContext)` / `flowProcess(OperateContext)` |
| `DataVisitor` | 2 | 3 | `match(OperateContext)` / `visit(OperateContext)` |
| `EntityLogFilter` | 1 | 1 | `ignoreLog(String)` |
| `AppInfoService` | 10 | 10 | `getAppName()` 等应用信息 |

**⇒ `OperateContext` 是贯穿全链的上下文对象，有 3 个接口围绕它：**
**⇒ `OperateListener` / `DataProcessor` / `DataVisitor` —— 这是「操作后处理」的扩展点。**

#### 8.0.1I ★★★ 对照验证：`deleteById()` 与 `create()` 完全同构

**为证明「回调 + ActionType 分发」不是 create 的特例，对 `deleteById(Long)`（201 行字节码）做了对照。**

**`deleteById` 的实际调用序列：**

```
deleteById(Long id)
│
├─ getBaseEntityCurdService()          ← 拿到自己能处理该实体的 service
├─ selectCascadeById(id)               ← 先读出完整数据（含子表）
├─ ...
├─ beforeDelete(...)                   ← ★ 前置回调
├─ ActionType.DELETE                   ← ★ 事件类型=DELETE
├─ entityEventHelper.beforeEvent(...)  ← ★ beforeEvent
├─ getMapper() → BaseDao
├─ ...dao.delete...
├─ afterDelete(...)                    ← ★ 后置回调
├─ entityEventHelper.afterEvent(...)   ← ★ afterEvent
├─ entityEventHelper.transactionSuccessEvent(...)  ← ★ 事务成功
└─ RequestContext.getRequestContext()  ← 请求上下文
```

**⇒ 与 `create()` 结构逐项对应：**

| 阶段 | `create()` | `deleteById()` |
|---|---|---|
| 前置处理 | `resetInsertHandle` / `permissionCallBack` | `getBaseEntityCurdService` / `selectCascadeById` |
| 前置回调 | `preCreateBatch` / `beforeCreate` | `beforeDelete` |
| ActionType | **INSERT** | **DELETE** |
| 事件 | `beforeEvent` | `beforeEvent` ✅ |
| 落库 | `getMapper` → `insert` | `getMapper` → `delete` ✅ |
| 后置回调 | `afterCreate` | `afterDelete` |
| 事件 | `afterEvent` | `afterEvent` ✅ |
| 事务 | `transactionSuccessEvent` | `transactionSuccessEvent` ✅ |

**⇒ 结论：这是平台的统一 CRUD 骨架，不是每个方法单独实现的。**

#### 8.0.1J ★★★ ActionType 全类使用统计（证明统一模式）

**统计 `BaseEntityCurdService` 全文对 `ActionType` 的引用：**

| ActionType | 引用次数 |
|---|---|
| **`ActionType.UPDATE`** | **20** |
| **`ActionType.INSERT`** | **9** |
| **`ActionType.DELETE`** | **6** |
| `ActionType.NORMAL` | 2 |
| `ActionType.equals` | 1（比较调用，非枚举值）|

**⇒ 4 个 ActionType 覆盖全部 CRUD，UPDATE 用得最多（因为 update 有多个变体）。**
**⇒ 这印证了：「事件/回调/AOP 都靠 ActionType 分发」。**

**⇒ 对开发者的意义：**
**写扩展时不是找 `beforeCreate` 还是 `beforeUpdate`，
而是实现 callback 接口 + 判断 `container.getActionType()`。**

#### 8.0.1K ★★★ `updateBase(D, boolean, boolean)` 完整还原（431 行字节码）

**`update(D)` 只有 10 行，真正逻辑在 `updateBase(D, boolean, boolean)`。**

**⚠️ 已修正前面的 PARTIAL：`updateBase` 已完整提取。**

**完整调用序列：**

```
updateBase(D dto, boolean flag1, boolean flag2)     ← 431 行字节码
│
├─ printTransactionInfo()
├─ ActionType.UPDATE                                 ← ★ 20 处引用之一
├─ beforeUpdateConsumer.accept(entityMeta, list)     ← ★ 可注入的 BiConsumer
├─ DtoConvertUtil.defaultUpdateListToMap(...)        ← ★ DTO 列表 → Map（用于比对旧值）
├─ selectCascadeById(...)                            ← ★★ 先查旧值（含子表）
│
├─ OperateContext.builder()
│    .actionType(ActionType.UPDATE)
│    .entityMeta(entityMeta)
│    .newData(list)
│    .oldData(oldMap)                                ← ★★ UPDATE 独有的 oldData
│    .build()
├─ OperateContext.enter()
├─ OperateContext.deepCopyNewData()                  ← ★ 深拷贝新数据
│
├─ ── 单据状态 ──
├─ billStateCallBack.xxx()                           ← ★★ create 里没有！UPDATE 独有
│
├─ permissionCallBack.xxx()                          ← 权限（主/从）
├─ preUpdateBatch(list)                              ← PreUpdateCallBack
│
├─ ── 变更事件（★ UPDATE 独有）──
├─ ChangeEventData.setCurrent(...)                   ← ★★★ 变更后数据
├─ ChangeEventData.setPrevious(...)                  ← ★★★ 变更前数据
├─ EventContainer.builder()
│    .dtoClass(dtoClass)
│    .actionType(ActionType.UPDATE)
│    .changeData(changeEventData)                    ← ★★★ 不是 eventData，是 changeData
│    .build()
├─ entityEventHelper.beforeEvent(container)
├─ afterBeforeEventCheck(list)
│
├─ ── 密级/快照 ──
├─ secretCallBack.xxx()                              ← 密级校验
├─ entityAttrSnapshotCallBack.xxx()                  ← ★★ 属性快照（create 里没直接见）
│
├─ deleteData(...)                                   ← ★★★ 更新时先删除（子表重建策略！）
├─ recursiveCheck(entityMeta, list, cache)
├─ recursiveUpdate(entityMeta, list, cache)          ← ★★ 递归更新（不是 recursiveCreate）
├─ getMapper() → BaseDao
├─ EntityClassContext.withEntityClass(dao, entityClass, ...)  ← 真正 UPDATE
├─ entityEventHelper.afterEvent(container)
├─ afterUpdate(list)
├─ OperateContext.leave()
├─ resetNormal(list)
└─ entityEventHelper.transactionSuccessEvent(container)
```

**⇒ 五个「create 没有、update 才有」的机制（重要）：**

| 机制 | create | update | 说明 |
|---|---|---|---|
| `oldData` 进上下文 | ❌ | ✅ | **更新必须知道旧值** |
| `billStateCallBack` | ❌ | ✅ | **单据状态只在更新时校验** |
| `ChangeEventData`（前后值） | ❌ | ✅ | **变更事件是 UPDATE 独有的** |
| `changeData` 而非 `eventData` | ❌ | ✅ | **事件载荷类型不同** |
| **`deleteData()` 先删** | ❌ | ✅ | **★★★ 子表更新是「先删后插」** |
| `recursiveUpdate` | ❌ | ✅ | 递归更新而非递归创建 |
| `entityAttrSnapshotCallBack` | ❌ | ✅ | 属性快照 |

**⇒★★★ 最关键发现：`deleteData()` 在 `recursiveUpdate()` 之前调用。**

**⇒ 初始判断为「先删光再重插」，但已用字节码推翻（见 8.0.1M）：**
**⇒ 实际是「只删标注了 `ActionType.DELETE` 的记录」，未标记的保留。**

**⇒ 正确表述：主子表更新 = 差异删除 + 递归更新，不是全删重建。**

#### 8.0.1M ★★★ `deleteData` 真相：按 `ActionType` 过滤的**差异删除**，不是全删

**前面标记为 PARTIAL 的问题，现在用字节码彻底回答了。**

**`deleteData(EntityMeta, Map<Long,D>, boolean)` 只有 34 行，逻辑极简：**

```java
private int deleteData(EntityMeta meta, Map<Long, D> dataMap, boolean flag) {
    AtomicInteger count = new AtomicInteger(0);

    // ① 过滤出「标记为 DELETE」的记录
    Map<Class<?>, List<D>> grouped = dataMap.values().stream()
        .filter(dto -> dto.getActionType() == ActionType.DELETE)   // ★ lambda$deleteData$22
        .collect(Collectors.groupingBy(dto -> dto.getClass()));    // ★ lambda$deleteData$23

    // ② 按元数据逐层删除
    if (MapUtils.isNotEmpty(grouped)) {
        EntityMetaUtil.forEachMeta(meta, (m) -> {
            // ★ lambda$deleteData$28:
            //   Map.get(meta.getDtoClass()) → 该类型的待删列表
            //   Lists.partition(list, N)  → 分批
            //   dao.deleteByIds(ids)      → 真正删除
            //   CacheUtil.evict(...)      → 清缓存
        });
    }
    return count.get();
}
```

**⇒ 三条机制结论（字节码直证）：**

**① 不是「全删子表」，是「只删标注了 ActionType.DELETE 的子表记录」。**

```java
.filter(dto -> dto.getActionType() == ActionType.DELETE)    ← 字节码偏移 21-26
```

**⇒ 这意味着前端/调用方必须显式把要删的子表行标成 DELETE。**
**⇒ 没标 DELETE 的子表行会被保留。**

**② 删除按 DTO 类型分组，再按 EntityMeta 逐层处理。**

```java
Collectors.groupingBy(dto -> dto.getClass())               ← 偏移 31-39
EntityMetaUtil.forEachMeta(meta, consumer)                 ← 偏移 73
```

**⇒ 支持一个主子表里有多种子表类型。**

**③ 删除走 `dao.deleteByIds(ids)` 批量 + `CacheUtil.evict()` 清缓存。**

```java
Lists.partition(list, batchSize)      ← Guava 分批
dao.deleteByIds(ids)                  ← BaseDao 批量删
CacheUtil.evict(entityClass)          ← ★ 清缓存
```

**⇒ 所以「子表 ID 每次保存都变」的真相是：**
**⇒ 只有被标 DELETE 的才删；没标的保留。**
**⇒ 若前端每次提交都不带 actionType，或全标 DELETE，就会表现为「全删重建」。**

**⇒ 这是一个**关键的使用约束**，开发文档必须写清楚：**
```
主子表更新时，子表行必须带 actionType:
  - 新增行 → ActionType.INSERT
  - 修改行 → ActionType.UPDATE
  - 删除行 → ActionType.DELETE
  - 不变行 → ActionType.NORMAL（默认，不删不改）
```

**⇒ 之前文档写的「先删后插」是**不准确**的，已修正为「按标记差异删除」。**

**证据：** `runtime-lowcode-5.3.517/BaseEntityCurdService.javap.txt` 偏移 1763-1806（deleteData）
　　　　+ `lambda$deleteData$22/$23/$28`
**等级：** `VERIFIED_STATIC_BYTECODE`
**修正记录：** 2026-11-17 推翻同轮早前「先删光再重插」的判断

**⇒ 第二个关键发现：`beforeUpdateConsumer` 是 `BiConsumer` 字段**
**⇒ 说明平台允许外部注入「更新前处理逻辑」，这是可配置的扩展点。**

#### 8.0.1L ★★ `create` / `update` / `delete` 三者对照总表

| 阶段 | create | update | deleteById |
|---|---|---|---|
| 前置查询 | — | `selectCascadeById`（旧值） | `selectCascadeById` |
| 上下文 | `enter(newData)` | `enter(newData, **oldData**)` | — |
| 单据状态 | — | **`billStateCallBack`** | — |
| 权限 | `permissionCallBack` | `permissionCallBack` | — |
| 前置回调 | `preCreateBatch` | `preUpdateBatch` | `beforeDelete` |
| 事件载荷 | `eventData` | **`changeData`** | 普通 |
| ActionType | INSERT | UPDATE | DELETE |
| 密级 | `secretCallBack` | `secretCallBack` | — |
| 快照 | — | **`entityAttrSnapshotCallBack`** | — |
| 子表处理 | `recursiveCreate` | **`deleteData`(差异删) + `recursiveUpdate`** | — |
| 落库 | `insert` | `update` | `delete` |
| 后置回调 | `afterCreate` | `afterUpdate` | `afterDelete` |
| 事务事件 | ✅ | ✅ | ✅ |

**⇒ 三者共用同一骨架，差异全是「按 ActionType 分支 + 单据/快照 callback」。**
**⇒ 这是平台设计的核心模式，也是理解所有 CRUD 行为的钥匙。**

#### 8.0.3A ★★★ `recursiveCreate` 真实源码（源码级，比字节码推断更完整）

**之前用字节码推断漏了两个关键动作：逐层 `beforeCreate`/`afterCreate`。**

```java
private int recursiveCreate(EntityMeta entityMeta, List<D> newDtoList) {
    AtomicInteger count = new AtomicInteger(0);
    if (CollectionUtils.isNotEmpty(entityMeta.getChildren())) {
        if (CollectionUtils.isNotEmpty(newDtoList)) {
            newDtoList.stream().forEach(newDto -> entityMeta.getChildren().stream().forEach(meta -> {
                Object dtoList = ReflectFieldUtil.getFieldValue(newDto, meta.getDtoListName());
                if (Objects.nonNull(dtoList)) {
                    ArrayList dtoColl = Lists.newArrayList();
                    if (dtoList instanceof Collection) dtoColl.addAll((Collection) dtoList);
                    else dtoColl.add((BaseEntityActionDto) dtoList);

                    // ★ ① 先递归更深层子表
                    if (CollectionUtils.isNotEmpty(meta.getChildren())) {
                        int i = this.recursiveCreate(meta, dtoColl);
                        count.set(count.get() + i);
                    }
                    // ★ ② 再插本层（注意：递归在前，插入在后）
                    Optional.ofNullable(this.entityBeanContainer.findDao(meta.getEntityClass())).ifPresent(mybatisDao -> {
                        List insetEntityList = BeanCopier.copyList(dtoColl, meta.getEntityClass());
                        BaseEntityCurdService baseEntityCurdService =
                            this.entityBeanContainer.findService(meta.getDtoClass());
                        Optional.ofNullable(baseEntityCurdService)
                                .ifPresent(service -> service.beforeCreate(dtoColl));   // ★★ 逐层回调
                        int k = EntityClassContext.withEntityClass(mybatisDao, meta.getEntityClass(),
                                    () -> mybatisDao.createBatch(insetEntityList));
                        Optional.ofNullable(baseEntityCurdService)
                                .ifPresent(service -> service.afterCreate(dtoColl));    // ★★ 逐层回调
                        count.set(count.get() + k);
                    });
                }
            }));
        }
    } else if (EntityType.MASTER_ENTITY != entityMeta.getEntityType()) {
        // 叶子节点（非主实体）直接批量插入
        Optional.ofNullable(this.entityBeanContainer.findDao(entityMeta.getEntityClass())).ifPresent(mybatisDao -> {
            List insetEntityList = BeanCopier.copyList(newDtoList, entityMeta.getEntityClass());
            BaseEntityCurdService baseEntityCurdService =
                this.entityBeanContainer.findService(entityMeta.getDtoClass());
            Optional.ofNullable(baseEntityCurdService).ifPresent(s -> s.beforeCreate(newDtoList));
            int k = EntityClassContext.withEntityClass(mybatisDao, entityMeta.getEntityClass(),
                        () -> mybatisDao.createBatch(insetEntityList));
            count.set(count.get() + k);
            Optional.ofNullable(baseEntityCurdService).ifPresent(s -> s.afterCreate(newDtoList));
        });
    }
    return count.get();
}
```

**⇒ 三条之前没发现的机制：**

**① 递归顺序是「先深层、后浅层」**
```
主表 → 子表A（有子表A1）→ 先插 A1 → 再插 A  → 主表最后插
```
**⇒ 这叫「自底向上插入」，保证外键依赖成立。**

**② 每一层子表都调用自己的 `beforeCreate` / `afterCreate`**
```java
this.entityBeanContainer.findService(meta.getDtoClass())    // 按子表 DTO 类找对应 service
    .ifPresent(service -> service.beforeCreate(dtoColl));   // 每个实体有自己的回调
```
**⇒ 不是只有主表 service 的回调生效 —— 每层子表的 service 回调都会触发。**

**③ 全部用 `createBatch`，没有单条 `create`**
**⇒ 即使只有一条也是批量接口。**

#### 8.0.3B ★★★ `recursiveUpdate` + `handleSelfUpdate`（差异更新真身）

**`recursiveUpdate` 只负责递归，真正更新在 `handleSelfUpdate`。**

```java
private int recursiveUpdate(EntityMeta entityMeta, List<D> newDtoList, Map<Long,D> oldMap, boolean adminUpdate) {
    AtomicInteger count = new AtomicInteger(0);
    if (CollectionUtils.isNotEmpty(entityMeta.getChildren())) {
        newDtoList.forEach(newDto -> entityMeta.getChildren().forEach(meta -> {
            Object dtoList = ReflectFieldUtil.getFieldValue(newDto, meta.getDtoListName());
            if (Objects.nonNull(dtoList)) {
                ArrayList dtoColl = ...;
                if (CollectionUtils.isNotEmpty(meta.getChildren())) {
                    count.set(count.get() + this.recursiveUpdate(meta, dtoColl, oldMap, adminUpdate));  // 递归
                }
                this.handleSelfUpdate(count, meta, dtoColl, oldMap, adminUpdate);   // 本层更新
            }
        }));
    } else if (EntityType.MASTER_ENTITY != entityMeta.getEntityType()) {
        this.handleSelfUpdate(count, entityMeta, newDtoList, oldMap, adminUpdate);
    }
    return count.get();
}
```

**`handleSelfUpdate` —— 按 actionType 分组，只处理 INSERT / UPDATE：**

```java
private void handleSelfUpdate(AtomicInteger count, EntityMeta meta, List<D> dtoColl,
                              Map<Long,D> oldMap, boolean adminUpdate) {
    Optional.ofNullable(this.entityBeanContainer.findDao(meta.getEntityClass())).ifPresent(mybatisDao -> {
        // ★ 按 actionType 分组成 Map<ActionType, List<DTO>>
        Map<ActionType, List<BaseEntityActionDto>> actionTypeMap = dtoColl.stream()
            .filter(a -> Objects.nonNull(a.getActionType()))          // ← 无 actionType 的直接丢弃
            .collect(Collectors.groupingBy(BaseEntityActionDto::getActionType));

        actionTypeMap.forEach((key, value) -> {
            if (ActionType.INSERT == key) {
                List insetEntityList = adminUpdate
                    ? BeanCopier.copyList(value, meta.getEntityClass(), CopyStrategy.IGNORE_NULL)
                    : BeanCopier.copyList(value, meta.getEntityClass());
                BaseEntityCurdService svc = this.entityBeanContainer.findService(meta.getDtoClass());
                if (!adminUpdate) Optional.ofNullable(svc).ifPresent(s -> s.beforeCreate(value));
                int i = EntityClassContext.withEntityClass(mybatisDao, meta.getEntityClass(),
                            () -> mybatisDao.createBatch(insetEntityList));
                // ★★ 主键回填：从 entity 读回写 DTO
                for (int j = 0; j < insetEntityList.size(); ++j) {
                    value.get(j).setId(((BaseEntity)insetEntityList.get(j)).getId());
                }
                count.set(count.get() + i);
                if (!adminUpdate) Optional.ofNullable(svc).ifPresent(s -> s.afterCreate(value));

            } else if (ActionType.UPDATE == key) {
                List updateEntityList = BeanCopier.copyList(value, meta.getEntityClass());
                int i = EntityClassContext.withEntityClass(mybatisDao, meta.getEntityClass(),
                            () -> mybatisDao.updateBatch(updateEntityList));
                count.set(count.get() + i);
                BaseEntityCurdService svc = this.entityBeanContainer.findService(meta.getDtoClass());
                List ids = value.stream().map(BaseEntityActionDto::getId).collect(Collectors.toList());
                Optional.ofNullable(svc).ifPresent(s -> {
                    if (!adminUpdate) s.afterUpdate(value, oldMap);   // ★ 带 oldMap
                    CacheUtil.evict(s.getClass(), ids);                // ★ 清缓存
                });
            }
            // ★★★ 没有 DELETE / NORMAL 分支！
        });
    });
}
```

**⇒ 四条关键结论：**

| # | 结论 | 含义 |
|---|---|---|
| **1** | **`handleSelfUpdate` 只处理 INSERT 和 UPDATE** | **DELETE 和 NORMAL 不在这里处理** |
| **2** | DELETE 已在前置 `deleteData()` 完成 | 所以这里是「先删后更新」的分工 |
| **3** | NORMAL 的 DTO 直接**被丢弃** | 不改不动，符合语义 |
| **4** | 无 `actionType` 的 DTO **被 filter 过滤掉** | 静默跳过，不报错 |

**⇒★★ 这是最重要的隐性约束：**
**⇒ 若子表行没带 `actionType`，更新时会被静默忽略（不报错、不更新）。**
**⇒ 这解释了「改了子表但没生效」的常见现象。**

**⇒ 对比 create 与 update 的子表策略：**

| 阶段 | create | update |
|---|---|---|
| 子表处理顺序 | 递归(深→浅) → 插入 | deleteData(差异删) → 递归(深→浅) → 分组处理 |
| INSERT | `createBatch` 全量 | `createBatch`（按 actionType 分组后）|
| UPDATE | — | `updateBatch` |
| DELETE | — | **在 `deleteData` 里，此处不处理** |
| NORMAL | — | **丢弃（不改）** |
| 无 actionType | `resetInsert` 统一置 INSERT | **静默过滤丢弃** |
| 主键回填 | 由 `resetInsert` 预生成 | INSERT 分支从 entity 读回写 |

#### 8.0.3C ★★ `recursiveCheck` 的 4 条校验规则（源码级）

```java
private String checkSystemAttribute(D parentDto, List<D> childDtoList, List<D> newDtoList, Map<Long,D> oldMap) {
    ActionType parentActionType = parentDto.getActionType();
    Long parentId = parentDto.getId();
    StringBuilder errorMsg = new StringBuilder();

    for (BaseEntityActionDto child : childDtoList) {
        Object parentIdObj = ReflectFieldUtil.getFieldValue(child, "parentId");

        // 规则① parentId 为空 → 自动回填
        if (Objects.equals(NULL_ID, parentIdObj) || Objects.isNull(parentIdObj)) {
            ReflectFieldUtil.setFieldValue(child, "parentId", parentId);
            continue;
        }
        // 规则② parentId 不匹配 → 报 ENTITY_0031
        if (!Objects.equals(parentId, parentIdObj)) {
            String message = messageRepository.getMessage("error.code.ENTITY_0031",
                new String[]{child.getClass().getName(), parentIdObj, parentId});
            errorMsg.append(message).append(";");
        }
    }

    if (ActionType.UPDATE == parentActionType && Objects.nonNull(oldMap)) {
        // 规则③ UPDATE 时，父 ID 必须在 oldMap 里，否则 ENTITY_0032
        if (!oldMap.containsKey(parentId)) {
            errorMsg.append(messageRepository.getMessage("error.code.ENTITY_0032", ...));
        }
        // 规则④ UPDATE 的子行 ID 也必须在 oldMap 里，否则 ENTITY_0032
        childDtoList.stream()
            .filter(child -> ActionType.UPDATE.equals(child.getActionType()))
            .forEach(child -> {
                if (!oldMap.containsKey(child.getId())) {
                    errorMsg.append(messageRepository.getMessage("error.code.ENTITY_0032", ...));
                }
            });
    }
    return errorMsg.toString();
}
```

**四条校验规则（可直接用于排查）：**

| # | 规则 | 错误码 | 触发条件 |
|---|---|---|---|
| ① | parentId 自动回填 | — | 子表 parentId 为空 |
| ② | parentId 必须匹配 | **ENTITY_0031** | 子表 parentId ≠ 当前父 ID |
| ③ | UPDATE 父必须存在 | **ENTITY_0032** | 更新时父 ID 不在数据库 |
| ④ | UPDATE 子必须存在 | **ENTITY_0032** | 更新时子行 ID 不在数据库 |

**⇒ 报错信息由 `messageRepository.getMessage("error.code.ENTITY_00xx", args)` 生成。**
**⇒ 所有错误聚合到 `StringBuilder`，最后一次抛出 `BusinessException("UDC_COMMON_0003", {msg})`。**

**⇒ 这意味着：一次保存会报出**所有**校验错误，不是遇到第一个就停。**

#### 8.0.3 递归操作（主子表的核心）

| 方法 | 签名 | 说明 |
|---|---|---|
| `recursiveCreate` | `(EntityMeta, List<D>): int` | **递归创建（主+子）** |
| `recursiveUpdate` | `(EntityMeta, List<D>, Map<Long,D>): int` | **递归更新** |
| `recursiveUpdate` | `(EntityMeta, List<D>, Map<Long,D>, boolean): int` | 带标志版 |
| `recursiveDelete` | `(EntityMeta, Map<Long,D>): int` | **递归删除（级联）** |
| `recursiveCheck` | `(EntityMeta, List<D>, Map<Long,D>): void` | 递归校验 |
| `recursiveCheck` | `(..., StringBuilder): void` | 带错误收集 |
| `recursiveSelect` | `(Collection<Long>, List<D>): void` | 递归查询 |
| `recursiveSelectWithCondition` | `(Collection<Long>, List<D>, Map<String,...>): void` | 条件递归查询 |
| `recursiveDefaultValue` | `(EntityMeta, D): void` | **★ 递归默认值（表达式！）** |
| `recursiveEntityRuntimeData` | `(EntityMeta, D, RecursiveType): D` | 递归运行时数据 |

**★★ 这直接回答了「主子表怎么入数据」的机制层：**
```
recursiveCreate(EntityMeta, List<D>)
  → 按 EntityMeta.getChildren() 递归
  → 每一层调 create/createBatch
```

**⚠️ 但「主表 ID 何时生成、子表外键何时回填」仍需实测确认。**

#### 8.0.2 级联查询

| 方法 | 签名 |
|---|---|
| `selectCascadeById` | `(Long): D` |
| `selectCascadeByIds` | `(Collection<Long>): List<D>` |
| `doSelectCascadeById` | `(Long): D` |
| **`doParallelSelectCascadeById`** | `(Long): D` | **并行级联** |
| `setSingeSubDtoList` | `(Long, D, EntityMeta, Supplier<...>)` | 单子表 |
| `setMultiSubDtoList` | `(Collection<Long>, List<D>, EntityMeta, Supplier<...>)` | 多子表 |
| `handleSubRelation` | `(List<BaseEntityActionDto>, EntityMeta, Supplier<...>)` | **处理子关系** |
| `getChildDtoFromMap` | `(Map<String,Object>, EntityMeta): Object` |
| `checkChildEntityData` | `(Map<String,Object>): void` |
| `selectCascadeListByConditions` | `(List<MapConditionDto>): List<D>` |
| `selectCascadeListByWrapper` | `(Wrapper): List<D>` |
| `selectCustomCascadeByCondition` | `(QueryConditionDto): D` |
| `selectOne2OneCascadeByDyCondition` | `(QueryConditionDto): D` |
| `recursiveSelectOne2OneCascadeByCondition` | `(...)` |

**⇒ 主子表查询是「一次查主 + 递归查子 + 内存拼装」，不是 SQL JOIN。**
**⇒ `doParallelSelectCascadeById` 说明有并行优化。**

#### 8.0.3 ★ 推翻「DAO 无 join」的判断

```java
BaseEntityCurdService
  # dynamicJoinSelect(ProxyJoinParamDto): PageData<D>        ← ★ JOIN 查询
  # dynamicCountJoinSelect(ProxyJoinParamDto): Integer        ← JOIN 计数
  # dynamicSelect(ProxyParamDto): PageResponse<D>
  # setJdbcDriverIfNecessary(ProxyJoinParamDto): void
```

**⇒ 平台**支持**动态 JOIN 查询，走 `com.seeyon.boot.starter.dynamicsql` 包。**
**⇒ 我之前「DAO 层无 join」的判断被推翻——41 个 DAO 方法确实没有，但 `BaseEntityCurdService` 有。**

**⚠️ 注意：`dynamicSelect` 返回 `PageResponse<D>`（transport 类型），而其他方法返回 `PageData<D>`（boot 类型）。两种分页类型并存。**

#### 8.0.4 ★ 单据相关方法

| 方法 | 签名 | 说明 |
|---|---|---|
| **`handlerCaseId`** | `(D): void` | **★ 处理 caseId（流程实例）** |
| **`create4Bpm`** | `(D): ResultDto` | **★ 为 BPM 创建单据** |
| **`create4BpmInternal`** | `(D, ApprovalContext): D` | 内部实现 |
| **`isMainProcess`** | `(ApprovalContext): boolean` | 是否主流程 |
| **`update4Bpm`** | `(D): ResultDto` | **★ 为 BPM 更新单据** |
| **`updateStatusType`** | `(D): int` | **★ 更新状态类型** |
| `processingTemplateData` | `(D): D` | 模板数据处理 |
| `processingForwardData` | `(D): D` | 流转数据处理 |

**★★ 这直接回答了「单据怎么入数据」：**

```
普通实体：create(D)
单据：    create4Bpm(D): ResultDto     ← 走 BPM
         handlerCaseId(D)             ← 补 caseId
         updateStatusType(D)          ← 维护状态
```

**⇒ 单据**不能**直接用 `create()`，必须走 `create4Bpm()`。**
**⇒ 这回答了「哪些操作不能直接用 DAO」——至少创建/更新单据要走 BPM 方法。**

**⚠️ 但 `create4Bpm` 内部是否真的调 BPM 引擎、是否要求流程模板，仍需实测。**

#### 8.0.5 其他关键方法

| 方法 | 签名 | 说明 |
|---|---|---|
| `createWithResult` | `(D): D` | 创建并返回结果 |
| `updateWithResult` | `(D): D` | 更新并返回 |
| `updateBatchWithResult` | `(List<D>): List<D>` | 批量带结果 |
| `updateNoEvents` | `(D): int` | **不触发事件更新** |
| `updateWithFields` | `(Map<String,Object>): int` | 按 Map 更新 |
| `updateBase` | `(D, boolean, boolean): int` | 基础更新 |
| `updateRootEntity` | `(D): int` / `(D, D): int` | **更新根实体** |
| `forceUpdate` | `(D): ForceUpdateResultDto` | 强制更新 |
| `resetNormal` | `(List<D>): void` | **★ 重置普通字段** |
| `operateRootBatch` | `(List<D>): int` | 根实体批量操作 |
| `copyAndInsert` | `(Long): Long` | 复制并插入 |
| `runtimeCopy` | `(Long): D` | 运行时复制 |
| `validateCreate` / `validateUpdate` / `validate` | `(List<D>): List<D>` / `(D): D` | 校验 |
| `uniqueFieldCheck` | `(EntityMeta, BaseEntityActionDto, List<D>, Map<...>)` | 唯一性校验 |
| `getCascadeDefaultValue` | `(): D` / `(String): D` | **级联默认值** |
| `importEntityInitData` | `(ExcelImportTransDto): List<ExcelImportResult>` | Excel 导入 |
| `listToMap` | `(List<D>): Map<Long,D>` | 转 Map |
| **`printTransactionInfo`** | `(): void` | **★ 打印事务信息** |
| `getEntityMeta` | `(): EntityMeta` | **★ 实体元数据** |
| `getMapper` | `(): DAO` | 取底层 DAO |

**★ `resetNormal(List<D>)` — 极可能与 `copyNeedResetNull` 是同一套逻辑的运行时侧。**
**⚠️ 未证。但这是目前最接近的线索。**

**★ `updateNoEvents` 的存在说明：默认 `update()` 会触发事件，需要时可不触发。**

### 8.0.6 `BaseCurdService` 接口（35 方法）

```java
com.seeyon.boot.starter.lowcode.core.BaseCurdService    ← interface
```

**★ 关键方法：**
```java
selectByParentId(Long): List<D>                    ← ★ 按父 ID 查子（主子表查询）
selectByParentIdIgnoreSort(Long): List<D>
selectByParentIds(Collection<Long>): List<D>       ← 批量按父查
selectByParentIdsIgnoreSort(Collection<Long>): List<D>
selectExceedsOneThousandRecordsByInCondition(String, Object): boolean  ← ★ 超 1000 条检查
selectCountByWrapper(Wrapper): int
selectPageByWrapper(PageInfo, Wrapper): PageData<D>
selectFuncByConditions(...)
afterBeforeEventCheck(List<D>): void
```

**★★ `selectExceedsOneThousandRecordsByInCondition(...)` — 平台自己就有「IN 条件超 1000 条」的保护检查！**
**⇒ 这印证了 Oracle IN 列表 1000 上限的处理，平台已内置。**

### 8.0.7 `EntityMeta`（运行时实体元数据，★ 关键对象）

```java
com.seeyon.boot.starter.lowcode.core.EntityMeta
  # getEntityType(): EntityType              ← 实体类型（枚举）
  # getEntityCategory(): String              ← 实体分类
  # getRelationType(): RelationType          ← ★ 关联类型（枚举）
  # getEntityId(): Long
  # getEntityTable(): String                 ← ★★ 实体 → 物理表名！
  # getName() / getCaption() / getStereotype()
  # getEntityClass(): Class<?>               ← 实体类
  # getDtoClass(): Class<?>                  ← DTO 类
  # getDtoListName(): String
  # getParentFullName() / getFullName()
  # isSortField(): boolean
  # getChildren(): List<EntityMeta>          ← ★ 子实体（主子表）
  # getAttributes(): List<AttributeMeta>     ← 字段元数据
  # getTopParent(): EntityMeta               ← ★★ 顶层父实体（多级主子表）
```

**★★ 三个关键结论：**
1. **`getEntityTable(): String` = 实体到物理表的映射**（运行时可直接取表名）
2. **`getChildren(): List<EntityMeta>` = 主子表树**
3. **`getTopParent(): EntityMeta` = 支持多级主子表**（孙表也能找到根）

**⇒ 这是运行时元数据模型，与设计态 `EntityDto` 对应。**

### 8.0.8 `AttributeMeta`（运行时字段元数据）

```java
com.seeyon.boot.starter.lowcode.core.AttributeMeta
  # getFullName() / getName() / getCaption() / getDescription()
  # isMultiSelect(): boolean                 ← 多选
  # isDataI18n(): boolean                    ← 数据国际化
  # getDataType(): String                    ← ★ 数据类型
  # getRealDataType(): String                ← ★★ 真实数据类型
  # getRelationAppName(): String             ← ★ 关联应用
  # getRelationEntity(): String              ← ★★ 关联实体
  # getUseSnapshot(): Boolean                ← 快照
  # getAttrGuid(): Long
  # getMaskType(): Maskable                  ← 脱敏类型
```

**★★ `getDataType()` vs `getRealDataType()` — 两个类型字段。**
**⇒ 推论（待证）：`dataType` 是逻辑类型（如 ENTITY），`realDataType` 是物理列类型（如 BIGINT）。**
**⚠️ 不得断言，需反编译或查 DDL。**

**★★ `getRelationEntity(): String` — 关联字段指向的实体名，这是关联关系的运行时表达。**

### 8.1 元数据层（来自专题 1）

```java
EntityDto#getParent(): EntityDto              ← 自引用父
EntityDto#getChildren(): List<EntityDto>      ← 自引用子
EntityDto#getHasChild(): Boolean
EntityDto#getGenerateAggregateValidateClass(): Boolean
EntityDto#getGenerateAggregateAssignClass(): Boolean
EntityDto#getGenerateAggregateDefaultValueClass(): Boolean

Entity4CodeDto#getParentEntityId(): Long
Entity4CodeDto#getMultiplicity(): EntityRelationMultiplicityEnum
```

**⇒ 主子表 = 实体树（自引用），不是「两张表 + 独立外键」。**

### 8.2 生成层（来自专题 2）

| 类 | 方法 |
|---|---|
| `EntityRuleTask` | `generateAggregateRootEntityRule(CodeContext, Map<String,Entity4CodeDto>, Set<String>)` |
| `EntityRuleTask` | `generateRootEntityRuleCode(..., EntityRuleAggregateTemplate, ...)` |
| `EntityRuleAggregateTemplate` | `getLayerMap(): Map<String,List<String>>` / `getCapRootEntityName()` / `getTargetGroupType()` / `getRootEntityAssignValueServiceOutPath()` |
| `FilterPlanTask` | `getMasterEntity(Long, String, Map<Long,EntityDto>): EntityDto` |
| `FilterPlanTask` | `getAggEntityAllAttribute(EntityDto, Map<Long,AttributeDto>, List<...>)` |
| `PageEntityControllerTask` | `buildChildrenEntityMultimap(Map<String,UdcEntityMetaDataDto>): Multimap` |
| `PageEntityControllerTask` | `containOne2One(...)` / `buildOne2oneEntityInfo4Up/Down` |

**⇒ `getLayerMap()` 说明主子表是「分层」结构（可能支持多级）。**
**⇒ `buildChildrenEntityMultimap` 说明子实体按父 ID 分组。**

### 8.3 运行时（❌ 全部未证）

| 问题 | 状态 |
|---|---|
| 主表 ID 何时生成 | `BLOCKED`（需实测） |
| 子表外键谁回填 | `BLOCKED` |
| 保存顺序 | `BLOCKED` |
| 更新策略（全量 vs 增量） | `BLOCKED` |
| 删除策略（级联 vs 手动） | `BLOCKED` |
| 事务范围 | `BLOCKED` |

**⇒ 这是本专题最大的空白。**
**⇒ 静态只能证「结构是实体树」，不能证「怎么保存」。**

---

## 9. 单据

### 9.0A ★★★ `create4Bpm` 完整链路（源码级）

**入口签名变了：返回 `ResultDto`，不是 void。**

```java
public ResultDto create4Bpm(@Nonnull D frontDto) {
    // ① 前端没给 ID 就先生成（注意：这里就生成了！）
    if (null == frontDto.getId()) {
        frontDto.setId(Ids.gidLong());
    }
    BaseEntityCurdService<D> svc = this.getBaseEntityCurdService();
    ApprovalContext<D> context = new ApprovalContext<>();
    context.putProcessData(frontDto);
    svc.create4BpmInternal(frontDto, context);

    ResultDto resultDto = new ResultDto();
    HashMap<String, Object> map = new HashMap<>(2);
    map.put("bpm", context.getParamter("bpm"));      // ← BPM 相关结果
    resultDto.setResultMap(map);
    resultDto.setId(frontDto.getId());
    return resultDto;
}
```

**`create4BpmInternal` —— 真正的单据创建：**

```java
public D create4BpmInternal(D frontDto, ApprovalContext context) {
    BaseEntityCurdService<D> svc = this.getBaseEntityCurdService();

    // ① 目标状态必须存在
    Enum targetStatusType = ReflectFieldUtil.getFieldValue(frontDto, "statusType");
    if (Objects.isNull(targetStatusType)) {
        throw BusinessException.message("目标状态错误：目标状态为空");
    }

    // ② ★ 老表单兼容：PENDING_REVIEW → TO_BE_SUBMITTED
    if ("PENDING_REVIEW".equals(targetStatusType.name())) {
        log.warn("老表单逻辑：发起走udc，单据状态设置为：TO_BE_SUBMITTED");
        Map enumMap = EnumUtils.getEnumMap(targetStatusType.getClass());
        ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
    }
    context.putTargetStatusType(targetStatusType.name());

    // ③ 审批前置回调
    this.approvalCallBack.beforeApprovalCreate(context);

    // ④ 走普通 create（含全部 callback + 主子表递归）
    svc.create(frontDto);

    // ⑤ 快照一份（用于后续比对）
    BaseEntityActionDto oldDto = BeanCopier.copy(frontDto, this.dtoClass);

    try {
        // ⑥ 审批后置回调（真正发 BPM）
        this.approvalCallBack.afterApprovalCreate(context);

        // ⑦ ★ BPM 失败降级：状态回退到 TO_BE_SUBMITTED
        if (context.hasException()) {
            log.info("数据id{},bpm流程有异常：{},状态置为待提交",
                     frontDto.getId(), context.getErrorMsg());
            Map enumMap = EnumUtils.getEnumMap(targetStatusType.getClass());
            ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
        }
    } catch (Exception e) {
        // ⑧ 抛异常也要先落库状态，再抛出
        log.warn("startProcess fail:{}", frontDto.getId(), e);
        Map enumMap = EnumUtils.getEnumMap(targetStatusType.getClass());
        ReflectUtil.setFieldValue(frontDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
        this.updateStatusType(frontDto);          // ★ 单独更新状态
        ExceptionUtils.rethrow(e);                 // ★ 然后才抛出
    }

    // ⑨ 主流程才更新 root（BPM 子流程不更新）
    if (this.isMainProcess(context)) {
        this.updateRootEntity(oldDto, frontDto);
    }
    return frontDto;
}
```

**⇒ 五个关键机制：**

| # | 机制 | 说明 |
|---|---|---|
| ① | **ID 在 BPM 前就生成** | `create4Bpm` 第一行 `if (id==null) setId(Ids.gidLong())` |
| ② | **状态先改后建** | `PENDING_REVIEW` → `TO_BE_SUBMITTED` 在 create 之前 |
| ③ | **BPM 失败不丢数据** | 单据已落库，状态降级为「待提交」，不抛异常 |
| ④ | **抛异常也先存状态** | catch 里 `updateStatusType` 后再 rethrow |
| ⑤ | **子流程不更新 root** | `isMainProcess(context)` 判断 `bpmProcessType` |

##### 单据状态机（`statusType` 取值，从源码反推）

| 状态 | 含义 | 出现位置 |
|---|---|---|
| `NONE` | 无状态 | `update4Bpm` 判断可走 BPM |
| `DRAFT` | 草稿 | 同上 |
| **`TO_BE_SUBMITTED`** | **待提交** | BPM 失败/异常时的降级态 |
| `PENDING_REVIEW` | 待审（老表单） | 会被转成 `TO_BE_SUBMITTED` |

**⇒ `update4Bpm` 只在 `NONE` / `DRAFT` / `TO_BE_SUBMITTED` 时才允许走 BPM，其他状态直接跳过 BPM。**

### 9.0B ★★★ `update4Bpm` 完整链路

```java
public ResultDto update4Bpm(@Nonnull D frontDto) {
    // ① 目标状态必须存在
    Enum targetStatusType = ReflectFieldUtil.getFieldValue(frontDto, "statusType");
    if (Objects.isNull(targetStatusType)) throw BusinessException.message("目标状态错误：目标状态为空");

    // ② ★ 可选的状态检查开关
    boolean checkStatusType = MapUtils.getBoolean(frontDto.getExtendMap(), "checkStatusType", false);
    Long id = frontDto.getId();
    Asserts.notNull(id, "id");                       // ★ id 必须非空
    boolean callBpm = true;

    if (checkStatusType) {
        Enum oldStatus = this.selectBillStatusById(id);
        if (Objects.nonNull(oldStatus)) {
            // ③ ★★ 只有 NONE / DRAFT / TO_BE_SUBMITTED 才允许进 BPM
            if (!("NONE".equals(oldStatus.name())
               || "DRAFT".equals(oldStatus.name())
               || "TO_BE_SUBMITTED".equals(oldStatus.name()))) {
                ReflectUtil.setFieldValue(frontDto, "statusType", null);
                callBpm = false;
                log.warn("表单状态：数据库状态为-{},目标状态为-{},不进行任何bpm操作!", oldStatus, targetStatusType);
            } else {
                log.warn("表单状态：数据库状态为-{},目标状态为-{},执行bpm逻辑。", oldStatus, targetStatusType);
            }
        }
    }

    ApprovalContext<Object> context = new ApprovalContext<>();
    context.putProcessData(frontDto);
    context.putTargetStatusType(targetStatusType.name());

    if (callBpm) {
        if ("PENDING_REVIEW".equals(targetStatusType.name())) {
            // ④ 老表单兼容，同 create
            ReflectUtil.setFieldValue(frontDto, "statusType", /* TO_BE_SUBMITTED */);
        }
        this.approvalCallBack.beforeApprovalUpdate(context);   // ⑤ 审批前置
    }

    // ⑥ 走普通 update（含 deleteData + recursiveUpdate）
    D dbDto = this.getBaseEntityCurdService().updateWithResult(frontDto);
    BaseEntityActionDto frontCopyDto = BeanCopier.copy(frontDto, this.dtoClass);

    if (callBpm) {
        try {
            context.putProcessData(frontCopyDto);
            this.approvalCallBack.afterApprovalUpdate(context);    // ⑦ 审批后置
        } catch (Exception e) {
            log.warn("startProcess fail:{}", frontCopyDto.getId(), e);
            // ⑧ 失败降级：状态 → TO_BE_SUBMITTED（不 rethrow！）
            Object statusType = ReflectFieldUtil.getFieldValue(frontCopyDto, "statusType");
            Map enumMap = EnumUtils.getEnumMap(statusType.getClass());
            ReflectUtil.setFieldValue(frontCopyDto, "statusType", enumMap.get("TO_BE_SUBMITTED"));
        }
        if (this.isMainProcess(context)) {
            this.updateRootEntity(dbDto, frontCopyDto);
        }
    }
    ...
}
```

**⇒ `create4Bpm` 与 `update4Bpm` 的关键区别：**

| 项 | create4Bpm | update4Bpm |
|---|---|---|
| ID | 无则生成 | **必须已存在（Asserts.notNull）** |
| 状态检查 | 无 | **有 `checkStatusType` 开关** |
| BPM 失败 | **rethrow（先存状态）** | **不 rethrow，只降级** |
| 底层调用 | `create()` | `updateWithResult()` |
| 能力 | 建单 + 起流程 | 改单 + 可能起流程 |

**⇒★★ 最关键的运维知识：** 
**`update4Bpm` 在状态非 `NONE/DRAFT/TO_BE_SUBMITTED` 时会「静默跳过 BPM」——不报错，只打 warn 日志。**
**⇒ 这解释了「改了单子但流程没动」的现象。**

### 9.0C ★ `updateStatusType` —— 只更新状态一个字段

```java
public int updateStatusType(@Nonnull D rootDto) {
    BaseEntity entity = BeanCopier.copy(rootDto, this.entityClass);
    Object mapper = this.getMapper();
    int i = EntityClassContext.withEntityClass(mapper, this.entityClass,
        () -> mapper.updateColumnsIgnoreVersion(entity,
                Sets.newHashSet("statusType")));   // ★ 只更新 statusType 一列
    return i;
}
```

**⇒ 这是「只改状态」的专用方法，绕过全部 callback 和事件。**
**⇒ 用在 BPM 异常降级场景 —— 因为此时不能触发业务事件。**

### 9.0D ★★ `updateRootEntity` —— 只更新主表指定列

```java
public int updateRootEntity(@Nonnull D oldRootDto, @Nonnull D newRootDto) {
    // ① 子表全部置 NORMAL（不动子表）
    Consumer<BaseEntityActionDto> consumer = DtoFieldHelper::resetChildNormal;
    newRootDto = DtoConvertUtil.forEach(this.entityMeta, newRootDto, consumer);

    // ② 主表置 UPDATE
    newRootDto.setActionType(ActionType.UPDATE);
    if (newRootDto instanceof BaseRootDto) {
        ((BaseRootDto)newRootDto).getLinkSourceIds().clear();
    }

    // ③ 构造变更事件（前后值）
    ChangeEventData changeData = new ChangeEventData();
    changeData.setCurrent(newRootDto);
    changeData.setPrevious(oldRootDto);
    EventContainer container = this.isMasterEntity
        ? EventContainer.builder().dtoClass(this.dtoClass)
            .actionType(ActionType.UPDATE)
            .changeData(Lists.newArrayList(changeData)).build()
        : null;
    this.entityEventHelper.beforeEvent(container);

    // ④ 只更新 root 相关列（getUpdateRootFiled 决定哪些列）
    BaseEntity entity = BeanCopier.copy(newRootDto, this.entityClass);
    Object mapper = this.getMapper();
    int i = EntityClassContext.withEntityClass(mapper, this.entityClass,
        () -> mapper.updateColumnsIgnoreVersion(entity, this.getUpdateRootFiled(entity)));

    CacheUtil.evict(this.getClass(), Lists.newArrayList(newRootDto.getId()));
    this.entityEventHelper.afterEvent(container);
    this.entityEventHelper.transactionSuccessEvent(container);
    return i;
}
```

**⇒ 「root 字段」由 `getUpdateRootFiled(entity)` 决定，不是全部字段。**
**⇒ 这是「单据状态等系统字段的专用更新通道」，子表完全不动。**

### 9.1 字段级区别（来自专题 1）

`billBasic` 13 字段，与 BPM 强绑定：

| 字段 | 类型 | 说明 |
|---|---|---|
| `caseId` | ENTITY | **流程实例** |
| `templateId` | ENTITY | **流程模板** |
| `caseTitle` | STRING | 流程标题 |
| `caseSendTime` | DATETIME | 发起时间 |
| `caseFinishTime` | DATETIME | 流程结束时间 |
| `billCode` | **Serial** | 单据编号 |
| `billDate` | DATETIME | 单据日期 |
| `applicant` | ENTITY | 申请人 |
| `caseSender` + 机构/部门/岗位 | ENTITY ×4 | 发起人五元组 |
| `deductionInfo` | MULTILINESTRING | 扣减规则信息 |

### 9.2 状态机（来自专题 1）

```
DRAFT(0) → TO_BE_SUBMITTED(1) → PENDING_REVIEW(2) → COME_INTO_FORCE(3)
                                                    ├→ TERMINATED(4)
                                                    ├→ NULLIFIED(5)
                                                    ├→ SUSPENDED(6)
                                                    └→ FAILED(7)
```

**⇒ 8 状态，其中 3 个（4/5/6）由 3 个操作特性触发。**

### 9.3 生成层

| 类 | 方法/资源 |
|---|---|
| `EntityFileTemplate` | `resolveBpmProcess(Map, EntityDto)` |
| `EntityFileTemplate` | `getApprovalSet(): Set<String>` |
| `PageEntityControllerTask` | `isBillEntity(String): boolean` |
| `_codegen_templates.json` | `common/macro-appservice-approval.ftl` |

### 9.4 运行时（❌ 全部未证）

| 问题 | 状态 |
|---|---|
| 单据保存 vs 普通实体保存的区别 | `BLOCKED` |
| 提交后状态谁维护 | `BLOCKED` |
| 哪些操作不能直接用 DAO | `BLOCKED` |
| `caseId` 如何获得 | `BLOCKED` |

---

## 10. 事务

### 10.1 已证：平台有事务级事件

```
TransactionSuccessCreateEvent   CREATE  TRANSACTION_SUCCESS
TransactionSuccessUpdateEvent   UPDATE  TRANSACTION_SUCCESS
TransactionSuccessDeleteEvent   DELETE  TRANSACTION_SUCCESS
```

**⇒ 平台区分「方法级（BEFORE/AFTER）」和「事务级（TRANSACTION_SUCCESS）」。**

### 10.2 ★ 已证：平台开启注解式事务

```
注解：com.seeyon.boot.annotation.BootApp
元素数：8
@Target：TYPE
元注解：SpringBootApplication, EntityScan, ComponentScan, EnableScheduling,
        EnableAsync, EnableAspectJAutoProxy, **EnableTransactionManagement**, Import
构件：boot-core / boot-core-5.3.600.jar
```

**⇒ `@BootApp` 带 `@EnableTransactionManagement`**
**⇒ 平台开启了 Spring 注解式事务 → 事务边界由 `@Transactional` 控制。**

**证据等级：** `STATIC_RULE`（注解元注解逐字）
**⚠️ 仍未证：** 哪些方法标了 `@Transactional`、传播行为、超时设置

### 10.3 未证

| 问题 | 状态 |
|---|---|
| 一次 `create` 是否单事务 | `BLOCKED` |
| `@Transactional` 具体标在哪些方法 | `BLOCKED`（需注解实例数据） |
| 批量写入是否分批事务 | `BLOCKED` |
| 事件异常是否回滚事务 | `BLOCKED` |

**⚠️ `TRANSACTION_SUCCESS` + `@EnableTransactionManagement` 只证明「有事务机制」，不证明「事务范围多大」。**

---

## 10A. 幂等与并发控制（★ 本轮新增）

### 10A.1 平台自带 4 个注解

| 注解 | 全限定名 | 元素 | Target | 构件 |
|---|---|---|---|---|
| **`@Idempotent`** | `com.seeyon.boot.starter.appservice.annotation.Idempotent` | **0** | METHOD | `boot-starter-appservice-5.3.600.jar` |
| **`@AntiReCommit`** | `com.seeyon.boot.starter.web.annotation.AntiReCommit` | **2** | METHOD | `boot-starter-web-5.3.600.jar` |
| **`@ExclusivePermit`** | `com.seeyon.udc.common.concurrent.ExclusivePermit` | **2** | METHOD | `udc-biz-5.3.517.jar` |
| **`@LimitCountOperation`** | `com.seeyon.udc.limit.LimitCountOperation` | **2** | METHOD | `udc-biz-5.3.517.jar` |

**⇒ 平台有完整的幂等/防重/互斥/限流注解体系，不需要自己实现。**

**⇒ 分工推断：**
```
@Idempotent          幂等（同一请求多次执行结果一致）
@AntiReCommit        防重复提交（表单重复点击）
@ExclusivePermit     互斥（同一资源不允许并发）
@LimitCountOperation 限流（次数限制）
```

**⚠️ 全部为 `METHOD` 级；`@Idempotent` 是 0 元素纯标记 → 幂等 key 从哪来、有效期多久，由框架内部决定，未证。**

**⇒ 这与用户复盘文档里「幂等写入用条件精确查询」的做法可以互补：**
- 平台注解：方法级幂等保护
- 业务层：条件精确查询 + 唯一索引

**证据等级：** `STATIC_RULE`（注解存在）
**⚠️ 未证：** 实现机制、key 生成规则、失效策略

### 10A.2 ★ `@CountSql`：COUNT SQL 控制

```
注解：com.seeyon.boot.starter.mybatis.annotation.CountSql
元素数：1
@Target：METHOD
构件：boot-starter-mybatis-5.3.600.jar
```

**⇒ 这是 mybatis 层的方法级注解，控制 COUNT SQL 生成。**
**⇒ 与 `PageInfo#isNeedTotal(false)` 很可能属于同一套「避免全量 COUNT」机制。**

**⚠️ 两者的关系未证。**
**⇒ 待证：`@CountSql` 的 1 个元素是什么（开关？SQL 片段？）**

**⇒ 这为用户「604 次全量 COUNT」问题提供了第二条线索：**
1. 运行时：`PageInfo#setNeedTotal(false)`
2. 注解级：`@CountSql`

**证据等级：** `STATIC_RULE`

---

## 11. 查询与 Mapper XML

### 11.1 已证

- `AllInOneBaseDao` 41 方法（含 4 档条件）
- `BaseMybatisDao` 16 方法（底层）
- `AllInOneDBDynamicSeeyonKeyMapUtil` 15 方法（SQL 构建）
- `getPageSql(PageInfo, String)` 分页（方言内部决定）
- `selectOneByWrapper(Wrapper)` tk.mybatis Wrapper 支持

### 11.2 未证

| 问题 | 状态 |
|---|---|
| `mybatis.xml.ftl` 生成什么 | `BLOCKED`（需产物） |
| 动态 SQL 生成规则 | `BLOCKED` |
| 关联查询（join）是否支持 | 未见 join 方法 → 可能不支持 |
| 查询结果映射 | 需产物 |

**★ 重要观察：`AllInOneBaseDao` 41 个方法里没有 join / 关联查询方法。**
**⇒ 推论（待证）：平台 DAO 层不做表连接，关联靠多次查询 + 内存拼装。**
**⚠️ 不得断言，需查 `mybatis.xml` 产物。**

---

## 12. 证据清单

| # | 结论 | 等级 | 来源 |
|---|---|---|---|
| 1 | 持久化四层：Service→AppService→DAO→Mapper | `VERIFIED` | 签名 |
| 2 | `AllInOneBaseDao` 41 方法（8 写 / 6 删 / 16 读 / 7 分页 / 2 聚合 / 2 投影） | `VERIFIED` | 签名 |
| 3 | 版本控制 4 个变体（递增/不递增 × 校验/不校验） | `VERIFIED` | 签名 |
| 4 | 条件四档（单/Map/Complex/Dynamic） | `VERIFIED` | 签名 |
| 5 | `SeeyonKeyMap` = `{key, value}`，用 List 允许重复 key | `VERIFIED` | 签名 |
| 6 | `PageInfo#isNeedTotal()` 可关闭 COUNT | `VERIFIED` | 签名 |
| 7 | `PageInfo#isNeedMore()` 轻量模式 | `VERIFIED` | 签名 |
| 8 | `PageData#to(Class)` 类型转换 | `VERIFIED` | 签名 |
| 9 | `BaseMybatisDao` 16 方法（含 `createBatchNoClob`） | `VERIFIED` | 签名 |
| 10 | 逻辑删除走 `SeeyonSqlHelper`（整型 + SQL 片段） | `VERIFIED` | 签名 |
| 11 | 底层框架是 tk.mybatis | `VERIFIED` | `EntityColumn` 参数类型 |
| 12 | **`tenantAdd()` 自动注入租户条件** | `VERIFIED` | 签名 |
| 13 | SQL 构建工具链 15 方法 | `VERIFIED` | 签名 |
| 14 | 主子表 = 实体自引用树 | `VERIFIED` | DTO 结构 |
| 15 | 主子表生成分散在 4 个 Task | `VERIFIED` | 签名 |
| 16 | 单据 8 状态 + 13 特殊字段 | `STATIC` | 配置 |
| 17 | 事务级事件存在 | `STATIC` | 配置 |
| 18 | DAO 层无 join 方法 | `VERIFIED`（方法缺失） | 签名 |
| 19 | 主键生成机制 | **无** | — |
| 20 | 子表外键回填 | **无** | — |

---

## 13. 未解决问题（按严重度）

| # | 问题 | 严重度 | 解决方式 |
|---|---|---|---|
| 1 | 主表 ID 何时生成、什么策略 | **高** | 实测（审批 E） |
| 2 | 子表外键谁回填、何时 | **高** | 实测（审批 E） |
| 3 | 主子表保存顺序 | **高** | 实测（审批 E） |
| 4 | 更新策略（全量 vs 增量） | **高** | 实测（审批 E） |
| 5 | 删除策略（级联 vs 手动） | **高** | 实测（审批 E） |
| 6 | 单据能否绕过 BPM 直接 DAO | **高** | 实测（审批 D/E） |
| 7 | 事务范围 | **高** | 实测 |
| 8 | `deleteById` 是否走逻辑删除 | 中 | 反编译/实测 |
| 9 | 逻辑删除字段名 | 中 | 查实体配置 |
| 10 | `SeeyonKeyMap` 重复 key 语义 | 中 | 反编译 |
| 11 | `needTotal=false` 是否真跳过 COUNT | 中 | 反编译/实测 |
| 12 | `mybatis.xml` 生成内容 | 中 | 需产物 |
| 13 | 关联查询是否支持 | 中 | 需产物 |
| 14 | 版本冲突抛什么异常 | 低 | 反编译 |

---

## 14. 下一轮任务

1. `AbstractAllInOneBaseDao` 55 方法语义梳理（相对接口多出什么）
2. 22 个 Mapper 组成（`dao-and-mybatis.md` 已记录，需核对）
3. 10 种方言清单
4. `Wrapper` 类的实际能力（tk.mybatis）
5. 转专题 4：表达式（静态部分）

---

#### 8.0.2A ★★★ `DtoConvertUtil` 完整签名（从描述符反推，不需要 jar）

**前面说 `DtoConvertUtil` 不在资产中 → 但它的方法签名全部在调用点的描述符里！**

**从 `BaseEntityCurdService` 的 5 处 `resetInsertHandle` 调用点提取描述符：**

```java
// 全部 7 个方法（描述符直接解析，无推断）
DtoConvertUtil.resetInsertHandle(EntityMeta, BaseEntityActionDto, BiConsumer) : BaseEntityActionDto
DtoConvertUtil.forEach(EntityMeta, BaseEntityActionDto, Consumer) : BaseEntityActionDto
DtoConvertUtil.forEach(EntityMeta, List, BiConsumer) : void
DtoConvertUtil.listToMap(EntityMeta, List) : Map
DtoConvertUtil.defaultUpdateListToMap(EntityMeta, List) : Map
DtoConvertUtil.mergeMapData(EntityMeta, Map, Map) : List
DtoConvertUtil.groupByAction(List) : Map
```

**⇒ 这就是 `DtoConvertUtil` 的全部对外方法（至少被 BaseEntityCurdService 用到的全部）。**

**⇒ 每个方法的用途推断（有调用点上下文支撑）：**

| 方法 | 用途 | 证据 |
|---|---|---|
| **`resetInsertHandle(meta, dto, BiConsumer)`** | **新增前处理字段（ID/创建人/时间等）** | `create()` 第一步调用 |
| `forEach(meta, dto, Consumer)` | 对单个 DTO 逐层处理 | `create()` 偏移 17 |
| `forEach(meta, List, BiConsumer)` | 对 DTO 列表逐层处理 | `create()` 偏移 45 |
| `listToMap(meta, List)` | DTO 列表 → Map | 多处 |
| **`defaultUpdateListToMap(meta, List)`** | **更新前把 DTO → Map（用于比对旧值）** | `updateBase` 调用 |
| `mergeMapData(meta, Map, Map)` | 合并新旧 Map | 更新/复制场景 |
| **`groupByAction(List)`** | **按 `ActionType` 分组（INSERT/UPDATE/DELETE/NORMAL）** | 印证差异删除机制 |

**⇒★★ `groupByAction` 的存在**直接印证了 8.0.1M 的结论：**
**⇒ 平台确实按 actionType 对 DTO 分组，再分别处理。**

**⇒★★ `resetInsertHandle` 的签名揭示：**
```java
resetInsertHandle(EntityMeta, BaseEntityActionDto, BiConsumer) : BaseEntityActionDto
```
- 返回 `BaseEntityActionDto`（可能返回同一个对象，也可能返回新对象）
- 第三个参数是 `BiConsumer`（`create()` 里偏移 17 的 lambda）
- **⇒ 说明「字段重置」是可定制的：调用方通过 BiConsumer 介入**

**⚠️ 但 `resetInsertHandle` 内部是否生成雪花 ID 仍然未知 —— 需要 jar。**
**⇒ 不过「它接受 BiConsumer 并能返回处理后的 DTO」这一点已足够确认它是「字段处理入口」。**

#### 8.0.2B ★★ `EntityMetaUtil` 的两个方法

```java
EntityMetaUtil.forEachMeta(EntityMeta, Consumer) : void
EntityMetaUtil.toDtoClassMetaMap(EntityMeta) : Map
```

**⇒ `forEachMeta` 是「遍历实体树所有节点」的通用工具，`deleteData` 用它逐层删除。**
**⇒ `toDtoClassMetaMap` 是「DTO 类型 → EntityMeta」的映射，用于按 DTO 类找元数据。**

#### 8.0.2C ★★★ BLOCKED 已解除：主键生成机制完整还原（源码级）

**`boot-starter-lowcode` jar 已在本机找到并反编译（无需下载）：**

```
D:/repo/CHIT/com/seeyon/udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar
D:/repo/CHIT/com/seeyon/boot-core/5.3.358/boot-core-5.3.358.jar   ← Ids 所在
反编译工具：C:/Users/白明涛/AppData/Local/Temp/cfr.jar（CFR 0.152）
```

**⇒ 状态：从 `BLOCKED` 变为 `VERIFIED_STATIC_SOURCE`（源码级证据，比字节码更强）**

##### ① `resetInsertHandle` 不生成 ID —— 它是递归遍历器

```java
public static <DTO extends BaseEntityActionDto> DTO resetInsertHandle(
        EntityMeta entityMeta, DTO parentDto, BiConsumer<DTO, DTO> biConsumer) {
    if (Objects.isNull(parentDto)) return null;
    if (Objects.nonNull(biConsumer)) {
        biConsumer.accept(parentDto, null);           // ← 对父 DTO 执行回调
    }
    if (CollectionUtils.isNotEmpty(entityMeta.getChildren())) {
        entityMeta.getChildren().stream().forEach(meta -> {
            Object dtoList = ReflectFieldUtil.getFieldValue(parentDto, meta.getDtoListName());
            if (Objects.nonNull(dtoList)) {
                ArrayList dtoColl = Lists.newArrayList();
                if (dtoList instanceof Collection) dtoColl.addAll((Collection) dtoList);
                else dtoColl.add(CastUtils.cast(dtoList));
                dtoColl.stream().forEach(subDto -> {
                    if (Objects.nonNull(biConsumer)) {
                        biConsumer.accept(parentDto, subDto);   // ← 对子 DTO 执行回调
                    }
                    resetInsertHandle(meta, subDto, biConsumer);  // ← 递归
                });
            }
        });
    }
    return parentDto;
}
```

**⇒ `resetInsertHandle` 本身**只管遍历**，真正的字段设置由传入的 `BiConsumer` 完成。**

**⇒ `create()` 传的 BiConsumer 是 `DtoFieldHelper::resetInsert`（见下）。**

##### ② 真正的字段重置：`DtoFieldHelper.resetInsert(parentDto, subDto)`

```java
public static final <D extends BaseEntityActionDto> D resetInsert(D parentDto, D subDto) {
    if (Objects.nonNull(parentDto)) {
        parentDto.setActionType(ActionType.INSERT);                          // ① actionType=INSERT
        if (Objects.isNull(parentDto.getId())
            || Objects.equals(UdcCommonConstant.NULL_ID, parentDto.getId())) {
            parentDto.setId(Ids.gidLong());                                  // ② ★★★ 生成主键
        }
        if (Objects.isNull(parentDto.getDraft()))      parentDto.setDraft(false);
        if (Objects.isNull(parentDto.getCreateTime())) parentDto.setCreateTime(new Date());
        if (Objects.isNull(parentDto.getUpdateTime())) parentDto.setUpdateTime(new Date());
    }
    if (Objects.nonNull(parentDto) && Objects.nonNull(subDto)) {
        subDto.setActionType(ActionType.INSERT);                             // ③ 子表也置 INSERT
        if (Objects.isNull(subDto.getId())
            || Objects.equals(UdcCommonConstant.NULL_ID, subDto.getId())) {
            subDto.setId(Ids.gidLong());                                     // ④ ★★★ 子表也生成主键
        }
        if (parentDto.getDraft()) subDto.setDraft(parentDto.getDraft());
        if (Objects.isNull(subDto.getCreateTime())) subDto.setCreateTime(new Date());
        if (Objects.isNull(subDto.getUpdateTime())) subDto.setUpdateTime(new Date());

        if (subDto instanceof BaseDetailDto) {                               // ⑤ ★★★ 外键回填
            Object parentIdObj = ReflectFieldUtil.getFieldValue(subDto, "parentId");
            if (Objects.isNull(parentIdObj)
                || Objects.equals(UdcCommonConstant.NULL_ID, parentIdObj)) {
                ReflectUtil.setFieldValue(subDto, "parentId", parentDto.getId());   // 首次赋值
            } else if (!Objects.equals(parentDto.getId(), parentIdObj)) {
                subDto.setId(Ids.gidLong());                                 // ⑥ ★ parentId 冲突时换新 ID
                ReflectUtil.setFieldValue(subDto, "parentId", parentDto.getId());
            }
        }
    }
    return subDto;
}
```

##### ③ ★★★ 三个 P0 的最终答案

| 问题 | 答案 | 证据 |
|---|---|---|
| **主表 ID 何时生成？** | **`create()` 第一行 `resetInsertHandle` 内部，在任何 DB 操作之前**，用 `Ids.gidLong()` | `DtoFieldHelper.resetInsert` 源码 |
| **子表外键何时赋值？** | **同一时刻**，主表 ID 生成后立刻 `ReflectUtil.setFieldValue(subDto, "parentId", parentDto.getId())` | 同上 ⑤ |
| **是否预生成（非 DB 自增）？** | **是，纯应用层预生成**。`recursiveCreate` 在 `dao.insert` 之前执行，靠的就是这个预生成 ID | 顺序 + 源码 |

**⇒ 所以「子表先写、主表后写」完全成立：因为 ID 早在内存里就有了，不依赖 DB 自增。**

##### ④ 雪花 ID 完整位布局（`SnowflakeIDGenerator` 源码）

```java
private long startTimeMillis  = 1596816000000L;   // epoch = 2020-08-08 00:00:00 +08:00
public static final long CENTER_ID_BITS = 3L;     //  3 位  centerId (0~7)
public static final long WORKER_ID_BITS = 12L;    // 12 位  workerId (0~4095)
private static final long SEQUENCE_BITS  = 9L;    //  9 位  sequence (0~511)
private static final long CENTER_ID_LEFT_SHIFT = 12L;
private static final long SEQUENCE_LEFT_SHIFT  = 15L;
private static final long TIMESTAMP_LEFT_SHIFT = 24L;

private synchronized long nextId() {
    long timestamp = currentTimeMillis();
    if (timestamp < lastTimestamp) log.error("时光倒流...拒绝生成ID");
    if (lastTimestamp == timestamp) {
        sequence = (sequence + 1) & 0x1FFL;        // 511 溢出
        if (sequence == 0L) timestamp = nextMillis(lastTimestamp);
    } else {
        sequence = 0L;
    }
    lastTimestamp = timestamp;
    return (timestamp - startTimeMillis) << 24
         | sequence << 15
         | centerId << 12
         | workerId;
}
```

**位分配（64 位）：**

| 段 | 位宽 | 位置 | 范围 |
|---|---|---|---|
| 时间戳（相对 epoch） | **40** | bit 24-63 | 34.8 年 → 到约 **2055 年** |
| sequence | **9** | bit 15-23 | 0-511/毫秒 |
| centerId | **3** | bit 12-14 | 0-7（系统属性 `CENTER_ID`） |
| workerId | **12** | bit 0-11 | 0-4095 |

**⇒ 单机 QPS 上限 = 512/毫秒 = 51.2 万/秒（理论），实际受 synchronized 限制。**

##### ⑤ ★★ 重要陷阱：`generateLong()` ≠ 纯雪花

```java
public Long generateLong() {
    if (absolute) {
        return Math.abs(nextId() + ThreadLocalRandom.current().nextLong());
    }
    return nextId() + ThreadLocalRandom.current().nextLong();     // ← ★ 加了随机数！
}
public String generateString() {
    return String.valueOf(nextId());                              // ← 这个是纯雪花
}
```

**⇒ `Ids.gidLong()` 返回的是 `雪花ID + 随机long`，位布局已被打乱！**
**⇒ 只有 `Ids.gidString()` 返回纯雪花 ID，才是「时间可反解」的。**

**⇒ 后果（开发者必须知道）：**

| 方法 | 结果 | 能否反解时间 | 单调递增 |
|---|---|---|---|
| `Ids.gidString()` | 纯雪花 | ✅ | ✅ |
| `Ids.gidLong()` | 雪花 + 随机 | ❌ | ❌ |
| `Ids.uuidLong()` | UUID 高位 | ❌ | ❌ |
| `Ids.uuidAbsLong()` | UUID 正数化 | ❌ | ❌ |

**⇒ 所以 `BaseEntityActionDto.id` 用 `gidLong()` 生成 → 主键是正负都可能、不连续、不可反解时间的。**

**⇒ 这与「分布式 ID 便于分库分表排序」的常见假设相反，必须写成约束。**

##### ⑥ workerId 从 IP 推导（`NetAddressIdWorker`）

```java
String ip = IpUtils.getFirstNoLoopbackIPV4Address();
Long ipLong = Ipv4Util.ipv4ToLong(ip);
this.workerId = ipLong & 0xFFFL;      // 取 IP 低 12 位
```

**⇒ workerId 不是配置的，是**从本机第一个非回环 IPv4 地址低 12 位取**。**

**⇒ 后果：**
- 同一 IP 段的多台机器可能撞 workerId
- **容器化部署（IP 每次变）会导致 workerId 变化**
- 若 IP 变化且时钟回拨，可能生成重复 ID

**⇒ 这是运维约束，不是开发约束，但必须记录。**

##### ⑦ 其他 `DtoFieldHelper` 关键方法（同批反编译得到）

| 方法 | 作用 |
|---|---|
| `throwActionTypeIfAbsent(dto)` | **actionType 为 null 直接抛异常**；UPDATE 时 id 必须非空 |
| `setIdIfAbsent(dto)` | 只在 id 为 null 或 `NULL_ID` 时才生成 |
| **`setParentIdIfAbsent(parentDto, dtoList)`** | 回填 parentId + 设子表 actionType |
| `setActionTypeIfAbsent(dto, type)` | 补默认 actionType |
| `resetChildNormal(dto)` | 子表置 NORMAL |
| `resetId(parentDto, subDto)` | **强制重生成 ID（复制场景）** |
| `set1ToNDtoList(...)` | 按 `RelationType` 处理 One2One / One2Many |
| **`setSubEntityOrderNo(...)`** | 子表 `orderNo` 按 10000 递增自动编号 |
| `diffDataByList / diffDataByMap` | 变更差异计算（供 ChangeEventData 用） |
| **`extractAttrChange(...)`** | 字段级差异，含 `__emptyFields` 清空标记 |

**⇒ `setSubEntityOrderNo` 的顺序号规则：`(i + 1) * 10000`，即 10000, 20000, 30000...**
**⇒ 这解释了子表排序为什么要留间隔（便于中间插入）。**

##### ⑧ `IGNORE_FIELDS` —— 变更比对时被排除的字段（部分）

```java
"createTime", "creator", "creatorInstitution", "creatorDepartment", "creatorPost",
"updater", "updateTime", "secretN", "deductionInfo", "orderNo",
"treePath", "isLeaf", "treeLevel", "treeCaptionPath", "id", "validate",
"maskTypeMap", "positionIndex", "linkSourceIds", "extendMap", "errorInfoList",
"__key", "version", "sort_i_no", "draft"
// 静态块追加：
"sendState", "parentId", "statusType",
"caseSendTime", "caseSender", "caseSenderInstitution", "caseSenderDepartment",
"caseSenderPost", "templateId", "caseId", "caseTitle",
"terminatorId", "terminateTime", "terminateReason", "terminateStatusType",
"cancelTerminatorId", "cancelTerminateTime", "cancelTerminateReason",
"nullifyId", "nullifyTime", "nullifyReason", "nullifyStatusType",
"cancelNullifyId", "cancelNullifyTime", "cancelNullifyReason",
"suspenderId", "suspendTime", "suspendReason", "suspendStatusType",
"cancelSuspenderId", "cancelSuspendTime", "cancelSuspendReason"
```

**⇒ 这批字段名直接暴露了单据的完整状态机字段：**
```
终止：terminateId / terminateTime / terminateReason / terminateStatusType
作废：nullifyId / nullifyTime / nullifyReason / nullifyStatusType
挂起：suspenderId / suspendTime / suspendReason / suspendStatusType
撤销：cancelTerminatorId / cancelNullifyId / cancelSuspenderId ...
```

**⇒ 每个业务动作都有「操作人+时间+原因+状态」四件套。**
**⇒ 这是 UDC 单据状态机的命名规范，可直接用于开发。**

**证据：**
- `udc-starter-lowcode-5.3.517.jar` → `DtoConvertUtil.java` / `DtoFieldHelper.java` / `EntityMetaUtil.java`
- `boot-core-5.3.358.jar` → `Ids.java` / `SnowflakeIDGenerator.java` / `NetAddressIdWorker.java`
**等级：** `VERIFIED_STATIC_SOURCE`（CFR 反编译源码，非字节码推断）
**修正记录：** 2026-11-17 解除原 BLOCKED，推翻「无法确定 ID 生成」的判断

### 8.0.2D 但可以确定的边界（字节码已证）

虽然 `resetInsertHandle` 内部未知，但**调用顺序是确定的**：

```
1. DtoConvertUtil.resetInsertHandle(...)     ← 插入字段处理（含 ID？）
2. recursiveCheck(...)                        ← 递归校验
3. recursiveCreate(...)                       ← 递归写子表
4. middleCreate(...)                          ← 中间层
5. BeanCopier.copy + dao.insert               ← 主表落库
6. entity.getId() → dto.setId(id)             ← 主键回填
```

**⇒ 关键推论（有边界，不外推）：**
**子表在步骤 3 写入，主表在步骤 5 写入，主键回填在步骤 6。**

**⇒ 所以子表写入时，主表还没 insert 完。**
**⇒ 若子表外键是自增主键，逻辑上不可能——必然要么预生成 ID，要么延迟绑定。**

**⇒ 这是从顺序推出的「必然性」，不是「机制」。机制仍需 DtoConvertUtil。**
