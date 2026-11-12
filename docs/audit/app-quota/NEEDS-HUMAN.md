# NEEDS-HUMAN｜建应用配额口径已闭合，需人工二选一

- **切片**：SLICE-A1（A 组 · 应用域 · P0）
- **日期**：2026-10-18
- **环境**：test2（库 `udc_test2` / Redis env=`test2` / 网关 `lowcode-test2.example.com`）
- **本片性质**：**只读取证**。0 写操作、0 页面重试建应用、0 数据库变更。
- **结论状态**：配额真实口径 **已闭合（LIVE）**；「建应用」动作本身仍 **BLOCKED**，但阻塞点已从「口径不明」变为「资源已满，需人工决策」。

---

## 一、一句话结论

`ctp_sandbox_config` 的两行**不是冲突，是主键语义不同**：配额表以 **`id` = 租户ID** 为业务键
（`tenant_id` 列恒为 -999，由 `create()` 里 `setTenantId(null)` + NOT NULL 无默认 → 框架回填平台默认租户，
是**写入路径副产物**，且 -999 行恰为「平台总体额度行」createAppNum=11 = License udc=11，
两行语义至此完全分离——【A1-DOC-FIX ② 机制描述补强，2026-10-18 auditor VERDICT】）。
按平台真实读取路径，本租户（`-8112660841495312922`）生效上限 = **`createAppNum = 10`**（LIVE 三通道），
当前占配额 = **10**（LIVE DB 实测）。
门语义 `count >= createAppNum` 为**字节码事实（STATIC）**——因此
**cap=10、count=10、门为 count>=cap ⇒ 按代码必然抛 `UDC_APP_0030`**。

> **结论强度声明【A1-DOC-FIX ②，2026-10-18 auditor VERDICT】**：「必抛 UDC_APP_0030」是
> **STATIC 合成结论**（LIVE 的 cap/count + STATIC 的门语义，二者相乘），**不是端到端实测**——
> 全仓至今没有任何一次真实 0030 响应样本（无抓包/无原文/无截图）。
> 引用本结论时请表述为「按代码必抛」，不要写成「实测抛出」。

因此「新建 NORMAL 应用」不是"上限可能还有 1 个空位"，而是**确定已满**。要继续建应用，必须先释放 1 个名额或由人工授权提高上限。

---

## 二、决定性证据（LIVE，三条独立通道一致）

### E1 — 平台自述接口（最直接，就是配额门读的那份 DTO）

```
GET https://lowcode-test2.example.com/service/udc/sandbox/tenant/config/-8112660841495312922
Cookie: <shared-credentials 路径引用，本文件不落 secret>
Referer: https://lowcode-test2.example.com/main/
```

响应 **HTTP 200**：

```json
{"status":0,"code":"BOOT_0000","message":"SUCCESS","traceId":"3278987915564157116",
 "data":{"content":{
   "validate":true,
   "useTenantId":"-8112660841495312922",
   "tenantCaption":"四川客户方信息产品有限责任公司",
   "createAppNum":10,
   "runAppNum":15,
   "currentCreateAppNum":null,
   "currentRunAppNum":null}}}
```

> 该端点在字节码里**无 `@HasRole`**（`SandboxTenantConfigController` `@GetMapping("{id}")`），
> 是平台对"租户级沙箱配额"最直接的只读自述，返回的 `createAppNum` 与配额门拿到的 `SandboxTenantConfigDto.createAppNum` 是同一个 DTO 类型。
> 注意：`BOOT_0000` 单独不构成 PASS，本结论另有 E2/E3 两条独立通道佐证（见下）。

### E2 — 平台生效缓存（Redis 哈希，`getTenantSandboxConfig` 的第一读取源）

