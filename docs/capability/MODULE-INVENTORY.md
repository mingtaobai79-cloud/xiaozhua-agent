# MODULE-INVENTORY｜模块清单 01–12（A2）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是其 §五"模块推进"的清单化，不新增定位/阶段）。
> 边界铁律（TASK-GOAL）：**02–12 只进本清单，不执行新审计、不展开正文**；01 UDC 为唯一 P0 样板
> （`ARCHITECTURE.md` 第四节已定）。本文件只做"现状证据量 / Capability 数 / 优先级"三列登记。
> 证据纪律：事实一律引在盘实据（`docs/audit/**`、registry 实测、`docs/operation-contracts/**`）；
> 无证据格标 **UNVERIFIED / 未审计**，不编。
> Capability 数口径沿用 `ARCHITECTURE.md` 第五节"59+2"口径纪律：registry 实位 =
> `components/platform_operations/registry.py`（`UdcOperationRegistry.default()`），
> **裸数 64 − 别名 3（udc.entity.get / udc.entity.list / udc.attribute.list）− R18 部署契约 2
> （udc.deploy.normal / udc.deploy.search_status）= 59 基础契约**；全部 64 条前缀均为 `udc.*`。

---

## 一、模块总表（ROADMAP-v2 §五 编号 01–12）

ROADMAP-v2 §五 原文编号：01 UDC（样板）｜02 BPM｜03 SPI｜04 Connector｜05 Standard Product｜
06 Runtime｜07 Integration｜…｜11 事项管理｜12 Gateway。其中 **08–10 为编号空档（"…"），
ROADMAP-v2 未给出具体名称**——本表照实登记"未枚举"，不发明模块名。

| # | 模块 | 现状证据量（在盘实据，引文件） | Capability 数（registry 口径） | 优先级 |
|---|---|---|---|---|
| 01 | UDC（样板） | **最厚**。registry 全 64 条 `udc.*`（59 基础+2 R18+3 别名）；`docs/audit/udc-*` 20 件（含 `udc-design-time-deploy-write-contracts.md` 6473 B，LIVE 实证）；`docs/operation-contracts/udc/` 10 子域（application/bi/entity/flow/menu/microflow/page/publish/resource/runtime）；`docs/audit/udc-capability-catalog.json`（schema v1）；375 测试覆盖 UDC readonly 链 | **59 基础 + 2 R18**（= 61 去别名；registry 现存唯一有契约登记的模块）。分段实测（`implementer/count_seg.py`）：entity 25 / flow 8 / application 6 / applog 6 / metadata 2 / microflow 1 / database 1 / datatype 1 / deploy 2 / entity_data 1 / page_info 2 / page_log 2 / role 1 / serial 2 / appinfo 1 | **P0**（样板，第一批跑通全链，禁止扩散——ROADMAP §五） |
| 02 | BPM | `docs/audit/modules/bpm-addsign.md`（FACT 级专项：bpm-facade-5.3.374 反编译 + 前端 chunk + i18n 枚举）；反编译产物 `docs/audit/modules/decompiled/bpm-addsign/`；`tools/scan_addsign_*.py` 扫描链在盘 | **0**（registry 无 `bpm.*` 前缀；`udc.flow.*` 8 条属 UDC 内部 flow 域契约，非 BPM 模块登记） | P1 |
| 03 | SPI | `docs/audit/modules/spi-module-profile.json`（FACT / STATIC，ch 客户仓 spi-mobile + spi-sso 两模块，`boot-starter-spi-customized`） | **0**（registry 无 `spi.*` 前缀） | P1 |
| 04 | Connector | 仅 `components/module_catalog.py` RELATIONS 声明 `customer-extension integrates-with integration`（原文注：*"requires exact adapter/call-site evidence"*，declared dependency to verify） | **0** | P2（未审计） |
| 05 | Standard Product | `docs/audit/modules/standard-product-module-profile.json`（FACT / STATIC，bpm-facade-3.12.101.jar 484 类 + sha256）；`docs/audit/modules/udc-standard-code-evidence.json`；`module_catalog.py` 标 `FACT/STATIC` | **0** | P1 |
| 06 | Runtime | `module_catalog.py` 标 `PARTIALLY_VERIFIED / LIVE_READ_ONLY`；`docs/audit/runtime/` 目录；`entity-runtime-deployment-boundary-evidence.md` 等；registry 中 microflow/metadata/application/applog/serial 等段 artifact 即 `udc-starter-runtime-5.3.517.jar`（运行态静态证据） | **0**（运行态 6 段契约已计入 01 UDC 的 59 基础，非独立 `runtime.*` 前缀） | P1 |
| 07 | Integration | `module_catalog.py` 标 `PARTIALLY_VERIFIED / SNAPSHOT_ONLY`；无独立 evidence 目录 | **0** | P2（未审计） |
| 08 | （编号空档"…"，ROADMAP-v2 未枚举） | UNVERIFIED / 未审计 | **0** | P2 |
| 09 | （编号空档"…"，ROADMAP-v2 未枚举） | UNVERIFIED / 未审计 | **0** | P2 |
| 10 | （编号空档"…"，ROADMAP-v2 未枚举） | UNVERIFIED / 未审计 | **0** | P2 |
| 11 | 事项管理 | 在盘无任何证据（`grep 事项管理/item-mgmt` 全库零命中）；ROADMAP §二 目标态 `modules/item-mgmt/` 未建 | **0** | P2（未审计） |
| 12 | Gateway | `docs/operation-contracts/gateway/` 6 件（gateway-access-evidence.md、gateway-access-v0.1.json、4 份 live-readonly json：application-get / attribute-list / entity-get / entity-list）；`docs/audit/udc-gateway-and-capability-boundary-evidence.md`；`udc-capability-catalog.json` 标 `PARTIAL_STATIC_FACT`，`route_resolution/auth/path_rewrite` 均 UNVERIFIED | **0**（registry 无 `gateway.*` 前缀） | P1 |

