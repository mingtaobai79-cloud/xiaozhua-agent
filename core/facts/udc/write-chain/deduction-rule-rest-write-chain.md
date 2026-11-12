# 扣减规则写链 REST LIVE（扣除域，此前全库 0 行）

> 端点 `POST /service/udc/deduction/rule`；契约 CFR `udc-common-5.3.517`。
> 结果：`udc_deduction_rule` 0 → **1**，`udc_deduction_algorithm` 0 → **1**；一致性检测无新增（仍 0 ERROR / 9 WARN）。

## 1. 端点面（`DeductionRuleController` @ udc-web，类级 `udc/deduction`，16 端点）

| 写 | 路径 | 说明 |
|---|---|---|
| W | `POST /udc/deduction/map` | 新增扣减关系图 → `SingleResponse<Long>` |
| W | `POST /udc/deduction/map/update` | 更新关系图 |
| W | `POST /udc/deduction/map/delete` / `map/delete/content` | 删图 / 删节点连线 |
| W | **`POST /udc/deduction/rule`** | **新增扣减规则 → `SingleResponse<DeductionResultDto>`** |
| W | `POST /udc/deduction/rule/update` | 更新规则 |
| W | `POST /udc/deduction/rule/delete` | 删除规则 |
| | `GET /udc/deduction/map/{id}`、`map/app/{appId}` | 读关系图 |
| | `POST /udc/deduction/validRule` | **校验规则（先校验后建）** |
| | `POST /udc/deduction/rule/search`、`GET /udc/deduction/rule/{id}`、`POST /udc/deduction/rule/init-data`、`POST /udc/deduction/rule/count` | 读面 |
| | `POST /udc/deduction/entity/list`、`entity-not-exist-ids` | 实体分类/存在性 |

## 2. DTO 契约（逐字段，CFR 实测）

```jsonc
DeductionRuleDto {
  appId, deductionMapId,
  caption*,            // @Length(1,50) @NotNull
  name*,               // @Length(1,30) @Pattern(^[a-zA-Z][0-9a-zA-Z_]*$)  ← 规则编码不能特殊字符
  sourceEntityId, targetEntityId, sourceEndEntityId, targetEndEntityId,
  sourceEntityFullName, targetEntityFullName, sourceEndEntityFullName, targetEndEntityFullName,
  searchCondition,     // JSON 字符串
  extendInfo,
  runtimeModifyState,  // 默认 'ON'（RuntimeModifyStateEnum）
  orderNum,
  searchConditionDtoList*,      // @Size(min=1) @NotNull
  deductionAlgorithmDtoList*,   // @Size(min=1) @NotNull，空则报「未设置算法，请检查」
  deductionRuleDetailDtoList,   // 可空
  extendInfoDto*                // @NotNull，且其 conditionExt 也 @NotNull
}
```

**被校验器逐个逼出来的必填（实测错误链）**：
```
1) No enum constant DeductionAlgorithmOperatorEnum.SUBTRACT   ← 枚举名错
2) extendInfoDto must not be null
3) conditionExt must not be null
→ 补全后 BOOT_0000
```

### 子 DTO

```jsonc
DeductionRuleSearchConditionDto { searchMethod /*默认 'EQUAL'*/, target, source, uuid }
DeductionSimpleFieldDto        { attributeId, attributeFullName, fixedValue }
DeductionAlgorithmDto {
  actionType /*默认 'NORMAL'*/, appId, deductionRuleId,
  caption*(1-50), explanation*(1-255),
  algorithmContent, algorithmContentList* @Size(min=1), code, checkRule, orderNum, extend, extendDto
}
DeductionAlgorithmContentDto { target, source, operatorEnum, uuid }
DeductionRuleExtendInfoDto   { conditionExt* }
DeductionConditionExtDto     { dataNotFoundStrategy /*默认 'ERROR'*/, toast }
```

### 枚举真实值域（★ 我猜错过）

| 枚举 | 实测值 | 说明 |
|---|---|---|
| `DeductionAlgorithmOperatorEnum` | **`PLUS_EQUAL`(0,"+") / `SUBTRACT_EQUAL`(1,"-")** | 不是 `ADD`/`SUBTRACT` |
| `DeductionSearchMethodTypeEnum` | `EQUAL`(1) / `CONSTANT`(2) | |

## 3. 实测成功体（本应用）

```json
{"appId":"8704025620829192834","caption":"小爪扣减规则","name":"xzhDedRule",
 "deductionMapId":"-3894187973392826420",
 "sourceEntityId/targetEntityId/sourceEndEntityId/targetEndEntityId":"474806313816300867",
 "…FullName":"com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795",
 "searchCondition":"{\"type\":\"GROUP\",\"conditions\":[]}",
 "runtimeModifyState":"ON","orderNum":1,
 "searchConditionDtoList":[{"searchMethod":"EQUAL","uuid":"sc-1",
   "source":{"attributeId":"8016904624316689195","attributeFullName":"…XzhExp950795.expText"},
   "target":{...}}],
 "deductionAlgorithmDtoList":[{"actionType":"NORMAL","appId":…,"caption":"扣减算法",
   "explanation":"数量相减","algorithmContentList":[{"uuid":"ac-1",
   "operatorEnum":"SUBTRACT_EQUAL","source":{"attributeId":"5752607439097763430",…},
   "target":{...}}]}],
 "extendInfoDto":{"conditionExt":{"dataNotFoundStrategy":"ERROR","toast":""}}}
→ content = {"validate":true, "id":"-2339240514292888379", "affectCount":1, "existRuleCount":1}
```

**★ 返回体不是裸 Long**：是 `DeductionResultDto = {validate, algorithmToastMap, id, affectCount, existRuleCount}`（我最初按 `content=Long` 解析导致后续 URL 拼接出错）。

## 4. 落库与回读

| 表 | 结果 |
|---|---|
| `udc_deduction_rule` | 1 行（`caption=小爪扣减规则`, `name=xzhDedRule`, `deduction_map_id=-3894187973392826420`, `source/target_entity_id=474806313816300867`, `search_condition` 416 字节） |
| `udc_deduction_algorithm` | 1 行 |
| `udc_deduction_rule_detail` | 0 行（`deductionRuleDetailDtoList` 传空数组） |

回读 `GET /udc/deduction/rule/{id}`：`caption/name` 一致，`searchConditionDtoList` 1 条、`deductionAlgorithmDtoList` 1 条、`extendInfoDto.conditionExt` 完整。

## 5. 一致性检测回归

修改前后均为 **0 ERROR / 9 WARN**（9 条 = 04003×7 + 04009×1 + 08100×1，与本域无关）
⇒ 扣减规则写入**不引入新检错**。

## 6. 复现

`scratch/deduction_create.py`

## 7. 边界（未测）

- `POST /udc/deduction/rule/validRule` 的校验语义（本次未先调它）。
- `deductionRuleDetailDtoList`（单据状态信息 `DeductionBillStatusInfoDto` / `checkRule` / `notice`）未构造。
- `DeductionRuleDetailDto.algorithmCode` 与 `DeductionAlgorithmDto.code` 的取值规则未定。
- 生单规则域（`DataFlowDesignController` @ `udc/data-flow`，24 端点）**未动**：本应用 `udc_data_flow` 1 行原型、`udc_data_flow_mapping` 0 行。
