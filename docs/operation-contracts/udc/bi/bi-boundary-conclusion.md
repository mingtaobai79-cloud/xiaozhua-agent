# UDC · BI（报表/可视化）域 · 归属边界结论

> **本件性质**：边界结论书面化（C 类边界确认任务的唯一业务产出）。**不含任何新取证**——全部结论由前序已收口证据合并书写，逐条给出证据路径。
> **授权链**：main HANDOFF #4（dedupe_key `bi-p3-boundary-doc`，2026-10-17T09:43:10Z）→ 本件为其唯一动作产出。
> **仓库**：`<SEEYON_AGENT_ROOT>`（纯 local，禁 push）。
> **证据等级纪律**：本件只做三件事——(1) 引用已收口证据；(2) 标注每条结论的等级（LIVE / STATIC / VACUUM / UNVERIFIED）；(3) 给出验收标准对账。**不新造端点、不新造表、不新造字段**。
> **版本单元纪律**：本件合并两个**物理分开、禁混写、禁互推**的证据单元 —— `5.3.517`（UDC 六个 jar，VACUUM 判定）与 `5.3.260`（`boot-starter-ganttchart`，Gantt 独立面）。两单元的任何数字都不得跨单元推论。
> **凭据**：仅按路径引用 `<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json`；本件 0 secret、0 token、0 cookie。

---

## 0. 结论（一句话 × 三条）

**UDC 域内没有 BI。** UDC 5.3.517 六个 jar 的真 BI 只读契约 = **0 条（VACUUM，完备负证据）**；DB 侧无 `udc_bi` / `udc_report` 表。

**Gantt 之外的 BI 不在 UDC，也不在 ctp 门户，而在标品侧独立子应用面 `cdp-bi`。** 前端 Module Federation scope = `cdp-data`，后端 `/service/cdp-bi/*`，数据 `cdp_data` / `cdp_data_test2`；ctp 门户只做菜单挂载。

**Gantt 面单独建模。** `gantt_chart_schema` 是 `ganttchart` starter 自有的落库表，对 UDC 应用是**数据层引用**（`app_guid` 列）而非表归属；静态维度读写均已覆盖，运行态（LIVE）读=0、写=0，4 项前置条件维持 UNVERIFIED 收口。

⇒ **客户要 BI，走标品侧 `cdp-bi` / `cdp-data` 建模；客户要甘特图，走 Gantt 面（starter 自有表 + UDC 动态实体）建模；两条路都不在本域内新建 BI 契约。**

---

## 1. 归属地图（三方分离）

| 维度 | **UDC 域**（5.3.517 六 jar） | **Gantt 面**（`boot-starter-ganttchart` 5.3.260） | **BI 子应用面**（`cdp-bi` / `cdp-data`） |
|---|---|---|---|
| 真 BI 端点 | **0 条**（VACUUM） | 16 条端点（本面自有；只读 5 / 写形态 9 / 副作用 2） | 报表中心读路径 3 接口 + 管理面/大屏面另有 4+ LIVE + bundle STATIC 若干 |
| 落库 | 无 BI 表 | `gantt_chart_schema`（starter 自有，15 列） | `cdp_data_test2` 内 7 张 `cdp_bi_*` 表 + `cdp_big_screen_model_rel`（合计 8 张；`cdp_bi_report` 精确 362 行） |
| 归属判定 | **BI 契约不在 UDC** | **表属 ganttchart，数据引用 UDC** | **独立标品子应用，非 UDC、非 ctp 门户自身** |
| 与 UDC 的连接方式 | —（自身即域） | `app_guid` 列 = 数据层引用；运行面读写目标为 **UDC 动态实体** | **无表级耦合**；仅门户菜单挂载 |
| 定级 | VACUUM（完备负证据） | STATIC 覆盖 / LIVE 未达 | LIVE（落点、菜单、页面、后端归属均已实测） |

**读法**：三列是**三个不同的业务面**，不是同一个「BI 模块」的三个子系统。任何跨列合并（如"UDC 有 Gantt 所以 UDC 有 BI"）都是错误建模。

---

## 2. 结论一：UDC 域内真 BI 契约 = 0 条（VACUUM）

### 2.1 判定

UDC `5.3.517` 六个 jar 上，按 13 个 BI 关键词宽口径扫描并逐条排除伪命中后，**不存在任何一条可证据化的「真 BI 域只读 controller/服务」**。判定性质 = **VACUUM（域真空，完备负证据）**，不是"未找到"。

