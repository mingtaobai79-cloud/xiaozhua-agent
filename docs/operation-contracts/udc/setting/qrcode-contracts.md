# 操作契约 · 设置域 / 二维码（QR Code Rule）

依据：反编译 `boot-starter-qrcode-5.3.262.jar` 的 `CtpQrCodeRuleController`
+ 2026-10-21 LIVE 实测。事实格见 `core/facts/udc/setting/qrcode/create.md`。

## 协议：REST（不是 GraphQL）

前缀 `/service/udc/qrcode-rule/*`。实现在 `boot-starter-qrcode`，不在 udc 构件里。

## operation 清单

| operation | 方法 | 路径 | 写 | 状态 |
|---|---|---|---|---|
| `setting.qrcode.rule.create` | POST | `/udc/qrcode-rule/create` | 是 | **LIVE PASS** |
| `setting.qrcode.rule.search` | POST | `/udc/qrcode-rule/search` | 否 | LIVE PASS |
| `setting.qrcode.rule.search_no_page` | POST | `/udc/qrcode-rule/search-no-page` | 否 | LIVE PASS |
| `setting.qrcode.rule.delete` | POST | `/udc/qrcode-rule/delete` | 是 | LIVE PASS |
| `setting.qrcode.rule.batch_delete` | POST | `/udc/qrcode-rule/batch-delete` | 是 | UNVERIFIED |
| `setting.qrcode.rule.update` | POST | `/udc/qrcode-rule/update` | 是 | UNVERIFIED |
| `setting.qrcode.rule.update_fieldcode` | POST | `/udc/qrcode-rule/update-fieldcode` | 是 | UNVERIFIED |
| `setting.qrcode.rule.update_implement` | POST | `/udc/qrcode-rule/update-implement` | 是 | UNVERIFIED |
| `setting.qrcode.rule.physical_delete` | POST | `/udc/qrcode-rule/physical-delete` | 是 | UNVERIFIED |
| `setting.qrcode.rule.deactivate` | POST | `/udc/qrcode-rule/deactivate` | 是 | UNVERIFIED |
| `setting.qrcode.rule.start_using` | POST | `/udc/qrcode-rule/start-using` | 是 | UNVERIFIED |
| `setting.qrcode.rule.get_by_id` | GET | `/udc/qrcode-rule/{id}` | 否 | UNVERIFIED |
| `setting.qrcode.rule.get_by_guid` | GET | `/udc/qrcode-rule/detail/{guid}` | 否 | UNVERIFIED |
| `setting.qrcode.rule.design_dropdown` | POST | `/udc/qrcode-rule/search-for-design-drop-down-list` | 否 | UNVERIFIED |

## create 的可选 body 槽位

```json
{
  "name": "≤50字，必填",
  "type": "FIELDQRCODE | BARCODE | LINKQRCODE | QRCODE",
  "linkType": "APP | CUSTOM",
  "appId": "<appId>",
  "appGuid": "<appGuid>",
  "entityFullName": "com.seeyon.<appName>.domain.entity.<Name>",
  "valueFieldCode": "字段码/条码必填；实体属性 name",
  "pcPagePath": "链接码必填；udc_page_info.page_url",
  "mobilePagePath": "链接码可选"
}
```

## 必填矩阵

| type | valueFieldCode | pcPagePath / mobilePagePath |
|---|---|---|
| `FIELDQRCODE` | **必填** | 留空 |
| `BARCODE` | **必填** | 留空 |
| `LINKQRCODE` | 留空 | **至少一个** |
| `QRCODE` | — | 页面 UI 不给选（VACUUM） |

## 错误码

| 场景 | 码 / 文案 |
|---|---|
| name 空 | `BOOT_1001` 规则名称不能为空 |
| name > 50 | `@Size(max=50)` 个数必须在1到50之间 |
| search 传 `sort:{}` | `BOOT_3000` message:null |
| delete 传裸 Long | `BOOT_4002` 数据不存在或无权限查看 |

## 链接二维码的页面值来源（关键）

`pcPagePath` = **`udc_page_info.page_url`**，不是 URL 路由、不是 `udc_resource.code`。

候选查询：

```sql
SELECT id, page_url, caption, page_type, url_type
FROM udc_test2.udc_page_info
WHERE app_id = ?
  AND (master_entity_ids LIKE '%<实体全类名>%'
       OR include_entity_ids LIKE '%<实体全类名>%')
ORDER BY sort_no
```

⚠ `udc_page_info` 没有 `is_deleted` 列。

页面手选对照（2026-10-21）：

```
选「数据源配置信息列表页」→ 落库 pc_page_path = 'sjypzxxListPage'
该实体候选 3 个：
  sjypzxxListPage       数据源配置信息列表页
  sjypzxxListPagecopy   数据源配置信息列表弹窗选择页面
  sjypzxxDetailPage     数据源配置信息详情页
```

## 组装提醒

- 枚举**传字符串**（`FIELDQRCODE` 等），DB 存 ordinal
- `search` 三 key 平铺：`{pageInfo, paramsDto, sort}`，**`sort` 必须 `null`**
- `search-no-page` 只传 `{"paramsDto": {...}}`
- `delete` / `physical-delete` 传 `{"id": <Long>}`
