# 设置域里两个 REST 子域：导入导出模板 / 二维码

UDC 设置域绝大多数 tab 走 GraphQL，但这两个是 **REST**，且都不在 udc 构件里。
放在这里是因为它们是同类问题的模板：**当一个子域找不到 GraphQL operation 时，
先怀疑它是 REST + 独立 starter 构件**，而不是猜更多 operation 名。

## 一、归属构件（都不在 udc-web / udc-biz）

| 功能 | 构件 | Controller | 路径前缀 |
|---|---|---|---|
| 导入导出模板 | `boot-starter-excel` | `ExcelController` | `/service/udc/excel/*` |
| 二维码规则 | `boot-starter-qrcode` | `CtpQrCodeRuleController` | `/service/udc/qrcode-rule/*` |

定位手法（不要在 udc 构件里翻）：

```bash
for j in $(find /d/repo/CHIT -name '*.jar'); do
  unzip -l "$j" 2>/dev/null | grep -qi 'ExcelExportTemplate' && echo "$j"
done
```

把 `ExcelExportTemplate` 换成业务词（`SerialScheme` / `QrCodeRule` / `ParameterDefiniton`）
就是通用定位器。命中的 artifact 名 = 归属构件。

⚠ 路径前缀是 `/service/udc/excel/*`，不是 `/service/excel/*`。
后者报 `server_404 excel 服务不存在，请重启服务或重新发布应用后再试` ——
这条报错说明「服务名对、网关前缀错」，不是「接口不存在」。

## 二、导入导出模板

### 端点

```
POST /service/udc/excel/search                        列表（只查 isCustom=false）
POST /service/udc/excel/search-custom-list-by-conditions  列表（只查 isCustom=true）
POST /service/udc/excel/create-template               新建
POST /service/udc/excel/update-template               更新
POST /service/udc/excel/select-by-id                  详情
POST /service/udc/excel/delete                        删除（body {"id": ...}）
POST /service/udc/excel/get-entity-metadata           实体元数据
POST /service/udc/excel/export-excel-template         导出成 Excel 文件
```

### ExcelExportTemplateDto

```java
Long    id
String  name                 // @NotNull @Size(max=20)
String  appId
Long    appGuid = -1L
String  appName
String  mainFullName         // ★ 实体全类名
Long    createUserId = -1L
String  signatureCode = ""
String  metadataContent = ""  // ★ 列定义（JSON 字符串）
String  excelHeadInfo = ""    // ★ 表头信息（JSON 字符串）
Boolean isCustom = true       // ★ 决定进哪个列表
Boolean isImport = true       // true=导入模板 false=导出模板
Boolean isDefault = false
Boolean deleteFlag = false
List<List<ExcelColumnDto>> columnList;   // @Min(1) —— 但响应里恒为 null
Long    belongGroupId = -1L
Long    originalId
List<String> importReminders
String  authInfo
```

### ExcelColumnDto（40+ 字段，关键项）

```java
String  attributeFullName     // ★ 唯一锚点：<实体全类名>.<字段名>
String  displayName           // ★ Excel 表头（可自定义）
String  entityType            // MASTER_ENTITY / SUB_ENTITY
List<List<String>> levelPath  // [appName, entityFullName, entityCaption, attrFullName, attrCaption]
String  type                  // java.lang.String
String  dataType              // STRING / INTEGER / BIGINTEGER / DECIMAL / DATE / DATETIME / BOOLEAN / ENTITY / CTPENUM
Integer curColIndex
Boolean unique / matchQuery / notBlankOrNotNull / multiSelect / isHidden
String  relation              // NONE / …
String  relationApp / relationEntity
String  columnType            // varchar(50) 等物理类型，可 null
SafetyDto safetyDto           // {encryption:"NOT_ENCRYPTION", mask:"None", auditLog:false, permission:false}
```

### 四个坑

1. **`isCustom` 决定进哪个列表**。`selectPageByCondition` 里硬写
   `columnMap.put("isCustom", false)`，`selectCustomListByConditions` 里硬写 `true`。
   建模板传 `isCustom=true` 后在 `search` 里永远 0 条。
