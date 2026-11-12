# P1 三块结构补齐（版本边界 / chunk 形态归类 / 端点↔页面元素）

> 依据：main HANDOFF #S3-CALIBER-FIX §四 授权「P1 三块结构补齐（纯 STATIC，零会话依赖）」
> 体例参照：`docs/audit/udc-semantics/SETTINGS-TABS-CALLCHAIN.md` §0 / §1.1
> 撰写：implementer · 2026-10-18 11:52–11:56 GMT+8（commit 5da3045）
> **本文件证据等级：STATIC**（javap 实跑 + bundle 原文提取 + sha256 锚定）
> **零 `/service`、零页面、零写、零登录动作，不依赖会话**

---

## 0. 为什么单独成文而不是直接改 P1

P1（`P1-role-frontend-call-chain.md`）的**结论全部保留**，本文件只补它缺的三块结构性内容。
理由：P1 是已交付产物，直接大改会让「谁在什么时候改了什么」失锚；单独立文 + 在 P1 顶部加指针，
两者都可独立复跑。**若日后合并，以本文件的实测数据为准，P1 原文结论不推翻。**

---

## 1. 版本边界（对齐 SETTINGS-TABS §0 体例）

### 1.0 ⚠️ 先纠正我自己写的一句错话：javap 的 SHA-256 **不能**「自证来源」

我原版曾主张：javap 的 `SHA-256 checksum` 与 sha256sum 一致即可**证明产物与 class 的对应关系**（原文见 `git show 6ff3eb8:` 该文件）。
**前半句对，后半句错。** 我按 main HANDOFF 要求**自己重做了一遍篡改实验**（不自采信 auditor 转述，
JDK 21.0.10，`$TMPDIR/javap_test`，未进仓库）：

```
自建 T.class（391 B）
① 原文件    javap=bc33b913…c79ae6   sha256sum=bc33b913…c79ae6   相等
② 篡改+1B   javap=3ee49470…e7a946   sha256sum=3ee49470…e7a946   仍相等   ← 关键
           （`printf 'Z' >> T.class` 追加 1 字节）
③ 还原      sha256sum=bc33b913…c79ae6   回到原值
```
⇒ 与我们自己的域无关，纯粹证明这个判据本身**恒真**。auditor 的原实验（`d9a729b0…` → `4f45cc1a…`）
结论一致，我的独立复现给出不同哈希但同一结论。

**为什么「仍相等」是关键**：javap 打印的是**它刚读到的这份 class 字节的即时 SHA-256**，
与 `sha256sum` **同源、同算法、算同一份字节** ⇒ 两者比对**恒为真**，不携带任何来源信息。
换句话说：

> 它能证明的只有「**我算的和 javap 算的是同一份文件**」；
> 它**不能**证明「这份文件来自 `udc-user-5.3.517.jar`」。

**正确表述（本节起以此为准）**：
- 「javap 结果可信」只能止于「**这堆字节的解包语义可信**」这一层；
- **jar 级 = UNVERIFIED（来源链真断）** —— jar 本体已丢，我和 auditor 双方都补不了
  （auditor `find /d/work /d/software -iname 'udc-user*.jar'` = 0 命中；本仓库 `alljars` 目录为空）。

> **这条为什么必须写死**：它会被后来者当作「能自证的模板」复用到其他域 ——
> 一旦复用，就会把「字节级一致」误记成「来源已验证」，污染整条证据链。
> 判据质量 ≠ 证据等级，这里同理：**哈希一致 ≠ 来源可信。**

SETTINGS-TABS §0 钉死了 5 个面（后端镜像 / javap artifact / 前端壳 / 远端入口 / 静态存储）。
角色域 P1 原来只有 jar 路径，缺其余 4 面。逐项实测结果如下 —— **有 2 项拿不到，如实标 BLOCKED，不编**：

