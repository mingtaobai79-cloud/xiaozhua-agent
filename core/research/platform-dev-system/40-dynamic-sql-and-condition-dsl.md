# 40 · ★★★★★ 动态 SQL 与条件 DSL（零 SQL 生成的真相）

**证据来源**：`AllInOneDBUtil` / `SearchFilter` / `SearchFilter$Operator` 反编译
**证据等级**：VERIFIED_STATIC_BYTECODE

---

## 一、★★★★★ SQL 拼装的真实代码

### 1.1 `buildQueryString` —— SELECT 拼接骨架

```java
private String buildQueryString(String tables, String[] columns,
                                Map<String,String> columnsMap, String where,
                                PageInfo pageInfo, Sort sort, Class<?> entityClass) {
    StringBuilder query = new StringBuilder(120);
    query.append("SELECT ");
    if (columns != null && columns.length != 0) {
        appendColumns(query, columns, columnsMap);      ← 指定列
    } else {
        appendColumns(query, columnsMap);               ← 全部列
    }
    query.append("FROM ");
    query.append(tables);
    appendClause(query, where);                          ← WHERE
    if (null != sort) {
        getSortSql(sort, query, entityClass);            ← ORDER BY
    }
    if (null != pageInfo) {
        return getPageSql(pageInfo, query.toString());   ← 分页
    }
    return query.toString();
}
```

**★ 拼接顺序：`SELECT 列 FROM 表 [WHERE] [ORDER BY] [分页]`**

### 1.2 `getSortSql` —— 属性名 → 列名映射

```java
private void getSortSql(Sort sort, StringBuilder sql, Class<?> entityClass) {
    sql.append(" order by ");
    for (Sort.Order order : sort) {
        String property = order.getProperty();
        SeeyonEntityColumns columns = SeeyonEntityHelper.getEntityColumns(entityClass);
        String columnName = columns.getColumns().get(property);
        Assert.notNull(columns, "类[" + entityClass + "]不存在");
        Assert.notNull(columnName, "属性[" + property + "]不存在");
        sql.append(columnName + " " + order.getDirection());
        sql.append(",");
    }
    sql.deleteCharAt(sql.length() - 1);
}
```

**★★★★★ 关键：`SeeyonEntityHelper.getEntityColumns(entityClass)` 返回**
```java
SeeyonEntityColumns {
    Map<String,String>  columns;      // 属性名 → 列名
    Map<String,Class>   javaTypes;    // 属性名 → Java 类型
}
```
**⇒ 平台的「实体元数据 → 数据库列」映射全在 `SeeyonEntityColumns` 里，运行时从注解/配置解析。**

### 1.3 `getPageSql` —— 数据库方言分页

```java
private String getPageSql(PageInfo pageInfo, String originalSql) {
    return DatabaseDialectManager.pageSql(pageInfo, originalSql);
}
```
**⇒ 分页完全靠 `DatabaseDialectManager`（MySQL/Oracle/达梦/人大金仓 等方言）**

---

## 二、★★★★★ 条件 DSL（`SearchFilter`）—— 这才是「动态查询」的真正接口

### 2.1 `SearchFilter` 结构

```java
public class SearchFilter {
    public String   property;    // 字段名
    public Operator operator;    // 操作符
    public Object   value;       // 值
    public Boolean  rightAttr = false;   // ★ true = value 是「另一个字段名」而不是字面值
}
```

### 2.2 14 个操作符（真实枚举）

```java
public enum Operator {
    EQ(" ="),          NEQ(" !="),
    LIKE(" like"),     LLIKE(" like"),    RLIKE(" like"),    NOTLIKE(" not like"),
    GT(" >"),          GE(" >="),          LT(" <"),          LE(" <="),
    IN(" in"),         NOTIN(" not in"),
    NULL(" is null"),  NOTNULL(" is not null");
}
```

### 2.3 ★★★★★ key 的写法（下划线分隔 DSL）

