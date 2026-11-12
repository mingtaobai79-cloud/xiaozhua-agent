# udc.datatype.get_all｜数据类型字典查询（LIVE 2026-09-26 实测）

## 1. Capability
`udc.datatype.get_all`（registry 登记 ID）：返回平台数据类型字典的**全量列表**（只读）。
- 控制器：`com.seeyon.boot.starter.udcrt.controller.UdcDataTypeController#getDataTypes()`
- 返回：`com.seeyon.boot.transport.ListResponse<com.seeyon.boot.starter.udcrt.dto.DataTypeDto>`
- 语义：读面（DataTypeManager.getDataTypes(EMPTY_STRING_ARRAY) → BeanCopier.copyList → ListResponse.from）。
- 溯源：`components/platform_operations/registry.py` L49（evidence）/ L50（contract）。

## 2. Version
- 静态契约单元 = **5.3.517**（本机 Maven 仓 jar；`<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`，本会话实测 sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`，861880 B，472 entries）。
- class sha256（本会话自测，与 registry 登记值逐字一致）：
  `03b3977b50574208eaad2b1925a80520a4686b268a56bacd35b87a144854bc38`（1787 B）。
- LIVE 目标单元 = test2 网关，其镜像版本为 config 键 `environments.test2.udc_image_version` = **5.3.496**。
- ⚠ 两个证据单元不同源：本格 LIVE 结论绑定 5.3.496 运行态；字节码结论绑定 5.3.517。未做 5.3.496 字节码比对（UNVERIFIED）。

## 3. Input
- **无业务参数**：javap 方法签名 `getDataTypes()`（无参）；方法级 `@GetMapping(value=["getAll"])`，类级 `@RequestMapping(value=["udc-runtime/datatype"])`。
- URL 组装（键全部取自 `config/environments.yaml: environments.test2`，前缀不拼字面量）：
  `{gateway_base} + /service/{default_app_id} + /udc-runtime/datatype/getAll`
- 本会话实测解析值：`https://lowcode-test2.example.com/service/app9000000000000000001/udc-runtime/datatype/getAll`
  （证据 JSON `env_binding`：cred_base_eq_cfg=true / cred_app_eq_cfg=true / prefix_eq_template=true）。
- 溯源：javap 自测件 `core/facts/runtime/evidence/udc-datatype-controller-javap-selfrun-20260926.txt`（L115-116 `GetMapping value=["getAll"]`、L129-130 `RequestMapping value=["udc-runtime/datatype"]`）。

## 4. Required
- 必需：网关前缀 `/service/{appId}`（本会话 LIVE 确证该前缀对本族端点生效）+ 只读凭据（运行期按路径引用 `shared-credentials/test2-web-credential.json`；**值零落盘**）。
- 无必需业务入参（无 query、无 body）。越权/无凭据形态未实测（UNVERIFIED）。

## 5. Execution
- 只读 `GET`；响应 envelope 顶层键：`code / data / message / status / traceId`；列表位于 `data.content`。
- 本会话 LIVE（双发，identity=去 traceId 后 md5 相等）：
  - 第 1 发：HTTP 200 / 1822 B / `code=BOOT_0000` / `message=SUCCESS` / traceId `3247033516839405756`
  - 第 2 发：HTTP 200 / 1822 B / `code=BOOT_0000` / `message=SUCCESS` / traceId `3247033524305266876`
  - identity：**MATCH**（md5_no_trace `65e685f35e0050c029ffa16475bf9fa4`）
- 载荷规模：`data.content` = **13** 项；首元素字段名（仅记名，不落值）：
  `caption, dataFormat, databaseType, javaType, name, order, validate`。

## 6. Side Effects
无（只读 GET；无写路径、无状态变更证据）。registry `write=False`（L50）。

## 7. Known Constraints
- **前缀边界（本格主要修正点）**：正确前缀 `/service/{appId}/udc-runtime/datatype/getAll` 在 test2 生效（200/BOOT_0000/非空）。
  09-17 旧探测使用错误前缀 `/service/udc/datatype/getAll` → Whitelabel 404（`docs/operation-contracts/udc/microflow/live-evidence/C2_datatype_live_f1_20260917T160331Z.json`）。
  该 404 应归因于**网关前缀白名单**，不得归因于端点不存在——本会话 LIVE 反证端点存在且可达。
- registry L50 将「网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）」列为约束；本会话对该端点实测通过 → 该约束在本端点维度**已被 LIVE 解除**（其余未实测端点不随之解除）。
- 版本非同源（见 §2）：LIVE 目标为 5.3.496 镜像。
- 无凭据 / 越权访问形态未实测（UNVERIFIED）。

## 8. Evidence
- 本会话 LIVE 证据件：`core/facts/runtime/evidence/runtime-live-probe-20260925T163800Z.json`
  （sha256 `743eb9c96e1b88e4fbad1d6897d7eb9433f3e8d13bebf8d360f01b437b7a3028`，6461 B）
- 本会话 traceId：`3247033516839405756`、`3247033524305266876`
- 静态证据件（自测，非转述）：
  - `core/facts/runtime/evidence/udc-datatype-controller-javap-selfrun-20260926.txt`（sha256 `3d392b63ef75361713cba04fe797d0477e7e9c4181dce25c17e82bf8362ce742`；工具 `<LOCAL_ROOT>/java/bin/javap` JDK21；`SHA-256 checksum 03b3977b…`）
  - `core/facts/runtime/evidence/runtime-static-verify-20260926.json`（sha256 `9a3fb1a8371d58917c4187a899908442fe12496427f30a7fee471011b964c1d9`；jar/class 哈希自测输出）
- registry 行：`components/platform_operations/registry.py` L49-L50
- 环境键：`config/environments.yaml: environments.test2`（gateway_base / gateway_prefix_template / default_app_id / udc_image_version）

## 9. Verified
- **LIVE（本会话 2026-09-26）**：HTTP 200 + `BOOT_0000/SUCCESS` + **非空列表（13 项 DataTypeDto）** + 双发 identity MATCH → 端点、前缀、envelope 形态、列表非空均实测成立。
- **STATIC（自测字节码）**：契约路径/方法/返回类型 = VERIFIED_STATIC_BYTECODE（class sha256 自测值与 registry 登记值一致）。
- **UNVERIFIED**：DataTypeDto 各字段的业务语义映射（仅观测到字段名）；5.3.496 与 5.3.517 的行为等价性；无凭据/越权响应形态。
