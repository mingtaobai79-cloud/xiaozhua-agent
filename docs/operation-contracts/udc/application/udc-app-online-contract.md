# udc.application.app_online 契约（HANDOFF-03 · Phase 3 / P3 · 2026-10-17 CST）

> 本件登记**发布（上线）动作**的 op 形态、入参、前置门链与 pushEnv 判定。**纯 STATIC 产物，本片 0 次 LIVE 调用**；
> 全篇禁写「发布已打通 / 可上线」——功能可用仍以 P3-B LIVE 串联回读为准。
> 证据单元：`udc-web 5.3.517`（本地 Maven，Controller javap + CFR 反编译）
> ｜`boot-starter-environment 5.3.358`（部署态构件清单实证版本，来源为 lowcode-test 命名空间 —— 环境口径见 §10，不是 test2）
> ｜Nacos `public-common` test2 实配（`docs/audit/evidence/nacos-public-common.yaml`，sha256 见 `nacos-test2-manifest.json`）
> 凭据：本片**完全未读取**（0 值入件）。

## 1. op 两形态（同一 service 方法，不同 Controller 入口）

| # | operation | HTTP | 完整路径 | 入参注解 | 入参类型 | 返回 |
|---|---|---|---|---|---|---|
| 1 | `udc.deployment.app_online` | POST | `{gateway_base}/service/udc/deployment/app-online` | `@MultiRequestBody` | `Long appId` | `SingleResponse<Long>`（deployId） |
| 2 | `udc.deployment.app_online_new` | POST | `{gateway_base}/service/udc/deployment/app-online-new` | `@RequestBody` | `DeployNormalDto` | `SingleResponse<Long>`（deployId） |

> **路径装配（逐字，禁凭记忆拼）**：`{gateway_base}/service/` + 类级 `@RequestMapping("udc/deployment")` + 方法级 `@PostMapping("/app-online-new")`
> = `/service/udc/deployment/app-online-new`。
> 校准依据 = 同族已 LIVE 的 `deploy-normal`：`DeployController` 类级 `@RequestMapping("udc/runtime")` + `@PostMapping("deploy-normal")`
> → `/service/udc/runtime/deploy-normal`（`core/facts/deploy/build-chain.md` L14-18，LIVE 矫正 09-27）。
> 同一装配规则套到 `DeploymentController` 即得上述路径。**注意 `/service/` 之后只有一个 `udc`，不是两个** ——
> 本契约初稿曾误写为 `/service/udc/udc/deployment/...`，已按 deploy-normal 的 LIVE 装配规则自纠。
> `build-chain.md` L21 亦已登记：`udc/deployment/*` 与 `udc/runtime/*` 是**同族易混控制器**，打错会得到 405/404 伪装页。

**入参注解差异是本契约最关键的一处**（HANDOFF 明确警示勿混）：
- `app-online`（形态 1）参数是 `Long`，带 `@MultiRequestBody` → 平铺 `{"appId":123}` 形态可取到值。
- `app-online-new`（形态 2）参数是 DTO，带 `@RequestBody` → **标准 JSON body**，**不是** `@MultiRequestBody` 平铺。
  > 注意：`appOnline(Long)` 内部 new 一个 `DeployNormalDto` 只塞 `appId`，再委托给同一 `DeploymentService.appOnline(dto)` ——
  > 故形态 1 是形态 2 的**退化封装**，两者最终走**完全相同**的前置门链与 pipeline。

**类级注解（两形态共享）**：
- `@RestController` + `@RequestMapping(["udc/deployment"])` + `@RestApi("应用部署")`
- `@HasRole(["udcAppDesigner","udcSystemAdmin","OpsAdmin","BpmSystemManager"])` ← **类级门，先于任何业务逻辑**

STATIC 来源（逐字）：
- `docs/audit/artifacts/udc-web-5.3.517-contracts/DeploymentController.javap.txt`
  - L376-386 类级 `@RequestMapping` / `@RestApi` / `@HasRole`
  - L247-293 `appOnline(Long)` `@PostMapping(["/app-online"])` + `@MultiRequestBody`（参数注解在 L287-293）
  - L295-331 `appOnlineNew(DeployNormalDto)` `@PostMapping(["/app-online-new"])` + `@RequestBody`（L325-331）
  - class_sha256 = `4b72a4fb893d41b2c98ec7bcbab34222ee23b23ba6023d9adc89d784cbb0cfe8`

## 2. DeployNormalDto 字段表（逐字段标 STATIC 来源）

`DeployNormalDto extends DeployParamDto extends BaseDto`

> **来源 jar 澄清（2026-10-17 补正，采纳 auditor VERDICT-handoff03 补正 2）**：
> 下表「STATIC 来源」列的 `tools/jars/udc-web-classes/` 是**采集目录名**，不代表这些 class 源自 udc-web。
> **经独立验证（`unzip -l udc-web-5.3.517.jar | grep DeployNormalDto` → 0 命中），DTO 实际来源为 `udc-common-5.3.517.jar`。**
> 详见 §11 版本锚。javap 文本文件本身在 `tools/jars/udc-web-classes/` 目录下，路径可照用，但**版本归属按 udc-common 记**。

| 字段 | 类型 | 默认值 | @DtoAttribute 名称（逐字） | STATIC 来源 |
|---|---|---|---|---|
| `deployId` | Long | null | — | `tools/jars/udc-web-classes/DeployParamDto.txt` |
| `appId` | Long | null | — | 同上（**必填**，见 §3 门1/门3） |
| `deployType` | `DeployTypeEnum` | null | — | 同上；本 op 内部强制覆写为 `ON_ONLINE`，**入参传值无效** |
| `projectType` | `ProjectTypeEnum` | null | — | 同上；透传至 `DeployInfoDto.projectType` |
| `terminalType` | `TerminalTypeEnum` | null | — | 同上；透传 |
| `pushEnv` | String | null | — | 同上（包级可见字段；**语义见 §6**） |
| `extraParamMap` | `Map<String,Object>` | null | — | 同上；appOnline 未使用（appDeltaDeploy 亦未用） |
| `lockCompatibility` | boolean | **false** | 是否锁定兼容性（example=true） | `docs/audit/artifacts/scratch-migrated/cfr-r31/com/seeyon/udc/common/dto/DeployNormalDto.java` |
| `generateLog` | boolean | **true**（`@Deprecated`） | 是否生成微流程日志（example=true） | 同上 |
| `entityFullNameCondition` | `Map<String,Map<String,Object>>` | null | 数据传输(预置数据实体)参数（example=`<entityFullName, <propName, propValue>>`） | 同上；**仅当非空**时才构造 `DataTransferRequest` |

`DeployTypeEnum` 全集（`tools/jars/udc-web-classes/DeployTypeEnum.txt`）：`TEST / RELEASE / ON_ONLINE / DELTA`（含 `code()`，实现 `Messageable`）。
`DeployBusinessTypeEnum` 全集（`docs/audit/artifacts/decompiled/cfr-r31/com/seeyon/udc/common/enums/DeployBusinessTypeEnum.java`）：`STANDARD(0) / REPUBLISH(1) / UPGRADE(2) / ON_ONLINE(3) / DELTA(4) / FORM_CROSS_ENV_PUSH(5)`。

## 3. 前置门清单（按 `DeploymentService.appOnline` 实际执行顺序）

执行体：`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/deployment/DeploymentService.java` **L196-239**（`appOnline(DeployNormalDto)`）。

| # | 门 | 触发条件 | 抛出（错误文案逐字，常量池 `\uXXXX` 还原） | agent 能否满足 |
|---|---|---|---|---|
| 0 | **类级 `@HasRole`** | 当前账号无 `udcAppDesigner/udcSystemAdmin/OpsAdmin/BpmSystemManager` 任一角色 | 框架层拒绝（非本方法抛出） | **需账号授权**（NEEDS_HUMAN 类） |
| 1 | `validEnv()`（L197 → L243-248） | `ctpSystemEnvUdc.getCurrentModel()` 返回**空 List** | `【低代码应用推送方向】未配置` | **是**（test2 已配置，见 §5 判定） |
| 1a | └ `validateEnv()`（`CtpSystemEnvApi` L22-33） | `deploymentEnvStr` 为空 / 拆出 >4 个 / `test` 与 `implement` 同时出现 | `[seeyon:environment:deploymentEnvStr]配置异常`（空）/ `系统配置[seeyon.system.deployment-env]数量不能超过4个` / `系统配置[seeyon.system.deployment-env]中test和implement不能同时出现` | **是**（test2 未触发，见 §5） |
| 1b | └ `currentEnv == null` | `currentEnv` 未配置 | `系统未配置[seeyon.system.current-env]` | **是**（test2 有值） |
| 2 | `udcAppOpsCheck.check(appId, APP_DEPLOY)`（L198） | `udcAppRightsConfig.isEnable()==true` **且** `!Apps.isRunInTest()` 时：取当前 userId → 该 appId 的 memberRights 不含 `APP_DEPLOY.strCode()` | `BOOT_1004`（无中文文案，`handlerException()` L133-136） | **需应用级授权**（与 P1 target server_403 同族，NEEDS_HUMAN） |
| 2a | └ 短路条件 | `udcAppRightsConfig.isEnable()==false` 或 `Apps.isRunInTest()==true` | 整门跳过 | 环境属性，非 agent 可控。**`isRunInTest()` 已解 = false（见下方判定依据块）；`isEnable()` 仍 UNVERIFIED** |
| 3 | `applicationService.checkApplication(appId)`（L199 → L1320-1328） | `appId` 为 null 或等于 `UdcCommonConstant.NULL_ID` → `UDC_APP_0001`；DB 查不到 → `UDC_APP_0001` | `UDC_APP_0001`（`checkApplicationNull` L1337-1342，中文仅 log 不抛） | **是**（须用真实已存在 appId） |
| 4 | `validDeploy(context)`（L215 → **L250-258**） | `deployRecordService.selectLastSuccessRecord(appId, DELTA)` 存在且 buildVersion 非空，**且** `previousSchemInfo.buildVersion` 非空，**且** `delta.buildVersion > previous.buildVersion` | `在【页面调试】之后,请先进行全量【测试】后再正式【发布】.` | **部分**：取决于目标应用是否做过 DELTA 增量调试；zzprobe 新应用通常无 DELTA 记录 → 门不触发 |
| 5 | `lockCompatibility` 门（L219-235） | `normalDto.isLockCompatibility()==true` **且** `applicationService.hasModifyAfterTime(appId, lockDate)` 为真 | `当前应用有修改,请先测试发布后再上线!` | **是**（置 `lockCompatibility=false` 即跳过整段，含 publishStateLock 副作用） |

