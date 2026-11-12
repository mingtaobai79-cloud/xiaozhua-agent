# 设置域 · 默认值赋值链（2026-10-22 实测）

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> 本文只讲**规则**。具体 appId / 字段集 id / 枚举项 id 只在 R-E8 与 `tools/` 脚本参数里。
> 实现：`components/udc/setting/attribute_set_constraints.py`
> 契约：`docs/operation-contracts/udc/setting/attribute-set-contracts.md`

## 零、这一节存在的理由

2026-10-22 之前，本仓对「字段集默认值」的记载是**错的**，并且错法很隐蔽：

```
旧说法：客户端只写 expressionDesignData + calculate（计算值路径）
实况：  字段集页面只有「默认值」一个入口，没有计算值入口
后果：  DB 有值、接口 BOOT_0000、页面全空 —— 四层里只有前两层过了
```

根因是**拿错链**：`ATTRIBUTE_EXPRESSION_PAIRS` 早就并列声明了两套列，
我没有 grep 仓内约束模块，直接挑了「计算值」那套。

⇒ **写面关键字一出现，先 grep `components/udc/*constraints*.py`，再动手。**

## 一、两条值链互斥（先定链，再写值）

```
链 A  基类值      udc_attribute.default_value / default_value_caption
                  + defaultValueIsChange
                  ← 枚举 / 选项集 / 布尔 / 数字 等「一个具体值」
                  ← 前端从这里直接取值，不解析表达式

链 B  表达式      udc_attribute.default_value_expr_design
                  + default_value_expr_runtime      （★ 两列必须成对写）
                  + defaultValueIsChange=false
                  ← 需要计算/引用出来的值
                  ← 前端读 design 渲染文本、读 runtime 执行
```

**判据**：`BOOT_0000` 不区分这两条链，写哪条都成功。
**唯一可靠的判据是回读哪一列为空**：

```sql
SELECT name, data_type,
       default_value,                    -- 链 A
       default_value_caption,            -- 链 A 显示名（服务端回填）
       default_value_expr_design,        -- 链 B design
       default_value_expr_runtime        -- 链 B runtime
FROM udc_attribute WHERE source_id = <字段集id>;
```

⚠ **链 B 的 runtime 不许置空。** 早期脚本写 `runtime=""`，结果 design 有值、
页面空白——前端拿不到 `executableExpr`。两者必须来自同一次 `transform` 返回值。

## 二、`resultTypeInfo` 必须等于字段 dataType（硬约束）

```
FORMULA_6901   计算结果为: 文本 类型, 无法赋值给: 长整数 类型
                  ← textToLong 参数给成 INTEGER
                  ← CTPENUM 默认值给成文本
```

实测结论：

| 字段 dataType | 默认值表达式 resultTypeInfo |
|---|---|
| STRING / MULTILINESTRING / ATTACHMENT / DOCUMENTNUMBER / OPINION / CONTENT / Serial | `STRING` |
| INTEGER | `INTEGER` |
| BIGINTEGER | `BIGINTEGER` |
| DECIMAL / CURRENCY | `DECIMAL` |
| DATE / TIME / DATETIME | `DATE` / `TIME` / `DATETIME` |
| BOOLEAN | `BOOLEAN` |
| **CTPENUM** | **`CTPENUM`，且 token 结果必须是长整数** |
| ENTITY | `ENTITY`，且 token 结果必须是长整数 |
| ENUM（选项集） | 走链 A，不用表达式 |

## 三、表达式里不许放组件（用户明确要求）

```
❌ {"type":"CONSTANT","value":"notStarted",
    "controlData":{"controlType":"ENUM",
                   "controlProperties":"{\"type\":\"CTP\",...}"}}
   → 前端渲染成「可下拉的枚举组件」
   → 报 下拉组件undefined: undefined的值为【processing】,数据格式不对
   → 表达式区的正确内容只有：函数 / 系统变量 / 参数

✅ 只用 FUNCTION / SYSTEM / VARIABLE / CONSTANT（纯文本或数字）
```

**枚举项要走链 A 的 `default_value`（存枚举项 id），不是塞进表达式。**

### 可用的"文本 → 基类值"函数（`explain.example.argTypes` 实拉）

| 目标类型 | 函数 | argTypes | 备注 |
|---|---|---|---|
| 长整数 | `textToLong` | `['文本']` | **参数必须真是文本**；传 INTEGER 报 FORMULA_6158 |
| 整数 | `textToInt` | `['文本']` | 同上 |
| 小数 | `textToDecimal` | `['文本']` | 同上 |
| 长整数（生成） | `idGenerate` | 无参 | 「生成长整数类型的ID标识」，ENTITY 默认值用它 |
| 文本（32位） | `uniqueMark` | 无参 | 唯一标识 |

**典型合法链**（实测 LIVE PASS）：

```
CTPENUM 默认值 = textToLong(substring(应用参数.xxx, 0, 18))
                 → 文本参数先截取，再转长整数 = 枚举项 id

ENTITY  默认值 = idGenerate()
                 → 长整数 id，不引用文本参数
```

## 四、枚举 / 选项集的绑定槽位（缺一个页面就坏）

```
relation_app            必填   ← 缺了前端显示 "undefined~<枚举id>"
relation_entity         必填   枚举 / 选项集 id
relation_entity_name    必填   显示名
relation_code           CTPENUM 才有（平台枚举 code）
relation_entity_category  ENTITY / EXT / EXT_GLOBAL / THIRD / COMPONENT_ENTITY / BASIC_DATA
                         （EntityCategoryEnum 六值；枚举/选项集用 ENTITY）
```

⚠ **`EntityCategoryEnum` 没有 CTPENUM 这个值。** 传 `"CTPENUM"` 报
`BOOT_3002 No enum constant`。枚举字段填 `ENTITY`（落库显示为字符串 `ENTITY`）。

