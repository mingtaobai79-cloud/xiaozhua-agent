---
name: xiaozhua-integration-diagnosis
description: Use for xiaozhua integration diagnosis.
version: 0.1.0
author: Hermes curator
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [xiaozhua, low-code, integration, nacos, kubernetes, mysql, logs]
    related_skills: [xiaozhua-low-code-environment]
---

# xiaozhua Integration Diagnosis

用于排查低代码应用的第三方接口、微流程、实体落库和运行时配置问题。核心原则是证据优先：先确认真实代码链路、真实配置、真实日志，再判断同步是否成功。报告先给结论和证据，避免重复背景。

## Scope

适用于：外部接口同步、微流程路由和认证；DTO/底层实体/物理表映射；Nacos 配置；Pod 日志与 traceId；同步前后数据库核验。

环境必须显式标记为 `test2` 或 `uat`，禁止混用 kubeconfig、namespace、数据库或日志。不要把单次业务名称、traceId 或表名固化为通用规则。

## Workflow

1. **确认目标**：记录环境、namespace、应用 ID、微流程名称和时间范围。
2. **确认代码路由**：从 Controller 的 `@RequestMapping`、`@PostMapping` 和微流程名称拼出完整路径；从 AppService 实现确认远程调用、DTO 构造、`createBatch`/`updateBatch` 和异常处理。
3. **严格区分层级**：
   ```text
   XxxDto → Xxx（底层实体）→ 物理表
   ```
   不因 DTO 或 AppService 名称相似就认定物理表；要结合实体元数据、表注释、字段结构和主子表关系。
4. **核对 Nacos**：读取目标 namespace/dataId/group 的实际配置，逐项核对代码绑定 key；回读确认地址不是 `default-value`。
5. **先直连第三方原接口，再测微流程**：用户要求验证集成时，优先用 Nacos 中的 `accessKey`/`secretKey` 和实际 URL 直接 POST 第三方接口，记录 HTTP、耗时、业务 `code`、`msg`、`total`、`data` 和 `requestId`；确认远端确有数据后再调用微流程。不要把微流程返回 `true` 当成远端或落库成功。验证「某页面/区块取不到值」时，第三方基线必须**双环境成对打 + 对照组**：测试与生产两套地址都要取（从各环境 thirdinterface/配置取，不能拿一份推另一份），同一业务键两边各打一次，再选一个已知测试侧有数据的键做对照；生产 N 条 / 测试 0 条而对照组测试有数据 ⇒ 结论写「源头测试环境数据缺口」，不得归因为应用缺陷；两边都 0 时先核对必填参数与业务键格式。
6. **收票接口按主从两步验证**：收票主接口通常是 `FIND_CHECK_BY_CONTRACT/v1.0`，请求 `contents.startTime/endTime`；拿到主记录 `ID` 后，再调用 `FIND_SI_INFO_BY_SI_ID/v1.0`，请求 `contents.siId` 验证明细。开票 `INVOICE_MESS_LIST/v1.0.0` 与收票接口不可混用。
   - **智税云开票信息同步是独立链路**：先从源码确认 `IntelligentTaxCloudAppServiceImpl`、`mFCUSTOMpOIeVj` 和 `seeyon.zsy.getPiaoJuDataUrl`；它写入 `Kaipiaoxinxi`，不要误走采购合同 `/purchase/contract/invoice`（该接口是采购合同开票金额查询/回写）。完整微流程通常为 `POST /service/{appId}/spxxlby/microflow/MFCUSTOMpOIeVj`。运行时 DTO `Zsysjtbrc` 的 `kaishishijian`/`jieshushijian` 是 `Date`、`shifouquanliang` 是 `Boolean`；REST 请求优先传 epoch milliseconds 和 Boolean，不要直接传日期字符串。反编译证据、已验证远程响应及排查顺序见 `references/intelligent-tax-cloud-invoice-sync.md`。若返回 `The input is not a valid base 64 encoded string`，优先判断请求体字段类型/平台反序列化失败，不能归因于智税云远程接口；要先用日志确认是否进入 `IntelligentTaxCloudAppServiceImpl`。
