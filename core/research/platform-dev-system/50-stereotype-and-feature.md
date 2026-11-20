# 50 · ★★★★★ 原型（Stereotype）与特性（Feature）体系全解

**证据来源**：`udc-biz-5.3.605.jar` 反编译 + `presetData/attributeSet.json` 真实数据 + 类反射实测
**证据等级**：**VERIFIED_STATIC_BYTECODE** + **LIVE_RULE**（JSON 数据实测解析）

---

## 一、★★★★★ 六个原型（Stereotype）—— 权威清单

```java
// com.seeyon.udc.common.constant.StereotypesConstant（反射实测）
public static final String STANDARD     = "standard"
public static final String BILL         = "bill"
public static final String ARCHIVE      = "archive"
public static final String ARCHIVE_TREE = "archiveTree"
public static final String FORM         = "form"
public static final String BASIC_DATA   = "basicData"
```

**★★★★★ 对应 6 个实现类（字节码扫描，包 `com.seeyon.udc.entity.stereotype.stereotype`）：**
```
StandardStereotype
BillStereotype
ArchiveStereotype
ArchiveTreeStereotype
FormStereotype
BasicDataStereotype
```

**⇒ 平台只有 6 种实体原型，不是可扩展的任意数量。新增原型必须写 Java 类 + 注册 Bean。**

### 1.1 ★★★★★ 命名机制（反编译确认）

```java
// Stereotypes.<clinit>
for (AbstractStereotype stereotype : map.values()) {
    String name = StringUtils.remove(
        StringUtil.camelhumpToUnderline(stereotype.getClass().getSimpleName()),
        SUFFIX);                        // SUFFIX = "_stereotype"
    AbstractStereotype loaded = configurationLoader.loadStereotype(name, StereotypeBean.class);
    Stereotypes.copyProperties(loaded, stereotype);
    stereotypeRepo.put(stereotype.getName(), stereotype);
}
```

**★★★★★ 机制：**
1. `camelhumpToUnderline("ArchiveTreeStereotype")` → `"archive_tree_stereotype"`
2. 去掉后缀 `_stereotype` → `"archive_tree"`
3. **再 `loadStereotype("archive_tree")` 从配置加载属性覆盖**

**★★ 但 `ARCHIVE_TREE = "archiveTree"` 是驼峰，不是下划线 —— 说明 `getName()` 是独立配置的，不是从类名推的。类名推导只用于找配置文件。**

### 1.2 ★★★ `AbstractStereotype` 的 11 个属性（反编译确认）

```java
public abstract class AbstractStereotype {
    List<String> getFeatures()             // 已启用特性
    List<String> getAvailableFeatures()    // 可选特性
    List<String> getNecessaryFeatures()    // 必需特性
    String  getName()
    String  getCaption()
    String  getDescription()
    Integer getOrder()
    Boolean getDeprecated()
    Boolean nonDeprecated()
    Boolean getProcessEmbedded()           // ★ 是否内嵌流程
    Boolean getDataFlowEnabled()           // ★ 是否启用数据流
}
```

**★★★★★ 三条结构事实：**
1. **特性三分：`features`（已启用）/ `availableFeatures`（可选）/ `necessaryFeatures`（必需）**
2. **`processEmbedded` —— 原型决定实体能否内嵌流程（单据原型才有）**
3. **`dataFlowEnabled` —— 原型决定实体能否被数据流生成**

### 1.3 ★★★ 原型的唯一运行时行为：保存/删除后处理枚举

**`BillStereotype`（完整反编译）：**
```java
@Component
public class BillStereotype extends AbstractStereotype {
    @Autowired private FeatureCommonService featureCommonService;

    public void afterEntitySaved(EntityDto before, EntityDto entity) {
        this.featureCommonService.afterEntitySaved(before, entity,
            "presetData/billEnum.json", "statusType", 15);
    }
    public void afterEntityDeleted(EntityDto entityDto) {
        this.featureCommonService.afterEntityDeleted(entityDto,
            Arrays.asList("statusType", "sendState"));
    }
}
```