```
KEY  : sandbox/test2/tenant/config   (type=hash)
HKEYS: ['-8112660841495312922']      ← 只有一个 field，且正好是本租户 id
HGET -8112660841495312922 ->
  ["com.seeyon.boot.starter.sandbox.dto.SandboxTenantConfigDto",
   {"validate":true,
    "useTenantId":["java.lang.Long",-8112660841495312922],
    "tenantCaption":"四川客户方信息产品有限责任公司",
    "createAppNum":10,
    "runAppNum":15}]
HGET -999 -> NULL（未命中）
```

**TTL 证据（本节为读取链的信息量主体【A1-DOC-FIX ③ 补正，2026-10-18 auditor VERDICT】）**：
- 本片首次读取时 `TTL = 204065` 秒（约 2.36 天）
- 调用 E1 端点后 `TTL = 604790` 秒（约 7.00 天，= `7 days` 常量回写）

`SandboxConfigService.entityToDto()` 唯一一处写缓存即 `putCache()`，其中 `expire(..., 7, DAYS)`。
TTL 由 2.36 天跳回 7 天，说明**E1 的响应体就是本次 `selectById` 回源、并已回写缓存的同一份数据**，不是历史残留。
关键机制（auditor 补正）：`getTenantSandboxConfig()` 在**缓存命中时不回写**（L143-151 else 分支无 `putCache`），
只有未命中→`selectById` 回源→`entityToDto` 才回写。所以「TTL 被刷回 7d」反证本次确实回源了——
**这才是本节真正的信息量所在**。

> **降级说明【A1-DOC-FIX ③】**：原文「`current*` 为 null ⇒ 走 selectById 分支」是**恒真判据**——
> `@GetMapping("{id}")` 无条件走 `selectById → entityToDto → putCache`，该端点没有第二分支。
> `current*` 均为 null 只能作**响应形态校验**（值符合预期形态），不构成「读取路径」的独立证据。
> 独立证据主体 = 上面的 TTL 回写。

### E3 — 数据库直读（设计态权威源）

```sql
SELECT id, tenant_id, create_app_num, run_app_num, version, update_time
FROM udc_test2.ctp_sandbox_config ORDER BY id;
```

| id | tenant_id | create_app_num | run_app_num | version | update_time |
|---|---|---|---|---|---|
| **-8112660841495312922** | -999 | **10** | 15 | 1 | 2026-08-17 11:03:27 |
| -999 | -999 | 11 | 0 | 3 | 2026-08-13 11:47:42 |

**两行不是冲突，是主键语义不同**——决定性 STATIC + LIVE 双重佐证：

1. **`create()` 里的赋值证明 `id` 才承载租户身份**（`docs/audit/artifacts/scratch-migrated/cfr-sbx/out/com/seeyon/boot/starter/sandbox/domain/service/SandboxConfigService.java` L175-179）：
   ```java
   SandboxConfig entity = BeanCopier.copy(dto, SandboxConfig.class);
   entity.setTenantId(null);                       // ← tenant_id 被显式置空
   entity.setId(dto.getUseTenantId());             // ← 租户ID 写进 id 主键
   this.sandboxConfigDao.create(entity);
   ```
2. **`configAllTenant()` 也把 `id` 当租户键**（同文件 L253-258）：
   ```java
   List<Long> tenantList = sandboxConfigs.stream().map(BaseEntity::getId)...;  // 用 id 取租户列表
   dto.setUseTenantId(config.getId());                                          // id → useTenantId
   ```
3. **业务表里租户 id 恒为 `-8112660841495312922`**：
   - `udc_application.tenant_id` 全库 20 行**只有这一个值**
   - `organization_test2.org_unit` 423 行、`udc_test2.udc_entity` 1814 行、`udc_function_node` 2269 行，`tenant_id` 均为该值
   - 反证：若租户真是 `-999`，则 `udc_application` 会全部落在 `-999` 下，事实不是。

   > **行数登记【A1-DOC-FIX ④，2026-10-18】**：`udc_function_node` 本片实测 **2269** 行，
   > TASK-GOAL.md 记载 2260 —— 差 9 行，属 TASK-GOAL 快照时点后新增，不影响本片任何结论，仅登记备查。
