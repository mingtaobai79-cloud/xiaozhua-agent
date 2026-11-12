# GraphQL op 命名规则（后端权威，字节码实证）

**证据级**：`VERIFIED_STATIC_BYTECODE`
**证据源**：`boot-starter-graphql-5.3.358.jar`
  - `com.seeyon.boot.starter.graphql.GraphQLProvider#pathToCamel` / `#queryBuild`
  - `com.seeyon.boot.starter.graphql.GraphQLObjectTypeParamsService#addMethodParamList`
  - `com.seeyon.boot.starter.graphql.GraphQLObjectTypeNReturnService#getContentType`

## 结论（本轮核心）

**GraphQL op 不是独立的接口面，而是 udc-web REST 端点的镜像。**

```
op = pathToCamel( restPath + "/" + httpMethod.toLowerCase() )
```

推导路径：`GraphQLProvider.run(appName, restApiMetadatas, ...)` 遍历
`RestApiMetadataDto` 的 `methodList`，对每个 `RestMethodMetadataDto` 调 `queryBuild(...)`，
其中 `methodTypeName = pathToCamel(methodDto.getPath() + "/" + httpMethod.toLowerCase())`，
再 `builder.name(methodTypeName)` 作为 GraphQL 字段名。

由此："页面按钮 → op" 映射的右端，**就是 Controller 方法 + @RequestMapping 路径 + HTTP 动词**。
前端 op 与后端 REST 的对账可以**按规则精确推导**，无需逐个反查 Resolver / 父类。

## 规则六步（与字节码逐行对应）

| # | 步骤 | 字节码 |
| --- | --- | --- |
| 1 | 去掉 path 变量花括号 | `path.replaceAll("\{","").replaceAll("\}","")` |
| 2 | 拼 `"/" + httpMethod.toLowerCase()` 后驼峰化（分隔符 `-` `/` `_`，**另恒含空格**）| `toCamelCase(path, false, '-','/','_')` |
| 3 | 去非字母数字 | `replaceAll("[^A-Za-z0-9]","")` |
| 4 | `IdGet$` → `Get` | `replaceAll("IdGet$","Get")` |
| 5 | `Id$` → 空串 | `replaceAll("Id$","")` |
| 6 | `SearchPost$` → `Search` | `replaceAll("SearchPost$","Search")` |

> 第 4/5/6 步是**唯一**三条业务缩写改写，**顺序不可交换**：`IdGet$` 必须先于 `Id$`。
> 实测依赖此顺序的用例：`/udc/entity/attribute/select-by-primary/{id}` + GET
> → `udcEntityAttributeSelectByPrimaryGet`（走了 `IdGet$→Get`）。

### 关键细节：首分隔符不大写（`outOffset == 0` 守卫）

`toCamelCase` 内：

```
if (delimiterSet.contains(codePoint)) {
    capitalizeNext = true;
    if (outOffset == 0) { capitalizeNext = false; }   // 关键：尚未输出字符时不首字母大写
    continue;
}
```

因为 REST 路径以 `/` 开头，**首字符必须是小写 `u`**：
`/udc/application/do/detection` → `udcApplicationDoDetectionPost`（**不是** `UdcApplication...`）。
本实现与 `apache-commons CaseUtils.toCamelCase` 行为**不同**（实现时踩过一次坑，已修）。
另注：`generateDelimiterSet` 恒把空格 `' '` 加入分隔符集合。

## 入参 / 出参类型名

| 参数来源（`RestParamMetadataDto.paramType`）| GraphQL 参数名 | 入参类型名 |
| --- | --- | --- |
| `path` | `path` | `<op>InputPath` |
| `body` | `body` | `<op>InputBody` |
| 其它（含无参）| `query` | `<op>InputQuery` |

- 出参：`<op>ResponseContent`（`getContentType` → `typeName = methodTypeName + "ResponseContent"`）。
- `form` / `formData` 参数类型**不支持**，Schema 初始化直接抛异常（`暂不支持form,formData请求参数类型`）。
- 挂载：`httpMethod == "get"` → 仅 Query；其余 → **Query 与 Mutation 同名双挂**。

