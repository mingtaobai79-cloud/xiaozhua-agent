# e8｜test2 运行态 SPI 插件加载面·本线复测（P7b 补充批次，2026-10-04）

本件登记本线（implementer）补充批次复测：**批0 本地预检命中锚 → 批1 实连仍 `Host key verification failed.`（ssh 客户端 rc=255）→ 通路 BLOCKED**。本批未获得任何远端直读值，不构成新的 LIVE 证据。

## 0. 批0 本地预检（0 网络 / 0 SSH 连接 / 0 远端命令）
- 本线执行用户 HOME: 当前执行用户主目录（记为「本线执行用户 HOME」；不落用户名与绝对盘符）。
- ssh 客户端实际读取的 known_hosts（取 `ssh -G <test2 中间服务器>` 的 `userknownhostsfile` 字段，纯本地解析、未发起连接）: **本线执行用户 HOME 下的 `.ssh/known_hosts`**（同列另有 `.ssh/known_hosts2`，未参与命中）。
- 该文件: **存在**，**1110 B / 5 行**。
- `ssh-keygen -F <test2 中间服务器>`（对同一 userknownhostsfile）: **rc=0，命中**（`# Host ... found: line 1`），该行密钥类型 = **ssh-ed25519**。
- 判读: 锚在本线 ssh 客户端读取路径内、连接串与锚同字面 ⇒ 命中 ⇒ 进批1（未绕行、未改/写 known_hosts、未 ssh-keyscan）。

## 1. 批1（决定性：pod 定位 + 落盘尺寸/mtime/sha256）— 本线结果 = BLOCKED
- 采集时点（`date -u` 实测）: 2026-10-04T04:12:29Z（会话发起）。
- 命令（脱敏形态）: `ssh -i <pem 相对路径 skills/devops/seeyon-low-code-environment/low-code-test.pem> -o BatchMode=yes -o ConnectTimeout=20 <test2 中间服务器> 'date -u; POD=$(kubectl --kubeconfig=configtest2 get pods --no-headers | awk "/ctp-user/{print \$1; exit}"); kubectl --kubeconfig=configtest2 get pods -o wide | grep ctp-user; kubectl --kubeconfig=configtest2 exec "$POD" -- sh -c "ls -l --time-style=long-iso <GAV 目录 com/seeyon/cip-spi-user-sso-sample/2.0.0>/; sha256sum <插件 jar>; echo RREM_RC=$?"'`
- **ssh 客户端退出码数值（先取到变量再处理输出，未让 `$?` 落 `sed`/管道）: 255**。
- 客户端输出（全量一行）: `Host key verification failed.`
- **远端退出码数值: 未取得**（会话未建立，`kubectl`/`ls`/`sha256sum` 均未在远端执行）。
- 本线远端取值: **0 pod 名 / 0 字节数 / 0 mtime / 0 sha256 / 0 目录项**。
- 会话计数如实登记: 首次 `OUT=$(...)` 捕获但未回显（记 1 次会话发起，rc=255）；随后一次同形态再发以取回显（rc=255）。两次为同一通路、同一失败串；此后停止，不再重发。
- 合规: 未加任何 host-key 相关 `-o` 参数、未 `ssh-keyscan`、未读/写/改 known_hosts ⇒ **host-key 绕行 0**；重试 0（止于 rc=255）；写面 0；HTTP 探测 0；0 远端命令成功执行。

## 2. 批2 / 批3 — 未执行
- 批2（注册对 `unzip -p spring.factories` + boot-starter-spi 清单 `jar tf`）、批3（运行期日志加载链 grep）依赖同一 SSH 通路；通路不成立 ⇒ 无观测面 ⇒ **未执行**（0 尝试、0 输出）。

