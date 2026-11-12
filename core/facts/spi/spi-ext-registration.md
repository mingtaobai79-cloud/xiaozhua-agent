# spi.spi-ext-registration｜SPI 扩展点注册契约（SPI-EXT-REG-01 · 九段式）

> 任务：HANDOFF P1（唯一活动边界）→ 在 `core/facts/spi/` 落 2 格九段式事实 + `evidence/`。
> 路线：`main/ROUTE.md`（P1，2026-09-29T10:35Z）。本件 = 动作 1。
> 交付仓 `<XIAOZHUA_AGENT_ROOT>`；写前实测 HEAD `dc12ef3d16a292116128ddc110c5cb1cd1cb4e8d`，
> `git status --porcelain` = 4 行（` M core/facts/INDEX.md`、`?? core/facts/connector/`、`?? core/facts/item-mgmt/`、`?? core/facts/spi/`）；
> 其中 `M INDEX.md` 与本件**无关**（本件写盘只限 `core/facts/spi/**` 与角色目录）。
> 证据等级：有 jar 字节码支撑 = `VERIFIED_STATIC_BYTECODE`；仅源码/文档 = `STATIC_CONTRACT`；运行态 = LIVE（本轮未做，属 P2）。
> 探时钟（落盘实测）：`2026-09-29T10:43:12Z` / 北京时间 `2026-09-29 18:43:12` / epoch `1790678592`。

## 1. Capability
**契约 SPI-EXT-REG-01 = 客开 SPI 模块的「接口 → 实现」注册声明契约。谁调用谁：平台侧（`boot-starter-spi`）在加载客开 SPI jar 时读取声明并实例化实现类；客开侧只提供声明文件与实现类。**

| 半 | 声明物 | 语义（字节码/在盘实测） |
|---|---|---|
| A 接口=实现 | `META-INF/spring.factories`（jar 内） | `java.util.Properties` 语义；**键 = 接口 FQN，值 = 实现类 FQN**；行尾 `\` 为 Properties 续行 |
| B 适配范围 | `metadata/spi_info.json`（客开模块） | 平台另有 `CustomizedSpiInfo.CUSTOMIZED_SPI_CONFIG_PATH` 常量（见 §7 口径差异） |

- 本格对象：`spi-mobile` / `spi-sso`（`docs/audit/modules/spi-module-profile.json`，status=FACT / verification_level=STATIC，sha256=`5d517319…`）。
- 接口侧身份（字节码）：`com.seeyon.cip.connector.api.sso.SsoService`，7 个抽象方法。
- **实现边界**：本格只登记「类/方法签名 + 声明文件字节 + 可观测副作用」，不含运行期执行（运行期为 SPI-EXT-LOAD-01 与本任务 P2）。

## 2. Version
- **契约版本单元 = `5.3.x`**（本格全部字节码证据来自 5.3.x 家族）。
- 接口侧 artifact：`com.seeyon:cip-connector-api:5.3.286`，本地 Maven 仓**仅此一版**；
  jar sha256=`de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91`（170420 B）。
- 客户模块声明的版本轴：父 POM `artifactId=boot-starter-spi-customized`、`version=1.0.0-TEST-SNAPSHOT`、
  `parent=com.seeyon:boot:5.3.293`、`properties.platform.version=3.10.1`、`modules=[spi-sso, spi-mobile]`。
- **版本缺口（强制登记，不得混写）：客户模块 `platform.version=3.10.1`，本地 Maven 仓无 3.10.1 家族
  → 本格契约对 `3.10.1` 的适用性 = `UNVERIFIED`。**

| 类 | jar（GAV） | class sha256（jar 内条目，实测） |
|---|---|---|
| `com.seeyon.cip.connector.api.sso.SsoService` | com.seeyon:cip-connector-api:5.3.286 | `f181b43f069eebf40e91601a0ba1c9e4f66fc37c2a498f91b37bba1cbc0e2f2a` |
| `com.seeyon.cip.connector.enums.SsoClientTypeEnum` | 同上 | `0853e034c9f8cdfa57aa6c490bc062dbf2fe632d60c681ea12d1def6f160b1eb` |

## 3. Input
### 3.1 客开侧在盘输入（`<PATH> sha256 实测）
| 文件 | 字节 | sha256 |
|---|---|---|
| `pom.xml`（父 POM） | 743 | `c01eea62157360ddcfa87046badfb72483e7c82669953ce6147f9428076a6c6f` |
| `README.md` | 1741 | `b6d6c6c5e3a022586de4341b1f18d537207f389d8bf7eb48abb8b21ae07083b3` |
| `spi-mobile/pom.xml` | 977 | `8299db4ddfe19255a8fc46a19ed83ef25d838af9bfe4e2ac0eaccb9749d3e85b` |
| `spi-sso/pom.xml` | 974 | `898ca6ebbe61128028949c6982171dde1cb45e99ca7be84cb0db094d7f63d989` |
| `spi-mobile/src/main/resources/META-INF/spring.factories` | 95 | `dddc9dc2c4c285aaeddeaf8b1b23d909be41cce33d82a10cd635683971105518` |
| `spi-sso/src/main/resources/META-INF/spring.factories` | 95 | 同上（`cmp` 实测**逐字节相同**） |
| `spi-mobile/src/main/resources/metadata/spi_info.json` | 95 | `258a66953210b2f850aa805b21977d77fc7ad7a83c0c2b23cc7abda4ab2079bc` |
| `spi-sso/src/main/resources/metadata/spi_info.json` | 95 | 同上（`cmp` 实测**逐字节相同**） |
| `spi-mobile/…/com/seeyon/extend/spi/sso/TemplateSsoServiceImpl.java` | 3712 | `ddac7a85b39dfcd01a3f9be304c9f9ab291ed0bb210c815030fc0b54bd535dd5` |
| `spi-sso/…/com/seeyon/extend/spi/sso/TemplateSsoServiceImpl.java` | 3712 | 同上（`cmp` 实测**逐字节相同**） |

