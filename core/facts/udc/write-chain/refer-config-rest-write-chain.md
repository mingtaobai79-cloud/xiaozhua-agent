# 参照域（udc_refer_config）REST 写链 —— 全链打通

> 领域：实体 → 参照（`udc/refer-config`，`ReferConfigController` @ udc-web）
> 状态：**参照创建 LIVE PASS + PC/MOBILE 配对一致 LIVE VERIFIED**
> 证据：CFR 反编译 `udc-plugin-api` / `udc-biz` 5.3.517 + 库内真实样本 + REST 实测

## 1. 端点面

| 写 | 路径 | 入参 → 出参 |
|---|---|---|
| W | `POST /udc/refer-config/create` | `ReferConfigDto` → `SingleResponse<Long>` |
| W | `POST /udc/refer-config/create-or-update` | `ReferConfigDto` → `Long` |
| W | `POST /udc/refer-config/create-config-info` | `ReferConfigInfoDto`（含 `referConfigDetail` 多终端）→ `Long` |
| W | `POST /udc/refer-config/update` | `ReferConfigDto` → `Integer` |
| W | `POST /udc/refer-config/update-config-info` | `ReferConfigInfoDto` → `Integer` |
| W | `POST /udc/refer-config/convert-to-mobile/{id}` | PC 转移动 |
| W | `POST /udc/refer-config/delete` / `delete-by-group-id` | |
| | `GET /udc/refer-config/{id}`、`selectPageByCondition`、`select-by-group` | 读 |

## 2. `ReferConfigDto` 契约（CFR，`com.seeyon.udc.dto` @ udc-plugin-api）

```jsonc
{
  id,                                  // update 必带
  caption*,        // @NotBlank @Size(1,50)
  type*,           // @NotBlank @Size(1,30)  —— 样本值 "List"
  displayName*,    // @NotBlank @Length(max=4000)  —— JSON 字符串（显示字段路径）
  pullDisplayName, // @Length(max=4000)
  detailPage,      // @Size(max=4000)
  detailPageId,
  configInfo*,     // 服务端 @NotBlank 校验（见 §3）
  isDefault,       // Boolean
  appId, entityId,
  terminalType,    // TerminalTypeEnum: PC(1) | MOBILE(2)
  groupId,         // 同组 PC/MOBILE 配对键（样本为 0）
  sourceType,      // ReferConfigSourceTypeEnum（DB 存 0，见 §5 坑）
  pageId = 0,
  relationApp, relationEntity, sourceRefer,
  actionType       // ActionType: ADD(0) | UPDATE(1) | DELETE(2) | DEFAULT(3)
}
ReferConfigInfoDto {                       // create-config-info / update-config-info
  caption*, appId, entityId, type*,
  referConfigDetail: List<ReferConfigDto>,   // ★ 一次提交 PC + MOBILE 两条
  operationLog
}
```

## 3. `configInfo` 结构（取自库内真实样本）

```jsonc
{
  "columns":[{"width":120,"widthType":"px","lineLimitedContent":"custom",
              "path":[{"fieldId":"<attrId>","entity":{"id":"<entityId>","appName":null}}]}],
  "search":[{"path":[{"fieldId":"<attrId>","entity":{"id":"<entityId>","appName":null}}]}],
  "orders":[{"path":[{"fieldId":"<attrId>","entity":{"id":"<entityId>","appName":null}}],
             "direction":"DESC"}],
  "whereCond":[{...条件树...}],
  "entities":["<entityId>"]
}
```

`displayName` 同样是**路径数组 JSON**：
```json
[{"fieldId":"8016904624316689195","entity":{"id":"474806313816300867","appName":null}}]
```

## 4. ★ 本地 LIVE 证据

```jsonc
POST /service/udc/refer-config/create
{"caption":"小爪实验参照","type":"List","displayName":"[...]","appId":APP,"entityId":<实体id>,
 "sourceType":0,"terminalType":2,"actionType":0,"pageId":0,"isDefault":false,
 "relationApp":"<appId>","relationEntity":"<fullName>","configInfo":"{columns,search,orders,whereCond,entities}"}
→ {"code":"BOOT_0000","data":{"content":"-1093318230470376547"}}
```
DB 回读 `udc_refer_config` id=-1093318230470376547（terminal_type=2 MOBILE, type='List'）。

## 5. ★ 三个坑（都实测踩过）

### 5.1 `sourceType` 用**数值**，不能用枚举名
```
{"sourceType":"CUSTOMIZE"} → BOOT_3002 No enum constant ...ReferConfigSourceTypeEnum.CUSTOMIZE
{"sourceType":0}           → 通过
```
即使 Java 端是 `ReferConfigSourceTypeEnum`，反序列化按 **DB 数值（0）** 走。

### 5.2 `configInfo` 必填（服务端 @NotBlank）
```
{} → BOOT_1001 configInfo must not be blank
```
必须给 `{columns,search,orders,whereCond,entities}` 结构。

### 5.3 ★ PC 参照必须与 MOBILE 参照配置**完全一致**（否则 UDC_CE_ENTITY_02119）
```
UDC_CE_ENTITY_02119 | refer [小爪实验实体参照]
  message: The entity refer PC mobile configuration is inconsistent:[参照显示名称不一致 / 显示列不一致 / 排序不一致]
  elementProperty: {groupId:"0", terminal:"PC", id:"<referId>"}
  path: displayName | columns | orders[null].direction | orders[null].path
```
检码逐项比对 **displayName / columns / orders(含 direction+path)** 三处：
- `displayName` 路径数组须相同
- `columns` 的 path 集合须相同
- `orders` 的 fieldId **和 direction** 都须相同（direction 不一致也算）

**修法**：把移动端参照的 `displayName`/`configInfo` 直接对齐 PC 那条的同名字段 → 02119 归零（LIVE VERIFIED，8 WARN → 0）。

## 6. `udc_refer_config` 表列

`id, create_time, tenant_id, update_time, version, guid, publish_state, app_id, caption,
config_info, detail_page_id, display_name, entity_id, is_default, type, terminal_type,
group_id, owner_code, backup_code, detail_page, source_type, page_id, relation_app,
relation_entity, source_refer, pull_display_name, original_id`

## 7. 边界（未做）

- 参照的"**下一步**"（选择后回填/关联字段绑定）未做 —— 只建了参照本体 + PC/MOBILE 一致。
- `create-config-info`（一次提交多终端）未实测（本次走 create + update 两步）。
- `detailPage`/`detailPageId`（参照详情页）未绑。
- `refer_config_group` 表分组语义未验。

## 8. 检测面复核

参照建成 + 配对一致后：**2 WARN / 0 ERROR**（04003 × 2 草稿微流程，不阻塞）。