## 3. 是否复现原料 §5/§6 与 e7 §2 对照表
- **未复现**（本线 0 直读）: 插件 jar 尺寸 14686 B、落盘 mtime=容器启动同刻、注册对行 `com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService=CHNsSsoAuthProviderService` ⇒ 三项本线均无读取，无一致/不一致可判。
- e7 §2 对照表所列「主控代跑观测」各条目，本线仍全部为「未复现」，与 e7 结论方向一致（同为通路 BLOCKED，非系统事实）；本批不改写 e7。

## 4. 对原料与 e7 的溯源引用（引路径+sha+条目号；禁整篇转写冒充本线观测）
- 原料: `main/HUMAN-PROBE-P7-raw-evidence-20261003.md`（**2961 B** / sha256 `4c9af39a40d6277c616d2f5675267c31e7beea6ebd7b11f4e1725b3f446b2ba1`）— §5（插件 jar 落盘事实）、§6（扩展点→实现注册对）为本批欲复现而未得的目标条目；观测者 = 主控代跑，非本线。
- e7: `core/facts/spi/evidence/live/e7-runtime-plugin-load-retest-20261004.md`（**7628 B** / sha256 `a9a2926c88ee15a25475b7c9a6d27f50199a85bc43f821ff81423816a195c8f5`）— §2 逐条对照表、§3 四类判级为本批前置记录；本批不触碰 e7。

## 5. 判级（本线口径；按预案不自升降，四类分写）
- **LIVE PASS（本线）= 0**。本线无任何远端直读输出，不得记 LIVE。
- **明确问题 = 本线 SSH 观测入口不成立**（`Host key verification failed.`，ssh 客户端 rc=255）。关键诊断对照: 批0 显示锚在本线 ssh 客户端读取的 known_hosts 内且 `-F` 命中，但实连仍拒 ⇒ 属**取证面/入口事实**，**非被观测系统的负事实**；不据本线 0 输出立「test2 未加载 SPI 插件」或「通路不可用」这类系统结论。
- **运行态加载面证据等级 = 不下调、不上调**: 维持 e7 所记「运行态证据·未经本线复现」（原料 §5+§6，观测者 = 主控代跑）。本批未新增任何本线直读值。
- **归因推断（禁写成直接观测）**: 「落盘由 SPI 框架 maven 通道于启动时完成」= 推断级；支撑链 = P1 `VERIFIED_STATIC_BYTECODE`（`SPIJarLoader` / `SpringDynamicRegister` / 配置键 `seeyon.spi.spi-plugins`）+ e1/e2 Nacos 配置 LIVE。
- **提供方调用面（SSO 真实登录流转）= 未测试**（需交互/会话凭据授权，本批 0 尝试）。
- 负向口径守住: 本线 0 输出、批2/批3 未执行、任何 0 命中一律不得读作被观测系统的负事实；HTTP 200/空结果不算 PASS 口径延续（本批 0 HTTP）。

## 6. 本批所缺（本线不可自决）
- 一条对本线 ssh 客户端**实际握手可用**的通路: 批0 已证锚在读取路径内并命中，但实连 rc=255。落锚/信任链修复权 = 主控，不在三角色；本线不绕行、不改写 known_hosts、不 keyscan。补齐后最小复测 = 批1+批2 两批即可以本线直读值定级。

## 7. 边界自查
- host-key 绕行 0（未加 `-o StrictHostKeyChecking=no` / `-o UserKnownHostsFile=/dev/null`、未 ssh-keyscan；批0 仅只读 `-F`/`ssh -G`/读文件字节行数）；重试 0；写面 0；HTTP 探测 0；既有测试改动 0。
- 禁改面零触碰: e7、runtime §1–§13、INDEX、e1–e6、inventory、STATUS、`components/`、`core/tools/`、`adapters/`、`tests/`、CLI/bootstrap、`docs/audit/**`。
- 凭据/脱敏: 本件 0 口令类/密钥类/令牌类/接口鉴权串/私钥块文本、0 特权用户前缀连接串、0 内网地址段、0 绝对盘符与密钥主机路径；known_hosts 表述为「本线执行用户 HOME 下的 known_hosts」；主机串以 `<test2 中间服务器>` 代。
