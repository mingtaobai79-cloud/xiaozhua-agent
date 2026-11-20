# BPM 流程域（bpm-facade）能力清单

> 来源：`bpm-facade-5.3.374.jar` CFR 反编译（533 类 / 40 接口）
> ⚠️ **版本核对（2026-11-18）**：官方清单 **5.3.600**，本机只有 5.3.374（旧）。契约主体应稳定，但**新增方法/字段未覆盖**。
> 等级：`VERIFIED_STATIC_SOURCE`

---

## 1. 规模与结构

```
533 个类 / 40 个接口 / 5,893 个方法
包前缀：com.seeyon.bpm
```

---

## 2. ★★★ `BpmAppService`（26 方法）—— 流程操作总入口

⚠️ **统计修正**：先前文档写 23，实测 **26**（8 个 `public` 声明 + 18 个 `default`）。
原因：初版正则只匹配带 `default` 的方法，漏掉普通 `public` 声明。详见 statistics-registry §11.3。

**包：** `com.seeyon.bpm.api.common.BpmAppService`

**这是「单据流转」的唯一入口，全部方法都接收 `SingleRequest<T>` 返回 `*Response<R>`。**

### 2.1 单据生命周期

| 方法 | 请求 DTO | 响应 DTO | 作用 |
|---|---|---|---|
| **`send`** | `BpmSendDto` | `BpmSendResultDto` | **发起流程（新建单据并起流程）** |
| **`saveDraft`** | `BpmSaveDraftDto` | `BpmSaveDraftResultDto` | **保存草稿** |
| **`submit`** | `BpmSubmitDto` | `BpmSubmitResultDto` | **提交（草稿→审批中）** |
| **`stepBack`** | `BpmStepBackDto` | `CommonResultDto` | **退回（退回到指定节点）** |
| **`repeal`** | `BpmRepealDto` | `CommonResultDto` | **撤销（发起人撤销）** |
| **`stop`** | `BpmStopDto` | `CommonResultDto` | **终止流程** |
| **`takeBack`** | `BpmTakeBackDto` | `CommonResultDto` | **取回（办理人取回到自己）** |
| `deleteDraft` | `Long` | `Void` | 删除草稿 |
| `deleteDraftAffair` | `DeleteDraftReqDto` | `Void` | 删除草稿+事项 |

**⇒ 7 个核心动作：`send` / `saveDraft` / `submit` / `stepBack` / `repeal` / `stop` / `takeBack`**

### 2.2 办理人变更

| 方法 | 请求 DTO | 作用 |
|---|---|---|
| **`replace`** | `BpmReplaceDto` | **换人（单人）** |
| **`multipleReplace`** | `BpmMultipleReplaceDto` | **换人（批量）** |
| **`addExecuteMember`** | `BpmAddExecuteUserDto` | **加签** |
| `counterSignNode` | `SimpleChangeProcessRequestDto` | **会签节点** |
| `addNode` | `SimpleChangeProcessRequestDto` | **加节点（流程中插入）** |

### 2.3 暂停 / 监督

| 方法 | 请求 DTO | 作用 |
|---|---|---|
| **`pause`** | `BpmPauseDto` | **暂停流程** |
| **`cancelPause`** | `BpmPauseDto` | **恢复流程** |
| `superviseRelive` | `BpmReliveDto` | 督办解除 |
| `superviseReliveFull` | `BpmReliveFullDto` | 督办解除（完整） |
| `monitorNodeRun` | `BpmMonitorRunDto` | **监控节点运行** |
| `hasten` | `BpmHastenDto` | **催办** |

### 2.4 其他

| 方法 | 请求 DTO | 作用 |
|---|---|---|
| `consult` | `BpmConsultDto` | **咨询（征求意见）** |
| `inform` | `BpmInformDto` | **知会** |
| `cancelItems` | `BpmCancelItemDto` | 取消事项 |
| **`batchDeal`** | `BpmBatchReqDto` | **批量处理** |
| **`selectFullCaseInfo`** | `BpmCaseFullInfoSearch` | **查完整单据信息**（含流程状态） |
| `check` | `SecurityCheckDto` | 安全检查 |

---

## 3. 其他核心接口（按方法数）

