# 实体/规则/菜单 三模块修复 —— LIVE 完成记录（2026-10-15）

> 应用 datamigration9000000000000000001（test2）。
> 起点：一致性检测 **9 阻断 + 7 警告**，构建 1.0.13 **FAIL**。
> 终点：**0 阻断 + 9 警告**，构建 **1.0.14 SUCCESS**。

## 0. 结果

| 指标 | 修复前 | 修复后 |
|---|---|---|
| 阻断(ERROR) | 9 | **0** ✅ |
| 警告(WARN) | 7 | 9 |
| 构建 | FAIL（1.0.8~1.0.13 六连败） | **SUCCESS（1.0.14）** |

构建返回原文：`{"state":"SUCCESS","jarVersion":"1.0.14","msg":"内部流水线构建成功"}`

## 1. 02104「字段关联枚举不存在」（阻断）→ 已修

**根因**（字节码 + DB + A/B）：
CTPENUM 字段的 `relationEntity` 必须是**平台枚举** `ctp_enum` 的 id，不是选项集 `udc_enum` 的 id。
检测器拼前缀 `com.seeyon.boot.starter.enums.domain.entity.CtpEnum.<值>` 去查（`AttributeMatchDetectionUtils` @ udc-biz 5.3.517）。

**修复（全 REST，实测）**：
```
POST /service/udc/enum          （EnumController @ boot-starter-enums-5.3.308，★不在 udc-web 674 契约里）
  body = {name:'{"zh_CN":"小爪平台枚举"}', code:'XzhCtpEnum953322', appId, appGuid,
          enumType:'SAME_LEVEL', expansible:true, enable:true, appId:..., ...}
  → content = "4456389269786582653"
POST /service/udc/entity/attribute/update
  body = 属性 DTO，relationEntity=4456389269786582653
         relationEntityName='小爪平台枚举' relationCode='XzhCtpEnum953322' relationApp=<appId>
→ 02104 = 0
```
读面：`GET /service/udc/enum/{id}`（返回 ctp_enum DTO）。
端点 base=**`udc/enum`**（不是 `udc-enum`，后者是选项集）。

## 2. 03104「控件事件关联微流程不存在」（阻断 ×4）→ 已修

**根因**：详情页 schema 是从**工作副本模板页**（`8898789886076928593`）复制来的，连带继承了模板的页面规则调用：
```
childById.button_aYoz.events[0].microFlow                     = 8326676356351414116
childById.udcToolBar_oytl.events[0].condEvents[1].microFlow   = 7300360210126816273
```
这两个微流程存在，但 `source_id=8898789886076928593`（模板页）→ 不属本页 → 03104。

**修复**：从两页 schema 移除上述绑定（button 事件整条、toolbar condEvents[1]），`udcPageInfoUpdatePost` 重存 → DB 回读确认 `page_schema LIKE '%8326%' = 0`、`draft_page_schema = 0` → 03104 = 0。

## 3. 04004「微流程入/出参 依赖应用已删除 / OpenApi 不匹配」（阻断 ×4）→ 已修

**根因（同应用对照实证）**：
```
小爪REST微流程     trigger.output.appName = 'datamigration9000000000000000001' → 无 04004 ✓
小爪实验微流程953182 trigger.output.appName = null                            → 04004 ×4 ✗
```
（我此前把 appName 置 null 恰好把它改坏了。）

**修复**：`input/output/trigger.output/endNode.output` 的 `appName/inApp/udcApp` 置回本应用 → `checkSchema` + `update` → 04004 = 0。

## 4. 剩余警告（不阻塞构建）

| 码 | 数量 | 对象 | 说明 |
|---|---|---|---|
| UDC_CE_MICRO_FLOW_04003 | 7 | 6 条微流程 + 1 页面规则 | 「未保存的微流程或者页面规则」 |
| UDC_MICRO_FLOW_04009 | 1 | 页面规则 [11] | 同上（页面规则版） |
| UDC_CE_FUNCTION_NODE_08100 | 1 | 菜单[小爪验收菜单] | 空目录未设默认页 |

（08100 的对象 `-1628253460115858501` 是**空目录**（无子节点）→ 无处可设默认页；属实验遗留，需清或补子节点。）

> **第二十六轮更正**：上句「空目录无处设默认页」**措辞不准确**。CFR 判据是「无子节点 **或** 无 `type==MENU` 的子节点」⇒ 子节点全为 PAGE 时仍算「空目录」，WARN 文案是「未设默认页」，**真实充分条件是「无子页面可指向」**。已 LIVE 补一个 PAGE 子节点即清零（WARN 9 → 8），详见 `core/facts/udc/write-chain/menu-default-page-write-chain.md`。

## 5. ★ 机制纠正（我此前的错误结论，必须覆盖）

| 我早前的说法 | 实测真相 |
|---|---|
| "检测面读缓存/上次发布产物，改了 DB 不动" | **错**。`POST /udc/application/do/detection` 是**异步**的——必须轮询 `do/detection-state` 到 `status!=doing` 再读 `search/detection`；否则读到上一轮快照，表现为"改了不动"。修正后每改必变。 |
| "CTPENUM = 选项集（udc_enum）" | **错**。CTPENUM 关联 `ctp_enum`（平台枚举）；`udc_enum` 是"选项集"（字段类型 `ENUM`）。前端字段清单本来就是两项。 |
| "枚举域已打通 ✅" | **错**。那是选项集；平台枚举从未建过，且其端点组 `boot-starter-enums` 完全不在 udc-web 契约里。 |

## 6. 复现脚本（scratch）

- `ctpenum_create.py`：建平台枚举
- `fix_03104b.py`：清详情页继承的事件绑定（DB 直读 → REST 重存）
- `fix_04004.py`：修微流程入出参 appName
- 检测统一范式：`do/detection` → **轮询 `do/detection-state`** → `search/detection`

## 7. 下一步（本轮未完）

1. 04003×7 / 04009：显式保存/提交那 6 条微流程 + 1 条页面规则，消警告。
2. 08100：处理空"小爪验收菜单"。
3. 实体 1.2：`is_not_null/uniqueness/default_value/calculate` 逐项 LIVE（**至今全为 0，未测**）。
4. 实体 1.3 事件 / 1.5 参照：`udc_event=0`、`udc_refer_config=0`，建+回读。
5. 规则条件结构：按真实样本修 `leftParam/operator/rightParams/logicalOperator`，并补校验器。
6. 生单规则 / 扣减规则域（用户点名要补，未动）。
