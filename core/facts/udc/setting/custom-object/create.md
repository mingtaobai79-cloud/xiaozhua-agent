# 自定义对象（DataTransferObject）域事实格

> 前置：本文所有 `udc*Post` 必填的 `appGuid`，取法见 [`precondition-appguid.md`](../precondition-appguid.md)（用 `udcApplicationDetailGet` 接口查，appGuid ≠ appId，无需查库）。
> **域归属**：UDC 九域之「设置」→ 自定义对象 tab
> **证据等级**：LIVE（2026-10-20 GraphQL 探测 + 真实创建/删除实测 + DB 回读）
> **落库表**：`udc_data_transfer_object`
> **实现**：`components/udc/setting/custom_object_constraints.py`
> **契约**：`docs/operation-contracts/udc/setting/custom-object-contracts.md`
> **skill**：`skills/seeyon-udc-setting/SKILL.md`（自定义对象节）

## R-E1 Capability

| 能力 | operation / 方式 | 方法 | 写 | 状态 |
|---|---|---|---|---|
| 创建 | `udcDataTransferObjectPost` | POST GraphQL | 是 | **LIVE PASS** |
| 更新 | `udcDataTransferObjectUpdatePost` | POST GraphQL | 是 | LIVE（必填实测，语义未跑） |
| 删除 | `udcDataTransferObjectDeletePost` | POST GraphQL | 是 | **LIVE PASS** |
| 列表 | **无 GraphQL 查询 operation** | DB 直读 | 否 | LIVE（平台事实，非缺失） |

**统一端点**：`POST /service/udc/graphql?<operation>`

**body 形态**：

```jsonc
{
  "query": "mutation graphqlLoader ($params0: udcDataTransferObjectPostInputBody) { \n  data0: udcDataTransferObjectPost(body: $params0) { code data { content } message status } }",
  "variables": { "params0": { /* 真正的 body */ } }
}
```

## R-E2 Version

- 平台 `udc-web` 5.3.517（`UdcDataTransferObjectController`）
- 网关 `https://lowcode-test2.example.com`（测试环境；文档内统一用 example.com 代号）
- 设计器入口：应用设计 → 设置 → 自定义对象
- 业务定位（设计器原文）：**「支持自定义对象，用于微流程/页面规则之间的相互调用数据传递」**

## R-E3 Input（必填槽位，BOOT_1001 逐字段探针实测）

```jsonc
{
  "appId":   "<appId 字符串>",      // 应用Id 不能为null
  "appGuid": "<udc_application.guid>",  // 取自 udc_application.guid，不是 appId
  "caption": "显示名",                // 对象显示名称 不能为空
  "name":    "objCode",              // 对象名称（编码）不能为空
  "source":  1                       // source不能为空（BOOT_4101）
}
```

⚠ `name` 是**对象编码**（英文），`caption` 是**显示名**（中文）——平台报错文案分别叫
「对象名称」与「对象显示名称」，别对调。

⚠ `appGuid` ≠ `appId`：`appGuid` 取自 `udc_application.guid`，
填 appId 会被拒。

## R-E4 Required（错误字典实测）

| 条件 | 平台报错 | code |
|---|---|---|
| 缺 appId | 应用Id 不能为null | `BOOT_1001` |
| 缺 appGuid | — | `BOOT_1001` |
| 缺 caption | 对象显示名称 不能为空 | `BOOT_1001` |
| 缺 name | 对象名称 不能为空 | `BOOT_1001` |
| 缺 source | source不能为空 | `BOOT_4101` |
| 缺 id（删除时） | **仍返回 BOOT_0000**，但 `content=0` | — |

⚠ **删除的成功码不代表删掉了**：缺 id 时平台回 `BOOT_0000` / `content=0`。
必须回读 DB 核对，不能只看 `code`。

## R-E5 Execution

```python
from components.udc.setting.custom_object_constraints import (
    build_custom_object_body, validate_custom_object_body,
    build_custom_object_delete_body, validate_custom_object_delete_body)

body = build_custom_object_body(app_id, app_guid, caption="显示名", name="objCode")
errs = validate_custom_object_body(body)     # 空 = 通过
POST /service/udc/graphql?udcDataTransferObjectPost
```

**代码落点**：
- 构造器 + 校验器 `components/udc/setting/custom_object_constraints.py`
- 契约 `components/platform_operations/registry.py`（4 条 `udc.custom_object.*`）
- 引用分析器 `tools/core/setting/custom_object_reference_analysis.py`

## R-E6 Side Effects + 回滚

| 动作 | 副作用 | 回滚 |
|---|---|---|
| 创建 | `udc_data_transfer_object` 增 1 行 | `udcDataTransferObjectDeletePost` |
| 更新 | 同表行更新 | 无快照；改前先读原值 |
| 删除 | 同行删除（返回 content = 实际条数） | 无 |

⚠ **删除前必须做引用分析**（微流程/页面规则会引用这些对象）——
删了会让引用方悬空，表现为微流程运行失败。

## R-E7 Known Constraints

1. **平台无查询 operation**：探测 40+ 候选（`SearchPost`/`QueryPost`/`PagePost`/`ListPost`/
   `AllPost`/`GetPost`/`TreePost` 等 × `DataTransferObject`/`CustomObject`/`DataObject`
   三种实体名）全部 `FieldUndefined`。→ 列表走 DB 直读。
   **这是平台事实，不是能力缺失**——不要去"补"一个不存在的接口。

2. **无批量删除 operation**：`udcDataTransferObjectBatchDeletePost` 等均 `FieldUndefined`。
   删除只能逐个调 `udcDataTransferObjectDeletePost`。

