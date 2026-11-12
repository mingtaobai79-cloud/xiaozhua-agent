# UDC 审计 JSON 一致性与证据口径核对

- 核对范围：`<USER_HOME>/... 中现有 UDC/版本审计 JSON；本次仅读取本地文件，未执行网络写操作。
- 目标结论：**PARTIALLY VERIFIED / WITH UNVERIFIED GAPS**。

## 1. 文件存在性与 JSON 可解析性

### 1.1 目标审计目录

- `<SEEYON_AGENT_ROOT>\docs\audit` 在核对时不存在；本报告由任务要求创建。
- 本地事实文件实际位于 `<USER_HOME>/...

### 1.2 已发现的 UDC JSON

共发现 24 个文件名包含 `udc` 的 JSON 文件，全部可用 UTF-8/UTF-8 BOM 解析为 JSON（无解析失败）。代表性文件包括：

`seeyon_udc_5.3.517_class_index.json`、`seeyon_udc_scan_parent.json`、`udc_5_3_517_core_chain_audit.json`、`udc_5_3_517_module_audit.json`、`udc_controller_service_edges.json`、`udc_deployment_artifacts_audit.json`、`udc_dynamic_contract_gap_catalog.json`、`udc_frontend_chunks_audit.json`、`udc_frontend_core_api_mapping.json`、`udc_frontend_design_api_mapping.json`、`udc_frontend_static_source_gap.json`、`udc_front_back_chain_audit.json`、`udc_member_version_diff*.json`、`udc_runtime_side_effect_catalog.json`、`udc_service_persistence_audit*.json`、`udc_version_compatibility_catalog.json`、`udc_version_samples_manifest.json`、`udc_web_controller_contracts.json` 等。

## 2. 关键计数一致性

### 2.1 5.3.517 模块/JAR汇总

`udc_5_3_517_module_audit.json` 的 8 个 JAR `class_count` 合计 **3,482**，与 `summary.total_classes_all_jars=3,482` 一致。`domain_class_count=3,422` 与域包计数 2,936 + 140 + 346 = **3,422** 一致；`priority_counts` 3,385 + 36 + 1 = **3,422**，也一致。

8 个 JAR 的 class/entry 计数为：udc-common 530/460、udc-facade 94/66、udc-biz 3,383/2,312、udc-app-common 39/15、udc-extend 143/84、udc-starter-lowcode 179/141、udc-starter-runtime 472/346、udc-starter-autocode 99/58（格式为 entry_count/class_count）。

### 2.2 Controller/Endpoint

`udc_controller_service_edges.json` 与 `udc_web_controller_contracts.json` 均为 `controller_count=54`、数量 672（前者为 `controller_edge_count`，后者为 `endpoint_count`），一致。672 是静态 contract/edge 提取数量，不是线上实际成功调用数量。

### 2.3 前端资源与 API 映射

- 前端资源：discovered 34、ok 19、failed 15；19 + 15 = **34**。
- suspicious resource count 25 是独立筛选计数，不应与 failed 相加。
- API 映射：raw loader calls 37、unique calls 36；fact_backend_matches 16 + unverified_backend_matches 20 = **36**。

### 2.4 口径边界

`selected_count=25` 是静态选取/审计记录数，不是数据库表数、运行时写入数或成功调用数。版本差异中的 class/resource/member 计数是样本 JAR 的静态比较，不是运行行为。未发现上述关键计数的算术矛盾，但必须避免混用 entry_count、class_count、domain_class_count、endpoint_count 和 unique_calls。

## 3. 5.3.496 / 5.3.517 版本证据口径

### 3.1 5.3.496

5.3.496 仅出现在 `seeyon_artifactory_inventory.json` 的多个 artifact 可用版本列表中；它不在 `udc_version_samples_manifest.json` 的六个实际样本（3.8.227、3.12.124、5.3.314、5.3.380、5.3.477、5.3.517）中，也不在两个 member diff 或 compatibility catalog 的样本版本中。因此 5.3.496 当前只能标为 **OBSERVATION（inventory 中观察到版本可用）**，不能标为该版本类/方法/行为的 FACT，不能据此生成与 5.3.517 的差异结论。

### 3.2 5.3.517

5.3.517 有本地实际样本、JAR 路径和 SHA-256，可将对应本地 artifact/JAR/反编译内容标为 **FACT**。但运行行为、线上请求成功、OSS 映射、完整 DTO 契约、Redis key/TTL、发布副作用等，不能因静态 JAR 或前端文字出现而自动升级为 FACT。compatibility catalog 的稳定性仅是六个已采样版本的字节码成员/资源静态比较，不证明行为或 wire/API 兼容性。

### 3.3 禁止误报

不要把版本号出现在清单/URL/文件名写成运行态已验证；不要把 5.3.517 静态事实扩展到 5.3.496；不要把候选匹配、命名推断、相邻版本观察写为 FACT；不要把单客户部署 artifact 当作全部客户或全部 5.3 的统一事实。

## 4. 未验证项保留情况

未验证项总体保留良好：

- `udc_dynamic_contract_gap_catalog.json` 保留顶层 `FACT+UNVERIFIED` 和 `unverified_dto_gaps`（EntityDto、AttributeDto、PageInfoDto、MicroFlowDefinitionDto、DataFlowDto 等）。
- `udc_frontend_core_api_mapping.json` 保留 16 个 FACT backend matches、20 个 UNVERIFIED matches。
- `udc_frontend_design_api_mapping.json` 保留 DTO/input member、schema/introspection 和启发式匹配缺口。
- `udc_frontend_static_source_gap.json` 保留 OSS bucket/endpoint/object key、Ingress 原始配置、线上字节一致性、上传/解压时机、线上 URL/缓存策略等未验证项。
- `udc_deployment_artifacts_audit.json` 明确 `static_resource_source` 为 UNVERIFIED at byte/content level。
- `udc_front_back_chain_audit.json` 为 `PARTIALLY VERIFIED`，保留前端源码、文档正文和 JAR 路径/版本/SHA-256 限制。
- `udc_5_3_517_module_audit.json` 保留 `MicroFlowDependencyAnalyser` targeted decompile missing。
- `udc_runtime_side_effect_catalog.json` 对缺失 key prefix/TTL/event/executor/call edge 保留空证据，不作否定推断。

## 5. 审计结论与建议

**结论：PASS（格式与主要计数）/ BLOCKED（5.3.496 实证）/ UNVERIFIED（运行态及动态契约部分）。**

1. 现有 UDC JSON 均可解析，主要内部计数可相互对上。
2. 5.3.496 必须降级为 OBSERVATION，不得标记为版本实现 FACT。
3. 5.3.517 的 FACT 必须携带 `artifact + version + sha256` 边界。
4. 后续编辑不得删除 `unverified_*`、`limitations`、`evidence_limits` 或把混合状态简化成纯 FACT。
5. 若需形成 5.3.496 与 5.3.517 的版本差异事实，先取得 5.3.496 实际 JAR、版本和 SHA-256，再按同一规则重新生成证据。
