# 51 · ★★★★★ 特性代码注入机制 + 系统枚举自动生成（CLASS_NEW / JOIN / APPEND）

**证据来源**：`udc-biz-5.3.605.jar` 内 `feature/*/template/config.json` 真实配置 + `FeatureCommonService` 完整反编译 + `presetData/*.json`
**证据等级**：**VERIFIED_STATIC_BYTECODE** + **LIVE_RULE**（JSON 实测解析）

---

## 一、★★★★★ 特性注入的四个真实模式（实测枚举）

### 1.1 `classMode` —— 3 个值（第 52 篇实测，本篇初稿写 2 个是错的）

```
CLASS_NEW(0)      新生成一个类（ExtensionService / ExtensionDao / ExtensionEntity / ExtensionDto）
CLASS_EXTEND(1)   生成扩展类（引擎支持，当前零使用）
CLASS_SAME(2)     往已有类里注入（Controller / AppService / Service / Dto）
```

**★★★ 4 个特性配置文件里只出现了 `CLASS_NEW` / `CLASS_SAME` —— `CLASS_EXTEND` 是引擎保留位，当前未使用。详见 52 篇。**

### 1.2 `classType` —— 7 个值

```
WEB_CONTROLLER           Controller
FACADE_APP_SERVICE       AppService 接口
BIZ_APP_SERVICE_IMPL     AppServiceImpl
BIZ_DOMAIN_SERVICE       Service
BIZ_DOMAIN_DAO           Dao
BIZ_DOMAIN_ENTITY        Entity
FACADE_DTO               Dto
```

**★★★★★ 与 `Type` 枚举的 9 个对比：这里少 `BIZ_DOMAIN_EVENT` 和 `FACADE_DTO`... 实际 `FACADE_DTO` 有。缺的是 `EVENT` 和 `LISTENER` —— 印证第 45 篇「事件类不支持特性扩展」。**

### 1.3 `methodType` —— 2 个值（最重要）

```
APPEND    追加新方法（方法不存在的场景）
JOIN      ★ 加入已有方法（改写/织入方法的实现体）
```

**★★★★★ `JOIN` 是真正的「代码织入」—— 平台能把特性代码插进已有的 `create`/`update`/`selectById` 方法体里，而不是简单追加方法。**

---

## 二、★★★★★ 特性模板配置的结构（4 个文件实测）

```
feature/tree_entity/template/config.json              9,237 B   4 个类
feature/disable/template/config.json                  8,467 B   7 个类
feature/attribute_scalability/template/config.json    8,463 B   7 个类
feature/attribute_scalability_global/template/config.json 8,805 B  7 个类
```

### 2.1 完整结构（真实 JSON）

```json
[ {
    "className":  "$Class{entityName}Controller",     // ★ 占位符
    "packageName": "",                                 // 空=按 classType 默认包
    "classMode":  "CLASS_SAME",                        // CLASS_SAME | CLASS_NEW
    "classType":  "WEB_CONTROLLER",                    // 7 类之一
    "tplName":    "",                                  // 类级模板（通常空）
    "imports": [ { "schema": "import com.seeyon.boot.transport.ListResponse;" } ],
    "fields":  [ { "fieldName": "extensionService",
                   "schema": "@Resource\n    private $Class{entityName}ExtensionService extensionService;" } ],
    "methods": [ {
        "methodName": "selectImmediateChildren;selectAllChildren;selectParent",   // ★ 分号分隔多方法
        "methodType": "APPEND",                        // APPEND | JOIN
        "description": "根据条件查询下一级列表(不分页)",
        "methodSign": "selectImmediateChildren();selectAllChildren();selectParent();",  // ★ 匹配签名
        "tplName":    "feature/tree_entity/template/feature.tree.entity.class[controller].ftl"
    } ]
} ]
```

**★★★★★ 7 个顶层字段：`className` / `packageName` / `classMode` / `classType` / `tplName` / `imports` / `fields` / `methods`**

**★★★ 两条匹配机制：**
1. **`methodName` 用分号分隔多个方法名** —— 一个模板可同时处理多个方法
2. **`methodSign` 是精确签名匹配** —— `selectById(Long id)` 必须与实际方法签名一致才会织入

### 2.2 ★★★★ `$Class{...}` 占位符

```
$Class{entityName}Controller      → CreateOrderController
$Class{entityName}Service         → CreateOrderService
$Class{entityName}ExtensionEntity → CreateOrderExtensionEntity
$Class{entityName}Dto             → CreateOrderDto
```

