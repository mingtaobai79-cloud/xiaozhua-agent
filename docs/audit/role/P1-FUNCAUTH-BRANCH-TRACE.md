# funcAuth 页面分支 STATIC 追溯（#13 vs #14 到底谁触发）

> 授权：main VERDICT #P1-STRUCT §一「§二 的 funcAuth STATIC 追溯（页面分支条件层）：授权，下轮可做（纯读 bundle，零会话依赖）」
> 撰写：implementer · 2026-10-18 12:04–12:07 GMT+8
> **证据等级：STATIC**（bundle 原文逐段提取，无任何页面操作、无 `/service`、无写）
> 产物源：`<HERMES_HOME>\cache\scratch\implementer-only\role_static_r2\web\`

---

## 0. 结论先给（三句话）

1. **页面上「设置权限」弹窗的「确定」按钮 → 走 #13 `func-auth`（单条）**，不是 #14。判据是**调用点级**，不是猜的。
2. **#14 `func-auth-all` 的触发点是另一个「确定」按钮** —— 位于**功能权限总表**（`U` 组件），不在「设置权限」弹窗里。
3. **两者共用同一个字面文案「确定」**，但属于**不同组件、不同 state、不同入参形态** ⇒
   「点一次设置权限无法区分命中哪个」这个担心**可以撤回**：它们甚至不在同一个弹窗里。

> 一句话：**不是「同一个入口两个分支」，而是「两个不同组件各有一个确定按钮」。**

---

## 1. 调用链三层（逐层有原文）

```
① 页面组件层（src_pages_role-permission_index_tsx.7d23367b.js）
     ├─ 组件 v（「设置权限」Modal）  → (0,c.Pt)({resourceList, roleId, roleCode})
     └─ 组件 U（功能权限总表）        → (0,N.ic)(e)
              ↓
② redux thunk 层（bussiness.8e39da83.js）
     ├─ 模块 6994「role-list」        Pt → thunk「role-list/handleFunctionAuthByRoleId」→ 调 op 层 o.Pt
     └─ 模块 226165「function-permission」
              ic → thunk「function-permission/handleSaveFunPermission」→ 调 op 层 o.ic
              ig → thunk「function-permission/fetchAllRoleAuth」      → 调 op 层 o.ig
              p  → thunk「function-permission/fetchRoleAuthByCode」   → 调 op 层 o.ig
              ↓
③ op 定义层（模块 1622，即 module1622.js 同源）
     Pt(h) = udcApolloQuery("mutation udcCtpUserRoleFuncAuthPost …")      ← #13 单条
     ic(v) = udcApolloQuery("mutation udcCtpUserRoleFuncAuthAllPost …")   ← #14 批量
     ig(E) = udcApolloQuery("mutation udcCtpUserRoleRoleAuthAllPost …")   ← #12 读
```

### 1.1 op 层绑定（原文逐字，**模块 id = 1622**，字符偏移 305,625 起）

> **⚠️ 2026-10-18 12:19 订正（auditor 复核抓出）**：本节原写「模块 **305647** 导出映射」——**错**。
> 305647 是**字符偏移量**，不是模块 id：
> ```
> grep -c '305647'          → 0        （全文件无此模块 id）
> '1622:function(e,t,n){'   → 位置 305,625   ← 真实模块起点
> 导出表起点 305647 = 模块起点 305625 + 22
> ```
> 我把「偏移 305647」抄成了「模块 305647」，且 305647 与 305625 只差 22，不易察觉。
> **正确表述：模块 id = 1622（起点字符偏移 305,625）。**

```js
.d(t,{MD:…, ig:function(){return E}, …, Pt:function(){return h}, …, ic:function(){return v}, …})

