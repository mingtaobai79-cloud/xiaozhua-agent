# spi-ext-contract-surface｜`cip-connector-api` 扩展点全集 × `spi-mobile`/`spi-sso` 实现边界

分级上限: `VERIFIED_STATIC_BYTECODE`（在盘 jar 字节码 + 在盘客户源）。运行态一律标 **未测试**。

## 1. Capability
- 枚举平台侧可供客户实现的 SPI 扩展点全集（`com.seeyon.cip.connector.api.**` 接口 + `javap -p` 签名）。
- 判定 `spi-mobile`/`spi-sso` 在该全集中实际注册并实现了哪几个（含负结果）。
- 本批不证: 插件是否被运行态加载/调用（未测试）、模块字节码（模块无编译产物，未取证）。

## 2. Version
- 被测对象: `com.seeyon:cip-connector-api:5.3.286`（GAV 坐标；jar 在本地 maven 镜像 `repo/CHIT` 内）。
- jar: 170420 B，sha256 前缀 `de4767da279c6622…`（锚件 `evidence/api-contracts/jar-anchor.sha256.txt`，命令 RC=0）。
- 客户模块: `custom-backend/spi-mobile`、`custom-backend/spi-sso`（各 5 件，源级在盘）。
- 工具: `javap -p`（JDK 21），沿 `spi-ext-loading.md` L219 先例。
- 采集时刻: 2026-10-08T04:27Z–04:29Z（`date -u` 实测，非推算）。

## 3. Input
| 输入 | 取得方式 | 锚 |
|---|---|---|
| api 全集清单 | `unzip -l <jar> \| grep -E 'com/seeyon/cip/connector/api/.*\.class'` | RC=0；`evidence/api-contracts/api-interfaces-unzip-l.txt`（内部输出 sha `17f28fb6`/2078 B） |
| FQN 列表 | `awk`+`sed` 由上行派生 | RC=0；`api-interfaces-list.txt`（内部输出 sha `89d63f5b`/1413 B，计 20 行） |
| mobile 组签名 | `javap -p -cp <jar> <api.mobile.* 8 FQNs>` | RC=0；`mobile-group.javap-p.txt`（内部输出 sha `b48ded20`/8398 B） |
| 非 mobile 组签名 | `javap -p -cp <jar> <其余 12 FQNs>` | RC=0；`nonmobile-group.javap-p.txt`（内部输出 sha `47b56176`/7483 B） |
| `SsoService` 单件 | `javap -p -cp <jar> com.seeyon.cip.connector.api.sso.SsoService` | RC=0；`sso.SsoService.javap-p.txt`（内部输出 sha `c8272902`/625 B） |
| 客户模块源 | `find`/`cat`/`grep` 只读 | RC=0；`customer-impl-crosscheck.md` §A 表逐行带命令与 RC |

## 4. Required
- 前置: 无网络、无凭据、无远端。jar 与 javap 可达即满足（实测 RC=0）。
- 依赖既有件（只读引用）: `evidence/jar-contents/cip-connector-api-5.3.286.unzip-l.txt`、`evidence/README.md`（jar 相对路径）、`spi-ext-registration.md` §E4（两模块逐字节相同）、`spi-ext-loading.md`（加载机制）。
- 不要求: 编译客户模块、启动平台、登录任何环境。

## 5. Execution
1. `ls -l` + `sha256sum` 取 jar 锚 → 170420 B / `de4767da…`（RC=0）。
2. `unzip -l` 全量列表 → grep `com/seeyon/cip/connector/api/**.class` → **20** 个条目（RC=0）。
3. `javap -p` 分三组跑全部 20 个（mobile 8 / 非 mobile 12，含 `SsoService` 另出单件），`grep -c "public interface"` 复核 = 8 + 12 = 20（RC=0）→ 全集 20 项**全部是接口**，无 DTO/枚举混入。
4. 客户模块源侧核验: `implements` 子句、`spring.factories` 注册键、`api.*` 包 import 命中集、`@Override` 计数、`*.class`/`*.jar` 存在性（RC=0，逐项见 `customer-impl-crosscheck.md` §A）。
5. 落格 + 落证据目录；本批 0 网络、0 改写既有件。

## 6. Side Effects
- 新增 1 格（本文件）+ 新目录 `evidence/api-contracts/` 内 7 件；0 改写既有件、0 删件。
- 0 网络副作用（无 SSH/kubectl/HTTP/建应用/探测）；0 远端写面。
- jar 与客户端源仅被读取，未被修改。

