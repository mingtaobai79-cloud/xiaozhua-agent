# 53 · ★★★★★ 特性加载条件 + 占位符 + SqlProcessor（引擎最后一环）

**证据来源**：`StereotypeDecorate` 剩余方法（`parseConfiguration`/`parseNames`/`parseSql`/`checkNameUnique`）+ `AbstractFeature`/`AbstractProcessor`/`PlaceholderResolver` 完整反编译
**证据等级**：**VERIFIED_STATIC_BYTECODE**（含 `@DtoAttribute` 原文注解）

---

## 一、★★★★★ `processEmbedded` 的真实语义（决定性证据）

**`AbstractFeature` 字段注解原文：**

```java
@DtoAttribute(value="该特性是否嵌入业务处理（[template 有无]）")
private Boolean processEmbedded = false;
```

**★★★★★ 这就解释了 `parseConfiguration` 的过滤：**

```java
protected List<Clazz> parseConfiguration(EntityDto entity) {
    List<Feature> features = Features.splitGet(entity.getFeatures());
    ConfigurationLoader loader = Apps.getApplicationContext().getBean(ConfigurationLoader.class);
    ArrayList<Clazz> classes = new ArrayList<>();

    features.stream()
        .filter(Feature::isProcessEmbedded)          // ★ 只处理 processEmbedded=true 的特性
        .forEach(feature -> classes.addAll(
            loader.loadGeneratorConfig(
                StringUtils.camelToUnderline(feature.getName()),   // treeEntity → tree_entity
                Feature.class)));

    return classes;
}
```

**★★★★★ 三条硬事实：**

| # | 事实 |
|---|---|
| 1 | **代码注入只处理 `processEmbedded = true` 的特性** |
| 2 | **特性名驼峰转下划线后找 `feature/{snake_name}/template/config.json`** |
| 3 | **当前 18 个特性里只有 `treeEntity` 是 `true`** |

### 1.1 ★★★★★ 由此推出一条需要如实报告的结构性事实

**实测 18 个特性的 `processEmbedded` 与 `template/config.json` 存在情况：**

| 特性 | processEmbedded | 有 template/config.json | 会被加载? |
|---|---|---|---|
| `treeEntity` | **true** | ✅ | **✅ 加载** |
| `attributeScalability` | false | ✅（8,463 B） | ❌ 跳过 |
| `attributeScalabilityGlobal` | false | ✅（8,805 B） | ❌ 跳过 |
| `disable` | false | ✅（8,467 B） | ❌ 跳过 |
| 其余 14 个 | false | ✗ | ❌ 跳过 |

**⇒ `attributeScalability` / `attributeScalabilityGlobal` / `disable` 三个特性的 `template/config.json` **在当前引擎下不会被 `StereotypeDecorate` 加载**。**
**⇒ 它们的代码注入必然走另一条路径（未在标品包内找到），或该配置为本版本「预留未启用」。**

**★ 这是如实记录的平台现状，不是我的推断 —— 全包扫 `loadGeneratorConfig` 调用方，只有 `StereotypeDecorate` 一个。**

---

## 二、★★★★★ `PlaceholderResolver` —— 三种占位符（完整反编译 88 行）

### 2.1 三个前缀常量

```java
public static final String DEFAULT_PLACEHOLDER_PREFIX = "${";
public static final String PACKAGE_PLACEHOLDER_PREFIX = "$Package{";
public static final String CLASS_PLACEHOLDER_PREFIX   = "$Class{";
public static final String DEFAULT_PLACEHOLDER_SUFFIX = "}";
```

**★★★★★ 三种占位符（权威）：**

| 前缀 | 用途 | 后处理 |
|---|---|---|
| `$Class{x}` | 类名 | **首字母转大写** |
| `$Package{x}` | 包名 | **全部转小写** |
| `${x}` | 通用值 | 无 |

### 2.2 ★★★ `resolveByRule` —— 解析循环（完整）

