# ROUTE-S2-create-capture｜S2 建删全链取证（2026-10-17 22:27–23:35 +08，S2-R1 重启轮）

> 角色：implementer ｜ 切片：S2-R1（HANDOFF `column-s2-restart-handoff-r1-v1`，inbox `20261017T142744.570016Z-main-to-implementer-HANDOFF.json`）
> 目标应用：`datamigration9000000000000000001`（test2）
> 执行环境：Edge CDP 9229 + profile `cdp-udc9-07-column-v4`（22:27 时 9229 进程已死，按 CDP-ENDPOINT.md 同端口同 profile 自行拉起；期间 renderer 三次卡死，均只重启本域专属进程）
> 凭据：只引用 `shared-credentials/test2-web-credential.json`（路径引用，未打印未落盘）
> 抓包方式：**提交前注入 window.fetch + XMLHttpRequest hook，把 url/method/body/responseText 存 sessionStorage**（main 22:41 DECISION `column-s2-t5-responsebody-missing-correction-v1` 的取证修正；全程不依赖 CDP Network.getResponseBody）
> 证据等级：LIVE（页面真实点击 + 完整响应体 + MySQL 只读回读）｜原始件：同目录 `raw/` 7 件

---

## 一、完成标准（S2）5 条逐条判定

| # | 标准 | 结果 | 判定 |
|---|---|---|---|
| 1 | 创建 REST 三元组（URL/method/body）+ 响应体落盘 | 分组、栏目、两次删除全部含**完整响应体**（§二、§四） | **PASS** |
| 2 | DB 回读新行 id 与响应/页面一致 | W1/W2/W3 白名单精确 SELECT 全命中且字段一致（§三） | **PASS** |
| 3 | 页面可见证据 | 真实 DOM 链三件：`s2r1_d4_out.txt`(23:11:09) 两对象同现 → `d5_out.txt`(23:18:45) 删栏目后仅剩分组 → `d7_out.txt`(23:30:00)「暂无结果」（§三.5；口径按裁定 T） | **PASS** |
| 4 | 删除链证据 | 先栏目后分组，两次 `udcPortletDeleteIdPost` content:1 + 白名单归零（§四） | **PASS** |
| 5 | 产物落盘 + 本地 commit | 本文件 + `raw/*.json`（7 件）+ B 项更正，本地 commit（禁 push） | **DONE** |

**main 22:41 裁定的三项取证修正执行情况**：①fetch/XHR hook 已采用并成功取回全部响应体（解决 `__BODY_ERR__`）；②不需要退到 antd 文案旁证；③提交前已核对「栏目分组」下拉**已自动选中**（因先建了分组），22:36 那次静默失败的真因即「本应用无分组 → 下拉为空 → 提交被前置校验拦截、请求体被拒」；本轮按裁定先建分组后该前置条件解除，一次提交成功。

---

## 二、创建链 REST（页面真实点击，响应体完整）

### 2.1 分组（type=GROUP，folder 图标入口）

- 入口：栏目列表页 folder 图标按钮 → 表单仅一个必填「分组名称」→ 确定
- REST：`POST /service/udc/graphql?udcPortletCreatePost`
- 请求 variables：`{"body":{"appId":"8704025620829192834","terminalType":"PC","type":"GROUP","name":"S2GROUP20261017"}}`
- 响应（原文）：`{"traceId":"17922483013725158661","data":{"udcPortletCreatePost":{"code":"BOOT_0000","data":{"content":{"appId":"8704025620829192834","groupId":null,"guid":null,"id":"-2821989384273517473","name":"S2GROUP20261017","orderNo":0,"pageRelationId":null,"portletList":null,"publishState":null,"terminalType":"PC","type":"GROUP"}},"message":"SUCCESS","status":0}}}`
- 原始：`raw/s2r1_group_create.json`

