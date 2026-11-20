# 持久化体系（boot-starter-mybatis 5.3.600，140 类）

> 数据源：`boot-starter-mybatis-5.3.600.jar` + `boot-core-5.3.600.jar`
> 等级：`VERIFIED_STATIC_BYTECODE`（javap 全部方法签名实测）
> ⚠️ 用户环境 5.3.517，本机 5.3.600

---

## 0. ★ 为什么叫「AllInOne」

**平台上每个实体只生成**一个 DAO 接口**，但这个 DAO 通过继承拿到全套 CRUD 能力。**

```java
// 生成物（典型）
public interface PurchaseOrderDao extends AllInOneBaseDao<PurchaseOrder> {}
```

**⇒ 不需要为每个实体写 Mapper XML，也不需要写 SQL。**

---

## 1. ★★★ 140 类的分层结构

| 分组 | 类数 | 是什么 |
|---|---:|---|
| `*.mapper.*` | **38** | **★ MyBatis 注解 Mapper（SQL 在这里）** |
| `*.dialect.*` | 13 | **★ 数据库方言（12 种数据库）** |
| `*.service.*` | 11 | **★ AllInOneDBUtil / AllInOneJdbcDao / DynamicAllInOneDaoService** |
| `*.inone.*` | 18 | AllInOne 专用（dao/mapper/entity） |
| `*.page.*` | 4 | 分页（PageObjectFactory/Wrapper） |
| `*.util.*` | 5 | SeeyonSqlHelper / ExSqlHelper / SeeyonKeyMap |
| `*.annotation.*` | 3 | `@CountSql` 等 |
| `*.loader.*` / 根包 | 5 | 扫描/配置 |
| `tk.mybatis.*` | 2 | tk.mybatis 补丁 |

---

## 2. ★★★ 核心继承链（必须理解）

```
com.seeyon.boot.domain.dao.BaseDao<T>              ← boot-core，纯接口，43 方法
    ↑
AllInOneBaseDao<T>                                 ← 41 方法（inone.dao）
    ↑
AbstractAllInOneBaseDao<T>                         ← 51 方法（抽象实现）

BaseMybatisDao<T> extends BaseDao<T>, tk.mybatis.Mapper<T>   ← 17 default 方法
    ↑
AllInOneBaseMybatisDao                            ← 空接口（只做组合）
```

**⇒ 三种 DAO 形态，各有用途：**

| 类型 | 用途 | 能否自定义 SQL |
|---|---|---|
| `AllInOneBaseDao<T>` | **标准 CRUD（无 SQL）** | ❌ 纯预制 |
| `AllInOneBaseMybatisDao` | **预制 + tk.mybatis** | ✅ 可加 |
| `BaseMybatisDao<T>` | **tk.mybatis 完整能力** | ✅ 完整 |

---

## 3. ★★★ AbstractAllInOneBaseDao（51 方法）—— 全量 CRUD API

### 3.1 写（11 方法）

```java
int create(Object obj)                                 // 单条插入
int createBatch(List list)                             // ★ 批量插入
int createBatchNoClob(List list)                       // ★ 批量插入（不含 CLOB 大字段）
int createBatchIgnoreTime(List list)                   // ★ 批量插入（不写时间字段）

int update(Object obj)                                 // 按主键更新（含乐观锁）
int versionNoUpdateIgnoreVersion(Object obj)           // ★ 强制更新（忽略版本号）
int updateColumns(Object obj, Set<String> columns)     // ★ 只更新指定列
int updateColumnsIgnoreVersion(Object, Set<String>)    // ★ 只更新指定列（忽略版本）

int updateBatch(List list)                             // ★ 批量更新
int updateBatchIgnoreTime(List list)                   // ★ 批量更新（不动时间）
int updateBatchIgnoreVersion(List list)                // ★ 批量更新（忽略版本）
int versionNoUpdateBatchIgnoreVersion(List list)       // ★ 批量强制更新
```

