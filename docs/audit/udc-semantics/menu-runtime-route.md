# P3-a 运行态门户路由可达 — 证据文档

> 角色：implementer（菜单域）· 2026-10-17 23:40–23:55 · 环境 test2 · 授权应用 `datamigration9000000000000000001`
> HANDOFF：`menu-p3a-runtime-route-probe-rev2`（main 23:00 REV2，作废首版）
> 证据等级：LIVE（CDP 浏览器实测 / MySQL / Redis 回读）+ STATIC（在盘 md）
> **取证时点：2026-10-17 23:20–23:55（GMT+8）。22:45 域外写入 S2PROBE20261017 之后，`udc_page_schema` 全库 1562 行（P2 时点 1561）。**

---

## 0. 判定总览

| 项 | 判定 | 依据 |
|---|---|---|
| P3-a 镜像内正常链路由可达 | **PASS（限定：静态主线 + SPA 加载实测，数据面被 token 黑名单阻断）** | §1–§4 |
| 页面可见证据（列表行渲染） | **BLOCKED（环境级：单账号互踢 + 沙箱服务 token 校验拒绝）** | §2 |
| 路由消费字段 | **pageUrl + menuCode 组合（page_id 不参与运行态路由）** | §4 |
| P3-b 副本链可达 | **BLOCKED（前置=应用发布通过一致性检测；本轮零发布动作）** | §5 |
| P2 所缺页面可见证据 | **未取得**（同一阻断） | §2 |

**总任务不停止**：按 HANDOFF 兜底条款，静态主线已完成，页面侧所需输入已列 §7。

## 1. 关键破案：所有「CDP 挂死」的真因（LIVE，本轮独立实证）

此前 auditor（P2）与本轮初始探测都把「Runtime.evaluate 40s 超时、DOM.getDocument 超时、Debugger.pause 超时」
归因为「JS 主线程挂死/单页路由死锁」。**本轮实测推翻该结论**：

1. 网络事件流正常推送（Runtime.consoleAPICalled / Page.domContentEventFired 等全部到达）；
2. 事件流里出现 **`Page.javascriptDialogOpening`**；
3. 消息内容：`alert('身份认证信息无效，请重新登录')` + `alert('token黑名单')`（以及互踢时 `alert('您的账号已在另一个设备上登录')`）。

**原生 alert 对话框阻塞渲染主线程 → CDP 同步域（evaluate/DOM/Debugger）全部排队不回。**
`Page.handleJavaScriptDialog(accept)` 处理后 evaluate 立即恢复正常（实测 `1+1→2` 与 DOM 快照均成功）。

⇒ 修正既有结论：**不存在「page-manage 单页 JS 死锁」，P2 的挂死同为 token 失效 alert 所致。**
（auditor 观察到的「microflow editor 标签正常、page-manage 标签挂死」差异 = 各标签 token 状态与 dialog 时点不同。）
⇒ 处置假设同步修正：「重启浏览器/换通道」确实不对症（与 auditor 结论一致），但正确处置是 **dialog 处理 + token 续期**，不是「避开该路由」。

## 2. 页面侧实测（LIVE，CDP）——SPA 加载链证明路由真实生效

带新 token 直开 `https://lowcode-test2.example.com/main/portal/datamigration9000000000000000001/qyfapzlb`：

**网络流（前 3.3s 内 122 事件）关键序列**（全部 200）：

```
0.0s  GET  /main/portal/datamigration9000000000000000001/qyfapzlb   ← SPA shell
0.2s  POST /service/ctp-application/appcenter/search-app-edition    ← 参数含 "datamigration9000000000000000001"
0.4s  GET  /service/ctp-user/menu/select-front-nav-menu?menuId=-4673562733611694157
0.4s  GET  /service/portal/config?portalType=PC
0.5s  GET  /datamigration9000000000000000001/remoteEntry.20261015192931_5.3.17_1.0.0.js   ← ★ 应用 remoteEntry，build_version 与最后成功部署一致
0.6s  GET  /datamigration9000000000000000001/udc-app-entry.aaa16645.js                     ← ★ UDC 应用入口
0.8s  GET  /libs/@seeyon/udc-runtime-core/5.3.143/module.js                                ← ★ 运行时核心
0.8s  GET  /datamigration9000000000000000001/page-entry-qyfapzlb.71bfc39f.js               ← ★★ 按目标页 pageUrl 精确命中的页面入口 chunk
0.9s  GET  /service/datamigration9000000000000000001/udc-runtime/evn-check/build-info/...
1.0s  （随后 UI 转入 ErrPage 资源 ui-ErrPage.9f845be8.js + 错误提示）
3.3s  POST /service/portal/main/query-bulk
```

