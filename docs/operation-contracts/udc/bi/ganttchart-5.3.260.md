# UDC · BI 域 · boot-starter-ganttchart **5.3.260** 只读契约（独立版本单元）

- **版本单元**: 5.3.260。本文件所有证据**仅适用 5.3.260**；与 `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`（5.3.517 单元，判定 = VACUUM，维持不变）是两个物理分开的证据单元，**禁混写、禁互相推论**。
- 授权链: HUMAN 2026-10-08 13:56 裁定（会话 inbox `evt-1791439622729-37732`）→ main ROUTE R7（§2 隔离红线）→ 本件为其唯一动作产出。
- 域定义口径（依 HUMAN 裁定）: 图表/甘特图类可视化构件**计入 BI 域**。
- jar: `<MAVEN_REPO>/com/seeyon/boot-starter-ganttchart/5.3.260/boot-starter-ganttchart-5.3.260.jar`（size 272340 B，jar_sha256 `a98863787e97733ea38c2bd57904b4a86dd2db6ada07c968445ac191b2acdbde`，jar_sha1 `0888ce459d30d3198c257aa97a096122bd65c6de` = 侧车 `.sha1` 内容）
- 扫描面: zipfile 只读 → 条目 101 / .class **50** / `sources` 条目 **0**；按**映射注解描述符**筛（非 `@RestController` stereotype）→ mapping-bearing **2 类**。
- 端点行 **16**（全部方法级）+ 类级基路径 **2** 条 = 映射注解共 **18** 条；其中**只读形态候选 = 5 条**（下逐条 7 要素），写形态 9 条（本轮不落契约），`exportWbs`/`print` 副作用未确证 2 条（不落契约）。
- 双口径互证: 常量池/注解属性解析 vs `javap -p -v` 解码文本，路径逐条比对 **mismatch = 0**。
- 证据等级: 路径/方法/参数注解/返回类型 = **VERIFIED_STATIC_BYTECODE**；类名与 `RestApiOperation` 中文标注的语义归因 = **OBSERVATION**；**运行时行为一律不写**。
- 工具链: `C:/Program Files/Java/latest/jdk-21/bin/javap.exe` = 21.0.10，命令 `javap -J-Dstdout.encoding=UTF-8 -p -v -cp <jar> <FQCN>`。

## 契约条目（7 要素齐备，write=False）

### 1. `udc.bi.ganttchart_running_dynamic_select_by_entity`
| 要素 | 值 |
|---|---|
| operation_id | `udc.bi.ganttchart_running_dynamic_select_by_entity` |
| HTTP method | **POST**（注解 `PostMapping` 隐含，无显式 `method` 元素；注: 本域只读候选含 POST，与 `registry.py:55-58` 既有 `udc.page_log.search`=POST+write=False 同风格） |
| 控制器原路径 | 类级 = `gantt-chart`；方法级 = `dynamic-select-by-entity`；拼接原值 = `gantt-chart/dynamic-select-by-entity`（**未拼任何网关前缀**，`/` 兜底见下方纪律） |
| 参数形态 | 形参注解 = p0:RequestBody；描述符 `(Lcom/seeyon/boot/transport/ListRequest;)Lcom/seeyon/boot/transport/ListResponse;`；泛型签名 `Signature: #59                          // (Lcom/seeyon/boot/transport/ListRequest;)Lcom/seeyon/boot/transport/ListResponse<Ljava/lang/Object;>;` |
| 返回 DTO | `ListResponse<java.lang.Object>` |
| evidence | artifact=`boot-starter-ganttchart-5.3.260.jar` / **version=`5.3.260`** / class=`com.seeyon.boot.starter.ganttchart.controller.GanttChartRunningController` / method=`dynamicSelectByEntity` / class_sha256=`8d43516d96edfb6c38ef7a9c8a5cdb1e00c9cdf03a8be47d2025b84ff0176f84` / javap=`docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartRunningController.javap.txt` / level=`VERIFIED_STATIC_BYTECODE` |
| 语义归因(OBSERVATION) | `RestApiOperation` 中文 value = `查询甘特图数据`；类名含 `GanttChart` → 依 HUMAN 口径计入 BI 域。**归因级，非字节码结论** |

