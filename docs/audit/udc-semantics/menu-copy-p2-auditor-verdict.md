# P2 复审裁决｜复制页面事件 microFlow 重映射完整性

> 角色：auditor（单步验证，不改实现、不接管路线）
> 时间：2026-10-17 22:55 (GMT+8)
> 被审对象：implementer RESULT（`docs/audit/udc-semantics/menu-copy-events-migration.md`，commit `d69c4c5`）
> 复审请求：`menu-p2-events-migration-review`（main → auditor）
> 环境：test2 / app `8704025620829192834` / DB `udc_test2`
> 本轮性质：**纯只读**。零建对象、零改数据、零写请求。

## 0. 裁决

**VERDICT = PARTIAL（核心声明全部独立成立；页面侧旁证 UNVERIFIED；3 处数字/语义需更正）**

按 `AUDITOR-CURRENT.md` 判定口径，PASS 要求「独立 LIVE 证据 + DB 回读 + 页面可见」三者一致。
本轮 DB 回读与独立复算**全部一致**，但**页面可见侧旁证未取得**。
→ 依硬规则，不得判 PASS。

**【2026-10-17 23:32 归因更正】阻断项的成因不是「取证能力/通道问题」，是平台授权前置缺失。**

原写法「阻断项是取证形态而非结论方向」**把原因说轻了**。经 main 23:25 实证 + 我 23:30 独立复核
（`auditor/AUDIT-20261017T2330-P3-notlisted-rootcause.md`），真实链条是**两道阻断串联**：

| 序 | 阻断 | 状态 | 性质 |
|---|---|---|---|
| 1 | token 黑名单 → 原生 `alert()` 锁死 renderer | ✅ 已修（清 cookie+续期+dialog handler） | **取证通道**问题，可修 |
| 2 | **应用未上架**（`ctp_role_application` 零行）→ 运行态一律 `server_403` | ❌ **未修，需 HUMAN 授权** | **平台授权前置**，不随取证手段改善而消失 |

→ 关键含义：**即使 token 正常、page-manage 正常、CDP 完全可用，本应用也拿不到运行态页面可见证据。**
所以这条阻断**不可能靠改进取证在 P3 消除**，只能等授权。
P2 的 PARTIAL **判定不变**（事实仍是"无页面可见证据"），但**成因必须记为平台授权前置**，
不能再写成"取证形态"或"通道/页面问题"。

| 声明 | 独立复核 | 裁决 |
|---|---|---|
| ① 三对页 24 事件 / 21 引用 / 100% 命中 / source_id 全==新 page_id / 0 失效 / 0 残留源 id | 完全复现 | ✅ CONFIRMED |
| ② 事件 id 三页逐字相同；4 事件共用 1 规则整体改指同一新 id；反向覆盖 3/3 无孤儿 | 完全复现（严格比对） | ✅ CONFIRMED |
| ③ 源详情页 8 条事件（页面级 1 + 控件级 7，四类）；「样本不足」不成立；未补样本未再复制 | 完全复现 | ✅ CONFIRMED |
| ④ 全库 1561 行 / 6595 事件 / 2327 引用 / 悬空 6（全在他应用）；本应用 97/40/0 | 完全复现 | ✅ CONFIRMED（口径需加注，见 §4） |
| ⑤ schema JSON id/originId 已重映射；eventDefine 非恒空（12 行非空） | 结论复现，分母需精确 | ✅ CONFIRMED（表述需收严） |
| ⑥ 残留 relationGroupId / pageUrl / guid 三处照抄源值 | 完全复现，guid 行为得正面解释 | ✅ CONFIRMED |
| 零写操作 | 时间戳侧证成立 | ✅ CONFIRMED |
| 页面点击侧旁证 | 未取得（我复现了阻断） | ⚠️ UNVERIFIED |

## 1. 独立取证方式（自抓，未复用 implementer 脚本）

- 自写三支只读校验器（`scratch/aud_menu_p2/aud_p2_verify.py`、`aud_p2_verify2.py`、`aud_p2_rows.py`、`aud_p2_diff.py`），
  递归遍历口径独立实现（键名判据 + 路径字符串均自行定义）。
