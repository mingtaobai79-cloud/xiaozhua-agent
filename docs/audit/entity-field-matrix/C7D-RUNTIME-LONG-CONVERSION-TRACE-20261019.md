# C-7D｜后端生成阶段 Long 转换路径追踪（STATIC）

2026-10-19｜**纯静态只读**：未触 test2、未请求页面/API、未跑沙箱、未改数据

## 结论
**未定位到**能把本案实体级 FQN `com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795` 送入 `Long.parseLong` 的具体代码点。
已排除 3 条候选路径（均有守卫或数据不匹配）；本机**无代码生成器完整实现**（仅模板 + 部分反编译），残余路径无法静态确证。

## 1. 已查范围（本机实存）
| 位置 | 内容 |
|---|---|
| `docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/**` | CFR 反编译 udc-biz（5.3.517 族） |
| `docs/audit/artifacts/scratch-migrated/cfr-r30/biz/autocode/JAVA/{2.7,2.9}/templates` | FTL 模板 125/141 个 |
| `docs/audit/modules/decompiled/` | facade 层，无 codegen |
| `docs/audit/artifacts/udc-biz-5.3.517/_codegen_templates.json` | 模板**文件名清单**（非内容） |

**不存在**：`AbstractDeployService`（日志中的类）、完整 pipeline/codegen jar。本机 `*udc*.jar` 仅 `udc-web-5.3.517.jar`，且为 **9 字节 pytest 占位文件**。

## 2. 候选路径逐条排除（全部 STATIC）
### 候选 A：`EntityFileTemplate.resolveEntity()` — **有守卫，排除**
`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/autocode/template/EntityFileTemplate.java:793-800`
```java
if (NumberUtil.isNumber(relationEntity)) {
    String name = this.entityMetadata.get(Long.parseLong(field.getRelationEntity())).getName();
```
`expMembers.relation_entity` = `com.seeyon.organization...OrgMemberMetadata` → `isNumber=false` → 走 else 分支，**不进 parseLong**。

### 候选 B：`EntityFileTemplate.getJavaType()` — **数据不匹配，排除**
同上文件 `:430`（ENUM 分支，仅校验 relationApp 未校验 relationEntity，形态上可炸）
本案该实体 `data_type='ENUM'` 字段 **0 条**（只有 1 条 CTPENUM，其 relation_entity=`4456389269786582653` 为数字）。
全库 `ENUM 且 relation_entity 非数字` = **0 行**。

### 候选 C：`PageEntityControllerTask.handleRelationEntityDtoFullName()` — **条件不匹配，排除**
`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/autocode/task/PageEntityControllerTask.java:1946`
```java
boolean inApp = isBlank(getRelationApp()) || isNumber(getRelationApp());
String dtoFullName = inApp ? entityDtoMap.get(Long.valueOf(relationEntity)).getDtoFullName() : outSideEntityDtoFullNameMapping.get(relationEntity);
```
本案 6 个 ENTITY 字段 `relation_app` **全部 = `organization`**（非空非数字）⇒ `inApp=false` ⇒ 走 else，**不进 valueOf**。
反查「`inApp=true` 且 relation_entity 非数字」的本案字段 = **0 条**。

## 3. 其余 parseLong 点
`ReferenceManager:665` / `FilterPlanTask:101` / `EntityRuleTask:180` 等，调用前均有 `isNumberTypeByString`/`isNumber` 守卫，或作用于 `drivenEntity`/`datasourceId`，非本案实体 FQN。

## 4. 与 C-7C 的映射判断
**不能映射。** 理由：
- C-7C 的 `udc_reference.reference_id` 3 行 FQN，`reference_type` 语义**未验证**，无法断定其参与 codegen 读取。
- 上述候选路径读的是 `AttributeDto.getRelationEntity()`（来自 `udc_attribute`），**不是** `udc_reference.reference_id`。
- 未发现 `udc_reference` 被 `autocode` 包内 parseLong 路径直接消费的证据。
⇒ 属**同名形态相似**，不认定关联。

## 5. 判定
- 本任务：**BLOCKED（局部）** — 缺代码生成器完整实现（该 app 5.3.517 的 `udc-biz` 完整 jar 或 `AbstractDeployService` 所属 artifact）。
- 已排除 3 条，非「无任何可能」，而是「本机证据不足以下结论」。
- 需 main 单独裁定：是否授权获取/反编译缺失 artifact（**涉及环境外取物，非我自行执行**）。

## 6. 未做
未运行沙箱、未请求 test2、未改任何数据/配置、未扩扫全库、未推根因。
零库写、零页面、零 REST、零发布。
