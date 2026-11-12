# item-mgmt.item-master-data｜物料/主数据 只读事实格（九段式 · 阶段 1）

> 任务：`core/facts` 三 stub 之一 **item-mgmt（物料主数据）** 推进为有 LIVE 双源证据的九段式格。
> 仓库 `<SEEYON_AGENT_ROOT>`，写前实测 HEAD `dc12ef3d16a292116128ddc110c5cb1cd1cb4e8d`，
> `git status --porcelain` = 1 行（仅 `?? core/facts/item-mgmt/`，本件落点），冻结件 0 触碰。
> 活体入口：test2 网关 `https://lowcode-test2.example.com`（config/environments.yaml::test2，凭据仅路径引用，值 0 入件）。
> 探时钟：2026-09-29 12:48–12:51 gmt8（UTC+8），epoch 1790657318–1790657510。

## 模块定位（重要·防外推）
2小爪 UDC 中**不存在**独立的 `ItemAppService`/`MaterialAppService`/`物料主数据` 业务类（反编译树全仓 grep 仅见
`物料编码/物料型号/物料描述` 作为**实体属性字段**，如 `Biangengleijituihuo.java` 的 `materiel_number`，
无 AppService/Controller 载体）。故"物料/主数据 只读面"在本模块内落为两条：
1. **真实数据读取面** = UDC 运行态数据查询 `POST /udc-runtime/data/query`
   （`UdcFormDataQueryController.queryFormData`，回读某实体某数据行的表单值，即文档上"物料编码"等业务字段的当前值）。
2. **主数据实体枚举面** = 串行配置实体清单 `GET /udc-runtime/serial-config/select-entity-list`
   （回读 app 下全部实体的 `fullName/name/caption/stereotype`，即主数据对象面的可枚举目录）。
本件按"能力 = 只读接口契约"立格，双源（字节码 + LIVE）逐面登记。

---

## 1. Capability
| 能力 | HTTP | 控制器原路径（逐字） | 入参 | 响应 | 写门判定（STATIC） |
|---|---|---|---|---|---|
| `item.data.query_form_data`（物料/主数据值回读） | POST | `udc-runtime/data/query` | `EntityDataRequestDto`（appName/dataId/entityFullName/attrKeys） | `SingleResponse<EntityDataResponseDto>` | POST → effective=False → 活体放行；**已调用，业务数据未验证** |
| `item.serial.select_entity_list`（主数据实体目录） | GET | `udc-runtime/serial-config/select-entity-list` | `String appName`（SingleRequest 包裹） | `SingleResponse<EntityGroupAndItemDto>` | GET + ¬write → effective=True |
| `item.meta.function_node_tree`（控件/函数节点树，对照面） | GET | `udc-runtime/meta-data/select-function-node-tree/{appName}` | `String appName`（PathVariable） | `ListResponse<UdcFunctionNodeMetadataDto>` | GET + ¬write → effective=True（本件仅作 LIVE 数据面可达对照） |

- 对应 registry 既有名：`udc.flow.form_data_query`（`udc-runtime/data/query`）与 `udc.entity_data.query_form_data`
  （`udc-runtime/data//query` 双斜杠变体）；`select-entity-list` = `udc.serial.select_entity_list`。
  **本件按"物料/主数据 域"重立 item-mgmt 格，不重复计数既有 udc.* 条目（别名纪律，同 S1–S4 口径）。**

## 2. Version
- Canonical = **5.3.517**（字节码件均源 `udc-starter-runtime-5.3.517.jar` / `udc-flow-5.3.517.jar`；本地 Maven 5.3.517）。
- **test2 活体镜像 = 5.3.496**（config/environments.yaml::test2.udc_image_version，与本地 5.3.517 是**两个证据单元**，
  字节码契约属 5.3.517，LIVE 观测属 5.3.496 网关；两者并行登记，不得互证）。
- 字节码类指纹（三份，逐件 sha256，见 §8）：
  | 类 | javap 源（在盘） | 字节 | class_sha256(javap 文本) |
  |---|---|---|---|
  | `UdcFormDataQueryController` | `docs/audit/artifacts/udc-entity-5.3.517/UdcFormDataQueryController.javap.txt` | 10241 B | `6cf5b0cd1d5c4f4ad7611d661f3d2f510f3e842c67dedef975eeb4472439d4ac` |
  | `UdcSerialConfigController` | `docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt` | 82745 B | `ddfd9081…`（全值见 §8 E3） |
  | `UdcFunctionNodeController` | `docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.javap.txt` | 8067 B | `7fa7876d915e75daf65680ddd80269515263f8d1166c098aaf86e70a577e4041` |
  - 三件已**逐位复制**入本件 `evidence/bytecode/`（复制后 sha256 与原件相等 = VERBATIM，实测 3/3 通过）。

