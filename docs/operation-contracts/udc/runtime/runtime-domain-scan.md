# runtime 域差分扫描 — 三层扫描法 + registry 全键差分（runtime-domain-scan.md）

- 域模块: udc-runtime（运行态支撑面 = `udc-starter-runtime` 启动器 jar 的 HTTP 控制器层）
- 版本单元: 5.3.517（本地 Maven `<MAVEN_REPO>\com\seeyon`，只读离线证据；**禁混写相邻 5.3.496/5.3.345-358 单元**）
- 证据等级: VERIFIED_STATIC_BYTECODE（类名层计数 + 端点路径字面量层 133 行逐条判定 + 27 类 `javap -p -v` 全量落盘）
- 方法论: 照抄 `docs/operation-contracts/udc/bi/bi-vacuum-contract.md` 三层扫描法（L-A 类名层 / L-B 端点路径字面量层 / L-C 常量池全量层）
- 生成: implementer · 依据 main/ROUTE.md v3 §S3（HANDOFF dedupe_key `R2-handoff-v1`）
- 证据包: `docs/audit/artifacts/udc-runtime-5.3.517/`（r2_* 前缀件；同目录下 9 月旧件为本域前序会话遗留，非本轮证据，未改动）

## 0. 证据单元与复现工具链

| 项 | 值 |
|---|---|
| jar | `<MAVEN_REPO>\com\seeyon\udc-starter-runtime\5.3.517\udc-starter-runtime-5.3.517.jar` |
| 字节 | 861880 |
| jar_sha256 | `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`（main 已实测，本轮独立复测一致） |
| javap | `C:\Program Files\Java\latest\jdk-21\bin\javap.exe`（21.0.10，不在 PATH，用绝对路径） |
| javap 命令 | `javap -J-Dstdout.encoding=UTF-8 -p -v -cp <jar> <FQCN>`（**必须** `-J-Dstdout.encoding=UTF-8`，否则中文注解值乱码） |
| python 入口 | `py`（3.11.9；本机无 `python`/`python3`） |

## 1. 三层扫描（L-A / L-B / L-C）

### L-A 类名层（class-name layer）
- jar 内 `.class` 条目 346（含 `$` 内部类）；顶层类去 `$` = 307。python `zipfile` 读目录（只读，等价 `unzip -l`）。
- 控制器层定位: `com.seeyon.boot.starter.udcrt.controller.*` = **19** 类；`com.seeyon.boot.starter.udcrt.proxy.controller.*` = **11** 类。
- 其余 277 顶层类为 dto / domain.service / domain.dao / domain.entity / appservice / util / event / job / api… 非 HTTP 端点层。
- 证据件: `r2_layerA_classname_scan.json`（含逐包计数）。

### L-B 端点路径字面量层（endpoint path literal layer）
- 按常量池内映射注解描述符筛 mapping-bearing 类（`Lorg/springframework/web/bind/annotation/{RequestMapping,GetMapping,PostMapping,PutMapping,DeleteMapping,PatchMapping};`）→ **27 类**（19 `udcrt.controller` + 8 `udcrt.proxy.controller`；后者 11 类中 3 类 `NormalAppMb/NormalAppPc/NormalRefer` 无映射注解故不计）。
  - **口径警示**: 按 `@RestController` stereotype 筛类会漏 3 个无 stereotype 的具体父类（`UdcBaseGeneralController` 38 行 + `UdcReferController` 14 行 + `UdcBaseAppInfoController` 1 行，均为 `proxy.controller` 包下、无类级 `@RequestMapping`、方法级映射由子类继承生效）。
- 路径取值 = 注解 `path` / `value` **element_value 原值**（逐字不改，不补 `/`、不拼网关前缀）。自实现 JVMS 常量池 + `RuntimeVisibleAnnotations` 解析器（`r2_scan_runtime.py`）。
- 计数: 类级映射声明 **24**（`udcrt.controller` 19 + `proxy.controller` 5 有类级基路径者）；带映射成员方法 **131**；类级基路径 × 方法级路径展开端点行 **133**。
- 证据件: `r2_endpoints_raw.json`（逐类 class_level/members/pool_slash_strings + class_sha256）、`r2_endpoints_flat.json`（133 行端点表）。

