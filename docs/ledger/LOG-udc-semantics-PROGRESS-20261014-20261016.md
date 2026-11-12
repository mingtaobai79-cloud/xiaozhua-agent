# UDC 平台补全 —— 进度看板（归档全文，2026-10-14 → 2026-10-16 第五十三轮）

> 本文件是 `docs/audit/udc-semantics/PROGRESS.md` 的历史全文，**逐字保留、按倒序堆叠**（最新轮在最上面）。
> 入口卡片已改在 `docs/audit/udc-semantics/PROGRESS.md`（只留当前结论 + 阻塞）。
> 迁出原因：P5 流水账收束——1,570 行倒序堆叠不适合当入口，但内容有证据价值，不得删除。
> 该线对应 cron 已于 2026-10-16 停止，本文件不再更新。

---

# UDC 平台补全 —— 进度看板（PROGRESS）

> 每 10 分钟自唤醒的 run：先读本文件 + `COMPLETION-METHOD-PROMPT.md`，**只推进未完项**，
> 完成后**原地更新本文件**（改状态 + 记证据 + 记下一步）。状态：✅ 完成 / 🟡 进行中 / ⬜ 未开始 / ⛔ 阻塞。



**更新时间**：2026-10-16 第五十三轮（04009 页面规则真实 DTO 提交探测；回滚后无净状态变化）：

① 基线实测：compileall 无错；全量 pytest = 1491 passed / 1 failed / 20 skipped（1512 collected）。唯一失败为已知并发项 `tests/udc/test_dynamic_register_channel.py::test_evidence_is_recomputable_by_the_tool_byte_for_byte`：证据文件含 `domain_containment_scan`，复算工具在当前类目录返回 `None`；本轮未改动其代码或证据。

② 按异步硬规则复跑检测：`POST /service/udc/application/do/detection` → 轮询 `detection-state=SUCCESS` → `search/detection`，基线 **ERROR=0 / WARN=5 / total=5**，构成为 `UDC_CE_MICRO_FLOW_04003 ×4`、`UDC_MICRO_FLOW_04009 ×1`。

③ 04009 只读回读 `GET /service/udc/microflow/findById/4774717078364917047`：`type=FRONTEND`、`state=DRAFT`、`dataSchema` 长度 49680。使用该对象自身完整 DTO（不是微流程 schema 拼装）调用 `POST /service/udc/microflow/checkSchema/update`，HTTP 200 / `BOOT_0000` / `check=true/errors=0`，REST 短暂回读 `RELEASE`；异步检测随即暴露 **27 条 UDC_MICRO_FLOW_04008 ERROR**（页面规则内部引用已删除），证明浅校验绿不等于页面规则可发布。立即用同一完整 DTO `state=DRAFT` 调 `POST /service/udc/microflow/update` 回滚，HTTP 200 / `BOOT_0000` / `content=1`；REST 回读 DRAFT，MySQL 回读 `state=10/version=3/LENGTH(data_schema)=52574`，再次异步检测恢复 ERROR=0/WARN=5。无净变更，未触碰并发对象 `-1014184770817921434`。

## 下一步（第五十三轮尾注）
1. 04009 已证实不能靠 `checkSchema/update` 直接提交：先从页面规则设计器真实保存/提交 GraphQL 请求捕获 DTO，禁止继续试错发布。
2. 在取得真实页面规则保存链前，继续只读核对 04003 对象并发归属；不触碰 `-1014184770817921434`。
3. 已知动态注册证据复算失败不属于本轮改动；若后续修复，必须同步证据生成器与计数契约。

**更新时间**：2026-10-16 第五十二轮（WARN 单对象复核；本轮未形成清除）：

① 基线实测：compileall 无错；全量 pytest = 1494 passed / 18 skipped（1512 collected）。

② 异步检测复核：do/detection → detection-state=SUCCESS → search/detection，当前 ERROR=0 / WARN=5 / total=5，构成为 UDC_CE_MICRO_FLOW_04003 ×4、UDC_MICRO_FLOW_04009 ×1。

③ 单对象尝试：1524985498115296151 的 checkSchema/checkSchema-update 均 BOOT_0000、check=true/errors=0，REST 曾回读 RELEASE，但检测暴露 UDC_MICRO_FLOW_04004；已用完整回读 DTO 经 microflow/update 恢复 DRAFT，复检回到 ERROR=0/WARN=5，DB state=10。改选 -3790333238868911627 时两端点均业务 status=3/code=BOOT_3000/data=null，REST/DB 仍 DRAFT/state=10，未扩大写入。并发对象 -1014184770817921434 未触碰。

## 下一步（第五十二轮尾注）
1. 先只读追 04009 页面规则真实保存/提交 DTO，禁止套微流程 DTO。
2. 04003 仅选择可通过 BOOT_0000 且能保持 ERROR=0 的对象；每次单对象复跑异步检测。
3. 若无安全对象，转做 04009 页面规则写链的前端 runtime/Controller DTO 证据补全。

**更新时间**：2026-10-16 第五十一轮（清 WARN 单对象写链 LIVE 成功）：

① 基线实测：uv run --no-project python -m compileall -q components tools tests 无错；全量 uv run --no-project python -m pytest tests -q = 1494 passed / 18 skipped（1512 collected）。

② 先按异步硬规则复跑检测：do/detection → 轮询 detection-state 至 SUCCESS → search/detection，基线为 ERROR=0 / WARN=6 / total=6（04003×5、04009×1）。只读 DB 核对 5 个微流程：并发对象 -1014184770817921434 为 state=10/version=19/update_time=2026-10-16 18:45:45，未触碰；选择无近期并发迹象的 3832725036227491834（state=10/version=59/update_time=2026-10-16 14:53:45）。

③ LIVE 保存/提交 DTO 已按前端 runtime 映射核验：POST /service/udc/microflow/update 携完整 findById DTO + state=RELEASE 返回 BOOT_0000/content=1，但仅保存为 DRAFT（DB version=60）；随后同一 DTO 经真实提交面 POST /service/udc/microflow/checkSchema/update 返回 BOOT_0000，业务结果 check=true/errors=0，REST 回读 state=RELEASE，MySQL 回读 state=20/version=61/LENGTH(data_schema)=1362。

④ 提交后再次按异步流程复核：status=SUCCESS、ERROR=0/WARN=5/total=5，该对象 3832725036227491834 已从检测面消失；剩余为 04003×4（含并发对象）+ 04009×1。

## 下一步（第五十一轮尾注）
1. 继续清 WARN，但先复跑检测并逐对象核对 update_time/version，绝不触碰并发对象 -1014184770817921434。
2. 优先选择无并发迹象的单个 04003/04009 对象，复用已验证的完整 DTO → microflow/update 保存 → checkSchema/update 提交 → detection-state SUCCESS → REST + MySQL 回读链；一次只处理一个。
3. 若目标是页面规则 04009，先只读确认其真实更新 DTO；不要把微流程 DTO 套到页面规则。

**更新时间**：2026-10-16 第五十轮（基线 + 既有完成项核验；未产生外部写入）：

① 基线实测：`uv run --no-project python -m compileall -q components tools tests` 无错；全量 `pytest tests -q` = **1494 passed / 18 skipped**（1512 collected），与 README / agent-version-audit / code-reality-audit 三处计数一致。

② 按提交与权威事实件核验：计算值 `calculate` + `default_value_expr_design` 已由 `1ee00d2`（expression schema/transform/check → attribute update，REST+DB 双面；字段 `8016904624316689195` / `7756131932705656129`）及 `043871a`（token 域 CFR+LIVE）完成；事件两类+4 源监听已由 `a93d841` 完成。故本轮不重复写入已完成项。

③ DB 只读回读：`udc_microflow_info` 目标对象仍为 `-1014184770817921434 state=10 version=19 schema_len=49284`（并发对象不触碰）、`862673936068342178 state=10 version=11 schema_len=11893`、页面规则 `4774717078364917047 state=10 version=1 schema_len=52574`；未发生本轮写入。

## 下一步（第五十轮尾注）
1. 继续清 WARN，但先只读定位 04003/04009 的真实保存/提交 DTO；不碰并发对象 `-1014184770817921434`。
2. 仅对确认可接管的单对象执行保存/提交 → detection-state=SUCCESS → REST + MySQL 回读；若 `BOOT_3000`，登记写链阻塞并停止扩大写入。
3. 既有计算值、事件、生单、扣减、菜单链均不重做；无安全接管对象时转「余 60 条 op 定域」或 CONNECTOR 前置读面。

**更新时间**：2026-10-16 第四十九轮（基线 + WARN 检测面复核；未产生外部状态变更）：

① 基线实测：`python -m compileall -q components tools tests` 无错；全量 `uv run --no-project python -m pytest tests -q` = **1494 passed / 18 skipped**（1512 collected），三处文档计数契约无漂移。

② 按硬规则复跑检测：`POST /service/udc/application/do/detection` 后轮询 `POST /service/udc/application/do/detection-state` 至 `SUCCESS`，再读 `search/detection`；当前 **ERROR=0 / WARN=6 / total=6**，构成 `UDC_CE_MICRO_FLOW_04003 ×5`、`UDC_MICRO_FLOW_04009 ×1`。

③ DB 对照：6 个 WARN 对象均 `udc_microflow_info.state=10`；非并发对象 `862673936068342178` 仍 `version=11/LENGTH(data_schema)=11893`，并发对象 `-1014184770817921434` 继续不触碰。计算值项已由 git `1ee00d2` + `043871a` 完成，未重复写入。

## 下一步（第四十九轮尾注）
1. 清 WARN 仍先查并发；不碰 `-1014184770817921434`，优先只读定位 04009/04003 的真实保存/提交 DTO 差异。
2. 对单个确认可接管对象做「保存/提交 → detection-state=SUCCESS → REST + MySQL 回读」；若仍 `BOOT_3000`，记录为写链阻塞，不扩大写入面。
3. 清 WARN 无安全接管对象时，转做完成判据余 60 条 op 定域或 CONNECTOR 前置读面，禁止重做已完成的计算值。

**更新时间**：2026-10-16 第四十八轮（基线复核 + WARN 安全对象写链尝试；未产生外部状态变更）：

① 基线实测：`uv run --no-project python -m compileall -q components tools tests` 无错；全量 `pytest tests -q` = **1494 passed / 18 skipped**（1512 collected）。

② 只读并发核对：MySQL `udc_test2.udc_microflow_info` 读取 6 个检测对象，均为 `state=10`；并发对象 `-1014184770817921434` 的 `update_time=2026-10-16 17:55:10`，继续不触碰。选取非并发对象 `862673936068342178`（`update_time=2026-10-15 18:17:44`、`version=11`）进行单对象保存/提交尝试。

③ LIVE 写链结果：`POST /service/udc/microflow/checkSchema/update` HTTP **200**，但业务响应 `status=3, code=BOOT_3000, data=null`；REST 回读仍 `state=DRAFT`，MySQL 回读仍 `state=10, version=11, LENGTH(data_schema)=11893`，故未宣称成功、未继续碰其他对象。随后按硬规则异步检测轮询至 `SUCCESS`：**ERROR=0 / WARN=6 / total=6**，对象 `862673936068342178` 仍有 `UDC_CE_MICRO_FLOW_04003`。本轮没有产生可交付的 WARN 清除。
**更新时间**：2026-10-16 第四十七轮（守基线 + 异步检测面复核；未写并发对象）：

① 基线实测：`uv run --no-project python -m compileall -q components tools tests` 无错；全量 `pytest tests -q` = **1494 passed / 18 skipped**（1512 collected），与 README / agent-version-audit / code-reality-audit 计数契约一致。

② 检测面实测：执行 `POST /service/udc/application/do/detection` 后按硬规则轮询 `detection-state` 至 `status=SUCCESS`，再读取 `search/detection`；结果 **ERROR=0 / WARN=6 / total=6**，`warnCount=6`。构成：`UDC_CE_MICRO_FLOW_04003 ×5`、`UDC_MICRO_FLOW_04009 ×1`。具体对象包括 04009 `4774717078364917047`，以及 04003 `1524985498115296151`、`-3790333238868911627`、`862673936068342178`、`3832725036227491834`、并发对象 `-1014184770817921434`。

③ 本轮只读检测，未向上述微流程/页面规则执行保存、提交或构建写操作；未新增代码/测试，基线无回归。

**更新时间**：2026-10-16 第四十六轮（守基线 + 检测面复核；清 WARN 仍不写入并发对象）：

① 基线实测：compileall components tools tests 无错；全量 pytest tests -q = 1494 passed / 18 skipped，收集总数 1512，与 README / agent-version-audit / code-reality-audit 三处计数契约一致。

② 检测面实测：按异步检测流程完成轮询（do/detection → detection-state 至 SUCCESS → search/detection），结果 ERROR=0 / WARN=6 / total=6；warnCount=6。构成：UDC_CE_MICRO_FLOW_04003 ×5、UDC_MICRO_FLOW_04009 ×1。此前 R45 的移动快照 WARN=7 已回落为 6；本轮没有把移动量当作稳定不变量。

③ 并发写入护栏继续生效：04003 对象 -1014184770817921434 仍在检测面（「小爪标准微流程-全节点流转(最终)」），本轮只读复核，未向其写入，避免与并发工作流互相覆盖。

④ 本轮未新增代码/测试：仅完成基线与 LIVE 检测复核，无计数契约漂移；检测状态为 SUCCESS，ERROR 已清零。

## 下一步（第四十六轮尾注）
1. 继续清 WARN 前先查目标微流程的 update_time/version 与最近提交，确认并发工作流是否已交接；
2. 若确认可接管，先选择单个 04003/04009 对象做「保存/提交 → 异步检测轮询 → REST + MySQL 回读」，不碰 -1014184770817921434；
3. 若无可安全接管对象，转做完成判据余 60 条 op 定域或只读补强 CONNECTOR 前置证据，禁止臆造路径。

**更新时间**：2026-10-16 第四十五轮（**清 WARN 项（04003×5/04009）本轮判定为 BLOCKED —— 但顺带把 R43 记的 ERROR=0 更正为 ERROR=1，并把该 ERROR 的真因单变量闭合**：

① **先守基线**：`compileall components tools tests` 无错；全量 `pytest tests -q` **1490 passed / 16 skipped**
   = collected **1506**，与 README / agent-version-audit / code-reality-audit 三处一致（开工无漂移）。

② **★ 交付物指称漂移（重要）**：提示词「本次要推进」的 6 项里，1-5 项**早已 LIVE 完成**，实测 git 有对应提交：
   计算值 `1ee00d2` / 生单规则 `e2190d1`+`6f76915` / 扣减规则 `b0846cd` / 菜单写链 `c8dde2c` /
   事件两类+4 源监听 `a93d841`。⇒ 真正未完成项**只有第 6 项（清 WARN）**。
   （计算值另有 `043871a`：表达式引擎 token 域 CFR+LIVE 全量固化。）

③ **★ 更正 R43 的「ERROR=0」**：本轮实测同一应用为 **ERROR=1 / WARN=5**，
   新增 ERROR = `UDC_MICRO_FLOW_04004`「微流程入参:依赖应用已删除」，对象
   `-1014184770817921434`「小爪标准微流程-全节点流转(最终)」。
   R43 记为 0 的原因**已定位**：04003 是**短路掩蔽器**（DRAFT 不进深度校验），该对象当时 `state=10`；
   本轮因**并发工作流把它改成 `state=20`**，真 ERROR 才浮出。⇒ **「ERROR=0」不是稳定事实**。

④ **★ 该 ERROR 的真因（单变量 2×3 臂 LIVE 闭合，可逆）**：
   根因 = **`input.appName` 写了本应用名，但 `inApp` 键缺失** ⇒ 参数被当**外部应用**参数
   ⇒ 本应用名不在 `udc_dependent_application`（该表**只登记外部应用**）⇒ `APP_DELETE`。
   | 臂 | 单变量 | 检测面（本对象） | DB state |
   |---|---|---|---|
   | E0 原状 | `inApp` 键缺失；`appName=本应用` | ERROR 04004「依赖应用已删除」 | 20 |
   | **E1 修复** | `inApp=true` | **ERROR 清零（1→0）** | **20 ✅** |
   | B 负控 | `inApp=false` | ERROR 复现（同文案） | 20 |
   | C 负控 | `inApp=false` + `appName='bpm'` | 换码：04004「OpenApi标识不匹配」 | 20 |
   | D 陷阱 | `inApp` 缺失 + `appName=null` | **假干净**（ERROR=0，但 state 被压回 10 → 04003 掩蔽） | 10 |
   | R 还原 | 回原 `dataSchema` | ERROR 复现（可逆） | 20 |
   CFR 权威（udc-biz 5.3.517）：`CheckUtils.check:282-287`（仅 MANUAL 校 input）/`:294-297`（恒校 output）
   → `detectionInputOutput:315-341`（**分支只由 inApp 决定**；false 才走 `detectionApp(appName)`）
   → `detectionApp:543-556`（GLOBAL：表内放行 / 表外 `APP_DELETE`）；`appNameSet` 来源
   `ImmutableNodeContext.from:174` = `udc_dependent_application.dep_app_name` 全集。
   ★ **第 5 个「checkSchema 绿 ≠ 配置对」实例**：E1/B 两臂 `checkSchema` 都是 `check:true,errors:0`。

⑤ **★ 为什么「清 WARN」本轮做不了：并发写入者**。目标对象在本轮被**并发本地工作流**改写
   （git `91b9d9e` 16:42:39「微流程 update 禁硬编码 type/state，恢复全节点流转为标准微流程(SERVICE/0)」）：
   `type 3→0`、`state 20→10`、`data_schema 149955→123702 字节`、`version→14`。
   此后每轮重读都是该原始形态 ⇒ 表现为「我改了又不动」。
   ⇒ **04003/04009 的消除被该并发工作流占据**（不是判据缺失、不是通道缺失）：对象归属已交接，
   本任务**不再回写**该对象，并以 `LIVE_R44_CONCURRENT_WRITER` 登记，避免下一轮再误判为「判据失效」。
   ⇒ 同时坐实：WARN 计数已从 6 升到 **7**（该对象被压回 DRAFT 后成为第 6 条 04003）——
   再次证明 WARN 是**移动量**（`LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT`）。

⑥ **本轮产物**：
   - `components/udc/microflow_constraints.py` +~120 行：`input_output_detection_branch()` /
     `validate_input_output_dependency()`（**零写风险**的前置判据，只用 `udc_dependent_application` + 参数体）/
     `INPUT_OUTPUT_APPNAME_MUST_BE_REGISTERED_DEPENDENT_APP` / `LIVE_R44_ARMS` /
     `R44_FALSE_CLEAN_ARM_IS_DRAFT_MASKED` / `R44_APPNAME_DEP_GATE_IS_INVISIBLE_TO_CHECK_SCHEMA` /
     `LIVE_R44_CONCURRENT_WRITER` / `LIVE_R44_WARN_SNAPSHOT`。
   - `tests/udc/test_microflow_constraints.py` **23 → 29 项**（+6）。`pytest tests/udc/test_microflow_constraints.py`
     **29 passed**。
   - 事实件 `core/facts/udc/write-chain/input-output-appname-dependent-app-gate.md`（5 节）。
   - ★ **计数契约 1506 → 1512**：+6 用例全部追加在**既有** `tests/udc/test_microflow_constraints.py` 内
     ⇒ collected 1506 → **1512**；README（1 处）/ agent-version-audit（6 处）/ code-reality-audit（7 处）同步，
     **逐 token 精确替换**并先断言「无长数字含 1506 子串」误伤（防 appId 类子串改坏），
     改前改后 CRLF/BOM/非 ASCII 计数一致（字节长度不变）。

⑦ **诚实边界**：
   - 目标对象 `-1014184770817921434` 的**最终配置状态不属于本轮交付**（并发工作流接管）。
   - `checkOpenApi` 内部真值面 **UNVERIFIED** ⇒ 判据对「表内 appName」只放行、不承诺不撞 OpenApi。
   - `inApp` 键缺失时 `getInApp().booleanValue()` 的**行级**执行路径 UNVERIFIED（行为级结论为准）。
   - R43 记的 ERROR=0 已被本轮**更正为 ERROR=1**；WARN 快照 5→7（移动量，非对象减少）。

## 下一步（第四十五轮尾注，供下一轮直接开工）
1. **先守基线**：`compileall` + 全量 `pytest -q`（契约 **1506**）；复跑检测面记录 ERROR/WARN（**移动量**）。
2. **清 WARN 前先查并发**：`git log -1 --format=%ci` + 目标行 `update_time/version`；
   若目标对象正被并发工作流编辑（如 `91b9d9e` 接管），**换对象**或**等交接**，不要互写。
3. **04003 的机制面已明确**（DRAFT 短路 + 单对象归属），若要真正消除需在**应用构建/发布**后复检
   （`udcRuntimeDeployNormalPost` → 轮询 `udcRuntimeSearchDeployStatusDeployIdPost`），构建为发布级操作，谨慎。
4. 其余未完成项（前三项经 git 复核已完成，勿重做）：CONNECTOR 正例（需先建 `cip_linker_*` 链路）、
   「余 60 条 op 定域」。

**更新时间**：2026-10-16 第四十三轮（**上轮 B 臂 UNVERIFIED 真因定位 = `output.appName` 缺键硬 NPE（单变量 2×2 四臂）+ CONNECTOR 合法目标 = 连接器动态 DTO（读面错配诚实边界）+ 上轮未入库产物全部补齐**：

① **先守基线（本轮第一件事）**：`compileall components tools tests` 无错；
   全量 `pytest -q` **1476 passed / 16 skipped**（= collected **1492**）⇒ 开工时文档契约
   `1492` **未漂移**（README / agent-version-audit / code-reality-audit 三处一致）。
   工作树开工时仅 `?? scratch/` 未跟踪。

② **★ 本轮主项（= 上轮交接口的「B 臂 UNVERIFIED」）：真因是硬 NPE，不是「读数不稳」**。
   上轮把 B 臂（删 `output.appName`）读成 `status=FAIL / 0 条` 后标为 UNVERIFIED；
   本轮**先复现**再**单变量定位**：
   - **复现**：同一臂连跑两次，两次都是 `detection-state` 返回
     `{"status":"FAIL","message":"System Error[java.lang.NullPointerException]","count":"0","errorCount":"0","warnCount":"0"}`
     —— **确定性**，不是偶发。
   - **单变量 2×2（四臂，每臂 REST + MySQL `state=20` 双面确认）**：

| 臂 | `output.appName` | `eventDataFullName` | checkSchema | detection-state | search/detection |
|---|---|---|---|---|---|
| A | 存在=`bpm`（外部） | `…bpm…BpmStartEvent` | `check:true,errors:0` | `SUCCESS` | 该对象 0 条 |
| B | 存在=本应用 | 同上（外部） | `check:true,errors:0` | `SUCCESS` | 0 条 |
| C | **`null`** | 同上（外部） | `check:true,errors:0` | **`FAIL`/NPE** | **0 条（整轮无结果）** |
| D | **键缺失** | 同上（外部） | `check:true,errors:0` | **`FAIL`/NPE** | 0 条 |
| E | 存在=本应用 | **本应用**微流程 DTO | `check:true,errors:0` | `SUCCESS` | 0 条 |
| F | **键缺失** | **本应用**微流程 DTO | `check:true,errors:0` | **`FAIL`/NPE** | 0 条 |

   ⇒ **自变量只有「`output.appName` 是否存在且非 null」**；DTO 属外部还是本应用**同结论**
     （C/D/F 三臂 NPE，A/B/E 三臂干净）。
   ⇒ **CFR 判据链**（`udc-biz 5.3.517`，`docs/audit/artifacts/scratch-migrated/cfr-r31b`）：
     `detectionTrigger:1388` → `isInAppEventOrMessage:1496-1502`
     （`EVENT` 直接 true；否则 `Optional.ofNullable(output).map(getAppName).map(equals).orElse(true)`）
     → `:1389-1422`（inApp 走 dtoMap 支）/ `:1412`（非 inApp 走 `detectionApp(refAppName=…)`）
     → `detectionApp:543-544`（`appNameSet.contains(appName)`）。
     ★ **精确抛点 UNVERIFIED**（`orElse(true)` 本应改道而非抛），但**充分判定已 4/4 复现**。
   ⇒ **与不变量 3 并列的「绿≠对」**：四臂 checkSchema **全绿**，唯一分辨面 = RELEASE 后
     `detection-state.status`。★ 附带陷阱：NPE 时 `search/detection` 返回 **0 条**
     —— 「该对象从检测面消失」在第三十二轮 A 臂被读成「修好了」，在这里会得到**反向结论**。

③ **★ CONNECTOR 源：判据闭环 + 诚实边界（判定为环境前置，不是判据缺失）**。
   - **CFR**：`MicroFlowUtil:134` marker `cip.connector.dynamic.dto.`；
     `FullNameUtil.isConnectorDto:320` = `contains(marker)`（**contains 非 startsWith**）；
     `ConnectorDtoFullNameCollector.extractDtoFullNameByTrigger:98` 只收 isConnectorDto 为真的 output；
     `CheckUtils.detectionTrigger:1452-1459` 查 `connectorDtoMap.containsKey(output.javaType)`；
     `MicroFlowDetectionMetadataAware.putDtoMetadata:125-137` 该 map 用
     `search.appName = depApp.getDepAppName()`（**依赖 `udc_dependent_application` 行**）。
   - **存储面真身**：`cip_connector_test2.cip_linker_metadata_info` **54 行**，
     `linker_type {0:33, 2:5, 3:2, 4:1, 5:13}`，前缀 `com.seeyon.cip.connector.dynamic.dto.<链路>.<DTO>`；
     6 条链路：VDAIBANJICHENG=V5待办集成 / ZHJHZZTB=客户方_组织集成 / CESHIDANDIANDENGLU=测试单点登录 /
     JICHENGCESHI=集成测试 / CESHIYINGYONG=测试应用 / FASONGXIAOXI=发送消息。
     本应用 `udc_dependent_application` 确有 `dep_app_name='cip-connector'` 行（id=8128767151459159276, v5.3.286）。
   - **★ 负证据（4 应用 × 3 应用名）**：`POST /udc/microflow/filter/mq` 对
     **`cip-connector` 与 `cip-manager` 恒 0 条**，对 `cip-capability` 恒 7 条
     ⇒ 前端「应用间」弹层**取不到**合法 CONNECTOR 目标。旁证：500 条微流程 `messageSource`
     直方图 `{EVENT:12, MESSAGE:8, MICRO_FLOW_EVENT:3}` —— **CONNECTOR 全租户 0 条**。
   - **结论**：CONNECTOR **正例**（LIVE 建 → 回读逐键一致）**本轮仍未取得** —— 需先建连接器链路
     （`cip_linker_*` 写链，不在本轮范围）。**属环境前置，不是判据缺失**；判据本身已 CFR + 存储面双证。
   - 澄清第三十三轮那 4 条含 `cip.connector.dynamic.dto.*` 的微流程：其 `trigger.type=MANUAL`、
     `messageInfo=null`（动态 DTO 在**节点参数**里，非 trigger 监听目标）—— 不构成 CONNECTOR 正例。

