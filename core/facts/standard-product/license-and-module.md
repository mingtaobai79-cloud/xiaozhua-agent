# 授权（license）与模块扩展（module）

## Capability

```
boot-starter-license       运行时授权读取与校验（插件、产品号、组织数、租户模式）
boot-license-generator     授权文件生成（RSA 密钥对 + 加解密 + LicenseDto）
boot-starter-module        模块级扩展：@ModuleEnhance、动态缓存、模块加载事件
```

## Version

`license` 5.3.600 / `license-generator` 2.6.0 / `module` 5.3.600。

## ★ 一、运行时授权（boot-starter-license）

```java
LicenseController extends BaseComponentController
  SingleResponse<Boolean>       hasPlugin(Map<String,String>);
  SingleResponse<Set<String>>   getPlugins(Long);
  SingleResponse<Map<String,String>> getProductNo(Long);
  SingleResponse<String>        createOrUpdate(LicenseInfoDto);

LicenseProcessor（接口，平台按产品线给实现）
  boolean init();
  boolean isTenantMode();
  Set<String>          getPlugins();
  Map<String,List>     getAppPlugins();
  String               getProductInfo();
  boolean hasApp(String);
  int     getOrganNum();          // ★ 授权组织数
```

现成实现：`DevelopLicenseProcessorImpl implements LicenseProcessor`（开发版）。

落库：`LicenseInfo` / `LicenseInfoDao` / `LicenseInfoService`。

## ★ 二、授权生成（boot-license-generator，独立小工具）

```java
LicenseGenerator
  static String generateLicenseInfo(LicenseDto);
  static String generateLicenseInfo(LicenseDto, String privateKey);
  static EncryptKeyPair generateKeyPair();          // publicKey / privateKey

LicenseEncryptor
  static String encrypt(String);
  static String decrypt(String);

LicenseDto / EncryptKeyPair / KryoUtil / JsonUtils（自带，不依赖 boot 其他包）
```

⇒ 发授权：`generateKeyPair()` → 私钥签 `LicenseDto` → 生成字符串 → 交付；
升级：换密钥对会让**已发授权全部失效**。

## ★ 三、模块扩展（boot-starter-module）

```java
@ModuleEnhance                       // 模块增强注解（无属性）
LocalDynamicCache implements InitializingBean
  void addDynamicInfo(Map<String,String>);
  List<Map<String,String>> getDynamicInfoCache();
  Set<String> getLocalDynamicName();
  boolean isLocalDynamic(String name);

CacheOperation                        // 缓存操作描述：getCacheKey / getCacheOperationType / getCachePrefix / getCacheName
CacheOperationType                    // 操作类型枚举
ProcessorTypeConstants
ModuleAppLoadEventHandler             // 模块应用加载事件
```

⇒ 动态（热加载）模块的类名/处理器登记走 `LocalDynamicCache`；
业务代码判断「这个类是不是动态加载来的」用 `isLocalDynamic(name)`。

## Side Effects

- `createOrUpdate` 改的是授权记录，直接写在跑着的应用上，误操作会导致功能被锁。
- `generateKeyPair` 生成新密钥对后，**旧授权无法再用新公钥验证**。
- `LocalDynamicCache.addDynamicInfo` 是内存态，重启后重建（靠 `afterPropertiesSet`）。

## Known Constraints

1. 授权校验点是**插件/应用/组织数**三个维度，`hasPlugin` 传的是 `Map<String,String>` 不是字符串。
2. `LicenseProcessor` 是接口，注入时可能拿到 `DevelopLicenseProcessorImpl`（开发版恒通过）。
3. `@ModuleEnhance` 没有属性，纯标记；真正生效靠 `ModuleAppLoadEventHandler` 这条链。
4. `boot-license-generator` 版本线是 2.6.0，与其他 5.3.x 不同族，**别按 5.3 找 jar**。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `LicenseController` 4 方法 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `LicenseProcessor` 7 抽象方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `LicenseGenerator` 3 静态方法 + `LicenseEncryptor` 2 方法 | `javap -p` 2.6.0 | VERIFIED_STATIC_BYTECODE |
| `LocalDynamicCache` 5 方法 / `CacheOperation` 4 方法 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `@ModuleEnhance` 无属性 | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与签名可复核
- ⚠️ 未真机验授权（无授权文件）

## 给 Agent 的判据

```
要判功能是否授权     → LicenseController.hasPlugin / LicenseProcessor.hasApp
要查授权组织数       → LicenseProcessor.getOrganNum()
要生成授权           → LicenseGenerator.generateLicenseInfo(dto, privateKey)
要判是否动态加载类    → LocalDynamicCache.isLocalDynamic(name)
```