4. **`ctp_user_test2.ctp_user` 的 `tenant_id` 是 `-999`，直接证明 `tenant_id` 这一列在 test2 是"平台默认值"而非租户归属**（5345 条用户全部 `-999`）。这正是为什么 `ctp_sandbox_config.tenant_id` 也不能用来判租户。

> 因此：按 `tenant_id=-999` 匹配会命中 2 行、无法唯一确定——这条路**本身是错的**；按 `id` 匹配唯一命中 1 行，且与 E1/E2 的 `useTenantId` 完全一致。**上限 = 10，不再是"10 vs 11 未决"。**

---

## 三、计数侧证据（配额门的 count 口径）

### E4 — 门的计数条件与语义（字节码）

`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/entity/domain/service/ApplicationService.java` **L533-546**：

```java
public void checkTenantLicenseAppCount(ApplicationDto applicationDto) {
    if (Objects.isNull(applicationDto) || ApplicationSourceEnum.NORMAL == applicationDto.getSourceType()) {
        SandboxTenantConfigDto configDto = this.sandboxConfigService.getCurrentTenantSandboxConfig();
        Optional.ofNullable(configDto).ifPresent(dto -> {
            Wrapper wrapper = new Wrapper(UdcApplication.class);
            wrapper.and().andEqualTo(SOURCE_TYPE, ApplicationSourceEnum.NORMAL);
            wrapper.and().andEqualTo(JSONPREFAB, false);
            int count = this.dao.selectCountByWrapper(wrapper);
            if (count >= dto.getCreateAppNum()) {                                  // ← >= 不是 >
                throw new BusinessException("UDC_APP_0030",
                    new String[]{String.valueOf(dto.getCreateAppNum()), String.valueOf(count)});
            }
        });
    }
}
```

- 计数条件：`source_type = NORMAL(0) AND json_prefab = 0`
  **【A1-DOC-FIX ① 补正，2026-10-18 auditor VERDICT】**：门的 count 在 `TenantChangeFunction` 上下文内执行，
  属**租户域计数**——上面的 Wrapper 代码虽无 tenant_id 谓词，但通用复现 SQL 必须补 `tenant_id=<本租户>`，
  否则在多租户库会算错。本库单租户恰好同值（补谓词后仍 = 10，auditor 已实测）。
  **通用口径 SQL**：
  ```sql
  SELECT COUNT(*) FROM udc_test2.udc_application
  WHERE source_type=0 AND json_prefab=0 AND tenant_id=-8112660841495312922;  -- 补租户谓词
  ```
- 比较符：**`count >= createAppNum`**（`>=`，不是 `>`）
- `ApplicationSourceEnum.NORMAL(0, "normal")` / `FORM(1, "form")`（`docs/audit/artifacts/scratch-migrated/cfr-r31/com/seeyon/udc/common/enums/ApplicationSourceEnum.java` L17-18）

### E5 — 实测计数（单条 SQL，多口径一致）

```sql
SELECT COUNT(*) FROM udc_test2.udc_application;                                  -- 20（全表）
SELECT COUNT(*) FROM udc_test2.udc_application WHERE source_type=0;              -- 10
SELECT COUNT(*) FROM udc_test2.udc_application WHERE source_type=0 AND json_prefab=0;  -- 10  ← 门的口径
```

分组明细：
```
tenant_id=-8112660841495312922, source_type=0(NORMAL), json_prefab=0 → 10
tenant_id=-8112660841495312922, source_type=1(FORM),   json_prefab=0 → 10
```

### E6 — 阈值判定

| 生效上限 | 来源 | count | `count >= cap`? | 结果 |
|---|---|---|---|---|
| **10** | **row id = -8112660841495312922（已由 E1/E2 三重确认为真）** | 10 | **YES** | **必抛 UDC_APP_0030** |
| 11 | row id = -999（`tenant_id` 干扰列误命中，已排除） | 10 | NO | （不成立的分支） |