**⇒ 占位符由 `PlaceholderResolver` 解析（`com.seeyon.udc.entity.stereotype.generator.PlaceholderResolver`）。**

---

## 三、★★★★★ `tree_entity` 的注入点（4 个类，实测）

| className | classType | classMode | 方法数 |
|---|---|---|---|
| `$Class{entityName}Controller` | `WEB_CONTROLLER` | `CLASS_SAME` | 1（APPEND） |
| `$Class{entityName}AppService` | `FACADE_APP_SERVICE` | `CLASS_SAME` | 1（APPEND） |
| `$Class{entityName}AppServiceImpl` | `BIZ_APP_SERVICE_IMPL` | `CLASS_SAME` | 1（APPEND） |
| `$Class{entityName}Service` | `BIZ_DOMAIN_SERVICE` | `CLASS_SAME` | **6**（APPEND） |

### 3.1 ★★★★★ 四层穿透的三级方法（全链一致）

```
Controller         selectImmediateChildren();selectAllChildren();selectParent();
AppService         selectImmediateChildren(SingleRequest<Long> request);
                   selectAllChildren(SingleRequest<Long> request);
                   selectParents(SingleRequest<Long> request)
AppServiceImpl     同 AppService
Service            （6 个方法，含实现）
```

**★ `selectParent` vs `selectParents` 命名不一致（Controller 用单数，AppService 用复数）—— 平台真实拼写。**

### 3.2 ★★★ imports 注入（精确清单）

```
Controller:       ListResponse / ApiParam / TreeQueryDto / ResponseUtils
AppService:       ListResponse / TreeQueryDto
AppServiceImpl:   TreeQueryDto
```
**⇒ 特性不只是加方法，还自动补 import。**

---

## 四、★★★★★ `attribute_scalability`（属性扩展）—— CLASS_NEW 的完整形态

### 4.1 ★★★★★ 4 个新类（`CLASS_NEW`）

```
$Class{entityName}ExtensionService    BIZ_DOMAIN_SERVICE   CLASS_NEW
$Class{entityName}ExtensionDao        BIZ_DOMAIN_DAO       CLASS_NEW
$Class{entityName}ExtensionEntity     BIZ_DOMAIN_ENTITY    CLASS_NEW
$Class{entityName}ExtensionDto        FACADE_DTO           CLASS_NEW
```

**★★★★★ 这就是「属性扩展」的实现方式：为每个实体生成 4 个独立的 `{E}Extension*` 类，实体主体不变。**

### 4.2 ★★★★★ 3 个已有类被织入（`CLASS_SAME`）

**（a）`{E}Service` —— 7 个 CRUD 方法全部 `JOIN`**

```json
"methods": [
  { "methodName": "selectById",             "methodType": "JOIN", "methodSign": "selectById(Long id)" },
  { "methodName": "selectPageByCondition",  "methodType": "JOIN", "methodSign": "selectPageByCondition(PageInfo pageInfo, Map<String, Object> columnMap, Sort sort)" },
  { "methodName": "selectPageByWrapper",    "methodType": "JOIN", "methodSign": "selectPageByWrapper(PageInfo pageInfo, Wrapper wrapper)" },
  { "methodName": "create",                 "methodType": "JOIN", "methodSign": "create(${entityName}Dto dto)" },
  { "methodName": "update",                 "methodType": "JOIN", "methodSign": "update(${entityName}Dto dto)" },
  { "methodName": "deleteById",             "methodType": "JOIN", "methodSign": "deleteById(Long id)" },
  { "methodName": "deleteByIds",            "methodType": "JOIN", "methodSign": "deleteByIds(List<Long> ids)" }
]
```

**★★★★★ 7 个方法全部被织入 —— 这是全平台最深的代码改写：**
```
查：selectById / selectPageByCondition / selectPageByWrapper
写：create / update
删：deleteById / deleteByIds
```

**⇒ 属性扩展在每个 CRUD 上都插入了扩展字段的读写逻辑。**

**★★★ `{E}Service` 的 2 个注入字段：**
```java
@Resource private AttributeExtensionMappingService attributeExtensionMappingService;
@Resource private $Class{entityName}ExtensionService extensionService;
```

**（b）`{E}Dto` —— 加一个字段**