**DOM 快照（token 有效窗口内）**：`document.title='测试'`、`readyState=complete`、
body 文本含全部门户菜单 + 错误提示 `「[获取应用参数失败] 无权限访问」`+「关闭/刷新页面」按钮。

**判定**：
- `page-entry-qyfapzlb.71bfc39f.js` 被 SPA 按路由参数**精确加载** —— 门户路由把
  `/main/portal/{appName}/{pageName}` 解析后请求了**以 pageUrl 命名的页面入口**，这是路由消费 pageUrl 的**直接行为证据**；
- 应用级服务（`{appName}/udc-runtime/evn-check/build-info`、`{appName}/ctp-parameter/values`）返回
  `HTTP 200 + code=server_403「无权限访问」`（响应体实抓），页面因此渲染错误态，未到列表数据请求。
- **列表行渲染未达成** → 页面可见证据按 BLOCKED 登记（§7）。

### 2.1 无效对照（负样本，LIVE）

同流程直开 `…/qyfapzlbcopy`（镜像外副本页）：网络流只到 SPA 骨架 +
`/service/portal/main/pc-user-info`，**没有任何 remoteEntry / page-entry 请求**
（26 事件 vs 正常链 122 事件；两轮复测一致）。
⇒ 负对照成立：**SPA 对镜像外 pageName 不发起应用级加载**，「发布快照是路由可达的真实门槛」在浏览器行为层成立。
（口径收严，auditor ③ PASS 附注：本结论是 **Redis + 浏览器双观测面一致** —— 同一事实的两个观测面，
**不是两条独立因果证据**；引用时不得写成「独立证明」或「浏览器证明了「发布快照是门槛」。）

## 3. 单账号互踢实录（LIVE，影响后续所有域的取证窗口）

- 23:29 本轮 re-auth 成功后 23:31 导航即遭 `alert('您的账号已在另一个设备上登录')` → 踢回 login；
- 23:37 立即续期并**立即导航**（窗口 <5s）→ 不再被踢，采集成功；
- 结论：**同一账号同时只允许一个有效 web 会话**；任何域的 re-auth 会立刻踢掉其他域正在用的 token。
- 本轮凭据刷新已回写 `shared-credentials/test2-web-credential.json`
  （`refresh_source=ctp-user-login.json re-auth (implementer P3-a …)`），后续域直接用最新 cookie 即可；
- **教训（建议进协议）**：re-auth 后必须「注入→导航→采集」一气呵成，且采集完不要再发会触发互踢的请求。

## 4. 路由消费字段判定（静态主线，LIVE DB+Redis 回读，23:50）

三个候选的反证：

| 候选 | 反证 |
|---|---|
| ❌ 设计态 `page_id` | 运行态 page hash 的 field 与设计态 page_id **24/24 全部不等**（如 qyfapzlb：设计态 `114216775019154694`，运行态 field `7898351679692554562`）。page_id 不出现在任何运行态路由键中 |
| ❌ `udc_function_node.default_page`（单独） | 同一 default_page 页可被多个菜单引用；运行态 24 条记录每个 menuCode 恰好唯一对应一个二级菜单，粒度是「菜单→页」而非「页」 |
| ❌ `udc_function_node.url`（单独） | PAGE 节点 url 与 MENU 节点 url 可同名（xzhpage951440 有 2 MENU + 2 PAGE 共享）；单凭 url 无法区分归属 |

**正向证据（运行态 pageUrl + menuCode 组合）**：

- 设计态 **32 个 PAGE 节点**（`udc_function_node` type=1）中 **25 个 url 在运行态 HIT**（url == 运行态 pageUrl，且该记录的 menuCode 精确等于其所属二级菜单 id，24/24 无一坏引用）；
  > **口径注记（auditor ① 要求，后续引用必须遵守）**：三个数字互不等价，不得混用 ——
  > **32 = PAGE 节点数**（`udc_function_node type=1`）· **31 = 页面数**（`udc_page_info` 行数）·
  > **31 = 去重 url 数**（`COUNT(DISTINCT url)`）。三者差 1 的原因：`xzhpage951440` 有 **2 个 PAGE 节点共用同一 url**。
  > 本节说「32 个 PAGE 节点」口径正确；**不得改口成「32 个页面」**。
