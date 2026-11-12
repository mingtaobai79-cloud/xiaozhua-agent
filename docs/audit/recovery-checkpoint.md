# 2小爪 Agent 恢复检查点

> ✅ **P6 裁决（2026-11-07）：保留原地，不移动、不删除。**
> 本文件是 2026-09-03 的恢复检查点（当时任务上下文），**仍被程序读取**：
> `tests/fixtures/udc-audit/manifest.json` 的 `source_documents` 列有本文件名（2026-11-07 实测确认，
> 另两份是 `udc-evidence-consistency-audit.md`、`next-direction-input.md`），
> `components/evidence_bundle.py` 读该 manifest 做证据包校验。
> ⇒ 要动本文件，必须同步改 fixture manifest 与相关测试。上级登记见 `docs/audit/README.md` §六。

更新时间：2026-09-03（由当前会话重新核对）

## 当前真实任务

当前主线不是开票测试，而是 `<SEEYON_AGENT_ROOT>` 的 UDC/Seeyon Agent 审计、事实边界和 Profile 架构整理。

目标是建立并保持四类独立对象：UDC Platform、Standard Product Application、Customer UDC Application、Extension Service。

禁止把标品应用嵌入 UDC；禁止把本地 Maven 缓存存在当作线上标品事实；静态证据不得升级为 LIVE。

## 上下文恢复结论

此前已确定：不再进行无边界的 UDC 全量静态扫描。后续只做：

1. 对客户生成应用源码做定向边界扫描；
2. 对 test2 做只读动态取证；
3. 在证据充分后，另行确认最小真实写入闭环；发布和部署必须单独授权。

优先补充真实前端 Network/GraphQL body、保存后的数据库和运行时 metadata 回读、发布/生成/部署状态机、frontend artifact 与 OSS/Ingress 关系、版本组合关系，以及必要的 Redis pattern。所有结果区分 FACT、OBSERVATION、UNVERIFIED、BLOCKED、LIVE。

## 当前工作区实测状态

核对目录：`<SEEYON_AGENT_ROOT>`

已存在：

- `components/profiles/__init__.py`：仅有四类 Profile 的最小模型；未发现 `builder.py`。
- `components/profile_graph.py`：已存在，约 174 行。
- `components/udc/component.py`：已存在，约 65 行。
- `seeyon_cli.py`：已存在，约 228 行。
- `docs/audit/code-reality-audit.md`
- `docs/audit/udc-evidence-consistency-audit.md`
- `docs/audit/next-direction-input.md`

本次通过 Python Path 核对以上文件时均存在；Hermes 的 read_file 对该 D: 路径返回过 File not found，属于当前工具路径读取异常，不能据此认定文件丢失。

## 当前测试实测

在当前工作区运行 `python -m pytest -q`：

- 194 passed
- 22 failed
- 退出码 1

失败集中在两类：

