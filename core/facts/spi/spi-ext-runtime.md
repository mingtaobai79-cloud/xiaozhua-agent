# SPI-EXT-RUNTIME-01 — 非 SSH 通道对 test2 运行态 SPI 加载/调用的可观测性（P4b 事实格）

> 事实格 ID: SPI-EXT-RUNTIME-01
> 建模口径: SPI 扩展点/插件契约/实现边界（不按 UDC 模式套）
> 本格主张: 判定"不使用 SSH/kubectl 的前提下，是否存在可观测 test2 运行态 SPI **加载链/调用**的通道"；可得则取证，不可得则把"不可得"坐实为**负结果事实**。
> 关联冻结格: `spi-ext-registration.md`(SPI-EXT-REG-01)、`spi-ext-loading.md`(SPI-EXT-LOAD-01) —— 观测目标合法性来自 P1 §5 加载链路（VERIFIED_STATIC_BYTECODE）
> 关联格: `spi-ext-live.md`(SPI-EXT-LIVE-01) —— 配置面 LIVE 证据；**本格禁重复/改动其配置面主张（同格两审=禁循环）**
> 阶段: P4b（新格）

## 1. Capability
主张能力: 在 0 SSH / 0 写面前提下，盘点并实测候选通道对 SPI 运行态**加载链**（`SPIApplicationRunListener` / `SPIJarLoader` / `registerSingleton` / `SPIProviderRegisterEvent`）及"实现被调用"的可观测性，并据实给出通道结论。
主张边界: 仅登记**实际观测到**的通道形态/响应；配置启用 ≠ 插件已加载 ≠ 实现被调用；通道不可达 ≠ 运行态未发生（不可达是探测面问题，非被测系统事实）。

## 2. Version
- 观测目标环境: `test2`（网关 `lowcode-test2.example.com`；Nacos `mse-c19f9232` tenant=seeyon-test2 group=seeyon）。
- `udc_image_version: "5.3.496"`（environments.yaml L16）——与本地 5.3.517 为两证据单元；对 P1 客户声明 3.10.1 的适用性仍 UNVERIFIED（承 P1 §4.5 缺口）。
- 采集时间: 2026-09-30T20:14Z（date -u，UTC，见 e3）；探测时间戳见 e4。

