---
name: seeyon-runtime-configuration-and-sync
description: Use when changing Seeyon runtime config, verifying sync, diagnosing data-migration plan runs (为什么失败/是否落库), or converting a field between entity-reference and enum semantics (字段引用转枚举/影响面清单).
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [seeyon, nacos, low-code, integration, sync, mysql, kubernetes]
    related_skills: [seeyon-low-code-environment]
---

# Seeyon Runtime Configuration and Sync

用于处理致远低代码应用的第三方接口配置、票据/开票同步、Nacos 配置核验、实体字段限制与落库验证。核心原则：把“接口调用成功”“业务逻辑成功”“实体校验成功”“数据库写入成功”分别取证，不能用 HTTP 200 或 `content: true` 代替最终成功。

## Scope and boundaries

适用于：

- 从源码/反编译 Controller 确认微流程真实路由；
- 从 `XxxDto → Xxx` 追踪到物理表；
- 读取或修改 test2/UAT 的 Nacos 配置；
- 诊断票据池、开票等同步任务；
- 修改目标表字段长度并验证实体层是否仍有旧约束；
- 把字段从「引用另一实体（ENTITY）」改为「枚举项（CTPENUM）」，需要全仓影响面清单；
- 联合检查应用日志、接口响应和数据库前后快照。

不把相似表名、记录数或猜测的 Controller 路径当作证据；不把物理表 DDL 修改误认为平台实体元数据已经修改。

## Required evidence model

每次报告至少分层标注：

- `FACT`：源码、Nacos GET、SQL 回读或日志原文直接证明；
- `OBSERVATION`：一次真实执行观察到的结果；
- `HYPOTHESIS`：尚未被直接证实的解释。

最终状态使用：`PASS`、`FAIL`、`BLOCKED`、`UNVERIFIED`。只有数据库同一目标的回读显示变化，才能报告落库成功。

## Procedure

1. **锁定环境和应用。** 明确 `uat` 或 `test2`、namespace、应用 ID、数据库名、Nacos namespace/dataId/group。不要依据主机名或相似配置猜环境。
2. **追踪代码链路。** 从业务方法开始，记录 Controller 注解中的 `@RequestMapping`、`@PostMapping`，得到完整路由；再记录 AppService、DTO、去掉 `Dto` 后缀的实体名，以及实体到表的映射证据。`XxxDto` 是接口对象，不是底层实体名。
3. **先读取运行配置。** 用 Nacos API 或已认证控制台读取精确的 `dataId/group/tenant`；修改前保存非敏感的配置键和值摘要。对外部接口地址优先以运行环境配置为准，源码默认值只作为 fallback 证据。
4. **确认配置键。** 对每个接口建立映射，例如“开票数据接口”“票据池主接口”“票据池明细接口”分别对应实际 `@Value`/配置键。不要把主表、明细表和接口名称混为一谈。
   - 智税云 `INVOICE_MESS_LIST/v1.0.0` 的同步对象是 `Kaipiaoxinxi`，由 `IntelligentTaxCloudAppServiceImpl.mFCUSTOMpOIeVj` 分页查询（代码每页 100 条）后按发票 ID 分为 `createBatch`/`updateBatch`。它与采购合同模块的 `/purchase/contract/invoice` 不同：后者是采购合同相关的开票金额查询/回写测试入口。调用前必须先根据源码和运行日志确认所测链路，避免因“开票”同名误测。
