# boot-starter-formconvert：表单转文档（导出 Word/图片）

## Capability

**把「一张单据的数据」按模板渲染成一个文件**（`doc`/`docx`/图片），返回 `FileDto`。
典型用途：客开里做单据打印、合同/凭证导出、批量生成附件。

## Version

`boot-starter-formconvert` 5.3.600（jar 在盘，javap 全量抽取）。

## Input

模板（`FormConvertTemplateDto`，落库由 `FormConvertTemplateAppService` 管）。

## Required

模板要有 `entityFullName` 与 `storageKey`（模板文件本体）。

## ★ 一、单张导出（最常用）

```java
@Autowired(required = false) private FormConvertAppService formConvert;

FormConvertDto req = new FormConvertDto();
req.setTemplateId(templateId);
req.setEntityFullName("com.seeyon.datamigration9000000000000000004.dto.AeProbeEntityDto");
req.setEntityId(recordId);
req.setEntity(entityDto);                    // 也可以直接给对象，不用 entityId
req.setMasterTableFields(masterFields);      // 主表字段清单
req.setSubTableMap(subMap);                  // 子表：表名 → 行 → 字段

SingleResponse<FileDto> r = formConvert.formConvert(SingleRequest.from(req));
FileDto file = r.getData().getContent();     // storageKey 等
```

```java
// 签名原文
SingleResponse<FileDto>  formConvert(SingleRequest<FormConvertDto>);        // 出文件
SingleResponse<String>   formConvertMicro(SingleRequest<FormConvertDto>);   // 出字符串（微流程/内嵌用）
SingleResponse<FormConvertBatchDto> formConvertBatch(SingleRequest<FormConvertBatchDto>);  // 批量
String                   getDynamicTitle(String, List<FormConvertFieldDto>, String);
ListResponse<FormConvertTemplateDto> selectApplyTemplateByEntityId(SingleRequest<FormConvertTemplateSearchDto>);
```

`FormConvertDto` 11 字段（字节码原文）：

```java
Long templateId; List<Long> templateIds;      // 单个 / 批量
List<String> storageKeys;                     // 模板文件
String fileName;
String entityFullName; Long entityId; Object entity;
List<FormConvertFieldDto> masterTableFields; String masterTableFieldsStr;   // ★ 有 Str 变体
Map<String,List<List<FormConvertFieldDto>>> subTableMap; String subTableMapStr;
```

## ★ 二、模板管理

```java
FormConvertTemplateAppService
  SingleResponse<Long>    create(SingleRequest<FormConvertTemplateDto>);
  SingleResponse<Integer> update(SingleRequest<FormConvertTemplateDto>);
  SingleResponse<Integer> deleteByIds(SingleRequest<List<Long>>);
  SingleResponse<FormConvertTemplateDto> selectById(SingleRequest<Long>);
  ListResponse<FormConvertTemplateDto>   selectListByConditions(ListRequest);
  PageResponse<FormConvertTemplateDto>   selectPageByConditions(PageRequest);
  ListResponse<FormConvertTemplateDto>   selectApplyTemplate(SingleRequest<FormConvertTemplateSearchDto>);
  SingleResponse<Integer> createBatchForAppApproval(List<FormConvertTemplateDto>);   // ★ 不包 Request
```

`FormConvertTemplateDto` 14 字段：

```java
String name; String code; String appId; String appGuid; String entityFullName;
String storageKey;                       // ★ 模板文档本体
Long createUserId; Long createOrgId;
String rule; String dynamicTitle;        // ★ 渲染规则 / 动态标题
Boolean enable; Boolean preset; Boolean convertImage; String imageConfig;
```

## 三、内部可用的工具方法（转 DTO 时省事）

```java
void dealEntityData(List<FormConvertFieldDto>, Map<String,List<List<FormConvertFieldDto>>>,
                    Object entity, Map<String,Map<String,JavaEnumItemDto>> enumMap, AggEntityMetadataDto);
Map<String,Map<String,JavaEnumItemDto>> getEnumMap(String, AggEntityMetadataDto);
```

常量：`FormConvertConstant.SUFFIX_DOC / SUFFIX_DOCX / CACHE_FORM_CONVERT_TEMPLATE /
REFERENCE_PROPS_TEMPLATE / CTPENUM_PROPS_TEMPLATE`。

## Side Effects

- 生成的文件进文件服务（返回 `FileDto`），**不占你的磁盘**；要落地自己下回来存。
- 批量导出会按模板逐份渲染，N 份就是 N 次渲染 + N 个文件，注意配额。
- `convertImage=true` 时走图片渲染（`imageConfig`），比文档慢。

## Known Constraints

1. 模板必须是**该实体的**转换模板（`entityFullName` 对齐），跨实体模板 `selectApplyTemplateByEntityId` 查不到。
2. `masterTableFields` 与 `masterTableFieldsStr` 二选一；字段名要跟模板占位符一致，否则渲染成空。
3. 子表靠 `subTableMap`（表名 → 多行 → 字段），空子表给空 List，**不要给 null**。
4. `formConvertMicro` 返回字符串，适合微流程节点内联，但内容形态（HTML/文本）由模板决定。
5. 本格全部来自字节码，**未真机渲染过**（无客户模板样本）。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `FormConvertAppService` 7 方法 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| `FormConvertTemplateAppService` 8 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `FormConvertDto` 11 字段 / `FormConvertTemplateDto` 14 字段 | 同上 | VERIFIED_STATIC_BYTECODE |
| `FormConvertConstant` 常量 | 同上 | VERIFIED_STATIC_BYTECODE |
| 三个事件 + 1 个监听器（模板增删改） | 类清单 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 签名与字段逐字可复核
- ⚠️ 未跑过真实渲染（缺模板与实体样本）

## 给 Agent 的判据

```
要导出单据成 Word     → FormConvertAppService.formConvert(templateId+entity+字段)
微流程里要内联内容     → formConvertMicro（返回 String）
要批量导出            → formConvertBatch / templateIds
找不到可用模板        → selectApplyTemplateByEntityId(SingleRequest<SearchDto>)
模板占位符渲染成空    → 字段名对齐 masterTableFields/subTableMap，子表别给 null
```