**`UDC_APP_0030` 错误码语义**：`AppErrorCode.APP_COUNT_EXCEEDED = "UDC_APP_0030"`（`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/exception/AppErrorCode.java` L16）。

i18n 文案（`app_common_test2.i18n_default_resource`，`resource_key='error.code.UDC_APP_0030'`）：

> `应用数量超出限制，您最多可以创建{0}个应用，现已创建了{0}个。`

**⚠ 顺带发现的平台文案缺陷**：`ApplicationService` L542 传的是**两个独立参数**
`{createAppNum}, {count}`，但中/英/繁三语文案**两个占位符都写成了 `{0}`**，
渲染时两个值位置都会显示"上限"（即"最多可以创建10个，现已创建了10个"），
`{count}` 被丢弃。**所以用户界面上的数字不能作为判定证据**——若看到两个都是 10，那是文案 bug 造成的巧合，不是"已建 10 个"的证明。本片结论全部取自 E1/E2/E3/E5，不依赖 UI 文案。

---

## 四、当前 10 个配额占用者（腾位决策依据）

`source_type=0 AND json_prefab=0` 的 10 行（`udc_test2.udc_application`）：

| # | id | caption | 是否已在沙箱运行 | create_time |
|---|---|---|---|---|
| 1 | 2378987216360786643 | 应收管理 | 是 | 2025-02-13 |
| 2 | 1656355078954763084 | 智慧营销结算 | 是 | 2025-08-21 |
| 3 | 5791640252914287064 | 项目考核管理 | 是 | 2026-01-27 |
| 4 | 3117198973910469031 | 采虹链 | 是 | 2026-03-11 |
| 5 | 3289082814923688017 | 智能项目管理平台 | 是 | 2026-03-17 |
| 6 | 6570299241515796755 | **原智能项目管理平台** | **否** | 2026-04-02 |
| 7 | 7417152852034669760 | 飞书集成 | 是 | 2026-05-15 |
| 8 | 4396215186967839451 | 云业务 | 是 | 2026-08-14 |
| 9 | **8704025620829192834** | **数据迁移（本项目）** | 是 | 2026-10-12 |
| 10 | 7001530513149673721 | **智慧营销结算副本（最新）** | **否** | 2026-10-14 |

- `ctp_sandbox_app` 共 10 行，`app_state=1(RUNNING)` 全部 10 个，`owner_tenant_id` 全为本租户 → 运行配额同样 10/15，尚余 5。
- 两个"未进沙箱"的 NORMAL 应用（#6、#10）**仍占用 create 配额**（配额门只看 `udc_application` 行，不看是否运行）。

---

## 五、二选一（需operator-a决策）

### 方案 A：**确认上限口径 = 10，接受"已满"，改为腾位**

- 含义：`createAppNum=10` 已由 LIVE 三重闭合，不再需要改配置。
- 动作：从第四节挑 1 个应用释放 create 配额（**只读本片不执行任何删除**）。
- 候选（按"最可能是历史残留"排序，最终由你定）：
  - **#6 原智能项目管理平台**（`6570299241515796755`，未进沙箱，名称含"原"，疑为 #5 的旧版）
  - **#10 智慧营销结算副本（最新）**（`7001530513149673721`，未进沙箱，疑为 #2 的 save_as 副本）
- 风险：删除 UDC 应用是不可逆操作，且需确认业务侧不再引用；删除动作按硬约束需你明确授权 + 走页面。
- 释放后：`count` 变 9，`9 >= 10` 不成立 → 可建 1 个 NORMAL 应用。

### 方案 B：**授权提高本租户上限（10 → 11）**

- 含义：改 `ctp_sandbox_config` 里 `id=-8112660841495312922` 的 `create_app_num`。
- 平台正规通道（**不是直连改表**）：
  ```
  POST /service/udc/sandbox/tenant/config/update
  Body: SandboxTenantConfigDto{ useTenantId=-8112660841495312922, createAppNum=11, runAppNum=15, ... }
  ```
  `update()` 会 `entityToDto → putCache`，Redis 同步刷新（`SandboxConfigService` L211-223）。