- 抽样**复跑 implementer 原脚本**做一致性核对：`p2_final_verify.py` → 失效引用数 **0**；
  `p2_global_census.py` → 6595 / 2327 / 悬空 6 / 跨页 31 / 本应用 [97,40,0] / 37:2327。
  两路结论一致，`str()` 规范化修正后的脚本可信。
- 逐条明细比对：源 / 副本A / 副本B 三页全部事件按「位置 + id + eventType + actionType + microFlow」四元逐行对照。
- schema 全文 unified diff（`sort_keys` + `indent`）核对除 id/microFlow 外还有哪些字段变动。

## 2. 核心链路逐条实测（LIVE）

三页各 **8 条事件 / 7 条 microFlow 引用**，合计 24 / 21 —— 与声明一致。

| 位置 | eventType | actionType | 源 microFlow | 副本A | 副本B |
|---|---|---|---|---|---|
| `$`（页面级） | onLoad | microflow | 8249313647887011099 | 4043450138967163293 | 7362485689270341281 |
| `input_lHwn` | onChange | microflow | 8249313647887011099 | 4043450138967163293 | 7362485689270341281 |
| `button_EHmQ` | onClick | microflow | 8600546570895050653 | 3215161447089261730 | -1912010165877710289 |
| `input_V7sz` | onChange | microflow | 8249313647887011099 | 4043450138967163293 | 7362485689270341281 |
| `input_9drg_1762917876133` | onChange | microflow | 8249313647887011099 | 4043450138967163293 | 7362485689270341281 |
| `button_wEQ2_1762917876133` | onClick | microflow | 8600546570895050653 | 3215161447089261730 | -1912010165877710289 |
| `udcToolBar_5aM6` | PjcMSm0X0B | widget | （无） | （无） | （无） |
| `udcToolBar_5aM6` | PF8Y9CQ6pa | microflow | 521032638709321259 | 6624846897693439808 | -3739553743323322310 |

- 21/21 引用命中 `udc_microflow_info`；`source_id` 逐条 == 本页 page_id；失效 0、残留源 id 0。
- 事件 id 三页**位置+id+type 严格相等**（Python `==` on list-of-tuples = True/True），串行不改写成立。
- 共用规则：源 `8249313647887011099` 被 4 个事件引用 → 副本内 4 处**全部**改指同一新 id（未拆散）。
- 反向覆盖：三页各 3 条规则，被事件引用 3/3，孤儿 ∅，引用越界 ∅。
- schema 全文 diff：副本 vs 源**仅 18 行差异** = 7 行 microFlow + id + originId。其余 219KB schema 逐字相同。

## 3. 需更正的 3 处（不影响结论方向，但必须改）

### 3.1 §2「副本A / 副本B 全部 16 条 microflow 引用」→ 实为 **14** 条

实测副本A = 7、副本B = 7，合计 **14**。最可能的成因是把"两副本各 8 条事件 = 16"误写成了"16 条引用"
（事件数与引用数混淆，该页 8 条事件中 1 条是 widget 无 microFlow）。
应为 14。**这是文档内数字串位，非取证错误。**

### 3.2 §0「24 条事件、21 条 microflow 引用」正确，但 §3 表的「弹窗页 5 事件」口径需说明来源

副本菜单内「列表弹窗页」两行都是 **5 事件 / 0 引用**，实测成立。
但该页的**复制源不是** `5175227629061096197`（sjypzxxListPage，4 事件，事件 id 完全不同），
而是 `992522359796286320`（sjypzxxListPagecopy，5 事件）。
实测：`9925 == 1185 == -8358` 三者事件四元逐条**完全相等**（`True`/`True`），`5175 != 9925`。
→ 弹窗页复制确实"随迁且不改写"，但**引用基数是 0**，该页对本切片的重映射结论**不提供正证据**（也不构成反例）。
文档未声明这一点，易被读成"三页都验了重映射"。建议在 §3 表加一列「本页是否贡献 microFlow 迁移证据」。

