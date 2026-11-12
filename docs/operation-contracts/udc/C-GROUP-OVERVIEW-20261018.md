# C 组三域交付物总览（2026-10-18 14:16）

> 用途：供后续会话 / 接手人一页看清「三域各自交了什么、证据强度到哪、还缺什么」。
> 纪律：**本表只写仓内可复算的事实**；每个数字附复算命令；不写『已验证通过』类断言。

## 一、锁点（全部 `git rev-parse` 可核）

| 域 | 交付物 | commit | 时刻 | 规模 | sha256[:16] |
|---|---|---|---|---|---|
| 栏目 | `docs/operation-contracts/udc/column/write-chain.contract.md` | `8aa2178` | 10-18 12:02:29 | 1,420 行 / 90,475 B | `07a20233db2eaf68` |
| 栏目 | `docs/operation-contracts/udc/column/SELF-CHECK-references-20261018.md` | `8aa2178` | 10-18 12:02:29 | 388 行 / 25,227 B | — |
| 栏目 | `docs/operation-contracts/udc/column/enums.md` | `9d510a8` | 10-18 00:58:44 | 213 行 / 16,330 B | — |
| 栏目 | `docs/operation-contracts/udc/column/README.md` | `42d157f` | 10-18 02:45:22 | 116 行 / 8,165 B | — |
| 设置 | `docs/operation-contracts/udc/setting/publish-chain.runbook.md` | `b2e0892` | 10-18 14:15:37 | 458 行 / 30,913 B | `69561e7c7fa5419b` |
| 角色 | `docs/operation-contracts/udc/role/write-chain.contract.md` | `b117979` | 10-18 14:11:38 | 707 行 / 38,369 B | `317e45806efbf0f7` |

复算：
```
for f in column/write-chain.contract.md setting/publish-chain.runbook.md role/write-chain.contract.md; do
  git log -1 --format="%h %ci" -- docs/operation-contracts/udc/$f
  wc -lc docs/operation-contracts/udc/$f
  sha256sum docs/operation-contracts/udc/$f | cut -c1-16
done
```

## 二、三域交付内容与证据强度

### 栏目域（column）—— 6 op 读写链契约
- **覆盖**：`udcPortletSelectByAppIdAppGet`（读）、create / update / delete / page-save / page-submit 等 6 op。
- **证据分级**：按 `README.md` §三 四级（LIVE / STATIC / DISCREPANCY / INFERRED），**无来源字段一律不写**。
- **LIVE 支撑**：`docs/audit/column-discovery/raw/` 7 件原始请求/响应，GraphQL 信封有原文。
- **S4 删分组**：已写入契约（§3 删栏目/删分组），含三个关键约束：
  ① 同一 op 服务两种对象（传栏目 id / 传分组 id），**前端无法从请求体区分**，只能靠 DB 行 `type` 判；
  ② 必须先删栏目再删分组（`deleteById(GROUP)` 会级联删子栏目）；
  ③ 删分组确认文案已记录（用于 LIVE 判定）。
- **未闭环**：S4 的 LIVE 执行仍在等 SSO 窗口（BOOT_1006 持续）。**契约是 STATIC 侧完备，LIVE 侧缺口。**

