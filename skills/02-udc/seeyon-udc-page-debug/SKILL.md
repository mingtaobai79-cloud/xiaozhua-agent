---
name: seeyon-udc-page-debug
description: Use when a UDC detail page loads or submits the wrong data.
---

# Seeyon UDC 详情页装载/提交调试

调试「详情页有数据但提交走 create」「提交撞子表主键」以及「前端弹窗关闭后仍产生页面数据」时的硬规则。平台机制细节与取证配方在 `references/detail-page-load-submit.md`；弹窗关闭/选择结果与前端副作用的定位配方在 `references/frontend-modal-side-effects.md`；Excel 导入/导出模板类问题（模板列不对、按模板填完导不进、导入入口的参照列不显示）在 `references/excel-import-template.md`；不打开设计器、用 udc_* 元数据库直查页面/微流程定义与相互引用（页面↔微流程按数字 id 反查、page_schema 节点树解树与分组字段清单、data_schema 解剖、模板文件与枚举存储机制、实体↔物理表映射与子表外键取证、按钮显隐与「提交后不能再操作」锁定排查、**校验类 bug 从报错文案反查微流程（判定在微流程里、页面规则只是入口；文案相近≠同一校验；判定里「缺的条件」就是根因）**、低代码 bug 先定位后动手工作流）在 `references/udc-designer-metadata-db.md`；整块/字段「打开无值」的定性（存量查询 vs 实时取数、谁负责落库、外源双环境对照核验）见 `references/section-empty-value-triage.md`。

## Procedure: 页面动作（生成/预览/导出）的落库与转换链定性

用户报「生成/预览后没内容」「要再点一次才更新」「左右两边显示不一致」「管理页无内容」时，先定位这条动作链，再谈修：

1. **从页面 schema 反查动作绑的微流程**，不要在 Java/前端源码里搜按钮名（这类链全在设计器/微流程里）。①从页面 `page_schema` 的工具栏节点（`type:UdcToolBar`，`settings.addOperates`）找按钮，它带 `events` 且 `eventType` = 按钮 id（如 `0tDvdwYxlQ`）；②该事件体里的 `microFlow` 就是按钮执行的微流程 id。**库位别搞混**：`udc_page_schema`/`udc_page_info`/`udc_microflow_info`/`ctp_enum*` 在**元数据库**（`udc_test2`/`udc_uat`），业务实体表（`htmbzxsc_*`、`kuozhanxi_*` 等）在**应用库**（`<appId>_test2`/`_uat`）——两者常是同一实例的不同 schema，在应用库连接上查元数据表会直接 `1146 Table ... doesn't exist`。
2. **把微流程节点按执行顺序列出**（`data_schema` 的 `nodes`，含嵌套 `conditions`）。重点看四个动作节点的先后：`ENTITY_SAVE`（保存记录）→ `FORM_CONVERT`（单据转文档，`config.convertType` = `content` 写正文字段 / `attachment` 写附件字段 / `pdf`，`converOperation` = `preview` 只渲染不落库）。
3. **数据实证：先按状态分组，再看趋势，最后双环境对照**——顺序错了整份结论作废。①查该单实体「正文/附件/转换后 pdf」列的取值分布时**必须先按单据状态分组**：草稿/未生成状态的行正文为空是**正常的**，把它们混进空值率会把结论彻底带偏（就此误报过「最近记录全部无内容」）。②只取「已生成/非草稿」状态的行，按 `DATE_FORMAT(create_time,'%Y-%m')` 分组看 空/有 的**按月趋势**，区分「近期退化」与「历史存量」。③**收尾做双环境对照**（同应用 `<appId>_test2` vs `<appId>_uat`）：另一环境若大量「已生成」记录都有值，则这不是产品缺陷，而是本环境的数据/历史缺口——**单环境 `ORDER BY create_time DESC LIMIT N` 的列表不能当判据**，它既会混入草稿行、也会漏掉真正的分组形态。设计态定义 ≠ 运行时落库：列存在且被引用，不代表有值。
4. **差额归因**：正文列多为空 + PDF 列全空 = 转换/落库链实际未写成功。再看弹框读哪一路：弹框/详情绑的是**落库字段**，左侧即时预览走的是 `converOperation=preview` 的**当期渲染**——一个读存量、一个读即时，所以会出现「左边有内容、右边弹框为空」。
5. **「点一次不更新、二次才更新」**：保存与转换在同一前端微流程里**顺序且异步**执行，首次点取不到刚保存的值（未落稳/未同步），第二次才生效——是时序竞争，不是缓存 bug。报告里标为强推断，附带「用日志坐实首次为何取空」的下一步，不要写成已实测结论。
6. **别指望应用日志能坐实这条链（先别去翻）**：前端微流程的 `ENTITY_SAVE`/`FORM_CONVERT` 节点**不写应用日志**——在 `{app}-info.log`/`{app}-error.log` 里 grep `单据转文档`/`FORM_CONVERT`/`转文档` 都搜不到，本应用日志并不能证实或证伪这条链。要定到最后一层，走「同实体里对照有值/无值记录的差异」（按模板名/操作路径/时间分组）或复现时抓结果服务（内容/文档转换服务）自己的日志，而不是反复 grep 本应用日志。另外本应用的 `error.log` 常被**别的功能**刷满（见 `seeyon-low-code-environment` 的日志节：按 logger 类名归类，不按时间窗口）。