```java
public static SearchFilter parse(String param, Object value) {
    String[] names = StringUtils.split(param, "_");
    ...
    if (names.length == 1) {              ← "amount"          → EQ
        fieldName = names[0];
        if (fieldName.startsWith("@")) { rightAttr = true; fieldName = fieldName.replace("@", ""); }
        op = Operator.EQ;
    } else if (names.length == 2) {       ← "GT_amount"       → GT on amount
        fieldName = names[1];
        String opStr = names[0].toUpperCase();
        if (opStr.startsWith("@")) { rightAttr = true; opStr = opStr.replace("@", ""); }
        op = Operator.valueOf(opStr);
    } else if (names.length == 3) {       ← "amount_GT_otherAmount" → GET column 3
        String opStr = names[0].toUpperCase();
        if (opStr.startsWith("@")) { rightAttr = true; }
        fieldName = names[2];
        op = Operator.valueOf(names[1].toUpperCase());
    } else {
        throw new IllegalArgumentException(param + " is not a valid search filter name");
    }
}
```

### ★★★★★ 三种 Key 形态（实证）

| 写法 | 含义 | 生成 SQL |
|---|---|---|
| `"amount"` | 等值 | `amount = ?` |
| `"GT_amount"` | 大于 | `amount > ?` |
| `"LIKE_name"` | 模糊 | `name like ?` |
| `"IN_status"` | 包含 | `status in (?,?,...)` |
| `"NULL_remark"` | 为空 | `remark is null` |
| `"NOTNULL_remark"` | 非空 | `remark is not null` |
| `"@amount"` | 字段对比 | `amount = otherColumn`（**右值是字段名**） |
| `"amount_GT_otherAmount"` | 两字段比较 | `otherAmount > amount`（3 段式，取 names[2] 为字段、names[1] 为操作符） |

**★★★ 注意 3 段式是反直觉的**
```
names[0] = 前缀（可带 @）
names[1] = 操作符
names[2] = 字段名
⇒ "amount_GT_otherAmount" → fieldName = "otherAmount", op = GT
```
**⇒ 3 段式写法很可能是**内部用法**，业务代码应优先用 2 段式 `GT_amount`。**

### 2.4 null 值保护

```java
if (value == null && op != Operator.NULL && op != Operator.NOTNULL) {
    throw new BusinessException("BOOT_4011", new String[]{fieldName});
}
```
**⇒ 除 NULL/NOTNULL 外，value 为 null 直接抛业务异常。**

### 2.5 字段对比（rightAttr）的真实 SQL 生成

```java
if (rightAttr) {
    if (op == NEQ || op == EQ || op == LT || op == LE || op == GT || op == GE) {
        whereSql.append(columnName).append(op.code());
        String vColumn = columnsNames.get(searchFilter.value);
        Assert.notNull(vColumn, "属性[...]右侧属性无法获取字段信息");
        whereSql.append(vColumn);
        whereSql.append(" AND ");
        continue;
    }
    Assert.notNull(null, "右侧属性不支持 " + op + " 操作");
}
```
**⇒ `@GT_amount` + value="otherAmount" → `amount > otherAmount`（列对列比较）**

---

## 三、★★★★★ WHERE 拼装的实际代码（jdbcCondition 前半）

```java
private void jdbcCondition(StringBuilder whereSql, Map<String,Object> whereMap,
                           Map<String,Object> paramMap, Class<?> entityClass) {
    SeeyonEntityColumns entityColumns = SeeyonEntityHelper.getEntityColumns(entityClass);
    Map columnsNames = entityColumns.getColumns();
    Map javaTypes   = entityColumns.getJavaTypes();
    if (MapUtils.isEmpty(whereMap)) return;

    whereSql.append(" WHERE ");
    boolean hasField = false;
    for (Map.Entry<String,Object> entry : whereMap.entrySet()) {
        SearchFilter searchFilter = SearchFilter.parse(entry.getKey(), entry.getValue());
        if (searchFilter == null) continue;

        String columnName = (String) columnsNames.get(searchFilter.getProperty());
        Class  javaType   = (Class)  javaTypes.get(searchFilter.getProperty());

        // ★ 非 String 类型不接受空串
        if (StringUtils.isBlank(searchFilter.getValue() + "")
            && !javaType.isAssignableFrom(String.class)
            && !javaType.isAssignableFrom(List.class)) {
            throw new BusinessException("BOOT_4000")
                  .addError(searchFilter.getProperty() + "非String类型条件数据不能为空");
        }
        Assert.notNull(columnName, "属性[" + searchFilter.getProperty() + "]不存在");
        ...
    }
}
```

