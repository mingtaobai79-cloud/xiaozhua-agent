# BPM 加签：识别、监听、消息与可读字段（证据审计）

> Evidence: FACT ✅（bpm-facade-5.3.374 CFR 反编译 / 前端 chunk 静态提取 / boot-starter-opinion i18n / UDC 客户 jar 反编译）
> 反编译产物：`docs/audit/modules/decompiled/bpm-addsign/`
> 原始报告：`docs/audit/evidence/addsign-report.txt`、`addsign-enums.txt`、`addsign-udc-event.txt`
> 扫描工具：`tools/core/scan_addsign_keywords.py`（**已移入 `_attic_pending/one-off/unsorted/scan_addsign_keywords.py`**，仓库内已无此路径）、`scan_addsign_v2.py`、`decompile_bpm_addsign.py`、`decompile_bpm_api_scan.py`、`decompile_addsign_enums.py`、`decompile_addsign_chain.py`、`decompile_udc_addsign_event.py`

## 一、加签怎么识别（四层标识，都是 FACT）

| 层 | 标识 | 来源 |
|----|------|------|
| 操作码（前端/权限） | `PROCESS_NODE_ADD`（加签）、`PROCESS_GIVE`（会签）、`PROCESS_NODE_DEL`（减签）、`PROCESS_NOTICE`（知会） | 前端 chunk 流程操作码枚举，共 31 个码 |
| 操作码（后端意见/记录） | `NODE_ADD` → i18n `bpm.operation.message.NODE_ADD=加签` | `boot-starter-opinion-5.3.260` `i18n/opinion/other_zh_CN.properties` |
| 流程修改类型枚举 | `ChangeTypeEnum`（@EnumInfo "流程修改类型"）`AddNode(0)`=加签、`AddInform(1)`=知会、`DeleteNode(3)`=减签、`Countersign(9)`=会签、`CountersignInnerAdd(12)`、`PostApprovalAddNode(13)`、`ADD_INNER(14)`、`LOOP(10)` | `com.seeyon.bpm.enums.ChangeTypeEnum` |
| 操作类型枚举 | `OperateTypeEnum.OPERATE_TYPE_ADD(1)`=加签、`OPERATE_TYPE_JOINTLY(2)`=会签、`OPERATE_TYPE_NOTICE(4)`=知会 | `com.seeyon.bpm.enums.OperateTypeEnum` |
| 节点权限响应 | `BpmNodePermissionResponseDto.operationCode`，@DtoAttribute 示例值就是 `"NODE_ADD"` | `com.seeyon.bpm.dto.BpmNodePermissionResponseDto` |

## 二、API 落点（FACT：bpm-facade 接口签名）

```java
// com.seeyon.bpm.api.common.BpmAppService
SingleResponse<ChangeNodeResponseDto> addNode(SingleRequest<SimpleChangeProcessRequestDto>);        // 加签
SingleResponse<ChangeNodeResponseDto> counterSignNode(SingleRequest<SimpleChangeProcessRequestDto>); // 会签
```

入参 `SimpleChangeProcessRequestDto`（@DtoInfo "加签减签"）：
`processId` / `processJson` / `saveProcess` / `currentActivityId`(@NotNull) / `workItemId` / **`needInsertLog`(默认 false)** / `simpleChangeNodeParameterDto`（加签/会签具体参数）

另有无 UDC 版本：`ChangeNodeRequestDto`（@DtoInfo "加签、减签请求参数对象"）
`changeTypeEnum` / `addNodeParameterDto` / `deletedNodeIds`（减签用）/ `replaceNodeDto` / `modifyNodeTermParameterDtos` / `currentOwnerId` / `needInsertLog` / `formDataMap`

## 三、怎么监听（三条路，优先级从高到低）

### 1. 流程事件里的字段（最直接，FACT 字段存在）
`com.seeyon.bpm.dto.message.event.BpmBaseEvent`（所有 BPM 事件的基类）带：

```java
@DtoAttribute("当前节点是加签，知会，会签出来")
private ChangeTypeEnum currentActivityChangeType;
```

→ 30+ 个事件子类（BpmStartEvent / BpmSubmitEvent / BpmFinishEvent / BpmStepbackEvent / BpmCancelEvent / BpmTransferEvent / BpmActivityFinishEvent / BpmTemporaryPendingEvent …）都继承它。
**监听流程事件后判断 `currentActivityChangeType == ChangeTypeEnum.AddNode(0)` 即可知道"当前节点是加签出来的"。**

