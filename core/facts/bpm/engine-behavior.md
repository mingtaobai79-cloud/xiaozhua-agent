# BPM 引擎对外行为实测｜flow 族只读端点（flow 域第 3 格）

> 基线：本任务总目标（本会话 `inputs/desktop-source/TASK-GOAL.md` + `main/ROUTE.md` §0/§3）+ 本会话 `HANDOFF-1`。
> 目标仓库 `<XIAOZHUA_AGENT_ROOT>`。九段式能力事实文档（本任务交付物第 1 件，`core/facts/bpm/engine-behavior.md`）。
> 本件**只做 flow 族只读端点对外行为实测**；前两格 `flow-node-tree.md` / `data-flow-map.md` 绑定字节不动；只写事实文档，不实现代码、不改 `components/**`；凭据值 0 入件。
> 探测在先、落盘在后：证据件 `core/facts/bpm/evidence/engine-behavior-live-20260927T092124Z.json`（20098 B，sha256 `2e62ac55…`）先落盘，本格后写。
> 行尾 CRLF（本格登记形态；实测 CR 数 = LF 数 = 行数，`tr -dc`/字节比对计数法；族内行尾不统一）。
> 本格所有 `traceId` / `code` / `message` / 字节数均逐字摘自该证据件，可逐条对上（auditor 判据②）。

---

## 1. Capability

**flow 族只读端点 → test2 网关的对外行为实测** —— 对对照 C 与 T1..T7 共 8 个只读端点，实测引擎在「未带凭据 / 带凭据 / 缺参 / 空实体 / 内部错误」各态的**对外响应形态**（HTTP 码 + envelope 三态 + code + message + traceId）。

- **类型**：READ 型观测（`write=False`，`method` 分 GET 2 条 / POST 5 条 + 对照 C 1 条）；全程只读，无写侧调用。
- **观测面**：网关 → 应用服务（对外响应）；不观测服务端内部实现（见 §7/§9 `UNVERIFIED`）。
- **实测结论概览**（计数为实测枚举，非外推）：
  - **2 条达数据面 `BOOT_0000`**：对照 C（datatype 列表 13 项）、T3（data-flow-map 列表 3 项）。
  - **3 条参数校验类**：T1 `BOOT_1000`、T5/T6 `BOOT_1001`。
  - **2 条空实体业务边界**：T2 `UDCRT_DATAFLOW_0005`、T4 `UDCRT_DATAFLOW_0008`。
  - **1 条引擎内部错误**：T7 `BOOT_4000`。
  - **2 条未鉴权对照**：T2c/T4c `BOOT_1006` + `redirectUrl`（SSO 鉴权墙）。

## 2. Version

- **活体环境**：`config/environments.yaml` L11-21 `environments.test2`（唯一来源键）：`gateway_base=https://lowcode-test2.example.com`；`gateway_prefix_template="/service/{appId}"`；`default_app_id=app9000000000000000001`。同段声明 `udc_image_version: "5.3.496"`（**config 声明值，本轮未实测验证部署镜像版本**，见 §9）。
- **静态契约证据单元**：本地 Maven 5.3.517（`docs/operation-contracts/udc/flow/flow-contracts.md` L2「本地 Maven 5.3.517（全离线，禁相邻版本混写）」）。**与活体 test2 是两个证据单元，禁混写**。
- **本轮活体响应体未回显任何版本号**（实测：10 条响应的 envelope 顶层键一律 `status/code/message/traceId/data`，无版本字段）。

## 3. Input

| 序号 | operation_id | method | 控制器原路径（逐字） | 本轮实测入参 |
|---|---|---|---|---|
| C | `udc.datatype.get_all` | GET | `udc-runtime/datatype/getAll` | 无体（对照端点） |
| T1 | `udc.flow.bpm_node_info_search` | POST | `node-info/search` | 最小体 `{}` |
| T2 | `udc.flow.data_flow_map_get_by_id` | GET | `udc-runtime/data-flow-map/1` | 路径 `id=1` |
| T3 | `udc.flow.data_flow_map_search` | POST | `udc-runtime/data-flow-map/search` | 最小体 `{}` |
| T4 | `udc.flow.data_flow_mapping_get_by_id` | GET | `udc-runtime/data-flow-mapping/1` | 路径 `id=1` |
| T5 | `udc.flow.data_flow_mapping_search_original` | POST | `udc-runtime/data-flow-mapping/search-original` | 最小体 `{}` |
| T6 | `udc.flow.data_flow_mapping_init_data` | POST | `udc-runtime/data-flow-mapping/init-data` | 最小体 `{}` |
| T7 | `udc.flow.data_flow_mapping_detail` | POST | `udc-runtime/data-flow-mapping/detail` | 最小体 `{}` |

