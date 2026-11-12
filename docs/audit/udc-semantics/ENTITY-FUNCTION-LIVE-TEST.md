# 实体页面全功能活体测试报告（2026-10-12）

**测试对象**：应用 `8704025620829192834`（`datamigration9000000000000000001`，7 个数据迁移业务实体——**全程未碰**），在其下建专用测试实体 `smokeEnt`。
**运行日志**：`<HERMES_HOME>/cache/scratch/entity_fn_run_log.json`（每个请求/响应/消息/code 全记录）。
**清理**：测试后全部删除，**DB 双证零残留**（实体/字段/索引/规则各 0 行，分组 0 行，应用实体总数回到 7）。

## 功能测试矩阵

| # | 功能 | op | 结果 | 关键发现/新约束 |
|---|---|---|---|---|
| A1 | 创建实体 | `udcEntityPost` + `{...body, appId}` | ✅ `BOOT_0000` | 默认 `{multiplicity:ONE2MANY, category:ENTITY, publishState:UNPUBLISH, customScalabilityId:"0", stereotype:"standard"}` |
| A2 | 回读实体 | `udcEntitySelectAllByAppidAppGet` | ✅ identity 5/5 | 平台自动生成 `tableName=smokeent_<guid>`、`g_l_index` |
| A3 | **更新实体** | `udcEntityUpdatePost` | ✅（3 次失败后） | **必须带 `stereotype`（BOOT_1001）+ `tableName`（BOOT_1000 实体tableName不能为空!）**；`appId` 前端自动注入 |
| A4 | 实体分组 | `udcEntityGroupCreatePost`（**不是** …CreateEntityGroupPost） | ✅ id 返回 | 分组表无 `name` 列，用 `caption` |
| A5 | openAPI 读 | `udcEntityOpenApiSelectGet` | ❌ 参数形态未通 | DB：新建实体 `open_api_data=''`、`permission=0`、`entity_group_id=0` |
| B1 | 建 6 类型字段 | `udcEntityAttributePost` | ✅ **6/6** | STRING/INTEGER/DECIMAL/DATE/DATETIME/BOOLEAN；平台给默认 `max_length`（STRING=100、INT=10、DECIMAL/DATE=20、BOOL=5）、`db_column_name`（下划线化）、`calculate=NORMAL`、`encryption=NOT_ENCRYPTION` |
| B3 | 默认值 | `udcEntityAttributeUpdatePost` | ✅ DB `default_value='冒烟默认'`、`default_value_caption` | 需完整形态回读再改（66 字段） |
| B4 | 必填 | 同上 | ✅ DB `is_not_null=1` | — |
| B5 | 唯一 | 同上 | ✅ DB `uniqueness=1` → **自动建唯一索引** | 见 C2 |
| B6 | min/max | 同上 | ✅ DB `min='0', max='9999'`（字符串存） | — |
| B7 | 字段组 | `udcAttributeGroupCreatePost` | ✅ id 返回 | 查询侧 3 个 op 名探测未通（次要） |
| B8 | 删除字段 | `udcEntityAttributeDeletePost {id}` | ✅ `content=1` + 回读已删 | — |
| C1 | 普通索引 | `udcIndexPost` | ✅ | **name 被平台改写**：传 `idx_smoke_str` → 存为 `idx_4518643506346672844`（`idx_/uk_` + 时间戳） |
| C2 | 唯一索引 | 同上 | ⚠️ `UDC_INDEX_0003` 拒绝 | **B5 `uniqueness=true` 自动生成唯一索引**（`uk_8101892493615121233`，`indexSource=ATTRIBUTE_UNIQUE`）→ 手工再建同字段唯一索引 = 重复被拒 |
| C3 | 索引列表 | `udcIndexEntityListPost`（**裸 Long**） | ✅ | `indexSource` 三值：`MANUAL_CREATE` / `ATTRIBUTE_UNIQUE`（自动） |
| D1 | 规则名检查 | `udcMicroflowCheckMicroFlowCaptionPost` | ✅ `content=false`（不重复） | **不是** CheckCaption |
| D2 | 创建规则 | `udcMicroflowCreatePost` | ✅（name 修正后） | **`name` 禁下划线**（`UDC_ENTITY_0001`: must use a combination of letters and numbers that first are letters）；前端 `"name_"+Date.now()` 提交前会调整 |
| D3 | 规则列表 | `udcMicroflowSearchEntityRulePost` | ✅ | **新规则 `groupType:"DEFAULT"`**（VALIDATE/ASSIGN_VALUE 需进编辑器设，创建时无此参数）、`state:"DRAFT"`；queryFields 多写 `sourceId/triggerType` 会导致整查询失败 |
| E1 | 创建事件 | `udcEventCreateWithDataPost` | ✅（3 次失败后） | **`eventDataType:"OBJECT"`（大写；`Object` 报 `No enum constant ObjectTypeEnum.Object`）+ `eventDataList` 必填（`UDC_EVENT_0002`）+ attributes 的 `dataTypeCategory` ∈ `PRIMITIVE`/`ENUM`/`COMPOSITE`（`STRING` 报 `No enum constant DataTypeCategoryEnum.STRING`）** |
| E2 | 事件列表 | `udcEventListPost` | ✅ | body 形态 `{"params":{sourceId}}` |
| E3 | 删除事件 | `udcEventDeletePost` | ✅ `content=1` | — |
| **F** | **参照配置** | **`udcReferConfigCreateConfigInfoPost`**（新建）/ `udcReferConfigUpdateConfigInfoPost`（更新）/ `udcReferConfigDeleteByGroupIdPost{groupId}`（删） | ✅ **全通（2026-10-12 二轮）** | **正确 op 不是 `udcReferConfigCreateOrUpdatePost`**（那是列表页快速保存，入参 `ReferConfigDto` 不含 `referConfigDetail`，乱传报 `Parameter Error`）。正确入参 = **`ReferConfigInfoDto`**（常量池全解）：`{appId*, entityId, caption*, type, sample, referConfigDetail[], operationLog}`；detail 元素（前端 e1 原文）：`{appId, entityId, caption, type, configInfo(JSON字符串), displayName(JSON字符串), terminalType, id, actionType:"INSERT"|"UPDATE", pullDisplayName}`。`configInfo` 内部键（真实样本）：`{entities:"[<entityId>]", columns:[{name,caption,width}], orders:[], pageSize, whereCond, search:[], dataRelation, constraint}`；`displayName` 内部 = `[{path:[{fieldId, entity:{id, appName}}]}]`。**DB `terminal_type` 存数字（1=PC），读面返回枚举名**。组结构 = `udc_refer_config_group`（caption/appId/entityId/type + `ReferConfigGroupDto.terminalTypes:["PC","MOBILE"]`）。删除 `deleteByGroupId` → `content=1`。误打 `CreateOrUpdatePost` 的 `configInfo must not be blank; terminalType must not be null` 是**顶层 ReferConfigDto 的校验**，不是正确路径的报错 |
| G | 清理 | 规则/索引/实体/分组删除 | ✅ DB 双证 0 残留 | 规则删除 `content=**true**`（boolean，非数字）；实体删除级联清字段/索引 |

