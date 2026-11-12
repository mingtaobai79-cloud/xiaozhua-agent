# STATUS｜2小爪 Agent v2 · 适配器切片（三宿主 Adapter + installer 目标态）

更新时间：2026-09-26 02:05 (CST)｜main 收口
目标仓库：`<SEEYON_AGENT_ROOT>`（收口时实测 HEAD `16a384c`）
规范源：`docs/capability/ROADMAP-v2.md` §二/§五、`docs/capability/AGENT-ADAPTER.md`（A8）
完成定义（TASK-GOAL）：5 项全落盘 + 全量测试绿 + STATUS 记录 → **本切片全部达成**

---

## 一、5 项交付（全部落盘 + auditor 三判据 VERDICT=PASS）

| # | 交付 | 目标路径 | 在盘文件 | 审计 |
|---|---|---|---|---|
| 1 | Agent 角色定义包 | `core/role/` | README / ROLE-CARD / BEHAVIOR / EVIDENCE-DISCIPLINE（4） | H-1 PASS |
| 2 | Hermes 宿主注册件 | `adapters/hermes/` | ADAPTER / Hermes-SKILL / MCP-TOOL-MANIFEST（3） | H-2 PASS |
| 3 | Codex 侧指令件 + MCP 清单 | `adapters/codex/` | AGENTS.template / MCP-TOOL-MANIFEST（2） | H-4 PASS |
| 4 | Claude Code 侧指令件 + MCP 清单 | `adapters/claude-code/` | CLAUDE.template / MCP-TOOL-MANIFEST（2） | H-5 PASS |
| 5 | installer 目标态设计 | `installer/` | README / INSTALL-MANIFEST（2） | H-6 PASS |

**在盘 sha256（收口实测，HEAD `16a384c`）**
- `core/role/`：README `03ccde41` / ROLE-CARD `3a5aae0d` / BEHAVIOR `cc7d6e9b` / EVIDENCE-DISCIPLINE `68b60484`
- `adapters/hermes/`：ADAPTER `5280920a` / Hermes-SKILL `747e95e5` / MCP-TOOL-MANIFEST `5f9934a9`
- `adapters/codex/`：AGENTS.template `90b2ae54` / MCP-TOOL-MANIFEST `4c4aeba1`
- `adapters/claude-code/`：CLAUDE.template `890ca675` / MCP-TOOL-MANIFEST `19739d5e`
- `installer/`：README `f9eef11b` / INSTALL-MANIFEST `da3c2a95`

---

## 二、全量测试（实测，非转述）

命令：`.venv/Scripts/python.exe -m pytest tests -q`（本机 Python 3.11.9，经仓库 `.venv`）
结果：
```
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 76%]
........................................................................ [ 96%]
...............                                                          [100%]
375 passed in 7.69s
```
退出码 RC=0。通过数 `375` 与 `README` L30 基线一致——本切片只新增声明级文档/清单，
不改变测试通过数（符合预期）。原始输出另存于协作会话 `main/_s6_pytest_raw.txt`（507 B）。

---

## 三、证据纪律声明（本切片全项遵守）

- **凭据 0 入件**：全部 5 项 13 个文件只写路径引用 / 环境变量机制（`credential_file` /
  `--credential-file` / `SEEYON_CRED_FILE` 宿主侧路径载体 / `path-ref-only`），无任何 token /
  密码 / 凭据值入盘。
- **实现态不虚写**：MCP server 传输层、三宿主注册 / 挂载 / 实装、五能力真实暴露、
  installer 打包 / 安装脚本、v2 宿主专属 schema、`generate` 方法体——全部逐条标
  `UNVERIFIED / 未实现`；不虚写"已实现 / 已落地 / 已安装 / 可运行"。
- **不连网 / 不连真实环境 / 禁 git push**：本切片未连任何真实环境，未执行任何 push。
- **边界遵守**：全程只写 `adapters/`、`installer/`、`core/role/`、`STATUS.md`；
  未触碰 `components/`、`core/facts|tools|skills/`、`docs/capability/`、`tests/` 及
  `seeyon_cli.py` / `seeyon_host_bootstrap.py`（收口实测 17 件 sha 逐项不变）。

---

## 四、环境与裁决登记（收口须如实记录，非本三角色所为者已标注归属）

1. **HEAD 漂移（外部并行会话）**：本切片派单基线曾为 `290de86`，收口时实测 HEAD=`16a384c`
   （"feat(facts): 事实模块批量推进"，另一并行会话提交，连带 commit 了本切片 S1/S2 产物）。
   不影响本切片产物正确性（各件 sha 可独立复算）。
2. **工作树外部噪音（外部并行 facts 会话）**：收口时 `core/facts/` 有 7 条未提交脏改
   （`M INDEX.md` + `?? bpm/ gateway/ runtime/ udc/application/ udc/page/ udc/serial/`），
   **全部属外部并行 facts 会话，非本切片所为**，本切片从未写 `core/facts/`。
3. **宿主指令件名裁决（§0.3，有据偏差）**：Hermes 写保护对 basename ∈
   `{agents.md, claude.md, soul.md, .cursorrules}` 的指令件 **fail-closed**（任意目录、
   无人批准通道即拒；单查询 / worker 模式不可达）。故 S3/S4 指令件以**模板件名**
   （`AGENTS.template.md` / `CLAUDE.template.md`）承载，**安装态规范名由 installer 物化**
   （`<target-repo>/AGENTS.md`、`<target-repo>/CLAUDE.md`，见 `installer/INSTALL-MANIFEST.md`）；
   适配器内**不存规范名文件**。该偏差不改业务目标 / 验收语义，仅改适配器内文件名，
   已如实登记、非静默替换。
4. **S3 件 H1 STAGED 残留**：`adapters/codex/AGENTS.template.md` H1 首行残留 H-3 暂存语境的
   `【STAGED · 待 main 放行】` 标签。处置口径=**以"安装态 H1 生成规则"归一语义**（物化时按
   规范名 + 版本锚 `5.3.517` + schema 锚重写覆盖模板作者期 H1），**不就地改写已 PASS 的 S3 件**
   （保其 sha 绑定 `90b2ae54`）；S4 `CLAUDE.template.md` H1 已直接合规，作对照。

---

## 五、收口判定

- 5 项全落盘（§一）✓
- 全量测试绿：`375 passed`，RC=0（§二）✓
- STATUS 记录：本文件（§三~§五）✓
- **2小爪 Agent v2 适配器切片目标态 = 已达成**（声明级 / 目标态；实现项标 UNVERIFIED，
  后续按 ROADMAP-v2 模块推进线实装，不在本切片范围）。

---

## 六、standard-product 事实格线（P1 字节码核验 + P2 对账，2026-09-29）

> 追加本小节（不覆盖既有 §一~§五）。落盘人：implementer。P3 本体（本小节 + INDEX 行）先按修订版 HANDOFF-3（`handoff-3-index-status-revised`）完成；main 已将该修订版作废并正式解冻 P2 件、发 **HANDOFF-4（dedupe_key=`p2-fix-reconciliation`）** 作 P2 更正 + P3 锚同步收尾，本小节 §6.2/§6.4 与 reconciliation.md 更正即按 HANDOFF-4 完成（实质同源、无重复改动）。
> 会话：`session-20260929-184027-7f85bd1f`。本线口径：纯静态、零活体（无 HTTP / 无 test2 / 无测试应用）。

### 6.1 P1/P2 达成与证据分级

- **P1（字节码核验，TASK-GOAL #1）达成**：现场 cfr（CFR 0.152）反编译在盘 `cip-connector-api-5.3.286.jar`，
  产出九段式事实格 `core/facts/standard-product/standard-product-contracts.md` + `evidence/bytecode/`（含 manifest.json）。
  分级：契约格 A（`com.seeyon.cip.connector.api.sso.SsoService`）/ B（`api.mobile.MobileOrgSyncProviderService`）/
  C（jar 级注册机制：`META-INF/services`·`spring.factories` 均 **ABSENT**，注解驱动 + Spring 上下文解析）=
  **`VERIFIED_STATIC_BYTECODE`**（源 jar 在盘、可现场重跑）；补充格 D（bpm-facade 3.12.101，**jar 本体缺失、不可现场重跑**，
  依据=在盘反编译件 + manifest source_sha256，逐字标注，未升为 A/B 同级）；存疑格 E（ctp-user-api 3.8.215，本体与产物均缺）= **UNVERIFIED**（不编）。
- **P2（对账，TASK-GOAL #2）达成**：`core/facts/standard-product/reconciliation.md` 三条对账逐条引在盘实据——
  ① `components/module_catalog.py` 模块级 `FACT/STATIC` 与 P1 件级 `VERIFIED_STATIC_BYTECODE` 属**两个层级**（模块级声明 vs 件级实测下钻，不互推）；
  ② `UdcOperationRegistry` 基础契约口径实测复现 **裸 64 − 3 别名（`udc.entity.get`/`udc.entity.list`/`udc.attribute.list`）− 2 R18 部署（`udc.deploy.normal`/`udc.deploy.search_status`）= 59 基础**（write 7 / read 57；口径锚 `docs/capability/ARCHITECTURE.md` §五 + `MODULE-INVENTORY.md` §二）；
  ③ 标品域↔客开域边界：registry 全 64 条前缀 = `udc.*`（客开域），标品域在 registry 登记数 = **0**（`MODULE-INVENTORY.md` #05「Capability 数 = 0」），标品域契约由标品 jar 接口定义承载、未进 registry → 两域独立。

