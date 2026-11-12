# standard-product｜标品域契约事实格（P1 字节码核验，2026-09-29）

> 会话：`session-20260929-184027-7f85bd1f` ｜ 授权：main/`main/ROUTE.md` §3 HANDOFF-1（dedupe_key=`handoff-1-bytecode-contracts`）
> 本线口径：纯静态——未连 test2 网关、未建测试应用、无任何业务接口探测；**唯一网络例外**＝HUMAN 授权 2026-10-01 对内网 Artifactory `libs-release` 的**只读 GET 制品拉取**（仅 ctp-user-api 3.8.215，见契约格 E），证据分级上限仍 `VERIFIED_STATIC_BYTECODE`，本线不产 `LIVE`。
> 证据分级：`STATIC_CONTRACT` < **`VERIFIED_STATIC_BYTECODE`（本格级）** < `LIVE`（本线不产）。
> 证据目录：`core/facts/standard-product/evidence/bytecode/`；其中 `manifest.json` 自身
> sha256 = `7da5394160d84aba67e99f5bb6fcb6e804e2eb01ed2cfc07ad8448198f25ffbd`。
> 工具链：cfr **CFR 0.152**（`java -jar <cfr.jar> --version` 实测可执行，位于 LBS 树只读引用）；
> java 21.0.10 LTS；`javap` 不在 PATH（javapath shim 仅 java/javac/javaw/jshell），故统一以 cfr 核验。
> 纪律：凭据 0 入件；每声明引在盘实据路径 + sha256；无证据一律 `UNVERIFIED`，不编。

---

## 契约格 A｜`com.seeyon.cip.connector.api.sso.SsoService`（cip-connector-api 5.3.286）

### 1. Capability
标品 CIP 连接器的 **SSO 单点登录扩展点契约**（SPI 接口）。宿主（CIP 连接器运行体）通过该接口
向第三方 SSO 实现索取登录入口、登录信息与页面配置：能力面 = SSO 提供方列举元信息
（名称/描述/排序/是否需用户绑定/页面 JSON）＋ 登录动作 ＋ 登录参数校验。

### 2. Version
- artifact `cip-connector-api`，version **5.3.286**（pom.properties 实测 `version=5.3.286`）。
- 源 jar（Maven 坐标）：`com.seeyon:cip-connector-api:5.3.286`（按坐标从 Artifactory/本地仓库解析）
  实测 sha256 = `de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91`
  ——与 `docs/audit/modules/standard-product-module-profile.json`（第 27 行）**逐字一致**。
- class 文件 major version = **52 → Java 8**；jar 内 `META-INF/MANIFEST.MF` 实测
  `Build-Jdk: 1.8.0_291`、`Created-By: Apache Maven 3.6.3`（原文见 evidence）。
- pom 父级：`com.seeyon:boot:5.3.271`。
- profile 登记 `class_count=124`，本格实测 jar 内 `.class` 条目 = **124，一致**。

### 3. Input
类型级无输入（`interface`）。方法级签名（cfr 反编译原文，逐字）：

```java
public interface SsoService {
    @CipConnectorComment(value="获取名称")                          public String getName();
    @CipConnectorComment(value="获取描述")                          public String getTypeCaption();
    @CipConnectorComment(value="登录url : 登录urljson : 登录信息json串
        userMap : 用户信息map clientType :客户端类型 extendParams : 扩展字段")
                                                                    public String login(String, String, Map<String,Object>,
                                                                                        SsoClientTypeEnum, Map<String,Object>);
    @CipConnectorComment(value="jsr303校验")                        public void check(String);
    @CipConnectorComment(value="获取页面json语句")                   public String getPageJson();
    @CipConnectorComment(value="排序")                              public Integer getSortNo();
    @CipConnectorComment(value="是否需要用户绑定操作")                public boolean needUserBind();
}
```
（上表为版面改写；**逐字原文**见 §8 证据件 `cip-connector-api-5.3.286-SsoService.java` 第 10–31 行。）

### 4. Required
- 实现方须实现上述 **7 个抽象方法**（`getName`/`getTypeCaption`/`login`/`check`/`getPageJson`/`getSortNo`/`needUserBind`）。
- 须实现为 **Spring 可发现 Bean**：本 jar 不提供 `META-INF/services/` 注册件（见契约格 C），
  字节码内唯一发现路径是注解元数据（`@Indexed`）＋ Spring `ApplicationContext` 查取。
- `login` 的客户端类型取自同 jar 枚举 `com.seeyon.cip.connector.enums.SsoClientTypeEnum`
  （in-jar class 条目 sha256 = `0853e034c9f8cdfa57aa6c490bc062dbf2fe632d60c681ea12d1def6f160b1eb`；
  枚举常量集未展开 → 本格对其取值集 `UNVERIFIED`）。
- 参数校验语义标注为 `jsr303校验`；实测 jar 内 **15** 个 DTO class 条目的常量池含
  `javax/validation` 标记（模式：`javax/validation`；`jakarta/validation` 命中 0）。

