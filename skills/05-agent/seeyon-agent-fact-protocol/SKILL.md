---
name: seeyon-agent-fact-protocol
description: "Use when landing facts or evidence into seeyon-agent repo."
version: 1.0.0
author: 小爪 🐾
license: MIT
platforms: [windows, macos, linux]
tags: [seeyon, seeyon-agent, evidence-discipline, repo-layout, reuse]
metadata:
  hermes:
    tags: [seeyon, seeyon-agent, evidence-discipline, repo-layout, reuse]
    related_skills: [seeyon-udc-setting, seeyon-udc-module-landing]
---

# Seeyon Agent · 事实／证据／skill 分层与沉淀规则

## When to Use

- 要把某域的结论 / 证据 / 脚本落进 `seeyon-agent`（任何域，不只 UDC）
- 拿不准某个值该进 `components/` 还是 `tools/`（规则 vs 测试值）
- 要新建“可复用脚本”，但不确定该放 `tools/core/` 还是 `_attic_pending/one-off/`
- 要清理仓库、分“可复用架构”与“两个收容桶”
- 要移动/重排 `tools/`、`docs/` 目录（先查测试里的路径字面量）
- 要把 Hermes skill 放进 `seeyon-agent/skills/`（先过 PII 与凭据闸门，别全量镜像）
- 发现 Hermes 侧 skill 散在多个平行目录、或与仓库副本已经漂移
- 发现事实格写了但检索不到 / 事实格与契约互相矛盾 / 实测与事实不符

不适用于：具体模块的接口细节（看 `seeyon-udc-setting` 等域 skill）。

## 域定位

本 skill 不是某个子模块的操作手册，而是**往 `seeyon-agent` 仓库写东西时的通用规矩**。
任何域（udc / org / user / bpm / menu / rule …）推进完一轮，都按这里落位。
具体模块的接口细节看该模块自己的 skill（如 `seeyon-udc-setting`）。

配套文件：`docs/KNOWLEDGE-LANDING-RULES.md`（仓内标准流程）、
`docs/REPO-LAYOUT.md`（目录边界）、`core/role/EVIDENCE-DISCIPLINE.md`（分级纪律）。

## 一、五层各归各位（不要互相复制）

```
事实    core/facts/<域>/<子模块>/create.md        平台行为结论、约束、错误字典、等级
证据    docs/audit/artifacts/<来源>/<版本>/        反编译产物、抓包 JSON、DB 导出
契约    docs/operation-contracts/<域>/               operation 清单 + 必填槽位 + 错误码
实现    components/<域>/                          构造器 / 校验器 / 模型（纯逻辑，无测试值）
脚本    tools/core/<域>/                           可复用操作脚本（参数化，无硬编码环境）
skill   Hermes skills/seeyon/<域>/                  使用方法、坑、正确姿势
```

**单向引用，不重复内容**：

```
skill  → 指向事实格 + 契约 + 实现位置（不内联代码、不抄错误字典全文）
事实格 → 指向证据文件相对路径 + 实现文件（不抄请求体全文，那是契约的事）
契约   → 指向实现 + 证据（不叙述"我当时怎么试的"）
```

硬规则：**同一句话不许在两处都写**。发现重复就留一个权威处，另一处改指针。

## 二、测试值只进 tools，绝不进 components

用户原话：「我们测试的事实，可以说做一些规则和限制，而不是全部放进来」。

| 内容 | 去处 | 判据 |
|---|---|---|
| **规则/约束**（字段名、必填槽位、枚举值域、错误码、类型→控件映射） | `components/` | 换应用照样成立 |
| **测试值**（appId、字段集 id、探针字段名、验收 caption） | `tools/` 脚本的 `--xxx` 参数 | 换应用就得换 |
| **一次跑出来的 id** | 事实格 R-E8 或 tools 的 docstring | 只是那次的结果 |

反例（本仓实测）：

```
❌ tools/core/setting/ 16 个脚本硬编码 appId，只 3 个有 --app-id
   → 换个应用全部报废，等于一次性脚本占了可复用目录
✅ appId 从 --app-id 必填参数取；无参时 argparse 报错退出
```

```
❌ components/udc/xxx_constraints.py 里写死 "zxjProbeField" 作为默认值
✅ 默认值一律空/None，测试值由调用方（tools）传
```