**LIVE 回读条件（本轮不做，仅写清需要什么）**: ① 网关到 ganttchart starter 的 service 路由前缀（离线不可确证，**禁在此拼**）；② 一套已启用的甘特图方案样本（含已知 `code` 与 `id`）；③ 通过认证的 V8 会话凭据 + 目标环境入口；④ 回读判据 = 同 `code`/同 `id` 二次请求 `identity_matches`、响应 envelope 为 `SUCCESS` 且 DTO 列表/对象非空；⑤ POST+`@MultiRequestBody`/`@RequestBody` 的传参约定需 LIVE 首验。

### 2. `udc.bi.ganttchart_schema_select_by_id`
| 要素 | 值 |
|---|---|
| operation_id | `udc.bi.ganttchart_schema_select_by_id` |
| HTTP method | **POST**（注解 `PostMapping` 隐含，无显式 `method` 元素；注: 本域只读候选含 POST，与 `registry.py:55-58` 既有 `udc.page_log.search`=POST+write=False 同风格） |
| 控制器原路径 | 类级 = `gantt-chart-schema`；方法级 = `select-by-id`；拼接原值 = `gantt-chart-schema/select-by-id`（**未拼任何网关前缀**，`/` 兜底见下方纪律） |
| 参数形态 | 形参注解 = p0:MultiRequestBody；描述符 `(Ljava/lang/Long;)Lcom/seeyon/boot/transport/SingleResponse;`；泛型签名 `Signature: #85                          // (Ljava/lang/Long;)Lcom/seeyon/boot/transport/SingleResponse<Lcom/seeyon/boot/starter/ganttchart/dto/setting/GanttChartSchemaDto;>;` |
| 返回 DTO | `SingleResponse<setting.GanttChartSchemaDto>` |
| evidence | artifact=`boot-starter-ganttchart-5.3.260.jar` / **version=`5.3.260`** / class=`com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController` / method=`selectById` / class_sha256=`cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb` / javap=`docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt` / level=`VERIFIED_STATIC_BYTECODE` |
| 语义归因(OBSERVATION) | `RestApiOperation` 中文 value = `根据id获取方案详情`；类名含 `GanttChart` → 依 HUMAN 口径计入 BI 域。**归因级，非字节码结论** |

**LIVE 回读条件（本轮不做，仅写清需要什么）**: ① 网关到 ganttchart starter 的 service 路由前缀（离线不可确证，**禁在此拼**）；② 一套已启用的甘特图方案样本（含已知 `code` 与 `id`）；③ 通过认证的 V8 会话凭据 + 目标环境入口；④ 回读判据 = 同 `code`/同 `id` 二次请求 `identity_matches`、响应 envelope 为 `SUCCESS` 且 DTO 列表/对象非空；⑤ POST+`@MultiRequestBody`/`@RequestBody` 的传参约定需 LIVE 首验。

