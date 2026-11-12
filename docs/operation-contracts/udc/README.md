# docs/operation-contracts/udc/ 索引（UDC 各域操作契约）

## 这个目录是什么

**UDC 各业务域的操作契约层**：14 个子域、**81 份 / 1,153,874 B**（2026-11-07 实测，**含各子域自己的 `README.md`**）。
每份契约回答「端点叫什么、参数必填什么、返回什么形状、证据强度到哪」。

⚠️ **本目录此前没有入口**（只有 2026-10-18 的 `C-GROUP-OVERVIEW-20261018.md`，只覆盖
column/setting/role 三域）。14 个子域里只有 3 个有自己的 `README.md`，其余 11 个靠本文件导航。

## 一、14 个子域一览（2026-11-07 实测）

> **口径**：本表「份 / 字节」是**各子域顶层** `*.md`，**含该子域自己的 `README.md`**，
> **不递归**子目录。这条必须写明，因为同一个 `microflow/` 在另一处有两种数：
>
> | 出处 | 份 | 字节 | 口径 |
> |---|---:|---:|---|
> | **本表** `microflow/` | 14 | 250,405 | 顶层，含 README |
> | `core/facts/udc/README.md` 位置表 | 25 | 277,632 | **递归**，含 `live-evidence/` 下 11 份 |
>
> **两个都对**，差的是 `live-evidence/` 那 11 份。跨文件对比时别把一个当成另一个的错。

| 子域 | 份 | 字节 | 入口 | 一句话职责 |
|---|---:|---:|---|---|
| `microflow/` | 14 | 250,405 | ✅ `README.md` | 微流程：三份大契约（map-node / state / runtime-engine）+ 节点普查 + 字段语义 |
| `column/` | 4 | 140,288 | ✅ `README.md` | 栏目（column）写链 + 枚举 + 自检记录 |
| `application/` | 8 | 132,690 | ✅ | 应用域：外层/内层只读契约、部署信息、在线状态。★ 域入口 = `application/README.md`——查出 `udc.deployment.*` 命名空间在 registry.py 里**不存在**，且 `registry-entries.md` 的「供照抄」已 5/5 落库 |
| `bi/` | 6 | 123,594 | ✅ | BI 域：**5.3.517 真空（0 条）+ 5.3.260 Gantt 5 条**，两单元禁混写。★ 域入口 = `bi/README.md` |
| `setting/` | 12 | 88,870 | ✅ `README.md` | 设置域 11 个 tab 契约 + 发布链 runbook |
| `entity/` | 6 | 72,058 | ✅ | 实体域：16 条只读契约（**按 path 核实 16/16 全落库**，3 条换了名字）。★ 域入口 = `entity/README.md`（P3 降级完成样本） |
| `flow/` | 5 | 60,833 | ✅ | 流程域(BPM 集成)：12 条建议 → **8 落库 / 1 去重归一 / 3 写侧未落**。★ 域入口 = `flow/README.md`（含 `.effective` 门控表：6 条 POST 读型会被判 False） |
| `page/` | 3 | 54,370 | ✅ | 页面规则域：8 条建议 → **5 落库 / 2 故意不落 / 1 待定**。registry 里有**唯一一条占位符 path**（`<BASE-UNRESOLVED-in-5.3.517>`）。★ 域入口 = `page/README.md` |
| `role/` | 2 | 54,998 | ✅ | 角色域：15 端点完整契约。**唯一一份「声称能自验且真的能自验」**（仓内一条命令复算 15/1/16）。★ 域入口 = `role/README.md` |
| `runtime/` | 4 | 49,265 | ✅ | runtime 域：**13 条建议全部未落库**（唯一整域 pending），但证据最全（76 份）。★ 域入口 = `runtime/README.md`（含三层扫描+差分方法论） |
| `menu/` | 8 | 42,465 | ✅ | 菜单域：**UDC 里没有 menu 类**（6 jar × 5 关键词=0 命中），5 条契约全是借来的。★ 域入口 = `menu/README.md`（含 13 条「GET 其实是写」排除项） |
| `resource/` | 3 | 35,462 | ✅ | resource 域：5/5 全部落库且证据一致——**「落库成功」的样板**。写形态 5 条是**明确排除**不是遗漏。★ 域入口 = `resource/README.md` |
| `publish/` | 3 | 30,013 | ✅ | publish 域：**唯一「0 条新增建议」的域**（候选已被既有条目覆盖）；但 `deploy-info` 被登记**三次**（文档写两次）。★ 域入口 = `publish/README.md` |
| `rule/` | 3 | 18,563 | ✅ | rule 域：**不是端点契约域**（0 条 `contracts[...]`），描述规则节点 schema 约束，落 constraints 不落 registry；两份文件等级不同（LIVE vs UNVERIFIED）。★ 域入口 = `rule/README.md` |

合计 **14 个子域 / 81 份 / 1,153,874 B**（= 上表 14 行之和，顶层含 README）。

另有顶层 `C-GROUP-OVERVIEW-20261018.md`（19,176 B，三域总览），**不计入上表**。

