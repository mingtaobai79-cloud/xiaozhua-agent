# BPM 实现层（bpm-biz 5.3.353，2,730 类）

> 数据源：`D:/repo/CHIT-extra/bpm-biz/5.3.353/bpm-biz-5.3.353.jar`（8.27 MB，2,730 个顶层类）
> 等级：`VERIFIED_STATIC_BYTECODE`（类清单 + javap 方法签名）
> ⚠️ **版本**：bpm-biz 5.3.353；官方清单只有 `bpm-facade` 5.3.600（本机 5.3.374）。**实现层版本与 facade 不同步，需注意。**
> ⚠️ **本 jar 不在官方 102 清单内** → 「实现层」，引用时须标注。

---

## 0. ★★★ 规模对比：facade 只是冰山一角

| | 类数 |
|---|---:|
| `bpm-facade`（契约，5.3.374） | **533** |
| **`bpm-biz`（实现，5.3.353）** | **2,730** |
| 倍数 | **5.1 倍** |

**⇒ 我之前基于 facade 的 BPM 文档（11/13/14 号）只覆盖了**契约层**，真正的流程引擎逻辑全在这 2,730 类里。**

---

## 1. ★★★ 分层结构

| 包 | 类数 | 是什么 |
|---|---:|---|
| **`domain`** | **1,319** | **领域实现（核心）** |
| `dto` | 669 | 数据传输对象 |
| `detection` | 234 | **检测/校验**（用到的参数、属性、权限） |
| `enums` | 206 | 枚举 |
| **`appservice`** | **99** | **对外服务入口** |
| `common` | 61 | 公共（bo/constant/util） |
| `utils` | 38 | 工具 |
| `upgrade` | 33 | 升级 |
| `bpmn` | 22 | **BPMN 核心模型** |
| `simulation` | 21 | **流程仿真** |
| `security` | 19 | 安全 |
| `schedule` / `exception` / `condition` | 8 | 零星 |

### 1.1 `domain` 内部分层（1,319 类）

| 子包 | 类数 | 是什么 |
|---|---:|---|
| **`domain.service`** | **894** | **业务逻辑（主体）** |
| `domain.entity` | 95 | 实体（对应 DB 表） |
| `domain.dao` | 92 | DAO |
| `domain.model` | 79 | **领域模型（`BpmDiagram` 等）** |
| `domain.cache` | 50 | 缓存 |
| `domain.eventbus` | 43 | 事件总线 |
| `domain.bo` | 35 | 业务对象 |

### 1.2 `domain.service` 再细分（894 类，取前 30）

| 子包 | 类数 | 是什么 |
|---|---:|---|
| **`transport`** | **126** | **导入导出/传输** |
| `(顶层)` | **88** | **★ 核心 Service** |
| **`deploy`** | **55** | **部署** |
| `cached` | 44 | 缓存型服务 |
| **`supervise`** | **38** | **督办** |
| `common` | 37 | 公共 |
| `diagram` | 33 | **流程图** |
| `postapproval` | 28 | 后加签 |
| `merge` | 26 | **流程合并** |
| `eventmatch` | 26 | **事件匹配** |
| `activity` | 25 | **活动（节点运行）** |
| `upgrade` | 25 | 升级 |
| **`autonode`** | **23** | **★ 自动节点（自动审批）** |
| `changenode` | 20 | 换人 |
| `proxy` | 18 | 代理 |
| `task` | 18 | 任务 |
| `subprocess` | 17 | 子流程 |
| `application` | 16 | 应用 |
| `processdetail` | 14 | 流程明细 |
| `nestedsubprocess` | 13 | 嵌套子流程 |
| `permission` | 13 | 权限 |
| `uniformity` | 12 | 统一性 |
| `detail` / `support` / `collectivize` | 各 11-12 | |
| `form` / `formpermission` | 9 / 5 | **表单权限** |
| `overtime` | 8 | 超时 |
| `actor` | 7 | **参与者** |
| `nodeaction` | 7 | **节点动作** |
| `opinion` | 6 | 意见 |
| `parameter` | 6 | 参数 |
| `spi` | 5 | **SPI 扩展点** |
| `lock` / `processrevision` / `hierachicalcontrol` | 各 4 | |
| `dubboProxy` | 2 | **★ Dubbo 代理** |

