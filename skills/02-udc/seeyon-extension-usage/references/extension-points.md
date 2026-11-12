# 扩展点速查（写代码前先定位）

权威表在 `core/facts/standard-product/extension-point-decision-table.md`（60 行场景表）。
本文件是**动手版**：按「我要干什么」直接给接口名 + 必实现方法 + 踩坑点。

## 一、先搞清三个数（别被旧数字误导）

```
全平台接口   1457          （1145 facade + 312 biz）
UDC 接口     274 = 250 真接口 + 24 注解
250 = 55 AppService + 195 其他
195 = 128 带 abstract + 67 无 abstract
128 = 101 有平台实现 + 27 纯扩展位
128 + 23 注解 = 151（决策表口径）
```

- **151** 是「决策表里归类的带 abstract 扩展点 + 注解」
- **128** 是真接口扩展点
- **27** 是纯扩展位（平台无实现，等你实现）

## 二、按场景找接口

| 我要干什么 | 实现 | 必实现方法 | 平台实现数 |
|---|---|---|---|
| 发布前校验，不通过就拦下 | `DeployBeforeService` | `boolean handle(AppContext)` | 7 |
| 元数据构建后补一段处理 | `AppMetaDataContextPostProcess` | `void postProcessAppMetaDataContext(AppContext)` | 27 |
| 生成新文件/配置类 | `CodeTask` | `String code(CodeContext)` | 50 |
| 导出时多一类产物 | `TransportHandler` | `List<SchemaInfo> out(CodeContext)` | 32 |
| 导入时自己处理一段 | `Importable` | `void in(TransportData)` | 29 |
| 属性类型 A→B 要迁数据 | `TypeChangeSqlResolver` | `boolean match(AttributeDto, AttributeDto, CodeContext)` | 5 |
| 自定义操作权限判定 | `ExtendAppOperationAuthCheck` | `boolean hasRight(ExtendAppAuthCheckInfoDto)` | 3 |
| 加一类一致性检测 | `DetectionTask` | `getDomainObjects()` + `detection(DetectionContext)` | 2 |
| 另存为时改产物 | `SaveAsHandler` | `void saveAs(TransportData)` | — |
| 加一个枚举项来源 | `CtpEnumItemProvider` 族 | 见 `cip-connector` | — |

`DeployBeforeService.handle` 返回 **false = 拦下整个发布**，这是最容易出错的地方。

## 三、四条注册通路（忘贴 = 静默失效）

| 通路 | 怎么用 | 实测 |
|---|---|---|
| **Spring 组件元注解** | 实现类自带 `@Component`/`@Service` + `@Primary` + `@Order` | 8 个注解自带（`AppService` / `Importer` / `ConsistencyDetection` / `TypeMapping` / `ParamLoadService` / `ExpressionFilter` / `EventHandler` / `ImportUpgradeHandler`） |
| **spring.factories** | `META-INF/spring.factories` 注册 | 48 jar / 85 键（真通路） |
| **`META-INF/services`** | Java SPI | **平台不用**（仅 2 jar 3 文件，全第三方） |
| **子类型扫描** | `getSubTypesOf` | 只有 2 个类型（`AppBeanNameModifier` / `UdcBaseEntity`） |

**结论**：ext 里写扩展点，靠的是**贴注解**，不是写 spring.factories。

⚠️ 表达式三件套（`ExpressionFilter` 相关）必须**同时注册**，少一个不生效。

## 四、谁在调用（判断扩展点是否真被用上）

`extension-point-consumers.md` 的三级分类：

```
154 个  跨包被引用 —— 真扩展点，改它有影响
 21 个  仅同包引用 —— 内部使用，扩展价值低
  8 个  零引用     —— 平台自己没用，谨慎
```

8 个零引用里，5 个值得注意：
`UdcTreeQueryService` / `PluginDefinition` / `Recoverable` / `Compatible` / `SchemaFilter`。

另 3 个（`autocode.v27.*BaseNode` / `BaseTrigger` / `ApplicationInnerReference`）是旧版遗留。

⚠️ **同名不同包大坑**：
- `autocode.v27.microflow.bo.BaseNode` → **0 引用**（旧版）
- `microflow.domain.bo.BaseNode` → **29 跨包引用**（现役）

查接口**必须用全名**，用短名会得出相反结论。

## 五、微流程扩展

微流程被调入口：
```java
Object MicroFlowProxyAppMicroFlow.invokeAppServiceMethod(MicroFlowRestRequestDto req);
// 构造：MicroFlowRestRequestDto.fromGet(meta) / fromPost(body, meta)
// 取参数：req.getRequestData() / req.getRestMetadata()
```

- 128 个微流程扩展接口见 `udc-microflow-extend-interfaces.md`
- 业务错误抛 `MicroFlowCustomErrorException(code, message)`
- 组织人员 8 个构造：`buildMemberCoreByUserId(String)` 等

## 六、扩展工程五模块（只有 -ext 可写）

```
<标识>-facade     接口定义（标品生成）
<标识>-biz        业务实现（标品生成）
<标识>-web        控制器（标品生成）
<标识>-ext       ← 只有这里可写
<标识>-assemble   装配（标品生成）

依赖链：facade ← biz ← web ← ext ← assemble
```

`-ext` 默认只有一个 `package-info.java`，手写代码放 `-ext/extend/` 下，
包名 `com/seeyon/<应用编码>/extend`。

⚠️ 写在其他模块**会被构建覆盖**——这是硬规矩，不是建议。

## 七、平台注解（109 个，108 RUNTIME）

Target 分布：METHOD 55 / TYPE 50 / FIELD 22 / 无 Target 9 / PARAMETER 9 /
CONSTRUCTOR 7 / ANNOTATION_TYPE 5 / TYPE_USE 2 / LOCAL_VARIABLE 1。

`EntityAttribute` 元素最多（19 个）。完整元信息见 `platform-annotations.md` 和
`docs/audit/artifacts/extension-surface-*/annotations.md`。

## 八、动手前的检查清单

```
① 我要干的事 → 本文件第二节找接口
② 这接口有人用吗 → extension-point-consumers.md（154/21/8）
③ 要贴什么注解 → 第三节（8 个自带 Spring 元注解的，忘贴就静默失效）
④ 方法签名逐字对 → packages/<构件>.md 或 udc-microflow-extend-interfaces.md
⑤ 平台参照实现 → 决策表里的实现数，去 service-flow 看那家怎么写的
⑥ 工程放哪 → 只有 -ext/extend/ 可写
⑦ 编译 → probe_contracts.py
```