> ⚠ 旧版本这里写「14 个子域 / 1,049,082 B」，那个数用的是**第三种口径**：
> 各子域顶层**不含** README（67 份 / 1,029,907 B）**加上**顶层那份总览（19,176 B）
> = 1,049,083 B。它和逐行的「含 README」不是一回事，所以逐行全对、合计却是错的。
> 第 68 轮统一成「含 README」，不再叠加顶层总览。

## 二、★ 9 份同名 `registry-entries.md` 的判断口径（最易误读）

9 个域各有一份 `registry-entries.md`，全部写着「供 **UDC-MERGE** 任务照抄进
`components/platform_operations/registry.py`；本任务不改 registry.py」。

**这句话是 2026-10 的时点状态，不是当前状态。** 实测（2026-11-07）：

| 事实 | 数值 |
|---|---|
| `registry.py` 现有契约条数 | **128** 条（`UdcOperationContract(` 出现 122 次 + 复用的 6 条） |
| registry.py 文件头部对 UDC-MERGE 的记录 | L129 / L134 / L145 / L160 四条「批 1/批 2/微批 3 照抄自 `<域>/registry-entries.md`」 |
| 9 份文档共提出的 operation_id | **42** 条 |
| 其中**已在 registry.py 中** | **37** 条（88%） |

⇒ **UDC-MERGE 已经执行过了**。这 9 份文件现在是**已落库条目的出处记录**，不是待办事项。
看到「供照抄」不要以为还没做。

### 剩余 5 条未落库，各有明确原因（不是漏做）

| operation_id | 域 | 实况 |
|---|---|---|
| `udc.applog.select_app_data_by_id` | entity | registry.py 无同名条目，最近的是 `udc.applog.list_app_data_by_dataid`（**不同端点**）。未落库原因未在文档中记录 → **UNVERIFIED** |
| `udc.page.check_exists` | entity | registry.py 里是 **`udc.page_info.check_exists`**——命名空间不同。疑为同一端点改名，**需人工确认** |
| `udc.page.select_host_only_pages` | entity | registry.py 里是 **`udc.page_info.select_host_and_only_page`**——命名空间**和**命名都不同，**需人工确认** |
| `udc.page_general.*` | page | 文档自身标注 `base UNRESOLVED-in-5.3.517，全条降级` —— **按设计未入册** |
| `udc.page_refer.*` | page | 文档自身标注「为 forward 候选，是否入册 = 独立 MERGE 决策（须 human 再授权解冻）」—— **按设计未入册** |

**判断规则**：未落库 ≠ 遗漏。先看文档自己有没有写门控注记；只有像前两条那种
「无注记且名字对不上」的，才是真缺口。

## 三、按问题找文件

| 你要找什么 | 去哪 |
|---|---|
| 微流程节点/状态语义 | `microflow/map-node-semantics.contract.md`（81,231 B）、`state-semantics.contract.md`（39,190 B）、`runtime-engine-location.contract.md`（22,136 B） |
| 栏目（column）写链 | `column/write-chain.contract.md` |
| 设置域某个 tab 的端点/必填/报错 | `setting/<tab>-contracts.md` |
| 为什么某个端点"不存在" | `flow/flow-domain-boundary-negative-evidence.md`（**负证据**，比正向契约更难重做） |
| 某个域的端点清单 | `<域>/registry-entries.md`，但先读 §二 |
| 域内还剩什么没做 | `<域>/SCAN.md`（menu）、`<域>/*-scan.md`（flow/runtime） |

## 四、本目录与相邻目录的分工（走错就白查）

| 目录 | 层级 | 回答 |
|---|---|---|
| `docs/operation-contracts/udc/`（**本目录**） | 契约层 | 端点叫什么、必填什么、返回什么形状 |
| `core/facts/udc/` | 事实层 | 实际操作长什么样、真实 body、实测坑 |
| `docs/audit/role/` | 审计层 | 这个结论是怎么推翻/更正过来的（阶段链） |
| `docs/audit/artifacts/` | 证据层 | 原始抓包/反编译产物 |

**同名目录陷阱**：`udc/setting/`（契约）vs `core/facts/udc/setting/`（事实）、
`udc/entity/`（契约）vs `core/facts/udc/entity/`（事实）、`udc/application/` vs `core/facts/udc/application/`。
**查用法去 facts，查端点来 contracts。**

## 五、不要做的事

- **不要**因为某域名下只有 1–2 份就删：`role/` 只有一份 42 KB，`publish/` `resource/` 各 2 份但各 ~25 KB。
- **不要**把 9 份 `registry-entries.md` 合并成一份：每份对应一个域、一个 MERGE 批次，
  合并会破坏 `registry.py` 头部的「照抄自哪个文件的哪一节」的追溯链（L129/L134/L145/L160）。
- **不要**直接改 `components/platform_operations/registry.py`：它是运行时消费方，
  改前先跑 `pytest tests -q`（128 条契约被大量测试引用）。
- **不要**给这 11 个无入口子域批量生成 README：按需补（哪个域在被人查，就补哪个）。
- **不要**把 `C-GROUP-OVERVIEW-20261018.md` 的 commit 号/sha256 当当前值——它是 10-18 的锁点快照。

---

维护：加子域 → §一 加一行 → 更新合计；某域补了 `README.md` → 把 §一 的 ❌ 改 ✅。
若 UDC-MERGE 又落库新条目，同步 §二 的 128 / 42 / 37 三个数（这三个数是实测，会漂）。