```java
public String resolveByRule(String content, Function<String, String> rule) {
    int start = content.indexOf(placeholderPrefix);
    if (start == -1) return content;                       // 无占位符，原样返回

    StringBuilder result = new StringBuilder(content);
    while (start != -1) {
        int end = result.indexOf(placeholderSuffix, start);
        String placeholder = result.substring(start + prefix.length(), end);
        String replaceContent = (placeholder == null || placeholder.trim().isEmpty())
                                ? "" : rule.apply(placeholder);

        switch (placeholderPrefix) {
            case "$Class{":
                replaceContent = isBlank(replaceContent) ? ""
                    : replaceContent.substring(0,1).toUpperCase() + replaceContent.substring(1);
                break;
            case "$Package{":
                replaceContent = replaceContent.toLowerCase();
                break;
        }
        result.replace(start, end + suffix.length(), replaceContent);
        start = result.indexOf(prefix, start + replaceContent.length());
    }
    return result.toString();
}
```

**★★★★★ 四条事实：**
1. **`$Class{}` 自动首字母大写** —— 所以配置写 `$Class{entityName}Controller`，`entityName="order"` → `OrderController`
2. **`$Package{}` 自动全小写**
3. **空占位符替换为空字符串（不报错）**
4. **循环替换（支持一行多个占位符）**

### 2.3 ★★★ `resolve(content, valueMap)`

```java
public String resolve(String content, Map<String, Object> valueMap) {
    return resolveByRule(content, key -> String.valueOf(valueMap.get(key)));
}
```

**⚠ 注意：`String.valueOf(null)` 返回字符串 `"null"`，不是空串 —— 占位符查不到值会变成字面量 `null`。**

### 2.4 ★★★ `$Class{}` 与 `$Package{}` 的分工（`parseNames` 实测）

```java
private void parseNames(Clazz clazz, Map<String,Object> arguments) {
    // 类名：用 $Class{} 解析（首字母大写）
    String clazzName = PlaceholderResolver.getClassResolver().resolve(clazz.getClassName(), arguments);
    clazz.setClassName(clazzName);

    // 包名：先取 classType 的默认包，再加后缀
    String packageName = clazz.getClassType().getClassPackage();
    if (StringUtils.isNotBlank(clazz.getClassPackageSuffix())) {
        packageName = packageName + clazz.getClassPackageSuffix();
    }
    // 再用 $Package{} 解析（全小写）
    packageName = PlaceholderResolver.getPackageResolver().resolve(packageName, arguments);
    clazz.setPackageName(packageName);

    clazz.setClassNameFull(packageName + "." + clazzName);      // ★ 全名 = 包 + 类
}
```

**★★★★★ 两条事实：**
1. **包名默认来自 `classType.getClassPackage()`** —— 不是配置里写死的（配置里 `packageName` 都是空串）
2. **`classPackageSuffix` 是配置可选的包后缀**

### 2.5 ★★★ 三个 resolver 的分工（`resolveImport`/`resolveField`/`resolveAnnotation`）

```java
protected String resolveImport(String schema, Map args) {
    String resolve = PlaceholderResolver.getPackageResolver().resolve(schema, args);  // 先包
    return PlaceholderResolver.getClassResolver().resolve(resolve, args);            // 再类
}

protected String resolveField(String schema, Map args) {
    return PlaceholderResolver.getClassResolver().resolve(schema, args);             // 只类
}

protected String resolveAnnotation(String schema, Map args) {
    return PlaceholderResolver.getClassResolver().resolve(schema, args);             // 只类
}
```

**★ import 走「包 → 类」两遍解析，因为 import 语句里同时有包名和类名。**

---

## 三、★★★★★ `getArguments` —— 模板可用的 4 类参数

```java
protected Map<String, Object> getArguments(EntityDto entity, CodeContext codeContext) {
    Map arguments = MetadataUtils.getBaseMetadata(codeContext);      // ① 元数据基础
    HashMap<String, Object> map = new HashMap<>(16);

    map.put(ARG_ENTITY, entity);                                     // ② EntityDto 全对象
    map.put(ARG_ENTITY_NAME, StringUtils.capitalize(entity.getName()));  // ③ 实体名（首字母大写）
    map.put(TABLE, entityFileTemplate.getTableInfoMap());             // ④ 表信息
    map.putAll(arguments);                                           // 合入元数据

    HashMap featureMap = new HashMap(8);
    map.put(ARG_FEATURE, featureMap);                                // ⑤ 特性占位 map（空）
    return map;
}
```

