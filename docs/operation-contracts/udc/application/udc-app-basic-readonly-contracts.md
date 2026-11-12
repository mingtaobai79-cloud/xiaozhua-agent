# UDC 基本信息/应用域 只读操作契约（R1 P1）

- 证据单元: 本地 Maven（env=local-maven，来源按 config 组装：maven_root 键=config/environments.yaml#environments.local-maven.maven_root，artifact=udc-starter-runtime，version=5.3.517，path 按 config/artifact-versions.yaml#path_template → {maven_root}/{artifact}/{version}/{artifact}-{version}.jar；jar SHA-256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f 保留），离线只读；非 test2 镜像 5.3.496（config/environments.yaml#environments.test2.udc_image_version，两证据单元禁混写）
- 证据等级: javap -p -v -cp + class-entry SHA-256（python zipfile 随机访问读取）= VERIFIED_STATIC_BYTECODE
- 证据落盘: `docs/audit/artifacts/udc-app-basic/`（各 .javap.txt + manifest.txt + controller-class-list.txt）
- 约定: 路径逐字抄自 javap RuntimeVisibleAnnotations（@RequestMapping/@GetMapping/@PostMapping 的 value），未拼网关/服务前缀；写操作（create/copy/delete/update*/upgrade/exist 之外的写）一律剔除。

## 只读端点扩量扫描（负/正证据）

- 命令: `python zipfile.ZipFile(jar).namelist()` 过滤 `*Controller.class` → 命中 30 个控制器类（全清单见 `controller-class-list.txt`）。
- 逐类 javap -p -v 落盘 5 个候选: CustomApplicationController / AppDraftController / FormAppInfoController / NormalAppInfoController / UdcBaseAppInfoController。
- 只读命中: CustomApplicationController.selectListByConditions 两个重载 + UdcBaseAppInfoController.getDeployInfo + AppDraftController.select / AppDraftController.exist，共 5 条只读契约（≥3，无需域真空负证据段）。
- 说明: FormAppInfoController / NormalAppInfoController 自身仅类级 @RequestMapping（"{hostAppName}/dynamic-rest/com-seeyon/{currentAppName}/app-info" 与 "{currentAppName}/app-info"），方法级映射继承自父类 UdcBaseAppInfoController.getDeployInfo（GET deploy-info），作为第 5 条契约的类级路径证据记录，不重复成契约。
- 写操作剔除: CustomApplicationController 的 create/createAsync/newLayoutCreateAsync/copy/copyAsync/deleteByIds/updateCaption/updateUsageState/updateDeployState/updateAuth/upgrade；AppDraftController 的 createOrUpdate/delete/deleteAll/deleteTimeout。

---

## 契约 1: udc.application.search.no_page

1. operation_id: `udc.application.search.no_page`
2. HTTP method: `POST`（javap 原文 `@PostMapping(value=["/search-no-page"])`；按注解原文为 POST，操作语义为只读查询）
3. 控制器原路径: 类级 `@RequestMapping(value=["udc-runtime/custom-app"])` + 方法级 `@PostMapping(value=["/search-no-page"])`（逐字抄注解 value，未拼网关前缀）
4. 参数形态: `Map<String,Object> params`（@MultiRequestBody）+ `Sort sort`（@MultiRequestBody）
5. 返回 DTO: `ListResponse<CustomApplicationDto>`（com.seeyon.boot.starter.udcrt.dto.CustomApplicationDto）
6. evidence:
   - artifact: udc-starter-runtime-5.3.517.jar, jar SHA-256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f
   - class: com.seeyon.boot.starter.udcrt.controller.CustomApplicationController, method: selectListByConditions(Map,Sort)
   - class_sha256=d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55
   - javap 证据: docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt
