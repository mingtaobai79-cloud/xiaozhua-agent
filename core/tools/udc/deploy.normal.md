# Tool 声明｜udc.deploy.normal（deploy_plan step4）

> B2 样板件（`core/tools/`）· deploy_plan 4 步映射 之 4/4（构建=收尾步）。
> 口径同 B1/step1；只描述执行契约，不实现代码；凭据 0 入仓；引 ROADMAP 限 §一~§七。

## 契约字段
| 字段 | 值 | 在盘依据 |
|---|---|---|
| op | `udc.deploy.normal` | `deployment.py:176`（step4，L175-181） |
| method | `POST` | 同上 |
| path | `/service/udc/runtime/deploy-normal` | **LIVE 矫正(09-27)**：类级 `@RequestMapping("udc/runtime")` + 方法级 `@PostMapping("deploy-normal")`，宿主前缀 `/service/`；见 `core/facts/deploy/build-chain.md` §1。此前记的裸 `udc/deploy` / `udc` 均 404 |
| body schema | `{"deployDto":{appId, deployType:"TEST", projectType:"ALL", terminalType:"ALL"}}`（deployType 可 TEST/RELEASE/ON_ONLINE/DELTA；LIVE 用 TEST） | `deployment.py` L176-179 原值 + **LIVE 09-27**：形参注 `@MultiRequestBody`（非 `@RequestBody`），**必须按形参名 `deployDto` 包裹**；平铺 body → DTO=null → `EL1007E` |
| verify 回读 | RDS `udc_test2.udc_deploy_record` 最新行（deploy_type=2, state=1）+ 应用库 `SHOW TABLES`（物理表落 `{app}_test2`） | `deployment.py` step4 `verify`（A6 §三 构建=部署） |

## registry 状态 + 证据等级（A4 口径，引 registry.py 实值）
- **registry status = `OBSERVED`**（`registry.py` 实值，本轮脚本实测；R18 设计态部署契约族，test2 活体登记）。
- **A4 归并等级 = LIVE**（OBSERVED→LIVE，A4 §二）。
- **写门事实**：`write=True` → `layer.py:22` → `DENIED` + `POLICY_DENIED`；agent 出方案 data、宿主执行（A1 §六）。
- **关联 R18 契约**：`udc.deploy.search_status`（GET 读部署记录）registry status=`UNVERIFIED`
  （类级前缀 LIVE 404，完整路由 UNVERIFIED，禁拼前缀执行）——仅登记、非本 4 步之一。

## LIVE 实证（非臆造）
- RELEASE 构建 `deploy_type=2 state=1 内部流水线构建成功`（`udc_deploy_record` 2026-09-24 15:52 行）
  + 物理表 `yanshouda_m5654091886000795633` 落 `9000000000000000001_test2` = **OBSERVED_LIVE**
  （`docs/audit/udc-design-time-deploy-write-contracts.md` §一 L17-18 逐字）。
- **TEST 全链路 LIVE（09-27，`core/facts/deploy/build-chain.md`）**：`POST /service/udc/runtime/deploy-normal`
  + `{"deployDto":{appId:<测试副本>,deployType:"TEST",projectType:"ALL",terminalType:"ALL"}}`
  → `200 {"status":0,"code":"BOOT_0000","deployId":"1006978865758003184"}`；
  流水线 `CdpDeployTask(2253ms)` → `CdpDataDetectionTask(107796ms)` → **一致性检测未过**
  → `AbstractDeployService.doParallel(AbstractDeployService.java:242)` 抛 `Business Error[一致性检测未通过]`；
  回读 `udc_deploy_record` id=2343914262409841112 `deploy_type=0 state=2 build_version=20260927190507`。
  = **链路 LIVE PASS / 构建业务结果 FAIL（数据侧）**。

## 前置门（LIVE）
- **一致性检测**是构建的硬门：未过即整单失败，无部分成功。失败根因分类（页面数据源缺失 146 / 参照悬空 30+ / 关联枚举元数据空 / 页面表达式一致性）见 build-chain §7。
- 检测明细**不落 MySQL**，只在 Redis：`test2:udc:5.3.517:DetectionError:Data::<appId>:<ENTITY|PAGE|MICRO>:<类全名>`；
  读取面前端走 `POST /service/udc/graphql`（仅预生成接口，无 introspection）。

## 未直读项（UNVERIFIED，不臆造）
- 生成 Java 工程是否落 OSS/仓库（`schema_storage_key`/`sql_storage_key` 指向存储对象）→ **UNVERIFIED**（audit §六）。
- 前端页面/列表是否随 RELEASE 构建生成 → **UNVERIFIED**（audit §六：需活体回读页面面，本轮未探）。
  （注：页创建本身由 step3 显式完成，不随构建；构建"是否再送页"为上述未探项。）
- 检测明细 Redis key **全名**、`udc.application.search.front-detection` 形参名、GraphQL 预生成接口清单 → **UNVERIFIED**。

> 4 步收尾 tool；与 B1/step1-3 同锚同一写门事实（layer.py:22），本件不重复 B1 事实体，只补 deploy tool 声明。
