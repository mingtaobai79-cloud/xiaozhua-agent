---
name: seeyon-v8-spi
description: "Seeyon V8 SPI/Super SPI 统一入口。入口只负责路由、证据规则、工程边界；子域知识下沉到 references/<domain>/ 独立目录，每个域按 SPI 类型拆分为独立文件夹。"
version: 8.0.0-LTS
author: operator-a
license: MIT
metadata:
  hermes:
    tags: [seeyon, v8, sso, spi, java, code-generation, generator, deployment]
    related_skills: []
---

# Seeyon V8 SPI / Super SPI 统一入口

> 本文件是入口/路由器。具体实现知识下沉到 `references/<domain>/` 子文档。

## 目录职责

> 总控制协议：`references/architecture-control-protocol.md`。

- `SKILL.md`：第 1 层 Routing / 主入口，只做需求识别、路由、证据优先级、生成边界。
- `references/index.md`：references 目录的顶层导航索引。
- `references/spi-domain-constraints.md`：**所有域的公共约束**（代码规范、Nacos、注册、部署、测试、质量门禁、运行模式、开发准备、工程结构）。生成代码前必须先读。
- `references/<domain>/`：第 2 层 Knowledge / 子域知识。每个域独立目录。
- `references/facts/`：事实库（语雀 rendered-md 231 篇）。
- `references/contract-index/`：第 3 层 Tools / Contract Index 工具包。
- `references/generation/tools/`：第 3 层 Tools / 生成后验证工具。
- `templates/`：第 4 层 Templates / 生成器与模板层。

## CFR 反编译工作流（Windows 实战）

**两种模式，按问题范围选：**

- **单类提取**（已知目标类）——先提 `.class` 再反编译。直接传 jar 给 CFR 且不给 `--outputdir` 会输出全部内容（13000+ 行）灌进上下文。
- **全 jar 导出**（要跨文件比对常量、枚举、注解白名单、grep 关键字时）——用 `--outputdir` 一次性写出全部 `.java`，再用 `grep` 在磁盘上检索。这才是跨文件类问题的正确做法，不要“逐类反编译”，也不用把结果读进上下文。

```bash
# 全 jar 导出（java 是原生程序，必须传 Windows 风格路径；MSYS 的 /d/... 它不认）
java -jar "<HERMES_HOME>/skills/seeyon/03-v8-extension/seeyon-v8-spi/references/contract-index/tools/cfr.jar" \
  "<MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar" \
  --outputdir ./common517
# 产物：./common517/com/seeyon/.../*.java，可自由 grep / 批量抽取常量
```

拿类型常量、能力开关、白名单这类**分散在多个类里的同一类信息**时，用脚本从导出目录批量提取（正则抽 `getDatabaseType()` / `getJavaType()` / `return false` 等），输出成一张对照表；用 `search_files` 定位候选文件。不要逐文件读，也不要靠记忆汇总。

单类提取（已知目标类，产物最小）：

```python
import subprocess, os, tempfile

cfr = r"<USER_HOME>/...yon-v8-spi\references\contract-index\tools\cfr.jar"
jar = r"<MAVEN_REPO>\com\seeyon\boot-starter-file\5.3.358\boot-starter-file-5.3.358.jar"
tmpdir = tempfile.mkdtemp()

# 1. 列出 jar 内容，找到目标 class
result = subprocess.run(['jar', 'tf', jar], capture_output=True, text=True, timeout=30)
entries = result.stdout.strip().split('\n')
target = [e for e in entries if 'StorageSpi' in e and e.endswith('.class')][0]

# 2. 提取 class 到临时目录
subprocess.run(['jar', 'xf', jar, target], cwd=tmpdir, capture_output=True, timeout=30)

# 3. 反编译提取的 class 文件
cls_path = os.path.join(tmpdir, target)
r = subprocess.run(['java', '-jar', cfr, cls_path], capture_output=True, text=True, timeout=60)
print(r.stdout)
```

## Jar 发现路径

