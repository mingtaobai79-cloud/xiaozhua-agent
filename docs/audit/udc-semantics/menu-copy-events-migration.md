# 复制页面事件随迁实测（P2）——events[].microFlow 重映射完整性核验

> 领域：菜单/导航 → `udcFunctionCopyPost` 复制路径的事件（绑定动作）随迁行为
> 状态：**LIVE PASS**（test2，app `8704025620829192834`，2026-10-17）
> 证据：DB 全量回读（只读 SQL），复用 P1 已留存的 3 份副本对象；全程零写操作
> 接续：`menu-copy-field-behavior.md`（P1）；`main/ROUTE.md` P2（auditor VERDICT 修正 A 之后路线）
> 复现脚本：`session/implementer/p2_ref_integrity.py`、`p2_final_verify.py`（终验表）、`p2_global_census.py`（全库普查）、`p2_events_census.py`（控件级普查）、`p2_eventdefine_check.py`（eventDefine 普查）——全部可重跑

## 0. 结论速览

| 问题 | 实测结论 | 等级 |
|---|---|---|
| 事件是否随迁 | **随迁**。副本页 schema `events`（页面级+全部控件级）与源逐条同构 | LIVE |
| `events[].microFlow` 重映射 | **完整**。24 条事件、21 条 microflow 引用，100% 命中 `udc_microflow_info` 且 `source_id` 全部正确指向新 page_id；失效引用 0 条、残留源 id 0 条 | LIVE |
| 事件 id 是否保留 | **保留**。8 个事件 id（zo8t0o/4UjQux/CNz6jK/Zvosj3/CzP0cV/po3qhP/AYCNxi/jyFpFw）三页完全相同 | LIVE |
| 多事件共用规则 | 正确：8249313647887011099 被 4 个事件引用，副本内全部改指**同一个**新 id，未拆散 | LIVE |
| eventDefine 是否恒空 | **否**。全库 1561 行 schema 中 12 行非空（事件定义=抛出事件的参数 schema，与 events 是两个独立字段）；本轮三页均为空，样本内恒空 | LIVE |
| 未重映射残留 | `schema.relationGroupId`、`schema.pageUrl`、`schema.guid` 三处照抄源值（不影响事件执行路径）；schema JSON 内 `id`/`originId` **已**正确重映射为本页 id | LIVE |
| condEvents 完整性 | **UNVERIFIED**。三页 condEvents 只有 `{id}` 光引用（ZEvUC3/pDtZut），schema 内递归找不到定义体；定义不在 page_schema 内，另一处存储 | UNVERIFIED |

## 1. HANDOFF 前提修正：不需要补事件再复制

HANDOFF 假设「现仅 1 条 onLoad，样本不足」。实测源详情页 `7286622650788629332`
共 **8 条事件**（页面级 1 + 控件级 7，全部 DB 回读）：

| 位置 | eventType | actionType | 源 microFlow |
|---|---|---|---|
| `$`（页面级） | onLoad | microflow | 8249313647887011099（加载数据源信息） |
| childById.input_lHwn | onChange | microflow | 8249313647887011099 |
| childById.button_EHmQ | onClick | microflow | 8600546570895050653（选择对应数据源） |
| childById.input_V7sz | onChange | microflow | 8249313647887011099 |
| childById.input_9drg_1762… | onChange | microflow | 8249313647887011099 |
| childById.button_wEQ2_1762… | onClick | microflow | 8600546570895050653 |
| childById.udcToolBar_5aM6 | PjcMSm0X0B | widget | （无，刷新记录） |
| childById.udcToolBar_5aM6 | PF8Y9CQ6pa | microflow | 521032638709321259（保存） |

事件类型已覆盖 **onLoad / onChange / onClick / widget（工具条）** 四类。
「补事件 + 再复制一次」按 HANDOFF 自身的条件分支（"如样本不足"）不触发，未执行，
也因此本轮零写操作、零新增副本。P1 auditor 只看了 schema 顶层 events（1 条），
是"样本不足"误判的来源。