5. **建立数据库前快照。** 读取目标表记录数、关键字段类型、最大长度和最近时间；如存在主表/子表候选，使用 `parent_id`、表注释、实体字段和 AppService 作为联合证据。
6. **执行配置或结构写入前确认范围。** 配置覆盖、数据库 `ALTER TABLE`、Kubernetes patch/restart 都是写操作；只修改用户指定的环境、应用和字段。避免打印密码、token、私钥或完整配置。
7. **修改字段时双层核验。** 先确认数据库 DDL，再确认平台实体元数据/生成实体校验。若日志仍报 `0 50`，说明实体层约束可能仍为 50，即使 SQL 列已经是 `varchar(200)`。
8. **重新执行真实接口。** 使用已确认的真实 Controller 路由和合法认证上下文。记录 HTTP 状态、业务 code、traceId 和是否进入 AppService/批量写入日志。登录跳转、`BOOT_1006` 等必须标记为未执行业务，不能当作同步成功。
9. **回读验证。** 按同一表、同一字段、同一时间窗口读取前后记录数和最新时间；同时按 traceId 检索日志。主表增加不代表明细表增加，必须分别核验。
10. **报告分层结论。** 明确“远程取数”“本地转换”“实体校验”“主表写入”“明细写入”各自 PASS/FAIL/BLOCKED，不用一个总的 SUCCESS 掩盖异常。


## ERP 时间范围同步与结果判定（可复用）

对 `Date` 类型的 HTTP 查询参数，不能把 Java `Date` 直接“传过去”；URL 参数始终是字符串，Controller 必须显式绑定格式：

```java
@DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
@RequestParam(required = false) Date last_update_date_f
```

两个起止时间参数都要加注解。部署后必须用真实 URL 传入 URL-encoded 的空格，并从运行日志确认 DTO 已解析成日期，而不能只看 HTTP 200。

ERP 全量/大时间窗同步时，执行顺序固定为：

1. 先直接调用 Nacos 配置的远程接口，记录 `code`、`total`、分页大小；
2. 再调用应用的带时间范围 Controller；
3. 执行前后读取同一目标表快照；
4. 按 traceId 聚合每页“创建/更新/跳过/失败”，并核对 `创建 + 更新 + 跳过 + 失败 = 本页返回数`；
5. 对 `create/update` 的 AppService 返回体检查业务码，不能把 HTTP 200、外层 `code=200` 或日志“成功”当作实体写入成功。

`跳过更新`通常表示本地已存在相同业务键（如 `saleNumber/manufacturerPo`），且 ERP `last_update_date` 不晚于本地 `update_time`；它不是远程未拉取，也不是失败。全量重跑后大量跳过是幂等逻辑的预期结果，但应验证业务键是否唯一，避免把重复返回误判为新数据。

实体长度问题要分两层验证：数据库列长度和平台实体元数据约束。若日志出现 `BOOT_6000`、`length must be between ...`，先查实体字段实际限制；调整后必须重新跑同一时间窗，并确认异常数为 0、数据库增量与创建成功数一致。若超长供应商等异常被修复，补偿重跑应作为独立证据记录。

注意：本地源代码提交成功不等于 test2 已部署。测试前先确认运行 Pod 的版本/启动时间或日志中的代码行为确实包含修改；若仍出现旧约束，优先判断为未发布或运行实例未刷新，而不是继续重复调用。



```text
dataId=<application-data-id>
group=<actual-group>
tenant=<environment-namespace>
```

读取用 Nacos Open API：`GET /nacos/v1/cs/configs`（**复数**；写成单数 `config` 返回 404），带 `tenant` / `dataId` / `group`。

返回值是**带缩进的 YAML**：按缩进判断层级——`schema`、`database`、数据源子级下会出现与顶层同名的键，用扁平正则扫 key 会把子级配置当成顶层配置。找源库/目标库 `jdbc_url` 这类键时必须按层级取。

读取后必须回读验证。若通过控制台操作，优先使用已认证 Edge/CDP 只读确认页面显示的 namespace、dataId、group；不要把浏览器页面的空 DOM 当作表格单元格为空，Canvas Sheet 必须通过其网络/runtime 数据接口取证。

配置更新的验收条件：

- Nacos PUT/POST 返回成功；
- 立即 GET 同一 `dataId/group/tenant`；
- 确认目标键和值已存在；
- 再观察应用是否重新加载配置或执行一次接口验证。

## 字段语义改造：引用表（ENTITY）→ 枚举（CTPENUM）

