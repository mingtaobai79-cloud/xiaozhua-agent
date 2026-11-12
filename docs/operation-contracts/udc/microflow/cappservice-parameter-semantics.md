# CALL_APP_SERVICE 节点「服务参数」语义契约

> 环境：test2（`lowcode-test2.example.com`），租户 `-8112660841495312922`
> 目标应用：`datamigration9000000000000000001`
> 切片：B-3（P2 纯读）。**写操作 0 次**，`/service` 请求 **0 次**（全部走 DB 只读 + 已落盘样本 + 反编译）
> 分级：**[SAMPLE]** 真实样本回读 / **[LIVE-DB]** 本会话 DB 直查 / **[STATIC]** 字节码反编译 / **[VACUUM]** 完备负证据 / **[UNVERIFIED]** 未取证

---

## 0. 一页结论

| # | 断言 | 等级 | 证据 |
|---|---|---|---|
| C1 | `selectMethod.fullName` = `implClass + "." + methodName`，是全链路唯一稳定的方法标识 | SAMPLE + LIVE-DB | 样本 12/12、全库 36/36 节点实现类前缀一致（§2.1） |
| C2 | `selectMethod.md5` 是**元数据（契约）快照指纹**，不是方法稳定标识；**禁止**用它做跨时间等值匹配 | STATIC + LIVE-DB | `MfAppServiceMethodDto.md5` 注解原文「元素据md5」；同一 fullName 存在 3 个 md5（§2.2） |
| C3 | `parameter.type` / `returnValue.type` 是**传输载体的全限定类名**，取值域有限的 5 个（§3.1） | LIVE-DB | 全库 345 节点分布（§3.1） |
| C4 | `node.output.id == returnValue.item.itemType`，在 DTO/对象型返回时恒成立；`PageResponse` 属唯一例外（`PageResponse.` 前缀，**平台级与否 UNVERIFIED**） | LIVE-DB | 270 命中 / 6 例外（同源）/ 69 简单类型不适用（§3.3） |
| C5 | `node.output.type` 与 `returnValue.type` 一一映射：`SingleResponse→OBJECT`、`ListResponse→ARRAY`、`PageResponse→OBJECT` | LIVE-DB | 345 节点类型配对数（§3.2） |
| C6 | `parameter.item` / `returnValue.item` 的键集是**稀疏序列化**结果，出现 `javaType/dataType/keyType` 表示该 DTO 为 UDC 应用内自建类型 | STATIC + LIVE-DB | `MfItemDto` `@JsonInclude(NON_NULL)`；富键集参数侧 **1** 条 + 返回侧 **1** 条，均属本应用唯一自建 AppService（§3.4） |
| C7 | `node.output.id` 为空不代表配置错误：简单类型（`java.lang.*` / `java.util.*`）返回时平台不写该键 | LIVE-DB | 69 条简单类型节点 `output.id=null`（§3.4） |

---

## 1. 节点与契约的结构关系

```
udc_microflow_info.data_schema (JSON)
  └─ nodes[] (含递归容器)
       └─ {actionType:"CALL_APP_SERVICE", nodeId, output{...}, selectMethod{...}, mappingType, attrs[]}

udcMicroflowSearchAppServiceByAppNamePost  (契约面, GET 候选列表)
  └─ [{fullName(类级), md5, caption, methods:[{fullName(方法级), md5, parameter, returnValue, available, appType}]}]
```

**样本池覆盖声明（D8 第 1 点）**：`real_CALL_APP_SERVICE.json` 共 12 条，覆盖 4 个**他应用** appId，
**目标应用 `8704025620829192834` 0 条** → 该池只支撑「平台通用形态」。本文所有涉及本应用的断言，
均改用本应用 LIVE 数据：`udc_microflow_info` 47 条中仅 **3** 个 `actionType=CALL_APP_SERVICE` 节点
（分布在 2 条微流程，其中 `CALL_APP_SERVICE_pfQeP7` 只有 `nodeId/type/actionType` 三键、`selectMethod` 缺失=空壳）。
产物：`docs/audit/artifacts/udc-node-evidence/b3-target-app-CALL_APP_SERVICE.json`。

两类契约条目形态（LIVE，本应用 13 条）：

