# 设置面板 13 个 tab 的前端页面与调用链路取证

> 状态：LIVE 取证完成（2026-10-12，test2）
> 方法：用户指令「你找对应的前端页面，然后找到调用链路，不知道的就是服务器上看对应的 pod 看前后端代码」
> 结论分级：LIVE=活体调用验证 / STATIC=前端 bundle 或 javap 静态证据 / UNVERIFIED=未验 / BLOCKED=取证受阻

---

## 0. 版本边界（先钉死）

| 面 | 版本 | 证据 |
|---|---|---|
| 后端镜像 | `chit-acr-registry.客户方.com/chjh-external/udc:5.3.517` | SSH+`kubectl get pod` jsonpath（pod `udc-7cbfc587f5-zzvmv`，namespace `lowcode-test`） |
| 后端 javap artifact | 5.3.517 | `docs/audit/artifacts/udc-web-5.3.517-javap/`（与镜像同号 → 本地反编译产物即 test2 部署代码） |
| 前端壳 | `seeyonGlobalVersion=5.3.41`、`seeyonSyfVersion=5.3.11`、`seeyonVendorVersion=1.0.12` | 设置页 HTML 内联 script（`/main/child-frame/udc/app-design/basic-setting`） |
| 设计器远端入口 | `/udc/remoteEntry.js` 47,554 字节，166 个 chunk | 同上，`GET /udc/remoteEntry.js` |
| 静态存储 | OSS `xiaozhua-public-test2.oss-cn-beijing.aliyuncs.com`，key = `udc/<chunk>.<hash>.js` | 404 时返回的 `HostId`/`Key` |

**jar 内部 class 级确认：BLOCKED** —— `/app/udc-assemble.jar`（502,607,791 字节，`-rwxr-x--- appuser root`）在容器内 `unzip -p` 对该 fat jar 全部静默失败（MANIFEST/条目计数均 0 输出）。镜像 tag 已完成版本对齐，此步为冗余确认，未继续攻坚。

**pod 内无前端静态目录**：`udc` 容器只有 `/app/udc-assemble.jar`（纯后端），`portal` 容器同为 `portal-assemble.jar`。前端经网关 → OSS 分发，故取 chunk 走 HTTP 而非文件系统。

---

## 1. 调用链机制（核心结论）

### 1.1 四种调用形态

前端所有 tab 共用一套 GraphQL 客户端，op 名 + 入参类型 + 参数键三元组决定一次调用：

| 形态 | 构造 | 证据 chunk |
|---|---|---|
| **A. loader 描述符** | `getRequestByAppName("udc").queryLoader.load({fieldType, paramsType, paramsKey, params, queryFields})` | `vendors-node_modules_xiaozhua_biz-basic-data...c121b851.js`（抽到 25 个） |
| **A'. mutation loader** | `getRequestByAppName(x).udcMutationLoader.load({fieldType, paramsType, paramsKey, queryFields, params})` | `src_redux_store_ts.14dc061e*.js`（`udcScalabilityOptionSelectAllOptionNamePost`、`udcApplicationUpdatePost`）—— **除 queryLoader 外的第二个 loader** |
| **B. apolloQuery + 前缀拼接** | `apolloQuery("mutation ".concat(PREFIX, "OpName ($body: ".concat(PREFIX, "OpNameInputBody) { ... }"))` | 同上（`BasicDataDesignUpdatePost` 实证） |
| **C. 字面量 query** | `n("mutation udcPageInfoBatchCreatePost($params: udcPageInfoBatchCreatePostInputBody) { ... }")` | `src_constants_design_page-type_ts-src_services_app-design_template...6494d14a.js` |
| **D. REST 直连** | axios `.post("/excel/set-auth")`；另有 `/service/udc/entity/attribute` 等 REST 面 | 同上 |

例外形态（引时须照抄）：
- `paramsType:"Map"`（非 `InputBody`）—— `src_redux_store_ts` 内存在
- **无 `paramsKey` 的零入参 op**：`fieldType:"".concat(prefix,"BasicDataDataTypesGet")` 只带 `queryFields`

### 1.2 三条硬规则（STATIC，可复用）