- 客户仓 `git HEAD = a954272`（"客开工程初始化"），`git status --porcelain` = `?? .idea/`。
- **无构建产物**：全仓 `find -name "*.jar"` 为空、无 `target/`；`third-jar/` 目录为空（ROUTE §4.2 记「仅 README.md」）。
- `spi-mobile/pom.xml` 依赖：`com.seeyon:cip-connector-api:${platform.version}`。

### 3.2 接口侧方法面（javap -p VERBATIM）
`SsoService`：`getName():String` / `getTypeCaption():String` / `login(String,String,Map<String,Object>,SsoClientTypeEnum,Map<String,Object>):String` /
`check(String):void` / `getPageJson():String` / `getSortNo():Integer` / `needUserBind():boolean`。
（原文：`evidence/javap-signatures/SsoService.javap-p.txt`，625 B，sha256 `c8272902a5a0e121d396fd068e13911642e1d76f43583ab51daf3e9c395e957a`）

## 4. Required
- **A 半（spring.factories）必需**：至少一条 `接口FQN=实现类FQN`；实测文件 95 B、LF=1 / CR=1（CRLF 行尾）、**无尾随换行**：
  ```
  com.seeyon.cip.connector.api.sso.SsoService=\<CRLF>com.seeyon.extend.spi.sso.TemplateSsoServiceImpl
  ```
  行尾 `\` 由 `java.util.Properties` 解析为续行（平台侧确以 Properties 装载，见 SPI-EXT-LOAD-01 §5）。
- **B 半（spi_info.json）实测字段**：`name`、`scopes[]`；实测 95 B、LF=3 / CR=3（CRLF）、**无尾随换行**：
  ```
  {<CRLF>
    "name": "boot-starter-spi-customized",<CRLF>
    "scopes": ["dongfangtong9044958822953602326"]<CRLF>
  }
  ```
  逐字源=在盘件 `spi-mobile/src/main/resources/metadata/spi_info.json` 实测转录。
- **实现类必需覆盖接口全部 7 个抽象方法**（§3.2 签名清单为准）。
- 缺省/可空行为（缺 `name`、空 `scopes`、`scopes=ALL`）→ **本轮未观测 = UNVERIFIED**。

## 5. Execution
- **调用向**：平台 → SPI（客开侧不主动调用平台；只提供声明文件 + 实现类）。注册动作发生在平台加载阶段，
  本格只固定「声明面」，实例化/注册/事件链在 **SPI-EXT-LOAD-01**。
- **注册定位（文件 + 行）**：
  | 项 | 文件 | 行 | 内容（逐字） |
  |---|---|---|---|
  | 接口 FQN | `spi-mobile/src/main/resources/META-INF/spring.factories` | L1 | `com.seeyon.cip.connector.api.sso.SsoService=\` |
  | 实现类 FQN | 同上 | L2 | `com.seeyon.extend.spi.sso.TemplateSsoServiceImpl` |
  | `name` | `spi-mobile/src/main/resources/metadata/spi_info.json` | L2 | `"name": "boot-starter-spi-customized"` |
  | `scopes` | 同上 | L3 | `"scopes": ["dongfangtong9044958822953602326"]` |
- 实现类签名（源码在盘，`STATIC_CONTRACT` 级）：`public class TemplateSsoServiceImpl implements SsoService`，
  `@Slf4j` 注解，方法体仅返回常量/透传（`getName()`→`"template"`、`getTypeCaption()`→`"xx认证"`、
  `getSortNo()`→`99`、`needUserBind()`→`false`、`check(String)` 空体、`getPageJson()` 返回内联 JSON 字面量、
  `login(...)` 内 `JsonUtils.fromJson(json, CasSsoDto.class)` 后回填 `url`）。`check` 与 `login` 同时被接口与实现双重约束。
- **运行期复现**：本格**未联网、未部署、未调用任何端点**（P1 禁 LIVE）。

## 6. Side Effects
| 侧 | 实测结论 |
|---|---|
| 客开侧运行时 | 实现类为无状态模板；**无写路径证据** → 宿主副作用 `UNVERIFIED` |
| 平台侧注册副作用 | `DefaultListableBeanFactory.registerSingleton(...)`（属 LOAD 格，字节码见 SPI-EXT-LOAD-01 §5） |
| 本件动作副作用 | **0 写业务数据、0 网络、0 凭据入件**；写盘仅 `core/facts/spi/**` + 角色目录 |

## 7. Known Constraints
1. **本地注册 ≠ 部署成功 ≠ 运行态被调用**：本轮仅证明「在盘声明 + 接口方法面」，无构建产物、无运行态观测（P2 范围）。
2. **两模块注册逐字节相同**（spring.factories 与 spi_info.json 与实现类三件全部 `cmp` 相同）→ 只能证明**静态注册事实**，
   不能证明生产归属或运行期加载（与 `spi-module-profile.json.limitations` 同口径）。
3. **`spi_info.json` 定位口径存在差异（如实登记，不外推）**：
   - 平台字节码常量 `CustomizedSpiInfo.CUSTOMIZED_SPI_CONFIG_PATH` = **`custom-backend/spi_info.json`**
     （`ConstantValue`，VERBATIM 见 `evidence/javap-verbose/CustomizedSpiInfo.javap-v.txt`）；
   - 客开模块在盘资源路径 = `src/main/resources/metadata/spi_info.json`（实际 jar 内位置需构建后才可验）；
   - 二者**不是同一路径串**，且客户父 POM 的 `<name>` 恰为 `custom-backend` —— 构建/打包是否重映射资源 = **UNVERIFIED**
     （客户仓无 `target/`、无任何构建 jar，无法复算）。
   - 本条为 main 本轮 HANDOFF/ROUTE 口径（写作 `metadata/spi_info.json`）与字节码常量的**不一致点**，按实测登记，请 main 确认口径。
4. **版本缺口**：`platform.version=3.10.1` 本地无家族 → 对 3.10.1 的适用性 = `UNVERIFIED`（§2）。
5. **`CasSsoDto` 观察项已闭合（降级为源码级观察）**：它是 `TemplateSsoServiceImpl.java` 内的 `public static` 嵌套类
   （源码 L107–113，同文件），**非缺失 import**；等级 = `STATIC_CONTRACT`（源码在盘），不作字节码级 FACT 传播。
   ROUTE §4.2 的「待核项 / OBSERVATION」自此关闭。
6. **文档级观察（doc-as-observation）**：客户 `README.md` 记载 `scope: ALL 针对所有应用`、三方 jar 放 `third-jar/` 用 `scope=system + systemPath`、
   以及「客开 spiPlugins 文件存储三形态」yaml 片段；这些是**客户仓文档转述**，本轮**未用字节码坐实** → 仅登记为 OBSERVATION。
7. ROUTE §4.3 所列 `3.12.x` 平台源码树本轮**未复读、未计入证据**（仅作定位线索）。

## 8. Evidence（逐条实测；禁转述）
证据根目录：`core/facts/spi/evidence/`（**实测件 63 件 / 合计 423320 B**（含清单自身），逐件 sha256 见 `evidence/hashes/evidence-inventory.sha256.txt`，6913 B / `27434d484e3b71c2a744a16f659225b377df7618ff87a001035b80e3572f5c7f`，62 行=清单自身除外）。

### E1 artifact sha256（落盘后重定向再读）
`evidence/hashes/jars.sha256.txt`（242 B，sha256 `e7152a137ee9f0e6cc2d67adde958aec617f1244a9a6f913f2672d8d8b0407f7`）
```
67b830e4da9e805e462dd9eb4ba809888ba6a21f06b3f2dfe8fa3558bfc39dab *boot-starter-spi/5.3.358/boot-starter-spi-5.3.358.jar
de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91 *cip-connector-api/5.3.286/cip-connector-api-5.3.286.jar
```
`evidence/hashes/customer-files.sha256.txt`（1080 B，sha256 `2778ecfe84f5bf98fff8d82cd0fb09e5f70bd955077602387d0f5008519e6269`）— 内容同 §3.1 十行。

### E2 接口字节码 VERBATIM
- `evidence/javap-signatures/SsoService.javap-p.txt`（625 B / `c8272902…`）与 `…/SsoClientTypeEnum.javap-p.txt`（765 B / `36467cd7…`）
  —— 明文：`public interface com.seeyon.cip.connector.api.sso.SsoService` + 7 抽象方法；
  `public final class com.seeyon.cip.connector.enums.SsoClientTypeEnum extends java.lang.Enum<…> implements com.seeyon.boot.enums.Messageable`，
  枚举常量 `PC`/`PHONE`，方法 `code():int`。
- 逐类 sha256：`evidence/hashes/cip-connector-classes.sha256.txt`（237 B / `8b575197…`）。
- 附 `evidence/javap-verbose/SsoService.javap-v.txt`（5250 B / `e4b667fd…`）、`…/SsoClientTypeEnum.javap-v.txt`（10161 B / `613d6b52…`）。

### E3 客开声明件 VERBATIM 副本（逐字节同一性已 `cmp` 实测）
| 副本（写入 `evidence/customer-modules/`） | 字节 | sha256（= 原件 sha256） |
|---|---|---|
| `spi-mobile/META-INF-spring.factories.txt` | 95 | `dddc9dc2c4c285aaeddeaf8b1b23d909be41cce33d82a10cd635683971105518` |
| `spi-sso/META-INF-spring.factories.txt` | 95 | 同上 |
| `spi-mobile/metadata-spi_info.json` | 95 | `258a66953210b2f850aa805b21977d77fc7ad7a83c0c2b23cc7abda4ab2079bc` |
| `spi-sso/metadata-spi_info.json` | 95 | 同上 |
| `spi-mobile/TemplateSsoServiceImpl.java` | 3712 | `ddac7a85b39dfcd01a3f9be304c9f9ab291ed0bb210c815030fc0b54bd535dd5` |
| `spi-sso/TemplateSsoServiceImpl.java` | 3712 | 同上 |
| `spi-mobile/pom.xml` | 977 | `8299db4ddfe19255a8fc46a19ed83ef25d838af9bfe4e2ac0eaccb9749d3e85b` |
| `spi-sso/pom.xml` | 974 | `898ca6ebbe61128028949c6982171dde1cb45e99ca7be84cb0db094d7f63d989` |
| `boot-starter-spi-customized.pom.xml` | 743 | `c01eea62157360ddcfa87046badfb72483e7c82669953ce6147f9428076a6c6f` |
| `boot-starter-spi-customized.README.md` | 1741 | `b6d6c6c5e3a022586de4341b1f18d537207f389d8bf7eb48abb8b21ae07083b3` |

### E4 行尾/字节形态（`od -c` 实测，非 `wc -l`）
- 客开 spring.factories（95 B）：`…SsoService=\ CR LF com…TemplateSsoServiceImpl`，**无尾随换行**（LF=1 / CR=1）。
- 客开 spi_info.json（95 B）：`{ CRLF 2空格"name"… CRLF …scopes… CRLF }`，**无尾随换行**（LF=3 / CR=3）。
- 两模块同名件 `cmp` 全通过：`FACTORIES_IDENTICAL` / `SPIINFO_IDENTICAL` / `IMPL_IDENTICAL`。

### E5 证据清单哈希
`evidence/hashes/` 内 5 件：`jars.sha256.txt`（242 B / `e7152a13…`）、`customer-files.sha256.txt`（1080 B / `2778ecfe…`）、
`platform-classes.sha256.txt`（1610 B / `3f525133…`，13 个平台 class 逐件 sha256）、
`cip-connector-classes.sha256.txt`（237 B / `8b575197…`）、`evidence-inventory.sha256.txt`（6913 B / `27434d48…`，62 件全量＝清单自身除外）。
另：常量池真值件 `class-constant-strings/loader-utf8-constants.txt`（10788 B / `dd29d074…`）、
`class-constant-strings/maven-and-registrar-utf8-constants.txt`（13216 B / `3389e861…`）、还原工具 `cp_strings.py`（1395 B / `356b96e6…`）、
目录索引 `evidence/README.md`（2897 B，见清单）。
复算口径：`cd core/facts/spi/evidence && find . -type f ! -name evidence-inventory.sha256.txt | sort | xargs sha256sum | diff - hashes/evidence-inventory.sha256.txt`（应 0 差异）。

## 9. Verified（逐项等级 + 未直读项）
| 项 | 等级 | 依据 |
|---|---|---|
| `SsoService` 接口方法面（7 方法 + 签名） | **VERIFIED_STATIC_BYTECODE** | E2 `cip-connector-api-5.3.286.jar` javap -p / -v |
| `SsoClientTypeEnum` 常量面（PC/PHONE、`code()`） | **VERIFIED_STATIC_BYTECODE** | E2 |
| 客开 `spring.factories` 声明「接口FQN=实现类FQN」 | **VERIFIED_STATIC_BYTECODE**（平台侧解析） + **在盘实测字节**（客开侧） | E3/E4 + SPI-EXT-LOAD-01 §5 `SpringFactoriesLoader.loadFactories` |
| 客开 `spi_info.json` 的 `{name, scopes}` 值 | **在盘实测（STATIC；客开件无字节码）** | E3/E4（95 B 逐字节副本） |
| 两模块注册件逐字节相同 | **实测（`cmp`）** | E4 |
| 实现类源码签名（implements SsoService、7 方法、`CasSsoDto` 为嵌套类） | **STATIC_CONTRACT**（源码在盘，无编译产物） | E3 源码副本 |
| jar 版本单元 = 5.3.x（boot-starter-spi 5.3.358 / cip-connector-api 5.3.286） | **VERIFIED_STATIC_BYTECODE** | E1 jar sha256 + E2 |
| 对客户声明 `platform.version=3.10.1` 的适用性 | **UNVERIFIED** | §2/§7.4（本地无 3.10.1 家族） |
| `spi_info.json` 在**运行/打包**时的读取路径 | **UNVERIFIED** | §7.3（平台常量 `custom-backend/spi_info.json` ≠ 在盘 `metadata/spi_info.json`；无构建产物） |
| 部署成功 / 运行态被调用 | **UNVERIFIED（P2 范围）** | §7.1 |
| 宿主侧副作用 | **UNVERIFIED** | §6 |
| 客户 README 的 `ALL`/三方 jar/文件存储口径 | **OBSERVATION（文档转述，未坐实）** | §7.6 |

**未直读项（如实登记）**：无构建 jar（无法验 jar 内资源路径与 shade 结果）；无 3.10.1 家族字节码；未做任何 LIVE；
`NAME`/`scopes` 的服务端消费行为未观测。本件**未改 `INDEX.md`/`STATUS.md`、未碰其他 `core/facts` 目录、凭据 0 入件**。

## 溯源索引（可复现）
| 项 | 路径 |
|---|---|
| artifact sha256 | `core/facts/spi/evidence/hashes/jars.sha256.txt` |
| 客开在盘 sha256 | `core/facts/spi/evidence/hashes/customer-files.sha256.txt` |
| 接口字节码 | `core/facts/spi/evidence/javap-signatures/SsoService.javap-p.txt`、`…/SsoClientTypeEnum.javap-p.txt`、`javap-verbose/` 同名件 |
| 客开声明件副本 | `core/facts/spi/evidence/customer-modules/`（10 件） |
| jar 清单 | `core/facts/spi/evidence/jar-contents/cip-connector-api-5.3.286.unzip-l.txt`（14815 B / `16dbc718…`） |
| 平台侧注册/加载字节码 | `core/facts/spi/evidence/javap-signatures/`、`javap-verbose/`、`javap-code/`（见 SPI-EXT-LOAD-01） |
| 复算工具 | `sha256sum`（MSYS）、`unzip`、`cmp`、`od`；javap=`"C:/Program Files/Java/latest/jdk-21/bin/javap.exe"` |

> 自报（写后实测值见 RESULT，此处不回填以免自指漂移）：本件与 `spi-ext-loading.md` 同批落盘；
> 证据目录 63 件 / 423320 B（含清单自身）；`cmp` 三组同一性全通过；凭据 0 入件。