**components 里允许出现的硬编码**：平台常量（表名、operation 名、枚举值域、
控件名）——这些是平台事实，不是测试值。

自检：

```bash
grep -rn "8704025620829192834\|zxj\|验收\|探针" components/ --include=*.py | grep -v '#'
# 只应命中 docstring/注释里的 LIVE 记录，不应命中赋值语句
```

## 三、证据必须可复现：R-E8 写三样

事实格的 `R-E8 Evidence` 段，**每条证据必须写全三样**，缺一不算完成：

```
① 路径    docs/audit/artifacts/<来源>/<版本>/xxx.json     ← 相对仓根
② 复现    命令或步骤（哪个脚本 / 页面怎么点 / 哪条 SQL）
③ 校验    你怎么知道它对（DB 回读哪张表哪列 / 接口回读哪个字段）
```

反例（本仓现状，必须改）：

```
❌ 「枚举：id -1052013552430069963，ctp_enum.category_id 正确指向分组」
   → 三个月后没人知道这个 id 哪来的、怎么重跑
✅ 「枚举 id=-1052013552430069963；证据 docs/audit/artifacts/udc-web-5.3.517/...json；
   复现 tools/core/setting/enum_seed.py --app-id X；校验 SELECT category_id FROM ctp_enum WHERE id=...」
```

**证据文件本身可以含客户标识**（可复核性前提），但事实格/契约/skill 里的引用
只能是路径，不能把客户名抄进结论区。

## 四、用户口述的六条硬规矩（跨会话有效）

### 1. 后台 JSON 优先，GraphQL 为主

```
前台接口基本都是 GraphQL。后台能通就不必前台一个个点。
以后台和 JSON 为先，实在不行再走反编译看 jar。
```

排查顺序：**GraphQL/REST 直发 → 反编译 Controller 读 DTO → 页面抓包兜底**。
不是反过来。

### 2. 抓接口用 rea，rea 挂了换 CDP

```
rea capture_browser_scenario        前端点击后抓
rea 在某页面 timeout                 改用 performance.getEntriesByType('resource')
                                     + 页面内 fetch 拦截
```

⚠ 字段集面板的 `+` 号（表达式入口）必须 CDP 真实鼠标事件，JS `.click()` 无效，
rea 在该页 timeout。这类记进对应域 skill。

### 3. 任何数据类型／类别都要试

```
「任何的数据类型的格式，和类别你都得试一下，你看看他是怎么组装的」
```

一个写面报「打通」前，三件事缺一不可：

```
① 必填槽位   空 body 逐轮收敛，拿到错误码字典
② 类型矩阵   平台类型清单里的每个值各提交一次，逐个 DB 回读
③ 组装形态   抓平台自己发的 body，逐字段对齐
```

类型清单**必须从平台元数据接口取**（如 `udcDataTypeDataTypesByAppIdAppGet`），
不许手抄。矩阵允许分批跑，但结论必须是一张完整矩阵表；没跑到的格子写 UNVERIFIED。

### 4. 换一个来源复验

```
「你现在的对象和选项集都换一个，别用选的那个，比如都选 bpm 引擎下的」
```

同一类对象只在**一个上下文**里验通不算通。至少换一个来源（本应用 → BPM 引擎 →
组织模型）复验，防止把「这个上下文的特例」当成通用规则。

### 5. 沉淀必须进仓库，不能只活在 skill 或对话里

```
「记住你写的这些东西必须都进 seeyon agent，保证后续我只要一个需求你能里面实现功能」
```

判断标准：**下一个会话只靠仓库能不能复现**。只写进 Hermes skill = 没沉淀。
四类资产（实现 + 事实 + 契约 + skill）必须同时存在且索引可查。

### 6. 汇报分清等级，成功码不算成功

```
LIVE PASS                  跑通 + 独立回读核实
LIVE                       跑通但回读维度有限
VERIFIED_STATIC_BYTECODE   静态证据坐实，未跑
UNVERIFIED                 真实不可用/未验证（写明缺口）
VACUUM                     真实不存在（完备负证据）
```

`BOOT_0000` 不是成功判据。缺 id 时平台仍回 `BOOT_0000` 但 `content=0`。
判据永远是**回读目标表/目标字段**。

## 五、可复用脚本 vs 一次性脚本：目录必须分开

用户原话：「后续可复用的脚本和现在的一次性脚本要分开，要分开对应的目录」

