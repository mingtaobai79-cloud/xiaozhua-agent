# R1 unblock v2（路由修正）环｜证据件（test2 活体 · 2026-09-30 16:49 CST）

> 性质：写路径 R1（建应用）环 **unblock v2 路由修正重做**。main 诊断 v1 根因 = test2 端点误走 uat
> `default_app_id` 网关前缀、body hostAppName 却填 test2 码 → 网关把 create 路由到 uat 宿主、绑不到 test2 host → status:2。
> v2 修正：所有 test2 端点（serial-config 枚举 + create + 回读）的**网关前缀/appName/hostAppName 三者统一走
> T2 = `znxmglptcopy5791640252914287064`**（config projects L59-73 `running_profile:test2`/`frontDomain:lowcode-test2`）。
> 仓库 `<SEEYON_AGENT_ROOT>`，HEAD `cf45180`。test2 镜像 5.3.496。
> **终态：BLOCKED（环境类 · test2 宿主在 test2 网关下 create 绑不上）** —— T2 前缀下 2/2 create 全 `status:2`，
> 未建成应用，无 `data` id / `appGuid`。需 main 裁定（见 §5）。凭据 0 入件（§6 自检）。

## 0. 环境与时钟（实测）
| 项 | 实测值 |
|---|---|
| 网关 | `{config键 gateway_base}`（test2，值 0 入件；len 37） |
| **T2 前缀**（本轮全部 test2 端点统一用） | `znxmglptcopy5791640252914287064`（config `running_profile:test2`，**非凭据**） |
| 弃用前缀 | uat `default_app_id`（`znxmglpt3289…8017`，v1 已证 status:2 根因，**本轮未再用**） |
| 探针时钟 | 2026-09-30 16:48–16:49 CST |
| 凭据 | `shared-credentials/ctp-user-login.json`（值 0 入件，sha256_16 `392fb61b…`）；本轮重新登录 |
| 应用命名 | `zzprobe20260930H3`（E6 防重名；H1/H2 前两轮用过未建成，H3 新后缀） |

## 1. 鉴权（重新登录）
- POST ctp-user 登录 → **HTTP 200 / BOOT_0000 / SUCCESS**，cookie `SY_ACCESS_TOKEN` 重新获取（值 0 入件，Set-Cookie 回显已脱敏占位，§6）。

## 2. E8 枚举 masterEntity（只读 · 走 T2 前缀）—— **路由修正生效**
- GET `/service/{T2}/udc-runtime/serial-config/select-entity-list?appName={T2}` → **HTTP 200 / BOOT_0000 / SUCCESS**
  / traceId `3253809089993509052`（首调）/ `3253809260785567932`（create-all 内二次）/ **`content` 命中 4 个实体，
  全部 test2 命名空间**（v1 走 uat 前缀时是 18 个 uat 命名空间实体，v2 走 T2 前缀后是 4 个 test2 实体 → **路由修正改变了结果**，坐实 main 根因诊断）。
- 4 个 test2 实体 fullName：`…domain.entity.{Yuedukaohedanju, Jidukaohedanju, Teshukaohedanju, Jdkhlcb}`（前缀 `com.seeyon.znxmglptcopy…064`）。
- 取用：`com.seeyon.znxmglptcopy5791640252914287064.domain.entity.Yuedukaohedanju`（作 `masterEntity`）。

## 3. create 探测（unblock v2 允许 ≤2 次，**已用满 2/2**，均未 BOOT_0000）
端点 POST `/service/{T2}/udc-runtime/custom-app/create`（走 **T2 前缀**）。

| # | body 关键键 | HTTP | envelope | traceId | 结果 |
|---|---|---|---|---|---|
| create-1 | `caption=zzprobe20260930H3` + `hostAppName=T2` + `masterEntity=<test2 实体>` | 200 | `status:2` / code=null | `3253809266405935292` | 静默业务失败 |
| create-2 | `caption=zzprobe20260930H3` + `hostAppName=T2`（**最小体，不带 masterEntity**） | 200 | `status:2` / code=null | `3253809282847606972` | 静默业务失败 |

- **判定**：2/2 全 `status:2`（非 4xx 参数错、非 BOOT_1001 校验错、非 401）→ 即使 T2 前缀 + test2 hostAppName +
  test2 命名空间 masterEntity，create 仍静默失败。

## 4. 回读同一目标（负证据）
- 2 次 create 均无 `data` id → **无有效回读目标**；search-no-page / application.get（走 T2 前缀）无目标可查（未发，避免无效 404）。
- **create 未成功 ⇒ 回读无从命中；不冒充 PASS。**

## 5. 失败归因 + 结论（交 main 裁）
| 类 | 命中 | 证据 |
|---|---|---|
| **环境类（test2 宿主在 test2 网关下 create 绑不上 / T2 前缀网关路由仍非 test2 宿主）** | **是（主因）** | 2/2 status:2（test2 hostAppName + test2 命名空间 masterEntity 均试）；只读 serial-config 在 T2 前缀下正常回 test2 实体，唯独 create 写端点 status:2 |
| 参数错 | 否（v2 已排除） | v1 已坐实必填链 caption/hostAppName；v2 两者都给足 test2 值仍 status:2 → 非参数缺失 |
| 权限不足 | 否 | 全程 200（cookie 有效），无 401/403 |
| 接口不存在 | 否 | create / serial-config 端点均 200（可解析 envelope） |

**诊断（供 main 裁定，非 implementer 决）**：路由修正（T2 前缀）对**只读**端点有效（serial-config 回 test2 实体），
但 **create 写端点在 T2 前缀下仍 status:2**（无论带不带 test2 masterEntity）→ 指向 (a) test2 宿主的 create 写面
在该网关下宿主绑定未坐实，或 (b) T2 前缀的网关路由实际仍非 test2 宿主写面。
**unblock v2 建议交 main 裁**：① 环境侧提供 test2 宿主可用的 create 宿主绑定；或 ② 转 uat 宿主建应用
（改走 uat 网关 + uat `default_app_id` 全套 —— v1 已证 uat 前缀下 hostAppName 用 uat 码可过 BOOT_1001 校验、
仅卡在 status:2 业务态，是更确定的可建路径）。**不硬闯。**

## 6. 脱敏自检（凭据 0 入件）
- 本轮 login 经 Set-Cookie 回显的 token 值已自动替换 `<REDACTED_CREDENTIAL>`；含 cookie 值的 session 临时件用完即删。
- 原始 REQ/RESP 逐字在 `evidence/R1-app-create-unblock-v2-*.jsonl`（含 2 次 create + 2 次 enum + login，全带 traceId）。

## 7. 交付绑定锚（实测）
| 项 | 值 |
|---|---|
| HEAD | `cf45180` |
| v2 证据 jsonl | `R1-app-create-unblock-v2-{20260930164823,20260930164854,20260930164904}.jsonl` |
| 本证据件 | `evidence/R1-app-create-unblock-v2-20260930.md` |
| 九段式 R1 段 | `write-chain.md`（本轮更新为 unblock v2 态：路由修正 + 环境类 BLOCKED） |
| STATUS 追加 | §八.6（unblock v2 段） |
| create 成功数 | **0**（2/2 探测均 status:2）；**deleteByIds 清单：无（未建成）** |
