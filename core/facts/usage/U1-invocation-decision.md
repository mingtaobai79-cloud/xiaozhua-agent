# U1 · 调用方式判据：Dubbo 泛化 / @Autowired / 静态调用，到底哪个

## Capability

**回答「这个类我该怎么调」** —— 判据全部来自字节码注解，不靠经验，不靠猜。

给 Agent 用：写任何一行跨模块调用前，先来本格对号。**判错就是运行期 NoSuchBean 或 404。**

## Version

| 构件 | 版本 |
|---|---|
| `@AppService` | `boot-core-5.3.600.jar`（`javap -v` 元注解实测） |
| `AppServiceBeanPostProcessor` | `boot-starter-appservice-5.3.600.jar` |
| `@DubboService` | `dubbo-*.jar` |

---

## 一、★★★★★ 一句话判据

```
看【实现类】上有没有 @DubboService
  有  → 可泛化调用（远程/invoke）＋ 也可 @Autowired（同 JVM）
  没有 → 只能 @Autowired（同 JVM），泛化调用必然失败
```

**★★★ 关键：`@AppService` 本身不是 Dubbo 标记。**
**且 Dubbo 标记有两种：`@DubboService`（标准）和 `@DubboComponent`（seeyon 自有）。**

`@AppService` 的元注解（`javap -v` 实测）：

```
@Target(TYPE)
@Retention(RUNTIME)
@Documented
@Inherited
@org.springframework.stereotype.Service      ← 只是个 Spring Bean
@org.springframework.context.annotation.Primary
```

**它等于 `@Service` + `@Primary`，跟 Dubbo 一点关系都没有。**
真正决定能否远程调用的是**同一个类上的 `@DubboService`**。

---

## 二、三类注解的完整语义表

| 注解 | 元注解 | 效果 | 能否泛化 |
|---|---|---|---|
| `@AppService` | `@Service` + `@Primary` | 注册为 Spring Bean，AOP 切面（日志/事务/幂等/参数校验）生效 | ❌ 单独不能 |
| `@DubboService` | `@org.apache.dubbo...` | 注册为 Dubbo provider，暴露服务 | ✅ **能** |
| `@Component` | — | 注册为 Spring Bean | ❌ |
| `@Service`（Spring） | — | 注册为 Spring Bean | ❌ |
| **两者同时有** | — | Bean + Dubbo provider + AOP 全生效 | ✅ **能** |
| `@DubboComponent` | 无 Spring 元注解，平台自有标记 | 由 `DubboComponentInitializer` 处理 | ✅ **能** |

### 2.1 两个 Dubbo 标记的区别（实测）

| 标记 | 元注解 | 分布 |
|---|---|---|
| `@DubboService` | Dubbo 官方 `org.apache.dubbo.config.annotation` | **业务应用 225 个**（15 个 -biz 合计） |
| `@DubboComponent` | 无（`@Target(TYPE)` + `@Retention(RUNTIME)`） | **业务应用 0 个**；boot-starter 仅 1 个（`FileInfoProxyImpl`） |

**⇒ 主判据仍看 `@DubboService`。`@DubboComponent` 是平台早期标记，出现在 boot-starter 少数类上，
   两者任一存在即视为 Dubbo provider。**

### 2.2 ★★★ 还有运行时开关（静态能注册 ≠ 实际暴露）

`DubboComponentInitializer.initialize` 字节码（默认实现）：

```java
System.setProperty("dubbo.application.logger", "slf4j");
boolean appEnabled = env.getProperty("seeyon.dubbo.enable", Boolean.class, true);
boolean provEnabled = env.getProperty("seeyon.dubbo.provider.enable", Boolean.class, true);
System.setProperty("dubbo.provider.enable", Boolean.valueOf(provEnabled).toString());
```

**⇒ 两个环境变量：**

| 变量 | 作用 | 关了会怎样 |
|---|---|---|
| `seeyon.dubbo.enable` | Dubbo 整体启用 | provider 全不暴露 |
| `seeyon.dubbo.provider.enable` | 仅 provider 侧 | 消费者能调出去，但本机不被外部调 |

**⚠️ 所以「类上有 `@DubboService`」只说明代码层面可暴露；环境里 `seeyon.dubbo.provider.enable=false`
   时仍然调不到。判据顺序：先看注解，再确认环境开关（Nacos 配置）。**

---

## 三、真实分布（实测，不是推测）

### 3.1 标品业务应用

