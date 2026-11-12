# docs/operation-contracts/udc/microflow/ 索引

## 这个目录是什么

**微流程域的 Operation Contract 与语义契约。** 与相邻目录分工：

| 目录 | 职责 |
|---|---|
| `core/facts/udc/microflow/` | **事实格**：环境无关的运行时契约、构造器修正、验证记录（消费方直接读） |
| 本目录 | **契约与语义**：某个操作如何被 Agent 请求、响应、回读；以及节点语义的字节码实证 |
| `docs/audit/udc-semantics/MICROFLOW-*` | **取证过程**：前端交互层实测、CDP 抓包、dataSchema 回读 |
| `docs/audit/artifacts/` | **原始证据归档**：按批次命名，只增不删 |

四层不是重复。同一主题在四处各说一层，引用时必须写明是"事实/契约/取证/原件"的哪一层。

---

## 〇★、**先读这一节：本目录的大契约是「被反复纠正过的结论」，不是一次成稿**

13 份顶层 md 里有 6 份共 **17 处**更正标记。这些不是笔误 —— 它们是**同一批结论经过 main 的多轮裁定后留下的痕迹**，
而 `map-node` / `state` 两份大契约里最关键的性质（`state` 与 `publish_state` 正交）**本身就是推翻出来的**。

⇒ **判据：读契约时，先看它有没有「撤回 / 已作废 / 已重写」段，再看结论。**
   下结论快的文档最危险，因为它们读起来最顺。

### 更正表（按"会不会让人引错结论"排序）

| # | 原判断（已撤回 / 已作废） | 更正为 | 代价 | 原文 |
|---|---|---|---|---|
| ① | 「`state=10` 疑为**草稿态**」 | **已撤回**：`state` 与 `publish_state` **正交**（state=10 的 289 行 `publish_state` 100% = 1；未发布的 21 行全在 state=20）⇒ **state 不是发布态**，真实语义 **UNVERIFIED** | **最贵**：把 state 当草稿态，会去过滤掉实际在生效的数据 | `map-node` L247 |
| ② | 「state=10 是草稿所以**未生效**」 | **没有数据支持**（B-6 UNVERIFIED#11 原表述已由 main 在 `3a6b757` **撤回**） | 同上（①的另一种说法） | `state-semantics` L142 / L460 |
| ③ | 「289 行 state=10 **无同名 state=20 兄弟行**」（原论据） | **已作废**，本节按 main **D51**（commit `d283b99`）**重写** | 论据塌了，结论必须重立 | `state-semantics` L421 |
| ④ | 用「**16.8×**」与「控 type 后 **6.0×**」两处引用当判定依据 | **两处均被 D52 作废**，本版已删除 | 引了作废的倍数 | `state-semantics` L499 |
| ⑤ | 三级表的读法（`49f0293` 首版） | **首版读错**，`D54` 用 **Fisher** 纠正 | **统计判据错** —— 读错分级表会把弱证据当强证据 | `state-semantics` L527 |
| ⑥ | main **D42**：「auditor 的推论不成立」 | **D43 撤销 D42**：「auditor 的推论成立，**是我判错**」 | — | `map-node` L164 |
| ⑦ | main **D42** 推定「按全库 nodeId 全局集合匹配 → 0；按微流程内匹配 → 10」 | 已更正（见原文节） | 口径错（全局 vs 域内） | `map-node` L191 |
| ⑧ | 「若业务只认已发布态，本应用实际应用面只有 **2 个**」 | **已被 LIVE 数据否定，撤回**（实测 2026-10-18） | 会严重低估可用面 | `map-node` L687 |
| ⑨ | 「不是版本草稿对」的原表述 | **有误，已更正**（正确证据已另立） | — | `map-node` L700 |
| ⑩ | 引擎定位「**0 命中**」表述 | **已作废**，改为全量分类证据 | 又是"0 命中"——见下 | `runtime-engine-location` L250 |
| ⑪ | 判据「`nodes` 仅非末位且 `expr` 非空时应非空」 | **撤回**：被 `n18_0`、`jxFAX9`（非末位 + `expr` 有值 + `body` 空）**推翻** | 判据边界错，会漏判或误判 | `FIELD-SEMANTICS-ctl-frontend` L33 / L91 |
| ⑫ | ROUTE 输入假设中「样本池含完整结构」的**隐含前提** | **直接推翻**：12 条样本池**全部来自他应用**、全是 `{enums,item,itemType}` 键集，**没有一条**覆盖本应用形态 | 拿别的应用的样本当本应用的证据 | `cappservice-parameter-semantics` L223 |
| ⑬ | 微流程 C1 的 **404** 现象 | 【R21 LIVE PASS + **404 根因纠正**】活体双发命中 | — | `a6-milestone-report` L31 |

