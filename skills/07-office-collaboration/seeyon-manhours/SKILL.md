---
name: seeyon-manhours
description: Fill 致远 顾问工时登记/补录 forms, and read past records.
version: 3.0.0
author: 小爪
license: MIT
metadata:
  hermes:
    tags: [seeyon, manhours, timesheet, cdp]
    related_skills: [seeyon-weekly-plan]
---

# 致远 顾问工时登记 / 补录

## 一键填表

```bash
cd seeyon-manhours/scripts
python fill.py reg                # 登记（当天）
python fill.py back 2026-10-15    # 补录到指定日期
python fill.py --dry <tabid>      # 只回读现状
```

登记 12/12、补录 13/13、周计划 19/19，全字段对账通过，页签保持打开不提交。

**回归命令（三个都要跑一遍再交付）**：
```bash
python fill.py reg                                    # 工时登记
python fill.py back 2026-10-17                        # 补录
cd ../../seeyon-weekly-plan/scripts && python fill.py  # 周计划
```

**公用驱动来自 `../_common/cap4.py`**（与周计划同一套，已抽取）。
**配置来自 `../_common/conf.py` + `../config.yaml`**。
字段映射在本文件下方的「表单字段」节；代码里的是 `seeyon-manhours/scripts/fill.py`。

## 配置驱动（改配置，不改代码）

**脚本里不硬编码任何业务值。** `fill.py` 启动时 `conf.load_config()` 读
`07-office-collaboration/config.yaml`，缺必填项直接抛 `ConfigError` 退出
（**故意不兜底**——兜底会导致「改了配置没生效，还以为在测新配置」）。

改这次要填什么，只动 `config.yaml`：

```yaml
manhours:
  entry:
    type: 项目实施                    # 工时类型
    project_hint: 智慧营销结算平台二期   # 项目按这个子串匹配
    customer: ""                      # 项目运维才需要手写
    work: 工时登记链路验证              # 工作内容
    hours: "1"                        # 消耗工时
  default_day: ""                     # 补录默认日期，留空则命令行传
  daily_total_limit: 1                # 合计上限，同时也是对账项
  columns: {type: 1, project: 3, work: 5, hours: 6, ...}   # 列索引
  main_fields: {work_date: field0022, total_hours: field0031}
```

| 层次 | 放什么 | 放哪里 |
|---|---|---|
| 平台层 | CDP 会话 / 页签 / 鼠标键盘 / 登录态 / 恢复弹窗 / 遮罩清理 | `_common/cap4.py`（`Sess`） |
| 配置层 | config.yaml 读取、点号取键、必填校验、URL 拼装 | `_common/conf.py` |
| cap4 层 | 子表读写 / 加行 / 下拉 / 人员选择器 / 明细选择器 / 主表字段 | `_common/cap4.py`（`Cap4Table`） |
| 业务层 | 填写顺序、对账规则、**该填什么值**（值在配置里） | 各 skill 的 `scripts/fill.py` + `config.yaml` |

**字段映射不进 `_common`** —— 一旦把 field0037 / ci11 这些写进公用模块，
两张表单的差异就会把公用层变成一堆 if 分支。

**周计划同样配置驱动**：`weekly_plan.plans` / `goals` / `summary` /
`row_defaults` / `main_receivers` / `columns` / `main_fields` 全在 config.yaml，
权重合计 100 也由 `plans` 的 `w` 决定。

## 两张表结构完全一致

| 用途 | config 键 | templateId | 差异 |
|---|---|---|---|
| 登记（当天） | `manhours.template_register` | -5700157742072248618 | 工时日期锁定当天，不可改 |
| 补录（历史日） | `manhours.template_backfill` | app9000000000000000001 | 工时日期可改，**必须改成实际那一天** |

`工时日期` = `field0022`。补录必须先写它（`write_field(s, "field0022", day)`），再选项目。

**工时日期是硬前置：写不进去直接中止，不能继续往下填。**
真踩过：早期版本日期写入报 `no holder`，脚本没中止、继续选项目填明细，
结果表单里日期空白但工时明细有内容 —— 整张废单，而且对账只报“日期 FAIL”没拦住。
现在 `fill.py` 在写日期失败、或补录模式下日期为空时，直接 `SystemExit(1)`。