### 3. `udc.bi.ganttchart_schema_select_by_code`
| 要素 | 值 |
|---|---|
| operation_id | `udc.bi.ganttchart_schema_select_by_code` |
| HTTP method | **GET**（注解 `GetMapping` 隐含，无显式 `method` 元素；注: 本域只读候选含 POST，与 `registry.py:55-58` 既有 `udc.page_log.search`=POST+write=False 同风格） |
| 控制器原路径 | 类级 = `gantt-chart-schema`；方法级 = `{code}`；拼接原值 = `gantt-chart-schema/{code}`（**未拼任何网关前缀**，`/` 兜底见下方纪律） |
| 参数形态 | 形参注解 = p0:PathVariable(value="code")、p0:ParameterInfo(value="方案编码")；描述符 `(Ljava/lang/String;)Lcom/seeyon/boot/transport/SingleResponse;`；泛型签名 `Signature: #92                          // (Ljava/lang/String;)Lcom/seeyon/boot/transport/SingleResponse<Lcom/seeyon/boot/starter/ganttchart/dto/setting/GanttChartSchemaDto;>;` |
| 返回 DTO | `SingleResponse<setting.GanttChartSchemaDto>` |
| evidence | artifact=`boot-starter-ganttchart-5.3.260.jar` / **version=`5.3.260`** / class=`com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController` / method=`selectByCode` / class_sha256=`cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb` / javap=`docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt` / level=`VERIFIED_STATIC_BYTECODE` |
| 语义归因(OBSERVATION) | `RestApiOperation` 中文 value = `获取code方案详情`；类名含 `GanttChart` → 依 HUMAN 口径计入 BI 域。**归因级，非字节码结论** |

**LIVE 回读条件（本轮不做，仅写清需要什么）**: ① 网关到 ganttchart starter 的 service 路由前缀（离线不可确证，**禁在此拼**）；② 一套已启用的甘特图方案样本（含已知 `code` 与 `id`）；③ 通过认证的 V8 会话凭据 + 目标环境入口；④ 回读判据 = 同 `code`/同 `id` 二次请求 `identity_matches`、响应 envelope 为 `SUCCESS` 且 DTO 列表/对象非空；⑤ POST+`@MultiRequestBody`/`@RequestBody` 的传参约定需 LIVE 首验。

### 4. `udc.bi.ganttchart_schema_search_list`
| 要素 | 值 |
|---|---|
| operation_id | `udc.bi.ganttchart_schema_search_list` |
| HTTP method | **POST**（注解 `PostMapping` 隐含，无显式 `method` 元素；注: 本域只读候选含 POST，与 `registry.py:55-58` 既有 `udc.page_log.search`=POST+write=False 同风格） |
| 控制器原路径 | 类级 = `gantt-chart-schema`；方法级 = `search-list`；拼接原值 = `gantt-chart-schema/search-list`（**未拼任何网关前缀**，`/` 兜底见下方纪律） |
| 参数形态 | 形参注解 = p0:MultiRequestBody、p1:MultiRequestBody；描述符 `(Ljava/util/Map;Lcom/seeyon/boot/transport/Sort;)Lcom/seeyon/boot/transport/ListResponse;`；泛型签名 `Signature: #106                         // (Ljava/util/Map<Ljava/lang/String;Ljava/lang/Object;>;Lcom/seeyon/boot/transport/Sort;)Lcom/seeyon/boot/transport/ListResponse<Lcom/seeyon/boot/starter/ganttchart/dto/setting/GanttChartSchemaDto;>;` |
| 返回 DTO | `ListResponse<setting.GanttChartSchemaDto>` |
| evidence | artifact=`boot-starter-ganttchart-5.3.260.jar` / **version=`5.3.260`** / class=`com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController` / method=`selectByConditions` / class_sha256=`cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb` / javap=`docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt` / level=`VERIFIED_STATIC_BYTECODE` |
| 语义归因(OBSERVATION) | `RestApiOperation` 中文 value = `根据条件获取配置列表`；类名含 `GanttChart` → 依 HUMAN 口径计入 BI 域。**归因级，非字节码结论** |

**LIVE 回读条件（本轮不做，仅写清需要什么）**: ① 网关到 ganttchart starter 的 service 路由前缀（离线不可确证，**禁在此拼**）；② 一套已启用的甘特图方案样本（含已知 `code` 与 `id`）；③ 通过认证的 V8 会话凭据 + 目标环境入口；④ 回读判据 = 同 `code`/同 `id` 二次请求 `identity_matches`、响应 envelope 为 `SUCCESS` 且 DTO 列表/对象非空；⑤ POST+`@MultiRequestBody`/`@RequestBody` 的传参约定需 LIVE 首验。

