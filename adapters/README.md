# adapters/｜v1 五能力按宿主暴露

> **定位**：把 v1 `bootstrap()` 的 **5 个能力**按四个宿主分别声明/实装，
> 供 `installer/` 物化为可安装单元。上层说明见 `docs/capability/AGENT-ADAPTER.md`（A8 交付物）。
>
> **全部是声明级文档 + 一个传输层实装**，不是四套独立实现。
> 凭据 0 入件：只写路径引用 / 环境变量机制，不引任何 token、密码、值。
> 未建/未实现/目标态项在各自文件里逐条标 **UNVERIFIED / 未实现**。

---

## 一、结构：三份 MANIFEST 不是重复

```
adapters/
├── hermes/       ADAPTER.md + Hermes-SKILL.md + MCP-TOOL-MANIFEST.md
├── codex/        AGENTS.template.md + MCP-TOOL-MANIFEST.md
├── claude-code/  CLAUDE.template.md + MCP-TOOL-MANIFEST.md
└── mcp/          DESIGN.md + STATUS.md + server.py   ← 唯一的传输层实装
```

**`MCP-TOOL-MANIFEST.md` 出现三次，但它们不是同一份文件的副本。**
三份都是「把 v1 `bootstrap()` 的 5 能力映射成 MCP tool 声明」，
**但每个宿主暴露的形态不同**（Hermes = MCP + Skill 文件；Codex = AGENTS 指令文件；
Claude Code = CLAUDE 指令文件），实现态标注也各不相同。

三份都引用同一个传输层 `mcp/server.py` —— **共享的是 server，不是清单**。

> ⚠ **不要把这三份合并成一份**。合并会丢掉「每个宿主自己那一层还没实现」的信息，
> 而那正是分发前必须逐宿主确认的东西（见 `docs/SKILL-DISTRIBUTION.md` 的 BLOCKED 项）。

---

## 二、9 份文档（本表不含本 README）

| 宿主 | 文件 | 字节 | 行 | 阶段 | 一句话 |
|---|---|---:|---:|---|---|
| hermes | `ADAPTER.md` | 6,199 | 82 | S2 · H-2 | 宿主注册件说明：A8 三层模型里的位置、暴露形态 |
| hermes | `Hermes-SKILL.md` | 5,967 | 82 | S2 · H-2 | Skill 文件 v2.0.0（frontmatter 形态），v1 基线只读引用 |
| hermes | `MCP-TOOL-MANIFEST.md` | 9,832 | 103 | S2 · H-2 | Hermes 侧 MCP tool 声明 + 逐层实现态 |
| codex | `AGENTS.template.md` | 6,968 | 89 | S3 · H-3 | AGENTS 指令文件模板（**STAGED**，待放行 `AGENTS.md` 写保护） |
| codex | `MCP-TOOL-MANIFEST.md` | 11,087 | 117 | S3 · H-3 | Codex 侧 MCP tool 声明（5 能力 + CLI op 面） |
| claude-code | `CLAUDE.template.md` | 9,070 | 103 | S4 · H-5 | CLAUDE 指令文件模板（规范名 `CLAUDE.md` 被写保护，故以 `.template` 落地） |
| claude-code | `MCP-TOOL-MANIFEST.md` | 11,335 | 121 | S4 · H-5 | Claude Code 侧 MCP tool 声明 |
| mcp | `DESIGN.md` | 13,452 | 182 | S1 | 传输层设计件：五能力 MCP 工具怎么建（**不写 server.py**） |
| mcp | `STATUS.md` | 3,179 | 37 | S2 | 传输层实装收口记录（2026-09-28 时点，数字用前重跑） |

**合计 9 份 / 87,054 B / 1,072 行。**

传输层实装：`mcp/server.py`（12,875 B）+ `tests/test_mcp_server.py`（**20 用例**）。
`STATUS.md` 里写「19 passed」是 2026-09-28 的时点值，当前 20。

---

## 三、本目录不设子目录 README

`hermes/`(3) `codex/`(2) `claude-code/`(2) `mcp/`(2) 都没有自己的 README。

理由同 `core/facts/udc/README.md` §六对 `page/` `serial/` 的处置：
**份数少、主题同构，一张顶层表就能覆盖导航**。哪个宿主真开始被反复查，再给它单独入口。

---

## 四、找东西

| 想干什么 | 看哪里 |
|---|---|
| 某个宿主怎么注册、暴露什么 | `<host>/` 下对应文件；A8 三层模型见 `docs/capability/AGENT-ADAPTER.md` |
| MCP tool 有哪些、各自实现到哪一步 | 该宿主的 `MCP-TOOL-MANIFEST.md` §3（逐层实现态） |
| 传输层怎么起、测什么 | `mcp/DESIGN.md` + `mcp/STATUS.md` + `mcp/server.py` + `tests/test_mcp_server.py` |
| 为什么还不能分发 | `docs/SKILL-DISTRIBUTION.md`（BLOCKED 清单） |