## 复用时踩到的三个坑（2026-10-20 实测）

**1. 工时明细表的数据行不是从 tr[1] 开始**
`tr[0]` 是「█ 工时明细」标题行，`tr[1]` 才是表头，数据从 `tr[2]` 开始。
`Cap4Table` 会自动求表头行下标（按「表头必须含这些字」找），业务层只管 `row=1` 是第一条数据。
周计划的计划表/关键目标表 `tr[0]` 就是表头 —— **两种形态都必须支持，不要把行号写死**。

**不要用 `rows()` 的行数当“数据行数”**：表尾还有「合计」行和「工时填写提示：…」长文本行，
它们也在 `tr` 里。判数据行要额外要求「第 1 列是纯数字」。

**2. 主表日期字段的容器 class 和人员字段不同**
- 人员/文本域（主送 field0326）：`cap-field-content cap-field formson_xxx_field0326`
- 日期/工号（工时日期 field0022）：`cap4-formmain__td default-field-style cap-field formmain_77793|field0022`

原来 `field_text`/`field_xy` 死抠 `cap-field-content`，导致写工时日期报 `no holder`。
现在用 `[class*="fieldXXXX"]` + 含 `cap-field` 匹配。

**3. 项目名称格有「选择图标」，点它才是就地回填**
明细表「项目名称」那一格虽然 section 是 `is-browse`，但格内有一个
`<div class="icon CAP cap-icon-mingxibiaoxuanzeqi">`（约 16×24）。点它打开
「关联列表」layui 弹窗，确定后**回填到当前行，不新增行**。

工具栏「选择工时项目」是另一条路，语义就是**追加一行**。想就地填首行就用格内图标。
详见下方「步骤 3：选项目」。

## 项目弹窗（layui，不是 cap4 也不是 .selectorg）

点明细表工具栏「选择工时项目」后弹 **layui 层**：

```
DIV.layui-layer.layui-layer-iframe > DIV.layui-layer-content > IFRAME
```

- 定位：取所有 iframe，找 parent 链里含 `layui-layer-iframe` 的那个
- **点按钮后 iframe 数量不变**，不要靠数量判断弹窗是否打开
- 勾选后必须确认出现「已选择N条数据」，否则是点上了但没进选中集
- 确定按钮在**顶层窗口** `.layui-layer-btn0`，不在 iframe 里；常在视口外（实测 y=860），
  必须先 `scrollIntoView({block:'center'})` 再点

## 其余平台规则

cap4 平台通用规则（fieldNNNN 是 class / 写值必须真键盘 / 必须失焦再回读）
见 `_common/cap4.py` 顶部注释与 `seeyon-weekly-plan/SKILL.md`，这里不再重复。

## 配置文件

**所有固定值在同级目录 `../config.yaml`**（与 `seeyon-weekly-plan` 共用），
由 `../_common/conf.py` 读取。完整键位见上文「配置驱动」节。

```yaml
manhours.template_register / template_backfill   # 两个模板 id
manhours.entry.{type,project_hint,customer,work,hours}   # 本次要填什么
manhours.default_day             # 补录默认日期
manhours.daily_total_limit       # 每天合计上限（同时是对账项）
manhours.columns / main_fields   # 列索引 / fieldNNNN
portal.home / summary_url        # 读历史工时入口
```

正文里的人名只是示例，**标题里的人是登录人自动带出的，不要写死**。

**写脚本时先问：这个值是「结构」还是「数据」？** 结构（field id、列索引、步骤顺序）留代码里；
数据（模板 id、人名、日期、工作内容、项目名、工时数）一律进 config.yaml。
用户明确要求过这一点 —— 脚本里出现不该硬编码的业务值就是缺陷。

## 环境前提