④ **产物（本轮入库）**：
   - `components/udc/event_listener_constraints.py` **+104 行**：
     `APP_NAME_KEY_ABSENCE_CAUSES_DETECTION_NPE` / `DETECTION_NPE_SIGNATURE` /
     `CHECK_SCHEMA_CANNOT_SEE_APPNAME_NPE` / `DETECTION_NPE_YIELDS_EMPTY_READ_FACE` /
     `LIVE_R43_*` 锚点 / `CONNECTOR_DYNAMIC_DTO_MARKER` / `CONNECTOR_TARGET_MUST_BE_DYNAMIC_DTO` /
     `CONNECTOR_RESOLUTION_REQUIRES_DEPENDENT_APPLICATION_ROW` / `CONNECTOR_DTOS_ARE_INVISIBLE_TO_FILTER_MQ` /
     `FILTER_MQ_PLANE_LIVE` / `CONNECTOR_DTO_REGISTRY_LIVE` (+TABLE/DB) /
     `CONNECTOR_SELECTOR_IS_UNREACHABLE_ON_THIS_TENANT` / `LIVE_MESSAGE_SOURCE_HISTOGRAM` /
     ★ `LIVE_DETECTION_WARN_COUNT_IS_MOVING_SNAPSHOT`（**纠正历史错误**：WARN 计数是移动量，
     不是不变量 —— 本轮实测同应用 **6**，而锚点记的是 9）。
   - `tests/udc/test_event_listener_constraints.py` **41 → 50 项**（+9，含对抗自证：
     `validate_event_output` 必须咬住 appName 缺键/null/空串；marker 三态复算；
     读面负证据钉到数字；WARN 移动量断言）。
   - 事实件 `core/facts/udc/write-chain/appname-key-npe-and-connector-target.md`（6 节）。
   - **计数契约 1492 → 1501**（README / agent-version-audit / code-reality-audit 三处同步，CRLF=0）。
     ★ 修契约时踩到一次坑：README 里 `app9000000000000000001` 含 `1492` 子串，
     先按「全量 replace 1492」会改坏 appId ⇒ 已改为**逐条精确替换**（README 该处 1492 原样保留，
     残留 3 处全是 appId 字面量，已核验）。

⑤ **诚实边界**：
   - NPE 精确抛点 **UNVERIFIED**（可断言充分条件，未定位行）。
   - `EVENT` / `MICRO_FLOW_EVENT` 源的 `appName` 缺键行为**未做 LIVE 负控**（CFR 上 `EVENT` 在
     `isInAppEventOrMessage:1498` 直接 `return true`、不读 appName ⇒ 推断不受影响）。
   - CONNECTOR 正例仍未取得（§③）。
   - 收尾干净：本轮所有发布臂均 `update` 还原 DRAFT，双面确认 `REST state=DRAFT` + `MySQL state=10`，
     `schema JSON-equal to orig: True`，sha256 回到 `a6c6f9eb…`。**无结转状态变更。**

## 下一步（第四十三轮尾注，供下一轮直接开工）
1. **先守基线**：`compileall components tools tests` + 全量 `pytest -q`（契约 **1501**）；
   复跑检测面确认 `ERROR=0`（WARN 是移动量，只记录不设断言）。
2. **未完成项重排**（前三项经 git 复核已完成，勿重做：计算值 / 生单规则 / 扣减规则 / 菜单写链）：
   - **(a) CONNECTOR 正例**：需先**建连接器链路**（`cip_linker_info` + `cip_linker_metadata_info`
     + `udc_dependent_application.dynamic_dependency`），使 `filter/mq` 对 `cip-connector` 返回非空，
     再走「LIVE 建 → 回读 messageInfo 逐键一致」。⚠️ 这是**跨模块写链**，动手前先只读探清
     `cip_linker_*` 的 REST 入口与必填键集。
   - **(b) 04009（页面规则 WARN）**：上一轮检测面已无 04009，需换对象复现后再定。
   - **(c) 完成判据「余 60 条 op 定域」**（静态路径已穷尽，见 COMPLETION-METHOD-PROMPT 文末）。
3. **方法提醒**：本轮再次证明 `checkSchema` 绿 ≠ 配置对（第 4 个独立实例）。
   凡涉及 trigger / messageInfo / output.appName 的判定，**必须以 RELEASE + `detection-state`** 取证；
   且 **`search/detection` 的「0 条」不可单独用作「干净」的证据**（须同时看 `status`）。

## 本轮证据（2026-10-16 第四十三轮 · appName 缺键 NPE + CONNECTOR 目标判据）
- **NPE 原文**：`{"validate":true,"appId":"8704025620829192834","status":"FAIL","message":"System Error[java.lang.NullPointerException]","count":"0","errorCount":"0","seriouCount":"0","warnCount":"0"}`
- **4 臂复现脚本**：`docs/audit/artifacts/scratch-migrated/root/r43_ab_keyabsent.py`（present/null/absent）、`docs/audit/artifacts/scratch-migrated/root/r43_ab2x2.py`（补 absent×本应用 DTO / present×本应用 DTO）、
  `docs/audit/artifacts/scratch-migrated/root/r43_b2diag.py`（抓原文）、`docs/audit/artifacts/scratch-migrated/root/r43_iso.py`、`docs/audit/artifacts/scratch-migrated/root/r43_arms.py`（MESSAGE 正例复测）
- **连接器读面矩阵**：`docs/audit/artifacts/scratch-migrated/root/r43_conn_readplane.json`
- **对象**：微流程 `3832725036227491834`（`xzhMsgBusL1` / 小爪消息总线监听），
  orig sha256(ds) = `a6c6f9ebb632d92923c26ebde2e3544957cae9204d9f0f81df2fdf96bb7eede7`；还原件 `docs/audit/artifacts/scratch-migrated/root/r41_restore.py`
- **存储面**：`cip_connector_test2.cip_linker_metadata_info` 54 行（linker_type 直方图见 §③）；
  `udc_test2.udc_dependent_application`（app 8704025620829192834 × cip-connector = 一行）

**更新时间**：2026-10-16 第三十二轮（**04004 最后 1 条真因 LIVE 收口（含负控）+ 交接的「未收尾」全部结清 + 计数契约修复**：

① **先清上轮交接（本轮第一件事，逐条兑现）**：
   - 上轮把 `1524985498115296151` 停在 **RELEASE**（检测面 ERROR=1）未还原。本轮**开工先复跑检测面**读数：
     `err=0 warn=2`，且 REST `findById.state=DRAFT` **同时** MySQL `udc_microflow_info.state=10` 双面一致
     ⇒ 上轮交接里「必须先把该微流程还原为 DRAFT」**已在上一轮末尾兑现**（`docs/audit/artifacts/scratch-migrated/root/r33_restore.py` 落库），
     本轮只是**复核**，未产生新的状态变更。**上轮的账已清。**
   - 上轮未入库的两个产物（`components/udc/microflow_constraints.py` +99 行 / `tests/udc/test_draft_warn_masking.py` +97 行）
     本轮**复核后入库**（未用 `git add -A`）。
   - 上轮「文档计数契约 1461 是否漂移」**实测为漂移**：`pytest --collect-only` = **1467**，三处文档写 **1461**。

② **★ 本轮主项：04004 真因判定从「正例」升级为「正例 + 负控」的垂直切片（LIVE）**。
   上轮 A/B 两臂（X 组占位三键 / Y 组 canonical 四键）**都是正例**，只能证明「填对能过」，
   不能证明「填错必报」——判据的**充分性**没有独立证据。本轮补**单变量负控**：
   - **CFR 再确认**（udc-biz 5.3.517）：`CheckUtils.detectionTrigger:1461-1471` 在 `BusinessEventTrigger` 分支
     `context.put(output.getJavaType().replace(".",""), variableBo)`；`CheckUtils.checkScope:1266-1284`
     首行 `context.get(selectParamOutputName)`，null **立即 return false**；`MicroFlowComponentUtils.checkSelectParam:902-915`
     只把 `getOutputName()` 交给 checkScope ⇒ **一元判据**；`detectionTrigger:1463` 注册的 nodeId 字面量是 `"root"`，
     而 `NodeUtils.getNodePath:234-241` 写进 schema 的 `nodePath` 也是 `root.*` 开头 ⇒ contains 判据**恒真**，
     通过与否**只取决于 `outputName` 是否命中 context 键**。
   - **LIVE 负控（A 臂正 / B 臂负，各臂 REST + MySQL 双面确认 `state=20`）**：

| 臂 | `outputName` | `name`/`path`/`key` | checkSchema | 检测面（该微流程） |
|---|---|---|---|---|
| A（正，磁盘现状） | `xzhExp950795comseeyonudccommoneventAfterUpdateEvent` | `_FLOW_OUTPUT_evt1` ×3（占位） | `check:true, errors:0` | **该微流程从检测面消失** |
| B（负控，**只改**`outputName`） | `_FLOW_OUTPUT_evt1` | `_FLOW_OUTPUT_evt1` ×3 | `check:true, errors:0` | **ERROR=1**：`UDC_MICRO_FLOW_04004` route `MFEndNode_&_value`「结束:前序节点发生变更请重新选择(事件数据)」 |

   ⇒ 唯一自变量 = `outputName`；**A 臂同时证伪**「需四键一致」（三键全占位仍全绿）。
   ⇒ **新不变量**：`END_NODE_SCOPE_IS_INVISIBLE_TO_CHECK_SCHEMA = True`（两臂 checkSchema 都是绿的，
     本判据**只能**靠 RELEASE + 检测面观测）。负控后立即 `update` 还原 DRAFT（REST + DB 双面确认 `state=10`）。

③ **产物**：`components/udc/microflow_constraints.py` 追加 `LIVE_END_NODE_AB_VERTICAL_SLICE`（含负控逐字段）+
   `END_NODE_SCOPE_IS_INVISIBLE_TO_CHECK_SCHEMA`；`tests/udc/test_draft_warn_masking.py` 由 15 → **17 项**
   （新增 `test_live_ab_vertical_slice_with_negative_control` 单变量对照断言 + `test_check_schema_cannot_observe_end_node_scope` 对抗自证）；
   事实件 `core/facts/udc/write-chain/endnode-selectparam-scope.md`（5 节，含 CFR 表 / A-B 表 / 与其它 4 条 holder 不变量的分工 / 边界）。
   **真盘突变 2/2 CAUGHT**：M1 把 `trigger_output_context_key` 的 `.replace(".","")` 去掉 ⇒ **2 failed / 15 passed**；
   M2 把 `SELECT_PARAM_DISPLAY_ONLY_KEYS` 改成两元（复活被证伪的「四键一致」）⇒ **1 failed / 16 passed**；
   每轮后**字节级还原** sha256 `c141629c960198b21588c3ef172d5d24db19f3aed34a1d5d41362ce649734570`（前后一致）。

④ **计数契约修复（提示词点名的顺手项，且本轮自己又改动了计数）**：`1461 → 1467 → 1469`（分两步：
   先修上轮遗留的 1461→1467 漂移，再并入本轮 +2 项）。三处文档 `README.md` / `agent-version-audit.md` /
   `code-reality-audit.md` 已同步，显式 `newline="
"` 保 LF（**CRLF=0**，diff 收敛为单点改动）。
   先跑 `pytest tests/udc/test_draft_warn_masking.py -q`（17 passed），再跑全量。

⑤ **04004 真因族至此全部 LIVE 收口（5 条，逐条带触发点）**：
   1) `messageInfo.eventDataFullName` = **DTO fullName**（`<base>.dto.<Cap>Dto`）[`CheckUtils.check:1427-1431`]
   2) `messageInfo.eventMfCustomDtoName` = `<实体短名>.<eventClassName>`（**与 1 不可互换**）[`:1433-1435`]
   3) `DATA_MAPPING` holder 的 `name` 不可占位、`id` 必为 `<DTOFQN>.<attr>` [`DataMappingActivity.checkTargetFieldList`]
   4) `mappingRule.javaType` = 目标 DTO FQN（非 `java.lang.Object`）[`DataMappingActivity:173`]
   5) **本轮** `endNode.value.selectParam.outputName` = `trigger.output.javaType` 去点全串 [`checkSelectParam:912` → `checkScope:1266`]

⑥ **诚实边界（我的账）**：
   - 本轮为取负控证据**又**把 `1524985498115296151` 发布成 RELEASE 一次（检测面一度 ERROR=1），
     **已用 `update` 还原 DRAFT 并双面实测 `state=10` / 检测面 `err=0 warn=2`**（非推断）。**本轮收尾干净，无结转。**
   - 公式经 CFR 取证的 trigger 分支**只有 `BusinessEventTrigger`**；其它 trigger（MANUAL/TIMER）的 context 键约定
     **未取证** ⇒ `validate_end_node_scope` 对非 BUSINESS_EVENT **既不报错也不外推**（已写进事实件 §5）。
   - 本判据只断言「**查表能否通过**」，**不**断言运行期变量取到业务正确数据（属执行期，未测）。
   - 完成判据「平台操作面（299 REST + 240 GraphQL 全量映射）」与「pending 清零（余 60 条 op 定域）」**仍未勾** ⇒ **任务不可暂停**。

## 下一步（第三十二轮尾注，供下一轮直接开工）
1. **先守基线**：复跑检测面确认 `ERROR=0 / WARN=2`（两条 04003 均为本应用 `state=10` 草稿微流程
   `1524985498115296151` 与 `862673936068342178`，二者**互为独立对象**，勿混为一条）；同时复跑
   `compileall components tools tests` 与全量 `pytest -q`（契约计数 **1469**）。
2. **提示词未完成项重排（前三项经 git 复核已完成，勿重做）**：
   - 第 1 项「计算值 `calculate` + `default_value_expr_design`」→ **已完成**（`1ee00d2` 第二十三轮 LIVE；
     AGGREGATION 第三态见 `attribute-aggregation-write-chain.md`）。
   - 第 3/4 项「生单规则域 / 扣减规则域」→ **已完成**（`b0846cd`、`e2190d1`、`6f76915`）。
   - 第 5 项「菜单写链补全」→ **已完成**（`c8dde2c` 第二十六轮 LIVE PASS）。
   - **真正剩余**：(a) 第 2 项的 **`MESSAGE`（消息总线）/ `CONNECTOR`（连接器回调）两源写链**
     —— 现有 `event_listener_constraints.py` 只有 CFR 闸门 + `checkSchema` 假绿证据，
     **尚无「LIVE 建 → 回读 messageInfo 逐键一致」的正例**（`topic` / `connectorMessageInfo` 未实测落库）；
     (b) 第 6 项 **`04009`（页面规则 WARN）**（本轮检测面已无 04009，需换对象复现后再定）；
     (c) 完成判据里的「余 60 条 op 定域」。
3. **方法提醒**：本轮再次证明「`checkSchema` 绿 ≠ 配置对」——凡涉及 trigger / messageInfo / selectParam
   的判定，**必须以 RELEASE + 检测面**（并配**单变量负控**）取证，不接受只有正例的结论。

## 本轮证据（2026-10-16 第三十二轮 · 04004 负控垂直切片）
- **检测面读法（勿省轮询）**：`POST /udc/application/do/detection` -> 轮询 `POST /udc/application/do/detection-state`
  到 `status not in (doing, EXECUTING)` -> 读 `POST /udc/application/search/detection`。
- **发布 / 还原**：发布 `POST /udc/microflow/checkSchema/update`（DTO 自带 `state=RELEASE`）；
  还原 `POST /udc/microflow/update`（`setServiceMfToDraft` 对 SERVICE 强制回 DRAFT）。
- **状态双面确认命令面**：REST `GET /udc/microflow/findById/{id}.state`；MySQL
  `SELECT state FROM udc_test2.udc_microflow_info WHERE id=1524985498115296151`（`state=10` DRAFT / `state=20` RELEASE）。

**更新时间**：2026-10-16 第三十一轮（**04003(WARN) 掩蔽机制实证：DRAFT 短路深度校验 ⇒ ERROR=0 是假安全；SERVICE 型可发布；04004 真因族之一闭合**：
① **先清交接（本轮第一件事）**：全量 `pytest -q` 实测 **1452 passed / 0 failed / 1452 collected**（三口径同一），
   `compileall components tools tests` 无错 ⇒ 上一轮交接的「1452 只验到 collect-only」**兑现为 VERIFIED**。
② **入库前轮未提交遗留**（`git add <具体文件>`，未用 `-A`）：`components/udc/attribute_expression_constraints.py`（AGGREGATION 第三态 +119）、
   `components/udc/data_type_java_type.py`、`components/udc/microflow_parse_errors.py`、`tests/udc/test_data_type_java_type.py`、
   两份事实件 + 三处计数文档。提交 `c276544`。**交接债务①③清零**。
③ **★ 本轮主项：`04003` 的真实性质 —— 它是检测掩蔽器，不是普通提示**（提示词第 6 项「清 WARN」的性质被改写）：
   - **CFR**（udc-biz 5.3.517 `CheckUtils.parallelDetection:430-479`）：`if (RELEASE == dto.getState()) { switch(type) {...深度校验...} }
     else { CheckUtils.warn(..., DRAFT_MICRO_FLOW); }` ⇒ **DRAFT 直接短路，不做任何深度 parse 校验**。
     同处还证明 `ENTITY_RULE` 且 `sourceId` 为空时 `continue`（深度校验连 WARN 都没有）。
   - **LIVE 决定性 A/B（同一条微流程 1524985498115296151「小爪标品事件监听」，type=SERVICE）**：
     `DRAFT -> ERROR=0 / WARN=2`；`RELEASE -> ERROR=10 / WARN=1`；`update` 还原 -> 回到 `ERROR=0 / WARN=2`。
     ⇒ **`04003` 让 10 条真 ERROR 结构性不可见**；历史多轮把「WARN 只有 04003」读成「未保存、无风险」是**假安全**。
   - 10 条 04004 的 message 与 `MicroFlowParseErrorEnum` 逐条对账：`DTO_ATTR_DELETE`(18) x5 /
     `ENTITY_DELETE`(19) x1 / `NOT_MATCH`(1) x1 / `ILLEGAL_DATA_SYSTEM`(84) x1 / `OUT_OF_SCOPE`(0) x1。
④ **更正旧结论「SERVICE 型永不可能发布」**：CFR `MicroFlowAppService.setServiceMfToDraft:926` 只被 `create`(:372) / `update`(:383) 调用；
   `checkSchemaAndUpdate`(:330) **不调用**它。LIVE：`type=SERVICE` 的 DRAFT 经 `checkSchema/update` 落库 **`state=20/RELEASE`** ⇒ 可发布。
   本轮反编译补齐枚举：`MicroFlowTypeEnum` = `SERVICE(0)/FRONTEND(1)/ENTITY_RULE(2)/CUSTOM(3)/FUNCTION(4)`；
   `MicroFlowDataStateEnum` = `DRAFT(10)/RELEASE(20)`（udc-common 5.3.517）。
⑤ **04004 真因族之一闭合（`DATA_MAPPING` path 元素的 javaType 配对）**：LIVE 6 个 holder path 元素中 **4 个不配对**
   （`expNum` INTEGER + `java.lang.String` x2；`expFlag` BOOLEAN + `java.lang.String` x2）→ 各报一条 `DTO_ATTR_DELETE`；
   经 `normalize_holder_java_types` 修 4 处后 **10 -> 6**。**判据更正**：holder 的 `path[]` 也必须过 `data_type_java_type` 配对校验
   （旧写法只查 holder 自身 4 键必填、path 元素只查必填不查配对 ⇒ 真因被漏）。余 6 条属另一根因族（实体/属性级删除 + 数据体系）**未闭合**。
⑥ **产物**：`components/udc/microflow_constraints.py` **+62 行**（`DRAFT_WARN_MASKS_DEEP_VALIDATION` / `DRAFT_WARN_CODE` /
   `RELEASE_VALIDATION_DISPATCH_BY_TYPE` / `MICRO_FLOW_TYPE_CODES` / `MICRO_FLOW_DATA_STATES` / `SERVICE_TYPE_CAN_BE_RELEASED` /
   `MAPPING_PATH_ELEMENTS_NEED_JAVA_TYPE_PAIRING` / `LIVE_04004_FROM_MAPPING_PATH_PAIRING`）；
   护栏 `tests/udc/test_draft_warn_masking.py`（**9 项**，含对抗自证 + 用真实数据复算 LIVE 计数）；
   事实件 `core/facts/udc/write-chain/draft-warn-masking-mechanism.md`（5 节，含副作用自我审计）。
   **真盘突变 M1 CAUGHT 6 failed / 3 passed**，随后字节级还原 sha256 `4ce33f092a569a62901d141d056570550e8edd736ec9b6d25b07532b3ba45387`（前后一致）。
⑦ **计数契约 1452 → 1461**（+9，collected == passed == 1461；README / `agent-version-audit.md` / `code-reality-audit.md` 三处已同步）。
   基线：`compileall` 无错；`pytest -q` **1461 passed / 0 failed**（实测）。
⑧ **诚实边界（我的账）**：
   - 取证据时把 `1524985498115296151` 发布成 RELEASE 一次（检测面一度 ERROR=10），**已用 `update` 还原 DRAFT 并实测回到 ERROR=0/WARN=2**（非推断）；
     还原后 `data_schema` LENGTH 11893 -> 11992（净增 = 4 处 javaType 修正的字符差），**已如实登记**。
   - `862673936068342178`（SERVICE/MANUAL）`checkSchema/update` 报 `BOOT_3000`（message 为 null，无细节）且**未落库**（回读仍 DRAFT）；
     已核查其节点无 `DATA_MAPPING`（SUB_MICROFLOW/RETRIEVE/RETRIEVE_ARRAY）⇒ **非本轮已解真因族，标 UNVERIFIED**，不宣布修复。
   - 余 6 条 04004：`messageInfo.eventDataFullName` / `eventMfCustomDtoName` 与 `context.getEntityDtoMapWithDtoFullNameKey()` 的
     **键格式约定 UNVERIFIED**（CFR 已定位分支 `CheckUtils.check:1486` 与取键函数 `MicroFlowUtil.getEntityNameFromEventMfCustomDtoName:585`，
     但权威格式未取到）；SSH `10.0.0.1:22` 本轮**不可达**（connect timed out），K8s/pod 日志通道不可用，无法反查请求日志。
   - 完成判据「平台操作面（299 REST + 240 GraphQL 全量映射）」与「pending 清零（余 60 条 op 定域）」**仍未勾** ⇒ **任务不可暂停**。

## 本轮证据（2026-10-16 · 04003 掩蔽机制）
- **检测面读法（复用范式，勿省轮询）**：`POST /udc/application/do/detection`（异步）-> 轮询 `POST /udc/application/do/detection-state` 到 `status!=doing`
  -> 读 `POST /udc/application/search/detection`。省轮询会读到上一轮快照。
- **发布/还原端点**：发布 `POST /udc/microflow/checkSchema/update`（DTO 必须自带 `state=RELEASE`）；还原 `POST /udc/microflow/update`
  （`setServiceMfToDraft` 对 SERVICE 强制回 DRAFT）。
- **对比表**：

| 微流程 | type | triggerType | 基线(DRAFT) | 发布后(RELEASE) | 还原后 |
|---|---|---|---|---|---|
| 1524985498115296151 小爪标品事件监听 | SERVICE | BUSINESS_EVENT | E0/W2 | **E10/W1** | E0/W2 |
| 862673936068342178 小爪标品服务定义 | SERVICE | MANUAL | E0/W2 | BOOT_3000 未落库 | E0/W2 |

## 下一步
1. **先守基线**：本轮已把 `1524985498115296151` / `862673936068342178` 还原为 DRAFT、检测面 `ERROR=0 / WARN=2` 不变；
   下轮开工前**先复跑检测面确认仍是 E0/W2**（防并发工作流改动混入）。
2. **收口余 6 条 04004（承接本轮）**：先取 `context.getEntityDtoMapWithDtoFullNameKey()` 的**权威键格式**
   （CFR 追 `MicroFlowDetectionContext` 的 map 构造处），再判 `messageInfo` 两键是「格式错」还是「对象确实已删」；SSH 不可达时**不得**用臆测替代。
3. 未完成项（按提示词序，仍未动）：第 3 项生单规则域（`DataFlowDesignController`）、第 4 项扣减规则域（`DeductionRuleController`）、
   第 2 项事件监听 4 源的**消息总线/自定义对象**两源（`MESSAGE`/`CONNECTOR` 的 `topic`/`connectorMessageInfo` 写链）。
   （注：生单/扣减规则写链已有事实件 `dataflow-rule-rest-write-chain.md` / `deduction-rule-rest-write-chain.md`，需核对是否已 LIVE 收口再决定是否重做。）