```java
@ApiModelProperty(value = "自定义扩展map")
private Map<String,Object> extension;
```
**⇒ 属性扩展的载体就是 DTO 上的一个 `Map<String,Object> extension` 字段。**

**（c）`{E}Service` 第二个条目（`CLASS_SAME`，1 个方法）**

```json
{ "methodName": "selectImmediateChildren", "methodType": "JOIN",
  "methodSign": "selectImmediateChildren(@NotNull Long id)",
  "fields": [{ "@Resource private AttributeExtensionMappingService attributeExtensionMappingService;" }] }
```

**★★ 注意：`attribute_scalability` 里也织入了 `selectImmediateChildren` —— 说明属性扩展**也**支持树实体（组合特性）。**

### 4.3 ★★★★ `attributeScalabilityGlobal`（全局扩展）

```
ExtensionGlobalService     BIZ_DOMAIN_SERVICE   CLASS_NEW    ← ★ 无 $Class{} 占位符！
ExtensionGlobalDao         BIZ_DOMAIN_DAO       CLASS_NEW
ExtensionGlobalEntity      BIZ_DOMAIN_ENTITY    CLASS_NEW
ExtensionGlobalDto         FACADE_DTO           CLASS_NEW
```

**★★★★★ 与 `attribute_scalability` 的唯一区别：新类名**不带** `$Class{entityName}` 前缀 —— 全局只生成一套 `ExtensionGlobal*`，所有实体共用。**

**★★★ `configuration` 字段给出各自对应的 Bean 名：**
```json
attributeScalability:        "configuration": "SystemPresetCustomExpansionPlan"
attributeScalabilityGlobal:  "configuration": "SystemPresetGlobalExpansionPlan"
```
**⇒ 这是扩展计划的 Bean 名（`SystemPresetCustomExpansionPlan` = 单实体扩展，`SystemPresetGlobalExpansionPlan` = 全局扩展）。**

---

## 五、★★★★ `disable` 特性 —— 与属性扩展同构

```
$Class{entityName}ExtensionService   BIZ_DOMAIN_SERVICE   CLASS_NEW
$Class{entityName}ExtensionDao       BIZ_DOMAIN_DAO       CLASS_NEW
$Class{entityName}ExtensionEntity    BIZ_DOMAIN_ENTITY    CLASS_NEW
$Class{entityName}ExtensionDto       FACADE_DTO           CLASS_NEW
$Class{entityName}Service            BIZ_DOMAIN_SERVICE   CLASS_SAME  7 methods
$Class{entityName}Dto                FACADE_DTO           CLASS_SAME
$Class{entityName}Service            BIZ_DOMAIN_SERVICE   CLASS_SAME  1 method
```

**★★★★★ `disable` 与 `attribute_scalability` 的配置结构**完全相同**（7 个类，同数量方法）—— 说明它们是同一套「扩展类 + CRUD 织入」模式的两次实例化。**

**⇒ 推论：平台的「属性扩展」和「禁用」共用 `AttributeExtensionMappingService` 基础设施。**

---

## 六、★★★★★ `FeatureCommonService` —— 系统枚举自动生成（完整反编译 283 行）

### 6.1 入口签名

```java
public void afterEntitySaved(EntityDto before, EntityDto entity,
                             String jsonPath, String statusType, Integer orderNo)
```

**★★★ 四个参数的含义：**
```
jsonPath    枚举定义 JSON（presetData/{bill|archive|form}Enum.json）
statusType  主状态字段名（"statusType"）
orderNo     该字段的排序号（bill=15, archiveTree=37）
```

### 6.2 ★★★★★ 创建分支（`before == null`）—— 首次建实体

```java
boolean needCreate = Objects.isNull(before);
List<UdcEnumDto> udcEnumDtoList = FileUtils.jsonToBeanList(jsonPath, UdcEnumDto.class);

if (needCreate) {
    Long defaultEnumCategoryId = selectDefaultEnumCategoryId(entity.getAppId());
    List<AttributeDto> attributeCreateList = new ArrayList<>(udcEnumDtoList.size());
    doCreateSystemUdcEnum(entity, statusType, orderNo, udcEnumDtoList,
                          defaultEnumCategoryId, attributeCreateList);
    attributeService.createBatch4System(attributeCreateList);   // ★ 批量建属性
}
```

### 6.3 ★★★★★ `doCreateSystemUdcEnum` —— 核心（逐步）