**门序不可调换**：门 1（env）在门 2（权限）之前 —— 故 P3-B LIVE 若先撞 env 错，**不能**据此外推「权限 OK」。

**门 2a 短路条件已解（2026-10-17，main 反编译 + 本侧独立复核 一致）**：
`Apps.isRunInTest()` 实现（`boot-core-5.3.358.jar` → `com.seeyon.boot.context.Apps` L599-606）：
```java
public static boolean isRunInTest() {
    if (isTest == null) {
        ConfigurableEnvironment environment = (ConfigurableEnvironment) Apps.getEnvironment();
        MutablePropertySources propertySources = environment.getPropertySources();
        isTest = propertySources.contains("Inlined Test Properties");
    }
    return isTest;
}
```
**判定依据 = Spring 环境 PropertySources 中是否存在名为 `"Inlined Test Properties"` 的 PropertySource。**
该 source 仅在 Spring Boot `@SpringBootTest`（测试上下文）中自动注入；test2 是 Nacos 配置 + K8s 部署的**生产形态容器**，非测试上下文
→ `contains()` = **false** → **`isRunInTest()` = false** → **门 2 在 test2 不被短路，应用级 `APP_DEPLOY` 授权检查是真跑的**。
> 纪律（纳入本契约，禁止违反）：**即使某次 P3-B LIVE 意外顺利，也不得写「权限已具备」** ——
> 必须同时证明门 2 是**真跑通**而非被跳过。本结论已排除「被跳过」这一可能，故 P3-B 顺利时只能归因为「授权已具备」，
> 而在拿到授权输入前该归因不可断言。

**门 0 的判定强度提示**：`@HasRole` 是框架层注解（`com.seeyon.boot.annotation.HasRole`），字节码层面只见注解值，见不到校验实现类。
故「当前账号是否具备 4 角色之一」**本契约不判定**（需 LIVE 或 DB 角色绑定表核实）；P1 已登记本环境无 `udc_role_member` 用户-角色绑定表，
该门在 LIVE 前属 **UNVERIFIED**，不得写成「权限已具备」。

## 4. 门后副作用（写面，P3-B 前必须知情）

`appOnline` 通过全部门后**不是只读**，按序执行：

1. `eventBus.publish(DeployStartEvent{... businessType=ON_ONLINE ...})`（L217）
2. `pipeLineManager.startOnlinePipeline(context)`（L218）← **真正启动上线流水线**
3. `publishStateManager.publishStateLock(app, appLockDto)`（仅 `lockCompatibility=true`，L235）
4. `ThreadUtil.execAsync(... gitCodeManager.createBranchTag(appInfoDto))`（L236-238，**异步建 tag 分支**）

> 判 P3-B 边界时注意：即使流水线后续失败，步骤 1/2/4 已发生。`deployId = Ids.gidLong()` 在门 3 之后即生成并返回。
> **不能**把「返回了 deployId」当作「上线成功」—— 成功与否须以 `udc_app_version.state` / 运行态回读为准。

## 5. pushEnv 判定（本 HANDOFF 决定性三态结论）

### 5.1 判定对象是 `validEnv()`，不是 `pushEnv` 字段

`validEnv()` 的实现（`DeploymentService` L243-248）：

```java
private void validEnv() {
    List modelDtoList = this.ctpSystemEnvUdc.getCurrentModel();
    if (CollectionUtils.isEmpty(modelDtoList)) {
        throw new BusinessException().addError("【低代码应用推送方向】未配置");
    }
}
```

`getCurrentModel()` 的实现（`CtpSystemEnvUdc`，boot-starter-environment **5.3.358** 反编译件 §SCRATCH）：

```java
public List<CtpSystemEnvModelDto> getCurrentModel() {
    this.validateEnv();
    ArrayList<CtpSystemEnvModelDto> modelDtoList = new ArrayList<>();
    List<String> strings = this.getPush(this.ctpSystemEnvProperties.getDeploymentEnvStr());
    if (strings == null) return modelDtoList;           // ← 空 List，触发 validEnv 抛错
    for (String envStr : strings) {
        String[] envs = envStr.split("-");
        if (!this.ctpSystemEnvProperties.getCurrentEnv().name().equals(envs[0])) continue;  // ← 关键过滤
        CtpSystemEnvModelDto dto = new CtpSystemEnvModelDto();
        dto.setEnv(CtpSystemEnvEnum.valueOf(envs[1]));
        modelDtoList.add(dto);
    }
    return modelDtoList;
}
```

`getPush(deploymentEnvStr)` 是**硬编码白名单**（同文件）—— 只有 4 个合法输入：

| `deploymentEnvStr` | 返回 |
|---|---|
| `development-prod` | `[development-prod]` |
| `development-prod-pre` | `[development-prod, development-pre]` |
| `development-implement-prod` | `[development-implement, development-prod]` |
| `development-implement-prod-pre` | `[development-implement, development-prod, development-pre]` |
| **其它任意值（含 `null`、含 `test*` 前缀）** | **`null`** |

**推论（两条硬约束，均字节码级）**：
1. `getPush` 白名单里**没有任何以 `test` 开头的项** → 若 `currentEnv == test`，`envs[0]` 永远不等于 `"test"` → `modelDtoList` 恒空 → `validEnv()` **必抛**「【低代码应用推送方向】未配置」。
2. `getPush` 只认 4 个白名单串 → 若 `deploymentEnvStr` 被配成 `test2-prod` 一类自造值 → 返回 `null` → 同样**必抛**。

### 5.2 test2 实配（Nacos 只读证据）

`docs/audit/evidence/nacos-public-common.yaml`（test2 / tenant `seeyon-test2` / group `seeyon` / HTTP 200 / 209 B / secrets_redacted）：

```yaml
seeyon:
  environment:
    dataPushStr: implement-prod-development
    checkDeploymentToProd: false
    currentEnv: development
    deploymentEnvStr: development-implement-prod
    checkDeploymentToDev: false
```

- 版本锚：`nacos-test2-manifest.json` 记 `sha256=7c5bb470c223b7e4b33199e9ea99e2491b37a75fd5ffb1af1a7d8b1323666e52`、`bytes=209`、
  http_status=200、network=live-read-only、tenant=seeyon-test2。采集件受 baseline commit `305e0ff` 管控（未改动）。
  > **sha 口径警告（2026-10-17 补正，采纳 auditor VERDICT-handoff03 补正 3；本侧独立复现）**：
  > `7c5bb470…666e52` 是 **Nacos 原样字节（LF 换行，209 B）**的哈希。
  > 本地文件 `docs/audit/evidence/nacos-public-common.yaml` 因 git `autocrlf` 被转成 **CRLF（216 B）**，
  > 直接对本地文件算 sha256 得 `f01f34fd0e7cd55fe6ec832864fc48e4f0faa4a2cb5f25e67f44100f526d11ec`（≠ manifest）——
  > **这容易误判成采集件被篡改，实际不是**。
  > 复现：`tr -d '\r' < 该文件 | sha256sum` → `7c5bb470…666e52`，`tr -d '\r' < 该文件 | wc -c` → `209`。**归一化后与 manifest 逐字一致，采集件完整。**
  > 纪律：比对 Nacos 采集件前，先做 **LF 归一化**。
- 枚举合法性核对（`CtpSystemEnvEnum` 5.3.358）：`development / prod / test / implement / pre`（5 个）。
  → `currentEnv: development` **合法**；`deploymentEnvStr: development-implement-prod` **在白名单内**。
- 若按此实配推演 `getCurrentModel()`：
  `getPush("development-implement-prod")` → `[development-implement, development-prod]`
  → 逐项 `split("-")[0]` = `development` / `development`，与 `currentEnv.name()="development"` **两两相等**
  → `modelDtoList` 得到 **2 项** → `CollectionUtils.isEmpty` = false → **`validEnv()` 不抛**。
