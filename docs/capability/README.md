# docs/capability/ 索引

## 这个目录是什么

**目标态架构（v2）的唯一权威来源。** 一句话：不造新 Agent，把 2小爪 现有能力固化成
Agent 可调用、可验证、可兼容的 Capability，再以「可安装的 Agent 角色 + 能力包」形态
嵌入 Hermes / Codex / Claude Code 等已有宿主。

**入口顺序：先 `ROADMAP-v2.md`，再按需读 A1–A8。**

```
ROADMAP-v2.md            总路线收口（v2 架构定稿，71 行）——取代此前所有路线描述
   │
   ├─ A1 ARCHITECTURE.md            总架构图：Global / UDC 两层 + Registry 契约总线 + 宿主 Adapter
   ├─ A2 MODULE-INVENTORY.md        模块清单 01–12（现状证据量 / Capability 数 / 优先级）
   ├─ A3 CAPABILITY-MODEL.md        CONFIG / CODE 二分正式定义 + 声明格式 schema
   ├─ A4 EVIDENCE-MODEL.md          四层事实体系 + registry OperationStatus 映射归并
   ├─ A5 VERSION-COMPATIBILITY.md   Canonical 版本规范 + 差异矩阵模板（三维）
   ├─ A6 SANDBOX-CONTRACT.md        CODE 能力执行契约（Sandbox→Compile→Test→Validate→Execute）
   ├─ A7 TOOL-SKILL-MODULE.md       Tool / Skill / Module 三者定义与映射
   └─ A8 AGENT-ADAPTER.md           宿主适配规范（三层兼容模型 + v1→v2 适配契约）
STATUS.md                phase1 交付进度（**时点快照**，不是当前状态）
```

## 一、十份一览（2026-11-07 实测）

| 文件 | 编号 | 字节 | 行 | 一句话 |
|---|---|---:|---:|---|
| `ROADMAP-v2.md` | — | 3,703 | 71 | **路线基线**。七节：定位 / 目录骨架 / 能力模型 / 四层事实 / 模块推进 / 三 Agent 新职责 / 本文件即基线 |
| `ARCHITECTURE.md` | A1 | 16,843 | 228 | 两层架构 + Registry 契约总线（64 条目 = 59 基础 + 2 R18 + 3 别名，在盘实测） |
| `MODULE-INVENTORY.md` | A2 | 7,702 | 81 | 模块 01–12；UDC=P0 样板，02–12 登记 Capability 数=0 |
| `CAPABILITY-MODEL.md` | A3 | 10,204 | 115 | CONFIG/CODE 二分；CONFIG 真例 = deploy_plan 4 步逐字段 |
| `EVIDENCE-MODEL.md` | A4 | 10,231 | 131 | `STATIC → VERIFIED → LIVE → GENERATED`；`GENERATED_HYPOTHESIS` 永不进 `VERIFIED_RULE` |
| `VERSION-COMPATIBILITY.md` | A5 | 10,229 | 126 | Canonical 版本 + Capability×版本×证据等级 三维矩阵 |
| `SANDBOX-CONTRACT.md` | A6 | 9,800 | 133 | 五阶段契约；**现状 = 未建** |
| `TOOL-SKILL-MODULE.md` | A7 | 10,462 | 142 | 三者边界；Skill 首例 = deploy_plan 4 步 |
| `AGENT-ADAPTER.md` | A8 | 12,427 | 143 | 三层兼容模型；v1 五能力 → 三宿主暴露形态 |
| `STATUS.md` | — | 12,520 | 100 | phase1 交付进度 + **时点声明表** |

合计 **10 份 / 104,121 B**。

## 二、三份必须分清"哪套架构"

本仓有两套架构文档，**不是重复**：

| 文件 | 视角 |
|---|---|
| `docs/capability/ARCHITECTURE.md`（A1，本目录） | **目标架构**：要建成什么样（两层 + Registry + Adapter） |
| `docs/ARCHITECTURE.md`（仓库根 docs/） | **实现视图**：现在盘上是什么（components/core/providers 等实际目录） |

两份已加分工头注并互引，**保持互引、不互抄**。读「应该怎样」看这里，读「实际怎样」看 `docs/ARCHITECTURE.md`。

## 三、几处「层内自相矛盾」——同一份文件里，头注已更正、正文还没改

这一类错与「结论被推翻」不同：**文件开头已经写了 2026-11-07 更正，正文里却还留着旧话**。
读者如果从中间（或搜索到某一行）进入，读到的就是过期结论。

| # | 文件 | 头注说 | 正文写着（旧） | 处置 |
|---|---|---|---|---|
| ① | `AGENT-ADAPTER.md` | L9「`adapters/*`、`installer/`、`core/{role,facts,skills,tools}` **现已存在**」 | L97「…**全部在盘未建**（`ls` 实测 absent）」、L105「`installer/`（在盘**未建**）」、L122、L137 四处同病 | **已就地改**（2026-11-07，第 57 轮）：四处统一为「**目录在盘、实现未建**」 |
| ② | `STATUS.md` | 时点表右列「`adapters/`、`installer/` **全部存在**」 | 正文 A6 条目仍写「`modules/sandbox/`、`sandbox/` 在盘不存在」（**这条仍成立**，不算矛盾） | 无需改 —— 记录在此以免被误判为同类 |
| ③ | `VERSION-COMPATIBILITY.md` L9–12 / `STATUS.md` L45 | 「**ROADMAP 仅 §一~§七，无 §九**」 | 三份文件（A5/A6/A8）在**头注**逐条说明「不引用不存在的 §九」——这是**正确做法**：错的是 ROUTE 的引法，不是这些文件 | 不改。**但要记下**：`ROADMAP-v2.md` 71 行只有七节，任何「§八/§九」引用都是错的 |

