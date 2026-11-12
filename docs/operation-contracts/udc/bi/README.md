# BI 域契约层（`docs/operation-contracts/udc/bi/`）

> **UTD 契约层的 BI 域**：5 份 / 114,811 B / 882 行（加本 README 共 6 份 / 123,594 B）。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `bi/` 那一行标 ❌）。这是它的域入口。

---

## 一、先读这一条，否则一定误判

**本目录里"0 条"和 registry 里 5 条 `udc.bi.*` 同时成立，不是矛盾。**

| | 版本单元 | 判定 |
|---|---|---|
| `bi-vacuum-contract.md` / `bi-boundary-conclusion.md` §2 | **5.3.517**（UDC 六个 jar） | 真 BI 只读契约 **0 条**（VACUUM） |
| `registry-entries.md` **末尾追加节** | **5.3.260**（`boot-starter-ganttchart`） | **5 条**，全部已落库 |

实测（2026-11-07）：`registry.py` 里 `udc.bi.*` 恰好 **5 条**，正是 5.3.260 那节列的 5 个 op_id，
`method` / `path` 与文档**逐字一致**。

⇒ 看到"本域 0 条"就去 registry 里数出 5 条、然后判定文档过期 —— **这是错的**。
两个版本单元**物理分开、禁混写、禁互推**，每个文件头都单独声明了这一点。

---

## 二、五份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `ganttchart-5.3.260-coverage.md` | 36,594 | 298 | 覆盖核对（读写） | Gantt 面 5.3.260 的**读写覆盖核对**，含 `jar_sha256` 实测复现 |
| `bi-vacuum-contract.md` | 28,140 | 120 | **负证据契约** | 5.3.517 域真空（VACUUM）的三层口径 + 7 要素负证据形式 |
| `bi-boundary-conclusion.md` | 24,763 | 246 | **归属结论**（唯一业务产出） | 三方分离地图：UDC 域 / Gantt 面 / `cdp-bi` 子应用面 |
| `ganttchart-5.3.260.md` | 13,395 | 86 | 只读契约（5 条 7 要素） | Gantt 面独立版本单元的 5 条只读候选 |
| `registry-entries.md` | 11,919 | 132 | 落库清单 | 正文 = 5.3.517 真空；**末尾追加节 = 5.3.260 的 5 条**（见 §三） |

合计 **114,811 B / 882 行**（含本 README 时不适用——上表只算 5 份）。

---

## 三、`registry-entries.md` 又写着"由 UDC-MERGE 照抄"——**5/5 已落库**

它第 5 行：「**本域不新增任何 UdcOperationContract 条目（0 条）**，由 UDC-MERGE 任务照抄本文件。」
末尾追加节又写「本节**不实际修改 `registry.py`**（冻结件）」。

**这是 2026-10 的事实，现在是过去时。** 实测 5/5 全部已在 `registry.py`，且：

| op_id | method | path |
|---|---|---|
| `udc.bi.ganttchart_running_dynamic_select_by_entity` | POST | `gantt-chart/dynamic-select-by-entity` |
| `udc.bi.ganttchart_schema_select_by_id` | POST | `gantt-chart-schema/select-by-id` |
| `udc.bi.ganttchart_schema_select_by_code` | **GET** | `gantt-chart-schema/{code}` |
| `udc.bi.ganttchart_schema_search_list` | POST | `gantt-chart-schema/search-list` |
| `udc.bi.ganttchart_schema_search` | POST | `gantt-chart-schema/search` |

（注意 `select_by_code` 是唯一的 **GET**，其余四条是 POST。照抄时容易一律写 POST。）

⇒ **别把本域当待办。** 但正文那个「0 条」也**不要删** —— 它是 5.3.517 单元的正式结论，
删了会丢掉"UDC 域内没有 BI"这条完备负证据。

---

## 四、本目录最值钱的东西：三方分离地图

`bi-boundary-conclusion.md` §1 把三件事画成三列，并明写：

> 三列是**三个不同的业务面**，不是同一个「BI 模块」的三个子系统。
> 任何跨列合并（如"UDC 有 Gantt 所以 UDC 有 BI"）都是**错误建模**。

| 维度 | UDC 域（5.3.517 六 jar） | Gantt 面（`boot-starter-ganttchart` 5.3.260） | BI 子应用面（`cdp-bi` / `cdp-data`） |
|---|---|---|---|
| 真 BI 端点 | **0 条**（VACUUM） | 16 条（只读 5 / 写形态 9 / 副作用 2） | 报表中心读路径 3 接口 + 管理面/大屏面另有 LIVE |
| 落库 | 无 BI 表 | `gantt_chart_schema`（starter 自有，15 列） | `cdp_data_test2` 内 7 张 `cdp_bi_*` + `cdp_big_screen_model_rel` |
| 与 UDC 的连接 | —（自身即域） | `app_guid` 列 = **数据层引用**，非表归属 | **无表级耦合**，仅门户菜单挂载 |
| 定级 | VACUUM（完备负证据） | STATIC 覆盖 / LIVE 未达 | LIVE（落点、菜单、页面、后端归属均实测） |