1. **入参类型命名**：`<操作名>InputBody`（body）/ `<操作名>InputPath`（path）/ `<操作名>InputQuery`（query）。
2. **参数键 `paramsKey`** 决定 GraphQL 变量位置：
   - `body:` ← 形态 A/B/C 的 `...Post` 操作
   - `path:` ← `...Get` 路径参数（实证 `udcMetaDataSelectCtpEnumAppGet(path: $path)` → BOOT_0000，LIVE）
   - `query:` ← 查询串参数（实证 `udcDesignMetadataAggEntityExcludeBootGet` type=`InputQuery`）
3. **操作名前缀可变**（形态 B 的 `PREFIX`）：
   - 默认 `udc`：`n=>"mutation example ($body: ".concat(n||"udc","CtpParameterDefinitonPostInputBody)")`（parameter-definition chunk）
   - appName 驼峰：`e.appName.replace(/\b(-\w)/g, x=>x.substring(1).toUpperCase())` → `my-app` 变 `MyApp`（二维码 op 由此得名 `Ctp...`）
   - appId 驼峰 + 实体末段：`y(e.appId)+v(实体名末段)+"ExcelSearchListByConditionsPost"` / `+"ExportPost"` → **导入导出按实体动态生成 op 名**

### 1.3 端点与响应信封

- `POST /service/udc/graphql`，信封 `{code:"BOOT_0000", message:"SUCCESS", status:0, data:{content:...}}`
- GraphQL introspection 已关闭：`{"data":{"__schema":{...,"message":"GraphQL未生成接口:__schema"}}}` → 只能从 chunk 挖 query 原文，不能问 schema
- 跨微前端引用：`RemoteComponent {url, scope, module}`（角色权限实证，见 §3.12）

### 1.4 LIVE 验证记录

| # | 操作 | 参数 | 结果 |
|---|---|---|---|
| 1 | `udcPageTemplateSearchNoPagePost` | `body:{appId: 6419954374508955097}` | `BOOT_0000`，3 条 PORTLET 模板 |
| 2 | `udcPageTemplatePublishedSearchNoPagePost` | `body:{}` | `BOOT_0000`，33 条，**LAYOUT 6 条**（档案外框/审批外框_经典布局/审批外框_左右布局） |
| 3 | `udcMetaDataSelectCtpEnumAppGet` | `path:{appId}` | `BOOT_0000`，`rootEnumDtos[].fullName = com.seeyon.boot.starter...` |

---

## 2. 页面类型常量表（外框/子页面的定性证据）

来源：`src_constants_design_page-type_ts-src_services_app-design_template...6494d14a.js`（STATIC）

```
PORTAL / WELCOME / REPORT_FORM / DETAIL / LIST / APPROVAL / CHANGE_TERMINAL
PORTLET / SEARCH_LIST / EDIT_LIST / LIST_DETAIL / ASSIST_INFO / OTHER
SUBPAGE / LAYOUT / NORMAL / FORM / MOBILE
发布态：PUBLISHED / UNPUBLISH / ON_SHELF / RELEASE
中文对照（同 chunk）：列表页 详情页 全表编辑页 其它 栏目页 子页面 外框 移动端
```

**`LAYOUT` = 外框、`SUBPAGE` = 子页面**（中文串与常量同现于该 chunk）。

### 存储分布（DB `udc_test2` 实查，LIVE）

| 表 | 行数 | page_type 分布 |
|---|---|---|
| `udc_page_info` | 1494 | DETAIL 745, SEARCH_LIST 479, PORTLET 136, SUBPAGE 95, OTHER 28, EDIT_LIST 7, LIST 4 —— **无 LAYOUT** |
| `udc_page_layout` | 56 | （列含 guid/backup_code/owner_code，独立对象表） |
| `udc_page_template` | 3 | PORTLET 3（草稿/当前应用态） |
| `udc_page_template_published` | 49 | DETAIL 17, SEARCH_LIST 12, **LAYOUT 10**, OTHER 6, EDIT_LIST 4 |
| `udc_page_schema` | 1489 | — |

结论：**外框模板存在 `udc_page_template_published`（LAYOUT），不在 `udc_page_template`**；`udc_page_layout` 是布局实例侧的独立对象。查错表会得到 0 行（我第一次就是）。

