# 微流程契约候选取证（R1 · 离线取证 P2/P3）

- round: R1 · phase: 取证-离线（P2/P3）
- 证据等级: **VERIFIED_STATIC_BYTECODE**（离线反编译 javap，离线，**非 LIVE**）
- 本文件为唯一产出物（R1）。仅记录离线字节码证据，不含任何 LIVE/活体观测。
- 两版本严格分开标注，**不混写**：
  - 客户侧 = `customer-web-1.0.11029`（客户应用 `app9000000000000000001`）
  - UDC 运行态 = `udc-runtime-5.3.517`（jar `com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar`）

## 判定总则（只读 vs 执行）
- 只读 A1 候选 = `method=GET` 且端点读「定义/节点/绑定/版本」。
- 执行型 = 走 `SingleRequest.from(obj)` → `AppServiceImpl`（POST/写路径），**不得入 A1 只读 registry**，仅记 EXECUTE/写路径。

---

## 候选契约表（≥3 条，每条 locator 齐备 8 要素）

| # | artifact (版本) | class 全限定名 | method | 路径原文 | 请求参数 | 响应类型 | 证据等级 | 只读/执行判定 |
|---|---|---|---|---|---|---|---|---|
| C1 | `udc-runtime-5.3.517`（jar `udc-starter-runtime-5.3.517.jar`，class 字节 SHA-256 `efd8f914…b748`） | `com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController` | `selectFunctionNodeTreeMetaData(String appName)` | `udc-runtime/meta-data/select-function-node-tree/{appName}`（类级 `@RequestMapping("udc-runtime/meta-data")` + 方法级 `@GetMapping("select-function-node-tree/{appName}")`） | `String appName`（`@PathVariable`，包装为 `SingleRequest<String>`） | `ListResponse<UdcFunctionNodeMetadataDto>` | VERIFIED_STATIC_BYTECODE | **只读 GET（A1 候选）** |
| C2 | `udc-runtime-5.3.517`（同 jar；javap.txt 字节 SHA-256 `a582ec33…b8e8`） | `com.seeyon.boot.starter.udcrt.controller.GraphqlProxyController` | `doGraphql(GraphqlProxyRequestDto)` | `udc-runtime/graphql-proxy/graphql`（类级 `@RequestMapping("udc-runtime/graphql-proxy")` + 方法级 `@PostMapping("graphql")`） | `@RequestBody GraphqlProxyRequestDto`（内部经 `SingleRequest.from(obj)` 调 `GraphqlProxyAppService.doGraphQL`） | `SingleResponse<String>` | VERIFIED_STATIC_BYTECODE | **执行型 POST（排除出 A1，记 EXECUTE/写路径）** |
| C3 | `customer-web-1.0.11029`（应用 `app9000000000000000001`；javap.txt 字节 SHA-256 `98cab117…ba7`） | `com.seeyon.9000000000000000001.controller.MicroFlowCkqxrypzbxqyController` | `mFSERVICEUjSZps(Long)` | `MicroFlow` 业务路径（`mFSERVICE*` 微流程服务方法；`SingleRequest.from(obj)` → `MicroFlowAppServiceImpl.mFSERVICEUjSZps`） | `Long`（`SingleRequest` 包装） | `SingleResponse<Boolean>` | VERIFIED_STATIC_BYTECODE | **执行型（POST 写路径，排除出 A1）** |
| C4 | `customer-web-1.0.11029`（同应用；javap.txt 字节 SHA-256 `8b9c66d1…035`） | `com.seeyon.9000000000000000001.controller.MicroFlowHtspkhlshzziyemianController` | `mFSERVICEaCPF3j()` / `mFSERVICE9sZKQc(String)` | `MicroFlow` 业务路径（`mFSERVICE*` 微流程服务方法；`SingleRequest.from(obj)` → `MicroFlowAppServiceImpl.*`） | 无参 / `String`（`SingleRequest` 包装） | `SingleResponse<Map<String,?>>` / `SingleResponse<Dyhtxqlsjyqkxgxxcc>` | VERIFIED_STATIC_BYTECODE | **执行型（POST 写路径，排除出 A1）** |
| C5 | `udc-runtime-5.3.517`（同 jar；`UdcRestPathParse` javap.txt 字节 SHA-256 `3a4d8e90…026`） | `com.seeyon.boot.starter.udcrt.proxy.UdcRestPathParse` | `parseMicroFlowRequestDtoByRest(UdcRestPathParseDto, T)` / `parseRestPath2Dto(UdcRestPathParseDto, String)` | 非 HTTP 端点（内部路径解析工具类，方法常量池出现 `microflow` / `microflow/` 字面量；`UdcRestPathParseBaseDto` 字段 `microFlowCode`/`restMethod`/`restPagePath`） | `UdcRestPathParseDto`（含 `microFlowCode`、`restMethod`、`restPagePath`） | `UdcMicroFlowRequestDto` / `UdcRestPathParseDto` | VERIFIED_STATIC_BYTECODE | **非契约端点（结构证据，用于确认微流程 REST 路径形态，非 GET/POST 端点，不入 registry）** |