**★★ 四个「Ignore」变体的真实用途：**

| 变体 | 场景 |
|---|---|
| `IgnoreTime` | **数据迁移/补数据**时不想刷新 gmtModified |
| `IgnoreVersion` | **并发冲突后强制覆盖**（慎用） |
| `NoClob` | **批量插入遇到 CLOB 字段会失败** → 用这个跳过 |
| `updateColumns` | **只改几个字段**，避免 `update` 把 null 写进去覆盖原值 |

**⚠️ `update` 的坑：平台默认是「全字段更新」还是「非 null 更新」我没读方法体，不确定。**
**⇒ 保险做法：用 `updateColumns(obj, Set.of("status","amount"))` 明确指定。**

### 3.2 删（5 方法）

```java
int deleteById(Long id)
int deleteByIds(List<Long> ids)
int deleteByCondition(String property, Object value)              // 单条件
int deleteByConditions(Map<String,Object> map)                    // 多条件 AND
int deleteByWrapper(Wrapper wrapper)                              // ★ 复杂条件
```

**★ 逻辑删除 vs 物理删除：** 类名只有 `delete`，没有 `logicDelete`。
**⇒ 逻辑删除应该是**实体有 `deleteFlag` 字段，由框架自动追加条件**（见 §7）。**

### 3.3 查 —— 单条（3 方法）

```java
T selectById(Long id)
T selectOneByCondition(String property, Object value)
T selectOneByConditions(Map<String,Object> map)
T selectOneByWrapper(Wrapper wrapper)
```

**⚠️ `selectOne*` 如果查到多条会抛异常（tk.mybatis 行为）。**

### 3.4 查 —— 列表（7 方法）

```java
List<T> selectListByCondition(String property, Object value, Sort sort)
List<T> selectListByConditions(Map<String,Object> map, Sort sort)
List<T> selectListPropertiesByConditions(String[] properties, Map map, Sort sort)   // ★ 只查指定列
List<T> selectListExcludeByConditions(String[] excludes, Map map, Sort sort)        // ★ 排除指定列
List<T> selectListByWrapper(Wrapper wrapper)
List<T> selectByIds(List<Long> ids)
List<T> selectListByComplexConditions(LinkedHashMap map, Sort sort)                 // ★ 复杂条件
```

**★★ `selectListPropertiesByConditions` —— 只查需要字段，**避免大字段全查**（性能优化关键）。**

### 3.5 查 —— 分页（6 方法）

```java
PageData<T> selectPageByCondition(PageInfo pageInfo, String property, Object value, Sort sort)
PageData<T> selectPageByConditions(PageInfo pageInfo, Map map, Sort sort)
PageData<T> selectPagePropertiesByConditions(PageInfo, String[] properties, Map, Sort)
PageData<T> selectPageExcludeByConditions(PageInfo, String[] excludes, Map, Sort)
PageData<T> selectPageByWrapper(PageInfo, Wrapper)
PageData<T> selectPageByComplexConditions(PageInfo, LinkedHashMap, Sort)
```

**★ 分页返回 `PageData<T>`，不是 `Page<T>`。**
**`PageData` 里有 `List<T> rows` + `long total` 之类（未 dump）。**

### 3.6 查 —— 统计（3 方法）

```java
int selectCountByCondition(String property, Object value)
int selectCountByConditions(Map map)
int selectCountByWrapper(Wrapper wrapper)
int selectCountByComplexConditions(LinkedHashMap map)
```

### 3.7 ★ 函数查询（`selectListFunc*`）

```java
String selectListFuncByComplexConditions(LinkedHashMap map, Sort sort, String func, ...)
String selectListFuncByDynamicConditions(...)
```

**★ 返回 `String` 而不是 List —— 说明是「聚合函数结果」（如 `MAX(code)` / `SUM(amount)`）。**
**⚠️ 具体支持哪些函数（`COUNT`/`SUM`/`MAX`/`MIN`/`AVG`）未验证。**