```
tools/core/<域>/     可复用：参数化（--app-id / --set-id 必填）、有校验器、长期维护
                    被 tests/ 或 docs/ 引用 → 必须留

_attic_pending/one-off/   一次性：探针、排查片段、临时 dump
                    验收完就地归档；整目录可一次删掉，不影响任何引用
```

⚠ 一次性脚本**不要单独留一个 `tools/one-off/`**——它最终整个进 `_attic_pending/one-off/`，
两个物理位置会漂移（新脚本不知道往哪写）。只在 pending 桶里有一处。

**判定方法（不是靠印象）**：

```bash
# 被 tests/docs/components 引用的 → 可复用
for f in tools/core/*.py; do b=$(basename $f .py);
  grep -rq "$b" tests/ docs/ components/ core/ --include=*.py --include=*.md && echo "REF   $b" || echo "ONEOFF $b"
done
```

完整判据（自引用干扰、体积维度、git 跟踪面、失败分类、台账格式）见
`references/repo-triage-by-reference-count.md`。

**ONEOFF 的三种处置**：

```
① 已被事实格/契约引用 → 提升进 tools/core/，参数化 + 补 docstring
② 只是一次性排查       → 移进 _attic_pending/one-off/（保持目录可整体删）
③ 连 one-off 都不算     → 直接删（git 有历史，能捞回来）
```

**铁律**：`tools/core/` 里不许出现硬编码 appId；`_attic_pending/one-off/` 里的脚本
不许被 tests/docs 引用（一旦被引用就说明它其实该提升）。

## 六、目录边界：可复用架构 vs 两个收容桶

用户明确要求的是**两个桶，不是一个**：

```
_attic_pending/   待删除，但现在不删 —— UDC 全部完工前冻结
                  里面是「含已取证事实、以后可能捞出来复用」的东西
                  处理方式是逐条抽离成正式资产，不是整目录搬走就完事

_attic_trash/     立马清理 —— 随时可 rm -rf，不用再考虑
                  只收：构建产物、可无成本重建的运行输出、零信息量调试残留
```

**为什么必须分两个**：证据区里躺着大量反编译产物与抓包 JSON，它们**是后续做功能的原料**。
把「暂时没消费者」和「纯死物」混在一个桶里，清理时就没法判断哪些能安心删——
要么全留（越来越乱），要么全删（把原料删了）。

```
_long-term（架构）
  core/facts/        事实格 + INDEX 登记
  core/role/         角色与纪律声明
  components/        实现（纯逻辑）
  providers/         只读连接器（mysql/redis/k8s/nacos/cdp）
  config/            环境与版本声明（凭据只在仓外）
  docs/operation-contracts/  契约
  docs/capability/   能力索引
  docs/ledger/       收口台账 + 续接摘要（只追加）
  docs/audit/artifacts/      证据（按来源+版本，长期保留）
  tools/core/        可复用脚本
  tests/             回归
```

两个桶的 README 必须写清「这里放什么 / 与另一个桶的区别 / 现在能不能删 / 已在此的内容台账」，
否则下一个会话分不清。台账每条要有：内容、体积、零引用验证方式、状态、去向。

### 分层执行顺序（每步可停，每步后跑全量测试）

```
1. 量体积       du -sh */ 先看谁大，别凭印象
2. 查引用       对每个待移目录/文件 grep 整个仓（tests/ docs/ components/ core/）
3. 建两个桶     README 先写，台账先建
4. 只移零引用   有引用的原地不动；引用数不明就先查再动
5. 跑全量       pytest tests -q --tb=line   ← 这一步会抓出你以为没引用的东西
6. 补 .gitignore 两个桶都加，避免污染仓库
```

⚠ **不要在同一轮既分层又删东西**。分层是移动 + 改引用，删除是另一件事；
混在一起出错时分不清是移动错了还是删错了。

**抽离流程（把 pending 里的东西变成正式资产）**：

```
1. 要做一个功能 → 先在 pending 桶 grep 相关关键词 / 文件名
2. 找到可复用的证据或逻辑
3. 抽离：规则→components/  事实→core/facts/（R-E8 写证据路径）
        可复用脚本→tools/core/<域>/（参数化）
4. 台账状态改 EXTRACTED，注明去向
5. 全部 EXTRACTED 或确认无价值 → 该目录才可删
```

