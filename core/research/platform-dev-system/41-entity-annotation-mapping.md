# 41 · ★★★★★ 实体注解映射 + Wrapper API + INSERT 拼装（P0 三连）

**证据来源**：`SeeyonEntityHelper` / `SeeyonExample` / `SeeyonCriteria` / `AllInOneDBUtil.insertBatch` 反编译
**证据等级**：VERIFIED_STATIC_BYTECODE

---

## 一、★★★★★ 实体注解 → 列名映射（`SeeyonEntityHelper` 真实代码）

### 1.1 `initEntity` —— 强制的 `@Table` 契约

```java
public static void initEntity(Class<?> entityClass) {
    SeeyonEntityColumns cols = new SeeyonEntityColumns();
    if (entityClass.isAnnotationPresent(Table.class)) {
        Table table = entityClass.getAnnotation(Table.class);
        Assert.notEmpty(table.name(), "实体Table注解必须指明表名");
        cols.setTableName(table.name());
        _getFields(entityClass, cols);
    } else {
        Assert.notEmpty("", "实体必须包含Table注解");
    }
    seeyonEntityColumnsMap.put(entityClass, cols);
}
```

### ★★★★ 硬约束：**实体类必须有 `@Table(name="真实表名")`，否则直接断言失败。**

### 1.2 `_getFields` —— 逐字段解析

```java
private static void _getFields(Class<?> entityClass, SeeyonEntityColumns cols) {
    Map<String,String>  columns      = cols.getColumns();      // 属性名 → 列名
    Map<String,Class>   javaTypes    = cols.getJavaTypes();    // 属性名 → Java 类型
    Map<String,JdbcType> jdbcTypes   = cols.getJdbcTypes();    // 属性名 → JDBC 类型
    Map<String,Field>   columnFields = cols.getColumnFields(); // 属性名 → Field
    Map<String,Messageable[]> enumList = cols.getEnumList();   // 属性名 → 枚举常量数组

    Class<?> source = entityClass;
    // ★ 沿继承链向上遍历（父类字段也会被收集！）
    while (entityClass != null && !entityClass.equals(Object.class)
           && (entityClass.isAnnotationPresent(Entity.class)
               || !Map.class.isAssignableFrom(entityClass)
                  && !Collection.class.isAssignableFrom(entityClass))) {
        for (Field field : entityClass.getDeclaredFields()) {
            String name = field.getName();
            Class<?> javaType = field.getType();

            if (field.isAnnotationPresent(Column.class)) {
                Column column = field.getAnnotation(Column.class);
                String columnName = column.name();
                if (StringUtil.isEmpty(columnName)) continue;
                columns.put(name, columnName);      // ★ 用 Column.name()，不是字段名
                javaTypes.put(name, javaType);
                if (!columnFields.containsKey(name)) columnFields.put(name, field);
            }
            if (field.isAnnotationPresent(ColumnType.class)) {
                jdbcTypes.put(name, field.getAnnotation(ColumnType.class).jdbcType());
            }
            // ★ List<XxxEnum> 泛型参数是 Messageable 子类 → 收集枚举常量
            if (List.class.isAssignableFrom(javaType)) {
                Type gt = field.getGenericType();
                if (gt instanceof ParameterizedType) {
                    Class actual = (Class)((ParameterizedType) gt).getActualTypeArguments()[0];
                    if (Messageable.class.isAssignableFrom(actual)) {
                        enumList.put(name, (Messageable[]) actual.getEnumConstants());
                    }
                }
            }
        }
        entityClass = entityClass.getSuperclass();   // ★ 逐级向上
    }
}
```

### ★★★★★ 五条关键规则

| # | 规则 | 证据 |
|---|---|---|
| 1 | 表名来自 **`@Table.name()`**，空则断言失败 | `Assert.notEmpty(table.name(), "实体Table注解必须指明表名")` |
| 2 | 列名来自 **`@Column.name()`**，**不是字段名** | `columns.put(name, column.name())` |
| 3 | `@Column.name()` 为空 → **该字段被跳过**，不进 SQL | `if (StringUtil.isEmpty(columnName)) continue;` |
| 4 | **沿继承链向上遍历**，父类字段也收集 | `entityClass = entityClass.getSuperclass()` |
| 5 | `List<Messageable枚举>` → 自动收集枚举常量 | `enumList.put(name, actual.getEnumConstants())` |