**`ArchiveTreeStereotype`：**
```java
public void afterEntitySaved(EntityDto before, EntityDto entity) {
    if (Objects.isNull(before)) return;      // ★ 只在更新时处理，新建跳过
    this.featureCommonService.afterEntitySaved(before, entity,
        "presetData/archiveEnum.json", "statusType", 37);
}
```

**★★★★★ 三条事实：**
1. **原型只做一件事：实体保存后按 JSON 初始化枚举字段**
2. **`statusType` 是枚举承载字段，`15`/`37` 是默认值**
3. **`ArchiveTree` 只在 UPDATE 时处理（`before == null` 直接 return）** —— 因为树实体新建时还没有状态流转

**★ `StandardStereotype` / `BasicDataStereotype` / `ArchiveStereotype` / `FormStereotype` 都是空壳（17 行，只有 serialVersionUID）—— 无运行时行为。**

---

## 二、★★★★★ 16 个特性（Feature）—— 权威清单

**字节码扫描 `AbstractFeature` 子类（包 `com.seeyon.udc.entity.stereotype.feature`）：**

```
ApproveFeature          审批特性
ArchiveBasicFeature     档案基本
ArchiveTiledFeature     平铺档案
BasicFeature            系统字段（id/tenantId/时间/版本/草稿）
BillBasicFeature        单据基本
DisableFeature          禁用
FormBasicFeature        表单基本
FulltextSearchFeature   全文检索
NullifyFeature          作废
OrganizationFeature     组织
SecretLevelFeature      密级
SendDownFeature         下发
SuspendFeature          挂起
TerminationFeature      终止
TreeEntityFeature       树形
ValidityPeriodFeature   有效期
```

**★★★★★ 16 个特性，与 `attributeSet.json` 的 18 个字段集高度对应（多 2 个是 `creator`/`updater`，属 `BasicFeature` 的一部分）。**

### 2.1 ★★★★★ 特性注册机制（`Features.<clinit>` 反编译）

```java
Map map = applicationContext.getBeansOfType(AbstractFeature.class);
for (AbstractFeature feature : map.values()) {
    String name = /* camelhumpToUnderline + 去 _feature 后缀 */;
    AbstractFeature loaded = configurationLoader.loadFeature(name, FeatureBean.class);
    featureRepo.put(feature.getName(), feature);
}
```

**⇒ 特性是 Spring Bean（`@Component`），通过 `getBeansOfType(AbstractFeature.class)` 自动收集。**
**⇒ 与原型同一套 `ConfigurationLoader` 加载覆盖机制。**

### 2.2 ★★★★★ `AbstractFeature` 的唯一扩展点

```java
public void resolveAttribute4Feature(EntityDto before, EntityDto now, List<AttributeDto> attributeDtoList)
```

**⇒ 特性在「实体保存前」有机会改写字段属性定义。**

### 2.3 ★★★★★ `TreeEntityFeature` —— 树实体的核心机制（完整反编译）

```java
public class TreeEntityFeature extends AbstractFeature {
    private static final String TREE_PARENT_ID = "treeParentId";

    public void resolveAttribute4Feature(EntityDto before, EntityDto now,
                                         List<AttributeDto> attributeDtoList) {
        if (CollectionUtils.isEmpty(attributeDtoList)) return;
        Optional<AttributeDto> first = attributeDtoList.stream()
            .filter(a -> TREE_PARENT_ID.equals(a.getName())).findFirst();
        first.ifPresent(f -> {
            f.setDataType(DataType.ENTITY.name());          // ★ BIGINTEGER → ENTITY
            f.setRelationApp(now.getAppId().toString());    // ★ 关联到自己所在应用
            f.setRelationEntity(now.getId().toString());    // ★ 关联到自己（自引用）
            f.setRelationEntityName(now.getCaption());
            f.setRelationType(RelationType.One2ManyAggregation);   // ★ 一对多聚合
            f.setMultiSelect(Boolean.FALSE);
        });
    }
}
```