**恢复判定标准第 4 条（op 命中判定）**：实际命中 `udcPortletCreatePost`（→ `udc/portlet/create`，PortletDto，type=GROUP），**未命中** `portlet-group/create`。静态预置 5.2.1 推断成立；`udc_portlet_group` 建后仍 0 行，与「建分组不碰该表（走门户 Dubbo 分类）」一致。

### 2.2 栏目（type=PORTLET，plus 图标入口）

- 提交前表单快照（裁定 I5，`raw/s2r1_portlet_form.json`）：适配终端 **PC=checked / MOBILE=unchecked** → page_info 期望 +1；「自定义页面」handWritten 未勾选；**栏目分组下拉已自动选中 S2GROUP20261017**（required 前置条件满足）
- REST：`POST /service/udc/graphql?udcPortletCreatePortletPost`
- 请求 variables：`{"body":{"appId":"8704025620829192834","caption":"S2PROBE20261017","curTerminalType":"PC","groupId":"-2821989384273517473","pageItems":[{"menuId":"-2821989384273517473","urlType":"PC"}],"pageType":"PORTLET","pageUrl":"S2PROBE20261017"}}`
- 响应（原文）：`{"traceId":"17922483545794594178","data":{"udcPortletCreatePortletPost":{"code":"BOOT_0000","data":{"content":{"appId":"8704025620829192834","groupId":"-2821989384273517473","guid":null,"id":"5810462779490574369","name":"S2PROBE20261017","orderNo":0,"pageRelationId":"8758458332069176381","portletList":null,"publishState":null,"terminalType":"PC","type":"PORTLET"}},"message":"SUCCESS","status":0}}}`
- 创建后自动跳转页面设计器 `portlet/edit/8758458332069176381`
- 原始：`raw/s2r1_portlet_create.json`（12 次调用，含跳转后设计器初始化全链）

> 注：`pageItems[0].menuId` 传的是**分组 id**（-2821989384273517473），不是栏目 id —— 这是前端表单的既有形态，登记备查。

### 2.3 H5 orderNo 动态断言

建前现场基线：`SELECT COUNT(*), COALESCE(MAX(order_no),0) FROM udc_portlet WHERE app_id=8704025620829192834` → `0, 0`
- 分组行 order_no=**1** = 建前 max+1 ✅
- 栏目行 order_no=**2** = 新 max+1 ✅
- 响应体 `orderNo` 恒为 0（两个创建响应都是 0），**不反映落库值** → H5 断言只能以 DB 回读为准（见 §六.6）

---

## 三、白名单回读（裁定 I 口径：禁全库绝对计数，按创建响应 id 精确 SELECT）

### W1 分组行
```sql
SELECT * FROM udc_test2.udc_portlet WHERE id=-2821989384273517473;   -- 命中 1 行
```
`type=0, group_id=NULL, order_no=1, terminal_type=1(PC), category=1(ADVANCED), template_type=NULL（平台不落，预期）, guid=-4399224624179689670, original_id=0, publish_state=1, page_relation_id=NULL`

### W2 栏目行
```sql
SELECT * FROM udc_test2.udc_portlet WHERE id=5810462779490574369;    -- 命中 1 行
```
`type=1, group_id=-2821989384273517473`（**S1 强制更正交叉验证 ✅**：type=1 的 group_id 指向 udc_portlet 自己的 type=0 行，不是 udc_portlet_group）`, order_no=2, terminal_type=1, category=1, template_type=NULL, page_relation_id=8758458332069176381`

### W3 page_info 行
```sql
SELECT * FROM udc_test2.udc_page_info WHERE relation_group_id=8758458332069176381;  -- 命中 1 行
```
`id=-1695224980799982257, page_type='PORTLET', page_url='S2PROBE20261017', url_type=1(PC), group_id=-2821989384273517473`（**page_info.group_id == 新建分组 id 交叉断言 ✅**）`, sort_no=331, layout_id=0, hand_written=0, schema_state=0`
命中行数 **1 = 表单勾选端数 1** ✅ → 裁定 I5 的 +1/+2 分叉现场判定为 **+1**。

