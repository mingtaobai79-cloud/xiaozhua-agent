---
name: xiaozhua-weekly-plan
description: Fill 周工作计划 weekly plan form on xt.seeyon.com.
version: 4.0.0
author: 小爪
license: MIT
metadata:
  hermes:
    tags: [xiaozhua, weekly-plan, cdp]
    related_skills: [xiaozhua-manhours]
---

# 周工作计划

## 一键填表

```bash
<HERMES_HOME>/hermes-agent/venv/Scripts/python.exe scripts/fill.py
```

19 项全字段对账，页签保持打开不提交。`--dry` 只回读不写。

## 脚本结构（2026-10-20 抽取公用）

```
07-office-collaboration/
  config.yaml                两个 skill 共用配置（业务值全在这里）
  _common/cap4.py            ★ 公用驱动（周计划 / 工时登记 / 补录 共用）
  _common/conf.py            ★ 配置加载器（读 config.yaml、必填校验）
  xiaozhua-weekly-plan/scripts/fill.py      周计划业务层
  xiaozhua-manhours/scripts/fill.py         工时业务层
```

## 配置驱动（改配置，不改代码）

`fill.py` 启动时读 `config.yaml`，缺必填项直接抛 `ConfigError` 退出，
**故意不兜底**——兜底会导致「改了配置没生效，还以为在测新配置」。

改周计划内容只动 `config.yaml` 的 `weekly_plan` 段：

```yaml
weekly_plan:
  plan_sequence: 通用维度        # 必须先选，否则一级维度下拉是空的
  main_receivers: [武超智, 许勇峰]
  cc_mode: department_all
  row_defaults: {dim1: 职能业务, dim2: 项目实施, owner: operator-a, collab: "", checker: 武超智}
  summary: "上周：…"
  plans:                         # 每行要事；w 合计必须 = 100
    - {w: 30, name: ..., deliver: ..., imp: 重要不紧急, start: 2026-10-19, end: 2026-10-23}
  goals:
    - {dim: 客开交付, item: ..., unit: 个, val: "1"}
  columns: {dim1: 1, ..., checker: 11}          # 列索引
  main_fields: {main_receiver: field0326, cc: field0327, summary: field0226}
```

`_common/cap4.py` 分两层，**只放跨业务复用的东西，不放字段映射**：

| 层 | 内容 |
|---|---|
| 平台层 | `Sess`（CDP 会话/鼠标/键盘/js）、`list_pages`/`new_tab`/`close_tab`/`xiaozhua_port`、`open_template`、`check_login`、`dismiss_restore_dialog`、`clear_overlays`、`blur` |
| cap4 层 | `Cap4Table`（子表读写/加行/下拉/复选框）、`field_text`/`field_xy`/`write_field`（主表字段）、`pick_people`（人员选择器）、`open_field_people_js`/`open_cell_people_js` |

业务字段 id（field0037 / ci11 这些）留在各 skill 自己的 `fill.py`。

CLI 排查：`python _common/cap4.py list` / `check 9222` / `tables 9222 <tabid>`

## ⚠️ 填写顺序有硬依赖（踩过的坑）

```
0. 计划要事「周计划序列」选「通用维度」   ← 必须最先！
1. 上周期总结
2. 主送（武超智+许勇峰）／抄送（部门全选）
3. 关键目标（2 条）
4. 计划表（4 条，权重 100）
```

**不先选周计划序列，计划表「一级维度」下拉展开是空的**（实测 0 个选项）。
选成「通用维度」后才会出现 职能业务/重点专项/体系建设/团队管理/规划管理/协作与协调/业务创新/学习提高 8 项。

## 该填什么（2026-10-20 用户确认）

| 字段 | 值 | 说明 |
|---|---|---|
| 周计划序列 | 通用维度 | 前置依赖 |
| 一级维度 | 职能业务 | 树形下拉，见下 |
| 二级维度 | 项目实施 | 真键盘写 |
| 责任人 | operator-a | ci9 |
| **协作人** | **留空** | **ci10。要么等于责任人要么留空，不要写别人** |
| **检查人** | **武超智** | **ci11** |
| 主送 | 武超智 + 许勇峰 | 两人，不是一人 |
| 抄送 | 部门全选（约 22 人） | |
| 协作内容表（我的周协作） | **不填** | 别人推过来的协作任务 |

