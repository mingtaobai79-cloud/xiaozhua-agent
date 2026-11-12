# STATUS｜core/facts/bpm/ 终态记账（两格 + 豁免裁定）

> 对象：`core/facts/bpm/` 事实模块任务（TASK-GOAL：`事实模块任务｜BPM-flow(flow 域 16 契约+微流程)`，完成定义「2 格 PASS+STATUS」）。
> 本件 = 收口记账件（只增，不改他格/不写运行代码；`core/facts/INDEX.md` 对应行归主线收口，本件不改）。
> 落盘人：implementer（按 main 裁定 dedupe `bpm-d2-waiver-decision` 授权）。时钟：2026-09-27 16:xx CST（本机 `date`）。

## 1. 两格终态

| 格 | 文件 | 绑定字节（sha256，含排版与行尾） | 行数/行尾 | 审计判定 | 状态 |
|---|---|---|---|---|---|
| 格1 | `flow-node-tree.md` | `36ead2218ba4d2d72b2ac6b046f3b7edbf7bf407fe0503c8322b744d2284ec5f` | 16070 B / 140 行 / CRLF 140 | **PASS**（VERDICT-1 三判据+边界 @ 前版 `a843dac6`；VERDICT-2 delta @ `36ead221`） | **已冻结** |
| 格2 | `data-flow-map.md` | `4f3e60a4a66756ccd1c57b7493f24fa20e0a0c990be0a93cc22b37e4a5702a11` | 20703 B / 169 行 / CRLF 169 | **PASS**（VERDICT-3 内容 @ 前版 `7320f81e`；D2 单句修正 @ `4f3e60a4`） | **PASS（经 main 豁免 D2 delta 复审）** |

- 格1 冻结声明：自 `DECISION-1`（dedupe `decision-1-close-verdict2`）起格1 绑定 `36ead221…`，任何写入使 PASS 失效；本轮及此后各轮 sha256sum 复测均一致，未动。
- 格2 判定链：`VERDICT-3`（四判据+边界全 PASS）绑定的是 D2 修正前字节 `7320f81e…`（20476 B）；`DECISION-2`（dedupe `decision-2-d2-lineending-fix`）裁定 §1 前言 L5「行尾 CRLF（同族约定）」为事实性错误陈述，授权单句最小替换 → 新字节 `4f3e60a4…`（20703 B）。该单句替换已由 implementer 反向替换法自证（还原回旧句后 = `7320f81e…`，`ONLY_THAT_SUBSTRING_CHANGED=True`）。

## 2. D2 delta 复审（VERDICT-4）= main 豁免（本裁定）

- **原文**：『D2 delta 复审经 main 豁免（本裁定，dedupe `bpm-d2-waiver-decision`）。』
- 豁免理由（main 独决，三条）：
  ① D2 修正 = `DECISION-2` 明令的**单句机械替换**，内容等价性由替换前后字节自证（格2 `4f3e60a4` 全文含修正句）；
  ② 再审计 = 审计「裁决的执行」而非「新内容」，属重复确认循环；
  ③ 本任务总目标 = 两格事实落盘 + 可溯源，格1 `36ead221` / 格2 `4f3e60a4` 绑定稳定，VERDICT-3 对格2 内容的 PASS 结论在修正句外的全文上一致。
- 影响：`core/facts/bpm/STATUS.md` 不再以 VERDICT-4 为门控（原 ROUTE §13 门控由本裁定解除）；格2 PASS 自本裁定起为**已确认**（不再「待确认」）。
- 如实备注：`auditor/` 目录内**无 `VERDICT-4.md`**（上轮因 LLM 额度墙未落地）；`auditor/verify_delta_d2.py` 脚本在盘可复现，但本裁定不以其为收口条件。

## 3. UNVERIFIED 项（如实，未外推；逐格实测计数）

- **格1**（`UNVERIFIED` 计数 = 13，§9 判定表 L121-124）：
  ① 网关 service 前缀本身（可拼接性）= UNVERIFIED（禁拼前缀当可用 URL）；
  ② 节点树 `children`/`code` 业务语义 = UNVERIFIED（未直读语义层）；
  ③ 微流程运行时行为（调度/执行/流转）= UNVERIFIED（无在盘证据）；
  ④ **BPM 引擎本体（执行器/模型/调度实现）= UNVERIFIED（整段）**（依据 `inputs/desktop-source/TASK-GOAL.md` L6）。
- **格2**（`UNVERIFIED` 计数 = 16，§9 判定表 L150-153）：
  ① 本族（data-flow-map / data-flow-mapping）运行时行为 / 响应实体实际取值 / 鉴权放行实测 = UNVERIFIED（本族**零 LIVE**）；
  ② 网关 service 前缀本身（可拼接性）= UNVERIFIED；
  ③ **BPM 引擎本体（执行器/模型/调度实现）= UNVERIFIED（整段）**；
  ④ 写侧 3 条（`bpm_fill_error_data` / `data_flow_mapping_update` / `…_update_state`）仅登记未启用（`write=True`，执行层 POLICY_DENIED）。
- 链路证据分列（格2）：`module-link-evidence.json` 文件级 = `PARTIALLY_VERIFIED`；`udc→standard-product` 关系级 = `VERIFIED_STATIC_BYTECODE`；**契约关系 ≠ 运行时调用关系**（同文件 limitations[0]，未升级为行为断言）。

## 4. INDEX 对应行（待主线收口，本件不改）

