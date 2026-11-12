---
name: seeyon-field-semantics-migration
description: Use when a Seeyon low-code 关联字段 converts to 枚举.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [windows, macos, linux]
metadata:
  hermes:
    tags: [seeyon, udc, low-code, enum, metadata, migration, mysql]
    related_skills: [seeyon-udc-runtime, seeyon-low-code-environment]
---

# 字段语义迁移（关联配置表 id → 枚举）

当事务型字段当前存的是「另一张配置表的主键」（币种、税率、费率、区域、账期…），用户要求改为「枚举项 id」时使用本 skill。改完不是改字段类型就完了：所有要拿汇率/费率、拿编码、拿名称的地方都必须经枚举转化，所以交付物是**改造点清单 + 数据迁移方案**。

环境连接、凭据边界用 `seeyon-low-code-environment`；UDC 元数据/运行态证据规则用 `seeyon-udc-runtime`；本 skill 只管这类改造的取证顺序、范围界定和产出格式。SQL 配方与清单模板见 `references/field-semantics-migration.md`；平台层字段类型切换的字节码事实（物理类型矩阵、类型转换器白名单、运行态解析规则）见 `references/field-type-change-mechanics.md`——**动手改方案前先读它**，平台的静默失效点都在那里。

## 核心原则：先定链，再扩面

范围以「主表 → 其子表」的归属确定：**只有引用到该主表/子表服务、实体或 DTO 的代码才算同一条链**。字段名相同但落在其他单据业务表上的字段，必须显式排除，并在报告里单列「同名但不同链，本次不动」。

- 收敛范围用子表服务名/实体名/DTO 名 grep；**不要用字段名 grep**——字段名（bizhong、shuilv、currency…）一定会命中无关模块，清单越界后用户会直接判定你找错表。
- 用户说「用到主表的地方才会用到明细」时，就是要求按主表使用点收口，不要按字段名铺开。
- 注入的变量名常是历史遗留且误导（名字像 A 表服务、类型实为 B 子表服务）。角色按注入类型判断，不按变量名；发现的误导命名要单独提示，这是后续误改的源头。

## 取证顺序

1. **物理表先探名。** 低代码物理表带 GUID 后缀（`xxx_<数字>`），用 `SHOW TABLES LIKE '%xxx%'` 探真实表名，不要用元数据实体名拼表名。
2. **元数据定字段类型。** 元数据 schema：UAT=`udc`、`udc_uat`、test2=`udc_test2`；表 `udc_entity`(name/caption/table_name/app_id) 与 `udc_attribute`(name/caption/db_column_name/data_type/relation_entity/relation_code/app_id)，按 `app_id` 过滤。判定只看 `data_type`：`CTPENUM` = 已是枚举；`ENTITY` = 仍关联实体。**不要用 `relation_code` 是否为空来反推**——CTPENUM 的 `relation_code` 可能为空或残留旧值，运行态根本不读它（见 `references/field-type-change-mechanics.md`）。
   - 元数据可能只存在于某一个环境（另一环境缺该实体、或已改成枚举），必须分环境取证，不从一个环境推断另一个环境。
   - `udc_entity` 没有 `code` 列，用 name/caption/table_name；猜列名会白跑几轮。
3. **枚举取值只查 `ctp_enum_item`。** 它自带 `enum_code`，不要 join `ctp_enum`；`item_value`=码值（对外编码，可能是 ISO 码也可能是 `1`/`5` 这种序号），`name`=中文名，`id`=落库值。业务里常并存多套相似枚举（如标准币种码 vs 签约币种序号），先确认用哪一枚再动代码。
4. **实测数据分布。** 子表字段 JOIN 配置表，确认命中率、有多少个不同配置 id、折叠后剩几个枚举值；命中率不足说明存在脏值，要单列。
5. **迁移映射要能自证。** 找关联目标表里**本身已是同一枚举 id** 的列作为映射桥（配置表常自带一个已枚举化的类型/币种列），由此推出可 JOIN 的刷数 SQL；再用子表里已存的文本快照列与枚举码值做一致性校验（不一致或为 NULL 的行要列出）。
6. **先算折叠后的唯一性。** 关联记录是「每条配置一行」，折成枚举后是「每个枚举值一行」：统计 `(父id, 枚举id)` 折叠后的重复组数并给出示例父 id，把去重规则（保留哪条）交给用户拍板，**不要默认去重**。
7. **语义变化必须显式提示。** 原字段锁定「某一条具体配置记录」（当时的汇率/费率快照），改后只能「按枚举值 + 生效日期动态取」：历史单据取值会随日期变化，需用户拍板是否保留快照字段。

## 平台机制：切换类型不是 DDL 变更，是运行态解析变更

