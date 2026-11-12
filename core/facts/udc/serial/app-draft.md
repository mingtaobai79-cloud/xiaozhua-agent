# udc.application.draft｜应用草稿只读能力族（九段式事实格 · S2）

> 基线：registry `udc.application.draft.*` 契约登记（L91-L94）+ 09-25 只读回读记录（`core/facts/udc/readonly-faces-batch2.md` 行 9）。
> 段序与 B1 样板格 `core/facts/udc/entity/create.md` 一致；本件**只做 `udc.application.draft` 两条**，
> application 域 search/get/deploy_info 归 S3、applog 归 S4；同控制器写端点（create/delete/deleteAll/delete-timeout）**仅注记、不入格、不计数**。
> 只写事实文档，不改 `registry.py`/`components/`/`docs/`；网关与凭据只写 config 键，值 0 入件。
> 仓库 `<SEEYON_AGENT_ROOT>`，实测 HEAD `16a384c`。

---

## 1. Capability

| operation_id | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 层 |
|---|---|---|---|---|---|
| `udc.application.draft.select` | POST | `udc-runtime/app-draft/select` | `String dataId`（@MultiRequestBody） | `SingleResponse<AppDraftDto>` | 设计态配置层 |
| `udc.application.draft.exist` | POST | `udc-runtime/app-draft/exist` | `String dataId`（@MultiRequestBody） | `SingleResponse<AppDraftExistDto>` | 设计态配置层 |

- 同 class（`com.seeyon.boot.starter.udcrt.controller.AppDraftController`）不同 method（`select` / `exist`）；
  class_sha256 同为 `5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9`（E1 L91/L93 实测）。
- **层次口径（依据 E4）**：两条均属**设计态配置层**（AppDraft 草稿读取，**非运行态元数据**）——
  `docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md` L76 / L91 原文；
  同件 L101「五层不顶替」把设计态配置层与运行态元数据 / 生成物 / 物理表 / Redis 并列，本格不得顶替或推断。
- 类级前缀：`@RequestMapping(value=["udc-runtime/app-draft"])` + 方法级 `@PostMapping(value=["select"|"exist"])`（E4 L67 / L82）。
- **排除项（同控制器写端点，只注记不入格）**：`create`（后端 `createOrUpdate`，javap 常量池 #4）、`delete`（javap L261-262 `value=["delete"]`）、
  `deleteAll`（#56 / #57 `delete-all`）、`delete/timeout`（#59 / #62）。四条均非本格能力，不计入任何计数。

## 2. Version

- Canonical = **5.3.517**（registry javap 锚点：E1 L91/L93 `"version": "5.3.517"`，artifact = `udc-starter-runtime-5.3.517.jar`）。
- jar SHA-256 = `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`（E4 契约 4/5 §6 原文）。
- class_sha256 = `5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9`（两 method 同值：E1 L91/L93；E6 L31-32 入库断言同值）。
- **javap 文本件 sha256（与 class_sha256 口径不同，禁混写）**：app-basic 副本 `131b18221d73f999dee7309e2a83d7978f50d0564471190f613a39a4aaa6df71`（21155 B）；
  udc-entity 副本 `8858efdae4014c4cc61967bf8ccee71b95840ef13ed07626e19d49c4d38f5aeb`（21327 B）——两副本**非同一文件**，行号亦不同（见 §8 E7）。

## 3. Input

- 参数形态：`String dataId`（`@MultiRequestBody`；E3 javap L206（exist）/ L239（select）注解，E4 L68 / L83 契约字段级）。
  内部经 `SingleRequest.from(Object)` 归一：E3 javap `exist` L183 / `select` L216（`invokestatic SingleRequest.from`）；
  常量池 #3 = `SingleRequest.from:(Ljava/lang/Object;)`（E3 L15）。
- 参数名 `dataId` 取自 javap `LocalVariableTable`（E3 L257 `dataId Ljava/lang/String;`；E4 L68/L83 同述）。
- 实测入参形态（**LIVE 事实**，E2 行 9 + 行 14）：09-25 探测对 `draft.select` 实发 `{"data":"<dataId>"}` 包装且**可通**（BOOT_0000）；
  E2 行 14 原文记「draft.select 为 MultiRequestBody 裸 dataId（`{"data":...}` 包装实测可通）」——**两种表述并存**，本格按实测原样记录，不择一改写。