- `core/facts/INDEX.md` 中本两格（`flow-node-tree` / `data-flow-map`）对应登记行 = **主线收口时更新**（ROUTE §7 明令本会话禁动 `core/facts/INDEX.md`，越界）。
- 本会话范围内唯一新增业务件 = `core/facts/bpm/{flow-node-tree,data-flow-map}.md`；本收口件 `STATUS.md` 为完成定义「+STATUS」所要求的第 3 件。

## 5. 终态判定口径

- 依 TASK-GOAL 完成定义「2 格 PASS+STATUS」：两格均 PASS（格2 经 main 豁免 D2 delta 复审后确认）+ 本 STATUS 落盘 → **本模块两格收口完成**。
- ROUTE §5 另载「是否写终态由 main 判定，目标未完成不得写 FINAL/COMPLETE」；本件为**记账件**（STATUS），不代 main 写跨任务 FINAL/COMPLETE；本模块范围内的收口已达成。

---
## 溯源（可复现）
- 格1/格2 sha256、行数、行尾、UNVERIFIED 计数：本轮 `sha256sum` + `wc` + `tr -dc` + `grep -o` 实测（非转述）。
- 判定链：`auditor/VERDICT-{1,2,3}.md`；`events.jsonl`（dedupe：`verdict-1/2/3`、`decision-1/2`、`bpm-d2-waiver-decision`）。
- 裁定：`main` `DECISION` dedupe `bpm-d2-waiver-decision`（本收件所引）。

---

## 6. 新任务 bpm-live 两格记账（只增）

> 本任务 = TASK-GOAL（`xiaozhua-engine-bpm-live`，本会话 `collaboration.json` 目标）。落盘人：implementer。时钟：2026-09-27 19:15 +0800（本机 `date` 实测）。
> 前 5454 B 为上一任务「BPM-flow」既有记账（§1-§5 + 溯源），**逐字未动**：前 5454 B sha256 = `4075dfea56136fcca1cda4861fb16e30d5b9b9c909073073739f04ef9aec50ef`（前缀哈希法，= 本件既有整件 5454 B 整件 sha256 `4075dfea56136fcc…`）。

### 6.1 本任务新增两格（格3 / 格4）

| 格 | 文件 | 绑定字节 | 行/行尾 | 判定链（dedupe 键在盘 events.jsonl / 裁定件） | 证据件 |
|---|---|---|---|---|---|
| 格3 | `engine-behavior.md` | 16072 B / sha256 `7908a94dbad20a082bb3e4cb06ae737dab93949b66eb1f9bbbd572b1a488c67d` | 139 行 / CRLF（CR=139） | 初版 15887 B / `02aa64fa…` → 计数补证（10 发→12 发；main DECISION dedupe `bpm-live-decision-grid1-countfix`）→ VERDICT PASS（auditor 在盘件 `auditor/VERDICT-grid1-newbytes.json`；PASS VERDICT 消息 dedupe `bpm-live-grid1-countfix-verdict`） | `20098 B` / `evidence/engine-behavior-live-20260927T092124Z.json` sha256 `2e62ac5570919d73…`（12 发、§5 表 10 条端点观测、BOOT_0000 数据面 C/T3） |
| 格4 | `bpm-version-map.md` | 18442 B / sha256 `026910f5ff57b8277a49304e9f90d038428d80052c4c3c6cfd4d3fae22bb0e6a` | 140 行 / CRLF（CR=140） | 初版 17618 B / `a7606049…` → D-1/D-2 补证（main DECISION dedupe `bpm-live-decision-grid2-d1d2fix`）→ VERDICT-grid2-postfix PASS（auditor 在盘件 `auditor/VERDICT-grid2-postfix.json`；PASS VERDICT 消息 dedupe `bpm-live-grid2-d1d2fix-verdict`） | `14943 B` / `evidence/bpm-version-map-static-20260927T100255Z.json` sha256 `862fc7d3f54e22f7…` |

### 6.2 前两格绑定（本任务复算未动）

| 格 | 文件 | 绑定字节（复算值） |
|---|---|---|
| 格1 | `flow-node-tree.md` | 16070 B / sha256 `36ead2218ba4d2d72b2ac6b046f3b7edbf7bf407fe0503c8322b744d2284ec5f` |
| 格2 | `data-flow-map.md` | 20703 B / sha256 `4f3e60a4a66756ccd1c57b7493f24fa20e0a0c990be0a93cc22b37e4a5702a11` |

### 6.3 本任务终态口径

- TASK-GOAL（xiaozhua-engine-bpm-live）完成定义「2 格 + STATUS 更新 + RESULT」：格3/格4 均经 auditor 三判据 PASS（补证链完整）+ 本增记 + RESULT → 本任务达成。
- **不写跨任务 FINAL/COMPLETE**（沿用本件 §5 口径：STATUS 为记账件，不代 main 写跨任务终态）。
- `core/facts/INDEX.md` 对应行归主线收口，本会话不动（沿用本件 §4 既有纪律）。

### 6.4 溯源（可复现）

- 绑定值全部为本轮落盘前**本机复算**（`wc`/字节计数 + `sha256` 对 raw 字节，非转述）；2026-09-27 11:15 UTC 实测。
- 裁定/判定链 dedupe 键在盘（`events.jsonl` / `auditor/VERDICT-*.json`）：`bpm-live-decision-grid1-countfix`、`bpm-live-decision-grid2-d1d2fix`、`bpm-live-grid1-countfix-verdict`（格① PASS VERDICT，main DECISION dedupe `bpm-live-decision-grid1-verdict-keyfix` 更正键，本件据此更正后逐字为准）、`bpm-live-grid2-d1d2fix-verdict`（格② PASS VERDICT）。