⚠ **字段集的 ENTITY 槽位用数字 id，不是全类名**：

```
实体属性（source_type=2/0）  relation_entity = com.seeyon.<app>.domain.entity.<Name>
字段集（source_type=1）      relation_entity = <udc_entity.id 数字串>
```

两种规则**相反**，照实体属性的写法配字段集会报 `UDC_DATATYPE_0014`。

## 五、Serial 字段：`serialNumberGuid` 填 guid，不是 id

```
ctp_serial_scheme.id    = -1087839647902612473
ctp_serial_scheme.guid  =  2126837692365228527    ← 这个才是要填的

udc_attribute.serial_number_guid = <scheme.guid>
```

填 id 报 `UDC_ATTRIBUTE_SET_903 字段绑定的流水号规则不存在`。

## 六、枚举项落库的两个坑

### 6.1 `appGuid` 缺了页面查不到

`ctp_enum_item` 必填 `appGuid`（取自 `udc_application.guid`，不是 appId）。
缺了平台落库成 `app_guid = -1`，**枚举管理页面查不到这些项**，
但 DB 里明明有、`BOOT_0000` 也返回成功。

构造器 `build_enum_item_body()` 必须有 `app_guid` 参数（2026-10-22 补）。

### 6.2 删除接口的成功码不可信

```
udcEnumItemDeletePost -> BOOT_0000 SUCCESS
回读 ctp_enum_item     -> 该 id 仍在（is_delete=0）
```

⇒ **删除后必须回读。** 与库内已有纪律一致（自定义对象删除同病）。

## 七、闸门：check 必须读 `data.content === true`

```
POST /service/udc/expression/check
→ {"code":"BOOT_0000","data":{"content":true}}      ← 通过
→ {"code":"BOOT_0000","data":{"content":false}}     ← 不通过（仍是 200/BOOT_0000！）
→ {"code":"FORMULA_6901", ...}                      ← 类型不匹配
→ {"code":"FORMULA_6158", ...}                      ← 参数类型不匹配
→ {"code":"BOOT_1000", ...}                         ← 业务拒绝（如"参数只能是单选枚举常量"）
```

**只看 `code == BOOT_0000` 会把 false 当通过。**
脚本里必须是 `code == "BOOT_0000" and data.content is True`。

**顺序铁律**：

```
组装 token → check（通过才继续）→ transform → 落库 → DB 回读
任何一步失败即报错停下，不兜底、不静默跳过
```

⚠ 但 `check` 只验**语法与类型**，不验「值语义是否匹配字段业务含义」
（例如实体字段塞文本参数，check 会过，但那是错的值）。业务语义要人判断。

## 八、R-E8 Evidence

```
证据  本机 test2 实例 DB 直读（udc_test2.udc_attribute）
      指定字段集 source_id 下去查 default_value / default_value_expr_*
      以及 udc_test2.ctp_enum_item / udc_enum_item 的 app_guid

复现  tools/core/setting/attribute_default_expr_build.py --app-id <id> --set-name <name>
      tools/core/setting/attribute_function_matrix.py  （函数维度）
      页面：设置 → 字段集 → 选字段 → 默认值旁的 + → 高级模式

校验  ① udc_attribute 回读：链 A 看 default_value 非空；
                          链 B 看 default_value_expr_design 与 _runtime 都非空
      ② check 接口 data.content === true
      ③ 页面默认值框显示 expressionTranslation 文本（不是空、不是下拉组件）

反编译  AttributeService.checkExpressionPattern:1593-1607（两套列各自校验）
        ControlData.java:40-61（枚举常量判定）
        ExpressionCommonUtil.getCtpEnumUniqueFullName:533-539（appName@enumCode）
        EntityCategoryEnum（javap 六值）
```

## 九、R-E9 Verified

| 项 | 状态 | 说明 |
|---|---|---|
| 两套链互斥（链 A / 链 B） | **LIVE PASS** | DB 回读两列各自非空 |
| `resultTypeInfo` = 字段 dataType | **LIVE PASS** | 17/17 字段回读匹配 |
| 表达式不含 controlData 组件 | **LIVE PASS** | `"controlData" in design` == False |
| `textToLong(substring(...))` 链 | **LIVE PASS** | CTPENUM 默认值 |
| `idGenerate()` 用于 ENTITY | **LIVE PASS** | resultType=ENTITY |
| 枚举绑定 `relation_app` 必填 | **LIVE PASS** | 缺则前端 `undefined~<id>` |
| 字段集 ENTITY 用数字 id | **LIVE PASS** | 全类名报 UDC_DATATYPE_0014 |
| Serial 用 guid | **LIVE PASS** | 用 id 报 UDC_ATTRIBUTE_SET_903 |
| 枚举项 `appGuid` 必填 | **LIVE PASS** | 缺则 `app_guid=-1`、页面查不到 |
| 枚举项删除需回读 | **LIVE PASS（负结果）** | `BOOT_0000` 但未真删 |
| check 需读 `data.content` | **LIVE PASS** | false 时 code 仍 BOOT_0000 |
| 页面渲染（18 字段逐个点开） | **UNVERIFIED** | CDP 点击不稳，未逐项确认 |
| 选项集 caption 回填成 id | **LIVE（平台行为）** | 真实样本同现象，非缺陷 |

## 十、已知未做 / 待验

```
页面渲染层        UNVERIFIED —— 18 个字段的默认值框逐个点开确认（本轮的缺口）
选项集 vs 枚举    选项集 caption 存 id，是否影响页面显示未验
多选默认值        逗号分隔多 id 的形态仅从真实样本推断，未实写
EntityCategoryEnum 六值的其余五值适用场景未摸
```
