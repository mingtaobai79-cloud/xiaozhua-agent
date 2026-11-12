---
name: sdd-protocol
description: Use when 修订三 Agent 协作协议或 VERDICT 规范时。成熟实践对照本机实测坑。
---

# SDD 协议（三 Agent 协作的成熟实践对照）

来源：obra/superpowers 的 subagent-driven-development（568 行）+ verification-before-completion。
与我们自研的三 Agent 工具高度同构，以下是有价值的核心差异点。

## 1. Rulings, not stalls（裁定而非停摆）

原文：
> A running plan does not wait on a human. Conflicts, ambiguities, plan defects — decide them.
> Record every decision as `Ruling: <决定> — <为什么> — <错了的代价>`，keep going.
> A wrong ruling costs rework your human partner can see and undo; a session parked
> on a question costs their whole day and buys nothing.

**只有四种情况才停下来问人**：
1. 不可逆/破坏性操作
2. 安全敏感动作
3. worktree 之外有副作用的操作（merge/push 共享分支/发布）
4. 计划烂到每条路都是瞎猜

对照我们的实践：C 组曾因「连续 8 轮元讨论」触发冻结令——正是缺 Ruling 机制导致
把该自行裁定的事上抛。本机 PROMPT 的 NEEDS_HUMAN 触发条件已接近，可补
`Ruling: 决定-理由-代价` 三段式记录格式。

## 2. 修复轮次上限（Fix Round Cap）

原文：`R≤3 resume implementer; R≥4 fresh implementer with more capable model; R=5 adjudicate`

即：同一发现修 3 轮内继续用同一 implementer（带上下文续修）；
第 4 轮换新 implementer + 更强模型（避免同一上下文里死磕）；
第 5 轮不再修，逐条人工裁定 open findings。

对照：B 组 B-9 硬化循环、数据迁移的工具链治理超 10 轮——都缺这个 cap。
已在本机 PROMPT 加「元讨论连续不超过 2 轮」，可再吸收「R≥4 换模型」策略。

## 3. 审查包（Review Package）先行

原文流程：implementer 完成后先生成 review package（diff + 测试输出 + 自查），
再派 task reviewer——reviewer 拿到的是打包好的证据，不是自己翻仓库。

对照：我们 auditor 有时自己重新跑一遍（重复烧 token），有时只看 implementer
自述（轻信）。折中：VERDICT 前必须包含 implementer 的 review package 引用 +
auditor 抽查一条独立验证（不重跑全量）。

## 4. Verification Before Completion（铁律）

原文核心：
```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
If you haven't run the verification command in this message, you cannot claim it passes.
```

对照表（原文）直接可用于 auditor 的 VERDICT 模板：

| 声称 | 需要 | 不算数 |
|---|---|---|
| 测试过 | 本轮测试命令输出 0 失败 | 上一次跑过/「应该能过」 |
| Bug 修了 | 复现原始症状的测试通过 | 代码改了就 assumed fixed |
| Agent 完成 | VCS diff 见到改动 | Agent 自报成功 |
| 需求满足 | 逐条 checklist | 测试全过 |

红旗词（出现即打回）：should / probably / seems to / 应该 / 大概 / 看起来。

与我们「STATIC ≠ LIVE」「HTTP 200 ≠ PASS」完全同源，可把此表补进
AUDITOR-CURRENT.md 作为 VERDICT 判定表。

## 5. Context 隔离（fresh subagent per task）

原文：每个 task 派全新 subagent，不继承 session 历史——「precisely crafting their
instructions and context」。

对照：我们用 --resume 复用上下文（用户明确要求，省 token），这与原文相反。
**不照搬**，但吸收其提示：resume 放大了重读成本，所以 ROUTE 4KB + 消息合并
+ 100k 压缩是必要补偿。两边取平衡即可。

## 6. 组装映射是采集的终态口径（用户定调，适用于一切 UDC 配置域）

微流程节点、面板配置、菜单配置本质同一模式：**预制模板 + 用户选择 → 组装器 → 存储 JSON**。
采集任务的验收不是「请求长什么样」的快照，而是「为什么长这样」的组装规则：