### 5. Execution
- 契约形态：**纯接口，无方法体**（`class` 条目 access_flags 含 `ACC_INTERFACE`）。
- 运行时解析路径（同 jar 内工具类 `com.seeyon.cip.connector.common.CipConnectorSpiUtils`
  反编译原文）：`getBean(Class)` → `com.seeyon.boot.context.Apps.getApplicationContext().getBean(clazz)`；
  或 `getInstance(Class)` → 无参构造反射实例化并缓存于静态 `ConcurrentHashMap<String,Object> instances`。
- 契约文件本身不含任何业务执行代码。

### 6. Side Effects
无。本件为接口定义（jar 内无实现类、无静态初始化副作用；`SsoService.class` 无 `<clinit>` 工件需求）。

### 7. Known Constraints
- **参数名不可由字节码确证**：cfr 对接口抽象方法只能输出 `var1..varN`（抽象方法无 LocalVariableTable），
  故 §3 中 URL/urlJson/userMap/clientType/extendParams 的对应关系**仅由 `@CipConnectorComment` 文案解释**，
  属 `STATIC_CONTRACT` 级解释，不是字节码确证事实。
- 7 个方法的**行为语义**（返回值含义、异常、幂等性）不可得：本 jar 只有接口，无实现；
  本线零活体，**未**取得任何 LIVE 证据 → 行为面 `UNVERIFIED`。
- `SsoClientTypeEnum` 常量集、`getPageJson` 的 JSON 结构 = `UNVERIFIED`。

### 8. Evidence
| 项 | 路径 | sha256 |
|---|---|---|
| 源 jar | `com.seeyon:cip-connector-api:5.3.286`（Maven 坐标） | `de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91` |
| 反编译件 | `core/facts/standard-product/evidence/bytecode/cip-connector-api-5.3.286-SsoService.java` | `fa08f8636237eb89f1465eb3063ede31eba0796a131703ec1941a97dac749fd3` |
| jar 内原始 class 条目 | `com/seeyon/cip/connector/api/sso/SsoService.class` | `f181b43f069eebf40e91601a0ba1c9e4f66fc37c2a498f91b37bba1cbc0e2f2a` |
| 注册/工具类证据 | `...-CipConnectorSpiUtils.java` | `d6a31b175271f7de09712cfb929ce2488c8e7329ccb7eb90a44e2b81a5b5e240` |
| 复算清单 | `.../evidence/bytecode/manifest.json` | `7da5394160d84aba67e99f5bb6fcb6e804e2eb01ed2cfc07ad8448198f25ffbd` |

命令（可重跑）：`java -jar <cfr.jar> <上述 jar> --outputdir <tmpdir>`。

### 9. Verified
**`VERIFIED_STATIC_BYTECODE`**（接口签名 + 注解元数据 + 类型引用；源 jar 在盘且 sha256 与 profile 逐字一致，可现场重跑）。
行为语义、枚举取值集、页面 JSON 结构 = **`UNVERIFIED`**。

---

## 契约格 B｜`com.seeyon.cip.connector.api.mobile.MobileOrgSyncProviderService`（cip-connector-api 5.3.286）

### 1. Capability
标品 CIP 连接器的 **移动平台组织/人员同步扩展点契约**（SPI 接口）。宿主通过该接口把
组织单位（Unit）与人员（User）的增/改/查/删同步动作委派给具体移动平台实现（如企业微信/WeLink 等实现方）。

### 2. Version
同契约格 A：`cip-connector-api` **5.3.286**，源 jar sha256 `de4767da…4f91`（与 profile 逐字一致）。

### 3. Input
父接口：`com.seeyon.cip.connector.api.mobile.MobileProviderService`（**空标记接口**，仅 `public interface MobileProviderService {}`）。
本接口 8 抽象方法 + 1 default 方法（cfr 反编译逐字）：

```java
public interface MobileOrgSyncProviderService extends MobileProviderService {
    Long   syncUnit(MobileUnitRequestDto, MobilePlatformConfigDto);
    void   updateUnit(MobileUnitRequestDto, MobilePlatformConfigDto);
    String getUnit(MobileUnitRequestDto, MobilePlatformConfigDto);
    void   removeUnit(MobileUnitRequestDto, MobilePlatformConfigDto);
    String syncUser(MobileUserRequestDto, MobilePlatformConfigDto);
    String updateUser(MobileUserRequestDto, MobilePlatformConfigDto);
    MobileUserResponseDto getUser(MobileUserRequestDto, MobilePlatformConfigDto);
    MobileUserResponseDto removeUser(MobileUserRequestDto, MobilePlatformConfigDto);
    default MobileOrgDto syncUnitNew(MobileUnitRequestDto dto, MobilePlatformConfigDto configDto) { return null; }
}
```
（同 A：入口参数名对抽象方法不可得，此处为版面改写；逐字原文见证据件第 14–44 行。）

