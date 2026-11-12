# DATA_MAPPING（数据转换）节点契约

取证：CDP 真实建节点 → 目标类型切换 → 实体树选择 → 映射关系弹窗配置 → 后端 dataSchema 回读 → 前端 bundle `eF={group:"base",name:"数据转换",type:"dataMapping"}` 权威定义交叉验证。
证据目录：`scratch/data_mapping-evidence/`。

## 1. 字段与必填（6 项全必填）

| key | 标签 | 类型 | 必填 | 默认值 |
|---|---|---|---|---|
| `selectParam` | 来源数据 | outputSelector（asyncFilter） | ✅ | — |
| `targetType` | 目标数据对象类型 | radio(button) | ✅ | `ENTITY` |
| `app` | 目标数据对象所属应用 | applicationSelector | ✅ | 当前应用 |
| `structure` | 实体对象 / 自定义对象 / 事件对象 | treeListSelector | ✅ | — |
| `mappingRule` | 映射关系 | 自定义弹窗 | ✅ | `null`（显示"未配置"） |
| `title` | 节点出参名称 | outputName | ✅ | — |

目标类型只有 2 种：`ENTITY`（实体对象）/ `DTO`（自定义对象）。

## 2. 映射关系弹窗（核心）

点「未配置」/「数据准备中...」按钮打开「映射关系配置」弹窗（1050×381）。
三个下拉：

| 字段 | 选项来源 | 实测选项 |
|---|---|---|
| 目标对象 | 目标实体的字段列表 | 10 项（创建时间/更新时间/创建人/…/实验文本(已改)/ID/实验枚举字段） |
| 映射方式 | 固定 2 种 | **`值拷贝` / `常量`** |
| 值 | 来源数据的字段列表 | 6 项（与目标同结构时可同名映射） |

映射方式对应后端 `mappingMode`：
- `值拷贝` → **`REFERENCE`**（引用赋值，`value.reference` 指向来源字段）
- `常量` → 应为 `CONSTANT`（`value.constant` 存字面值）

## 3. 后端数据结构（ENTITY + 值拷贝，已回读证实）

```json
{
  "nodeId": "DATA_MAPPING_DSCdJd",
  "type": "ACTIVITY",
  "actionType": "DATA_MAPPING",
  "caption": "数据转换(1)",
  "targetType": "ENTITY",
  "title": "转换列表",
  "dataType": "DTO",
  "app": {
    "appId": "9000000000000000001",
    "appName": "datamigration9000000000000000001",
    "caption": "数据迁移",
    "inApp": true, "udcApp": true, "dynamicDependency": false
  },
  "structure": {
    "key": "com.seeyon...domain.entity.XzhExp950795",
    "id": "com.seeyon...dto.XzhExp950795Dto",
    "label": "小爪实验实体950795V2",
    "dataType": "DTO",
    "entity": "com.seeyon...domain.entity.XzhExp950795",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true,
    "fullName": "com.seeyon...dto.XzhExp950795Dto"
  },
  "selectParam": {
    "description": "查询结果",
    "dataType": "DTO",
    "outputName": "_RETRIEVE_MSwqDF",
    "position": "parent",
    "udcApp": true,
    "dtoType": "MASTER_ENTITY",
    "appName": "datamigration9000000000000000001",
    "path": "comseeyondatamigration...dtoXzhExp950795Dto",
    "id": "com.seeyon...dto.XzhExp950795Dto",
    ...
  },
  "mappingRule": {
    "uuid": "Npg3ptzz4lh5M5jY",
    "id": "com.seeyon...dto.XzhExp950795Dto",
    "caption": "小爪实验实体950795V2",
    "type": "ARRAY",
    "javaType": "com.seeyon...dto.XzhExp950795Dto",
    "mappingRows": [
      {
        "uuid": "OOnL4J2MLvpaUeHJ",
        "targetField": {
          "id": "com.seeyon...dto.XzhExp950795Dto.expText",
          "path": [],
          "name": "expText",
          "desc": "实验文本(已改)",
          "dataType": "STRING",
          "type": "OBJECT",
          "javaType": "java.lang.String"
        },
        "mappingMode": "REFERENCE",
        "value": {
          "reference": {
            "id": "com.seeyon...dto.XzhExp950795Dto.expText",
            "path": [],
            "name": "expText",
            "desc": "实验文本(已改)",
            "dataType": "STRING",
            "type": "OBJECT",
            "javaType": "java.lang.String"
          }
        }
      }
    ],
    "subobjects": []
  },
  "output": {
    "id": "com.seeyon...dto.XzhExp950795Dto",
    "javaType": "com.seeyon...dto.XzhExp950795Dto",
    "dataType": "DTO",
    "type": "ARRAY",
    "desc": "转换列表",
    "appName": "datamigration9000000000000000001",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true,
    "name": "_DATA_MAPPING_..."
  },
  "isCompleted": true
}
```

## 4. 关键认知

1. **`output.type` 是 `ARRAY`**（不是 `OBJECT`）：数据转换产出的是**列表**，
   `output.dataType` 是 `DTO`，`javaType` 是目标 DTO 全名。
2. **`mappingRule.mappingRows[]` 每行三要素**：
   `targetField`（目标字段）+ `mappingMode`（`REFERENCE`/`CONSTANT`）+ `value`（`reference` 或 `constant`）。
   每行都有独立 `uuid`。
3. **`mappingRule.subobjects: []`**：子对象映射单独存，主对象为空数组。
4. **`structure` 与 `selectParam` 是两套独立引用**：
   - `structure` 描述**目标**实体（含 `entity` 域类全名）
   - `selectParam` 描述**来源**节点输出（含 `nodeInfo`/`position`）
5. **`mappingRule.id` 是目标 DTO 全名**，不是节点 ID。
6. **实体下拉是 tree 结构**：DOM 用 `.ant-select-tree-treenode`，
   不是 `.ant-select-item-option`。抓选项必须两个选择器都匹配。
7. **来源数据 `asyncFilter`**：与 CONVERT_DATA 共用 `fetchMicroflowFilterNotVirtual`，
   候选只包含非虚拟 DTO。本次实测 4 个候选（含空项 + 3 个真实输出）。
