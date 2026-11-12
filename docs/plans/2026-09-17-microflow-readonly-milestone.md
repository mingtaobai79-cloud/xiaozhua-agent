# 微流程只读里程碑（M1）实施方案

状态：待执行（main 主控）
适用仓库：`<SEEYON_AGENT_ROOT>`
基线：HEAD `a799744`，工作区干净，离线全量测试 309 passed

## 一、已核实的基线事实

现有能力（不重复建设）：

- `PlatformOperationLayer` 是唯一执行边界：只在「契约生效 + method=GET + write=false + auth_scope 含 `<appId>:readonly`」时放行；否则 DENIED/POLICY_DENIED，缺执行上下文 BLOCKED，契约未声明 UNVERIFIED，读回空集合判 BUSINESS_NOT_FOUND，身份对不上判 UNVERIFIED。
- 23 条 UDC operation contract，全部源自反编译 `com.seeyon.udc.controller.EntityController`（`udc-web-5.3.517.jar`，证据级 VERIFIED_STATIC_BYTECODE）；其中 6 条为写操作（entity.create/update、attribute.create/create_batch/update/delete），已声明但被策略拦截。
- gateway 只读通道齐备：`components/gateway/`（client / credentials / discovery / adapter / filters / models）；凭据按 ref 临时解析、不落盘；网络默认关闭，`--allow-network` 才开。
- CLI 26 个子命令，主体是离线审计/取证（audit-bundle、evidence-ledger、udc-path-matrix、impact-graph、version-audit、artifact-inventory、runtime-report、integration-report、diagnostic-report、provider-capabilities、capabilities、module-catalog、test-report），执行入口为 `dry-run` / `udc-execute` / `op-execute`。

缺口（本轮要填的坑）：

- `docs/operation-contracts/udc/microflow/` 为空目录（0 文件）→ 微流程零契约 → 任何微流程操作只返回 UNVERIFIED「operation contract is not declared」，连只读都读不了。
- 设计态证据缺失：`docs/audit/artifacts/udc-design-targeted-5.3.517` 为空；`docs/audit/udc-design-artifact-availability-evidence.md` 记录 udc-biz / udc-web / udc-assemble / udc-extend 等设计态模块在本地 Maven 仓库 MISSING，状态 BLOCKED / UNVERIFIED。这是「做微流程」的卡点，同一缺口也影响「看微流程」的设计态读取。

现有微流程相关证据（可作为起点，不得凭业务名推测）：

- `docs/audit/modules/decompiled/udc-facade-5.3.517-MicroFlowInfoAppService.java`：仅 `findCallConnectorAppService` / `findCallIntegrationAppService` 两个方法（AppService 层，非 REST）。
- `docs/audit/artifacts/customer-web-1.0.11029/CustomRestApiMicroFlowController.javap.txt`（**客户场景证据，已迁出至 `seeyon-customer-evidence/javap/`**，仓库内已无此路径） 及同目录大量 `MicroFlow*Controller.javap.txt`（客户应用 app9000000000000000001 的微流程页面控制器）。
- `docs/audit/artifacts/udc-runtime-5.3.517/`：`UdcFunctionNodeController.javap.txt`、`GraphqlProxyController.javap.txt`、`UdcRestPathParse.javap.txt`、`EntityRuntimeService.javap.txt` 等 25 份。
- 已知客户应用微流程路径形态（来自 `seeyon-low-code-environment` skill 的应用路由约定）：`{base}/service/{applicationId}/{业务路径}/microflow/{methodId}`，Controller 侧由 `@RestApi("微流程-xxx")` + `@RequestMapping("{applicationId}")` + `@PostMapping("{业务路径}/microflow/{methodId}")` 反查；拼接必须保留 `/service/` 前缀，应用 ID / 路径 / 方法 ID 按注解原值保留。

## 二、本轮目标

把「看微流程」做成可验证的**只读**能力：契约 + 只读调用 + 回读证据。**不做写**。

## 三、验收标准（A1–A6 缺一不可）