| 形态 | 条数 | 特征 |
|---|---|---|
| 应用级类条（11） | 11 | 只有类级 `fullName` + `md5`，**无 `methods[]`** → 方法级契约须另行按类取 |
| 容器条（2） | 2 | `FileAppService` / `FormServiceProxy`，带 `methods[]`，每条含 `parameter`/`returnValue`/`appType` |

> 容器条的两个 `MicroFlowAppServiceImpl` 条目 `md5` 为**缺失**（非 null 字符串，键不存在）——属平台微流程类，可解释缺省。

---

## 2. fullName 与 md5 的真实语义（本切片核心）

### 2.1 fullName = 实现类全限定名 + "." + 方法名

**[SAMPLE]** 12/12 样本、**[LIVE-DB]** 本应用 2/2 有效节点，均满足 `fullName == implClass + "." + 方法名`：

```json
{ "fullName": "com.seeyon.datamigration9000000000000000001.appservice.XzhExp950795AppServiceImpl.selectById",
  "implClass": "com.seeyon.datamigration9000000000000000001.appservice.XzhExp950795AppServiceImpl",
  "interfaceClass": "com.seeyon.datamigration9000000000000000001.api.XzhExp950795AppService" }
```

`implClass` = 实现类，`interfaceClass` = Dubbo 接口类（两者可不同：`FormServiceProxy` 即代理实现）。
全库 345 个非空 `selectMethod` 节点的 `implClass` 均为 `fullName` 的严格前缀 → **345/345 无例外**。

### 2.2 md5 是元数据快照指纹，**不是**稳定标识（已被反证）

**[STATIC]** `docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/microflow/dto/metadata/MfAppServiceMethodDto.java`

```java
@DtoAttribute(value="元素据md5")     // 原文注解，L29-30
private String md5;
```

字段名是 md5，但**注解语义是"元数据 md5"**——即被引用契约在某一时刻的元数据摘要。

**[LIVE-DB] 反证一：同一 AppService，节点 md5 ≠ 契约 md5**

| 项 | 值 |
|---|---|
| 节点 `CALL_APP_SERVICE_n16` 的 `selectMethod.md5` | `3277002066736383209` |
| 契约 `XzhExp950795AppServiceImpl` 的 `md5` | `3277384813636486377` |
| 关系 | 同一 implClass、同一方法，两个值**不等** |

**[LIVE-DB] 反证二：同一 fullName 在实例内存在 3 个 md5**

`com.seeyon.cip.connector.dynamic.appservice.VDAIBANJICHENG.gengxin`

| md5 | 所属微流程 | 微流程 create_time | 微流程 update_time |
|---|---|---|---|
| `dd6f4c4d8b0f751e051872c6144030e6` | 推送已办2 | 2025-02-13 16:16:51 | 2025-02-26 09:22:29 |
| `a7b87bb2385979a416929b0418426571` | 推送已办 | 2025-02-13 16:16:51 | 2025-02-25 14:24:35 |
| `ba786a463373d73dfeeb9b6d15ebbfab` | 工作交接 / 监听回写节点处理人 | 2025-05-11 22:38:25 / 2025-02-13 16:16:51 | 2025-05-13 18:03:47 / 2025-03-31 13:52:29 |

两条 create_time **完全相同**却 md5 不同 → 与"微流程创建时间"无因果关系，只与**引用时被引用方的契约内容**有关。

**[LIVE-DB] 形态分布（345 节点）**

| 形态 | 数量 | 说明 |
|---|---|---|
| 32 位 hex | 344 | 平台内置 / Dubbo 标准方法 |
| 19 位雪球数字 | 1 | UDC 应用自建 AppService（本应用 `n16`） |
| 同一 fullName 多 md5 | **1**（上述 VDAIBANJICHENG） | 证明可变 |
| 同一 md5 对应多 fullName | **0** | 无碰撞，方向性成立 |

### 2.3 由此得出的匹配规则（可执行口径）