## 3. Input
- 观测面清单（本地只读盘点，见 e3）: C1 网关 business/udc-runtime、C2 Nacos config 组、C3 Nacos naming 组、C4 在盘审计件/日志快照(docs/audit/**, 他线面)、C5 actuator/metrics 类未登记端点。
- 输入源: `config/environments.yaml`（键引用，值不入件）、e1/e2（配置面既有证据，仅引用不重取）。

## 4. Required
- 来自 P1 §5（VERIFIED_STATIC_BYTECODE）: `SPIProperties.spiPlugins` 默空 → `initialize()` 遇空即 return（加载链短路，不加载任何插件 jar）。
- 故"运行态加载链被执行"的直接观测必要载体 = **承载 boot-starter-spi 的平台进程（ctp-user/cip-connector）启动/运行日志**；该载体仅 SSH/kubectl 可得（P4a 阻塞）。

## 5. Execution
1. 步1 盘点（0 网络）→ e3。
2. 步2 有界只读探测（硬上限 3 发，全 GET、0 凭据）仅对 C1/C3 发；逐发记 UTC 时间戳/端点/请求形态/响应摘要 → e4。
3. 步3 3 发无加载链命中 ⇒ 登记负结果事实，停；禁扩 SSH、禁绕 host key、禁开写面。
- 判级四类分写: LIVE PASS / 已调用但业务数据未验证 / 明确问题 / 未测试；HTTP 200 或空结果不算 PASS。

## 6. Side Effects
- 全只读（GET），0 写；无 zzprobe 应用创建、无 jar 上传、无 Nacos 改配、无 SSH、无 kubectl。
- 凭据 0 入件: username/password/token/artifactory URL 一律 `<REDACTED>` 或仅键名；缺凭据即记"通道不可得（缺凭据）"并停，不从 docs/audit/** 他线件取真值。

## 7. Known Constraints
- **本格不含 SSH 通道结论**（SSH/kubectl 运行态日志面属 P4a，需人工解阻，非本格范围）。
- 配置启用 ≠ 部署成功 ≠ 运行态被调用（承 P1/live 约束）。"未加载"若由空 spi-plugins 推断，**推断源 = P1 VERIFIED_STATIC_BYTECODE**（`spiPlugins` 空即 return），非运行态直接观测。
- 通道不可达 / 缺凭据 = 探测面事实，不得写成"test2 未加载 SPI 插件"的系统事实。
- 覆盖面缺口: naming 面即使可得，也仅"服务实例存活"粒度，**不证 SPI 加载链**。

## 8. Evidence
- `core/facts/spi/evidence/live/e3-runtime-channel-inventory-20260930.md` — 通道盘点（2026-09-30T20:14Z 本地只读；加载链关键串在 docs/audit 命中: SPIJarLoader=1(他线静态件)、余=0；spi-plugins=0）。绝对路径 core/facts/spi/evidence/live/e3-runtime-channel-inventory-20260930.md（6114B）；sha256=edecde915832a270689c8017d7f148b5fe846d67d8f99bea75434ab076b60b2d；落盘 `date -u` 实测 2026-09-30T20:14Z。
- `core/facts/spi/evidence/live/e4-runtime-probe-nonssh-20260930.md` — 步2 有界探测逐发记录（3 发 GET / 0 凭据 / UTC 时间戳 / 响应）。结果: P1 网关根 TLS 中断(exit 35, 20:20:41Z)、P2/P3 Nacos naming `/ns/service/list` 连接重置(exit 56, 20:20:42Z)——**3 发皆传输层失败，无 HTTP 200 正文、无加载链命中**。绝对路径 core/facts/spi/evidence/live/e4-runtime-probe-nonssh-20260930.md（3113B）；sha256=49e771d507d39c606c9f61d6e19a84b0e8fb628ceb252954dedab1520fe75e41；探测 3 发 `date -u` 实测 2026-09-30T20:20:41Z（P1）/2026-09-30T20:20:42Z（P2、P3）。
- 关联既有: e1(3594B/7f6d7f52…)、e2(2493B/f3d6639e…)（配置面，**本线禁再触碰**）。

## 9. Verified
- 判级（四类分写，步2 后据实）:
  - 运行态 SPI 加载链（监听器/类加载/动态注册/事件）= **未测试**（直接载体=平台进程日志属 SSH/kubectl 面，P4a 阻塞，**本格不含 SSH 通道结论**）。
  - 网关 business/udc-runtime（C1）= **明确问题（通道不可达，TLS 中断 exit 35）**；即便可达亦不呈现加载链（e3 §C1 判定）。
  - Nacos naming 服务实例存活（C3）= **明确问题（连接重置 exit 56）**；且属旁证粒度，**不证 SPI 加载链**。
  - 无任一探测获 HTTP 200 正文 ⇒ 不存在 200/空结果冒充 PASS。
- 已证（盘点+探测层面）: 无"非 SSH 且能直接观测 SPI 加载链"的现成通道（e3 逐项判定）；本会话 3 发只读探测均传输失败（e4）。
- 未证 / UNVERIFIED: 运行态 SPI 加载链正/负向命中 = **未获取**。
- **负结果事实（据实登记，非断言系统未加载）**: 非 SSH 只读通道不足以观测 test2 运行态 SPI 加载链；**G2 运行态子面仍未达成，需 P4a 人工解阻**（可信 host key / 可信 kubeconfig 后 kubectl logs grep，硬上限 3 发）。
  - 传输层不可达属**探测面事实**，不得写成"test2 未加载 SPI 插件"的系统事实；"未加载"只能由 P1 VERIFIED_STATIC_BYTECODE（spiPlugins 空即 return）作**推断**，非观测。
- 本节等级 = 实际观测等级（未高于）。G2 运行态 LIVE **未达成 → 禁写终态**。

## 10. 通道状态登记（OBSERVATION）
- 步1: 达成（e3 落盘，可独立审计）。
- 步2: 达成（e4，3 发只读 GET，硬上限内，0 凭据，未重试）；均传输层失败，无加载链证据。
- 步3: **停**（负结果事实已登记）。未扩 SSH、未绕 host key、未开写面。
- 待 main: ①P4a 人工解阻后单独重派运行态日志面；②如判定需写面（部署 zzprobe SPI jar 触发调用）才能推进 G2 运行态子面 → 本线**仅提设计方案、不动手**，设计方案见 RESULT 附报，等 main 批准。

## 11. P5 有界只读复测追加段（2026-10-03；只追加，§1–§10 既有判级零改写）
- 采集时点: `date -u` 实测 2026-10-03T08:43:07Z / 08:43:08Z（UTC）；证据件 `core/facts/spi/evidence/live/e5-runtime-probe-recheck-20261003.md`。
- 探测形态: 3 发硬上限、全 GET、0 header 凭据、0 body、0 重试；逐发（含 DNS/TCP/TLS/HTTP 层级、正文摘要、CURL_EXIT、traceId）见 e5。
  - P1 `GET https://lowcode-test2.example.com/` → **TLS 成功 + HTTP 301 / 162 B（nginx 重定向页）**，CURL_EXIT=0 ⇒ §9 所记「网关 TLS 中断 exit 35」在本次复测**不复现**（探测面时点差，非被测系统结论）。
  - P2 `GET /service/{appId}/udc-runtime/datatype/getAll` → **HTTP 200 / 514 B / `code=BOOT_1006` / `traceId=3258152084922434331`**；`data.content.redirectUrl` 取值含鉴权参数，凭据 0 入件故不落文 ⇒ **明确问题（0 凭据撞 SSO 鉴权墙）**；HTTP 200 与空结果均不算 PASS。
  - P3 `GET /login/third-auth/code` → **HTTP 200 / 7405 B（前端 SPA 壳，含 `/custom-extensions/pc_extensions.js` 静态引用）** ⇒ **未测试**（SPI 实现 `TemplateSsoServiceImpl` 调用需有效 test2 会话凭据，本线未持有、未取用）。
- 判级（本段新增观测，不回改 §9/§10 文字）:
  - 运行态 SPI **加载链** = **仍未观测**；3 发均无 SPI 可归因响应 ⇒ **不记 LIVE**。
  - C1 网关通道状态 = 由「不可达（exit 35）」更新为**可达（301 / 200）**；可达性属**探测面事实**，不升级为 LIVE，亦不据以推翻 e3 §C1「udc-runtime 为业务数据面、不呈现 SPI 加载链」判定。
  - **G2 运行态 LIVE 仍未达成**。所缺人工门: ①可信 host key / 可信 kubeconfig（P4a）→ 平台进程 pod 启动日志；②`test2-web-credential` 有效会话 → SPI SSO 提供方调用面。二者本线均不自决、不绕行。
- 边界: 0 SSH、0 kubectl、0 host-key 绕过、0 凭据构造、0 写面、0 既有测试改动、0 重试；未触碰 e1–e4、`hashes/evidence-inventory.sha256.txt`、`INDEX.md`、`docs/audit/**`、`components/`、`core/tools/`、`adapters/`、`tests/`、CLI/bootstrap；本段仅尾部追加，§1–§10 前序字节零改动。

## 12. §Verified 追加｜P6 认证态只读差分探测（2026-10-03T12:03Z，evidence/live/e6-auth-sso-dispatch-probe-20261003.md）
- 观测: `GET /login/third-auth/template` 与 `GET /login/third-auth/zznone9x7q`（Cookie 三键按
  `test2-web-credential.json` 模板填充；凭据剩余 ≈23.8 h 有效，实测 `expires_epoch` vs `date +%s`）
  各 1 发，HTTP 200 / 7405 B / `ETag: E8E8185E…8168` 两发一致，`x-oss-*` 头族表明响应由 OSS 前端静态对象呈现。
- 事实: 已注册 SPI 提供方名（`getName()`→`"template"`，源=§5/§6 冻结契约）与未注册名
  **响应不可区分** ⇒ 该端点族的 GET 形态不体现服务端按 SPI 提供方名查表，请求未进入承载
  `boot-starter-spi-customized` 的应用进程；亦与 §P3（e5，0 凭据）命中同一静态对象。
- 判级: **LIVE PASS=无**；`/login/third-auth/{name}` 登记为「明确问题（只读观测点不成立）」——
  后续 SPI 调用面取证不再复用此路径。
- 边界: 2 发 / 上限 3；0 重试、0 写面、0 SSH、0 kubectl；残留 1 发主动不用（盘上无登记来源的
  SPI 可归因只读服务端端点）。
- 口径: 本追加**不改动** §1–§11 既有判级，亦不推翻 `e3` §C1；HTTP 200 与静态壳不算 PASS 的纪律保持。
## 13. 运行态插件加载面复测（2026-10-04，本线）

- 本线复测: `date -u` 2026-10-04T03:52:06Z，本机 OpenSSH → test2 中间服务器 → 远端 `kubectl --kubeconfig=configtest2`（全只读）。批1 返回 `Host key verification failed.`，会话未建立 ⇒ 远端 `ls -l` / `sha256sum` / `unzip -p` / `jar tf` 均未执行，本线 0 远端输出；批2/批3 依赖同一通路，未执行。0 host-key 绕行、0 重试、0 写面、0 HTTP 探测。
- 判级: **LIVE PASS（本线）= 0**。运行态加载面证据（插件 jar 落盘 `/root/appdata/ctp-user/mvn/com/seeyon/cip-spi-user-sso-sample/2.0.0/cip-spi-user-sso-sample.0.0.jar` 14686 B、落盘 mtime 与容器启动同刻、同目录 `_remote.repositories` + `.sha1`；扩展点注册对 `com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService=CHNsSsoAuthProviderService`）现存等级 = **运行态证据·未经本线复现**（观测者=主控代跑；逐条溯源见 e7 §2，引 `main/HUMAN-PROBE-P7-raw-evidence-20261003.md` 2961B/`4c9af39a…2ba1` 之 §5/§6，未冒充本线观测）。
- 归因推断（非直接观测）: 「落盘由 SPI 框架 maven 通道于启动时完成」= 推断级；支撑 = P1 VERIFIED_STATIC_BYTECODE（`SPIJarLoader` / `SpringDynamicRegister` / 配置键 `seeyon.spi.spi-plugins`）+ e1/e2 Nacos 配置 LIVE。
- 提供方调用面（SSO 真实登录流转）= **未测试**（需交互/会话凭据授权，本批 0 尝试）。
- 负向口径: 本线 0 输出、运行日志 0 命中（启动段已轮转）均属观测面/入口事实，禁读作「test2 未加载 SPI 插件」的系统事实；HTTP 200/空结果不算 PASS 的口径延续。
- 证据锚: `evidence/live/e7-runtime-plugin-load-retest-20261004.md`。
## 14. P7b 本线复测追加段（2026-10-04；补充批次·非新阶段；只追加，§1–§13 既有判级零改写）
- 采集时点（`date -u`）: 批0 本地预检 + 批1 实连 2026-10-04T04:12:29Z；证据件 `core/facts/spi/evidence/live/e8-runtime-plugin-load-blocked-20261004.md`（6622 B / sha256 `30b0ff5261443a6d8537075fc1dcc95b6d9d7f30f641a25c01e09e3486217e1f`）。
- 批0 预检（0 网络 / 0 SSH 连接 / 0 远端命令）: `ssh -G <test2 中间服务器>` 之 `userknownhostsfile` = 本线执行用户 HOME 下的 `.ssh/known_hosts`；该文件 **1110 B / 5 行**；`ssh-keygen -F <test2 中间服务器>` **rc=0 命中 ssh-ed25519 锚**（found line 1）。⇒ 锚在本线读取路径内且字面一致 ⇒ 判「命中·进批1」。
- 批1 实连（决定性）: `ssh -i <pem 相对路径> -o BatchMode=yes -o ConnectTimeout=20 <test2 中间服务器> … kubectl --kubeconfig=configtest2 exec …`；**ssh 客户端退出码数值=255**（先取到变量再处理输出，未让 `$?` 落 sed/管道），输出 `Host key verification failed.`；会话未建立 ⇒ **远端退出码未取得**、`ls -l`/`sha256sum`/`unzip -p`/`jar tf` 均未执行 ⇒ 本线 **0 pod 名 / 0 字节数 / 0 mtime / 0 sha / 0 注册对**；批2/批3 依赖同一通路，未执行。
- 是否复现原料 §5/§6（14686 B、mtime=容器启动同刻、注册对行 `CtpUserSsoAuthProviderService=CHNsSsoAuthProviderService`）: **未复现**（本线 0 直读，无一致/不一致可判）；方向与 e7 §2「本线未复现」一致，未据此改写 e7。
- 判级（本线口径，按预案不自行升降级）: **LIVE PASS（本线）= 0**；运行态加载面证据等级 = **维持** e7 所记「运行态证据·未经本线复现」（观测者=主控代跑），不下调为静态、不上调为 LIVE。「落盘由 SPI 框架 maven 通道完成」仍为**归因推断**（支撑链 P1 `VERIFIED_STATIC_BYTECODE` `SPIJarLoader`/`SpringDynamicRegister`/配置键 `seeyon.spi.spi-plugins` + e1/e2 Nacos LIVE）；提供方调用面 = **未测试**。
- 关键差异登记（本批新增事实）: 批0「锚可见且 `-F` 命中」与批1 实连 rc=255「`Host key verification failed.`」**并存** ⇒ 记为**明确问题（本线 SSH 观测入口不成立）**，属取证面/入口事实，**非被观测系统的负事实**；不得读作「test2 未加载 SPI 插件」，亦不得据本线 0 输出立系统结论。
- 边界: 0 host-key 绕行（未加任何 host-key 相关 `-o` 参数、未 `ssh-keyscan`、批0 仅只读查询）、0 重试（止于 rc=255）、0 写面、0 HTTP 探测、0 既有测试改动；未触碰 e1–e7、`INDEX.md`、`evidence/hashes/evidence-inventory.sha256.txt`、`STATUS.md`、`components/`、`core/tools/`、`adapters/`、`tests/`、CLI/bootstrap、`docs/audit/**`；§1–§13 前序字节零改动（纯追加，自证见 RESULT）。

## 15. 运行态插件加载面·本线复测直读（2026-10-04，ASCII 通路修复后）

- 通路: 纯 ASCII 本地路径下、主控背书的同一把已核验 ED25519 锚 + 逐字节同一的 pem；三次 ssh 连接的本地客户端退出码数值均=**0**（0 host-key 放宽变体、0 keyscan、0 known_hosts 写、0 换主机/换跳板、0 重试）。§14 保留为 ASCII 修复前记录，其结论由本节新观测承接。
- 观测对象: pod `ctp-user-cb67d55f9-jxdnr`（1/1 Running，restartCount=0，AGE 13d），容器 `ctp-user`；namespace 由 `configtest2` context 决定。
- **LIVE PASS（本线复现·加载面）**:
  - 插件 jar `/root/appdata/ctp-user/mvn/com/seeyon/cip-spi-user-sso-sample/2.0.0/cip-spi-user-sso-sample.0.0.jar` = **14686 B**，sha256 **`112f573fcc65cf6b2bc596f745410081bd145267dfa28cdd96a5d627ce7b9968`**，mtime=2026-04-16 16:13:39，ctime=2026-09-20 23:52:11。
  - 注册对（`unzip -p <插件 jar> META-INF/spring.factories`，远端 rc=0）: `com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService` = `com.seeyon.cip.spi.user.auth.bccastlens.CHNsSsoAuthProviderService`。
  - 运行 boot jar `BOOT-INF/lib`（`jar tf`，远端 rc=0）: `boot-starter-spi-5.3.358.jar` + `boot-spi-5.3.260.jar`。
  - 上述三项与 HUMAN 原料（会话根相对 `main/HUMAN-PROBE-P7-raw-evidence-20261003.md`）§5/§6/§1 取值**一致**。
- **明确问题 A（一致性硬规则触发·落盘时刻归属）**: 原料 §5 表述「mtime=容器启动同刻」本线不可复现——jar mtime=2026-04-16 16:13:39（与原料所载 jar 内 pom Last-Modified 同日），落盘时刻由 jar **ctime**=2026-09-20 23:52:11（=目录与 `_remote.repositories` 的 mtime）记录，容器 startTime=2026-09-20T15:50:21Z（+08=23:50:21）⇒ 落盘晚于启动约 110 s。以不一致为事实登记。
- **明确问题 B（运行期日志观测窗口不成立）**: 加载链四串 `SPIApplicationRunListener` / `SPIJarLoader` / `registerSingleton` / `SPIProviderRegisterEvent` 在 `--since=48h --tail=200000` 窗口内命中 0（远端 grep rc=1）；0 命中不作「test2 未加载 SPI 插件」系统事实。与原料 §7 同向。
- **归因推断（非直接观测）**: 「落盘由 SPI 框架 maven 通道完成」支撑=P1 `VERIFIED_STATIC_BYTECODE`（`SPIJarLoader`/`SpringDynamicRegister`/配置键 `seeyon.spi.spi-plugins`）+ e1/e2 Nacos LIVE + 本线 `_remote.repositories` 192 B 与 `.jar.sha1` 40 B 同刻（23:52:11）落盘痕迹；拉取动作本身未被直读。
- **未测试**: 提供方调用面（SSO 真实登录流转）。**已调用但业务数据未验证**: 本批 0（0 HTTP 探测复用）。
- 工具面事实（不归入系统结论）: 容器为 BusyBox v1.31.1，`ls -l --time-style=long-iso` 不支持、`unzip -l` 对该 boot jar 报 `short read`（远端 rc=1）；本线以 `ls -la`+`stat -c`+`wc -c` 与 `jar tf` 取等价只读字段。
- 证据锚: `evidence/live/e9-live-plugin-drop-and-registration-20261004.md`（逐批命令形态脱敏稿、退出码数值、对照表、脱敏自查）；e7/e8 保留为本边界前序 BLOCKED 记录，未改写。