⚠️ 这三列**曾经全部填错**：检查人写成了operator-a、协作人写成了武超智（两头对调）。
ci9=责任人 / ci10=协作人 / ci11=检查人，别搞反。

## 关键控件坑（全部实测）

**控件类型速查：见 `references/cap4-control-dispatch.md`** ——
列名 → 真实控件类型 → 该调哪个方法的对照表，含「同名不同型」、行索引偏移、
数据行判定、主表字段容器两种 class。**填表前先查它，别凭列名猜。**

**点击无效时：见 `references/cdp-interaction-debugging.md`** ——
「点了没反应」按 cost 从低到高 6 步排查（`elementFromPoint` 双层对照 → 遮罩 →
坐标过期 → 可见性 → iframe 重绘 → 占位符改坏 JS）。**同一现象失败两次就升到这一步定位，
不要继续轮着换点击姿势。**

**0. 对账必须逐列，不能只查"自己刚写过的那几列"**
`check_plan_rows()` 是纯函数单测入口（不碰浏览器）。曾经对账只覆盖了主动写的几列，
**重要程度整列空着照样报 0 FAIL**，用户当场在截图上指出来。
判据总表与反向验证要求见「完成标准 → 对账铁律」。

**1. 一级维度是树形下拉，点单元格中心没用**
必须点 `.cap-icon-shu-zhankai` 图标才展开：
```python
await s.pick_select(1, "职能业务", table_key="plan", row=n,
                    click_icon="cap-icon-shu-zhankai")
```
普通下拉（重要程度 ci6）点中心即可，不要传 click_icon。

**2. 遮罩残留 → 后面全部写空（有两类，漏一类就全废）**

| 遮罩 | 来源 | 处理 |
|---|---|---|
| `.selectorg-shade`（z-index 1041） | 人员选择器点「确定」后 `.selectorg` 没了、这层还挂着 | 点它一下即关；`pick_people` 返回前已等两者归零 |
| **`.mask.mask_msg`（opacity 0.45，z-index 1052）** | 消息提示层卡住不消失，覆盖全屏 | **点不掉**，只能 `display:none` + `pointer-events:none` |

`.mask` 这层最阴——它不报错、不弹窗，只是让**所有** `Input.dispatchMouseEvent` 打在它身上。
表现为「点了没反应」，会让人以为是选择器/坐标/时序问题，然后一路试错几十次。
`clear_overlays()` 现在两类都查、都清（`.mask` 直接停用），每次写值前调用。

**2b. 点击反复没反应，先查 `elementFromPoint`，别再换点击姿势**

坐标算错、元素没渲染、被遮罩挡住，三种情况表象完全一样。先花一步定位：

```js
// 顶层：谁真正接住了这一击
document.elementFromPoint(x, y)          // 期望 IFRAME，若是 DIV.mask… 就是遮罩
// iframe 内：扣掉 frame 偏移再查一次
d.elementFromPoint(x - fb.left, y - fb.top)   // 期望目标控件；能命中说明坐标没问题
```

**两侧对照就能一次分清**：`topHit` 是遮罩、`inHit` 是目标控件 → 纯粹是遮罩问题；
两边都命中不到 → 坐标/滚动问题。先分清再动手，比逐个试点击方式快一个数量级。

**3. 三张子表的「新建」按钮文字完全相同**
不能按 y 分区（滚动后失效，且协作内容表压在同一条线上）。
判据：向上找最近的「含 ≥2 行 table」的祖先，读表头 ——
关键目标含「是否专项」，计划表含「一级维度」。

**4. 重要程度选项是四选一**：`重要紧急 / 重要不紧急 / 不重要紧急 / 不重要不紧急`
写「重要且紧急」会 `option not found`。

**5. 计划序列 / 关键目标序号 是只读字段**，系统自动生成，不要尝试写。