1. **本地 CHIT 仓库**：`<MAVEN_REPO>\com\seeyon\{artifactId}\{version}\{artifactId}-{version}.jar`
2. **Artifactory**：`http://10.0.0.1/artifactory/libs-release/com/seeyon/{artifactId}/`
3. **项目 lib 目录**：`<PATH>

## Evidence 升级工作流

1. `jar tf` 列出所有 class，搜索目标接口/DTO
2. `jar xf` 提取到临时目录
3. CFR 反编译提取的 .class 文件
4. 更新 `references/{domain}/{spi}/README.md`：
   - 头部 Evidence 标记改为 `FACT ✅`
   - 接口定义段落标记 `[FACT ✅]`
   - 补充完整 FQCN、方法签名、DTO 字段
5. 更新 `references/{domain}/{spi}/constraints.md` 索取清单
6. 更新 `references/{domain}/index.md` Evidence 表格（含状态列）
7. 更新 `references/index.md` 主索引的域状态汇总
8. 若目标 artifact 本地缺失：不要就此收尾。把该 artifact 涉及的**调用链上下游**反编译出来，用上下游契约 + 运行态证据支撑结论，并在报告里逐个标 UNVERIFIED 的是哪一层。例：`udc-biz` 缺失时，`udc-common` 提供数据类型常量、`udc-facade` 提供 AppService 契约、`udc-starter-runtime` 提供运行态解析——足以定性机制，不足以证明保存逻辑。**用知识库源码快照补位时必须显式标注，不得冒充字节码证据。**

## Evidence 批量审计工作流

当需要全量审计所有域状态时：

1. 遍历所有域 `index.md`，统一 Evidence 表格格式（加状态列：✅ / 🧊 冻结）
2. 遍历所有 SPI `README.md`：
   - FACT 级：检查是否有 jar 引用、FQCN、FACT 标记
   - FROZEN 级：检查是否有 🧊 冻结 banner
3. 检查所有 `constraints.md` 是否存在
4. 扫描顶层文件（`spi-domain-constraints.md`、`architecture-control-protocol.md`）中的过期路径引用
5. 更新主 `references/index.md` 的域目录表（含 ✅/🧊 计数）

**常见过期引用**：`references/sso/` → `references/auth-sso/`、`auth-sso-legacy` → `auth-sso`、`spi-legacy/` → 已删除。

## 已知缺失 Artifact（🧊 冻结清单）

以下 artifact 在 libs-release 仓库和本地 CHIT 仓库中均不存在，遇到时直接标记 🧊 冻结：

| Artifact | 阻塞的 SPI | 域 |
|----------|-----------|-----|
| `boot-starter-encrypt` | digest, symmetric | crypto |
| `cip-provider-api` | provider-service | capability-channel |
| `ctp-user-loginpre` | login-pre-portal | auth-sso |
| `boot-starter-systemvariable` (高版本) | system-variable-spi | system-variable |
| `boot-starter-formula` (高版本) | system-variable-spi | system-variable |
| `edoc-facade` | edoc | workflow-document |
| `ctp-user-api` (更高版本) | auth-check | account-org-security |
| `boot-starter-file` (更高版本) | storage-interceptor | file-storage |

**冻结语义**：用户说"冻结"时，意思是停止该域的工作推进，不修改已冻结域的文件内容（除非用户明确要求）。冻结的 SPI README.md 头部必须加 🧊 banner。

### 域目录标准结构（用户明确要求）

每个域目录必须按以下结构组织，这是用户在多次纠正后确定的最终形态：

```
{domain}/
├── index.md                    ← 纯导航（SPI 文件夹路由表）
├── shared/                     ← 共享资源（契约、部署、健康检查、策略等）
│   ├── contract.md
│   ├── deployment-guide.md
│   └── ...
├── {spi-name-1}/               ← SPI 文件夹（每个 SPI 独立）
│   ├── README.md               ← 场景描述、接口定义、方法表格、代码骨架
│   └── constraints.md          ← 该 SPI 的独有约束
├── {spi-name-2}/
│   ├── README.md
│   └── constraints.md
└── ...
```

**关键规则：**
- `index.md` **只做路由**：SPI 文件夹路由表 + scope + 重启服务 + 索取清单。绝不塞实现细节、接口源码、代码骨架。
- `shared/` 放跨 SPI 共享的资源（契约文档、部署指南、健康检查规则、认证策略等）。
- 每个 SPI 有独立文件夹，包含该 SPI 的所有内容：约束、模板、代码骨架、提示词。
- 新建域时如果只有 index.md + constraints.md（无 FACT 数据），属于"框架占位"，等有反编译源码后再拆 SPI 文件夹。

### 三层约束层级

执行任何域的 SPI 开发/生成/改造时，按以下顺序读取：

1. **`references/spi-domain-constraints.md`** — 所有域通用
2. **`references/<domain>/<spi-name>/constraints.md`** — SPI 独有约束
3. **`references/<domain>/<spi-name>/README.md`** — 具体接口契约 + 代码骨架

### 质量标准：对标 auth-sso/ 和 mq/

`references/auth-sso/` 和 `references/mq/` 是已完成收敛的子域，文档质量是金标准。新建域的 SPI 文件夹必须对标其深度：
- 完整接口定义（FACT 级，含方法签名、泛型、异常、注解）
- 逐方法表格说明
- 完整代码骨架（JavaDoc + SLF4J 日志 + 错误处理 + DTO 构建）
- Nacos 配置模板（含 key/required/sensitive/example）
- spring.factories 注册示例

## 入口原则

1. **主 skill = 导航 / 路由器**：先读本文件判断任务属于哪个 SPI 子域，再按路径读取对应 reference。
2. **跨 Agent 可迁移**：Hermes、Claude Code、Codex 等 agent 只要读到本 `SKILL.md`，就能顺着路径继续执行。
3. **分层导航**：入口只放决策树、边界、共性铁律；具体 Contract / 版本 / 示例 / 代码细节放到 references 子目录。
4. **Super SPI 唯一工程形态**：统一 Maven 多模块，无 `lib/`，平台依赖走 Maven。
5. **公共能力上提**：HTTP、JSON、加解密、签名、Nacos 配置读取等共性能力放 `spi-common`。
6. **先定边界，再补资料**：先进入 `references/architecture-control-protocol.md`，确认四层架构、Contract Source、Evidence、stop point。
7. **产品化闭环优先于继续沉淀资料**：SPI 生成类任务必须进入 `references/workflows/spi-generation-workflow.md`，生成后运行 `references/generation/tools/validate_generated_spi_project.py`。

## UDC Boundary

UDC 低代码设计器和 UDC 生成的客户微服务不是 SPI 体系，也不调用 SPI。UDC 的设计态、前后端生成物、`web/core/ext/biz` 分层、运行态、数据库和 Redis 由独立的 `seeyon-udc-runtime` skill 负责。本 skill 只负责后端可插拔 SPI（组织架构、单点登录、基础组件等）的接口契约、实现、注册、版本差异和调用链。两套体系不得合并；只有用户明确要求同时研究时，才并列汇总，不建立“UDC 调 SPI”的调用链。


当 SPI 调用来自致远低代码应用时，必须同时核对 UDC 运行态，不把 SPI 契约和 UDC 业务代码混为一层：

```text
低代码应用 Controller / 微流程
    ↓
