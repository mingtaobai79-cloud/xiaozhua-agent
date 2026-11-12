# udc-entity-dev｜Skill 打法：「在 UDC 建一个单据实体」（B3）

> 样板链 B 第 3 件（`core/skills/`）——把"建一个单据实体"固化为**任务打法（Skill）**：
> 串 5 段、每段引用在盘 B1 事实格 + B2 4 tool 声明 + 八件套，不实现代码。
> 基线 `docs/capability/ROADMAP-v2.md` @ git `d76f7af`；引 ROADMAP 限 §一~§七（§七为"本文件即路线基线"结尾节，无 §八/§九）。

**适用宿主**：`hermes / codex / claude-code` via adapter（A8 三宿主目标暴露形态；本 Skill 打法对宿主解耦，
同一打法可向多宿主暴露——A7 §一"宿主不是映射终点"）。
**canonical 版本**：客户当前仓库（= 5.3.517，A5 §一 核定）；版本差异走 Version Adapter，Agent 不判分支。

**引用件（绑定，未重写）**：
- B1 事实格 = `core/facts/udc/entity/create.md`（`f5476b8b`，entity.create 九段式 LIVE 实证）
- B2 4 tool 声明 = `core/tools/udc/{entity.create,entity.attribute.create,page.create,deploy.normal}.md`
  （`884ae001 / d87febf3 / beb12f12 / f57efdad`）
- 八件套 = `docs/capability/CAPABILITY-MODEL.md`（A3 §三 CONFIG 真例 4 步）、`TOOL-SKILL-MODULE.md`（A7 Skill 定义）

**铁律**：本 Skill 只描述**打法**（怎么做这件事），不实现代码、不改 `components/`/`core/` 运行代码；
凭据 0 入仓（只描述 `shared-credentials/` 路径引用机制，不引 token/凭据值）；不展开 02–12 模块正文。

---

## 打法总览（5 段串联）

```
① 需求解析 → ② 生成 deploy_plan → ③ 宿主执行 4 步 → ④ 回读验证 → ⑤ 异常路径处置
（字段→dataType）  （bootstrap 5 能力）   （B2 4 tool）     （audit §一 LIVE）    （B1 §七 + audit §四/§七）
```

## ① 需求解析（字段 → dataType，不臆造）

- 输入=自然语言"要建一个 ×× 单据实体，含字段 A/B/C…"。
- 字段 → dataType 走 `components/platform_operations/deployment.py:81` `infer_datatype()`（**实测 L81**，
  非规格误写的 L197）：命中 `_NAME_HINT` 表（date→DATE、amount/price→DECIMAL、count/int→INTEGER、
  status→ENUM、name/no→STRING、flag/bool→BOOLEAN、text→MULTILINESTRING）；**未命中或缺省 → 进 `unknowns`
  交宿主确认，不静默臆造**（B1 §4 同纪律）。
- stereotype 固定 `bill`（在实测值域 `{archive,standard,bill,archiveTree}` 内）；出值域进 `unknowns`。

## ② deploy_plan 生成（bootstrap 5 能力，agent 只出 readonly data）

- 宿主调 `seeyon_host_bootstrap.bootstrap()` 拿能力面（**实测 9 键 dict，`seeyon_host_bootstrap.py:136-149`**；
  A8 §二 已逐键登记）：`agent / dispatch / generate / generate_from_requirement / live_probe / deploy_plan /
  allow_network / capabilities{components[], readonly_only=True, credential_mode="path-ref-only",
  deployment_plan="readonly data; host executes the write steps", schema="seeyon-host-bootstrap.v1"}`。
- 打法选 `host["deploy_plan"](application_id, entity_name, attributes, caption, stereotype="bill")` →
  返回 `seeyon-deployment-plan.v1` 方案 data（`steps[]` 4 步 + `enums` + `evidence` + `unknowns`，
  A3 §三 CONFIG 真例逐字段）；**agent 不出写，只出方案 data**。

## ③ 4 步执行（宿主按 steps + shared-credentials 调网关；= B2 4 tool 声明）

宿主拿方案 `steps[]` + `shared-credentials/` 凭据**路径引用**（`credential_mode="path-ref-only"`，值 0 入仓）
调真实网关端点，按 B2 4 tool 声明序执行（写门 `layer.py:22` 仍 DENIED/POLICY_DENIED，宿主授权执行）：