## 2. 核心交付：microFlow → udc_microflow 引用完整性逐条校验表

样本：P1 留存的三对页面（源 7286622650788629332 → 副本A 3254255197550241742
[菜单 6054953263042158495] → 副本B 8267428021549491279 [菜单 -389182344634194186]）。

**副本A / 副本B 详情页各 8 事件 / 各 7 条 microflow 引用（合计 14 条）：规则存在=YES、caption 一一对应、source_id==本页=YES。**

> 更正（P2 复审 auditor 指出，本轮已独立复验）：原文「两副本全部 16 条 microflow 引用」是
> **事件数（8×2=16）与引用数（7×2=14）串位**。实测副本A 8 事件/7 引用、副本B 8 事件/7 引用。

重映射对照（源 → 副本A / 副本B，逐条实测）：

| 源规则（caption） | 副本A 新规则 | 副本B 新规则 |
|---|---|---|
| 8249313647887011099（加载数据源信息） | 4043450138967163293 | 7362485689270341281 |
| 8600546570895050653（选择对应数据源） | 3215161447089261730 | -1912010165877710289 |
| 521032638709321259（保存） | 6624846897693439808 | -3739553743323322310 |

规则反向覆盖：源/副本A/副本B 三页各 3 条规则，被事件引用 3/3，无孤儿规则。
空副本菜单 -6340030840568160268：0 子页面（P1 静默失败分支，无事件可查，非本缺陷范围）。

> 脚本修正记录：`p2_final_verify.py` 原版 rules dict 用 int id 做 key、JSON microFlow 是 str，
> 导致表1 假阳性「规则存在=NO ×21、失效引用数 21」。已修为 `str(r['id'])` 后复跑，
> 失效引用数 **0**。修数不改结论方向——修正前后对比见本文末尾"校验器自查"。

## 3. 扩大样本：副本菜单全部 6 页（LIVE）

| 页面 | 名称 | 事件数 | microflow 引用 | 失配 |
|---|---|---|---|---|
| 844278122493924338 | 迁移方案配置列表_副本 | 11 | 6 | 0 |
| 1185161788250969507 | 数据源配置信息列表弹窗选择页面_副本 | 5 | 0 | 0 |
| 3254255197550241742 | 迁移方案配置详情_副本 | 8 | 7 | 0 |
| 540101808703999634 | 迁移方案配置列表_副本 | 11 | 6 | 0 |
| -8358257041803639157 | 数据源配置信息列表弹窗选择页面_副本 | 5 | 0 | 0 |
| 8267428021549491279 | 迁移方案配置详情_副本 | 8 | 7 | 0 |

（两份副本菜单各 3 页，两份「列表_副本」是不同 page_id，非同一行重复。）

> **更正（P2 复审，本轮已独立复验）**：弹窗选择页一列的复制源**不是** `5175227629061096197`
> （数据源配置信息列表页，4 事件/0 引用），而是 **`992522359796286320`**（数据源配置信息列表弹窗选择页面，5 事件/0 引用）。
> 实测事件四元组 `992522359796286320 == 1185161788250969507 == -8358257041803639157` 完全相等，
> 而 `5175227629061096197 != 992522359796286320`（前者 4 事件、后者 5 事件）。
> **该页 3 页的引用基数均为 0**，因此它对「microFlow 重映射」结论**不贡献正证据**，
> 只证明「0 引用页复制后仍 0 引用」。原文未声明此点，易被读成「三页都验了重映射」。

## 4. 全库基线：证明重映射是机制完备，不是样本侥幸（LIVE）

`udc_page_schema` 全库 **1561 行**（**取证时点 2026-10-17 16:20**；2026-10-17 22:45 被他域写入
`S2PROBE20261017` 后已漂移为 **1562**，见 §10），递归（含控件级）统计：