### 2. SPI 同步拦截（FACT：SPI 契约）
`BpmOperationSpi.checkNodePermission(BpmCheckNodePermissionReq{caseId, affairId, permissionId, commentDto, operationCode})`
→ `operationCode` 取值即上面操作码集合（含 `NODE_ADD`），可在操作发起时同步校验/拦截。
配合 `BpmDetailViewSpi.mergeNodePermission` 做权限合并。scope=`bpm`，重启 `bpm`。

### 3. UDC 低代码侧（FACT：客户 jar 反编译）
`ApproveFeatureService`（udc-starter-runtime）从 `billExtraMap.get("changeNodeRequestDtos")` 取加签/减签 → `bpmSendUdcDto.setChangeNodeRequestDtos(List<ChangeNodeRequestDto>)`；`BpmSendUdcDto` 该字段 @DtoAttribute="加签相关请求参数，没有做加签相关操作，传递NULL就可以"。
**即：UDC 审批发起时可携带加签/减签参数进入 BPM。**
客户 UDC 应用（znxmglpt，50 个版本）已生成"加签事件"消息类：
`JiaqianshijianMessage` @MessageInfo("加签事件") topic=`UDC_ZNXMGLPT3289082814923688017_MQ`，customs: `from=udc`、`source=MICRO_FLOW`、`name=jiaqianshijian`、`openApiCustom=true`，`extends BaseMessage<Jiaqianshijian>`。
→ UDC 微流程存在"加签事件"触发器/消息，且对 OpenApi 开放。

## 四、源代码发送消息没有？（结论：BPM 侧不发专属消息）

`com.seeyon.bpm.dto.message.BpmMqDataType`（@EnumInfo "消息类型"，appName=bpm）共 39 个类型：
TIMER_ACTIVIY_DELAY_MESSAGE(0)、TIMER_START_DELAY_MESSAGE(1)、PROCESS_OVERTIME(2)、ACTIVITY_OVERTIME(3)、DETECTION(4)、PROCESS_STARTED(10)、PROCESS_FINISHED(11)、PROCESS_CANCELED(12)、PROCESS_STOPPED(13)、CUSTOM_NODE_EVENT(14)、TEMPLATE_SYNC(15)、STEP_BACK(16)、PROCESS_SUBMIT(17)、APPROVAL_RESULT(18)、BUSINESS_ACTIVITY_SEND(19)、BUSINESS_ACTIVITY_RECEIVE(20)、RETRIEVE(21)、TRANSFER(22)、CONSULT(23)、TEMPORARY_PENDING(24)、SUPERVISE_CHANGE_PROCESS(25)、INFORM(26)、HASTEN(27)、VIP_SUPERVISE_CREATE(28)、VIP_SUPERVISE_CANCEL(29)、PROCESS_RELIVE(30)、PROCESS_DRAFT(31)、PROCESS_PAUSE(32)、PROCESS_CANCEL_PAUSE(33)、ABNORMAL_REPORT(34)、PROCESS_DELETE(35)、MULTI_WRITE(36)、CHANGE_OPINION(37)、CONSULTOR_SETTING(38)

**没有 ADD_NODE / NODE_ADD。** 即：加签动作本身不产生独立的 BPM MQ 消息类型；加签的"可观测痕迹"是 ① 后续流程事件带 `currentActivityChangeType` ② 流程日志 ③ 意见/操作记录。

## 五、哪些字段能读到（可直接读的落点）

| 落点 | 字段/常量 | 说明 |
|------|-----------|------|
| 流程事件 | `BpmBaseEvent.currentActivityChangeType` | 加签出来的节点，值为 `ChangeTypeEnum.AddNode(0)` |
| 流程日志（操作常量） | `LogActionDetailOperationConstants.ADD_NODE = "bpm.processLog.action.operation.addNode#"` | 加签写日志；`DELETE_NODE`=减签、`ADD_INFORM`=知会、`ASSIGN`/`COUNTERSIGN`=`...assign#` |
| 日志开关 | `SimpleChangeProcessRequestDto.needInsertLog`（默认 false）、`ChangeNodeRequestDto.needInsertLog` | 调用方决定是否插入变更日志 |
| 变更日志 DTO | `ChangeNodeLogDto`（@DtoInfo "加签、减签等改变流程的日志对象"）：`changeTypeEnum`、`handlerId`、`processId`、`nodeAndPolicyNames`、`nodeNames`、`newNodeNames` | 加签/减签的历史记录 |
| 意见/操作记录 | 操作码 `NODE_ADD`，i18n 标签 `bpm.operation.message.NODE_ADD=加签` | 意见表按操作码可筛出加签 |
| 前端消息条件 | 流程消息设置 `msgCondition.ADD_NODE="加签"`（同族：`DELETE_NODE`=减签、`ADD_INFORM`=知会、`RETRIEVE`=取回） | 流程消息规则可按"加签"触发通知 |