1. `<USER_HOME>/... 中当前可读取的 UDC 审计证据不完整，导致 catalog/platform/domain 相关测试从预期 FACT 降为 UNVERIFIED，证据文件数为 3 而测试预期至少 8；
2. 文档中的旧测试计数为 211，但当前收集数为 216，导致文档契约测试失败。

历史摘要中的 195 passed 或 59 passed 不能代替当前状态；当前可靠基线以本次真实运行结果为准。

## 子 agent 状态

此前多批子 agent 曾出现 600 秒超时或 API 连接/HTTP 500。没有完成摘要或没有可验证落盘时，一律按 BLOCKED/UNVERIFIED 处理，不能采信口头完成。

当前确认的落盘成果只有上面列出的 Profile 最小模型、Profile Graph/CLI 和既有 UDC 组件；Profile Builder、完整 UDC Platform Profile 整合及 Pod→Image→JAR→Controller 链路仍不能宣布完成，需以文件和测试重新核验。

## 下一步硬边界

先做工作区与证据文件的定向核对，再修复当前测试/证据装载问题；不要继续泛化 Provider、不要重做无边界扫描、不要连接 test2 写接口、不要创建应用、不要改数据库/Redis、不要发布或部署。任何外部写操作都必须另行确认并做精确回读。


## 2026-09-04 Entity CRUD continuation

- Frontend module `64527` statically maps `createEntity` to `udcEntityPost` / `udcEntityPostInputBody` / `body`, with `{...payload, appId: currentAppId}`.
- Frontend module `64527` statically maps `updateEntity` to `udcEntityUpdatePost` / `udcEntityUpdatePostInputBody` / `body`, with `{...payload, appId: currentAppId}`.
- Frontend module `64527` statically maps list/detail reads to `udcEntitySelectAllByAppidAppGet` and `udcEntityGet`; detail selection includes `tableName` and nested attributes.
- Targeted facade bytecode confirms `EntityAppService.create(SingleRequest<EntityDto>)`, `update(SingleRequest<EntityDto>)`, and read methods.
- `ApplicationManagerAppService.createEntity` is a default no-op-like interface method returning `SingleResponse.ok()` in the decompile; it is not persistence evidence.
- Concrete resolver/controller/service/persistence/generation/runtime linkage remains UNVERIFIED.
- Evidence: `docs/audit/frontend/entity-api-module-64527-evidence.md`（**客户场景证据，已迁出至 `seeyon-customer-evidence/frontend/`**，仓库内已无此路径）, `docs/audit/entity-backend-static-chain-evidence.md`.


## 2026-09-04 metadata artifact continuation

- Local Maven repository contains `boot-starter-metadata-5.3.358.jar` (SHA-256 `926c28022df0502bfd988df0cf31417fb70e0603af3d39df98015e65a7028431`).
- Bytecode confirms `MetadataModifyAppService.modifyEntityAttribute(EntityAttributeModifyDto)` and `coverAllModifyEntityAttribute(List<EntityAttributeModifyDto>)` delegate to `MetadataService`.
- Bytecode references confirm entity metadata type, RedisTemplate/cache, FileService, storage keys, MD5 keys, metadata create/select/remove and change propagation methods.
- This advances the generic metadata subsystem to VERIFIED_STATIC_BYTECODE, but does not link `udcEntityPost` to this subsystem; UDC GraphQL resolver and concrete EntityAppService implementation remain UNVERIFIED.
- Evidence: `docs/audit/metadata-artifact-5.3.358-evidence.md`.


## 2026-09-04 extmetadata Entity read-chain continuation

- Local Maven repository contains `boot-starter-extmetadata-5.3.318.jar` (SHA-256 `14e1c96ed59827b3672cd809a3d08139578de9f727efb19cc03ba118a1cbee11`).
- Bytecode confirms `UdcMetaDataController → UdcMetaDataAppV2Service → UdcEntityMetaDataService → MetadataQueryAppService`.
- Entity reads use `EntityMetadataDto` / `AggEntityMetadataDto` and convert through `MetadataConvertUtil` into `UdcEntityMetaDataDto` / `UdcAttributeMetaDataDto`; attribute conversion consumes `EntityAttributeMetadataDto`.
- REST operation names include `select-entity`, `select-all-entity-by-app-name/{appName}`, and aggregation routes.
- This closes the UDC extmetadata Entity read composition at VERIFIED_STATIC_BYTECODE. It does not yet link GraphQL `udcEntityGet` or `udcEntityPost` to these routes, and does not prove Entity write persistence/generation.
- Evidence: `docs/audit/extmetadata-entity-read-chain-evidence.md`.


## 2026-09-04 runtime proxy and generated Entity consumer continuation

- Target runtime artifact: `udc-starter-runtime-5.3.517.jar`, SHA-256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`.
- `GraphqlProxyController.doGraphql` delegates to `GraphqlProxyAppServiceImpl.doGraphQL`, which serializes `GraphqlProxyRequestDto` and posts to `http://127.0.0.1:<httpPort>/graphql-app/<appName>/graphql`, propagating user/org/tenant/trace/language context.
- `GraphqlProxyRequestDto` contract: appName, appType(default FORM), query, operationName, variables.
- Generated Entity runtime path: `UdcProxyEntityAppService.selectById/selectByIds → UdcProxyAppServiceComponent.proxyEntityAppServiceMethod → FormHandler.getClass/getBeanObject → reflective method(SingleRequest) invocation`.
- `EntityAppServiceInvokeService` resolves generated AppService metadata via `MetadataQueryAppService.selectAppServiceMetadataByFullName`, selects method metadata by suffix, deserializes its parameter item type, and invokes the generated bean.
- `udc-common 5.3.517` EntityDto contract extracted; SHA-256 `30085724949703b1c2f96a37e72813a6ed9e7b752ebc206c7a47d26afceb30d7`.
- This verifies runtime consumption of generated Entity app services and GraphQL proxy transport, but not design-time `udcEntityPost → create → generation/persistence`.
- Evidence: `docs/audit/entity-runtime-proxy-and-generated-consumer-evidence.md`.


