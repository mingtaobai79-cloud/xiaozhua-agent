# UDC 运行态存储层（LIVE：Redis + MySQL）

**证据**：udc pod（`udc-7cbfc587f5-*`）netstat 实证连接
- Redis `10.0.0.1:6379`（阿里云 rds：`r-2zertbiuu892wf8jid.redis.rds.aliyuncs.com`）
- MySQL `10.0.0.1:3306`（阿里云 rds）
- 配置源：**Nacos**（`NACOS_ADDR=mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848`，tenant `xiaozhua-test2`）

## 1. Redis key 模式（LIVE scan 实证，db0 共 ~15815 key）

| 模式 | 例 | 语义 |
| --- | --- | --- |
| `{env}:Metadata:JSON:MD5:{appName}:udc@{EntityClass}@{TYPE}@{id}.json` | `test2:Metadata:JSON:MD5:app9000000000000000001:udc@com.seeyon.udc.page.domain.entity.PageSchemaEntity@PAGE@-786727548396484538.json` | **元数据缓存失效戳**（值是版本戳如 `"1.0.11222-20261014181248"`，非全量内容） |
| `{env}:{tenantId}:{component}:{version}:CtpEnumCodeLocal::{appId}#{enumName}#{bool}` | `test2:-8112660841495312922:udc:5.3.517:CtpEnumCodeLocal::8704025620829192834#shifoutuisong#true` | 枚举 code 本地缓存（值 `["java.lang.Long",1791986471198]`） |
| `{env}:udc:app:sandbox:deploy-info:{appName}` | `test2:udc:app:sandbox:deploy-info:datamigration9000000000000000001` | 沙箱部署信息 |
| `{env}:udc:{version}:dubbo:log::{date}` | `test2:udc:5.3.517:dubbo:log::2026-10-13` | dubbo 调用日志 |
| `{env}:udc::dataChange` | — | 数据变更标记 |
| `{env}:i18n:{策略}V1:{appName}/entity-metadata` | `test2:i18n:BundleRelation_V1:bpm/entity-metadata` | 实体元数据 i18n bundle |

**覆盖实体**：`PageSchemaEntity@PAGE@*`、`MicroFlowEntity@FRONTEND@*`、`PageActionEntityDataSource@*`、
`ParamRuntimeDataSource@*`、`CtpParameterDefinitionDto`。

**★运行态读路径结论**：Redis 的 `Metadata:JSON:MD5:*` 是**元数据缓存（失效戳机制）**——
不是全量元数据正文，正文在**发布镜像/OSS**（见 `PRESET-TEMPLATE`/发布流程）。
`CtpEnumCodeLocal` 是枚举运行态 code 缓存。

## 2. MySQL 交互表（99 张，`udc_test2` schema）
见 `INTERACTION-TABLES-MAP.md`：
- **设计态** `udc_*`（81 张）：`udc_application`/`udc_entity`/`udc_attribute`/`udc_page_info`/`udc_page_schema`/
  `udc_function_node`/`udc_microflow_info`/`udc_enum`/`udc_filter_plan` 等（元数据权威源）。
- **运行态** `udc_rt_*`（18 张）+ `udc_filter_plan_formal`/`udc_filter_plan_rt`/`udc_affair_register*`：
  发布后运行路径日志/映射/筛选方案。

## 3. 元数据三层存储链
```
设计态（前端设计器）
  → MySQL udc_test2.udc_* （权威源，事务写）
  → 发布 → 生成发布镜像 + 写 Redis Metadata:JSON:MD5:*(失效戳)  
  → 运行态读：Redis 缓存（180h TTL 语义）→ OSS 发布镜像（miss 时）
```
- 版本戳格式 `1.0.{seq}-{yyyyMMddHHmmss}`（每次写元数据刷新，触发缓存失效）
- 枚举走 `CtpEnumCodeLocal`（按 appId#enumName 缓存，值 = Long id + 时间戳）

## 4. 配置源
运行态配置（Redis/MySQL/OSS 地址）来自 **Nacos**（非本地文件、非 K8s env）：
- 读法：`python scripts/conn.py nacos <dataId> [--group=G] [--tenant=T]`（tenant=`xiaozhua-test2`，group=`xiaozhua`）
- 本地只保留连接*引导*信息（`.env` 的 NACOS_ADDR/USERNAME/PASSWORD + `config/environments.yaml`）
