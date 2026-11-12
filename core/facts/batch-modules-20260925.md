# 模块事实切片批量｜storage · nacos · deploy · bpm（2026-09-25）

> 口径：全部取自已 PASS 的模块线归档证据（u4/u5/u6 VERDICT + audit 文档 + 本会话 LIVE），
> 无证据处一律 UNVERIFIED。每格可独立拆回九段式，批量合写避免碎片化。

## G1 storage（core/facts/storage/mysql-redis-map.md 之原料）
- **MySQL**：主实例 `pc-2ze10b12l15nu9874.rwlb.rds.aliyuncs.com:3306`；两个 UDC app **同实例不同库**
  （`udc_test2` 平台元数据库 172 表 / 应用自身库 `znxmglpt…_test2` 1094 表 / `_uat` 1054 表——U5 VERDICT + 本会话 SHOW TABLES 复测）。
- **连接参数来源**：Nacos `public` dataId（datasource url/username/密码键；凭据值 0 入件，路径引用）。
- **Redis**：两 app **同实例同 db0 共享**（DBSIZE=15839，U5 STEP 实测）。
- **生成表落点**：实体 RELEASE 构建后物理表落**应用自身库**，非 udc_test2（本会话 yanshouda_m5654091886000795633 实证）。
- Verified：LIVE。约束：跳板 host pymysql 1.0.2 可连（密码含 `&`，bash 传参需 base64/单引号）。

## G2 nacos（core/facts/nacos/dataid-diff.md 之原料）
- 端点：MSE `mse-c19f9232-nacos-ans.mse.aliyuncs.com:8848`（k8s 内 svc，无公网；经 test2 跳板 curl）。
- 命名空间：`xiaozhua-uat`（totalCount=63 dataId）/ `xiaozhua-test2`（50+）；group=`xiaozhua`。
- 取数：`GET /v1/cs/configs?dataId=&group=xiaozhua&tenant=&search=blur&pageNo=1&pageSize=500`（本会话 LIVE）。
- 关键事实：每 dataId 的 `datasource.database` 明写（应用命名空间 dataId=app id 名）→ **DB 从 Nacos 直读**成立。
- 差异样例（LIVE FACT）：`udc` dataId → frontDomain lowcode-uat vs lowcode-test2、database udc_uat vs udc_test2。
- Verified：LIVE。约束：内网域名解析+跳板可达性依赖（09-24 曾断 3h）。

## G3 deploy（core/facts/deploy/build-chain.md 之原料）
- 入口 `POST /service/udc/runtime/deploy-normal`（DeployController：类级 `@RequestMapping("udc/runtime")` + 方法级 `deploy-normal`；09-27 LIVE 确诊 —— 旧记"类级前缀实测 404 / 可拼前缀 UNVERIFIED"已解除，裸 `/service/udc/deploy-normal` 经探针判为 404 无映射）。
- 参数枚举 LIVE：DeployTypeEnum{TEST,RELEASE,ON_ONLINE,DELTA} / ProjectTypeEnum{FRONTEND,BACKEND,ALL} / TerminalTypeEnum{ALL,PC,MOBILE}（javap 读值）。
- 编码映射：`deploy_type=2`=RELEASE；`state=1`=构建成功（udc_deploy_record 行实测，09-24 15:52 验收单构建）。
- 执行体：`boot-starter-sandbox-5.3.289` UdcAppDeployService（流水线 PipelineProperties + Redis 锁 + MQ 回调；Nacos pipeline.buildTimeout=900）。
- 失败形态实录：一致性检测未通过(AbstractDeployService.doParallel:242) / 编译错(maven-compiler-plugin 报 ext 模块 String→Long)——均 state=2 + msg 内嵌详情链接。
- Verified：LIVE+VERIFIED_STATIC_BYTECODE。

## G4 bpm / item-mgmt / spi / connector（core/facts/{mod}/stub.md）
- **BPM**：在盘唯一硬证据=UDC↔BPM 契约字节码（runtime 5.3.517 ↔ bpm-facade 3.12.101）+ flow 域 16 条 registry 契约（node-info/data-flow-map 族，多为 POST 未放行 POLICY_DENIED）。可写边界格：契约级，模块能力=UNVERIFIED。
- **事项管理/SPI/Connector**：**零在盘证据** → 只立占位 stub，整格 UNVERIFIED，禁止从"常见低代码平台"外推。这是事实纪律的硬边界。
- Verified：stub=UNVERIFIED（如实）。
