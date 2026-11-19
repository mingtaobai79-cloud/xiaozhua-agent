# bpm-facade 方法签名索引（flow 域第 5 格）

## 1. Capability

**回答「流程操作要调哪个类、方法叫什么、出入参什么形态」。**

适用：扩展代码 / 自定义微流程里要**发起流程、提交、回退、撤销、催办、加签、暂停、查待办、写意见**时查本格。

**本格不涉及任何具体应用/工程/环境。**

## 2. Version

| 构件 | 实际 jar | 版本 |
|---|---|---|
| `com.seeyon:bpm-facade` | `bpm-facade-5.3.600.jar` | **5.3.600** |
| `com.seeyon:ctp-affair-facade` | `ctp-affair-facade-5.3.600.jar` | **5.3.600** |

规模（本次全量 javap 实测）：**533 类 / 40 接口 / 96 枚举 / 5901 方法**。

> ⚠️ 旧 `surface-index` 标注 5.3.374，实际 jar 是 5.3.600。**本格按 5.3.600 实证。**

## 3. Input

`docs/audit/artifacts/extension-surface-20261118/interfaces.json` → `com.seeyon.bpm.api.common.*`

## 4. Required

无前置。跨进程 `@DubboReference`。

## 5. Execution

```java
// 发起并送达（主入口）
@DubboReference private BpmAppService bpmAppService;

BpmSendResultDto r = bpmAppService
    .send(SingleRequest.from(sendDto))
    .getData().getContent();

// 按模板发起（另一条路）
@DubboReference private BpmTemplateAppService bpmTemplateAppService;
bpmTemplateAppService.startByTemplateId(SingleRequest.from(startDto));
```

## 6. Output

---

## 6.1 ★★★★★ `BpmAppService`（26 方法）—— **流程操作总入口**

`com.seeyon.bpm.api.common.BpmAppService`
DTO 包：`com.seeyon.bpm.dto.operation.openapi.*`

**这是本次最重要的修正：`BpmAppService` 不是 4 个方法，是 26 个，且包含全部流转动作。**

### 6.1.1 发起 / 草稿

```java
SingleResponse<BpmSendResultDto>      send(SingleRequest<BpmSendDto>);           // ★ 发起并送达
SingleResponse<BpmSaveDraftResultDto> saveDraft(SingleRequest<BpmSaveDraftDto>); // 存草稿
SingleResponse<Void>                  deleteDraft(SingleRequest<Long>);
SingleResponse<Void>                  deleteDraftAffair(SingleRequest<DeleteDraftReqDto>);
```

**⇒ `send` 是「发起一条流程」的主入口。**

### 6.1.2 流转五动作

```java
SingleResponse<BpmSubmitResultDto> submit(SingleRequest<BpmSubmitDto>);       // 提交（审批）
SingleResponse<CommonResultDto>    stepBack(SingleRequest<BpmStepBackDto>);  // 回退
SingleResponse<CommonResultDto>    repeal(SingleRequest<BpmRepealDto>);      // 撤销
SingleResponse<CommonResultDto>    stop(SingleRequest<BpmStopDto>);          // 终止
SingleResponse<CommonResultDto>    takeBack(SingleRequest<BpmTakeBackDto>);  // 取回
```

| 方法 | 语义 | 谁做 |
|---|---|---|
| `submit` | **提交流转到下一节点** | 当前处理人 |
| `stepBack` | **退回上一节点** | 当前处理人 |
| `repeal` | **撤销整个流程**（回到发起人） | 发起人 |
| `stop` | **终止流程**（不可继续） | 有权限者 |
| `takeBack` | **取回**（追回已发出的） | 发起人 |

### 6.1.3 人员与节点变更

```java
SingleResponse<CommonResultDto>       replace(SingleRequest<BpmReplaceDto>);                   // 换人
SingleResponse<CommonResultDto>       multipleReplace(SingleRequest<BpmMultipleReplaceDto>);   // 批量换人
ListResponse<BpmItemInfoDto>          addExecuteMember(SingleRequest<BpmAddExecuteUserDto>);   // 加签/加办理人
SingleResponse<ChangeNodeResponseDto> counterSignNode(SingleRequest<SimpleChangeProcessRequestDto>); // 会签
SingleResponse<ChangeNodeResponseDto> addNode(SingleRequest<SimpleChangeProcessRequestDto>);    // 加节点
SingleResponse<CommonResultDto>       cancelItems(SingleRequest<BpmCancelItemDto>);            // 取消事项
```

### 6.1.4 催办 / 通知 / 暂停