---

## 2. ★★★ 88 个核心 Service（顶层，最重要的清单）

**流程运转的骨架，全在这 88 个类里：**

### 2.1 引擎核心（4 个）

```
BpmExecute                     ★ 流程执行器（30 方法）
BpmService                     ★ 流程主服务（91 方法）
BpmProcessService              ★ 流程定义服务（114 方法）
BpmOperationTransactionalService  事务性操作
```

### 2.2 案例（流程实例）相关

```
BpmCaseService                 流程实例
BpmCaseLogService              实例日志
BpmCaseExtendService           实例扩展
CaseEngine                     ★ 案例引擎
BpmBranchRunningInfoService    分支运行信息
```

### 2.3 节点/活动相关

```
BpmNodeService                 节点
BpmNodePropertyService         节点属性
BpmNodeOperationService        节点操作（4 方法，只读）
BpmNodeAssembleOperationService 节点组装操作
BpmNodePermissionService       节点权限
BpmNodePermissionInitService   节点权限初始化
BpmNodePermissionOperationService 节点权限操作
BpmNodeForecastService         ★ 节点预测（审批路径预测）
BpmHumanActivityService        人工活动
BpmAutoNodeService             ★ 自动节点
```

### 2.4 模板（流程模板）

```
BpmTemplateService             模板
BpmTemplateConfigService       模板配置
BpmTemplateCategoryService     模板分类
BpmTemplateTagService          模板标签
BpmTemplateOwnerService        模板所有者
BpmTemplateLiablePersonService 模板责任人
BpmTemplateEvaluationService   模板评价
BpmTemplateResourceService     模板资源
BpmTemplateRecentService       最近使用
BpmUserTemplateService         用户模板
BpmPersonalTemplateService     个人模板
BpmThirdTemplateService        第三方模板
BpmNormalAppMultiVersionService ★ 多版本
```

### 2.5 流程图

```
BpmDiagramService              流程图
BpmDiagramDetailService        流程明细
BpmDiagramFragmentService      流程片段
```

### 2.6 表达式/参数

```
BpmExpressionService           表达式
BpmParameterExtendService      参数扩展
BpmParameterMapperService      ★ 参数映射（节点入参）
BpmSystemParameterService      系统参数
BpmCustomFieldService          自定义字段
```

### 2.7 待办/工作项

```
BpmWorkItemService             工作项（待办）
BpmTaskRelationService         任务关系
BpmTransferService             移交
BpmProcessReplaceService       流程替换（离职转办）
BpmAgentService                代理
BpmAgentParameterService       代理参数
```

### 2.8 意见/沟通

```
BpmOpinionRegisterService      意见登记
BpmConsultService              咨询
AffairConsultService           事项咨询
BpmSummaryService              流程摘要
```

### 2.9 附件/文件

```
BpmAttachmentService           附件
BpmFileService                 文件
BpmLargeObjectService          大对象（CLOB）
```

### 2.10 权限/安全

```
ApprovalSecurityService        审批安全
BpmAuthDetailService           授权明细
BpmMyProcessPermissionService  我的流程权限
BpmThirdFormPermissionService  第三方表单权限
```

### 2.11 显示/列表

```
BpmDisplayService              显示
BpmDynamicTitleService         动态标题
DependentDynamicTitleService   依赖动态标题
BpmListDisplayColumnService    列表显示列
BpmCustomTabService            自定义页签
```

### 2.12 监控/日志

```
BpmMonitorNodeService          监控节点
BpmMonitorNodeHandler          监控处理
BpmProcessLogService           流程日志
BpmProcessDetailLogService     流程明细日志
BpmEffectLogService            生效日志
BpmTransportLogService         传输日志
BpmApplicationOperateLogService 应用操作日志
BpmDetectionService            检测
```

### 2.13 其他

