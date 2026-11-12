# standard-product｜Dao 层与 MyBatis 用法（环境无关）

> 本格只讲**包内怎么用**。不涉及任何具体应用/工程/环境。
> 适用：扩展代码要读写库、要写自定义 SQL、要接非 MySQL 数据库时。

分级：`VERIFIED_STATIC_BYTECODE`（javap 逐类，见 §8）。

## 1. Capability

后端三层的**最底层**：Dao 已由平台提供通用 CRUD，正常业务不该手写 SQL。

- `AllInOneBaseDao<T>`（41 方法）：一站式通用 Dao，含条件/复杂条件/动态条件三套查询
- `BaseMybatisDao<T>`（16 方法）：组合式 Dao，由 22 个 Mapper 接口拼装
- 22 个细粒度 Mapper：可单独 mixin 进自己的 Dao
- 10 种数据库方言：MySQL / Oracle / PostgreSQL / SQLServer / 达梦 Dm8 / 人大金仓 KingbaseV8 /
  GBase / 神通 Oscar / 巨杉 SequoiaDB / TDSQL / TiDB

不证：各方法生成的 SQL 具体形态；也不证索引与性能。

## 2. Version

`com.seeyon:boot-starter-mybatis` 5.3.358（138 类 / 44 接口 / 872 方法）

## 3. Input

`boot-starter-mybatis-<ver>.jar`，包前缀 `com/seeyon/boot/starter/mybatis/`。

## 4. Required

实体已按平台注解标注（`@EntityInfo` 等），Dao 由 `MapperScannerRegistrar` 扫描注册。

## 5. Execution

按「一站式 / 组合式 / 单 Mapper / 方言」四组取签名。见 §7。

## 6. Side Effects

读写数据库。

## 7. Known Constraints

### 7.1 ★ 首选 `AllInOneBaseDao<T>`：41 个方法覆盖绝大多数场景

```java
public interface AllInOneBaseDao<T> extends com.seeyon.boot.domain.dao.BaseDao<T> {
    // 写
    int create(T);                      int createBatch(List<T>);
    int update(T);                      int updateBatch(List<T>);
    int updateColumns(T, Set<String>);  int updateColumnsIgnoreVersion(T, Set<String>);
    int versionNoUpdateIgnoreVersion(T);int versionNoUpdateBatchIgnoreVersion(List<T>);
    int deleteById(Long);               int deleteByIds(List<Long>);
    int deleteByCondition(String, Object);          int deleteByConditions(Map<String,Object>);
    int deleteByComplexConditions(Map<String,Object>);
    int deleteByDynamicConditions(LinkedHashMap<String,Object>);
    int deleteByDynamicConditions(List<SeeyonCondition>);
    // 读
    T   selectById(Long);               List<T> selectByIds(List<Long>);
    T   selectOneByCondition(String, Object);       T selectOneByConditions(Map<String,Object>);
    int selectCountByCondition(String, Object);     int selectCountByConditions(Map<String,Object>);
    List<T> selectListByCondition(String, Object, Sort);
    List<T> selectListByConditions(Map<String,Object>, Sort);
    List<T> selectListPropertiesByConditions(String[], Map<String,Object>, Sort);   // 只取指定列
    List<T> selectListExcludeByConditions(String[], Map<String,Object>, Sort);      // 排除指定列
    PageData<T> selectPageByCondition(PageInfo, String, Object, ...);
    PageData<T> selectPageByConditions(PageInfo, Map<String,Object>, Sort);
    PageData<T> selectPagePropertiesByConditions(PageInfo, String[], Map<String,Object>, Sort);
    PageData<T> selectPageExcludeByConditions(PageInfo, String[], Map<String,Object>, Sort);
    // 复杂条件 / 动态条件（复杂条件用 LinkedHashMap 保序；动态条件可用 SeeyonCondition 列表）
    int selectCountByComplexConditions(LinkedHashMap<String,Object>);
    List<T> selectListByComplexConditions(LinkedHashMap<String,Object>, Sort);
    PageData<T> selectPageByComplexConditions(PageInfo, LinkedHashMap<String,Object>, Sort);
    String selectListFuncByComplexConditions(LinkedHashMap, Sort, String, List<String>);  // 聚合函数
    int selectCountByDynamicConditions(List<SeeyonCondition>);
    List<T> selectListByDynamicConditions(List<SeeyonCondition>, Sort);
    PageData<T> selectPageByDynamicConditions(PageInfo, List<SeeyonCondition>, Sort);
}
```