- `validateEnv()` 三项也不触发：`deploymentEnv()` 拆 3 项（≤4）；含 `implement` 不含 `test`（无冲突）；`currentEnv` 非 null。

### 5.3 结论（三态取一）

> **pushEnv 前置 = 已配置（test2 门 1 可通过）。证据 = STATIC 字节码 + Nacos 只读实配，两者一致。**

严格表述（不越界）：
- **门 1「【低代码应用推送方向】未配置」在 test2 不会触发** —— 这是字节码 + 实配的双向推演结论，**不是 LIVE 观测**。
  本轮 0 次 /service 调用，故不得写成「已 LIVE 验证门 1 通过」。
- `pushEnv` **业务字段本身可为空**：`DeployParamDto.pushEnv` 无注解、无必填校验；`appOnline` 仅 `deployInfoDto.setPushEnv(normalDto.getPushEnv())` 透传（L206）。
  其消费方 `AppDataPushService.pushData` 对空值有显式分支：`if (isBlank(pushEnv) || pushEnv.equals(currentEnv.name()))` → 走 `sendNoticeMQ` + `compatibleLess310`，**不抛错**（L156-158）。
  → 故 **pushEnv 是软参数，不是硬前置**；硬前置是 `validEnv()`，而它已满足。
- 与 P3-B 的关系：**门 1 不再是 P3-B 的阻断项**；P3-B 的真实阻断概率前移到**门 0（角色）/ 门 2（应用级 APP_DEPLOY 授权）**，
  二者与 target `server_403` 同族，NEEDS_HUMAN 未解。**本件不改变 NEEDS_HUMAN 状态。**

### 5.4 反证储备（若 P3-B 仍撞门 1，按此二分）

| 观测到 | 指向 | 处置 |
|---|---|---|
| 文案=`【低代码应用推送方向】未配置` | `getPush` 返回 null（`deploymentEnvStr` 不在白名单）**或** `currentEnv` 不等于任何 `envs[0]` | 读 Nacos `public-common` 当下值（本件 5.2 为采集件，可能已漂移）；比对白名单 4 串 |
| 文案=`系统未配置[seeyon.system.current-env]` | `currentEnv` 为 null | 配置缺失，非 agent 可写（Nacos 写面禁） |
| 文案=`系统配置[seeyon.system.deployment-env]...` | `validateEnv()` 三项之一 | 配置非法 |
| 文案=`BOOT_1004` | 门 2 应用级授权缺 `APP_DEPLOY` | 与 target server_403 同族，NEEDS_HUMAN |
| 文案=`当前应用有修改,请先测试发布后再上线!` | 门 5 兼容性锁 | 置 `lockCompatibility=false` 重试，或先测试发布 |

## 6. ON_ONLINE 与 deploy-normal 的区别

| 维度 | `app-online-new`（本件） | `deploy-normal`（既有 LIVE 契约，**不重探**） |
|---|---|---|
| service 方法 | `DeploymentService.appOnline(DeployNormalDto)` L196 | `DeploymentService`（pipeline 另入口，`core/tools/udc/deploy.normal.md` 已 LIVE） |
| `DeployTypeEnum` | **强制 `ON_ONLINE`**（L200/L203，入参 `deployType` 被覆写） | 参数化（TEST / RELEASE 等） |
| `DeployBusinessTypeEnum` | `ON_ONLINE`（L202） | 由入参决定 |
| pipeline | `startOnlinePipeline(context)`（L218） | `startTestPipeline` 族（TEST/RELEASE 路径） |
| `validEnv()` | **有**（L197） | 既有契约未登记该门 → **两者门链不同，不得互相套用** |
| `validDeploy(context)` | **有**（L215） | 既有契约未登记该门 |
| `lockCompatibility` | **有**，且带 `publishStateLock` 副作用 | 既有契约未登记 |
| 语义 | 「正式上线」：把已测试通过的版本推到运行态 | 「部署/测试发布」：构建并部署到测试形态 |
| 返回 | `SingleResponse<Long>` deployId | 同族 `SingleResponse` |

**与 `appDeltaDeploy` 的对照（重要反例）**：`appDeltaDeploy(DeployNormalDto)`（L321-338）**不调 `validEnv()`、不调 `udcAppOpsCheck.check`、不调 `validDeploy`**，
只做 `checkApplication` + pipeline。→ 说明 env 门与权限门是 `appOnline` 独有的，**不能把 delta 的可调用性外推到 online**。

## 7. appId 来源约束（硬约束 · main 轮7 只读 DB 实测后要求补入）

> **核心一句**：`app-online` 只能对**已存在于 `udc_application` 的行**执行上线。它**不能凭空建应用**，也不是「草稿转正」端点。
> 写成「调 app-online 就能建出应用」是错误口径。

### 7.1 结构性约束：`checkApplication(appId)` 要求行已存在

门 3（§3）决定了这一点：`applicationService.checkApplication(appId)` → `selectById(appId)` → `checkApplicationNull`，
查不到即抛 `UDC_APP_0001`（`ApplicationService` L1320-1342）。
→ `appId` 必须是**已落库的 `udc_application.id`**（bigint）。任何「先上线再建应用」的设想在字节码层面不成立。

### 7.2 新建 NORMAL 应用受配额硬门 `UDC_APP_0030`（test2 已满）

`ApplicationService.checkTenantLicenseAppCount(ApplicationDto)`（L533-548）字节码逻辑：

```java
if (Objects.isNull(applicationDto) || ApplicationSourceEnum.NORMAL == applicationDto.getSourceType()) {
    SandboxTenantConfigDto configDto = this.sandboxConfigService.getCurrentTenantSandboxConfig();
    Optional.ofNullable(configDto).ifPresent(dto -> {
        Wrapper wrapper = new Wrapper(UdcApplication.class);
        wrapper.and().andEqualTo(SOURCE_TYPE, ApplicationSourceEnum.NORMAL);
        wrapper.and().andEqualTo(JSONPREFAB, false);
        int count = this.dao.selectCountByWrapper(wrapper);
        if (count >= dto.getCreateAppNum()) {
            throw new BusinessException("UDC_APP_0030", new String[]{...createAppNum, ...count});
        }
    });
}
```

- 计数条件：`source_type = NORMAL(0) AND json_prefab = 0`；上限 `SandboxTenantConfigDto.createAppNum`。

#### 7.2.1 受门面 = **4 入口 + 1 汇聚点**（2026-10-17 HANDOFF-06 重写，推翻「3 处直接调用」口径）

> **定位说明（HANDOFF-07 后）**：本节是**入口层视角**（4 条业务链，**归纳**，不完备）。
> **最终口径已升级为出口层穷尽证明**（2 个 INSERT 出口 + 门前置），见 **§7.2.3 视角 B** —— 读本节请以下一节为准。

> **口径推翻记录（双向认错，如实留痕）**：
> - **HANDOFF-05 #1 的机制句错**：原文称「L1541 `saveAsNewDesign` 走 `checkTenantLicenseAppCount()` 无参重载间接受门」——
>   无参重载 L529-531 **全树 0 调用者**，不走这条。该句无验证即写入，不成立。
> - **本契约 2a46143 的「受门仍是 3 处」结论也错**：本侧当时只做**符号 grep**（搜 `checkTenantLicenseAppCount`），
>   只命中直接调用点，**漏掉了全程不出现方法名的纯间接路径**（`saveAsNewDesign` → schema 另存链 → `copyCreate`）。
> - **正确口径**：受门面 = **4 个入口，统一汇聚到 `copyCreate` 的 L491**。配额门在**出口**不在入口 —— 这正是它「绕不掉」的原因。

**4 入口表**

| # | 入口 | 命中方式 | 受门位置 |
|---|---|---|---|
| 1 | `create`（L414） | **直接** | `checkTenantLicenseAppCount(dto)` **L418** |
| 2 | `copyCreate`（L487）本身 | **直接** | **L491**（同时是下列 3 条的汇聚点） |
| 3 | `saveAsNormalNewDesign`（L1562） | **直接 + 间接（双重）** | 直接 **L1564**；并 L1576 `schemaManager.saveAsNormal` → L269 `importDelegate.saveAs` → L306 `normalSaveAs` → `ApplicationSaveAsHandler` **L77** `copyCreate` → **L491** |
| 4 | **`saveAsNewDesign`（L1541）** | **纯间接**（自身 0 次直接配额调用） | `SchemaManager.saveAs` **L247** → `ImportDelegateColi.saveAs` **L308** → `ApplicationSaveAsHandler.saveAs` **L66** → `copyCreate` → **L491** |

**出口汇聚链（逐环行号，本侧独立回验 5/5 命中）**