**6. `write_cell` 的 JS 注入：占位符名不能出现在 JS 源码里**
把 Python 值拼进 JS 一律用专用占位符（`COND`/`ROW`/`CI`/`ICON`）再 `.replace()`，
**不要用有语义的名字**。踩两次：
- 用 `.replace("table_key", table_key)` → 把 JS 里的 `table_key:` 字段名一起替掉：
  `SyntaxError: Unexpected string`
- 用占位符 `IFR` 时，`.replace("IFR", ...)` 会把 `iframe[src*="cap4"]` 里的字符也扫到，
  拼出来的 JS 静默变形
规矩：占位符取名先在一份 JS 里 grep 一遍，确认原 JS 里不存在该子串；
或用 `str.format` 风格的具名占位 `{COND}` 避开子串误伤。

**7. `field_text` / `field_xy` 不能死抠 `cap-field-content`**
主表字段容器有两种形态：
- 人员/文本域（主送 field0326、上周期总结 field0226）：`cap-field-content cap-field formson_xxx_field0326`
- 日期/工号类（工时日期 field0022、登记日期 field0009）：`cap4-formmain__td default-field-style cap-field formmain_77793|field0022`

死抠 `cap-field-content` 会让日期类字段全部报 `no holder`。判据用
`[class*="fieldXXXX"]` + 含 `cap-field`。

## 配置文件

**所有固定值在同级目录 `../config.yaml`**（与 `xiaozhua-manhours` 共用）：

```yaml
seeyon.base_url
weekly_plan.template_url        # 完整 URL（优先）；也可只给 template_id
weekly_plan.plan_sequence       # 「周计划序列」，必须先选
weekly_plan.main_receivers      # 主送（列表）
weekly_plan.cc_mode             # 抄送（department_all = 全选本部门）
weekly_plan.row_defaults        # dim1/dim2/owner/collab/checker
weekly_plan.summary             # 上周期总结正文
weekly_plan.plans               # 计划表每行：{w,name,deliver,imp,start,end}
weekly_plan.goals               # 关键目标：{dim,item,unit,val}
weekly_plan.columns / main_fields  # 列索引 / fieldNNNN
portal.home / summary_url       # 读工时记录
```

正文里出现的人名只是示例，**实际一律以 config 为准**。

**硬编码纪律：结构留代码，数据进配置。** field id、列索引、填写顺序属结构；
模板 id、人名、日期、要事条目、总结正文属数据。用户明确要求过：
脚本里出现不该硬编码的业务值就是缺陷。

## 环境前提

- Chrome/Edge 已开 `--remote-debugging-port=9222`，且已登录 xt.seeyon.com
- 用 Hermes venv 的 python：`<HERMES_HOME>\hermes-agent\venv\Scripts\python.exe`，需要 `websockets`
- 通过 CDP `Target.attachToTarget` + `Runtime.evaluate` 执行 JS，鼠标用 `Input.dispatchMouseEvent`
- 表单内容在 cap4 iframe：`document.querySelector('iframe[src*="cap4"]').contentDocument`
- **业务层是 `scripts/fill.py`，平台层一律从 `../_common/cap4.py` import。不要另写一套。**
  旧版 `cdp.py` / `regress.py` 已废弃（改名为 `*_old.py.bak`），里面的 API 不再维护。

```bash
P=<HERMES_HOME>/hermes-agent/venv/Scripts/python.exe
D=<HERMES_HOME>/skills/seeyon/07-office-collaboration

$P $D/xiaozhua-weekly-plan/scripts/fill.py            # 填整张表 + 19 项对账
$P $D/xiaozhua-weekly-plan/scripts/fill.py --dry      # 只回读现状不写
$P $D/_common/cap4.py list                          # 扫 9222/9223/9226/9229 所有页签
$P $D/_common/cap4.py check 9222                    # 判定登录态
$P $D/_common/cap4.py tables 9222 <tabid>           # 列出当前页所有表的表头
```

`scripts/fill.py` 退出码 0 = 全 PASS，1 = 有 FAIL。**它是唯一的验收闸门** ——
不要用「我挑的几个单点操作都成功」来代替整表对账（真踩过：单点全绿但表单大半是空的）。

模块用法：

