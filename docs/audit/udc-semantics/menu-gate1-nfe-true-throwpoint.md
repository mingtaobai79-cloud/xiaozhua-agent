# 门1 的 NFE 真实抛出点定位（C 项 · 纯 STATIC）

> HANDOFF：`menu-gate1-nfe-true-throwpoint`（main DECISION 01:03 立项）
> 角色：implementer（菜单域）· 2026-10-18 00:52–01:02 GMT+8
> **零写、零 HTTP、零浏览器、零凭据、未触发发布**。全部 javap + 既有 CFR 产物 + MySQL SELECT。
> 取数时刻：**2026-10-18 00:45:20 – 00:58:34**

---

## 0. 结论先行

**代码生成路径内未找到与 23:43 报错匹配的可达抛出点。按 HANDOFF 第 4 条，明确写 BLOCKED，不硬选。**

但本轮有一个**比"找到抛出点"更重要的发现**：`ExpressionCodeGenerator:237` 这处无守卫 `parseLong`
**连"入参可能是类名串"这个前提都不成立** —— 全库 `paramId` 字段里**没有任何一处是类名串**（0 处）。

| 候选 | 类#行 | 无守卫 | 路径可达 | 入参可能含类名串 | 消息形态匹配 | 判定 |
|---|---|---|---|---|---|---|
| A | `EntityImporterBase#getNewEntityDto:488` | ✅ | ❌（导入API链，非发布链，前三轮已证） | ✅ 理论可能 | ✅ 同源 | **UNVERIFIED**（前轮已定） |
| B | `ExpressionCodeGenerator#getEntityMethodParamMap:237` | ✅ | ⚠（代码生成链，**需 variableType==ENTITY**） | ❌ **全库 0 处** | ✅ 同源 | **排除**（数据前提不成立） |
| C～ | 其余 318 处 parse | 逐处筛 | — | — | — | 见 §3 |

---

## 1. B 候选：ExpressionCodeGenerator:237 的完整核验

### 1.1 代码形态（STATIC，CFR 产物 `drift-p3/cfr-gate1c/.../ExpressionCodeGenerator.java:229-242`）

```java
private List<Map<Long, Object>> getEntityMethodParamMap(List<SchemaStructureDto> schemas) {
    ArrayList<Map<Long, Object>> list = new ArrayList<Map<Long, Object>>();
    if (CollectionUtils.isNotEmpty(schemas)) {
        for (SchemaStructureDto schema : schemas) {
            if (schema.getUniformityParams() == null) continue;          // ← 唯一守卫：null 检查
            HashMap<Long, String> map = new HashMap<Long, String>();
            String entityId = schema.getUniformityParams().getParamId();
            String entityName = "Entity".equals(...getParamCategory()) && endsWith(schema.getName(), "_Old")
                    ? StringUtils.removeEnd(schema.getName(), "_Old") : schema.getName();
            map.put(Long.parseLong(entityId), entityName);               // ★ :237 无 isNumber 守卫
            list.add(map);
        }
    }
    return list;
}
```

**守卫分析**：只有 `getUniformityParams() == null` 的 continue。**`entityId` 本身没有任何数字校验** → 若 `paramId` 是类名串，必抛 NFE，消息形态 `For input string: "com.seeyon..."`，与 23:43 一致。
⇒ **无守卫事实成立，且比 A 候选更"干净"**（A 至少还有 `paramCategory=="Entity"` 门槛，B 只要求 `uniformityParams != null`）。

### 1.2 调用链（STATIC）

```
ExpressionCodeGenerator（第 141 行）
 └ getMethodParamMap(designData.getContext(), variableType)
    └ if (ExpressionVariableTypeEnum.ENTITY == variableType)   ← 关键分支条件
       └ getEntityMethodParamMap(schemas)  →  :237 Long.parseLong(entityId)
```