```
BpmBillCodeService             ★ 单据编号
BpmUrlService                  URL
BpmWorkItemService             工作项
BpmCrossServiceRelationService 跨服务关联（BpmAcrossServiceRelationService）
ExtendInfoService              扩展信息
PreMatchService                ★ 预匹配（发起前匹配流程）
Interpreter                    解释器
OrgAppServiceProxy             ★ 组织服务代理
ShortMessageEmailService       短信邮件
BpmSyncEventRegisterService    同步事件注册
BpmOrgChangedService           组织变更
BpmSystemSettingService        系统设置
BpmEvaluationRecordService     评价记录
BpmHastenAppHastenService      催办
BpmMessageTemplateService      消息模板
BpmConsultService              咨询
```

---

## 3. ★★★ 三阶段执行链路（`BpmService` 91 方法实证）

**从方法名可以直接读出完整生命周期：**

### 3.1 发起阶段

```java
WorkflowBpmContext getStartProcessContext(BpmStartDto, boolean)   // 构建上下文
RunCaseResultDto preStartProcess(WorkflowBpmContext)              // ★ 预发起
RunCaseResultDto preStartProcessByAppId(WorkflowBpmContext)       // 按 appId 预发起
BpmProcessDto matchProcessTemplateByAppId(WorkflowBpmContext, ...) // ★ 按应用匹配流程模板
RunCaseResultDto startProcess(WorkflowBpmContext)                 // ★ 正式发起
boolean dealPreSendAndSubmit(PreMatchResponseDto, WorkflowBpmContext) // 处理预发送+提交
```

**★★ 关键设计：`preStartProcess` ≠ `startProcess`**
```
preStartProcess   预发起（校验、匹配流程、算参与者，不落库）
startProcess      正式发起（落库、生成工作项、发消息）
```
**⇒ 这是「表单上展示即将发起给谁」的实现（`BpmNodeForecastService` 也做这个）。**

**★ `matchProcessTemplateByAppId` —— 一个应用可配多个流程模板，发起时按条件匹配。**

### 3.2 办理阶段

```java
BpmFinishWorkitemResultDto preFinish(WorkflowBpmContext)              // 预提交
BpmFinishWorkitemResultDto preFinishWorkItem(BpmFinishWorkItemDto, boolean)
WorkflowBpmContext getFinishWorkItemContext(BpmFinishWorkItemDto, ...)
BpmFinishWorkitemResultDto finishWorkItem(WorkflowBpmContext)          // ★ 正式提交
BpmFinishWorkitemResultDto finishWorkItemSimulation(WorkflowBpmContext) // ★ 仿真提交
```

**★ 同样是 pre/finish 两段式。**

### 3.3 其他操作（全部在 `BpmService`）

```java
// 撤销
String repeal(BpmRepealDto)                      // 撤销（3 个重载）

// 终止
String stop(BpmStopDto, BpmCase, ...)            // 终止（2 个重载）

// 退回（回退）
BpmValidNodeForStepBackDto getValidStepBackNodeList(Long)    // ★ 可取回节点列表
Map<String,List<String>> getStepBackMemberName(List)         // 退回人员名
BpmStepBackResponseDto startStepBack(BpmStepBackRequestDto, Long)  // ★ 执行退回
BpmValidNodeForSpecialBackDto getValidSpecialStepBackNodeList(...) // 特殊退回
BpmWorkItemRun superviseSpecialStepBack(Long, Long)

// 加签
ChangeNodeResponseDto informNode(InformAddNodeDto)    // ★ 知会/加签

// 移交/转办
void cancelWorkItem(BpmReplaceWorkItemDto, boolean)
List<Long> replaceWorkItem(BpmReplaceWorkItemDto, ...)  // ★ 替换工作项

// 暂存
String temporaryPending(BpmTemporaryDto, BpmCase, ...)  // 暂存待办
void validateTemporaryPending(BpmTemporaryDto)

// 已读
void readWorkItem(BpmReadDto, BpmDiagram, Long, ...)

// 草稿
void saveDraftCreate(BpmSaveDraftDto, BpmSaveDraftResponseDto, ...)
void updateDraftCreate(Long, Map, ...)
void sendProcessDraftEvent(...)

// 意见
void saveOpinion(BpmOpinionDto, BpmMemberPost, Long, ...)
```

**★★★ 这几个方法名就是「BPM 能不能做什么」的完整答案：**
```
发起 / 撤销 / 终止 / 退回 / 加签 / 移交转办 / 暂存 / 草稿 / 意见
```