- 事件条目 **6595**，其中 microflow 引用 **2327**
- 悬空引用（规则不存在）**6 条** —— 全部指向同一 id `-6114638575851512413`，全在**其他应用**
- 跨页引用（source_id 非本页）**31 条** —— 全在 `page_id=0` 等异常行/其他应用
- **本应用（8704025620829192834）：97 条事件、40 条引用、失配 0**
- 全库失配率 37/2327 ≈ 1.59%，且没有一条落在本应用或本轮副本上

## 5. 边界条件与未重映射残留（LIVE）

| 字段 | 行为 | 影响 |
|---|---|---|
| schema JSON `id` / `originId` | 已重映射为各页新 id（7286…/3254…/8267…） | 无。P1 VERDICT 中"schema id/originId 未重映射"经实测**不成立**，修正 |
| schema.relationGroupId | 残留源值 7427956962460123794（3/3） | 与 P1 auditor 结论一致；不影响事件按 microFlow id 寻址的执行路径 |
| schema.pageUrl | 残留源值 qyfapzxq（page_info.page_url 已加 copy） | 双源 URL 不一致，P1 已登记 |
| schema.guid | **新发现**：三页 JSON 内 guid 完全相同 3748908307771247742（照抄源）；表行级 `udc_page_schema.guid` 却是新值 | 观察项；未定性为缺陷，疑似血缘标记 |
| 规则 guid | 照抄源（三对相同） | 同上，观察项 |
| noticeEntitys | 保留 `com.seeyon.datamigration9000000000000000001.domain.entity.MigrationPlan`（appId 硬编码在类名） | 同应用内等价；为 P1"跨应用复制实体错绑"推断提供字段级证据，仍未实测跨应用 |

## 6. eventDefine 澄清（修正 ROUTE 一处表述）

`eventDefine`（事件定义：抛出事件的参数 schema）与 `events`（绑定动作：事件→规则）是
**两个独立字段**。ROUTE 裁决里"eventDefine 恒为 []"应修正为：
**本轮样本（三页）内恒空；全库 1561 行中 12 行非空**（合同域页面，如
page -79285102570067724「内部结算」等，定义体含 params/nodeType=FORM）。
副本复制时 eventDefine 的重映射行为**未取证**（本轮样本无非空 eventDefine 源页）。

## 7. UNVERIFIED / 未完成（明确列出）

1. **condEvents 完整性**（**已重测，原数字严重高估**）：原文「全库 5865 条带定义体」不成立。
   逐条按 key 形状重分类（全库 condEvents 共 **12551** 条，唯一 id 6301 个）：
   - 仅 `{id}`：**6686** 条
   - `{id, afterAction}`：**5274** 条（只带一个 `afterAction:noOperation` 流程标志，**不是**定义体）
   - 其余带 `afterAction` 但无 `actionType`：5277 条
   - **含 `actionType` 的真内联定义体：582 条**（≈原 5865 的错误来源，疑把"含 afterAction"当成"带定义体"）
   - 本应用 6 个样本页共 26 个 cond id，其中在全库带定义体的 = **0**
   - 全库 `condEvents.id`（6301）与 `events[].id`（3159）**交集 = 0**，
     且 12551 条 condEvents 无一能解析到任何 `events[].id`
   ⇒ 「条件定义体存储在另一处」应标 **推断**（原标"另一处存储未定位"尚可，但依据须换成上面这组数字）。
   复制后条件是否可用仍 **UNVERIFIED**。
2. **跨应用复制**：实体/规则/eventDefine 错绑仍是推断（字段证据见 §5），未实测。
3. **eventDefine 非空页的复制**：需找 eventDefine 非空的源页复制一次（如做，并入后续）。
4. **页面点击侧旁证**：设计器打开副本页读事件面板——**根因已由 auditor 收窄（非通道卡死）**：
   `microflow editor` / `role-permission` 标签 Runtime.evaluate 正常（1+1→2），
   而 `page-manage/functions` child-frame 标签多次 40s TIMEOUT、直连该 URL 返回
   OSS `NoSuchKey`(app-design/index.html)、Page.navigate 与 history.pushState 均无法恢复
   ⇒ **是 page-manage 这一个路由页 JS 主线程挂死，重启浏览器/换通道不对症**。
   入口备忘：`/main/child-frame/udc/app-design/page-manage/functions?appId=…`。
   本轮仍未补页面旁证，P3 建议改从**门户侧**取运行态证据（不经 page-manage child-frame）。