### W4 udc_page_schema
按 `page_id IN (-1695224980799982257)` 计 **0 行** —— 空白页面无 schema 内容（同接口 `udcPageInfoDetailGet` 返回 `pageSchema:""`），非取证失败。

### 5. 页面可见（口径按 main 裁定 T：以真实 DOM 链为证，不要求创建当刻快照）

`raw/` 七件为 REST 抓包，**不含页面文案**；页面可见性以 scratch 真实 DOM 件为准，三件均已在盘可复核：

| 件 | 时刻 | 列表树 innerText | 对应用途 |
|---|---|---|---|
| `scratch/s2r1_d4_out.txt` | **23:11:09** | `S2GROUP20261017` + `S2PROBE20261017` | 建后两对象**同时可见** |
| `scratch/s2r1_d5_out.txt` | **23:18:45** | 仅剩 `S2GROUP20261017`（`S2PROBE20261017` 已消失） | 删栏目后**仅剩分组** |
| `scratch/s2r1_d7_out.txt` | **23:30:00** | `暂无结果` | 删分组后**空态** |

（上述三件均为 `cdp5.Tab.js()` 读 `document.body.innerText` 的原样输出，非截图、非推断。）

---

## 四、删除链（先栏目后分组，页面真实点击）

删除入口形态（本轮首次 LIVE 确认）：列表树节点 **hover 才出现** `filled-more` 图标 → 点开下拉 → 「重命名 / 编辑 / **删除**」 → 删除 → antd 确认弹窗 → 确定。CDP 需用 `Input.dispatchMouseEvent` 真实 mouseMoved（JS `dispatchEvent(mouseover)` 不足以触发该 hover 层）。

### 4.1 删栏目 S2PROBE20261017
- 确认弹窗文案：「删除静态栏目页面 / 您确定要删除S2PROBE20261017页面吗？」
- REST：`POST /service/udc/graphql?udcPortletDeleteIdPost`，`{"path":{"id":"5810462779490574369"}}` → `{"code":"BOOT_0000","data":{"content":1},"message":"SUCCESS","status":0}`
- 原始：`raw/s2r1_delete_portlet.json`

### 4.2 删分组 S2GROUP20261017
- 确认弹窗文案：「删除文件夹 / 您确定要删除文件夹S2GROUP20261017吗？」
- REST：`POST /service/udc/graphql?udcPortletDeleteIdPost`，`{"path":{"id":"-2821989384273517473"}}` → `content:1 / SUCCESS`
- 删除后前端自动回读 `udcPortletSelectByAppIdAppGet` → `content: []`
- **页面可见证据（口径按裁定 T）**：`scratch/s2r1_d7_out.txt`（23:30:00）列表树 innerText = `暂无结果`
  ⚠ 登记纪律：`raw/s2r1_delete_group.json` 里的 `content: []` 只是**接口空态**，不得单独当页面可见；页面空态只认 d7 的真实 DOM innerText
- 原始：`raw/s2r1_delete_group.json`

### 4.3 删除后白名单归零（LIVE 回读）

| 白名单 | 删除后 | 判定 |
|---|---|---|
| `udc_portlet id IN (-2821989384273517473, 5810462779490574369)` | **0 行** | ✅ |
| `udc_page_info id=-1695224980799982257` | **0 行** | ✅ |
| `portal_portlet_category category_code='-2821989384273517473'` | **0 行** | ✅ 门户分类同步删除（**物理删**） |
| `udc_portlet` 全库 | **157（26/131）** | 与建前基线一致，零残留 |
| `udc_portlet_group` | **0** | 全程未动 ✅ |

**门户定义是软删除（H2 关键判定点）**：`portal_portlet_definition` 该行**仍在**（id=329969732608628974），`delete_flag` 0→**1**，`update_time=23:18:39`（删栏目时刻）。
→ 「行还在」**≠** 残留；H2 残留判定**必须带 `delete_flag=0` 条件**，否则会把正常软删误判成脏数据。

---

## 五、必抓附加项逐条判定