2. **`columnList` 读回来恒为 null**。列定义在 `metadataContent` / `excelHeadInfo`
   两个 JSON 字符串里（二维：外层 sheet、内层列）。提交时两个写同一份。
3. **分页 body 是 `{pageInfo:{pageNumber,pageSize}, params:{...}}`**，
   写成 `{page:1,size:10}` 报 `BOOT_3000 message:null`。
4. **`delete` 必须 `{"id": ...}`**，裸 Long 报 `BOOT_4002 数据不存在或无权限查看`。

### 实测形状

实体 16 个属性 → 导入/导出各一个模板，16 列：

```
name = 验收导入模板 / 验收导出模板
mainFullName = com.seeyon.<app>.domain.entity.<Entity>
metadataContent = excelHeadInfo = json.dumps([[col, ...]])
isImport = 1 / 0     isCustom = 0
DB: metadata_content = excel_head_info = 20718 字节
```

## 三、二维码规则

### 端点

```
POST /service/udc/qrcode-rule/create            新建（@RequestBody CtpQrCodeRuleDesignDto）
POST /service/udc/qrcode-rule/update
POST /service/udc/qrcode-rule/delete            body {"id": ...}
POST /service/udc/qrcode-rule/batch-delete      body {"ids": [...]}
POST /service/udc/qrcode-rule/physical-delete
POST /service/udc/qrcode-rule/deactivate / start-using
POST /service/udc/qrcode-rule/search            3 个 @MultiRequestBody
POST /service/udc/qrcode-rule/search-no-page    2 个 @MultiRequestBody
GET  /service/udc/qrcode-rule/{id}
GET  /service/udc/qrcode-rule/detail/{guid}
POST /service/udc/qrcode-rule/search-for-design-drop-down-list
```

### CtpQrCodeRuleDesignDto

```java
Long    id
String  name                 // @NotBlank @Size(max=50)
CtpQrCodeTypeEnum type
CtpQrCodeLinkTypeEnum linkType
Long    appGuid / appId
String  entityFullName
String  valueFieldCode       // ★ 取哪个字段的值
String  pcPagePath / mobilePagePath
```

### 枚举（传字符串，DB 存 ordinal）

```java
CtpQrCodeTypeEnum     BARCODE(0) / LINKQRCODE(1) / FIELDQRCODE(2) / QRCODE(3)
CtpQrCodeLinkTypeEnum APP(0) / CUSTOM(1)
```

| type | 还需要什么 |
|---|---|
| `BARCODE` | `valueFieldCode` |
| `FIELDQRCODE` | `valueFieldCode` |
| `LINKQRCODE` | `pcPagePath` 或 `mobilePagePath` |
| `QRCODE` | — |

### search 的参数坑

```
{"pageInfo":{...},"paramsDto":{...},"sort":{}}    → BOOT_3000 message:null  ❌
{"pageInfo":{...},"paramsDto":{...},"sort":null}  → BOOT_0000               ✅
search-no-page 只传 {"paramsDto":{...}}，不要 sort key
```

`CtpQrCodeRuleParamsDto`：`{name, active, appGuid, appId, entityFullName, deleteFlag, originalId}`。

### 落库表 `ctp_qr_code_rule`

```
id / is_active / app_guid / app_id / code / is_delete
entity_full_name / field_code / value_field_code / name
pc_page_path / mobile_page_path / release_state / type / link_type / logo_file_id
```

`type` / `link_type` 存 ordinal；`field_code` 与 `value_field_code` 是两个不同槽位（只传后者时前者为 null）。

## 四、这两个子域的共同教训

```
找不到 GraphQL operation      → 先试 REST 前缀（/service/udc/<svc>/），别加倍猜 op 名
REST 也 404                   → 报错文案里的服务名对不对？前缀对不对？
归属不明                      → 按业务词扫全仓 jar，命中的 artifact 就是归属
BOOT_3000 + message:null      → 某个入参反序列化失败（空对象/类型不符），不是参数名错
DB 有但接口 0 条               → 反编译看 Service 里的隐式 columnMap 过滤
写入成功但查不到               → 写入时带的 flag 与查询时的隐式过滤不一致
```