**★ 第 3 条最危险：字段上有 `@Column` 但 `name=""` → 静默跳过。**
**⇒ 该字段既不 select 也不 insert，排查「字段不落库」时先查这个。**

### 1.3 `contains` —— 双通道判定依据

```java
public static boolean contains(Class<?> entityClass) {
    return seeyonEntityColumnsMap.containsKey(entityClass);
}
```
**⇒ `contains()` 返回 true 的条件：`initEntity` 被调用过（即 `@Table` 解析成功）。**
**⇒ 所以「走 JDBC 通道」的实际含义是：「该实体被 SeeyonEntityHelper 成功初始化过」。**

### 1.4 `SeeyonEntityColumns` 的五个 Map

```java
Map<String,String>     columns;      // 属性名 → 列名
Map<String,Class<?>>   javaTypes;    // 属性名 → Java 类型
Map<String,JdbcType>   jdbcTypes;    // 属性名 → JDBC 类型（@ColumnType）
Map<String,Field>      columnFields; // 属性名 → 反射 Field
Map<String,Messageable[]> enumList;  // 属性名 → 枚举常量数组
String                 tableName;    // @Table.name()
```

---

## 二、★★★★ 实体类真实结构（3.0 模板 LIVE 渲染产物）

**★★★★★ 重大发现：实体类由 `3.0` 版模板生成，其余类由 `2.9`。**

```
2.9: 141 个模板，**没有 entity/entity.java.ftl**
3.0: 只有 2 个模板 —— entity.java.ftl (13,272 B) + baseservice.java.ftl (74,308 B)
2.7: 125 个，有 entity.java.ftl
2.8: 138 个，有 entity.java.ftl
```
**⇒ 2.9 把实体类和 BaseService 单独升级到 3.0，其余留在 2.9。这是**分层版本策略**。**

### 2.1 真实渲染的 Entity（关键结构）

```java
@Entity(name="demoOrder")
@Table(name = "")                       ← 空（我的模型没传表名）
@Alias("demoOrder")
@EntityInfo(value = "订单", description = "", sort = ,
    isPublic = true,
    customs = {
      @Custom(properties = @CustomAttribute(name = "stereotype", value = "")),
      @Custom(properties = @CustomAttribute(name = "features", value = "")),
      @Custom(properties = @CustomAttribute(name = "id", value = "0")),
      @Custom(properties = @CustomAttribute(name = "guid", value = "")),
      @Custom(properties = @CustomAttribute(name = "name", value = "order")),
      @Custom(properties = @CustomAttribute(name = "entityCategory", value = "NORMAL"))
    })
public class Order extends  {           ← 空（父类变量缺失）

    private static final long serialVersionUID = L;

    @Column(name = "id", columnDefinition = "")
    @EntityAttribute(value = "主键", description = "", sort = ,
        dataType = DataType. ,
        safety = @Safety(auditLog = false, openApiEncrypt = ),
        customs = {@Custom(properties = {
            @CustomAttribute(name = "id", value = "4355"),
            @CustomAttribute(name = "guid", value = "109108"),
            @CustomAttribute(name = "useSnapshot", value = "false"),
            @CustomAttribute(name = "name", value = "id"),
            @CustomAttribute(name = "notNull", value = "true")})})
    @Id
    private LONG id;

    @Override @JsonProperty("id")
    public LONG getId(){ return this.id; }
    @Override @JsonProperty("id")
    public void setId(LONG value){ this.id = value; }
    ...
}
```

### ★★★★★ 实体类的注解栈（顺序固定）

```
类级：@Entity(name) → @Table(name) → @Alias(name) → @EntityInfo(...)
字段级：@Column(name, columnDefinition) → @EntityAttribute(...) → [@Id | @ColumnType]
        → private {JavaType} {name};
        → @JsonProperty("name") getter/setter（主键多一个 @Override）
```

### ★★★ 三个必填的 CustomAttribute

```
@EntityInfo.customs:  stereotype / features / id / guid / name / entityCategory
@Column 字段 customs:  id / guid / useSnapshot / name  (+ notNull / decimalDigits 按需)
```

**⇒ 平台元数据的「设计态 ID」全部嵌在注解的 `@CustomAttribute` 里。**