```
ApplicationService.saveAsNewDesign(Long)                  L1541   ← 入口 4，本身无配额门
  └─ L1554  this.schemaManager.saveAs(appId, schemaInfoList)
       └─ SchemaManager.saveAs(long, List<SchemaInfo>)     L229
            ├─ L232  Asserts.isTrue(sourceType == FORM)   ← 仅对 FORM 开放
            ├─ L245  resetResult.setTransportTypeEnum(FORM_SAVE_AS)
            └─ L247  this.importDelegate.saveAs(transportData)
                 └─ ImportDelegateColi.saveAs(TransportData)   L279  @Transactional
                      ├─ L305  if (NORMAL_SAVE_AS.equals(transportType))
                      │          └─ L306  saveAsHandler.normalSaveAs(...)
                      └─ L308  else → saveAsHandler.saveAs(...)     ← FORM_SAVE_AS 走这条
                           └─ ApplicationSaveAsHandler.saveAs(...)  L57
                                └─ L66  applicationService.copyCreate(dto, transportType)
                                     └─ ApplicationService.copyCreate(...)  L487
                                          └─ L491  this.checkTenantLicenseAppCount(dto)  ★ 配额门
```

**同一汇聚点的另一条分支（入口 3，本侧补充）**

```
ApplicationService.saveAsNormalNewDesign(ApplicationSaveAsDto)  L1562
  ├─ L1564  this.checkTenantLicenseAppCount(applicationDto)     ← 直接门（第 1 道）
  └─ L1576  schemaManager.saveAsNormal(...)
       └─ SchemaManager.saveAsNormal(...)  L251
            ├─ L267  setTransportTypeEnum(NORMAL_SAVE_AS)
            └─ L269  importDelegate.saveAs(transportData)
                 └─ ImportDelegateColi.saveAs L279 → L305 命中 NORMAL_SAVE_AS → L306 normalSaveAs
                      └─ ApplicationSaveAsHandler.normalSaveAs(...)  L69
                           └─ L77  applicationService.copyCreate(...)  → copyCreate L487 → L491  ★ 第 2 道门（同一门，重复命中）
```

**必须明写的三条判断**
1. **`saveAsNewDesign` 无自身配额门，但不等于不受门** —— 受门位置在出口 `copyCreate` **L491**。写成「3 处直接调用」会漏掉它，结论会错。
   > ⚠ **但「受门」≠「被拦」**：L491 会被执行到，可 `checkTenantLicenseAppCount` 对 FORM 入参**跳过检查体**（见 §7.2.2 / §7.2.4）。本条的准确含义是「门被执行到」，不是「被拦住」。
2. **无参重载 `checkTenantLicenseAppCount()`（L529-531）0 调用者**（本侧已确认，保留）。它只是 `L530 this.checkTenantLicenseAppCount(null)` 的转发壳，无外部入口。
3. **配额门在出口**：4 个入口里只有 1 个（`create`）是独立门，其余全部流经 `copyCreate` L491 —— 故「绕开某个入口」不等于绕开配额门。
   > ⚠ **补充修正（HANDOFF-08）**：本句后半仍成立（换入口不改变「门被调用」），但**不能推出「一定被拦」** ——
   > 门的**生效**取决于 `dto.sourceType`：NORMAL 生效、FORM 跳过。**入口多寡与生效无关，sourceType 才决定生效。**

#### 7.2.2 `saveAsNewDesign` 的 source_type 约束与 test2 分布（业务含义）

- `SchemaManager.saveAs` **L232**：`Asserts.isTrue(applicationDto.getSourceType().equals(ApplicationSourceEnum.FORM), "判断应用类型为表单")`
  → **`saveAsNewDesign` 只对 `source_type=FORM` 开放**；非 FORM 应用在 L232 即被断言拦下。
- test2 实测分布（main 轮19）：**NORMAL 10 个（占满配额）／FORM 10 个（其中 4 个已发布）**。

> **⚠ 因果修正（2026-10-17 HANDOFF-08，推翻本节原文）**
> 本节原文写：「**但它照样撞 L491 配额门** —— 因为 `copyCreate` 的计数条件统计全租户 NORMAL 应用数，与入口 source_type 无关。」
> **这句是错的，已删。** 错在把「撞门」（调用）当成了「被拦」（生效）。

**正确区分（本轮定稿口径）**：

> **撞门 ≠ 被拦。** 计数条件（`source_type=NORMAL AND json_prefab=0`）确实与入口 `source_type` 无关，
> 但**门体进入条件与 `dto.sourceType` 有关**。非 NORMAL 时 `if` 首条件不成立，检查体整块跳过。
> 「2 个 INSERT 出口 + 门前置」回答的是「**还有别的写入路径吗**」（答：否），
> **不是**「所有路径都会被拦吗」（答：否）。

- 对 FORM 应用：门**被调用**（`copyCreate` L491 确实执行到了），但**检查体被跳过**（`if (isNull(dto) || NORMAL == FORM)` 为假）→ **不计数、不抛错**。
- FORM 域的通路见 **§7.2.4**（本轮新增，3 条静态通路）。

#### 7.2.3 两个视角：入口层（4 条业务链，归纳） vs 出口层（2 个 INSERT 点，**穷尽**）

> **口径演进留痕（三轮，逐次收紧）**：
> ① 「3 处直接调用」（本契约 2a46143）—— **错**，只做符号 grep，漏纯间接路径。
> ② 「4 入口汇聚 copyCreate.L491」（HANDOFF-06 / 本契约 65c38a4）—— **方向对，但是归纳**。
> ③ **「2 个 INSERT 出口 + 各自门前置」（本轮 HANDOFF-07）—— 穷尽证明**，这才是「绕不掉」的完整证据。

##### 视角 A — 入口层（业务链视角，**归纳**，不完备）

`grep -rn "\.copyCreate(" docs/audit/artifacts/scratch-migrated/cfr-r31b/` 共 **4 个调用点**：

| 调用点 | 所属 | 性质 |
|---|---|---|
| `ApplicationSaveAsHandler` **L66** | 另存为（`saveAs`，`FORM_SAVE_AS`） | 入口 4 的链 |
| `ApplicationSaveAsHandler` **L77** | 另存为（`normalSaveAs`，`NORMAL_SAVE_AS`） | 入口 3 的第二道门 |
| `ApplicationImporterBase` **L103** | 应用导入（`@Transactional` 导入器） | **导入链** → `copyCreate` → L491 |
| `ApplicationImporterBase` **L120** | `transferFilter`（`CustomerMetadataConst.APPLICATION` 分支） | **迁移/传输链** → 同一门 |

→ 业务面比「4 入口」更广：建 / 复制 / 两种另存为 / **应用导入** / **应用迁移传输**。
> **但这个视角是不完备的**：入口数不完（后人可以问「还有第 5 条业务链吗？」）。
> 本表的作用只是**说明业务面广**，**不能**用它来证明「统一出口」——证明必须靠视角 B。

##### 视角 B — 出口层（实体写入点视角，**穷尽**，静态可证）

**证明 1：全树 `udc_application` 只有 2 个 INSERT 出口**
```bash
$ grep -rn "this.dao.create((Object)udcApplication)" docs/audit/artifacts/scratch-migrated/cfr-r31b/
ApplicationService.java:458:        this.dao.create((Object)udcApplication);   # create 方法内
ApplicationService.java:525:        this.dao.create((Object)udcApplication);   # copyCreate 方法内
→ 命中数 = 2
```
**证明 2：无 SQL 直写旁路**
```bash
$ grep -rni "insert into udc_application" docs/audit/artifacts/scratch-migrated/cfr-r31b/
→ 命中数 = 0
$ grep -rni "@Insert" docs/audit/artifacts/scratch-migrated/cfr-r31b/ --include=*.java
→ 命中数 = 0
```
**证明 2 补充（本侧扩查，防变量名变体）**：`grep -rn "\.dao\.create("` 全树共 7 处，其中仅 2 处写 `udcApplication`；
其余 5 处写别的实体（`DependentApplicationService` L203 `depApp` / `EntityPresetService` L203/L220 `entity` / `EntityService` L320 / `ParameterService` L46 `parameter`）
→ **不存在「换个变量名偷偷 INSERT udc_application」的路径**。

**证明 3：2 处均在同一方法内、INSERT 之前有门（门前置，且是直线前置）**

| 方法 | 门 | INSERT | 间距 | 门与 INSERT 之间的控制流 |
|---|---|---|---|---|
| `create(ApplicationDto)` **L414** | `checkTenantLicenseAppCount(dto)` **L418** | `dao.create` **L458** | 门在前 **40 行** | 仅 1 处 `throw new BusinessException("UDC_APP_0025")`（**早退**，不跳过门）；**无 `continue` / 无循环回跳 / 无 catch 吞异常** |
| `copyCreate(ApplicationDto, TransportTypeEnum)` **L487** | `checkTenantLicenseAppCount(dto)` **L491** | `dao.create` **L525** | 门在前 **34 行** | 同上：仅 1 处 `throw UDC_APP_0025`（早退）；无 `continue` / 无回跳 |

→ **门是直线前置（fall-through）**：门抛异常则方法终止、INSERT 不执行；门通过则必然流到 INSERT。
**不存在「门被 if 包住而在某分支跳过」的情况** —— 这是比「行号在之前」更强的结论。

**证明 3 补充（排除 update 路径被误当 INSERT，本侧扩查）**：
`updateNoEvents`（L633）虽也整行写 `udc_application`，但它是 `selectById(dto.getId())` → `throwIfNotExist(...)` → `dao.update(...)`
—— **只更新已存在行，不新增**。故**不计入 INSERT 出口**；配额门不覆盖 update 是正确的（改已有应用不消耗配额）。

