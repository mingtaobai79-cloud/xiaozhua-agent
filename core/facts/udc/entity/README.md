# core/facts/udc/entity/ 索引

## 这个目录是什么

**UDC「实体」域的事实格**：9 份顶层 md + `evidence/` 两个抓包子树。
对应 INDEX 行 `core/facts/INDEX.md` L46（`udc/entity/`：顶层 9 / 含子目录 11）。

⚠️ **这个目录有两种格式，别混着读**：

| 格式 | 文件 | 读法 |
|---|---|---|
| **九段式能力事实文档**（Capability / Version / Input / Required / … / Verified） | `create.md`、`attribute-create.md` | 逐段有证据等级标签，`Verified` 段的等级就是可信度 |
| **实测坑清单**（铁律 / 结论 / 最小 body / 坑） | 其余 7 份 | 先读「铁律」或「结论」，别从正文第一行顺读 |

九段式是 B1 样板链的产物（`ROADMAP-v2` 口径），只有两格落地；其余 7 份是取证过程中长出来的坑记录，
**不是同一体裁**，用同一套期待去读会失望。

## 一、9 份一览（2026-11-07 实测）

| 文件 | 格式 | 字节 | 行 | 外部引用 | 一句话 |
|---|---|---:|---:|---:|---|
| `create.md` | 九段式 | 8,129 | 127 | **65** | `udc.entity.create` 建单据实体（B1 样板格） |
| `attribute-create.md` | 九段式 | 7,430 | 121 | 5 | `udc.entity.attribute.create` 建属性（B1 第 2 格） |
| `entity-update-payload.md` | 坑清单 | 3,747 | 81 | 1 | 实体更新权威 payload + 「枚举名 vs 数字」铁律 |
| `event-dto-binding.md` | 坑清单 | 4,528 | 94 | 1 | 事件绑的是 DTO 不是实体；无 DTO 时建事件静默成功 |
| `refer-event-index-tabs.md` | 坑清单 | 8,845 | 173 | 3 | 参照/事件/索引三 tab 的 GraphQL 写入面（e6） |
| `scalability.md` | 坑清单 | 5,539 | 81 | 2 | 扩展实体机制（实测 + 反编译双证） |
| `ctpenum-domain-fix.md` | 坑清单 | 32,077 | 519 | 1 | CTPENUM 枚举域错配修复（切片1，最长一份） |
| `rule-domain.md` | 坑清单 | 11,742 | 248 | 3 | 实体规则域（微流程）写入链 LIVE |
| `rules-microflow.md` | **已并入** | 2,229 | 40 | 3 | 见下 §四，**保留作历史记录** |

合计 **9 份 / 84,266 B**。

`create.md` 的 **65 处外部引用**（`components/udc/**`、`adapters/mcp/DESIGN.md`、
`components/platform_operations/registry.py` 等）意味着：**它是 B1 样板链的锚，动它会断一片代码引用。**

## 二、五条「静默成功」坑（本域最贵的一类，按危险度排）

这 9 份里有五处是同一个模式的变体：**接口返回成功、DB 也有行，但页面上什么都没有。**
这类坑的共同教训是「`BOOT_0000` + DB 回读正确 ≠ 可用」。

| # | 坑 | 症状 | 出处 |
|---|---|---|---|
| 1 | **枚举字段要字符串枚举名，不是数字** | 照 DB 里的数字传 → `BOOT_3000`，`message` 恒为 `null`，看不出原因 | `entity-update-payload.md` 铁律 |
| 2 | **事件绑的是 DTO 不是实体** | 实体无 DTO 时建事件：`BOOT_0000`、DB 有行、页面 0 条、列表接口 0 条，**不报错** | `event-dto-binding.md` §2 |
| 3 | **事件列表 `sourceId` 过滤不生效** | 返回全应用 49 条，看着像"建成功了"。精确校验必须用 `udcEventGet` | `refer-event-index-tabs.md` §1 |
| 4 | **扩展实体 create 不触发、update 才触发** | 建实体时带 `customScalabilityId` 只存值，不生成 `<name>Ext` 影子实体 | `scalability.md` §4 |
| 5 | **`fieldIds` 是逗号分隔字符串不是数组** | 传数组 → `属性fieldIds的值反序列化为String类型时失败` | `refer-event-index-tabs.md` §2 |

## 三、`ctpenum-domain-fix.md` 的读法（445 行，最容易被误读为结论）

这份头部有 **HANDOFF-C 更新块**：下表是 **18:30（403 阶段）的即时判定**，保留作过程记录；
当前结论要看本节末尾的「最终判定（2026-10-17 23:59 +08）— LIVE PASS」。

**直接读中间的 18:30 表会读到 `PARTIAL` / `BLOCKED`，那是当时状态，不是现状。**
这是本仓库反复出现的模式（同 `docs/audit/role/`）：**先读头部更正块，再读正文。**

## 四、`rules-microflow.md` 为什么还留着（P3 已办）

它**已经并入** `rule-domain.md` §5（三类规则 radio 值 / groupType / 初始 state 对照表）与 §4（编辑器），
文件头部自己写着"已并入…保留作历史记录，内容不再更新"。

**仍不删的三个理由**：

1. `tests/udc/test_fact_discoverability.py` 的 `CRITICAL` 元组**按文件名**锁定它（L39），删了测试红；
2. `core/facts/INDEX.md` 有它的登记行；
3. 它记录的「3 条规则全链路 LIVE 证据」在 `rule-domain.md` 里是压缩表述，原文的 5 步实验序列只在这里。

P3 这条可以判关闭：**合并动作已完成，剩余的是"零删除"决策，不是文档整理缺陷。**

## 五、`evidence/` 两个子树

| 子树 | 件数 | 内容 |
|---|---:|---|
| `evidence/entity-write-2026-10-23/` | 12 | 实体写链抓包：属性批量保存 body、类型矩阵、字段字典、stereotype 权威值、移动/复制请求 |
| `evidence/entity-surface-2026-10-23/` | 3 | 实体页面暴露面：切实体、页面 boot 抓包 + `README.md` |

**只在本地读，不入分发**：`entity-write` 里是运行态业务数据（见进度卡片的 BLOCKED 条）。

## 六、不要做的事

- **不要**把 7 份坑清单"统一改写成九段式"：它们是取证副产品，改造成本远高于价值，
  而且 §二的对照关系会散掉。
- **不要**动 `create.md`：65 处引用、B1 样板链锚点。要改先跑 `pytest tests/udc -q`。
- **不要**删 `rules-microflow.md`：见 §四，测试按文件名锁着它。
- **不要**从 `ctpenum-domain-fix.md` 中间的表取结论：见 §三。
- **不要**在本目录再建 README/INDEX：`core/facts/udc/` 这一级整体还没有入口，
  将来要补也是补**上一级**（覆盖 page/ application/ entity/ serial/ 四域），不要再往下分层。

---

维护：新增实体域事实格 → §一 加一行 → 更新合计字节 → 若引入新的"静默成功"坑，必须登记进 §二
（这一类坑是本域最贵的知识，散落在正文里就等于没有）。
