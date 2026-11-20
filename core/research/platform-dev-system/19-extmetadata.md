# 元数据读写体系（boot-starter-extmetadata 5.3.603，106 类）

> 数据源：`boot-starter-extmetadata-5.3.603.jar` javap 实测
> 等级：`VERIFIED_STATIC_BYTECODE`（方法签名 + 类结构）
> ⚠️ 用户环境 5.3.517，本机 5.3.603

---

## 0. ★ 这个包到底是什么

**名字叫 `extmetadata`（扩展元数据），实际是**UDC 元数据的运行时读取层**。**

**证据：106 类里 102 个在 `com.seeyon.boot.starter.extmetadata`，但**全部 DTO/Service 都叫 `Udc*`**，并且 import 了 `com.seeyon.ctp.metadata.dto.*`（标品元数据）。**

**⇒ 结构：**
```
com.seeyon.ctp.metadata        ← 标品元数据（ctp 老框架）
        ↓ 转换
com.seeyon.boot.starter.extmetadata  ← UDC 视角的元数据（Udc*Dto）
        ↓ 提供给
UDC 运行时 / GraphQL Schema 生成
```

---

## 1. ★★★ 106 类的分层

| 包 | 类数 | 是什么 |
|---|---:|---|
| `dto` | 41 | **Udc*MetaDataDto（元数据模型）** |
| `request` | 22 | **查询请求 DTO（SearchDto）** |
| `enums` | 12 | **元数据枚举** |
| `domain` | **9** | **★ 元数据读写 Service（核心）** |
| `utils` | 6 | 转换/校验/路径工具 |
| `resource` | 3 | 资源加载（前端/动态） |
| `oss` | 5 | **OSS 存储（方法在父类，未 dump 到）** |
| `appservice` | 3 | 门面（V2） |
| `controller` | 2 | REST 入口 |
| `constant` / `event` / 其他 | 3 | |

---

## 2. ★★★ 9 个 domain Service —— 元数据的读写入口

| Service | 方法数 | 管什么元数据 |
|---|---:|---|
| **`UdcEntityMetaDataService`** | **16** | **实体 + 属性（最重要）** |
| `UdcReferMetaDataService` | 9 | 关联（引用关系） |
| `UdcPageInfoMetaDataService` | 7 | 页面信息 |
| `UdcServiceMetadataService` | 6 | Service / Starter 元数据 |
| `UdcCtpEnumMetaDataService` | 6 | CTP 枚举（选项集） |
| `UdcCtpEnumItemMetaDataService` | 6 | CTP 枚举项 |
| `UdcEnumMetaDataService` | 5 | Java 枚举 |
| `UdcDtoMetaDataService` | 3 | DTO 元数据 |
| `UdcAppServiceMetaDataService` | 3 | AppService 元数据 |

**⇒ **9 类元数据对象**：实体 / 属性 / 关联 / 页面 / Service / DTO / 枚举(Java) / 枚举(CTP) / AppService。**

---

## 3. ★★★ UdcEntityMetaDataService（16 方法）—— 实体元数据

```java
// ★ 核心：按应用名取实体（全量）
List<UdcEntityMetaDataDto> selectEntityByAppName(UdcEntitiesMetaDataSearchDto)
List<UdcEntityMetaDataDto> selectEntity2DtoByAppName(...)

// ★ 简单版（不含属性，性能好）
List<UdcSimpleEntityMetaDataDto> selectAllSimpleEntityByAppName(...)
Map<String, UdcEntityMetaDataDto> selectAllSimpleAggEntity...(两版)

// ★ 单个实体
UdcEntityMetaDataDto selectEntity(UdcEntityMetaDataSearchDto)

// ★★★ 聚合实体（含子实体/关联）—— 主子表结构从这来
List<UdcEntityMetaDataDto>  selectAggEntity(...)              // 两版
List<UdcEntityMetaDataDto>  selectAggEntityIncludeAssociation(...)
Map<String, UdcEntityMetaDataDto> selectAggEntitiesMapIncludeAssociation(...)
Map<String, UdcEntityMetaDataDto> selectAggEntityMapIncludeAssociation(...)

// ★ 聚合元数据（汇总）
List<UdcAggMetadataDto> selectSimpleAggMetadata(...)

// ★ 属性
Map<String, List<UdcAttributeMetaDataDto>> getAttribute...(两版)
Map<String, List<EntityActionEnum>> selectAction...(两版)

// ★ 扩展方案（客户定制元数据）
List<AggEntityMetadataDto> selectExtensionPlanMetadataList(...)
```

**★★★ 三个关键词必须理解：**