| 面 | 值 | 证据 | 等级 |
|---|---|---|---|
| **后端 class（字节级锚）** | `UdcRoleController.class`，**SHA-256 = `885fba64…b098db`**，major version 52（Java 8） | `javap -p -v` 的 `SHA-256 checksum` 行与 `sha256sum` 实测值一致 —— **注意：这是恒真，不含来源信息**（见下 §1.0） | ✅ STATIC（**仅字节级**） |
| 后端 jar 名 | `udc-user-5.3.517.jar` | P1 §0 声明；**jar 本体已不在本机**（见下 BLOCKED-1） | ⚠️ 仅文档自述；**jar 级 = UNVERIFIED（来源链断，双方都补不了：auditor find 0 命中 / 仓库 alljars 空）** |
| javap 产物 | `role_static_r2/ctrl_v.txt` **77,922 B / sha16 `98b7ce94`** | 本地实测 size+sha256 | ✅ STATIC |
| class 解包树 | `role_static_r2/classes/com/seeyon/udc/user/{controller,dto}/` | 本地存在，`UdcRoleController.class` + `UdcRoleDto.class` 均在 | ✅ STATIC（**可重跑 javap**） |
| **前端远端入口** | `/ctp-user/remoteEntry.js`，**15,328 B / sha16 `a69f9b9b`** | 本地 `web/remoteEntry.js` | ✅ STATIC |
| 前端壳版本 | **未取得** | `remoteEntry.js` 内无 `seeyonGlobalVersion` / 任何 `x.y.z` 版本字面量（grep 0 命中） | ❌ **BLOCKED-2** |
| 静态存储 | **未取得**（角色域未抓 OSS key） | 本次未做 HTTP 请求（冻结令 + 零会话依赖约束） | ❌ **BLOCKED-2** |
| 后端镜像 tag | **未取得** | 需 pod 查询；本切片冻结令下不做集群操作 | ❌ **BLOCKED-2** |

### BLOCKED-1｜jar 本体丢失（影响**来源链**，不影响「可重跑」）

```
P1 §0 声明路径：  scratch/djars/udc-user-5.3.517.jar        → 目录已不存在
实际找到：        scratch/alljars/udc-user-5.3.517/         → 目录存在但为空（0 个 jar）
```

**能保留的（对）**：**可重跑性未丢** —— class 文件本体在，
`javap -p -v` 能重新跑出同一份结果（版本边界表「class 解包树 ✅ STATIC（可重跑 javap）」）。
这是「能力仍在」，与「来源已验证」是两件事。

**必须删掉的（错，2026-10-18 12:21 订正；12:28 二次收紧写法）**：本段原有两条错误结论，**已删除**。
此处不复述原句全文，只记「错了什么、为什么错」：

| 已删除的错误结论（摘要） | 为什么错 |
|---|---|
| 认为 javap 的 checksum 能与 sha256sum 互证，从而**跳过来源** | 见 §1.0：两者同源同算法算同一份字节，互证恒真，**不含来源信息** |
| 认为 jar 丢失**不影响**「一致性」的证明 | `一致性` 只能到**字节级**，到不了**来源级**；jar 丢 = 来源链断 |

> **订正说明（写作方式也改了，这是本轮真正的收获）**：这两条错结论我最初是**整句抄在引用块里**做「订正留痕」，
> 结果任何 `grep` 都会命中，被 main 与 auditor 各判一次「仍存活」—— 而它们当时已经是引用而非断言。
> **教训：订正留痕不要保留原句全文。**
> 只写「错了什么」的摘要，原因是：**基于 grep 的核查无法区分「断言」与「引用旧错」**，
> 保留原句会反复触发误判，白白消耗三方轮次。
> （代价是失去逐字可对照性 —— 但原文仍在 git 历史里，需要对照时 `git show 6ff3eb8:<file>` 即可。）

**上述两条错误结论与本节 §1.0 直接冲突，且本身不成立。** 理由（§1.0 已详述）：
javap 打印的是它读到的字节的即时 SHA-256，与 `sha256sum` 同源同算法 ⇒ **互证恒真，不含任何来源信息**。
所以：

| 能证明 | 不能证明 |
|---|---|
| 我算的和 javap 算的是**同一份文件** | 这份文件**来自 `udc-user-5.3.517.jar`** |
| 这份 class 的**解包语义**可信 | 这份 class 与 test2 部署镜像**同源** |

⇒ **正确结论**：
- **jar 丢失影响的是「来源链」** —— 无法证明这份 class 来自 `udc-user-5.3.517.jar`（**jar 级 = UNVERIFIED**）；
- **「可重跑 javap」这一能力仍在**（不影响复现实验结果）；
- **不能**主张该比对能证明来源、也不能主张 jar 可省、更不能主张一致性已被证明 —— **这三处措辞已删除**。

不建议为此重建 jar（要重新拉包，成本大于收益；且 auditor 与我都 find 0 命中，双方都补不了）。