| 层 | 口径 | 覆盖量 | 结果 | 等级 |
|---|---|---|---|---|
| L-A 类名层 | 1217 class FQCN × 13 BI 关键词宽口径子串 | 1217 class | 真 BI = **0**（唯一 `bi` 子串 29 条全为 `biginteger`/`bill`/`biz`/`scalability`/`combination`/`compatibility` + `BiLinkedList`） | VERIFIED_STATIC_BYTECODE |
| L-B 端点路径字面量层 | **219 行逐条判定**（35 类级 + 184 方法级） | 6 jar / 1217 class → mapping-bearing 类 **38** 个 | CANDIDATE(真 BI) = **0**；PSEUDO-EXCLUDED = 4（`stat` 词干被 `state`/`status` 包含）；EXCLUDED-NO-BI-STEM = 215 | VERIFIED_STATIC_BYTECODE |
| L-C 常量池全量层 | 1217 类全部常量池 Utf8（含中文）BI 词干扫描 | 1217 class | BI 邻近词干命中 84 条，**属 mapping-bearing 类的 = 0** | VERIFIED_STATIC_BYTECODE（计数）；语义判读为 OBSERVATION |
| 双口径一致性 | 自实现常量池/注解解析 vs `javap -p -v` 解码文本 | 38/38 类 | **mismatch = 0** | VERIFIED_STATIC_BYTECODE |

- **扫描方法完备性**：6 jar / 1217 class / 13 关键词 / 219 行端点字面量 / 38 类 `javap -p -v`。L-B 覆盖全部 mapping-bearing 类，无缺口（`@RestController` 35 个全在 bearing 集内；bearing 38 − 35 = 3 个无 stereotype 基类已计入端点表；bearing 类中 `@interface` = 0 → 不存在自定义 meta-annotation 声明映射的盲区）。
- **DB 侧边界复核（LIVE）**：UDC 目标库 `datamigration9000000000000000002_test2` 对 `%bi%|%report%|%chart%|%dashboard%` 的命中仅 3 张 —— `gantt_chart_schema`（Gantt 独立面）+ `cip_ability_doc_file_convert` / `cip_ability_doc_file_version`（`ability` 里的 `bi` 子串伪命中，能力中心表）。**无 `udc_bi` / `udc_report` 表。**

### 2.2 registry 影响

本域 registry **不新增任何 `UdcOperationContract` 条目（0 条）**，`contracts["udc.bi.*"]` 不写入；MERGE 任务照抄"真空"这一事实即可，不得因"查不到"而补哨兵或留空争议。

### 2.3 证据路径

| 内容 | 路径 |
|---|---|
| VACUUM 负证据契约（28.1KB，三层口径 + 7 要素负证据形式） | `docs/operation-contracts/udc/bi/bi-vacuum-contract.md` |
| registry 真空登记 | `docs/operation-contracts/udc/bi/registry-entries.md` |
| 端点全量表 + 逐类 provenance（106KB） | `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md` |
| 可复跑脚本（6 个）/ 原始计数（5 个 json）/ 38 个 javap | `docs/audit/artifacts/udc-bi-5.3.517/`（`r1_scan_mapping_bearing.py`、`r1_extract_endpoints.py`、`r1_javap_dump.py`、`r1_completeness_checks.py`、`r1_build_report.py`、`r1_bi_judge.py`；`r1_step1_raw.json`…`r1_step5_completeness.json`；`r1-<Class>.javap.txt`） |

---

## 3. 结论二：Gantt 之外的 BI 落在标品侧独立子应用面 `cdp-bi`

### 3.1 落点（LIVE）

| 断言 | 实测结果 | 等级 |
|---|---|---|
| 前端子应用 | Module Federation scope = **`cdp-data`**；页面 URL 段 `/cdp-data/report/<guid>`、`/cdp-data/reportReception` | LIVE |
| 后端服务 | `/service/cdp-bi/*`（**路径段是 `cdp-bi`，页面 URL 段是 `cdp-data`，两者不同名**） | LIVE |
| 数据 | `cdp_data` / `cdp_data_test2`；`cdp_data_test2` 内 7 张 `cdp_bi_*` 表 + `cdp_big_screen_model_rel`（合计 8 张；`cdp_bi_report` = **362** 行精确 `COUNT(*)`） | LIVE |
| 部署面 | 独立工作负载 `cdp-data-587fb58d45-74jld` 1/1 Running（`kubectl --kubeconfig=configtest2` 只读）；应用名 `cdp-data` 与 schema / 前端 scope / 后端路径同族 | LIVE |
| 与 UDC 关系 | **无表级耦合**：BI 表全在 `cdp_data*`，UDC 目标库 0 张 BI 表 | LIVE |