**ENTITY → CTPENUM 不改变物理列类型。** 字节码实测：`EntityDataType` 与 `CtpEnumDataType` 的 `getDatabaseType()` 都返回 `-5`（BIGINT）、`getJavaType()` 都是 `Long`，多选时都返回 `2011`（NCLOB）+ `String`。所以：

- **没有 DDL diff，就不会有平台侧数据迁移，也不会报错**——存量值在改完后**静默失效**（显示为空或错值，但没有异常、没有 error 日志）。刷数不是「顺手办」，而是**必须显式 UPDATE**。
- `com/seeyon/udc/common/datatype/convert/` 下 22 个 `@TypeMapping` 里**没有 ENTITY → CTPENUM 转换器**（涉及 CTPENUM 的只有 `StringToLong`，且 `isFormulaResult=true`，属公式求值不是字段迁移）。不要指望平台帮你转值。
- 别把「自定义枚举 → varchar」当成本场景的 DDL 结论：那条对应的是 `EnumDataType`（选项集，`getDatabaseType()=12` VARCHAR），与 `CtpEnumDataType`（CTPENUM）是两种东西。写方案前先确认字段到底是选项集还是 CTPENUM。
- 运行态把 CTPENUM 的 `relationEntity` **硬编码覆盖**为 `CtpEnumItem`，再按 id 查显示名（`UdcEntityLogService`）。因此落库值**必须是枚举项 id**，否则显示名永远查不到——这是刷数映射的唯一正确目标。
- 设计态 `CtpEnumDataType.check()` 只要求 `relationEntity` 非空，`EntityDataType.check()` 额外要求 `relationType` 非 `NONE` 且 `relationApp`/`relationEntity` 非空。**同一个字段在两态语义不同**：设计态当占位、运行态被覆盖。所以「切完没报错」不代表切对了。
- `CtpEnumDataType` 不支持 `sensitive`/`encryption`/`lengthRange`/`maxAndMin`/`decimalDigits`/`pattern`（字节码 `return false`）。切换前先确认原字段有没有在用这些配置，**尤其脱敏和加密**——切完是静默失效，属合规风险，要单独提。

## 产出物

改造点清单（表格，按「读该字段拿什么」分类：拿汇率/费率、拿编码、拿名称、仅传递），每行：`位置（文件:行）`、`用途`、`现状实现`、`改造后实现`。清单必须包含：

- 数据实测结论（行数、命中数、折叠后分布、重复组、脏值）
- 排除项（同名但不同链的表/文件，说明为什么排除）
- 待用户拍板的口径（用哪枚枚举；存枚举 id 还是码值；是否保留快照字段；对外展示中文名还是码值）
- 顺带挖出的自相矛盾（同一字段两种解析、枚举 id 写进关联字段、内部主键对外输出）单列一节

命令行环境下用等宽对齐的纯文本列，**不要用 markdown 表格**（CLI 不渲染，行会对不上）。

改造顺序：公共工具类（被全仓复用的取值入口，先改）→ 主表/子表导入导出（反查 id 的方法；「找不到返回 `0L`/`0`」这类返回值必须去掉——导入侧空值/未知值直接抛业务异常并报出父级名称与实际填的值，不要静默写 0 或 null）→ 计算/落库调用方（传参语义从配置 id 变枚举 id）→ 对外接口输出。改一处跑一次。

## 改造落地（代码侧）

1. **导出**：不再 `selectById(字段值)` 查配置表取名称列，改为枚举服务 `selectById(字段值)` 取展示名；名称取不到退化为 `item_value`（码值）。原来的「币种不存在或过期」文案改成「为空或枚举已失效，请检查 <枚举编码> 枚举配置」。
2. **导入**：文本 → 枚举 id 的反查要**同时吃枚举名称与码值**（先按码值、忽略大小写，再按名称），否则新导出的模板能回灌、老模板整批报错；匹配循环里 `item_value`/`name` 都可能为 null，比较前判空，取值走工程的 i18n 方法（如 `DataI18nUtils.getCurrentLocaleStr`）。
3. **删除旧反查**：按「名称 + 生效时间区间」查配置表拿 id 的老方法整段删掉；只为它存在的注入服务、import 一起删，别把死依赖留在 diff 里。
4. **枚举编码提常量**：`private static final String XXX_ENUM_CODE = "<枚举编码>"`，不要在方法里散落字面量。
5. **公共取值入口**：把「码值 + 生效日期 → 唯一一条配置」抽成公共工具方法（命中条件必须是 `开始时间 <= 业务日期 <= 结束时间`，日期为空取当前时间，多条命中打 warning），并让既有私有实现改为委托它（等价重构、零行为变化），新调用方一行接上。
6. **不顺手改语义**：计算入口的传参语义变更（例如由「按申请日期选中的那条配置 id」改成「码值 + 当前时间」）会让历史单据取值漂移，只列入待拍板，不擅自改；公共方法备好并说明「一行就能接」即可。
7. **误导性命名一并修**：注入变量名与实际类型不符的（子表服务却叫配置表服务名）在本次改造中改名并同步全部使用点——改名是防后续误改，不是纯洁癖。