- 响应 DTO：`select` → `SingleResponse<AppDraftDto>`；`exist` → `SingleResponse<AppDraftExistDto>`（E1 L92/L94 实测）。

## 4. Required（必填链与缺省推断）

- registry 实测 `required_inputs = ("dataId",)`（两条同值；来源：探针 `implementer/probe_draft_contracts.py` 输出 `required= ('dataId',)`，RC=0）。
- 缺省/必填推断：契约层只登记 `dataId` 一项；**缺省值未观测**（无缺参 LIVE 响应）→ 缺省行为 **UNVERIFIED**，不外推。
- 网关前缀不构成入参：`service` 前缀在 registry verification_rules 内明标 **UNVERIFIED（离线不可确证，禁止拼前缀）**（E1 L92/L94 第三条规则）。

## 5. Execution

- 路径组装（键组装，**不写前缀字面**）：`{config键 gateway_base}/service/{app_id}/udc-runtime/app-draft/select|exist`
  （前缀口径键：`config/environments.yaml#environments.test2.gateway_prefix_template`；服务前缀本身 UNVERIFIED，见 §7）。
- 控制器映射链（E3 / E4 实测）：类级 `@RequestMapping(value=["udc-runtime/app-draft"])`（E4 L67/L82）
  → 方法级 `@PostMapping(value=["select"])`（javap L229）/ `@PostMapping(value=["exist"])`（javap L196）。
- **agent 侧写门（本轮实测复现，非转述）**：两条 `method=POST` → `UdcOperationContract.effective` 实测 **False**
  （源码 `components/platform_operations/models.py` L46-48：`effective` 要求 status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} ∧ ¬write ∧ method == "GET"）
  → `PlatformOperationLayer.execute` 命中 `components/platform_operations/layer.py` L22-23 分支 →
  实测 `status=DENIED`、`kind=code=POLICY_DENIED`、`message="operation is not an effective GET-only readonly contract"`（§8.3 逐字输出）。
  **结论：agent 侧不可执行该调用，只能由宿主授权执行**（与 S1 `udc.serial.select_entity_by_serial` 同口径）。
- LIVE 边界：`draft.select` 有 09-25 LIVE（E2 行 9）；`draft.exist` **无 LIVE 记录**（§8.2 负证据）→ §9 标 UNVERIFIED；**禁**把 select 的 LIVE 顺延给 exist。

## 6. Side Effects

- 注册侧：两条 `write=False`（E1 L92/L94 实测；探针 `write= False`）。
- 语义侧：契约明记操作语义为**只读**——「查找当前用户草稿」/「当前用户是否存在草稿」（E4 L66 / L81）。
- agent 侧：因 §5 写门 `DENIED`，**agent 侧不产生任何副作用**（未发起调用）。
- 宿主侧副作用：**未观测 → UNVERIFIED**（无 LIVE、无宿主侧执行记录）；不外推为「无副作用」。

## 7. Known Constraints

- **策略**：POST 动词的只读语义契约在 agent 侧被 `POLICY_DENIED` 拦下（§5 实测）；宿主授权是唯一执行路径。
- **网关前缀 UNVERIFIED**：两条 verification_rules 第三条均为「网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）」（E1 L92/L94）。
- **层不可顶替**：设计态配置层（AppDraft）≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis（E4 L101）。
- **`draftData` 双层序列化（必须如实写）**：`draftData` 是**字符串内嵌 JSON**（双层序列化），消费方需**二次 `json.loads`**——
  E2 行 18 原文；E2 行 9 记 LIVE 实测该字段为「JSON 串，含字段 `_display` 形态」。
- **路径白名单 / 403 事件**：相关面全在 `udc-runtime/` 前缀白名单内；无 PF 直挂会被 nginx 挡（09-24/25 两次 403 事件，E2 行 17）。
- **`exist` 无 LIVE**：见 §8.2（负证据）；不得以 `select` 的 LIVE 代表 `exist`。

## 8. Evidence（逐条实测复核；禁转述）

