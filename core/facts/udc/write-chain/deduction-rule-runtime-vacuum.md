# 扣减规则运行态 —— VACUUM 负证据 + 设计态契约闭合（B-2 收口，D5 口径）

> 环境：test2（`lowcode-test2.example.com`），租户 `-8112660841495312922`
> 目标应用：`datamigration9000000000000000001`
> 扣减规则：`xzhDedRule`（caption 小爪扣减规则），id `-2339240514292888379`
> 收口口径：main D5 —— **设计态契约闭合 + 运行态 VACUUM 负证据**（不是"已触发"，也不是"未做"）
> 独立复核：`auditor/B2-PRE-AUDIT-20261018.md`（DB 侧）+ `auditor/B2-REVIEW-FEEDBACK-20261018.md`（字节码侧，判 PARTIAL 并订正机制）
> 本文取代此前 `docs/audit/artifacts/udc-node-evidence/b2-runtime-trigger-BLOCKED.md` 的"BLOCKED"表述为主口径
> **v2（2026-10-18 02:50）**：按 auditor REVIEW_FEEDBACK 订正 —— 末次成功构建时刻（19:29:35）、§2 标题、补两个 UPDATE 入口。
> **v3（2026-10-18 03:30）**：按 auditor SELF-CORRECTION **作废「INSERT 环」**。反射通用 INSERT 通路确实存在
> （`JsonDataInitializer` → `allInOneDaoService.createBatch`，不经过 DAO，DAO 级 grep 扫不到）。
> 真实阻断机制改为：**构建产物从未包含扣减 datainit json**。解锁=让工件带上该 json 后重发（datainit 会 INSERT），
> 或人工/工具造首行（二者皆可）。
> 参考：`auditor/B2-SELF-CORRECTION-20261018.md`
> **v4（2026-10-18 03:10）**：B-2 v3 获 auditor VERDICT = **PASS**。本轮补两条：
> ①全实例 `app_starter_init_detail` 普查（114 schema / 6193 行 / 含 `@` = **0**）——决定性证据，覆盖面从"本应用"升到"全实例"；
> ②修正 v3 一处断言层级：「构建没生成」只能到 **UNVERIFIED**（DB 只记已执行，不记是否生成）；
> ③B-4 判据升级为三步（auditor 补第 2 步，防"工件看不到但确实执行过"误判）。

---

## 0. 结论

| 维度 | 判定 | 证据等级 |
|---|---|---|
| 扣减规则**设计态契约** | **闭合**（规则 / 算法 / 映射 三层字段与生成机制齐备） | LIVE + STATIC |
| 扣减规则**运行态可验证性** | **VACUUM**（全实例 66~69 schema 穷举 0 行，无任何可比对样本） | LIVE（穷举，非抽样） |
| 本次运行态"触发 + DB 回读" | **不成立**（结构性前提缺失，非 SSO、非实现失败） | LIVE |
| 运行态首行来源 | **理论有来源**：存在反射通用 INSERT 通路（`init/tenant/<app>@<实体FQCN>.json` → `createBatch`） | STATIC（字节码，已复核） |
| 实际为何 0 行 | **构建产物从未包含扣减 datainit json**（jar 内 `init/tenant` 条目=0 / 全仓 29 个 5.3.5xx jar 全 0 / `app_starter_init_detail` 192 行 file_name 无 deduction / `metadata_schema` 405KB 不含 `DeductionRt`） | LIVE（穷举+回读） |
| 写操作 | **0 次**（D4 一次写授权按 D5 作废，未执行） | — |

**因果链（订正后，v3）**

```
10-13 11:29:59  成功构建 (type=2, jar 1.0.7)
10-15 15:32:38  成功构建 (type=3, jar 1.0.7)   show_version=1.0.7
10-15 19:29:35  成功构建 (type=2, jar 1.0.14)  ← 末次成功，此前文档漏记
10-15 22:17:10  扣减规则 + 算法创建            ← 晚于末次成功构建，从未被任何成功构建带走
10-17 22:56:06  发布 FAIL（一致性检测未通过）
10-17 23:43:05  发布 FAIL（NFE：实体全限定名被当数字解析）
```

