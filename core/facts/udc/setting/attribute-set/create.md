# 设置域 · 字段集（Attribute Set）

> 版本：`udc-web-5.3.517`
> 证据等级：**LIVE PASS**（字段集壳 + 字段写入全打通）
> 实现：`components/udc/setting/attribute_set_constraints.py`

## 零、最大发现：父子两级用**两种协议**

```
父（字段集本身）  REST     /service/udc/attributeSet        ← 驼峰
父（分组）        REST     /service/udc/attribute-group     ← 连字符
子（字段）        GraphQL  udcEntityAttributePost           ← ★ 不是 REST
```

我最初以为字段也走 REST `attributeSet/update`（因为 DTO 里有 `attributes` 字段），
**4 种变体全部静默失败**：回 `BOOT_0000` 但 `udc_attribute` 零写入。

真相是从页面真实操作抓包得到的 —— 页面点「确定」时发的是
`/service/udc/graphql?udcEntityAttributePost`。

**教训**：DTO 里有某个字段 ≠ 该类通过它写入。父子两级很可能分属两种协议。

## R-E1 Capability

字段集 = 一组可复用的字段定义，供微流程出参/入参、页面规则等处引用。

```
一个字段集  →  udc_attribute_set 一行
它的字段    →  udc_attribute    多行（entity_id = 字段集 id，source_type=1）
```

支持：建字段集、加字段、读字段、读分组、删。

## R-E2 Version / 协议

```
父 REST（驼峰）
POST   /service/udc/attributeSet                       新建 / 修改（@RequestBody）
POST   /service/udc/attributeSet/update
POST   /service/udc/attributeSet/delete                删除（@MultiRequestBody Long id）
POST   /service/udc/attributeSet/batch-delete
GET    /service/udc/attributeSet/{id}
POST   /service/udc/attributeSet/search-list
POST   /service/udc/attributeSet/select-by-appid
POST   /service/udc/attributeSet/search/term
POST   /service/udc/attributeSet/select-attribute-list 读字段 @MultiRequestBody

父 REST（连字符）
POST   /service/udc/attribute-group/operate-batch      分组整表（要求字段已存在）
GET    /service/udc/attribute-group/{entityId}         读分组（含 attributeDtoList）

子 GraphQL ★
       udcEntityAttributePost                          加字段
```

⚠ 写 `/udc/attribute-set` 会拿到 nginx 403（路径不存在被 ingress 拒）。

## R-E3 Input

### AttributeSetDto（REST 父级）

```java
Long id              // @NotNull(groups=Update)
Long appId           // @NotNull
String name          // @NotBlank @Length(max=30)  编码
String caption       // @NotBlank @Length(max=50)  显示名
String description
List<AttributeDto> attributes   // ★ 本接口不消费
AttributeSetSourceTypeEnum sourceType   // @NotNull：UDC(1)/ISV(2)/APP(3)
int orderNo
```

### 字段 body（GraphQL `udcEntityAttributePost`）

页面实际发出的完整 body（逐字）：

```json
{
  "0": "1",
  "caption": "验收字段集U",
  "name": "yanshouziduanjiU",
  "dataType": "STRING",
  "notNull": false,
  "searchable": false,
  "defaultValue": "",
  "uniqueness": false,
  "minLength": 0,
  "maxLength": 50,
  "auditLog": false,
  "attributeGroup": "",
  "defaultValueSystemVariable": "",
  "defaultValueExpressionDesignData": "",
  "defaultValueExpressionRuntimeData": "",
  "defaultValueIsChange": true,
  "defaultValueCaption": "",
  "calculate": "NORMAL",
  "expressionDesignData": "",
  "expressionRuntimeData": "",
  "sourceType": "ATTRIBUTESET",
  "entityId": "<字段集 id>",
  "sourceId": "<字段集 id>",
  "appId": "<appId>",
  "description": "",
  "widgetConfig": "{\"pc\":\"Input\",\"mobile\":\"Input\",\"list\":true,\"detail\":true,\"quickSearch\":true}"
}
```

⚠ `"0"` 是排序占位，**键名就是字符串 "0"**，值是字符串 `"1"`。
⚠ `widgetConfig` 是 **JSON 字符串**，不是对象。

## R-E4 Required

| 缺失/非法 | 报错 |
|---|---|
| appId | `BOOT_1001` 字段集所属应用Id 不能为null |
| caption | `BOOT_1001` 字段集显示名称 不能为空 |
| sourceType | `BOOT_1001`（update 时必填） |
| 字段 `entityId` | `BOOT_1001` 实体主键ID 不能为null |
| 分组 caption（operate-batch） | `BOOT_1001` 分组名称 不能为空 |
| 读字段传 `id` | `UDC_ENTITY_0022` 字段集不存在 |
| 页面名称/编码留空点确定 | 前端红字「请输入名称 / 请输入编码」，**不发请求** |

## R-E5 Execution

### 1) 建字段集壳（REST）

```
POST /service/udc/attributeSet
{ "appId": <appId>, "name": "zxjFieldSetA", "caption": "验收字段集A",
  "sourceType": "APP", "attributes": [] }
→ BOOT_0000, data.content = <字段集 id>
```