- **但有硬闸**：`update()` 先调 `tenantChangeCheck()`（L184-208），其中：
  ```java
  int systemCreateAppNum = this.getSystemCreateAppNum();   // = licenseProcessor.getLimit("udc")
  ...
  if (createCount > systemCreateAppNum) throw "超过系统最大创建应用数!";
  ```
  `getSystemCreateAppNum()` 取 **License 的 `udc` 额度**。
  **本片未能取证该 License 值**：`ctp_license_info` 在 `app_common_test2` / `app_sandbox_test2` / `ctp_user_test2` / `udc_test2` 四个候选 schema 里均为 **0 行**；
  故「能否提到 11」取决于 License 是否 ≥ 11，这一项 **UNVERIFIED**。
- 该端点带 `@HasRole({"OpsAdmin"})`，**需要 OpsAdmin 账号**（test-account-1 是否具备未验证）。

### 建议

**优先方案 A**，理由：
1. 上限 10 已被三条独立 LIVE 通道钉死，方案 B 要推翻的是「License 系统上限」这道未取证的门，不确定性更高。
2. 第四节里 #6 / #10 两个未运行的 NORMAL 应用本身就疑为历史残留，释放它们对业务影响最小。
3. 方案 B 需要 OpsAdmin + License 双前置，任一不满足仍然 BLOCKED，会再次空转。

若你更希望"不动现有应用"，则选 B，但需先确认 License `udc` 额度 ≥ 11 且 test-account-1 有 OpsAdmin 权限。

---

## 六、可复现命令

```bash
cd <XIAOZHUA_AGENT_ROOT>

# 1) 设计态 + 缓存态取证（DB + Redis，只读，0 次 /service）
uv run --no-project --with pymysql python docs/audit/artifacts/scratch-migrated/slice-a1/a1_quota_closure.py

# 2) 平台自述接口（只读 GET，1 次 /service；与其他组共用账号，务必 ≥30s 间隔）
python docs/audit/artifacts/scratch-migrated/slice-a1/a1_live_config.py
# 可选指定租户： python docs/audit/artifacts/scratch-migrated/slice-a1/a1_live_config.py -999
```

- DB/Redis 取证日志：`docs/audit/artifacts/scratch-migrated/slice-a1/a1_quota_closure.log`
- 平台自述原始响应：`docs/audit/artifacts/scratch-migrated/slice-a1/a1_live_config.captured.json`（body）
  + `docs/audit/artifacts/scratch-migrated/slice-a1/a1_live_config.log`（HTTP 状态 + body，**追加写，不覆盖**）
- 逐字留证（人类可读）：`docs/audit/app-quota/EVIDENCE-LIVE-tenant-config.md`

> 脚本已内置：网关前缀校正（`/service/udc/...`）、`selectById` 路径判据（`current*` 为 null）、
> 阈值判定输出。重放若遇 `BOOT_1006 token黑名单`，属同账号互踢，**不要连发重试**。

---

## 七、证据等级汇总

