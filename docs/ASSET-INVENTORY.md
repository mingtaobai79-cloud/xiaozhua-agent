# 资产清单（_attic_pending 分类）

> 先分类标记，不物理删除。本文解决 `_attic_pending/` 50+ 目录「正式业务 / 探针 / 过时副本」混堆的问题。
> 分类只作标记，迁移/归档需用户确认 + 独立 git 提交。

## 分类标准

| 类 | 定义 | 处置 |
|---|---|---|
| A 正式业务案例 | 承载真实业务、可回归验收 | **保留**（RMA/制造业/采购） |
| B 可复现验收案例 | 验证节点/形态的完整闭环（含构建+运行+断言） | 保留，作回归语料 |
| C 一次性探针 | 单次取证/调试脚本，无复用价值 | 归档，不维护 |
| D 原始证据 | 抓包/反编译/DB 快照 | 保留（证据只增不删） |
| E 过时副本 | 已被替代的镜像/旧版本 | 标「待归档」，确认后清理 |

## 清单

### A 正式业务案例（保留为回归资产）

| 目录 | 内容 | 状态 |
|---|---|---|
| `biz/rma/` | 售后退换货闭环（16 实体 + 6 流程 + 2 模拟服务 + 事件） | RELEASE + BUILD SUCCESS |
| `biz/mfg/` | 制造订单履约（26 实体 + 8 流程 + 2 事件 + 4 模拟服务） | RELEASE + BUILD SUCCESS（14 断言待跑） |
| `biz/procurement/` | 采购业务（建实体 + MF 验证） | 已沉淀 |

### B 可复现验收案例（回归语料）

| 目录 | 验证内容 |
|---|---|
| `batch-verify/` | 批量节点验证（conv/map 等） |
| `p6groupbysum/` | GROUP_AND_SUM 双键分组 |
| `p6pagination/` | RETRIEVE_ARRAY 分页 |
| `p7e2e/` | 端到端业务闭环 |
| `verification-flow-schemas/` | 验证流程 schema |

### C 一次性探针（归档，不维护）

| 目录/文件 | 说明 |
|---|---|
| `p2-expression-probes/` `p3-logic-graph-probes/` | 表达式/逻辑图探针 |
| `p5-*/`（batch-node/break-event/change-list/dataflow/probes/r1/retrieve-array/runtime/sub-microflow/stable-node-ids/write-node） | P5 各节点验证探针 |
| `p6-closed-loop/` `p6-data-mapping/` `p6-map-verify/` `p6-svc-event/` | P6 验证探针 |
| `convert-data-probes/` `cv-forms-probes/` | 转换/表单探针 |
| `scratch-pii-20261102/` `scratch-pii-probes/` | PII 脱敏探针 |
| `one-off/` | 一次性脚本 |
| `legacy-audit/` | 遗留审计 |
| 散落 `_*.py` `_*.json`（`_p6_*` `_p7_*` `_ui_*` `_expr_sweep*` `_probe_*` 等） | 一次性探针脚本 |

### D 原始证据（保留）

`legacy-audit/`（如含抓包/反编译）→ 归档到 `docs/audit/artifacts/`，不删。

### E 过时副本（待归档，确认后清理）

| 目录 | 说明 |
|---|---|
| `mirrored-skills/` | 镜像 skill（seeyon-udc-entity-domain-dup） |
| `mirrored-skills-20261022/` | 2026-10-22 镜像 |
| `stale-skill-copies/` | 过时 skill 副本（sdd-protocol-old 等） |
| `superseded-artifacts/` | 被替代的 JSON 产物（mf_all.json、r33_* 等） |

## 结论

- **A 类（biz/mfg、biz/rma、biz/procurement）是正式业务资产，不能当临时文件清掉。** 尤其制造业，
  14 项断言补完前，`biz/mfg/` 的脚本 + entities.json 是唯一可复现的资产。
- **E 类（4 个过时副本）** 是唯一可以安全清理的，但需用户确认 + git 提交后删，不 reset/clean。
- **C 类探针** 归档到 `_attic_pending/` 子目录或 `tools/one-off/`，不删除（取证方法参考）。
- 本轮**只做标记，不物理移动/删除**任何文件。