### L-C 常量池全量层（constant-pool layer）
- 346 个 class 的**全部**常量池 Utf8 逐条扫描 → 38646 条 Utf8；其中以 `/` 开头或 `udc-runtime` 开头字面量 **47** distinct。
- 与 L-B 端点表比对: 仅 **3** 条字面量不在 L-B 载体中 —— `/package.json`、`/proxy/`、`/app/lock/.lock` —— **均为非端点字面量（前端构件路径 / 目录 / 锁文件）**，即**常量池层不存在端点表之外的新端点路径**（L-C 对 L-B 的完备性交叉验证 = 通过）。
- 证据件: `r2_layerC_constantpool_scan.json`。

### 三层齐备性结论
| 层 | 口径 | 覆盖量 | runtime 域判定 | 等级 |
|---|---|---|---|---|
| L-A 类名层 | 346 class FQCN（307 顶层）逐包分类 | 346 | 控制器层 = 19+8=27 mapping-bearing | VERIFIED_STATIC_BYTECODE |
| L-B 端点路径字面量层 | 27 mapping-bearing 类逐条展开 | 27 类 / 24 类级 / 131 成员 / 133 行 | 见 §2 差分 | VERIFIED_STATIC_BYTECODE（27 类 `javap -p -v` 落盘） |
| L-C 常量池全量层 | 346 类全 Utf8 | 38646 Utf8 / 47 路径型字面量 | 端点表外新增 = 0 | VERIFIED_STATIC_BYTECODE（扫描计数） |
| 交叉验证 | L-C 路径型字面量 ⊄ L-B 的差集 = 3（全非端点） | — | 完备性通过 | VERIFIED_STATIC_BYTECODE |

## 2. 差分（registry 全键）

差分规则（main R2 HANDOFF ②）: **只收 registry 全键 0 命中的只读候选**；重复形态标注去重映射不入库；写形态标注排除；分级 VERIFIED_STATIC_BYTECODE 封顶；版本仅 5.3.517。

- registry 基线: `components/platform_operations/registry.py` `UdcOperationRegistry.default()` 运行态 distinct 键 **76**，字面 `contracts["…"]=` 赋值口径 **56**（OBS-1 基线，见 §4）。
- 匹配口径: 端点路径规范化（去前导 `/` 合并重复 `/`、`{var}`→`{}` 模板化）与 registry 各 `path` 模板比对。
- 结果: **133 行 = 27 已覆盖（重复形态·去重映射）+ 106 零命中**。

### 2.1 重复形态（registry 命中 → 去重映射，不入库）—— 27 行
| 端点模板 | registry 键 |
|---|---|
| `deploy-info` | udc.appinfo.get_deploy_info |
| udc-runtime/app-draft/exist, /select | udc.application.draft.exist, /select |
| udc-runtime/app-log/datalog/{id} | udc.applog.select_by_id |
| udc-runtime/app-log/datalog/list-by-dataid/{dataId} | udc.applog.list_app_data_by_dataid, udc.applog.datalog_list_by_data_id |
| udc-runtime/app-log/datalog/search | udc.applog.search_app_data_log |
| udc-runtime/app-log/search/microflow | udc.applog.search_microflow |
| udc-runtime/app-log/search-details/microflow(+ /flowLog) | udc.applog.search_details_microflow(_flowlog) |
| udc-runtime/attachment-template/{guid}, /app/{appId}, /select-by-guids | udc.attachment.template_get_by_guid, _list_by_app_id, _list_by_guids |
| udc-runtime/custom-app/search-no-page, /search-page | udc.application.search.no_page, /page |
| udc-runtime/data/query | udc.flow.form_data_query, udc.entity_data.query_form_data |
| udc-runtime/database/query-data | udc.database.query_data |
| udc-runtime/datatype/getAll | udc.datatype.get_all |
| udc-runtime/dynamic/jar/download(+ /{appName}) | udc.jar.download, udc.jar.export_app |
| udc-runtime/meta-data/check-page-exists | udc.page_info.check_exists, udc.metadata.page_exists_check |
| udc-runtime/meta-data/select-function-node-tree/{appName} | udc.microflow.function_node_tree |
| udc-runtime/meta-data/select-host-and-only-page-pages | udc.page_info.select_host_and_only_page, udc.metadata.page_tree |
| udc-runtime/rt-page-log/search(+ /search-non-metadata) | udc.page_log.search(_non_metadata) |
| udc-runtime/serial-config/select-entity-list | udc.serial.select_entity_list, udc.serial_config.entity_list |
| udc-runtime/serial-config/select-entity-by-serial-id | udc.serial.select_entity_by_serial |
| udc-runtime/udc-role/has-system-admin/{appName} | udc.role.has_system_admin |