引用的同 jar 类型（in-jar class 条目 sha256，实测）：
- `dto/mobile/MobileUnitRequestDto.class` = `e3a217cfdd6847e77f8a84f412c4708b53dfc1379b10d345ea6c759ed6949a4f`
- `dto/mobile/MobilePlatformConfigDto.class` = `686ac3ba5c68fd9301d21be652ef4ca0d5db142585fb36ba13a5403379aa6d55`
- `dto/mobile/MobileUserRequestDto.class` = `fd5d0e1ce976479d667f14196253d925ccc8bc6c852fee6117388398f68fc0bd`
- `dto/mobile/MobileUserResponseDto.class` = `b45a4f5aad1d7bcab0c9672a90bd3f92ea20ddd79cdbc9c29c5580f2edd2ef43`
- `dto/mobile/MobileOrgDto.class` = `b306f2b0c6abfe8208b467e17cc9b77e61c8b56c46f1aa01e0a986def8b26e04`

### 4. Required
- 实现方须实现 8 个抽象方法（`syncUnit`/`updateUnit`/`getUnit`/`removeUnit`/`syncUser`/`updateUser`/`getUser`/`removeUser`）。
- `syncUnitNew` **带 default 实现**：不实现亦可编译，默认返回 `null`（"无该能力"的语义须由调用侧处理）。
- 每个方法均须携带 `MobilePlatformConfigDto`（平台配置）作为末位入参 → 配置为**逐次调用显式传入**，非实现类内部持有。
- 同样须以 Spring Bean 形态被发现（本 jar 无 ServiceLoader 注册件，见契约格 C）。

### 5. Execution
纯接口（除 `syncUnitNew` 的 `return null` 默认体外无代码）。`syncUnitNew` 的 default 方法是本 jar 内
**唯一带方法体的契约成员**，其字节码仅 `aconst_null; areturn`（cfr 输出 `return null;`）——
即该默认实现的语义就是"不提供"。

### 6. Side Effects
无。契约文件为接口定义；`syncUnitNew` 默认实现无副作用（仅返回 null）。

### 7. Known Constraints
- 参数语义（哪个 DTO 承载哪段数据）**不可由字节码确证**（抽象方法无参数名）；本格只确证类型与元数。
- 实现方行为（是否真同步、事务边界、失败重试）不可得：jar 内无实现类，本线零活体 → `UNVERIFIED`。
- 3 个 DTO 的字段结构未展开（本次边界只做"接口签名/DTO/注册机制"核验中的签名与注册面）→ 字段级 `UNVERIFIED`。

### 8. Evidence
| 项 | 路径 | sha256 |
|---|---|---|
| 反编译件（契约） | `evidence/bytecode/cip-connector-api-5.3.286-MobileOrgSyncProviderService.java` | `551b9e01aeafcf00e21bea68c330addeb7815e8ac34865155ca18df00317afa7` |
| 反编译件（父接口） | `evidence/bytecode/cip-connector-api-5.3.286-MobileProviderService.java` | `1b78ddec336bcaab1abecef999ef785dc90847076ffd60ef87d1616ec906eab0` |
| jar 内原始 class 条目 | `com/seeyon/cip/connector/api/mobile/MobileOrgSyncProviderService.class` | `e5550dec578ae21a075e800557ca1c985ba892acacf47bd6d81561cbb70aeea8` |
| jar 内原始 class 条目（父） | `com/seeyon/cip/connector/api/mobile/MobileProviderService.class` | `36f118e1ea1f2c758f7f853d4541aaceabfedc6d3657b9e5c8377ec70ca2720d` |

### 9. Verified
**`VERIFIED_STATIC_BYTECODE`**（签名 + 继承关系 + 类型引用；可现场重跑）。
实现行为、DTO 字段结构 = **`UNVERIFIED`**。

---

## 契约格 C｜注册机制（jar 级核验）：无 ServiceLoader 注册件，注解驱动 + Spring 上下文解析

### 1. Capability
事实性登记：该标品 API jar 的 **扩展点发现/注册机制**是什么、注册件在哪。

### 2. Version
`cip-connector-api` 5.3.286（源 jar sha256 `de4767da…4f91`）。

### 3. Input
对 jar 全量条目一览（165 条目）与**全部 124 个 `.class` 条目**的原始常量池做标记扫描。

### 4. Required（实测结论）
- `META-INF/services/**`：**ABSENT**
- `spring.factories`：**ABSENT**
- `META-INF/spring.components`（spring-context-indexer 产物）：**ABSENT**
- 唯一注册相关原语：**3 个注解类**的常量池含 `org/springframework/stereotype/Indexed`（Spring 组件索引 stereotype）：
  `annotation/CipConnectorComment`、`annotation/ConnectorChannelRouter`、`annotation/MiddleTableChannelRouter`；
  三者的注解元数据均为 `@Target` + `@Retention(RUNTIME)` + `@Documented` + `@Indexed`。
- 运行时解析：`common/CipConnectorSpiUtils` 经 `Apps.getApplicationContext().getBean(...)` 或
  无参反射 + 静态缓存解析实例。
- 另有 `javax/validation` 标记出现在 **15** 个 DTO class 条目常量池（JSR-303 校验面）。

### 5. Execution
无（登记性事实）。

### 6. Side Effects
无。

### 7. Known Constraints
- 本结论的射程：**仅限本 jar 自身字节码**。消费方模块编译期由 spring-context-indexer 生成的
  `META-INF/spring.components` 存在于**消费方 jar**，不在本 jar 内 → 本格不推断其内容。
