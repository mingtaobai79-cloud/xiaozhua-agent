# 42 · ★★★★★ AllInOneDBInterceptor：自动填充与类型转换中枢

**证据来源**：`AllInOneDBInterceptor` 反编译（271 行）+ `AllInOneDBUtil.updateBatchByIds`
**证据等级**：VERIFIED_STATIC_BYTECODE

---

## 一、★★★★★ 这个类做什么

```
AllInOneDBUtil.insertBatch / updateBatchByIds
   ↓ 对每一行数据调用
AllInOneDBInterceptor.before(o, dbType)          ← 前置
AllInOneDBInterceptor.update(o, dbMap, dbType, cols, ignoreTenant, noUpVersion)  ← 主逻辑
   ↓
真正交给 jdbcTemplate.batchUpdate
```

**它是「对象 → 数据库行」的最后一站，负责：**
1. 租户 ID 注入
2. Boolean → 0/1 转换（非 MySQL）
3. 枚举对象 → 枚举 code
4. 多选枚举 List → 逗号分隔 code 串
5. **主键生成 + 创建/更新时间 + 版本号自动填充**
6. 加解密处理

---

## 二、★★★★★ 租户注入（强制）

```java
Assert.isTrue(!ignoreTenant, "禁止使用IgnoreTenant结尾的方法");
if (!ignoreTenant) {
    Assert.notNull(RequestContext.get().getTenantId(), "租户ID不能为null");
    dbMap.put("tenant_id", RequestContext.get().getTenantId());
}
```

### ★★★★ 两条硬约束

| # | 约束 |
|---|---|
| 1 | **调 `*IgnoreTenant` 结尾的 DAO 方法直接断言失败** |
| 2 | **必须有 `RequestContext`，且 `tenantId` 非空** |

**⇒ 所有写操作/读操作都必须在**有请求上下文的线程**里执行。**
**⇒ 定时任务、异步线程池直接调 DAO 会炸（这是「必须在上下文中」的第二个证据，第一个是 `create4Bpm`）。**

---

## 三、★★★★★ 类型转换（三组）

### 3.1 Boolean → 0/1（仅非 MySQL）

```java
if (Apps.getDatabaseType() != DatabaseType.mysql && Boolean.class.isAssignableFrom(javaType)) {
    Object v = dbMap.get(columnName);
    if (v == null)      dbMap.put(columnName, 0);
    else if ((Boolean) v) dbMap.put(columnName, 1);
    else                dbMap.put(columnName, 0);
}
```
**★ MySQL 有原生 boolean（tinyint），其他库（Oracle/达梦等）转 0/1。**

### 3.2 枚举对象 → 枚举 code

```java
if (Messageable.class.isAssignableFrom(javaType)) {
    Messageable[] constants = (Messageable[]) javaType.getEnumConstants();
    Object v = dbMap.get(columnName);
    for (Messageable e : constants) {
        if (e == v) dbMap.put(columnName, e.code());   // ★ 存 code，不存 name
    }
}
```
**⇒ 数据库中存的是 `Messageable.code()`，不是枚举名。**

### 3.3 多选枚举 List → 逗号分隔 code

```java
if (enumList.containsKey(property)) {
    String v = dbMap.get(columnName) + "";
    if ("[]".equals(v)) { dbMap.put(columnName, ""); continue; }   // 空列表 → 空串
    if (StringUtil.isEmpty(v)) continue;
    String[] split = v.split(",");
    List<String> nSplit = new ArrayList<>();
    for (String s : split) {
        for (Messageable e : enumList.get(property)) {
            if (e.toString().equalsIgnoreCase(s)) nSplit.add(e.code() + "");
        }
    }
    dbMap.put(columnName, String.join(",", nSplit));
}
```
**⇒ `CtpEnumItem` 多选字段在库里是 `"1,2,3"` 这样的 code 串。**

---

## 四、★★★★★ INSERT 自动填充（5 个字段）

```java
if (AllInOneDBType.INSERT == dbType) {
    Long id = null;
    try {
        Entityable entityable = (Entityable) o;
        if (entityable.getId() != null) id = entityable.getId();
    } catch (Exception ignored) {}

    if (null == id) id = Ids.gidLong();              // ① 主键（雪花+随机）

    Date date = new Date();
    dbMap.put("id",          id);                     // ①
    dbMap.put("create_time", date);                   // ②
    dbMap.put("update_time", date);                   // ③
    dbMap.put("version",     0);                      // ④

    setObjectId(o,         id,   columnFields);       // ★ 回写到对象
    setObjectCreateTime(o, date, columnFields);       // ★
    setObjectUpdateTime(o, date, columnFields);       // ★
    setObjectVersion(o,    0,    columnFields);       // ★
}
```