5. P3（运行态可达）按 HANDOFF 边界未动。

## 8. 校验器自查（防假阳性，留给 auditor）

- 三脚本交叉：`p2_final_verify.py`（str 规范化 + DB 直查）、`p2_ref_integrity.py`
  （MySQL 参数化直查，类型强转）、`p2_global_census.py`（str 规范化）——三者结论一致。
- 已知坑：pymysql DictCursor 返回 int id，JSON microFlow 是 str；dict 查找必须先
  `str()` 规范化，否则必产生"规则存在=NO"假阳性（本轮已实际踩到并修复）。
- 结论分级：§0/§2/§3/§4/§5/§6 全部 LIVE（只读 DB 回读，可重跑）；§7 全部 UNVERIFIED，无推断混入。

## 9. 副作用登记

本轮零写操作：未建任何对象、未改任何数据；沿用 P1 留存副本（6054953263042158495、
-6340030840568160268、-389182344634194186 及其 6 个子页面），按 HANDOFF 嘱托全部保留未清理。

## 10. P2 复审补证记录（2026-10-17 23:00，按 VERDICT 定向补，仅 3 处数字/口径 + 2 条时效标注）

VERDICT = **PARTIAL**（`menu-p2-events-migration-review`，auditor commit 7cc2420）。
阻断项是**取证形态**（无页面可见证据），不是结论方向；核心 6 项声明全部被 auditor 独立复现。
本轮补证范围严格限定在 auditor 指出的条目，**未扩范围、未补样本、未再做复制、零写入**。

| # | auditor 指出 | 我的独立复验结果 | 处理 |
|---|---|---|---|
| 1 | 「两副本 16 条 microflow 引用」应为 14 | 副本A 8 事件/7 引用、副本B 8 事件/7 引用 → **7+7=14 成立**，原 16 是事件数与引用数串位 | §2 已改 + 加更正注 |
| 2 | 弹窗页复制源不是 `5175227629061096197` 而是 `992522359796286320` | 实测事件四元组 `9925 == 1185 == -8358` 完全相等；`5175` 4 事件 ≠ `9925` 5 事件 → **成立**；且该 3 页引用基数=0，不贡献正向证据 | §3 已加更正注，明确「不贡献正证据」 |
| 3 | 「condEvents 带定义体 5865」严重高估 | 全库 12551 条按 key 形状重分类：仅`{id}` 6686 / `{id,afterAction}` 5274 / **真内联定义体 582**；本应用 6 页 26 个 cond id **全库 0 个带定义体**；全库 cond id(6301) 与 events id(3159) **交集 0** | §7 已整条重写 |
| 4 | 全库绝对数字需标取证时间戳 | 已确认 22:45 他域写入致 udc_page_schema 1561→1562 漂移 | §4 已标时点 + §10 记录 |
| 5 | 「CDP 通道卡死」原因需改写 | 采纳 auditor 收窄结论（page-manage child-frame 单页 JS 挂死，microflow editor / role-permission 标签正常） | §7.4 已改写 |

**结论方向不变**：`events[].microFlow` 重映射 = 完整。数字更正只动计数，不动判定。

**并发写入登记（非本域，仅记录）**：2026-10-17 22:45 本域授权应用被写入他域对象
`S2GROUP20261017`（udc_portlet -2821989384273517473）、`S2PROBE20261017`
（udc_portlet 5810462779490574369 + udc_page_info -1695224980799982257）。
本应用事件口径仍 97/40/0，未影响本切片。已由 me 与 auditor 双路独立确认并上报 main。

**仍未取证（不因本轮而变）**：页面可见旁证（PARTIAL 的阻断项）、condEvents 定义体位置、
跨应用复制错绑、eventDefine 非空页复制、P3 运行态可达。
