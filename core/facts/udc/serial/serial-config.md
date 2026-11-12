# udc.serial｜流水配置只读能力族（九段式事实格 · S1）

> 基线：registry `udc.serial.*` 契约登记（L97-L100）+ 三次只读回读离线记录（2026-09-18 / 09-20 / 09-25）。
> 段序与 B1 样板格 `core/facts/udc/entity/create.md`（8145 B）一致；本件**只做 `udc.serial` 一格**，
> 别名 `udc.serial_config.entity_list` 仅注记、不计新能力；只写事实文档，不改 `registry.py`/`components/`/`docs/`；
> 网关与凭据只写 config 键，值 0 入件。
> 仓库 `<XIAOZHUA_AGENT_ROOT>`，实测 HEAD `16a384c`。

---

## 1. Capability

| operation_id | 语义 | method | 控制器原路径（逐字，未拼网关前缀） |
|---|---|---|---|
| `udc.serial.select_entity_list` | 按 appName 读取**流水配置下已挂实体组与项清单**（EntityGroupAndItemDto） | GET | `udc-runtime/serial-config/select-entity-list` |
| `udc.serial.select_entity_by_serial` | 按流水 Id（Map 入参）读取**使用的实体字段元数据**（UdcEntityMetaDataDto 列表） | POST | `udc-runtime/serial-config/select-entity-by-serial-id` |

- **控制器**：`com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController`（artifact `udc-starter-runtime-5.3.517.jar`，
  classfile SHA-256 `fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658`），
  类级 `@RequestMapping(value=["udc-runtime/serial-config"])`（javap 实测，见 §8 E4）；类级 `@RestApi("流水配置接口")`。
- **真实语义取自 RestApiOperation 注解原值**（javap 实测）：`selectEntityList` = “3.1 查询流水配置可用的实体列表”，
  `selectEntityBySerial` = “3.2 按流水 Id 获取使用的实体字段”。
- **别名/同面（注记，不计新能力）**：`udc.serial_config.entity_list` 与 `select_entity_list` **同控制器同方法同端点**
  （同 artifact/class/method、同 `select-entity-list` 路径），仅为命名变体 + 另一域（menu）的候选登记项；
  本格只注记、不重复计数（见 §8 E6）。
- **非本格范围**：同控制器的 `update`（POST 写）、`list`（POST 分页查询，语义非本只读族两条）、
  `refresh-historical-data/{appName}`、`cache-evict/{appName}`（GET 名但刷新/逐出语义）**不纳入**（§8 E5 排除项）。

## 2. Version

- **Canonical = 5.3.517**：两条契约的 evidence 均锚 `udc-starter-runtime-5.3.517.jar` + `version=5.3.517`（registry.py L97/L99 逐字）。
- javap 工件同批 5.3.517：`docs/audit/artifacts/udc-entity-5.3.517/`（82745 B）、`docs/audit/artifacts/udc-menu-5.3.517/`（83013 B）。
  两文件**实测 sha256 不同**（`ddfd9081…ebcf` / `676a33a5…98bb`，`diff -q` RC=1），**差异性质本轮未逐行归因 → UNVERIFIED**；
  但两文件内已逐项核对的关键锚点（类级 RequestMapping、两条方法的 mapping 注解与声明行）**逐字一致**。
- **版本差异机制**：走 Version Adapter（`adapter-5.3/5.4/…`）；**Adapter 未建 → 其他版本 UNVERIFIED**，不自行判版本分支。

## 3. Input

| 能力 | 入参（实测） | 形态 |
|---|---|---|
| `udc.serial.select_entity_list` | `appName`（`java.lang.String`，参数注解 `@MultiRequestBody`） | GET + `@MultiRequestBody`（全域 52 POST 先例 0 GET，本方法为 GET+@MultiRequestBody 唯一法） |
| `udc.serial.select_entity_by_serial` | `serialKey`（`java.util.Map<String, java.lang.Object>`，参数注解 `@MultiRequestBody`） | POST 请求体 Map |

- **传参形态实测（别名面 P4，同端点同方法）**：① `?appName=` 查询串 ② JSON 请求体 `{"appName":<appId>}`
  两形态**均 LIVE 通过且 body_md5 一致 → runtime 等效**（§8 E6，2026-09-20 两次开火）。
- **路径拼接口径**：类级 `udc-runtime/serial-config` + 方法级 `select-entity-list` / `select-entity-by-serial-id`。
  网关 `service` 前缀**不写字面**，一律引用 config 键（§4/§7）。
- **字节码调用链（实测）**：`selectEntityList(SingleRequest)` → `UdcSerialConfigAppService.selectEntityList`；
  `selectEntityBySerial(Map)` → `ListRequest.from(Map)` → `UdcSerialConfigAppService.selectEntityBySerialId`（javap E4）。

