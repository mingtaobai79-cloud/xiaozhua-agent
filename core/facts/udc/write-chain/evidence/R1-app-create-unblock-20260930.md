# R1 unblock 环｜证据件（test2 活体 · 2026-09-30 16:30 CST）

> 性质：写路径 R1（建应用）环 **unblock 重做**（main 选 option a：供给侧给有效 hostAppName）。
> spec `main/ROUTE.md`（E7/E8 + 最小动作重发）+ main HANDOFF `r1-app-create-unblock-handoff-v1`。
> 仓库 `<SEEYON_AGENT_ROOT>`，HEAD `cf45180`。test2 镜像 5.3.496。
> **终态：BLOCKED（参数错类 · host 归属未坐实）** —— 3/3 允许 create 探测全 `status:2` 静默业务失败，
> 未建成任何应用，无 `data` id / `appGuid`。需 main 再裁（见 §5）。凭据 0 入件（§6 自检）。

## 0. 环境与时钟（实测）
| 项 | 实测值 |
|---|---|
| 网关 / 路由 appId | `{config键 gateway_base}` / `{config键 default_app_id}`（uat 码，值 0 入件；len 37/27） |
| **E7 宿主码**（main 供给） | `znxmglptcopy5791640252914287064`（config `running_profile: test2` / `k8s_namespace: lowcode-test` / `frontDomain: lowcode-test2`，L59-71；**非凭据**） |
| 探针时钟 | 2026-09-30 16:29–16:30 CST |
| 凭据 | `shared-credentials/ctp-user-login.json`（值 0 入件，sha256_16 `392fb61b…`）；本轮重新登录换会话 cookie |

## 1. 鉴权（重新登录）
- POST ctp-user 登录 → **HTTP 200 / BOOT_0000 / SUCCESS**，cookie `SY_ACCESS_TOKEN`（Set-Cookie）重新获取（len 327，值 0 入件）。
- 上轮 session 临时件已删，本轮重新生成 → 用完即删（§6）。

## 2. E8 枚举 masterEntity（只读，先做）
- GET `…/udc-runtime/serial-config/select-entity-list?appName={E7}` → **HTTP 200 / BOOT_0000 / SUCCESS**
  / traceId `3253789492108069052`（二次 `3253789492108069052`/`…9210` 同）/ **`content` 命中 18 个实体 fullName**。
- 取用：`com.seeyon.9000000000000000001.domain.entity.Tbfysq1`（作 `masterEntity`）。
- **关键负证据（跨应用命名空间）**：这 18 个实体 fullName 全部挂在 **uat 应用的包命名空间**
  `com.seeyon.9000000000000000001.domain.entity.*`（`default_app_id` = uat 码），**而非 E7 的
  `znxmglptcopy…`（test2）命名空间**。说明：serial-config 端点经 `default_app_id`（uat）网关路由时，
  即便 `appName={E7}`，返回的仍是 uat 侧实体族 → **`appName` 过滤未切到 test2 宿主**（或 test2 宿主无自有 custom 实体）。
  → 直接后果：喂给 create 的 `masterEntity` 是 uat 命名空间实体，与 test2 `hostAppName`=E7 跨应用 → 强候选 status:2 根因。

## 3. create 探测（unblock 允许 ≤3 次，**已用满 3/3**，均未 BOOT_0000）
端点 POST `…/udc-runtime/custom-app/create`（走 `{default_app_id}` 路由，body `hostAppName`=E7）。

| # | body 关键键 | HTTP | envelope | traceId | 结果 |
|---|---|---|---|---|---|
| create-1 | `caption=zzprobe20260930H2` + `hostAppName=E7` + `masterEntity=<uat 命名空间实体>` | 200 | `status:2` / code=null | `3253789499322271932` | 静默业务失败 |
| create-2 | `caption=…H2` + `hostAppName=default_app_id` + `masterEntity`（回退） | 200 | `status:2` / code=null | `3253789511989070012` | 静默业务失败 |
| create-3 | `caption=…H2` + `hostAppName=E7`（**单独，不带 masterEntity**，ROUTE E8 最小成功体） | 200 | `status:2` / code=null | `3253790538922461372` | 静默业务失败 |

- **判定**：3/3 全 `status:2`（非 4xx 参数错、非 BOOT_1001 校验错、非 401）→ **host 归属未坐实**。
  即使最小体（E7 码 + 无 masterEntity）也 status:2 → **status:2 根因不是 masterEntity 命名空间污染本身**，
  而是 `hostAppName`=E7 经 uat `default_app_id` 网关路由时**宿主应用绑定未解析**（test2 宿主未在该路由下可见）。

## 4. 回读同一目标（负证据）
- 3 次 create 均无 `data` id → **无有效回读目标**。
- search-no-page 按 `caption=zzprobe20260930H2` → **0 条**；application.get 无 id 可查（未发，避免无效 404）。
- **create 未成功 ⇒ 回读无从命中；不冒充 PASS。**

## 5. 失败三类归因 + unblock 建议（交 main）
| 类 | 命中 | 证据 |
|---|---|---|
| 参数错（host 归属未坐实） | **是（主因）** | 3/3 status:2 静默；E7 宿主在 uat 路由下未解析 |
| 权限不足 | 否 | 全程 200（cookie 有效），无 401/403 |
| 接口不存在 | 否 | create / serial-config 端点均 200（可解析 envelope，非 404） |

**根因假设（需 main 裁定，供下一 HANDOFF）**：create 网关前缀用了 `default_app_id`（**uat 码**），
而 `hostAppName`=E7（**test2 码**）→ 网关把 create 路由到 uat 宿主，uat 宿主绑不到 test2 host app → status:2。
要坐实 test2 host，**create 的网关路由前缀应走 test2 宿主码（E7）而非 uat `default_app_id`**；
或确认 test2 宿主下可用的实体/宿主绑定（serial-config 在 E7 路由下复查 `appName` 过滤是否切到 test2）。

## 6. 脱敏自检（凭据 0 入件）
- 本轮 login 响应若含 token 值已自动替换为 `<REDACTED_CREDENTIAL>`（`_r1_unblock.py` 内做）；
  含 cookie 值的 session 临时件用完即删（§6 复核 0 命中）。
- 原始 REQ/RESP 逐字在 `evidence/R1-app-create-unblock-*.jsonl`（含 3 次 create + 2 次 enum + login，全带 traceId）。

## 7. 交付绑定锚（实测）
| 项 | 值 |
|---|---|
| HEAD | `cf45180` |
| unblock 证据 jsonl | `R1-app-create-unblock-{162903,162915,162926,163028}.jsonl` |
| 本证据件 | `evidence/R1-app-create-unblock-20260930.md` |
| 九段式 R1 段 | `write-chain.md`（本轮更新为 unblock 态） |
| STATUS 追加 | §八.5（unblock 段） |
| create 成功数 | **0**（3/3 探测均 status:2）；**deleteByIds 清单：无（未建成）** |
