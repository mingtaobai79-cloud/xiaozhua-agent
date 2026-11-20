# e7｜test2 运行态 SPI 插件加载面复测（2026-10-04）+ HUMAN 代跑原料溯源引用

- 本线采集时点: `date -u` = 2026-10-04T03:52:06Z（发起与失败同秒返回）
- 本线采集方式: 本机 OpenSSH → test2 中间服务器 → 远端 `kubectl --kubeconfig=configtest2`（`configtest2` 属远端主机文件，本机不存在；namespace 以该 context 为准 = `lowcode-test`，未自行追加 `-n low-code`）
- 面: 全只读（`get pods` / `get pod -o jsonpath` / `exec -- ls -l` / `exec -- sha256sum`）；0 写面、0 HTTP 探测、0 重试
- **本线结果: 批1 即被 SSH host key 校验拒绝，未获得任何远端输出 ⇒ 本线未独立复现插件落盘事实**

## 1. 本线逐批记录

### 批1（决定性：pod 定位 + 插件落盘尺寸/mtime/sha256）
命令（脱敏形态，单条会话内链式只读）:

```
ssh -i skills/devops/xiaozhua-low-code-environment/low-code-test.pem \
    -o BatchMode=yes -o ConnectTimeout=20 <test2 中间服务器> \
  'date -u; POD=$(kubectl --kubeconfig=configtest2 get pods -o name | grep ctp-user | head -1);
   kubectl --kubeconfig=configtest2 get pods -o wide | grep -E "NAME|ctp-user";
   kubectl --kubeconfig=configtest2 get $POD -o jsonpath="{.status}|...";
   kubectl --kubeconfig=configtest2 exec $POD -- sh -c
     "ls -l --time-style=long-iso /root/appdata/ctp-user/mvn/com/seeyon/cip-spi-user-sso-sample/2.0.0/;
      sha256sum /root/appdata/ctp-user/mvn/com/seeyon/cip-spi-user-sso-sample/2.0.0/cip-spi-user-sso-sample.0.0.jar"'
```

- UTC 时点: 2026-10-04T03:52:06Z
- 远端命令退出码: **未取得**（SSH 会话未建立，`kubectl` / `ls` / `sha256sum` 均未在远端执行）
- 客户端输出（全量，原文一行）: `Host key verification failed.`
- 本机可见字段的取值: 无（0 字节数 / 0 mtime / 0 sha / 0 pod 名 / 0 容器路径读取）
- 记录口径缺陷（如实）: 该发命令输出经 `sed` 脱敏后管道，`$?` 取到的是 `sed` 的 0 而非 ssh 客户端退出码数值；按「0 重试」纪律未重发，故 ssh 客户端退出码数值本线未取
- 合规自查: 未加 `-o StrictHostKeyChecking=no`、未加 `UserKnownHostsFile=/dev/null`、未使用 `ssh-keyscan`、未读/未写/未改 `known_hosts` ⇒ **host-key 绕行 = 0**；未重试 = 0

### 批2（注册对 + boot-starter-spi 清单）
**未执行** —— 与批1 依赖同一 SSH 通路，通路不成立即无观测面。0 次尝试、0 输出。

### 批3（运行期日志加载链 grep，可选批）
**未执行** —— 同上。注：主控代跑原料已记该面启动段被日志轮转冲掉（负向命中），与本线结果相互独立。

## 2. 对 HUMAN 代跑原料的溯源引用（非本线观测，禁冒充）

- 原料件: `main/HUMAN-PROBE-P7-raw-evidence-20261003.md`（**2961 B** / sha256 `4c9af39a40d6277c616d2f5675267c31e7beea6ebd7b11f4e1725b3f446b2ba1`）
- 原料采集时点: 2026-10-03 20:4x +08（= 2026-10-03 12:4xZ 量级），执行者 = 主控用户（pem ACL 修复后由本机直连代跑）
- 引用方式: 仅引条目号与关键取值，未整篇转写；下表数值一律归属「主控代跑观测」，非本线 LIVE