三条要点：

- **Dao 返回的是 `PageData<T>`，不是 transport 的 `PageResponse`**：Dao 是数据层，
  包装成 `PageResponse` 是 AppService 的事。别在 Dao 层套 transport。
- **「三套条件」要分清**：`ByCondition(s)`（简单 map）→ `ByComplexConditions`（`LinkedHashMap`，保序，
  支持 and/or 组合）→ `ByDynamicConditions`（`SeeyonCondition` 列表，最灵活）。
  需求简单就用简单那套，不要一律上动态条件。
- **`selectListFuncBy*` 是聚合**（count/sum 等），返回 `String`；签名里那两个 `String`/`List<String>`
  分别是函数表达式与参数。

### 7.2 `BaseMybatisDao<T>`：由 22 个 Mapper 拼装

`extends` 子句实测（一次列全，这是「我能用哪些方法」的权威答案）：

```
BaseDao<T>, tk.mybatis.mapper.common.Marker,
CreateMapper, CreateBatchMapper, UpdateMapper, UpdateBatchMapper,
UpdateByConditionMapper, UpdateByWrapperMapper, UpdateBatchIgnoreVersionMapper, UpdateIgnoreVersionMapper,
DeleteByIdMapper, DeleteByConditionMapper, DeleteByComplexConditionMapper,
DeleteByDynamicConditionMapper, DeleteByWrapperMapper,
SelectByIdMapper, SelectByConditionMapper, SelectFuncByConditionMapper,
SelectFuncByComplexConditionMapper, SelectFuncByDynamicConditionMapper,
SelectByComplexConditionMapper, SelectByDynamicConditionMapper, SelectByWrapperMapper
```

自己实现 `BaseMybatisDao<T>` 就自动获得上面全部方法；只想用其中几个就**只 mixin 对应 Mapper**
（如 `CreateMapper<T>, SelectByIdMapper<T>`），接口面更小更清楚。

单 Mapper 的实测签名（照抄，别猜）：

```java
CreateMapper<T>          int create(T);  int createIgnoreTime(T);
CreateBatchMapper<T>     int createBatchInternal(List<T>);  int createBatchInternalIgnoreTime(List<T>);
UpdateMapper<T>          int update(T);  int updateIgnoreTime(T);
                         int updateColumns(T, Set<String>);  int updateColumnsIgnoreVersion(T, Set<String>);
UpdateBatchMapper<T>     int updateBatchInternal(List<T>);  int updateBatchInternalIgnoreTime(List<T>);
                         int updateColumnsBatch(List<T>, Set<String>);
DeleteByIdMapper<T>      int deleteById(Long);  int deleteByIdsInternal(List<Long>);
SelectByIdMapper<T>      T selectById(Long);    List<T> selectByIds(List<Long>);
SelectByConditionMapper<T>
                         List<T> selectListByConditions(Map<String,Object>, Sort);
                         PageData<T> selectPageByConditions(PageInfo, Map<String,Object>, Sort);
                         List<T> selectListPropertiesByConditions(String[], Map, Sort);
                         List<T> selectListExcludeByConditions(String[], Map, Sort);
                         PageData<T> selectPagePropertiesByConditions(PageInfo, String[], Map, Sort);
                         PageData<T> selectPageExcludeByConditions(PageInfo, String[], Map, Sort);
                         int selectCountByConditions(Map<String,Object>);
SelectByWrapperMapper<T> List<T> selectListByWrapper(Wrapper);  PageData<T> selectPageByWrapper(PageInfo, Wrapper);
UpdateByWrapperMapper<T> int updateByWrapper(...);  int updateByWrapperSelective(...);
```

⇒ `*Internal` 后缀的方法是**批量真实现**（供 default 方法调用），业务代码一般调 `createBatch`/`deleteByIds`
这类 default 方法，不要直接调 `*Internal`。

### 7.3 多数据库：方言由 `DatabaseDialectManager` 选，不要写 if-else

```java
public interface DatabaseDialect { ... }        // 2 方法
MySQLDatabaseDialect / OracleDatabaseDialect / PostgreSQLDatabaseDialect /
SqlServerDatabaseDialect / Dm8SQLDatabaseDialect / KingbaseV8SQLDatabaseDialect /
GBaseSQLDatabaseDialect / OscarSQLDatabaseDialect / SequoiaDBSQLDatabaseDialect /
TDSQLDatabaseDialect / TidbSQLDatabaseDialect
public class DatabaseDialectManager { ... }     // 2 方法
public class MybatisDatabaseIdProvider { ... }
```