7. **从生成 Controller 反查微流程路由（优先于业务扩展 Controller）。** 低代码生成的微流程 Controller 通常位于外部生成包/运行时产物，不一定在项目 `src/main/java`。必须检索源码、`target/classes`、依赖 jar、运行镜像或反编译 class，读取 `@RestApi`、类级 `@RequestMapping`、方法级 `@PostMapping` 的原值并拼接完整 URL。不要把扩展类中的 AppService 方法名直接当成 REST 路径，也不要按业务名猜路径。典型证据形态：`@RestApi("微流程-kaipiaoxinxiliebiao")` + `@RequestMapping("{appId}")` + `@PostMapping("kaipiaoxinxiliebiao/microflow/MFCUSTOMpOIeVj")` → `/service/{appId}/kaipiaoxinxiliebiao/microflow/MFCUSTOMpOIeVj`。
8. **看日志**：以实际运行 Pod、环境、namespace 和 traceId 精确筛选；保留远程入参/结果、`createBatch`/`updateBatch`、实体校验、异常和外层返回。过滤超长 ID 列表。
9. **核对数据库**：对同一主表和明细表查询执行前后数量、最大时间和业务唯一键，区分无远程数据、已存在、校验失败、事务回滚和吞异常。
10. **采购 ERP 同步要追到扩展代码。** 对采购订单/小时增量同步，优先检查 `extend/controller/PurchaseContractController`、`extend/domain/service/purchase/PurchaseContractService`、`extend/domain/service/impl/PurchaseContractServiceImpl` 和 `extend/domain/appservice/ERPMicroFlowAppServiceImpl`；从 `@Value` 配置键读取真实 ERP URL，再核对 `CaigouERPAppService`、`CaigouERPDto`、去掉 `Dto` 后的实体和物理表。不要把“开票测试接口”误认为“采购 ERP 同步接口”。对 ERP 分页同步，先用小时间窗和 `pageSize=1` 直连原接口，再执行扩展入口，并按 PO 唯一键、create/update 数量和失败汇总回读。

## Schema vs entity metadata

出现以下错误时：

```text
length must be between the specified boundaries:0 50
```

不能只修改 MySQL `VARCHAR(50)`。必须分别检查物理表字段和运行时实体 `com.seeyon.<app>.domain.entity.Xxx` 的平台元数据。只有两层都变更，并且重试后日志不再出现 50 的校验错误，才能判定生效。

物理表结构变更应保留原字符集、排序规则、注释和可回读证据；按环境操作规范确认后执行。

数值类型同理（实例：19 位合同 ID 写入 UDC 生成实体的 `contract_id`，运行时报 `Long -> Integer overflow`）：根因是双层类型都装不下——平台元数据 `udc_test2.udc_attribute.data_type=INTEGER(max_length=10)` + 物理列 `int(11)`。必须两层一起改：`UPDATE udc_attribute SET data_type='BIGINTEGER', max_length='20'` + `ALTER TABLE ... MODIFY COLUMN ... bigint(20)`（backup 表不动），改完后需在 UDC 设计器重新发布相关实体/页面，运行时校验才用新类型。执行写 SQL 前先保存原值快照 JSON 供回滚，执行后逐项回读（元 data_type + information_schema.COLUMN_TYPE）。

## Fix delivery（修复提交推送）

源码修复完成后的提交推送：git-bash 下 `git push` 会因 `git-askpass.exe` 缺失失败；用 `cmd.exe /c "git push origin <branch>"` 走 Windows 凭据管理器。被拒（remote contains work）先 `git pull --rebase origin <branch>` 再推；推完用 `git log --oneline origin/<branch>` 验证提交确实在远端顶部，不能以本地 commit 成功代替推送成功。

## 修复范围纪律（客户 ext 代码）

