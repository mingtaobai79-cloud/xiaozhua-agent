# C-7C（修订）｜FQN 在 ID 型列的定位

2026-10-19｜test2｜app 8704025620829192834｜零写

## 0. 修订声明（推翻原报告）
原结论「**未命中 / 库内无静态错值**」**撤回**：原扫描把 `udc_reference`/`udc_resource`/`udc_microflow_info`/`udc_deduction_*` 判为「不存在」整表跳过 —— **误判**，实际全部存在（83033/6995/4767/1/1 行）⇒ 原「运行时拼装」依据失效，改标 **待验假设**。

## 1. 补扫命中（本 app）
| 表.列 | 命中 | 语义 |
|---|---|---|
| **udc_reference.reference_id** | **3** | **ID 语义列 varchar(100) 承载 FQN** |
| udc_resource.entity_full_name | 8 | fullName 位 |
| udc_microflow_info.data_schema | 7 | JSON 全名槽 |
| udc_deduction_rule.{source,target}{,_end}_entity_full_name | 各 1 | fullName 位 |
| udc_deduction_rule.search_condition | 1 | 文本 |
| udc_deduction_algorithm.algorithm_content | 1 | 文本 |

## 2. udc_reference.reference_id 详查
列：`...app_id, reference_id varchar(100), reference_type smallint, source_id, source_type`

| 形态 | rt | 行数 | 值 |
|---|---|---|---|
| 数字 ID | 1 | **9** | `474806313816300867` |
| **FQN** | 1 | **3** | `com.seeyon...domain.entity.XzhExp950795` |
| 数字 ID | 22 | 3 | `474806313816300867` |

3 行 FQN（全 2026-10-16）：`-2568064509606509084` 04:06:04 / `8584012646946208371` 08:38:07 / `5500622452836132193` 21:59:56，rt 均 1。

**全库分布（仅描述，不作正常/异常判定）：**
- rt=1 全库：数字 **6307** / FQN **10848** / 计 17738
- rt=1 `LIKE %OrgMember%`：**5165**；精确 `OrgMember`：**5161**（差 4=Metadata/Post/Dto 变体）

**边界声明**：`reference_type` 语义**未验证** ⇒ **不得据分布断言该列对本案「正常」或「异常」**，也不得推根因。已知仅：本 app 内本案实体同时存在数字 ID（rt=1:9 / rt=22:3）与 FQN（rt=1:3）；**语义待确认**。

## 3. log_details 重扫（app_id 索引过滤）
本 app **778** 行(0.17s)；含实体名 207(0.32s)；含**精确实体 FQN** **155**(0.33s)。原 8s 超时**可避免**。

**键级统计（分两层）：**
| 层 | `id` | `dataFieldId` | `paramId` |
|---|---|---|---|
| **精确实体 FQN** | **0** | **0** | **0** |
| **DTO 级 FQN** | **3252** | **2** | **6** |

DTO 合计 **3260**（全名 2128 + 字段 1110 + 其他 14）；结论仅限「精确实体 FQN」层。`udc_microflow_info.data_schema` 另有 DTO-FQN `id` **169**（全名 98 / 字段 71）。

**语义限制**：DTO 名在**类型描述符** `id` 位，同结构并存 `type=ARRAY`/`nodeType=FORM`、`dataFieldId=...Dto.expText`、`dataField=expText`，且与 `relationEntity` 数字 ID 并存 ⇒ 只能写「DTO 类型名出现在 `id` 键」，**不得写「ID 槽错值」**。

**精确 FQN 落键（样本 5）**：`relationEntityFullName`（同结构 `relationEntity` 为数字）、`structure.key`、`entityObject.key` —— 均全名键 ⇒ **无「ID 键载值」形态**。

## 4. 结论（边界收紧）
1. **已证**：库内确有 ID 语义列承载**精确实体 FQN** —— 仅 `udc_reference.reference_id`（3 行，本 app）；其余命中列属 fullName 或文本。
2. **不作判定**：rt=1 分布（6307/10848）仅描述；`reference_type` 语义未验证 ⇒ 不断言对本案正常或异常。
3. **已证（限定层）**：精确实体 FQN 在该三键 **= 0**；DTO 级 FQN 共 **3260**（见 §3），属类型描述符，**不得写成「ID 槽错值」**。
4. **撤回**：原「库内无静态错值 ⇒ 运行时拼装」两条前提均塌（库内有 ID 语义列含精确实体 FQN；「4 秒时序」已在 C-7B 作废，本报告误继承）。
5. **待验假设**：运行时拼装仅为候选，未验证。
6. **未推出**：reference 3 行 FQN ≠ 根因，不得推为需修复配置。

## 5. 未扫 / 未取证
`udc_micro_flow_group`(265) 文本列仅 backup_code/owner_code/caption，无命中；`reference_type` 语义未取证(rt=1/22/3/4)，需平台契约。

## 6. 行为声明
零库写/页面/REST/发布；仅 SELECT。