### 3.3 §0/§7 condEvents 判读：**"带定义体 5865"严重高估，实为 582**

全库 12551 条 condEvents 元素，按 key 形状分布：

| 形状 | 条数 | 性质 |
|---|---|---|
| `{id}` | 6686 | 纯引用 |
| `{id, afterAction}` | 5274 | 纯引用 + 一个后置标志位 |
| 含 `actionType` 等字段（内联动作定义） | **582** | 真内联定义体 |

implementer 把"len>1 即算定义体"→ 5865。**5274 条 `{id, afterAction}` 只有一个 `afterAction:"noOperation"` 标志，
不含任何 action 定义**，不能计为定义体。正确口径：**内联定义体 582 条，其余 11969 条为引用型**。
三页那 16 个 condEvent id（ZEvUC3/pDtZut/…）在**全库任何 schema 中都不带定义体**，且
**12551 条 condEvents 无一能解析到任何 `events[].id`** —— 说明 condEvents 不是"引用其它事件"，
而是"内联动作链 或 指向 page_schema 外某存储的引用"。implementer 的"另一处存储"是**推断**，须标 `推断`。

## 4. 全库口径加注（数字对，但 31 条跨页的构成必须写明）

`udc_page_schema` 1561 行中：**65 行 `page_id=0`**（无对应 page_info，`app_id` 为 NULL，共 1058 条事件），
另有 **10 行 `page_schema` 为空串**（JSON 不可解析，已在统计中跳过）。

- 悬空 6 条：全部指向同一个不存在的规则 `-6114638575851512413`，分布在 6 个页面，
  页面归属 app `3289082814923688017`（1 页）+ `6570299241515796755`（5 页）。**"全在他应用"成立。**
- 跨页 31 条：**其中 30 条落在 `page_id=0` 的伪行**上（无 page_info，不是真实页面）；
  **真实非零 page_id 的跨页仅 1 条**（page `-1495076214515139705`，app `3289082814923688017`，
  `source_id` 指向他页）。
→ "本应用或本轮副本 0 失配"**成立且更强**：真实页面维度全库只有 1 条跨页陈旧引用，也不在本应用。
建议 §4 把 31 拆成「30 条 page_id=0 伪行 + 1 条真实页面」，否则 1.59% 失配率会被误读为业务缺陷率。

分母提示：`12/1561` 的 eventDefine 统计中，可解析为 dict 的行实为 **1551**（10 行空串）。
精确表述：**12 非空 / 1551 可解析**，其中 1532 行为 `[]`、7 行缺该键。12 这个数复核无误。

## 5. 声明⑤对 P1 VERDICT 修正 A 的覆盖关系（复审要点 2）

**成立，且覆盖是"部分推翻 + 部分收严"，不是全盘否定。**

| P1 VERDICT 原文 | P2 实测 | 判定 |
|---|---|---|
| §5.1/§9.3 「schema `id`/`originId` 未重映射」 | JSON `id`==`originId`==page_id，3/3 | ❌ **P1 错**，P2 正确。我认此错。 |
| §3/§101 「`eventDefine` 恒为 `[]`」 | 样本内恒空；全库 12 行非空 | ⚠️ **"恒"字过强**，P2 收严正确 |
| §101 「eventDefine 不承载页面事件，implementer 采错字段」 | 12 个非空样本全是**事件抛出参数 schema**（`params`/`nodeType=FORM`），无一条是事件→规则绑定 | ✅ **P1 实质结论仍成立** |

→ 结论：P2 声明⑤**正确覆盖了 P1 的两个事实性错误**，但 P1 "采错字段"的机制结论不受影响，
两者可并存。ROUTE 里"eventDefine 恒为 []"这行应改为"样本内恒空（全库 12/1551 非空，均为事件抛出参数定义）"。