- Chrome/Edge 已开 `--remote-debugging-port=9222`，且已登录 xt.seeyon.com
- 用 Hermes venv 的 python：`<HERMES_HOME>\hermes-agent\venv\Scripts\python.exe`，需要 `websockets`
- 通过 CDP `Target.attachToTarget` + `Runtime.evaluate` 执行 JS，鼠标用 `Input.dispatchMouseEvent`
- 表单内容在 cap4 iframe：`document.querySelector('iframe[src*="cap4"]').contentDocument`
- 直接用 `../_common/cap4.py`：`list` 扫全部端口页签 / `check <port>` 判登录态 / `tables <port> <tabid>` 读表头。
  模块里有 `Sess` / `Cap4Table` / `field_text` / `write_field` / `pick_people`，**别自己另写一套**。
  旧版 `../seeyon-weekly-plan/scripts/cdp.py` 已废弃。

### cap4 平台通用规则（两张表都适用）

- **`fieldNNNN` 是 class，不是 element id。** `getElementById('field0041')` 拿不到元素（已在周计划表实测证伪：19 个“字段 ID”里 17 个 MISSING）。真实选择器是 `.cap-field-content.cap-field.<fieldNNNN>`；子表字段的 class 带 `formson_<表单id>_<记录id>_` 前缀，用 `[class*="fieldNNNN"]` 匹配。只有日期这类内层控件才有真 id（`field0087_<子表id>`）。
- **写值必须真实键盘**（点进单元格 → Ctrl+A → `Input.insertText`）。用 native setter + dispatchEvent 只改 DOM 不进 Vue 状态：回读看着有值，但依赖字段（合计、自动带出）不变，提交会丢。
- **必须失焦再回读**。数字字段常在 blur 时才重算 / 提交。

### 步骤 0：先验登录态再开表单

未登录时打开填报页，表现是「cap4 iframe 里等不到『消耗工时』，轮询到超时」——像渲染慢，实际是登录墙。先跑 `python ../_common/cap4.py check 9222`（`list` 扫全部端口页签），并先扫 9222/9223/9226/9229 几个端口（本机常同时跑多个调试实例，其中一个可能仍有有效会话）。

登录通过的唯一判据是落地到工作台（`method=main` 且有工作台正文）。`document.cookie` 非空、`Network.setCookie` 返回 `success: true` 都**不是**证据——登录墙页也带 cookie，过期 token 也能注入成功。未登录就停下让用户自己在那个窗口登录，不自己提交登录、不拿其他域的共享凭据去套。

## 两个模板

| 用途 | 配置键 | 标题 |
|---|---|---|
| 登记（当天） | `manhours.template_register` | 顾问工时登记(<登录人> <日期>) |
| 补录（历史日） | `manhours.template_backfill` | 【补录】顾问工时登记(<登录人> <日期>) |

**两者结构完全一致，唯一差异：登记的工时日期锁定当天不可选，补录的工时日期可选。**

URL：`{base_url}/seeyon/collaboration/collaboration.do?method=newColl&from=templateNewColl&templateId={id}&showTab=true`

## 表单字段

下面的 `fieldNNNN` 指 **class 名**（见上文平台通用规则），不是 element id。

基本信息：

| 字段 | id |
|---|---|
| 顾问姓名 | field0033 |
| 登记日期 | field0009 |
| 流水号 | field0024 |
| **工时日期** | field0022 |
| 天 | field0023 |
| 本月工时合计 | field0029 |
| 工时年度 / 月度 / 周 | field0018 / field0019 / field0020 |
| 所属战区 / 区域 / 岗位序列 | field0025 / field0011 / field0026 |
| 抄送人员 / 知会人员 | field0095 / field0096 |

工时明细表（表头含「消耗工时」，用 `/消耗工时/` 定位最稳）：

| 列 | 字段 | 控件 |
|---|---|---|
| 序号 | - | 自动 |
| 工时类型 | field0037 | 选择器 |
| 是否驻场运维 | field0141 | 选择器 |
| 项目名称 | field0072 | 只读文本，点格内 `div.icon.cap-icon-mingxibiaoxuanzeqi` 打开选择器，回填当前行 |
| 客户名称 | field0039 | 项目实施=只读；**项目运维=可手写** |
| 工作内容 | field0040 | textarea |
| 消耗工时 | field0041 | input |