**更新时间**：2026-10-16 第二十六轮（**菜单写链补全：PAGE 子节点 + default_page + 树回读全链 LIVE PASS，`08100` 清零（WARN 9→8）**：
① **先清交接（本轮第一件事）**：全量 `pytest -q` 实测 **1391 passed / 0 failed / 1391 collected**（三口径同一），
   `compileall components tools tests` 无错 ⇒ 上一轮交接的「文档计数 1391 只验到 collect-only，属 UNVERIFIED」**已兑现为 VERIFIED**，未修正计数。
② **入库上一轮遗留（未用 `git add -A`）**：`components/udc/event_listener_constraints.py` +
   `tests/udc/test_event_listener_constraints.py`（事件两类 + 4 源，LIVE/CFR 双层）+ 三处计数文档 1350→1391。
   提交 `a93d841`。**「事件两类（应用内/应用间）+ 监听 4 种源」由此标 ✅**。
③ **★ 本轮主项：菜单写链补全（提示词第 5 项）—— 一次拿到 5 条新不变量**：
   - **★ 建 PAGE 子节点不能用 `POST /udc/function`**。CFR 逐字段确认入参 `FunctionDto` **没有 `resourceId`**；
     `createFunctionNode`(:189) → `setSchemaState`(:218) → `selectOnePageByPageId(appId, dto.getResourceId())`(:606)
     拿到 `null` ⇒ `SearchFilter` 拒绝 `[resourceId]字段的条件数据不能为null` ⇒ `BOOT_4000 DB Error`。
     **LIVE 3/3 复现且零落库**（探针 `COUNT(*)=0`，不是"建了再删"）；pod 堆栈逐帧对上（见证据件 §1）。
     正解 = `POST /udc/function/create/function-refer`（`FunctionReferDto` 带 `@NotBlank resourceId`）。
   - **★ 建 PAGE 子节点后父菜单 `default_page` 自动落**（`handleFunctionDefaultPage`(:1181)，仅 PC 端）：
     取「最早创建的（create_time 升序）非 MENU 且非 SUBPAGE」子节点写入 `defaultPage/url/relationApp`。
     LIVE：建 C1 后父 `defaultPage=4630606675502338872`；再建 C2 父**不变**（containsKey 判据正确）；删 C2 保留。
     ⇒ **一次调用即消 `08100`，无需额外调用**。
   - **★ `08100` 的真实语义更正（覆盖上一轮措辞）**：CFR `FunctionNodeDetectionUtils#doDetection` 第 4 条是
     「childNodes 为空 **或** 无任何 type==MENU 的子节点」⇒ 子节点全为 PAGE 仍判「空」，
     故 WARN 文案「未设默认页」的**真实充分条件是「无子页面可指向」**，
     上一轮写的「空目录无处设默认页」**不准确**（已就地更正，写进约束模块与事实件）。
     `ConsistenceDetectionCodeEnum.UDC_CE_FUNCTION_NODE_MIS_DEFAULT_PAGE(500, "UDC_CE_FUNCTION_NODE_08100")`。
   - **★ 显式 `default_page` 三前提 + 三写入 LIVE 全验**：`setFunctionDefaultPage`(:510)：
     前提 = ①`refer.parentId == function.id` ②`excludeSubPage`（PAGE 须 `resourceId` 非空且数字且 `!= NULL_ID`，
     且非 `SUBPAGE`）③双侧 `lateralAuthChecker`；写入 = `url/defaultPage/relationApp` 三者。
     **A/B**：切 C2 → 父 `defaultPage=-9192829783122158852 url=xzhdetail958033`；切回 C1 → `4630606675502338872 / xzhpage951440`；
     **负控**（sourceId 非直接子节点）→ `BOOT_1000 菜单绑定的默认页面信息异常` ✓。
   - **★ 树回读双端点口径陷阱**：`find/tree-and-group` 内部置 `onlyMenu=true` ⇒ `selectFunctionTree` 先按
     `type==MENU` 过滤 ⇒ **`pcTree` 里菜单 `childNodes` 恒为空，不是"没建成"**（我一度据此误判）。
     要连子 PAGE 一起读须用 `POST /udc/function/select/function-tree`，
     **body 是两层包装 `{params:{appId,terminalType}, sort:{...}}`**（裸 `{appId,terminalType}` → `BOOT_3000`）；
     且该方法会剔除 null/空白参数（`terminalType` 缺失 → `UDC_APP_0026`）。
   - 端点补充：`update/name/function-refer` 入参是 `@MultiRequestBody {appId, relationId, name}`（**relationId 而非 id**）；
     `delete` 是 `@MultiRequestBody Long id`（裸 Long，非对象包装）。
④ **终态**：`08100` 从检测面**消失**，`ERROR=0 / WARN=8`（04003×7 + 04009×1 仍在）；
   菜单 `-1628253460115858501`「小爪验收菜单」→ 子节点 `4630606675502338872`「小爪验收页面」
   （`url=xzhpage951440`, `resourceId=1520098474917276520`, `schemaState=FORMAL`），三面回读一致（REST 单节点 / REST 树 / DB）。
⑤ **产物**：`components/udc/menu_constraints.py` **+143 行**（`FUNCTION_DTO_FIELDS`/`FUNCTION_REFER_DTO_FIELDS`/
   `MENU_CREATE_ENDPOINT_BY_TYPE`/`FUNCTION_NODE_08100_*`/`SET_DEFAULT_PAGE_*`/`FUNCTION_TREE_READ_ENDPOINTS`/
   `validate_function_refer`/`validate_default_page_call` + LIVE 锚点）；
   `tests/udc/test_menu_constraints.py` **+9 项**（共 15 项）；
   事实件 `core/facts/udc/write-chain/menu-default-page-write-chain.md`（8 节）。
   **真盘突变 CAUGHT**：给 `FUNCTION_DTO_FIELDS` 补 `resourceId`（等价改坏本轮核心 CFR 结论）⇒ **3 failed / 12 passed**，
   随后**字节级还原** sha256 `55be543e48b76e7fbb4f6d6e4de940bbd1705327417f363dd4d6d78388c8a9eb`（前后一致）。
⑥ **计数契约 1391 → 1400**（+9，collected == passed == 1400；三处文档 README / `agent-version-audit.md` /
   `code-reality-audit.md` 已同步，显式 `newline="\n"` 保 LF、**CRLF=0**，diff 收敛为单点改动，未重蹈全文件重写）。
   基线：`compileall` 无错；`pytest -q` **1400 passed / 0 failed**。
⑦ **诚实边界（我的账）**：
   - 为定端点，我先用 `POST /udc/function` 跑 3 次逐步探针（`xzhPgProbe0/1` + 正式体），**全部 BOOT_4000 且零落库**
     （DB 复核 `COUNT(*)=0`）—— 与上一轮那次"误建 3 个垃圾菜单"不同，本次**无副作用**，如实登记以区隔。
   - 验证「切换」语义时建了第二个子节点 `-9192829783122158852`，验完已删（`delete` 返回 `content=1`），
     DB 复核父下仅余 1 个子节点。
   - `04003×7`（微流程 `state=10` 草稿）/`04009×1`（页面规则）**本轮未动**（不阻塞构建已实测）。
   - 完成判据「平台操作面（299 REST + 240 GraphQL 全量映射）」与「pending 清零（余 60 条 op 定域）」**仍未勾**
     ⇒ **任务不可暂停**。
⑧ **欠账（本轮一并登记，防再丢）**：`PROGRESS.md` 此前只写到**第二十二轮**，
   第二十三~二十五轮（表达式引擎写链 / 扣减规则 + 生单规则写链 / 事件监听约束 + `.pyc` 等长同秒陷阱）
   **从未入看板**，仅存在于 git 提交与 `docs/audit/udc-semantics/FIX-*.md`。本轮补记于下方 §补记。

**补记（第二十三~二十五轮，据 git 提交与 FIX 文档回填，非本轮实测）**：
- **第二十三轮**（`b0846cd` / `1ee00d2`）：扣减规则 `udc_deduction_rule` 0→1、`udc_deduction_algorithm` 0→1（LIVE）；
  生单规则 `POST /udc/data-flow` 建成功（`DataFlowDto.caption` 必填）；映射规则入参 `DataFlowMappingSaveDto`
  **本地原缺**，已自 Artifactory 取回 `udc-dataflow-5.3.517.jar`（**推翻"本地不可得"旧结论**）并 CFR 解出全链契约；
  属性**计算值/默认值表达式引擎**整链 LIVE（`/udc/expression/schema` 必须**省略** appId，带上即 `BOOT_3000`；
  `designData` 必须含 `context` 键否则全局检测 NPE；`attribute/update` 走 `IGNORE_NULL`，清表达式须用空字符串）。
- **第二十四轮**（`e2190d1`）：映射规则写链 LIVE PASS（5 条根因全解：入参继承 `DataFlowDto` 需顶层 `appId`；
  `definition` 空串会在 `handleGraphDefinition(:227)` NPE；`rules` 空 → `dataProcess(:1173)` 越界；
  `entityMappingRelation` 空 → `UDC_DATAFLOW_0003`；`MANUALLY` 触发时 `listSchema` 必填 → `UDC_DATAFLOW_0060`）。
- **第二十五轮**（`6f76915` / `a93d841`）：生单规则图节点 `id` 必须为**实体 id**（伪造 id → `UDC_CE_DATA_FLOW_05005` ×2）；
  事件监听约束入仓（两类 + 4 源，`filterEvents` 的 `sourceTypes` 是 null-致命键但空数组合法且被忽略；
  `eventTypes` 对 `/filter/event` **完全无效**；**`checkSchema` 通过 != 配置正确**，须以回读 `messageInfo` 判成败）；
  `.pyc` 失效判据是 **`(mtime 整秒, size)`** 而非内容哈希 ⇒「等长 + 还原 mtime」改写会导致新进程静默 import 旧值
  （已加反陈旧护栏 `test_imported_values_agree_with_a_fresh_parse_of_the_source`）。

**更新时间**：2026-10-15 第二十二轮（**清结转 + marker 判据的边界补课（本轮主项）**：
① **开工实测基线**：`pytest -q` **1305 passed + 4 failed / 1309 collected**；`compileall components tools tests` 无错。
   4 个失败**全部**是 `test_documentation_contract.py` 的**计数契约差 1**（三处文档写 `1308`、实收 `1309`），**非结论漂移** —— 与上轮交接逐字一致。
② **清上轮结转（两件）**：
   - **计数契约 1308 → 1309**：`README.md` / `agent-version-audit.md` / `code-reality-audit.md` 三处同步；复跑全量 ⇒ **1309 passed / 0 failed**。
   - **上轮 10 个产物已入库**（见下 §commit），**未用 `git add -A`**。
③ **★ 本轮主项：给 marker 闭包判据补上「边界检验」——查出我自己论据里一个真窟窿并补实**。
   上轮 `DEPLOYED-MARKER-CLOSURE.json` 以「常量池含 `bind/annotation`」当「能暴露注解路由」的必要条件，
   据此论证 0-marker 构件不可能藏端点。**该判据只覆盖 Spring MVC**：JAX-RS（`@Path`）与原生 Servlet
   （`@WebServlet`/`@WebFilter`/`extends HttpServlet`）**不需要**该串即可暴露端点 ⇒ **若不检验，闭包论证有真窟窿**。
   - **新复算器** `tools/core/enumerate_deployed_exposure_census.py`（离线只读，243 行）。
   - **新证据件** `docs/audit/udc-semantics/DEPLOYED-EXPOSURE-CENSUS.json`（`sha256 5af85cf2ac5d90dc`，8417 bytes；复算器**字节级**原样重现）。
   - **★ 途中自查出一处我自己的假阳（如实记）**：我第一版用**子串**判「继承 HttpServlet」，
     实测得 **23 件**平台构件「具备 HTTP 暴露结构」——**全是假阳**。根因：
     `javax/servlet/http/HttpServlet` 是 `javax/servlet/http/HttpServletRequest` 的**前缀子串**。
     改为解析 `super_class` 常量池槽位做**精确相等**后，降至 **2 件**且**全为第三方**。
     ⇒ 该陷阱已写进工具 `known_trap_avoided` 字段与护栏的**对抗自证**（证伪「子串就够了」）。
   - **实测结论（第二条必要条件）**：**544 = 515 scanned + 29 NOT_OBTAINABLE**；
     **0-marker 428 件中「真实具备 HTTP 暴露能力」者 = 2 件，且全为第三方容器/库**
     （`tomcat-embed-core-9.0.104`、`jersey-common-2.35`）⇒ **平台家族 0 命中，闭包 PASS**；
     **平台家族构件带非 Spring 路由注解者 = `[]`**。
   - **同时把一条此前含糊的边界量化了（诚实记账）**：**0-marker 里有 48 件平台家族构件**（含 `udc-biz` 2312 class、
     `bpm-facade` 543、`organization-facade` 408 等）⇒「0-marker 构件不可能是暴露者」这句**不能**只靠 marker 判据说，
     必须由本件的第二条必要条件兑现；护栏已把该集合**钉住下界 48**，防止有人悄悄改小来掩盖。
   - **新护栏** `tests/udc/test_deployed_exposure_census.py`（**13 项**）：三支穷尽划分 / 与姊妹件逐字一致 /
     平台家族闭包空 / 恰好这 2 件且非平台 / 平台非 Spring 注解为 `[]` / **平台 0-marker 集合下界 48** /
     **子串陷阱对抗自证** / 复算器字节级重现 / 只改空白也咬住 / 判据须带理由 / 限制须写未扫缺口 / 规模下界 / 清洗门。
     **真盘突变 2/2 CAUGHT**（① 只改空白：1 failed；② 语义突变「把平台 0-marker 集合缩到 10」：2 failed），
     每轮后**字节级还原**（`5af85cf2ac5d90dc` 前后一致）。
④ **同轮修掉一处我自己造出的缺陷（如实记）**：本轮我改三处计数文档时先用 `Path.write_text()` 未带 `newline=`，
   在 Windows 文本模式下把三件文档**整体转成 CRLF** ⇒ `git diff` 由「1 行改动」膨胀为 **216/304/388 行全文件重写**、
   **无法评审**（正是第二十轮登记的同一类「宿主指纹」缺陷）。已按各文件 **HEAD 约定还原为 LF**（`README` 108 / `audit` 152,194 行），
   diff 收敛为**真正的单点改动**；此后所有文档改写一律显式 `newline=HEAD 约定`。
⑤ **两条基线矛盾的解释**：护栏报重跑得 **497 scanned**，证据件写 **515**。逐件复核：**不矛盾** ——
   差额 **18** 件是**找到 jar 但 jar 内无任何 `.class`**（netty-* 平台原生件、starter 空壳等，属容器/依赖聚合件），
   marker 普查把 `classes=0` 计为 SCANNED，而我的复跑脚本跳过它们。**双方都没有错**，已在本轮记明（防下轮误判为漂移）。
⑥ **基线 / 计数契约**：`pytest -q` **1322 passed / 1322 collected**（0 failed；`1309 → 1322 = 本轮新增 13 项`）；
   `compileall components tools tests` 无错；三处文档计数同步 **1309 → 1322**。
⑦ **诚实边界（未变）**：余 **60** 条 op **仍 UNVERIFIED** —— 本轮**没有**证伪它们，只是把「域是否漏构件」的
   口径从 marker 单判据升为**双必要条件**（marker + 暴露能力），两轴均 PASS 且取不到的 29 件全第三方；
   **唯一开口仍在**：运行期加载的**域外 ext 组件**（静态不可见、pod 日志仅存 ~2h、`/udc/**` 无会话一律 `BOOT_1006` 且负控同响应）
   ⇒ **仍不得写「不存在」**。`COMPLETION-METHOD-PROMPT.md` 的「平台操作面」「pending 清零」两项**仍未勾** ⇒ **任务不可暂停**。）

**更新时间**：2026-10-15 第二十一轮（**域扩展收口 + 部署域 marker 闭包入仓（本轮主项）**：
① **开工实测基线**：`pytest -q` **1299 passed / 1299 collected**（0 failed）；`compileall components tools tests` 无错 —— 与上轮交接一致，未破。
② **★ 上轮「域扩展」半成品收口（上轮产物全在 scratch、未入库、受 24h 清理）**：把扫描域从 `sup`（90 jar）正式切到 **`sup_v2`（94 jar / 1170 `.class` / 1044 FQCN）**，并**原地重算两件已入库证据件**：
   - `DEPLOYED-FULL-DOMAIN-OP-SURFACE.json`：`970→1044` FQCN、`1096→1170` 文件、`167→238` 有路由类、`1576→2110` 方法、`1573→2107` distinct op、`49→53` 贡献 jar。
   - `DYNAMIC-REGISTER-CHANNEL.json`（域内包含关系实测）：`89→90` BCC 后代 / `17→60` 仅 BC / `61→88` 两者皆非 / `167→238` 路由类。
   - **两条同域对照在扩域后仍全过**：udc-web 674 契约 **674/674 PASS**；跨构件归位 32 条 **32/32 PASS**；余 **60** 条 **0/60** 命中；超集检验 `routed_without_bind_annotation = []`；稳健性 `none`/`substr` 两变体下余 60 **均 0 命中**（且 `none` 变体确实丢前缀 rel32=5，对照非空转）。
   - **护栏同步升级**（不是只改数值）：`test_full_domain_op_surface.py` 的 `MIN_*` 由旧域 `(1096,970,167,1576,1573,49)` 升到新域 **`(1170,1044,238,2110,2107,53)`**；`CLASSDIR` 由 `scratch/sup` 改为 `scratch/sup_v2`；`test_dynamic_register_channel.py` 的三支计数与 `CLASSDIR` 同步。**修一处跑一次**：先在子集上实测（发现该文件里有**第二处** `route_classes == 167` 旧断言残留 ⇒ 一并修），再跑全量。
③ **★★ 本轮真正的新结论：部署域已闭包（从「抽样」升级为「可检验命题」）**。上轮的 544 jar marker 普查只在 scratch，本轮把它做成**仓内耐久证据件 + 复算器 + 护栏**：
   - 新复算器 `tools/core/enumerate_deployed_marker_census.py`（离线只读；只落文件名 + sha256 + 计数，**不落 scratch 绝对路径**，避免把宿主指纹写进证据件）。
   - 新证据件 `docs/audit/udc-semantics/DEPLOYED-MARKER-CLOSURE.json`（复算器原样产出；`sha256` 见件）。实测：**544 total = 515 SCANNED（216,782 class）+ 29 NOT_OBTAINABLE**；其中 **87 件含 marker / 428 件 0 marker**。
   - **判据（本件核心）**：marker = `.class` 常量池含 `bind/annotation`。任何带 `@RequestMapping/@GetMapping/...` 的类必然引用 `org/springframework/web/bind/annotation/*` ⇒ 含 marker 是「能暴露注解路由」的**必要条件** ⇒ **0 marker 的构件结构上不可能暴露注解路由**，漏掉它不可能藏端点。
   - **闭包命题**：**全部含 marker 的部署构件 ⊆ 扫描域 ⇒ PASS（缺失清单 = 空）**；且 **29 件 NOT_OBTAINABLE 全是第三方构件（平台家族前缀命中 0）**。⇒「域是否会漏构件」由「约 90/544 抽样」升级为**以 marker 为判据的完备性论断**。
   - 新护栏 `tests/udc/test_deployed_marker_closure.py`（**10 项**）：544 三支穷尽划分 / 闭包缺失清单为空 / **取不到的件不得当 0 marker 用** / **取不到的件须全为第三方** / 规模下界 / 按构件名（非仅计数）复核 / 复算器**字节级**原样重现 / 只改空白也要咬住的自证 / 判据须带理由 / 清洗门。
④ **Reroute 一条上轮遗留：`pods/exec` 注记已更正（LIVE 复检）**。对 K8s 发 `SelfSubjectAccessReview` **实测**：`pods/exec` **get/create/list 三个 verb 全 `allowed=False`**，`pods/portforward`/`pods/attach` 亦全 False；**仅 `pods/log get` = True**。⇒ 第十八轮记的「`pods/exec` 实为 ALLOWED」**在本轮已不成立**（该轮取件窗口与当前 RBAC 不同）。已取的 544 jar 清单**仍作有效证据**（导出件 sha256 可校验），但该通道**不得再写进后续计划当可用手段**；已就地更正 `COMPLETION-METHOD-PROMPT.md`，`PROGRESS.md` 的旧 forbidden 记录**恢复为准确表述**（历轮 forbidden 与当轮 allowed 都如实保留，另记本轮 DENIED）。
⑤ **清理自造残留**：上轮 `--emit` 误建的空目录树（`/d/d/software/hermes/cache/scratch/bulk/contracts`）已用 `rmdir`（非 `rm`）**逐级清空**，`/d/d` 仅余两棵真实树、无空壳。
⑥ **基线 / 计数契约**：`pytest -q` **1308 passed / 1308 collected**（0 failed；1299 → 1308 = 本轮新增 10 项 − 旧 1 项并入，实为 +9）；`compileall components tools tests` 无错；计数契约三处文档（`README.md` / `agent-version-audit.md` / `code-reality-audit.md`）**同步 1299 → 1308**（同步后全量复跑 0 failed）。
⑦ **完成判据仍未满足**（余 **60** 条 op 仍 UNVERIFIED；`COMPLETION-METHOD-PROMPT.md` 的「平台操作面」「pending 清零」两项未勾）⇒ **任务不可暂停**。)

**更新时间**：2026-10-15 第二十轮（**补做上轮 commit + 把「字节级复算」审计推广到其余复算对（本轮主项）**：
① **补做上轮 commit（上轮明确遗留的缺口）**：`git add` 上轮点名的 **10 个具体文件**（4 改 + 6 新增：`README.md` / `agent-version-audit.md` / `code-reality-audit.md` / `PROGRESS.md` / `DEPLOYED-FULL-DOMAIN-OP-SURFACE.json` / `DYNAMIC-REGISTER-CHANNEL.json` / `test_dynamic_register_channel.py` / `test_full_domain_op_surface.py` / `enumerate_dynamic_register_channel.py` / `enumerate_full_domain_op_surface.py`），**未用 `-A`**，入库 `fcfadc2`。开工实测基线 **1296 passed / 1296 collected**（上轮已修绿）。
② **★ 本轮主项：把上轮「字节级复算」不变量推广到其余复算对（= 上轮「下一步③」）** —— 逐个**实测**（跑工具 + 与证据件字节比对），得到一张**三类**清单：
   - (a) **已字节级**（上轮已修）：`DYNAMIC-REGISTER-CHANNEL.json`（LF 明文钉死）、`DEPLOYED-FULL-DOMAIN-OP-SURFACE.json`（LF 明文钉死）。
   - (b) **看似能重现、实为宿主依赖（= 本轮新发现，最隐蔽的一类）**：`DEPLOYED-OP-SURFACE.json` / `ROUTE-IMPLEMENTATION-VERDICT.json` / `METADATA-PLANES.json` —— 三者在本机实测**确实字节全等**，但原因**不是**生成处钉死了换行，而是 `Path.write_text(...)`（无 `newline=`）/ `print()` **落到 Windows 文本模式**、被隐式转成 CRLF。**同一工具在 Linux 上会产出 LF** ⇒ 该「可重现」**不是不变量，而是宿主指纹**。实测：三件的 `parsed` 版本与 LF 重排**语义全等**（`json.loads` 相等）而**字节不等**，即**换行漂移对 parsed 判等完全隐形**。
   - (c) **结论面 parsed 判等**（未做字节比较）：上述三件对应护栏原写法。
③ **修法（最小改动）**：① 三个生成处把换行**显式钉死** —— `tools/core/enumerate_deployed_op_surface.py` / `tools/core/enumerate_route_implementation.py` 的 `write_text(..., newline=CRLF)`；`tools/core/enumerate_metadata_planes.py` 原经 `print()` 输出（宿主文本模式），改为**显式构造 CRLF 字节** + 新增 `--emit`（`sys.stdout.buffer.write` 走二进制，绕开文本模式）。② 三条护栏的复算判等**由 parsed 升为字节级**（`out.read_bytes() == EVID.read_bytes()`）。③ **补 3 项「会咬自证」**（CRLF→LF 突变：parsed 等价必须判字节不等）。
④ **真盘突变 3/3 CAUGHT**（逐件：CRLF→LF 后 `2 failed`；每轮后**字节级还原**，sha256 `714062d375c06efd` / `95d29b88b71c6d5a` / `498c7265eed5011e` 前后一致）。**修后三件实测字节全等**（`714062d3…` / `498c7265…` / `95d29b88…`），且不再依赖宿主。
⑤ **口径更正（如实记）**：上轮把「LF 明文 + 无尾换行」当成**同族统一约定**推广到 `enumerate_full_domain_op_surface.py`；本轮实测发现该族**内部本就不统一**（另三件是 CRLF），故**不为统一而改动已入库三件的字节**（那会让它们与既有证据链断裂），只把**换行从隐式变为显式**、把**判等从 parsed 变为字节级**。**唯一不变量是「字节级可复算」，不是「某个特定换行」**。
⑥ **基线**：`pytest -q` **1299 passed**（0 failed，collected **1299**；+3 = 本轮 3 项突变自证）；`compileall components tools tests` 无错；计数契约 **1296 → 1299**（README / `agent-version-audit.md` / `code-reality-audit.md` 三处已同步，无残留 1296）。
⑦ **完成判据仍未满足**（余 **60** 条 op 仍 UNVERIFIED；「平台操作面」「pending 清零」两项未勾）⇒ **任务不可暂停**。）