补充（P1 未覆盖、本轮新证）：schema `id`/`originId` 在本应用**并非无条件重映射**——
本应用 31 页中有 2 页 JSON `id != page_id`，但两页均为 **10-14 的既有非复制页**
（`-8121300410989827961` 小爪实验详情958006、`1520098474917276520` 小爪实验页面951440），
**与复制路径无关**，不构成"复制不重映射 id"的反例。判读时必须排除，否则会得出伪结论。

## 6. 页面点击侧旁证：本次仍未取得；根因判定——【2026-10-17 23:20 更正，原判定错误】

> ⚠️ **本节原版（本人在 22:55 写下的结论）是错的，已保留原文于 §6.1 作错误留痕，
> 正确结论见 §6.2。触发更正的证据来自 main 2026-10-17 23:20 亲手定位。**

### 6.1 原判定（错误，留痕不改写历史）

~~implementer §7.4 称"CDP 通道卡死（WS 能连、Runtime.evaluate 全 timeout）"。我复现成功，且定位更精确：
不是"CDP 通道卡死"，是"page-manage child-frame 这一个路由页的 JS 主线程挂死"。
同浏览器其余 UDC 页面 evaluate 完全正常。这个区分决定了后续处置：
重启 Edge / 换通道不对症；应换另一条读取面。~~

原版表格（结论保留，机制解释作废）：

| 标签页 | Runtime.evaluate | 原版解释（错） |
|---|---|---|
| `.../app-design/rule/microflow/editor/-1014...` | ✅ 正常 | "该页没坏" |
| `.../app-design/role-permission?appId=...` | ✅ 正常 | "该页没坏" |
| `.../app-design/page-manage/functions?appId=...`（child-frame） | ❌ `TIMEOUT` | **"单页 JS 主线程挂死"** ← 错 |
| `.../app-design/page-manage/functions?appId=...`（直连） | ✅ 正常但 OSS `NoSuchKey` | "入口错" |

### 6.2 正确根因（main 23:20 实证，我用自己的既有证据复核确认）

**根因是 token 黑名单 → 原生 `alert()` → 模态对话框锁死 renderer 主线程。不是页面 JS 坏。**

- 失效 token 打开运行态/设计器页 → `Page.javascriptDialogOpening`：`alert('token黑名单')` + `alert('身份认证信息无效，请重新登录')`
- alert 是**模态原生对话框，阻塞 renderer 主线程** → `Runtime.evaluate` / `DOM.getDocument` / `Page.captureScreenshot` 全部超时
- 但 `Network.*`（browser 侧）正常、`Runtime.consoleAPICalled` 仍在到达 ← **这才是判别式**
- 清 cookie + 注入当场续期 token + 注册 `Page.handleJavaScriptDialog` 后：`dialogs=0`，门户 / page-manage / 运行态页全部正常渲染

### 6.3 我为什么错了：三处自查（用自己的原始产物反证）

我回头查了本轮遗留的 `scratch/aud_menu_p2/net_capture.json`（当时抓的原始数据），
**判别式的两条证据当时就在我手里，我却读成了相反结论**：

| 我当时的观测 | 我的错误解读 | 正确解读 |
|---|---|---|
| `Runtime.evaluate` 全部超时 | "JS 主线程挂死" | renderer 被模态 alert 阻塞，evaluate 排不进队列 |
| `Network.requestWillBeSent` 收到 **9 条**（含 `pc-user-info` Fetch） | 只当作"通道还活着"的旁证 | 这正是"非通道卡死"的判别式，但我没往 dialog 想 |
| `Runtime.consoleAPICalled` 收到 **2 条**（`createJSsdk`/`createJSSDKfinish`） | 完全忽略 | **Runtime 域能收事件 = JS 引擎在跑 = 不可能是主线程挂死** |

三处具体失误：

1. **我把"evaluate 超时"直接等同于"JS 引擎停止"**。CDP 语义上这两者不同：`consoleAPICalled` 能到达就证明
   引擎在跑；`evaluate` 排不进去只说明有东西挡住了执行入口——模态 dialog 正是这种情况。这是我机制知识的盲区。
