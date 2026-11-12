# udc.page.schema｜页面设计器拖拽 Schema 协议

## 1. Capability
页面设计器（拖拽式）将控件布局保存为 JSON Schema，存储在 `udc_test2.udc_page_schema` 表。

## 2. Version
udc-web 5.3.517 / designer_version 2.4.0

## 3. 存储
- 表: `udc_test2.udc_page_schema`
- 关键字段: `page_schema`(正式) + `draft_page_schema`(草稿) — LONGTEXT JSON
- 关联: `page_id` → `udc_page_info.id`
- 触发: 设计器"保存并提交"按钮 → udcPageInfoUpdatePost GraphQL mutation

## 4. JSON 结构（拖拽产生的元数据）
```json
{
  "children": ["udcDataGridView_iPdx"],           // 顶层子控件ID引用
  "childById": {                                   // 控件定义（按ID索引）
    "udcDataGridView_iPdx": {
      "id": "udcDataGridView_iPdx",
      "type": "UdcDataGridView",                  // 控件类型
      "parentId": "PAGE",
      "settings": {
        "columns": [                               // 列定义（绑定实体字段）
          {
            "dataIndex": "ziduan1",               // 实体字段编码
            "dataFieldId": "2667087430121200499",  // 实体字段ID
            "fullName": "com.seeyon.{appName}.domain.entity.ZzprobeEnt1.ziduan1",
            "dataType": "STRING",
            "widthValue": 100, "align": "left"
          }
        ],
        "topOperates": [                          // 顶部操作按钮
          {"id": "K76cM3lSTR", "name": "操作1", "type": "item"}
        ]
      }
    }
  },
  "settings": {                                    // 页面级设置
    "title": {"type": "Simple"},
    "resolutionPower": {"type": "auto", "value": {"per": 100, "minWidth": 1200, "maxWidth": 1920}},
    "backgroundColor": "#ffffff",
    "boxModel": {"margin": "0 auto 0 auto", "padding": "16px 20px 0 20px"}
  },
  "pageDefinedEvents": [],                        // 页面事件（拖拽事件规则后填充）
  "pageVariable": [],                              // 页面变量
  "masterEntityIds": "1214120700508048602",        // 主实体ID
  "pageType": "SEARCH_LIST",                       // 页面类型
  "type": "PAGE",                                  // 根节点类型
  "terminal": "PC"                                 // 终端类型
}
```

## 5. 控件类型清单
| 类别 | 控件类型 |
|---|---|
| 页面 | PAGE |
| 布局 | UdcContainer, UdcPanel |
| 数据 | UdcDataGridView, UdcRepeatNode, UdcFilter, UdcForm |
| 录入 | Input, TextArea, DateTimePicker, CascaderSelect, GroupRadio |
| 展示 | Label, UdcToolBar |
| 标品参考 | 13种(标品项目考核管理实测) |

## 6. 参照文件
- zzprobe实测: `page-schema-zzprobe.json` (7.4KB, UdcDataGridView+1列)
- 标品参考: `page-schema-standard-ref.json` (74KB, 13种控件)
- DB表: `udc_test2.udc_page_schema` (page_schema LONGTEXT)
- 关联 Controller: `PageInfoController`(基本信息), `PageLayoutController`(布局)

## 7. 保存链路
拖拽 → React 状态更新 → "保存并提交" → POST udcPageInfoUpdatePost(graphql) → udc_page_schema 表


---

## 【已验证】API 构造列表页全链（2026-10-01 03:00）

### 结论：页面设计态 100% 可 API 自动化
拖拽只是前端 Redux 状态操作；保存动作 = 一个 GraphQL mutation。**不需要任何人工拖拽。**

### 鉴权（关键坑）
- ✅ `Cookie: SY_ACCESS_TOKEN=...; TK_EXP=...; SY_UID=...`
- ❌ `accessToken` 请求头 → BOOT_1006 跳 SSO
- token 续期：`POST /service/ctp-user/auth/token`，读 `Set-Cookie` + `data.content['access-token']`

### 保存请求体（实测通过）
```
mutation submitPage($body: udcPageInfoUpdatePostInputBody) {
  udcPageInfoUpdatePost(body: $body) { code data{content} message status }
}
variables.body = {
  appId, id(=originId), urlType, pageSchema(JSON), draftPageSchema(JSON),
  publicAccess, pageUrl, pageType, groupId, guid, relationGroupId,
  sortNo, layoutId:"0", layoutInfo:"",
  eventDefine, outParameters, inPortletParams, pageVariable
}
→ BOOT_0000 SUCCESS
```

### 前端代码引擎硬约束（踩坑 3 次才通）
`@seeyon/udc-code-engine/parse-page/component-status-deps.js:166` 遍历控件 settings 时：
- 每控件 settings **必须**有 `topOperates[]` + `actionColumnOperates[]` + `operateButtons[]`
- 缺任一 → `TypeError: Cannot read properties of undefined` → 部署 state=2 失败
- UdcDataGridView 还需 `settings.dataSource.entity.{id,name,fullName,appName,caption}`
- 非标字段（rowSelection/pagination/scroll/size/stripe/bordered）无害

### 部署状态判定
| state | 含义 |
|---|---|
| 2 | 编译中 / 失败（msg 里有具体原因）|
| 0 | 成功（msg 为空）|

### 通道判定修正
| 环节 | 结论 |
|---|---|
| 页面设计（拖控件）| ✅ **API 可**（构造 schema JSON + submitPage）|
| 微流程编排 | ✅ 同构（dataSchema JSON + 对应 mutation）|
| 建应用 | ⚠️ REST 持久化不完整，需 UI 表单 |
