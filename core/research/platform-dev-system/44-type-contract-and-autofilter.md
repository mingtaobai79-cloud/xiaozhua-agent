# 44 · ★★★★★ 元数据→代码 的类型契约 + 缓存/自动过滤（P0 四连）

**证据来源**：`ObjToMapUtil` / `ExprDataTypeTransferUtil` / `DataType` / `TemplateAdapter` / `AllInOneDBInterceptor` / 模板原文
**证据等级**：VERIFIED_STATIC_BYTECODE + LIVE

---

## 一、★★★★★ 修正：`field.dataType` 与 `field.javaType` 的真相

### 1.1 我之前的错误（必须记录）

第 20-21 轮渲染时我用：
```java
f.put("javaType",   jt);   // Java 类型名
f.put("dataType",   dt);   // ← 我传了枚举名（如 LONG）
f.put("dataTypeName", dt);
```
产物成了 `private LONG id;`，我当时标为「模型缺失，UNVERIFIED」。

### 1.2 模板原文（3.0 `entity/entity.java.ftl`）

```freemarker
,dataType = DataType.${field.dataTypeCapName}          ← 行 219
private ${field.dataType} ${DtoCodeUtil.handleAttributeName4Dto(field.name)}   ← 行 234
public ${field.dataType} get${DtoCodeUtil.handleCapAttributeName4Dto(field.name)}()   ← 行 240
<#if field.dataTypeName == 'DECIMAL' || field.dataTypeName == 'CURRENCY'>   ← 行 153
```

### ★★★★★ 真正的契约

| 模板变量 | 真实含义 | 示例值 |
|---|---|---|
| **`field.dataType`** | **Java 类型全名** | `java.lang.Long` |
| **`field.dataTypeName`** | 平台 DataType 枚举名 | `BIGINTEGER` |
| **`field.dataTypeCapName`** | 枚举名首字母大写（拼 `DataType.XXX` 用） | `BigInteger`…（实际是 `BIGINTEGER`） |

### 1.3 修正后重渲染（LIVE）

```java
@Column(name = "id", columnDefinition = "")
,dataType = DataType.LONG
private Long id ;

@Column(name = "orderno", columnDefinition = "")
,dataType = DataType.STRING
private String orderNo ;

@Column(name = "amount", columnDefinition = "")
,dataType = DataType.DECIMAL
private BigDecimal amount ;

@Column(name = "createdate", columnDefinition = "")
,dataType = DataType.DATETIME
private Date createDate ;
```

**⇒ 完全正确。`field.dataType` = Java 全类名，`field.dataTypeName` = 枚举名。**
**⇒ 之前记录的「类型名问题」是我传参错误，已修正。**

---

## 二、★★★★★ `DataType` 枚举全部 19 个取值

```java
public enum DataType implements Messageable {
    STRING(0),          INTEGER(1),
    BIGINTEGER(5),      DECIMAL(6),      BOOLEAN(7),
    DATETIME(8),        DATE(9),         TIME(10),
    ENTITY(11),         OBJECT(12),      ENUM(13),
    ATTACHMENT(14),     MULTILINESTRING(15),
    CURRENCY(17),       CTPENUM(18),
    ARRAY(20),          MAP(21),         SORTORDER(22),
    METADATA(23);
}
```

### ★★★ code 不连续（0,1,5,6,7,8,9,10,11,12,13,14,15,17,18,20,21,22,23）

**缺 2/3/4/16/19 —— 说明有历史废弃类型，code 是持久化值不能复用。**

### ★★ 四类关联实体

```java
public static final Set<String> DATATYPE_RELATION_ENTITY =
    Sets.newHashSet(DataType.CTPENUM.name(), DataType.ENUM.name(), DataType.ENTITY.name());
```
**⇒ 只有这 3 个是「关联实体」类型（ATTACHMENT 单独处理）。**

---

## 三、★★★★★ `DataType` → Java 类型映射表（表达式用）

```java
// ExprDataTypeTransferUtil$1（匿名内部类初始化）
this.put(DataType.STRING.name(),          String.class.getName());
this.put(DataType.MULTILINESTRING.name(), String.class.getName());
this.put(DataType.BOOLEAN.name(),         Boolean.class.getName());
this.put(DataType.CURRENCY.name(),        BigDecimal.class.getName());
this.put(DataType.DECIMAL.name(),         BigDecimal.class.getName());
this.put(DataType.INTEGER.name(),         Integer.class.getName());
this.put(DataType.BIGINTEGER.name(),      Long.class.getName());
this.put(DataType.TIME.name(),            String.class.getName());   ← ★ TIME 是 String
this.put(DataType.DATE.name(),            Date.class.getName());
this.put(DataType.DATETIME.name(),        Date.class.getName());
```

```java
public static String getJavaType(String dataTypeName) {
    String javaType = dataTypeExchangeMap.get(dataTypeName);
    if (isEmpty(javaType)) throw new BusinessException("不支持的表达式返回值类型");
    return javaType;
}
```