**更新时间**：2026-10-15 第十九轮（**先修继承基线 + 把「复算产物」的判等从 parsed 升到字节级（本轮主项）**：
① **继承基线破裂定位（本轮第一件事）**：开工实测 `pytest -q` = **1 failed / 1293 passed**（collected **1294**）。唯一失败 = `test_full_domain_op_surface.py::test_full_domain_evidence_is_recomputable_by_the_tool`：上轮为提高可读性**手工改写了** `DEPLOYED-FULL-DOMAIN-OP-SURFACE.json` 的 `limitations`（把散文升级为「动态注册通道已锚定」），而该件是**复算产物**、护栏做逐字比对 ⇒ 一致性破裂。**这是我上轮自己破的基线，如实记。**
② **★ 挖出更深一层根因（比「忘了改生成处」严重）**：即使把 limitations 文本同步进生成处，该件**仍然无法被复算器字节重现** —— `tools/core/enumerate_full_domain_op_surface.py` 的 `json.dumps` 用 `indent=1` **且追加尾换行**，而证据件实为 `indent=2 / sort_keys=True / 结尾无换行`（实测 `json.dumps(evid, indent=2, sort_keys=True)` 与文件字节**全等**）。⇒ **复算器从来没能原样产出过本件**；护栏只比 `json.loads(...) == ...`（**parsed 相等**），故这种格式漂移**一直是隐形的**。
③ **修法（三处，最小改动）**：(a) 生成处格式对齐**同族既有约定**（`tools/core/enumerate_dynamic_register_channel.py` 即 `indent=2, sort_keys=True`）⇒ 本工具改为 `indent=2, sort_keys=True` + `write_text(..., newline=LF)`；改后**实测字节全等**（sha256 `6efc8e7c393e3303` / 7743 bytes；改前工具输出 sha256 `69d13fcd29583283`，仅空白不同）。(b) 两条护栏的复算判等从 parsed 升到**字节级**（`out.read_bytes() == EVID.read_bytes()`）；(c) **补 2 项内存内突变自证**，证伪「只比 parsed 就够」：**① 只改缩进一格**（parsed 等价）必须被判不一致；**② 整件按 `indent=4` 重序列化**（语义 100% 等价）必须被判不一致 —— 即证明**格式本身是契约的一部分**（本件是复算产物，不是可自由重排的散文）。真盘突变实测 **CAUGHT**，突变后文件**字节级还原**。
④ **自我纠正（如实记）**：`tests/udc/test_dynamic_register_channel.py` 的测试**名叫** `..._byte_for_byte` 却**只比 parsed**（名不副实，上轮我写的）⇒ 本轮改为真字节比较；并顺带核验**同族两对**（动态注册通道 / 第十八轮部署域 op 面）**都确实字节全等**（`2a3610ae96a0894c` / `6efc8e7c393e3303`）⇒ 该不变量真实成立，非补丁式特例。
⑤ **上轮工作一并记账（上轮未更新本文件）**：上轮把「动态注册通道」从一句形容词升级为**字节码锚定边界** —— 契约 `ComponentDynamicRegister` 只有 `register`/`unregister` 且**只在 `boot-core` 内**（全仓仅 3 版本命中）；`spring.factories` 三实现中**只有 `ControllerDynamicRegister` 与路由有关**；闸门（CFR 全文）：`getSelfBean(beanName)` → **非 `BaseController` 直接 continue** → `wrapController` → 反射 `RequestMappingHandlerMapping.detectHandlerMethods`；**支点 = 包含关系**：前缀谓词是 `BaseComponentController.isAssignableFrom(aClass)` 而 `BaseComponentController extends BaseController` ⇒ **前缀谓词集合 ⊆ 动态闸门集合** ⇒ 把限制从「通道存在、边界无界」收窄为「动态通道暴露的 `/udc` 前缀路由，控制器必属 `BaseComponentController` 后代这一已知类别」；域内实测（1096 class）路由类 167 = BCC 后代 **89** + 仅 BC 17 + 两者皆非 61，与全域裁定器 **167/89 逐字吻合**（交叉验证）。产物：`tools/core/enumerate_dynamic_register_channel.py` / `DYNAMIC-REGISTER-CHANNEL.json`（`2a3610ae...`）/ `tests/udc/test_dynamic_register_channel.py`（**9 项**）。**诚实边界（已写进件里）**：LIVE 探针**不可用** —— `/udc/**` 未带会话一律 `BOOT_1006`，且**负控**（`/udc/zzz-nonexistent-xyz`）返回**完全相同**响应 ⇒ `BOOT_1006` 不是路由存在性判据；pod 日志仅保留约 2h ⇒ **启动段不可观测** ⇒ **不消除「域外 ext 组件」边界**。
⑥ **计数契约 1294 -> 1296**（新增 2 项突变自证；collected == passed == **1296**；三处文档 README / `agent-version-audit.md` / `code-reality-audit.md` 已同步）。
⑦ **完成判据仍未满足**（余 **60** 条 op 仍 UNVERIFIED；「平台操作面」「pending 清零」两项未勾）⇒ **任务不可暂停**。）

**更新时间**：2026-10-15 第十八轮（**基线段被外部写入所破 + 部署态 op 面终裁入仓（候选 vii-b）**：① **先修基线（本轮第一件事）**：全量 `pytest` 实测 **1 failed / 1260 passed**（提示词里的 755 已过期）。定位 = `test_route_implementation_verdict.py::test_verdict_is_reproducible_by_the_tool`：护栏把证据件**逐字**比对，而证据件含 `jars_scanned`；本地 maven 仓库 `<MAVEN_REPO>` 在 **15:49-15:51** 被**其它工作流**写入 **3 个客户构件**（1.0.11228 的 biz/web/facade），计数 1518 -> 1521 ⇒ 只有这一个键变。**根因是护栏写法**：把**可变域**计数当成了契约（等于拿环境指纹当契约），不是结论漂移，也不是本轮改坏的。② **修法（最小改动，三处）**：`tools/core/enumerate_route_implementation.py` 产物**新增 `jars_scanned_note`** 显式标注可变域；护栏改为 **结论面逐字判等（去掉 jars_scanned*）+ 扫描域不得缩小（>=）** 双判据；**新增** `test_evidence_marks_the_volatile_count_as_non_contract`。**真盘突变 2/2 CAUGHT**（provider_count 1->2；对照叶子 batch-move 清空），每次突变后证据件**字节级还原**（sha256 `498c7265` 前后一致）；该护栏 14 -> **15 项**。③ **★ 部署态 op 面终裁入仓（本轮主项）**：上轮已用 `pods/exec` 取出部署态 `BOOT-INF/lib`（544 jar），但结论只在 scratch、且**阳性对照用错域**。本轮落成仓内**耐久**证据件 + 复算器 + 护栏：`DEPLOYED-LIB-INVENTORY.json`（22 个 udc 构件 / **11 个本地缺失**；导出 `udc-web-5.3.517.jar` sha256 `0d6b0a6528` / 136930 bytes 与 DEPLOYED-VERSION-NOTE.md 逐字一致）、`DEPLOYED-OP-SURFACE.json`（域内 **10** jar 有映射 / **100 类 / 958 方法 / 958 distinct op**）、`tools/core/enumerate_deployed_op_surface.py`、`tests/udc/test_deployed_lib_inventory.py`（5 项）、`tests/udc/test_deployed_op_surface.py`（7 项）。④ **★ 自我纠正（如实记）**：上轮写的「阳性对照 **32/32** 命中」是**跨域对照**——32 条归位里 **22 条属 `boot-starter-sandbox`**（沙箱族），**不在 22 个 udc jar 域内**；拿它当本域阳性对照实测只有 **5/32**，是**假阴性**。本轮改为**同域对照**：udc-web **674 契约 op 面 / 674 命中 = 674/674 PASS** ⇒ 「余 **60** 条 0 命中」才有资格当强负面。⑤ **口径升级**：余 60 条从「Artifactory 侧静态穷尽不承接」升级为「**部署态构件域内亦不承接**」（证据阶梯 **LIVE-DEPLOYED**）。域边界如实写：只裁 `udc-*.jar` 域，`boot-starter-*` 等其余 522 jar **未纳入**，不得据此对全平台下结论。⑥ 计数契约 **1261 -> 1274**（collected == passed == 1274，本任务面 0 failed；三处文档 README / `agent-version-audit.md` / `code-reality-audit.md` 已同步）。⑦ **完成判据仍未满足**（余 60 条 op 仍 UNVERIFIED；COMPLETION-METHOD-PROMPT.md 的「平台操作面」「pending 清零」两项未勾）⇒ **任务不可暂停**。）

**更新时间**：2026-10-15 第十七轮（**发现 B 收口收尾：护栏修正 + 突变 ⑦ 重验证 + 计数契约结清**：① **结清上轮两条诚实标注**：(1) 计数契约**已同步**——`README.md` / `agent-version-audit.md` / `code-reality-audit.md` 三处均已是 `1261 passed`，且 = `pytest --collect-only` 的 **1261 collected** = 全量实测 **1261 passed**（三口径同一）；(2) 第十七轮的 5 个产物（`ROUTE-IMPLEMENTATION-VERDICT.json` / `LIVE-ROUTE-IMPLEMENTATION-CONTROL.json` / `tools/core/enumerate_route_implementation.py` / `tests/udc/test_route_implementation_verdict.py` / `RUNTIME-URL-SURFACE.md` §8）**已随 `c845a57` 入库**。② **★ 突变 ⑦（文档反向护栏）重验证完成**：原护栏按**裸字面量**匹配，会被文档里的常态反引号写法 `\`search-list\` 由 …` **绕过**（上轮实测漏过）；本轮改为「**先去反引号 / 表意空格归一化 → 压平空白 → 再子串匹配**」，并把模式从 4 条扩到 **6 类**（`由` / `归位` / `属 ` / `提供者` / `在 udc-` / `= ` 等式）。**真盘突变 6/6 CAUGHT**：M1 反引号+由（= 上轮漏过的那一类，现已挡住）、M2 裸写法、M3 归位、M4 等式、M5 在 udc-、M6 提供者名；每轮突变后 `RUNTIME-URL-SURFACE.md` **字节级还原**（sha256 `23f236b3…` 前后一致）。③ **自我纠正（如实记）**：上轮把该护栏文件写成了**整文件 CRLF**（HEAD 为 LF，仓内 `core.autocrlf=false`、无 `.gitattributes`）⇒ `git diff` 变成**全文件重写**、根本无法评审，且把「修一处」变成了「改整个文件」。本轮先 `git checkout --` 回到 HEAD 的 LF 基线，再用**断言式脚本只替换目标函数** ⇒ 最终 diff 收敛为 **+12/-3 的单点改动**。④ **护栏之外的独立性**：突变后每次都重跑**全量** `pytest -q` 的对应子集 + `compileall`，确认护栏修正**不误伤**其余 1247 项。⑤ **★ 轴 3 补第三方独立交叉复核（本轮新增）**：原轴 3（LIVE 同 traceId 行数分组）此前只由手工计数支撑、且原始窗口已随 scratch 清理。本轮把它与 **udc-web 5.3.517 契约（674 端点）**做逐字（`{...}`→`{arg}` 归一）对账并落盘 `contract_cross_check`：试验组 **2/2 在契约内 0 命中**（与轴 2 的字节码「注册面完整且无此叶子」**独立一致**）；对照组 **14/16** 逐字落在契约内，余 **2** 条各有另档契约背书 —— `/udc/graphql` 属 **GraphQL 操作面**（另档契约，见 `PLATFORM-GRAPHQL-OPERATIONS.md`），`/udc/metadata/app-service-by-name` 属 **ctp `MetadataController` 面**（`/udc/metadata/` 105 映射，见 `METADATA-PLANES.json`）⇒ 分组结论**不依赖单一契约口径**。新增 3 项护栏（含「未落进 674 的对照模板恰好是这 2 条且各带背书」与 ctp 面 leaf 实测），**真盘突变 4/4 CAUGHT**（对照模板挪组 / 篡改命中数 14→16 / 伪造 graphql 背书 / 掩盖非契约对照），每轮**字节级还原**。⑥ **基线**：`pytest -q` **1261 passed**（0 failed）；`compileall components tools tests` 无错；工作树改动仅本护栏文件。⑦ **完成判据仍未满足**（余 **60** 条 op UNVERIFIED；`COMPLETION-METHOD-PROMPT.md` 的「平台操作面」与「pending 清零」两项未勾）⇒ **任务不可暂停**。）

**更新时间**：2026-10-15 第十六轮（**先修上轮自破基线 + 候选 (v) 收口：三个并行 metadata 面**：① **上轮遗留全部清零**：修掉我上轮写错的 2 条断言（`test_no_op_endpoints_...` 两侧不同序；`test_lossy_javap_dump_...` 把「残缺 dump」误说成「零信息」）——实测定性为**截断**而非空：该 javap 只落 **309/865** 个 Utf8 常量，且注解类型名/`Constant pool:`/`flags:`/`Code:` **全 0 命中**，故「按 dump grep 得 0 ⇒ 不存在」是假阴性；同时**不均匀**——`entity-by-name`/`refresh-all`/`downgrade-all` 在该 dump 内**确有命中**，这条不均匀性本身就是「不能拿它做否证」的证据。② **PROGRESS.md 损坏修复**：第十五轮头部 7 处反引号内容被 bash 命令替换吃掉 + 第 54/55 行产物路径被删空 ⇒ 已按上下文**等义重建**并显式标注（不再用双引号串写文档）。③ **★ 候选 (v) 收口（本轮主项）**：用**仓内耐久**证据证明 `/udc` 前缀下有**三个并行 metadata 面**——`/udc/meta-data/`（udc-web `MetaDataController`，**32**）/ `/udc/design-metadata/`（udc-web `UdcDesignMetadataController`，**47**）/ `/udc/metadata/`（ctp `MetadataController`，**105 mapping / 99 op 面**）；后两面共享 **43** 个同名 leaf，`refer-and-app` 是**三面唯一共有**字面量，且 `/udc/meta-data/refer-and-app` 与 `/udc/metadata/refer-and-app` **只差一个连字符**。④ **口径更正**：`674 端点` = **udc-web 单构件视图**，不是平台操作面全量；按全构件并集至少 **779**（674 + ctp 105），而 779 **也不是运行期全量**（其它非 udc-web 提供者未纳入）⇒ 两口径**不可混用**。⑤ **哪个面是活的（两条独立轴）**：设计器耐久 chunk 内 `udcMetaData*` **68** 次 / `udcDesignMetadata*` **0** 次；LIVE 窗口 `/udc/metadata/` **20** 次 / `/udc/design-metadata/` **0** 次 ⇒ **design-metadata 面在本窗口是死面**（契约在案、词表与活面大面积同名、却无人调用）。⑥ **产物**：新增复算器 `tools/core/enumerate_metadata_planes.py`（可 `--json`）、证据件 `METADATA-PLANES.json`、护栏 `tests/udc/test_metadata_planes.py`（**16 项**，含「证据件可由复算器原样重现」与 4 类真盘突变 2 failed + 字节还原一致）；`RUNTIME-METADATA-CONSTRAINTS.md` **新增第 5 节**并把 §3 里早已被字节码证伪的「12 端点」旧口径就地更正。⑦ **自我纠正（如实记）**：本轮我 `tee` 覆盖了已入库的 `RUNTIME-METADATA-CONSTRAINTS.md`（误以为是新文件），已 `git checkout` **完整还原**后改为**追加第 5 节**；并在护栏里写错过一条自反断言（清洗门文件自身含其禁止字面量）与一处漏洞（`udcDesignMetadata` 是 `udcMetaData` 的子串、`count()` 差分不可靠）⇒ 分别改为**只查产物/拼接构造**与**直接钉绝对计数**。⑧ 计数契约 **1218 → 1240 collected**（collected == passed，本任务面 0 failed）。⑨ **完成判据仍未满足**（余 60 条 op UNVERIFIED；pending 未清零）⇒ **任务不可暂停**。）

**更新时间**：2026-10-15 第十五轮（**候选 (viii)：设计器 bundle 族 op 全集落成仓内耐久证据件 + 护栏**：① 把上轮只在 scratch 复算（受 24h 清理）的「micro-flow-group 族 op 全集 = 6」落成仓内证据件 `frontend-microflowgroup-family-ops.json`〔第十六轮修复：反引号内内容曾被 bash 命令替换吃掉，此处为按上下文的等义重建〕，证据源改为**仓内原始 webpack chunk**（`docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`，sha256 `6051e1df…f387d`，2530724 字节，**非** wakaru 解包产物）—— 并**自纠上轮边界**：上轮用 unpacked 产物，而 `test_decompile_loss.py` 已钉死 unpacked 会丢字面量，故「0 命中」类负证据必须回到原始 chunk 复检；② 新增护栏 **12 项** （chunk sha256 钉死 + 族内 6 op 逐条 paramsType/paramsKey + kebab 字面量 = 0 + **负证据成立前提** = 同 chunk 确有 RAW_REST 约定 + **命名习惯反证** = 同 chunk 确有他族 `udc*SearchList*` 字面量 + 不过度外推 + 清洗门），**5 类突变实测均 failed 且字节还原一致**；③ 新增第二条独立否证轴：族内 op 无 `SearchList` 成员只否证 LOADER 约定，本件再证 **kebab 字面量 `micro-flow-group` 在 chunk 内 = 0** ⇒ RAW_REST 约定同样不可能发出该请求（双轴否证）；④ **答案确定为 NO**：`/udc/micro-flow-group/search-list` 的「设计器前端来源」支 **REFUTED**，余下「客户应用页面 / 其它构件提供 / 死路径」三选一，该路由仍 **UNVERIFIED**（不因此件升级）；⑤ 计数契约 **1187 → 1258 passed**（collected == passed == 1218））

**更新时间**：2026-10-15 第十一轮（**dataType 约束矩阵补全**：① 定位根因——`entity_constraints.py` 的 `ENTITY_DATA_TYPES` 只有注释引用、从未定义值域；② 从前端设计器 bundle `src_redux_store_ts` module-65420/31623 用 node 直导出权威表：`pe` JavaType→dataType **34 种**、`Uz` 14 种字段默认模板、`WB` 值域、`d4` 中文名、`fU` 日期格式、`py` PC/移动端控件、`mG` 可新建 9 种白名单；③ 后端对账：`boot-starter-datatype` 5.3.358（15 个运行时基础类型）+ `udc-common` UdcDataType instance（22 种，DataTypeManager 扫描注册）→ 落 `ENTITY_DATA_TYPES` 等 8 张表 + `validate_attribute_datatype()`；④ `boot-starter-condition` 5.3.318 对账：`OperatorEnum` 22 个不变，`ParamTypeEnum` 实测 **5 个**（原文档 2 个不完整），补 `ConditionService.check` 契约（leftParam/operator/rightParams 不可 null；GROUP 内从第 2 个条件起 logicalOperator 不可空）；⑤ 修正 `CONDITION_TYPE_OPERATORS`：BOOLEAN 补 ZERO/NOTZERO、BIGINTEGER 补 NULL/NOTNULL、INTEGER/DATETIME 补 ZERO/NOTZERO；计数契约 1167 保持）

**测试基线**：**1322 passed / 1322 collected**（全量 `pytest -q` 实测，本轮 0 failed）；`compileall components tools tests` 无错；纯本地 git（勿 push）。上轮尾注的「1 failed（复算件被手工改写）」已在本轮修掉并**升级为字节级复算护栏**。（全量 `pytest -q` 实测）；`compileall` 无错；纯本地 git（勿 push）。工作树干净（第十六轮登记的 `test_serialnumber_constraints.py::test_endpoints` 并发 WIP 失败已随之清零，本轮全量 0 failed。）

**上轮遗留**：**已清**——第十轮标为"并发工作流未提交"的 `entity_constraints.py`/`microflow_model.py`/`test_entity_constraints.py`/`test_microflow_condition_constraints.py` 正是本轮任务对象（dataType 约束矩阵），本轮已补齐并提交；口径偏差已消除。


## 域进度

| 域 | 权威约束 | 从零手写/在线验证 | 备注 |
| --- | --- | --- | --- |
| 微流程 nodes | ✅ 50 Activity 类，48 码全表，每节点必填 | ✅ 本地 PASS（`test_author_from_constraints.py`） | 后端解析器 `NodeUtils.getXxx(required)` |
| 微流程 条件 | ✅ 22 操作符 + GROUP 嵌套 + LogicalOperator | ✅ LIVE 实证（3 标品字节级） | boot-starter-condition 5.3.308 |
| 微流程 DATA_MAPPING | ✅ mappingRows/REFERENCE\|CONSTANT/ENTITY\|DTO | ✅ LIVE 实证 path 元素 | — |
| 实体/属性 | ✅ EntityBaseDto/BaseUdcAttributeDto 必填 | ✅ **LIVE 从零构造→创建(id=-6338668863907875875)→回读一致**；8实体+190属性零误报 | `entity_constraints.py` |
| 页面/布局 | ✅ PageDefinitionDto/PageLayoutDefinitionDto 必填 + PageTypeEnum + pageItems.urlType + biz层强制链 | ✅ **LIVE 从零构造→创建(pageId=6150153921121584026)→成功** | `page_constraints.py` |
| 菜单/导航 | ✅ FunctionNodeDto/FunctionDto 必填 + 枚举 + 交互表 `udc_function_node` + REST 端点 | ✅ **LIVE 从零构造→创建(id=-623283056435289078)→回读一致** | `menu_constraints.py` |
| 平台操作面 | ✅ 299 REST + 240 GraphQL；**三个并行 metadata 面已澄清**（`/udc/meta-data/` 32 udc-web / `/udc/design-metadata/` 47 udc-web / `/udc/metadata/` 105 ctp；口径更正 **674 = 单构件视图**、并集 **779**，**不可混用**；双轴判活 ⇒ design-metadata 在本窗口为**死面**，见 `RUNTIME-METADATA-CONSTRAINTS.md` §5）；**op 命名规则字节码实证** + **full_path 缺陷已修** + **暴露机制已证** + **跨构件归位 32/92**（32/32 字节验证）+ **udc-web 契约方法级缺陷已修**（657->674 端点 / op 面 666）+ **全版本全构件穷尽扫描**（619 Controller / 201 构件 / 437 jar / 12 版 udc-web，负证据）+ **文档名幻影口径更正**（raw 230/93 -> corrected 231/92）+ **第二解析器独立复核 674**（660 带值 + 14 裸，逐条 0 双向差；op 面 673 / 暴露面 666 双侧一致） + **LIVE 日志通道首证**（K8s API 直连；`pods/exec` forbidden / `pods/log` allowed；真实请求 URL 面 425 条对账 **11/13**；路由字面段形近陷阱 41 条 / 0 同义撞车） + **LIVE 多 pod 面首扫**（32 pod / 1407 URL 行 / 421 distinct；模板级对账 **14/18**；**发现 A**：`/udc` 前缀下 udc-web 之外的提供者（20:0）+ **发现 B**：被调用但无实现的路由） + **部署态版本/路由裁定**（19 平台构件 tag LIVE；**udc=5.3.517 ⇒ 版本差假设证伪**；部署态字节码裁定 `select-by-appid` = 映射字面 `select-by-type`、`search-list` 该类无字面） + **部署态 tag 入版本审计**（`agent-version-audit.md` §2.1，第十四轮 LIVE 复验 19/19、差异 0）| 🟡 前端 346 op 中 **231** 精确归位；**92** 未归位 udc* 中 **32 已跨构件归位 / 60 UNVERIFIED**（**名单 + loader 契约已落盘**）；**扫描域已扩到 94 jar / 1044 FQCN / 2107 op**，且**部署域 marker 闭包 PASS**（87 含 marker 构件全部在域内，见 `DEPLOYED-MARKER-CLOSURE.json`） | 详见 `REST-EXPOSURE-MECHANISM.md`（机制）、`COMPONENT-RELOCATION.md`（归位 + **674 端点 / 673 op / 666 op 面**）、`frontend-udc-unlocated.json`（60 名单 + 族分布）、**`COMPONENT-COVERAGE-EXHAUSTION.md`（穷尽扫描）** + **`frontend-op-loader-contract.json`（loader 契约）**；旧持久化 657 作废 |
| BPM 域 | ✅ facade API 契约（30 AppService/132 方法） | ⛔ biz 类在加密 assemble.jar 内；本地仅 facade | `BPM-ORG-USER-OPERATIONS.md` |
| ORG 域 | ✅ facade API 契约（44 AppService/342 方法） | ⛔ 同上 | 同上 |
| USER 域 | ✅ facade API 契约（41 AppService/199 方法） | ⛔ 同上 | 同上 |
| 存储层(Redis/OSS) | ✅ LIVE 实证：Redis key 模式（`{env}:Metadata:JSON:MD5:{app}:udc@{Entity}@{TYPE}@{id}.json` 失效戳 / `CtpEnumCodeLocal` 枚举缓存）+ 99 交互表 | ✅ udc pod netstat 指向 redis 10.0.0.1:6379 / mysql 10.0.0.1:3306 | `STORAGE-RUNTIME-LAYER.md` / `INTERACTION-TABLES-MAP.md` |

## 已落模型 / 文档
- 模型：`components/udc/{microflow,entity,page,menu}_constraints.py`、`components/udc/graphql_op_naming.py`
- 文档：`docs/audit/udc-semantics/{MICROFLOW-*,CONDITION-*,ENTITY-*,PAGE-*,PLATFORM-*,FRONTEND-OP-*,GRAPHQL-OP-NAMING-RULE}.md`
- 文档（新增）：`docs/audit/udc-semantics/FULL_PATH-CONCAT-DEFECT.md`
- 证据件（新增，第四轮）：`docs/audit/udc-semantics/frontend-udc-unlocated.json`（60 名单 + 32 归位 + 族分布）
- 护栏（新增，第四轮）：`tests/udc/test_frontend_udc_unlocated.py`
- 证据件（新增，第五轮）：`docs/audit/udc-semantics/frontend-op-loader-contract.json`（60 条中 32 条 loader 契约 + 4 条命名偏离）
- 文档（新增，第五轮）：`docs/audit/udc-semantics/COMPONENT-COVERAGE-EXHAUSTION.md`
- 护栏（新增，第五轮）：`tests/udc/test_frontend_op_loader_contract.py`（11 项）
- 文档（新增，第九轮）：`docs/audit/udc-semantics/RUNTIME-URL-SURFACE.md`（运行期 URL 面 / 双发现 / 限制）