合计 field0031 自动算，备注 field0032。

## 核心规则

**每天合计消耗工时 ≤ 1**（`daily_total_limit`）。

常规情况：
- 一天一般只记**一个项目**，消耗工时直接填 **1**
- 只有真跨项目才拆，拆完合计仍 = 1（如 0.9 + 0.1）
- 不要自己发挥拆成 0.3/0.3/0.4
- 工时内容由operator-a提供，不自己编

## 工时类型与差异

七种：项目实施 / 项目运维 / 售前支持 / 能力提升 / 公司会议 / 其他事务 / 运维服务

**默认只用：项目实施、项目运维**

| 类型 | 项目名称 | 客户名称 |
|---|---|---|
| 项目实施 | 格内选择器（`cap-icon-mingxibiaoxuanzeqi`）回填本行 | 跟随项目自动带出，只读 |
| 项目运维 | 格内选择器回填本行 | **不跟随项目，需手写**（已实测可编辑） |
| 其余五种 | 未逐一验证（UNVERIFIED），按项目实施流程走，遇到差异现场确认 | 同左 |

**先选工时类型，再点项目名称的图标** —— 图标可能要等类型写入后才渲染出来。

## 填报流程

### 步骤 1：打开并等就绪

用上面 URL 打开，轮询等 `消耗工时` 出现在 body 里再动手。补录先改`工时日期`（field0022）。

```js
for (let i = 0; i < 40; i++) {
  const d = document.querySelector('iframe[src*="cap4"]')?.contentDocument;
  if (d?.body && /消耗工时/.test(d.body.innerText || '')) break;
  await new Promise(r => setTimeout(r, 1000));
}
```

控件类型速查（选下拉 / 与输入框同容器 / 日期浮层）见同级技能文件
`../seeyon-weekly-plan/references/cap4-control-dispatch.md`。**填表前先查它。**

### 步骤 2：选工时类型

点第一个数据行「工时类型」单元格 → 在 **`.ui-popper`** 里选目标类型。
选项面板 selector 是 `.ui-popper > .ui-popper-content`；`.ui-select-dropdown` 在本平台
查不到元素，按它查会稳定返回 0 个选项（伪造成“没展开”）。选完失焦回读，
确认「工时类型」列真有值再往下走。

**每个选项在 DOM 里嵌套渲染 3 份**（`.ui-select-option` > `.cap4-select__option` >
`.cap4-select__option__left`，同一文字同一 y）。两个直接后果：
- 按坐标点要取**最外层 `.ui-select-option`**，点到内层包装可能只是 hover 不进值；
- 键盘 `↓` 一次跨 3 个节点 → 会跳过一项（`↓`+`Enter` 得到的是第 2 项「项目运维」，
  不按 `↓` 直接 `Enter` 才是「项目实施」）。

**下拉面板可能向上弹出**（popper 自动翻转），所以点选项前必须重新读面板 item 的 y，
不能沿用点开下拉前的行坐标。

### 步骤 3：选项目（两种入口，语义不同）

| 入口 | 行为 | 什么时候用 |
|---|---|---|
| 明细行「项目名称」格内的 `div.icon.cap-icon-mingxibiaoxuanzeqi` | **回填当前行**，不新增 | 默认用这个；首行空行就地填满 |
| 明细表工具栏「选择工时项目」（`.formson-list__button`） | **追加一行** | 确实要多记一个项目时才用 |

**首选格内图标**，它让表单保持「1 行 = 1 条记录」，不用面对空行问题。

#### 格内图标走法（已验证）

```js
// 定位：第 1 行第 4 个 td（ci=3）里的选择图标
const tb=[...d.querySelectorAll('table')].find(x=>
  /工时类型/.test(x.innerText)&&/消耗工时/.test(x.innerText));
const icon = tds[3].querySelector('div.icon.cap-icon-mingxibiaoxuanzeqi');
```

