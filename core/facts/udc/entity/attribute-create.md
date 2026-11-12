# udc.entity.attribute.create｜单据实体属性创建（B1 样板链第二格）

> 基线：`docs/capability/ROADMAP-v2.md`。九段式能力事实文档，逐段锚在盘实据；
> 与 `entity/create.md`（B1）同格式同纪律。只写 `udc.entity.attribute.create` 一格；
> page/deploy 格归后续。凭据 0 入仓；只引 zzprobe 自有测试应用证据，不引客户业务明细。

---

## 1. Capability

**`udc.entity.attribute.create`** — 在已建实体下创建单个业务属性（字段）。
- **类型**：CONFIG 型（agent 出只读方案 data，宿主执行写步；A3 §三 口径）。
- **位置**：`components/platform_operations/deployment.py` `build_deployment_plan()` 的 **step2**，
  经 `seeyon_host_bootstrap.deploy_plan()` 暴露给宿主。
- **语义**：挂到指定 `entityId` 下建一条字段（name/caption/dataType），返回属性 id，
  供页面 schema 引用；平台自动补单据族系统属性列。
- **样板链位序**：`entity.create → attribute.create → page.create → deploy.normal` 第 2 步（B1 §9 收口预告的 attribute 格）。

## 2. Version

- **Canonical = 5.3.517**（A5 核定；registry artifact 锚点）。
- 差异走 Version Adapter（未建 → UNVERIFIED）；能力定义以 Canonical 为准。

## 3. Input

`deploy_plan(...)` 产出的 **step2 声明**（deployment.py step2 + R2/R6 活体实测修正）：

```
op      = udc.entity.attribute.create
method  = POST
path    = /service/udc/entity/attribute
body    = {                          # ⚠️ 单对象，非数组
    "appId":    <app_id_num>,        # 数字（_to_app_id）
    "entityId": <entity_id_num>,     # step1 返回的 data.content（数字，可负）
    "name":     <attribute_name>,    # Java 标识符；保留字被拒见 §7
    "caption":  <显示名>,
    "dataType": <值域内类型>          # 缺 → BOOT_1001
}
```

- 一条属性一次调用；多属性 = **单条循环**（数组喂本端点 → `BOOT_3002` 反序列化失败，R6 LIVE 实测）。
- registry 另登记批量契约 `udc.entity.attribute.create_batch`
  （`POST /udc/entity/attribute-batch`，`List<AttributeDto>` → `SingleResponse<Integer>`）
  ——**该端点无本仓活体回读证据，等级 UNVERIFIED（仅静态登记）**；批量需求以单条循环为主通道。

## 4. Required（必填链与值域）

| 字段 | 约束 | 缺失/越界后果 | 依据 |
|---|---|---|---|
| `appId` | 数字 | — | deployment.py step2 |
| `entityId` | 数字（step1 `data.content` 原值，可为负） | 归属错乱/拒 | R2 §2 实测（entityId=-324146415073342494 建成功） |
| `dataType` | 必填 | `BOOT_1001` | deployment.py step2 `note` |
| `name` | 合法标识符 + **非保留字** | `UDC_ENTITY_0002`（system reserved field） | R6 LIVE（`orderNo` 被拒→改 `orderCode` 过；DESIGN-BUILD-20261009.json） |
| body 形态 | 单对象 | 数组 → `BOOT_3002` | R6 LIVE（同上件 `protocol_learnings.建属性body`） |

- **dataType 值域**：从 bill 单据实体 51 属性回读统计的受控词表（`OBSERVED_LIVE`，
  deployment.py 头部注释与 `infer_datatype`）；`DECIMAL`/`DATE`/`STRING` 直接可用无需附加参数（R6 LIVE）。
  值域为活体快照非永久常量，随活体复核刷新（audit §七 铁律 2）。
- **缺省推断（不臆造）**：dataType 缺省时 `infer_datatype` 按名推断并进 `unknowns` 交宿主确认
  （deployment.py step2 前循环；A3 铁律）。

## 5. Execution

- **宿主调真实端点**：`POST {gateway_base}{prefix}/udc/entity/attribute`（service 前缀由宿主拼，铁律 040402）。
- **agent 侧不出写**：写门 `layer.py:22` → `OperationStatus.DENIED` + `ErrorKind.POLICY_DENIED`（同 B1 §5）。
- **回读验证**：`GET /service/udc/entity/attribute/select-all-by-entity-id/{entityId}`
  （deployment.py step2 `verify`；registry `all_by_entity` 静态契约同路径）。