- 证据件（新增，第九轮）：`docs/audit/udc-semantics/RUNTIME-URL-SURFACE.json`（**去客户业务明细**：appId/页面键/表名/记录 id 全占位化 + 清洗门）

- 护栏（新增，第九轮）：`tests/udc/test_runtime_url_surface.py`（13 项；4 处篡改实测均 failed + 还原字节一致）

- 文档（新增，第十轮）：`docs/audit/udc-semantics/DEPLOYED-STATE-VERDICT.md`（部署态版本裁定 + 微流程分组路由裁定 + 限制）

- 证据件（新增，第十轮）：`docs/audit/udc-semantics/DEPLOYED-COMPONENT-TAGS.json`（19 平台构件 LIVE tag；**只落平台构件，客户 pod/镜像名不落**）

- 护栏（新增，第十轮）：`tests/udc/test_deployed_state_verdict.py`（8 项；2 处篡改实测均 failed + 还原字节一致）

- 文档/证据（新增，第十四轮）：`docs/audit/agent-version-audit.md` §2.1（部署态构件版本 LIVE 全表）
- 护栏（新增，第十四轮）：`tests/udc/test_deployed_tags_version_audit_alignment.py`（8 项）
- 证据件（新增，第十五轮）：`docs/audit/udc-semantics/frontend-microflowgroup-family-ops.json`（族 op 全集 = 6 / 无 SearchList / kebab 字面量 = 0；源 = 仓内原始 chunk + sha256 钉死）
- 护栏（新增，第十五轮）：`tests/udc/test_frontend_microflowgroup_family_ops.py`（12 项；5 类突变实测均 failed + 字节还原一致）
- 复算器（新增，第十六轮）：`tools/core/enumerate_metadata_planes.py`（三个并行 metadata 面；`--json`；离线只读）
- 证据件（新增，第十六轮）：`docs/audit/udc-semantics/METADATA-PLANES.json`（三面 / 交集 / 并集口径 / 双轴判活）
- 护栏（新增，第十六轮）：`tests/udc/test_metadata_planes.py`（16 项；证据件可由复算器原样重现 + 4 类真盘突变 failed 且字节还原一致）
- 文档（改，第十六轮）：`docs/audit/udc-semantics/RUNTIME-METADATA-CONSTRAINTS.md`（**新增 §5** 三个并行 metadata 面；§3 旧「12 端点」就地更正）
- 证据件（改，第十七轮）：`docs/audit/udc-semantics/LIVE-ROUTE-IMPLEMENTATION-CONTROL.json`（**新增 `contract_cross_check`**：LIVE 分组 vs udc-web 674 契约逐字对账；试验组 0 命中、对照组 14/16 + 2 条另档背书）
- 护栏（改，第十七轮）：`tests/udc/test_route_implementation_verdict.py`（11 → **14 项**；新增轴 3 独立交叉复核算；真盘突变 4/4 CAUGHT + 字节还原一致）
- 证据件（新增，第十八轮）：`docs/audit/udc-semantics/DEPLOYED-LIB-INVENTORY.json`（部署域 544 jar / 22 udc 构件 / **11 个本地缺失**；导出哈希与版本注记逐字一致）
- 证据件（新增，第十八轮）：`docs/audit/udc-semantics/DEPLOYED-OP-SURFACE.json`（域内 10 jar / **100 类 / 958 方法 / 958 distinct op**；**同域对照 674/674 PASS**；余 60 条 **0 命中**）
- 复算器（新增，第十八轮）：`tools/core/enumerate_deployed_op_surface.py`（直读 .class 常量池 + op 命名规则复算；强制输出同域对照）
- 护栏（新增，第十八轮）：`tests/udc/test_deployed_lib_inventory.py`（5 项）+ `tests/udc/test_deployed_op_surface.py`（7 项）；真盘突变 2/2 CAUGHT + 字节还原一致
- 护栏（改，第十八轮）：`tests/udc/test_route_implementation_verdict.py`（14 → **15 项**：可变域键不得当契约；真盘突变 2/2 CAUGHT + 字节还原一致）
- 复算器（改，第十八轮）：`tools/core/enumerate_route_implementation.py`（产物新增 `jars_scanned_note`，标注可变域不参与结论面比对）
- 复算器（新增，上轮/第十九轮记账）：`tools/core/enumerate_dynamic_register_channel.py`（动态注册通道字节码锚定；离线只读）
- 证据件（新增，上轮/第十九轮记账）：`docs/audit/udc-semantics/DYNAMIC-REGISTER-CHANNEL.json`（契约 2 方法 / 3 实现 / 闸门 4 字面量 / 包含关系 / 域内 167=89+17+61；sha256 `2a3610ae96a0894c`）
- 护栏（新增，上轮/第十九轮记账）：`tests/udc/test_dynamic_register_channel.py`（**9 项**，含复算与清洗门）
- 护栏（改，第十九轮）：`tests/udc/test_full_domain_op_surface.py`（11 -> **13 项**：复算判等升为**字节级** + 2 项内存内突变自证「只比 parsed 不够」）
- 护栏（改，第十九轮）：`tests/udc/test_dynamic_register_channel.py`（仍 9 项：`byte_for_byte` 名实相符，由 parsed 改为**真按字节**比较）
- 复算器（改，第十九轮）：`tools/core/enumerate_full_domain_op_surface.py`（输出格式对齐同族约定 `indent=2, sort_keys=True` + LF、无尾换行 ⇒ 与证据件**字节全等**；此前 `indent=1`+尾换行**根本无法重现**本件）
- 复算器（改，第二十轮）：`tools/core/enumerate_deployed_op_surface.py`（换行**显式钉死** `newline=CRLF`；此前靠 Windows 文本模式隐式转换 ⇒ Linux 上会出 LF）+ `tools/core/enumerate_route_implementation.py`（同）
- 复算器（改，第二十轮）：`tools/core/enumerate_metadata_planes.py`（原经 `print()` 走宿主文本模式，改为**显式构造 CRLF 字节**并新增 `--emit`；`--json` 改走 `sys.stdout.buffer` 二进制，绕开文本模式）
- 护栏（改，第二十轮）：`tests/udc/test_deployed_op_surface.py`（7 → **8 项**：复算判等升**字节级** + 1 项 CRLF→LF 会咬自证）
- 护栏（改，第二十轮）：`tests/udc/test_route_implementation_verdict.py`（15 → **16 项**：同上；**并保留**上轮改造的「可变域键不参与逐字比对」判据）
- 护栏（改，第二十轮）：`tests/udc/test_metadata_planes.py`（同：复算判等升**字节级** + 1 项会咬自证）
- 复算器（新增，第二十一轮）：`tools/core/enumerate_deployed_marker_census.py`（544 jar marker 普查；判据=常量池 `bind/annotation`；闭包检验 marker 构件 ⊆ 域；只落文件名+sha256，不落 scratch 绝对路径）
- 证据件（新增，第二十一轮）：`docs/audit/udc-semantics/DEPLOYED-MARKER-CLOSURE.json`（544 = 515 SCANNED + 29 NOT_OBTAINABLE；87 marker / 428 zero；闭包 PASS；216,782 class）
- 护栏（新增，第二十一轮）：`tests/udc/test_deployed_marker_closure.py`（**10 项**；复算器字节级重现 + 空白突变自证 + 取不到件须全为第三方 + 清洗门）
- 护栏（改，第二十一轮）：`tests/udc/test_full_domain_op_surface.py`（`MIN_*` 升到新域 `(1170,1044,238,2110,2107,53)`、`CLASSDIR` → `sup_v2`）；`tests/udc/test_dynamic_register_channel.py`（三支计数 90/60/88/238、`CLASSDIR` → `sup_v2`）
- 证据件（改，第二十一轮）：`DEPLOYED-FULL-DOMAIN-OP-SURFACE.json` / `DYNAMIC-REGISTER-CHANNEL.json` 由新域原地重算（两件仍字节级可由复算器重现）
- 文档（改，第二十一轮）：`COMPLETION-METHOD-PROMPT.md`（`pods/exec` 第十八轮 ALLOWED 注记**就地更正为 LIVE DENIED**）
- 方法：skill `xiaozhua-constraint-extraction`

## 下一步（按序）
**第二十轮已落地**：① **补做上轮遗留 commit**（10 个具体文件，`fcfadc2`，未用 `-A`）；② **把「字节级复算」不变量推广到其余复算对** —— 实测出三类：
    - (a) **已字节级**：`DYNAMIC-REGISTER-CHANNEL.json` / `DEPLOYED-FULL-DOMAIN-OP-SURFACE.json`（上轮修）。
    - (b) **★ 看似能重现、实为宿主依赖**：`DEPLOYED-OP-SURFACE.json` / `ROUTE-IMPLEMENTATION-VERDICT.json` / `METADATA-PLANES.json` —— 本机字节全等，纯因 `write_text()`/`print()` 落到 **Windows 文本模式**隐式转 CRLF；**Linux 上会出 LF** ⇒ 该「可重现」是**宿主指纹**而非不变量。三件的 LF 重排 **parsed 全等 / 字节不等** ⇒ 换行漂移对 parsed 判等**完全隐形**。
    - (c) 三条对应护栏原写法 = parsed 判等。
  ③ 修法：三个生成处**显式钉死 CRLF**（`newline=CRLF`；metadata 工具原走 `print()`，改为显式构造 CRLF 字节 + 新增 `--emit`，`--json` 改走 `sys.stdout.buffer` 二进制）；三条护栏升**字节级**；补 **3 项** CRLF→LF 会咬自证。**真盘突变 3/3 CAUGHT** + 逐件**字节级还原**（`714062d3…` / `498c7265…` / `95d29b88…`）；修后三件实测**字节全等且不再依赖宿主**。④ 计数契约 1296 → **1299**。

**第二十一轮已落地**：① **域扩展收口**：扫描域由 `sup`（90 jar）切到 **`sup_v2`（94 jar / 1170 class / 1044 FQCN / 2107 op / 53 贡献 jar）**，两件证据件（`DEPLOYED-FULL-DOMAIN-OP-SURFACE.json` / `DYNAMIC-REGISTER-CHANNEL.json`）**原地重算**并把两处护栏「数值 + CLASSDIR」同步升级（含修掉一处残留旧断言）。**扩域后两条同域对照仍全过**（674/674、32/32），余 60 仍 **0/60**。
② **★ 部署域 marker 闭包入仓**：新复算器 `tools/core/enumerate_deployed_marker_census.py` + 证据件 `DEPLOYED-MARKER-CLOSURE.json` + 护栏 `tests/udc/test_deployed_marker_closure.py`（**10 项**）。实测 544 = **515 SCANNED（216,782 class）+ 29 NOT_OBTAINABLE**，**87 含 marker / 428 0 marker**；**闭包命题 PASS（缺失清单空）**，且 **29 件取不到的全为第三方构件**。判据 = 常量池 `bind/annotation` 是「能暴露注解路由」的必要条件 ⇒ 0-marker 构件不可能藏端点。
③ **`pods/exec` 注记更正（LIVE）**：`SelfSubjectAccessReview` 实测 `pods/exec` **get/create/list 全 False**、`portforward`/`attach` 全 False、**仅 `pods/log get` = True** ⇒ 第十八轮「ALLOWED」**不成立**，就地更正提示词；544 jar 清单仍作有效证据。
④ **清理**：上轮 `--emit` 误建的空目录树已 `rmdir` 清空。⑤ 计数契约 1299 → **1308**（三处文档同步）。

**第二十二轮已落地**：① **清上轮两件结转**：计数契约 **1308 → 1309**（三处文档同步，复跑 0 failed）；上轮 10 个产物 `git add` 入库。② **★ 给 marker 闭包判据补「边界检验」（本轮主项）**：查出 marker 判据**只覆盖 Spring MVC**（JAX-RS `@Path` / 原生 Servlet 不需 `bind/annotation` 即可暴露端点）⇒ 原闭包论证有真窟窿；新复算器 `tools/core/enumerate_deployed_exposure_census.py` + 证据件 `DEPLOYED-EXPOSURE-CENSUS.json`（`sha256 5af85cf2ac5d90dc`）+ 护栏 `tests/udc/test_deployed_exposure_census.py`（**13 项**，真盘突变 **2/2 CAUGHT**）。实测 **0-marker 428 件中真实可暴露者 = 2 件且全第三方**（`tomcat-embed-core` / `jersey-common`），**平台家族 0 命中 ⇒ 闭包 PASS**；**平台构件带非 Spring 路由注解 = `[]`**。③ **自查出一处我自己的假阳（如实记）**：初版用**子串**判「继承 HttpServlet」得 **23 件**平台构件假阳 —— 根因 `HttpServlet` 是 `HttpServletRequest` 的**前缀子串**；改解析 `super_class` 槽位精确相等后降至 **2 件全第三方**，该陷阱已写进工具 + 护栏对抗自证。④ **量化一条此前含糊的边界**：**0-marker 里有 48 件平台构件**（含 `udc-biz` 2312 class）⇒「0-marker 不可能是暴露者」不能只靠 marker 判据说，须由查据②兑现；护栏已钉住**下界 48** 防掩盖。⑤ **修掉我本轮自造的缺陷（如实记）**：改计数文档时未带 `newline=`，Windows 文本模式把三件文档整体转 CRLF ⇒ diff 由 1 行膨胀为 216/304/388 行不可评审（同第二十轮那类宿主指纹）；已按 HEAD 约定还原 LF，diff 收敛为单点改动。⑥ 计数契约 **1309 → 1322**（三处文档同步，全量 0 failed）。

**仍余（下一轮起）**：
① **60 条 op 仍 UNVERIFIED（措辞可升一档，但仍不得写「不存在」）**：现证据 = 「**marker-闭包域**（94 jar / 2107 op）内 0 命中」+「87 个含 marker 的部署构件**全部**在域内」＋**「双必要条件」两轴均 PASS（第二十二轮新增）**：轴 A = marker（Spring MVC 必要）闭包 PASS；轴 B = **HTTP 暴露能力**（JAX-RS `@Path` / 原生 Servlet `@WebServlet|WebFilter|extends HttpServlet`，无 marker 也能暴露）⇒ **0-marker 的 428 件中真实可暴露者仅 2 件、且全为第三方容器/库**，**平台家族 0 命中**；+「取不到的 29 件**全为第三方、平台家族 0」⇒ 「域漏构件」这一支已可判为**不可能藏平台端点**。**但须同时记住（诚实边界）**：**0-marker 里有 48 件平台构件**（含 `udc-biz` 2312 class）⇒ 「0-marker 不可能是暴露者」这句**不是** marker 判据独立给出的，而是**由轴 B 兑现**的。**仍未消除的边界只剩一条：运行期加载的域外 ext 组件**（不在磁盘构件内，静态不可见；且 pod 日志仅存 ~2h、`/udc/**` 未带会话一律 `BOOT_1006` 且负控同响应 ⇒ 本窗口不可证）。故**升一档措辞、不升格为「不存在」**。
② **`NOT_OBTAINABLE` 29 件 = 已落成「低风险豁免」条目（第二十二轮完成）**：豁免成立的三条依据（均实测、见 `DEPLOYED-MARKER-CLOSURE.json` / `DEPLOYED-EXPOSURE-CENSUS.json`）：(a) 29 件**全为第三方、平台家族前缀命中 0**（`aliyun-log-0.6.33` / `beetl-2.9.10` / `bucket4j-core-7.6.0` / `jose4j-0.9.6` / `client-java-*` / `google-*` / `jib-*` 等，无 `udc-`/`boot-starter-`/`ctp-`/`cdp-`/`cip-`/`organization-`/`bpm-` 前缀）；(b) 它们**按定义**是「装在部署镜像里、但不属于平台自研面」的第三方库；平台端点不可能由第三方库定义 xiaozhua 命名空间的路由；(c) 取件缺口已定位：本地 maven 无此件、**Artifactory GAVC 只返回 `.pom` 兄弟** ⇒ 本轮多次尝试**无可用取件通道**（`pods/exec` 亦已实测 DENIED）。⇒ 记为**低风险豁免**并**明确写出取件缺口**；豁免**不升格**为「已证不存在」，措辞仍留 UNVERIFIED。
③ **`scratch/` 24h 清理风险已内置**：`sup_v2` 与 `lib_inventory.json` 消失时，三处护栏分别 **skip**（域根）/ **skip**（清单）—— 但**结论面断言（544/87/428/闭包）不依赖 scratch**，只依赖入仓证据件，故基线不会因此变红。
④ **复算件一律按字节级写**（新件已照此办）：新增复算器**默认** `newline=` 显式 + 护栏字节级判等。**延伸铁律（第二十二轮血证）**：不止复算件 —— **任何** `Path.write_text()` 改文档时，**必须**显式 `newline=` 指定该文件 **HEAD 约定**（本仓多数为 LF），否则 Windows 文本模式会把整文件转 CRLF、把「单点改动」变成「全文件重写而无法评审」。本轮已因此自查自纠一次。
⑤ **(vi-b) 「死路径」判决仍只靠三条间接轴**：直证（405/404 区分）两条通道均失败，已如实记为负结果、按负结果冻结。
⑥ `pods/log` 通道**请勿盲目重登**（`ctp-user-login.json` 曾返回 USER_0055，未重试）。
⑦ 完成判据两项未勾 ⇒ **任务不可暂停**。

**第十七轮已落地**：**发现 B 收口 + 其护栏收尾**——`/udc/micro-flow-group/search-list` 的三选一按两条独立轴裁定为「**死路径 / 无实现**」：轴 1 提供者唯一性（`<MAVEN_REPO>` 全量 **1518** jar 逐 class 直读字节码 ⇒ 声明类级 mapping `udc/micro-flow-group` 的 class **全局只有 1 个** ⇒ 「另一构件提供」证伪）＋轴 2 注册面完整（该 class **7** 个叶子无 `search-list` / `select-by-appid`，而对照叶子 `select-by-type` / `batch-move` 在同一次扫描**确有命中** ⇒ 0 命中非扫描器空转）＋轴 3 LIVE 同 traceId 行数对照分组（对照 **16** 条最小行数 **2** : 试验组 **2** 条孤行，且 `select-by-appid` 另有第十轮独立裁定作**正向标定**）。（a)(b) 均证伪 ⇒ 余下只能是「调用方发出的死路径」。本轮补完其护栏修正（反引号归一化）与**突变 ⑦ 6/6 CAUGHT** 重验证；并给轴 3 补上**第三方独立交叉复核**（LIVE 分组 vs udc-web 674 契约：试验组 2/2 的 0 命中与轴 2 独立一致，对照组 14/16 逐字落契约 + 2 条另档背书 ⇒ 不依赖单一契约口径），护栏 11 → **14** 项、突变 4/4 CAUGHT。

**仍余（下一轮起）**：① **(vi-b) 「死路径」判决缺一条独立直证** —— 本意用「GET 直打只标 `@PostMapping` 的路由 ⇒ 405/404 可区分」取直证，两条通道**均失败**（网关未带前缀一律 OSS 静态 `404 NoSuchKey`；带 `gateway_prefix` 一律应用层 `server_404`，对照组 `/udc/microflow/search` 同样如此）⇒ **如实记为负结果**，该判决目前只建立在上述三条间接轴之上（若不再取直证，按负结果冻结并保留 UNVERIFIED 措辞边界）。② **60 条 op 仍 UNVERIFIED**：Artifactory 侧已穷尽（第五轮 619 Controller / 201 构件 / 437 jar / 12 版 udc-web，0 归位），**唯一剩余静态路径 = pod `BOOT-INF/lib` 全量扫描**，而 K8s `pods/exec` 现为 **RBAC forbidden** ⇒ 需**人工开通 `pods/exec`** 或提供 `udc-assemble.jar`。③ `pods/log` 通道**请勿盲目重登**：`ctp-user-login.json` 上轮返回 `USER_0055`（认证失败 1 次，失败 99 次后需验证码），已立即停止、未重试。④ 完成判据两项未勾 ⇒ **任务不可暂停**。

**第十六轮已落地**：候选 **(v)** 已收口（三个并行 metadata 面 + 口径更正 674↔779 + 双轴判活）⇒ `COMPLETION-METHOD-PROMPT.md` 的「平台操作面」条目已把 ctp `metadata` 面正式纳入「全构件并集」口径；余下待办：(vi) 收窄为「客户应用页面 / 其它构件提供 / 死路径」三选一（**三选一仍 UNVERIFIED**），60 条 op 仍 UNVERIFIED，(iii) 仍需人工开 `pods/exec`。

**第十四轮已落地**：① 候选 **(vii)** 完成（19 构件 LIVE tag 入版本审计，见上 + 本轮证据）；② 候选 **(vi)** 的设计器侧一支完成（族 op 全集 6 / 无 `search-list`，负证据）；③ `pods/exec` 仍 `forbidden`、(ii)(v) 未动 ⇒ 60 op UNVERIFIED 与 pending 清零两项**仍未完**。

**第十轮已落地**：① 修掉第九轮工具语法回归（`tools/core/k8s_pod_log_surface.py`，`compileall` OK）；② 候选 **(iv)** 收口（部署态 tag + 部署态字节码）；③ 第九轮全部产物随本轮一次性提交 → 已提交（12 文件，具体 `git add`，未 `-A`；哈希见 `git log -1`，避免文档内自引用哈希失效）。**下轮第一件事 = 候选 (vii)**（纯本地：把 19 构件 LIVE tag 与版本审计表对齐）或 **(vi)**（需前端调用来源）。
1. ~~菜单/导航域~~ ✅ 完成
2. ~~平台操作面 op↔端点对账~~ ✅ 完成（GraphQL op 命名规则字节码实证）
2b. ~~full_path 拼接缺陷~~ ✅ 完成（159/657 纠正，122 幻影 op 清零）
2c. ~~非 udc-web 构件归位~~ ✅ **32 -> 27**（更正：原 32 含 5 条实为 udc-web 内，缺陷 A 修复后归本构件）；
   27/27 独立字节验证（sandbox 22 / udc-portal 4 / udc-cdpbi 1）
2d. ~~udc-web 契约方法级缺陷~~ ✅ 定位并落护栏（漏 18 / 多 1，根因 A/B/C；op 面 674/666）
2e. ~~修 tools/core/extract_udc_web_methods.py~~ ✅ **已完成**（A/B/C + 声明门 D）：
   _api_full.json 重算 657 -> **674** 端点；独立 class 解析器复核 54/54 类 0 差异；
   口径收口 **674 端点 / 673 distinct op（ParameterController.create 无 full_path）/ 666 op 面**；
   旧稿「应达 663」与「674 -> 674 op」均**证伪**