```
✅ 允许：fullName 做等值匹配（唯一稳定键）
✅ 允许：md5 做「引用时快照」比对，用于判断"被引用契约是否变更过"
✅ 允许：md5 无碰撞 → 由 md5 反查 fullName 是安全的（单射成立）
❌ 禁止：断言「节点 md5 必须等于当前契约 md5」
❌ 禁止：用 md5 跨微流程/跨时间判等（同一 fullName 可有多值）
❌ 禁止：把 md5 当"32 位 hex"解析（存在 19 位数字形态）
```

---

## 3. parameter / returnValue 契约

### 3.1 `type` = 传输载体（5 个取值，全部实测）

| 侧 | 取值 | 节点数 |
|---|---|---|
| `parameter.type` | `com.seeyon.boot.transport.SingleRequest` | **343** |
| `parameter.type` | `com.seeyon.boot.transport.PageDtoRequest` | **2** |
| `returnValue.type` | `com.seeyon.boot.transport.SingleResponse` | **313** |
| `returnValue.type` | `com.seeyon.boot.transport.ListResponse` | **26** |
| `returnValue.type` | `com.seeyon.boot.transport.PageResponse` | **6** |

**[STATIC]** `MfParameterDto` / `MfReturnValueDto` 结构完全同构：

```java
@DtoInfo("参数")  class MfParameterDto   { String caption; String type; MfItemDto item; }
@DtoInfo("返回值") class MfReturnValueDto { String caption; String type; MfItemDto item; }
```

`type` 注解原文「参数类型」，承载的是**请求/响应包装器全限定名**，不是业务 DTO 类型；业务类型在 `item.itemType`。

> 观察：`PageDtoRequest` 在全部 345 节点中仅 2 例，且均伴随 `PageResponse`/分页服务——分页请求走独立载体，不与 `SingleRequest` 混用。

### 3.2 `output.type` ↔ `returnValue.type` 映射（345 节点配对实测）

| returnValue.type | output.type | 是否成立 |
|---|---|---|
| `SingleResponse` | `OBJECT` | 是（含 1 例 output 缺失） |
| `ListResponse` | `ARRAY` | 是 |
| `PageResponse` | `OBJECT` | 是 |

单值响应 → 标量对象；多值响应 → 数组；分页响应 → **对象**（分页容器本身是对象，元素在 `item` 里）。

### 3.3 `node.output.id` 与 `returnValue.item.itemType` 的等式

全库 4755 条微流程扫描，共 **395** 个 `actionType=CALL_APP_SERVICE` 节点，其中 **345** 个带有效 `selectMethod.fullName`（余 50 个为空壳）：

| 类别 | 数量 | 说明 |
|---|---|---|
| **等式成立** | **270** | `output.id == returnValue.item.itemType` |
| 不适用（简单类型） | **69** | `returnValue.item.itemType` 为 `java.lang.String/Boolean/Void/Integer`、`java.util.Map/List` → `output.id` 为 null，平台不写 |
| 真实结构差异 | **6** | 全部为 `PageResponse`，见下 |
| 空壳节点 | 50 | 只有 `nodeId/type/actionType`，无 `selectMethod` |
| **合计** | **395** | 270 + 69 + 6 + 50 = 395 ✔（`real_bad` 余量 = 0） |

**6 例 `PageResponse` 的唯一例外形态**（`b3-equality-mismatch-samples.json`）：

```
returnValue.type = com.seeyon.boot.transport.PageResponse
returnValue.item.itemType = com.seeyon.ctp.affair.dto.table.AffairDto
output.id = "PageResponse.com.seeyon.ctp.affair.dto.table.AffairDto"   ← 多了 "PageResponse." 前缀
```

即：分页返回时 `output.id` = `"PageResponse." + itemType`，不是裸 `itemType`。

**⚠️ 该形态的可断言边界（v2 按 auditor 复核降级）**

6/6 全部指向同一方法 `AffairOpenApiAppServiceImpl.selectPageByCondition`、同一 implClass。
单一来源**无法区分**两种解释：

- 解释 A：平台对 `PageResponse` 统一加 `"PageResponse."` 前缀（平台级约定）
- 解释 B：该方法/该 DTO 的实现特性（`AffairDto` 专属）

