# 操作契约 · 设置域 / 选项集（Option Set）

> 事实格：`core/facts/udc/setting/option-set/create.md`
> 实现：`components/udc/setting/option_set_constraints.py`
> 脚本：`tools/core/setting/option_set_seed.py`

## ★ 与枚举是两套独立表（最容易搞错）

```
枚举    ctp_enum / ctp_enum_category / ctp_enum_item
选项集  udc_enum / udc_enum_category  / udc_enum_item
```

两套表 **id 不互通**。把枚举 id 当选项集提交，页面会显示 `_<appName>_<id>` 异常串。

## operation 清单

| operation | 方法 | 路径 | 写 | 落库表 | 状态 |
|---|---|---|---|---|---|
| `udc.option_set.category.create` | POST | `graphql?udcUdcEnumCategoryPost` | 是 | `udc_enum_category` | **LIVE PASS** |
| `udc.option_set.create` | POST | `graphql?udcUdcEnumPost` | 是 | `udc_enum` | **LIVE PASS** |
| `udc.option_set.item.create` | POST | `graphql?udcUdcEnumItemPost` | 是 | `udc_enum_item` | **LIVE PASS** |
| `udc.option_set.category_and_enum` | POST | `graphql?udcUdcEnumCategorySelectCategoryAndEnumPost` | 否 | — | LIVE |
| `udc.option_set.batch_delete` | POST | `graphql?udcUdcEnumBatchDeletePost` | 是 | — | UNVERIFIED |

⚠ `udcUdcEnumCategorySearch` / `udcUdcEnumSearchNoPagePost` **不存在**（FieldUndefined）。

## 必填槽位

### 分组 `udcUdcEnumCategoryPost`

```json
{"appId": "<appId>", "appGuid": "<udc_application.guid>",
 "name": "分组编码", "caption": "分组显示名",
 "orderNo": 1, "parentId": "0", "description": ""}
```

| 缺失 | 报错 |
|---|---|
| appId | `BOOT_1001 应用ID 不能为null` |
| caption | `BOOT_1001 分类名称 不能为空` |

### 选项集 `udcUdcEnumPost`

```json
{"appId": "<appId>", "appGuid": "<guid>", "name": "ZxjOptProbe",
 "caption": "选项集显示名", "categoryId": "<分组id>", "orderNo": 10}
```

| 缺失/非法 | 报错 |
|---|---|
| caption | `BOOT_1001 选项集名称 不能为空` |
| **name 首字母小写** | `UDC_ENUM_0001 编码只能由首字母大写的数字和字母的组合` |

⚠ 编码**必须首字母大写**。这条与枚举的 `UDC_ENUM_0002` 不是同一套规则。

### 选项项 `udcUdcEnumItemPost`

```json
{"appId": "<appId>", "appGuid": "<guid>", "enumId": "<选项集id>",
 "name": "ONE", "caption": "选项甲", "code": 1,
 "orderNo": 1, "enable": true}
```

三个槽位缺一不可：**name=编码（英文）/ caption=显示名（中文）/ code=整数**。
缺 caption 报 `BOOT_1001 选项名称 不能为空`（报错文案说"名称"，实际缺 caption）。

## 作为字段默认值（选项集走基类值，不走表达式）

```sql
-- 正确：default_value 存 udc_enum_item.id
SELECT default_value, default_value_caption FROM udc_attribute WHERE name = '<字段>';
```

真实样本（其它应用，DB 实测）：

```
default_value         = 3410469842981068319        ← udc_enum_item.id
default_value_caption = 3410469842981068319        ← 平台回填成 id（不是显示名）
```

⚠ 选项集的 caption 回填成 id 是**平台既有行为**，不是缺陷。
（平台枚举 `ctp_enum` 会正确回填显示名，两者不同。）

多选：`default_value = <id1>,<id2>`，caption 逗号分隔。

## 错误码

| 场景 | 码 |
|---|---|
| 缺 appId | `BOOT_1001 应用ID 不能为null` |
| 缺分组 caption | `BOOT_1001 分类名称 不能为空` |
| 缺选项集 caption | `BOOT_1001 选项集名称 不能为空` |
| 编码首字母小写 | `UDC_ENUM_0001` |
| 缺选项项 caption | `BOOT_1001 选项名称 不能为空` |
| 缺选项项 code | `BOOT_1001 选项值 不能为null` |

## 未验证

```
更新接口（udcUdcEnumUpdatePost 之类）    UNVERIFIED（未探测）
选项项更新/删除                          UNVERIFIED
批量删 content=0 的真实语义               UNVERIFIED
udc_enum 表无 is_delete 列（逐列核对）    → 「逻辑删除」这一说法未成立
```