### 2.2 类型名问题

产物里是 `LONG` / `STRING` / `DECIMAL` / `DATETIME`，不是 `Long` / `String`。
**⇒ 我的简化模型少了 `javaType` 映射（真实走 `EntityCodeUtils.getJavaType`）。UNVERIFIED，不是平台 bug。**

---

## 三、★★★★★ `Wrapper` API（另一套条件表达）

### 3.1 三层继承（实证）

```
com.seeyon.boot.domain.dao.Wrapper          ← 4 个构造函数，无自带方法
  extends com.seeyon.boot.tkmybatis.SeeyonExample
    extends tk.mybatis.mapper.entity.Example   ← tk.mybatis 原生
```

```java
public class Wrapper extends SeeyonExample {
    public Wrapper(Class<?> entityClass) { super(entityClass); }
    public Wrapper(Class<?> entityClass, boolean exists) { super(entityClass, exists); }
    public Wrapper(Class<?> entityClass, boolean exists, boolean notNull) { super(entityClass, exists, notNull); }
}
```

### 3.2 `SeeyonExample` 的 7 个方法

```java
public SeeyonExample(Class<?> entityClass)
public SeeyonExample(Class<?> entityClass, boolean exists)
public SeeyonExample(Class<?> entityClass, boolean exists, boolean notNull)
public SeeyonCriteria createCriteriaAddOn()     ← ★ 返回 SeeyonCriteria
public Example.Criteria or()                    ← ★ 显式 or 连接
public Example.Criteria and()                   ← ★ 显式 and 连接
public Example.Criteria createCriteria()
```

**★★★ `or()` / `and()` 是平台加的（tk.mybatis 原生只有 `or()`）**
**⇒ 可以做 `criteriaA.and()` / `criteriaB.or()` 的显式连接。**

### 3.3 `SeeyonCriteria` 只有 4 个额外方法

```java
public Example.Criteria andEqualTo(String property, Object value)
public Example.Criteria andNotEqualTo(String property, Object value)
public Example.Criteria orEqualTo(String property, Object value)
public Example.Criteria orNotEqualTo(String property, Object value)
```

**⇒ 其余全部方法来自 `Example.Criteria`（tk.mybatis 原生）：**
```
andIsNull / andIsNotNull / andEqualTo / andNotEqualTo / andGreaterThan /
andGreaterThanOrEqualTo / andLessThan / andLessThanOrEqualTo / andIn / andNotIn /
andLike / andNotLike / andBetween / andNotBetween / andCondition ...
```

### 3.4 Wrapper 用法（构造顺序）

```java
Wrapper w = new Wrapper(Order.class);
Example.Criteria c = w.createCriteria();          // 或 createCriteriaAddOn()
c.andEqualTo("status", 1);
c.andLike("orderNo", "%2026%");
c.andGreaterThan("amount", 100);
w.or().andEqualTo("type", "VIP");                  // OR 另一组
List<Order> list = demoDao.selectListByWrapper(w);
PageData<Order> page = demoDao.selectPageByWrapper(pageInfo, w);
```

**★ `boolean exists` / `boolean notNull` 两个构造参数：**
```
exists  = true → 表字段是否存在的校验
notNull = true → 是否强制非空
（默认 false，由 AllInOneDBUtil 兜底）
```

---

## 四、★★★★★ `insertBatch` 的真实 SQL 拼装

