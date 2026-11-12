# 分组与批量管理（建组 / 清组 / 批量生成 / 部署锁）

交付验收常要求「清空某个分组 → 新开分组 → 放 N 条流程」时走这里。

## 1. 分组 API

| 动作 | 调用 | 关键点 |
|---|---|---|
| 列分组 | `POST /service/udc/graphql?udcMicroFlowGroupSelectByTypePost` body `{appId, type:"BACKEND_SERVICE"}` | 返回分组维度数据（id/caption/preset/orderNo），不是流程 |
| 建分组 | `udcMicroFlowGroupCreatePost` body `{appId, caption, type:"BACKEND_SERVICE", sourceId:"-1"}` | 返回 `data.content` = 新分组 id（字符串） |
| 列流程 | `udcMicroflowSearch` body `{pageInfo:{needTotal:true,pageNumber:1,pageSize:100}, params:{appId}}` | 用返回的 `microFlowGroupId` 判归属 |

★ **`udcMicroFlowGroupCreatePost` 的 F 是大写**；写成 `udcMicroflowGroupCreatePost` 会报
`Unknown type ...InputBody` + `FieldUndefined`，看着像接口不存在，其实是大小写。

## 2. 清组：按 groupId 过滤，绝不按 caption 猜

```python
cc = search_flows(app_id)
mine = [x for x in cc if str(x.get("microFlowGroupId")) == TARGET_GROUP]
for x in mine: DP.delete(host, ck, x["id"])
```

同一应用里通常至少三个组：根分组（用户自己的流程常在这里）、默认分组、以及你新建的组。
**按 caption 前缀删会把用户的流程一起删掉**；删前先把待删清单打印出来核对条数。

## 3. 批量生成到一个新分组

1. 建组拿 id；2. 生成脚本里 `publish(..., group_id=新组id)`；3. 脚本支持 `sys.argv` 按名跑，
改一条不用重跑整批；4. 每条 publish 后立刻 `prove()`，失败当场定位到那一条。

节奏：单条 publish 约 20–60 秒（含 checkSchema），一批控制在 10 条以内，超过就分轮。
难度分档用节点数说话：简单 2–3 节点（查/统计/出参）、中等 4–6（含分支或循环）、
困难 7–9（循环+字段映射+批量写+分支+自定义错误）。

## 4. 部署锁

- `deploy-normal` 返回 `code=UDC_DEPLOY_0002 / message="app publishing"` = 上一个部署还占着锁，
  等它跑完，或 `POST /service/udc/runtime/deploy/stop/{deployId}` 释放后再发。
- 同一应用**不能并发构建**；前一次卡在 PUBLISHING 时新构建会 FAIL 或排队「沙箱全忙」。
- 构建结论只认 `backBuild.log` 的 `BUILD SUCCESS/FAILURE` + 报错行，`search-deploy-status` 的 state 不算。

## 5. 清理验收/验证流程：删前脱敏归档，删后重建收尾

删除实验期验收流程（验证-* / 探针流）的固定顺序：

1. **归档**：逐条拉 `dataSchema`，把真实字面量替换成仓库标准假值
   （app 名→`datamigration9000000000000000001`、域名→`lowcode-test2.example.com`、
   真实 appId→假 id），落 `_attic_pending/verification-flow-schemas/<形态名>.json`——
   这些是已验证形态的唯一离线模板，直接删会丢证据。
2. **删除**：`DP.delete(host, ck, mid)`（`udcMicroflowDeletePost`），逐条打返回值。
3. **重建收尾**：`udcRuntimeDeployNormalPost`（RELEASE）→ 轮询 `udcSandboxBuildInfoAppGet`
   → BUILD SUCCESS 才算清完（删除本身不触发重建，残留引用要靠这轮暴露）。

### ★ 列举时必须包含 DRAFT，不能只用 `sub_mf_candidates()`

`LiveRefs.sub_mf_candidates()` 只返回 `state=RELEASE`。而**发布失败的流程停在 DRAFT**，
恰恰是这些失败品最需要清——用它会漏掉一半，且删完“看着干净了”。
直接调 `udcMicroflowSearch` 拿全量再按名前缀筛：

```python
q = ("mutation g($p: udcMicroflowSearchInputBody) { data0: udcMicroflowSearch"
     "(body: $p) { code data { content { id name state } } message } }")
# 删前把名字+state 全打出来核对条数，按名字前缀匹配，别按 caption 模糊删
```

### ★ 定时流程不删会一直生产数据：先删流程，再清数据

调度型验收流程（`SCHEDULE`）只要还 RELEASE 就按周期不停触发。实测：清完数据后
又冒出一条新行——因为删数据时流程还活着，下一轮调度又插了一行。

正确顺序：**删流程 → 重建应用使删除生效 → 再清数据 → 复查残留为 0**。
用 `DELETE ... WHERE <标记字段> LIKE '<前缀>%'` 前先 `GROUP BY` 看影响行数，
不做无范围删除；清完再 `COUNT(*)` 复核一次。

## 6. 构建被「一致性检测未通过」挡住时

先拉明细再归因：`udcApplicationSearchDetectionPost` → `content[]`，按流程名/id 过滤。
应用既有问题（循环内调服务的警告、选项集缺项、生单规则 ID 映射）同样会挡住构建，
**不要归因到刚生成的那几条流程上**；自有流程的问题再逐条修。