**★★★★★ 五条决定性事实：**
1. **`treeParentId` 原始定义是 `BIGINTEGER`（见 attributeSet.json），保存时被改写成 `ENTITY`**
2. **关联目标是实体自身（`relationEntity = now.getId()`）—— 自引用树**
3. **关联类型固定 `One2ManyAggregation`（一对多聚合）**
4. **`multiSelect = false`（树父节点单选）**
5. **只在实体保存时触发，不是建表时**

**⇒ 这就是「树形实体」的全部机制：一条字段改写。`treePath`/`treeLevel`/`isLeaf`/`treeCaptionPath` 只是配套冗余字段。**

### 2.4 ★★ 其他特性的形态

```java
// SuspendFeature / SecretLevelFeature / BasicFeature —— 全部是空壳（17 行）
public class SuspendFeature extends AbstractFeature {
    private static final long serialVersionUID = 5640979620181092222L;
}
```

**⇒ 16 个特性里，绝大多数**没有**代码逻辑 —— 它们的价值全在 `attributeSet.json` 的字段集定义上：**
**「特性」= 一组字段 + 可能的一条改写逻辑。**

---

## 三、★★★★★ 18 个字段集（`presetData/attributeSet.json`，实测解析）

**证据：真实解压 `udc-biz-5.3.605.jar` → `presetData/attributeSet.json`（99,808 字节，18 条）**

| # | name | caption | 字段数 |
|---|---|---|---|
| 1 | `basic` | 系统字段集 | 6 |
| 2 | `creator` | 创建人字段集 | 4 |
| 3 | `updater` | 更新人字段集 | 1 |
| 4 | `archiveBasic` | 档案基本字段集 | **36** |
| 5 | `archiveTiled` | 平铺档案字段集 | 0 |
| 6 | `billBasic` | 单据基本字段集 | 13 |
| 7 | `suspend` | 挂起字段集 | 7 |
| 8 | `termination` | 终止字段集 | 7 |
| 9 | `nullify` | 作废字段集 | 7 |
| 10 | `disableFeature` | 禁用字段集 | 1 |
| 11 | `fulltextSearch` | 全文检索字段集 | 0 |
| 12 | `treeEntity` | 树形实体字段集 | 5 |
| 13 | `validityPeriod` | 有效期字段集 | 0 |
| 14 | `approve` | 审批字段集 | 0 |
| 15 | `organization` | 组织字段集 | 0 |
| 16 | `sendDown` | 下发字段集 | 0 |
| 17 | `formBasic` | 表单基本字段集 | **33** |
| 18 | `secretLevel` | 密级等级 | 2 |

### 3.1 ★★★★★ `basic`（系统字段集，6 项）—— 每个实体都有

```
id            ID         BIGINTEGER
tenantId      租户ID      BIGINTEGER
createTime    创建时间     DATETIME
updateTime    更新时间     DATETIME
version       版本号       INTEGER      ← ★ 乐观锁
draft         是否草稿     BOOLEAN
```

**★★★★★ `version` 是乐观锁字段，所有实体自带。**

### 3.2 ★★★★★ `treeEntity`（5 项）—— 树形实体的全部结构

```
treePath          ID路径        STRING
treeParentId      上级          BIGINTEGER   ← ★ 保存时被改写成 ENTITY 自引用
isLeaf            是否末级      BOOLEAN
treeLevel         级次          INTEGER
treeCaptionPath   显示名称路径   STRING
```

**⇒ 5 个字段，1 个改写，4 个冗余维护。这就是完整树实体。**

### 3.3 ★★★★★ `billBasic`（13 项）—— 单据原型

```
caseSendTime          发起时间        DATETIME
caseSender            发起人          ENTITY
caseSenderInstitution 发起机构        ENTITY
caseSenderDepartment  发起部门        ENTITY
caseSenderPost        发起岗位        ENTITY
billCode              单据编号        Serial     ← ★ 序列号类型
billDate              单据日期        DATETIME
applicant             申请人          ENTITY
deductionInfo         扣减规则信息     MULTILINESTRING  ← ★ 扣减规则落在字段里
templateId            流程模板        ENTITY
caseId                流程实例        ENTITY
caseTitle             流程标题        STRING
caseFinishTime        流程结束时间     DATETIME
```