| 词 | 含义 | 为什么重要 |
|---|---|---|
| **`Simple`** | 只有实体基本信息，**不含属性** | 列表页/下拉选实体时用，快 |
| **`Agg` / `AggEntity`** | **聚合实体 = 实体 + 属性 + 子实体 + 关联** | **GraphQL Schema 生成的输入** |
| **`IncludeAssociation`** | 额外带关联关系 | 要多跳查询时用 |
| **`ExtensionPlan`** | **客户扩展方案**（客开改的元数据） | 客开定制 |

**⇒ 「主子表」在元数据层就是 `Agg` 结构 —— 主实体带子实体列表。**

---

## 4. ★★ UdcReferMetaDataService（9 方法）—— 关联关系

```java
static final String TYPE_LEFT_TREE_RIGHT_LIST        // ★ 页面类型常量

List<UdcReferMetaDataDto> selectReferMetaData(...)           // ★ 按查询条件
List<UdcReferMetaDataDto> selectReferMetaDataByEntity(...)   // ★ 按实体查
UdcReferAndAppMetaDataDto selectReferAndAppMetadataByEntity(...)   // 关联 + 应用
UdcReferAndMetaDataDto    selectReferAndMetadata(...)        // 关联 + 元数据

Map<String, Map<String, List<String>>> getParsedEntityPath...(...)  // ★ 路径解析
UdcBaseApplicationMetaDataDto getBaseApplicationMetaDataDto(...)
List<UdcReferMetaDataDto> convert2UdcReferMetadata(...)
```

**★★ `getParsedEntityPath` —— 返回 `Map<实体, Map<字段, List<路径>>>` 结构。**
**⇒ 这是**跨实体引用链解析**（如 A.x → B.y → C.z）。**

**★ `TYPE_LEFT_TREE_RIGHT_LIST` —— 「左树右表」是标准页面类型（关联字段的展示形态）。**

---

## 5. ★★ 页面元数据（7 方法）

```java
UdcPageMetadataV2Dto selectPageInfo(UdcPageMetaDataSearchDto)
UdcPageMetadataV2Dto selectPageInfoBySearchDto(...)
List<UdcPageMetadataV2Dto> selectPageInfoList(...)
List<UdcPageMetadataV2Dto> selectPageInfoListByAppName(...)
List<UdcApplicationMetaDataDto> selectApplicationAndPageLayout4Host(...)  // ★ 宿主用
UdcApplicationMetaDataDto checkAppIncludeUrl(UdcCheckAppIncludeUrlDto)    // ★ 应用是否含URL
```

**★ `selectApplicationAndPageLayout4Host` —— 给**宿主（被嵌入方）**提供页面布局。**

---

## 6. ★ Service / AppService 元数据（6 + 3）

### 6.1 UdcServiceMetadataService（6）

```java
UdcApplicationMetaDataDto selectServiceMetadataByName(String)       // ★ 按名字
UdcApplicationMetaDataDto selectStarterMetadataByName(String)       // ★ Starter
UdcApplicationMetaDataDto selectServiceMetadataByName(dto版本)
UdcApplicationMetaDataDto selectServiceMetadata(dto)
List<UdcApplicationMetaDataDto> selectServiceMetadataByNames(List)
```

**★ `Service` vs `Starter` —— 两种元数据来源（服务 vs 启动器）。**

### 6.2 UdcAppServiceMetaDataService（3）

```java
Map<String, UdcAppServiceMetaDataDto> selectAppServiceByE...(...)           // 按实体
Map<String, String> selectAppServiceByEntityFullName(String, List)          // ★ 实体 → AppService 名
```

**★★ `selectAppServiceByEntityFullName` —— **实体全名 → AppService** 的映射。**
**⇒ 这是**GraphQL Schema 里 mutation/query 名字的来源**（每个实体对应一个 AppService）。**

---

## 7. ★ 枚举元数据（Java 5 + CTP 6 + 项 6）

### Java 枚举（`UdcEnumMetaDataService`）
```java
List<UdcJavaEnumMetaDataDto> selectEnumByAppName(...)
List<UdcJavaEnumMetaDataDto> selectEnumByFullNames(...)
UdcJavaEnumCategoryAndItemDto selectEnumCategoryByAppName(...)   // ★ 分类+项
List<UdcJavaEnumItemMetaDataDto> selectEnumItem4Metadata(...)
```

### CTP 枚举（选项集，`UdcCtpEnumMetaDataService`）
```java
List<UdcCtpEnumDto> selectCtpEnumByAppName(...)
List<UdcCtpEnumDto> selectCtpEnumByAppNameNoLevel(...)    // ★ 不分层级
CtpEnumDto selectParentEnumByCode(...)                    // ★ 父枚举
List<UdcCtpEnumDto> selectCtpEnumByFullNames(...)
List<UdcCtpEnumDto> selectTiledCtpEnumByFullNames(...)    // ★ 平铺
```