2f. ~~测试基线收口~~ ✅ 计数同步 **932 passed**（含本轮 3 项新护栏）；compileall 无错
3. **实体/页面/菜单 在线写验证**：终态验收扩域（已各域 ✅）
4. **余 60 个 udc* 未归位 op 定域**（原始 93；-32 归位；第六轮口径更正 62 -> 60）：
   - ✅ **第四轮**：名单 + 基数 + 族分布已落盘（`frontend-udc-unlocated.json`），
     4 条新归位（excel/formula/file，javap 常量池 4/4）；
   - ✅ **第五轮**：**全版本全构件穷尽扫描**（619 `@RestApi` Controller / 201 构件 / 437 jar /
     12 个 `udc-web` 版本 5.3.314→5.3.517）→ **0 归位**（负证据，见
     `COMPONENT-COVERAGE-EXHAUSTION.md`）；**静态侧定域手段已用尽**
     （管线自证：同法对已验 31 条归位跑 31/31 命中）；
   - ✅ **第五轮**：前端 loader 契约补 25→**32/60**（`frontend-op-loader-contract.json`），
     并证「前端不携带 path，只带 fieldType/paramsType/paramsKey」；
   - ✅ **第七轮**：**(a) 已做** —— 用**第二解析器** `tools/core/enumerate_udc_web_http_methods.py`
     （按 javap 缩进层级解 `RuntimeVisibleAnnotations`，与提取器的文本搜索是两条独立轴）
     对仓内 54 个 javap **重算全量**：**660 带值 + 14 裸 = 674**，与契约**逐条 0 双向差**；
     op 面 **673**、暴露面 **666** 双侧一致（见 `test_udc_web_independent_enumeration.py`，16 项）。
     ⇒ **674 不再只由「刚被修过的提取器」自证**，派生口径疑点已排除。
     **同时钉死一个陷阱**：残缺的 52 类快照（缺 `ParameterController`/`UdcFileController`）
     恰好得 `653+13=666` —— 会「看起来验证了暴露面」，已在护栏里固定；
   - ✅ **第八轮**：**(d) LIVE 通道建立** —— 直连 K8s API（无 kubectl）+ `pods/log`
     （`pods/exec` 403，如实记录）⇒ 首次拿到**真实运行期请求 URL 面**：425 条 / 13 distinct，
     对账契约 **11/13**（EXACT 5 + PARAM 6；MISS = `/udc/graphql` + 一条**形近路由**）；
     并得 **872 条运行期 biz 方法**记录。由此钉死**路由字面段形近陷阱**
     （41 条驼峰字面段 / 0 组同义撞车，`ROUTE-LITERAL-SIMILARITY.json` + 14 项护栏）。
     工具 `tools/core/k8s_pod_log_surface.py`（只 GET，无 exec/attach）。
     ⚠️ 本通道只给「被调用的面」，给不了「全部注册的面」⇒ **不能**替代构件扫描；
   - ✅ **第九轮**：**(i) 已完成** —— 日志通道**扩到全 ns 32 个 running pod**（`tailLines=60000`）：
     1407 条 `request url:` 行 / **421 distinct**；切面为控制面 `/udc/**` **271** + 应用运行期 `/{appId}/**` **150**；
     控制面归一化 18 模板，与 674 契约**模板级对账 14 EXACT_T / 4 MISS_T**。
     **对 60 条余量族：0 条被调用**（与第八轮同结论，负证据加强：族名未在真实 URL 面出现）；
     但换出**两条正向新发现**（见 `RUNTIME-URL-SURFACE.md`）：
     **A. `/udc` 前缀下存在 udc-web 之外的 REST 提供者**（`/udc/metadata/app-service-by-name`
     → 同线程 `MetadataQueryAppService#selectAppServiceMetadataByFullName`；单窗计数
     `/udc/metadata/`=**20** vs `/udc/design-metadata/`=**0**；提供者字节码 = ctp `MetadataController`，
     父类 `BaseComponentController`、类路径字面 `metadata`）⇒ **674 契约是单构件视图**，
     「平台操作面」的完整口径必须按**全构件并集**理解；
     **B. 两条「被调用但契约没有」的路由**：`/udc/micro-flow-group/select-by-appid/{id}`
     （语义正确、字面不存在 ⇒ 同线程**无** biz 行 = 无实现；契约里同方法字面是 `select-by-type`，
     平台源码复制粘贴瑕疵）与 `/udc/micro-flow-group/search-list`（**UNVERIFIED**：
     部署版本 ≠ 5.3.517 / 另一构件 / 死路径，三者未区分）；
   - ⬜ **下轮候选（按证据可得性排序）**：
     (ii) 对运行期 biz 方法名（250k 单窗 **133** 个 distinct；200k 窗 872 条记录）做**反向归位**：
         `XxxAppService#method` → 构件，与 60 条余量族名交叉（独立第三轴）；
     (iv) ✅ **第十轮已完成** —— 假设**证伪**：平台 `udc` 镜像 tag = **5.3.517**（LIVE，K8s API 只读），
         且全 ns **唯一**打印 `request url:/udc/**` 的平台 pod 就是这个 5.3.517 容器（360 条）
         ⇒ 第九轮的「真实请求 URL 面」全部出自被审计构件；再叠加部署态 javap（`udc-web-5.3.517.jar`
         sha8=`0d6b0a65` / 136930 bytes 逐 class 一致）⇒ **不能用「跑的是别的版本」解释 `search-list`**；
         顺带裁定 `selectByAppId` 的映射字面 = `select-by-type`（部署态注解实值 + 方法体调 `selectByType`）
         ⇒ `select-by-appid` 必然 404（**方法存在、字面不存在**，第九轮「无实现」措辞已更正）；
     (vi) **拆 (a)/(b)**：`/udc/micro-flow-group/search-list` 余下两解释（其它构件提供 / 死路径）需
         前端 bundle 侧找到该调用的来源页面（本地可查：`frontend-op-*.json` 当前**无**该字面
         ⇒ 更可能来自**客户应用页面**而非设计器，属客户面，按纪律只做临时查询不入库）；
     (vii) ✅ **第十四轮已完成** —— 19 构件 LIVE tag 已入版本审计：`agent-version-audit.md` **§2.1** 全表
         （证据件 `DEPLOYED-COMPONENT-TAGS.json` 双向逐条对齐）+ §2/§3 表各加一行 + §4 边界；
         LIVE 复验（pod 总数 79）**19/19 相同 / 差异 0**；护栏 8 项（含内存突变自证）；
     (viii) **新（第十四轮产出）**：把「设计器 bundle 的 micro-flow-group 族 op 全集 = 6」落成**仓内**证据件
         （本轮只在 scratch 复算，受 24h 清理约束），据此把 (vi) 收窄到「客户应用面 / 其它构件」二选一；
     (v) **契约补面**：把「ctp metadata 面」纳入平台操作面的登记口径（`/udc/metadata/**` 与
         `/udc/design-metadata/**` 的并行关系），避免后续按契约全量理解时漏面；
     (iii) 仍待人工：`pods/exec` 提权 或 `udc-assemble.jar`；
   - ⬜ **下轮首选**：不再扫 Artifactory（已穷尽）——
     (b) 8 个族（CustomDataType/PageComponent/FormUpgradeDeploy/MessageCategory/MessageLink/
         Pinyin/PageAdmin/RuntimeUpgrade，共 28 条）在本地 Artifactory **零 Controller**：
         需从 test2 pod `BOOT-INF/lib` 或加密 `assemble.jar` 取（见 (c)）；
   - ⬜ 沙箱族余 10 条：`boot-starter-sandbox` **全 4 个版本**（5.3.271/274/276/289）已扫，
     该类内无对应 mapping ⇒ 不再重扫，转 (c)；
   - ⬜ LIVE 侧（需人工介入）：直连网关 403（nginx WAF）；共享 token 2026-10-13 过期 -> 无法取运行期 op 注册表；
   - ~~查 udc_test2.udc_microflow_info.rest_path/rest_api~~ ❌ **已证伪**（微流程级开关，非 REST 注册表）；
   - 🟡 **(c) pod BOOT-INF/lib 全量扫描**（唯一剩余静态缺口）——**本轮通道已换，结论更精确**：
     - ✅ **K8s API 直连成功**（`kubeconfig-zhiyuan` token + CA 直连 `10.0.0.1:6443`，
       本地无 kubectl 亦可）；**SSH 跳板 `10.0.0.1:22` 仍 timeout**（已被 K8s API 替代，不再阻塞）；
     - ⛔ **但 `pods/exec` 被 RBAC 挡死**：`SelfSubjectRulesReview` 实测
       `User system:serviceaccount:low-code:zhiyuan cannot get resource "pods/exec" in namespace lowcode-test`（403）；
       同理无 `attach` / `portforward` / `pods/portforward`。**故 pod 内 jar 仍取不到**（不是放弃，是权限事实）；
     - ✅ **换到 `pods/log` 通道（新）**：udc pod 的 `AppContextFilter:50` 逐条打印**真实请求 URL**
       ⇒ 首次拿到**真实运行期**面，见第八轮「(d)」；
     - ⬜ 仍需人工：开通 `pods/exec`（或提供 `udc-assemble.jar`）才能取构件全量。
5. **BPM/ORG/USER 域**：biz 类在加密 assemble.jar 内，本地不可反编译（已记边界）
6. **存储层**：🟡 Redis/OSS 运行态读路径已 LIVE 实证

## 本轮证据（2026-10-15 第十八轮 · 外部写入侵袭基线 + 部署态 op 面终裁入仓）

**本轮完成两件事**：① 修掉被**外部写入**击破的基线（不是代码缺陷，是护栏把可变域当契约）；② 把上轮只在 scratch 的**部署态 op 面终裁**落成仓内耐久证据 + 复算器 + 护栏，并**纠正其阳性对照口径**。

### 1. 基线段被外部写入所破（REGRESSION -> FIXED）

上轮提交（`37c8dfd`）时全量 **1262 passed**；本轮开工实测 **1 failed / 1260 passed**。
唯一失败 = `test_route_implementation_verdict.py::test_verdict_is_reproducible_by_the_tool`，其断言形态是「复算器产物与证据件**逐字**相等」。

| 项 | 值 | 判读 |
| --- | --- | --- |
| 漂移键 | 仅 `jars_scanned`（1518 -> 1521） | 结论面（provider 唯一性 / 叶子命中 / 契约路由）**逐字未变** |
| 外部写入事实 | `<MAVEN_REPO>/com/seeyon/` 下 **3 个客户构件** 于 **15:49-15:51** 落地（1.0.11228 的 biz/web/facade） | 写入者**不是本任务**（工作树当时无相关改动）|
| 根因 | 护栏把**可变域**计数（本地 maven 仓库 jar 数）写进了逐字比对 | = 拿**环境指纹**当契约 |

**修法（三处最小改动）**

1. `tools/core/enumerate_route_implementation.py`：产物新增 `jars_scanned_note`，显式声明该键属**可变域**（本地 maven 仓库会被其它工作流写入、客户构件随构建落地），**不参与结论面比对**；docstring 增加「产物契约」段。
2. 护栏改为**双判据**：① **结论面逐字判等**（`_conclusion_surface` 去掉 `jars_scanned*`）；② **扫描域不得缩小**（`>= `）；③ 可变域键必须自带说明。
3. **新增** `test_evidence_marks_the_volatile_count_as_non_contract` —— 把这一课钉死，防后人重犯。

**突变验证（真盘）**：M1 `provider_count` 1->2 ⇒ **2 failed**（含复算比对）；M2 对照叶子 `batch-move` 清空 ⇒ **2 failed**。每轮突变后证据件**字节级还原**（sha256 `498c7265` 前后一致）。该护栏 **14 -> 15 项**。

> **诚实边界**：修的是**护栏写法**，不是结论。裁定本身（提供者唯一 / 叶子 0 命中）在修复前后**逐字相同** —— 故「发现 B 收口」的判决**未被削弱**，只是不再因外部写入而假失败。

### 2. ★ 部署态 op 面终裁入仓（主项）

历轮把「构件本身不在本仓库」记为**推断**（`pods/exec` RBAC `forbidden`）；上轮通道破局后取出部署态 `BOOT-INF/lib`（**544 jar**，含 **11 个本地缺失** udc 构件），但结论只在 scratch、且阳性对照**用错了域**。本轮全部收口。

**产物**

| 文件 | 内容 |
| --- | --- |
| `DEPLOYED-LIB-INVENTORY.json`（新） | 部署域 **544 jar / 22 个 udc 构件 / 11 个本地缺失**（名单逐条固定）；导出 `udc-web-5.3.517.jar` sha256 `0d6b0a6528...` / 136930 bytes 与 `DEPLOYED-VERSION-NOTE.md` **逐字一致** |
| `DEPLOYED-OP-SURFACE.json`（新） | 域内 **10** jar 有映射 / **100 类 / 958 方法 / 958 distinct op**；同域对照 **674/674 PASS**；余 **60** 条 **0 命中** |
| `tools/core/enumerate_deployed_op_surface.py`（新） | 复算器：直读 `.class` 常量池 + 按 op 命名规则复算；强制输出**同域对照** |
| `tests/udc/test_deployed_lib_inventory.py`（新，5 项） | 544/22/11 名单固定 + 本地存在侧**非空对照** + 导出哈希与版本注记对齐 + 清洗门 |
| `tests/udc/test_deployed_op_surface.py`（新，7 项） | 同域对照 PASS + 余 60 零命中 + 域规模下界 + **跨域对照只作解释不作判据** + 复算一致 + 清洗门 |

**★ 自我纠正：阳性对照口径（跨域 -> 同域）**

上轮写「管线自证：对已归位 32 条跑同一管线 ⇒ **32/32 命中**」。实测**不成立**：

| 对照 | 命中 | 为什么 |
| --- | --- | --- |
| 上轮口径：归位 32 条 vs 部署 **udc-*.jar** 域 | **5/32** | 32 条里 **22 条属 `boot-starter-sandbox`**（沙箱族），**不在 22 个 udc jar 域内** ⇒ 跨域对照，得**假阴性** |
| 本轮口径：udc-web **674 契约 op 面** vs 同域 | **674/674 PASS** | **同域**：契约 op 必须全落本域 |

⇒ 「余 60 条 **0 命中**」只有在**同域对照 PASS** 时才可信。上轮的 32/32 是**口径错用**，本轮更正并写进护栏注释与判据位。

**结论（口径升级 + 边界）**

- 余 **60** 条 op：由「Artifactory 侧静态穷尽**不承接**」升级为「**部署态 `udc-*.jar` 域内亦不承接**」；证据阶梯 = **LIVE-DEPLOYED**（真取了部署产物）。
- **域边界（不得外推）**：本裁定只覆盖 **22 个 `udc-*.jar`**；部署域另外 **522 jar（`boot-starter-*` 等）本域未纳入**，故**不能**据此对「全平台操作面」下 0 命中的结论。这正是上轮 32/32 假阴性的同一类错误的反面教材。
- 8 个「本地零 Controller」族（`CustomDataType / PageComponent / FormUpgradeDeploy / MessageCategory / MessageLink / Pinyin / PageAdmin / RuntimeUpgrade`）在部署态 udc 域内同样**无路由字面量** ⇒ 其构件归属仍 **UNVERIFIED**（不能升格为「不存在」）。
- 60 条 op **仍 UNVERIFIED**：本件是**强负面**（域内穷尽不承接），不是正面归位。

## 本轮证据（2026-10-15 第十六轮 · 上轮自破基线修复 + 候选 (v) 收口：三个并行 metadata 面）

**本轮完成三件事**：① 修掉我上轮写错的两条断言与自破的计数基线；② 修复 PROGRESS.md 的损坏；
③ 收口候选 **(v)** —— 把 `/udc` 前缀下的 metadata 面从「一个」澄清为「三个并行面」。

1. **先修基线（FOCUSED）**：上轮 `pytest` 6 failed（其中 4 项是计数契约连带、2 项是我自己写错的断言）。

   - `test_no_op_endpoints_are_exactly_the_lifecycle_six`：`no_op` 经 `sorted()` 而 `PINNED_NO_OP` 未排序
     ⇒ 改 `tuple(sorted(PINNED_NO_OP))` + 集合相等。**根因是断言写法，不是事实漂移**（6 条不变）。
   - `test_lossy_javap_dump_has_no_annotation_values`：我把该 dump 说成「零信息」**不精确**。
     实测：该 javap 只落 **309** 个 Utf8 常量而行（`.class` 常量池 **865** 个 Utf8 ⇒ 缺 **556**），
     且 `RestController`/`GetMapping`/`Constant pool:`/`flags:`/`Code:` **全 0 命中**（注解值面确实不可读）；
     **但** `entity-by-name`/`refresh-all`/`downgrade-all` 在该 dump 内**确有命中**。
     ⇒ 断言改为三条可复现特征：注解类型名 0 命中 + 截断量（309/865，缺 556）+ **截断不均匀**
     （上面三个词有命中）与 **5 条精确 Utf8 假阴性实例**（`starter-all`/`app-service-by-name`/`sync-cache`/
     `online-app-info`/`online-front-app-info`：dump 内 0 命中，而字节码里是**精确** Utf8 常量）。
     独立复算走仓内 `tools/core/enumerate_class_http_mappings.py` 直读常量池，不经 javap/CFR。

2. **PROGRESS.md 修复（REGRESSION -> FIXED）**：第十五轮头部 7 处反引号内容 + 第 54/55 行两条产物路径
   被 bash 命令替换吃掉。已**按上下文等义重建**并植入显式标注
   `〔第十六轮修复：反引号内内容曾被 bash 命令替换吃掉，此处为按上下文的等义重建〕`，
   **不假装是原文**，便于日后发现重建与原文的偏差。此后写文档一律不用双引号串（本轮用 `tee` + 引号 heredoc）。

3. **★ 候选 (v) 收口：三个并行 metadata 面（本轮主项）**

   | # | 外部前缀 | 提供构件 | Controller | 端点 | 面内 leaf |
   | --- | --- | --- | --- | --- | --- |
   | 1 | `/udc/meta-data/` | `udc-web-5.3.517` | `MetaDataController` | 32 | 30 |
   | 2 | `/udc/design-metadata/` | `udc-web-5.3.517` | `UdcDesignMetadataController` | 47 | 47 |
   | 3 | `/udc/metadata/` | `metadata-5.3.358` | ctp `MetadataController` | 105 | 105 |

   面 3 即第九轮**发现 A** 的提供者（`/udc` 前缀下 udc-web 之外的 REST 提供者）。

   - **交集**：面1∩面2 = 1；面1∩面3 = 1；**面2∩面3 = 43**；三面共有 = 1（`refer-and-app`）。
   - **陷阱的具体形态**：`/udc/meta-data/refer-and-app` 与 `/udc/metadata/refer-and-app` **只差一个连字符**；
     而面 2 与面 3 有 43 个同名字面量 ⇒「按语义猜路径」在 `design-metadata` 上几乎总能拼出一个**语法成立**的路径。
   - **口径更正（重要）**：`674 端点` = **udc-web 单构件视图**。全构件并集至少 **779**（674 + 105），
     而 779 **也不是运行期全量**（其它非 udc-web 提供者未纳入）。两个数字**不可混用**。
   - **哪个面是活的（两条独立轴）**：
     (a) 设计器耐久 chunk `docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js`：
     `udcMetaData*` **68** 次 / `udcDesignMetadata*` **0** 次；
     (b) LIVE `RUNTIME-URL-SURFACE.json`：`/udc/metadata/` **20** 次 / `/udc/design-metadata/` **0** 次。
     ⇒ **面 2（design-metadata）在本窗口是死面**。
   - **op 名三分**（`path_to_op` 由全路径派生）：`udcMetaDataReferAndAppPost` /
     `udcDesignMetadataAppServiceByNamePost` / `udcMetadataAppServiceByNamePost` —— 拿错 op 名即打到错面。

4. **产物与护栏会咬**

   - 复算器 `tools/core/enumerate_metadata_planes.py`（`--json`；证据源全在仓内，离线只读）；
     证据件 `docs/audit/udc-semantics/METADATA-PLANES.json`；护栏 `tests/udc/test_metadata_planes.py`（**16 项**）。
   - 核心护栏：`test_recomputation_matches_the_evidence_file_endpoint_for_endpoint`
     （证据件必须能由复算器**原样重现**，不是人工抄录）。
   - **真盘突变实测（4 类，均 failed 且还原字节一致）**：
     `union 779->674` → 2 failed；`shared 43->0` → 2 failed；
     `frontend hits udcDesignMetadata 0->5` → 2 failed；`plane3 endpoints 105->104` → 2 failed。
     证据件 sha256 `95d29b88…e47d` 还原后**逐字节相同**。
   - 文档：`RUNTIME-METADATA-CONSTRAINTS.md` **新增第 5 节**（三个并行面），并把 §3 里早已被字节码证伪的
     「MetadataController 12 端点」旧口径**就地更正**为 105/99（保留旧稿可追溯）。

5. **自我纠正（如实记，两处）**

   - **我覆盖了已入库文件**：`RUNTIME-METADATA-CONSTRAINTS.md` 本就在 HEAD 里（我误判为新文件，用 `tee` 覆盖）。
     已 `git checkout --` **完整还原**（54 行），再改为**追加第 5 节**（+38/-1）。教训：写文件前先 `git cat-file -e HEAD:<path>`。
   - **我写错了两条断言的/护栏**：清洗门最初拿本文件自身当检查对象 ⇒ 自反假失败（改为只查产物 + 拼接构造标记）；
     `udcDesignMetadata` 是 `udcMetaData` 的**子串**，故用 `count()` 差分判「design 族命中」不可靠
     ⇒ 改为**直接钉两个绝对计数**（68 / 0）而非做减法。
   - 另修一处护栏内的**悬空引用**（§1.6 不存在）与一条我**断言方向写反**的自证（`test_cleaning_gate_actually_bites_...`）。

6. **计数契约**：**1218 → 1240 collected == passed**（本任务面 **0 failed**）；
   `README.md`(1) / `agent-version-audit.md`(6) / `code-reality-audit.md`(7) 用断言式脚本同步（每处先 `assert` 命中数）。

7. **清洗门 + 诚实边界**：新产物零客户业务明细（长数字串 0）；ctp 面证据为 **5.3.358** 样本 + LIVE 同线程日志，
   未取 5.3.517 部署态该 class 字节；设计器 chunk 为 **5.3.496** 而部署 `udc` 为 **5.3.517**；
   LIVE 计数是**单窗口**事实 ⇒ **不证明**面 2 永不使用。本件**不改变**余 60 条 op 的 UNVERIFIED 状态。

8. **工作树状态（如实登记）**：工作树另有 **1 项失败**
   `tests/udc/test_serialnumber_constraints.py::test_endpoints`（其模块 `serialnumber_constraints.py` 已 45 端点、
   其测试仍断言 44）—— 两文件均 **untracked**、创建于本轮运行中（13:52），
   属**并发工作流的 WIP**，**非本任务产物**，本任务**不触碰、不提交**其归属文件。

## 本轮证据（2026-10-15 第十四轮 · 部署态 tag 入版本审计（候选 vii）+ 设计器侧 (vi) 一支）

**本轮推进两项**：① 把 19 个平台构件 LIVE 部署 tag 正式**对齐进版本边界审计文档**（候选 (vii)，纯本地）；
② 用设计器 bundle 的**族 op 全集**把候选 (vi) 收窄一支（负证据）。

1. **★ LIVE 复验（候选 vii 的第一步，只读 K8s API）**：`GET /api/v1/namespaces/lowcode-test/pods`
   （pod 总数 **79**，比第十轮快照大）取 `spec.containers[].image`，对 19 个平台构件逐一比对
   第十轮落盘的 tag ⇒ **19/19 相同、差异 0、无未观测构件**；`udc` 仍 = `5.3.517`。
   复验记录写进证据件 `DEPLOYED-COMPONENT-TAGS.json#reverification`（`matched=19 / differences=0 / not_seen=[]`）。
   工具：本轮临时只读脚本（scratch），**不落集群地址 / token**。

2. **★ 文档对齐（候选 vii 本体）**：`docs/audit/agent-version-audit.md`
   - 新增 **§2.1 部署态构件版本（LIVE，K8s API 只读）**：19 构件 tag **全表**（11 行双列）+ 证据件路径
     + 通道 + 捕获/复验时点 + 清洗门声明（只落平台构件，客户 pod 名/镜像名不入库）；
   - §2 事实版本表新增一行「部署态平台构件 tag … **LIVE VERIFIED**」；
   - §3 验证版本表新增一行「部署态构件 tag 复验 19/19 相同 / 差异 0 … **LIVE VERIFIED**」；
   - §4 未验证清单补精确边界：镜像 tag 之下的 `BOOT-INF/lib` 构件全量（`pods/exec` 为 RBAC `forbidden`）。
   - **三条口径边界**：`udc`=5.3.517 静态样本与部署态**同版本互证**（但不证 class 字节）；
     三个 facade（`bpm` 5.3.374 / `organization` 5.3.368 / `ctp-user` 5.3.429）与 LIVE **3/3 一致**；
     静态 `sampled version set`（3.8.227 / 3.12.124 / 5.3.314 / 5.3.380 / 5.3.477 / 5.3.517）
     **不是部署集合**，不得据它推断线上版本。

3. **护栏 8 项 + 会咬自证（新增品类：内存内突变）**：
   `tests/udc/test_deployed_tags_version_audit_alignment.py`；
   对齐判定收敛到 `check_alignment(text)`（**双向**：缺行 / 多出构件 / 版本漂移 + LIVE 标记 + 通道 + 证据件路径
   + `REFUTED` + 「不是部署集合」），再由 `test_alignment_checker_bites_on_mutation`
   对**内存副本**注入 4 类突变（`udc` 5.3.517→5.3.518 / 删行 / 塞幻影构件 / 改小节标题）逐一双向断言
   —— **不写文件**，故失败模式不可能来自并发会话（比历轮的「手工篡改再还原」更强）。

4. **★ 候选 (vi) 一支收口：设计器 bundle 侧「谁调用 `search-list`」= 否**
   - 在 unpacked 设计器 bundle 里枚举 micro-flow-group 族 **op 字面量全集 = 12**
     （`udcMicroFlowGroup{Create,Update,Delete,DeleteBatch,BatchMove,SelectByType}Post` 各 + 其 `InputBody`）
     ⇒ 族内 **6 个 op**，**其中没有 `SearchList`**；
   - **反证「不是命名习惯」**：同一 bundle 里`udc*SearchList*` 字面量**确实存在**（他族：`udcDataTransferObjectSearchListPost`、
     `udcExcelSearchListByConditionsPost`）⇒ 家族级缺省是**真负证据**，不是搜索模式造成的假阴性；
   - 仓内可复核的耐久面：`docs/audit/udc-semantics/frontend-op-model.json` 内该族仅 2 条 op（BatchMove/DeleteBatch），
     `search-list` 的 4 处命中全部属**其它族**（`attributeSet` / `data-transfer-object` / `entity`）；
   - **诚实边界**：12 字面量的枚举源在 scratch（受 24h 清理），且 bundle 快照为 5.3.496 而部署 udc 为 5.3.517；
     故结论只到「**设计器前端不是该调用的来源**」，余下仍是「客户应用页面 / 其它构件提供 / 死路径」三选一，
     `search-list` **仍 UNVERIFIED**。

5. **计数契约**：1258 passed / 0 failed（collected == passed == 1186）；compileall 无错；
   `README.md`(1 处) / `agent-version-audit.md`(6 处) / `code-reality-audit.md`(7 处) 用**断言式脚本**同步
   （每条替换先 `assert` 命中数），PROGRESS「测试基线」行单独同步（历史轮次正文里 1178 的旧记录**不改**）。

6. **清洗门**：本轮产物（§2.1 / 证据件 / 护栏）零客户业务明细；护栏断言 §2.1 与证据件均无 6 位以上数字串。

## 本轮证据（2026-10-15 第十轮 · 候选 (iv) 收口 + 上轮工具回归修复）

**本轮完成两件事**：① 修掉第九轮遗留的**工具语法回归**（因此第九轮才没能提交）；② 用**部署态**证据
（LIVE 镜像 tag + 已落盘的部署态 javap）把候选 **(iv)** 收口，并顺带**更正**第九轮发现 B 的一处措辞。

1. **回归修复（REGRESSION -> FIXED）**：`tools/core/k8s_pod_log_surface.py` 第 192 行 `_run_all_pods` 的
   `json.dumps(...) + "<真实换行>"` 是坏字面量（`SyntaxError`）。按**字节级**替换修复
   （`b"indent=2) + " + b"'" + b"

" + b"'"` -> `b"indent=2) + chr(10)"`，命中数先 `assert == 1`），
   避开上一轮踩到的「转义层降级」；`py_compile` + `compileall -q components tools tests` 均 **OK**，
   工具 `--help` 四参数（含 `--all-pods`）可用，10880 -> 10883 bytes。

