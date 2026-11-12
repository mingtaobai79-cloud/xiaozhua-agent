# 微流程 schema 生成：用仓库构造器，不要克隆库内样本

用户明确要求：**不要从数据库里扒一条真实微流程当模板去改**，用 seeyon-agent 仓库里已经沉淀的
生成器 + 约束模型产出 schema。克隆样本会把别人的语义带进来，且样本一删就失去依据。

## 1. 三个入口（按顺序用）

| 位置 | 作用 |
|---|---|
| `components/udc/microflow/build.py::build_schema(spec, app_id=, flow_name=)` | 声明式 spec → dataSchema。**首选** |
| `components/udc/microflow_constraints.py` | CFR 反编译的权威约束：`required_fields(actionType)` / `validate_node_fields` / `validate_end_node_scope` / `validate_release_readiness` / `validate_call_app_service` |
| `tools/core/microflow/all_nodes_demo.py` | 20 类节点的可执行样板生成器（spec 形状参考实现），产出 spec JSON |
| `tools/core/microflow/build_microflow.py` | 提交流程（CLI） |

生成后**必须**依次过 `validate_node_fields` → `validate_end_node_scope` → `validate_release_readiness`，
三道全过才算可提交。

## 2. schema 顶层契约（build.py 头部已取证，别自己发明）

- 顶层固定 6 键，顺序即前端保存顺序：`endNode / output / input / sourceType / trigger / nodes`。
- **没有 `lines`、没有 `flowPaths`**（写了会被前端丢弃）。执行顺序 = `nodes` 数组顺序；
  分支节点用 `conditions[].nodes` 嵌套表达。
- `runAfter` 全库恒为 null，**不要拿它表达顺序**。
- 节点 id：`<ACTION_TYPE>_<6 位字母数字>`；节点出参名 `_<ACTION_TYPE>_<同样后缀>`；
  开始节点出参名 `_FLOW_INPUT_<6 位>`。
- 换/替换节点就地改 `actionType` 并**保留 nodeId**——拓扑按 id 关联，换 id 等于断链。

## 3. all_nodes_demo 的正确调用

```bash
# 1) 字段元数据（实体 → attr_meta JSON，demo 必需 --attr-json，缺了直接 KeyError 字段名）
python -c "import json,sys;sys.path.insert(0,'.');\
from tools.core._env import connect_db,load_env,query;\
db=connect_db(load_env('test2'),'udc_test2');\
rows=query(db,'SELECT name,caption,data_type,id FROM udc_attribute WHERE entity_id=<id> AND (is_system=0 OR is_system IS NULL)');\
json.dump({r['name']:{'name':r['name'],'caption':r['caption'],'dataType':r['data_type'],'id':str(r['id'])} for r in rows},open('scratch/attrs.json','w'))"

# 2) 生成 spec
./.venv/Scripts/python.exe tools/core/microflow/all_nodes_demo.py \
  --app-id <appId> --app-name <appName> --entity <entityName> --entity-id <实体id> \
  --entity-caption <中文名> --subflow-id <id> --subflow-name <name> \
  --attr-json scratch/attrs.json --out scratch/all_nodes.json
```

`all_nodes_demo` 覆盖 20 类：CREATE_VARIABLE（基础/实体）/CREATE_LIST/CREATE_MAP/CHANGE_VARIABLE/
LIST_OPERATION/CHANGE_LIST/MAP_OPERATION/RETRIEVE/RETRIEVE_ARRAY/CREATE_ENTITY/CHANGE_ENTITY/
CREATE_BATCH_ENTITY/CHANGE_BATCH_ENTITY/DELETE_ENTITY/SUB_MICROFLOW/FOR/BRANCH/CONDITION/BREAK/CUSTOM_ERROR。

**未覆盖**（需额外语义输入，必须自己补）：`CALL_APP_SERVICE`（要真实 selectMethod 签名）、
`CONVERT_DATA`（字段级 selectParam + 类型匹配）、`DATA_MAPPING`、`PUBLISH_BUSINESS_EVENT`、`CALL_DATA_FLOW`。

## 4. required_fields 实测（写节点前先对齐）

```
CREATE_ENTITY   app, structure, mappingType, value, title
RETRIEVE        app, structure, title, condition|value
RETRIEVE_ARRAY  app, structure, variableTitle, condition|value
CREATE_VARIABLE paramType, title
CHANGE_VARIABLE selectParam
CHANGE_LIST     selectParam, action, dataSource
CALL_APP_SERVICE app, selectMethod
SUB_MICROFLOW   mfService
```

## 5. 相关表（只读取证用）

- `udc_microflow_info.data_schema` —— 流程本体（JSON 字符串）。
- `udc_dependent_application` —— 应用依赖；跨应用服务节点缺这行就报 `04004 依赖应用已删除`。
- `udc_data_flow_mapping` —— 生单规则映射行；执行生单规则节点 `dataFlow` 指向**映射行 id**，
  指规则 id 只会显示裸 ID。
- `udc_custom_data_type` —— 自定义数据类型（入参/出参自定义对象）。

pymysql 的 `query()` 会把 `%` 当格式符：`LIKE '%x%'` 要写成 `LIKE '%%x%%'`，否则
`not enough arguments for format string`。

## 6. 双层校验口径

`udcMicroflowCheckSchemaUpdatePost` 只做单流程浅校验，返回 `check:true` 后 UI「检查」仍可能给
`UDC_MICRO_FLOW_04004` 阻断（前序节点变更 / 依赖应用已删除 / 生单规则已被删除）。两个都要跑：
先 checkSchema，再在草稿态点「检查」读 `.ant-table-tbody tr`。

## 7. 提交闭环（CLI 实跑顺序）

```bash
# 1) spec → schema，本地校验（返回 errors 必须为 0）
./.venv/Scripts/python.exe scripts/spec_xxx.py

# 2) 提交：首次建流程用 --spec；已存在用 --resume <id> 更新同一 id
./.venv/Scripts/python.exe tools/core/microflow/build_microflow.py \
  --app-id <appId> --caption "<中文名>" --name <name> \
  --spec scratch/xxx.spec.json --db-env test2
# 已有 id：
./.venv/Scripts/python.exe tools/core/microflow/build_microflow.py \
  --app-id <appId> --resume <flowId> --spec scratch/xxx.spec.json --db-env test2
```

输出注释（别误判）：

- `checkSchema： BOOT_1001 None` —— 建流程前对不存在 id 的探测，**正常**，不是失败。
- `提交门禁：失败 N 条` —— `validate_release_readiness` 拦下，例：
  `DATA_MAPPING_xxx.mappingRule 缺 'name'`（生成器不填 mappingRule.name/caption，自己补）。
- `create： BOOT_0000 <id>` → `publish(update)： BOOT_0000 SUCCESS` → `接口读回：state=RELEASE` 三步齐了才算发布。

★ 生成器静默丢节点的坑：`Builder(...)` 构造时的 `sub=None` 会让 `sub_microflow()` 返回 `None`，
`nodes.append(None)` 后 `validate_schema` 直接抛 `AttributeError: 'NoneType' object has no attribute 'get'`。
组装时用 `add(**...)` 包一层打印 `[skip]`，并在 `build_schema` 前过滤空节点；生成后**必看类型分布与节点数**，
节点数比预期少就是有方法返回了 None（缺 sub / 缺必填 ref）。