## 4. Required（必填链与缺省推断）

- **`appName` 必填**（registry L98 `required_inputs=("appName",)`）；**`serialKey` 必填**（L100 `required_inputs=("serialKey(Map)",)`）。
- **权限前置链（字节码实测）**：两条方法体首段均为 `checkSerialConfigResourcePermission()`
  → 返回 false 即 `handlerErrorResponse()` / `handlerErrorListResponse()` 提前 return，**不进入 appService 调用**
  （`ifne 12` 早退分支，javap E4 逐条核对）→ 无权限时是 envelope 错误响应，而非异常穿透。
- **缺省推断：无**。两条契约的缺省值在盘无证据 → 不臆造；`stereotype` 式值域推断链本域不存在。
- **写门判定链（agent 侧）**：`models.py` L47-L48 `effective = status ∈ {PASS, VERIFIED_STATIC_BYTECODE, OBSERVED} and not write and method.upper()=="GET"`
  → `layer.py:22` `if contract.write or contract.method != "GET" or not contract.effective:` → `OperationStatus.DENIED` + `POLICY_DENIED`。

## 5. Execution

- **端点可达性**：`{gateway_base} + /service/{default_app_id} + <控制器原路径>`（config 键：`config/environments.yaml#environments.test2.{gateway_base,gateway_prefix_template,default_app_id}`；
  值不写本件）。网关 `service` 前缀的**完整可拼字面 UNVERIFIED**（离线不可确证，禁拼前缀）。
- **实测 effective（本机只读探针 RC=0，2026-09-26）**：

```
OK udc.serial.select_entity_list | method= GET | path= udc-runtime/serial-config/select-entity-list | req= java.lang.String | status= VERIFIED_STATIC_BYTECODE | write= False | effective= True | required= ('appName',)
OK udc.serial.select_entity_by_serial | method= POST | path= udc-runtime/serial-config/select-entity-by-serial-id | req= java.util.Map<String, java.lang.Object> | status= VERIFIED_STATIC_BYTECODE | write= False | effective= False | required= ('serialKey(Map)',)
ALL_PRESENT= True | registry_total= 64
```

- **推论（实测支撑，非外推）**：`select_entity_list` 为 `effective=True` 的 GET 只读契约 → **agent 侧可执行**；
  `select_entity_by_serial` 虽 `write=False`，但 method=POST → `effective=False` → **写门恒 DENIED/POLICY_DENIED**：
  agent 侧不出此调用，如需走该端点只能由**宿主授权执行**（与 B1 写门同口径）。

## 6. Side Effects

- 两条契约 `write=False`（registry L98/L100 逐字）：**查询语义，无写副作用**；`select_entity_by_serial` 用 POST 仅是传参形态（Map 请求体），
  非写语义（同控制器真正写语义的 `update` 为独立方法，未纳入本格）。
- `select_entity_list` LIVE 回读为**二次回读 identity MATCH**（同响应体字节数 3561 B 稳定）→ 未见读触发状态漂移（§8 E2）。
- **无权限前置**：权限门不通过时提前 return（§4），**不产生任何服务端调用**。
- 本格不主张任何缓存/落库副作用；同控制器 `cache-evict` 属另一方法（已排除），**不得**归因到本两条。

## 7. Known Constraints

| 约束 | 后果 | 在盘依据 |
|---|---|---|
| `select_entity_by_serial` method=POST → `effective=False` | agent 侧写门恒 `DENIED/POLICY_DENIED`；只能宿主授权执行 | `models.py` L47-48 + `layer.py:22` + 本机探针 RC=0（§5） |
| 两条方法先过 `checkSerialConfigResourcePermission()` | 无权限 → envelope 错误响应（`handlerError*`），不进 appService | javap E4（`checkSerialConfigResourcePermission:()Z` 早退分支） |
| 网关 `service` 前缀完整字面 | **UNVERIFIED**（不拼前缀当可用 URL；只引 config 键） | `registry-entries.md` 待 MERGE 注意；B1 同口径 |
| GET + `@MultiRequestBody` 传参 | 两形态（查询串/请求体）runtime 等效已实测；其余形态（路径变量等）无证据 | E6（P4，2026-09-20 两次开火） |
| 版本差异 | 非 5.3.517 无在盘证据；Adapter 未建 → UNVERIFIED | registry evidence `version=5.3.517`；B1 §2 同铁律 |
| 两份同 class 的 javap（entity/menu）sha256 不同 | 差异性质未见归因 → 引用时**以锚点逐字核对为准**，不假定两文件等价 | §2 实测 sha256 + `diff -q` RC=1 |
| 任务书「registry serial 4 条」口径 | 与 registry.py 实测 **2 条**不符 → **如实注记差异，不改数迎合** | §8 计数实测段 |

