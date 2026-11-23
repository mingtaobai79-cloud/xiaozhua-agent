# boot-starter-datasource：数据源、连接池、读写分离与分片

## Capability

**平台的 DataSource 是自研连接池 + 代理层，客开只消费不配置。**
本格回答：能拿到什么、`dy*` 那套是什么、读写分离/分片开关在哪、慢 SQL 阈值在哪。

## Version

`boot-starter-datasource` 5.3.600（jar 在盘，javap 全量抽取）。

## Input

平台配置（`DataSourceProperties`）。

## Required

无。客开代码里**不要自己 new DataSource**，注入 `javax.sql.DataSource` 或直接用 Dao。

## ★ 一、注入什么

```java
@Autowired private DataSource dataSource;              // 平台代理后的数据源
Connection c = dataSource.getConnection();
```

`DataSourceProxySeeyon implements javax.sql.DataSource`（字节码原文）：

```java
DataSource getOriginalDataSource();
void       refreshConfig();                        // 配置热刷新
Connection getConnection();
Connection getConnection(String, String);          // 账号/密码覆盖
```

## ★ 二、`DataSourceProperties` 全字段（37 个，按用途分组）

```java
// 基本
boolean enable; String engine; String url; String database;
String username; String password; String driverClassName;

// ★ dy* = 达梦（国产库）这套连接参数，与主库并存
String dyUrl; String dyUsername; String dyPassword;
String dyDbaUsername; String dyDbaPassword; String dyDbaDatabase; String dyTablespace;

// 池
Integer initialSize; Integer maxActive; Integer minIdle; Integer maxWait;
Integer slowSqlThreshold;      // ★ 慢 SQL 阈值（毫秒）
Integer maxResultThreshold;    // 结果集行数阈值

// 读写分离
boolean enableRWS; List<String> slaveDataSourceNames;

// 分片
boolean enableShard; List<ShardConfigItem> shardConfigItems;
int shardingCount; List<String> shardingDataSourceNames;

// 其它
boolean enableStatistics; boolean overflowMonitorEnabled; boolean enableShardingLog;
ClassLoader beanClassLoader; CompatibilityItem compatibilityItem;
```

连接池实现三选一（私有方法名即证据）：`buildHikari()` / `buildDBCP()` / `buildDBPool()`。

## 三、连接池代理与监控

```
A9ConnectionPoolProxy extends AbstractConnectionPoolProxy
  int  getTotalConnection();
  int  getNoUseCount();
  Set<ConInfo> getUseList();          // 当前占用的连接（排查连接泄漏用）
  void clearPool(); void clearExceedConnInfos();
  void init(DBConProviderConfig, Properties);
```

`ConnectionTimeFilter`（AOP）记录连接耗时；`DBStatementStat` 统计语句。
⇒ **连接泄漏的排查路径：`getUseList()` 看谁占着 + `slowSqlThreshold` 调低看慢 SQL。**

## Side Effects

- `refreshConfig()` 会重建连接池，运行期调用会让在途连接失效。
- 读写分离开启后，写后立刻读可能读到从库旧值（延迟），强一致场景要显式走主库。
- 分片配置改动需要重建数据源，不能热切。

## Known Constraints

1. **`dy*` 是达梦库专用参数**，不代表「两个数据源随便切」；主从切换由 `enableRWS` 控制。
2. 分片（`enableShard` + `shardConfigItems`）是平台级配置，客开代码不能按表指定分片键。
3. 慢 SQL 阈值是**毫秒**，且只在开启统计时才有数据。
4. 事务与数据源绑定：跨数据源的写不在同一事务里（平台没做 XA）。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `DataSourceProperties` 37 私有字段（含 dy*/RWS/shard） | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `DataSourceProxySeeyon` 4 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `A9ConnectionPoolProxy` 监控方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| 三种池实现（buildHikari/buildDBCP/buildDBPool） | 同上（方法名） | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 字段/方法逐个可复核
- ⚠️ 未在真机做过读写分离/分片切换（只读契约）

## 给 Agent 的判据

```
要用数据源        → 注入 javax.sql.DataSource，别自己 new
连接泄漏          → A9ConnectionPoolProxy.getUseList() + 池 maxActive
慢 SQL            → slowSqlThreshold（毫秒）调低 + DBStatementStat
读写分离          → enableRWS + slaveDataSourceNames（注意主从延迟）
国产库适配        → dy* 一组参数（达梦），与主库并存
```