- 因此任何"本 jar 通过 ServiceLoader 自注册"的说法与在盘条目清单**矛盾**，判 `UNVERIFIED` 并作废。

### 8. Evidence
- jar 条目一览（165）/ class 条目 124：见 `manifest.json` → `sources[0].registration_mechanism`；
- 注解原文三件：`...-CipConnectorComment.java`（`a46123b612205c38458b207df84ddd54fc896fbb10e01e2c4db1218f7d017fa3`）、
  `...-ConnectorChannelRouter.java`（`e6a0c8dfe8f45111875743eceb7dac1e5967d2e138fd52fc3bf7695ef87d9a55`）、
  `...-MiddleTableChannelRouter.java`（`bc9bcb5fd5694ff00b43c4cf707d007700b442c24958753e4619bbdb35a298ce`）；
- 原始注册位（有/无）：`...-META-INF-MANIFEST.MF`（`a00dbe7db97770f0eef0b58f12cbc3a88ff10a0b946501f2600963d531d314fb`，242B，9 CR/9 LF）、
  `...-pom.properties`、`...-pom.xml` 原文同目录。

### 9. Verified
**`VERIFIED_STATIC_BYTECODE`**（注册件存在性 = 对全 jar 条目的确定性枚举，非推断）。

---

## 补充格 D｜`bpm-facade` **3.12.101**（jar 本体缺失 · 依据=在盘反编译件 + manifest source_sha256）

> **逐字标注（强制）：jar 本体缺失、不可现场重跑，依据=在盘反编译件 + manifest source_sha256。**

### 1. Capability
BPM 标品域契约类（`com.seeyon.bpm.api.common|udc` 包）的字节码产物登记与一致性复核。

### 2. Version
- artifact `bpm-facade`，version **3.12.101**；profile（第 13 行）登记 sha256 =
  `26b312fdd40cc921a4cd8d08239f6b8d857c02a5ac8d4db271d07f6fcbd98af0`，`class_count=484`。
- **本体缺失实测**：仓库中 `com.seeyon:bpm-facade` 仅有 `5.3.374/`（本格复测），不存在 `3.12.101` 制品。
- 在盘反编译件 `docs/audit/modules/decompiled/bpm-api-decompile-manifest.json` 的
  `source_sha256` = `26b312fdd40cc921a4cd8d08239f6b8d857c02a5ac8d4db271d07f6fcbd98af0`
  → 与 profile 登记**逐字一致**。故"反编译件↔profile 绑定"成立，但**源 jar 不可复算**。

### 3. Input
manifest 5 条 record（覆盖 4 个不同输出文件）+ 在盘 7 个 `bpm-facade-3.12.101-*.java`。

### 4. Required（逐条对齐结果，如实登记）
| # | class | 文件 | manifest sha256 | 实测 sha256 | 对齐 |
|---|---|---|---|---|---|
| 1 | `com.seeyon.bpm.api.udc.BpmUdcApiService` | `...-BpmUdcApiService.java` | `5028e167…f64e` | `5028e167…f64e` | ✅ MATCH |
| 2 | `com.seeyon.bpm.api.udc.BpmApiProcessAppService` | `...-BpmApiProcessAppService.java` | `e3b0c442…b855` | `40d07249…17c3` | ❌ **MISMATCH** |
| 3 | `com.seeyon.bpm.api.common.BpmApiProcessAppService` | `...-BpmApiProcessAppService.java` | `40d07249…17c3` | `40d07249…17c3` | ✅ MATCH |
| 4 | `com.seeyon.bpm.api.common.BpmAppService` | `...-BpmAppService.java` | `56275617…4402` | `56275617…4402` | ✅ MATCH |
| 5 | `com.seeyon.bpm.api.common.BpmDeployAppService` | `...-BpmDeployAppService.java` | `1bb33700…9090` | `1bb33700…9090` | ✅ MATCH |

**如实登记的偏差（不得静默对齐）**：
- 第 2 条 record 的 `sha256` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，
  即 **空文件（0 字节）的 sha256**；而在盘同名文件为 **781 字节**、实测 `40d07249abe01ab7a74d6e1201df93e18d9d57e35e35d8c221612aec390c17c3`。
  该 record **内部不一致，判 MISMATCH**（4/5 record 与盘一致，1/5 不一致）。
- 在盘 7 件中 **3 件未被 manifest 登记**（其 sha256 本格代为登记以便追溯）：
  - `bpm-facade-3.12.101-BpmSaveDraftUdcDto.java` = `e467675ebcf6c18a51a13458c777b9d67c5ac3cc61fc4adeef2146c75d12ad8f`
  - `bpm-facade-3.12.101-BpmSendUdcDto.java` = `2929db4b348545b81edac439bc5040daa961938353e1eab1503c970ea00ad5ba`
  - `bpm-facade-3.12.101-BpmTriggerFlowUdcRequestDto.java` = `557f15820d9950e6fb6422a966eb8ce27fe8a38c854a7487be33dbbd998c3dbf`

### 5. Execution
不可现场执行（无 jar）。本格只做"在盘产物 sha256 复算 + 与 manifest/profile 绑定比对"。

### 6. Side Effects
无。