## 3. Input
- `data/query`：`EntityDataRequestDto`。**LIVE 服务端揭示必填链 = `appName` / `dataId` / `entityFullName`**
  （首轮 status=3 报文 verbatim：`"appName 应用编码;  dataId 数据id;  entityFullName 实体FullName"`；
  补字段后二轮 status=3 报文：`"dataId 数据id"` —— 即 `appName`+`entityFullName` 可过首层校验，**卡死在 `dataId`（行键）必填**）。
- `select-entity-list`：`String appName`（本件用 `app9000000000000000001`）。
- `select-function-node-tree/{appName}`：`String appName`（PathVariable）。

## 4. Required（必填链与缺省推断）
- `data/query` 必填链（LIVE 服务端逐步揭示，非外推）：`appName` → `entityFullName` → `dataId`（**行键，非枚举可得**）。
  - `dataId` = 具体数据行 id，需先经"实体数据行列表"类接口枚举（本件**未探测**该枚举手，故 `data/query` 非空业务样本**未达成**，如实标"已调用但业务数据未验证"，§7/§9）。
  - 缺省/可空行为：**未观测 → UNVERIFIED**。
- `select-entity-list` / `select-function-node-tree`：`appName` 必填；缺省未观测 → UNVERIFIED。

## 5. Execution
- 路径组装（**键组装，禁写字面**）：
  - `{config键 gateway_base}/service/{app_id}/udc-runtime/data/query`
  - `{config键 gateway_base}/service/{app_id}/udc-runtime/serial-config/select-entity-list`
  - `{config键 gateway_base}/service/{app_id}/udc-runtime/meta-data/select-function-node-tree/{app_id}`
- 写门（STATIC，引 `components/platform_operations/models.py` L46-48 / `layer.py` L22-23）：
  | 能力 | method | write | effective | agent 侧结论 |
  |---|---|---|---|---|
  | `item.data.query_form_data` | POST | False | **False** | 执行链默认 POLICY_DENIED，**活体已放行**（本件已发，见 §8 E1/E2） |
  | `item.serial.select_entity_list` | GET | False | **True** | 通过写门 |
  | `item.meta.function_node_tree` | GET | False | **True** | 通过写门 |
- 运行期复现：本件**已联网**（test2 活体只读探测，5 发封顶，无重试轰炸），LIVE 证据见 §8 E1/E2。

## 6. Side Effects
- 注册侧：三能力均 `write=False`（字节码 `@PostMapping/@GetMapping` 读语义 + registry 契约）。
- 语义侧：全只读（数据值回读 / 实体目录 / 节点树）。
- agent 侧：本件仅发**只读** GET/POST，0 写操作；`data/query` 因 `dataId` 缺失停在业务校验层，**未触发任何数据变更**。
- 宿主侧副作用：**未观测 → UNVERIFIED**（只读面，无写路径证据）。

## 7. Known Constraints
- **`data/query` 非空业务样本未达成（硬边界，如实标）**：服务端要求行键 `dataId`，需经"实体数据行枚举"接口
  （本件未探测、未登记该手）取得 → 只读探测无法自行造出行键。故 `data/query` = **已调用（HTTP 200 + traceId + 服务端
  字段契约揭示），但业务数据未验证（status=3，非 BOOT_0000 成功）**。
- **非空业务样本由 `select-entity-list` 承担**：LIVE 回读 18 个真实实体（fullName/name/caption/stereotype），
  满足"≥1 条 LIVE 非空业务样本"（§8 E1 send #2，traceId `3252117687647602876`，BOOT_0000，3755 B）。
- **test2 镜像 5.3.496 ≠ 本地字节码 5.3.517**：契约（字节码）与 LIVE（网关）分属两证据单元，本件并行登记、不互证。
- **凭据声明时效已过期、但网关仍接受**（§8 E1 实测）：`expires_epoch=1790595614`（09-28 gmt8）< 探时钟 `1790657318`
  （09-29 gmt8），即**声明过期**；但带 cookie 请求全 200 达数据面 → 会话仍活。按"expiry 是声明非裁定"原则：
  同时记录**声明过期值 + 实测被接受**，真实有效窗 = **UNVERIFIED**（不据字段断"token 无效"）。
- **`udc-runtime/data//query` 双斜杠变体归一化行为 UNVERIFIED**（registry 双 ID 分域登记，本件未探测双斜杠，留活体）。
- **网关 service 前缀**：本件 LIVE 已带 `/service/{app_id}` 前缀实测 200 达数据面 → **前缀有效 = LIVE 实证**（区别于既有格"前缀 UNVERIFIED"口径，本件按实测升为已证）。