⇒ 10 种方言都已内置。写分页/字符串拼接/日期函数时**用方言能力**，不要判断「当前是不是 MySQL」。
要新增数据库：实现 `DatabaseDialect` 并注册，不改既有代码。

### 7.4 平台已内置的横切能力（不要重写）

```
DataAuditInterceptor(4)         数据审计
DtoDesensitizationInterceptor(6) DTO 脱敏
AggregationInterceptor(9)       聚合查询
QueryInterceptor(25) / UpdateInterceptor(10)
PermissionCheckUtil(11)         权限校验
DataPermissionCheck(1)          数据权限扩展点
SensitiveService(2) / SeeyonSensitive(1)
EntityEncryptionService(3)      实体字段加密
DataSignService(6) / DataSignMybatisService(5)   验签
SafeField(4) / SeeyonKeyMap(8) / SQLWildcardUtil(6)  字段安全与通配符转义
AllInOneDBUtil(22) / ExSqlHelper(10) / SeeyonSqlHelper(7) / SeeyonSqlParserUtils(3)
```

⇒ 审计、脱敏、权限、加密、验签都是拦截器：**加注解/实现 SPI 即可**，不要在业务 SQL 里手写。
`PermissionCheckUtil` 提供数据权限校验；`DataPermissionCheck` 是可实现的扩展点。

### 7.5 确实要写自定义 SQL 时

`MapperConfig` / `MapperScannerRegistrar` / `ClassMapperScanner` 负责扫描注册；
XML 放资源目录下的 mybatis 路径（工程约定，见 skill）。平台组件 `SeeyonCondition` /
`SeeyonKeyMap` / `SQLWildcardUtil` 在写动态条件时可直接用。

## 8. Evidence

```
① 路径  docs/audit/artifacts/extension-surface-20261029/batch2/boot-starter-mybatis.json
        （138 类 / 44 接口 / 872 方法；含全部 22 个 Mapper 接口）
② 复现  uv run --no-project python tools/core/platform/extract_jar_symbols.py \
          --jar "<按 Maven 坐标 com.seeyon:<artifact>:<ver> 解析出的 jar>" \
          --include com/seeyon/boot/starter/mybatis/ \
          --javap <javap 原生路径> --limit 1000 --emit <out.json>
③ 校验  §7.2 的 extends 子句在 classes[].symbols.extends 里逐字可核（22 个 Mapper 全列）；
        §7.1 的 41 个方法在 AllInOneBaseDao 的 methods[] 里逐个可核。
```

## 9. Verified

| 项 | 等级 |
|---|---|
| `AllInOneBaseDao` 41 方法与三套条件查询 | `VERIFIED_STATIC_BYTECODE` |
| `BaseMybatisDao` 的 22 Mapper 组合 | `VERIFIED_STATIC_BYTECODE`（extends 逐字） |
| 单 Mapper 签名（`*Internal` 为批量真实现） | `VERIFIED_STATIC_BYTECODE` |
| 10 种数据库方言类 | `VERIFIED_STATIC_BYTECODE`（类名逐字） |
| 审计/脱敏/权限/加密/验签拦截器族 | `VERIFIED_STATIC_BYTECODE` |
| 生成 SQL 的实际形态与性能 | **UNVERIFIED** |

## 铁律

- 首选 `AllInOneBaseDao<T>`（41 方法）；想缩小接口面就只 mixin 需要的单 Mapper。
- Dao 返回 `PageData<T>`，不要在这一层套 transport 的 `PageResponse`（那是 AppService 的事）。
- 三套条件按需选：简单 `ByCondition(s)` → 保序组合 `ByComplexConditions(LinkedHashMap)` → 最灵活 `ByDynamicConditions(SeeyonCondition)`；不要一律上动态条件。
- `*Internal` 方法是批量真实现，业务调 `createBatch`/`deleteByIds` 这类 default 方法。
- 多数据库走 `DatabaseDialect`（已内置 10 种），不要写「当前是不是 MySQL」的 if-else。
- 审计/脱敏/权限/加密/验签是拦截器 + 注解/SPI，不要在业务 SQL 里手写。
- 自定义 SQL 只在通用 Dao 确实覆盖不了时写，用 `SeeyonCondition`/`SeeyonKeyMap`/`SQLWildcardUtil` 等平台组件。