- **URL 组装（键写法，非写死）**：`environments.test2.gateway_base` + `gateway_prefix_template`（`/service/{appId}`，`appId` 取键 `environments.test2.default_app_id`）+ 控制器原路径（逐字拼接，不另加前缀）。实测拼接结果见 §5。
- **凭据注入**：`Cookie` 头由 `shared-credentials/test2-web-credential.json` 的键 `cookie_header_template`（`SY_ACCESS_TOKEN={sy_access_token}; TK_EXP={tk_exp}; SY_UID={sy_uid}`）组装，单请求内存注入；**凭据值 0 入件、零回显**（本格与证据件仅存键名与路径引用）。
- **配额**：同一端点最多 2 发；实测 C/T3/T2/T4 各 2 发，T1/T5/T6/T7 各 1 发，合计 12 发（含 C/T3 各 1 次全量落盘重发、T2/T4 各 1 次 cookie-free 对照）= 10 条端点观测（§5 表行数）；无重试轰炸（见 §5 备注与证据件 `send_count`，`total_sends=12` 逐字一致）。

## 4. Required（实测必填链，逐条由引擎响应原文读出）

- **T1**：需 `appName` 或 `pageGuid` —— 缺则 `BOOT_1000`「参数错误:appName/pageGuid 为空!」（原文见 §5）。
- **T5**：需 `dataFlowId` —— 缺则 `BOOT_1001`「dataFlowId must not be null」。
- **T6**：需 `sourceEntity` —— 缺则 `BOOT_1001`「sourceEntity must not be null」。
- **T2 / T4**：路径 `{id}` 须指向已存在实体 —— `id=1` 得 `UDCRT_DATAFLOW_0005` / `UDCRT_DATAFLOW_0008`（空实体业务边界，非鉴权墙、非路由缺失）。
- **T3**：最小体 `{}` 即放行（`BOOT_0000`）。
- **C**：无入参要求（`BOOT_0000`）。

> 口径：以上为**引擎对外响应原文**读出，非静态契约 DTO 外推；契约 DTO 类型（`CBpmNodePermissionRequestDto` 等）仍是静态层事实，见 `flow-contracts.md`（本格不据此改写必填链）。

## 5. Execution（逐端点活体实测表，原始未美化）

| 序号 | method | URL（键组装写法） | cookie | HTTP | bytes | JSON | 顶层键 | code | message（原文） | traceId 原文 | redirectUrl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C | GET | `{gateway_base}` + `/service/{default_app_id}` + `udc-runtime/datatype/getAll` | 是 | 200 | 1822 | 是 | status,code,message,traceId,data | `BOOT_0000` | `SUCCESS` | `3249493134115080380` | 否 |
| T1 | POST | 同上 + `node-info/search` | 是 | 200 | 125 | 是 | status,code,message,traceId,data | `BOOT_1000` | `参数错误:appName/pageGuid 为空!` | `3249493138561042620` | 否 |
| T2 | GET | 同上 + `udc-runtime/data-flow-map/1` | 是 | 200 | 136 | 是 | status,code,message,traceId,data | `UDCRT_DATAFLOW_0005` | `Generation rule diagram does not exist` | `3249493144114301116` | 否 |
| T3 | POST | 同上 + `udc-runtime/data-flow-map/search` | 是 | 200 | 832 | 是 | status,code,message,traceId,data | `BOOT_0000` | `SUCCESS` | `3249493150086990012` | 否 |
| T4 | GET | 同上 + `udc-runtime/data-flow-mapping/1` | 是 | 200 | 143 | 是 | status,code,message,traceId,data | `UDCRT_DATAFLOW_0008` | `Generation rule mapping scheme does not exist` | `3249493154868496572` | 否 |
| T5 | POST | 同上 + `udc-runtime/data-flow-mapping/search-original` | 是 | 200 | 115 | 是 | status,code,message,traceId,data | `BOOT_1001` | `dataFlowId must not be null` | `3249493160002324668` | 否 |
| T6 | POST | 同上 + `udc-runtime/data-flow-mapping/init-data` | 是 | 200 | 117 | 是 | status,code,message,traceId,data | `BOOT_1001` | `sourceEntity must not be null` | `3249493171075287228` | 否 |
| T7 | POST | 同上 + `udc-runtime/data-flow-mapping/detail` | 是 | 200 | 96 | 是 | status,code,message,traceId,data | `BOOT_4000` | `DB Error` | `3249493175772907708` | 否 |
| T2c | GET | 同上 + `udc-runtime/data-flow-map/1` | **否** | 200 | 514 | 是 | status,code,message,traceId,data | `BOOT_1006` | （空） | `3249493180520858395` | **是** |
| T4c | GET | 同上 + `udc-runtime/data-flow-mapping/1` | **否** | 200 | 514 | 是 | status,code,message,traceId,data | `BOOT_1006` | （空） | `3249493186493547291` | **是** |