```java
public int insertBatch(List list, Class<?> entityClass, Boolean ignoreTenant) {
    if (CollectionUtils.isEmpty(list)) return 0;

    SeeyonEntityColumns entityColumns = SeeyonEntityHelper.getEntityColumns(entityClass);
    String tableName = entityColumns.getTableName();

    ArrayList<HashMap<String,Object>> datas = new ArrayList<>();
    for (Object o : list) {
        allInOneDBInterceptor.before(o, AllInOneDBType.INSERT);          // ① 拦截器前置
        Map copyMap = ObjToMapUtil.objectToMap(o);                        // ② 对象转 Map
        HashMap<String,Object> dbMap = new HashMap<>();
        copyMap(copyMap, dbMap, entityColumns.getColumns());              // ③ 属性名→列名
        allInOneDBInterceptor.update(o, dbMap, AllInOneDBType.INSERT,
                                     entityColumns, ignoreTenant, false); // ④ 拦截器加工（租户等）
        datas.add(dbMap);
    }

    Map valueMap = datas.get(0);
    StringBuilder columnSql = new StringBuilder();
    StringBuilder unknownMarkSql = new StringBuilder();
    Object[] keys = new Object[valueMap.size()];
    int i = 0;
    for (String key : valueMap.keySet()) {
        keys[i] = key;
        columnSql.append(i == 0 ? "" : ",").append(key);
        unknownMarkSql.append(i == 0 ? "" : ",").append("?");
        ++i;
    }

    StringBuilder sql = new StringBuilder();
    sql.append("INSERT INTO ").append(tableName);
    sql.append(" (").append(columnSql).append(" ) VALUES (").append(unknownMarkSql).append(" )");

    jdbcTemplate.batchUpdate(sql.toString(), datas,
        allInOneProperties.getBatchSize(),                                 // ⑤ 批量大小
        new CustomParameterizedPreparedStatementSetter(keys));
    return datas.size();
}
```

### ★★★★★ 六条关键事实

| # | 事实 |
|---|---|
| 1 | SQL 模板：`INSERT INTO {table} ({col1,col2}) VALUES (?,?)` |
| 2 | **列名用第一条数据的 keySet**（假定所有行字段一致） |
| 3 | 走 `jdbcTemplate.batchUpdate`，**不是 MyBatis** |
| 4 | 批次大小 = `allInOneProperties.getBatchSize()` |
| 5 | **`AllInOneDBInterceptor`** 在前后都有钩子（`before` / `update`） |
| 6 | `ignoreTenant` 参数控制是否注入租户条件 |

### ★★★★ 第 2 条曾被误判（已在 44 篇修正）

```
columnsSql 取 datas.get(0) 的 keySet —— 看起来会因行字段不同而丢列
```

**★★★ 实际不会（第 44 轮反编译 `copyMap` 后修正）：**
```java
private void copyMap(Map copyMap, Map dbMap, Map<String,String> columns) {
    for (Map.Entry<String,String> entry : columns.entrySet()) {   // ★ 遍历 @Column 注解
        dbMap.put(entry.getValue(), copyMap.get(entry.getKey()));
    }
}
```
**⇒ dbMap 的 key 集合恒等于 `@Column` 注解集合，与对象实际值无关。**
**⇒ 列清单永远一致，不会丢列；唯一影响是某列为 null 时插 NULL。**

---

## 五、`updateBatchByIds` 的签名（未展开）

```java
public int updateBatchByIds(List list, Set<String> columnSet,
                            Boolean ignoreTenant, Boolean noUpVersion, Class<?> entityClass)
```
**★ 五参数：`columnSet` = 只更新指定列，`noUpVersion` = 不递增版本号。**
**待展开（下一轮）。**

---

## 六、闭环：从注解到 SQL 的完整路径

```
@Entity + @Table(name) + @Column(name) 实体类
   ↓ SeeyonEntityHelper.initEntity()（应用启动时）
SeeyonEntityColumns { tableName, columns(属性→列), javaTypes, jdbcTypes, enumList }
   ↓ AbstractAllInOneBaseDao.xxx()
   ↓ isAllInOneByJDBC() && contains(entityClass)
AllInOneDBUtil.insertBatch / jdbcCondition / buildQueryString
   ↓ columns.get(属性名) → 列名
"INSERT INTO t_order (id,orderno,amount) VALUES (?,?,?)"
   ↓ jdbcTemplate.batchUpdate(batchSize)
DB
```

---

## 七、待验证

| 问题 | 状态 |
|---|---|
| `entity.java.ftl` 3.0 的 `superClass` 变量名 | UNVERIFIED（我传空） |
| `DataType` 枚举全部取值 | 部分（LONG/STRING/DECIMAL/DATETIME/INTEGER 已见） |
| `javaType` 与 `dataTypeName` 的真实映射表 | UNVERIFIED（`EntityCodeUtils.getJavaType`） |
| `updateBatchByIds` 的 UPDATE 拼装 | 待展开 |
| `AllInOneDBInterceptor.before/update` 做什么 | 待反编译 |
| `ObjToMapUtil.objectToMap` 的空值策略 | 待反编译 |
| `batchSize` 默认值 | UNVERIFIED |