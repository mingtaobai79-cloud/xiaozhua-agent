# 设置域 · 导入导出模板（Excel Template）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> 证据等级：**LIVE PASS**（2026-10-21，REST 接口提交 + DB 回读 + search 复查）
> 实现：`components/udc/setting/excel_template_constraints.py`
> 脚本：`tools/core/setting/excel_template_seed.py`

## 一、这是什么

页面：**应用设计 → 设置 → 导入导出模板**

左边选实体，右边两个 tab（**导入模板** / **导出模板**），每个 tab 下列出该实体的模板。
一个模板 = 选实体 + 配置要导入/导出哪些字段 + 每个字段的**表头名称**。

落库表：`ctp_excel_export_template`

## 二、接口是 REST，不是 GraphQL

```
POST /service/udc/excel/search                        列表（内置模板）
POST /service/udc/excel/search-custom-list-by-conditions   列表（自定义模板）
POST /service/udc/excel/create-template               新建
POST /service/udc/excel/update-template               更新
POST /service/udc/excel/select-by-id                  详情
POST /service/udc/excel/delete                        删除（body 用 {"id": ...}）
POST /service/udc/excel/get-entity-metadata           实体元数据（选实体后拉字段）
```

⚠ **路径前缀是 `/service/udc/excel/*`**，不是 `/service/excel/*`
（后者报 `server_404 excel 服务不存在，请重启服务或重新发布应用后再试`）。

## 三、PageRequest 形态（反编译 boot-core 5.3.345）

```java
PageRequest extends ListRequest {
    PageInfo pageInfo;                    // 分页
}
ListRequest {
    Map<String,Object> params;            // 查询条件
    Sort sort;
}
PageInfo {
    int pageNumber = 1;
    int pageSize = 20;
    int pages; int total; boolean needTotal; boolean needMore;
}
```

正确 body：

```json
{"pageInfo":{"pageNumber":1,"pageSize":50},"params":{"appId":"..."}}
```

⚠ 写成 `{"page":1,"size":10,"params":{...}}` → `BOOT_3000 message:null`。

## 四、`isCustom` 决定进哪个列表（重要坑）

反编译 `ExcelExportTemplateService.selectPageByCondition`：

```java
public PageData<ExcelExportTemplateDto> selectPageByCondition(PageInfo pageInfo, Map columnMap, Sort sort) {
    columnMap.put("isCustom", false);      // ★ 强制 false
    columnMap.put("deleteFlag", false);
    ...
}
```

**结论**：
- `search` 接口**只查 `isCustom=false`**（内置/标准模板）
- `search-custom-list-by-conditions` **只查 `isCustom=true`**（用户自定义模板）
- 建模板时 `isCustom=true` → 只会出现在自定义列表；`false` → 出现在主列表

我第一版建了 `isCustom=true`，`search` 查不到（`该实体模板数: 0`），
改成 `false` 后两个模板都能在 `search` 里看到。

## 五、ExcelExportTemplateDto（反编译 boot-starter-excel 5.3.318）

```java
Long    id
String  name                  // @NotNull @Size(max=20)
String  appId
Long    appGuid = -1L
String  appName
String  mainFullName          // ★ 实体全类名
Long    createUserId = -1L
String  signatureCode = ""    // md5 签名
String  metadataContent = ""  // ★ 列定义（JSON 字符串）
String  excelHeadInfo = ""    // ★ 表头信息（JSON 字符串）
Boolean isCustom = true
Boolean isImport = true       // ★ true=导入模板 false=导出模板
Boolean isDefault = false
Boolean deleteFlag = false
List<List<ExcelColumnDto>> columnList;   // @Min(1) —— 但 search 读回来恒为 null
Long    belongGroupId = -1L
Long    originalId
List<String> importReminders
String  authInfo
```

⚠ **`columnList` 读回来是 null**。列定义存在 `metadataContent` / `excelHeadInfo` 里，
都是 JSON 字符串，二维数组（外层 sheet、内层列）。提交时两个都写同一份。