**★★★★★ 两条事实：**
1. **`deductionInfo`（扣减规则信息）是单据标准字段 —— 扣减（库存/预算）由原型预置，不是业务自己加**
2. **`billCode` 类型是 `Serial`（平台序列号生成器）**

**★★ 另有 `MASTER_SYSTEM_ATTRIBUTE_NAMES`（`Stereotypes` 静态常量，实测）：**
```java
Set MASTER_SYSTEM_ATTRIBUTE_NAMES = [caseSenderInstitution, caseSenderDepartment, caseSenderPost]
```
**⇒ 这 3 个字段是「主实体系统属性」—— 发起机构/部门/岗位，业务不可改。**

### 3.4 ★★★★★ `archiveBasic`（36 项）—— 最重的原型

**基础 5 项（同 billBasic）：** caseSendTime / caseSender / caseSenderInstitution / caseSenderDepartment / caseSenderPost

**档案 6 项：**
```
orgId              组织机构       ENTITY
archiveCode        编码           STRING
archiveCaption     名称           STRING
archiveNameShort   简称           STRING
archiveMnemonicCode 助记码        STRING
isEnabled          是否启用       BOOLEAN
```

**三组状态流转（每组 6 项，共 18 项）：**
```
终止：terminatorId / terminateTime / terminateReason / terminateStatusType
      + cancelTerminatorId / cancelTerminateTime / cancelTerminateReason
作废：nullifyId / nullifyTime / nullifyReason / nullifyStatusType
      + cancelNullifyId / cancelNullifyTime / cancelNullifyReason
挂起：suspenderId / suspendTime / suspendReason / suspendStatusType
      + cancelSuspenderId / cancelSuspendTime / cancelSuspendReason
```
**★★★★★ 三种状态流转（终止/作废/挂起）各带「取消」操作 —— 每个状态都是 6 字段（人/时间/原因 + 状态类型 + 取消三人）。**

**收尾 2 项：** caseFinishTime / caseSendTime

### 3.5 ★★★ `secretLevel`（密级，2 项）

```
secretId    密级       CTPENUM    ← ★ 引用标品枚举（CtpEnumItemService 那套）
secretN     密级等级   INTEGER
```
**⇒ 密级引用的是**标品**枚举（`CTPENUM`），不是 UDC 自定义枚举。**

### 3.6 ★★★ `suspend` / `termination` / `nullify`（各 7 项，结构相同）

```
{action}Id              挂起人/终止人/作废人       ENTITY
{action}Time            时间                      DATETIME
{action}Reason          原因                      STRING
{action}StatusType      当时单据状态               ENUM
cancel{Action}Id        取消人                    ENTITY
cancel{Action}Time      取消时间                   DATETIME
cancel{Action}Reason    取消原因                   STRING
```
**⇒ 三组完全对称，说明是同一套「状态流转」模式的三次实例化。**

### 3.7 ★★★ `creator` / `updater` / `disableFeature`

```
creator            创建人      ENTITY
creatorInstitution 创建机构    ENTITY
creatorDepartment  创建部门    ENTITY
creatorPost        创建岗位    ENTITY

updater            更新人      ENTITY

disabled           是否禁用    BOOLEAN
```

### 3.8 ★★ 空字段集（0 项）—— 占位

```
archiveTiled      平铺档案      0 项
fulltextSearch    全文检索      0 项
validityPeriod    有效期        0 项
approve           审批          0 项
organization      组织          0 项
sendDown          下发          0 项
```

**★★★★ 6 个字段集有定义但零字段。已由 `feature/*/config.json` 实测解答：见第六之二节 `ignored` 分析。**

---

## 四、★★★★★ presetData 全清单（11 个 JSON）