### H1 门户侧分类同步（LIVE ✅ —— 本域 P0「栏目在门户侧是什么」首个 LIVE 支点）
```sql
SELECT * FROM portal_test2.portal_portlet_category WHERE category_code='-2821989384273517473';
```
建分组后**即时**命中 1 行：
`id=-1582715737185534094, category_code='-2821989384273517473'`（**== 本地分组 id ✅**，精确比对键生效，name 模糊匹配未使用）`, category_name='S2GROUP20261017', category_path='-1/datamigration9000000000000000001/-2821989384273517473', sort_no=1（=order_no）, category_type=0（注册的栏目分类）, data_status=0（设计态）, app_code='datamigration9000000000000000001', original_app_id=8704025620829192834`

**与静态预置不符（提交 main 更正）**：`parent_category_code` 实为 **`datamigration9000000000000000001`**（应用 code），**不是**字节码常量 `PARENT_CATEGORY_CODE="-1"`；`-1` 只出现在 `category_path` 的根前缀。即「门户分类父级 = 应用」而非「全局根 -1」。

### H2 门户侧残留复查（LIVE ✅，判定键=delete_flag）
删分组后：`portal_portlet_category` 白名单 **0 行**（物理删）；`portal_portlet_definition` 行在但 **delete_flag=1**（软删）。分类物理删 + 定义软删，两者时刻均与删除链对应，**无脏残留**。

### H3 删除顺序（按裁定执行，证据独立）
先删栏目（→ `udc_page_info` 同删 → `portal_portlet_definition` 软删），后删分组（→ `portal_portlet_category` 删）。两次 REST 分别抓到，「删栏目」证据**独立成立**（未依赖级联删除）。

### H4 op-log 判读（LIVE，与静态预期不符 → 提交 main 更正）
```sql
SELECT * FROM udc_test2.udc_operation_log WHERE create_time>='2026-10-17 22:40:00' AND domain_caption LIKE 'S2%';
```
| 动作 | 条数 | 形态 |
|---|---|---|
| 建分组 | **1** | action_type=1, module=4, sub_module=6, log_element=`["栏目\栏目分组[S2GROUP20261017]"]`, trace_id 与创建响应一致 |
| 建栏目 | **1** | action_type=1, sub_module=**40**, log_element 数组含 **2 元素**：「栏目\栏目页面[S2PROBE20261017][PC]」+「栏目\栏目分组\栏目节点[S2PROBE20261017]」, domain_id=-1695224980799982257 |
| **保存并提交** | **1** | **action_type=3, module=4, sub_module=4**, log_element=`["栏目\栏目"]`, domain_id=-1695224980799982257, **22:47:38**, trace `17922484587530491237` |
| 删栏目 | 1 | action_type=2, sub_module=40, 23:18:39 |
| 删分组 | 1 | action_type=2, sub_module=6, 23:29:52 |

**保存页独立 op-log（main 裁定 U-b 追加，auditor 确认属实）**：第 3 行不是创建行，是「保存并提交」(`udcPageInfoUpdatePost`) 产生的独立动作行 —— `action_type=3`（既非 1 创建也非 2 删除）、`sub_module=4`、`log_element` 单元素 `栏目\栏目`、`domain_id` 指向**栏目页面 id**（不是 portlet id）。其 `trace_id=17922484587530491237` 与 `raw/s2r1_page_save_submit.json` 中 `udcPageInfoUpdatePost` 响应的 traceId 完全一致，可交叉锁定。
→ 判读纪律：**保存页面 ≠ 创建栏目**，两者各有独立 op-log；不得把 action_type=3 计入创建、也不得漏记（本次首版产物即漏记，本表已补）。

**结论更正**：静态 H4「建栏目产生**两条** op-log（PORTLET_PAGE=40 baseCreate + PORTLET=5 create）」在 LIVE **未复现**。实际是**一条** sub_module=40 记录、内部 `log_element` 数组含 **2 个元素**；`PORTLET=5 create` 行完全未出现。
→ 判读规则应改为「建栏目 = 1 条 op-log、log_element 双元素；看到 2 条才是异常」。静态那两条可能是别处写路径（未触发），以 LIVE 为准。

