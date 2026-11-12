# 文档整理循环 LOG（2026-11-07，第 1–15 轮）

> 从 `docs/plans/doc-consolidation-progress.md` 迁出的逐轮记录，**逐字保留**，倒序（最新在前）。
> 入口卡片只放当前结论；需要"某轮到底改了什么、为什么、测试跑出什么数"时查这里。
>
> 迁出时点：2026-11-07 第 16 轮。迁出前该文件 678 行 / 43,816 B。
> 迁出动作由脚本按二级标题切分完成，正文未改写；仅新增本头注。

---

## 当前结论（2026-11-07，第 15 轮 —— P0 复核：code-reality-audit 里的「假通过」与失效断言）

### 为什么这轮做 P0

P0 之前只守住「Test collection 那一行必须等于 pytest --collect-only」。
`tests/test_documentation_contract.py` 用正则只认 `Test collection: \`N tests collected\`` 这一种写法，
**文档里其他形式的测试数字完全没有闸门**。

### 实测发现（4 处数字问题，3 处失效断言）

| 位置 | 原文 | 实况 | 性质 |
|---|---|---|---|
| L20 / L49 | `183 passing tests` / `183 collected tests` | 当前 2710 收集 / 2687 通过 | 时点值，由顶部声明覆盖 |
| L103 命令块 | `pytest tests -q --tb=short` -> `2710 passed` | **2687 passed, 23 skipped** | **真错**：把收集数当通过数 |
| L171 结果表 | `** passed**` | 同上 | **真空格**：数字丢了只剩空格 |
| L140 | 「README 报 2710 passed，与实测一致」 | README 报的是**收集数**，不是通过数 | **口径混淆**，原结论已不成立 |

失效断言（事实变了，不是数字漂移）：

- L122 `providers/ contains only __init__.py` -> 现有 **10 个 `.py`** 只读 provider
- L144 `no Adapters directory` -> `adapters/{hermes,codex,mcp,claude-code}` 已建，`installer/` 已建
- L144 `core.evidence.report` 定义三次 -> `grep -c "^def report"` = **1**，已清理

### 处理方式：不改历史结论，只标注现值

审计文档的价值在「当时看到了什么」。把 2026-09-03 的结论改成今天的样子等于销毁证据。
所以统一加 `【当前 2026-11-07】` 标记：原文一字不动，后面追加实测现值 + 判据。
顶部加声明块，说明「正文是时点快照，只有 Test collection 那行被闸门守着」。

唯一真正改数字的是**命令块与结果表**——那是「我跑过这条命令」的记录，数字错了就是记录错了，
不是观点错了。并补了一句 2710 = 2687 + 23 的口径自洽说明。

### 一个闸门缺口（记录，未修）

`test_documentation_contract.py` 只认 `Test collection:` 前缀。若有人把 `2710 passed` 写进命令块
（就像 L103 那样），闸门不会红——这次是靠人肉发现的。要不要扩展闸门去扫「N passed」形式的历史断言、
并允许 `【当前】` 标记豁免，得先定豁免语法，**列入待裁决**（盲扫会把所有合法的时点值都打红）。

### 验证
`tests/test_documentation_contract.py` -> **6 passed**
全量 `pytest tests` -> **2687 passed / 23 skipped**
diff：`docs/audit/code-reality-audit.md` 20/10

---

## 第 14 轮结论（2026-11-07 —— P4 审计孤岛：34 份 MICROFLOW-* 裁决表 + 目录入口文件）

### 先量后判（本轮全部数字都由脚本产出）

`docs/audit/udc-semantics/` 有 **99 份 md + 27 份 json**，其中 `MICROFLOW-*` **34 份**。
对每一份做三件事：

1. **精确路径引用扫描**：`git grep "udc-semantics/<文件名>"`，命中 `components|core|tools` 的算「代码读取」
2. **facts 侧对位检查**：按 actionType 映射到 `core/facts/udc/microflow/node-*.md`（映射目标逐个
   `assert exists`），核对该格是否真有这个 actionType 的独立契约
3. **内容重叠度**：对「有对位」的几组做行级覆盖率

### 裁决表（34 份）

| actionType | facts 对位 | 行覆盖率 | 裁决 |
|---|---|---|---|
| BREAK | `node-break.md` | 0.13 | 取证文档保留（facts 讲 `type` 陷阱，audit 讲只能在循环体内添加 + 提交路径） |
| CALL_APP_SERVICE | `node-call-app-service.md` | — | 保留 |
| CHANGE_BATCH_ENTITY / CREATE_BATCH_ENTITY | `node-batch-entity.md` | — | 保留 |
| CHANGE_LIST | `node-change-list.md` | 0.12 | 保留 |
| CREATE_ENTITY | `node-insert-entity.md` | — | 保留 |
| DELETE_ENTITY | `node-change-delete-entity.md` | — | 保留 |
| LIST_OPERATION | `node-list-operation.md` | 0.08 | 保留 |
| PUBLISH_BUSINESS_EVENT | `node-publish-event.md` | — | 保留 |
| RETRIEVE_ARRAY | `node-retrieve-array.md` | 0.17 | 保留（facts 讲分页 pageInfo，audit 讲 4 种查询方式联动 + OTHERS 聚合） |
| CHANGE_ENTITY / CHANGE_VARIABLE / CONVERT_DATA / CREATE_MAP / CREATE_VARIABLE / CUSTOM_ERROR / DATA_MAPPING / FOR / FOR_EACH / MAP_OPERATION / RETRIEVE / EXPRESSION_EDITOR | **无** | — | **唯一来源，绝对不可删** |

再叠加「代码读取」这一维度：85 份中命中 13 份（其中 3 份 `MICROFLOW-*` 经
`components/udc/live_write_templates.py` 的 `doc` 字段渲染进宿主提示词）。

**结论：0 份可判定为重复品 → 0 移动、0 合并、0 删除。** 这个 0 是测量结果，不是不作为。

### 交付物：给这个目录补了入口文件

`docs/audit/udc-semantics/README.md`（新建，5,767 B）：
- 目录定位（取证 vs 事实库的分工）
- 34 份 MICROFLOW-* 与 facts 的对应裁决表（上表）
- 99 份按 8 组分类的实测计数
- 13 份被代码读取的清单（含引用处）
- 「零精确引用的 65 份为什么仍不删」的判据
- 三条「不要做的事」