**报表按归属应用分布**（`cdp_bi_report`，LIVE）：`app9000000000000000001` 158 / `yznxmglpt…` 38 / `znxmgl121386570299241515796755` 38 / `xiangmuguanli…` 32 / `cdp-data` 21 / … / 共 12 个应用。⇒ 这是**多应用共享的标品 BI 引擎**，不是某一应用的私有能力，更不是 UDC 的延伸。

### 3.2 ctp 门户的角色 = **仅菜单挂载**（LIVE）

| 断言 | 实测结果 |
|---|---|
| 菜单归属 | `ctp_user_test2.ctp_menu` 中 `app_id='cdp-data'` 共 12 行（含 `menu_level=1` 「报表中心」`sort=70 display=1`、`menu_level=2` 「报表分析」`sort=71 display=1`） |
| 资源声明 | `ctp_user_test2.ctp_resource` `id=-7115018481021843449` / `code=frontend-data-report` / `name=报表中心` / `app_id=cdp-data` / `frontend_app_id=cdp-data` / **`plugins=cdpBi`** |
| 入口条数 | 前导航 API `GET /service/ctp-user/menu/select-front-nav-menu` 响应 602 个菜单节点、顶层 19 个；其中 url 直接命中 `/cdp-data/report/<guid>` 的 **5 条**（项目考核管理×3、智慧营销结算报表×1、应收管理×1） |
| 判读 | `ctp_resource.plugins = cdpBi` 是门户侧对 BI 归属的**显式声明**：ctp 只登记"入口"，BI 能力由 `cdpBi` 插件/子应用提供。**门户自身不含 BI 对象。** |

### 3.3 端点面口径（**必须按此书写，不得简化**）

> **报表中心读路径 3 接口**（管理面/大屏面另有 **4+ LIVE**，见 `auditor/evidence/aud_bi_svcscan2.out.json`）

| 分组 | 数量 | 端点 | 等级 |
|---|---|---|---|
| 报表中心读路径（页面点击实测） | **3** | `POST /service/cdp-bi/report-category/run-report-tree-by-category`、`POST /service/cdp-bi/report-design/get-user-report`、`GET /service/cdp-bi/report-runtime/get-report-data` | LIVE（200，响应体已落盘） |
| 管理面 / 大屏面（另抓） | **4** | `POST /service/cdp-bi/auth/user-report-auth`、`POST /service/cdp-bi/report-design/get-report-page`、`GET /service/cdp-bi/screen-auth/user-bigscreen-auth`、`POST /service/cdp-bi/screen-manage/get-bigscreen-page` | LIVE（200） |
| bundle 静态字面量 | 若干 | `remoteEntry.js` 内 `src_portlet_cdp-bi_reportCategory_index_jsx`×4、`reportSelect_index_jsx`×3、`myReport_index_jsx`×4、`reportConfig_index_jsx`×1、`cdp-bi`×1、`/cdp-bi/report-runtime/link`×1；路由表 10 条（含 `/cdp-data/udc/portlet/select/report`、`/cdp-data/report/`、`/cdp-data/screen/`、`/cdp-data/udc`） | STATIC（bundle 扫描） |

**红线**：`cdp-bi` **全端点 ≠ 3**。3 只是"报表中心读路径"的局部口径；把它写成"cdp-bi 全部端点"是把局部当全集，属实证错误。

### 3.4 证据路径

| 内容 | 路径 |
|---|---|
| 落点主证据（13.4KB，LIVE） | `docs/audit/artifacts/udc-bi-5.3.517/bi-portal-ctp-landing.md` |
| DB 关键词扫描 / 明细 / 菜单归属 / 前导航 / cdp-bi 响应体（5 个 raw） | `docs/audit/artifacts/udc-bi-5.3.517/bi-portal-{db-keyword-scan,db-detail,menu-attribution,front-nav-menu,cdpbi-api-bodies}.raw.json` |
| 端点面修正证据（bundle / 路由） | `session-20261017-150721-8c130f15/auditor/evidence/aud_bi_svcscan2.out.json`、`aud_bi_routes.out.json` |
| 3 接口抓包与响应体 | `session-20261017-150721-8c130f15/auditor/evidence/aud_bi_cap.log`（`report-runtime/get-report-data` 全响应 12580B） |
| 管理面 2 接口抓包 | `session-20261017-150721-8c130f15/auditor/evidence/aud_bi_cat2.log`（`user-report-auth` / `get-report-page`） |
| 大屏面 2 接口抓包 | `session-20261017-150721-8c130f15/auditor/evidence/aud_bi_screen.log`（`user-bigscreen-auth` / `get-bigscreen-page`） |