---

## 二、Capability 数口径说明（沿用 A1 第五节纪律）

- registry 实位：`components/platform_operations/registry.py`（`UdcOperationRegistry.default()`，本轮脚本实测）。
- 裸数 64 → 去别名 3 → 61 → 去 R18 2 → **59 基础**；写 7 / 读 57；状态分布 VERIFIED_STATIC_BYTECODE 53 /
  UNKNOWN 9 / OBSERVED 2。
- **registry 现网唯一前缀 = `udc.*`**：故 01 UDC 的 Capability 数 = 61（去别名口径），
  02–12 各模块 = 0（无契约登记，进清单等后续批次按流水线补契约，本清单不预填）。
- 02–12 的 "0" 是**登记事实**（当前未登记），不代表"无能力"——后续每个模块走
  ROADMAP §五 流水线（Module → Capability Inventory → CONFIG/CODE 分型 → 事实证据 →
  Tool Contract → Skill → Test → Sandbox 需求 → Agent Adapter 暴露）补契约，届时更新本表。

---

## 三、优先级判据（仅用于清单登记，不改 main 路线阶段）

- **P0**：01 UDC——ROADMAP-v2 §五 明令"第一批只做 UDC 样板跑通全链，不扩散"。
- **P1**：在盘已有专项审计/profile 证据、可启动流水线的模块：02 BPM、03 SPI、05 Standard Product、
  06 Runtime、12 Gateway。
- **P2**：未审计 / 证据仅为声明依赖 / 编号空档：04 Connector、07 Integration、08–10（空档）、11 事项管理。
- 判据=在盘证据量（专项审计/profile/契约目录存在性）+ 声明依赖密度（`module_catalog.py` RELATIONS）。
  **优先级≠执行顺序**：推进顺序由 main/ROUTE.md 决定，本文件不新增阶段、不发起新审计。

---

## 四、未展开项登记（边界铁律：本清单不展开正文）

| 模块 | 后续需补的证据缺口（登记，不执行） |
|---|---|
| 02 BPM | `bpm.*` 契约未登记；bpm-addsign 专项之外（监听/消息主链）待 Capability Inventory |
| 03 SPI | 客户仓 SPI 仅 ch 样例；平台侧 `spi.*` 契约未登记 |
| 04 Connector | adapter/call-site 精确证据（module_catalog RELATIONS 原文待验） |
| 07 Integration | SNAPSHOT_ONLY，需部署/配置/日志三类证据 |
| 08–10 | 模块名未枚举（ROADMAP-v2 §五 "…"） |
| 11 事项管理 | 全库零在盘证据 |
| 12 Gateway | route_resolution / auth / path_rewrite 均 UNVERIFIED（catalog 原话） |

---

## 五、与 ROADMAP-v2 / 前件的对应

- 模块编号与流水线定义：ROADMAP-v2 §五（本文件 §一 表头、§二 判据均引此节，未改）。
- registry 实位与 "59+2" 口径：`ARCHITECTURE.md` 第五节（本文件 §二 沿用，未改口径）。
- 唯一 P0 样板：`ARCHITECTURE.md` 第四节 UDC 模块层 + ROADMAP-v2 §五"第一批只做 UDC"。
- 边界：TASK-GOAL "不新开模块审计" + MAIN-CONTROL "02–12 只进 INVENTORY 清单，不执行"。