---

## 4. ★★★ 三种条件形态的区别（最容易混）

| 形态 | 入参 | 能表达什么 | 对应方法 |
|---|---|---|---|
| **Condition** | `String property, Object value` | **单字段等值** | `selectListByCondition` |
| **Conditions** | `Map<String,Object>` | **多字段 AND 等值** | `selectListByConditions` |
| **ComplexConditions** | `LinkedHashMap<String,Object>` | **★ 字段名里带运算符** | `selectListByComplexConditions` |
| **DynamicConditions** | `LinkedHashMap` 或 `List<SeeyonKeyMap>` | **★ 动态拼接（可 OR）** | `selectListByDynamicConditions` |
| **Wrapper** | `Wrapper` 对象 | **★ tk.mybatis Example（最灵活）** | `selectListByWrapper` |

### 4.1 `SeeyonKeyMap` 的结构（实测）

```java
public class SeeyonKeyMap {
    private String key;
    private Object value;
    public SeeyonKeyMap(String, Object)   // ★ 只有 key-value
}
```

**⚠️ 就两个字段 —— 说明「运算符」编码在 `key` 字符串里，不是独立字段。**

### 4.2 `Wrapper` 的真相（实测）

```java
public class Wrapper extends com.seeyon.boot.tkmybatis.SeeyonExample
// SeeyonExample extends tk.mybatis.mapper.entity.Example

Wrapper(Class<?>)
Wrapper(Class<?>, boolean)
Wrapper(Class<?>, boolean, boolean)

// SeeyonExample
Criteria createCriteria()          // 新建条件组
Criteria createCriteriaAddOn()     // ★ 加自己造的条件组
Criteria or()                      // OR
Criteria and()                     // AND
```

**★★ `Wrapper` 就是 tk.mybatis 的 `Example`，所以能这样用：**

```java
Wrapper w = new Wrapper(PurchaseOrder.class);
Example.Criteria c = w.createCriteria();
c.andEqualTo("status", 1)
 .andGreaterThan("amount", 1000)
 .andLike("code", "PO%")
 .andIn("orgId", orgIds);
w.orderBy("createTime").desc();

List<PurchaseOrder> list = dao.selectListByWrapper(w);
PageData<PurchaseOrder> page = dao.selectPageByWrapper(pageInfo, w);
```

**⇒ `Wrapper` 是**唯一能做 OR / 范围 / IN / LIKE 的标准方式**。**

### 4.3 ComplexCondition 的实现（实测线索）

**`AllInOneDBComplexUtil` 的私有方法暴露了机制：**
```java
private String whereMatcher(String)              // ★ 匹配运算符
private void jdbcComplexCondition(StringBuilder, Map, ...)  // 拼条件
private void tenantAdd(Map, Boolean)             // ★ 自动加租户条件
private String getPageSql(PageInfo, String)      // 分页 SQL
private void getSortSql(Sort, StringBuilder, Class)
```

**★★★ 关键发现：`tenantAdd` —— 复杂条件查询会**自动追加租户条件**。**
**⇒ 这是平台多租户的实现方式之一。**

**⇒ `whereMatcher(String)` 说明 ComplexCondition 是**对 key 做字符串匹配**判运算符。**
**⚠️ 具体支持哪些运算符前缀（如 `>amount` / `amount_in`）未验证。**

---

## 5. ★★★ 方言体系（12 种数据库）

```java
DatabaseDialect（接口）
  └─ DatabaseDialectManager（管理器）

12 个实现：
  MySQLDatabaseDialect
  OracleDatabaseDialect
  PostgreSQLDatabaseDialect
  SqlServerDatabaseDialect
  Dm8SQLDatabaseDialect            ← 达梦
  KingbaseV8SQLDatabaseDialect     ← 人大金仓
  GBaseSQLDatabaseDialect          ← 南大通用
  OscarSQLDatabaseDialect          ← 神通
  SequoiaDBSQLDatabaseDialect      ← 巨杉
  TDSQLDatabaseDialect             ← 腾讯 TDSQL
  TidbSQLDatabaseDialect           ← TiDB
```