---

## 2.5 tab 定义（代码级直接证据）

来源：`basic-setting` chunk 内 `D={collections:{...},...}` 对象（STATIC，逐条可复核）。**JS key 与中文标签存在交叉错位，勿凭 key 猜语义。**

| JS key | 中文 tab | uniformityKey | identityCAF | 组件模块 | 组件所在 chunk | 备注 |
|---|---|---|---|---|---|---|
| `collections` | **枚举** | `""` | `BASIC_SETTING_TABS_ENUMERATION` | `m`=16345 | basic-setting 本体 | key 叫 collections 但标签是"枚举" |
| `enumeration` | **选项集** | `enum` | `BASIC_SETTING_TABS_COLLECTIONS` | `p`=62727 | basic-setting 本体 | key 叫 enumeration 但标签是"选项集"；CAF 也是交叉的 |
| `objectDefinition` | 自定义对象 | **`dto`** | `BASIC_SETTING_TABS_OBJECT_DEFINITION` | `y`=3774 | basic-setting 本体 | 组件内 `fromType:"CUST"`；**`dto` 坐实=DTO** |
| `fieldSet` | 字段集 | `fieldSet` | `BASIC_SETTING_TABS_FIELD_SET` | `N`=27949 | `entity-fieldset` chunk | |
| `arguments` | 参数 | `arguments` | `BASIC_SETTING_TABS_ARGUMENTS` | `I`=70083 | `parameter-definition` chunk | |
| `rolePermission` | 角色权限 | `""` | `BASIC_SETTING_TABS_ROLE_PERMISSION` | `C`=17402 | basic-setting 本体 | 内联 `RemoteComponent{url:"/ctp-user/remoteEntry.js", scope:"ctp-user", module:"RolePermission"}` |
| `customExtension` | 扩展实体 | `customExtension` | `BASIC_SETTING_TABS_CUSTOM_EXTENSION` | `T`=46581 | **`extension-plan` chunk** | `createElement(T.default,{type:"custom"})` |
| `serialCode` | 流水号 | `serial` | `BASIC_SETTING_TABS_SERIAL_CODE` | `f`=30912 | basic-setting 本体 | 复用 `biz-serial-scheme` npm 子组件 |
| `excelSetting` | 导入导出模板 | `""` | `BASIC_SETTING_TABS_EXCEL_SETTING` | `E`=14284 | basic-setting 本体 | |
| `basicData` | 基础资料 | `""` | `BASIC_SETTING_TABS_BASIC_DATA` | `h`=92233 | basic-setting 本体 | 组件内含动态 `import()` |
| `qrcode` | 二维码 | `qrcode` | `BASIC_SETTING_TABS_QRCODE` | `g`=44104 | basic-setting 本体 | |
| `pageTemplateManage` | 页面模板 | `""` | （无） | **`v`=39637** | `template-manage` chunk | `components: e=>createElement(v.default,{category:"PAGE", sourceType, appId, appGuid})` |
| `layoutTemplateManage` | 外框模板 | `""` | （无） | **`v`=39637** | `template-manage` chunk | 同一组件，`category:"LAYOUT"` |

**两条硬结论（STATIC，替代此前的推断）**：
1. **页面模板与外框模板是同一个组件 `v.default`，靠 `category` prop 分流**（`"PAGE"` / `"LAYOUT"`），不是两套页面 —— 与 §2 pageType 常量、§3.11 published 表 LAYOUT 数据三方互证。
2. 两者的 `visible(e)` 返回 `"FORM" !== appDetails.sourceType` → **表单应用下这两个 tab 不显示**。
3. `uniformityKey` 是跨 tab 的统一性/权限键（`enum`/`dto`/`fieldSet`/`arguments`/`serial`/`qrcode`/`customExtension`），枚举/角色权限/导入导出/基础资料/页面模板/外框模板为空。

组件模块→chunk 归属的复核方法：在已下 chunk 中搜 `"<模块id>:function"` 定义点（本表 39637/70083/27949/46581 均如此定位）。

---

## 3. 13 个 tab 全表

