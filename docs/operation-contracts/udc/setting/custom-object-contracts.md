# 设置域 · 自定义对象操作契约

> 证据等级：LIVE（2026-10-20 GraphQL 探测 + 真实创建/删除实测 + DB 回读）
> 域归属：UDC 九域之「设置」→ 自定义对象 tab
> 事实格：`core/facts/udc/setting/custom-object/create.md`
> 实现：`components/udc/setting/custom_object_constraints.py`

## 入口与定位

设计器：**应用设计 → 设置 → 自定义对象**

业务定位（设计器原文）：
> 支持自定义对象，用于微流程/页面规则之间的相互调用数据传递

落库表：`udc_data_transfer_object`

## 契约清单

| operation_id | GraphQL operation | 方法 | 写 | 状态 |
|---|---|---|---|---|
| `udc.custom_object.create` | `udcDataTransferObjectPost` | POST | 是 | LIVE PASS |
| `udc.custom_object.update` | `udcDataTransferObjectUpdatePost` | POST | 是 | LIVE |
| `udc.custom_object.delete` | `udcDataTransferObjectDeletePost` | POST | 是 | LIVE PASS |
| `udc.custom_object.list` | ——（**平台无查询 operation**） | DB 直读 | 否 | LIVE |

**统一端点**：`POST /service/udc/graphql?<operation>`

**统一 body 形态**：

```jsonc
{
  "query": "mutation graphqlLoader ($params0: <X>InputBody) { \n  data0: <X>(body: $params0) { code data { content } message status } }",
  "variables": { "params0": { /* 真正的 body */ } }
}
```

## 必填槽位与错误字典

| 缺失/非法 | 平台报错 | code |
|---|---|---|
| 缺 `appId` | 应用Id 不能为null | `BOOT_1001` |
| 缺 `appGuid` | —— | `BOOT_1001` |
| 缺 `caption` | 对象显示名称 不能为空 | `BOOT_1001` |
| 缺 `name` | 对象名称 不能为空 | `BOOT_1001` |
| 缺 `source` | source不能为空 | `BOOT_4101` |
| 删除缺 `id` | **仍回 BOOT_0000**，但 `content=0` | —— |

⚠ `name` 是对象编码（英文），`caption` 是显示名（中文）——别对调。
⚠ `appGuid` 取自 `udc_application.guid`，不是 `appId`。

## 平台机制（已证实的"没有"）

| 能力 | 状态 | 说明 |
|---|---|---|
| 查询 operation | **VACUUM** | 探测 40+ 候选全 `FieldUndefined` → 列表走 DB |
| 批量删除 operation | **VACUUM** | `udcDataTransferObjectBatchDeletePost` 等全 `FieldUndefined` → 逐个删 |

**这些是平台事实，不是能力缺失**——不要去"补"不存在的接口。

## 操作探测的判据（枚举域教训复用）

URL 里的 operation 名**不参与** GraphQL 字段解析，所以
「Invalid Syntax: offending token 'body'」对**所有**候选都出现，无法区分真假。

正确判据：

```
FieldUndefined: Field '<op>' in type 'Mutation'   ⇒  该字段不存在
其他（BOOT_xxxx / BOOT_1001）                      ⇒  该字段存在
```

## 删除前必做引用分析

```bash
python tools/core/setting/custom_object_reference_analysis.py --app-id <appId>
```

工具会先做**阳性对照**（用已知被引用的实体名验证检测方法），对照不通过时退出码非 0，
此时"无引用"结论不可信。

本应用实测（2026-10-20，230 个对象）：

```
引用源    707 个（资源 610 / 导出模板 45 / 微流程 20 / 页面信息 14 / 实体 10 / 页面 8）
阳性对照  4/4 → 方法有效
有引用    6 个（不可删）
无引用    224 个（仅查 name/caption）
```

补查 id/guid 形式后：有引用 6、无引用 223（20 号漏判的 4 个是 id 形式引用）。

## 2026-10-21 批量删除（用户授权）

用户明确指令删除后执行，对象数 **229 → 4**（6 个有引用 → 用户手工删掉 2 个导出模板相关的，
剩余 4 个仍被微流程引用，是迁移链的真实数据载体）。

```
预检   custom_object_delete_precheck.py
       备份 229 行全列 → <HERMES_HOME>\backups\custom-object-delete-20261021-105341\
       引用源 707，阳性对照 4/4 有效，四种引用形式全查
       candidates 223，referenced 6
执行   custom_object_delete_batch.py --i-have-write-authorization
       逐个删 + 逐行回读，223/223 成功，0 失败，progress.json 可续跑
复验   重新跑引用分析：707 源无新增悬空引用
```

剩余 4 个（全部被微流程引用，保留）：

```
5756609313379862991  DataSourceTestDTO           1.6数据源测试出参      微流程 ×2
143200354095678405   pddqqyfasfczzxtyzbcc        判断当前启用方案…出参   微流程 ×2
8251073728930991987  pddqqyfasfczzxtyzbrc        判断当前启用方案…入参   微流程 ×2
3770622987513249942  SyncNowDto                  立即同步入参           微流程 ×2
```

## 两条实测陷阱

1. **删除成功码不可信**：缺 `id` 时平台仍回 `BOOT_0000` 但 `content=0`，判据只能是 DB 回读。
2. **设计器列表有前端缓存**：接口删完后表格可能仍显示旧数据（实测 DB 只剩 6 行时页面仍显示 229 个）。
   页面验收须切 tab / 刷新；权威判据永远是 DB 回读。

## 判定口径

"无引用 ≠ 可删"依然成立，但**删不删由用户授权决定，不由脚本的无引用结论决定**。
脚本职责：把引用面、阳性对照、全量备份摆出来，让人有据可决。

## 写操作授权

写面必须显式传 `WriteScope`（应用白名单 + 操作白名单 + 次数上限），默认 fail-closed。
失败即停，不重试。见 `components/platform_operations/write_scope.py`。