→ 因此**只能写到**：「已观测 6 例均满足 `PageResponse.` + itemType 前缀形态，全部同源；
**是否为平台级约定 = UNVERIFIED**」。
要闭合需要一个**不同 implClass** 的 `PageResponse` 节点；本实例 395 节点内只有这 6 例且同源，**闭合不了**。

→ 可执行校验（**建议形式，非已证事实**）：

```
if returnValue.type == PageResponse:  assert output.id == "PageResponse." + itemType   # 仅 6 例同源观测
elif itemType 是 java.* 简单类型:      assert output.id is null                          # 69 例成立
else:                                 assert output.id == itemType                      # 270 例成立
```

> C4 主体（`output.id == itemType`，270 例）不受此影响，仍然成立；
> 降级的只是「`PageResponse` 前缀=平台统一约定」这一句的外推强度。

### 3.4 `item` 的键集是稀疏序列化（STATIC 根因）

**[STATIC]** `MfItemDto` 带 `@JsonInclude(JsonInclude.Include.NON_NULL)`，字段全集：

```java
itemType, javaType, type, dataType, dtoType="CUSTOM", udcApp=false,
enums, refId="", refApp="", caption="", item(递归), keyType, keyEnums, keyItem(递归)
```

但因 NON_NULL，**未赋值的键不会落盘**。实测两种形态：

| 键集 | parameter 侧 | returnValue 侧 | 条件 |
|---|---|---|---|
| `{enums, item, itemType}` | **344** | **344** | 平台内置 / Dubbo 标准服务的参数描述，只回填这三项 |
| `{dataType, enums, item, itemType, javaType, keyType}` | **1** | **1** | UDC **应用内自建** AppService，回填了 `javaType`/`dataType` |

> 两侧各 1 条，合计 **2 条记录**（不是 4+1）。此前草稿把"含 javaType/dataType 的历史统计"与"当前全库实测"混写，已按实测订正。

**富键集 2 条记录（参数侧 + 返回侧）全部落在本应用唯一自建服务** `XzhExp950795AppServiceImpl.selectById`（`b3-rich-item-samples.json`）：

```json
"parameter":  {"type":"SingleRequest",  "item":{"itemType":"java.lang.Long","javaType":"java.lang.Long","dataType":"BIGINTEGER","keyType":null,...}}
"returnValue":{"type":"SingleResponse","item":{"itemType":"com.seeyon...dto.XzhExp950795Dto","javaType":"...","dataType":"DTO","keyType":null,...}}
```

**这直接推翻了 ROUTE 输入假设中"样本池含完整结构"的隐含前提**：12 条样本池全部来自他应用，全部是 `{enums,item,itemType}` 键集；**没有一条**覆盖本应用形态。
→ 若照样本池直推，会把"UDC 自建服务会多回填 javaType/dataType"这条漏掉。

`keyType` 只在 `Map` 型参数才有非空值；本应用该字段存在但为 `null` → `Map` 未实测，标 **[UNVERIFIED]**。

---

## 4. mappingType / attrs（节点侧参数绑定）

| 字段 | 实测 |
|---|---|
| `mappingType` | 恒为 `"attrs"`（样本 12/12 + 本应用 2/2） |
| `attrs` | 数组；元素 = `{attrType{...}, value{type:"Expression", expression{schema, title}}}` |
| `attrs` 长度 | 本应用 `n16` = **0**（`selectById` 只需 ID，无字段绑定）；`x16` = 1 |
| `node.input` | 恒为 `null`（对照 `output` 有值） |

`attrs[].attrType.id` 形态 = `"<参数DTO全名>.<字段名>"`，与 `parameter.item.itemType` 同前缀 → 参数绑定的作用域由 `parameter.item.itemType` 决定，不是由 `returnValue`。

`node.pageInfo`：`x16`/`n16` 均存在该键（分页节点携带），值为页码/页大小配置 → 与 `PageDtoRequest`/`PageResponse` 呼应。**[UNVERIFIED]**：`pageInfo` 内部字段语义未逐一取证。

---

## 5. 逐字段总表（可直接用于生成/校验）