## 六、ExcelColumnDto（反编译，40+ 字段，关键如下）

```java
String  attributeFullName           // ★ 属性全名 <实体全类名>.<字段名> —— 唯一锚点
String  parentEnumAttributeFullName
String  entityType                  // MASTER_ENTITY / SUB_ENTITY
List<List<String>> levelPath        // 层级路径 [appName, entityFullName, entityCaption, attrFullName, attrCaption]
String  type                        // java.lang.String
Boolean dataI18n
String  dataType                    // STRING / INTEGER / BIGINTEGER / DECIMAL / DATE / DATETIME / BOOLEAN / ENTITY / CTPENUM
String  jsr303
Integer curColIndex
CtpEnumType ctpEnumType
Long    rootEnumId
Integer enumLevel
List<String> enums
String  enumClass
List<String> ctpEnums
Map<String,Object> ctpEnumMap
Boolean unique
Boolean matchQuery
Boolean parentUnique
Boolean isAssUniqueField
Boolean notBlankOrNotNull
Boolean parentNotBlankOrNotNull = true
Boolean multiSelect
Boolean parentAssMultiSelect
String  relation                    // NONE / ...
String  relationApp
String  relationEntity
String  columnType                  // varchar(50) 等物理类型，可 null
String  displayName                 // ★ Excel 表头显示名
Boolean isHidden
SafetyDto safetyDto                 // {validate,encryption,mask,auditLog,permission}
Map     relationMap
List<String> relationValueList
Map     enumCodeAndNameMap
MaskableDto maskable
String  cellValue
```

## 七、构造要点

1. **`attributeFullName` 是唯一锚点**：`<实体全类名>.<字段名>`，平台靠它定位字段。
2. **`displayName` 是 Excel 表头**，默认取字段 `caption`，可自定义 —— 这就是用户说的"配置名称"。
3. **`levelPath`** 建议给：`[[appName, entityFullName, entityCaption, attrFullName, attrCaption]]`。
4. **`safetyDto`** 建议带上：`{validate:true, encryption:"NOT_ENCRYPTION", mask:"None", auditLog:false, permission:false}`。
5. 无关联的普通字段：`relation="NONE"`, `relationApp=<appName>`, `relationEntity=null`。
6. `columnType` 可 null（平台自己从实体推导）。

## 八、本应用实测（LIVE PASS）

实体：`郑杰验证实体` / `com.seeyon.datamigration…domain.entity.ZxjVerifyEntity` / id=`5417588098661281954`

该实体 16 个属性（含系统字段）：
```
code 编号 STRING / id ID BIGINTEGER / tenantId 租户ID BIGINTEGER
createTime 创建时间 DATETIME / updateTime 更新时间 DATETIME / version 版本号 INTEGER
draft 是否草稿 BOOLEAN / title 名称 STRING / amount 金额 DECIMAL / bizDate 日期 DATE
creator 创建人 ENTITY / creatorInstitution 创建机构 ENTITY …（共 16）
```

建成两个模板（16 列，表头 = 字段 caption）：

```
验收导入模板  id=-3078489123242493101  isImport=True   isCustom=False  16 列
验收导出模板  id=-2357100757691115378  isImport=False  isCustom=False  16 列
表头: ['编号','ID','租户ID','创建时间','更新时间','版本号','是否草稿','名称',...]
```

DB 回读：`metadata_content` = `excel_head_info` = 20718 字节，`import_flag` 分别 1/0。

## 九、脚本用法

```bash
# 只读：拉实体 + 属性 + 现有模板
python tools/core/setting/excel_template_seed.py --entity 郑杰验证实体 --dump

# 建导入 + 导出两个模板
python tools/core/setting/excel_template_seed.py --entity 郑杰验证实体 \
    --i-have-write-authorization
```

## 九、关联实体字段的展开（用户截图那个下拉框）

页面上「创建人 ▸ 姓名 ▸ 编号/性别/工作电话…」这种**树形多选框**，
对应的数据结构是 **`levelPath` 两层**：