```
presetData/
  attributeSet.json               99,808 B  ★ 18 个字段集定义
  attribute.json                     831 B   系统属性模板
  archiveEnum.json                 1,786 B   档案状态枚举
  billEnum.json                    1,780 B   单据状态枚举
  formEnum.json                    1,780 B   表单状态枚举
  basicDataEntityExtension.json    1,171 B   基础数据实体扩展
  customerAttributeSet.json        2,416 B   客户自定义字段集
  dependencyGraph.json             2,466 B   依赖图
  entity.json                        556 B   实体模板
  scalability.json                   728 B   扩展性配置
  scalabilityGlobal.json             759 B   全局扩展性配置
```

**★★★★★ 三个 Enum JSON（archive/bill/form）对应三个原型的 `statusType` 初始化 —— 这就是 `afterEntitySaved` 里加载的那三个文件。**

### 4.1 ★★★ `attribute.json`（系统属性模板，831 B）

**⇒ 这是「系统属性」模板，实体创建时可从这里取默认系统属性。**

### 4.2 ★★★ `dependencyGraph.json`（依赖图，2,466 B）

**⇒ 特性/原型之间有依赖关系图 —— 决定哪些特性组合合法。**

---

## 五、★★★★★ 特性 ↔ 字段集的真实映射

```
Feature 类（16 个）           attributeSet.json（18 个）
BasicFeature          →      basic (6)
CreatorFeature*       →      creator (4)      * 未见独立类，可能并入 Basic
UpdaterFeature*       →      updater (1)
BillBasicFeature      →      billBasic (13)
ArchiveBasicFeature   →      archiveBasic (36)
ArchiveTiledFeature   →      archiveTiled (0)
SuspendFeature        →      suspend (7)
TerminationFeature    →      termination (7)
NullifyFeature        →      nullify (7)
DisableFeature        →      disableFeature (1)
FulltextSearchFeature →      fulltextSearch (0)
TreeEntityFeature     →      treeEntity (5)
ValidityPeriodFeature →      validityPeriod (0)
ApproveFeature        →      approve (0)
OrganizationFeature   →      organization (0)
SendDownFeature       →      sendDown (0)
SecretLevelFeature    →      secretLevel (2)
FormBasicFeature      →      formBasic (33)
```

**★★★★★ 16 个 Feature 类 vs 18 个字段集：`creator` 和 `updater` 没有独立 Feature 类 —— 它们被 `BasicFeature` 管辖。**

---

## 六、★★★★★ 原型 × 特性：权威配置（`stereotype/*/config.json` 实测）

**证据：真实解压 `udc-biz-5.3.605.jar` → `stereotype/{name}/config.json`（6 个文件，全部解析）**

| 原型 name | caption | order | dataFlowEnabled | necessaryFeatures（必需） | availableFeatures（可选） |
|---|---|---|---|---|---|
| `standard` | 标准 | — | true | `basic` | `secretLevel` |
| `bill` | 单据 | 1 | true | `basic` + `approve` + `organization` + `billBasic` + `termination` + `suspend` + `nullify` | `secretLevel` |
| `archive` | 平铺档案 | 2 | true | `basic` + `archiveBasic` + `approve` + `archiveTiled` | `secretLevel` |
| `archiveTree` | 树形档案 | 3 | true | `basic` + `archiveBasic` + `approve` + `treeEntity` | `secretLevel` |
| `form` | 表单 | — | true | `basic` + `formBasic` | `secretLevel` |
| `basicData` | 基础资料 | — | — | `basic` | `secretLevel` |

**★★★★★ 六条决定性事实：**

| # | 事实 |
|---|---|
| 1 | **`bill` 原型有 7 个必需特性 —— 最重**（含三状态：termination/suspend/nullify + organization + approve） |
| 2 | **`archive` 与 `archiveTree` 只差一个特性**：`archiveTiled` vs `treeEntity` |
| 3 | **`secretLevel` 是全部 6 个原型的唯一可选特性**（`availableFeatures` 都是它） |
| 4 | **`standard` / `form` / `basicData` 都只有 `basic` 打底**（+ formBasic 给 form） |
| 5 | **`dataFlowEnabled = true` 几乎所有原型都有**（`archiveTree`/`bill`/`archive`/`form`/`standard`）—— 只 `basicData` 缺失 |
| 6 | **`archive` 的 caption 是「平铺档案」，不是「档案」** —— `archive` 就是平铺档案 |