应用 AppService / 生成实体服务
    ↓
UDC 运行态（实体、元数据、页面、微流程、表映射）
    ↓
平台 SPI / 基础能力服务
```

UDC 相关 jar 的发现顺序：

1. 用户提供的 Artifactory `libs-release/com/seeyon/` 目录；
2. 组件库 `39.107.192.235:9082` 中的 artifact/version 索引；
3. 本地 CHIT Maven 仓库和工程 `target`；
4. 运行 Pod 镜像或挂载目录中的 jar。

反编译要求：先按 artifact/version 建立轻量索引，再针对 UDC 生成器、元数据、微流程、运行态服务和 SPI 调用链做 targeted decompile。不得把完整大 jar 反编译结果直接塞入 skill。

UDC 运行态证据至少包含：

- Controller 注解和完整 `/service/{applicationId}/...` 路由；
- AppService 接口、实现类和方法调用；
- DTO、实体元数据、物理表和主子表关系；
- UDC 运行态表结构、记录规模和关键索引；
- Redis key/缓存用途（只记录 key 模式和脱敏样例）；
- Nacos 配置键、版本和应用加载状态；
- SPI 接口 FQCN、调用点、参数/返回值和版本差异。

版本适配必须以 `artifact + version + sha256` 为最小证据单元。相邻版本只能标记 OBSERVATION/HYPOTHESIS，不能直接当作 FACT。


1. 永远先读 `seeyon-v8-spi/SKILL.md`。
2. 把本文件中的路径视为权威导航。
3. 遇到 SSO / 统一认证 / 免登 / 单点登录 → `references/auth-sso/index.md`。
4. 遇到 MQ / RocketMQ → `references/mq/index.md`。
5. 遇到系统变量扩展 → `references/system-variable/index.md`。
6. 遇到其他 SPI 域 → 按域路由到 `references/<domain>/index.md`（见路由决策树）。
7. 遇到语雀资料查询 → 搜索 `references/facts/yuque-v8-docs-rendered-md/`。
8. 遇到接口契约 / jar → 进入 `references/contract-index/`。
9. 新增 SPI 子域时，必须在本主入口登记。
10. 外部 Agent 适配：`references/agent-portability.md`。

## 最高优先级规则

### Rule-000: Contract First

如果用户提供 jar、源码、反编译接口、paste 的接口代码，优先从实际接口提取 Contract，禁止靠版本矩阵猜。

触发后加载：`references/contract-index/contract-discovery.md`、`references/contract-index/contract-bundle.md`、`references/contract-index/contract-normalization.md`。

### Rule-001: Evidence First / Contract Source

所有关键判断必须同时标明 Contract Source、Evidence、Locator。

Contract Source 优先级：
1. 用户提供的源码 / jar / 反编译结果
2. 外部 Swagger / OpenAPI exact match
3. MCP capability adapter
4. HTTP capability adapter
5. 本地语雀 rendered-md：`references/facts/yuque-v8-docs-rendered-md/`
6. 本地 jar 轻量索引：`references/facts/jar-contracts/`
7. 版本矩阵 / 历史经验
8. AI 推断

| 等级 | 标记 | 定义 |
|------|------|------|
| FACT | ✅ | 源码/jar/反编译结果/官方 OpenAPI exact match |
| OBSERVATION | ⚠️ | 语雀 rendered-md、历史样例、项目观察 |
| HYPOTHESIS | ❓ | 版本矩阵、经验推断、AI 推断，必须提示待验证 |

详细规则：`references/architecture-control-protocol.md`（含证据分级系统）、`references/contract-index/source-types.md`。

### Rule-002: Closed-world Code Generation

生成代码只能使用白名单依赖。禁止直接使用数据库、Redis、内部 service/dao/mapper、`@Autowired` 等。

详细规则：`references/auth-sso/shared/allowed-dependencies.md`。

### Rule-003: Super SPI Only

生成格式只有一种：Super SPI Maven 多模块工程。

详细结构见 `references/spi-domain-constraints.md`（附录 D：Super SPI 统一工程结构）。

核心形态：

```
custom-backend/
├── pom.xml
├── third-jar/          # 本地/私有三方 jar 暂存，不是 lib/
├── spi-common/         # 公共能力，不注册 SPI
├── spi-sso/            # SSO/统一认证/免登/单点登录
└── spi-{domain}/       # 后续其他 SPI 子域
```

禁止：`lib/`、`systemPath`、把 SSO 拆成多个 `spi-sso-*` module、在 `spi-common` 放 `spring.factories` / `spi_info.json`。

## 路由决策树

### 1. Auth-SSO / 认证 / 单点登录

先加载：`references/auth-sso/index.md`

| 用户说法 | SPI 文件夹 | 路径 |
|----------|-----------|------|
| 统一认证、登录页接统一认证中心 | unified-auth/ | `references/auth-sso/unified-auth/` |
| 三方免登 V8、外部系统登录后跳 V8 | avoid-login/ | `references/auth-sso/avoid-login/` |
| V8 菜单跳三方、V8 单点到 ERP | sso-connector/ | `references/auth-sso/sso-connector/` |
| 登录扩展、自定义认证方式 | auth-provider/ | `references/auth-sso/auth-provider/` |
| 三方→V8 免登（旧版本机制） | inbound-sso/ | `references/auth-sso/inbound-sso/` |
| V8→三方单点（旧版本机制） | outbound-sso/ | `references/auth-sso/outbound-sso/` |
| V8 接入三方 App（企微/钉钉/飞书） | mobile-app/ | `references/auth-sso/mobile-app/` |
| ticket 返回人员信息自定义 | ticket-custom-userinfo/ | `references/auth-sso/ticket-custom-userinfo/` |
| M5 扫码登录 PC | qrcode-login/ | `references/auth-sso/qrcode-login/` |
| 登录前门户（预置 jar + Nacos） | login-pre-portal/ | `references/auth-sso/login-pre-portal/` |

认证协议/加密策略：`references/auth-sso/shared/auth-strategies.md`

### 2. MQ / RocketMQ

先加载：`references/mq/index.md`

| 用户说法 | SPI 文件夹 | 路径 |
|----------|-----------|------|
| MQ 扩展、RocketMQ、阿里云 ONS | rocketmq-ons/ | `references/mq/rocketmq-ons/` |

共享契约：`references/mq/shared/contract.md`

### 3. 工程结构 / 多 SPI 融合 / Super SPI

公共约束已含工程结构：`references/spi-domain-constraints.md`

若用户明确要求生成工程、写代码、改已有 SPI 项目、打包或验证：
- Workflow：`references/workflows/spi-generation-workflow.md`
- Validator：`references/generation/tools/validate_generated_spi_project.py`

### 4. 系统变量扩展 / SystemVariableSPIService

先加载：`references/system-variable/index.md`

| 用户说法 | SPI 文件夹 | 路径 |
|----------|-----------|------|
| 系统变量扩展、计算条件弹框变量 | system-variable-spi/ | `references/system-variable/system-variable-spi/` |

### 5. 其他 SPI 域（8 个域，全部 GOLD ✅）

以下域各自独立目录，已全部升级为 GOLD 结构（index.md + shared/ + SPI 文件夹）。执行时先读公共约束 `references/spi-domain-constraints.md`，再读域 `index.md`。

| 域目录 | 覆盖场景 | SPI 文件夹数 | Evidence | 入口 |
|--------|----------|-------------|----------|------|
| `account-org-security/` | 通讯录脱敏、登录人数控制、密码强度/默认密码 | 3 | 混合（address-book FACT, password-policy FACT, auth-check OBS） | `references/account-org-security/index.md` |
| `capability-channel/` | 28 项基础能力通道（短信、邮件、OCR、支付、电子签等） | 1 | OBS ⚠️ | `references/capability-channel/index.md` |
| `crypto/` | 散列加密（DigestSpi）、对称加密（SymmetricSpi） | 2 | OBS ⚠️ | `references/crypto/index.md` |
| `datasource/` | 数据源扩展（DataBaseExecutorService） | 1 | FACT ✅ | `references/datasource/index.md` |
| `entry-menu-mobile/` | 三方菜单、移动插件 | 2 | FACT ✅ | `references/entry-menu-mobile/index.md` |
| `file-storage/` | 上传下载拦截（StorageInterceptorSpi）、文件操作（StorageSpi） | 2 | 混合（storage-spi FACT, storage-interceptor OBS） | `references/file-storage/index.md` |
| `infra-config-registry/` | 注册中心（RegisterServiceSPI）、配置中心（ConfigServiceSPI） | 2 | FACT ✅ | `references/infra-config-registry/index.md` |
| `workflow-document/` | 公文扩展（OpenAPI/service）、事项中心流程扩展（BPM SPI） | 2 | 混合（bpm FACT, edoc OBS） | `references/workflow-document/index.md` |

**Evidence 总览（2026-06 更新）**：22 FACT ✅ / 8 🧊 冻结 / 30 总计（73% 完成率）。冻结原因：缺少 jar 包（`boot-starter-encrypt`、`cip-provider-api`、`ctp-user-loginpre`、`boot-starter-systemvariable`、`edoc-facade` 等）。`integration-sync/` 已独立为 GOLD+FACT 域（3 个 SPI）。

### 6. 契约发现 / 外部索引 / jar 反编译 / Contract Index

进入 Contract Index 模块：

- 模块入口：`references/contract-index/overview.md`
- 契约发现：`references/contract-index/contract-discovery.md`
- 契约打包：`references/contract-index/contract-bundle.md`
- 契约归一化：`references/contract-index/contract-normalization.md`
- 外部契约索引：`references/contract-index/external-contract-index.md`
- Jar 索引方案：`references/contract-index/jar-contract-indexing-plan.md`
- 状态检查：`references/contract-index/tools/contract_index_status.py`

常用命令：
```bash
python references/contract-index/tools/decompile_jar.py index <PATH>
python references/contract-index/tools/decompile_jar.py query --symbol CtpUserSsoAuthProviderService
python references/contract-index/tools/decompile_jar.py status
```

### 7. 版本 / POM / 部署 / Health Check

按需加载：
- `references/auth-sso/shared/version-matrix.md`
- `references/auth-sso/shared/deployment-guide.md`
- `references/auth-sso/shared/health-check-rules.md`

## 默认执行流程

1. 识别用户场景。
2. 按 `references/architecture-control-protocol.md` 约束判断路由。
3. 加载对应域的 `index.md` → 定位 SPI 文件夹 → 读 `README.md` + `constraints.md`。
4. 涉及接口/DTO/jar → 统一进入 Contract Source 流程。
5. 有 jar/源码 → 先做 Contract Discovery。
6. 判断生成/修改的是新 Super SPI 工程还是已有工程增量。
7. 公共能力放 `spi-common`；SSO 代码放 `spi-sso`；MQ 代码放 `spi-mq`。
8. 生成前先读 `references/spi-domain-constraints.md`。
9. 生成后运行 `python references/generation/tools/validate_generated_spi_project.py <project-root>`。
10. 按 `references/workflows/spi-generation-workflow.md` 的交付报告格式输出。

## 知识库卫生（Knowledge Base Hygiene）

用户明确纠正过：references/ 顶层文件太多会导致上下文爆炸，skill 变得杂乱不可用。以下规则必须遵守：

1. **顶层 md 文件数控制在 6 个以内**：index.md、spi-domain-constraints.md、architecture-control-protocol.md、v8-openapi.md、yuque-local-index.md、agent-portability.md。新增知识必须下沉到域目录或合并到已有文件。
2. **能合并就合并**：相关的小文件合并成大文件的附录，不要散放。
3. **spi-legacy/ 已完全删除**：所有子域已迁移到 references/ 顶层独立目录。不要再创建 spi-legacy/ 或任何嵌套 legacy 结构。
4. **sso/ 和 auth-sso-legacy/ 已合并为 auth-sso/**：不要再引用旧路径。
5. **mq-legacy/ 已合并到 mq/**：不要再引用旧路径。
6. **域目录结构固定**：`index.md`（纯导航）+ `shared/`（共享资源）+ `{spi-name}/`（SPI 文件夹含 README.md + constraints.md）。index.md 绝不塞实现细节。
7. **定期审计**：每次大改后跑一次 `references/` 目录审计，确认顶层文件数、目录数、总大小在合理范围。

## 域升级检查清单（占位 → 金标准）

将域从"框架占位"升级到"金标准"时，按此清单逐项执行：

### Phase 0: Evidence Alignment Audit（先做这个！）

**在等 jar 之前，先检查已有数据是否被浪费。**

很多域的 shared/ 目录已经有 FACT 级契约（来自 jar 反编译），但 SPI 级 README.md 仍然标 OBSERVATION 且没有引用 shared/ 文件。这是文档对齐问题，不是数据缺口。

审计步骤：
1. 扫描域内所有 SPI 的 README.md，找 `OBSERVATION` 标记
2. 检查 `shared/` 目录是否有 `*-contract.md` 或 `contract.md` 文件
3. 交叉比对：SPI README 中的接口 FQCN 是否已在 shared 契约中出现
4. 如果匹配：直接升级标记为 FACT ✅，添加指向 shared 文件的引用头
5. 检查工程目录（如 auth-sso-spi-parent/）中 spring.factories 的实际 key，确认 FQCN

这个审计可以在零新 jar 的情况下把多个 SPI 从 OBSERVATION 升到 FACT。2026-06 实战：unified-auth、sso-connector、rocketmq-ons 三个域通过此方法一次性升级，契约数据早就在 shared/ 里了。

### Phase 1: 结构重组
1. 创建标准目录结构：`index.md`（纯导航）+ `shared/` + `{spi-name}/`（每个 SPI 独立文件夹）
2. `index.md` 只做路由表：SPI 文件夹索引 + scope + 重启服务 + 索取清单。**绝不塞实现细节**。
3. 删除旧的平铺 md 文件，内容合并到 `shared/README.md` 或各 SPI 的 `README.md`。

### Phase 2: SPI 文件夹内容（每个 SPI 的 README.md 必须包含）
- [ ] 场景描述 + 适用版本
- [ ] Maven 依赖
- [ ] 接口定义 [FACT ✅ 或 OBSERVATION ⚠️]
- [ ] 方法说明表格
- [ ] DTO 定义 [FACT ✅ 或 OBSERVATION ⚠️]
- [ ] 代码骨架（含 JavaDoc + SLF4J 日志 + 错误处理）
- [ ] Nacos 配置模板
- [ ] spring.factories 注册示例
- [ ] **spi_info.json**（scope = 该 SPI 对应的微服务应用名）
- [ ] 重启服务

### Phase 3: constraints.md（每个 SPI 独有约束）
- [ ] 域特有规则
- [ ] 禁止项
- [ ] 索取清单（P0/P1 分级，已有项标 ✅）

### Phase 4: 验证
- [ ] 金标准段落检查：代码骨架、Nacos、spring.factories、spi_info.json、Maven 全部命中
- [ ] 更新 SKILL.md 路由表
- [ ] 更新 SKILL.md References 区域

### spi_info.json scope 规则
scope 值 = 该 SPI 部署到的微服务应用名，不是域名也不是模块名：

| SPI 域 | scope 值 | 说明 |
|--------|----------|------|
| auth-sso 模式 A/B | `ctp-user` | 认证服务 |
| auth-sso 模式 C | `cip-connector` | 连接器服务 |
| MQ | `ALL` | 全系统生效 |
| todo-batch | `ctp-affair` | 待办服务 |
| api-auth | `cip-connector` | 连接器服务 |
| org-sync-middle-table | `cip-connector` | 连接器服务 |
| system-variable | `ALL`（兜底） | UDC 应用，具体 scope 待确认 |

**规律**：同一个微服务下的多个 SPI 共享同一个 scope 值。新增 SPI 时先确认它部署到哪个微服务，再填 scope。

## 关键坑

0. 认证/SSO/免登/三方 App SPI 模板有专门质量门禁（已合并到 `references/spi-domain-constraints.md` 附录 A）。用户明确纠正过：只生成类、少注释、不用接口参数/注解/日志、没有 Nacos 参数、把结构验证当真实测试，都是"玩具"。
1. `spi-common` 不是 SPI，不注册 `spring.factories`，不放 `spi_info.json`。
2. `spi-sso` 是 SSO 唯一 module，统一认证/免登/单点登录只在内部按 package 分流。
3. 统一认证固定进 `spi-sso/unifiedauth`。
4. 三方免登固定进 `spi-sso/avoidlogin`。
5. V8 到三方单点固定进 `spi-sso/connector`。
6. 本地三方 jar 只能放 root `third-jar/` 暂存，优先 install/deploy 后 Maven dependency 引用。
7. 用户说"SM3 解密"时必须纠正：SM3 是摘要，不可解密；需确认是 SM2 还是 SM4。
8. 解密后的人员编号/工号如果就是 V8 loginName/code，可直接返回对应字段，不一定要 OpenAPI 二次查询。
9. 生成 SSO/SPI Java 代码时禁止默认套 Hutool `StrUtil`。除非 POM/Contract 明确证明可用。
10. Contract First ≠ Jar First。先走 Contract Index 状态检查。
11. 子域 reference 不是事实终点。找不到时搜索 `references/facts/yuque-v8-docs-rendered-md/docs/`。
12. MQ 是 SSO 后的第二子域。
13. Contract Index 保持一个内聚模块。
14. 外部 Agent 适配层统一沉淀到 `references/agent-portability.md`。
15. 生成示例工程后必须做静态结构验证。
16. 维护本 skill 结构时保持"子域 reference + facts 事实库 + 模块 tools/tests"三分法。
17. 查询语雀 rendered-md 时，跳过 bootstrap 巨长行。
18. 系统变量扩展文档只给短名和示例，full qualified name 必须经 jar/source 确认。
21. **system-variable SPI 接口不在预期 jar 中**：`boot-starter-systemvariable-5.3.313.jar`（仅 4 个类：EnvFunction、SystemVariableKeyEnum、SystemVariableService、SystemVariableUtils）和 `boot-starter-formula-5.3.313.jar`（有 ExpressionService 但无 SPI 接口）都不包含 `SystemVariableSPIService`、`@SPISystemVariable`、`SPISystemVariableType`。这三个 SPI 接口在一个尚未确认的 jar 中（可能是 `boot-starter-spi-api` 或类似 artifact）。
22. **已确认的 FQCN**（来自 jar 反编译 FACT）：`Apps` = `com.seeyon.boot.context.Apps`；`ExpressionService` = `com.seeyon.boot.starter.formula.domain.service.ExpressionService`。
23. **"冻结"语义**：用户说"去掉/除去/冻结"某个域时，意思是停止该域的工作推进，不是替换引用。不要主动修改已冻结域的文件内容。
19. 新增/重抓语雀 rendered-md 时，先查 manifest 避免重复。
20. **域合并规则**：auth-sso 域包含 Super SPI（unified-auth、avoid-login、sso-connector）和旧版本 SPI（auth-provider、inbound-sso、outbound-sso、mobile-app、ticket-custom-userinfo、qrcode-login、login-pre-portal），统一在 `references/auth-sso/` 下，不再分 legacy。MQ 同理，`references/mq/` 包含所有 MQ 内容。
21. **Frozen Skeleton 模式**：当 jar 不可用但用户要求"先做一个版本"时，不要阻塞。生成 frozen skeleton：(a) implements 接口注释掉，(b) @注解注释掉，(c) 平台 API 调用注释掉并加 `// placeholder` 返回值，(d) 文件头加 EVIDENCE STATUS 块列出所有待确认 FQCN，(e) spring.factories 用 PLACEHOLDER key。代码可编译（注释掉的代码不影响编译），拿到 jar 后 5 分钟内可激活。这是用户明确偏好的降级方式，不要反复确认。
22. **工程模块命名惯例**：auth-sso-spi-parent 项目中模块按 `spi-NN-{name}` 编号（spi-01 到 spi-16），新增模块取下一个编号。不要创建独立的 custom-backend/ 工程，除非用户明确要求。

