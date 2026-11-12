---
name: udc-trace-to-api
description: Use when 逆向 UDC REST 契约或监听页面请求时。CDP 抓包转 OpenAPI。
---

# UDC Trace → API（浏览器抓包 → REST 契约还原）

## 适用场景
- 审计 UDC 前端某操作的 REST 写链（如「页面构建」「字段保存」「微流程发布」）
- 监听前台接口：worker 手写 CDP 脚本抓包前的标准化替代
- 从真实页面操作生成 OpenAPI 文档（替代手工整理 299 个 REST op）

## 铁律：op 名未知时先抓包，禁止连续猜（用户红线）

**猜接口名的成本远高于抓一次包。** 本平台 GraphQL 的 `UnknownArgument` / `FieldUndefined`
是唯一反馈，每猜一次就是一次完整往返；而一次真实抓包能直接给出 op 名 +
paramsType + 完整 body + variables 层数。猜两轮不中就**立刻切抓包**，不要枚举第三个名字。

判据：只要你在写「这个参数名是不是 `ids` / `enumIds` / `idList` …」这类变体循环，
已经越线了。停下来**自己抓包**（见 `references/rea-evidence-capture.md`）。

**默认不许把抓包成本转给用户。** 「请他贴一下报文」听起来零成本，实际会被明确拒绝：
他要的是你自己会抓，而不是每次都来问他要。只有自己确实抓不到（hover 才出现的隐藏按钮、
必须人工确认的二次弹窗）才请用户操作**一次**，且一次说清是哪个动作。
他已经给过的报文当模板复用，同一个接口绝不问第二遍。

**请求用户操作前，先把自己能做的部分做完。** 典型反例：弹窗已经打开、字段已经知道 id，
却直接请用户「贴一下报文」——其实只差「填三个框再点确定」这一步，而这步自己能做。
正确顺序是：自己先走完整个动作序列（开弹窗 → 读字段 → 填表 → 提交），
只有当某个交互物理上做不到（必须人眼确认的二次弹窗、必须人工拖拽的控件）才请用户。

同样的规则适用于 REST 路径：`404` 说明路径不存在、`405` 说明路径在但动词/绑定错，
两者都是「机制反馈」而不是「名字候选表」——读 404 响应体回显的 `path` 字段确认自己
到底请求了什么，再决定下一版，别连环盲试。

## 抓包前先确认数据是否已经在页面里

写操作之前的读数据通常**在页面加载时就请求完了**：滚动、切 tab 只是重绘，不会产生新请求。
在这种页面上装 hook 再滚动，抓到的是 0 条——不是 hook 坏了，是没有请求可抓。
⇒ 要抓某条请求，必须**从触发点前一步开始**：先装 hook，再执行会真正发请求的动作
（点「新建」→ 填表 → 点「确定」），而不是在已加载完成的页面上反复滚动。

**页面内 fetch/JS hook 会被导航重置**：`location.href = ...` / 刷新之后 `window.__TRACE__` 归零、
包装器失效。跨导航抓包要么在导航前装（CDP 级持久），要么导航后**重新装再动作**，
别把「导航后 hook 还在」当默认前提。

## 核心思路（源自 browserbase browser-trace/browser-to-api）

```
自动化（worker/CDP 点击）──▶ Edge CDP target（9223~9231）
         │                          │
         ▼                          ▼
   驱动页面操作            tracer：CDP firehose → raw.ndjson
                           sampler：周期截图 + DOM dump
```

**关键设计（照抄 browser-trace）**：tracer 只启用只读域（Network/Runtime/Log/Page），
绝不发 Input.dispatch* 或 Runtime.evaluate——多客户端挂同一 target 时不会干扰正常自动化。

## 管道四步

### 1. start — 启动抓包

对指定端口（如 9223）的 target 开启 Network 域监听，事件流写 NDJSON：

```
.o11y/<run-id>/cdp/raw.ndjson
```

实现要点：`Network.enable` 后循环 `c.on(method, ...)` 记录；事件按 requestId 配对。
CDP 允许多客户端并发挂同一 target——worker 照常操作，tracer 旁路记录。

### 2. operate — 执行被审计的操作

worker 用现有 cdp_drive.js / 页面点击流程执行目标操作（保存字段、点构建、跑检查）。
tracer 全程旁听，不做任何动作。

### 3. stop + bisect — 切片

停抓后按两种维度切片（照抄 bisect-cdp.mjs 设计）：
- 按域：`network/requests.jsonl`、`network/responses.jsonl`、`console/logs.jsonl`、`page/navigations.jsonl`
- 按页面：以 `Page.frameNavigated` 为界切 pages/000、pages/001...

**bisect map（UDC 审计最常用的是前两行）**：