定位到根因后先分类，只在允许范围内改：

```text
允许直接改：空指针/拆箱 NPE、数字解析崩溃（NumberFormatException）、缺判空
允许直接改：参数、查询条件键写错（例如把物理列名当条件键）
必须先问用户：业务判断分支、取值来源（枚举编码 ↔ 枚举项值）、表/实体归属、接口语义
```

- **不要因为“某个样本在某张表 0 行”就断言接口查错表或业务逻辑错。** 分支口径由业务定义，先把事实摆出来（各表按同一 parent 命中行数、覆盖合同数）让用户判断；实例：产品/服务行的取值分支是“迁移合同查产品服务行、新数据查内部结算/非内部结算子表”，两侧都按设计工作，凭数据形状宣布“查错表”是误判。
- 用户明确要求过：不要乱改业务逻辑，只修空指针和参数错。即使是看起来明显错的取值（`getEnumCode()` 当数字用），也先给出**文件 + 行号 + 原写法/新写法 + 依据**，等确认再改；改动错了立刻回滚，不要辩解。
- 加固优先“防御 + 可观测”，不改取值口径：新增 `safeLong(x)`（非数字 → null + warn）替代裸 `Long.valueOf`/`Long.parseLong`，跳过处打 warn 日志，事后可用日志串计数统计数据缺口。
- 静态扫描出的“数据缺失才会炸”的点（`selectById(null)`、`getContent()` 未判空、枚举 item 查不到）不要一次性全改，先汇总数量报给用户等他发话。
- 只由业务流程触发、没有 HTTP 入口的接口，可在既有测试壳（如 pushTest 风格 controller）里临时补一个入口来测（用户认可的做法），不要为测试去改主链路代码。
- 改完一处就编译一次（单文件编译脚本），不要攒一批再编译。

### 枚举项、条件键与部署判定的平台事实

- **枚举项转数字必须取 `itemValue`。** `CtpEnumItemDto` 上 `enumCode` 是枚举编码（同一枚举所有项完全相同，如 `kj_status`、`to_contract_file`），`itemValue` 才是枚举项值/项编码；`Long.valueOf(x.getEnumCode())` 会抛 `NumberFormatException: For input string: "kj_status"`。要拿“item 的 code”就是 `itemValue`。
- **平台查询条件键必须用属性名，不能用物理列名。** 用列名会抛 `IllegalArgumentException: 属性[xxx]不存在`；若需要属性名/列名都兜一次，外面必须包 try/catch，否则一次失败整条链路 500。
- **判定“修复没生效”之前先核对线上镜像版本与本地提交。** 构建往往滞后于 commit（镜像 tag 对应的提交比工作区/新提交早），先取运行中镜像版本 + 启动时间，再用“自己新增的那条 warn/日志串在日志里的出现次数”判断哪一轮真的上线了，否则会把“没部署”误判成“没修好”。

## Response interpretation