## 8. Evidence（逐条实测复核；禁转述；字节码/LIVE 双源在盘）
### E1 LIVE 原始（双源之一）`core/facts/item-mgmt/evidence/live-probe-item-master-data.json`
（**11260 B**，sha256 `342b23e129760dd0ea2fb9d3dc3fc6c77dde62174efebfef46d488c7a89fe00a`，CRLF 294行(293 CRLF终止符)）
| send# | 端点 | 方法 | HTTP | 字节 | code/status | traceId（verbatim） | ts |
|---|---|---|---|---|---|---|---|
| 1 | `meta-data/select-function-node-tree/{app}` | GET | 200 | 205298 B | BOOT_0000/SUCCESS | `3252117671340148924` | 09-29 12:48:36 |
| 2 | `serial-config/select-entity-list?appName={app}` | GET | 200 | 3755 B | BOOT_0000/SUCCESS | `3252117687647602876` | 09-29 12:48:38 |
| 3 | `data/query`（appName+entityCode+attrKeys，registry 字段名） | POST | 200 | 160 B | status=3 | `3252117704659699900` | 09-29 12:48:38 |
| 4 | `data/query`（空 businessKey 对照） | POST | 200 | 160 B | status=3 | `3252117707562158268` | 09-29 12:48:38 |
- **非空业务样本 = send#2**：`data.content.entities[]` 18 个真实实体（首：`…entity.Tbfysq1`/`tbfysq1_3301113173155828788`/"投标费用申请"/standard）。
- 凭据：键名/cookie 长度（375）/声明时效（1790595614）入件，**值 0 入件**（E1 已脱敏自检：secret/uid 串 0 命中，§8.3）。
- 发送数：`meta-data`×1、`select-entity-list`×1、`data/query`×2；`no_retry_bombing=true`。

### E2 LIVE 补证（data/query 修正字段）`core/facts/item-mgmt/evidence/live-probe-data-query-corrected.json`
（**1985 B**，sha256 `962b673735686585291df55fbca6157a381ac8d40423eace40d400a55f9f0f96`，CRLF 57行(56 CRLF终止符)）
- 单发（`data.query.corrected`）：`appName`+`entityFullName`（无 `dataId`）→ **HTTP 200 / 105 B / status=3 / traceId `3252120935783729340`** /
  报文 verbatim `"dataId 数据id"` → 证实服务端必填链推进到 `dataId` 层（§4），**仍非 BOOT_0000 成功、非空样本未达成**。
- 与 E1 send#3/#4 对照（同端点不同字段组合），3 种入参形态全为 status=3 业务校验，**根因（缺行键枚举手）UNVERIFIED 不外推**。

### E3 字节码（双源之二）`core/facts/item-mgmt/evidence/bytecode/`（3 件 VERBATIM 副本，sha256 == 原件）
| 件 | 字节 | 关键锚点（javap 原值） |
|---|---|---|
| `UdcFormDataQueryController.javap.txt` | 10241 B（sha `6cf5b0cd…`） | L106 `queryFormData(EntityDataRequestDto)`；L57 类级 `@RequestMapping("udc-runtime/data")`；L135 `@PostMapping` |
| `UdcSerialConfigController.javap.txt` | 82745 B（sha `ddfd9081fe4fb68794821cff942e5c3510ca4f928efbc6b1ec8181eb78f7ebcf`） | L648 `selectEntityList(String)`→`SingleResponse<EntityGroupAndItemDto>`；L679 `@GetMapping value=["select-entity-list"]`；L1168 类级 `@RequestMapping("udc-runtime/serial-config")` |
| `UdcFunctionNodeController.javap.txt` | 8067 B（sha `7fa7876d…`） | L110 `@GetMapping value=["select-function-node-tree/{appName}"]`；L123 类级 `@RequestMapping("udc-runtime/meta-data")` |

### E4 registry 契约锚（在盘，禁改）
`components/platform_operations/registry.py`：L72 `udc.flow.form_data_query`（`udc-runtime/data/query`，
`EntityDataRequestDto`，写门 POST=POLICY_DENIED）；L47 `udc.microflow.function_node_tree`；L102 `udc.entity_data.query_form_data`（双斜杠变体）。

### 8.1 实测计数（本机命令 + 结果）
- LIVE 非空业务样本：`select-entity-list` = **1**（send#2，18 实体）。
- `data/query` 非空样本：**0**（3 种入参全 status=3）→ 标"已调用但业务数据未验证"。
- 字节码 VERBATIM 副本：3/3（sha 与原件相等）。

