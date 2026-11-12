# R1 unblock v3（静默成功排除 + 独立建应用主线 B）环｜证据件（test2 活体 · 2026-09-30 17:21 CST）

> 性质：写路径 R1（建应用）环 **unblock v3**（main 复核 v2 环境类 BLOCKED 后，切两条独立主线：
> A 静默成功排除（只读）+ B 从未试过的设计态草稿写面 `app-draft/create`）。
> spec `main/ROUTE.md`（E9/E10 + unblock v3 最小动作）+ main HANDOFF `r1-app-create-unblock-v3-handoff-v1`。
> 仓库 `<SEEYON_AGENT_ROOT>`，HEAD `cf45180`。test2 镜像 5.3.496。
> **终态：B 命中 = R1 LIVE PASS（设计态应用草稿写面 `app-draft/create`）** —— `app-draft/create`
> 第 4 次探测（T2 前缀 + 正确字段 `dataId`+`draftData`）= **200/BOOT_0000/SUCCESS，`data.content=1`**；
> 同目标回读 `app-draft/select?dataId=1`（T2 前缀）= **非空草稿样本**（traceId `3253841201584933052`）。
> **口径差如实登记（交 main 裁）**：B PASS 的是**设计态草稿写面**，非 v1–v2 反复 status:2 的
> **只页 custom-app 写面**；草稿面 DTO 无 `appGuid`（发布后才 mint）→ 收口判据改为「草稿存在性」。凭据 0 入件（§6）。

## 0. 环境与时钟（实测）
| 项 | 实测值 |
|---|---|
| 网关 | `{config键 gateway_base}`（test2，值 0 入件） |
| T2 / default_app_id | `znxmglptcopy579…064`（test2）/ `{default_app_id}`（uat，值 0 入件） |
| 本轮新端点（B 独立主线） | `POST …/udc-runtime/app-draft/create`（`AppDraftController`，类级 `udc-runtime/app-draft`，静态 javap 在盘） |
| 探针时钟 | 2026-09-30 17:14–17:21 CST |
| 凭据 | `shared-credentials/ctp-user-login.json`（值 0 入件，sha256_16 `392fb61b…`）；本轮重新登录（cookie 值 0 入件） |

## 1. 鉴权
- 重新登录 → **HTTP 200 / BOOT_0000 / SUCCESS**，cookie `SY_ACCESS_TOKEN`（值 0 入件，Set-Cookie 回显已脱敏占位，§6）。

## 2. A · 静默成功排除（只读 search sweep，≤6 次，不计 create 预算）
`POST …/udc-runtime/custom-app/search-no-page` 按 caption `zzprobe20260930H1/H2/H3` × 前缀（T2 + default_app_id）各一遍：

| 前缀 | H1 | H2 | H3 | content | traceId |
|---|---|---|---|---|---|
| T2 | 200/BOOT_0000 | 200/BOOT_0000 | 200/BOOT_0000 | **全 `[]`（0 条）** | `3253837421510396092`/`…976`/`…434` |
| default_app_id | 200/BOOT_0000 | 200/BOOT_0000 | 200/BOOT_0000 | **全 `[]`（0 条）** | `3253837440384764092`/`…450`/`…456` |

- **结论：6/6 全 `content=[]` → 之前 3 轮 `status:2`（custom-app/create）确为「未建成」，非「已建成但回读空作用域」→
  静默成功排除，进 B。**（200/空结果 不算 PASS，符合纪律。）

## 3. B · 独立建应用主线（设计态草稿写面 `app-draft/create`，未在任何轮试过）
端点：`POST {gateway}/service/{prefix}/udc-runtime/app-draft/create`（`AppDraftController.createOrUpdate(AppDraftDto)`
→ `SingleResponse<Integer>`；静态 javap `docs/audit/artifacts/udc-app-basic/…AppDraftController.javap.txt`）。
`AppDraftDto` 字段（test2 5.3.496 jar 自解）= **`dataId` + `draftData`**（本轮 b5 用对；b3/b4 误用 appName/caption）。

| # | 前缀 | body | HTTP | envelope | traceId | 结果 |
|---|---|---|---|---|---|---|
| b1 | default_app_id | `{}` | 200 | **BOOT_1001**「dataId 数据id不能为空; draftData 草稿内容不能为空」 | `3253837769134311612` | **可达性 PASS：端点存在（非 404）**，错误字典坐实必填 = `dataId`+`draftData` |
| b3 | default_app_id | `{appName,caption}`（误字段） | 200 | BOOT_1001 同上 | `3253837775174109372` | 字段未对上（未用 DTO 真名） |
| b4 | T2 | `{appName,caption}`（误字段） | 200 | BOOT_1001 同上 | `3253837780207274172` | 同上 |
| **b5** | **T2** | **`{dataId:1, draftData:"{}", caption:zzprobe20260930H3}`** | **200** | **BOOT_0000 / SUCCESS** / `data.content=1` | `3253838679969368252` | **B PASS：草稿建成（dataId=1 回显）** |