##### 两个视角的关系（必须这样表述）

| 视角 | 断言 | 性质 | 能否回答「还有别的路吗」 |
|---|---|---|---|
| A 入口层 | 4 条业务链（导入/迁移再 +2 → 实际业务面更广） | **归纳**，不完备 | ❌ 不能 |
| B 出口层 | **2 个 INSERT 点，门前置，0 SQL 旁路** | **穷尽**，静态可证 | ✅ 能 |

→ **结论（最终口径）**：`udc_application` 实体新增**只有 2 个物理出口**（`ApplicationService` L458 / L525），
每个出口的**同一方法内、INSERT 之前**都有配额门（L418→L458、L491→L525），**无 SQL 直写旁路、无变量名变体旁路、无分支跳过门**。
因此 **`custom-app/create` 之外的所有建应用路径都必然经过 `L491` 配额门 —— 该门绕不掉，是结构性的**。

> 本侧仅登记事实，**不据此扩 P2 结论**（P2 判的是「建应用」是否可行；导入/迁移/update 不在该验收口径内）。

- 错误码常量：`AppErrorCode.APP_COUNT_EXCEEDED = "UDC_APP_0030"`（`docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/exception/AppErrorCode.java` L16）。
- 既有登记（旁证，非本片新取）：`core/facts/deploy/build-chain.md` §10.3「test2 租户 createAppNum = 10；NORMAL 占配额者恰 10 个」。
- **main 轮7 只读 DB 实测**：`SELECT COUNT(*) FROM udc_application WHERE source_type=0 AND json_prefab=0` → **10**。
  > **上限未决（2026-10-17 轮14 补正，采纳 main DECISION `traceid-keep-and-quota-10v11-report-v1`）**：
  > **已确定**：`COUNT(*)` = 10（多口径一致：全库 / 按 `tenant_id=-8112660841495312922` 分组 / `json_prefab` 全为 0 无歧义）。
  > **未决**：**生效上限是 10 还是 11**。`ctp_sandbox_config` 有**两行**冲突：
  >
  > | id | tenant_id | create_app_num | version |
  > |---|---|---|---|
  > | -8112660841495312922 | -999 | **10** | 1 |
  > | -999 | -999 | **11** | 3 |
  >
  > 按 `id` = 当前租户 id 匹配 → 取 **10**（当前应用表 `tenant_id` 恰为 -8112660841495312922）；
  > 按 `tenant_id=-999` 匹配 → 两行都命中，**无法唯一确定**。
  > 读它的 `SandboxConfigService` 在 `com.seeyon.boot.starter.sandbox`，**575 个本地 jar 全扫 0 命中** → **本侧无法静态闭合，需 LIVE 确认**。
  > **若生效 11 则当前 10 个尚未满，仍可再建 1 个。**
  >
  > 记账口径：按更严格的 **10/10 满** 记账（id 匹配符合「id=业务主键」的普遍约定），但**不得写成绝对确定**。
  > 对结论的精确影响：**上限=10 时必抛 `UDC_APP_0030`；上限=11 时还可建 1 个、不抛**。
  > 本契约据此把「新建 NORMAL 应用必抛」降级为「**在 10 上限下必抛；上限未决**」。
  → **配额门**性质与门 0/门 2 的**授权门**不同：配额是资源上限，授权是身份权限。

#### 7.2.4 FORM 域三条静态通路（2026-10-17 HANDOFF-08 新增）

> **前提（三方收敛，不再是争议）**：`checkTenantLicenseAppCount` 是**条件门** ——
> `if (Objects.isNull(dto) || ApplicationSourceEnum.NORMAL == dto.getSourceType())` → **FORM 整块跳过检查体**。
> auditor javap 直读：`if_acmpne 38`（38 = return），非 NORMAL 时**整段检查体不执行**。
> 行号口径：**CFR 件 L533-546 ≡ class LineNumberTable L511/512/513/523**（见 §11）。

| # | 路径 | 为何不受配额门 | **操作约束** | 证据（CFR 件行号） | 状态 |
|---|---|---|---|---|---|
| 1 | **`create(sourceType=null)`** | L418 门在 L429-431 默认化**之前**；门判 `isNull(dto)` **而非** `isNull(sourceType)` → DTO 非 null 且 `null != NORMAL` → 跳过 → L430 默认化为 FORM → L458 INSERT | **不可同时指定 `orgId`/`creator`**（否则 `checkAssignOrgIdAndCreator` **L482** 抛「非低代码系统管理员，不可指定应用所属机构和所属人!」）。原因：该校验在 **L417** 执行，早于 L429-431 默认化，此时 `sourceType` 仍为 `null`，L479 的 FORM 早退**不生效** | `ApplicationService` L414-458 + L478-485 | **STATIC_CLOSED**（门序缺口） |
| 2 | **`create(sourceType=FORM)`** | L534 首条件 `NORMAL == FORM` 不成立 → 整块跳过检查体 | **无** orgId/creator 限制（L479 显式 FORM 早退） | L533-546 + L478-485 | **STATIC_CLOSED** |
| 3 | **`saveAsNewDesign`** | `SchemaManager.saveAs` **L232** 断言源应用必为 FORM → 链路 `dto.sourceType` 恒为 FORM → 门体跳过 | 不受 create 入口的 orgId/creator 约束（不走 `create`）；但需过 **L1545** RELEASE+SUCCESS 与 **L1548** 一致性检查（见下「通路 3」） | L1541-1560 + L229-249 | **STATIC 闭合，待 LIVE** |

> **⚠ 第 4 道门作用域（P3-B 必检，勿遗漏）**：**仅路径 A / B（`create` 入口）需过「第 4 道门」——orgId 无条件覆写**（详见下节）。
> **路径 C（`saveAsNewDesign`）不受此门**：`copyCreate` 不调 `appFeatureHandlerFacade`，且 L501 是「仅 null 才补」而非无条件覆写。
> 该门与上表的「操作约束」列**并存**，不是替代关系：操作约束管「能不能带 orgId/creator」，第 4 道门管「环境里 loginOrgId 是否有效」。

##### 第 4 道门：`orgId` 无条件覆写（2026-10-18 HANDOFF-09 补遗，auditor 轮29 发现）

> **三通路表此前漏登的一道门。** 该门在 `appFeatureHandlerFacade.buildApplicationDto4Create(dto)` 内部，
> 位于**配额门之后、INSERT 之前**，且**无任何 sourceType 条件分支把它跳过**。

> **⚑ 作用域 = 仅路径 A / B（`create` 入口）——`copyCreate` 无此门**（2026-10-18 amendment-1 收窄，auditor 轮30 复核、本侧独立重验）
> - `appFeatureHandlerFacade` 在 `ApplicationService` 全类**只有 1 个调用点**：`L439`（位于 `create` 方法内）→ **通路 A/B 受此门**
> - `copyCreate`（L487-527）**不调 facade**、**无 `LONG_MINUS_ONE` 检查**，且其 orgId 是「**仅 null 才补**」（见下）→ **通路 C 不受此门**
> - ⚠ 防误读：**不得把本节读成「FORM 族全路径都撞此门」** —— 只有走 `create` 的 A/B 撞。

**代码事实（两父类，逐字）**

`AbstractFormlAppFeatureHandler.buildApplicationDto4Create` **L243-249**：
```java
L243  Long loginOrgId = RequestContext.get().getLoginOrgId();
L244  log.info("创建应用上下文获取 loginOrgId:{}", loginOrgId);
L245  applicationDto.setOrgId(loginOrgId);                                  ← 无条件覆写
L246  if (Objects.equals(applicationDto.getOrgId(), Constants.LONG_MINUS_ONE)) {
L247      log.error("创建表单应用所属机构Id:{}", applicationDto.getOrgId());
L248      throw new BusinessException("BOOT_1000").addError("表单应用所属机构信息异常");
L249  }
```

`AbstractNormalAppFeatureHandler.buildApplicationDto4Create` **L229-231**：
```java
L229  Long loginOrgId = RequestContext.get().getLoginOrgId();
L230  log.info("创建应用上下文获取 loginOrgId:{}", loginOrgId);
L231  applicationDto.setOrgId(loginOrgId);                                  ← 同样覆写，但**无 -1 检查**
```

**对照：通路 C 的 `copyCreate` L499-503（不是覆写，是条件补值）**
```java
L499  Long loginOrgId = RequestContext.get().getLoginOrgId();
L501  if (dto.getOrgId() == null) {
L502      dto.setOrgId(loginOrgId);                                        ← 仅 null 才补
L503  }
```
→ C 的 `orgId` 来自源应用 schema 深拷贝，**通常非 null → L501 不触发**；且无 `LONG_MINUS_ONE` 校验。

**时序（决定「落库 orgId 是谁」的关键，仅 A/B）**

```
L439  this.appFeatureHandlerFacade.buildApplicationDto4Create(dto);   ← 覆写发生在这里（orgId := loginOrgId）
L450  if (ApplicationSourceEnum.NORMAL == dto.getSourceType()) {
L451      if (assignOrgId != null) { udcApplication.setOrgId(assignOrgId); }   ← 仅 NORMAL 才用入参回填
L457  }
...    L458  this.dao.create((Object)udcApplication);                 ← INSERT
```
→ **FORM 族不回填**，故 `udc_application.orgId` **落库值 = `loginOrgId`（覆写值），不是入参值**。
→ NORMAL 族若 `assignOrgId != null` 会用入参覆盖回来；否则同样是 `loginOrgId`。