## References

### 核心文档
- `references/index.md` — references 目录顶层导航
- `references/spi-domain-constraints.md` — 所有域公共约束（含质量门禁、运行模式、开发准备、工程结构、官方部署规范）
- `references/architecture-control-protocol.md` — Skill 架构治理（含证据分级系统、知识结构规则、健康检查）
- `references/v8-openapi.md` — V8 OpenAPI 平台契约 + 文档索引
- `references/yuque-local-index.md` — 语雀本地索引说明
- `references/agent-portability.md` — 外部 Agent 适配

### 工具与验证
- `references/workflows/spi-generation-workflow.md` — M1 生成闭环
- `references/generation/tools/validate_generated_spi_project.py` — 静态验证脚本
- `references/contract-index/` — Contract Index 模块（9 个文档 + 工具包）

### Auth-SSO 域（金标准，10 个 SPI 文件夹 + shared/）
- `references/auth-sso/index.md` — Auth-SSO 总导航
- `references/auth-sso/shared/` — 共享资源（auth-strategies、allowed-dependencies、version-matrix、deployment-guide、health-check-rules、ctp-user-api-contract、cip-connector-api-contract、validation-results）
- `references/auth-sso/unified-auth/` — 统一认证（Super SPI）
- `references/auth-sso/avoid-login/` — 免登（Super SPI）
- `references/auth-sso/sso-connector/` — SSO 连接器（Super SPI）
- `references/auth-sso/auth-provider/` — 认证提供者（Legacy）
- `references/auth-sso/inbound-sso/` — 入站 SSO（Legacy）
- `references/auth-sso/outbound-sso/` — 出站 SSO（Legacy）
- `references/auth-sso/mobile-app/` — 移动应用（Legacy）
- `references/auth-sso/ticket-custom-userinfo/` — 票据自定义（Legacy）
- `references/auth-sso/qrcode-login/` — 二维码登录（Legacy）
- `references/auth-sso/login-pre-portal/` — 登录前门户（Legacy）