- **7 个 MISS = 6 个副本页 + `_deduct`** —— 全部是 2026-10-15 19:29:35（最后成功部署）之后创建的节点，未进发布镜像；
- SPA 行为证据（§2）：路由解析后请求的 chunk 名 = `page-entry-{pageName}`；
- **同名 page_url 的节点分布（实测，不含机制推断）**：`xzhpage951440` 被 4 个节点共享
  （MENU `-4342605165649097565` / `-1628253460115858501`，PAGE `1909192145328011364` / `4630606675502338872`），
  运行态只有**一条**记录 `field=4404482732396528589, caption=小爪实验页面951440, menuCode=-4342605165649097565`。

  > ⚠️ **本节已按 auditor VERDICT（2026-10-18 00:35，② 判 PARTIAL）改写，删去原「后写覆盖」叙事。**
  >
  > **实测（复核确认）**：两个 PAGE 节点 `1909192145328011364`(10-14 12:17:19) 与
  > `4630606675502338872`(10-16 00:44:36) 的 `resource_id` **是同一个** `1520098474917276520`；
  > 而 `udc_page_info` 中 `page_url='xzhpage951440'` **只有 1 行**（同应用内 page_url 重复组数 = 0）。
  > ⇒ **设计态本来就只有 1 份页面数据，运行态 1 条是天然结果。**
  > 严格链条是：4 个节点 → 2 个 PAGE 节点 → **1 个 page_info** → 1 条运行态记录。
  > **从来没有 4 份页面数据**；原「设计态 4:1 / 运行态 1:1」类比会误导成「数据被覆盖丢失」，已删除。
  >
  > **「未进镜像」已能完全解释较晚那个 PAGE 节点**：`4630606675502338872` 创建于 10-16 00:44:36，
  > **晚于部署 10-15 19:29:35**，本来就该不在镜像里。故「覆盖」是**不必要的多余假设**（奥卡姆剃刀），已删。
  >
  > **仍未解释（UNVERIFIED）**：两个 MENU **都早于部署**
  > （`-4342605165649097565` = 10-14 12:17:19，`-1628253460115858501` = 10-14 22:01:07），
  > 运行态 menuCode 指向较早的那个。**为什么两个都早于部署，只有一个进镜像？**
  > 可能机制（同 page_url key 去重 / 发布时按 page_url 建 map 天然只留一条 / 发布顺序）**单时间切片无法区分**，
  > 标注 **UNVERIFIED，不猜**。
  >
  > **归属声明（DRIFT-REVIEW 纪律）**：本组 4 个节点全部是**小爪实验/验收残留，非本域业务产物，仅作旁证**；
  > 其 `masterEntity` = `XzhExp950795`，正是发布阻断的嫌疑实体。⇒ 用这条数据论证「P1 缺陷的运行态放大器」**证据力不足**，
  > 原「撞名覆盖机制」结论**不再成立**，降级为「同名 page_url 的节点分布实测」。

**结论（明确到字段）**：门户运行态路由 = `f(appName, pageUrl, menuCode)`。
URL 形状 `/main/portal/{appName}/{pageName}` 中 `{pageName}` 消费运行态 `PageMetadataDto.pageUrl`，
菜单归属与可达性由 `menuCode`（=设计态二级 MENU 节点 id）决定；`page_id` 与 `default_page` 都不参与路由判定。
（等级：pageUrl+menuCode 为 **LIVE 实测**。⚠ 原文此处写「『后写覆盖』为推断」——该叙事已按 auditor VERDICT 删除（见本节上方），
「两个 MENU 只有 1 个进镜像」的真实机制 = **UNVERIFIED**，不作任何机制断言。）

## 5. P3-b（副本链运行态可达）：BLOCKED，前置=发布

- 复核（23:50 Redis 回读）：`qyfapzlbcopy / qyfapzlbcopycopy / qyfapzxqcopy / qyfapzxqcopycopy / sjypzxxListPagecopycopy / sjypzxxListPagecopycopycopy` 全部 ABSENT；
- 浏览器行为对照（§2.1）：镜像外 pageName 不触发应用级加载；
- 前置依赖：应用须通过一致性检测完成发布——本轮**未触发**（HANDOFF 禁止）；
- 副本对象按 HANDOFF 全部保留（3 副本菜单 + 6 副本页 + P1 空副本，23:55 复核在盘）。

## 6. 工具与脚本

- `implementer/p3a_session.py`：CDP 会话封装（dialog 自动处理 / cookie 注入 / DOM 快照 / 网络流收集）
- `implementer/p3_portal_probe.py`、`p3a_watch.py`：过程探针（保留供复跑）
- 关键技巧：`Page.addScriptToEvaluateOnNewDocument` + localStorage/title 哨兵（dialog 未处理时代的免 evaluate 通道）；`Runtime.consoleAPICalled` 事件流
- Redis 访问需 `protocol=2`（旧版服务不支持 RESP3 HELLO）

## 7. BLOCKED 所需输入（页面可见证据 / P3-b）

