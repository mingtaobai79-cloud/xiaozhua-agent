# runtime 域契约层（`docs/operation-contracts/udc/runtime/`）

> **UTD 契约层的 runtime 域**：3 份 / 39,816 B / 320 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> **本目录此前零入口**（上级总表里 `runtime/` 那一行标 ❌）。这是它的域入口。
> 证据单元：`udc-starter-runtime-5.3.517.jar`（`jar_sha256 = 74ae50bd…40a66f`）。

---

## 一、本域 13 条**全部未落库**——这是全库唯一一个整域 pending 的目录

| 组 | 条数 | 内容 |
|---|---:|---|
| **A 组** runtime 原生面 | 7 | 环境检查 5（`env_check_*`）+ 前端函数支持 1 + GraphQL 代理 1 |
| **B 组** 跨域词干重叠 | 6 | `applog` 4 条 + `serial.config_list` 1 + `jar_import_status` 1 |

实测（2026-11-07）：13 条的 **op_id 与 path 在 `registry.py` 里都是 0 命中**，
`udc-runtime/evn-check/*` 更是**一条都没有**。
这与其余 13 个子域都不同（它们至少部分落库）。

⇒ **别把本目录当"已完成"**。它是**唯一一个"13 条建议全部待落"的域**。
⇒ 与此同时它也是**证据最完整的一个**：`docs/audit/artifacts/udc-runtime-5.3.517/`
有 **76 份文件**（含 5 个可复跑脚本 + 3 层扫描 JSON + 33 份 `javap` 全文），
`r2_registry_key_check.txt` 逐条记着 `id_hits=0 path_hits=0`。

### 它自己写了"这个 0 命中会过期"

> ⚠ 盘面漂移警示：上述 0 命中基于本轮实测 registry.py（运行态 **76 键**）。
> MERGE 落库前必须对当时 registry.py **重新实测 key 唯一性**。

⇒ 这句话是**正确做法**：把"实测时点"和"会漂移"都写进来。
⇒ 本轮复核时 registry 已是 **117 条契约**（含 `write=True` 25 条），**远多于当年的 76 键** ——
所以"0 命中"这个结论**必须重测**，不能沿用。
本轮重测结果：**13 条仍然 0 命中**（`evn-check` 段整段为空）。

---

## 二、⚠️ B 组有 4 条是"同族内补齐"，不是新概念

这是本域最容易漏看的一层。看 registry 里 `app-log` 的现有条目：

| registry 现有 | 路径 |
|---|---|
| `udc.applog.search_microflow` | `udc-runtime/app-log/search/microflow` |
| `udc.applog.search_details_microflow` | `udc-runtime/app-log/search-details/microflow` |
| `udc.applog.search_details_microflow_flowlog` | `udc-runtime/app-log/search-details/microflow/flowLog` |

而 B 组建议的是**同一族的另一半**：

| 建议条目 | 路径 |
|---|---|
| `udc.applog.search_dataflow` | `udc-runtime/app-log/search/dataflow` |
| `udc.applog.search_dataflow_details` | `udc-runtime/app-log/search-details/dataflow` |
| `udc.applog.search_deduction` | `udc-runtime/app-log/search/deduction` |
| `udc.applog.search_deduction_details` | `udc-runtime/app-log/search-details/deduction` |

⇒ **microflow 三条已落库，dataflow/deduction 四条没有。** 同一控制器、同一 URL 族、只差一个分母词。
⇒ 这不是"新域"，是**前一批合并只做了三分之一**。
⇒ 同样：`udc.serial.select_entity_list` 与 `select_entity_by_serial` 已落库，
建议补的 `udc.serial.config_list`（`serial-config/list`）是同一控制器的第三个端点。
`udc.jar.download` / `export_app` 已落库，建议补的 `jar_import_status`
（`dynamic/jar/import/status/{requestId}`）是同一控制器的状态查询。
⇒ **判据：看到"0 命中"要先问一句"它的兄弟端点落库了吗"。**
兄弟落了、它没落 —— 那是**遗漏**；兄弟全都没落 —— 那才是"这一族还没开始"。

---

## 三、三层扫描 + registry 全键差分：本域最可复用的方法论

`runtime-domain-scan.md` 用的不是"搜关键词"，是**五步差分**：

| 层 | 做什么 | 实测数 |
|---|---|---:|
| **Layer A** 类名层 | `jar tf` 全枚举 + 类名扫描 | 346 class entries / **307** 顶层类 / **19** udcrt controller / **11** proxy controller |
| **Layer B** 映射注解层 | 按**映射注解描述符**筛类（不是按 `@RestController`） | **27** mapping-bearing 类 / 24 类级映射声明 / **131** 带映射方法 / **133** 展开后端点行 |
| **Layer C** 常量池层 | 全部类常量池 Utf8（含中文）斜杠字面量扫描 | **346** 类 / **38,646** Utf8 / **47** distinct 斜杠字面量 |
| **差分** | 133 端点行 vs registry 全键 | 已覆盖去重 **27** / **零命中 106** / 读 **37** / 写 **50** / R7R8 排除 **8** / 人工排除 **11** |

### 关键一步：Layer C 的独立价值

> `lC_only_literals_not_in_lB` = `/package.json`(1) / `/proxy/`(1) / `/app/lock/.lock`(1)

