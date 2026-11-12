# Gantt 面 5.3.260 契约读写覆盖核对（P2 / HANDOFF #2）

> 版本单元：**5.3.260**（独立单元；`bi-vacuum-contract.md` = 5.3.517 单元，两件**禁混写、禁互推**）
> 产出授权：main HANDOFF #2（dedupe_key `bi-p2-gantt-coverage`，2026-10-17T08:41:13Z）
> 上级基线（**不修改、不推翻，仅引用**）：`docs/operation-contracts/udc/bi/ganttchart-5.3.260.md`
> 本件性质：**只读覆盖核对**。不落任何写操作契约为可执行；不改既有契约判定。
> 订正记录：**r2（HANDOFF #3 / dedupe `bi-p2-verdict-fixes`）**按 auditor VERDICT（`bi-p2-gantt-coverage-review-verdict`，PARTIAL）订正 6 项——§0/(c) 结论句口径（DDL↔活体 15/15、实体↔活体 nullable 10/15）、§3.1 三方比对改为可比对脚本可复现、W4 importWbs 落库面升 STATIC 确证不落库并加业务语义口径限定、W9 补 MQ 应用条件门与执行序、saveAuditLog 补「审计上下文+日志，非直写业务表」、§2.4 及全文「落库面=UNVERIFIED」统一改「STATIC 确证不落库」。**仅订正声明措辞/限定/定级，未新增业务声明**；r7 判定与 `ganttchart-5.3.260.md` 基线未改。

- jar：`<MAVEN_REPO>/com/seeyon/boot-starter-ganttchart/5.3.260/boot-starter-ganttchart-5.3.260.jar`
  - size 272340 B；`jar_sha256 = a98863787e97733ea38c2bd57904b4a86dd2db6ada07c968445ac191b2acdbde`（本轮实测复现，与基线一致）
- 工具链：`C:/Program Files/Java/latest/jdk-21/bin/javap.exe`（21.0.10）`javap -p -v`；`jar xf` 只读解包
- 证据目录：`docs/audit/artifacts/udc-bi-5.3.260/p2/`（javap 全文（含二轮增量 *.p2.javap.txt）+ jar 内 ddl/starter_info + DB raw json + **`three_way_compare.py` 可比对脚本与 `.out.txt` 输出**）

## 0. 结论速览（三问）

| 问 | 问题 | 定级 | 一句话结论 |
|---|---|---|---|
| (a) | 5 条只读候选是否足以支撑「读」结论 | **STATIC 完备 / LIVE 未达** | 5 条 7 要素**逐条自洽完整**（字节码可证），**5 条全部有 LIVE 缺口**，缺口同源同因（网关 service 前缀 + 有效会话），非条目级质量缺陷 |
| (b) | 9 条写形态 = 缺口还是 VACUUM | **STATIC 覆盖（非 VACUUM）、契约登记缺口** | 9 条写形态字节码**全部可补齐 7 要素**，写能力真实存在 ⇒ **不是 VACUUM**；未落契约是**登记策略缺口**（write=True 只登记不授权），非证据缺口 |
| (c) | `gantt_chart_schema` 表 ↔ schema 类端点落库对应 | **(c-1) STATIC+LIVE 双向闭合 / (c-2) 表归属 LIVE 确证** | DDL≡活体 15/15 逐列全等（列名/顺序/类型族/可空性）；实体↔活体 nullable 仅 10/15（实体 nullable 只影响 JPA 生成，建表以 ddl.sql 为准）；表由 ganttchart starter 自身 `ddl.sql` 建于**应用库**，非 UDC 域、非 cdp-bi 库 |

---

## 1. 问 (a)：5 条只读候选的 7 要素逐条核对

核对口径：7 要素 = ①method ②路径（类级+方法级原值）③参数注解 ④返回 DTO ⑤evidence ⑥语义归因 ⑦LIVE 回读条件。
判定三档：**自洽完整**（7 要素齐 · 字节码可证）／**LIVE 缺口**（①②③④⑤⑥ 成立但⑦条件不满足）／**矛盾**（要素间互斥）。

| # | operation_id | ①method | ②路径拼接原值 | ③参数注解 | ④返回 DTO | ⑤evidence | ⑥归因 | ⑦LIVE 条件 | 判定 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `udc.bi.ganttchart_running_dynamic_select_by_entity` | POST | `gantt-chart/dynamic-select-by-entity` | p0 `@RequestBody` ListRequest | `ListResponse<Object>` | class_sha256 `8d43516d…` | 查询甘特图数据 | 未达 | **自洽完整 + LIVE 缺口** |
| 2 | `udc.bi.ganttchart_schema_select_by_id` | POST | `gantt-chart-schema/select-by-id` | p0 `@MultiRequestBody` Long | `SingleResponse<GanttChartSchemaDto>` | class_sha256 `cad87965…` | 根据id获取方案详情 | 未达 | **自洽完整 + LIVE 缺口** |
| 3 | `udc.bi.ganttchart_schema_select_by_code` | GET | `gantt-chart-schema/{code}` | p0 `@PathVariable(value="code")` + `@ParameterInfo("方案编码")` | `SingleResponse<GanttChartSchemaDto>` | class_sha256 `cad87965…` | 获取code方案详情 | 未达 | **自洽完整 + LIVE 缺口** |
| 4 | `udc.bi.ganttchart_schema_search_list` | POST | `gantt-chart-schema/search-list` | p0/p1 `@MultiRequestBody`（Map, Sort） | `ListResponse<GanttChartSchemaDto>` | class_sha256 `cad87965…` | 根据条件获取配置列表 | 未达 | **自洽完整 + LIVE 缺口** |
| 5 | `udc.bi.ganttchart_schema_search` | POST | `gantt-chart-schema/search` | p0/p1/p2 `@MultiRequestBody`（PageInfo, Map, Sort） | `PageResponse<GanttChartSchemaDto>` | class_sha256 `cad87965…` | 根据条件获取配置分页列表 | 未达 | **自洽完整 + LIVE 缺口** |

