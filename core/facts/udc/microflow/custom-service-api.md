# 自定义服务节点 —— 接口链路与 GraphQL 契约（用户贴 body，2026-10-25）

自定义服务节点是「选应用 → 选服务 → 选方法 → 加载方法出入参」的链路，全程走 GraphQL。
接口名 = `udcMicroflow + 动词 + 对象 + Post`，POST `/service/udc/graphql`，query string 带 operation 名（可多 operation `&` 合并批量）。

## 链路（按顺序，用户口述：选引用→加载接口列表→选接口→加载参数→填参数→校验参数）

1. 选应用 → `udcMicroflowSearchAppsPost`（应用列表）
2. 选服务 → `udcMicroflowSearchAppServiceByAppNamePost`（按 appName 搜服务，返回 methods 列表）
3. 选方法 → `udcMicroflowSearchMethodByNamePost`（加载方法的 parameter 入参 + returnValue 出参，含 md5）
4. 加载入参字段 → 若 `parameter.item.itemType` 是 DTO，再调 `udcMicroflowFindCustomDtoPost`（`dtoFullName`=该 DTO）拿 `attributes`（字段列表），这就是「参数映射」里的字段（如 部门名称/部门ID/标签ID/引用次数）
5. 填参数 → 每个字段配值（引用/常量/表达式）
6. 校验参数 → 校验接口（body 待抓，用户观察「填参数时有时走校验」）

**核心机制：参数定义是后端返回的，不是前端写死的。**
dubbo 方法的 `parameter`/`returnValue` 结构由后端反射/反编译返回（含 DTO fullName + md5），
DTO 的字段列表再通过 `FindCustomDtoPost` 拿 `attributes` 渲染成「参数映射」的表单。
这跟「节点确定后元数据重载」是同一套：选什么 → 后端返回什么定义 → 前端渲染。

## 1. udcMicroflowSearchAppsPost（选应用）

variables:
```json
{"appId":"9000000000000000001","needBootStarter":true,"needConnectorApp":true,"needDependency":true}
```
返回 content 字段：`appId, name, caption, description, fullName, inApp, id, udcApp, appType, dynamicDependency`

## 2. udcMicroflowSearchAppServiceByAppNamePost（选服务）

variables:
```json
{"appId":"9000000000000000001","appName":"datamigration9000000000000000001","needDynamicConnector":false}
```
返回 content：`caption, fullName, description` + `methods[]{caption, description, dubbo, fullName, group, implClass, interfaceClass, appType}`
- appName 可为依赖应用名（如 `app-common`、`bpm`）。
- 返回的 methods 就是「选择服务」下拉的选项。

## 3. udcMicroflowSearchMethodByNamePost（选方法 → 加载出入参）

variables:
```json
{"appId":"9000000000000000001","appName":"app-common",
 "dtoFullName":"com.seeyon.app.common.label.appservice.api.LabelCommonAppServiceImpl.updateReferenceCount",
 "methodFullName":"com.seeyon.app.common.label.appservice.api.LabelCommonAppServiceImpl.updateReferenceCount"}
```
返回 content：
```json
{
  "caption":"部门引用标签","customs":null,"description":"更改标签引用次数",
  "dubbo":true,"dubboVersion":"1.0",
  "fullName":"com.seeyon.app.common.label.appservice.api.LabelCommonAppServiceImpl.updateReferenceCount",
  "group":null,
  "implClass":"com.seeyon.app.common.label.appservice.api.LabelCommonAppServiceImpl",
  "interfaceClass":"com.seeyon.app.common.label.api.LabelAppService",
  "md5":"8ba3572ff736e2e710b631b8b1a8cd9e",
  "parameter":{"caption":null,"type":"com.seeyon.boot.transport.SingleRequest",
    "item":{"enums":null,"itemType":"com.seeyon.app.common.label.dto.LabelDepartmentDto","item":null}},
  "returnValue":{"caption":"","type":"com.seeyon.boot.transport.SingleResponse",
    "item":{"enums":null,"itemType":"java.lang.Boolean","item":null}}
}
```

**关键结构**：
- `parameter`/`returnValue` 是 `{caption, type, item{enums, itemType, item{javaType,dataType,keyType}}}` 递归结构。
- `type` = 包装类型（`com.seeyon.boot.transport.SingleRequest/SingleResponse`）。
- `item.itemType` = 真实 DTO / 基本类型（`LabelDepartmentDto`、`java.lang.Boolean`）。
- `md5` = 方法的签名指纹（用于引用校验，同实体 attributes 的 md5 机制）。
- `fullName`/`implClass`/`interfaceClass` 是 dubbo 服务三元组。

## 4. udcMicroflowFindCustomDtoPost（选自定义对象）

variables:
```json
{"appId":"9000000000000000001","appName":"bpm","dtoFullName":"com.seeyon.bpm.dto.BpmCaseActivitySearchDto","needChildren":true}
```
返回 content：`attributes, caption, fullName, type, relationEntityId, methodLegals, dtoType, udcApp, refApp, entity`

## 赋值方式三态

- 字段映射：按 `parameter` 的入参字段逐个配值（文本/长整数/整数/…）。
- 对象引用：选一个来源对象参数，整体引用。
- 自动映射：选来源参数 + 参数映射（自动按同名匹配）。

## 待确认

- 用户观察「填写参数时有时走校验」——可能存在参数校验接口，未抓到 body，需运行时同步抓确认。