> tab 标签取自 `basic-setting` chunk 内中文串（比截图多 2 项：角色权限、基础资料）。
> 状态：✅=调用链闭环（前端 chunk + op + 后端 Controller 三端对齐）；⚠️=部分；❌=未闭环

### 3.1 枚举 ✅
- 前端：`src_pages_app-design_entity-modeling_enum-manger_enum-field_index_tsx.9476b6a5.js`（UI：枚举项显示名称/枚举项名称/枚举值/新建组/移动至）
- op：`udcMetaDataSelectCtpEnumAppGet`（**key=path**, type=`InputPath`，LIVE PASS）、`udcMetaDataSelectCtpEnumItemPost`（key=body）、`EnumCategorySearchCategoryAndEnumPost`（key=body）
- 后端（javap 5.3.517）：`UdcEnumController`(8 api)、`UdcEnumItemController`(12)、`UdcEnumCategoryController` `udc/udc-enum-category`(8)、`UdcCtpEnumController` `udc/udc-enum-item`(5)
- 本会话写侧 LIVE：`POST /service/udc/udc-enum`、`/udc-enum-item`（见 A 层冒烟）

### 3.2 选项集 ⚠️（类型已分清，写侧 op 未定）
- **与枚举是两种 dataType**：字段类型清单 `{lable:"选项集", val:Enum}` / `{lable:"枚举", val:CtpEnum}`（`operate-list` chunk）
- 模块码映射：`UDC_ENUM:{name:"选项集", position→/app-design/basic-setting}`（operation-log chunk）→ **模块码叫 UDC_ENUM 但标签是"选项集"**
- UI（在 basic-setting 本体内，无独立 chunk）：选项集列表/新建选项集/选项名称/选项值编码（自动生成可修改）/选项值/排序号/状态/启用停用/「已经上架的选项集不能删除」/选项集导入模板
- op：`EnumSearchParentByCodePost`、`BasicDataDesign{Create,Update,Delete,BatchDelete}Post`（形态 B，前缀拼接）
- 后端：`DataTypeController` `data-types/base`(6 api) 待确认归属

### 3.3 自定义对象 ⚠️（两件事必须分开）
- 截图说明：「支持自定义对象，用于微流程/页面规则之间的相互调用数据传递」= **DTO**
- 前端 chunk：`src_pages_udc_customtype_index_tsx.21130696.js`（UI 实为字段级类型定义：显示名称/基础类型/最小最大长度/默认值/匹配规则/错误提示/多选）→ 这是**自定义数据类型**，不是 DTO 列表
- op：`udcCustomDataTypeSearch`（loader，key=body, type=`...InputBody`）、`SerialSchemeSearchNoPagePost`（apolloQuery）
- 后端：`DataTransferObjectController`（20 api：create/createDtoWithAttrs/update/updateDtoWithAttrs/deleteById/selectById）、`DataTypeController`
- 本会话 DTO 写侧 LIVE PASS：`POST create-dto-with-attrs` id=8711390834283907064
- **UNVERIFIED**：该 tab 实际渲染哪个子页（`_dataTransferObject` 页面在 zzprobe 存在）未逐层追到

### 3.4 字段集 ✅（读写 op 齐，未活体冒烟）
- 前端：`src_pages_app-design_entity-modeling_entity-fieldset_index_tsx.fdeccdc6.js`（本地 46KB）
- op：`postEntityAttribute`、`postBatchField`、`updateBatchField`、`deleteField`、`addGroup`(→`udcPageGroupCreatePost`, key=body)、`deleteGroupNode`(→`udcPageGroupDeleteIdPost`, key=path)、svc `udc-entity-field`/`udc-field-table`
- 后端：`AttributeGroupController` `udc/attribute-group`(7 api: create/update/cancel/remove/swap/operateBatch)、`AttributeSetController`(10 api)
- 注：GraphQL 面还有 `udcEntityAttributeBatchPost` / `udcEntityAttributeBatchUpdatePost`（本地 chunk query 原文）