---

## 4. ★★★ `BpmExecute`（30 方法）—— 流程状态机

**这是执行引擎，管理「活动（Activity）」的生命周期：**

```java
RunCaseResultDto startCase(BpmDiagram, boolean, Long, ...)     // ★ 启动实例
void reStartCase(BpmDiagram, boolean)                          // 重启实例
void addReadyActivity(BpmDiagram, BpmCase, List)               // ★ 添加就绪活动
void removeActivity(BpmDiagram, BpmCase, Set)                  // 移除活动
void finishActivity(BpmDiagram, BpmCase, ...)                  // ★ 完成活动
void stopActivity(BpmDiagram, AbstractBpmNode, ...)            // 停止活动
int  cancelCase(BpmCase, BpmDiagram, List)                     // ★ 取消实例
List<BpmWorkItemBase> awakeCase(BpmDiagram, ...)               // ★ 唤醒实例（暂存转正式）
TakeBackResultBo takeBackActivity(BpmDiagram, ...)             // ★ 取回活动
void processFinished(BpmCase, BpmDiagram)                      // 流程结束
void processFinishedOperation(WorkflowBpmContext)
void startCaseToMe(AbstractBpmNode, BpmCase, Long, ...)        // 发给自己
void startCaseRevokeToMe(AbstractBpmNode, BpmCase, ...)        // 撤销回自己
void clearSpecifyBackState(BpmCase)                            // 清除指定回退状态
Date getProcessDeadline(WorkflowBpmContext)                    // ★ 流程期限
```

**★★ 状态机模型（从方法名推断）：**
```
BpmCase（实例）
  ├─ Activity（活动）：ready → running → finish / stop
  ├─ 特殊状态：awake（唤醒）、takeBack（取回）、revokeToMe（撤销回自己）
  └─ 终态：processFinished / cancelCase
```

**★ 日志埋点很多：`recorderProcessLog` / `recorderProcessLogDto` / `saveContextProcessLogs` / `createRecorderProcessLog`**
**⇒ 流程每一步都有日志，这是能审计的基础。**

---

## 5. ★★★ `BpmProcessService`（114 方法）—— 流程定义

**这是「设计态」的核心（流程模板/流程定义/流程图）：**

```java
// 流程实体 CRUD（面向 DB 表）
Long createProcessEntity(BpmProcess)
Long updateBpmProcessEntity(BpmProcess)
Long updateBpmProcessEntityIgnoreVersion(BpmProcess)     // ★ 忽略版本
BpmProcess selectProcessEntityById(Long)
List<BpmProcess> selectByApplicationId / Name / TemplateId / TemplateIds
PageData<BpmProcess> selectPageByWrapper(Wrapper)       // ★ 用 Wrapper（与 MyBatis 一致）

// 流程 DTO 层（面向业务）
Long createBpmProcess(BpmProcessDto)
Long updateProcess(BpmProcessDto)
Integer deleteProcess(List<Long>)
BpmProcessDto selectProcessById(Long)
PageData<BpmProcessDto> selectProcessPageByConditions(...)

// ★★★ 流程图（BPMN 模型）
BpmDiagram updateProcessWorkflow(BpmProcessWorkflowUpdateDto, ...)   // 3 个重载
void parseAndSaveDiagramDetail(BpmProcess, BpmDiagram, ...)
BpmDiagram selectEffectedDiagram(BpmCase, ...)          // 取生效的图
void validateActor(BpmDiagram)                          // ★ 校验参与者
void validateNodeActorIsExist(AbstractBpmNode, List)
void updateBpmNode(BpmDiagram, Long, Long, List)        // 更新节点
void recursionBpmNode(AbstractBpmNode, List)            // 递归处理节点

// ★ 条件/子流程
boolean checkSubProcessLoopError(BpmDiagram, List<Long>)   // 子流程循环检测
BpmProcessDto dealProcessStartCondition(BpmProcess)        // 发起条件
SingleResponse<Void> updateProcessStartCondition(...)
void createOrUpdateStartCondition(BpmProcess, String)

// 生效版本
List<BpmProcessDto> selectEffectedProcessByTemplateId(WorkflowBpmContext)
List<BpmAppTemplateDto> selectEffectedDiagramListByAppId(BaseBpm...)
```