当用户说「把 X 字段从引用某张表改成枚举，全仓列出来我们要修正」时，交付物是**落盘的影响面清单 + 数据侧基线**，不是对话里的摘要。

- **先定语义，再 grep 代码。** 物理列注释是权威：`DataType:ENTITY|<实体名>` = 引用实体主键，`DataType:CTPENUM` = `ctp_enum_item.id`。同一业务字段在不同表可以分别是 ENTITY / CTPENUM / varchar，必须逐表查，禁止按字段名成批归类；生成代码里带「引用表名」的 Service 字段常是历史误命名，不能拿它判语义。
- **用覆盖率 SQL 证明现状。** 「命中引用表主键」与「命中 `ctp_enum_item`」分开计数：全命中引用表即需刷数，两边都不命中的脏值单独计数。刷数优先走引用表里已有的枚举列 JOIN，不按名称文本匹配。
- **扫描分组，并排除同形异义词。** `huilv`（汇率）是 `shuilv`（税率）的子串，`XxxShuilvpeizhibiaoService` 会被 `huilvpeizhibiao` 的正则命中部；用 `[Ss]huilv` / `\bhuilv` 锚定排除，并把排除项连同理由写进清单，否则统计虚高、无关模块被误列为改造点。
- **清单写进被改造仓库之外的目录**（项目同级），格式 `file:line → 现状 → 改法`，按模块分组并标出必改 / 可复用样板 / 排除项；单列「风险点」与「待用户拍板的口径」（用哪一枚枚举、关联字段是否一起改、对外展示用名称还是代码），不替用户决定。
- **顺带发现的缺陷单列并附证据**：同一字段两套解析、枚举 id 被写进引用字段、内部主键输出到外部报文、查不到返回 0 / 抛业务异常、硬编码枚举类覆盖不全。

改造顺序：公共取值入口（Util）→ 写入侧（导入、建草稿）→ 读取侧（导出、对外接口），改一处跑一次。SQL 模板、分组清单骨架见 `references/field-semantics-and-enum-conversion.md`。

## Database and entity pitfalls

- 物理表列长度与平台实体字段约束是两层独立状态；必须分别查询。
- 主表/明细表可能共享相似前缀；`parent_id` 通常是明细关系线索，但仍需结合 AppService 实体。
- `createBatch` 被实体校验拦截时，SQL 表记录数不会增加；不能只看接口返回的 Boolean。
- 代码捕获异常后仍返回 `true` 时，响应是弱证据，必须以日志和数据库为准。
- 修改 SQL 后若重新调用进入认证跳转，不能用这次调用证明修改有效；应先恢复认证，再重新执行。
- PolarDB 不接受 `CREATE TABLE ... SELECT`（报 `Statement violates GTID consistency`）；建备份表用 `CREATE TABLE <t>_bak LIKE <t>` 再 `INSERT INTO <t>_bak SELECT ...`。
- 清理重复/脏数据：先建备份表并回读备份行数 → 按精确 id 列表删除（不要用范围条件猜）→ 再回读主表计数，并把回滚 SQL 一并交给用户；备份表保留到用户确认清理无误为止。

## Sensitive-data handling

凭据只从本机私密配置读取，不写入技能、脚本、日志和最终报告。报告中只保留环境、资源名、配置键、非敏感 URL、字段类型、traceId（如需要）和错误摘要；必要时对 token、账号、密码完全脱敏。

## 平台数据迁移（迁移方案）运行核验

适用：用户在平台上跑完「数据迁移 / 融合同步」方案，要求「看日志、看库里落了没」。先锁定源库和目标库，再做源目标对账；不要用 Pod 日志里的失败计数当作根因。