## 7. Known Constraints
- 只到静态字节码层: 接口签名与继承关系为字节码实测；「平台是否在某时刻加载/调用」不属本格结论范围 = **未测试**。
- 泛型接口签名引用外部类型（如 `com.seeyon.boot.transport.BaseDto`），本格不解依赖闭包，`javap` 输出按原样入件。
- 客户模块无本地编译产物 ⇒ 模块实现关系仅有源级证据，**未取证**（模块字节码）。
- 分组口径差异（实测 vs 前缀初核）: 总数 **20 相符**；`api.mobile` 包 8、`api.midorgsync` 包 5（2 + callback 3）、`api.callback` 2、sso/sign/authentication/affair/db 各 1。此前登记的 midorgsync=6 与其余分组求和为 21，与总数 20 自相矛盾；**以本格实测 5 为准**。
- 旧计数不回填: 既有格所记「证据 63 件 / 423320 B」为**时点锚**；本格只声明自身新增 8 件与时刻实测值，不重算历史计数。
- 扩展点全集=该 jar 的 `api` 包；其他 jar（如 boot-starter-spi 自身）可能另含平台侧扩展点，本格未覆盖 = **未取证**。

## 8. Evidence
| 件 | 内部锚 |
|---|---|
| `evidence/api-contracts/api-interfaces-unzip-l.txt` | 命令 + RC=0 + sha `17f28fb6`/2078 B |
| `evidence/api-contracts/api-interfaces-list.txt` | RC=0 + sha `89d63f5b`/1413 B + 20 行清单 |
| `evidence/api-contracts/mobile-group.javap-p.txt` | RC=0 + sha `b48ded20`/8398 B（8 接口） |
| `evidence/api-contracts/nonmobile-group.javap-p.txt` | RC=0 + sha `47b56176`/7483 B（12 接口） |
| `evidence/api-contracts/sso.SsoService.javap-p.txt` | RC=0 + sha `c8272902`/625 B（7 abstract 方法） |
| `evidence/api-contracts/jar-anchor.sha256.txt` | RC=0 + sha `09bdf422`/276 B；取得后对路径脱敏（`/d/repo/CHIT`→`repo/CHIT`），文件内注明 |
| `evidence/api-contracts/customer-impl-crosscheck.md` | §A 每行带命令与 RC=0；§B 指向本目录 javap 件 |
件级 sha（本批写后复算）与字节数随 RESULT 回 main；引用清单类锚一律带时点（2026-10-08T04:29Z）。

## 9. Verified
| 主张 | 判级 |
|---|---|
| `cip-connector-api:5.3.286` 的 `com.seeyon.cip.connector.api.**` 扩展点全集 = **20 个接口**（mobile 8 / midorgsync 5 / callback 2 / sso 1 / sign 1 / authentication 1 / affair 1 / db 1） | **VERIFIED_STATIC_BYTECODE**（`unzip -l` + `javap -p` 双测，RC=0） |
| `SsoService` 契约 = 7 个 abstract 方法（`getName`/`getTypeCaption`/`login`/`check`/`getPageJson`/`getSortNo`/`needUserBind`） | **VERIFIED_STATIC_BYTECODE**（`sso.SsoService.javap-p.txt`） |
| mobile 组 8 接口中 `MobileProviderService` 为根、其余 7 个 `extends` 之（`MobileCallBackProviderService` 另多重继承 `ConnectorCallbackProviderService<T,Res>`） | **VERIFIED_STATIC_BYTECODE**（`mobile-group.javap-p.txt`） |
| `spi-sso` 实现边界 = 注册并实现 `SsoService` 1 个（`spring.factories` 单键 + 单 `implements` + 7 `@Override` 对齐平台 7 方法） | **已证实**（源级实测）；模块字节码侧 **未取证 UNVERIFIED** |
| `spi-mobile` **未实现任何 mobile 组接口**（源侧 `implements` 仅 `SsoService`；`api.*` import 仅 `api.sso.SsoService`；`spring.factories` 注册键仅 Sso 一项） | **已登记但未实现 = 负结果（成立）**；模块字节码侧 **未取证 UNVERIFIED**（0 `.class`/`.jar` 在盘） |
| 其余 19 个扩展点（非 SsoService）在两模块中的实现情况 | **负结果**：源侧 0 命中（`customer-impl-crosscheck.md` §A 第 4 行实测） |
| 上述接口的运行态加载/调用 | **未测试**（本批 0 网络；禁写 LIVE） |
| 其他 jar 是否另含扩展点 | **未取证 UNVERIFIED** |
