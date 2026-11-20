## 概念对照（bpm 的名词和中文业务词不是一一对应）

| 平台术语 | 中文业务含义 | 关键 id |
|---|---|---|
| **template**（模板） | 流程**设计态**：流程图、节点、权限配置 | `templateId` |
| **case**（案件） | 流程**实例**（一次发起 = 一个 case） | `caseId` |
| **activity**（节点实例） | case 里某个节点的一次运行记录 | `activityId` |
| **workItem**（待办项） | 某节点某人的一条待办 | `workItemId` |
| **opinion**（意见） | 办理意见 / 表单批注 | `opinionId` |
| **processLog** | 流程日志（流转轨迹） | — |
| **publish**（发布） | 把设计态模板推到运行态 | — |

**最容易搞混的两个**：
- `send`（发起，产生 case）vs `saveDraft`（存草稿，不产生 case）
- `repeal`（撤销，发起人收回）vs `takeBack`（取回，办理人收回自己刚提交的）

## 三条入口，选错就白改

```
我要从自己的扩展代码发起流程
  → BpmUdcApiService.sendForUdc / triggerFlowForUdc     ★ UDC 专用入口

我要从平台内部/初始化发起
  → BpmAppService.send

我只想知道某个表单记录对应哪个流程
  → BpmCaseAppService.selectBpmCaseByFormRecordId
```

**`BpmUdcApiService` 和 `BpmAppService` 的区别（这是关键）**：

| | `BpmAppService.send` | `BpmUdcApiService.sendForUdc` |
|---|---|---|
| 入参 | `BpmSendDto`（平台内部结构） | `BpmSendUdcDto`（UDC 结构，字段更少） |
| 返回值 | `BpmSendResultDto` | `BpmApiSendApiResponseDto` |
| 权限 | 走平台用户上下文 | 走 UDC 应用上下文 |
| 用途 | 标品内部发起 | **扩展代码 / 微流程节点 / 数据流生单** |

**UDC 生成的代码引用流程，只认后者。**

## 典型调用链

### 链 1：UDC 扩展发起一条流程

```java
@Autowired
private com.seeyon.bpm.api.udc.BpmUdcApiService bpmUdc;

// ① 拿到模板（按根实体名找，不要写死 templateId）
//    根实体名 = UDC 实体的全名
SingleResponse<BpmApiSendApiResponseDto> resp = bpmUdc.sendForUdc(
        SingleRequest.from(bpmSendUdcDto));

// ② dto 里必须有的（按 BpmSendUdcDto 字段）：模板、表单记录 id、标题、发起人
// ③ 返回里带 caseId —— 后续查流程状态全靠它
```

### 链 2：批量触发（数据流生单 / 微流程节点）

```java
// 列表入参：一次传多条，每条一个流程
ListResponse<BpmTriggerFlowUdcResponseDto> rs = bpmUdc.triggerFlowForUdc(
        SingleRequest.from(List.of(req1, req2, req3)));

// 数据量大（>1000）改异步，避免超时
bpmUdc.asyncTriggerFlowForUdc(SingleRequest.from(asyncReq));
```

### 链 3：办完流程后回写业务表

```java
@Autowired
private com.seeyon.bpm.api.common.BpmCaseAppService caseService;

// 已知表单记录 id → 找 caseId
SingleResponse<BpmCaseDto> c = caseService.selectBpmCaseByFormRecordId(
        SingleRequest.from(searchDto));

// 看流程跑到哪了
ListResponse<BpmActivityRunDto> acts = activityService.selectAllByCaseId(
        SingleRequest.from(c.getData().getId()));
```

### 链 4：在节点扩展里拿上下文

```java
// 节点扩展的入参里通常带 BpmSupportOperation
Long caseId     = op.getCaseId();
Long activityId = op.getActivityId();
Long templateId = op.getTemplateId();
String recordId = op.getFormRecordId();
String appName  = op.getApplicationName();
Long currentUser = op.getCurrentUserId();

// 往后续节点传值
op.setParameter("approveLevel", 3);
```

## UDC 和 bpm 的接口边界（谁能调谁）

```
UDC 扩展代码
  ├── 可调 BpmUdcApiService（★专用，10 个方法）
  ├── 可调 BpmCaseAppService（只读查实例）
  ├── 可调 BpmApiFormPermissionAppService / BpmApiNodePermissionAppService（读权限配置）
  └── 不应直接调 BpmAppService（那是标品内部入口，上下文不匹配）

bpm 内部
  └── 走 BpmAppService + BpmSupportOperation（节点上下文）
```

## 落表（流程侧）

流程数据落在 bpm 域自己的表，**不在 UDC 实体表里**。UDC 侧只需要保存 `caseId`。

⚠️ 具体表名 `UNVERIFIED`（字节码索引不含 SQL）。取证：反编译 `bpm-biz` 找 mapper，
或在 test2 库查 `information_schema.tables` 里 `%_bpm_%`。