### BLOCKED-2｜三面缺证据，且**不能靠猜补**

前端壳版本 / 静态存储 / 镜像 tag 三者都需一次 HTTP 或集群查询才能取证。
本轮是「纯 STATIC、零会话依赖」切片，**按约束不做**。
**风险提示**：缺这三面 ⇒ 无法证明「本地 bundle 抓取时刻 = 当前线上」。
但 `remoteEntry.js` 有 sha256 锚 + chunk 名带 contenthash（`7d23367b`/`cef9f043` 等），
**contenthash 本身就是版本标识** —— 若线上 chunk 名变了，说明版本变了。这算部分替代。

---

## 2. chunk 按调用形态归类（对齐 SETTINGS-TABS §1.1 的 A/A'/B/C/D 五形态）

### 2.1 实测：角色域只用到 3 种形态，不是 5 种

对 `role_static_r2/web/*.js` 全量做构造器计数（`grep -o` 逐文件统计）：

| chunk | size | `queryLoader` | `udcQueryLoader` | `udcMutationLoader` | `udcApolloQuery` | `AU.post` |
|---|---|---|---|---|---|---|
| `bussiness.8e39da83.js` | 335,756 B | 15 | 2 | **0** | 10 | 31 |
| `module1622.js` | 3,994 B | 1 | 2 | **0** | 10 | 1 |
| `commons.2d409314.js` | 417,654 B | 3 | 0 | 0 | 0 | 0 |
| `src_pages_role-authority_index_tsx.cef9f043.js` | 58,457 B | 0 | 0 | 0 | 0 | 1 |
| `src_pages_role-permission_index_tsx.7d23367b.js` | 16,319 B | 0 | 0 | 0 | 0 | 0 |
| `src_pages_role-permission_entry_tsx.ebba5ac6.js` | 16,574 B | 0 | 0 | 0 | 0 | 0 |
| `src_pages_system-role_index_tsx.4d3aa5ed.js` | 2,256 B | 0 | 0 | 0 | 0 | 0 |
| `remoteEntry.js` | 15,328 B | 0 | 0 | 0 | 0 | 0 |

**关键结论 1：`udcMutationLoader` 在角色域出现 0 次。**
SETTINGS-TABS 里有 A'（mutation loader）形态，**角色域不用**。
⇒ 角色域的写操作全部走 `udcApolloQuery("mutation …")`。这是域间差异，写进契约可省后来人的排查。

**关键结论 2：页面组件 chunk 里 `udcApolloQuery` 也是 0** ——
调用全部沉在 `module1622.js`（op 定义层）和 `bussiness`（redux thunk 层），
页面 chunk 只拿 thunk 引用 ⇒ **页面 ↔ 端点之间隔着两层，不能从页面 chunk 直接推端点。**

### 2.2 逐 op 形态认定（module1622.js 原文提取，非推断）

| op | GraphQL 类型 | 构造器 | `paramsKey` | 判据（原文片段） |
|---|---|---|---|---|
| `udcCtpUserRoleCreatePost` | mutation | `udcApolloQuery` | `body` | `udcApolloQuery("mutation … ($body: …InputBody) {…}",{body:e})` |
| `udcCtpUserRoleUpdatePost` | mutation | `udcApolloQuery` | `body` | 同上 |
| `udcCtpUserRoleDeletePost` | mutation | `udcApolloQuery` | `body` | `{body:{id:e}}` |
| `udcCtpUserRoleSelectListPost` | mutation | `udcApolloQuery` | `body` | `{body:e}` |
| `udcCtpUserRoleRoleAuthPost` | mutation | `udcApolloQuery` | `body` | `{body:{roleId:e}}` |
| `udcCtpUserRoleFuncAuthPost` | mutation | `udcApolloQuery` | `body` | `{body:e}` |
| `udcCtpUserRoleRoleAuthAllPost` | mutation | `udcApolloQuery` | `body` | `{body:{appId:e,code:t}}` |
| `udcCtpUserRoleFuncAuthAllPost` | mutation | `udcApolloQuery` | `body` | `{body:e}`（List） |
| `udcCtpUserRoleAppResourceGet` | **query** | `udcApolloQuery` | `query` | `udcApolloQuery("query …(query: $query){…}",{query:e})` |
| `udcCtpUserRoleAppResourceTypeGet` | **query** | `udcApolloQuery` | **无（零入参）** | `udcApolloQuery("query udcCtpUserRoleAppResourceTypeGet {…}",{})` |
| `udcCtpUserRoleSelectPageResourceGet` | **query** | **`udcQueryLoader`** | `query` | `udcQueryLoader.load({fieldType:…,paramsType:…InputQuery,paramsKey:"query",params:e,…})` |
| `udcCtpUserRoleGet` | **query** | **`udcQueryLoader`** | **`path`** | `paramsType:…InputPath,paramsKey:"path",params:{id:e}` |
| `/ctp-user/role/create-system-admin` | — | **`AU.post`（REST 直连）** | — | 唯一 REST，不经 GraphQL |