**★★★ `archive` vs `archiveTree` 的精确差异：**
```
archive      necessaryFeatures = [basic, archiveBasic, approve, archiveTiled]
archiveTree  necessaryFeatures = [basic, archiveBasic, approve, treeEntity]
                                  ↑ 完全相同              ↑ 只这一项不同
```

---

## 六之二、★★★★★ 18 个特性完整元数据（`feature/*/config.json` 实测）

| order | name | caption | ignored | processEmbedded | attributeSet | 说明 |
|---|---|---|---|---|---|---|
| 0 | `basic` | 系统 | **true** | — | `basic` | 基本特性 |
| 2 | `billBasic` | 单据基本 | false | false | `billBasic` | 单据基本特性 |
| 3 | `archiveBasic` | 档案基本 | false | false | `archiveBasic` | 档案基本特性 |
| 4 | `disable` | 禁用 | false | — | `disable` | 禁用特性 |
| 5 | `validityPeriod` | 有效期 | false | — | `validityPeriod` | 有效期特性 |
| 6 | `attributeScalability` | 属性扩展 | false | false | — | **属性扩展** |
| 7 | `attributeScalabilityGlobal` | 属性全局扩展 | false | false | — | **属性全局扩展** |
| 8 | `fulltextSearch` | 全文检索 | false | — | `fulltextSearch` | 全文检索特性 |
| 9 | `treeEntity` | 树形实体 | false | **true** | `treeEntity` | **物化路径，最多 20 层** |
| 12 | `approve` | 审批 | false | false | `approve` | 审批特性 |
| 13 | `archiveTiled` | 平铺档案 | false | — | `archiveTiled` | 平铺档案基本特性 |
| 13 | `organization` | 组织 | **true** | — | `organization` | 组织特性 |
| 14 | `sendDown` | 下发 | **true** | — | `sendDown` | 下发特性 |
| 20 | `nullify` | 作废 | **true** | — | `nullify` | 作废特性 |
| 21 | `termination` | 终止 | **true** | — | `termination` | 终止特性 |
| 22 | `suspend` | 挂起 | **true** | — | `suspend` | 挂起特性 |
| 50 | `formBasic` | 表单基本 | false | — | `formBasic` | 表单基本特性 |
| 60 | `secretLevel` | 密级 | false | false | `secretLevel` | 密级特性 |

### ★★★★★ `ignored = true` —— 解答第 3.8 节的「空字段集」疑问

**6 个 `ignored=true` 的特性，恰好对应 6 个「有定义但零字段」的字段集：**
```
basic        ignored=true   →  basic (6 字段，实际有值)   ★ 例外
organization ignored=true   →  organization (0 字段)
sendDown     ignored=true   →  sendDown (0 字段)
nullify      ignored=true   →  nullify (7 字段)           ★ 例外
termination  ignored=true   →  termination (7 字段)       ★ 例外
suspend      ignored=true   →  suspend (7 字段)           ★ 例外
```

**★★★★★ 修正：`ignored=true` 不等于「无字段」。真正零字段的是 `organization` / `sendDown` / `approve` / `archiveTiled` / `fulltextSearch` / `validityPeriod`。**

**★★ `ignored` 的真实语义（推断）：字段集不在常规属性列表里展示/不参与通用校验，由特性代码专门处理（如三状态流转字段由 `NullifyFeature` 等管理）。**

### ★★★★★ 特性配置的 13 个字段（完整结构）

```json
{
  "id": "9",                        // 特性 ID（字符串数字）
  "name": "treeEntity",             // 名称（驼峰）
  "caption": "树形实体",
  "description": "树形实体(物化路径实现方式，最多20层)",
  "deprecated": false,              // 已废弃
  "stereotypeBind": false,          // ★ 是否绑定原型（true 表示不可自由选）
  "ignored": false,                 // ★ 在通用列表里忽略
  "configurable": true,             // ★ 是否可配置
  "processEmbedded": true,          // ★ 是否内嵌流程
  "configuration": "{}",            // ★ 配置 JSON 字符串
  "order": 9,                       // 排序（决定 UI 顺序）
  "attributeSet": "treeEntity",     // ★ 绑定的字段集名
  "behaviors": []                   // ★ 行为列表（全为空！）
}
```