### 3.5 参数 ✅
- 前端：`src_components_app-design_parameter-definition_index_tsx.d0a30409.js`（16KB）
- op：**`CtpParameterDefinitonPost` / `CtpParameterDefinitonUpdatePost` / `CtpParameterDefinitonDeletePost` / `CtpParameterDefinitonBatchDeletePost`**（`Definiton` 少一个 i 是平台原样，禁止"修正"）+ `udcDataTypeDataTypesParamGet`（type=`...GetInput`）
- 形态 C，前缀可变：`n=>"mutation example ($body: ".concat(n||"udc","CtpParameterDefinitonPostInputBody)"))`
- 后端：`ParameterController`（6 api：create/update/deleteById/deleteByIds/selectById/selectPageByCondition）

### 3.6 扩展实体 ✅（op↔method 名前后端对上）
- 前端：`src_pages_app-design_entity-modeling_custom-extension_index_tsx.400f885f.js`（7.8KB，UI：自定义扩展配置方案/字段名称前缀/预留字段数量/数据类型）+ `src_pages_app-design_extension-plan_index_tsx.c111914a.js`（21.9KB，UI：扩展实体名称/编码/选择流水号）
- **GraphQL op（`src_redux_store_ts`，形态 A' `udcMutationLoader`）**：`udcScalabilityOptionSelectAllOptionNamePost`（queryFields 含 `attributeDtoList{attributeGroup auditLog calculate caption dataFormat dataType dataTypeDisplayName ...}`）
- **REST 面（LIVE 端点存在性验证，只读 GET）**：
  - `GET /service/udc/scalability/selectByOptionId` → **200 `BOOT_3000`**（缺参，端点在）
  - `GET /service/udc/scalability-option/selectByAppId?appId=6419954374508955097` → **200 `BOOT_3000`**
  - `select-by-appid/tree` → 404；`/udc-extension-plan`（多个候选路径）→ **全 404**（它是前端 svc 变量名，非 REST 路径）
- **后端对齐（javap 5.3.517）**：`ScalabilityController` `udc/scalability`(6 api: create/update/deleteById/deleteByIds/selectById/selectByOptionId)、`ScalabilityOptionController`(8 api: …/`selectAllOptionName`/`selectScalabilityDataType`)
- **闭合证据**：前端 op `…SelectAllOptionNamePost` ↔ 后端 method `selectAllOptionName`，名逐字对上
- 注：页面 chunk 内 `customExtensionList`/`customExtListUpdate`/`scalabilityDtoList` 是 **reducer 属性名**（`t.customExtensionReducer`），不是 op —— 别误当调用链

### 3.7 流水号 ⚠️
- **tab 组件**：`f`=模块 30912（basic-setting 本体，读 `appDesign.appReducer.appDetails`），uniformityKey=`serial`
- 复用子组件：`vendors/node_modules_xiaozhua_biz-serial-scheme_dist_index-9208ea8a_js.b8764667.js`（npm 包，UI：预留规则/登录日期/登录组织/登录用户/序号/规则编码/规则名称）
- op：`udcUdcSerialSelectPost`（key=body, type=`...InputBody`）、`SerialConditionBatchCreatePost`（形态 B）；函数名 `serialSectionDtoList`、`combinedFieldList`、`simpleFieldList`、`getReserveData`
- 后端：**`UdcSerialConfigController`**（`udc-starter-runtime`，路径 `udc-runtime/serial-config{,/list,/select-entity-list,/select-entity-by-serial-id}`）—— registry 已有 4 条只读契约（`udc.serial.select_entity_list` 等）
- 写侧 op 未定 ⚠️

### 3.8 导入导出模板 ⚠️（op 半齐）
- 前端：`src_pages_udc_templateManage_index_tsx.edf44d56.js`（12.5KB，UI：模板名称/终端/页面类型/推荐标签/模板描述/序号/所属应用/表单应用/标准应用/创建人/创建时间/模板来源(平台预置/应用创建)）
- op：`udcExcelSearchListByConditionsPost`（key=body, type=`...InputBody`，本地 chunk 字面量 query）、`<appId驼峰><实体名>ExcelSearchListByConditionsPost`（形态 B 动态拼）、`udcFileDownloadUrlsPost`、REST `POST /excel/set-auth`
- 后端：`AttachmentTemplateController` `udc/attachment-template`(7 api: create/createBatch/selectByGuid/selectByGuids/selectByAppId/delete)
- 早前 audit：落表 `ctp_excel_export_template`

