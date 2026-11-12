# docs/ 索引

## 这个目录是什么

**全部文档的根**。10 份顶层 md + 7 个子目录（392 + 11 + 1 + 1 + 7 + 85 + 9 份 md）。

⚠️ **顶层 10 份几乎全是「规则」，不是「内容」**——它们回答"东西该放哪、怎么算合格"，
不回答"平台怎么用"。查平台用法去 `core/facts/`，查操作契约去 `docs/operation-contracts/`。

这也是这 10 份**外部引用极少**（6 份 `git grep` 零命中）的原因：它们是给**写文档的人**看的，
不是给查资料的人看的。阅读顺序上优先级低，但**动手前的自检清单在这里**。

## 一、10 份顶层文档（2026-11-07 实测）

| 文件 | 字节 | 行 | 外部引用 | 一句话 |
|---|---:|---:|---:|---|
| `ARCHITECTURE.md` | 10,327 | 207 | 0 | **实现视图**（现在盘上有什么）。与 `capability/ARCHITECTURE.md`（目标架构）互引不互抄 |
| `REPO-LAYOUT.md` | 4,532 | 87 | 1 | 目录约定 + 判断口诀（哪个目录放什么） |
| `KNOWLEDGE-GOVERNANCE.md` | 3,726 | 75 | 0 | 四种资产（Facts/Skills/Components/Evidence）的职责边界与引用规则 |
| `KNOWLEDGE-LANDING-RULES.md` | 5,509 | 136 | 1 | 沉淀归位：什么算「必须进仓库」、事实分级 |
| `HOST-INTEGRATION.md` | 4,379 | 77 | **10** | Agent-Host 集成指南（宿主怎么调这个仓的能力） |
| `SKILL-DISTRIBUTION.md` | 6,657 | 116 | 1 | Skill 分发与三套目录的关系（**含一处待裁决冲突，见 §四**） |
| `CONSTRUCTOR-DEPENDENCY.md` | 4,112 | 61 | 0 | 节点构造器模块依赖图（5 文件的重复定义现状） |
| `ASSET-INVENTORY.md` | 3,337 | 68 | 0 | `_attic_pending/` 的 A–E 分类清单（只标记，不删） |
| `MFG-BUSINESS-VERIFICATION.md` | 2,372 | 48 | 0 | 制造业业务验收状态（**单一时点快照，2026-11-05**） |
| `REPO-INCIDENT-20261018.md` | 5,351 | 125 | 0 | 两起误入库事故记录（**禁止删除，末尾追加不改正**） |

合计 **10 份 / 50,302 B**。

### 两份"规则"容易混，分工如下

| | `KNOWLEDGE-GOVERNANCE.md` | `KNOWLEDGE-LANDING-RULES.md` |
|---|---|---|
| 管什么 | **四种资产各自的边界**（Facts 不许写"怎么搭节点"，那是 Skill 的活） | **什么必须进仓库**（结论/校验器/契约/原始证据四类） |
| 什么时候读 | 决定"这条知识该写成哪一种资产" | 决定"这份产出要不要入库" |
| 关系 | 前者是 `ARCHITECTURE.md` §4 的展开 | 自称与前者"互补，不重复" |

两者都自称互补——**实测内容确实不重叠**，可以都读，不必担心重复。

## 二、7 个子目录

| 目录 | md 数 | 入口 | 是什么 |
|---|---:|---|---|
| `audit/` | 401 | ✅ `README.md` | 审计现场与证据。`artifacts/`（36 子目录 / 8,851 文件 / 409 MB）有自己的入口 `artifacts/README.md` |
| `operation-contracts/` | 99 | ✅ `README.md` | 九域操作契约。★ 整层入口 = `udc/README.md`（14 子域 / 81 份 / 1,153,874 B）；`udc/microflow/`、`udc/setting/`、`udc/column/` 另有子目录入口 |
| `capability/` | 11 | ✅ `README.md` | **目标架构**（ROADMAP-v2 + A1–A8 + STATUS） |
| `plans/` | 9 | ✅ `README.md` | 计划与进度卡片（含 `doc-consolidation-progress.md`） |
| `ledger/` | 8 | ⚙ 图例 | 流水归档。四个前缀 `LOG-`/`DIGEST-`/`RESUME-`/`STATUS-` 即性质契约，**只增不改**。`README.md` 是**前缀图例**（不是导读入口），由 `tests/udc/test_ledger_layout.py` 守着 |
| `construction-rules/` | 1 | ❌ | 构造规则（单份，无需入口） |
| `deliverables/` | 1 | ❌ | 交付物（单份，无需入口） |

