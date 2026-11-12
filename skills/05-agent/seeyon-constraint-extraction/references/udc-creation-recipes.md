# UDC 创建端点 + 最小可用 body（LIVE 验证过）

每域：端点 → 最小 body → 返回 → 回读。均为 test2（app=8704025620829192834）实测成功。

## 实体
- 创建：`POST /service/udc/entity`（**无子路径**；`/create` 是 405）。body=`EntityDto`：`{appId,name,caption,stereotype,features,description}`（name≤21，caption≤50）。
  成功返回 `data.content` = 新实体 id（字符串化 Long，可能为负）。
- 回读：`GET /service/udc/entity/{id}`；`data` 可能是 EntityDto，也可能是 `{content:{...}}`——两种都处理。

## 页面（PageInfoController，base `udc/page-info`）
- 创建：`POST /service/udc/page-info/base-info/create`。最小成功 body：
  ```json
  {"appId":<long>,"relationGroupId":<long>,"pageType":"DETAIL","groupId":0,
   "pageUrl":"xzhPage1","curTerminalType":"ALL",
   "pageItems":[{"pageUrl":"xzhPage1","urlType":"PC","menuName":"菜单名"}]}
  ```
  成功返回 `data.content` = PageInfoGroupDto（含新 `id` 与 `relationGroupId`）。`relationGroupId` 可从任一现有页面的 `POST /service/udc/page-info/select-list/by-conditions` body `{"params":{"appId":...}}` 取样本。
- biz 层校验链（`PageInfoService.checkDefinitionPageDto`，DTO 注解不全，全靠它）：
  1. `pageItems` 非空 → 否则『页面终端信息为空，请选择』
  2. `pageUrl`（BOOT_1001 pageUrl must not be null）
  3. `pageItems[].urlType`（`@NotNull(groups=Create)`；空报 `curTerminalType 字段不能为空！`）
  4. `pageItems[].menuName 或 menuId`（否则『页面必需绑定归属资源』）——**仅当** 应用 sourceType≠FORM 且 pageType 不属于 `PageTypeEnum.unRelationFunction()`
  5. `curTerminalType`（否则『curTerminalType 字段不能为空！』）——**仅当**有个 pageItem 的 `menuName` 非空，走进 `setFunctionRefer`
  - 顺序：pageItems非空 → checkPageUrl(唯一性) → validationPageUrl → validationPageType → validationOnCreate → 归属资源 → validationGroup → validationSubpage4Layout

## 菜单/功能节点（FunctionNodeController，base `udc/function`）
- 更新/创建：`POST /service/udc/function/update` 等；必填 `appId,terminalType,type,name(1..64)`（FunctionNodeDto）
- 交互表 `udc_function_node`（FunctionNodeEntity @Table）；`name` NOT NULL

## 微流程
- 创建：`POST /service/udc/microflow/create`（dataSchema 为 json 字符串）；本地从零验收见 `tests/udc/test_author_from_constraints.py`（不下发）。
- 回读：`GET /service/udc/microflow/findById/{id}`

## 通用坑
- 分页/列表：`@MultiRequestBody Map params, @MultiRequestBody Sort sort` → body 必须 `{"params":{...}}`。
- 返回包壳：`data` 有时直接是对象，有时 `{content:...}`，也有 `PageResponse`/`ListResponse`——取前统一兼容。
- 凭据：`<COLLAB_ROOT>/agent-collaboration/shared-credentials/test2-web-credential.json`（cookie + base），值不外泄。