1. **先定位源与目标，不要从执行 Pod 推断落库环境。** 方案与数据源定义都在应用库中：`migration_<metadataId>` 是方案/数据源/映射实体表，数据源实体的列含 `jdbc_url`、`username`、`passwords`、`driver_class_name`、`enabled`。按方案记录里的 source/target 数据源 id 取 `jdbc_url` 才能得到真实库名。执行 Pod 在 test2 不代表写入 test2 库——目标数据源可能直接指向 `*_uat`，跨环境写入是常见配置。
2. **Pod 日志按三类行取证，不找逐行失败明细。** (a) 计数行：`[全量迁移] 迁移完成，总共处理: N 行，成功: A 行，失败: B 行`、每批的 `[数据转换] 转换完成，成功: A, 新增: B, 更新: C, 跳过: D, 失败: E`、`[迁移日志] <源表> - 数据一致性校验通过: 源表总数=N = 插入数(A) + 跳过数(B) + 失败数(C)`；(b) 消息行：`[日志保存] 保存日志: MigrationLogDTO(logId=…, taskId=…, tableName=…, level=…, message=…, errorMessage=…)` 是平台唯一打印 message 文本的地方，用 `grep <planCode>` 配合 `grep -oE "message=[^,]*, details" | sed -E 's/[0-9]{4,}/N/g' | sort | uniq -c` 一次列全该次运行的消息模板和重复次数；(c) 备份行：`备份完成: <目标表>_backup_<epochMs>`，备份表常在运行结束被清理，别指望事后回读它拿运行前状态。**「应用库日志明细表 0 行」≠「平台没输出逐行原因」——别就此收尾。** 明细落在 `migration_<log_metadataId>`，但应用库 test2/uat 上该表常恒为 0 行；逐行原因实际打在**跑 UniversalMigrationService 的那个 pod 日志**里（`样本 ... 校验失败，差异字段: [...]` / `[数据校验] ...`），只是集群轮转 + 滚动发布会很快把旧 pod 日志带走，必须**先抢时间抓日志再慢慢分析**。进度/任务记录在应用库 `logscheme_<id>`（`stage`、`progress`、`processed_rows`、`total_rows`、`plan_code`、`task_id`、`log_time`），该表没有 message/level 列；`ctp_data_migration_task_info`/`_detail` 常为空。
3. **落库用 `COUNT(*)` 精确核对**，不要用 `information_schema.tables.table_rows`（估算值，会差几行）。
4. **用批次列判定「本次产物」**：目标表 `batch_id` ≈ 该次运行时刻的 epoch 毫秒，`task_id` 形如 `migration:<planCode>:<epochMs>`；表里其它 batch_id 是历史遗留。若方案映射了源的 `update_time`，目标 `update_time` 不会刷新——不能据此判断「没写入」。
5. **源目标对账定根因。** 从数据源定义取源库只读连接（只做 SELECT），先 `SHOW CREATE TABLE <目标表>` 读列注释（`DataType:ENTITY|multiSelect:false|<实体名>`）确定字段映射，**实测对齐键**：用外键名猜（父表主键字段 → 目标 `business_id`）会得到「源有目标无 = 全部」的假象，真实对齐键可能是源子表自身主键。同一个「假全集」也会来自**值类型不一致**：源库 driver 读到 int、工具封装读到 str，`int in {str}` 恒为假 → 必须两侧统一 `str()` 再比较。差集后把失败行按父级状态、空值、枚举分类。
6. **报告分层**：逐个任务给出运行时刻 / 源表 / 处理·成功·失败 / 目标库.表；落库核对写成「目标行数 = 本次 batch_id 行数 + 历史遗留行数」；失败归因给出失败行数、涉及父级数、父级状态分布，并标注证据来源（源库对账还是平台日志）。平台未打印的失败码要明确写「平台未输出逐行原因」，不要补编。

### 失败行机制取证（方案配置 + 计数 + 2×2 判别）

用户追问「他是怎么失败的」时，要给出机制而不是相关性。三步取证：