| # | 路径（在盘实测） | 实测要点 |
|---|---|---|
| E1 | `components/platform_operations/registry.py`（**51734 B**）L91/L92、L93/L94 | 两条契约登记：method / path / req / resp / status / write / required_inputs + evidence dict；`class_sha256=5090304d…`，`method=select|exist` |
| E2 | `core/facts/udc/readonly-faces-batch2.md`（**1930 B**）行 9 / 14 / 15 / 17 / 18 / 20 | 行 9 = **09-25 LIVE** `draft.select` BOOT_0000 + 真草稿 `dataId=4854586837685616411` + `draftData`（JSON 串）；行 20 = traceId `3247010154532571324`；行 14 入参包装；行 15 全只读；行 17 403 约束；行 18 双层序列化 |
| E3 | `docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt`（**21155 B**，sha256 `131b1822…`） | L175 `exist(String)` 声明；L196 `@PostMapping(value=["exist"])`；L206 `@MultiRequestBody`；L208 `select(String)` 声明；L183 / L216 `SingleRequest.from`；L229 `@PostMapping(value=["select"])`；L239 `@MultiRequestBody`；L257 `LocalVariableTable` `dataId`；L261-262 `value=["delete"]`（排除项） |
| E4 | `docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md`（**12899 B**）§契约 4 L63-77 / §契约 5 L78-91；L100-101 | 字段级契约：类级前缀 + 方法级映射；**层次 = 设计态配置层**（L76 / L91）；L101 五层不顶替；L100 相邻面注记 |
| E5 | `docs/operation-contracts/udc/application/registry-entries.md`（**7946 B**）L15-18（代码块）/ L28-29（表） | MERGE 照抄条目（含 class_sha256 与 readback 三要素）；`exist` 行为 `dict(appbasic_draft_evidence, method="exist")` 派生 |
| E6 | `tests/test_application_readonly_contract.py`（**5401 B**）L25 / L31-32 / L87-92 | 入库断言：两条同属 `POST_CONTRACTS`；同 class 不同 method；同 SHA `5090304d…` |
| E7 | `docs/audit/artifacts/udc-entity-5.3.517/AppDraftController.javap.txt`（**21327 B**，sha256 `8858efda…`） | 同 class 另一副本：`exist` 声明 L177 / `value=["exist"]` L198；`select` 声明 L210 / `value=["select"]` L231 —— **与 E3 非同一文件（字节、哈希、行号均不同），不得假定等价** |

### 8.1 实测计数（本机命令 + 结果，禁照抄任务书）

- `grep -c 'contracts\["udc\.application\.draft' components/platform_operations/registry.py` → **2**（draft 域真条目数）。
- 运行期实测（探针 RC=0）：`UdcOperationRegistry.default()` → `REGISTRY_TOTAL= 64`、`HAS_BOTH= True`。
- **口径差异注记（不改数迎合）**：任务书原料写「application 12 条」，实测 `registry.py` 内 application 域条目 = **6**（main 本轮实测同值，ROUTE §6.2）；
  本格 draft 面实测 = **2**（`select` / `exist`）。与任务书 12 条口径**不一致**——差异在于任务书按「域内命名总数（含别名与文档候选）」计数，
  本格按**可复现命令输出**（registry 内 draft 条目 2 条）为准。**不修改任何数字以迎合任务书。**

### 8.2 负证据（明确未观测到，防外推）

- **`udc.application.draft.exist` 无 LIVE 记录**。复现命令与命中清单（本轮实测）：
  - `grep -rn 'app-draft/exist' --include='*.md' --include='*.py' --include='*.json' .` → 命中仅 **3 处，全为契约侧**：
    `components/platform_operations/registry.py:94`（登记）、`docs/operation-contracts/udc/application/registry-entries.md:18`（MERGE 代码块）、
    `:29`（MERGE 表）；**无任何 HTTP 响应 / 回读记录**。
  - `grep -rln 'draft\.exist' .` → 命中文件：`registry.py`、`registry-entries.md`、`udc-app-basic-readonly-contracts.md`（契约 5，回读条件明记「本轮不做」）、
    `tests/test_application_readonly_contract.py`（入库断言）→ **全为 STATIC / 契约侧**。
  - 全仓唯一 draft 面 LIVE 记录 = `core/facts/udc/readonly-faces-batch2.md:9` 的 `draft.select`（`dataId=4854586837685616411`）。
- 因此 `draft.exist` 的**执行面**证据等级 = **UNVERIFIED**（仅字节码 / 契约级 STATIC 证据）；**不得**以 `draft.select` 的 LIVE 代表 `exist`。
- 另：`draft.select` 的 LIVE 记录**不含 `exist` 端点响应**；`AppDraftExistDto` 内部字段形态亦**未观测** → UNVERIFIED。