**第一步：枚举重命名（加实体名前缀）**
```java
udcEnumDto.setAppId(appId);
udcEnumDto.setName(StereotypeUtil.resolveEnumName(entity.getName()) + udcEnumDto.getName());
    //  "billStatus"  →  "CreateOrderBillStatus"
udcEnumDto.setCaption(entity.getCaption() + udcEnumDto.getCaption());
udcEnumDto.setCategoryId(defaultEnumCategoryId);
udcEnumService.createBatch(udcEnumDtoList);
```

**第二步：枚举项建库**
```java
udcEnumItemDto.setEnumId(udcEnumDto.getId());
udcEnumItemDto.setAppId(appId);
udcEnumItemService.createBatch(所有枚举项);
```

**第三步：为每个枚举建一个属性字段（关键）**
```java
AttributeDto attributeDto = new AttributeDto();
attributeDto.setEntityId(entity.getId());
attributeDto.setAppId(appId);

if (udcEnumDto.getName().containsIgnoreCase("status")) {         // ★ status 类
    attributeDto.setWidgetConfig("{\"pc\":\"TreeSelect\",\"mobile\":\"CascaderSelect\","
                                 + "\"list\":false,\"detail\":false,\"quickSearch\":false}");
    attributeDto.setName(statusType);                            // "statusType"
    attributeDto.setAttributeGroup("流程");                       // ★ 分组 = 流程
    attributeDto.setOrderNo(34);

    // ★★★ 同时改写三组状态字段，全部指向这一个枚举
    List<AttributeDto> list = attributeService.selectByNames(entity.getId(),
        ["suspendStatusType", "nullifyStatusType", "terminateStatusType"]);
    for (AttributeDto attr : list) {
        attr.setRelationApp(appId.toString());
        attr.setRelationEntity(udcEnumDto.getId().toString());
        attr.setRelationEntityName(udcEnumDto.getCaption());
    }
    attributeService.updateBatch4System(list);
} else {                                                         // ★ sendState 类
    attributeDto.setWidgetConfig(同上);
    attributeDto.setName("sendState");
    attributeDto.setAttributeGroup("系统");                       // ★ 分组 = 系统
    attributeDto.setOrderNo(25);
}

attributeDto.setEdit(false);                                     // ★ 系统字段不可编辑
attributeDto.setCaption(udcEnumDto.getCaption());
attributeDto.setDataType(DataType.ENUM.name());
attributeDto.setRelationApp(appId.toString());
attributeDto.setRelationEntity(udcEnumDto.getId().toString());
attributeDto.setRelationEntityName(udcEnumDto.getCaption());
attributeDto.setSourceType(AttributeSourceTypeEnum.SYSTEM_ATTRIBUTE_SET);  // ★ 来源=系统字段集
attributeDto.setRelationType(RelationType.Many2OneAssociation);
attributeDto.setUniqueness(false);

// 分组 ID 绑定（"系统" / "流程"）
attributeCreateList.add(attributeDto);
```

**★★★★★ 六条决定性事实：**

| # | 事实 |
|---|---|
| 1 | **一组状态字段共享同一个枚举**：`statusType` 建枚举，`suspendStatusType`/`nullifyStatusType`/`terminateStatusType` 全部改写指向它 |
| 2 | **`statusType` 归「流程」分组，orderNo=34；`sendState` 归「系统」分组，orderNo=25** |
| 3 | **Widget 固定 `{pc:TreeSelect, mobile:CascaderSelect}`** |
| 4 | **`edit=false`** —— 系统状态字段用户不可编辑，只能由流程驱动 |
| 5 | **`sourceType = SYSTEM_ATTRIBUTE_SET`** —— 标记来源，可区分自定义字段 |
| 6 | **`relationType = Many2OneAssociation`** —— 状态字段对枚举是多对一 |

### 6.4 ★★★★ `selectDefaultEnumCategoryId` —— 默认枚举分组

```java
Map paramMap = { "appId": appId, "preset": true, "name": "默认分组" };
UdcEnumCategoryDto dto = selectListByConditions(paramMap).stream().findFirst().orElse(null);
if (dto == null) {
    dto = new UdcEnumCategoryDto();
    dto.setPreset(true);  dto.setAppId(appId);
    dto.setName("默认分组");  dto.setOrderNo(0);
    return udcEnumCategoryService.create(dto);
}
return dto.getId();
```
**⇒ 每个应用自动建一个 `preset=true` 的「默认分组」，系统枚举全放这里。**

### 6.5 ★★★★★ 更新分支（`before != null`）—— 实体改名时同步

