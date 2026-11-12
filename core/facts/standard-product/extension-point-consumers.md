# 扩展点被谁调用：静态引用面

## 1. Capability

补上「是否被调用」这一层证据。前面几格解决了：

```
有哪些扩展点（128 真接口）→ 怎么写（决策表逐字签名）→ 怎么注册（spring.factories）
```

但还差最后一问：**平台代码里到底有没有地方用它？** 没有 = 写了也不生效。

本格给出 **183 个 UDC 真接口**（= 128 个扩展点 + 55 个 `*AppService` 调用面，两者都带 abstract）在 12252 个 class 常量池里的引用统计，按证据强度分三级。

## 2. Version

基线同 `BASELINE.md`（udc 族 5.3.517/5.3.605、boot 族 5.3.600）。

## 3. Input

```
- interfaces.json（10414 类 / 1145 接口）→ 183 个 com.seeyon.udc 下带 abstract 的真接口
- 91 个标品 jar 的全部 class 字节
```

## 4. Required

无（纯静态取证）。

## 5. Execution

```
对每个目标接口 I：
  扫 91 jar 里 12252 个 class 的字节
  若常量池含 "com/seeyon/…/I" 且不是 I 自身
    → 记一条引用；同包记 intra，跨包记 cross
```

## 6. Side Effects

无。只读 jar。

## 7. Known Constraints

### 7.1 三级证据强度

| 级别 | 数量 | 含义 | 能推出什么 |
|---|---|---|---|
| **跨包引用（cross）** | **154** | 其他 jar 里的类引用了这个接口 | 平台真在用，**一定会被调**（可能是注入、类型转换、Bean 查找） |
| **仅同包引用（intra）** | **21** | 只有本包内的类引用 | 包内自用；实现和调用都在同一 jar，改它影响面限于本包 |
| **零引用（zero）** | **8** | 12252 个 class 里没人引用 | 连平台实现都没有，**写了很可能不被调** |

### 7.2 引用最多的（不是扩展点，是入参 / 上下文对象）

| 接口 | 跨包引用 | 来源包 | 性质 |
|---|---|---|---|
| `CodeContext` | 190 | udc-biz / udc-extend / udc-plugin-api | 代码生成入参，13 方法 |
| `AppContext` | 165 | udc-biz / udc-cicd / udc-extend / udc-plugin-api | 应用上下文，4 方法 |
| `DetectionContext` | 148 | udc-biz / udc-extend / udc-plugin-api | 一致性检测上下文，5 方法 |
| `UdcDataType` | 59 | udc-biz / udc-common / udc-plugin-api / udc-starter-dataflow | 类型系统，39 方法 |
| `BaseNode`（`microflow.domain`） | 29 | udc-biz | 微流程节点基类，18 方法 |

⇒ 这几个是「进方法后从哪取数据」的对象，引用多是因为所有人都在收它们当参数，不是因为要你去实现。

### 7.3 真扩展点的引用数（这才是「会被调」的排序）

| 扩展点 | 跨包引用 | 来源包 | 必实现方法 |
|---|---|---|---|
| `CodeTask` | **58** | udc-biz / udc-cicd / udc-extend / udc-plugin-api | `String code(CodeContext)` |
| `AppFeature` | 38 | udc-biz / udc-extend / udc-plugin-api / udc-web | 4 方法 |
| `TransportHandler` | 35 | udc-biz / udc-extend / udc-plugin-api | `List<SchemaInfo> out(CodeContext)` |
| `Importable` | 31 | udc-biz / udc-extend / udc-plugin-api | `void in(TransportData)` |
| `AppMetaDataContextPostProcess` | 28 | udc-biz / udc-cicd / udc-extend | `void postProcessAppMetaDataContext(AppContext)` |
| `ElementRepository` | 23 | udc-biz | 6 方法 |
| `SaveAsHandler` | 19 | udc-biz / udc-extend | `void saveAs(TransportData)` |
| `MicroFlowSchemaDeterminer` | 18 | udc-biz | 12 方法 |
| `LateralAuthChecker` | 18 | udc-biz | `check(Supplier<Long>)` |
| `ConsistenceDetection` | 17 | udc-biz | 3 方法 |
| `MicroFlowSimpleComponentCascadeHandler` | 16 | udc-biz | 1 方法 |

⇒ 引用数 = 写它之后被动触发的机会多少。`CodeTask` 58、`TransportHandler` 35、`Importable` 31
这类高频钩子，写错影响面最大；反过来也最容易验证（一发布就跑到）。