### 一条判据（比这三条都值钱）

**「头注已更正」不等于「文件已更正」。**
`AGENT-ADAPTER.md` 的头注把 `adapters/`/`installer/` 的「在盘未建」明确标了作废，
正文却在四个地方继续写「全部在盘未建」——于是**同一份文件对同一件事给了两个答案**，
而**头注与正文谁先被读到是随机的**。

⇒ 判据：**改结论时，要全文搜该结论出现的每一处**；只改头注等于给文件加了一层"免责声明"，
真正被引用（被 grep 命中、被复制进别的文档）的是**正文那几行**。

⇒ 配套做法：更正表里要写清「**改了哪几处**」（上表 ① 写明四处），
否则下一个人不知道该信任头注还是正文，会再改一遍。

---

## 四、STATUS.md 的读法（最容易误读的一份）

`STATUS.md` 是 **phase1 交付时点快照**，不是当前状态。它的「时点声明（2026-11-07 复核）」
一节有左（当时记载）右（当前实测）两列对照表：

| 项 | 当时记载 | 2026-11-07 实测 |
|---|---|---|
| A1–A8 八份字节数/sha256 | 全部漂移 | 见该表右列 |
| `adapters/`、`installer/`、`core/{role,facts,skills,tools}` | 「在盘全不存在」 | **全部存在** |
| `modules/`、`sandbox/`、`core/capabilities/` | 未建 | 仍未建（一致） |
| 全量测试 | `395 passed`（2026-09-28） | 见 `README.md` 的 Test collection |
| 状态码 | 全部 `[x]` | 勾选只表示"当时已落盘"，**不代表当前可安装或已验收** |

**右列由 `tests/udc/test_capability_status_snapshot.py` 逐条重算**——改 A1–A8 任一份不同步改表即红灯。
左列是历史时点值，不校验也不改（审计价值在"当时看到了什么"）。

## 五、和"实现"的落差（读架构时必须同时知道）

`ROADMAP-v2.md` §二 的目录骨架是**目标态**。当前实际落差（实测）：

| 目标态目录 | 实际 |
|---|---|
| `core/{role,facts,skills,tools}/` | ✅ 存在 |
| `core/capabilities/` | ❌ **未建** |
| `modules/{udc,gateway,sandbox,item-mgmt}/` | ❌ **未建**（UDC 内容在 `core/{facts,tools,skills}/udc/`） |
| `adapters/{hermes,codex,claude-code}/` | ✅ 存在（+ `mcp`） |
| `installer/` | ✅ 存在 |
| `sandbox/` | ❌ **未建** |

`modules/` 未建不是遗漏：phase1 的实现选择是把 UDC 样板放在 `core/` 下按 facts/tools/skills 三分，
`modules/` 是留给第二个模块出现时才建的层。这条差异见 A1 §四 与 STATUS 的对照表。

## 六、外部引用清单（改前必查）

| 被引文件 | 引用方 |
|---|---|
| `ROADMAP-v2.md` | 全仓 12 处（`docs/ARCHITECTURE.md`、`docs/plans/*`、`core/facts/*` 的纪律段落） |
| `STATUS.md` | 30 处（`README.md`、`docs/SKILL-DISTRIBUTION.md`、`docs/plans/*`、`core/facts/*`） |
| `ARCHITECTURE.md`（A1） | 9 处（含 `docs/ARCHITECTURE.md` 的互引头注） |
| `AGENT-ADAPTER.md`（A8） | 10 处 |
| `SANDBOX-CONTRACT.md`（A6） | **0 处外部引用**——它是 CODE 能力的目标态契约，当前无 CODE 实现，所以没人引。**不是垃圾**：一旦建 `sandbox/` 它就是唯一依据 |
| `MODULE-INVENTORY.md`（A2）/ `VERSION-COMPATIBILITY.md`（A5）/ `TOOL-SKILL-MODULE.md`（A7） | 各 4 处 |
| `EVIDENCE-MODEL.md`（A4） | 3 处 |
| `CAPABILITY-MODEL.md`（A3） | 2 处 |

（均为 `git grep -l <文件名>` 排除本目录后的命中数，2026-11-07 实测。）

## 七、不要做的事

- **不要**把本目录当成"当前实现说明"：它是目标态。看实现去 `docs/ARCHITECTURE.md` 与 `docs/REPO-LAYOUT.md`。
- **不要**改写 `STATUS.md` 左列的历史时点值：那是 phase1 当时的现场，改掉就销毁了"漂移了多少"这条信息。
- **不要**在 A1–A8 之间互抄正文：八份各自展开 `ROADMAP-v2.md` 的一个小节，重复即意味着某一节失主。
- **不要**因为 `SANDBOX-CONTRACT.md` 零外部引用就删它（见 §六）。

---

维护：本文件是入口，不是架构文档。新增 A9+ = 先改 `ROADMAP-v2.md` §七 的清单 →
落盘新件 → 本目录 §一 加一行 → 更新合计字节数 → 同步 `STATUS.md` 的时点表。