`ledger/` 仍是归档区，**导读仍从 `plans/` 各卡片进入**——这一点不变。
2026-11-07 补了一份 `ledger/README.md`，但它不是导读入口，而是**四个前缀的图例**：
`LOG-`/`DIGEST-`/`RESUME-`/`STATUS-` 各是什么、哪份是"某个时点的断言"、迁出件的现行版在哪。
这三件事此前没有一处集中写过（`plans/` 三份卡片只在提到具体文件时顺带指路），
而 `STATUS-2026H2.md` 自称"适配器切片全部达成"，不带图例极易被当现状读。
`construction-rules/`、`deliverables/` 只有 1 份，加 README 是过度设计。

## 三、按问题找文档

| 我要… | 去哪 |
|---|---|
| 了解平台某功能怎么用 / 接口长什么样 | `core/facts/`（**不在 docs/**） |
| 找一个域的操作契约（端点/必填/报错） | `docs/operation-contracts/udc/<域>/` |
| 看架构要建成什么样 | `docs/capability/ROADMAP-v2.md` + A1–A8 |
| 看现在盘上有什么 | `docs/ARCHITECTURE.md`、`docs/REPO-LAYOUT.md` |
| 找某条结论的原始证据 | `docs/audit/artifacts/` |
| 看某轮做了什么决定 | `docs/ledger/`、`docs/plans/` |
| **动手写文档/代码前自查** | `KNOWLEDGE-GOVERNANCE.md` + `KNOWLEDGE-LANDING-RULES.md` |

## 四、写在这里的两条待裁决（不自行决定）

1. **`SKILL-DISTRIBUTION.md` 与 `skills/README.md` 规则冲突**：前者说"仓库 `skills/` = 源"，
   后者说"权威副本在 Hermes、仓库只是镜像"。两条规则方向相反，需用户裁决回填 references 还是改写引用方向。
2. **`MFG-BUSINESS-VERIFICATION.md` 的数字是时点快照**：它写着 `2606 passed / 22 skipped`（2026-11-05），
   与当前全量结论不一致。因为它是"验收状态单一事实源"，**本轮不改它的历史值**——
   改了会销毁"当时验收到哪一步"这条信息。要更新需先确认这个问题是否还在跟踪。

## 五、不要做的事

- **不要**在 `docs/` 顶层再新增"一次性报告"。这类内容归 `docs/audit/` 或 `docs/ledger/`；
  顶层只放**长期有效的规则与总览**。
- **不要**因为某份顶层文档 `git grep` 零命中就删：§一 那 6 份零引用的都是规则文档，
  零引用是因为"没人链接规则"，不是因为"规则没用"（`REPO-INCIDENT-20261018.md` 甚至明写禁止删除）。
- **不要**把 `docs/ARCHITECTURE.md` 和 `docs/capability/ARCHITECTURE.md` 合并：一个是实现视图、
  一个是目标架构，合并会失去"目标 vs 现状"的落差信息。
- **不要**手改 `MFG-BUSINESS-VERIFICATION.md` 的历史数字，除非确认该问题仍在跟踪（见 §四）。

---

维护：新增顶层文档 → §一 加一行 → 更新合计字节 → 若它是"规则"类，§三 的查找表要加一条指向。
新增子目录 → §二 加一行；md 数超过 8 份时补该目录自己的 README（由
`tests/udc/test_docs_root_layout.py` 守着本表）。