### 2.2 零命中（106 行）分类
| 类 | 行数 | 处置 |
|---|---|---|
| 只读候选 | 37 | 见 §2.3 → 13 入本域候选，24 移交（proxy 层，见 §3） |
| 写形态 | 50 | 标注排除（不构造契约，见 §2.4） |
| R7/R8 移交排除 | 8 | flow/microflow 透明路径，裁定勿入本域（见 §3） |
| human 裁定域排除 | 11 | page-refer 读面（见 §3） |

### 2.3 只读候选拆分（37）
- **本域只读候选 = 13**（`udcrt.controller` 层，见 §2.5）：runtime 域原生 7 + 跨域词干重叠 6。
- **proxy 层只读 = 24**（`udcrt.proxy.controller`：`UdcReferController` 14 + `UdcBaseGeneralController` 10）→ 见 §3 移交/排除，**本域只登记，不构造契约**。

### 2.4 写形态排除清单（50，仅登记）
- `udcrt.controller` 写端点: app-draft create/delete/delete-all/delete/timeout；app-log clear-org-manager / clear-runtime-data-source-cache / delete-all / enable-log/{enable} / unload-dynamic-app/{appName} / create-batch / init-tenant-data / save/front-log / update-data-init-version；attachment-template create / create-batch / delete-by-guids / delete/{guid}；attr-snapshot delete-by-data-id / delete-by-master-data-id；coli upgrade / upload/result；custom-app copy / copy-async / create / create-async / delete / new-layout-create-async / update-auth / update-caption / update-deploy-state / update-usage-state / upgrade；dynamic/jar import；rt-page-log create-batch / delete-all；serial-config cache-evict / refresh-historical-data / update；update-test update-with-fields。
- `proxy.controller` 写端点: {…}/create / create-batch / delete-by-id / delete-by-ids / update / update-batch / update-with-result / operate-root-batch / runtime-copy / export / import（`UdcBaseGeneralController`）。
- 说明: 含 GET 但写语义者（app-log clear-*/delete-all/enable-log/unload-dynamic-app、attr-snapshot delete-by-*、rt-page-log delete-all、serial-config cache-evict/refresh-historical-data）**按语义判为写形态排除**（HTTP verb 为 GET 不改其写语义）。

### 2.5 本域只读候选（13，registry 全键 0 命中）
| # | operation_id | method | path（类级+方法级原值） | 控制器#方法 |
|---|---|---|---|---|
| A1 | udc.runtime.env_check_build_info | GET | udc-runtime/evn-check/build-info/{appName} | RuntimeEnvCheckController#getBuildInfo |
| A2 | udc.runtime.env_check_app_version | GET | udc-runtime/evn-check/app-version/{appName} | RuntimeEnvCheckController#checkAppVersion |
| A3 | udc.runtime.env_check_data_permission | GET | udc-runtime/evn-check/data-permission/{entityFullName} | RuntimeEnvCheckController#checkDataPermission |
| A4 | udc.runtime.env_check_response_length | GET | udc-runtime/evn-check/response-length/{length} | RuntimeEnvCheckController#checkResponseLength |
| A5 | udc.runtime.env_check_request_content | POST | udc-runtime/evn-check/request-content | RuntimeEnvCheckController#checkRequestContent |
| A6 | udc.runtime.function_support_calculate | POST | udc-runtime/function-support/calculate | FrontFunctionSupportController#selectListByEntityName |
| A7 | udc.runtime.graphql_proxy_graphql | POST | udc-runtime/graphql-proxy/graphql | GraphqlProxyController#doGraphql |
| B1 | udc.applog.search_dataflow | POST | udc-runtime/app-log/search/dataflow | UdcAppLogController#searchDataFlow |
| B2 | udc.applog.search_dataflow_details | POST | udc-runtime/app-log/search-details/dataflow | UdcAppLogController#searchDataFlowDetails |
| B3 | udc.applog.search_deduction | POST | udc-runtime/app-log/search/deduction | UdcAppLogController#searchDeduction |
| B4 | udc.applog.search_deduction_details | POST | udc-runtime/app-log/search-details/deduction | UdcAppLogController#searchDeductionDetails |
| B5 | udc.serial.config_list | POST | udc-runtime/serial-config/list | UdcSerialConfigController#selectListByConditions |
| B6 | udc.runtime.jar_import_status | GET | udc-runtime/dynamic/jar/import/status/{requestId} | DynamicJarController#getRequestStatus |