| # | 所需输入 | 说明 |
|---|---|---|
| 1 | **有效且不被互踢的 token 窗口** | 九域共用 test-account-1 单账号。需要 main 协调：采集窗口内其他域暂停 re-auth；或为每域申请独立账号（根治） |
| 2 | **沙箱应用服务 403 的解除** | `{appName}/udc-runtime/*`、`{appName}/ctp-parameter/*` 对 test-account-1 返回 `server_403「无权限访问」`（HTTP 200 包裹），portal 服务正常。<br>**归因（已按 auditor VERDICT ④ 收严）**：20 个已注册 UDC 应用中 12 个 `ctp_role_application`>0、8 个=0；4 个已知 200 可访问应用分别 **15 / 10 / 6 / 5 行**，本应用 **0 行**；8 个零行应用里**只有本应用有沙箱（state=1）与运行态镜像（24 页）**，其余 7 个连沙箱都没有。<br>⇒ 「零行 ⇒ 403」在**可比样本内成立**，但**只有 1 个负例，不构成统计显著**。等级 = **强一致证据**，<br>**不得写成「已证机制」**。<br>⚠ 注意 `ctp_role_application.app_id` 是 varchar 存 **appName**，不是数字 id；用数字 id 查会因 `dict.get(k,0)` 默认值把「查不到」伪装成「0 行」（main 00:45 踩过，已撤回）。 |
| 3 | （P3-b）应用通过一致性检测发布 | **门1 主因 = 「一致性检测未通过」11 次 / 20 条**（10-12→10-17，见 §9.4）。`NumberFormatException` 只 **1 次**（10-17 23:43），是**独立第二失败条件**，不是主因。<br>另：02104「枚举不存在」经本轮实测**不成立** —— `expEnum→XzhCtpEnum953322` 在 `ctp_enum` 库内 EXISTS |

## 8. 副作用与边界遵守

- 零设计态写入：未创建/修改/删除任何 UDC 对象；
- 副本对象全部保留（含 P1 空副本 -6340030840568160268）；
- 未触发发布；未重启 Edge；未使用 page-manage child-frame（不再需要——挂死根因已移除）;
- `shared-credentials/test2-web-credential.json` 被本轮刷新 3 次（23:29 / 23:32 / 23:37，均为 token 黑名单或互踢后的续期），已按路径引用纪律操作，secret 未打印；
- 修正 auditr P2 结论 1 条：CDP 挂死根因 = token 失效 alert（见 §1），「page-manage 单页 JS 死锁」不成立。

### 8.1 ⚠ 撤回并更正（原 PROGRESS 中的 ④ 声明，auditor 判 FAIL）

**原文（错，已作废，不得再引用）**：
> 「`{appName}/udc-runtime/evn-check/build-info`、`{appName}/ctp-parameter/values` 对 test-account-1 全部 HTTP200 + server_403，
> **ZZprobe 应用对照同 403，排除单应用问题**。」

**错在哪（auditor 实测，2026-10-18 00:35）**：
`zzprobenew26419954374508955097` 的 `ctp_role_application` 是 **3 行，不是 0 行**；
但它 `udc_application` **无注册记录**、`ctp_sandbox_app` **无沙箱记录**、`udc_page_info` **0**、`udc_function_node` **0**。

**正确表述（以此为唯一版本）**：
> `zzprobenew` 在 `udc_application` **无注册、无沙箱、页面与节点均为 0**，**不是一个可运行态访问的 UDC 应用**；
> 它的 403 属「应用不存在 / 未注册」类，与本应用「已注册 + 已部署沙箱 + 零上架」**不同因**。
> ⇒ **不能作对照，也不能用来「排除单应用问题」。**

**连带影响**：原推断「ZZprobe 同 403 ⇒ 排除单应用问题 ⇒ 只剩账号权限一个方向」**失效**。
403 归因改按 §7#2 的收严表述：**强一致证据（1 个负例），不是已证机制**。

---

# §9 REV7｜运行态镜像 vs 设计态一致性判定（纯 DB/Redis，零 HTTP、零浏览器、零凭据）

> HANDOFF `menu-p3a-mirror-consistency-rev7` · 2026-10-17 23:46–00:05（GMT+8）
> **零写：无 INSERT/UPDATE/DELETE，无 HTTP，无浏览器，无凭据动作。全部 MySQL SELECT + Redis 只读。**
> 取数窗口 **2026-10-17 23:46:48 – 23:59:16**，各条标注具体时刻。等级：LIVE（DB/Redis 实测）· STATIC（javap 字节码）· 推断（明确标注）
> ⚠ 本节**取代** §5 与 §7#3 对 P3 阻断原因的表述（§1–§4 的浏览器侧事实仍然成立，但已不是 P3 结论的主线）。