| 路径 | 语义 | 稳定匹配键 | 生成时必须写 | 校验规则 |
|---|---|---|---|---|
| `node.actionType` | 节点类型 | — | `"CALL_APP_SERVICE"` | 等值 |
| `node.nodeId` | 节点实例 id | — | `CALL_APP_SERVICE_<6位随机>` | 同流程内唯一 |
| `selectMethod.fullName` | 方法唯一标识 | **是** | 由服务选择回填 | 存在性校验（对契约） |
| `selectMethod.implClass` | 实现类 | 否（可推导） | 回填 | `fullName` 前缀一致 |
| `selectMethod.interfaceClass` | Dubbo 接口 | 否 | 回填 | 与 `dubbo=true` 配套 |
| `selectMethod.md5` | 元数据快照指纹 | **否** | 回填引用时值 | **禁等值比对**（C2） |
| `selectMethod.dubbo` | 是否 Dubbo | — | boolean | — |
| `selectMethod.dubboVersion` | Dubbo 版本 | — | `"1.0"` 或 null | 与 dubbo 配套 |
| `selectMethod.isCondition` | 是否条件分支服务 | — | boolean | — |
| `selectMethod.parameter.type` | 请求载体 | — | 由服务签名决定 | ∈ {SingleRequest, PageDtoRequest} |
| `selectMethod.parameter.item.itemType` | 请求业务类型 | 作用域键 | 由签名决定 | 非空 |
| `selectMethod.parameter.item.*` | 类型补充 | — | 稀疏，见 §3.4 | NON_NULL |
| `selectMethod.returnValue.type` | 响应载体 | — | 由签名决定 | ∈ {SingleResponse, ListResponse, PageResponse} |
| `selectMethod.returnValue.item.itemType` | 响应业务类型 | 是 | 由签名决定 | 非空 |
| `node.output.id` | 下游可引用的输出类型 | — | 见 §3.3 三态 | 三态校验 |
| `node.output.type` | OBJECT / ARRAY | — | 由载体映射 | 见 §3.2 |
| `node.output.name` | 输出变量名 | — | `_<nodeId>` 或 `<nodeId>Out` | 同流程唯一 |
| `node.mappingType` | 映射方式 | — | `"attrs"` | 等值 |
| `node.attrs[]` | 入参绑定 | — | `attrType` + `value.expression` | `attrType.id` 前缀 == `parameter.item.itemType` |
| `node.input` | 实测恒 null | — | 不写 | — |

---

## 6. SELF-CHECK 复现命令（全部只读，`/service` 0 次）

```bash
# §3.3 / §3.4 / §5：全库 CALL_APP_SERVICE 节点扫描与等式归因
python "<HERMES_HOME>/cache/scratch/b3_scan_global.py"
python "<HERMES_HOME>/cache/scratch/b3_bad_classify.py"
python "<HERMES_HOME>/cache/scratch/b3_real_diff.py"

# §2.1 / §2.2：md5 语义（节点 vs 契约、同一 fullName 多 md5）
python "<HERMES_HOME>/cache/scratch/b3_md5_check.py"

# §3.1 / §3.4：parameter/returnValue 载体分布 + item 键集分布
python "<HERMES_HOME>/cache/scratch/b3_itemsets.py"

# §3.4 富键集归因
python "<HERMES_HOME>/cache/scratch/b3_rich.py"

# 本应用 3 个 CALL_APP_SERVICE 节点提取
python "<HERMES_HOME>/cache/scratch/b3_extract.py"
```

产物：
- `docs/audit/artifacts/udc-node-evidence/b3-target-app-CALL_APP_SERVICE.json`（本应用 3 节点全量）
- `docs/audit/artifacts/udc-node-evidence/b3-equality-mismatch-samples.json`（6 例 PageResponse 例外）
- `docs/audit/artifacts/udc-node-evidence/b3-rich-item-samples.json`（富键集 6 条）

---

## 6.5 已知变体 / 样本池未覆盖（D8 第 4 点：如实列出，不硬闭合）

> **前提**：`real_CALL_APP_SERVICE.json` 的 12 条样本覆盖 **4 个他应用 appId**
> （`2378987216360786643` / `3289082814923688017` / `5791640252914287064` / `7001530513149673721`），
> **目标应用 0 条**。该池只能支撑「**平台通用形态**」结论；凡涉及本应用的断言已全部改用本应用 LIVE 数据（3 节点，1 空壳）。

