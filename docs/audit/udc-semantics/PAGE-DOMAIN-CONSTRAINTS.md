# UDC 页面/布局域 约束（后端权威，反编译 udc-biz 5.3.517）

**证据源**：`udc-biz-5.3.517.jar` + `udc-plugin-api-5.3.517.jar` 反编译
- `com.seeyon.udc.page.dto.PageDefinitionDto` / `PageLayoutDefinitionDto` / `PageInfoGroupDto` / `PageDesignerDto`
- `com.seeyon.udc.page.enums.PageTypeEnum` / `OpenTypeEnum` / `FunctionTypeEnum` / `PortletTypeEnum`

## 1. 页面创建（PageDefinitionDto）必填

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `appId` | Long | ★ | 应用ID |
| `relationGroupId` | Long | ★ | 关联分组 |
| `pageType` | String | ★ | 页面类型（PAGE_TYPES） |
| `groupId` | Long | | 分组ID |
| `masterEntityIds` | String | | 页面对应的主实体Id |
| `relationAppName` | String | | 页面对应主实体的 appName |
| `handWritten` | Boolean | | 手写页面（自定义页面） |
| `defaultOpenType` | String | | 默认打开方式 |
| `curTerminalType` | TerminalTypeEnum | | 当前端类型 |
| `category` | PortletCategoryEnum | | 栏目模板分类 |
| `pageItems` | List\<PageItemDefinitionDto\> | | 页面信息 |

## 2. 页面布局创建（PageLayoutDefinitionDto）必填
`appId`（★）；其余：`relationGroupId` / `designState` / `sourceAppName` / `sourceType` /
`pageLayoutItems` / `curTerminalType`。

## 3. 页面类型（PageTypeEnum，14 值；13 缺）
PORTAL 1 / WELCOME 2 / REPORT_FORM 3 / **DETAIL 4** / **LIST 5** / APPROVAL 6 / PORTLET 7 /
SEARCH_LIST 8 / EDIT_LIST 9 / LIST_DETAIL 10 / ASSIST_INFO 11 / OTHER 12 / LAYOUT 14 / SUBPAGE 15

## 4. 其它枚举
- **OpenTypeEnum**：WORK_SPACE 1 / DIALOG 2（默认打开方式）
- **FunctionTypeEnum**：FRONTEND 0 / BACKEND 1
- **PortletTypeEnum**：GROUP 0 / PORTLET 1

## 5. 机器可读模型
`components/udc/page_constraints.py`：`PAGE_DEFINITION_FIELDS` / `PAGE_DEFINITION_REQUIRED` /
`PAGE_LAYOUT_FIELDS` / `PAGE_LAYOUT_REQUIRED` / `PAGE_TYPES` / `OPEN_TYPES` / `FUNCTION_TYPES` /
`PORTLET_TYPES` + `validate_page_definition` / `validate_page_layout`。

## 6. 页面 REST 端点（udc-web，`udc/page-info` / `udc/page-layout`）
- `POST /service/udc/page-info/base-info/create`（PageDefinitionDto）→ 创建页面
- `POST /service/udc/page-info/update`（PageInfoDto，含 `pageSchema`/`draftPageSchema`）
- `GET  /service/udc/page-info/{id}` / `/detail/{id}`
- `POST /service/udc/page-info/select-list/by-conditions`（`@MultiRequestBody Map params, Sort`）
- 布局同理：`udc/page-layout/base-info/create` / `/update` / `/{id}`