```java
ListResponse<BpmHastenResponseDto> hasten(SingleRequest<BpmHastenDto>);        // 催办
SingleResponse<CommonResultDto>    inform(SingleRequest<BpmInformDto>);       // 通知
ListResponse<BpmPauseResponseDto>  pause(SingleRequest<BpmPauseDto>);         // 暂停
ListResponse<BpmPauseResponseDto>  cancelPause(SingleRequest<BpmPauseDto>);   // 恢复
```

### 6.1.5 督办

```java
SingleResponse<CommonResultDto> superviseRelive(SingleRequest<BpmReliveDto>);
SingleResponse<CommonResultDto> superviseReliveFull(SingleRequest<BpmReliveFullDto>);
```

### 6.1.6 批量 / 查询 / 监控

```java
ListResponse<BpmBatchResponseDto> batchDeal(SingleRequest<BpmBatchReqDto>);                      // 批量审批
SingleResponse<BpmCaseFullInfo>   selectFullCaseInfo(SingleRequest<BpmCaseFullInfoSearch>);      // 全量详情
SingleResponse<Boolean>           check(SingleRequest<SecurityCheckDto>);                        // 权限校验
SingleResponse<BpmMonitorRunResultDto> monitorNodeRun(SingleRequest<BpmMonitorRunDto>);          // 节点监控
SingleResponse<CommonResultDto>   consult(SingleRequest<BpmConsultDto>);                         // 传阅
```

---

## 6.2 `BpmTemplateAppService`（55 方法）—— 按模板发起 + 模板管理

`com.seeyon.bpm.api.common.BpmTemplateAppService`

### 6.2.1 发起（另一条路）

```java
ListResponse<BpmTemplateDto> startByTemplateId(SingleRequest<BpmStartTemplateDto>);
ListResponse<BpmTemplateDto> startByTemplateIdWithoutAuth(SingleRequest<BpmStartTemplateDto>);
ListResponse<BpmTemplateDto> startCheck(SingleRequest<BpmStartTemplateDto>);          // 发起前校验
SingleResponse<Void>         start(SingleRequest<String>, SingleRequest<String>);     // 旧形态
```

**⇒ 两种发起方式：**
- **`BpmAppService.send(BpmSendDto)`** —— 完整 DTO，能带表单数据、选人
- **`BpmTemplateAppService.startByTemplateId(BpmStartTemplateDto)`** —— 按模板 id 发起

### 6.2.2 发布链（改流程模板必经）

```java
SingleResponse<Void>    publishCheck(SingleRequest<String>);
SingleResponse<Void>    publishLock(SingleRequest<...>);
SingleResponse<Void>    publishLockByAppInfo(SingleRequest<...>);
SingleResponse<Void>    publishFinish(SingleRequest<BpmPublishResult>);
SingleResponse<Integer> deleteById(SingleRequest<Long>);
SingleResponse<Integer> deleteByApps(SingleRequest<...>);
```

### 6.2.3 高频查询

```java
Boolean                        hasDesignTemplateByEntityName(SingleRequest<String>);  // 实体配了流程吗
ListResponse<BpmTemplateDto>   selectTemplateByRootEntityName(SingleRequest<String>);
SingleResponse<BpmTemplateDto> selectCascadeById(SingleRequest<Long>);
ListResponse<BpmTemplateDto>   selectByIds(SingleRequest<List<Long>>);
ListResponse<String>           filterEnableTemplateAppName(SingleRequest<List<String>>);
SingleResponse<Integer>        updateTemplateExtend(SingleRequest<BpmTemplateExtendUpdateDto>);
```

**⇒ 55 个方法里 40+ 是查询/管理，业务代码只用发起与 `hasDesignTemplateByEntityName`。**

---

## 6.3 `BpmActionAppService`（2 方法）—— 活动级操作

`com.seeyon.bpm.api.common.BpmActionAppService`

```java
SingleResponse<BpmSubmitResultDto> activitySubmit(SingleRequest<BpmActivitySubmitDto>);
SingleResponse<Void>               activityStepBack(SingleRequest<BpmActivityTakeBackDto>);
```

**★ 与 `BpmAppService.submit/stepBack` 的区别：**

| | `BpmAppService.submit` | `BpmActionAppService.activitySubmit` |
|---|---|---|
| 粒度 | 流程级（caseId / affairId） | **活动级（activityId）** |
| 场景 | 常规审批 | 指定某节点活动 |

**⇒ 一般用 `BpmAppService`；要精确到活动用 `BpmActionAppService`。**

---

## 6.4 `AffairMicroflowAppService`（4 方法）—— 微流程发起事项

`com.seeyon.ctp.affair.api.microflow.AffairMicroflowAppService`