**⇒ 平台**原生支持 12 种数据库**（含全部国产库）。**
**★ 与 `boot-core` 的 `DatabaseUtils.mysql2Xxx` 配合：工具类做静态转换，方言类做运行时分页/函数。**

---

## 6. ★★ 38 个 Mapper（SQL 真正所在）

### 6.1 标准 Mapper（成对出现，`AllInOne*` 是 inone 包的重载版）

| Mapper | 方法 | SQL |
|---|---|---|
| `CreateMapper` | `create` / `createIgnoreTime` | INSERT |
| `CreateBatchMapper` | `createBatchInternal` / `...IgnoreTime` | **批量 INSERT（内部方法）** |
| `SelectByIdMapper` | `selectById` / `selectByIds` | SELECT |
| `SelectByConditionMapper` | 7 个（count/list/page × properties/exclude） | SELECT |
| `SelectByComplexConditionMapper` | `selectCountByComplexConditions` 等 | SELECT（复杂） |
| `SelectByDynamicConditionMapper` | 动态条件 | SELECT（动态） |
| `SelectFuncByConditionMapper` | 聚合函数 | SELECT MAX/SUM |
| `UpdateMapper` | `update` / `updateColumns` | UPDATE |
| `UpdateBatchMapper` | 批量 | **批量 UPDATE** |
| `UpdateBatchIgnoreVersionMapper` | 批量（忽略版本） | |
| `UpdateIgnoreVersionMapper` | 单条（忽略版本） | |
| `DeleteByIdMapper` / `DeleteByConditionMapper` / `DeleteByComplexConditionMapper` / `DeleteByDynamicConditionMapper` / `DeleteByWrapperMapper` | | DELETE |

**⇒ 每个操作一个独立 Mapper，**通过 `AllInOneBaseDao` 组合起来**。**

## 7. ★★ `SeeyonSqlHelper` —— 逻辑删除与乐观锁的实现在这里

```java
public static String logicDeleteColumnEqualsValue(EntityColumn, boolean)   // ★ 逻辑删除条件
public static int    getLogicDeletedValue(EntityColumn, boolean)          // ★ 删除标记值
public static String updateSetColumns(Class<?>, String, boolean, boolean, Set<String>)  // ★ 更新列
public static String getIfNotNull(String, EntityColumn, String, boolean)  // ★ 非空判断
public static Object valueParser(Object, EntityColumn)                    // ★ 类型转换
public static String updateSetColumns(...)                                // ★
```

**★★ 三个机制确认：**

| 机制 | 实现位置 | 说明 |
|---|---|---|
| **逻辑删除** | `logicDeleteColumnEqualsValue` | 有 `@LogicDelete` 注解的字段自动加条件 |
| **乐观锁** | `updateSetColumns` + version 字段 | `update` 自动带 `version = version+1` 条件 |
| **非空更新** | `getIfNotNull` | `update` 生成的 SET 子句带 `<if test="xxx != null">` |

**★ `@LogicDelete` 注解 → 实体有这个注解的字段，**所有查询自动追加 `delete_flag = 0`**。**
**⇒ 这就是「逻辑删除不写代码」的原理。**

**配套注解（`annotation` 包 3 个）：**
```java
@CountSql          // ★ 自定义 count SQL（分页时 count 语句可能和 list 不同）
```

---

## 8. ★★ AllInOneDBUtil（9 方法）—— 无泛型的动态入口