- **读方案配置，先确定「失败」还是「跳过」。** 方案表 `migration_<id>` 的 `is_parent_relation=1` + `parent_table` / `parent_business_id_field` / `target_field` / `required=1` 表示子表行必须在目标父表里按业务键找到父记录；查不到即必填校验失败 → 整行计入「失败」，既不插入也不计入「跳过」。同一框架在 `required` 未生效的历史运行里记的是 INFO「跳过该条数据（找不到主表数据）」。所以「失败」不等于技术故障，先读配置再解释计数。
- **用每批计数行定位失败阶段。** `[数据转换] 转换完成，成功: A, 新增: B, 更新: C, 跳过: D, 失败: E`：某批出现 `新增=E=失败`、其它批 `新增: 0, 失败: 0`，即失败全部落在新增写入路径（转换阶段的父级/引用解析在写库前就判死）；`一致性校验` 里的 `插入数` 是实际写入行数。
- **2×2 判别表把相关性变成判别。** 把源行按「父级是否存在于目标父表」× 「是否落库」交叉计数；只有干净分离（父级存在→全落库、父级缺失→全失败）才能把机制定死。再**排除替代解释**并写进报告：引用/枚举映射目标表里是否真有这些枚举值、`SHOW INDEX` 有无唯一约束、字段长度、业务键为空的行数。

平台数据迁移常见失败形态：方案只迁了父表中 `status=0`（生效）的行，而子表里挂在已停用 / 已删除 / 空的父级上的行会全部插入失败，被计入「失败」而不是「跳过」。这不是平台缺陷，是源侧未过滤；给出过滤条件的修复（在源查询上排除 `parent_id IS NULL` 与父级失效的行），并说明是否属于无需迁移的业务数据。历史批次遗留行会让总数一直对不上，报告要单独列出，清理前先要用户确认。

### 抽样校验失败（VALIDATE 阶段）→ 整表回滚

「迁移失败 + 数据回滚」**不等于**数据有问题。先分清是哪个阶段抛的：

- **写入阶段失败**（上一节）：一致性校验本身的计数就不平（`插入数 + 跳过数 + 失败数 ≠ 源表总数`），失败行集中在父级失效/空键。
- **VALIDATE 阶段失败**（本节）：写入其实是成功的 —— `数据一致性校验通过: 源表总数=N = 插入数(N) + 跳过数(0) + 失败数(0)` 会正常打出，然后才在抽样校验里抛 `数据校验失败，进行数据回滚`。此时是**校验实现的口径问题，不是数据问题**，重跑永远同样失败。

判读三步：

1. `grep -c "数据一致性校验通过"` 与 `grep -n "采样校验有失败"` 同时出现 ⇒ 锁定 VALIDATE 阶段。
2. `grep -o "差异字段: \[.*" pod.log`：**若所有样本只差同一个字段**，就是该字段的比对口径问题，与其余 99% 数据无关。
3. 形态特征判根因：源值 `2024-03-31T00:00` 对目标值 `2024-03-31 00:00:00` 这种**同一时刻的两种字符串形态**，说明该字段没进代码的 Date 分支（`fieldMapping.fieldType == Date.class || type == FieldType.DATE` 不成立），落到最后的字符串 `equals` 分支恒为假。常见成因：映射记录的 `field_type` 没标成 DATE，或目标列实际是 `varchar` 而源是 `datetime`（`SHOW COLUMNS` 逐列比对即可证实）。