| 结论 | 等级 | 依据 |
|---|---|---|
| 配额表业务主键 = `id`；`tenant_id` 为写入路径副产物（框架回填默认租户），-999 行 = 平台总体额度行 | **LIVE + STATIC** | E3 + `create()` L176-177 + `configAllTenant()` L253-258 + `ctp_user.tenant_id` 反证 + License udc=11（auditor 闭合） |
| 本租户生效上限 = **10** | **LIVE**（三通道） | E1 平台自述 + E2 Redis 生效缓存(+TTL 刷新) + E3 DB 直读 |
| 当前占配额 = **10** | **LIVE** | E5 DB 直读（全表/条件/分组三口径一致；**通用 SQL 须补 tenant_id 谓词**【A1-DOC-FIX ①】） |
| 门语义 `count >= cap` | **STATIC** | `ApplicationService` L541 字节码（auditor 直读 L533-546 确认 L542 两实参） |
| **按代码必然抛 0030**（cap=10 + count=10 + 门>=） | **STATIC 合成**【A1-DOC-FIX ②】 | 非**端到端实测**：全仓无任何一次真实 0030 响应样本 |
| `UDC_APP_0030` 文案两占位符均为 `{0}`（UI 数字不可信） | **LIVE** | `i18n_default_resource` 行（app_common_test2 与 app_common 两库各 1 行，auditor 复核）+ L542 参数个数 |
| 运行配额 10/15（余 5） | **LIVE** | E1 `runAppNum=15` + `ctp_sandbox_app` 10 行 state=1 |
| E1 响应形态符合 `selectById` 输出 | **LIVE**（形态校验）【A1-DOC-FIX ③ 降级】 | `currentCreateAppNum=null` + `currentRunAppNum=null`。**恒真判据，不构成读取路径独立证据**；独立证据 = TTL 回写（缓存命中不回写，L143-151） |
| 网关路由：`sandbox` 只能经 `/service/udc/` 访问 | **LIVE** | 三种前缀实测，详见 `EVIDENCE-LIVE-tenant-config.md` |
| License `udc` 额度 = **11** | **LIVE**【auditor 闭合】 | `GET /service/udc/sandbox/system/config/get-app-limit` → `{maxCreateNum:11, maxRunNum:2147483647}`（traceId=3279011218580310204）；额度走 LicenseProcessor，不走 ctp_license_info |
| test-account-1 是否具备 `OpsAdmin` | **LIVE 否**【auditor 闭合】 | `ctp_user_test2.ctp_user_role`：OpsAdmin 唯一持有者 user_id=-187785715538770856（login_name=system-admin）；test-account-1 只有 OrgAdmin/OrgManager |
| `udc_function_node` 实测 2269 行 vs TASK-GOAL 2260 | **LIVE**【A1-DOC-FIX ④ 登记】 | 差 9 行为快照时点后新增，不影响结论 |

---

## 八、本片边界声明

- 未做任何写操作：无 INSERT/UPDATE/DELETE，无 Redis 写命令（TTL 变化由平台 E1 接口自身 `putCache` 造成，非本侧写）。
- 未重试页面建应用。
- `/service` 请求共 **6 次**，逐条如实登记：

  | # | 请求 | 结果 |
  |---|---|---|
  | 1 | `GET /service/6419954374508955097/sandbox/tenant/config/-811...` | `server_404`（应用级前缀不带 sandbox） |
  | 2 | `GET /service/sandbox/tenant/config/-811...` | `server_404`（sandbox 非独立服务名） |
  | 3 | `GET /service/udc/sandbox/tenant/config/-811...` | **HTTP 200 BOOT_0000，createAppNum=10 ← 决定性证据** |
  | 4 | `GET /service/udc/sandbox/tenant/config/-999` | `BOOT_1006 token黑名单`（互踢） |
  | 5 | 脚本重放（同 #3 URL） | `BOOT_1006 token黑名单`（互踢） |
  | 6 | 探针脚本（探路用，未计入正式取证） | 见 `docs/audit/artifacts/scratch-migrated/slice-a1/` 日志 |

  除 #3 外均无有效业务载荷。**#3 的原始响应已另行落盘，不被后续失败覆盖**：
  - `docs/audit/artifacts/scratch-migrated/slice-a1/a1_live_config.captured.json`（纯 body）
  - `docs/audit/artifacts/scratch-migrated/slice-a1/a1_live_config.log`（HTTP 状态 + body）
  - `docs/audit/app-quota/EVIDENCE-LIVE-tenant-config.md`（人类可读逐字留证）
- `BOOT_1006` 为同账号 `test-account-1` 与其他两组互踢（硬约束第 8 条已登记的已知风险）。**未刷新 token、未连发重试**。
- 未改全局 Hermes 配置，未 push。