7. LIVE 回读条件（本轮不做，仅写需要；凭据缺口=已解决）: 需可登录的V8 网关环境，凭据引用 config/environments.yaml#environments.test2.credential.file（值不入仓/不入日志），网关基址=同文件 gateway_base，appId=default_app_id，prefix=gateway_prefix_template，test2 镜像版本=udc_image_version（与本地 5.3.517 为两个证据单元，禁混写）；另需 udcAppDesigner/AppAdmin 角色；对同一 conditions Map 回读两次，断言 ListResponse.data 非空且 CustomApplicationDto identity 字段稳定（identity_matches）。
   【层次】契约 1/2 udc.application.search.* = 应用对象元数据查询面（custom-app 查询）；是否 = 已证 meta-data/* 首选读写面 UNVERIFIED（五层 设计态配置/运行态元数据/生成物/物理表/Redis 不可互相顶替）。

## 契约 2: udc.application.search.page

1. operation_id: `udc.application.search.page`
2. HTTP method: `POST`（javap 原文 `@PostMapping(value=["/search-page"])`）
3. 控制器原路径: 类级 `@RequestMapping(value=["udc-runtime/custom-app"])` + 方法级 `@PostMapping(value=["/search-page"])`
4. 参数形态: `PageInfo pageInfo` + `Map<String,Object> params` + `Sort sort`（均 @MultiRequestBody；内部经 PageRequest.from(pageInfo, params, sort) 归一）
5. 返回 DTO: `PageResponse<CustomApplicationDto>`
6. evidence:
   - artifact: udc-starter-runtime-5.3.517.jar, jar SHA-256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f
   - class: com.seeyon.boot.starter.udcrt.controller.CustomApplicationController, method: selectListByConditions(PageInfo,Map,Sort)
   - class_sha256=d3e82d8bbc65dc92d5f9d30532159f1d10169f2aef1eae6ab67c70d7ad75ae55
   - javap 证据: docs/audit/artifacts/udc-app-basic/CustomApplicationController.javap.txt
7. LIVE 回读条件（本轮不做；凭据缺口=已解决，引用 config/environments.yaml#environments.test2.credential.file，值不入仓/日志；网关基址=gateway_base、appId=default_app_id、prefix=gateway_prefix_template、镜像版本=udc_image_version，与本地 5.3.517 两证据单元禁混写）: 同契约 1；另需固定页码/页大小入参，断言 PageResponse 的 pageNum/pageSize/total 与 data 列表一致。
   【层次】契约 1/2 udc.application.search.* = 应用对象元数据查询面（custom-app 查询）；是否 = 已证 meta-data/* 首选读写面 UNVERIFIED（五层 设计态配置/运行态元数据/生成物/物理表/Redis 不可互相顶替）。

## 契约 3: udc.application.deploy_info

1. operation_id: `udc.application.deploy_info`
2. HTTP method: `GET`（javap 原文 `@GetMapping(value=["deploy-info"])`）
3. 控制器原路径: 方法级 `@GetMapping(value=["deploy-info"])`；参数 `@PathVariable(value="currentAppName")`。类级 @RequestMapping: UdcBaseAppInfoController 本体无类级 @RequestMapping；子类 FormAppInfoController 类级 `@RequestMapping(value=["{hostAppName}/dynamic-rest/com-seeyon/{currentAppName}/app-info"])`，NormalAppInfoController 类级 `@RequestMapping(value=["{currentAppName}/app-info"])`（逐字抄自各自注解，未拼网关前缀，未做组合推断）。
4. 参数形态: `String currentAppName`（@PathVariable，路径变量）
5. 返回 DTO: `SingleResponse<String>`（内部读取资源 app-deploy-info.json 原文）
6. evidence:
   - artifact: udc-starter-runtime-5.3.517.jar, jar SHA-256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f
   - class: com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController, method: getDeployInfo(String)
   - class_sha256=deebcc39cff41fc3b28748cacf5c44657a5f4cd600914b44ecd075436b3fde95
   - javap 证据: docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.proxy.controller.UdcBaseAppInfoController.javap.txt（父类）及 Form/Normal 两子类 javap.txt（类级路径）
7. LIVE 回读条件（本轮不做；凭据缺口=已解决，引用 config/environments.yaml#environments.test2.credential.file，值不入仓/日志；网关基址=gateway_base、appId=default_app_id、prefix=gateway_prefix_template、镜像版本=udc_image_version，与本地 5.3.517 两证据单元禁混写）: 需网关环境 + 目标应用 currentAppName 已部署；回读同 currentAppName，断言 SingleResponse.data（部署信息 JSON 字符串）非空且稳定。网关 service 前缀 UNVERIFIED（离线不可确证，禁止拼前缀）。
   【层次】契约 3 deploy_info = 生成物层：读 app-deploy-info.json（部署时生成），非运行态元数据；LIVE 回读仅作部署一致性旁证，验收锚点须元数据 identity_matches，HTTP 200/JSON 非空不算证据。

## 契约 4: udc.application.draft.select

1. operation_id: `udc.application.draft.select`
2. HTTP method: `POST`（javap 原文 `@PostMapping(value=["select"])`；操作语义为只读"查找当前用户草稿"）
3. 控制器原路径: 类级 `@RequestMapping(value=["udc-runtime/app-draft"])` + 方法级 `@PostMapping(value=["select"])`
4. 参数形态: `String dataId`（@MultiRequestBody，见 javap RuntimeVisibleParameterAnnotations；内部经 SingleRequest.from(dataId) 归一；参数名 dataId 取自 LocalVariableTable）
5. 返回 DTO: `SingleResponse<AppDraftDto>`（com.seeyon.boot.starter.udcrt.dto.AppDraftDto）
6. evidence:
   - artifact: udc-starter-runtime-5.3.517.jar, jar SHA-256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f
   - class: com.seeyon.boot.starter.udcrt.controller.AppDraftController, method: select(String)
   - class_sha256=5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9
   - javap 证据: docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt
7. LIVE 回读条件（本轮不做；凭据缺口=已解决，引用 config/environments.yaml#environments.test2.credential.file，值不入仓/日志；网关基址=gateway_base、appId=default_app_id、prefix=gateway_prefix_template、镜像版本=udc_image_version，与本地 5.3.517 两证据单元禁混写）: 需网关环境 + 登录用户且存在 dataId 对应草稿；回读同 dataId，断言 SingleResponse.data 的 AppDraftDto identity 稳定。
   【层次】契约 4/5 app-draft select/exist = 设计态配置层：AppDraft 草稿读取，非运行态元数据。

## 契约 5: udc.application.draft.exist

1. operation_id: `udc.application.draft.exist`
2. HTTP method: `POST`（javap 原文 `@PostMapping(value=["exist"])`；操作语义为只读"当前用户是否存在草稿"）
3. 控制器原路径: 类级 `@RequestMapping(value=["udc-runtime/app-draft"])` + 方法级 `@PostMapping(value=["exist"])`
4. 参数形态: `String dataId`（@MultiRequestBody，见 javap RuntimeVisibleParameterAnnotations；内部经 SingleRequest.from(dataId) 归一；参数名 dataId 取自 LocalVariableTable）
5. 返回 DTO: `SingleResponse<AppDraftExistDto>`（com.seeyon.boot.starter.udcrt.dto.AppDraftExistDto）
6. evidence:
   - artifact: udc-starter-runtime-5.3.517.jar, jar SHA-256=74ae50bd8510414113248f0b1d400bca80d2ae2e0022c9dbbb31321a6040a66f
   - class: com.seeyon.boot.starter.udcrt.controller.AppDraftController, method: exist(String)
   - class_sha256=5090304dcb69cd0d3cd7b4e961d6ceff5f41e56d27b60eecf48950a34e5fabb9
   - javap 证据: docs/audit/artifacts/udc-app-basic/com.seeyon.boot.starter.udcrt.controller.AppDraftController.javap.txt
7. LIVE 回读条件（本轮不做；凭据缺口=已解决，引用 config/environments.yaml#environments.test2.credential.file，值不入仓/日志；网关基址=gateway_base、appId=default_app_id、prefix=gateway_prefix_template、镜像版本=udc_image_version，与本地 5.3.517 两证据单元禁混写）: 需网关环境 + 登录用户；回读同 dataId，断言 AppDraftExistDto 的 exist 布尔值两次一致。
   【层次】契约 4/5 app-draft select/exist = 设计态配置层：AppDraft 草稿读取，非运行态元数据。

## 元数据锚点对齐（08:45Z 人指）

- 验收锚点 = 回读元数据 identity_matches（HTTP 200 / Boolean 非空不算证据，与本文件 4 条 LIVE 的 identity 稳定断言一致）。
- 平台 meta-data 首选面已证三端点（OBSERVATION 级，证据落盘于相邻域 javap，非本域新证）：
  - `udc-runtime/meta-data/select-function-node-tree/{appName}`（@GetMapping，class=com.seeyon.boot.starter.udcrt...UdcFunctionNodeController，证据: docs/audit/artifacts/udc-runtime-5.3.517/UdcFunctionNodeController.javap.txt）
  - `udc-runtime/meta-data/check-page-exists`（@PostMapping，class=UdcRtPageInfoController，证据: docs/audit/artifacts/udc-page-5.3.517/UdcRtPageInfoController.javap.txt）
  - `udc-runtime/meta-data/select-host-and-only-page-pages`（@PostMapping，class=UdcRtPageInfoController，同上证据）
  - 该三端点与本域 custom-app / app-draft 面为**相邻面**；MERGE 落库并表时以 meta-data 族为准。
- 五层不顶替（设计态配置 ≠ 运行态元数据 ≠ 生成物 ≠ 物理表 ≠ Redis）：本域契约 1/2 为应用对象元数据查询面（custom-app，是否=已证 meta-data/* 首选面 UNVERIFIED，不顶替不推断）；契约 3 为生成物层（app-deploy-info.json）；契约 4/5 为设计态配置层（AppDraft）。
- 版本族隔离：本域证据属 5.3 族（本地 5.3.517 / test2 5.3.496 两证据单元，config 引用见文件头），元数据结构按族隔离，禁以 5.3.517 推断 5.3.496 元数据层行为。
