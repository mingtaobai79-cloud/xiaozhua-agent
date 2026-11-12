# R1 建应用环｜证据件（test2 活体 · 2026-09-30 CST）

> 性质：**写路径 R1（建应用）环探测 + 回读 LIVE 证据**。spec `main/ROUTE.md`（E1–E6）+ main HANDOFF
> `r1-app-create-handoff-v1`（dedupe=`r1-app-create-handoff-v1`）。
> 仓库 `<XIAOZHUA_AGENT_ROOT>`，HEAD `cf45180`。test2 镜像版本 5.3.496（`config/environments.yaml` 键）。
> **终态：BLOCKED（参数错类）** —— create 未在 8 次探测预算内收敛到 BOOT_0000；
> `caption` + `hostAppName` 已被服务端错误字典确认必填，但 `hostAppName` 有效值（真实宿主应用名）未知，
> 两种猜测形态均返回业务失败（`status:2` 静默）。**需 main 提供有效 `hostAppName` 或放行继续探测，R1 方可闭环。**
> 凭据 0 入件（仅 ref 路径 + sha256 + cookie 长度；含 token 值的一次 login 响应已脱敏为占位，详见 §7）。

## 0. 环境与时钟（实测）

| 项 | 实测值 |
|---|---|
| 网关 | `{config键 gateway_base}` = test2（值 0 入件；len=37） |
| 目标 app | `{config键 default_app_id}`（值 0 入件；len=27） |
| 前端控制器 | `CustomApplicationController` 类级 `udc-runtime/custom-app`（javap L1133，V 件在盘） |
| 探针时钟 | 2026-09-30 15:36–15:48 CST（本机） |
| 凭据引用 | `shared-credentials/ctp-user-login.json`（写路径用户登录流；值 0 入件，sha256_16 `392fb61b…`） |
| 已弃用只读件 | `shared-credentials/test2-web-credential.json`（`scope=read-only`，09-28 已过期，**本写环未用**） |

## 1. 鉴权（登录换会话 cookie，活体）

- POST `{ctp-user 登录端点}`（值取自 ctp-user-login.json，0 入件）→ **HTTP 200 / BOOT_0000 / SUCCESS**
  / traceId `3253736491523770556` / resp 774 B。
- 会话 cookie `SY_ACCESS_TOKEN`（Set-Cookie）= len **327**（值 0 入件；仅存 session 临时件，已删除）。
- 后续 create / search / get 请求头携带该 cookie；**cookie 值 0 落任何 evidence 件**（§7 脱敏复核 = 0 命中）。

## 2. 查重名（E6，建前先 search-no-page）

- POST `…/udc-runtime/custom-app/search-no-page`，`params.name=zzprobe` → **HTTP 200 / BOOT_0000 / SUCCESS**
  / traceId `3253738498850556092` / **resp 105 B / `data.content=[]`（0 条）**。
- 枚举补充（同端点）：`{}`、`{"params":{}}`、`name=znxmglpt`、`caption=项目管理` 全部 → 200/BOOT_0000 / **0 条**。
- **结论：可见范围内无 zzprobe* 既有应用，也无任何 custom-app 列表行**（与已收口事实格
  `application-search.md` §7「`data.content` 空集成因 UNVERIFIED」一致，不重复建、不臆测非空）。

## 3. create 探测（错误驱动，**已用满 8/8 次**，原始 REQ/RESP 见 `evidence/*.jsonl`）

端点：POST `…/udc-runtime/custom-app/create`（`CreateOnlyPageApplicationDto`；javap L402 方法 /
L427-428 `@PostMapping("/create")`；响应 `SingleResponse<Integer>`）。DTO 字段静态件（udc-facade 5.3.496，
本环自解）：`caption, hostAppName, pageUrl, pageUrlTypeEnum, masterEntity, originAppName,
originPageGuid, originPageUrl, spiltTerminal, authJson, copySchema, description`；含 `@NotBlank` +
`AppService.ValidationGroup.Create` 校验组。**注意：DTO 无 `name` 字段** —— 服务端校验链实为
`caption` → `hostAppName`，`name` 键被忽略。

| 探测 | 请求体（关键键） | HTTP | envelope | traceId | 服务端原文（参数字典） |
|---|---|---|---|---|---|
| 1–3 | `{}` / `{name}` / `+description` | 200 | `BOOT_1001` | `3253738870…/…76/…412` | **`caption must not be blank`** |
| 4–6 | `+caption` / `+caption,pageUrl,…` | 200 | `BOOT_1001` | `…968038076/…82435772/…8955478` | **`hostAppName must not be blank`** |
| 7 | `caption` + `hostAppName={default_app_id}` | 200 | `status:2` / code=null | `3253747748884711612` | 业务失败（静默，无 msg） |
| 8 | `caption` + `hostAppName=znxmglpt` | 200 | `status:2` / code=null | `3253747756870666428` | 业务失败（静默，无 msg） |

