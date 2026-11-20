# EntityMeta / AttributeMeta 元数据结构（源码级）

> 来源：`udc-starter-lowcode-5.3.517.jar` CFR 反编译
> 文件：`core/EntityMeta.java`（34 方法）、`core/AttributeMeta.java`（26 方法）
> 等级：`VERIFIED_STATIC_SOURCE`

---

## 1. EntityMeta 的 17 个字段（完整）

```java
private EntityType    entityType;        // ★ 主实体 / 子实体
private String        entityCategory;    // ★ 实体分类（标准 / EXT 扩展）
private RelationType  relationType;      // ★ 关系类型（5 种）
private Long          entityId;          // 实体元数据 ID
private String        entityTable;       // ★ 物理表名
private String        name;              // 逻辑名
private String        caption;           // 显示名
private String        stereotype;        // ★ 版型（standard/bill/archive/form…）
private Class<?>      entityClass;       // ★ 实体类（Entity）
private Class<?>      dtoClass;          // ★ DTO 类
private String        dtoListName;       // ★ DTO 里子表集合的字段名（关键！）
private String        parentFullName;    // 父实体全名
private String        fullName;          // ★ 实体全名（app.entity）
private boolean       sortField = false; // ★ 是否启用排序字段
private List<EntityMeta>     children;   // ★★ 子实体列表（递归依据）
private List<AttributeMeta>  attributes; // ★ 属性列表
private EntityMeta    topParent;         // 顶层父实体
```

**⇒ `children` + `dtoListName` 是主子表机制的**全部依据**：**
```java
// recursiveCreate 里的核心两行
Object dtoList = ReflectFieldUtil.getFieldValue(newDto, meta.getDtoListName());
//   ↑ 通过 dtoListName 反射拿到 DTO 里的子表集合字段
this.recursiveCreate(meta, dtoColl);
//   ↑ 对 children 递归
```

**⇒ 所以「子表怎么关联」的答案是：**
**`EntityMeta.children[i].dtoListName` → DTO 里对应字段名 → 反射取集合。**

---

## 2. `EntityType` 枚举（2 个值）

```java
public enum EntityType implements Messageable {
    MASTER_ENTITY(0),    // 主实体（聚合根）
    SUB_ENTITY(1);       // 子实体（明细）
}
```

**⇒ 只有 2 个值，非常简单。**

**⇒ `recursiveCreate` / `recursiveUpdate` / `recursiveDelete` 都判断：**
```java
} else if (EntityType.MASTER_ENTITY != entityMeta.getEntityType()) {
    // 非主实体才直接落库
}
```
**⇒ 主实体不在这里落库，由调用方 `create()` 自己 insert。**

---

## 3. `RelationType` 枚举（5 个值）★ 重要

```java
public enum RelationType implements Messageable {
    Many2OneAssociation(1),    // 多对一关联
    One2OneAssociation(2),     // 一对一关联
    One2OneAggregation(3),     // ★ 一对一聚合（内嵌子表，1 条）
    One2ManyAggregation(4),    // ★ 一对多聚合（内嵌子表，N 条）
    NONE(0);                   // 无关系
}
```

**⇒ 只有 `Aggregation` 才是「主子表」，`Association` 是「关联引用」。**

**⇒ `DtoFieldHelper.set1ToNDtoList` 的处理逻辑：**
```java
if (RelationType.One2OneAggregation == entityMeta.getRelationType()) {
    Object fieldValue = CollectionUtils.isNotEmpty(mergedSubDtoList) ? mergedSubDtoList.get(0) : null;
    ReflectFieldUtil.setFieldValue(parentDto, field, fieldValue);        // 单个对象
} else if (RelationType.One2ManyAggregation == entityMeta.getRelationType()) {
    ReflectFieldUtil.setFieldValue(parentDto, field, mergedSubDtoList);  // List
}
```

**⇒★★ 这是关键区别：**

| RelationType | DTO 字段类型 | 是否参与递归 | 是否级联删 |
|---|---|---|---|
| `One2OneAggregation` | **单个对象** | ✅ | ✅ |
| `One2ManyAggregation` | **List** | ✅ | ✅ |
| `One2OneAssociation` | 单个对象 | ❌ | ❌ |
| `Many2OneAssociation` | 单个对象 | ❌ | ❌ |
| `NONE` | — | ❌ | ❌ |

**⇒ 开发主子表时，`relationType` 必须是 `One2OneAggregation` 或 `One2ManyAggregation`。**
**⇒ 若误设成 `Association`，子表不会参与级联写入。**

---

## 4. AttributeMeta 的 13 个字段（完整）

```java
private String   fullName;          // 属性全名（app.entity.attr）
private String   name;              // 属性名（对应 DTO 字段名）
private String   caption;           // 显示名
private String   description;       // 描述
private boolean  multiSelect;       // ★ 是否多选（枚举多选）
private boolean  dataI18n;          // ★ 是否启用数据国际化
private String   dataType;          // ★ 数据类型（STRING/LONG/DATE/ENUM…）
private String   realDataType;      // ★★ 真实数据类型（如 CONTENT 内容字段）
private String   relationAppName;   // ★ 关联字段：目标应用名
private String   relationEntity;    // ★ 关联字段：目标实体
private Boolean  useSnapshot;       // ★ 是否使用快照（历史留痕）
private Long     attrGuid;          // 属性 GUID
private Maskable maskType;          // ★ 脱敏配置
```