```java
SingleResponse<Void> createAffairByMicroflow(SingleRequest<AffairMicroflowInfoDto>);
ListResponse<Long>   createAffairByMicroflowReturnIds(SingleRequest<AffairMicroflowInfoDto>); // ★ 要 id
SingleResponse<Void> updateAffairReadByMicroflow(SingleRequest<AffairMicroUpdateConditionDto>);
SingleResponse<Void> updateAffairDoneByMicroflow(SingleRequest<AffairMicroUpdateConditionDto>);
```

---

## 6.5 `BpmWorkItemAppService`（4 方法）—— 待办工作项

`com.seeyon.bpm.api.common.BpmWorkItemAppService`

```java
SingleResponse<Integer>        create(SingleRequest<BpmWorkItemDto>);
SingleResponse<Integer>        createBatch(SingleRequest<List<BpmWorkItemDto>>);
SingleResponse<BpmWorkItemDto> selectById(SingleRequest<Long>);
ListResponse<BpmWorkItemDto>   selectByCaseId(SingleRequest<Long>);   // ★ 查待办
```

## 6.6 `BpmOpinionAppService`（7 方法）—— 意见

`com.seeyon.bpm.api.common.BpmOpinionAppService`

```java
SingleResponse<Integer> create(SingleRequest<BpmOpinionDataDto>);
SingleResponse<Integer> createBatch(SingleRequest<List<BpmInputOpinionDto>>);
SingleResponse<Integer> createBatchOpinion(SingleRequest<List<BpmOpinionDataDto>>);
SingleResponse<Void>    updateOpinion(SingleRequest<BpmOpinionUpdateDto>);
SingleResponse<Void>    deleteOpinion(SingleRequest<...>);
SingleResponse<Void>    adminDeleteOpinion(SingleRequest<Long>);
ListResponse<...>       selectOpinionGroupByActivityNodeWithObjectId(SingleRequest<...>);
```

## 6.7 `BpmProcessLogAppService`（7 方法）—— 流程日志

`com.seeyon.bpm.api.common.BpmProcessLogAppService`

```java
SingleResponse<Integer>        create(SingleRequest<...>);
SingleResponse<Integer>        createBatch(SingleRequest<...>);
SingleResponse<Integer>        createBatchProcessLog(SingleRequest<List<BpmProcessLogDto>>);
PageResponse<BpmProcessLogDto> selectPageByConditions(PageRequest);   // ★ 裸 PageRequest
ListResponse<...>              selectLogList(SingleRequest<...>);
ListResponse<...>              selectOriginalI18nLogList(SingleRequest<...>);
ListResponse<...>              selectLogOriginalListByCaseIds(SingleRequest<...>);
```

## 6.8 `BpmCaseAppService`（23 方法）—— 流程实例

`com.seeyon.bpm.api.common.BpmCaseAppService`

```java
// 按 id 查
selectCaseById / selectById / selectByIds / selectCascadeById / selectCascadeByIds
selectMainCaseBySubCaseId             // 子流程查主流程
selectBpmCaseByFormRecordId           // 表单记录反查流程
selectByIdDisplayName / selectByIdsDisplayName

// 分页 / 动态查询
selectByPageCondition / selectPageByConditions / dynamicSelect / dynamicJoinSelect
selectCascadeByConditions / selectCascadeListByConditions / getCascadeDefaultValue
selectExpression

// 写
create / createBatch / updateCase / deleteCaseByIds
refreshCaseTitleById                  // 重算标题
selectCaseAttachmentList              // 附件
```

**⇒ `create` 是引擎内部建实例，业务代码不调；
   查实例用 `selectCaseById` / `dynamicSelect`；
   子流程查主流程用 `selectMainCaseBySubCaseId`。**

## 6.9 `BpmActivityAppService`（4 方法）

`com.seeyon.bpm.api.common.BpmActivityAppService`

```java
SingleResponse<Integer> create(SingleRequest<BpmActivityRunDto>);
SingleResponse<Integer> createBatch(SingleRequest<List<BpmActivityRunDto>>);
```

---

## 7. Side Effects

| 方法 | 副作用 |
|---|---|
| `send` / `startByTemplateId` | **建流程实例、生成待办、发消息、触发事件** |
| `submit` / `stepBack` / `activitySubmit` | **流转、写日志、改待办状态** |
| `repeal` / `stop` / `takeBack` | **终止或撤销流程（外部可见）** |
| `replace` / `multipleReplace` / `addExecuteMember` | **改处理人（会通知到人）** |
| `pause` / `cancelPause` | 停 / 启流程计时 |
| `batchDeal` | **批量审批（影响多条）** |
| `createAffairByMicroflow*` | **建事务、发消息、进待办箱** |

**⇒ 全部有外部可见效果。必须在事务内、验证前先记录基线。**

## 8. Known Constraints