- 图标是 **`<div>`**，不是 `<i>`/`<svg>`/`<img>`。用 `querySelectorAll('i,svg,img')`
  查图标会得到空数组，从而得出「这格没有图标、没有写入通道」的**错误结论**。
  查图标一律用 `[class*=icon]` 或直接按 `cap-icon-*` class 名查。
- 弹窗标题是「关联列表」，同样是 layui iframe，定位方式同下。
- 勾选项目行后点**顶层** `A.layui-layer-btn0`（文字=确定）。实测该按钮 y≈860，
  在视口外，必须在**顶层**窗口按坐标点，不能只在 iframe 内找。
- 弹窗里**没有**「已选择N条数据」提示也能提交；判定成功只看回填后格子里有没有项目名。

#### 工具栏「选择工时项目」走法（会新增行）

弹窗是 **layui 层**，既不在 cap4 iframe，也不是 `.selectorg`：

```
DIV.layui-layer.layui-layer-iframe > DIV.layui-layer-content > IFRAME
```

定位：取所有 iframe，找 parent 链里含 `layui-layer-iframe` 的那个。
**点按钮后 iframe 数量不变，不要靠数量判断弹窗是否打开。**

弹窗内容：合同/项目列表，表头 合同编号 / 客户名称 / 项目名称；上方筛选 合同编号、客户名称、所属区域、项目编号，带「筛选」「重置」「高级展开」。

操作：
1. 在 iframe 内按项目名称或客户名称文字匹配目标 `tr`
2. 点它的 `input[type=checkbox]`（真实鼠标，用 iframe rect + 行 rect 算页面坐标）
3. 确认出现「已选择N条数据」
4. 点确定：按钮在**顶层窗口** `.layui-layer-btn0`（文字=确定），不在 iframe 里；先 `scrollIntoView({block:'center'})` 再真实点击（实测坐标常在 y>1000，视口外必须滚）

### 步骤 4：确认回填结果

用格内图标 → 回填当前行，行数不变：

```
行1: 1 | 项目实施 |  | 智慧营销结算平台二期 | 四川客户方 | |
```

用工具栏「选择工时项目」→ **新增一行**，原空行保留：

```
行1: 1 | （空） |   |                |                | |
行2: 2 |        |   | 智慧营销结算平台二期 | 四川客户方 | |
```

无论哪种，都要**回读确认**再往下填，不要默认往某一行写。

### 不要制造多余空行

**不要为了多一行而用工具栏按钮，也不要在有数据行时先「新建」。**
格内图标能就地回填，就没有多余行需要处理。

如果已经产生了多余空行：空行删不掉（工具条「删除」/ 行首「+」菜单「删除一行」/
「删除全部」实测均无效，「删除全部」后平台立刻补回 1 行）。这时**不要继续折腾删行**，
重新打开表单重来更快 —— 用格内图标路径一次就不会有这个问题。

**验收标准是「恰有 1 条有数据的数据行、且已填全」**：判数据行要求第 1 列是纯数字；
判空行要同时要求工时类型/项目名称/工作内容/消耗工时全空（序号列不算，空行也有序号）。

**不要为了消除空行去改数据**（如把空行也填上内容），那会把废行提交上去。

### 元教训：查不到图标时，先怀疑自己的选择器

本轮最贵的错误：用 `querySelectorAll('i,svg,img')` 统计图标，得到空数组，
就断定「这格只读、没有写入通道」，进而改用会新增行的工具栏按钮，
然后花了几个小时研究「怎么删掉删不掉的空行」—— **整条路线都是错的**。

- 查图标一律用 `[class*=icon]`、`[class*=xuanzeqi]`，或直接按 `cap-icon-*` 类名找。
  平台大量用 `<div class="icon CAP cap-icon-xxx">`，不是 `<i>`。
- `is-browse` 只说明「不是直接输入框」，**不等于不可操作**：里面可能装着选择器图标。
- 判「有没有写入通道」的正确做法是**点一下试试并回读**，不是只读 class。

为一个字段折腾几十次点击/删行之前，先用 30 秒读它的 DOM 状态：

```bash
python scripts/probe_row_state.py          # 逐行逐格导出 editable / readonly / no-channel
```

