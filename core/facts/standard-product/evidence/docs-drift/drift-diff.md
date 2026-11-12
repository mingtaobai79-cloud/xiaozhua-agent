# drift-diff｜docs/capability registry 状态分布时点漂移修正（P6 / HANDOFF-6）

> 线：`session-20260929-184027-7f85bd1f`（standard-product 事实格线，纯静态）
> 边界：`main/ROUTE.md` §7.2（授权② docs/capability 漂移修正）——先出 diff、后改、只改漂移行。
> 生成时钟：2026-10-01。落盘人：implementer。本步零 HTTP、零活体、凭据 0 入件。

## 0. 口径源（唯一，main 派发前实测锁定）

- 分布口径源件：`core/facts/standard-product/evidence/reconciliation/count_registry_contracts.out.json`
  - sha256 = `3a07224c06d1e52b5338c3ca89aa91294536e36d2b8c8665822ae644848f9d72`
  - `status_census` = `{"VERIFIED_STATIC_BYTECODE": 53, "OBSERVED": 2, "UNKNOWN": 9}`（合计 64，**无 UNVERIFIED 键 = 0/64**）
- 计数脚本：`core/facts/standard-product/evidence/reconciliation/count_registry_contracts.py`
  - sha256 = `611e73990acc0b660526e85a7ad8ace650ab09391b093e47995a9bc5b22e9ab0`
- **禁止混淆项**：同一 out.json 的 `evidence_level_census = {"VERIFIED_STATIC_BYTECODE": 62, "OBSERVED_LIVE": 2}` 是**另一维度**（契约 `evidence_level` 轴），**不得**用于修本四处 `status_census` 漂移行。

### 0.1 两条 OBSERVED 契约逐条点名（实测 registry.py 在盘）

| op_id | 源码位置 | OperationStatus | write | 根因 |
|---|---|---|---|---|
| `udc.deploy.normal` | `registry.py:125` | OBSERVED | **True** | R18 部署契约升 OBSERVED |
| `udc.deploy.search_status` | `registry.py:128` | OBSERVED | **False** | 部署历史真面 `appVersion/{appGuid}` 升级 OBSERVED |

- 根因提交（`git log`）= `210aa72`「facts(deploy): 部署历史真面 appVersion/{appGuid} 升级 OBSERVED + Redis 布局 + 配额契约 (09-28 LIVE)」。
- 因此 `status_census.OBSERVED` 由旧上游文档记的 1 条（仅 deploy.normal）实为 2 条；`OperationStatus.UNVERIFIED` 契约承载 = 0/64（`:126` 的 `evidence_level="UNVERIFIED"` 为 dead 变量、`:128` 实引 `:127` deploy_hist_evidence）。

---

## 1. S1｜`docs/capability/ARCHITECTURE.md:138`

- 旧（逐字）：
  `| 证据等级分布 | VERIFIED_STATIC_BYTECODE **53** / UNKNOWN **9** / OBSERVED **1** / UNVERIFIED **1** | 与 A4 四层体系归并 |`
- 新（逐字）：
  `| 证据等级分布 | VERIFIED_STATIC_BYTECODE **53** / UNKNOWN **9** / OBSERVED **2** | 与 A4 四层体系归并 |`
- 依据：`status_census` = 53/9/2、UNVERIFIED 0（删 UNVERIFIED 项）。

## 2. S2｜`docs/capability/MODULE-INVENTORY.md:41-42`（串跨 41→42，行尾折行）

- 旧（逐字，41 行末 + 42 行）：
  ```
  - 裸数 64 → 去别名 3 → 61 → 去 R18 2 → **59 基础**；写 7 / 读 57；状态分布 VERIFIED_STATIC_BYTECODE 53 /
    UNKNOWN 9 / OBSERVED 1 / UNVERIFIED 1。
  ```
- 新（仅折行段末串变更，其余逐字保留）：
  ```
  - 裸数 64 → 去别名 3 → 61 → 去 R18 2 → **59 基础**；写 7 / 读 57；状态分布 VERIFIED_STATIC_BYTECODE 53 /
    UNKNOWN 9 / OBSERVED 2。
  ```
- 依据：同 `status_census`（53/9/2、UNVERIFIED 0）。

## 3. S3｜`docs/capability/EVIDENCE-MODEL.md:32-33`（串跨 32→33）

- 旧（逐字）：
  ```
  其中**契约登记态**（registry 实值，全 64 条分布：`VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 /
  OBSERVED 1 / UNVERIFIED 1`，口径同 A1 第五节）与**执行期态**（layer 运行返回）分两类归并。
  ```
- 新（仅分布串变更，其余逐字保留）：
  ```
  其中**契约登记态**（registry 实值，全 64 条分布：`VERIFIED_STATIC_BYTECODE 53 / UNKNOWN 9 /
  OBSERVED 2`，口径同 A1 第五节）与**执行期态**（layer 运行返回）分两类归并。
  ```
- 依据：同 `status_census`（53/9/2、UNVERIFIED 0）。

## 4. S4｜`docs/capability/EVIDENCE-MODEL.md:40`（OBSERVED 归并行 · 相关假陈述）

- 旧（逐字）：
  `| `OBSERVED` | **LIVE** | 活体回读实证；全 64 条中仅 `udc.deploy.normal`（write=True，R18）为 OBSERVED，证据=test2 活体 `udc_deploy_record` 行 |`
- 新（改为两条均 OBSERVED，证据句保留原样）：
  `| `OBSERVED` | **LIVE** | 活体回读实证；全 64 条中 `udc.deploy.normal`（write=True）与 `udc.deploy.search_status`（write=False）为 OBSERVED，证据=test2 活体 `udc_deploy_record` 行 |`
- 依据：`registry.py:125`/`:128` 两条均 `OperationStatus.OBSERVED`（根因提交 `210aa72`）；旧句「仅 … 为 OBSERVED」漏计 `udc.deploy.search_status`。

---

## 5. 范围自证（勿扩范围）

- 本 P6 仅动上述 **S1~S4 四处漂移行**；同文件其它行、`docs/audit/**`、兄弟线件、6 件冻结锚（contracts `4cd71033…` / manifest `d7643f75…` / file-hashes `0cfb5119…` / reconciliation `c29962df…` / out.json `3a07224c…` / count.py `611e7399…`）一律**未改**。
- 非阻断观察（登记不改，交 main/auditor 裁定）：S4 相邻的 `EVIDENCE-MODEL.md:41`（`UNVERIFIED` 归并行）仍以 `udc.deploy.search_status` 为例描述其为「完整路由 UNVERIFIED」。§7.2 漂移站点清单未列入该行、且明令「改动仅限 S1~S4 四处」，故本步**未触碰**；如实登记此行与 S4 现文存在口径张力，留 main 决定是否纳入后续修正。