**前置实测项（P3-B 发请求前必须确认）**

> **探针发请求前必须确认 `RequestContext.get().getLoginOrgId() != -1`。**
> - **须真实调用 `RequestContext.get().getLoginOrgId()`，不可用 DB `org_id` 查询替代** ——
>   两者来源不同（一个是请求上下文，一个是落库值），**DB 正常 ≠ 上下文正常**。
> - 路径 A（`create(null)`）与路径 B（`create(FORM)`）**都会撞此门**（FORM 族走 Forml 父类，有 -1 检查）。
> - `loginOrgId == -1` → **抛 `BOOT_1000`「表单应用所属机构信息异常」**，请求根本到不了配额门之后的成功路径。
> - **失败时的归因纪律**：先查**环境侧**（当前凭据账号的 loginOrgId 是否为 -1），**勿误判为「通路失效 / 静态结论错了」**。
> - 该检查是 **P3-B LIVE 前的环境前提**，不是通路本身的缺陷。

**三道门的关系（避免混读）**

| 门 | 判据 | 失败表现 | 能否被请求参数绕过 | 作用域 |
|---|---|---|---|---|
| 配额门 `checkTenantLicenseAppCount` | `dto.sourceType` 是否 NORMAL | `UDC_APP_0030` | **是**（FORM/null 跳过） | A/B（C 也经 L491，但 C 的 sourceType 为 FORM → 同样跳过） |
| orgId/creator 校验 `checkAssignOrgIdAndCreator` | **L417 时**的 `dto.sourceType` | 「非低代码系统管理员…」 | 路径 B 可（FORM 早退），路径 A 不可 | 仅 `create`（A/B） |
| **第 4 道门 orgId 覆写** | **环境** `loginOrgId` | `BOOT_1000`「表单应用所属机构信息异常」 | **否**（无 sourceType 分支） | **仅 A/B**（`copyCreate` 不调 facade） |


##### 通路 1 补证：`create(null)` 门序缺口的 4 条支撑（逐条独立复核）

```
L418: this.checkTenantLicenseAppCount(dto);                    ← 门（最先执行）
L429: if (Objects.isNull(dto.getSourceType())) {
L430:     dto.setSourceType(ApplicationSourceEnum.FORM);        ← 门之后才补默认值（门序缺口点）
L431: }
L443: if (Objects.isNull(dto.getSourceType()) || !containCode(...))   ← 此时已非 null，FORM=1 通过
L458: this.dao.create((Object)udcApplication);                 ← INSERT
```

1. **`buildApplicationDto4Create(dto)` 不回写 sourceType**
   `AbstractFormlAppFeatureHandler` **L232-250** 方法体内只设 `name / basePackage / copVersion / orgId`；
   `AbstractNormalAppFeatureHandler` **L219-229** 只设 `name / copVersion / orgId` → **方法体内 `setSourceType` 0 命中**。
   > 复核方法说明：两文件**全文**各有 2 处 `setSourceType`（Forml: L221 `dependentComponentDto` / L316 `dependentStaterDto`；
   > Normal 同类），但**均不在目标方法体内**、且是别的 DTO → 不构成回写。**勿用文件级 `grep -c` 回答方法级问题。**

   > **覆盖范围补强（2026-10-18 HANDOFF-09 改动 2，auditor 轮29 复核）**：
   > 上述结论**覆盖全部 8 个实现类**（不是只覆盖两个父类）：
   > - **两父类持实现**：`AbstractNormalAppFeatureHandler` / `AbstractFormlAppFeatureHandler`（`buildApplicationDto4Create` 实现在此）
   > - **6 个子类继承、均不 override**：`FormAppFeatureHandlerImpl` / `StandardAppFeatureHandlerImpl` /
   >   `LayoutAppFeatureHandlerImpl` / `OnlyPageAppFeatureHandlerImpl` / `IntegrationAppFeatureHandlerImpl` / `BusinessAppFeatureHandlerImpl`
   >   → 本侧独立复核：6 子类文件内 `buildApplicationDto4Create` 命中 **均为 0**（全部继承父类实现，无覆盖）
   > - 全树 `*AppFeatureHandler*.java` 恰好 **8 个**（2 父类 + 6 子类），**无第 9 个实现类**
   > → 故「父类方法体内 `setSourceType` 0 命中」即可覆盖全部实际分派路径。
2. **`create` L443 `containCode(sourceType.code())` 只验码值 ∈ {0,1}** → FORM(1) **通过**（不拦）。
3. **`ApplicationDto.sourceType` 无 `@NotNull`**（javap：L66-67 为 `getSourceType()`/`setSourceType()`，字段声明 L17；`@NotNull` 出现在 `terminalType` 相关注解、groups=Create，**不在 sourceType 上**）；
   `ApplicationAppServiceImpl.create` **L180-183** 直传 `request.getData()`（无补值/无校验）。
4. **`checkAssignOrgIdAndCreator` L478-485 —— 时序敏感，两种入参结论不同**（本轮先写错、已按 main 纠正，留痕）
   ```
   L414  public Long create(ApplicationDto dto) {
   L415      Long assignOrgId = dto.getOrgId();
   L416      Long assignCreator = dto.getCreator();
   L417      this.checkAssignOrgIdAndCreator(assignOrgId, assignCreator, dto);   ← 此刻 sourceType 仍为入参原值
   L418      this.checkTenantLicenseAppCount(dto);
   L429      if (Objects.isNull(dto.getSourceType())) {
   L430          dto.setSourceType(ApplicationSourceEnum.FORM);                    ← 默认化晚于 L417
   L431      }
   ```
   ```
   L478  private void checkAssignOrgIdAndCreator(Long assignOrgId, Long assignCreator, ApplicationDto dto) {
   L479      if (ApplicationSourceEnum.FORM == dto.getSourceType()) {
   L480          return;                                                    ← FORM 早退
   L481      }
   L482      if (!(assignOrgId == null && assignCreator == null || isUdcSystemAdmin())) {
   L483          throw "非低代码系统管理员，不可指定应用所属机构和所属人!"
   L484      }
   ```

   | 入参场景 | L417 时 `sourceType` | L479 判断 | 结果 |
   |---|---|---|---|
   | **显式传 FORM**（通路 2） | `FORM` | `FORM == FORM` 真 | **早退 → 无 orgId/creator 限制** |
   | **传 null**（通路 1，门序缺口） | **`null`** | `FORM == null` **假** | **不早退 → 落 L482：指定了 orgId/creator 且非系统管理员 → 抛「非低代码系统管理员，不可指定应用所属机构和所属人!」** |

   → **通路 1（`create(null)`）的操作约束：不可同时指定 `orgId`/`creator`**（否则 L482 抛错）。**这是 P3-B LIVE 探针发请求的前提条件，不能漏。**
   → **通路 2（`create(FORM)`）：无该限制**（L479 显式 FORM 早退）。
   > **自纠留痕（如实登记）**：本契约初稿在此处写「FORM 连 OrgId/Creator 限制都不适用」，并把它当作对通路 1 有利的支撑 ——
   > **该结论只对「显式传 FORM」成立，对「传 null」不成立**。错因是**方法级结论忽略了调用时序**（`checkAssignOrgIdAndCreator` 在 L417 执行，
   > 早于 L429-430 的默认化）。由 main 复核指出，本侧已复核确认并改正。**性质与前一条「文件级 grep 回答方法级问题」同类：结论正确但用错了适用域。**

**定级：STATIC_CLOSED。明写「不是 LIVE PASS」。**
> 未闭合项（不得越级）：`AppFeatureHandlerFacade` 分派实现在**另一 jar**（不在当前 `docs/audit/artifacts/scratch-migrated/cfr-r31b` 反编译树）；
> 网关/鉴权是否另设白名单**未验**。故**不得写「可以建应用」「已打通」「可绕过」**。

##### 通路 3 可用源应用：9 → **7**（数字更正）

- 判据：`saveAsNewDesign` **L1544** → `AppVersionService.selectByAppIdAndDeployType` **L272-281**，
  查询带 **`state == DeployStateEnum.SUCCESS`** 过滤。
- `DeployStateEnum` = `UNPUBLISHED(-1) / PUBLISHING(0) / SUCCESS(1) / FAIL(2)`。
- test2 实测 `deploy_type=2` 的 FORM 应用 **9 个**，其中 `state=1` 的 **7 个**：
  `912667056861626502` / `3890487949927400401` / `5150746664960478913` / `5746064954083329093` /
  `6712017922882617636` / `7022003764439498867` / `7324620281389731265`
- 另 2 个非 SUCCESS → L1545 抛 `UDC_APP_0033`：`6388488623384448921`（state=0 发布中）/ `5245855677018033156`（state=-1 未发布）
- **口径差异（两个数都记，防后人再混）**：
  - **9** = 「有 RELEASE 发布记录」口径（`udc_deploy_record.deploy_type=2` 计数）
  - **7** = 「能过 L1545」口径（额外要求 `udc_app_version.state=SUCCESS`）
  → **只有 7 个是可作为 `saveAsNewDesign` 源应用的候选。**
  > 本侧未直连 DB，上述 9/7 均**采信 main/auditor 实测**，未独立复现；标注为采信项。