### 1.1 逐条复核的原始证据（本轮独立复现，非引用基线文本）

全部 7 要素本轮从**同一 jar** 重新 javap 复现，行号可核：

- `p2/GanttChartRunningController.javap.txt:219` `dynamicSelectByEntity` → `@PostMapping(value=["dynamic-select-by-entity"])`（同文件 236–262 行注解块），`@RequestBody` 见参数注解块。
- `p2/GanttChartSchemaController.javap.txt:412` `selectById` → `@PostMapping(["select-by-id"])`；`:447` `selectByCode` → `@GetMapping(["{code}"])` + `@PathVariable(value="code")`；`:488` `selectByConditions` → `@PostMapping(["search-list"])`；`:538` `selectPageByConditions` → `@PostMapping(["search"])`（三者参数注解均 `@MultiRequestBody`）。
- 类级基路径：`GanttChartRunningController` = `@RequestMapping(["gantt-chart"])`；`GanttChartSchemaController` = `@RequestMapping(["gantt-chart-schema"])`（两文件尾 `RuntimeVisibleAnnotations`）。
- 返回 DTO 泛型签名（`Signature:` 属性逐字）：`(:412) SingleResponse<…setting.GanttChartSchemaDto>`、`(:447)` 同、`(:488) ListResponse<…setting.GanttChartSchemaDto>`、`(:538) PageResponse<…setting.GanttChartSchemaDto>`、`(:219) ListResponse<Object>`。
- **新增可信度加强（基线未记）**：16 个控制器方法**无一例外**在方法体入口即 `invokevirtual checkLicense()`（offset 0 为 `aload_0`，`checkLicense` 在 **offset 1**，其前无任何分支）；`checkLicense` 体 = `licenseProcessor.hasPlugin("ganttchart")`，false 则抛 `BOOT_3006`。
  → 证据：`p2/GanttChartRunningController.javap.txt` `checkLicense` 方法体；`p2/GanttChartSchemaController.javap.txt:637` 同构。**含义**：本面全部端点（含只读）受 ganttchart 插件授权门约束，LIVE 首验必过此门，否则拿到的是 `BOOT_3006` 而非端点语义结果。

### 1.2 「读」结论是否成立

- **STATIC 层：成立且完备。** 16 条端点中只读形态 5 条，路径/方法/参数/返回/证据链七要素无一条存在要素间矛盾；方法名→语义归因（OBSERVATION 级）与 `RestApiOperation` 中文标注一致（"查询/获取/根据条件获取"），无「名为读实为写」的双关项。
- **LIVE 层：0/5 达成。** 5 条**全部**有 LIVE 缺口，且是**同一组前置条件**未满足，不是 5 个独立缺陷：
  1. 网关到 ganttchart starter 的 service 路由前缀 = **UNVERIFIED**（本轮未取证；离线不可确证，禁拼）；
  2. 目标环境有效会话（`shared-credentials/test2-web-credential.json`，值 0 入件）；
  3. 一套已启用甘特图方案样本。
- **本轮新增的 LIVE 阻塞硬证据（把「缺条件」从假设变成事实）**：`gantt_chart_schema` 在**全库 72 个 schema 中行数合计 = 0**（§3.2）。即使前缀与会话就绪，`select-by-id` / `select-by-code` / `search-list` / `search` 四条也**必然返回空集**，无法用「非空回读」判 PASS；只有 `dynamic-select-by-entity`（走 `GanttChartUtil.invokeSelectListByConditionsDynamicMethod`，目标为 UDC 动态实体而非本表）在理论上不受此限。**⇒ 只读 LIVE 缺口严格来说是「前置数据缺口 + 路由前缀缺口」双缺，不是单一会话问题。**

**定级：(a) = STATIC 完备 / LIVE 未达（UNVERIFIED，非 BLOCKED）。** 判 UNVERIFIED 而非 BLOCKED 的理由：无外部强制阻断，缺口是待补的前置件，且已把所需输入逐项写死（§1.3）。

### 1.3 各条 LIVE 回读所需输入（可直接作为后续 LIVE 单的前置清单）

| 条目 | 前置输入 | 回读判据 |
|---|---|---|
| dynamic_select_by_entity | ①service 前缀（禁拼·需 LIVE 首验）②有效会话 ③`ListRequest.params.fullName` 指向的 **UDC 动态实体全名**（代码路径：`MapUtils.getString(params,"fullName")`，blank 即短路返回空 List —— 见 `GanttChartAppService.javap.txt:1508` 方法体） | 同 `fullName` 二次请求 `identity_matches`；`ListResponse` envelope=SUCCESS |
| schema_select_by_id | ①②+④**一行 `gantt_chart_schema` 样本行与其 `id`**（当前全库 0 行） | 同 id 二次回读 identity_matches；`SingleResponse<GanttChartSchemaDto>` 非空 |
| schema_select_by_code | ①②+④样本行的 `code` | 同上，按 `code` |
| schema_search_list | ①②+④任意样本行（条件查询） | `ListResponse` 非空；控制器已强制注入 `params["delete"]=false`（`GanttChartSchemaController.javap.txt:488` 方法体 offset 4–16），回读须带同条件 |
| schema_search | ①②+④任意样本行（分页） | `PageResponse` 的 total>0；同样受 `delete=false` 强制注入 |

