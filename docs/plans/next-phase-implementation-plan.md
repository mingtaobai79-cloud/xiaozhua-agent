# 2小爪 Agent 下一阶段实施方案

目标：把当前离线只读骨架推进为证据驱动的 2小爪 Agent 审计与诊断平台，再以最小、可回读、可撤销的闭环验证执行能力。

## 目标架构

用户任务 -> Core任务拆解/策略 -> UDC/Runtime/Integration/SPI组件 -> Provider取证 -> Evidence Ledger -> 诊断/影响分析 -> dry-run计划 -> 确认 -> 受控执行 -> 回读验证。

## 当前结论

UDC静态事实已基本足够，不再做无边界class扫描。仍需定向增强动态事实：

- D1：设计器真实POST/GraphQL请求、DTO、Controller、Service闭环。
- D3：设计态metadata、生成物、运行态metadata、物理表关系。
- D4：Redis key、TTL、应用/租户隔离和失效时机。
- D5：frontend JAR、Ingress、OSS、线上资源来源链。
- D2/D8：发布/生成/部署的异步状态、幂等、超时、重试。
- D7：目标版本行为差异；5.3.496仍只能是OBSERVATION。

## 实施阶段

### Phase A：证据平台收口
完成Provider、Evidence Ledger、Schema、scope、limitations、冲突检测和报告统一模型。

验收：全量pytest、py_compile、CLI JSON合法；BLOCKED/UNVERIFIED不得升级为FACT。

### Phase B：只读Provider
依次建立HTTP、Kubernetes、Nacos、MySQL metadata、Redis metadata、Filesystem/JAR接口；默认只读，统一超时、脱敏、错误分类和证据来源。

### Phase C：UDC关键路径矩阵
针对Application、Entity、Field、Page Schema、MicroFlow、DataFlow、Version、Generate、Publish、Deploy、Runtime Metadata逐条记录前端请求、后端入口、DTO、Service、DAO/表、Redis/事件、artifact/version和状态。

状态区分STATIC FACT、HTTP PASS、API PASS、LIVE PASS、TIMEOUT、FAIL、BLOCKED、UNVERIFIED。

### Phase D：客户扩展边界
定向扫描web/core/facade/biz/ext，建立UDC Core与Customer Extension边界；SPI只有发现真实依赖才连接。

### Phase E：一致性与影响分析
建立metadata -> version -> generated artifacts -> runtime metadata -> physical tables -> Redis -> events -> routes/assets影响图，输出权威源、传播顺序、刷新、失败和回滚可能性。

### Phase F：Dry-run工作流
计划必须包含目标、环境、依赖、风险、确认要求、回滚和验证步骤；证据不完整时禁止生成可执行写计划。

### Phase G：最小真实闭环
仅在G0-G6通过且获得明确授权后，才在test2临时应用中执行实体/字段/页面/微流程保存和回读；发布、部署、清缓存、重启分开确认。

## 近期执行顺序

1. 收口Evidence Ledger和Schema。
2. 修正README测试数与snapshot-only说明。
3. 增加只读Provider接口和fixture测试。
4. 建立UDC关键路径矩阵并导入现有证据。
5. 定向扫描客户ext及SPI/Integration依赖。
6. 形成影响图和dry-run计划器。
7. 再决定是否申请最小真实写入授权。

## 明确不做

不把单客户/单版本事实泛化；不把HTTP 200当落库成功；不直接修改业务表或Redis；不自动发布/部署/重试；不创建默认UDC->SPI链路。