### 两条反复出现的错因（比单条更正更值钱）

| 错因 | 实例 | 判据 |
|---|---|---|
| **"state / 状态"类字段被当成语义标签** | ①②③ | 字段名像语义 ≠ 字段是语义。`state` 与 `publish_state` 正交是**算出来的**（289 行交叉分布），不是读名字来的 |
| **统计判据自己站不住** | ④⑤ | 倍数（16.8× / 6.0×）和分级表的读法都要**另一次统计检验**（D54 用 Fisher）才算数；`49f0293` 首版就读错了 |
| **"0 命中"当结论** | ⑩ | 与 `column-discovery` 同一个病：**0 命中先问"查的名字对吗"**（方法论 60） |

### 一条特别值得记的：**"是我判错"要留痕**

`map-node` L164 记的是 main **D43 撤销自己的 D42**：「auditor 的推论成立，**是我判错**」。
这条留痕的价值超过它纠正的那一条结论 —— 它告诉后来者：**这里的裁定链是可被推翻的，且推翻会写下来。**

⇒ **不要把这类"自我推翻"整理掉。** 删掉它，下一个读者就无法判断哪些结论经过对抗检验。

---

## 一、13 份顶层 md，按职责分四组

### A｜大契约（三份，合计 141,549 B，本目录的主体）

| 文件 | 字节 | 行 | 内容 |
|---|---:|---:|---|
| `map-node-semantics.contract.md` | 81,838 | 1,171 | **映射类节点（B-6）**：CREATE_MAP / MAP_OPERATION / DATA_MAPPING 三节点的语义。含分母口径（全文唯一）、两套 `mappingMode` 必须分开（最易混淆点） |
| `state-semantics.contract.md` | 39,190 | 694 | **`state` 语义（B-7）**：`MicroFlowDataStateEnum` 字节码实证；`state` 与 `publish_state` 正交（否证「草稿」误读）；生产口径判定 `state=10` 不进代码生成 |
| `runtime-engine-location.contract.md` | 22,136 | 376 | **执行引擎定位（B-8）**：逐跳证据链全 STATIC 字节码；引擎不在哪些 jar（扫描范围清单）；state 过滤判定 |

### B｜节点级语义契约（一份，被代码读取）

| 文件 | 字节 | 内容 | 读取方 |
|---|---:|---|---|
| `cappservice-parameter-semantics.md` | 20,706 | **CALL_APP_SERVICE「服务参数」语义**：`fullName`/`md5` 真实语义、`parameter`/`returnValue` 契约、`mappingType`/`attrs`、逐字段总表 | `components/udc/microflow_constraints.py:488` 注释直接指本文件 §5；`tests/udc/test_call_app_service_node_contract.py` 与 `skills/05-agent/seeyon-agent-evidence-driven/SKILL.md` 引用 |

**这份位置锁定，不得移动。**

### C｜普查与字段语义（五份，同一批 B-1R / P2 取证）

| 文件 | 字节 | scope / 快照戳 |
|---|---:|---|
| `NODE-CENSUS-all-20261018.md` | 16,027 | **all**：4755 流程 / 55670 节点，快照 **2026-10-19 10:24:32** |
| `NODE-CENSUS-app-20261018.md` | 12,546 | **app**：47 流程 / 251 节点，快照 **2026-10-17 15:41:03** |
| `FIELD-SEMANTICS-app-std-20261019.md` | 6,242 | 标准域 ACTIVITY 字段语义（P2 · D157 返工） |
| `FIELD-SEMANTICS-ctl-frontend-20261019.md` | 6,393 | CONTROL 3 种 + 前端域分层 |
| `FIELD-SEMANTICS-final-20261019.md` | 6,362 | P2 收官（type=2 · 组装映射 · 落点互证） |

**两份 NODE-CENSUS 不是重复**：scope 不同、快照戳不同。引用数字必须连快照戳一起引，不可跨文件混用——两份文件头部都已写明这一点。

