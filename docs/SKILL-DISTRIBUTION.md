# Skill 分发与三套目录关系

> 解决「三套 Skill 目录无同步机制」的问题。本文记录审计结果 + 目标关系 + 同步设计。
> 【现状】= 已确认 /【目标】= 规划未落地。

## 0. 裁决（2026-11-07）：两套规则其实是两种关系，不是矛盾

`skills/README.md` 说"权威副本在 Hermes、仓库只是选择性镜像"，本文 §3 说"仓库 skills/ = 源"。
**两者都对，作用面不同**——冲突在措辞，不在事实：

| 目录族 | 权威方向 | 理由 |
|---|---|---|
| `skills/01-platform` · `02-udc` · `03-v8-extension` · `04-integration` · `06-delivery` · `07-office-collaboration` | **Hermes → 仓库（镜像）** | 这些是操作手册，本来就该写真实环境（域名/组织/工号/凭据路径）。Hermes 侧是唯一持续维护处，仓库侧是脱敏后的快照 |
| `skills/05-agent` · 顶层 `seeyon-agent` · `sdd-protocol` · `udc-trace-to-api` | **仓库 → Hermes（源）** | 这些是仓库自身的规矩与方法论，与具体客户环境无关，Hermes 是消费方 |

2026-11-07 实测（`tools/core/_meta/sync_skills_from_hermes.py --check` 与逐字节比对）：
仓库 35 个 `SKILL.md`，**同 4 / 更 23 / Hermes 缺 8**；23 个差异里 **16 个是
"仓库行被 Hermes 覆盖率 ≥0.98"**，即仓库侧是旧子集、只是没跟上（不是各有独有内容）。
所以「仓库是镜像」这个方向判断在数据上成立。

**未决**：文档目录族（先归 Hermes 还是先归仓库）仍需用户定；本文 §3 的"仓库=源"
只对 `05-agent` 与顶层那 4 个成立。§3–§5 保留为**目标态**，不是现状。

## 1. 三套目录定位