报告先给「链是什么（按钮→微流程→保存→转文档）」，再给「库里到底有没有值」，最后给「无法佐证的环节（无日志时）单列」，不要拿静态配置直接下修复结论。

## Procedure: 详情页区块「无值」（先定数据来源，再谈 bug）

用户报「XX区块/字段无值，期望有展示」时，不要先怀疑前端。先定性数据来源，再决定查哪一段链路：

1. **读组件 dataSource 定性**：`type=ENTITY`+`subType=RELATION`（key 形如 `<容器formKey>.<实体>DtoList`）是**读子表存量**——页面打开不回源第三方，库里无行必然空，与前端无关；`type=MICROFLOW`/绑接口才是实时取数。容器/分组节点只存 `childById` 子 id，必须解引用才能看到目标网格。
2. **定「谁写这张表」**：按实体全名扫微流程 `data_schema`，看命中流程的节点 actionType；全是 RETRIEVE/CREATE_LIST、没有任何 SAVE/CREATE/CREATE_ENTITY ⇒ **没有流程负责落库**，数据只可能来自导入/扩展代码/外部推送/手工新增，缺口在下游，不在页面。
3. **外源双环境对照实测**：从扩展实现类的 `@Value`/配置类取第三方 URL（测试与生产是两套），同一业务键各打一次，**并另选一个测试侧确实有数据的键做对照组**；生产有 N 条、测试 0 条而对照组测试有数据 ⇒ 断言「源头测试环境数据缺口」，不得报成应用缺陷。
4. **两侧库对齐**：主档在目标环境是否存在（按业务键）、子表命中几行、子表全表行按业务键 group by（确认是否只是别人测试期造的样例数据）。
5. **旧系统口径 = 设计语义证据**：旧系统同区块若实时调中台，新系统改读存量，则「谁在何时落库」必须有人接——写成给开发的缺口问题，不要自己猜或直接补数。

报告先给「源头有没有数据」，再给「页面是存量还是实时」，最后给可执行修复路径（补数据 / 加同步落库 / 换环境验证），test2 与 uat/生产分开写。

## Procedure: 区块/字段「比预期少」（设计态有、运行时不渲染）

「少字段/展示不对」是**相对判定**，先建基准再谈差异——顺序错了整份结论作废：

1. **先要对照基准。** 有老系统/期望清单就拿它当验收标准。手上只有新系统时，**只能说「本系统设计态定义 >> 运行时渲染」这一件事，不能替用户断言「比老系统少哪几个」**——去要老系统同模板的界面截图或字段清单，别拿新系统的设计态冒充老系统基准。
2. **设计态字段清单**：按分组容器（`type:"Collapse"`/`UdcContainer`，组名在 `settings.content.simple`）收其后代 `type:"Label"` 节点的 `settings.content.simple`（是字段名；`uiModelSchema` 里的「标题/状态/正常/禁用/隐藏」是属性面板元数据，不是字段名）。解树配方见 `references/udc-designer-metadata-db.md` 的「页面 page_schema 解剖」——**`children` 是 id 字符串列表、节点体在 `childById`**，按对象列表递归会得到「节点数 1、Label 数 0」的假空页。
3. **运行时清单**：从用户截图逐条抄实际渲染的字段（vision_analyze）。两者相减 = 设计态有、运行时没渲染的集合。
4. **差额归因（动态显隐，不是漏配）**：控件 `settings.calculationValue.expression` 绑在某个驱动字段/枚举上，`uiModel.status` 可为 invisible；驱动字段在业务表里全 NULL/空 ⇒ 表达式判不出分支 ⇒ 整组字段不渲染。**先查驱动字段的实际取值分布**（列名常带「模板特殊信息」这类词），再判是「少配字段」还是「开关没值」；定义表（如「合同特殊字段」）全 0 行是另一条独立线索，一并列。
5. 报告分三层：设计态定义（有证据的清单）/ 运行时实际（截图）/ 差额与候选根因（未验证）。缺老系统基准时把「无法判定是否比老系统少」单列出来，不要含糊过去。

