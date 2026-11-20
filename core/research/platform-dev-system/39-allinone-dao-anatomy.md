# 39 · ★★★★★ AbstractAllInOneBaseDao 真实解剖（持久化核心）

**证据来源**：`boot-starter-mybatis-5.3.600.jar` 反编译（CFR）
**证据等级：VERIFIED_STATIC_BYTECODE**

---

## 一、★★★★★ 类声明（真实反编译）

```java
@Component
public class AbstractAllInOneBaseDao<T> implements AllInOneBaseDao {

    @Autowired AllInOneBaseMybatisDao allInOneBaseMybatisDao;   ← MyBatis 通道
    @Autowired AllInOneJdbcDao       allInOneJdbcDao;           ← JDBC 直连通道
    @Autowired private MybatisProperties properties;

    LFUCache<Class, Integer> FIELD_COUNT_LFU_CACHE = CacheUtil.newLFUCache(500);

    private Class<T> entityClass;

    public AbstractAllInOneBaseDao() {
        // ★ 从泛型父类参数里取出实体 Class
        Type type = this.getClass().getGenericSuperclass();
        if (type instanceof ParameterizedType) {
            Type[] parameter = ((ParameterizedType) type).getActualTypeArguments();
            if (parameter != null && parameter.length > 0) {
                this.entityClass = (Class) parameter[0];
                Assert.notNull(this.entityClass);
            }
        }
    }
```

### ★★★★★ 三条关键机制

```
1. 泛型 T = 实体类，构造时从 AbstractAllInOneBaseDao<Order> 反射取出
2. 双通道：allInOneJdbcDao（JDBC） / allInOneBaseMybatisDao（MyBatis）
3. FIELD_COUNT_LFU_CACHE(500) —— 缓存实体字段数（用于 SQL 拼装优化）
```

**⇒ 开发者只需写 `interface XxxDao extends AbstractAllInOneBaseDao<Entity>{}`，
泛型一写，实体类型就绑定了，完全不用写方法。**

---

## 二、★★★★★ 双通道选择逻辑（create / selectById 真实代码）

```java
public int create(Object entity) {
    try {
        this.putThreadContext();
        if (this.properties.isAllInOneByJDBC() && SeeyonEntityHelper.contains(this.getT())) {
            return this.allInOneJdbcDao.create(entity, this.getT());      ← JDBC 通道
        }
        return this.allInOneBaseMybatisDao.inOneCreate(entity);           ← MyBatis 通道
    } finally {
        this.removeThreadContext();
    }
}

public T selectById(Long id) {
    try {
        this.putThreadContext();
        if (this.properties.isAllInOneByJDBC() && SeeyonEntityHelper.contains(this.getT())) {
            return (T) this.allInOneJdbcDao.selectById(id, this.getT());  ← JDBC
        }
        return (T) this.allInOneBaseMybatisDao.inOneSelectById(id);       ← MyBatis
    } finally {
        this.removeThreadContext();
    }
}
```

### ★★★★★ 双通道判定条件

```
走 JDBC 需要**同时**满足：
  1. properties.isAllInOneByJDBC() == true      → 全局配置开关
  2. SeeyonEntityHelper.contains(entityClass)   → 该实体已注册为 AllInOne 实体

否则走 MyBatis（inOneCreate / inOneSelectById）
```

### ★★★ ThreadLocal 上下文

```java
private void putThreadContext() {
    Class<T> clazz = this.getT();
    if (Objects.isNull(clazz) && Objects.nonNull(this.entityClass)) {
        ThreadLocalUtil.set("entityClass", this.entityClass);
    }
}
```
**⇒ 用 `ThreadLocalUtil` 传递 entityClass，供底层动态 SQL 生成器读取。**
**⇒ 每个 DAO 方法都是 `putThreadContext()` → 操作 → `removeThreadContext()` 的 try/finally 结构。**

---

## 三、★★★★★ 51 个方法完整清单（按能力分类）

### 3.1 创建（4 个）

