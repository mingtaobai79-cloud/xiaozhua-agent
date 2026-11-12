# 流程重发幂等（NODE_ID_STABLE_BY_ALIAS）

> 2026-11-02 实测 + 修正

## 现象

设计器标红 `所选"单条数量"已变更`，但平台校验通过、构建 SUCCESS、运行结果正确。

## 根因

节点 id 原来是 `f"{action}_{uuid4().hex[:6]}"`（`node_builder._new_id`），
每次 compose 都是新的随机值，出参名 `_" + nodeId` 和下游引用名跟着一起变。
把整张 schema 重发到同一个流程 id，等于**整图换节点**：
服务端上原来那个节点已不存在，设计器里开着的那份副本一比对就报「已变更」。

后果不止红字：

- 设计器上人工点确认，可能把节点搞乱
- 页面规则 / 其他流程 / 报表引用该节点 → **断链**
- 反复重发，服务端堆孤儿节点

## 修正

`nodeId` 改为按 `(actionType, 逻辑图别名, 该别名下第几次)` 派生：

```python
seed = "%s|%s|%d" % (action, node_key, n)
return "%s_%s" % (action, hashlib.md5(seed.encode()).hexdigest()[:6])
```

- `composer.step(kind, alias)` 是唯一收口点，进节点前设 `builder.node_key = alias`
- 分支内 `CONDITION_*` 不走 step，`logic_graph._exec_branch` 里手动设同一个 key
- 没有 key 时仍随机（单测/临时构造不受影响）

## 实测（2026-11-02，`p5idemprobe`）

| 场景 | 结果 |
|---|---|
| 同一张图 compose 两次 | nodeId 完全一致 |
| 同图重发到同一流程 | **节点 id + 出参名 + 引用名全部不变** |
| 中间插入一个新节点 | 原有节点 id 全部保持（新节点另得新 id） |

```
① 首次发布: 查=RETRIEVE_ARRAY_4172f6 数数=LIST_OPERATION_ec3ac4 写=CREATE_ENTITY_023d3a
② 同图重发: 查=RETRIEVE_ARRAY_4172f6 数数=LIST_OPERATION_ec3ac4 写=CREATE_ENTITY_023d3a
   节点 id 与引用完全不变: True
③ 插入节点后: 查/数数/写 全部保持，新节点=CREATE_ENTITY_83b52d
```

## 边界

- 别名是种子，所以**改别名 = 换节点 id**（例如把 `sz` 改成 `sz2`）
- 同一别名下建多个节点时按序号区分，删掉中间那个会让后面的序号前移
  → 改图时尽量「新增别名」而不是「删了重建同名别名」

## 相关

- 设计态「属性已更新 / 所选 xxx 已变更」都是**引用新鲜度**提示，不挡构建、不挡运行
  （同族：`SUB_MICROFLOW_SCHEMA_COMPATIBILITY_CHECK`，那个是构建期才拦）
- 平台保存时**不会**改写出参名（探针：发布前后 `name`/`outputName` 一致）
