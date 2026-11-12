# CTPENUM 字段的枚举归属：平台枚举(ctp_enum) vs 选项集(udc_enum) —— 字节码 + LIVE 实证

> 结论先行：**字段 dataType=CTPENUM（"枚举"）必须关联平台枚举域 `ctp_enum`；
> 我在 S7 用 `POST /udc/udc-enum` 建的是"选项集"域 `udc_enum`，两者是不同 dataType、不同存储域、不同端点组。**
> 把 `udc_enum.id` 塞进 `udc_attribute.relation_entity` ⇒ 一致性检查 **UDC_CE_ENTITY_02104「字段关联枚举不存在」（阻断级）**，构建被卡。
> 证据链：字节码判定规则 + DB 归属对照 + LIVE A/B 对照（改前 02104=1，改后 02104=0）。

## 1. 判定规则（CFR 反编译 udc-biz 5.3.517）

`com.seeyon.udc.detection.task.util.AttributeMatchDetectionUtils`：

```java
private static final String CTP_ENUM_FULL_NAME_PREFIX =
    "com.seeyon.boot.starter.enums.domain.entity.CtpEnum";

if (DataType.CTPENUM.name().equals(entityAttributeMetadataDto.getDataType())) {
    attributeMatchDto.setRelationApp(entityAttributeMetadataDto.getRelationApp());
    String relationEntity = entityAttributeMetadataDto.getRelationEntity();
    if (!relationEntity.startsWith(CTP_ENUM_FULL_NAME_PREFIX)) {
        relationEntity = CTP_ENUM_FULL_NAME_PREFIX + "." + relationEntity;   // ← 自动拼前缀
    }
    attributeMatchDto.setRelationEntity(relationEntity);
}
```

⇒ 检测器把 CTPENUM 的 `relationEntity` 当作**平台枚举实体的主键**，拼成
`com.seeyon.boot.starter.enums.domain.entity.CtpEnum.<值>` 去查。
把"选项集 id"放进去 → 拼出的全名指向不存在的平台枚举 → **02104**。

`EntityCategoryEnum` / `CtpEnumType` / `CtpEnumDto` / `CtpEnumItemDto` 同在该类的引用集里（import 段实证）。

## 2. DB 归属对照（udc_test2，LIVE）

| | 我们的字段 | 本应用正常枚举字段 |
|---|---|---|
| 字段 | `expEnum` (data_type=CTPENUM) | `syncMode` / `enumType` / `joinType` / `fieldType` / `javaType` / `referenceType` |
| `relation_entity` | `3934748939202274853` | 如 `343286139204944935` |
| 该 id 所在表 | **`udc_enum`**（选项集） | **`ctp_enum`**（平台枚举） |
| 该 id 的行 | `name=XzhEnum953322, caption=小爪实验枚举953322` | `code=SyncMode, name={"zh_CN":"同步模式"}` |
| 结果 | **02104** | 0 检错 |

同一实例两域并存、互不通用：

| 域 | 表 | 本应用行数 |
|---|---|---|
| 选项集 | `udc_enum` / `udc_enum_item` / `udc_enum_category` | 1 / 2 / 1（我 S7 建的） |
| 平台枚举 | **`ctp_enum`** / `ctp_enum_item` / `ctp_enum_category` | **371 / — / —** |

`ctp_enum` 关键列：`id, code(varchar75,MUL), name(JSON 形如 {"zh_CN":"同步模式"}), category_id, enable, enum_type, app_id, is_preset, is_delete, root_enum_id, enum_level, data_status`。
（`SELECT COUNT(*) FROM ctp_enum` = **1680**，全租户。）

## 3. LIVE A/B（决定性）

```
A. expEnum.relation_entity = udc_enum.id (3934748939202274853)
   → POST /service/udc/application/do/detection → search/detection
   → UDC_CE_ENTITY_02104 × 1        「字段关联枚举不存在」阻断

B. expEnum.relation_entity = ctp_enum.id (343286139204944935, code=SyncMode)
   → 同上重算
   → UDC_CE_ENTITY_02104 × 0        ✅ 阻断消除（总量 17 行，其中 9 ERROR/7 WARN 结构不变，仅此条消失）
```

A/B 仅改 `relation_entity`(+name/code/app 四列) 一处，其余不变 ⇒ 因果唯一。

> 注：B 用 SyncMode 只为证伪，语义上应指向本应用自建的平台枚举；因端点被网络阻塞，暂留 B 态并登记。

## 4. 端点归属（★ 我的契约清单长期缺失这一域）

| 域 | 端点 | 来源 | 是否在 `udc-web` 契约(674) |
|---|---|---|---|
| 平台枚举 | `EnumController` base=`enum`：`create` / `update` / `batch-delete` / `{id}` / `copy` / `search` / `search-no-page` / `search-by-code/{code}` / `search-parent-by-code` / `calc-order-num` / `upgrade-enums` | **`boot-starter-enums-5.3.308.jar`** | ❌ **不在**（所以从未被登记） |
| 平台枚举分类 | `EnumCategoryController` base=`enum-category`：`create` / `update` / `delete` / `{id}` / `search` / `search-category-and-enum` | 同上 | ❌ 不在 |
| 平台枚举项 | `EnumItemController` base=`enum-item`：`create`/`update`/`delete`/`search`/`search-by-enum-code/{enumCode}`/`search-by-enumId/{enumId}` | 同上 | ❌ 不在 |
| 选项集 | `UdcEnumController` base=`udc/udc-enum` 等 | `udc-web-5.3.517.jar` | ✅ 在 |
| 平台枚举**读** | `POST /udc/meta-data/select-ctp-enum-by-app` / `select-ctp-enum-by-app1` / `select-ctp-enum-item` | udc-web `MetaDataController` | ✅ 在（只读） |

- 网关前缀：udc 业务走 `/service/udc/...`；`boot-starter-enums` 是平台级组件，其前缀待网络恢复后实测（候选 `/service/enum*`、`/service/udc/enum*`）。
- 前端字段类型清单已把两者分开：`{lable:"选项集", val:Enum}` / `{lable:"枚举", val:CtpEnum}`（`SETTINGS-TABS-CALLCHAIN.md` §3.2 既有事实）。

## 5. 我错在哪（如实记）

1. S7 写链表把 `POST /udc/udc-enum` 记为"建枚举 ✅"，实际建的是**选项集**，且该错误进了 PROGRESS/域矩阵，被当成了"枚举域已打通"。
2. 域矩阵里"设置域 88%、枚举 ✅"的结论**没有一条 LIVE 的 CTPENUM 字段端到端验证**支撑——只有建对象成功。
3. 契约面从 udc-web 单构件出发，**漏了 boot-starter-enums 整个域**，导致"平台枚举怎么建"长期为空白且未被发现。

## 6. 待办（网络恢复后）

1. 实测 `boot-starter-enums` 的 create 端点 → 替本应用建一个真正的平台枚举（如 `XzhCtpEnum`）。
2. `expEnum.relation_entity` 指向它 → 重算 → 02104 应保持 0。
3. 把 `boot-starter-enums` 三控制器纳入契约清单与域矩阵（设置域口径重算）。
4. 复验：`udc_enum`（选项集）该由哪个 dataType(`ENUM`) 承载、哪个页面入口建。