### 7.4 零引用的 8 个（别急着写）

| 接口全名 | 方法 | 判断 |
|---|---|---|
| `com.seeyon.udc.autocode.v27.microflow.bo.BaseNode` | 18 | **v27 遗留**：现役是 `com.seeyon.udc.microflow.domain.bo.BaseNode`（29 跨包引用）。同名不同包，别看错 |
| `com.seeyon.udc.autocode.v27.microflow.bo.BaseTrigger` | 18 | 同上，现役是 `microflow.domain.bo.BaseTrigger`（16 跨包） |
| `com.seeyon.udc.autocode.ApplicationInnerReference` | 3 | **v27 遗留**：现役是 `com.seeyon.udc.common.autocode.ApplicationInnerReference`（14 方法，**14 跨包引用**，决策表写的就是这个）。同名不同包，别用短名查 |
| `com.seeyon.udc.common.api.UdcTreeQueryService` | 1 | 只有一个方法，可能已废弃 |
| `com.seeyon.udc.PluginDefinition` | 8 | 插件定义，可能在别处以配置/DB 形式存在 |
| `com.seeyon.udc.common.autocode.Recoverable` | 1 | 单方法标记接口 |
| `com.seeyon.udc.common.autocode.transport.compare.Compatible` | 1 | 单方法标记接口 |
| `com.seeyon.udc.common.transport.SchemaFilter` | 2 | 导入过滤，可能走配置不走向外调用 |

⇒ 「零引用」不等于「不能用」，只等于「静态看不到调用方」。可能有三种情况：

1. 靠 Spring `getBeansOfType` 反射拿实现（常量池里只有泛型擦除后的 `Class` 参数）
2. 靠配置/元数据驱动（数据库里配了实现类名）
3. 真的废弃了

**判断法**：写个空实现 + 打日志，构建部署后看有没有被实例化/调用。这就是 §8 的实测。

### 7.5 同名不同包是这轮最大的坑

`BaseNode` / `BaseTrigger` / `ApplicationInnerReference` 各有两个全名：

```
com.seeyon.udc.autocode.v27.microflow.bo.BaseNode                  零引用（旧）
com.seeyon.udc.microflow.domain.bo.BaseNode                       29 跨包（现役）

com.seeyon.udc.autocode.v27.microflow.bo.BaseTrigger               零引用（旧）
com.seeyon.udc.microflow.domain.bo.BaseTrigger                    16 跨包（现役）

com.seeyon.udc.autocode.ApplicationInnerReference                  3 方法 / 零引用（旧）
com.seeyon.udc.common.autocode.ApplicationInnerReference          14 方法 / 14 跨包（现役）
```

按简单名查会得出完全相反的结论。**查任何接口都先用全名 grep，别用 `BaseNode` 这种短名。**

规律：`autocode.v27.*` / 无 `common` 前缀的那批是旧版遗留，现役统一在
`microflow.domain.*` 和 `common.autocode.*` 下。

## 8. Evidence

```
docs/audit/artifacts/extension-surface-20261029/consumers.json
  scope: com.seeyon.udc / scanned_classes: 12252 / targets: 183
  rows[].{iface, methods, pkg, ref_count, cross_count, intra_count, cross_pkgs, refs}

生成器 tools/core/platform/scan_extension_consumers.py
  判据：class 文件常量池含 "com/seeyon/…/Iface" 字节串，排除接口自身
  同包引用单独计数（intra），不混进 cross
```

**方法局限（必须知道）**：

- 常量池引用只能证明「有人提到这个类型」，不能证明「运行时必定调用它」
- 反过来的假阴性：`getBeansOfType(X.class)` 里 X 会出现在常量池（算命中），
  但靠配置字符串反射加载的实现类则完全不可见
- 泛型擦除导致的间接引用（`List<? extends Xxx>`）也能命中，属于正常

所以本格结论定位为：**排除法** —— 有引用 = 大概率会被调；零引用 = 需要实测才能确认。

## 9. Verified


| 断言 | 方法 |
|---|---|
| 跨包引用数 | 重跑 `scan_extension_consumers.py`，比 `cross_count` |
| 零引用是否真废弃 | 取 §7.4 任一接口，写空实现 + `System.out.println`，构建部署看日志 |
| 同名不同包 | `grep -c "\.BaseNode$"` 应得到 2 个全名 |