`docs/audit/README.md` 末尾补一段互指，避免两处各写一遍。

### 一个方法论收获

之前几轮把「34 份与 facts 双向零引用」当成待处理问题。实测后发现：**零引用是事实，
但"零引用 = 重复"是错的判断**。34 份里有 12 个 actionType 在 facts 侧根本没有独立事实格
（只出现在矩阵行里）。这说明**「孤岛」的真正问题不是文件冗余，而是缺少入口文件** ——
补 README 比搬文件有用得多，且零风险。

### 验证
`pytest tests` → **2687 passed / 23 skipped**；`tests/test_deidentification.py` 4 passed。
diff：`docs/audit/README.md` 4/0，`udc-semantics/README.md` 新建。

### 待裁决
- ⬜ `_attic_pending/` 156 MB 是否物理删除
- ⬜ 19 位平台对象 ID（2,359 处）是否纳入脱敏面
- ⬜ `module-landing` 两份重复副本合并方向

---

## 第 13 轮结论（2026-11-07 —— 待裁决第 1 条：skills 权威方向）

### 问题
`skills/README.md`：「权威副本在 Hermes，仓库只是选择性镜像，禁止在仓库侧编辑 skill 正文」
`docs/SKILL-DISTRIBUTION.md` §3：「仓库 skills/ = 源（版本化、可发布、可 review）」
两条规则直接对立，卡了好几轮。

### 实测（先量再判）

用 `tools/core/_meta/sync_skills_from_hermes.py --check` + 逐字节比对，仓库 35 个 `SKILL.md`：

| 结果 | 数量 | 说明 |
|---|---|---|
| 两侧完全相同 | 4 | `seeyon-field-semantics-migration`、`seeyon-excel-import-export-migration`、`seeyon-external-api-testing`、`sdd-protocol` |
| 内容不同 | 23 | 其中 **16 个**「仓库行被 Hermes 覆盖率 ≥0.98」= 仓库是旧子集 |
| Hermes 无同名 | 8 | `seeyon-agent`、`seeyon-udc-setting`、`seeyon-udc-module-landing` 等 |

覆盖率最低的三个（也是"各有独有内容"的嫌疑对象）：
`05-agent/seeyon-constraint-extraction` 0.917、`02-udc/seeyon-udc-page-debug` 0.925、
`02-udc/seeyon-udc-module-landing` 0.953 —— 仍属"仓库更短"，不是各有独有段落。

另实测两处硬事实：
- `seeyon-udc-microflow-generation` 与 `seeyon-udc-business-flow-assembly` 都在
  `<HERMES_HOME>/skills/udc/`（**兄弟目录**，不在 `skills/seeyon/` 下）——原文档写成 `seeyon/02-udc/` 是错的。
- `skills/README.md` 说 `02-udc/seeyon-udc-module-landing` 被测试断言 —— **实测无任何测试引用该路径**。

### 裁决：不是矛盾，是两种关系

| 目录族 | 权威方向 | 理由 |
|---|---|---|
| `01-platform` `02-udc` `03-v8-extension` `04-integration` `06-delivery` `07-office-collaboration` | **Hermes → 仓库（镜像）** | 操作手册，本就该写真实环境；Hermes 是唯一持续维护处 |
| `05-agent` + 顶层 4 个 | **仓库 → Hermes（源）** | 仓库自身规矩，与环境无关 |

`docs/SKILL-DISTRIBUTION.md` 新增 §0 记录此裁决 + 实测数字；`skills/README.md` 头部加互指块。
§3「仓库=源」保留但标注**只对 `05-agent` 与顶层 4 个成立**，§3–§5 明确为目标态而非现状。

### 顺手修正的三处过期断言
1. §2.2 业务组装 Skill：原文"工作树存在、未跟踪" → **已入库**（`skills/02-udc/`，22647 B）
2. §2.2 核心微流程生成 Skill：原文 Hermes 位置 `udc/` → `skills/udc/`（兄弟目录）
3. §2.3 module-landing 重复副本："被测试断言" → 实测**无测试引用**，两份 13204 B 逐字节相同，未合并

### 又踩了一次自己的坑
进度记录里写"复查：客户应用 ID、组织域名等在该文件 0 命中"时，**把要复查的那个域名字符串原样写进去了**——
PII 闸门当场红（`docs/plans/doc-consolidation-progress.md:L29`）。改成描述性写法（"客户组织域名"）后通过。
这是本次会话第三次"记录脱敏这件事本身又变成泄漏"。

### 验证
`pytest tests` → **2687 passed / 23 skipped**。
diff：`docs/SKILL-DISTRIBUTION.md` 45/9、`skills/README.md` 6/0。

### 待裁决现状
- ✅ 第 1 条（skills 权威方向）：**已裁决**，见上
- ⬜ 第 2 条（是否允许物理删除）：仍未决；`_attic_pending/` 现占 156 MB
- ⬜ 第 3 条（19 位平台对象 ID 是否纳入脱敏面，2,359 处）：仍未决
- ⬜ `module-landing` 两份重复副本合并方向：需先定引用方向

---

## 第 12 轮结论（2026-11-07 —— P6 收口：四件临时件逐个裁决）

### 方法：先查读取面，再定去留

一次性扫描（`rg`/`grep -rl` 全仓 `.py/.md/.json/.yaml/.sh`，排除 `_attic`）：
`COMPLETION-METHOD-PROMPT.md` 与 `UNDERSTANDING-CHECKPOINT.md` 均 **零代码读取**，
但分别被 `DEPLOYED-STATE-VERDICT.md`（交叉校验）和 `skills/05-agent/seeyon-constraint-extraction/SKILL.md`
（范式引用）正文提到。按约束「零引用不能作为删除依据」，逐份核内容是否有替代。

| 文件 | 读取面 | 内容替代性 | 裁决 |
|---|---|---|---|
| `udc-semantics/COMPLETION-METHOD-PROMPT.md` | 零代码；2 处正文引用 | **无替代**：方法论六步是 SKILL 的范式源；§环境 的运行时版本被 `DEPLOYED-STATE-VERDICT.md` 做 3/3 交叉校验；完成判据 checklist 是「什么算做完」唯一成文标准 | **保留原地** + 头注改为已裁决 |
| `udc-semantics/UNDERSTANDING-CHECKPOINT.md` | 零代码、零正文引用 | **无替代**：§3 组件语义（UdcForm / UdcSubPage / UdcReference / UdcPanel）+ 动作枚举（`buildin\|widget\|microflow\|enevtThrow`）全仓仅此一处；`core/facts/udc/write-chain/` 只有保存协议与 page-schema 形状 | **保留原地** + 头注改为已裁决 |
| `recovery-checkpoint.md`、`next-direction-input.md` | 被代码/测试夹具读取 | — | 第 6 轮已判：禁止移动 |