**只有 3 条常量池字面量不在映射注解层里，且全都不是端点。**
这正是"**B 层已经够了**"的证明——不是"我觉得够了"，是**用 C 层反证 B 层无遗漏**。
⇒ 这是负证据的正确形状：**用独立口径互证，而不是重复同一口径**。

### 关键判据：筛类必须按映射注解描述符

`Layer A` 得 19 个 `udcrt` controller，但 `Layer B` 得 27 个 mapping-bearing 类。
差 **8 个** —— 是**无 `@RestController` 但有类级/方法级映射**的类。
按 `@RestController` 筛会**漏掉这 8 个类里的端点**。
⇒ 这条已在 BI 域（方法论）出现过一次，这里是第二个实证。

---

## 四、`.effective` 门控：本域同样有 POST 只读被漏的风险

`registry-entries.md` 的门控提示原文：

> A1–A4、B6 为 `GET` + `write=False` → `.effective()=True`；
> A5–A7、B1–B5 为 `POST` 只读（`write=False`）→ `.effective()=False`
> （与 page/flow 域 POST 只读**同一门控事实**，MERGE 须走与普通只读 POST 相同的 auth_scope 通道）。

逐条对应：

| `.effective` | 条数 | 条目 |
|---|---:|---|
| **True** | **5** | A1 `build_info` / A2 `app_version` / A3 `data_permission` / A4 `response_length`（均 GET）+ B6 `jar_import_status`（GET） |
| **False（POST 只读）** | **8** | A5 `request_content` / A6 `function_support_calculate` / A7 `graphql_proxy_graphql` + B1–B5（`applog` ×4 + `serial.config_list`） |

⇒ **13 条里 8 条会被 `.effective` 判成 False。** 按 `.effective` 筛只读会漏掉一大半。
⇒ 判据同 flow 域：**筛只读用 `write=False`，不要用 method，更不要只信 `.effective`。**

---

## 五、三份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `registry-entries.md` | 15,655 | 88 | **13 条建议条目**（主文档） | A/B 两组分组 + 门控提示 + 盘面漂移警示 |
| `runtime-domain-scan.md` | 15,407 | 145 | **差分扫描方法论** | 三层扫描 + registry 全键差分，含各层实测计数 |
| `runtime-readonly-contracts.md` | 8,754 | 87 | 扫描结论与候选 | 只读候选的字段级定义与排除理由 |

合计 **39,816 B / 320 行**（含本 README 时不适用——上表只算 3 份）。

---

## 六、⚠️ 顺带查出 registry 里一处拼写缺陷（不属本域，只记录）

`registry.py` 里有 **`udc-runtime/data//query`（双斜杠）**：

| op_id | path |
|---|---|
| `udc.entity_data.query_form_data` | `udc-runtime/data//query` ← **双斜杠** |
| `udc.flow.form_data_query` | `udc-runtime/data/query` ← 单斜杠 |

**同一控制器、同一端点，两个 op_id、两个 path，其中一个多一个斜杠。**
这是第 41 轮查出的"同路径重复注册"之外**另一种形态**：**拼写不一致导致按 path 查重查不出来**。
⇒ 说明**按 path 查重前要先归一化**（去掉重复斜杠），否则这种缺陷会一直漏。
⇒ **不属文档整理范围**，已记入待裁决。

---

## 七、拿不到什么

- **LIVE 回读** —— 本域全部 `VERIFIED_STATIC_BYTECODE`，0 次 LIVE。
- **网关 service 前缀** —— 每条 `verification_rules` 都写「网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）」。
- **B 组的最终域段归属** —— 文件明写「最终域段归并交 MERGE 裁定」，本域只给建议。
- **R7R8 排除的 8 行** —— 属 proxy 层，与微流程域合并裁定（同 flow 域）。
- **那 13 条进不进 registry** —— 属策略决定，未授权。

---

## 八、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 13 条建议的入参/返回/`write`/evidence | **本层**（`registry-entries.md`） |
| 怎么扫一个域才不遗漏（可复用方法） | **本层**（`runtime-domain-scan.md` 三层 + 差分） |
| 哪些条目 `.effective` 会是 False | **本层**（§四） |
| runtime 域在运行态怎么跑 | `core/facts/udc/` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

---

## 九、证据在哪

`docs/audit/artifacts/udc-runtime-5.3.517/`（**76 份**）：

| 类别 | 文件 |
|---|---|
| 可复跑脚本 | `r2_scan_runtime.py` / `r2_flatten.py` / `r2_diff.py` / `r2_layerAC.py` / `r2_classify.py` / `r2_report.py` / `r2_verify.py` / `r2_dryrun.py` / `r2_javap_dump.py` / `r2_sig.py` |
| 扫描结果 | `r2_layerA_classname_scan.json` / `r2_layerC_constantpool_scan.json` / `r2_endpoints_raw.json` / `r2_endpoints_flat.json` / `r2_classified.json` / `r2_diff.json` / `r2_candidates.json` / `r2_staged_manifest.json` / `r2_javap_manifest.json` |
| 结论 | `r2_summary.json` / `r2_registry_key_check.txt` / `r2_registry_entries_dryrun.txt` / `r2_MANIFEST.txt` |
| `javap` 全文 | 33 份 `r2-*Controller.javap.txt` 等 |