### 2) 加字段（GraphQL）★

```
POST /service/udc/graphql?udcEntityAttributePost
mutation graphqlLoader ($params0: udcEntityAttributePostInputBody) {
  data0: udcEntityAttributePost(body: $params0) { code data { content } message status }
}
variables.params0 = <上面 R-E3 的字段 body>
→ BOOT_0000, data.content = <字段 id>
```

### 3) 读字段（REST）

```
POST /service/udc/attributeSet/select-attribute-list
{ "attributeSetId": "<字段集 id>" }          ← 键名不是 id
→ data.content = [AttributeDto, ...]
```

### 4) 读分组（REST GET）

```
GET /service/udc/attribute-group/{entityId}
→ [{ id:"1", virtual:true, caption:null, attributeDtoList:[...] }]
```

## R-E6 Side Effects

```
udc_attribute_set     字段集主表
udc_attribute         字段（entity_id = 字段集 id，source_type=1）
udc_attribute_group   字段分组（字段集只有一个虚拟分组）
```

## R-E7 Constraints

- `name` ≤ 30、（字段）`caption` ≤ 50
- `sourceType`：`APP`/`UDC`/`ISV`（或 3/1/2），不能缺
- 字段 `name` 是**编码**，不能含中文 —— 页面会自动转拼音
  （`验收字段集U` → `yanshouziduanjiU`）
- 字段 `entityId` = `sourceId` = 字段集 id
- `widgetConfig` 必须是 JSON 字符串
- 字段集路径驼峰 `attributeSet`，分组路径连字符 `attribute-group`

## R-E8 Evidence

```
反编译 /d/repo/CHIT/com/seeyon/udc-web/5.3.517/udc-web-5.3.517.jar
       → AttributeSetController / AttributeGroupController
反编译 /d/repo/CHIT/com/seeyon/udc-plugin-api/5.3.517/udc-plugin-api-5.3.517.jar
       → AttributeSetDto
反编译 /d/repo/CHIT/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar
       → AttributeDto / AttributeSetSourceTypeEnum(UDC=1,ISV=2,APP=3)

页面抓包 2026-10-21（关键突破）
       在字段集界面「右侧名称框填 验收字段集U → 点确定」
       → 页面发送 /service/udc/graphql?udcEntityAttributePost
       → body 见 R-E3（完整逐字）
       → 读回 select-attribute-list 字段数 1 → 2

接口复现 用同一 op 建 probeFieldTwo 到另一字段集
       → BOOT_0000 content="-4695616866915756448"

DB 回读 udc_attribute:
        cslccxcc1          entity_id=-4221824384234270285 source_type=1
        yanshouziduanjiU   entity_id=-4221824384234270285 source_type=1
        probeFieldTwo      entity_id=1696005332877934176 source_type=1
```

## R-E9 Verified

| 项 | 状态 | 证据 |
|---|---|---|
| 建字段集壳（REST） | **LIVE PASS** | id=-1975604686864273565 / 1696005332877934176，DB 回读正确 |
| **加字段（GraphQL `udcEntityAttributePost`）** | **LIVE PASS** | 页面建 `yanshouziduanjiU` + 接口复现 `probeFieldTwo`，均落库 |
| `select-attribute-list` 读字段 | **LIVE PASS** | 键名 `attributeSetId` |
| `attribute-group/{entityId}` 读分组 | **LIVE PASS** | 虚拟分组 id="1" |
| `delete` | **UNVERIFIED** | 端点存在，未实测 |
| `search/term` / `search-list` | **UNVERIFIED** | 端点存在 |
| `attribute-group/operate-batch` | **UNVERIFIED** | 要求字段已存在（BOOT_1000），改字段场景未测 |

## 已推翻的旧结论（留档，别再走）

```
① create 带 attributes（entityId 空）      → BOOT_1001 实体主键ID 不能为null
② create 自带 id + 字段 entityId 指向它    → BOOT_0000，字段读回 0（静默忽略）
③ 先建壳再 update 带 attributes            → BOOT_0000 content=1，字段读回 0
④ update 带 sourceType=APP/3/缺省          → 0000 或 1001，字段始终 0
```

以上四条都试过，结论：**REST 父级接口不处理子集合**。真正入口是 GraphQL。

## 待删除清单

| 对象 | 判定依据 | 处置 | 状态 |
|---|---|---|---|
| `zxjFieldSetA`（id=-1975604686864273565） | 探针壳 | 删 | PENDING |
| `zxjFieldSetF`（id=-7777000011111222222） | 探针壳 | 删 | PENDING |

保留（有字段，可作样本）：
```
测试流程查询出参  id=-4221824384234270285   字段 cslccxcc1 + yanshouziduanjiU
验收字段集D       id=1696005332877934176   字段 probeFieldTwo
```

## 可用构造器