### 7. Known Constraints
- **不可现场重跑**：源 jar 缺失，`source_sha256` 无法在本机复算验证，只能引用 manifest 登记值。
- 故本格分级为 **`VERIFIED_STATIC_BYTECODE（补充格）`**：产物字节在盘可复算 + 与 profile 的 sha256 链完整，
  但**不满足**"源 jar 在盘 → 现场反编译"的完整链条（低于契约格 A/B 的强度）。

### 8. Evidence
- 对齐明细：`evidence/bytecode/manifest.json` → `sources[1].recomputed_alignment`（5 条，含 `match` 布尔）；
- 在盘件目录：`docs/audit/modules/decompiled/`（7 件，逐件 sha256 见上/见 manifest）；
- profile：`docs/audit/modules/standard-product-module-profile.json`（第 9–14 行）。

### 9. Verified
**`VERIFIED_STATIC_BYTECODE（补充格，jar 缺失已逐字标注）`**；`bpm-api-decompile-manifest.json` 第 2 条 record 自身
**内部不一致**（登记了空文件 sha256），已在 §4 明列 MISMATCH。

---

## 契约格 E｜`ctp-user-api` **3.8.215** SSO/免登 SPI（原「存疑格 E」，2026-10-01 翻正）

> **获取方式 = Artifactory 只读拉取，HUMAN 授权 2026-10-01**（main/ROUTE.md §7.0.1 对「零活体」纪律的有限例外：仅 `libs-release` 只读 GET，无凭据、无 test2、无 POST）。
> 原 `UNVERIFIED` 记录逐字保留在 `evidence/bytecode/manifest.json` → `sources[2]`（未改写）与 `gaps_and_deviations` 第 4 条（未改写）；本格绑定件为**新追加**的 `sources[3]`。
> 分级 **`VERIFIED_STATIC_BYTECODE`**：签名由 javap 直接读 class 取得，并与整 jar CFR 反编译交叉核验（5/5 接口方法名集合完全一致）。

### 1. Capability
CTP 用户域的**统一三方认证（SSO）与免登（avoid-login）SPI 扩展接口族**——宿主（CTP 用户/登录运行体）按这些接口向第三方实现索取登录要素：

- `com.seeyon.ctp.user.api.sso.CtpUserSsoAuthProviderService`（`@CtpUserComment("统一三方认证 SPI 扩展接口, 实现类需要增加 @CtpUserChannelRouter 注解")`，19 个成员）：取临时 code/ticket 的参数 key、拼三方 SSO 登录地址、以 request+code 换取三方身份并映射为 v8 登录用户信息、移动端用户名密码登录、短信验证码、三方登出与登出重定向、短链模式、多用户择优、三方 token 刷新、4A token 缓存 key、上下文租户 tidCode、按设备声明支持的认证方式。
- 免登三形态：`avoidlogin.CtpAvoidLoginBackendProviderService`（后端免登）、`CtpAvoidLoginMiddlePageProviderService`（中转页免登 + token 刷新）、`CtpAvoidLoginClientModeProviderService`（客户端模式免登）。
- 公共基 `com.seeyon.ctp.user.api.CtpSsoAvoidLoginBaseService`（`getClientId()` + `String TAG = "[avoid]"`）。

### 2. Version
- artifact `ctp-user-api`，version **3.8.215**（jar 内 `pom.properties` 实测 `version=3.8.215`、`groupId=com.seeyon`；`META-INF/MANIFEST.MF` 实测 `Implementation-Version: 3.8.215`、`Build-Jdk: 1.8.0_291`、`Created-By: Apache Maven 3.6.3`；pom 父级 `com.seeyon:boot:3.8.210`）。
- 源 jar（Maven 坐标）：`com.seeyon:ctp-user-api:3.8.215`，实测 55669 字节，实测 sha256 = `5b1ec52abd87ba79abe962453776e54fa9bc27551aa171e76981d211a5950543`
  —— 与 `docs/audit/modules/standard-product-module-profile.json` 第 20 行登记值**逐字一致**（`sha256_matches_profile=true`）。
- `class_count`：profile 登记 49 → 实测 jar 内 `.class` 条目 = **49，一致**；49 个 class 的 major version **全部 = 52（Java 8）**。
- 与在盘 `5.3.331` / `5.3.351` 属**不同证据单元**，本版独立成格，不与其他版本合并（profile `limitations` 第 3 条口径）。

### 3. Input
类型级无输入（`interface`）。契约面全部方法签名由 `javap -public -s` 逐字取得（`evidence/.../javap-com_seeyon_ctp_user_api_sso_CtpUserSsoAuthProviderService.txt`）：

