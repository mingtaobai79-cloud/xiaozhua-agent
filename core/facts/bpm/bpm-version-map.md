# bpm-facade 3.12.101 ↔ udc-starter-runtime 5.3.517 接口对照（flow 域第 4 格）

> 基线：本任务总目标（本会话 `inputs/desktop-source/TASK-GOAL.md` + `main/ROUTE.md` §3 P2 spec / §1.7 / §1.8）+ `HANDOFF-2`。
> 目标仓库 `<SEEYON_AGENT_ROOT>`。九段式能力事实文档（本任务交付物第 2 件，`core/facts/bpm/bpm-version-map.md`）。
> 本件**只做 bpm-facade 3.12.101 与 udc-starter-runtime 5.3.517 的静态字节码接口对照**（纯静态，无 LIVE 探测、不涉凭据）；
> 已 PASS 冻结的格① `engine-behavior.md`（16072 B / sha256 `7908a94d…`）与前两格 `flow-node-tree.md` / `data-flow-map.md` 绑定字节均不动。
> 证据先落盘：`core/facts/bpm/evidence/bpm-version-map-static-20260927T100255Z.json`（14943 B / sha256 `862fc7d3…`，436 行 / LF）先落盘，本格后写。
> 两版本 3.12.101 与 5.3.517 是**两个独立证据单元，禁合并**；接口对照 ≠ 运行时调用关系（沿用前两格 limitations，未升级为行为断言）。

---

## 1. Capability

**bpm-facade 3.12.101 对 UDC runtime 暴露的接口（`com.seeyon.bpm.api.udc.BpmUdcApiService`）与 udc-starter-runtime 5.3.517 的注入/调用对照**，以及入/出 DTO 字段 ↔ 5.3.517 调用点的静态映射。

- **性质**：静态字节码对照（反编译 `.java` + manifest + jar 哈希），**无 LIVE 探测、不涉凭据**；本环节是「契约/接口对照」层，**非运行时调用断言**。
- **观测面**：3.12.101 facade 侧（`bpm-facade-3.12.101-*.java`，反编译件）↔ 5.3.517 runtime 侧（`udcrt-5.3.517-*.java`，反编译件 + jar）。
- **对照结论概览**（实测枚举，非外推）：
  - **接口**：`BpmUdcApiService` 声明 **9 个方法**（= 6 个 `*ForUdc` + 1 个 `saveDraft` + 2 个 `getNodePermission*`）；5.3.517 侧 `ApproveFeatureService` / `ApprovalStateChangeListener` 注入该接口并**实测 6 处调用点**。
  - **入/出 DTO**：3 个 UDC DTO（`BpmSendUdcDto` / `BpmSaveDraftUdcDto` / `BpmTriggerFlowUdcRequestDto`，包 `com.seeyon.bpm.dto.approval`）字段在盘可读。
  - **回流**：BPM 事件 → UDC 经 `UdcBpmProcessService`（4 方法 `processBpm*`）+ `UdcBpmProcessServiceImpl`（在盘）。
- **实测计数纪律**：接口 9 方法、调用点 6 处、DTO 3 个——均为**在盘实测枚举**，未照抄任务文「16 契约」口径。

## 2. Version

- **3.12.101 侧（证据单元 A）**：`bpm-api-decompile-manifest.json` `artifact=bpm-facade` / `version=3.12.101` / `source_sha256=26b312fdd40cc921a4cd8d08239f6b8d857c02a5ac8d4db271d07f6fcbd98af0`。
  - **jar 本体缺盘**：`<MAVEN_REPO>/com/seeyon/bpm-facade/` 在盘仅 `5.3.374/`，**`3.12.101/` 不存在**（实测目录枚举）。→ 3.12.101 侧证据**止于反编译 `.java`，字节码层不可再深验**（§7 强制登记）。