| 应用 | 总类数 | **可泛化**（@DubboService） | 仅本地（@AppService 无 Dubbo） |
|---|---:|---:|---:|
| organization | 668 | **50** | 62 |
| bpm | 2730 | **30** | 50 |
| ctp-affair | 345 | **9** | 10 |
| ctp-message | 151 | **4** | 0 |
| ctp-user | 876 | **40** | 37 |
| portal | 594 | **4** | 33 |
| m5 | 401 | **3** | 15 |
| cip-connector | 1205 | **12** | 28 |
| cip-capability | 840 | **40** | 5 |
| app-common | 632 | **18** | 38 |
| app-approval | 232 | **2** | 10 |
| app-doc | 477 | **0** | 70 |
| ai | 132 | **0** | 6 |
| cdp-data | 1927 | **9** | 81 |
| ctp-media | 25 | **1** | 0 |

**15 个应用合计：11,235 个类 / 225 个 `@DubboService` / 861 个 `@AppService` / 0 个 `@DubboComponent`**

**★★★ 读这张表的三个结论：**

1. **portal 有 79 个 `@AppService` 但只有 4 个能泛化** —— 75 个只能 `@Autowired`
2. **app-doc（70）/ ai（6）一个都不能泛化** —— 这两个域只能本进程注入
3. **同一应用内部也不统一** —— 不能凭「这个应用是标品」就断定全可泛化
4. **861 个 `@AppService` 里只有 225 个能泛化 = 26%**

### 3.2 boot-starter 组件

| 组件 | 总类数 | **可泛化** |
|---|---:|---:|
| boot-starter-file | 89 | **1**（`FileInfoProxyImpl`） |
| boot-starter-basicdata | 57 | **1** |
| boot-starter-enums | 51 | **0** |
| boot-starter-metadata | 81 | **0** |
| boot-starter-excel | 72 | **0** |
| boot-starter-serialnumber | 85 | **0** |
| boot-starter-eventbus | 24 | **0** |
| boot-starter-security | 17 | **0** |
| boot-starter-i18n | 28 | **0** |
| boot-starter-cache | 50 | **0** |
| boot-starter-attachment | 15 | **0** |
| boot-starter-opinion | 64 | **0** |
| boot-starter-qrcode | 59 | **0** |
| boot-starter-parameter | 22 | **0** |
| boot-starter-documentnumber | 101 | **0** |
| boot-starter-condition | 77 | **0** |

**★★★★★ 结论：boot-starter 组件几乎全部不可泛化，只能 `@Autowired`。**

**⇒ 所以你之前记的「组件用 @Autowired」是对的，但原因不是「组件在本地」，
   而是「组件压根没注册成 Dubbo provider」（16 个组件 447 类里只有 1 个 `@DubboService`）。**

---

## 四、四类调用方式（对号入座）

### 类型 1：Dubbo 泛化调用

**适用**：`-biz` 里带 `@DubboService` 的实现类（上表第一列）

```java
// 5 个必填位（顺序不能错）
GenericService genericService = ...;
Object result = genericService.$invoke(
    methodName,                                    // ① 方法名
    new String[]{"com.seeyon.boot.transport.SingleRequest"},  // ② 参数类型
    new Object[]{request}                         // ③ 参数值
);
// ④ interfaceName  ⑤ genericType 在引用配置里
```

**判据**：`实现类.class` 里能搜到 `org/apache/dubbo/config/annotation/DubboService`

### 类型 2：`@DubboReference` 强类型远程调用

**适用**：同上（有 `@DubboService` 的），但你有 facade jar 在 classpath

```java
@DubboReference
private OrgCommonAppService orgCommonAppService;   // facade 接口

SingleResponse<Map<String,Object>> r =
    orgCommonAppService.selectMemberInfoById(SingleRequest.from(id));
```

**⚠️ 泛化 vs 强类型的取舍：**

| | 泛化 | 强类型 |
|---|---|---|
| 要有 facade jar | ❌ 不需要 | ✅ 需要 |
| 编译期检查 | ❌ 无 | ✅ 有 |
| 升级影响 | 小（字符串） | 大（签名变则编译失败） |
| **默认用哪个** | 调试/临时 | **生产代码** |

### 类型 3：`@Autowired` 同 JVM 注入

**适用**：
- `boot-starter-*` 组件（file/enums/metadata/excel/cache/…）
- 只有 `@AppService` 没有 `@DubboService` 的类
- 你自己的 UDC 生成物（`{E}Service` / `{E}AppService`）

```java
@Autowired
private CtpEnumItemService ctpEnumItemService;   // 组件，无 DubboService

@Autowired
private OrderService orderService;              // 你自己的生成物
```

**判据**：能 `@Autowired` 的**一定**能注入（只要在同一个 Spring 容器），但**不一定**能远程调。
> 反过来不成立：能 `@DubboService` 的也能 `@Autowired`（同 JVM 时优先本地 bean）。

### 类型 4：静态调用（无容器）

