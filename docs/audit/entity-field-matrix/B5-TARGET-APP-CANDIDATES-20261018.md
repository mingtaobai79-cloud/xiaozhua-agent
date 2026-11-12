# B5 target-app DB candidate check (2026-10-18)

Slice: entity-field matrix / BIGINTEGER. This is a read-only DB candidate check, not page-build or LIVE end-to-end validation.

Environment/source: `udc_test2`, credentials loaded from the existing local environment file; no secret values printed or persisted.

Query time: 2026-10-18 17:42:18 (DB server time).

Predicate: `app_id='8704025620829192834' AND data_type='BIGINTEGER' AND is_system=0`.

## 一、查询

- 查询时刻（DB 服务器时间，第一次）：`2026-10-18 17:42:18`
- 复核时刻（DB 服务器时间，第二次全量复算）：`2026-10-18 17:48:22`
- 谓词：`app_id='8704025620829192834' AND data_type='BIGINTEGER' AND is_system=0`
- 关联：`udc_entity` 取实体名，按 `entity_name, name` 排序

## 二、结果：9 条业务 BIGINTEGER 字段（全量，非抽样）

| 实体 | 字段 | attribute id | entity_id |
|---|---|---|---|
| fileMigration | batchId | 6524864861081717289 | 3582244432195832261 |
| fileMigration | fileSize | 8143482926516424148 | 3582244432195832261 |
| LogSchemeInformatio | processedRows | 1974268840135643078 | 8456954308866361572 |
| LogSchemeInformatio | totalRows | 7304194156614467752 | 8456954308866361572 |
| MigrationLog | duration | 4553232611742008541 | 1627860264017874938 |
| MigrationLog | processedRows | 975752443473513348 | 1627860264017874938 |
| MigrationLog | totalRows | 1731857372831370262 | 1627860264017874938 |
| migrationPlan | sourceDatasourceId | 8151122576261071662 | 4796455827714164161 |
| migrationPlan | targetDatasourceId | 6620621891156590913 | 4796455827714164161 |

分布：4 个实体（MigrationLog 3、fileMigration 2、LogSchemeInformatio 2、migrationPlan 2）。9 行 `min=''`、`max=''`（空串，非 NULL）——与 B5 结论「业务字段走显式空串」一致。

## 三、口径上下文（同一查询时刻）

- 该 app BIGINTEGER 全量（含系统）= 27 行，覆盖 9 个实体
- 该 app `is_system=0` 属性 = 134；`is_system=1` = 69；合计 203
- 该 app `data_type` 分布：STRING 62 / ENTITY 35 / BIGINTEGER 27 / INTEGER 25 / DATETIME 22 / BOOLEAN 22 / CTPENUM 7 / MULTILINESTRING 3

## 四、证据等级与边界

**等级：DB（统计口径）**。本次无活体 `/service` 调用、无页面可见，按分级不构成 `LIVE`（LIVE 需活体调用 + DB 回读 + 页面可见）。

本文件只证明：目标 app 当前存在这 9 条业务 BIGINTEGER 属性及其元数据。**不证明**：设计器/页面可见、字段为本次新建、运行态可访问、值域可用。

写操作反证（auditor 独立执行）：17:35–17:55 窗口内 `udc_attribute` create/update 命中 0 行、`udc_operation_log` 命中 0 行。

DB 服务器时间戳本身不可事后独立证实；旁证：文件 mtime 17:42 与 auditor 17:44:19 的 `NOW()`（tz=+08:00）一致，不证伪、不阻塞。

## 五、修订记录

- v1：抽样 5 行、覆盖 2 个实体，标签误写 `LIVE/DB`。
- v2（本版，按 auditor VERDICT）：改全量 9 行 + 4 实体完整覆盖；等级降为 `DB`；补口径上下文与分布；补写操作反证与时间戳限定。
