# ★★★ 重大修正：EntityMeta 由注解扫描构建，不是数据库读取

> 来源：`EntityRelationHandler.java`（CFR 反编译，`udc-starter-lowcode-5.3.517.jar`）
> 等级：`VERIFIED_STATIC_SOURCE`
> 修正时间：2026-11-17

---

## 1. 推翻的旧结论

| # | 旧结论 | 修正 |
|---|---|---|
| 1 | `EntityMeta` 从数据库 / 元数据表加载 | **❌ 错误。从 `@EntityInfo` 注解扫描 ClassLoader 构建** |
| 2 | `EntityMeta` 是 DB 数据的运行时映射 | **❌ 是**编译期注解 → 运行时反射**的产物** |
| 3 | `dtoListName` 是配置项 | **❌ 是按 `relationType` 自动生成的命名规则** |
| 4 | 主子表关系存在元数据表 | **❌ 存在 `@EntityAttribute(relationType=..., relationEntity=...)` 注解里** |

**⇒ 这是本轮最重要的认知修正。**
**⇒ UDC「低代码」的本质不是「配数据库」，而是「代码生成 + 注解扫描」。**

---

## 2. `EntityRelationHandler` 构建流程（源码级）

### 2.1 入口：扫描 ClassLoader 找注解类

```java
private static void scanClass(ClassLoader classLoader, String appName) {
    if (classLoader instanceof ModuleAppClassLoader) {
        ModuleAppClassLoader loader = (ModuleAppClassLoader) classLoader;
        Set<Class> entityClass = loader.getAllClassList().stream()
            .filter(aClass -> aClass.isAnnotationPresent(EntityInfo.class))   // ★ 找 @EntityInfo
            .collect(Collectors.toSet());
        Set<Class> dtoClass = loader.getAllClassList().stream()
            .filter(aClass -> {
                DtoInfo dtoInfo = AnnotationUtil.getAnnotation(aClass, DtoInfo.class);
                return dtoInfo != null && StringUtils.isNotBlank(dtoInfo.entity());  // ★ 找 @DtoInfo 且 entity 非空
            }).collect(Collectors.toSet());
        LRU_CLASS_SET_CHCHE.put(key, MutablePair.of(entityClass, dtoClass));
    } else if (classLoader instanceof ModuleClassLoader) {
        // 同上，用 getClassList()
    } else {
        // 单体模式：按包名扫描
        Set<Object> udcAppPackageNames = Sets.newHashSet();
        if (Apps.isMonolithic()) {
            udcAppPackageNames = Apps.getAllAppInfo().values().stream()
                .filter(app -> app.isUdcApp())
                .map(appInfo -> "com.seeyon." + appInfo.getAppName())
                .collect(Collectors.toSet());
        }
        Set<Class> entityClass = ClassScanner.scan(
            StringUtils.join(udcAppPackageNames, ","), EntityInfo.class)
            .stream().distinct()
            .filter(aClass -> !aClass.getName().contains(".extend."))   // ★ 排除 extend 包
            .collect(Collectors.toSet());
        Set<Class> dtoClass = ClassScanner.scan(..., DtoInfo.class).stream()...;
    }
}
```

**⇒ 三种 ClassLoader 场景：**
1. `ModuleAppClassLoader`（模块化应用）
2. `ModuleClassLoader`（模块）
3. 单体模式（按包名 `com.seeyon.<appName>` 扫）

**⇒ `.extend.` 包被明确排除 → 扩展类不参与元数据构建。**

### 2.2 构建单个 EntityMeta