```python
from components.udc.setting.attribute_set_constraints import (
    build_attribute_set_body, build_attribute_field_body,
    build_read_attributes_body,
    validate_attribute_set_body, validate_attribute_field_body)

# 1) 壳（REST）
body = build_attribute_set_body(app_id, name="zxjFieldSetA", caption="验收字段集A")
errs = validate_attribute_set_body(body)

# 2) 字段（GraphQL udcEntityAttributePost）
fbody = build_attribute_field_body(app_id, set_id, name="probeA", caption="探针A")
ferrs = validate_attribute_field_body(fbody, set_id=set_id)

# 3) 读
q = build_read_attributes_body(set_id)      # {"attributeSetId": ...}
```

## 十一、18 种字段类型 × 能力矩阵（2026-10-21 全量实测）

### 11.1 类型清单（`udcDataTypeDataTypesByAppIdAppGet` 实拉，18 种）

| dataType | 中文 | custom | base | 支持的能力（enable*） |
|---|---|---|---|---|
| `STRING` | 文本 | — | — | Calculable/Index/Required/Sensitive/Encryption/SensitiveWordCheck/Log/DefaultValue/LengthRange/Unique/Pattern/Search/I18n |
| `MULTILINESTRING` | 多行文本 | — | — | Calculable/Required/SensitiveWordCheck/Log/DefaultValue/LengthRange/Search/I18n |
| `INTEGER` | 整数 | — | — | Calculable/Required/Log/DefaultValue/MaxAndMin/Unique/Search |
| `BIGINTEGER` | 长整数 | — | — | +Index |
| `DECIMAL` | 小数 | — | — | +DecimalDigits |
| `CURRENCY` | 货币 | — | — | 同 DECIMAL |
| `DATE` | 日期 | — | — | Calculable/Index/Required/Log/DefaultValue/MaxAndMin/Unique/Search |
| `TIME` | 时间 | — | — | 同 DATE |
| `DATETIME` | 日期时间 | — | — | 同 DATE |
| `BOOLEAN` | 布尔 | — | — | Calculable/Index/Log/DefaultValue/Unique |
| `ENUM` | 选项集 | — | — | Index/Required/Log/DefaultValue/MultiSelect/Unique/Search |
| `CTPENUM` | 枚举 | — | — | 同上 |
| `ATTACHMENT` | 附件 | — | — | Required/Log/MultiSelect/Search |
| `ENTITY` | 实体 | — | — | Index/Required/Log/DefaultValue/MultiSelect/Unique/Search |
| `DOCUMENTNUMBER` | 文号 | ✔ | STRING | Index/Required/SensitiveWordCheck/Log/LengthRange/Search/I18n |
| `Serial` | 流水号 | ✔ | STRING | Calculable/Index/Required/SensitiveWordCheck/Log/LengthRange/Unique/Search |
| `OPINION` | 意见 | ✔ | MULTILINESTRING | Calculable/Required/SensitiveWordCheck/Log/LengthRange/Search |
| `CONTENT` | 正文 | ✔ | STRING | Calculable/Index/Required/SensitiveWordCheck/Log/LengthRange/Search |

### 11.2 全量实测结果：18/18 通过

```
1  STRING           ✅   2  MULTILINESTRING  ✅   3  INTEGER      ✅
4  BIGINTEGER       ✅   5  DECIMAL          ✅   6  CURRENCY     ✅
7  DATE             ✅   8  TIME             ✅   9  DATETIME     ✅
10 BOOLEAN          ✅   11 ENUM             ✅   12 CTPENUM      ✅
13 ATTACHMENT       ✅   14 ENTITY           ✅   15 DOCUMENTNUMBER ✅
16 Serial           ✅   17 OPINION          ✅   18 CONTENT      ✅
```

字段集 `zxjTypeFull`（id=-2183969222955947047），19 个字段全部 DB 回读正确。

### 11.3 各类型的额外必填（踩过的坑）

| 类型 | 额外必填 | 错误码 |
|---|---|---|
| `CTPENUM` | `relationEntity`=枚举id、`relationApp`=appId、`relationType=Many2OneAssociation` | `UDC_DATATYPE_0015` 关联枚举不存在 |
| `ENUM` | 同上，指向 `udc_enum` 的 id | `BOOT_3000` |
| `ENTITY` | `relationEntity`=实体全类名、`relationApp`=应用名、`relationEntityCategory=ENTITY` | `UDC_DATATYPE_0017` 关联实体不存在 |
| `Serial` | `serialNumberName` + `serialNumberCode` + `serialNumberGuid` | `UDC_ATTR_0019` 必须指定流水号规则 |
| `DECIMAL` / `CURRENCY` | **`maxLength`（总精度）+ `decimalDigits`** | `UDC_DATATYPE_0006` 最大值取值太大，允许的最大值为38 |

⚠ **DECIMAL 的精度靠 `maxLength` 表达，不是 `maxValue`**：
真实样本 `max_length` 是 20/22/24，`decimal_digits` 是 2/4。
传 `maxValue` 会被平台当成精度去校验（报「最大值取值太大，允许的最大值为38」）。
正确写法：`{"decimalDigits": 3, "maxLength": 20}`。

### 11.4 字段编码规则（`UDC_ENTITY_0026`）