## 9.0 结论摘要

| 判定项 | 结果 | 等级 |
|---|---|---|
| main 给的三组数字 | **全部独立复现，一致** | LIVE |
| 运行态缺失项 | **7 页 + （P1/P2 全部 14 条复制规则所在的）18 条微流程** | LIVE |
| 门1 阻断是否唯一由两个 xzh 实体引起 | **不能断言唯一**；更精确的根因见 §9.3.3 | LIVE + STATIC |
| 修正 main 一处归因 | `_deduct` 不是「P1/P2 产物」，是 10-15 22:17 的域外系统页 | LIVE |

## 9.1 必做 1：独立复算三组数字（全部一致）

### 9.1.1 部署记录（取数时刻 2026-10-17 23:46:48）

```sql
SELECT id,create_time,state,jar_version,build_version,msg,
       schema_storage_key IS NULL AS sk_null, image_url IS NULL AS img_null, deploy_type
FROM udc_deploy_record WHERE app_id=8704025620829192834 ORDER BY create_time DESC;
```

- 总 **20** 条；`state=1` 成功 **3**，失败 **17**
- 成功清单（与 main 一致）：`8639376853026190261` 2026-10-15 19:29:35 (1.0.14/20261015192931)、`-5773506210473691288` 10-15 15:32:38 (1.0.7)、`-349758333031480854` 10-13 11:29:59 (1.0.7)
- **main 未列出的关键对比**：

| create_time | jar | state | sk_null | img_null | msg |
|---|---|---|---|---|---|
| **2026-10-17 23:43:05** | 1.0.15 | 2 | **1** | **1** | `NumberFormatException: For input string: "...entity.XzhExp950795"` |
| 2026-10-17 22:56:06 | 1.0.15 | 2 | **1** | **1** | 一致性检测未通过（AbstractDeployService.doParallel:242） |
| 2026-10-15 19:23:31 | 1.0.13 | 2 | 0 | 1 | 一致性检测未通过 |

> 增量事实：`schema_storage_key IS NULL` **只**在 10-17 那两次出现；10-15 的失败仍产出了 schema。
> ⇒ 10-17 两次失败在**更早阶段**中止（尚未走到一致性检测/打包），与 NumberFormatException 的位置吻合。
> 这也说明门1 有**两个不同**的失败机制先后出现：先一致性检测（10-15 系列），后 NumberFormatException（10-17）。

### 9.1.2 设计 31 vs 运行 24，缺 7（取数时刻 2026-10-17 23:46:57）

```sql
SELECT id,caption,page_url,create_time,update_time FROM udc_page_info
WHERE app_id=8704025620829192834;   -- 31 行，page_url 唯一，无重复
```
Redis `key = test2:Metadata:Page:datamigration9000000000000000001`（hash），`fields = 24`，**`TTL = 459958s (127.8h)`**（与 main 一致，排除缓存过期）。

| 项 | 值 |
|---|---|
| 设计态 | **31**（page_url 唯一 31，重复组 0） |
| 运行态 | **24** |
| 设计有/运行无 | **7** |
| 运行有/设计无 | **0** |

| 分区（界=2026-10-15 19:29:35） | 数量 | 在运行态 |
|---|---|---|
| create_time ≤ 界 | 24 | **24/24** |
| create_time > 界 | 7 | **0/7** |

| page_url | id | create/update | 归属（**本轮修正**） |
|---|---|---|---|
| `_deduct` | 1636132534412578055 | 10-15 **22:17:10** | ⚠ **非 P1/P2 产物**（最后成功部署之后的域外系统页） |
| `qyfapzlbcopy` | 844278122493924338 | 10-17 15:18:50 | P1 |
| `qyfapzxqcopy` | 3254255197550241742 | 10-17 15:18:50 | P1 |
| `sjypzxxListPagecopycopy` | 1185161788250969507 | 10-17 15:18:49 | P1 |
| `qyfapzlbcopycopy` | 540101808703999634 | 10-17 15:41:03 | P1/P2 |
| `qyfapzxqcopycopy` | 8267428021549491279 | 10-17 15:41:03 | P1/P2 |
| `sjypzxxListPagecopycopycopy` | -8358257041803639157 | 10-17 15:41:03 | P1/P2 |

⇒ P1/P2 的 **6 个复制页 100% 不在运行态**（与 main 一致）。

## 9.2 必做 2：全部 Metadata 类型（本轮增量最大）

### 9.2.1 运行态 Metadata key 全览（取数时刻 2026-10-17 23:47:07）

