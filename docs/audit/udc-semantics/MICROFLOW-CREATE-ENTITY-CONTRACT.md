# CREATE_ENTITY（插入数据）节点契约

取证：前端 addNode(插入数据) → 默认确认捕获必填 → 对象引用/字段映射双分支验证 → 回读 dataSchema。
证据目录：`scratch/insert_entity-evidence/`。

## 1. 默认必填

```
structure    请输入选择实体
mappingType  请输入赋值方式
title        请输入节点出参名称
```
- 出参名字段名是 **`title`**（RETRIEVE 也是 `title`，而 RETRIEVE_ARRAY 是 `variableTitle`）。

## 2. 赋值方式（mappingType）两分支与字段联动

| 赋值方式 UI | mappingType 枚举 | 触发字段 | 说明 |
|---|---|---|---|
| **对象引用** | `"value"` | `param` | 选择前序已有相同类型的 DTO/实体对象（如查询结果） |
| **字段映射** | `"attrs"` | `attrs` | 自定义逐个字段赋值（支持常量、前序变量、表达式） |

## 3. 后端数据结构（已回读证实）

### A. 对象引用 (`mappingType: "value"`)
```json
{
  "actionType": "CREATE_ENTITY",
  "caption": "插入数据(1)",
  "mappingType": "value",
  "title": "新增结果_对象引用",
  "structure": {
    "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto",
    "entity": "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795",
    "label": "小爪实验实体950795V2",
    "dataType": "DTO",
    "dtoType": "MASTER_ENTITY",
    "udcApp": true
  },
  "output": {
    "id": null,
    "dataType": "BIGINTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Long",
    "desc": "新增结果_对象引用"
  },
  "isCompleted": true
}
```

### B. 字段映射 (`mappingType: "attrs"`)
```json
{
  "actionType": "CREATE_ENTITY",
  "caption": "插入数据(1)",
  "mappingType": "attrs",
  "title": "新增结果_字段映射",
  "attrs": [
    {
      "value": {
        "type": "Simple",
        "simple": "小爪测试新建记录",
        "desc": "小爪测试新建记录"
      },
      "attrType": {
        "name": "expText",
        "id": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto.expText",
        "fullName": "com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto.expText",
        "javaType": "java.lang.String",
        "dataType": "STRING",
        "type": "OBJECT",
        "desc": "实验文本(已改)"
      }
    }
  ],
  "output": {
    "id": null,
    "dataType": "BIGINTEGER",
    "type": "OBJECT",
    "javaType": "java.lang.Long",
    "desc": "新增结果_字段映射"
  },
  "isCompleted": true
}
```

## 4. 关键认知与差异对比

1. **出参本质**：`CREATE_ENTITY` 返回的 **不是实体对象**，而是插入后生成的 **主键长整数 ID (`BIGINTEGER` / `java.lang.Long`)**。这与很多开发者的直觉不同（误以为会返回创建后的对象）。
2. **出参命名**：字段为 `title`，提交时受 `configChanged` 保护，更改后确定自动触发 `saveMicroflowSchema(DRAFT)` 落库。