```
只能字母 / 数字 / 下划线
必须以字母开头          ← tm01_string 会被拒（数字开头）
不能以下划线结尾
不能含中文              ← 页面会自动转拼音，如 验收字段集U → yanshouziduanjiU
```

## 十二、字段级配置项全量实测（20/20 通过）

用户点名的项全部验过：

| 配置项 | 传参 | 落库 | 结果 |
|---|---|---|---|
| 必填 | `notNull=true` | `is_not_null=1` | ✅ |
| 唯一 | `uniqueness=true` | `uniqueness=1` | ✅ |
| 多选 | `multiSelect=true`（需关联） | `multi_select=1` | ✅ |
| 审计 | `auditLog=true` | `audit_log=1` | ✅ |
| 全文检索 | `searchable=true` | `searchable=1` | ✅ |
| 最小/最大长度 | `minLength`/`maxLength` | `min_length`/`max_length` | ✅ |
| 小数精度 | `decimalDigits` + `maxLength` | `decimal_digits` | ✅ |
| 默认值-固定值 | `defaultValue="固定默认值"` | `default_value` | ✅ |
| 默认值-系统变量 | `defaultValueIsChange=false` + `defaultValueSystemVariable="CURRENT_DATE"` | `default_value_sys_variable` | ✅ |
| 描述 | `description` | `description` | ✅ |
| 输入校验（正则） | `dataFormat="^[0-9]{6}$"` + `patternMessage` | `data_format`/`pattern_message` | ✅ |
| 加密 | `enableEncryption=true` + `encryption="REVERSIBLE_ENCRYPTION"` | `encryption=1` | ✅ |
| 脱敏-全 | `enableDesensitization=true` + `desensitization="All"` | `desensitization=1` | ✅ |
| 脱敏-自动 | `desensitization="Auto"` | `desensitization=0` | ✅ |
| 脱敏-自定义 | `desensitization="Custom"` | `desensitization=2` | ✅ |
| 敏感词检测 | `enableSensitiveWordCheck=true` | `enable_sensitive_word_check=1` | ✅ |
| WEB/移动端控件 | `widgetConfig`（JSON 字符串） | `widget_config` | ✅ Input/InputNumber/TextArea/Select 四种都试过 |

### 12.1 两个枚举的真实值域（反编译 boot-core 5.3.358）

```java
EncryptionType   NOT_ENCRYPTION(0) / REVERSIBLE_ENCRYPTION(1) / DECRYPT_ONLY(2)
MaskType         None(-1) / Auto(0) / All(1) / Custom(2)
```

⚠ 我一开始猜 `AES`/`MD5`/`FULL` 全部报
`BOOT_3002 No enum constant com.seeyon.boot.annotation.enums.EncryptionType.AES`。
**枚举值必须从反编译读，别猜。**

### 12.2 widgetConfig 形态

```json
{"pc":"Input","mobile":"Input","list":true,"detail":true,"quickSearch":true}
```

是 **JSON 字符串**（不是对象）。`pc`/`mobile` 换控件名即可：
`Input` / `InputNumber` / `TextArea` / `Select` 实测都通过。

### 12.3 页面上的控件（用户截图对应）

- 「类型」下拉 → 18 种 dataType，选不同值下方配置项会变
- 「默认值」下拉 + 加号 → 加号展开系统变量/表达式配置
  （对应 `defaultValueIsChange` / `defaultValueSystemVariable`）
- 五个开关 → 多选 / 必填 / 唯一 / 审计 / 全文检索
- 「描述」文本域 → `description`
- 「WEB端默认控件」「移动端默认控件」→ `widgetConfig.pc` / `.mobile`

## 十三、可复用脚本

```bash
# 类型矩阵：18 种类型各建一个字段
python tools/core/setting/attribute_set_type_matrix.py --run \
    --set-id <字段集id> --prefix tq --with-capabilities \
    --ctp-enum-id <枚举id> --enum-id <选项集id> \
    --entity-full-name <实体全类名> \
    --serial-name <流水号名> --serial-code <code> --serial-guid <guid> \
    --i-have-write-authorization

# 字段级配置：20 项配置各建一个字段
python tools/core/setting/attribute_set_field_config.py --run \
    --set-id <字段集id> --prefix cfg --ctp-enum-id <枚举id> \
    --i-have-write-authorization

# 只读查看某字段集全部字段的配置
python tools/core/setting/attribute_set_field_config.py --dump --set-id <字段集id>
```

## 十四、枚举字段显示 null 的根因（用户点名问题，2026-10-21）

### 现象

页面上 CTPENUM 字段的「枚举」列显示 **null**，但字段本身建成功了。

### 根因：`relation_entity_name` 为空

真实业务字段 vs 我建的字段（DB 对比）：

```
真实  OAlcspzt             relation_entity=-4937502446078815912
                          relation_app=4396215186967839451
                          relation_entity_name='OA流程审批状态'   ← 有中文名
我建  tq12ctpenum          relation_entity=-1052013552430069963
                          relation_app=8704025620829192834
                          relation_entity_name=None               ← 空的
```