**★★★★★ 参数常量：**
```java
ARG_ENTITY_NAME = "entityName"
ARG_ENTITY      = "entity"
ARG_FEATURE     = "feature"
TABLE           = "table"
```

**★★★ 三条事实：**
1. **`entityName` 已经 `capitalize()`** —— 所以 `$Class{entityName}Controller` 拿到的是首字母大写，再 `$Class{}` 又大写一次（幂等）
2. **`feature` map 是空 HashMap** —— 预留给特性传参（当前未填充）
3. **`table` 是 `getTableInfoMap()`** —— 表信息（`dbTableName` 等，第 46 篇树实体 SQL 用的就是它）

---

## 四、★★★★★ `checkNameUnique` —— 去重键是 `classType`（实测）

```java
private Clazz checkNameUnique(Clazz clazz, Map<Type, Clazz> checkedClazz) {
    Clazz clazzExists = null;
    if (checkedClazz.containsKey(clazz.getClassType())) {
        clazzExists = checkedClazz.get(clazz.getClassType());

        boolean checkResult = clazz.getClassName().equals(clazzExists.getClassName());
        checkResult = checkResult && clazz.getPackageName().equals(clazzExists.getPackageName());

        if (!checkResult) {
            log.error("[" + clazz.getClassName() + "]: different name or packages for the same class type!");
            throw new BusinessException("STEREOTYPE_0025");     // ★ 同类不同名 → 报错
        }
    }
    return clazzExists;
}
```

**★★★★★ 三条决定性事实：**

| # | 事实 |
|---|---|
| 1 | **去重键 = `classType`**（不是 className） |
| 2 | **同一 classType 的 className 和 packageName 必须一致**，否则抛 `STEREOTYPE_0025` |
| 3 | **一致则合并到同一个 `Clazz` 对象** —— 多特性的注入累积 |

**⇒ 这就是为什么 `treeEntity` 和 `attributeScalability` 都能往 `{E}Service` 注入 —— 它们的 `classType` 都是 `BIZ_DOMAIN_SERVICE`，类名都是 `$Class{entityName}Service`，因此合法合并。**

**⇒ 反过来：如果两个特性对同一 classType 用了不同的类名，平台直接报错。**

---

## 五、★★★★★ `parseSql` —— SQL 注入机制（完整反编译）

```java
private void parseSql(EntityDto entity, CodeWrapper code) {
    ArrayList<SqlProcessor> processors = new ArrayList<>();

    processors.add((SqlProcessor) stereotypes.get(entity.getStereotype()));   // ① 原型
    Features.splitGet(entity.getFeatures())
            .forEach(feature -> processors.add((SqlProcessor) feature));      // ② 每个特性

    HashMap sql = new HashMap(processors.size());
    processors.stream()
        .filter(Objects::nonNull)
        .forEach(p -> sql.put(p.getName(), p.getSql(entity)));               // ③ 按名字收集

    code.setSql(sql);
}
```

**★★★★★ 四条事实：**

| # | 事实 |
|---|---|
| 1 | **SQL 来源有两类：原型 + 特性** |
| 2 | **都实现 `SqlProcessor` 接口**（`getSql(EntityDto)` + `getName()`） |
| 3 | **结果按 `getName()` 存进 Map** —— `code.setSql(Map<String,String>)` |
| 4 | **原型和特性平等参与 SQL 生成** |

### 5.1 ★★★★★ `SqlProcessor` 接口（完整）

```java
public interface SqlProcessor {
    String getSql(EntityDto entity);     // 返回 SQL 字符串
    String getName();                    // SQL 的唯一键
}
```

### 5.2 ★★★★★ `AbstractProcessor` —— 全部特性的统一基类（完整）

