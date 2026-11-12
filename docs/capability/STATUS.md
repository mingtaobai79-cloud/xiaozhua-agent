# STATUS｜seeyon-v2-capability-phase1 交付进度

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`。
> 完成定义：A 八件 + B 样板格全落盘 + 全量测试保持绿。
> 勾选纪律：落盘即勾，附文件与实测证据；未完成留空，不预勾。

## 时点声明（2026-11-07 复核）

**本文件是 phase1 交付时点的快照，不是当前状态。** 文中的字节数、sha256、
测试数量（`395 passed`）和目录存在性判断都属于时点记录，使用前必须重新实测。
复核发现的差异（右侧「2026-11-07 实测」列由 `tests/udc/test_capability_status_snapshot.py` 逐条重算，改文件不同步改表即红灯）：

| 项 | 本文件记载 | 2026-11-07 实测 |
|---|---|---|
| A1 ARCHITECTURE.md | 16594 B / `00391301…` | 16843 B / `d6a3dcfe…` |
| A2 MODULE-INVENTORY.md | 7717 B / `54b96e3a…` | 7702 B / `bc84310b…` |
| A3 CAPABILITY-MODEL.md | 10111 B / `f6f9b0eb…` | 10204 B / `727d2cba…` |
| A4 EVIDENCE-MODEL.md | 10083 B / `677754dd…` | 10231 B / `d6fd9298…` |
| A5 VERSION-COMPATIBILITY.md | 10189 B / `8a84d910…` | 10229 B / `4cabbdee…` |
| A6 SANDBOX-CONTRACT.md | 9806 B / `393432b8…` | 9800 B / `d7c7effa…` |
| A7 TOOL-SKILL-MODULE.md | 10501 B / `e4531ac4…` | 10462 B / `b5b8c3dc…` |
| A8 AGENT-ADAPTER.md | 11657 B / `fb996462…` | 12427 B / `3fd71fed…` |
| `adapters/`、`installer/`、`core/{role,facts,skills,tools}` | 「在盘全不存在」 | **全部存在**（`adapters/{hermes,codex,claude-code,mcp}`、`installer/`） |
| `modules/`、`sandbox/`、`core/capabilities/` | 未建 | 仍未建（与记载一致） |
| 全量测试 | `395 passed`（2026-09-28） | 已远不止此数，见 `README.md` 的 Test collection 与最新进度记录 |
| 状态码 | 全部 `[x]` | 勾选仅表示"当时已落盘"，**不代表当前可安装或已验收** |

## 交付物 A｜架构文档八件套（docs/capability/）

- [x] **A1 ARCHITECTURE.md** — 总架构图（Global/UDC 两层 + Registry + Adapter）
      落盘：`docs/capability/ARCHITECTURE.md`（16594 B，sha256 `00391301f5587fea44cbdc89b32666621a30b13877ef7fdf656d6275d49a08f0`）
      实测：registry 64 条目 = 59 基础 + 2 R18 部署 + 3 别名；deploy_plan 4 步；395 passed（9.01s）
- [x] **A2 MODULE-INVENTORY.md** — 模块清单 01–12（三列：现状证据量 / Capability 数 / 优先级）
      落盘：`docs/capability/MODULE-INVENTORY.md`（7717 B，sha256 `54b96e3a7a0ee2f23b4604cfffd12ed90063ceb8568ce2fc513af60812a76121`）
      实测：registry 仅 `udc.*` 前缀（64 裸 / 59 基础 + 2 R18 + 3 别名）；UDC=P0 样板；02–12 登记 Capability 数=0（未登记）；08–10 编号空档、11 事项管理零在盘证据
- [x] **A3 CAPABILITY-MODEL.md** — CONFIG/CODE 二分正式定义 + 声明格式 schema
      落盘：`docs/capability/CAPABILITY-MODEL.md`（10111 B，sha256 `f6f9b0eb456c0e2f84769f67f7616242fa5e3e6312511a89fbb97a4d24e0173e`）
      实测：CONFIG 真例=deploy_plan 4 步（deployment.py:115 build_deployment_plan，step op/method/path/body/verify/note 逐字段引）；schema 字段对齐 models.py UdcOperationContract 实字段；CODE 型三要素（compile_unit/test_binding/sandbox_dep）全标 UNVERIFIED（归 A6）
- [x] **A4 EVIDENCE-MODEL.md** — 四层事实体系 + registry OperationStatus 映射归并
      落盘：`docs/capability/EVIDENCE-MODEL.md`（10083 B，sha256 `677754ddc4e968f91c235add8d27c273ea64186797fe5818afffbd285aab4c53`）
      实测：OperationStatus 8 值枚举（models.py）；全 64 分布 53/9/2（UNVERIFIED 0/64）（同 A1 口径）；写门 DENIED/POLICY_DENIED 在 layer.py:22；4 步 evidence.level 逐值重跑；169/51 回读=LIVE（漂移修正 2026-10-01，见 drift-diff-f6.md）
- [x] **A5 VERSION-COMPATIBILITY.md** — Canonical 版本规范 + 差异矩阵模板
      落盘：`docs/capability/VERSION-COMPATIBILITY.md`（10189 B，sha256 `8a84d9105c4db981a2b8436eae511f7509b67ec4cae6ebe9f17cb18fcca6a0f7`，A5-FIX 后值）
      实测：Canonical=5.3.517（registry 106 处锚点 + udc jars + test2 LIVE）；差异矩阵三维（Capability×版本×证据等级），UDC 行第一列填 A1/A3/A4 已核定等级；上一版本(5.3.358 属 metadata 非 UDC)/下一版本(5.4 全库零证据)全标 UNVERIFIED；deployment.py L28-37 受控词表常量锚 5.3.517
      引用更正：HANDOFF/ROUTE 引「ROADMAP §九」不存在（ROADMAP 仅 §一~§七），已对齐真实 §一.1/§二 并回报 main
- [x] **A6 SANDBOX-CONTRACT.md** — CODE 能力执行契约（Sandbox→Compile→Test→Validate→Execute 五阶段）
      落盘：`docs/capability/SANDBOX-CONTRACT.md`（9806 B，sha256 `393432b815d822c5f5ad7d7587f6b7f5e99d7e3a9a24f7d5972d27daa50928aa`）
      实测：五阶段各给 输入/输出/通过判据/失败回流边界；绑定 A3 §2.2 三要素(compile_unit/test_binding/sandbox_dep)；
      现状=未建（modules/sandbox/、sandbox/ 在盘不存在，components/ 无 sandbox 执行体）全标 UNVERIFIED；
      替代门=test2 应用级"构建即部署"(boot-starter-sandbox UdcAppDeployService，LIVE)+写门 DENIED/POLICY_DENIED(layer.py:22)；
      test2 sandbox 事实引 docs/audit/evidence/nacos-udc.yaml（enable/domain/name-space=lowcode-test/deployEnv/imageUrlPrefix=app-sandbox:5.3.00，凭据 0 入仓）
- [x] **A7 TOOL-SKILL-MODULE.md** — Tool/Skill/Module 三者定义与映射
      落盘：`docs/capability/TOOL-SKILL-MODULE.md`（10501 B，sha256 `e4531ac421e7f3d3524e6bbc9ef8f9c5722ea4b91115a0aea802e9d542ef3f65`）
      实测：三者定义（1 契约=1 Tool 候选，registry 外=UNVERIFIED）；64 裸=59 基础+2 R18+3 别名、读 57/写 7、17 域逐条 status（map_a7.py 逐条打印）；写 7 全走写门 DENIED；Skill 首例=deploy_plan 4 步建单据实体（组合 4 Tool+回读，LIVE 实证）；A8 留接口（Tool 清单→MCP 占位，不重复定义宿主）
- [x] **A8 AGENT-ADAPTER.md** — 宿主适配规范（三层兼容模型 + v1 adapter + 三宿主暴露 + v1→v2 字段映射 + installer 目标态）
      落盘：`docs/capability/AGENT-ADAPTER.md`（11657 B，sha256 `fb996462fa2e7c21c86571d5fa44c60ac1b62a7c40d0c92f5c23026444ea814d`，补 (c) v1→v2 字段映射后值）
      实测：三层兼容模型（版本/角色包/宿主，引 ROADMAP §一.2 不自研 Loop）；v1 adapter=seeyon_host_bootstrap.py 返回 dict(L136-149)+5 宿主能力+readonly_only/credential_mode=path-ref-only；registry 3 组件(integration 3/runtime 4/udc 12)；三宿主暴露(MCP 清单/Skill 文件/角色提示词包)除 Hermes Python-native 外全标 UNVERIFIED 未建；§四 v1→v2 字段映射（可复用 8 项在盘实测 + UNVERIFIED 未建项，对齐 A7 §四 占位）；★ **2026-11-07 更正**：`adapters/`、`installer/`、`core/{role,facts,skills,tools}` 现已存在（本句原文的「在盘全不存在」已作废）；`core/capabilities/`、`modules/`、`sandbox/` 仍未建

## 交付物 B｜UDC 样板链（core/{facts,tools,skills}/udc/）

- [x] **B1 `core/facts/udc/entity/create.md`（九段式）** — UDC 样板链首件（entity.create 一格）
      落盘：`core/facts/udc/entity/create.md`（8145 B，sha256 `f5476b8b948cedfacb5440cfe646c61bdaec5e531058789ebef0cc914c8bfb08`）
      实测：九段式逐段锚在盘——Capability=udc.entity.create(CONFIG 型, agent 出 readonly plan/宿主执行写步, deployment.py step1)；
      Version=Canonical 5.3.517(A5)+Version Adapter 未建 UNVERIFIED；Input/Required=step1 声明+必填链(stereotype 出值域进 unknowns, 不臆造,
      deployment.py L143-151)；Execution=宿主调 POST /service/udc/entity + 写门 DENIED/POLICY_DENIED(layer.py:22)；
      Side Effects=物理表随 RELEASE 构建落 {app}_test2 非 udc_test2(audit §一 L18 实测 yanshouda_m5654091886000795633 + §七铁律3)；
      Known Constraints=缺 entityNature/stereotype→UDC_ENTITY_0010/BOOT_1001 + 值域活体快照非永久常量；
      Evidence=LIVE 实证 POST→BOOT_0000 YanshouDan id 7670732978062038177(OBSERVED_LIVE, audit §一 L13 逐字)；
      Verified=该步 OBSERVED_LIVE + 写门 DENIED=VERIFIED_STATIC + 未直读项(生成物落 OSS/前端随构建生成)标 UNVERIFIED(audit §六)；
      只做 entity.create 一格不扩散, 凭据 0 入仓
- [x] **B2 `core/tools/`（deploy_plan 4 步映射为 tool 声明）** — UDC 样板链第 2 件
      落盘：`core/tools/udc/` 5 件（4 tool 声明 + README 映射表）
      · entity.create.md  1948 B sha `884ae001b710bd10cfdb1ce2e54293017207263f8257459de222d4bcdf90b366`（registry VSB→STATIC）
      · entity.attribute.create.md  2113 B sha `d87febf369c077d78cf756780ef508531ce941b1a65c6f9be4d43c3fc3357fde`（registry UNKNOWN→未取证）
      · page.create.md  2786 B sha `beb12f12bf5ae1c121b912944f13d720a063466478fbe31e535e5e8e801df8ab`（**registry-gap=UNVERIFIED 不编造**；页创建契约=audit §二 OBSERVED_LIVE）
      · deploy.normal.md  2539 B sha `f57efdad0371c6d0c802e91fcb1bd9357b40c720232802e12f6adf1a986fc324`（registry OBSERVED→LIVE）
      · README.md（映射表）  2998 B sha `cfa9ece569c2dd46e91fd528da119c85386255bfa7bc026b97c46e28d15e034d`
      实测：4 步=entity.create→attribute.create→page.create→deploy.normal（deployment.py L142-178 实测 op 标签）；registry status 引 registry.py 实值（本轮 map_a7.py 逐条）；
      step3 udc.page.create 全库 grep=0 命中→registry-gap 纪律（status 填 UNVERIFIED 不编造，页创建契约引 audit §二 建页 2 命中 1871471844026226944/2146495017352265083=OBSERVED_LIVE）；
      写门 4 步全 DENIED/POLICY_DENIED（layer.py:22）；与 B1 同 step1 声明/同写门/同 audit 行号；凭据 0 入仓、不改 components/ core/ 运行代码
- [x] **B3 `core/skills/udc-entity-dev.md`** — 「在 UDC 建一个单据实体」Skill 打法（B 链 3/3 件）
      落盘：`core/skills/udc-entity-dev.md`（6936 B，sha256 `45a05379ffa7cac66a79f2363db1b651fd6cd418cad79770adfba414e91fc1f8`）
      实测：5 段串 打法 ①需求解析(deployment.py:81 infer_datatype，实测 L81 非规格误写 L197)→②deploy_plan 生成(bootstrap 5 能力，实测 seeyon_host_bootstrap.py L136-149 9 键，引 A8 §二)→③4 步执行(宿主按 steps+shared-credentials 路径引用，4 步=B2 4 tool op：entity.create→attribute.create→page.create→deploy.normal)→④回读验证(audit §一 L13-18 LIVE 行：建实体 7670732978062038177/建属性×4/建页 2 命中/物理表 yanshouda_m5654091886000795633)→⑤异常路径(BOOT_1001/UDC_ENTITY_0010/BOOT_1000[audit L35]/BOOT_3002[audit L36] 实测错路，引 B1 §7 + audit §二/§四/§七)；
      头部标『适用宿主 hermes/codex/claude-code via adapter』+『canonical=客户当前仓库(5.3.517)』；引用 B1 f5476b8b + B2 4 tool(884ae001/d87febf3/beb12f12/f57efdad) + A3 §三/A7；
      未直读项(生成物落 OSS/前端随构建生成)=UNVERIFIED 不臆造；只写打法不实现代码，components/ core/ 零改动，凭据 0 入仓
- [x] B4 宿主演示验收（Hermes 用 bootstrap+skill 完成一次"建实体"）
      落盘：`core/B4-HOST-DEMO.md`（HUMAN 总控以 Hermes 宿主身份实测，2026-09-25 15:0x+08）
      实测：Skill 4921B 五段齐 / deploy_plan 4 步 / tools 4 声明一一对齐 / facts 九段齐 / bootstrap schema 装配 OK（离线 dry，真实写链 09-24 已 LIVE 实证）
- [x] **B5 `core/facts/udc/entity/attribute-create.md`（九段式）** — 样板链第 2 格（attribute.create）
      落盘：`core/facts/udc/entity/attribute-create.md`（与 B1 同格式；只写一格不扩散，凭据 0 入仓）
      实测：契约=registry L28 VERIFIED_STATIC；LIVE=R2 §2/§3（BOOT_0000 属性 id 回读命中）+
      DESIGN-BUILD-20261009.json（保留字 UDC_ENTITY_0002/数组 BOOT_3002/DECIMAL 直过 三条 protocol_learnings 逐引）；
      写门 DENIED（layer.py:22 同 B1）；attribute-batch 端点与 update/delete 面**如实标 UNVERIFIED**（无活体回读件不承诺可用）

## 全量测试

- 时点值：`395 passed`（`.venv/Scripts/python.exe -m pytest tests -q`，2026-09-28）。
- ★ **已过时**：当前测试规模见 `README.md` 的 `Test collection`；通过数以实际运行为准，不可引用本行。

- 第二实体端到端 LIVE（09-27，live-demo2 线）：采购订单全链 PASS，样板可复制性证实（见 core/B4-HOST-DEMO.md 追加段）
