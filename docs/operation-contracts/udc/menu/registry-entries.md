# registry-entries — 菜单域只读契约建议条目（供 UDC-MERGE 任务照抄）

不实际改 registry.py（冻结文件）。字段顺序与 `models.py` `UdcOperationContract` 10 字段构造签名逐字段一致：
`operation_id, method, path, request_type, response_type, status, write, evidence, required_inputs, verification_rules`。
条目风格照抄 registry.py L44–L51（evidence 用 dict、required_inputs/verification_rules 用元组、write=False、status=OperationStatus.VERIFIED_STATIC_BYTECODE）。

jar 基线：`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`
jar sha256 = `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`（74ae50bd...06f）

> **NOTE（LIVE-13, 跨文件网关前缀口径说明）**: 网关 service 前缀在离线字节码层面
> UNVERIFIED / 禁止拼前缀（本构造参数口径不变，MERGE 照抄离线部分）；test2 LIVE 侧实测
> 前缀=/service/app9000000000000000001，源 docs/audit/evidence 同级 test2-live-route-facts.json
> （HUMAN 探测非转述），供 LIVE 开火参考，不进离线证据链。

## 与已登记条目的关系（MERGE 前必读）
- **P2 = udc.applog.datalog/{id} 已存在于 registry.py L51 `udc.applog.select_by_id`**（同路径、同 controller、同 method、class_sha256 f6a2111d... 一致）→ MERGE 时 P2 **不新增条目**，直接复用 `udc.applog.select_by_id`（本任务契约 P2 文档保留作域内证据映射）。
- P3、P4 为 registry.py 尚无的新条目，照抄下方构造。**P1 udc.role.has_system_admin 已被并行 entity 会话登记于 registry.py L108**（同 UdcRoleRtController class_sha256 `ed0248…` + 同 method `search` + 同 path + GET + `SingleResponse<Boolean>`，等价）→ **MERGE 时 P1 不新增**，按去重/合并处理。差异（供 MERGE 取舍）：本任务 P1 版 `request_type` 更精确（`String appName(@PathVariable)` vs L108 `java.lang.String`）、`verification_rules` 3 项含 identity_matches 双读 + 网关前缀 UNVERIFIED 标注（L108 仅 1 项"响应 SingleResponse 包裹 Boolean"）；evidence `javap` 目录 menu vs entity（同 class SHA ed0248）。**保留 entity L108 还是并入本 P1 精确版属跨会话业务取舍，由 MERGE 定**；本文件 L36+ 的 P1 构造文本保留作"精确版参照"。
- P5（udc.database.query-data）入参绑定 HYPOTHESIS（javap 回读：方法块无 RuntimeVisibleParameterAnnotations，全文件出现 0 次）→ **不入 registry**。

> **⚠ 盘面易漂移警示（main, 07:33 北京 实测; MERGE 落库前必读）**: 本节「P1/P3/P4 为 registry.py 尚无的新条目」
> 基于 R2 时点 registry.py 快照。main 07:33 对**当时** registry.py（mtime 07:32:33, 被并行微流程会话
> session-20260917-175618 活跃改写）grep + 只读 import 枚举 62 已登记 operation_id 实测:
> - **`udc.role.has_system_admin` 已存在于 registry.py L108**（`ent_role_evidence`，非本菜单域所登记）
>   → 与 P1 同名，**MERGE 直接新增 P1 会 key 冲突**；P1 改按去重/合并处理，或确认 L108 条目
>   evidence/verification_rules 与本 P1 一致性后择一保留。
> - `udc.applog.datalog_list_by_data_id`（P3）、`udc.serial_config.entity_list`（P4）实测**仍唯一**，可新增。
> - `udc.applog.select_by_id`（P2 去重目标）存在，P2 去重成立不变。
> registry.py 属并行会话冻结写盘、盘面随时间漂移（R9 曾记 04:50 盘面，现 07:32 又变）。**MERGE 落库时
> 务必对当时的 registry.py 重新实测 key 唯一性（`grep -cE 'contracts\["<op>"' registry.py`），勿以本文件
> 时点断言为准。** 本注只登记盘面事实，不改上方 3 条构造行（构造文本本身仍逐字正确，仅 P1 目标 key
> 可能需 MERGE 去重/合并）。

## 建议构造调用（可直接并入 UdcOperationRegistry.default()）

