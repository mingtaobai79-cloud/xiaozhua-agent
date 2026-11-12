# docs/ledger/ 索引

## 这个目录是什么

**归档区。这里没有一份是"现行结论"。**

7 份 / 398,965 B / 3,463 行，按四个前缀分四类：`LOG-` 逐字归档、`DIGEST-` 压缩续接、
`RESUME-` 断点交接、`STATUS-` 时点快照。**看到这四个前缀，就不该把它当现状引用。**

现状去哪看：

- 文档整理线 → `docs/plans/doc-consolidation-progress.md`
- 分发线 → `docs/plans/xiaozhua-distribution-progress.md`
- 现在盘上有什么 → `docs/ARCHITECTURE.md`、`docs/REPO-LAYOUT.md`

> **为什么 `docs/README.md` 写着"`ledger/` 没有入口是刻意的"？**
> 那条决定的意图是：归档区不当导航起点，读者应先看 `plans/` 再看具体归档件。
> 本 README 不与该意图冲突——它只解决一件那条决定没覆盖到的事：
> **四个前缀各是什么意思、哪份是"某个时点的断言"、迁出件的现行版在哪。
> 这三件事此前没有地方写**（`plans/` 三份卡片只在提到具体文件时顺带指路，
> 没有一处解释 `DIGEST-` / `RESUME-` / `STATUS-` 的性质）。
> 所以本文件是**归档件的命名与用法图例**，不是 `docs/ledger/` 的导读入口。

## 一、7 份一览（2026-11-07 实测，按字节降序）

| 文件 | 字节 | 行 | 时间跨度 | 性质 |
|---|---:|---:|---|---|
| `LOG-udc-semantics-PROGRESS-20261014-20261016.md` | 181,401 | 1,579 | 2026-10-13 → 10-16 | 迁出的逐字全文（原 `docs/audit/udc-semantics/PROGRESS.md`） |
| `LOG-distribution-20261020-20261107.md` | 71,924 | 159 | 2026-10-20 → 11-07 | 迁出的逐字全文（原 `docs/plans/xiaozhua-distribution-progress.md`） |
| `STATUS-2026H2.md` | 62,920 | 449 | 2026-09-22 → 10-08 | **时点快照**：适配器切片收口（自称 HEAD `16a384c`） |
| `LOG-doc-consolidation-20261107-rounds1-15.md` | 43,853 | 678 | 2026-09-03 → 11-07 | 迁出的逐字全文（第 1–15 轮，倒序） |
| `DIGEST-2026-10-22-setting-close-to-app.md` | 27,615 | 403 | 2026-10-21 → 10-22 | 上下文压缩续接件（源会话 `20261021_234751_d68325`） |
| `DIGEST-2026-10-21-setting-domain.md` | 7,473 | 127 | 2026-10-21 | 上下文压缩续接件（设置域 8 tab） |
| `RESUME-2026-10-23-entity-rule-condition.md` | 3,779 | 68 | 2026-10-22 → 10-23 | 单会话断点交接（模型响应超时被掐断） |
| **合计** | **398,965** | **3,463** | | |

## 二、四个前缀分别是什么意思（这份 README 的主要价值）

### `LOG-*`（3 份，297,178 B）——逐字迁出，考证用

从入口文件里**逐字迁出**的流水账，迁出时正文未改写、只加一条头注（迁出时点、原文规模、迁出原因）。

- 用途：回答"某轮到底改了什么、为什么、测试跑出什么数"。
- 三份的现行版入口：
  - `LOG-udc-semantics-PROGRESS-…` → `docs/audit/udc-semantics/PROGRESS.md`（只留当前结论 + 阻塞）
  - `LOG-distribution-…` → `docs/plans/xiaozhua-distribution-progress.md`
  - `LOG-doc-consolidation-…rounds1-15` → `docs/plans/doc-consolidation-progress.md`
- ⚠️ **不要拿 `LOG-*` 当依据**：它记的是当时的状态。

### `DIGEST-*`（2 份，35,088 B）——上下文压缩后的续接件

只记"下一轮开局必须知道的东西"：目标、规矩、已完成、缺口、下一步。细节一律指向
仓内事实格/契约/skill，不复制。

- ⚠️ 两份有重叠：`DIGEST-2026-10-21-setting-domain.md` 是**单日快照**，
  `DIGEST-2026-10-22-setting-close-to-app.md` 是它的续接。**读后一份即可。**

### `RESUME-*`（1 份，3,779 B）——断点交接，删了就找不回

文件自己写明：存在的唯一目的是**让那个被中断的会话能被重新找回并接上**，
且"会话标题是旧主题留下的，按标题搜不到，只能按 ID 或本文件"。
里面那串 64 位会话 ID 是全库唯一的找回凭据。

### `STATUS-*`（1 份，62,920 B）——时点快照，最容易误导

2026-09-26 的适配器切片收口快照，自称 HEAD `16a384c`。
★ **它是本目录唯一一份"断言过某状态达成"的文件，也正因如此最容易误读。**

2026-11-07 实测对照：

| 文中说 | 现在 |
|---|---|
| 目标 `adapters/hermes`、`adapters/codex`、`adapters/claude-code` | **真的存在**（当时在建） |
| `installer/INSTALL-MANIFEST.md` | 存在 |
| `main/_s6_pytest_raw.txt` | **已不存在** |
| `evidence/bytecode/`、`META-INF/services`（相对路径） | 按文中基准解析不到 |

**按"时点快照"读，不要按"当前状态"读。** 要现状看 `docs/ARCHITECTURE.md`。

## 三、维护规则

1. **新流水优先迁到这里，不要往入口文件里追加。** 入口只放当前结论——
   这是 P5「流水账收束」的结论，`LOG-*` 三份就是这条规则的产物。
2. **迁入必须逐字保留正文**，只在头部加说明（迁出时点、原文规模、迁出原因、现行版在哪）。
   改正文会让"当时的记录"失去证据价值。
3. **不要因为这个目录"零代码引用"就删文件。** 已核对：16 处文档引用本目录路径
   （`docs/audit/udc-semantics/PROGRESS.md`、`docs/plans/*`、`skills/…fact-protocol/SKILL.md` 等）；
   `RESUME-*` 的会话 ID 是全库唯一找回凭据。
4. **文件名前缀是契约**：新件继续用 `LOG-` / `DIGEST-` / `RESUME-` / `STATUS-`，
   **不要引入第五种前缀**，并在本表登记。

---

维护：新增/删除任何一份都必须同步 §一 表的份数、字节、行数与合计
（`tests/udc/test_ledger_layout.py` 会核对）。