### 5. `udc.bi.ganttchart_schema_search`
| 要素 | 值 |
|---|---|
| operation_id | `udc.bi.ganttchart_schema_search` |
| HTTP method | **POST**（注解 `PostMapping` 隐含，无显式 `method` 元素；注: 本域只读候选含 POST，与 `registry.py:55-58` 既有 `udc.page_log.search`=POST+write=False 同风格） |
| 控制器原路径 | 类级 = `gantt-chart-schema`；方法级 = `search`；拼接原值 = `gantt-chart-schema/search`（**未拼任何网关前缀**，`/` 兜底见下方纪律） |
| 参数形态 | 形参注解 = p0:MultiRequestBody、p1:MultiRequestBody、p2:MultiRequestBody；描述符 `(Lcom/seeyon/boot/transport/PageInfo;Ljava/util/Map;Lcom/seeyon/boot/transport/Sort;)Lcom/seeyon/boot/transport/PageResponse;`；泛型签名 `Signature: #113                         // (Lcom/seeyon/boot/transport/PageInfo;Ljava/util/Map<Ljava/lang/String;Ljava/lang/Object;>;Lcom/seeyon/boot/transport/Sort;)Lcom/seeyon/boot/transport/PageResponse<Lcom/seeyon/boot/starter/ganttchart/dto/setting/GanttChartSchemaDto;>;` |
| 返回 DTO | `PageResponse<setting.GanttChartSchemaDto>` |
| evidence | artifact=`boot-starter-ganttchart-5.3.260.jar` / **version=`5.3.260`** / class=`com.seeyon.boot.starter.ganttchart.controller.GanttChartSchemaController` / method=`selectPageByConditions` / class_sha256=`cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb` / javap=`docs/audit/artifacts/udc-bi-5.3.260/r7-GanttChartSchemaController.javap.txt` / level=`VERIFIED_STATIC_BYTECODE` |
| 语义归因(OBSERVATION) | `RestApiOperation` 中文 value = `根据条件获取配置分页列表`；类名含 `GanttChart` → 依 HUMAN 口径计入 BI 域。**归因级，非字节码结论** |

**LIVE 回读条件（本轮不做，仅写清需要什么）**: ① 网关到 ganttchart starter 的 service 路由前缀（离线不可确证，**禁在此拼**）；② 一套已启用的甘特图方案样本（含已知 `code` 与 `id`）；③ 通过认证的 V8 会话凭据 + 目标环境入口；④ 回读判据 = 同 `code`/同 `id` 二次请求 `identity_matches`、响应 envelope 为 `SUCCESS` 且 DTO 列表/对象非空；⑤ POST+`@MultiRequestBody`/`@RequestBody` 的传参约定需 LIVE 首验。

## 路径与分级纪律

- 所有路径为注解 `value`/`path` element_value **原值逐字抄录**；类级基路径无先导 `/`（`gantt-chart`、`gantt-chart-schema`），方法级路径亦无先导 `/`，`{code}` 为路径变量原形。
- **禁跨单元推论**: 不得由「5.3.260 有甘特图端点」推出「5.3.517 承载 BI」，也不得反向；跨版本装配关系 = HYPOTHESIS，本轮不取证。
- `boot-starter-ganttchart-5.3.260-sources.jar.lastUpdated` = Maven Resolver 拉取失败标记，依 HUMAN 裁定**原样登记、不下载、不修复、不重试**；其内部 artifactory base URL 已脱敏为 `<artifactory-host-redacted>`。
- 未触碰件: `docs/audit/artifacts/udc-bi-5.3.517/**`（64 件已入库跟踪件）、`components/platform_operations/registry.py`/`layer.py`、`seeyon_cli.py`、`tests/**`、`README.md`、`docs/audit/agent-version-audit.md`、`docs/audit/code-reality-audit.md`、其他域契约目录。