**这张表的实际用法**：有人问"UDC 能不能做 BI"时，
答"能，但不在本域"——走标品侧 `cdp-bi`/`cdp-data`；要甘特图走 Gantt 面。
**两条路都不在本域新建 BI 契约。**

---

## 五、"0 条"是怎么证明的（负证据的写法）

VACUUM 不是"没找到"，是**完备负证据**。三层口径 + 双口径互证：

| 层 | 口径 | 覆盖量 | 结果 |
|---|---|---|---|
| L-A 类名层 | 1217 class FQCN × 13 BI 关键词宽口径子串 | 1217 class | 真 BI = **0**（唯一 `bi` 子串 29 条全是 `biginteger`/`bill`/`biz`/`scalability`/`combination`/`compatibility` + `BiLinkedList`） |
| L-B 端点路径字面量层 | **219 行逐条判定**（35 类级 + 184 方法级） | mapping-bearing 类 **38** 个 | CANDIDATE = **0**；PSEUDO-EXCLUDED = 4（`stat` 词干被 `state`/`status` 包含） |
| L-C 常量池全量层 | 1217 类全部常量池 Utf8（含中文）BI 词干扫描 | 1217 class | 命中 84 条，**属 mapping-bearing 类的 = 0** |
| 双口径一致性 | 自实现常量池/注解解析 vs `javap -p -v` 解码文本 | 38/38 类 | **mismatch = 0** |

**"完备"是怎么论证的**（这段是负证据的写法范本）：
- L-B 覆盖全部 mapping-bearing 类，无缺口
- `@RestController` 35 个全在 bearing 集内
- bearing 38 − 35 = 3 个无 stereotype 基类已计入端点表
- bearing 类中 `@interface` = 0（实测）→ **不存在自定义 meta-annotation 声明映射的盲区**
- 筛类必须按**映射注解描述符**，按 `@RestController` 筛只有 35 类、**会漏 53 行端点**

⇒ 负证据要能回答"你怎么知道你找全了"。这四条就是答案。

---

## 六、拿不到什么

- **UDC 域内的 BI 端点** —— 不存在。别在本域找。
- **Gantt 的运行态读写** —— LIVE 读=0、写=0，4 项前置条件维持 **UNVERIFIED** 收口。
  `ganttchart-5.3.260-coverage.md` 明写「本件性质：只读覆盖核对。**不落任何写操作契约为可执行**」。
- **`cdp-bi` 的契约** —— 本域没有。它在标品侧，本仓库未建契约。
- **网关 service 前缀** —— 三条 `verification_rules` 都写着「网关 service 前缀 UNVERIFIED（离线不可确证，**禁止拼前缀**）」。
  registry 里的 path 是控制器原值，不含 `/service/udc` 之类前缀。

---

## 七、两个证据单元（禁混写）

| 单元 | 版本 | 构件 | 出现于 |
|---|---|---|---|
| UDC 六 jar | **5.3.517** | `local-maven-53517` | 2 份（真空 + 边界结论） |
| Gantt starter | **5.3.260** | `boot-starter-ganttchart-5.3.260.jar`（272,340 B，`jar_sha256 = a9886378…cdbde`） | 2 份（契约 + 覆盖核对） |

`ganttchart-5.3.260.md` 头注原文：

> 本文件所有证据**仅适用 5.3.260**；与 `bi-vacuum-contract.md`（5.3.517 单元，判定 = VACUUM，维持不变）
> 是两个物理分开的证据单元。

⇒ **任何数字都不得跨单元推论。** 5.3.260 的 16 条端点不能用来反证"UDC 有 BI"。

---

## 八、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| BI 该不该在本域建契约、该走哪条路 | **本层**（`bi-boundary-conclusion.md`） |
| 某条 `udc.bi.*` 的入参/返回/证据 | **本层**（`ganttchart-5.3.260.md`） |
| 甘特图表在运行态怎么被读写 | `core/facts/udc/`（Gantt 面属 ganttchart starter，UDC 侧只有 `app_guid` 数据引用） |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

---

## 九、证据都在哪

| 内容 | 路径 |
|---|---|
| 端点全量表 + 逐类 provenance（106 KB） | `docs/audit/artifacts/udc-bi-5.3.517/bi-endpoint-literal-scan.md` |
| 可复跑脚本（6 个） | `docs/audit/artifacts/udc-bi-5.3.517/r1_scan_mapping_bearing.py` / `r1_extract_endpoints.py` / `r1_javap_dump.py` / `r1_completeness_checks.py` / `r1_build_report.py` / `r1_bi_judge.py` |
| 原始计数（5 个 json） | 同目录 `r1_step1_raw.json` … `r1_step5_completeness.json` |
| 38 个 javap 全文 | 同目录 `r1-<Class>.javap.txt` |
| Gantt 面证据 | `docs/audit/artifacts/udc-bi-5.3.260/`（`p2/`、`jar 内 ddl/starter_info`、`three_way_compare`） |

**复跑注意**：`javap` 必须带 `-J-Dstdout.encoding=UTF-8`；筛类必须按**映射注解描述符**。