| 接口 | 方法数 | 职责 |
|---|---|---|
| **`BpmTemplateAppService`** | **55** | **流程模板管理（最多）** |
| `BpmAppService` | 23 | **流程操作总入口** |
| **`BpmCaseAppService`** | **23** | **流程实例查询** |
| `BpmApiFormPermissionAppService` | 18 | **表单权限** |
| `BpmSupportOperation` | 16 | 辅助操作 |
| `BpmApiNodePermissionAppService` | 11 | **节点权限** |
| `BpmTemplateManageAppService` | 11 | 模板管理 |
| **`BpmUdcApiService`** | **10** | **★ UDC 集成专用** |
| `BpmApiDetectionService` | 9 | 流程检测 |
| `ActivityBehavior` | 8 | 节点行为 |
| `BpmApiParamAppService` | 8 | 流程参数 |
| `BpmOpinionAppService` | 7 | **意见** |
| `BpmProcessLogAppService` | 7 | 流程日志 |
| `BpmApiTransportAppService` | 7 | 传输 |
| `BpmDeployAppService` | 6 | 部署 |
| `BpmActivityAppService` | 4 | 节点活动 |
| `BpmAutoApprovalAppService` | 4 | **自动审批** |
| `BpmNodeAppService` | 4 | 节点 |
| `BpmThirdTemplateSyncAppService` | 4 | 三方模板同步 |
| `BpmWorkItemAppService` | 4 | 工作项 |
| `BpmApiPermissionAppService` | 3 | 权限 |
| `BpmApplicationOperateLogAppService` | 3 | 操作日志 |
| `BpmSuperviseAppService` | 3 | 督办 |
| `BpmActionAppService` | 2 | 动作 |
| `BpmCaseLogAppService` | 2 | 实例日志 |
| `BpmNodePermissionOperationAppService` | 2 | 节点权限操作 |
| `BpmNormalAppMultiVersionAppService` | 2 | 多版本 |
| `BpmProcessTrackAppService` | 2 | 流程轨迹 |
| `BpmApiSimulationAppService` | 2 | 流程模拟 |
| `BpmApiProcessAppService` | 1 | 流程定义 |
| `BpmDetailAppService` | 1 | 明细 |
| `BpmCoMiAppService` | 1 | 协同消息 |

---

## 4. ★★★ `BpmUdcApiService`（10 方法）—— UDC 与 BPM 的桥

**包：** `com.seeyon.bpm.api.udc.BpmUdcApiService`
**源码：** `bpm-facade/com/seeyon/bpm/api/udc/BpmUdcApiService.java`

**这是 UDC 单据调用 BPM 的专用接口，最关键。全部方法已实测读取：**

| 方法 | 请求 | 响应 | `default` |
|---|---|---|---|
| **`sendForUdc`** | `SingleRequest<BpmSendUdcDto>` | `SingleResponse<BpmApiSendApiResponseDto>` | public |
| **`repealForUdc`** | `SingleRequest<BpmOperationRepealUdcDto>` | `SingleResponse<Void>` | public |
| **`stopForUdc`** | `SingleRequest<BpmStopDto>` | `SingleResponse<CommonResultDto>` | public |
| **`deleteCaseByIdForUdc`** | `(SingleRequest<Long>, SingleRequest<Long>)` | `SingleResponse<Void>` | public |
| `saveDraft` | `SingleRequest<BpmSaveDraftUdcDto>` | `SingleResponse<BpmSaveDraftUdcResponseDto>` | default |
| `triggerFlowForUdc` | `SingleRequest<List<BpmTriggerFlowUdcRequestDto>>` | `ListResponse<BpmTriggerFlowUdcResponseDto>` | default |
| `asyncTriggerFlowForUdc` | `SingleRequest<BpmAsyncTriggerFlowUdcRequestDto>` | `SingleResponse<Void>` | default |
| `prefixForUdc` | `SingleRequest<BpmPrefixForUdcDto>` | `SingleResponse<BpmPrefixForUdcResponseDto>` | default |
| `getNodePermissionOperation` | `SingleRequest<BpmNodePermissionRequestDto>` | `ListResponse<BpmNodePermissionResponseDto>` | default |
| `getNodePermission` | `SingleRequest<BpmNodePermissionRequestDto>` | `SingleResponse<BpmNodePermission4PageDto>` | default |

### ★★ 三个关键结论（推翻先前推断）

**① UDC 发起流程的真实方法是 `sendForUdc`，不是 `send`**

先前在 `13-bpm-operation-dtos.md` 里我写「方法名待确认」，现在确认了：
```java
// ✅ 正确
bpmUdcApiService.sendForUdc(SingleRequest<BpmSendUdcDto>)

// ❌ 错误（这是 openapi 通用入口）
bpmAppService.send(SingleRequest<BpmSendDto>)
```

**② `BpmAppService`（26 方法）里没有任何 UDC 专用方法**

