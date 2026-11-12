# UDC 微流程数据源类型全谱与后端适配（LIVE + CFR 双证）

> 2026-10-28。回答两个问题：① 数据源到底有多少种（前端 UI vs 后端枚举）；② 前端填的值能不能被后端解析。

## 一、结论先行

| 层 | 数量 | 值域 | 权威来源 |
|---|---|---|---|
| **后端 `ParamTypeEnum`** | **8 种** | `DEFAULT_OBJECT(0)` `BASIC(1)` `ENTITY_OBJECT(2)` `ENUM(3)` `MAP(4)` `METADATA(5)` `MESSAGE(6)` `OTHER(7)` | CFR 反编译 `cfr-r31b/com/seeyon/udc/enums/microflow/ParamTypeEnum.java` |
| 前端「选择数据」radio | 7 种 | 缺 `MAP` | 真实 UI 实测（`映射操作` 抽屉） |
| 参数页入参/出参 | 4 种 | 无参数 / 基本类型 / 实体对象 / 自定义对象 | 真实 UI 实测（`参数` 页签） |
| 历史记录（错误） | 5 种 | 漏 `METADATA` `MESSAGE` `OTHER` | 本文件更正前 |

**「后台没那么少」是对的**：后端 8 种，我们之前只记了 5 种，漏掉的 `METADATA` / `MESSAGE` / `OTHER` 会导致这三类生成必然失败。

## 二、8 种数据源逐个说明

| # | paramType | 中文 | code | needFullName | 后端读取字段 | 典型用途 |
|---|---|---|---|---|---|---|
| 1 | `DEFAULT_OBJECT` | 自定义对象 | 0 | ✅ | `app` `structure` `mappingType` | 应用内自定义 DTO |
| 2 | `BASIC` | 基本类型 | 1 | ❌ | `dataType` | 文本/整数/日期等 |
| 3 | `ENTITY_OBJECT` | 实体对象 | 2 | ✅ | `app` `structure` | 实体/业务表记录 |
| 4 | `ENUM` | 选项集 | 3 | ✅ | `app` `structure` `value` | 枚举值 |
| 5 | `MAP` | 映射 | 4 | ❌ | `dataType` | `Map<String,Object>`，**前端 radio 不提供** |
| 6 | `METADATA` | 元数据 | 5 | ❌ | `app` `metaDataType` | 页面/实体元数据 |
| 7 | `MESSAGE` | 事件对象 | 6 | ❌ | `dataType` | MQ 消息 / 业务事件 |
| 8 | `OTHER` | 其他 | 7 | ❌ | `otherType` | 系统内置对象 |

### needFullName 的含义

后端 `ParamTypeEnum.needFullName()` 只对三种返回 true：

```java
return DEFAULT_OBJECT.equals(paramType)
    || ENTITY_OBJECT.equals(paramType)
    || ENUM.equals(paramType);
```

即这三类**必须带完整 javaType/fullName**，否则解析器拿不到类型。其余五种不需要。

## 三、后端如何解析（决定「填的值能否适配」）

`CreateVariableActivity.parseActivityNode` 的分支逻辑：

```java
String paramTypeStr = NodeUtils.getString("paramType", node, false, location, result);
createVariable.setParamType(ParamTypeEnum.getByName(paramTypeStr));
if (ParamTypeEnum.OTHER.equals(createVariable.getParamType())) {
    this.buildOtherTypeVariable(node, result, location, createVariable);   // 只认 otherType
} else {
    String dataType = NodeUtils.getDataType(node, location, result);
    createVariable.setDataType(dataType);
    createVariable.setJavaType(NodeUtils.convertDataType(dataType));
    this.buildActivityByDataType(...);                                     // 按 dataType 再分支
}
```

**关键**：`paramType` 决定第一层分支，`dataType` 决定第二层分支。两个都要对。

### dataType 二次分支（`buildActivityByDataType`）

| dataType | 后端行为 | 缺什么会报错 |
|---|---|---|
| `Dto`（=DTO） | 读 `mappingType`，分 value / mapping / 其它三种 | `mappingType` 为空 → 走 else，attrs 为空 |
| `Enum` | 读 `structure` + `value`，校验 `value.selectParam.javaType` 与结构一致 | 不一致 → `ENUM_NOT_MATCH` |
| `Metadata` | 读 `metaDataType`；PAGE 型要 `guid`，实体型要 `entityFullName` | 缺 → `PROPERTY_IS_REQUIRED` |

## 四、当前草稿流程的适配实测

微流程 `-6371737850148111694` 共 27 节点，带 `paramType` 的 4 个：

| 节点 | paramType | 值域合法 | 后端必需字段 | 结论 |
|---|---|---|---|---|
| `CREATE_VARIABLE`（创建变量1） | `BASIC` | ✅ | `dataType`=DATETIME | 适配 |
| `CREATE_VARIABLE`（创建变量2） | `OTHER` | ✅ | `otherType`=SYSTEM_PAGE_INFO | 适配 |
| `CREATE_LIST` | `BASIC` | ✅ | `dataType`=BIGINTEGER | 适配 |
| `MAP_OPERATION` | `BASIC` | ✅ | `dataType`=STRING | 适配 |

