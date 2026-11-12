# 实体域契约层（`docs/operation-contracts/udc/entity/`）

> **UTD 契约层的实体域**：5 份 / 65,038 B / 1,034 行。
> 上级入口：`docs/operation-contracts/udc/README.md`（14 子域总表）。
> 与**事实层** `core/facts/udc/entity/` 是两件事：那个记"它实际怎么动"，这个记"它允许怎么被调"。
> **本目录此前零入口**（上级总表里 `entity/` 那一行标 ❌）。这是它的域入口。

---

## 一、先读这一条：16 条**全部落库**，但 3 条换了名字

`registry-entries-code.md` 的 16 条只读契约，按 **op_id 字面量** grep `registry.py` 只命中 **13/16**，
看上去"缺 3 条"。**按路径再查一遍，16/16 全在。**

| 文档里写的 op_id | registry 里实际叫 | method / path |
|---|---|---|
| `udc.applog.select_app_data_by_id` | `udc.applog.select_by_id` | GET `udc-runtime/app-log/datalog/{id}` |
| `udc.page.check_exists` | `udc.page_info.check_exists`<br>**也** `udc.metadata.page_exists_check` | POST `udc-runtime/meta-data/check-page-exists` |
| `udc.page.select_host_only_pages` | `udc.page_info.select_host_and_only_page`<br>**也** `udc.metadata.page_tree` | POST `udc-runtime/meta-data/select-host-and-only-page-pages` |

实测（2026-11-07）：三对（后者实为两对双别名）的 **method 与 path 与文档逐字一致**。

⇒ **判"落没落库"必须拿 path 再核一遍，不能只比 key 字符串。**
⇒ 顺带：这两条路径各被注册了**两次**（`udc.page_info.*` 与 `udc.metadata.*` 各一份）。
名字与路径的语义也对不上（`metadata.page_tree` 配的是 `select-host-and-only-page-pages`）。
**这是 registry.py 自己的重复注册问题，不属文档整理范围，已记入进度文件待裁决。** 本目录不动它。

---

## 二、五份一览（按字节降序）

| 文件 | 字节 | 行 | 性质 | 一句话 |
|---|---:|---:|---|---|
| `registry-entries.md` | 21,342 | 390 | **主文档** | 实体域 registry 建议条目 + 降级登记（本文档体系里 P3 合并的**完成样本**） |
| `registry-entries-code.md` | 20,456 | 306 | ⚠️ **已降级** | 原"可直接粘贴代码块"中间件；头部已写明「已并入 `registry-entries.md`，保留作历史」 |
| `entity-readonly-contracts.md` | 15,364 | 223 | 只读契约（16 条 7 要素） | 证据等级 VERIFIED_STATIC_BYTECODE；**未拼网关前缀**，前缀本身 UNVERIFIED |
| `registry-merge-handoff.md` | 4,426 | 71 | 移交索引（已过期） | 「UDC-MERGE 的**单一入口**」——MERGE 已结束 |
| `PRE-MERGE-GATE-R7-report.md` | 3,450 | 44 | 离线 gate 报告（已过期） | MERGE 照抄入库前最后一道 6 项复测 |

合计 **65,038 B / 1,034 行**（含本 README 时不适用——上表只算 5 份）。

---

## 三、P3 合并的完成样本：本目录已经做过一次

这个目录是本仓库**唯一一处把「重复文档降级」按标准做法走完的**，值得当范本：

1. 内容并入主文档 —— `registry-entries-code.md` 的代码块已落入 `registry.py`，
   条目本体在 `registry-entries.md`（390 行 vs 306 行）
2. **原文件头部加一行指针** —— 该文件第 3–5 行写着
   「⚠️ **已并入** `registry-entries.md` …保留作历史记录，**不再作为入库依据**」
3. **主文档补反向指针** —— `registry-entries.md` §0 写了「本文件是**主文档**」并指向 code 变体