这正好解释了既有前端抓包形态：`udcEntityGet / udcEntityGetInputPath / path:{id}`、
`udcIndexPost / udcIndexPostInputBody / body`、`udcMicroflowFindNodesGet / ...InputQuery / query`。

## 对账结果（全部用规则复算，非模糊匹配）

| 口径 | 数量 | 规则复现 |
| --- | --- | --- |
| udc-web REST 方法 | 657 | 规则产出 **778** 唯一 op（含 class_mapping 与 full_path 双拼法候选）|
| 前端 op 总量 | 346 | **224** 可用规则精确回到 REST 端点 |
| 旧对账"已精确对齐" | 173 | **164** 复现 |
| 旧对账"仅前端" | 173 | **60** 其实能精确归位（原判"需 GraphQL 解析"不成立）|
| 前端 op 中非 udc-web REST | — | **122**（udc 99 / appCommon 13 / portal 2 / bpm 2 / ctp 2 / cip 1 / organization 1 / main 1 / edoc 1）|

## 旧对账的 9 个假阳性（已证据化修正）

`FRONTEND-OP-TO-ENDPOINT-ALIGNMENT.md` 中这 9 个 op 被**模糊**归到同名 Controller 上；
按规则复算，它们**不由任何 udc-web 端点产出**，真名如下：

| 旧（不存在的 op）| 规则给出的真名 |
| --- | --- |
| `udcApplicationCopyGet` | `udcApplicationCopyPost` |
| `udcApplicationSaveAsPost` | `udcApplicationSaveAsTemplatePost` / `udcApplicationSaveAsNewDesignPost` |
| `udcMetaDataMergeReferPost` | `udcMetaDataMergeReferByMapPost` |
| `udcMetaDataSelectAggregationEntityPost` | `udcMetaDataSelectAggregationEntityEntityIdPost` |
| `udcMetaDataSelectAppByIdPost` | `udcMetaDataSelectEntityByAppIdAppGet` |
| `udcMicroflowCopy` | `udcMicroflowCopyPageRuleBoundControlPost` |
| `udcMicroflowSearch` | `udcDataTransferObjectSearchMicroFlowCustomDtoAppIdPost` 等 |
| `udcRuntimeDeployPost` | `udcRuntimeDeployNormalPost` / `DeployForm` / `DeployStopDeployIdPost` |
| `udcApplicationPost` | `udcApplicationCreateLayoutAppPost` / `DeletePost` / `DeleteRenamePost` |

余下 99 个 `udc*` 前缀前端 op 未归位 udc-web：集中在 **sandbox / message / portalSpace /
formUpgrade / pageComponent / customDataType** 等子域 —— 这些 op **确实存在**于前端，
但不由 udc-web 的 54 个 Controller 暴露（属其它构件或网关动态路由），
**保持 UNVERIFIED，不以规则臆造**。

## 用法

```python
from components.udc.graphql_op_naming import path_to_op, derive_ops, explain

> **依赖前置（2026-10-14）**：`derive_ops` 的 op **只由 `_api_full.json` 的 `full_path` 产出**；`full_path`
> 必须遵守类级+方法级**恒拼接**。该规则曾有拼接缺陷（159/657 条错、造出 122 个幻影 op），已修复并加全量护栏 ——
> 见 `FULL_PATH-CONCAT-DEFECT.md`。修复后 `derive_ops` 的 "双候选兜底" 实测为 no-op，已删除。
path_to_op("/udc/entity/attribute/batch-delete", "POST")   # udcEntityAttributeBatchDeletePost
explain("udcEntityDeletePost")                             # [{'ctrl':'EntityController', ...}]
```

回归护栏：`tests/udc/test_graphql_op_naming.py`（15 项）——复现 164 真阳 + 暴露 9 假阳 + 守 224/346；另含 3 项 full_path 契约护栏（2026-10-14，见 `FULL_PATH-CONCAT-DEFECT.md`）。