```python
from cap4 import open_template, open_field_people_js, open_cell_people_js

t = Cap4Table(s, ["一级维度", "检查人"], name="plan")
await t.pick_select(1, "职能业务", row=n, click_icon="cap-icon-shu-zhankai")
await t.write_cell(2, "二级维度值", row=n)
await t.write_cell(3, "40", row=n)
await s.blur()
await t.pick_people(open_cell_people_js(9), names=["武超智"])           # 责任人 radio
await s.pick_people(open_field_people_js("field0326"), names=["武超智"])  # 主送
await s.pick_people(open_field_people_js("field0327"),
                    switch_tab="部门", select_all_in_dept=True)         # 抄送全选
```

### 步骤 0：先验登录态，再碰表单

**没登录就开表单页，会得到「cap4 iframe 里等不到『权重』，轮询 40 秒超时」这种误导性现象。** 先花 10 秒判定：

1. `curl -s http://127.0.0.1:<port>/json/list` 扫 **9222 / 9223 / 9226 / 9229**——本机常同时跑多个调试实例，其中一个可能仍带着有效会话。挑 URL 已在 `xt.seeyon.com/seeyon/main.do` 的那个 attach，不要新开一个干净 profile 就认定没登录。
2. `Runtime.evaluate` 读 `location.href` + `document.body.innerText` 前 300 字。**通过的唯一判据是落地到了工作台**（`method=main` 且正文有工作台内容）。以下任一均属**未登录**：落地在 `method=index`；正文含「请输入验证码」「账号被锁定」「该账号未开启短信登录」。
3. `document.cookie.length > 0` **不是**登录证据——登录墙页本身也带 `route` / `SY_ACCESS_TOKEN` 等 cookie。同理，`Network.setCookie` 注入旧 cookie 会 `success: true` 但仍然落回登录页（token 的 `exp` 已过）。判定只看第 2 条的落地页面。
4. 未登录就停手，把「请在 <port> 那个窗口里登录 xt.seeyon.com，登完我再继续」明确告诉用户。**不要自己提交登录、不要自己去拿/刷新 token**（见 chrome-profiles 的凭据安全条），也不要拿 test2 的共享凭据去套 xt.seeyon.com——那是另一个域的账号。

## 通用工具

**⚠️ 不要用 `setV` 直接改 value（本机实测 2026-10-20 证伪）。**
`Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set` + dispatchEvent
在 cap4 的 Vue 组件上**只会改 DOM，不进表单状态**：读回看着有值，但「权重合计」仍是 0%，
提交时这些值会丢。唯一可靠路径是**真实鼠标点进单元格 + `Input.insertText` 真键盘输入**。

```js
// 1) 算目标元素在【顶层视口】的坐标（iframe 内坐标必须加 frameElement 偏移）
const d = document.querySelector('iframe[src*="cap4"]').contentDocument;
const fr = d.defaultView.frameElement.getBoundingClientRect();
el.scrollIntoView({block:'center'});
const r = el.getBoundingClientRect();
const x = Math.round(fr.left + r.left + r.width/2);
const y = Math.round(fr.top  + r.top  + r.height/2);
```

```python
# 2) 真实点击 + 真键盘输入
for t in ("mousePressed", "mouseReleased"):
    await s.call("Input.dispatchMouseEvent",
                 {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
await s.call("Input.insertText", {"text": "要写的值"})
```

要覆盖已有值：Ctrl+A（`modifiers: 2` 的 keyDown/keyUp）→ `Input.insertText`，
或直接 Delete 键清空。**清空也必须走真实键盘**，否则同样不进状态。

**必须失焦才提交值。** 填完点空白处（iframe 内任意坐标，例如 frame 左上 +700,+60）再回读；
不失焦时 number 字段的合计不会重算，会以为没写进去。

页面必须轮询等就绪，固定 sleep 会踩空。**判据不能用 `/权重/`**——表头在表单没加载完时
也可能命中；实测更稳的是等**计划表数据行出现**：

