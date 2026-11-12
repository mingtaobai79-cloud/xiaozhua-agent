# e3 — 非 SSH 运行态观测通道盘点（P4b 步1；本地只读、0 网络）

> 采集时间: 2026-09-30T20:14Z（date -u 实测，UTC）
> 采集会话: implementer / P4b
> 目的: 在**不使用 SSH/kubectl** 前提下，逐项判定候选通道能否观测 SPI 运行态**加载链**
> 观测目标（P1 §5 加载链路，等级 VERIFIED_STATIC_BYTECODE）:
>   `SPIApplicationRunListener` / `SPIJarLoader` / `registerSingleton` / `SPIProviderRegisterEvent`
> 关联既有证据: e1（2026-09-22 配置面快照）、e2（2026-09-30 配置面新鲜复核）；本件只作通道盘点，不重复配置面取证。

## 0. 判据前提（措辞硬约束）
配置启用 ≠ 插件已加载 ≠ 实现被调用。运行态**加载链**是 JVM 内 Spring Boot 启动期行为（监听器→扫描→类加载→动态注册→事件广播），
其唯一直接可观测载体是**承载 boot-starter-spi 的平台进程的启动/运行日志**。任何 HTTP 业务面 / 配置面至多给出**旁证**，不能替代加载链日志。

## 1. 候选通道逐项盘点

### C1 网关只读端点（business / udc-runtime 面）
- 事实: `config/environments.yaml` L12–L14 `kind: gateway` / `gateway_base=https://lowcode-test2.example.com` / 前缀模板 `/service/{appId}`；L15 default_app_id=`app9000000000000000001`。
- 环境事实（直接引用）: 活体只读 `POST /udc-runtime/*` 可用；`GET /udc/*` 实测 404。
- 进程归属: 网关按 `/service/{appId}` 路由到**低代码应用运行时（UDC 业务处理）**，非承载 boot-starter-spi 的平台进程（ctp-user / cip-connector）。
- 能否观测加载链: **否**。udc-runtime 是业务数据面，不呈现 SPI 监听器/类加载/动态注册日志；即便命中 SSO 业务调用，也只证"某实现被调用"这一独立命题，且不等于加载链被观测，且 SSO 面需 `test2-web-credential`（token 有时效，本线未持有有效凭据）。
- 前提: 只读请求 0 凭据可达形态待 e4 探测坐实（预期 301/404/401，非加载链信息）。

### C2 Nacos 配置面（config 组）
- 事实: L76–L83 `mse-c19f9232` kind=aliyun-mse / port 8848 / protocol http / **readonly: true** / credential ref=`nacos-mse-credential`（仓库外，本线未持真值）。
- 已坐实: P2b e2 本地直连 `GET /nacos/v1/cs/configs?dataId=public&group=seeyon&tenant=xiaozhua-test2` → 200（0 SSH、0 凭据），`seeyon.spi.enable=true`、`spi-plugins`/`spiPlugins` grep **0 命中**。
- 能否观测加载链: **否**。属**配置面**，只证开关与（缺失的）插件清单声明，不证运行态加载被执行（main 门4/P2b 已定性）。**本线禁再触碰 spi-ext-live.md 已覆盖的配置面主张（同格两审=禁循环）。**

### C3 Nacos 命名 / 服务注册面（naming 组，运行态语义）
- 假设: Nacos 除 config 组外有 naming 组（`/nacos/v1/ns/...`），登记**服务实例存活/健康**，属运行态语义（比配置面更接近"服务在跑"）。
- 能否观测加载链: **仅到"服务实例存活"粒度，仍不证 SPI 加载链**。即使见 ctp-user/cip-connector 实例在线，也推不出 SPI 插件已加载（无 spi-plugins 声明 → 加载链可能短路；推断源=P1 VERIFIED_STATIC_BYTECODE）。
- 前提: 与 config 组同 host:8848；是否 0 凭据可达、命名空间是否可枚举 ⇒ 由 e4 探测坐实（只读 GET）。

### C4 在盘审计件 / 日志快照（docs/audit/**，他线面）
- 本地只读检索（0 网络，2026-09-30T20:14Z）关键串命中计数:
  - `SPIApplicationRunListener` = 0；`SPIJarLoader` = **1**；`registerSingleton` = 0；`SPIProviderRegisterEvent` = 0；`spiPlugins` = 0；`spi-plugins` = 0。
- 唯一命中件: `<XIAOZHUA_AGENT_ROOT>/docs/audit/udc-gateway-and-capability-boundary-evidence.md`（他线能力边界件，属**静态/设计面**字样提及，**非 test2 运行态日志快照**）。
- 能否观测加载链: **否**。①为历史/静态件、非新鲜运行态观测；②`docs/audit/**` 属他线面，本线**禁改**、**禁取其中真值使用**；③未见任何 test2 运行态 SPI 加载/注册日志行。

### C5 其它不需 SSH 的替代路径（actuator / metrics / 健康）
- 候选: Spring Boot actuator（`/actuator/health`、`/beans`）、Prometheus `/metrics` 经网关暴露。
- 能否观测加载链: **不确定，倾向否**。`/beans` 理论上可见 SPI 实现 bean 是否注册（若平台应用对外暴露 actuator）；但此类端点是否经网关对 `/service/{appId}` 暴露、是否需鉴权，均未在 config/既证事实中登记，属未坐实假设。**不盲探未登记的 URL 形态**（no_retry_bombing + 禁猜测端点）；如 main 认定值得单独探测，可在后续单边界授权下以有界 GET 验。
- 前提: 需已知可读端点，本线无。

## 2. 盘点结论（步1 产出，先于探测）
- 能直接观测 **SPI 运行态加载链**（监听器/类加载/动态注册/事件）的通道 = **仅 test2 平台进程日志**（SSH/kubectl → ns=lowcode-test 的 ctp-user / cip-connector pod logs）。该通道在 P4a 被 SSH host-key 阻塞，**属需人工解阻**，非本线可绕。
- C1/C2/C4 明确**不能**观测加载链；C3 至多给"服务存活"旁证、**不证加载链**；C5 未坐实、本线不盲探。
- 故本步先行判定: **不存在"非 SSH 且能观测 SPI 加载链"的现成通道**。步2 仅对 C1/C3 发**有界只读探测**以坐实可达形态（非为翻案，为把"不可得"落成实测负结果，而非断言）。
- Verified 面据实预置为"**未达成/待探测**"（见 spi-ext-runtime.md §9）；探测结果与负结果事实落 e4 与 §8/§9。

## 3. 凭据与边界声明
- 全程 0 凭据入件：username/password/token/artifactory URL 一律 `<REDACTED>` 或仅键名。C1/C2 若需凭据而缺 ⇒ 记"通道不可得（缺凭据）"并停，**不从 docs/audit/** 他线件取真值**。
- 本件仅新增于 `core/facts/spi/evidence/live/`，未触碰 spi-ext-live.md、P1 冻结三件、e1/e2、INDEX/STATUS、docs/audit/**。
