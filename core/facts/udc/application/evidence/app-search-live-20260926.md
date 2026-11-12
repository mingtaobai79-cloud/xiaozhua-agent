# app search 两端点｜LIVE 只读补测证据（S1P · 2026-09-26 CST）

> **性质：探测量（非事实格）**。规格 `main/S1P-PROBE-HANDOFF.md`（dedupe=`app-search-live-probe-s1p`）。
> 只读边界：仅发 `udc.application.search.no_page` / `udc.application.search.page` 两条 `write=False` 查询端点；
> **未**触碰同域写端点（create/copy/deleteByIds/update*）与任何 cache-evict / refresh-*。
> 脱敏口径：URL 一律以 **config 键占位**表达（`{gateway_base}` / `{app_id}`），不写机器字面；
> 凭据仅运行期注入请求头，**值 0 落盘**（本文件、脚本、日志均不含凭据值，脚本不打印请求头）。
> 本文件不写事实格结论，仅提供 S3（`application-search.md`）可引用的实测锚点。

## 0. 环境与时钟（实测）

| 项 | 实测值 |
|---|---|
| 探针时钟 | 2026-09-26 00:46 CST（本机） |
| 仓库 | `<XIAOZHUA_AGENT_ROOT>`，HEAD `16a384c` |
| 凭据引用 | `config/environments.yaml#environments.test2.credential.ref/file`（值不入件） |
| 窗口余量 | 探针运行期实测 `remaining_s = 83684`（≈23.25 h，未过期） |
| 客户端复用 | `components/gateway/client.py:38` `GatewayReadonlyClient`（`allow_network=True` 显式开网） |
| 请求头解析复用 | `components/platform_operations/live_readonly.py:165` 的请求头解析工厂（**函数符号名不复述**：含敏感词根、易被误读为凭据值；逐字符号名与 grep 自检输出见会话件 `implementer/S1P-PROBE.md` §4） |
| 探针脚本 | `implementer/probe_app_search_live.py`（会话目录；仓库零改动） |
| 原始输出 | `implementer/S1P-PROBE.out.json`（stdout 逐字）/ `implementer/S1P-PROBE.err.txt`（空） |

## 1. 逐端点实测（两个端点均**首尝即通**）

| op | method | URL（键组装，未拼字面） | 尝试体 | HTTP | 响应体 B（wire 实测） | envelope code | envelope msg | traceId（首次） | data 结构（实测） | 双发 identity | **终态** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `udc.application.search.no_page` | POST | `{gateway_base}/service/{app_id}/udc-runtime/custom-app/search-no-page` | `{}` | **200** | **105** | **BOOT_0000** | SUCCESS | `3247042976269994172` | `data.content = []`（0 条） | md5(去 traceId) `1e6f194d0381d4fe28cfe7abb5675b78` ×2 → **MATCH**（二次 traceId `3247042983182207164`，HTTP 200/BOOT_0000） | **LIVE** |
| `udc.application.search.page` | POST | `{gateway_base}/service/{app_id}/udc-runtime/custom-app/search-page` | `{"pageInfo":{"pageNo":1,"pageSize":10}}` | **200** | **202** | **BOOT_0000** | SUCCESS | `3247042987309402300` | `data.pageInfo`（6 键）+ `data.content = []`（0 条） | md5(去 traceId) `65933780b01157367094d42ebf9ba588` ×2 → **MATCH**（二次 traceId `3247042991671478460`，HTTP 200/BOOT_0000） | **LIVE** |

- **端点原路径**逐字取自 `registry.py` L86（no_page）/ L88（page），类级前缀 `udc-runtime/custom-app`
  （`docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md` L21-22 / L36-37 同源）。
- **identity 算法**：响应对 JSON 去 `traceId` 后 canonical dump 的 md5，双发比对（二次 traceId 不同、内容 md5 相同 → 结果稳定）。

## 2. 参数字典实测（与预登记尝试序的差异，如实记录）

- 预登记序：no_page 依次 `{}` → `{"params":{}}` → `{"params":{},"sort":{}}`；page 依次 `{"pageInfo":{...}}` → `+params` → `+sort`。
- **实测**：两端点均在**第 1 次尝试**即 200/BOOT_0000 → P2/P3、Q2/Q3 **未执行**（成功后即停，不为凑样本多发请求）。
- → 预登记的「错误信息即参数字典」补齐轮次**未触发**：`params` / `sort` 键在本次实测中**未被服务端要求**。
- **边界（不臆造）**：`params`/`sort` 是否影响结果集、`{}` 与带参形态是否语义等价 → 本轮**无证据 = UNVERIFIED**，不外推。
- 停止规则（同端点连续 2 次同码失败即停）**未触发**（无失败尝试）。

## 3. 终态判定（写死，不留「未测」）

- `udc.application.search.no_page` = **LIVE**（HTTP 200 + envelope BOOT_0000/SUCCESS + traceId + 双发 identity MATCH + 响应 105 B）。
- `udc.application.search.page` = **LIVE**（同上 + 响应 202 B）。
- **同时如实标注（关键）**：两条的 `data.content` 均为**空列表（0 条）** →
  **传输 / 授权 / 包封 / 可解析链已坐实；业务数据面为空**。
  S3 引用口径：按 LIVE 记录（HTTP+envelope+traceId+identity 四要素齐），并**显式注明「返回非空列表未观测到」**；
  空集成因（凭据用户可见范围 / 目标应用无自定义应用 / 参数过滤）**无证据 → UNVERIFIED，不外推**。

## 4. 边界与未做（禁外推）

- 未探测第三、第四端点（applog 族另有计划）；未触碰任何写端点 / cache-evict / refresh-*。
- 未改 `registry.py` / `components/` / `docs/` / 其他事实格；未 `git push`。
- 未申请新凭据，未在窗口外重试；凭据值未落入任何文件（见 §5）。

## 5. 脱敏自检

- 本文件**不含**网关字面、`app_id` 字面、任何凭据值；URL 100% 以 config 键占位。
- 严格 grep 自检：按 ROUTE §3 的检索式（5 个词根逐字见会话件 §4，此处不复述以免自命中）检索本文件 = **0 命中值**。
- 探针 stdout/stderr 落 `implementer/`（会话目录）：stdout 仅含键组装 URL + 响应侧事实（HTTP/envelope/traceId/字节数/结构形状），
  stderr 为空；脚本设计上**不打印请求头**（`request` 字段未进任何输出）。