```js
for (let i = 0; i < 45; i++) {
  const d = document.querySelector('iframe[src*="cap4"]')?.contentDocument;
  if (d?.body) {
    const plan = [...d.querySelectorAll('table')].find(t => /一级维度/.test(t.innerText) && /检查人/.test(t.innerText));
    if (plan && plan.querySelectorAll('tr').length >= 2) break;
  }
  await new Promise(r => setTimeout(r, 1000));
}
```

另注：`Page.navigate` / `Page.enable` 在这个页面会**挂住不返回**（cap4 表单页阻塞），
永远用 `PUT /json/new?<url>` 开新页签，只用 `Runtime.evaluate` 读页面。

## 表单字段定位

**重要：`fieldNNNN` 是 class 名，不是 element id。** 用 `getElementById('field0101')` 一类写法
全线拿不到元素（实测 19 个“字段 ID”里 17 个 MISSING，2 个只有 `field0087_<子表id>` 前缀形式）。
正确姿势是按 class 定位：

```js
// 主表（非子表）字段：.cap-field-content.cap-field.<fieldNNNN>
const f = (name) => d.querySelector('.cap-field-content.' + name);

// 子表字段：class 里带 formson_<表单id>_<记录id>_，用 [class*=""] 匹配最稳
const sf = (name) => d.querySelector('[class*="_' + name + '"]');
```

### 主表字段（无前缀，直接 `[class*="fieldXXXX"]`）

| 区域 | 字段 | 定位 | 控件 |
|---|---|---|---|
| 周期起/止 | field0053 / field0054 | `[class*="field0053"] input` | date，只读展示，勿手改 |
| 上周总结 | field0226 | `[class*="field0226"] textarea`（placeholder=`上周工作总结`） | textarea，**真键盘写** |
| 部门上周总结 | field0305 | `[class*="field0305"]` | 按钮，点了自动汇总 |
| 主送 | field0326 | `[class*="field0326"] .cap-icon-xuanduoren` | 人员选择器 |
| 抄送 | field0327 | `[class*="field0327"] .cap-icon-xuanduoren` | 人员选择器 |
| 上月/本月甘特图 | field0275 / field0274 | `[class*="field0275"]` | 按钮 |

### 计划表（子表 formson_73882）——按**单元格列序**取，不要按字段名

计划表定位（实测最稳，两个表都有 `权重` 字样，只认 `一级维度` + `检查人`）：

```js
const plan = [...d.querySelectorAll('table')]
  .find(t => /一级维度/.test(t.innerText) && /检查人/.test(t.innerText));
const rows = [...plan.querySelectorAll('tr')];   // rows[0]=表头  rows[1]=数据行
const cells = [...rows[1].querySelectorAll('td')];
```

单元格列序（实测 12 列）：

| ci | 列 | 控件 | 怎么写 |
|---|---|---|---|
| 0 | 序号 | 自动 | 不碰 |
| 1 | 一级维度 | `.cap4-select` | 选择器，点开选 |
| 2 | 二级维度 | `.cap4-text` → `input` | 真键盘 |
| 3 | 权重(%) | `.cap4-number` → `input` | 真键盘，十进制 |
| 4 | 本周专项/要事 | `.cap4-textarea` → `textarea` | 真键盘 |
| 5 | 交付物 | `.cap4-text` → `input` | 真键盘 |
| 6 | 重要程度 | `.cap4-select` | 选择器 |
| 7 | 计划开始日期 | `.cap4-date` → `input[id^="field0087_"]` | 默认带本周，一般不改 |
| 8 | 计划完成日期 | `.cap4-date` → `input[id^="field0090_"]` | 默认带本周五，一般不改 |
| 9 | 责任人 | `.cap4-choose-people` → `.cap-icon-xuanren` | 人员选择器 |
| 10 | 协作人 | `.cap4-choose-people` → `.cap-icon-xuanduoren` | 人员选择器，可留空 |
| 11 | 检查人 | `.cap4-choose-people` → `.cap-icon-xuanduoren` | 人员选择器 |

表尾第三行（cells<12、内容是 `0%`）是**权重合计行**，靠 `rows[rows.length-1]` 取。

### 关键目标（子表 formson_73884）

同为 6 列，但**列序和控件与计划表不同，别照搬**：