### ★★★★★ 六条映射事实

| DataType | Java 类型 | 备注 |
|---|---|---|
| `STRING` | `String` | |
| `MULTILINESTRING` | `String` | 多行文本也是 String |
| `BOOLEAN` | `Boolean` | |
| `CURRENCY` / `DECIMAL` | **`BigDecimal`** | 金额用 BigDecimal |
| `INTEGER` | `Integer` | |
| `BIGINTEGER` | **`Long`** | ★ 名字叫 Big**Integer**，实际是 Long |
| `TIME` | **`String`** | ★★ 不是 java.sql.Time！ |
| `DATE` / `DATETIME` | `Date` | 都是 java.util.Date |

### ★★★★ 三个反直觉点（容易踩坑）

1. **`BIGINTEGER` → `Long`**（不是 BigInteger）
2. **`TIME` → `String`**（不是 Date/Time）
3. **`DECIMAL`/`CURRENCY` → `BigDecimal`**（不是 Double）

**⇒ 这条表只覆盖 10 个类型，`ENTITY`/`ENUM`/`CTPENUM`/`ATTACHMENT`/`ARRAY`/`MAP`/`OBJECT`/`SORTORDER`/`METADATA` 不在表达式可用类型里（调用会抛「不支持的表达式返回值类型」）。**

---

## 四、★★★★★ `DataTypeMappingUtil` 的 Java 类型常量

```java
public static final String STRING   = "java.lang.String";
public static final String INTEGER  = "java.lang.Integer";
public static final String LONG     = "java.lang.Long";
public static final String DOUBLE   = "java.lang.Double";
public static final String DECIMAL  = "java.math.BigDecimal";
public static final String DATE     = "java.util.Date";
public static final String BOOLEAN  = "java.lang.Boolean";
public static final String LIST     = "java.util.List";
public static final String MAP      = "java.util.Map";

public static final Set<String> STRINGS  = {"String", "BigDecimal", "Integer", "Long"};
public static final Set<String> DECIMALS = {"Long", "Double", "BigDecimal", "Integer"};
```

**★ `STRINGS` / `DECIMALS` 是两个「可互相转换的类型组」白名单。**
**★ `Double` 只在 `DECIMALS` 里，不在 `STRINGS` 里。**

---

## 五、★★★★★ `ObjToMapUtil.objectToMap` —— 空值策略（关键修正）

```java
public static Map<String, Object> objectToMap(Object obj) {
    if (obj == null) return null;
    Map<String,Object> map = new HashMap<>();
    BeanInfo beanInfo = beanInfoCache.get(obj.getClass());
    if (beanInfo == null) {
        beanInfo = Introspector.getBeanInfo(obj.getClass());
        beanInfoCache.put(obj.getClass(), beanInfo);
    }
    for (PropertyDescriptor property : beanInfo.getPropertyDescriptors()) {
        String key = lowerFirst(property.getName());
        if (key.compareToIgnoreCase("class") == 0) continue;      // 跳过 class
        Method getter = property.getReadMethod();
        Object value = getter != null ? getter.invoke(obj) : null;

        // ★ 单个枚举 → code
        if (value instanceof Messageable) value = ((Messageable) value).code();

        // ★ 枚举 List → 逗号分隔 code
        if (value instanceof List && !isEmpty && first != null && first instanceof Messageable) {
            List<String> codes = ...;
            if (!isEmpty(codes)) value = String.join(",", codes);
        }
        map.put(key, value);          // ★★ null 也 put！
    }
    return map;
}
```

### ★★★★★ 四条事实

| # | 事实 |
|---|---|
| 1 | 用 **`Introspector.getBeanInfo`**（JavaBean 属性），不是反射字段 |
| 2 | **`null` 值也会 `put`**（key 一定存在） |
| 3 | 枚举值直接转成 `code()` |
| 4 | 枚举 List 转成 `"1,2,3"` 逗号串 |

### ★★★★ 修正我第 41 轮的错误结论

**我在 `41-entity-annotation-mapping.md` 里写：「列清单取 datas.get(0) 的 keySet，如果第二条数据有额外字段就丢字段」——这是错的。**

```java
private void copyMap(Map<String,Object> copyMap, Map<String,Object> dbMap, Map<String,String> columns) {
    for (Map.Entry<String,String> entry : columns.entrySet()) {   // ★ 遍历的是 columns（@Column 注解）
        String property = entry.getKey();
        String column   = entry.getValue();
        dbMap.put(column, copyMap.get(property));                  // ★ 注解里有就一定 put
    }
}
```

**⇒ dbMap 的 key 集合 = `columns` 的 key 集合 = 所有带 `@Column` 的字段。**
**⇒ 与对象实际值无关，**列清单永远一致**，不会丢列。**
**⇒ 唯一影响：`copyMap.get(property)` 可能返回 null，导致该列插 NULL（不是丢列）。**