> 路径口径注：HANDOFF #4 正文写作 `audit_bi_svcscan2.out.json`，实测同名件为 **`aud_bi_svcscan2.out.json`**（无 `it` 前缀），本件按实测文件名引用。

---

## 4. 结论三：Gantt 面单独建模（5.3.260，P2 订正后口径）

### 4.1 表归属（本节最关键的一条）

**`gantt_chart_schema` 属 `ganttchart` 面 starter 自有落库表；对 UDC 应用是数据层引用（`app_guid` 列），不是表归属。**

| 事实 | 证据 | 等级 |
|---|---|---|
| 表存在于**目标业务应用库** `datamigration9000000000000000002_test2`，15 列，`COUNT(*) = 0` | `SHOW CREATE TABLE` + `COUNT(*)` | LIVE |
| 建表执行者 = **ganttchart starter 的 starter-init 机制**：`app_starter_init_detail` 有 `starter='ganttchart', file_name='ddl.sql', init_version='0.0.0-SNAPSHOT-0', status='SUCCESS'`（create_time 2026-10-13 11:34:23） | `app_starter_init_detail` 对账 | LIVE |
| jar 内 `META-INF/starter/ganttchart/0.0.0-SNAPSHOT-0/ddl.sql` ≡ 活体表结构；`SNAPSHOT-1/ddl.sql` = 0 字节空件（sha256 `e3b0c442…`） | 逐列比对 + `ls -l` | STATIC+LIVE |
| 与 UDC 的 `udc_test2` **不是同一库**；也不是 cdp-bi 的 `cdp_data*` 库 | `SHOW TABLES` / schema 清单 | LIVE |
| 全库横向：`gantt_chart_schema` 在 **72 个 schema** 中存在；逐库 `COUNT(*)` **合计 0 行，非零 schema = ∅** | 72 库逐库精确 COUNT | LIVE |

⇒ **三层归属分离**：表属 `ganttchart`（starter 自有 DDL，按"每个应用库一套"随应用初始化部署）；`app_guid` 列表达"某方案归属某 UDC 应用"，是**数据层引用关系**；UDC 的实体/属性元数据体系**不参与**本表建表。

### 4.2 静态维度：读写静态覆盖

| 问 | 结论 | 定级 |
|---|---|---|
| (a) 「读」 | 5 条只读候选的 **7 要素逐条自洽完整**（method / 路径原值 / 参数注解 / 返回 DTO / evidence / 语义归因 / LIVE 条件），字节码可证，无"名为读实为写"双关项 | **STATIC 完备** |
| (b) 「写」 | 9 条写形态 7 要素**全部可补齐**，写路径闭环到真实持久化动作（DAO `create`/`update`/`updateBatch`、UDC 动态写方法）⇒ **不是 VACUUM**；未落契约是**登记策略缺口**（`write=True` 只登记不授权） | **STATIC 覆盖** |
| 副作用 | `exportWbs` 有副作用（文件服务上传 + 审计上下文/日志）、`print` 有副作用（临时落盘 + 外部进程 + PNG 上传）；`importWbs` = **纯解析端点**（0 DAO / 0 DynamicMethod / 0 MQ，全链追到叶子） | **STATIC 确证不落库**（原 UNVERIFIED 已消除） |
| (c) 落库对应 | `schema` 面 9 条端点 ↔ `gantt_chart_schema` 一一闭合；`running` 面 7 条端点落 **UDC 动态实体**（配置读 `gantt_chart_schema.config_schema`） | STATIC+LIVE 双向闭合 |