| 文件 | CDP 方法 | 内容 |
|---|---|---|
| cdp/network/requests.jsonl | Network.requestWillBeSent | url/method/headers/postData/requestId |
| cdp/network/responses.jsonl | Network.responseReceived | status/headers/mimeType |
| cdp/network/failed.jsonl | Network.loadingFailed | 错误请求（403/500 定位） |
| cdp/console/exceptions.jsonl | Runtime.exceptionThrown | 前端异常栈 |
| cdp/page/navigations.jsonl | Page.frameNavigated | 页面边界（iframe 跳转） |

**response body 不在 firehose 里**——需要 body 必须在请求结束时机同步调
`Network.getResponseBody`（用 requestId）。这是 UDC 抓包最容易漏的点：
POST 的业务返回（BOOT_0000/affectCount）都在 body 里。

### 4. discover — 配对 → 模板化 → 推断 → OpenAPI

照抄 browser-to-api 五阶段：
1. **load**：requests+responses 按 requestId 配对，丢 OPTIONS/3xx/静态资源，只留 XHR/Fetch/Document
2. **filter**：剔除埋点/字体/CSS；UDC 场景加白名单 `lowcode-test2.example.com`
3. **normalize**：路径段模板化——UUID→{id}、纯数字→{id}、hex≥8→{id}；按 (origin,method,templatedPath) 分组
4. **infer**：JSON-Schema 推断——required=全样本都有、类型=并集、enum≤8 值且≥5 样本；日期/uuid 格式提示
5. **emit**：结构相同的 schema 合并进 components.schemas；产出 openapi.yaml + report.md + confidence.json

**UDC 特化**：GraphQL（/graphql?udcPageInfoUpdatePost 这类）的 body 是 `{operationName, variables}`，
infer 阶段对 variables 做深度展开才有意义；introspection 已禁用，样本推断是唯一途径。

## 与现有工具的关系
- **替代**：worker 每次手写 `ed_check*.js` / `capfunc.js` 抓包
- **组合**：`getcol3.py` 直连 MySQL 仍是权威（trace 只看流量，不碰库）
- **产出落盘**：`docs/audit/artifacts/udc-trace/<run-id>/`，报告摘要进事实文档

## 抓不到请求时的排查顺序

**先查工具，不要猜接口名。** 本机有 `rea` MCP 三件套，比手写脚本可靠得多：

```
rea:list_browser_targets         列出 CDP target（先确认 target 存在）
rea:inspect_web_page             被动观察：DOM/a11y/console/请求响应结构
rea:capture_browser_scenario     主动操作+抓包（connect 模式接已有 CDP）
rea:inspect_web_network_capture  离线读 HAR
```

**排查顺序**：
1. `list_browser_targets` 确认 target 的 **当前 URL**——如果已是 `/login`，登录态已失效，
   抓什么都是空的。这一步必须先做。
2. 页面内 `fetch` 拦截器（`window.fetch = ...`）在**导航后立即失效**，不要依赖它抓跨页流程。
3. 手工 CDP 的 `Network.*` 域在部分 Edge 版本返回 `-32601`；遇到就把抓包交给 rea，
   不要再改页面钩子硬扛——钩子还会被导航冲掉。
4. `capture_browser_scenario` 常以 `resource_constraint` 报错结束——**这不是失败**，
   证据已完整保留，`export_evidence_bundle` 导出后本地解析即可。详见 references。

**最贵的错误**：接口名靠猜。`udc<领域><动作>Post` 是固定规律，所以 op 名可以从相邻接口推；
但 **参数名与字段语义绝不能推**（`enumId` vs `enumCode`、`name` 是 i18n JSON 还是裸文本、
`appGuid` vs `appId`）——一次真实抓包胜过十次猜测，而猜错的代价是每轮一次完整往返。

## 先读本仓/本机的既有事实，再抓包

抓包前先查这三处，它们往往已经写好了答案：

```text
1  本地 skill 的 references/  ← 已经有该域的契约表、抓包配方、错误字典
2  目标仓库的 core/facts/ 与 docs/operation-contracts/  ← 已经有事实格与写链
3  目标仓库的 components/  ← 已经可能有构造器/校验器，只是没接上
```

**读到「某条契约还没验证、必须靠抓包解决」时，先确认那是指令而不是现状。**
当本仓已经有一份枚举域契约表、而你正花十轮去猜同一组字段名时，你缺的不是抓包能力，
是那一份文档没被读。猜错的成本是每轮一次完整往返 × 十轮；读一份已有文档是一轮。

反过来，如果某条契约在本地文档里确实没有、只有一句「未定」，那才真的去抓。

### 「已有文档」不是「已经读过」——开抓前先真读

上面第三条是本 skill 自身反复被违反的地方：仓里明明有该域的契约表，
但因为没打开那个文件，就在同一个字段名上猜了十几轮。

