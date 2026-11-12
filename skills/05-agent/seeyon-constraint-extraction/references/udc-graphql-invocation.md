# UDC GraphQL 调用配方 与 微流程节点落数据

## GraphQL 调用形态（实测可用，REST 优先于 CDP）

```
POST {base}/service/udc/graphql?<op>
body {"query": "...", "variables": {"x": <path 或 body 对象>}}
headers: Content-Type: application/json, Cookie: <会话 cookie>, Accept: application/json
```

写/校验类（mutation）：

```
mutation graphqlLoader ($x: <op>InputBody) { data0: <op>(body: $x) { code message status data { content { ...字段 } } } }
```

读类（query）：`data0: <op>(path: $x)`（带 id 的 GET 类）或 `(body: $x)`。

- **paramsKey 由前端 loader 定义决定**：绝大多数 mutation 用 `body`，带 id 的 GET 类用 `path`（前端 `{paramsKey:'body'|'query'}` 就是它）。
- **`data` 下的返回内容必须再包一层 `content{...}`**：直接写 `check`/`errorMessage` 会报 `Validation error of type FieldUndefined: Field 'check' in type '<op>ResponseContent' is undefined`。前端 loader 的 `queryFields` 里写的 `content{ ... }` 就是这个含义——照抄它，别自己猜字段路径。
- **不要用内省枚举字段**：`{ __schema { ... } }` 返回 `GraphQL_3000`（生产已禁）；字段是否存在只以**前端 bundle 的 loader 定义**为权威。
- **业务错误 = HTTP 200 + `data0.status != 0`**（不是 HTTP 4xx）。`code` 是稳定码（`BOOT_*` / `UDC_*` / `GraphQL_*`），用它分支；`message` 可能是 i18n key 或中文文案。`BOOT_1001 xxx must not be null` = 入参缺字段。
- 变量类型名 = `<op>InputBody`（mutation）/ `<op>InputPath`（path）。类型名错报 `UnknownType`；字段错报 `FieldUndefined`——两种报错直接指出你抄错了哪一层。

## 微流程保存/校验链（按 type 分流）

设计器保存微流程时按 `type` 走不同通路：

- **type=BACKEND(0)**：先调 `udcMicroflowCheckSchemaUpdatePost`（入参=完整流程对象，含 `dataSchema=JSON.stringify(nodes)`），返回 `content{ check:bool, errorMessage[], errors:int }`。
  - `check=false` → `errorMessage[]` 每项 `{errorCode, errorType, level, message, nodeCaption, nodeId, path, propertyKey}`；前端据此弹「节点校验不通过」并滚动到 `nodeId`。
  - `check=true` 才真正保存。
  - **这条 op 是「不点界面判一条后端微流程结构是否合法」的权威探针**——REST 直调即可，无需 CDP。
- **type=FRONTEND(1) / FUNCTION / DRAFT**：直接 `updateMicroflowSchema` / `saveMicroflowSchema`，不走校验。

## 节点引用必须命中本应用候选列表（「所选数据已变更」根因）

节点里每个字段/实体/DTO 引用都以 key 形式存（如 `com.seeyon.<appName>.dto.<Entity>Dto.<field>`）。前端字段选择器判定：

```js
h = candidateList.find(e => e[key]===value || e.options?.some(o => o[key]===value))
// h 为空 → 渲染红字「所选数据已变更，请重新选择」
```

服务端同源判定：`udcMicroflowFindDtoByEntityPost` → `UDC_MICROFLOW_0022`
（*The entity data does not expose the corresponding object, please select again*）。
`udcMicroflowTreeEntityDtoPost` 还会返回「接口不支持查询其他应用的数据，请查询当前应用」——**跨应用取数在服务端也被拒**。

**铁律：不要拿别的应用的真实流程当节点模板。** appId 能替换，但节点里的 DTO/实体类名/变量 key 仍是原应用的，落到目标应用就是**整套节点飘红**。挖节点结构必须从**目标应用自己的真实流程**里取，且要排除自己造的流程（否则循环污染）。

- 用 DB 逐条 dump，不要一次全取（大字段会被 `conn.py` 截断）：
  `SELECT data_schema FROM udc_microflow_info WHERE app_id='<appId>' AND id='<flowId>'`
- 提取引用时按「节点 actionType 归类」聚类成模板：`real_own_nodes.json`（本应用真实节点）→ 与待修流程逐节点 diff。
- 本应用引用的前缀规律：
  - 实体：`com.seeyon.<appName>.domain.entity.<Entity>`
  - DTO：`com.seeyon.<appName>.dto.<Entity>Dto`（字段 `.field`；列表/表格常带 `Dto` 后缀差异）
  - 流程自定义 DTO：`com.seeyon.<appName>.dto.microflow.<随机名>`
  - 变量 key 形态：`_CREATE_VARIABLE_<rand>`、`_RETRIEVE_<rand>`、`_FLOW_INPUT_<rand>`、`_CALL_MICRO_FLOW_<rand>` + `_<DTO全名>.<字段>`
- **两种域不要混**：微流程=后端流转（`type=0`，表 `udc_microflow_info`，triggerType MANUAL/SCHEDULE）；页面规则=依赖应用的前端流转（`type=1`，必须绑页面 `sourceId`，triggerType FRONTEND_PARAM）。前端节点（28 种，`*_FRONT` 后缀等）与后端节点（18 种）结构不同，别互相套用模板。

## 审计口径

- 修正前先量化：扫出「非本应用前缀」的引用条数与受影响节点数，作为修复前基线与修复后回归对比。
- **服务端 `check=true` ≠ 画布无红字**：服务端只校验结构，前端红字来自本地候选列表比对。宣称修好必须两边都过——先过 `udcMicroflowCheckSchemaUpdatePost`，再 CDP 开画布确认无红字。
