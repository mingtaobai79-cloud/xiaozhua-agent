# 2小爪 Agent Platform — 总路线收口（v2 架构定稿）

> 2026-09-25 operator-a裁示。本文件取代此前所有"继续单类审计/继续舰队推进"的路线描述。
> 核心原则（一句话）：**不造新的 Agent，而是把 2小爪 现有能力、代码、事实、运行环境和
> 版本差异固化成 Agent 可调用、可验证、可兼容的 Capability——再以"可安装的 Agent 角色与
> 能力包"形态嵌入 Hermes / Codex / Claude Code 等已有宿主。**

## 一、定位（两级兼容模型）

1. **2小爪 版本兼容**（对内）：客户当前仓库版本为 Canonical，能力定义稳定，
   差异走 Version Adapter（adapter-5.3 / adapter-5.4 / ...），Agent 不自行判断版本分支。
2. **Agent Host 兼容**（对外）：2小爪 Agent = 可安装的 **Agent 角色 + 能力包**
   （Role / Facts / Skills / Tools / Code / Sandbox），经 Adapter 进入不同宿主。
   不自研 Agent Loop / 记忆 / Planner / Agent OS。

## 二、目录骨架（目标态）

```
seeyon-agent/
├── core/
│   ├── role/            # Agent 角色与行为规范（第一等公民）
│   ├── facts/           # 事实文档（按模块分域，四层证据体系）
│   ├── skills/          # Skill（一类任务怎么做，可组合多 Tool）
│   ├── tools/           # Tool（单动作执行）
│   └── capabilities/    # Capability 契约（CONFIG 型声明 + CODE 型入口）
├── modules/
│   ├── udc/             # 第一套完整样板（Entity/Page/MicroFlow/Metadata）
│   ├── gateway/
│   ├── sandbox/
│   ├── item-mgmt/       # 事项管理
│   └── ...              # Module Inventory 驱动，不发现式蔓延
├── adapters/
│   ├── hermes/
│   ├── codex/
│   └── claude-code/
├── installer/
└── sandbox/             # Global 级（Runtime/Sandbox/Evidence/Version/Registry/Adapter）
```

## 三、能力模型（CONFIG / CODE 二分）

- **CONFIG 能力**：Agent 产结构化声明（`{"capability":"udc.entity.create","input":{...}}`），
  平台执行。例：建实体/建字段/建页面/配权限/配路由/配菜单。
- **CODE 能力**：配置表达不了的（复杂规则/校验/转换/三方调用），必须走
  **Sandbox → Compile → Test → Validate → Execute**，禁止 Agent 直出 Java 直跑。

## 四、四层事实体系（防 Agent 胡编的机制核心）

```
STATIC（源码/javap）→ VERIFIED（测试/调用）→ LIVE（真实环境）→ GENERATED（仅假设）
```
GENERATED_HYPOTHESIS 永不进入 VERIFIED_RULE。现有 registry 的
VERIFIED_STATIC_BYTECODE / OBSERVED / UNVERIFIED 体系直接归并。

## 五、模块推进（Module Inventory 驱动）

01 UDC（样板）｜02 BPM｜03 SPI｜04 Connector｜05 Standard Product｜06 Runtime｜
07 Integration｜…｜11 事项管理｜12 Gateway。
每模块统一流水线：Module → Capability Inventory → CONFIG/CODE 分型 → 事实证据 →
Tool Contract → Skill → Test → Sandbox 需求 → Agent Adapter 暴露。
**第一批只做 UDC 样板跑通全链，不扩散。**

## 六、三 Agent 生产线的新职责

不再"发现一个类研究一个类"，而是**给 2小爪 Agent 补充能力资产**：
每个审计回合的产出=Capability Contract + Fact 文档 + Test + 证据等级。
（生产线机制保留：main 路由 / implementer 执行 / auditor 验证。）

## 七、本文件即路线基线。后续 ARCHITECTURE/MODULE-INVENTORY/CAPABILITY-MODEL/
EVIDENCE-MODEL/VERSION-COMPATIBILITY/SANDBOX-CONTRACT/TOOL-SKILL-MODULE/AGENT-ADAPTER
八份文档按此展开。