3. **删除成功码不可信**：缺 id 时回 `BOOT_0000` / `content=0`。必须回读 DB。

4. **删除的引用面很窄但真实**：本应用 230 个对象里 **仅 5 个被引用**
   （引用源：微流程 20 / 页面 8 / 导出模板 45 / 页面信息 14 / 实体 3），
   其余 225 个无引用。阳性对照（实体名）4/4 命中，检测方法有效。

5. **字段探测判据**（枚举域教训复用）：URL 里的 operation 名**不参与** GraphQL 字段解析，
   所以「Invalid Syntax: offending token 'body'」对所有候选都出现，无法区分真假。
   正确判据是 **`FieldUndefined: Field '<op>' in type 'Mutation'` ⇒ 该字段不存在**。

## R-E8 Evidence（逐条实测，禁转述）

- 创建 LIVE：body `{appId, appGuid, name, caption, source}` → `BOOT_0000`，
  content=`3554785288460535088`，traceId `3283038013688383676`
- 删除 LIVE：`udcDataTransferObjectDeletePost` 缺 id → `BOOT_0000` / `content=0`
  （证明成功码不可信）
- 引用分析：230 个对象 → 5 有引用 / 225 无引用；阳性对照 4/4
- 落库回读：`udc_data_transfer_object` 本应用 230 行（分析前 229 + 本轮新建 1）

## R-E9 Verified

| 项 | 等级 | 备注 |
|---|---|---|
| 创建 | **LIVE PASS** | BOOT_0000 + content 拿到 id + DB 回读 |
| 删除 | **LIVE PASS** | 成功码语义已坐实（含 content=0 陷阱） |
| 更新 | LIVE | 必填已实测，未跑成功更新 |
| 列表（DB 直读） | LIVE | 230 行读出 |
| 引用分析 | LIVE | 阳性 4/4 对照有效 |
| 批量删除 | **VACUUM** | 平台无该 operation —— 但**脚本实现**了逐个删的批量执行器 `custom_object_delete_batch.py`（回读门 + 可续跑），223 条实测 0 失败 |
| 查询 operation | **VACUUM** | 平台无该 operation（列表走 DB） |
| 对象字段定义（字段集/属性） | **UNVERIFIED** | 需进一步抓 `udc_data_transfer_object_field` 类表与接口 |

## 待删除清单

| 对象 | 判定依据 | 处置 | 状态 |
|---|---|---|---|
| `zxjProbeObject`（探针对象，id 3554785288460535088） | 本轮为探测接口而建的探针，无引用 | 删 | **DONE**（2026-10-20 21:30，平台 `content=1` + DB 回读确认行已消失，对象数 230→228） |
| `xzhEvtA1`（小爪事件A1，id 4112540037455973528） | 命名是实验残留且无引用 | 删 | **DONE**（2026-10-20 21:30，同上，228→227） |
| `DataSourceTestDTO`（id 5756609313379862991） | 名字像测试但**被 2 个微流程引用** | **不可删** | 保留 |
| 223 个无引用对象（含验收对象 `zxjAcceptObject`） | 引用分析无引用；用户 2026-10-21 明确指令「删除吧」 | 删 | **DONE**（2026-10-21 10:54，逐个 `BOOT_0000` + 每行 DB 回读确认消失，对象数 229→6，`progress.json` 223 条全成功、0 失败） |
| 剩余 6 个（被引用） | 4 个微流程引用 / 2 个导出模板+资源引用 | 保留 | 保留 |

⚠ 2026-10-21 删除口径说明：这一轮是**用户明确指令后执行的批量删除**，不是"无引用即删"的自动结论。
删前的闸门证据（`custom_object_delete_precheck.py` 产出）：
引用源 707 个、阳性对照 4/4 有效、按 name/caption/id/guid 四种形式全查。
全量 229 行完整备份：`<HERMES_HOME>\backups\custom-object-delete-20261021-105341\udc_data_transfer_object.json`。
**应用包的「设计资产」判断在这批对象上被推翻**：它们虽同一秒导入，但确实零引用，删除后引用面（707 源）无新增悬空引用。
这条记录的是「用户授权下的批量清理」，不能反过来当作"以后无引用就能删"的先例——仍须逐个过阳性对照闸门。

## 本轮实际动作记录（可复算）

```
删除前引用核对  引用源 707 个 | 阳性对照 3/3 → 方法有效 ✅
                zxjProbeObject 引用：无 ✅
                xzhEvtA1       引用：无 ✅
删除 zxjProbeObject  BOOT_0000 content=1  trace=3283084406129952956
删除 xzhEvtA1        BOOT_0000 content=1  trace=3283084407908337852
回读核对            两条均已从 udc_data_transfer_object 消失；对象数 230→228

创建 zxjAcceptObject（走 seeyon-agent 构造器 + 校验器）
  build : {"appId","appGuid","name":"zxjAcceptObject","caption":"验收自定义对象",
           "source":1,"orderNo":200,"hostAppName":null,"dataStatus":false}
  check : ✅ 通过
  submit: BOOT_0000 content=-6090940344689672614  trace=3283084410458474684
  回读  : id=-6090940344689672614  name=zxjAcceptObject  caption=验收自定义对象
          source=1  publish_state=1  create_time=2026-10-20 21:31:20
  对象数: 228 → 229
```

**执行器**：`tools/core/setting/custom_object_write.py`
（delete / create / list 三个子命令；写操作需 `--i-have-write-authorization` 显式确认）