```java
if (Objects.equals(before.getName(), entity.getName())) return;   // ★ 名字没变就不动

for (UdcEnumDto udcEnumDto : udcEnumDtoList) {
    List<AttributeDto> attrs;
    if (udcEnumDto.getName().containsIgnoreCase("status")) {
        attrs = attributeService.selectByNames(entity.getId(),
            ["statusType","suspendStatusType","nullifyStatusType","terminateStatusType"]);
    } else {
        AttributeDto a = attributeService.selectByName(entity.getId(), "sendState");
        if (a == null) continue;
        attrs = [a];
    }
    UdcEnumDto old = udcEnumService.selectById(Long.parseLong(attrs.get(0).getRelationEntity()));
    if (old == null) continue;

    String newName = StereotypeUtil.resolveEnumName(entity.getName()) + udcEnumDto.getName();
    old.setName(newName);
    udcEnumService.update4System(old);                      // ★ 改枚举名

    for (AttributeDto attr : attrs) attr.setRelationEntityName(newName);
    attributeService.updateBatch4System(attrs);             // ★ 改属性引用名
}
```

**★★★★★ 实体改名 → 枚举自动改名（`{旧实体名}{枚举名}` → `{新实体名}{枚举名}`）。**
**★★ 通过 `attr.getRelationEntity()` 反查枚举 ID —— 属性到枚举的引用链。**

---

## 七、★★★★★ 单据状态枚举的真实数据（`presetData/billEnum.json`）

### 7.1 `billStatus`（8 个状态）

| code | name | caption |
|---|---|---|
| 0 | `DRAFT` | 草稿 |
| 1 | `TO_BE_SUBMITTED` | 待提交 |
| 2 | `PENDING_REVIEW` | 提交中 |
| 3 | `COME_INTO_FORCE` | 已生效 |
| 4 | `TERMINATED` | 已终止 |
| 5 | `NULLIFIED` | 已作废 |
| 6 | `SUSPENDED` | 已挂起 |
| 7 | `FAILED` | 不通过 |

**★★★★★ 这就是单据的完整生命周期：草稿 → 待提交 → 提交中 → 已生效 →（终止/作废/挂起/不通过）**

### 7.2 `billSendState`（2 个状态）

| code | name | caption |
|---|---|---|
| 0 | `SEND_SUCCESS` | 发送成功 |
| 1 | `SENDING` | 发送中 |

**⇒ `sendState` 只有两态 —— 单据下发（互信/主数据同步）的确认状态。**

### 7.3 ★★★ 三个 Enum JSON 的差异

```
billEnum.json      2 个枚举（billStatus 8 项 + billSendState 2 项）
archiveEnum.json   1 个枚举（37 是 orderNo，说明档案只建 1 个状态枚举）
formEnum.json      1 个枚举（表单状态）
```

**⇒ 单据原型最复杂：两个枚举（业务状态 + 发送状态）；档案/表单只有一个。**

---

## 八、★★★★★ `dependencyGraph.json` —— UDC 的完整平台依赖（17 项）

**`copVersion = "test"`（测试版依赖图）**

### 8.1 SERVICE 类型（11 个标品服务）

| caption | name | version |
|---|---|---|
| 组织机构 | `organization` | 3.12.0-TEST-SNAPSHOT |
| 用户中心 | `ctp-user` | 3.12.0-TEST-SNAPSHOT |
| BPM引擎 | `bpm` | 3.12.0-TEST-SNAPSHOT |
| 事项中心 | `ctp-affair` | 3.12.0-TEST-SNAPSHOT |
| 消息中心 | `ctp-message` | 3.12.0-TEST-SNAPSHOT |
| 连接器 | `cip-connector` | 3.12.0-TEST-SNAPSHOT |
| 数据中台 | `cdp-data` | 3.12.0-TEST-SNAPSHOT |
| 门户 | `portal` | 3.12.0-TEST-SNAPSHOT |
| 基础设置 | `app-common` | 3.12.0-TEST-SNAPSHOT |
| 基础能力接入 | `cip-capability` | 3.12.0-TEST-SNAPSHOT |
| **低代码平台** | **`udc`** | **3.12.0-DEV-SNAPSHOT** |

### 8.2 FRONTEND（1 个）

```
前端控件   FRONTEND   version = "beta"
```

### 8.3 STARTER 类型（5 个组件）