| 步 | op（B2 tool 声明） | method/path | registry status（A4 归并） |
|---|---|---|---|
| 3.1 | `udc.entity.create` | POST `/service/udc/entity` | VSB→STATIC |
| 3.2 | `udc.entity.attribute.create` | POST `/service/udc/entity/attribute` | UNKNOWN→未取证 |
| 3.3 | `udc.page.create` | POST `/service/udc/page-info/base-info/create` | **registry-gap=UNVERIFIED（不编造）**；页创建契约=audit §二 OBSERVED_LIVE |
| 3.4 | `udc.deploy.normal` | POST `/service/udc/runtime/deploy-normal`（body 包 `deployDto`） | OBSERVED→LIVE |

## ④ 回读验证（select-by-appid / 物理表 / 页面回读，引 audit §一 L13-18 LIVE 行号）

每步带 `verify` 回读断言（deployment.py step `verify` + B1 §5）：
- 3.1 后：`GET /service/udc/entity/{id}` → publishState/tableName（audit §一 L13：`POST→BOOT_0000`，
  验收单 id `7670732978062038177`，OBSERVED_LIVE）。
- 3.2 后：`GET .../attribute/select-all-by-entity-id/{entityId}`（audit §一 L14 建属性 ×4 SUCCESS）。
- 3.3 后：`GET /service/udc/page-info/select-by-appId/{appId}` 回读新页 caption+relationGroupId
  （audit §一 L15 建页 2 命中 `1871471844026226944`/`2146495017352265083`）。
- 3.4 后：RDS `udc_test2.udc_deploy_record` 最新行（`deploy_type=2` RELEASE、`state=1`）+ 应用库
  `SHOW TABLES`（物理表 `yanshouda_m5654091886000795633` 落 `znxmglpt…_test2`，非 `udc_test2`；
  audit §一 L17-18 + §七 铁律 3）。

## ⑤ 异常路径（实测错路，不臆造；引 B1 §七 + audit §四/§七）

| 症状 | 错路/原因 | 处置 |
|---|---|---|
| `dataType` 缺省/未命中 | `infer_datatype` 进 `unknowns`，不静默臆造 | 宿主确认后再建（B1 §4；deployment.py L81） |
| 缺 `entityNature`/`stereotype` | `UDC_ENTITY_0010` / `BOOT_1001` | 补齐必填（B1 §7；deployment.py step1 note） |
| 值域出界（stereotype 非 4 值） | `BOOT_1001`，值域=活体快照**非永久常量** | 校验值域，`unknowns` 交宿主（audit §四/§七 铁律 2） |
| 缺 `pageType`/`pageUrl` | `BOOT_1001 pageType/pageUrl must not be null` | 补必填（audit §二 页面创建契约） |
| 缺 `curTerminalType` | `BOOT_1000 页面终端信息为空` | 补必填（audit §二 L35） |
| `actionType` 用了 VIEW | `BOOT_3002`（VIEW 不存在；枚举 `{NORMAL,INSERT,UPDATE,DELETE}`） | 改用合法值（audit §二 L36） |
| `udc.page.create` registry 无登记 | registry-gap | 契约面 UNVERIFIED、不编造；页创建走 audit §二 LIVE 契约（B2 step3 纪律） |

---

## 未直读/UNVERIFIED 登记（不臆造，收口）
- 生成 Java 工程是否落 OSS/仓库（`schema_storage_key`/`sql_storage_key`）→ **UNVERIFIED**（audit §六）。
- 前端页面/列表是否随 RELEASE 构建生成 → **UNVERIFIED**（audit §六；页创建本身由 3.3 显式完成，
  构建"是否再送页"为未探项）。
- `udc.page.create` registry 未登记 → **UNVERIFIED/registry-gap**（B2 step3）。

> **本 Skill = 在 01 UDC 样板域把 B1（事实格）+ B2（4 tool 声明）串成"建一个单据实体"的可复现打法；
> 逐段锚在盘 LIVE/STATIC 实据 + 八件套，未直读项如实标 UNVERIFIED。** 宿主执行时由 B4（Hermes bootstrap+skill
> 演示）验收一次完整"建实体"链路。