- A1 微流程只读契约 ≥3 条写入 registry（可独立 microflow registry），每条必须绑定：来源 artifact + version + class + method + 路径原文 + 参数 + 响应类型 + 证据等级。禁止用业务名拼路径、禁止只凭类名推断。
- A2 ≥1 条在 test2 上 LIVE PASS：同一 target 回读成功且 `identity_matches=true`；HTTP 200 或非空响应不单独等于 PASS。
- A3 证据落 `docs/operation-contracts/udc/microflow/`（当前空目录），并能被 evidence ledger / audit-bundle 聚合。
- A4 离线全量 pytest 通过（基线 309 passed）+ 新增契约有单测；文档契约计数测试（README/审计文档计数 = pytest 收集数）同步更新。
- A5 写路径保持 POLICY_DENIED，本轮不新增任何写能力。
- A6 结论回答三件事：能读什么（微流程定义 / 节点 / 绑定关系 / 版本）、精确怎么读（路径 + 参数 + 返回）、哪些仍 UNVERIFIED / BLOCKED 及精确缺口。

## 四、取证顺序（按证据强度，逐条推进，一次一个动作）

- P1 运行态/部署态 jar（最强）：SSH `root@10.0.0.1`（key 见访问材料）→ 远端执行 `kubectl --kubeconfig=configtest2` → 定位 UDC 应用 Pod/镜像 → 取 udc 相关 jar → 反编译微流程 Controller → 路径 + DTO + 类归属。
- P2 客户侧已落地 javap：`docs/audit/artifacts/customer-web-1.0.11029/` 下的微流程 Controller → 提取路径形态与入参，交叉验证 P1。
- P3 平台 metadata / GraphQL 通道：`UdcFunctionNodeController` / `GraphqlProxyController` / `UdcRestPathParse` 已有 javap → 判断微流程定义读取是否走 metadata 查询接口而非专用 Controller。
- P4 活体只读探测：对 `https://lowcode-test2.example.com` 发只读查询请求做交叉验证；凭据只从本机环境变量或私密文件读取，不落盘、不进对话、不写进产物。

## 五、访问材料（全部只读）

- `<HERMES_HOME>/skills/devops/seeyon-low-code-environment/.env`：`SEEYON_SSH_*`、`SEEYON_KUBECONFIG_TEST2`、`SEEYON_KUBECONFIG_UAT`、`SEEYON_DB_*`、`SEEYON_REDIS_*`、`SEEYON_K8S_NAMESPACE`、`SEEYON_ENV`
- 同目录 `low-code-test.pem`（仅用于 10.0.0.1）、`kubeconfig-zhiyuan`（作为 test2 kubeconfig 使用）
- 同目录 `SKILL.md`：环境识别、凭据边界、Pod 诊断、Redis/MySQL 访问规范
- 应用基址 `https://lowcode-test2.example.com`；业务路径形态 `/service/{applicationId}/{业务路径}`
- 本机命令：`uv run --quiet --with pytest python -m pytest tests -q`（本机 python 无 pytest，必须走 uv）

## 六、约束（硬约束）

- 只读。写操作、发布、部署、数据库/Redis 修改本轮一律不做。
- test2 命令必须 SSH 到 `10.0.0.1` 后在远端执行 `kubectl --kubeconfig=configtest2`；禁止连接 `10.0.0.1`；禁止擅自追加 `-n low-code`（namespace 由远端 context 决定）。
- 证据等级不得升级：STATIC_CONTRACT < VERIFIED_STATIC_BYTECODE < LIVE。本地 5.3.517 与服务器镜像版本若有差异必须分别标注，不混写。
- 不打印密钥、密码、cookie、accessToken；产物中一律脱敏。
- 客户业务明细（微流程实例数据）只按任务临时查询，不进长期事实库；只沉淀平台机制与契约。
- 一个 ROUTE 一个动作；implementer 只执行当前切片；auditor 只审当前切片。
- 允许本地 git commit，禁止 push；每个提交要能看出证据来源。

## 七、停止条件

- A1–A6 全部满足 → 本轮终态（是否写 FINAL 由 main 决定）。
- 或 P1–P4 全部有证据地 BLOCKED → 转 NEEDS_HUMAN，并列出精确缺口（缺哪个 artifact、凭据、路径或授权），不得只写「无法推进」。