## 8. Evidence（逐条实测复核；禁转述）

| # | 路径（在盘实测字节） | 用途 | 本轮复核方式与结果 |
|---|---|---|---|
| E1 | `components/platform_operations/registry.py`（51734 B）L97-L100 | 两条契约登记（method/path/req/resp/status/write/required） | `grep -n 'udc\.serial'` + `sed -n '90,105p'` 逐字引用；L98/L100 为两条契约，L97/L99 为 evidence dict |
| E2 | `docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md`（5810 B）回读表行 1 + §“### 1 udc.serial.select_entity_list” | LIVE 依据：HTTP 200 / 3561 B / `code=BOOT_0000` / `msg=SUCCESS` / 二次回读 identity **MATCH** | 读文件逐字核对；**窗口 2026-09-18 已过期作废 → 只作离线结果记录**，非本轮复跑 |
| E3 | `core/facts/udc/readonly-faces-batch2.md`（1930 B）行 8（表行）+ §8 | 09-25 15:5x LIVE 探测量：`BOOT_0000` + `content.groups/entities` 清单；traceId `3247010114032371900` | 读文件逐字核对（该行即 `udc.serial.select_entity_list` 行） |
| E4 | `docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt`（82745 B）+ `docs/audit/artifacts/udc-menu-5.3.517/UdcSerialConfigController.javap.txt`（83013 B） | 字节码证据：类级 RequestMapping（L1167 区）、`selectEntityList` 声明 L648 + `@GetMapping(value=["select-entity-list"])` L678 + `@MultiRequestBody` L689、`selectEntityBySerial` 声明 L691 + `@PostMapping(value=["select-entity-by-serial-id"])` L724 + `@MultiRequestBody` L735、权限门早退分支、appService 调用点 L663/L706 | `wc -c` + `sha256sum` + `grep -n` + `sed` 段落核对；两文件关键锚点逐字一致（sha256 不同见 §2） |
| E5 | `docs/operation-contracts/udc/entity/entity-readonly-contracts.md`（15364 B）§1/§2 + `entity/registry-entries.md`（20853 B）§1/§2 + `entity/registry-entries-code.md`（20111 B）§1/§2 | 字段级契约描述与可照抄构造代码（含 class_sha256、required_inputs、verification_rules）；排除项清单 L211-L212 | `grep -n -B/-A` 命中处逐字核对；排除项实测在 `entity-readonly-contracts.md` L211-212 |
| E6 | `docs/operation-contracts/udc/menu/P4-udc-serial-config-entity-list.md`（4216 B）+ `docs/audit/artifacts/udc-menu-5.3.517/registry-entries-constructibility.md`（2087 B）+ `docs/audit/artifacts/udc-menu-5.3.517/multi-request-body-get-binding.md` | **别名/同面**注记：`udc.serial_config.entity_list` `effective=True`（构造实测 RC=0）；两传参形态 LIVE 200+BOOT_0000+identity_matches（2026-09-20） | 读文件逐字核对；别名**只注记，不计新能力** |
| E7 | 本机只读探针 `implementer/probe_serial_contracts.py`（974 B）+ 输出 `implementer/probe_serial_contracts.out.txt`（会话目录） | 运行期实测两条契约的登记字段与 `effective` | `python implementer/probe_serial_contracts.py` → RC=0，stdout 见 §5（`registry_total=64`） |

### 8.1 实测计数（本机命令 + 结果，禁照抄任务书）

- `grep -c 'contracts\["udc\.serial' components/platform_operations/registry.py` → **2**（serial 域真条目数）。
- `grep -oE '"udc\.serial[A-Za-z0-9_.]*"' components/platform_operations/registry.py | sort -u` → 2 个 op_id（两条真条目）。
- 全仓（`*.md/*.py/*.json/*.txt`，排除 .git/.venv/node_modules）
  `grep -rhoE 'udc\.serial[A-Za-z0-9_.]*' . | sed 's/\.*$//' | sort -u` → **3 个 op-id 形态命名**：
  `udc.serial.select_entity_list`（9 文件）、`udc.serial.select_entity_by_serial`（7 文件）、`udc.serial_config.entity_list`（4 文件，别名）；
  若把裸域词 `udc.serial`（B1 式标题/表头出现，非 op_id）一并计入字符串去重则为 **4**。
- 运行期实测：`UdcOperationRegistry.default()` `registry_total=64`（探针 RC=0）；文本层 `grep -c 'contracts\['`=46、
  `grep -c 'OperationStatus.VERIFIED_STATIC_BYTECODE'`=40（**文本出现次数 ≠ 运行期条目数**，两口径并存如实记录）。