> **MERGE 执行 guard（LIVE-16, 收交付物 #3 内部矛盾; 0 删纯追加, python 块 3 构造行逐字不动）**:
> 本段 python 块含 P1/P3/P4 三条构造, 但 **MERGE 盲追加 3 行会撞 registry.py L108 已有 key**, 执行前必须按本 guard 分流:
> 1. **P3 `udc.applog.datalog_list_by_data_id`、P4 `udc.serial_config.entity_list`**: registry.py 尚无的新条目,
>    照抄 python 块 L53/L56 两行追加（含各自 evidence 行 L52/L55）。
> 2. **P1 `udc.role.has_system_admin`**: 已存在 registry.py L108（entity 会话 ent_role_evidence 登记）,
>    本 python 块 L50 该条 **仅作精确版参照**, MERGE **勿直接追加**（会撞 L108 key）; 按下方
>    「P1 ↔ L108 字段对账表 + 合并建议」段去重合并: 保留 L108 登记位, 取 P1 更精确 `request_type`
>    （`String appName(@PathVariable)`）并入 L108 + verification_rules 取并集（P1 3 项 + L108
>    「true=系统管理员」语义注）, evidence 取 entity 侧 1 份（menu_role_evidence 仅旁证）。
> 3. **盘面漂移**: L108/本文件均可能被并行会话改动, MERGE 落库前以 MERGE 时点
>    `grep -n 'udc.role.has_system_admin' components/platform_operations/registry.py` 实测为准,
>    漂移则按对账表重做取舍（L108 现值锚定 registry.py mtime 09-20 07:32）。

```python
menu_role_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcRoleRtController", "method": "search", "class_sha256": "ed024802b6c205041e4368840993412be184ff67c5f9b12938bee5a13a2aae47", "javap": "docs/audit/artifacts/udc-menu-5.3.517/UdcRoleRtController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.role.has_system_admin"] = UdcOperationContract("udc.role.has_system_admin", "GET", "udc-runtime/udc-role/has-system-admin/{appName}", "String appName(@PathVariable)", "SingleResponse<Boolean>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [menu_role_evidence], ("appName",), ("同一 appName 回读权限判定 identity_matches", "响应 Boolean 非 None", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

menu_applog_list_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcAppLogController", "method": "selectAppDataByDataId", "class_sha256": "f6a2111d3f5fd28b7c84d7eb1dddacd42ca38ffa0be194f2c34550faed2ee775", "javap": "docs/audit/artifacts/udc-menu-5.3.517/UdcAppLogController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.applog.datalog_list_by_data_id"] = UdcOperationContract("udc.applog.datalog_list_by_data_id", "GET", "udc-runtime/app-log/datalog/list-by-dataid/{dataId}", "Long dataId(@PathVariable)", "ListResponse<UdcEntityMonitorLogDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [menu_applog_list_evidence], ("dataId",), ("同一 dataId 回读日志列表 identity_matches", "响应 UdcEntityMonitorLogDto 列表", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))

menu_serialcfg_evidence = {"source": "local-maven-53517", "artifact": "udc-starter-runtime-5.3.517.jar", "version": "5.3.517", "class": "com.seeyon.boot.starter.udcrt.controller.UdcSerialConfigController", "method": "selectEntityList", "class_sha256": "fe1e5a72d7a25b34c566a9f49dbd47461c0abe54735dbd190b62203b07f81658", "javap": "docs/audit/artifacts/udc-menu-5.3.517/UdcSerialConfigController.javap.txt", "evidence_level": "VERIFIED_STATIC_BYTECODE"}
contracts["udc.serial_config.entity_list"] = UdcOperationContract("udc.serial_config.entity_list", "GET", "udc-runtime/serial-config/select-entity-list", "String appName(@MultiRequestBody)", "SingleResponse<EntityGroupAndItemDto>", OperationStatus.VERIFIED_STATIC_BYTECODE, False, [menu_serialcfg_evidence], ("appName",), ("同一 appName 回读实体组与项 identity_matches", "响应 EntityGroupAndItemDto 非空", "MultiRequestBody 经 GET 的传参约定 UNVERIFIED（LIVE 需实测；离线负证据：全域 52 POST 先例 0 GET，P4 为 GET+@MultiRequestBody 唯一法，LIVE 首验优先请求体假设，详见 docs/audit/artifacts/udc-menu-5.3.517/multi-request-body-get-binding.md；LIVE 注：传参形态 LIVE 实测 ?appName= 查询串有效（2026-09-20 10:35:33 开火 200+SUCCESS+entities 非空，见 main/LIVE-READBACK-VERIFIED.md）", "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）"))
```

## P1 ↔ registry.py L108 `udc.role.has_system_admin` 字段对账表 + 合并建议（LIVE-15, MERGE 交付物 #3 收口）

L108 现值实测（registry.py mtime 09-20 07:32, `ent_role_evidence` + L108 构造行, grep 逐字）：
L107 evidence = source=local-maven / javap=`docs/audit/artifacts/udc-entity-5.3.517/UdcRoleRtController.javap.txt`
（该文件实测在位: 8107B, mtime 09-17 22:30）/ method=`search(String)` / class_sha256=ed0248…；
L108 构造 = operation_id/GET/同 path/`java.lang.String`/`com.seeyon.boot.transport.SingleResponse<java.lang.Boolean>`/
VERIFIED_STATIC_BYTECODE/False/required_inputs=("appName",)/verification_rules 1 项
"响应为 SingleResponse 包裹 Boolean（true=该 app 系统管理员）"。

