# SANDBOX-CONTRACT｜CODE 能力执行契约（Sandbox→Compile→Test→Validate→Execute）（A6）

> 基线：`docs/capability/ROADMAP-v2.md` @ git `d76f7af`（本文件是 §三"CODE 能力"与 §二目标态
> `modules/sandbox/`、`sandbox/` 的契约化展开，不新增定位/阶段）。引 ROADMAP 章节一律**实测范围
> §一~§七**（§七即"本文件即路线基线"结尾节；无 §八/§九——同 A5 更正口径）。
> 配套：`CAPABILITY-MODEL.md`（§2.2 CODE 型入口契约三要素）、`EVIDENCE-MODEL.md`（A4 四层 +
> OperationStatus 归并口径）。
> 铁律：**现状=未建，本文件只写契约不建实现**（TASK-GOAL 边界）；**Agent 禁直出 Java 直跑**
> （ROADMAP-v2 §三 原文）；凭据 0 入仓（只引对象标识与证据等级，不引 token/凭据值）；
> 无在盘证据处标 **UNVERIFIED / 未建**，不写成已实现。本文不实现任何 sandbox 代码（禁改 components/）。

---

## 一、五阶段契约正式定义（对齐 ROADMAP-v2 §三）

ROADMAP-v2 §三 原文：**"CODE 能力：配置表达不了的（复杂规则/校验/转换/三方调用），必须走
Sandbox → Compile → Test → Validate → Execute，禁止 Agent 直出 Java 直跑。"**

据此定义五阶段。每阶段给 **输入 / 输出 / 通过判据 / 失败回流边界**；未建阶段全部标 UNVERIFIED。

| 阶段 | 输入 | 输出 | 通过判据 | 失败回流边界 | 现状 |
|---|---|---|---|---|---|
| **Sandbox** | `compile_unit`（目标 Java 模块/包路径标识）+ `sandbox_dep`（JDK/三方 jar/pipeline 配置） | 隔离执行环境（独立 namespace + 沙箱镜像） | 环境可达、资源隔离成立 | 依赖缺失/环境不可达 → 停在本阶段，不进 Compile | **未建**（目标态，UNVERIFIED）|
| **Compile** | 上阶段产出的代码单元 + 编译工具链 | 可执行构件（class/jar） | 编译 0 error | 编译失败 → 回流 Compile 或 Sandbox（依赖问题） | **未建**（UNVERIFIED）|
| **Test** | 编译产物 + `test_binding`（关联 Test 集） | 测试报告（pass/fail + 覆盖断言） | 绑定 Test 全绿 | 测试失败 → 回流 Compile（修代码）或 Test（修断言） | **未建**（UNVERIFIED）|
| **Validate** | 通过测试的构件 + 校验规约（契约/边界/副作用断言） | 校验结论（可发布/不可发布） | 满足 Validate 判据 | 校验不过 → 回流 Test 或 Compile，不直放行 | **未建**（UNVERIFIED）|
| **Execute** | 已 Validate 的构件 + 宿主授权上下文 | 实际运行结果 + 证据（对象标识/回读断言） | 宿主授权执行、回读确证 | 执行失败 → 记录证据，禁 Agent 自行"再直跑" | **未建**（UNVERIFIED）|

> **红线**：Agent 全程**只产结构化 CODE 声明 + 证据**，不直出 Java 直跑；Execute 由**宿主授权**
> 执行（与 A1 第四节"只读 agent + 宿主执行"边界一致）。本契约定义的是**目标态闸门**，非已实现。

---

## 二、A3 §2.2 三要素 → 五阶段绑定

`CAPABILITY-MODEL.md` §2.2 的 CODE 型入口契约三要素，分别落入五阶段：

| 三要素（A3 §2.2） | 语义 | 绑定阶段 | 消费点 |
|---|---|---|---|
| `compile_unit` | 可编译代码单元标识 | **Sandbox**（+ Compile） | Sandbox 段取该单元；Compile 段编译之 |
| `test_binding` | 单元关联 Test 集 | **Test** | Test 段跑绑定 Test，全绿才进 Validate |
| `sandbox_dep` | 运行时依赖（JDK/三方 jar/pipeline 配置） | **Sandbox→Compile 前置** | 缺失则 Sandbox 段即失败，不进入后续 |

三要素在 A3 已标 **UNVERIFIED（Sandbox 未建）**；本文件不改其等级，仅给出**目标态绑定关系**，
不声称已实现。

---

## 三、现状=未建（TASK-GOAL 边界铁律，在盘事实）

**目标态目录未建（实测）**：ROADMAP-v2 §二 目标态 `modules/sandbox/`、`sandbox/`（Global 级）
在盘均**不存在**（`ls modules/ sandbox/` = No such file/directory）；`components/` 下无 sandbox
执行体实现（`components/platform_operations/` 现存仅 readonly 契约/写门/部署方案 data 生成，
不含 Compile/Validate/Execute 执行链）。→ **Sandbox 本体、Compile 链、Validate 判据 = 未建/UNVERIFIED**。

**在盘最接近的活体事实（当前替代门，非新 sandbox）**：
1. **test2 RELEASE 构建流水线 = 应用级 sandbox 部署（构建即部署）**。
   `docs/audit/udc-design-time-deploy-write-contracts.md` §一 关键认知修正（原文）："构建走的是
   **应用级 sandbox 部署**（`boot-starter-sandbox` 的 `UdcAppDeployService` + `PipelineProperties`
   流水线 + `SandboxK8sService`），不是实体级 `PublishStateController.update`"。这是**平台既有**
   部署侧 sandbox 能力（LIVE 实证），**不是**本 v2 待建的"CODE 型 Sandbox 契约"——两者勿混。