## 2026-09-04 runtime/deployment boundary continuation

- 5.3.517 runtime scan found no concrete `EntityAppServiceImpl`, `MetadataCreateAppService`, or obvious code-generator class in `udc-starter-runtime`; its role is runtime consumption, proxying, application registry, and deployment/cache events.
- `CustomApplicationService.create/createBatch → CustomApplicationDao.createBatch → CustomApplicationCreateEvent` is a verified custom-application registry path, not Entity metadata persistence.
- `AppLoadEventListener.onCompleteLoad(AppInfoDto) → StringRedisTemplate.convertAndSend` publishes appName/appVersion/traceId; `onUnLoad` clears `EntityRelationHandler` cache.
- Evidence: `docs/audit/entity-runtime-deployment-boundary-evidence.md`.


## 2026-09-04 Entity Metadata write-contract continuation

- `MetadataCreateAppService.createAllEntityMetadata(SingleRequest<ServiceEntityMetadataDto>)` calls `MetadataService.createMetadata(MetadataTypeEnum.Entity, appName, appVersion, metadatas, booleanFlag)`.
- `createAllAppServiceMetadata` uses the same primitive with `MetadataTypeEnum.AppService`, proving the two metadata families are separate typed writes.
- `MetadataModifyAppService.modifyEntityAttribute` and `coverAllModifyEntityAttribute` are separate attribute-update contracts.
- Evidence: `docs/audit/entity-metadata-write-contract-evidence.md`.


## 2026-09-04 Entity Metadata storage continuation

- `MetadataService.createMetadata(Entity, appName, appVersion, metadatas, flags)` computes metadata/MD5 keys, updates Redis value/hash state, computes `MetadataMD5Utils.dataMd5(metadatas)`, calls `onChange`, creates multi-version metadata, and synchronizes storage through `syncSave2Storage`.
- Entity attribute modification persists an app-scoped modification map through `syncSave2Storage` and Redis hash/expiry; batch replacement removes the modification key after synchronization.
- Exact physical storage provider and caller from `udcEntityPost` remain unverified.
- Evidence: `docs/audit/entity-metadata-storage-evidence.md`.


## 2026-09-04 design-time Artifact availability continuation

- Parsed `udc-parent-5.3.517.pom`: `udc.version=5.3.517`, `boot-extend.version=5.3.318`; requested `udc-biz`, `udc-web`, `udc-assemble`, `udc-cicd`, `udc-upgrade`, `udc-extend`, `udc-starter-autocode` all resolve to `com.seeyon:<artifact>:5.3.517`.
- Physical repository checks found no real requested JARs in `<MAVEN_REPO>`, `<EVIDENCE_ROOT>`, Desktop, or Downloads. Matching Temp files are pytest fixtures and excluded.
- Same-version available UDC artifacts remain common/facade/runtime/lowcode/dataflow/customplan.
- Design-time implementation and autocode artifacts are `BLOCKED / UNVERIFIED`.
- Evidence: `docs/audit/udc-design-artifact-availability-evidence.md`.


## 2026-09-04 generated source artifact discovery

- Targeted local filesystem scan found `<USER_HOME>/...com_seeyon_9000000000000000001_dto_HetongdanganDto.java`.
- This is a real generated-source delivery artifact, but its producer, generation trigger, compile/package step, and relation to `udcEntityPost` remain unverified. It is not treated as a UDC design-time module Artifact.
- Docker CLI probe was blocked by the local terminal backend path/WSL wrapper failure (`cd /c/Users/10514` unavailable); no Docker evidence is claimed.