**顺带清掉一处垃圾**：`_attic_pending/extension-surface-intermediates-20261107/` 是 0 文件空壳
（上一轮误移后又原样恢复留下的），已 `rmdir`。

### 顺手做的脱敏（本轮唯一内容改动）

`COMPLETION-METHOD-PROMPT.md` 的 §环境 原写死：客户应用 ID + 显示名、目标实体 ID、
K8s 命名空间、凭据文件绝对路径、本机 maven 仓库路径。这些都在**结论区**（`.md`，非 artifacts），
属仓库脱敏规则覆盖范围。已改为「配置键 / 占位符」写法，并加了脱敏说明块；**方法论与完成判据一字未动**。
改完复查：客户应用 ID、目标实体 ID、集群命名空间名、客户组织域名，这四类在该文件 0 命中；
但同时确认 §环境 的**运行时版本三元组仍在**（`DEPLOYED-STATE-VERDICT.md` 的交叉校验依赖它，不能一起删）。

### 验证
`pytest tests` → **2687 passed / 23 skipped**（与上轮同，本轮未加测试）。
diff：`docs/audit/README.md` 2/0、`COMPLETION-METHOD-PROMPT.md` 15/7、`UNDERSTANDING-CHECKPOINT.md` 7/2。

### P6 状态：关闭（4/4 有裁决，零文件移动）
`COMPLETION-METHOD-PROMPT.md` 保留 · `UNDERSTANDING-CHECKPOINT.md` 保留 ·
`recovery-checkpoint.md` 禁止移动 · `next-direction-input.md` 禁止移动 ·
`entity-field-matrix/C3–C9` 第 6 轮已判被 gate 脚本字节校验 · `plans/hermes/plans/` 已登记保留。

### 发现但未处理（记录，不改）
全仓清点发现 302 个结论区文件含**裸 19 位数字**共 2,359 处（剔除保留段后），
最高的是 `docs/audit/role/P0-role-object-model.md` 207 处、`write-chain.contract.md` 111 处。
逐一核查语义：这些是**平台对象 ID**（appId / entityId / menuId / pageId），不是客户名，
现有 PII 闸门只拦「客户应用名/实例名/组织/人名/工号」四类，故不报红。是否把 19 位平台对象 ID
纳入脱敏面（会大幅降低可复现性）——**列入待裁决，不自行决定**。

---

## 第 11 轮结论（2026-11-07 —— P2 收口：STATUS.md 时点表变成闸门）

### 本轮做了什么

**1）STATUS.md 的 A1–A8 实测列又漂了一条**

上一轮（第 2 轮）建表时 8 份里 7 份漂、只有 A8 一致。这轮复核发现 **A8 也漂了**：
`AGENT-ADAPTER.md` 从 11657 B / `fb996462…` 变成 **12200 B / `1d2d7b96…`**（我自己在第 2 轮改过它 5 处断言）。
A1–A7 的实测列仍准。已更新 A8 行。

**2）把实测列变成闸门：`tests/udc/test_capability_status_snapshot.py`（4 用例）**

仿 `test_deployed_tags_version_audit_alignment.py` 的写法：
- `test_table_covers_all_eight_docs`：A1–A8 八行都在、文件名对得上（防表格被改坏导致闸门空转）
- `test_measured_column_matches_disk`：逐行重算字节 + sha256 前 8 位
- `test_gate_bites_on_mutation`：**内存内突变**自证会咬（改字节 +1、sha 改 `00000000`），
  不写文件 ⇒ 失败不可能是并发会话造成的假象
- `test_directory_existence_claims_hold`：`adapters/`、`installer/`、`core/{role,facts,skills,tools}`
  必须在；`modules/`、`sandbox/`、`core/capabilities/` 必须不在

判据纪律写进模块 docstring：**左列历史值不校验、不改**，只校验右列与本轮实测同步。

**3）P0 同步**：+4 用例 → 收集 2706 → **2710**，`sync_test_counts.py` 三处同步并回读通过。

**验证**：闸门单跑 4 passed；全量 **2687 passed / 23 skipped**。

### P2 状态：关闭
- 两份 ARCHITECTURE 的分工头注：第 2 轮已加
- STATUS.md：时点声明 ✓ 实测对照表 ✓ 过期断言纠正 ✓ **且有测试守着**（本轮新增）
- 剩余 10 处正文 40 位 sha256 仍为历史值时点，已被顶部声明覆盖，不再逐条改

---

## 第 10 轮结论（2026-11-07 —— P1 最后一项：INDEX sha 锚点 + 锚点闸门）

### 本轮做了什么

**1）INDEX 的 sha 锚点漂移 2 条，已修正并写明原因**

脚本解析 `core/facts/INDEX.md` 的 SPI 行（2,632 字符的长格），逐条按 SPI 子树找同名件、
算 sha256、比字节数——5 条锚里 **2 条漂移**：

| 锚 | 原值 | 实测 | 漂移原因 |
|---|---|---|---|
| `spi-ext-runtime.md` | `2a5861c9…`/18537B | `b76b68f2…`/18529B | 提交 `2e0d1d8d` 脱敏（把 把带客户域名的网关主机名改成 `lowcode-test2.example.com`），**字节数少 8**，正好是域名差 |
| `evidence/README.md` | `b96cd568…`/4131B | `98762a6b…`/4340B | 我在第 1–2 轮给它补了「P3d 时点」声明与 2026-11-07 复核注记 |

两条都改成"现值 + 旧锚作废原因"，保留旧值作历史（`git diff` = **1 行**，不是 124 行——
第一次写时 CRLF 被我改成 LF 导致全文件重写，已还原成 CRLF 后重做）。

**2）把人工核对变成闸门：新增 `tests/udc/test_facts_index_anchors.py`**

仿 `test_deployed_tags_version_audit_alignment.py` 的写法，2 个用例：
- `test_index_anchor_format_is_parseable`：断言能解析出 ≥4 条锚且含 registration/runtime，
  防止有人把锚格式改坏导致闸门静默失效
