# 知识治理规范（四种资产 + 引用规则）

> 本文定义四种知识资产的职责边界和引用规则，是 ARCHITECTURE.md §4 的展开。
> 与 `KNOWLEDGE-LANDING-RULES.md`（沉淀归位 + 事实分级 + 证据可复现）互补，不重复。

## 1. 四种资产职责

| 资产 | 是什么 | 权威来源 | 反例 |
|---|---|---|---|
| **Facts** | 平台事实、接口契约、字段结构、限制 | `core/facts/<域>/` | 把"怎么搭节点"写进 facts（那是 skill 的活） |
| **Skills** | 工作步骤、操作纪律、决策规则 | `skills/`（仓库为源） | 把 61 个 facts 复制进 SKILL.md |
| **Components** | 真正执行的代码（构造器/校验器/执行器） | `components/` | 用注释替代契约文档 |
| **Evidence** | 页面/请求/响应/构建/运行记录 | `docs/audit/artifacts/` | 只写 id 不写路径和复现方法 |

判断口诀（来自 REPO-LAYOUT.md）：

```
是平台行为的事实/契约？   → core/facts/<域>/
是可执行的约束/断言？     → components/udc/<域>_constraints.py
是任务的工作流/决策规则？  → skills/<skill>/SKILL.md
是活体抓包/字节码证据？   → docs/audit/artifacts/
是可复用的工具？          → tools/core/
```

## 2. 引用规则（四层之间的边界）

1. **Skill 可以引用 Facts，不得复制大量事实内容。**
   Skill 里写「见 `core/facts/udc/microflow/node-retrieve-array.md`」，不把整篇复制进 SKILL.md。
   例外：一句话的硬约束（如「实体 name 限 21 字符」）可以简短复述 + 标注出处。

2. **Facts 必须注明证据来源和验证等级。**
   每条事实标注等级（LIVE PASS / LIVE / VERIFIED_STATIC_BYTECODE / UNVERIFIED / VACUUM）
   + 证据路径 + 复现方法 + 校验方式（R-E8 三样，见 KNOWLEDGE-LANDING-RULES §四之二）。

3. **Components 不得通过注释替代契约文档。**
   契约写 `docs/operation-contracts/udc/<域>/` 或 facts；代码注释只说明实现，不承载平台契约。

4. **Tests 必须能追溯对应 Facts 或规则。**
   每个契约测试对应一条闸门/规则/事实，`tests/test_gates_doc_contract.py` 这类测试
   就是防「代码与文档脱节」的闸门。

## 3. 四类资产成对存在（推进一个模块的完成标准）

任何域模块推进完，四类必须同时存在且互相引用：

```
实现   components/udc/<域>/<子模块>_*.py
事实   core/facts/udc/<域>/<子模块>/create.md + <子模块>-write-chain.md
契约   docs/operation-contracts/udc/<域>/<子模块>-contracts.md
skill  skills/seeyon-udc-<域>-<子模块>/SKILL.md
```

缺一类 = 模块没沉淀完。`tools/core/capability_report.py --check` 报缺口。

## 4. 渐进式知识加载（MCP 场景）

【目标】宿主 Agent 通过 MCP Resources 按需获取知识，不一次把 61 个 facts 全读进上下文：

- Facts 总索引 → 先看地图，再按主题取。
- 节点能力矩阵 / 表达式能力矩阵 → 按需取单节点。
- 业务组装 skill → 触发时才加载。

## 5. 事实与代码同步（skill 铁律负二）

技能目录（Hermes `<HERMES_HOME>\skills\`）和仓库（`<SEEYON_AGENT_ROOT>\`）是两套文件，
无自动同步。改一边必须改另一边：

| 技能里加了什么 | 仓库对应位置 |
|---|---|
| 闸门规则（G 编号） | `components/udc/microflow/gates.py` 的 `run_gates()` 函数体 |
| 闸门判据/踩坑 | `core/facts/udc/microflow/generation-gates.md` 闸门清单表 |
| 可复用脚本 | `scripts/` |
| 实测结论 | `core/facts/udc/microflow/*.md` |

目标：见 `SKILL-DISTRIBUTION.md`（仓库=源，Hermes=安装副本，同步脚本验证前不覆盖）。
