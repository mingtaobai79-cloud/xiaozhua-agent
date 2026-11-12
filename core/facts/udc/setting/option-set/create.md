# 设置域 · 选项集（Option Set）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> 证据等级：**LIVE PASS**（2026-10-21，接口提交 + DB 回读，全链路三段）
> 探针对象：分组 `zxjOptProbeGroup`(id=-7694596147549924998) /
>           选项集 `ZxjOptProbe`(id=-7445288973993128877) / 2 个选项项
> 实现：`components/udc/setting/option_set_constraints.py`

## 一、选项集 ≠ 枚举（最容易搞错的一条）

| | 枚举 | 选项集 |
|---|---|---|
| 主表 | `ctp_enum` | **`udc_enum`** |
| 分组表 | `ctp_enum_category` | **`udc_enum_category`** |
| 项表 | `ctp_enum_item` | **`udc_enum_item`** |
| 分组建 | `udcEnumCategoryPost` | **`udcUdcEnumCategoryPost`** |
| 本体建 | `udcEnumPost` | **`udcUdcEnumPost`** |
| 项建 | `udcEnumItemPost` | **`udcUdcEnumItemPost`** |
| 批量删 | `udcEnumBatchDeletePost` | **`udcUdcEnumBatchDeletePost`** |
| 列表 | `udcEnumSearchNoPagePost` | **`udcUdcEnumCategorySelectCategoryAndEnumPost`** |

两套表**完全独立，id 不互通**。我把枚举当选项集提交过一次，
页面显示成 `_<appName>_<id>` 异常串（`relationApp` 和 `dataType` 都错）。

## 二、接口清单（全部 GraphQL，路径 `POST /service/udc/graphql?<op>`）

| 动作 | operation | 落库表 | 状态 |
|---|---|---|---|
| 分组列表 | `udcUdcEnumCategorySelectCategoryAndEnumPost` | — | LIVE（content 可为 null） |
| 分组新建 | `udcUdcEnumCategoryPost` | `udc_enum_category` | **LIVE PASS** |
| 选项集新建 | `udcUdcEnumPost` | `udc_enum` | **LIVE PASS** |
| 选项项新建 | `udcUdcEnumItemPost` | `udc_enum_item` | **LIVE PASS** |
| 批量删除 | `udcUdcEnumBatchDeletePost` | 逻辑删除 | LIVE（content=0 语义待查） |

⚠ `udcUdcEnumCategorySearch` / `udcUdcEnumSearchNoPagePost` **不存在**（FieldUndefined）。

⚠ **`udc_enum` 表实测没有 `is_delete` 列**（2026-10-21 逐列核对：
`id/create_time/tenant_id/update_time/version/guid/publish_state/app_id/caption/description/
enable/name/state/owner_code/backup_code/category_id/order_no/is_edit/icon_display/original_id`）。
所以上文「批量删除 = 逻辑删除 `udc_enum.is_delete=1`」**未成立**，批量删真实语义仍是
UNVERIFIED（不排除平台做物理删或走 `state`）。写这类结论前先 `SHOW COLUMNS`，
不要把「别的表有 is_delete」当 UDC 表通例（`udc_page_info` 也没有）。

## 三、必填槽位与错误字典（实测）

### 分组 `udcUdcEnumCategoryPost`

```json
{"appId","appGuid","name":"zxjOptProbeGroup","caption":"探针选项集分组",
 "orderNo":90,"parentId":"0","description":"probe"}
```

| 缺失 | 报错 |
|---|---|
| appId | `BOOT_1001 应用ID 不能为null` |
| caption | `BOOT_1001 分类名称 不能为空` |

### 选项集 `udcUdcEnumPost`

```json
{"appId","appGuid","name":"ZxjOptProbe","caption":"探针选项集",
 "categoryId":"-7694596147549924998","orderNo":10,"description":"probe"}
```

| 缺失/非法 | 报错 |
|---|---|
| caption | `BOOT_1001 选项集名称 不能为空` |
| **name 首字母小写** | `UDC_ENUM_0001 编码只能由首字母大写的数字和字母的组合` |

⚠ **编码必须首字母大写**。`zxjOptProbe` 被拒，`ZxjOptProbe` 通过。
这条与枚举的 `UDC_ENUM_0002`（要求大写+下划线）不是同一套规则。

### 选项项 `udcUdcEnumItemPost`

```json
{"appId","appGuid","enumId":"<选项集 id>","name":"ONE","caption":"选项甲",
 "code":1,"orderNo":1,"enable":true,"description":"probe 1"}
```

| 缺失 | 报错 |
|---|---|
| caption | `BOOT_1001 选项名称 不能为空` ← 报错说"名称"，实际是 **caption** |
| name | （同上，两个都要） |
| code | `BOOT_1001 选项值 不能为null` |

⚠ 三个槽位都不能少，且 **name=编码（英文）、caption=显示名（中文）、code=整数**。
我第一次只传 name+code，被拒。

## 四、本应用实测结果（LIVE）

```
分组    zxjOptProbeGroup    id=-7694596147549924998   udc_enum_category
选项集  ZxjOptProbe         id=-7445288973993128877   udc_enum
        category_id 正确指向分组
选项项  ONE / 选项甲  code=1  order_no=1  enable=1   udc_enum_item
        TWO / 选项乙  code=2  order_no=2  enable=1
```

## 五、与自定义对象字段的关系

选项集作为自定义对象字段时（见 `custom-object/fields.md` §5.3）：

```
本应用选项集   dataType = "<选项集 id 数字串>"
               dataTypeCategory = "ENUM"        ← 第三个枚举值
               relationApp = "<appId 数字串>"
               relationEntity = "<选项集 id>"

BPM 引擎选项集 dataType = "<Java 全类名>"
               dataTypeCategory = "ENUM"
               relationApp = "bpm"
               relationEntity = ""（或残值）
```

## 六、未验证

| 项 | 状态 | 说明 |
|---|---|---|
| 选项集更新接口 | **UNVERIFIED** | 只验了新建，未找 `udcUdcEnumUpdatePost` 类接口 |
| 选项项更新/删除 | **UNVERIFIED** | 同上 |
| 批量删除 content=0 语义 | **UNVERIFIED** | 空 body 返回 `content:0`，不确定是"删 0 条"还是"参数错" |
| 分组删除 | **UNVERIFIED** | 未探测 |
| 页面 tab 的新建按钮定位 | **已记录** | 选项集 tab 必须先选中树节点才出现「新建」；且页面有多层嵌套 tab，`.ant-tabs-tabpane-active` 会同时匹配外层 |
