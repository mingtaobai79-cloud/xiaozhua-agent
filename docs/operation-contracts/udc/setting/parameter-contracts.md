# 操作契约 · 设置域 / 参数（Parameter）

> 事实格：`core/facts/udc/setting/parameter/create.md`
> 实现：`components/udc/setting/parameter_constraints.py`
> 脚本：`tools/core/setting/parameter_seed.py`

## 落库表

`ctp_parameter_definition`

⚠ **`app_id` 是 varchar，不是 bigint**（其他 UDC 表都是 bigint）。

## operation 清单

| operation | 方法 | 路径 | 写 | 状态 |
|---|---|---|---|---|
| `udc.parameter.create` | POST | `graphql?udcCtpParameterDefinitonPost` | 是 | **LIVE PASS** |
| `udc.parameter.update` | POST | `graphql?udcCtpParameterDefinitonUpdatePost` | 是 | LIVE |
| `udc.parameter.search` | POST | `graphql?udcCtpParameterDefinitonSearch` | 否 | LIVE |
| 数据类型候选 | POST | `graphql?udcDataTypeDataTypesParamGet` | 否 | LIVE |

## ⚠ `Definiton` 少一个 i —— 平台拼写错误

```
✅ udcCtpParameterDefinitonPost
❌ udcCtpParameterDefinitionPost      → FieldUndefined
```

必须照抄平台的错误拼写。

## body 形态

```json
{
  "appId": "<appId>",
  "appGuid": "<udc_application.guid>",
  "name": "paramCode",
  "caption": "参数显示名",
  "description": "",
  "dataType": "STRING",
  "dataTypeProperties": { "minLength": 0, "maxLength": 100 },
  "paramGroup": "",
  "value": "paramValue",
  "orderNo": 10,
  "type": 0
}
```

## 必填与坑

| 缺失/非法 | 报错 |
|---|---|
| caption | `BOOT_1001 参数显示名称 不能为空` |
| `dataTypeProperties` 传 JSON **字符串** | `BOOT_3002 属性dataTypeProperties的值反序列化为LinkedHashMap类型时失败` |

⚠ **`dataTypeProperties` 提交时必须是对象**，落库时平台自己序列化成字符串。

## 作为字段默认值（走表达式链，参数是可引用变量）

参数会出现在 `expression/schema` 的返回里，可直接当 `VARIABLE` token 引用：

```json
{
  "type": "VARIABLE",
  "value": "__SYSTEM_PARAMS.<参数name>",
  "desc": "应用参数.<参数 caption>"
}
```

`expression/schema` 请求：

```json
{"appId": "<appId>", "extension": "", "ids": [], "idsStr": [],
 "idsTuple": [], "paramType": "CONFIG_PARAM"}
```

返回的每条含 `uniformityParams.paramId`（长整数），`transform` 时用它生成
`getSystemParameter('<paramId>')` 的 runtime。

## 落库字段

```
id / tenant_id / create_time / update_time / version / guid
app_id(varchar) / name / caption / description
data_type / data_type_properties / param_group / value / order_no
type / aggregation_app_name / original_id / app_name / is_delete
```

## 统计口径

⚠ **统计参数数量必须带 `is_delete=0`**。
实测某应用 `is_delete=0` 只有 3 条、`is_delete=1` 有 40 条——
把已删行当存量会误判能力规模。

## 错误码

| 场景 | 码 |
|---|---|
| 缺 caption | `BOOT_1001 参数显示名称 不能为空` |
| dataTypeProperties 传字符串 | `BOOT_3002 反序列化为LinkedHashMap类型时失败` |
| operation 名拼错 Definition | FieldUndefined |

## 未验证

```
删除接口                                  UNVERIFIED（未探测）
paramGroup 分组语义                        UNVERIFIED（样本里都是空串）
type 字段语义                              UNVERIFIED（样本全是 0）
各 dataType 的 dataTypeProperties 值域      UNVERIFIED（只验了 STRING/INTEGER）
```
