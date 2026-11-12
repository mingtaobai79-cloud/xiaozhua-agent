# UDC 平台全面补全 —— 方法提示词（Method Prompt）

> ✅ **P6 裁决（2026-11-07）：保留原地，不移动、不删除。**
> 本文件是 udc-semantics 线（cron 已于 2026-10-16 停）的**任务级方法提示词**，
> 其中「完成判据」「每 10 分钟自唤醒」等属历史任务上下文，**不是当前有效指令**。
> 保留理由：① 方法论六步仍被 `skills/05-agent/xiaozhua-constraint-extraction/SKILL.md` 当作范式引用；
> ② `DEPLOYED-STATE-VERDICT.md` 拿本文件 §环境 的运行时版本做交叉校验（3/3 一致）；
> ③ 完成判据 checklist 是「什么算做完」的唯一成文标准。
> 已登记于 `docs/audit/README.md` 第六节。§环境 已按仓库脱敏规则改写，方法内容一字未动。

> 本文件是**任务级方法提示词**。任何接手此任务的 agent（含每 10 分钟自唤醒的 cron run）
> 必须先读本文件 + `PROGRESS.md`，再按此方法论推进，完成后更新 `PROGRESS.md`。

## 目标（终态）

把 xiaozhua-agent 从"能读会分析"推进到**"能把任何 UDC/BPM/ORG/USER 需求自己完整写出且不出错"**。
判据：**仅凭沉淀的权威约束，从零手写一个完整需求对象 → 本地校验 PASS → 在线创建 → 回读一致**。

## ★ 核心方法论（用户明确要求，逐条执行）

**方向**：`前端功能 → REST/JSON 请求 → biz 业务 service → 交互表（元数据可能在 Redis/存储）`

1. **以前端代码为主**：先逆向设计器前端 bundle/TS chunk，找到**渲染该页面的代码位置**，
   追**按钮的 onClick → 调用链 → 就是 json/rest 接口（op 名 + body 形状）**。
   - 前端解包：`<HERMES_HOME>/cache/scratch/udc-frontend/unpacked/`（chunk 名 ≈ 原源码路径）
   - 前端 runtime 真值：`components/udc/frontend_runtime_ops.py`（语义函数 → op）
2. **追后端 biz 业务逻辑**（Controller 只是入参壳）：
   - `udc-web` = `com.seeyon.udc.controller.*`（54 Controller / 299 REST，入参/路由）
   - `udc-biz` = `com.seeyon.udc.*`（**业务逻辑在此**：api/AppService、microflow、entity、page、metadata、autocode…）
   - 反编译用 CFR：`<HERMES_HOME>/skills/seeyon/03-v8-extension/xiaozhua-v8-spi/references/contract-index/tools/cfr.jar`
3. **追交互表 / 存储**（元数据可能在 Redis 或 OSS/DB，按配置找）：
   - DB：schema `udc_test2`（表 `udc_microflow_info.data_schema` 等）、`information_schema` 找表
   - Redis：按配置（`xiaozhua-low-code-environment` skill 的 env）扫 key；设计态权威源 = MySQL `udc_entity`/`udc_attribute`，
     运行态读 = Redis(180h)→OSS 发布镜像
   - 配置：`config/` 下的 environments.yaml（jar 路径/版本/网关/凭据一律引用配置键，不写死）
4. **遇 BPM/USER/ORG 应用功能**：**和 UDC 一样的方法**追它们的前端代码 + web（Controller/DTO/Service）+ 交互表。
   - 运行时版本（test2）：`bpm-facade-5.3.374` / `organization-facade-5.3.368` / `ctp-user-facade-5.3.429` / `cip-*`
   - jar 事实源：本地 maven 仓库（路径见 `config/environments.yaml`；123+ 构件，按 artifact/version 取）
5. **证据优先顺序**：真实前端 bundle/注册表/schema、Controller/DTO/DAO 字节码（javap/CFR）、
   jar 内资源 > 文档推测。**臆造 0 / 漏登记 0** 双向对账。LIVE（真实运行）证据优先于静态推断。
6. **沉淀形式**：约束/值域落成 `components/udc/*_constraints.py` 的常量 + `validate_*()` + 测试；
   知识落成 `docs/audit/udc-semantics/*.md`。**只写有证据的项，无证据的推断必须删。**

## 环境（test2）

> **脱敏说明（2026-11-07）**：本节原写有具体客户应用 ID、显示名、目标实体 ID、K8s 命名空间与凭据文件路径。
> 这些属任务期环境上下文，已按仓库脱敏规则改为「配置键 / 占位符」，真实值只在运行环境与
> `xiaozhua-customer-evidence/`（不入库）里取。方法内容未改。

- 工作目录：`<XIAOZHUA_AGENT_ROOT>`（纯本地 git，勿 push）
- 目标应用与实体：**从 `config/environments.yaml` 的 env 键取**，不在此写死具体 ID
- 环境操作：`xiaozhua-low-code-environment` skill（`python scripts/conn.py selftest --env=test2`；SSH/K8s/Redis/MySQL/Nacos）
- 凭据：由仓库外的共享凭据目录提供（路径见环境 skill）；**本文件不记录任何凭据路径或值**
- 集群/命名空间：由 env 配置决定，不在此写死