**列映射口径（禁止简化成"三方全等"）**：
- **DDL ↔ 活体**：15/15 全等（列名 / 列顺序 / 类型族 / 可空性），mismatch = 0。
- **实体 @Column ↔ 活体 nullable**：仅 **10/15** 一致，5 列不符 —— `id`（`@Column` 未标 nullable，JPA 默认可空 vs 活体 NOT NULL）、`name` / `code` / `app_guid` / `config_schema`（`nullable=false` vs 活体 `DEFAULT NULL` / 可空 longtext）。
- **口径裁定**：实体 `@Column(nullable=…)` 仅影响 JPA schema 生成路径；本表由 starter `ddl.sql` 建立（`app_starter_init_detail` 实证），故**可空性以 `ddl.sql` 为准**。不得表述为"三方全等 / All_MATCH=True"。

### 4.3 建模边界（三条关键区分）

1. **"方案配置"与"运行数据"是两张不同落点**：`gantt_chart_schema` 只存方案配置；WBS 任务数据落在 UDC 动态实体表（**本面无权取证**）。不能混为一张表。
2. **`import` 是解析端点**：归入"写形态"系按端点业务语义（用户视角的导入动作会经由前端后续 `save` 改变业务状态），实际落库由前端后续 `save` 承担，不由本端点承担。
3. **`delete-by-ids` 的 MQ 有应用条件门**：`Apps.getAppName() ∈ {udc, app-approval}` 才 `executorService.execute` 异步发 `GanttChartDetectionMessage`，且 `execute` 提交先于 `dao.updateBatch`。作为 UDC 应用语境成立，作为通用契约缺条件门 —— 不得表述为"本端点恒发 MQ"。

### 4.4 运行态：读=0、写=0，4 项维持 UNVERIFIED 收口

| # | LIVE 待验项 | 现状 |
|---|---|---|
| 1 | 网关到 ganttchart starter 的 service 路由前缀 | UNVERIFIED（离线不可确证，**禁拼**） |
| 2 | 目标环境有效会话（`shared-credentials/test2-web-credential.json`，值 0 入件） | UNVERIFIED |
| 3 | 已启用甘特图方案样本数据（`gantt_chart_schema` 全库 0 行，4/5 只读条目必然空集返回） | UNVERIFIED |
| 4 | `checkLicense → hasPlugin("ganttchart")` 授权门（16/16 端点共用；未启插件一律 `BOOT_3006`） | UNVERIFIED |

**收口裁定**：上述 4 项**维持 UNVERIFIED 收口**，本域（C 类边界确认任务）**不排打通任务**。§4.2 的静态覆盖不因 LIVE 未达而降级或升级。

### 4.5 证据路径

| 内容 | 路径 |
|---|---|
| 覆盖核对（P2 主件，r2 订正后） | `docs/operation-contracts/udc/bi/ganttchart-5.3.260-coverage.md` |
| 上级基线（**未改一字**，判定原样维持） | `docs/operation-contracts/udc/bi/ganttchart-5.3.260.md` |
| jar / class / ddl 哈希、javap 全文、DB raw、比对脚本 | `docs/audit/artifacts/udc-bi-5.3.260/p2/`（`three_way_compare.py` + `three_way.out.txt` 可复现；`db-raw/p2-db-probe.raw.json` 含 72 库 COUNT / SHOW CREATE / starter-init 对账） |
| auditor 独立复核（VERDICT=PASS 依据：25 文件） | `session-20261017-150721-8c130f15/auditor/evidence/aud_p2/`（`aud_three_way.py` + `.out.txt` 独立同口径脚本）；`auditor/evidence/AUD-VERDICT-p2-gantt-coverage.md` |

---

## 5. 验收标准对账（TASK-GOAL 五、三条）