- ❌ **不要用「控件列表为空 + `is-browse`」判定没有写入通道。** 这是本轮真正烧掉整个下午的错误判据：
  关联字段的选择器图标是 `<div class="icon CAP cap-icon-*xuanzeqi">`，既不是 input/textarea，
  也不是 `<i>`；按 `input,textarea,[class*=select],i` 查出空数组 → 误判「不可操作」→
  改用会新增行的工具栏按钮 → 再花几小时研究怎么删掉删不掉的空行。
- 正确判据：**点一下并回读**。点格内任意 `[class*=icon]` / `cap-icon-*` 元素，看是否弹出选择器、
  回读该格是否出现值。DOM class 只是线索，不是结论。

### 结论纪律：不能为了收尾而美化观察结果

用户贴截图指出「第 1 行是空的」，就不能回答「不需要删除」；用户说某条路走得通，
就不能把自己的 DOM 快照当成唯一事实去否定他。这两件事都是**用结论凑结果**，比报失败更糟。

- 与自己快照冲突时，明确说出差异（「你截图里这格是黄底带蓝图标，我这边 DOM 里
  `is-browse`、连图标节点都不存在」），然后**请用户手动做一遍那一步**，在他停住的那一刻抓 DOM。
  抓用户真实操作，比再猜十次点击姿势有效。
- **抓之前先确认抓的是同一个页签**：按标签标题里的时间去核对（标题形如
  `【补录】顾问工时登记(operator-a 2026-10-20 17:16)`），不要凭“最近一个”或列表顺序猜。
  抓错页签会得出“用户的截图和平台不一致”这种完全错误的结论，而真相只是两边看的是不同标签页。
- **一次排查只用一个页签，用完就关**。每次尝试新开一个页签，几次下来会堆出几十个同名页签，
  之后既找不到用户在看哪一个，也分不清哪次尝试留下了什么状态。复用同一个页签重开 URL 即可。
- **同一个控件连续 2 次尝试失败就停手**，改跑探针、读状态、或直接问用户。
  第 3 次开始的盲点只是在消耗用户耐心（本轮为此浪费了整个下午）。
- 报失败要给出「已排除什么 + 还差什么信息」，不要给一堆试探日志让用户自己判断。

「点了没反应」的完整排查顺序（`elementFromPoint` 双层对照 → 遮罩 → 坐标过期 →
可见性 → iframe 重绘 → 占位符改坏 JS），见同级技能文件
`../seeyon-weekly-plan/references/cdp-interaction-debugging.md`。

### 步骤 5：补齐字段

- 工时类型（field0037，选择器）
- 是否驻场运维（field0141，选择器）
- 客户名称：**项目运维类型要手写**；项目实施类型是只读
- 工作内容（field0040，textarea）
- 消耗工时（field0041，小数，默认 1）

### 步骤 6：校验

- **恰有 1 条有数据的数据行**（项目名称非空的），且该行工时类型/客户名称/工作内容/消耗工时全填
- 合计 ≤ 1
- 回读全部行确认

**不要把「首行空行」判为 FAIL** —— 用格内图标路径根本不会有空行；
若出现空行，是用了工具栏按钮，重开表单重来即可。

**提交前交operator-a确认。**

## 读历史工时（周计划事实来源）

1. 打开 `portal.home`
2. 在「已发事项」里找标题含 `portal.sent_list_keyword` 且带日期的记录，记下 affairId
3. 打开 `portal.summary_url`（替换 affairId）
4. 轮询等 `消耗工时` 出现，再读明细：

```js
const d = document.querySelector('iframe[src*="cap4"]').contentDocument;
const tb = [...d.querySelectorAll('table')].find(t => /消耗工时/.test(t.innerText));
[...tb.querySelectorAll('tr')].slice(2).forEach(tr => {
  const c = [...tr.querySelectorAll('td')];
  // c[1] 工时类型  c[3] 项目名称  c[4] 客户名称  c[5] 工作内容  c[6] 消耗工时
});
```

## 坑