补充：以上 5 条**共用** `checkLicense → hasPlugin("ganttchart")` 门（§1.1）。若环境未启该插件，LIVE 一律 `BOOT_3006`，此时应判定为「环境未授权」而非「端点不成立」——这是后续 LIVE 单必须先分清的前提。

---

## 2. 问 (b)：9 条写形态的 7 要素补齐 + 缺口定性 + 副作用消除路径

### 2.0 定性先说

- **「写」契约 = 登记缺口（write=True 仅登记不授权），不是 VACUUM。**
  依据：9 条写形态的 **7 要素全部可从字节码补齐**，且写路径在下游**闭环到真实持久化动作**（DAO `create`/`update`/`updateBatch`、UDC 动态写方法），并非"名字像写、实现是读"。VACUUM 的定义是"域内 0 条可证据化契约（完备负证据）"——本面 16 条端点俱在，9 条写形态逐条可证，**VACUUM 定义不成立**。
- **本节所有条目 `write=True`，仅登记，不授权任何写操作执行。** 本 HANDOFF 边界=只读，本轮 0 次写调用。

### 2.1 9 条写形态方法级 7 要素（同 5 条只读候选同口径）

| # | 端点（拼接原值） | method | 参数注解 | 返回 DTO | 下游落点（字节码证据） | 判定 |
|---|---|---|---|---|---|---|
| W1 | `gantt-chart/save` | POST | p0 `@RequestBody` WbsSaveDto | `SingleResponse<Long>` | `GanttChartAppService.saveProject` → `GanttChartService.saveProject(ProjectDto,GanttChartDto)`；内部经 `invokeInsertDynamicMethod` / `invokeUpdateDynamicMethod` / `invokeDeleteDynamicMethod` 写 **UDC 动态实体** | STATIC 齐 |
| W2 | `gantt-chart/copy` | POST | p0 `@RequestBody` GanttChartCopyDto | `SingleResponse<Long>` | → `GanttChartService.copyWbs(wbsCode, entityId, wbsId, GanttChartDto)` | STATIC 齐 |
| W3 | `gantt-chart/delete-by-wbsId` | POST | p0 `@RequestBody` GanttChartCopyDto | `SingleResponse<Integer>` | → `GanttChartService.deleteByWbsId(...)` | STATIC 齐 |
| W4 | `gantt-chart/import` | POST | p0 `@MultiRequestBody` String(storageKey) | `SingleResponse<Map<String,Object>>` | `FileService.download(storageKey)` → `PlusProject.Read(InputStream)` → 仅解析为 HashMap 返回；**0 DAO / 0 DynamicMethod / 0 MQ（全链追到叶子）** | STATIC 齐（落库面=**STATIC 确证不落库**，见 2.3 / 2.4） |
| W5 | `gantt-chart-schema/create` | POST | p0 `@RequestBody` GanttChartSchemaDto | `SingleResponse<Long>` | `GanttChartSchemaService.create` → `GanttChartSchemaDao.create(entity)`（`SchemaService.javap.txt:487`） | STATIC 齐 |
| W6 | `gantt-chart-schema/update` | POST | p0 `@RequestBody` GanttChartSchemaDto | `SingleResponse<Integer>` | `...Service.update` → `Dao.update` | STATIC 齐 |
| W7 | `gantt-chart-schema/copy` | POST | p0 `@MultiRequestBody` Long | `SingleResponse<Long>` | `...Service.copyById` → `Dao.selectById` → `copyName`/`copyCode` → `Dao.create`（`:808`） | STATIC 齐 |
| W8 | `gantt-chart-schema/update-active` | POST | p0 `@RequestBody` GanttChartSchemaUpdateActiveDto | `SingleResponse<Integer>` | `...Service.updateActive` → `Dao.selectByIds` → `forEach(setEnable)` → `Dao.updateBatch`（`:669`） | STATIC 齐 |
| W9 | `gantt-chart-schema/delete-by-ids` | POST | p0 `@MultiRequestBody` List&lt;Long&gt; | `SingleResponse<Integer>` | `...Service.deleteByIds` → `Dao.selectByIds` → 逻辑删（`setDelete(true)`）→ `Dao.updateBatch`；**并异步发 MQ `GanttChartDetectionMessage`（`wbs一致性检查发送udc 删除消息`），但受应用门约束**（见 2.2-5） | STATIC 齐（MQ 条件门见 2.2-5） |

### 2.2 写形态新增的机制事实（基线未记，对后续建模必要）