```java
public interface CtpUserSsoAuthProviderService {
  // 必须实现（abstract，3 个）
  String getRequestParaKey();                                        // ()Ljava/lang/String;
  String getSsoLoginUrl(HttpServletRequest, String);                 // (Ljavax/servlet/http/HttpServletRequest;Ljava/lang/String;)Ljava/lang/String;
  CtpUserSpiLoginUserInfoDto getUserLoginInfo(HttpServletRequest, String)
        throws CtpUserSpiSsoException, SpiAuthContinueException;     // 同上 descriptor
  // 可选覆写（default，16 个）
  default void setServerDomain(String);            /* @Deprecated */ default void setServerEnv(CtpUserSpiServerEnvDto);
  default Boolean sendVerifyCode(String);           default Boolean isRedirectShortLink() /* @Deprecated */;
  default ShortLinkModeEnum shortLinkMode();        default String getEncodeLogoutRedirectUrl();
  default void thirdSsoLogout(HttpServletRequest, String);
  default CtpUserSpiLoginUserInfoDto getUserLoginInfoForMobile(String, Map<String,Object>, CtpUserSpiAuthTokenEnum)
        throws CtpUserSpiSsoException;
  default boolean tokenExpiredSetNull();            default Long rebuildCtpUserDtoList(List<CtpUserSpiUserDto>);
  default CtpUserSpiThirdTokenDto refreshThirdToken(String, long) /* @Deprecated */;
  default CtpUserSpiThirdTokenDto refreshThirdTokenByConfig(String, Map<String,Object>);
  default String get4aTokenKey();                   default String getTidCode();
  default Map<String, CtpUserSpiAuthTokenEnum[]> mapSupportsAuthTokenEnum();
  default CtpUserSpiAuthTokenEnum getSuccessAuthTokenEnum();
}
```

免登三形态与基接口（同目录 4 个 javap 件）：`CtpAvoidLoginClientModeProviderService` = `preCheck(CtpUserSpiAvoidLoginClientModeDto) throws CtpUserSpiSsoException` + `getUserInfo(CtpUserSpiAvoidLoginClientModeDto) → CtpAvoidLoginUserInfoDto`；`CtpAvoidLoginMiddlePageProviderService` = `getUserInfo(String, Map<String,String>)` / `getCtpUserInfo(...)` / `isRefreshTokenCycle()` / `doRefreshToken(ThirdTokenDto)`（全 default）；`CtpAvoidLoginBackendProviderService` = `doExecuteAvoidLoginBackend(HttpServletRequest, HttpServletResponse)` / `avoidLoginBackend(...)`（全 default）；`CtpSsoAvoidLoginBaseService` = `getClientId()`（abstract）+ `static final String TAG`（实测值 `"[avoid]"`，见 cfr 件）。

DTO 面（profile 登记的 `com.seeyon.ctp.user.dto`，实测 18 类）：关键入出参 `CtpUserSpiLoginUserInfoDto`（`implements Serializable`，14 个 `private` 字段，含 `thirdUserId/thirdUserCode/thirdMobile/thirdLoginName/thirdUserEmail/tenantType/tenantData/thirdUserInfoJson/ctpUserSpiThirdTokenDto`）、`CtpUserSpiUserDto`（52 字段）、`CtpUserSpiServerEnvDto`、`CtpUserSpiThirdTokenDto`、`CtpAvoidLoginUserInfoDto`、`CtpUserSpiRedirectUrlDto`、`CtpUserSpiAvoidLoginClientModeDto`、`ThirdTokenDto`；`@CtpUserComment` 逐字段带中文语义说明（cfr 件原文）。

### 4. Required
- **必须实现**（class file flags = `ACC_PUBLIC, ACC_INTERFACE, ACC_ABSTRACT`，方法无 `default`）：SSO = `getRequestParaKey` / `getSsoLoginUrl` / `getUserLoginInfo`；ClientMode 免登 = `preCheck` + `getUserInfo`；所有免登形态继承 = `getClientId`（`extends CtpSsoAvoidLoginBaseService`，实测 3 个形态均 extends）。
- **可选**：SSO 其余 16 个 `default` 方法（含 3 个 `@Deprecated`：`setServerDomain`、`isRedirectShortLink`、`refreshThirdToken`）；Backend/MiddlePage 两形态**无 abstract 方法**⇒ 可只声明 `getClientId`。
- **实现类前置条件（契约注释原文，非推断）**：类上必须加 `@CtpUserChannelRouter`（见 §5）。

### 5. Execution（注册/装载机制 = 注解驱动，非 services 文件）
- `META-INF/services/**`、`spring.factories`、`org.springframework.*.imports`：**实测 ABSENT**（`unzip -l` 全清单 grep 无命中 ⇒ `registration-mechanism.txt` 记 `(no output) ABSENT`）。
- 实际机制 = **`@CtpUserChannelRouter`**：`@Target(TYPE)` + `@Retention(RUNTIME)` + `@Documented` + **元注解 `@org.springframework.stereotype.Indexed`**，唯一属性 `String value()`；`javap -p -v` 的 `RuntimeVisibleAnnotations` 段实测到该元注解链（`javap-verbose-annotation-CtpUserChannelRouter.txt`），与 cfr 件互证。`@CtpUserComment`（`TYPE/METHOD/FIELD`、`RUNTIME`、`@Repeatable(CtpUserComments.class)`、同样 `@Indexed`）承载契约文档串。
- 运行期取用件 = `CtpUserSpiUtils`：`getInstance(Class)`（自维护 `ConcurrentHashMap` 单例缓存 + 反射无参构造）、`getBean(Class)` / `getBean(String,Class)`（走 `Apps.getApplicationContext()`）、`invokeBean(beanName, methodName, params...)`（`ReflectUtil.getMethodByName` + `invoke`）、`getPropertyByName(key)`（yaml/nacos 配置读取）、`getRequest()`（`RequestContextHolder`）。
- **本线不证明任何一次真实调用或部署**（无 LIVE 级证据）；本节只描述 jar 内静态契约与注解机制。