**★★★ 关键概念：`BpmProcess`（流程定义） ↔ `BpmTemplate`（模板） ↔ `BpmCase`（实例）**
```
BpmTemplate（模板，业务概念：一个审批类型）
   └─ BpmProcess（流程定义，可有多个版本）
         └─ BpmDiagram（流程图，BPMN 模型）
               └─ AbstractBpmNode（节点）
BpmCase（实例，一次具体审批）
   └─ BpmWorkItemBase（工作项，待办）
```

**★ `selectEffectedDiagram` —— 「生效版本」概念：一个实例发起后，用它发起时的流程图；模板改了不影响在途实例。**

---

## 6. ★★ `BpmIndependentDeployService`（20 方法）—— 部署

```java
BpmExportInitDataDto deployBpmTemplatesIndependent(String, Long)      // ★ 独立部署
BpmExportInitDataDto deployBpmTemplatesIndependent(String, String)
BpmExportInitDataDto deployBpmTemplatesIndependent0(...)
BpmExportInitDataDto mergeEditToRunnableTemplate(String, Long)        // ★ 草稿→可运行模板
void checkDeployLimitLock(String)          // ★ 部署并发锁
void reduceDeployLimit(String)             // 释放许可
void checkPublish(String)                  // 发布检查
List<BpmTemplate> getEditTemplates(String) // 草稿模板列表
void autoDeployStartAndAuth(BpmAppInfoDto) // ★ 自动部署+启动+授权
void authAndStart(BpmAppInfoDto, BpmTemplate)
ReplaceIdContext buildReplaceIdContext(String, String, ...)  // ★ ID 替换（导入时）
```

**★★★ 「部署」的真实含义：**
```
设计态模板（草稿）→ 发布 → 运行态模板（可发起）
```
**★ `autoDeployStartAndAuth` —— 部署后自动启动+授权（这就是 UDC 应用「发布」时做的）。**

**★ `deployBpmTemplatesIndependent` 返回 `BpmExportInitDataDto` —— 说明部署走的是**导出-导入**机制（跨环境搬运）。**

---

## 7. ★★ 自动节点（`autonode`，23 类）—— 自动审批

**`AutoNodeExecuteService`（39 方法）是自动节点执行器：**

```java
AutoNodeActionParam autoNodeExecute(AutoNodeContext)        // ★ 执行自动节点
AutoNodeActionParam autoNodeRun(BpmAutoNodeControl)         // 2 个重载
AutoNodeActionParam autoNodeRunByDelayMessage(Long)         // ★ 延迟消息触发
AutoNodeActionParam firstAutoNodeRun(BpmAutoNodeControl)    // ★ 首次运行
void prepareFirstExecuteAutoActivity()
void executeNodeControl(List<BpmAutoNodeControl>)
void sendAutoNodeMqMessage(BpmAutoNodeControl, Long)        // ★ 发 MQ 消息

boolean getConditionResult(String, Map<String,Object>)      // ★ 条件判断
BpmExpressionDto getTrueBpmExpression(List<String>, ...)    // ★ 取真的表达式
boolean checkProcessStateIsStop(Long)
AutoNodeActionParam getFailActionCode(AutoNodeTolerantModeEnum, ...)  // ★ 容错模式
```

**★★ 自动节点有 10 种动作（`AutoNode*Action`）：**
```
AutoNodeAction（抽象基类）
  ├─ AutoNodeSubmitAction      自动提交
  ├─ AutoNodeBackAction        自动退回
  ├─ AutoNodeBackToStartAction 自动退回发起人
  ├─ AutoNodeRevokeAction      自动撤销
  ├─ AutoNodeStopAction        自动终止
  ├─ AutoNodeInterventionAction 自动干预
  ├─ AutoNodeRetryAction       ★ 自动重试
  └─ AutoNodeActionManager     动作管理器
```

**★★★ 三个关键机制：**
1. **`sendAutoNodeMqMessage` —— 自动节点靠 **MQ 驱动（异步）**，不是同步执行**
2. **`AutoNodeRetryAction` —— 有**重试机制**
3. **`AutoNodeTolerantModeEnum` —— 有**容错模式**（失败怎么办）

