# e6｜P6 认证态只读差分探测（SSO 提供方分发面）— 2026-10-03

## 0. 边界声明
- 全程 0 SSH / 0 kubectl / 0 host-key 绕过 / 0 写面 / 0 zzprobe 建应用 / 0 改既有测试。
- 请求形态: 认证态只读 GET，Cookie 三键（`SY_ACCESS_TOKEN` / `TK_EXP` / `SY_UID`）**已按
  `shared-credentials/test2-web-credential.json` 的 `cookie_header_template` 填充**；本件不落任何键值真值。
- 凭据有效性实测（只读元数据，不打印真值）: `expires_epoch=1791114524` vs 探测时 `now=1791028987`
  ⇒ 有效，剩余 85537 s（≈23.8 h）。
- 本件为**新增**证据件，未触碰 e1–e5 与 `spi-ext-runtime.md` §1–§11。

## 1. 探测设计（先列后打）
- 目标（G2 取证面）: 观测 SPI 提供方 `SsoService` 实现（注册契约=`spi-ext-registration.md` §5/§6，
  `getName()`→`"template"`）在 test2 运行态是否被真实分发/调用。
- 方法: **差分探测**。同形态、同层位各打一次「已注册提供方名 `template`」与「未注册名 `zznone9x7q`」；
  若两者响应存在可区分差异 ⇒ 说明服务端按 SPI 提供方名查表并被触达；若逐字节同源 ⇒ 说明该路径由前端静态层
  兜底呈现，**请求未进入承载 SPI 的应用进程**。
- 端点合法性来源: `e5-runtime-probe-recheck-20261003.md` §P3 已登记路径 `/login/third-auth/{name}`
  （第三方授权回调），本件仅替换 `{name}` 段，未新造路径。
- 预算: 硬上限 3 发，本件实用 **2 发**；每端点恰 1 发；0 重试。

## 2. 逐发原始记录
### SHOT-1
- `date -u`: 2026-10-03T12:03:07Z
- 端点: `GET https://lowcode-test2.example.com/login/third-auth/template`
- 请求形态: GET，0 query，0 body，Cookie 三键已按模板填充
- 响应层级: DNS/TCP/TLS 成功 / HTTP **200** / `Content-Type: text/html` / **7405 B**
- 关键头: `x-oss-request-id`、`x-oss-object-type: Normal`、`x-oss-storage-class: Standard`、
  `x-oss-meta-x-oss-meta-app: app-common`、`ETag: "E8E8185EE0ACAF410FC61B2EB7688168"`、
  `Last-Modified: Mon, 14 Sep 2026 02:01:03 GMT`、`Accept-Ranges: bytes`
- 正文摘要（≤400 B）: `<!doctype html><html><head>…<title></title>…
  <script src="/custom-extensions/pc_extensions.js?v=20260914100054"></script>…`（SPA 壳）
- `curl exit`: 0

### SHOT-2
- `date -u`: 2026-10-03T12:03:08Z
- 端点: `GET https://lowcode-test2.example.com/login/third-auth/zznone9x7q`
- 请求形态: 同上（对照发）
- 响应层级: DNS/TCP/TLS 成功 / HTTP **200** / `Content-Type: text/html` / **7405 B**
- 关键头: `ETag: "E8E8185EE0ACAF410FC61B2EB7688168"`（与 SHOT-1 **同一 ETag**）、
  `Last-Modified` 同、`x-oss-*` 同族头同在
- 正文摘要: 与 SHOT-1 同字节长度、同 SPA 壳起始段
- `curl exit`: 0

## 3. 观测事实（不含裁断）
- F1: 两发 HTTP 状态、字节数（7405）、`ETag`、`Last-Modified` **全部一致**；`x-oss-*` 头族表明对象由
  阿里云 OSS 静态对象存储直接呈现（前端托管层），非应用服务端渲染或后端重定向。
- F2: 「已注册提供方名」与「未注册名」**不可区分** ⇒ 该路径在本层位未体现任何按 SPI 提供方名的服务端查表行为。
- F3: 7405 B / 同 ETag 与 `e5` §P3（0 凭据、同一路径族）**逐字节同对象** ⇒ 认证态与非认证态在该层位
  呈现完全一致；本件的 Cookie 有效性**无法**从此端点得到印证（≠ 反向证否，HUMAN 已实测 `getAll` 命中）。
- F4: 无 `Location` 重定向、无 `BOOT_*` 业务码、无 JSON 业务体 ⇒ 未观测到 `SsoService` 方法
  （`login`/`getCodeUrl` 类）被调用的任何响应侧特征。

## 4. 判级（四类分写）
- **LIVE PASS**: **无**。本件未取得可归因于 SPI 扩展点/插件加载或提供方调用的运行态响应。
- **已调用但业务数据未验证**: 无（未观测到调用特征）。
- **明确问题（负结果事实，可复用）**: `/login/third-auth/{name}` 在 test2 由 **OSS 前端静态壳兜底**，
  以 GET 方式访问**不进入**承载 `boot-starter-spi-customized` 的应用进程 ⇒ 该端点族作为
  「SPI 提供方调用面」的**只读观测点不成立**（差分不可区分即为其证明）。后续同类取证不宜再消耗预算于此路径。
- **未测试（保持开放）**:
  - (a) SPI 提供方**真实登录流转**（需有效 SSO 会话 + 上游 CAS 回调参数，属写/交互面，未授权）；
  - (b) 服务端 SPI 加载链日志（`ctp-user`/`cip-connector` 容器日志，需人工门①可信 host key/kubeconfig）；
  - (c) 部署态客开 jar 是否存在（需人工门③写面方案授权）。
- 残留预算: 3 发上限实用 2 发，剩 1 发**主动不用**——盘上无可登记来源的 SPI 可归因只读服务端端点；
  以杜撰路径消耗发数不产生可解释事实（`GET /udc/*` 404 已实测、`udc-runtime` 面 e3 §C1 已定性为业务数据面）。

## 5. 与既有件的口径一致性
- 本件**不推翻** `e3` §C1「udc-runtime 不呈现 SPI 加载链」；两发的「鉴权可达」亦**不升级为** SPI 系统事实。
- 判级口径与 `e4`/`e5` 相同: HTTP 200、静态壳、空结果一律不算 PASS。