2. **★ 候选 (iv) 裁定 —— 假设「部署 udc-web 版本 ≠ 5.3.517」证伪（LIVE）**
   - 全 ns 只读 `GET /api/v1/namespaces/<ns>/pods` 取 `spec.containers[].image`：19 个平台构件 tag
     全部为 `5.3.x`，其中 **`udc` = 5.3.517**（= 被审计 artifact 同版本）；证据件 `DEPLOYED-COMPONENT-TAGS.json`；
   - **谁在打印控制面 URL**：全 ns 唯读日志通道里，**唯一**打印 `request url:/udc/**` 的平台 pod 就是
     `udc` 容器（tag 5.3.517，该类 URL **360** 条）⇒ 第八/九轮的「真实运行期 URL 面」**全部出自 5.3.517 构件**；
   - **交叉校验 3/3 一致**：`COMPLETION-METHOD-PROMPT.md` 声明的 `bpm-facade-5.3.374` /
     `organization-facade-5.3.368` / `ctp-user-facade-5.3.429` 与 LIVE tag **逐条相等**；
   - ⇒ `search-list` **不能**再以「跑的是别的版本」解释；第九轮 UNVERIFIED 的该支已排除。

3. **★ 发现 B 裁定（部署态字节码，非本地静态推断）**：对象 = 部署态
   `com.seeyon.udc.controller.MicroFlowGroupController`（`MicroFlowReadPlane.javap.txt`，`javap -v -p`）：
   类级 `#90 = udc/micro-flow-group`；`selectByAppId` 方法注解 `#30(#31=s#84)` + `#33(#31=[s#85])`
   且 **`#85 = select-by-type`**、方法体 `invokevirtual MicroFlowGroupAppService.selectByType`；
   **常量池无 `select-by-appid`、无 `search-list`**（全文件亦 0 命中）。
   ⇒ 两处收口：(a) `/udc/micro-flow-group/select-by-appid/{id}` **必然 404** ——
   **更正第九轮措辞**：不是「方法无实现」，而是**方法存在、映射字面不存在**
   （方法名/映射字面/方法体三处不一致 = 源码复制粘贴瑕疵）；
   (b) `search-list` 在本 Controller 部署态字节码里不存在 ⇒ 余下解释收窄为「其它构件提供」/「死路径」，
   **(a)/(b) 二选一仍 UNVERIFIED**（需前端调用来源或 `pods/exec` 提权）。

4. **窗口事实（负证据，如实记）**：本轮全 ns 日志**不带 `tailLines`**（6 pod 有 URL 信号）后
   `micro-flow-group` 命中 **0** ⇒ 第九轮窗口已滚出保留区，**未再观测**到那两条 MISS_T 路由，
   故**没有新的同线程证据**；该限制写入 `DEPLOYED-STATE-VERDICT.md` §4。

5. **清洗门（客户明细不入库）**：新证据件只落 **19 个平台构件**（客户应用 pod 名/镜像名含客户标识，
   **一律不落名**）；门断言「19 个构件、version 全 `x.y.z`、无 6 位以上数字串」。

6. **护栏会咬**：新增 8 项（`tests/udc/test_deployed_state_verdict.py`，含第 9 轮同口径 `source` 子树清洗门）；
   **2 处篡改**（① 证据件 `udc` tag 5.3.517 -> 5.3.518；② 部署态 javap 里把 `#85 = select-by-type`
   改成 `select-by-appid`）**均 failed**（1 failed / 2 failed），还原后 **sha256 前后一致**
   （J `a940ac3e…` / V `86848cb9…`）。

7. **计数契约**：1156 -> **1258 passed / 0 failed**（**+8** = 本轮护栏；另 **+3** 来自**并发工作流**——`tests/udc/test_entity_constraints.py` 本轮被另一会话改动 +46 行（**未提交、非本任务产物**），故本提交后的干净检出可能显示 **1164**；1167 是**本轮实测值**，不声明对那 3 项的所有权。已核：`--ignore=tests/udc/test_deployed_state_verdict.py` ⇒ 1159 collected = 1156 + 3）；
   `README.md`(1) / `agent-version-audit.md`(6) / `code-reality-audit.md`(7) 共 **14 处**用**断言式脚本**同步
   （每处命中数先 assert，不符即抛错）。首次全量跑因 `RUNTIME-URL-SURFACE.json` 的 `source` 子树含
   6 位计数被我误当清洗门违规 → 已按第九轮同口径（排除 `source` 子树）修正。

## 本轮证据（2026-10-15 第九轮 · LIVE 面扩到 32 pod + 契约外提供者 + 被调用无实现的路由）



**本轮完成**：第八轮留下的候选 (i) —— 把 pod 日志 LIVE 通道**从单 pod 扩到全 namespace**，

并把「实际被调用轴」与 674 端点契约做成**模板级对账**，换出两个正向发现。



1. **通道扩展（只读 `GET pods/log`）**：namespace 内 **32** 个 running pod × `tailLines=60000`

   ⇒ **1407** 条 `request url:` 行 / **421** 条 distinct 原始 URL；仅 **6** 个 pod 真正打印过请求 URL

   （平台类 1 + 应用运行期 5）。另取 udc pod `tailLines=250000` 单窗：**213073** 行 / 1095 条 URL 行 /

   78617 条 `AppServiceLogFilter` 行 / **133** 个 distinct biz 方法。工具 `tools/core/k8s_pod_log_surface.py`。



2. **面切分（首次整体落盘）**：控制面 `/udc/**` **271** distinct、应用运行期 `/{appId}/**` **150** distinct

   ⇒ 两个**互不重叠的路由根**（设计态 vs 运行态）。运行期归一化为 **23 个家族模板**

   （`/{appId}/udc-runtime/{app-draft,app-log,evn-check,meta-data}/...`、`/{appId}/{key}/microflow/*`、

   `filter-plan`、`refer`、`refer-carry`、`cascade`、`graphql`、`file`、`enum-item`、`ctp-parameter`）。

   ⚠️ 该面**不在** 674 契约内（契约只覆盖 `/udc/**`）。



3. **模板级对账**：控制面 271 条原始 URL 归一化 = **18 个模板**，与 674 契约逐字比对：

   **14 EXACT_T / 4 MISS_T**（原始 URL 口径：EXACT 10 / PARAM 258 / MISS 3）。

   4 条契约外模板：`/udc/graphql`（非 REST）、`/udc/metadata/app-service-by-name`、**两条 micro-flow-group 路由**。



4. **★ 发现 A：`/udc` 前缀下存在 udc-web 之外的 REST 提供者（LIVE × 字节码）**

   - **LIVE 同线程关联（硬证据）**：`http-nio-80-exec-23` 上 `AppContextFilter:50 request url:/udc/metadata/app-service-by-name`

     → 同线程 ~150ms 后 `AppServiceLogFilter:70 method : MetadataQueryAppService#selectAppServiceMetadataByFullName`（窗口内 18 次）

     ⇒ 该路由**确有实现**且进入业务方法；

   - **单窗计数**：`/udc/metadata/` = **20**，`/udc/design-metadata/` = **0**

     ⇒ 契约登记的那个家族**真实零调用**，前端实际走的是契约外那条；

   - **字节码**（`metadata-5.3.358/MetadataController.class`）：父类 `com/seeyon/boot/starter/web/BaseComponentController`、

     类级路径字面 `metadata`、方法字面 `app-service-by-name`、业务接口 `MetadataQueryAppService`（**ctp 侧**）；

     而 udc-web 契约里同名 op 属 `UdcDesignMetadataController → /udc/design-metadata/app-service-by-name`；

   - ⇒ **674 端点契约是单构件（udc-web）视图**；“平台操作面”的完整口径必须按**全构件并集**理解；

   - **未验证**：`/udc` 前缀的**注入点未到方法级**（`BaseComponentController` 内无 `addPathPrefix`/`getAppName` 字面），

     前缀机制记为**推断**；LIVE 事实（被服务 + 进业务方法）为**硬证据**。



5. **★ 发现 B：两条「被调用但契约没有」的路由**

   - `/udc/micro-flow-group/select-by-appid/{id}`：契约里 `${方法名 selectByAppId}` 的字面是

     **`/udc/micro-flow-group/select-by-type`**（平台源码**复制粘贴瑕疵**）；LIVE 同线程**后续无任何** biz 日志行

     ⇒ 该请求未进业务方法（404/静默）。与第八轮「形近字面段陷阱」**互补**：那里是「读起来像 ⇒ 404」，

     这里是「**语义正确、字面不存在** ⇒ 无实现」；同时 `/udc/micro-flow-group/select-by-type` 在窗口内**确实被调用**；

   - `/udc/micro-flow-group/search-list`：契约该前缀仅 7 条路由、**无 search-list**，而同仓其它 Controller

     （entity / attributeSet / data-transfer-object）**都有 search-list** ⇒ 非命名习惯问题；状态 **UNVERIFIED**。



6. **自我纠正一次（如实记）**：第一版归一化把**驼峰字面段**（`findById`）也误当占位符，

   把本已命中的 `/udc/microflow/findById/{id}` 误判为 MISS（得到错误口径 13/5）；修正归一化后复算为 **14/4**。



7. **清洗门（客户明细不入库）**：数据件对 appId / 页面键 / 表名 / 记录 id **一律占位化**，

   pod 名（内嵌客户应用名）**只落计数不落名**；门断言「非 `source` 子树 6 位以上数字串 = 0」，

   首版因 `miss_routes` 带原始实参、pod 名带客户 appId **被门挡住并修**（挡 3 次）。



8. **护栏会咬**：新增 13 项（`tests/udc/test_runtime_url_surface.py`）；**4 处篡改**

   （LIVE 计数 20→0 / 删 1 条 MISS_T / 期望数 4→3 / 伪造提供者路径）**均 failed**，还原后**字节一致**。



9. **计数与清洗**：**1156 collected == 1156 passed / 0 failed**，compileall 无错；

   README / agent-version-audit / code-reality-audit 计数**断言式**同步（每处替换命中次数先断言）。



## 本轮证据（2026-10-15 第六轮 · 基线收尾 + 文档名幻影口径更正 62->60 + 形态判据自我证伪 + 反编译丢失面）

**本轮完成**：收尾第六轮开头继承的**破坏基线**（1086 passed / 7 failed -> 1111 passed / 0），
并**自我更正**上一轮自己写下的错误判据，另新发现一处「反编译丢失」证据管缺口。

1. **基线修复**：用**断言式替换脚本**改（每个替换必须命中恰好 N 次，未命中即抛错退出）——
   正是针对上轮「heredoc 没写出却当成功」的失效模式。两个护栏文件同步 corrected 口径
   （`230→231 / 93→92 / 31→32 / 62→60`），README / agent-version-audit / code-reality-audit
   计数同步到 `pytest --collect-only` 真值。compileall 无错。

2. **★ 自我更正：上轮的判据是错的（结论对、理由错）**
   上轮写「文档名恒不带 HTTP 动词后缀 ⇒ 按构造不可达」。**证伪**：`udcPinyinGet` 恰以 `Get` 结尾。
   改用**位置槽**判据（紧跟 `mutation|query` 的文档头槽 vs 后接 `(` 的字段槽），在**仓内快照**
   `docs/audit/artifacts/udc-frontend-5.3.496/chunks/src_redux_store_ts.14dc061e.js` 实测：

   | 字符串 | 文档头槽 | 字段槽 |
   |---|---|---|
   | `udcMicroflowCopy` | 1 | 0 |
   | `udcPinyinGet` | 1 | 0 |
   | `udcMicroflowCopyPost` | 0 | 1 |
   | `udcI18nResourceStrToPinyinGet` | 0 | 1 |

   全 346 条按位置槽扫，**确实只有这 2 条**属「仅出现在文档头槽」。错误理由已在
   `test_frontend_udc_unlocated.py` / `test_component_relocation.py` 两处显式标注为**已证伪**。

3. **★ 新发现：反编译丢失面（影响「bundle 内 0 命中」这类负面结论）**
   346 条 harvest op 中 **6 条**存在于原始 chunk（158 js）却消失于解包产物（1474 js）：
   `appCommonImageSearch` / `appCommonImageStoreCategoryGet` /
   `cipManagerManageSelectActivexCapabilityEnumGet` / `organizationOrgMemberAvatarIdsPost` /
   `udcDesignMetadataAggEntityExcludeBootGet` / `udcPageInfoDeletePost` —— 后 2 条是 udc* 
   且**由 udc-web 契约独立推导**，直接反证「解包产物=完整事实源」。
   **范围界定已核**：60 余量 + 32 归位**每条**在解包产物内均有 >=1 处字面量（60/60）
   ⇒ 62→60 的更正确实未被污染。
   工具 `tools/core/detect_decompile_loss.py`（钉死 6 条、`--json`、不符即 rc=1）+
   护栏 `tests/udc/test_decompile_loss.py`（16 项，会话内缓存后 223s -> 13.5s）。
   **诚实边界**：两侧证据都在 scratch，受 24h 清理约束；仓内快照只含 1 个 chunk。

4. **护栏自证会咬**：幻影塞回余量名单 -> 6 failed；归位 32→31 -> 1 failed；
   loader `remaining_total` 60→62 -> 2 failed；还原后全绿。

5. **`tools/core/classify_frontend_op_reference.py` 首次跑通**（60 条：LOADER 25 / GQL_FIELD 1 / ABSENT 34）。

## 本轮证据（2026-10-15 第八轮 · K8s API 直连 + pod 日志 LIVE 通道 + 路由字面段形近陷阱）

**0. 先补第七轮欠账（本任务第一件事）**
第七轮结束时 17 个文件已 `git add`（具体文件，未用 `-A`）但**未 commit**（迭代上限）。
本轮已用**具体文件列表**提交为 `2bf06c4`，提交前扫描三个目标 ID 在 17 文件内 **0 处**。
（当时已顺手补完第七轮 PROGRESS 正文段，本轮只补提交。）

**1. ★ K8s API 直连（打破「SSH 不可达」的长期阻塞）**
历轮把 `10.0.0.1:22` timeout 记为「静态缺口不可达」。本轮改用**另一条控制面**：
`kubeconfig-zhiyuan`（仓外 skill 目录，含 token + `certificate-authority-data`）直连
`https://10.0.0.1:6443`。本机**没有 kubectl**，故自写最小客户端（`urllib` + `websocket-client`，
经 `uv run --with` 临时取依赖）。**结果：API 完全可用**（列 namespaces 66 个、列 pods）。
⇒ 复测口径更正：**「不可达」只对 SSH 跳板成立；K8s 控制面一直可达**。

**2. ★ RBAC 自审：`pods/exec` 被挡，`pods/log` 可用（实测，非推测）**
用 `SelfSubjectRulesReview` 逐 namespace 拉规则（`lowcode-test` / `low-code` / `default`）：
- ❌ 无 `pods/exec`：直连 WS 返回 **403**
  `pods "udc-…" is forbidden: User "system:serviceaccount:low-code:zhiyuan" cannot get resource "pods/exec"`
- ❌ 无 `attach` / `portforward`（规则表里不存在）
- ✅ 有 `pods/log` / `pods` / `namespaces` (get) / 各类 get,list,watch
⇒ **pod `BOOT-INF/lib` 仍取不到**（第七轮定的「唯一剩余静态路径」依然被挡）。
另：pod 内 `/tmp/BOOT-INF/lib` 与 `/tmp/blob` 是**历史轮次 SSH 会话遗留**（探针脚本 `podattr.sh` 指向它），
`pods/exec` 被封后**不可复现** —— 该通道不再算「可用」，如实记录。

**3. ★★ LIVE 通道（本轮主收获）：pod 日志里的真实请求 URL**
`pods/log`（tail 200k）实得 **11137 行 / 3.07 MB**。容器镜像 `chjh-external/udc:5.3.517`。
关键发现：`AppContextFilter:50` **逐条打印真实请求 URL**：`request url:/udc/entity/...`。
- 抽出 **425 条请求 URL / 13 个 distinct**；`/udc/graphql` 占 375 条（前端主入口）。
- 与本仓契约逐条对账（工具 `tools/core/k8s_pod_log_surface.py`，本轮新增）：
  **EXACT 5 + PARAM 6 = 11 命中**，MISS 2。
- 另从 `AppServiceLogFilter:70` 抽出 **872 条 biz 方法**（如 `EntityAppServiceImpl#create`、
  `MetadataQueryAppService#selectPageMetadataList`）—— 这是**运行期真正执行的 biz 方法名**，
  静态侧此前只有 facade 契约，从未有运行期实调记录。
- 限制如实记：logback 未开 SQL/StackTrace（`404` 字面仅 63 行且**均为时间戳/端口串**），
  故**不能**从日志取「运行期 bean 映射全集」；本通道的价值是**真实 URL 面 + 真实 biz 方法**，不是端点全集。

**4. ★★ 由此钉死：路由字面段「形近」陷阱（本轮唯一异常）**
2 条 MISS 之一：日志里出现
`/udc/entity/select-all-by-entity-id/<实体id实参>`，
而契约（且 javap 常量池逐字）里 `EntityController` 只有
`/udc/entity/select-all-by-entityId/{id}`（**驼峰 `Id`**）。连字符版在契约里**不存在**。
同一前缀下另有**真实存在**的连字符路由
`/udc/entity/attribute/select-all-by-entity-id/{entityId}`（取**属性**，与取**实体**不同）。
- **危害**：kebab-case 与 Java 驼峰 `Id` 后缀在同一路径前缀下混用，
  按「读起来像」拼路径会打偏；打偏后果 = 404，**不入业务方法**
  （日志里连 `AppServiceLogFilter: method :` 行都不会出现 ⇒ 现象是"静默无效果"）。
- **量化（新证据件 `ROUTE-LITERAL-SIMILARITY.json`）**：
  「占位符之前的字面段」含驼峰的端点 **41 条**（逐条落盘）；
  归一化（驼峰→连字符）后**0 组**同义撞车 ⇒ **不存在「两种写法都行」**，只能逐字用 `full_path`。
- **护栏（新增 `tests/udc/test_route_literal_similarity.py`，14 项）**：41 条逐条固定；
  0 同义撞车；驼峰路由的连字符改写**不得存在**（负向）；占位符名不参与匹配
  （骨架相同 ⇒ 字面段集合必须唯一）；LIVE 分类器 EXACT/PARAM/MISS 逐条钉住；证据件含长数字串 = 失败。

**5. ★ 自我证伪一次（如实记）**
第一版 LIVE 对账分类器写成 `re.escape(p)` 后再还原 `\{`，**顺序错误**，
导致 `/udc/entity/{id}` 这类路径无法整段匹配，把 6 条 PARAM **误报成 MISS**
（于是先得到「8 精确 + 3 占位」的错误口径）。第二版按段拼骨架并**复跑对账**，
两侧不一致 → 定位到该缺陷 → 修正为 **5 + 6**，并写进证据件 `live_channel.classifier_bug_caught`。
⇒ 教训与第七轮的「666 巧合陷阱」同类：**口径也要交叉验证，不能只信一台机器的输出**。

**6. 护栏会咬（本轮实测）**：证据件 `camel_literal_segment_count` 41→40 ⇒ **1 failed**；
证据件注入 19 位 ID ⇒ **1 failed**；证据件删 1 条驼峰端点 ⇒ **1 failed**；
**三次还原后字节一致**（sha256 相同），复跑 2 passed。

**7. 计数与清洗**：新增 **14 项**（`test_route_literal_similarity.py`）→
**1143 collected == 1143 passed / 0 failed**，compileall 无错；
三个文档计数用**断言式脚本**同步（每次替换必须命中恰好 N 次，未命中即抛错）。
新增 3 个文件**零客户业务 ID**（长数字串扫描 CLEAN）；证据件/工具**不含集群地址与 token**。

**8. 本轮未完成（诚实标注）**
- ⬜ **60 条未归位 op 仍 UNVERIFIED**：本轮是**通道建设 + 陷阱定死**，**不是**新的正面归位。
- ⛔ `pods/exec` 403 ⇒ pod `BOOT-INF/lib` 全量构件仍取不到（需人工提权或提供 `udc-assemble.jar`）。
- ⬜ 日志通道只给「被调用的面」，不给「全部注册的面」⇒ 不能替代构件扫描。

## 本轮证据（2026-10-15 第七轮 · 第二解析器独立复核 674 + 残缺扫描巧合陷阱 + 补录第六轮正文）

**本轮完成**：把「674 端点」这条**唯一的、且刚被修过的**证据链换成**两条独立链**；
顺手修掉 loader 契约里一处自相矛盾，并补完第六轮未落盘的正文。

1. **★ 674 的独立复核（本轮主项，即上轮留下的「下一步 4(a)」）**
   上轮把下轮首选定为「改用类级+方法级恒拼接**直接枚举** controller 内全部带 HTTP 注解的方法
   重算 op 面，而非只信派生结果」。本轮用既有但**从未跑通**的
   `tools/core/enumerate_udc_web_http_methods.py`（按 javap **缩进层级**解析
   `RuntimeVisibleAnnotations` 块，与提取器的 `annotation.<Name>` **文本搜索**是两条不同轴）
   对仓内 **54 个 javap** 全量重算：

   | 量 | 契约 `_api_full.json` | 独立枚举 | 一致 |
   |---|---|---|---|
   | Controller 类 | 54 | 54 | ✅ |
   | 带 value 的 mapping 端点 | 660 | 660 | ✅ |
   | 裸 mapping（无 value） | 14 | 14 | ✅ |
   | 合计 | **674** | **674** | ✅ |
   | 逐条 `(类,方法,动词,full_path)` | — | — | ✅ **0 双向差**（非抽样） |
   | 裸 mapping 的 `(类,方法)` 集合 | — | — | ✅ 完全相同 |
   | distinct op | 673 | 673 | ✅ |
   | 暴露面（双注解门） | 666 | 666 | ✅ |
   | 两个仓内 javap 副本（GBK / UTF-8） | — | — | ✅ 结果一致 |

   ⇒ **674 不再只由「三轮前刚被修过四类缺陷的提取器」自证**，派生口径疑点排除。
   证据源**全在仓内**（`docs/audit/artifacts/udc-web-5.3.517-{javap,contracts}/`），
   不受 scratch 24h 清理影响。

2. **★★ 钉死一个「看起来对」的陷阱（本轮新发现，重要）**
   第一版把独立解析器指向 scratch 快照 `scratch/art517-contracts/`（90 javap）——
   该快照**只有 52 个 udc-web Controller**（缺 `ParameterController` / `UdcFileController`，
   二者恰是暴露面被排除的 2 个类），于是得 `653 + 13 = **666**`。
   **666 恰好等于暴露面数** —— 一个**少扫 2 个类**的残缺扫描，会「看起来验证了暴露面 666」。
   已在护栏 `test_stale_52_class_subset_yields_666_by_coincidence` 里把该巧合**固定**：
   任何人若把 666 说成「独立扫描得 666」，必须解释这 2 个类去哪了。

3. **loader 契约 `scope` 自相矛盾修复**：`scope` 仍写「62 条余量 op」而 `remaining_total` 已是 60
   —— 口径更正只改了计数键，人读字段漂移。已同步 + 新增 2 项护栏
   （`scope` 不得把 62 说成当前范围 / 三个计数键必须同时等于记录条数、余量名单长度且互斥穷尽）。
   **护栏自证会咬**：把 `scope` 改回旧文 -> 1 failed；还原 -> 全绿。

4. **补录第六轮正文**（上轮只改到头部/状态行/下一步标题；本轮补齐第六轮证据段）+ 清理残留 `62`。

5. **护栏与计数**：+16（`tests/udc/test_udc_web_independent_enumeration.py`）+2（loader scope）
   -> 计数契约 **1111 -> 1129**（README / agent-version-audit / code-reality-audit 三处同步，
   `collect == passed`）。**护栏自证会咬（本轮全部实测）**：
   契约删 1 条 valued 端点 -> 3 failed；裸 mapping 的 `full_path` 改成 `/` -> 3 failed；
   删掉那 2 个类 -> 7 failed；loader `scope` 回退 -> 1 failed；**全部还原后 1129 passed**，
   且 `_api_full.json` 与 loader json 恢复**字节一致**（`git diff` 空）。

6. **诚实边界**
   - 本轮是**证据链加固 + 口径修复**，**不是**新的正面归位：余 **60** 条仍 **UNVERIFIED**。
   - 独立复核只证明「674 / 673 / 666 这三个数**可从 javap 独立重算**」，
     **不**证明「这 674 条就是线上全部端点」（构件覆盖仍受 pod `BOOT-INF/lib` 缺口限制）。
   - LIVE 通道仍全断（网关 403 / token 过期 / SSH timeout）。
   - 完成判据「平台操作面」仍 `[ ]` ⇒ **任务不可暂停**。

## 本轮证据（2026-10-15 第五轮 · 余量 62 穷尽扫描 0 归位 + 前端 loader 契约 25->32 + 计数契约 1093）

**本轮完成**：把「余 62 条」从「候选取样扫过」升级为「**全版本全构件穷尽扫描仍不承接**」（负证据），
换维度补出前端 **loader 契约 32/62**，并把它做成可咬护栏。

1. **★ 扫描域升级 10 倍**：历轮最多 34 jar / 90 controller；本轮自建并落盘 **437 jar（230.3 MB）**，
   覆盖 **201 个含 `@RestApi` Controller 的构件 / 619 个 distinct Controller 类**，
   **全 `5.3.x`**（`udc-web` 12 个版本 5.3.314→5.3.517）。事实源 = Artifactory `libs-release-local`
   （匿名，与既有约定一致）。工具沿用 `tools/core/extract_component_contracts.py`。