| caption | name |
|---|---|
| starter组件 | `starter` |
| 平台拓展组件 | `boot-extend` |
| **udc运行态组件** | **`udc-starters`** |
| 文件组件 | `boot-starter-file` |
| 意见组件 | `boot-starter-opinion` |

**★★★★★ 四条结论：**

| # | 结论 |
|---|---|
| 1 | **UDC 运行依赖 11 个标品微服务，不是独立运行** |
| 2 | **`udc` 自己是 `3.12.0-DEV-SNAPSHOT`，其余是 `TEST-SNAPSHOT`** —— udc 开发版 |
| 3 | **前端控件版本是 `beta`** —— UDC 前端未 GA |
| 4 | **`udc-starters` 是运行态组件 —— 对应 Maven 里的 `udc-starter-runtime`** |

**★★★ 这正是我在第 22 轮记的「Seeyon 能力三形态」的服务清单在配置文件里的权威版本：**
```
Dubbo 泛化：organization / ctp-user / bpm / ctp-affair / ctp-message / cip-connector
数据：cdp-data
门户：portal
基础：app-common / cip-capability
低代码：udc
```

---

## 九、★★★★★ 综合：特性的三层生效机制

```
① 字段集层（attributeSet.json）
   特性 → 一组字段定义
   例：treeEntity → treePath/treeParentId/isLeaf/treeLevel/treeCaptionPath

② 属性改写层（resolveAttribute4Feature）
   特性 → 保存时改写字段属性
   例：TreeEntityFeature → treeParentId: BIGINTEGER → ENTITY 自引用

③ 代码注入层（template/config.json）
   特性 → 生成/织入代码
   例：tree_entity → 4 个类（Controller/AppService/AppServiceImpl/Service）
        attribute_scalability → 4 个新类 + 3 个类 JOIN
```

**★★★★★ 三层是独立的：**
- **有字段集但无代码注入**：`billBasic` / `archiveBasic` / `formBasic` / `secretLevel` 等（只有字段）
- **有属性改写但无代码注入**：`treeEntity`（既有改写又有注入，是唯一的「全三层」特性）
- **有代码注入但无字段集**：`attributeScalability` / `attributeScalabilityGlobal`（`attributeSet` 为空）

---

## 十、★★★★★ 对开发者的 10 条结论

| # | 结论 |
|---|---|
| 1 | **特性注入有 4 个模式：`CLASS_SAME`/`CLASS_NEW` × `APPEND`/`JOIN`** |
| 2 | **`JOIN` 是真正的代码织入**，能改写 `create`/`update`/`selectById`/`deleteById` 等方法体 |
| 3 | **`CLASS_NEW` 生成独立扩展类**：`{E}ExtensionService/ExtensionDao/ExtensionEntity/ExtensionDto` |
| 4 | **属性扩展的载体是 DTO 上的 `Map<String,Object> extension` 字段** |
| 5 | **属性扩展织入 7 个 CRUD 方法**（3 查 2 写 2 删），是全平台最深的改写 |
| 6 | **单实体扩展 vs 全局扩展只差类名前缀**（`{E}Extension*` vs `ExtensionGlobal*`） |
| 7 | **建实体时自动建系统枚举**，命名 `{实体名}{枚举名}`（如 `CreateOrderBillStatus`） |
| 8 | **一组状态字段共享一个枚举**：`statusType` + `suspendStatusType` + `nullifyStatusType` + `terminateStatusType` |
| 9 | **系统状态字段 `edit=false`**，用户不可改，只能流程驱动；`statusType` 归「流程」组，`sendState` 归「系统」组 |
| 10 | **单据有 8 个业务状态**（草稿→待提交→提交中→已生效→终止/作废/挂起/不通过）+ 2 个发送状态 |

---

## 十一、待验证

| 问题 | 状态 |
|---|---|
| `PlaceholderResolver` 支持的全部占位符 | 待反编译 |
| `JOIN` 的织入实现（怎么插入方法体） | 待反编译（`StereotypeDecorate`） |
| `AttributeExtensionMappingService` 的实现 | 待反编译（扩展字段怎么存表） |
| `SystemPresetCustomExpansionPlan` Bean | 待反编译 |
| `archiveEnum.json` / `formEnum.json` 的枚举项 | 待解析 |
| `methodType` 是否还有第三值 | 实测仅 2 个（APPEND/JOIN），4 个文件覆盖 |
| `stereotypeBind=true` 的场景 | 待查（6 原型全 false） |