| 原料条目 | 内容（引述要点） | 本线复现状态 |
|---|---|---|
| §目标 | pod `ctp-user-cb67d55f9-jxdnr`（1/1 Running，13d，namespace 由 `configtest2` context 决定） | 未复现（0 输出） |
| §1 | `/app/ctp-user-assemble.jar`（219MB Spring Boot fully-executable）BOOT-INF/lib 含 `boot-starter-spi-5.3.358.jar` + `boot-spi-5.3.260.jar` | 未复现 |
| §2 | boot-starter-spi `META-INF/spring.factories` = `EnableAutoConfiguration=com.seeyon.boot.starter.spi.SPIAutoConfiguration`；类清单含 `SPIApplicationRunListener.class` / `SpringDynamicRegister` / `plugin/CustomizedSpiInfo` | 未复现 |
| §3 | jar 内 README 配置键 `seeyon.spi.enable` + `seeyon.spi.spi-plugins`（支持 `maven:`/`file:`/`oss:` 三种 GAV 形态） | 未复现 |
| §4 | Nacos 实配（tenant=xiaozhua-test2, dataId=ctp-user, group=seeyon, 793B）: `authenticationType: spisso`；`spi: spi-plugins: - maven:com.seeyon,cip-spi-user-sso-sample,2.0.0` | 未复现（本批未走该面） |
| **§5** | 插件 jar 落盘 = 容器内 `/root/appdata/ctp-user/mvn/com/seeyon/cip-spi-user-sso-sample/2.0.0/cip-spi-user-sso-sample.0.0.jar`，**14686 B**，jar 内 pom Last-Modified 4-16，落盘 mtime 9-20 23:52（= 容器启动同刻），同目录含 `_remote.repositories`、`.sha1`；**原料未记 sha256 数值** | **未复现**（尺寸/mtime/sha256 三项本线均 0 读取） |
| **§6** | 插件 jar 内 `META-INF/spring.factories` = `com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService=CHNsSsoAuthProviderService`；实现类 `com/seeyon/cip/spi/user/auth/bccastlens/CHNsSsoAuthProviderService.class` | **未复现**（注册对行本线 0 读取） |
| §7 | 运行期日志 75MB 仅存 10-04 02:52 之后，grep `spi` / `SPIApplicationRunListener` = 0 命中（启动段已轮转，无 previous 容器） | 未复现（批3 未执行）；与原料同为负向命中面 |

## 3. 判级（四类分写；口径按预案，不自升降级）

- **LIVE PASS（本线）= 0**。本线无任何远端直读输出，不得记 LIVE。
- **运行态证据·未经本线复现 = 原料 §5 + §6**（插件 jar 落盘于运行容器文件系统：尺寸 14686 B / 落盘 mtime 与容器启动同刻 / 同目录 `_remote.repositories` + `.sha1`；扩展点→实现注册对 `CtpUserSsoAuthProviderService=CHNsSsoAuthProviderService`）。该面为「加载面·运行态痕迹」，观测者为代跑通道，本线复测未成立，故等级不下调为静态、也不上调为 LIVE。
- **明确问题 = 本线 SSH 观测入口不成立**（`Host key verification failed.`）：属取证面事实，不是被观测系统的负事实。
- **未测试 = 提供方调用面**（SSO 真实登录流转需交互/会话凭据授权；本批 0 尝试）。
- **归因推断（禁写成直接观测）**: 「§5 的落盘由 SPI 框架 maven 通道在启动时完成」= 推断级。支撑链 = P1 `VERIFIED_STATIC_BYTECODE`（`SPIJarLoader` / `SpringDynamicRegister` / 配置键 `seeyon.spi.spi-plugins`）+ e1/e2 Nacos 配置 LIVE。落盘本身（§5）与注册对（§6）是文件事实；「由谁拉取」不是。
- **负向命中口径**: 本线 0 输出、原料 §7 日志 0 命中，均禁写成「test2 未加载 SPI 插件」的系统事实（「未加载」只能由 spiPlugins 空即 return 作推断）。
- HTTP 200 / 空结果不算 PASS 的口径延续：本批 0 HTTP 探测，无该类命中。

## 4. 写盘前基线实测（本线 sha256sum 亲算，非转述）

`core/facts/spi/spi-ext-runtime.md` **10696 B** / `bc46634ee376abc7e70427580ff2fd3fca5b963ab5d334d120364294d9908f85`；`core/facts/INDEX.md` 8754 B / `42abee5f…fbec8`；`evidence/live/` 实测 6 件（e1 `7f6d7f52…`、e2 `f3d6639e…`、e3 `edecde91…`、e4 `49e771d5…`、e5 `7b02944a…`、e6 `fd812aed…`）；`evidence/hashes/evidence-inventory.sha256.txt` `27434d48…`。

## 5. 所缺（本线不可自决）

- 一条对本线可用的 SSH 通路: 目标主机公钥需存在于本线执行用户的 `known_hosts`（或由既有可信信任锚解析）。补法属主机侧配置动作，本线按纪律未绕行、未改 `known_hosts`。
- 若该入口补齐，可复测的最小动作 = 批1（`ls -l --time-style=long-iso` + `sha256sum` 插件 jar）+ 批2（`unzip -p` spring.factories / `jar tf` boot jar 的 spi 清单），两批即可取到 §5/§6 的本线直读值。