- **前缀回退经验（宿主未发布态）**：宿主运行时服务未发布时 `/service/{appId}/udc/...` 报
  `server_404`，回退平台服务面 `/service/udc/...` 以 body.appId 定宿主——建属性与建实体同根（R2 §1/§2 LIVE）。

## 6. Side Effects

- 属性建入**设计态元数据**（publishState 随宿主实体）；物理列在 RELEASE 构建后落应用自身库
  （`{app}_test2`/`{app}_uat`，非 `udc_test2`；audit §七 铁律 3，同 B1 §6）。
- 单据族系统属性列由平台自动补（deployment.py step2 `note`；R2 §3 物理表 DDL 含全套系统列 OBSERVED_LIVE）。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| 保留字段名（如 `orderNo`） | `UDC_ENTITY_0002` 拒建 | R6 DESIGN-BUILD-20261009.json（orderNo→orderCode 实证） |
| 数组 body | `BOOT_3002` | 同上（单对象×N 循环为唯一实测通道） |
| dataType 缺失 | `BOOT_1001` | deployment.py step2 note |
| entityId 形态 | step1 `data.content` 原值直传（数字，可为负） | R2 §2/§3 |
| 批量端点未活体验证 | UNVERIFIED，不承诺可用 | registry L29 静态登记；无回读件 |
| 写门 | agent 不出写 | layer.py:22 |
| dataType 值域 | 活体快照非永久常量 | audit §七 铁律 2 |

## 8. Evidence（LIVE 实证行，非臆造）

| 行 | 事实 | 等级 |
|---|---|---|
| R2（2026-09-30，T2 复制宿主） | `POST /service/udc/entity/attribute` 单对象 → `BOOT_0000`，属性 id `-8300366849300533454`，traceId `3253881685174913212`；回读 `select-all-by-entity-id` 命中归属正确 | **OBSERVED_LIVE**（`evidence/R2-entity-create-20260930.md` §2/§3） |
| R6（2026-10-09，zzprobe 测试应用） | Dingdan 实体下 5 属性建成（含 DECIMAL/DATE）；保留字换名重试过；数组 BOOT_3002 反证在案 | **OBSERVED_LIVE**（`evidence/DESIGN-BUILD-20261009.json`） |
| 全链（2026-09-24） | 建属性 ×4 SUCCESS 属"实体→属性→页→构建"全链一环（YanshouDan 线） | OBSERVED_LIVE（`docs/audit/udc-design-time-deploy-write-contracts.md` §一，B1 §8 同源） |

## 9. Verified（逐项等级）

| 项 | 等级 | 依据 |
|---|---|---|
| 契约登记（method/path/DTO） | VERIFIED_STATIC（registry `VERIFIED_STATIC_BYTECODE`） | registry.py L28 |
| 单对象建属性 + 回读 | OBSERVED_LIVE | R2 §2/§3；R6 件 |
| 数组→BOOT_3002 / 保留字→UDC_ENTITY_0002 | OBSERVED_LIVE | R6 件 protocol_learnings |
| 写门 DENIED | VERIFIED_STATIC | layer.py:22 |
| `attribute-batch` 批量端点可用 | **UNVERIFIED**（无活体回读） | 仅 registry 静态登记 |
| update/delete 面（registry L30/L31） | **UNVERIFIED**（本格不扩，留后续格） | registry 登记未见回读件 |

> **收口**：`udc.entity.attribute.create` 九段落盘，样板链四步中第 2 格补齐；
> 未直读项（批量端点、update/delete 面）如实 UNVERIFIED 不臆造。

---

## 溯源索引

| 段 | 在盘来源 |
|---|---|
| step2 声明/note | `components/platform_operations/deployment.py`（build_deployment_plan step2） |
| 契约登记 | `components/platform_operations/registry.py` L28-29（静态登记口径 A1 §五） |
| R2 LIVE | `core/facts/udc/write-chain/evidence/R2-entity-create-20260930.md` §2/§3 |
| R6 协议学习 | `core/facts/udc/write-chain/evidence/DESIGN-BUILD-20261009.json` |
| 写门/前缀铁律 | `layer.py:22`；audit §七 铁律 040402/铁律 2/铁律 3 |