```java
entityClassSet.stream().distinct().forEach(aClass -> {
    EntityMeta entityMeta = new EntityMeta();

    // ① 从自定义注解属性取 id / stereotype / entityCategory
    Map customAttributeMap = AnnotationUtils.getCustomAttributeMap(aClass, EntityInfo.class);
    String id = customAttributeMap.get("id");
    if (StringUtils.isNotBlank(id) && NumberUtil.isNumber(id)) {
        entityMeta.setEntityId(Long.valueOf(id));
    }
    entityMeta.setStereotype(customAttributeMap.get("stereotype"));       // ★ 版型
    entityMeta.setEntityCategory(customAttributeMap.get("entityCategory")); // ★ 分类

    // ② 基础信息
    entityMeta.setEntityClass(aClass);
    entityMeta.setFullName(aClass.getName());                            // ★ 全名 = 类全限定名
    EntityInfo entityInfo = aClass.getAnnotation(EntityInfo.class);
    entityMeta.setName(aClass.getSimpleName());                          // ★ 逻辑名 = 简单类名
    entityMeta.setCaption(entityInfo.value());                           // ★ 显示名 = @EntityInfo.value()

    // ③ 按 @DtoInfo(entity=...) 匹配 DTO 类
    Class dtoClass = dtoClassMap.get(aClass.getName());
    entityMeta.setDtoClass(dtoClass);

    // ④ 解析属性（@EntityAttribute）
    EntityRelationHandler.parseAttribute(aClass, dtoClass, entityMeta);

    // ⑤ 表名从 JPA @Table 取
    Optional.ofNullable(aClass.getAnnotation(Table.class))
        .ifPresent(t -> entityMeta.setEntityTable(t.name()));

    // ⑥ ★★ 按 EntityType 分两种构建方式
    if (EntityType.MASTER_ENTITY == entityInfo.entityType()) {
        entityMeta.setEntityType(EntityType.MASTER_ENTITY);
        entityMeta.setRelationType(RelationType.NONE);                   // 主实体无关系类型
        entityMeta.setDtoListName(convertDtoList(null, aClass.getName()));
        entityMeta.setParentFullName(aClass.getName());                  // 父=自己
        entityMeta.setChildren(Lists.newArrayList());
        entityRelationMap.put(aClass.getName(), entityMeta);
    } else if (EntityType.SUB_ENTITY == entityInfo.entityType()) {
        // ★★★ 子实体的关系配置在 parentId 字段的注解上！
        Field field = ReflectFieldUtil.getField(aClass, "parentId");
        if (Objects.nonNull(field) && field.isAnnotationPresent(EntityAttribute.class)) {
            EntityAttribute parentAttr = field.getAnnotation(EntityAttribute.class);
            RelationType relationType = parentAttr.relationType();       // ★ 关系类型
            entityMeta.setEntityType(EntityType.SUB_ENTITY);
            Field sortField = ReflectFieldUtil.getField(aClass, "orderNo");
            entityMeta.setSortField(Objects.nonNull(sortField));         // ★ 有 orderNo 就启用排序
            entityMeta.setRelationType(relationType);
            entityMeta.setDtoListName(convertDtoList(relationType, aClass.getName()));
            entityMeta.setParentFullName(parentAttr.relationEntity());   // ★ 父实体全名
            entityMeta.setChildren(Lists.newArrayList());
            entityRelationMap.put(aClass.getName(), entityMeta);
        } else {
            log.warn("子实体:{} parentId 不存在", aClass.getName());      // ★ 子实体必须有 parentId
        }
    }
});
```

**⇒★★ 五条硬性规则（直接约束开发）：**

| # | 规则 | 违反后果 |
|---|---|---|
| ① | 实体类必须有 `@EntityInfo` | 不被扫描，EntityMeta 不存在 |
| ② | DTO 类必须有 `@DtoInfo(entity="实体全名")` | `dtoClass` 为 null，无法写入 |
| ③ | **子实体必须有 `parentId` 字段且带 `@EntityAttribute(relationType, relationEntity)`** | **日志 warn「子实体:xxx parentId 不存在」，子表关系断掉** |
| ④ | `@EntityInfo.entityType()` 必须是 `MASTER_ENTITY` 或 `SUB_ENTITY` | 实体不会被构建 |
| ⑤ | 表名来自 `@Table(name=...)` | `entityTable` 为空 |

### 2.3 构建父子树

```java
// ① 找出所有 SUB_ENTITY
Set<EntityMeta> subEntityList = entityRelationMap.values().stream()
    .filter(m -> EntityType.SUB_ENTITY == m.getEntityType()).collect(Collectors.toSet());

// ② 对每个实体，把 parentFullName 匹配的子实体挂到 children
entityRelationMap.forEach((key, value) -> buildSubEntity(key, value, subEntityList));

private static void buildSubEntity(String entityFullName, EntityMeta entityMeta, Set<EntityMeta> subEntitySet) {
    if (CollectionUtils.isEmpty(subEntitySet)) return;
    HashSet notRelationSet = new HashSet();
    subEntitySet.forEach(meta -> {
        if (StringUtils.isNotBlank(entityFullName) && entityFullName.equals(meta.getParentFullName())) {
            if (!entityMeta.getChildren().contains(meta)) {
                entityMeta.getChildren().add(meta);      // ★ 挂到 children
            }
        } else {
            notRelationSet.add(meta);
        }
    });
    // ★★ 递归：对已挂上的每个子实体，继续挂它自己的子实体（支持多层主子表）
    if (subEntitySet.size() == notRelationSet.size()) return;   // 没有新增，停止
    entityMeta.getChildren().forEach(subMeta ->
        buildSubEntity(subMeta.getFullName(), subMeta, notRelationSet));
}
```