1. **9 条写形态同样全部过 `checkLicense()`**（§1.1）。
2. **两处写语义属于"逻辑删"而非物理删**：W9 `deleteByIds` 走 `setDelete(true)+updateBatch`；控制器侧 `search-list`/`search` 强制 `params.delete=false`，即删除后的方案在列表查询中不可见 —— 读写口径自洽（这条闭合了"读不到≠不存在"的歧义）。
3. **W8 `update-active` 只写 `is_enable`**（`lambda$updateActive$0` 仅 `setEnable(dto.getEnabled())`，`SchemaService.javap.txt` 的 synthetic lambda 段），**不触碰 `is_delete`** —— 启停用与删除是两个正交操作，建模时不得合并。
4. **W5/W7 的 `app_guid` 来源**：`create` 从 `RequestContext` 取 `userId`/`loginOrgId` 填 `create_user_id`/`create_org_id`（`:487` 方法体），而 `app_guid` 取自 DTO —— 即建方案时应用归属由**调用方入参**决定，非服务端推断。
5. **W9 的跨域副作用带应用条件门（本轮补正，字节码实证）**：删除触发 MQ 前有一道应用语境门 —— 仅当 `Apps.getAppName()` ∈ {`app-approval`, `udc`} 时才 `executorService.execute(...)` 提交异步任务发 MQ（`GanttChartSchemaService.javap.txt` deleteByIds 方法体 **offset 41–75**：41 `Apps.getAppName()` → 44 `ldc "app-approval"` → 46 `equals` → 49 `ifne 63`；52 再次 `getAppName()` → 55 `ldc "udc"` → 60 `ifeq 80` 跳过；63 `getfield executorService` → 75 `invokeinterface execute`）。
   - **执行序**：`execute` 提交（offset 63–75）**先于** `dao.updateBatch`（offset 80–85）—— 即 MQ 任务在软删落库**之前**已提交到线程池，异步任务与 `updateBatch` 无先后保证。
   - **口径限定**：该 MQ 联动**在 UDC 应用语境下成立**（业务实况即 UDC/app-approval 应用），**但作为通用契约缺条件门** —— 不得表述为「本端点恒发 MQ」。建模时按「UDC 应用语境下的有证据联动」表达，不改变模块归属。

### 2.3 `exportWbs` / `print` 两条「副作用未确证」的消除路径

两条**静态即可消除**，本轮已消，不遗留 LIVE：

**E1 `gantt-chart/export`（`exportWbs`）→ 结论：确定有副作用（写文件对象存储 + 写审计日志），非纯读。**
- 证据链（`p2/GanttChartAppService.javap.txt:1722` 方法体 offset 33–213）：
  - `new File #118("_")` 拼名 → `DateUtil.format(new Date(),"yyyyMMddHHmmss")` → `.xml`；
  - `File.createTempFile("wbs-temp",".xml")` → `FileOutputStream` → `PlusProject.Write(fos, map)`；
  - `new UploadRequestDto()` + `setUserId(RequestContext.getUserId())` + `setAppName(Apps.getAppName())` + `setFileName(fileName)` → **`FileService.upload(InputStream, UploadRequestDto)`** → `FileDto`；
  - `File.deleteOnExit()`（临时件）；
  - `GanttChartUtil.saveAuditLog("WBS组件", "导出了[<name>]的WBS")` —— **写访问审计上下文 + `auditLog.info()`**；审计落库由框架切面**后置**完成，**非直写业务表**（`aud_GanttChartUtil.u8.txt` saveAuditLog 方法体 = `AccessAuditContext.get()` → `getAccessAuditDto()` → `setDescription`/`setCategory` → `auditLog.info(auditDto.toLog())`，0 DAO）；
  - 返回 `SingleResponse<FileDto>`（`SingleResponse.from(fileDto)`）。
- 判定：**STATIC 确证有副作用**（对象存储产生新文件对象 + 审计上下文/日志一条）。**DB 落库面 = STATIC 确证不落库**（`dao` 字段在本方法体内 0 引用，0 DAO 写）。原"未确证"项**消除**。定级由 UNVERIFIED 升 **STATIC（副作用存在已证）**；副作用的具体存储位置/清扫策略仍属运行态细节，不在本面建模范围。
  - **审计契约注**：`saveAuditLog` 只写访问审计上下文 + `auditLog.info()`，**审计落库由框架切面后置，非直写业务表** —— 不构成对本表/业务表的写。

**E2 `gantt-chart/print`（`print`）→ 结论：确定有副作用（落 HTML 快照 + 起外部进程渲染 PNG + 上传 + 写审计无），非纯读。**
- 证据链（`p2/GanttChartAppService.javap.txt:1955` 方法体）：
  - 入参 `html`（String），先 `html.replace("charset=gb2312","charset=utf-8")`；
  - 文件名 `"snapshot_" + System.currentTimeMillis() + ".html"`；
  - `FileHelper.write(dir + fileName, html)` —— **落盘写 HTML**（`FileHelper.write` 体 = `FileOutputStream + OutputStreamWriter("UTF-8")`，已核）；
  - `createImg(dir+fileName, fileName)` → 内部 `savePage(htmlPath, pngPath)` → `Runtime.getRuntime().exec("chmod -R 777 " + dir)` + 拼 `sh <browserPath> … snapshot.js …` 存 StringBuffer 后执行 → **起外部浏览器进程做无头渲染**（日志串 `phantomjs-success:{}` / `phantomjs-error:{}` / `不支持的OA版本` / `打印出错`）；
  - 产出 `images/snapshot_<ts>.png` → `FileService.upload(...)` → 返回 storageKey；
  - 返回 `SingleResponse<String>`（storageKey）。
- 判定：**STATIC 确证有副作用**（本地临时文件 + 外部进程 + 对象存储上传）。**DB 落库面 = STATIC 确证不落库**（方法体内 0 DAO/0 DynamicMethod）。原"未确证"项**消除**。
- **但暴露一个新的、必须写进建模边界的事实**：`print` 依赖 `private static String dir` 与 `private static String browserPath`，二者在 `static{}` 初始化块中**均被赋空串 `""`**（`GanttChartAppService.javap.txt:2565/2567`，`ldc #79 // String` 后 `putstatic`），jar 内**无任何其它赋值点**（全文件 grep `putstatic #153`／`#172` 仅此一处）。⇒ 静态可证的结论是："**该端点在本 jar 内无法自足工作**，需外部（运行态反射/配置注入）为 `dir`/`browserPath` 赋值"，否则路径退化为 `""+fileName` 相对路径、`sh <空>` 无意义。**这一条只能标注为 LIVE 待验（外部注入机制 UNVERIFIED），不得写成"打印不可用"。**