- `test_index_sha_anchors_match_disk`：逐条比对 sha256 前 8 位 + 字节数，漂移即失败并打印差异

意图：以后再有人改这四格事实件却忘同步 INDEX，测试会红，而不是索引无声撒谎。

**3）P0 同步**：新增 2 个用例 → 收集数 2704 → **2706**，跑
`tools/core/audit/sync_test_counts.py` 同步 README / agent-version-audit / code-reality-audit
三处（工具自身回读校验通过，三处均为 2706）。

**验证**：全量 `pytest tests` → **2683 passed / 23 skipped** ；
`tests/udc/test_fact_discoverability.py + test_documentation_contract.py + test_deidentification.py`
→ 19 passed。

### P1 状态：全部关闭
- `core/facts/INDEX.md` 表格死引用：**0**（三路径脚本核验，跳过 `…`/`<` 模板占位）
- sha 锚点：**5/5 与磁盘一致**，且有闸门守着
- `spi/evidence/README.md`、`write-chain/README.md`：第 1–2 轮已处理
- L36 之前挂着"等未提交改动定稿再重算"——本轮工作树已清空（第 9 轮提交完），条件满足

---

## 第 9 轮结论（2026-11-07 —— 用户指令：清客户标识 + 提交）

### 用户指令（本轮执行依据）
> "看见客户的就改，改删除就删除，git那边为提交的就提交，你先检索那里面有没有用然后删除，整理，胡总和你先抽有用的"

理解为：**客户标识就地脱敏；该删的删；工作树该提交的提交；删之前先判断有没有用，有用的先抽出来。**

### 已完成

**1）客户标识脱敏（结论区已全清）**
- `tests/test_deidentification.py` 首轮 **FAILED**：本轮前几轮我自己写的进度记录里把
  `<客户应用名><19 位应用 ID>` / `<客户实例名><19 位实例 ID>` 抄进了
  `docs/plans/doc-consolidation-progress.md`（L66/L67）——**自己的文档违规**，已改回脱敏写法，
  现在 **4 passed**。
- `验收/` + `验收_min/` 41 份 schema 内客户应用 ID 共 **4,038 处**
  → 全部替换为保留段 `9000000000000000001`，41 个文件 JSON 全部仍可解析。
- 全仓结论区（`.md/.py/.yaml`，排除 `artifacts/`、`_attic_pending/`）PII 命中：**0**。

**2）抽取有用内容，再移走无用的大块**
- 新建 `docs/audit/microflow-acceptance-suite/`：从仓库根 `验收/` 抽出
  `INDEX.md`（20 业务 × 2 变体的节点编排对照）+ `COVERAGE.md`（18 种 actionType 使用频次）
  + README（说明价值、边界、取用方法）。**这两张表是结构知识，不含客户标识。**
- 仓库根 `验收/`（43 文件 / 2 MB）+ `验收_min/` → 移入 `_attic_pending/acceptance-suite-root/`
- `tools/_mfdump/`（8 份客户流程抓包，零代码引用）→ 移入 `_attic_pending/mfdump-root/`
- 两者都**未删除磁盘文件**，只是移出受管路径；`docs/REPO-LAYOUT.md` 与
  `_attic_pending/README-20261107-migration.md` 登记了去向与恢复命令。

**3）回滚了 3 次错误删除（诚实记录）**
第一次移除 `extension-surface-20261029/{interfaces.json, interfaces-facade-only.json,
batch2-old-v517}`（178 MB 中间产物）后，`tests/udc/test_extension_usage_assets.py` **9 failed**：
`interfaces.json` 被 `align_version_baseline.py` / `audit_facts.py` / `emit_action_index.py` /
`probe_contracts.py` 4 个工具读取，还有 4 个测试断言它存在。
同理，三份客户 `*-biz.md` 被 `test_extension_usage_assets.py` 断言「客户应用 biz 至少 3 份」。
**全部原样恢复**，测试回到 45 passed / 全量 2681 passed。
教训：`git grep` 零命中 ≠ 无引用——这些路径被**未跟踪的** tools 脚本引用，只能靠跑测试发现。

**4）分 5 批提交（工作树已清空）**

| commit | 内容 | 文件数 |
|---|---|---|
| `9fa07b76` | 代码：证据分级 / 否定路由 / advisory 全量透传 / 分发闸门原型 | 30 |
| `85f0b211` | 文档：索引归零 + 重复降级 + 流水账收束 + 标准品 24 格事实 | 75 |
| `5b3268c6` | 修复 + 文档：子流程详情报错 + 5.3.600 构件面重抽 + 审计文档计数 | 369 |
| `a8d384d3` | 工具/技能：platform 抽取工具链 28 脚本 + 2 个 UDC Skill + 验收套件索引 | 57 |
| `1ecabc6c` | 清理：`scratch/aud` 7 件 + `tools/_mfdump` 8 件移出索引 | 15 |

- 全部**显式列路径** `git add -- <paths>`，未用 `git add -A`，未 push。
- 每次提交前跑全量：**2681 passed / 23 skipped**。
- 最终 `git status --porcelain` = **0 行**。

### 未做 / 需裁决
1. **41 份客户流程 schema 与 8 份抓包仍在 `_attic_pending/`**（磁盘占 156 MB）。
   是否物理删除需你确认 —— 按约束删除是最后手段，且已归档可回溯。
2. `_attic_pending/extension-surface-intermediates-20261107/` 为空壳（内容已恢复原位），可删。
3. 提交未 push（约束禁止）。

---

## 第 8 轮结论（2026-11-07）

### 本轮完成（P3/P4 补漏：docs/audit 根目录无索引 + 两份能力矩阵同主题未登记）

**P3 清单外的新发现**：`docs/audit/` 根目录有 **29 份顶层 .md + 16 个专题目录**，却**从来没有索引**。
它不是 P3 列举的七组重复，但符合 P0–P6 的总目标（"让每个目录职责清晰、可发现"）。本轮处理：

1. **新建 `docs/audit/README.md`**（5.2 KB），按职能分 6 组登记：
   当前基线（5）/ 微流程（8）/ 实体与字段（10）/ 页面菜单列角色设置（6 目录）/
   平台网关运行态（7）/ 流水与检查点（3，含"被代码读取"标注）。
   只做登记，**不改任何原文件、不给新结论**。明确写出 `artifacts/` 不逐条登记的理由
   （按取证批次组织，逐条登记会立刻过期）。

