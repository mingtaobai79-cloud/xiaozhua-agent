# 标准微流程（type=SERVICE）节点流转 —— 真机验证 + 修正

> **重要纠正**：此前把节点建进了 `type=CUSTOM(3)`（自定义微流程），错了。
> 用户所指"标准微流程的节点流转"= **`type=SERVICE(0)` 的服务定义**，带**入参/出参**，是"规则"域下的服务编排。
> 状态：**17 种节点已在标准微流程（SERVICE）中建成并通过 checkSchema**

## 1. ★ 我的两个错误（已修）

| 错误 | 真相 |
|---|---|
| `type` 用了 `CUSTOM(3)` | 标准微流程是 **`type=SERVICE(0)`**（`MicroFlowTypeEnum.SERVICE`）|
| 统一没有出参 | 标准微流程的 `data_schema.output` **必须有出参**（`_FLOW_OUTPUT_*`），endNode.output 同步 |

已删除 12 条误建的 CUSTOM 微流程（`udcMicroflowDeletePost` 全部 SUCCESS）。

## 2. `MicroFlowTypeEnum` 全值域（CFR udc-common）

```
SERVICE(0)      标准微流程（服务定义）  ← 用户所指"标准节点流转"
FRONTEND(1)     前端微流程
ENTITY_RULE(2)  实体规则
CUSTOM(3)       自定义微流程（我误建的）
FUNCTION(4)     函数
```

**判定标准微流程**：`udc_microflow_info.type=0` + `service_interface='CustomMicroFlowAppService'`。

## 3. ★ 标准微流程 vs 自定义微流程（data_schema 差异）

| 维度 | 标准（SERVICE） | 自定义（CUSTOM） |
|---|---|---|
| `type` | 0 | 3 |
| `output`（顶层出参） | **必填**，`{name:_FLOW_OUTPUT_*, dataType:DTO, type:ARRAY, dtoType:MASTER_ENTITY, udcApp:true}` | 可为 null |
| `trigger` | `MFStartNode` type=MANUAL 或 `SERVICE_*` type=SCHEDULE；含 `basic/isArray/desc` | `MFStartNode` type=MANUAL |
| `endNode.output` | 与顶层 output 一致 | 常为 null |
| 用途 | 服务编排、被调用、定时/事件驱动 | 页面内嵌逻辑 |

### 标准微流程 `data_schema` 权威样本（本应用 `小爪标品服务定义`）
```jsonc
{
  "input":  { "name":"_FLOW_INPUT_svc1", "javaType":"java.lang.Long", "appName":"<appName>",
              "dataType":"BIGINTEGER", "type":"OBJECT", "desc":"订单ID" },
  "output": { "name":"_FLOW_OUTPUT_svc1", "javaType":"<dtoFullName>", "appName":"<appName>",
              "dataType":"DTO", "type":"ARRAY", "desc":"<实体>列表",
              "dtoType":"MASTER_ENTITY", "udcApp":true, "inApp":true, "hasPagination":false },
  "trigger": { "nodeId":"MFStartNode", "caption":"开始", "type":"MANUAL", "output":<input>,
               "paramType":"BASIC", "basic":"BIGINTEGER", "isArray":false, "desc":"订单ID" },
  "endNode": { "nodeId":"MFEndNode", "type":"END", "actionType":"END_NODE", "caption":"结束",
               "output":<output>, "paramType":"BASIC", "basic":"DTO", "isArray":true },
  "nodes": [ ... ], "sourceType": null
}
```
**定时任务型**：`trigger = {nodeId:"SERVICE_xxx", caption:"定时任务", type:"SCHEDULE",
  scheduleCronRule:{jobCode, jobCaption, cronRules:[{cycleType:"DAY", rotationType:"HOUR", type:"ANY", value:"8"}]}}`

## 4. ★ 17 种节点在标准微流程中真机建成（checkSchema errors=0）

| 分组 | 节点 | actionType | id |
|---|---|---|---|
| 逻辑 | 分支 | `BRANCH` | -8894514952290990866 |
| 逻辑 | 列表循环 | `FOR_EACH` | 6325829978519983365 |
| 逻辑 | 计数循环 | `FOR` | 7569114204316496096 |
| 逻辑 | 自定义错误 | `CUSTOM_ERROR` | -5849190223968865342 |
| 变量 | 创建变量 | `CREATE_VARIABLE` | 4260053566853583522 |
| 变量 | 修改变量 | `CHANGE_VARIABLE` | -4939028242414318082 |
| 映射 | 创建列表 | `CREATE_LIST` | -506192889574917771 |
| 列表 | 列表操作 | `LIST_OPERATION` | 8450849678243163303 |
| 数据 | 查询单条数据 | `RETRIEVE` | -104542001772604953 |
| 数据 | 查询多条数据 | `RETRIEVE_ARRAY` | 4810826811202165121 |
| 数据 | 插入数据 | `ENTITY_SAVE` | -2307619429042762508 |
| 数据 | 更新数据 | `CHANGE_ENTITY` | -4399474802104099166 |
| 数据 | 删除数据 | `DELETE_ENTITY` | -8724529805834699934 |
| 基础服务 | 事件投递 | `PUBLISH_BUSINESS_EVENT` | 2417198731547213581 |
| 基础服务 | 子微流程 | `SUB_MICROFLOW` | 4915516489388776197 |
| 数据加工 | 类型转换 | `CONVERT_DATA` | 6253280942458436572 |
| 数据加工 | 数据映射 | `DATA_MAPPING` | -4903027944616938305 |

另有综合示例：**小爪标准节点流转** id=6535946353192090208（6 节点：创建变量→查询单条→查询多条→数据转换→提示消息→保存记录，带完整出参）。

## 5. 侧面板节点目录（用户截图 = 权威 UI 分类）

```
逻辑活动：分支 / 列表循环 / 计数循环 / 自定义错误
变量活动：创建变量 / 修改变量
映射活动：创建映射组 / 映射操作
列表活动：创建列表 / 修改列表 / 列表操作
数据活动：查询单条数据 / 查询多条数据 / 插入数据 / 批量插入数据 / 更新数据 / 批量更新数据 / 删除数据
基础服务：自定义服务 / 事件投递 / 子微流程 / 执行生单规则
数据加工：类型转换 / 数据转换
```

## 6. 边界（未做）

- 侧面板 24 项中已真机建 17 项；剩 `CREATE_MAPPING_GROUP`（创建映射组）、`MAP_OPERATION`（映射操作）、`CHANGE_LIST`（修改列表）、`CHANGE_BATCH_ENTITY`（批量更新数据）、`ENTITY_BATCH_SAVE`（批量插入数据）、`CALL_APP_SERVICE`（自定义服务）、`CALL_DATA_FLOW_FRONT`（执行生单规则）未逐个建。
- 未走"应用构建"验证 04003 消除。
- 微流程运行期未触发。

## 7. 复现

```bash
python cleanup_custom.py    # 删除误建的 CUSTOM 微流程
python std_fix.py           # 标准微流程（SERVICE + 出参）示例
python std_nodes_batch.py   # 17 种节点在标准微流程中建 + checkSchema
```
