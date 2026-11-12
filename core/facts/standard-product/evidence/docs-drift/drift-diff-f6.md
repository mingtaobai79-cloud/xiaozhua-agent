# drift-diff-f6｜docs/capability registry 状态分布漂移站点全集 S5~S11 新旧逐字对照

- 线：`session-20260929-184027-7f85bd1f`（standard-product 事实格线，纯静态）
- 单：HANDOFF-7（P7 = 授权② 收尾），判据与站点表 = `main/ROUTE.md` §7.3；dedupe_key=`p7-docs-drift-site-complete`
- 时钟：2026-10-01 ｜ 落盘人：implementer ｜ **先出本件、后改文档**
- 关系：本件是 `drift-diff.md`（=`0c8d001d…770b`，S1~S4）的**续件**，非替代；`drift-diff.md` 既有段**逐字未改写**（sha 复核见 §6）。

## 0. 口径源（唯一）与禁混声明

- 口径源 = `core/facts/standard-product/evidence/reconciliation/count_registry_contracts.out.json`
  sha256 = `3a07224c06d1e52b5338c3ca89aa91294536e36d2b8c8665822ae644848f9d72`
- 实测 `status_census`（本次 `json.load` 复算，非转述）：
  `{"VERIFIED_STATIC_BYTECODE": 53, "OBSERVED": 2, "UNKNOWN": 9}` → 合计 64，**无 UNVERIFIED 键 ⇒ UNVERIFIED 承载 = 0/64**。
- 计数脚本锚 = `count_registry_contracts.py` = `611e73990acc0b66…e9ab0`（冻结件，未改）。
- 展示序口径（N-6a）：分布串统一 `VERIFIED_STATIC_BYTECODE / UNKNOWN / OBSERVED`（简写 `53/9/2`）。
- **禁混**：`evidence_level_census` = `{VERIFIED_STATIC_BYTECODE 62, OBSERVED_LIVE 2}` 是**证据等级轴**，
  与 `status_census`（OperationStatus 轴）不同维度；本单所有修正值只取 `status_census`。
- 两条 OBSERVED 契约（`registry.py` 实测行号）：
  - `registry.py:125` `udc.deploy.normal`（write=True，`POST udc/runtime/deploy-normal`）
  - `registry.py:128` `udc.deploy.search_status`（write=False，`POST application/appVersion/{appGuid}`）
  根因提交 = `210aa72`「facts(deploy): 部署历史真面 appVersion/{appGuid} 升级 OBSERVED + Redis 布局 + 配额契约 (09-28 LIVE)」（`git log --oneline -1 210aa72` 实测）。

## 1. 派发时点 vs 实施时点 grep 重定位（首步实测）

命令：`grep -rn "53/9/1/1|OBSERVED.?\(?1\)?|UNVERIFIED.?\(?1\)?|UNVERIFIED 1|LIVE 1" docs/capability/`（implementer 首步实测 2026-10-01）

| 站点 | §7.3 派发时点行号 | 实施时点 grep 实测 | 位移 |
|---|---|---|---|
| S5 | `EVIDENCE-MODEL.md:45` | `:45` | 0 |
| S6 | `EVIDENCE-MODEL.md:47-48` | `:47-48`（同一句跨行折行） | 0 |
| S7 | `EVIDENCE-MODEL.md:41` | `:41` | 0 |
| S8 | `EVIDENCE-MODEL.md:128` | `:128` | 0 |
| S9 | `docs/capability/STATUS.md:20` | `:20` | 0 |
| S10 | `TOOL-SKILL-MODULE.md:51` | `:51` | 0 |
| S11 | `VERSION-COMPATIBILITY.md:81` | `:81` | 0 |

⇒ 站点全集 = 7 处 / 5 文件，与 §7.3 一致，**无行号位移**，无新增站点；
grep 亦**未**命中 S5~S11 之外的 registry 状态分布旧值（`:102` 命中情况见 §5）。

## 2. S5｜`docs/capability/EVIDENCE-MODEL.md:45`（归并结论首行）

- 旧（逐字）：
  `- \`VERIFIED_STATIC_BYTECODE\`(53) → STATIC；\`OBSERVED\`(1) → LIVE；\`UNVERIFIED\`(1) → GENERATED 待证；`
- 新（逐字）：
  `- \`VERIFIED_STATIC_BYTECODE\`(53) → STATIC；\`OBSERVED\`(2) → LIVE；\`UNVERIFIED\`(0) → GENERATED 待证（当前无契约承载）；`
