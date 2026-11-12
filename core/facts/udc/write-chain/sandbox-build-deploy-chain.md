# SANDBOX 构建部署机制 —— 权威事实（CFR 字节码 + LIVE 双源）

> 取证时间：2026-10-15。证据等级：`VERIFIED_STATIC_BYTECODE`（CFR 反编译）+ `LIVE`（test2 REST 实测）。
> 证据件：`scratch/sbx_biz/*.java`（app-sandbox-biz/web 5.3.271 反编译）、`scratch/sbx_controller.java`（udc-web 5.3.517 SandboxController）、`scratch/DeployController.class`/`DeploymentController`（CFR 摘要）。

## 1. sandbox 是什么（定性）

**sandbox = UDC 应用的构建+部署执行器**（devops pipeline 的执行端），不是业务应用。
- Pod：`sandbox--5156856193794012477-test2-*`（test2 集群，1 副本），镜像 `chit-acr-registry.../app-sandbox:5.3.x`
- 启动参数：`-Dseeyon.sandbox.id=-5156856193794012477 -Dseeyon.design.env=test2 -Dseeyon.env.namespace=lowcode-test`
- 构件：`app-sandbox.jar`（launcher）+ `BOOT-INF/lib/app-sandbox-biz-5.3.271.jar` + `app-sandbox-web-5.3.271.jar`
- 用户原话印证："sandbox 本质很多是后端接口，前端没啥应用"

## 2. 构建链（BuildTask，CFR 证实）

```
udc-web（设计器点"构建/发布"）
  → Redis 队列入队：
      {env}:sandbox:build:queue   (list，任务ID)
      {env}:sandbox:build:hash    (hash，taskId → BuildParamDto)
      {env}:sandbox:build:status  (状态)
    {env}=SystemEnvironment.getEnv() → test2
  → app-sandbox BuildTask 消费（buildThreadNum=3 线程，轮询 sleep 3s）
  → 构建流水线（LIVE 实测 37 行日志，2026-10-13 datamigration 1.0.7 构建全程 4m55s）：
      任务开始(3ms) → 应用元数据准备(1s+DependCodeContextAware 10s) → 一致性检测(2s)
      → 生成后端代码(14s, 版本=appName:1.0.7) → 生成元数据(OSS storageKey=metadata/udc/...)
      → [app-sandbox]沙箱构建(编译由沙箱-5156856193794012477完成) → 环境数据准备
      → 前端生成依赖 → 生成前端代码(6s) → 拉取手写代码(前端2.2s+后端1.8s，git 仓库)
      → 推送代码(前后端) → 前端PC编译(20s) + 前端MOBILE编译(15s) → 后端编译(79s)
      → 生成镜像(45s, 镜像=chit-acr-registry.../seeyonv8test/<appName>:<tag>)
      → 部署(147s, appName:1.0.7) → 结束
  → 回调：AppServiceReliableInvoker.invoke
      interface=com.seeyon.boot.starter.sandbox.appservice.SandboxClientAppService
      method=taskCallBack(SingleRequest<taskId>)   ← udc-web 侧实现（收构建结果/更新状态）
      （失败另路：com.seeyon.app.common.customized.development.appservice.CustomizedDevelopmentAppService）
```

配置（`AppSandboxProperties`，前缀 `seeyon.sandbox`）：
`repositoryPath` / `udcYamlConfigDataId=udc-app-yaml` / `ciCdTaskTimeOut=3600000` / `deployTimeOut=1800000` / `buildThreadNum=3` / `buildThreadSleepTime=3000` / `restartTaskEnd=true`

## 3. 部署链（SandboxUdcAppDeployService，CFR 证实）

Redis 键：
- 运行中部署：`{env}:udc:app:test:deploy:run:{sandboxId}`（hash，field=`appName+appVersion`，TTL 1 天）
- 部署信息：`{env}:udc:app:sandbox:deploy-info:{appName}`（value=DTO，TTL 7 天）
- 状态：`deployStatusRedisKey(appName, appVersion)`（AppDeployStatus）
- 调度器：`scheduleAtFixedRate(30s 首延, 10s 周期)` 扫运行队列 → deployCheck / 超时检查（checkDeployTimeOut）
- 应用 YAML：Nacos dataId 先取 `{appName}-yaml`，空则回落 `udc-app-yaml`（SandboxEnvironmentInit 相关）
- K8s：`DeploymentOperate/PodOperate`（boot-starter-k8s）做 deploy/restart/getPodIp；`getPodIp` 由 Nacos RegisterCenterService 解析