**直接因果** = 「扣减规则创建时间晚于最后一次成功构建」⇒ 规则从未进过任何构建产物 ⇒ 运行态不可能有它。
「发布全 FAIL」只是**相关**论据（失败≠一定无行，历史上也可能残留旧行），不能单独支撑结论。
**更强的一条（v3 订正）** = 构建产物从未包含扣减 datainit json（§2.3(d2)），
所以 datainit 的反射 INSERT 通路从未被触发 —— 这才是 0 行的直接机制。
（v2 曾写「INSERT 环 / 首行无来源」，已被 auditor 自我订正推翻，见本文头部 v3 说明。）

---

## 1. 运行态 VACUUM（LIVE，穷举）

### 1.1 全实例表级穷举

复现脚本：`<HERMES_HOME>\cache\scratch\b2_evidence.py`（只读，约 8s）
产物：`docs/audit/artifacts/udc-node-evidence/b2-runtime-trigger-blocker.json` 的 `rt_census`

```sql
SELECT table_schema FROM information_schema.tables WHERE table_name='udc_rt_deduction_rule';
-- 66 个 schema 命中，逐 schema：
SELECT COUNT(*) FROM `<schema>`.udc_rt_deduction_rule;
SELECT COUNT(*) FROM `<schema>`.udc_rt_deduction_rule_detail;
SELECT COUNT(*) FROM `<schema>`.udc_rt_deduction_log;
```

| 表 | 有该表的 schema 数 | 非空 schema 数 | 合计行数 |
|---|---|---|---|
| `udc_rt_deduction_rule` | **66** | **0** | **0** |
| `udc_rt_deduction_rule_detail` | 66 | 0 | 0 |
| `udc_rt_deduction_log` | 69 | 0 | 0 |
| `udc_rt_deduction_map` / `_algorithm` | 66 | 0 | 0 |
| `udc_deduction_id_mapping` | 66 | 0 | 0 |

三库（`udc` / `udc_test2` / `udc_uat`）运行态五表同样全 0（产物 `rt_by_schema_3`）。
本应用 schema `datamigration9000000000000000002_test2` 内 12 张运行态相关表逐表 0 行。

**含义**：test2 实例内**任何应用**从未产生过一行扣减运行态数据。该域在实例层面无对照样本 → 判定 VACUUM（完备负证据），不是"本次没取到"。

### 1.2 三层结构性前提（任一独立成立即阻断）

| # | 事实 | 查询 | 结果 |
|---|---|---|---|
| L3 | 扣减图是空壳 | `SELECT definition, source_entity_id FROM udc_deduction_map WHERE id=-3894187973392826420` | `definition=NULL`、`source_entity_id=NULL`；全实例 `udc_deduction_map` total=1，definition 非空 **0** |
| L4 | 规则晚于末次成功构建 | 比对 `udc_deduction_rule.create_time` vs `udc_deploy_record` **state=1 全部行** | 规则/算法 `2026-10-15 22:17:10` > 末次成功构建 `2026-10-15 19:29:35`（type=2, jar 1.0.14）→ **从未被任何成功构建带走**（三条成功构建见下） |
| L7 | 源实体无数据 | `SELECT COUNT(*) FROM datamigration9000000000000000002_test2.xzhexp950_m1719416608666233204` | **0**；`search_condition` 为 `expText EQUAL expText`（自身对自身），无源记录可匹配 |

补充：`udc_deduction_rule_detail` 全实例 0 行（与 c2004ff 一致，此处独立复核成立）——无明细行即无算法绑定落库。

### 1.3 发布链路当前为红

**全部 state=1（成功）记录，共 3 条**（v2 订正：此前只写 15:32，漏记 19:29:35）：

