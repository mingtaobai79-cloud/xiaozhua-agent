# SUB_MICROFLOW（调用子微流程）

> 2026-11-02 实测：**父子流程自建、入参出参全链贯通、属性变更检测与刷新均验证**。
> 能力等级 RUNTIME_VERIFIED。

## 1. 语料形态（251 条真实样本 / 156 条流程）

语料源：`scratch/pmp_schemas.json`（另一应用的 643 条 RELEASE 微流程全量 dump，7937 个节点）。
**注意：能力矩阵里旧的「706 条」是错的，本节点实际样本是 251 条。**

### 调用节点结构（251/251 全有）

| 键 | 说明 |
|---|---|
| `mfService` | 子流程描述（16 个键全 100% 出现） |
| `output` | 215 有 / 36 为 null |
| `outputName` | 215 |
| `value` | 162（**标量入参走这里**，不是 attrs） |
| `mappingType` | 45%（DTO 入参才需要，值 `value` / `attrs`） |

`mfService` 键：`id / appCaption / appId / appName / caption / description / hasInput /
hasOutput / hostPath / input / method / name / output / path / triggerType / type /
restType(241) / label(26)`。

### 入参出参类型分布

| 入参 dataType | 数量 | | 出参 dataType | 数量 |
|---|---|---|---|---|
| DTO | 112（CUSTOM 109 / MASTER_ENTITY 2 / SUB_ENTITY 1） | | STRING | 81 |
| STRING | 66 | | DTO | 80 |
| BIGINTEGER | 55 | | BOOLEAN | 44 |
| DATETIME | 4 | | BIGINTEGER | 4 / DATETIME 3 / DECIMAL 3 |

`hasInput/hasOutput` 组合：`(T,T) 207`、`(T,F) 30`、`(F,F) 6`、`(F,T) 8`。
→ **无参子流程只占 6/251**，主流是带参调用。早期构造器写死 `hasInput=False`
只能覆盖这 2.4%。

## 2. 运行时解析规则（`SubMicroFlowActivity.parseActivityNode`）

```
mfService = buildMfService(node, ..., required=true, "mfService")
if mfService.input != null:
    if input.dataType == "DTO":
        mappingType = getString("mappingType", required=true)
        if mappingType == "value":  value = buildAttrValue(..., required=true)
        else:                       attrs = buildSelectObjectAttrs(..., required=true)
        if input.hasPagination:     pageInfo = buildAttrValue("pageInfo", ...)
    else:                           # 标量
        mappingType = "value"       # 代码里直接置，不读 JSON
        value = buildAttrValue(..., required=true)
if mfService.output != null:
    output = buildOutPut(node, ..., required=true, true)
    output["inApp"] = mfService.output.inApp == null || != false
```

要点：**标量入参只需要 `mfService` + `value`**；DTO 入参才需要 `mappingType`/`attrs`/`pageInfo`。

## 3. 流程入参怎么在节点里引用（85 个写节点样本）

子流程内部用 `trigger.output`（名形 `_FLOW_INPUT_xxx`）时，写节点 `attrs[].value` 形态：

```json
{"type": "SelectParam",
 "selectParam": {"id": null, "javaType": "java.lang.String", "dataType": "STRING",
                 "type": "OBJECT", "desc": "分公司", "dtoType": null, "udcApp": null,
                 "name": "_FLOW_INPUT_xxx", "key": "_FLOW_INPUT_xxx",
                 "path": "_FLOW_INPUT_xxx", "outputName": "_FLOW_INPUT_xxx",
                 "description": "分公司", "position": "parent"},
 "desc": "分公司 [文本]"}
```

查询条件里则用 `CONTEXT_VARIABLE` + JSON 字符串。两种形态都已落实现。

## 4. 属性刷新：机制与实测

### 机制（字节码）

`MicroFlowComponentUtils.checkMfService`（发布/检测时）：

```java
if (!microFlowDtoMap.containsKey(mfService.id))     → FUNCTION_PAGE_RULE_DELETE
if (dto.state == DRAFT)                             → NOT_RELEASE
if (!mfService.path.endsWith(dto.name))             → MICRO_FLOW_CHANGE
compare(mfService.input,  childSchema.input)        → MICRO_FLOW_CHANGE
compare(mfService.output, childSchema.output)       → MICRO_FLOW_CHANGE
hasPagination 不一致                                 → SUB_MICRO_FLOW_NOT_INCLUDE_PAGE_INFO
```

`compare()` **只比 `dataType` / `type` / `id`**（desc、name、javaType 变了不算）。

### 实测（受控实验）

1. Child 出参 `STRING` → 父流程调用、构建、执行全通（`taskId=CHILD-OUT`）。
2. 把 Child 出参改成 `BIGINTEGER`（常量 424242）并发布。
3. **父流程不刷新直接再发布 → 平台居然放行**（单流程 checkSchema 不做全局比对）。
4. **触发构建 → 11 秒 FAIL**：
   `发布失败: Business Error[一致性检测未通过]，
    报错位置 com.seeyon.udc.pipeline.AbstractDeployService.doParallel(AbstractDeployService.java:242)`
5. 刷新（重读子流程契约 → 重建调用节点 → 回读确认 `dataType=BIGINTEGER`）→ 发布通过、构建 SUCCESS。
6. 再跑一轮：父流程下游写入 `processed_rows = 424242` —— 新契约在运行期真实生效。

