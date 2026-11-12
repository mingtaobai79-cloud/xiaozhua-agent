# udc.serial + udc.application.draft + role + node-tree｜运行态只读四格（LIVE 2026-09-25）

> 合格说明：四面对象小、证据同批（09-25 15:5x 探测），按能力族合并。逐条可拆。

## 1. Capability / 3. Input / 5. Execution（实测响应）
| 能力 | 端点({PF}=/service/{app}) | 入参 | LIVE 结果(09-25) |
|---|---|---|---|
| udc.serial.select_entity_list | GET /udc-runtime/serial-config/select-entity-list?appName={app} | appName | BOOT_0000，content.groups/entities 清单（含 fullName 实体族） |
| udc.application.draft.select | POST /udc-runtime/app-draft/select | {"data":"<dataId>"} | BOOT_0000，真草稿 dataId=4854586837685616411 + draftData(JSON 串，含字段 _display 形态) |
| udc.role.has_system_admin | GET /udc-runtime/udc-role/has-system-admin/{app} | appName | BOOT_0000，content=true（当前凭据用户为该 app 系统管理员） |
| udc.microflow.function_node_tree | GET /udc-runtime/meta-data/select-function-node-tree/{app} | appName | BOOT_0000，节点树数组（id=23088985804278345…children/code 结构） |

## 2. Version：Canonical=5.3.517（registry javap 锚点）。
## 4. Required：GET 面 appName 必填；draft.select 为 MultiRequestBody 裸 dataId（`{"data":...}` 包装实测可通）。
## 6. Side Effects：全只读。
## 7. Known Constraints
- 四面全在 `udc-runtime/` 前缀白名单内（同 meta-data 族）；无 PF 直挂被 nginx 挡（09-24/25 两次 403 事件）。
- draftData 是**字符串内嵌 JSON**（双层序列化），消费方需二次 json.loads。
- node-tree 的 children/code 字段语义（微流程节点树）与 docs/plans/2026-09-17-microflow-readonly-milestone.md 微流程只读族同面。
## 8. Evidence：本会话 09-25 15:5x 探测原响应（traceId 3247010114032371900/3247010154532571324/3247010158592657596/3247010162132650172）+ registry 契约行。
## 9. Verified：LIVE×4。