修复优先级（给出方案，不要只报问题）：① **纯配置修法（首选；能改配置就不要改代码）**：让它进 Date 分支即可。两个字段是两个闸门，凭「要不要动落库」来选：**只改 `java_type` 为日期**——写入侧只看 `field_type`，所以落库内容一字不变，校验侧因 `fieldType == Date.class` 进日期分支 ⇒ 通过，**这是最安全的修法**；只改 `field_type` 为日期则写入侧也改走格式化，此时 **`format` 必须非空**（否则落库形态从字符串变 Date 对象，可能改变目标 varchar 列的内容，`format` 非空时输出同一 pattern 字符串则不变）；两个都改等价于同表 `create_time`/`update_time` 的配置。**`format` 本身不决定分支**：只配 `format` 而 `java_type`/`field_type` 仍是普通，照样落进字符串直比（本类字段常常早已配了 format 却仍然失败），所以把「配 format」当修法是错的；判走哪条分支只看 `field_type`/`java_type`，且这两列描述的是**目标侧**语义（用「源/目标列类型不一致」的映射行即可验证：`java_type` 跟目标走）。② 只当业务上确实要让该列能被 SQL 当日期用时，才改目标列为 `datetime(6)`：改列前先确认该列可空、且源列无空串/脏值（写入侧解析失败会置 null），并给源查询加非空过滤。③ 把「抽样 100 条只要 1 条失败就整表回滚」改成按字段统计失败率再决定是否中断（设计缺陷，任何形态差异都会 100% 失败）。改方案配置/表结构属写操作，先确认再动。定位并修好一个字段后，**立刻扫全部映射做同类排查**（源列与目标列的类型大类逐对比对），把其余潜在同因失败一次性列出，别等下一次回滚。映射记录里 `field_type` / `java_type` 存的是枚举项 id，解码 SQL、写入侧不变量与同类排查脚本见 `references/platform-data-migration-verification.md` 第 7 节。

回滚已生效的证据：目标表只剩 `batch_id=0` 的历史行、本次 `batch_id` 一行都不剩（`need_backup=1` 时回滚是 `TRUNCATE` + 从备份表回灌 + `DROP` 备份表，所以**备份表事后查不到，不能靠它取运行前基线**）。

### 批次级中断：一次全量迁移只失败一部分，剩下的停在「准备中/运行」

「调度失败」经常不是某个方案报错，而是**这一轮的批次没跑完**。先把「批次编排」和「单方案失败」分开：一次全量迁移是**三队列串行 + 批内并发**（配置表 → 主表 → 子表），队列没跑完就整体结束，后续方案永远停在初始状态。

```text
[迁移事件] 收到全量迁移事件
[迁移任务] 全量迁移开始，共 N 个启用的方案需要迁移
[迁移任务] 配置表方案数量: a, 主表方案数量: b, 子表方案数量: c
  ↓ 先并发「准备方案」：[迁移事件] 全量迁移 - 准备方案: planCode=…, executeOrder=…, taskId=…
  ↓ 队列 1 配置表 → [迁移任务] 开始处理配置表队列 → 线程 N 开始处理配置表: planCode=…
  ↓ 队列 2 主表   → [迁移任务] 开始处理主表队列
  ↓ 队列 3 子表   → [迁移任务] 开始处理子表队列
```

关键判据：**三个队列启动 marker 各只有一行，缺哪个就是该队列从未启动**——不是「失败」也不是「卡住」，是前面的队列还没跑完。只有 `开始处理配置表队列`/`开始处理主表队列` 而没有子表那一行时，全部子表方案连执行阶段都没进，`statuss` 会一直停在「准备中」、`jindu=0`，而 `is_on=1` 表示它仍挂着未收尾。

**用户看到的「一直在准备中」还可能来自前端轮询残留任务**，不是新调度没触发：日志里 `http-nio-*-exec-*` 线程上的 `[进度获取] 获取进度: 任务ID=migration:<planCode>:<epochMs>` 就是页面在拉旧任务的进度。注意区分线程池：`pool-30-*` 准备方案、`pool-31-*` 执行方案、`pool-44-*` 报进度、`http-nio-*` 是页面在轮询。

残留识别 SQL（`<epochMs>` 从任一 `task_id` 尾部取，即该批次时刻的 epoch 毫秒）：

