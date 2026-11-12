# spi.spi-ext-loading｜SPI 扩展点加载契约（SPI-EXT-LOAD-01 · 九段式）

> 任务：HANDOFF P1（唯一活动边界）→ `core/facts/spi/` 2 格九段式事实 + `evidence/`。本件 = 动作 2。
> 路线：`main/ROUTE.md`（P1，2026-09-29T10:35Z）。
> 字节码来源（本地 Maven 仓 `<MAVEN_REPO>/com/seeyon`）：
> **`com.seeyon:boot-starter-spi:5.3.358`** sha256=`67b830e4da9e805e462dd9eb4ba809888ba6a21f06b3f2dfe8fa3558bfc39dab`（22906 B）；
> 接口侧 `com.seeyon:cip-connector-api:5.3.286` sha256=`de4767da279c6622aef95994d3c657e29b01c33eaea0db55e8fdf45537544f91`（170420 B）。
> javap = `"C:/Program Files/Java/latest/jdk-21/bin/javap.exe"`；全部输出 VERBATIM 落 `evidence/`。
> 探时钟：`2026-09-29T10:43:12Z` / 北京 `18:43:12` / epoch `1790678592`。分级同 ROUTE：字节码=`VERIFIED_STATIC_BYTECODE`。

## 1. Capability
**契约 SPI-EXT-LOAD-01 = 平台侧 `boot-starter-spi` 对客开 SPI 插件 jar 的「扫描 → 类加载 → Spring 注册 → 事件广播」契约；触发面 = `seeyon.spi.enable` + `seeyon.spi.spi-plugins`（三种取值形态）。谁调用谁：平台启动/配置变更回调 → SPI 插件 jar（客开实现类被平台读入并注册）。**

| 环节 | 类（本 jar 内，逐字节码） | 职责 |
|---|---|---|
| 自动装配入口 | `SPIAutoConfiguration` | `@Configuration` + `@EnableConfigurationProperties(SPIProperties.class)` + `@ConditionalOnProperty(value=["seeyon.spi.enable"])` |
| 应用启动监听 | `SPIApplicationRunListener` | `@Component`，`implements com.seeyon.boot.init.SeeyonApplicationRunner`；`run()` → `initialize()` + `loadExtendsSpi()` |
| 配置载体 | `SPIProperties` | `@ConfigurationProperties(prefix="seeyon.spi")` + `@ConfigAutoRefresh`；字段 `enable:boolean`（默认 `true`）、`spiPlugins:List<String>`（默认空 `ArrayList`） |
| jar 加载器 | `SPIJarLoader` | `@Service`；`getFilePath(List)`、`loadSPIPlugins(List)`、`loadSPIPlugins(List,boolean)`、`loadRemoteSPIPlugins()` |
| 插件类加载器 | `SPIClassloader` | `extends java.net.URLClassLoader`，构造 `(URL[], ClassLoader)` |
| 配置变更监听 | `SPIConfigChangeEventListener` | `@EventHandler`（类）+ `onConfigChange(ConfigItemChangeEvent)` 带 `@EventSubscribe` |
| 动态注册器 | `SpringDynamicRegister` | `implements ApplicationContextAware`；`registerBeanDefinition(String, Class<?>)`、`getBean(String)` |
| 制品解析（下载） | `SpiArtifactService`（接口）/ `SpiMavenService`（`@Component` + `@ConditionalOnBean(SpiMavenProperties.class)`）/ `SpiMavenProperties`（`PREFIX="seeyon.dynamic.loader.maven"`）/ `ArtifactInfo` / `CustomizedSpiInfo`(+`$SpiInfoModel`) | maven 形态的制品获取与自定义 SPI 信息载体 |

## 2. Version
- **契约版本单元 = `5.3.x`**（本格全部字节码来自 `boot-starter-spi:5.3.358`；接口来自 `cip-connector-api:5.3.286`）。
- class 文件 `major version: 52`（Java 8 目标）。jar 内 29 条目（含 13 个 class + `META-INF/spring.factories` + `README.md` + Maven 元数据），清单 VERBATIM：`evidence/jar-contents/boot-starter-spi-5.3.358.unzip-l.txt`（2286 B / `b60cde18…`）。
- **版本缺口（强制登记）**：客开模块声明 `platform.version=3.10.1`，本地 Maven 仓无 3.10.1 家族
  → **本格契约对 `3.10.1` 的适用性 = `UNVERIFIED`**。