## 硬约束

- 不得写客户业务明细进仓库（客户明细只进 `xiaozhua-customer-evidence/`，不回流）——**用 `git add <具体文件>`，勿用 `git add -A`**
- 语法基线：`uv run --no-project python -m compileall -q components tools tests` 须无错
- 测试基线：`uv run --no-project python -m pytest tests/ -q` 须全绿；改测试后同步
  README/`docs/audit/agent-version-audit.md`/`docs/audit/code-reality-audit.md` 里的 `N passed`
  （须等于 `pytest --collect-only` 的 collected 数）
- 对外/破坏性操作先确认；`trash` > `rm`

## 完成判据（全部满足才可暂停本任务）

- [x] 微流程域：全活动节点字段约束 + 从零手写 PASS ✅
- [x] 实体/属性域：DTO 必填 + LIVE 从零创建→回读一致 ✅
- [x] 页面/布局域：biz 强制链全捕获 + LIVE 从零创建成功 ✅
- [x] 菜单/导航域：FunctionNodeDto/PageRouteDto 完整字段 + LIVE 从零创建→回读 ✅
- [ ] 平台操作面：299 REST + 240 GraphQL 全量映射
      （op 命名规则字节码实证 ✅；暴露机制本体字节码实证 ✅ — MetadataScanner 双分支，见
      REST-EXPOSURE-MECHANISM.md；前端 346 op 中 **231** 精确归位 udc-web；
      余 **92** udc* 经机制判定属**非 udc-web 构件**；**跨构件归位 32/92**
      （32/32 独立字节码验证，见 COMPONENT-RELOCATION.md 第 1、3 节；口径更正 raw 230/93 -> corrected 231/92）；
      **udc-web 持久化契约缺陷 A/B/C/D 已修**：657 -> **674** 端点，op 面 **666**
      （`ParameterController.create` 无 full_path，故 distinct op = **673**；三口径不可混用）；
      余 **60** 条仍 UNVERIFIED（**名单已落盘** `frontend-udc-unlocated.json`；
      **loader 契约 32/60** 落 `frontend-op-loader-contract.json`）—
      **Artifactory 侧已穷尽**（第五轮：619 Controller / 201 构件 / 437 jar / 12 版 udc-web，
      0 归位，见 `COMPONENT-COVERAGE-EXHAUSTION.md`；8 族 28 条本地零 Controller）⇒