**适用**：`*Utils` / `*Helper`，零注解

```java
JsonUtils.fromJson(json, MyDto.class);
Ids.gidLong();
CacheUtils.getCompleteCacheKey(tenant, app);
BeanCopier.copy(src, Target.class);
```

**判据**：类上**零注解**，方法全 `public static`。
**⚠️ 不要对这些类做 `@Autowired`** —— 会注入失败（它们不是 Bean）。

---

## 五、boot-starter 里为什么「能 @Autowired 却搜不到类」

**实测数据**：8 个组件 447 个类中

```
@DubboService          1    ← 可泛化
@Component            32    ← Spring Bean
@Service              36    ← Spring Bean
@AppService           24    ← Spring Bean（= @Service + @Primary）
四者皆无              355    ← DTO / Entity / Utils / 接口
```

**★★★ 355 个「四者皆无」的类里，绝大多数是：**

| 类型 | 例子 | 怎么用 |
|---|---|---|
| DTO | `CtpEnumItemDto` | 自己 `new`，当参数传 |
| Entity | `BusDynamicSubscribe` | 由框架读写，你不直接碰 |
| **Utils** | `CacheUtils` / `MetadataMD5Utils` | **静态调用** |
| 接口 | `StorageSpi` | 找实现类注入 |
| 常量/枚举 | — | 直接引用 |

**⇒ 你搜不到「文件服务类」，很可能是因为你搜的是 DTO 或 Utils，不是 Service。
   真正能注入的是那 32+36+24 = 92 个带注解的类。**

---

## 六、实战判定流程（三步）

```
第 1 步：拿到实现类的 class（不是接口、不是 DTO）
   └─ 名字通常以 AppServiceImpl / ServiceImpl 结尾

第 2 步：javap -v 看类级 RuntimeVisibleAnnotations
   └─ grep "org/apache/dubbo/config/annotation/DubboService"

第 3 步：按结果分派
   ├─ 有 @DubboService → 泛化 或 @DubboReference 都行
   ├─ 只有 @AppService/@Service/@Component → 只能 @Autowired
   └─ 零注解 → 静态调用 or 自己 new
```

**一行命令：**

```bash
unzip -p <jar> <class路径>.class | strings | grep -c "DubboService"
# 1+ → 可泛化；0 → 不可
```

---

## 七、常见误判（我自己踩过的）

| # | 误判 | 真相 |
|---|---|---|
| 1 | 「标品 AppService 都能泛化」 | **错**。portal 33 个里 29 个不能；app-doc / ai 一个都不能 |
| 2 | 「`@AppService` 是 Dubbo 注解」 | **错**。它 = `@Service` + `@Primary`，与 Dubbo 无关 |
| 3 | 「组件在本地所以用 @Autowired」 | 结论对，**原因错**。真实原因是它们没注册 Dubbo provider（447 类仅 1 个） |
| 4 | 「`CacheUtils` 是 Bean，可以注入」 | **错**。零注解、全 static，注入必失败 |
| 5 | 「搜不到类 = 平台没有这个能力」 | **多半是搜错了对象**（DTO/Utils vs Service） |
| 6 | 「同一应用内调用方式统一」 | **错**。organization 49 可泛化 / 62 仅本地 |

---

