# Seeyon 能力包整理进度（入口）

> **本文件只放当前结论。** 历史追加式流水（151 行 / 71,472 B，逐字保留）已迁至
> `docs/ledger/LOG-distribution-20261020-20261107.md`。
> 文档整理循环的逐轮记录见 `docs/plans/doc-consolidation-progress.md`。

## 当前结论（2026-11-07）

### 已完成
- **分发闸门（实验性）**：`tools/core/distribution_manifest.py`——只接受显式列出的普通文件，
  拒绝目录/链接/通配/越界/`.git`/scratch/缓存；有限内容扫描 + 顶层 `LIVE_` 常量 AST 检查；
  `snapshot_sources` 返回已检字节；`build_snapshot_zip` 内存压缩 + `xb` 独占写。
- **源码修复**（均有定向测试）：
  - `components/construction/microflow.py` 保留全部 `advisory`（原只留含 `UNVERIFIED` 的）。
  - `components/udc/microflow/capability_registry.py` 证据分级
    （readback / trace / contradicted / self_report）。
  - `core/intent_actions.py` 分句 + 否定语境判定（20 例）。
  - `adapters/mcp/server.py` schema 属性名 `dataType` → `type`；非对象 JSON 帧回 `-32600` 后继续。
- **文档整理**：第 1–5 轮在本卡片记账（`core/facts/INDEX.md` 死引用 7 处 + 重复行 + 分目录计数；
  `microflow/INDEX.md` 62/README；`spi/evidence/README.md`、`capability/STATUS.md`、
  `AGENT-ADAPTER.md` 时点化；P3 七组重复文档降级；P4 34 份 `MICROFLOW-*.md` 全部归类；
  P5 分发流水迁 `docs/ledger/`）。
  **第 6 轮起转入独立循环，逐轮记录只写 `docs/plans/doc-consolidation-progress.md`。**
  ⚠ 本卡片**不复制轮次与数字** —— 第 65 轮复核时，此处原写的「第 1–5 轮」已落后 **59 轮**，
  而「下一步」原第 4 条列的两件事（P5 剩余、P6 登记）**在第 5 / 6 轮就已完成**。
  一个文件复制另一个文件的易变数字，必然过期；只留指针。

### 阻塞（BLOCKED，未验收）
- **正式可安装能力包：0 个。** 缺经审核的安全清单、完整依赖闭包、来源版本与完整性、
  宿主发现、隔离安装与调用、升级及版本冲突负例。
- `components/udc/microflow_constraints.py` 含 5 个 `LIVE_` 常量与客户标识；
  `docs/construction-rules/entity/package.json` 含 `support.applications` 客户样例；
  evidence JSON 含运行态业务数据 → 均不得进分发包。
- `distribution_install.py`：检查与 `os.rename` 间竞态、POSIX rename 可替换空目录、
  Windows 特殊名/目录别名/ZIP 资源限制未闭环。
- `source_projection.py` 不做脱敏，存在字符串拼接与动态语义风险。
- `capability_registry` 证据可追溯仍可被自报元数据欺骗
  （`{'env':'invented','date':'invented'}` 判为 `True`）。
- 能力矩阵不可原样分发：含租户生成物标识、无版本/环境声明、统计自相矛盾（22 类 vs 24 类口径）。

### 下一步（按序，**只列分发线**）
1. 矩阵与证据脱敏 + 版本绑定（先出安全清单，再谈打包）。
2. 依赖闭包收敛：`components/udc/__init__.py` eager import 绑架 23 文件。
3. 宿主发现 + 隔离安装的真实调用验证（Hermes / Codex / Claude Code 各一次）。

> ~~4. 文档整理 P5 剩余、P6 临时件登记。~~ **已完成**（P5 第 5 轮、P6 第 6/12 轮），
> 文档整理的后续一律记在 `doc-consolidation-progress.md`，不再占分发线的「下一步」。

### 待裁决
1. `skills/README.md`（Hermes 为权威副本）vs `docs/SKILL-DISTRIBUTION.md`（仓库 skills/ 为源）冲突。
2. 是否允许物理删除文件（当前策略：只合并 + superseded 指针）。
3. **客户应用 ID 明文（文件名层）**：`docs/audit/artifacts/service-flow-20261103/` 下三份 `*-biz.md`
   文件名含客户应用 ID（已入库），是否改名/脱敏。
   **实测 2026-11-07（第 65 轮）：三份仍在、文件名未变**（具体文件名**不在本文重复** ——
   抄一遍就等于把客户应用 ID 又落进一个新文件；要查直接 `ls docs/audit/artifacts/service-flow-20261103/*-biz.md`）。
   第 32 轮已补闸门用例（`test_deidentification` 现在会扫文件名），但**改名本身仍需授权**
   （改名会断掉 ledger 与 artifacts README 里的路径引用）。详见
   `docs/ledger/LOG-doc-consolidation-20261107-rounds1-15.md` 第 7 轮 BLOCKED。
