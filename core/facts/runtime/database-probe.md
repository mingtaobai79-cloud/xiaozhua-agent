# udc.database.query_data｜运行态数据库取数（LIVE 2026-09-26 实测）

## 1. Capability
`udc.database.query_data`（registry 登记 ID）：按实体与数据 id 查询运行态数据库数据（只读）。
- 控制器：`com.seeyon.boot.starter.udcrt.controller.UdcRuntimeDatabaseController#queryData(RuntimeDataBaseQueryDataReqDto)`
  —— 方法体实测（javap 自测件 L91-92）：`SingleRequest.from(dto)` → `UdcRuntimeDatabaseQueryAppService.queryData(SingleRequest)`；方法签名 L83。
- 返回：`com.seeyon.boot.transport.SingleResponse<com.seeyon.boot.starter.udcrt.dto.UdcRuntimeDatabaseQueryRespDto>`
  —— 响应 DTO 字段（自测 javap）：`columnMetadata: List<UdcRuntimeDataBaseColumnMetadataDto>`、`dataList: List<Object>`。
- 溯源：`components/platform_operations/registry.py` L111（evidence）/ L112（contract）。

## 2. Version
- 静态契约单元 = **5.3.517**（jar `<MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`，本会话实测 sha256 `74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f`）。
- class sha256（自测，与 registry 登记值逐字一致）：`588bc1cf97cf53357ce0a851d16eb28244b6a9607aa5c813b80e4c2c8d4b3c48`（1876 B）。
- LIVE 目标单元 = test2 网关，镜像版本 config 键 `environments.test2.udc_image_version` = **5.3.496**（与静态单元不同源）。

## 3. Input
- 契约入参类型：`com.seeyon.boot.starter.udcrt.dto.RuntimeDataBaseQueryDataReqDto`。
- **入参字段（本会话 javap 自测实测）**：`java.lang.String entityFullName`、`java.lang.String ids`（继承 `com.seeyon.boot.transport.BaseDto`）。
  ⚠ **与 registry 登记不符**：registry L112 / `docs/operation-contracts/udc/entity/registry-entries.md` L251 记
  `RuntimeDataBaseQueryDataReqDto(dataSource,table,condition)`，本机 5.3.517 字节码中**不存在** `dataSource/table/condition` 三字段。
  本格以字节码实测为准，登记行疑为外推，需 main 侧转登修正（本格不改 registry，边界外）。
- 方法级/类级映射（自测 javap L107-108 / L116-117）：`@GetMapping(value=["query-data"])` + 类级 `@RequestMapping(value=["udc-runtime/database"])`。
- **方法无任何参数绑定注解**（javap 全类 0 处 `RuntimeVisibleParameterAnnotations`；与 `docs/operation-contracts/udc/menu/P5-udc-database-query-data.md` L8 判断一致）。
- URL 组装（键取 `config/environments.yaml: environments.test2`）：`{gateway_base} + /service/{default_app_id} + /udc-runtime/database/query-data`。

## 4. Required
- 必需：网关前缀 `/service/{appId}` + 只读凭据（运行期按路径引用 `shared-credentials/test2-web-credential.json`，值零落盘）。
- 业务参数：实测入参名为 `entityFullName` / `ids`；逐键必填性未单键实测（UNVERIFIED）。
- 参数通道（LIVE 判定）：**query string**，非请求体（见 §7）。

## 5. Execution
- 只读 `GET`；envelope 顶层键 `code / data / message / status / traceId`。
- 本会话三支实测（每支双发，identity=去 traceId 后 md5 相等）：
  | 支 | 路径/入参 | HTTP | 字节 | envelope | traceId（1/2 发） | md5_no_trace | identity |
  |---|---|---|---|---|---|---|---|
  | B | 无体 | 200 | 90 | BOOT_3000（message 空） | 3247033528533125308 / 3247033532727429308 | 4979bebcd1ae4ceff251114e5195cbf7 | MATCH |
  | C1 | 体 `{dataSource,table,condition}` | 200 | 90 | BOOT_3000 | 3247033536837847228 / 3247033540763715772 | 4979bebcd1ae4ceff251114e5195cbf7 | MATCH |
  | C2 | 体 `{entityFullName,ids}` | 200 | 90 | BOOT_3000 | 3247033544857356476 / 3247033548867111100 | 4979bebcd1ae4ceff251114e5195cbf7 | MATCH |
  | C3 | query `?entityFullName=x&ids=x` | 200 | 118 | BOOT_3000 / message=`String index out of range: -12` | 3247033552994306236 / 3247033557205387452 | 20e87a2e236f779c2b243ad162377991 | MATCH |