## 七、目录重排：三类路径依赖，漏一类就一片红

**重排前先把待收的改动 commit 成干净基线。** 目录重排会一次改几十个文件，
若工作区还带着未提交的零散修改，事后分不清哪个 diff 是重排造成的、哪个是之前的。
先按主题拆成独立 commit（事实订正 / 测试修复 / 分层 / 重排 各一个），
再动目录——出问题能 `git checkout <dir>` 回到重排前，归因也是一眼的事。

**移动脚本/目录名不是纯文件操作。** 一个仓里同时存在三种路径依赖，必须分别处理：

```bash
# ① tests/ 里的路径字面量（最容易想到）
grep -rn '"tools" */ *"core"\|tools/core/\|tools/audit/' tests/ --include=*.py

# ② 脚本内部的 parents[N] 深度（下移一层就失效，最容易漏）
grep -rn 'parents\[' tools/ --include=*.py

# ③ 脚本引用兄弟脚本的拼接路径（字符串形式，前两项都盖不到）
grep -rn 'core" */ *"\|core/" *+' tools/ --include=*.py
```

### ① tests 路径字面量

典型形态（一个仓里就有十几处）：

```python
TOOL = ROOT / "tools" / "core" / "enumerate_xxx.py"    ← pathlib 逐段拼，
                                                         简单字符串替换盖不到
```

处置顺序：先列清单 → 新目录定下来再改 → 移完跑全量 → 按失败清单逐个改。
改完必须用**逐段形式**再扫一遍。

### ② parents[N] 深度

脚本从 `tools/core/x.py` 移到 `tools/core/<域>/x.py`，`parents[2]` 算出的「仓库根」
就变成了 `<repo>/tools`，于是它去 `tools/docs/...` 找证据 → `FileNotFoundError`。

**别手改 N。** 仓内已有按标志物判定的修正器（标志物 = `docs/audit`、`components`、
`tests` 三者同时存在即仓库根）：

```bash
grep -rn 'fix_parents_depth' tools/          # 先找仓里有没有现成的
python tools/core/audit/fix_parents_depth_repo.py
# 输出形如：xx/enumerate_xxx.py  parents[2]→parents[3]
```

没有现成的就按同一原理写一个：**按「上溯到哪一层能看到仓库标志物」判定，
不按目录层数硬编码。**

⚠ 这类脚本会把 `_attic_pending/` 里的脚本也一起改 —— 那里面的深度也变了，
一并改掉是对的（将来捞回来还能跑），不要以为改到了桶里就是越界。

### ③ 兄弟脚本拼接路径

```python
ENUMERATOR = ROOT / "tools" / "core" / "enumerate_class_http_mappings.py"   # ❌ 移完就断
```

它不在 tests 里、也不是 parents[N]，前两条 grep 全都不报。
**移动后必须把每个被移动脚本的模块级常量路径行过一遍**，或用上面第三条 grep 兜。

### ★ 批量改文件必须字节写，不要 write_text

Windows 上 `Path.write_text()` 会把 **CRLF 改写成 LF**，于是 git 里每个文件都变成
「整文件删除 + 整文件新增」，真实改动被行尾噪音完全掩盖 —— 十几个文件、几千行假 diff。

```python
# ❌ 行尾被改写，diff 爆炸
tp.write_text(new, encoding="utf-8")

# ✅ 保留原行尾
raw = tp.read_bytes()
text = raw.decode("utf-8")
out = do_replace(text)
if out != text:
    tp.write_bytes(out.encode("utf-8"))
```

**判定是否踩了坑**：改完立刻 `git diff --numstat`。
若行数接近文件总行数（而不是只有改的那几行），就是行尾被改了 —— **回退重做**，
不要在这堆假 diff 上继续改。

### 同理：测试不许依赖仓库根目录的运行产物

`http.json` / `runtime.json` / `matrix.actual.json` 这类文件往往在 `.gitignore` 里
（= 本机跑过才有，新克隆/清缓存后不存在）。测试若直接读仓根那份，就是**必然的环境依赖失败**。

```python
# ❌ 依赖仓根那份，clean 环境下 FileNotFoundError
result = _run("...", "--http", str(ROOT / "http.json"))

# ✅ 测试自建到 tmp_path
http = tmp_path / "http.json"
http.write_text(json.dumps({...}), encoding="utf-8")
result = _run("...", "--http", str(http))
```