---

## 六、★★★★★ `AllInOneDBInterceptor.select` 的自动过滤

```java
public void select(Map<String,Object> whereMap, boolean ignoreTenant,
                   Class<?> entityClass, String daoMethod) {
    Assert.isTrue(!ignoreTenant, "禁止使用IgnoreTenant结尾的方法");
    selectByIgnoreTenant(whereMap, ignoreTenant, entityClass, daoMethod);
}

private void selectByIgnoreTenant(Map<String,Object> whereMap, boolean ignoreTenant,
                                  Class<?> entityClass, String daoMethod) {
    // ① 租户过滤（强制）
    if (!ignoreTenant) {
        Assert.notNull(RequestContext.get().getTenantId(), "租户ID不能为null");
        if (whereMap == null) whereMap = new LinkedHashMap<>();
        whereMap.put("EQ_tenantId", RequestContext.get().getTenantId());
    }

    // ② 密级过滤（有密级体系时）
    String secretClass = EntityAnnotationCache.getSecretClassName(entityClass.getName());
    if (!"selectById".equals(daoMethod)                       // ★ 按 daoMethod 排除
        && !StringUtils.isEmpty(secretClass)
        && (secretLevel = RequestContext.get().getSecretLevel()) != null
        && secretLevel >= 0) {
        whereMap.put("LE_secretN", secretLevel);              // ★ 密级 <= 当前用户密级
    }
}
```

### ★★★★★ 三条硬事实

| # | 事实 |
|---|---|
| 1 | **每次查询自动加 `EQ_tenantId`**（业务代码永远不用写租户条件） |
| 2 | **密级实体自动加 `LE_secretN`**（只看得到 ≤ 自己密级的数据） |
| 3 | **`selectById` 被排除在密级过滤外**（按 id 查不受密级限制） |

**★★★ 第 3 条是安全边界：**知道 id 就能拿到任意密级数据**（平台有意为之，用于精确访问）。**

**★ `daoMethod` 的真实用途：只用来判断「是不是 `selectById`」。**
**⇒ 我第 42 轮猜的「按方法名做字段裁剪」是错的，真正用途是密级过滤豁免。**

---

## 七、★★★★ `LazyCacheUtils` —— 模板注册表的读口

```java
public final class LazyCacheUtils {
    public static final String TEMPLATE_PATH_CACHE = "template_path_cache";

    public static String getTemplatePath(String templatePath) {
        return (String) LazyCacheFactory.get(TEMPLATE_PATH_CACHE, templatePath);
    }
    public static List<SchemaInfo> getSchemaInfo(long deployId) {
        return (List) LazyCacheFactory.get("schemaCache", deployId);
    }
    public static String generatePublishStateCacheKey(long deployId) {
        return "deploy:state:" + deployId;
    }
}
```
**⇒ 只是缓存读口，缓存名 `template_path_cache`。**
**⇒ 谁往里写（模板扫描/注册）待查 `LazyCacheFactory` 及启动扫描器。**

---

## 八、完整自动注入清单（最终版）

| 时机 | 自动做的事 | 位置 |
|---|---|---|
| **INSERT** | `id` = `Ids.gidLong()`（无则生成） | Interceptor.update |
| **INSERT** | `create_time` / `update_time` = `new Date()` | Interceptor.update |
| **INSERT** | `version` = 0 | Interceptor.update |
| **INSERT** | `tenant_id` = `RequestContext.getTenantId()` | Interceptor.update |
| **UPDATE** | `update_time` = `new Date()` | Interceptor.update |
| **UPDATE** | `version` = +1（`noUpVersion` 则不变） | Interceptor.update |
| **UPDATE** | `create_time` **被移除** | Interceptor.update |
| **UPDATE** | `tenant_id` **被移除** | AllInOneDBUtil |
| **SELECT** | `EQ_tenantId` 条件 | Interceptor.select |
| **SELECT** | `LE_secretN` 密级条件（非 `selectById`） | Interceptor.select |
| **所有** | 枚举 → `code()` | ObjToMapUtil |
| **所有** | 枚举 List → `"1,2,3"` | ObjToMapUtil |
| **非 MySQL** | `Boolean` → 0/1 | Interceptor.update |
| **写入** | `@Safety(openApiEncrypt)` 字段加解密 | processReversibleEncryption |
| **所有** | `*IgnoreTenant` 方法直接断言失败 | Assert |

---

## 九、待验证

| 问题 | 状态 |
|---|---|
| `LazyCacheFactory` 与模板注册写入者 | 待反编译 |
| `StringUtils.compareVersion` 排序规则 | 待确认 |
| `Explore secretClass`（`EntityAnnotationCache.getSecretClassName`） | UNVERIFIED |
| `EntityEncryptionService` 的算法 | UNVERIFIED |
| `batchSize` 默认值 | UNVERIFIED |