- 依据：`status_census` OBSERVED=2；UNVERIFIED 键缺失 ⇒ 承载 0。第 46 行 `UNKNOWN`(9) → 不可归并 半句不动。

## 3. S6｜`docs/capability/EVIDENCE-MODEL.md:47-48`（59 基础口径自洽句）

- 旧（逐字，跨两行）：
  ```
  - 59 基础口径下：`VERIFIED_STATIC_BYTECODE 50` + `UNKNOWN 9`（=59）；两条 R18（OBSERVED 1 +
    UNVERIFIED 1）另计——与全 64 分布 `53/9/1/1` 自洽。
  ```
- 新（逐字，跨两行）：
  ```
  - 59 基础口径下：`VERIFIED_STATIC_BYTECODE 50` + `UNKNOWN 9`（=59）；两条 R18（OBSERVED 2）
    另计——与全 64 分布 `53/9/2`（UNVERIFIED 0/64）自洽。
  ```
- 依据：59 基础半句（VSB 50 + UNKNOWN 9）不动；R18 两条均 OBSERVED（§0 两条 op_id）；全 64 分布串改 `53/9/2` 并注 UNVERIFIED 0/64。

## 4. S7｜`docs/capability/EVIDENCE-MODEL.md:41`（UNVERIFIED 归并行的举例）

- 旧（逐字）：
  `| \`UNVERIFIED\` | **GENERATED（待证）** | 登记为"已知但活体未确证"，禁止升 VERIFIED；全 64 条中 \`udc.deploy.search_status\`（类级前缀 LIVE 404，完整路由 UNVERIFIED，禁拼前缀） |`
- 新（逐字）：
  `| \`UNVERIFIED\` | **GENERATED（待证）** | 登记为"已知但活体未确证"，禁止升 VERIFIED；全 64 条承载 = 0/64（\`udc.deploy.search_status\` registry 态已于提交 \`210aa72\` 升 OBSERVED，见上表 OBSERVED 行；其完整路由活体证据另列，不属本行状态分布） |`
- 依据：归并定义语义（「已知但活体未确证，禁止升 VERIFIED」）**逐字保留**；仅把 search_status 的 registry 态举例改为 0/64 承载表述，并以交叉引用标明两维度之分（解决 F-6b 与 S4 的张力，不改活体证据事实）。

## 5. S8/S9/S10/S11 与「明确不入站」

**S8｜`EVIDENCE-MODEL.md:128`**
- 旧：`| 全 64 分布 53/9/1/1、59 基础 50/9 | \`registry.py\`（本轮脚本 \`count_status.py\` 实测，同 A1 第五节口径） |`
- 新：`| 全 64 分布 53/9/2（UNVERIFIED 0/64）、59 基础 50/9 | \`registry.py\`（本轮脚本 \`count_status.py\` 实测，同 A1 第五节口径） |`
- 来源半句不动。

**S9｜`docs/capability/STATUS.md:20`**（A4 历史日志体）
- 旧：`实测：OperationStatus 8 值枚举（models.py）；全 64 分布 53/9/1/1（同 A1 口径）；写门 DENIED/POLICY_DENIED 在 layer.py:22；4 步 evidence.level 逐值重跑；169/51 回读=LIVE`
- 新：`实测：OperationStatus 8 值枚举（models.py）；全 64 分布 53/9/2（UNVERIFIED 0/64）（同 A1 口径）；写门 DENIED/POLICY_DENIED 在 layer.py:22；4 步 evidence.level 逐值重跑；169/51 回读=LIVE（漂移修正 2026-10-01，见 drift-diff-f6.md）`
- 仅分布值改串 + 段末加历史修正注（该行属历史日志体，按 §7.3 S9 指示加注）；同行其余逐字不动。

**S10｜`docs/capability/TOOL-SKILL-MODULE.md:51`**（deploy R18 行）
- 旧：`| **deploy（R18）** | 2 | W1/R1 | OBSERVED 1（deploy.normal）+ UNVERIFIED 1（deploy.search_status） | OBSERVED→LIVE / UNVERIFIED→待证 | 2 候选（deploy.normal=LIVE 已实证；search_status=UNVERIFIED） |`
- 新：`| **deploy（R18）** | 2 | W1/R1 | OBSERVED 2（deploy.normal / deploy.search_status） | OBSERVED→LIVE | 2 候选（deploy.normal=LIVE 已实证；search_status=UNVERIFIED） |`
- 第 4 列=registry 状态列（改）、第 5 列=归并列（改）；**第 6 列=活体证据维度，逐字保留、不得翻正**（search_status 完整路由活体未实证是既成事实，非本单范围）。前 3 列不动。