2. **`Page.enable` 我调了，但事件循环只 print 了 `Network.*` 和 `Runtime.consoleAPICalled` 两类，
   把 `Page.javascriptDialogOpening` 直接过滤掉了**。证据当时到达我的客户端，是我自己丢弃的。
   核对：`page_probe.py:36` 有 `Page.enable`，而 `:61-65` 的事件分支只认 `Network.requestWillBeSent`
   和 `Runtime.consoleAPICalled` 两种 method，其余全部落空。
3. **我把"4 个标签页里 2 个正常、1 个超时"解释成"这一页特别坏"**，却没去问"这一页和那两页在**凭据状态**上
   有什么不同"——运行态/设计器页要验 token，microflow editor 与 role-permission 那两页可能命中了缓存
   或不触发黑名单校验。差异在凭据，不在页面代码。

### 6.4 影响面（必须一起更正的下游结论）

| 我原结论 | 状态 | 更正 |
|---|---|---|
| "page-manage 单页 JS 主线程挂死" | ❌ 错 | token 黑名单 + 模态 alert 阻塞 renderer |
| "重启 Edge / 换通道不对症" | ❌ 错 | **对症**：清 cookie + 续期 token + 处理 dialog 即恢复；换到干净 profile 也有效 |
| "P3 应改从门户侧取旁证（绕开 page-manage）" | ⚠️ 部分错 | 门户侧也会因同一根因挂死；绕开 page-manage 不是解法，修 token 才是 |
| §10 建议 3「P3 的 CDP 处置按单页挂死修正」 | ❌ 错 | 作废 |

**这条错误对 P2 判定本身没有影响**：P2 判 PARTIAL 的唯一理由是"无页面可见证据"，
这个事实不变；变的只是"为什么取不到"的机制解释。但若不更正，P3 会沿着错误处置走（换通道/换入口），
所以必须显式改。

### 6.5 【23:32 二次更正】还有第二道阻断：应用未上架

上面 6.2 只解了**第一道**阻断（token/dialog）。复核 main 23:25 的实证后，还有**第二道更硬的**：

| 序 | 阻断 | 可修性 |
|---|---|---|
| 1 | token 黑名单 → 原生 alert 锁死 renderer | ✅ 可修（已修：清 cookie + 续期 + dialog handler） |
| 2 | **应用未上架**：`ctp_role_application` 零行 → 运行态一律 `server_403 无权限访问` | ❌ **不可由取证改进解决**，需 HUMAN 授权上架 |

DB 证据（我在 `auditor/AUDIT-20261017T2330-P3-notlisted-rootcause.md` 独立复现）：
- 本应用 `ctp_role_application` = **0 行**（10 个本应用 `ctp_role.id` 在该表零命中）
- 8 个"有沙箱行"的可比较应用中，7 个有 `role_application`，**唯一零行者就是本应用，且实测 403**
- 沙箱侧 `app_state=1 / 1.0.14 / sandbox_version=last`，与可通应用结构一致 → **排除"未部署沙箱"**

⇒ **即使 token 正常、page-manage 正常，本应用也拿不到运行态页面可见证据。**
这就是 P2 的"无页面可见证据"的**真正成因**：不是取证能力问题，是平台授权前置缺失。

⚠️ 注意与我 6.1 原判的区别：原判把阻断归给"页面 JS 挂死"（错）；
6.2 归给"token 黑名单"（对，但不完整）；**6.5 才是最终归因：两道串联，第二道是平台授权。**

其余三个 UNVERIFIED 标记**恰当**：condEvents 定义体（见 §3.3，可再收严）、跨应用错绑（推断）、
eventDefine 非空页复制（现可指名 12 个候选页，如 `-79285102570067724` 内部结算）。

## 7. 零写核验（时间戳侧证）

本应用在 P2 取证窗口（15:48–16:22）之后**无任何新增或更新**：

