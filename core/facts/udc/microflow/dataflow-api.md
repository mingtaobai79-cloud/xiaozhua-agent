# 执行生单规则节点 —— 接口链路（用户贴 body，2026-10-25）

链路（用户口述：先加载实体列表 → 选实体 → 加载实体元数据/DTO → 选生单规则(按实体查)）。

## 1. 选来源实体 → udcMetaDataSelectEntityByAppIdAppGet

元数据选实体（按 appId 拿实体列表）。body 未贴全，接口名已确认。

## 2. 实体 → DTO（获取实体元数据）→ udcMicroflowFindDtoByEntityPost

variables:
```json
{"appId":"9000000000000000001",
 "appName":"datamigration9000000000000000001",
 "entityFullName":"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795"}
```
返回 content：`caption, entity, fullName, dtoType, udcApp, attributes, type`
- `entityFullName` = 实体的 fullName（domain.entity 包）。
- 返回的 `attributes` = 实体字段列表，`fullName` = 对应 DTO fullName。
- 这是「实体 → DTO + 字段」的桥接接口（比 FindCustomDtoPost 多 entity 维度）。

## 3. 选生单规则 → udcDataFlowListManuallyMappingPost

variables:
```json
{"appId":"9000000000000000001","sourceEntityId":"474806313816300867"}
```
返回 content：`appId, appUrl, caption, id, name, sourceEntityId`
- 按 `sourceEntityId`（来源实体 id）查可用的生单规则（数据流）列表。
- 生单规则是「手动映射」类数据流（ManuallyMapping）。

## 4. 选自定义对象 → udcMicroflowFindCustomDtoPost（复用）

variables:
```json
{"appId":"9000000000000000001","appName":"datamigration9000000000000000001",
 "dtoFullName":"com.seeyon.datamigration9000000000000000001.dto.XzhExp950795Dto","needChildren":false}
```

## 数据来源方式两态

- 查询数据：按「过滤条件」查实体数据，批量执行生单规则。
- 选择数据：引用「来源实体数据」（前序节点的实体变量）。

## 关键结论（用户强调：生单规则也是查询出来的）

生单规则列表不是静态的，是按「来源实体 sourceEntityId」动态查询出来的
（`udcDataFlowListManuallyMappingPost`）。所以生成器必须先拿到来源实体的 id，
再查生单规则列表，不能凭空写规则 id。