- **envelope 三态（实测）**：`status=0` → 数据面（C/T3）；`status=1` → 参数校验（T5/T6）；`status=2` → 业务错误/鉴权墙（T1/T2/T4/T7/T2c/T4c）。envelope 形态实测为 `{status, code, message, traceId, data}` 五顶层键。
- **JSID/数据面内容（实测）**：C `data.content` = 13 项（首项键 `validate,name,caption,order,javaType,dataFormat,databaseType`）；T3 `data.content` = 3 项（首项键 `validate,id,guid,appId,caption,definition,description,state,createTime,updateTime`；三项 caption 原文 `合同复制` / `华为生单` / `投标报备-投标费用申请页面`，`appId=3289082814923688017`）。
- **第 2 发（配额内，非重试）**：C 与 T3 各重发 1 次，目的是**完整响应体落盘**（第 1 发仅存 600 B 头）；两次 code 均为 `BOOT_0000`，第 2 发 traceId 原文 `3249494137912690876`（C）/ `3249494142425761980`（T3），全量体 sha256 见证据件。T2/T4 的第 2 发为 cookie-free 对照（T2c/T4c）。
- **未鉴权路径（实测）**：cookie-free 请求 HTTP 仍 200，但 envelope 为 `status=2` + `code=BOOT_1006` + `data.content.redirectUrl`（`https://uatsso.客户方.com/esc-sso/oauth2.0/authorize?...`，原文截断存证据件）。**不得据此断言「端点不存在」** —— 对照 C 用于区分鉴权墙与路由缺失（C 带 cookie 达数据面）。
- **无 403/429**：实测 12 发全部 HTTP 200（无重试轰炸触发点）。

## 6. Side Effects

- **全只读**：本轮仅 GET 与 POST 读型（`write=False`）调用；**未调用任何 `write=True` 端点**（`bpm_fill_error_data` / `data_flow_mapping_update` / `data_flow_mapping_update_state` 一律未触）。
- **无写入副作用观测**：响应对 T1/T2/T4/T5/T6/T7 一律 `data:null`（无业务数据返回）；C/T3 返回读型列表。
- **T7 `BOOT_4000`「DB Error」** 为引擎对外返回码，**照记**；其服务端内部副作用（是否触库、是否产生日志）= `UNVERIFIED`（本格未观测服务端）。
- **HTTP 层无重定向跟随**：实测无 30x（`http_redirect_followed=false`），SSO 墙以 200 + envelope 表达。

## 7. Known Constraints

1. **凭据时效（环境事实，如实登记）**：在盘 `tk_exp=1790438529` = **2026-09-27 00:02:09 +0800**（解析值）；本机时钟（探测时刻）= **2026-09-27 17:21 +0800**，即 `tk_exp` 已过约 17h19m。**但实测带 cookie 请求仍被接受并达数据面**（C/T3 = HTTP 200 + `BOOT_0000`）；cookie-free 对照 = `BOOT_1006` SSO 墙。→ 结论仅限本轮实测：`tk_exp` 客户端字段过期 ≠ 服务端会话已失效；其**有效窗口与服务端校验规则 = UNVERIFIED**。根副本 `agent-collaboration/test2-web-credential.json`（`expires_epoch 1789709327`）更旧，本轮未使用。**禁据此续期或改写 `shared-credentials/`**（禁做项）。
2. **网关 service 前缀**：静态契约 evidence `note` 一律标「网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）」；本轮以键组装（`/service/{default_app_id}`）实测**命中数据面**（C/T3 = `BOOT_0000`）→ 就**本环境 + 本 appId** 而言「前缀可拼接」= LIVE 实测成立；**不外推**到其他环境/appId。
3. **未鉴权 = `BOOT_1006` + `redirectUrl`（SSO 授权墙）**，HTTP 仍 200 → 判端点存在性必须用对照 C；未鉴权响应不得解释成「端点不存在」。
4. **计数纪律（实测枚举）**：`components/platform_operations/registry.py` 实测 `udc.flow.*` `write=False` **8 条** + `udc.microflow.*` **1 条** = **9 条**；`udc.flow.*` 中 `write=True` 在 `registry.py` **0 条**（写侧 3 条仅 `registry-entries.md` 登记，未落地 registry）。→「flow 族 16 契约」口径在盘不成立（沿用前两格「禁照抄 16」）。
5. **未观测项（禁止外推）**：`udc_image_version 5.3.496`（config 声明）未实测验证；引擎内部实现（`BOOT_4000` 根因、鉴权过滤器实现、DB 层）= `UNVERIFIED`；8 端点中仅 C/T3 命中数据面，其余 6 条的「正常路径」响应形态**未实测**，不得由静态契约外推。
6. **本格边界**：不评价写侧 3 条行为、不评价 BPM 引擎本体实现（执行器/模型/调度）= `UNVERIFIED`（整段）。