以下 4 处结构变体**样本池未覆盖**，本文按实测记录，**不据此硬闭合语义**：

| # | 变体 | 样本池（12 条） | 全库实测（345 有效节点） | 本文处置 |
|---|---|---|---|---|
| V1 | `parameter.type = PageDtoRequest` | 0 例（12/12 为 `SingleRequest`） | **2 例**（均伴随分页服务） | 记为「分页请求走独立载体」，取值域扩到 2 值；**语义细节 UNVERIFIED** |
| V2 | `item` 带 `javaType` / `dataType` / `keyType` | 0 例（12/12 为 `{enums,item,itemType}`） | **参数侧 1 + 返回侧 1**（均属本应用 `n16`） | 记为「UDC 自建 AppService 的稀疏序列化形态」，STATIC 根因 = `@JsonInclude(NON_NULL)`；`keyType` **UNVERIFIED**（无 Map 实例） |
| V3 | `selectMethod.md5` 为 19 位雪花数字 | 0 例（12/12 为 32hex） | **1 例**（本应用 `n16`） | 记为「md5 形态不唯一」；**不据此推导编码规则** |
| V4 | `mappingType = attrs` 且 `attrs` 可为空 / 带 SelectParam | 样本池未展开该字段 | `attrs` 长度 **0**（`n16`）与 **1**（`x16`）两态 | 记为「`attrs` 可空」；**SelectParam 变体 UNVERIFIED** |

> 这四处**不是缺陷**，是平台在不同来源（平台内置 / UDC 自建 / connector 动态服务）下的正常形态差异。
> 若后续生成器要支持 UDC 自建服务，V2 必须处理（否则会按朴素键集误判 DTO 类型）。

---

## 7. 未取证（明确声明，不得外推）

| 项 | 状态 | 原因 |
|---|---|---|
| `keyType` / `keyEnums` / `keyItem` 的 Map 型实态 | **UNVERIFIED** | 全库 0 个 Map 型参数节点（`keyType` 全 null） |
| `pageInfo` 内部字段语义 | **UNVERIFIED** | 未逐一取证分页节点配置 |
| `operationType` / `inputParam`（`SelectMethod` STATIC 字段） | **UNVERIFIED** | `data_schema` 实测未出现这两个键，疑为另一写入路径 |
| `attrs[].value.expression` 的表达式契约细节 | 见 `8085235` 表达式契约文档 | 本切片不重复取证 |
| 运行时按 md5 判定"契约已变更"的具体分支 | **UNVERIFIED** | 需运行态证据；本切片纯读且运行态 SSO 受阻 |
| 本应用 `CALL_APP_SERVICE_pfQeP7` 空壳节点为何只有 3 个键 | **UNVERIFIED** | 可能为编辑器未完成态；无写授权可复现 |

---

## 8. 与 auditor 预审的口径差异（自查记录）

`auditor/B3-PRE-AUDIT-20261018.md` 提出 4 处"样本池未覆盖的结构变体"，本文落盘后逐条比对：

| auditor 提法 | 本文实测 | 处置 |
|---|---|---|
| `parameter.type` 出现 `PageDtoRequest` | 确认，且全库仅 **2** 例（非"偶发个体"） | 采纳并量化 |
| `item` 键集多出 `{javaType,dataType,keyType}` | 确认，参数侧 1 条 + 返回侧 1 条（同一节点 `n16` 的两侧） | 采纳并给出 STATIC 根因（NON_NULL） |
| `selectMethod.md5` 出现 19 位雪花数字 | 确认，全库 **1** 例（本应用 `n16`） | 采纳 |
| `mappingType` 为 `attrs` | 确认，且全库样本 12/12 + 本应用 2/2 无例外 | 采纳 |

**一处数字差异需说明**：auditor 记 `parameter.item` 富键集"节点 x16"，本文实测富键集属 `n16`（`x16` 的 `parameter.item` 是 `{enums,item,itemType}` 朴素形态）。
定位：auditor 那张表把"目标应用出现 PageDtoRequest"（x16）与"键集变体"并列描述，易被读成同一节点。本文按节点粒度分开。
不影响任何结论，已按本文口径记录。