- **口径差异注记（不改数迎合）**：任务书原料写“registry serial 4 条”，实测 registry.py 内 serial 域条目 = **2**；
  main 本轮口径记“4（2 真条目 + 2 别名）”，我的实测为“2 真条目 + 1 别名 + 1 裸域词 = 4 个字符串 / 3 个 op-id”。
  **二者差异在于是否把裸域词与文档候选计入**；本格以**可复现命令输出**为准（2 真条目 / 3 op-id 形态命名 / 4 字符串去重），
  不修改任何数字以迎合任务书。

### 8.2 负证据（明确未观测到，防外推）

- `grep -rn --include='*.md' --include='*.json' 'select-entity-by-serial' .` 于 LIVE/HTTP 语境**无命中** →
  `select_entity_by_serial` **本轮无 LIVE 响应**（全仓无该端点的 HTTP/envelope 记录）。
- 目标目录本轮前**不存在**（`ls -d core/facts/udc/serial` → No such file or directory），本格为该目录首件。

## 9. Verified（逐项等级 + 未直读项）

| 项 | 等级 | 依据 |
|---|---|---|
| `udc.serial.select_entity_list` 契约登记（method/path/req/resp/write） | **VERIFIED_STATIC_BYTECODE** | `registry.py` L97-L98 + javap E4（class_sha256 `fe1e5a72…`） |
| `udc.serial.select_entity_list` 端到端只读回读 | **LIVE** | E2（2026-09-18 窗口：200/3561 B/BOOT_0000/二次 identity MATCH，**窗口已过期，作离线记录**）+ E3（09-25 15:5x BOOT_0000 + groups/entities，traceId `3247010114032371900`）+ E6（别名同面 09-20 两形态 200+BOOT_0000） |
| `udc.serial.select_entity_by_serial` 契约登记（method/path/req/resp/write） | **VERIFIED_STATIC_BYTECODE** | `registry.py` L99-L100 + javap E4 |
| `udc.serial.select_entity_by_serial` 端到端只读回读 | **UNVERIFIED** | §8.2 负证据：全仓无该端点 LIVE/HTTP 记录；契约描述亦记“需真实网关 + 一条 serial 键值 Map，本轮不做”（E5 §2） |
| 写门判定：`select_entity_by_serial` → `effective=False` → agent 侧 DENIED | **VERIFIED_STATIC_BYTECODE**（+运行期实测） | `models.py` L47-48、`layer.py:22`、探针 RC=0 stdout（§5） |
| 权限门 `checkSerialConfigResourcePermission()` 早退 | **VERIFIED_STATIC_BYTECODE** | javap E4 方法 Code 段逐条核对 |
| 别名 `udc.serial_config.entity_list` 同面（不新增能力） | **VERIFIED_STATIC_BYTECODE** | E6：同 class/method/端点；构造实测 `effective=True` RC=0 |
| 网关 `service` 前缀完整可拼字面 | **UNVERIFIED** | 离线不可确证；只引 config 键（`environments.test2.*`） |
| 两份同 class javap 差异性质 | **UNVERIFIED** | §2 实测 sha256 不同、未逐行归因 |
| 非 5.3.517 版本行为 | **UNVERIFIED** | 无在盘证据；Adapter 未建 |

> **收口**：`udc.serial` 一格按九段式落盘，逐段锚定在盘 STATIC/字节码/LIVE 实据；
> **`select_entity_by_serial` 无 LIVE → 如实标 UNVERIFIED（不外推）**；别名只注记不计新能力；
> 计数以本机可复现命令为准并注记与任务书/main 口径的差异。**本件不含凭据值，网关仅引用 config 键**。
> app 域与 app-draft 三格归 S2/S3/S4，本件不扩散。

---

## 溯源索引（可复现）

| 段 | 在盘来源 |
|---|---|
| §1 Capability / §3 Input | `registry.py` L97-L100；javap E4（类级 `udc-runtime/serial-config`、两条方法注解与 RestApiOperation 原值） |
| §2 Version | registry evidence `artifact/version/class_sha256`；两 javap 目录名与 sha256 实测 |
| §4 Required / §5 Execution | `registry.py` L98/L100 `required_inputs`；`models.py` L47-48；`layer.py:22`；本机探针 stdout（§5） |
| §6 Side Effects | `write=False`（L98/L100）；E2 二次 identity MATCH |
| §7 Known Constraints / §9 Verified | E2/E3/E4/E5/E6 逐条；§8.2 负证据 |
| §8 Evidence 计数 | §8.1 命令与输出（本机 2026-09-26 CST 实测） |
| 排除项（非只读方法） | `docs/operation-contracts/udc/entity/entity-readonly-contracts.md` L211-212 |

> 本件自报字节数（写后 `wc -c` 实测，等宽回填不改大小）：16655 B · 时钟 2026-09-26 CST · 仓库 HEAD 16a384c
