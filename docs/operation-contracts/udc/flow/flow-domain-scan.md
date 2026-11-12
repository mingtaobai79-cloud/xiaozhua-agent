# 流程域(BPM集成) P0 扫描定位 — flow-domain-scan.md

- 轮次: R1 (P0 扫描定位) | 证据单元: 本地 Maven 5.3.517（6 个 UDC jar）
- 生成时间(本机时钟): 2026-09-17 22:1x +08:00
- 证据等级标注约定: OBSERVATION=清单/目录/常量池观察；HYPOTHESIS=推断，待 R2 javap -p -v 确认；VERIFIED=后续 javap -v 全量+sha256
- 硬约束遵守: 全轮只读（jar tf / javap 只读 + sha1sum 只读 + git status）；未触碰 bpm-facade 5.3.374 与 app-approval 5.3.295（仅本地存在确认，未进任何证据）；未拼网关前缀（下列路径均为控制器 @RequestMapping/@*Mapping 原字面量，逐字保留）；冻结文件零改动。

## 构件定位（OBSERVATION）

| 模块 | jar 路径 | class 总数(jar tf .class) | BPM 命中(.class) | jar sha1(实测=sha1sum, 与 maven .sha1 逐一对上) |
|---|---|---|---|---|
| udc-common | <MAVEN_REPO>/com/seeyon/udc-common/5.3.517/udc-common-5.3.517.jar | 460 | 4 | 6e85481861a2e65a02ba809e1a2003a2f34c3cbf |
| udc-facade | <MAVEN_REPO>/com/seeyon/udc-facade/5.3.517/udc-facade-5.3.517.jar | 66 | 0 | d4b5abdda968a510802c11a6fd8c33f39dde2aa3 |
| udc-starter-customplan | <MAVEN_REPO>/com/seeyon/udc-starter-customplan/5.3.517/udc-starter-customplan-5.3.517.jar | 83 | 5 | 5bdaa4452d605ceabb33bb69638cd71436b3b832 |
| udc-starter-dataflow | <MAVEN_REPO>/com/seeyon/udc-starter-dataflow/5.3.517/udc-starter-dataflow-5.3.517.jar | 121 | 8 | de9f1cfba73b34cd4667741ff85e9482105619e7 |
| udc-starter-lowcode | <MAVEN_REPO>/com/seeyon/udc-starter-lowcode/5.3.517/udc-starter-lowcode-5.3.517.jar | 141 | 0 | bbab2b21fde1b490c4c78a5ada6ab1e8694f7367 |
| udc-starter-runtime | <MAVEN_REPO>/com/seeyon/udc-starter-runtime/5.3.517/udc-starter-runtime-5.3.517.jar | 346 | 22(类)/23(行) | e3e27271fab53b0610a954d83dadab003cabad62 |