```java
public abstract class AbstractProcessor implements SqlProcessor, EntitySaveProcessor {

    @Override public String getSql(EntityDto entityDto) { return ""; }        // ★ 默认空 SQL

    @Override public void afterEntitySaved(EntityDto before, EntityDto entity) { }

    @Override public void resolveAttribute4Feature(EntityDto before, EntityDto now,
                                                   List<AttributeDto> attributeDtoList) { }

    @Override public void afterEntityDeleted(EntityDto entityDto) { }
}
```

**★★★★★ 这就是所有原型和特性可重写的全部 4 个扩展点：**

| # | 方法 | 时机 | 已实测的实现 |
|---|---|---|---|
| 1 | `getSql(EntityDto)` | 代码生成时 | 默认 `""`；树实体 SQL 走这里 |
| 2 | `afterEntitySaved(before, entity)` | 实体保存后 | `BillStereotype`/`ArchiveTreeStereotype` → 枚举初始化 |
| 3 | `resolveAttribute4Feature(before, now, attrs)` | 实体保存时，字段列表已就绪 | `TreeEntityFeature` → `treeParentId` 改写 |
| 4 | `afterEntityDeleted(entity)` | 实体删除后 | `BillStereotype` → 清 `statusType`/`sendState` |

**⇒ 平台的全部「特性行为」就这 4 个方法。没有第五个。**

**★★ `AbstractProcessor implements SqlProcessor, EntitySaveProcessor` —— 两个接口合并，说明 SQL 生成和保存处理是同一批处理器。**

### 5.3 ★★★★★ 继承链（完整）

```
SqlProcessor (interface)          EntitySaveProcessor (interface)
        \                                /
         \                              /
          AbstractProcessor (abstract, 4 空方法)
                │
                ├── AbstractFeature  (特性基类, 16 个字段, @DtoAttribute)
                │        │
                │        ├── TreeEntityFeature     (有 resolveAttribute4Feature)
                │        ├── SuspendFeature        (空)
                │        ├── SecretLevelFeature    (空)
                │        └── ... 共 16 个
                │
                └── AbstractStereotype (原型基类, 11 字段)
                         │
                         ├── BillStereotype        (有 afterEntitySaved/Deleted)
                         ├── ArchiveTreeStereotype (有 afterEntitySaved)
                         ├── StandardStereotype    (空)
                         └── ... 共 6 个
```

**★★★★★ 决定性结论：原型和特性共享同一个基类 `AbstractProcessor`，因此它们有完全相同的 4 个扩展能力。**

---

## 六、★★★★★ `AbstractFeature` 的 16 个字段（含注解原文）

```java
public class AbstractFeature extends AbstractProcessor implements Feature, Serializable {
    @DtoAttribute("id")                                             Long id;
    @DtoAttribute("名称")                                            String name;
    @DtoAttribute("表示名称")                                         String caption;
    @DtoAttribute("描述")                                            String description;
    @DtoAttribute("排序")                                            Integer order;
    @DtoAttribute("是否不再推荐")                                       Boolean deprecated = false;
    @DtoAttribute("版型绑定")                                          Boolean stereotypeBind = false;
    @DtoAttribute("生成是忽略")                                        Boolean ignored = false;
    @DtoAttribute("是否可配置")                                        Boolean configurable = false;
    @DtoAttribute("配置信息")                                          String configuration;
    @DtoAttribute("实体传入的配置信息")                                    String customerConfiguration;
    @DtoAttribute("绑定的字段集")                                        String attributeSet;
    @DtoAttribute("属性清单")                                          List<AttributeDto> attributes;
    @DtoAttribute("行为清单")                                          List<BehaviorDto> behaviors;
    @DtoAttribute("该特性是否嵌入业务处理（[template 有无]）")                 Boolean processEmbedded = false;
}
```

**★★★★★ 关键注解原文（平台自己的措辞）：**
```
"该特性是否嵌入业务处理（[template 有无]）"   ← processEmbedded 的官方解释
"生成是忽略"                              ← ignored 的官方解释
"版型绑定"                                ← stereotypeBind 的官方解释
"绑定的字段集"                             ← attributeSet 的官方解释
```

**⇒ 「生成是忽略」直接证实 `ignored=true` 的语义是「跳过代码生成」，与第 50 篇的推断一致。**