| # | 约束 |
|---|---|
| 1 | **`BpmAppService` 有 26 个方法**，是流程操作总入口（不是 4 个） |
| 2 | **发起用 `BpmAppService.send(BpmSendDto)`** 或 `BpmTemplateAppService.startByTemplateId` |
| 3 | **`submit`/`stepBack`/`repeal`/`stop`/`takeBack` 五个语义不同**，不能混用 |
| 4 | **`BpmActionAppService` 是活动级**（activityId），与流程级 `submit` 不同 |
| 5 | 所有入参 `SingleRequest.from(...)`；**`BpmProcessLogAppService.selectPageByConditions` 例外，用裸 `PageRequest`** |
| 6 | 取值两层 `getData().getContent()` |
| 7 | 跨进程 `@DubboReference` |
| 8 | `createAffairByMicroflow` **不返回 id**，要 id 用 `...ReturnIds` |
| 9 | `start(SingleRequest<String>, SingleRequest<String>)` 是旧形态，新代码用 `startByTemplateId` |

## 9. Evidence

| 内容 | 证据 | 等级 |
|---|---|---|
| 533 类 / 40 接口 / 5901 方法 | 本次全量 javap 重建 `interfaces.json` | **VERIFIED_STATIC_BYTECODE** |
| **`BpmAppService` 26 方法（含 send/submit/stepBack/repeal/stop/takeBack）** | `interfaces.json` → `classes[...].methods` 逐个枚举 | **LIVE（本次重建）** |
| **`BpmTemplateAppService` 55 方法（含 startByTemplateId）** | 同上 | **LIVE（本次重建）** |
| `BpmActionAppService` 2 方法 | 同上 | **LIVE（本次重建）** |
| `AffairMicroflowAppService` 4 方法 | 同上 | **LIVE（本次重建）** |
| 全部签名 | javap -p 逐字 | **VERIFIED_STATIC_BYTECODE** |

## 10. Verified

- ✅ **LIVE**：本次从 `cplib/bpm-facade-5.3.600.jar` 全量重建索引，方法清单逐个枚举
- ✅ **VERIFIED_STATIC_BYTECODE**：所有签名 javap 原文
- ⚠️ **UNVERIFIED**：各 DTO 字段结构（见 `dto-fields/bpm.md`）
- ⚠️ **UNVERIFIED**：真实调用效果（需 LIVE 环境）

### 本次修正记录（重要）

| # | 先前写错 | 实测真相 |
|---|---|---|
| 1 | 「`BpmAppService` 只有 4 个方法，没有 start/submit」 | **26 个，含 `send`/`submit`/`stepBack`/`repeal`/`stop`/`takeBack`/`replace`/`addExecuteMember`** |
| 2 | 「发起流程 = `BpmActionAppService.activitySubmit`」 | **发起 = `BpmAppService.send` 或 `BpmTemplateAppService.startByTemplateId`** |
| 3 | 「`BpmTemplateAppService` 23 方法」 | **55 方法，含 `startByTemplateId`/`startCheck`/`publishCheck`** |
| 4 | 「`BpmOpinionAppService` 5 方法」 | **7 方法** |
| 5 | 「`BpmProcessLogAppService` 2 方法」 | **7 方法** |

**根因**：旧索引 `packages/bpm-facade.md` 只渲染「关键类」的部分方法，我误当全量。
**本次用重建的 `interfaces.json` 逐个枚举方法名，才是真实完整面。**

## 11. 给 Agent 的判据

```
问「怎么发起流程」
  → BpmAppService.send(SingleRequest<BpmSendDto>)            ★ 主入口
  → 或 BpmTemplateAppService.startByTemplateId(BpmStartTemplateDto)
  → 微流程里发事项要 id：AffairMicroflowAppService.createAffairByMicroflowReturnIds

问「怎么提交/审批」
  → BpmAppService.submit(SingleRequest<BpmSubmitDto>)
  → 活动级：BpmActionAppService.activitySubmit(BpmActivitySubmitDto)

问「怎么回退」
  → BpmAppService.stepBack(SingleRequest<BpmStepBackDto>)

问「怎么撤销/终止/取回」
  → repeal / stop / takeBack   ← 三个不同，看清语义

问「怎么催办」
  → BpmAppService.hasten(SingleRequest<BpmHastenDto>)

问「怎么换人/加签」
  → replace / multipleReplace / addExecuteMember

问「怎么查待办」
  → BpmWorkItemAppService.selectByCaseId(流程实例id)
  → 或 BpmAppService.selectFullCaseInfo(全量详情)

问「这个实体配了流程吗」
  → BpmTemplateAppService.hasDesignTemplateByEntityName(实体名)

问「BpmAppService 有几个方法」
  → 26 个。别再信旧索引的 4 个。
```