三份 `FIELD-SEMANTICS` 同理：同一研究的三个切片（标准域 / 控制+前端域 / 收官互证），共享 2026-10-19 批次，是**一份证据的三个部分**而非三个版本。

### D｜里程碑与候选取证（四份）

| 文件 | 字节 | 内容 |
|---|---:|---|
| `a6-milestone-report.md` | 14,514 | 微流程只读里程碑 A6 收口：能读什么 / 精确怎么读 / 仍 UNVERIFIED·BLOCKED + 证据清单（sha256 前 16 位） |
| `candidate-contracts-evidence.md` | 6,655 | R1 离线取证：候选契约表（每条 locator 8 要素）+ 缺口清单 + 自回读核对 |
| `gateway-live-facts.md` | 3,157 | 网关 service 前缀活体确证（与本地 5.3.517 静态**分列不混写**） |
| `local-53517-offline-candidates.md` | 3,034 | 本地 5.3.517 jar 离线取证：已知 GET 只读候选 / 被排除的 destructive GET / P1 支路 BLOCKED |

## 二、两个子目录

| 子目录 | 内容 | 性质 |
|---|---|---|
| `live-evidence/` | 11 份 md + 40 份 json | **原始活体探测记录**（`C*_node_tree_*.json` 等）。被 `core/facts/bpm/`、`core/facts/runtime/`、`core/facts/udc/` 多处以**路径 + 字节数 + 内容摘要**引用（含负证据：6 件全 404 的 applog 探测）。**只读归档，位置锁定** |
| `microflow-ledger-inputs/` | 9 份 json | 台账管线的中间件（`bundle-output` / `evidence_context` / `http` / `impact_graph` / `ledger-output`）。不是文档 |

`live-evidence/` 是全仓**唯一**记录微流程端点活体行为的原件目录。`core/facts/` 里凡写"实测零 live-evidence"
或"负证据 6 件全 404"的地方，判据都落在这里 —— **删任何一件都会让那些断言失去依据。**

## 三、外部引用清单（改前必查）

`git grep` 全仓命中（排除本目录内互引）：

| 被引文件 | 引用方 |
|---|---|
| `cappservice-parameter-semantics.md` | `components/udc/microflow_constraints.py`、`tests/udc/test_call_app_service_node_contract.py`、`skills/05-agent/seeyon-agent-evidence-driven/SKILL.md` |
| `a6-milestone-report.md` | `core/facts/udc/application/applog-family.md`、`docs/deliverables/microflow-readonly-milestone-report.md` |
| `candidate-contracts-evidence.md` / `gateway-live-facts.md` / `local-53517-offline-candidates.md` | `docs/deliverables/microflow-readonly-milestone-report.md` |
| `live-evidence/**` | `core/facts/bpm/{data-flow-map,flow-node-tree}.md`、`core/facts/runtime/datatype-getAll.md`、`core/facts/udc/application/applog-family.md`、`core/facts/spi/evidence/live/` |

## 四、零外部引用的四份：为什么仍不删

`map-node-semantics.contract.md`、`state-semantics.contract.md`、`runtime-engine-location.contract.md`
三份大契约，和三份 `FIELD-SEMANTICS` / 两份 `NODE-CENSUS`，按精确路径搜索零外部引用。**不是删除依据**：

- `core/facts/udc/microflow/` 下**没有**对应的映射类节点、state 语义、引擎定位事实格
  （实测：`ls | grep -iE "map-node|state-semantic|runtime-engine|node-census|field-semantic"` = 0 命中）。
  这三份是这条链路的**唯一成文契约**。
- 引用方可能是未跟踪脚本或未来才落的事实格 —— `git grep` 只搜已跟踪文件。

## 五、不要做的事

- **不要**把本目录内容搬进 `core/facts/`：facts 要求环境无关，本目录多份绑定了快照戳、活体探测时间戳。
- **不要**合并三份 `FIELD-SEMANTICS` 或两份 `NODE-CENSUS`：它们是同一研究的切片，合并会丢快照戳对应关系。
- **改前**先看 `docs/operation-contracts/README.md`（上层目录的七条判据）与
  `docs/ledger/LOG-doc-consolidation-20261107-rounds1-15.md` 的裁决记录。