| Type | items | TTL(s) |
|---|---|---|
| Agg | 85 | 459948 |
| AppService | 115 | 459944 |
| CtpEnum | 372 | 459947 |
| CtpEnumItem | 6197 | 459944 |
| Dto | 884 | 459945 |
| **Entity** | **88**（79 starter 自带 + **本应用 9 个全在**） | 459947 |
| Enum | 341 | 459947 |
| Mq | 115 | 459944 |
| OpenApi | 159 | 459946 |
| **Page** | **24** | 459948 |
| RestApi | 99 | 459949 |
| Service | 2（field=`1.0.14`） | 459945 |
| **MicroFlow** | **0（该 hash 不存在）** | — |

`*:1.0` 别名键内容相同；**MD5 校验键 69 个，值统一 `"1.0.14-20261015193001"`**，与成功部署 `build_version=20261015192931` 对齐。

### 9.2.2 设计态 vs 运行态计数（取数时刻 2026-10-17 23:48:15）

| Type | 运行态 | 设计态 | 说明 |
|---|---|---|---|
| Entity | 88 | 9 | 88 是全局合并视图；本应用 9 个全在 |
| **Page** | **24** | **31** | **缺 7** |
| MicroFlow | 0（无 hash） | **47** | **机制差异，非缺失**（§9.2.3） |
| 其余类型 | 见 9.2.1 | 无一一对应 udc_ 表 | 由镜像 jar 生成，不做表级对照 |

### 9.2.3 ★ MicroFlow 真实形态：按 page_id 分片，不进 Metadata hash

```
test2:Metadata:JSON:MD5:datamigration9000000000000000001:
  udc@...microflow.domain.entity.MicroFlowEntity.json                = "1.0.14-20261015193001"
  udc@...MicroFlowEntity@FRONTEND@114216775019154694.json             = "1.0.14-20261015193001"
  udc@...MicroFlowEntity@FRONTEND@8898789886076928593.json            = "1.0.14-20261015193001"
  udc@...MicroFlowEntity@FRONTEND@7286622650788629332.json            = "1.0.14-20261015193001"
  udc@...MicroFlowEntity@FRONTEND@1805559981642060210.json            = "1.0.14-20261015193001"
  udc@...MicroFlowEntity@FRONTEND@72064815891039882.json              = "1.0.14-20261015193001"
  udc@...MicroFlowEntity@FRONTEND@3062424803371796128.json            = "1.0.14-20261015193001"
  udc@...MicroFlowGroup@SERVICE.json / MicroFlowEntity@SERVICE.json  = "1.0.14-20261015193001"
```

- `@FRONTEND@{id}` 的 id 回查**全是 page_id**：`qyfapzlb`=114216775019154694、`qyfapzxq`=7286622650788629332、`sjypzxxDetailPage`=8898789886076928593、`xzhdetail958033`=1805559981642060210、`rizhixiangqing`=72064815891039882。
- **1 条例外**：`3062424803371796128` 在 `udc_page_info` 已无对应行 —— MicroFlow 分片里的**陈旧镜像残留**（Page hash 里仍是 0 孤儿，两者口径不同，需注意）。
- ⇒ 用「有没有 `Metadata:MicroFlow` hash」判缺失是**错的方法**；运行态微流程按页分片缓存。

### 9.2.4 设计态微流程 47 条，18 条在部署界之后（含 P1/P2 全部 14 条）

| 分区 | 数量 |
|---|---|
| ≤ 2026-10-15 19:29:35 | 29 |
| > 该界 | **18** |

部署后新增 18 条：

| create_time | name / caption |
|---|---|
| 10-16 09:43:31 | xzhMsgBusL1 / 小爪消息总线监听 |
| 10-16 12:18:41 | xzhFinalAllNodes / 小爪标准微流程-全节点流转(最终) |
| 10-16 13:09:50 | xzhFront27390 / 小爪页面规则-全前端节点 |
| 10-16 14:10:45 | xzhStdReal31046 / 小爪标准微流程-真数据全节点 |
| **10-17 15:18:50** | m261017151849772/491/496、151850091/096/101/107 —— 保存/加载数据源信息/选择对应数据源/全量同步/查看日志/保存数据/立即同步（**P1 复制 7 条**） |
| **10-17 15:41:03** | m261017154102850/857/863、154103069/074/078/084 —— 同上（**P2 复制 7 条**） |

⇒ **P1/P2 的 14 条复制规则 100% 不在 1.0.14 镜像内。**
⇒ **这是 REV7 对 P2 定性的实质补充**：P2 验证的 `events[].microFlow → 新规则 id` 重映射，其目标规则在运行态**根本不存在**。
   即便复制页进了镜像，事件也会指向空规则。**P2 = PASS 只在设计态成立；运行态目前不可观测。** 这不是 P2 的错，是门1 的连带后果，但收口口径必须写清，否则会被误读为「运行态已验证」。