### 6.2 上游漂移登记（不代改上游，仅登记）

- **D1（真差异）**：`docs/capability/ARCHITECTURE.md:138` 状态分布「VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 / OBSERVED 1 / UNVERIFIED 1」**不可复现**；
  实测 `OperationStatus` 分布 = 53 / OBSERVED 2 / UNKNOWN 9（UNVERIFIED 0）。**可核验根因**：`OperationStatus.UNVERIFIED` 契约承载 = 0/64；
  `evidence_level="UNVERIFIED"` 全 `registry.py` 仅 `:126` `deploy_search_evidence` 一处，且该变量定义后无引用（dead）；`:128` 实引 `:127` `deploy_hist_evidence`（`OBSERVED_LIVE`）。
  （原句「`UNVERIFIED` 字样仅存于 `:126`」经 F2 精确更正——该串全文件实测 38 处、多为 note 内「网关 service 前缀 UNVERIFIED」，字面不成立。）主口径 64/3/2/59 与 7/57 不受影响。
- **D1 第二上游站点（F1 补登）**：`docs/capability/MODULE-INVENTORY.md:41-42` 的「状态分布 VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 / OBSERVED 1 / UNVERIFIED 1」与 `ARCHITECTURE.md:138` **逐字同串**，同属上游文档时点漂移，本线不代改，仅登记。
- **D2（轴混用）**：`ARCHITECTURE.md:138` 题称「证据等级」实列 `OperationStatus` 枚举；`evidence_level` 轴实测 = `VERIFIED_STATIC_BYTECODE 62 / OBSERVED_LIVE 2`。两轴须写轴引用。
- **写法口径纪律**：源码点计数（46 行 / 45 赋值 / 42 构造点 / 3 replace）与运行期 64 **不可互推**（for 1 行代表 20 条；replace 生成 3 别名）；main 早期 grep 得 47 属此类，与裸数 64 不得混。
- **方法学注记（F3）**：P2 件 `out.json` 数值捕获命令 = `python evidence/reconciliation/count_registry_contracts.py > out.json`；Windows stdout 重定向产生 **CRLF**（该件实测 103 CR + 103 LF，非纯 LF），比较须同法重跑 `cmp` 才一致；通用换行比较会假报不符。
- **P6 修正落实（2026-10-01，HANDOFF-6，授权②）**：§6.2 登记的 D1/D1-第二站点（S1~S4 四处漂移行）已按 HUMAN 授权② 修正——`docs/capability/ARCHITECTURE.md:138`、`MODULE-INVENTORY.md:41-42`、`EVIDENCE-MODEL.md:32-33` 状态分布改 `VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 / OBSERVED 2`（删 UNVERIFIED 项，其承载=0/64）；`EVIDENCE-MODEL.md:40` 补 `udc.deploy.search_status`（write=False）亦 OBSERVED。口径源唯一 = `out.json` `status_census`（`3a07224c…`），新旧逐字对照与范围自证见 `core/facts/standard-product/evidence/docs-drift/drift-diff.md`。授权② 覆盖 §3b「不代改」保守默认，仅动漂移行本身、先出 diff（`git diff -U0 -- docs/capability/` = 4 hunk）。
- **P6 收口 PASS(2026-10-01) + P7 修正落实（HANDOFF-7，授权② 收尾）**：P6 经 auditor VERDICT PASS + main 复现署名收口；§5 登记的 F-6a/F-6b 由 main 裁定另发单步 HANDOFF-7，站点全集经派发时点全目录 grep 复扫补全为 **S5~S11（7 处 / 5 文件）**——`EVIDENCE-MODEL.md:45`、`:47-48`、`:41`、`:128`、`docs/capability/STATUS.md:20`、`TOOL-SKILL-MODULE.md:51`、`VERSION-COMPATIBILITY.md:81` 的 registry 状态分布旧值（`53/9/1/1` / `OBSERVED 1` / `UNVERIFIED 1`）改 `VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 / OBSERVED 2`、UNVERIFIED 承载 0/64；口径源仍唯一 = `out.json` `status_census`（`3a07224c…`），未混 `evidence_level_census`；`EVIDENCE-MODEL.md:102` 与 `TOOL-SKILL-MODULE.md:51` 末列属**活体证据维度**，逐字未改。新旧逐字对照与 grep 重定位见 `core/facts/standard-product/evidence/docs-drift/drift-diff-f6.md`。
- **P7 收口 PASS(2026-10-01) + P8=F-7a 括注单站点收口（HANDOFF-8，授权② 派生发现）**：P7 经 auditor VERDICT PASS + main 独立复现双签收口；P8 只收口 drift-diff-f6 §7 登记的 **F-7a**——`docs/capability/VERSION-COMPATIBILITY.md:80` 的 registry 态括注「（registry 状态 `UNVERIFIED`，完整路由未证）」改「（registry 态 `OBSERVED`（`210aa72`），完整路由活体未证）」，该行层标签与后三列（活体/版本兼容维度）逐字不动、活体维度未翻正；口径源仍唯一 = `out.json` `status_census`（`3a07224c…`），未混 `evidence_level_census`。P6 PASS(10-01) + P7 PASS(10-01) + P8 收口的逐字对照与新锚见 `core/facts/standard-product/evidence/docs-drift/drift-diff-f6.md` §8（该件 §0~§7 既有段逐字未改写、仅末尾追加）。 P8 新锚：`VERSION-COMPATIBILITY.md`=`4cabbde…`（改前 P7 锚 `c20d9385…` 为起点已复核）、`drift-diff-f6.md`=`64a2647a…`（改前 `34f4e2c2…`）。

### 6.3 边界自证（P1/P2/P3 全程）

- 零活体：无任何真实网络调用（交付件内仅 pom.xml 的 Maven XML 命名空间 URL = jar 原文，非调用）；禁连 test2、禁 HTTP、禁建测试应用。
- 凭据 0 入件：`core/facts/standard-product/**` grep credential 类词（password/secret/token/apikey/Authorization/密码/口令）= 0 命中。
- 受控路径 0 改动：`components/`、`core/tools/`、`adapters/`、`tests/`、`seeyon_cli.py`、`seeyon_host_bootstrap.py` 均未改；
  兄弟线领地 `core/facts/item-mgmt|connector|spi/` 只读未写。
- P3（本小节）仅**新增** `core/facts/INDEX.md` 一行 standard-product + 本 STATUS.md 小节；`INDEX.md` 其余行逐字未改（diff 可证），`tests/` 未改。

### 6.4 P1/P2 冻结件 sha256（收口绑定；P2 经 F1/F2/F3 更正后再冻结）

- `core/facts/standard-product/standard-product-contracts.md` = `4cd71033079276353fd9b73ac9793d4aa0057cb22efbba7b490d92fab56efede`（33805 B / 384 行，纯 LF；**P5=HANDOFF-5 后锚，旧锚 `13a82834…d168` 作废**——仅「存疑格 E→契约格 E」翻正 + 文件头本线口径 1 行更新，A/B/C/D 格与附加事实段逐字节未变，`git diff` 可证 1..266 行唯一差异为口径行）
- `core/facts/standard-product/evidence/bytecode/manifest.json` = `d7643f75b916d32742a35c65cd2f0b0f032f3b49464eb93a7d0227291fb634f8`（30198 B；**旧锚 `4e53e5f0…aa44` 作废**——HANDOFF-5 只追加 `sources[3]`=ctp-user-api 3.8.215 VERIFIED_STATIC_BYTECODE 与顶层 `handoff5_append_20261001`，`sources[0..2]`/`toolchain`/`gaps_and_deviations` 语义逐字未变；`git diff --numstat` = 146 增 / 1 删，唯一删行 = `sources` 数组收尾 `]` 随追加位移（`assert sources[:3]` 已证前 3 条目逐字未变））
- `core/facts/standard-product/reconciliation.md` = `c29962dfb7a65249d34d0c5bb33c4ba92bcc594bcc91e236d7ff911b2a7146eb`（17172 B / 161 行，**P2 再冻结锚；旧锚 `246f3108…7203` 作废**，仅被 F1/F2/F3 更正句替换）
- `core/facts/standard-product/evidence/reconciliation/count_registry_contracts.py` = `611e73990acc0b660526e85a7ad8ace650ab09391b093e47995a9bc5b22e9ab0`
- `core/facts/standard-product/evidence/reconciliation/count_registry_contracts.out.json` = `3a07224c06d1e52b5338c3ca89aa91294536e36d2b8c8665822ae644848f9d72`
- **P5 追加登记（2026-10-01，HANDOFF-5，dedupe_key=`p5-ctp-user-api-e-grid`）**：本节 §6.1 中「存疑格 E（ctp-user-api 3.8.215，本体与产物均缺）= **UNVERIFIED**」一句为 P1 时点事实，**已被 P5 翻正**（jar 经 Artifactory 只读拉取到手、sha256 与 profile 逐字一致、javap+cfr 双路核验），现记为 `standard-product-contracts.md` **契约格 E = `VERIFIED_STATIC_BYTECODE`**，证据目录 `core/facts/standard-product/evidence/bytecode/ctp-user-api-3.8.215/`（68 件，清单 sha256 `0cfb5119…2301`）。§6.1 原句按冻结纪律**不改写**，以本条为超集记录；网络纪律见 `main/ROUTE.md` §7.0.1（HUMAN 授权 2026-10-01 的 libs-release 只读 GET 例外，其余活体禁令不变，分级上限仍 `VERIFIED_STATIC_BYTECODE`）。