**S11｜`docs/capability/VERSION-COMPATIBILITY.md:81`**
- 旧：`| registry 64 契约（整体） | **STATIC 53 / UNKNOWN 9 / LIVE 1 / UNVERIFIED 1**（A1 §五 分布口径） | UNVERIFIED | UNVERIFIED | — |`
- 新：`| registry 64 契约（整体） | **STATIC 53 / UNKNOWN 9 / LIVE 2**（A1 §五 分布口径；registry 态 OBSERVED 2/UNVERIFIED 0） | UNVERIFIED | UNVERIFIED | — |`
- 该行其余列（后三列 `UNVERIFIED | UNVERIFIED | —`）逐字不动。

**明确不入站（本单未改）**：`docs/capability/EVIDENCE-MODEL.md:102`
`| \`deploy.search_status\` 完整路由 | **UNVERIFIED（GENERATED 待证）** | 类级前缀 LIVE 404，禁拼前缀执行 |`
= §三「已实证事实清单」中的**活体证据维度**行，不是 registry 状态分布的承载行；不在授权②「registry 状态分布漂移行」范围，本单**逐字未改**。

## 6. 冻结锚与范围自证（改后回填位）

本单**不得改写**锚（预期值，改后复核见 `implementer/RESULT-HANDOFF-7.md`）：
`standard-product-contracts.md`=`4cd71033…efede`、`evidence/bytecode/manifest.json`=`d7643f75…34f8`、
E 格 68 件清单=`0cfb5119…2301`、`reconciliation.md`=`c29962df…46eb`、`out.json`=`3a07224c…f9d72`、`count.py`=`611e7399…e9ab0`；
P6 终态锚 `ARCHITECTURE.md`=`52b6754c…`、`MODULE-INVENTORY.md`=`bc84310b…`、`drift-diff.md`=`0c8d001d…`。

改前基线（实施时点实测）：`git diff -U0 -- docs/capability/` = **4 hunk**（S1 `ARCHITECTURE.md:138`、S3 `EVIDENCE-MODEL.md:33`、S4 `:40`、S2 `MODULE-INVENTORY.md:42`，均属 HANDOFF-6 已收口改动，未提交）；
`--numstat` = ARCH 1/1、EVD 2/2、INV 1/1。本单新增 hunk 以此为基线另计，逐文件增删数在 RESULT 回报。

## 7. 非站点发现（登记交 main，本单未改）

- **F-7a｜§7.3 站点表外的 registry 态旧值 1 处**：`docs/capability/VERSION-COMPATIBILITY.md:80`
  `| \`udc.deploy.search_status\` | **UNVERIFIED/GENERATED 待证**（registry 状态 \`UNVERIFIED\`，完整路由未证） | UNVERIFIED | UNVERIFIED | — |`
  括号半句「registry 状态 `UNVERIFIED`」承载的正是本单口径源已翻正的那个维度（`status_census` 中 search_status = OBSERVED，`210aa72`），与同文件 S11（`:81`）改后自相矛盾；
  而该行的**层标签**（`UNVERIFIED/GENERATED 待证`）与后三列（版本兼容维度）属活体/兼容证据维度，与 `EVIDENCE-MODEL.md:102` 同性质、不在授权② 范围。
  即：本行是「活体维度表述 + registry 态括注」混写体，**不是 §7.3 边界内的纯 registry 状态分布漂移行**。
- 为何本单未改：判据② 明令「改动**仅限**站点表 S5~S11」，本行不在站点表；改它 = 扩范围，须 main 裁定。
  implementer 保守登记（同 HANDOFF-6 F-6a/F-6b 处置），**未触碰**。
- 建议（仅供 main 裁量，不构成动作）：若要收口，最小改法 = 仅把该括注改为「registry 态 OBSERVED（`210aa72`），完整路由活体未证」，层标签与后三列不动。
- 复扫证据：`grep -rn "registry 状态.?\*\?UNVERIFIED|状态 \`UNVERIFIED\`" docs/capability/` = 1 命中（即本行）；
  `grep -rn "53/9/1/1|OBSERVED.?\(?1\)?|UNVERIFIED.?\(?1\)?|UNVERIFIED 1|LIVE 1" docs/capability/` 在 S5~S11 改后 = 0 命中（纯分布串站点已清空）。