**⇒ 层级关系靠 `parentFullName` 字符串匹配，递归构建。**
**⇒ 支持**无限层级**主子表（不止两级）。**

```java
// ③ 给所有节点设 topParent
Set<EntityMeta> masterEntityList = entityRelationMap.values().stream()
    .filter(m -> EntityType.MASTER_ENTITY == m.getEntityType()).collect(Collectors.toSet());
masterEntityList.forEach(meta -> {
    Consumer<EntityMeta> consumer = m -> m.setTopParent(meta);
    EntityMetaUtil.forEachMeta(meta, consumer);      // 遍历整棵树设置
});
```

### 2.4 ★★★ `dtoListName` 生成规则（核心！）

```java
public static String convertDtoList(RelationType relationType, String entityFullName) {
    String simpleName = StrUtil.lowerFirst(StringUtils.substringAfterLast(entityFullName, "."));
    if (RelationType.One2OneAggregation == relationType) {
        return simpleName + "Dto";        // ★ 一对一聚合 → xxxDto
    }
    if (RelationType.One2ManyAggregation == relationType) {
        return simpleName + "DtoList";    // ★ 一对多聚合 → xxxDtoList
    }
    return simpleName;                     // 关联类型 → xxx
}
```

**⇒ 举例（假设实体 `com.seeyon.app.OrderDetail`）：**

| relationType | `dtoListName` | DTO 里必须有字段 |
|---|---|---|
| `One2OneAggregation` | `orderDetailDto` | `private OrderDetailDto orderDetailDto;` |
| `One2ManyAggregation` | **`orderDetailDtoList`** | `private List<OrderDetailDto> orderDetailDtoList;` |
| `One2OneAssociation` | `orderDetail` | `private OrderDetail orderDetail;` |
| `Many2OneAssociation` | `orderDetail` | `private OrderDetail orderDetail;` |

**⇒★★ 这是最常见的踩坑点：**
**⇒ `One2ManyAggregation` 的 DTO 字段名**必须**是 `<实体简单名首字母小写>DtoList`。**
**⇒ 名字不对 → `ReflectFieldUtil.getFieldValue(dto, dtoListName)` 拿到 null → 子表完全不写入，且不报错。**

### 2.5 缓存机制

```java
static LRUCache<String, Map<String, EntityMeta>> LRU_ENTITY_CACHE = CacheUtil.newLRUCache(200);
static LRUCache<String, MutablePair<Set<Class>, Set<Class>>> LRU_CLASS_SET_CHCHE = CacheUtil.newLRUCache(200);

public static void clearCache(URLClassLoader classLoader, String appName) {
    String key = EntityMetaUtil.genKey(classLoader, appName);
    LRU_ENTITY_CACHE.remove(key);
    LRU_CLASS_SET_CHCHE.remove(key);
}
```

**⇒ 缓存 key = `classLoader + appName`。**
**⇒ LRU 容量 200 个应用。**
**⇒ 部署新版本 / 卸载模块时必须 `clearCache`，否则拿到旧元数据。**

---

## 3. `@EntityInfo` 注解完整定义（11 个属性）

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
public @interface EntityInfo {
    String  value();                              // ★ 必填，实体显示名（caption）
    String  description()      default "";        // 描述
    EntityType entityType()    default EntityType.MASTER_ENTITY;  // ★ 主/子实体
    String  historyEntity()    default "";        // 历史实体（快照用）
    String  plugins()          default "";        // 插件
    boolean fullTextSearch()   default false;     // 全文检索
    boolean permission()       default false;     // 启用权限
    boolean isPublic()         default false;     // 是否公开
    boolean export()           default false;     // 允许导出
    boolean isLogicDelete()    default false;     // ★ 逻辑删除
    int     sort()             default 0;         // 排序
    Custom[] customs()         default {};        // ★ 自定义属性（含 id/stereotype/entityCategory）
}
```

**⇒ `@EntityInfo.value()` 是**必填的显示名**（`caption`）。**
**⇒ `isLogicDelete()` 决定是否走逻辑删除 —— 与专题 3 的逻辑删除机制对应。**
**⇒ `customs()` 承载 `id` / `stereotype` / `entityCategory` 三个扩展属性。**

---

## 4. `AttributeMeta` 的构建（`parseAttribute`）

```java
private static void parseAttribute(Class<?> entityClass, Class<?> dtoClass, EntityMeta entityMeta) {
    // ① 从 DTO 字段收集 @Maskable（脱敏配置在 DTO 上，不在 Entity 上！）
    Map<String, Maskable> maskableMap = ReflectFieldUtil.getFieldList(dtoClass).stream()
        .filter(f -> f.isAnnotationPresent(Maskable.class))
        .collect(Collectors.toMap(f -> f.getName(), f -> AnnotationUtil.getAnnotation(f, Maskable.class)));

    // ② 从 Entity 字段收集 @EntityAttribute
    List<AttributeMeta> attributeMetaList = ReflectFieldUtil.getFieldList(entityClass).stream()
        .filter(f -> f.isAnnotationPresent(EntityAttribute.class))
        .map(f -> { ... })
        ...
}
```

**⇒★★ 关键分工：**
- **`@EntityAttribute` 打在 Entity 字段上**（属性元数据）
- **`@Maskable` 打在 DTO 字段上**（脱敏）**

**⇒ 所以 DTO 和 Entity 的字段注解是**分工的**，不是重复的。**

---

## 5. 完整的元数据加载链路（修正版）

```
应用启动 / 部署
    ↓