```java
int create(Object entity)
int createBatch(List list)
int createBatchNoClob(List list)          ← 不写 CLOB 字段（大文本分离）
int createBatchIgnoreTime(List list)      ← 忽略时间字段（导入场景）
```

### 3.2 更新（8 个）

```java
int update(Object entity)                                   ← 全字段更新
int updateColumns(Object entity, Set columnSet)             ← ★ 只更新指定列
int updateColumnsIgnoreVersion(Object entity, Set columnSet)  ← 指定列 + 忽略版本号
int updateBatch(List list)
int updateBatchIgnoreTime(List list)
int updateBatchIgnoreVersion(List list)
int versionNoUpdateIgnoreVersion(Object entity)             ← 显式控制版本号
int versionNoUpdateBatchIgnoreVersion(List list)
```

**★★★ 乐观锁机制：方法名带 `IgnoreVersion` / `versionNo` → 说明有版本号字段的自动递增控制**

### 3.3 删除（5 个）

```java
int deleteById(Long id)
int deleteByIds(List ids)
int deleteByConditions(Map columnMap)
int deleteByCondition(String column, Object value)
int deleteByWrapper(Wrapper wrapper)
```

### 3.4 查询 - 按 ID（2 个）

```java
T    selectById(Long id)
List selectByIds(List ids)
```

### 3.5 查询 - 单条件（4 个）

```java
T    selectOneByCondition(String column, Object value)
T    selectOneByConditions(Map columnMap)
int  selectCountByCondition(String column, Object value)
int  selectCountByConditions(Map columnMap)
```

### 3.6 查询 - Wrapper（4 个）★ 类似 MyBatis-Plus

```java
Object   selectOneByWrapper(Wrapper wrapper)
int      selectCountByWrapper(Wrapper wrapper)
List     selectListByWrapper(Wrapper wrapper)
PageData selectPageByWrapper(PageInfo pageInfo, Wrapper wrapper)
```

### 3.7 查询 - 列表/分页（8 个）

```java
List     selectListByCondition(String column, Object value, Sort sort)
List     selectListByConditions(Map columnMap, Sort sort)
PageData selectPageByCondition(PageInfo pageInfo, String column, Object value, Sort sort)
PageData selectPageByConditions(PageInfo pageInfo, Map columnMap, Sort sort)

// ★ 字段裁剪（性能优化）
PageData selectPageExcludeByConditions(PageInfo, String[] excludeProperties, Map, Sort)  ← 排除字段
PageData selectPagePropertiesByConditions(PageInfo, String[] selectProperties, Map, Sort) ← 只选字段
List     selectListExcludeByConditions(String[] excludeProperties, Map, Sort)
List     selectListPropertiesByConditions(String[] selectProperties, Map, Sort)
```

**★★★ 四个字段裁剪方法 —— 大表查询时避免 select * 的关键**

### 3.8 复杂条件（5 个）

```java
int      selectCountByComplexConditions(LinkedHashMap columnMap)
List     selectListByComplexConditions(LinkedHashMap columnMap, Sort sort)
PageData selectPageByComplexConditions(PageInfo pageInfo, LinkedHashMap columnMap, Sort sort)
String   selectListFuncByComplexConditions(LinkedHashMap columnMap, Sort sort, String funcName, List params)
int      deleteByComplexConditions(Map columnMap)
```

**★ 用 `LinkedHashMap`（有序）而不是 Map —— 条件顺序影响 SQL 拼装**

### 3.9 动态条件（10 个）★ 最灵活

```java
int      selectCountByDynamicConditions(LinkedHashMap columnMap)
List     selectListByDynamicConditions(LinkedHashMap columnMap, Sort sort)
PageData selectPageByDynamicConditions(PageInfo pageInfo, LinkedHashMap columnMap, Sort sort)
String   selectListFuncByDynamicConditions(LinkedHashMap, Sort, String funcName, List params)
int      deleteByDynamicConditions(Map columnMap)

// 同名的 List 版本（另一种条件表达）
int      selectCountByDynamicConditions(List columnMap)
List     selectListByDynamicConditions(List columnMap, Sort sort)
PageData selectPageByDynamicConditions(PageInfo pageInfo, List columnMap, Sort sort)
String   selectListFuncByDynamicConditions(List columnMap, Sort sort, String funcName, List params)
int      deleteByDynamicConditions(List columnMap)
```