平台读字段时用 `relation_entity_name` 回显「枚举」列，我传的 body 里**没有这个字段**，
所以落库为 null → 页面显示 null。

### 枚举候选的真实加载入口（页面抓包）

```
POST /service/udc/graphql?udcMetaDataSelectCtpEnumAppGet
path = {"appId": "<appId>"}
```

返回结构（`content` 是**数组**，不是对象）：

```jsonc
[{
  "applicationInfo": {"id":"...","name":"datamigration...","caption":"数据迁移"},
  "categoryAndItemDtos": [          // 分组
    {"id":"-2664725665501750254", "name":"验收分组E2E",
     "children":[                    // 分组下的枚举
       {"id":"5079316968262147703", "name":"{\"zh_CN\":\"E2E验收枚举\"}",
        "code":"zxjE2eEnum", "fullName":"...", "enumType":"...", "enumLevel":...,
        "children":[...]}            // 枚举项（第三层）
     ]}
  ],
  "rootEnumDtos": [...]              // 根枚举
}]
```

本应用实测：8 个分组，第三层是枚举项。

⚠ `name` 是 **i18n JSON 字符串**（`{"zh_CN":"E2E验收枚举"}`），不是纯文本；
页面显示的中文是从这个 JSON 里取的。

### 枚举树的正确操作方式（页面点不动时）

antd 的 tree dropdown 用**虚拟滚动 + fixed 定位**，实测：
- `getBoundingClientRect()` 返回 `x=-9245, y=-9588`（被移到视口外）
- 真实鼠标点击坐标无效
- JS `.click()` 也无效（受控组件）

**可用方式：键盘导航**（焦点在 selector 上）：

```
ArrowDown / ArrowUp    在树节点间移动
ArrowRight             展开当前分组
ArrowLeft              收起
Enter                  选中
```

实测序列（本应用）：

```
数据迁移 → 验收分组E2E → 验收分组2026 → 数据迁移枚举 → 验收分组E2E二
        → UI轨迹枚举 → 小爪平台枚举 → 事项中心 → 用户中心 → 组织模型
```

展开展开「验收分组E2E」后，其下出现「E2E验收枚举」，
`ArrowDown` 到它 → `Enter` → selector 显示「E2E验收枚举」✅

### 已解决（用户提供抓包报文）

**页面的保存 op 是 `udcEntityAttributeUpdatePost`，不是 `udcEntityAttributePost`！**
（我之前一直在用 Post，所以怎么传都是 null。）

CTPENUM 字段的 body 必须包含三个关联槽位 + relationCtpEnum 嵌套：

```json
{
  "name": "enumNestedTest",
  "dataType": "CTPENUM",
  "relationCode": "XzhCtpEnum953322",
  "relationEntity": "4456389269786582653",
  "relationEntityName": "小爪平台枚举",
  "relationCtpEnum": {"enumType": "SAME_LEVEL", "enumLevel": 0},
  ...
}
```

| 槽位 | 含义 | 缺了会怎样 |
|---|---|---|
| `relationCode` | 平台枚举编码（非自建） | `relation_code` 落库为空 |
| `relationEntity` | 枚举 id | `relation_entity` 落库为空 |
| `relationEntityName` | 枚举显示名 | **页面「枚举」列显示 null** |
| `relationCtpEnum` | 嵌套对象，只带 `enumType`+`enumLevel` | 不影响落库但形态不对 |

⚠ **不要传 `id`/`code` 到 `relationCtpEnum` 里** —— 页面没传，我也不要传。

实测：修正后 `relation_entity_name = '小爪平台枚举'` 落库成功。

### 待办

| 项 | 状态 | 说明 |
|---|---|---|
| 「高级模式」默认值面板 | **未开始** | 用户说这个面板在实体/微流程/页面规则都复用，各处的 JSON 格式不同，需逐个测 |
| 实体选择器 | **同 CTPENUM 模式** | 应走 `udcEntityAssociationEntityAppGet` 加载 → 选 id + name + code |

### 教训（用户明确指出）

> 「你咋又直接路径了，为啥不看加载然后选择」

**关系型字段（枚举/实体/选项集）必须先调候选加载接口、从返回列表里选 id，
不能自己拼一个 id 或全类名塞进去。** 自己拼的 id 能过服务端校验（BOOT_0000），
但 `relation_entity_name` 等回显字段是空的，页面就显示 null。

这条同样适用于：
- 字段集的「实体」类型 → 候选来自 `udcEntityAssociationEntityAppGet` 或类似
- 二维码的 `pcPagePath` → 候选来自 `udc_page_info.page_url`（已修正过）
- 导入导出模板的 `entityFullName` → 应走实体候选

## 十五、表达式字段（calculate=COMPUTE）—— 2026-10-21 实测

### 15.1 三段链全部 LIVE PASS