⇒ **两条副作用项的消除结果：静态可消，已消。** 交付物 = 本节 E1/E2 证据链；不再需要 LIVE 输入来回答"是否有副作用"。E2 遗留的唯一待验项是"`dir`/`browserPath` 外部注入机制"，属该端点的**可用性**问题，不属"是否有副作用"问题，已分离标注。

### 2.4 本节顺带发现（不影响本步结论，供 main 决定是否另开）

- `importWbs`（W4）字节码路径 = `FileService.download` → `PlusProject.Read` → 返回 `HashMap`，**0 DAO / 0 DynamicMethod / 0 MQ**。**全链已追到叶子**：`PlusProject.Read` → `MSProject.Read` → `Import.ImportFile`（纯 XML DOM 解析）+ `checkProject`（仅改内存 HashMap 的 `FinishDate`），**三层均在本 jar `com/seeyon/boot/starter/ganttchart/utils/` 包内，均 0 持久化调用**（本轮独立 javap 复跑三类的 `// Method com/seeyon…` 引用集，仅 `Convert`/`StringUtil`/`Export` 等同包工具类，无 DAO/动态写/MQ）。
- ⇒ **落库面定级：STATIC 确证「import 不落库」**（原「`PlusProject.Read` 为外部 jar、内部行为不可证」的保留理由**作废**——三类均在本 jar 内，已逐层追空）。
- **口径限定（不改 r7 判定）**：`import` = **解析端点**（STATIC 确证 0 落库）；其被归入「写形态」系**按端点业务语义**（用户视角的导入动作会经由前端后续 `save` 改变业务状态），**实际落库由前端后续 `save` 承担**，不由本端点承担。据此 W4 在 §2.1 的「写形态」归类保持不变，仅将落库面定级由 UNVERIFIED 升为 STATIC 确证不落库。

---

## 3. 问 (c)：`gantt_chart_schema` 表与 schema 类端点的落库对应关系

### 3.1 三方字段映射（DDL ≡ 实体 ≡ 活体）—— DDL↔活体全等；实体 nullable 10/15

三个独立来源，逐列比对（**DDL↔活体 15/15 全等；实体↔活体 nullable 维度 10/15，5 列不符，详见下表 B**）：

| 来源 | 证据 | 列数 |
|---|---|---|
| ① jar 内 `ddl.sql`（jartext 权威建表件） | `p2/jar-extract/META-INF/starter/ganttchart/0.0.0-SNAPSHOT-0/ddl.sql`（sha256 `16019c3a…`，863 B） | 15 |
| ② 实体 `GanttChartSchema` 的 `@Entity/@Table` + `@Column` | `p2/GanttChartSchema.entity.javap.txt`（class_sha256 `76d591e1…`） | 15（本类 9 + 基类 6） |
| ③ 活体 `datamigration9000000000000000002_test2.gantt_chart_schema` | `p2/db-raw/p2-db-probe.raw.json` → `Q3_target_show_create` / `Q5_target_columns`（SHOW CREATE TABLE + information_schema.COLUMNS） | 15 |

比对结果（可复现脚本 `p2/three_way_compare.py`，输出 `p2/three_way.out.txt`，auditor 独立同口径脚本 `auditor/evidence/aud_p2/aud_three_way.py` + `.out.txt` 结果一致）：

| 比对 | 结果 |
|---|---|
| **A. DDL ↔ 活体**（列名 / 列顺序 / 类型族 / 可空性） | **15/15 全等**，mismatch=0（`DDL_ONLY=∅`、`LIVE_ONLY=∅`） |
| **B. 实体 `@Column` nullable=false ↔ 活体 NOT NULL** | **10/15 一致，mismatch=5**（5 列不符，见下） |
| C. 实体字段声明顺序 vs DDL 列序（观察项，不参与建表） | 位置 13/14 互换（`is_preset`/`is_enable`），列序以 ddl.sql 为准 |

**B. 5 列不符明细（实体侧 vs 活体侧）**：

| # | 列 | 实体注解 | 活体 IS_NULLABLE | DDL |
|---|---|---|---|---|
| 1 | `id` | `BaseEntity.id` `@Id` + `@Column(name="id")`，**未标 nullable**（JPA 默认 true，可空） | NO | NOT NULL |
| 7 | `name` | `@Column(name="name", nullable=false)` | **YES** | DEFAULT NULL |
| 8 | `code` | `@Column(name="code", nullable=false)` | **YES** | DEFAULT NULL |
| 9 | `app_guid` | `@Column(name="app_guid", nullable=false)` | **YES** | DEFAULT NULL |
| 12 | `config_schema` | `@Column(name="config_schema", nullable=false)` | **YES** | longtext（可空） |

> **口径注**：实体 `@Column(nullable=…)` **仅影响 JPA schema 生成路径**，不参与本表建表。本表由 ganttchart starter 的 `ddl.sql` 建立（`app_starter_init_detail` 有 `starter='ganttchart', file_name='ddl.sql', status='SUCCESS'` 实证，§3.2）。⇒ **可空性以 `ddl.sql` 为准**；实体注释与活体的 5 处偏差属实体注解层面的宽松/冗余，不构成建表事实差异。