- **5.3.517 侧（证据单元 B）**：`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar` 在盘，**861880 B / sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`**（实测，可 javap 补验）；反编译件 `udcrt-5.3.517-*.java` 4 件 + `udc-starter-runtime-5.3.517-*.java` 在盘。
- **两单元独立**：3.12.101（门面/契约层）与 5.3.517（runtime 调用侧）为不同制品、不同版本，**禁合并为一个证据单元**。

## 3. Input（对照两侧的接口与 DTO 定义）

### 3.1 3.12.101 facade 侧接口 `com.seeyon.bpm.api.udc.BpmUdcApiService`（`bpm-facade-3.12.101-BpmUdcApiService.java`，3366 B，sha256 `5028e167…`，manifest 记录）

| 方法 | 行号 | abstract? | 签名（在盘原文） |
|---|---|---|---|
| `sendForUdc` | L46 | 是 | `SingleResponse<BpmApiSendApiResponseDto> sendForUdc(SingleRequest<BpmSendUdcDto>)` |
| `saveDraft` | L48 | 否（default） | `SingleResponse<BpmSaveDraftUdcResponseDto> saveDraft(SingleRequest<BpmSaveDraftUdcDto>)` |
| `triggerFlowForUdc` | L52 | 否（default） | `ListResponse<BpmTriggerFlowUdcResponseDto> triggerFlowForUdc(SingleRequest<List<BpmTriggerFlowUdcRequestDto>>)` |
| `prefixForUdc` | L56 | 否（default） | `SingleResponse<BpmPrefixForUdcResponseDto> prefixForUdc(SingleRequest<BpmPrefixForUdcDto>)` |
| `repealForUdc` | L60 | 是 | `SingleResponse<Void> repealForUdc(SingleRequest<BpmOperationRepealUdcDto>)` |
| `stopForUdc` | L62 | 是 | `SingleResponse<CommonResultDto> stopForUdc(SingleRequest<BpmStopDto>)` |
| `deleteCaseByIdForUdc` | L64 | 是 | `SingleResponse<Void> deleteCaseByIdForUdc(SingleRequest<Long>, SingleRequest<Long>)` |
| `getNodePermissionOperation` | L66 | 否（default） | `ListResponse<BpmNodePermissionResponseDto>` |
| `getNodePermission` | L70 | 否（default） | `SingleResponse<BpmNodePermission4PageDto>` |

### 3.2 入/出 DTO（3.12.101，包 `com.seeyon.bpm.dto.approval`，反编译在盘，**manifest 未覆盖 → 引用自测 sha256**，§7-3）

| DTO | 文件（raw 字节 / sha256 前 8） | 成员行号（在盘，全部成员） | 成员数 |
|---|---|---|---|
| `BpmSendUdcDto` | `bpm-facade-3.12.101-BpmSendUdcDto.java`（8713 B / `2929db4b…`） | L31/33/35/37/40/42/44/46/49/51/53/55/57/59/61/63 | 16 |
| `BpmSaveDraftUdcDto` | `bpm-facade-3.12.101-BpmSaveDraftUdcDto.java`（6787 B / `e467675e…`） | L29/31/33/35/38/40/42/45/47/49/51/53/55/57/59/61 | 16（含 L29 常量） |
| `BpmTriggerFlowUdcRequestDto` | `bpm-facade-3.12.101-BpmTriggerFlowUdcRequestDto.java`（7311 B / `557f1582…`） | L25/27/29/31/34/36/38/41/43/45/47/49/51/53 | 14（含 L25 常量） |

- `BpmSendUdcDto` 字段原文（在盘 L31-63，全部 16 成员）：`templateId` / `rootEntityId` / `rootEntityName` / `caseId` / **`userId`（内联 `@NotNull` 必填）** / `commentDto` / `preMatchRequestDto` / `formData(Map)` / **`formRecordId`（内联 `@NotNull` 必填）** / `applicationName` / `startFormUrl` / `changeNodeRequestDtos` / `informAddSelectPeoples` / `commentRequired` / `affairId` / `trackRequestDto`。
- `BpmSaveDraftUdcDto` 字段原文（在盘 L31-61，15 业务字段；另有常量 L29 → 16 成员）：`templateId` / `rootEntityId` / `rootEntityName` / **`userId`（内联 `@NotNull` 必填）** / `commentDto` / `formData` / **`formRecordId`（内联 `@NotNull` 必填）** / `templateGuid` / `pageUrl` / `pageType` / `pageGuid` / `bpmOperationNodeDto` / `pageParameter` / `affairId` / `trackRequestDto`。
- `BpmTriggerFlowUdcRequestDto` 字段原文（在盘 L27-53，13 业务字段；另有常量 L25 → 14 成员）：`templateId` / `rootEntityId` / `rootEntityName` / **`userId`（内联 `@NotNull` 必填）** / `commentDto` / `formData` / **`formRecordId`（内联 `@NotNull` 必填）** / `templateGuid` / `pageUrl` / `pageType` / `pageGuid` / `needSend` / `pageParameter`。
- **`serialVersionUID` 单列（序列化常量，非业务字段）**：`BpmSaveDraftUdcDto` **L29**（`private static final long serialVersionUID = -9134629414698004241L;`）、`BpmTriggerFlowUdcRequestDto` **L25**（`= -5883293787371399180L`）；`BpmSendUdcDto` 无该常量。

## 4. Required（对照成立的条件 / 证据边界）

- **对照可复算的最小条件**：每条接口/DTO 需「在盘 `.java` 行号 或 manifest sha256 或 jar sha256」中**≥1 项可对 raw 字节复算**（三选一以上）；缺一项即降级为 `UNVERIFIED`。
- **manifest 覆盖 ≠ 有效产出**：`bpm-api-decompile-manifest.json` 中 `com.seeyon.bpm.api.udc.BpmApiProcessAppService` 记录 sha256 = `e3b0c442…`（**空内容哈希**，该次反编译零字节产出）；在盘同名文件 781 B 实为 `com.seeyon.bpm.api.common.BpmApiProcessAppService`（sha256 `40d07249…`，与其自身 manifest 记录一致）→ **`udc` 包该接口无有效反编译产出，不得当有效接口证据**（§7-1）。
- **byte 口径双记**：`udcrt-bpm-link-decompile-manifest.json` 的 `bytes` 字段 = **LF 归一计数**，在盘文件为 CRLF；sha256 一律对 **raw 字节**成立。引字节须注 raw(CRLF) / lf 两口径（§7-2）。

## 5. Execution（对照主表：5.3.517 注入/调用点 ↔ 3.12.101 接口签名）

| # | 5.3.517 调用点（文件 · 行号） | 调用方法 | 3.12.101 接口方法（`BpmUdcApiService.java` 行号） | 入参 DTO |
|---|---|---|---|---|
| 1 | `ApproveFeatureService.java` L183（注入字段 L109） | `prefixForUdc` | L56（default） | `BpmPrefixForUdcDto`（未单列反编译件，UNVERIFIED） |
| 2 | `ApproveFeatureService.java` L325 | `sendForUdc` | L46（abstract） | `BpmSendUdcDto`（§3.2，`2929db4b…`） |
| 3 | `ApproveFeatureService.java` L421（私有方法 `saveDraft` L391 组装） | `saveDraft` | L48（default） | `BpmSaveDraftUdcDto`（§3.2，`e467675e…`） |
| 4 | `ApproveFeatureService.java` L465 | `repealForUdc` | L60（abstract） | `BpmOperationRepealUdcDto`（未单列，UNVERIFIED） |
| 5 | `ApprovalStateChangeListener.java` L114（注入字段 L70） | `deleteCaseByIdForUdc` | L64（abstract） | `Long caseId + Long userId`（无 DTO） |
| 6 | `ApprovalStateChangeListener.java` L138 | `stopForUdc` | L62（abstract） | `BpmStopDto`（未单列，UNVERIFIED） |

- **注入形态（在盘原文）**：`ApproveFeatureService` L109 `private BpmUdcApiService bpmUdcApiService;`；`ApprovalStateChangeListener` L70 `private BpmUdcApiService bpmUdcApiService;`。
- **`BpmUdcApiService` 的 import 行**：`ApproveFeatureService` L66 / `ApprovalStateChangeListener` L49 `import com.seeyon.bpm.api.udc.BpmUdcApiService;`。
- **`triggerFlowForUdc`（接口 L52，default）与 `getNodePermission*`（L66/L70）：在盘 5.3.517 反编译件中未见调用点**（本会话对全部在盘反编译件扫描 `bpmUdcApiService.<m>(` 无命中）→ 调用点 = **UNVERIFIED**（接口声明 ≠ 已被 5.3.517 调用）。
- **入参 DTO 覆盖**：6 处调用点中仅 3 处（#2/#3 + 隐式 #4 经 `BpmOperationRepealUdcDto`）对应 §3.2 三 UDC DTO；`#1 BpmPrefixForUdcDto`、`#4 BpmOperationRepealUdcDto`、`#6 BpmStopDto` 的 `.java` 未单列反编译件在盘 → 这些 DTO 字段 = **UNVERIFIED**（不臆造字段）。

## 6. Side Effects（回流通道）

- **BPM → UDC 回流（在盘）**：`UdcBpmProcessService`（接口，4 方法）+ `UdcBpmProcessServiceImpl`（实现，在盘）：
  - `processBpmApproval`（接口 L30 / 实现 L267，`SingleResponse<Boolean>`，委托 `bpmActionProcessingService.processApprovalAction(..., false)`）
  - `processBpmStop`（接口 L32 / 实现 L271 → `processBpmStopAction`）
  - `processBpmCancel`（接口 L34 / 实现 L275 → `processBpmCancelAction`）
  - `processBpmTakeBack`（接口 L36 / 实现 L279 → `processApprovalAction(..., true)`）
  - 实现类错误面：`getErrorResponse` L283-300（`status=2` / `code="PROCESS_0002"`，在盘原文）。
- **副作用边界**：本节仅登记**回流接口的在盘存在与签名**；BPM 事件如何实际触发这些 `processBpm*`、是否落库/发消息 = **UNVERIFIED**（契约关系 ≠ 运行时调用关系，未观测运行态）。
- **无写操作**：本格纯静态对照，未调用任何写侧端点、未触发任何运行态副作用。

## 7. Known Constraints（强制如实登记三处证据陷阱 + 版本边界）

1. **空内容产出陷阱（manifest ↔ 在盘错位）**：`bpm-api-decompile-manifest.json` 记 `com.seeyon.bpm.api.udc.BpmApiProcessAppService` 的 sha256 = `e3b0c44298fc1c14…` = **空内容哈希**（该次反编译零字节产出）；在盘同名 `bpm-facade-3.12.101-BpmApiProcessAppService.java`（781 B）实为 **`com.seeyon.bpm.api.common.BpmApiProcessAppService`**（sha256 `40d07249…`，与其自身 manifest 记录一致，package 行 L10 实测）。→ **`udc` 包下 `BpmApiProcessAppService` 无有效反编译产出 = UNVERIFIED，不得当有效接口证据**；本表未据此作任何接口断言。
2. **byte 口径陷阱（LF 归一 vs raw/CRLF）**：`udcrt-bpm-link-decompile-manifest.json` 的 `bytes` 字段 = **LF 归一计数**，在盘文件实为 CRLF。四件实测双口径：`ApproveFeatureService` raw **36002** B / CRLF 595 / lf 35407；`ApprovalStateChangeListener` raw **9088** / CRLF 160 / lf 8928；`UdcBpmProcessServiceImpl` raw **16641** / CRLF 301 / lf 16340；`UdcBpmProcessService` raw **1944** / CRLF 43 / lf 1901。**sha256 一律对 raw 字节成立**（manifest 记录的 `f49a8582…`/`15513d47…`/`5d324773…`/`feeec5ce…` 与在盘 raw sha256 逐字一致）；**禁把 manifest 的 `bytes` 当原始字节数照抄**，本格引字节均注 raw(CRLF)/lf 两口径。
3. **manifest 未覆盖的 3 DTO**：`BpmSaveDraftUdcDto`（6787 B / `e467675e…`）、`BpmSendUdcDto`（8713 B / `2929db4b…`）、`BpmTriggerFlowUdcRequestDto`（7311 B / `557f1582…`，均 raw sha256）在盘但**不在 `bpm-api-decompile-manifest.json` 的 records 内**；引用时**自测 sha256** 并注「manifest 未覆盖」。
4. **jar 本体缺盘（3.12.101 侧边界）**：`<MAVEN_REPO>/com/seeyon/bpm-facade/` 在盘仅 `5.3.374/`，**`3.12.101/` 不存在** → 3.12.101 侧证据**止于反编译 `.java`，字节码层不可再深验**（无 jar 可 javap 补验）。
5. **版本独立 + 行为边界**：3.12.101（契约层）与 5.3.517（runtime 调用侧）为两个独立证据单元，**禁合并**；接口/契约对照 **≠ 运行时调用关系**（沿用 `module-link-evidence.json` limitations[0]「A contract relationship is not a runtime invocation relationship」，未升级为行为断言）。
6. **BPM 引擎本体（执行器/调度/模型）实现 = UNVERIFIED（整段）**：在盘仅门面/契约/调用侧件，未直读引擎实现。

## 8. Evidence（逐条在盘路径）

- **E1** 本格局部证据源：`core/facts/bpm/evidence/bpm-version-map-static-20260927T100255Z.json`（14943 B / sha256 `862fc7d3f54e22f7e2556f8b085af5bc70e575045097bdf36c72271b011ee5bd`；含 11 件反编译件 raw/lf/sha、两份 manifest 全量、jar 哈希、三陷阱实测、跨侧对照行号/DTO 字段行号）。
- **E2** 3.12.101 反编译件（raw sha256 见 E1）：`docs/audit/modules/decompiled/bpm-facade-3.12.101-{BpmUdcApiService, BpmAppService, BpmDeployAppService, BpmApiProcessAppService, BpmSendUdcDto, BpmSaveDraftUdcDto, BpmTriggerFlowUdcRequestDto}.java`；manifest `bpm-api-decompile-manifest.json`（`source_sha256 26b312fd…`）。
- **E3** 5.3.517 反编译件 + jar：`docs/audit/modules/decompiled/udcrt-5.3.517-{ApproveFeatureService, ApprovalStateChangeListener, UdcBpmProcessService, UdcBpmProcessServiceImpl}.java`；`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`（861880 B / sha256 `74ae50bd…`）；manifest `udcrt-bpm-link-decompile-manifest.json`。
- **E4** 链路记录：`docs/audit/modules/module-link-evidence.json`（4370 B / sha256 `f9c6ef7b…`；`exposes-platform-runtime-contracts-to` 关系 = `VERIFIED_STATIC_BYTECODE`，`exact_methods`/`outbound`/`inbound` 段 + limitations）。
- **E5** 前两格/格①（未动，绑定字节）：`engine-behavior.md` 16072 B / `7908a94d…`；`flow-node-tree.md` 16070 B / `36ead221…`；`data-flow-map.md` 20703 B / `4f3e60a4…`（引 `STATUS.md`/`main/ROUTE.md` §7 轮 5 记账，非本轮复算；本角色未改）。

## 9. Verified（逐项证据等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `BpmUdcApiService` 接口 9 方法签名（3.12.101） | **VERIFIED_STATIC_BYTECODE** | E2/E1（`.java` L46-L70 原文 + manifest `5028e167…` 与在盘 raw sha 逐字一致） |
| 5.3.517 注入 `BpmUdcApiService` + 6 处调用点 | **VERIFIED_STATIC_BYTECODE** | E3/E1（行号 L109/L70/L183/L325/L421/L465/L114/L138） |
| 3 个 UDC DTO 字段（§3.2） | **VERIFIED_STATIC_BYTECODE（自测 sha）** | E2/E1（manifest 未覆盖，逐件自测 raw sha + 字段行号） |
| 回流 `UdcBpmProcessService`(4 方法) + Impl | **VERIFIED_STATIC_BYTECODE** | E3/E1（接口 L30-L36 / 实现 L267-L279） |
| `com.seeyon.bpm.api.udc.BpmApiProcessAppService` 接口 | **UNVERIFIED**（空内容产出） | §7-1（manifest `e3b0c442…` 空哈希；在盘同名件实为 common 包） |
| `triggerFlowForUdc` / `getNodePermission*` 在 5.3.517 的调用点 | **UNVERIFIED**（在盘反编译件无调用点） | §5（全件扫描无命中；接口声明 ≠ 已调用） |
| `BpmPrefixForUdcDto` / `BpmOperationRepealUdcDto` / `BpmStopDto` 字段 | **UNVERIFIED**（未单列反编译件在盘） | §5（未反编译到的 DTO，不臆造字段） |
| 3.12.101 字节码层（无 jar 可 javap 补验） | **止于反编译 `.java`（UNVERIFIED 更深层）** | §7-4（jar 缺盘，实测目录枚举） |
| **BPM 引擎本体**（执行器/调度/模型实现） | **UNVERIFIED（整段）** | §7-6；在盘仅门面/契约/调用侧件 |
| 运行时调用关系（契约 ≠ 运行态） | **未升级为行为断言** | E4（limitations[0]）；§6 |

> **收口**：第 4 格已按九段式落盘，逐段锚定在盘 STATIC 实据（行号/manifest sha/jar sha 均可对 raw 复算）；
> 空产出/缺盘/未反编译项一律 `UNVERIFIED`，**未把「接口声明」外推成「已被 5.3.517 调用/已部署」**；
> 三处证据陷阱（§7-1/2/3）强制如实登记。格① `7908a94d…` 与两格 `36ead221…`/`4f3e60a4…` 未动（绑定字节见 §8-E5）；`core/facts/INDEX.md` 待主线收口时更新（本轮未动）。

---

## 溯源索引（可复现）

| 段 | 在盘来源（行号 / sha 可复算） |
|---|---|
| Capability / Version | E2（manifest `source_sha256 26b312fd…`；jar 缺盘实测）；E3（jar 861880 B / `74ae50bd…`） |
| Input | `bpm-facade-3.12.101-BpmUdcApiService.java` L46-L70；3 DTO `.java` 字段行号（§3.2 表） |
| Required | `bpm-api-decompile-manifest.json` records（`e3b0c442…` 空哈希）；`udcrt-bpm-link-decompile-manifest.json` `bytes`=LF（§7-2 双口径） |
| Execution / Side Effects | E3（调用点 L109/L70/L183/L325/L421/L465/L114/L138；回流接口 L30-L36 / 实现 L267-L279）；`module-link-evidence.json` `outbound`/`inbound` 段 |
| Known Constraints | §7-1/2/3 三陷阱（manifest ↔ 在盘 sha 逐字对照，E1 实测）+ §7-4/5/6 版本与行为边界 |
| Evidence / Verified | E1-E5（§8 逐条路径 + raw sha256） |