### 6. Side Effects
接口自身无外部副作用（`interface` + `default` 体仅返回常量/委托）。契约语义规定的副作用面（来自 `@CtpUserComment` 原文，非推断）：三方登录后**重定向地址**（`getEncodeLogoutRedirectUrl`、`shortLinkMode` 短链开关：设模式即自动开启短链）、**三方 token 刷新与缓存**（`refreshThirdTokenByConfig`、`get4aTokenKey` 缓存 4A token）、**上下文租户赋值**（`getTidCode`）、**登录异常提示到页面**（`CtpUserSpiSsoException.message` 作为提示内容）、`tokenExpiredSetNull`（v8 token 过期置空以回三方登录页）。工具类实测含日志写出：`getRequest()` 打 `log.info("get request: {}")`、`invokeBean` 以 `JsonUtils.toJson` 记录入参/结果、异常走 `log.error`。

### 7. Known Constraints
- **jar 外依赖**（cfr 件头 `Could not load the following classes` 原文）：`javax.servlet.http.HttpServletRequest`、`org.apache.commons.collections.CollectionUtils`、`com.seeyon.boot.*`（`Apps`/`JsonUtils`）、`cn.hutool.core.util.ReflectUtil`、`org.slf4j.*`、`org.springframework.*`（含 `@Indexed`）⇒ 单独持有本 jar **不可编译/运行**完整链路，需宿主 classpath。
- `CtpUserSpiAuthTokenEnum` 三个常量各自绑定一个 Spring 认证令牌类名：`SPI_SSO→…authentication.SpiSsoAuthenticationToken`、`USERNAME_PASSWORD→…UsernamePasswordAuthenticationToken`、`PHONE_VERIFY_CODE→…PhoneNumberDynamicPasswordAuthenticationToken`；**这 3 个类不在本 jar 内**（实测 `security.authentication` 包仅 4 类 + provider 1 类）⇒ 类名仅为契约字符串，其真实存在性在本线为 **`UNVERIFIED`**，不得据此主张任何认证方式可用。
- profile 仅登记 3 个契约包（实测命中 **3/3**），但 jar 实际 **14 包 / 49 类**，登记覆盖 **22/49**；未登记的扩展包含 `api.menu`（`AbstractThirdMenuService`，abstract `selectThirdMenu`）、`api.qrcode`（`AbstractLoginQrCodeService`，3 个 abstract）、`annotation`、`constant`、`enums`、`exception`、`security.authentication(+.provider)`、`util`、`dto.menu`、`api`（⇒ `reconciliation.md` 的 profile 口径应以 `package-inventory.txt` 补全，本线不改写 `docs/audit/**`）。
- 本 jar **只有契约、0 个实现类**（49 类中无 `@CtpUserChannelRouter` 标注的实现）⇒ 不能证明任何具体标品/客开 SSO 实现存在；实现类由客开侧提供。
- 拉取通道：制品以 Maven 坐标定位（不记录本机路径）；任取 Artifactory 或本地仓库解析后用 `source_jar_measured_sha256` 校验即可复算（class 级 sha 已在 `file-hashes.txt` 与 manifest 留存以支持离线核对）。

### 8. Evidence
目录 `core/facts/standard-product/evidence/bytecode/ctp-user-api-3.8.215/`（**68 件** = 67 件证据 + `file-hashes.txt` 清单自身；逐件 sha256 见 `file-hashes.txt`，该清单自身 sha256 = `0cfb511959be185104d051af23f56115bb058980b1007d4e2527e544cce92301`，下表为关键件，均可用 `sha256sum` 独立复算）：