## 本轮新增错误码与约束（写进 skill 侧）

| 码 | 语义 | 触发 |
|---|---|---|
| `UDC_ENTITY_0001` | name 必须字母开头+字母数字（**禁下划线**） | 规则/实体 name |
| `UDC_INDEX_0003` | `index fields is duplication: Duplicate index-[…], duplicate field-[…]` | 唯一索引字段已存在唯一约束 |
| `UDC_EVENT_0002` | `Create event data error:null` | 事件缺 `eventDataList` |
| `BOOT_1000` | `实体tableName不能为空!` | 更新实体缺 `tableName` |
| `BOOT_1001` | `stereotype must not be blank` / `configInfo must not be blank; terminalType must not be null` / `displayName must not be blank` | 更新缺 stereotype；参照缺字段 |
| `BOOT_3002` | `No enum constant …ObjectTypeEnum.Object` / `…DataTypeCategoryEnum.STRING` / `Failed to deserialize the value of property configInfo to type String` | 枚举值大小写；configInfo 类型 |

## 平台行为发现

1. **唯一约束与唯一索引联动**：字段 `uniqueness=true` → 平台自动生成 `uk_<时间戳>` 唯一索引（`indexSource=ATTRIBUTE_UNIQUE`，不可删/改）；此时再为同字段建 UNIQUE 索引被 `UDC_INDEX_0003` 拒绝。
2. **索引 name 平台改写**：`name` 传入值被忽略，统一 `idx_/uk_ + 时间戳数字`（与图17 `idx_4317890813011251043` 形态一致）。
3. **系统字段 11 个**（`id/tenantId/createTime/updateTime/version/draft/creator/creatorInstitution/creatorDepartment/creatorPost/updater`），组 `attribute_group='系统'`（`attribute_group_id=3149984497173407807`），其中 4 个用**系统变量默认值**：
   - `creator` → `{"type":"SYSTEM_VARIABLE","value":"currentUserId","desc":"登录人员ID","dataType":"BIGINTEGER"}`
   - `creatorInstitution` → `currentInstitutionId`；`creatorDepartment` → `currentOrgId`；`creatorPost` → `currentPostId`
   （与 `/expression/preset/list` 返回的系统变量一一对应）
4. **删除返回类型不统一**：字段/索引/事件/实体 = 数字（影响行数，断言 `>=1`）；**规则 = boolean**；分组 op 返回 0 但 DB 已删（实体级联）。
5. **更新类操作必须带回完整形态**：实体要 `tableName+stereotype+appId`；字段要全量 66 字段（先 GET 再改）。

## 残留（2026-10-12 二轮更新）

- ~~参照（F）~~ → **已全部打穿**（create/update/delete + DB 双证 + 组列表回读，二轮清理后零残留）。**6 大 tab 全部 LIVE PASS。**
- openAPI 读（A5）：op 参数形态未通（DB 侧已确认默认值）。
- 字段组查询（B7a）：3 个 op 名未通（创建已通）。