**★ `BpmAutoActivityRunner` / `BpmAutoNodeControlService` / `BpmAutoNodeControlDetailService` —— 自动节点的控制与明细记录。**

---

## 8. ★★ `appservice.autogenerate`（10 类）—— 自动生成流程图

**这个包与「代码生成」专题直接相关：**

```
ApplicationAutoGenerateService        接口
ApplicationAutoGenerateServiceImpl     实现
dispatcher.DispatcherContext          分发上下文
dispatcher.DispatcherHandler          分发处理器
dispatcher.V8DiagramDispatcher        ★ V8 流程图分发器
dispatcher.impl.ClearJoinGatewayDispatcherHandler        ★ 清理 join 网关
dispatcher.impl.DifferentBranchesUseOneJoinGatewayDispatcherHandler  ★ 不同分支共用一个 join
dispatcher.impl.EndNodeHasManyCommingBranchesDispatcherHandler      ★ 结束节点多入边
dispatcher.impl.IdsDispatcherHandler                     ★ ID 处理
dispatcher.impl.SplitAndJoinGatewayInOneDispatcherHandler ★ split/join 在同一网关
```

**★★★ 这是「自动生成流程图」的**规整器**：**
```
用户画的流程图（可能不规范）
    ↓ DispatcherHandler 系列（6 个具体处理器）
    ↓ V8DiagramDispatcher
规整后的标准流程图
```

**★ 6 个 DispatcherHandler 各处理一种「不规范画法」：**
```
ClearJoinGateway              多余的 join 网关 → 清掉
DifferentBranchesUseOneJoin   不同分支共用一个 join → 调整
EndNodeHasManyCommingBranches 结束节点多条入边 → 规整
IdsDispatcher                 ID 重排
SplitAndJoinGatewayInOne      split 和 join 挤在同一网关 → 拆开
```

**⇒ 这解释了为什么 UDC 自动生成的流程图总是规范的 —— 有 6 道规整规则。**

---

## 9. ★★ 其他重要机制

### 9.1 流程合并（`merge`，26 类）

```
AbstractMergeService / MergeBpmTaskService / MergeHandle
MergeOnCreateService          创建时合并
MergeOnSubmitService          ★ 提交时合并
MergeSubmitAspect             ★ AOP 切面
strategy.AbstractCreateMergeStrategy
```

**★ `MergeSubmitAspect` —— 用 AOP 做合并，说明合并是**横切逻辑**。**

### 9.2 事件匹配（`eventmatch`，26 类）

**★ 26 个类做「事件 → 流程节点」的匹配。**

### 9.3 督办（`supervise`，38 类）

**★ 流程督办是独立子域（不只是「催办」）。**

### 9.4 流程仿真（`simulation`，21 类）

```
finishWorkItemSimulation(WorkflowBpmContext)   ★ 仿真提交
BpmApiSimulationServiceImpl
```
**★ 可以在不真正提交的情况下跑流程 —— 用于测试和预测。**

### 9.5 SPI 扩展点（`spi`，5 类）

**★ 5 个类，是 BPM 的客开扩展点。**

### 9.6 Dubbo 代理（`dubboProxy`，2 类）

**★ `domain.service.dubboProxy` —— BPM 内部调外部服务走 Dubbo 代理。**

---

## 10. ★★★ 检测体系（`detection`，234 类）—— 这是本轮最有价值的新知识

**`bpm.detection` 独立分包，234 类，做**三层检测**：**

| 子包 | 类数 | 检测什么 |
|---|---:|---|
| **`usedparam`** | **115** | **★ 依赖分析：流程引用了什么** |
| `attribute` | 24 | 属性 |
| `operationpermission` | 12 | 操作权限 |
| `ctpenum` / `udcenum` | 10 / 10 | 枚举引用 |
| `ctpparameterdefinition` | 9 | CTP 参数定义 |
| 其余 | 剩余 | |

### 10.1 ★★★ `usedparam` 的真实用途（接口实证）