### 3.10 聚合函数（2 个）

```java
selectListFuncByComplexConditions(columnMap, sort, funcName, params)  → String
selectListFuncByDynamicConditions(columnMap, sort, funcName, params)  → String
```

**★ `funcName` = SUM / AVG / MAX / MIN / COUNT**

### 3.11 不支持的方法

```java
private static void notSupportedException() {
    throw BusinessException.message("不支持的方法");
}
```
**⇒ 有部分接口方法故意抛「不支持的方法」—— 说明 `AllInOneBaseDao` 接口里有平台不实现的默认方法。**

---

## 四、★★★★★ 底层实现类（真实存在，已确认）

```
com.seeyon.boot.starter.mybatis.service.AllInOneJdbcDao           ← JDBC 直连通道
com.seeyon.boot.starter.mybatis.inone.dao.AllInOneBaseMybatisDao  ← MyBatis 通道
com.seeyon.boot.starter.mybatis.service.AllInOneDBUtil            ← SQL 拼装工具
com.seeyon.boot.starter.mybatis.service.AllInOneDBDynamicUtil     ← 动态 SQL
com.seeyon.boot.starter.mybatis.service.AllInOneDBComplexUtil     ← 复杂条件 SQL
com.seeyon.boot.starter.mybatis.service.AllInOneDBInterceptor     ← MyBatis 拦截器
com.seeyon.boot.starter.mybatis.service.AllInOneDataParseUtil     ← 数据解析
com.seeyon.boot.starter.mybatis.service.AllInOneDBType            ← 类型映射
com.seeyon.boot.starter.mybatis.service.AllInOneDBDynamicSeeyonKeyMapUtil
com.seeyon.boot.starter.mybatis.service.DataSignRuleService       ← 数据签名规则
com.seeyon.boot.starter.mybatis.service.SecretEnumUpdateService   ← 密文枚举更新
com.seeyon.boot.starter.mybatis.service.DynamicAllInOneDaoService
com.seeyon.boot.starter.mybatis.service.StartersSqlCheckService
com.seeyon.boot.starter.mybatis.service.AllDbService
```

**★★★★★ `AllInOneDBInterceptor` 是关键 —— MyBatis 拦截器在 SQL 执行前注入真正的 SQL。**

---

## 五、★★★★★ 与「空 DAO + 空 XML」的闭环解释

```
生成的 DAO：    interface DemoOrderDao extends AbstractAllInOneBaseDao<Order> {}
                ↓ 空接口，靠泛型绑定实体
生成的 XML：    <mapper namespace="...DemoOrderDao"></mapper>
                ↓ 空，只做 namespace 注册
运行时：        Service 调 demoDao.selectPageByConditions(...)
                ↓ AbstractAllInOneBaseDao 的实现
                ↓ isAllInOneByJDBC() ? AllInOneJdbcDao : AllInOneBaseMybatisDao
                ↓ AllInOneDBUtil 按元数据动态拼 SQL
                ↓ AllInOneDBInterceptor / JDBC PreparedStatement
                ↓ DB
```

**⇒ 这就是平台「零 SQL 生成」的完整机制。**

---

## 六、待验证

| 问题 | 状态 |
|---|---|
| `isAllInOneByJDBC()` 的默认值 | UNVERIFIED |
| `SeeyonEntityHelper.contains()` 的判定依据 | UNVERIFIED（在 tk.mybatis 里） |
| `AllInOneDBUtil` 的 SQL 拼装细节 | 待反编译 |
| `Wrapper` 的结构 | 待反编译 |
| `PageData.to()` 的转换实现 | 待反编译 |