EntityRelationHandler.getClassSet(classLoader, appName)
    ├─ 扫描 ClassLoader 所有类
    ├─ filter @EntityInfo  → entityClassSet
    └─ filter @DtoInfo(entity非空) → dtoClassSet
            ↓ (LRU 缓存 key=classLoader+appName)
    buildEntityRelationMap()
        ├─ 对每个 entityClass：
        │   ├─ @EntityInfo → caption / entityType / isLogicDelete / customs
        │   ├─ @Table → entityTable
        │   ├─ @DtoInfo(entity=全名) → dtoClass
        │   ├─ parseAttribute() → @EntityAttribute(Entity字段) + @Maskable(DTO字段)
        │   └─ 按 entityType 构建（MASTER / SUB）
        ├─ buildSubEntity() 递归 → children 树（靠 parentFullName 匹配）
        └─ forEachMeta → 设置 topParent
            ↓
    LRU_ENTITY_CACHE.put(key, entityRelationMap)
            ↓
BaseEntityCurdService.entityMeta  ← 从这里取
            ↓
recursiveCreate / recursiveUpdate / recursiveDelete
    全部靠 entityMeta.getChildren() + getDtoListName()
```

**⇒ 整条链路**没有一次数据库查询**。**

---

## 6. 对开发者的硬约束（最终版）

```
【实体类必须】
1. @EntityInfo("显示名")                    ← 必填
2. @EntityInfo(entityType=MASTER_ENTITY)    ← 主实体
3. @Table(name="物理表名")                   ← 否则 entityTable 为空
4. 字段打 @EntityAttribute                   ← 否则不是元数据属性

【DTO 类必须】
5. @DtoInfo(entity="实体类全限定名")          ← 否则 dtoClass 为 null
6. 字段打 @Maskable                          ← 脱敏配置在 DTO 上

【子实体额外必须】
7. @EntityInfo(entityType=SUB_ENTITY)
8. 必须有 parentId 字段
9. parentId 字段必须打 @EntityAttribute(
       relationType = One2ManyAggregation,
       relationEntity = "父实体全限定名"
   )
10. 有 orderNo 字段则自动启用排序

【DTO 字段命名必须匹配】
11. One2ManyAggregation → 字段名 = <子实体简单名首字母小写>DtoList
12. One2OneAggregation  → 字段名 = <子实体简单名首字母小写>Dto
    名字不对 → 子表静默不写入
```

---

## 7. 缓存与热更新

| 项 | 值 |
|---|---|
| 元数据缓存 | `LRU_ENTITY_CACHE`，容量 200，key = `classLoader + appName` |
| 类集合缓存 | `LRU_CLASS_SET_CHCHE`，容量 200 |
| 清除方法 | `EntityRelationHandler.clearCache(classLoader, appName)` |
| 触发时机 | 部署 / 卸载（`ModuleUnloadEvent`）|

**⇒ 改了注解但没重新部署 → 读到的还是旧元数据。**
**⇒ 这是「改了代码没生效」的常见原因之一。**

---

## 8. 与之前文档的冲突处理

**`01-metadata.md` 里关于「元数据存储」的描述需要复核：**
- 如果原文说「元数据在数据库表」→ 那是**设计态元数据**（UDC 设计器保存的）
- 本文说的是**运行态 EntityMeta**（注解扫描产物）

**⇒ 两者是**不同层次**，不矛盾：**
```
设计态：UDC 设计器 → 数据库 / OSS（保存用户配置的实体定义）
运行态：代码生成 → Java 类 + 注解 → 启动时扫描 → EntityMeta
```

**⇒ 下一步必须去 `01-metadata.md` 核对这个区分是否写清楚了。**