### 设置域（setting）—— 发布链 runbook
- **覆盖 23 端点** = 5 条执行步骤端点（步骤 1–6，步骤 6 上线仅登记）+ 18 条步骤 7 登记备查。
- **23 可仓内复算**（三件齐备，D39 正例）：
  ```
  cd docs/audit/artifacts/udc-web-5.3.517-contracts
  cat DeployController.javap.txt DeploymentController.javap.txt SandboxController.javap.txt 
    | grep -cE 'annotation[.](Post|Get)Mapping[(]'          # → 23
  ```
  > ### ★ 命令写法（推荐零反斜杠）—— 三方 33 分钟分歧的真正解
  >
  > **结论先行：改用不含反斜杠的等价写法，三条通道全部正确，不需要记任何矩阵。**
  > ```
  > 括号：  \(  →  [(]        （等价，字符类里括号无特殊含义）
  > 点号：  \.  →  [.]        （字符类里点为字面点；不要用裸 . —— 它匹配任意字符）
  > 词尾：  \b  →  -w 标志     （grep -w 整词匹配，实测与 \b 等价）
  > ```
  > **四条命令的零反斜杠形态（照抄即得，三条通道全 rc=0）**：
  > ```
  > grep -cE 'annotation[.](Post|Get)Mapping[(]' UdcRoleController.javap.txt            # → 15
  > grep -cE 'annotation[.]RequestMapping[(]' UdcRoleController.javap.txt               # → 1
  > cat DeployController.javap.txt DeploymentController.javap.txt \
  >     SandboxController.javap.txt | grep -cE 'annotation[.](Post|Get)Mapping[(]'       # → 23
  > grep -owE 'udcCtpUserRole[A-Za-z]*(Post|Get)' write-chain.contract.md | sort -u | wc -l   # → 12
  > ```
  > `-w` 与 `\b` 等价性实测：合成三行输入 `udcCtpUserRoleCreatePostInputBody` /
  > `udcCtpUserRoleGet` / `udcCtpUserRoleXxxPostInputBody` → 两种写法均输出 1 行 `udcCtpUserRoleGet`。
  >
  > ### 为什么必须避开反斜杠（实测矩阵，三条通道各不同）
  > ```
  > 每点反斜杠数 | bash <file>        | bash -c（终端粘贴） | PowerShell
  > 1 个        | rc=0 → 15   ✓      | rc=0 → 15          | rc=2  ✗
  > 2 个        | rc=2        ✗      | rc=0 → 15          | rc=0 → 15 ✓
  > 3 个        | rc=1 → 0（静默）    | rc=2               | rc=0 → 15
  > 4 个        | rc=2        ✗      | rc=2               | rc=2  ✗
  > 零反斜杠      | rc=0 → 15   ✓      | rc=0 → 15   ✓      | rc=0 → 15 ✓  ★
  > ```
  > ⇒ **没有任何一个反斜杠数能在三条通道同时正确；零反斜杠是唯一交集。**
  > 这也解释了今天三方各执一词：**三份表各自在自己那条通道下都对。**
  >
  > **点号处为什么用 `[.]` 而不是裸 `.`**：裸 `.` 在 ERE 里匹配任意字符，
  > 本文件恰好只有 `annotation.`(64) 与 `annotation/`(13) 两种，而 `/` 那条后面接的是 `Autowired`
  > 不是 `Post|GetMapping`，**所以裸 `.` 在这里碰巧不误匹配** —— 是巧合，不是稳健。
  > 合成反例（`annotation.PostMapping` / `annotationXPostMapping` / `annotation/PostMapping` 三行）：
  > ```
  > grep -cE 'annotation.(Post|Get)Mapping[(]'     → 3 行   ❌ 裸点把 X 和 / 都算进来
  > grep -cE 'annotation[.](Post|Get)Mapping[(]'   → 1 行   ✓ [.] 只匹配字面点
  > ```
  > ⇒ **`[.]` 同样零反斜杠，且不依赖数据巧合。** 本文件四条命令已统一用 `[.]`。
  >
  > **可复现验证（不信上面的表，自己复制两条命令即可）—— implementer 15:17 实测并留档**
  > ```
  > 实测目录：docs/audit/artifacts/udc-user-5.3.517-contracts
  > bash 入口：       grep -cE 'annotation\.(Post|Get)Mapping\(' UdcRoleController.javap.txt   → 15  rc=0  ✓
  > PowerShell 入口： 同一条命令原样复制                                                          → rc=2  Unmatched
  > ```
  > PowerShell 三种投递方式结果一致（均 rc=2），**已排除"投递层差异"这个解释**：
  > `-EncodedCommand`（base64 UTF-16LE）/ `-File .ps1`（二进制写入）/ `-Command`（argv 直传）。
  > ⇒ **是 PowerShell 传给 MSYS grep 的 argv 与 bash 不同，不是某一种投递方式的问题。**
  > ⇒ **这正是"零反斜杠"的必要性来源：含反斜杠的命令无法同时服务两个入口。**
  >
  > **通道差异的机理（探针脚本实测，非推断）**：用替身脚本打印它收到的反斜杠数：
  > ```
  > 源文本 2 bs → bash <file> 收到 2 / bash -c 收到 2 / PowerShell 收到 0
  > 源文本 4 bs → bash <file> 收到 4 / bash -c 收到 2 / PowerShell 收到 2
  > 源文本 6 bs → bash <file> 收到 6 / bash -c 收到 4 / PowerShell 收到 2
  > 源文本 8 bs → bash <file> 收到 8 / bash -c 收到 4 / PowerShell 收到 4
  > ```
  > ⇒ **`bash <file>` 完全保真；`bash -c` 从 4 bs 起折半；PowerShell 还多折一层。**
  >
  > **分离变量（哪个反斜杠才是致命的）**：
  > ```
  > 报错只来自括号处：括号 0 个→rc=2 / 1 个→15 / 2 个→rc=2 / 3 个→rc=1 得 0
  > 点号处 0~1 个都得 15（javap 里 annotation 后只跟 . 或 /，测不出差别）；2 个以上 rc=1
  > ```
  >
  > **报告纪律**：写「n 个反斜杠」或「rc=?」时，必须同时写明 ①每点还是整行 ②哪条通道。
  > 两个不写，结论不可用 —— 这是今天 33 分钟、五人次分歧的全部原因。

  > **自证技术（必须）**：二进制写 `.sh` → `od -An -tx1 <f> | grep -c '^5c$'` 确认字节数 → `bash <f>`。
  > **禁止内联自证**：内联投递（`bash -c` / agent 命令通道）会多抹一层，同一字符串能得出相反结论 ——
  > 今天三人各自据此得出过三个互相矛盾的"实测"，全部是通道假象。
  > **禁止看 repr**：Python `repr` 的 `\\` 是「一个反斜杠」的转义写法，易读成两个；只认 `od`。

  互证分解：按 Controller 12+6+5；按文档用途 5 执行 + 18 登记。两套不相交路径同得 23。