h = e => l.udcApolloQuery("mutation udcCtpUserRoleFuncAuthPost ($body: udcCtpUserRoleFuncAuthPostInputBody) {…}", {body: …})
v = e => l.udcApolloQuery("mutation udcCtpUserRoleFuncAuthAllPost ($body: [udcCtpUserRoleFuncAuthAllPostInputBody]) {…}", {body: e})
E = (e,t) => l.udcApolloQuery("mutation udcCtpUserRoleRoleAuthAllPost ($body: udcCtpUserRoleRoleAuthAllPostInputBody) {…}", {body:{appId:e, code:t}})
```

| 导出名 | 内部变量 | op | 对应端点 | 入参形态 |
|---|---|---|---|---|
| `Pt` | `h` | `FuncAuthPost` | **#13** | 单条 `InputBody` |
| `ic` | `v` | `FuncAuthAllPost` | **#14** | **`[InputBody]` 数组** |
| `ig` | `E` | `RoleAuthAllPost` | #12 | `{appId, code}` |

> **关键**：`Pt` 与 `ic` 在**同一个模块里是两个不同的导出** ⇒ 不存在「一个函数按条件分派」的实现。

### 1.2 thunk 层绑定（原文逐字）

**模块 6994「role-list」**（导出 `Pt:function(){return h}`）：
```js
h = createAsyncThunk("role-list/handleFunctionAuthByRoleId", async (e,t) => {
      … let t = await o.Pt(e); … message.success("设置角色权限成功"); …
    })
```
⇒ `c.Pt` = **thunk** `role-list/handleFunctionAuthByRoleId` → 内部调 `o.Pt` = op `FuncAuthPost`（#13）。
**这一层没有分支**：thunk 名字就带 `ByRoleId`，入参就是单角色。

**模块 226165「function-permission」**（导出 `ic:function(){return d}`）：
```js
d = createAsyncThunk("function-permission/handleSaveFunPermission", async (e,t) => {
      … let t = await o.ic(e); … message.success("设置页面功能权限成功！"); … n(s(i.vL)); …
    })
```
⇒ `N.ic` = thunk `function-permission/handleSaveFunPermission` → 内部调 `o.ic` = op `FuncAuthAllPost`（#14）。
注意提示文案不同：**「设置页面功能权限成功！」**（#14）vs **「设置角色权限成功」**（#13）——
这是运行时区分两者的**免费判据**（响应后 toast 文案不同）。

**同模块还有两个读 thunk**（都不是写）：
```js
s = createAsyncThunk("function-permission/fetchAllRoleAuth",   … o.ig(e) …)      → #12
c = createAsyncThunk("function-permission/fetchRoleAuthByCode", … o.ig(n,a) …)    → #12
```
⇒ `N.ig` 是**读**（role-auth-all），不是写。特别记：`fetchRoleAuthByCode` 正是 P3 §9.4 那个
「`code` 参数是资源 code 不是 appId」的坑所在的调用 —— **它就是 #12 的第二个入口**。

---

## 2. 页面层两个触发点（这是本轮真正的答案）

### 2.1 触发点 A：「设置权限」弹窗的「确定」→ #13

原文（`src_pages_role-permission_index_tsx.7d23367b.js`，逐字）：

```js
let v = async () => {
  let {id:e, code:t} = i;
  if (e) {
    let l = f(u, m);
    s((0,c.Pt)({resourceList:l, roleId:e, roleCode:t})).then(()=>{b()})   // ← #13
  }
},
b = () => { s((0,c.k6)({})), l() },
k = {PC:"web功能权限", MOBILE:"移动功能权限"};