---

## 逐条判定小结
- **只读 GET 候选（可入 A1）**：仅 **C1** `UdcFunctionNodeController.selectFunctionNodeTreeMetaData`。
  依据：类级 `@RestController` + `@RequestMapping("udc-runtime/meta-data")`，方法级 `@GetMapping("select-function-node-tree/{appName}")`，入参 `@PathVariable appName`，经 `SingleRequest.from(appName)` → `UdcFunctionNodeAppService.selectFunctionNodeTreeMetaData` → `UdcFunctionNodeService.selectFunctionNodeTreeMetaData(appName)`，读「函数节点树元数据」（`ListResponse<UdcFunctionNodeMetadataDto>`）——读定义/节点元数据，**只读**。
- **执行型（排除出 A1，记 EXECUTE/写路径）**：**C2**（POST graphql 代理）、**C3 / C4**（客户 `MicroFlow*Controller` 走 `SingleRequest.from(obj)` → `MicroFlowAppServiceImpl` 的 `mFSERVICE*` 微流程方法，POST 写路径）。
- **非端点结构证据**：**C5** 仅用于佐证微流程 REST 路径形态与 `microFlowCode`/`restMethod` 绑定字段，不作为 registry 契约候选。

## 缺口清单（哪些端点盘上拿不到，须 P1/P3）
1. **微流程「定义/版本/绑定」的 GET 只读端点在离线盘上缺失**：本刀仅 C1 一条 GET（读函数节点树）。微流程本体定义（`microflow` 路径 + `microFlowCode`/`restMethod` 绑定）的只读 GET 定义端点，在 `udc-runtime-5.3.517` 与 `customer-web-1.0.11029` 的已盘 javap 中**未出现**（客户 `MicroFlow*Controller` 全部为 `mFSERVICE*` 执行型，无 `@GetMapping`；`UdcRestPathParse` 只是解析工具类，非端点）。
   - 需 **P1（test2 部署 jar）** 取 UDC Pod 内 `udc` jar，反编译微流程只读定义端点（`/service/{applicationId}/{业务路径}/microflow/{methodId}` 形态的 GET）。
   - 或 **P3（GraphQL 只读通道）**：C2 `doGraphql` 为 POST 入口，只读 GraphQL 查询模板需另取证。
2. 因此**本刀 R1 不判 OFFLINE-BLOCKED**（至少 C1 一条 GET 只读候选成立），但 A1 若需≥3 条只读定义契约，则缺口须 P1/P3 补齐——main 据此决定 R2 走向（选 C1 写 registry，或转 P1/P3 取证补齐只读定义端点）。

---

## 回读 8 要素齐备核对（self readback）
本文件已包含：artifact+版本（两版本分列）· class 全限定名 · method · 路径原文 · 参数（请求 DTO）· 响应类型 · 证据等级（全部 VERIFIED_STATIC_BYTECODE，无 LIVE）· 只读/执行判定。共 ≥3 条候选（C1–C5），明确标注唯一 GET=C1、POST 执行型=C2/C3/C4。缺口指向 P1 部署 jar / P3 GraphQL。两版本未混写。