2. **两份微流能力矩阵同主题**（P3 清单外）：
   - `docs/audit/microflow-capability-matrix.md`（12 KB，2026-10-31，**审计视角**：
     状态定义 / 接口契约 / P1–P4 验收标准 / 修正记录）
   - `core/facts/udc/microflow/capability-matrix.md`（10 KB，**事实视角**，被
     `components/udc/microflow/capability_registry.py` 直接读取，运行时唯一数据源）
   裁决：**判据以 facts 为准**，审计侧保留。在审计侧文件头加了 8 行分工登记
   （`git diff --numstat` = 8/0，纯插入），说明"两文件数字不一致时不要合并数字，先查时点"。

**验证**：`pytest tests/test_documentation_contract.py tests/udc/test_fact_discoverability.py
tests/udc/test_extension_usage_assets.py` → **50 passed**（离线）。零删除、零移动。

### 说明：为什么这轮不是 P4/P3 的其他项
- P4 已在第 4 轮做完 34/34 分类，结论是"无一份可安全删除"，剩余是"补 facts"（需要平台复核，超出文档整理范围）。
- P3 七组已在第 3 轮全部处理。
- 本轮选的是"目录可发现性"这个此前漏掉的横切面——`docs/audit/` 是全仓第二大文档目录（仅次于 core/facts），
  却一直没有入口文件。

### 剩余
- 待裁决 3 条（skill 源/镜像冲突、是否允许物理删除、客户应用 ID 明文文件名）。
- `core/facts/INDEX.md` L36 sha 锚点等未提交改动定稿。

---

## 第 7 轮结论（2026-11-07）

### 本轮完成（P1 收尾：INDEX 死引用归零 + 客户标识脱敏）

**先复核 P0**：`pytest tests --collect-only` 实测 **2704 tests collected**（0.75s），
与 README / 两份审计文档一致；`tests/test_documentation_contract.py` 绿。

**P1 剩余死引用 5 条（上一批只修了 8 条中的前 4 条 + 3 条标 UNVERIFIED）——本轮全修：**