| 表 | 本应用最大 create_time | 最大 update_time |
|---|---|---|
| udc_page_info | 2026-10-17 15:41:03 | 15:41:03 |
| udc_page_schema | 2026-10-17 15:41:03 | 15:41:03 |
| udc_microflow_info | 2026-10-17 15:41:03 | 15:41:03 |
| udc_function_node | 2026-10-17 15:41:03 | 15:48:32 |

`16:00` 之后创建/更新行数：**0 / 0 / 0 / 0**。零写声明成立。

⚠️ 并发观测（不计入本切片，仅供 main 知悉）：22:45:54 本应用新增页面 `S2PROBE20261017`
（`-1695224980799982257`，schema 857B、0 事件、无 function_node），命名与本域外的 udc-column 域
`S2PROBE-20261017` 工作链一致，应属另一域会话写入。**不影响本切片结论**：
本应用事件口径复核仍为 97/40/0（新页 0 事件）。但**全库行数已由 1561 漂移到 1562**，
任何"全库绝对行数"复跑都会漂移，属基线时效问题，非 implementer 缺陷。

## 8. 复跑指引（供 main / 后续轮次）

```
cd <HERMES_HOME>/cache/scratch/aud_menu_p2
python aud_p2_verify.py     # S1-S6：三页 schema / 事件明细 / 引用完整性 / 共用规则 / 反向覆盖
python aud_p2_verify2.py    # S7-S13：菜单树 / 全库普查 / eventDefine / condEvents / schema diff
python aud_p2_rows.py       # 按行遍历修正版（避免 page_id=0 的 65 行互相覆盖）
python aud_p2_diff.py       # 数字差异定位
```
实现者脚本复跑（一致性核对）：`implementer/p2_final_verify.py`、`implementer/p2_global_census.py`。

**自查留痕（我的错，记录在案）**：首版校验器把 schema 按 `page_id` 做 dict key，
65 行 `page_id=0` 互相覆盖，导致我一度报出「全库 5562 事件 / 跨页 1 条 / condEvents 4331」三处偏差。
改为**按行遍历（不去重）**后全部对齐 implementer 数字。implementer 用 `JOIN` 逐行遍历，无此缺陷。

## 9. 副作用登记

- 建对象：**0**
- 改数据：**0**
- 写请求：**0**（CDP 仅 navigate + evaluate 只读表达式，未触发保存）
- 新增标签页：1 个 `about:blank`（已由后续 navigate 使用，可随时关闭）
- 本地未提交改动：无（本文档为本轮唯一产物）

## 10. 给 main 的建议（仅建议，不接管路线）

1. **P2 结论可采信**：事件随迁 + microFlow 重映射完整，机制级成立（21/21 + 全库 2327 口径支撑）。
   ~~若 main 接受"页面侧旁证转 P3 一并补"，可把本切片判 PASS；但请在 ROUTE 明示"PASS 无页面可见证据"。~~
   **【23:32 更正】此建议作废。** 页面侧旁证**不是"转 P3 补"就能补的**——它被平台授权前置阻断
   （应用未上架，见 §6.5），在授权到位前**永远补不到**。建议改为：
   「P2 机制级 CONFIRMED；页面侧旁证受平台授权前置阻断（非本域缺陷），
   待上架授权后在 P3 复验；在此之前 P2 不得判 FULL PASS」。
2. **要求 implementer 改 3 处数字**再收口：§2 16→14、§3 加"弹窗页 0 引用不贡献正证据"、
   §3.3/§7 condEvents 定义体 5865→582（并标"另一处存储"为推断）。
3. ~~**P3 的 CDP 处置方案需按 §6 修正**：不是通道卡死，是 page-manage child-frame 单页挂死。
   重启浏览器不对症；建议 P3 改从门户侧（非设计器 page-manage）取运行态旁证。~~
   **【23:20 更正】本条作废。** 真根因是 token 黑名单触发原生 alert 锁死 renderer 主线程（§6.2）；
   正确处置是清 cookie + 续期 token + 注册 `Page.handleJavaScriptDialog`，不是绕开页面。
4. 全库绝对数字建议标注取证时间戳，避免 1561/1562 漂移被当作矛盾。