### 6.5 未做 / 后续（不虚写完成）

- **D1/D2 上游文档更正**：属上游 `docs/capability/ARCHITECTURE.md:138` 与现行 registry 的时点漂移，本线**不代改上游**（非本线领地、TASK-GOAL 未授权），仅登记，待后续专门任务处置。
- **TASK-GOAL #4 闭环留痕核对**：由 main 在收口时做（本 HANDOFF-3 不做）。
- 标品域 `ctp-user-api` 3.8.215 契约 = UNVERIFIED（本体与产物均缺，不编）。

---

## 七、item-connector-probe 收口（main，2026-09-29T12:2xZ 实测）

> 本小节 = 本任务（item-connector-probe，collab 会话 `session-20260929-123555-3f6eb605`）阶段3 收口段，仅登记本任务 item-mgmt + connector 两格交付；**§六 standard-product 属域外并发线 `session-20260929-184027-7f85bd1f`，不计入本任务交付 hash 绑定**。

### 7.1 收口判定 = COMPLETE

| 判据（ROUTE 停止条件） | 实测 | 结论 |
|---|---|---|
| 阶段1 item-mgmt VERDICT PASS | `item-master-data.md` sha `a53f9f37…` 冻结，双源在盘（字节码 javap VERBATIM + LIVE test2 5.3.496）；auditor VERDICT-phase1 = PASS | ✓ |
| 阶段2 connector VERDICT PASS | `connector-readonly.md` sha `fcbd98ae…`（20201 B / 176 LF）；E6 证据 `live-probe-connector-dataflow.json` sha `f0c1fe48…`（2342 B）；字节码 5 件 cmp==docs/audit 原件 5/5 VERBATIM；auditor VERDICT-phase2-connector-e6-rework-b = PASS | ✓ |
| INDEX 三行更新 | item-mgmt / connector 行已刷新（在盘见 `core/facts/INDEX.md`）；spi 行仍 stub（域外不代改） | ✓ |
| STATUS 追加收口段 | 本 §七 | ✓ |
| 全量测试绿 | `.venv/Scripts/python.exe -m pytest tests -q` → **395 passed in 9.09s**（main 实测，非转述；不改既有测试） | ✓ |
| 三角色闭环留痕 | `history/`：7×HANDOFF(main→implementer) + 5×REVIEW_REQUEST(main→auditor) + 5×VERDICT(auditor→main) + 2×COMPLETE(implementer→main) + 本轮 VERDICT，全在盘可溯 | ✓ |

### 7.2 TASK-GOAL #2 达成情况（connector 格）

- **达成**：`udc-runtime/data-flow-map/search` 经 E6 单发实测 = **200 / BOOT_0000 / 非空 901 B（真实业务数据：数据流映射列表含「合同复制」「华为生单」）/ traceId `3252497685650868412` / 19:06:06+0800** → 该 connector 接口 **LIVE=PASS**，满足「≥1 条 LIVE 的连接器接口契约」。
- **诚实边界（不冒充）**：`data-flow-mapping/search-original` = 200/BOOT_1001/空结果 → UNVERIFIED（已调用但业务数据未验证）；A 域其余 4 路由未单发仍 UNVERIFIED；B 设计态 `udc/microflow` 仍 UNVERIFIED（环境 `GET /udc/*` 404）；写面（update/state/bpm/fill-data）仅登记未调用。E5 控制端点（meta-data 面）LIVE PASS 属**不同域**，未据其推 A/B 域 LIVE。

### 7.3 域外并发产物登记（不计入本任务交付，仅如实标注归属）

- `core/facts/spi/**` + `core/facts/standard-product/**`：属并发会话（standard-product 头标 `session-…-7f85bd1f`；spi 头标另一 ROUTE P1）产物。收口 commit `cf45180` 将其与本任务两格**一并入库**（human 一次性提交），但本任务交付 hash 绑定**仅** item-mgmt（`a53f9f37`）+ connector（`fcbd98ae`）+ E6（`f0c1fe48`）；spi/standard-product 不纳入本任务验收。
- **O1（auditor 12:1x VERDICT 非阻断观察）落实**：`STATUS.md` 于本任务 connector 动作**0 字节写入**；STATUS §六 standard-product 小节追加系域外线所为，非本任务阶段3 收口段。本任务自身收口段 = 本 §七。

### 7.4 收口绑定锚（实测值，收口时点复算）

- 仓库 HEAD：`cf451808caf3d3b56fcbaff5904aa394690a10fe`（commit「facts: 四格收口入库…395 tests 绿」，2026-09-29 20:17 +0800；本任务两格 + INDEX + STATUS §六 在此件入库）。
- item-mgmt 格 `core/facts/item-mgmt/item-master-data.md` = `a53f9f37…`（16063 B，冻结未变）。
- connector 格 `core/facts/connector/connector-readonly.md` = `fcbd98aef037465ed39f522d58c6021f5144ed97b9739c68287b146af1696487`（20201 B / 176 LF）。
- E6 证据 `core/facts/connector/evidence/live-probe-connector-dataflow.json` = `f0c1fe480b0f1f90d05ba4ee5d583af4699421f90f112090f08a8a2332684290`（2342 B）。
- 全量测试 `395 passed`（RC=0，main 实测）。
- 凭据 0 入件（本任务交付件 grep 真实值 = 0，仅 ref 路径 + cookie 长度 + 声明时效）。

**本任务 item-connector-probe = COMPLETE（两格 VERDICT PASS + INDEX/STATUS 收口 + 全量测试绿 + 闭环留痕 全在盘）。**

---

## 八、zzprobe 写路径链 · R1 建应用环（implementer，2026-09-30 15:48 CST 实测 · test2 活体）

> 会话 `session-20260930-152536-efab788e`；spec `main/ROUTE.md`（E1–E6）+ main HANDOFF `r1-app-create-handoff-v1`。
> **只写 `core/facts/udc/write-chain/**` + 本 STATUS 追加段，未改其他 facts / registry / components。**

### 8.1 判定 = **BLOCKED（参数错类）** —— R1 未闭环
- 活体登录换会话 cookie（`SY_ACCESS_TOKEN` len 327）→ create 探测 **已用满 HANDOFF 上限 8/8 次**，**均未 BOOT_0000**（无成功 `data` id / `appGuid`）。
- **服务端参数字典坐实**：`CreateOnlyPageApplicationDto` 必填链 = `caption`（`BOOT_1001 caption must not be blank`）→ `hostAppName`（`BOOT_1001 hostAppName must not be blank`）；**DTO 无 `name` 字段**（`name` 键被忽略）。
- 探测 7/8 给 `hostAppName` 两种猜测形态（`default_app_id` 全值 / 前缀 `znxmglpt`）→ **`status:2` 静默业务失败**（非 4xx/非 BOOT_1001）→ 判定：`hostAppName` 须为**真实宿主应用名**，有效值未知。
- 回读负证据：`search-no-page`（zzprobe/znxmglpt/项目管理/空）全部 **0 条**；`application.get` 按 `default_app_id` → **HTTP 404**（网关路由 appId ≠ 应用实体 id，目标 id 形态 UNVERIFIED）。
- **失败三类归因：参数错（主因）；非权限不足（全程 200）；非接口不存在（create/search 端点均 200）。**

### 8.2 交付（在盘可溯）
- 证据件：`core/facts/udc/write-chain/evidence/R1-app-create-20260930.md` + 5 件原始 jsonl（12 记录 / 5817 B，含 traceId）。
- 九段式格：`core/facts/udc/write-chain/write-chain.md`（R1 段已填；R2/R3/R4 骨架待下一 HANDOFF）。
- **回滚：本环未建成任何应用 → 无 `deleteByIds` 清单、无可回滚不可逆写**（建成后的删应用清单待 main 确认，不自行删）。
- 凭据 0 入件：自检脚本比对 live 敏感值 × 全部 evidence + STATUS → **0 命中**；含 token 值的一次 login 响应已脱敏为 `<REDACTED_CREDENTIAL>`，session 临时件已删除。

### 8.3 unblock 动作（交 main 决）
- **唯一缺的输入 = 有效 `hostAppName`**（真实宿主应用名，其下可挂只页应用）。两选：
  ① main 由环境侧给出有效 `hostAppName`（及 `masterEntity`/`pageUrl` 若需要）→ implementer 下一单步直接 create + 回读；
  ② main 放行追加探测预算（>8 次）+ 给宿主应用枚举线索（本仓静态 javap 无宿主应用名字面；search 可见范围 0 条，枚举不到）。
- 在 unblock 前 R1 维持 BLOCKED，**不硬闯、不扩偏移分支**；R2–R4 依赖 R1，暂不发。

### 8.4 绑定锚（实测）
- HEAD `cf45180`；test2 5.3.496；create 成功数 **0**；证据 5 jsonl + 1 md + 九段式格 1 件全在盘。