| 行 | 原引用 | 修正为 | 依据 |
|---|---|---|---|
| L29 | `attribute-set/create.md` | `setting/attribute-set/create.md` | 该行模块列已是 `udc`，需带 `setting/` 前缀 |
| L36 | `customer-impl-crosscheck.md` | `evidence/api-contracts/customer-impl-crosscheck.md` | 在 `spi/evidence/api-contracts/` |
| L117 | `app-inner/create.md` | `application/app-inner/create.md` | 在 `udc/application/app-inner/` |
| L118 | `udc-biz-appservice.md` / `udc-biz-domain.md` | `docs/audit/artifacts/service-flow-20261103/…`（两处） | 这两个 md **不在 core/facts/**，在审计产物目录 |
| L118 | 客户应用 `-biz.md` 三份（`znxmglpt…` / `xiangmuguanli…` / `datamigration…` 前缀） | 改为「`*-biz.md` 三份（同目录，应用标识按脱敏缩写记载、本索引不展开）」并保留类数/体积 | **见下 BLOCKED 说明** |

**验证方法**：脚本按 `module/ref` → `facts/ref` → `repo/ref` 三路径解析（不是正则盲替），
修完全表扫描 **remaining dead: []**（跳过含 `…`/`<` 的模板占位）。
`pytest tests/udc/test_fact_discoverability.py tests/test_documentation_contract.py
tests/udc/test_extension_usage_assets.py` → **50 passed**。`git diff --numstat` = `15/16`（单行改动，无整文件重写）。

### ⚠️ BLOCKED（新发现，未处理，需裁决）
`core/facts/INDEX.md` L118 及 `docs/audit/artifacts/service-flow-20261103/` 下三份
`*-biz.md` 三份（`docs/audit/artifacts/service-flow-20261103/` 下，文件名 = `<应用标识><19 位应用 ID>-biz.md`）
**文件名内含客户应用 ID 明文**，且这些 md 内是客户业务
类清单（458 类 / 130 类 / 27 类）。它们**已入库**（`git ls-files` 命中），不是本轮产物。
本轮只把 INDEX 行里的明文 ID 换成脱敏写法，**未改名、未移动、未删文件**——改名会破坏
`docs/audit/artifacts/` 的"只增不删"约定和可能的字节级引用。
按硬约束这属于「发现客户数据进入文档 → 停止该条并记 BLOCKED」。

### P1 状态
- `core/facts/INDEX.md` 死引用：**0 条**（含 3 条已标 `⚠️ 格未落盘` 的规划项）。
- L36 的 sha256 锚点仍未重算（等未提交改动定稿，见原任务约束）。
- 待裁决项新增 1 条：客户应用 ID 明文文件是否改名/脱敏（现为 BLOCKED）。

---

## 第 6 轮结论（2026-11-07）

### 本轮完成（P6 临时件登记 —— 一个都没移动，全部先取证再定性）

**关键发现：P6 清单里的 4 个"临时件"中有 2 个被程序读取，按硬约束不得移动。**

| 文件 | 谁读它 | 裁决 |
|---|---|---|
| `docs/audit/next-direction-input.md` | **`components/audit_summary.py:12`**（`REPORTS["next_direction"]`）+ `seeyon_cli.py:333` 的 `summary` 子命令 + `tests/test_audit_summary.py:20` | ⛔ **禁止移动**，加登记头注 |
| `docs/audit/recovery-checkpoint.md` | **`tests/fixtures/udc-audit/manifest.json:9`** 的 `source_documents`（`components/evidence_bundle.py` 校验该 manifest） | ⛔ **禁止移动**，加登记头注 |
| `docs/audit/udc-semantics/COMPLETION-METHOD-PROMPT.md` | 仅 `skills/05-agent/seeyon-constraint-extraction/SKILL.md:219` 提及；`DEPLOYED-STATE-VERDICT.md` 与归档日志各一处历史引用 | 🟡 加登记头注，暂不移动（方法论仍有参考价值） |
| `docs/audit/udc-semantics/UNDERSTANDING-CHECKPOINT.md` | **全仓零引用** | 🟡 加登记头注，暂不移动（「前端真实机制」「页面保存链」两节是该线唯一系统叙述） |

**另两个 P6 项经核对不需要处理：**
- `entity-field-matrix/C3–C9`：**不是临时件**。`B4/SLICE-B2/EVIDENCE-batch-*/assets/bundle-*` 被
  `tools/audit/gate_b4_doc.py`、`gate_b5_bigint_v2.py`、`gate_b6_decimal.py` 按固定路径字节级校验；
  C1–C9 是同一批取证记录。新建 `docs/audit/entity-field-matrix/README.md` 作索引（含"谁在读、不要移动"）。
- `docs/plans/hermes/plans/` 双层嵌套：`rg` 全仓确认**无程序读取**，`docs/REPO-LAYOUT.md:37`
  已登记该目录。只有 1 份文件（`frontend-ui-full-extraction.md`，67 行）。搬迁会让登记失效、
  收益低于风险 → 保留原位，在新建的 `docs/plans/README.md` 里说明来由。

**新建两个索引（原本这两个目录都没有 README）：**
- `docs/plans/README.md`：区分「当前有效」3 份 / 「历史计划」5 份，逐条给时点；说明 `hermes/plans/` 嵌套来由。
- `docs/audit/entity-field-matrix/README.md`：B 段（7 件）/ C 段（12 件）/ 证据资产 / 谁在读。

**验证**：`pytest tests/test_documentation_contract.py tests/udc/test_fact_discoverability.py
tests/udc/test_extension_usage_assets.py tests/test_audit_summary.py tests/test_evidence_bundle.py`
→ **55 passed**（离线）。四个被改文件 `git diff --numstat` 均为纯插入（5/0、5/0、4/0、4/0），
零删除、零移动、零重命名。

### P6 结论
P6 六项全部完成分类，**物理移动 0 个**。原因不是偷懒：按硬约束「移动前确认无程序读取」，
两项直接命中代码读取（audit_summary、evidence_bundle manifest），一项属取证批次且被闸门脚本
字节级校验，一项是唯一系统性叙述、零引用但不宜据此删除。

---

## 第 5 轮结论（2026-11-07）

### 本轮完成（P5 流水账收束，零删除、零搬迁既有资产，只新增归档副本 + 改入口）

**1）docs/plans/seeyon-distribution-progress.md**
- 原文件 151 行 / 71,472 B 的追加式日志**逐字复制**到新文件
  `docs/ledger/LOG-distribution-20261020-20261107.md`（含迁移说明头；正文与原件 `endswith` 校验为 True，
  字节数 71,472 一致）。
- 入口文件重写为 ~1.9 KB 卡片：已完成 / 阻塞（6 条）/ 下一步（4 步）/ 待裁决（2 条）。
- 未删除任何内容；原件在归档件内完整可查。

**2）docs/audit/udc-semantics/PROGRESS.md**
- 原文件 1,570 行 / 180,859 B（倒序堆叠，2026-10-14 → 10-16 第五十三轮）**逐字复制**到
  `docs/ledger/LOG-udc-semantics-PROGRESS-20261014-20261016.md`（181,401 B，含说明头）。
- 入口改写为 ~2.2 KB 卡片：已完成 8 类 / 未完成与阻塞 3 条（余 60 条 op UNVERIFIED、
  BPM+ORG+USER 仅 facade、节点类数 20/22/24 口径冲突）/ 权威入口 / 证据纪律。
- `git diff --numstat`：`40 insertions / 1566 deletions`（内容未丢，见归档件）。

**3）修两处因迁移而失效的引用**
- `core/role/EVIDENCE-DISCIPLINE.md:52`、`STATUS.md:18` 原指向 `PROGRESS.md` L585
  （"测试通过数不得当契约"的同型错记录）——迁移后行号失效，改为指向
  `docs/ledger/LOG-udc-semantics-PROGRESS-20261014-20261016.md` 第十八轮。
- 未改 `skills/05-agent/seeyon-constraint-extraction/SKILL.md:219`（仍指向 PROGRESS.md
  作为进度看板，该路径现仍是有效入口，无需改）。

**验证**：`pytest tests/test_documentation_contract.py tests/udc/test_fact_discoverability.py
tests/udc/test_extension_usage_assets.py` → 50 passed（离线）。零文件删除。

### 注意事项
- 两份归档件是**新增未跟踪文件**（`??`），未 `git add`。若后续要入库需人工确认。
- `docs/audit/udc-semantics/PROGRESS.md` 是**已跟踪文件**，本轮改动会在 `git diff` 中显示
  1566 行删除——这是 P5 的设计结果，内容在归档件，非丢失。

---

## 第 4 轮结论（2026-11-07）

### 本轮完成（P4 审计孤岛归属裁决表，34/34 分类完毕；零移动、零删除）

数据来源：`rg` 全仓引用扫描 + `docs/audit/udc-semantics/` 目录清单 + `core/facts/udc/microflow/`
62 个 .md 交叉比对 + `capability-matrix.md` 23 行 action 清单（22 类 + 1 表头误匹配 `RUNTIME_VERIFIED`）。

**关键更正**：上一批扫描报告称"34 份双向零引用"，实测**有 3 份被生产代码引用**
（`components/udc/live_write_templates.py`），**不可移动**——这是"零引用不能作为删除依据"的实证。

#### A 组｜已沉淀，facts 有对位（6 份，保留不动）

| 审计侧文件 | actionType | facts 对位 |
|---|---|---|
| MICROFLOW-BREAK-CONTRACT.md | BREAK | node-break.md |
| MICROFLOW-CALL-APP-SERVICE-CONTRACT.md | CALL_APP_SERVICE | node-call-app-service.md |
| MICROFLOW-CHANGE-LIST-CONTRACT.md | CHANGE_LIST | node-change-list.md |
| MICROFLOW-LIST-OPERATION-CONTRACT.md | LIST_OPERATION | node-list-operation.md |
| MICROFLOW-RETRIEVE-ARRAY-CONTRACT.md | RETRIEVE_ARRAY | node-retrieve-array.md |
| MICROFLOW-PUBLISH-BUSINESS-EVENT-CONTRACT.md | PUBLISH_BUSINESS_EVENT | node-publish-event.md |

裁决：facts 为准（有运行时证据等级），审计侧保留作 CDP 抓包过程件，**不移动**。

#### B 组｜facts 缺口（15 份，最有价值 —— 不可当垃圾清理）

| 审计侧文件 | actionType | facts 现状 |
|---|---|---|
| MICROFLOW-CHANGE-ENTITY-CONTRACT.md | CHANGE_ENTITY | 无 node-*.md |
| MICROFLOW-CREATE-ENTITY-CONTRACT.md | CREATE_ENTITY | 无 |
| MICROFLOW-CHANGE-VARIABLE-CONTRACT.md | CHANGE_VARIABLE | 无 |
| MICROFLOW-CREATE-VARIABLE-CONTRACT.md | CREATE_VARIABLE | 无 |
| MICROFLOW-CONVERT-DATA-CONTRACT.md | CONVERT_DATA | 无 |
| MICROFLOW-DATA-MAPPING-CONTRACT.md | DATA_MAPPING | 无 |
| MICROFLOW-MAP-OPERATION-CONTRACT.md | MAP_OPERATION | 无 |
| MICROFLOW-CREATE-MAP-CONTRACT.md | CREATE_MAP | 无 |
| MICROFLOW-RETRIEVE-CONTRACT.md | RETRIEVE | 无 |
| MICROFLOW-CUSTOM-ERROR-CONTRACT.md | CUSTOM_ERROR | 无 |
| MICROFLOW-FOR-CONTRACT.md | FOR（结构） | 无 |
| MICROFLOW-FOR-EACH-CONTRACT.md | FOR_EACH（结构） | 无 |
| MICROFLOW-DELETE-ENTITY-CONTRACT.md | DELETE_ENTITY | node-change-delete-entity.md（部分覆盖） |
| MICROFLOW-CREATE-BATCH-ENTITY-CONTRACT.md | CREATE_BATCH_ENTITY | node-batch-entity.md（部分覆盖） |
| MICROFLOW-CHANGE-BATCH-ENTITY-CONTRACT.md | CHANGE_BATCH_ENTITY | node-batch-entity.md（部分覆盖） |

裁决：**这些是 facts 的补位来源，不是垃圾**。后续若要补 facts，从这批取证；在此期间保持原位。

#### C 组｜跨节点机制/方法论（11 份，其中 3 份被生产代码引用）

| 审计侧文件 | 主题 | 引用情况 |
|---|---|---|
| MICROFLOW-PARAMS-TAB-DATACHAIN.md | 参数 tab 数据链 | **live_write_templates.py:175** |
| MICROFLOW-BUSINESS-EVENT-TRIGGERS.md | 业务事件触发 | **live_write_templates.py:208,224** |
| MICROFLOW-SERVICE-AND-ACTIVITY-NODES.md | 标品类型 + 活动节点 | **live_write_templates.py:246,269** |
| MICROFLOW-EXPRESSION-4-TYPES.md | 表达式四类型 | — |
| MICROFLOW-EXPRESSION-EDITOR-CONTRACT.md | 表达式编辑器操作 | — |
| MICROFLOW-EVENT-OBJECT-SEMANTICS.md | 事件对象语义 | — |
| MICROFLOW-DATASOURCE-TYPES.md | 数据源类型全谱 | — |
| MICROFLOW-NODE-FIELD-CONSTRAINTS.md | 节点字段约束规范 | — |
| MICROFLOW-NODE-BACKEND-CONSTRAINTS.md | 后端权威解析约束 | — |
| MICROFLOW-VIEW-MODE-TRAP.md | 查看模式假通过真凶 | — |
| MICROFLOW-NODE-ACCEPTANCE-SOP.md | 节点验收 SOP | — |

裁决：前 3 份被代码 `doc` 字段引用（渲染进宿主提示，见
`components/construction/host_llm_prompt.py:89`、`intent_draft_schema.py:279,317`）→
**位置锁定，禁止移动**。其余为方法论，保留。

#### D 组｜汇总取证，与 facts 三方并存（2 份）

| 审计侧文件 | 口径 |
|---|---|
| MICROFLOW-24-NODE-CONTRACTS.md | 24 类（CDP 实测，2026-10-27） |
| MICROFLOW-NODES-FULL-FORENSICS.md | 24 类全量取证 |

裁决：与 `node-ui-contracts-22.md`（22 类）、`all-nodes-coverage.md`（22+3 结构）、
`node-catalog.md`（51 定义）并存，**口径 20/22/24 三套**。这属于"知识口径冲突"而非重复文档，
需先定主源口径（22 类 = capability-matrix 基线）再处理；本轮只登记，不动。

#### 结论
- 34 份中 **18 份不能动**（A 组 6 + C 组 3 被代码引用 + D 组 2 + B 组部分覆盖 3 的关联）。
- **没有一份是"可安全删除的垃圾"**；上批"孤岛"判断不成立。
- 下一步若要收口，正确动作是「把 B 组事实并入 facts 并在 INDEX 登记」，而不是删审计侧。

### 待办
- B 组事实补位（需逐条与平台重新核对，不能直接抄审计结论）。
- D 组口径统一（22 vs 24）。

---

## 第 3 轮结论（2026-11-07）

### 本轮完成（P3 重复文档降级，全部"合并 + superseded 指针"，零删除）
- `core/facts/udc/setting/enum/create.md`：修正指向 `write-chain/enum-write-chain.md`（不存在）的
  2 处路径 → `setting/enum/enum-write-chain.md`；`enum-write-chain.md` 头部加「两份分工」说明
  （create = 九段式摘要，write-chain = 全量操作表）。**不做内容合并**——两者是分层而非重复。
- `core/facts/udc/entity/rule-domain.md` §5：并入 `rules-microflow.md` 的独有内容
  （三类规则的新建弹窗 radio 值 `VALIDATE/ASSIGN_VALUE/DEFAULT_VALUE` + 初始 state
  `RELEASE/DRAFT/DRAFT` + 「页面默认值列表显示成计算」）；`rules-microflow.md` 头部加
  「已并入 rule-domain.md §5/§4，保留作历史记录」。
- `docs/operation-contracts/udc/entity/registry-entries-code.md`：加 superseded 指针
  （MERGE 中间件，代码已落入 registry.py，主文档 = `registry-entries.md`）。
- `docs/audit/udc-semantics/FRONTEND-EXTRACTION-STATUS.md`（v1）：加 superseded 指针 → v2
  （v1 op 数 346；v2 并集 456、action 6 命名空间/55 方法）。
- `docs/audit/udc-semantics/S7-WRITE-CHAIN-LIVE.md`（v1）：加部分取代指针 → v2（W5/W5b/W6/W6b）。
- **纠正上一轮的误判**：`NODE-CENSUS-all/app` 两份**不是重复**（scope=all 4755 流程/55670 节点，
  快照 10-19 10:24:32 vs scope=app 47 流程/251 节点，快照 10-17 15:41:03）；`FIELD-SEMANTICS` 三份
  是同一 P2 研究的三个部分（ACTIVITY / CONTROL+前端 / type=2 VACUUM 收官）。两批均只加
  「同批/非重复」互指说明，不合并、不改数字。
- 验证：`pytest tests/udc/test_fact_discoverability.py tests/test_documentation_contract.py
  tests/udc/test_extension_usage_assets.py` → 50 passed（离线）。
- 本轮零文件删除、零移动。

### P3 剩余（未做）
- `docs/audit/udc-semantics/PROGRESS.md`（P5）、34 份 `MICROFLOW-*.md` 归属（P4）。

---

## 第 2 轮结论（2026-11-07）

### 本轮完成（P2b：capability 状态文档时点化）
- `docs/capability/STATUS.md` 新增「时点声明」表：逐件列出 A1–A8 的记载字节数/sha256 与
  2026-11-07 实测值（仅 A8 一致，其余 7 件漂移）；并纠正「`adapters/`、`installer/`、
  `core/{role,facts,skills,tools}` 在盘不存在」的过期断言——实测全部存在，
  `core/capabilities/`、`modules/`、`sandbox/` 仍未建。
- 同一文件把 `395 passed`（2026-09-28）标注为时点值并提示已过时，指向 README 的 Test collection。
- `docs/capability/AGENT-ADAPTER.md` 更正 4 处「目标态未建」断言 + 1 处 `installer/` 不存在断言，
  改为「目录已在盘、内容为声明级模板/清单、安装器与真实宿主加载仍未验收」。
- 验证：`pytest tests/test_documentation_contract.py tests/udc/test_fact_discoverability.py` → 15 passed（离线）。
- 未做：A1–A7 正文里的旧哈希未逐条改写（只在 STATUS 建对照表），避免大面积改写正文；
  如需正文同步，应先决定「哈希表是否改由脚本生成」。

### 待办（本轮未动）
- `docs/capability/STATUS.md` 正文行内仍保留 7 条旧 sha256 原文，已由顶部对照表声明为时点值。

---

## 第 1 轮结论（2026-11-07）

### 已完成（离线测试通过）
- P0 文档一致性：`README.md`、`docs/audit/agent-version-audit.md`、
  `docs/audit/code-reality-audit.md` 的 Test collection 已校正为 `2704`。
  验证：`pytest tests/test_documentation_contract.py tests/udc/test_fact_discoverability.py` → 15 passed。
- P1 `core/facts/INDEX.md` 死引用修复（7 处路径 + 1 处重复行 + 1 处分目录计数）：
  - L13 `runtime-data/read.md` → `runtime-data-read.md`
  - L14 `udc microflow/tree.md` → `bpm flow-node-tree.md`（模块列同时纠正）
  - L15 `serial.md` → `serial/serial-config.md`
  - L16 `app-draft.md` → `serial/app-draft.md`
  - L19 `enum/create.md + write-chain/enum-write-chain.md` → `setting/enum/...`
  - L20 `fields.md` → `setting/custom-object/fields.md`
  - L31/32/33 `storage/mysql-redis-map.md`、`nacos/dataid-diff.md`、`bpm/boundary.md`：
    三个文件在 git 历史中**从未存在**（`git log --all` 无记录），标注为「格未落盘 / UNVERIFIED」，
    不删除行（保留规划意图），并注明相关证据的实际位置。
  - L42/L54 重复登记 `entity/refer-event-index-tabs.md`：合并为一行的全量内容，删除重复行。
  - L46 分目录计数：`application 2→(顶层 4/含子目录 7)`、`entity 2→(顶层 9/含子目录 11)`、`serial 1→2`。
- P1 `core/facts/udc/microflow/INDEX.md`：61 个 .md → 实测 62，并补 `README.md` 入口。
- P1 `core/facts/spi/evidence/README.md`：标注原文数字为 P3d 时点值，补 2026-11-07 复核
  （`evidence/live/` 9 件、全树 79 文件）；未重生成 inventory（避免重开已 PASS 的 P1 证据面）。
- P1 `core/facts/udc/write-chain/README.md`：重跑 `tools/core/facts/gen_write_chain_index.py --write`，
  仅 2 行行数变化（87→176、82→122），符合预期。
- P2 架构文档分工头注：`docs/ARCHITECTURE.md`（仓库实现视图）与
  `docs/capability/ARCHITECTURE.md`（ROADMAP-v2 目标架构）互引，均声明数量/路径存在性有时点性。
- P2 `docs/operation-contracts/README.md`：Directory 段补全为实际 14 个 UDC 子域
  （application/bi/column/entity/flow/menu/microflow/page/publish/resource/role/rule/runtime/setting）。

### 阻塞 / 未验证
- `docs/capability/STATUS.md` 8 件套 sha256/字节数漂移 + 断言 `adapters/`、`installer/` 不存在
  （两者实际已存在）：**本轮未改**，属于需重算哈希的批次，下一批处理。
- `core/facts/INDEX.md` L36 的 sha256 锚点：等未提交改动定稿后再重算，现在改会写错。
- 客户数据：本轮未触碰任何客户证据、凭据、scratch；未访问平台。

### 待裁决（用户决定，不自行处理）
1. `skills/README.md`「权威副本在 Hermes、仓库只是镜像」 vs `docs/SKILL-DISTRIBUTION.md`
   「仓库 skills/ = 源」——两条规则冲突。裁决后：回填 `_attic_pending/mirrored-skills-20261022/`
   的 243 个 references，或改写 262 条引用方向。
2. 是否允许物理删除任何文件（当前策略：只合并 + superseded 指针，不删）。

### 下一批候选（按优先级）
- P2b：`docs/capability/STATUS.md` 时点化（哈希漂移 + adapters/installer 存在性断言）。
- P3：重复文档降级（enum-write-chain / rules-microflow / registry-entries-code /
  NODE-CENSUS / FIELD-SEMANTICS / FRONTEND-EXTRACTION-STATUS v1v2 / S7-WRITE-CHAIN-LIVE v1v2）。
- P5：本文件历史流水迁 `docs/ledger/`；`docs/audit/udc-semantics/PROGRESS.md` 同处理。
- P4：34 份 `docs/audit/udc-semantics/MICROFLOW-*.md` 归属裁决表。