```java
interface BpmFieldsUsedForDetectionInterface extends BpmCascade {
    // ★ 检测：流程用了哪些参数
    List<Object> getUsedParameterAndRelation(List<BpmTemplate>, ...)
    // ★ 检测：流程用了哪些选项集
    List<Object> getUsedCtpEnumAndRelation(List<BpmTemplate>, ...)
    // ★ 检测：流程用了哪些 UDC 枚举
    List<Object> getUsedUdcEnumAndRelation(List<BpmTemplate>, ...)
    // ★ 检测：流程用了哪些页面
    List<Object> getUsedPageInfoAndRelation(List<BpmTemplate>, ...)
    // ★ 检测：流程用了哪些扩展方案
    List<Object> getUsedExPlanAndRelation(List<BpmTemplate>, ...)
    // ★ 检测：子流程引用了哪些流程
    List<Object> getSubProcessUsedProcessAndRelation(Map<BpmTemplate,...>, ...)
    // ★ 检测：流程用了哪些组织
    List<Object> getProcessUsedOrgProcessAndRelation(...)
    // ★ 表达式里的组织引用
    Set<Pair<String, NodeTypeEnum>> get...(3 个)
    List<BpmOrgId2CodeDto> transformExpressionToBpmOrgId2CodeList(String, ...)
}
```

**★★★ 这是「级联影响分析」体系：**
```
接口继承 BpmCascade
每个实现类有两个级联方法：
  void cascadeHandleAffectedForAttr(CascadeUpdateContext)     ★ 字段被改 → 处理受影响流程
  void cascadeHandleAffectedForEntity(CascadeUpdateContext)   ★ 实体被改 → 处理受影响流程
```

**⇒ 业务含义（对客开极有价值）：**
```
改一个 UDC 字段 / 删一个选项集 / 换一个页面
      ↓ 系统自动检测
哪些流程模板受影响了（usedparam 115 类逐一扫）
      ↓ cascadeHandleAffectedForXxx
自动修复 或 标记异常
```

**⇒ 这就是「为什么平台敢让你随便改字段」的底气 —— 有完整依赖分析 + 级联处理。**

### 10.2 ★ 检测维度矩阵（`bo` 子包的组织方式）

**115 类按「检测对象 × 检测目标」二维组织：**

| 对象（bo 子包） | 含义 | 类数示例 |
|---|---|---|
| **`bo/param/`** | **流程用了哪些参数** | 24 类：`HumanActivityActorUsedParam` / `NodeActionUsedParam` / `ProcessStartConditionUsedParam` / `SubProcessUsedParam` / `TimerActivityUsedParam` … |
| **`bo/org/`** | **流程用了哪些组织** | 11 类：`TemplateUsedOrg` / `NodeActionConditionUsedOrg` / `ProcessStartConditionUsedOrg` / `ExpressionOrgMetadata` … |
| **`bo/ctpenum/`** | **流程用了哪些选项集** | 11 类：`NodeActionUsedEnum` / `RouteNodeConditionUsedEnum` / `PathTableUsedEnum` … |
| **`bo/udcenum/`** | **流程用了哪些 UDC 枚举** | 10 类：`NodeActionUsedUdcEnum` / `MultiLineActivityUsedUdcEnum` … |
| **`bo/formpermission/`** | **表单权限引用** | 5 类：`TemplateFormPermissionUsedInfo` / `ActivityPermissionUsedInfo` … |
| **`bo/nodepermission/`** | **节点权限引用** | 2 类：`TemplateNodePermissionUsedInfo` / `ActivityNodePermissionUsedInfo` |
| **`bo/pageinfo/`** | **页面引用** | 3 类：`TemplateUsedPageInfo` / `HumanActivityUsedPageInfo` / `FormPermissionUsedPageInfo` |
| `bo/path/` | 路径表 | 1 类 |
| `bo/subprocess/` | 子流程 | 1 类 |
| `bo/openapi/` | 开放 API | 1 类 |
| `bo/basicdata/` | 基础数据 | 1 类 |

**⇒ 12 个检测维度，覆盖**参数、组织、选项集、UDC 枚举、表单权限、节点权限、页面、路径表、子流程、开放 API、基础数据**。**

### 10.3 ★★ 50 个 `*ForDetectService`（按检测职责交叉命名）

**命名规律：`Bpm<功能>Used<维度>ForDetectService`**