- **B 预算 ≤4 次，用满 4/4，第 4 次即收敛 BOOT_0000**（服务端错误字典驱动：b1 揭示 `dataId`+`draftData` 必填，
  b5 补齐即成功）。**非硬闯、非试已试宿主组合**（B 是 v1–v2 从未试过的 `app-draft` 独立写面）。

## 4. 回读同一目标（B 命中的草稿）
| 回读 | 前缀 | HTTP | envelope | 结果 |
|---|---|---|---|---|
| `POST …/app-draft/select` `{dataId:1}` | **T2** | 200 | **BOOT_0000** / `data.content={"validate":true,"dataId":"1","draftData":"{}","updateTime":1790759899000}` | **非空草稿样本命中**（traceId `3253841201584933052`） |
| `POST …/app-draft/select` `{dataId:1}` | default_app_id | 200 | BOOT_0000 / `data.content=null` | uat 前缀下查不到 → **证明草稿 host-scoped = T2**（traceId `3253841208128047292`） |
| `POST …/custom-app/search-no-page` `{caption:H3}` | T2 / default | 200 | BOOT_0000 / `content=[]` | 草稿≠只页应用（草稿未发布，符合预期）（traceId `3253841213916186812`/`3253841220375414972`） |
| `GET …/udc/application/1`（按 create 回显 dataId=1） | T2 / default | **404** | — | dataId=1 是草稿行 id，**非 `/udc/application/{id}` 应用实体 id**（不同面） |

- **同目标回读结论**：`app-draft/select`（T2 前缀）命中 **非空草稿 `dataId=1 / draftData="{}" / updateTime=1790759899000`**
  → 写→回读同一目标配对成立。**注：草稿 DTO 无 `appGuid`/名称键**（草稿是待发布设计态，发布后才 mint appGuid）→
  **R1 收口判据 = 草稿存在性（非空 content + dataId + updateTime），非 custom-app 的 appGuid 非空**（口径差，如实登记）。

## 5. 终态 + Side Effects + 回滚（交 main）
- **R1 = B 命中 = LIVE PASS（设计态草稿写面）**。custom-app 只页应用写面维持 v2 的 BLOCKED-环境（host 绑定未坐实），
  但 TASK-GOAL 写路径链第 1 环「建应用」经 B 独立主线已闭环（建应用草稿 → 回读同一草稿 → 非空 LIVE 证据）。
- **Side Effects（本轮实建，非零）**：1 条设计态应用草稿（宿主 = T2，`dataId=1`，`draftData="{}"`，updateTime `1790759899000`）。
- **回滚方式（不可逆写 → 先报清单经 main 确认，不自行删）**：`POST /service/{T2}/udc-runtime/app-draft/delete`
  body `"1"`（`AppDraftController.delete(String dataId)` → `SingleResponse<Integer>`，静态 javap 在盘）清掉本条草稿；
  或 `/delete-all` / `/delete/timeout`。**deleteByIds 清单 = [dataId=1 @ T2]，待 main 确认。**
- **口径裁示（交 main）**：① 接受 B（草稿面）作为 R1 收口 → 进 R2；或 ② 要求 R1 必须 custom-app 只页应用面
  （则维持 v2 BLOCKED-环境，需环境侧给可用宿主绑定或授权转 uat 全套）；或 ③ 发布该草稿（`deploy` 面）mint appGuid 再按 custom-app 口径回读。

## 6. 脱敏自检（凭据 0 入件）
- 本轮 login Set-Cookie 回显的 `SY_ACCESS_TOKEN` 值自动脱敏 `<REDACTED_CREDENTIAL>`；含 cookie 值的 session 临时件用完即删。
- 原始 REQ/RESP 逐字在 `evidence/R1-app-create-unblock-v3-{171703,171724,171818,172048}.jsonl`（16 记录 / 14 traceId，全在盘）。

## 7. 交付绑定锚（实测）
| 项 | 值 |
|---|---|
| HEAD | `cf45180` |
| v3 证据 jsonl | `R1-app-create-unblock-v3-{20260930171703,171724,171818,172048}.jsonl`（16 记录） |
| 本证据件 | `evidence/R1-app-create-unblock-v3-20260930.md` |
| 九段式 R1 段 | `write-chain.md`（本轮更新为 unblock v3 态：B PASS + 回滚清单） |
| STATUS 追加 | §八.7（unblock v3 段） |
| B create 成功 | **1**（b5，BOOT_0000，data.content=1） |
| deleteByIds 清单 | **[dataId=1 @ T2] 待 main 确认（不自行删）** |
