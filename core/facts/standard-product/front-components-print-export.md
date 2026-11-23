# 甘特图 · 标签打印 · 依赖导出 · CIP OpenAPI 公共层

## Capability

```
boot-starter-ganttchart    甘特图（WBS 项目、Schema 配置、动态取数）
boot-starter-labelprint    标签打印（分类 + 模板 + 对外模板 URL）
boot-starter-mgn-export    依赖导出/版本一致性校验（跨用户域导出）
cip-openapi-common         CIP 开放接口的签名与报文基类（外部系统对接必看）
```

## Version

`ganttchart` / `labelprint` / `mgn-export` 5.3.600 系；`cip-openapi-common` 5.3.260。

## ★ 一、甘特图（ganttchart）

```java
GanttChartAppService
  SingleResponse<Long>    copyWbs(SingleRequest<GanttChartCopyDto>);
  SingleResponse<Integer> deleteByWbsId(SingleRequest<GanttChartCopyDto>);
  SingleResponse<Long>    saveProject(SingleRequest<WbsSaveDto>);
  ListResponse<Object>    dynamicSelectByEntity(ListRequest);

GanttChartSchemaAppService            // 甘特图配置（列/层级/取数）
  create / update / selectListByConditions / selectPageByConditions

GanttChartRunningController / GanttChartSchemaController
GanttChartSchema 实体 + GanttChartSchemaDao + GanttChartDetectionMessage（一致性检测消息）
```

⇒ 客开做「项目计划/排期」不用自己造树：`saveProject(WbsSaveDto)` 存整个 WBS，
`dynamicSelectByEntity(ListRequest)` 直接按实体取数渲染。

## ★ 二、标签打印（labelprint）

```java
LabelPrintAppService
  // 分类
  createCategory / updateCategory / deleteCategoryById / selectCategoryById / selectCategoryListByConditions
  // 模板
  createTemplate / updateTemplate / updateTemplateStatus / deleteTemplateById / deleteTemplateByIds
  selectTemplateById / selectTemplatePageByConditions / selectTemplateListByConditions
  templateUrlForApi(SingleRequest<LabelPrintTemplateUrlDto>)     // ★ 给外部系统取模板 URL
```

实体：`LabelPrintCategory` / `LabelPrintTemplate` / `LabelPrintRecord`（各自的 Dao 都在）。
常量：`LabelPrintConstant.EXCLUDE_PROPERTIES / ENTITY_PREFIX / FIELD_SORT_NUMBER / NAME_KEY / FORM`。

⇒ 打印记录落 `LabelPrintRecord`；模板启用状态走 `updateTemplateStatus`。

## ★ 三、依赖导出（mgn-export）

```java
DependentExportAppService.getDependentVersionByName(SingleRequest<ValidateRequestDto>)
  → SingleResponse<DependentValidateDto>

DependentExportController
  getDependentDynamicVersion(String, String, CtpSystemEnvEnum)
  getDependentVersionByName(String, List<String>, CtpSystemEnvEnum)
```

用途：导出/迁移时**校验目标环境里依赖模块的版本是否齐**，`CtpSystemEnvEnum` 指定目标环境。

## ★ 四、CIP OpenAPI 公共层（外部系统对接必看）

```java
ApiConstants
  SIGN_METHOD_MD5 / CHARSET_UTF8
  X_API_APP_KEY / X_API_SIGN_TYPE / X_API_SIGN       // ★ 三个请求头

SignTypeEnum: MD5 / SHA256HEX

ApiBaseResponse { int status; String code; String message; }    // 所有开放接口的响应壳
ApiListRequest / ApiListResponse / ApiPageRequest / ApiPageResponse
ApiRequestContext { Map<String,String> getHeaders(); ... }      // 请求上下文
```

⇒ 对接方签名流程：`X-Api-App-Key` + `X-Api-Sign-Type` + `X-Api-Sign`（按 `SignTypeEnum` 算），
报文用 `ApiBaseResponse` 的 `status/code/message` 判结果，**HTTP 200 不代表业务成功**。

## Side Effects

- `copyWbs` / `deleteByWbsId` 是按整个 WBS 操作，误删范围大。
- `updateTemplateStatus` 停用模板会让已排队的打印任务拿不到模板。
- 开放接口签名错误通常返回 `status != 0` 而非 4xx，客户端要把两处都判。

## Known Constraints

1. 甘特图与「微流程的甘特图节点」是两层：本格是**数据与配置层**，前端渲染在组件包里。
2. `templateUrlForApi` 返回的是**外部可访问 URL**，与内部 `selectTemplateById` 不是一回事。
3. `mgn-export` 只做版本校验，不做真实导出内容。
4. `cip-openapi-common` 只有常量/报文/上下文，**没有业务接口**（业务在 `cip-manager-facade`）。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `GanttChartAppService` 4 方法 / `GanttChartSchemaAppService` 4 方法 | `javap -p` | VERIFIED_STATIC_BYTECODE |
| `LabelPrintAppService` 14 方法（分类 5 + 模板 9） | 同上 | VERIFIED_STATIC_BYTECODE |
| `DependentExportAppService` / `DependentExportController` 方法 | 同上 | VERIFIED_STATIC_BYTECODE |
| `ApiConstants` 5 常量 / `SignTypeEnum` 2 值 / `ApiBaseResponse` 3 字段 | `javap -p` 5.3.260 | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与签名可复核
- ⚠️ 四块均未真机调用

## 给 Agent 的判据

```
做项目计划/排期     → GanttChartAppService.saveProject(WbsSaveDto)
要打印标签模板URL   → LabelPrintAppService.templateUrlForApi
导出前查依赖版本     → DependentExportAppService.getDependentVersionByName
对接 CIP 开放接口    → 三个头 X-Api-App-Key/Sign-Type/Sign + ApiBaseResponse.status
```