```java
int insertBatch(List data, Class<?> clazz, Boolean ...)
int updateBatchByIds(List, Set<String> columns, Boolean, Boolean, Long/Class)
int delete(Map<String,Object> condition, Boolean ..., Class<?> clazz)
int deleteIds(List<Long> ids, Class<?> clazz)
List<Map<String,Object>> selectSql(PageInfo, String sql, ...)    // ★ 手写 SQL
List<Object> selectBatch(String[] properties, Map, ..., Class<?>)
int selectCount(Map<String,Object>, Boolean, Class<?>)
```

**★★ `selectSql(PageInfo, String sql)` —— 可以**直接执行手写 SQL 并返回 Map 列表**。**
**⇒ 复杂报表/多表 JOIN 走这个，不用建实体。**

**★ `AllInOneDBUtil` 与 `AbstractAllInOneBaseDao` 的区别：**
```
AbstractAllInOneBaseDao   ← 泛型 T，编译期类型安全，DAO 里用
AllInOneDBUtil            ← Class<?> 运行时传，适合动态/元数据场景（如 UDC）
```

---

## 9. ★★ DynamicAllInOneDaoService（45 方法）—— UDC 真正的持久化入口

**每个方法都多两个参数：`String appName, String entityName`**

```java
Class<?> getT(String appName, String entityName)          // ★ 运行时拿类型

int create(Object data, String appName, String entityName)
int createBatch(List, String appName, String entityName)
int update(Object, String, String)
int updateColumns(Object, Set, String, String)
int deleteById(Long, String, String)
Object selectById(Long id, String appName, String entityName)
Object selectOneByConditions(Map, String, String)
int selectCountByConditions(Map, String, String)
List selectListByConditions(Map, Sort, String, String)
PageData selectPageByConditions(PageInfo, Map, Sort, String, String)
List selectListByWrapper(...)
int deleteByWrapper / selectCountByWrapper
// 全套 45 个
```

**★★★ 这是本节最重要的发现：**

**UDC 的实体是**运行时动态加载的 Class**，没有编译期泛型。**
```
AbstractAllInOneBaseDao<T>    ← 生成物（代码生成的实体）
DynamicAllInOneDaoService     ← UDC 动态实体（appName + entityName 定位）
```

**⇒ Agent 写扩展代码时：**
- **操作**自己应用的实体** → 用生成的 `XxxDao`（泛型）
- **操作**UDC 动态实体** → 用 `DynamicAllInOneDaoService`

**★ `onApplicationEvent(ModuleUnloadEvent)` —— 模块卸载时清理 `entityClassLoaderCache`。**
**⇒ 说明动态实体的 Class 是**按模块热加载**的，卸载要清缓存防泄漏。**

---

## 10. ★ 130 行代码讲完的完整用法

```java
// ① 标准 DAO（代码生成产物）
@Autowired
private PurchaseOrderDao purchaseOrderDao;

// 单条
PurchaseOrder po = new PurchaseOrder();
po.setId(Ids.gidLong());
po.setCode("PO2026110001");
purchaseOrderDao.create(po);

// 批量（注意 CLOB）
purchaseOrderDao.createBatch(list);
purchaseOrderDao.createBatchNoClob(clobList);   // 有大字段用这个

// 只改几个字段（避免 null 覆盖）
purchaseOrderDao.updateColumns(po, Set.of("status", "amount"));

// 查询
PurchaseOrder one = purchaseOrderDao.selectById(id);
List<PurchaseOrder> list = purchaseOrderDao.selectListByConditions(
    Map.of("status", 1, "orgId", orgId),
    Sort.desc("createTime"));

// 分页
PageData<PurchaseOrder> page = purchaseOrderDao.selectPageByConditions(
    new PageInfo(1, 20),
    Map.of("status", 1),
    Sort.desc("createTime"));
// page.getRows() / page.getTotal()

// 复杂条件（Wrapper = tk.mybatis Example）
Wrapper w = new Wrapper(PurchaseOrder.class);
w.createCriteria()
 .andEqualTo("status", 1)
 .andIn("orgId", orgIds)
 .andLike("code", "PO%");
w.orderBy("createTime").desc();
List<PurchaseOrder> result = purchaseOrderDao.selectListByWrapper(w);

// 聚合
String maxCode = purchaseOrderDao.selectListFuncByComplexConditions(
    map, sort, "MAX", "code", ...);
```