**不适配节点：0 个。** 现有流程里用到的 3 种（BASIC / OTHER）都在 8 种值域内，且后端必需字段齐全。

## 五、前端「选择数据」下拉的真实分类结构

### 5.1 7 类 radio 的精确值域（bundle 逐字实证 @979714）

```javascript
options:[
  {label:"基本类型", value:"BASIC"},
  {label:"实体对象", value:"ENTITY_OBJECT"},
  {label:"自定义对象", value:"DEFAULT_OBJECT"},
  {label:"选项集", value:"ENUM"},
  {label:"元数据", value:"METADATA"},
  {label:"事件对象", value:"MESSAGE"},
  {label:"其他", value:"OTHER"}
]
```

**7 类全部命中后端 8 种**，唯一没出现在 radio 里的是 `MAP(4)`。

### 5.2 下拉数据的 5 组分类（另一个结构）

下拉列表不是平铺的 7 项，而是按 `group` 分 5 组（bundle 实证）：

```javascript
{ PRIMITIVE: [], COMPOSITE: [], ENUM: [], CTPENUM: [], ENTITY: [] }
```

| group | 内容 | 数据来源接口 |
|---|---|---|
| `PRIMITIVE` | 基本类型（文本/整数/日期…） | 内置常量表 |
| `COMPOSITE` | 自定义对象（DTO）、实体对象、映射 | `fetchUdcMicroflowTreeEntityDto` |
| `ENUM` | 选项集 | 选项集查询 |
| `CTPENUM` | 第三方选项集 | 独立接口 |
| `ENTITY` | 关联实体 | 独立接口 |

`COMPOSITE` 组的构造代码（实测）：

```javascript
n && e.push({key:"DTO", id:"DTO", value:"自定义对象", group:"COMPOSITE", disabled:true})
a && e.push({key:"ENTITY", id:"ENTITY", value:"实体对象", group:"COMPOSITE", disabled:true})
e.push({key:"java.util.Map<String,Object>", id:"java.util.Map<String,Object>",
        value:"映射", group:"COMPOSITE"})
```

注意 `DTO` / `ENTITY` 是 `disabled:true` 的分组节点，真实叶子在其 `children` 里。
`MAP` 类型在这里以 `java.util.Map<String,Object>` 出现，这就是 radio 里没有 MAP 但后端有 MAP(4) 的原因。

## 六、`MicroFlowParamDataTypeEnum` 只有 2 个值

容易和 `ParamTypeEnum` 混淆：

```java
public enum MicroFlowParamDataTypeEnum {
    ENTITY(1, "Entity"),
    DTO(0, "Dto");
}
```

这是**流程级入参**（`MFStartNode.output`）的类型，只有 Entity / Dto 两种。节点级的 `paramType` 才是 8 种。两者不能混用。

## 七、参数页（流程级入参/出参）的 4 类

真实 UI 实测（`参数` 页签）：

```
入参配置：无参数 / 基本类型 / 实体对象 / 自定义对象
出参配置：无参数 / 基本类型 / 实体对象 / 自定义对象
```

对应 `TRIGGER_PARAM_TYPES = (NONE, BASIC, ENTITY_OBJECT, DEFAULT_OBJECT)`。

- `NONE` → `paramType` 不出现
- `BASIC` → 需要 `basic`（STRING/INTEGER/LONG/BIGINTEGER/DECIMAL/BOOLEAN/DATE/DATETIME/OBJECT/DTO/ARRAY）
- `ENTITY_OBJECT` / `DEFAULT_OBJECT` → 需要 `app` + 结构选择

## 八、修复动作

`components/udc/microflow_ui_constraints.py` 已更新：

```python
MAP_PARAM_TYPES  # 5 种 → 8 种（补 METADATA/MESSAGE/OTHER）
PARAM_TYPE_ENUM  # 新增：含 code 与 need_full_name
UI_PARAM_TYPES   # 新增：前端 radio 的 7 类（不含 MAP）
PARAM_TYPE_REQUIRED_FIELDS  # 新增：每种类型后端实际读的字段
```

`tests/test_microflow_ui_constraints.py::test_map_param_types_match_backend_enum`
断言 8 种值域、code 连续 0..7、前端 7 类 = 后端 8 种减 MAP。

## 九、证据链

| 证据 | 路径 |
|---|---|
| 后端枚举 | `docs/audit/artifacts/decompiled/cfr-r31b/com/seeyon/udc/enums/microflow/ParamTypeEnum.java` |
| 流程入参枚举 | 同目录 `MicroFlowParamDataTypeEnum.java` |
| 解析分支 | `.../microflow/domain/bo/flow/activity/CreateVariableActivity.java` |
| 前端下拉分组 | `scratch/array-evidence/bundles/src_redux_store_ts.14dc061e.js` |
| 真实 UI 参数页 | `scratch/datasource-evidence/params-page.json` |
| 草稿流程 schema | `scratch/draft-diagnosis/schema.json` |

**证据等级**：后端枚举 = `VERIFIED_STATIC_BYTECODE`（CFR 反编译）；UI 实测 = `LIVE`；草稿适配检查 = `LIVE`（真实 dataSchema 回读）。