**执行动作（按顺序，不得跳）**：

```
1  tool_search / skills_list 查该域有没有现成 skill
2  skill_view 打开它，linked_files 里看 references/ 有没有该域的契约表
3  找到后先 grep 目标字段名（enumId / enumCode / itemValue / parentId…）
4  文档里写「未定 / 需抓包」→ 才进抓包流程
5  文档里已有 → 直接用，不再猜
```

**自查信号**（出现即停手回第 2 步）：

```
- 自己在心里列举「应该是 X 还是 Y」
- 已经改了第三版参数名
- 报错文案里出现的是业务字段名（如「上级枚举项ID 不能为null」）
  → 这不是「名字错了」，是「名字对了、缺必填字段」，去看契约表
```

错误文案里点名业务字段时，**答案通常已经在契约表的必填槽位列里**，
继续猜参数名等于把已知信息扔掉。

### 抓包得到真实 body 后，要回读对齐构造器

抓到真实 body 后，把平台字段逐个对到自己的构造器产出上。
本例抓到 `udcEnumPost` body 后，发现自有构造器缺 8 个字段
（`appGuid` / `categoryId` / `dataStatus` / `bizType` / `expansible` / `enable` /
`enumType` / `children`），且 `name` 是 i18n JSON 而非裸文本。
**不改构造器 = 下次仍会造出平台拒绝的请求体。**

回读对齐后，把「平台真实 body」写成断言测试（字段齐全 + 形态正确），
否则下次重构会再漂回去。

### 已知「平台报错指向必填字段」时的正确解法

平台报 `BOOT_1001 <业务字段> 不能为空` 时，**这是契约反馈**：
字段名与槽位已对，缺的是这个槽位的值。动作是去查该槽位的来源
（表结构 / 契约表 / 抓到的 body），不是换参数名。

判据：报错文案里出现的是**业务语义名**（枚举项编码、上级枚举项ID、业务版型、
实体性质）而非**英文字段名**时，直接走「查槽位来源」分支。

## 抓包能力本身也会被高估

能驱动浏览器不等于能拿到请求体。三类失败要分开：

```text
没点到目标元素    → 点击元素选错/被遮挡/需 hover；先读弹窗结构与元素坐标
动作没走完        → 只点了「新建」没填表，body 为空或请求没发生
body 没暴露        → body.state == "not_exposed"：没开 request_body，或该请求根本没发生
```

**「点开弹窗」不等于「操作完成」**——必须填完字段再提交，否则拿到的是空 body，
而你会把「表单是空的」误读成「接口不对」。

## 批量猜名字时，先按错误信息归类

平台报错本身是契约反馈，不是重试信号：

```text
UnknownArgument  / FieldUndefined   → 名字错了（换个词）
Index: 0, Size: 0                    → 名字对了但参数个数/位置不对
BOOT_1001 <field> 不能为空            → 名字对了，缺某个必填字段（这是最有价值的一类）
BOOT_3002 to type Int                → 名字对了，类型不对
```

`BOOT_1001 <field>` 直接点名了缺哪个字段——把这一串错误记下来，它就是该接口的必填字段清单。
**连着猜三轮不中就切抓包**，别把变体序列当工作流；已经问过用户的报文绝不再问第二遍。

## 安全红线（不可违反）
- 凭据值/cookie 一律 [REDACTED]，trace 落盘前过滤 Authorization/Cookie 头
- tracer 只读，不得在同一 CDP 连接里混入点击动作（干扰 worker 的操作序列）
- 9223~9231 是各域专属端口，tracer 用哪个端口就记进 run-id，防止跨域串数据

## 终态口径：组装映射，不是请求快照（用户定调）

一切 UDC 配置（微流程节点/面板/菜单）本质 = **预制模板 + 用户选择 → 组装器 → 存储 JSON**。
trace 只是手段，终态产出必须把三层分开：
1. **预制层**：节点/面板/菜单的模板从哪来（udc_* preset 表 / attribute.json / 前端 chunk schema 枚举），插槽结构与默认值
2. **用户选择层**：面板每字段接受什么输入（枚举/实体引用/表达式）
3. **组装层**（核心产出）：前端如何把选择填进模板生成 POST body——每个字段能被「插槽 + 来源 + 填充规则」完整解释，否则组装规则未闭环

## 参考原文
- 本机 rea 证据抓包实操（connect 模式、超预算导出、事件解析、body base64）：
  `references/rea-evidence-capture.md`
- 方法论：browserbase/skills 的 browser-trace/REFERENCE.md（架构+bisect map）
         与 browser-to-api/REFERENCE.md（五阶段管道）
- 本地缓存：<HERMES_HOME>/cache/scratch/skill-src/skills/{browser-trace,browser-to-api}/