| # | 列 | ddl 类型 | 活体类型 | 可空（ddl≡活体） | 实体来源 |
|---|---|---|---|---|---|
| 1 | `id` | bigint | bigint(20) | NOT NULL | `BaseEntity.id`（`@Column(name="id")`） |
| 2 | `tenant_id` | bigint | bigint(20) | NOT NULL | `BaseEntity.tenantId` |
| 3 | `create_time` | datetime | datetime | NOT NULL | `BaseEntity.createTime` |
| 4 | `update_time` | datetime | datetime | NOT NULL | `BaseEntity.updateTime` |
| 5 | `version` | smallint | smallint(6) | NOT NULL | `BaseEntity.version` |
| 6 | `guid` | bigint | bigint(20) | NOT NULL | `BaseTraceableEntity.guid` |
| 7 | `name` | varchar(50) | varchar(50) | NULL | 本类 `@Column(name="name")` |
| 8 | `code` | varchar(50) | varchar(50) | NULL | 本类 |
| 9 | `app_guid` | varchar(50) | varchar(50) | NULL | 本类 |
| 10 | `create_user_id` | bigint | bigint(20) | NOT NULL | 本类 |
| 11 | `create_org_id` | bigint | bigint(20) | NOT NULL | 本类 |
| 12 | `config_schema` | longtext | longtext | NULL | 本类 |
| 13 | `is_enable` | tinyint | tinyint(4) | NOT NULL | 本类（字段名 `enable`，列名 `is_enable`） |
| 14 | `is_preset` | tinyint | tinyint(4) | NOT NULL | 本类（`preset` → `is_preset`） |
| 15 | `is_delete` | tinyint | tinyint(4) | NOT NULL | 本类（`delete` → `is_delete`） |

- 实体类级注解（`p2/GanttChartSchema.entity.javap.txt` 尾）：`@Entity`、`@Table(name="gantt_chart_schema")`、`@EntityInfo(value="项目管理方案配置", description="项目管理配置", entityType=MASTER_ENTITY)`。
- 基类字段来源：`boot-core` 的 `BaseEntity`（`@Column(name="id"/"tenant_id"/"create_time"/"update_time"/"version")`）与 `BaseTraceableEntity`（`guid`）—— 已 javap 直读确认，非推断。
- DAO：`GanttChartSchemaDao extends BaseMybatisDao<GanttChartSchema>`（空接口，方法由泛型基类提供）⇒ ORM 映射对象就是该实体，映射目标表就是 `gantt_chart_schema`。

### 3.2 表归属哪个 schema / 数据源 —— LIVE 确证

| 事实 | 证据 | 定级 |
|---|---|---|
| `datamigration9000000000000000002_test2.gantt_chart_schema` **存在**，15 列，`COUNT(*) = 0` | `Q3`/`Q4`/`Q5`（SHOW CREATE + COUNT） | **LIVE** |
| 该 schema 共 97 张表；`gantt_chart_schema` 是其中唯一 gantt/wbs 相关表 | `Q11` + LIKE 'gantt%'/'wbs%'/'project%' 查询 | **LIVE** |
| 表由 **ganttchart starter 自身 ddl 机制**建立：`app_starter_init_detail` 有 `starter='ganttchart', file_name='ddl.sql', init_version='0.0.0-SNAPSHOT-0', status='SUCCESS'`（create_time 2026-10-13 11:34:23） | `Q7_starter_init_detail_ganttchart` | **LIVE** |
| 同库 `app_starter_init_version` 记 `starter='ganttchart'` 的 `init_version='0.0.0-SNAPSHOT-1'`、`app_version='1.0.7'` | `Q6_starter_init_version_ganttchart` | **LIVE** |
| jar 内 `META-INF/starter/ganttchart/0.0.0-SNAPSHOT-0/ddl.sql` 内容 = 活体表结构（逐列全等）；`0.0.0-SNAPSHOT-1/ddl.sql` = **0 字节空文件**（sha256 `e3b0c442…`=空文件哈希） | ①③比对 + `ls -l`（SNAPSHOT-1 大小 0） | **STATIC+LIVE** |

**归属结论**：
1. 表位于**目标业务应用库**（`datamigration9000000000000000002_test2`），与 UDC 的 `udc_test2` **不是同一库**；
2. 建表执行者是 **ganttchart starter 的 starter-init 机制**（`META-INF/starter/<name>/<init_version>/ddl.sql` ←→ `app_starter_init_detail` 逐条对账），**不是** UDC 的实体/属性元数据体系，也**不是** cdp-bi 的 `cdp_data*` 库；
3. ⇒ `gantt_chart_schema` 是 **ganttchart 面的自有落库表，按"每个应用库一套"随的应用（starter）初始化部署**，与 `app_guid` 列（"UDC应用GUID"）表达的"方案归属某 UDC 应用"是**数据层引用关系**，不是表归属关系。**表属 ganttchart，数据引用 UDC 应用。**

**全库横向（LIVE，本轮实测）**：`gantt_chart_schema` 在 **72 个 schema** 中存在；对 72 个逐库 `COUNT(*)` **合计 = 0 行，非零 schema = 空集**。
⇒ 与阶段1 P1 结论「Gantt 独立面、0 行」**方向一致、口径加强**（P1 用的是 `TABLE_ROWS` 估算 + 单库，本轮是 72 库逐库精确 COUNT）。
⇒ 实证了 §1.3 的核心阻塞：**5 条只读候选中 4 条依赖本表数据的 LIVE 回读，当前必然空集返回**。

### 3.3 端点 ↔ 落库对应（方法级闭环）