return a().createElement(r.Modal, {
  title: d ? "查看权限" : "设置权限",       // ← 这个 Modal 的标题
  visible: t, onCancel: b, width: 1100, …,
  footer: d ? null : [ … 取消 … 确定 … ]
})
```

**判据（三条，全部原文级）**：
1. 调用点是 `(0,c.Pt)`，`Pt` = thunk `handleFunctionAuthByRoleId` = op `FuncAuthPost` = **#13**；
2. 入参是**单条对象** `{resourceList, roleId, roleCode}`，含 `roleId` —— #14 是 `List`，不含 roleId 字段；
3. 所在 Modal 标题是 **「设置权限」/「查看权限」**，宽 1100，footer 有「取消/确定」。
   **`title = d ? "查看权限" : "设置权限"`** —— `d` 为真时是查看模式，此时 footer 为 null（无确定按钮）。
   ⇒ 这也解释了 S5 那次 `permissionLook` 恒 true、复选框全 disabled、无保存按钮的现象（**查看模式**）。

### 2.2 触发点 B：功能权限总表的「确定」→ #14

原文（同文件，逐字）：

```js
U = e => {
  let {type:t="PC"} = e, l = useDispatch(),
      {appResourceById:i} = useSelector(e=>e.appDesign.roleListReducer),
      {allResourceIds:d, allRoleInfo:s, btnLoading:m} = useSelector(e=>e.appDesign.functionPermissionReducer);

  useEffect(()=>{ l((0,N.ig)(u.vL)) }, [l]);          // ← 载入：读 #12 全部角色授权
  let p = (0,z.$)(t);
  useEffect(()=>{ l((0,c.WW)(p)) }, [p]);

  return createElement("div", {className:"af44c3ac"},
    createElement(j, {type:t}),                        // ← 资源树/权限表
    createElement("div", {className:"_6b0a9d2f"},
      createElement(r.Button, {
        type:"primary",
        onClick: ()=>{ let e = k(d,i,s); l((0,N.ic)(e)) },   // ← #14（批量）
        loading: m
      }, "确定")
    ))
}
```

**判据（三条）**：
1. 调用点是 `(0,N.ic)`，`ic` = thunk `handleSaveFunPermission` = op `FuncAuthAllPost` = **#14**；
2. 入参 `e = k(d, i, s)` —— 由 `allResourceIds` / `appResourceById` / `allRoleInfo` 聚合成 **数组**（对应 `List<InputBody>`）；
3. 组件 `U` 与「设置权限」Modal 是**两个独立组件**，`U` 自带 `useEffect` 拉 #12，且按钮文案同为「确定」。

### 2.3 ⚠️ 为什么这两者「看起来像同一个入口」

- 两个按钮**文案都是「确定」**（一个字面量相同）；
- 都在角色权限页面内；
- 从 UI 上看，一个是弹窗底部的确定，一个是页面内嵌表格区块底部的确定 —— **位置不同但都叫确定**。

⇒ 若只看「点了确定」，确实分不清。**但它们在代码里是两个 `createElement`、两个 `onClick`、两个 thunk。**

---

## 3. 撤回我上一轮的担心（结论修正）

上一轮（`P1-STRUCTURE-SUPPLEMENT.md` §3.4）我写：

> 「补 LIVE 时若只点一次设置权限，无法确定命中的是 #13 还是 #14」

**这个担心不成立，现在撤回。** 准确表述：

| 场景 | 命中 | 说明 |
|---|---|---|
| 在「设置权限」弹窗点「确定」 | **#13** `func-auth` | 单角色单条，Modal title=设置权限 |
| 在功能权限总表点「确定」 | **#14** `func-auth-all` | 批量 List，组件 U |
| 页面加载 / 展开资源节点 | **#12** `role-auth-all`（读） | 组件 U 的 useEffect + `fetchRoleAuthByCode` |

⇒ **不存在「一个入口两个分支」**。原担心来自我只看了 thunk 名都在 bundle 里，
没看**调用点**（`(0,c.Pt)` vs `(0,N.ic)`）——**这是「有名字≠有分支」的又一次同型错误**（同 §2.3 的按名字猜形态）。

### 3.1 运行时区分判据（比读代码更快，留给下次 LIVE）

| 判据 | #13 | #14 |
|---|---|---|
| GraphQL op 名（URL） | `?udcCtpUserRoleFuncAuthPost` | `?udcCtpUserRoleFuncAuthAllPost` |
| 请求体顶层 | **对象** `{roleId, roleCode, resourceList}` | **数组** `[{roleId, roleCode, resourceList}, …]` |
| 成功 toast | 「**设置角色权限成功**」 | 「**设置页面功能权限成功！**」 |
| 数量级 | 1 条 | N 条 |

**最省事的是 toast 文案**：两个文案不同，肉眼可辨，不需要开 DevTools。

---

## 4. 顺带确认：S5 那次为何必然是 #13（三条独立判据）

| # | 判据 | 值 |
|---|---|---|
| 1 | URL op 名 | `?udcCtpUserRoleFuncAuthPost`（P3 §11 请求原文） |
| 2 | body 形态 | 单条对象，含 `roleId:"-4544711258376164024"`、`roleCode`、`resourceList` 长度 1 |
| 3 | 本轮新增：该 op 的唯一页面调用点 | `(0,c.Pt)` in 「设置权限」Modal ⇒ **#14 的调用点是 `(0,N.ic)`，与弹窗无关** |

⇒ S5 的 `func-auth` LIVE **无歧义**，三条判据互相独立。

---

## 5. 边界与未取证

| 项 | 状态 |
|---|---|
| 两个「确定」按钮的**实际 DOM 位置/可见条件** | **UNVERIFIED** —— 需页面（会话 BLOCKED） |
| `d`（查看模式）在什么条件下为 true | **UNVERIFIED** —— 与 S5 的 `permissionLook` 恒 true 现象相关，但本轮未追 |
| 组件 `U`（功能权限总表）从哪个路由进入 | **UNVERIFIED** —— `role-permission_entry_tsx` 与 `role-authority_index_tsx` 都未定位到它 |
| #14 是否真被用户点过 | **UNVERIFIED**（P1-LIVE-GAP-MATRIX 记 `—`，一致） |

> 以上未取证项**都不影响 §0 的三条结论** —— 结论建立在「调用点是哪个 thunk」上，那是 bundle 原文级的硬事实。

---

## 6. 可复跑命令（本地，零会话）

> **⚠️ 2026-10-18 12:19 订正（auditor 复核抓出）**：本节原三条 `grep -o 'Pt:function(){return h}'` 之类的命令
> **会指错模块**，必须改。实测：
> ```
> 'Pt:function(){return h}'  → 2 处：模块 6994（h 是 createAsyncThunk，是 thunk 不是 op）
>                                     模块 1622（正确）
> 'ic:function(){return d}'  → 1 处：**模块 2789，不是 1622**   ← 原命令完全指错
> 'ig:function(){return E}'  → 1 处：模块 1622 ✅
> ```
> 且 1622 里 `ic → v`（不是 `d`）。**原命令的可检验性等于零。**
> **教训：`grep` 命中 ≠ 语义归属 —— 必须先判定命中处在哪个模块作用域内。**

```bash
S="<HERMES_HOME>/cache/scratch/implementer-only/role_static_r2"
cd "$S/web"