1. **预制层**：节点/面板/菜单模板来源（udc_* preset 表 / attribute.json / 前端 chunk schema 枚举），插槽结构与默认值
2. **用户选择层**：面板每字段接受什么输入（枚举/实体引用/表达式）
3. **组装层（核心产出）**：前端如何把选择填进模板生成 POST body——每个字段能被「插槽 + 来源 + 填充规则」完整解释

闭环验证靠四落点互证：同一份配置有四个可验证落点——①前端请求 body（trace 抓取）②MySQL udc_* 行（getcol3 直读）③Redis Hash `{env}:Metadata:{Type}:{appName}`（180h TTL）④OSS JSON `udc@<实体全名>.json`（发布产物）。设计态写只落 MySQL（发布前 ③④ 查不到是预期不是 bug）；①② 对上 = CROSS-VERIFIED；发布后再对上 ③④ = 全链路。

快照类产出（只存请求 body 不沉淀插槽映射）不满足切片验收；引用工具：skill `udc-trace-to-api`。

## 7. 本机模型路由（角色级）

| 角色 | 主模型 | 兜底 |
|---|---|---|
| main | seeyon/glm-5.3-flash | api/gpt-6-luna |
| implementer | d1/deepseek-v4.1-flash | d1/deepseek-v4.1-flash（同模型重跑） |
| auditor | d1/deepseek-v4.1-flash | d1/deepseek-v4.1-flash（同模型重跑） |

路由是**角色级**，不是全局级：`run_turn()` 里按 `if role == "main"` 分叉，不要把三个角色写成同一对 provider/model。

教训一：**渠道可用性是会变的，任何历史结论都必须当场重测再采信。**
skill 里曾写「seeyon/glm-5.3-flash 认证已失效、彻底退出主模型」，复测发现它已恢复可用——
照旧结论直接排除它是一个渠道，就会在用户明确指定它时先反驳一轮。
正确顺序：先 `probe` 主渠道与兜底各一次（看到真实回字且 RC=0），把结果报出来，再改配置。
反过来同理：单次 smoke 成功也不证明该渠道能当主模型——见教训二。

教训二：**判断渠道可用性不能靠单次测试，要看 fallback_triggered 计数**——高频兜底 = 主渠道实质不可用，应立即换掉主渠道，而不是让重试机制硬扛。清零计数无意义，看 `from=<provider>` 字段：只有 `from=api` 的 fallback 才是 api 渠道真故障。

教训三：改路由要同时核三处，缺一处就等于没改：
1. `agent_worker.py` 的 `run_turn()` 角色分叉
2. `HERMES_CONFIG` 指向的共享 config `custom_providers` 里 provider 是否存在
3. 该 provider 的 `models:` 映射里**模型名是否已声明**——漏声明会报 unknown model。只测 provider 存在不够，新加的模型要在两棵配置树（主树 `<HERMES_HOME>\config.yaml` 与 `hermes-shared-config/config.yaml`）都补齐。

教训四：**改完必须重启 worker 才生效**。worker 是长期驻留的 python 进程，启动时把脚本读进内存；改文件对已跑进程零影响，`fallback_triggered` 仍按旧路由继续刷。验证顺序固定为：先直连 smoke 两条路由（主模型 + 兜底各一条，看到真实回字且 RC=0 才算通），再重启 worker。

正确的 smoke 命令形状（参数必须在子命令之前，`chat` 子命令不接收这些 flag；也没有 `--no-tools`）：

```bash
HERMES_HOME=<HERMES_HOME> \
HERMES_CONFIG="<COLLAB_ROOT>/三Agent协作工具/hermes-shared-config/config.yaml" \
<HERMES_HOME>/hermes-agent/venv/Scripts/python.exe -m hermes_cli.main \
  --provider api -m gpt-6-luna -z "只回复两个字：可用" --yolo
```

smoke 通过只证明 provider/model 组合可用，**不证明运行中的 worker 已加载新路由**——两件事必须分开报。