| # | 时间 | deploy_type | jar | msg |
|---|---|---|---|---|
| 1 | 2026-10-13 11:29:59 | 2 | 1.0.7 | 内部流水线构建成功 |
| 2 | 2026-10-15 15:32:38 | 3 | 1.0.7 | 内部流水线构建成功（`udc_app_version.show_version=1.0.7`, state=1） |
| 3 | **2026-10-15 19:29:35** | **2** | **1.0.14** | 内部流水线构建成功 ← **末次成功** |

**失败记录**：

| 时间 | state | msg |
|---|---|---|
| 2026-10-17 22:56:06 | 2 FAIL | `业务异常[一致性检测未通过] … AbstractDeployService` |
| 2026-10-17 23:43:05 | 2 FAIL | `NumberFormatException: For input string: "com.seeyon.datamigration9000000000000000001.domain.entity.XzhExp950795"` |

`deploy_type` 分布（本应用）：type=2 共 20 条（2 成功 / 18 失败）、type=3 共 1 条（1 成功）。
`udc_app_version` 仅 1 条 state=1（15:32:38 / 1.0.7）—— 该表不记录 19:29:35 那次 type=2 构建，故**不能只凭 `udc_app_version` 判断末次成功**。

---

## 2. 设计态契约闭合（LIVE + STATIC）

### 2.1 四层数据模型（LIVE，DB 回读）

```
udc_deduction_map (id=-3894187973392826420, caption='1', definition=NULL)   ← 空壳
      ↑ deduction_map_id
udc_deduction_rule (id=-2339240514292888379, name=xzhDedRule, publish_state=1)
      ├─ search_condition : [{"searchMethod":"EQUAL","target/source": XzhExp950795.expText, "uuid":"sc-1"}]
      ├─ extend_info      : {"conditionExt":{"dataNotFoundStrategy":"ERROR","toast":""}}
      └─ id ─ deduction_rule_id ─> udc_deduction_rule_detail  (0 行，机制性)
                                        └─ deduction_algorithm_id
                                   udc_deduction_algorithm (id=2173732574526581210,
                                                            operatorEnum=SUBTRACT_EQUAL, expNum)
```

### 2.2 明细 0 行的机制原因（STATIC，c2004ff 已闭合，此处引用不重做）

`BillStatusOfJavaEnumRuleDetailServiceImpl.match` 触发条件：
`stereotype == 'bill'` **且** 存在 `name=='statusType' && dataType==ENUM` 的属性。
本应用 9 个实体全部 `stereotype=standard`（LIVE：`udc_entity.app_id=9000000000000000002` 9 行全 standard），
且无 `statusType` ENUM 属性 → **明细必然 0 行**，属机制而非数据缺失。

### 2.3 运行态写入入口（STATIC）—— DAO 层唯一 INSERT 是 `saveRuleNewVersion`，另有两条 UPDATE + 一条反射通用 INSERT

> **v2 订正**：此前标题写「唯一写入入口是 `saveRuleNewVersion`」，与字节码矛盾。正确表述如下（auditor 反编译同源 jar 指出，我已独立复跑确认）。