- A 组（7）= runtime 域原生面（环境检查 / 前端函数支持 / GraphQL 代理），无既有概念域词干覆盖。
- B 组（6）= 只读 0 命中但落在既有概念域词干（`app-log`/`serial-config`/`jar`）→ operation_id 域段交 MERGE 统一（本文件按概念域给 `udc.applog.*`/`udc.serial.*`/`udc.runtime.*`）。
- 逐条 0 命中证明: `r2_registry_key_check.txt`（operation_id 与 path 模板对 registry.py grep = 0）。
- 全字段构造见 `docs/operation-contracts/udc/runtime/registry-entries.md`。

## 3. 域边界与移交/排除（本域不构造契约，仅登记）

### 3.1 R7/R8 移交项（flow/registry-entries.md L227④）—— 8 行排除
`com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseGeneralController`（runtime/proxy，无类级 `@RequestMapping`）proxy 层 flow/microflow 透明路径 = `{…}/create-bpm` / `{…}/update-bpm`（写侧） + `dataflow/{entityName}/{restMappingName}` / `…/dynamic/select` + `microflow/{microFlowName}` / `host/microflow/{microFlowName}`。主任务裁定**不扩流程域边界**、MERGE 时与微流程域合并裁定该 proxy controller、**勿入本域只读契约**。→ R2 已遵守: 上述 8 行**未作为 runtime 域只读契约落库**（仅登记于 `r2_classified.json` r7r8 桶）。

### 3.2 page-refer 读面 —— 11 行排除（human 裁定域）
`page-refer/{entityAppName}/{entityName}/{referGuid}...`（`UdcBaseGeneralController` 的 4Refer/selectTree 族）。**page refer 条目 6/7/8 = human 裁定域 → 本批零触碰**（禁改面）。

### 3.3 proxy 动态实体读面 —— 24 行（移交，本域仅登记）
`udcrt.proxy.controller` 的只读动态 REST 读面（`UdcReferController` 14 + `UdcBaseGeneralController` 10：cascade/tree/filter 族）。
- 归属依据: ① R7/R8④ 裁定该 proxy controller **与微流程域合并裁定**（勿入本域只读契约的口径延伸）；② 该类族中的 `get-cascade-default-value` 已在 **page 域**条目 5（C5，status=UNKNOWN）登记；③ `UdcReferController` 的 refer 读面已在 **page 域**条目 6/7/8 登记（base UNRESOLVED-in-5.3.517）。
- 按此，proxy 层动态 REST 读面**整体不在 runtime 域构造只读契约**（登记于 `r2_classified.json` read 桶中的 proxy 段，交 MERGE 与 page/entity/微流程域合并裁定）。**如 main 认为其中某子集应扩入本域，请另开 HANDOFF 明示**。

### 3.4 版本族隔离
本文件全部计数/字节码 sha256/路径绑定 `udc-starter-runtime` 5.3 族 **5.3.517** 单一构件；跨版本族（5.3.496 test2 镜像 / 5.3.345-358 相邻旧版）**不得复用本判定**。

## 4. 计数口径（OBS-1 基线，与 R1/REPORT 一致）
- **字面 contracts 口径**: `contracts["…"]=` 赋值条数 —— 基线 56（R1 落库后）。
- **运行态 distinct 键口径**: `UdcOperationRegistry.default()` 运行后 `len(_contracts)` —— 基线 **76**（specs 循环 20 键未被字面赋值口径覆盖）。
- 本域差分**按运行态 distinct 键口径**（76 全键）做 0 命中判定；13 只读候选在两口径下 net delta 均为 **+13**（不与任何既有键冲突；B 组 operation_id 若改域段亦 0 冲突）。

## 5. 证据件清单（`docs/audit/artifacts/udc-runtime-5.3.517/`）
- 三层: `r2_layerA_classname_scan.json` / `r2_endpoints_raw.json` + `r2_endpoints_flat.json`（L-B）/ `r2_layerC_constantpool_scan.json`
- 差分: `r2_diff.json` / `r2_classified.json` / `r2_candidates.json` / `r2_registry_key_check.txt` / `r2_summary.json`
- provenance: `r2_javap_manifest.json` + 27 个 `r2-<Class>.javap.txt`（每件头含 source_jar / jar_sha256 / class_fqcn / class_entry / class_sha256 / class_bytes / command / exit_code / run_at_utc / evidence_level 五元组+）
- 可复跑脚本: `r2_scan_runtime.py` / `r2_flatten.py` / `r2_diff.py` / `r2_classify.py` / `r2_layerAC.py` / `r2_javap_dump.py` / `r2_sig.py` / `r2_verify.py` / `r2_report.py`（sha256 见 `r2_staged_manifest.json`）