- **参数字典（本环实测坐实）**：必填 `caption`（NotBlank）+ `hostAppName`；`hostAppName` 须引用
  **一个真实存在的宿主应用**。探测 7/8 用了两种 `hostAppName` 猜测形态（config `default_app_id` 全值 /
  前缀 `znxmglpt`）→ 均 `status:2` 静默业务失败（非 4xx 参数错、非 BOOT_1001 校验错）→
  判定：**两值都不是合法宿主应用名**（或未同时满足下游 `masterEntity`/`pageUrl` 依赖）。
- **未产生任何成功建应用**：无 `data` id、无 `appGuid` → **R1 回读目标尚未生成**。

## 4. 回读同一目标（E4，负证据）

- `application.get` GET `…/udc/application/{default_app_id}` → **HTTP 404**（134 B，非 envelope）/ traceId `None`。
  **归因：`default_app_id` 是网关 `/service/{appId}` 路由 id，不等于 `/udc/application/{id}` 的应用实体 id
  → 404 = 目标 id 形态不符，非接口不存在。**（与事实格 `application-search.md` §4「网关前缀/路由
  UNVERIFIED、禁止拼前缀」一致。）
- `search-no-page` 按名称回读 → **0 条**（§2 已述）。
- **结论：create 未成功 ⇒ 无有效回读目标；回读端点本身可达（200），但业务数据为空/404 → 不冒充 PASS。**

## 5. 失败三类归因（ROUTE §完成标准 · 不硬闯）

| 类 | 命中 | 证据 |
|---|---|---|
| 参数错 | **是（主因）** | `caption`/`hostAppName` 必填链坐实；`hostAppName` 有效值未知 |
| 权限不足 | 否 | 全程 200（cookie 有效），无 401/403 |
| 接口不存在 | 否 | create/search 端点均 200；`application.get` 404 = 目标 id 形态不符（非端点缺失） |

## 6. 终态与 unblock 动作（交 main）

- **R1 = BLOCKED（参数错类）**：8/8 探测预算用满，create 未收敛。继续推进**唯一缺的输入**是
  一个**有效 `hostAppName`**（真实宿主应用名，须其下可挂只页应用）。两选：
  ① main 从环境侧给出有效 `hostAppName`（及其 `masterEntity`/`pageUrl` 若需要）→ implementer 下一单步直接 create；
  ② main 放行追加探测预算（>8 次）并给宿主应用枚举线索（本仓静态 javap 无宿主应用名值；
     search-no-page 可见范围为空，枚举不到宿主应用）。
- **不自行删**：本环未建成任何应用，无 `deleteByIds` 清单可回滚；九段式 Side Effects/回滚段如实登记为「无」。
- 本环**只动了** `write-chain/**` + `STATUS.md` 追加段（§八），未改其他 facts 目录 / registry / components。

## 7. 脱敏自检（凭据 0 入件 · 实测）

- 自检脚本 `scripts/_tmp_leakcheck.py`：比对 live 敏感值（`loginName`/`password` + session cookie token，
  值不回显）× 全部 `evidence/*.jsonl` + `STATUS.md` → **命中 2（均在 login 记录 resp_body 里回显的
  `SY_ACCESS_TOKEN` 值）→ 已脱敏为 `<REDACTED_CREDENTIAL>` 占位，复核 = 0 命中**。
- 含 cookie 值的 `.session-*.json` 临时件**已删除**（不进 git、不留盘）。
- 原始 REQ/RESP 逐字在 5 件 jsonl（共 12 记录 / 5817 B）：`R1-app-create-{153640,153840,153902,154502,154751}.jsonl`
  （login/dedupe/create×8/readback 全在盘可溯）。

## 8. 交付绑定锚（实测值）

| 项 | 值 |
|---|---|
| HEAD | `cf45180` |
| 证据 jsonl | `core/facts/udc/write-chain/evidence/R1-app-create-*.jsonl`（5 件，5817 B） |
| 本证据件 | `core/facts/udc/write-chain/evidence/R1-app-create-20260930.md` |
| 九段式格 | `core/facts/udc/write-chain/write-chain.md`（本环新建，R1 段 + 骨架） |
| STATUS 追加 | `STATUS.md` §八（R1 建应用环 · BLOCKED-参数错） |
| create 成功数 | **0**（8 次探测均未 BOOT_0000） |
| 凭据入件 | **0**（§7 自检通过） |