### 8.3 探针输出（实测，RC=0；全文见会话件 `implementer/S2-PROBE.out.txt`）

- `FIELD udc.application.draft.select | method= POST | path= udc-runtime/app-draft/select | req= String dataId(MultiRequestBody, SingleRequest) | resp= SingleResponse<AppDraftDto> | status= VERIFIED_STATIC_BYTECODE | write= False | effective= False | required= ('dataId',) | gate_true= True`
- `FIELD udc.application.draft.exist | method= POST | path= udc-runtime/app-draft/exist | req= String dataId(MultiRequestBody, SingleRequest) | resp= SingleResponse<AppDraftExistDto> | status= VERIFIED_STATIC_BYTECODE | write= False | effective= False | required= ('dataId',) | gate_true= True`
- `LAYER udc.application.draft.select | status= DENIED | kind= POLICY_DENIED | code= POLICY_DENIED | msg= operation is not an effective GET-only readonly contract`
- `LAYER udc.application.draft.exist | status= DENIED | kind= POLICY_DENIED | code= POLICY_DENIED | msg= operation is not an effective GET-only readonly contract`
- `REGISTRY_TOTAL= 64 | HAS_BOTH= True`

## 9. Verified（逐项等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `udc.application.draft.select` 契约登记（method/path/req/resp/write/required） | VERIFIED_STATIC_BYTECODE | E1 L91-92；§8.3 探针 |
| `udc.application.draft.select` 控制器映射与注解 | VERIFIED_STATIC_BYTECODE | E3 javap L208 / L216 / L229 / L239；E4 L63-77 |
| `udc.application.draft.select` **执行面（09-25 回读）** | **LIVE** | E2 行 9：BOOT_0000 + `dataId=4854586837685616411` + `draftData`；traceId `3247010154532571324`（E2 行 20） |
| `udc.application.draft.exist` 契约登记与控制器映射 | VERIFIED_STATIC_BYTECODE | E1 L93-94；E3 javap L175 / L196 / L206；E4 L78-91 |
| `udc.application.draft.exist` **执行面** | **UNVERIFIED** | §8.2 负证据（全仓无 LIVE / 回读记录）；禁顺延 select 的 LIVE |
| 两条 agent 侧可执行性（写门） | **LIVE**（本轮实测） | §5 + §8.3：`DENIED` / `POLICY_DENIED`；源码 `models.py` L46-48、`layer.py` L22-23 |
| `draftData` 双层序列化 | VERIFIED_STATIC_BYTECODE（含实测记录） | E2 行 18 + 行 9 |
| 网关 service 前缀 | UNVERIFIED | E1 L92/L94 第三条规则（禁止拼前缀） |
| 缺省入参行为 / 宿主侧副作用 / `AppDraftExistDto` 字段形态 | UNVERIFIED | 无观测（§4、§6、§8.2） |

**未直读项（如实登记）**：本轮**未**联网、**未**执行任何宿主侧调用；`exist` 无 LIVE；`draftData` 内部字段仅知 `_display` 形态（E2 行 9），未展开。

## 溯源索引（可复现）

| 项 | 路径 |
|---|---|
| 契约登记（两条） | `components/platform_operations/registry.py` L91-94 |
| 09-25 LIVE 记录 | `core/facts/udc/readonly-faces-batch2.md` 行 9 / 行 20 |
| 字节码证据（主） | `docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt` |
| 字节码证据（副本，非等价） | `docs/audit/artifacts/udc-entity-5.3.517/AppDraftController.javap.txt` |
| 字段级契约 | `docs/operation-contracts/udc/application/udc-app-basic-readonly-contracts.md` §契约 4 / §契约 5 |
| MERGE 条目 | `docs/operation-contracts/udc/application/registry-entries.md` L15-18 / L28-29 |
| 入库断言 | `tests/test_application_readonly_contract.py` L25 / L31-32 / L87-92 |
| 写门源码 | `components/platform_operations/models.py` L46-48；`components/platform_operations/layer.py` L22-23 |
| 本轮探针 | `implementer/probe_draft_contracts.py`（会话目录；输出 `implementer/S2-PROBE.out.txt`） |

> 本件自报字节数（写后 `wc -c` 实测，等宽回填不改大小）：15541 B · 时钟 2026-09-26 CST · 仓库 HEAD 16a384c