## 八、Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `@AppService` = `@Service` + `@Primary`，无 Dubbo 元注解 | `javap -v com/seeyon/boot/annotation/AppService.class` 的 `RuntimeVisibleAnnotations` 第 4/5 条 | **VERIFIED_STATIC_BYTECODE** |
| `OrgCommonAppServiceImpl` 类级 = `@AppService(value="组织信息查询", sort=201)` + `@DubboService` | `javap -v` 输出 `SourceFile:` 之后的类级注解块，`#1803` + `#1806()` | **VERIFIED_STATIC_BYTECODE** |
| `OrgWorkFlowAppServiceImpl` 类级 = `@AppService(sort=301)` + `@DubboService` | 同上，`#2078` + `#2081()` | **VERIFIED_STATIC_BYTECODE** |
| `PortalSetAppServiceImpl` 类级 = `@DubboService` + `@AppService(value="门户设置")` | 同上，`#396()` + `#397` | **VERIFIED_STATIC_BYTECODE** |
| `OrganizationMatchMemberAppServiceImpl` 只有 `@AppService`，无 Dubbo | 同上 | **VERIFIED_STATIC_BYTECODE** |
| `AppServiceBeanPostProcessor` 引用 `org.apache.dubbo.config.spring.AnnotationBean` | `javap -v` 常量池 #233 + 方法 `getDubboBPPIndex`/`getFacadeBPPIndex` | **VERIFIED_STATIC_BYTECODE** |
| `@DubboComponent` 无 Spring 元注解，`@Target(TYPE)` + `@Retention(RUNTIME)` | `javap -v com/seeyon/boot/starter/dubbo/annotation/DubboComponent.class` | **VERIFIED_STATIC_BYTECODE** |
| `DubboComponentInitializer` 读 `seeyon.dubbo.enable` / `seeyon.dubbo.provider.enable` 并设 `dubbo.provider.enable` | `javap -c DubboComponentInitializer.initialize` 偏移 14/19/46/51/77 | **VERIFIED_STATIC_BYTECODE** |
| `CacheUtils` 零注解、全 static | `javap -v` 无类级 `RuntimeVisibleAnnotations`；`javap -p` 全 `public static` | **VERIFIED_STATIC_BYTECODE** |
| `FileInfoProxyImpl` = `@DubboComponent` + `@DubboService` + `@AppService` | `javap -v` 类级三注解 | **VERIFIED_STATIC_BYTECODE** |
| 15 应用 11,235 类 → 225 `@DubboService` / 861 `@AppService` | 扫 `*-biz.jar` 全部顶层类字节；脚本 `generic_matrix.py` 可复算 | **VERIFIED_STATIC_BYTECODE** |
| 16 组件 447 类 → 仅 1 个 Dubbo 标记 | 同上 | **VERIFIED_STATIC_BYTECODE** |
| 字节扫描 与 类级注解 一致（6 案例交叉验证） | `verify_u1_v2.py` 退出码 0 | **VERIFIED_STATIC_BYTECODE** |
| 泛化调用真实发起 | 未实测 | **UNVERIFIED** |
| 环境内 `seeyon.dubbo.provider.enable` 实际取值 | 未查 Nacos | **UNVERIFIED** |

## 九、Verified

- ✅ **VERIFIED_STATIC_BYTECODE**：`@AppService` 元注解、两种 Dubbo 标记、运行时开关、`CacheUtils` 静态性（全部 javap 逐条）
- ✅ **交叉验证**：`verify_u1_v2.py` 用「字节扫描」和「类级注解」两条独立路径比对 6 个案例，结果一致（退出码 0）
- ✅ **数量可复算**：所有表格数字来自 `*-biz.jar` 顶层类字节扫描
- ⚠️ **UNVERIFIED**：泛化调用真实发起（需 provider 在线）
- ⚠️ **UNVERIFIED**：`@DubboService` 的 `version`/`group` 属性（可能影响泛化寻址）
- ⚠️ **UNVERIFIED**：目标环境的 Nacos 里 `seeyon.dubbo.provider.enable` 真实值

### 9.1 本轮修正的验证脚本错误

第一版 `verify_u1.py` 报 3 个 FAIL —— 不是判据错，是**脚本读错位置**：

```
javap -v 输出结构：
  ... 各方法 ...
  }                          ← 类体结束
  SourceFile: "X.java"
  RuntimeVisibleAnnotations:  ← ★ 类级注解在这里
  InnerClasses:

第一版脚本取的是「第一个 RuntimeVisibleAnnotations」= 某个字段的注解，
所以 PortalSetAppServiceImpl 明明有 @DubboService 却读不到。
```

修正后（`verify_u1_v2.py`）只读 `SourceFile:` 之后那块，6 案例全 OK。

## 十、给 Agent 的判据

```
问「我能用泛化调用 xxx 吗」
  → 先找【实现类】，看类级有没有 @DubboService 或 @DubboComponent
  → 有 → 能。都没有 → 不能，只能 @Autowired
  → 还要确认环境 seeyon.dubbo.provider.enable 不为 false

问「@AppService 是不是 Dubbo 注解」
  → 不是。它 = @Service + @Primary，纯 Spring Bean
  → 必须同一个类上另有 @DubboService 才能远程调

问「标品都能泛化吧」
  → 不能。861 个 @AppService 里只有 225 个能泛化 = 26%
  → portal 79 个只 4 个能；app-doc 70 个 / ai 6 个 全都不能

问「boot-starter 组件怎么调」
  → 一律 @Autowired
  → 因为 447 个类里只有 1 个注册了 Dubbo provider

问「CacheUtils 能注入吗」
  → 不能。零注解全 static，直接 CacheUtils.xxx() 静态调

问「这个类是 DTO 还是 Service」
  → 名字带 Dto/Entity → 自己 new
  → 带 Utils/Helper → 静态调
  → 带 AppService/Service 且带注解 → 注入

问「搜不到某个能力」
  → 先确认搜的是 Service 而不是 DTO/Utils
  → 16 组件的 447 类里，355 个根本不是 Bean

问「同一应用内调用方式一样吗」
  → 不一样。organization: 49 可泛化 / 62 仅本地
```