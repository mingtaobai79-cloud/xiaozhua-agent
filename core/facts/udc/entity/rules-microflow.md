# 规则域（实体规则/Microflow 三类）— LIVE 证据

> ⚠️ **已并入** `rule-domain.md` §5（三类规则的 radio 值 / groupType / 初始 state 对照表）
> 与 §4（编辑器：SPAN 按钮、设计器锁、表达式 schema）。本文件保留作历史记录，
> 内容不再更新；查规则域契约请用 `rule-domain.md`。


> 状态：LIVE PASS，2026-10-23 实体域取证。全部实验数据已复原（实体回 10 条基线）。

## 1. 三类规则（UI 新建弹窗 radio）

| 类型 | radio 值 | groupType | 初始 state |
|---|---|---|---|
| 校验 | VALIDATE | DEFAULT_VALUE | RELEASE（保存并提交后） |
| 计算 | ASSIGN_VALUE | ASSIGN_VALUE | DRAFT |
| 页面默认值 | DEFAULT_VALUE | ASSIGN_VALUE | DRAFT（列表显示"计算"） |

类型差异在 microflow schema 内部；列表 `groupType` 不可反推 UI 类型。

## 2. 契约 ops

- 列表：`udcMicroflowSearchEntityRulePost` body `{pageInfo:{needTotal,pageNumber,pageSize}, params:{sourceId:<entityId>}}`
  - `params` 只要 `sourceId`（appId 放进去也不报错但非必需）
  - **content 选择器只能选 `{id name}` 级别的合法字段**——`state/groupType/total` 在该 content 类型上不是 GraphQL 字段（FieldUndefined），详情才查得到
- 详情：`udcMicroflowFindByIdGet` path `{appId, id}` → 返回含 id/name/state/groupType/schema
- 删除：`udcMicroflowDeletePost` body `{appId, id}` → BOOT_0000（逐条删，非 ids 数组）

## 3. LIVE 证据（3 条规则全链路）

1. UI 建成 3 条（校验 RELEASE/DEFAULT_VALUE；计算 DRAFT/ASSIGN_VALUE；页面默认值 DRAFT/ASSIGN_VALUE）
2. `udcMicroflowSearchEntityRulePost` sourceId 查询 → 3 条 id
3. `udcMicroflowFindByIdGet` 逐条回读 → state/groupType 与上表一致（rule_details.json）
4. `udcMicroflowDeletePost` ×3 → 全部 BOOT_0000 SUCCESS
5. 删宿主实验实体 → 实体列表回 10 条基线

## 4. 编辑器（UI）

- 规则行「编辑/删除」是 SPAN 不是 button
- 画布：开始→动作→结束，按钮「保存并提交」（校验类提交后 state=RELEASE）
- 设计器锁：`udcMultiEditLockPost`/`udcMultiEditUnlockPost`；表达式 schema：`udcExpressionSchemaPost`