教训五：Windows 下 worker 结构是 `cmd.exe /d /k title <role> watcher && python agent_worker.py --role ...` 父壳 + python 子进程。清点进程要按 `--role` 与 session 后缀分组计数，正常是每组每角色 1 个；杀进程必须 `taskkill /PID <父cmd> /T /F` 清整棵树，单杀 python 会被父壳重启。

教训六：**启动方式决定用户能否看到消息**。用 `creationflags=DETACHED_PROCESS` + `stdout=DEVNULL` 拉起时进程照跑、日志照写，但 12 个窗口全不可见，用户会直接反馈「我咋看不到消息」。正确做法：为每个 (组, 角色) 生成一个 `.cmd`（`title` + `cd /d` + `python agent_worker.py ...` + 退出时 `pause`），用 `subprocess.Popen(["cmd.exe", "/c", bat], creationflags=CREATE_NEW_CONSOLE)` 拉起，每个角色一个独立可见控制台，崩溃后窗口停住可读。`.cmd` 内容必须按 **GBK** 编码写盘（路径含中文），否则 cmd 解析乱码。验证窗口真实性用 `user32.EnumWindows` + `IsWindowVisible` + `GetWindowTextW` 抓标题，别只数进程。

教训七：启动器脚本要按 tag 精确选目录。`agent-collaboration/` 下大量历史 session，其中存在同名重复目录（如 `session-20261017-093815-60e4b4f5` 与 `session-20261017-093815-093815-60e4b4f5`），无 `collaboration.json` 的那个是空壳。选择条件必须是 `os.path.isdir(p) and os.path.exists(p/'collaboration.json')`，否则会把 worker 指向空壳、日志永不增长。

## 8. 运行中集群的健康判定与进度汇报

### 8.1 卡死判定用三元组，不要只看 worker.log 的 mtime

三元组 =（log 静默秒数，该角色私 inbox 待处理数，进程 pid 是否存活）。判定表：

| 静默 | 私 inbox 待处理 | 判定 |
|---|---|---|
| <120s | 任意 | WORKING |
| ≥120s | 0 | IDLE（正常） |
| ≥120s | >0 | STALLED? 需查 |

角色收完单、发完消息后主动停手等 HANDOFF 是设计行为，log 不再增长**不是故障**。把静默当卡死会导致反复误重启，反而打断正常运行的一轮。

真正的堵点信号只有一条：pending>0 且静默持续超过 5 分钟。此时看该角色 `worker.log` 尾部停在哪种形态——停在 `正在准备 terminal` / `compacting context` 是真在跑；停在 `恢复此会话 … exit_code=0` 是这一轮已退出、消息没人捡。

现成脚本：`scripts/worker_health.py`（`python worker_health.py [BASE]`），直接跑，不要手写探测。

### 8.2 汇报完成度读主控文档，不要扫 inbox

inbox 只反映最近几分钟的往返，不代表累计完成度。`main/ROUTE.md` 是 main 自己维护的路由快照，含「当前阶段 / 唯一活动动作」「完成标准」「已收口」「待办」，是该组进度的权威来源；再配合 `TASK-GOAL.md` 第四节的域状态表得到全貌。

ROUTE 被 4KB 纪律瘦身过：头部可能残留旧状态，尾部会指向存档文件或 `MAIN-CONTROL.md`；以 mtime 最新且段落自洽的那份为准。有些组的 main 每轮另写 `main/ROUND-<UTC时间戳>Z.md`，此时最新 ROUND 比 ROUTE 更准。

### 8.3 完成度按四态分组回答

用户问「每个任务完成得怎么样」时，按组给四段，不要按时间线复述：

1. **已闭环** — 带 commit 短号 + 证据等级（PASS/LIVE/STATIC/VACUUM）
2. **明确问题** — 分「能力问题」与「外部阻塞」（平台缺陷/配额/单账号 SSO 互踢/需人工授权），阻塞项必须写清需要什么输入
3. **进行中** — 当前唯一切片 + 预计产出
4. **明确缺口** — TASK-GOAL 里一直没打勾的验收项，单独列出