| 端点 | 落库动作（字节码证据） | 对应表 |
|---|---|---|
| `create` / `update` / `copy` / `update-active` / `delete-by-ids` | `GanttChartSchemaDao.create / update / create / updateBatch / updateBatch`（`p2/GanttChartSchemaService.javap.txt:487 / 528 / 808 / 669 / 734`） | `gantt_chart_schema` |
| `select-by-id` / `select-by-code` / `search-list` / `search` | `Dao.selectById / selectOneByCondition("code") / selectListByConditions / selectPageByConditions`（`:572 / 989 / 607 / 637`） | `gantt_chart_schema` |
| `save` / `copy` / `delete-by-wbsId`（Running 面，写） | **不落 `gantt_chart_schema`**：经 `GanttChartUtil.invoke*DynamicMethod` 操作 **UDC 动态实体**（WBS 任务数据），`gantt_chart_schema.config_schema` 仅作配置读取（`selectByCode(...).getConfigSchema()` → `JsonUtils.fromJson(..., GanttChartDto)`） | UDC 业务实体表（**非本面无权取证**）；配置读 `gantt_chart_schema` |
| `import`（Running 面） | **STATIC 确证不落库**：`FileService.download` → `PlusProject.Read` → `MSProject.Read` → `Import.ImportFile`，全链 0 DAO/0 DynamicMethod/0 MQ（§2.4） | 无（仅解析返回 HashMap） |
| `export` / `print`（Running 面） | **STATIC 确证不落库（DB）**：有副作用但不写业务表（对象存储上传 / 临时落盘+外部进程 / 审计上下文+日志，§2.3） | 无 DB 写 |

⇒ **schema 面 9 条端点 ↔ `gantt_chart_schema` 一一对应且闭合；Running 面 7 条端点的数据落点是 UDC 动态实体，`gantt_chart_schema` 只提供 schema 配置。** 这条区分是本面建模的关键：**"项目管理方案配置"与"甘特图运行数据"是两张不同落点，不能混为一张表。**

---

## 4. 定级汇总（逐问）

| 问 | 子项 | 定级 | 依据件 |
|---|---|---|---|
| (a) | 5 条只读候选 7 要素自洽性 | **STATIC 完备** | `p2/*Controller.javap.txt` 行号见 §1.1 |
| (a) | 5 条 LIVE 回读 | **UNVERIFIED**（5/5 缺口；4/5 叠数据缺口） | §1.2、§3.2（72 库 0 行） |
| (b) | 9 条写形态 7 要素 | **STATIC 齐备** | §2.1 表 + 各 javap 行号 |
| (b) | 「写」是否 VACUUM | **非 VACUUM**（VACUUM 定义不成立） | §2.0 |
| (b) | 写契约登记状态 | **登记缺口**（write=True 只登记不授权，维持） | §2.0 |
| (b) | `exportWbs` 副作用 | **STATIC 已确证有副作用**（原 UNVERIFIED 消除） | §2.3 E1 |
| (b) | `print` 副作用 | **STATIC 已确证有副作用**（原 UNVERIFIED 消除）；其 `dir`/`browserPath` 外部注入 = **UNVERIFIED（可用性项，非副作用项）** | §2.3 E2 |
| (b) | `importWbs` 落库面 | **STATIC 确证不落库**（0 DAO/0 DynamicMethod/0 MQ；PlusProject→MSProject→Import 全链在本 jar 内已追到叶子）；归入写形态系按端点业务语义，见 §2.4 口径限定 | §2.4 |
| (c-1) | DDL↔活体 字段映射 | **STATIC+LIVE 双向闭合**（列名/顺序/类型族/可空性 15/15 全等） | §3.1 A |
| (c-1) | 实体↔活体 nullable 维度 | **10/15**（5 列不符：`id`/`name`/`code`/`app_guid`/`config_schema`）；实体 nullable 仅影响 JPA schema 生成，建表以 ddl.sql 为准 | §3.1 B |
| (c-2) | 表归属 schema/数据源 | **LIVE 确证**：应用库 `…_test2`，ganttchart starter-init 建表 | §3.2 |
| (c-2) | 全库行数 | **LIVE**：72 schema，合计 0 行 | §3.2 |

## 5. 对「现有 5.3.260 证据是否覆盖读写」的直接回答

- **读：静态覆盖完备，运行态覆盖为 0。** 5 条只读候选 7 要素无缺陷，可作为"读契约"的静态基础；但一条 LIVE 都未达成，且其中 4 条被"全库 0 行"硬性挡住。⇒ **不能声称「读已打通」，只能声称「读契约静态成立、LIVE 未验」。**
- **写：静态覆盖完备（且比基线更完整——基线标"未落契约"，本轮已补齐 9 条 7 要素），运行态覆盖为 0，登记策略 = 只登记不授权。** ⇒ **「写」不是缺口也不是 VACUUM，是"证据已足、按纪律不落可执行契约"的有意状态。**
- **副作用两疑项：已按静态消除，不再挂账。**
- **落库：表归属与 DDL↔活体列映射双向闭合（15/15，含列名/顺序/类型族/可空性），且与活体实测一致；实体↔活体在 nullable 维度 10/15（5 列不符，属实体注解层冗余，建表以 ddl.sql 为准，不影响落库结论）。**
- **落库面三疑项已全部静态消除**：`exportWbs` / `print` / `importWbs` 均**STATIC 确证不落业务表**（前两者有非 DB 副作用，后者为纯解析端点）。

