# 实体更新（udcEntityUpdatePost）权威 payload

> 来源：2026-10-24 在实体「基本」tab 勾选 openAPI 四个复选框 + 确定，**抓页面真实请求**得到。
> 证据等级：LIVE（页面自己发、返回 `BOOT_0000 content=1`、复选框回显 ✓）

## 铁律

- `category` 必须传字符串枚举名 `ENTITY`，传 DB 里的数字 `0` 直接 `BOOT_3000`（`message` 恒为 null）
- `multiplicity` 必须传 `ONE2MANY`，`stereotype`/`features` 传枚举名，`preset`/`permission` 传布尔
- DB 里存的是数字是**存储形态**，接口要的是**枚举名**，照 DB 传必挂
- `customScalabilityId` 才是 UI「扩展实体」槽位，传方案 id 会自动生成影子实体 `<name>Ext`
- `scalabilityOptionId` 是另一槽位，清空要传字符串 `"0"`
- `openApiData` 是逗号分隔字符串，四个复选框对应 20 个接口
- `BOOT_0000` + `content=1` 不够，必须回页面看复选框与下拉是否回显

## 1. 完整 body（逐字）

```json
{
  "caption": "验收实体-全字段类型",
  "name": "ysTypesAll",
  "stereotype": "standard",
  "features": "basic",
  "entityGroupId": "-6060304108904679308",
  "permission": false,
  "openApiData": "create,createBatch,create4bpm,deleteById,deleteByIds,deleteByComplexConditions,update,updateBatch,update4bpm,selectCascadeById,selectCascadeByIds,selectById,selectByIds,selectCountByConditions,selectPageByConditions,selectListByComplexConditions,selectPageByComplexConditions,selectCountByComplexConditions,selectAllChildren,selectListFuncByComplexConditions",
  "entityGroup": "验收目录",
  "parentEntityId": "0",
  "attributeSetIds": "2490259262299963129",
  "category": "ENTITY",
  "superior": 0,
  "orderNo": 0,
  "preset": false,
  "multiplicity": "ONE2MANY",
  "tableName": "ystypesal_6590234594323325264",
  "id": "-1516209680943439395",
  "appId": "8704025620829192834"
}
```

## 2. ★ BOOT_3000 的根因：枚举字段要「字符串枚举名」，不是数字

| 字段 | 正确 | 错误（→ BOOT_3000，message 恒为 null） |
| --- | --- | --- |
| `category` | `"ENTITY"` | `0` |
| `multiplicity` | `"ONE2MANY"` | `1` |
| `stereotype` | `"standard"` | — |
| `features` | `"basic"` | — |
| `preset` | `false` | — |
| `permission` | `false` | — |

DB 里 `category=0`、`multiplicity=1` 是**存储形态**，接口要的是枚举名 —— 照 DB 传必挂。

## 3. 高级设置两个槽位

| 字段 | 含义 | 效果 |
| --- | --- | --- |
| `customScalabilityId` | UI「扩展实体」 | 传方案 id → 自动生成影子实体 `<name>Ext` |
| `scalabilityOptionId` | 另一槽位 | 传 `"0"` 清空 |

LIVE：带 `customScalabilityId` 更新后自动生成 `ysTypesAllExt`（`验收实体-全字段类型扩展`）。

## 4. openAPI 四个复选框 ↔ 20 个接口

```
创建 = create, createBatch, create4bpm
删除 = deleteById, deleteByIds, deleteByComplexConditions
更新 = update, updateBatch, update4bpm
查询 = selectCascadeById, selectCascadeByIds, selectById, selectByIds,
       selectCountByConditions, selectPageByConditions,
       selectListByComplexConditions, selectPageByComplexConditions,
       selectCountByComplexConditions, selectAllChildren,
       selectListFuncByComplexConditions
```

`openApiData` 是**逗号分隔字符串**，不是数组。

## 5. 判定标准

`BOOT_0000` + `content=1` **不够** —— 必须回页面看复选框/下拉是否回显。
本实体曾出现「DB `open_api_data` 有值但页面全空」，根因是写入时 `category` 用错导致整条 update 被拒（`BOOT_3000`），而此前某次用极简 body 写入只落了 DB 字段、没走完实体保存链。
