# e9｜test2 运行态 SPI 插件落盘与注册对本线直读证据（2026-10-04）

性质: 运行态加载面证据件（本线直读）。承接 e7（同边界·ASCII 修复前 BLOCKED）与 e8（入口不成立记录）。

## 0. 元信息与通路
- 远端时钟 `date -u`: 批1=2026-10-04T04:32:09Z；批2=04:32:46Z；批3=04:33:36Z。
- 通路: 纯 ASCII 本地路径下、主控背书的同一把已核验 ED25519 锚 + 逐字节同一的 pem；命令形态 `ssh -i <pem> -o BatchMode=yes -o ConnectTimeout=20 -o UserKnownHostsFile=<ASCII known_hosts> <test2 中间服务器> '<只读远端命令>'`。
- 本地 ssh 客户端退出码数值: 批1=0、批2=0、批3=0（先取变量再处理输出，`$?` 未落 sed/管道）。远端退出码数值逐批见下。
- 会话计数如实: 3 次连接，均首次即回显，0 重发、0 通路重试、0 换主机/换跳板。host-key 放宽变体 0、`ssh-keyscan` 0、known_hosts 写/改 0。
- 观测对象: pod `ctp-user-cb67d55f9-jxdnr`（1/1 Running，RESTARTS=0，AGE 13d）；容器 `ctp-user`（显式指定，因该 pod 含 `one-pilot-initcontainer`）；namespace 由 `configtest2` context 决定（lowcode-test），本线未自行加 `-n`。
- 节点/地址类字段已脱敏（不落内网 IP 与内网节点主机名）。

## 1. 批1｜插件 jar 落盘直读（远端 rc=0）
命令形态（脱敏）: `… kubectl --kubeconfig=configtest2 get pods -o wide`（PG_RC=0）→ `get pod <POD> -o jsonpath={.status.startTime|restartCount}` → `exec -c ctp-user -- sh -c "sha256sum <GAV 目录>/*.jar; wc -c …; stat -c %y …; echo BATCH1_REM_RC=$?"`。
- `kubectl get pods` 远端退出码数值=0；pod `ctp-user-cb67d55f9-jxdnr` 定位成立。
- pod startTime = **2026-09-20T15:50:21Z**；containerStatuses[0].restartCount = **0**。
- 容器内对象路径: `/root/appdata/ctp-user/mvn/com/seeyon/cip-spi-user-sso-sample/2.0.0/cip-spi-user-sso-sample.0.0.jar`
  - 尺寸 = **14686 B**（wc -c 直读）
  - sha256 = **112f573fcc65cf6b2bc596f745410081bd145267dfa28cdd96a5d627ce7b9968**
  - mtime（`stat -c %y`，容器本地时区）= **2026-04-16 16:13:39.000000000**
- BATCH1 远端退出码数值=0。
- 命令形态适配（工具面事实）: HANDOFF 指定的 `ls -l --time-style=long-iso` 在容器 BusyBox v1.31.1 不支持（远端回显 `ls: unrecognized option`）；本线以 `ls -la` + `stat -c "%y / %z"` + `wc -c` 取等价字段（尺寸 / mtime / ctime），非换通路、非重试。