**★ 新增字段 `customerConfiguration`（实体传入的配置信息）—— 第 50 篇没发现，是实例级配置覆盖。**

---

## 七、★★★★★ 完整链路最终版（引擎全闭环）

```
① 触发   EntityFileTemplate 生成时 → new StereotypeDecorate(template)
② 判跨应用 isOutter = codeContext.appId != entity.appId → matches() 返回 false 则跳过
③ 读配置 parseConfiguration(entity)
           features = Features.splitGet(entity.getFeatures())
           只保留 processEmbedded=true 的特性
           → feature/{camelToUnderline(name)}/template/config.json
           → List<Clazz>
④ 准备参数 getArguments: entity / entityName / table / baseMetadata / feature{}
⑤ 解析名  parseNames: $Class{} → 类名(首字母大写)
                      classType.getClassPackage() + suffix → $Package{} → 包名(小写)
                      classNameFull = package + "." + className
⑥ 三分支  CLASS_NEW    → parseTemplate(tplName) → classNew[]
          CLASS_EXTEND → parseTemplate(tplName) → classExtend[]
          CLASS_SAME   → resolveClassSame
                           checkNameUnique(classType 去重, 名/包必须一致否则 STEREOTYPE_0025)
                           parseClassAttachments(注解/import/字段 → 渲染 + 合并 + distinct)
                           JOIN   → parseMethodJoinPoints
                                      key = methodSign + "#" + joinPointName
                                      snippets.sort(order) → joinSnippets[key].add()
                           APPEND → parseTemplate(tplName) → appendMethods[]
⑦ SQL    parseSql: 原型 + 所有特性（SqlProcessor）→ code.setSql(Map<name, sql>)
⑧ 回传    getExtraArgs: 7 个 Type → 模板数据模型
⑨ 落盘    doMore: classNew + classExtend → 写文件
                  {base}/{app}-{module}/src/main/java/{pkg}/{Class}.java
```

**★★★★★ 九个步骤，每一步都有实测证据。**

---

## 九、★★★★★ `Type` 枚举 —— 9 个类型的完整定义（反编译，含包路径与默认类名）

```java
public enum Type {
    FACADE_APP_SERVICE     (Module.FACADE, "FACADE_APP_SERVICE",     0, "$Package{appPackagePath}.api",                    "$Class{entityName}AppService"),
    FACADE_DTO             (Module.FACADE, "FACADE_DTO",             1, "$Package{appPackagePath}.dto",                    "$Class{entityName}Dto"),
    BIZ_APP_SERVICE_IMPL   (Module.BIZ,    "BIZ_APP_SERVICE_IMPL",   2, "$Package{appPackagePath}.appservice",             "$Class{entityName}AppServiceImpl"),
    BIZ_DOMAIN_ENTITY      (Module.BIZ,    "BIZ_DOMAIN_ENTITY",      3, "$Package{appPackagePath}.domain.entity",          "$Class{entityName}Entity"),
    BIZ_DOMAIN_SERVICE     (Module.BIZ,    "BIZ_DOMAIN_SERVICE",     4, "$Package{appPackagePath}.domain.service",         "$Class{entityName}Service"),
    BIZ_DOMAIN_DAO         (Module.BIZ,    "BIZ_DOMAIN_DAO",         5, "$Package{appPackagePath}.domain.dao",             "$Class{entityName}Dao"),
    BIZ_DOMAIN_EVENT       (Module.BIZ,    "BIZ_DOMAIN_EVENT",       6, "$Package{appPackagePath}.domain.event",           "$Class{entityName}Event"),
    BIZ_DOMAIN_EVENT_LISTENER(Module.BIZ,  "BIZ_DOMAIN_EVENT_LISTENER",7,"$Package{appPackagePath}.domain.event.listener",  "$Class{entityName}Listener"),
    WEB_CONTROLLER         (Module.WEB,    "WEB_CONTROLLER",         8, "$Package{appPackagePath}.controller",             "$Class{entityName}Listener");
}
```

**★★★★★ 三条决定性事实：**