# 1) 定位模块 1622（op 层）的真实边界，并在该作用域内取导出表
python - <<'PY'
import re
b=open('bussiness.8e39da83.js',encoding='utf-8',errors='replace').read()
mods=[(m.start(), m.group(1)) for m in re.finditer(r'(\d+):function\(', b)]
i=[p for p,n in mods if n=='1622'][0]
end=[p for p,n in mods if p>i][0]
seg=b[i:end]
print('模块 1622 起点偏移:', i, '| 长度:', len(seg))
for k in ('MD','ig','Pt','ic'):
    m=re.search(r'[,{]'+k+r':function\(\)\{return (\w+)\}', seg)
    print('  1622.%s -> %s' % (k, m.group(1) if m else 'NOT IN 1622'))
# 期望：MD->c  ig->E  Pt->h  ic->v
PY

# 2) 模块作用域归属校验（证明原三条 grep 会指错）
python - <<'PY'
import re
b=open('bussiness.8e39da83.js',encoding='utf-8',errors='replace').read()
mods=[(m.start(), m.group(1)) for m in re.finditer(r'(\d+):function\(', b)]
own=lambda p:[n for s,n in mods if s<=p][-1]
for pat in ('Pt:function(){return h}','ic:function(){return d}','ig:function(){return E}'):
    print(pat, '->', [(m.start(), own(m.start())) for m in re.finditer(re.escape(pat), b)])
PY

# 3) thunk 层名字（含提示文案差异 —— 这条是免费运行时判据）
grep -o 'handleFunctionAuthByRoleId' bussiness.8e39da83.js
grep -o 'handleSaveFunPermission'    bussiness.8e39da83.js
grep -o '设置角色权限成功\|设置页面功能权限成功' bussiness.8e39da83.js