### ★★★★★ 四条关键事实

| # | 事实 |
|---|---|
| 1 | 主键 = 对象已有 id 则沿用，否则 `Ids.gidLong()` |
| 2 | `create_time` = `update_time` = `new Date()`（同一时刻） |
| 3 | `version` 初始 0 |
| 4 | **四个值都回写到 Java 对象**（`setObjectXxx` 用反射 setField） |

**⇒ 第 4 条极重要：`insertBatch` 之后，传入的对象已经有 id 了。**
**⇒ 这就是「主键回填」在 JDBC 通道的实现（MyBatis 通道走 `entity.getId() → dto.setId()`）。**

### 4.1 回写机制

```java
private void setObjectId(Object o, Long id, Map<String,Field> columnFields) {
    Field f = columnFields.get("id");
    if (f != null) { f.setAccessible(true); f.set(o, id); }
}
```
（同类：`setObjectCreateTime` / `setObjectUpdateTime` / `setObjectVersion`）

**⇒ 靠 `SeeyonEntityColumns.getColumnFields()` 拿到 Field 反射回写。**
**⇒ `columnFields` 只在有 `@Column` 的字段上建立 —— 没标 `@Column` 的字段不会回写。**

---

## 五、★★★★★ UPDATE 的乐观锁

```java
if (AllInOneDBType.UPDATE == dbType) {
    Date date = new Date();
    dbMap.put("update_time", date);                        // ① 刷新更新时间
    setObjectUpdateTime(o, date, columnFields);

    if (dbMap.get("version") != null) {
        int version = Integer.parseInt(dbMap.get("version") + "");
        if (noUpVersion) {
            setObjectVersion(o, version, columnFields);    // ② 不递增
        } else {
            dbMap.put("version", version + 1);             // ③ 递增
            setObjectVersion(o, version + 1, columnFields);
        }
    } else {
        dbMap.put("version", 0);                           // ④ 无版本则置 0
        setObjectVersion(o, 0, columnFields);
    }
    dbMap.remove("create_time");                           // ⑤ 创建时间不参与更新
}
```

### ★★★★★ 五条事实

| # | 事实 |
|---|---|
| 1 | `update_time` 每次更新自动刷新（不用手写） |
| 2 | `version` 默认 `+1`（乐观锁） |
| 3 | `noUpVersion=true` → 版本号保持不变（`.versionNoUpdate*` 系列方法） |
| 4 | `create_time` **被移除**（永远不会被 UPDATE 覆盖） |
| 5 | 版本递增也**回写到对象** |

**⇒ 「为什么我的 create_time 没变」的答案：平台主动删掉了。**
**⇒ 「为什么 version 自己涨了」的答案：平台主动 +1。**

---

## 六、★★★★★ `updateBatchByIds` 的 SQL 拼装

```java
public int updateBatchByIds(List list, Set<String> columnSet,
                            Boolean ignoreTenant, Boolean noUpVersion, Class<?> entityClass) {
    // ... 对每行调 interceptor 生成 dbMap ...

    // ★ columnSet 过滤：排除 tenant_id 和 id
    Set cSet = null;
    if (columnSet != null) {
        cSet = new HashSet();
        for (String c : columnSet) {
            if (columnsMap.get(c) == null                // 属性不存在
                || "tenant_id".equals(columnsMap.get(c)) // ★ 不能更租户
                || "id".equals(columnsMap.get(c))) continue;  // ★ 不能更主键
            cSet.add(columnsMap.get(c));
        }
    }

    Map valueMap = datas.get(0);
    valueMap.remove("tenant_id");                        // 租户不进 SET

    sql.append("UPDATE ").append(tableName).append(" SET ");
    if (cSet != null) {
        keys = new Object[cSet.size() + 1];
        for (String s : cSet) { columnSql.append(s + " = ? ,"); keys[i++] = s; }
        keys[i] = "SWHEREid";                            // ★ 哨兵键
    } else {
        for (String key : valueMap.keySet()) {
            if ("id".equals(key)) continue;               // id 不进 SET
            columnSql.append(key + " = ? ,");
            keys[i++] = key;
        }
        keys[i] = "SWHEREid";
    }
    sql.append(columnSql).append(" WHERE id = ?");
    for (Map m : datas) m.put("SWHEREid", m.get("id"));   // ★ id 挪到参数末尾
    jdbcTemplate.batchUpdate(sql, datas, batchSize, new CustomParameterizedPreparedStatementSetter(keys));
}
```