## 8. Evidence（逐条在盘路径）

- **E1** 本格唯一活体证据源：`core/facts/bpm/evidence/engine-behavior-live-20260927T092124Z.json`（20098 B / sha256 `2e62ac55…`；含 10 条原始观测 + C/T3 第 2 发全量体 + 时钟 + URL 键组装 + registry 计数实测）。
- **E2** 端点集与逐字原路径、URL 组装键：`main/ROUTE.md` §3（本会话）。
- **E3** URL 组装键在盘出处：`config/environments.yaml` L11-21（`gateway_base` / `gateway_prefix_template` / `default_app_id`）。
- **E4** 凭据引用（只读、值 0 入件）：`shared-credentials/test2-web-credential.json`（键 `cookie_header_template` / `tk_exp`）。
- **E5** 契约静态层：`components/platform_operations/registry.py` L50（`udc.datatype.get_all`）、L69-L84（flow 只读族）；`docs/operation-contracts/udc/flow/flow-contracts.md` L10-L89；`registry-entries.md` L13-L209。
- **E6** 计数实测：本机脚本解析 `registry.py`（结果与脚本摘要存 E1 的 `registry_count_measured`）。
- **E7** 前两格（本格未动，绑定字节）：`flow-node-tree.md` 16070 B / sha256 `36ead221…`；`data-flow-map.md` 20703 B / sha256 `4f3e60a4…`（引 `STATUS.md` §1 记账，非本轮复算）。

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| 8 端点在 test2 的可达性（路由存在，非 404） | **LIVE** | E1（12 发全部 HTTP 200 + 业务 envelope） |
| 对照 C 数据面（datatype 列表 13 项） | **LIVE** | E1（traceId 原文 + 全量体 sha256） |
| T3 数据面（data-flow-map 列表 3 项） | **LIVE** | E1（同上） |
| T1/T5/T6 必填参数（appName\|pageGuid / dataFlowId / sourceEntity） | **LIVE**（引擎响应原文读出） | E1 |
| T2/T4 空实体边界码 `UDCRT_DATAFLOW_0005/0008` | **LIVE** | E1 |
| T7 `BOOT_4000`「DB Error」 | **LIVE**（照记；根因 `UNVERIFIED`） | E1 |
| 未鉴权 = `BOOT_1006` + `redirectUrl`（SSO 墙） | **LIVE** | E1（T2c/T4c） |
| 网关 service 前缀可拼接（本环境 + 本 appId） | **LIVE** | E1 |
| flow 族只读计数 9 条（8 + 1） | **实测枚举** | E6 |
| 凭据被接受（tk_exp 过期而请求仍达数据面） | **LIVE（现象）**；有效窗口/校验规则 `UNVERIFIED` | E1 |
| `udc_image_version 5.3.496` 部署态 | **UNVERIFIED**（config 声明，未实测） | E3 |
| 引擎内部实现（`BOOT_4000` 根因 / 鉴权过滤器 / DB 层） | **UNVERIFIED** | 未观测 |
| 写侧 3 条（`write=True`）行为 | **UNVERIFIED**（本轮未调用） | 未观测 |
| **BPM 引擎本体**（执行器 / 模型 / 调度实现） | **UNVERIFIED（整段）** | 本格仅观测对外响应，未直读实现 |

> **收口**：第 3 格已按九段式落盘，逐段锚定在盘实据；LIVE 断言仅限本轮 12 发实测所及；未实测项一律 `UNVERIFIED`，未以「应为/通常」补空。
> 前两格未动（绑定字节见 §8-E7）；`core/facts/INDEX.md` 待主线收口时更新（本轮未动）。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| Capability / Version | `main/ROUTE.md` §3（本会话）；`config/environments.yaml` L11-21；`docs/operation-contracts/udc/flow/flow-contracts.md` L2 |
| Input / Required | E1（`url_assembly` / `entries`）；`components/platform_operations/registry.py` L50/L69-L84；`flow-contracts.md` L10-L89 |
| Execution | E1（10 条 `entries` = 端点观测条数，非发数；原始观测 + C/T3 第 2 发全量体 + `send_count`） |
| Side Effects | E1（`entries[*].code/message`；未调用写侧端点） |
| Known Constraints | E1（`credential` / `registry_count_measured`）；`registry-entries.md` L13-L209 |
| Evidence / Verified | E1-E7（§8 逐条路径） |