```
1) POST /service/udc/expression/schema
   {"ids":["474806313816300867"], "paramType":"ENTITY", "upsource":true, "serverName":"udc"}
   ★ 不能带 appId（带上报 BOOT_3000）
   → data.content = [SchemaStructureDto…]（字段集/实体的变量树）

2) POST /service/udc/expression/check
   {"resultTypeInfo","schemas","tokens","isMultiSelect","terminalSupportType"}
   → data.content = true

3) POST /service/udc/expression/transform
   同 schema → data.content = {
     "designData":  {expressionTranslation, resultTypeInfo, resultTypeFullName,
                     terminalType, isMultiSelect, context, tokens, sourceAppName, version},
     "runtimeData": {executableExpr}
   }
```

实测产出（系统日期时间）：

```
designData  = {"expressionTranslation":"系统日期时间 ","resultTypeInfo":"DATETIME",
               "resultTypeFullName":null,"terminalType":"BACKEND","isMultiSelect":false,
               "context":[],"tokens":[{"uid":"t1","type":"SYSTEM",
               "value":"system.currentDateTime","desc":"系统日期时间"}],
               "sourceAppName":null,"version":null}
runtimeData = {"executableExpr":"93gDaq3/nXB1+C8j4AjYNEVRRY+GX/DRejGmES20GvQ=currentDateTime%28%29"}
```

⚠ `executableExpr` 里那段 base64 是**服务端加密前缀**，客户端不能自造。

### 15.2 落库：design 能写，runtime 写不进去（已定性）

```
POST /service/udc/entity/attribute/update   （REST，不是 GraphQL UpdatePost）
  body = GET /service/udc/entity/attribute/{id} 拿到的完整 DTO（77 键）改后整体回传
```

实测结果：

| expressionRuntimeData 传值 | 结果 |
|---|---|
| `null` | **BOOT_0000** ✅ |
| `""` | **BOOT_0000** ✅ |
| `{}` | **BOOT_3000** ❌ |
| `{"a":1}` | **BOOT_3000** ❌ |
| `{"executableExpr":"x"}` | **BOOT_3000** ❌ |
| `{"executableExpr":"1+1"}` | **BOOT_3000** ❌ |
| `{"executableExpr":"currentUserId()"}` | **BOOT_3000** ❌ |
| transform 原样返回的那个（带 base64） | **BOOT_3000** ❌ |

⇒ **该接口完全拒绝任何非空 `expressionRuntimeData`**，连 `{"a":1}` 都拒。
`BOOT_3000` 且 `message=null` = 反序列化阶段就挂了，不是业务校验。

**结论**：`expressionRuntimeData` 由服务端在**代码生成阶段**写入，不接受客户端传。
客户端只写 `expressionDesignData` + `calculate`。

### 15.3 已落库的成果

`txtCompute`（id=-6576460611454632943）：

```
calculate            = COMPUTE
expressionDesignData = {"expressionTranslation":"系统日期时间 ","resultTypeInfo":"DATETIME",...}
expressionRuntimeData = ""   ← 空，等代码生成时服务端补
```

真实业务样本对照（`matCount` / `updater` 等）的 runtime **都有值** ——
说明它们经过了代码生成（应用构建/发布），而设计态直接写库时 runtime 就是空的。

### 15.4 关键约束（踩过的）

| 项 | 结论 |
|---|---|
| `expression/schema` 带 appId | **BOOT_3000**，必须省略 |
| `tokens[].type` 值域 | 恰 5 值：CONSTANT / VARIABLE / SYSTEM / FUNCTION / OPERATOR（`SYSTEM_VARIABLE` 不存在）|
| `designData` 缺 `context` 键 | 检测器 `EntityExprConsistencyValidationImpl.buildSchemaMap:148` 抛 NPE，整个检测 FAIL |
| `calculate=COMPUTE` 必须有 designData | 否则 `UDC_ATTR_0017` |
| `executableExpr` 的 base64 前缀 | 服务端加密产物，客户端不可造 |

### 15.5 可用脚本

```bash
# 预设方案列表（sys_datetime / sys_userid / concat / constant）
python tools/core/setting/attribute_expression_build.py --list

# 给指定字段写入表达式（三段链 + 落库）
python tools/core/setting/attribute_expression_build.py --run \
    --set-id <字段集id> --field-name txtCompute --plan sys_datetime \
    --i-have-write-authorization
```

⚠ 脚本里落库那段固定用 `expressionRuntimeData = null`（写非空必被拒）。

### 15.6 ★ 函数维度实证（2026-10-22 补：本轮之前是空白）

用户 2026-10-21 原话：「文本x6 然后**每个文本不同的表达式和不同函数和不同的校验**」。
上一轮只做到「不同校验」——`calculate=1` 仅 `txtCompute` 一个，`concat` 方案
写好了**从没运行过**，DB 里 `token.type=FUNCTION` 一个都没有。2026-10-22 补齐。

**平台函数清单（实测 `POST /service/udc/expression/preset/list`）**：

```
88 个函数 / 8 大类
  基础函数 15   日期函数 24   数学函数 10   文本函数 17
  条件函数  1   聚合函数 18   变化函数  1   枚举函数  2
系统变量 131 个 / 4 组：organization 95 / date 33 / env 2 / plugin 1
```