⇒ 综合：**5.3.260 证据在静态维度已覆盖读写；在 LIVE 维度读=0、写=0（写不做）。P2 的「是否覆盖读写」应回答为「静态覆盖，运行态未覆盖」，不得表述为「已覆盖」。**

## 6. 边界与红线自查

- **未修改** `docs/operation-contracts/udc/bi/ganttchart-5.3.260.md` 任何字节（基线判定原样维持；本件新增结论全部落在本文件）。
- **未落任何写操作契约为可执行**：9 条写形态仅登记 7 要素，`write=True` 不变，无 registry 改动、无 `components/platform_operations/*` 改动。
- **未碰** `docs/audit/artifacts/udc-bi-5.3.517/**`（64 件入库跟踪件）。
- **未做跨单元推论**：未由 5.3.260 推 5.3.517，未反向；跨版本装配关系保持 HYPOTHESIS。
- **DB 侧全 SELECT**：`SHOW CREATE TABLE` / `information_schema` / `COUNT(*)` / 定向 `SELECT`，0 写、0 DDL、0 测试数据。
- **凭据**：仅按路径引用 `shared-credentials/test2-web-credential.json`；DB 凭据来自本机环境文件路径，**未打印任何 secret**（raw json 中仅记 host/port/env 与 `note`）。
- **未 push**；本轮 jar 解析/DB 探测的中间脚本与 raw 输出均已落在 `p2/`、`p2/db-raw/`，可复现。
- **r2 订正范围自查（HANDOFF #3）**：只改本文件 + `p2/` 新增 `three_way_compare.py` / `three_way.out.txt`；`ganttchart-5.3.260.md`、registry、5.3.517 单元、实现代码 **0 字节变更**（`git diff --stat` 空）。订正性质 = 结论句措辞 / 口径限定 / 定级升级，**未新增业务声明**，未新增端点/表/字段事实。

## 7. 原始证据清单（路径 = `docs/audit/artifacts/udc-bi-5.3.260/p2/`）

| 文件 | 内容 | 用途 |
|---|---|---|
| `GanttChartRunningController.javap.txt` | 8 方法全字节码 + 注解 + 常量池 | (a)(b) Running 面 |
| `GanttChartSchemaController.javap.txt` | 10 方法全字节码 + 注解 | (a)(b) Schema 面 |
| `GanttChartAppService.javap.txt` | Running 应用服务（含 exportWbs/print/createImg/savePage 全方法体） | (b) 副作用 + 写链 |
| `GanttChartSchemaAppService.javap.txt` | Schema 应用服务 9 方法 | (b) 写链 |
| `GanttChartSchemaService.javap.txt` | 域服务（DAO 调用点、lambda、MQ 发送） | (b)(c) 落库闭环 |
| `GanttChartService.javap.txt` | 动态实体写方法调用链 | (b)(c) Running 面落点 |
| `GanttChartSchema.entity.javap.txt` | 实体 @Table/@Column 全量 | (c-1) 字段映射 |
| `jar-extract/META-INF/starter/ganttchart/0.0.0-SNAPSHOT-0/ddl.sql` | jar 内建表件（863 B） | (c-1)(c-2) |
| `jar-extract/metadata/starter_info.json` | starter 元数据（name/basePackage/type=2） | (c-2) 归属 |
| `db-raw/p2-db-probe.raw.json` | 72 库表清单、活体 SHOW CREATE、starter-init 对账、全库 COUNT | (c-2) + (a) 阻塞 |
| `db_probe*.py` / `db-raw/` | 探测脚本（可复现） | 复现性 |
| `three_way_compare.py` / `three_way.out.txt` | **三方列比对脚本 + 落盘输出**（DDL↔活体 15/15、实体↔活体 nullable 10/15 的全部数字由此复现） | (c-1) 复现性 |
| `MSProject.p2.javap.txt` / `FileHelper.p2.javap.txt` / `File.p2.javap.txt` / `Export.p2.javap.txt` / `GanttChartSchemaDao.p2.javap.txt` / `GanttChartSchemaDto.p2.javap.txt` | 二轮独立复核增量（import 全链叶子 / print 落盘 / DAO 泛型基类） | (b) W4、§2.3、(c) |

**复现方式（(c-1) 结论）**：
```
cd docs/audit/artifacts/udc-bi-5.3.260/p2
python three_way_compare.py            # 或 tee three_way.out.txt
```
交叉复现（auditor 独立同口径脚本，结果一致）：
`session-20261017-150721-8c130f15/auditor/evidence/aud_p2/aud_three_way.py` → `aud_three_way.out.txt` / `.out.json`

- jar：`a98863787e97733ea38c2bd57904b4a86dd2db6ada07c968445ac191b2acdbde`
- ddl.sql：`16019c3abd1261a57a92f28c70e0f99704cbcba85933d48dcee47f77350000f9`
- `GanttChartSchema.class`：`76d591e1e9be94b1dc6b880db7011785de31bacfd684e81b89ad21d2abd6e26b`
- `GanttChartSchemaController.class`：`cad8796509e7ccf4ffd0a020ae3ba004e3bf2670c6a058248d825c9d652385cb`
- `GanttChartRunningController.class`：`8d43516d96edfb6c38ef7a9c8a5cdb1e00c9cdf03a8be47d2025b84ff0176f84`
- `GanttChartAppService.class`：`8f92e1d8a11f435f0d0275d5d8e7f2795f8556ca3c04a0cb8350d274e76fa524`
- `GanttChartSchemaService.class`：`95f58c6b5e22ddd3d45a6bcb281252706160c3269827264badd6113937e72e6f`