⇒ **三件事都做齐了，才叫"降级"。只加 superseded、不补反向指针，读者从主文档看不出还有个变体。**
⇒ 本目录这一处是正确做法，**不要再去"清理"那份 code 文件** —— 它是 P3 的留痕。

---

## 四、三份"照抄入库"的文件都已过期

`registry-entries.md` / `registry-entries-code.md` / `registry-merge-handoff.md` / `PRE-MERGE-GATE-R7-report.md`
四份都带「供 UDC-MERGE 照抄」「照抄入库」「单一入口」「冻结 registry.py」这类措辞。

**UDC-MERGE 已经执行完了。** 实测 16/16 全部落库（见 §一）。

| 文件 | 里面的措辞 | 现在的事实 |
|---|---|---|
| `registry-merge-handoff.md` | 「本文件是 UDC-MERGE 会话照抄入库的**单一入口**」 | MERGE 已结束，入口失效 |
| `PRE-MERGE-GATE-R7-report.md` | 「UDC-MERGE 照抄入库前**最后一道**离线 gate」 | gate 已过，报告留痕 |
| `registry-entries-code.md` | 「供 UDC-MERGE 任务把本块粘贴进 registry.py」 | 已粘贴完（且已自我降级） |
| `registry-entries.md` | 「不改冻结 registry.py」 | registry.py 已改完 |

⇒ **别把它们当待办。** 看到"供 X 照抄"必须去消费方实测（这条已是本系列方法论第 9 条）。
⇒ 但这四份**都不要删** —— 它们是"16 条各自凭什么这样构造"的构造依据，
删了 `registry.py` 里那 16 条就只剩结论没有推导。

---

## 五、`entity-readonly-contracts.md` 里两条硬约束

### ① 路径逐字照 javap 常量，**未拼网关前缀**

> 控制器路径逐字照 javap 常量，**未拼网关前缀**；网关 service 前缀是否真实存在=UNVERIFIED
>（本任务不连网关，不做推断）。

所以 registry 里那 16 条的 `path` 是 `udc-runtime/...`，**没有** `/service/udc` 之类前缀。
看到路径"短了一截"不是漏写，是**故意不拼**。

### ② 两个版本单元禁混写

> 版本单元: 本地 Maven **5.3.517**（勿与 test2 镜像 **5.3.496** 混写）

这一域的证据全部来自 5.3.517 的 `javap -p -v` + SHA-256，**0 次 LIVE**。
`5.3.496` 的运行态行为不能拿 517 的字节码结论去推。

---

## 六、拿不到什么

- **网关 service 前缀** —— UNVERIFIED。文件明确"本任务不连网关，不做推断"。
- **LIVE 回读** —— 本目录 0 次 LIVE。16 条全部 `VERIFIED_STATIC_BYTECODE`。
  想找"实际调通了没有"要去事实层 `core/facts/udc/entity/`。
- **写面契约** —— 16 条全部 `write=False`。实体域的写面不在本目录。
- **`udc.metadata.*` 那两条别名的来由** —— 本目录没有解释。它们在 registry 里，
  但不在任何一份 `registry-entries*.md` 里。**来路不明，已记待裁决。**

---

## 七、与事实层怎么分工

| 想知道 | 去 |
|---|---|
| 这 16 条 op_id 的入参/返回/证据等级 | **本层**（`entity-readonly-contracts.md` 7 要素） |
| 它们凭什么这样构造（evidence dict / 字段签名） | **本层**（`registry-entries-code.md`） |
| 实体域五处「静默成功」坑（`BOOT_0000` + DB 有行 + 页面 0 条且不报错） | `core/facts/udc/entity/` |
| 实体域的写链与 DTO 约束 | `core/facts/udc/entity/` + `core/facts/udc/write-chain/` |
| 本层在 14 个子域里的位置 | `docs/operation-contracts/udc/README.md` |

---

## 八、证据在哪

`docs/audit/artifacts/udc-entity-5.3.517/`（`MANIFEST.md` 为索引，含各 `javap -p -v` 全文与 class SHA-256）。
`entity-readonly-contracts.md` 头注指向该目录。