我逐个核对了 26 个方法名：`send` / `saveDraft` / `submit` / `stepBack` / `repeal` / `stop` / `takeBack` / `replace` / `consult` / `hasten` / `multipleReplace` / `pause` / `cancelPause` / `superviseRelive` / `superviseReliveFull` / `inform` / `addExecuteMember` / `cancelItems` / `batchDeal` / `selectFullCaseInfo` / `counterSignNode` / `addNode` / `monitorNodeRun` / `check` / `deleteDraft` / `deleteDraftAffair`

**⇒ 没有 `sendUdc`、没有 `*ForUdc`。UDC 链路完全走 `BpmUdcApiService`。**

**③ `deleteCaseByIdForUdc` 需要 2 个参数**

```java
deleteCaseByIdForUdc(SingleRequest<Long> var1, SingleRequest<Long> var2)
```
**⇒ 两个 `Long` 的 Request，签名看不出哪个是 caseId / userId。需读实现类（未读）。**

### UDC 专用响应 DTO

| DTO | 位置 |
|---|---|
| `BpmApiSendApiResponseDto` | `dto/approval/` |
| `BpmSaveDraftUdcResponseDto` | `dto/approval/` |
| `BpmTriggerFlowUdcResponseDto` | `dto/approval/` |
| `BpmPrefixForUdcResponseDto` | `dto/approval/` |
| `BpmAsyncTriggerFlowUdcRequestDto` | `dto/approval/` |

**⇒ 全部集中在 `com.seeyon.bpm.dto.approval` 包，与 openapi 的 `dto.operation.openapi` 分离。**
**⇒ 说明平台在设计上就把「UDC 集成」当成独立契约面。**

### 未解决

| 项 | 状态 |
|---|---|
| `deleteCaseByIdForUdc` 两个 Long 的含义 | **UNVERIFIED** |
| `BpmApiSendApiResponseDto` 字段 | 未读 |
| `BpmOperationRepealUdcDto` 字段 | 未读 |
| `BpmTriggerFlowUdcRequestDto`（触发流程，非发起） | 未读 |
| `prefixForUdc` 干什么 | 未读 |
| `BpmUdcApiService` 的实现类 | 未读 |

---

## 5. 流程模板管理 `BpmTemplateAppService`（55 方法）

**从已有的 domains/bpm.md 签名可见关键方法：**

```java
createOrUpdate(SingleRequest<BpmTemplateDto>)              : SingleResponse<Long>
deleteById(SingleRequest<Long>)
publishCheck(SingleRequest<String>)                        ★ 发布前检查
publishCheckByAppInfo(...)
publishLock / publishLockByAppInfo                          ★ 发布加锁
publishFinish(...)                                          ★ 发布完成
cleanCacheByApplicationName(...)                            ★ 清缓存
startCheck(SingleRequest<...>)                             : ListResponse<BpmTemplateDto>
start(SingleRequest<String>)                                ★ 启用模板
startByTemplateId / startByTemplateIdWithoutAuth            ★ 按模板ID启用
stop / stopByTemplateId                                     ★ 停用
deleteByApps(...)
selectByApplicationName(...)
updateEffectTimeByTemplateId / updateEffectTime             ★ 有效期
updateAuthorized(...)                                       ★ 授权
selectById / selectByTemplateUrlId
selectTemplateListByCondition(...)
selectEffectedDiagramListByAppName(...)                     ★ 已生效流程图
selectTemplateUserGuidInfo(...)                             ★ 用户引导信息
selectTemplateById(...)                                     ★ 模板详情
selectPathTableCondition(...)                               ★ 路径表条件
selectTemplateIdsByName(...)
selectTemplateByRootEntityId(...)                           ★ 按根实体找模板
selectTemplateByParams(...)
selectTemplateByRootEntityName(...)
```

**⇒ `selectTemplateByRootEntityId/Name` 是「业务单据怎么找到自己的流程模板」的答案。**
**⇒ `publishLock` / `publishFinish` 说明发布是**两阶段**（加锁 → 完成）。**
**⇒ `cleanCacheByApplicationName` 说明模板有缓存，改完必须清。**

---

## 6. 权限体系：两个独立接口

### 6.1 `BpmApiFormPermissionAppService`（18 方法）—— 表单权限

**控制「哪个节点能看/改哪些字段」。**

### 6.2 `BpmApiNodePermissionAppService`（11 方法）—— 节点权限

**控制「谁能办这个节点」。**

**⇒ 表单权限和节点权限是**两套独立机制**，不能混。**
**⇒ 这与 `01-metadata.md` 里的「58 字段 × 33 开关」权限矩阵对应。**

