# 微流程生成链：声明式 spec → dataSchema → 提交

> 状态：LIVE（2026-10-24，实建 3 条微流程，DB 回读 + 清理全通）
> 实现：`components/udc/microflow/build.py` · CLI：`tools/core/microflow/build_microflow.py`

## 铁律

- 顶层固定 6 键：`endNode / output / input / sourceType / trigger / nodes`，多一个键前端保存时丢弃
- **没有 `flowPaths`** —— 全库样本该键恒为 null；写了也不生效，别用它表达连线
- 执行顺序 = `nodes` 数组顺序；`runAfter` 全库恒为 null，不要用它表达先后
- 分支 = `conditions[].nodes` 嵌套，`name` 只能取 `ifBranch` / `elseIfBranch` / `elseBranch`
- 节点出参名必须 `_<actionType>_<6位>`，开始节点（顶层 `input`）必须 `_FLOW_INPUT_<6位>`
- `state` 有两套形态：DB 与 create body 用数字 `20`，`validate_release_readiness` 判字符串 `"RELEASE"`
- 接口 `BOOT_0000` 不等于建成，必须 DB 回读 + 页面列表可见

## 1. 顶层结构（全库取证）

```json
{
  "endNode": {"id":"","name":"","type":"END","actionType":"END_NODE",
              "nodeId":"MFEndNode","caption":"结束","description":"",
              "input":null,"output":null},
  "output": null,
  "input":  {"name":"_FLOW_INPUT_xxxxxx","dataType":"STRING","type":"OBJECT", ...},
  "sourceType": "PAGE",
  "trigger": {"id":"","nodeId":"MFStartNode","caption":"开始","description":"",
              "type":"MANUAL","input":null,"output": <与顶层 input 同一对象>},
  "nodes": [ ... ]
}
```

`sourceType` 实测值：`PAGE` / `SUBPAGE`。即便 `type=0`（服务定义）也可为 `PAGE`。

## 2. 节点形态

```json
{
  "nodeId": "<ACTIONTYPE>_<6位>",
  "name": null, "type": "ACTIVITY", "caption": "查询单条数据(1)",
  "description": null, "runAfter": null,
  "input": null,
  "output": {"name":"_RETRIEVE_xxxxxx","dataType":"ENTITY","type":"OBJECT",
             "javaType":"java.lang.Object","desc":"账单导入","hasPagination":false},
  "isCompleted": true,
  "actionType": "RETRIEVE",
  ...节点自身字段（condition / mappingType / error 等直接摊在顶层）
}
```

分支节点：`type` 与 `actionType` 都是 `BRANCH`，`output`/`input` 为 null，带 `conditions`。

## 3. 分支结构

```json
{
  "nodeId":"BRANCH_xxxxxx","type":"BRANCH","actionType":"BRANCH",
  "conditions":[
    {"name":"ifBranch","expression":{"title":"...","schema":"<JSON字符串>"},
     "logicalOperator":"AND","nodes":[...]},
    {"name":"elseBranch","expression":null,"logicalOperator":"AND","nodes":[...]}
  ]
}
```

★ 条件表达式 `schema` 是**JSON 字符串**不是对象（见 `rule-domain.md` 同名坑）。
★ 最后一项 `expression=null` 即默认分支；生成器会自动补，不补则前端渲染缺 else。

## 4. LIVE 证据链

```
tools/core/microflow/build_microflow.py --app-id <appId> --spec <json>
  → 生成校验 通过（validate_schema）
  → 提交门禁 通过（validate_for_submit）
  → checkSchema BOOT_1001（已知：该接口对非检测面 schema 返回此码，不阻塞 create）
  → create      BOOT_0000 content=<id>
  → DB 回读     type=0 state=10 顶层键 6 个 节点数 2
  → delete      BOOT_0000，残留 0
```

三条实建样本（单节点 / 变量+分支 / CLI 全链路）均回读一致后删除，基线复原。

## 5. 已知未解

- **`state` 落成 10（草稿）**：create body 传 `state: 20` 仍落 10，需另行 publish
  （`checkSchema/update` 或发布接口）。未验证，属 UNVERIFIED。
- `checkSchema` 返回 `BOOT_1001` 且 `content=None`：在非检测面用途下不代表 schema 非法，
  判据仍是 create 成功 + DB 回读。此点与 `rule-domain.md` 的「checkSchema 0000 也可能 check=False」互为镜像，
  **两个方向都不能只看 code**。

## 6. 约束入口

```
components/udc/microflow/build.py
  build_schema(spec, app_id, source_type)      声明式 → dataSchema
  validate_schema(schema)                      节点字段 / 顶层键 / 结束节点作用域
  validate_for_submit(schema, app_id, name)    RELEASE 深解析（含 state 形态转换）

components/udc/microflow_constraints.py
  validate_node_fields / validate_call_app_service /
  validate_mapping_rule / validate_end_node_scope / validate_release_readiness
```