⚠ **函数清单必须从 `preset/list` 实拉，不许手抄**（平台加函数你不知道）。
聚合函数 18 个需「明细表属性」，字段集没有明细行 ⇒ 不可用，选函数时排除。

**已落库的 6 个函数字段（LIVE PASS，DB 回读 confirm）**：

| 字段 | 函数 | 类别 | 校验配置 | DB 回读 |
|---|---|---|---|---|
| `fnJoin` | `join` | 文本 | `notNull=1` + len 0-80 | `calculate=1` FUNC=['join'] ✅ |
| `fnSubstr` | `substringByIndex` | 文本 | len 1-4 | `calculate=1` FUNC=['substringByIndex'] ✅ |
| `fnDateStr` | `dateToString` | 日期 | len 8-8 | `calculate=1` FUNC=['dateToString'] ✅ |
| `fnRound` | `round` | 数学 | len 0-20 | `calculate=1` FUNC=['round'] ✅ |
| `fnIfs` | `ifs`（嵌套 `isNull`） | 条件 | 正则 `^[A-Z_]+$` | `calculate=1` FUNC=['ifs'] ✅ |
| `fnRand` | `randBetween` | 基础 | len 1-4 | `calculate=1` FUNC=['randBetween'] ✅ |

**6/6 全部落库**，覆盖 5 个函数大类（文本/日期/数学/条件/基础）+ 4 种校验形态
（notNull / 定长 / 长度区间 / 正则）+ 1 个嵌套函数（`ifs` 内嵌 `isNull`）。

⇒ **函数 token 组装形态已实证**：`{"type":"FUNCTION","value":"<函数名>",
"subOps":[[子token组],...],"uid":"<8位hex>"}`，
`subOps` 是**二维数组**（每组 = 一个参数位置的候选），嵌套函数也放进 `subOps`。

**字段集取 schema 的正确姿势（踩过三种错）**：

```
字段集 id + paramType=ENTITY      -> BOOT_0000 但 schemas=0（静默空，最容易误判成功）
空 ids + paramType=CONFIG_PARAM   -> 3 个内置变量（与字段无关，但函数提交够用）
实体 id + paramType=ENTITY        -> 1 个 schema（该实体的字段清单）
```

⚠ 字段集本身没有实体，所以**拿不到字段列表是正常的**；函数表达式的
参数位置由平台按函数元数据校验，不依赖 schema 里的实体字段。

**GraphQL 响应是双层（踩过）**：

```python
# ❌ r["code"] 恒为 None —— 建字段其实成功却判 FAIL
# ✅ 正确读法
d0 = r["data"]["data0"];  code = d0["code"];  fid = d0["data"]["content"]
```

**脚本**：

```bash
python tools/core/setting/attribute_function_matrix.py --list
python tools/core/setting/attribute_function_matrix.py --run \
    --app-id <appId> --set-id <setId> [--entity-id <实体id>] [--plan <方案名>] \
    --i-have-write-authorization
```

## 十六、widgetConfig 按 dataType 的正确取值（2026-10-21 全库统计）

### 16.1 问题

我最初所有字段一律用 `{"pc":"Input","mobile":"Input"}`，这是错的：

- 日期字段用 `Input` 装不了
- 枚举用 `Input` 选不了
- 附件用 `Input` 传不了
- 金额用 `Input` 显示不出货币格式

### 16.2 真实对照表（按 dataType 分组统计全库众数）

| dataType | pc 控件 | mobile 控件 | 样本数 |
|---|---|---|---|
| `STRING` | `Input` | `Input` | 15819 |
| `MULTILINESTRING` | `TextArea` | `TextArea` | 462 |
| `INTEGER` | `InputNumber` | `InputNumber` | 2831 |
| `BIGINTEGER` | **`Input`** | **`Input`** | 3632 |
| `DECIMAL` | `InputNumber` | `InputNumber` | 4330 |
| `CURRENCY` | `Currency` | `Currency` | 100 |
| `DATE` | `DatePicker` | **`DateTimePicker`** | 1322 |
| `TIME` | `TimePicker` | `TimePicker` | 188 |
| `DATETIME` | `DatePicker` | **`DateTimePicker`** | 7896 |
| `BOOLEAN` | `Switch` | `Switch` | 3089 |
| `ENUM` | `TreeSelect` | **`CascaderSelect`** | 2725 |
| `CTPENUM` | `TreeSelect` | **`CascaderSelect`** | 2132 |
| `ENTITY` | `UdcReference` | `UdcReference` | 11258 |
| `ATTACHMENT` | `Attachment` | **`Upload`** | 265 |
| `CONTENT` | `UiBusinessContent` | `UiBusinessContent` | 3 |
| `DOCUMENTNUMBER` / `Serial` / `OPINION` | `Input` | `Input` | 2 / 215 / 2 |

**四个反直觉的点：**

1. **`BIGINTEGER` 用 `Input` 不是 `InputNumber`** —— 大整数可能超出 JS 安全整数范围，用文本框
2. **PC 和移动端控件常不同**：
   - `DATE`/`DATETIME`：PC `DatePicker` / 移动 `DateTimePicker`
   - `ENUM`/`CTPENUM`：PC `TreeSelect` / 移动 `CascaderSelect`
   - `ATTACHMENT`：PC `Attachment` / 移动 `Upload`