- 工时记录标题带日期，按标题筛比按时间筛准
- `天` 字段自动算，不要手改
- 明细表「合计」行 cells 也是 7，靠内容「合计」区分
- 工时类型、是否驻场运维都是选择器，`Input.insertText` 打不进去。
**下拉面板 selector 是 `.ui-popper`，不是 `.ui-select-dropdown`**（后者在本平台查不到元素，
会稳定返回 0 个选项，伪装成「下拉没展开」）。详见 `seeyon-weekly-plan` 的
`references/cap4-control-dispatch.md`。
- 项目名称只读文本，靠格内 `div.icon.cap-icon-mingxibiaoxuanzeqi` 回填本行（**不要**用工具栏「选择工时项目」，那个会新增行）
- 选完项目**回读确认行数没变**；行数变了说明走错入口，重开表单重来
- 空行**删不掉**（工具条「删除」/ 行首「+」菜单「删除一行」/「删除全部」实测均无效，
  「删除全部」后平台立刻补回 1 行）。所以**根本不要制造空行**，不是「接受空行」
- **表格变动后不要复用位次索引**（`_rows[表头行+1]`）。回填/新建/删行都会让脚本里
  缓存的 `row` 指到别的行，从而反复读到“值没变”的假象。每次操作后按「序号列纯数字」
  或 `selected-tr` **重新定位**目标行再读。
- **日期字段 holder 里有两个 input**：可见的 `field0022_format`（w=170）和隐藏镜像
  `field0022`（w=0）。`querySelector('input')` 会拿到宽 0 那个，写进去回读永远空。
  按宽度倒序取可见元素。
- **写完日期会残留 `.ui-datepicker` 浮层**，盖住表格吃掉后续所有点击。
  `blur()` 里已按 `Escape` 关掉（`close_pickers()`）。
- **cap4 iframe 持续空白（`bodyLen === 0`）不是渲染慢，是草稿恢复弹窗挡住了**。
  顶层 body 里有「有未保存数据，是否恢复？ 恢复 / 不恢复」时，表单**根本不会渲染**，
  轮询多久都等不到「消耗工时」——死等 30 秒再报“超时”会把你引向排查登录态/网络，全是错方向。
  判据：先读顶层 `document.body.innerText`，含「是否恢复」就先点「不恢复」（`dismiss_restore_dialog`）再轮询。
  每次开表单都要处理，因为上一次失败的会话会留下草稿。
- 标题里的人名是登录人，不要写死
- **校验要盯依赖字段，不能只回读自己刚写的输入框**：工时看「合计」/「本月工时合计」，它们不动就说明写入没进表单状态

## 已验证 / 未验证

**先跑 `scripts/probe_row_state.py` 再动手**：逐行逐格给出 editable / readonly / no-channel，
比任何点击试探都快。以下结论均可用它复现。

- PASS：**1 行完成全链路**（选类型 → 格内图标选项目回填本行 → 工作内容 → 工时 → 合计 1.00），
  登记 12/12、补录 13/13 对账通过，**全程无多余行**
- PASS：工时类型下拉（`.ui-popper` 里 `.ui-select-option`，必须点箭头 `cap-icon-shu-zhankai`）
- PASS：格内选择器回填（`div.icon.cap-icon-mingxibiaoxuanzeqi` + 顶层 `A.layui-layer-btn0`）
- PASS：补录日期写入（取可见的 `field0022_format`，非宽 0 镜像）
- PASS：人员选择器通用流程（见 seeyon-weekly-plan）
- PASS：项目运维的客户名称可手写
- **已证伪（旧结论，勿再沿用）**：
  - ❌「项目名称格只读、无图标」→ 图标是 `div`，只查 `i/svg/img` 会漏掉
  - ❌「必须接受 1 空行 + 1 数据行」→ 用格内图标就不产生空行
  - ❌「空行删不掉所以只能接受」→ 根本不需要删，不要制造它
- UNVERIFIED：售前支持 / 能力提升 / 公司会议 / 其他事务 / 运维服务 五种类型的字段差异
- UNVERIFIED：带多余空行的表单能否提交通过校验（提交前必须问operator-a）