```sql
-- 谁还挂着：is_on=1 且 statuss 非成功就是上一轮的残局
SELECT plan_name, source_table, target_table, statuss, jindu, execute_order, is_config_table, task_id, update_time
FROM <app_db>.migration_<plan_metadataId> WHERE is_on=1 ORDER BY statuss, execute_order;
-- 本轮的账：按 statuss 计数（成功/失败/准备中/运行）
SELECT statuss, COUNT(*) FROM <app_db>.migration_<plan_metadataId>
WHERE task_id LIKE 'migration:%:<epochMs>%' GROUP BY statuss;
-- 卡在中间的那个：0<jindu<100 且 statuss='运行'
SELECT plan_name, source_table, target_table, jindu, task_id
FROM <app_db>.migration_<plan_metadataId> WHERE statuss='运行';
-- 同一源表是否被换过目标表（前后两次结果不可混谈）
SELECT plan_name, source_table, target_table, statuss, jindu, create_time, update_time
FROM <app_db>.migration_<plan_metadataId> WHERE source_table='<源表名>' ORDER BY update_time;
```

批次被打断的机制**必须逐个排除，不能默认是 OOM**。同一组现象（堆水位日志 + `exitCode: 137` + `退出master节点`）至少有三个来源：**滚动发布替换 pod、节点驱逐、JVM/内核 OOM**，而运维环境里**滚动发布是最常见的那个**——先把这条排除掉再谈内存。判读纪律：

- `137` 只是 `128+SIGKILL`，**谁发的信号都长这样**，它不能证明内存。`lastState.terminated.reason` 是 `OOMKilled` 才是内核判定；写着 `Error` 就已经不是 OOM。
- 三项必查：`kubectl get events -A --field-selector reason=OOMKilling`（0 行即排除内核 OOM）、`kubectl get events -A | grep -iE 'evict|memorypressure'`（0 行即排除驱逐）、`deploy` 的 `strategy.rollingUpdate`（`maxSurge`/`maxUnavailable` 非 0 + `imagePullPolicy: Always` + `annotations.deployment.kubernetes.io/revision` 很大 = 高频发版，滚更杀 pod 是首选解释）。被杀与重启的时间线也要对：滚动发布是「旧 pod 被杀 → 新 RS 起新 pod」，而进程崩溃是「同一 pod 内 restartCount 自增」。
- **堆水位日志是应用自报的 gauge，不是崩溃原因**：`[内存监控] 内存使用率过高: 9x%, 已用: <X>MB, 最大: <Y>MB, 进行清理` 的下一动作是「清理」，它只说明当时忙、GC 压力大。
- 启动参数带 `-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=<dir>` 时，**真 OOM 会留下 hprof**——去那个目录看，不存在或没有 hprof 就是**没发生过 JVM OOM 的直接反证**。注意容器启动命令常按发版重新生成（`echo java … -XX:HeapDumpPath=…<时间戳>… > start.sh && ./start.sh`），路径带时间戳却从不建目录是模板陈旧，不是证据。
- 只有三项都排除、且 `used/max` 逼近上限时，才写「内存为最强嫌疑」；再对照 `resources.limits.memory` 与日志「最大」（= `-Xmx`），堆上限远低于容器 limit 时先给「调堆」而不是「调 limit」。给用户的修复方向也要跟着改：滚更打断 ⇒ 迁移窗口避开发版窗口 / 让迁移可断点续跑，而不是「调大内存」。落库核对照第 3 节用 `batch_id` 精确计数——**「目标表已有一大半本次批次的行」与「方案状态仍是运行」可以同时成立**（写入是分批提交的），别用方案状态反推落库量。

修复方向（属写操作，先让用户确认）：调小单方案 `batch_size` / 调小队列并发线程数 / 在 limit 允许范围内调大 JVM 堆 / 百万级大表方案单独错峰跑 / **重跑前必须先收尾残留**（把 `statuss` 非成功的 `is_on=1` 方案复位），否则新旧两轮混在一起无法判读。

### 目标表结构不满足迁移要求（`Unknown column 'batch_id'`）

平台生成的 INSERT **显式**带 `batch_id`（多数表还带 `business_id`），所以目标表必须有这一列。缺列时每个批次都失败，并升级到整轮终止：