| class（jar 内条目） | sha256（实测） |
|---|---|
| `SPIAutoConfiguration.class` | `a8bf49a2eae166ce93141510fe15d3daa0049ca4ddf4e160a4c05b8f9abbb784` |
| `SPIApplicationRunListener.class` | `767d4cfcb453a435b6cf62a5bda99d7d8e45bd29f923c5e1050464bb81166fb3` |
| `SPIProperties.class` | `a811015d970a323ca4713fe8fe38d97d4b49182a77776cf77a71451139a32365` |
| `SPIJarLoader.class` | `6452014252fec5e0ff3d33024bf20f58d6e04fb1565c873fe4d7754376a054dd` |
| `SPIClassloader.class` | `85c0a2a04d5ae0818477e9bd9778c7139dae83933b712153ecb9a6b12d399483` |
| `SPIConfigChangeEventListener.class` | `2b3885ed23a7d49e3bd4d51c8a1178a8d6d1460ef9696a63ead4c63cb9753170` |
| `SpringDynamicRegister.class` | `0c27132f56d1c4875364c61c5885d96a445b853427191fc928d031396e8bbd81` |
| `plugin/ArtifactInfo.class` | `04d8c390e94824fbe487bde0018596ea5c233e27697cdc2b72fab1f194f51363` |
| `plugin/CustomizedSpiInfo.class` | `09a3650425c8ee531be69907f7a454e7c74514a8fcc92810921f2c4dc99d9875` |
| `plugin/CustomizedSpiInfo$SpiInfoModel.class` | `3077a8bd763923c61215dab3c02efabcbca69c3f9fa714ece951453624cef6e4` |
| `plugin/SpiArtifactService.class` | `1c6b8ca4288a20d95964827745dab72e5cdd82b5d453aab436129b2d5d5837f8` |
| `plugin/maven/SpiMavenProperties.class` | `141c31b477587cdf671729a4b21a2548f2f53eb55e217905e9c3dc1d14f38e8c` |
| `plugin/maven/SpiMavenService.class` | `e734ced1b15ca8ca0607159cb8cfb2e01e0d1fb37d389e82e67027e986da8975` |

（13 件全量清单：`evidence/hashes/platform-classes.sha256.txt`，1610 B / `3f525133…`）

## 3. Input
### 3.1 触发配置（键面，字节码 VERBATIM）
| 键 | 出处（类/常量池） | 值形态 |
|---|---|---|
| `seeyon.spi.enable` | `SPIApplicationRunListener` 常量池 `#5/#66 = Utf8 seeyon.spi.enable`；`SPIAutoConfiguration` `@ConditionalOnProperty(value=["seeyon.spi.enable"])` | 字符串比较 `"true".equals(prop)` |
| `seeyon.spi`（前缀） | `SPIProperties.PREFIX` `ConstantValue: String seeyon.spi`；`@ConfigurationProperties(prefix="seeyon.spi")` | 绑定前缀 |
| `seeyon.spi.spi-plugins` / `seeyon.spi.spiPlugins` | `SPIConfigChangeEventListener` 常量池 `#16/#96` 与 `#15/#97`（同一判定分支） | `List<String>` |
| `seeyon.dynamic.loader.maven` | `SpiMavenProperties.PREFIX` `ConstantValue` | 4 字段 `snapshotUrl/releaseUrl/username/password` |

### 3.2 `spi-plugins` 三形态（字节码解析，`SPIJarLoader.getFilePath`）
| 形态 | 前缀判定（字节码） | 截断 | 后续 |
|---|---|---|---|
| `maven:group,artifactId,version` | `ldc #10 "maven:"` + `startsWith` | `bipush 6` → `substring(6)` | `split(",")` → trim 后 setGroupId/setArtifactId/setVersion → `SpiArtifactService.download(ArtifactInfo)` |
| `file:/abs/path.jar` | `ldc #26 "file:"` + `startsWith` | `iconst_5` → `substring(5)` | `trim()` 后**直接作为路径** add |
| `oss:group,artifactId,version` | `ldc #27 "oss"` + `startsWith` | `iconst_4` → `substring(4)` | `split(",")` → set… → `EventBus.publish(ArtifactInfo)` → 取 `getFileFullPath()` add |

- `ArtifactInfo` 字段：`appId/groupId/artifactId/version/extension/fileFullPath/file`；`setAppId(Apps.getAppName())` 由平台自动填。
- 客开侧输入（被加载对象）：`META-INF/spring.factories`（接口FQN=实现类FQN）+ `metadata/spi_info.json`（见 SPI-EXT-REG-01）。