---

## 7. 流程实例查询 `BpmCaseAppService`（23 方法）

**从签名可见：**
```java
selectCaseById / selectMainCaseBySubCaseId
deleteCaseByIds / deleteCaseByIdForUdc              ★ UDC 专用删除
selectBpmCaseByFormRecordId                          ★ 按表单记录 ID 找流程
selectBpmCaseActivityByCaseId                        ★ 节点活动
selectRunningProcessPreNode                          ★ 运行中的前置节点
```

**⇒ `selectBpmCaseByFormRecordId` 是「业务数据 ↔ 流程实例」的关联键。**
**⇒ `deleteCaseByIdForUdc` 说明 UDC 删除单据有专用路径（不是普通 delete）。**

---

## 8. 单据状态机（结合 `03-persistence.md`）

**从 `BaseEntityCurdService.create4Bpm/update4Bpm` 反推 + 本域签名：**

```
NONE              无状态
DRAFT             草稿（saveDraft）
TO_BE_SUBMITTED   待提交（BPM 失败降级态）
PENDING_REVIEW    待审（老表单，会转 TO_BE_SUBMITTED）
（审批中）         submit 之后
（已结束）         stop / 流程走完
```

**状态流转：**
```
saveDraft  → DRAFT
submit     → 提交（从 DRAFT/TO_BE_SUBMITTED）
send       → 直接发起（从 NONE）
stepBack   → 退回（节点回退）
repeal     → 撤销（发起人，回到 DRAFT）
stop       → 终止（流程结束，不可再走）
takeBack   → 取回（办理人拿回）
```

**⇒⚠️ `update4Bpm` 只在 `NONE/DRAFT/TO_BE_SUBMITTED` 时才允许走 BPM，否则静默跳过。**

---

## 9. 开发要点

### 9.1 发起单据的三种方式

```
① BPM 原生：BpmAppService.send(BpmSendDto)
② UDC 集成：BaseEntityCurdService.create4Bpm(dto)     ← 推荐，自动处理主子表
③ 草稿后提交：saveDraft → submit
```

### 9.2 所有方法必须构造 Request 对象

```java
// 错误：直接传参数
bpmAppService.send(dto);

// 正确：包一层 SingleRequest
SingleRequest<BpmSendDto> req = new SingleRequest<>();
req.setData(dto);
SingleResponse<BpmSendResultDto> resp = bpmAppService.send(req);
```

### 9.3 单据 → 模板的查找

```
BpmTemplateAppService.selectTemplateByRootEntityId(rootEntityId)
BpmTemplateAppService.selectTemplateByRootEntityName(rootEntityName)
```

**⇒ 单据类型（根实体）决定用哪个流程模板。**

### 9.4 表单权限 vs 节点权限

```
节点权限（谁能办）      → BpmApiNodePermissionAppService
表单权限（能看/改哪些字段）→ BpmApiFormPermissionAppService
```

**⇒ 两者独立配置，缺一个都不完整。**

### 9.5 模板缓存

```
BpmTemplateAppService.cleanCacheByApplicationName(appName)
```

**⇒ 改模板后必须清缓存，否则读到旧的。**

---

## 10. 与 UDC 单据的完整链路

```
业务代码
  ↓
BaseEntityCurdService.create4Bpm(dto)
  ├─ if (id == null) setId(Ids.gidLong())
  ├─ 检查 statusType 非空
  ├─ approvalCallBack.beforeApprovalCreate(context)
  ├─ create(dto)                          ← 主表+子表落库
  ├─ approvalCallBack.afterApprovalCreate(context)
  │      ↓ 内部调
  │   BpmAppService.send(BpmSendDto) 或 BpmUdcApiService.*
  ├─ if (BPM 异常) statusType = TO_BE_SUBMITTED
  └─ updateRootEntity(oldDto, frontDto)
```

**⇒ `ApprovalCallBack` 的实现类是 UDC → BPM 的**实际桥接点**（下一轮要读）。**

---

## 11. 未覆盖（下一轮）

| 项 | 说明 |
|---|---|
| `ApprovalCallBack` 实现类 | UDC→BPM 实际桥接 |
| `BpmSendDto` 字段 | 发起流程要传什么 |
| `BpmSubmitDto` 字段 | 提交要传什么 |
| `BpmStepBackDto` 字段 | 退回要传什么（退回目标节点怎么指定）|
| `BpmUdcApiService` 10 个方法 | UDC 专用集成 |
| `BpmAutoApprovalAppService` | 自动审批规则 |
| `BpmApiDetectionService` | 流程检测做什么 |