### 3.9 二维码 ❌（op 已知，后端未定位）
- 无独立 chunk（166 个 chunk 中 qrcode/qr-code/barcode 0 命中）
- op（形态 B，biz-basic-data chunk 内实证）：
  ```js
  let t = appName.replace(/\b(-\w)/g, x=>x.substring(1).toUpperCase());
  apolloQuery(`mutation ${t}CtpQrcodePageMetadataListPost($body: ${t}CtpQrcodePageMetadataListPostInputBody) {
      ${t}CtpQrcodePageMetadataListPost(body: $body) { code data{ content } message status } }`,
      {body:{...params}})   // params = {appName, appId, fullName}
  ```
- **op 名前缀 = appName 驼峰**，入参含实体 `fullName` → 按实体取页面元数据供扫码
- 后端：udc-web 5.3.517 javap 中 qrcode/barcode **0 命中** → 服务在标品侧（`Ctp` 前缀），UNVERIFIED

### 3.10 页面模板 ✅（LIVE）
- **tab 定义**：`pageTemplateManage`，组件 `v`=39637，`createElement(v.default,{category:"PAGE", sourceType, appId, appGuid})`，`visible: sourceType!=="FORM"`，uniformityKey=`""`
- 前端：`src_pages_app-design_template-manage_index_tsx.7ebad08d.js`（9.3KB，UI：公开模板/外框/页面/名称/分类/推荐标签/表单/排序号/描述/缩略图）
- op（9 个，全在 `6494d14a` services chunk）：`udcPageTemplateGet`(**key=path**)、`ClassSelectTreeCategoryGet`(**key=path**)、`CreateOrUpdatePost`、`PublishPost`、`DeleteByIdsPost`、`CheckNamePost`、`SearchNoPagePost`、`SearchWithRightsPost`、`PublishedSearchNoPagePost`
- 页面信息 op（7 个）：`udcPageInfo{BatchCreate,SearchNoPage,Delete,UpdateDraf,Update,DetailGet(path),PresetListAppGet(path)}`
- 页面分组：`udcPageGroup{CreatePost,DeleteIdPost}`
- 后端：`PageTemplateController` `udc/page-template`(14 api: batchCreate/createOrUpdate/saveAs/deleteById/selectById…)、`PageTemplateClassController` `udc/page-template-class`(7)、`PageTemplatePublishedController` `udc/page-template/published`(9)、`PageInfoController`(25)、`PageLayoutController`(18)
- LIVE PASS ×2（§1.4 #1 #2）

### 3.11 外框模板 ✅（type 机制已证）
- **tab 定义**：`layoutTemplateManage`，组件 `v`=39637（**与页面模板同一个组件**），`createElement(v.default,{category:"LAYOUT", ...})`，`visible: sourceType!=="FORM"`
- 前端：`src_pages_udc_page-frame-tmp-manage_index_tsx.95ba118a.js`（9.5KB，UI：创建分类/模板名称/终端/移动端/页面类型/模板描述/预览/编辑/重命名/添加分类/模板分类）
- **与页面模板共用 `udcPageTemplate*` 九个 op，靠 `pageType=LAYOUT` 区分**（page-type 常量表 §2）—— 现有三层证据：tab 组件 `category` prop、pageType 常量中文"外框"、published 表 LAYOUT 数据
- LIVE PASS：`udcPageTemplatePublishedSearchNoPagePost` 返回 LAYOUT 6 条（档案外框/审批外框_经典布局/审批外框_左右布局）
- 后端两层（勿混）：
  - 模板层 = `PageTemplateController`（pageType=LAYOUT 行）+ `PageTemplatePublishedController`
  - 布局实例层 = `PageLayoutController`(18 api: createBaseInfo/updateBaseInfo/findPageByRelationId/selectById/selectMergeListByAppId) + 表 `udc_page_layout`(56 行)
- 关联页面 chunk：`src_pages_design_page-frame_*`（sider/actions/copy-page-frame）