### ★★★ Oracle 特殊处理（实证）

```java
// Oracle: LIKE 空值直接跳过
if (Apps.getDatabaseType() == DatabaseType.oracle
    && (op == LIKE || op == LLIKE || op == RLIKE || op == NOTLIKE)
    && StringUtils.isEmpty(actualValue + "")) continue;

// Oracle: String 空值 EQ → is null；NEQ → is not null
if (isOracle && javaType == String.class && StringUtils.isBlank(value + "")) {
    if (op == EQ)  { whereSql.append(columnName).append(" is null "); ... }
    if (op == NEQ) { whereSql.append(columnName).append(" is not null "); ... }
}
```
**★★★★★ 这是 Oracle 特有坑：Oracle 里 `''` 等于 `NULL`。**
**⇒ 平台在 Oracle 上自动把 `= ''` 改写成 `is null`，业务代码不用管。**

---

## 四、★★★★★ 完整的「零 SQL」链条（闭环）

```
开发者写：
    Map<String,Object> cond = new HashMap<>();
    cond.put("GT_amount", 100);
    cond.put("LIKE_name", "订单");
    demoDao.selectPageByConditions(pageInfo, cond, sort);

运行时：
    AbstractAllInOneBaseDao.selectPageByConditions
      ↓ isAllInOneByJDBC() ?
    AllInOneJdbcDao  →  AllInOneDBUtil
      ↓ jdbcCondition(whereSql, whereMap, paramMap, entityClass)
      ↓ SearchFilter.parse("GT_amount", 100)  →  {property:"amount", op:GT, value:100}
      ↓ columnsNames.get("amount")            →  "amount"（列名）
      ↓ buildQueryString("t_order", null, columnsMap, where, pageInfo, sort, entityClass)
      ↓ "SELECT id,order_no,amount,... FROM t_order WHERE amount > ? ORDER BY ... "
      ↓ DatabaseDialectManager.pageSql(...)   →  MySQL: "... LIMIT ?,?"
      ↓ PreparedStatement + setValues(ps)
    DB
```

**⇒ 这就是「zero SQL generation」的完整实现。**
**⇒ 开发者永远不写 SQL，只写 `Map<String,Object>` 条件。**

---

## 五、★★★★★ 对开发者的实际约束

| 约束 | 原因 |
|---|---|
| 查询条件必须用 `Map`，key 遵循 DSL | `SearchFilter.parse` 只认这个格式 |
| key 里不能有下划线（除 DSL 分隔） | `split("_")` 会切开 |
| 3 段式取 `names[2]` 为字段 | 反直觉，慎用 |
| 非 String 类型不能传空串 | 抛 `BOOT_4000` |
| Oracle 上 LIKE 空值会被跳过 | 平台自动处理 |
| 排序属性名必须是实体属性名 | `getEntityColumns().getColumns()` 查表 |
| `Wrapper` 是另一套（类 MyBatis-Plus） | 4 个 `*ByWrapper` 方法 |

---

## 六、待验证

| 问题 | 状态 |
|---|---|
| `DatabaseDialectManager.pageSql` 支持哪些库 | UNVERIFIED |
| `Wrapper` 的完整 API | 待反编译 |
| `SeeyonEntityColumns` 如何从注解解析 | 待反编译 `SeeyonEntityHelper` |
| `insertBatch` 的 INSERT 拼装 | 待读 `dbutil.txt` 前半段 |
| IN 操作符的参数展开 | 待读 |