# boot-starter-elasticsearch：ES 索引与检索

## Capability

**平台把 ES 包成「Spring Data Repository + Criteria 构造器」**：
定义索引实体 → 继承 `BaseElasticsearchRepository` → 用 `Criteria` 拼条件，不写 JSON DSL。

## Version

`boot-starter-elasticsearch` 5.3.290（jar 在盘，javap 全量抽取）。

## Input

`ElasticsearchProperties`（`enable` / `mode` / `hosts` / `userName` / `password` /
`connectTimeOut` / `socketTimeOut` / `compatibilityMode` / `enableVersionCheck`）。

## ★ 一、三步接入

```java
// ① 索引实体：继承 BaseElasticsearchIndex（自带给 id / tenantId 与转换）
public class OrderDoc extends BaseElasticsearchIndex {
    private String orderNo;
    private Long   amount;
    // getter/setter
}

// ② 仓储：继承 BaseElasticsearchRepository
public interface OrderDocRepository extends BaseElasticsearchRepository<OrderDoc> { }

// ③ 用
orderDocRepository.save(doc);
OrderDoc one = orderDocRepository.selectById("id-1");
```

## ★ 二、仓储方法全集（字节码原文）

```java
<S extends T> S save(S);
<S extends T> Iterable<S> saveAll(Iterable<S>);
void deleteById(String);
void deleteByIds(Iterable<String>);
T selectById(String);
List<T> selectByIds(Iterable<String>);
T selectOneByCriteria(Criteria);                                  // default
List<T> selectListByCriteria(Criteria, Sort);
PageData<T> selectPageByCriteria(PageInfo, Criteria, Sort);
```

⇒ **没有 update/deleteByQuery**：更新=再 save（同 id 覆盖），批量删用 `deleteByIds`。

## ★ 三、Criteria 构造（不写 DSL）

```java
Criteria c = Criteria.and();
c.is("orderNo", "SO20261122");
c.isNot("status", "CANCELLED");
c.exists("amount");

Criteria or = Criteria.or().addCriteria(Criteria.and().is("a", 1))
                          .addCriteria(Criteria.and().is("b", 2));

NestedCriteria n = Criteria.nested("items");     // 嵌套字段
```

原文方法：

```java
static Criteria and() / or() / nested(String)
boolean isAnd() / isOr() / isCriteriaEntry() / isNestedCriteria()
Criteria addCriteria(Criteria)
Criteria is(String, Object) / isNot(String, Object) / exists(String)
Operator: AND / OR
```

## 四、索引实体基类提供什么

```java
void from(Object);              // 普通对象 → 索引文档
<T> T to(Class<T>);            // 索引文档 → 普通对象
String getId(); Long getTenantId();
void setId(String); void setTenantId(Long);
```

⇒ **`tenantId` 是基类字段**，租户隔离靠它；写入前要赋值，否则跨租户检索会串。

## Side Effects

- `save` 走 ES 近实时刷新，**写完立刻查可能查不到**（refresh 间隔）。
- 索引结构变更（mapping）需要重建索引，不是改实体就行。
- `selectPageByCriteria` 的分页深翻（from+size 很大）会慢，超大结果集用 `aggregation`。

## Known Constraints

1. `BaseElasticsearchRepository` 继承的是 `org.springframework.data.repository.Repository`（**不是 CrudRepository**）——没有 `findAll()`。
2. 分页/排序用的是平台的 `PageInfo` / `Sort`（`com.seeyon.boot.transport`），不是 Spring Data 的那套。
3. `mode` 决定连接方式（单机/集群），配置错的表现是启动时连不上或写入静默失败。
4. `enable=false` 时整套 Repository 不装配 → 注入就是 null，要 `required=false`。
5. ES 相关能力在标品里主要用于检索/统计，**不是主数据存储**：业务真值仍在 MySQL。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `BaseElasticsearchRepository` 9 方法 | `javap -p` 5.3.290 | VERIFIED_STATIC_BYTECODE |
| `BaseElasticsearchIndex` from/to/id/tenantId | 同上 | VERIFIED_STATIC_BYTECODE |
| `Criteria` 静态构造 + is/isNot/exists + Operator AND/OR | 同上 | VERIFIED_STATIC_BYTECODE |
| `ElasticsearchProperties` 9 字段 | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 全部签名可复核
- ⚠️ 未真机连过 ES（环境未确认启用）

## 给 Agent 的判据

```
要按条件检索            → 定义 Doc extends BaseElasticsearchIndex + Repository，用 Criteria
要更新 ES 里的文档       → 同一个 id 再 save（没有 update 方法）
写完立刻查不到           → ES 近实时，refresh 前查不到属正常
多租户串数据            → 文档 setTenantId 了吗
注入 Repository 为 null → ElasticsearchProperties.enable 是不是 false
```