- 关键比较：C1、C2 的 md5 与无体 B **逐字相同** → 请求体未被绑定（两组键均无效）；
  C3 的 md5 与 B **不同**且返回解析异常 → query 参数确被送达并进入业务解析（值 `x` 非法，非"参数缺失"）。
- 取样最小化：本支未取到任何数据行，故无行数据落盘（0 行 / 0 字段名）。

## 6. Side Effects
无（只读 GET；registry `write=False`（L112）；三支响应均为业务码，无写入证据）。

## 7. Known Constraints
- **GET 带请求体语义（registry 自注 UNVERIFIED）→ 本会话 LIVE 判定 = 不生效（bound: NO）**：
  无 `@RequestBody`/参数注解（字节码），且带体请求的响应与无体响应 md5 完全相同（两次独立键组均如此）。
  实际入参通道 = **query 参数**（C3 证明参数被送达）。**禁止**再按"GET 携带请求体"实现调用方。
- **数据返回语义 = UNVERIFIED**：未取得该 app 的真实合法 `entityFullName`/`ids` 样本（禁臆造、禁外推），
  故"有数据返回"路径未实测。**解阻动作（唯一）**：以运行态可枚举的真实样本（该 app 实体枚举 + 真实数据 id）做**单支**只读 GET 复测。
- **基数边界**：无体 / 带体一律 `BOOT_3000`（空结果业务码，HTTP 200）——该码在本端点是"无结果/条件不满足"形态，
  不得读作端点不可用。
- **历史基线复现**：`docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md` 行 6（2026-09-18：200 / 90 B / BOOT_3000）
  本会话 B 支逐字复现（同为 90 B，md5 见 §5）。
- 版本非同源（5.3.517 字节码 vs 5.3.496 运行镜像）。

## 8. Evidence
- 本会话 LIVE 证据件：`core/facts/runtime/evidence/runtime-live-probe-20260925T163800Z.json`
  （sha256 `743eb9c96e1b88e4fbad1d6897d7eb9433f3e8d13bebf8d360f01b437b7a3028`，6461 B）
- 本会话 traceId：`3247033528533125308`、`3247033532727429308`（B）；`3247033536837847228`、`3247033540763715772`（C1）；
  `3247033544857356476`、`3247033548867111100`（C2）；`3247033552994306236`、`3247033557205387452`（C3）。
- 静态证据件（自测，非转述）：
  - `core/facts/runtime/evidence/udc-runtime-database-controller-javap-selfrun-20260926.txt`（sha256 `934e0d9bfc5e3f735333e4ef8031c15850ce7a1dfe746b898f3a9c47728ace5c`）
  - `core/facts/runtime/evidence/udc-runtime-database-req-dto-javap-selfrun-20260926.txt`（sha256 `a38e5983bdb51682ff16b242bdaa420f799eecd2b05cbdcba8355240f9f43938`）
  - `core/facts/runtime/evidence/udc-runtime-database-resp-dto-javap-selfrun-20260926.txt`（sha256 `c6941015ed2f406d9877a4665117af692652d05389345dac64ada08d0d5666d7`）
  - `core/facts/runtime/evidence/runtime-static-verify-20260926.json`（sha256 `9a3fb1a8371d58917c4187a899908442fe12496427f30a7fee471011b964c1d9`）
- 在盘文档：`docs/audit/artifacts/udc-entity-5.3.517/LIVE-readback.md` 行 6；`docs/operation-contracts/udc/menu/P5-udc-database-query-data.md` L8（无参数注解判断）。
- registry 行：`components/platform_operations/registry.py` L111-L112。

## 9. Verified
- **契约层 = VERIFIED_STATIC_BYTECODE（自测）**：路径 `udc-runtime/database/query-data`、方法 `GET`、返回类型
  `SingleResponse<UdcRuntimeDatabaseQueryRespDto>`；jar/class sha256 自测值与 registry 登记值一致。
- **LIVE（本会话）**：端点可达 + 无体基线（200/90 B/BOOT_3000）+ 双发 identity MATCH；
  **GET 带请求体语义 = NOT BOUND（带体无效）**、入参通道 = query 参数（C1/C2 与 B 同 md5，C3 因参数送达而响应变化）。
- **UNVERIFIED**：数据返回路径（无真实合法样本）；`entityFullName`/`ids` 的合法取值形态与必填性；
  5.3.496 与 5.3.517 行为等价性；无凭据/越权形态。
- **本格产出的登记修正请求（属 main 侧动作）**：registry L112 与 `registry-entries.md` L251 的
  `(dataSource,table,condition)` 字段清单与字节码不符，建议改为 `(entityFullName,ids)` 并撤下"GET 携带请求体"注解。