- `API PASS` 只表示 HTTP/外层业务响应成功。
- 远程日志出现“接口调用成功”且 `total>0`，随后 `createBatch` 报错，根因在本地实体/事务。
- 外层 `BOOT_0000` 不能覆盖内部 `BOOT_6000`；检查是否吞异常或固定返回 `true`。
- `BOOT_1006` 时检查认证载体（Header/Cookie）、登录域、有效期和 Referer/Origin。
- **HTTP 超时不等于业务未执行。** 对同步微流程必须在请求超时后继续检查运行 Pod 日志与数据库快照；只有日志和同一目标表的回读都没有业务证据，才能判定为未执行或 `UNVERIFIED`。
- **数据库回读优先于客户端响应。** 若主表/明细表在调用窗口内出现新增记录，且日志能关联到本次调用，即使 HTTP 客户端超时，也应将业务落库标记为 `LIVE PASS`，同时单独记录接口响应为 `TIMEOUT`。
- **收票类同步要分别核对主表和明细表。** 票据池主记录通常落到 `Shoupiaoxinximingxi` 对应表，票据池明细落到 `Piaojuchimingxi` 对应表；分别记录执行前后 count、最大时间和新增量，不能用单表结果代表全链路。
- **日志筛选要抑制噪声。** 先按调用时间窗口和 traceId 定位，再提取 `BillAppServiceImpl`、远端 URL、`total/code`、`createBatch/updateBatch`、异常等关键行；不要直接输出整段包含大量 `dynamicJoinSelect` 的日志。
- **同一实体的多个对外接口要做同字段 diff（值未转化审计）。** 一端返回可读名称/枚举文本、另一端同字段返回裸 ID（≥5 位数字字符串）即为转化缺失；根因通常是反射 beanToMap 组装路径没有调用手工路径的枚举/人员/币种转化函数（实例：手工路径逐字段调用 getCtpEnumItemValue/getMemberName/getHuilvpeizhibiaoName，反射路径 0 次调用，converter 的 convertToString 只是 value.toString()）。注意此类端点均为 @PostMapping，GET 探测只会得到 405。
- **"查不到数据"先复现 DB 查询条件再定性。** 接口返回 code=E"没有对应的合同信息"时，从源码提取全部查询条件（如 statusType=COME_INTO_FORCE + shenpileixing=枚举ID），直连库按同条件跑一遍：若全库满足组合的行极少（实例：仅 1 条），用它 LIVE 复测接口——返回正常即判定"接口按设计工作、样本不满足前置条件"，而不是接口缺陷。CTPENUM 列存的是枚举项 ID 不是业务 code，判定前先 `ctp_enum_item` JOIN `ctp_enum` 查枚举名（name 是 `{"zh_CN":"..."}` i18n JSON）。金额类 null 的定性也要 DB 取证：同一业务数值可能存在于另一个 pinyin 列（实例：`htzjehs` 全库非零 0 条 vs `fnbjshtzehj` 非零 14,792 条——后者才是真实金额来源）。UNVERIFIED（样本无数据）接口先查子表 `parent_id` 关联找有数据的其他合同换样本，不要直接要求造数。**但搜表前缀要宽且用反向查找兜底**：判"全库无数据"前先 `SHOW TABLES` 用多个前缀变体扫，再用 `udc_test2.udc_entity` 的 `caption LIKE '%业务名%'` 反查物理表名（实例：产品赠物实际表是 `chanpinze_7279308198137569652` 有 2,206 行，按 `chanpinzeng*`/`zeng*` 前缀搜索全部漏掉导致误判"需造数"——caption 反查一发命中）。多轮测试样本推荐按"一张合同覆盖最多接口子表"从 DB parent_id 统计中选，可将多轮测试压缩为一轮。

### 推送类接口失败归因（先读对方响应原文，再决定动不动代码）

外层 `content=false` / `BOOT_3000` 大多只是包装：推送类接口把对方响应体映射成 `isSuccess()`。在 traceId 日志里按顺序取三行，拿到对方原文再定性质：

```text
<接口名>推送地址：<url>
发送post请求成功：<url> params: {...}
<接口名>推送响应：{ ...对方原文... }
```

```text
对方业务校验拒绝（如“已存在，禁止重复创建：<对方单号>”） → 业务/数据问题，改样本，不改代码
对方必填字段为空（ORA-01400/必填校验）                  → 回本地报文找缺失字段 + 查该字段来源列在库中的值
我方堆栈（NPE / NumberFormatException）                 → 才动本地代码（判空 / 安全解析 / 条件键）
```

