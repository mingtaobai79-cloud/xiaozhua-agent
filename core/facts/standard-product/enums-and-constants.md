# 枚举与常量：值从哪查

## 1. Capability

回答「这个枚举有哪些值」「这个错误码等于什么字符串」「这个特性开关的键名是什么」。

这三类东西在代码里天天用，但方法签名里一个都看不到——它们是类型定义的一部分，不是方法。

| 你要找 | 数量 | 在哪 |
|---|---|---|
| 枚举及其值名 | **758 个枚举 / 5632 个值** | `packages/<构件>.md` 的「四、枚举」节 |
| 常量类的字面值 | **157 个类 / 5965 个常量** | `docs/audit/artifacts/extension-surface-20261029/constants.md` |
| 全部带值字段 | 10257 个（散在小类里） | `interfaces.json` 的 `classes[x].fields[].value` |

## 2. Version

同 `BASELINE.md`。

## 3. Input

```
javap -p -constants 的输出
  `public static final String X = "abc";`  → fields[].value = "abc"
  `public static final Color RED;`         → 枚举值（无值，ordinal = 声明顺序）
```

## 4. Required

无（纯查表）。

## 5. Execution

```
① 知道类名 → constants.md 里搜类名（>=10 个常量的类都在）
② 只知道用途 → 看下面 §7.1 的表定位到类
③ 枚举 → packages/<构件>.md 的「四、枚举」节，值名按声明顺序（= ordinal）
```

## 6. Side Effects

无。

## 7. Known Constraints

### 7.1 高频常量类（这 8 个覆盖日常 90%）

| 类 | 常量数 | 是什么 | 典型值 |
|---|---|---|---|
| `udc.detection.constant.ConsistenceErrorCode` | **529** | 一致性检测错误码 | `UDC_CE_NOT_NULL = "UDC_CE_0001"` |
| `boot.starter.systemvariable.util.SystemVariableUtils` | 288 | 系统变量名 | 见 §7.3 |
| `cip.provider.common.FeatureConstant` | 240 | 能力特性键名 | `ENTERPRISE_INFO_CODE = "enterpriseInfo"` |
| `boot.starter.formula.engine.functions.date.DateFunction` | 230 | 表达式日期函数名 | — |
| `udc.common.constant.UdcCommonConstant` | 187 | 表名 / 包路径 / 前缀 | `APP_ATTACHMENT = "app_attachment"` |
| `cip.capability.exception.CapabilityErrorCode` | 141 | 能力异常码 | — |
| `boot.starter.formula.engine.functions.text.TextFunction` | 130 | 表达式文本函数名 | — |
| `boot.starter.formula.engine.functions.list.ListFunction` | 109 | 表达式集合函数名 | — |

### 7.2 枚举怎么用

`packages/<构件>.md` 的「四、枚举」节长这样：

```
- `BizType`（5 常量）：UDC_DESIGN, UDC_RUNTIME, FORM, ORGANIZATION, CTP_AFFAIR
- `CtpEnumType`（3 常量）：SAME_LEVEL, MULTI_LEVEL, CASCADE
```

**值名按 javap 输出顺序，即 ordinal 顺序**。JSON 里传 ordinal 时是 0/1/2…，
传名字时是 `"UDC_DESIGN"` 这种——具体平台用哪种，看 DTO 字段类型（枚举类型 vs String）。

枚举分布最密的地方：`bpm-facade` 96 个、`udc-biz` 90 个、`organization-facade` 64 个、
`udc-common` 64 个、`ctp-user-facade` 54 个。

### 7.3 系统变量名 288 个（最常被问）

`SystemVariableUtils` 里那 288 个常量就是系统变量的键名。
`boot.starter.systemvariable` 域的 `SystemVariableUtils` 有 126 个**静态方法**（取值用），
常量是**键名**（传参用）——两者别混。

### 7.4 拿不到的东西：枚举的自定义值

```java
public enum Status {
    DRAFT("1", "草稿"),          // ← "1" 和 "草稿" 拿不到
    SENT("2", "已发送");
    Status(String code, String label) { ... }
}
```

`javap -p -constants` 只给 `public static final Status DRAFT;`，**构造参数在 `<clinit>` 里**，
要看值必须 `javap -c` 反汇编 static 初始化块，本产物没做。

⇒ 所以：**枚举值名有了，枚举的 code/label 映射还得看源码或反编译**。
遇到必须知道 label 的场景（如导出报表要中文名），按 §8 的方法单独反编译那个枚举。

同理，`FeatureConstant` 里有中文值（如 `ENTERPRISE_INFO = "企业搜索+工商..."`），
那是 String 常量所以能拿到；但枚举里的中文标签拿不到。

### 7.5 常量不在 constants.md 里怎么办

`constants.md` 只收常量数 >= 10 的类（157 个）。少于 10 个的散落在
`packages/<构件>.md` 里——但那边只列方法、不列字段值。

要查单个类的常量值，直接读 `interfaces.json`：

```python
d = json.load(open("interfaces.json"))
[f for f in d["classes"]["com.x.YyyConstant"]["fields"] if "value" in f]
```

或者重跑 `emit_constants.py --min-consts 1` 导全量（会很大）。

## 8. Evidence

```
docs/audit/artifacts/extension-surface-20261029/
  constants.md          157 类 / 5965 常量（带值），369 KB
  packages/*.md         「四、枚举」节：758 个枚举的 5632 个值名
  interfaces.json       classes[].constants（枚举值名数组）
                        classes[].fields[].value（常量字面值）

生成器
  tools/core/platform/emit_constants.py   --min-consts 10
  tools/core/platform/emit_package_surfaces.py  枚举节
  tools/core/platform/index_backend_interfaces.py  枚举还原 + -constants 字段值

踩过的坑（都修了）
  ① javap 把 enum 输出成 `final class X extends java.lang.Enum<X>`，
     不还原就全被当 class（实测漏了 758 个枚举）
  ② javap 默认不显示常量值，必须加 -constants（漏了 10257 个值）
```

## 9. Verified

| 项 | 等级 |
|---|---|
| 758 个枚举、5632 个值名、756 个带常量 | `VERIFIED_STATIC_BYTECODE`（javap -p） |
| 10257 个字段的字面值 | `VERIFIED_STATIC_BYTECODE`（javap -p -constants） |
| 枚举的 code/label 映射 | **UNVERIFIED**（在 `<clinit>` 里，需 javap -c） |
| 常量值不等于存储值（如中文名 vs 英文码） | **UNVERIFIED**，两者可能不同，写库前先确认 |