判定法：测试里出现 `ROOT / "<某个在 .gitignore 里的文件名>"` 就是缺陷，不看它当时能不能跑。

## 八、skill 镜像：Hermes 权威，仓库只放被断言的

### 权威只有一个：Hermes

```
权威   <HERMES_HOME>/skills/seeyon/<层>/<skill>/     ← 只编辑这里
镜像   <repo>/skills/<层>/<skill>/                       ← 仅当 tests 断言需要
```

两边各存一份必然漂移。实测过 `seeyon-udc-module-landing`：Hermes 51KB / 仓库 13KB，
仓库版停在旧版本、缺 37KB 内容，而两边都在被读。**同步只能是单向 Hermes→仓库，
禁止在仓库侧编辑**（下次同步直接覆盖，改动无声消失）。

### ★ 绝不能全量镜像：仓库有 PII 闸门

`tests/test_deidentification.py::test_conclusion_docs_have_no_pii` 会扫**全仓**
`.md/.py/.yaml/.yml`（只放过 `/artifacts/`、`/live-evidence/` 证据区与两个收容区），
命中任一类模式即失败。检测的是五类：

```
工号        形如 <字母前缀><3 位数字>
真实人名    项目负责人姓名
客户应用名  datamigration<非保留段数字>
客户实例名  znxmglpt<6 位以上数字>
客户组织    客户域名关键词 / 中文全称
```

（具体正则见测试文件本身 —— 本文不抄字面量，否则本文件自己就会命中。）

Hermes 侧的 skill 是**工作手册**，本来就该写真实环境（测试环境域名、客户组织、工号、人名）——
它们没有错。错的是把工作手册当交付物塞进仓库。全量镜像一次实测：19 个文件、
5 类模式全中，闸门直接红。

⇒ **镜像是白名单，不是全量复制。** 判定：

```
可镜像   纯平台机制 / 方法论 / 协作协议，无客户名、无实例域名、无人名工号
不可镜像  带 .env / kubeconfig / *.pem / 客户实例名 / 真实人名的操作手册
```

带客户信息的 skill 留在 Hermes 用，**不要为了入库去删掉它们的环境细节**——
删了下次就不知道该连哪个环境。

### 凭据红线：镜像脚本必须自带 deny list

即使只做白名单镜像，也要在脚本层硬拦（防止有人改判据时漏掉）：

```python
DENY_NAMES  = {".env", ".env.local", "kubeconfig-*", "shared-credentials",
               "*credential*.json", "config.yaml"}
DENY_SUFFIX = {".pem", ".p12", ".pfx", ".key", ".jks", ".crt", ".cer",
               ".sqlite", ".db"}
```

判据要作用在**相对路径的每一段**（不只是文件后缀）：`07-office-collaboration/config.yaml`
这种共用配置也可能是凭据载体。镜像完必须验一次：

```bash
find skills -name ".env" -o -name "*.pem" -o -name "kubeconfig*" \
     -o -name "*credential*" -o -name "config.yaml"      # 必须是空输出
```

### 漂移检测：`--check` 进 CI

镜像脚本要能只比对不写，退出码非零表示漂移：

```
同 / 补 / 更 / 删  四类计数 + 逐条路径
--check 有差异 → rc=1
```

仓内实现：`tools/core/_meta/sync_skills_from_hermes.py --check`。

### 回滚坏镜像：不要 `rm -rf`

镜像判错要撤回时：

```bash
git checkout <dir>/                        # 恢复被覆盖的已跟踪文件
git clean -fd <dir>/                       # 只删未跟踪的新目录，git 有记录的可捞
# 或最保险：mv 进 _attic_pending/mirrored-skills/
```

`rm -rf` 属破坏性动作，会被拦、也可能是不可逆的第一步。**回滚也要走"先移到桶里"**，
与分层同一原则。

### skill 目录本身也要单一化

Hermes 侧曾同时存在 `skills/seeyon/`、`skills/seeyon-agent/`、`skills/seeyon-05-agent/`、
`skills/v8/` 四个平行目录，同一域的 skill 分散在多处，`skill_view(name)` 靠 name 解析
所以能用，但人找起来乱、合并时容易漏。

规矩：**致远相关的一律在 `skills/seeyon/<层>/` 下，不新建平行根目录**。
合并时注意两点：