## 六、假阳性甄别（搜"加签/sign"时别被带偏）

| 命中 | 实际含义 | 结论 |
|------|----------|------|
| `boot-starter-web` `AccessAuditLg.dataSign`（`data_Sign`，COMMENT '加签数据'） | **数字签名**（访问审计日志里的数据签名），非流程加签 | 假阳性，排除 |
| `cip-capability-common` `SignConfigDto` / `SignConfigsDto` | 电子签/能力通道的签名配置 | 假阳性，排除 |
| `ctp-user-facade` `CtpDataSignSetChangeDto` | 数据签名设置变更 | 假阳性，排除 |
| `boot-core` `PDDocument`（含 addSign） | PDF 文档签名（PDFBox） | 假阳性，排除 |
| 客户 UDC 应用 `Jiaqianshijian` / `JiaqianshijianMessage`（127 个 artifact 命中） | **真** 加签事件微流程消息（`JiaqianshijianMessage` @MessageInfo("加签事件")，source=MICRO_FLOW） | 真命中 |

流程加签的真命中只有三处 artifact：`bpm-facade`（DTO/枚举/事件基类）、`udc-starter-runtime`（ApproveFeatureService 桥）、`boot-starter-opinion`（i18n 操作码标签）。

## 七、通道确认：BpmBaseEvent 是 payload，不是发送体

**继承链（FACT，CFR 反编译）**
```
BpmEventActivityReadyEvent（@DtoInfo 节点激活事件）
  └─ extends BpmActivityEventBase（@DtoInfo 节点事件基类）
       └─ extends BpmBaseEvent（@DtoInfo bpm事件触发消息；声明 currentActivityChangeType）
            └─ extends BpmMqData（@DtoInfo bpm消息基类；字段 BpmMqDataType dataType，示例 PROCESS_STARTED）
                 └─ extends BaseDynamicAppDto
```

**发送体在另一套包里**：`com/seeyon/bpm/dto/message/msg/**` 48 个信封类（另 2 个在 `overtime` 包），
统一 `@MessageInfo(topic="BPM", value="<中文名>", openApi=@OpenApi)`，且绝大多数
`extends BaseMessage<BpmXxxEvent>` —— **把 Event 当泛型 payload 装进信封再发 MQ**。

信封结构（`boot-core` `com.seeyon.boot.mq`）：
```java
public abstract class BaseMessage<T> { private T data; private Integer partition; }
public abstract class DelayBaseMessage<T> extends BaseMessage<T> { private Long executeTime; }  // 延迟类信封
@MessageInfo：value() 中文名、topic() 必填、sort()、openApi()、customs()
```

**结论**：不是 Spring in-JVM 事件，是 **MQ 消息（topic=`BPM`）**，对 OpenApi 开放可订阅；
`BpmBaseEvent` 及 31 个 `event` 包子类只是消息内容（93 个消息类里仅 `BpmBaseEvent` 自己声明该字段，
其余全部靠继承 → 任一事件 payload 都带 `currentActivityChangeType`）。

**加签落到哪个信封**：42 个信封中**没有加签专属消息**（无 addNode/加签 value）。加签产生新节点 →
走既有信封，最贴的是 `BpmEventActivityReadyMessage`（"节点激活消息"，payload `BpmEventActivityReadyEvent`，
继承链带 `currentActivityChangeType`）。同理可用：事项结束/提交（`BpmSubmitEventMessage`）、
意见修改（`BpmChangeOpinionMessage`）、督办（`BpmSuperviseChangeProcessMessage`）。

BPM 信封清单（topic=BPM，OpenApi 开放的 33 个）与延迟类（DelayBaseMessage，不开放）全文见
`docs/audit/evidence/bpm-mq-envelopes.txt`。

## 八、未验证 / 待 LIVE 确认（不得当结论用）

1. `currentActivityChangeType` 在真实加签流程里是否被实际填充（字段存在是 FACT，填充行为需跑一条带加签的流程抓事件验证）。
2. `addNode` / `counterSignNode` 的 REST 路由与 Controller（实现在 bpm 服务本体 jar，本地 Maven 仓库无该 artifact）。
3. UDC "加签事件"在低代码设计器里的触发器入口名与配置方式（客户 jar 已生成消息类，平台侧触发器定义未取到）。
4. 流程日志/意见的物理表名与字段（日志 DTO 已确认，落库表结构需连环境核对）。