# 4) 页面层两个调用点（答案所在）
grep -o '(0,c.Pt)({resourceList:[^}]*}' src_pages_role-permission_index_tsx.7d23367b.js
grep -o '(0,N.ic)(e)'                    src_pages_role-permission_index_tsx.7d23367b.js
grep -o 'title:d?"查看权限":"设置权限"'   src_pages_role-permission_index_tsx.7d23367b.js
grep -o 'footer:d?null'                  src_pages_role-permission_index_tsx.7d23367b.js
```

### 6.1 ⚠️ 两个必须注意的口径（auditor 复核补，2026-10-18 12:26）

#### (a) 正则必须 `\d+`，不能 `\d{2,5}` —— 否则 33/101 个模块跨度算错

本节初版用 `r'(\d{2,5}):function\('`，**漏掉 70 个一位数模块 id**（`8:function(` / `6:function(` / `9:function(` …）：

```
\d{2,5}  → 101 个模块   位数分布 {4位:95, 3位:6}          ← 漏掉全部一位模块
\d+      → 171 个模块   位数分布 {4位:95, 3位:6, 1位:70}   ← 正确
两版重叠 101 个模块，其中 33 个 span 不一致：
  模块 2741  \d{2,5}=(1513,1665)      \d+=(1513,1542)      差 123
  模块 9673  \d{2,5}=(30098,31869)    \d+=(30098,30127)    差 1742
  模块 3138  \d{2,5}=(195227,195960)  \d+=(195227,195256)  差 704
  模块 3922  \d{2,5}=(205351,210515)  \d+=(205351,205428)  差 5087
```

**对 1622 本身无影响**（两版 span 都是 `(305625, 309620)`，长度 3995）⇒ 本轮结论不受影响。
**但这段是当通用配方写的** —— 下一个人拿它定位别的模块，33% 概率把相邻模块的内容一起吃进来，
正好重演「把 A 模块的东西算到 B 头上」那个错。

> **不要以为 `[\d,]+` 更稳**：我实测过，它会把模块间的**前导逗号吃进 id**（得到 `,1622`），
> 171 条里只有 `6662` 和 `8` 两个不带逗号 ⇒ 反而引入新 bug。**就用 `\d+`。**

归类：这是「文本存在 ≠ 语义成立」的**另一面** —— **「正则能匹配 ≠ 覆盖全集」**。
三条并列：
| 错 | 表现 | 本质 |
|---|---|---|
| 一个入口两分支 | 看 thunk 名都在，以为有分支 | 有名字 ≠ 有分支 |
| 模块 305647 | 看偏移数字当成模块 id | 数字 ≠ 那个语义对象 |
| `\d{2,5}` | 正则能跑通且对当前目标有效 | **能匹配 ≠ 覆盖全集** |

#### (b) 「调用点各为 1」只是本 chunk 口径，全局是 2

auditor 实测（我复核一致）：

```
src_pages_role-permission_index_tsx.7d23367b.js : (0,c.Pt)=1  (0,N.ic)=1  (0,N.ig)=1
src_pages_role-permission_entry_tsx.ebba5ac6.js : (0,c.Pt)=1  (0,N.ic)=1  (0,N.ig)=1
entry chunk 头部：push([["src_pages_role-permission_entry_tsx","src_pages_role-permission_index_tsx"], …])
```

⇒ **`*_entry_tsx` 是带两个 chunk 名字的同一模块副本（webpack 多入口命名），不是独立调用点。**
所以正确表述是：

> **本 chunk 内 1 处；`*_entry_tsx` 为同模块副本（chunk 名数组含两个名字），非独立调用点。**

这不影响「#13/#14 是两个不同调用点」的结论 —— 两个 op 的调用点分别在弹窗与总表两个组件里，
副本不改变「它们是两个组件」这个事实。但**「grep 计数=1」在全局口径不成立，不能那么写。**

---

## 7. 与 P1 补充文件的关系

本文件补充 `P1-STRUCTURE-SUPPLEMENT.md` §3.4（原写「页面分支条件未取证」）。
**§3.4 的担心已被本文件撤回**；补充文件里保留原文 + 指向本文件的指针，不删历史（保留订正痕迹）。

**本文件证据等级：STATIC。** 零 `/service`、零页面、零写、零登录。