```jsonc
// 本实体字段（一层）
"levelPath": [
  ["<appName>", "<entityFullName>", "<entityCaption>",
   "<entityFullName>.<field>", "<fieldCaption>"]
]

// 关联实体展开的字段（两层）
"levelPath": [
  ["<appName>", "<entityFullName>", "<entityCaption>",
   "<entityFullName>.<relField>", "<relFieldCaption>"],          // 第一层：本实体的关联字段
  ["<relApp>", "<relEntityFullName>", "<relEntityCaption>",
   "<relEntityFullName>.<subField>", "<subFieldCaption>"]        // 第二层：关联实体的子字段
]
```

**关键**：
- `attributeFullName` 取的是**第二层**（关联实体的属性全名），
  例如 `com.seeyon.organization.domain.core.entity.OrgMember.code`
- `displayName` 用「本字段名/子字段名」形式：`创建人/编号`、`销售员/编号`
  （真实样本就是这样，不是随便起的）
- `entityType` 仍是 `MASTER_ENTITY`（不是 SUB_ENTITY —— 那是子表的标记）
- `relation` = `NONE`，`relationApp` = 关联实体所属应用（`organization`），
  `relationEntity` = 空字符串

**真实样本对照**（从 `ctp_excel_export_template` 实读）：

```
本实体字段（dept 关联到组织）
levelPath[0] = [znxmglpt…, …entity.Bumenxinxipeizhi, 部门信息配置,
                …Bumenxinxipeizhi.benbu, 本部]
levelPath[1] = [organization, com.seeyon.organization.domain.core.entity.OrgUnit,
                组织, com.seeyon.organization.domain.core.entity.OrgUnit.name, 名称]
attributeFullName = com.seeyon.organization.domain.core.entity.OrgUnit.name
displayName       = 本部

本实体字段（销售员关联到人员）
levelPath[0] = […entity.Yxdsprypzb, 预下单审批人员配置表,
                …Yxdsprypzb.xiaoshouyuan, 销售员]
levelPath[1] = [organization, …entity.OrgMember, 人员, …OrgMember.code, 编号]
attributeFullName = com.seeyon.organization.domain.core.entity.OrgMember.code
displayName       = 销售员/编号
```

### 本应用实测（LIVE PASS）

实体 `郑杰验证实体` 有 5 个 ENTITY 类型字段：

```
creator              创建人    → OrgMember
creatorInstitution   创建机构  → OrgUnit
creatorDepartment    创建部门  → OrgUnit
creatorPost          创建岗位  → OrgPost
updater              更新人    → OrgMember
```

每个展开 4 个子字段（编号/姓名/手机号码/邮箱），共 20 个展开列，
加上 11 个基本字段 + 5 个关联字段本身 = **36 列**。

```
验收导入模板-实体字段  id=-6820629284288926507  36 列（20 两层展开）
验收导出模板-实体字段  id=3393458473218147025   36 列（20 两层展开）
复查：search 能查到，displayName 形如「创建人/姓名」，levelPath 两层 ✅
```

### 脚本

```bash
python tools/core/setting/excel_template_entity_fields.py --dump
python tools/core/setting/excel_template_entity_fields.py --i-have-write-authorization
```

## 十、未验证

| 项 | 状态 | 说明 |
|---|---|---|
| `get-entity-metadata` 接口的参数形态 | **UNVERIFIED** | 属性改走 DB 读取，未调通这个接口 |
| 关联实体/枚举字段的 `relationEntity`/`enumClass` 填法 | **UNVERIFIED** | 只建了基本类型字段的模板 |
| 子表（SUB_ENTITY）多 sheet 模板 | **UNVERIFIED** | `metadataContent` 二维的外层意义未实测 |
| `importReminders` 用法 | **UNVERIFIED** | DTO 有，未测 |
| `signatureCode` 的算法 | **UNVERIFIED** | 传空串平台接受 |
| 模板导出成 Excel 文件 | **UNVERIFIED** | `export-excel-template` 接口未测 |
| 模板的更新（update-template） | **UNVERIFIED** | 未测 |