| ci | 列 | 控件 | 怎么写 |
|---|---|---|---|
| 0 | 序号 | 自动 | 不碰 |
| 1 | 维度 | `.cap4-text` → `input` | 真键盘 |
| 2 | 目标项 | `.cap4-text` → `input` | 真键盘 |
| 3 | 单位 | `.cap4-text` → `input` | 真键盘 |
| 4 | 目标值 | `.cap4-text` → `input` | 真键盘 |
| 5 | 是否专项 | **`.cap4-checkbox`（复选框！）** | **不是下拉**，点 `.ui-checkbox__inner` |

**坑：`是否专项` 是 checkbox，不是 select。** 用 `pick_select()` 会返回
`option not found`（选项列表为空）。正确做法：

```python
# 幂等：设成目标状态，不是"翻转"
await s.toggle_checkbox(5, table_key="goal", want=True)
```

**注意（实测不稳定）**：点 `.ui-checkbox__inner` 有时点不中（页面滚动导致坐标失效），
`toggle_checkbox` 内部已做 4 次重试 + 每次重新 scrollIntoView + 幂等校验。
即便如此，在长流程（前面做过多次人员选择器弹窗）后仍有约 20% 概率失败。
**遇到 `ok: false` 就单独再调一次**，不要当成功能不可用。

**不要用 JS `.click()`**：在 `.ui-checkbox` label 上 `click()` 会把已勾的取消、
未勾的仍然不勾，行为与真实鼠标相反（实测）。

**加行：** 调 `Cap4Table.add_row()`，它自己找对工具栏，不要自己算坐标。

**别按 y 坐标区分工具栏。** 旧文档写「关键目标 y≈504、计划表 y≈720」，这套在**页面滚动后全部失效**，
而且三张子表（关键目标 / 计划表 / 协作内容）的「新建/复制/删除」按钮文字完全重复，
协作内容表又压在同一条 y 线上。可靠判据是**读按钮所包含的那张表的表头**：
向上找最近的「含 ≥2 行 table」的祖先，读它的 `tr` 文字 ——
关键目标表头含「是否专项」，计划表含「一级维度」。`add_row()` 已封装这个逻辑。

### 工具栏按钮

`.cap-icon-jiahao` 在页面上有 **7 个**，不能盲点。按文字定位 `.formson-list__button.cap-btn`：

| 按钮 | 用途 |
|---|---|
| 新建 / 复制 / 删除 / 删除全部 | 增删行 |
| 选择未完成目标 / 录入本周目标 | 关键目标批量 |
| 选择计划维度 / 选择未完成 / 录入本周计划 | 计划表批量 |
| 总结上周工作 | 自动汇总 |

**定位靠表头，不靠 y 坐标**（见上一节）。计划表与关键目标的按钮文字完全重复，
`closest('.formson-toolbar-container')` 也不够区分协作内容表，因为三张表共用同样的容器结构。

## 流程

1. **加行**：调 `Cap4Table.add_row()`（内部按表头定位工具栏，不靠 y 坐标）。
   不要盲点 `.cap-icon-jiahao`（全页 7 个）。
2. **文本类一律真键盘写**：上周总结、二级维度、权重、要事描述、交付物、关键目标 1~4 列。
   点单元格中心 → `Input.insertText`。**不要用 setV**（不进表单状态，见上）。
3. **选择器字段**（一级维度 / 重要程度 / 日期）：
   - 真实鼠标点单元格中心，进 `is-edit`
   - JS 找**最近的、可见的、文字匹配**的 `.cap4-select__option`，距离 = `|r.left-cr.left| + |r.top-cr.bottom|`
   - `option.click()`，然后回读 `cell.querySelector('input').value`
   - 坑：选项会残留在 DOM 且坐标常在视口外（y>1000），必须过滤可见性 + 取最近
   - 日期列（ci 7/8）默认已带本周起止，**不加行就不用改**
4. 人员选择器走「人员选择器通用流程」
5. **每填完一段就失焦**（点 frame 内空白处），再回读；不失焦合计不重算
6. 权重合计由系统自算，校验是否 100

## 内容来源

**不写死任何外部文档链接。**