### 3.12 角色权限 ✅（跨微前端，链路已定）
- **不是 udc 的代码**：stub `src_pages_app-design_role-permission_index_tsx.4f87e943.js`（634B，纯容器）内写死：
  ```js
  RemoteComponent {config:{url:"/ctp-user/remoteEntry.js", scope:"ctp-user", module:"RolePermission"}}
  ```
- 真身在 `/ctp-user/remoteEntry.js`（68 chunk），已下 4 个：
  - `src_pages_role-permission_index_tsx` / `_entry_tsx`（15.9KB/16.2KB）：`roleList`、`resourceList`、`adminAppResourceTreeList`、`appResourceTreeList`、`mobileAppResourceTreeList`
  - `src_pages_role-authority_index_tsx`（57KB）：`authObjectList`、`authorityAuthorityList`、`dataPermissionList`、`ruleRoleList`、`ctpApplicationApplicationList`、svc `role-info`
  - `src_pages_system-role_index_tsx`：**`ctpUserCtpRoleSystemRoleSearch`**（key=body, type=`...InputBody`，LIVE 未调）
- 后端：udc-web 无 Role controller（符合预期，属 ctp-user 服务）UNVERIFIED

### 3.13 基础资料 ✅（redux 命名空间 + 建后初始化链已追到）
- 与选项集共用 `biz-basic-data` 共享包（220KB chunk `c121b851.js`）
- **归属 redux 命名空间 `data-management`**（`createAsyncThunk("data-management/getBasicDataSearch")`）—— 即"数据管理"页，设置里"基础资料"标签复用同一套 op
- op 与形态：
  | op | 形态 | 关键细节 |
  |---|---|---|
  | `BasicDataSearch` | A | thunk `getBasicDataSearch`，body 含 `pageInfo{needTotal,pageNumber,pageSize}` + `sort.orders[{direction:"ASC",property:"createTime"}]` |
  | `<prefix>BasicDataDesignCreatePost` / `…UpdatePost` | B | 前缀 `Z(appName)`（驼峰），成功回调 `createSuccessfully/modifySuccessfully` |
  | `udcBasicDataDesignInitBasicdataPagePost` | A | `getRequestByAppName("udc")`、`paramsKey:"body"`、`params:{id,appId}` —— **建完即初始化页面**，返回 `masterEntityIds` + `dataSourceDtoList:[{appId, dataShape:"LIST", layoutId:"0", pageUrlType:"PC", pageId, ...}]` |
  | `<prefix>BasicDataDataTypesGet` | A（零入参） | 只带 `queryFields:"content{ caption extensionProperties frontComponent length name }"` |
  | `<prefix>BasicDataSelectPresetAttributesGet` | A（零入参） | queryFields 含 **`actionType caption dataType defaultValue description edit id maxLength minLength name system notNull uniqueness enabled`** —— 与 A 层属性冒烟的 `uniqueness` 白名单同源 |
- 后端归属：javap 5.3.517 中无 `BasicData*Controller` → UNVERIFIED（候选 `DataTypeController` `data-types/base` 只有 6 个 select 方法，不含 create/update）

### 3.14 顺带：功能节点/菜单（非 tab，但同 chunk 抽到）
- op：`udcFunctionFindTreeAndGroupPost`（mutation, $body）、`udcMetaDataSelectFunctionNodeWithPageTreePost`
- 后端：`FunctionNodeController`（19 api: createFunction/updateFunction/createFunctionRefer/updateFunctionRefer/updateFunctionReferName/selectFunction…）

---

## 4. 未闭环项（如实登记）