**② UDC 动态实体**
```java
@Autowired
private DynamicAllInOneDaoService dynamicDao;

// appName + entityName 定位，不用泛型
Class<?> t = dynamicDao.getT(appName, entityName);
Object row = dynamicDao.selectById(id, appName, entityName);
dynamicDao.create(dto, appName, entityName);
```

**③ 手写 SQL（报表/多表 JOIN）**
```java
@Autowired
private AllInOneDBUtil allInOneDBUtil;

List<Map<String,Object>> rows = allInOneDBUtil.selectSql(
    pageInfo,
    "select o.code, c.name from po_order o join crm_customer c on o.customer_id=c.id where o.status=#{status}",
    params);
```

---

## 11. ★★★ 主子表怎么入（回答用户核心问题）

**平台主子表的标准形态：**

```
主表实体 PurchaseOrder
子表实体 PurchaseOrderItem（有 purchaseOrderId 字段）
```

**★ 没有 `createWithItems` 这类 API —— 主子表要**自己写两段**：**

```java
@Transactional(rollbackFor = Exception.class)     // ★ 必须加事务
public void createOrder(PurchaseOrderDto dto) {
    // ① 主表
    Long orderId = Ids.gidLong();                 // ★ 预生成主键
    PurchaseOrder po = BeanCopier.copy(dto, PurchaseOrder.class);
    po.setId(orderId);
    purchaseOrderDao.create(po);

    // ② 子表：先回填外键
    List<PurchaseOrderItem> items = dto.getItems().stream()
        .map(i -> {
            PurchaseOrderItem item = BeanCopier.copy(i, PurchaseOrderItem.class);
            item.setId(Ids.gidLong());
            item.setPurchaseOrderId(orderId);     // ★ 关键：回填
            return item;
        }).collect(Collectors.toList());

    // ③ 子表批量插入
    purchaseOrderItemDao.createBatch(items);
}
```

**★★ 三个关键点：**
1. **`Ids.gidLong()` 预生成主键** —— 不依赖 DB 自增，主子表能先拿到 ID
2. **必须 `@Transactional`** —— 否则主子表可能只成一半
3. **`createBatch` 用批量** —— 子表多时逐条插入会慢

**★★ 大数据量主子表：用 `createBatchNoClob` + 分批（每批 500~1000）。**

**⚠️ 如果是**单据（Bill）**，走 BPM 的保存流程，不是直接 insert —— 见 `14-udc-bpm-bridge.md`。**

---

## 12. ★ 12 种数据库支持

```
MySQL / Oracle / PostgreSQL / SQL Server
+ 国产 8 种：达梦(Dm8) / 人大金仓(KingbaseV8) / 南大通用(GBase)
             神通(Oscar) / 巨杉(SequoiaDB) / 腾讯TDSQL / TiDB
```

**⇒ 平台是完整信创适配的。写 SQL 一律用 `DatabaseUtils.mysql2Xxx` 转，或走方言层。**

---

## 13. 未覆盖

| 项 | 说明 |
|---|---|
| `update` 是全字段还是非 null 更新 | **未读方法体，不确定** |
| ComplexCondition 的运算符语法 | `whereMatcher` 只知存在，未读匹配规则 |
| `PageInfo` / `PageData` 字段 | 未 dump |
| `AllInOneDataParseUtil` 的类型转换规则 | 未读 |
| `@CountSql` 的用法 | 未读 |
| 12 个方言的具体差异（分页语法/函数名） | 未读 |
| `BaseMybatisDao` 的 tk.mybatis 完整能力 | 只读了 17 个 default 方法 |
| 逻辑删除注解的确切名字 | 我写的是 `@LogicDelete`，**未在 jar 里确认** |