## 2. 批2｜注册对与 SPI 框架 jar 清单
- `unzip -p <插件 jar> META-INF/spring.factories`（容器内 unzip）远端退出码数值=0，直读两行（换行续接形式）:
  - `com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService=\`
  - `com.seeyon.cip.spi.user.auth.bccastlens.CHNsSsoAuthProviderService`
- `unzip -l /app/ctp-user-assemble.jar | grep boot-starter-spi` 远端退出码数值=**1**，回显 `unzip: short read`（BusyBox unzip 对该 fully-executable boot jar 读取失败；工具面事实，非系统负事实）。
- 同批改用静态源同形态 `jar tf /app/ctp-user-assemble.jar | grep -E "boot-starter-spi|boot-spi"` 远端退出码数值=**0**，直读命中:
  - `BOOT-INF/lib/boot-starter-spi-5.3.358.jar`
  - `BOOT-INF/lib/boot-spi-5.3.260.jar`
- 该次 exec 的 stderr 夹带一行 JVM agent 启动参数，内含第三方监控许可密钥串 ⇒ 本件不落真值（凭据 0 入件）。

## 3. 批3｜落盘时刻归属与运行期日志四串
- `ls -la <GAV 目录>` 远端退出码数值=0，目录项 3 个: `_remote.repositories` 192 B、`cip-spi-user-sso-sample.0.0.jar` 14686 B、`cip-spi-user-sso-sample.0.0.jar.sha1` 40 B；目录本身 4096。
- `stat -c "n=%n type=%F mt=%y ct=%z"` 远端退出码数值=0:
  - 目录: mt=2026-09-20 23:52:11 ct=2026-09-20 23:52:11
  - `.jar`: mt=2026-04-16 16:13:39 **ct=2026-09-20 23:52:11**
  - `_remote.repositories`: mt=2026-09-20 23:52:11 ct=2026-09-20 23:52:11
- 容器内 `date -u`=2026-10-04T04:33:36Z（时间戳字段为容器本地时区，+08）。
- 日志四串 grep（`SPIApplicationRunListener` / `SPIJarLoader` / `registerSingleton` / `SPIProviderRegisterEvent`，`logs -c ctp-user --since=48h --tail=200000`）⇒ 命中计数 **0**，grep 远端退出码数值=**1**。

## 4. 溯源对照（本线直读值 vs 原料取值 vs e7）
原料=会话根相对 `main/HUMAN-PROBE-P7-raw-evidence-20261003.md`（观测者=主控代跑，2026-10-03 20:4x +08）；只引条目号与取值，不转写全文。

| 项 | 原料锚 | e7 §2（ASCII 修复前） | 本线 e9 直读 | 一致性 |
|---|---|---|---|---|
| 插件 jar 尺寸 14686 B | §5 | 未复现 | 14686 B | 一致 |
| 插件 jar sha256 | §5 未记 | 未复现 | 112f573f…9968 | 本线新增值 |
| 落盘时间=容器启动同刻（mtime 表述） | §5 | 未复现 | jar mt=2026-04-16 16:13:39；jar ct=2026-09-20 23:52:11；startTime=2026-09-20T15:50:21Z | **不一致**（见 §5-A） |
| 注册对 `CtpUserSsoAuthProviderService=CHNsSsoAuthProviderService` | §6 | 未复现 | 两行全限定名同上 | 一致 |
| boot-starter-spi 在 `BOOT-INF/lib` | §1（5.3.358）+ boot-spi 5.3.260 | 未复现 | 5.3.358 / 5.3.260 两行 | 一致 |
| 日志四串 0 命中 | §7（75MB，仅存 10-04 02:52 之后） | 未复现 | 48h + tail 200000 窗口内 0（rc=1） | 一致（同属观测窗口限制） |

## 5. 判级（按 main 预裁预案照写；本线不自升降级、不自判达成、不写终态）
- **LIVE PASS（本线复现·加载面）**: 批1 落盘尺寸/mtime/ctime/sha256 + 批2 注册对内容与 `BOOT-INF/lib` 框架 jar 清单 ⇒ 本线远端直读成立，退出码数值逐批见 §1–§3。
- **明确问题 A（一致性硬规则触发）**: 原料 §5 以「mtime=容器启动同刻」表述；本线直读 jar **mtime=2026-04-16 16:13:39**（与原料同条所载「jar 内 pom Last-Modified 4-16」同日），而**落盘动作**由 jar **ctime=2026-09-20 23:52:11** 与目录/兄弟文件 mtime 记录；容器 startTime=2026-09-20T15:50:21Z（+08=23:50:21）⇒ 落盘晚于容器启动约 110 s，且「同刻」不能由 jar mtime 复现。该项以**不一致**为事实登记，不掩盖、不改写原料。
- **明确问题 B（观测窗口不成立）**: 加载链四串 0 命中（§3），启动段（09-20）不在现存日志窗口内，且无 previous 容器。0 命中不作「test2 未加载 SPI 插件」系统事实。
- **归因推断（非直接观测）**: 「落盘由 SPI 框架 maven 通道完成」——支撑=P1 `VERIFIED_STATIC_BYTECODE`（`SPIJarLoader` / `SpringDynamicRegister` / 配置键 `seeyon.spi.spi-plugins`）+ e1/e2 Nacos LIVE（`maven:com.seeyon,cip-spi-user-sso-sample,2.0.0`）+ 本线 `_remote.repositories` 192 B 与 `.sha1` 40 B 同刻（23:52:11）落盘痕迹。拉取动作本身未被本线观测。
- **未测试**: 提供方调用面（SSO 真实登录流转）。
- **已调用但业务数据未验证**: 本批 0（无 HTTP 探测；P5/P6 已证该路不成立，本批未复用）。
- 工具面事实（不归入系统结论）: BusyBox `ls --time-style` 不支持、`unzip -l` short read（rc=1），已按 §1/§2 换用等价只读命令形态。

## 6. 脱敏与禁改面自查
- 本件 0 内网 IP / 0 内网节点主机名 / 0 特权用户前缀真值 / 0 密钥文件绝对盘符 / 0 主机名字面 / 0 键内容 / 0 私钥块 / 0 口令·令牌·接口鉴权串真值 / 0 第三方监控许可密钥串。容器内数据路径、pod 名、GAV 坐标、类名属运行态对象，按 HANDOFF §七 保留。
- 写面自查: 仅新建本件 + `core/facts/spi/spi-ext-runtime.md` 尾部追加 `## 15.`；e1–e8、§1–§14、INDEX.md、STATUS.md、hashes/inventory、evidence/README.md、registration/loading/live、components/、core/tools/、adapters/、tests/、seeyon_cli.py、seeyon_host_bootstrap.py、docs/audit/** 均未触碰。
- 0 写观测面: 未建 zzprobe 应用、未上传 jar、未改 Nacos、pod 内 0 写/rm/重启/rollout；0 HTTP 探测复用；0 既有测试改动。