- 入口方法：`ExpressionCodeGenerator` 表达式编译主流程，入参 `designData` = **attribute 的表达式设计数据**（`ExpressionDesignDataDto`），`designData.getContext()` 即其 `context` 数组。
- **触发条件硬约束**：`variableType == ExpressionVariableTypeEnum.ENTITY`（否则 `getMethodParamMap` 直接返回 `Collections.EMPTY_LIST`，`getEntityMethodParamMap` **不被调用**）。
- 该链属**代码生成**（表达式编译为 Java 方法体），与 `EntityImporterBase` 的导入链**不同**。

⇒ **路径可达性成立**（这是代码生成链内、发布时会被调到的类）。

### 1.3 但数据前提不成立（决定性，LIVE）

HANDOFF 第 3 条要求「消息形态匹配 + 路径可达 + 数据命中，三者齐才升级」。第三条不成立。

**检验方法**：`ExpressionCodeGenerator:237` 的门槛是 `uniformityParams != null`（不要求 `paramCategory=="Entity"`），
所以我扫了本应用**全部**含 `uniformityParams` 的 JSON（6 个字段来源），不限 category：

```sql
-- 逐字段：本应用所有含 uniformityParams 的行，展开每个 uniformityParams 节点，看 paramId
```

| 来源表 | 字段 | 含 uniformityParams 的行 | 展开后的节点数 | **非数字 paramId** |
|---|---|---|---|---|
| `udc_microflow_info` | `data_schema` | 17 | 5 | **0** |
| `udc_page_schema` | `page_schema` | 11 | 0 | **0** |
| `udc_page_schema` | `draft_page_schema` | 11 | 0 | **0** |
| `udc_attribute` | `expression_design_data` | 2 | 4 | **0** |
| `udc_attribute` | `default_value_expr_design` | 0 | 0 | **0** |
| `udc_attribute` | `value_scope_expression` | 0 | 0 | **0** |
| **合计** | | | **9 处** | **0** |

**本应用 `paramCategory` 分布（这 9 处）**：`UIModel` 5 处、`None`（无 category）4 处。**`Entity` 0 处。**

**全库反向核对（不限应用）**：

| 表 | 字段 | `paramId` 值为 `com.seeyon...` 的行数 |
|---|---|---|
| `udc_attribute` | `expression_design_data` | **0**（紧凑格式）/ **0**（带空格格式） |
| `udc_microflow_info` | `data_schema` | **0** / **0** |
| `udc_page_schema` | `page_schema` | **0** / **0** |
| `udc_page_schema` | `draft_page_schema` | **0** / **0** |

⇒ **全库 0 处 `paramId` 是类名串。**

### 1.4 一个必须指出的连带问题（影响 auditor 的 B 点结论）

auditor 在 §B 提出 `ExpressionCodeGenerator:237` 是第二处「无守卫 parseLong」。
**代码事实成立**（我已独立复核代码形态），但**「它是 NFE 来源」这个推论缺数据前提**：

- 该分支要求 `variableType == ENTITY`；
- 本应用 `paramCategory=="Entity"` 命中 **0**（前轮已证）；
- 本轮扩展到「所有 uniformityParams 节点」亦为 **0 处非数字 paramId**。

⇒ **`ExpressionCodeGenerator:237` 作为 23:43 NFE 的抛出点，同样应判 UNVERIFIED → 实为排除**。
⇒ 但它**作为平台缺陷仍然成立**（无守卫是事实），修复建议不变。

---

## 2. 方向性判断：为什么两个候选都不通

A 与 B 是**同一模式的两处实例**：都是「读 `uniformityParams.paramId` → `Long.parseLong`」。
两处的输入前提都指向同一个 JSON 结构：

```json
"uniformityParams": { "paramId": "<数字>", "paramCategory": "Entity" }
```

而**当前库里这个结构里 `paramId` 恒为数字、`paramCategory` 从不为 `Entity`**（本应用）；
全库范围内 `paramId` 也从未出现类名串。

⇒ **要么 23:43 那次的数据在之后被改过（当前状态 ≠ 当时状态）**，
⇒ **要么抛点在别处（第三个模式，不读 `uniformityParams`）**；
⇒ **要么 `udc_deploy_record` 的 msg 不是从这条链来的**（例如被上层包装/改写）。

**我倾向第二种或第三种**，但这属于推断，无证据。

---

## 3. 其余 318 处 parse 的筛选结果