### 枚举项（`UdcCtpEnumItemMetaDataService`）
```java
List<UdcCtpEnumItemDto> selectByAppName(...)
UdcCtpEnumItemDto selectById(...)
List<UdcCtpEnumItemTreeDto> selectByEnumCode(...)          // ★ 树形
List<UdcCtpEnumItemDto> selectCascadeTreeByEnumCode(...)   // ★ 级联树
List<UdcCtpEnumItemDto> selectByEnumCodes(...)
```

**★★ 两种枚举必须区分：**

| | `UdcEnum*`（Java 枚举） | `UdcCtpEnum*`（CTP 枚举） |
|---|---|---|
| 来源 | **Java 代码里的 enum** | **数据库配置的选项集** |
| 能否改 | 改代码 | **页面配置** |
| 层级 | 无 | **有（父枚举/树/级联）** |
| 场景 | 固定状态值 | **业务字典（客户可改）** |

**⇒ 业务字典一律用 CTP 枚举（`UdcCtpEnum*`）。**

---

## 8. ★★ `MetadataConvertUtil` —— 转换层（关键词表）

**这个类里有大量常量，直接暴露了元数据的字段名：**

```java
DECIMAL_DIGITS      // 小数位数
REQUIRED            // 必填
MAX_LENGTH          // 最大长度
MIN / MAX           // 最小/最大值
MIN_LENGTH          // 最小长度
UNIQUENESS          // 唯一性
PATTERN             // 正则
VERSION             // 版本
PARENT_ID           // ★ 父ID（主子表/树）
BASIC_DATA          // ★ 基础数据
Set<String> RELATION_DATA_TYPE              // ★ 关联数据类型集合
Map<String, Set<String>> UDC_OUTER_TREE_ENTITY_MAP   // ★ 外部树实体映射
```

**★★★ `PARENT_ID` + `UDC_OUTER_TREE_ENTITY_MAP` —— 证明平台支持：**
1. **树形实体**（parentId 自关联）
2. **外部树实体**（跨应用树）

**★ 转换方法命名规则（能看出转换方向）：**
```java
aggMedata2UdcAgg(...)                 // ctp 聚合 → UDC 聚合
aggResolveMetadata(...)               // ★ 聚合解析成扁平
resolveAgg2FlatList(...)              // ★ 聚合 → 扁平列表（核心）
assAggResolveMetadata(...)            // 关联聚合解析
aggEntityMetaData2Udc(...)            // 实体
attributeMetaData2Udc(...)            // 属性
childrenEntity2Attribute(...)         // ★ 子实体 → 属性（主子表的关键转换）
entityMetaDataDto2UdcIncludeAttri...  // 含属性
entityMetaDataDto2UdcExclud...        // 不含属性
ctpMetaEnumDto2UdcCtpEnum(...)        // CTP 枚举
enumMetaDto2UdcJavaEnum(...)          // Java 枚举
```

**★★★ `childrenEntity2Attribute` —— **子实体转成属性**。**
**⇒ 这说明平台里「主子表」在元数据层表现为**主实体的一个属性，该属性的类型是子实体**。**
**⇒ 这就是 GraphQL 里主子表能嵌套查的原因。**

---

## 9. ★ `UdcMethod2ActionUtil` —— AppService 方法 → 动作权限

```java
static Map<String, List<String>> method2ActionMap     // ★ 方法名 → 动作列表

static List<EntityActionEnum> getActionEnumByAppServiceMetadata(...)
```

**★★ `method2ActionMap` 是**方法名到动作权限码的映射表**。**
**⇒ 说明平台把 AppService 的方法名（如 `create` / `update` / `delete`）**映射成权限动作**，做数据权限控制。**

**★ `EntityActionEnum`（12 个枚举之一）就是动作枚举（增删改查导出等）。**

---

## 10. ★★ 22 个 SearchDto（查询条件的形态）

| SearchDto | 查什么 |
|---|---|
| `UdcEntitiesMetaDataSearchDto` | **多个实体** |
| `UdcEntityMetaDataSearchDto` | 单个实体 |
| `UdcSimpleEntitiesMetaDataSearchDto` | 多个简单实体 |
| `UdcSimpleEntityMetaDataSearchDto` | 单个简单实体 |
| `UdcApplicationMetaDataSearchDto` | 应用 |
| `UdcPagesMetaDataSearchDto` | 多个页面 |
| `UdcPageMetaDataSearchDto` | 单个页面 |
| `UdcPageInfoSearchV2Dto` | 页面信息 V2 |
| `UdcReferMetaDataSearchDto` | 关联 |
| `UdcReferMetaDataSearch_V1_Dto` | 关联 V1 |
| `UdcDtoListMetaDataSearchDto` | DTO |
| `UdcJavaEnumMetaDataSearchDto` / `...s...` | Java 枚举（单/多） |
| `UdcCtpEnumMetaDataSearchDto` / `...s...` | CTP 枚举（单/多） |
| `UdcCtpEnumItemMetaDataSearchDto` / `...s...` | 枚举项（单/多） |
| `UdcObjectMetaDataSearchDto` / `...s...` | 对象（单/多） |
| `UdcGeneralMetaDataSearchDto` | 通用 |
| `UdcMetaDataSearchDto` | 总入口 |
| `UdcPageLayoutSearchDto` | 页面布局 |

