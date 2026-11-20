# e5 — 运行态有界只读复测记录（P5；3 发硬上限，全 GET，0 凭据，0 重试）

> 采集会话: implementer / P5（HANDOFF dedupe `p5-handoff-20261003T0839Z`）
> 时钟口径: 全部 `date -u`（UTC）
> 请求形态: `curl -sS -g --max-time 12 <URL>`；0 header 凭据、0 body、0 cookie、0 query
> 目的: ①复测 e4 所记传输层不可达是否仍复现（TASK-GOAL 记 09-29 15:0x 网关恢复 vs e4 09-30T20:20Z TLS 中断 ⇒ 存在时点差）；②检索任一**可归因于 SPI 扩展点/插件加载或调用**的运行态响应。

## 探测逐发记录

### P1 — 网关根（C1）
- 时间: 2026-10-03T08:43:07Z（UTC，`date -u` 实测）
- 端点: `GET https://lowcode-test2.example.com/`
- 请求形态: GET，无 query、无 body、0 header 凭据
- 响应层级: DNS 解析成功 / TCP 连接成功 / **TLS 握手成功** / HTTP **301**（Server: nginx）/ 正文 **162 B**：`<html>…<title>301 Moved Permanently</title>…<center>nginx</center>…`
- CURL_EXIT=**0**
- 判级: **通道可达（探测面事实）**。响应为网关重定向提示页，与 SPI 扩展点/插件加载或调用**无可归因关系** ⇒ 不记 LIVE。
- 对照既有: e4 P1（2026-09-30T20:20:41Z）记 CURL_EXIT=35（TLS Recv failure）⇒ **同一端点本次不复现**；差异属探测面（会话/时点），不构成被测系统运行态结论。

### P2 — udc-runtime 只读对照端点（C1，0 凭据）
- 时间: 2026-10-03T08:43:08Z（UTC）
- 端点: `GET https://lowcode-test2.example.com/service/app9000000000000000001/udc-runtime/datatype/getAll`
- 端点合法性来源（在盘登记，非猜测）: `core/facts/bpm/engine-behavior.md` L63（行 C，鉴权=是 → 200/1822 B/BOOT_0000）与 L71（行 T2c，鉴权=否 → 200/514 B/BOOT_1006）；`core/facts/bpm/evidence/engine-behavior-live-20260927T092124Z.json` `url_assembled_written_form`
- 响应层级: DNS/TCP/TLS 成功 / HTTP **200** / 正文 **514 B**；字段结构 `status,code,message,traceId,data`；`status=2`、`code=BOOT_1006`、`message` 为空、`traceId=3258152084922434331`、`data.content.redirectUrl` 指向外部 SSO 授权端点
- 凭据处理: `redirectUrl` 取值含 client_id / 回调 URL / oauth 时间戳等参数 ⇒ **按「凭据 0 入件、含凭据 URL 不落文」仅登记字段名，不转录取值**
- CURL_EXIT=**0**
- 判级: **明确问题（0 凭据条件下业务面被 SSO 鉴权墙拦截，未获得业务 data）**；HTTP 200 与空 `message` 一律不算 PASS。响应可归因于网关鉴权跳转，**不可归因于 SPI 扩展点/插件加载或调用** ⇒ 不记 LIVE。
- 对照既有: 与 e3 §C1 判定一致（udc-runtime 属业务数据面，不呈现 SPI 加载链），且与 engine-behavior 已登记 BOOT_1006 形态逐字段相符 ⇒ 本发无新增通道结论。

### P3 — SSO 提供方调用面最近登记路径（C1 / SPI 关联面）
- 时间: 2026-10-03T08:43:08Z（UTC）
- 端点: `GET https://lowcode-test2.example.com/login/third-auth/code`
- 端点合法性来源: P2 响应体内回调路径；`docs/operation-contracts/udc/microflow/live-evidence/**`（他线既有件，仅取**路径名**作合法性来源，未取其中真值、未改动）
- 请求形态: GET，无 query、无 body、0 header 凭据、0 cookie
- 响应层级: DNS/TCP/TLS 成功 / HTTP **200** / 正文 **7405 B**，内容为前端 SPA 壳：`<!doctype html><html>…<title></title>…<script src="/custom-extensions/pc_extensions.js?v=20260914100054"></script><link rel="stylesheet" href="/c…`
- CURL_EXIT=**0**
- 判级: **未测试（SPI 提供方调用未被观测）**。该路径为第三方授权回调；进入 SPI 实现 `com.seeyon.extend.spi.sso.TemplateSsoServiceImpl`（注册契约见 spi-ext-registration.md §5/§6，接口 `com.seeyon.cip.connector.api.sso.SsoService`）需有效 SSO 会话/凭据，本线未持有、**不自行取用** ⇒ 登记为「未测试 / 需人工门」并停。HTTP 200 + HTML 壳不算 PASS。

## 探测结论（P5 产出）
- **3 发（硬上限）均未获得可归因于 SPI 扩展点/插件加载或调用的运行态响应**；无任一 LIVE 命中。达 3 发即停，未重试、未换分支、未扩 SSH/kubectl、未开写面。
- 新增可登记事实: ①网关根 `GET /` 于 2026-10-03T08:43:07Z = TLS 成功 + HTTP 301（e4 的 exit 35 本次不复现）；②`udc-runtime/datatype/getAll` 在 0 凭据下 = HTTP 200 / BOOT_1006 SSO 鉴权墙（与在盘既有事实相符，含 traceId 可复核）；③SSO 授权回调路径可达但返回前端壳，SPI 提供方调用面被鉴权前置阻挡。
- 四类分写（据实）: **LIVE PASS = 0**；**已调用但业务数据未验证 = 0**；**明确问题 = P2**（0 凭据鉴权墙，非业务数据面）；**未测试 = P3**（缺凭据 ⇒ 人工门）；P1 属通道可达性事实，不入 PASS。
- 判级依据（不越级）: SPI 运行态**加载链**唯一直接观测载体仍为承载 boot-starter-spi 的平台进程（ctp-user / cip-connector）启动/运行日志（e3 §2、本格 §4），该载体仅 SSH/kubectl 可得；SPI 提供方**调用**需有效 test2 会话凭据。二者本线均未获授权 ⇒ 未绕行、未自决。
- 所缺人工门（事实登记）: ①可信 host key / 可信 kubeconfig → P4a 后 `kubectl logs` grep 加载链关键串；②`test2-web-credential` 有效会话 → SSO 提供方调用面观测。
- 边界遵守: 0 SSH、0 host-key 绕过、0 kubectl、0 凭据构造、0 写面（未建 zzprobe 应用、未上传 jar、未改 Nacos 配置）、0 既有测试改动、0 重试；未触碰 e1–e4、`hashes/evidence-inventory.sha256.txt`、`core/facts/INDEX.md`、`components/`、`core/tools/`、`adapters/`、`tests/`、`xiaozhua_cli.py`、`xiaozhua_host_bootstrap.py`、`docs/audit/**`。