| # | 验收标准原文 | 达成 | 结论位置 | 证据路径 |
|---|---|---|---|---|
| 1 | **BI 归属边界结论书面化（UDC 域内 0 条，转标品侧）** | ✅ **达成** | §0 结论二/三、§2（UDC 0 条 + VACUUM）、§3（落点在 `cdp-bi`）、§6（转标品侧路由） | `docs/operation-contracts/udc/bi/bi-vacuum-contract.md`（VACUUM 判定 + 三层完备口径）<br>`docs/operation-contracts/udc/bi/registry-entries.md`（0 条登记）<br>`docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md`（219 行逐条）<br>`docs/audit/artifacts/udc-bi-5.3.517/bi-portal-ctp-landing.md`（BI 真实落点 LIVE）<br>`docs/audit/artifacts/udc-bi-5.3.517/bi-portal-db-keyword-scan.raw.json`（DB 边界） |
| 2 | **Gantt 面单独建模，读写契约明确** | ✅ **达成（静态维度）**；运行态标注 UNVERIFIED 收口 | §3.1 表归属、§4.1–§4.4（读 5 / 写 9 / 副作用 2 / 列映射 / 建模边界 3 条 / LIVE 4 项） | `docs/operation-contracts/udc/bi/ganttchart-5.3.260-coverage.md`（(a)(b)(c) 三问 + 定级汇总 + §5 直接回答）<br>`docs/operation-contracts/udc/bi/ganttchart-5.3.260.md`（基线只读契约，未改）<br>`docs/audit/artifacts/udc-bi-5.3.260/p2/three_way_compare.py` + `three_way.out.txt`（列映射可复现）<br>`docs/audit/artifacts/udc-bi-5.3.260/p2/db-raw/p2-db-probe.raw.json`（表归属 + 72 库 0 行） |
| 3 | **不与其余八域混淆，不虚构 UDC BI 契约** | ✅ **达成** | §1 归属地图（三方分离）、§2（registry 0 条、无哨兵）、§3.3（端点面口径红线：不得写"全端点=3"）、§4.3（三类区分）、§7（不做项与红线） | `docs/operation-contracts/udc/bi/registry-entries.md`（`contracts["udc.bi.*"]` 不写入）<br>`docs/audit/udc-nine-modules-status.md:16/131-149`（九域对照，BI 单列）<br>`session-20261017-150721-8c130f15/auditor/evidence/aud_bi_svcscan2.out.json` + `aud_bi_routes.out.json`（端点面全集口径）<br>`main/ROUTE.md`（阶段隔离与硬边界） |

**达成度说明**：三条全部达成。第 2 条的"读写契约明确"限定在**静态维度**（STATIC 完备 / 运行态未达）——这是本域（C 类边界确认）的口径，**不等于"已打通"**，且无需在本域内打通（见 §4.4 收口裁定）。

---

## 6. 交付路由：客户要 BI 时怎么走

| 客户诉求 | 建模归属 | 建模方式 | 依据 |
|---|---|---|---|
| **报表 / 大屏 / 数据集 / 数据流 / 看板** | **标品侧 `cdp-bi` / `cdp-data`**（本域域外） | 前端走 `cdp-data` 子应用（经宿主壳 `/main/child-frame/cdp-data/…`），后端 `/service/cdp-bi/*`，数据落 `cdp_data*`；门户只挂菜单（`ctp_menu.app_id='cdp-data'` / `ctp_resource.plugins='cdpBi'`） | §3.1、§3.2 |
| **甘特图 / WBS / 项目管理计划** | **Gantt 面**（5.3.260 独立单元） | 方案配置 → `gantt_chart_schema`（starter 自有表，`app_guid` 引用 UDC 应用）；任务数据 → UDC 动态实体；端点面 = `gantt-chart` / `gantt-chart-schema` 两组 | §4.1、§4.2、§4.3 |
| **期望"在 UDC 低代码里直接建 BI 报表"** | —（能力不存在） | **不做 UDC BI 契约建模**；转上两行路由，或按下一条说明缺口 | §2（VACUUM）；`docs/audit/udc-nine-modules-status.md` |
| **BI 与 UDC 业务数据打通** | 跨面集成（本域**不建模**） | 需另立集成任务（数据源/接口对接），不在本域范围；本域只提供"边界已确认、无表级耦合"这一前提 | §3.1（无表级耦合）、§7 |

---

## 7. 边界、不做项与已知坑

### 7.1 本件明确不做

- **不新建 UDC BI 契约**（VACUUM 已完备，任何"补齐"都是虚构）。
- **不排 LIVE 打通任务**（§4.4 4 项维持 UNVERIFIED 收口；本域是边界确认，不是开发任务）。
- **不做 BI 与 UDC 的集成建模**（跨面，另立任务）。
- **不改** `ganttchart-5.3.260-coverage.md` / `ganttchart-5.3.260.md` / `registry-entries.md` / 5.3.517 单元 64 件 / 任何实现代码（本件为**唯一新增产出**）。
- **不跨单元推论**：不得由 5.3.260 推 5.3.517，不得反向（跨版本装配关系保持 HYPOTHESIS）。

### 7.2 表述红线（复述，防后续误用）