## 4. Required
- `seeyon.spi.enable` 必须**字面等于 `"true"`**：`initialize()` 读环境属性后 `ldc #7 "true"` + `String.equals` 判定，
  不等则 `log.warn("应用依赖了SPI插件，但未开启相应功能")` 并 return（字节码 `17: ifne 31` / `23: ldc #10`（UTF-8 还原值见 `evidence/class-constant-strings/loader-utf8-constants.txt`））。
- 双重门（两处判定，字节码均实证）：① 环境属性 `seeyon.spi.enable=="true"`；② 之后 `SPIProperties.isEnable()` 为真，否则 `log.info("未开启SPI插件加载机制，忽略SPI实现的加载")` 并 return。
  - `SPIProperties.enable` **默认 `true`**（`<init>` 内 `iconst_1 → putfield enable`），`spiPlugins` 默认空 `ArrayList`。
- `spiPlugins` 为 `null` 或 `isEmpty()` → `initialize()` 直接 return（不加载）。
- `SPIJarLoader` 依赖注入：`spiArtifactService` `@Autowired(required=false)`；`eventBus` `@Autowired`（默认必需）；
  `SPIConfigChangeEventListener` 的 `spiProperties`/`spiJarLoader` 均 `@Autowired(required=false)`。
- `getFilePath` 异常/空值行为：末元素为 `null` → `log.error("获取的spiPlugins数据有错 spiPluginUrl: [{}]")` + 返回 `Collections.emptyList()`（→ 后续空加载）。
- 缺省与边界（未观测项）：`seeyon.spi.enable` 值为 `"TRUE"`/`1`/yaml 未解析等形态的行为 = `UNVERIFIED`（仅有字节码 `String.equals` 语义，无 LIVE）。

## 5. Execution（链路，逐段带字节码锚点）
引用件：`evidence/javap-code/SPIJarLoader.javap-c.txt`（24182 B / `7e9bbde8…`）、`…/SPIApplicationRunListener.javap-c.txt`（4889 B / `53da4dd2…`）、`…/SPIConfigChangeEventListener.javap-c.txt`（6561 B / `4f5f71d1…`）、`…/SpringDynamicRegister.javap-c.txt`（3110 B / `2f5fb249…`）。行号为该文件内行号。