| # | 事实 |
|---|---|
| 1 | **`WEB_CONTROLLER` 的 `defaultClassName` 是 `$Class{entityName}Listener`** —— **确实是平台 bug**（复制粘贴自 `BIZ_DOMAIN_EVENT_LISTENER`）。因特性配置都显式写 `className`，实际生成走 `Abstract{E}Controller`（第 45/49 篇实测），未暴露。 |
| 2 | **9 个 Type 分属 3 个 Module**（`biz` / `facade` / `web`），与第 49 篇 4 模块结构对应 |
| 3 | **包路径全部由 `$Package{appPackagePath}` + 固定后缀构成** —— 应用包根 + 类型后缀 |

### 9.1 ★★★ `Module` 枚举（完整）

```java
BIZ("biz", 0),
FACADE("facade", 1),
WEB("web", 2);
```

**⇒ `Module` 只有 **3** 个值 —— 与第 49 篇的 `facade`/`biz`/`web` 三模块对应（`assemble` 和 `ext` 不含生成代码）。**

### 9.2 ★★★ `EntitySaveProcessor` 接口（完整）

```java
public interface EntitySaveProcessor {
    void afterEntitySaved(EntityDto before, EntityDto entity);
    void resolveAttribute4Feature(EntityDto before, EntityDto now, List<AttributeDto> attributeDtoList);
    void afterEntityDeleted(EntityDto entityDto);
}
```

**★★★★★ 接口分层（实测）：**
```
SqlProcessor          (2 方法)  getSql(EntityDto)  /  getName()
EntitySaveProcessor   (3 方法)  afterEntitySaved / resolveAttribute4Feature / afterEntityDeleted
AbstractProcessor     实现两者，全部给空实现（4 个方法）
```

**⇒ `AbstractFeature` 继承 `AbstractProcessor` 但**不**实现 `getName()` —— `getName()` 来自 `Feature` 接口（`AbstractFeature` 有 `name` 字段 + `getName()`）。**

---

## 十、★★★★★ 对开发者的 10 条结论

| # | 结论 |
|---|---|
| 1 | **只有 `processEmbedded=true` 的特性才注入代码**，当前只有 `treeEntity` |
| 2 | **`attributeScalability`/`disable` 的 template config 当前不被 `StereotypeDecorate` 加载**（如实记录） |
| 3 | **占位符只有 3 种**：`$Class{}`（首字母大写）/ `$Package{}`（全小写）/ `${}` |
| 4 | **占位符查不到值会变成字面量 `null`**（`String.valueOf(null)`） |
| 5 | **包名来自 `classType.getClassPackage()`**，配置里的 `packageName` 是空串 |
| 6 | **`checkNameUnique` 去重键是 `classType`**；同类不同名抛 `STEREOTYPE_0025` |
| 7 | **SQL 由原型 + 特性平等参与**，按 `getName()` 收集 |
| 8 | **所有原型和特性共享 `AbstractProcessor` 的 4 个扩展点**（`getSql`/`afterEntitySaved`/`resolveAttribute4Feature`/`afterEntityDeleted`） |
| 9 | **`ignored` 官方解释是「生成是忽略」** —— 跳过代码生成 |
| 10 | **`customerConfiguration` 是实例级配置覆盖**（第 50 篇未发现） |

---

## 九、待验证

| 问题 | 状态 |
|---|---|
| `attributeScalability`/`disable` 的代码注入实际路径 | **BLOCKED** —— 标品包内无调用方；需运行时观察 |
| `Type` 的 9 个包路径与默认类名 | ✅ **已实测**（见第九节，含 `WEB_CONTROLLER` 类名 bug） |
| `EntitySaveProcessor` 接口 | ✅ **已实测**（3 方法，见 9.2） |
| `Module` 枚举 | ✅ **已实测**（3 值 biz/facade/web） |
| `TableInfoMap` 的完整字段 | 待反编译 |
| `BehaviorDto` 的结构 | 待反编译（`behaviors` 全空，未启用） |
| `MetadataUtils.getBaseMetadata` 提供哪些键 | 待反编译 |
| `CLASS_EXTEND` 的继承语义 | 待查（当前零使用） |