## Procedure: 定位页面规则的弹窗副作用

1. 先读调用方生成源码 `pc/src/microflows/<ruleId>.ts`，从 `OPEN_PAGE` 往后按执行顺序列出所有 `CALL_MICRO_FLOW`、`CREATE_VARIABLE_FRONT`、`VALUE_HANDLE/DATA_INSERT`、`ENTITY_*` 节点；不要只看设计器上的弹窗名称。
2. 检查 `OPEN_PAGE` 的 `openType`、版本和 `needStopMicroFlow` 语义，再读生成包的 `nodeActions/open_page.ts`，确认关闭后是否会写入页面输出；“弹窗已关闭”不等于“用户已确认选择”。
3. 追到被打开页面的 `component-events.ts`：确认按钮必须有明确的选中行/业务 ID 输出，取消按钮必须是空输出或明确的 cancel 状态；父规则必须用这个结果门控后续副作用。
4. 对每个副作用节点回答两个问题：它是否只在“确认且选中”分支执行？它读取的数据是否按本次交互/合同/请求关联，而不是只按当前用户查询共享中间表？任一答案为否，先判定存在串数据或关闭误插风险。
5. 先做“直接关闭”实验，再做“选中并确认”实验：前者必须没有 `CALL_MICRO_FLOW` 转换、`DATA_INSERT` 或持久化写入；后者才允许进入完整链路。`DATA_INSERT` 只能证明前端行被插入，是否落库要另查提交 payload/保存接口/数据库。

## Procedure: 只有前端编译包时，定位字段取值来源与显隐权限

客户前端包 `pc/src/pages/<页面>/profiles/*.ts` 是设计器配置的编译产物，不开设计器就能定性取值链与显隐：

1. **值从哪来**：先看 `component-view-state.ts`。绑定实体字段（`dataSourceField` 指向 `Xxx.<字段>`）＝读存量；空白/无绑定又在微流程里被 SET 的＝实时算出来的。两侧不等时，差异在「谁算、什么时点算」，不在前端。
2. **页内变量是不是死的**：读 `page-variable.ts` 拿默认值，再全应用 grep 该变量 code 是否出现在任何 `microflows/*.ts` 的赋值节点里。**默认 `true` + 零赋值点 = 显隐恒开**——这类页面的字段显隐看着像权限，实则形同虚设。`page-in-params.ts` 里同名字段是入参（且可能是 `DATA_SOURCE` 型），与页面变量同名会误导判读，先分清来源类型。
3. **容器/按钮的显隐条件**：`page-component-expressions.ts`（表达式）＋ `component-view-state.ts` 的 `status`/`viewState`。条件形如 `PAGE_IN_PARAM x == 'view'` ⇒ 何时可操作由调用方传参决定；条件形如 `currentUser == FORM.某扩展字段` ⇒ 判的是「合同上记的角色人是不是我」，不是「我的角色」，维度错误且方向常相反。硬编码人名/工号的显隐要单独列出来当缺陷。
4. **弹窗＝独立页面**：从 `page-datasource-metadata.ts` 列实体、`page-component-tree.ts` 列组件，`component-view-state.ts` 逐组件对字段；「不该看到成本/其他毛利」直接由弹窗里是否存在「实际毛利」类网格及成本列界定，而不是靠主页面。
5. **页面级微流程入口**：`page-events.ts` 的 `onLoad → microflow -<id>` ＋ `microflows/_<id>.ts` 就是打开页面时跑的那条链，顺它找到 `CALL_MICRO_FLOW` 的后端服务出参 DTO，就能说清「页面上这个值实际来自哪个接口」。
6. 结论里区分 STATIC（编译产物）与需环境复核项：口径差、调用方传参、微流程内过滤表达式，都要去环境实测，别用静态配置下最终结论。