##### 已知风险（两条，均非结构性阻断）

1. **`checkHasNewEntityOrAttributeAfterDeployed`（L1548）不是「永不阻断」**
   对**当前给定样例**不阻断（源应用 RELEASE 后新增实体 0 / 改字段 0），但任何**发布后改过实体/字段**的源应用都会撞。
   属**可选源应用过滤条件**，非结构性阻断。
2. **`ImportDelegateColi.saveAs` L306-320 的 try/catch —— 更正：不是「吞异常」**
   > **HANDOFF-08 原文称「任一 handler 抛错被吞并记日志」「静默降级 = 数据质量风险」。本侧复核后认为该描述不准确，如实登记：**
   - L315-319 catch 块内容为：`log.error(errorMsg, ex);` **紧接着 `BootException.throwIt(errorMsg, ex);`**
   - `BootException.throwIt(String, Throwable)`（boot-core-5.3.358 反编译）：`BootException bootException = new BootException("BOOT_3000", cause); bootException.setMessage(message); **throw bootException;**`
   - 且 `ImportDelegateColi.saveAs` 标 `@Transactional(rollbackFor={Exception.class})`（L278），调用方 `SchemaManager.saveAs` **无 try/catch**（L247 直调）
   → **异常会重新抛出并触发事务回滚，不是静默降级。**
   → 准确表述：**「catch 内 log + rethrow，明细进日志、异常仍上抛 → 不构成静默数据降级；但对可达性也无『支持』作用」**。
   > 本侧未做 LIVE，无法确认 handler 内部是否有**更内层**的 try/catch 吞错；若存在，则风险仍在。**该未闭合点如实保留。**
3. **通路 C 的 `loginOrgId = -1` 传播 —— 理论风险，当前无实例**（2026-10-18 amendment-1 留痕）
   通路 C（`saveAsNewDesign`）的 `copyCreate` L501 是「**仅 `dto.getOrgId() == null` 才补 `loginOrgId`**」，不是无条件覆写；
   若源应用 `orgId` 恰为 `null`，则仍会把 `loginOrgId`（可能为 -1）补进去，且 C 链上**无 `LONG_MINUS_ONE` 校验** → 理论上可传 -1。
   **当前状态：全库 `org_id = -1` 为 0 实例**（main/auditor 实测），故为**理论风险、非现实阻断**。
   > 该条不改变通路 C 的「STATIC 闭合，待 LIVE」定级；仅登记边界。

### 7.3 「草稿面」不构成 appId 来源（推翻既有记账）

P2 曾把 `app-draft/create` 记为「建应用 LIVE PASS」的主线绕行。main 轮7 只读 DB + 字节码核查后推翻，本契约采信并落实：

| 事实 | 证据 | 含义 |
|---|---|---|
| `app_data_draft` 表 **0 行**；列 = `id/tenant_id/create_time/update_time/version/data_id(varchar)/user_id/draft_data(longtext)` | main 轮7 只读 DB | **纯键值草稿表，无 `udc_application` 外键** |
| 类级 `@RestApiOperation("应用草稿")`；`exist`="当前用户存在草稿"；`select`="查找当前用户的草稿"；`delete`="删除当前用户指定dataId的草稿"；`deleteAll`="删除所有指定dataId的草稿"；`deleteTimeout`="删除所有过期的草稿(3个月)" | `docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt` 常量池（本片按 GBK 逐字解码复核，7 条注解文案全对上） | 语义 = **当前用户的草稿暂存**，非应用实体 |
| `AppDraftController` 方法全集：`createOrUpdate / exist / select / delete / deleteAll / deleteTimeout`（**无** publish / online / deploy） | 同上 javap | 草稿面**没有**上线或转正动作 |

**推论（三条，缺一即错）**：
1. `app-draft/create` **不产生 `udc_application` 行** → 它给不出本 op 需要的 `appId`。
2. `AppDraftDto` 的 `dataId` 是 **varchar 键**，`DeployNormalDto.appId` 是 **Long** → 类型与语义双重不兼容，**喂不进去**。
3. 因此「草稿 `dataId` → 上线」这条链路**不存在**（不是「未定位」，是**结构上不存在**）。
   > 修正上一稿措辞：本契约初稿 §8 曾写「转正端点仍未定位」，属**过宽表述**。正确说法是：`getPush`/`appOnline` 面**没有** dataId→appId 的转换路径；
   > 若要找「草稿转正」，只能在**其他控制器**里找（本片未取证，不外推）。

### 7.4 对 P3 的含义（两条 appId 来源全闭）

| appId 来源 | 状态 | 阻断性质 |
|---|---|---|
| 既有应用（如 target `datamigration9000000000000000001`） | **BLOCKED** | **授权门**：`/service/{appName}/` → `server_403`（应用内网关鉴权；门 2 `APP_DEPLOY` / 门 0 `@HasRole`） |
| 新建应用（`POST /service/udc/application`） | **BLOCKED（上限未决）** | **配额门**：`UDC_APP_0030`。`COUNT(*)` = 10 已实测；**生效上限 10 或 11 未决**（`ctp_sandbox_config` 两行冲突，需 LIVE 确认）→ 上限=10 时必抛；上限=11 时还可建 1 个（见 §7.2 未决块） |
| 草稿面转正 | **不存在** | 结构性：草稿表无外键、DTO 无 appId、控制器无上线动作 |

→ **本 op 在 test2 当前无可用 appId 来源。** 出路（**释放配额 / 确认并调整上限 10-or-11 / 直接授权 target 运行态 / 承认不可达**）
**均属 HUMAN 决策**，agent 不自行选、不自行删应用、不改环境配置。
> 2026-10-17 轮14 补：原三条出路（A 释放配额 / B 提 createAppNum / C 承认不可达）已调整为四条 ——
> B 因上限未决（§7.2、§9.7）改问法为「确认生效上限是 10 还是 11」，并新增 **D：直接授权 target 运行态**（main 建议优先，
> 因其不经配额门、也不需新建应用，直接解掉既有应用通道）。

## 8. 与 P3 验收的关系（不越界声明）
- 本件是**契约面**产物。验收标准第 3 条「建应用→发布→部署→运行态 URL 可访问」**未因本件达成**。
- 已达成的仅是：发布动作的 op/路径/入参/门链/pushEnv 前置**已确定且可复核**（STATIC）。
- 仍缺：门 0（角色）/ 门 2（`APP_DEPLOY` 授权）需 LIVE 或授权输入；`ON_ONLINE` pipeline 实际行为 UNVERIFIED；
  appId 来源见 §7（两条全闭）。
- **禁写**：「发布已打通」「可上线」「pushEnv 已验证」「app-online 能建应用」。

## 9. 未验证项（如实登记）

1. `@HasRole` 校验实现类未定位（仅见注解值），当前账号是否具备 4 角色之一 —— **UNVERIFIED**。
   > 状态收窄（2026-10-17，采纳 main DECISION 追加要求 2）：同属框架层的另一判定 `Apps.isRunInTest()` **已解**
   > （`boot-core-5.3.358` `Apps` L599-606 = PropertySources 含 `"Inlined Test Properties"`；test2 为 false，门 2 不被跳过）。
   > 但 `isRunInTest` **不在 `@HasRole` 链上** —— `@HasRole` 本身仍在 Spring Security / 拦截器层，**实现类仍未定位**，本条如实保留。
   > 即：框架层两条判定中，**一条已解（isRunInTest）、一条未解（@HasRole）**，不得合并表述。
2. `udcAppRightsConfig.isEnable()` 实配 —— **UNVERIFIED**（未读该配置类）。
   > 原条目并写的 `Apps.isRunInTest()` **已解**（见上第 1 条收窄块）：`isRunInTest()` = false → **门 2 不被跳过**。
   > 剩余未知仅 `isEnable()`：若它为 false 则门 2 整体不执行（与「被 isRunInTest 跳过」是不同机制，不可混读）。
3. `ON_ONLINE` pipeline（`startOnlinePipeline`）内部行为与失败语义 —— **UNVERIFIED**（本片不展开）。
4. ~~草稿 `dataId` → 正式 `appId` 的转正端点未定位~~ —— **已修正为结构性不存在**（见 §7.3）。`appOnline` 只收 `appId`；
   草稿表无 `udc_application` 外键、`AppDraftDto.dataId` 为 varchar、`AppDraftController` 无上线动作。
   是否在**其他控制器**存在草稿转正路径 —— **本片未取证，不外推**。