| 目录 | 定位 | 是否版本化 |
|---|---|---|
| `<HERMES_HOME>\skills\` | ★ 运行时加载的 skill（系统提示从这里读） | 否 |
| `<SEEYON_AGENT_ROOT>\skills\` | 仓库内的 skill 源 | 是（git） |
| `<SEEYON_AGENT_ROOT>\core\facts\` | 权威平台事实（不是 skill） | 是（git） |

## 2. 现状审计（2026-11-05）

### 2.1 分类前缀不一致

- Hermes：`seeyon/01-platform/`、`seeyon/02-udc/`、`seeyon/03-v8-extension/` ...
- 仓库：`skills/01-platform/`、`skills/02-udc/`、`skills/03-v8-extension/` ...

仓库少了 `seeyon/` 前缀，且 Hermes 顶层还有散落 `seeyon-udc-custom-extension-engine`。

### 2.2 核心 skill 单边（关键缺口）

| skill | Hermes | 仓库 |
|---|---|---|
| `seeyon-udc-microflow-generation`（★ 核心，微流程生成） | ✅ `skills/udc/`（**兄弟目录**，不在 `skills/seeyon/` 下） | ❌ 无 |
| `seeyon-udc-business-flow-assembly`（业务组装） | ✅ `skills/udc/`（同上，兄弟目录） | ✅ `skills/02-udc/`（已入库，PII 通过） |

更新（2026-11-07）：两条都已变化——
- 业务组装 Skill **已入库**（`skills/02-udc/seeyon-udc-business-flow-assembly/`，22647 B），
  不再是"未跟踪"；但其 `business_readiness_audit` 仍绑定 `scratch/pmp_schemas.json`，
  分发前需替换该依赖（已记录在分发 BLOCKED 清单）。
- 核心微流程生成 Skill 仍在 Hermes `skills/udc/` 下、仓库侧无副本，源资产与依赖闭包未解决。

### 2.3 重复副本

- `seeyon-udc-module-landing`：仓库顶层 `skills/seeyon-udc-module-landing/` 和 `skills/02-udc/seeyon-udc-module-landing/` 各一份，**逐字节相同**（13204 B，`cmp` 通过）。
  两份都在盘、都无测试断言；顶层那份被 `docs/KNOWLEDGE-LANDING-RULES.md` 与本文引用，
  `02-udc/` 那份被 `skills/README.md` 登记为"被测试断言"——但实测该断言在 `tests/udc/` 下并不存在。
  **未合并、未删除**：合并需先确认引用方向（列入待裁决）。
- `seeyon-udc-setting`：Hermes `seeyon/02-udc/` 有，仓库 `skills/02-udc/` 无、但顶层 `skills/seeyon-udc-setting/` 有（44461 B）。
  被 `tests/udc/test_setting_custom_object_asset_layout.py` 与 `test_setting_enum_asset_layout.py` 按路径断言，
  以及 `core/facts/udc/setting/custom-object/create.md`。**位置锁定，不得移动**。

### 2.4 散落未分类（仓库）

`seeyon-agent`、`sdd-protocol`、`udc-trace-to-api`、`seeyon-udc-application-app-inner`、
`seeyon-udc-microflow-node`、`seeyon-udc-module-landing`、`seeyon-udc-setting` 共 7 个在顶层。
**不迁移**——每个都有引用方（下表），迁移等于改一圈测试与文档：

| 顶层 skill | 引用方 |
|---|---|
| `seeyon-agent` | `adapters/hermes/ADAPTER.md`、`installer/INSTALL-MANIFEST.md`、`docs/HOST-INTEGRATION.md`、`skills/05-agent/seeyon-agent-fact-protocol/SKILL.md` |
| `seeyon-udc-application-app-inner` | `tests/udc/test_application_app_inner_asset_layout.py`、`core/facts/udc/application/app-inner/create.md` |
| `seeyon-udc-microflow-node` | `docs/ledger/LOG-distribution-*.md`（仅流水提及） |
| `seeyon-udc-module-landing` | `docs/KNOWLEDGE-LANDING-RULES.md`、本文 |
| `seeyon-udc-setting` | 两个 `test_setting_*_asset_layout.py`、`core/facts/udc/setting/custom-object/create.md` |
| `sdd-protocol` / `udc-trace-to-api` | 仓库内零正文引用；但两者 Hermes 侧都有同名副本（`udc-trace-to-api` 差异 14102 vs 48466） |

## 3. 目标关系

【目标，仅对 `05-agent` 与顶层 4 个成立】三层职责 + 单向同步：

```
仓库 skills/  = 源（版本化、可发布、可 review）
     │  同步脚本（install）
     ▼
Hermes skills/ = 安装运行副本（宿主加载）
     │  引用（不复制内容）
     ▼
core/facts/   = 权威事实（skill 通过相对路径引用，不复制大量事实）
```

原则（用户定）：
1. Skill 只描述工作流和决策规则，**不复制大量 Facts**。
2. Skill 通过相对引用加载所需 Facts。
3. 每个 skill 写清适用/不适用场景，渐进式加载，不一次塞满上下文。

## 4. 同步脚本设计

【目标】`installer/` 提供同步，**验证前不覆盖 Hermes 运行中的 skill**：

```
seeyon skill sync          # 仓库 skills/ → Hermes skills/（diff 后逐个确认）
seeyon skill install <名>  # 安装单个
seeyon skill diff          # 列出仓库 vs Hermes 差异
```

同步规则：
- 只增不覆盖（Hermes 有而仓库无的，先反向拉回仓库，再决定）。
- 同名内容不同 → 报告差异，人工裁决，不自动覆盖。
- 凭据/cookie 永不进 skill。

## 5. 本轮不做

【未实现】暂不执行物理同步，只记录关系 + 审计结果。等同步脚本验证后再动。
当前 Hermes 运行中的 skill（含核心 `seeyon-udc-microflow-generation`）**保持原样不动**。