```text
[迁移错误] <源表> - 配置错误：批量新增失败，可能是字段映射配置错误。错误信息: PreparedStatementCallback; bad SQL grammar [INSERT INTO <目标表> (…, batch_id, …)]
[全量迁移-多线程] 批次 N 处理失败，可能是字段映射配置错误
[全量迁移-多线程] 批次处理失败，立即中断所有任务 → 配置错误，立即终止迁移
[数据迁移] 迁移任务异常: table=…, taskId=…, error=Unknown column 'batch_id' in 'field list'   ← 最外层放大器
[迁移事件] 方案执行失败, planCode=…, error=…                                                    ← statuss 转「失败」，jindu 停在 25 左右
```

**`Unknown column` 是结构问题，不是数据问题**：换数据、重跑、改映射行都不会好。报错 INSERT 的列清单和目标表实际列一比对即可证实（`information_schema.columns` 按 `ordinal_position` 取全列）。两个必须写进报告的判别点：

- **「表里没有 batch_id」本身不是缺陷**（UDC 实体默认不建这列），只有被选作迁移目标时才必须补；同一实体常并存「有 batch_id」和「没有」两张历史表，**换回结构正确的那张目标表**是最省事的修法。
- **不要直接 `ALTER TABLE` 补列**：物理表是按元数据生成的，要动就改 UDC 实体定义并重新发布，否则物理列有了、实体元数据还是旧的。

另一高频陷阱是**中途换目标表**：方案记录里同一 `source_table` 出现两条、`target_table` 不同（一张有 batch_id、一张没有）时，前后两次运行的结果不可混谈——老 `task_id`/落库行属于旧目标表，报错属于新目标表，按目标表分别下结论。

取证配方见 `references/platform-data-migration-verification.md` 第 8、9 节。

## Reference

只读取证脚本一律落盘到 scratch 目录再执行（`write_file` 写 `.py` → `uv run --no-project --with pymysql python <path>`），不要用 `python - <<'PY'` heredoc：超过一分钟未获确认会被平台拦下（BLOCKED），且长脚本无法逐步修正。查询按「一次拉全列、Python 里聚合」写，不要用相关子查询逐表统计（跨上百张表必超时）。

本技能的会话级证据与复现摘要见 `references/test2-invoice-pool-diagnostics.md`。该文件只记录可复用的诊断事实，不保存凭据。

平台数据迁移（迁移方案）核验的命令、SQL 与对账骨架见 `references/platform-data-migration-verification.md`。第 8 节是应用 pod 文件日志取证（`kubectl logs` 为空时的唯一取证面），第 9 节是批次编排、残局识别与批次被 OOM 打断的判读。

字段「引用表 → 枚举」改造的语义判定 SQL、代码扫描分组与清单骨架见 `references/field-semantics-and-enum-conversion.md`。

## UDC runtime / generated application discovery

当任务涉及低代码应用生成机制时，必须把以下层次分开取证：

```text
UDC 设计态 → 生成物（前端/后端）→ UDC 运行态 → 数据库/Redis
```

优先从用户提供的 UDC jar、反编译 class、应用 Controller、Nacos 和运行态表取得 FACT；SPI 调用链另按 `seeyon-v8-spi` 的 Contract First 规则核对。版本适配以 artifact/version/sha256 为单位，不把 5.3 某个版本的行为直接外推到所有版本。


- [ ] 环境、namespace、Nacos tenant/group/dataId 明确；
- [ ] DTO、底层实体、物理表三层已分开；
- [ ] 真实路由来自 Controller 注解或运行请求，不是猜测；
- [ ] 配置键和值来自运行配置读取；
- [ ] 写入后对同一目标完成回读；
- [ ] SQL schema 与实体元数据分别验证；
- [ ] 日志 traceId 与数据库快照对应；
- [ ] 未把 HTTP 200、`true` 或登录跳转误报为业务成功；
- [ ] 未泄露凭据。
