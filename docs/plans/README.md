# docs/plans/ 索引

> 本目录只放**计划与进度**，不放事实、契约、证据。事实进 `core/facts/`，契约进
> `docs/operation-contracts/`，证据进 `docs/audit/artifacts/`。
> 本索引的目的是让"哪份计划还有效"一眼可判 —— 计划文件本身不加改动，只在此登记状态。

## 当前有效（在推进）

| 文件 | 内容 | 状态 |
|---|---|---|
| `doc-consolidation-progress.md` | 文档整理循环的**入口卡片**（P0–P6 状态表 + 4 条待裁决 + 下一批候选） | ✅ P0–P6 全关闭；逐轮记录已迁 `docs/ledger/LOG-doc-consolidation-20261107-rounds1-15.md` |
| `seeyon-distribution-progress.md` | 能力包整理入口卡片（已完成 / 阻塞 / 下一步） | 🟡 阻塞中（无正式可安装包） |
| `microflow-100-plan.md` | 微流程 100% 可生成化方案（2026-10-16 起） | ⚪ 参考（节点事实仍有缺口，见 `doc-consolidation-progress.md` P4 B 组） |

## 历史计划（已执行或已过期，保留作记录）

| 文件 | 内容 | 时点 |
|---|---|---|
| `2026-09-03-skeleton-convergence.md` | 只读骨架收敛与下一阶段实施计划（Core/Profiles/Components/Providers/Workflows 五层） | 2026-09-03 |
| `next-phase-implementation-plan.md` | 同一主线的前一版实施方案 | 2026-09-14 |
| `platform-operation-layer-v0.1.md` | Platform Operation Layer v0.1 收口计划 | 2026-09-14 |
| `2026-09-17-microflow-readonly-milestone.md` | 微流程只读里程碑 M1（基线 HEAD `a799744`，309 passed） | 2026-09-17 |
| `hermes/plans/frontend-ui-full-extraction.md` | 设计器前端每页每位置功能全量提取计划 | 2026-10-20 |

## 关于 `hermes/plans/` 双层嵌套

`docs/plans/hermes/plans/` 是历史遗留的双层嵌套（Hermes 侧 plan 目录被整目录拷入）。
目前只有一份文件，且 `docs/REPO-LAYOUT.md:37` 把它登记为"计划文档"。
**未被任何代码读取**（已 `rg` 全仓核对）。保留原位，不做搬迁 —— 搬迁会让
`REPO-LAYOUT.md` 的登记失效，收益低于风险。