### 上周总结 = 上周工时记录

1. 打开 `portal.home`
2. 找标题含「顾问工时登记」且日期在上周的记录，取 affairId
3. 打开 `portal.summary_url`，替换 affairId
4. 读工时明细：工时日期 / 工时类型 / 项目名称 / 客户名称 / 工作内容 / 消耗工时
5. 按日期排序归纳成总结（合并同类项，不逐字抄）

### 本周计划 = 上周未完成 + 本周新内容

1. 上周未完成项（标「【续】」或未闭环的）
2. operator-a提供的新内容

条数按实际定，权重按重要性分配，**合计必须 100**。

### 行默认值

从 `weekly_plan.row_defaults` 读：一级维度、二级维度、责任人、检查人。
重要程度按条目实际紧急度分配，不要全填同一个值。

## 人员选择器通用流程（2026-10-20 全链实测）

**直接用 `s.pick_people(opener, ...)`，别手搓。** 下面是它内部做的事，理解原因再改。

责任人 / 检查人 / 主送 / 抄送都走这套：

1. **打开弹窗：用 JS `ic.click()`，不要算坐标真实点击。**
   实测：cap4 表单 iframe 本身就覆盖在那个坐标上，`Input.dispatchMouseEvent`
   打到的是 IFRAME 元素而非里面的图标——第一次可能碰巧成功，第二次必失效。
   `ic.click()` 每次都成功，是本页面上唯一可靠的"点图标"方式。
2. 弹窗是顶层 `.selectorg`，内部嵌 `iframe(src=selectpeople.do)`。
3. **光是 `.selectorg` 出现还不够**：里面的 iframe 异步加载，必须等它出现
   `input[placeholder="请输入人员名称"]` 才算可用。不等就报 "no name input"（第一次打开最容易踩）。
4. **连续开多个选择器时，必须先等上一个 `.selectorg` 完全消失**（count==0）。
   不等会拿到上一个已卸载的 iframe。
5. **切「最近」tab** 做全局检索；`部门` tab 只在选"全选本部门"时用。
6. 姓名用**真键盘**输入（`Input.insertText`），不要 setV。
7. **点放大镜要挑可见的那个**：页面有 2 个 `.anticon-search`，其中一个是
   `w=0,h=0` 的隐藏元素，点它不触发检索，会得到未过滤的 29 人全部门列表。
8. 勾选结果项：责任人 / 主送是**单选 radio**（`.ant-radio-inner`），
   主送明细 / 抄送是**多选 checkbox**（`.ant-checkbox-inner`）。两种都要兼容，别写死 checkbox。
9. 点确定：**必须点 `.button.emphasize`（65×28）**，不是外层那个 840px 宽的
   `.selectorg-btn` 容器——点容器无效，弹窗不关。

**全选本部门**（抄送用）：切到「部门」tab → 点 `.sroll-list-head` 里的
`.ant-checkbox-inner`。实测勾到 23~25 人（计数含组织节点，人数以写入后的姓名串为准）。
**注意：重复点这个表头会来回切换全选/取消**，想清空要确认当前 `ant-checkbox-checked` 状态再操作。

坐标换算（文本/选择器类仍需要）：iframe 内元素 `getBoundingClientRect()` 加
`iframe 自身` + `frameElement` 的偏移。**人员图标走 JS click，不需要坐标。**

**验证**：写完必须**失焦**再回读（点 frame 内空白处），且要先盯一个**依赖字段**
（权重合计 / 主送人数）有没有动。只回读自己刚写的输入框不算验证——DOM 改了而表单状态没改时，
回读一样有值。

## 完成标准

先跑 `scripts/fill.py`，必须 `RESULT: 0 FAIL` 才算完成。下面是对账覆盖的项，
**每一列都要查，不能只查自己刚写过的那几列**（教训见下面「对账铁律」）：

- 计划条数 ≥ 期望条数
- **重要程度：逐行非空 + 是四个合法值之一 + 等于期望值**
- 责任人 = operator-a（逐行）
- 协作人 = 空（逐行）
- 检查人 = 武超智（逐行）
- 二级维度 / 要事描述 / 交付物 / 起止日期：逐行非空
- 一级维度 = 职能业务（逐行）
- 权重合计 = 100%
- 主送两人、抄送人数、周计划序列、上周期总结