### 8.2 别名纪律（同端点不同名 → 并列登记、不归一）
- `item.data.query_form_data` ≡ registry `udc.flow.form_data_query`（同控制器 `UdcFormDataQueryController` 同方法 `queryFormData` 同路径 `udc-runtime/data/query`）；
  `udc.entity_data.query_form_data`（双斜杠 `data//query`）为**同 class 同 method 不同 path** 的第二 ID → 并列登记。
- `item.serial.select_entity_list` ≡ registry `udc.serial.select_entity_list`；`item.meta.function_node_tree` ≡ `udc.microflow.function_node_tree`。
  **本件按 item-mgmt 域重立格，不重复计数既有 udc.* 条目。**

### 8.3 凭据 0 入件自检（实测）
- 对 E1/E2 两文件扫 `sy_access_token`（311 字符）/`cookie_header_template`（67 字符）/`sy_uid` 值：**0 命中**。
- 仅键名/cookie 长度（375）/声明时效（1790595614）入件。

## 9. Verified（逐项等级 + 未直读项）
| 项 | 等级 | 依据 |
|---|---|---|
| `item.data.query_form_data` 契约（method/path/DTO/写门） | VERIFIED_STATIC_BYTECODE | E3 UdcFormDataQueryController（L106/L57/L135）+ E4 registry L72 |
| `item.serial.select_entity_list` 契约 | VERIFIED_STATIC_BYTECODE | E3 UdcSerialConfigController（L648/L679/L1168） |
| `item.meta.function_node_tree` 契约 | VERIFIED_STATIC_BYTECODE | E3 UdcFunctionNodeController（L110/L123） |
| `item.serial.select_entity_list` **执行面** | **LIVE（PASS，非空业务样本 18 实体）** | E1 send#2：200/BOOT_0000/3755 B/traceId `3252117687647602876`/18 实体 |
| `item.meta.function_node_tree` **执行面** | **LIVE（对照，200 达数据面）** | E1 send#1：200/BOOT_0000/205298 B/traceId `3252117671340148924` |
| `item.data.query_form_data` **执行面** | **已调用但业务数据未验证（status=3，非 BOOT_0000）** | E1 send#3/#4 + E2：3 种入参全 status=3；服务端揭示必填链 appName→entityFullName→dataId；**非空样本未达成** |
| `data/query` 行键 `dataId` 的枚举手 | **UNVERIFIED（本件未探测、未登记）** | §7 硬边界；非本阶段范围（不扩 connector/写路径） |
| test2 网关 service 前缀有效性 | **LIVE 实证**（带前缀 200 达数据面） | E1 全部 send url 含 `/service/{app}` 且 200 |
| 凭据真实有效窗 | UNVERIFIED（声明过期值 + 实测被接受，二者并记） | E1 credential 块；§7 |
| 宿主侧副作用（3 面） | UNVERIFIED（只读面，无写路径证据） | §6 |

**未直读项（如实登记）**：`data/query` 非空业务样本未达成（缺 `dataId` 枚举手）；`udc-runtime/data//query` 双斜杠归一化未探测；
宿主侧副作用未观测；test2 凭据真实有效窗 UNVERIFIED。本件**未进入 connector 阶段、未新建测试应用、未发任何写请求**。

## 溯源索引（可复现）
| 项 | 路径 |
|---|---|
| LIVE 原始（4 发） | `core/facts/item-mgmt/evidence/live-probe-item-master-data.json`（11260 B / `342b23e1…`） |
| LIVE 补证（1 发，修正字段） | `core/facts/item-mgmt/evidence/live-probe-data-query-corrected.json`（1985 B / `962b6737…`） |
| 字节码（3 件 VERBATIM） | `core/facts/item-mgmt/evidence/bytecode/{UdcFormDataQueryController,UdcSerialConfigController,UdcFunctionNodeController}.javap.txt` |
| 字节码原件 | `docs/audit/artifacts/udc-entity-5.3.517/UdcFormDataQueryController.javap.txt`、`docs/audit/artifacts/udc-entity-5.3.517/UdcSerialConfigController.javap.txt`、`docs/audit/artifacts/udc-flow-5.3.517/UdcFunctionNodeController.javap.txt` |
| 写门源码 | `components/platform_operations/models.py` L46-48；`components/platform_operations/layer.py` L22-23 |
| registry 契约锚 | `components/platform_operations/registry.py` L47/L72/L102 |

> 自报（写后实测）：HEAD `dc12ef3`；E1 `342b23e1…`(11260 B)、E2 `962b6737…`(1985 B)、E3 三件 sha 与原件相等（VERBATIM）；
> 凭据值 0 入件（§8.3 自检通过）；本件写后 `wc -c` 实测值见 RESULT（此处不回填以免自指漂移）。