反编译产物：`<HERMES_HOME>\cache\scratch\aud\cfr-b2-upgrade\`（源 jar `udc-starter-dataflow-5.3.517.jar`）

#### (a) DAO 层 INSERT 入口：`DeductionRtRuleService.saveRuleNewVersion`

| 行 | 事实 |
|---|---|
| L365–366 | 先 `deductionRtRuleDao.selectById(id)`，取不到直接 `Assert.notNull` 抛「未查询到数据」（L358–406 全文无 fallback 分支） |
| L370–374 | 取到后 `Ids.gidLong()` 新 id + `setStartState(OFF)` + `setVersionNumber(+1)` + `create()` |
| L435–458 | `enableRule(Long)` 入参即**运行态** rule id，先 `selectById` 读 `startState`，同版本才切 `ON/OFF` |

**DAO 层穷举**（我独立复跑）——**注意：DAO 级 grep 不能证明「唯一 INSERT」**，见 (d)：

```bash
grep -rnE 'Rt[A-Za-z]*Dao\.(create|createBatch)' <cfr-out>
# 对扣减运行态规则表仅命中一处：
# DeductionRtRuleService.java:374  this.deductionRtRuleDao.create(...)
# （另 385/399 是 algorithm / rule_detail 的 createBatch，不产生 rule 首行）
grep -rn 'deductionRtRuleDao' <cfr-out>
# 其余全部是 select* / updateBatch / updateByWrapperSelective
```

#### (b) UPDATE 入口一：`DeductionDataInitListener`（租户初始化完成事件驱动）

`com/seeyon/boot/starter/deduction/listener/DeductionDataInitListener.java`

| 行 | 事实 |
|---|---|
| L57–59 | `@Component implements AppStartUpProcessor` |
| L61–63 | 数据源 = classpath `init/tenant/<appName>@<DeductionRtRule>.json` / `@<DeductionRtMap>.json` |
| L73–81 | `onCompleteTenantInit(AppInfoDto)`；`stereotype=FORM` 表单应用直接 return |
| L95–98 | `mapJson` 或 `ruleJson` 为空白 → return（无扣减数据则不执行） |
| **L133–140** | **关键**：`wrapper.and().andNotIn("id", ruleIds).and().andEqualTo("appId", appId).and().andEqualTo("startState", ON)` → `updateByWrapperSelective(setAllFieldNullObject + setStartState(OFF))` |

**这个 UPDATE 的语义是「关停」而非「初始化」**：
它把「属于本应用、但**不在** JSON 清单里、当前处于启用态」的运行态规则置为 OFF。
JSON 里列出的规则**不会被写入**，JSON 里没有的行也不会被创建 —— 它既不 INSERT，也不给已存在行赋启用值。

调用方（auditor 追到，我采信其 jar 定位，未独立复跑 lowcode jar）：

```
udc-starter-lowcode-5.3.517.jar
  AppStartUpManager.L87  @EventSubscribe onAfterLocalTenantInitEvent(AfterLocalTenantInitMessage)
  AppStartUpManager.L99  processor.onCompleteTenantInit(appInfoDto)