最后给一句总体判断（哪组最实、哪组卡在哪），不要均匀分配篇幅，也不要给时间线流水账。

### 8.5 进度汇报：进程在线 ≠ 进度，日志更新 ≠ 进度

用户判定进度不看「12 个 worker 都在线」「日志刚更新」这类活动指标。**验收口径固定为**：

```
哪一个具体对象已经正确
在哪个页面能看到
哪个真实操作已经跑通
哪些错误配置还在
谁负责把自己留下的问题闭环
```

四条交付物缺一条就说「尚不可测」：测试入口 / 操作步骤 / 预期结果 / 实测结论。

两种被明确否决的汇报形态：

```
✗ 「四组都在正常推进」     ← 实际 A 阻塞 90 分钟、其余在收尾旧报告
✗ 「在线、日志已更新」     ← 只证明进程活着，不证明任何业务结果
```

正确写法是先分四态（已闭环 / 明确问题 / 进行中 / 明确缺口），再对每组写
「今天新增了哪个可用功能、在哪个页面可见」。做不到就直说没交付，不要用活动量填空。

### 8.6 取证手段不能被当成主任务

三种自证空转，出现即停：

```
为了凑报告字节数（如 4096B）反复删改压字
为行号、登记格式、文档计数开多轮审计
同一事实由多个人重复取证
```

审计只拦两类问题：**业务结果不正确**、**操作越过安全边界**。其它文字问题一次记下、
不阻塞交付。同理，局部阻塞不能扩大成整组停工：
单点卡住就先推进不依赖它的独立任务，并明确报告缺哪一步输入。

### 8.4 凭据读取要收口成固定命令

prompt 里不要把 `.env` 路径丢给 sub-agent 让它自己解析——它会在同一轮里反复 `read_file` 同一文件十几遍、偶发撞 180s 工具超时，把预算烧在取凭据而不是业务上。给一个固定入口（`python env.py <env> mysql` 这类现成脚本），sub-agent 只调一次。

## 9. 角色报告字节纪律（按 92% 起写，不要贴边）

实现者报告有硬上限（如 4096 B）。**按上限的 92%（约 3800）起草，留 250–300 B 给评审补丁**，不要写到贴边。

贴边写的代价是连乘的：评审给 N 条修正 → 每条都是等值替换 → 任何一处字数变化都要重排全文才能压回上限 → 一轮修改烧掉十几轮往返，而且每压一次都有丢内容的风险。留出余量后，同一批修正一轮落完。

压字不是删语义：优先合并同类项、删重复的路径前缀、把长代码块换成关键行摘录，最后才考虑删论述。

**改完必须用断言核，不要重读全文**：把每条修正写成一次 grep 计数，一次调用验证全部：
```bash
wc -c REPORT.md && grep -c '^```' REPORT.md   # 字节 + 围栏配对（偶数）
for k in "L1936" "CallDataFlowActivity L50" "无 dataFlowId" "28 节点"; do
  printf "%-28s %s\n" "$k" "$(grep -c "$k" REPORT.md)"
done
```
围栏数是奇数就说明有一处代码块没闭合（常见的压字副作用），比通读快且不漏。

## 10. 否定结论的分级写法

「没找到」和「不存在」是两个等级，不能混写：
- **STATIC 否定**：给出可复现的搜索分母 + 命中 0（解了 N 个 jar / M 个 class / K 条调用行，命中 0）。读者能复算才算证据。
- **UNVERIFIED**：搜索范围之外（如实现类只在运行时 bean 表里、定义在仓库外的依赖里）。必须写明「为什么出界」，否则下一位会当成没查。
- **推断**：单独一行，不与 STATIC 合并。

一条否定结论只要缺分母，就等于自述。反之，把边界写清楚（「定义不在仓库任一 jar 内」）比含糊的「找不到」有价值得多——它把搜索空间永久性截断，下一位不用重走。

## 参考原文
- <HERMES_HOME>/cache/scratch/sp-src/skills/subagent-driven-development/SKILL.md
- <HERMES_HOME>/cache/scratch/sp-src/skills/verification-before-completion/SKILL.md