### 8.5 R1 unblock 轮（main option a 供 E7 · 16:30 CST 实测）
- main 按 8.3 (a) 供给侧给有效 `hostAppName`（E7 = test2 驻留宿主码 `znxmglptcopy579…`，config L59-71 `running_profile:test2`/`k8s_namespace:lowcode-test`）+ E8 只读枚举端点；重发 R1 单环，R2-R4 仍待。
- **实测**：重新登录 OK（cookie 值 0 入件）→ E8 `serial-config/select-entity-list?appName={E7}` = 200/BOOT_0000/**18 实体**（traceId `3253789492108069052`），**但 18 个实体 fullName 全挂 uat 命名空间 `com.seeyon.znxmglpt3289…`（= default_app_id），非 E7/test2 命名空间**。
- create 用满 unblock 允许 **3/3 次全 `status:2` 静默业务失败**（traceId `3253789499322271932` E7+me / `3253789511989070012` default+me / `3253790538922461372` E7-alone 最小体）；**未建成应用，无 `data` id，无 deleteByIds 清单**。
- **根因判定（交 main 裁定）**：create 网关前缀走 uat `default_app_id`，而 `hostAppName`=E7(test2) → 网关把 create 路由到 uat 宿主，uat 宿主绑不到 test2 host app → status:2。最小体（E7+无 me）亦 status:2 ⇒ 根因**非 masterEntity 命名空间污染本身**，而是 **host 经 uat 路由未解析到 test2 host**。
- **失败三类归因：参数错（host 归属未坐实）；非权限（全程 200）；非接口不存在（create/serial-config 均 200）。**
- 交付在盘：`evidence/R1-app-create-unblock-20260930.md` + 4 件 unblock jsonl；`write-chain.md` R1 段已更 unblock 态；**R1 维持 BLOCKED，待 main 再裁**（下一 HANDOFF 建议：create 网关前缀改走 E7/test2 宿主码，或坐实 test2 宿主下可用绑定）。**不硬闯、不扩偏移分支，只动 write-chain/** + 本 STATUS 追加段。**

### 8.6 R1 unblock v2 轮（main 路由修正重发 · 16:49 CST 实测）
- main 按 8.5 建议（option b 环境侧给 test2 宿主码）改 ROUTE：**所有 test2 端点（serial-config/create/回读）网关前缀/appName/hostAppName 三者统一走 T2 test2 驻留码 `znxmglptcopy…064`**，绝不再用 uat `default_app_id`；create 预算 ≤2 次（T2 / T2+masterEntity）。
- **路由修正对只读端点生效（坐实 v1 根因）**：E8 `GET /service/{T2}/serial-config/select-entity-list?appName={T2}` = 200/BOOT_0000/**4 实体全 test2 命名空间** `com.seeyon.znxmglptcopy…064.domain.entity.*`（traceId `3253809089993509052`）；对比 v1 走 uat 前缀时是 18 个 uat 实体 → **前缀决定返回命名空间，v1 根因 = uat 前缀确认**。
- **create 用满 2/2 全 `status:2` 静默业务失败**（T2+test2 masterEntity traceId `3253809266405935292` / T2 最小体 traceId `3253809282847606972`）；**未建成应用、无 data id、无 deleteByIds 清单**。
- **归因改为环境类（非参数）**：test2 hostAppName + test2 命名空间 masterEntity 都给足仍 status:2 → 非参数缺失，判定 **test2 宿主在 test2 网关下 create 写面绑定未坐实（或 T2 前缀网关路由仍非 test2 宿主写面）**；全程 200 非权限、非接口不存在。
- 交付在盘：`evidence/R1-app-create-unblock-v2-20260930.md` + 3 件 v2 jsonl；`write-chain.md` R1 段已更 unblock v2 态。**R1 维持 BLOCKED（环境类），待 main 裁定**：① 环境侧给 test2 宿主可用 create 绑定；或 ② 转 uat 宿主建应用（uat 网关 + uat default_app_id 全套）。**不硬闯、不扩偏移分支，只动 write-chain/** + 本 STATUS 追加段。**

### 8.7 R1 unblock v3 轮（静默成功排除 A + 独立建应用主线 B · 17:21 CST 实测）
- main 复核 v2 后重发 unblock v3：**不再重试已试宿主组合**，切两条独立主线 —— A 静默成功排除（只读 search sweep）+ B 从未试过的设计态草稿写面 `app-draft/create`（E9/E10）。
- **A 静默成功排除 = 否**：`custom-app/search-no-page` 按 caption `zzprobe20260930H1/H2/H3` × 前缀（T2 + default_app_id）共 6 次全 `200/BOOT_0000/content=[]`（0 条）→ 之前 3 轮 `status:2`（custom-app/create）确为「未建成」，非「已建成但回读空作用域」。
- **B 命中 = R1 LIVE PASS（设计态草稿写面）**：`app-draft/create` 可达性探测（default_app_id，`{}`）= 200/BOOT_1001「dataId/draftData 不能为空」（**端点可达、非 404，错误字典坐实必填 = `dataId`+`draftData`**，traceId `3253837769134311612`）；第 4 次（T2 前缀 + `{dataId:1,draftData:"{}"}`）= **200/BOOT_0000/SUCCESS，`data.content=1`**（traceId `3253838679969368252`）。B 预算 ≤4 次用满、第 4 次即收敛。
- **同目标回读（写→回读配对成立）**：`app-draft/select?dataId=1` 走 **T2 前缀** = 200/BOOT_0000/`content={"validate":true,"dataId":"1","draftData":"{}","updateTime":1790759899000}`（**非空草稿**，traceId `3253841201584933052`）；同回读走 uat 前缀 = `content=null` → **证明草稿 host-scoped = T2**。
- **口径差（如实登记，交 main 裁）**：B PASS 的是**设计态草稿写面**，非 v1–v2 反复 status:2 的**只页 custom-app 写面**；草稿 DTO 无 `appGuid`（发布后才 mint）→ R1 收口判据 = **草稿存在性（非空 content + dataId + updateTime）**，非 custom-app 的 appGuid 非空。custom-app 面维持 §8.6 BLOCKED-环境。
- **Side Effects（本轮实建 1 条）+ 回滚（不可逆写，不自行删）**：设计态应用草稿 1 条（宿主 T2，dataId=1）→ 回滚 = `POST /service/{T2}/udc-runtime/app-draft/delete` body `"1"`，**deleteByIds 清单 = [dataId=1 @ T2]，待 main 确认**。
- 交付在盘：`evidence/R1-app-create-unblock-v3-20260930.md` + 4 件 v3 jsonl（16 记录/14 traceId）；`write-chain.md` R1 段已更 unblock v3 态（§R1.10 + 全链汇总拆两行）。**R1 = B 命中 LIVE PASS（草稿面，口径交 main）；R2–R4 待 main 按 R1 收口口径发下一 HANDOFF。不硬闯、不扩偏移分支，只动 write-chain/** + 本 STATUS 追加段。**

### 8.8 R2 实体环（main 裁定 R1 收口后发 R2 HANDOFF · 17:56–18:14 CST 实测 · test2 活体）
- main 裁定（R2 HANDOFF 前置）：① R1 收口口径 = 接受 B 设计态草稿面（custom-app 已 3 轮证据化坐实 host 绑定环境阻塞，非 R1 判据；不发布草稿——会重落 uat/custom-app 面无增量）；② 不可逆写留置不删：实建草稿 `dataId=1 @ T2` 是 R2 挂接宿主，删掉断链，登记 deleteByIds 清单 `[dataId=1 @ T2]`，终态（≥3 环绿）收口时 main 再裁是否清。
- **R2 实测 = LIVE PASS**：数字 appId 由 T2 末尾数字串自算 `5791640252914287064`（`_to_app_id` 规则，勿硬编码）→
  建实体 `POST /service/udc/entity`（`create.md` 收口契约 EntityDto，stereotype=bill/entityNature=MAIN）= **200/BOOT_0000，
  实体 id=`-324146415073342494`（取 `data.content`，非 traceId——skill 坑①）**（traceId `3253879429058791612`）；
  建属性 `POST /service/udc/entity/attribute`（单 AttributeDto，dataType=STRING）= **200/BOOT_0000，属性 id=`-8300366849300533454`**（traceId `3253881685174913212`）。
- **前缀修正（普通可逆，单步内自修，交 main 知会）**：ROUTE E-R2 的 `/service/{T2数字appId}/udc/entity` 网关宿主前缀形态
  实测 **`server_404/status=3`「服务不存在，请重启服务或重新发布应用」**（T2 宿主运行时未发布，与 R1 环境类同根）→
  回退 `create.md` 收口契约的 `/service/udc/entity` 无前缀形态（body.appId 定向宿主）→ 成功；属性同修。
  **未改阶段/范围/验收，未等第三方。**
- **同目标回读（独立重发，不采信写步转述）**：`GET /service/udc/entity/primary/select-by-appid/{T2数字appId}` 命中实体行
  （id/guid=`6233922445365373130`/tableName=`zzprober2_6233922445365373130`/publishState=UNPUBLISH 全非空；行数 48→49，
  traceId `3253894632135723196` 复证）；`GET …/attribute/select-all-by-entity-id/{entityId}` 命中字段行
  （`ZzprobeR2FieldA` dataType=STRING，**entityId 归属=`-324146415073342494` = 非孤儿**，traceId `3253894642202052796` 复证）。
  `fullName` 设计态 UNPUBLISH 回读 = null（发布才 mint，不冒充非空）。
- **Side Effects + 回滚（不可逆写，不自行删）**：本轮实建 1 实体 + 1 字段（宿主 T2，UNPUBLISH，未落物理表）。
  回滚清单待 main 确认：字段 `POST /service/udc/entity/attribute/delete` body `-8300366849300533454`（registry L31 在盘）；
  **实体级 delete 端点 registry 无 op = UNVERIFIED**（须 main 裁定/环境侧给端点；字段删后实体可留置）；连带 R1 草稿 `[dataId=1 @ T2]`（§8.7 留置）。
- 交付在盘：`evidence/R2-entity-create-20260930.md` + 8 件 R2 jsonl（含崩溃轮 precheck 防重 + 复证轮）；`write-chain.md` R2 段九段式已填（§R2.1–R2.9 + 全链汇总 R2 行）。**R2 = LIVE PASS；R3–R4 待 main 下一 HANDOFF。凭据 0 入件（自检 0 命中：17:56 login 回显 token 已脱敏、session 临时件已删）。**

### 8.10 R3 页面环（main 发 R3 HANDOFF · 18:43–18:44 CST 实测 · test2 活体 · 第 3 环）
- main 三裁定（R3 HANDOFF 前置，全在 §八.8 报过的事上）：①前缀形态采纳 implementer 修正——设计态写/读面（entity/attribute/page）走**无前缀 + body.appId=T2NUM（自算勿硬编码）**，`/service/{T2NUM}/…` 网关宿主前缀 = T2 运行时未发布 → server_404，R3 起不再用；②不可逆写留置不删，deleteByIds 清单终态收口 main 一并裁；③fullName 设计态回读 null 如实接受。
- **R3 实测 = LIVE PASS（一次收敛，第 3 环达成北极星「≥3 环闭环」）**：
  - 建 LIST 页 `POST /service/udc/page-info/base-info/create`（**无前缀 + 单 PageDefinitionDto，非数组——skill 坑② 遵守；body 全给必填链** pageType/pageUrl(顶层+items)/curTerminalType/actionType=NORMAL/masterEntityIds=R2 实体 id）= **200/BOOT_0000/SUCCESS**，
    页面 id=`-1050844983045962497`，**`relationGroupId=-1825103036523123395`（取 data.content，非 traceId）**（traceId `3253924213555202236`）。
  - **同目标独立复证回读**：`GET /service/udc/page-info/select-by-appId/{T2NUM}`（无前缀）= 200/BOOT_0000，**展平 `row.pageList[]`（skill 坑③：顶层扫描=假阴性）后 flat 62 行命中 1 行**：
    `pageType=LIST / caption=zzprobe列表 / pageUrl=zzprober3list / relationGroupId=-1825103036523123395`（**非空，与建页返回同值**，traceId `3253924226641430716`）。
  - 未触发止点条件：无 BOOT_1001（缺字段，一次收敛）/ status:2 / server_404（宿主绑定，无前缀形态绕开）/ 401 / 404。
  - **口径如实登记**：命中行 `masterEntity` 设计态 UNPUBLISH 回读 = null（同 R2 fullName null 口径，非空断言按 caption+relationGroupId+pageType+pageUrl 取，未冒充）；页面随 RELEASE 构建发布 = 未做（归 R4/加分环）。
- **Side Effects + 回滚（不可逆写，main 裁定 2 留置不删，不逐环删，终态收口 main 一并裁）**：
  本轮实建 1 个 LIST 页面（宿主 T2，UNPUBLISH）。**deleteByIds 清单（4 项）=
  [R3 页面 relationGroupId=-1825103036523123395（页面 base-info 删除端点 UNVERIFIED：registry page 域无 delete op，
  javap STATIC 锚 `UdcPageProxyAppService.deleteByIds` + 路径字面 `{entityAppName}/{entityName}/{controlId}/delete-by-ids` 前缀未定未 LIVE，不臆造）]
  + [R2 字段 -8300366849300533454（registry L31 attribute.delete 在盘）] + [R2 实体 -324146415073342494（实体级 delete UNVERIFIED）]
  + [R1 草稿 dataId=1 @ T2]，终态收口交 main 一并裁。**
- **北极星进度（main 侧）**：R1 草稿面 + R2 实体面 + **R3 页面面 = 3 环 LIVE 闭环达成「≥3 环」北极星**；R4 数据写入 = TASK-GOAL 可选加分项，等 main 裁。
- 交付在盘：`evidence/R3-page-create-20260930.md` + 2 件 R3 jsonl（184308 login / 184316 create+回读）；`write-chain.md` R3 段九段式已填（§R3.1–R3.9 + 头部 R3 bullet + 全链汇总 R3 行更正为 LIVE PASS 实测态）。**R3 = LIVE PASS；R4 待 main 下一 HANDOFF。凭据 0 入件（自检 0 命中：18:43 login 回显 token 已脱敏、session 临时件已删）。**

### 8.9 R1 收口修正 + 北极星达成（HUMAN 接管通报 18:40 +08 · main 收口 · 只追加不改前段）
- **HUMAN 接管通报**（events `20260930T103226.452334Z-human-to-main-HUMAN_MESSAGE`）：R1 建应用环由
  主控（用户侧）接管直查完成，main 侧无需再探测。HUMAN 侧结论证据 `core/facts/udc/write-chain/evidence/
  R1R2-write-chain-20260930.json`（HEAD `cf45180` 后追加，untracked）：
  - **`entity.create` / `deploy-normal` / `meta-data.select-entity` 三环 = LIVE PASS**（HUMAN 侧 @ znxmglpt，
    北极星依据）：zzprobeEntTest `id=6655869284078002850`（trace 3253778497914538172）/ zzprobeSimple
    `id=-9036848312021150932`（trace 3253892200966129852）；deploy-normal deployId `-5934667574923322524`
    SUCCESS jar 1.0.11175 ~19min / `-3075684243680240588` 18:19:49 编译完成；meta-data.select-entity 部署后
    元数据注册（ZzprobeEntTest 45 attrs / ZzprobeSimple 9 attrs，端点在 extmetadata jar `UdcMetaDataController.
    selectEntity`，需 appName+fullName 双键）。
  - **`custom-app/create` = BLOCKED-平台 NPE**（`create4CustomPage:892` NPE，双实体 bill 45attrs/standard 9attrs
    复现坐实平台侧缺陷；元数据匹配全 200 后才 NPE；retry_matrix 6 组坐实参数字典：`masterEntity`=裸 fullName
    字符串（非 JSON，`UdcEntityMetaDataSearchDto.setFullName` 字节码证实）、`hostAppName`=宿主应用名）。
    **定性平台侧缺陷或存在未公开前置条件，非 agent 可解，按单一证据源纪律不再硬闯。**
- **main 侧 3 轮 unblock（§8.5–§8.7）复核**：custom-app 面 status:2（v1 供 hostAppName / v2 T2 路由修正 /
  v3 独立主线 A 静默成功排除=否）与 HUMAN 侧 NPE 同根（宿主绑定/平台侧），**main 侧证据并入事实格 §R1.7/§R1.8/
  §R1.9 注记，不再重试**。main 侧 unblock v3 B（app-draft 草稿面 `dataId=1 @ T2`）与 R2（ZzprobeR2 @ T2）
  为独立复现分支件，**如实登记但不作为北极星依据**（北极星 = HUMAN 侧三环 LIVE PASS）。
- **北极星「≥3 环闭环」达成口径（收口）**：HUMAN 侧 `entity.create` + `deploy-normal` +
  `meta-data.select-entity` 三环 LIVE PASS（+ 双实体复现）= 写路径「实体→部署→元数据」全链走通并逐环回读
  → **达成 TASK-GOAL 完成定义 1（≥3 环闭环，每环 LIVE 回读证据在盘）**。custom-app 只页应用面维持
  BLOCKED-平台 NPE（如实登记，非北极星环）；R3 页面/R4 数据写入未实施（HUMAN 通报测试应用改平台级入口
  另起，等 HUMAN 排期）。
- **测试应用登记（TASK-GOAL 完成定义 3）**：
  | 对象 | 宿主 | 用途 | 留置决定 |
  |---|---|---|---|
  | zzprobeEntTest / zzprobeSimple（UNPUBLISH 实体 ×2） | znxmglpt（HUMAN 侧） | 双实体复现 NPE 的平台测试体 | **待 HUMAN 裁定去留**（main 不自行删） |
  | deployId -5934667574923322524 / -3075684243680240588（TEST 部署 ×2） | znxmglpt（HUMAN 侧） | 触发实体元数据注册 | **待 HUMAN 裁定** |
  | 设计态草稿 dataId=1（app-draft 面） | T2（main 侧 §8.7） | R1 草稿面独立复现 | 留置，终态收口裁 |
  | ZzprobeR2 实体 -324146415073342494 + 字段 -8300366849300533454 | T2（main 侧 §8.8） | R2 实体面独立复现 | 留置；实体级 delete 端点 UNVERIFIED |
- **不可逆写清理总清单（终态收口交 main/HUMAN 一并裁，不逐环删、不自行删）**：HUMAN 侧 2 UNPUBLISH 实体 +
  2 TEST 部署（待 HUMAN 裁定去留）；main 侧 app-draft 草稿 delete body "1" + 属性 delete body -8300366849300533454
  + 实体 delete（端点 UNVERIFIED）。
- **ROUTE.md 已按 HUMAN 通报重写为收口修正件**（R3/R4 不再由 main 侧实施，等 HUMAN 排期平台级入口）。
  本段只追加，未改 §八.1–§八.8、未改其他 facts 目录（四格已收口冻结）、未删桌面原件。

### 8.11 R3 接受裁定 + 收口确认（main · 2026-09-30 18:52 CST · 只追加不改前段）
- **在途交叉裁定（非违规）**：时间线 = R3 HANDOFF 投递 18:33 → R3 执行 18:43–18:44 → main 取消 DECISION 投递 18:46。
  执行早于取消投递，implementer 在执行时 R3 HANDOFF 仍有效 → **无违规**；且 HUMAN 通报的「停止探测」边界是
  **znxmglpt（uat 侧）**，R3 执行在 **T2（test2 侧）**，不在停止范围内 → **R3 交付有效，main 裁定接受**。
  main 上轮 DECISION（`r3-cancel-closeout-v1`）的作废范围澄清为「**不再新派环**」，不追认已完成交付为无效。
- **R3 复核 PASS**：建 LIST 页无前缀单 dto 一次 BOOT_0000（页面 id=-1050844983045962497，
  `relationGroupId=-1825103036523123395`，traceId 3253924213555202236）；展平 `select-by-appId` 回读命中同值
  （traceId 3253924226641430716，flat 62 行命中 1 行 caption+pageUrl+relationGroupId 非空）→ 写→回读配对成立；
  命中行 masterEntity 设计态 null 如实（未冒充）；凭据 0 入件自检 0 命中；只动 write-chain/** + STATUS 追加段。
- **段号顺序说明（可逆小瑕疵，登记不重排）**：盘上顺序为 §8.8 → §8.10（implementer R3 段）→ §8.9（main 收口段），
  两段号唯一、内容独立；implementer 显式避让同号（PROGRESS 已述），属并发追加的物理顺序差，非内容冲突。
  按「不改历史追加段」纪律保留现状，本段说明避免后续误读。
- **TASK-GOAL 完成定义逐条核对（main 复核）**：
  1. **≥3 环闭环（含每环 LIVE 回读证据在盘）= 达成（双链）**：main 侧 R1 草稿面（app-draft/select 回读非空）+
     R2 实体面（select-by-appid/select-all-by-entity-id 双命中非孤儿）+ R3 页面面（select-by-appId 展平命中同值）；
     HUMAN 侧 entity.create + deploy-normal + meta-data.select-entity 三环 LIVE PASS。**建应用→实体→页面 全链逐环配对**。
  2. **write-chain.md 九段式（含每环 Side Effects + 回滚方式）= 达成**：R1（§R1.1–R1.10）/R2（§R2.1–R2.9）/
     R3（§R3.1–R3.9）+ 全链汇总表（8 行，含 R4 未实施裁定 + 侧效应 + 回滚清单）。
  3. **STATUS 追加段 + 测试应用登记（appGuid/用途/留置决定）= 达成**：§8.1–§8.11（本段含登记表 + 清理清单）。
     注：草稿面/设计态无 appGuid（发布才 mint）→ 登记以 dataId/entityId/relationGroupId 为对象标识，口径如实。
  4. **三角色闭环留痕全在 history/ 可溯 = 达成**：events.jsonl + history/inbox + history/outbox 全序可溯
     （START/HANDOFF×5/BLOCKED×3/PROGRESS×3/HUMAN_MESSAGE/DECISION/REVIEW_REQUEST）。
- **不可逆写清理总清单（终态一并裁，不逐环删、不自行删）——5 项**：
  | # | 对象 | 宿主 | 清理端点 | 状态 |
  |---|---|---|---|---|
  | 1 | 页面 relationGroupId=-1825103036523123395 | T2（main 侧 R3） | 页面 delete 端点 **UNVERIFIED** | 留置待裁 |
  | 2 | R2 字段 -8300366849300533454 | T2（main 侧 R2） | `POST /service/udc/entity/attribute/delete`（registry L31 在盘） | 留置待裁 |
  | 3 | R2 实体 -324146415073342494 | T2（main 侧 R2） | 实体级 delete 端点 **UNVERIFIED** | 留置待裁 |
  | 4 | R1 草稿 dataId=1 | T2（main 侧 R1） | `POST /service/{T2}/udc-runtime/app-draft/delete` body "1" | 留置待裁 |
  | 5 | zzprobeEntTest / zzprobeSimple（UNPUBLISH 实体 ×2）+ 2 轮 TEST 部署 | znxmglpt（HUMAN 侧） | — | **待 HUMAN 裁定去留** |
- **R4 裁定 = 不派**（T2 运行时未发布 → data/query 同根不可达；实体 UNPUBLISH 无物理表；HUMAN 平台级入口待排期）
  → 关闭该局部环境分支，**不依赖它的主线（≥3 环）已达成，非总任务停止**；契约蓝图留 write-chain.md §R4 供后续复用。
- **本段只追加**：未改 §八.1–§八.10、未改其他 facts 目录（四格已收口冻结）、未删桌面原件；HEAD 仍 `cf45180`（本轮仅工作区追加）。

### 8.12 更正注记（main · 2026-09-30 19:08 CST · 只追加，更正 §8.11 清单 ⑤ 的留置状态）
- **§8.11 清理清单 ⑤ 更正**：HUMAN 侧 znxmglpt 2 UNPUBLISH 测试实体（zzprobeEntTest / zzprobeSimple）
  **已由 HUMAN 侧删除**（`udcEntityDeletePost` GraphQL，双双回读 `content=None` 确认；
  证据 `evidence/R1R2-write-chain-20260930.json` 4201 B 版 cleanup 字段，implementer 19:04 PROGRESS 复核在盘）。
  去留项「待 HUMAN 裁定」状态 → 已裁并执行。
- **留置清单更正后 = 4 项待终态裁**（main 侧）：① R3 页面 `relationGroupId=-1825103036523123395`
  （delete 端点 UNVERIFIED）② R2 字段 `-8300366849300533454`（registry L31 在盘）③ R2 实体 `-324146415073342494`
  （级 delete UNVERIFIED）④ R1 草稿 `dataId=1@T2`（app-draft/delete body "1"）；+ HUMAN 侧 2 轮 TEST 部署
  （deployId 两值，部署清理端点 UNVERIFIED）。**main 侧 4 项一律不自行删，终态收口一并裁。**
- 双 VERDICT PASS 在盘（`closeout-verdict-v1` 5/5 + DRIFT-1 已按 main option (a) 关闭；`r3-verdict-v1`
  R3 三判据 PASS 无补证项），implementer `closeout-ack-r3-cancel-v1` 回执零异议（CLOSEOUT-ACK.md 在盘）
  → **会话收口条件齐**，main 发 COMPLETE。

### 8.13 R4 数据环收口（main · 2026-10-01 04:2x CST 实测直读证据件 · 只追加不改 §8.1–§8.12）
- **本环执行主体 = HUMAN controller 代跑**（implementer 的 R4 HANDOFF `r4-data-write-handoff-v1` turn 挂死被停，
  main 按 HUMAN 指令**不再重派同一 HANDOFF**，改由 main 收口落格）。事实源 = `evidence/R4-data-write-readback-20261001.json`
  （1959 B，git `aa5dfef`）+ 通道探测 6 件 jsonl，非转述。
- **回读环 = LIVE PASS（第 4 环 · TASK-GOAL 加分项落地）**：物理表 `zzprobenew26419954374508955097_test2.zzprobeen_m2128447441671076182`
  新增 1 行（`id=147154`，`ziduan1='ZZPROBE-R4-202610010406'`，`tenant_id=-8112660841495312922`）→
  `POST /service/zzprobenew26419954374508955097/udc-runtime/data/query`（三键 `appName/entityFullName/dataId`，
  复用 `runtime-data-read.md` §3 未重探）→ **`BOOT_0000` / traceId `3254491595596105916`**，回读行 `id` 与 `dataId` 同值、
  `ziduan1` 逐字一致且非空 → 写→回读同一目标配对成立，非 200 空结果。
- **口径三分（不虚写）**：① 回读面 REST = **LIVE PASS**；② 写入面 = **DB 直插实测（非 API 写面）**；
  ③ **API 写入通道 = UNVERIFIED-待终端字段协议** —— 新事实：**运行态 REST 路由 = 页面注册函数节点的动态投影**
  （`UdcRestPathParse`；SEARCH_LIST 页只挂 `/udc-runtime/data/query`）→ 通道 A dynamic-rest create 4 次全
  `BOOT_4002 应用坐标数据不存在`（traceId `3254493466155026620`/`3254493476036806844`/`3254493480902199484`）、
  16 候选写路径全 404；通道 B GraphQL 设计面+proxy 面无数据保存 mutation（`graphql-absent-*`）；补全前置需建
  CRUD/DETAIL 页，而 `addPage`(`udcPageInfoBaseInfoCreatePost`) 被 `BOOT_1000 页面终端信息为空` 阻断
  （facade 校验，**页面终端数组字段名未解**）→ 属平台协议缺口，非 agent 可绕，**不再重探、不硬闯**。
- **物理表新事实**：实体表落**应用专属 schema**（非 `udc_test2`），表名 `zzprobeen_m<entityId>`；
  `zzprobeda_8660586335710379483`（zzprobeData）**不是** ZzprobeEnt1 的表（全库 `information_schema.COLUMNS` 搜列名坐实）。
- **纪律偏差如实登记（凭据 0 入件）**：route-A 两件 jsonl（`aa5dfef` 内）的 `resp_body_redacted` 含未脱敏
  `access-token` JWT → main 已就地脱敏为 `<REDACTED-JWT>`（每文件 `git diff --numstat` 1 增/1 删，CRLF 与其余记录字节不变，
  3138→2841 B / 3102→2805 B，`grep -c eyJ0eXAi` = 0）；**残留**：原 token 仍在 git 历史 `aa5dfef` blob，历史重写与否待 HUMAN 裁。
- **落格**：`write-chain.md` §R4 由「未实施·main 裁定不派」更正为**实测态九段式 R4.1–R4.9**（含 Side Effects =
  新增 1 行数据 + 回滚方式）+ 全链汇总 R4 行 + 北极星段补登第 4 环；文件头 R3 段口径随之更正。
- **归属与预算（不并口、不追认）**：implementer 探测程件 `evidence/R4-data-write-20261001.md`（6895 B）件头自记
  「收口权已按 HUMAN 指令移交 main，本件不作第二收口件」→ §R4 唯一权威 = main 收口版，两源无口径冲突。
  该件自记通道 A **实发 4 次 > HANDOFF ≤3 上限**：main 采信其 `BOOT_4002` 归因、**不采信为写面 PASS、不追认新预算**，
  后续同型 HANDOFF 仍按 ≤3 硬上限。
- **清理清单更新（main 侧 4 项 → 5 项，一律不自行删）**：① R3 页面 `-1825103036523123395` ② R2 字段 `-8300366849300533454`
  ③ R2 实体 `-324146415073342494` ④ R1 草稿 `dataId=1@T2` ⑤ **新增 R4 数据行 `id=147154`**（DB DELETE，REST 删除端点 UNVERIFIED）。
  注：原清单曾计「R1 草稿 + HUMAN 侧 2 部署」，HUMAN 侧 2 部署留置状态仍按 §8.12 口径不变。
- **本段提交边界（如实）**：只 commit `core/facts/udc/write-chain/**`；**STATUS.md 未随本段 commit** ——
  该文件当前工作区还含另一线未提交产物（§6.4 P5 锚更新 + §九 SPI P1–P3 段，归属 `session-20260929-182955-a559c772`），
  main 不代提交他线工作；§8.13 已在盘，待该线收口或 HUMAN 裁定后一并 commit。

## 九、SPI 事实格线（spi-facts）P1–P3 阶段结论（implementer · 2026-09-30T19:52Z 实测 date -u · P3 纯落盘 0 网络 · 只追加）

- **G1 达成**: SPI-EXT-REG-01（spi-ext-registration.md）+ SPI-EXT-LOAD-01（spi-ext-loading.md）两格 VERIFIED_STATIC_BYTECODE，auditor VERDICT=PASS（P1）；字节码证据件在盘可复算。
- **G2 部分达成（禁写终态）**: 配置面 LIVE 只读证据在盘——e1 快照（2026-09-22）+ e2 新鲜复核（2026-09-30T19:28Z 本地直连 Nacos，0 SSH/0 凭据），`seeyon.spi.enable=true`、`spi-plugins` 0 命中。运行态「真实加载/调用表现」子面**未达成**：步3 需经 SSH `10.0.0.1` 取 `kubectl logs`，实测 Host key verification failed，属需人工信任判定（任何角色禁绕过）。判级口径：`enable=true` 只证配置、不证加载、不证调用；「未加载插件」推断源=P1 VERIFIED_STATIC_BYTECODE（非运行态直接观测）。
- **G3 本批落地**: `core/facts/INDEX.md` L23 spi 行由 stub 替换为三格如实分级；本段为 STATUS 追加段（不动任何既有段，避让另一线 §8.12）。
- **G4 闭环留痕**: 本线 HANDOFF→RESULT→REVIEW_REQUEST→VERDICT 全在 `session-20260929-182955-a559c772/history/{inbox,outbox}/`（P1 两轮 + P2a/P2b + P2 终格 PASS）。
- **三格最终 sha 锚（P3 落盘后 date -u 实测重算）**: registration 17204B `c5e63495…`、loading 27122B `6f19ad99…`、live 8126B `b43ced81be1c53e40341f424a9b419a86be5f435ec2b92de8563d1120ade779b`；evidence: e1 3594B `7f6d7f52…`、e2 2493B `f3d6639e…`（live 格 P2 旧锚 8125B/`c8ddc9aa…` 作废）。
- **本批异常如实登记（行尾事件 → 影响复锚口径）**: 订正 live 格时，首次使用的就地编辑（perl -i 文本模式）剥离了全文件 67 个 CR（CRLF→LF）并将 L7/L15 置空。已逐行重建 CRLF 并核对：**除被授权改写的 L7（阶段标记）与 L15（新鲜复核时间收敛）外，其余 65 行文本字节未变**，§8/§9/§10 的判级与证据主张一字未动（`diff --strip-trailing-cr` 对备份可复现）。因原 L15 残留句无法逐字节复现（差 1 字节），P2 锚 `c8ddc9aa` 不能用「还原原文再改」路径复算；P3 产出锚以 `b43ced81…`/8126B 为准，main/auditor 复锚请用此值，并把该行尾事件计入审阅判据。备份留在 `implementer/_scratch/`（live-LFstripped-backup.md）。
- **P4 待派（两条独立路径，由 main 裁定，本线未自派）**: (a) 人工确认可信 SSH host key 或提供可信 kubeconfig → `kubectl logs` grep SPI 加载关键串，硬上限 3 发；(b) 不依赖 SSH 的只读通道盘点——`config/environments.yaml`（`nacos_endpoints.mse-c19f9232`，readonly: true）+ test2 网关 `POST /udc-runtime/*`，目标是拿到「插件是否真被加载/调用」的运行态侧证，避免重复 P2 配置面结论。
- N2/N4（涉 P1 冻结件字节订正）按 main 门6 裁定留 P3b，本批未动；凭据 0 入件（本段仅引用路径与键名）。

## 十、SPI 运行态边界（P4/P4b）阶段结论（implementer · 2026-09-30T20:34:11Z 实测 date -u · P3c 纯落盘 0 网络/0 SSH/0 探测/0 写面 · 只追加，不动任何既有段）

- **G2 运行态子面 = 未达成（禁写终态）**: P4b 把「非 SSH 通道不足以观测 SPI 运行态加载链」升格为**有界实测负结果事实**——e3 通道盘点 + e4 只读探测 3 发（硬上限内，即停）全部传输层失败：P1 网关根 TLS 中断 exit 35（2026-09-30T20:20:41Z）、P2/P3 Nacos naming `/ns/service/list` 连接重置 exit 56 ×2（2026-09-30T20:20:42Z），**无 HTTP 200 正文、无加载链关键串命中**。0 凭据入件、0 写面操作。
- **P4a 需人工（开放项，任何角色禁绕过）**: 运行态闭合仅剩 ①可信 SSH host key / 可信 kubeconfig → 只读 `kubectl logs` grep SPI 加载关键串；②写面观测方案（涉共享 test2 环境 + 凭据 + 改配），须主控用户授权。二者未取得之一，G2 不判达成。
- **G1/G3/G4 保持**: 两格 VERIFIED_STATIC_BYTECODE（P1 PASS）、配置面 LIVE PASS（e1/e2, enable=true 新鲜复核 2026-09-30T19:28Z）、闭环留痕 HANDOFF→RESULT→REVIEW_REQUEST→VERDICT 在 `session-20260929-182955-a559c772/history/` 可溯（P4b auditor VERDICT=PASS 2026-09-30T20:28Z）。
- **本段 P3c 锚迁移（写后 `date -u` 实测重算，见下方 RESULT 复算行）**: 新格 `core/facts/spi/spi-ext-runtime.md` §8 sha 内联后 6777B/`253e98d51ce5b12b2a77b10da3b289faeba63be29a67fa0ee7540ba4ab6a15c1` → **7123B/`64f332dd59172af7133e170d70beb4437ff373cf185fec4ebd51b27519370d4e`**（仅 §8 L44/L45 两行变动，`diff --strip-trailing-cr` 自证；该文件实测为 LF 行尾，本批改写保持 0 CR 不变）；`core/facts/INDEX.md` 仅 L23 spi 行由三格更新为四格：7227B/`21d65f08…`（并发他线追加后的实测值，门8 `348cdd02`/6976B 早已失效）→ **7600B/`b37456418191a8e7cdb65f441a61d8f4a9d23de96a33e3213a757150fc44f2e7`**；本段自身 sha 因自引用不落本段，由 RESULT 登记。本段为 STATUS 追加段，他线 §8.1–§8.13 与本线 §九 逐字节未触。
- **N2/N4（涉 P1 冻结件字节订正）按门6/门11 留 P3b，本批未动。**

## 十一、SPI 线 P3d（末批文档一致性微订正）锚迁移登记（implementer · 2026-10-01 · 0 网络/0 SSH/0 写面 · 纯追加，不改任何既有行）

- **R1 口径**：历史时点锚一律作废，现盘为唯一基准；本节只登记锚迁移与表述落地（NB-2/NB-3 + OBS-1/OBS-2），
  证据主张、分级、九段结构、结论、INDEX 与 inventory 一字未动，非边界重开。
- **registration 锚迁移**：`c5e63495…`/17204B（§九 P3 时点）→ **历史作废**；现锚 `d293e5f068d3fca09eac396ae566e208da09c3a48e8050317d607819ef3347bb`/17337B
  （N4 逐字引文订正，仅引文呈现字节变化；P1 VERDICT PASS 不受损）。（OBS-2）
- **README 锚迁移**：P1 `d174efc5…`/2897B → P3b `4311434feb9ec5db7966b69d49f5e46567508654590d4a75b0df133be78502e1`/2897B → P3d 新值
  （新值以本批 RESULT 重算登记为准；沿 §十 口径，本节不自引 sha）。
- **INDEX 锚迁移**：门13 `f8a5d6f3…`/8216B → 现锚 `42abee5fba23ed5d488c62b351894e002609cf1e2ebb0a8cd52cb3935c9fbec8`/8754B
  （NB-1 排版订正 + 他线并发，R1 重锚）。
- **状态收口（本线，非终态）**：G1/G3/G4 达成；G2 **部分达成**——运行态子面为有界实测负结果事实，闭合需 P4a 人工路径
  （可信 host key/可信 kubeconfig 只读 `kubectl logs`）或写面授权，本线不可自派；P3d 为末批文档一致性微订正，
  PASS 后不再开文档批次。**不写 G2 达成，不写 COMPLETE/终态。**

## 十二、SPI 线 P8｜spi 事实格收口面订正（implementer · 2026-10-08T03:31:58Z 实测 date -u · 0 网络/0 SSH/0 kubectl/0 HTTP/0 探测/0 建应用/0 写观测面 · 只改 core/facts/INDEX.md 第 23 行 + 本段尾部纯追加）

- **本批边界（单 HANDOFF 单写面）**: 依 HANDOFF-P8（dedupe `p8-handoff-20261008T0330Z`）订正 INDEX.md 第 23 行 spi 行的状态段与锚段，并追加本段。除该两件外 0 字节改动；`core/facts/spi/**`（四格 + evidence/live e1–e9 + hashes 清单 + README）、docs/audit/**、tests/**、components/、core/tools/、adapters/、seeyon_cli.py、seeyon_host_bootstrap.py 全部未触碰，写前/写后逐值复算零漂移（见 RESULT-P8 对照表）。写前基线实测: INDEX.md 8754 B/`42abee5f`/30 行（行尾 CRLF，实测 30 CR）· STATUS.md 56098 B/`9f1039ba`（行尾 LF，0 CR）——与 HANDOFF §二 基线逐值 MATCH，无他线并发写入。
- **订正掉的已作废事实**: 原 L23 状态段写「spi-ext-runtime.md = P4b 边界 PASS 但**运行态子面 = 未达成**……运行态闭合需 P4a 人工」，锚段写 runtime `64f332dd…`/7123B 且 `evidence/live` 只列 e1–e4。该两处已由 P7c 本线远端只读直读 + auditor VERDICT-P7bc=PASS（2026-10-08 入站）取代，锚段按本批写前实测刷新。
- **引用口径（依 NB-A 引用纪律，禁压缩表述）**:
  - **LIVE PASS（本线复现·加载面）** 的外延 = 三项远端直读——插件 jar 落盘尺寸/sha256/mtime/ctime、`META-INF/spring.factories` 注册对、`BOOT-INF/lib` 框架 SPI jar 清单（e9）。
  - 「SPI 加载事件实际发生」= **归因推断**，非直接观测；支撑 = P1 `VERIFIED_STATIC_BYTECODE`（`SPIJarLoader`/`SpringDynamicRegister`/`seeyon.spi.spi-plugins`）+ e1/e2 Nacos 配置面 LIVE + `_remote.repositories`/`.jar.sha1` 与目录 mtime/ctime 同刻痕迹；拉取动作本身未被直读。
  - **明确问题 A** 维持为事实：原料 §5「mtime=容器启动同刻」与本线实测（jar mtime 承载构件 Last-Modified、ctime 才是落盘时刻）不一致，以不一致为事实落盘，未改原料、未掩盖。
  - **明确问题 B** 维持为事实：加载链日志四串在 48h/200000 行窗口 0 命中 = 观测窗口不成立；**0 命中不得读作「test2 未加载 SPI 插件」的系统事实**。
  - **提供方调用面 = 未测试**：调用面观测设计方案已另件报主控用户待 GO，本线未动手、未采数。
  - 分级阶梯照实：**配置启用 ≠ 插件已加载 ≠ 实现被调用**；HTTP 200/空结果不算 PASS。
- **锚迁移登记（沿 §十一 R1 口径：历史时点锚一律作废，现盘为唯一基准）**: runtime `64f332dd…`/7123B、`253e98d5…`/6777B → 现锚 **`2a5861c9…`/18537B**（§15 追加后，P7c 写面，本批未改）；`evidence/live` 清单 e1–e4 → **e1–e9**（逐件 sha256 前缀与字节数取本批写前实测值，已内联 INDEX L23）；INDEX.md 本批写前基线 8754 B/`42abee5f…` → 订正后现值与本段自身 sha 因自引用不落本段，由 RESULT-P8 登记复算值（STATUS.md 追加前 56098 B/`9f1039ba…` 为 `head -c` 纯追加自证基准）。
- **职责边界**: 本段只落事实与口径订正，**不自判 G2/G3 达成、不写 COMPLETE/终态、不作路线裁断**；判级与终局判定属 main，审阅属 auditor。本批不发 REVIEW_REQUEST，RESULT 只回 main。

## 十三、SPI 线 P10 契约面 + P11 收口（implementer · 2026-10-08T06:14:07Z · 0 网络/0 SSH/0 kubectl/0 HTTP/0 探测/0 建应用/0 写观测面 · 只改 core/facts/spi/spi-ext-contract-surface.md L72 + core/facts/INDEX.md L23 + 本段尾部纯追加）
- **P10 契约面结论**（`core/facts/spi/spi-ext-contract-surface.md`，auditor `VERDICT-P10`=PASS 2026-10-08 入站）: `cip-connector-api-5.3.286.jar` 内 `com.seeyon.cip.connector.api.**.class` 扩展点全集 = **20 个接口**；分组实测 mobile 8 / midorgsync 5 / callback 2 / sso 1 / sign 1 / authentication 1 / affair 1 / db 1（求和 20）；`api.sso.SsoService` 契约 = **7 个 abstract 方法**（`getName`/`getTypeCaption`/`login`/`check`/`getPageJson`/`getSortNo`/`needUserBind`）；mobile 组继承结构 = `MobileProviderService` 为根、其余 7 个 `extends` 之（`MobileCallBackProviderService<T,Res>` 另 `extends ConnectorCallbackProviderService<T,Res>`）。判级止线 = `VERIFIED_STATIC_BYTECODE`（平台侧 jar 字节码）。
- **实现边界（含负结果）**: 两模块合计 **注册并实现 1 个（`api.sso.SsoService`）／未实现其余 19 个**。源侧三方一致: `implements` 子句仅 `SsoService` 1 命中、`spring.factories` 仅单键单值（Sso 注册）、`com.seeyon.cip.connector.api.*` import 仅 `api.sso.SsoService` 1 命中（mobile/midorgsync/callback/sign/affair/authentication/db 均 0 命中）。判级止线: 两模块内 `*.class`/`*.jar` 实测 0 ⇒ **模块字节码侧未取证 UNVERIFIED**；其他 jar 是否另含扩展点 = **未取证 UNVERIFIED**；运行态加载/调用 = **未测试**。
- **NB-1 单行订正（先于外部引用建立，0 引用迁移窗口）**: `spi-ext-contract-surface.md` L72 逐字对照 = 该行负结果计数 `18` → `19`，实改 1 字符（`8`→`9`）；事由 = 该行值与本格 §7 分区求和（20）、所引 `customer-impl-crosscheck.md` §C-1 实文（「未实现其余 19 个」）及 `api-interfaces-list.txt` 的 `com.seeyon.cip.connector.api.` 计数 20 减 `api.sso.SsoService` 1 = 19 三者算术闭合。锚迁移: `1fb4d481…`/7187B（P10 审结时点 2026-10-08T04:31Z，本批作废）→ `60a8057dde3104aa…`/7187B（同字节数替换，其余 73 行逐字未动）。
- **收口登记**: `core/facts/INDEX.md` L23 spi 行由四格追加为五格（既有四格与 LIVE 口径文字逐字保留，仅在各列末插入）；INDEX 锚 `e6107fc1…`/9705B → `2f80db4df0e4f758…`/11214B（写后实测）。
- **清点面滞后（OBS-8）**: `evidence/api-contracts/` 7 件（引用时点 2026-10-08T06:10Z 实测 `2b2f6ad8`/1581 · `0c587a27`/2275 · `9f7ea63b`/2867 · `45e20a98`/574 · `4cb508bd`/8612 · `9fd163a1`/7658 · `1d010545`/818）**不在** `evidence/hashes/evidence-inventory.sha256.txt`（`27434d48…`/6913B，2026-10-08 时点）62 条清单内 = 清点面授权滞后；旧计数「63 件/423320 B」保留为时点锚、不得回填。
- **midorgsync 6 → 5**: 本项为对 main 前批包名前缀初核的细化（初核分组求和 21 与实测总数 20 自相矛盾），以 jar 内实测 5 行为准。
- **职责边界**: 本段只落事实与口径订正，**不自判 G 项达成、不写 COMPLETE/终态、不作路线裁断**；判级与终局判定属 main，审阅属 auditor。本批不发 REVIEW_REQUEST，RESULT 只回 main。