**静态路径已走通（第十八轮）**：`pods/exec` 实为 **ALLOWED**（历轮记的 forbidden 已不复存在；**第二十一轮 LIVE 复检已回到 DENIED，见文末更正**），
据此完整取出部署态 `BOOT-INF/lib`（**544 jar / 22 个 udc 构件 / 11 个本地缺失**，
见 `DEPLOYED-LIB-INVENTORY.json`；导出 `udc-web-5.3.517.jar` sha256 `0d6b0a6528` 与版本注记逐字一致）；
并在部署态 `udc-*.jar` 域内做终裁：**同域对照 674/674 PASS**，余 **60** 条 **0 命中**
（`DEPLOYED-OP-SURFACE.json` + `tools/core/decompile/enumerate_deployed_op_surface.py`）
⇒ 60 条由「Artifactory 侧静态穷尽不承接」升级为「**部署态构件域内亦不承接**」（LIVE-DEPLOYED）。
**第二十一轮 LIVE 更正**：对 K8s 发 `SelfSubjectAccessReview` 实测 `pods/exec` **三个 verb 全 False**（get/create/list 均 `allowed=False`），`pods/portforward`/`pods/attach` 亦全 False，仅 `pods/log get` = True ⇒ 第十八轮记的「`pods/exec` 实为 ALLOWED」**在本轮已不成立**（该轮取件窗口与当前 RBAC 不同）。已取的 `DEPLOYED-LIB-INVENTORY.json`（544 jar）**仍作有效证据**（导出件 sha256 可校验），但该通道**不得再被当作可用手段**写入后续计划。
**但域边界未闭合**：本裁定只覆盖 22 个 `udc-*.jar`，部署域其余 **522 jar**（`boot-starter-*` 等）**未纳入**
⇒ 「60 条不存在」仍**不可断言**，须下一轮把域扩到全 544 jar 复跑（且同域对照须仍 PASS）。
**口径自我纠正（第十八轮）**：上轮以「已归位 32 条 32/32 命中」当阳性对照，实测仅 **5/32** ——
32 条中 22 条属 `boot-starter-sandbox`（不在该域），属**跨域对照假阴性**；
同域对照才是有效对照（已写进护栏 `tests/udc/test_deployed_op_surface.py`）。
      **新增 LIVE 通道（第八轮）**：`pods/log` 可用 ⇒ udc pod 的 `AppContextFilter`
      打印真实请求 URL，首次得到**真实运行期**面（425 条 / 13 distinct，对账契约 11/13，
      见 `ROUTE-LITERAL-SIMILARITY.json`；并钉死路由字面段形近陷阱）
      **第九轮（LIVE 扩面 + 两发现）**：日志通道扩到**全 ns 32 pod**（1407 条 URL 行 / **421 distinct**；
      控制面 `/udc/**` 271 + 应用运行期 `/{appId}/**` 150；模板级对账 **14 EXACT_T / 4 MISS_T**）；
      对 60 条余量族在真实 URL 面命中 **0**（负证据加强）；换出**发现 A**：`/udc` 前缀下存在 udc-web 之外的
      REST 提供者（单窗计数 `/udc/metadata/` = 20 vs `/udc/design-metadata/` = 0，提供者 = ctp `MetadataController`）
      ⇒ **674 契约是单构件（udc-web）视图**，平台操作面的完整口径须按**全构件并集**理解；
      **发现 B**：两条「被调用但契约没有」的路由（见下）。
      **第十轮（部署态裁定，收口候选 iv）**：① 只读 K8s API 取 **19 个平台构件部署 tag**，
      **`udc` = 5.3.517**（= 被审计 artifact 同版本），且全 ns **唯一**打印 `request url:/udc/**` 的平台 pod
      就是这个 5.3.517 容器（360 条）⇒ 假设「部署版本 != 5.3.517」**证伪**；
      文档声明的 `bpm-facade-5.3.374` / `organization-facade-5.3.368` / `ctp-user-facade-5.3.429`
      与 LIVE tag **3/3 一致**；② 部署态字节码（`udc-assemble-5.3.517-deployed/MicroFlowReadPlane.javap.txt`）裁定：
      `MicroFlowGroupController` 类级 `udc/micro-flow-group`；`selectByAppId` 的 `@PostMapping` 值 = `select-by-type`、
      方法体调 `MicroFlowGroupAppService.selectByType`；常量池**无 `select-by-appid`、无 `search-list`**
      ⇒ `/udc/micro-flow-group/select-by-appid/{id}` 必然 404（**方法存在、映射字面不存在**，
      第九轮「无实现」措辞已更正）；`search-list` 余下解释 =「其它构件提供」/「死路径」，**二选一仍 UNVERIFIED**。
      证据件 `DEPLOYED-COMPONENT-TAGS.json` + 文档 `DEPLOYED-STATE-VERDICT.md`。
      **第十四轮（候选 vii）**：19 构件 LIVE tag 已入版本审计 —— `agent-version-audit.md` **§2.1** 全表
      （+§2/§3 各一行、§4 边界），复验 **19/19 相同 / 差异 0**，护栏
      `tests/udc/test_deployed_tags_version_audit_alignment.py`（8 项，含内存突变自证）。
      余量侧：设计器 bundle 的 micro-flow-group 族 op **全集 = 6、无 `search-list`**
      （他族确有 `*SearchList*` 字面量作反证）⇒ 该条路由的「设计器前端来源」支**排除**，仍三选一。
      **第二十二轮（判据补课）**：marker 判据**只覆盖 Spring MVC**（JAX-RS `@Path` / 原生 Servlet
      `@WebServlet|@WebFilter|extends HttpServlet` 无需 `bind/annotation` 即可暴露端点）⇒ 闭包论证
      有真窟窿，已补**第二条必要条件**并逐件实测：`tools/core/decompile/enumerate_deployed_exposure_census.py`
      + `DEPLOYED-EXPOSURE-CENSUS.json` + `tests/udc/test_deployed_exposure_census.py`（13 项）。
      实测 **0-marker 428 件中真实可暴露者仅 2 件、全为第三方容器/库**（`tomcat-embed-core-9.0.104` /
      `jersey-common-2.35`），**平台家族 0 命中、平台构件带非 Spring 路由注解 = `[]`** ⇒ 双轴 PASS。
      **须同时记住**：**0-marker 里有 48 件平台构件**（含 `udc-biz` 2312 class）⇒
      「0-marker 不可能是暴露者」**不是** marker 判据独立给出的，而是由第二条必要条件兑现的。
      陷阱已钉死：`javax/servlet/http/HttpServlet` 是 `HttpServletRequest` 的**前缀子串**，
      以子串判继承会得 23 件假阳（精确解析 `super_class` 槽位后 = 2 件）。
      + test2 网关路由表
      （`udc_test2.udc_microflow_info.rest_path/rest_api` 已 **LIVE 证伪**：非 REST 注册表））
- [~] BPM/ORG/USER 域：facade API 契约（115 AppService/673 方法）✅；biz 类在加密 assemble.jar 内 ⛔（本地不可反编译，边界已记为诚实结论）
- [x] 存储层：Redis key 模式 + 99 交互表 + 配置源(Nacos) LIVE 实证 ✅
- [ ] PROGRESS.md 中所有 pending 项清零（余：**60** 未归位 op 定域；提取器缺陷 A/B/C/D 已修 ✅）