| # | 字段 (UdcOperationContract 10 位) | L108 (registry.py, entity 域) | P1 (本文件 L37, menu 域) | 对账判定 |
|---|---|---|---|---|
| 1 | operation_id | `udc.role.has_system_admin` | `udc.role.has_system_admin` | 同 → 保留 L108 条目, P1 不新增（避免 key 重复） |
| 2 | method | `GET` | `GET` | 同 |
| 3 | path | `udc-runtime/udc-role/has-system-admin/{appName}` | 同 | 逐字同 |
| 4 | request_type | `java.lang.String` | `String appName(@PathVariable)` | 冲突=精确度层 → **建议取 P1 更精确值并入 L108** |
| 5 | response_type | `com.seeyon.boot.transport.SingleResponse<java.lang.Boolean>`（全限定） | `SingleResponse<Boolean>`（简写） | 同类型, 表述详略不同 → 取任一并注明（建议保留 L108 全限定, MERGE 不改动） |
| 6 | status | `VERIFIED_STATIC_BYTECODE` | 同 | 同 |
| 7 | write | `False` | `False` | 同 |
| 8 | evidence | `ent_role_evidence`（source=local-maven, javap=udc-entity-5.3.517 目录, method 记 `search(String)`） | `menu_role_evidence`（source=local-maven-53517, javap=udc-menu-5.3.517 目录, method 记 `search`） | 同 class UdcRoleRtController + 同 class_sha256 ed0248… + 同 artifact → **保留 1 份（建议留 L108 entity 侧, 已在 registry.py 不动冻结件）, P1 menu 侧仅作旁证**；若 MERGE 独立新增则 javap 路径二选一且须实测该目录 javap.txt 在位（两目录均已实测在位: entity 8107B 09-17 22:30 / menu 见 L36） |
| 9 | required_inputs | `("appName",)` | `("appName",)` | 同 |
| 10 | verification_rules | 1 项: "响应为 SingleResponse 包裹 Boolean（true=该 app 系统管理员）" | 3 项: "同一 appName 回读权限判定 identity_matches" / "响应 Boolean 非 None" / "网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）" | 冲突=口径层 → **建议取并集 = P1 3 项 + L108 语义注「true=该 app 系统管理员」**（共 4 项） |

**合并建议（可机械执行）**: 两条同 class（class_sha256 ed0248…）同 method（search）同 path 同
method/status/write/required_inputs, 实质等价, 冲突仅在「精确度/口径标注」层（#4 #5 #8 #10）→
**MERGE 去重为 1 条**（保留 L108 登记位, P1 不新增 key）, 字段取法:
- request_type ← P1 `String appName(@PathVariable)`（更精确）
- verification_rules ← 并集 4 项（P1 3 项 + L108「true=该 app 系统管理员」语义注）
- evidence ← 保留 L108 `ent_role_evidence` 1 份（menu 侧 menu_role_evidence 仅作旁证记录, 不入 registry）
- response_type ← 保留 L108 全限定写法（注明与 P1 简写同型）
- 若 MERGE 盘面时 L108 已漂移/被并行会话改动, 以 MERGE 时点 `grep -n 'udc.role.has_system_admin' registry.py`
  实测为准重做本表对账（本表锚定 L108 现值 mtime 09-20 07:32）。

## 逐字段说明
| 字段 | 取值规则 |
|---|---|
| operation_id | `udc.<域>.<操作>`，与已登记命名风格一致 |
| method | `GET`（javap verb 原值） |
| path | 类级 @RequestMapping value + 方法级 @GetMapping value 逐字拼接；**不含** `/` 开头（运行时控制器），**禁拼网关前缀**（对照 L46 microflow / L49 datatype 风格） |
| request_type | 参数名+类型+绑定注解（对照 L46 `String appName(SingleRequest)`、L51 `Long id(SingleRequest)` 风格；绑定注解按 javap 原值：@PathVariable / @MultiRequestBody） |
| response_type | 完整泛型写法（对照 L46 `ListResponse<UdcFunctionNodeMetadataDto>`） |
| status | `OperationStatus.VERIFIED_STATIC_BYTECODE` |
| write | `False` |
| evidence | dict 列表，逐条含 source/artifact/version/class/method/class_sha256/javap/evidence_level（对照 L45 microflow_evidence 风格） |
| required_inputs | 元组，路径变量/入参名 |
| verification_rules | 元组，含 identity_matches 回读 + 网关前缀 UNVERIFIED 如实标注（对照 L49/L51） |