- **新建/save 类接口要用“对方系统尚未建档”的样本。** 同一合同 edit 报成功、save 报“已存在”是最强对照：链路通，是对方的新建校验。样本判定线索是本地 ERP 单号列（如 `hetong_e_r_p_id`）为空或 0。
- **对方必填字段为空时，先定性为“报文取数字段口径”问题并上报，不要自己换取数列。** 反查链条：对方报的列名 → 我方报文中对应字段有无 → 本地赋值点的来源属性 → 该属性在库中的值；同时给出同业务其他候选列的实测值让业务选。
- **必填参数没传导致的空结果/失败是调用方问题，不改代码。** 返回空列表前先核对必填参数（按流水号查询必须给 `contractNum`，传 `{}` 会被 blank 校验短路返回空）。
- **拿日志两种方式并做镜像核对。** ① 按 traceId 精确取窗口；② 日志已被回收或 `unable to retrieve container logs` 时，优先用最新 rollout 的 Pod 并重新触发一次接口拿新 traceId 立即取。取日志同时核对运行镜像版本，避免在旧版本上继续归因。
- **样本批测逐条闭环，不要用一次批量推送的结果下结论。** 每换一张样本就重新调用一次并按新 traceId 立即取“推送地址/params/推送响应”三行；某张样本日志里三行都不出现 = 我方早退，与“对方拒绝”是两类结论。试完一批仍无通过样本时，结论写“现有数据中无合适样本，需业务造数或确认接口预期场景”，按状态维度把分布讲清楚（已建档/已生效样本 → 对方报“已存在”；未建档但行匹配不上的样本 → 我方早退），不要把“找不到样本”包装成通过。
- **用户拍板保留取数字段口径后，定性转为数据侧，不再找代码改动。** 例：用户确认“接口就用 htzjehs1 这个字段不变”，而该列全库非空 0 行 → 结论是“该数据下接口必然被对方必填校验打回，需回填数据或业务侧容忍”；给量化证据（属性→物理列→`COUNT(*) WHERE col IS NOT NULL` 的实测行数）并停止在代码里找原因。
- **无 HTTP 入口的接口被问“还差什么”时，先证明有没有独立实现。** 把微流程表按 `caption` 关键词全表筛（含“审批结束/合同结束/编号”等多种说法），再找同名实现类；若筛不出独立条目、实现类又与既有接口同一个方法，结论就是“代码不缺东西，缺的是那个业务事件触发条件（如合同走到审批结束）”，不要把它记成“未实现”。

## Reporting

按此顺序简洁报告：

```text
结论：PASS / FAIL / BLOCKED / UNVERIFIED
环境：test2|uat，namespace，应用
调用：真实路由、HTTP、业务 code、traceId
日志：远程调用 / 实体写入 / 错误根因
数据库：表，执行前后数量，变化量
修复状态：改动层次和回读结果
```

区分 API PASS、LIVE PASS、FAIL、BLOCKED、UNVERIFIED，不用“接口成功”代替“数据已落库”。

联调进度类提问按用户口径回答：

- 用户问“还剩几个接口没测完”时，第一行给数字和名单（如“剩 4 个：2.1 / 3.4 / 3.6 / 51”），不要贴逐条证据表；他要细节会再问。
- 用户说“这两个分别在哪里，我去看看”时，给：绝对文件路径 + 当前行号 + 原写法→新写法 + **已提交 commit / 工作区未提交**的区分 + 可直接执行的 `git show <commit> -- <file>` / `git diff -- <file>` 命令。
- 报“已改 / 待提交”必须和 `git status`、`git diff` 对齐：先说清哪些在 commit 里、哪些只在工作区，不要把未提交说成已修。
- 多轮测试统计“总任务数”和“本人负责数”分开报。

## Pitfalls