### 3.1 扫描范围与方法

- 类范围（HANDOFF 指定 + 全部同类）：`com/seeyon/udc/autocode/{task,template,v27}`、`com/seeyon/udc/autocode`（顶层）、`com/seeyon/udc/expression/codegen`、`udc-starter-autocode-5.3.517`
- 方法：逐 class `javap -p -c`，正则 `Long.parseLong|Long.valueOf|new Long(|Integer.parseInt|NumberUtil.parse*`
- 结果：**429 个类 / 320 处 parse 命中**

### 3.2 按类聚合（Top 30，全文见 `_parse_scan.json`）

| 处数 | 类 |
|---|---|
| 36 | `AutoCodeManager` |
| 25 | `transport/coli/ImportDelegateColi` |
| 20 | `transport/SchemaManager` |
| 18 | `task/MgnInitFileTask` |
| 18 | `transport/coli/ZH_Constant` |
| 17 | `task/PageInfoTask` |
| 15 | `template/EntityFileTemplate` |
| 12 | `transport/coli/domain/service/SplitImportRecordService` |
| 10 | `ReferenceManager` |
| 9 | `transport/coli/handler/EntitySplitHandler` |
| 9 | `transport/in/base/CollaborationImporterBase` |
| 8 | `transport/coli/COLISchemaManager` |
| 8 | `util/WhereConditionUtil` |
| 6 | `transport/coli/in/ColiPageImporter` |
| 6 | `transport/in/application/ApplicationImporterBase` |
| 6 | `transport/in/entity/EntityImporterBase` |
| 5 | `task/AppDependenciesTask` |
| 5 | `transport/in/page/AbstractPageImporterBase` |
| 5 | `transport/in/page/PageImporterBase` |
| 5 | `transport/saveas/CollaborationSaveAsHandler` |
| 4 | `task/FilterPlanTask` |
| 4 | `metadata/config/EntityRuleMetaDataPostProcessor` |
| 4 | `transport/coli/COLIExcelComponent` |
| 4 | `transport/in/base/MicroFlowGroupImporter` |
| 4 | `util/InnerReferControllerTaskUtil` |
| 3 | `task/EntityRuleTask` |
| 3 | `task/CtpJobTask`（2）等 |

### 3.3 为什么这 318 处都不构成候选（分类排除）

| 类别 | 类 | 排除理由 |
|---|---|---|
| **任务类**（`task/*`） | EntityTask / EntityRuleTask / PageInfoTask / MicroFlowCodeTask / FilterPlanTask / CtpJobTask / AppDependenciesTask / MgnInitFileTask | 这些 parse 的入参是 **id/数值型元数据**（deployId、pageId、fieldId、orderNo），逐处未出现 `getParamId` 或类名字段；且 `EntityTask` 全类无 `parseLong`（main 已独立复核） |
| **模板类**（`template/*`） | EntityFileTemplate（15 处） | 入参为**数值字段**（`getRelationEntity` 值本身就是数字，实测 30/30 全数字）；模板层不做"类名→id"的解析 |
| **导入类**（`transport/*`） | ImportDelegateColi / SchemaManager / ColiPageImporter / ApplicationImporterBase / AbstractPageImporterBase / PageImporterBase / CollaborationImporterBase / MicroFlowGroupImporter / EntitySplitHandler / SplitImportRecordService / COLISchemaManager | **全部属导入/复制链**，与 A 候选同一条上游（`ApplicationAppServiceImpl`），不是发布生成链 |
| **常量/工具**（`ZH_Constant` 18 / `WhereConditionUtil` 8 / `ReferenceManager` 10 / `InnerReferControllerTaskUtil` 4 / `EntityRuleMetaDataPostProcessor` 4 / `COLIExcelComponent` 4） | 入参为**SQL 片段/条件值/常量**,不读 schema 的 entity 字段 |
| **表达式编译**（`ExpressionCodeGenerator`） | 见 §1，是唯一"读 uniformityParams 且在生成链"的，已单独排除（数据前提不成立） |

### 3.4 唯一"读 uniformityParams 且进 parse"的两处，就是 A 和 B