## 硬规则

- create-bpm/update-bpm 只看表单 DTO 根 `id` 是否指向一条**已存在**的记录：先拿提交瞬间的 DTO 快照定案，再谈其它。`0` 和**负数临时 id**（页面新建行的本地 id，库里查不到）都算「未绑定」——别因为 id 非空就判成 update。业务字段差异、按钮配置正常都不能推翻这个判定。
- 装载器可能只把主键写进 `__key`（行标识）而不写 `id`（数据字段）；路由只读 id。判定法：解析 `app_data_draft.draft_data` 的 formData，对照 `id` 与 `__key`——`id:'0'` 或负数 + `__key:真实id` 即为此症。页面控件显示有值≠序列化值正确，两者取数位置不同。
- 主表单 `get-cascade-default-value` 返回全 0 默认值骨架，页面打开后**异步数秒**才调用，按「空字段才填」合并：业务字段、子行真实 id 幸存，唯独空着的根 id 被填成 0。①onLoad 规则里的 SET_VALUE 会被这次合并冲掉，要钉住 id 必须赋在**提交规则最前（第一个节点之前）**——提交规则常含多条提交路径（ENTITY_SAVE、多条 ENTITY_SUBMIT、FLOW_ACTION 分支），只插在某个保存节点前会漏掉其余分支；点击→赋值→序列化同步完成，无异步可覆盖；②「刚打开就提交成功、放一会儿再提交就炸」= 与合并的竞态，是时序信号不是玄学。
- 「同样操作时好时坏」先查 switch-view 的 localStorage 表单缓存（`formCacheData-*`）：SingleDatasource.query 里缓存优先于真实装载，旧失败现场的 id=0 快照会原样恢复（读到即删，但残留跨会话存活）。Console 清 `formCacheData*` 后新开页面重测；机制见 reference。
- 差分实验最锋利：同一 URL 逐个增删页面入参对比保存结果，一次锁定肇事参数。ENUM 型入参（如合同审批打开方式）有几十处消费（控件显隐/初始化分支/提交分支），是首要嫌疑；但删参数只是诊断手段，修复不能靠删——业务开关（变更/终止面板、审批类型赋值）全挂它上面。去掉参数后提交成功≠修好：成功可能只是绕开了肇事链路（变更重演分支没跑、业务校验缺失），且常落在刚打开页面的竞态窗口内；用提交包 `extraParamMap.openTime`（页面打开毫秒时间戳）到日志提交时刻的间隔量停留时长，几分钟后的稳定成功才算数。
- 分支配置自检：规则分支的 SET 值枚举必须与分支条件枚举一致（出现过条件==合同申请却 SET 合同变更的自相矛盾配置，导致变更场景审批类型永远赋不上）；还要查**分支整体缺失**——枚举有 N 个场景但分支只写了 N-1 个，缺失场景的赋值静默不执行，数据落库即缺赋值。从 `udc_microflow_info.data_schema` 解出各 conditions 对照 ctpEnum id/desc。
- 「首提必败(create)、重载后次提必成(update)」是 id 被异步初始化链洗掉的标志性节奏，不是偶发抖动：失败提交触发运行态 queryData 重装载把真实 id 带回来，所以第二次总是成功。用户报「第二次就好了」时既别当已修复也别当玄学——对齐 createWithResult/updateWithResult 与同 trace select-cascade 的时序即可定案；「刚打开就成功、放久了失败」是同一竞态的另一半，判读时先算提交包 `extraParamMap.openTime` 到提交时刻的间隔。
- 复制/变更链路的数据污染自检：同一业务键（合同号等）在主表堆多行、且新建行的枚举字段存了默认值/错误枚举 ⇒ 每轮变更都在留脏数据，且对应赋值分支从未执行（与上一条分支缺失互为表里）。修机制前先量化脏数据规模，清理脚本留回滚口、写后回读。
- `select-cascade-by-conditions` 不装载主档；只有 `select-cascade-by-id`（按 id 查主表）才算编辑装载。日志里无 by-id 只能当旁证：单 pod 日志只覆盖该实例（页面 http 请求可能落在别的 pod，提交走 dubbo 时痕迹只在提供者侧），别用它反证「页面从没请求过」。副本会滚动：同应用可能同时存在 Error 态旧副本（容器日志不可读，`kubectl logs` 报 unable to retrieve container logs）与 Running 新副本——先 `kubectl get pods` 看状态，用 `logs <pod> --since | wc -l` 验证副本真的吐得出行，再下「无日志」结论。
- 微流程 CREATE_ENTITY 裸 INSERT，主档停在 NONE 状态；页面正常保存的单据状态 ≥ 待提交。状态不同，同一页面的装载行为不同。
- 主键冲突先分主档/子表：报错 DAO 是子表 DAO（`...XxxDao.createBatchInternal-Inline`）时撞的一定是子表行。子表行 id 在库里已存在、提交却标 `actionType=INSERT` ⇒ **双写**：某条微流程（CREATE_ENTITY，独立事务）已把它落库，页面提交又插一次。此时删页面上的 ENTITY_SAVE/「保存记录」节点无用——真正写库的是提交本身（`createWithResult`），冲突发生在提交事务里。
- 复制/变更类微流程预建「主档+子表行」后，页面必须以真实 id 走 UPDATE 提交；否则同一批行必被插两次。修复只能二选一：页面绑真实 id，或微流程不预落子表行（同一行不能由两边各插一次）。
- 「控件有值 ≠ recordData.data.id 有值」：提交路由读的是 `datasource.getData()` = `recordData.data`（diff 后取 `finalData.id`），**不读画布控件显示值，也不读 `__key`**。默认值骨架 `setData(initialValue, true)` replace=true 重置 recordData 后，控件显示旧值但 data.id='0'，草稿快照呈 `id:'0'+__key:真实id` 的混合态。源码链（v5.3.149/dist）：use-handle-events.js ENTITY_*→handlers.js saveData→single.js save→diffSubmitData→dynamic-api.js getSaveApiField（只看 data.id）。现场验证：Console 读 `window.__UDC_DATASOURCE__[sig][formId].recordData.data`，看 id 与 __key 分离。SET_VALUE 赋值写的就是 recordData.data，放提交规则里能赶上序列化，故对症。**Console 直改 `recordData.data.id` 不是有效的修复/差分手段**：点提交会触发提交规则执行与组件树/datasource 重建（常伴「获取组件displayName超时」等报错），直改值随旧对象引用一起被丢，提交包里 id 仍是 '0'——用户报「控制台改了又被改回去」就是重建信号。判读这类实验只看提交 payload 的 formData.id 是否仍为 '0'，别把实验失败当成诊断被推翻。
- 元数据包 vs 生成包要对时间戳：页面 json 的 `updateTime`/`publishState`（UNPUBLISH=草稿态导出）与前端 profiles 的 mtime 差多少天。导出的元数据包可能是旧版本，生成代码才是运行真相；设计器里看容器条件时别拿旧元数据包当现状。反过来：生成代码里多出来的 `fixCondition`/`defaultPlan` 若在元数据包里不存在，说明那是导出之后新加的——时间点常与最近的功能改动重合，是定位「谁改坏的」的利器。
- 默认值优先级（源码级，component-value.js）：表单权限表达式初始值(ALL 时强制覆盖) > 装载现值 > 控件计算值(calculationValue) > 组件默认值 > 实体默认值 > 空。字段有值（含 false）不套默认值；为空才依次套。「打开方式=页面入参」这类 calculationValue 只在字段为空时生效——自装载数据后不会被它覆盖。唯一例外：审批权限方案配 initValueTriggerConditionEnum='ALL' 会把 record.data 置 undefined 强制套权限值，排查「字段莫名被改」优先查它。
- 应用内消息/邮件链路的固定套路：trigger.type=MESSAGE 监听 DTO 消息（topic=UDC_<appId>_MQ）→ 节点 CALL_APP_SERVICE(dubbo) 查 OrgMember 拿邮箱 → SUB_MICROFLOW 调 type=3 微流程服务（`udc_microflow_info.service_interface` 直指 Java 实现类，如 EmailService）→ Java 里 httpClientPost 外部网关。生产者用 `PUBLISH_BUSINESS_EVENT`（事件投递）节点发同一 topic。找“谁发的消息”就搜 data_schema 里的这两个节点类型，不要去 Java 里搜。
- 赋值条件自检：`isNull(X.ID) || X.ID == 0` 这类「为空或等于 0」漏掉**负数临时 id**（新建行 id 为负，既非空也非 0）→ 赋值分支被跳过，真实 id 永远回填不上。放宽为 为空/0/负数，或在变更模式下无条件赋值。
- SET 主实体 id 可能根本配不了：全应用生成代码里没有任何规则 SET 过主表 id（字段选择器不提供主键当赋值目标，画布上的 id 控件是隐藏纯数据绑定控件）——这是平台默认而非个例。设计器路线前先 grep 生成代码树有无 SET 主 id 的先例；没有就直接走替代路：①主档数据源 fixCondition 右侧绑页面入参.id + anyConditionValueEmpty 改忽略条件（条件 ready → 装载稳定）；②「生成/复制」微流程打开页面时把 id 写进普通业务字段中转，提交规则里转回；③微流程不预落子表行；④主档容器 disableAutoLoad（默认不加载）+ 条件右侧绑页面变量，页面规则把真实 id 写进变量触发标准装载（同应用已有此配法先例：上传附件弹窗容器 = condition id=页面变量 + disableAutoLoad:true）——默认值链只填空字段，灌入的真实 id 不会被覆盖，提交仍走标品 update-bpm。
- 数据容器被异步重洗的监控法：浏览器 Console hook `ds.setData`（所有装载/重置的唯一入口）打印 replace 标志/传入 id/调用栈，加 300ms 轮询哨兵记 `recordData.data.id` 变化时刻；服务端同步 tail 应用 pod 抓 `select-cascade-by-conditions` / `get-cascade-default-value` / `app-draft` 事件对齐时间轴。提交成功后 2~3 秒内的再查 + `app-draft/delete` 是成功回调的标准动作（queryData 刷新 + 清草稿），无害，别误判为肇事者。
指导用户配赋值节点时，指路**规则编辑器的字段选择器**，别让他去画布找控件：主实体 id 在画布上是无标题单行文本（绑定实体字段 id、埋在网格里）肉眼找不到；画布容器标题（如重复节「合同档案」）与字段树名字（如「合同档案1[单一记录]」）不一致是常态。给步骤时直接写字段树路径：目标=主实体[单一记录]→ID，来源=页面属性→页面入参→ID（preset_id，label 就叫 ID）。
- 草稿优先于 URL 入参 id：失败提交会把 id=0 现场存回 `app_data_draft`，形成恢复→失败→再存的死循环。解堵先删草稿，且必须在**新开页面**重测——已打开页面的表单 id 不会因改库/删草稿而变。
- 分支条件对了不等于赋值生效：打开生成代码 `pc/src/microflows/<ruleId>.ts` 确认该分支体内真的有节点——出现过「条件 `isNull(id)||id==0` 写对、分支体只有日志、没有任何 SET_VALUE」的配置，等于什么都没做。改前先看生成代码，别信设计器截图。生成物节点实现本身也可能是空壳：部分版本的 `nodeActions/call_service.ts`（调用服务节点）把 callService 导入注释掉、直接返回 context 值——节点静默不执行，用前先读生成物确认实现存在。
- 最快的「装载到了没」铁证 = 失败现场的 `app_data_draft.draft_data`：根 `id:'0'` + `__key:真实主键` + 子行 `id/__key=真实id` ⇒ 页面**确实装载过**（装载器把主键写进 __key），只是根的数据字段 id 没回填；别再判成「页面没请求过」。
- 主档数据源条件也要查：`pc/src/pages/<page>/profiles/component-settings.ts` 里主档容器（重复节/单记录）的 `anyConditionValueEmpty`（如 `returnNull`）与 `fixCondition`（如 `id EQ` 而右侧表达式未配置）——运行态在全无值时会直接跳过装载；`page-datasource-metadata.ts` 给出该容器的 entityName/dataShape 便于认主档。
- 提交按钮的规则 = 钉 id 的落点：查 `component-events.ts` 的 `button_<eventId>.onClick` 与 `page-info.ts` 的 `addOperates`（工具栏按钮名），就能把「提交/提交_自定义」按钮对应到具体规则 id。
- 用户观察与诊断冲突时（如「画布 id 明明有值」）：别复述结论，把运行态源码调用链走通来调和——「有值」多半指控件显示值，路由读的是 `recordData.data.id`，两者是不同存储。调和成功后再解释两条取数路径的区别。
- 汇报以「改哪个页面、哪条规则、哪个节点、条件与值」开头，机制解释放后面——用户要的是可执行的改动点，不是机制讲座。中间推理对用户不可见，别把「我上一条说法」留在最终答案里，发现前面说错要显式认错并给出修正版。用户消息里引用了截图/视频时先读图再定位：新截图按修改时间从 Pictures/Downloads 找最新，图片走 vision_analyze；**同机常有两处自动落图，两处都扫**：Hermes 的 `images/clip_*.png` 是其他任务的剪贴板留档（mtime 可能更新但内容与本次无关），用户亲手截的图在 `Pictures/Snipaste_*.png`——按内容判相关性，别只按 mtime 取，否则会对着无关图白读十来张；vision 通道 400 时用本地 OCR 兜底——`uv pip install rapidocr-onnxruntime` 按坐标输出文本（比 PowerShell Windows.Media.Ocr 省事），飞书 bug 单附件经已登录页 CDP fetch `/space/api/box/stream/download/all/<token>/` 直接拉原图。表单类截图用坐标还原版面：选项文本中间嵌的「请输入」输入框、被挤成竖排的列，就是「选项排版错乱」类 bug 的真身；先分清错乱在表单页还是生成文档——生成记录里该长选项值从未出现过 ⇒ 表单页问题（归口页面布局），别按生成文档问题去改模板。用户点名去看 jar/上服务器时，jar 审计走 seeyon-udc-runtime skill 的 Jar 审计节（本地 maven_root 配置化取最新版，CFR --jarfilter 按类反编译，常量池中文关键词扫描判定「生成骨架无业务逻辑」）；SSH 上服务器属需放行的写范围命令，被拦就退回本地证据链。
- DB 写操作必须 autocommit 直连并回读；封装查询函数若无 autocommit，UPDATE 会静默回滚且返回假成功。
- 同一业务量在两个页面显示不一致，先比两侧取数口径再谈数据对错：常见结构是「提交侧把算好的值回写主表快照字段，审批/详情页经聚合接口把子表明细全行重算」，两条链路的行集合与分母（含税/不含税）都可能不同，数值必然不同；先画两条取数路径（回写字段 vs 聚合子表+分母）再定位，别一上来就怀疑数据错。
- 「最近/一直无内容」这类定性必须先分状态、再分环境，缺一步就是假故障：同一张表并存草稿行与已生成行，草稿行正文为空属正常，混在一起统计会造出「大面积空」的假象；正确顺序是「按 status 分组 → 只看已生成 → 按月看趋势 → 双环境对照」。对照环境正常即说明是个案/历史，不要升级成产品缺陷，更不要据此下修复结论。
- UAT 业务键（合同号等）重复多行是脏数据常态：先按当前处理人/流程状态锁定「正主」行再对数；按业务键兜底「取 create_time 最新一条」的接口在重复键下会取错行；主表多行 update_time 精确到同一毫秒 = 被批量任务统一刷过，主表上的汇总/快照字段不可信，对账以子表明细为准。
- 「不该看的字段能看到」类权限缺陷：接口无条件下发全量字段组时，前端隐藏无意义（F12 直接可见），修复=接口按角色裁剪字段组（如销售侧只回考核毛利/毛利率，成本与实际毛利组不下发），按钮可用性同时加后端流程状态校验兜底，不要只改前端显隐。长川毛利聚合出口在 ContractMoneyUtil.getGrossProfitTotal（合同详情接口调用），子表明细在「核算后毛利数据」类实体；备货侧算完经 converter 写子表、审批侧再聚合读回，两侧分母（含税/不含税、行集合）不同必然对不上，修口径先对齐聚合行集合与分母口径。
- 用户扔日志截图问「啥问题」：先 OCR/读图提取异常类与线程名再判读。跨服务 SocketTimeoutException 报在调用方线程（kafka-invoker/scheduler 等）只说明它等下游回包超时，定位需栈上方目标 URL，直接向用户要截图往上一屏，别臆断下游故障。
- 没找到就说没找到，禁止用猜测顶替；但先穷尽获取手段再宣布缺料。运行态源码不必缺：`@seeyon/udc-runtime-core` 可从致远 verdaccio npm 仓库直接拉 tgz 解包读 dist（装载/分发/默认值合并全部源码级可查），获取与分析配方见 references/detail-page-load-submit.md 的「运行态源码」节。
- 多条 bug 单让挑一条做时：优先选「修复中」状态且本地已有定位产物/已改模板的（活已干一半，收尾最快）；排除涉外部系统联调、全流程回归面、需求含「前端配置功能开发」的。用户只要一条答案+理由（为什么这条好解决），不要把单条任务拆成子项再排优先级。