1. **装配**：平台 `spring.factories`（jar 内 115 B，LF 行尾，sha256 `c970f2dd4ac15a16db1d66b46c3689d763e7c1dd4de0c60cdcc2559c413ccda8`）：
   `org.springframework.boot.autoconfigure.EnableAutoConfiguration=\`⏎`com.seeyon.boot.starter.spi.SPIAutoConfiguration`⏎⏎
   → `SPIAutoConfiguration` 仅在 `seeyon.spi.enable` 存在时生效（`@ConditionalOnProperty`）。
2. **启动链**：`SPIApplicationRunListener.run()` = `initialize()` → `loadExtendsSpi()`（`SPIApplicationRunListener.javap-c.txt` L14–L16）。
3. **门 + 取插件列表**：`initialize()`（同件 L21–L101）：
   `Apps.getEnvironment().getProperty("seeyon.spi.enable")` → `"true".equals` → `Apps.getBeanFactory().getBean(SPIProperties.class)` / `getBean(SPIJarLoader.class)` → `isEnable()` → `getSpiPlugins()` → `spiJarLoader.loadSPIPlugins(list)`。
4. **配置热加载**：`SPIConfigChangeEventListener.onConfigChange(ConfigItemChangeEvent)`（`SPIConfigChangeEventListener.javap-c.txt` L35–L73）：
   遍历 `getChangeData().keySet()`，发现 key `startsWith("seeyon.spi")` → 再筛 `seeyon.spi.spiPlugins` / `seeyon.spi.spi-plugins` → 取 `ChangeItem.getNewValue().toString()`（非空）→ `spiJarLoader.loadSPIPlugins(list)`，并 `log.info("接收到spi配置变化通知，{}， 动态加载spi的插件...")` / `"动态加载spi的插件完成。"`。
5. **三形态解析**：`getFilePath()`（`SPIJarLoader.javap-c.txt` L15–L157，锚点 L39 `54: ldc #10 // String maven:`、L43 `64: bipush 6`、L82 `152: ldc #26 // String file:`、L88 `163: iconst_5`、L94 `181: ldc #27 // String oss`、L98 `191: iconst_4`、L145 错误日志、L153 `317: Collections.emptyList`）。
6. **类加载 + 注册 + 事件**：`loadSPIPlugins(List)` → `loadSPIPlugins(List,true)`（同件 L159–L166 `2: iconst_1`），后者：
   | 步 | 字节码锚点（同件行号） | 动作 |
   |---|---|---|
   | 6.1 | L171 `2: invokespecial #36 // getFilePath` | 取 jar 路径列表 |
   | 6.2 | L189–L200 `File.toURI().toURL()` → `URL[]` | 逐路径转 URL |
   | 6.3 | L209–L216 `Thread.currentThread().getContextClassLoader()` → `new SPIClassloader([URL], ClassLoader)` | 建插件类加载器 |
   | 6.4 | L223–L224 `ldc #52 "META-INF/spring.factories"` → `SPIClassloader.findResources` | 枚举插件 jar 内 spring.factories |
   | 6.5 | L233–L242 `new FileUrlResource(URL)` → `PropertiesLoaderUtils.loadProperties` → `Properties.keySet()` → `Set.addAll` | 汇总接口 FQN 集合 |
   | 6.6 | L246–L251 `ifne 213` / 空则 `log.error("没有发现任何spi接口定义[{}]")` | 空集合告警 |
   | 6.7 | L261–L266 `SPIClassloader.loadClass(FQN)` → `SpringFactoriesLoader.loadFactories(接口Class, classLoader)` | 实例化实现类 |
   | 6.8 | L277–L282 `Apps.getBeanFactory().registerSingleton(provider.getClass().getName(), provider)` | **动态注册进 Spring 容器** |
   | 6.9 | L284–L300 `iload_2`（sendEvent）为真 → `new SPIProviderRegisterEvent` + `setInterfaceName(接口)` + `setSpiProviders(list)` → `eventBus.publish(event)` | **广播注册事件** |
   | 6.10 | L304 / L311 `log.error("加载SPI失败：")` / `"SPI插件加载失败"` | 异常分支（`ClassNotFoundException` 与 `Throwable` 两段 try/catch） |
   事件类型与总线：`com.seeyon.boot.starter.spi.event.SPIProviderRegisterEvent`、`com.seeyon.boot.starter.eventbus.EventBus`（均**不在本 jar 内**，见 §7.4）。
7. **远端/自定义形态**：`loadRemoteSPIPlugins()`（同件 L321–L411）：`new CustomizedSpiInfo()` → `eventBus.publish(该对象)`（**先用事件总线收集**）→ `CollUtil.isNotEmpty(getSpiInfoModels())` →
   `log.info("load custom spi :{}", JsonUtils.toJson(models))` → 逐 model 组 `"file:" + fileFullPath`，`thirdJars` 非空则逐个加 `"file:" + thirdJar` → `loadSPIPlugins(list, true)`；异常 → `log.error("load remote spi error", e)`。
8. **动态注册器**：`SpringDynamicRegister`（`@Component`，`implements ApplicationContextAware`）：`setApplicationContext` → `ConfigurableApplicationContext.getBeanFactory()`；
   `registerBeanDefinition(String, Class<?>)` → `BeanDefinitionBuilder.genericBeanDefinition(Class).getRawBeanDefinition()` → `DefaultListableBeanFactory.registerBeanDefinition(String, BeanDefinition)`；`getBean(String)` → `context.getBean(String)`。
9. **maven 制品获取**：`SpiMavenService`（`@Component` + `@ConditionalOnBean(SpiMavenProperties.class)`，`implements SpiArtifactService, InitializingBean`）：
   `download(ArtifactInfo)` → `getRemoteRepository(String)` → `new RemoteRepository$Builder(...).build()`（含 `setAuthentication(Authentication)` 分支）/ `ArtifactRequest.addRepository(...)`；
   `afterPropertiesSet()` → `getMvnBasePath()`；常量池 ASCII 串 `"mvn"`/`"central"`/`"always"`/`"jar"`/`"]jar"`；失败日志 UTF-8 还原值 `maven私服下载[{}]jar包失败`。
   `SpiMavenProperties` 字段：`snapshotUrl/releaseUrl/username/password`（`PREFIX="seeyon.dynamic.loader.maven"`；常量池另有 `Utf8 seeyon.dynamic.loader`，其键角色 `UNVERIFIED`）。