**提交前交operator-a确认，不自动提交。**

### 对账铁律（本次最贵的一条）

**对账只覆盖“自己主动写的那几列”，等于没对账。**
实测：重要程度整列有一行空着，脚本照样报 `0 FAIL` —— 因为写对账时只检查了确实写过的列。
用户当场在截图上指出来。

规矩：**写对账时先列全部列，再逐列给判据**，不能从“我写了什么”反推。
空着也是错误，和写错一样严重。

**改完对账必须反向验证。** 找一个**已知有问题的旧数据**（比如历史失败页签的真实行值）
喂给对账函数，确认它真能报 FAIL。
只会 PASS 的检查不是检查。纯对账逻辑要抽成不碰浏览器的纯函数（`check_plan_rows(prows)`），
才能这么单测。

## 已验证 / 未验证

### 2026-10-20 全链路实测（CDP 9222，登录态 operator-a，连续 2 次可重复）

`scripts/fill.py` 一次跑完，退出码 0，19/19 PASS（对账已并入 fill.py，不再单列 regress.py）：

| 项 | 结果 |
|---|---|
| 开模板 + 自动处理「是否恢复」弹窗 + 等就绪 | PASS |
| 一级维度选择器（8 选项，选「交付工作」） | PASS |
| 真键盘写 ci2/ci3/ci4/ci5 → 失焦 → 权重合计 0%→40% | PASS |
| 责任人 ci9（**单选 radio**）选「武超智」 | PASS |
| 主送 field0326（**多选 checkbox**）选「武超智」 | PASS |
| 抄送 field0327 部门「全选」→ 写入 23~25 人 | PASS |

### 本次实测证伪并已修正的错误（原文档写法）

1. `setV` 直接改 value + dispatchEvent **只改 DOM，不进 Vue 表单状态**。
   读回有值、权重合计仍 0%、提交必丢 → 已全部改为真键盘路径。
2. `getElementById('field0101')` 等 19 个"字段 ID" **全部拿不到元素**——
   `fieldNNNN` 是 class 不是 id → 已改为 class / 列序定位。
3. `.cap-icon-jiahao` 全页 7 个，不能盲点 → 改为按「向上找最近含 ≥2 行 table 的祖先，读表头」定位工具栏（**不是按 y 分区，滚动后失效**）。
4. 就绪判据 `/权重/` 会误命中表头 → 改为等计划表数据行。
5. `PUT /json/new?<url>` 不编码 → `&` 被吃、templateId 截断、开出空白页 → 必须整串 quote。
6. 人员图标算坐标真实点击 → 打到 iframe 本身，第二次必失效 → 改用 `ic.click()`。
7. 只看 `.selectorg` 出现就动手 → 内部 iframe 未加载完，报 "no name input" → 要等名叫输入框出现。
8. 连续开选择器不等旧弹窗销毁 → 拿到已卸载 iframe → 要等 count==0。
9. 有 2 个 `.anticon-search`，点隐藏的（w=0）不触发检索 → 必须过滤可见性。
10. 点 `.selectorg-btn` 容器无效 → 必须点里面的 `.button.emphasize`。

### 已验证（`scripts/fill.py` 全链路，`RESULT: 0 FAIL`）

19 项全 PASS：周计划序列 / 上周期总结 / 主送两人 / 抄送部门全选 / 关键目标 2 条 /
计划表 4 条 / 重要程度全填且等于期望 / 责任人=operator-a / 协作人为空 / 检查人=武超智 /
文本列全填 / 一级维度=职能业务 / 权重合计=100%。

关键目标表（formson_73884）写入、重要程度 ci6 选择器、加行、树形一级维度
（需点 `cap-icon-shu-zhankai`）均已跑通 —— 旧版曾把这些列为“未验证”。

### 仍未验证

- 计划开始/完成日期（ci7/ci8）手工改期（默认带本周，一直没改过）
- 「总结上周工作」按钮自动汇总、甘特图按钮
