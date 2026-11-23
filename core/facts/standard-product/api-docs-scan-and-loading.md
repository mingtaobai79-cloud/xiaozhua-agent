# 接口文档 · 索引合并 · 元数据扫描 · 动态模块加载

## Capability

四个「平台自举」组件，客开通常在**排查为什么接口/元数据没生效**时用到：

```
boot-starter-swagger        接口文档分组与缓存（DTO 扫描）
boot-starter-index          索引数据合并（EntityData → GlobalIndexInfo）
boot-starter-scanner        启动时扫描元数据并注册（starter/模块应用）
boot-starter-dynamicloader  动态模块加载（上传即加载，重启不丢）
```

## Version

均 5.3.600 系（`index` 5.3.265）。

## ★ 一、swagger

```java
SeeyonSwaggerCache.dtoMap                    // static Set<String>：已收录 DTO
SeeyonSwaggerConstants
  DY_CLASS_PREFIX / GROUP_NAME_DEFAULT / GROUP_NAME_METADATA / GROUP_NAME_STARTER / GROUP_ENABLE
```

插件式修正（jsr303 注解 → swagger 文档）：

```
SeeyonDateAnnotationPlugin / SeeyonDigitsAnnotationPlugin / SeeyonNotNullAnnotationPlugin
CustomVendorExtension
```

⇒ 接口文档按 **三组**（default / metadata / starter）输出，`GROUP_ENABLE` 控制开关。
新增 AppService 后文档没出现 → 先看 `dtoMap` 是否收录、再看分组开关。

## ★ 二、index（数据合并，不是 ES 索引）

```java
EntityDataCombiner.combine(EntityDataInfo, EntityMetadataDto, DataProcessorService) → GlobalIndexInfo
ContentComparator.compare(Integer,Integer) / compare(Object,Object)
DataProcessorManager / DataProcessorTask / EntityDataListener
EntityDataCombiner.EDOC_COLUMN_ENTITY_DRAFT_UNIT / ..._REGISTER_UNIT / ..._HOST_DEPARTMENT
```

这是**平台全局索引/聚合**的数据合并层（公文类字段映射常量即为证据），
不是 `boot-starter-elasticsearch` 那套检索。

## ★ 三、scanner（元数据注册的关键）

```java
MetadataScanner implements SeeyonApplicationRunner, ApplicationListener<ModuleUnloadEvent>
  void run();                                        // 启动时执行
  void registerCurrentAppDynamicMetadata(List<Class>, List<Class>, List<Class>, List<Class>, List<Class>, EntityMetadataDto);
  long registerDynamicAppMetadata(String, String, String, String, String, BuildInfo, ServiceStatusEnum, String, String, String);
  long registerModuleAppMetadata(ModuleAppClassLoader, String, ModuleMetaInfo, BuildInfo, ServiceStatusEnum, String, String, String);

MetadataScannerUtils
  static Map<String, StarterMetadataDto> scanStarterInfoMetadata(String);
  static void removeParameterNamesCache(List<Class>);
  static <V> Map<String,V> buildStarterMetadataMap(String, Map<String,V>);
  static MetadataClassLoader getClassLoader(String);
```

⇒ **AppService/DTO 之所以能被 GraphQL 找到，靠这里注册**。
「接口 404 / op 不存在」的第一现场就是 scanner 有没有扫到你的类。

## ★ 四、dynamicloader（动态模块）

```java
DynamicLoaderAppService.selectPageByConditions(PageRequest)   // 已加载模块分页
DynamicModuleController / DynamicModuleService / CtpDynamicModule
InitDataCallback.initBasicData(Long, String)                  // 加载后初始化基础数据
```

## Side Effects

- `MetadataScanner.run()` 在启动期跑，重即可感知启动变慢。
- 动态加载的模块**与主应用共享上下文**，卸载走 `ModuleUnloadEvent`（scanner 监听它清理元数据）。
- 索引合并（index）写的是全局索引表，误合并会污染检索结果。

## Known Constraints

1. `index` 与 `elasticsearch` 是两个包、两件事，别相互引用找答案。
2. scanner 的注册方法参数长（5~11 个 `String`），**不要手调**——靠启动自动跑。
3. 动态模块的类加载器是 `ModuleAppClassLoader`，跨模块强转会 `ClassCastException`。
4. swagger 三组开关是全局的，关掉 `GROUP_ENABLE` 后所有分组都不出文档。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `SeeyonSwaggerCache.dtoMap` + 5 个常量 + 3 个 jsr303 插件 | `javap -p` | VERIFIED_STATIC_BYTECODE |
| `EntityDataCombiner.combine` + 3 个列常量 | 同上 | VERIFIED_STATIC_BYTECODE |
| `MetadataScanner` 4 方法（含 3 个 register*） | 同上 | VERIFIED_STATIC_BYTECODE |
| `MetadataScannerUtils` 4 静态方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `DynamicLoaderAppService` / `InitDataCallback` | 同上 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与签名可复核
- ⚠️ 未做「删掉注册后 op 消失」的反向验证（属运行期实验）

## 给 Agent 的判据

```
新接口 GraphQL 找不到    → 先确认 MetadataScanner 启动日志扫到了你的 AppService
接口文档没出现          → SeeyonSwaggerCache.dtoMap + GROUP_ENABLE
要动态加载模块          → dynamicloader（CtpDynamicModule + InitDataCallback）
全局索引数据怎么合并     → boot-starter-index 的 EntityDataCombiner（不是 ES）
```