## 6. Side Effects
| 侧 | 实测结论 |
|---|---|
| 平台容器 | **新增单例 Bean**：`registerSingleton(实现类FQN, 实例)`（§5-6.8，字节码实证） |
| 事件总线 | `EventBus.publish(SPIProviderRegisterEvent)`（§5-6.9）；`oss:` 形态额外 `EventBus.publish(ArtifactInfo)`（§3.2）；`loadRemoteSPIPlugins` 先 `publish(new CustomizedSpiInfo())` 以收集（§5-7） |
| 文件/网络 | `file:` 形态**只读本地路径**；`maven:`/`oss:` 形态会走 `SpiArtifactService.download`（网络下载，实现见 `SpiMavenService`）→ 真实网络副作用**本轮未触发**（P1 禁 LIVE）＝ `UNVERIFIED` |
| 业务数据 | **0**（无任何业务表/业务接口写入面） |
| 本件动作副作用 | **0 写业务数据、0 网络、0 凭据入件**；只读盘 + javap + 写 `core/facts/spi/**` |

## 7. Known Constraints
1. **本地注册 ≠ 部署成功 ≠ 运行态被调用**：本格仅证明 5.3.358 字节码内的加载/注册/事件链；无部署、无 LIVE 观测（P2 范围）。
2. **两处 enable 判定并存**（§4 ① / ②）：环境属性必须字面 `"true"`，且 `SPIProperties.isEnable()` 为真。任一不满足即静默跳过（warn/info 日志）。**该双门语义是否在 3.10.1 家族一致 = UNVERIFIED**。
3. **配置键别名**：字节码同时接受 `seeyon.spi.spiPlugins` 与 `seeyon.spi.spi-plugins`（kebab-case 由 Spring relaxed binding 生效；本格以**字节码字面串**为准，不解释绑定优先级）。
4. **事件类/总线不在本 jar 内**：`com.seeyon.boot.starter.spi.event.SPIProviderRegisterEvent`、`com.seeyon.boot.starter.eventbus.EventBus`
   在 `boot-starter-spi-5.3.358.jar` 内**无定义**（`unzip -l` 实测该 jar 无 `spi/event/` 条目，`grep -c "spi/event"` = 0）→ 其契约属其他 artifact，**本格不宣称其方法面**（仅登记引用点）。
5. **`SpringDynamicRegister` 无本 jar 内调用者**：`grep -rl "SpringDynamicRegister"` 在 jar 内仅命中自身 class → 其装配/被调用路径 = `UNVERIFIED`（不作外推）。
6. **`SpiArtifactService` 的注入实例**：`SpiMavenService` 是本 jar 内唯一实现（`@Component` + `@ConditionalOnBean(SpiMavenProperties.class)`）；`SPIJarLoader.spiArtifactService` 为 `@Autowired(required=false)` → **无实现时可空**，`maven:`/`oss:` 形态在无实现时的行为 = `UNVERIFIED`。
7. **`CustomizedSpiInfo.CUSTOMIZED_SPI_CONFIG_PATH` = `custom-backend/spi_info.json`**（`ConstantValue` 实证），与客开模块在盘资源路径 `metadata/spi_info.json` **不一致**；构建是否重映射 = `UNVERIFIED`（详见 SPI-EXT-REG-01 §7.3）。
8. **javap 中文渲染**：本机 javap 以 GBK 渲染常量池中文，VERBATIM 落盘件中出现乱码字节；**真值以 `class-constant-strings/*-utf8-constants.txt` 为准**（由 `cp_strings.py` 直读 class 常量池还原），两件并存、不互相替换。
9. **随附文档（in-artifact doc）**：`boot-starter-spi-5.3.358.jar!/README.md`（1877 B / `44bf3483…`）记载三形态样例、`SPIProviderRegisterEvent` 字段（`interfaceName` / `spiProviders`）、spring.factories 样例与 maven 坐标 —— 属**实现方随附文档**，只作 `STATIC_CONTRACT` 级辅证，**不替代字节码**。
10. 客开 `README.md` 的文件存储 yaml 片段把 `spiPlugins` 写在 `seeyon.file:` 下（`file.storage-type: spi`），与本格字节码的 `seeyon.spi.*` 前缀**不同** → 记为 `OBSERVATION`（文档转述，本格不裁其正误）。