**多选枚举的 Java 类型不变**：UDC 多选枚举字段仍是 `String`，存「枚举项 id 逗号分隔串」（如 `1001,1002`），不会像单选枚举那样变成 `Long`。因此：

- 导出/模板：id 串 → 名称串，逐个取枚举展示名、逗号拼接；单个值解析不到名称时**按原值输出 + 打 WARN**，不要抛异常（一个脏值不该让整表导出失败）。
- 导入：名称串 → id 串，按分隔符切分（同时吃半角 `,` 与全角 `，`）、逐个 trim、按 `name` 匹配（可再用 `item_value` 忽略大小写兜底），拼回时按入参顺序去重；匹配不到的名称直接抛业务异常，并把该枚举的全部可选值列进错误信息。
- 单选/多选必须问用户或查元数据的多选标记，不要按「字段是 Long」反推单选——写错会白改一轮，单选版会编译报 `incompatible types: String cannot be converted to Long`。

改完**必须做编译验证**，不能以「看代码没问题」收尾：这类工程常没有可用的 mvn/mvnw，用 `references/offline-javac-verification.md` 的全源码 javac 配方（脚本 `scripts/build_javac_args.py`）拿到 0 error 才算验证通过。

汇报格式（用户会直接 review）：改了什么（文件 + 行号 + 每处意图）、验证证据（命令 + error 数 + 产物）、平台侧待办（元数据改没改、历史数据刷没刷）、以及**明确列出故意没改的项和原因**（语义待拍板的部分）。不要只说「改好了」。

## Pitfalls

- 用字段名 grep 划范围 = 清单越界；用子表服务/实体/DTO 名 grep 才会收敛到同一条链。
- 关联字段转枚举会改变唯一性：不去重就出现「同一父、同一枚举值两行」，方案里必须带重复组统计。
- 导入回填方法返回 `0L` 而不是 `null`，转枚举后会往子表写 0；改字段类型时必须一起改。
- 用户报「导入/运行时报了某个错」时先归因再改：把异常栈对回源码行号，判断是本次改造引入的（REGRESSION）还是老代码路径本来就有的隐患，汇报里必须分开写。把老 BUG 讲成改造副作用、或反过来默认自己的改动有问题，都会让用户不再相信你的证据。定位到与本次改造无关时，给出证据（行号 + 是哪几行数据触发的）并顺手修掉——用户要的是导入成功，不是责任划分。
- 改造期间用户会拿真实 xlsx 试导入：先用 `seeyon-excel-import-export-migration` 的 `references/import-data-preflight.md` 做数据自检（导出的模板要能回灌、老模板也要能回灌），一次报齐所有会被拒的行，数据问题和代码问题分开列。
- 元数据只在一个环境有该实体时，别把该环境结论当两环境的共同事实。
- 文本快照列（如「币种文本」）常与目标枚举码值同义，是最省事的迁移校验手段，不要只盯着 bigint 列。
- 枚举项的 `item_value`/`name` 可能为 null，匹配循环必须先判空再比较，否则直接 NPE。
- 只改代码不查元数据等于没改：`Data_type` 没转成 `CTPENUM` + 正确 `relation_code` 时，运行期取到的仍是老的关联值；元数据改动属平台侧待办，必须在汇报里点名。
- 交付前没跑编译验证：这类工程没有 mvn 命令行，很容易以「肉眼看着没问题」收尾；用 `references/offline-javac-verification.md` 的配方拿到 0 error。
- 把「字段类型变了所以库表也变了」当默认前提。ENTITY→CTPENUM 物理列类型不变，**没有 DDL diff 就没有任何平台侧自动迁移**；报告里必须写明刷数是手工步骤，并给出刷数 SQL，否则交付等于没迁。
- 只凭文档（数据字典/数据库规范/元数据判定式）下类型结论。文档会与字节码冲突（选项集 varchar vs CTPENUM bigint 就是实例）；字段类型类结论优先取 `udc-common` 反编译的 `getDatabaseType()`/`getJavaType()` 常量，文档只作旁证。
- 设计态保存逻辑在 `udc-biz`/`udc-web`，本地 CHIT 仓库常缺这两个 artifact。取证走「本地能拿到的契约层 + 运行态」，`udc-common`（数据类型体系）与 `udc-starter-runtime`（运行态解析）通常有 5.3.517，够支撑类型矩阵和运行态规则；拿不到的层在报告里标 UNVERIFIED，不要用知识库源码快照冒充字节码证据。
