# 画布节点定义清单（从前端 bundle 提取）

> 自动生成，勿手改：`python tools/audit/extract_microflow_nodes.py`

微流程 / 页面规则 / 实体规则共用同一套画布，但**同 type 的定义有几套互不相同**，
按所在规则类型取对应那份，key 用错会「check 通过但页面不认」。

`必填(顶层)` 是「保存并提交」时前端真正校验的键（值为 null/undefined 就报错）；
`必填(在rules里)` 前端不校验，但页面槽位为空 —— 两套判据分开用。

## 按归属分组

### 实体规则（ENTITY_RULE，26 个）

| 名称 | type | 必填(顶层) | 必填(在rules里) | 字段 |
|---|---|---|---|---|
| 下载全部 | `DOWNLOAD_ALL` | — | — | config |
| 刷新页面 | `RELOAD_PAGE` | — | — | — |
| 单据转文档 | `FROM_CONVERT` | — | — | config |
| 可见性 | `ATTR_VISIBLE` | — | — | visible、invisible |
| 唯一 | `ATTRIBUTE_UNIQUE` | value | params | params、value* |
| 实体操作 | `ENTITY` | outputName | config | config、outputName* |
| 必填 | `ATTRIBUTE_REQUIRED` | value | params | params、value* |
| 打印 | `PRINTPAGE` | — | — | — |
| 打开链接 | `OPEN_REPORT` | — | — | config |
| 扩展行为 | `EXTEND_ACTION` | — | — | config |
| 扫码 | `SCAN_CODE` | outputName | — | scanType、outputName* |
| 批量标签打印 | `LABEL_PRINT` | — | — | config |
| 抛出页面事件 | `THROW_EVENT` | event | — | event* |
| 收藏/取消收藏 | `ATTENTION` | — | — | config |
| 显示信息 | `SHOW_MESSAGE` | level、value | param | param、level*、value* |
| 流程动作 | `FLOW_ACTION` | — | — | actionName |
| 类型转换 | `CONVERT_DATA` | convertType、selectParam、regex、title | — | convertType*、selectParam*、regex*、title* |
| 自定义错误 | `FRONT_CUSTOM_ERROR` | error | — | error* |
| 设置值 | `ASSIGN_VALUE` | value | param | param、value* |
| 设置数据源 | `SET_DATASOURCE` | — | — | items |
| 调用后端服务 | `CALL_SERVICE` | outputName | — | app、service、paramList、outPutDesc、outputName* |
| 锚点跳转 | `LOCATION_CMP` | — | — | — |
| 附件上传 | `ATTACHMENT_UPLOAD` | outputName | — | outputName* |
| 附件下载 | `ATTACHMENT_DOWNLOAD` | — | — | — |
| 附件预览 | `ATTACHMENT_PREVIEW` | — | — | config |
| 默认值 | `DEFAULT_VALUE` | attrs | — | attrs* |

### 页面规则（FRONTEND_RULE，20 个）

| 名称 | type | 必填(顶层) | 必填(在rules里) | 字段 |
|---|---|---|---|---|
| 值操作 | `VALUE_HANDLE` | — | — | items |
| 取消关闭页面 | `CLOSE_PAGE` | — | — | — |
| 对话框 | `DIALOG` | title、showInfo、outPutName | — | scenario、title*、showInfo*、okText、cancelText、configBtn、outPutName* |
| 对话框 | `DIALOG` | showInfo | closeType | messageType、showInfo*、element、closeType |
| 必填 | `CLEAR_VALUE` | — | — | element |
| 必填 | `ATTRIBUTE_REQUIRED` | — | — | required、option |
| 打开链接 | `OPEN_LINK` | — | — | config |
| 打开页面 | `OPEN_PAGE` | outputName | — | config、outputName* |
| 执行脚本 | `EXECUTE` | caption | — | caption* |
| 控件动作 | `OTHER_CONTROL` | outputName | — | config、outputName* |
| 数据源保存 | `DATA_SOURCE_SAVE` | dataSource | — | dataSource* |
| 数据源删除 | `DATA_SOURCE_DELETE` | dataSource | — | dataSource* |
| 数据源查询 | `DATA_SOURCE_SEARCH` | dataSource | — | dataSource* |
| 清空信息 | `CLEAR_MESSAGE_INFO` | — | element、element | element、element |
| 确定关闭页面 | `CONFIRM_CLOSE_PAGE` | — | — | — |
| 设置值 | `ASSIGN_VALUE` | element、value | — | element*、value* |
| 设置可见 | `VISIBLE` | — | — | visible、invisible |
| 调用微流程 | `CALL_MICRO_FLOW` | mfService、value、mappingType、value、pageInfoSourceElement、outputName | — | mfService*、value*、mappingType*、value*、attrs、outPutDesc、pageInfoSourceElement*、outputName* |
| 调用页面规则 | `CALL_FRONT_FLOW` | microFlow、value、mappingType、value、outputName | — | microFlow*、value*、mappingType*、value*、attrs、outPutDesc、outputName* |
| 高级属性操作 | `ADDVANCED_PROPERTIES` | — | — | items |

### 微流程（MICROFLOW，5 个）

| 名称 | type | 必填(顶层) | 必填(在rules里) | 字段 |
|---|---|---|---|---|
| 只读 | `READ_ONLY` | — | — | readOnly、disabled、editable |
| 子微流程 | `SUB_MICROFLOW` | mfService、value、mappingType、value、pageInfo、outputName | — | mfService*、value*、mappingType*、value*、attrs、pageInfo*、outPutDesc、outputName* |
| 控件状态 | `CONTROL_STATUS` | — | — | editable、readOnly、disabled、invisible |
| 类型转换 | `CONVERT_DATA` | convertType、selectParam、regex、title | — | convertType*、selectParam*、regex*、title* |
| 自定义服务 | `CALL_APP_SERVICE` | app、selectMethod、value、mappingType、selectParam、pageInfo、outputName | — | app*、selectMethod*、condition、value*、mappingType*、value、value、attrs、selectParam*、mapping、pageInfo*、outPutDesc、outputName* |

## ⚠ 同名多套定义（必须按规则类型选对应那份）

- **`ASSIGN_VALUE`** — 2 份：
    - 页面规则 @1137911：element、value
    - 实体规则 @1216303：param、value
- **`ATTRIBUTE_REQUIRED`** — 2 份：
    - 页面规则 @1141564：required、option
    - 实体规则 @1217649：params、value
- **`CONVERT_DATA`** — 2 份：
    - 微流程 @1094438：convertType、selectParam、regex、title
    - 实体规则 @1199579：convertType、selectParam、regex、title
- **`DIALOG`** — 2 份：
    - 页面规则 @1143142：scenario、title、showInfo、okText、cancelText、configBtn、outPutName
    - 页面规则 @1145122：messageType、showInfo、element、closeType