## 8. Evidence（逐条实测；禁转述）
证据根目录 `core/facts/spi/evidence/`：
**实测件 63 件 / 合计 423320 B**（含清单自身），清单件 `hashes/evidence-inventory.sha256.txt`（6913 B / `27434d484e3b71c2a744a16f659225b377df7618ff87a001035b80e3572f5c7f`，62 行=清单自身除外）。

### E1 artifact sha256
`evidence/hashes/jars.sha256.txt`（242 B / `e7152a13…`）：`boot-starter-spi-5.3.358.jar` = `67b830e4…`（22906 B）；`cip-connector-api-5.3.286.jar` = `de4767da…`（170420 B）。

### E2 jar 内容清单（unzip -l VERBATIM）
`evidence/jar-contents/boot-starter-spi-5.3.358.unzip-l.txt`（2286 B / `b60cde18…`）——29 条目，含 `META-INF/spring.factories`(115 B)、`README.md`(1877 B)、13 class。

### E3 class 字节码 VERBATIM（javap -p / -v / -c）
| 件 | 字节 | sha256 |
|---|---|---|
| `javap-signatures/SPIJarLoader.javap-p.txt` | 665 | `b6c884f0238abb9297c1526720374175ffdb344db111a391958566923b257897` |
| `javap-signatures/SPIProperties.javap-p.txt` | 532 | `f64c9db02c7a8651f8ae8a1c5a26156149f03397e48b888fe981957a2e48e656` |
| `javap-code/SPIJarLoader.javap-c.txt` | 24182 | `7e9bbde8b9ff092c25c192bc59103aea7cb83ddd39d34d6cfc6698c97356bfc8` |
| `javap-code/SPIApplicationRunListener.javap-c.txt` | 4889 | `53da4dd2be550408d1e3930219d8044b675418c3353d5f50cc4cf8cb40ee26c1` |
| `javap-code/SPIConfigChangeEventListener.javap-c.txt` | 6561 | `4f5f71d14ab05bf018f798cc151256d4baeb1ff34b5a12ceb418301f7fd73687` |
| `javap-code/SpringDynamicRegister.javap-c.txt` | 3110 | `2f5fb2499a04529dc4e2a1c9ed066bd745368cc41ecf7221f6290c0587845e34` |
| `javap-code/SpiMavenService.javap-c.txt` | 20603 | `f7da8badd63c6a8bf4fe779ebf7528a8be288030780b3f67deceee1fdf78e9f1` |
| `javap-code/SpiMavenProperties.javap-c.txt` | 9826 | `a8b8079ed5b888532271e24849f5c9f461e4072eb13eee4bfd273fccf39ef83d` |
| `javap-verbose/SPIProperties.javap-v.txt` | 8646 | `c91eade0090605d34a57c6fba484a844b081203b5331d80427c1d2d498927cb0` |
| `javap-verbose/SPIAutoConfiguration.javap-v.txt` | 4347 | `64378d2b81dbf6d0f2a9828d9fcbffcced72a69d5c49ae52f061181ceb5d7e6d` |
| `javap-verbose/SPIJarLoader.javap-v.txt` | 65548 | `90309c06120169c15004b9f1f272b60e519f05dfdf31fcd9df206951da5b464e` |
| `javap-verbose/CustomizedSpiInfo.javap-v.txt` | 6140 | `8313f942c575c1de2bc8514d1a8d848e11850bf7bb150a39e6061de1f26ab266` |
| `javap-verbose/SPIApplicationRunListener.javap-v.txt` | 17079 | `b5c63230ae9acac51a9f09e74b037d412dca6cd38de9e141da4b3643ce035b53` |
| `javap-verbose/SPIConfigChangeEventListener.javap-v.txt` | 21675 | `db6a7508f3d785266e2fc89046fbca0ab183195716c4a5cce2b4489e40376f44` |
| `javap-verbose/SpiMavenService.javap-v.txt` | 56956 | `257c7999d620e5753e788da931513f4d185e6747f9d7b779cd297b341d69a870` |
| `javap-verbose/SpringDynamicRegister.javap-v.txt` | 12522 | `58aa1bd2b65bdaa104589009ab2bbefd7521c8dc9de14219e6827624de845be1` |
| `javap-verbose/SpiMavenProperties.javap-v.txt` | 27459 | `d0c8735ac33aef2c48cd5967bcf398521e00d10558a216c7983685a12fc4e324` |