- DTO 不是底层实体；实体也不等于物理表名。
- 物理表改长不代表实体元数据改长。
- 固定成功返回会掩盖 AppService 失败，必须看内部日志。
- 只看表总数不够，要结合 traceId、业务 ID 和时间字段。
- URL 必须从 Controller 注解确认，不能猜。
- 飞书 Sheet 可能用 Canvas 渲染、多维表格 DOM 虚拟化，正文为空不代表没有数据；应查认证网络请求或运行时 API（见 `references/feishu-data-extraction-via-cdp.md`）。
- 反编译只是 STATIC 证据：它证明代码里有什么，不证明环境里配了什么。链路结论要标 STATIC，动到环境（设计器、存储、部署）的判定必须补 LIVE。
- 日志和配置可能包含凭据，输出时脱敏。
- Nacos、数据库结构、Pod 重启等外部写操作必须有明确授权和回读验证。
- 单文件 `javac` 校验会被陈旧的 `target/classes` 或旧版本依赖 jar 骗出“找不到方法/符号”的假错：把精选版本的业务 jar 排在 classpath 前面，或把相关源码一起编译，再判定编译是否真的通过。
- 我方堆栈消失不等于接口通过：异常修完之后暴露出的内部 `false` 往往来自对方业务校验，必须继续读对方响应原文，别把它记成“修复无效”。

## 低代码事件链取证（微流程 ↔ MQ 事件 ↔ 生成服务类）

排查“某个业务事件该发的邮件/该走的流程没生效”这类问题，目标不是猜设计器，而是从客户应用的**编译产物**还原：谁触发、传了什么、文案在哪拼、哪个分支是死代码。完整步骤与命令见 `references/microflow-event-chain-forensics.md`，要点：

1. 微流程实现类在业务应用 jar 的 `com/seeyon/<app>/` 下（`MF<xxx>Service`/`MFSERVICE<xxx>Service`），事件监听是 `<同名>Listener`，入参 DTO 在 `microflow` 包，**不在项目 `src/main/java`**；列 jar 条目 → 扫字节码常量池中文串 → 反编译命中类。
2. Listener 的事件泛型（如 `BpmStepbackEvent`、`BpmEventActivityReadyEvent`）就是触发源；日志串/`buildMfLogV2` 参数给出微流程中文名。
3. 找调用者时全仓扫 jar 里出现的类名（符号引用），区分“只定义”与“被引用”，不要把没人调用的类当链路。
4. 入参 DTO 的字段就是上游唯一能给的东西。**目标场景需要的标识不在入参里，就是链路缺陷**（标题/文案流程因此无法区分场景），修法是 DTO 补字段 + 上游投递时填，而不是在末游硬猜。
5. `setXxx("驳回")` 这类硬编码常量会让本该有分支的流程永远走一个分支；同一类里成对出现的场景关键词只有一个活分支时，另一个是死代码。
6. 判定“某场景识别不了”前先问“触发事件存在吗”：若平台侧只有 `ChangeTypeEnum.AddNode(0)` / `currentActivityChangeType`，而全应用没有任何监听者（0 命中），结论是**缺触发源**，不是设计器缺陷。

报告要区分 STATIC（反编译事实）/ LIVE（环境实跑）/ UNVERIFIED；“设计器里能否选到某事件节点”必须在环境查，不能从编译产物推断。

## MQ 消息重发语义（监听失败 / 发送失败 / 补偿）

被问「消息监听失败有没有重发」「监听抛异常会不会重发」时，按**框架层（引擎投递行为）→ 监听方法是否吞异常 → 补偿层（落库+定时任务）**三层取证，引擎对照表、补偿 job 清单和陷阱（如 `MESSAGE_RESEND` 不是失败重发）见 `references/mq-message-retry-semantics.md`。核心规则：异常逃不出监听方法就没有框架重投；RocketMQ 默认重投后进死信无人捞；Kafka 失败可能被后一条成功的 offset 跳过；Redis 无重发；真正的重发在发送端落库 + 时间轮 + 定时补偿。结论标 STATIC，运行时引擎（`seeyon.mq.engine`）必须补 LIVE。

## Reference

票据池主接口/明细接口的直连请求与已验证响应见 `references/ticket-pool-direct-api-verification.md`；推送类接口失败的对方响应形态与归因对照见 `references/push-interface-failure-attribution.md`；微流程/事件/生成服务类的链路取证见 `references/microflow-event-chain-forensics.md`；飞书多维表格与电子表格取数见 `references/feishu-data-extraction-via-cdp.md`。