1. `cdp-bi` **全端点 ≠ 3**；3 是"报表中心读路径"局部口径，管理面/大屏面另有 4+ LIVE 与 bundle STATIC 若干。
2. `gantt_chart_schema` **不是 UDC 表**，也不是 cdp-bi 表；表属 `ganttchart` starter。
3. 列映射不得写"三方全等"：DDL↔活体 15/15，实体↔活体 nullable 10/15（5 列不符，以 `ddl.sql` 为准）。
4. Gantt 面 **"静态覆盖、运行态未覆盖"**，不得表述为"已覆盖 / 已打通"。
5. UDC BI 是**完备的零（VACUUM）**，与其余域"证据量大但仍在深挖"性质不同，不能套用同一"完成度"话术。

### 7.3 已知坑（供后续任务复用）

1. `cdp-data` 子应用深链 `/cdp-data/reportReception` 直开会命中 OSS 静态桶（`NoSuchKey: cdp-data/index.html`），**必须经宿主壳** `/main/child-frame/cdp-data/...`，否则会误判"BI 不存在"。
2. 页面 URL 段是 `cdp-data`，后端路径段是 `cdp-bi` —— 两者不同名，凭 URL 猜后端会错。
3. `information_schema.TABLE_ROWS` 是估算值（`cdp_bi_report` 估 317、实测 362），结论必须用 `COUNT(*)`。
4. BI 关键词伪命中极多（`cip_ability_*`、`bizhongpe_*`、`biangeng*`、`toubiao*`、`stat`→`state/status`），必须逐 schema / 逐类归类，不能按命中数下结论。
5. `cdp-data-assemble.jar` 是加密 zip（`zip flag 1 (encryption) is not supported`），取类清单需另找路径；不影响边界结论。

---

## 8. 证据路径总清单

| # | 文件 | 角色 | 等级 | 支撑结论 |
|---|---|---|---|---|
| 1 | `docs/operation-contracts/udc/bi/bi-vacuum-contract.md` | 本域 VACUUM 负证据契约 | VACUUM / STATIC | §2 全部 |
| 2 | `docs/operation-contracts/udc/bi/registry-entries.md` | registry 0 条登记 | — | §2.2、§5-1/§5-3 |
| 3 | `docs/operation-contracts/udc/bi/ganttchart-5.3.260.md` | Gantt 基线只读契约（**未改**） | STATIC | §4.2 |
| 4 | `docs/operation-contracts/udc/bi/ganttchart-5.3.260-coverage.md` | Gantt 读写覆盖核对（P2 r2） | STATIC / LIVE | §4 全部 |
| 5 | `docs/audit/artifacts/udc-bi-5.3.517/bi-portal-ctp-landing.md` | BI 真实落点主证据 | LIVE | §3.1、§3.2 |
| 6 | `docs/audit/artifacts/udc-bi-5.3.517/bi-portal-*.raw.json`（5 件） | 落点原始数据 | LIVE | §3.1、§3.2 |
| 7 | `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md` + `r1_*` 脚本/计数/javap | 端点层完备负证据 | STATIC | §2.1 |
| 8 | `docs/audit/artifacts/udc-bi-5.3.260/p2/`（javap + cfr + db-raw + `three_way_compare.py`/`.out.txt`） | Gantt 静态与落库证据 | STATIC / LIVE | §4.1、§4.2 |
| 9 | `session-…-8c130f15/auditor/evidence/aud_bi_svcscan2.out.json` + `aud_bi_routes.out.json` | 端点面全集口径（bundle/路由） | STATIC | §3.3 |
| 10 | `session-…-8c130f15/auditor/evidence/aud_bi_cap.log` / `aud_bi_cat2.log` / `aud_bi_screen.log` | 3+4 接口抓包与响应体 | LIVE | §3.3 |
| 11 | `session-…-8c130f15/auditor/evidence/aud_p2/`（25 文件）+ `AUD-VERDICT-p2-gantt-coverage.md` | Gantt 独立复核 | 独立复核 | §4 全部 |
| 12 | `docs/audit/udc-nine-modules-status.md`（:16、:131-149） | 九域全局状态（BI 单列） | 权威状态 | §5-3 |
| 13 | `docs/audit/artifacts/udc-bi-5.3.517/r1_step2_endpoints.json`（215KB） | 端点全集原始件 | STATIC | §2.1 |

**凭据**：全程仅路径引用 `<COLLAB_ROOT>\agent-collaboration\shared-credentials\test2-web-credential.json`；本件与全部被引证据件 **0 secret / 0 token / 0 cookie**。