### 2.3 ⚠️ 必须纠正的一个「按名字猜形态」的坑

**`udcCtpUserRoleSelectPageResourceGet` 名字带 `Get`，但形态与 `AppResourceGet` 不同：**

```
AppResourceGet           → udcApolloQuery("query …")      paramsKey=query
SelectPageResourceGet    → udcQueryLoader.load({…})       paramsKey=query     ← 不同构造器
Get（by id）              → udcQueryLoader.load({…})       paramsKey=path      ← 不同 paramsKey
```

三者名字都像「GET」，实际是 **2 个构造器 × 2 个 paramsKey 的三种组合**。
⇒ **不许按 `Get`/`Post` 后缀推形态**，必须看构造器 + `paramsKey`。
这条是本轮实测最值钱的一条：`AppResourceGet` 我最初按 loader 推断，读原文发现是 `udcApolloQuery`，已纠正。

---

## 3. 端点 ↔ 页面元素映射（P1 原来完全没有这块）

P1 §4.2 只给出「op ↔ 后端端点」；缺「**用户在哪个页面点哪个东西** → 触发哪个 op」。
补法：三层追溯（页面 chunk 文案 → redux thunk 名 → module1622 op 名）。

### 3.1 三层追溯链（逐层有证据）

```
页面 UI 元素（chunk 里的中文文案 + 组件）
   ↓ 引 thunk
redux thunk（bussiness.8e39da83.js，模块 6994）
   ↓ 调 op
module1622.js op 名
   ↓ GraphQL fieldType 路由
UdcRoleController 端点（§2 编号）
```

### 3.2 映射表（端点 ↔ 页面元素）