```
① 目标目录已存在同名 → 不覆盖，先 diff 再决定（可能是更新的版本）
② 合并后 name 必须仍唯一：find ... -name SKILL.md -exec dirname {} \;
   | xargs -n1 basename | sort | uniq -d      ← 空输出才算通过
```

移动完同步更新 `skills/README.md` 的分层清单（**注意：不是 `skills/seeyon/README.md`，该路径从未存在**；`skills/` 下只有 `skills/README.md` 与 6 个数字分层目录 + 若干独立 skill 目录），否则下一个会话按 README 找会落空。

## 九、落位自检清单

一轮推进收尾，逐项核对：

```
□ 实现进 components/<域>/，无测试值硬编码
□ 事实格 core/facts/<域>/<子模块>/create.md，R-E8 三样齐全（路径/复现/校验）
□ 事实格已在 core/facts/INDEX.md 登记（没登记 = 检索不到 = 没写）
□ 契约 docs/operation-contracts/ + registry.py 登记
□ 脚本进 tools/core/<域>/，参数化
□ skill 指向上面四处，不内联代码
□ 落位测试 tests/udc/test_<域>_<子模块>_asset_layout.py
□ 能力自检 python tools/core/capability_report.py --check 无新增缺口
□ pytest tests -q 全绿（记录实测数，不引用历史数）
□ 结论区脱敏；证据区保留原文
```

## 十、常见坑

| 坑 | 后果 | 规避 |
|---|---|---|
| 事实格只写 id 不写证据路径 | 下个会话无法复现，等于没沉淀 | R-E8 三样齐全 |
| 事实格写了但 INDEX 没登记 | 检索不到 | 落位测试断言 INDEX 命中 |
| 测试值写进 components | 换个应用全废 | 只进 tools 参数 |
| tools/core 里硬编码 appId | 可复用目录被一次性脚本占满 | 参数必填，无参报错 |
| 一次性脚本散在 tools/core | 清理时不知道哪些能删 | 一律进 pending/one-off |
| 只建一个收容桶 | 暂时无用但含事实的东西被当垃圾删 | 必分 pending / trash 两桶 |
| 清理时直接 rm | 无法回退，引用断裂 | 先移 pending，UDC 完工后再删 |
| 分层同轮又删东西 | 出错时分不清移动错还是删错 | 分层与删除分两轮 |
| 目录重排不改测试路径断言 | 一片红，且误以为是逻辑回归 | 先 grep 路径字面量，逐段形式再扫 |
| 目录重排只改了 tests 里的路径 | 脚本内部 `parents[N]` / 兄弟脚本拼接路径仍在旧深度 → FileNotFoundError | 三类依赖都扫（见 §七），有仓内修正器就用 |
| 用 `write_text` 批量改文件 | Windows 下 CRLF→LF，整文件变成删除+新增，真改动被淹没 | 字节读写；改完 `git diff --numstat` 验行数 |
| 把 `docs/audit` 引用当活引用 | 只被历史证据文档点名的死脚本占用可复用目录 | 判据分三档：tests/契约/能力索引用才是活引用 |
| 测试读仓根运行产物 | clean 环境必失败（文件在 .gitignore） | 测试自建到 tmp_path |
| 两个 skill 目录同内容 | 改一处另一处漂移（实测差 37KB 仍在被读） | 只留一个权威（Hermes），仓库侧禁止编辑 |
| 把 Hermes 工作 skill 全量镜像进仓库 | 撞 `test_deidentification` PII 闸门，19 文件全红 | 白名单镜像：只放无客户名/实例名/人名工号的 |
| 为过闸门删掉 skill 里的环境细节 | 下次不知道该连哪个环境 | 带客户信息的 skill 留 Hermes，不入库 |
| 镜像脚本不拦凭据 | `.env`/`kubeconfig`/`*.pem` 入库 | deny list 作用在相对路径每一段 + 镜像后 find 验空 |
| 合并 skill 目录时覆盖同名 | 丢掉更新的那份 | 先 diff 再决定；合并后查 name 唯一性 |
| 回滚坏镜像用 `rm -rf` | 破坏性、被拦、可能不可逆 | `git checkout` + `git clean -fd`，或 mv 进桶 |
| 事实格重复契约内容 | 两处必然互相矛盾 | 单向引用 |
| 引用历史测试数当契约 | 计数随时间漂移 | 一律实测，不写死 |