- **P0 发布链 LIVE 全链**：**双重阻塞** —— SSO `BOOT_1006`（被踢）+ `XzhExp950795` NFE。已升级 `NEEDS_HUMAN`，等人工三选一（补授权 / 改走另一 app / 降级验收）。
- **N-3 已修**（b2e0892）：裸短名需两条命令分列（`PostMapping(`=18 / `GetMapping(`=5），原写「一条命令得 18+5」是表述合错。

### 角色域（role）—— 写链契约（15 端点）
- **覆盖**：`UdcRoleController` 全部 **15** 个注解方法 / 端点，基路径 `udc/ctp-user/role`。
  入口分布（三套口径，都可仓内复算，**不要混用**）：
  ```
  grep -cE 'annotation[.](Post|Get)Mapping[(]' UdcRoleController.javap.txt        # → 15  端点数
  sed -n '/# 4\. GraphQL op/,/^---$/p' write-chain.contract.md | grep -cE '^[|] `udc|^[|] （REST'   # → 13  有映射的端点数
  grep -owE 'udcCtpUserRole[A-Za-z]*(Post|Get)' write-chain.contract.md | sort -u | wc -l     # → 12  唯一 GraphQL op 名
  ```
  | 口径 | 数 | 含义 | 随什么变 |
  |---|---|---|---|
  | 端点数 | **15** | javap 注解方法总数 | 只在 Controller 增删方法时变 |
  | 有映射的端点 | **13** | §4 表 13 行 = 12 个 GraphQL op + 1 个 REST 直连（#15 `create-system-admin`） | **§4 表增删行就变**；15 与 12 不受影响 |
  | 唯一 GraphQL op 名 | **12** | bundle 里读到的 fieldType | 只在 bundle 增删 op 时变 |
  | 无映射 | **2** | #4 `delete-resource/app/{appId}`、#5 `delete-resource/{id}`（仅 REST，bundle 里无 op） | — |
  **校验：12 + 1 + 2 = 15** ✓

  > ⚠️ **③ 的口径边界（不写清就会算错）**：`12` 依赖「op 名以 `Post`/`Get` 结尾」这个约束。
  > 用宽松模式 `grep -oE 'udcCtpUserRole[A-Za-z]+'` 去重会得 **13**，多出的一个是
  > `udcCtpUserRoleCreatePostInputBody` —— 它是 GraphQL 的 **InputBody 类型名，不是 op**。
  > 所以必须用 `(Post|Get)` 收尾的模式才得 12。**宽模式 13 ≠ 有映射端点 13，两个 13 不是同一个数。**
  >
  > ⚠️ **③ 的命令必须带 `-w`（右边界）**：`(Post|Get)` 后不加 `-w`，`…CreatePostInputBody` 这类类名会被截成
  > `…CreatePost` —— 一个「幻影 op」。本文件恰好只有 `CreatePostInputBody` 一个，截断后与真实 op 同名、
  > 去重不虚增，**所以现在得 12 是巧合，不是稳健**。合成反例可验：
  > `echo 'udcCtpUserRoleXxxPostInputBody' | grep -oE 'udcCtpUserRole[A-Za-z]*(Post|Get)'` → 输出 `udcCtpUserRoleXxxPost`（错）；
  > 加 `-w` 后 → 无输出（rc=1，对）。**边界说明不能替代稳健写法。**
- **等级分布**：**✅ LIVE 恰 4**（#7 / #8 / #11 / #13）+ **⚠️ 部分 LIVE 2**（#12 / #15）+ **9 STATIC**。
- **仓内复算**（只用 `javap.txt`）：
  ```
  cd docs/audit/artifacts/udc-user-5.3.517-contracts
  grep -cE 'annotation[.](Post|Get)Mapping[(]'  UdcRoleController.javap.txt   # → 15
  grep -cE 'annotation[.]RequestMapping[(]'     UdcRoleController.javap.txt   # → 1
  grep -oE 'value=[[]"[^"]*"[]]' UdcRoleController.javap.txt | wc -l          # → 16
  ```
- **三级证据链**（§14.1，勿读成「能验/不能验」两句对立）：
  | 层级 | 在仓库里 | 能证什么 | 不能证什么 |
  |---|---|---|---|
  | javap.txt | ✅ 在 | 15 / 1 / 16 计数 | 这份 javap 是否真来自该 class |
  | class | ❌ 不在（`.gitignore:41 *.class`） | 自备后本地可证 javap↔class（须 JDK 21） | 仓内证不了；也证不了 class↔jar |
  | 官方 jar | ❌ 不在 | 自备后可溯源 | 任何人都证不了 |
- **JDK 前置**：**必须 JDK 21**。JDK 8 下 `annotation[.](Post|Get)Mapping(` 命中 **0**（不展开注解类名），会让人误判整份契约是伪造的。
- **高危/不可逆项**：`#15 create-system-admin` **进角色页必然被动触发**（无法靠不点按钮避免）；`#13 func-auth` 无 `setResourceType` ⇒ 写入行恒 `resource_type=0`，**既有非 0 行会被退化**，退化面须执行前 `COUNT(rr.resource_type <> u.type) = 0` 现查。

## 三、可复现性强度对比（三域不均匀，不可混谈）

| 域 | 数字复算 | 产物在仓 | 备注 |
|---|---|---|---|
| 设置 | ✅ 23（仓内） | ✅ javap 在仓 | 三件齐备 |
| 角色 | ✅ 15/1/16（仓内） | ✅ javap 在仓 / ❌ class 不在 | 三级链已在契约内声明 |
| 栏目 | 部分（依赖 audit raw 7 件） | ✅ raw 在仓 | 证据是 LIVE 原文，非 javap 计数 |

## 四、已知残留（不阻交付，但必须让接手人知道）

| # | 域 | 内容 | 定级 |
|---|---|---|---|
| 1 | 设置 | P0 发布链 LIVE 全链双重阻塞（SSO BOOT_1006 + XzhExp950795 NFE） | **NEEDS_HUMAN** |
| 2 | 栏目 | S4 删分组 LIVE 未执行（等 SSO 窗口） | BLOCKED-EXTERNAL |
| 3 | 角色 | `#15` 首次创建分支（app 尚无 SystemAdmin）UNVERIFIED；已知会真建一行 | 已声明于 §0.4 |
| 4 | 角色 | `#13` 退化面须执行前 COUNT 现查，无现成数字 | 已声明于 #13 行 |
| 5 | 设置 | N-3 已修；同文件无其他账 | CLOSED |

## 五、下一步依赖（谁能动、等什么）

- **栏目 S4**：等 SSO 窗口。窗口判定 = 连续 2 次 `/service` 不返回 `BOOT_1006`（间隔 ≥30s）。**任何人不得为它循环重试。**
- **设置 P0**：等人工三选一（补授权 / 换 app / 降级验收）。在拿到答复前**不进发布页、不建 app**。
- **角色域**：已闭环。若后续要升 `#15`/`#12` 为 ✅，须补「首次创建」分支的真实证据（须在无 SystemAdmin 的 app 上做，风险自负）。

## 六、纪律清单（本组今日沉淀，接手人必读）

| # | 纪律 | 一句话 |
|---|---|---|
| D26 | 改方 + 引方双义务 | 改了要回扫全文；引了要先 grep 同文件有没有撤回 |
| D27 | 真值须二次独立交叉 | 「一方跑两遍」≠「两方各跑」 |
| D28 | 关单锁 commit 不锁文件 | 关单后任何改动使关单失效，须增量重核；关单条件含工作区干净 |
| D29 | 两行制 / 三行制汇报 | 内容面 / 交付态 / 可复现性分开判 |
| D30 | 「数字对」≠「依据对」 | 四形态分类；补条 1b（前置条件缺失）/ 补条 2（等级核对双向跑）/ 补条 3（升格须有据并写来源） |
| D31 | ctrl_v.txt 入仓范围 | 只收语义等价的副本；不因「看起来一样」放宽 |
| D32 | 每封必贴 `git log -1` | 防版本交叉 |
| D33 | 路径/数字/时刻/等级须贴命令输出 | 写进交付物的每个断言都要可回溯到一次实跑 |
| D34 | 报 diff 必须标口径 | 总输出行 vs 变更行（`^[<>]`）—— 不标口径的 diff 数不可复核 |
| D35 | 同日同命令双向错误：352/230/2408 | 同一数字被两种口径各读一次错；这是 D34 的实例，也是 D37 形态 5 的实例 |
| D36 | 验证输出不进仓库目录 | 一律 `$TMPDIR`，完事 `git status --untracked-files=all` |
| D37 | 形态 5：测量污染被测对象 | 比对前核行尾 + 编码；「两数刚好等于某两量之和/差」先疑伪影 |
| D38 | 局部验证 ≠ 全局断言 | 问：我验的是这个对象还是邻居？这个性质还是前一步？ |
| D39 | REPRO-DEGRADED 三维之一 | 落点是**写作规范**（三件齐备 + 条件/敏感性/边界），返工只是兜底 |
| D40 | 关单前独立全文回扫 | 补：落点是「换检查对象」，不是「多扫一遍」 |
| D41 | 提交前扫 inbox 全部未读 | 补：按 `ls -t inbox/` 取前 20 条，与「本批合并 N 条」对账 |
| D42 | 两类订正不可混用 | 结论被撤回→保留+标注；表述合错→直接改对 |
| D43 | 回扫两级 | 改时扫同节（主路径）+ 关单前全文（兜底） |
| D44 | 形态 7：下了指令就当它被执行 | 指令 ≠ 执行；须看对方的回执或产物，不能凭「我说了」推定「他做了」 |
| D45 | ROUTE 每域必须有固定状态行 | 不能只在该域是主线时才写 —— 否则非主线域的状态会静默腐烂 |
| D46 | REVIEW_REQUEST 须标核验类别 | 修错类（原错清除+无新错）/ 新建类（锁点+口径）/ 索引类（数字可追源或附命令） |
| D47 | 四态互不等价 | 编辑动作 → 工作区态 → commit 态 → 运行态；越往上越细越不可复核，四者不能互相否证。描述过程须贴实测输出，无快照须明说「仅凭记忆」 |
| D48 | 域级全审 = 事件触发 | 只在即将执行 LIVE 时对该域做全审；无未决争议的域不做常规巡检 |
| D49 | 结论正确 ≠ 推导可复用 | 错误推导得到正确结论更危险——没人会复查「答对了」的结论 |
| D50 | 同一裁定发多人须改人称 | 共享文档用第三人称（角色名），单发消息才用第二人称；否则等于拿对 A 说的话评判 B。收到含第二人称的指正时，先核①是否同时发给别人 ②「你」在这个语境指向谁；核不到就不认领，先回问 |
| D51 | 引用他人言论必须回查原文 | 任何「某人说了 X」都必须回查该人原文，不采信第三方转述。判据：转述与原文冲突时，一律以原文为准 |
| D52 | 行尾/编码判定禁用 grep | MSYS/WSL 的 grep 是文本模式，读入时把 CRLF 归一成 LF ⇒ `\r` 恒不命中（假阴性）。须用 ①Python 字节计数 ②`od -An -tx1` 数 `^0d$` ③`file`，三种取二互证 |
| D53 | **能消除转义层，就别去数转义层** | 一条命令若在不同 shell 需不同写法，是它写错了，不是读者该记矩阵。`\(`→`[(]`、`\.`→`.`、`\b`→`-w`、`\`+竖线→「字符类包管道」，三通道全通（`\.`→`.` 一条已被 D55 修正为 `[.]`：裸点匹配任意字符，本文件是「碰巧对」）|
| D54 | **探针法优先于结果法** | 判断"某层改写了什么"时，用打印它收到什么的替身脚本，而非跑真命令看结果 —— 后者无法区分"命令错"与"输入被改" |
| D55 | **能消除的转义一律消除** | `\X` 转义先问能否用 `[X]` 或 grep 标志替代：`\(`→`[(]`、`\.`→`[.]`、`\`+竖线→「字符类包管道」、`\b`→`-w`。能 ⇒ 用它（零反斜杠+可移植+更稳健）；不能（`\d` `\s` `\w`）⇒ 保留但写明通道。裸 `.` 在本文件「碰巧对」，合成反例可证伪 |

> D26–D52 全 27 条的完整正文见 `main/DECISIONS.md`。**本表只是索引，不是全文** ——
> 若本表与 `DECISIONS.md` 冲突，以 `DECISIONS.md` 为准（D46 索引类：本表数字只有编号与一句话，无独立新事实）。
> 同步校验：`comm -3 <(grep -oE '^\| D[0-9]+' 本文件 | grep -oE 'D[0-9]+' | sort -u) <(grep -oE '^##+ D[0-9]+' main/DECISIONS.md | grep -oE 'D[0-9]+' | sort -u)` 应为空。
