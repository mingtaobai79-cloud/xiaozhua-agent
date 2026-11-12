# BREAK（跳出循环）运行时契约

> 2026-11-02 实测于 test2。**这是目前发现的最隐蔽一类错误**：所有闸门都绿、构建成功、
> 运行 success=true，但节点根本没生效。

## 1. ★★★ `type` 必须是 `BREAK`，不能是 `ACTIVITY`

### 现象

第一轮验证把 BREAK 构造成 `{"type": "ACTIVITY", "actionType": "BREAK"}`（从模板骨架取的），
一条流程里放两个 `FOR_COUNT(1..3)` 互为对照：

```
对照 lpA：body = [CREATE_ENTITY(taskId=MARK+'N')]          → 期望 3 行
实验 lpB：body = [CREATE_ENTITY(taskId=MARK+'Y'), BREAK]   → 期望 1 行
```

实测结果：

```
构建: ok=True state=SUCCESS 224s
运行: success=True（每个节点都 success）
库内: P5BRK613143N = 3 行   ← 对照，正常
      P5BRK613143Y = 3 行   ← 实验，BREAK 完全没起作用
```

**零报错**。构建、发布、运行、节点日志全部正常。

### 根因（字节码 + 代码生成模板双证）

1. `MicroFlowParser.node()`：

```java
String type = NodeUtils.getString("type", node, true, location, result);
if (!MicroFlowNodeTypeEnum.isInclude(type)) { result.error(...); return null; }
MicroFlowNodeTypeEnum nodeType = MicroFlowNodeTypeEnum.valueOf(type.toUpperCase());
if (ACTIVITY.equals(nodeType) && ActivityNodeTypeEnum.isInclude(actionType)) {
    activityNodeType = ActivityNodeTypeEnum.valueOf(actionType.toUpperCase());
}
NodeParser parser = NodeParserFactory.createNode(nodeType, activityNodeType);
```

`MicroFlowNodeTypeEnum` 只有 8 个值：
`CONDITION / FOR_EACH / BRANCH / CUSTOM_ERROR / END / ACTIVITY / FOR / BREAK`。

`type="ACTIVITY"` → 解析成普通 Activity；而 **`ActivityNodeTypeEnum` 里没有 BREAK**（0 处命中），
`activityNodeType` 为 null，于是走了通用 Activity 解析器。

2. 代码生成模板 `MicroFlowDomainService.java.ftl` 按 **`node.type`** 分发：

```ftl
<#switch node.type>
  <#case "Activity"> <@nodeActivityHandler .../> <#break>
  <#case "Branch">   ...
  <#case "For">      ...
  <#case "Break">    break;   ← 只有这里才会生成 break;
</#switch>
```

`nodeActivityHandler` 里**没有** `case "BREAK"`（0 处）→ 什么都不生成 → 节点被静默丢弃。

### 正确形态

```json
{"nodeId": "BREAK_xxx", "type": "BREAK", "actionType": "BREAK",
 "caption": "跳出", "output": null}
```

### 验证（修复后）

同一实验重跑（`p5brk613966`，构建 224s，执行 18:12:00）：

```
P5BRK613966N = 3 行（对照，跑满 3 次）
P5BRK613966Y = 1 行（实验，第 1 轮就跳出）
```

同一次构建、同一条流程、同一份数据，**3 : 1** —— BREAK 生效。

## 2. BREAK 没有配置项

`BreakNode.parse()` 直接 `return new BreakNode()`，**完全不读节点 JSON**。
`nodeLogicCheck()` 只用 `use` 字段判「是否在循环内使用」：

```java
if (!this.use) CheckUtils.error(..., "请在循环内使用循环终止节点");
```

`use` 由 `AbstractForNode.parse()` 在解析完循环体后调用
`NodeUtils.setBreakNodeUse(allNodes)` 置位。所以：

- BREAK 只能放 FOR / FOR_EACH / FOR_COUNT 的 body 内（放外面平台会报错）
- 它**不需要**任何字段（不像其它节点要 selectParam/attrs）

## 3. ★★ 删除流程不会停掉已注册的定时任务

实测：`p5brk613143` 在 17:58 被删除（`DP.delete → True`，平台流程列表里已查不到），
但它的定时任务继续执行——18:03、18:08 仍在往库里插数据。

```
ctp_job_info:  job_caption=p5brk613143, is_delete=1
ctp_job_simple: job_name=ecc9040d98594b83, repeat_interval=5(分钟), is_delete=1
```

即使两表都标了 `is_delete=1`，调度器仍按缓存触发；已构建进应用包的产物也还在。

**收尾顺序**：删流程 → 清数据 → **再构建一次（让包里不再包含该流程）** → 等一个周期复查。
只删流程不清数据、或只清数据不删流程，都会持续长出新数据。

## 4. 仍不能证明的

- BREAK 在 `FOR_EACH`（列表循环）里的行为未单独验（本轮只验了 FOR_COUNT）
- 嵌套循环里 BREAK 跳哪一层未验
- BREAK 放在 BRANCH 里（`if 条件 then break`）未验