2. **写门 DENIED / POLICY_DENIED = 当前替代门禁**（`layer.py:22-23`，A4 已核）：
   `if contract.write or contract.method != "GET" or not contract.effective:` → `DENIED` +
   `ErrorKind.POLICY_DENIED`。即：在 v2 的 CODE 型 sandbox 建立之前，**写动作由 readonly 写门
   拦截、宿主执行**，作为五阶段 Execute 段"宿主授权"的**当前在盘替代门**。

> 结论：本文定义目标态五阶段闸门；**在盘现存的只有"构建即部署"这条平台部署侧活体链路 + readonly
> 写门替代**。不得把这两者在盘事实写成"v2 CODE sandbox 已实现"。

---

## 四、test2 sandbox 事实引用（只引在盘 LIVE 记录，凭据 0 入仓）

**来源文件：`docs/audit/evidence/nacos-udc.yaml`（seeyon.udc.sandbox / seeyon.udc.deploy 段，
test2 活体配置快照；本文件只引对象标识与键名，不引任何凭据/token 值）。** 实测键值：

| 键 | 在盘值（test2） | 语义（yaml 注释原话） |
|---|---|---|
| `udc.sandbox.enable` | `true` | "设计环境设置为 true, 非设计环境为 false" |
| `udc.sandbox.domain` | `lowcode-test2.example.com` | 沙箱应用运行态入口域名 |
| `udc.sandbox.name-space` | `lowcode-test` | k8s 运行沙箱宿主服务的命名空间（"建议使用独立空间方便控制资源"） |
| `udc.sandbox.deployEnv` | `lowcode-test` | udc 发布应用的目标环境标识 |
| `udc.sandbox.imageUrlPrefix` | `chit-acr-registry.客户方.com/chjh-external/app-sandbox:5.3.00` | 沙箱镜像地址前缀 |
| `udc.deploy.disableK8s` | `true` | deploy 段，同文件 L29 |

> 证据等级 = **LIVE**（test2 活体 Nacos 配置快照，`docs/audit/evidence/nacos-udc.yaml`）。
> 注意：这是**部署侧 sandbox 配置**，与 §三.2 的"应用级构建即部署"同属平台既有能力，
> **不是 v2 CODE sandbox 已实现**的证据；引它只为说明 test2 侧已有 sandbox 宿主设施可作目标态参考。

**相关在盘版本锚（对照，非混淆）**：`config/environments.yaml` 实测 test2 `udc_image_version: "5.3.496"`
（注释原话："与本地 5.3.517 是两个证据单元"）；而 §四 沙箱镜像前缀是 `app-sandbox:5.3.00`
（sandbox 镜像独立版本线）。两条版本线（业务镜像 5.3.496 / 沙箱镜像 5.3.00）**分开登记，不合并**。

---

## 五、与 CONFIG/CODE 二分的对齐（A3 口径）

- **CONFIG 型能力不进 sandbox**：结构化声明由平台/宿主执行（`deployment.py` deploy_plan 4 步为真例，
  A3 §三），走 readonly 写门 + 宿主授权，不经五阶段。
- **CODE 型能力必进 sandbox 五阶段**：`compile_unit/test_binding/sandbox_dep` 三要素（§二）驱动
  Sandbox→Compile→Test→Validate→Execute。
- 二者与 A4 证据纪律一致：本契约所有"现状"断言均引在盘实据（§三/§四 文件 + 行号），
  未建项标 UNVERIFIED，不臆造为已实现。

---

## 六、边界与铁律自证

- **不实现任何 sandbox 代码**：本文只描述契约/阶段/在盘事实映射；未改 `components/`（git 核实
  零改动），未建 `modules/sandbox/`、`sandbox/`。
- **不展开 02–12 模块**：sandbox 契约是 Global 级横向能力（A1 第三节），只以 01 UDC 的 test2
  事实作在盘示例；其余模块 sandbox 需求归后续批次。
- **不新增定位/阶段/验收**：五阶段定义引 ROADMAP-v2 §三；三要素引 A3 §2.2；写门替代门引 A4；
  test2 sandbox 配置引在盘 yaml；无自造口径。
- **凭据 0 入仓**：§四 只列键名 + 值（域/namespace/镜像前缀等对象标识），不含 token/密码；
  敏感项（datasource.password/redis-password 等）在源 yaml 已 `redacted`，本文不展开。
- **UNVERIFIED 清单**：v2 CODE sandbox 五阶段执行体（Sandbox 本体/Compile 链/Validate 判据）、
  `compile_unit/test_binding/sandbox_dep` 执行体、目标态 `modules/sandbox/`、`sandbox/` 目录——
  全部**未建**，标 UNVERIFIED，不写成已实现。

---

## 七、与 ROADMAP-v2 / 前件的对应

| 内容 | 来源（实测） |
|---|---|
| CODE 五阶段 + 禁直出 Java 直跑 | ROADMAP-v2 §三（§一~§七 实测范围内） |
| 目标态 `modules/sandbox/`、`sandbox/` | ROADMAP-v2 §二（实测：在盘未建） |
| CODE 型入口契约三要素 | `CAPABILITY-MODEL.md` §2.2（compile_unit/test_binding/sandbox_dep） |
| 写门 DENIED/POLICY_DENIED 替代门 | `components/platform_operations/layer.py:22-23`（A4 已核） |
| test2 应用级"构建即部署"活体链路 | `docs/audit/udc-design-time-deploy-write-contracts.md` §一 |
| test2 sandbox 宿主配置（键值） | `docs/audit/evidence/nacos-udc.yaml` seeyon.udc.sandbox / .deploy 段 |
| 业务镜像 vs 沙箱镜像版本线对照 | `config/environments.yaml`（5.3.496）/ nacos-udc.yaml（5.3.00） |