（其余 6 件签名/verbose：`ArtifactInfo` 1270 B / `aa645d1a…`；`SPIClassloader` 224 B / `74b5a9c1…` 与 2632 B / `93decd27…`；`SpiInfoModel` 911 B / `4d13ef92…` 与 11848 B / `40101d9f…`；`SpiArtifactService` 213 B / `3b45ab32…` 与 1526 B / `e60ce0ea…`；`SPIAutoConfiguration.javap-p.txt` 233 B / `036a6959…`；`SpringDynamicRegister.javap-p.txt` 690 B / `034662f0…`；`SPIConfigChangeEventListener.javap-p.txt` 481 B / `80d9d63a…`。全量 62 件 sha256 见 `hashes/evidence-inventory.sha256.txt`。）

### E4 平台 `spring.factories`（jar 内 VERBATIM 副本 + 字节形态）
`platform-jar-resources/boot-starter-spi-META-INF-spring.factories.txt`（115 B / `c970f2dd…`）：`od -c` 实测 LF=3 / CR=0（**LF 行尾**），内容 = `org.springframework.boot.autoconfigure.EnableAutoConfiguration=\`⏎`com.seeyon.boot.starter.spi.SPIAutoConfiguration`⏎⏎。

### E5 常量池真值（UTF-8 还原，修正 javap 乱码）
- `class-constant-strings/loader-utf8-constants.txt`（10788 B / `dd29d074…`）——`SPIApplicationRunListener` / `SPIJarLoader` / `SPIConfigChangeEventListener` 三件常量池全文。
  关键还原值：`应用依赖了SPI插件，但未开启相应功能`、`未开启SPI插件加载机制，忽略SPI实现的加载`、`获取的spiPlugins数据有错 spiPluginUrl: [{}]`、`没有发现任何spi接口定义[{}]`、`加载SPI失败：`、`SPI插件加载失败`、`load custom spi :{}`、`load remote spi error `、`接收到spi配置变化通知，{}， 动态加载spi的插件...`、`动态加载spi的插件完成。`
- `class-constant-strings/maven-and-registrar-utf8-constants.txt`（13216 B / `3389e861…`）——含 `maven私服下载[{}]jar包失败`。
- 还原工具随证据留档：`class-constant-strings/cp_strings.py`（1395 B / `356b96e6…`）。

### E6 平台 README（jar 内随附文档，VERBATIM）
`platform-jar-resources/boot-starter-spi-README.md`（1877 B / `44bf3483…`）：三形态样例、`SPIProviderRegisterEvent{interfaceName, spiProviders}`、spring.factories 样例、`com.seeyon:boot-starter-spi` 坐标、`seeyon.spi.enable/spi-plugins` yaml 样例。

### E7 引用关系实测（用于 §7.4/§7.5 结论）
- `grep -c "spi/event" <jar 清单>` = **0**（事件类不在本 jar）。
- `grep -rl "SpringDynamicRegister"`（解包目录）→ 仅自身 class；`SPIProviderRegisterEvent` → 仅 `SPIJarLoader.class` 与 `README.md`；`SPIConfigChangeEventListener` → 仅自身 class。

## 9. Verified（逐项等级 + 未直读项）
| 项 | 等级 | 依据 |
|---|---|---|
| 自动装配入口与开关键（`@Configuration`/`@EnableConfigurationProperties`/`@ConditionalOnProperty("seeyon.spi.enable")`） | **VERIFIED_STATIC_BYTECODE** | E3 `SPIAutoConfiguration.javap-v.txt`（`RuntimeVisibleAnnotations`）+ E4 |
| `SPIProperties`（`prefix="seeyon.spi"`、`@ConfigAutoRefresh`、`enable` 默认 `true`、`spiPlugins` 默认 `ArrayList`） | **VERIFIED_STATIC_BYTECODE** | E3 `SPIProperties.javap-v.txt`（字段 `ConstantValue` / `<init>` 字节码 / 注解） |
| 启动链 `run()→initialize()+loadExtendsSpi()`、双门 enable 判定 | **VERIFIED_STATIC_BYTECODE** | E3 `SPIApplicationRunListener.javap-c.txt` L14–L101 + E5 |
| `spi-plugins` 三形态解析（`maven:`(6)/`file:`(5)/`oss`(4) + `split(",")`） | **VERIFIED_STATIC_BYTECODE** | E3 `SPIJarLoader.javap-c.txt` L39–L101 |
| 扫描 `META-INF/spring.factories` → `Properties` → 接口集合 | **VERIFIED_STATIC_BYTECODE** | 同上 L223–L251 |
| `SpringFactoriesLoader.loadFactories` 实例化 + `registerSingleton(FQN, 实例)` 动态注册 | **VERIFIED_STATIC_BYTECODE** | 同上 L261–L282 |
| `SPIProviderRegisterEvent` 广播（`setInterfaceName`/`setSpiProviders`/`EventBus.publish`） | **VERIFIED_STATIC_BYTECODE**（**引用点**） | 同上 L284–L300；事件类本体不在本 jar（§7.4） |
| Nacos 配置变更触发重载（`seeyon.spi` 前缀 + 两键别名 + `loadSPIPlugins`） | **VERIFIED_STATIC_BYTECODE** | E3 `SPIConfigChangeEventListener.javap-c.txt` L35–L73 + `@EventHandler`/`@EventSubscribe`（javap -v） |
| `loadRemoteSPIPlugins`（`CustomizedSpiInfo` 收集 → `file:` 形态 → `loadSPIPlugins(list,true)`） | **VERIFIED_STATIC_BYTECODE** | E3 `SPIJarLoader.javap-c.txt` L321–L411 |
| `SpringDynamicRegister` 方法面（`registerBeanDefinition`/`getBean`，`@Component`） | **VERIFIED_STATIC_BYTECODE** | E3 `SpringDynamicRegister.javap-c.txt` L24–L47；**调用者 UNVERIFIED**（§7.5） |
| `SpiMavenService`/`SpiMavenProperties` 结构（`@Component`+`@ConditionalOnBean`、`PREFIX=seeyon.dynamic.loader.maven`、aether `RemoteRepository`） | **VERIFIED_STATIC_BYTECODE** | E3 `SpiMavenService.javap-v/-c`、`SpiMavenProperties.javap-v` |
| 三形态语义细节（oss 摆渡桶路径、maven 私服 URL） | **STATIC_CONTRACT（随附文档级）** | E6（jar 内 README，非字节码逻辑） |
| 运行态：SPI 插件在 test2 的实际加载/调用 | **UNVERIFIED（P2 范围）** | §7.1 |
| 对 `platform.version=3.10.1` 的适用性 | **UNVERIFIED** | §2 版本缺口 |
| `maven:`/`oss:` 形态的真实网络下载副作用 | **UNVERIFIED（本轮未触发）** | §6 |
| 事件类/EventBus 方法面 | **UNVERIFIED（不在本 artifact）** | §7.4 |
| 客开 README 的 `seeyon.file.*` spiPlugins 片段 | **OBSERVATION** | §7.10 |

**未直读项（如实登记）**：无 LIVE、无部署、无构建产物；事件总线与事件类契约属其他 artifact（本格只登记引用点）；
`seeyon.dynamic.loader` 键角色未定；`SpringDynamicRegister` 调用路径未定。本件**未改 `INDEX.md`/`STATUS.md`、未碰其他 `core/facts` 目录、凭据 0 入件**。

## 溯源索引（可复现）
| 项 | 路径 |
|---|---|
| jar sha256 | `core/facts/spi/evidence/hashes/jars.sha256.txt` |
| platform class sha256（13 件） | `core/facts/spi/evidence/hashes/platform-classes.sha256.txt` |
| jar 清单 | `core/facts/spi/evidence/jar-contents/boot-starter-spi-5.3.358.unzip-l.txt` |
| 字节码 VERBATIM | `core/facts/spi/evidence/javap-signatures/`、`javap-verbose/`、`javap-code/` |
| 常量池真值 | `core/facts/spi/evidence/class-constant-strings/`（含 `cp_strings.py`） |
| 平台 spring.factories / README / MANIFEST | `core/facts/spi/evidence/platform-jar-resources/` |
| 全证据 sha256 清单 | `core/facts/spi/evidence/hashes/evidence-inventory.sha256.txt` |
| 复算命令（实测） | `sha256sum`；`unzip -l/-o`；`cmp`；`od -c`；javap=`"C:/Program Files/Java/latest/jdk-21/bin/javap.exe" -p[-c/-v] -cp <jar> <FQN>` |

> 自报：本件与 `spi-ext-registration.md` 同批落盘；证据 63 件 / 423320 B；§7.4/§7.5 的「不在本 jar / 无调用者」均由 `grep -rl` + `unzip -l` 实测得出。写后实测字节数见 RESULT（此处不回填以免自指漂移）。