### ★★★★★ SQL 最终形态

```sql
UPDATE t_order SET orderno = ? , amount = ? , update_time = ? , version = ?  WHERE id = ?
```

### ★★★ `SWHEREid` 哨兵技巧（值得学）

```
问题：batchUpdate 的 keys 数组顺序 = PreparedStatement 的参数位置顺序
      SET 部分的参数在前，WHERE id = ? 的参数在最末
解决：在 keys 数组末尾塞一个假键 "SWHEREid"，
      然后对每行数据 map.put("SWHEREid", map.get("id"))
⇒ 参数顺序自然对齐，不用特殊处理最后一位
```

### ★★★ 三条约束

| # | 约束 |
|---|---|
| 1 | `columnSet` 里的 `tenant_id` / `id` **被静默丢弃** |
| 2 | `columnSet` 里的属性名必须存在于 `columnsMap`，否则静默丢弃 |
| 3 | 无条件 `WHERE id = ?` —— **必须有 id，不支持条件更新** |

---

## 七、★★★ `delete` / `select` 的两个钩子

```java
public void delete(Map<String,Object> whereMap, boolean ignoreTenant)
public void select(Map<String,Object> whereMap, boolean ignoreTenant,
                   Class<?> entityClass, String daoMethod)
private void selectByIgnoreTenant(Map<String,Object> whereMap, boolean ignoreTenant,
                                  Class<?> entityClass, String daoMethod)
```

**★★★ `select` 带 `daoMethod` 参数 —— 真实用途（第 44 轮反编译确认）：**
```java
if (!"selectById".equals(daoMethod) && !isEmpty(secretClass) && secretLevel >= 0) {
    whereMap.put("LE_secretN", secretLevel);
}
```
**⇒ 只用来判断「是不是 `selectById`」，从而**跳过密级过滤**。**
**⇒ 我第 42 轮猜的「按方法名做字段裁剪」是错的，已修正。**

---

## 八、★★★ 加解密

```java
private void processReversibleEncryption(boolean isCreate, Object arg, List<SafeField> safeFieldList)
private EntityEncryptionService entityEncryptionService;   ← 注入
private SecretEnumUpdateService secretEnumUpdateService;   ← 注入
```

```java
if (AllInOneDBType.INSERT == dbType) processReversibleEncryption(true,  o, safeFieldList);
else                                 processReversibleEncryption(false, o, safeFieldList);
```

**⇒ 字段级加解密在写入前自动执行（`@Safety(openApiEncrypt=true)` 的字段）。**

---

## 九、★★★★★ 完整自动填充清单（开发者不用手写）

| 字段 | INSERT | UPDATE | 说明 |
|---|---|---|---|
| `id` | ✅ `Ids.gidLong()` | ❌（只做 WHERE） | 主键 |
| `tenant_id` | ✅ `RequestContext.getTenantId()` | ❌（被移除） | 租户 |
| `create_time` | ✅ `new Date()` | ❌（被移除） | 创建时间 |
| `update_time` | ✅ `new Date()` | ✅ `new Date()` | 更新时间 |
| `version` | ✅ `0` | ✅ `+1`（或不变） | 乐观锁 |

**⇒ 主键、租户、创建时间、更新时间、版本号**全部自动**，业务代码一个都不用碰。**

---

## 十、待验证

| 问题 | 状态 |
|---|---|
| `select` 的 `daoMethod` 分支 | 待展开 |
| `objToMap` 的空值策略（null 是否进 map） | 待反编译 `ObjToMapUtil` |
| `Ids.gidLong()` 是否就是雪花+随机 | 已证（第 7 轮：`nextId()+ThreadLocalRandom.nextLong()`） |
| `EntityEncryptionService` 的算法 | UNVERIFIED |
| `SafeField` 的来源 | UNVERIFIED |
| `batchSize` 默认值 | UNVERIFIED |