3. **`CURRENCY` 有专属控件**，不是 `InputNumber`
4. **`CONTENT` 用 `UiBusinessContent`**（正文编辑器）

### 16.3 list / detail / quickSearch 也按类型不同

| dataType | list | detail | quickSearch |
|---|---|---|---|
| `STRING` | true | true | true |
| `MULTILINESTRING` | true | true | **false** |
| `INTEGER` / `BIGINTEGER` | **false** | **false** | **false** |
| `DECIMAL` / `CURRENCY` | true | true | true |
| `DATETIME` | **false** | **false** | **false** |
| `ENUM` | **false** | **false** | **false** |
| `CTPENUM` | true | true | true |
| `ENTITY` | **false** | **false** | **false** |
| `ATTACHMENT` | **false** | **true** | **false** |
| `CONTENT` | **false** | **true** | **false** |

### 16.4 代码

```python
from components.udc.setting.attribute_set_constraints import (
    DEFAULT_WIDGETS, DEFAULT_WIDGET_FLAGS, build_widget_config)

# 按 dataType 自动生成正确形态
cfg = build_widget_config("DATE")
# → {"pc":"DatePicker","mobile":"DateTimePicker","list":true,"detail":true,"quickSearch":true}

# 覆盖部分字段
cfg = build_widget_config("STRING", pc="Select", list_=False)

# build_attribute_field_body 已自动按 dataType 选控件
body = build_attribute_field_body(app_id, set_id, name="f", caption="c", data_type="ENUM")
json.loads(body["widgetConfig"])["pc"]  # → "TreeSelect"
```

### 16.5 修正脚本

```bash
# 只读：列出每个字段应有的 vs 实际的控件
python tools/core/setting/attribute_widget_fix.py --dump --set-id <id>

# 修正（按 DEFAULT_WIDGETS 逐个 UpdatePost）
python tools/core/setting/attribute_widget_fix.py --fix-all --set-id <id> \
    --i-have-write-authorization
```

### 16.6 修复实测

演示集 8 个字段中 2 个控件错误：

```
枚举字段  CTPENUM  Input/Input  →  TreeSelect/CascaderSelect   ✅
实体字段  ENTITY   Input/Input  →  UdcReference/UdcReference   ✅
```

6 个 STRING 字段本来就是 `Input`，无需改。

⚠ 修正 UpdatePost 时**必须同时把 `expressionRuntimeData` 置 null**
（上一轮已定性：传任何非空 JSON 都报 `BOOT_3000`）。

### 16.7 ★ 页面实证：控件名 ≠ DOM 类名（2026-10-22）

上一轮只验到接口层（DB 里 widget_config 正确）。用 CDP 点进字段读真实 DOM 后，
发现**用 antd 类名做判据会误判**：

| widgetConfig 值 | 页面控件下拉显示 | DOM 实测 | 说明 |
|---|---|---|---|
| `Input` | 文本 | `.ant-input` | 纯 antd ✅ |
| `InputNumber` | 数字 | `.ant-input-number` | 纯 antd ✅ |
| `DatePicker`/`DateTimePicker` | 日期 | `.ant-picker` | 纯 antd ✅ |
| `Switch` | 开关 | `.ant-switch` | 纯 antd ✅ |
| `TreeSelect`/`CascaderSelect` | 下拉 | `.ant-tree-select`/`.ant-select` | 纯 antd ✅ |
| **`Attachment`** | **附件** | **无 `.ant-upload`** | ★ 平台自定义组件 |
| **`UdcReference`** | 引用 | 非 `.ant-select` | ★ 平台自定义组件 |
| **`Currency`** | 货币 | `.ant-input-number` | ★ 包装层 |
| **`UiBusinessContent`** | 正文 | 无独立 class | ★ 平台自定义组件 |

⇒ **页面实证的正确判据是读「WEB端默认控件 / 移动端默认控件」下拉的显示值**
（"附件"/"文本"/"日期"…），不是查 antd 类名。
类名判据只对纯 antd 控件有效；对 4 个平台自定义组件会把「已正确渲染」误判成「没渲染」。

⚠ 列表行（`.ant-table-row`）里**不渲染控件**，只有文本（名称/编码/类型/关联）；
控件在**字段详情面板**。判断渲染必须点进字段。

**实测覆盖（zxjTypeFull 74 字段）**：

```
PASS      STRING / INTEGER / BIGINTEGER / DATE / TIME / DATETIME / ENUM / CTPENUM / CURRENCY
已确认     ATTACHMENT（下拉显示「附件」）
PARTIAL   MULTILINESTRING / BOOLEAN / CONTENT（被面板其他控件干扰，未单独隔离）
```

**踩过的坑**：zxjTypeFull 里 **28 个字段的 widget_config 仍是 Input** ——
`attribute_widget_fix.py --fix-all` 从没对这个字段集跑过（只在表达式演示集跑过）。
`--dump` 能查出来，`--fix-all` 一次修完 28/28。