### MQ 域（金标准，1 个 SPI 文件夹 + shared/）
- `references/mq/index.md` — MQ 总导航
- `references/mq/shared/` — 共享资源（contract、deployment-guide、health-check-rules、closeout、generated-project-validation）
- `references/mq/rocketmq-ons/` — 阿里云 RocketMQ / ONS

### 系统变量扩展域
- `references/system-variable/index.md` — 系统变量扩展总导航
- `references/system-variable/shared/README.md` — 注解属性、方法限制、部署指南、原文示例
- `references/system-variable/system-variable-spi/README.md` — 接口定义、代码骨架、spring.factories、spi_info.json
- `references/system-variable/system-variable-spi/constraints.md` — 独有约束、索取清单

### Integration-Sync 域（GOLD+FACT，3 个 SPI 文件夹 + shared/）
- `references/integration-sync/index.md` — 三方集成同步总导航
- `references/integration-sync/todo-batch/` — 批处理三方待办
- `references/integration-sync/api-auth/` — 集成接口鉴权
- `references/integration-sync/org-sync-middle-table/` — 组织同步中间表

### 其他 SPI 域（全部 GOLD ✅，Evidence 待 jar 升级 FACT）
- `references/account-org-security/` — 账号/组织/安全（3 SPI: address-book, auth-check, password-policy）
- `references/capability-channel/` — 能力通道扩展（1 SPI: provider-service, 28 项能力）
- `references/crypto/` — 加解密（2 SPI: digest, symmetric）
- `references/datasource/` — 数据源扩展（1 SPI: database-executor）
- `references/entry-menu-mobile/` — 入口/菜单/移动（2 SPI: third-menu, mobile-plugin）
- `references/file-storage/` — 文件/存储（2 SPI: storage-interceptor, storage-spi）
- `references/infra-config-registry/` — 配置/注册中心（2 SPI: register, config）
- `references/workflow-document/` — 流程/公文（2 SPI: edoc, bpm）

### 事实库
- `references/facts/yuque-v8-docs-rendered-md/` — 语雀 rendered-md（231 篇）
- `references/facts/yuque-v8-docs-rendered-md/tools/` — 导出工具
- `references/openapi-docs/` — OpenAPI Word 文档（18 份）