| # | 端点 | 触发元素（chunk 实测文案） | 所在 chunk | redux thunk | 触发方式 |
|---|---|---|---|---|---|
| 7 | `select-list` | 角色列表首屏（**无按钮，页面加载即拉**） | `role-permission_index_tsx` | `fetchRoleList` | 自动 |
| 1 | `create` | 「**新建**」按钮 → 弹窗「角色名称/**请输入角色名称**」「角色编号/**请输入角色编号**」「默认授权给」「说明」→「**确定**」 | `role-permission_index_tsx` | `handleRoleInfo` | 点击 |
| 2 | `update` | 「**编辑**」（列表行操作列）→ 同弹窗 →「确定」 | `role-permission_index_tsx` | `handleRoleInfo` | 点击 |
| 3 | `delete` | 「**删除**」+ 确认文案「**确认删除此角色？**」 | `role-permission_index_tsx` | `handleDeleteRole` | 点击 |
| 11 | `role-auth` | 角色行 →「**权限**」/「**查看**」（Tab：菜单功能 / 移动功能权限） | `role-permission_index_tsx` | `fetchAuthByRoleId` | 点击 |
| 13 | `func-auth` | 勾选复选框后「**设置权限**」/「**确定**」 | `role-permission_index_tsx` | `handleFunctionAuthByRoleId` | 点击 |
| 8 | `app-resource` | 权限面板资源树数据源（**无按钮，随 Tab 加载**） | `role-permission_index_tsx` | `fetchAppResource` | Tab 切换 |
| 9 | `select/page-resource` | 页面功能控制资源（`{appId,code}`，随选中资源节点） | `role-permission_index_tsx` | `fetchPageControlResource` | 点选节点 |
| 10 | `app-resource-type` | 资源类型参数（**零入参**，随面板初始化） | `role-permission_index_tsx` | `fetchAppResourceType` | 自动 |
| 14 | `func-auth-all` | 「**设置权限**」的批量分支（List 入参） | `role-permission_index_tsx` | `FuncAuthAll` | 点击（批量） |
| 6 | `{id}` | **页面主路径不走**（P1 §4.2 已注明；列表用 `select-list`） | — | — | 未接 |
| 4 | `delete-resource/app/{appId}` | **页面无入口**（bundle 里无对应按钮） | — | — | **无 UI** |
| 5 | `delete-resource/{id}` | **页面无入口** | — | — | **无 UI** |
| 12 | `role-auth-all` | **有 UI 入口（自动触发）** —— 组件 `U` 的 `useEffect(()=>{l((0,N.ig)(u.vL))},[l])`，进页面即拉 | `role-permission_index_tsx` | `fetchAllRoleAuth`（另 `fetchRoleAuthByCode`） | **自动（读）** |
| 15 | `create-system-admin` | 「**查看人员**」/「系统角色管理」（`src_pages_system-role_index_tsx`）附近；**精确触发点未取证** | `system-role_index_tsx` | 未定位 | **未确证** |

### 3.3 这张表最直接的用途：定「能不能靠点页面取证」

| 类别 | 端点 | 含义 |
|---|---|---|
| **有 UI 入口**（**11 个**） | #1 #2 #3 #7 #8 #9 #10 #11 **#12** #13 #14 | **可以用页面取证**（需会话；#12 为自动触发，非点击） |
| **无 UI 入口**（2 个） | #4 #5 | 只能 REST 直调取证；**这是我在 P1-LIVE-GAP-MATRIX §4.2 建议「#4/#5 登记 DANGER-ZONE 不补 LIVE」的额外依据** |
| **入口未确证**（1 个） | #15 | 需要页面实测确认（`system-role_index_tsx` 只有 2,210 B，未见明显调用点） |
| **页面不接**（1 个） | #6 | 主路径不用，补 LIVE 价值低（与 GAP-MATRIX §4.3 一致） |

**计数校验（可加性）**：11（有 UI）+ 2（无 UI）+ 1（入口未确证）+ 1（页面不接）= **15** ✅

> **⚠️ 本表 2026-10-18 12:10 订正过两处**（auditor 复核 + 我自己回查）：
> ① 原文写「有 UI 入口（7 个）」但后面列了 10 个，自相矛盾；**7+3+1+1=12≠15，加不上端点总数**。
>    且同一文件 §4 写的是「10 有 UI」，两处打架。已按实数列出。
> ② 更重的一条：**#12 `role-auth-all` 原被判「页面无入口」，是错的**。
>    组件 `U` 的 `useEffect(()=>{l((0,N.ig)(u.vL))},[l])` 进页面就调它（自动触发、读操作）。
>    完整证据链见 `P1-FUNCAUTH-BRANCH-TRACE.md` §1.2（`ig` → thunk `fetchAllRoleAuth` → op `RoleAuthAllPost`）。
>    ⇒ #12 **有入口**，已从「无 UI 入口」移出，计数由 10 变 11。
>    **成因**：§3.2 那行（「bundle 无调用点」）写在 67cb7f9 追溯**之前**，追溯完成后我只在 §3.4 加了更正块，
>    **没有回改 §3.2/§3.3 的旧结论** —— 这是「新证据不回改旧结论」的典型脱节，比数字错严重。

### 3.3.1 #4 / #5 / #12 三个端点的取证判断（逐个给结论，不含糊）

| 端点 | 有无 UI 入口 | 该不该补 LIVE | 理由 |
|---|---|---|---|
| #4 `delete-resource/app/{appId}` | **无** | **不补** | 危险面最大（一次清空单应用全部角色授权），补证要主动制造该风险；信息增量已被 #13 `func-auth` 同表覆盖式语义覆盖 ⇒ **DANGER-ZONE，禁止无整表备份时调用** |
| #5 `delete-resource/{id}` | **无** | **不补** | 同上但影响面小一档；与 #4 同源，登记同一条 DANGER-ZONE |
| #12 `role-auth-all` | **有（自动触发，读）** | **不补**（**但理由完全不同**） | ① 它是**读**操作，无破坏风险，与 #4/#5 的「危险」性质不同；② **已有 P3 的 LIVE 佐证**（参数语义修正后：`code=2084600749018399891`→289 行、`code=9183843213439484192`→21 行），再补是重复取证；③ 补它只能拿到「进页面自动拉一次」，**无独立信息增量**。⇒ 不是「没入口所以补不了」，而是**「有入口、已有 LIVE、增量价值低」** |

> **口径纠正（auditor §四 也撤回了同一条旁证）**：我曾在 GAP-MATRIX 里暗示「#12 因页面不可达才只能手调，
> 所以易踩参数语义坑」。**前提错了** —— #12 页面可自动触发。
> P3 那次踩坑的真因是**参数语义**（`code` 是资源 code 非 appId），与可达性无关。已在 GAP-MATRIX 同步订正。

> **交叉验证**：`P1-LIVE-GAP-MATRIX.md` §4.2 建议 #4/#5「不补 LIVE、登记 DANGER-ZONE」，
> 本 §3.3 给出**独立于破坏面论证的第二条理由**：它们**在页面上根本没有入口**，
> 要取证就得手写 REST 调用 —— 风险与成本都高于收益。两条论证独立成立。

### 3.4 一个必须登记的边界

**`func-auth`(#13) 与 `func-auth-all`(#14) 在页面上共用「设置权限」入口**，
bundle 里两个 thunk 都存在（`handleFunctionAuthByRoleId` / `FuncAuthAll`），
但**页面在什么条件下走哪个，本轮未从 chunk 取证**（需读 thunk 分支逻辑或页面实测）。

**但既有 LIVE 结论不受此影响 —— 请求体是硬判据：**

```
POST /service/udc/graphql?udcCtpUserRoleFuncAuthPost      ← op 名 = #13
body: {roleId:"-4544711258376164024", roleCode:"ZZPROBE-ROLE-235451-C",
       resourceList:[{resourceId:"2710418858302391088",
                      resourceType:"MENU", action:"basic"}]}   ← 单条对象，长度 1
```

| 判据 | #13 `func-auth` | #14 `func-auth-all` |
|---|---|---|
| op 名 | `udcCtpUserRoleFuncAuthPost` | `udcCtpUserRoleFuncAuthAllPost` |
| body 形态 | **单条对象**（含 `roleId`/`roleCode`） | **`List<UdcRoleFuncPermissionDto>`** |

⇒ S5 那次实测命中 #13，**无歧义**（证据：`P3-role-write-chain.md` §11 请求原文）。
残留未取证项仅为「页面分支条件」，登记为 `UNVERIFIED-funcAuth页面分支` —— **不是 LIVE 结论的缺口**。

> **教训（自记）**：本轮我一度把「chunk 层没读到分支条件」写成「S5 的 LIVE 结论可疑」。
> 那是把**未取证当反证**，方向错了。正确顺序是：先查已有产物（P3 请求原文）能否闭合，
> 闭合了就只登记页面层残项；**不能因为读不懂前端分支，就质疑已经拿到的请求级证据。**

> **📌 2026-10-18 12:07 更新：本节那条「页面在什么条件下走哪个，本轮未从 chunk 取证」的担心已撤回。**
> 已做完调用点级追溯（`docs/audit/role/P1-FUNCAUTH-BRANCH-TRACE.md`），结论：
> **不是「一个入口两个分支」，而是「两个不同组件各有一个『确定』按钮」**：
> | 触发点 | 命中 |
> |---|---|
> | 「设置权限」弹窗（`title: 查看权限/设置权限`）的「确定」→ `(0,c.Pt)` | **#13** `func-auth`（单条，含 roleId） |
> | 功能权限总表（组件 `U`）的「确定」→ `(0,N.ic)` | **#14** `func-auth-all`（List 批量） |
> | 组件 `U` 的 `useEffect` → `(0,N.ig)` | #12 `role-auth-all`（**读**，非写） |
> 运行时最省事的区分判据：**成功后 toast 文案不同** ——「设置角色权限成功」（#13）vs「设置页面功能权限成功！」（#14）。
> ⇒ 原「点一次无法区分」不成立，S5 判定进一步加固（三条独立判据）。

---

## 4. 三块补齐后的状态

| 块 | 补齐前 | 补齐后 | 仍缺 |
|---|---|---|---|
| 版本边界 | 只有 jar 名 | 5 面中 2 面有**字节级**锚（class SHA-256 / 产物 sha16）；**jar 级 = UNVERIFIED（来源链断）**；3 面 BLOCKED 明确 | 前端壳版本 / 静态存储 / 镜像 tag / **jar 来源链** |
| chunk 形态归类 | 无 | 8 个 chunk 的构造器计数 + 12 个 op 的形态逐条认定 | `funcAuth`/`funcAuth-all` **页面分支条件**（请求级判据已有，见 §3.4） |
| 端点↔页面元素 | 无 | 15 端点全覆盖（**11 有 UI / 2 无 UI / 1 入口未确证 / 1 不接** = 15 ✅） | #15 精确触发点 |

### 4.1 给收口的三条判断

1. **「先结构后 LIVE」这个顺序是对的，价值在 #4/#5 上已经兑现**：
   §3.3 一建出来就发现 **#4/#5 根本没有 UI 入口**（只能 REST 手调）——
   如果按原计划先去补 LIVE，会白跑一趟。
   **但要注意反例**：同一张表最初把 #12 也判成「无入口」，事后证明是错的（它有 `useEffect` 自动触发）。
   ⇒ **「先结构」的价值是真的，但结构判断本身也会错，必须留回改机制**（本文件 §3.3 就因此订正了两次）。
   #12 不补 LIVE 的真实理由不是「没入口」，而是「有入口 + 已有 P3 LIVE + 无独立增量」，见 §3.3.1。
2. **#15 `create-system-admin` 不建议排期补 LIVE**：入口未确证 + 是权限提升写操作。
   若 main 要补，建议先做 **纯 STATIC 的 thunk 追溯**（读 `bussiness` chunk 找调用点），零风险。
3. **`funcAuth` 页面分支虽未取证，但不阻塞既有结论**（§3.4 已用请求体排除歧义）。
   若日后要补 #14 `func-auth-all` 的 LIVE，则必须先搞清页面分支，否则「点一次设置权限」验不清命中哪个。
   建议届时先做 STATIC 追溯（读 bussiness 的 thunk 分支），零风险。

---

## 5. 可复跑命令（全部本地，零会话）

```bash
# 1) class 校验与端点重跑（需 JDK，本机 /d/software/java/bin）
export PATH="/d/software/java/bin:$PATH"
S="<HERMES_HOME>/cache/scratch/implementer-only/role_static_r2"
javap -p -v "$S/classes/com/seeyon/udc/user/controller/UdcRoleController.class" \
  | grep -E "SHA-256 checksum|major version"          # → 885fba64…b098db / 52
javap -p -v "$S/classes/com/seeyon/udc/user/controller/UdcRoleController.class" \
  | grep -cE "^\s+org.springframework.web.bind.annotation.(Post|Get)Mapping"   # → 15

# 2) 构造器分布（形态归类）
cd "$S/web"
for f in *.js; do echo -n "$f "; grep -c "udcApolloQuery" "$f"; done

# 3) op 形态逐条（paramsKey）
grep -oE 'udcQueryLoader\.load\(\{[^}]{0,160}' module1622.js
```

> **注意**：本机无 `javap` 在 PATH（默认 `command not found`），
> 我第一遍因此得到「0 个 Mapping」的假结果。**必须显式加 JDK bin 到 PATH**。
> JDK 路径：`/c/Program Files/Java/latest` → 软链 → `/d/software/java`（javap 21.0.10）。

---

## 6. 证据文件（绝对路径）

| 内容 | 路径 | size / 校验 |
|---|---|---|
| javap 全量 | `<HERMES_HOME>\cache\scratch\implementer-only\role_static_r2\ctrl_v.txt` | 77,922 B / sha16 `98b7ce94` |
| class 本体（可重跑） | `…\role_static_r2\classes\com\xiaozhua\udc\user\controller\UdcRoleController.class` | sha256 `885fba64…b098db` |
| op 定义层 | `…\role_static_r2\web\module1622.js` | 3,994 B / sha16 `4acd467f` |
| 微前端入口 | `…\role_static_r2\web\remoteEntry.js` | 15,328 B / sha16 `a69f9b9b` |
| 角色管理页 | `…\role_static_r2\web\src_pages_role-permission_index_tsx.7d23367b.js` | 16,319 B / sha16 `468aafbb` |
| 角色授权页 | `…\role_static_r2\web\src_pages_role-authority_index_tsx.cef9f043.js` | 58,457 B / sha16 `a82a7b7d` |
| redux thunk 层 | `…\role_static_r2\web\bussiness.8e39da83.js` | 335,756 B |

**本文件全部结论 = STATIC。** 不含任何新 LIVE；引用的 LIVE 结论均转述自 P2/P3/S5。
**本轮零 `/service`、零页面、零写、零登录动作。**