## 8. F-7a 收口｜`docs/capability/VERSION-COMPATIBILITY.md:80` registry 态括注半句（HANDOFF-8 / P8）

- 单：HANDOFF-8（P8 = 授权② 派生发现 F-7a 单站点修正），dedupe_key=`p8-version-compat-registry-parenthesis`；判据与动作清单 = `main/ROUTE.md` §7.4 原文。
- 前置：P7 双签收口 PASS（`auditor/RESULT-AUDIT-HANDOFF-7.md` + `main/P7-VERDICT-CLOSE.md`）。
- 时钟：2026-10-01 ｜ 落盘人：implementer ｜ **本段追加先行于文档修正**。

**口径源（唯一，同 §0/§2~§5）**：
- `core/facts/standard-product/evidence/reconciliation/count_registry_contracts.out.json`
  sha256 = `3a07224c06d1e52b5338c3ca89aa91294536e36d2b8c8665822ae644848f9d72`
  `status_census` = `{VERIFIED_STATIC_BYTECODE 53, OBSERVED 2, UNKNOWN 9}`，**无 UNVERIFIED 键 ⇒ UNVERIFIED 承载 = 0/64**。
- `udc.deploy.search_status` 的 registry 态 = **OBSERVED**，根因提交 = **`210aa72`**「部署历史真面 appVersion/{appGuid} 升级 OBSERVED」（同 §0 两条 OBSERVED 清单）。
- **禁混**：`evidence_level_census` = `{VERIFIED_STATIC_BYTECODE 62, OBSERVED_LIVE 2}`（证据等级轴，另一维度），本段修正值只取 `status_census`。

**grep 重定位（实施时点实测）**：
`grep -n "udc.deploy.search_status" docs/capability/VERSION-COMPATIBILITY.md` → `:80`（与 §7 F-7a 登记行号**一致、无位移**）；同文件 `:112` 的命中属「UNVERIFIED 清单」说明行（版本兼容维度，非 registry 态括注），不在本单范围。

**新旧逐字对照**：
- 旧（逐字，`:80`）：
  `| \`udc.deploy.search_status\` | **UNVERIFIED/GENERATED 待证**（registry 状态 \`UNVERIFIED\`，完整路由未证） | UNVERIFIED | UNVERIFIED | — |`
- 新（逐字，`:80`）：
  `| \`udc.deploy.search_status\` | **UNVERIFIED/GENERATED 待证**（registry 态 \`OBSERVED\`（\`210aa72\`），完整路由活体未证） | UNVERIFIED | UNVERIFIED | — |`
- 改动面 = 仅括注半句 `（registry 状态 \`UNVERIFIED\`，完整路由未证）` → `（registry 态 \`OBSERVED\`（\`210aa72\`），完整路由活体未证）`，即 §7 建议的最小改法。

**不动项（防扩范围）**：
- 层标签 `**UNVERIFIED/GENERATED 待证**` 逐字不动；后三列 `UNVERIFIED | UNVERIFIED | —`（上一版本/下一版本/差异 = 活体与版本兼容证据维度）逐字不动。
- 该行性质 = 「活体/兼容维度表述 + registry 态括注」混写体；本单只翻正其中**承载 registry 态**的括注半句（它正是 `status_census` 已翻正的那个维度），活体维度**不得翻正**（search_status 完整路由活体未实证是既成事实，同 `EVIDENCE-MODEL.md:102` 不入站口径）。
- 修正后与同文件 S11（`:81`，改后 `STATIC 53 / UNKNOWN 9 / LIVE 2`；registry 态 OBSERVED 2/UNVERIFIED 0）不再自相矛盾（解决 §7 登记的矛盾项）。

**范围自证预期值（改后实测见 `implementer/RESULT-HANDOFF-8.md`）**：
- `git diff -U0 -- docs/capability/VERSION-COMPATIBILITY.md` 本单新增 hunk = **1**（基线 = §6 记录的 P6/P7 已收口未提交改动）；`--numstat` 该文件 = **1/1**。
- 本段为**追加**，§0~§7 既有段逐字未改写；改前基线 sha = `34f4e2c2…15b1`（117 行），追加后本件新 sha 与逐段未改证明在 RESULT 回报。
- 本段**不含改后回填**（N-7a 纪律）：所有改后实测值（文件 sha、hunk/numstat、锚复算）一律落 `implementer/RESULT-HANDOFF-8.md`，本件仅一次追加、一次 sha 变化。