**结论：属性失效检测发生在「构建期一致性检测」，不在单流程发布期。**
设计器里的「属性已更新，请重新选择」提示，对应的就是这个检测；
只重发 API 不改 `mfService` 是绕不过去的（第 4 步会一直 FAIL）。

## 5. 端到端结果（读侧数据）

同一条迁移断点表，两次执行：

| 时刻 | task_id | processed_rows | 谁写的 | 证明 |
|---|---|---|---|---|
| 19:54:00.390 | `P5SUB619804` | 0 | Child | 父流程变量传进子流程，子流程确实执行 |
| 19:54:00.663 | `CHILD-OUT` | 0 | Parent | 子流程返回值回到父流程，并被下游节点使用 |
| 20:01:00.419 | `P5SUB619804B` | 0 | Child | 新标记同样传入 |
| 20:01:00.662 | `P5SUB619804B` | **424242** | Parent | 刷新后的 BIGINTEGER 返回值真实流回 |

两次都是「子流程先写、父流程后写」，间隔 0.24~0.27 秒，调用链顺序正确。

## 6. 实现改动

| 位置 | 改动 |
|---|---|
| `logic_graph._ref_value` | 新增流程入参分支 → `_flow_input_ref()`（此前直接抛「不是已构建节点」） |
| `logic_graph._do_sub_microflow` | 透传 `value`（标量映射）与 `out_desc`、`attrs` |
| `composer._st_sub_microflow` | `hasInput/hasOutput/input/output/path` 全部改为读子流程**当前**定义（原来写死 False） |
| `live_refs.microflow_detail()` | 新增：读 `udcMicroflowFindByIdGet` 取子流程 input/output |
| `microflow_nodes_svc.sub_microflow` | 支持 `value` → `mappingType="value"`；`out_desc` 落到 outputName/desc |

## 7. 未覆盖

- **DTO 入参**（112/251，最主流）未跑：需要子流程有自定义 DTO 参数，属于设计器建 DTO 的活
- `attrs` 逐字段映射（DTO 形态）未跑
- `pageInfo` 分页入参未跑（`SUB_MICRO_FLOW_NOT_INCLUDE_PAGE_INFO` 只做了静态阅读）
- 循环调用检测（`checkLoopCall`）未实测

## 6. ★★ DTO 入参：attrType 是**子流程入参 DTO 的字段**

旧结论说「需在设计器里建自定义 DTO 参数」——一半对一半错：

- **能无头做**：把流程的 `input` 声明成实体 DTO（`dtoType=MASTER_ENTITY`），
  `publish=True`，平台接受；父流程就能按字段映射传参。
- **仍需设计器**：`dtoType=CUSTOM` 的自定义参数 DTO（109/112 条语料），
  创建该 DTO 的接口没找到。

### 真实形态（112 条语料）

```
mappingType = "attrs"
attrs = [{attrType: <子流程入参 DTO 的字段>, value: Simple | SelectParam}]
```

`attrType` 取自**子流程**的入参 DTO，不是父流程的字段。

### ★ 最大的坑：整变量引用 → 重复声明局部变量

取值写成 `{"input": "taskId"}` 但生成的是「整个入参变量」引用
（`position="parent"`、`name=_FLOW_INPUT_xxx`），两个字段都这么写就变成：

```
已在方法 assignValue2JavaBeanCREATE_ENTITY_xxx(...) 中定义了变量 _FLOW_INPUT_xxx
```

**必须**按字段引用：`position="children"`、
`key="<入参名>_<DTO全名>.<字段>"`、`path="<DTO去点>.<字段>"`、`name=<纯字段名>`。

### DSL

```json
{"id": "sm", "kind": "sub_microflow", "sub_name": "子流程名",
 "inputs": {"taskId": {"const": "X"}, "processedRows": {"const": 7}}}
```

### 实测

```
父流程 → 子流程（入参 DTO = 迁移断点）
  写库结果：task_id='P6SM03-DTOIN'、processed_rows=7、source_table='SUBDTO'
```

### 连带事故（备忘）

残留的坏流程会让**整个应用**编译失败，且报错会扩散到平台胶水类
（`DefaultCustomMicroFlowConfig`、`MicroFlowAppServiceImpl` 报「找不到符号: 变量 log」）。
删掉坏流程后重建即 SUCCESS —— 看到大范围 `log` 找不到，先查自己有没有留坏流程。

## 9. ★ 标量入参 value.desc 用「子流程入参字段名」，不是父流程变量名（2026-11-04）

标量入参（`dataType != DTO`）走 `mappingType="value"` + `value` 引用父流程变量。
但 `value.selectParam.desc` 若用父流程变量名（如 `reqId`），前端「参数」栏显示
`reqId [长整数]`，用户**看不到映射到子流程哪个入参**（MF-00 的「采购申请ID」）。

正确：`value.selectParam.desc` / `value.desc` 用**子流程入参**的 `desc/description`
（「采购申请ID」），`key/name/outputName` 仍指向父流程变量（引用关系不变，只改显示名）。

```python
# composer._st_sub_microflow 里：inp = 子流程入参（microflow_detail.input）
in_desc = (inp.get("desc") or inp.get("description") or "").strip()
value["selectParam"]["desc"] = value["selectParam"]["description"] = in_desc
value["desc"] = f"{in_desc} [{类型中文}]"
```

判据：dump SUB_MICROFLOW 节点的 `value.selectParam.desc` 应等于子流程入参字段名，
不是父流程变量名。