## 9.3 必做 3：两个 xzh 实体影响面（并定位真根因，修正 main 的推断层）

### 9.3.1 实体本体（取数时刻 2026-10-17 23:48:33）

| id | name | table_name | entity_group_id | publish | create_time |
|---|---|---|---|---|---|
| `474806313816300867` | xzhExp950795 | `xzhexp950_m1719416608666233204` | `899610436891002621`（默认分组，**仅此 2 个实体**） | 1 | 10-14 12:06:35 |
| `-6338668863907875875` | xzhVerifyEntity | `xzhverify_m8856046371009890617` | 同上 | 1 | 10-14 21:53:33 |

正常业务 7 实体分属 `5350354693552752972`(4) / `5390798299778466729`(3)。属性数：xzhExp950795=**17**，xzhVerifyEntity=**11**。
**两实体都已在 1.0.14 镜像内**（运行态 Entity hash 的本应用 9 实体含 `XzhExp950795`、`XzhVerifyEntity`）。
⇒ 它们**不是**「部署后新增对象」，所以「删掉就能发布」需谨慎：删除本身是写操作且会改变镜像基线。

### 9.3.2 被引用情况（取数时刻 23:48:33 / 23:59:01）

| 引用面 | xzhExp950795 | xzhVerifyEntity |
|---|---|---|
| `udc_page_info` 实体引用 | **3 页**：xzhdetail958006 / xzhpage951440 / xzhdetail958033 | 0 |
| `udc_microflow_info.data_schema` 含**全限定类名** | **7 条微流程** | 0 |
| `udc_page_schema.page_schema` 或 `draft_page_schema` 含全限定类名 | **3 页**（同上） | 0 |
| `udc_attribute` 公式字段 | 0 | 0 |
| CTPENUM 关联 `expEnum → XzhCtpEnum953322`(4456389269786582653) | **枚举 EXISTS**（main 引用的 02104「枚举不存在」**不成立**） | — |

含全限定类名的 7 条微流程：xzhSvcSchcHXa(10-14 17:31:18)、xzhRestMf(10-15 18:18:00)、**xzhStdReal31046(10-16 14:10:45)**、**xzhFinalAllNodes(10-16 12:18:41)**、xzhSvcDefK4Ge(10-14 17:31:17)、xzhSvcEvtBpDA(10-14 17:31:17)、**xzhFront27390(10-16 13:09:50)**。

### 9.3.3 ★ NumberFormatException 的准确抛点（STATIC，javap 实测）

```
javap -p -c udc-biz-5.3.517/com/seeyon/udc/autocode/transport/in/entity/EntityImporterBase.class
```

```java
private EntityBaseDto getNewEntityDto(SchemaStructureDto node, Map<Long, EntityBaseDto> map) {
    if (!isEntitySchemaNode(node)) return null;
    UniformityParams p = node.getUniformityParams();
    String paramId = p.getParamId();          // 直接取字符串
    return map.get(Long.parseLong(paramId));  // ← 825 行：无任何数字校验 → NumberFormatException
}
```

**同类门有保护、唯独这一处没有**：

| 位置 | 代码 | 保护 |
|---|---|---|
| `EntityTransportHandler.lambda$out$1` | `CTPENUM.equals(dt) && NumberUtil.isNumber(rel)` → `NumberUtil.parseLong(rel)` | ✅ |
| `EntityImporterBase.lambda$doImportInfo$8`（filter） | `ENTITY.equals(dt) && isNotEmpty(rel) && NumberUtil.isNumber(rel)` | ✅ |
| **`EntityImporterBase.getNewEntityDto`** | **`Long.parseLong(p.getParamId())`** | ❌ **无** |

⇒ 抛点确定：**公式/事件 schema 的 `uniformityParams.paramId` 存实体全限定类名而非数字 id 时，此处必抛 `NumberFormatException`，消息即 `For input string: "<类名>"`**，与 23:43:05 部署记录 msg **逐字一致**。
（等级：抛点位置 = **STATIC 实测**；「实际抛的就是此处」= **LIVE+STATIC 强一致**：该类是 ENTITY 元数据导入路径上唯一无保护 parseLong 点，且消息形态完全对应。）

### 9.3.4 回答「删掉它能否解阻」

- **不能断言是唯一原因**，但可确定是**必要原因之一**：`XzhExp950795` 被 7 条微流程 + 3 个页面的 schema 以类名引用，这些 schema 正是 `getNewEntityDto` 的输入源。
- **只删实体本体不足以解阻**：7 条微流程 + 3 个页面的 schema 里仍留着类名串，照样会崩。
- 本轮**未删除任何对象**（HANDOFF 禁止写）。