### H5 orderNo（LIVE ✅，见 §2.3）

### H6 门户定义同步（保存页面触发；LIVE ✅）
- 「暂存草稿」→ `udcPageInfoUpdateDrafPost`（content:1，`isDraftPage` 仍 true）→ **草稿不触发门户同步**（门户定义未变）
- 「保存并提交」→ `udcPageInfoUpdatePost`（content:1，`isDraftPage` true→**false**）→ **同秒（22:47:38）生成**门户定义行
- 定义行：`portal_portlet_definition` `id=329969732608628974, expose_name='S2PROBE20261017', category_code='-2821989384273517473'`（==分组 id）`, category_path` 同 H1`, enable_pc=1, enable_mobile=0, m_definition_info=NULL, sort_no=2, app_code/original_app_id` 与应用一致
- **H6-a 本轮不适用**（不落 UNVERIFIED 标签）：「只建栏目不保存页面」场景未发生 —— 本轮先建（22:45）后保存（22:47），直接取到 LIVE 正证据
- **H6-b 单端形态验证 ✅（裁定 M 三项核对）**：仅 PC 端保存 → 该端 `enable_pc=1 + expose_name + definition_info` **三项齐**；手机端 `enable_mobile=0 + m_definition_info=NULL`。与字节码推演一致
- **重大映射更正（静态件需改）**：`portal_portlet_definition.portlet_id = **8758458332069176381（= pageRelationId / relationGroupId）**，**不是** `udc_portlet.id`(5810462779490574369)。此前按 portlet.id 精确查 0 行即此故
- **另一个不同键**：`definition_info` JSON 内 `categoryCode=8704025620829192834`（**appId 语义**），与表列 `category_code`（**分组 id 语义**）不是同一个东西，判读不得混用
- 原始：`raw/s2r1_page_save.json`（暂存草稿）、`raw/s2r1_page_save_submit.json`（保存并提交）

---

## 六、对 ROUTE / 静态预置的更正清单（提交 main 裁定，本角色不改 ROUTE）

1. **H1 parent_category_code**（**按裁定 U-a 的 Q1 精确化版**，main 原「-1 仅是 path 根前缀」表述已废止）：**非根层**分类 parent = 所属应用 code（本轮实测 1/1；auditor 全库口径 94/94 = 100%）；**根层**分类 parent = `-1`（37 行：33 应用根分类 + 4 平台内置 common/thirdColumn/usual）。→ `-1` 在根层是**真实 parent 值**，同时也是 `category_path` 前缀，两种语义并存，判读须先分层。
2. **portal_portlet_definition.portlet_id 映射**：= **pageRelationId**（= relationGroupId），**非** udc_portlet.id。按 udc_portlet.id 查门户定义必 0 行。
3. **H4 op-log**：建栏目 = **1 条**记录（sub_module=40，log_element 双元素），非两条独立记录；`PORTLET=5 create` LIVE 未出现。
4. **H2 判定键**：门户定义删除为**软删**（delete_flag=1），残留判定须带 `delete_flag=0`；「行存在」≠残留。
5. **definition_info.categoryCode**：JSON 内是 appId 语义，与表列 category_code（分组 id 语义）不同键。
6. **创建响应 orderNo 恒 0**：`udcPortletCreatePost` / `udcPortletCreatePortletPost` 响应体 orderNo 均为 0，不反映落库值 → H5 只能以 DB 回读断言。
7. **删除入口交互**：列表树节点 hover（CDP 需真实 `Input.dispatchMouseEvent`，JS dispatchEvent 不触发）才出现 `filled-more` → 下拉 → 删除 → 确认弹窗。恢复期若再遇「找不到删除入口」，先查这点，别判成 BLOCKED。
8. **保存页面另有一条独立 op-log**（main 裁定 U-b / auditor 确认）：`action_type=3`、`module=4`、`sub_module=4`、`log_element` 单元素 `栏目\栏目`、`domain_id`=栏目页面 id。**不得并入创建计数，也不得漏记**（首版产物即漏记，§五 H4 表已补第 5 行）。

---

## 六之二、证据登记纪律（VERDICT PARTIAL 的直接教训，2026-10-18 按裁定 T/U 补）

本轮被 auditor 判 PARTIAL 的根因**不是**业务事实，而是**产物里引用了不存在的证据**：

> 下段两处出现的「添加成功」等字样，是**被订正错误自身的引述**（用于追溯改了什么），**不是证据声明**。机械 grep 会命中，请按语义判读。产物正文其余位置已无该文案。

- 原文写「页面消息『添加成功！』（原始件 AFTER 段）」—— `raw/` 七件经 auditor 与本人双向 grep，**0 命中**「添加成功」；该文案只存在于本人会话中的临时输出，从未落盘。
- 由此订正三条纪律（后续所有切片适用）：
  1. **可引用的证据 = 已落盘文件 + 可复算的绝对路径/时刻**。会话内临时输出、屏幕记忆、被裁剪的中间变量，**一律不得写入产物**。
  2. **区分三类证据对象**：REST 抓包（`raw/*.json`，只有接口层事实）/ 页面 DOM 快照（`scratch/*_out.txt` 的 innerText）/ DB 回读（SQL + 结果）。三者**不可互相冒充**：接口 `content:[]` 是接口空态，不是「页面暂无结果」；页面 innerText 也不证明落库。
  3. **写完产物立刻 grep 自证**：把产物里出现的每个 `文件名`/「引文」回到盘上 grep 一次，0 命中即删改。本轮补丁已完成该自证（`添加成功`/`原始件 AFTER`/`AFTER 段` 三个关键词全 0 命中）。

---

## 七、B 项状态文档更正（裁定 B，随本件 commit）

`docs/audit/udc-nine-modules-status.md`：
- **L17 表格行**：栏目域状态 `VACUUM（几乎零证据）` → **`PARTIAL（S1+S2 定位完成，写链 LIVE）`**；表族名由「无 udc_column/udc_portal 表」更正为 **`udc_portlet` + `udc_page_info(PORTLET)` + 门户侧 `portal_portlet_category`/`portal_portlet_definition`**；证据量由「1 文件 / 0.7KB」更正为含 S1 导航抓包 + S2 建删全链。
- **§7 栏目段首**：补定位结论指针（详见 `ROUTE-S1-nav-capture.md` / 本文件 / `raw/`）。

---

## 八、边界遵守

- 写操作：1 分组 + 1 栏目创建、1 次暂存草稿 + 1 次保存并提交、2 次删除 —— 全部页面真实点击、全部在授权应用内、**全部已删清**（§4.3 归零表）
- DB 仅 SELECT（`conn.py` 只读通道）；未 push；未改 ROUTE / DECISIONS / 阶段 / 范围 / 验收标准；未跨域；未打印 secret
- 浏览器仅本域 9229 / `cdp-udc9-07-column-v4`；renderer 三次卡死按授权重启本域专属进程，未动他域端口
- 测试对象命名 `S2*` 前缀独立，不与他域对象冲突；创建-删除窗口期内列表里可见，已回收

---

## 历史：BLOCKED 轮（403，2026-10-17 17:2x，结论已被本轮取代）

17:00–17:1x 间 `lowcode-test2` 入口对 `/service/*` 整段 403（nginx 页 548B，与 token/cookie/浏览器均无关，登录接口同时被拒），S2 首轮零写 BLOCKED（证据与推断原文见 git 历史 commit）。22:27 main 门禁复核解封（`/service/common/version`=200 业务 JSON、`/main/`=200），S2-R1 重启即本轮。
首轮（22:36）提交虽有 HTTP 200 但响应体缺失 + DB 零落行，main 22:41 裁定 `UNVERIFIED-响应体缺失` 并给出 fetch/XHR hook 取证修正 —— 本轮已采用，问题闭环。