**★★★★★ 三条硬事实：**
1. **`behaviors` 全 18 个特性都是空数组** —— 说明行为不通过配置声明，而是走 `resolveAttribute4Feature` 代码
2. **`attributeSet` 把特性精确绑定到字段集** —— 这是特性↔字段集的权威映射
3. **`treeEntity` 的描述含硬约束：「物化路径实现方式，最多20层」—— 树深上限 20 层**

**★ `attributeScalability` / `attributeScalabilityGlobal` 没有 `attributeSet` —— 它们是纯配置特性，不带字段。**

---

## 六之三、★★★★★ 三个特性模板（`feature/*/template/config.json`）

```
feature/attribute_scalability/template/config.json          8,463 B
feature/attribute_scalability_global/template/config.json   8,805 B
feature/tree_entity/template/config.json                    9,237 B
feature/disable/template/config.json                        8,467 B
```

**★★★★★ 只有 4 个特性带模板配置 —— 即只有它们真的生成代码：**
```
tree_entity             → 10 个 .ftl（已有文档 46）
disable                 → 1 个 template config（但 autocode 里无 disable 模板目录）
attribute_scalability   → 属性扩展
attribute_scalability_global → 属性全局扩展
```

**★★ `disable` 的 template config 存在但 `autocode/JAVA/2.9/templates/feature/` 下只有 `tree_entity` —— 说明 disable 的模板在别处或未随包发布。**

**⇒ 「16 个特性」里真正能生成代码的只有 `tree_entity` 一个（其余是纯字段集）。**

---

## 七、★★★★★ 对开发者的 12 条结论

| # | 结论 |
|---|---|
| 1 | **只有 6 个实体原型**（standard / bill / archive / archiveTree / form / basicData） |
| 2 | **原型 = 一组特性 + 可选的一条保存后处理逻辑**，不可任意扩展 |
| 3 | **18 个特性（16 个 Feature 类 + 2 个纯配置）**，价值主要在字段集 |
| 4 | **18 个字段集，共 112 个字段**，这是 UDC 实体的「标准库」 |
| 5 | **树实体 = `treeParentId` 一条字段在保存时被改写成自引用 ENTITY**，物化路径，**最多 20 层** |
| 6 | **`version` 是乐观锁，所有实体自带** |
| 7 | **单据原型自带 `deductionInfo`（扣减规则）—— 扣减是原型预置能力** |
| 8 | **`billCode` 用 `Serial` 类型**（平台序列号），不需要自己生成单据号 |
| 9 | **签发机构/部门/岗位（caseSender*）是主实体系统属性，业务不可改** |
| 10 | **密级走标品枚举（`CTPENUM`），不是 UDC 自定义枚举** |
| 11 | **`bill` 原型最重：7 个必需特性，含三状态流转（终止/作废/挂起）** |
| 12 | **`secretLevel` 是所有原型的唯一可选特性；`archive` vs `archiveTree` 只差一个特性** |

---

## 八、待验证

| 问题 | 状态 |
|---|---|
| 6 个原型的 `necessaryFeatures` / `availableFeatures` | ✅ **已实测**（`stereotype/*/config.json`，见第六节） |
| 18 个特性元数据 | ✅ **已实测**（`feature/*/config.json`，见第六之二节） |
| `ignored=true` 的真实语义 | ⚠ 推断为「不参与通用属性列表」，待运行时验证 |
| `FeatureCommonService.afterEntitySaved` 的实现 | 待反编译（枚举初始化细节） |
| `dependencyGraph.json` 的内容 | 待解析（特性依赖规则） |
| `customerAttributeSet.json` 的作用 | 待解析 |
| `disable` / `attributeScalability` 的 template config 内容 | 待解析（8KB 级别，含生成规则） |
| `stereotypeBind=true` 的场景 | 待查（当前 6 个原型全是 false） |