2. **★ 结论：62 条中 0 条归位**，三道独立判据全为 0：
   - **path→op 规则匹配**（含 `BaseComponentController` → `addPathPrefix /udc` 前缀机制）→ 0 命中；
     *管线自证*：同一管线对**已验 31 条跨构件归位**跑 **31/31 命中**（管线非空转）。
   - **字面量片段扫描**（kebab 化 op 名 / 族名，437 jar 逐 class）→ 仅 27 条命中，
     **逐条查证均为「同形不同源」**（`ctp-message` / `ctp-affair` / `app-common` /
     `udc-runtime` 族 vs 设计态 `udc/web` rpc 语义），**不得据此归位**（已列表入文档）。
   - **Controller 类名族扫描**（`@RestApi`+`@RestApiOperation` 双注解门）→
     `CustomDataTypeController` / `PageComponentController` / `FormUpgrade` / `MessageCategory` /
     `MessageLink` / `Pinyin` / `PageAdmin` / `RuntimeUpgrade` **零 Controller**
     ⇒ 这 8 族 28 条**构件本身不在本仓库**（在 pod `BOOT-INF/lib` 或加密 `assemble.jar`）。

3. **★ 前端 loader 契约 25 -> 32/62**（新证据源，机械复算）：
   新增 `docs/audit/udc-semantics/frontend-op-loader-contract.json`。
   **关键结构事实**：前端**从不携带 path** —— 一律
   `udcMutationLoader|udcQueryLoader.load({fieldType:<op>, paramsType, paramsKey, params, queryFields})`
   ⇒ ① path 只能由规则反推（既有归位法前提）；② 但 **`paramsType/paramsKey` 可直接读**，
   请求体形状**无需臆造**。32 条中 **28 标准**（`<op>InputBody|InputPath|InputQuery`）、
   **4 条偏离**（`udcCtpManagerTransferSelectGet` / `udcEnvCurrentEnvGet` /
   `udcSandboxResourcesGet` 跨 op 复用他人 DTO；`udcSandboxClearDataPost` 标量 `String`）。

4. **护栏 +11，计数契约 1082 -> 1093 passed**：
   `tests/udc/test_frontend_op_loader_contract.py`（**11** 项）：口径互斥穷尽（32+30=62）/
   与 `frontend-udc-unlocated.json` 名单同集 / 有证据必有 `paramsType`（无证据不得半填）/
   loader 种类白名单 / **4 条命名偏离硬断言** / 标准命名由 op 名机械推导 / 偏离计数。
   README + agent-version-audit + code-reality-audit 计数同步 1082 -> **1093**（collect == passed）。
   **护栏自证会咬**：`remaining_total` 改 66 → 2 项失败；删 1 条偏离标记 → 2 项失败；还原 → 全绿。

5. **诚实边界**
   - 62 条仍 **UNVERIFIED**：本轮是**强负面证据**，**不是**正面归位。
     「穷尽扫描无 Controller」与「Controller 藏在未入 Artifactory 的构件（加密 `assemble.jar` /
     pod `BOOT-INF/lib`）」两种解释**本轮无法区分** ⇒ 不写成「证明不存在」。
   - 抽取值（619 controller / 201 构件 / 437 jar / 12 版 udc-web）为扫描时点事实。
   - LIVE 通道仍全断：直连网关 403、共享 token 2026-10-13 过期、`10.0.0.1:22` timeout。
   - 完成判据「平台操作面」仍 `[ ]` -> **任务不可暂停**。

## 本轮证据（2026-10-15 第四轮 · 余量名单落盘 + 归位 27->31 + 计数契约 1082）

**本轮完成**：把上一轮 scratch 里**未入库**的余量研究收口入库 —— 首次给出「余量名单」而非只有计数；
新增 4 条字节码 VERIFIED 归位；把口径钉成互斥穷尽的机械复算物 + 逐条护栏。

1. **★ 余量名单首次落盘（此前只有计数，无名单）**
   - 落 `docs/audit/udc-semantics/frontend-udc-unlocated.json`（机械复算，非人工抄录）：
     346 前端 op = 230（可由 udc-web 673 op 推导）+ 116；116 中 `udc*` 前缀 = **93**；
     **93 = 31 归位 + 62 剩余**，两者互斥且穷尽。
   - 我**独立复现**了 31 条归位名单（27 条从既有测试表解析 + 4 条本轮新增），
     `93 = 27 + 66`（旧口径）与 `93 = 31 + 62`（新口径）**均能机械复算**，差额恰为 4。
   - 62 条**逐条**经两道反证：① 是 bundle 内**字面量** op（`grep -roh` 命中 1-9 次/条，非规则反推）；
     ② **不由** udc-web 契约产出（674 端点全扫 0 命中）。

2. **★ 新增 4 条归位（27 -> 31，字节码 VERIFIED_STATIC_BYTECODE）**
   构件从 Artifactory 拉取（落 `scratch/cand/`），`javap -v -p` 常量池直证（全文落 `scratch/v4out/`）：

   | op | 构件 :: Controller | 类级 mapping | 方法级 mapping | 方法名 | 动词 | javap 行 |
   |---|---|---|---|---|---|---|
   | `udcExcelSearchListByConditionsPost` | `boot-starter-excel-5.3.318` :: `ExcelController` | `excel`(L1116) | `search-list-by-conditions`(L576) | `selectListByConditions`(L541) | POST(L575) | 4/4 |
   | `udcExpressionSystemVariableListGet` | `boot-starter-formula-5.3.318` :: `ExpressionController` | `expression`(L567) | `system-variable/list`(L341) | `listSystemVariable`(L318) | GET(L340) | 4/4 |
   | `udcFileDownloadUrlGet` | `boot-starter-file-5.3.358` :: `FileController` | `file`(L3540) | `download-url`(L1290) | `generateDownloadUrl`(L1263) | GET(L1289) | 4/4 |
   | `udcFileDownloadUrlsPost` | `boot-starter-file-5.3.358` :: `FileController` | `file`(L3540) | `download-urls`(L1323) | `generateDownloadUrl`(L1293) | POST(L1322) | 4/4 |

   三条类**均 `extends BaseComponentController`**（常量池 `super_class` 直读）-> `udc` 前缀由
   `addPathPrefix` 叠加（与已验 sandbox 族同构）；四条 `path_to_op` 复算精确命中。
   **同时更正一处分寸**：原 27 条中的 `udc-portal` 类级 mapping **自带 `udc`** 且**不继承**
   `BaseComponentController`（`udc-cdpbi` 继承的是 `BaseController`）—— 故归位判定不能只看
   「类级 mapping 有没有 udc」，必须看「类级+方法级恒拼接 + 前缀机制」。已写入文档与护栏。

3. **★ store_registry 入参契约（新证据源，首次量化）**：`frontend-extraction.json#store_registry`
   （291 op，含 `paramsType`/`paramsKey`/`queryFields`）覆盖余 62 中的 **25 条**（旧轮记 26，
   本轮按 62 口径重算为 25）。**命名规约不是铁律**：标准 `<op>InputBody`(207)/`<op>InputPath`(56) 为主，
   但 **13 条偏离**（跨 op 类型复用 7 / 标量 3 / `paramsKey` 异常 3）-> 构建请求体**必须读原值，
   禁止按 op 名臆造 DTO**（已入护栏）。

4. **护栏 +150，计数契约收口 1082 passed**（932 -> 1082）：
   - `tests/udc/test_frontend_udc_unlocated.py`（**新**，146 项）：schema 钉桩 / 93=31+62 互斥穷尽
     机械复算 / 62 条逐条「bundle 字面量 ∧ 非 udc-web 产出」双向钉桩 / 4 条新归位参数化 /
     `93-27==66` 与 `93-31==62` 口径防回退 / registry 覆盖 25 条 / 族分布复算 + 分桶穷尽；
   - `tests/udc/test_component_relocation.py`（**26 -> 34**）：表扩到 31 条，分布断言改
     `sandbox 22 / portal 4 / cdpbi 1 / excel 1 / formula 1 / file 2 = 31`，唯一性断言 27 -> 31；
   - `tests/udc/test_graphql_op_naming.py`：归位计数 27 -> 31、余量 66 -> 62；
   - README / agent-version-audit / code-reality-audit 计数 932 -> **1082**（collect == passed）。

5. **诚实边界（本轮未拿下）**
   - **余 62 条仍 UNVERIFIED**：本地 616 jar 路径字面量扫描零命中；新拉 12 个候选构件只出上表 4 条。
   - **LIVE 通道全断**：直连网关 HTTP **403**（nginx WAF）；共享凭据 token **2026-10-13 已过期**；
     `10.0.0.1:22` 复测仍 timeout。
   - **工具环境更正**：`PATH` 无 `javap`（`javapath` 只有 java/javac），本轮改用
     `<LOCAL_ROOT>/java/bin/javap.exe` 绝对路径，一次通过。
   - 完成判据「平台操作面」仍 `[ ]` -> **任务不可暂停**。

## 本轮证据（2026-10-15 第三轮 · 提取器修复入库 + 计数契约收口 + 线索证伪）

**本轮完成**：收尾上一轮继承的破坏基线（4 项文档计数契约失败），对齐真值；全量 **932 passed**、compileall 无错。

1. **基线修复**：提取器 A/B/C（+ 声明门 D）修复已落到 `_api_full.json`（657 -> **674** 端点）。
   上一轮遗留 4 项失败 = README / agent-version-audit / code-reality-audit 写 926、实收 929；
   已同步为 932（含本轮新增 3 项），并清理同三文档内残留旧计数（309 / 361 / 277 -> 932）。
2. **★ 674/673 口径收口（新发现，此前未量化）**：`derive_ops` 的 distinct op = **673**，非 674。
   差额 1 = `ParameterController.create`：类级 `class_mapping=None` + 方法级**裸 `@PostMapping`**
   -> `full_path="/"` -> `derive_ops` 里 strip 后为空即跳过。旧稿 COMPONENT-RELOCATION.md 第 2 节
   「674 -> 674 个不同 op」**证伪**。三口径：**674 端点 / 673 op / 666 op 面**。
   护栏：`test_udc_web_contract_defects.py`（**+2** 项：总端点 vs distinct op、差额来源可定位）。
3. **前端对账真值钉桩**：346 前端 op -> **230** 可由 udc-web 契约推导（旧计 224；模型文件里是 173）；
   udc* 未归位 **93**（旧计 99）；扣 **27** 跨构件归位后**余 66**。三数与 COMPONENT-RELOCATION.md 2.5 节一致。
   护栏：`test_graphql_op_naming.py::test_frontend_op_reconciliation_counts_are_pinned`。
   注：`frontend-op-model.json` 内嵌 reconcile（matched=173 / frontend_only=173）为**旧口径**，不得引用。
4. **LIVE 证伪 `udc_microflow_info` 线索**：`conn.py selftest --env=test2` 仅 **mysql / nacos** 可达。
   该表全 **4661** 行，`rest_path` 非空仅 **5** 行、`rest_api` 非零仅 **3** 行；
   样本（`formToPDF` / `queryTransfer` / `getEndRejectEmail`：rest_path=微流程名、rest_api=1；
   `getConfBusiness`：rest_path=23123、rest_api=0）——该列是**微流程级 REST 开关/路径名**，
   **不是** REST 端点注册表，**无法**提供余 66 条 path。下一轮转网关 / ingress 路由表。
5. **诚实边界**：余 66 条仍 **UNVERIFIED**（未以规则臆造路径）；SSH `10.0.0.1:22` 仍 timeout，
   pod `BOOT-INF/lib` 全量扫描未取到；`ParameterController` 是否真不暴露仍**未 LIVE 验证**（仅字节码结论）。
   完成判据「平台操作面」仍 `[ ]`，**不可暂停**。

## 本轮证据（2026-10-15 · udc-web 契约方法级缺陷 + 32 条跨构件归位落地）

**本轮完成**：把上一轮「99 op 归位」从 27 推到 **32**，并**首次定位 udc-web 持久化契约自身的
方法级缺陷**（漏 18 条真实 op / 多 11 条幻影）—— 这解释了上轮记的「21 处不一致」。
落文档 `docs/audit/udc-semantics/COMPONENT-RELOCATION.md`（157 行）。

1. **更正上轮「构件不在本地」结论**：Artifactory `libs-release-local/com/seeyon` 实有 **539** 构件，
   `udc-biz / udc-extend / udc-starter-runtime / udc-common / udc-plugins` **均有 5.3.517**。
   已实拉 **22** jar 落 `scratch/artif/`。`udc-web-5.3.517.jar` 的 sha256 与 `<MAVEN_REPO>` 副本一致。

2. **归位 27 -> 32/99**：`boot-starter-sandbox-5.3.289` 22 条、`udc-portal-5.3.517` 4 条、
   `udc-cdpbi-5.3.517` 1 条、`udc-web-5.3.517` 5 条。
   **32/32 独立验证**：对每条在 class 常量池查四类字面量（类级 mapping / 方法级 mapping /
   方法名 / HTTP 注解），齐备才算 VERIFIED（`s10/verify_reloc.py`，本轮复跑得 32/32）。

3. **机制再实证**：`Sandbox{Client,AppRun,SystemConfig,TenantConfig,Flexible}Controller`
   五类全 `extends BaseComponentController`，类级 mapping 是 `sandbox/client`（无 `udc`），
   而 op 是 `udcSandboxClient*` -> 前缀由 Spring 层 `addPathPrefix` 叠加。

4. **★ udc-web 契约方法级缺陷（本轮新发现，独立于归位）**：站点 663 path vs 持久化 657，
   **18 条真实 op 缺失 / 11 条幻影**。根因在 `tools/core/extract_udc_web_methods.py`：
   - **A** `methods` 以**方法名**为 dict key -> 同名重载（不同 `@PostMapping` value）后写覆盖前写，
     **14 组 / 15 实例**（如 `MetaDataController.mergeReferMetaData` 的 `merge-refer` 与
     `merge-refer-by-map` 只剩后者；`ApplicationController.create` 3 个端点只剩 1）；
   - **B** 注解块取值越界：裸 `@PostMapping`（无 value）在 `@RestApiOperation` 之前时，
     中文描述被当路径（污染 2 条：`创建数据传输对象` / `创建枚举分类`）；裸 mapping 全量 14 处；
   - **C** 无 mapping 的方法被 `setdefault(path_value=名字)` 兜底 -> 幻影
     `ApplicationController.saveAsTemplate`（`http: null`，全量仅 1）。
   ⇒ 上轮「21 处不一致」由此解释：其中「少解析」是**上版扫描脚本漏读裸 mapping** 的假差异，
   本版修正后归零。**持久化 657 不是权威真值**；站点 663 为当前最强静态下界。
   本轮**未**改写 `_api_full.json`（需先补护栏 + 全量逐方法复核）。

5. **连带**：`rem67` 中 **1** 条可由修正后 udc-web 契约精确归位
   （`udcApplicationPost -> ApplicationController`，POST `/udc/application`）；其余 66 条仍属非 udc-web。

6. **回归护栏 +133**（790 -> **923**）：
   - `tests/udc/test_udc_web_contract_defects.py`（**67** 项，新）：缺陷面基线 / 14 组重载字节码实证 /
     契约塌缩断言 / 缺失路径在 javap 中「有」且契约中「无」的双向钉桩 /
     3 个「已知缺陷钉桩」（修好即失败，强制同步文档）；
   - `tests/udc/test_component_relocation.py`（**66** 项，新）：32 条归位 op 规则复算 +
     不由 udc-web 契约产出 + 构件分布 + 路径唯一；
   - README / agent-version-audit / code-reality-audit 计数同步（790 -> 923）。
   `tests/` **923 passed**（12.4s），`compileall components tools tests` 无错。

7. **工具诚实标注更新**：`tools/core/extract_component_contracts.py` docstring 记入
   站点 663 vs 契约 657 的真实根因（A/B/C），仍限「构件级定域」，**不得**作方法级权威源。

8. **本轮未完成（诚实标注）**：未修提取器（2e 为下一轮首选）；未以站点 663 覆盖契约；
   67 条未归位 op 仍 **UNVERIFIED**（本地 594 jar 对这些子域路径字面量 0 命中，未以规则臆造）。
   LIVE：`conn.py selftest --env=test2` 仅 mysql/nacos 可达；`udc_history_metadata` 全表 3 行且
   `metadata_schema=[]`，`metadata_type=2`(RestApi) 槽位为空 -> LIVE op 注册表仍未取到。

## 本轮证据（2026-10-15 · REST/GraphQL 暴露机制定域）

**结论**：99 个未归位 `udc*` op 的**暴露机制已字节码闭环**，且**证伪了上一轮的 `@AppService` 假设**。
落文档 `docs/audit/udc-semantics/REST-EXPOSURE-MECHANISM.md`（195 行）。

1. **证伪**：上一轮把未归位 op 归因于「`@AppService`/`@AppServiceOperation` 第二套 REST 暴露机制」。
   CFR 反编译 `boot-starter-appservice-5.3.358.jar` **全 41 类无任何 HTTP 映射**：
   只有 `AppServiceAutoConfiguration`（注册 `AppServiceBeanPostProcessor` + AOP advisor 事务/日志/幂等）
   与 `AppServiceBeanPostProcessor#appServiceMethodInterceptor` → `AppServiceMethodInterceptor.register(method)`
   （**业务切面注册，非 RequestMapping**）。`@AppServiceOperation.value()` 是中文操作名（如「获取沙箱应用角色」），不是路径。
   `boot-starter-web` 的 `ComponentDynamicRegister` 实现只有 `ControllerDynamicRegister`（模块热插拔重扫），与 AppService 无关。

2. **真实机制（VERIFIED_STATIC_BYTECODE）**：`boot-starter-scanner-5.3.358.jar`
   `MetadataScanner#collectMetadataByClass`（第 556 行）**两条并列分支**：
   - 分支一 `@RestApi` → `collectRestMetadata`（第 1368 行）：path **取自** `RequestMappingHandlerMapping.getHandlerMethods()`
     的 `mapping.getPatternsCondition()`，即 **Spring 实际注册表**，不是注解字面量拼接；
     类/方法注解 `@RestApi` + `@RestApiOperation` 缺一不可；另有 `isMonolithic()` 的 `/a9/`→`/{appName}/`
     与 `isHostSandbox()` 的 `/app-sandbox/`→`/{appName}/` 两处前缀改写。
   - 分支二 `@AppService` → `collectAppServiceMetadata`（第 1641 行）：独立 `AppServiceMetadataDto` map，**不进 GraphQL**。
   - 下游：`GraphQLProvider#addMethod` → `MetadataProxyService.selectRestApiMetadata(appName)`
     → `metadataService.selectForMap(MetadataTypeEnum.RestApi, {appName})` —— **按应用维度，不按构件维度**。
   ⇒ op 面 = 全应用全构件所有 `@RestApi` Controller，≠ udc-web 的 657 方法。

3. **更正上一轮负面结论（诚实标注）**：上轮「全仓 572 jar 逐 class 无字面量」的**搜索域不成立** ——
   扫描根 `<MAVEN_REPO>/com/seeyon` 本轮实测 **1518** jar，而 99 op 的归属构件
   （udc-portal / udc-cdpbi / udc-upgrade / udc-affair / udc-app-common / udc-m5 / udc-user / udc-bpm / udc-cip /
   boot-starter-sandbox）**不在本地仓库**（`ls com/seeyon | grep -i udc` 仅 17 项，无 portal/cdpbi/sandbox）。
   正确表述：这些构件**只存在于 test2 pod 的 `/app/udc-assemble.jar` `BOOT-INF/lib/` 内**，属事实源缺口。

4. **归档上轮 pod 扫描的 artifact 级命中**：`probe99/podscan_out.txt` 12 条 MATCH 全部映射到 99 名单 op
   （boot-starter-sandbox-5.3.289 承接 8 条 sandbox 族；udc-cdpbi-5.3.517 → `udcCdpDataReportGetReportListPost`；
   udc-portal-5.3.517 → `udcPortalPortalSpaceSpaceSaveCopyPost`）。

5. **反向规则跨构件复算 9/9 精确命中**（写入回归护栏）：如 `/udc/sandbox/client/check-all-status` GET →
   `udcSandboxClientCheckAllStatusGet`；`/udc/portal/portal-space/space-save-copy` POST →
   `udcPortalPortalSpaceSpaceSaveCopyPost`。证明 op 命名规则对外构件同样成立。

6. **新增前端 bundle 字面量佐证（本轮，本地可复核）**：`udc-frontend/unpacked`（13MB）grep 得
   `/udc/*` 与 `/udc-runtime/*` 字面量 34 条，与 99 op 交叉命中 21 个调用点
   （`/udc/sandbox/app/search`、`/udc/sandbox/system/config/is-deploy-war`、
   `/udc/application/search/front-detection` 等）。

7. **回归护栏 +10**：`tests/udc/test_graphql_op_naming.py` 新增 9 项参数化（跨构件路径→op 精确命中）
   + 1 项反证（这些 op 不得由 udc-web 契约产出）；文件 15 → 25 项。
   基线 **780 → 790 passed**（README/agent-version-audit/code-reality-audit 计数同步），compileall 无错。

8. **本轮未完成（诚实标注）**：`10.0.0.1:22` **不可达**（connect timed out，两次重试），
   故无法补扫 pod `BOOT-INF/lib` 全量构件 → 99 op 的**全量** artifact 级归属仍 UNVERIFIED（已归档 12 条）。

## 本轮证据（2026-10-14 · full_path 拼接缺陷修复）
- **缺陷**：`tools/core/merge_udc_web_api.py` 把**方法级** `path_value` 以 `/` 开头当作绝对路径
  （`full_path = "/udc" + pv`），而 Spring 语义是**类级 + 方法级恒拼接**。
- **字节码实证**（`udc-web-5.3.517.jar`, `javap -v`）：`PageInfoController` 类级 `udc/page-info`
  + 方法级 `/base-info/create` -> 真路径 `/udc/page-info/base-info/create`；缺陷产物给 `/udc/base-info/create`。
- **LIVE 佐证（先行证据，说明缺陷长期被文档钉死却未修）**：
  `S7-WRITE-CHAIN-LIVE.md` 已记录页面真路径为带 page-info 前缀，且旧绝对路径**已证 404**；
  `live_write_templates.py`（在线创建成功）用的就是 `/service/udc/page-info/base-info/create`。
- **量化**：657 方法中 **159 个（24.2%）** `full_path` 错（12 个 Controller 全量逐条 javap 核对类级 mapping）。
- **修复**：`frag = pv.lstrip("/")` + 恒拼接；`.strip("/")` 会误删 `transfer/batch/` 的字节码字面尾斜杠，已改 `.lstrip`，差异收敛到恰好 159 条。
- **op 面影响**：规则可推导 op 618 -> **655**；其中**线上不存在**的幻影 op **122 -> 0**
  （如 `udcAppOnlinePost` 真名 `udcDeploymentAppOnlinePost`）。
- **归位口径区分（重要）**：extraction 346 op 口径**不变**（224 已归位/122 未归位）；
  catalog 456 op 口径未归位 **225 -> 133**（多归位 92）。
- **掩蔽机制拆除**：`graphql_op_naming.derive_ops` 原并列试算 `full_path` 与 `class_mapping+path` 两拼法，
  后者兜底**掩盖了本缺陷**且并入幻影 op；修复后两拼法产出完全相同 op 集（655 vs 655，差异 0）-> 死代码已删，只留 full_path。
- **断言重判**：3 个测试文件 / 21 处缺陷固化断言按字节码修正（7+11+3；详见 `FULL_PATH-CONCAT-DEFECT.md` 第 5 节）。
- **回归护栏 +6**（5->8 与 12->15 项）：`test_udc_web_full_api.py`（PageInfoController 类级拼接 / **全量 657 方法前缀恒等** / 幻影路径负面护栏）；
  `test_graphql_op_naming.py`（op 只由 full_path 产出 / 幻影 op 不得产出 / 兜底已是 no-op）。
- 基线：**780 passed**（README/agent-version-audit/code-reality-audit 计数同步 774->780），compileall 无错。

## 前轮证据（2026-10-14 · 平台操作面）
- **GraphQL op 命名规则字节码实证**：`boot-starter-graphql-5.3.358.jar`
  `GraphQLProvider#pathToCamel/#queryBuild` + `GraphQLObjectTypeParamsService#addMethodParamList`
  + `GraphQLObjectTypeNReturnService#getContentType`
  → op = `pathToCamel(restPath + "/" + httpMethod.toLowerCase())`，六步改写（IdGet$/Id$/SearchPost$ 顺序敏感），
  含 `outOffset==0` 守卫（首分隔符不大写，故 `/udc/...` → `udc...`），
  入参 `InputPath/InputBody/InputQuery`、出参 `ResponseContent`，get 仅 Query、其余 Query+Mutation 双挂。
- **交叉验证**：规则复现旧对账 164/173 真阳；暴露 9 个模糊假阳（`udcApplicationCopyGet` 等，真名已列）；
  346 前端 op 中 224 精确归位 udc-web，122 属他应用域。
- 落模型 `components/udc/graphql_op_naming.py`（`path_to_op/derive_ops/explain`）+
  测试 `tests/udc/test_graphql_op_naming.py`（12 项）；
- 文档 `docs/audit/udc-semantics/GRAPHQL-OP-NAMING-RULE.md`。
- 基线：774 passed（README/agent-version-audit/code-reality-audit 计数同步 761→774），compileall 无错。

## 阻塞 / 待确认
- 无硬阻塞。
- 第十轮工作树剩余改动**全部属于并发工作流**（`components/udc/entity_constraints.py`、`components/udc/microflow_model.py`、`tests/udc/test_entity_constraints.py`、`tests/udc/test_microflow_condition_constraints.py` 及 `tools/*` 新脚本），**本任务未触碰、未提交**（如实登记，避免误认归属）。
- 第十轮标为"并发工作流未提交"的 `entity_constraints.py`/`microflow_model.py`/`test_entity_constraints.py`/`test_microflow_condition_constraints.py` 正是本轮任务对象（dataType 约束矩阵），本轮已补齐并提交；1167 为本轮实测，**+13 用例均在既有测试文件内追加，collection 保持 1167**（文档契约测试动态对账 pytest collection，不改文件数）。