BPM 命中明细(OBSERVATION, jar tf | grep -i bpm, 只列 .class):
- udc-common(4): utils/Cache4BpmUtil(+内部类$PermissionCheckStatusType)、dto/PageBPMProcessEventDto、event/AfterBpmProcessEvent
- udc-facade(0): 无 bpm 命中（PageProcessEvent* 走 "PageProcessEvent" 而非 "bpm" 关键词，见下）
- udc-starter-customplan(5): enums/PageBpmEventSearchTypeEnum、dto/CBpmNodePermissionRequestDto、dto/BpmFromPermissionCheckDto、appservice/BpmNodeInfoAppService、controller/BpmNodeInfoController
- udc-starter-dataflow(8): dto/DataFlow4BpmReqDto、domain/service/BpmInterfaceService、appservice/DataFlowForBpmAppServiceImpl、api/DataFlowForBpmAppService、controller/DataFlowForBpmController、mq/DataFlow4BpmReqMessage、mq/DataFlowWithBpmListener、mq/DataFlow4BpmReqRetryDelayMessage
- udc-starter-lowcode(0): 无 bpm 命中
- udc-starter-runtime(22 类/23 行): 集中在 udcrt/dto(BpmParameterDataDto/BpmProcessLaunchResultDto/BpmRetryDto/BpmRetryTaskResultDto)、udcrt/domain/service(BpmPermissionHandlerService/BpmRetryService/BpmActionProcessingService/bpmpermisssion/*)、udcrt/event/listener(BpmRetryListener/BpmRetryDelayMessage)、udcrt/api/UdcBpmProcessService、udcrt/appservice/UdcBpmProcessServiceImpl、udcrt/util/BpmDataUtil、udcrt/constants/BpmProcessConstant、udcrt/exception/BpmProcessErrorCode
- facade 侧 PageProcessEvent* 补扫(OBSERVATION, 关键词 PageProcessEvent/PageBpm): com/seeyon/udc/dto/page/PageProcessEventDto、com/seeyon/udc/dto/page/PageProcessEventSearchDto、com/seeyon/udc/api/PageProcessEventAppService

## 候选类初判（OBSERVATION/HYPOTHESIS，基于 javap -v 注解表常量池 + RuntimeVisibleAnnotations 区）

方法级路径与类级 @RequestMapping 值取自各 jar 的 javap -v 常量池(String 字面量)与注解区，未拼任何网关前缀；类级 @RequestMapping 的具体 value 数组绑定待 R2 javap -p -v 落盘证据确认。

### ① DataFlowForBpmController（udc-starter-dataflow 5.3.517）
- FQCN: com.seeyon.boot.starter.dataflow.controller.DataFlowForBpmController
- 注解表初判: @RestController + @RequestMapping（常量池值 "udc-runtime/bpm"）→ REST controller
- 方法: fillErrorFlowData(FillFlowReqDto) @PostMapping("fill-data") @RestApiOperation，返回 SingleResponse<Boolean>
- 判定: REST 控制器，但唯一方法为 POST 写操作（fill 流转数据）→ 写侧，不进只读契约（仅记录存在）

### ② DataFlowRtMapController（udc-starter-dataflow 5.3.517）
- FQCN: com.seeyon.boot.starter.dataflow.controller.DataFlowRtMapController（extends BaseComponentController）
- 注解表初判: @RestController + @RequestMapping（常量池 "udc-runtime/data-flow-map"）→ REST controller
- 方法: selectByCondition(DataFlowRtMapQueryDto) @PostMapping("search") @RequestBody → ListResponse<DataFlowRtMapDto>（读，POST 形态）；selectById(Long) @GetMapping("{id}") @PathVariable → SingleResponse<DataFlowRtMapDto>（读，GET 形态）
- 判定: REST 控制器，2 方法均只读

### ③ DataFlowRtMappingController（udc-starter-dataflow 5.3.517）
- FQCN: com.seeyon.boot.starter.dataflow.controller.DataFlowRtMappingController（extends BaseComponentController）
- 注解表初判: @RestController + @RequestMapping（常量池 "udc-runtime/data-flow-mapping"）→ REST controller
- 方法: selectOriginalMappingList @PostMapping("search-original")→ListResponse<DataFlowRtMappingDto>(读)；selectById @GetMapping("{id}")→SingleResponse<DataFlowRtMappingDto>(读)；selectMappingInitData @PostMapping("init-data")→SingleResponse<DataFlowRtEditInitialDataDto>(读)；selectDetailByCondition @PostMapping("detail")→SingleResponse<DataFlowRtMappingDto>(读)；update @PostMapping→SingleResponse<DataFlowRtMappingDto>(写)；updateMappingState @PostMapping("state")→SingleResponse<OperationResultDto>(写)
- 判定: REST 控制器，4 读 2 写，只读子集可用于契约

### ④ BpmNodeInfoController（udc-starter-customplan 5.3.517）
- FQCN: com.seeyon.boot.starter.customplan.controller.BpmNodeInfoController（extends BaseComponentController）
- 注解表初判: @RestController + @RequestMapping（常量池 "node-info"）→ REST controller
- 方法: selectByComplexCondition(CBpmNodePermissionRequestDto) @PostMapping("/search") @RequestBody → SingleResponse<BpmNodePermission4PageDto>（读，POST 形态；方法内从 RequestContext.get().getUserId() 回填 userId）
- 判定: REST 控制器，1 只读方法。核心 BPM 节点权限查询，BPM 集成强相关

### ⑤ UdcFunctionNodeController（udc-starter-runtime 5.3.517）
- FQCN: com.seeyon.boot.starter.udcrt.controller.UdcFunctionNodeController（extends BaseComponentController）
- 注解表初判: @RestController + @RequestMapping（常量池 "udc-runtime/meta-data"）→ REST controller
- 方法: selectFunctionNodeTreeMetaData(String appName) @GetMapping("select-function-node-tree/{appName}") @PathVariable → ListResponse<UdcFunctionNodeMetadataDto>（读，GET 形态）
- 判定: REST 控制器，1 只读方法

### ⑥ UdcFormDataQueryController（udc-starter-runtime 5.3.517）
- FQCN: com.seeyon.boot.starter.udcrt.controller.UdcFormDataQueryController（extends BaseComponentController）
- 注解表初判: @RestController + @RequestMapping（常量池 "udc-runtime/data"）→ REST controller
- 方法: queryFormData(EntityDataRequestDto) @PostMapping("/query") @RequestBody → SingleResponse<EntityDataResponseDto>（读，POST 形态；委托 FormDataQueryService.selectEntityData）
- 判定: REST 控制器，1 只读方法

### ⑦ PageProcessEventAppService（udc-facade 5.3.517，交叉验证，禁写契约）
- FQCN: com.seeyon.udc.api.PageProcessEventAppService
- 注解表初判: public interface，零 Spring MVC 注解（javap -v 注解区计数 0）；唯一方法 selectListByCondition(SingleRequest<PageProcessEventSearchDto>) → ListResponse<PageProcessEventDto>
- 判定: 内部 service/api 接口（facade 无 controller 承接）→ 只作交叉验证，禁写进 REST 契约。其读侧语义可由 ②③④ 对应 controller 覆盖

### ⑧ UdcBpmProcessService（udc-starter-runtime 5.3.517，交叉验证，禁写契约）
- FQCN: com.seeyon.boot.starter.udcrt.api.UdcBpmProcessService
- 注解表初判: public interface，零 Spring MVC 注解；8 方法全部写/事件侧: validCreateFilterData / validUpdateFilterData / validFilterData / processBpmApproval / processBpmStop / processBpmCancel / processBpmTakeBack / updateData
- 判定: 内部 appservice API（BPM 事件回调入口，非 REST）→ 只作交叉验证，禁写进 REST 契约

### ⑨ UdcBpmProcessServiceImpl（udc-starter-runtime 5.3.517，交叉验证，禁写契约）
- FQCN: com.seeyon.boot.starter.udcrt.appservice.UdcBpmProcessServiceImpl（implements UdcBpmProcessService）
- 注解表初判: 零 Spring MVC 注解（implements ⑧）；委托 BpmActionProcessingService
- 判定: 内部 service 实现 → 禁写进 REST 契约

> 候选计数说明: main HANDOFF 记 "10 候选类"，本域实测落 9 个独立 FQCN（②③④⑤⑥⑦⑧⑨ 加 ①=9；main 括号内 "UdcBpmProcessService/Impl" 展开为 ⑧⑨ 两个类）。差异为计数口径（Service/Impl 是否拆两计），非遗漏；9 个 FQCN 全部已 javap 定位成功。

## R2 只读契约候选清单（≥4 条，HYPOTHESIS 级，待 R2 javap -p -v 全量落盘+sha256 确认）

| 候选 | 类(FQCN 简名) | 方法 | HTTP | 控制器原路径(类级@ReqMapping+方法级, 逐字, 不拼网关前缀) | 参数形态 | 返回 DTO | 读/写 |
|---|---|---|---|---|---|---|---|
| R2-C1 | BpmNodeInfoController (customplan) | selectByComplexCondition | POST | node-info/search | @RequestBody CBpmNodePermissionRequestDto | SingleResponse<BpmNodePermission4PageDto> | 读 |
| R2-C2 | UdcFunctionNodeController (runtime) | selectFunctionNodeTreeMetaData | GET | udc-runtime/meta-data/select-function-node-tree/{appName} | @PathVariable appName | ListResponse<UdcFunctionNodeMetadataDto> | 读 |
| R2-C3 | UdcFormDataQueryController (runtime) | queryFormData | POST | udc-runtime/data/query | @RequestBody EntityDataRequestDto | SingleResponse<EntityDataResponseDto> | 读 |
| R2-C4 | DataFlowRtMapController (dataflow) | selectById | GET | udc-runtime/data-flow-map/{id} | @PathVariable id | SingleResponse<DataFlowRtMapDto> | 读 |
| R2-C5 | DataFlowRtMapController (dataflow) | selectByCondition | POST | udc-runtime/data-flow-map/search | @RequestBody DataFlowRtMapQueryDto | ListResponse<DataFlowRtMapDto> | 读 |
| R2-C6 | DataFlowRtMappingController (dataflow) | selectById | GET | udc-runtime/data-flow-mapping/{id} | @PathVariable id | SingleResponse<DataFlowRtMappingDto> | 读 |
| R2-C7 | DataFlowRtMappingController (dataflow) | selectOriginalMappingList | POST | udc-runtime/data-flow-mapping/search-original | @RequestBody OriginalDataFlowMappingListQueryDto | ListResponse<DataFlowRtMappingDto> | 读 |

排除项（写侧，不进只读契约）: DataFlowForBpmController.fillErrorFlowData(POST fill-data)；DataFlowRtMappingController.update / updateMappingState；UdcBpmProcessService.process*/updateData（非 REST 事件回调）。

> 说明: 上表 7 条 HYPOTHESIS 均已满足"≥4 条只读候选"。R2 需对 R2-C1..C4（或全 7）逐条 javap -p -v 全量落盘到 docs/audit/artifacts/udc-flow-5.3.517/ + 记录 jar sha256 + 提取 7 要素（operation_id/method/原路径/参数/返回DTO/evidence/LIVE回读条件），并出 registry-entries.md。类级 @RequestMapping value 数组的"绑定到类而非字段"须在 R2 用注解体 0: #N(...) 位置确认，以排除路径误读。

## 本地阻塞/负证据
- 无域真空：只读 GET/POST-读 候选共 7 条 ≥ 4，无需扩到相邻版本（bpm-facade 5.3.374 / app-approval 5.3.295）补数；本轮未用其作证据。
- 设计态 udc-web/udc-biz/udc-assemble/udc-extend 本地 MISSING（与 microflow P1 缺口一致）→ 本域 REST 契约只锚定 5.3.517 已有 6 jar。

## 结束读回（本轮）
- 本文件为 R1 唯一产出（<SEEYON_AGENT_ROOT>/docs/operation-contracts/udc/flow/flow-domain-scan.md）。
- git 基线快照: implementer/git-baseline-R1.txt（R1 开始前 git status --porcelain，14 行，HEAD a799744）；R1 结束时 git status 与基线比对见 PROGRESS 消息正文。
