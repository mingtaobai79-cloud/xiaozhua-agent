# MCP setting 域工具真机验证（第一批）

> 日期：2026-11-08
> 环境：test2，`appId=app9000000000000000001`，`appGuid=appGuid0000000000000001`
> 传输：CDP 9333 页面代发（cookie 不出浏览器）
> 结论：**9 个工具真机通过，3 个卡在参数，发现 2 个真 bug + 5 个 registry 缺口**
> 测试数据：**全部清零**（复查证据见 §5）

## 1. 为什么要真跑

工具是「参数生成器」，只保证 body 形状，不保证平台接受。此前 setting 域 18 个工具里
只有 `option_set_category_body` 真提交过。rule 域第一次真跑就连抓两个 bug
（`type=ENTITY`、`checkSchema` 取错路径），所以「测试绿」不能替代「平台认」。

## 2. 通过（9 个）

| 工具 | mutation / REST | 建成 id | 回读 | 删除 |
|---|---|---|---|---|
| `enum_category_body` | `udcEnumCategoryPost` | 7826212895483268353 | ✅ `udcEnumCategorySearch` 查到 | ✅ `udcEnumCategoryDeletePost` |
| `enum_body` | `udcEnumPost` | 8641119291467649272 | ✅ | ✅ `udcEnumBatchDeletePost` |
| `enum_item_body` | `udcEnumItemPost` | -4478604924672861419 | ✅ | ✅（随 enum 删） |
| `option_set_category_body` | `udcUdcEnumCategoryPost` | 1274020635137434798 | ✅ 树 | ✅ `udcUdcEnumCategoryDeletePost` |
| `attribute_set_body` | REST `/udc/attributeSet` | 8500899177252064545 | — | ✅ `udcAttributeSetDeletePost` |
| `attribute_set_field_body` | `udcEntityAttributePost` | 1980387929430117650 | — | ✅（随字段集删） |
| `parameter_body` | `udcCtpParameterDefinitonPost` | -2680623455858438361 | ✅ 搜到 `zzVfParam` | ✅ `udcCtpParameterDefinitonDeletePost` |
| `qrcode_body` | REST `/udc/qrcode-rule/create` | -3338421010953614845 | — | ✅ `/udc/qrcode-rule/delete` |
| `scalability_option_body` | REST `/udc/scalability-option` | 8037816747274501125 | — | ✅ `/udc/scalability-option/delete` |

## 3. 失败（3 个，2 个是我方法错）

### 3.1 `serial_scheme_body` / `serial_section` —— 参数域未验证

```
传 CONSTANT 段 → SERIALNUMBER_1008  流水段有且只能有一段
传 INCREASE 段 → BOOT_3002  No enum constant
                 SerialTypeEnum.INCREASE
```

两条线索：

1. `SerialTypeEnum` 里**没有 `INCREASE`** —— `serial_section(section_type=...)` 的取值域
   从来没验证过，工具默认值 `CONSTANT` 能过枚举校验但过不了段数校验
2. test2 上**零个流水号方案**，无法反推合法段结构；jar 里只有 `SerialTypeEnum` 的类型引用，
   没有常量表（`docs/audit/artifacts/extension-surface-20261029/batch2/boot-starter-serialnumber.json`
   只到方法签名）

⇒ 待办：反编译 `boot-starter-serialnumber` 的 `SerialTypeEnum` 拿常量，再定 `section_type` 的
合法取值。**不要靠试错** —— 每试一次可能留一条脏数据。

### 3.2 `scalability_field_body` —— BOOT_3000（我的顺序错）

我先删了父 `scalability_option` 再建字段，`option_id` 指向已删对象，必然 3000。
**不是工具问题**，重测时先建父再建子。

## 4. 两个真 bug

### bug #1 `enum_category_body` 缺 app_guid

```python
enum_category_body(app_id, name, *, order_no, parent_id, description)   # 现状
option_set_category_body(app_id, app_guid, name, caption, *, ...)        # 对照
```

建出来的分组 `appGuid = "-1"`（正常应是 `appGuid0000000000000001`）。
`enum_category_body` 没有 `app_guid` 参数，平台只能落 `-1`。

### bug #2 `enum_body` 缺 category_id

```python
enum_body(app_id, caption, name, order_no=100)   # 没有 category
```

产出的 body 里 `categoryId` 恒为 `"0"`，**枚举永远挂不到分组下**。
对照 `option_set_body(app_id, app_guid, name, caption, category_id, ...)` 是有的。

⇒ 这两个说明 `enum_*` 那一套（ctp_enum）比 `option_set_*`（udc_enum）旧，参数没补齐。
补之前先确认 ctp_enum 和 udc_enum 是不是同一张表的两套视图
（`udc.enum.create` 的 registry note 写「落库 ctp_enum（不是 udc_enum）」）。

## 5. registry 缺口（5 个删除接口，都是试出来的）

以下接口**平台有、registry 没登记**，不试出来测试数据根本清不掉：

| 接口 | 入参 | 返回 |
|---|---|---|
| `udcEnumCategoryDeletePost` | `{"id": <id>}` | content 1 |
| `udcAttributeSetDeletePost` | `{"id": <id>}` | content 1 |
| `udcCtpParameterDefinitonDeletePost` | `{"id": <id>}` | content 1 |
| REST `/udc/qrcode-rule/delete` | `{"id": <id>}` | content 1 |
| REST `/udc/scalability-option/delete` | `{"id": <id>}` | content 1 |

另记两个易错点：

- `udcEnumBatchDeletePost` 的 `ids` 必须是 **String 数组**，传 Long 报「数据不存在」
- `/udc/attributeSet/delete`、`/deleteByIds` 返回 **MethodNotAllowed**（nginx 层），
  真接口是 GraphQL 的 `udcAttributeSetDeletePost`

## 6. 清理证据（全量复查）

查的是各域**自己的读接口**，不是 SQL：

| 域 | 接口 | 结果 |
|---|---|---|
| enum 分类 | `udcEnumCategorySearch` | `BOOT_0000`，4920 B，无 `Zz` |
| enum 枚举 | `udcEnumSearchNoPagePost` | `BOOT_0000`，4161 B，无 `Zz` |
| 选项集 | `udcUdcEnumCategorySelectCategoryAndEnumPost` | `BOOT_0000`，2105 B，无 `Zz` |
| 参数 | `udcCtpParameterDefinitonSearch` | `content: []` |
| 流水号 | `udcSerialSchemeSearchPagePost` | `content: []` |
| 二维码 | REST `/udc/qrcode-rule/search` | 无命中 |
| 扩展选项 | REST `select-by-appid/with-detail` | 无命中 |
| 实体规则 | `udcMicroflowSearchEntityRulePost` | `content: []` |

`content: []` 是真空数组（不是查询报错），已逐条看原始响应确认。

## 7. 未验证（28 个）

```
application  5   app_dependency_body / app_dependency_remove_body / app_deploy_body
                 / app_version_list / app_build_info
entity       4   deploy_plan / dto_body / index_body / refer_config_body
setting      8   enum_item_body(已过) / event_body / event_data_body
                 / excel_template_body / excel_template_column
                 / scalability_field_body(重测) / serial_scheme_body / serial_section
flow         7   microflow_* 全套
page         4   list_page_schema / detail_page_schema / custom_page_scaffold / filter_plan_body
expression   2   expression_catalog / expression_filter
```

其中 `microflow_*` 有额外铁律：UI 点「检查」+ 逐节点开抽屉看红字，
后端 checkSchema 绿 ≠ 前端过。