### 4.1 `realDataType` 的特殊值

**从 `DtoFieldHelper.isContentField` 看到：**
```java
private static boolean isContentField(AttributeMeta attributeMeta) {
    boolean isContentField = Objects.nonNull(attributeMeta)
        && "CONTENT".equals(attributeMeta.getRealDataType());
    if (isContentField) {
        log.info("realDataType:{},fullName:{}",
            attributeMeta.getRealDataType(), attributeMeta.getFullName());
    }
    return isContentField;
}
```

**⇒ `realDataType = "CONTENT"` 是「大文本/富文本内容字段」，会在变更比对时被排除。**

**⇒ 原因：内容字段可能很大，比对成本高，所以 `extractAttrChange` 用 `contentFieldFilter` 跳过。**

### 4.2 `Maskable` 脱敏结构

**从 `extractAttrChange` 反推：**
```java
MaskableDto maskableInfo = new MaskableDto();
maskableInfo.setType(attributeMeta.getMaskType().type().name());
maskableInfo.setMaskKeys(attributeMeta.getMaskType().maskKeys());
maskableInfo.setStart(attributeMeta.getMaskType().start());
maskableInfo.setEnd(attributeMeta.getMaskType().end());
```

**⇒ `Maskable` 有 4 个属性：`type` / `maskKeys` / `start` / `end`。**

### 4.3 关联字段（`relationAppName` / `relationEntity`）

**⇒ 这两个字段配对使用，表示「指向哪个应用的哪个实体」。**
**⇒ 对应 `DataType` 里的引用类型（关联字段），不是普通标量。**

---

## 5. EntityMeta 的 34 个方法（按用途归类）

### 5.1 类型/分类判断

```java
getEntityType()      → EntityType       主实体 or 子实体
getEntityCategory()  → String           "EXT" 表示扩展实体
getRelationType()    → RelationType     关系类型
getStereotype()      → String           版型
```

### 5.2 类/表映射

```java
getEntityClass()  → Class<?>    实体类
getDtoClass()     → Class<?>    DTO 类
getEntityTable()  → String      物理表名
getDtoListName()  → String      ★ DTO 里子表集合字段名
```

### 5.3 层级关系

```java
getChildren()    → List<EntityMeta>    ★★ 子实体（递归依据）
getAttributes()  → List<AttributeMeta> ★ 属性
getTopParent()   → EntityMeta          顶层父
getParentFullName() → String           父全名
getFullName()    → String              自身全名
```

### 5.4 其他

```java
isSortField()   → boolean   是否启用排序
getName() / getCaption()    逻辑名 / 显示名
getEntityId()              实体元数据 ID
```

**⇒ 这些方法都是简单 getter，没有复杂逻辑。**
**⇒ EntityMeta 是**纯数据结构**，所有行为逻辑都在 Service 层。**

---

## 6. 关键机制串联（把元数据和写入链连起来）

```
EntityMeta
├─ getChildren()            → 递归遍历依据
│   └─ child.getDtoListName()  → 反射取 DTO 子表集合
├─ getEntityType()          → 判断是否主实体（主实体不落库）
├─ getEntityClass()         → findDao / BeanCopier 目标类
└─ getDtoClass()            → findService 依据
        │
        ↓ 传给
DtoConvertUtil.resetInsertHandle(meta, dto, DtoFieldHelper::resetInsert)
        │
        ├─ 遍历 meta.getChildren()
        ├─ 反射 child.getDtoListName() 取子表集合
        └─ 递归 + 对每层调 biConsumer
                │
                ↓ DtoFieldHelper.resetInsert(parent, sub)
                ├─ parent.setId(Ids.gidLong())        ← 主表 ID
                ├─ sub.setId(Ids.gidLong())           ← 子表 ID
                └─ sub.setFieldValue("parentId", parent.getId())  ← 外键
                        │
                        ↓ 然后
BaseEntityCurdService.create(dto)
        ├─ recursiveCheck()   → 4 条校验规则
        ├─ recursiveCreate()  → 深→浅 createBatch + 逐层 beforeCreate/afterCreate
        └─ 主表 insert + entity.getId() → dto.setId()
```

**⇒ 整条链**完全由元数据驱动**，没有硬编码的实体名或字段名。**

**⇒ 这就是 UDC「低代码」的本质：元数据 → 反射 → 泛型 Service → 通用 DAO。**

---

## 7. 与专题 1 的一致性检查

| 项 | 专题 1 结论 | 本轮源码验证 |
|---|---|---|
| 扩展列 30 个 | `01-metadata.md §2.9` | `entityCategory = "EXT"` + `listEnableExtField` 证实 |
| 两个状态维度 | `billStatus` / `caseId` | `statusType`（业务）+ `sendState`（发送）分开 |
| nullify 是特性 | `resources/feature/nullify/config.json` | `IGNORE_FIELDS` 里 nullify 四件套证实 |
| 主子表靠元数据树 | 推断 | ✅ `getChildren()` + `getDtoListName()` 直接证实 |