| 件 | sha256 |
|---|---|
| `class-inventory-unzip-l.txt`（76 条目 / 49 class 清单） | `08d4c2d671585b32daab667e0cc8cab2b3280ad9736bd82a00f3d21e119b1777` |
| `package-inventory.txt`（14 包分布 + major=52） | `40a780d46d5095963ef577d7f277709167030af530bda9de6a7da9182ad3d138` |
| `registration-mechanism.txt`（services/spring.factories ABSENT + @Indexed 指针） | `0d19372243ea861817a6c3d572ddead2b0757f55e1c4635ce953fa467e6c3861` |
| `crosscheck-javap-vs-cfr.json`（5 接口方法名集合等值） | `f09eb13136c39ec8fa3b84742c77b07fca8e6a7ee8520682567da8d52a95a6ff` |
| `javap-com_seeyon_ctp_user_api_sso_CtpUserSsoAuthProviderService.txt` | `c5741d241f54352d4281ad3349c26ef29dbf2b179c2bbe661934b9e889db5df1` |
| `javap-com_seeyon_ctp_user_api_CtpSsoAvoidLoginBaseService.txt` | `050fc182afa864aa5804e3f277c0c963b7691aa937001d59aee7ea5b7ffbe9a1` |
| `javap-com_seeyon_ctp_user_api_avoidlogin_CtpAvoidLogin{Backend,MiddlePage,ClientMode}ProviderService.txt` | `1421b924da98b15612b033506575c88d71269f4252b8565c6eafdbc2c6f0786a` / `16cdfcb7e97b156d64f338b80ae7bee9fba721a673bcc8b2f557aa2a858cedb6` / `f30f1c4aa30e0574856ef71342e1e7e06f2876158dbd9ef096d383c870b355be` |
| `javap-verbose-annotation-CtpUserChannelRouter.txt`（@Indexed 元注解） | `f56f781b15e2ccf9aad4bd0f83f947db156150987909fa9616bb537ccc16b691` |
| `javap-verbose-sso-interface-header.txt`（major 52 / flags 0x0601） | `24172937c2ed29ca68ccc2312d17b16815d63563e79d3fdea1dce03fd3167031` |
| `cfr-jar/com/seeyon/ctp/user/api/sso/CtpUserSsoAuthProviderService.java` | `4c3b6c155c5b286e0f0faf43ccd3424eee9ce6002e7d80b3a58723f1be83c0d7` |
| `cfr-jar/com/seeyon/ctp/user/annotation/CtpUserChannelRouter.java` | `fb231c2f3f9e3a28d5268e94e3fa261b694e3c21c74e27b773866edd2a6faa35` |
| `cfr-jar/com/seeyon/ctp/user/util/CtpUserSpiUtils.java` | `4b7a6fd0b951e3cadf73f9891819a4f55c06b3a0c8468853f396373266d5f9b2` |
| `cfr-jar/summary.txt`（CFR 0.152 整 jar 38 件产物） | `9e015cb596d716f9d56aead6ac4d02bd45887f8a4c2b63e33c59435d3042925f` |
| `META-INF-MANIFEST.MF` / `pom.xml` / `pom.properties`（jar 内原文提取） | `b7b059690da612caa9f4b373a6641a70263dbe6c65e9464567542e0d9784d12f` / `27ccba8fb545dffea8010a081b68d131832ff7baaab28c37e81586921e400953` / `9f80a36cc1ece01f4bddbf0aba50fdf11eb7abc484efef908ecd94aeeab4b4cd` |

登记锚：`evidence/bytecode/manifest.json` 追加后 sha256 = `d7643f75b916d32742a35c65cd2f0b0f032f3b49464eb93a7d0227291fb634f8`（追加前 `4e53e5f0…aa44`，`git diff --numstat` = 146 增 / 1 删，唯一“删”行是把 `sources[2]` 收尾的 `}` 改为 `},`，既有 3 条 source 与 `gaps_and_deviations` 经 `==` 断言证明语义逐字未变）。
命令与工具：`<LOCAL_ROOT>/java/bin/javap.exe`（JDK 21.0.10，`-public -s` / `-p -v`）、`java -jar <cfr.jar>`（CFR 0.152）、`unzip -l` / `unzip -p`、`curl -sS -O`（HTTP 200）；逐条见 manifest `sources[3].commands`。

### 9. Verified
**`VERIFIED_STATIC_BYTECODE`**（本线最高级；获取方式 = Artifactory 只读拉取，HUMAN 授权 2026-10-01）。
可独立复算链：jar sha256 ↔ profile 第 20 行 ↔ manifest `sources[3]` 三处一致；class 计数与 major ↔ `package-inventory.txt`；签名 ↔ javap 与 cfr 两路一致（`crosscheck-javap-vs-cfr.json`，5/5 集合等值）。
**不主张**：任何注册文件存在（实测 ABSENT）、任何实现类存在、任何运行期行为、任何 test2/活体调用（`LIVE` 由兄弟线负责）。

---

## 契约格附加事实｜`api/**` 接口清单（同 jar，支撑 A/B 的域边界）

对 `com/seeyon/cip/connector/api/**` 全部条目按 class 头部 access_flags 解析（与 cfr 无关的独立路径）：
**20 个条目，20 个均为 `interface`**——`affair`(1) `authentication`(1) `callback`(2) `db`(1)
`midorgsync`(2)+`midorgsync/callback`(3) `mobile`(8) `sign`(1) `sso`(1)。
profile 为该 artifact 登记的 5 个契约包（`api.sso`/`api.mobile`/`api.midorgsync`/`api.db`/`api.authentication`）
**均在本清单内命中**；契约格 A/B 所属包 `api.sso`、`api.mobile` 即其中两个。

---

## 本格边界（明确不在本次范围）

- **P2 对账**（`module_catalog.py` FACT/STATIC 标注、`UdcOperationRegistry` 基础契约口径 47 vs 59）——未做。
- **P3**（`core/facts/INDEX.md` 的 standard-product 行、`STATUS.md` 小节）——未做。
- **活体面**：本格零 HTTP、零环境接触；不存在任何 LIVE 声明。
- **凭据**：0 入件（本格全文只含路径、类名、sha256、工具版本）。
- 兄弟线领地（`core/facts/item-mgmt|connector|spi/**`）只读未写。