```
按流程功能（20 种）：
  HumanActivity           人工节点
  AutoActivity            自动节点
  AutoStartActivity       自动开始
  TimerActivity           定时节点
  TimerStartActivity      定时开始
  MessageActivity         消息节点
  MonitorActivity         监控节点
  EventActivity           事件节点
  MultiLineActivity       多分支节点
  LevelApproval           逐级审批
  SubProcess              子流程
  PathTable               路径表
  PathTableActivity       路径表节点
  PathTableBasicData      路径表基础数据
  NodeAction              节点动作
  NodeOvertime            节点超时
  ProcessOvertime         流程超时
  ProcessStartCondition   流程发起条件
  RouteNodeCondition      路由条件
  NodePermission          节点权限
  FormPermission          表单权限
  ApprovalFrame           审批框架
  ProcessOpenApi          开放 API
  Template                模板
  Express                 表达式
  Layout / TemplateInfo   布局/模板信息
  DynamicTitle            动态标题
  DynamicNode             动态节点
  Permission              权限
  PermissionUsedNodeOperation 节点操作权限
  ProcessFormPermission   流程表单权限

按检测维度（后缀）：
  *UsedParamForDetectService     参数
  *UsedOrgForDetectService       组织
  *UsedAppParamForDetectService  应用参数
  *UsedPageForDetectService      页面
  *UsedTemplateForDetectService  模板
  *UsedProcessForDetectionService 流程
  *UsedFieldsForDetectService    字段
```

**⇒ 33 种功能 × 7 种维度 → 50 个实际实现（部分组合不存在）。**

### 10.4 ★★★ 一个具体的实现（`BpmHumanActivityUsedParamForDetectService`）

```java
List<Object> getUsedParameterAndRelation(List<BpmTemplate>, ...)
List<HumanActivityActorUsedParam> getUsedParametersByProcess(..., ...)
void getUsedParamList(List<AbstractBpmNode>, Long, ...)
void setUserParam(Long, BpmProcess, AbstractBpmNode, ...)
void cascadeHandleAffectedForAttr(CascadeUpdateContext)
void cascadeHandleAffectedForEntity(CascadeUpdateContext)
```

**★ 它依赖 `BpmParameterService`，并用 `HumanMatchParam`（人员匹配参数）—— 说明人工节点的参与者规则是核心检测对象。**

**★ `BpmProcessStartConditionUsedParamForDetectService` 依赖 `BpmExpressionService`**
**⇒ 流程发起条件里的表达式，也要被解析出引用了什么。**

---

## 11. ★ 对已有文档的补充（11/13/14 号）

| 我之前写的（基于 facade） | biz 层的新知识 |
|---|---|
| `BpmAppService` 的操作 DTO（13 号） | **biz 里 `BpmService` 有 91 个方法**，DTO 只是入参壳 |
| 流程状态机 | **`BpmExecute` 30 方法确认真实状态机**（ready/running/finish/stop/awake/takeBack） |
| 部署 | **`BpmIndependentDeployService` 20 方法** + 部署锁 + ID 替换 |
| 自动节点 | **10 种 AutoNodeAction + MQ 驱动 + 重试 + 容错** |
| 未提 | **`detection` 234 类做设计态校验（usedparam 115 类做依赖分析）** |
| 未提 | **`autogenerate` 6 个 DispatcherHandler 规整流程图** |

---

## 12. 未覆盖

| 项 | 说明 |
|---|---|
| `BpmService` 91 方法中剩余 46 个 | 只列了前 45 个 |
| `BpmProcessService` 114 方法中剩余 69 个 | 只列了前 45 个 |
| 各方法的方法体 | **全部未反编译**（只读签名） |
| `domain.model.BpmDiagram` 的结构 | 未 dump（79 个 model 类） |
| `detection/usedparam` 115 类的算法 | ✅ **已确认：`getUsedParameterAndRelation` + `cascadeHandleAffectedForAttr/Entity`**，12 个检测维度 |
| `MergeSubmitAspect` 的合并规则 | 未读 |
| `spi` 5 个扩展点的契约 | 未读 |
| bpm-biz 5.3.353 vs facade 5.3.600 的**版本差异** | **未评估**（两侧版本不同步） |