## 4. udc-web 侧 REST 面（设计器调用端）

### SandboxController（`udc/sandbox`，@HasRole OrgAdmin/udcAppDesigner/OpsAdmin/udcSystemAdmin）
| 方法 | 路径 | 语义 |
|---|---|---|
| POST | /udc/sandbox/select-roles | 沙箱应用角色（body: sandboxId, appName）|
| GET | /udc/sandbox/select/{appId} | 沙箱信息获取 |
| GET | /udc/sandbox/build-info/{appId} | 构建信息（DeployTypeEnum.RELEASE）|
| GET | /udc/sandbox/delta-build-info/{appId} | 增量构建信息（DELTA）|
| GET | /udc/sandbox/release-build-info/{appId} | 上架构建信息（ON_ONLINE）|

### DeployController（`udc/runtime`）
- POST `/udc/runtime/deploy-normal`（DeployNormalDto）= 普通发布
- POST `/udc/runtime/deploy-form` / `cross-deploy-form`（DeployFormDto）= 表单发布/跨域
- POST `/udc/runtime/deploy/stop/{deployId}`、`/udc/runtime/deploy/ferry`（迁移）
- POST `/udc/runtime/search-deploy-status/{deployId}`、`search-by-name/{appName}`、`search-deploy`
- GET `/udc/runtime/frontend/metadata/{appId}`、POST `expect-deploy-time`、`deploy-statistics`、`/auth-access-url`

### DeploymentController（`udc/deployment`）
- POST `/udc/deployment/restart`（appId）= 重启应用
- POST `/udc/deployment/app-ready-state` = 就绪状态
- POST `/udc/deployment/latest-test-info` = 最后一次测试信息
- POST `/udc/deployment/app-online`（appId）/ `app-online-new`（DeployNormalDto）= 上线
- POST `/udc/deployment/app-delta-deploy`（DeployNormalDto）= 增量发布

## 5. app-sandbox 自身暴露面

### REST（app-sandbox/sandbox/server，SandboxServerController）
- GET `healthCheck`（SandboxServer.isRunning）
- GET `shell`（body=shell 串，在 `{baseRoot}/frontend-dependencies/plat-dependencies/udc-shared-deps/node_modules/` 执行；默认 `find -path '*/bin/*.js'`）@HasRole OpsAdmin/udcAppDesigner
- GET `settings`（下载 /A8C/maven/conf/settings.xml）
- GET `download-war?warPath=`（flexible-war 走 FileService）

### AppService 代理面（@Service SandboxServer，非 REST；经 AppServiceReliableInvoker 调用）
`restartApp / getRestartAppProgress / cleanSandboxAppData / dropAppDatabase / deleteImage / unLoadApp / getBuildLogs / readLogLines(appName:lines) / getSandboxInfo / inspectionImageRepoTaskSubmit / lockAppImage`

### 数据清理（SandboxAppDataService）
- `dropAppDatabase(appName)`：直接 drop 应用库（checkDbExists→dropDatabase）
- `cleanSandboxAppData(appName)`：按 appName 取表名 → `delete from <table>` 逐表清数据
- 依赖：DataSourceProperties（应用独立数据源）+ MetadataQueryAppService + MQ 通知

## 6. LIVE 验证（2026-10-15，test2）

- `GET /service/udc/sandbox/select/8704025620829192834`（数据迁移）→ BOOT_0000，
  `sandboxCreateStatus=ENABLE`，logs=["【沙箱环境准备】沙箱准备完成"]
- `GET /service/udc/sandbox/build-info/8704025620829192834` → BOOT_0000，
  `state=SUCCESS progress=100`，buildTime=2026-10-13 11:29:56（版本 1.0.7），总耗时 294s，37 行流水日志（全文见上）
- `GET /service/udc/sandbox/select/6419954374508955097`（zzprobe）→ UDC_APP_0001 "The application is not exist"
  （zzprobe 已被删除，与用户"那个应用被我删除了"一致）

## 7. 与既有事实的接驳

- 旧认知「设计器点发布 → appVersion/{appGuid} 查部署历史」只是**查询面**；真实执行面 = 本文件的 Redis 队列 → sandbox 构建 → 镜像 → K8s 部署链。
- 构建日志里的 `拉取手写代码`（前后端 git 仓库）对应 ext 手工代码来源；`生成镜像` 产物即部署 Deployment 的 image。
- 部署记录双轨：Redis（运行/信息/状态）+ `udc.application.appVersion/{appGuid}`（历史查询）。
