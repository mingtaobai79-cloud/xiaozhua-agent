# 敏感词 · 数据类型体系 · boot 侧制品

## Capability

```
boot-starter-sensitive   敏感词校验（含 BPM 模板/事项的接口常量）+ 脱敏 SPI 实现
boot-starter-datatype    平台数据类型体系（DataType / DataTypeManager，19+ 类型实现）
boot-starter-artifact    boot 侧制品上传下载（与 devops-starter-artifact 是两套）
```

## Version

`sensitive` 5.3.603 / `datatype` 5.3.600 / `artifact` 5.3.600。

## ★ 一、敏感词（sensitive）

```java
SensitiveWordService
  void sensitiveCheck(SensitiveCheckDto dto, Object payload);                       // 旧口
  void sensitiveCheckNew(SensitiveCheckDto, Map<String,Object>, Map<String,String>); // 新口
  Object invokeResult(Object);
  String getTranslateCode(String, String);
  String invokeBpmTemplate(Long, String);
  SingleResponse<Object> invokeAppService(String, String, String, Object, String);
```

关键常量（被检查的三个面）：

```
CASE_INTERFACE / CASE_METHOD          案件（case）
TEMPLATE_INTERFACE / TEMPLATE_METHOD  模板（BPM 模板）
AFFAIR_INTERFACE / AFFAIR_METHOD      事项（affair）
```

脱敏侧：`SensitiveSpiImpl implements com.seeyon.boot.starter.mybatis.sensitive.SeeyonSensitive`
→ `String sensitiveProcess(String)`。
⇒ **读写库时的字段脱敏走这条 SPI**；注解侧是 `@Maskable` / `@Safety`（见 `platform-annotations.md`）。

错误码：`SensitiveErrorCode.SENSITIVE_CHECK_ERROR`。

## ★ 二、数据类型体系（datatype）

```java
public interface DataType<T> extends Serializable {
    String  getName();            boolean getVisibility();
    String  getCaption();         boolean baseDataType();
    String  getJavaType();        int     getDatabaseType();
    T       valueOf(String);      String  getString(T);
    boolean isValid(Object);
}

DataTypeManager
  static List<DataType> getDataTypes(String... names);
  static DataType       getDataTypeByName(String name);
```

已有实现（类名即类型）：`StringDataType` / `NumberDataType` / `BigIntegerDataType` /
`DateDataType` / `BooleanDataType` / `ObjectDataType` / `FileDataType` / `AttachmentDataType` /
`ArrayDataType` …，抽象基类 `AbstractDataType<T>` 提供 `getVisibility()` / `mockUp()`。

⇒ 场景：**自定义实体属性/导入导出**里做「字符串 ↔ Java 值 ↔ 库列类型」的转换与校验，
先 `getDataTypeByName(name)` 再 `isValid` / `valueOf`，不要自己写 if-else 判类型。

## ★ 三、boot 侧制品（boot-starter-artifact）

```java
BootArtifactManager
  boolean upload(ArtifactDto);
  String  download(ArtifactDto);

实体：CtpArtifactUpload（appName / appVersion ...） + CtpArtifactUploadDao
```

与 `devops-starter-artifact` 的分工：后者走 Maven/桶/命令三形态的制品仓；
这个是 boot 侧的上传记录与下载（平台自用），客开一般不用。

## Side Effects

- `sensitiveCheck` 命中会**抛业务异常**（`SENSITIVE_CHECK_ERROR`），不是返回布尔。
- `DataType.valueOf` 对非法输入的行为由实现决定（多数抛异常）—— 先 `isValid`。
- `BootArtifactManager.upload` 会写 `ctp_artifact_upload` 记录。

## Known Constraints

1. 敏感词有三个检查面（case/template/affair），选错常量 = 检查不到。
2. `sensitiveCheckNew` 的第三个参数是 `Map<String,String>`（字段→翻译码），不是 DTO。
3. `DataTypeManager` 是静态方法，无 Spring 依赖。
4. 两套 artifact 包名相近（`boot.starter.artifact` vs `devops.starter.artifact`），别注入错。

## Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| `SensitiveWordService` 6 方法 + 6 常量 | `javap -p` 5.3.603 | VERIFIED_STATIC_BYTECODE |
| `SensitiveSpiImpl implements SeeyonSensitive` | 同上 | VERIFIED_STATIC_BYTECODE |
| `DataType` 9 抽象方法 + `DataTypeManager` 2 静态方法 | `javap -p` 5.3.600 | VERIFIED_STATIC_BYTECODE |
| 8+ 具体 DataType 实现类 | 类清单 | VERIFIED_STATIC_BYTECODE |
| `BootArtifactManager` upload/download | `javap -p` | VERIFIED_STATIC_BYTECODE |

## Verified

- ✅ 类与签名可复核
- ⚠️ 未真机触发敏感词校验

## 给 Agent 的判据

```
要校验敏感词        → SensitiveWordService.sensitiveCheckNew(dto, 字段Map, 翻译码Map)
字段要脱敏          → 走 SeeyonSensitive SPI（@Maskable/@Safety 注解侧）
要在类型间转换      → DataTypeManager.getDataTypeByName + isValid/valueOf
制品上传（boot 侧）  → BootArtifactManager.upload（别与 devops-starter-artifact 混）
```
