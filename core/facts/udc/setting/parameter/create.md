# 设置域 · 参数（Parameter）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> 证据等级：**LIVE PASS**（2026-10-21，接口提交 + DB 回读）
> 探针对象：`zxjParamProbe` / 探针参数 / id=`4078955676278128592`
> 实现：`components/udc/setting/parameter_constraints.py`

## 一、表与接口

落库表：**`ctp_parameter_definition`**
（⚠ `app_id` 是 **varchar**，不是 bigint——其他 UDC 表都是 bigint）

| 动作 | operation | 状态 |
|---|---|---|
| 列表 | `udcCtpParameterDefinitonSearch` | LIVE（抓包确认） |
| 数据类型候选 | `udcDataTypeDataTypesParamGet` | LIVE（抓包确认） |
| 新建 | `udcCtpParameterDefinitonPost` | **LIVE PASS** |
| 更新 | `udcCtpParameterDefinitonUpdatePost` | 存在（同样报「参数显示名称 不能为空」） |

⚠ **`Definiton` 是平台的拼写错误**（少一个 i），必须照抄，写成 `Definition` 会 FieldUndefined。

## 二、body 形态

```json
{
  "appId": "8704025620829192834",
  "appGuid": "2275741415570096882",
  "name": "zxjParamProbe",
  "caption": "探针参数",
  "description": "probe",
  "dataType": "STRING",
  "dataTypeProperties": { "minLength": 0, "maxLength": 100 },
  "paramGroup": "",
  "value": "probeValue",
  "orderNo": 99,
  "type": 0
}
```

## 三、必填与坑

| 缺失/非法 | 报错 |
|---|---|
| caption | `BOOT_1001 参数显示名称 不能为空` |
| `dataTypeProperties` 传 JSON **字符串** | `BOOT_3002 属性dataTypeProperties的值反序列化为LinkedHashMap类型时失败` |

⚠ `dataTypeProperties` **提交时必须是对象**，落库时平台自己序列化成字符串。
我第一版传了 `"{\"minLength\":0,\"maxLength\":100}"`（字符串），被拒。

## 四、落库字段（ctp_parameter_definition 实读）

```
id / tenant_id / create_time / update_time / version / guid
app_id(varchar) / name / caption / description
data_type / data_type_properties / param_group / value / order_no
type / aggregation_app_name / original_id / app_name / is_delete
```

样本（本应用真实数据）：

```
id=3892518804295730308  name=daglcshj   caption=档案管理测试环境
  data_type=STRING  data_type_properties={"minLength":0,"maxLength":100}
  value=" "  order_no=20  type=0  is_delete=0
```

## 五、本应用实测（LIVE）

```
zxjParamProbe / 探针参数 / id=4078955676278128592
  data_type=STRING  value=probeValue  order_no=99  is_delete=1
本 app 参数（is_delete=0）：3 条   已删（is_delete=1）：40 条
```

⚠ **2026-10-21 订正**：旧文写「本 app 参数总数（is_delete=0）：40」是错的。
DB 实测 `SELECT is_delete,COUNT(*) ... GROUP BY is_delete` → `{0: 3, 1: 40}`；
`zxjParamProbe` 本身也已 `is_delete=1`（探针在用完后被逻辑删除）。
活的 3 条是 `fujian` / `zxjApiBaseUrl` / `zxjPageSize`。
⇒ 统计参数数量前一律带 `is_delete=0`，别把已删行当能力存量。

## 六、未验证

| 项 | 状态 | 说明 |
|---|---|---|
| 各 dataType 的 dataTypeProperties 值域 | **UNVERIFIED** | 只验了 STRING；INTEGER/DECIMAL/DATE 等的约束键未逐个测 |
| 参数删除接口 | **UNVERIFIED** | 未探测 |
| paramGroup 分组语义 | **UNVERIFIED** | 样本里都是空串 |
| type 字段语义 | **UNVERIFIED** | 样本全是 0 |
