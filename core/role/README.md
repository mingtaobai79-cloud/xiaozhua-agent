# Role 角色包索引（core/role/）

> 本包为 `core/role/` 角色定义包：把 Seeyon Agent 的角色定位、行为规范与证据纪律固化为
> 可安装角色+能力包的一部分（ROADMAP-v2 §二 目标态目录骨架 `core/role/`，
> 在盘锚点 `docs/capability/ROADMAP-v2.md` L16–L38，`core/role/` 标注"Agent 角色与行为规范（第一等公民）"）。
>
> 目标态/实现态口径：本包 4 个文件为**声明级文档（刚落盘）**；所描述的宿主暴露形态
> （MCP 传输层 / Skill 文件 / 角色提示词包 / `adapters/{hermes,codex,claude-code}/` /
> `installer/`）在盘未建，一律 **UNVERIFIED / 未实现**（口径同 `docs/capability/AGENT-ADAPTER.md` §三/§五
> L62–L68、L108–L109）。本包内容全部引在盘资产，未新造定位/阶段/验收。

## 包内 4 文件清单

| 文件 | 内容 | 主要锚点 |
|---|---|---|
| `README.md` | 本索引：Role 第一等公民定位、包内清单、目标态/实现态口径 | ROADMAP-v2 §二 |
| `ROLE-CARD.md` | 角色卡：身份定位（不自研 Agent Loop/记忆/Planner/Agent OS）、能力面、宿主关系 | ROADMAP-v2 §一.2/§二；AGENT-ADAPTER §一/§二；`seeyon_host_bootstrap.py` L25/L136–L149；`core/registry.py` |
| `BEHAVIOR.md` | 行为规范：CONFIG/CODE 二分、只读与写门纪律、意图路由/单步执行、边界不扩散 | ROADMAP-v2 §三；`seeyon_host_bootstrap.py` L144–L149；`README.md` 安全边界 |
| `EVIDENCE-DISCIPLINE.md` | 证据纪律：四层事实体系、GENERATED_HYPOTHESIS 隔离、声明≠实现、UNVERIFIED 标注 | ROADMAP-v2 §四；AGENT-ADAPTER §四 |

## Role 为第一等公民

ROADMAP-v2 §二（`docs/capability/ROADMAP-v2.md` L16–L38）目标态目录骨架中
`core/role/` 即"Agent 角色与行为规范（第一等公民）"，与 `core/{facts,skills,tools,capabilities}`
并列构成可安装角色+能力包（AGENT-ADAPTER §一 L21：可安装单元 =
**Role + Facts + Skills + Tools + Code + Sandbox**）。

## 实现态口径

- 本包 4 文档 = 声明级落盘（在盘存在即可复核）；
- 凡"未建/未实现/目标态"逐条标 UNVERIFIED 或"未实现"，不写"已实现/已落地"；
- 凭据 0 入件：本包只写凭据机制（`credential_mode="path-ref-only"` 路径引用），
  不引任何 token/密码/值（AGENT-ADAPTER §六 L122 同口径）。