| 项 | 状态 | 缺什么 |
|---|---|---|
| 扩展实体调用链 | ✅ 已闭环 | op↔method 名对上 + REST 端点 LIVE（见 §3.6）；**写侧 op**（create/update/delete 的 GraphQL 名）未逐个定位 |
| 二维码后端 | UNVERIFIED | udc-web javap 0 命中，`Ctp` 前缀指向标品服务（前端构造式已完整，见 §3.9） |
| 角色权限后端 | UNVERIFIED | 属 ctp-user 服务，未解其后端；前端 4 chunk + op 已齐 |
| 选项集写侧 op 归属 | UNVERIFIED | `BasicDataDesign{Create,Update,Delete,BatchDelete}Post` 形态 B 已确认，但这些是"基础资料"命名空间的 op，选项集 tab 是否复用同一套未验证 |
| 基础资料后端 controller | UNVERIFIED | javap 无 `BasicData*Controller`；`DataTypeController` 仅 6 个 select 方法，无 create/update |
| jar 内 class 级确认 | BLOCKED | 容器内 `unzip -p /app/udc-assemble.jar`（502MB）静默失败，无输出（镜像 tag `udc:5.3.517` 已完成版本对齐） |
| `class_mapping` 字段可靠性 | UNVERIFIED | javap artifact 中部分值非规范路径形态（如 `search/term`、`attribute/update`、`select-by-name/attributes`），疑似提取到非常量池末尾 mapping，引用时须复核 |
| 二维码/角色权限 op 活体调用 | UNVERIFIED | 只做静态构造，未发请求 |
| `BOOT_3000` 语义 | UNVERIFIED | javap txt 全文 grep 0 命中（端点存在性判定用它：200+BOOT_3000 = 端点在但缺参） |

---

## 5. 复核索引（证据文件）

- 本地 chunk：`<HERMES_HOME>/cache/scratch/udc-pod-chunks/`（36 个，含 `remoteEntry.js`、`ctp-user-remoteEntry.js`、`manifest.json`、`op-catalog.json`）
- 原始 bundle（另一批）：`<HERMES_HOME>/cache/scratch/udc-semantics-audit/webpack-modules/`（1387 个）
- 后端 javap：`<XIAOZHUA_AGENT_ROOT>/docs/audit/artifacts/udc-web-5.3.517-javap/_full_api_map.json`（54 controller）、`*.javap.txt`
- 探测脚本：`<HERMES_HOME>/cache/scratch/pod_probe.sh`（SSH heredoc；注意 Windows 下须 `ssh host 'bash -s' < file` 或 base64 内联，纯 `<` 与嵌套单引号会断）


---

## 附：构建/部署执行链 op 组（2026-10-12 用户抓包 `?udcRuntimeDeployNormalPost` + 主 store 核实）

**URL query 形态**：`POST /service/udc/graphql?<op名>` —— **op 名放 URL query 是 Apollo 客户端带的，可选**（`?op` 与 body `operationName` 两种都活体验证 `BOOT_0000`）。

| op | 用途 | 参数（主 store 原文） |
|---|---|---|
| **`udcRuntimeDeployNormalPost`** | **测试构建执行器** | `paramsType:"…InputBody"`、`paramsKey:"body"`、**`params:{deployDto:e}`**（**body 是 `{deployDto:…}` 嵌套**）、`queryFields:"content{appId,deployId,deployType,projectType,terminalType}"`、走 **queryLoader**（非 mutation） |
| `udcDeploymentAppReadyStatePost` | 就绪状态 | `params:{appId:e}`、`queryFields:"content"`、`showError:!0` → `{validate:true, appName:"datamigration9000000000000000001", appVersion:"1.0.0", appId, terminalType:null, enableLoginEntry:false, enableClearEntry:true, state}` |
| `udcDeploymentLatestTestInfoPost` | 最新测试信息 | body |
| `udcManagerRequestStatusRequestGet` | 构建请求状态 | `paramsType:"…InputPath"`、`paramsKey:"path"` |
| `udcRuntimeAuthAccessUrlPost` | 访问 URL | body |
| `udcRuntimeDeployOnlinePost` | 上线发布 | `params:{...e, **deployType:"ON_ONLINE"**}`（印证「deploy-normal 测试 / app-online-new 上线」边界） |

**状态枚举**：`NONE | STOP | RUNNING | PENDING | FAILED | UNKNOWN`。

**LIVE 记录（2026-10-12）**：`udcDeploymentAppReadyStatePost` + `body:{appId:8704025620829192834}` → `BOOT_0000`，`appName="datamigration9000000000000000001"`、`appVersion="1.0.0"`、`enableLoginEntry:false`、`enableClearEntry:true`。两种 URL 形态（`?op` / 纯 body）结果一致。