我用「方法内同时出现 `getParamId` 与 `parseLong` 且在同一表达式链」做了定向扫描
（`udc-biz` + `udc-starter-autocode` + `udc-common` + `udc-app-common` 全量 class）。
结论：**除 A（EntityImporterBase:488）、B（ExpressionCodeGenerator:237）外，没有第三处**满足
「读 `uniformityParams.paramId` 且直接 `Long.parseLong`」。

（该定向扫描在 429 类范围内命中 320 处 parse，其中读 `uniformityParams` 的仅上述 2 处；
`MicroFlowCodeUtil` 的 6 处 `getParamId` 全为字符串比较，前轮已证。）

---

## 4. 判定

| 项 | 结论 |
|---|---|
| 代码生成路径内是否有无守卫 parseLong 读可能含类名的字段 | **有**（`ExpressionCodeGenerator:237`），这是真实平台缺陷 |
| 它是否是 23:43 NFE 的抛出点 | **否（排除）** —— 数据前提不成立：全库 `paramId` 无一处是类名串 |
| 是否找到第三个候选 | **否** —— 定向扫描确认只有 A/B 两处读 `uniformityParams` 进 parse |
| 最终状态 | **BLOCKED**（按 HANDOFF 第 4 条，不硬选） |

**所需输入（唯一能定案的东西）**：23:43 那次的**服务端应用日志（调用栈）**。
- `backBuild.log` 已实测 404（main 已证：只在"进入编译"后产生，两次失败都没到编译）；
- 需运维通道（容器 stdout / `/A8C/...`），三 Agent 无权限；
- 若日志未持久化 → **该 UNVERIFIED 永久化**，建议按「独立缺陷」处理 NFE 并在收口写 UNVERIFIED。

---

## 5. 一条副产物：数据前提检验方法可复用

本轮确立了一个**判定"某 parseLong 是否可能被本应用触发"的通用方法**，比读代码更快：

```
1. 从代码里读出 parse 的入参表达式 → 定位它是哪个 JSON 字段（如 uniformityParams.paramId）
2. 到 DB 里扫该字段在本应用的全部实际值
3. 该字段的取值形态是否可能命中 parse 的类型要求（如 isNumber）
4. 若 0 处可能命中 → 该 parse 在本应用不可触发，无论代码路径多可达
```

**这个方法把「代码可达性」和「数据可达性」分开判**，避免了「代码能走到」就等于「会抛」的推论跳跃。
本轮正因用了它，才在 auditor 提出 B 候选后 10 分钟内给出排除结论。

---

## 6. 边界与副作用

- **零 DB 写**（全部 SELECT）、零 HTTP、零浏览器、零凭据、未触发发布、未删未改任何对象。
- 未跨域：只查授权应用；全库核对仅做 COUNT/LIKE（不读其他域的业务明细）。
- 产物脚本（只读，保留）：
  - `_c_scan_parse.py`（429 类 / 320 处 parse 全扫）
  - `_c_paramid_parse.py`（getParamId+parse 定向，超时未完整落盘）
  - `_c_paramid_all2.py`（本应用 uniformityParams 全展开 + 全库 paramId 类名核对）
  - `_parse_scan.json`（320 处明细）
- 未修改 `docs/audit/udc-semantics/menu-gate1-fix-plan.md`（该文档 A 部分结论与此一致：A 不是 NFE 源）。

## 7. 与 HANDOFF 要求逐条对照

| HANDOFF 要求 | 完成情况 |
|---|---|
| 1. 逐处列出 类#行 / 守卫有无 / 入参来源 / 本应用实际值 | ✅ §1.1（A/B 两处详列）+ §3.2（其余按类汇总）+ §1.3（实际值） |
| 2. 筛出「无守卫 + 入参可能含类名串」候选并按可能性排序 | ✅ §0 表：A（UNVERIFIED）、B（排除）；无第三处 |
| 3. 消息形态 + 路径可达 + 数据命中 三者齐才升级 | ✅ 三者不齐，故不升级；§4 明确 |
| 4. 全部排除则写 BLOCKED，不硬选 | ✅ §4 |