## 9.4 对 P3 因果链的修正

```
[门1] 发布链阻断（主因 = 一致性检测未通过 11 次 / 20 条记录）
       ├─ 段A（10-12 两次，rg冲突=0）：与 relationGroupId 无关，历史 ERROR（03907/02104/03108），现已消除，不复现
       ├─ 段B（10-15 八次，2页共用 rg）：同配置下成功过 2 次 → 原因不是 rg 冲突，未知，不复现
       ├─ 段C（10-17 22:56 一次，3组三方共用）：当前真阻塞，强嫌疑 = P1「relationGroupId 照抄不重映射」累积到第 3 份
       └─ 独立条件：NumberFormatException **1 次**（10-17 23:43）
              = xzhExp950795 全限定类名进入 schema 的 paramId →
                getNewEntityDto 无保护 Long.parseLong（STATIC 已定位，见 9.3.3）
              → schema_storage_key=NULL → 无新镜像
       ⇒ 运行态永远停在 2026-10-15 19:29:35 的 1.0.14
[门2] ctp_role_application 零行（未上架）→ 403（强一致证据，1 个负例，非已证机制）
[P3]  两门串联；门1 未修时即使上架，运行态也没有 P1/P2 的 6 页 + 14 规则
```

### 9.4.1 ⚠ 修正上一版 REV7 的归因次序（本轮自查）

- 全文 20 条部署记录按 msg 分类（取数时刻 **2026-10-18 00:06:01**）：
  **一致性检测未通过 11 · 其他发布失败 8 · NumberFormatException 1 · 成功 3**（11+8+1+3 与 main 一致）。
- 一致性检测失败的完整时点：10-12 18:18:18(1.0.0) / 18:19:33(1.0.1) / 10-15 15:34:55,15:36:53(1.0.8) /
  17:04:22(1.0.8) / 17:09:49(1.0.9) / 17:12:56(1.0.10) / 17:15:44(1.0.11) / 17:19:14(1.0.12) / 19:23:31(1.0.13) /
  10-17 22:56:06(1.0.15)。
- **REV7 上一版的表述问题**：把 `NumberFormatException` 放在门1 主因位置（§9.0 摘要与 §9.4 初稿），
  实际它只出现 **1 次**，而一致性检测 **11 次**。已在上表拆为「主因（11次，分3段）」+「独立第二条件（1次）」。
- **连带撤回**：`xzhExp950795` 创建于 10-14 12:06:35，而一致性检测失败在它创建**之前**就有 2 条（10-12），
  ⇒ **xzh 不可能是「一致性检测未通过」的原因**。9.3.4 中「必要原因之一」的措辞仅对 **NumberFormatException 这一条**成立，
  **不适用于门1 主因**。另：同一 jar 1.0.15 在 47 分钟内两次失败、原因完全不同 → **至少两个独立失败条件**。

## 9.5 REV7 完成标准核对

- [x] 每条数字给 SQL 原文 + 结果 + 取数时刻（9.1.1 / 9.1.2 / 9.2.1 / 9.2.2 / 9.2.4）
- [x] Redis 给 key 全名 + TTL（9.1.2 / 9.2.1 / 9.2.3）
- [x] 运行态缺失清单按类型分组 + 标注是否 P1/P2 产物（9.1.2 / 9.2.4）
- [x] 门1 是否唯一由两实体引起 → **不能断言唯一**，已给「必要原因之一 + 单删实体不足」+ STATIC 抛点
- [x] 结论区分 LIVE / STATIC / 推断
- [x] 零写、零 HTTP、零浏览器、零凭据

## 9.6 REV7 未做 / 未定性

1. 未触发发布、未删实体、未上架（均禁）。
2. 未查 `udc_entity` 之外还有哪些源会把类名写进 paramId（`udc_expression` 表不存在）。
3. `getNewEntityDto` 的调用方（行 174）遍历哪个 schema 集合，静态已读到调用点，完整调用栈未展开（不影响根因定位）。
4. `_deduct` 的真实归属模块未查，仅登记为非本域复制产物。
5. MicroFlow 分片中陈旧 id `3062424803371796128` 在设计态无对应页 —— 登记为镜像残留，未定性。

## 9.7 REV7 副作用登记

**零副作用**：无 DB 写、无 HTTP、无浏览器、无凭据续期。
`p3a_session.py` / `p3a_watch.py` / `p3_portal_probe.py` 按 HANDOFF 要求**本轮未运行**。