5. Nacos `public-common` 实配为 2026-09-03 采集件，**可能已漂移**；P3-B 前若需强口径应重采（读面，非本片边界）。
6. 门 4 `validDeploy` 的 `previousSchemInfo.buildVersion` 来源字段链未逐层展开 —— 只登记判据，未追 pipeline 内部。
7. **配额：数值已定、上限未决（2026-10-17 轮14 改写，采纳 main 要求）**：
   - **已确定**：`COUNT(*) WHERE source_type=0 AND json_prefab=0` = **10**（main 轮7 只读 DB 实测；本片未直连 DB，按 main 实测采信）。
   - **未决**：**生效上限是 10 还是 11**。`ctp_sandbox_config` 两行冲突
     （`id=-8112660841495312922, tenant_id=-999, create_app_num=10, version=1` /
     `id=-999, tenant_id=-999, create_app_num=11, version=3`）；
     当前应用表 `tenant_id` 恰为 `-8112660841495312922` → 按 id 匹配取 10（满）；按 `tenant_id=-999` 匹配则两行都命中、**无法唯一**。
     读它的 `SandboxConfigService`（`com.seeyon.boot.starter.sandbox`）**不在本地**（575 jar 全扫 0 命中）→ **需 LIVE 确认**。
   - **结论强度**：**若生效 11 则当前 10 个尚未满，仍可再建 1 个**；若生效 10 则已满、必抛 `UDC_APP_0030`。
   - 记账按更严格的 10/10 满，但**不得写成绝对确定**；HUMAN 若变更配额/上限，此条须重测。
   > 本条替代原表述「`createAppNum` = 10 为既有登记 + main 实测」—— 原表述把未决上限当成了确定值。
8. **「进没进 pod」判据补强（main 2026-10-17 22:59 实测，采纳其可入契约建议）**：
   响应头字段名实测为 **`Traceid`**（首字母大写 T，其余小写），且 body 内同名 `traceId` **值与响应头相同**。
   - 对照应用（已部署 `app9000000000000000001`）：round16 两发均 `traceIdHdr = envelope.traceId`
     （`3278392001468303548` / `3278392024771856572`）→ **有 `Traceid` 头**。
   - target `datamigration9000000000000000001`：`server_403` 时 `trace_hdr = null` → **无 `Traceid` 头**。
   → **「对照应用有 `Traceid` 头 / target 无」是「是否进入 pod 业务链」的硬区分**，强于仅记 `hdr=null`。
     本契约 §5.4 反证表中判「是否进 pod」时按此口径；P3-B 若需判路由/授权层，优先看该头而非仅看 HTTP 状态。

## 10. 复现命令（只读）

```bash
# 1) Controller 两形态 + 类级注解
sed -n '247,340p' docs/audit/artifacts/udc-web-5.3.517-contracts/DeploymentController.javap.txt
sed -n '376,395p' docs/audit/artifacts/udc-web-5.3.517-contracts/DeploymentController.javap.txt

# 2) appOnline 全文 + validEnv/validDeploy + appDeltaDeploy 反例
sed -n '196,258p' docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/deployment/DeploymentService.java
sed -n '321,338p' docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/deployment/DeploymentService.java

# 3) DTO 字段表
cat tools/jars/udc-web-classes/DeployNormalDto.txt tools/jars/udc-web-classes/DeployParamDto.txt

# 4) pushEnv 判定链（boot-starter-environment 5.3.358）
#    解包 → CFR → getPush/getCurrentModel/validateEnv
unzip -o -q "<MAVEN_REPO>/com/seeyon/boot-starter-environment/5.3.358/boot-starter-environment-5.3.358.jar" -d docs/audit/artifacts/scratch-migrated/env358
java -jar "<PATH>" \
  docs/audit/artifacts/scratch-migrated/env358/com/seeyon/boot/starter/system/env/service/CtpSystemEnvUdc.class --outputdir docs/audit/artifacts/scratch-migrated/env358/out

# 5) 权限门
sed -n '52,90p' docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/collaboration/filter/UdcAppOpsCheck.java

# 6) test2 实配
cat docs/audit/evidence/nacos-public-common.yaml
python -c "import json;print([f for f in json.load(open('docs/audit/evidence/nacos-test2-manifest.json'))['files'] if f['dataId']=='public-common'])"

# 7) 配额门（§7.2）字节码
grep -n "checkTenantLicenseAppCount" -A 20 docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/entity/domain/service/ApplicationService.java | sed -n '1,40p'
grep -n "APP_COUNT_EXCEEDED" docs/audit/artifacts/scratch-migrated/cfr-r31b/com/seeyon/udc/exception/AppErrorCode.java

# 8) 草稿面语义（§7.3）—— javap 常量池中文按 GBK 解码
python -c "
raw=open('docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt','rb').read()
for line in raw.split(b'\n'):
    if b'Utf8' in line:
        try:
            s=line[line.index(b'Utf8')+4:].strip().decode('gbk')
            if any('\u4e00'<=c<='\u9fff' for c in s): print(s)
        except Exception: pass
"
```

## 11. 版本锚（四单元禁混写）

### 11.0 行号基准声明（2026-10-17 HANDOFF-08 新增，auditor 提出、采纳）

> **本文所有行号，除特别标注外，均为 `docs/audit/artifacts/scratch-migrated/cfr-r31b`（CFR 反编译件）坐标，不是 class 的 LineNumberTable 坐标。**
>
> 两套坐标系存在稳定偏移。已确认的对应关系：
>
> | 对象 | CFR 件坐标 | class `javap -l` LineNumberTable | 说明 |
> |---|---|---|---|
> | `checkTenantLicenseAppCount`（配额门体） | **L533-546** | **L511 / 512 / 513 / 523** | `if_acmpne 38`；38=return |
>
> **纪律**：
> 1. 引用契约/事实格中的行号时，默认按 **CFR 件坐标**理解。
> 2. 需与 class 字节码对账（如 auditor 独立 javap 复核）时，**以 LineNumberTable 为准**，并按本表换算。
> 3. **不得混用两套坐标做「行号不一致 = 事实错误」的判定。**
>
> 原因：CFR 件由另一版本 class 反编译或含行号偏移，属**坐标基准差异，非事实错误**。

| 单元 | 版本 | 出处 |
|---|---|---|
| Controller / DeploymentService | **udc-web 5.3.517** | 本地 Maven `<MAVEN_REPO>/com/seeyon/udc-web/5.3.517`；javap class_sha256 `4b72a4fb...cbb0cfe8` |
| **DTO（DeployNormalDto / DeployParamDto / DeployTypeEnum 等）** | **udc-common 5.3.517** | 本地 Maven `<MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar`。**补正（采纳 auditor VERDICT-handoff03 补正 2，本侧独立验证）**：`unzip -l udc-web-5.3.517.jar \| grep DeployNormalDto` → **0 命中**；`DeployNormalDto.class` 只在 `udc-common-5.3.517.jar` 内。原稿只标采集目录 `tools/jars/udc-web-classes/`，**目录名与实际来源 jar 不一致**，此处按真实来源 jar 登记 |
| pushEnv 判定链 | **boot-starter-environment 5.3.358** | 部署态构件清单实证：`docs/audit/udc-semantics/DEPLOYED-EXPOSURE-CENSUS.json` `marker_jars` 含该 jar 全名。**注意环境口径**：该清单由 `DEPLOYED-LIB-INVENTORY.json` 标注 `namespace=lowcode-test` / `container_version=5.3.517`（`kubectl exec` 取 `udc-assemble.jar` → `BOOT-INF/lib`，544 jar），**是 lowcode-test 命名空间的部署态，不是 test2** |
| test2 运行镜像 | **5.3.496** | `config/environments.yaml` `environments.test2.udc_image_version` |

> **四单元禁混写（本轮再校准）**：
> - `udc-web 5.3.517` 是**本地 Maven 静态样本**（Controller / DeploymentService 字节码来源）。
> - `udc-common 5.3.517` 是**本地 Maven 静态样本**（DTO 来源）。**注意**：`tools/jars/udc-web-classes/` 只是**采集目录名**，
>   不代表其中 class 都来自 udc-web —— DTO 实际来自 udc-common。
> - `boot-starter-environment 5.3.358` 是 **lowcode-test 命名空间部署态**构件清单里的实证版本，用于 pushEnv 判定链源码。
> - `test2` 运行镜像登记为 **5.3.496**，且 `agent-version-audit.md` L36/L39 明确：5.3.496「仅在 inventory 可用版本列表中观察到，未进入实际样本集」，
>   **不得写成已采样实现事实**。
>
> 推论（必须如实登记）：
> 1. 本契约的门链/pushEnv 结论建立在 **5.3.517 本地样本 + 5.3.358 部署态构件** 的组合上，**不是 test2 运行镜像的样本**。
> 2. `CtpSystemEnvUdc.getPush` 的 4 项白名单是**硬编码常量**，跨 boot-starter-environment 小版本高度稳定，
>    但「test2 的 boot-starter-environment 恰为 5.3.358」**本片未取证**（无 test2 pod `BOOT-INF/lib` 清单在盘）。
>    → §5.3「门 1 在 test2 不会触发」的强度应理解为：**按 Nacos 实配 + 5.3.358 字节码推演成立**；若 test2 实际用的 environment 构件版本改了 `getPush` 白名单，结论需重算。
> 3. 该不确定性**不影响 §5.3 的核心推论方向**：Nacos 实配 `currentEnv=development` + `deploymentEnvStr=development-implement-prod`
>    恰好落在 4 项白名单**唯一一组以 development 开头的项**上，属「按设计正常配置」，非边界规避。