**★ 命名规律：`单数=查一个`，`复数=查一批`（Entities/Enums/Objects/Pages）。**
**★ 每个元数据类型都有自己的 SearchDto —— **说明查询是分类型的，不是万能查询**。**

---

## 11. ★★ 12 个元数据枚举（业务语义）

| 枚举 | 含义 |
|---|---|
| **`EntityActionEnum`** | **实体动作（增删改查导出等，权限用）** |
| **`EntityCategoryEnum`** | **实体分类** |
| **`EntityRelationMultiplicityEnum`** | **关联多重性（1:1 / 1:N / N:N）★ 主子表关键** |
| `AttributeSourceTypeEnum` | 属性来源类型 |
| `AttributeCalculateEnum` | 属性计算方式（计算字段） |
| `DependentAppTypeEnum` | 依赖应用类型 |
| `DynamicDependencyTypeEnum` | 动态依赖类型 |
| **`MedaDataPageTypeEnum`** | **页面类型**（注意拼写 MedaData） |
| `PageSourceTypeEnum` | 页面来源类型 |
| `PageUrlTypeEnum` | 页面 URL 类型 |
| **`FrontendPackageTypeEnum`** | **前端包类型（客开前端资源）** |
| `OpenWayEnum` | 开放方式 |

**★★ `EntityRelationMultiplicityEnum` —— 关联多重性枚举，这就是「主子表/多对多」的定义处。**

---

## 12. ★★★ 完整元数据读取链路（推断）

```
① Agent/前端要操作某实体
    ↓
② UdcEntityMetaDataService.selectAggEntity(SearchDto)
    ├─ MetadataConvertUtil.aggResolveMetadata    （ctp 聚合 → UDC）
    ├─ MetadataConvertUtil.childrenEntity2Attribute（子实体 → 属性）
    └─ 得到 UdcEntityMetaDataDto（含 List<UdcAttributeMetaDataDto>）
    ↓
③ 需要权限 → UdcMethod2ActionUtil.getActionEnumByAppServiceMetadata
             + EntityActionEnum
    ↓
④ 需要页面 → UdcPageInfoMetaDataService.selectPageInfo
⑤ 需要关联 → UdcReferMetaDataService.selectReferMetaData
⑥ 需要枚举 → UdcCtpEnumMetaDataService.selectCtpEnumByAppName
    ↓
⑦ 汇总给 GraphQL Schema 生成（SeeyonSchemaService）
```

**⚠️ 上述 ①~⑦ 的**衔接关系是推断**（各 Service 独立，我没读到调用方）。**
**⇒ 等级：`UNVERIFIED`（各 Service 能力确定，编排关系未验证）。**

---

## 13. ★ 与之前结论的一致性校验

**我之前在 `01B-metadata-loading-CORRECTION.md` 里写：**
```
设计态 = MySQL udc_entity / udc_attribute
运行态 = Redis(180h) → OSS
presetData/attribute.json 仅系统属性模板
```

**本轮新证据的补充：**
1. **`oss` 包有 5 个 `*4OssService`** —— 确认了 OSS 存储层的存在 ✅
2. **`MetadataConvertUtil` 的 `PARENT_ID` / `UDC_OUTER_TREE_ENTITY_MAP`** —— 树形实体的机制
3. **`childrenEntity2Attribute`** —— 主子表在元数据层是「属性」形态（**这是新知识**）

**⚠️ `oss` 包的方法我**没 dump 到**（javap 返回空，可能方法在父类且父类不在这个 jar）。**
**⇒ OSS 的具体读写方法仍是空白。**

---

## 14. 未覆盖

| 项 | 说明 |
|---|---|
| `oss` 包 5 个 Service 的方法 | **javap 返回空**，父类不在本 jar |
| `resource` 包 3 个 Service 的方法 | **同上** |
| `UdcMetaDataAppV2Service`（19 方法） | 只看了开头，未全读 |
| 各 Service 之间的编排关系 | **未验证**（可能由 controller 串起来） |
| `UdcMetaDataController` 的 REST 路径 | 未读 |
| Redis 缓存的具体 TTL 和 key 结构 | 未读（沿用旧结论 180h） |
| 22 个 SearchDto 的字段 | 未 dump |
| `UdcEntityMetaDataDto` 的字段 | 未 dump（41 个 DTO 太多） |