```

#### (c) UPDATE 入口二：`DeductionUpgradeAppService`（`@Deprecated` 升级接口）

`com/seeyon/boot/starter/deduction/upgrade/DeductionUpgradeAppService.java`

| 行 | 事实 |
|---|---|
| L43–44 | `@AppService("运行态扣减规则升级接口")` |
| L57–59 | `@Deprecated @Transactional upgradeDeductionMapAppId()` |
| L61–62 | 条件 `startState=ON` 且 `appId != NULL_ID` |
| L68–85 | `upgradeDeductionRule`：`updateByWrapperSelective` 回填 `appId`（条件 `originalRuleId=? and (appId is null or appId=-1)`） |
| L87–104 | `upgradeDeductionMap`：同上，针对 map 表 |

HTTP 面：`DeductionRtUpgradeController` → `GET udc-runtime/deduction/upgrade/upgradeDeductionMapAppId`。
用途是**历史数据补 appId**（V8 升级遗留），只在行已存在且有 appId 缺口时有效，**不产首行**。

#### (d) 反射通用 INSERT 通路（v3 新增 —— 推翻「INSERT 环」）

> **v3 订正**：v2 写的「INSERT 环：首行无来源」**作废**。原因是 v2 的穷举方法有漏洞：
> 只 grep 了 `Rt*Dao.create/createBatch` 这类 **DAO 级调用点**，漏掉了**反射通用通路**。

反编译产物：`<HERMES_HOME>\cache\scratch\aud\cfr-datainit\`（源 `boot-starter-datainit-5.3.358.jar`）

`com/seeyon/boot/starter/datainit/service/JsonDataInitializer.java`

| 行 | 事实（我已独立复核） |
|---|---|
| L110–111 | `initAppData(fileName, appName, …)` → `ResourceUtils.getAppClassPathResource(appName, initTenantPath + fileName)` |
| **L201** | `String entityName = getEntityNameFromFileName(fileName)` ← **从文件名反射出实体 FQCN** |
| **L202** | `Class<?> entityClass = Class.forName(entityName)` |
| **L203** | `List entityList = JsonUtils.toList(content, entityClass)` |
| L208 | `doEntityList(...)` |
| **L523** | `this.allInOneDaoService.createBatch(insertCache, entityName, targetAppName)` ← **INSERT** |

`com/seeyon/boot/starter/datainit/service/DefaultDataInitializer.java`
L1201 `ResourceUtils.getAppClassPathResources(appName, INIT_TENANT + "*" + postFix)` ← 扫描 `init/tenant/*`

**这条通路不经过 `DeductionRtRuleDao`**，所以 DAO 级 grep 永远命中不了。
它可以批量 INSERT **任意实体**，包括 `com.seeyon.boot.starter.deduction.domain.entity.DeductionRtRule`。

→ 所以 v2 的推论（首行无来源、发布修好也没用）**前提不成立，结论失效**。

#### (d2) 那为什么实际是 0 行？—— 构建产物里没有这个 json

| 检查 | 结果 | 等级 |
|---|---|---|
| `udc-starter-dataflow-5.3.517.jar` 内 `init/tenant/*` 条目 | **0**（该 jar 只有 `metadata/starter_info.json`） | STATIC |
| 全仓 **29 个** `5.3.5xx` jar 含 `init/tenant` 资源 | **0 个**（逐个 `unzip -l \| grep -c` 实测，全部为 0） | STATIC |
| 全仓**所有版本** jar 含 `init/tenant` | **0 个** | STATIC |
| 本应用 `app_starter_init_detail` | **192 行**，distinct file_name 仅 `ddl.sql`(181) + `dml.sql`(11)；含 `deduction`=0 | LIVE |
| **全实例** `app_starter_init_detail` 普查（决定性） | **114 个 schema / 合计 6193 行 / `file_name LIKE '%@%'`（datainit json 命名特征）= 0 行 / 含 `deduction` = 0 行** | LIVE（穷举） |
| 本应用 `udc_history_metadata`（3 行）`metadata_schema` 含 `DeductionRtRule` | **否**（单行 405 093 字符，全文不含） | LIVE |

→ **正确机制（v4 精确表述）**：本应用构建产物从未包含扣减运行态的 datainit json，
因此 datainit 通路从未 INSERT 过运行态扣减行。
阻断不是"平台没有 INSERT 能力"，而是"**该应用从未执行过 datainit json 形式的初始化**"。

> **v4 修正一处断言层级（auditor 指出，我接受）**：v3 曾写"不是平台缺文件，是**构建没生成**文件"——
> 方向对，但「构建没生成」只能到 **UNVERIFIED**，不能算已证。理由：`app_starter_init_detail`
> 只记录**已执行**的 init；若构建生成了 json 但未执行（版本未变跳过、失败重试前），DB 也不会有记录。
> 所以 DB 侧能证的是「**从未执行过** datainit json 形式的 init」，不能证「从未生成过」。
> 「平台/构建是否具备生成该 json 的能力」= **UNVERIFIED**，留给 B-4 判定。

#### (e) 设计态服务不碰运行态表（STATIC，维持原结论）

`cfr-b2/.../deduction/domain/service/DeductionRuleService.java` 全文**无** `Rt` / `udc_rt_` 引用
（`grep -E "\bRt[A-Z]|deductionRt|udc_rt_|DeductionRt"` 零命中）→ 在设计器保存扣减规则**不**产出运行态行。

### 2.4 平台确有"设计态→运行态"通道（STATIC，反证 VACUUM 是"未搬过"）

`DeductionRtUpgradeController` @RequestMapping `udc-runtime/deduction/upgrade`，
`GET upgradeDeductionMapAppId`（udc-starter-dataflow-5.3.517.jar）。

**v2 订正**：此前本段结论写"从未执行过升级/发布带出"，暗含"发布能带出运行态行"，与 §2.3(d) 矛盾。
正确表述：平台**有**两条通往运行态表的自动通道（init listener / upgrade），但**两条都是 UPDATE**，
作用分别是「关停不在清单内的启用行」与「补写历史行缺失的 appId」，**都不 INSERT**。
→ 全实例 0 行的结论是「从未有任何 INSERT 发生过」，而不是「没跑过发布」。

---

## 3. 本轮 /service 台账（≤3 次/轮，≥30s 间隔；均未计 PASS）

| # | 请求 | HTTP | 响应码 | 判读 |
|---|---|---|---|---|
| 1 | `POST /service/6419954374508955097/udc-runtime/deduction/rule/getAll` | 200 | `server_404` | 凭据 `gateway_prefix` 属他应用，非本应用前缀 |
| 2 | `GET /service/9000000000000000002/udc-runtime/deduction/map/getAll/9000000000000000002` | 200 | `server_404` | appId 不是服务名 |
| 3 | `GET /service/datamigration9000000000000000001/udc-runtime/deduction/map/getAll/9000000000000000002` | 200 | `server_403` | 服务前缀存在，test-account-1 对本应用运行态扣减接口**无权限** |

页面分支：CDP 9226 导航扣减规则设计页 → `alert: 身份认证信息无效，请重新登录` → 落 `/login`。
按 D4/D5 记录后停止，未重试登录（脚本 `scratch/b2_cdp2.py`）。

---

## 4. 结论边界（不得外推）

**可以断言**
- 扣减规则设计态三层契约完整、字段语义明确（§2.1）。
- 明细 0 行是 `stereotype=bill + statusType ENUM` 机制缺省（§2.2）。
- 运行态在 test2 实例层面 VACUUM（§1.1，穷举）。
- 平台存在**反射通用 INSERT 通路**，可从 `init/tenant/<app>@<实体FQCN>.json` 批量 INSERT 任意实体（§2.3(d)，STATIC）。
- **全实例从未执行过 datainit json 形式的 init**：114 个 schema / 6193 行 `app_starter_init_detail`，
  `file_name LIKE '%@%'` = **0**（含 deduction = 0）（§2.3(d2)，LIVE 穷举）。
- 本应用 `udc_history_metadata.metadata_schema`（单行 405KB）不含 `DeductionRtRule`；
  `udc-starter-dataflow` 等 29 个 5.3.5xx **平台 jar** 内 `init/tenant` 条目 = 0（§2.3(d2)）。

**不可断言（明确未取证）**
- 平台/构建设施**是否具备生成** `init/tenant/*DeductionRtRule.json` 的能力（**UNVERIFIED**，B-4 判定）。
  DB 只能证"从未执行过"，不能证"从未生成过"——`app_starter_init_detail` 仅记录已执行的 init。
- 扣减触发后 `udc_rt_deduction_log` 的实际内容与字段填充。
- 扣减结果在业务表上的数值变更（源表 0 行，无从观测）。
- `enableRule` 的两行 `updateBatch` 在真实数据下的行为（无运行态行可切）。

**解除 VACUUM 的必要输入（v3 重写 —— 作废 v2 的「只能造首行」）**

> ⚠️ **v2 写「发布只 UPDATE 不 INSERT，修发布解不了」——这句话被 v3 推翻。**
> 反射通路证明了平台**有** INSERT 能力，缺的是**工件里的 json 文件**。

| # | 路径 | 做法 | 性质 | 可行性 |
|---|---|---|---|---|
| **A** | 修发布 + 工件带 json | ①解 NFE 与一致性检测 → ②让构建产出 `init/tenant/<appName>@com.seeyon.boot.starter.deduction.domain.entity.DeductionRtRule.json`（及 `@DeductionRtMap.json`）→ 重发 → 租户 init 时 datainit **INSERT** | 写（发布） | **可行**，前提是平台构建设施能生成该 json（B-4 待验证） |
| **B1** | 人工造 init json（**独立可行**） | 直接在应用 classpath 放 `init/tenant/<appName>@...DeductionRtRule.json`，再触发租户 init → `JsonDataInitializer` L201-203 反射解析 → **L523 `createBatch` INSERT** | 写（文件 + init） | **可行且独立** —— `JsonDataInitializer` 专为此设计，**不需要**配合任何 "①" |
| **B2** | 直接 INSERT 表 | 不走 datainit，直接 INSERT `udc_rt_deduction_rule` / `_map` / `_algorithm` / `_rule_detail` | 写（超授权） | 可行，但绕过了平台初始化流程，后续 init 可能按其 JSON 清单把行「关停」 |
| C | 走 init listener | `DeductionDataInitListener` 只 UPDATE（语义=关停，见 §2.3(b)） | — | **不可行**（不产行） |

> **B1 vs B2 的区别（v4 修正 —— auditor 指出我漏了两个前置，其中一个让结论方向反转）**
>
> B1 走平台正规初始化通路，产出的行会被 `DeductionDataInitListener` 认为在清单内而保留；
> B2 直插的行不在任何 init JSON 清单里。
>
> **关停逻辑的完整触发条件（四个前置，缺一不触发）**：
>
> | # | 前置 | 出处 |
> |---|---|---|
> | ① | 应用不是 `FORM` 类型（表单应用整条链路 return） | L75–78 |
> | ② | **`mapJsonString` 与 `ruleJsonString` 双双非空**（任一 blank 直接 return，`initRule` 根本不被调用） | L95–98 |
> | ③ | init JSON 清单非空 | L129–131 |
> | ④ | 目标行处于 `startState=ON` | L139 |
>
> **分场景结论（关键，v3 写错了方向）**：
>
> - **应用当前无 init/tenant json（= 本应用现状）**：`ruleJsonString` blank → L95–98 直接 return
>   → `initRule` **永不执行** → **B2 直插的行不会被关停，安全**。
> - 应用后来补了 json 并重跑 init → 才会被关停。
> - B1 造 json 后重跑 → 行在清单内 → 保留。
>
> → 精确表述：**「B2 会被关停」的前提是该应用存在 `init/tenant` 的 map+rule 双 json 且后续重跑 init**；
> 若应用始终无该 json（本应用现状），关停逻辑不触发，**B2 无此风险**。
> B-4 选路含义：若在 zzprobe 走 B2 直插且不打算给 zzprobe 造 init json，则 B2 没有关停风险。
> （STATIC 依据 L73–141，推断非实测）

A / B1 / B2 任一成功后仍需：补 `udc_deduction_map.definition`（空壳图）、补明细行、源实体落 ≥1 行、`enableRule` 启用并触发回读。

**B-4 判据（v4 三步版，采纳 auditor 分层 + 其补的第 2 步）**

前提认知：查**应用工件**，不是平台 jar。平台 jar 已证 `init/tenant`=0，且**本来就不该有**
（datainit 扫的是 `getAppClassPathResources(appName,'init/tenant/*')`，是应用级路径）。

| 步 | 动作 | 判定 |
|---|---|---|
| 1 | zzprobe 构建后，取**该应用工件** `unzip -l \| grep init/tenant` | **有** → 平台具备生成能力，A 路可行，B-2 的 VACUUM 可解 |
| 2 | 查 zzprobe schema 的 `app_starter_init_detail` 有无 `file_name LIKE '%@%'` 形态 | **有执行但工件没留** → 镜像差异，重点转「json 内容正确性」 |
| 3 | 1、2 皆无 | **平台不具备生成能力** → 只能走 B1（人工造 json）/B2（直插）；并写 NEEDS_HUMAN 记**平台构建能力缺口**（不是发布缺陷） |

> 第 1 步即可定性，不必触发扣减。第 2 步是防「工件看不到但确实执行过」的误判——因为
> `app_starter_init_detail` 记的是**已执行**，与文件是否在本地可见无关。
> 这两条信息源互补，缺一条都会误判。

---

## 5. SELF-CHECK 复现命令

```bash
# 运行态穷举（66 schema，只读）
python "<HERMES_HOME>/cache/scratch/b2_evidence.py"

# 设计态三层 + 发布历史
python "<HERMES_HOME>/cache/scratch/b2_probe14.py"

# 明细 0 行机制（实体 stereotype 分布）
python "<HERMES_HOME>/cache/scratch/b2_probe4.py"

# v2 新增：发布成功记录全量 + 规则创建时序（订正 2 的复现）
python "<HERMES_HOME>/cache/scratch/b2_timeline_check.py"

# v2 新增：B-2 四条断言自跑复核（L3/L4/L5/L7）
python "<HERMES_HOME>/cache/scratch/b2_selfcheck.py"

# v2：DAO 层 INSERT 点（注意：DAO 级 grep 不足以证明"唯一"）
grep -rnE 'Rt[A-Za-z]*Dao\.(create|createBatch)' <HERMES_HOME>/cache/docs/audit/artifacts/scratch-migrated/aud/cfr-b2-upgrade
grep -rn 'deductionRtRuleDao' <HERMES_HOME>/cache/docs/audit/artifacts/scratch-migrated/aud/cfr-b2-upgrade

# v3 新增：反射通用 INSERT 通路（v2 漏掉的那条）
grep -n 'allInOneDaoService.createBatch' \
  <HERMES_HOME>/cache/docs/audit/artifacts/scratch-migrated/aud/cfr-datainit/com/seeyon/boot/starter/datainit/service/JsonDataInitializer.java
# → L523；配合 L201 getEntityNameFromFileName / L202 Class.forName / L203 JsonUtils.toList

grep -n 'INIT_TENANT' \
  <HERMES_HOME>/cache/docs/audit/artifacts/scratch-migrated/aud/cfr-datainit/com/seeyon/boot/starter/datainit/service/DefaultDataInitializer.java
# → L1201 getAppClassPathResources(appName, "init/tenant/*")

# v3 新增：工件是否含 init/tenant（全仓 29 个 5.3.5xx jar，逐个实测，全部为 0）
for j in $(find /d/repo/CHIT/com/seeyon -path "*5.3.5*" -name "*.jar"); do
  echo "$(unzip -l "$j" | grep -c 'init/tenant')  $(basename $j)"
done | sort -rn

# v3：DB 侧 datainit / metadata 是否含扣减
python "<HERMES_HOME>/cache/scratch/b2_init_check.py"
python "<HERMES_HOME>/cache/scratch/b2_meta_check.py"

# v4 新增：全实例 app_starter_init_detail 普查（114 schema / 6193 行 / 含 @ = 0）
python "<HERMES_HOME>/cache/scratch/b2_init_census.py"
# 期望输出：schemas=114 / TOTAL rows=6193 / rows with '@'=0 / rows with 'deduction'=0
```

产物对照：
- `docs/audit/artifacts/udc-node-evidence/b2-runtime-trigger-blocker.json`（rt_census / design_state / deploy_state / entity_physical）
- `docs/audit/artifacts/udc-node-evidence/b2-runtime-trigger-BLOCKED.md`（过程叙事，结论一致）
- `auditor/B2-PRE-AUDIT-20261018.md`（DB 侧独立复核，L1–L7 + S1）
- `auditor/B2-REVIEW-FEEDBACK-20261018.md`（字节码侧复核，判 PARTIAL —— v2 据此修订）
- `auditor/B2-SELF-CORRECTION-20261018.md`（auditor 自我订正「INSERT 环」—— **v3 据此修订**）
